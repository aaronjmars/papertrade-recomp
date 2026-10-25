#!/usr/bin/env python3
"""Check the live linked-library harvest path against saved traces and state diffs."""

import collections
import json
import pathlib
import subprocess

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_queue"
OUT = ATLAS / "exchange_library_harvest_behavior.json"
LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
PARENT = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SELECTOR = "0x79810ffe"
HARVEST = "0xddc63262"
TOPIC = "0x81ca9b2c230070eaa84787556b1aaf18bf1e2f07ea5d3dae4819db77a1a5b224"
SLOT18 = "0x" + f"{18:064x}"
HISTORICAL_TX = "0x4214fa14d9c5bf46fade1c7f3ca8d242baefaa52426395b1840f43b626ee8a99"
PROBE_FILES = (
    "harvest_0_probe.json", "harvest_1_probe.json", "harvest_2_probe.json", "harvest_3_probe.json",
    "partial_node_historical_state.json", "partial_node_probes.json",
    "append_harvest_1_local_probe.json", "append_harvest_2_local_probe.json",
)


def words(value):
    assert value.startswith("0x") and (len(value) - 2) % 64 == 0
    return [int(value[i:i + 64], 16) for i in range(2, len(value), 64)]


def descendant(call):
    if call.get("to", "").lower() == LIBRARY and call.get("input", "").startswith(SELECTOR):
        yield call
    for child in call.get("calls", []):
        yield from descendant(child)


def storage_delta(diff, slot):
    pre = diff["pre"].get(EXCHANGE, {}).get("storage", {})
    post = diff["post"].get(EXCHANGE, {}).get("storage", {})
    if slot not in pre:
        assert slot not in post, slot
        return 0
    return int(post.get(slot, "0x0"), 16) - int(pre[slot], 16)


