#!/usr/bin/env python3
"""Reconcile older factory proxies against pinned EVM and public Core data."""

import argparse
import collections
import datetime
import decimal
import gzip
import json
import os
import pathlib
import urllib.request

from atlas_deployer_scope import PIN, call, rpc_batch
from atlas_exchange_sweeps import mapping_slot, word
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
STALLED = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_proxy_core.json.gz"
CORE_INFO = "https://api.hyperliquid.xyz/info"
EXCHANGES = (
    "0x1b534e482b92bb6daff452cd12f2e35219e13493",
    "0x2ede04561914c61a5f49212609541934fd7f5901",
)
RAW_UNIT = decimal.Decimal(100_000_000)


def saved_json(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def post(payload):
    request = urllib.request.Request(
        CORE_INFO,
        json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def core_ledger(proxy, start, end):
    rows = post(
        {
            "type": "userNonFundingLedgerUpdates",
            "user": proxy,
            "startTime": start,
            "endTime": end,
        }
    )
    assert isinstance(rows, list) and len(rows) < 500, proxy
    return rows


def raw(value):
    amount = decimal.Decimal(value) * RAW_UNIT
    assert amount == amount.to_integral_value(), value
    return int(amount)


def spot_delta(proxy, entry, exchange):
    delta = entry["delta"]
    kind = delta["type"]
    if kind in ("send", "spotTransfer"):
        assert delta["token"] == "USDC"
        sender, destination = delta["user"].lower(), delta["destination"].lower()
        assert (sender == proxy) != (destination == proxy), entry
        amount = raw(delta["amount"])
        if destination == proxy:
            if kind == "send":
                assert delta["destinationDex"] in ("spot", "")
                return amount if delta["destinationDex"] == "spot" else 0
            return amount
        if kind == "spotTransfer":
            assert destination == exchange
        if kind == "send":
            assert delta["sourceDex"] == "spot"
        fee = raw(delta["fee"])
        assert (fee == 0) or delta["feeToken"] == "USDC"
        return -amount - fee
    if kind == "accountClassTransfer":
        amount = raw(delta["usdc"])
        return -amount if delta["toPerp"] else amount
    assert kind == "accountActivationGas", entry
    assert delta["token"] == "USDC"
    return -raw(delta["amount"])


def capture():
    scope, stalled = saved_json(SCOPE), saved_json(STALLED)
    assert scope["pin"] == stalled["pin"] == PIN
    assert scope["block_hash"] == stalled["block_hash"]
    pin_ms = (int(stalled["pin_header"]["timestamp"], 16) + 1) * 1000 - 1
    observed_at_ms = int(datetime.datetime.now(datetime.UTC).timestamp() * 1000)
    groups = []
    for index, factory in enumerate(scope["earlier_factory_deployments"]):
        exchange = EXCHANGES[index]
        rows = []
        for event in factory["events"]:
            log = event["log"]
            proxy = "0x" + log["topics"][2][-40:].lower()
            user = "0x" + log["topics"][1][-40:].lower()
            rows.append(
                {
                    "user": user,
                    "proxy": proxy,
                    "creation_block": int(log["blockNumber"], 16),
                    "creation_tx": log["transactionHash"].lower(),
                    "through_pin_ledger": core_ledger(proxy, 0, pin_ms),
                    "after_pin_ledger": core_ledger(proxy, pin_ms + 1, observed_at_ms),
                    "observed_spot_state": post(
                        {"type": "spotClearinghouseState", "user": proxy}
                    ),
                }
            )
        groups.append({"factory": factory["factory"], "exchange": exchange, "rows": rows})

    keccak = Keccak()
    requests = []
    targets = {}
    for group_index, group in enumerate(groups):
        for row_index, row in enumerate(group["rows"]):
            user, proxy, exchange = row["user"], row["proxy"], group["exchange"]
            operations = {
                "balance_getter": ("eth_call", [{"to": exchange, "data": "0x27e235e3" + word(user)}, hex(PIN)]),
                "balance_storage": ("eth_getStorageAt", [exchange, mapping_slot(user, 9, keccak), hex(PIN)]),
                "last_sweep_getter": ("eth_call", [{"to": exchange, "data": "0xf84a74d3" + word(proxy)}, hex(PIN)]),
                "last_sweep_storage": ("eth_getStorageAt", [exchange, mapping_slot(proxy, 32, keccak), hex(PIN)]),
                "pending_storage": ("eth_getStorageAt", [exchange, mapping_slot(user, 33, keccak), hex(PIN)]),
            }
            for key, (method, params) in operations.items():
                identifier = len(requests)
                requests.append(call(method, params, identifier))
                targets[identifier] = (group_index, row_index, key)
    results = rpc_batch(os.environ["PAPERTRADE_ARCHIVE_RPC"], requests)
    for identifier, value in results.items():
        group_index, row_index, key = targets[identifier]
        groups[group_index]["rows"][row_index].setdefault("pinned_evm", {})[key] = value

    payload = {
        "pin": PIN,
        "block_hash": scope["block_hash"],
        "pin_timestamp": stalled["pin_header"]["timestamp"],
        "pin_ms": pin_ms,
        "observed_at_ms": observed_at_ms,
        "sources": {"core_info": CORE_INFO, "core_ledger_type": "userNonFundingLedgerUpdates", "core_spot_type": "spotClearinghouseState", "evm": "PAPERTRADE_ARCHIVE_RPC"},
        "groups": groups,
    }
    OUT.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), compresslevel=9, mtime=0))
    return verify()


