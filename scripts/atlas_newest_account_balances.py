#!/usr/bin/env python3
"""Reconcile newest Exchange ordinary balances to its pinned total."""

import argparse
import collections
import gzip
import json
import os
import pathlib

from atlas_exchange_sweeps import mapping_slot, word
from atlas_factory_events import Keccak
from atlas_newest_event_census import EXCHANGE, PIN, factory_users, scan
from atlas_older_positions import rpc_batches

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
BALANCES = ROOT / "artifacts" / "newest_account_census" / "account_balances.json.gz"
MANIFEST = ATLAS / "manifest.json"
BALANCE_SELECTOR = "0x27e235e3"
TOTAL_SELECTOR = "0xa69a2ad1"
MARGIN_SELECTOR = "0x01ad056f"
QUEUE_SELECTOR = "0x53ac4b66"
NEXT_POSITION_SELECTOR = "0x899346c7"


def saved():
    return json.loads(gzip.decompress(BALANCES.read_bytes()))


def manifest():
    return json.loads(MANIFEST.read_text())


def candidate_addresses(event_scan):
    shaped = event_scan["indexed_addresses"]
    factory = factory_users()
    direct = {address.lower() for address in manifest()["contracts"]}
    return [
        {
            "address": address,
            "indexed_event": address in shaped,
            "factory_user": address in factory,
            "known_direct": address in direct,
        }
        for address in sorted(shaped | factory | direct)
    ]


def rpc_call(method, params, identifier):
    return {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}


def read_batched(url, calls, label):
    results = {}
    for start in range(0, len(calls), 1000):
        chunk = calls[start : start + 1000]
        result = rpc_batches(url, chunk)
        assert not (results.keys() & result.keys())
        results.update(result)
        print(
            f"{label}: {min(start + len(chunk), len(calls))}/{len(calls)}", flush=True
        )
    assert set(results) == {call["id"] for call in calls}
    return results


def capture_balances():
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    events = scan()
    accounts = candidate_addresses(events)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    scalar_calls = [rpc_call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    for index, selector in enumerate(
        (TOTAL_SELECTOR, MARGIN_SELECTOR, QUEUE_SELECTOR, NEXT_POSITION_SELECTOR), 1
    ):
        scalar_calls.append(
            rpc_call("eth_call", [{"to": EXCHANGE, "data": selector}, hex(PIN)], index)
        )
    scalar_calls.append(rpc_call("eth_getStorageAt", [EXCHANGE, hex(22), hex(PIN)], 5))
    scalars = rpc_batches(url, scalar_calls)
    assert scalars[0]["hash"].lower() == manifest()["block_hash"]
    calls = [
        rpc_call(
            "eth_call",
            [
                {"to": EXCHANGE, "data": BALANCE_SELECTOR + word(row["address"])},
                hex(PIN),
            ],
            index,
        )
        for index, row in enumerate(accounts)
    ]
    print(f"reading {len(accounts)} candidate balance getters", flush=True)
    results = read_batched(url, calls, "balance getters")
    keccak = Keccak()
    for index, row in enumerate(accounts):
        row["balance_getter"] = results[index]
        row["storage_slot"] = mapping_slot(row["address"], 9, keccak)
    nonzero = [row for row in accounts if int(row["balance_getter"], 16)]
    print(f"checking {len(nonzero)} nonzero raw mapping words", flush=True)
    calls = [
        rpc_call("eth_getStorageAt", [EXCHANGE, row["storage_slot"], hex(PIN)], index)
        for index, row in enumerate(nonzero)
    ]
    results = read_batched(url, calls, "raw balance slots")
    for index, row in enumerate(nonzero):
        row["balance_storage"] = results[index]
    payload = {
        "pin": PIN,
        "block_hash": manifest()["block_hash"],
        "exchange": EXCHANGE,
        "scalar_reads": {
            "total_balances": scalars[1],
            "total_locked_margin": scalars[2],
            "total_queued": scalars[3],
            "next_position_id": scalars[4],
            "slot22": scalars[5],
        },
        "candidate_basis": "all address-shaped indexed Exchange event words, all factory users, pinned manifest addresses",
        "accounts": accounts,
    }
    BALANCES.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    return verify_balances_payload(payload, events)


def verify_balances_payload(payload, events):
    m = manifest()
    assert payload["pin"] == m["block"] == PIN
    assert payload["block_hash"] == m["block_hash"]
    assert payload["exchange"] == EXCHANGE
    assert (
        payload["candidate_basis"]
        == "all address-shaped indexed Exchange event words, all factory users, pinned manifest addresses"
    )
    expected = candidate_addresses(events)
    assert len(payload["accounts"]) == len(expected)
    keccak = Keccak()
    counts = collections.Counter()
    totals = collections.Counter()
    nonzero = []
    for row, lead in zip(payload["accounts"], expected, strict=True):
        assert {key: row[key] for key in lead} == lead
        assert row["storage_slot"] == mapping_slot(row["address"], 9, keccak)
        balance = int(row["balance_getter"], 16)
        if balance:
            assert balance == int(row["balance_storage"], 16)
            nonzero.append(row)
        else:
            assert "balance_storage" not in row
        group = "factory" if row["factory_user"] else "other"
        counts[group] += bool(balance)
        totals[group] += balance
    scalars = payload["scalar_reads"]
    packed = int(scalars["slot22"], 16)
    total = int(scalars["total_balances"], 16)
    margin = int(scalars["total_locked_margin"], 16)
    queued = int(scalars["total_queued"], 16)
    assert total == packed & ((1 << 128) - 1)
    assert margin == packed >> 128
    assert (
        int(
            json.loads((ATLAS / "exchange_storage_words.json").read_text())["slots"][
                "22"
            ],
            16,
        )
        == packed
    )
    event_summary = events["summary"]
    assert event_summary["candidate_addresses"] == len(expected)
    assert event_summary["opens"] == int(scalars["next_position_id"], 16)
    assert event_summary["active_margin_18"] == margin
    assert event_summary["total_queued_18"] == queued
    position_summary = {
        "opened": event_summary["opens"],
        "terminal": event_summary["terminal_positions"],
        "active": event_summary["active_positions"],
        "active_opening_margin_18": event_summary["active_margin_18"],
    }
    queue_summary = {
        "enqueue_events": event_summary["enqueue_events"],
        "enqueue_users": event_summary["enqueue_users"],
        "harvest_events": event_summary["harvest_events"],
        "partial_harvests": event_summary["partial_harvests"],
        "enqueued_18": event_summary["total_enqueued_18"],
        "harvest_paid_18": event_summary["total_paid_18"],
        "total_queued_18": queued,
    }
    return {
        "candidate_accounts": len(expected),
        "nonzero_accounts": len(nonzero),
        "nonzero_by_group": dict(counts),
        "balance_by_group_18": dict(totals),
        "sum_candidate_balances_18": sum(totals.values()),
        "exchange_total_balances_18": total,
        "difference_18": total - sum(totals.values()),
        "total_locked_margin_18": margin,
        "total_queued_18": queued,
        "positions": position_summary,
        "queue": queue_summary,
        "top_nonzero": [
            {
                "address": row["address"],
                "balance_18": int(row["balance_getter"], 16),
                "factory_user": row["factory_user"],
            }
            for row in sorted(
                nonzero, key=lambda r: int(r["balance_getter"], 16), reverse=True
            )[:10]
        ],
    }


def verify_balances():
    return verify_balances_payload(saved(), scan())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    result = capture_balances() if args.capture else verify_balances()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
