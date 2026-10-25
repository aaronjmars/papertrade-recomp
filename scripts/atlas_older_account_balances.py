#!/usr/bin/env python3
"""Check pinned older Exchange balances for event users and known suite addresses."""

import argparse
import collections
import gzip
import json
import os
import pathlib
import urllib.request

from atlas_deployer_scope import PIN, call
from atlas_exchange_sweeps import mapping_slot, word
from atlas_factory_events import Keccak
from atlas_older_event_census import OUT as EVENTS
from atlas_older_event_census import address_shaped_topics

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = [
    ROOT / "artifacts" / "deployer_scope" / f"older_exchange_{index}_balances.json.gz"
    for index in range(2)
]
EXCHANGE_INDEX = (4, 23)
BALANCES = "0x27e235e3"
BATCH_SIZE = 50
EXPECTED_CANDIDATES = (463, 4_275)
EXPECTED_INDEXED = (411, 4_223)
EXPECTED_NONZERO = (369, 4_208)
EXPECTED_TOTALS = (
    84_448_601_522_052_004_894_103_251,
    640_399_665_663_368_462_177_355_391,
)
EXPECTED_FACTORY_TOTALS = (
    3_296_777_828_011_776_131_754_231,
    432_874_813_948_011_436_749_202,
)


def saved_json(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def rpc_batch_wide(url, calls):
    results = {}
    for start in range(0, len(calls), BATCH_SIZE):
        chunk = calls[start : start + BATCH_SIZE]
        request = urllib.request.Request(
            url,
            json.dumps(chunk).encode(),
            {"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            reply = json.load(response)
        assert isinstance(reply, list) and len(reply) == len(chunk)
        for row in reply:
            assert "error" not in row, row
            assert row["id"] not in results
            results[row["id"]] = row["result"]
    assert set(results) == {row["id"] for row in calls}
    return results


def candidates(events, scope, set_index):
    seen_in_events = set()
    for window in events["windows"]:
        for log in window["logs"]:
            seen_in_events.update(address_shaped_topics(log))
    factory = {
        "0x" + event["log"]["topics"][1][-40:].lower()
        for event in scope["earlier_factory_deployments"][set_index]["events"]
    }
    known_direct = {row["address"] for row in scope["rows"]}
    all_accounts = sorted(seen_in_events | factory | known_direct | {scope["deployer"]})
    return [
        {
            "address": address,
            "event_indexed_candidate": address in seen_in_events,
            "factory_user": address in factory,
            "known_direct": address in known_direct,
            "deployer": address == scope["deployer"],
        }
        for address in all_accounts
    ]


def capture_set(set_index):
    events, scope = saved_json(EVENTS[set_index]), saved_json(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert events["pin"] == scope["pin"] == manifest["block"] == PIN
    assert events["block_hash"] == scope["block_hash"] == manifest["block_hash"]
    assert events["set"] == set_index
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    accounts = candidates(events, scope, set_index)
    exchange = scope["rows"][EXCHANGE_INDEX[set_index]]["address"]
    keccak = Keccak()
    calls = [call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    for index, account in enumerate(accounts):
        address = account["address"]
        slot = mapping_slot(address, 9, keccak)
        account["storage_slot"] = slot
        calls.append(
            call(
                "eth_call",
                [{"to": exchange, "data": BALANCES + word(address)}, hex(PIN)],
                1 + index,
            )
        )
    result = rpc_batch_wide(os.environ["PAPERTRADE_ARCHIVE_RPC"], calls)
    assert result[0]["hash"].lower() == manifest["block_hash"]
    for index, account in enumerate(accounts):
        account["balance_getter"] = result[1 + index]
    nonzero_indices = [
        index
        for index, account in enumerate(accounts)
        if int(account["balance_getter"], 16) > 0
    ]
    storage_calls = [
        call(
            "eth_getStorageAt",
            [exchange, accounts[index]["storage_slot"], hex(PIN)],
            1 + len(accounts) + offset,
        )
        for offset, index in enumerate(nonzero_indices)
    ]
    storage_results = rpc_batch_wide(
        os.environ["PAPERTRADE_ARCHIVE_RPC"], storage_calls
    )
    for offset, index in enumerate(nonzero_indices):
        accounts[index]["balance_storage"] = storage_results[1 + len(accounts) + offset]
    for account in accounts:
        account.setdefault("balance_storage", None)
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "set": set_index,
        "exchange": exchange,
        "candidate_basis": "address-shaped indexed event words, factory users, known direct creations, deployer",
        "accounts": accounts,
    }
    summary = verify_set_payload(payload, events, scope, manifest)
    OUT[set_index].write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return summary


def verify_set_payload(saved, events, scope, manifest):
    set_index = saved["set"]
    assert set_index in (0, 1) and events["set"] == set_index
    assert saved["pin"] == events["pin"] == scope["pin"] == manifest["block"] == PIN
    assert (
        saved["block_hash"]
        == events["block_hash"]
        == scope["block_hash"]
        == manifest["block_hash"]
    )
    exchange = scope["rows"][EXCHANGE_INDEX[set_index]]
    assert saved["exchange"] == exchange["address"]
    assert (
        saved["candidate_basis"]
        == "address-shaped indexed event words, factory users, known direct creations, deployer"
    )
    expected = candidates(events, scope, set_index)
    assert len(saved["accounts"]) == len(expected)
    keccak = Keccak()
    counts = collections.Counter()
    totals = collections.Counter()
    nonzero = []
    for account, lead in zip(saved["accounts"], expected):
        assert {key: account[key] for key in lead} == lead
        assert account["storage_slot"] == mapping_slot(account["address"], 9, keccak)
        amount = int(account["balance_getter"], 16)
        if amount:
            assert amount == int(account["balance_storage"], 16)
        else:
            assert account["balance_storage"] is None
        assert 0 <= amount < 1 << 256
        if amount:
            assert account["event_indexed_candidate"]
            nonzero.append(
                {
                    "address": account["address"],
                    "raw_balance": amount,
                    "factory_user": account["factory_user"],
                    "event_indexed_candidate": account["event_indexed_candidate"],
                }
            )
        group = "factory" if account["factory_user"] else "other"
        counts[group] += amount > 0
        totals[group] += amount
    total_balances = int(exchange["exchange_getters"]["totalBalances"], 16)
    assert len(expected) == EXPECTED_CANDIDATES[set_index]
    assert (
        sum(row["event_indexed_candidate"] for row in expected)
        == EXPECTED_INDEXED[set_index]
    )
    assert len(nonzero) == EXPECTED_NONZERO[set_index]
    assert totals["factory"] == EXPECTED_FACTORY_TOTALS[set_index]
    assert sum(totals.values()) == total_balances == EXPECTED_TOTALS[set_index]
    assert counts == (
        {"factory": 32, "other": 337}
        if set_index == 0
        else {"factory": 4, "other": 4_204}
    )
    return {
        "set": set_index,
        "candidate_accounts": len(expected),
        "indexed_candidates": sum(row["event_indexed_candidate"] for row in expected),
        "factory_users": sum(row["factory_user"] for row in expected),
        "nonzero_counts": dict(counts),
        "balance_totals_raw": dict(totals),
        "sum_candidate_balances_raw": sum(totals.values()),
        "exchange_total_balances_raw": total_balances,
        "unmatched_total_raw": total_balances - sum(totals.values()),
        "nonzero_account_count": len(nonzero),
        "top_nonzero_accounts": sorted(
            nonzero, key=lambda row: row["raw_balance"], reverse=True
        )[:10],
    }


def verify_set(set_index):
    return verify_set_payload(
        saved_json(OUT[set_index]),
        saved_json(EVENTS[set_index]),
        saved_json(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-set", type=int, choices=(0, 1))
    args = parser.parse_args()
    if args.capture_set is not None:
        capture_set(args.capture_set)
    summaries = [verify_set(index) for index in range(2) if OUT[index].exists()]
    print(json.dumps(summaries, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
