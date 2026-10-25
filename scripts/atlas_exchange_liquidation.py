#!/usr/bin/env python3
"""Verify sampled Exchange single-liquidation paths on an archive-backed fork."""

import argparse
import json
import os
import pathlib

from atlas_exchange_positions import position_slot
from atlas_factory_events import Keccak
from atlas_oracle_behavior import PRE_BBO, returndata, rpc
from atlas_paper_token import calldata

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_liquidation" / "pinned_local_probes.json"
PIN = 48902346
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
KEEPER = "0x07626d8137ede6b922bcecf3b67f82a21100a612"
LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
BATCH_EXTRA_TOPIC = "0x0bb3f42f9fe304326ba30302693425c1db2e2f6a4675df44372fc0af5ce73706"
ERRORS = {"NotLiquidatable()": "0xddeb79ba", "PositionNotOpen()": "0x94e88a21"}
POSITIONS = (
    (1394473, "long", 700000, 809525),
    (1394058, "long", 117500, 235015),
    (1394062, "long", 404000, 809325),
    (1394060, "short", 235015, 245000),
)


def logs_in(call):
    result = list(call.get("logs", []))
    for child in call.get("calls", []):
        result.extend(logs_in(child))
    return result


def storage_only(diff):
    return {address.lower(): {"pre": diff.get("pre", {}).get(address, {}).get("storage", {}),
                              "post": diff.get("post", {}).get(address, {}).get("storage", {})}
            for address in sorted(set(diff.get("pre", {})) | set(diff.get("post", {})))
            if diff.get("pre", {}).get(address, {}).get("storage") or
               diff.get("post", {}).get(address, {}).get("storage")}


