#!/usr/bin/env python3
"""Reconcile older Exchange locked margin to opened and terminal positions."""

import argparse
import collections
import gzip
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from atlas_deployer_scope import PIN, call
from atlas_exchange_sweeps import mapping_slot
from atlas_factory_events import Keccak
from atlas_older_event_census import OUT as EVENTS

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = [
    ROOT / "artifacts" / "deployer_scope" / f"older_exchange_{index}_positions.json.gz"
    for index in range(2)
]
OPEN = "0x88451ea1189f73b554f0bf39c09868560ed149b3d788fcc933ff66ba926827f3"
TERMINAL = (
    {
        "0x330ea55ab7d6f2662fc122ba5ed0d3bc3bb56ef7e9387b5aa6a78411b363c013",
        "0xed1740fa1feb6b39daff59946d53a251b3aacbd74ca7c793ff045f89337d5cd2",
    },
    {
        "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf",
        "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8",
    },
)
GETTERS = {
    "nextPositionId": ("0x899346c7", 11, "whole"),
    "treasury": ("0x61d027b3", 14, "whole"),
    "totalQueued": ("0x53ac4b66", 18, "whole"),
    "totalBalances": ("0xa69a2ad1", 22, "low128"),
    "totalLockedMargin": ("0x01ad056f", 22, "high128"),
}
EXPECTED_OPEN = (398_945, 51_834)
EXPECTED_TERMINAL = (378_668, 51_822)
EXPECTED_ACTIVE = (20_277, 12)
EXPECTED_MARGIN = (27_815_598_618_510_431_633_825_980, 454_788_380_311_788_076_713_585)
BATCH_SIZE = 50


def saved(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i : i + 64], 16) for i in range(2, len(data), 64)]


def positions_from_events(events, set_index):
    opened = {}
    terminal = {}
    counts = collections.Counter()
    for window in events["windows"]:
        for log in window["logs"]:
            topic = log["topics"][0].lower()
            if topic != OPEN and topic not in TERMINAL[set_index]:
                continue
            assert len(log["topics"]) == 3
            position_id = int(log["topics"][1], 16)
            user = "0x" + log["topics"][2][-40:].lower()
            if topic == OPEN:
                assert position_id not in opened
                data = words(log["data"])
                assert len(data) == 6 and 0 <= data[4] < 1 << 128
                opened[position_id] = {
                    "user": user,
                    "instrument": data[0],
                    "side": data[1],
                    "entry_price": data[3],
                    "margin": data[4],
                    "leverage": data[5],
                }
            else:
                assert position_id in opened and position_id not in terminal
                assert user == opened[position_id]["user"]
                terminal[position_id] = topic
            counts[topic] += 1
    assert len(opened) == EXPECTED_OPEN[set_index]
    assert set(opened) == set(range(len(opened)))
    assert len(terminal) == EXPECTED_TERMINAL[set_index]
    active = {key: value for key, value in opened.items() if key not in terminal}
    assert len(active) == EXPECTED_ACTIVE[set_index]
    assert sum(row["margin"] for row in active.values()) == EXPECTED_MARGIN[set_index]
    return opened, terminal, active, counts


