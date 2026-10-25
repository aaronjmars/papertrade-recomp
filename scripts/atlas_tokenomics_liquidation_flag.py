#!/usr/bin/env python3
"""Compare Tokenomics liquidation mint branches at the pinned HyperEVM state."""

import argparse
import json
from pathlib import Path

from trace import rpc
from atlas_tokenomics import (EXCHANGE, LIQUIDATION_EVENT, LIQUIDATION_MINT,
                              TOKEN, TOKENOMICS, TRANSFER_EVENT, encode_call)

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "tokenomics_liquidation_flag"
PIN = 48902346
RECIPIENT = int("0x4444444444444444444444444444444444444444", 16)
CASES = {
    "true_positive": (1, 10**18, 98 * 10**16),
    "false_positive": (0, 10**18, 98 * 10**16),
    "true_zero": (1, 0, 0),
    "false_zero": (0, 0, 0),
    "true_credit_only": (1, 0, 98 * 10**16),
    "false_credit_only": (0, 0, 98 * 10**16),
}


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def descendants(call):
    yield call
    for child in call.get("calls", []):
        yield from descendants(child)


def call_shape(trace):
    return [(node.get("type"), (node.get("to") or "").lower(),
             node.get("input", "")[:10], node.get("error"))
            for node in descendants(trace)]


