#!/usr/bin/env python3
"""Check pinned queue mappings for every older Exchange enqueue recipient."""

import argparse
import collections
import gzip
import json
import os
import pathlib

from atlas_deployer_scope import PIN, call
from atlas_exchange_sweeps import mapping_slot, word
from atlas_factory_events import Keccak
from atlas_older_event_census import OUT as EVENTS
from atlas_older_positions import rpc_batches, saved

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = [
    ROOT
    / "artifacts"
    / "deployer_scope"
    / f"older_exchange_{index}_queue_accounts.json.gz"
    for index in range(2)
]
ENQUEUED = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
HARVESTED = "0x81ca9b2c230070eaa84787556b1aaf18bf1e2f07ea5d3dae4819db77a1a5b224"
GETTERS = {
    "total": ("0x551306f3", 19),
    "head": ("0xdcab7f6a", 20),
    "tail": ("0x3a21be03", 21),
}
EXPECTED_EVENTS = (8_452, 0)
EXPECTED_USERS = (132, 0)
EXPECTED_HARVESTS = (8_516, 0)
EXPECTED_PARTIAL_HARVESTS = (64, 0)


def enqueue_users(events, set_index):
    users = collections.defaultdict(lambda: {"events": 0, "enqueued_raw": 0})
    harvested = collections.Counter()
    paid_by_user = collections.Counter()
    node_ids = []
    for window in events["windows"]:
        for log in window["logs"]:
            topic = log["topics"][0].lower()
            if topic == ENQUEUED:
                assert len(log["topics"]) == 3
                user = "0x" + log["topics"][1][-40:].lower()
                node_id = int(log["topics"][2], 16)
                amount = int(log["data"], 16)
                node_ids.append(node_id)
                users[user]["events"] += 1
                users[user]["enqueued_raw"] += amount
            elif topic == HARVESTED:
                assert len(log["topics"]) == 2 and len(log["data"]) == 2 + 2 * 64
                user = "0x" + log["topics"][1][-40:].lower()
                paid = int(log["data"][2:66], 16)
                remaining = int(log["data"][66:130], 16)
                harvested["events"] += 1
                harvested["paid_raw"] += paid
                harvested["partial"] += remaining > 0
                harvested["cleared"] += remaining == 0
                paid_by_user[user] += paid
    assert len(node_ids) == EXPECTED_EVENTS[set_index]
    assert len(users) == EXPECTED_USERS[set_index]
    assert node_ids == list(range(1, len(node_ids) + 1))
    assert harvested["events"] == EXPECTED_HARVESTS[set_index]
    assert harvested["partial"] == EXPECTED_PARTIAL_HARVESTS[set_index]
    assert harvested["cleared"] == len(node_ids)
    assert set(paid_by_user) == set(users)
    assert all(paid_by_user[user] == row["enqueued_raw"] for user, row in users.items())
    assert harvested["paid_raw"] == sum(row["enqueued_raw"] for row in users.values())
    return dict(sorted(users.items())), harvested


def capture_set(set_index):
    events = saved(EVENTS[set_index])
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert events["pin"] == manifest["block"] == PIN
    assert events["block_hash"] == manifest["block_hash"]
    users, _ = enqueue_users(events, set_index)
    exchange = events["exchange"]
    keccak = Keccak()
    calls = [call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    request_id = 1
    global_calls = {}
    for name, method, params in (
        ("slot_16", "eth_getStorageAt", [exchange, hex(16), hex(PIN)]),
        ("slot_17", "eth_getStorageAt", [exchange, hex(17), hex(PIN)]),
        ("slot_18", "eth_getStorageAt", [exchange, hex(18), hex(PIN)]),
        ("queueHead", "eth_call", [{"to": exchange, "data": "0x96523644"}, hex(PIN)]),
        ("totalQueued", "eth_call", [{"to": exchange, "data": "0x53ac4b66"}, hex(PIN)]),
    ):
        global_calls[name] = request_id
        calls.append(call(method, params, request_id))
        request_id += 1
    user_calls = {}
    for user in users:
        fields = {}
        for name, (selector, base) in GETTERS.items():
            slot = mapping_slot(user, base, keccak)
            getter_id, storage_id = request_id, request_id + 1
            calls.append(
                call(
                    "eth_call",
                    [{"to": exchange, "data": selector + word(user)}, hex(PIN)],
                    getter_id,
                )
            )
            calls.append(
                call("eth_getStorageAt", [exchange, slot, hex(PIN)], storage_id)
            )
            fields[name] = (slot, getter_id, storage_id)
            request_id += 2
        user_calls[user] = fields
    results = rpc_batches(os.environ["PAPERTRADE_ARCHIVE_RPC"], calls)
    assert results[0]["hash"].lower() == manifest["block_hash"]
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "set": set_index,
        "exchange": exchange,
        "global": {name: results[index] for name, index in global_calls.items()},
        "users": [
            {
                "address": user,
                "fields": {
                    name: {
                        "slot": slot,
                        "getter": results[getter_id],
                        "storage": results[storage_id],
                    }
                    for name, (slot, getter_id, storage_id) in fields.items()
                },
            }
            for user, fields in user_calls.items()
        ],
    }
    summary = verify_set_payload(payload, events, manifest)
    OUT[set_index].write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return summary


def verify_set_payload(payload, events, manifest):
    set_index = payload["set"]
    assert set_index in (0, 1) and events["set"] == set_index
    assert payload["pin"] == events["pin"] == manifest["block"] == PIN
    assert payload["block_hash"] == events["block_hash"] == manifest["block_hash"]
    assert payload["exchange"] == events["exchange"]
    users, harvested = enqueue_users(events, set_index)
    assert [row["address"] for row in payload["users"]] == sorted(users)
    global_values = payload["global"]
    assert global_values["slot_16"] == global_values["queueHead"]
    assert global_values["slot_18"] == global_values["totalQueued"]
    keccak = Keccak()
    nonzero = collections.Counter()
    for row in payload["users"]:
        for name, (_, base) in GETTERS.items():
            field = row["fields"][name]
            assert field["slot"] == mapping_slot(row["address"], base, keccak)
            assert field["getter"] == field["storage"]
            nonzero[name] += int(field["getter"], 16) > 0
    return {
        "set": set_index,
        "enqueue_events": sum(row["events"] for row in users.values()),
        "enqueue_users": len(users),
        "enqueued_raw": sum(row["enqueued_raw"] for row in users.values()),
        "harvest_events": harvested["events"],
        "harvest_paid_raw": harvested["paid_raw"],
        "partial_harvest_events": harvested["partial"],
        "queue_head": int(global_values["queueHead"], 16),
        "next_node": int(global_values["slot_17"], 16),
        "total_queued": int(global_values["totalQueued"], 16),
        "nonzero_user_fields": dict(nonzero),
    }


def verify_set(set_index):
    return verify_set_payload(
        saved(OUT[set_index]),
        saved(EVENTS[set_index]),
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
