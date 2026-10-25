#!/usr/bin/env python3
"""Decode saved Papertrade calls into HyperCore read precompiles and CoreWriter."""

import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SAMPLES = ROOT / "artifacts" / "exchange_core_withdrawal" / "status_samples"
OUTPUT = ATLAS / "hypercore_boundary_behavior.json"
WRITER = "0x3333333333333333333333333333333333333333"
WRITER_TOPIC = "0x8c7f585fb295f7eb1e6aeb8fba61b23a4fe60beda405f0045073b185c74412e3"
READS = {
    "0x0000000000000000000000000000000000000801": "spotBalance(address,uint64)",
    "0x0000000000000000000000000000000000000803": "withdrawable(address)",
    "0x000000000000000000000000000000000000080e": "bbo(uint32)",
    "0x0000000000000000000000000000000000000810": "coreUserExists(address)",
}
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
EXCHANGE_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
ORACLE_IMPL = "0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a"
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"


def words(value):
    assert value.startswith("0x") and (len(value) - 2) % 64 == 0
    return [int(value[i:i + 64], 16) for i in range(2, len(value), 64)]


def writer_payload(call):
    raw = bytes.fromhex(call["input"][2:])
    assert raw[:4].hex() == "17938e13"
    assert int.from_bytes(raw[4:36], "big") == 32
    size = int.from_bytes(raw[36:68], "big")
    payload = raw[68:68 + size]
    assert len(payload) == size == 100 and len(raw) == 196
    assert payload[:4] == bytes.fromhex("01000006")
    fields = [int.from_bytes(payload[i:i + 32], "big") for i in (4, 36, 68)]
    destination, token, amount = fields
    assert destination < 2**160 and token == 0 and amount < 2**64 and amount > 0
    return {"action_version": 1, "action_id": 6, "action": "spot send",
            "destination": "0x" + destination.to_bytes(20, "big").hex(),
            "token": token, "amount_core_8_decimals": str(amount)}


