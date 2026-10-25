#!/usr/bin/env python3
"""Replay an Exchange close into a synthetic same-user queue on an archive-backed Anvil fork."""

import argparse
import json
import pathlib

from atlas_exchange_queue_harvest import HARVESTED_TOPIC, ordered_logs, words
from atlas_exchange_queue_layout import AMOUNT, ENQUEUES, HARVEST, PROXY, TOPIC, mapped, slot, storage
from atlas_oracle_behavior import PRE_BBO, returndata
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_queue"
HISTORICAL = ROOT / "artifacts" / "historical"
BLOCK = 48173880
BLOCK_HASH = "0xc4e06ae5048b4457d3df2b1f9658abd429a233649f617c2eb73a67f5f06a48b3"
EXISTING = 5 * 10**18
USER = "0xecba25a6b7cb7dfbe08a1ddf49873e3a6ff49f93"
SENDER = "0x423c409deb1777960f99a72b11b976df01c40f63"
MASK160 = (1 << 160) - 1


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def write(name, payload):
    (ARTIFACTS / name).write_text(json.dumps(payload, indent=2) + "\n")


def load(name):
    return json.loads((ARTIFACTS / name).read_text())


def contract_logs(root):
    return [(row["topics"], row["data"]) for row in ordered_logs(root)
            if row["address"].lower() == PROXY]


def close_call():
    original = json.loads((HISTORICAL / f"{ENQUEUES[0][0]}.calls.json").read_text())
    return {"from": original["from"], "to": original["to"],
            "data": original["input"], "gas": "0x200000"}


def historical_bbo():
    original = json.loads((HISTORICAL / f"{ENQUEUES[0][0]}.calls.json").read_text())
    matches = [node for node in descendants(original) if node.get("to", "").lower() == PRE_BBO]
    assert len(matches) == 1
    pair = words(matches[0]["output"])
    assert len(pair) == 2 and pair[0] <= pair[1]
    return pair


