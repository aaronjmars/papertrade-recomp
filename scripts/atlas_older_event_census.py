#!/usr/bin/env python3
"""Capture every emitted event from both older Exchange proxies through the pin."""

import argparse
import collections
import gzip
import json
import pathlib

from atlas_deployer_scope import PIN
from atlas_exchange_withdrawal_history import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = [
    ROOT / "artifacts" / "deployer_scope" / f"older_exchange_{index}_events.json.gz"
    for index in range(2)
]
EXCHANGE_INDEX = (4, 23)
WINDOW = 100_000
MAX_LOGS = 10_000
EXPECTED_LOGS = (1_216_528, 142_814)
EXPECTED_TOPICS = (27, 25)
EXPECTED_INDEXED_CANDIDATES = (411, 4_223)


def saved_json(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def fetch(address, start, end):
    try:
        logs = rpc(
            "eth_getLogs",
            [{"fromBlock": hex(start), "toBlock": hex(end), "address": address}],
        )
    except RuntimeError as error:
        if "Log response size exceeded" not in str(error) or start == end:
            raise
        midpoint = (start + end) // 2
        return fetch(address, start, midpoint) + fetch(address, midpoint + 1, end)
    if len(logs) >= MAX_LOGS and start < end:
        midpoint = (start + end) // 2
        return fetch(address, start, midpoint) + fetch(address, midpoint + 1, end)
    assert len(logs) < MAX_LOGS
    return [{"from_block": start, "to_block": end, "logs": logs}]


def capture_set(set_index):
    scope = saved_json(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert scope["block_hash"] == manifest["block_hash"]
    assert (
        rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    )
    exchange = scope["rows"][EXCHANGE_INDEX[set_index]]
    windows = []
    for start in range(exchange["creation_block"], PIN + 1, WINDOW):
        windows.extend(fetch(exchange["address"], start, min(PIN, start + WINDOW - 1)))
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "set": set_index,
        "exchange": exchange["address"],
        "creation_block": exchange["creation_block"],
        "window_target": WINDOW,
        "windows": windows,
    }
    summary = verify_set_payload(payload, scope, manifest)
    OUT[set_index].write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return summary


def address_shaped_topics(log):
    for topic in log["topics"][1:]:
        value = int(topic, 16)
        if (1 << 96) <= value < (1 << 160):
            yield "0x" + topic[-40:].lower()


def verify_set_payload(saved, scope, manifest):
    set_index = saved["set"]
    assert set_index in (0, 1)
    assert saved["pin"] == scope["pin"] == manifest["block"] == PIN
    assert saved["block_hash"] == scope["block_hash"] == manifest["block_hash"]
    exchange = scope["rows"][EXCHANGE_INDEX[set_index]]
    assert saved["exchange"] == exchange["address"]
    assert saved["creation_block"] == exchange["creation_block"]
    assert saved["window_target"] == WINDOW
    cursor = exchange["creation_block"]
    seen = set()
    topic_counts = collections.Counter()
    shaped = set()
    for window in saved["windows"]:
        start, end = window["from_block"], window["to_block"]
        assert start == cursor and start <= end <= PIN
        cursor = end + 1
        assert len(window["logs"]) < MAX_LOGS
        for log in window["logs"]:
            assert log["address"].lower() == exchange["address"]
            assert log["removed"] is False
            assert start <= int(log["blockNumber"], 16) <= end
            assert len(log["topics"]) >= 1
            key = (log["transactionHash"].lower(), log["logIndex"])
            assert key not in seen
            seen.add(key)
            topic_counts[log["topics"][0].lower()] += 1
            shaped.update(address_shaped_topics(log))
    assert cursor == PIN + 1
    factory_users = {
        "0x" + event["log"]["topics"][1][-40:].lower()
        for event in scope["earlier_factory_deployments"][set_index]["events"]
    }
    assert len(seen) == EXPECTED_LOGS[set_index]
    assert len(topic_counts) == EXPECTED_TOPICS[set_index]
    assert len(shaped) == EXPECTED_INDEXED_CANDIDATES[set_index]
    assert factory_users <= shaped
    return {
        "set": set_index,
        "exchange": exchange["address"],
        "windows": len(saved["windows"]),
        "logs": len(seen),
        "topic_counts": dict(topic_counts),
        "factory_users": len(factory_users),
        "address_shaped_indexed_words": len(shaped),
        "candidate_count_outside_factory": len(shaped - factory_users),
        "candidate_addresses_outside_factory": sorted(shaped - factory_users),
    }


def verify_set(set_index):
    return verify_set_payload(
        saved_json(OUT[set_index]),
        saved_json(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-set", type=int, choices=(0, 1))
    args = parser.parse_args()
    if args.capture_set is not None:
        capture_set(args.capture_set)
    result = [verify_set(index) for index in range(2) if OUT[index].exists()]
    for row in result:
        row["candidate_addresses_outside_factory"] = row[
            "candidate_addresses_outside_factory"
        ][:20]
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
