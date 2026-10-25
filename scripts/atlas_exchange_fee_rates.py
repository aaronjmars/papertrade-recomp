#!/usr/bin/env python3
"""Verify Exchange fee-rate setter, getters, event, and bound at the pin."""

import argparse
import json
import os
import pathlib

from atlas_exchange_queue_layout import KECCAK, PROXY
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_fee_rates" / "pinned_probes.json"
BEHAVIOR = ATLAS / "exchange_fee_rates_behavior.json"
PIN = 48902346
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SETTER = "0xe538b280"
EVENT = "0xe4af0531d4ba8c578b5076b042e4505372fb4f4986aea8ebf77f4ff1585e3e75"
GETTERS = {23: "0xf1a8786c", 24: "0x48ee5e08", 25: "0x5fb3b1b5"}
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x1111111111111111111111111111111111111111"
FIRST_MAX = 5 * 10**17
CASES = {
    "owner_distinct": (OWNER, (10**16, 2 * 10**16, 3 * 10**16)),
    "owner_all_at_max": (OWNER, (FIRST_MAX, FIRST_MAX, FIRST_MAX)),
    "owner_zero": (OWNER, (0, 0, 0)),
    "outsider": (OUTSIDER, (10**16, 2 * 10**16, 3 * 10**16)),
    "owner_first_above_max": (OWNER, (FIRST_MAX + 1, 4, 5)),
    "owner_second_above_max": (OWNER, (1, FIRST_MAX + 1, 5)),
    "owner_third_above_max": (OWNER, (1, 4, FIRST_MAX + 1)),
}


def read(name):
    return json.loads((ATLAS / name).read_text())


def word(value):
    return f"0x{value:064x}"


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def all_logs(trace):
    return list(trace.get("logs", [])) + [row for child in trace.get("calls", []) for row in all_logs(child)]


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read("manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    base = {slot: rpc(url, "eth_getStorageAt", [PROXY, hex(slot), hex(PIN)]) for slot in GETTERS}
    getters = {slot: rpc(url, "eth_call", [{"to": PROXY, "data": selector}, hex(PIN)])
               for slot, selector in GETTERS.items()}
    probes = {}
    for name, (sender, args) in CASES.items():
        call = {"from": sender, "to": PROXY,
                "data": SETTER + "".join(word(arg)[2:] for arg in args), "gas": hex(10_000_000)}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                                             {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        row = {"sender": sender, "arguments": [str(value) for value in args],
               "calldata": call["data"], "error": trace.get("error"),
               "output": trace.get("output", ""), "logs": all_logs(trace)}
        if name in ("owner_distinct", "owner_all_at_max", "owner_zero"):
            diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                                                 {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            row["pre_storage"] = diff.get("pre", {}).get(PROXY, {}).get("storage", {})
            row["post_storage"] = diff.get("post", {}).get(PROXY, {}).get("storage", {})
            override = {PROXY: {"stateDiff": {word(slot): word(value)
                                                for slot, value in zip(GETTERS, args)}}}
            row["getter_after_override"] = {str(slot): rpc(url, "eth_call", [
                {"to": PROXY, "data": selector}, hex(PIN), override])
                for slot, selector in GETTERS.items()}
        probes[name] = row
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin": PIN, "block_hash": manifest["block_hash"],
                                    "proxy": PROXY, "base_storage": {str(k): v for k, v in base.items()},
                                    "base_getters": {str(k): v for k, v in getters.items()},
                                    "probes": probes}, indent=2) + "\n")


