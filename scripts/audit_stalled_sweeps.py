#!/usr/bin/env python3
"""Verify two uncredited Exchange sweeps against pinned EVM and Core evidence."""

import argparse
import collections
import datetime
import decimal
import gzip
import hashlib
import json
import os
import pathlib

import audit_sweep_event_census as census
import audit_sweep_settlement as core
from atlas_exchange_sweeps import descendants, mapping_slot, rpc
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
PRE_SPOT = "0x0000000000000000000000000000000000000801"
WRITER = "0x3333333333333333333333333333333333333333"
RECONCILE_TOPIC = "0x8da9931e615ce9dfd2d7914e0cee3246839757203d34810cde64e0d0026f75c3"


def stalled_rows():
    summary = census.verify()
    firsts = {
        row["user"]: row
        for row in summary["nonzero_perp_requests"]
        if row.get("outcome") == "cleared"
    }
    assert len(firsts) == len(summary["pending_at_pin"]) == 2
    assert firsts.keys() == summary["pending_at_pin"].keys()
    return [
        (firsts[user], {"user": user, **summary["pending_at_pin"][user]})
        for user in sorted(firsts)
    ]


def timeline(user, start_block):
    saved = json.loads(gzip.decompress(census.ARTIFACT.read_bytes()))
    events = []
    for window in saved["windows"]:
        if window["to_block"] < start_block:
            continue
        for log in window["logs"]:
            if (
                int(log["blockNumber"], 16) >= start_block
                and log["topics"][1][-40:].lower() == user[2:]
            ):
                events.append(log)
    return events


def capture():
    archive = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    pin_header = rpc(archive, "eth_getBlockByNumber", [hex(census.PIN), False])
    assert pin_header["hash"].lower() == manifest["block_hash"]
    derived = {
        row["proxy"]: row
        for row in json.loads(
            (ATLAS / "deposit_proxy_derived_runtime_map.json").read_text()
        )["rows"]
    }
    keccak = Keccak()
    cases = []
    for first, last in stalled_rows():
        proxy = first["proxy"]
        assert last["proxy"] == proxy
        assert derived[proxy]["user"] == first["user"]
        first_header = rpc(
            archive, "eth_getBlockByNumber", [hex(first["block"]), False]
        )
        last_header = rpc(archive, "eth_getBlockByNumber", [hex(last["block"]), False])
        start_ms = int(first_header["timestamp"], 16) * 1000
        end_ms = (int(pin_header["timestamp"], 16) + 1) * 1000 - 1
        pending_slot = mapping_slot(first["user"], 33, keccak)
        last_slot = mapping_slot(proxy, 32, keccak)
        case = {
            "user": first["user"],
            "proxy": proxy,
            "first_request_tx": first["tx"],
            "last_request_tx": last["tx"],
            "first_header": first_header,
            "last_header": last_header,
            "query_window_ms": [start_ms - 5000, end_ms],
            "core_ledger": core.core_ledger(proxy, start_ms - 5000, end_ms),
            "first_trace": rpc(
                archive,
                "debug_traceTransaction",
                [
                    first["tx"],
                    {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
                ],
            ),
            "last_trace": rpc(
                archive,
                "debug_traceTransaction",
                [
                    last["tx"],
                    {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
                ],
            ),
            "first_receipt": rpc(archive, "eth_getTransactionReceipt", [first["tx"]]),
            "last_receipt": rpc(archive, "eth_getTransactionReceipt", [last["tx"]]),
            "pending_slot": pending_slot,
            "pending_word": rpc(
                archive,
                "eth_getStorageAt",
                [core.EXCHANGE, pending_slot, hex(census.PIN)],
            ),
            "last_sweep_slot": last_slot,
            "last_sweep_word": rpc(
                archive, "eth_getStorageAt", [core.EXCHANGE, last_slot, hex(census.PIN)]
            ),
            "proxy_code": rpc(archive, "eth_getCode", [proxy, hex(census.PIN)]),
            "derived_runtime_sha256": derived[proxy]["runtime_sha256"],
        }
        cases.append(case)
        print(f"captured {len(cases)}/2 stalled proxies", flush=True)
    reconcile_logs = rpc(
        archive,
        "eth_getLogs",
        [
            {
                "fromBlock": hex(census.CREATION),
                "toBlock": hex(census.PIN),
                "address": core.EXCHANGE,
                "topics": [RECONCILE_TOPIC],
            }
        ],
    )
    payload = json.dumps(
        {
            "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pin": census.PIN,
            "block_hash": manifest["block_hash"],
            "pin_header": pin_header,
            "cases": cases,
            "reconcile_topic": RECONCILE_TOPIC,
            "reconcile_logs": reconcile_logs,
        },
        separators=(",", ":"),
    ).encode()
    ARTIFACT.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))


def writer_actions(trace):
    return [
        call["input"].lower()
        for call in descendants(trace)
        if call.get("to", "").lower() == WRITER
    ]


