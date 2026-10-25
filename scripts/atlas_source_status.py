#!/usr/bin/env python3
"""Check explorer source verification for captured nonproxy contracts."""

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
status = {}
for address, contract in manifest["contracts"].items():
    if contract["role"].endswith("_proxy"):
        continue
    try:
        run = subprocess.run(["etherscan", "contract", "getsourcecode", address, "--chain", "999"], capture_output=True, text=True, check=True, timeout=30)
        rows = json.loads(run.stdout)
        row = rows[0] if rows else {}
        verified = bool(row.get("SourceCode"))
        status[address] = {"role": contract["role"], "verified": verified, "contract_name": row.get("ContractName"), "compiler_version": row.get("CompilerVersion")}
        if verified:
            (ATLAS / "verified_source").mkdir(exist_ok=True)
            (ATLAS / "verified_source" / f"{address}.json").write_text(json.dumps(row, indent=2) + "\n")
    except Exception as exc:
        status[address] = {"role": contract["role"], "verified": None, "error": str(exc)}
    print(contract["role"], status[address]["verified"], flush=True)
(ATLAS / "source_verification.json").write_text(json.dumps(status, indent=2) + "\n")
