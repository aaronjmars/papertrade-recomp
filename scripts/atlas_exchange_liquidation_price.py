#!/usr/bin/env python3
"""Capture and verify the unnamed Exchange liquidation-price view at the pin."""

import argparse
import json
import os
import pathlib

from atlas_exchange_queue_layout import PROXY, mapped
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_liquidation" / "pinned_price_getter.json"
BEHAVIOR = ATLAS / "exchange_liquidation_price_behavior.json"
PIN = 48902346
SELECTOR = "0x50c23fab"
RATE_MASK = (1 << 64) - 1


def read(name):
    return json.loads((ATLAS / name).read_text())


def calculate(entry, leverage, side, rate):
    assert leverage > 0 and side in (0, 1)
    base = entry - entry // leverage if side else entry + entry // leverage
    adjustment = base * rate // 10**18
    return base + adjustment if side else base - adjustment


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read("manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    recorded = read("exchange_position_layout.json")["records"]
    ids = [1] + sorted({row["position_id"] for row in recorded})
    rows = []
    instrument_words = {}
    for position_id in ids:
        word0 = rpc(url, "eth_getStorageAt", [PROXY, mapped(position_id, 10), hex(PIN)])
        word1 = rpc(url, "eth_getStorageAt", [PROXY, mapped(position_id, 10, 1), hex(PIN)])
        instrument = (int(word0, 16) >> 160) & 0xffffffff
        if instrument not in instrument_words:
            instrument_words[instrument] = rpc(url, "eth_getStorageAt", [PROXY, mapped(instrument, 7, 1), hex(PIN)])
        output = rpc(url, "eth_call", [{"to": PROXY, "data": SELECTOR + position_id.to_bytes(32, "big").hex()}, hex(PIN)])
        rows.append({"position_id": position_id, "word0": word0, "word1": word1,
                     "instrument": instrument, "instrument_word1": instrument_words[instrument],
                     "getter_output": output})
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin": PIN, "block_hash": manifest["block_hash"],
                                    "proxy": PROXY, "selector": SELECTOR, "rows": rows}, indent=2) + "\n")


def verify():
    raw = json.loads(ARTIFACT.read_text())
    manifest = read("manifest.json")
    assert raw["pin"] == PIN and raw["block_hash"] == manifest["block_hash"]
    assert raw["proxy"] == PROXY and raw["selector"] == SELECTOR
    recorded = {row["position_id"]: row["decoded"] for row in read("exchange_position_layout.json")["records"]}
    assert len(raw["rows"]) == len(recorded) + 1
    assert {row["position_id"] for row in raw["rows"]} == set(recorded) | {1}
    results = []
    for row in raw["rows"]:
        position_id = row["position_id"]
        word0, word1, instrument_word = (int(row[key], 16) for key in ("word0", "word1", "instrument_word1"))
        entry = (word0 >> 192) & RATE_MASK
        instrument = (word0 >> 160) & 0xffffffff
        leverage = (word1 >> 128) & 0xffffffff
        side = (word1 >> 224) & 1
        active = (word1 >> 240) & 1
        rate = (instrument_word >> 120) & RATE_MASK
        assert instrument == row["instrument"]
        assert 0 < rate < 10**18
        if position_id in recorded:
            decoded = recorded[position_id]
            assert (entry, instrument, leverage, side) == (
                decoded["entry_price"], decoded["instrument"], decoded["leverage"], decoded["top_32_flags"] & 1)
        predicted = calculate(entry, leverage, side, rate)
        actual = int(row["getter_output"], 16)
        assert actual == predicted, (position_id, actual, predicted)
        results.append({"position_id": position_id, "instrument": instrument, "entry_price": entry,
                        "leverage": leverage, "side": "long" if side else "short", "active": bool(active),
                        "maintenance_rate_1e18": rate, "observed_price": actual, "predicted_price": predicted})
    boundary = read("exchange_liquidation_behavior.json")["price_boundaries"]
    by_id = {row["position_id"]: row for row in results}
    for item in boundary:
        target = item["last_success_price"] if item["side"] == "long" else item["first_success_price"]
        assert by_id[item["position_id"]]["observed_price"] == target
    behavior = {"pin": PIN, "block_hash": manifest["block_hash"], "exchange_proxy": PROXY,
                "implementation": "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee", "selector": SELECTOR,
                "raw_evidence": "../../artifacts/exchange_liquidation/pinned_price_getter.json",
                "sample_count": len(results), "matched_formula_count": len(results),
                "active_count": sum(row["active"] for row in results),
                "long_count": sum(row["side"] == "long" for row in results),
                "short_count": sum(row["side"] == "short" for row in results),
                "fork_boundary_count": len(boundary), "instrument_rates_1e18": {
                    str(k): next(row["maintenance_rate_1e18"] for row in results if row["instrument"] == k)
                    for k in sorted({row["instrument"] for row in results})},
                "formula": "base = entry - floor(entry / leverage) for long, else entry + floor(entry / leverage); adjustment = floor(base * maintenance_rate / 10^18); output = base + adjustment for long, else base - adjustment",
                "position_word0": "mapping 10: entry bits 192..255, instrument bits 160..191",
                "position_word1": "mapping 10 offset 1: leverage bits 128..159, side bit 224, active bit 240",
                "instrument_word1": "mapping 7 offset 1: maintenance rate bits 120..183",
                "signature_status": "semantic behavior verified; exact Solidity function name unresolved",
                "limits": ["Sampled 26 position IDs at one pinned block and two instrument rates.",
                           "The view also calculates a price for inactive positions.",
                           "Other field values, overflow, and zero-leverage behavior are untested."],
                "cases": results}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print({k: behavior[k] for k in ("sample_count", "matched_formula_count", "active_count", "long_count", "short_count", "fork_boundary_count")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
