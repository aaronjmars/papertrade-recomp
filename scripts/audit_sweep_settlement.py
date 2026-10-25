#!/usr/bin/env python3
"""Capture public HyperCore transfers and verify sampled Exchange sweep credits."""

import argparse
import datetime
import decimal
import json
import pathlib
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "audit_sweep_settlement" / "public_ledger.json"
SWEEPS = ATLAS / "exchange_sweep_behavior.json"
MANIFEST = ATLAS / "manifest.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
EVM_RPC = "https://rpc.hyperliquid.xyz/evm"
CORE_INFO = "https://api.hyperliquid.xyz/info"
CORE_UNIT = decimal.Decimal(100_000_000)


def post_json(url, payload):
    request = urllib.request.Request(url, json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def block(number):
    response = post_json(EVM_RPC, {"jsonrpc": "2.0", "id": 1,
                                   "method": "eth_getBlockByNumber", "params": [hex(number), False]})
    if response.get("error") or response.get("result") is None:
        raise RuntimeError(f"public EVM RPC did not return block {number}")
    header = response["result"]
    return {key: header[key] for key in ("number", "hash", "timestamp")}


def core_ledger(proxy, start_ms, end_ms):
    response = post_json(CORE_INFO, {"type": "userNonFundingLedgerUpdates",
                                          "user": proxy, "startTime": start_ms,
                                          "endTime": end_ms})
    if not isinstance(response, list):
        raise RuntimeError(f"public Core info API did not return a ledger for {proxy}")
    return response


def receipt(tx):
    for directory in (ROOT / "artifacts" / "historical", ROOT / "artifacts" / "exchange_sweeps"):
        path = directory / f"{tx}.receipt.json"
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError(f"missing saved receipt for {tx}")


def raw_amount(value):
    amount = decimal.Decimal(value) * CORE_UNIT
    if amount != amount.to_integral_value():
        raise ValueError(f"non-integral USDC raw amount: {value}")
    return int(amount)


def matching_transfer(entry, row, start_ms, end_ms):
    delta = entry.get("delta", {})
    return (start_ms <= entry.get("time", -1) <= end_ms
            and delta.get("type") == "spotTransfer"
            and delta.get("token") == "USDC"
            and delta.get("user", "").lower() == row["proxy"].lower()
            and delta.get("destination", "").lower() == EXCHANGE
            and raw_amount(delta["amount"]) == row["spot_raw"])


def verify():
    evidence = json.loads(ARTIFACT.read_text())
    sweeps = json.loads(SWEEPS.read_text())
    manifest = json.loads(MANIFEST.read_text())
    assert evidence["source"] == {"evm_rpc": EVM_RPC, "core_info": CORE_INFO,
                                  "core_info_type": "userNonFundingLedgerUpdates"}
    assert evidence["pin"] == sweeps["pin"] == manifest["block"] == 48902346
    assert evidence["block_hash"] == sweeps["block_hash"] == manifest["block_hash"]
    assert len(evidence["pairs"]) == len(sweeps["records"]) == 13
    results = []
    seen_hashes = set()
    for pair, row in zip(evidence["pairs"], sweeps["records"]):
        assert pair["request_tx"] == row["request_tx"]
        assert pair["finalize_tx"] == row["finalize_tx"]
        assert pair["proxy"].lower() == row["proxy"].lower()
        assert row["perp_raw"] == row["finalize_spot_raw"] == row["finalize_perp_raw"] == 0
        assert row["credited_internal"] == row["spot_raw"] * 10**10
        request_header, finalize_header = pair["request_header"], pair["finalize_header"]
        for tx, number, header in ((row["request_tx"], row["request_block"], request_header),
                                   (row["finalize_tx"], row["finalize_block"], finalize_header)):
            saved_receipt = receipt(tx)
            assert int(header["number"], 16) == number == int(saved_receipt["blockNumber"], 16)
            assert header["hash"].lower() == saved_receipt["blockHash"].lower()
            assert saved_receipt["transactionHash"].lower() == tx.lower()
            assert int(saved_receipt["status"], 16) == 1
        start_ms = int(request_header["timestamp"], 16) * 1000
        end_ms = (int(finalize_header["timestamp"], 16) + 1) * 1000 - 1
        assert pair["query_window_ms"] == [start_ms - 5000, end_ms + 5000]
        matches = [entry for entry in pair["core_ledger"]
                   if matching_transfer(entry, row, start_ms, end_ms)]
        assert len(matches) <= 1, f"ambiguous Core transfers for {row['proxy']}"
        if matches:
            entry = matches[0]
            delta = entry["delta"]
            assert raw_amount(delta["usdcValue"]) == row["spot_raw"]
            assert decimal.Decimal(delta["fee"]) == decimal.Decimal(delta["nativeTokenFee"]) == 0
            assert entry["hash"].startswith("0x") and len(entry["hash"]) == 66
            assert entry["hash"] not in seen_hashes
            seen_hashes.add(entry["hash"])
        results.append({"request_block": row["request_block"], "proxy": row["proxy"],
                        "spot_raw": row["spot_raw"], "matched": bool(matches),
                        "core_hash": matches[0]["hash"] if matches else None,
                        "core_time_ms": matches[0]["time"] if matches else None})
    return results


def capture():
    sweeps = json.loads(SWEEPS.read_text())
    evidence = {
        "source": {"evm_rpc": EVM_RPC, "core_info": CORE_INFO,
                   "core_info_type": "userNonFundingLedgerUpdates"},
        "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pin": sweeps["pin"], "block_hash": sweeps["block_hash"], "pairs": [],
    }
    for row in sweeps["records"]:
        request_header = block(row["request_block"])
        finalize_header = block(row["finalize_block"])
        start_ms = int(request_header["timestamp"], 16) * 1000
        end_ms = (int(finalize_header["timestamp"], 16) + 1) * 1000 - 1
        query_window = [start_ms - 5000, end_ms + 5000]
        ledger = core_ledger(row["proxy"], *query_window)
        evidence["pairs"].append({
            "request_tx": row["request_tx"], "finalize_tx": row["finalize_tx"],
            "proxy": row["proxy"], "request_header": request_header,
            "finalize_header": finalize_header, "query_window_ms": query_window,
            "core_ledger": ledger,
        })
        print(f"captured {len(evidence['pairs'])}/13: {row['request_block']} {row['proxy']}", flush=True)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(evidence, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh public Core and EVM data")
    args = parser.parse_args()
    if args.capture:
        capture()
    rows = verify()
    for row in rows:
        print(f"{row['request_block']} {row['proxy']} matched={row['matched']} "
              f"core_hash={row['core_hash']}")
    print(f"matched {sum(row['matched'] for row in rows)}/{len(rows)} sampled spot sweeps")


if __name__ == "__main__":
    main()
