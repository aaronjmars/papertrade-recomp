#!/usr/bin/env python3
"""Record revert selectors actually observed in saved historical call traces."""

import collections
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
TRACES = ROOT / "artifacts" / "historical"
manifest = json.loads((ATLAS / "manifest.json").read_text())
roles = {a: x["role"] for a, x in manifest["contracts"].items()}
grouped = collections.defaultdict(list)


def visit(node, tx_hash):
    if node.get("error"):
        target = (node.get("to") or "").lower()
        output = node.get("output", "")
        selector = output[:10] if len(output) >= 10 else None
        grouped[(target, selector)].append({"tx": tx_hash, "called_selector": node.get("input", "")[:10],
                                           "error": node["error"], "output_prefix": output[:74]})
    for child in node.get("calls", []):
        visit(child, tx_hash)


for path in TRACES.glob("*.calls.json"):
    visit(json.loads(path.read_text()), path.name.removesuffix(".calls.json"))
resolved = {}
rows = []
for (target, selector), samples in sorted(grouped.items()):
    if selector and selector not in resolved:
        run = subprocess.run(["cast", "4byte", "--json", selector], capture_output=True, text=True, timeout=30)
        try:
            resolved[selector] = json.loads(run.stdout).get("data") or []
        except json.JSONDecodeError:
            resolved[selector] = []
        time.sleep(0.1)
    rows.append({"target": target, "role": roles.get(target, "external_or_system"), "revert_selector": selector,
                 "public_signature_candidates": resolved.get(selector, []) if selector else [],
                 "count_in_saved_traces": len(samples), "samples": samples[:5]})
(ATLAS / "observed_reverts.json").write_text(json.dumps({"saved_trace_count": len(list(TRACES.glob("*.calls.json"))), "reverts": rows}, indent=2) + "\n")
print(len(rows), "target-selector revert groups")
