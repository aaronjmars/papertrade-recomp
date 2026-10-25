#!/usr/bin/env python3
"""Verify Staking distribution with a positive synthetic unallocated balance."""

import argparse
import json
from pathlib import Path

from trace import rpc, summarize_call

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "staking_unallocated"
OUT = ATLAS / "staking_unallocated_behavior.json"
TX = "0xd5a907988c178cb4fe55b8f3a8b87080eb3869e16ac548a8b9f7aa4a871a17c0"
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
SELECTOR = "0xf0355460"
TOPIC = "0xf7576d8c2653e9d07af5ef229acf59b339e327d4e0eaddb4a96615534cf148f8"
SLOT5 = "0x" + f"{5:064x}"
SLOT6 = "0x" + f"{6:064x}"
SLOT7 = "0x" + f"{7:064x}"
SLOT8 = "0x" + f"{8:064x}"
UNALLOCATED = 10**18
PRECISION = 10**27


def read(path):
    return json.loads(path.read_text())


def write_if_missing(name, value):
    path = ARTIFACTS / name
    if not path.exists():
        path.write_text(json.dumps(value, indent=2) + "\n")


def descendants(call):
    yield call
    for child in call.get("calls", []):
        yield from descendants(child)


def signed_call(root):
    calls = [call for call in descendants(root) if call.get("to", "").lower() == STAKING
             and call.get("input", "").startswith(SELECTOR)]
    assert len(calls) == 1
    return calls[0]


def skeleton(trace):
    return [(row["type"], (row["to"] or "").lower(), row["selector"], row["error"])
            for row in summarize_call(trace)]


def logs(trace):
    return [(row["address"].lower(), tuple(row["topics"]), row["data"])
            for call in descendants(trace) for row in call.get("logs", [])]


def distributed(trace):
    found = [row for row in logs(trace) if row[0] == STAKING and row[1][0].lower() == TOPIC]
    assert len(found) == 1
    data = found[0][2]
    assert len(data) == 2 + 4 * 64
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def child_call(root):
    child = signed_call(root)
    return {"from": child["from"], "to": STAKING, "input": child["input"],
            "value": child.get("value", "0x0"), "gas": "0x1000000"}


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    manifest = read(ATLAS / "manifest.json")
    pin = rpc("eth_getBlockByNumber", [hex(manifest["block"]), False])
    assert pin["hash"].lower() == manifest["block_hash"]
    receipt = read(ROOT / "artifacts" / "tokenomics" / f"{TX}.receipt.json")
    assert int(receipt["transactionIndex"], 16) == 0
    tx = rpc("eth_getTransactionByHash", [TX])
    block = int(tx["blockNumber"], 16)
    header = rpc("eth_getBlockByNumber", [hex(block), False])
    assert header["hash"] == receipt["blockHash"] and block < manifest["block"]
    overrides = {"number": header["number"], "time": header["timestamp"]}
    for original, target in (("baseFeePerGas", "baseFeePerGas"),
                             ("prevRandao", "prevRandao"), ("miner", "feeRecipient")):
        if header.get(original):
            overrides[target] = header[original]
    root_call = {key: tx[key] for key in ("from", "to", "input", "value", "gas")}
    if not (ARTIFACTS / "baseline_replay.json").exists():
        replay = rpc("debug_traceCall", [root_call, hex(block - 1),
            {"tracer": "callTracer", "tracerConfig": {"withLog": True},
             "blockOverrides": overrides}])
        write_if_missing("baseline_replay.json", {"tx": TX, "block": block,
            "block_hash": header["hash"], "block_overrides": overrides,
            "call": root_call, "trace": replay})
    original = read(ROOT / "artifacts" / "tokenomics" / f"{TX}.calls.json")
    call = child_call(original)
    assert int(rpc("eth_getStorageAt", [STAKING, SLOT8, hex(block - 1)]), 16) == 0
    states = {"base": {}, "alt": {SLOT8: UNALLOCATED},
              "zero_stakers": {SLOT5: 0},
              "zero_stakers_with_prior": {SLOT5: 0, SLOT8: UNALLOCATED}}
    for name, storage in states.items():
        state = {"stateOverrides": {STAKING: {"stateDiff": {
            slot: "0x" + f"{value:064x}" for slot, value in storage.items()}}}} if storage else {}
        options = {"blockOverrides": overrides, **state}
        trace_path = ARTIFACTS / f"{name}_child.json"
        if not trace_path.exists():
            trace = rpc("debug_traceCall", [call, hex(block - 1),
                {"tracer": "callTracer", "tracerConfig": {"withLog": True}, **options}])
            write_if_missing(f"{name}_child.json", trace)
        diff_path = ARTIFACTS / f"{name}_child_diff.json"
        if not diff_path.exists():
            diff = rpc("debug_traceCall", [call, hex(block - 1),
                {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}, **options}])
            write_if_missing(f"{name}_child_diff.json", diff)
    getter_path = ARTIFACTS / "zero_stakers_getter.json"
    if not getter_path.exists():
        override = {STAKING: {"stateDiff": {SLOT5: "0x" + f"{0:064x}",
            SLOT8: "0x" + f"{UNALLOCATED:064x}"}}}
        getter = rpc("eth_call", [{"to": STAKING, "data": "0x817b1cd2"}, hex(block - 1), override])
        write_if_missing("zero_stakers_getter.json", {"block": block - 1,
            "total_staked_override": getter, "slot5": SLOT5, "slot8": SLOT8,
            "unallocated_override": "0x" + f"{UNALLOCATED:064x}"})
    print("captured Staking positive-unallocated and zero-staker branches")


