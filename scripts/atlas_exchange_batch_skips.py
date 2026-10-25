#!/usr/bin/env python3
"""Explain one historical partial liquidation batch from transaction prestate."""

import argparse
import json
import os
from pathlib import Path

from atlas_exchange_positions import EXCHANGE, position_slot, rpc
from atlas_exchange_liquidation_price import calculate
from atlas_exchange_queue_layout import mapped

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_batch_summary"
OUT = ATLAS / "exchange_batch_skip_behavior.json"
TX = "0xdfe4d997bd2d8ee4d5a96d0759e38a6b24e9719c40545eae6ea406b43ed119f9"
IDS = (1392363, 1394076, 1394080)
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
BBO = "0x000000000000000000000000000000000000080e"
LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
SUMMARY = "0x0bb3f42f9fe304326ba30302693425c1db2e2f6a4675df44372fc0af5ce73706"


def read(path):
    return json.loads(path.read_text())


def walk(node):
    yield node
    for child in node.get("calls", []):
        yield from walk(child)


def word(storage, slot):
    return int(storage[f"0x{slot:064x}"], 16)


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read(ATLAS / "manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(manifest["block"]), False])["hash"].lower() == manifest["block_hash"]
    requests = (
        ("partial_tx_prestate.json", "debug_traceTransaction", [TX, {"tracer": "prestateTracer"}]),
        ("partial_tx_calls.json", "debug_traceTransaction",
         [TX, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
        ("partial_tx_receipt.json", "eth_getTransactionReceipt", [TX]),
    )
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for name, method, params in requests:
        path = ARTIFACTS / name
        if not path.exists():
            path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")
    receipt = read(ARTIFACTS / "partial_tx_receipt.json")
    header_path = ARTIFACTS / "partial_tx_block.json"
    if not header_path.exists():
        header_path.write_text(json.dumps(rpc(url, "eth_getBlockByHash",
                                              [receipt["blockHash"], False]), indent=2) + "\n")


def build():
    manifest = read(ATLAS / "manifest.json")
    summary = read(ATLAS / "exchange_batch_summary_behavior.json")
    record = next(row for row in summary["rows"] if row["tx"] == TX)
    assert record["requested_ids"] == list(IDS)
    assert record["liquidated_ids"] == [IDS[0]]
    prestate = read(ARTIFACTS / "partial_tx_prestate.json")
    trace = read(ARTIFACTS / "partial_tx_calls.json")
    receipt = read(ARTIFACTS / "partial_tx_receipt.json")
    header = read(ARTIFACTS / "partial_tx_block.json")
    assert receipt["transactionHash"].lower() == TX
    assert int(receipt["blockNumber"], 16) == record["block_number"] == 48902280
    assert header["hash"].lower() == receipt["blockHash"].lower()
    assert int(header["number"], 16) == record["block_number"]
    assert int(receipt["transactionIndex"], 16) == 8
    assert header["transactions"][8].lower() == TX
    assert receipt["status"] == "0x1"
    assert trace["to"].lower() == EXCHANGE and trace["input"].startswith("0x599dc539")
    assert not trace.get("error") and int(trace["output"], 16) == 1
    calls = list(walk(trace))
    oracle = [call for call in calls if call.get("to", "").lower() == ORACLE
              and call.get("input", "")[:10] == "0xc0182669"]
    assert len(oracle) == 1 and not oracle[0].get("error")
    assert int(oracle[0]["input"][10:], 16) == 1
    price = int(oracle[0]["output"], 16)
    bbo = [call for call in calls if call.get("to", "").lower() == BBO]
    assert len(bbo) == 1 and not bbo[0].get("error")
    bbo_words = bytes.fromhex(bbo[0]["output"][2:])
    assert len(bbo_words) == 64
    bid, ask = (int.from_bytes(bbo_words[i:i + 32], "big") for i in (0, 32))
    assert 0 < bid <= ask and price == (bid + ask) // 2
    tokenomics = [call for call in calls if call.get("to", "").lower() == TOKENOMICS
                  and call.get("input", "")[:10] == "0x0efdf838"]
    assert len(tokenomics) == 1 and not tokenomics[0].get("error")
    logs = [log for log in receipt["logs"] if log["address"].lower() == EXCHANGE]
    liquidations = [log for log in logs if log["topics"][0].lower() == LIQUIDATED]
    summaries = [log for log in logs if log["topics"][0].lower() == SUMMARY]
    assert len(liquidations) == len(summaries) == 1
    assert int(liquidations[0]["topics"][1], 16) == IDS[0]
    assert int(liquidations[0]["data"][2:66], 16) == price
    assert summaries[0]["data"].lower() == record["summary_data"].lower()
    storage = prestate[EXCHANGE]["storage"]
    positions = []
    instrument_words = {}
    for position_id in IDS:
        base = position_slot(position_id)
        first, second = word(storage, base), word(storage, base + 1)
        instrument = (first >> 160) & 0xffffffff
        entry = first >> 192
        leverage = (second >> 128) & 0xffffffff
        side = (second >> 224) & 1
        active = (second >> 240) & 1
        assert instrument == 1 and side == 0 and active == 1
        instrument_slot = mapped(instrument, 7, 1)
        instrument_word = int(storage[instrument_slot], 16)
        rate = (instrument_word >> 120) & ((1 << 64) - 1)
        assert 0 < rate < 10**18
        instrument_words[str(instrument)] = storage[instrument_slot]
        threshold = calculate(entry, leverage, side, rate)
        eligible = price <= threshold if side else price >= threshold
        assert eligible == (position_id in record["liquidated_ids"])
        positions.append({
            "position_id": position_id, "prestate_word0": storage[f"0x{base:064x}"],
            "prestate_word1": storage[f"0x{base + 1:064x}"],
            "instrument": instrument, "entry_price": entry, "leverage": leverage,
            "side": "long" if side else "short", "active": bool(active),
            "maintenance_rate_1e18": rate, "liquidation_threshold": threshold,
            "oracle_midpoint": price, "threshold_predicted_eligible": eligible,
            "historically_liquidated": position_id in record["liquidated_ids"],
        })
    assert price == 235155
    assert [row["liquidation_threshold"] for row in positions] == [235149, 235156, 235156]
    assert [row["threshold_predicted_eligible"] for row in positions] == [True, False, False]
    return {
        "pin_block": manifest["block"], "pin_hash": manifest["block_hash"],
        "historical_transaction": TX, "historical_block": record["block_number"],
        "historical_block_hash": receipt["blockHash"].lower(), "transaction_index": 8,
        "raw_evidence": {
            "prestate": "../../artifacts/exchange_batch_summary/partial_tx_prestate.json",
            "call_trace": "../../artifacts/exchange_batch_summary/partial_tx_calls.json",
            "receipt": "../../artifacts/exchange_batch_summary/partial_tx_receipt.json",
            "block_header": "../../artifacts/exchange_batch_summary/partial_tx_block.json",
        },
        "oracle_midpoint": price, "hypercore_bbo": {"bid": bid, "ask": ask},
        "instrument_word1": instrument_words, "positions": positions,
        "requested_count": len(IDS), "threshold_predicted_count": 1,
        "historical_liquidated_count": len(liquidations),
        "interpretation": "All three positions were active. The short liquidation threshold selects only the first ID at the observed midpoint.",
        "limits": [
            "One historical partial batch verifies this boundary, not every batch skip branch.",
            "The threshold formula was established separately from 26 pinned view outputs and four local price-boundary probes.",
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
    print("Partial batch:", result["requested_count"], "active,", result["threshold_predicted_count"],
          "eligible,", result["historical_liquidated_count"], "liquidated")


if __name__ == "__main__":
    main()
