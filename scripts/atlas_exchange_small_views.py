#!/usr/bin/env python3
"""Verify six small Exchange views and the Tokenomics excess wrapper."""

import argparse
import json
import os
import pathlib
import subprocess

from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_small_views" / "pinned_calls.json"
BEHAVIOR = ATLAS / "exchange_small_views_behavior.json"
PIN = 48902346
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
EXCESS = "0x18715c9a"
TOKENOMICS_EXCESS = "0xae745703"
SLOT4_VIEW = "0xc43fbc8c"
CONSTANTS = {"0x6d60ae8e": 10**9, "0xaf210ecc": 25,
             "0xfdfd905d": 10**18, "0xff3bc415": 64}
SELECTORS = (EXCESS, *CONSTANTS, SLOT4_VIEW)
AUDIT_URL = "https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/"


def read(name):
    return json.loads((ATLAS / name).read_text())


def word(n):
    return f"0x{n:064x}"


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    block = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    manifest = read("manifest.json")
    assert block["hash"] == manifest["block_hash"]
    slots = {"exchange_4": rpc(url, "eth_getStorageAt", [EXCHANGE, word(4), hex(PIN)]),
             "tokenomics_3": rpc(url, "eth_getStorageAt", [TOKENOMICS, word(3), hex(PIN)]),
             "tokenomics_6": rpc(url, "eth_getStorageAt", [TOKENOMICS, word(6), hex(PIN)])}
    pinned = {}
    for selector in SELECTORS:
        call = {"to": EXCHANGE, "data": selector}
        pinned[selector] = {
            "output": rpc(url, "eth_call", [call, hex(PIN)]),
            "trace": rpc(url, "debug_traceCall", [call, hex(PIN), {"tracer": "callTracer"}]),
        }
    slot4_cases = []
    for value in (0x123405a, 0x1234000):
        output = rpc(url, "eth_call", [{"to": EXCHANGE, "data": SLOT4_VIEW}, hex(PIN),
                                       {EXCHANGE: {"stateDiff": {word(4): word(value)}}}])
        slot4_cases.append({"slot4": word(value), "output": output})
    excess_cases = []
    for tracked, cap in ((1000, 600), (1000, 1000), (600, 1000)):
        output = rpc(url, "eth_call", [{"to": EXCHANGE, "data": EXCESS}, hex(PIN),
                                       {TOKENOMICS: {"stateDiff": {word(3): word(tracked),
                                                                   word(6): word(cap)}}}])
        excess_cases.append({"tracked_lp": word(tracked), "reward_cap": word(cap),
                             "output": output})
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin": PIN, "block_hash": block["hash"],
                                    "exchange": EXCHANGE, "tokenomics": TOKENOMICS,
                                    "slots": slots, "pinned": pinned,
                                    "slot4_cases": slot4_cases, "excess_cases": excess_cases}, indent=2) + "\n")


def verify():
    raw = json.loads(ARTIFACT.read_text())
    assert raw["pin"] == PIN and raw["block_hash"] == read("manifest.json")["block_hash"]
    assert raw["exchange"] == EXCHANGE and raw["tokenomics"] == TOKENOMICS
    assert set(raw["pinned"]) == set(SELECTORS)
    slots = {key: int(value, 16) for key, value in raw["slots"].items()}
    assert int(raw["pinned"][EXCESS]["output"], 16) == max(slots["tokenomics_3"] - slots["tokenomics_6"], 0)
    assert int(raw["pinned"][SLOT4_VIEW]["output"], 16) == slots["exchange_4"] & 0xff
    for selector, expected in CONSTANTS.items():
        entry = raw["pinned"][selector]
        assert int(entry["output"], 16) == expected
        assert not entry["trace"].get("error")
        assert not [node for node in descendants(entry["trace"])
                    if node.get("type") == "STATICCALL"]
    for row in raw["slot4_cases"]:
        assert int(row["output"], 16) == int(row["slot4"], 16) & 0xff
    assert len(raw["slot4_cases"]) == 2
    for row in raw["excess_cases"]:
        expected = max(int(row["tracked_lp"], 16) - int(row["reward_cap"], 16), 0)
        assert int(row["output"], 16) == expected
    assert len(raw["excess_cases"]) == 3
    trace = raw["pinned"][EXCESS]["trace"]
    calls = [node for node in descendants(trace)
             if node.get("to", "").lower() == TOKENOMICS]
    assert len(calls) == 1 and calls[0]["type"] == "STATICCALL"
    assert calls[0]["input"] == TOKENOMICS_EXCESS
    assert calls[0]["output"] == raw["pinned"][EXCESS]["output"]
    assert subprocess.run(["cast", "sig", "stakerLpExcessToDistribute()"], check=True,
                          capture_output=True, text=True).stdout.strip() == EXCESS
    storage = read("storage_trace_catalog.json")[IMPLEMENTATION]["views"]
    by_selector = {row["selector"]: row for row in storage}
    assert by_selector[SLOT4_VIEW]["direct_slots"] == [4]
    assert by_selector[EXCESS]["direct_slots"] == [3, 6]
    assert all(by_selector[selector]["direct_slots"] == [] for selector in CONSTANTS)
    behavior = {"pin": PIN, "block_hash": raw["block_hash"], "exchange_proxy": EXCHANGE,
                "implementation": IMPLEMENTATION,
                "raw_evidence": "../../artifacts/exchange_small_views/pinned_calls.json",
                "selector_reconstructions": {EXCESS: "stakerLpExcessToDistribute()"},
                "source_name_evidence": AUDIT_URL,
                "excess_formula": "max(Tokenomics.slot3 - Tokenomics.slot6, 0)",
                "excess_nested_selector": TOKENOMICS_EXCESS,
                "slot4_formula": "Exchange.slot4 & 0xff",
                "constant_outputs": {selector: str(value) for selector, value in CONSTANTS.items()},
                "pinned_outputs": {selector: row["output"] for selector, row in raw["pinned"].items()},
                "override_case_count": len(raw["slot4_cases"]) + len(raw["excess_cases"]),
                "limits": ["The audited source commit is not matched to the pinned runtime; the excess wrapper name is supported by its hash, report context, and live call path.",
                           "The four literal getters and slot-4 getter have verified outputs but unresolved source names and economic labels."]}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified six pinned Exchange views and five storage override calls")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
