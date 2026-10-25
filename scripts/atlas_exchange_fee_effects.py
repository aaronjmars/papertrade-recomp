#!/usr/bin/env python3
"""Isolate the Exchange liquidation fee slot on an archive-backed local fork."""

import argparse
import json
import os
import pathlib

from atlas_exchange_liquidation import EXCHANGE, LIQUIDATED, PIN, trace
from atlas_exchange_positions import position_slot
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_fee_effects" / "local_probes.json"
BEHAVIOR = ATLAS / "exchange_fee_effects_behavior.json"
RATE = 2 * 10**16
CASES = {
    "long_baseline": (1394473, 800000, {23: RATE, 24: RATE, 25: RATE}),
    "long_slot23_zero": (1394473, 800000, {23: 0, 24: RATE, 25: RATE}),
    "long_slot24_zero": (1394473, 800000, {23: RATE, 24: 0, 25: RATE}),
    "long_slot25_zero": (1394473, 800000, {23: RATE, 24: RATE, 25: 0}),
    "long_slot25_double": (1394473, 800000, {23: RATE, 24: RATE, 25: 2 * RATE}),
    "short_slot25_zero": (1394060, 245000, {23: RATE, 24: RATE, 25: 0}),
    "short_slot25_one": (1394060, 245000, {23: RATE, 24: RATE, 25: 1}),
    "short_slot25_three": (1394060, 245000, {23: RATE, 24: RATE, 25: 3}),
    "short_slot25_odd": (1394060, 245000, {23: RATE, 24: RATE, 25: 10**16 + 1}),
    "short_baseline": (1394060, 245000, {23: RATE, 24: RATE, 25: RATE}),
}


def read(name):
    return json.loads((ATLAS / name).read_text())


def word(value):
    return f"0x{value:064x}"


def log_words(log):
    data = log["data"]
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def capture(local_url):
    archive_url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read("manifest.json")
    hashes = {name: rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"]
              for name, url in (("archive", archive_url), ("local", local_url))}
    assert set(hashes.values()) == {manifest["block_hash"]}
    assert int(rpc(local_url, "eth_chainId", []), 16) == manifest["chain_id"]
    base = {slot: rpc(archive_url, "eth_getStorageAt", [EXCHANGE, word(slot), hex(PIN)])
            for slot in (23, 24, 25, 26)}
    assert all(rpc(local_url, "eth_getStorageAt", [EXCHANGE, word(slot), hex(PIN)]) == value
               for slot, value in base.items())
    witness_slot = word(position_slot(1394473) + 1)
    witness = {name: rpc(url, "eth_getStorageAt", [EXCHANGE, witness_slot, hex(PIN)])
               for name, url in (("archive", archive_url), ("local", local_url))}
    assert witness["archive"] == witness["local"]
    records = []
    try:
        for label, (position_id, price, rates) in CASES.items():
            for slot, rate in rates.items():
                rpc(local_url, "anvil_setStorageAt", [EXCHANGE, word(slot), word(rate)])
                assert int(rpc(local_url, "eth_getStorageAt", [EXCHANGE, word(slot), hex(PIN)]), 16) == rate
            result = trace(local_url, position_id, price, state=True)
            records.append({"label": label, "position_id": position_id, "price": price,
                            "rates": {str(slot): str(rate) for slot, rate in rates.items()}, "trace": result})
    finally:
        for slot in (23, 24, 25):
            rpc(local_url, "anvil_setStorageAt", [EXCHANGE, word(slot), base[slot]])
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin": PIN, "block_hash": manifest["block_hash"],
                                    "chain_id": manifest["chain_id"], "exchange": EXCHANGE,
                                    "source": "archive-backed Anvil fork with synthetic HyperCore BBO",
                                    "hashes": hashes, "witness_slot": witness_slot, "witness_words": witness,
                                    "base_slots": {str(slot): value for slot, value in base.items()},
                                    "records": records}, indent=2) + "\n")


