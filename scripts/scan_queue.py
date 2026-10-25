#!/usr/bin/env python3
"""Find Papertrade queued-profit events in a HyperEVM block range."""

import json
import os
import pathlib
import sys
import urllib.request

RPC = os.environ.get("PAPERTRADE_ARCHIVE_RPC")
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
QUEUED_PROFIT_TOPIC = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
OUT = pathlib.Path(__file__).resolve().parents[1] / "artifacts" / "historical" / "queue_scan.json"


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


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: scan_queue.py FROM_BLOCK TO_BLOCK")
    start, stop = map(int, sys.argv[1:])
    if start > stop:
        raise ValueError("FROM_BLOCK must not exceed TO_BLOCK")
    chunks = []
    events = []
    for lo in range(start, stop + 1, 1000):
        hi = min(lo + 999, stop)
        logs = rpc("eth_getLogs", [{"address": EXCHANGE, "topics": [QUEUED_PROFIT_TOPIC],
                                    "fromBlock": hex(lo), "toBlock": hex(hi)}])
        chunks.append({"from": lo, "to": hi, "queued_profit_events": len(logs)})
        for log in logs:
            if len(log["data"]) != 66:
                raise ValueError(f"unexpected queued-profit event at {log['transactionHash']}")
            events.append({"block": int(log["blockNumber"], 16),
                           "transaction_hash": log["transactionHash"],
                           "log_index": int(log["logIndex"], 16),
                           "queued_profit_usd_wei": str(int(log["data"], 16)),
                           "topics": log["topics"]})
        print(f"{lo}-{hi}: {len(logs)} queued-profit events", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"from": start, "to": stop, "topic": QUEUED_PROFIT_TOPIC,
                               "chunks": chunks, "events": events}, indent=2) + "\n")
    print(f"saved {len(events)} events to {OUT}")


if __name__ == "__main__":
    main()