def all_logs(trace):
    return [(entry["address"].lower(), tuple(entry["topics"]), entry["data"])
            for node in descendants(trace) for entry in node.get("logs", [])]


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def storage_delta(diff, address, slot):
    key = "0x" + f"{slot:064x}"
    before = diff["pre"][address]["storage"][key]
    after = diff["post"][address]["storage"][key]
    return int(after, 16) - int(before, 16), int(before, 16), int(after, 16)


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    manifest = read(ATLAS / "manifest.json")
    header = rpc("eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    for name, (flag, basis, credit) in CASES.items():
        path = ARTIFACTS / f"{name}.json"
        if path.exists():
            saved = read(path)
        else:
            call = {"from": EXCHANGE, "to": TOKENOMICS,
                    "data": encode_call(LIQUIDATION_MINT,
                        [RECIPIENT, 123456789, flag, basis, credit]), "value": "0x0"}
            options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
            trace = rpc("debug_traceCall", [call, hex(PIN), options])
            diff = rpc("debug_traceCall", [call, hex(PIN),
                {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            saved = {"pin": PIN, "block_hash": header["hash"], "name": name,
                     "flag": flag, "basis": str(basis), "credit": str(credit),
                     "call": call, "trace": trace, "state_diff": diff}
        if name.endswith("positive") and "opcode_path" not in saved:
            result = rpc("debug_traceCall", [saved["call"], hex(PIN),
                {"disableStack": True, "disableMemory": True, "disableStorage": True}])
            assert not result.get("failed")
            saved["opcode_path"] = [[row["depth"], row["pc"], row["op"]]
                                     for row in result["structLogs"]]
        write(path, saved)
        print(name, saved["trace"].get("error", "success"),
              len(all_logs(saved["trace"])), flush=True)


def build():
    saved_cases = {}
    manifest = read(ATLAS / "manifest.json")
    for name, (flag, basis, credit) in CASES.items():
        saved = read(ARTIFACTS / f"{name}.json")
        assert saved["pin"] == PIN and saved["block_hash"].lower() == manifest["block_hash"]
        assert saved["name"] == name and saved["flag"] == flag
        assert saved["basis"] == str(basis) and saved["credit"] == str(credit)
        assert saved["call"]["from"].lower() == EXCHANGE
        assert saved["call"]["to"].lower() == TOKENOMICS
        assert saved["call"]["data"] == encode_call(LIQUIDATION_MINT,
            [RECIPIENT, 123456789, flag, basis, credit])
        saved_cases[name] = saved
    pairs = (("true_positive", "false_positive"),
             ("true_zero", "false_zero"),
             ("true_credit_only", "false_credit_only"))
    pair_checks = []
    for true_name, false_name in pairs:
        yes, no = saved_cases[true_name], saved_cases[false_name]
        assert call_shape(yes["trace"]) == call_shape(no["trace"])
        assert yes["state_diff"] == no["state_diff"]
        assert yes["trace"].get("error") == no["trace"].get("error")
        assert yes["trace"].get("output") == no["trace"].get("output")
        pair_checks.append({"true": true_name, "false": false_name,
                            "same_call_shape": True, "same_storage_diff": True,
                            "same_error_and_output": True})
    yes = saved_cases["true_positive"]
    no = saved_cases["false_positive"]
    assert yes["opcode_path"] == no["opcode_path"]
    assert len(yes["opcode_path"]) > 1000
    yes_logs, no_logs = all_logs(yes["trace"]), all_logs(no["trace"])
    assert len(yes_logs) == len(no_logs) == 2
    assert yes_logs[0][0] == no_logs[0][0] == TOKENOMICS
    assert yes_logs[0][1] == no_logs[0][1]
    assert yes_logs[0][1][0].lower() == LIQUIDATION_EVENT
    assert yes_logs[1] == no_logs[1]
    assert yes_logs[1][0] == TOKEN and yes_logs[1][1][0].lower() == TRANSFER_EVENT
    yes_event, no_event = words(yes_logs[0][2]), words(no_logs[0][2])
    assert len(yes_event) == len(no_event) == 6
    assert yes_event[0] == 1 and no_event[0] == 0
    assert yes_event[1:] == no_event[1:]
    assert yes_event[1] == CASES["true_positive"][1]
    tracked_delta, tracked_before, tracked_after = storage_delta(yes["state_diff"], TOKENOMICS, 3)
    tail_delta, _, _ = storage_delta(yes["state_diff"], TOKENOMICS, 4)
    supply_delta, _, _ = storage_delta(yes["state_diff"], TOKEN, 6)
    assert tracked_delta == CASES["true_positive"][2]
    assert yes_event[2:] == [tracked_before, tracked_after, tail_delta, supply_delta]
    assert words(yes_logs[1][2]) == [supply_delta]
    assert yes_logs[1][1][1] == "0x" + "0" * 64
    assert int(yes_logs[1][1][2], 16) == RECIPIENT
    for name in ("true_zero", "false_zero"):
        row = saved_cases[name]
        assert not row["trace"].get("error") and not all_logs(row["trace"])
        assert len(call_shape(row["trace"])) == 2
        assert TOKENOMICS not in row["state_diff"].get("post", {})
        assert TOKEN not in row["state_diff"].get("post", {})
    for name in ("true_credit_only", "false_credit_only"):
        row = saved_cases[name]
        assert row["trace"].get("error") == "execution reverted"
        assert row["trace"].get("output") == "0x85c58396"
        assert not all_logs(row["trace"])
        assert TOKENOMICS not in row["state_diff"].get("post", {})
        assert TOKEN not in row["state_diff"].get("post", {})
    report = {"pin": PIN, "block_hash": manifest["block_hash"],
              "selector": LIQUIDATION_MINT, "proxy": TOKENOMICS,
              "evidence": "six read-only archive debug_traceCall cases at the pinned block",
              "pairs": pair_checks,
              "positive_opcode_steps_per_case": len(yes["opcode_path"]),
              "positive_opcode_paths_identical": True,
              "positive_event_words_true": [str(x) for x in yes_event],
              "positive_event_words_false": [str(x) for x in no_event],
              "positive_paper_minted": str(supply_delta),
              "positive_tokenomics_tracked_delta": str(tracked_delta),
              "positive_tokenomics_tail_delta": str(tail_delta),
              "zero_cases_no_logs_or_tokenomics_writes": True,
              "credit_without_basis_error": "0x85c58396",
              "raw_artifacts": [str((ARTIFACTS / f"{name}.json").relative_to(ROOT))
                                for name in CASES],
              "limitations": ["Synthetic pinned calls, not historical false-flag execution.",
                              "Identical opcode paths proved for the sampled positive inputs only.",
                              "The source function and event names remain unresolved."]}
    write(ATLAS / "tokenomics_liquidation_flag_behavior.json", report)
    print("six Tokenomics flag cases checked; positive opcode paths:",
          len(yes["opcode_path"]), "identical")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    build()
