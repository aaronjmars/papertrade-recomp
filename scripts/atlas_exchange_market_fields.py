#!/usr/bin/env python3
"""Verify a keeper-updated Exchange mapping and its two five-word getters."""

import argparse
import concurrent.futures
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_tokenomics import EXCHANGE, PIN, rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_market_fields" / "pinned_probes.json"
TX = "0x324a3b9eb75351965b220c16095b56b053f91fbda37525202051604fbd618f7d"
SELECTOR = "0x628a9fd6"
EVENT = "0xa065d6ba54c5124cd73ce640fd3fbc0ce6eb8a4f4c9d5155347dcc461ad0cffe"
GETTERS = ("0xcb163b03", "0xf37d3c4f")
KEEPER_GETTER = "0x21f55a6c"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
KEEPER = "0x3721476de31190dc1af8908026abe20efe25cf99"
OUTSIDER = "0x1111111111111111111111111111111111111111"
ERRORS = {"unauthorized": "0x989c4c7c", "invalid_instrument": "0x67207a88"}


def word(value):
    return f"0x{value:064x}"


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[index:index + 64], 16) for index in range(2, len(data), 64)]


def call_data(selector, *arguments):
    return selector + "".join(f"{value:064x}" for value in arguments)


def mapping_slot(instrument):
    digest = Keccak()(instrument.to_bytes(32, "big") + (36).to_bytes(32, "big"))
    return int.from_bytes(digest, "big")


def all_logs(call):
    logs = list(call.get("logs", []))
    for child in call.get("calls", []):
        logs.extend(all_logs(child))
    return logs


def cases():
    return {"keeper_instrument_0": (KEEPER, 0, 123, 456),
            "owner_instrument_1": (OWNER, 1, 789, 1011),
            "outsider_instrument_0": (OUTSIDER, 0, 123, 456),
            "keeper_instrument_2": (KEEPER, 2, 123, 456),
            "keeper_max_uint128": (KEEPER, 0, 2**128 - 1, 2**128 - 1)}


def capture():
    if ARTIFACT.exists():
        return
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    count_word = rpc(url, "eth_getStorageAt", [EXCHANGE, hex(8), hex(PIN)])
    keeper_word = rpc(url, "eth_getStorageAt", [EXCHANGE, hex(37), hex(PIN)])
    keeper_output = rpc(url, "eth_call", [{"to": EXCHANGE, "data": KEEPER_GETTER}, hex(PIN)])
    markets = []
    for instrument in (0, 1, 2):
        base = mapping_slot(instrument)
        markets.append({"instrument": instrument, "base_slot": word(base),
                        "raw_words": [rpc(url, "eth_getStorageAt", [EXCHANGE, word(base + offset), hex(PIN)])
                                      for offset in (0, 1)],
                        "getter_outputs": {selector: rpc(url, "eth_call", [
                            {"to": EXCHANGE, "data": call_data(selector, instrument)}, hex(PIN)])
                            for selector in GETTERS}})
    probes = {}
    for name, (sender, instrument, first, second) in cases().items():
        call = {"from": sender, "to": EXCHANGE,
                "data": call_data(SELECTOR, instrument, first, second), "gas": "0x989680"}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                                              {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        row = {"sender": sender, "instrument": instrument, "values": [str(first), str(second)],
               "calldata": call["data"], "error": trace.get("error"),
               "output": trace.get("output", ""), "logs": all_logs(trace),
               "implementation_calls": [{"type": child["type"], "to": child["to"],
                                         "input": child["input"]} for child in trace.get("calls", [])]}
        if name in ("keeper_instrument_0", "owner_instrument_1"):
            diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                                                 {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            row["pre_storage"] = diff.get("pre", {}).get(EXCHANGE, {}).get("storage", {})
            row["post_storage"] = diff.get("post", {}).get(EXCHANGE, {}).get("storage", {})
        probes[name] = row
    ARTIFACT.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                    "instrument_count_slot_8": count_word,
                                    "keeper_slot_37": keeper_word,
                                    "keeper_getter_output": keeper_output,
                                    "markets": markets, "probes": probes}, indent=2) + "\n")