def capture(url):
    assert rpc(url, "eth_getBlockByNumber", [hex(BLOCK), False])["hash"] == BLOCK_HASH
    assert int(rpc(url, "eth_blockNumber", []), 16) == BLOCK, "start a fresh fork at the pre-close block"
    call = close_call()
    bid, ask = historical_bbo()
    rpc(url, "anvil_setCode", [PRE_BBO, returndata(bid, ask)])
    options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
    diff_options = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
    baseline = {"block": BLOCK, "block_hash": BLOCK_HASH, "call": call, "bbo_override": [bid, ask],
                "trace": rpc(url, "debug_traceCall", [call, hex(BLOCK), options]),
                "diff": rpc(url, "debug_traceCall", [call, hex(BLOCK), diff_options])}
    write("append_local_baseline.json", baseline)
    assert_baseline(baseline)

    user = int(USER, 16)
    overrides = {slot(16): 1, slot(17): 2, slot(18): EXISTING,
                 mapped(1, 15): user, mapped(1, 15, 1): EXISTING,
                 mapped(user, 19): EXISTING, mapped(user, 20): 1, mapped(user, 21): 1}
    original_words = {key: rpc(url, "eth_getStorageAt", [PROXY, key, hex(BLOCK)]) for key in overrides}
    assert all(int(value, 16) == (1 if key == slot(17) else 0)
               for key, value in original_words.items())
    for key, value in overrides.items():
        rpc(url, "anvil_setStorageAt", [PROXY, key, slot(value)])
    append = {"block": BLOCK, "block_hash": BLOCK_HASH, "call": call,
              "bbo_override": [bid, ask], "existing_queue_amount": str(EXISTING),
              "original_words": original_words,
              "overrides": {key: slot(value) for key, value in overrides.items()},
              "trace": rpc(url, "debug_traceCall", [call, hex(BLOCK), options]),
              "diff": rpc(url, "debug_traceCall", [call, hex(BLOCK), diff_options])}
    write("append_same_user_local_probe.json", append)
    assert_append(baseline, append)

    exchange_diff = append["diff"]
    before = exchange_diff["pre"][PROXY]["storage"]
    after = exchange_diff["post"][PROXY]["storage"]
    for key in set(before) | set(after):
        rpc(url, "anvil_setStorageAt", [PROXY, key, after.get(key, slot(0))])
    assert int(rpc(url, "eth_getStorageAt", [PROXY, slot(18), hex(BLOCK)]), 16) == EXISTING + AMOUNT
    previous_treasury = int(rpc(url, "eth_getStorageAt", [PROXY, slot(14), hex(BLOCK)]), 16)
    packed_balances = int(rpc(url, "eth_getStorageAt", [PROXY, slot(22), hex(BLOCK)]), 16)
    packed_fees = int(rpc(url, "eth_getStorageAt", [PROXY, slot(26), hex(BLOCK)]), 16)
    mask128 = (1 << 128) - 1
    reserve = (packed_balances & mask128) + (packed_balances >> 128)
    reserve += (packed_fees & mask128) + (packed_fees >> 128)
    treasury = reserve + EXISTING + AMOUNT + 100 * 10**18
    rpc(url, "anvil_setStorageAt", [PROXY, slot(14), slot(treasury)])
    available = int(rpc(url, "eth_call", [{"to": PROXY, "data": "0x138e9de2"}, hex(BLOCK)]), 16)
    assert available == EXISTING + AMOUNT + 100 * 10**18
    for limit in (1, 2):
        call = {"from": SENDER, "to": PROXY,
                "data": "0xddc63262" + limit.to_bytes(32, "big").hex(), "gas": "0x200000"}
        result = {"block": BLOCK, "block_hash": BLOCK_HASH, "call": call,
                  "prior_synthetic_close": "append_same_user_local_probe.json",
                  "treasury_before": str(previous_treasury), "treasury_override": str(treasury),
                  "queue_available": str(available),
                  "trace": rpc(url, "debug_traceCall", [call, hex(BLOCK), options]),
                  "diff": rpc(url, "debug_traceCall", [call, hex(BLOCK), diff_options])}
        write(f"append_harvest_{limit}_local_probe.json", result)
    partial_cases = []
    for available in (0, 3 * 10**18, EXISTING, EXISTING + 2 * 10**18):
        partial_treasury = reserve + available
        rpc(url, "anvil_setStorageAt", [PROXY, slot(14), slot(partial_treasury)])
        getter = int(rpc(url, "eth_call", [{"to": PROXY, "data": "0x138e9de2"}, hex(BLOCK)]), 16)
        assert getter == available
        for limit in (1, 2):
            partial_call = {"from": SENDER, "to": PROXY,
                            "data": "0xddc63262" + limit.to_bytes(32, "big").hex(), "gas": "0x200000"}
            partial_cases.append({
                "available": str(available), "treasury_override": str(partial_treasury),
                "limit": limit, "call": partial_call,
                "trace": rpc(url, "debug_traceCall", [partial_call, hex(BLOCK), options]),
                "diff": rpc(url, "debug_traceCall", [partial_call, hex(BLOCK), diff_options]),
            })
    write("partial_node_probes.json", {"block": BLOCK, "block_hash": BLOCK_HASH,
                                        "reserve": str(reserve),
                                        "source": "synthetic post-close Exchange state from append_same_user_local_probe.json",
                                        "cases": partial_cases})


