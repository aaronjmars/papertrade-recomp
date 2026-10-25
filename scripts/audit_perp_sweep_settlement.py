#!/usr/bin/env python3
"""Match credited perp sweep events to public HyperCore transfers."""

import argparse
import collections
import concurrent.futures
import datetime
import decimal
import gzip
import json
import pathlib

import audit_sweep_event_census as census
import audit_sweep_settlement as core

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "audit_sweep_event_census" / "perp_core_ledger.json.gz"
EXCHANGE = core.EXCHANGE
CORE_UNIT = decimal.Decimal(100_000_000)


def credited_rows():
    return [
        row
        for row in census.verify()["nonzero_perp_requests"]
        if row.get("outcome") == "credited"
    ]


def capture_one(row):
    request_header = core.block(row["block"])
    finalize_header = core.block(row["outcome_block"])
    start_ms = int(request_header["timestamp"], 16) * 1000
    end_ms = (int(finalize_header["timestamp"], 16) + 1) * 1000 - 1
    query_window = [start_ms - 5000, end_ms + 5000]
    ledger = core.core_ledger(row["proxy"], *query_window)
    return {
        "request_tx": row["tx"],
        "finalize_tx": row["outcome_tx"],
        "request_header": request_header,
        "finalize_header": finalize_header,
        "query_window_ms": query_window,
        "core_ledger": ledger,
    }


def capture():
    rows = credited_rows()
    assert len(rows) == 73
    pairs = [None] * len(rows)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(capture_one, row): index for index, row in enumerate(rows)
        }
        for future in concurrent.futures.as_completed(futures):
            pairs[futures[future]] = future.result()
            done = sum(pair is not None for pair in pairs)
            if done % 10 == 0 or done == len(pairs):
                print(f"captured {done}/{len(pairs)} perp sweeps", flush=True)
    payload = json.dumps(
        {
            "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pin": census.PIN,
            "block_hash": json.loads(gzip.decompress(census.ARTIFACT.read_bytes()))[
                "block_hash"
            ],
            "source": {
                "evm_rpc": core.EVM_RPC,
                "core_info": core.CORE_INFO,
                "core_info_type": "userNonFundingLedgerUpdates",
            },
            "pairs": pairs,
        },
        separators=(",", ":"),
    ).encode()
    ARTIFACT.write_bytes(gzip.compress(payload, compresslevel=9, mtime=0))


def amount_raw(value):
    amount = decimal.Decimal(value) * CORE_UNIT
    assert amount == amount.to_integral_value(), value
    return int(amount)


def verify():
    saved = json.loads(gzip.decompress(ARTIFACT.read_bytes()))
    summary = census.verify()
    rows = credited_rows()
    assert saved["pin"] == summary["pin"] == census.PIN
    assert (
        saved["block_hash"]
        == json.loads(gzip.decompress(census.ARTIFACT.read_bytes()))["block_hash"]
    )
    assert saved["source"] == {
        "evm_rpc": core.EVM_RPC,
        "core_info": core.CORE_INFO,
        "core_info_type": "userNonFundingLedgerUpdates",
    }
    assert len(saved["pairs"]) == len(rows) == 73
    findings = []
    hashes = set()
    for row, pair in zip(rows, saved["pairs"]):
        assert pair["request_tx"] == row["tx"]
        assert pair["finalize_tx"] == row["outcome_tx"]
        for number, block_hash, header in (
            (row["block"], row["block_hash"], pair["request_header"]),
            (row["outcome_block"], row["outcome_block_hash"], pair["finalize_header"]),
        ):
            assert int(header["number"], 16) == number
            assert header["hash"].lower() == block_hash
        start_ms = int(pair["request_header"]["timestamp"], 16) * 1000
        end_ms = (int(pair["finalize_header"]["timestamp"], 16) + 1) * 1000 - 1
        assert pair["query_window_ms"] == [start_ms - 5000, end_ms + 5000]
        expected_raw = row["spot_raw"] + 100 * row["perp_raw"]
        assert row["credited_internal"] == expected_raw * 10**10
        transfers = [
            entry
            for entry in pair["core_ledger"]
            if start_ms <= entry.get("time", -1) <= end_ms
            and entry.get("delta", {}).get("type") == "spotTransfer"
            and entry["delta"].get("token") == "USDC"
            and entry["delta"].get("user", "").lower() == row["proxy"]
            and entry["delta"].get("destination", "").lower() == EXCHANGE
        ]
        exact_transfers = [
            entry
            for entry in transfers
            if amount_raw(entry["delta"]["amount"]) == expected_raw
            and amount_raw(entry["delta"]["usdcValue"]) == expected_raw
        ]
        conversions = [
            entry
            for entry in pair["core_ledger"]
            if start_ms <= entry.get("time", -1) <= end_ms
            and entry.get("delta", {}).get("type") == "accountClassTransfer"
            and entry["delta"].get("toPerp") is False
            and amount_raw(entry["delta"]["usdc"]) == 100 * row["perp_raw"]
        ]
        if len(transfers) != 1 or len(exact_transfers) != 1 or len(conversions) != 1:
            findings.append(
                {
                    "request_tx": row["tx"],
                    "proxy": row["proxy"],
                    "expected_raw": expected_raw,
                    "transfer_count": len(transfers),
                    "exact_transfer_count": len(exact_transfers),
                    "exact_conversion_count": len(conversions),
                }
            )
            continue
        transfer, conversion = exact_transfers[0], conversions[0]
        if (
            conversion["time"] > transfer["time"]
            or decimal.Decimal(transfer["delta"]["fee"]) != 0
            or decimal.Decimal(transfer["delta"]["nativeTokenFee"]) != 0
        ):
            findings.append({"request_tx": row["tx"], "kind": "order_or_fee_mismatch"})
        if transfer["hash"] in hashes:
            findings.append(
                {"request_tx": row["tx"], "kind": "reused_core_transfer_hash"}
            )
        hashes.add(transfer["hash"])
    return {
        "checked": len(rows),
        "unique_core_transfers": len(hashes),
        "perp_request_outcomes": dict(
            collections.Counter(
                row.get("outcome", "pending")
                for row in summary["nonzero_perp_requests"]
            )
        ),
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="refresh public Core ledger evidence"
    )
    args = parser.parse_args()
    if args.capture:
        capture()
    result = verify()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