def trace(url, position_id, price, batch=False, state=False):
    code = returndata(price, price)
    rpc(url, "anvil_setCode", [PRE_BBO, code])
    data = calldata("0x599dc539", 32, 1, position_id) if batch else calldata("0x415f1240", position_id)
    call = {"from": KEEPER, "to": EXCHANGE, "data": data, "gas": "0x2dc6c0"}
    traced = rpc(url, "debug_traceCall", [call, hex(PIN),
                                            {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
    row = {"position_id": position_id, "mock_bid": price, "mock_ask": price,
           "mock_runtime_code": code, "selector": data[:10],
           "error": traced.get("error"), "output": traced.get("output", ""),
           "logs": logs_in(traced),
           "implementation_calls": [{"to": x["to"], "input": x["input"][:10],
                                     "error": x.get("error")} for x in traced.get("calls", [])]}
    if state:
        diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                                             {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
        row["storage_changes"] = storage_only(diff)
    return row


def capture(local_url):
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    archive_url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    public_url = "https://rpc.hyperliquid.xyz/evm"
    headers = {name: rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"].lower()
               for name, url in (("archive", archive_url), ("public", public_url), ("local", local_url))}
    assert set(headers.values()) == {manifest["block_hash"]}
    witness_slot = f"0x{position_slot(1394473) + 1:064x}"
    witness_words = {name: rpc(url, "eth_getStorageAt", [EXCHANGE, witness_slot, hex(PIN)])
                     for name, url in (("archive", archive_url), ("public", public_url), ("local", local_url))}
    assert witness_words["archive"] == witness_words["local"]
    assert int(witness_words["archive"], 16) - int(witness_words["public"], 16) == 1 << 240
    position_rows = {x["position_id"]: x for x in json.loads((ATLAS / "exchange_position_layout.json").read_text())["records"]
                     if x["status"] == "matched"}
    probes = []
    for position_id, side, lower, upper in POSITIONS:
        position = position_rows[position_id]["decoded"]
        assert position["entry_price"] == (upper if side == "long" else lower)
        assert (position["top_32_flags"] & 1) == (side == "long")
        word = int(rpc(local_url, "eth_getStorageAt",
                       [EXCHANGE, hex(position_slot(position_id) + 1), hex(PIN)]), 16)
        assert word >> 240 & 1
        low_probe, high_probe = trace(local_url, position_id, lower), trace(local_url, position_id, upper)
        assert (low_probe["error"] is None, high_probe["error"] is None) == (
            (True, False) if side == "long" else (False, True))
        while upper - lower > 1:
            middle = (lower + upper) // 2
            good = trace(local_url, position_id, middle)["error"] is None
            if (good and side == "long") or (not good and side == "short"):
                lower = middle
            else:
                upper = middle
        failed_price, successful_price = (upper, lower) if side == "long" else (lower, upper)
        failed = trace(local_url, position_id, failed_price)
        successful = trace(local_url, position_id, successful_price, state=True)
        assert failed["error"] == "execution reverted" and failed["output"] == ERRORS["NotLiquidatable()"]
        assert successful["error"] is None
        probes.append({"position_id": position_id, "side": side, "entry_price": position["entry_price"],
                       "margin": str(position["margin"]), "leverage": position["leverage"],
                       "first_success_price": successful_price if side == "short" else None,
                       "last_success_price": successful_price if side == "long" else None,
                       "adjacent_failed_price": failed_price,
                       "failed": failed, "successful": successful})
    inactive = trace(local_url, 0, 800000)
    assert inactive["output"] == ERRORS["PositionNotOpen()"]
    single = trace(local_url, 1394473, 800000, state=True)
    batch = trace(local_url, 1394473, 800000, batch=True, state=True)
    assert single["error"] is None and batch["error"] is None
    result = {"pin_block": PIN, "pin_hash": manifest["block_hash"],
              "method": "read-only debug_traceCall on an archive-backed Anvil fork with fixed HyperCore BBO runtime",
              "provider_crosscheck": {"block_hashes": headers, "slot": witness_slot, "words": witness_words},
              "price_boundary_probes": probes, "inactive_probe": inactive,
              "single_batch_comparison": {"single": single, "batch": batch},
              "limits": ["The public HyperEVM RPC and archive RPC disagree on one active flag at the same block hash; only the archive-backed fork is used for behavior probes.",
                         "Prices are synthetic read-precompile outputs, so successful calls are simulations and do not prove live liquidation eligibility.",
                         "Four active sampled positions and one inactive ID do not establish all liquidation formulas or branches."]}
    ARTIFACT.write_text(json.dumps(result, indent=2) + "\n")


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    signature = "liquidate(uint256)"
    assert "0x" + Keccak()(signature.encode()).hex()[:8] == "0x415f1240"
    fixture = json.loads((ATLAS / "exchange_interface_evidence.json").read_text())
    assert any(row["selector"] == "0x415f1240" and row["signature"] == signature
               for row in fixture["functions"])
    assert all("0x" + Keccak()(name.encode()).hex()[:8] == selector for name, selector in ERRORS.items())
    result = json.loads(ARTIFACT.read_text())
    assert result["pin_block"] == PIN and result["pin_hash"] == manifest["block_hash"]
    crosscheck = result["provider_crosscheck"]
    assert set(crosscheck["block_hashes"].values()) == {manifest["block_hash"]}
    assert crosscheck["words"]["archive"] == crosscheck["words"]["local"]
    assert int(crosscheck["words"]["archive"], 16) - int(crosscheck["words"]["public"], 16) == 1 << 240
    assert len(result["price_boundary_probes"]) == 4
    for row in result["price_boundary_probes"]:
        side = row["side"]
        success_price = row["last_success_price"] if side == "long" else row["first_success_price"]
        assert abs(success_price - row["adjacent_failed_price"]) == 1
        failed, successful = row["failed"], row["successful"]
        assert failed["mock_bid"] == failed["mock_ask"] == row["adjacent_failed_price"]
        assert failed["error"] == "execution reverted" and failed["output"] == ERRORS["NotLiquidatable()"]
        assert not failed["logs"]
        assert successful["mock_bid"] == successful["mock_ask"] == success_price
        assert successful["error"] is None and successful["implementation_calls"] == [
            {"to": IMPLEMENTATION, "input": "0x415f1240", "error": None}]
        liquidation_events = [x for x in successful["logs"] if x["topics"][0] == LIQUIDATED]
        assert len(liquidation_events) == 1
        log = liquidation_events[0]
        assert log["address"].lower() == EXCHANGE
        assert int(log["topics"][1], 16) == row["position_id"]
        assert int(log["data"][2:66], 16) == success_price
        storage = successful["storage_changes"][EXCHANGE]
        position_word = f"0x{position_slot(row['position_id']) + 1:064x}"
        assert int(storage["pre"][position_word], 16) - int(storage["post"][position_word], 16) == 1 << 240
        event_words = [int(log["data"][i:i + 64], 16) for i in range(2, len(log["data"]), 64)]
        assert event_words[3] * 100 == event_words[4] * 100 == int(row["margin"])
    inactive = result["inactive_probe"]
    assert inactive["position_id"] == 0 and inactive["error"] == "execution reverted"
    assert inactive["output"] == ERRORS["PositionNotOpen()"] and not inactive["logs"]
    comparison = result["single_batch_comparison"]
    single, batch = comparison["single"], comparison["batch"]
    assert single["error"] is None and batch["error"] is None
    assert single["storage_changes"] == batch["storage_changes"]
    assert single["logs"] == [log for log in batch["logs"] if log["topics"][0] != BATCH_EXTRA_TOPIC]
    assert len([log for log in batch["logs"] if log["topics"][0] == BATCH_EXTRA_TOPIC]) == 1
    behavior = {"pin_block": PIN, "pin_hash": manifest["block_hash"],
                "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION,
                "selector_reconstructions": {"0x415f1240": signature},
                "signature_evidence": "Exact hash, pinned public ABI fixture, and saved local execution",
                "sampled_active_positions": 4,
                "price_boundaries": [{key: row[key] for key in ("position_id", "side", "entry_price", "leverage",
                                                              "last_success_price", "first_success_price", "adjacent_failed_price")}
                                     for row in result["price_boundary_probes"]],
                "single_batch_same_storage_changes": True,
                "single_batch_same_logs_except_batch_summary": True,
                "simulated_error_catalog": [{"selector": selector, "reconstructed_signature": name,
                                             "probe_paths": ["inactive_id_zero"] if name == "PositionNotOpen()" else
                                                            [f"price_boundary_{row['position_id']}" for row in result["price_boundary_probes"]]}
                                            for name, selector in ERRORS.items()],
                "limits": result["limits"]}
    (ATLAS / "exchange_liquidation_behavior.json").write_text(json.dumps(behavior, indent=2) + "\n")
    print("Exchange liquidation: 4 exact price boundaries, 2 exercised errors, single/batch state match")
    return behavior


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-rpc-url", help="Archive-backed local Anvil fork URL, not a live chain URL")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    verify()
