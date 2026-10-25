#!/usr/bin/env python3
"""Verify seven live Tokenomics getter names against pinned proxy storage."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "tokenomics_getters"
SAVED = ARTIFACTS / "pinned_getters.json"
OUT = ATLAS / "tokenomics_direct_getters_behavior.json"
PROXY = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
IMPLEMENTATION = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
PIN = 48902346
KECCAK = Keccak()
LOW160 = (1 << 160) - 1
GETTERS = {
    "0x1c3972ba": ("flatRate()", 7, "uint256"),
    "0x8cf554a7": ("trackedLpUsd()", 3, "int256_word"),
    "0x8da5cb5b": ("owner()", 0, "address_shift16"),
    "0xcbb451da": ("tailDecayScaleUsd()", 8, "uint256"),
    "0xd2f7265a": ("exchange()", 1, "address"),
    "0xdc5682d2": ("tailProgressUsd()", 4, "uint256"),
    "0xe9ed73e9": ("lpFlatThresholdUsd()", 5, "uint256"),
}
ALIAS = "0x3886cade"


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    slots = sorted({slot for _, slot, _ in GETTERS.values()})
    words = {str(slot): rpc(url, "eth_getStorageAt", [PROXY, hex(slot), hex(PIN)]) for slot in slots}
    outputs = {selector: rpc(url, "eth_call", [{"to": PROXY, "data": selector}, hex(PIN)])
               for selector in (*GETTERS, ALIAS)}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin_block": PIN, "block_hash": header["hash"],
                                 "storage_words": words, "getter_outputs": outputs}, indent=2) + "\n")


def decoded(word, kind):
    if kind == "address":
        return word & LOW160
    if kind == "address_shift16":
        return (word >> 16) & LOW160
    return word


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert saved["pin_block"] == manifest["block"] == PIN
    assert saved["block_hash"].lower() == manifest["block_hash"]
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[IMPLEMENTATION]
    runtime_selectors = {row["selector"] for row in catalog["functions"]}
    traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]
    assert traces["target"] == PROXY
    views = {row["selector"]: row for row in traces["views"]}
    initial = json.loads((ATLAS / "tokenomics_initializer_behavior.json").read_text())
    assert initial["fresh_state"]["owner_bits"] == [16, 175]
    params = json.loads((ATLAS / "tokenomics_params_behavior.json").read_text())
    assert params["argument_storage_slots"] == [5, 6, 7, 8]
    alias = json.loads((ATLAS / "tokenomics_getter_alias_behavior.json").read_text())
    assert alias["selector_behaviors"][ALIAS]["direct_slot"] == 5
    rows = []
    names = {}
    for selector, (name, slot, kind) in GETTERS.items():
        assert selector in runtime_selectors
        assert "0x" + KECCAK(name.encode()).hex()[:8] == selector
        assert views[selector]["direct_slots"] == [slot] and not views[selector]["failed"]
        raw = int(saved["storage_words"][str(slot)], 16)
        output = int(saved["getter_outputs"][selector], 16)
        assert output == decoded(raw, kind), (selector, output, raw)
        names[selector] = name
        rows.append({"selector": selector, "signature": name, "storage_slot": slot,
                     "field": kind, "raw_word": saved["storage_words"][str(slot)],
                     "getter_output": saved["getter_outputs"][selector]})
    assert views[ALIAS]["direct_slots"] == [5]
    assert int(saved["getter_outputs"][ALIAS], 16) == int(saved["storage_words"]["5"], 16)
    assert saved["getter_outputs"][ALIAS] == saved["getter_outputs"]["0xe9ed73e9"]
    assert saved["storage_words"]["5"] == alias["pinned_slot_values"]["5"]
    assert int(saved["storage_words"]["0"], 16) & 1 == 1
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "tokenomics_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": names, "direct_getter_checks": rows,
            "unnamed_slot5_alias": ALIAS,
            "limits": ["The slot-5 alias and slot-6 direct getter remain unnamed.",
                       "The source-language integer widths and future values are not established by one pinned state."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Tokenomics getters: {len(result['selector_reconstructions'])} hash-checked names")
