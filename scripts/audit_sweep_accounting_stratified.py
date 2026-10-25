#!/usr/bin/env python3
"""Reconcile Exchange storage changes for the varied spot sweep sample."""

import argparse
import concurrent.futures
import gzip
import json
import os
import pathlib

from atlas_exchange_sweeps import mapping_slot, rpc
from atlas_factory_events import Keccak
from audit_sweep_settlement import EXCHANGE
from audit_sweep_settlement_stratified import OUT as SETTLEMENT
from audit_sweep_settlement_stratified import selected, words

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = (
    ROOT
    / "artifacts"
    / "audit_sweep_settlement_stratified"
    / "accounting_diffs.json.gz"
)
SWEPT_TOPIC = "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696"


def trace(tx):
    return rpc(
        os.environ["PAPERTRADE_ARCHIVE_RPC"],
        "debug_traceTransaction",
        [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}],
    )


def capture():
    samples = json.loads(gzip.decompress(SETTLEMENT.read_bytes()))["samples"]
    txs = sorted(
        {
            sample["case"][stage]["transactionHash"]
            for sample in samples
            for stage in ("request", "finalize")
        }
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        diffs = dict(zip(txs, pool.map(trace, txs), strict=True))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    payload = {
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "source": "Alchemy HyperEVM debug_traceTransaction prestateTracer diffMode",
        "diffs": diffs,
    }
    OUT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )


def changes(diff):
    return {
        stage: diff.get(stage, {}).get(EXCHANGE, {}).get("storage", {})
        for stage in ("pre", "post")
    }


def delta(storage, slot, mask=None):
    before = int(storage["pre"].get(slot, "0x0"), 16)
    after = int(storage["post"].get(slot, "0x0"), 16)
    if mask is not None:
        before &= mask
        after &= mask
    return after - before


def verify():
    source = json.loads(gzip.decompress(OUT.read_bytes()))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    settlement = json.loads(gzip.decompress(SETTLEMENT.read_bytes()))
    assert source["pin"] == settlement["pin"] == manifest["block"] == 48902346
    assert source["block_hash"] == settlement["block_hash"] == manifest["block_hash"]
    assert (
        source["source"]
        == "Alchemy HyperEVM debug_traceTransaction prestateTracer diffMode"
    )
    assert len(settlement["samples"]) == len(selected()) == 19
    keccak = Keccak()
    treasury_slot = "0x" + f"{14:064x}"
    total_slot = "0x" + f"{22:064x}"
    low128 = (1 << 128) - 1
    rows = []
    for sample in settlement["samples"]:
        case = sample["case"]
        user = case["user"]
        user_slot = mapping_slot(user, 9, keccak)
        pending_slot = mapping_slot(user, 33, keccak)
        request_tx = case["request"]["transactionHash"]
        finalize_tx = case["finalize"]["transactionHash"]
        request = changes(source["diffs"][request_tx])
        finalize = changes(source["diffs"][finalize_tx])
        expected = case["spot_raw"] * 10**10
        assert pending_slot in request["post"]
        assert int(request["post"][pending_slot], 16) & low128 == case["spot_raw"]
        assert pending_slot in finalize["pre"]
        assert int(finalize["pre"][pending_slot], 16) & low128 == case["spot_raw"]
        assert pending_slot not in finalize["post"]
        assert delta(finalize, user_slot) == expected
        request_credit = (
            treasury_slot in request["post"]
            or total_slot in request["post"]
            or user_slot in request["post"]
        )
        swept = [
            log
            for log in sample["finalize_receipt"]["logs"]
            if log["address"].lower() == EXCHANGE
            and log["topics"][0].lower() == SWEPT_TOPIC
        ]
        all_credits = sum(words(log["data"])[0] for log in swept)
        treasury = delta(finalize, treasury_slot)
        total = delta(finalize, total_slot, low128)
        assert treasury == total == all_credits
        assert delta(finalize, total_slot, ((1 << 256) - 1) ^ low128) == 0
        assert not request_credit
        rows.append(
            {
                "stratum": case["stratum"],
                "request_tx": request_tx,
                "finalize_tx": finalize_tx,
                "user_credit_18": expected,
                "tx_total_credit_18": all_credits,
                "swept_events_in_tx": len(swept),
                "request_wrote_credit_fields": request_credit,
            }
        )
    return {
        "matched": len(rows),
        "user_credit_18": sum(r["user_credit_18"] for r in rows),
        "multi_credit_finalizations": sum(r["swept_events_in_tx"] > 1 for r in rows),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="read archive transaction state diffs"
    )
    args = parser.parse_args()
    if args.capture:
        capture()
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
