#!/usr/bin/env python3
"""Verify sampled Exchange liquidation batch branches on a pinned archive fork."""

import argparse
import json
import os
from pathlib import Path

from atlas_exchange_liquidation import (
    BATCH_EXTRA_TOPIC, EXCHANGE, IMPLEMENTATION, KEEPER, LIQUIDATED, PIN, PRE_BBO,
    logs_in, position_slot, rpc, storage_only,
)
from atlas_oracle_behavior import returndata

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_liquidation" / "pinned_batch_branches.json"
OUT = ATLAS / "exchange_batch_branches_behavior.json"
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
POSITIONS = (1394473, 1394062, 1394058, 1394060)
CASES = (
    ("empty", (), 800000, ()),
    ("inactive_only", (0,), 800000, ()),
    ("eligible_only", (1394473,), 800000, (1394473,)),
    ("inactive_first", (0, 1394473), 800000, (1394473,)),
    ("inactive_last", (1394473, 0), 800000, (1394473,)),
    ("duplicate_eligible", (1394473, 1394473), 800000, (1394473,)),
    ("ineligible_only", (1394473,), 802000, ()),
    ("eligible_then_ineligible", (1394473, 1394062), 801700, (1394473,)),
    ("ineligible_then_eligible", (1394062, 1394473), 801700, (1394473,)),
    ("two_eligible", (1394473, 1394062), 801600, (1394473, 1394062)),
    ("long_only", (1394058, 1394060), 230400, (1394058,)),
    ("short_only", (1394058, 1394060), 242100, (1394060,)),
    ("short_first", (1394060, 1394058), 242100, (1394060,)),
    ("mixed_instruments", (1394473, 1394058), 800000, (1394473,)),
    ("mixed_instruments_reversed", (1394058, 1394473), 800000, (1394473,)),
)


def read(path):
    return json.loads(path.read_text())


def word(value):
    return value.to_bytes(32, "big").hex()


def calldata(ids):
    return "0x599dc539" + word(32) + word(len(ids)) + "".join(word(i) for i in ids)


def walk(node):
    yield node
    for child in node.get("calls", []):
        yield from walk(child)