def sampled_closed_ids(terminal):
    ids = sorted(terminal)
    return sorted({ids[(index * (len(ids) - 1)) // 63] for index in range(64)})


def sampled_active_ids(active, set_index):
    ids = sorted(active)
    if set_index == 1:
        return ids
    spread = {ids[(index * (len(ids) - 1)) // 255] for index in range(256)}
    largest = sorted(active, key=lambda key: (-active[key]["margin"], key))[:64]
    return sorted(spread | set(largest))


class RateLimited(Exception):
    pass


def rpc_batches(url, requests):
    batches = [
        requests[start : start + BATCH_SIZE]
        for start in range(0, len(requests), BATCH_SIZE)
    ]

    def fetch(batch):
        request = urllib.request.Request(
            url,
            json.dumps(batch).encode(),
            {"Content-Type": "application/json"},
        )
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    reply = json.load(response)
                assert isinstance(reply, list) and len(reply) == len(batch)
                result = {}
                for row in reply:
                    if "error" in row:
                        if row["error"].get("code") == 429:
                            raise RateLimited()
                        raise AssertionError(row)
                    assert row["id"] not in result
                    result[row["id"]] = row["result"]
                assert set(result) == {row["id"] for row in batch}
                time.sleep(0.3)
                return result
            except (
                RateLimited,
                urllib.error.HTTPError,
                urllib.error.URLError,
                TimeoutError,
            ):
                if attempt == 5:
                    raise
                time.sleep(1 * (2**attempt))
        raise AssertionError("unreachable")

    results = {}
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(fetch, batch) for batch in batches]
        for future in as_completed(futures):
            result = future.result()
            assert not (results.keys() & result.keys())
            results.update(result)
    assert len(results) == len(requests)
    return results


def capture_set(set_index):
    events, scope = saved(EVENTS[set_index]), saved(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert events["block_hash"] == scope["block_hash"] == manifest["block_hash"]
    _, terminal, active, _ = positions_from_events(events, set_index)
    exchange = events["exchange"]
    keccak = Keccak()
    requests = [call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    request_id = 1
    global_calls = {}
    for slot in (11, 14, 18, 22):
        global_calls[f"slot_{slot}"] = request_id
        requests.append(
            call("eth_getStorageAt", [exchange, hex(slot), hex(PIN)], request_id)
        )
        request_id += 1
    for name, (selector, _, _) in GETTERS.items():
        global_calls[name] = request_id
        requests.append(
            call("eth_call", [{"to": exchange, "data": selector}, hex(PIN)], request_id)
        )
        request_id += 1
    active_calls = {}
    for position_id in sampled_active_ids(active, set_index):
        base = int(mapping_slot(position_id, 10, keccak), 16)
        active_calls[position_id] = (base, request_id, request_id + 1)
        for offset in (0, 1):
            requests.append(
                call(
                    "eth_getStorageAt",
                    [exchange, hex(base + offset), hex(PIN)],
                    request_id,
                )
            )
            request_id += 1
    closed_calls = {}
    for position_id in sampled_closed_ids(terminal):
        base = int(mapping_slot(position_id, 10, keccak), 16)
        closed_calls[position_id] = (base + 1, request_id)
        requests.append(
            call("eth_getStorageAt", [exchange, hex(base + 1), hex(PIN)], request_id)
        )
        request_id += 1
    results = rpc_batches(os.environ["PAPERTRADE_ARCHIVE_RPC"], requests)
    assert results[0]["hash"].lower() == manifest["block_hash"]
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "set": set_index,
        "exchange": exchange,
        "global": {key: results[index] for key, index in global_calls.items()},
        "active_words": [
            [position_id, hex(ids[0]), results[ids[1]], results[ids[2]]]
            for position_id, ids in active_calls.items()
        ],
        "closed_sample_words": [
            [position_id, hex(slot), results[index]]
            for position_id, (slot, index) in closed_calls.items()
        ],
    }
    summary = verify_set_payload(payload, events, scope, manifest)
    OUT[set_index].write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return summary


def verify_set_payload(payload, events, scope, manifest):
    set_index = payload["set"]
    assert set_index in (0, 1) and events["set"] == set_index
    assert payload["pin"] == events["pin"] == scope["pin"] == manifest["block"] == PIN
    assert (
        payload["block_hash"]
        == events["block_hash"]
        == scope["block_hash"]
        == manifest["block_hash"]
    )
    assert payload["exchange"] == events["exchange"]
    opened, terminal, active, counts = positions_from_events(events, set_index)
    global_values = payload["global"]
    for name, (_, slot, part) in GETTERS.items():
        raw = int(global_values[f"slot_{slot}"], 16)
        expected = (
            raw >> 128
            if part == "high128"
            else raw & ((1 << 128) - 1)
            if part == "low128"
            else raw
        )
        assert int(global_values[name], 16) == expected, name
    assert int(global_values["nextPositionId"], 16) == len(opened)
    assert int(global_values["totalLockedMargin"], 16) == EXPECTED_MARGIN[set_index]
    assert int(global_values["totalQueued"], 16) == 0
    assert (
        global_values["treasury"]
        == scope["rows"][(4, 23)[set_index]]["exchange_getters"]["treasury"]
    )
    assert (
        global_values["totalBalances"]
        == scope["rows"][(4, 23)[set_index]]["exchange_getters"]["totalBalances"]
    )
    assert [row[0] for row in payload["active_words"]] == sampled_active_ids(
        active, set_index
    )
    keccak = Keccak()
    for position_id, slot, first_raw, second_raw in payload["active_words"]:
        row = active[position_id]
        base = int(mapping_slot(position_id, 10, keccak), 16)
        assert int(slot, 16) == base
        first, second = int(first_raw, 16), int(second_raw, 16)
        assert first & ((1 << 160) - 1) == int(row["user"], 16)
        assert (first >> 160) & ((1 << 32) - 1) == row["instrument"]
        assert first >> 192 == row["entry_price"]
        assert second & ((1 << 128) - 1) == row["margin"]
        assert (second >> 128) & ((1 << 32) - 1) == row["leverage"]
        assert (second >> 224) & 1 == row["side"]
        assert second & (1 << 240)
    assert [row[0] for row in payload["closed_sample_words"]] == sampled_closed_ids(
        terminal
    )
    for position_id, slot, second_raw in payload["closed_sample_words"]:
        assert int(slot, 16) == int(mapping_slot(position_id, 10, keccak), 16) + 1
        second = int(second_raw, 16)
        assert second & ((1 << 128) - 1) == opened[position_id]["margin"]
        assert not second & (1 << 240)
    return {
        "set": set_index,
        "open_events": len(opened),
        "terminal_events": len(terminal),
        "terminal_topics": {
            topic: counts[topic] for topic in sorted(TERMINAL[set_index])
        },
        "active_positions": len(active),
        "active_storage_checked": len(payload["active_words"]),
        "sampled_active_margin": sum(
            active[row[0]]["margin"] for row in payload["active_words"]
        ),
        "closed_storage_sampled": len(payload["closed_sample_words"]),
        "event_active_margin": sum(row["margin"] for row in active.values()),
        "getter_locked_margin": int(global_values["totalLockedMargin"], 16),
        "queued": int(global_values["totalQueued"], 16),
    }


def verify_set(set_index):
    return verify_set_payload(
        saved(OUT[set_index]),
        saved(EVENTS[set_index]),
        saved(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-set", type=int, choices=(0, 1))
    args = parser.parse_args()
    if args.capture_set is not None:
        print(json.dumps(capture_set(args.capture_set), sort_keys=True))
    for index in range(2):
        if OUT[index].exists():
            print(json.dumps(verify_set(index), sort_keys=True))


if __name__ == "__main__":
    main()
