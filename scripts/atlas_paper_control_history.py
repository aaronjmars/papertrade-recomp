#!/usr/bin/env python3
"""Capture and verify complete PAPER admin-event and burn-event history."""

import argparse
import collections
import concurrent.futures
import json
import pathlib

from atlas_exchange_withdrawal_history import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "paper_control_history" / "event_queries.json"
OUTPUT = ATLAS / "paper_control_history_behavior.json"
PIN = 48902346
TOKEN = "0xe40f17915daa230324030003a197cdaef2261c0e"
CREATION = 47855130
WINDOW = 100000
ZERO_TOPIC = "0x" + "0" * 64


def topics():
    behavior = json.loads((ATLAS / "paper_token_behavior.json").read_text())
    assert behavior["token_proxy"] == TOKEN
    events = {row["reconstructed_signature"]: row["topic0"]
              for row in behavior["event_catalog"]}
    admin = {key: value for key, value in events.items() if key in (
        "MinterUpdated(address)", "OwnerUpdated(address)",
        "StakingContractUpdated(address)", "AutoApprovedSpenderUpdated(address)")}
    assert len(admin) == 4 and "Transfer(address,address,uint256)" in events
    return admin, events["Transfer(address,address,uint256)"]


def query(start, end, query_topics):
    params = [{"address": TOKEN, "fromBlock": hex(start), "toBlock": hex(end),
               "topics": query_topics}]
    try:
        logs = rpc("eth_getLogs", params)
    except RuntimeError as error:
        if "Log response size exceeded" not in str(error) or start == end:
            raise
        middle = (start + end) // 2
        return query(start, middle, query_topics) + query(middle + 1, end, query_topics)
    return [{"from_block": start, "to_block": end, "logs": logs}]


def capture():
    admin, transfer = topics()
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    ranges = [(start, min(PIN, start + WINDOW - 1))
              for start in range(CREATION, PIN + 1, WINDOW)]
    queries = {
        "admin": [[*sorted(admin.values())]],
        "burn": [transfer, None, ZERO_TOPIC],
    }
    def fetch(item):
        name, start, end = item
        return name, query(start, end, queries[name])

    results = {name: [] for name in queries}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for name, windows in pool.map(fetch, [(name, start, end)
                                              for name in queries for start, end in ranges]):
            results[name].extend(windows)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "pin": PIN, "block_hash": manifest["block_hash"], "creation_block": CREATION,
        "token": TOKEN, "query_topics": queries, "windows": results,
        "query_limit": "Only emitted successful event logs are visible; unlogged writes and reverted calls are not covered."
    }, indent=2) + "\n")


def verify():
    saved = json.loads(ARTIFACT.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    admin, transfer = topics()
    assert saved["pin"] == PIN and saved["block_hash"] == manifest["block_hash"]
    assert saved["token"] == TOKEN and saved["creation_block"] == CREATION
    assert manifest["contracts"][TOKEN]["origin"]["block"] == CREATION
    assert saved["query_topics"] == {"admin": [[*sorted(admin.values())]],
                                     "burn": [transfer, None, ZERO_TOPIC]}
    counts = {}
    admin_rows = []
    burn_rows = []
    for name in ("admin", "burn"):
        cursor, seen, count = CREATION, set(), 0
        for window in saved["windows"][name]:
            start, end = window["from_block"], window["to_block"]
            assert start == cursor and start <= end <= PIN
            cursor = end + 1
            for log in window["logs"]:
                assert log["address"].lower() == TOKEN
                assert start <= int(log["blockNumber"], 16) <= end
                key = (log["transactionHash"], log["logIndex"])
                assert key not in seen
                seen.add(key)
                if name == "admin":
                    assert log["topics"][0] in admin.values()
                    admin_rows.append(log)
                else:
                    assert log["topics"][0] == transfer and len(log["topics"]) == 3
                    assert log["topics"][2].lower() == ZERO_TOPIC
                    burn_rows.append(log)
                count += 1
        assert cursor == PIN + 1
        counts[name] = count
    names = {v: k for k, v in admin.items()}
    admin_events = [{"signature": names[log["topics"][0]],
                     "tx": log["transactionHash"],
                     "block": int(log["blockNumber"], 16),
                     "indexed_address": "0x" + log["topics"][1][-40:]}
                    for log in admin_rows]
    burn_events = [{"tx": log["transactionHash"],
                    "block": int(log["blockNumber"], 16),
                    "from": "0x" + log["topics"][1][-40:],
                    "amount": str(int(log["data"], 16))}
                   for log in burn_rows]
    assert counts == {"admin": 5, "burn": 0}
    assert collections.Counter(row["signature"] for row in admin_events) == {
        "OwnerUpdated(address)": 2, "MinterUpdated(address)": 1,
        "AutoApprovedSpenderUpdated(address)": 1,
        "StakingContractUpdated(address)": 1,
    }
    token = json.loads((ATLAS / "paper_token_behavior.json").read_text())
    expected_txs = {manifest["contracts"][TOKEN]["origin"]["tx"],
                    *token["admin_transactions"].values()}
    assert {row["tx"] for row in admin_events} == expected_txs
    assert next(row for row in admin_events if row["signature"] == "MinterUpdated(address)")["indexed_address"] == token["initializer"]["minter"]
    output = {"pin": PIN, "block_hash": saved["block_hash"], "token": TOKEN,
              "admin_event_count": counts["admin"],
              "admin_signature_counts": dict(collections.Counter(row["signature"] for row in admin_events)),
              "admin_events": admin_events, "burn_event_count": counts["burn"],
              "burn_events": burn_events,
              "limit": "Complete event scans prove emitted admin and burn events through the pin, not absence of reverted calls or unlogged writes."}
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print(counts["admin"], "PAPER admin events;", counts["burn"], "burn Transfer events")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