def build():
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    census = json.loads((ATLAS / "exchange_withdrawal_event_census.json").read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert graph["traces"] and census["block_hash"] == manifest["block_hash"]
    family = json.loads((ATLAS / "deposit_proxy_instances.json").read_text())
    deposit_addresses = {row["address"].lower() for row in family["instances"]}
    sample_blocks = {row["tx"]: row["block"] for row in census["sampled_events"]}
    seen, sources = set(), []
    for entry in graph["traces"]:
        tx = entry["hash"]
        path = ROOT / "artifacts" / entry["source_directory"] / (entry["source_stem"] + ".calls.json")
        receipt = path.with_name(entry["source_stem"] + ".receipt.json")
        assert receipt.exists() and tx not in seen
        seen.add(tx)
        sources.append((tx, entry["block"], path, receipt, "paired_historical"))
    for path in sorted(SAMPLES.glob("*.calls.json")):
        tx = path.name.removesuffix(".calls.json")
        if tx not in seen:
            assert tx in sample_blocks
            seen.add(tx)
            sources.append((tx, sample_blocks[tx], path, None, "stratified_call_only"))
    assert len(graph["traces"]) == 139 and len(sources) == 170

    records, midpoint_checks = [], []
    writer_receipt_checks = writer_inline_log_checks = 0
    for tx, block, path, receipt_path, tier in sources:
        root = json.loads(path.read_text())
        writer_calls = []

        def visit(node, ancestors):
            nonlocal writer_inline_log_checks
            target = (node.get("to") or "").lower()
            if target in READS or target == WRITER:
                assert not node.get("error") and len(ancestors) > 0
                parent = ancestors[-1]
                context = parent.get("to", "").lower()
                assert context in (EXCHANGE_IMPL, ORACLE_IMPL) or context in deposit_addresses
                selector = parent.get("input", "")[:10]
                sender = node["from"].lower()
                role = ("exchange_proxy" if sender == EXCHANGE else
                        "oracle_proxy" if sender == ORACLE else
                        "user_deposit_proxy" if sender in deposit_addresses else None)
                assert role is not None
                row = {"tx": tx, "block": block, "evidence_tier": tier,
                       "trace": str(path.relative_to(ROOT)), "caller_role": role,
                       "caller": sender, "context_selector": selector,
                       "target": target, "call_type": node["type"]}
                if target == WRITER:
                    assert node["type"] == "CALL" and int(node.get("value", "0x0"), 16) == 0
                    action = writer_payload(node)
                    assert (role == "exchange_proxy") == (action["destination"] != EXCHANGE)
                    row["decoded_action"] = action
                    writer_calls.append(node["input"][10:].lower())
                    logs = [log for log in node.get("logs", []) if log["address"].lower() == WRITER]
                    if tier == "stratified_call_only":
                        assert len(logs) == 1 and logs[0]["topics"][0] == WRITER_TOPIC
                        assert logs[0]["data"][2:].lower() == node["input"][10:].lower()
                        writer_inline_log_checks += 1
                else:
                    assert node["type"] == "STATICCALL"
                    ins, outs = words(node["input"]), words(node["output"])
                    if target.endswith("0801"):
                        assert role == "exchange_proxy" and len(ins) == 2 and len(outs) == 3
                        assert ins[0] < 2**160 and ins[1] == 0
                        row["decoded_input"] = {"user": "0x" + ins[0].to_bytes(20, "big").hex(), "token": 0}
                        row["output_words"] = [str(v) for v in outs]
                    elif target.endswith("0803"):
                        assert role == "exchange_proxy" and len(ins) == len(outs) == 1
                        assert ins[0] < 2**160
                        row["decoded_input"] = {"user": "0x" + ins[0].to_bytes(20, "big").hex()}
                        row["output_words"] = [str(outs[0])]
                    elif target.endswith("080e"):
                        assert role == "oracle_proxy" and context == ORACLE_IMPL
                        assert len(ins) == 1 and len(outs) == 2 and ins[0] in (0, 1)
                        bid, ask = outs
                        assert 0 < bid <= ask
                        midpoint = (bid + ask) // 2
                        assert int(parent["output"], 16) == midpoint
                        assert selector == "0xc0182669"
                        row["decoded_input"] = {"instrument_id": ins[0]}
                        row["output_words"] = [str(bid), str(ask)]
                        row["oracle_midpoint"] = str(midpoint)
                        midpoint_checks.append(row)
                    else:
                        assert target.endswith("0810") and role == "exchange_proxy"
                        assert len(ins) == len(outs) == 1 and ins[0] < 2**160 and outs[0] in (0, 1)
                        row["decoded_input"] = {"user": "0x" + ins[0].to_bytes(20, "big").hex()}
                        row["core_user_exists"] = bool(outs[0])
                records.append(row)
            for child in node.get("calls", []):
                visit(child, ancestors + [node])

        visit(root, [])
        if receipt_path:
            receipt = json.loads(receipt_path.read_text())
            assert receipt["transactionHash"].lower() == tx
            writer_logs = [log for log in receipt["logs"] if log["address"].lower() == WRITER]
            assert all(log["topics"][0] == WRITER_TOPIC for log in writer_logs)
            assert collections.Counter(writer_calls) == collections.Counter(
                log["data"][2:].lower() for log in writer_logs)
            writer_receipt_checks += len(writer_calls)

    target_counts = collections.Counter(row["target"] for row in records)
    selector_counts = collections.Counter((row["caller_role"], row["context_selector"], row["target"])
                                         for row in records)
    writer_roles = collections.Counter(row["caller_role"] for row in records if row["target"] == WRITER)
    existence = collections.Counter(int(row["core_user_exists"]) for row in records
                                   if row["target"].endswith("0810"))
    withdrawable = [row for row in records if row["target"].endswith("0803")]
    distinct_midpoints = len({(row["decoded_input"]["instrument_id"], row["oracle_midpoint"])
                              for row in midpoint_checks})
    assert target_counts == {
        "0x0000000000000000000000000000000000000801": 131,
        "0x0000000000000000000000000000000000000803": 26,
        "0x000000000000000000000000000000000000080e": 102,
        "0x0000000000000000000000000000000000000810": 105,
        WRITER: 118,
    }
    assert len(midpoint_checks) == 102 and writer_receipt_checks == 19
    assert writer_inline_log_checks == 99
    assert writer_roles == {"exchange_proxy": 105, "user_deposit_proxy": 13}
    assert existence == {0: 44, 1: 61}
    assert len(withdrawable) == 26 and all(row["output_words"] == ["0"] for row in withdrawable)
    assert distinct_midpoints == 37
    assert len(records) == 482
    return {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "paired_trace_count": len(graph["traces"]),
        "additional_call_only_trace_count": len(sources) - len(graph["traces"]),
        "boundary_call_count": len(records),
        "boundary_transaction_count": len({row["tx"] for row in records}),
        "target_names": {**READS, WRITER: "CoreWriter.sendRawAction(bytes)"},
        "target_call_counts": dict(sorted(target_counts.items())),
        "context_call_counts": [
            {"caller_role": role, "context_selector": selector, "target": target, "count": count}
            for (role, selector, target), count in sorted(selector_counts.items())],
        "corewriter_action_counts": {"spot_send_6": target_counts[WRITER], "other": 0},
        "corewriter_sender_role_counts": dict(sorted(writer_roles.items())),
        "corewriter_receipt_log_matches": writer_receipt_checks,
        "corewriter_trace_log_matches_without_saved_receipt": writer_inline_log_checks,
        "oracle_bbo_midpoint_matches": len(midpoint_checks),
        "oracle_bbo_midpoint_distinct_transactions": len({row["tx"] for row in midpoint_checks}),
        "oracle_bbo_distinct_instrument_midpoints": distinct_midpoints,
        "oracle_bbo_instrument_counts": dict(collections.Counter(
            str(row["decoded_input"]["instrument_id"]) for row in midpoint_checks)),
        "core_user_exists_result_counts": {str(k): v for k, v in sorted(existence.items())},
        "withdrawable_zero_result_count": len(withdrawable),
        "records": records,
        "limits": ["Counts cover saved paired traces plus 31 additional stratified withdrawal traces, not all historical transactions.",
                   "A CoreWriter call and EVM log prove action enqueue, not later HyperCore settlement.",
                   "The 31 additional withdrawal sample traces have callTracer logs but no saved receipts or storage diffs."],
    }


def verify():
    result = build()
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(result["boundary_call_count"], "HyperCore boundary calls;",
          result["oracle_bbo_midpoint_matches"], "midpoints;",
          result["corewriter_action_counts"]["spot_send_6"], "spot-send actions")
    return result


if __name__ == "__main__":
    verify()
