#!/usr/bin/env python3
"""Pair 32 stratified Exchange withdrawals with both public HyperCore ledgers."""

import argparse
import collections
import concurrent.futures
import datetime
import decimal
import gzip
import json
import pathlib

from atlas_exchange_withdrawal_census import chosen_events, event_rows
from atlas_exchange_withdrawal_history import ARTIFACT as WITHDRAWAL_LOGS
from atlas_exchange_withdrawal_history import EXCHANGE, PIN, TOPIC
from audit_sweep_settlement import (
    CORE_INFO,
    EVM_RPC,
    block,
    core_ledger,
    post_json,
    raw_amount,
)
from audit_withdrawal_settlement import SAMPLES as EARLIER_SAMPLES

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "audit_withdrawal_settlement_stratified" / "public_ledger.json.gz"
CENSUS = ATLAS / "exchange_withdrawal_event_census.json"
MANIFEST = ATLAS / "manifest.json"


def cases():
    raw = json.loads(WITHDRAWAL_LOGS.read_text())
    census = json.loads(CENSUS.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert raw["pin"] == census["pin"] == manifest["block"] == PIN
    assert raw["block_hash"] == census["block_hash"] == manifest["block_hash"]
    chosen = chosen_events(event_rows(raw))
    assert len(chosen) == len(census["sampled_events"]) == 32
    result = []
    for (event, gap), meta in zip(chosen, census["sampled_events"], strict=True):
        assert event["address"].lower() == EXCHANGE and event["topics"][0] == TOPIC
        assert len(event["topics"]) == 2 and len(event["data"]) == 130
        block_number = int(event["blockNumber"], 16)
        log_index = int(event["logIndex"], 16)
        user = "0x" + event["topics"][1][-40:]
        debit = int(event["data"][2:66], 16)
        amount = int(event["data"][66:130], 16)
        assert gap == debit - amount * 10**10
        assert meta["tx"].lower() == event["transactionHash"].lower()
        assert meta["block"] == block_number and meta["log_index"] == log_index
        assert meta["selector"] == "0x8d09f23f"
        assert meta["event_debit_gap_18_decimals"] == str(gap)
        assert meta["hypercore_user_status"] == (0 if gap else 1)
        result.append({"tx": event["transactionHash"], "block": block_number,
                       "block_hash": event["blockHash"], "log_index": log_index,
                       "user": user, "status": meta["hypercore_user_status"],
                       "core_amount_8": amount, "internal_debit_18": debit,
                       "extra_debit_18": gap, "event": event})
    assert len({row["tx"] for row in result}) == 32
    return result


def receipt(tx):
    reply = post_json(EVM_RPC, {"jsonrpc": "2.0", "id": 1,
                                "method": "eth_getTransactionReceipt", "params": [tx]})
    if reply.get("error") or reply.get("result") is None:
        raise RuntimeError(f"public EVM RPC did not return receipt {tx}")
    return reply["result"]


def nearest_raw_amount(value):
    scaled = decimal.Decimal(value) * 100_000_000
    rounded = scaled.to_integral_value(rounding=decimal.ROUND_HALF_UP)
    residual = abs(scaled - rounded)
    assert residual <= decimal.Decimal("0.1"), f"Core API amount drift exceeds tolerance: {value}"
    return int(rounded), residual


def transfer_matches(entry, case, start_ms):
    delta = entry.get("delta", {})
    return (start_ms <= entry.get("time", -1) < start_ms + 10_000
            and delta.get("type") == "spotTransfer"
            and delta.get("token") == "USDC"
            and delta.get("user", "").lower() == EXCHANGE
            and delta.get("destination", "").lower() == case["user"].lower()
            and nearest_raw_amount(delta.get("amount", "0"))[0] == case["core_amount_8"])


def verify():
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    manifest = json.loads(MANIFEST.read_text())
    assert saved["source"] == {"evm_rpc": EVM_RPC, "core_info": CORE_INFO,
                               "core_info_type": "userNonFundingLedgerUpdates"}
    assert saved["pin"] == manifest["block"] == PIN
    assert saved["block_hash"] == manifest["block_hash"]
    expected = cases()
    assert len(saved["samples"]) == len(expected) == 32
    seen_core_hashes = set()
    rows = []
    for sample, case in zip(saved["samples"], expected, strict=True):
        assert {key: sample[key] for key in case} == case
        header, evm_receipt = sample["header"], sample["receipt"]
        assert int(header["number"], 16) == case["block"]
        assert header["hash"].lower() == case["block_hash"].lower()
        assert int(evm_receipt["blockNumber"], 16) == case["block"]
        assert evm_receipt["blockHash"].lower() == case["block_hash"].lower()
        assert evm_receipt["transactionHash"].lower() == case["tx"].lower()
        assert int(evm_receipt["status"], 16) == 1
        receipt_logs = [log for log in evm_receipt["logs"]
                        if all(log[key] == case["event"][key]
                               for key in ("address", "topics", "data", "transactionHash", "blockHash"))]
        assert len(receipt_logs) == 1
        log_index_match = int(receipt_logs[0]["logIndex"], 16) == case["log_index"]
        tx_index_match = evm_receipt["transactionIndex"] == case["event"]["transactionIndex"]
        start_ms = int(header["timestamp"], 16) * 1000
        assert sample["query_window_ms"] == [start_ms - 2000, start_ms + 10_000]
        recipient = [row for row in sample["recipient_ledger"] if transfer_matches(row, case, start_ms)]
        exchange = [row for row in sample["exchange_ledger"] if transfer_matches(row, case, start_ms)]
        assert len(recipient) == len(exchange) == 1, f"Core transfer count for {case['tx']}: {len(recipient)}, {len(exchange)}"
        assert recipient[0] == exchange[0], f"Core ledgers differ for {case['tx']}"
        transfer = recipient[0]
        assert len(transfer["hash"]) == 66 and transfer["hash"].startswith("0x")
        assert transfer["hash"] not in seen_core_hashes
        seen_core_hashes.add(transfer["hash"])
        delta = transfer["delta"]
        amount, amount_residual = nearest_raw_amount(delta["amount"])
        value, value_residual = nearest_raw_amount(delta["usdcValue"])
        assert amount == value == case["core_amount_8"]
        fee = raw_amount(delta["fee"])
        assert fee * 10**10 == case["extra_debit_18"]
        assert decimal.Decimal(delta["nativeTokenFee"]) == 0
        assert delta["feeToken"] == ("USDC" if fee else "")
        rows.append({"tx": case["tx"], "block": case["block"],
                     "status": case["status"], "amount_8": case["core_amount_8"],
                     "fee_8": fee, "core_hash": transfer["hash"],
                     "delta_ms": transfer["time"] - start_ms,
                     "api_amount_residual_raw": str(amount_residual),
                     "api_value_residual_raw": str(value_residual),
                     "log_index_match": log_index_match, "tx_index_match": tx_index_match})
    counts = collections.Counter((row["status"], row["fee_8"]) for row in rows)
    assert counts == {(0, 100_000_000): 16, (1, 0): 16}
    previous = {tx for _, tx in EARLIER_SAMPLES}
    selected = {row["tx"] for row in rows}
    assert len(previous) == 4 and len(selected & previous) == 1
    return {"pin": PIN, "matched": len(rows),
            "distinct_with_previous_four": len(selected | previous),
            "status_fee_counts": [{"core_user_exists": status, "fee_8": fee, "count": count}
                                  for (status, fee), count in sorted(counts.items())],
            "delivered_8": sum(row["amount_8"] for row in rows),
            "fee_8": sum(row["fee_8"] for row in rows),
            "max_delivery_delay_ms": max(row["delta_ms"] for row in rows),
            "provider_log_index_mismatches": sum(not row["log_index_match"] for row in rows),
            "provider_tx_index_mismatches": sum(not row["tx_index_match"] for row in rows),
            "api_amount_precision_cases": sum(decimal.Decimal(row["api_amount_residual_raw"]) > 0
                                              for row in rows),
            "max_api_amount_residual_raw": str(max(decimal.Decimal(row["api_amount_residual_raw"])
                                               for row in rows)),
            "limits": ["The sample contains 16 evenly spaced events per debit-gap class, not all withdrawals.",
                       "Some saved log-query indices differ from receipt indices across providers; exact transaction hash, block hash, emitter, topics, and data are required instead.",
                       "The public Core API formats one sampled amount slightly below an integer raw unit; nearest-unit normalization is bounded to 0.1 raw unit and reported.",
                       "Public Core API ledgers are not cryptographic state proofs.",
                       "The match checks delivery to the named Core recipient near the EVM block, not later account balances."],
            "rows": rows}


def capture():
    manifest = json.loads(MANIFEST.read_text())
    selected = cases()
    def fetch(case):
        header = block(case["block"])
        start_ms = int(header["timestamp"], 16) * 1000
        window = [start_ms - 2000, start_ms + 10_000]
        return {**case, "header": header, "receipt": receipt(case["tx"]),
                "query_window_ms": window,
                "recipient_ledger": core_ledger(case["user"], *window),
                "exchange_ledger": core_ledger(EXCHANGE, *window)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        samples = list(pool.map(fetch, selected))
    payload = {"source": {"evm_rpc": EVM_RPC, "core_info": CORE_INFO,
                          "core_info_type": "userNonFundingLedgerUpdates"},
               "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
               "pin": PIN, "block_hash": manifest["block_hash"], "samples": samples}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0))
    return verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh public Core and EVM captures")
    args = parser.parse_args()
    result = capture() if args.capture else verify()
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