def build():
    manifest = read(ATLAS / "manifest.json")
    receipt = read(ROOT / "artifacts" / "tokenomics" / f"{TX}.receipt.json")
    original = read(ROOT / "artifacts" / "tokenomics" / f"{TX}.calls.json")
    prestate = read(ROOT / "artifacts" / "staking" / f"{TX}.prestate.json")
    root_replay = read(ARTIFACTS / "baseline_replay.json")
    assert int(receipt["status"], 16) == 1 and int(receipt["transactionIndex"], 16) == 0
    assert root_replay["tx"] == TX and root_replay["block_hash"] == receipt["blockHash"]
    assert root_replay["block"] < manifest["block"]
    assert root_replay["call"]["input"] == original["input"]
    assert skeleton(original) == skeleton(root_replay["trace"])
    assert sorted(logs(original)) == sorted(logs(root_replay["trace"]))
    historical_child = signed_call(original)
    base_trace = read(ARTIFACTS / "base_child.json")
    alt_trace = read(ARTIFACTS / "alt_child.json")
    assert not base_trace.get("error") and not alt_trace.get("error")
    assert base_trace["to"].lower() == alt_trace["to"].lower() == STAKING
    assert base_trace["from"].lower() == alt_trace["from"].lower() == historical_child["from"].lower()
    assert base_trace["input"] == alt_trace["input"] == historical_child["input"]
    assert skeleton(base_trace) == skeleton(alt_trace) == skeleton(historical_child)
    assert logs(base_trace) == logs(historical_child)
    base_logs = logs(base_trace)
    alt_logs = logs(alt_trace)
    assert len(base_logs) == len(alt_logs) == 5
    assert [(i, row) for i, row in enumerate(base_logs) if row != alt_logs[i]][0][0] == 1
    assert sum(row != alt_logs[i] for i, row in enumerate(base_logs)) == 1
    base_fields, alt_fields = distributed(base_trace), distributed(alt_trace)
    total_staked = int(prestate[STAKING]["storage"][SLOT5], 16)
    assert total_staked > 0 and int(prestate[STAKING]["storage"][SLOT8], 16) == 0
    assert base_fields[1] == base_fields[2]
    assert alt_fields[0] == base_fields[0] and alt_fields[1] == base_fields[1]
    assert alt_fields[2] == base_fields[2] + UNALLOCATED
    accumulator_delta = UNALLOCATED * PRECISION // total_staked
    assert alt_fields[3] == base_fields[3] + accumulator_delta
    base_diff = read(ARTIFACTS / "base_child_diff.json")
    alt_diff = read(ARTIFACTS / "alt_child_diff.json")
    base_pre = base_diff["pre"][STAKING]["storage"]
    alt_pre = alt_diff["pre"][STAKING]["storage"]
    base_post = base_diff["post"][STAKING]["storage"]
    alt_post = alt_diff["post"][STAKING]["storage"]
    assert SLOT8 not in base_pre and SLOT8 not in base_post
    assert int(alt_pre[SLOT8], 16) == UNALLOCATED and SLOT8 not in alt_post
    assert int(base_post[SLOT6], 16) == base_fields[3]
    assert int(alt_post[SLOT6], 16) == alt_fields[3]
    assert int(base_post[SLOT7], 16) == int(alt_post[SLOT7], 16) == base_fields[0]
    assert {key: value for key, value in base_post.items() if key != SLOT6} == {
        key: value for key, value in alt_post.items() if key != SLOT6}
    assert {key: value for key, value in base_diff["post"].items() if key != STAKING} == {
        key: value for key, value in alt_diff["post"].items() if key != STAKING}
    zero_trace = read(ARTIFACTS / "zero_stakers_child.json")
    zero_prior_trace = read(ARTIFACTS / "zero_stakers_with_prior_child.json")
    assert not zero_trace.get("error") and not zero_prior_trace.get("error")
    assert skeleton(zero_trace) == skeleton(zero_prior_trace) == skeleton(base_trace)
    zero_logs = logs(zero_trace)
    assert logs(zero_prior_trace) == zero_logs and len(zero_logs) == len(base_logs)
    assert [(i, row) for i, row in enumerate(base_logs) if row != zero_logs[i]][0][0] == 1
    assert sum(row != zero_logs[i] for i, row in enumerate(base_logs)) == 1
    zero_fields = distributed(zero_trace)
    zero_prior_fields = distributed(zero_prior_trace)
    assert zero_fields == zero_prior_fields
    assert zero_fields == [base_fields[0], base_fields[1], 0,
                           int(prestate[STAKING]["storage"][SLOT6], 16)]
    zero_diff = read(ARTIFACTS / "zero_stakers_diff.json")
    zero_prior_diff = read(ARTIFACTS / "zero_stakers_with_prior_diff.json")
    zero_post = zero_diff["post"][STAKING]["storage"]
    zero_prior_post = zero_prior_diff["post"][STAKING]["storage"]
    assert SLOT6 not in zero_post and SLOT6 not in zero_prior_post
    assert int(zero_post[SLOT7], 16) == int(zero_prior_post[SLOT7], 16) == base_fields[0]
    assert int(zero_post[SLOT8], 16) == base_fields[1]
    assert int(zero_prior_diff["pre"][STAKING]["storage"][SLOT8], 16) == UNALLOCATED
    assert int(zero_prior_post[SLOT8], 16) == base_fields[1] + UNALLOCATED
    assert {key: value for key, value in zero_diff["post"].items() if key != STAKING} == {
        key: value for key, value in base_diff["post"].items() if key != STAKING} == {
        key: value for key, value in zero_prior_diff["post"].items() if key != STAKING}
    getter = read(ARTIFACTS / "zero_stakers_getter.json")
    assert getter["block"] == root_replay["block"] - 1 and getter["slot5"] == SLOT5
    assert getter["slot8"] == SLOT8 and int(getter["unallocated_override"], 16) == UNALLOCATED
    assert int(getter["total_staked_override"], 16) == 0
    result = {"pin": manifest["block"], "block_hash": manifest["block_hash"],
              "transaction": TX, "transaction_block": root_replay["block"],
              "transaction_block_hash": root_replay["block_hash"],
              "transaction_index": 0, "staking_proxy": STAKING, "selector": SELECTOR,
              "baseline_root_call_count": len(skeleton(original)),
              "baseline_root_log_count": len(logs(original)),
              "isolated_child_call_count": len(skeleton(base_trace)),
              "isolated_child_log_count": len(base_logs),
              "baseline_distributed_event_words": base_fields,
              "unallocated_override": UNALLOCATED,
              "override_distributed_event_words": alt_fields,
              "total_staked_prestate": total_staked,
              "acc_reward_per_share_extra": accumulator_delta,
              "unallocated_cleared": True,
              "zero_staker_distributed_event_words": zero_fields,
              "zero_staker_with_prior_distributed_event_words": zero_prior_fields,
              "zero_staker_deferred_rewards": base_fields[1],
              "zero_staker_with_prior_deferred_rewards": base_fields[1] + UNALLOCATED,
              "other_contract_post_storage_equal": True,
              "limits": ["Positive unallocated and zero-staker balances are read-only synthetic storage overrides, not historical on-chain distributions.",
                         "One nonzero amount and one first-in-block transaction were checked; other boundaries remain open.",
                         "The isolated Staking call avoids unrelated BatchExecutor calls in the transaction."],
              "evidence": {"baseline_root": "../../artifacts/staking_unallocated/baseline_replay.json",
                           "baseline_child": "../../artifacts/staking_unallocated/base_child.json",
                           "override_child": "../../artifacts/staking_unallocated/alt_child.json",
                           "baseline_diff": "../../artifacts/staking_unallocated/base_child_diff.json",
                           "override_diff": "../../artifacts/staking_unallocated/alt_child_diff.json",
                           "zero_stakers_child": "../../artifacts/staking_unallocated/zero_stakers_child.json",
                           "zero_stakers_diff": "../../artifacts/staking_unallocated/zero_stakers_diff.json",
                           "zero_stakers_with_prior_child": "../../artifacts/staking_unallocated/zero_stakers_with_prior_child.json",
                           "zero_stakers_with_prior_diff": "../../artifacts/staking_unallocated/zero_stakers_with_prior_diff.json",
                           "zero_stakers_getter": "../../artifacts/staking_unallocated/zero_stakers_getter.json"}}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    print("Staking unallocated reward delta:", result["unallocated_override"],
          result["acc_reward_per_share_extra"])
