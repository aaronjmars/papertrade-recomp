#!/usr/bin/env python3
"""Compare old public-fork sweep probes with archive-backed reruns."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PUBLIC = ROOT / "artifacts" / "exchange_sweep_local"
ARCHIVE = ROOT / "artifacts" / "exchange_sweep_archive_local"
OUTPUT = ATLAS / "exchange_sweep_fork_comparison.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"


def descendants(call):
    yield call
    for child in call.get("calls", []):
        yield from descendants(child)


def logs(trace):
    return [{"address": log["address"], "topics": log["topics"], "data": log["data"]}
            for call in descendants(trace) for log in call.get("logs", [])]


def changed_storage(diff):
    trace = diff["trace"]
    result = {}
    for address in set(trace.get("pre", {})) | set(trace.get("post", {})):
        before = trace.get("pre", {}).get(address, {}).get("storage", {})
        after = trace.get("post", {}).get(address, {}).get("storage", {})
        for slot in set(before) | set(after):
            delta = int(after.get(slot, "0x0"), 16) - int(before.get(slot, "0x0"), 16)
            if delta:
                result[(address, slot)] = delta
    return result


def capture():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    cases = []
    baseline_differences = set()
    for path in sorted(PUBLIC.glob("*.call.json")):
        old = json.loads(path.read_text())
        new = json.loads((ARCHIVE / path.name).read_text())
        assert old["block_hash"] == new["block_hash"] == manifest["block_hash"]
        diff_name = path.name.replace(".call.json", ".diff.json")
        old_diff = json.loads((PUBLIC / diff_name).read_text())
        new_diff = json.loads((ARCHIVE / diff_name).read_text())
        old_trace, new_trace = old["trace"], new["trace"]
        old_deltas, new_deltas = changed_storage(old_diff), changed_storage(new_diff)
        differences = [{"address": address, "slot": slot,
                        "public_delta": str(old_deltas.get((address, slot), 0)),
                        "archive_delta": str(new_deltas.get((address, slot), 0))}
                       for address, slot in sorted(set(old_deltas) | set(new_deltas))
                       if old_deltas.get((address, slot), 0) != new_deltas.get((address, slot), 0)]
        old_pre, new_pre = old_diff["trace"].get("pre", {}), new_diff["trace"].get("pre", {})
        for address in set(old_pre) | set(new_pre):
            old_storage = old_pre.get(address, {}).get("storage", {})
            new_storage = new_pre.get(address, {}).get("storage", {})
            for slot in set(old_storage) | set(new_storage):
                public_value = old_storage.get(slot)
                archive_value = new_storage.get(slot)
                if int(public_value or "0x0", 16) != int(archive_value or "0x0", 16):
                    baseline_differences.add((address, slot, public_value, archive_value))
        cases.append({"name": path.name.removesuffix(".call.json"),
                      "same_error_and_output": (old_trace.get("error"), old_trace.get("output")) ==
                                               (new_trace.get("error"), new_trace.get("output")),
                      "same_ordered_logs": logs(old_trace) == logs(new_trace),
                      "same_storage_deltas": not differences,
                      "storage_delta_differences": differences})
    old_minimum = json.loads((PUBLIC / "minimum_threshold.json").read_text())
    new_minimum = json.loads((ARCHIVE / "minimum_threshold.json").read_text())
    assert old_minimum["block_hash"] == new_minimum["block_hash"] == manifest["block_hash"]
    result = {"pin_block": manifest["block"], "pin_hash": manifest["block_hash"],
              "public_fork_artifacts": "../../artifacts/exchange_sweep_local",
              "archive_fork_artifacts": "../../artifacts/exchange_sweep_archive_local",
              "case_count": len(cases),
              "call_outcome_match_count": sum(row["same_error_and_output"] for row in cases),
              "ordered_log_match_count": sum(row["same_ordered_logs"] for row in cases),
              "storage_delta_match_count": sum(row["same_storage_deltas"] for row in cases),
              "baseline_differences": [{"address": a, "slot": s, "public": p, "archive": v}
                                       for a, s, p, v in sorted(baseline_differences)],
              "minimum_raw": {"public": old_minimum["minimum_success_raw"],
                              "archive": new_minimum["minimum_success_raw"]},
              "cases": cases,
              "limits": ["This compares the 24 saved sweep simulations only; it does not certify every Exchange path on a public fork.",
                         "The public-fork source is documented by the earlier capture setup; its artifact files did not record the upstream RPC URL.",
                         "Identical branch outcomes and logs do not make absolute storage values from the public fork correct."]}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    result = json.loads(OUTPUT.read_text())
    assert result["pin_block"] == manifest["block"] and result["pin_hash"] == manifest["block_hash"]
    assert result["case_count"] == len(result["cases"]) == 24
    assert result["call_outcome_match_count"] == result["ordered_log_match_count"] == 24
    assert result["storage_delta_match_count"] == 21
    assert len(result["baseline_differences"]) == 4
    assert {row["slot"] for row in result["baseline_differences"]} == {
        f"0x{14:064x}", f"0x{22:064x}",
        "0x933a5f0af51b8c355d37612ed469ebbf7f68d712e0def9e96e026e58c110fa76",
        "0x9dd4b849c5f1b72bdde76f68a1377400346bb6b113564c65e9ed4950e2cd821f"}
    changed = [row for row in result["cases"] if not row["same_storage_deltas"]]
    assert {row["name"] for row in changed} == {
        "finalize_perp_equal_normalized_spot", "finalize_perp_unchanged", "request_perp_at_minimum"}
    assert all(len(row["storage_delta_differences"]) == 1 and
               row["storage_delta_differences"][0]["address"] == EXCHANGE and
               row["storage_delta_differences"][0]["slot"].startswith("0x9dd4b849") for row in changed)
    assert result["minimum_raw"] == {"public": 1000000000, "archive": 1000000000}
    print("Sweep fork comparison: 24/24 outcomes and logs match, 21/24 storage deltas match")


if __name__ == "__main__":
    capture()
    verify()
