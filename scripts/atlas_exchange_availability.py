#!/usr/bin/env python3
"""Verify Exchange LP and queue availability against pinned storage overrides."""

import argparse
import json
import os
import pathlib

from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_availability" / "pinned_overrides.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN = 48902346
LOW = (1 << 128) - 1
SELECTORS = {"queue": "0x138e9de2", "lp": "0x0cdd5fc4"}


def word(value):
    return "0x" + value.to_bytes(32, "big").hex()


def fields(slots):
    return {"treasury": slots[14], "queued": slots[18],
            "balances": slots[22] & LOW, "locked": slots[22] >> 128,
            "staker_fee": slots[26] & LOW, "dev_fee": slots[26] >> 128}


def cases(base):
    f = fields(base)
    reserve = f["balances"] + f["locked"] + f["staker_fee"] + f["dev_fee"]
    available = max(f["treasury"] - reserve, 0)
    delta = 100 * 10**18
    assert available > delta and f["queued"] == 0
    return {
        "baseline": {},
        "queue_one": {18: 1},
        "queue_hundred": {18: delta},
        "queue_above_available": {18: available + 1},
        "treasury_zero": {14: 0},
        "treasury_exact_reserve": {14: reserve},
        "treasury_one_above_reserve": {14: reserve + 1},
        "balances_plus_hundred": {22: (f["locked"] << 128) | (f["balances"] + delta)},
        "locked_plus_hundred": {22: ((f["locked"] + delta) << 128) | f["balances"]},
        "staker_fee_plus_hundred": {26: (f["dev_fee"] << 128) | (f["staker_fee"] + delta)},
        "dev_fee_plus_hundred": {26: ((f["dev_fee"] + delta) << 128) | f["staker_fee"]},
    }


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    base = {i: int(rpc(url, "eth_getStorageAt", [PROXY, hex(i), hex(PIN)]), 16)
            for i in (14, 18, 22, 26)}
    saved = json.loads((ATLAS / "exchange_storage_words.json").read_text())
    assert all(base[i] == int(saved["slots"][str(i)], 16) for i in base)
    records = {}
    for name, changes in cases(base).items():
        override = {PROXY: {"stateDiff": {word(i): word(value)
                                            for i, value in changes.items()}}}
        results = {}
        for label, selector in SELECTORS.items():
            call = [{"to": PROXY, "data": selector}, hex(PIN)]
            if changes:
                call.append(override)
            results[label] = rpc(url, "eth_call", call)
        records[name] = {"changes": {str(i): word(value) for i, value in changes.items()},
                         "results": results}
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                    "proxy": PROXY, "base_slots": {str(i): word(value)
                                                                    for i, value in base.items()},
                                    "cases": records}, indent=2) + "\n")


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(ARTIFACT.read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert saved["proxy"] == PROXY
    base = {int(i): int(value, 16) for i, value in saved["base_slots"].items()}
    assert set(base) == {14, 18, 22, 26}
    assert set(saved["cases"]) == set(cases(base))
    traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]["views"]
    views = {row["selector"]: row for row in traces}
    assert set(views[SELECTORS["queue"]]["direct_slots"]) == {14, 22, 26}
    assert set(views[SELECTORS["lp"]]["direct_slots"]) == {14, 18, 22, 26}
    for name, row in saved["cases"].items():
        changes = {int(i): int(value, 16) for i, value in row["changes"].items()}
        assert changes == cases(base)[name]
        state = fields(base | changes)
        reserve = sum(state[key] for key in ("balances", "locked", "staker_fee", "dev_fee"))
        queue_available = max(state["treasury"] - reserve, 0)
        lp_available = 0 if state["queued"] > 0 else queue_available
        assert int(row["results"]["queue"], 16) == queue_available, name
        assert int(row["results"]["lp"], 16) == lp_available, name
    assert int(saved["cases"]["queue_one"]["results"]["queue"], 16) > 0
    assert int(saved["cases"]["queue_one"]["results"]["lp"], 16) == 0
    result = {"pin_block": PIN, "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
              "case_count": len(saved["cases"]), "call_count": 2 * len(saved["cases"]),
              "queue_formula": "max(treasury - balances - locked - staker_fee - dev_fee, 0)",
              "lp_formula": "0 if totalQueued > 0 else queueHarvestAvailable()",
              "evidence": "../../artifacts/exchange_availability/pinned_overrides.json",
              "limitations": ["The formulas match 11 pinned states with overrides, not every reachable state.",
                              "No transaction was sent; storage changes are read-only simulations."]}
    (ATLAS / "exchange_availability_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange availability:", len(saved["cases"]), "states,", 2 * len(saved["cases"]), "pinned calls")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
