#!/usr/bin/env python3
"""Reconcile newest Exchange pinned aggregate accounting to Tokenomics LP."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"


def read(name):
    return json.loads((ATLAS / name).read_text())


def verify():
    manifest = read("manifest.json")
    storage = read("exchange_storage_words.json")
    exchange_getters = read("exchange_direct_getters_behavior.json")
    tokenomics_getters = read("tokenomics_direct_getters_behavior.json")
    assert (
        manifest["block"]
        == storage["block"]
        == exchange_getters["pin_block"]
        == tokenomics_getters["pin_block"]
        == 48902346
    )
    assert (
        manifest["block_hash"]
        == storage["block_hash"]
        == exchange_getters["block_hash"]
        == tokenomics_getters["block_hash"]
    )
    assert storage["address"] == exchange_getters["exchange_proxy"] == EXCHANGE
    slots = storage["slots"]
    relevant = {
        selector: next(
            row
            for row in exchange_getters["direct_slot_getters"]
            if row["selector"] == selector
        )
        for selector in (
            "0x01ad056f",
            "0x53ac4b66",
            "0x61d027b3",
            "0x7d004aeb",
            "0xa69a2ad1",
            "0xafdf6702",
        )
    }
    for row in relevant.values():
        assert int(row["raw_word"], 16) == int(slots[str(row["storage_slot"])], 16)
    packed_total = int(slots["22"], 16)
    total_balances = packed_total & ((1 << 128) - 1)
    locked_margin = packed_total >> 128
    packed_fees = int(slots["26"], 16)
    staker_fee = packed_fees & ((1 << 128) - 1)
    dev_fee = packed_fees >> 128
    treasury = int(slots["14"], 16)
    queued = int(slots["18"], 16)
    for selector, expected in (
        ("0xa69a2ad1", total_balances),
        ("0x01ad056f", locked_margin),
        ("0x61d027b3", treasury),
        ("0x53ac4b66", queued),
        ("0xafdf6702", staker_fee),
        ("0x7d004aeb", dev_fee),
    ):
        assert int(relevant[selector]["getter_output"], 16) == expected
    tracked = next(
        row
        for row in tokenomics_getters["direct_getter_checks"]
        if row["selector"] == "0x8cf554a7"
    )
    assert tracked["signature"] == "trackedLpUsd()"
    raw = int(tracked["raw_word"], 16)
    lp = raw - (1 << 256) if raw >= 1 << 255 else raw
    assert int(tracked["getter_output"], 16) == raw
    assert queued == 0
    assert treasury == total_balances + locked_margin + staker_fee + dev_fee + lp
    return {
        "pin": 48902346,
        "treasury_18": treasury,
        "ordinary_balances_18": total_balances,
        "locked_margin_18": locked_margin,
        "staker_fee_18": staker_fee,
        "dev_fee_18": dev_fee,
        "tracked_lp_18": lp,
        "queued_18": queued,
        "difference_18": 0,
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