def verify():
    raw = json.loads(ARTIFACT.read_text())
    manifest = read("manifest.json")
    assert raw["pin"] == PIN and raw["block_hash"] == manifest["block_hash"]
    assert raw["chain_id"] == manifest["chain_id"] and raw["exchange"] == EXCHANGE
    assert set(raw["hashes"].values()) == {manifest["block_hash"]}
    assert raw["witness_slot"] == word(position_slot(1394473) + 1)
    assert raw["witness_words"]["archive"] == raw["witness_words"]["local"]
    base = {int(slot): int(value, 16) for slot, value in raw["base_slots"].items()}
    assert all(base[slot] == RATE for slot in (23, 24, 25))
    assert len(raw["records"]) == len(CASES)
    margins = {row["position_id"]: row["decoded"]["margin"]
               for row in read("exchange_position_layout.json")["records"]}
    assert set(CASES) == {row["label"] for row in raw["records"]}
    summary = {}
    by_label = {}
    for row in raw["records"]:
        label = row["label"]
        position_id, price, rates = CASES[label]
        assert (row["position_id"], row["price"]) == (position_id, price)
        assert {int(slot): int(value) for slot, value in row["rates"].items()} == rates
        traced = row["trace"]
        assert traced["error"] is None and traced["mock_bid"] == traced["mock_ask"] == price
        events = [log for log in traced["logs"] if log["topics"][0] == LIQUIDATED]
        assert len(events) == 1 and events[0]["address"].lower() == EXCHANGE
        assert int(events[0]["topics"][1], 16) == position_id
        words = log_words(events[0])
        assert words[0] == price
        total = margins[position_id] * rates[25] // 10**18
        staker, dev = total // 2, total - total // 2
        assert words[3:5] == [staker, dev], (label, words[3:5], staker, dev)
        storage = traced["storage_changes"][EXCHANGE]
        pre = int(storage["pre"].get(word(26), raw["base_slots"]["26"]), 16)
        post = int(storage["post"].get(word(26), raw["base_slots"]["26"]), 16)
        mask = (1 << 128) - 1
        assert (post & mask) - (pre & mask) == staker
        assert (post >> 128) - (pre >> 128) == dev
        summary[label] = {"position_id": position_id, "margin": str(margins[position_id]),
                          "slot25_rate": str(rates[25]), "total_fee": str(total),
                          "staker_fee": str(staker), "dev_fee": str(dev)}
        by_label[label] = traced
    baseline = by_label["long_baseline"]
    prior = json.loads((ROOT / "artifacts" / "exchange_liquidation" / "pinned_local_probes.json").read_text())
    prior_baseline = prior["single_batch_comparison"]["single"]
    assert baseline["logs"] == prior_baseline["logs"]
    assert baseline["storage_changes"] == prior_baseline["storage_changes"]
    for label in ("long_slot23_zero", "long_slot24_zero"):
        assert by_label[label]["logs"] == baseline["logs"]
        assert by_label[label]["storage_changes"] == baseline["storage_changes"]
    assert summary["short_slot25_one"]["total_fee"] == "315"
    assert summary["short_slot25_one"]["staker_fee"] == "157"
    assert summary["short_slot25_one"]["dev_fee"] == "158"
    behavior = {"pin": PIN, "block_hash": manifest["block_hash"], "exchange_proxy": EXCHANGE,
                "raw_evidence": "../../artifacts/exchange_fee_effects/local_probes.json",
                "case_count": len(CASES), "prior_baseline_logs_match": True,
                "prior_baseline_storage_match": True, "slot23_or_24_zero_same_as_baseline": True,
                "fee_formula": "total = floor(margin * slot25 / 10^18); staker = floor(total / 2); dev = total - staker",
                "slot26": "low 128 bits staker fee accumulator; high 128 bits dev fee accumulator",
                "cases": summary,
                "limits": ["The observed fee split covers two active positions and synthetic prices on an archive-backed fork.",
                           "Changing slots 23 and 24 did not alter the tested liquidation path, but may affect other paths.",
                           "No live transaction changed the three fee rates in the saved history."]}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print({"cases": len(CASES), "odd_split": summary["short_slot25_one"],
           "baseline_match": behavior["prior_baseline_storage_match"]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-rpc-url", help="Archive-backed local Anvil fork URL")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    verify()