def check_case(label, trace, diff, events, kind, source, keccak):
    assert trace["to"].lower() == EXCHANGE and trace["input"].startswith(HARVEST)
    limit = words("0x" + trace["input"][10:])[0]
    assert len(trace.get("calls", [])) == 1
    parent = trace["calls"][0]
    assert parent["to"].lower() == PARENT and parent["input"] == trace["input"]
    calls = list(descendant(parent))
    assert len(calls) == 1, (label, len(calls))
    child = calls[0]
    assert child["type"] == "DELEGATECALL" and child.get("error") is None
    args = words("0x" + child["input"][10:])
    returns = words(child["output"])
    assert len(args) == 5 and len(returns) == 2
    assert args[0] == 15 and args[1] == limit and args[3] == 9
    paid, accumulator = returns
    assert paid <= args[2]
    assert accumulator == args[4] + paid
    assert words(parent["output"]) == words(trace["output"]) == [paid]
    assert storage_delta(diff, SLOT18) == -paid

    harvested = [event for event in events if event["topics"][0].lower() == TOPIC]
    assert len(harvested) <= limit
    assert (len(harvested) > 0) == (paid > 0)
    credits = collections.Counter()
    event_rows = []
    for event in harvested:
        assert event["address"].lower() == EXCHANGE and len(event["topics"]) == 2
        user = int(event["topics"][1], 16)
        assert user < 1 << 160
        amounts = words(event["data"])
        assert len(amounts) == 2 and amounts[0] > 0
        credits[user] += amounts[0]
        event_rows.append({"user": f"0x{user:040x}", "paid": str(amounts[0]),
                           "node_remaining": str(amounts[1])})
    assert sum(credits.values()) == paid
    for user, amount in credits.items():
        slot = "0x" + keccak(user.to_bytes(32, "big") + (9).to_bytes(32, "big")).hex()
        assert storage_delta(diff, slot) == amount, (label, user, amount)
    return {"label": label, "kind": kind, "source": source,
            "arguments": [str(value) for value in args],
            "returns": [str(value) for value in returns],
            "harvested_events": event_rows,
            "checks": {"limit_matches_parent": True, "paid_within_funding_cap": True,
                       "second_return_equals_fifth_argument_plus_paid": True,
                       "parent_return_equals_paid": True,
                       "queued_total_debit_equals_paid": True,
                       "event_amounts_equal_paid": True,
                       "user_balance_credits_equal_events": True}}


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["contracts"][LIBRARY]["code_present"]
    queue = json.loads((ATLAS / "exchange_queue_layout_behavior.json").read_text())
    assert queue["harvest"]["tx"] == HISTORICAL_TX
    keccak = Keccak()
    base = ROOT / "artifacts" / "historical" / HISTORICAL_TX
    trace = json.loads(base.with_suffix(".calls.json").read_text())
    diff = json.loads(base.with_suffix(".state_diff.json").read_text())
    receipt = json.loads(base.with_suffix(".receipt.json").read_text())
    assert receipt["status"] == "0x1"
    rows = [check_case("historical_harvest_32", trace, diff, receipt["logs"], "historical",
                       f"../../artifacts/historical/{HISTORICAL_TX}.calls.json", keccak)]
    counts = {}
    for name in PROBE_FILES:
        payload = json.loads((ARTIFACTS / name).read_text())
        cases = payload.get("cases", [payload])
        seen = 0
        for index, case in enumerate(cases):
            calls = list(descendant(case["trace"]))
            if not calls:
                assert case.get("available") == "0", (name, index)
                continue
            assert len(calls) == 1
            row = check_case(f"{name}:{index}", case["trace"], case["diff"],
                             calls[0].get("logs", []), "read_only_simulation",
                             "../../artifacts/exchange_queue/" + name, keccak)
            rows.append(row)
            seen += 1
        counts[name] = seen
    assert counts == {"harvest_0_probe.json": 1, "harvest_1_probe.json": 1,
                      "harvest_2_probe.json": 1, "harvest_3_probe.json": 1,
                      "partial_node_historical_state.json": 1, "partial_node_probes.json": 6,
                      "append_harvest_1_local_probe.json": 1,
                      "append_harvest_2_local_probe.json": 1}
    assert len(rows) == 14
    assert subprocess.run(["cast", "sig", "harvest(uint256)"], capture_output=True,
                          text=True, check=True).stdout.strip() == HARVEST
    assert sum(row["kind"] == "historical" for row in rows) == 1
    assert sum(row["kind"] == "read_only_simulation" for row in rows) == 13
    assert {int(row["arguments"][1]) for row in rows} == {0, 1, 2, 3, 32}
    assert any(int(row["arguments"][2]) == 3 * 10**18 and
               int(row["returns"][0]) == 3 * 10**18 for row in rows)
    assert any(len(row["harvested_events"]) == 2 and
               int(row["returns"][0]) == 7 * 10**18 for row in rows)
    result = {"pin": manifest["block"], "block_hash": manifest["block_hash"],
              "library": LIBRARY, "exchange_proxy": EXCHANGE,
              "exchange_parent_implementation": PARENT,
              "exchange_parent_selector_reconstructions": {HARVEST: "harvest(uint256)"},
              "selector": SELECTOR, "parent_selector": HARVEST,
              "historical_count": 1, "read_only_simulation_count": 13,
              "argument_semantics": {"0": "queue node mapping base 15",
                                     "1": "maximum nodes to process",
                                     "2": "payment cap supplied by Exchange",
                                     "3": "user balance mapping base 9",
                                     "4": "running amount whose returned value increases by the payment; economic name unresolved"},
              "return_semantics": {"0": "total amount credited to users",
                                   "1": "argument 4 plus total amount credited"},
              "observed_branches": ["zero node limit", "one to three different-user nodes",
                                    "same-user two-node queue", "underfunded first node",
                                    "underfunded second node"],
              "cases": rows,
              "limits": ["Only one of the 14 calls executed on-chain; thirteen are read-only archive-backed simulations.",
                         "A zero-availability Exchange call bypasses the library in two saved simulations.",
                         "All tested queues have at most three nodes; authorization, extreme values, and concurrent changes remain open."]}
    return result


def main():
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("linked-library harvest: 1 historical and 13 simulated calls, return words, events, and storage checked")


if __name__ == "__main__":
    main()
