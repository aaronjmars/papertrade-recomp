"""Replay invalid BBO liquidation paths on the exact pinned Exchange runtime."""

import argparse
import hashlib
import json
from pathlib import Path

from atlas_exchange_batch_branches import calldata as batch_calldata
from atlas_exchange_batch_branches import walk
from atlas_exchange_liquidation import (
    EXCHANGE,
    IMPLEMENTATION,
    KEEPER,
    PIN,
    PRE_BBO,
    logs_in,
    position_slot,
    rpc,
    storage_only,
)
from atlas_exchange_positions import balance_slot
from atlas_oracle_behavior import IMPLEMENTATION as ORACLE_IMPL
from atlas_oracle_behavior import PROXY as ORACLE
from atlas_oracle_behavior import returndata, revert_reason
from atlas_paper_token import calldata as scalar_calldata

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
RAW = ROOT / "artifacts" / "exchange_liquidation" / "invalid_prices.json"
SUMMARY = ATLAS / "exchange_liquidation_invalid_prices.json"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
TOKENOMICS_IMPL = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
PAPER = "0xe40f17915daa230324030003a197cdaef2261c0e"
PAPER_IMPL = "0x433bd418ec92818a960585f4d5fae563e735bb4a"
PAPER_MATH = "0xe991817199363046da0a28da6fbad0284e4aa492"
RUNTIMES = (EXCHANGE, IMPLEMENTATION, ORACLE, ORACLE_IMPL, TOKENOMICS, TOKENOMICS_IMPL,
            PAPER, PAPER_IMPL, PAPER_MATH)
LONG_0 = 1394473
LONG_1 = 1394058
GOOD_0 = returndata(800000, 800000)
GOOD_1 = returndata(230400, 230400)
BAD = {
    "missing": "0x00",                 # STOP returns no bytes
    "reverted": "0x60006000fd",       # explicit precompile failure
    "zero": returndata(0, 0),
    "zero_bid": returndata(0, 800000),
    "zero_ask": returndata(800000, 0),
    "crossed": returndata(800001, 800000),
}
REASONS = {
    "missing": "BBO read failed",
    "reverted": "BBO read failed",
    "zero": "BBO unavailable",
    "zero_bid": "BBO unavailable",
    "zero_ask": "BBO unavailable",
    "crossed": "BBO crossed",
}
CASES = (
    ("single_valid", (LONG_0,), "single", GOOD_0, None, None),
    ("batch_valid_two_assets", (LONG_0, LONG_1), "batch", GOOD_0, GOOD_1, None),
    *((f"single_{kind}", (LONG_0,), "single", code, None, kind) for kind, code in BAD.items()),
    *((f"batch_{kind}", (LONG_0,), "batch", code, None, kind)
      for kind, code in BAD.items() if kind in ("missing", "reverted", "zero", "crossed")),
    *((f"mixed_good_then_{kind}", (LONG_0, LONG_1), "batch", GOOD_0, BAD[kind], kind)
      for kind in ("missing", "zero", "crossed")),
    *((f"mixed_{kind}_then_good", (LONG_1, LONG_0), "batch", GOOD_0, BAD[kind], kind)
      for kind in ("missing", "zero", "crossed")),
)


def selective_code(asset_0, asset_1):
    """Return asset 0's code unless the uint32 calldata word equals asset 1."""
    first = asset_0[2:]
    second = asset_1[2:]
    jump = 9 + len(bytes.fromhex(first))
    assert jump < 256
    return f"0x60003560011460{jump:02x}57{first}5b{second}"


def code_for(asset_0, asset_1):
    return asset_0 if asset_1 is None else selective_code(asset_0, asset_1)


def request_for(ids, entrypoint):
    data = scalar_calldata("0x415f1240", ids[0]) if entrypoint == "single" else batch_calldata(ids)
    return {"from": KEEPER, "to": EXCHANGE, "data": data, "gas": hex(2900000)}


def watched_slots(position_rows):
    slots = {f"0x{slot:064x}": label for slot, label in (
        (14, "treasury"), (18, "total_queued"), (22, "total_balances_and_locked_margin"),
        (25, "liquidation_fee_rate"), (26, "staker_and_dev_fees"))}
    for position_id in (LONG_0, LONG_1):
        slots[f"0x{position_slot(position_id):064x}"] = f"position_{position_id}_word_0"
        slots[f"0x{position_slot(position_id) + 1:064x}"] = f"position_{position_id}_flags"
        user = position_rows[position_id]["decoded"]["user"]
        slots[f"0x{balance_slot(user):064x}"] = f"user_{position_id}_balance"
    return slots