def assert_baseline(baseline):
    assert baseline["block"] == BLOCK and baseline["block_hash"] == BLOCK_HASH
    assert baseline["call"] == close_call() and baseline["bbo_override"] == historical_bbo()
    assert not baseline["trace"].get("error")
    actual_diff = json.loads((HISTORICAL / f"{ENQUEUES[0][0]}.state_diff.json").read_text())
    for phase in ("pre", "post"):
        assert baseline["diff"][phase][PROXY]["storage"] == actual_diff[phase][PROXY]["storage"]
    receipt = json.loads((HISTORICAL / f"{ENQUEUES[0][0]}.receipt.json").read_text())
    all_logs = [(row["address"].lower(), row["topics"], row["data"])
                for row in ordered_logs(baseline["trace"])]
    receipt_logs = [(row["address"].lower(), row["topics"], row["data"]) for row in receipt["logs"]]
    assert all_logs == receipt_logs


def assert_append(baseline, append):
    assert append["block"] == BLOCK and append["block_hash"] == BLOCK_HASH
    assert append["call"] == baseline["call"] and append["bbo_override"] == baseline["bbo_override"]
    assert int(append["existing_queue_amount"]) == EXISTING
    user = int(USER, 16)
    expected = {slot(16): 1, slot(17): 2, slot(18): EXISTING,
                mapped(1, 15): user, mapped(1, 15, 1): EXISTING,
                mapped(user, 19): EXISTING, mapped(user, 20): 1, mapped(user, 21): 1}
    assert append["overrides"] == {key: slot(value) for key, value in expected.items()}
    assert all(int(value, 16) == (1 if key == slot(17) else 0)
               for key, value in append["original_words"].items())
    assert not append["trace"].get("error")
    base_logs = contract_logs(baseline["trace"])
    appended_logs = contract_logs(append["trace"])
    assert len(base_logs) == len(appended_logs) == 3
    assert base_logs[1:] == appended_logs[1:]
    assert base_logs[0] == ([TOPIC, slot(user), slot(1)], slot(AMOUNT))
    assert appended_logs[0] == ([TOPIC, slot(user), slot(2)], slot(AMOUNT))
    diff = append["diff"]
    assert storage(diff, "pre", slot(17)) == 2 and storage(diff, "post", slot(17)) == 3
    assert storage(diff, "pre", slot(18)) == EXISTING
    assert storage(diff, "post", slot(18)) == EXISTING + AMOUNT
    assert storage(diff, "pre", mapped(user, 19)) == EXISTING
    assert storage(diff, "post", mapped(user, 19)) == EXISTING + AMOUNT
    assert storage(diff, "pre", mapped(user, 21)) == 1
    assert storage(diff, "post", mapped(user, 21)) == 2
    assert slot(16) not in diff["pre"][PROXY]["storage"]
    assert mapped(user, 20) not in diff["pre"][PROXY]["storage"]
    node1 = storage(diff, "post", mapped(1, 15))
    node2 = storage(diff, "post", mapped(2, 15))
    assert node1 & MASK160 == node2 & MASK160 == user
    assert node1 >> 160 == 2
    assert node2 >> 208 == 1 and ((node2 >> 160) & ((1 << 48) - 1)) == 0
    assert storage(diff, "post", mapped(2, 15, 1)) == AMOUNT