def verify():
    scope, stalled, saved = saved_json(SCOPE), saved_json(STALLED), saved_json(OUT)
    assert saved["pin"] == scope["pin"] == stalled["pin"] == PIN
    assert saved["block_hash"] == scope["block_hash"] == stalled["block_hash"]
    assert saved["pin_timestamp"] == stalled["pin_header"]["timestamp"]
    assert saved["pin_ms"] == (int(saved["pin_timestamp"], 16) + 1) * 1000 - 1
    assert saved["sources"]["core_info"] == CORE_INFO
    assert len(saved["groups"]) == len(EXCHANGES) == 2
    counts = collections.Counter()
    for index, (group, factory) in enumerate(zip(saved["groups"], scope["earlier_factory_deployments"])):
        assert group["factory"] == factory["factory"]
        assert group["exchange"] == EXCHANGES[index]
        assert len(group["rows"]) == len(factory["events"]) == (33, 5)[index]
        for row, event in zip(group["rows"], factory["events"]):
            log = event["log"]
            proxy, user = row["proxy"], row["user"]
            assert proxy == "0x" + log["topics"][2][-40:].lower()
            assert user == "0x" + log["topics"][1][-40:].lower()
            assert row["creation_block"] == int(log["blockNumber"], 16)
            assert row["creation_tx"] == log["transactionHash"].lower()
            evm = row["pinned_evm"]
            assert int(evm["balance_getter"], 16) == int(evm["balance_storage"], 16)
            assert int(evm["last_sweep_getter"], 16) == int(evm["last_sweep_storage"], 16)
            assert int(evm["pending_storage"], 16) == 0
            assert 0 <= int(evm["last_sweep_getter"], 16) <= PIN
            balance = 0
            assert len(row["through_pin_ledger"]) < 500
            for entry in row["through_pin_ledger"]:
                assert entry["time"] <= saved["pin_ms"]
                balance += spot_delta(proxy, entry, group["exchange"])
                counts[entry["delta"]["type"]] += 1
            assert all(saved["pin_ms"] < entry["time"] <= saved["observed_at_ms"] for entry in row["after_pin_ledger"])
            later_balance = balance + sum(spot_delta(proxy, entry, group["exchange"]) for entry in row["after_pin_ledger"])
            usdc = [item for item in row["observed_spot_state"]["balances"] if item["coin"] == "USDC" and item["token"] == 0]
            assert len(usdc) == 1
            assert later_balance == raw(usdc[0]["total"])
            assert raw(usdc[0]["hold"]) == 0
            counts["proxy_count"] += 1
            counts[f"group_{index}_ledger_entries"] += len(row["through_pin_ledger"])
            counts[f"group_{index}_nonzero_internal_balances"] += int(int(evm["balance_getter"], 16) > 0)
            counts[f"group_{index}_internal_balance_raw"] += int(evm["balance_getter"], 16)
            counts[f"group_{index}_pinned_spot_raw"] += balance
            counts["post_pin_entries"] += len(row["after_pin_ledger"])
            counts["nonzero_spot_proxies"] += int(balance > 0)
    assert counts["proxy_count"] == 38
    assert counts["group_0_ledger_entries"] == 203
    assert counts["group_1_ledger_entries"] == 38
    assert counts["group_0_pinned_spot_raw"] == 0
    assert counts["group_1_pinned_spot_raw"] == 100_000_000
    assert counts["nonzero_spot_proxies"] == 1
    assert counts["group_0_nonzero_internal_balances"] == 32
    assert counts["group_1_nonzero_internal_balances"] == 4
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh public Core and pinned archive reads")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
