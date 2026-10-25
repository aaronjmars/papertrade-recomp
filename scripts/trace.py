#!/usr/bin/env python3
"""Save historical HyperEVM transaction call traces and receipts.

Set PAPERTRADE_ARCHIVE_RPC to an archive endpoint. The endpoint URL is never
written to an artifact because it may contain an API key.
"""

import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "historical"
RPC = os.environ.get("PAPERTRADE_ARCHIVE_RPC")


def rpc(method, params):
    if not RPC:
        raise SystemExit("set PAPERTRADE_ARCHIVE_RPC to an archive HyperEVM endpoint")
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(RPC, data=payload, headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def summarize_call(call, depth=0):
    line = {
        "depth": depth,
        "type": call.get("type"),
        "from": call.get("from"),
        "to": call.get("to"),
        "selector": call.get("input", "")[:10],
        "gas_used": call.get("gasUsed"),
        "error": call.get("error"),
    }
    lines = [line]
    for child in call.get("calls", []):
        lines.extend(summarize_call(child, depth + 1))
    return lines


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: trace.py TX_HASH [TX_HASH ...]")
    OUT.mkdir(parents=True, exist_ok=True)
    for tx_hash in sys.argv[1:]:
        if not tx_hash.startswith("0x") or len(tx_hash) != 66:
            raise ValueError(f"invalid transaction hash: {tx_hash}")
        receipt = rpc("eth_getTransactionReceipt", [tx_hash])
        trace = rpc("debug_traceTransaction", [tx_hash, {"tracer": "callTracer"}])
        state_diff = rpc("debug_traceTransaction", [tx_hash, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
        if not receipt or not trace:
            raise ValueError(f"missing receipt or trace: {tx_hash}")
        stem = OUT / tx_hash
        (stem.with_suffix(".receipt.json")).write_text(json.dumps(receipt, indent=2) + "\n")
        (stem.with_suffix(".calls.json")).write_text(json.dumps(trace, indent=2) + "\n")
        (stem.with_suffix(".state_diff.json")).write_text(json.dumps(state_diff, indent=2) + "\n")
        summary = {
            "hash": tx_hash,
            "block": int(receipt["blockNumber"], 16),
            "status": int(receipt["status"], 16),
            "calls": summarize_call(trace),
            "logs": [{"address": log["address"], "topic0": log["topics"][0] if log["topics"] else None} for log in receipt["logs"]],
        }
        (stem.with_suffix(".summary.json")).write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps({"hash": tx_hash, "block": summary["block"], "status": summary["status"], "calls": len(summary["calls"])}))


if __name__ == "__main__":
    main()
