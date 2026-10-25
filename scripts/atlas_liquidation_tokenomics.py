#!/usr/bin/env python3
"""Reconcile direct Exchange liquidation batches through Tokenomics and PAPER."""

import argparse
import concurrent.futures
import json
import os
from pathlib import Path

from atlas_exchange_batch_thresholds import artifact as batch_artifact
from atlas_exchange_batch_thresholds import read, walk
from atlas_tokenomics import (
    EXCHANGE, IMPLEMENTATION, LIQUIDATION_EVENT, LIQUIDATION_MINT, MATH,
    MODULUS, PIN, TOKEN, TOKEN_IMPLEMENTATION, TOKENOMICS, TRANSFER_EVENT,
    input_words, math_quote, rpc, storage_before, storage_delta,
)

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "liquidation_tokenomics"
OUT = ATLAS / "liquidation_tokenomics_behavior.json"
LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"


def diff_path(tx):
    return ARTIFACTS / f"{tx}.state_diff.json"


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read(ATLAS / "manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"].lower() == manifest["block_hash"]
    rows = read(ATLAS / "exchange_batch_summary_behavior.json")["rows"]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    def one(row):
        tx = row["tx"]
        path = diff_path(tx)
        if not path.exists():
            diff = rpc(url, "debug_traceTransaction",
                       [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            path.write_text(json.dumps(diff, indent=2) + "\n")
        return tx

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for tx in pool.map(one, rows):
            print("captured", tx[:10], flush=True)


def child_calls(parent, address, selector):
    return [call for call in walk(parent)
            if call is not parent and call.get("to", "").lower() == address
            and call.get("input", "")[:10] == selector]


def build():
    manifest = read(ATLAS / "manifest.json")
    summary = read(ATLAS / "exchange_batch_summary_behavior.json")
    calls_out = []
    transactions = []
    for source in summary["rows"]:
        tx = source["tx"]
        trace = read(batch_artifact(tx, "calls"))
        receipt = read(batch_artifact(tx, "receipt"))
        header = read(batch_artifact(tx, "block"))
        diff = read(diff_path(tx))
        assert receipt["transactionHash"].lower() == tx
        assert header["hash"].lower() == receipt["blockHash"].lower()
        assert header["transactions"][int(receipt["transactionIndex"], 16)].lower() == tx
        assert receipt["status"] == "0x1"
        liquidations = {
            int(log["topics"][1], 16): log for log in receipt["logs"]
            if log["address"].lower() == EXCHANGE and log["topics"][0].lower() == LIQUIDATED
        }
        assert len(liquidations) == source["completed_count"]
        tokenomics_calls = [call for call in walk(trace)
                            if call.get("to", "").lower() == TOKENOMICS
                            and call.get("input", "")[:10] == LIQUIDATION_MINT]
        assert len(tokenomics_calls) == len(liquidations)
        assert all(not call.get("error") and call["from"].lower() == EXCHANGE
                   for call in tokenomics_calls)
        tracked = storage_before(diff, TOKENOMICS, 3)
        progress = storage_before(diff, TOKENOMICS, 4)
        supply = storage_before(diff, TOKEN, 6)
        total_credit = total_tail = total_mint = total_fee = 0
        tx_calls = []
        traced_mint_events = []
        traced_transfers = []
        for ordinal, call in enumerate(tokenomics_calls):
            args = input_words(call["input"])
            assert len(args) == 5
            recipient, position_id, flag, basis, credit = args
            assert flag == 1 and basis > credit > 0
            assert position_id == source["liquidated_ids"][ordinal]
            liquidation = liquidations[position_id]
            assert int(liquidation["topics"][2], 16) == recipient
            liquidation_words = input_words("0x00000000" + liquidation["data"][2:])
            assert len(liquidation_words) == 5
            fee_a, fee_b = liquidation_words[3:5]
            assert basis - credit == fee_a + fee_b
            assert fee_a > 0 and fee_b > 0
            impls = [child for child in call.get("calls", [])
                     if child.get("to", "").lower() == IMPLEMENTATION]
            assert len(impls) == 1 and not impls[0].get("error")
            events = [log for log in impls[0].get("logs", [])
                      if log["topics"][0].lower() == LIQUIDATION_EVENT]
            assert len(events) == 1 and events[0]["address"].lower() == TOKENOMICS
            event = events[0]
            traced_mint_events.append(event)
            assert len(event["topics"]) == 3
            assert int(event["topics"][1], 16) == recipient
            assert int(event["topics"][2], 16) == position_id
            event_words = input_words("0x00000000" + event["data"][2:])
            assert len(event_words) == 6
            assert event_words[:2] == [flag, basis]
            assert event_words[2] == tracked
            assert event_words[3] == (tracked + credit) % MODULUS
            assert event_words[4] == basis
            math_calls = child_calls(call, MATH, "0x7aac24ba")
            assert len(math_calls) == 1 and not math_calls[0].get("error")
            math_args = input_words(math_calls[0]["input"])
            math_output = input_words("0x00000000" + math_calls[0]["output"][2:])
            assert len(math_args) == 6 and len(math_output) == 2
            assert math_args == [tracked, progress, basis,
                                 2 * 10**24, 100 * 10**18, 120 * 10**24]
            assert math_output == math_quote(math_args)
            assert math_output == [event_words[5], event_words[4]]
            minted, tail = math_output
            assert minted > 0 and tail > 0
            mint_calls = child_calls(call, TOKEN, "0x40c10f19")
            assert len(mint_calls) == 1 and not mint_calls[0].get("error")
            assert input_words(mint_calls[0]["input"]) == [recipient, minted]
            token_impls = [child for child in mint_calls[0].get("calls", [])
                           if child.get("to", "").lower() == TOKEN_IMPLEMENTATION]
            assert len(token_impls) == 1 and not token_impls[0].get("error")
            transfers = [log for log in token_impls[0].get("logs", [])
                         if log["topics"][0].lower() == TRANSFER_EVENT]
            assert len(transfers) == 1 and transfers[0]["address"].lower() == TOKEN
            assert int(transfers[0]["topics"][1], 16) == 0
            assert int(transfers[0]["topics"][2], 16) == recipient
            assert int(transfers[0]["data"], 16) == minted
            traced_transfers.append(transfers[0])
            tx_calls.append({
                "ordinal": ordinal, "position_id": position_id,
                "recipient": f"0x{recipient:040x}",
                "mint_basis": str(basis), "tracked_credit": str(credit),
                "exchange_fee_fields": [str(fee_a), str(fee_b)],
                "tracked_before": str(tracked), "tracked_after": str(event_words[3]),
                "tail_before": str(progress), "tail_delta": str(tail),
                "paper_minted": str(minted),
            })
            tracked = event_words[3]
            progress += tail
            total_credit += credit
            total_tail += tail
            total_mint += minted
            total_fee += fee_a + fee_b
        receipt_mint_events = [log for log in receipt["logs"]
                               if log["address"].lower() == TOKENOMICS
                               and log["topics"][0].lower() == LIQUIDATION_EVENT]
        receipt_transfers = [log for log in receipt["logs"]
                             if log["address"].lower() == TOKEN
                             and log["topics"][0].lower() == TRANSFER_EVENT
                             and int(log["topics"][1], 16) == 0]
        for expected_logs, observed_logs in ((traced_mint_events, receipt_mint_events),
                                              (traced_transfers, receipt_transfers)):
            assert len(expected_logs) == len(observed_logs) == len(tx_calls)
            assert [(log["address"].lower(), [topic.lower() for topic in log["topics"]],
                     log["data"].lower()) for log in expected_logs] == [
                (log["address"].lower(), [topic.lower() for topic in log["topics"]],
                 log["data"].lower()) for log in observed_logs]
        checks = {
            "tracked_lp_usd_slot_3": storage_delta(diff, TOKENOMICS, 3) == total_credit % MODULUS,
            "tail_progress_usd_slot_4": storage_delta(diff, TOKENOMICS, 4) == total_tail,
            "paper_total_supply_slot_6": storage_delta(diff, TOKEN, 6) == total_mint,
        }
        assert all(checks.values()), (tx, checks)
        assert tracked == (storage_before(diff, TOKENOMICS, 3) + total_credit) % MODULUS
        assert progress == storage_before(diff, TOKENOMICS, 4) + total_tail
        calls_out.extend({"tx": tx, **row} for row in tx_calls)
        transactions.append({
            "tx": tx, "block_number": source["block_number"],
            "call_count": len(tx_calls), "tracked_credit": str(total_credit),
            "exchange_fee_total": str(total_fee),
            "tail_delta": str(total_tail), "paper_minted": str(total_mint),
            "storage_checks": checks,
        })
    assert len(transactions) == 26 and len(calls_out) == 67
    assert sum(row["call_count"] for row in transactions) == 67
    prior = read(ATLAS / "tokenomics_observed_paths.json")
    prior_liquidations = {
        (row["tx"], int(row["arguments"][0])): row
        for row in prior["calls"] if row["selector"] == LIQUIDATION_MINT
    }
    assert len(prior_liquidations) == 6
    overlapping = [row for row in calls_out
                   if (row["tx"], row["position_id"]) in prior_liquidations]
    assert len(overlapping) == 3
    for row in overlapping:
        old = prior_liquidations[(row["tx"], row["position_id"])]
        assert old["arguments"][1:] == [
            "1", row["mint_basis"], row["tracked_credit"]]
        assert old["minted"] == row["paper_minted"]
    return {
        "pin_block": PIN, "pin_hash": manifest["block_hash"],
        "sample_window": "last 256 blocks ending at pin",
        "exchange_proxy": EXCHANGE, "tokenomics_proxy": TOKENOMICS,
        "paper_proxy": TOKEN, "paper_math_library": MATH,
        "selector": LIQUIDATION_MINT, "signature_status": "exact source name unresolved",
        "transaction_count": len(transactions), "liquidation_call_count": len(calls_out),
        "tokenomics_event_count": len(calls_out),
        "paper_math_call_count": len(calls_out),
        "paper_mint_count": len(calls_out),
        "storage_reconciled_transaction_count": len(transactions),
        "overlap_with_prior_tokenomics_liquidations": len(overlapping),
        "new_distinct_liquidation_calls": len(calls_out) - len(overlapping),
        "unique_liquidation_calls_across_both_ledgers": len(prior_liquidations) + len(calls_out) - len(overlapping),
        "raw_call_receipt_header_pattern": "../../artifacts/exchange_batch_thresholds/<tx>.(calls|receipt|block).json",
        "raw_state_diff_pattern": "../../artifacts/liquidation_tokenomics/<tx>.state_diff.json",
        "transactions": transactions, "calls": calls_out,
        "checked_behavior": "liquidation mint basis less the two Exchange fee fields equals tracked LP credit; Tokenomics event, PaperMath output, PAPER mint and Transfer, and slots 3,4,6 reconcile",
        "limits": [
            "The 26 direct-batch transactions contain active short liquidations only.",
            "All 67 sampled calls take the positive tail-mint branch; zero, flat, and alternate input branches rely on separate probes.",
            "The exact Tokenomics function and mint event source names remain unresolved.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("Liquidation Tokenomics:", result["transaction_count"], "transactions,",
          result["liquidation_call_count"], "mints and reconciled state diffs")


if __name__ == "__main__":
    main()
