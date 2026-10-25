#!/usr/bin/env python3
"""Verify full-history absence of four Exchange control success events."""

import argparse
import datetime
import json
import pathlib

from atlas_public_name_gaps import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_control_history" / "event_queries.json"
BEHAVIOR = ATLAS / "exchange_control_event_history_behavior.json"
PIN = 48902346
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
QUERIES = {
    "trading_paused_updated": ("0xae69b95b", "0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e"),
    "market_paused": ("0x2d2451d1", "0x25e933a27e6487478d7617f2f4ef2f5c77355faf6cad2e6fd7c4b8d029930d9f"),
    "fee_rates_updated": ("0xe538b280", "0xe4af0531d4ba8c578b5076b042e4505372fb4f4986aea8ebf77f4ff1585e3e75"),
    "instrument_limit_updated": ("0xd7c7e5fb", "0x62db1b2b923b6f20043c492d3586df1a823e447c63e44d15dbc90c1a3bc9fcc5"),
}


def read(name):
    return json.loads((ATLAS / name).read_text())


def capture():
    block_hash = rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"]
    assert block_hash == read("manifest.json")["block_hash"]
    rows = []
    for name, (_, topic) in QUERIES.items():
        params = [{"fromBlock": "0x0", "toBlock": hex(PIN),
                   "address": EXCHANGE, "topics": [topic]}]
        logs = rpc("eth_getLogs", params)
        assert all(row["address"].lower() == EXCHANGE and row["topics"][0].lower() == topic
                   for row in logs)
        rows.append({"name": name, "method": "eth_getLogs", "params": params, "result": logs})
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "queried_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pin": PIN, "block_hash": block_hash, "queries": rows}, indent=2) + "\n")


def verify():
    saved = json.loads(ARTIFACT.read_text())
    assert saved["pin"] == PIN and saved["block_hash"] == read("manifest.json")["block_hash"]
    assert len(saved["queries"]) == len(QUERIES)
    pause = read("exchange_pause_behavior.json")
    fee = read("exchange_fee_rates_behavior.json")
    limit = read("exchange_instrument_limit_behavior.json")
    assert QUERIES["trading_paused_updated"][1] == pause["event_catalog"][1]["topic0"]
    assert QUERIES["market_paused"][1] == pause["event_catalog"][2]["topic0"]
    assert QUERIES["fee_rates_updated"][1] == fee["event_catalog"][0]["topic0"]
    assert QUERIES["instrument_limit_updated"][1] == limit["event_topic"]
    results = []
    for row, (name, (selector, topic)) in zip(saved["queries"], QUERIES.items()):
        assert row["name"] == name and row["method"] == "eth_getLogs"
        assert row["params"] == [{"fromBlock": "0x0", "toBlock": hex(PIN),
                                  "address": EXCHANGE, "topics": [topic]}]
        assert row["result"] == []
        results.append({"selector": selector, "event_topic0": topic,
                        "successful_event_log_count": 0})
    result = {"pin": PIN, "block_hash": saved["block_hash"], "exchange_proxy": EXCHANGE,
              "raw_query": "../../artifacts/exchange_control_history/event_queries.json",
              "full_history_zero_event_paths": results,
              "limit": "No returned success event does not prove the selector was never called, reverted, or changed state without emitting this topic."}
    BEHAVIOR.write_text(json.dumps(result, indent=2) + "\n")
    print(len(results), "Exchange control success topics have zero returned logs through the pin")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
