#!/usr/bin/env python3
"""Stream and reconcile all newest Exchange events through the audit pin."""

import argparse
import collections
import gzip
import hashlib
import json
import os
import pathlib

from atlas_exchange_withdrawal_history import rpc
from atlas_older_event_census import address_shaped_topics, fetch

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "newest_account_census"
INDEX = OUT / "events_index.json"
LEGACY = OUT / "exchange_events.json.gz"
MANIFEST = ATLAS / "manifest.json"
FACTORY = ATLAS / "factory_user_proxy_map.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
CREATION = 47854719
PIN = 48902346
WINDOW = 100_000
CHUNK_LOGS = 100_000
OPEN = "0x88451ea1189f73b554f0bf39c09868560ed149b3d788fcc933ff66ba926827f3"
CLOSED = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
ENQUEUED = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
HARVESTED = "0x81ca9b2c230070eaa84787556b1aaf18bf1e2f07ea5d3dae4819db77a1a5b224"
SWEEP_REQUESTED = "0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025"
SWEPT = "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696"
SWEEP_CLEARED = "0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e"
WITHDRAWAL = "0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75"


def pinned():
    return json.loads(MANIFEST.read_text())


def factory_users():
    users = {row["user"].lower() for row in json.loads(FACTORY.read_text())}
    assert len(users) == 22_586
    return users


def write_chunks(windows):
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.glob("events_[0-9][0-9][0-9][0-9].json.gz"):
        path.unlink()
    entries = []
    batch = []
    count = 0

    def flush():
        nonlocal batch, count
        if not batch:
            return
        name = f"events_{len(entries):04d}.json.gz"
        packed = gzip.compress(
            json.dumps(batch, separators=(",", ":")).encode(), compresslevel=9, mtime=0
        )
        (OUT / name).write_bytes(packed)
        entries.append(
            {
                "file": name,
                "from_block": batch[0]["from_block"],
                "to_block": batch[-1]["to_block"],
                "logs": count,
                "sha256": hashlib.sha256(packed).hexdigest(),
            }
        )
        batch = []
        count = 0

    for window in windows:
        batch.append(window)
        count += len(window["logs"])
        if count >= CHUNK_LOGS:
            flush()
    flush()
    m = pinned()
    index = {
        "pin": PIN,
        "block_hash": m["block_hash"],
        "exchange": EXCHANGE,
        "creation_block": CREATION,
        "window_target": WINDOW,
        "chunk_target_logs": CHUNK_LOGS,
        "chunks": entries,
    }
    INDEX.write_text(json.dumps(index, indent=2) + "\n")
    return index


def capture():
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    assert (
        rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"].lower()
        == pinned()["block_hash"]
    )

    def windows():
        total = 0
        for start in range(CREATION, PIN + 1, WINDOW):
            rows = fetch(EXCHANGE, start, min(PIN, start + WINDOW - 1))
            total += sum(len(row["logs"]) for row in rows)
            print(f"captured through {rows[-1]['to_block']}: {total} logs", flush=True)
            yield from rows

    write_chunks(windows())
    return scan()["summary"]


def repack_legacy():
    chunks = sorted(OUT.glob(LEGACY.name + ".part*"))
    assert chunks and [path.name for path in chunks] == [
        f"{LEGACY.name}.part{i:02d}" for i in range(len(chunks))
    ]
    legacy = json.loads(gzip.decompress(b"".join(path.read_bytes() for path in chunks)))
    m = pinned()
    assert legacy["pin"] == m["block"] == PIN
    assert legacy["block_hash"] == m["block_hash"]
    assert legacy["exchange"] == EXCHANGE and legacy["creation_block"] == CREATION
    write_chunks(legacy["windows"])
    result = scan()["summary"]
    for path in chunks:
        path.unlink()
    return result


def iter_windows():
    index = json.loads(INDEX.read_text())
    m = pinned()
    assert index["pin"] == m["block"] == PIN
    assert index["block_hash"] == m["block_hash"]
    assert index["exchange"] == EXCHANGE
    assert index["creation_block"] == CREATION
    assert index["window_target"] == WINDOW
    assert index["chunk_target_logs"] == CHUNK_LOGS
    cursor = CREATION
    for number, entry in enumerate(index["chunks"]):
        assert entry["file"] == f"events_{number:04d}.json.gz"
        assert entry["from_block"] == cursor
        packed = (OUT / entry["file"]).read_bytes()
        assert hashlib.sha256(packed).hexdigest() == entry["sha256"]
        windows = json.loads(gzip.decompress(packed))
        assert (
            windows and sum(len(window["logs"]) for window in windows) == entry["logs"]
        )
        for window in windows:
            start, end = window["from_block"], window["to_block"]
            assert start == cursor and start <= end <= PIN
            assert len(window["logs"]) < 10_000
            cursor = end + 1
            yield window
        assert entry["to_block"] == cursor - 1
    assert cursor == PIN + 1


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[index : index + 64], 16) for index in range(2, len(data), 64)]


