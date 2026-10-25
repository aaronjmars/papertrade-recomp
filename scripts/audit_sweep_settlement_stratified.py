#!/usr/bin/env python3
"""Check a deterministic, varied spot-only sweep sample end to end."""

import argparse
import collections
import concurrent.futures
import datetime
import decimal
import gzip
import json
import pathlib

from audit_sweep_event_census import ARTIFACT as CENSUS
from audit_sweep_event_census import TOPICS
from audit_sweep_settlement import (
    CORE_INFO,
    EVM_RPC,
    EXCHANGE,
    block,
    core_ledger,
    post_json,
    raw_amount,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "audit_sweep_settlement_stratified" / "public_ledger.json.gz"
EXPLORER = "https://rpc.hyperliquid.xyz/explorer"
WRITER = "0x3333333333333333333333333333333333333333"
WRITER_TOPIC = "0x8c7f585fb295f7eb1e6aeb8fba61b23a4fe60beda405f0045073b185c74412e3"


def words(data):
    blob = bytes.fromhex(data[2:])
    assert len(blob) % 32 == 0
    return [int.from_bytes(blob[i : i + 32], "big") for i in range(0, len(blob), 32)]


def candidates():
    source = json.loads(gzip.decompress(CENSUS.read_bytes()))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert source["pin"] == manifest["block"] == 48902346
    assert source["block_hash"] == manifest["block_hash"]
    pending = {}
    just_cleared = set()
    rows = []
    for window in source["windows"]:
        for log in window["logs"]:
            kind = next(
                k for k, topic in TOPICS.items() if topic == log["topics"][0].lower()
            )
            user = "0x" + log["topics"][1][-40:].lower()
            if kind == "requested":
                spot, perp, request_block = words(log["data"])
                assert request_block == int(log["blockNumber"], 16)
                pending[user] = {
                    "user": user,
                    "proxy": "0x" + log["topics"][2][-40:].lower(),
                    "request": log,
                    "spot_raw": spot,
                    "perp_raw": perp,
                    "retry_after_clear": user in just_cleared,
                }
                just_cleared.discard(user)
            elif kind == "cleared":
                pending.pop(user, None)
                just_cleared.add(user)
            else:
                old = pending.pop(user, None)
                if old is None or old["perp_raw"]:
                    continue
                (credit,) = words(log["data"])
                assert credit == old["spot_raw"] * 10**10
                old["finalize"] = log
                old["delay_blocks"] = int(log["blockNumber"], 16) - int(
                    old["request"]["blockNumber"], 16
                )
                rows.append(old)
    assert len(rows) == 53125
    return rows


def selected():
    rows = candidates()
    old = json.loads(
        (
            ROOT / "artifacts" / "audit_sweep_settlement" / "public_ledger.json"
        ).read_text()
    )
    already = {(p["request_tx"].lower(), p["proxy"].lower()) for p in old["pairs"]}
    available = [
        r
        for r in rows
        if (r["request"]["transactionHash"].lower(), r["proxy"]) not in already
    ]
    picks = []
    seen = set()

    def add(label, row):
        key = (row["request"]["transactionHash"].lower(), row["user"])
        if key not in seen:
            seen.add(key)
            picks.append({"stratum": label, **row})

    chronological = sorted(
        available,
        key=lambda r: (
            int(r["request"]["blockNumber"], 16),
            int(r["request"]["logIndex"], 16),
        ),
    )
    for i in range(8):
        add(
            f"time_octile_{i + 1}",
            chronological[round(i * (len(chronological) - 1) / 7)],
        )
    by_amount = sorted(
        available, key=lambda r: (r["spot_raw"], r["request"]["transactionHash"])
    )
    for label, row in (
        ("minimum", by_amount[0]),
        ("small", by_amount[len(by_amount) // 10]),
        ("large", by_amount[9 * len(by_amount) // 10]),
        ("maximum", by_amount[-1]),
    ):
        add(label, row)
    delayed = sorted(
        (r for r in available if r["delay_blocks"] >= 3),
        key=lambda r: (-r["delay_blocks"], r["request"]["transactionHash"]),
    )
    assert len(delayed) >= 4
    for i, row in enumerate(delayed[:4], 1):
        add(f"delay_{i}", row)
    fractional = [r for r in chronological if r["spot_raw"] % 100_000_000]
    assert len(fractional) >= 4
    for i in range(4):
        add(f"fractional_{i + 1}", fractional[round(i * (len(fractional) - 1) / 3)])
    assert len(picks) >= 16
    return picks


def receipt(tx):
    response = post_json(
        EVM_RPC,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getTransactionReceipt",
            "params": [tx],
        },
    )
    if response.get("error") or response.get("result") is None:
        raise RuntimeError(f"missing public receipt {tx}: {response.get('error')}")
    return response["result"]


def capture_one(case):
    request, finalize = case["request"], case["finalize"]
    request_header = block(int(request["blockNumber"], 16))
    finalize_header = block(int(finalize["blockNumber"], 16))
    start_ms = int(request_header["timestamp"], 16) * 1000
    end_ms = (int(finalize_header["timestamp"], 16) + 1) * 1000 - 1
    query = [start_ms - 5000, end_ms + 5000]
    proxy_ledger = core_ledger(case["proxy"], *query)
    matching = [
        entry
        for entry in proxy_ledger
        if start_ms <= entry.get("time", -1) <= end_ms
        and entry.get("delta", {}).get("type") == "spotTransfer"
        and entry["delta"].get("user", "").lower() == case["proxy"]
        and entry["delta"].get("destination", "").lower() == EXCHANGE
    ]
    exchange_ledger = core_ledger(EXCHANGE, *query)
    details = [
        post_json(EXPLORER, {"type": "txDetails", "hash": entry["hash"]})
        for entry in matching
    ]
    return {
        "case": case,
        "request_header": request_header,
        "finalize_header": finalize_header,
        "request_receipt": receipt(request["transactionHash"]),
        "finalize_receipt": receipt(finalize["transactionHash"]),
        "query_window_ms": query,
        "proxy_ledger": proxy_ledger,
        "exchange_ledger": exchange_ledger,
        "execution_details": details,
    }


def capture():
    picks = selected()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(capture_one, picks))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    payload = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "source": {
            "evm_rpc": EVM_RPC,
            "core_info": CORE_INFO,
            "core_explorer": EXPLORER,
        },
        "samples": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )


def matching_event(receipt_data, event):
    return [
        log
        for log in receipt_data["logs"]
        if all(
            log[key].lower() == event[key].lower()
            for key in ("address", "data", "transactionHash", "blockHash")
        )
        and [t.lower() for t in log["topics"]] == [t.lower() for t in event["topics"]]
    ]


def writer_actions(receipt_data, proxy, amount):
    matches = []
    for log in receipt_data["logs"]:
        if log["address"].lower() != WRITER or log["topics"][0].lower() != WRITER_TOPIC:
            continue
        if len(log["topics"]) != 2 or log["topics"][1][-40:].lower() != proxy[2:]:
            continue
        encoded = bytes.fromhex(log["data"][2:])
        assert int.from_bytes(encoded[:32], "big") == 32
        size = int.from_bytes(encoded[32:64], "big")
        action = encoded[64 : 64 + size]
        if len(action) == 100 and action[:4] == bytes.fromhex("01000006"):
            destination = "0x" + action[16:36].hex()
            token = int.from_bytes(action[36:68], "big")
            raw = int.from_bytes(action[68:100], "big")
            if destination == EXCHANGE and token == 0 and raw == amount:
                matches.append(log)
    return matches


def verify():
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin"] == manifest["block"] == 48902346
    assert saved["block_hash"] == manifest["block_hash"]
    assert saved["source"] == {
        "evm_rpc": EVM_RPC,
        "core_info": CORE_INFO,
        "core_explorer": EXPLORER,
    }
    expected = selected()
    assert len(saved["samples"]) == len(expected)
    rows = []
    seen_hashes = set()
    for sample, case in zip(saved["samples"], expected, strict=True):
        assert sample["case"] == case
        request, finalize = case["request"], case["finalize"]
        req_header, fin_header = sample["request_header"], sample["finalize_header"]
        req_receipt, fin_receipt = sample["request_receipt"], sample["finalize_receipt"]
        for event, header, receipt_data in (
            (request, req_header, req_receipt),
            (finalize, fin_header, fin_receipt),
        ):
            assert int(header["number"], 16) == int(event["blockNumber"], 16)
            assert header["hash"].lower() == event["blockHash"].lower()
            assert receipt_data["blockHash"].lower() == event["blockHash"].lower()
            assert (
                receipt_data["transactionHash"].lower()
                == event["transactionHash"].lower()
            )
            assert int(receipt_data["status"], 16) == 1
            assert len(matching_event(receipt_data, event)) == 1
        assert len(writer_actions(req_receipt, case["proxy"], case["spot_raw"])) == 1
        start_ms = int(req_header["timestamp"], 16) * 1000
        end_ms = (int(fin_header["timestamp"], 16) + 1) * 1000 - 1
        assert sample["query_window_ms"] == [start_ms - 5000, end_ms + 5000]
        transfers = [
            entry
            for entry in sample["proxy_ledger"]
            if start_ms <= entry.get("time", -1) <= end_ms
            and entry.get("delta", {}).get("type") == "spotTransfer"
            and entry["delta"].get("token") == "USDC"
            and entry["delta"].get("user", "").lower() == case["proxy"]
            and entry["delta"].get("destination", "").lower() == EXCHANGE
        ]
        assert len(transfers) == len(sample["execution_details"]) == 1
        delivered = [
            entry
            for entry in transfers
            if raw_amount(entry["delta"]["amount"]) == case["spot_raw"]
        ]
        assert len(delivered) == 1, (
            f"delivery gap {case['stratum']}: {len(delivered)} exact transfers"
        )
        transfer = delivered[0]
        assert transfer in sample["exchange_ledger"]
        assert transfer["hash"] not in seen_hashes
        seen_hashes.add(transfer["hash"])
        assert raw_amount(transfer["delta"]["usdcValue"]) == case["spot_raw"]
        assert raw_amount(transfer["delta"]["fee"]) == 0
        assert decimal.Decimal(transfer["delta"]["nativeTokenFee"]) == 0
        detail = next(
            x
            for x in sample["execution_details"]
            if x["tx"]["hash"] == transfer["hash"]
        )
        assert detail["type"] == "txDetails"
        assert detail["tx"]["error"] is None
        assert detail["tx"]["time"] == transfer["time"]
        assert detail["tx"]["user"].lower() == case["proxy"]
        assert detail["tx"]["action"] == {
            "type": "SystemSpotSendAction",
            "destination": EXCHANGE,
            "token": 0,
            "wei": case["spot_raw"],
        }
        assert words(finalize["data"]) == [case["spot_raw"] * 10**10]
        rows.append(
            {
                "stratum": case["stratum"],
                "request_block": int(request["blockNumber"], 16),
                "delay_blocks": case["delay_blocks"],
                "amount_8": case["spot_raw"],
                "core_hash": transfer["hash"],
                "core_delay_ms": transfer["time"] - start_ms,
                "request_log_index_match": int(
                    matching_event(req_receipt, request)[0]["logIndex"], 16
                )
                == int(request["logIndex"], 16),
                "finalize_log_index_match": int(
                    matching_event(fin_receipt, finalize)[0]["logIndex"], 16
                )
                == int(finalize["logIndex"], 16),
            }
        )
    return {
        "matched": len(rows),
        "amount_8": sum(row["amount_8"] for row in rows),
        "by_stratum": dict(
            collections.Counter(row["stratum"].split("_")[0] for row in rows)
        ),
        "max_delay_blocks": max(row["delay_blocks"] for row in rows),
        "max_core_delay_ms": max(row["core_delay_ms"] for row in rows),
        "provider_log_index_mismatches": sum(
            not row["request_log_index_match"] or not row["finalize_log_index_match"]
            for row in rows
        ),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="capture public EVM and Core data"
    )
    args = parser.parse_args()
    if args.capture:
        capture()
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
