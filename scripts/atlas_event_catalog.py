#!/usr/bin/env python3
"""Summarize observed events and their root transaction selectors."""

import collections
import json
import pathlib

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
logs = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
grouped = collections.defaultdict(list)
for log in logs:
    if log["topics"]:
        grouped[(log["address"].lower(), log["topics"][0].lower())].append(log)

txs = {}
events = []
for (address, topic), rows in sorted(grouped.items()):
    samples = []
    for log in (rows[0], rows[-1]):
        tx_hash = log["transactionHash"]
        if tx_hash not in txs:
            tx = rpc("eth_getTransactionByHash", [tx_hash])
            txs[tx_hash] = {"hash": tx_hash, "to": tx["to"], "input_selector": tx["input"][:10], "block": int(tx["blockNumber"], 16)}
        samples.append({"tx": tx_hash, "block": int(log["blockNumber"], 16), "topic_count": len(log["topics"]), "data_bytes": (len(log["data"]) - 2) // 2, "root_transaction": txs[tx_hash]})
    runtime_hits = []
    for contract_address, contract in manifest["contracts"].items():
        if contract["role"].endswith("_proxy"):
            continue
        if topic[2:] in (ATLAS / contract["runtime_file"]).read_text().lower():
            runtime_hits.append({"address": contract_address, "role": contract["role"]})
    events.append({"emitter": address, "emitter_role": manifest["contracts"][address]["role"], "topic0": topic, "count_last_256_blocks": len(rows), "sample": samples, "runtime_constant_hits": runtime_hits})
    print(manifest["contracts"][address]["role"], topic[:10], len(rows), flush=True)

(ATLAS / "event_catalog.json").write_text(json.dumps({"window": [48902090, 48902346], "events": events}, indent=2) + "\n")
