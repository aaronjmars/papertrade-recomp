"""Replay the older Exchange queue branch on pinned historical runtime code."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib

from atlas_exchange_queue_harvest import ordered_logs
from atlas_factory_events import Keccak
from atlas_older_exchange_library import (
    CLOSE,
    OLD_BATCH_PROXY,
    OLD_IMPLEMENTATION,
    OLD_LIBRARY,
    OLD_PROXY,
    SCOPE,
    children,
    read_gzip,
    words,
)
from atlas_oracle_behavior import PRE_BBO, returndata
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SOURCE = ROOT / "artifacts" / "deployer_scope" / "older_exchange_queue_traces.json.gz"
RAW = ROOT / "artifacts" / "deployer_scope" / "older_exchange_queue_replay.json.gz"
OUT = ATLAS / "older_exchange_queue_replay_behavior.json"
TX = "0xe1d903a527ed571e938719d6c16a6580ba699dd9afbc6ca5bf4c1f651ae1be27"
MATH = "0x82296364"
SETTLEMENT = "0xaa31b143"
QUEUE = "0xacbc814f"
POSITION_GETTER = "0x99fbab88"
ENQUEUED = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
LOSS_EVENT = "0x64afd02d9793c990e8eae9bdefeff49b3ece7e7a2d2eebc011bf39b7eedf5255"


def word(value):
    return f"0x{value:064x}"


def mapping_slot(key, base):
    return int.from_bytes(Keccak()(key.to_bytes(32, "big") + base.to_bytes(32, "big")), "big")


def library_calls(frame):
    return [call for call in children(frame)
            if call.get("to", "").lower() == OLD_LIBRARY]


def close_frames(frame):
    return [call for call in children(frame)
            if call.get("to", "").lower() == OLD_IMPLEMENTATION
            and call.get("input", "").startswith(CLOSE)]


def recordable(frame):
    return {
        "type": frame["type"], "from": frame["from"], "to": frame["to"],
        "input": frame.get("input", "0x"), "output": frame.get("output", "0x"),
        "error": frame.get("error"),
        "logs": [{"address": log["address"], "topics": log["topics"],
                  "data": log["data"]} for log in frame.get("logs", [])],
        "calls": [recordable(child) for child in frame.get("calls", [])],
    }


def source_case():
    saved = read_gzip(SOURCE)["transactions"][TX]
    history = saved["trace"]
    assert history["to"].lower() == OLD_BATCH_PROXY
    closes = close_frames(history)
    assert len(closes) == 1
    call_words = words("0x" + closes[0]["input"][10:])
    array_offset = call_words[1] // 32
    assert call_words[array_offset] == 1
    position_id = call_words[array_offset + 1]
    assert position_id == 398_819
    slot = (int.from_bytes(Keccak()(position_id.to_bytes(32, "big")
                                    + (10).to_bytes(32, "big")), "big") + 1) % 2**256
    bbo = [call for call in children(history) if call.get("to", "").lower() == PRE_BBO]
    assert len(bbo) == 1 and not bbo[0].get("error")
    prices = words(bbo[0]["output"])
    assert len(prices) == 2 and prices[0] < prices[1]
    receipt = saved["receipt"]
    assert int(receipt["status"], 16) == 1
    block = int(receipt["blockNumber"], 16)
    call = {"from": history["from"], "to": history["to"], "data": history["input"],
            "gas": history["gas"], "value": history.get("value", "0x0")}
    return history, receipt, block, call, position_id, slot, prices


def capture(url):
    archive = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    history, receipt, block, call, position_id, slot, prices = source_case()
    header = rpc(archive, "eth_getBlockByNumber", [hex(block - 1), False])
    assert rpc(url, "eth_getBlockByNumber", [hex(block - 1), False])["hash"] == header["hash"]
    assert int(rpc(url, "eth_chainId", []), 16) == 999
    assert int(rpc(url, "eth_blockNumber", []), 16) == block - 1
    source_word = rpc(archive, "eth_getStorageAt", [OLD_PROXY, word(slot), hex(block - 1)])
    rpc(url, "anvil_setStorageAt", [OLD_PROXY, word(slot), source_word])
    assert rpc(url, "eth_getStorageAt", [OLD_PROXY, word(slot), hex(block - 1)]) == source_word
    original = int(source_word, 16)
    assert original >> 232 & 0xFF == 0
    scope = read_gzip(SCOPE)
    implementations = {row["address"]: row["runtime"] for row in scope["rows"]
                       if row["address"] == OLD_IMPLEMENTATION}
    assert len(implementations) == 1
    expected_library = (ATLAS / "runtime" / (OLD_LIBRARY + ".hex")).read_text().strip()
    runtime_hashes = {}
    for address, expected in ((OLD_IMPLEMENTATION, implementations[OLD_IMPLEMENTATION]),
                              (OLD_LIBRARY, expected_library)):
        actual = rpc(url, "eth_getCode", [address, hex(block - 1)])
        assert actual.lower() == expected.lower()
        runtime_hashes[address] = hashlib.sha256(bytes.fromhex(actual[2:])).hexdigest()
    mock = returndata(*prices)
    rpc(url, "anvil_setCode", [PRE_BBO, mock])
    cases = []
    options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
    diff_options = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
    getter = {"to": OLD_PROXY, "data": POSITION_GETTER + word(position_id)[2:]}
    try:
        for flag in (0, 1, 2):
            changed = original | (flag << 232)
            rpc(url, "anvil_setStorageAt", [OLD_PROXY, word(slot), word(changed)])
            getter_output = rpc(url, "eth_call", [getter, hex(block - 1)])
            trace = rpc(url, "debug_traceCall", [call, hex(block - 1), options])
            diff = rpc(url, "debug_traceCall", [call, hex(block - 1), diff_options])
            cases.append({"flag": flag, "word": word(changed),
                          "position_getter_output": getter_output,
                          "trace": trace, "diff": diff})
            print("queue flag", flag, "library", [x["input"][:10] for x in library_calls(trace)], flush=True)
    finally:
        rpc(url, "anvil_setStorageAt", [OLD_PROXY, word(slot), word(original)])
    payload = {
        "source_tx": TX, "source_receipt": receipt, "source_trace": history,
        "fork_block": block - 1, "fork_block_hash": header["hash"],
        "chain_id": 999, "call": call, "position_id": position_id,
        "position_slot": word(slot), "original_position_word": word(original),
        "historical_bbo": prices, "mock_bbo_code": mock,
        "runtime_hashes": runtime_hashes, "cases": cases,
        "method": "archive-backed Anvil fork at preceding block with recorded BBO output and one position-byte override",
    }
    RAW.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0))


def build():
    raw = read_gzip(RAW)
    history, receipt, block, call, position_id, slot, prices = source_case()
    assert raw["source_tx"] == TX
    assert raw["source_receipt"] == receipt and raw["source_trace"] == history
    assert raw["fork_block"] == block - 1 and raw["chain_id"] == 999
    assert raw["call"] == call and raw["position_id"] == position_id
    assert raw["position_slot"] == word(slot) and raw["historical_bbo"] == prices
    assert raw["mock_bbo_code"] == returndata(*prices)
    assert "0x" + Keccak()(b"positions(uint256)").hex()[:8] == POSITION_GETTER
    original = int(raw["original_position_word"], 16)
    assert original >> 232 & 0xFF == 0
    scope = read_gzip(SCOPE)
    first = next(row for row in scope["rows"] if row["address"] == OLD_IMPLEMENTATION)
    assert raw["runtime_hashes"][OLD_IMPLEMENTATION] == hashlib.sha256(
        bytes.fromhex(first["runtime"][2:])).hexdigest()
    assert raw["runtime_hashes"][OLD_LIBRARY] == hashlib.sha256(
        bytes.fromhex((ATLAS / "runtime" / (OLD_LIBRARY + ".hex")).read_text().strip()[2:])).hexdigest()
    assert [case["flag"] for case in raw["cases"]] == [0, 1, 2]
    assert recordable(raw["cases"][0]["trace"]) == recordable(history)
    assert [{"address": log["address"], "topics": log["topics"], "data": log["data"]}
            for log in ordered_logs(raw["cases"][0]["trace"])] == [
                {"address": log["address"], "topics": log["topics"], "data": log["data"]}
                for log in receipt["logs"]]
    summaries = []
    for case in raw["cases"]:
        flag = case["flag"]
        assert int(case["word"], 16) == original | flag << 232
        position_fields = words(case["position_getter_output"])
        assert len(position_fields) == 9
        assert position_fields[6:9] == [1, int(flag > 0), 1]
        trace = case["trace"]
        assert not trace.get("error")
        closes = close_frames(trace)
        assert len(closes) == 1 and not closes[0].get("error")
        calls = library_calls(closes[0])
        selectors = [call["input"][:10] for call in calls]
        assert selectors == [MATH, SETTLEMENT if flag == 0 else QUEUE]
        assert not any(call.get("error") for call in calls)
        assert calls[0]["input"] == library_calls(history)[0]["input"]
        assert calls[0]["output"] == library_calls(history)[0]["output"]
        second_args = words("0x" + calls[1]["input"][10:])
        if flag:
            assert len(second_args) == 4
            pnl = second_args[3] if second_args[3] < 2**255 else second_args[3] - 2**256
            queue_amount = max(0, second_args[2] + pnl)
            assert words(calls[1]["output"]) == [queue_amount]
            assert calls[1].get("logs") and calls[1]["logs"][0]["topics"][0] == ENQUEUED
            log = calls[1]["logs"][0]
            assert log["address"].lower() == OLD_PROXY
            assert int(log["topics"][1], 16) == second_args[1]
            node_id = int(log["topics"][2], 16)
            assert words(log["data"]) == [queue_amount]
        events = [{"topic": log["topics"][0], "data": log["data"]}
                  for log in ordered_logs(closes[0])]
        assert (events[0]["topic"] == LOSS_EVENT) == (flag == 0)
        if flag:
            assert events[0]["topic"] == ENQUEUED
        post = case["diff"].get("post", {})
        pre = case["diff"].get("pre", {})
        assert OLD_PROXY in post and OLD_PROXY in pre
        changed_slots = sorted(post[OLD_PROXY].get("storage", {}))
        if flag:
            before = pre[OLD_PROXY].get("storage", {})
            storage = post[OLD_PROXY]["storage"]
            assert int(before[word(17)], 16) == node_id
            assert int(storage[word(17)], 16) == node_id + 1
            assert int(before.get(word(18), "0x0"), 16) == 0
            assert int(storage[word(18)], 16) == queue_amount
            assert int(before.get(word(mapping_slot(second_args[1], 19)), "0x0"), 16) == 0
            assert int(storage[word(mapping_slot(second_args[1], 19))], 16) == queue_amount
            assert int(before.get(word(mapping_slot(second_args[1], 20)), "0x0"), 16) == 0
            assert int(storage[word(mapping_slot(second_args[1], 20))], 16) == node_id
            assert int(before.get(word(mapping_slot(second_args[1], 21)), "0x0"), 16) == 0
            assert int(storage[word(mapping_slot(second_args[1], 21))], 16) == node_id
            node_slot = mapping_slot(node_id, 15)
            assert int(before.get(word(node_slot), "0x0"), 16) == 0
            assert int(storage[word(node_slot)], 16) == second_args[1]
            assert int(before.get(word(node_slot + 1), "0x0"), 16) == 0
            assert int(storage[word(node_slot + 1)], 16) == queue_amount
        summaries.append({"flag": flag, "position_word": case["word"],
                          "position_getter_flags": position_fields[6:9],
                          "library_selectors": selectors,
                          "second_library_input": calls[1]["input"],
                          "second_library_output": calls[1]["output"],
                          "close_events": events,
                          "queued_amount": queue_amount if flag else None,
                          "queued_node_id": node_id if flag else None,
                          "exchange_changed_storage_slots": changed_slots,
                          "changed_contracts": sorted(post),
                          "exchange_pre_storage": pre[OLD_PROXY].get("storage", {}),
                          "exchange_post_storage": post[OLD_PROXY].get("storage", {})})
    assert summaries[1]["close_events"] == summaries[2]["close_events"]
    assert summaries[1]["second_library_input"] == summaries[2]["second_library_input"]
    assert summaries[1]["second_library_output"] == summaries[2]["second_library_output"]
    for key in ("exchange_pre_storage", "exchange_post_storage"):
        first = dict(summaries[1][key])
        second = dict(summaries[2][key])
        first.pop(word(slot))
        second.pop(word(slot))
        assert first == second
    return {
        "source_tx": TX, "fork_block": block - 1,
        "fork_block_hash": raw["fork_block_hash"],
        "exchange_proxy": OLD_PROXY, "implementation": OLD_IMPLEMENTATION,
        "linked_library": OLD_LIBRARY, "position_id": position_id,
        "position_slot": raw["position_slot"], "original_position_word": raw["original_position_word"],
        "historical_bbo": prices, "baseline_full_call_tree_matches_archive": True,
        "cases": summaries,
        "limits": [
            "The baseline matches one successful historical BatchExecutor call using the historical BBO response installed as local bytecode at precompile 0x080e.",
            "Flags 1 and 2 are constructed position-storage overrides in this close replay. A separate exact-runtime signed-open fork test writes flag 1 from a signed useDebt=true intent; no historical useDebt=true call is proven.",
            "The replay verifies one-position close and queue behavior only; it does not prove other queue sizes, settlement, or Core delivery.",
        ],
    }


def verify():
    expected = build()
    assert json.loads(OUT.read_text()) == expected
    print("Older Exchange queue caller: baseline settlement, flags 1 and 2 queue")
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-rpc-url")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
        OUT.write_text(json.dumps(build(), indent=2) + "\n")
    verify()