def scan():
    topics = collections.Counter()
    addresses = set()
    active = {}
    node_ids = []
    enqueued = collections.Counter()
    paid = collections.Counter()
    partial_harvests = 0
    harvests = 0
    opened = 0
    previous = (-1, -1)
    logs = 0
    for window in iter_windows():
        for log in window["logs"]:
            assert log["address"].lower() == EXCHANGE and log["removed"] is False
            block_number = int(log["blockNumber"], 16)
            log_index = int(log["logIndex"], 16)
            assert window["from_block"] <= block_number <= window["to_block"]
            assert (block_number, log_index) > previous
            previous = (block_number, log_index)
            topic = log["topics"][0].lower()
            topics[topic] += 1
            addresses.update(address_shaped_topics(log))
            logs += 1
            if topic == OPEN:
                assert len(log["topics"]) == 3
                position_id = int(log["topics"][1], 16)
                assert position_id == opened
                opened += 1
                values = words(log["data"])
                assert len(values) == 6
                active[position_id] = ("0x" + log["topics"][2][-40:].lower(), values[4])
            elif topic in (CLOSED, LIQUIDATED):
                assert len(log["topics"]) == 3
                position_id = int(log["topics"][1], 16)
                user = "0x" + log["topics"][2][-40:].lower()
                assert active.pop(position_id)[0] == user
            elif topic == ENQUEUED:
                assert len(log["topics"]) == 3
                user = "0x" + log["topics"][1][-40:].lower()
                node_ids.append(int(log["topics"][2], 16))
                enqueued[user] += int(log["data"], 16)
            elif topic == HARVESTED:
                assert len(log["topics"]) == 2
                amounts = words(log["data"])
                assert len(amounts) == 2
                user = "0x" + log["topics"][1][-40:].lower()
                paid[user] += amounts[0]
                harvests += 1
                partial_harvests += amounts[1] > 0
    users = factory_users()
    storage = json.loads((ATLAS / "exchange_storage_words.json").read_text())
    assert storage["block"] == PIN and storage["block_hash"] == pinned()["block_hash"]
    slots = storage["slots"]
    margin = sum(value for _, value in active.values())
    queued = int(slots["18"], 16)
    assert logs == 4_301_896 and len(topics) == 29
    assert len(addresses) == 45_182 and users <= addresses
    assert topics[OPEN] == opened == int(slots["11"], 16) == 1_394_595
    assert topics[CLOSED] + topics[LIQUIDATED] == opened - len(active)
    assert margin == int(slots["22"], 16) >> 128
    assert node_ids == list(range(1, len(node_ids) + 1))
    assert queued == 0 and enqueued == paid
    assert topics[SWEEP_REQUESTED] == 59_027 and topics[SWEPT] == 53_198
    assert topics[SWEEP_CLEARED] == 5_827 and topics[WITHDRAWAL] == 28_643
    summary = {
        "logs": logs,
        "topics": len(topics),
        "indexed_addresses": len(addresses),
        "factory_users": len(users),
        "candidate_addresses": len(addresses | users | set(pinned()["contracts"])),
        "opens": opened,
        "terminal_positions": topics[CLOSED] + topics[LIQUIDATED],
        "active_positions": len(active),
        "active_margin_18": margin,
        "enqueue_events": len(node_ids),
        "enqueue_users": len(enqueued),
        "harvest_events": harvests,
        "partial_harvests": partial_harvests,
        "total_enqueued_18": sum(enqueued.values()),
        "total_paid_18": sum(paid.values()),
        "total_queued_18": queued,
        "topic_counts": dict(topics),
    }
    return {"summary": summary, "indexed_addresses": addresses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--repack-legacy", action="store_true")
    args = parser.parse_args()
    if args.capture:
        result = capture()
    elif args.repack_legacy:
        result = repack_legacy()
    else:
        result = scan()["summary"]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
