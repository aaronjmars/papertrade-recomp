#!/usr/bin/env python3
"""Verify BatchExecutor calldata, call traces, and emitted result events."""

import collections
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
BATCH = ROOT / "artifacts" / "batch_executor"
ADDRESS = "0x233ff29b239abc1d7748605da9b205c3e008626e"
SELECTOR = "0x251fb27d"
SIGNATURE = "execute((address,bytes,bool,bytes32,bytes32)[])"
EXECUTED = "0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad"
SUMMARY = "0x9d65322d939fd0a2d0032c87248c8e9f9b14cc177e27b2c049cb4b0356e5160b"
REJECTED = "0x6002fcbae88fcbb8133c69c91df90bbc0b4464af94df2a56f8bb843f1cc5a193"
EVENT_SIGNATURES = {
    EXECUTED: "CallExecuted(bytes32,uint256,bytes32,bool,bytes)",
    SUMMARY: "BatchExecuted(bytes32,uint256,uint256,uint256,uint256)",
    REJECTED: "CallRejected(bytes32,uint256,bytes32,bytes)",
}


def cast(*args):
    return subprocess.run(["cast", *args], capture_output=True, text=True, check=True).stdout.strip()


def saved(hash_, suffix, source_directory=None):
    folders = [BATCH, HISTORICAL]
    if source_directory:
        source = ROOT / "artifacts" / source_directory
        assert source.is_dir(), source
        if source not in folders:
            folders.append(source)
    for folder in folders:
        path = folder / f"{hash_}.{suffix}.json"
        if path.exists():
            return json.loads(path.read_text()), str(path.relative_to(ROOT))
    return None, None


def words(data):
    raw = bytes.fromhex(data[2:])
    assert len(raw) % 32 == 0
    return [int.from_bytes(raw[i:i + 32], "big") for i in range(0, len(raw), 32)]