def spot_reads(trace):
    return [
        int(call["output"][2:66], 16)
        for call in descendants(trace)
        if call.get("to", "").lower() == PRE_SPOT and call.get("output")
    ]


def verify():
    saved = json.loads(gzip.decompress(ARTIFACT.read_bytes()))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin"] == manifest["block"] == census.PIN
    assert (
        saved["block_hash"]
        == saved["pin_header"]["hash"].lower()
        == manifest["block_hash"]
    )
    rows = stalled_rows()
    assert len(saved["cases"]) == len(rows) == 2
    assert saved["reconcile_topic"] == RECONCILE_TOPIC
    owner_probe = json.loads(
        (
            ROOT
            / "artifacts"
            / "exchange_sweep_probes"
            / "reconcile_owner_one.call.json"
        ).read_text()
    )
    assert any(
        log["topics"][0].lower() == RECONCILE_TOPIC
        for call in [owner_probe, *descendants(owner_probe)]
        for log in call.get("logs", [])
    )
    assert saved["reconcile_logs"] == []
    results = []
    for case, (first, last) in zip(saved["cases"], rows):
        assert case["user"] == first["user"] == last["user"]
        assert case["proxy"] == first["proxy"] == last["proxy"]
        for row, tx_key, header_key, receipt_key in (
            (first, "first_request_tx", "first_header", "first_receipt"),
            (last, "last_request_tx", "last_header", "last_receipt"),
        ):
            assert case[tx_key] == row["tx"]
            assert int(case[header_key]["number"], 16) == row["block"]
            assert case[header_key]["hash"].lower() == row["block_hash"]
            assert case[receipt_key]["transactionHash"] == row["tx"]
            assert case[receipt_key]["blockHash"].lower() == row["block_hash"]
            assert int(case[receipt_key]["status"], 16) == 1
        assert (
            hashlib.sha256(bytes.fromhex(case["proxy_code"][2:])).hexdigest()
            == case["derived_runtime_sha256"]
        )
        expected_pending = (
            last["spot_raw"] + (last["perp_raw"] << 64) + (last["block"] << 128)
        )
        assert int(case["pending_word"], 16) == expected_pending
        assert int(case["last_sweep_word"], 16) == last["block"]
        first_actions = writer_actions(case["first_trace"])
        assert len(first_actions) == 2
        assert "01000007" in first_actions[0] and "01000006" in first_actions[1]
        last_actions = writer_actions(case["last_trace"])
        assert len(last_actions) == 1 and "01000006" in last_actions[0]
        assert spot_reads(case["last_trace"]) == [last["spot_raw"], last["spot_raw"]]
        logs = [
            log
            for log in case["last_receipt"]["logs"]
            if log["address"].lower() == core.EXCHANGE
        ]
        assert [log["topics"][0].lower() for log in logs] == [
            census.TOPICS["cleared"],
            census.TOPICS["requested"],
        ]
        assert int(logs[1]["data"][2:66], 16) == last["spot_raw"]
        start_ms = int(case["first_header"]["timestamp"], 16) * 1000
        end_ms = (int(saved["pin_header"]["timestamp"], 16) + 1) * 1000 - 1
        assert case["query_window_ms"] == [start_ms - 5000, end_ms]
        assert all(
            start_ms - 5000 <= entry["time"] <= end_ms for entry in case["core_ledger"]
        )
        class_transfers = [
            entry
            for entry in case["core_ledger"]
            if entry["delta"].get("type") == "accountClassTransfer"
            and entry["delta"].get("toPerp") is False
            and core.raw_amount(entry["delta"]["usdc"]) == 100 * first["perp_raw"]
        ]
        assert len(class_transfers) == 1
        sends_to_exchange = [
            entry
            for entry in case["core_ledger"]
            if entry["delta"].get("type") == "spotTransfer"
            and entry["delta"].get("user", "").lower() == case["proxy"]
            and entry["delta"].get("destination", "").lower() == core.EXCHANGE
        ]
        assert not sends_to_exchange
        events = timeline(case["user"], first["block"])
        counts = collections.Counter(
            next(
                kind
                for kind, topic in census.TOPICS.items()
                if topic == log["topics"][0].lower()
            )
            for log in events
        )
        assert counts["swept"] == 0
        assert counts["requested"] == counts["cleared"] + 1
        assert events[-1]["transactionHash"] == last["tx"]
        assert events[-1]["topics"][0].lower() == census.TOPICS["requested"]
        results.append(
            {
                "user": case["user"],
                "proxy": case["proxy"],
                "first_request_block": first["block"],
                "last_request_block": last["block"],
                "pending_raw_spot": last["spot_raw"],
                "pending_usdc": str(decimal.Decimal(last["spot_raw"]) / 100_000_000),
                "retry_count": counts["cleared"],
                "core_entries": len(case["core_ledger"]),
                "core_sends_to_exchange": len(sends_to_exchange),
            }
        )
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="capture archive and public Core data"
    )
    args = parser.parse_args()
    if args.capture:
        capture()
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
