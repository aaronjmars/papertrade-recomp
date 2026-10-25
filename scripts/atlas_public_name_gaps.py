#!/usr/bin/env python3
"""Verify public signature misses and an unobserved Exchange event at the pin."""

import argparse
import datetime
import hashlib
import json
import os
import urllib.request
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_guardian_signature_leads import CALLED, IDENTIFIER, REPORT, VisibleText


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts"
HISTORY = ARTIFACTS / "exchange_instrument_admin" / "full_history_event_query.json"
OUTPUT = ATLAS / "public_name_gap_checks.json"
PIN = 48902346
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
INSTRUMENT_EVENT = "0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9"
CONTROL_EVENT = "0xa065d6ba54c5124cd73ce640fd3fbc0ce6eb8a4f4c9d5155347dcc461ad0cffe"
EVENT_LAYOUTS = {
    CONTROL_EVENT: ["uint32,uint128,uint128", "uint32,uint256,uint256",
                    "uint256,uint128,uint128", "uint256,uint256,uint256"],
    "0x3050fba19ada85812db26b240c13c72cabec711cbf18c7c6b3554d511e2951ee":
        ["address,uint256,bool,uint256,uint256,uint256,uint256,uint256"],
    "0x620c26bf4591919d64df736a6afdfe2981d15eb343c50644b49456c6facb3ab2":
        ["address,uint256,uint256,uint256,uint256,uint256,uint256"],
    "0x5bcf15b0a82479fbcfcb086707ad8be24c96d445448a1f625310e1c3fe491759":
        ["uint128,uint128", "uint256,uint256"],
}


def read(name):
    return json.loads((ATLAS / name).read_text())


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(os.environ["PAPERTRADE_ARCHIVE_RPC"], body,
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["result"]


def capture_history():
    block_hash = rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"]
    assert block_hash == read("manifest.json")["block_hash"]
    queries = []
    for start, topic in ((0, INSTRUMENT_EVENT), (PIN - 256, CONTROL_EVENT)):
        params = [{"fromBlock": hex(start), "toBlock": hex(PIN),
                   "address": EXCHANGE, "topics": [topic]}]
        logs = rpc("eth_getLogs", params)
        assert all(row["address"].lower() == EXCHANGE and row["topics"][0].lower() == topic
                   for row in logs)
        queries.append({"method": "eth_getLogs", "params": params, "result": logs})
    assert not queries[0]["result"] and len(queries[1]["result"]) == 29
    HISTORY.write_text(json.dumps({
        "queried_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pin": PIN, "block_hash": block_hash, "queries": queries,
        "limit": "A provider's empty eth_getLogs result does not prove that no historical call was attempted."
    }, indent=2) + "\n")


def build():
    unresolved = read("unresolved.json")
    function_rows = json.loads((ARTIFACTS / "openchain_unmatched_function_lookup.json").read_text())
    function_selectors = sorted({row["selector"] for row in unresolved["unmatched_selector_candidates"]})
    assert function_rows["selectors"] == function_selectors
    assert function_rows["response"]["ok"]
    function_results = function_rows["response"]["result"]["function"]
    assert set(function_results) == set(function_selectors)
    keccak = Keccak()
    for selector, candidates in function_results.items():
        assert all("0x" + keccak(row["name"].encode())[:4].hex() == selector
                   for row in candidates or [])
    event_rows = json.loads((ARTIFACTS / "openchain_unresolved_event_lookup.json").read_text())
    event_topics = sorted({row["topic0"] for row in unresolved["observed_events_without_resolved_signature"]})
    assert sorted(event_rows["topics"]) == event_topics == sorted(EVENT_LAYOUTS)
    for topic, row in event_rows["topics"].items():
        assert row["http_status"] == 200 and row["body"]["ok"]
        assert set(row["body"]["result"]["event"]) == {topic}
        assert all("0x" + keccak(candidate["name"].encode()).hex() == topic
                   for candidate in row["body"]["result"]["event"][topic] or [])
    parser = VisibleText()
    raw_report = REPORT.read_bytes()
    parser.feed(raw_report.decode())
    visible = " ".join(parser.all_parts)
    code = " ".join(parser.code_parts)
    names = {word for word in IDENTIFIER.findall(code) if len(word) > 2}
    names.update(CALLED.findall(visible))
    names.update(word for word in IDENTIFIER.findall(visible)
                 if len(word) > 3 and any(letter.isupper() for letter in word[1:]))
    report_matches = []
    for topic, layouts in EVENT_LAYOUTS.items():
        for layout in layouts:
            for name in names:
                signature = f"{name}({layout})"
                if "0x" + keccak(signature.encode()).hex() == topic:
                    report_matches.append({"topic0": topic, "signature": signature})
    history = json.loads(HISTORY.read_text())
    assert history["pin"] == PIN and history["block_hash"] == read("manifest.json")["block_hash"]
    assert len(history["queries"]) == 2
    for row, start, topic in zip(history["queries"], (0, PIN - 256),
                                 (INSTRUMENT_EVENT, CONTROL_EVENT)):
        assert row["method"] == "eth_getLogs"
        assert row["params"] == [{"fromBlock": hex(start), "toBlock": hex(PIN),
                                  "address": EXCHANGE, "topics": [topic]}]
        assert all(log["address"].lower() == EXCHANGE and log["topics"][0].lower() == topic
                   for log in row["result"])
    assert not history["queries"][0]["result"]
    assert len(history["queries"][1]["result"]) == 29
    assert {log["transactionHash"] for log in history["queries"][1]["result"]}
    result = {
        "pin": PIN, "block_hash": history["block_hash"],
        "openchain_function_lookup": "../../artifacts/openchain_unmatched_function_lookup.json",
        "openchain_function_selector_count": len(function_selectors),
        "openchain_function_selectors_with_candidates": sum(bool(rows) for rows in function_results.values()),
        "openchain_event_lookup": "../../artifacts/openchain_unresolved_event_lookup.json",
        "openchain_event_topic_count": len(event_topics),
        "openchain_event_topics_with_candidates": sum(bool(row["body"]["result"]["event"][topic])
                                                       for topic, row in event_rows["topics"].items()),
        "guardian_report_sha256": hashlib.sha256(raw_report).hexdigest(),
        "guardian_report_event_name_count": len(names),
        "guardian_report_event_layouts_checked": EVENT_LAYOUTS,
        "guardian_report_event_matches": sorted(report_matches, key=lambda row: (row["topic0"], row["signature"])),
        "instrument_event_full_history_lookup": "../../artifacts/exchange_instrument_admin/full_history_event_query.json",
        "instrument_event_full_history_log_count": 0,
        "control_event_last_256_block_log_count": len(history["queries"][1]["result"]),
        "limits": ["Registry absence and report text search cannot prove that a signature has no preimage.",
                   "Event field widths cannot be established from 32-byte log words alone; tested layouts are explicit above.",
                   "An empty provider log query does not prove that no historical call was attempted."],
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-history", action="store_true")
    arguments = parser.parse_args()
    if arguments.capture_history:
        capture_history()
    result = build()
    print({"unmatched_functions": result["openchain_function_selector_count"],
           "unmatched_events": result["openchain_event_topic_count"],
           "historical_instrument_event_logs": result["instrument_event_full_history_log_count"]})