def verify():
    saved = json.loads(ARTIFACT.read_text())
    manifest = read("manifest.json")
    assert saved["pin"] == PIN and saved["block_hash"] == manifest["block_hash"] and saved["proxy"] == PROXY
    assert "0x" + KECCAK(b"setFeeRates(uint256,uint256,uint256)").hex()[:8] == SETTER
    assert "0x" + KECCAK(b"FeeRatesUpdated(uint256,uint256,uint256)").hex() == EVENT
    assert "0x" + KECCAK(b"liquidationFeeRate()").hex()[:8] == GETTERS[25]
    assert "0x" + KECCAK(b"NotOwner()").hex()[:8] == "0x30cd7471"
    assert "0x" + KECCAK(b"FeeTooHigh()").hex()[:8] == "0xcd4e6167"
    assert set(saved["probes"]) == set(CASES)
    assert {int(slot): int(value, 16) for slot, value in saved["base_storage"].items()} == {
        23: 2 * 10**16, 24: 2 * 10**16, 25: 2 * 10**16}
    for slot, selector in GETTERS.items():
        assert int(saved["base_getters"][str(slot)], 16) == int(saved["base_storage"][str(slot)], 16)
        view = next(row for row in read("storage_trace_catalog.json")[IMPLEMENTATION]["views"]
                    if row["selector"] == selector)
        assert view["direct_slots"] == [slot]
    successes = []
    reverts = {}
    for name, (sender, args) in CASES.items():
        row = saved["probes"][name]
        assert row["sender"] == sender and [int(value) for value in row["arguments"]] == list(args)
        assert row["calldata"] == SETTER + "".join(word(arg)[2:] for arg in args)
        if name in ("owner_distinct", "owner_all_at_max", "owner_zero"):
            assert not row["error"] and len(row["logs"]) == 1
            event = row["logs"][0]
            assert event["address"].lower() == PROXY and event["topics"] == [EVENT]
            assert words(event["data"]) == list(args)
            for slot, arg in zip(GETTERS, args):
                key = word(slot)
                base_value = int(saved["base_storage"][str(slot)], 16)
                if arg != base_value:
                    assert int(row["pre_storage"][key], 16) == base_value
                    assert int(row["post_storage"].get(key, "0x0"), 16) == arg
                else:
                    assert key not in row["pre_storage"] and key not in row["post_storage"]
                assert int(row["getter_after_override"][str(slot)], 16) == arg
            assert set(row["pre_storage"]) == {word(slot) for slot, arg in zip(GETTERS, args)
                                                   if arg != int(saved["base_storage"][str(slot)], 16)}
            successes.append(name)
        else:
            assert row["error"] and not row["logs"]
            reverts[name] = row["output"][:10]
    assert reverts == {"outsider": "0x30cd7471",
                       "owner_first_above_max": "0xcd4e6167",
                       "owner_second_above_max": "0xcd4e6167",
                       "owner_third_above_max": "0xcd4e6167"}
    liquidated = [position for batch in read("exchange_position_layout.json")["liquidation_accounting"]
                  for position in batch["positions"]]
    assert len(liquidated) == 6
    assert all(row["staker_fee"] + row["dev_fee"] ==
               row["margin"] * int(saved["base_storage"]["25"], 16) // 10**18
               for row in liquidated)
    result = {"pin": PIN, "block_hash": manifest["block_hash"], "exchange_proxy": PROXY,
              "implementation": IMPLEMENTATION, "setter_selector": SETTER, "event_topic0": EVENT,
              "raw_evidence": "../../artifacts/exchange_fee_rates/pinned_probes.json",
              "selector_reconstructions": {SETTER: "setFeeRates(uint256,uint256,uint256)",
                                           GETTERS[25]: "liquidationFeeRate()"},
              "event_catalog": [{"topic0": EVENT, "reconstructed_signature":
                                 "FeeRatesUpdated(uint256,uint256,uint256)", "status": "simulated_log_only"}],
              "simulated_error_catalog": [
                  {"selector": "0x30cd7471", "reconstructed_signature": "NotOwner()",
                   "probe_paths": ["outsider"]},
                  {"selector": "0xcd4e6167", "reconstructed_signature": "FeeTooHigh()",
                   "probe_paths": ["owner_first_above_max",
                   "owner_second_above_max", "owner_third_above_max"]}],
              "probe_count": len(CASES), "successes": successes, "revert_selectors": reverts,
              "historical_liquidation_fee_pairs_consistent": len(liquidated),
              "each_rate_max_inclusive": FIRST_MAX, "getter_slots": {selector: slot for slot, selector in GETTERS.items()},
              "limits": ["No saved historical transaction called this setter.",
                         "The exact names of the slot-23 and slot-24 getters and the economic meanings of all three rates remain unverified.",
                         "Simulation tests setter branches but does not prove future trades under changed rates."]}
    BEHAVIOR.write_text(json.dumps(result, indent=2) + "\n")
    print({"probes": len(CASES), "successes": successes, "reverts": reverts})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
