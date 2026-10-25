#!/usr/bin/env python3
"""Compare public-fork and archive-backed PriceOracle branch probes."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PUBLIC = ROOT / "artifacts" / "oracle_local_replay"
ARCHIVE = ROOT / "artifacts" / "oracle_archive_local_replay"
OUTPUT = ATLAS / "oracle_fork_comparison.json"


def call_tree(trace):
    return {key: trace.get(key) for key in ("type", "to", "input", "output", "error")} | {
        "calls": [call_tree(child) for child in trace.get("calls", [])]}


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    cases = []
    for path in sorted(PUBLIC.glob("*.call.json")):
        public = json.loads(path.read_text())
        archive = json.loads((ARCHIVE / path.name).read_text())
        assert public["pin"] == archive["pin"] == manifest["block"]
        assert public["block_hash"] == archive["block_hash"] == manifest["block_hash"]
        cases.append({"name": path.name.removesuffix(".call.json"),
                      "same_mock_runtime_codes": public["mock_runtime_codes"] == archive["mock_runtime_codes"],
                      "same_call_tree": call_tree(public["trace"]) == call_tree(archive["trace"]),
                      "success": archive["trace"].get("error") is None})
    result = {"pin_block": manifest["block"], "pin_hash": manifest["block_hash"],
              "case_count": len(cases),
              "same_mock_count": sum(row["same_mock_runtime_codes"] for row in cases),
              "same_call_tree_count": sum(row["same_call_tree"] for row in cases),
              "cases": cases,
              "limits": ["The 25 cases use synthetic HyperCore read precompile outputs and prove only their tested Oracle paths.",
                         "The earlier public-fork files did not record their upstream RPC URL; this comparison uses their saved traces."]}
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    assert result["case_count"] == result["same_mock_count"] == result["same_call_tree_count"] == 25
    print("Oracle fork comparison: 25/25 call trees and mock runtimes match")


if __name__ == "__main__":
    main()
