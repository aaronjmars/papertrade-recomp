#!/usr/bin/env python3
"""Find historical older Exchange opens that could have spent queued credit."""

import argparse
import collections
import gzip
import json
import os
import pathlib
import tempfile
import urllib.request

from atlas_deployer_scope import PIN
from atlas_older_event_census import OUT as EVENTS
from atlas_older_exchange_library import OLD_BATCH_PROXY
from atlas_older_positions import OPEN as OPEN_EVENT
from atlas_older_positions import saved, words
from atlas_older_queue_accounts import ENQUEUED, HARVESTED
from atlas_session_open_typehash import OPEN as OPEN_CALL

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_debt_history.json.gz"
CHECKPOINT = pathlib.Path(tempfile.gettempdir()) / "papertrade_debt_history_partial.json.gz"
BATCH = 50


def candidates(events):
    assert events["set"] == 0 and events["pin"] == PIN
    queue = collections.Counter()
    transactions = {}
    enqueued = harvested = opened = 0
    for window in events["windows"]:
        for log in window["logs"]:
            topic = log["topics"][0].lower()
            if topic == ENQUEUED:
                user = "0x" + log["topics"][1][-40:].lower()
                queue[user] += int(log["data"], 16)
                enqueued += 1
            elif topic == HARVESTED:
                user = "0x" + log["topics"][1][-40:].lower()
                queue[user] -= words(log["data"])[0]
                assert queue[user] >= 0
                harvested += 1
            elif topic == OPEN_EVENT:
                opened += 1
                user = "0x" + log["topics"][2][-40:].lower()
                data = words(log["data"])
                assert len(data) == 6
                margin = data[4]
                if 0 < margin <= queue[user]:
                    tx = log["transactionHash"].lower()
                    row = transactions.setdefault(
                        tx,
                        {
                            "hash": tx,
                            "block": int(log["blockNumber"], 16),
                            "positions": [],
                        },
                    )
                    assert row["block"] == int(log["blockNumber"], 16)
                    row["positions"].append(
                        {
                            "id": int(log["topics"][1], 16),
                            "user": user,
                            "instrument": data[0],
                            "side": data[1],
                            "margin": margin,
                            "leverage": data[5],
                            "queue_visible": queue[user],
                        }
                    )
    assert (enqueued, harvested, opened) == (8_452, 8_516, 398_945)
    assert all(amount == 0 for amount in queue.values())
    result = sorted(transactions.values(), key=lambda row: (row["block"], row["hash"]))
    assert len(result) == 4_611
    assert sum(len(row["positions"]) for row in result) == 15_689
    return result


def fetch_batch(url, batch):
    requests = [
        {
            "jsonrpc": "2.0",
            "id": index,
            "method": "eth_getTransactionByHash",
            "params": [row["hash"]],
        }
        for index, row in enumerate(batch)
    ]
    request = urllib.request.Request(
        url,
        json.dumps(requests).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        replies = json.load(response)
    assert isinstance(replies, list) and len(replies) == len(batch)
    by_id = {row["id"]: row for row in replies}
    assert set(by_id) == set(range(len(batch)))
    result = []
    for index, candidate in enumerate(batch):
        reply = by_id[index]
        assert "error" not in reply, reply.get("error")
        tx = reply["result"]
        assert tx["hash"].lower() == candidate["hash"]
        assert int(tx["blockNumber"], 16) == candidate["block"]
        result.append(
            {
                "hash": candidate["hash"],
                "block": candidate["block"],
                "to": tx["to"].lower(),
                "input": tx["input"].lower(),
            }
        )
    return result


def call_args(input_data):
    cursor = 0
    calls = []
    while (cursor := input_data.find(OPEN_CALL[2:], cursor)) >= 0:
        raw = input_data[cursor + 8 : cursor + 8 + 11 * 64]
        cursor += 8
        if len(raw) != 11 * 64:
            continue
        args = [int(raw[index : index + 64], 16) for index in range(0, len(raw), 64)]
        if not (
            args[0] < 1 << 160
            and args[2] in (0, 1)
            and args[3] > 0
            and args[5] in (0, 1)
        ):
            continue
        calls.append(args)
    return calls


def verify_payload(payload, events, manifest):
    assert payload["pin"] == events["pin"] == manifest["block"] == PIN
    assert payload["block_hash"] == events["block_hash"] == manifest["block_hash"]
    assert payload["method"] == "eth_getTransactionByHash"
    source = candidates(events)
    assert len(payload["transactions"]) == len(source)
    flags = collections.Counter()
    match_multiplicity = collections.Counter()
    outer_targets = collections.Counter()
    ambiguous = []
    for candidate, tx in zip(source, payload["transactions"], strict=True):
        assert (tx["hash"], tx["block"]) == (candidate["hash"], candidate["block"])
        assert tx["input"].startswith("0x") and tx["to"].startswith("0x")
        outer_targets[tx["to"]] += 1
        calls = call_args(tx["input"])
        for position in candidate["positions"]:
            matches = [
                args
                for args in calls
                if (
                    args[0],
                    args[1],
                    args[2],
                    args[3],
                    args[4],
                )
                == (
                    int(position["user"], 16),
                    position["instrument"],
                    position["side"],
                    position["margin"],
                    position["leverage"],
                )
            ]
            match_multiplicity[len(matches)] += 1
            values = {args[5] for args in matches}
            if len(values) == 1:
                flags[values.pop()] += 1
            else:
                ambiguous.append(
                    {
                        "tx": tx["hash"],
                        "position_id": position["id"],
                        "flags": sorted(values),
                    }
                )
    assert sum(flags.values()) + len(ambiguous) == 15_689
    assert match_multiplicity == {1: 15_685, 2: 4}
    assert outer_targets == {OLD_BATCH_PROXY: 4_611}
    return {
        "candidate_transactions": len(source),
        "candidate_opens": 15_689,
        "matched_use_debt_false": flags[0],
        "matched_use_debt_true": flags[1],
        "match_multiplicity": dict(match_multiplicity),
        "ambiguous": ambiguous,
        "outer_targets": dict(outer_targets),
    }


def capture():
    events = saved(EVENTS[0])
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    source = candidates(events)
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "method": "eth_getTransactionByHash",
        "transactions": [],
    }
    if CHECKPOINT.exists():
        prior = saved(CHECKPOINT)
        assert prior["pin"] == payload["pin"]
        assert prior["block_hash"] == payload["block_hash"]
        payload = prior
    start = len(payload["transactions"])
    assert [row["hash"] for row in payload["transactions"]] == [
        row["hash"] for row in source[:start]
    ]
    for offset in range(start, len(source), BATCH):
        payload["transactions"].extend(
            fetch_batch(
                os.environ["PAPERTRADE_ARCHIVE_RPC"], source[offset : offset + BATCH]
            )
        )
        if (offset // BATCH + 1) % 10 == 0:
            CHECKPOINT.write_bytes(
                gzip.compress(
                    json.dumps(payload, separators=(",", ":")).encode(), mtime=0
                )
            )
            print(f"captured {len(payload['transactions'])}/{len(source)}", flush=True)
    result = verify_payload(payload, events, manifest)
    OUT.write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    CHECKPOINT.unlink(missing_ok=True)
    return result


def verify():
    return verify_payload(
        saved(OUT),
        saved(EVENTS[0]),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), sort_keys=True))


if __name__ == "__main__":
    main()
