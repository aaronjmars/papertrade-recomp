#!/usr/bin/env python3
"""Replay every observed multisig interaction against its previous block state."""

import json
import pathlib

from trace import rpc, summarize_call

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORY = ROOT / "artifacts" / "historical"
MULTISIG = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"


def call_skeleton(trace):
    return [(x["type"], (x["to"] or "").lower(), x["selector"], bool(x["error"]))
            for x in summarize_call(trace)]


def trace_logs(trace):
    result = []

    def visit(node):
        for item in node.get("logs", []):
            result.append((item.get("address", "").lower(), tuple(item.get("topics", [])), item.get("data", "")))
        for child in node.get("calls", []):
            visit(child)

    visit(trace)
    return sorted(result)


def storage(diff):
    return {a.lower(): x.get("storage", {}) for a, x in diff.get("post", {}).items() if x.get("storage")}


rows = []
for explorer_row in json.loads((ATLAS / "multisig_txs.json").read_text()):
    if (explorer_row.get("to") or "").lower() != MULTISIG:
        continue
    tx_hash = explorer_row["hash"]
    tx = rpc("eth_getTransactionByHash", [tx_hash])
    block = int(tx["blockNumber"], 16)
    block_data = rpc("eth_getBlockByNumber", [hex(block), False])
    overrides = {"number": block_data["number"], "time": block_data["timestamp"]}
    for source, target in (("baseFeePerGas", "baseFeePerGas"), ("prevRandao", "prevRandao"), ("miner", "feeRecipient")):
        if block_data.get(source):
            overrides[target] = block_data[source]
    call = {key: tx[key] for key in ("from", "to", "input", "value", "gas")}
    actual = json.loads((HISTORY / f"{tx_hash}.calls.json").read_text())
    actual_diff = json.loads((HISTORY / f"{tx_hash}.state_diff.json").read_text())
    receipt = json.loads((HISTORY / f"{tx_hash}.receipt.json").read_text())
    call_options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}, "blockOverrides": overrides}
    diff_options = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}, "blockOverrides": overrides}
    replay = rpc("debug_traceCall", [call, hex(block - 1), call_options])
    replay_diff = rpc("debug_traceCall", [call, hex(block - 1), diff_options])
    actual_shape = call_skeleton(actual)
    replay_shape = call_skeleton(replay)
    actual_events = sorted((x["address"].lower(), tuple(x["topics"]), x["data"]) for x in receipt["logs"])
    replay_events = trace_logs(replay)
    actual_storage = storage(actual_diff)
    replay_storage = storage(replay_diff)
    rows.append({"tx": tx_hash, "block": block, "transaction_index": int(tx["transactionIndex"], 16),
                 "root_selector": tx["input"][:10], "block_overrides": overrides,
                 "call_skeleton_match": actual_shape == replay_shape,
                 "event_multiset_match": actual_events == replay_events,
                 "storage_post_match": actual_storage == replay_storage,
                 "historical_call_skeleton": actual_shape, "replay_call_skeleton": replay_shape,
                 "historical_event_count": len(actual_events), "replay_event_count": len(replay_events),
                 "historical_storage_post": actual_storage, "replay_storage_post": replay_storage})

assert len(rows) == 13
counts = {key: sum(x[key] for x in rows) for key in ("call_skeleton_match", "event_multiset_match", "storage_post_match")}
result = {"pin": 48902346, "method": "debug_traceCall at previous-block state with original block metadata overridden; earlier same-block transactions can cause divergence",
          "transaction_count": len(rows), "match_counts": counts, "rows": rows}
(ATLAS / "multisig_replays.json").write_text(json.dumps(result, indent=2) + "\n")
print(len(rows), "multisig transactions replayed", counts)