def snapshot_words(url, slots):
    return {slot: rpc(url, "eth_getStorageAt", [EXCHANGE, slot, "latest"]) for slot in slots}


def capture(url):
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    assert int(rpc(url, "eth_blockNumber", []), 16) == PIN
    runtime_hashes = {}
    for address in RUNTIMES:
        code = rpc(url, "eth_getCode", [address, hex(PIN)])
        digest = hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
        expected = manifest["contracts"][address]["sha256"]
        assert digest == expected
        assert code.lower() == (ATLAS / manifest["contracts"][address]["runtime_file"]).read_text().strip().lower()
        runtime_hashes[address] = digest
    layout = json.loads((ATLAS / "exchange_position_layout.json").read_text())
    position_rows = {row["position_id"]: row for row in layout["records"] if row["position_id"] in (LONG_0, LONG_1)}
    assert {position_id: row["decoded"]["instrument"] for position_id, row in position_rows.items()} == {
        LONG_0: 0, LONG_1: 1}
    slots = watched_slots(position_rows)
    archived = json.loads((ROOT / "artifacts" / "exchange_liquidation" / "pinned_batch_branches.json").read_text())
    for position_id in (LONG_0, LONG_1):
        flag_slot = f"0x{position_slot(position_id) + 1:064x}"
        actual = rpc(url, "eth_getStorageAt", [EXCHANGE, flag_slot, hex(PIN)])
        assert actual == archived["provider_crosscheck"]["position_words"][str(position_id)]["archive"]
        assert int(actual, 16) >> 240 & 1

    rpc(url, "anvil_impersonateAccount", [KEEPER])
    rpc(url, "anvil_setBalance", [KEEPER, hex(10**20)])
    rows = []
    for name, ids, entrypoint, asset_0, asset_1, invalid_kind in CASES:
        code = code_for(asset_0, asset_1)
        rpc(url, "anvil_setCode", [PRE_BBO, code])
        request = request_for(ids, entrypoint)
        trace = rpc(url, "debug_traceCall", [request, hex(PIN),
                                              {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        diff = rpc(url, "debug_traceCall", [request, hex(PIN),
                                             {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
        before = snapshot_words(url, slots)
        state = rpc(url, "evm_snapshot", [])
        try:
            tx = rpc(url, "eth_sendTransaction", [request])
            rpc(url, "evm_mine", [])
            receipt = rpc(url, "eth_getTransactionReceipt", [tx])
            assert receipt is not None
            after = snapshot_words(url, slots)
        finally:
            assert rpc(url, "evm_revert", [state])
        rows.append({
            "name": name, "ids": list(ids), "entrypoint": entrypoint,
            "invalid_kind": invalid_kind, "asset_0_code": asset_0, "asset_1_code": asset_1,
            "mock_runtime_code": code, "request": request, "trace": trace,
            "storage_changes": storage_only(diff), "watched_before": before, "watched_after": after,
            "receipt": {"status": receipt["status"], "logs": receipt["logs"],
                        "gas_used": receipt["gasUsed"], "block": receipt["blockNumber"]},
        })
        print(name, "reverted" if trace.get("error") else "succeeded", flush=True)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "pin_block": PIN, "pin_hash": manifest["block_hash"],
        "method": "archive-backed Anvil fork, read-only pinned trace and snapshotted local transaction",
        "runtime_sha256": runtime_hashes, "watched_slots": slots, "cases": rows,
    }, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(RAW.read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    for address, digest in saved["runtime_sha256"].items():
        assert digest == manifest["contracts"][address]["sha256"]
    assert set(saved["runtime_sha256"]) == set(RUNTIMES)
    assert len(saved["cases"]) == len(CASES)
    layout = json.loads((ATLAS / "exchange_position_layout.json").read_text())
    positions = {row["position_id"]: row for row in layout["records"]
                 if row["position_id"] in (LONG_0, LONG_1)}
    assert saved["watched_slots"] == watched_slots(positions)
    baseline = saved["cases"][0]["watched_before"]
    assert all(row["watched_before"] == baseline for row in saved["cases"])
    summaries = []
    for row, (name, ids, entrypoint, asset_0, asset_1, invalid_kind) in zip(saved["cases"], CASES):
        assert (row["name"], row["ids"], row["entrypoint"], row["invalid_kind"]) == (
            name, list(ids), entrypoint, invalid_kind)
        assert (row["asset_0_code"], row["asset_1_code"], row["mock_runtime_code"]) == (
            asset_0, asset_1, code_for(asset_0, asset_1))
        assert row["request"] == request_for(ids, entrypoint)
        trace = row["trace"]
        assert trace["to"].lower() == EXCHANGE and trace["input"].lower() == row["request"]["data"].lower()
        assert trace["calls"][0]["to"].lower() == IMPLEMENTATION
        touched = {call.get("to", "").lower() for call in walk(trace)
                   if call.get("to", "").lower() in manifest["contracts"]}
        assert touched <= set(saved["runtime_sha256"])
        receipt = row["receipt"]
        assert int(receipt["block"], 16) == PIN + 1
        assert 0 < int(receipt["gas_used"], 16) < int(row["request"]["gas"], 16)
        assert set(row["watched_before"]) == set(saved["watched_slots"])
        assert set(row["watched_after"]) == set(saved["watched_slots"])
        oracle_calls = [call for call in walk(trace) if call.get("to", "").lower() == ORACLE
                        and call.get("input", "").startswith("0xc0182669")]
        assets = [int(call["input"][10:], 16) for call in oracle_calls]
        expected_assets = [0] if asset_1 is None else ([1] if name.endswith("_then_good") else [0, 1])
        assert assets == expected_assets
        settlement_calls = [call for call in walk(trace) if call.get("to", "").lower() == TOKENOMICS
                            and call.get("input", "").startswith("0x0efdf838")]
        reason = revert_reason(trace)
        if invalid_kind is None:
            assert len(settlement_calls) == len(ids)
            assert not trace.get("error") and not reason
            assert receipt["status"] == "0x1"
            assert row["storage_changes"] and row["watched_before"] != row["watched_after"]
            liquidation_topic = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
            assert len([log for log in logs_in(trace) if log["topics"][0] == liquidation_topic]) == len(ids)
            committed = [log for log in receipt["logs"] if log["topics"][0] == liquidation_topic]
            assert [int(log["topics"][1], 16) for log in committed] == list(ids)
            for position_id in ids:
                flag_slot = f"0x{position_slot(position_id) + 1:064x}"
                assert int(row["watched_before"][flag_slot], 16) >> 240 & 1
                assert not (int(row["watched_after"][flag_slot], 16) >> 240 & 1)
        else:
            assert trace.get("error") == "execution reverted"
            assert reason == REASONS[invalid_kind]
            assert oracle_calls[-1].get("error") == "execution reverted"
            assert not logs_in(trace) and row["storage_changes"] == {}
            assert row["receipt"]["status"] == "0x0" and row["receipt"]["logs"] == []
            assert row["watched_before"] == row["watched_after"]
            if name.startswith("mixed_good_then_"):
                assert len(settlement_calls) == 1
                path = [call.get("to", "").lower() for call in walk(trace)
                        if call.get("to", "").lower() in (ORACLE, TOKENOMICS)]
                assert path == [ORACLE, TOKENOMICS, ORACLE]
            else:
                assert not settlement_calls
        summaries.append({
            "name": name, "entrypoint": entrypoint, "requested_ids": list(ids),
            "oracle_assets_read": assets, "settlement_calls_before_result": len(settlement_calls),
            "revert_reason": reason, "receipt_status": row["receipt"]["status"], "committed_log_count": len(row["receipt"]["logs"]),
            "storage_change_contracts": sorted(row["storage_changes"]),
            "watched_exchange_slots_unchanged": row["watched_before"] == row["watched_after"],
        })
    return {
        "pin_block": PIN, "pin_hash": manifest["block_hash"],
        "raw_evidence": "../../artifacts/exchange_liquidation/invalid_prices.json",
        "case_count": len(summaries), "invalid_case_count": sum(x[5] is not None for x in CASES),
        "runtime_sha256": saved["runtime_sha256"], "watched_slots": saved["watched_slots"],
        "cases": summaries,
        "limits": [
            "HyperCore BBO returns are synthetic; the calls are local simulations at the pinned EVM state.",
            "The mock supplies prices or failures but has no update timestamp. These cases cannot establish data freshness or whether stale yet nonzero prices are rejected.",
            "Transaction receipts come from the next local block; read-only traces use the exact pinned block.",
            "Two active positions and six contract runtimes are checked, not every position or upgrade variant.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-rpc-url", help="Archive-backed local Anvil fork URL")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    result = build()
    SUMMARY.write_text(json.dumps(result, indent=2) + "\n")
    print("Invalid liquidation prices:", result["invalid_case_count"], "reverts and",
          result["case_count"] - result["invalid_case_count"], "success controls")


if __name__ == "__main__":
    main()
