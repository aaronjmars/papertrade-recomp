#!/usr/bin/env python3
"""Verify Exchange sideBucket getter, event, and adjacent historical writes."""

import json
import pathlib

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
CLOSE_TX = "0x20ee69d9f4191bff17d45a850a584d5803ca477986fd1684af985765d64d794b"
HARVEST_TX = "0x4214fa14d9c5bf46fade1c7f3ca8d242baefaa52426395b1840f43b626ee8a99"
GETTER = "sideBucket()"
SELECTOR = "0x9274682e"
EVENT = "SideBucketUpdated(uint256)"
TOPIC = "0xc2a40711b646c786b80242364fa8e26da64c5a4dfb2bf8fff83692db43600d89"
SLOT = "0x" + (27).to_bytes(32, "big").hex()


def verify():
    h = Keccak()
    assert "0x" + h(GETTER.encode()).hex()[:8] == SELECTOR
    assert "0x" + h(EVENT.encode()).hex() == TOPIC
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    assert SELECTOR in {row["selector"] for row in catalog[IMPLEMENTATION]["functions"]}
    traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
    getter = next(row for row in traces[IMPLEMENTATION]["views"] if row["selector"] == SELECTOR)
    assert not getter["failed"] and getter["direct_slots"] == [27]
    assert int(getter["return_prefix"], 16) == 0

    rows = []
    for tx, root_selector in ((CLOSE_TX, "0x251fb27d"), (HARVEST_TX, "0xddc63262")):
        receipt = json.loads((HISTORICAL / f"{tx}.receipt.json").read_text())
        call = json.loads((HISTORICAL / f"{tx}.calls.json").read_text())
        diff = json.loads((HISTORICAL / f"{tx}.state_diff.json").read_text())
        assert receipt["status"] == "0x1" and call["input"][:10] == root_selector
        logs = [log for log in receipt["logs"]
                if log["address"].lower() == PROXY and log["topics"][0] == TOPIC]
        assert len(logs) == 1 and logs[0]["topics"] == [TOPIC]
        assert len(logs[0]["data"]) == 66
        amount = int(logs[0]["data"], 16)
        pre = int(diff.get("pre", {}).get(PROXY, {}).get("storage", {}).get(SLOT, "0x0"), 16)
        post = int(diff.get("post", {}).get(PROXY, {}).get("storage", {}).get(SLOT, "0x0"), 16)
        assert amount == post
        rows.append({"transaction": tx, "block": int(receipt["blockNumber"], 16),
                     "root_selector": root_selector, "slot_27_pre": str(pre),
                     "slot_27_post": str(post), "event_amount": str(amount),
                     "zero_post_omitted_by_diff_tracer": SLOT not in diff.get("post", {}).get(PROXY, {}).get("storage", {})})
    assert rows[0]["block"] + 1 == rows[1]["block"]
    assert rows[0]["slot_27_post"] == rows[1]["slot_27_pre"]
    assert int(rows[0]["slot_27_post"]) > 0 and int(rows[1]["slot_27_post"]) == 0
    result = {"pin_block": 48902346, "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
              "selector_reconstructions": {SELECTOR: GETTER},
              "event_catalog": [{"topic0": TOPIC, "reconstructed_signature": EVENT,
                                 "status": "observed_historical_topic"}],
              "slot": 27, "pinned_getter_value": 0,
              "historical_transitions": rows,
              "limitations": ["Two adjacent historical transactions prove the emitted post values, not every writer of slot 27.",
                              "Diff-mode omission of a zero post word is interpreted as a cleared slot."]}
    (ATLAS / "exchange_side_bucket_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange side bucket: getter, event, close increase, harvest clear verified")


if __name__ == "__main__":
    verify()
