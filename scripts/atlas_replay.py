#!/usr/bin/env python3
"""Compare read-only pre-block calls with recorded Papertrade transactions."""

import json
import pathlib

from trace import rpc, summarize_call

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HASHES = [
    "0xddf30f3fd0d78c0516e37f32ed1ece2ef4ab488d7b4be8439c7196878047fb2e",  # factory CREATE2
    "0xf7dfd1a2d3d5950aa92e398e03c3de33c9e8e23dfae0d214ecb001759b1fcc9b",  # first-in-block batch
    "0xd4ee56dd5d1e271b8fc142e340362d3ab1eede92a9810ab33de4d90a9f798257",  # request sweep
    "0x34b7ae5b487e74118446994402ec8f4651a1414ad1de75dcfe1f8267cc9854b9",  # liquidate batch
    "0x324a3b9eb75351965b220c16095b56b053f91fbda37525202051604fbd618f7d",
    "0x2f9333500c9e715e4c974f2c6bc7bb20ad3897ad6135d6d9788805fec95dc4e8",  # index-2 sweep finalization
    "0xc6a5c27f6be82e15d1e1654888e0957ee67475a3de5deee56a95fd685033462b",  # PAPER approve
]


def skeleton(trace):
    return [(x["type"], (x["to"] or "").lower(), x["selector"]) for x in summarize_call(trace)]


def logs(trace):
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


def same_block_storage_prestate(tx_hash, tx, block):
    """Restore touched slots changed by earlier transactions in one sampled block."""
    if tx_hash != "0x2f9333500c9e715e4c974f2c6bc7bb20ad3897ad6135d6d9788805fec95dc4e8":
        return {}, []
    parent = hex(int(tx["blockNumber"], 16) - 1)
    prestate = rpc("debug_traceTransaction", [tx_hash, {"tracer": "prestateTracer"}])
    changes = []
    overrides = {}
    for address, account in prestate.items():
        for slot, value in account.get("storage", {}).items():
            previous = rpc("eth_getStorageAt", [address, slot, parent])
            if int(previous, 16) == int(value, 16):
                continue
            changes.append({"address": address.lower(), "slot": slot, "parent": previous, "pre_transaction": value})
            overrides.setdefault(address, {"stateDiff": {}})["stateDiff"][slot] = value
    assert len(changes) == 1, "the sampled sweep should have exactly one changed touched slot"
    block_hashes = rpc("eth_getBlockByNumber", [block["number"], False])["transactions"]
    prior_hashes = block_hashes[:int(tx["transactionIndex"], 16)]
    assert len(prior_hashes) == 2
    current = changes[0]["parent"]
    prior_writes = []
    for prior_hash in prior_hashes:
        diff = rpc("debug_traceTransaction", [prior_hash, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
        address, slot = changes[0]["address"], changes[0]["slot"]
        before = diff.get("pre", {}).get(address, {}).get("storage", {}).get(slot)
        after = diff.get("post", {}).get(address, {}).get("storage", {}).get(slot)
        assert before is not None and after is not None and int(before, 16) == int(current, 16)
        prior_writes.append({"tx": prior_hash, "before": before, "after": after})
        current = after
    assert int(current, 16) == int(changes[0]["pre_transaction"], 16)
    changes[0]["earlier_same_block_writes"] = prior_writes
    return overrides, changes


rows = []
for tx_hash in HASHES:
    tx = rpc("eth_getTransactionByHash", [tx_hash])
    block = int(tx["blockNumber"], 16)
    block_data = rpc("eth_getBlockByNumber", [hex(block), False])
    block_override = {"number": block_data["number"], "time": block_data["timestamp"]}
    if block_data.get("baseFeePerGas"):
        block_override["baseFeePerGas"] = block_data["baseFeePerGas"]
    if block_data.get("prevRandao"):
        block_override["prevRandao"] = block_data["prevRandao"]
    if block_data.get("miner"):
        block_override["feeRecipient"] = block_data["miner"]
    call = {key: tx[key] for key in ("from", "to", "input", "value", "gas")}
    state_overrides, same_block_prestate = same_block_storage_prestate(tx_hash, tx, block_data)
    replay_config = {"blockOverrides": block_override}
    if state_overrides:
        replay_config["stateOverrides"] = state_overrides
    opts = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
    actual = rpc("debug_traceTransaction", [tx_hash, opts])
    replay = rpc("debug_traceCall", [call, hex(block - 1), {**opts, **replay_config}])
    diff_opts = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
    actual_diff = rpc("debug_traceTransaction", [tx_hash, diff_opts])
    replay_diff = rpc("debug_traceCall", [call, hex(block - 1), {**diff_opts, **replay_config}])
    row = {
        "tx": tx_hash, "block": block, "transaction_index": int(tx["transactionIndex"], 16),
        "block_override": block_override, "same_block_storage_prestate": same_block_prestate,
        "selector": tx["input"][:10], "to": tx["to"],
        "actual_error": actual.get("error"), "replay_error": replay.get("error"),
        "actual_call_count": len(skeleton(actual)), "replay_call_count": len(skeleton(replay)),
        "call_skeleton_equal": skeleton(actual) == skeleton(replay),
        "actual_log_count": len(logs(actual)), "replay_log_count": len(logs(replay)),
        "log_multiset_equal": logs(actual) == logs(replay),
        "contract_storage_changes_equal": storage(actual_diff) == storage(replay_diff),
        "actual_storage_post": storage(actual_diff), "replay_storage_post": storage(replay_diff),
    }
    rows.append(row)
    print(tx_hash[:10], row["call_skeleton_equal"], row["log_multiset_equal"], row["contract_storage_changes_equal"], flush=True)

(ATLAS / "replay_comparisons.json").write_text(json.dumps({"method": "debug_traceCall on previous block state with original block number, timestamp, base fee and fee recipient overridden; the index-2 sweep replay also restores its sole changed touched storage slot using the original transaction prestate, checked against both earlier same-block writes", "comparisons": rows}, indent=2) + "\n")
