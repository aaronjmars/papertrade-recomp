#!/usr/bin/env python3
"""Generate untrusted Heimdall hints for each distinct nonproxy runtime."""

import json
import os
import pathlib
import shutil
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
# Heimdall 0.9.2 (https://github.com/Jon-Becker/heimdall-rs) generated the saved hints.
TOOL = os.environ.get("HEIMDALL") or shutil.which("heimdall") or "heimdall"
OUT = ATLAS / "decompiled"
OUT.mkdir(exist_ok=True)
manifest = json.loads((ATLAS / "manifest.json").read_text())
seen = set()
results = []

for address, contract in manifest["contracts"].items():
    role = contract["role"]
    if role.endswith("_proxy") or not contract["code_present"] or contract["sha256"] in seen:
        continue
    seen.add(contract["sha256"])
    for style, flag in (("sol", "--include-sol"), ("yul", "--include-yul")):
        name = f"{role}_{style}"
        cmd = [str(TOOL), "decompile", str(ATLAS / contract["runtime_file"]), flag, "--skip-resolving", "--default", "--output", str(OUT), "--name", name]
        started = time.monotonic()
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            result = {"role": role, "address": address, "style": style, "exit_code": run.returncode, "elapsed_seconds": round(time.monotonic() - started, 2), "log": f"decompiled/{name}.log"}
            (OUT / f"{name}.log").write_text(run.stdout + "\n" + run.stderr)
        except subprocess.TimeoutExpired as exc:
            result = {"role": role, "address": address, "style": style, "exit_code": None, "elapsed_seconds": round(time.monotonic() - started, 2), "error": "120s timeout"}
        results.append(result)
        print(result, flush=True)

(ATLAS / "decompiler_runs.json").write_text(json.dumps(results, indent=2) + "\n")
