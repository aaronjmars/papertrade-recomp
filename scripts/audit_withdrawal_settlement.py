#!/usr/bin/env python3
"""Match four exact EVM withdrawal samples to public HyperCore transfers and fees."""

import argparse
import datetime
import decimal
import json
import pathlib

from audit_sweep_settlement import (ATLAS, CORE_INFO, EVM_RPC, EXCHANGE, ROOT,
                                    block, core_ledger, raw_amount)


ARTIFACT = ROOT / "artifacts" / "audit_withdrawal_settlement" / "public_ledger.json"
DIRECT = ATLAS / "exchange_direct_withdrawal_behavior.json"
SIGNED = ATLAS / "exchange_withdrawal_trace_corpus.json"
MANIFEST = ATLAS / "manifest.json"
TOPIC = "0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75"
SAMPLES = (
    ("direct", "0x7c69ba558b4076ef20f880f89d910168cbd92e3cc0a2f70a564b2117f46fa6ac"),
    ("direct", "0xd11efba2b91838576b957f7297677b46676ec7a27db60331377212f4de8ba771"),
    ("signed", "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5"),
    ("signed", "0x0f15e1a5d5bcaf5764df51439680fa8b3f748b47240d5c89c31be8d487a49a90"),
)


def cases():
    direct = json.loads(DIRECT.read_text())["historical_direct_calls"]
    signed = json.loads(SIGNED.read_text())["calls"]
    result = []
    for kind, tx in SAMPLES:
        rows = [row for row in (direct if kind == "direct" else signed) if row["tx"] == tx]
        assert len(rows) == 1, f"ambiguous {kind} withdrawal sample: {tx}"
        row = rows[0]
        if kind == "direct":
            result.append({"kind": kind, "tx": tx, "block": row["block"],
                           "user": row["caller"], "raw_amount_6": int(row["raw_amount"]),
                           "core_amount_8": int(row["core_amount"]),
                           "internal_debit_18": int(row["internal_debit"]),
                           "extra_debit_18": int(row["extra_debit"]),
                           "core_user_exists": bool(row["core_user_status_word"])})
        else:
            result.append({"kind": kind, "tx": tx, "block": row["block"],
                           "user": row["user"],
                           "raw_amount_6": int(row["raw_amount_6_decimals"]),
                           "core_amount_8": int(row["corewriter_spot_send_amount_8_decimals"]),
                           "internal_debit_18": int(row["event_internal_debit_18_decimals"]),
                           "extra_debit_18": int(row["extra_debit_18_decimals"]),
                           "core_user_exists": row["core_user_exists"]})
    assert len(result) == 4
    return result


def receipt(tx):
    for directory in (ROOT / "artifacts" / "historical",
                      ROOT / "artifacts" / "exchange_core_withdrawal"):
        path = directory / f"{tx}.receipt.json"
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError(f"missing saved EVM receipt for {tx}")


def matching_transfer(entry, case, start_ms):
    delta = entry.get("delta", {})
    return (start_ms <= entry.get("time", -1) < start_ms + 1000
            and delta.get("type") == "spotTransfer"
            and delta.get("token") == "USDC"
            and delta.get("user", "").lower() == EXCHANGE
            and delta.get("destination", "").lower() == case["user"].lower()
            and raw_amount(delta["amount"]) == case["core_amount_8"])


