#!/usr/bin/env python3
"""Verify four unnamed Exchange unit-scaling views with archive calls."""

import argparse
import json
import os
import pathlib

from atlas_exchange_queue_layout import PROXY
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_unit_scales" / "pinned_calls.json"
BEHAVIOR = ATLAS / "exchange_unit_scales_behavior.json"
PIN = 48902346
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SELECTORS = {
    "slot5": "0x31a39849",
    "multiply_slot5": "0x70f75ff5",
    "ratio_slot3_slot5": "0x2dcc7fce",
    "multiply_slot3": "0xbacd9ea0",
    "collateral_scale": "0xec0bdcfc",
}
HISTORICAL_RAW = 199000000
INPUTS = [0, 1, 2, 5, 11, HISTORICAL_RAW]


def read(name):
    return json.loads((ATLAS / name).read_text())


def word(value):
    return "0x" + value.to_bytes(32, "big").hex()


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read("manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    base = {i: int(rpc(url, "eth_getStorageAt", [PROXY, hex(i), hex(PIN)]), 16) for i in (3, 5)}
    cases = []
    for label, slots in (("pinned", base), ("override", {3: 7, 5: 3})):
        override = {} if label == "pinned" else {PROXY: {"stateDiff": {word(k): word(v) for k, v in slots.items()}}}
        for name, selector in SELECTORS.items():
            for amount in ([None] if name in ("slot5", "collateral_scale") else INPUTS):
                data = selector + ("" if amount is None else word(amount)[2:])
                params = [{"to": PROXY, "data": data}, hex(PIN)]
                if override:
                    params.append(override)
                output = rpc(url, "eth_call", params)
                cases.append({"state": label, "slots": {str(k): word(v) for k, v in slots.items()},
                              "name": name, "selector": selector, "input": amount, "output": output})
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin": PIN, "block_hash": manifest["block_hash"],
                                    "proxy": PROXY, "base_slots": {str(k): word(v) for k, v in base.items()},
                                    "cases": cases}, indent=2) + "\n")


def verify():
    raw = json.loads(ARTIFACT.read_text())
    manifest = read("manifest.json")
    assert raw["pin"] == PIN and raw["block_hash"] == manifest["block_hash"] and raw["proxy"] == PROXY
    assert len(raw["cases"]) == 40
    base = {int(k): int(v, 16) for k, v in raw["base_slots"].items()}
    assert base == {3: 10**12, 5: 10**10}
    observed = {}
    for row in raw["cases"]:
        slots = {int(k): int(v, 16) for k, v in row["slots"].items()}
        assert slots == (base if row["state"] == "pinned" else {3: 7, 5: 3})
        name, amount = row["name"], row["input"]
        assert row["selector"] == SELECTORS[name]
        if name == "slot5":
            expected = slots[5]
        elif name == "collateral_scale":
            expected = slots[3]
        elif name == "multiply_slot5":
            expected = amount * slots[5]
        elif name == "multiply_slot3":
            expected = amount * slots[3]
        else:
            expected = amount * slots[3] // slots[5]
        assert int(row["output"], 16) == expected, row
        observed[(row["state"], name, amount)] = expected
    withdrawal = read("exchange_core_withdrawal_behavior.json")["transactions"][0]
    assert int(withdrawal["signed_raw_amount"]) == HISTORICAL_RAW
    assert observed[("pinned", "ratio_slot3_slot5", HISTORICAL_RAW)] == int(withdrawal["event_core_amount"])
    assert observed[("pinned", "multiply_slot3", HISTORICAL_RAW)] == int(withdrawal["event_core_amount"]) * 10000000000
    traces = read("storage_trace_catalog.json")[IMPLEMENTATION]["views"]
    by_selector = {row["selector"]: row for row in traces}
    for name, slots in (("slot5", {5}), ("multiply_slot5", {5}),
                        ("ratio_slot3_slot5", {3, 5}), ("multiply_slot3", {3}),
                        ("collateral_scale", {3})):
        assert set(by_selector[SELECTORS[name]]["direct_slots"]) == slots
    result = {"pin": PIN, "block_hash": manifest["block_hash"], "exchange_proxy": PROXY,
              "implementation": IMPLEMENTATION, "raw_evidence": "../../artifacts/exchange_unit_scales/pinned_calls.json",
              "selectors": SELECTORS, "call_count": len(raw["cases"]), "matched_count": len(raw["cases"]),
              "pinned_slot3": base[3], "pinned_slot5": base[5],
              "formulas": {"multiply_slot3": "input * slot3", "multiply_slot5": "input * slot5",
                           "ratio_slot3_slot5": "floor(input * slot3 / slot5)"},
              "withdrawal_raw_amount_checked": HISTORICAL_RAW,
              "withdrawal_core_amount_checked": int(withdrawal["event_core_amount"]),
              "limits": ["The four selector names remain unknown; only collateralScale() has a verified name.",
                         "Captured base and one synthetic scaling state at one pinned block.",
                         "Overflow and zero-divisor behavior were not tested."],
              "cases": raw["cases"]}
    BEHAVIOR.write_text(json.dumps(result, indent=2) + "\n")
    print({"calls": len(raw["cases"]), "slot3": base[3], "slot5": base[5],
           "withdrawal_core_amount": result["withdrawal_core_amount_checked"]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
