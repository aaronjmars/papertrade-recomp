#!/usr/bin/env python3
"""Reconcile every saved signed withdrawal call with its status, event and CoreWriter action."""

import collections
import json
import pathlib

from atlas_exchange_core_withdrawal import IMPLEMENTATION, PROXY, SELECTOR, TOPIC, words
from atlas_hypercore_boundary import ROOT, ATLAS, SAMPLES, WRITER, writer_payload

OUTPUT = ATLAS / "exchange_withdrawal_trace_corpus.json"
STATUS = "0x0000000000000000000000000000000000000810"
SPOT_BALANCE = "0x0000000000000000000000000000000000000801"


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def build():
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    census = json.loads((ATLAS / "exchange_withdrawal_event_census.json").read_text())
    history = json.loads((ROOT / "artifacts" / "exchange_core_withdrawal" /
                          "full_history_event_query.json").read_text())
    assert graph["traces"] and census["block_hash"] == history["block_hash"]
    full_history = collections.defaultdict(collections.Counter)
    history_blocks = {}
    for window in history["windows"]:
        for log in window["logs"]:
            tx = log["transactionHash"]
            full_history[tx][(log["topics"][1], log["data"])] += 1
            history_blocks[tx] = int(log["blockNumber"], 16)
    sample_blocks = {row["tx"]: row["block"] for row in census["sampled_events"]}
    sources, seen = [], set()
    for entry in graph["traces"]:
        tx = entry["hash"]
        path = ROOT / "artifacts" / entry["source_directory"] / (entry["source_stem"] + ".calls.json")
        receipt_path = path.with_name(entry["source_stem"] + ".receipt.json")
        assert receipt_path.exists() and tx not in seen
        sources.append((tx, entry["block"], path, receipt_path, "paired_historical"))
        seen.add(tx)
    for path in sorted(SAMPLES.glob("*.calls.json")):
        tx = path.name.removesuffix(".calls.json")
        if tx not in seen:
            assert tx in sample_blocks
            sources.append((tx, sample_blocks[tx], path, None, "stratified_call_only"))
            seen.add(tx)
    rows = []
    for tx, block, path, receipt_path, tier in sources:
        root = json.loads(path.read_text())
        receipt = json.loads(receipt_path.read_text()) if receipt_path else None
        if receipt:
            assert receipt["transactionHash"].lower() == tx
        for call in descendants(root):
            if call.get("to", "").lower() != IMPLEMENTATION or call.get("input", "")[:10] != SELECTOR:
                continue
            args = words("0x" + call["input"][10:])
            assert len(args) == 7 and args[0] < 2**160 and args[4] in (27, 28)
            user, raw_amount = args[:2]
            user_topic = "0x" + user.to_bytes(32, "big").hex()
            descendants_of_call = list(descendants(call))
            statuses = [n for n in descendants_of_call if n.get("to", "").lower() == STATUS]
            spot_reads = [n for n in descendants_of_call if n.get("to", "").lower() == SPOT_BALANCE]
            writer_calls = [n for n in descendants_of_call if n.get("to", "").lower() == WRITER]
            assert len(statuses) == len(spot_reads) == len(writer_calls) == 1
            status, spot, writer = statuses[0], spot_reads[0], writer_calls[0]
            assert words(status["input"]) == [user]
            exists = int(status["output"], 16)
            assert exists in (0, 1)
            assert words(spot["input"]) == [int(PROXY, 16), 0]
            assert len(words(spot["output"])) == 3
            assert writer["from"].lower() == PROXY
            action = writer_payload(writer)
            assert action["destination"] == "0x" + user.to_bytes(20, "big").hex()
            assert int(action["amount_core_8_decimals"]) == raw_amount * 100

            inline = [log for log in call.get("logs", [])
                      if log.get("address", "").lower() == PROXY and
                      log.get("topics", [None])[0] == TOPIC]
            if inline:
                assert len(inline) == 1
                event = inline[0]
                event_source = "callTracer_withLog"
                if receipt:
                    assert any(log["topics"] == event["topics"] and log["data"] == event["data"]
                               for log in receipt["logs"])
            else:
                assert receipt
                matching = [log for log in receipt["logs"]
                            if log["address"].lower() == PROXY and
                            log["topics"] == [TOPIC, user_topic] and
                            words(log["data"])[1] == raw_amount * 100]
                assert len(matching) == 1
                event = matching[0]
                event_source = "saved_receipt"
            assert event["topics"] == [TOPIC, user_topic]
            debit, core_amount = words(event["data"])
            assert core_amount == raw_amount * 100
            gap = debit - core_amount * 10**10
            assert gap == (10**18 if exists == 0 else 0)
            assert debit == raw_amount * 10**12 + gap
            event_key = (user_topic, event["data"])
            assert history_blocks[tx] == block and full_history[tx][event_key] > 0
            full_history[tx][event_key] -= 1
            rows.append({
                "tx": tx, "block": block, "trace": str(path.relative_to(ROOT)),
                "evidence_tier": tier, "event_source": event_source,
                "user": action["destination"], "raw_amount_6_decimals": str(raw_amount),
                "core_user_exists": bool(exists),
                "core_spot_total_read_8_decimals": str(words(spot["output"])[0]),
                "corewriter_spot_send_amount_8_decimals": str(core_amount),
                "event_internal_debit_18_decimals": str(debit),
                "extra_debit_18_decimals": str(gap),
            })
    counts = collections.Counter(row["core_user_exists"] for row in rows)
    tiers = collections.Counter(row["evidence_tier"] for row in rows)
    assert len(rows) == 103 and counts == {False: 43, True: 60}
    assert tiers == {"paired_historical": 4, "stratified_call_only": 99}
    assert collections.Counter(row["event_source"] for row in rows) == {
        "callTracer_withLog": 102, "saved_receipt": 1}
    for sample in census["sampled_events"]:
        assert any(row["tx"] == sample["tx"] and
                   row["core_user_exists"] == bool(sample["hypercore_user_status"]) and
                   row["extra_debit_18_decimals"] == sample["event_debit_gap_18_decimals"]
                   for row in rows)
    return {
        "pin": census["pin"], "block_hash": census["block_hash"],
        "selector": SELECTOR, "event_topic0": TOPIC,
        "matched_call_count": len(rows),
        "distinct_transaction_count": len({row["tx"] for row in rows}),
        "core_user_exists_counts": {str(int(k)): v for k, v in sorted(counts.items())},
        "evidence_tier_counts": dict(sorted(tiers.items())),
        "event_source_counts": dict(collections.Counter(row["event_source"] for row in rows)),
        "matched_full_history_event_count": len(rows),
        "checks": ["signed user and raw amount match event indexed user and CoreWriter spot-send payload",
                   "one 0x0810 account-existence read and one 0x0801 Exchange spot-balance read per call",
                   "internal debit equals raw amount scaled to 18 decimals plus one USD exactly when 0x0810 is false",
                   "every matched event is present in the complete saved on-chain event history"],
        "calls": rows,
        "limits": ["Saved calls are selected transactions, not all 28,643 historical withdrawal events.",
                   "99 calls have callTracer logs and full-history event matches but no saved receipt or storage diff in this corpus.",
                   "CoreWriter submission is proven; downstream HyperCore delivery and fee disposition are not checked."],
    }


def verify():
    result = build()
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(result["matched_call_count"], "signed withdrawals matched to status, amount, writer, event and full history:",
          result["core_user_exists_counts"])
    return result


if __name__ == "__main__":
    verify()