def verify():
    evidence = json.loads(ARTIFACT.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert evidence["source"] == {"evm_rpc": EVM_RPC, "core_info": CORE_INFO,
                                  "core_info_type": "userNonFundingLedgerUpdates"}
    assert evidence["pin"] == manifest["block"] == 48902346
    assert evidence["block_hash"] == manifest["block_hash"]
    assert len(evidence["samples"]) == len(SAMPLES) == 4
    result = []
    seen_hashes = set()
    for sample, case in zip(evidence["samples"], cases()):
        assert {key: sample[key] for key in case} == case
        assert case["core_amount_8"] == case["raw_amount_6"] * 100
        assert case["extra_debit_18"] == (0 if case["core_user_exists"] else 10**18)
        assert case["internal_debit_18"] == case["raw_amount_6"] * 10**12 + case["extra_debit_18"]
        header = sample["header"]
        saved_receipt = receipt(case["tx"])
        assert int(header["number"], 16) == case["block"] == int(saved_receipt["blockNumber"], 16)
        assert header["hash"].lower() == saved_receipt["blockHash"].lower()
        assert saved_receipt["transactionHash"].lower() == case["tx"].lower()
        assert int(saved_receipt["status"], 16) == 1
        event_logs = [log for log in saved_receipt["logs"]
                      if log["address"].lower() == EXCHANGE and log["topics"][0] == TOPIC
                      and log["topics"][1][-40:].lower() == case["user"][2:].lower()
                      and int(log["data"][2:66], 16) == case["internal_debit_18"]
                      and int(log["data"][66:130], 16) == case["core_amount_8"]]
        assert len(event_logs) == 1, f"missing exact EVM withdrawal event in {case['tx']}"
        start_ms = int(header["timestamp"], 16) * 1000
        assert sample["query_window_ms"] == [start_ms - 2000, start_ms + 5000]
        recipient_matches = [entry for entry in sample["recipient_ledger"]
                             if matching_transfer(entry, case, start_ms)]
        exchange_matches = [entry for entry in sample["exchange_ledger"]
                            if matching_transfer(entry, case, start_ms)]
        assert len(recipient_matches) == len(exchange_matches) == 1
        transfer = recipient_matches[0]
        assert transfer == exchange_matches[0]
        assert transfer["hash"].startswith("0x") and len(transfer["hash"]) == 66
        assert transfer["hash"] not in seen_hashes
        seen_hashes.add(transfer["hash"])
        delta = transfer["delta"]
        assert raw_amount(delta["usdcValue"]) == case["core_amount_8"]
        fee_raw = raw_amount(delta["fee"])
        assert fee_raw * 10**10 == case["extra_debit_18"]
        assert decimal.Decimal(delta["nativeTokenFee"]) == 0
        assert delta["feeToken"] == ("USDC" if fee_raw else "")
        result.append({"tx": case["tx"], "kind": case["kind"],
                       "core_user_exists": case["core_user_exists"],
                       "delivered_8": case["core_amount_8"], "fee_8": fee_raw,
                       "core_hash": transfer["hash"], "time_ms": transfer["time"]})
    return result


def capture():
    manifest = json.loads(MANIFEST.read_text())
    evidence = {
        "source": {"evm_rpc": EVM_RPC, "core_info": CORE_INFO,
                   "core_info_type": "userNonFundingLedgerUpdates"},
        "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pin": manifest["block"], "block_hash": manifest["block_hash"], "samples": [],
    }
    for case in cases():
        header = block(case["block"])
        start_ms = int(header["timestamp"], 16) * 1000
        window = [start_ms - 2000, start_ms + 5000]
        evidence["samples"].append({
            **case, "header": header, "query_window_ms": window,
            "recipient_ledger": core_ledger(case["user"], *window),
            "exchange_ledger": core_ledger(EXCHANGE, *window),
        })
        print(f"captured {len(evidence['samples'])}/4: {case['kind']} {case['tx']}", flush=True)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(evidence, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh public EVM and Core data")
    args = parser.parse_args()
    if args.capture:
        capture()
    rows = verify()
    for row in rows:
        print(f"{row['kind']} {row['tx']} delivered={row['delivered_8']} "
              f"fee={row['fee_8']} core_hash={row['core_hash']}")
    print(f"matched {len(rows)} direct/signed withdrawals; "
          f"new-account fee cases={sum(row['fee_8'] > 0 for row in rows)}")


if __name__ == "__main__":
    main()
