#!/usr/bin/env python3
"""Check all sampled historical liquidation batches against prestate price thresholds."""

import argparse
import concurrent.futures
import json
import os
from pathlib import Path

from atlas_exchange_positions import EXCHANGE, position_slot, rpc
from atlas_exchange_liquidation_price import calculate
from atlas_exchange_queue_layout import mapped

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_batch_thresholds"
OUT = ATLAS / "exchange_batch_thresholds_behavior.json"
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
BBO = "0x000000000000000000000000000000000000080e"
LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
SUMMARY = "0x0bb3f42f9fe304326ba30302693425c1db2e2f6a4675df44372fc0af5ce73706"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"


def read(path):
    return json.loads(path.read_text())


def walk(node):
    yield node
    for child in node.get("calls", []):
        yield from walk(child)


def artifact(tx, suffix):
    return ARTIFACTS / f"{tx}.{suffix}.json"


def capture_one(url, row):
    tx = row["tx"]
    requested = (
        ("prestate", "debug_traceTransaction", [tx, {"tracer": "prestateTracer"}]),
        ("calls", "debug_traceTransaction",
         [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
        ("receipt", "eth_getTransactionReceipt", [tx]),
    )
    for suffix, method, params in requested:
        path = artifact(tx, suffix)
        if not path.exists():
            path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")
    receipt = read(artifact(tx, "receipt"))
    assert receipt["transactionHash"].lower() == tx
    assert int(receipt["blockNumber"], 16) == row["block_number"]
    header_path = artifact(tx, "block")
    if not header_path.exists():
        header_path.write_text(json.dumps(rpc(url, "eth_getBlockByHash",
                                              [receipt["blockHash"], False]), indent=2) + "\n")
    return tx


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read(ATLAS / "manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(manifest["block"]), False])["hash"].lower() == manifest["block_hash"]
    rows = read(ATLAS / "exchange_batch_summary_behavior.json")["rows"]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for tx in pool.map(lambda row: capture_one(url, row), rows):
            print("captured", tx[:10], flush=True)


def build():
    manifest = read(ATLAS / "manifest.json")
    summary = read(ATLAS / "exchange_batch_summary_behavior.json")
    archived_inputs = {row["tx"]: row for row in read(
        ROOT / "artifacts" / "exchange_batch_summary" / "recent_inputs.json")["transactions"]}
    rows = []
    for source in summary["rows"]:
        tx = source["tx"]
        prestate = read(artifact(tx, "prestate"))
        trace = read(artifact(tx, "calls"))
        receipt = read(artifact(tx, "receipt"))
        header = read(artifact(tx, "block"))
        assert receipt["transactionHash"].lower() == tx
        assert receipt["status"] == "0x1"
        assert int(receipt["blockNumber"], 16) == source["block_number"]
        assert header["hash"].lower() == receipt["blockHash"].lower()
        assert int(header["number"], 16) == source["block_number"]
        assert header["transactions"][int(receipt["transactionIndex"], 16)].lower() == tx
        assert trace["to"].lower() == EXCHANGE and not trace.get("error")
        assert trace["input"].lower() == archived_inputs[tx]["input"].lower()
        assert trace["input"].startswith("0x599dc539")
        assert int(trace["output"], 16) == source["completed_count"]
        calls = list(walk(trace))
        oracle_calls = [call for call in calls if call.get("to", "").lower() == ORACLE
                        and call.get("input", "")[:10] == "0xc0182669"]
        assert len(oracle_calls) == 1 and not oracle_calls[0].get("error")
        instrument = int(oracle_calls[0]["input"][10:], 16)
        midpoint = int(oracle_calls[0]["output"], 16)
        bbo_calls = [call for call in calls if call.get("to", "").lower() == BBO]
        assert len(bbo_calls) == 1 and not bbo_calls[0].get("error")
        bbo = bytes.fromhex(bbo_calls[0]["output"][2:])
        assert len(bbo) == 64
        bid, ask = (int.from_bytes(bbo[i:i + 32], "big") for i in (0, 32))
        assert 0 < bid <= ask and midpoint == (bid + ask) // 2
        tokenomics_calls = [call for call in calls if call.get("to", "").lower() == TOKENOMICS
                            and call.get("input", "")[:10] == "0x0efdf838"]
        assert len(tokenomics_calls) == source["completed_count"]
        assert all(not call.get("error") for call in tokenomics_calls)
        logs = [log for log in receipt["logs"] if log["address"].lower() == EXCHANGE]
        liquidated = [int(log["topics"][1], 16) for log in logs
                      if log["topics"][0].lower() == LIQUIDATED]
        batch_logs = [log for log in logs if log["topics"][0].lower() == SUMMARY]
        assert liquidated == source["liquidated_ids"]
        assert len(batch_logs) == 1 and batch_logs[0]["data"].lower() == source["summary_data"].lower()
        for log in logs:
            if log["topics"][0].lower() == LIQUIDATED:
                assert int(log["data"][2:66], 16) == midpoint
        storage = prestate[EXCHANGE]["storage"]
        instrument_key = mapped(instrument, 7, 1)
        instrument_word = storage[instrument_key]
        rate = (int(instrument_word, 16) >> 120) & ((1 << 64) - 1)
        assert 0 < rate < 10**18
        positions = []
        for position_id in source["requested_ids"]:
            base = position_slot(position_id)
            key0, key1 = (f"0x{base + offset:064x}" for offset in (0, 1))
            word0, word1 = int(storage[key0], 16), int(storage[key1], 16)
            actual_instrument = (word0 >> 160) & 0xffffffff
            entry = word0 >> 192
            leverage = (word1 >> 128) & 0xffffffff
            side = (word1 >> 224) & 1
            active = (word1 >> 240) & 1
            assert actual_instrument == instrument and active == 1
            assert 0 < leverage
            threshold = calculate(entry, leverage, side, rate)
            eligible = midpoint <= threshold if side else midpoint >= threshold
            observed = position_id in liquidated
            assert eligible == observed, (tx, position_id, midpoint, threshold)
            positions.append({
                "position_id": position_id, "prestate_word0": storage[key0],
                "prestate_word1": storage[key1], "instrument": instrument,
                "entry_price": entry, "leverage": leverage,
                "side": "long" if side else "short", "active": bool(active),
                "maintenance_rate_1e18": rate, "liquidation_threshold": threshold,
                "midpoint": midpoint, "threshold_predicted_eligible": eligible,
                "historically_liquidated": observed,
            })
        rows.append({
            "tx": tx, "block_number": source["block_number"],
            "block_hash": receipt["blockHash"].lower(),
            "transaction_index": int(receipt["transactionIndex"], 16),
            "instrument": instrument, "oracle_midpoint": midpoint,
            "hypercore_bbo": {"bid": bid, "ask": ask},
            "instrument_word1": instrument_word,
            "requested_count": len(positions),
            "predicted_count": sum(item["threshold_predicted_eligible"] for item in positions),
            "liquidated_count": len(liquidated), "positions": positions,
        })
    assert len(rows) == 26
    assert sum(row["requested_count"] for row in rows) == 69
    assert sum(row["predicted_count"] for row in rows) == 67
    assert sum(row["liquidated_count"] for row in rows) == 67
    assert {row["instrument"] for row in rows} == {0, 1}
    assert sum(item["side"] == "short" for row in rows for item in row["positions"]) == 69
    return {
        "pin_block": manifest["block"], "pin_hash": manifest["block_hash"],
        "sample_window": "last 256 blocks ending at pin",
        "transaction_count": len(rows), "requested_position_count": 69,
        "active_position_count": 69, "oracle_call_count": 26,
        "oracle_instruments": [0, 1], "short_position_count": 69,
        "threshold_predicted_liquidation_count": 67,
        "historical_liquidation_count": 67,
        "mismatch_count": 0, "partial_transaction": summary["partial_batch"]["tx"],
        "raw_evidence_pattern": "../../artifacts/exchange_batch_thresholds/<tx>.(prestate|calls|receipt|block).json",
        "threshold_formula_evidence": "exchange_liquidation_price_behavior.json",
        "rows": rows,
        "limits": [
            "The 256-block sample covers 26 direct batches, two instruments, and only short positions.",
            "Every sampled position was active; inactive-ID and mixed-instrument batch paths remain untested.",
            "Threshold agreement with historical outcomes supports this branch but does not recover the original Solidity source.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange batches:", result["transaction_count"], "transactions,",
          result["requested_position_count"], "positions,",
          result["threshold_predicted_liquidation_count"], "predicted liquidations,",
          result["mismatch_count"], "mismatches")


if __name__ == "__main__":
    main()
