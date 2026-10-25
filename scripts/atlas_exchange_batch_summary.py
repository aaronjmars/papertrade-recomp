#!/usr/bin/env python3
"""Decode the unnamed Exchange liquidation batch summary from saved logs and inputs."""

import argparse
import concurrent.futures
import json
import os
import pathlib

from atlas_tokenomics import EXCHANGE, PIN, rpc
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_batch_summary" / "recent_inputs.json"
SELECTOR = "0x599dc539"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SIGNATURE = "liquidateBatch(uint256[])"
SUMMARY_TOPIC = "0x0bb3f42f9fe304326ba30302693425c1db2e2f6a4675df44372fc0af5ce73706"
SUMMARY_SIGNATURE = "LiquidationBatchProcessed(uint256,uint256)"
LIQUIDATED_TOPIC = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
PARTIAL_TX = "0xdfe4d997bd2d8ee4d5a96d0759e38a6b24e9719c40545eae6ea406b43ed119f9"


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[index:index + 64], 16) for index in range(2, len(data), 64)]


def capture():
    if ARTIFACT.exists():
        return
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    logs = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    summaries = [log for log in logs if log["address"].lower() == EXCHANGE
                 and log["topics"][0] == SUMMARY_TOPIC]
    hashes = sorted({log["transactionHash"] for log in summaries})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        transactions = dict(zip(hashes, pool.map(
            lambda tx: rpc(url, "eth_getTransactionByHash", [tx]), hashes)))
    partial_trace = rpc(url, "debug_traceTransaction", [PARTIAL_TX,
        {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
    implementation = partial_trace["calls"][0]
    partial = {"root_error": partial_trace.get("error"),
               "implementation_error": implementation.get("error"),
               "implementation_logs": implementation.get("logs", []),
               "child_calls": [{"to": child["to"], "selector": child.get("input", "")[:10],
                                "error": child.get("error")} for child in implementation.get("calls", [])]}
    ARTIFACT.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                    "transactions": [{"tx": tx, "from": row["from"],
                                                      "to": row["to"], "input": row["input"]}
                                                     for tx, row in sorted(transactions.items())],
                                    "partial_trace": partial}, indent=2) + "\n")


def verify():
    assert "0x" + Keccak()(SUMMARY_SIGNATURE.encode()).hex() == SUMMARY_TOPIC
    assert "0x" + Keccak()(SIGNATURE.encode()).hex()[:8] == SELECTOR
    fixture = json.loads((ATLAS / "exchange_interface_evidence.json").read_text())
    assert any(row["selector"] == SELECTOR and row["signature"] == SIGNATURE
               for row in fixture["functions"])
    saved = json.loads(ARTIFACT.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    logs = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    by_tx = {}
    for log in logs:
        by_tx.setdefault(log["transactionHash"], []).append(log)
    summaries = [log for log in logs if log["address"].lower() == EXCHANGE
                 and log["topics"][0] == SUMMARY_TOPIC]
    transactions = {row["tx"]: row for row in saved["transactions"]}
    assert len(summaries) == len(transactions) == 26
    assert set(transactions) == {log["transactionHash"] for log in summaries}
    rows = []
    for summary in summaries:
        tx = summary["transactionHash"]
        transaction = transactions[tx]
        assert transaction["to"].lower() == EXCHANGE and transaction["input"][:10] == SELECTOR
        assert len(summary["topics"]) == 1
        encoded = words("0x" + transaction["input"][10:])
        assert encoded[0] == 32 and len(encoded) == 2 + encoded[1]
        requested_ids = encoded[2:]
        requested_count, completed_count = words(summary["data"])
        liquidated_ids = [int(log["topics"][1], 16) for log in by_tx[tx]
                          if log["address"].lower() == EXCHANGE
                          and log["topics"][0] == LIQUIDATED_TOPIC]
        assert requested_count == len(requested_ids)
        assert completed_count == len(liquidated_ids)
        assert len(liquidated_ids) == len(set(liquidated_ids))
        assert set(liquidated_ids).issubset(set(requested_ids))
        rows.append({"tx": tx, "block_number": int(summary["blockNumber"], 16),
                     "requested_ids": requested_ids, "liquidated_ids": liquidated_ids,
                     "summary_data": summary["data"],
                     "requested_count": requested_count, "completed_count": completed_count})
    partial_rows = [row for row in rows if row["completed_count"] < row["requested_count"]]
    assert len(partial_rows) == 1 and partial_rows[0]["tx"] == PARTIAL_TX
    assert partial_rows[0]["requested_ids"] == [1392363, 1394076, 1394080]
    assert partial_rows[0]["liquidated_ids"] == [1392363]
    trace = saved["partial_trace"]
    assert trace["root_error"] is None and trace["implementation_error"] is None
    assert [log["topics"][0] for log in trace["implementation_logs"]] == [
        LIQUIDATED_TOPIC, SUMMARY_TOPIC]
    assert [child["selector"] for child in trace["child_calls"]] == [
        "0xc0182669", "0x0efdf838"]
    assert all(child["error"] is None for child in trace["child_calls"])
    result = {"pin_block": PIN, "pin_hash": manifest["block_hash"],
              "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION,
              "selector": SELECTOR, "selector_reconstructions": {SELECTOR: SIGNATURE},
              "signature_evidence": "Exact hash, pinned public ABI fixture, and 26 archived direct ABI inputs",
              "summary_topic0": SUMMARY_TOPIC, "liquidated_topic0": LIQUIDATED_TOPIC,
              "summary_signature": SUMMARY_SIGNATURE,
              "summary_layout": "unindexed uint256 requestedCount, uint256 completedCount",
              "event_catalog": [{"topic0": SUMMARY_TOPIC,
                                 "reconstructed_signature": SUMMARY_SIGNATURE,
                                 "status": "observed_historical"}],
              "transaction_count": len(rows),
              "requested_position_count": sum(row["requested_count"] for row in rows),
              "completed_position_count": sum(row["completed_count"] for row in rows),
              "partial_batch": partial_rows[0], "rows": sorted(rows, key=lambda row: row["tx"]),
              "limits": ["All 26 sampled batch outcomes are checked against transaction-prestate price thresholds in exchange_batch_thresholds_behavior.json; inactive and mixed-instrument paths remain untested.",
                         "The 256-block sample does not establish all liquidation batch branches."]}
    (ATLAS / "exchange_batch_summary_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange liquidation batch summary:", len(rows), "transactions,",
          result["requested_position_count"], "requested,",
          result["completed_position_count"], "completed")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
