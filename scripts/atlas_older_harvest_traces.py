#!/usr/bin/env python3
"""Verify two historical older Exchange harvest transactions against storage diffs."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib

from atlas_deployer_scope import IMPLEMENTATION_SLOT, PIN, call, rpc_batch
from atlas_exchange_sweeps import mapping_slot
from atlas_factory_events import Keccak
from atlas_older_event_census import OUT as EVENTS
from atlas_older_positions import saved
from atlas_older_queue_accounts import HARVESTED
from atlas_older_runtime_links import OLD_EXCHANGE_LIBRARY
from atlas_older_runtime_links import OUT as LINKED_LIBRARIES

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_exchange_harvest_traces.json.gz"
SAMPLES = (
    (
        "partial",
        "0xc0d5ec453f06c0ba0712457bdc956179873ea83fa7934d2f7ea3c13d0bb03c6b",
        (12,),
    ),
    (
        "final",
        "0x442f607e6eb1fa2534cdcda782c7f03804501b3e65ece2de6d3356c272003436",
        (14, 15),
    ),
)
EXCHANGE_INDEX = 4
IMPLEMENTATION_INDEX = 3


def harvest_logs(events):
    by_tx = {}
    for window in events["windows"]:
        for log in window["logs"]:
            if log["topics"][0].lower() == HARVESTED:
                by_tx.setdefault(log["transactionHash"].lower(), []).append(log)
    return by_tx


def capture():
    events, scope = saved(EVENTS[0]), saved(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert events["block_hash"] == scope["block_hash"] == manifest["block_hash"]
    log_map = harvest_logs(events)
    exchange = scope["rows"][EXCHANGE_INDEX]["address"]
    implementation = scope["rows"][IMPLEMENTATION_INDEX]["address"]
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    samples = []
    for label, tx, _ in SAMPLES:
        logs = log_map[tx]
        block = int(logs[0]["blockNumber"], 16)
        result = rpc_batch(
            url,
            [
                call("eth_getTransactionByHash", [tx], 0),
                call("eth_getTransactionReceipt", [tx], 1),
                call(
                    "debug_traceTransaction",
                    [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}],
                    2,
                ),
                call(
                    "debug_traceTransaction",
                    [
                        tx,
                        {
                            "tracer": "prestateTracer",
                            "tracerConfig": {"diffMode": True},
                        },
                    ],
                    3,
                ),
                call("eth_getCode", [exchange, hex(block)], 4),
                call("eth_getCode", [implementation, hex(block)], 5),
                call(
                    "eth_getStorageAt", [exchange, IMPLEMENTATION_SLOT, hex(block)], 6
                ),
                call("eth_getCode", [OLD_EXCHANGE_LIBRARY, hex(block)], 7),
            ],
        )
        samples.append(
            {
                "label": label,
                "tx": tx,
                "transaction": result[0],
                "receipt": result[1],
                "call_trace": result[2],
                "state_diff": result[3],
                "proxy_code_sha256": hashlib.sha256(
                    bytes.fromhex(result[4][2:])
                ).hexdigest(),
                "implementation_code_sha256": hashlib.sha256(
                    bytes.fromhex(result[5][2:])
                ).hexdigest(),
                "implementation_slot": result[6],
                "library_code_sha256": hashlib.sha256(
                    bytes.fromhex(result[7][2:])
                ).hexdigest(),
            }
        )
    payload = {"pin": PIN, "block_hash": manifest["block_hash"], "samples": samples}
    summary = verify_payload(payload, events, scope, manifest)
    OUT.write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return summary


def verify_payload(payload, events, scope, manifest):
    assert payload["pin"] == events["pin"] == scope["pin"] == manifest["block"] == PIN
    assert (
        payload["block_hash"]
        == events["block_hash"]
        == scope["block_hash"]
        == manifest["block_hash"]
    )
    assert len(payload["samples"]) == len(SAMPLES)
    exchange_row = scope["rows"][EXCHANGE_INDEX]
    implementation_row = scope["rows"][IMPLEMENTATION_INDEX]
    exchange, implementation = exchange_row["address"], implementation_row["address"]
    log_map = harvest_logs(events)
    linked = saved(LINKED_LIBRARIES)
    assert linked["pin"] == PIN and linked["block_hash"] == manifest["block_hash"]
    assert "0x" + Keccak()(b"harvest(uint256)").hex()[:8] == "0xddc63262"
    results = []
    for sample, (label, tx, node_ids) in zip(payload["samples"], SAMPLES):
        logs = log_map[tx]
        transaction, receipt = sample["transaction"], sample["receipt"]
        assert sample["label"] == label and sample["tx"] == tx
        assert transaction["hash"].lower() == receipt["transactionHash"].lower() == tx
        assert int(receipt["status"], 16) == 1
        assert receipt["blockHash"].lower() == logs[0]["blockHash"].lower()
        assert len(logs) == len(node_ids) == len(receipt["logs"])
        assert all(
            any(
                row["address"].lower() == exchange
                and row["topics"] == log["topics"]
                and row["data"] == log["data"]
                and row["logIndex"] == log["logIndex"]
                for row in receipt["logs"]
            )
            for log in logs
        )
        assert sample["implementation_slot"][-40:].lower() == implementation[2:]
        assert (
            sample["proxy_code_sha256"]
            == hashlib.sha256(bytes.fromhex(exchange_row["runtime"][2:])).hexdigest()
        )
        assert (
            sample["implementation_code_sha256"]
            == hashlib.sha256(
                bytes.fromhex(implementation_row["runtime"][2:])
            ).hexdigest()
        )
        assert (
            sample["library_code_sha256"]
            == hashlib.sha256(
                bytes.fromhex(linked["libraries"][OLD_EXCHANGE_LIBRARY][2:])
            ).hexdigest()
        )
        root = sample["call_trace"]
        assert root["to"].lower() == exchange and root["input"] == transaction["input"]
        assert root["input"].startswith("0xddc63262") and not root.get("error")
        assert len(root.get("calls", [])) == 1
        delegate = root["calls"][0]
        assert (
            delegate["type"] == "DELEGATECALL"
            and delegate["to"].lower() == implementation
        )
        assert (
            delegate["from"].lower() == exchange and delegate["input"] == root["input"]
        )
        assert not delegate.get("error") and len(delegate.get("calls", [])) == 1
        library = delegate["calls"][0]
        assert (
            library["type"] == "DELEGATECALL"
            and library["to"].lower() == OLD_EXCHANGE_LIBRARY
        )
        assert library["input"].startswith("0x79810ffe") and not library.get("error")

        diff = sample["state_diff"]
        before = diff["pre"][exchange]["storage"]
        after = diff["post"][exchange]["storage"]
        keccak = Keccak()

        def values(slot, before=before, after=after):
            return int(before.get(slot, "0x0"), 16), int(after.get(slot, "0x0"), 16)

        users = {"0x" + log["topics"][1][-40:].lower() for log in logs}
        assert len(users) == 1
        user = next(iter(users))
        paid = sum(int(log["data"][2:66], 16) for log in logs)
        for log, node_id in zip(logs, node_ids):
            event_paid = int(log["data"][2:66], 16)
            remaining = int(log["data"][66:130], 16)
            node_amount = f"0x{int(mapping_slot(node_id, 15, keccak), 16) + 1:064x}"
            old, new = values(node_amount)
            assert old - new == event_paid and new == remaining
        balance_before, balance_after = values(mapping_slot(user, 9, keccak))
        queued_before, queued_after = values(mapping_slot(user, 19, keccak))
        global_before, global_after = values(f"0x{18:064x}")
        packed_before, packed_after = values(f"0x{22:064x}")
        bucket_before, bucket_after = values(f"0x{27:064x}")
        low128 = (1 << 128) - 1
        assert balance_after - balance_before == paid
        assert queued_before - queued_after == global_before - global_after == paid
        assert (packed_after & low128) - (packed_before & low128) == paid
        assert packed_after >> 128 == packed_before >> 128
        assert bucket_before == paid and bucket_after == 0
        assert f"0x{14:064x}" not in before and f"0x{14:064x}" not in after
        if label == "partial":
            assert int(logs[0]["data"][66:130], 16) > 0
            assert f"0x{16:064x}" not in before and f"0x{16:064x}" not in after
        else:
            assert int(logs[0]["data"][66:130], 16) == 0
            assert int(logs[1]["data"][66:130], 16) > 0
            assert values(f"0x{16:064x}") == (14, 15)
            assert values(mapping_slot(user, 20, keccak)) == (14, 15)
        results.append(
            {
                "label": label,
                "tx": tx,
                "harvest_events": len(logs),
                "paid_raw": paid,
                "user": user,
                "node_ids": list(node_ids),
                "balance_credit_raw": balance_after - balance_before,
            }
        )
    return results


def verify():
    return verify_payload(
        saved(OUT),
        saved(EVENTS[0]),
        saved(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        print(json.dumps(capture(), sort_keys=True))
    else:
        print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
