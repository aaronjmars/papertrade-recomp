#!/usr/bin/env python3
"""Verify independent profit and loss rate inputs to the live close-settlement library."""

import json
import pathlib

from atlas_exchange_close_fee_effects import verify as verify_positive_replays
from atlas_exchange_library import LIBRARY, SETTLEMENT_SELECTOR, all_calls, settlement_model, words
from atlas_exchange_negative_close_fee import verify as verify_mixed_replay

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
BEHAVIOR = ATLAS / "exchange_library_fee_rates_behavior.json"
SOURCES = {
    "mixed_gain_loss": ROOT / "artifacts" / "exchange_negative_close" / "local_probes.json",
    "queued_profit": ROOT / "artifacts" / "exchange_close_fee_effects" / "local_probes.json",
    "direct_profit": ROOT / "artifacts" / "exchange_close_fee_effects" / "direct_local_probes.json",
}


def library_settlements(trace):
    return [node for node, _ in all_calls(trace)
            if node.get("to", "").lower() == LIBRARY
            and node.get("input", "")[:10] == SETTLEMENT_SELECTOR]


def run():
    verify_positive_replays()
    verify_mixed_replay()
    records = []
    for source, path in SOURCES.items():
        raw = json.loads(path.read_text())
        for case in raw["records"]:
            rates = {int(slot): int(value) for slot, value in case["rates"].items()}
            calls = library_settlements(case["trace"])
            assert len(calls) == (2 if source == "mixed_gain_loss" else 1)
            for node in calls:
                args = words("0x" + node["input"][10:])
                actual = words(node["output"])
                assert len(args) == 8 and len(actual) == 6
                assert args[5] == rates[24] and args[6] == rates[23]
                assert actual == settlement_model(args)
                pnl = args[3]
                selected_rate = args[5] if pnl > 0 else args[6] if pnl < 0 else 0
                fee = abs(pnl) * selected_rate // 10**18
                if pnl > 0 and args[7] != 0:
                    assert actual[1] == pnl - fee and actual[4] + actual[5] == fee
                elif pnl > 0:
                    assert actual[2] == pnl - fee and actual[4:6] == [0, 0]
                elif pnl < 0:
                    assert actual[0] == args[2] + pnl
                    if args[7] != 0:
                        assert actual[4] + actual[5] == fee
                records.append({"source": source, "case": case["label"],
                                "adjusted_pnl": str(pnl), "tail_input": str(args[7]),
                                "profit_rate": str(args[5]), "loss_rate": str(args[6]),
                                "selected_rate": str(selected_rate), "fee": str(fee),
                                "arguments": [str(x) for x in args],
                                "outputs": [str(x) for x in actual]})
    assert len(records) == 36
    assert {row["source"] for row in records} == set(SOURCES)
    mix = {}
    for row in records:
        if row["source"] == "mixed_gain_loss":
            mix[(row["case"], "profit" if int(row["adjusted_pnl"]) > 0 else "loss")] = row
    assert len(mix) == 20
    for side in ("profit", "loss"):
        assert mix[("baseline", side)]["outputs"] == mix[("slot25_zero", side)]["outputs"]
    assert mix[("slot23_zero", "profit")]["outputs"] == mix[("baseline", "profit")]["outputs"]
    assert mix[("slot24_zero", "loss")]["outputs"] == mix[("baseline", "loss")]["outputs"]
    assert mix[("slot23_zero", "loss")]["fee"] == "0"
    assert mix[("slot24_zero", "profit")]["fee"] == "0"
    summary = {source: sum(row["source"] == source for row in records) for source in SOURCES}
    behavior = {"pin": 48902346, "library": LIBRARY,
                "selector": SETTLEMENT_SELECTOR,
                "source_artifacts": {name: str(path.relative_to(ROOT)) for name, path in SOURCES.items()},
                "call_count": len(records), "calls_by_source": summary,
                "profit_rate_argument_index": 5, "loss_rate_argument_index": 6,
                "slot_mapping": {"23": "loss rate", "24": "profit rate", "25": "not passed to this library call"},
                "rate_denominator": str(10**18),
                "fee_rule": "floor(abs(adjusted PnL) * selected rate / 10^18)",
                "mixed_baseline_profit_fee": mix[("baseline", "profit")]["fee"],
                "mixed_baseline_loss_fee": mix[("baseline", "loss")]["fee"],
                "mixed_slot23_zero_loss_fee": mix[("slot23_zero", "loss")]["fee"],
                "mixed_slot24_zero_profit_fee": mix[("slot24_zero", "profit")]["fee"],
                "records": records,
                "limits": ["All 36 changed-rate calls are local fork traces derived from three historical signed-close baselines.",
                           "The saved changed-rate set covers profit with and without a queue and a directly settled loss. A queued loss with unequal rates was not observed.",
                           "The exact Solidity name of the linked-library selector remains unknown."]}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(f"verified {len(records)} linked-library settlement calls with independent fee rates")


if __name__ == "__main__":
    run()
