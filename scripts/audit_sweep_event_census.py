#!/usr/bin/env python3
"""Capture and check every Exchange sweep event through the pinned block."""

import argparse
import collections
import datetime
import gzip
import json
import os
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "audit_sweep_event_census" / "events.json.gz"
MANIFEST = ROOT / "atlas" / "block_48902346" / "manifest.json"
PIN = 48902346
CREATION = 47854719
WINDOW = 100000
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOPICS = {
    "requested": "0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025",
    "swept": "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696",
    "cleared": "0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e",
}


def rpc(method, params):
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    request = urllib.request.Request(
        os.environ["PAPERTRADE_ARCHIVE_RPC"],
        payload,
        {"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        data = json.loads(error.read().decode())
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]


def fetch_range(start, end):
    try:
        rows = rpc(
            "eth_getLogs",
            [
                {
                    "fromBlock": hex(start),
                    "toBlock": hex(end),
                    "address": EXCHANGE,
                    "topics": [list(TOPICS.values())],
                }
            ],
        )
    except RuntimeError as error:
        if "Log response size exceeded" not in str(error) or start == end:
            raise
        midpoint = (start + end) // 2
        return fetch_range(start, midpoint) + fetch_range(midpoint + 1, end)
    assert all(
        row["address"].lower() == EXCHANGE
        and row["topics"][0].lower() in TOPICS.values()
        and start <= int(row["blockNumber"], 16) <= end
        for row in rows
    )
    return [{"from_block": start, "to_block": end, "logs": rows}]


def capture():
    manifest = json.loads(MANIFEST.read_text())
    block_hash = rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"].lower()
    assert manifest["block"] == PIN and manifest["block_hash"].lower() == block_hash
    windows = []
    for start in range(CREATION, PIN + 1, WINDOW):
        windows.extend(fetch_range(start, min(PIN, start + WINDOW - 1)))
        print(
            f"captured through {windows[-1]['to_block']}: "
            f"{sum(len(item['logs']) for item in windows)} logs",
            flush=True,
        )
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        {
            "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pin": PIN,
            "block_hash": block_hash,
            "contract_creation_block": CREATION,
            "exchange": EXCHANGE,
            "topics": TOPICS,
            "windows": windows,
        },
        separators=(",", ":"),
    ).encode()
    ARTIFACT.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))


def words(data):
    raw = bytes.fromhex(data.removeprefix("0x"))
    assert len(raw) % 32 == 0
    return [
        int.from_bytes(raw[index : index + 32], "big")
        for index in range(0, len(raw), 32)
    ]


def verify():
    evidence = json.loads(gzip.decompress(ARTIFACT.read_bytes()))
    manifest = json.loads(MANIFEST.read_text())
    assert evidence["pin"] == manifest["block"] == PIN
    assert evidence["block_hash"] == manifest["block_hash"]
    assert evidence["exchange"] == EXCHANGE and evidence["topics"] == TOPICS
    all_logs = []
    next_block = CREATION
    for window in evidence["windows"]:
        assert window["from_block"] == next_block
        assert window["to_block"] <= PIN
        for log in window["logs"]:
            assert log["address"].lower() == EXCHANGE
            assert log["topics"][0].lower() in TOPICS.values()
            assert (
                window["from_block"]
                <= int(log["blockNumber"], 16)
                <= window["to_block"]
            )
            assert log.get("removed") is False
            all_logs.append(log)
        next_block = window["to_block"] + 1
    assert next_block == PIN + 1
    assert len({(log["transactionHash"], log["logIndex"]) for log in all_logs}) == len(
        all_logs
    )
    all_logs.sort(
        key=lambda row: (
            int(row["blockNumber"], 16),
            int(row["transactionIndex"], 16),
            int(row["logIndex"], 16),
        )
    )
    pending = {}
    counts = collections.Counter()
    anomalies = []
    nonzero_perp = []
    for log in all_logs:
        topic = log["topics"][0].lower()
        kind = next(name for name, value in TOPICS.items() if value == topic)
        counts[kind] += 1
        user = "0x" + log["topics"][1][-40:].lower()
        position = {
            "block": int(log["blockNumber"], 16),
            "block_hash": log["blockHash"].lower(),
            "tx": log["transactionHash"],
            "log_index": int(log["logIndex"], 16),
        }
        if kind == "requested":
            assert len(log["topics"]) == 3
            spot, perp, request_block = words(log["data"])
            assert request_block == position["block"]
            if user in pending:
                anomalies.append(
                    {"kind": "request_over_pending", "user": user, **position}
                )
            pending[user] = {
                "spot_raw": spot,
                "perp_raw": perp,
                "proxy": "0x" + log["topics"][2][-40:].lower(),
                **position,
            }
            if perp:
                pending[user]["user"] = user
                nonzero_perp.append(pending[user])
        elif kind == "cleared":
            assert len(log["topics"]) == 3 and words(log["data"]) == []
            previous = pending.pop(user, None)
            if previous is not None and previous["perp_raw"]:
                previous["outcome"] = "cleared"
                previous["outcome_block"] = position["block"]
                previous["outcome_block_hash"] = position["block_hash"]
            if (
                previous is None
                or previous["proxy"] != "0x" + log["topics"][2][-40:].lower()
            ):
                anomalies.append(
                    {"kind": "clear_without_matching_request", "user": user, **position}
                )
        else:
            assert len(log["topics"]) == 2
            (credited,) = words(log["data"])
            previous = pending.pop(user, None)
            if previous is None:
                anomalies.append(
                    {
                        "kind": "credit_without_request",
                        "user": user,
                        "credited_internal": credited,
                        **position,
                    }
                )
            else:
                if previous["perp_raw"]:
                    previous["outcome"] = "credited"
                    previous["outcome_block"] = position["block"]
                    previous["outcome_block_hash"] = position["block_hash"]
                    previous["outcome_tx"] = position["tx"]
                    previous["credited_internal"] = credited
                expected = (previous["spot_raw"] + 100 * previous["perp_raw"]) * 10**10
                if credited != expected:
                    anomalies.append(
                        {
                            "kind": "credit_amount_mismatch",
                            "user": user,
                            "expected": expected,
                            "actual": credited,
                            "request": previous,
                            **position,
                        }
                    )
    assert all(
        "outcome" in row or pending.get(row["user"]) is row for row in nonzero_perp
    )
    return {
        "pin": PIN,
        "windows": len(evidence["windows"]),
        "logs": len(all_logs),
        "counts": dict(counts),
        "nonzero_perp_requests": nonzero_perp,
        "anomalies": anomalies,
        "pending_at_pin": pending,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="refresh historical archive logs"
    )
    args = parser.parse_args()
    if args.capture:
        capture()
    summary = verify()
    print(
        json.dumps(
            {
                "pin": summary["pin"],
                "windows": summary["windows"],
                "logs": summary["logs"],
                "counts": summary["counts"],
                "nonzero_perp_requests": len(summary["nonzero_perp_requests"]),
                "perp_outcomes": dict(
                    collections.Counter(
                        row.get("outcome", "pending")
                        for row in summary["nonzero_perp_requests"]
                    )
                ),
                "anomalies": len(summary["anomalies"]),
                "pending_at_pin": len(summary["pending_at_pin"]),
            },
            indent=2,
        )
    )
    for row in summary["anomalies"][:20]:
        print("anomaly", json.dumps(row))


if __name__ == "__main__":
    main()
