#!/usr/bin/env python3
"""Verify the saved Exchange instrument registration path offline."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
OUT = ATLAS / "exchange_instrument_creation_behavior.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
TX = "0xab0322e685e608455d03f0f3a4eeabafee85785f0bcaf0a91ef7d8ae6728c115"
SECOND_TX = "0xa527dea1cef73784e42ba989c8763f103fce30432b25c423921cb8f04d3d71c5"
SELECTOR = "0xc88bbcf3"
EVENT = "0x443c80f61da46228681c9b23ea9ae79b1a6f01ccf004b523675849bdfac11e20"
COUNT_SLOT = "0x" + f"{8:064x}"


def read(name):
    return json.loads((ATLAS / name).read_text())


def historical(suffix, tx=TX):
    return json.loads((HISTORICAL / f"{tx}.{suffix}.json").read_text())


def cast(*args):
    return subprocess.run(["cast", *args], capture_output=True, text=True, check=True).stdout.strip()


def slot_at(base, offset=0, key=0):
    return "0x" + f"{int(cast('index', 'uint32', str(key), str(base)), 16) + offset:064x}"


def main():
    manifest = read("manifest.json")
    runtime_row = manifest["contracts"][IMPLEMENTATION]
    runtime = bytes.fromhex((ATLAS / runtime_row["runtime_file"]).read_text().strip().removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == runtime_row["sha256"]
    assert cast("keccak", "InstrumentAdded(uint32,uint32)") == EVENT
    assert cast("sig", "instrumentCount()") == "0xf28bbdb2"

    summary, call, receipt, diff = (historical(x) for x in ("summary", "calls", "receipt", "state_diff"))
    assert summary["block"] == 47855385 and summary["status"] == 1
    assert call["to"].lower() == EXCHANGE and call["input"][:10] == SELECTOR
    assert len(call["input"]) == 10 + 9 * 64
    args = [int(call["input"][10 + i * 64:10 + (i + 1) * 64], 16) for i in range(9)]
    assert args == [15000000000000000000000, 814598000000000000000, 0, 1000,
                    10000000000000000000000000, 476041580087574, 100000000000000000,
                    100000000000000000000000, 10]
    assert len(call.get("calls", [])) == 1 and call["calls"][0]["to"].lower() == IMPLEMENTATION
    assert int(call["calls"][0]["output"], 16) == 0

    assert len(receipt["logs"]) == 1
    log = receipt["logs"][0]
    assert log["address"].lower() == EXCHANGE and log["topics"] == [EVENT, "0x" + "0" * 64]
    assert int(log["data"], 16) == 0
    post = diff["post"][EXCHANGE]["storage"]
    instrument_base = slot_at(7)
    market_base = slot_at(36)
    instrument_words = [int(post[slot_at(7, i)], 16) for i in range(3)]
    market_words = [int(post[slot_at(36, i)], 16) for i in range(2)]
    assert int(post[COUNT_SLOT], 16) & 0xffffffff == 1
    assert COUNT_SLOT not in diff["pre"].get(EXCHANGE, {}).get("storage", {})
    assert instrument_words == [args[0] | args[1] << 96 | args[2] << 192 | args[3] << 224,
                                args[4] | args[5] << 120 | args[6] << 184,
                                args[7]]
    assert market_words == [args[8] << 192, 2**256 - 1]

    storage = read("storage_trace_catalog.json")[IMPLEMENTATION]["views"]
    count_getter = next(row for row in storage if row["selector"] == "0xf28bbdb2")
    instrument_getter = next(row for row in storage if row["selector"] == "0xdc8a47ef")
    assert count_getter["direct_slots"] == [8] and int(count_getter["return_prefix"], 16) == 2
    assert [(row["base_slot"], row["field_offset"]) for row in instrument_getter["mapping_matches"]] == [(7, 0), (7, 1), (7, 2)]
    txlist = json.loads((ROOT / "artifacts" / "deployer_txlist.json").read_text())
    second = next(row for row in txlist if row["hash"] == SECOND_TX)
    assert second["blockNumber"] == "47855387" and second["txreceipt_status"] == "1"
    assert second["to"].lower() == EXCHANGE and second["input"][:10] == SELECTOR
    second_args = [int(second["input"][10 + i * 64:10 + (i + 1) * 64], 16) for i in range(9)]
    assert len(second["input"]) == 10 + 9 * 64 and second_args[2] == 1
    second_summary, second_call, second_receipt, second_diff = (
        historical(suffix, SECOND_TX) for suffix in ("summary", "calls", "receipt", "state_diff")
    )
    assert second_summary["block"] == 47855387 and second_summary["status"] == 1
    assert second_call["to"].lower() == EXCHANGE and second_call["input"].lower() == second["input"].lower()
    assert second_call["from"].lower() == second["from"].lower()
    assert len(second_call.get("calls", [])) == 1 and second_call["calls"][0]["to"].lower() == IMPLEMENTATION
    assert int(second_call["output"], 16) == int(second_call["calls"][0]["output"], 16) == 1
    assert second_receipt["transactionHash"].lower() == SECOND_TX and second_receipt["status"] == "0x1"
    assert len(second_receipt["logs"]) == 1
    second_log = second_receipt["logs"][0]
    assert second_log["address"].lower() == EXCHANGE and second_log["topics"] == [EVENT, "0x" + f"{1:064x}"]
    assert int(second_log["data"], 16) == 1
    second_post = second_diff["post"][EXCHANGE]["storage"]
    second_pre = second_diff["pre"][EXCHANGE]["storage"]
    second_instrument_base = slot_at(7, key=1)
    second_market_base = slot_at(36, key=1)
    second_instrument_words = [int(second_post[slot_at(7, i, 1)], 16) for i in range(3)]
    second_market_words = [int(second_post[slot_at(36, i, 1)], 16) for i in range(2)]
    assert int(second_pre[COUNT_SLOT], 16) & 0xffffffff == 1
    assert int(second_post[COUNT_SLOT], 16) & 0xffffffff == 2
    assert second_instrument_words == [
        second_args[0] | second_args[1] << 96 | second_args[2] << 192 | second_args[3] << 224,
        second_args[4] | second_args[5] << 120 | second_args[6] << 184,
        second_args[7]]
    assert second_market_words == [second_args[8] << 192, 2**256 - 1]
    pinned_instruments = json.loads((ROOT / "artifacts" / "exchange_instrument_admin" / "pinned_probes.json").read_text())["instruments"]
    assert [int(word, 16) for word in pinned_instruments[0]["words"]] == instrument_words
    assert [int(word, 16) for word in pinned_instruments[1]["words"]] == second_instrument_words
    pinned_markets = json.loads((ROOT / "artifacts" / "exchange_market_fields" / "pinned_probes.json").read_text())["markets"]
    assert int(pinned_markets[0]["raw_words"][0], 16) >> 192 == args[8]
    assert int(pinned_markets[1]["raw_words"][0], 16) >> 192 == second_args[8]
    assert runtime.find(bytes.fromhex("63c88bbcf3146114ee57")) >= 0
    assert runtime[0x14ee] == 0x5b
    assert bytes.fromhex("61152a614a5356") in runtime[0x14ee:0x1540]

    local_replay = json.loads((ROOT / "artifacts" / "exchange_instrument_creation_local" / "replay.json").read_text())
    assert local_replay["test_count"] == 8 and local_replay["word7_observed_width_bits"] == 128
    assert local_replay["owner_guard_order"].startswith("words 0 through 7:")

    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION,
        "selector": SELECTOR, "source_name_status": "unresolved",
        "selector_reconstructions": {"0xf28bbdb2": "instrumentCount()"},
        "behavior_label": "register instrument",
        "historical_tx": TX, "historical_block": summary["block"],
        "historical_caller": call["from"], "input_words": [str(x) for x in args],
        "second_registration_tx": SECOND_TX, "second_registration_block": 47855387,
        "second_input_words": [str(x) for x in second_args],
        "second_evidence": "saved receipt, call trace, and state diff match deployer transaction list and pinned instrument words",
        "second_returned_instrument_id": 1,
        "second_instrument_mapping_entry_slot": second_instrument_base,
        "second_instrument_storage_words": [hex(x) for x in second_instrument_words],
        "second_market_fields_entry_slot": second_market_base,
        "second_market_fields_storage_words": [hex(x) for x in second_market_words],
        "second_event_indexed_id": 1, "second_event_data_value": 1,
        "historical_registration_count": 2,
        "local_replay": "../../artifacts/exchange_instrument_creation_local/replay.json",
        "word7_observed_width_bits": local_replay["word7_observed_width_bits"],
        "sampled_owner_guard_order": local_replay["owner_guard_order"],
        "second_trace_artifacts": {suffix: f"../../artifacts/historical/{SECOND_TX}.{suffix}.json"
                                   for suffix in ("summary", "calls", "receipt", "state_diff")},
        "returned_instrument_id": 0,
        "instrument_mapping_base_slot": 7, "instrument_mapping_entry_slot": instrument_base,
        "instrument_storage_words": [hex(x) for x in instrument_words],
        "market_fields_mapping_base_slot": 36, "market_fields_entry_slot": market_base,
        "market_fields_storage_words": [hex(x) for x in market_words],
        "count_slot": 8, "count_after": 1, "pinned_count": 2,
        "event_catalog": [{"topic0": EVENT, "reconstructed_signature": "InstrumentAdded(uint32,uint32)",
                           "status": "observed_historical_topic", "indexed_arguments": ["uint32 instrumentId"],
                           "observed_indexed_value": 0, "observed_data_value": 0,
                           "second_observed_indexed_value": 1, "second_observed_data_value": 1,
                           "local_divergent_case": "id 0 with input word 2 equal to 7 emits indexed 0 and unindexed 7"}],
        "simulated_error_catalog": [
            {"selector": "0x30cd7471", "probe_paths": ["registration_outsider"]},
            {"selector": "0xb0cb274d", "probe_paths": ["zero_input_words_0_3_4_7"]},
            {"selector": "0x924d25e6", "probe_paths": ["zero_input_word_8"]},
        ],
        "runtime_sha256": runtime_row["sha256"], "dispatcher_entry_pc": 0x14ee,
        "owner_check_pc": 0x4a53,
        "observed_success_formula": {
            "instrument_word0": "arg0 | arg1 << 96 | arg2 << 192 | arg3 << 224",
            "instrument_word1": "arg4 | arg5 << 120 | arg6 << 184",
            "instrument_word2": "arg7",
            "market_word0": "arg8 << 192", "market_word1": "2^256 - 1"},
        "limits": ["The two historical registrations have saved full call traces, receipts, and state diffs; no later successful registration was found in the deployer list through the pin.",
                   "The exact source function name, field meanings, return-type declaration, and untested rejection boundaries remain unresolved.",
                   "Owner and sampled input-boundary rejections come from exact pinned-runtime local replay, not historical transactions."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified Exchange instrument registration write path")


if __name__ == "__main__":
    main()
