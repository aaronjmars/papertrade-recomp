#!/usr/bin/env python3
"""Trace one direct transaction per as-yet untraced entrypoint selector."""

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
samples = json.loads((ATLAS / "direct_transaction_samples.json").read_text())
graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
seen = {(row["root_role"], row["root_selector"]) for row in graph["traces"]}
hashes = []
selected = []
for contract in samples.values():
    for selector, group in contract["selectors"].items():
        if (contract["role"], selector) in seen:
            continue
        options = [group["first"], group["last"]]
        chosen = next((row for row in options if row["status"] == 1), options[0])
        hashes.append(chosen["hash"])
        selected.append({"role": contract["role"], "selector": selector, "tx": chosen["hash"], "status": chosen["status"]})
(ATLAS / "trace_expansion_targets.json").write_text(json.dumps(selected, indent=2) + "\n")
print(len(hashes), "transactions to trace", flush=True)
if hashes:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "trace.py"), *hashes], check=True)