def capture_recent():
    saved = json.loads(ARTIFACT.read_text())
    if "recent_event_calls" in saved:
        return
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    logs = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    relevant = [log for log in logs if log["address"].lower() == EXCHANGE
                and log["topics"][0] == EVENT]
    transaction_hashes = sorted({log["transactionHash"] for log in relevant})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        transactions = dict(zip(transaction_hashes, pool.map(
            lambda tx: rpc(url, "eth_getTransactionByHash", [tx]), transaction_hashes)))
    saved["recent_event_calls"] = [
        {"tx": log["transactionHash"], "block_number": int(log["blockNumber"], 16),
         "log_index": int(log["logIndex"], 16), "topics": log["topics"],
         "data": log["data"], "root_from": transactions[log["transactionHash"]]["from"],
         "root_to": transactions[log["transactionHash"]]["to"],
         "root_input": transactions[log["transactionHash"]]["input"]}
        for log in relevant]
    ARTIFACT.write_text(json.dumps(saved, indent=2) + "\n")


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(ARTIFACT.read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert int(saved["instrument_count_slot_8"], 16) == 2
    assert int(saved["keeper_slot_37"], 16) == int(KEEPER, 16)
    assert int(saved["keeper_getter_output"], 16) == int(KEEPER, 16)
    links = json.loads((ATLAS / "state_links.json").read_text())
    assert any(row["from"].lower() == EXCHANGE and row["getter"] == "owner()"
               and row["to"].lower() == OWNER for row in links)
    assert any(row["from"].lower() == EXCHANGE and row["getter"] == "marketKeeper()"
               and row["to"].lower() == KEEPER for row in links)
    assert [row["instrument"] for row in saved["markets"]] == [0, 1, 2]
    for row in saved["markets"]:
        base = mapping_slot(row["instrument"])
        first, second = [int(value, 16) for value in row["raw_words"]]
        assert row["base_slot"] == word(base)
        low96 = first & (2**96 - 1)
        middle96 = first >> 96 & (2**96 - 1)
        high64 = first >> 192
        low128 = second & (2**128 - 1)
        high128 = second >> 128
        assert words(row["getter_outputs"][GETTERS[0]]) == [low96, middle96, low128, high128, high64]
        assert words(row["getter_outputs"][GETTERS[1]]) == [low96, middle96, high64, low128, high128]
        if row["instrument"] == 2:
            assert first == second == 0

    trace = json.loads((ROOT / "artifacts" / "historical" / f"{TX}.calls.json").read_text())
    diff = json.loads((ROOT / "artifacts" / "historical" / f"{TX}.state_diff.json").read_text())
    receipt = json.loads((ROOT / "artifacts" / "historical" / f"{TX}.receipt.json").read_text())
    assert trace["to"].lower() == EXCHANGE and trace["input"][:10] == SELECTOR
    historical_instrument, historical_first, historical_second = words("0x" + trace["input"][10:])
    assert historical_instrument == 0 and 0 <= historical_first < 2**128 and 0 <= historical_second < 2**128
    event = next(row for row in receipt["logs"] if row["address"].lower() == EXCHANGE
                 and row["topics"][0] == EVENT)
    assert len(event["topics"]) == 2 and int(event["topics"][1], 16) == historical_instrument
    assert words(event["data"]) == [historical_first, historical_second]
    slot = word(mapping_slot(historical_instrument) + 1)
    pre = int(diff["pre"][EXCHANGE]["storage"][slot], 16)
    post = int(diff["post"][EXCHANGE]["storage"][slot], 16)
    assert post == historical_first + (historical_second << 128) and pre != post
    recent = saved["recent_event_calls"]
    assert len(recent) == 29
    assert len({row["tx"] for row in recent}) == 29
    for row in recent:
        assert row["root_to"].lower() == EXCHANGE and row["root_input"][:10] == SELECTOR
        event_instrument = int(row["topics"][1], 16)
        first, second = words(row["data"])
        assert len(row["topics"]) == 2 and 0 <= event_instrument < 2
        assert row["root_input"] == call_data(SELECTOR, event_instrument, first, second)
        assert row["root_from"].lower() == KEEPER
    assert set(saved["probes"]) == set(cases())
    for name, row in saved["probes"].items():
        sender, instrument, first, second = cases()[name]
        assert row["sender"] == sender and row["instrument"] == instrument
        assert row["values"] == [str(first), str(second)]
        assert row["calldata"] == call_data(SELECTOR, instrument, first, second)
        assert row["implementation_calls"] == [{"type": "DELEGATECALL",
                                                "to": "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee",
                                                "input": row["calldata"]}]
        if name.startswith("outsider") or name == "keeper_instrument_2":
            assert row["error"] == "execution reverted" and row["logs"] == []
            assert row["output"] == (ERRORS["unauthorized"] if name.startswith("outsider")
                                     else ERRORS["invalid_instrument"])
        else:
            assert row["error"] is None and row["output"] == "" and len(row["logs"]) == 1
            log = row["logs"][0]
            assert log["address"].lower() == EXCHANGE and log["topics"][0] == EVENT
            assert len(log["topics"]) == 2 and int(log["topics"][1], 16) == instrument
            assert words(log["data"]) == [first, second]
            if "post_storage" in row:
                key = word(mapping_slot(instrument) + 1)
                assert row["pre_storage"] == {key: saved["markets"][instrument]["raw_words"][1]}
                assert row["post_storage"] == {key: word(first + (second << 128))}

    result = {"pin_block": PIN, "exchange_proxy": EXCHANGE,
              "implementation": "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee",
              "historical_transaction": TX, "historical_instrument": historical_instrument,
              "historical_values": [str(historical_first), str(historical_second)],
              "recent_event_call_count": len(recent),
              "setter_selector": SELECTOR, "getter_selectors": list(GETTERS),
              "event_topic0": EVENT, "event_layout": "indexed uint32 instrument; unindexed uint128 first, uint128 second",
              "event_catalog": [{"topic0": EVENT, "reconstructed_signature": None,
                                 "status": "observed_historical", "indexed_fields": ["instrument"],
                                 "data_fields": ["first", "second"]}],
              "storage_layout": {"instrument_count_slot": 8, "market_keeper_slot": 37,
                                 "mapping_base_slot": 36, "updated_word_offset": 1,
                                 "updated_word_packing": "first + (second << 128)"},
              "pinned_instrument_count": 2, "historical_post_word": word(post),
              "setter_probe_count": len(saved["probes"]), "getter_instruments_checked": [0, 1, 2],
              "revert_selectors": ERRORS,
              "simulated_error_catalog": [
                  {"selector": ERRORS["unauthorized"], "probe_paths": ["outsider_instrument_0"]},
                  {"selector": ERRORS["invalid_instrument"], "probe_paths": ["keeper_instrument_2"]}],
              "limits": ["The setter and getter names and economic meaning of the five mapping fields remain unknown.",
                         "The five setter cases are read-only pinned simulations; the historical transaction is separate observed execution.",
                         "The sampled bounds do not prove every possible input and role transition."]}
    (ATLAS / "exchange_market_fields_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange market fields: historical write, 3 getter keys, 5 setter probes verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-recent", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
        capture_recent()
    if args.capture_recent:
        capture_recent()
    verify()