def assert_harvest(probe, limit):
    assert probe["block"] == BLOCK and probe["block_hash"] == BLOCK_HASH
    assert probe["prior_synthetic_close"] == "append_same_user_local_probe.json"
    assert probe["call"] == {"from": SENDER, "to": PROXY,
                              "data": "0xddc63262" + limit.to_bytes(32, "big").hex(),
                              "gas": "0x200000"}
    assert int(probe["queue_available"]) > EXISTING + AMOUNT
    assert int(probe["treasury_override"]) > int(probe["treasury_before"])
    trace = probe["trace"]
    assert not trace.get("error")
    expected_amount = EXISTING if limit == 1 else EXISTING + AMOUNT
    assert int(trace["output"], 16) == expected_amount
    diff = probe["diff"]
    user = int(USER, 16)
    assert storage(diff, "pre", slot(16)) == 1
    assert storage(diff, "post", slot(16)) == 1 + limit
    assert storage(diff, "pre", slot(18)) == EXISTING + AMOUNT
    assert storage(diff, "post", slot(18)) == (AMOUNT if limit == 1 else 0)
    assert storage(diff, "post", slot(22)) - storage(diff, "pre", slot(22)) == expected_amount
    assert storage(diff, "post", mapped(user, 9)) - storage(diff, "pre", mapped(user, 9)) == expected_amount
    assert storage(diff, "pre", mapped(user, 19)) == EXISTING + AMOUNT
    assert storage(diff, "post", mapped(user, 19)) == (AMOUNT if limit == 1 else 0)
    assert storage(diff, "pre", mapped(user, 20)) == 1
    assert storage(diff, "post", mapped(user, 20)) == (2 if limit == 1 else 0)
    assert storage(diff, "pre", mapped(1, 15, 1)) == EXISTING
    assert storage(diff, "post", mapped(1, 15, 1)) == 0
    assert storage(diff, "pre", mapped(2, 15)) == user | (1 << 208)
    assert storage(diff, "post", mapped(2, 15)) == user
    if limit == 1:
        assert mapped(user, 21) not in diff["pre"][PROXY]["storage"]
        assert mapped(2, 15, 1) not in diff["pre"][PROXY]["storage"]
    else:
        assert storage(diff, "pre", mapped(user, 21)) == 2
        assert storage(diff, "post", mapped(user, 21)) == 0
        assert storage(diff, "pre", mapped(2, 15, 1)) == AMOUNT
        assert storage(diff, "post", mapped(2, 15, 1)) == 0
    logs = contract_logs(trace)
    assert len(logs) == limit
    for i, (topics, data) in enumerate(logs):
        assert topics == [HARVESTED_TOPIC, slot(user)]
        assert words(data) == [EXISTING if i == 0 else AMOUNT, 0]


def assert_partial_matrix(matrix):
    assert matrix["block"] == BLOCK and matrix["block_hash"] == BLOCK_HASH
    assert matrix["source"] == "synthetic post-close Exchange state from append_same_user_local_probe.json"
    reserve = int(matrix["reserve"])
    cases = matrix["cases"]
    expected_pairs = [(available, limit)
                      for available in (0, 3 * 10**18, EXISTING, EXISTING + 2 * 10**18)
                      for limit in (1, 2)]
    assert [(int(case["available"]), case["limit"]) for case in cases] == expected_pairs
    summary = []
    user = int(USER, 16)
    for case in cases:
        available, limit = int(case["available"]), case["limit"]
        assert int(case["treasury_override"]) == reserve + available
        assert case["call"] == {"from": SENDER, "to": PROXY,
                                "data": "0xddc63262" + limit.to_bytes(32, "big").hex(),
                                "gas": "0x200000"}
        trace, diff = case["trace"], case["diff"]
        assert not trace.get("error")
        first_paid = min(available, EXISTING)
        second_paid = min(max(available - EXISTING, 0), AMOUNT) if limit == 2 else 0
        total_paid = first_paid + second_paid
        assert int(trace["output"], 16) == total_paid
        logs = contract_logs(trace)
        expected_logs = []
        if first_paid:
            expected_logs.append(([HARVESTED_TOPIC, slot(user)],
                                  slot(first_paid) + slot(EXISTING - first_paid)[2:]))
        if second_paid:
            expected_logs.append(([HARVESTED_TOPIC, slot(user)],
                                  slot(second_paid) + slot(AMOUNT - second_paid)[2:]))
        assert logs == expected_logs
        if total_paid == 0:
            assert PROXY not in diff.get("pre", {}) and PROXY not in diff.get("post", {})
        else:
            assert storage(diff, "pre", slot(18)) == EXISTING + AMOUNT
            assert storage(diff, "post", slot(18)) == EXISTING + AMOUNT - total_paid
            assert storage(diff, "post", slot(22)) - storage(diff, "pre", slot(22)) == total_paid
            assert storage(diff, "post", mapped(user, 9)) - storage(diff, "pre", mapped(user, 9)) == total_paid
            assert storage(diff, "pre", mapped(user, 19)) == EXISTING + AMOUNT
            assert storage(diff, "post", mapped(user, 19)) == EXISTING + AMOUNT - total_paid
            assert storage(diff, "pre", mapped(1, 15, 1)) == EXISTING
            assert storage(diff, "post", mapped(1, 15, 1)) == EXISTING - first_paid
            assert mapped(user, 21) not in diff["pre"][PROXY]["storage"]
            if first_paid < EXISTING:
                assert slot(16) not in diff["pre"][PROXY]["storage"]
                assert mapped(user, 20) not in diff["pre"][PROXY]["storage"]
            else:
                assert storage(diff, "pre", slot(16)) == 1
                assert storage(diff, "post", slot(16)) == 2
                assert storage(diff, "pre", mapped(user, 20)) == 1
                assert storage(diff, "post", mapped(user, 20)) == 2
                assert storage(diff, "pre", mapped(2, 15)) == user | (1 << 208)
                assert storage(diff, "post", mapped(2, 15)) == user
            if second_paid:
                assert storage(diff, "pre", mapped(2, 15, 1)) == AMOUNT
                assert storage(diff, "post", mapped(2, 15, 1)) == AMOUNT - second_paid
            else:
                assert mapped(2, 15, 1) not in diff["pre"][PROXY]["storage"]
            assert slot(27) not in diff["pre"][PROXY]["storage"]
        summary.append({"available": str(available), "max_entries": limit,
                        "returned_amount": str(total_paid),
                        "first_node_remaining": str(EXISTING - first_paid),
                        "second_node_remaining": str(AMOUNT - second_paid),
                        "harvest_events": len(logs)})
    return summary