def capture(url):
    manifest = read(ATLAS / "manifest.json")
    archive = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    block_hashes = {name: rpc(endpoint, "eth_getBlockByNumber", [hex(PIN), False])["hash"].lower()
                    for name, endpoint in (("archive", archive), ("local", url))}
    assert set(block_hashes.values()) == {manifest["block_hash"]}
    words = {}
    for position_id in POSITIONS:
        slot = hex(position_slot(position_id) + 1)
        words[str(position_id)] = {
            name: rpc(endpoint, "eth_getStorageAt", [EXCHANGE, slot, hex(PIN)])
            for name, endpoint in (("archive", archive), ("local", url))
        }
        assert words[str(position_id)]["archive"] == words[str(position_id)]["local"]
        assert int(words[str(position_id)]["local"], 16) >> 240 & 1
    rows = []
    for name, ids, price, expected in CASES:
        code = returndata(price, price)
        rpc(url, "anvil_setCode", [PRE_BBO, code])
        request = {"from": KEEPER, "to": EXCHANGE, "data": calldata(ids), "gas": "0x5b8d80"}
        trace = rpc(url, "debug_traceCall", [request, hex(PIN),
                        {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        diff = rpc(url, "debug_traceCall", [request, hex(PIN),
                       {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
        rows.append({
            "name": name, "ids": list(ids), "mock_price": price,
            "mock_runtime_code": code, "calldata": request["data"],
            "expected_liquidated": list(expected),
            "trace": trace, "storage_changes": storage_only(diff),
        })
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "pin_block": PIN, "pin_hash": manifest["block_hash"],
        "method": "read-only debug_traceCall on archive-backed Anvil fork with fixed HyperCore BBO runtime",
        "provider_crosscheck": {"block_hashes": block_hashes, "position_words": words},
        "cases": rows,
    }, indent=2) + "\n")


def build():
    manifest = read(ATLAS / "manifest.json")
    saved = read(ARTIFACT)
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert set(saved["provider_crosscheck"]["block_hashes"].values()) == {manifest["block_hash"]}
    for pair in saved["provider_crosscheck"]["position_words"].values():
        assert pair["archive"] == pair["local"] and int(pair["local"], 16) >> 240 & 1
    assert len(saved["cases"]) == len(CASES)
    cases = []
    for row, (name, ids, price, expected) in zip(saved["cases"], CASES):
        assert (row["name"], row["ids"], row["mock_price"], row["expected_liquidated"]) == (
            name, list(ids), price, list(expected))
        assert row["mock_runtime_code"] == returndata(price, price)
        assert row["calldata"] == calldata(ids)
        trace = row["trace"]
        assert not trace.get("error") and trace["to"].lower() == EXCHANGE
        assert trace["input"].lower() == row["calldata"].lower()
        assert len(trace.get("calls", [])) == 1
        assert trace["calls"][0]["to"].lower() == IMPLEMENTATION
        assert trace["calls"][0]["input"].startswith("0x599dc539")
        assert int(trace["output"], 16) == len(expected)
        logs = logs_in(trace)
        exchange_logs = [log for log in logs if log["address"].lower() == EXCHANGE]
        liquidation_logs = [log for log in exchange_logs if log["topics"][0] == LIQUIDATED]
        summary_logs = [log for log in exchange_logs if log["topics"][0] == BATCH_EXTRA_TOPIC]
        assert [int(log["topics"][1], 16) for log in liquidation_logs] == list(expected)
        assert all(int(log["data"][2:66], 16) == price for log in liquidation_logs)
        assert len(summary_logs) == 1
        summary = summary_logs[0]["data"]
        assert (int(summary[2:66], 16), int(summary[66:130], 16)) == (len(ids), len(expected))
        calls = list(walk(trace))
        oracle = [call for call in calls if call.get("to", "").lower() == ORACLE
                  and call.get("input", "")[:10] == "0xc0182669"]
        oracle_instruments = [int(call["input"][10:], 16) for call in oracle]
        assert len(oracle_instruments) == len(set(oracle_instruments))
        assert all(not call.get("error") and int(call["output"], 16) == price for call in oracle)
        tokenomics = [call for call in calls if call.get("to", "").lower() == TOKENOMICS
                      and call.get("input", "")[:10] == "0x0efdf838"]
        assert len(tokenomics) == len(expected) and all(not call.get("error") for call in tokenomics)
        if name == "empty" or name == "inactive_only":
            assert not oracle and not row["storage_changes"]
        if name == "duplicate_eligible":
            assert len(oracle) == 1 and len(liquidation_logs) == 1
        if name.startswith("mixed_instruments"):
            assert len(oracle) == 2
            assert oracle_instruments == ([0, 1] if name == "mixed_instruments" else [1, 0])
        for position_id in expected:
            slot = f"0x{position_slot(position_id) + 1:064x}"
            change = row["storage_changes"][EXCHANGE]
            assert int(change["pre"][slot], 16) - int(change["post"][slot], 16) == 1 << 240
        cases.append({
            "name": name, "requested_ids": list(ids), "mock_price": price,
            "liquidated_ids": list(expected), "return_count": len(expected),
            "summary_counts": [len(ids), len(expected)],
            "oracle_instruments": oracle_instruments,
            "tokenomics_call_count": len(tokenomics),
            "storage_write_contracts": sorted(row["storage_changes"]),
        })
    return {
        "pin_block": PIN, "pin_hash": manifest["block_hash"],
        "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION,
        "selector": "0x599dc539", "signature": "liquidateBatch(uint256[])",
        "raw_evidence": "../../artifacts/exchange_liquidation/pinned_batch_branches.json",
        "case_count": len(cases), "cases": cases,
        "observed_branches": [
            "empty array succeeds and emits summary (0,0)",
            "inactive ID is skipped without a revert",
            "duplicate eligible ID is liquidated once",
            "ineligible active ID is skipped without a revert",
            "long and short positions each follow sampled price boundaries",
            "mixed-instrument arrays cause one Oracle read per instrument in request order",
        ],
        "limits": [
            "Cases are read-only simulations with fixed synthetic HyperCore BBO prices.",
            "The mixed-instrument mock returns the same price for both instruments.",
            "Large arrays, invalid ABI encoding, and all combinations of inactive and eligible IDs remain untested.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-rpc-url", help="Archive-backed local Anvil fork URL")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    behavior = build()
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("Exchange liquidation batch branches:", behavior["case_count"], "cases")


if __name__ == "__main__":
    main()