def executed_event(log):
    data = bytes.fromhex(log["data"][2:])
    assert len(log["topics"]) == 4 and len(data) >= 96
    ok, offset, size = (int.from_bytes(data[i:i + 32], "big") for i in (0, 32, 64))
    assert ok in (0, 1) and offset == 64
    assert len(data) == 96 + ((size + 31) // 32) * 32
    assert not any(data[96 + size:])
    return ok, "0x" + data[96:96 + size].hex()


def main():
    assert cast("sig", SIGNATURE).lower() == SELECTOR
    assert cast("sig", "paperStaking()").lower() == "0xd5c539ce"
    assert cast("sig", "NotAuthorizedRelayer()").lower() == "0x17fb2066"
    assert cast("sig", "BatchCallFailed(uint256,bytes)").lower() == "0x651ab1b3"
    for topic, signature in EVENT_SIGNATURES.items():
        assert cast("keccak", signature).lower() == topic

    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    graph_sources = {r["hash"]: r["source_directory"] for r in graph["traces"]
                     if r["root_role"] == "batch_executor_proxy" and r["root_selector"] == SELECTOR}
    hashes = set(graph_sources) | {p.name.split(".")[0] for p in BATCH.glob("*.tx.json")}
    recent_logs = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    recent_by_tx = collections.defaultdict(list)
    for log in recent_logs:
        if log["address"].lower() == ADDRESS:
            recent_by_tx[log["transactionHash"]].append(log)

    rows = []
    for hash_ in sorted(hashes):
        tx, tx_path = saved(hash_, "tx", graph_sources.get(hash_))
        trace, trace_path = saved(hash_, "calls", graph_sources.get(hash_))
        receipt, receipt_path = saved(hash_, "receipt", graph_sources.get(hash_))
        assert trace is not None and trace["to"].lower() == ADDRESS
        input_ = tx["input"] if tx else trace["input"]
        assert input_.startswith(SELECTOR)
        assert trace["input"].lower() == input_.lower()
        decoded = json.loads(cast("decode-calldata", "--json", SIGNATURE, input_))["data"][0]
        logs = receipt["logs"] if receipt else recent_by_tx[hash_]
        result_logs = [x for x in logs if x["address"].lower() == ADDRESS and x["topics"][0] == EXECUTED]
        summary_logs = [x for x in logs if x["address"].lower() == ADDRESS and x["topics"][0] == SUMMARY]
        assert len(summary_logs) == 1
        assert len(trace.get("calls", [])) == 1 and trace["calls"][0]["type"] == "DELEGATECALL"
        internal_calls = trace["calls"][0].get("calls", [])
        assert len(decoded) == len(internal_calls) == len(result_logs)
        batch_id = cast("keccak", input_).lower()
        assert summary_logs[0]["topics"][1].lower() == batch_id

        intents = []
        for index, (entry, call, log) in enumerate(zip(decoded, internal_calls, result_logs)):
            target, calldata, continue_on_failure, field4, intent_id = entry
            ok, returndata = executed_event(log)
            assert target.lower() == call["to"].lower()
            assert calldata.lower() == call["input"].lower()
            assert log["topics"][1].lower() == batch_id
            assert int(log["topics"][2], 16) == index
            assert log["topics"][3].lower() == intent_id.lower()
            assert ok == (0 if call.get("error") else 1)
            assert returndata.lower() == call.get("output", "0x").lower()
            intents.append({"index": index, "target": target.lower(), "selector": calldata[:10].lower(),
                            "continue_on_failure": continue_on_failure, "field4": field4.lower(),
                            "intent_id": intent_id.lower(), "succeeded": bool(ok),
                            "return_bytes": (len(returndata) - 2) // 2, "return_prefix": returndata[:74]})

        counters = words(summary_logs[0]["data"])
        assert len(counters) == 4
        assert counters[:3] == [len(decoded), sum(i["succeeded"] for i in intents), sum(not i["succeeded"] for i in intents)]
        rows.append({"tx": hash_, "block": int((tx or receipt)["blockNumber"], 16),
                     "batch_id": batch_id, "summary_fields": counters, "intents": intents,
                     "sources": {"transaction": tx_path, "call_trace": trace_path,
                                 "receipt": receipt_path or "atlas/block_48902346/event_logs_last_256_blocks.json"}})

    recent_results = [log for log in recent_logs if log["address"].lower() == ADDRESS and log["topics"][0] == EXECUTED]
    recent_summaries = [log for log in recent_logs if log["address"].lower() == ADDRESS and log["topics"][0] == SUMMARY]
    for log in recent_results:
        executed_event(log)
    for summary in recent_summaries:
        batch_logs = [log for log in recent_by_tx[summary["transactionHash"]] if log["topics"][0] == EXECUTED]
        counters = words(summary["data"])
        assert len(counters) == 4
        assert counters[:3] == [len(batch_logs), sum(executed_event(x)[0] for x in batch_logs),
                                sum(not executed_event(x)[0] for x in batch_logs)]

    traced_failures = {(row["tx"].lower(), intent["index"]) for row in rows
                       for intent in row["intents"] if not intent["succeeded"]}
    recent_failures = {(log["transactionHash"].lower(), int(log["topics"][2], 16))
                       for log in recent_results if not executed_event(log)[0]}
    assert recent_failures <= traced_failures

    behavior = {
        "pin": 48902346,
        "address": ADDRESS,
        "implementation": "0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262",
        "selector_reconstructions": {SELECTOR: SIGNATURE, "0xd5c539ce": "paperStaking()"},
        "event_catalog": [
            {"topic0": topic, "reconstructed_signature": signature,
             "evidence": "exact topic hash plus saved receipt payloads" if topic != REJECTED else "exact topic hash plus pinned read-only rejection probes",
             "observed_last_256_blocks": topic in (EXECUTED, SUMMARY)}
            for topic, signature in EVENT_SIGNATURES.items()
        ],
        "error_catalog": [
            {"selector": "0x17fb2066", "reconstructed_signature": "NotAuthorizedRelayer()", "evidence": "pinned read-only unauthorized empty-batch probe"},
            {"selector": "0x651ab1b3", "reconstructed_signature": "BatchCallFailed(uint256,bytes)", "evidence": "pinned read-only failure with continue flag zero"},
        ],
        "read_only_probe_artifact": "atlas/block_48902346/batch_executor_probes.json",
        "field4_local_replay_artifact": "../../artifacts/batch_executor_field4_local/replay.json",
        "allowlist_local_replay_artifact": "../../artifacts/batch_allowlist_local/replay.json",
        "storage_layout": {"slot_0": "Exchange address", "slot_1": "SessionKeyManager address",
                           "slot_2": "PAPER staking address", "slot_3": "owner address",
                           "mapping_base_slot_4": "authorizedRelayers(address) bool",
                           "slot_5_low_byte": "initialization status; exact getter name unresolved"},
        "recent_window": {"blocks": [48902090, 48902346], "batches": len(recent_summaries),
                          "call_results": len(recent_results),
                          "successful_calls": sum(executed_event(x)[0] for x in recent_results),
                          "failed_calls": sum(not executed_event(x)[0] for x in recent_results),
                          "failed_calls_with_matching_saved_trace": len(recent_failures),
                          "summary_field4_values": sorted({words(x["data"])[3] for x in recent_summaries})},
        "traced_batches": rows,
        "limits": [
            "The fourth tuple field is bytes32 in the hash-matched signature, but its purpose is unresolved; every traced batch used zero. Sixteen exact-runtime local cases with five field values did not change sampled success, continued failure, or rejection behavior beyond changing the calldata-derived batch ID.",
            "Only continue_on_failure=true appears in saved successful batch transactions. Pinned read-only probes exercise false and invalid values.",
            "CallRejected is hash-matched in read-only probes; it was absent from the recent event window.",
            "Summary field four is zero in the recent window and its meaning is unresolved.",
            "The allowlist scan exercises all 262 recorded candidate selectors against Exchange, SessionKeyManager, Staking, and an unrelated target; it is not exhaustive over all possible bytes4 values or targets.",
        ],
    }
    output = ATLAS / "batch_executor_behavior.json"
    output.write_text(json.dumps(behavior, indent=2) + "\n")
    count = sum(len(row["intents"]) for row in rows)
    print(f"wrote {output}: {len(rows)} traced batches, {count} verified intents, {len(recent_summaries)} recent batch summaries")


if __name__ == "__main__":
    main()