def verify():
    baseline = load("append_local_baseline.json")
    append = load("append_same_user_local_probe.json")
    assert_baseline(baseline)
    assert_append(baseline, append)
    for n in (1, 2):
        assert_harvest(load(f"append_harvest_{n}_local_probe.json"), n)
    partial_summary = assert_partial_matrix(load("partial_node_probes.json"))
    result = {
        "pin_block": 48902346, "pre_close_block": BLOCK, "pre_close_block_hash": BLOCK_HASH,
        "historical_close_tx": ENQUEUES[0][0], "exchange_proxy": PROXY,
        "historical_bbo": historical_bbo(),
        "baseline_replay": {"exchange_storage_diff_equal": True, "all_ordered_logs_equal": True},
        "synthetic_existing_amount": str(EXISTING),
        "append": {"new_node_id": 2, "new_amount": str(AMOUNT), "global_head": 1,
                   "next_id_after": 3, "total_queued_after": str(EXISTING + AMOUNT),
                   "user_head_after": 1, "user_tail_after": 2,
                   "packed_node_word": "owner address in low 160 bits; next ID in bits 160-207; previous ID in bits 208-255"},
        "same_user_harvest": [
            {"limit": 1, "returned_amount": str(EXISTING), "user_head_after": 2,
             "user_tail_after": 2, "user_queued_after": str(AMOUNT)},
            {"limit": 2, "returned_amount": str(EXISTING + AMOUNT), "user_head_after": 0,
             "user_tail_after": 0, "user_queued_after": "0"}],
        "partial_node_payouts": partial_summary,
        "limitations": ["The append and same-user harvest are local fork simulations with a synthetic existing node.",
                        "The fork uses the historical BBO return words as mock HyperCore precompile code.",
                        "Same-user harvest needed a synthetic treasury increase to pass its availability gate.",
                        "No underfunded harvest or same-user append was observed on chain; larger lists and concurrent enqueues remain untested."]}
    (ATLAS / "exchange_queue_append_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange queue: historical close replay, same-user append, and eight funding-limited harvest branches verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-rpc-url", help="fresh archive-backed Anvil fork at block 48173880")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    verify()
