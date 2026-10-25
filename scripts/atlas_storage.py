#!/usr/bin/env python3
"""Trace historical view calls to map exact EVM storage reads."""

import json
import pathlib
import re
import subprocess
import sys

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PIN = 48902346
manifest = json.loads((ATLAS / "manifest.json").read_text())
catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
proxy_for = {}
for address, contract in manifest["contracts"].items():
    if contract["role"].endswith("_proxy"):
        impl = "0x" + contract["eip1967_slots"]["implementation"][-40:]
        proxy_for[impl] = address


def case_body(text, selector):
    marker = f"case {selector} {{"
    pos = text.find(marker)
    if pos < 0:
        return ""
    start = pos + len(marker)
    depth = 1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
    return ""


def encode_arg(type_name):
    if not type_name:
        return "", None
    value = 1 if type_name in ("uint256", "uint32") else int("fb94d3404c1d3d9d6f08f79e58041d5ea95accfa", 16)
    if type_name == "bytes32":
        value = 0
    return value.to_bytes(32, "big").hex(), value


results = {}
for address, contract in manifest["contracts"].items():
    role = contract["role"]
    if role.endswith("_proxy") or "variant" in role or "library" in role:
        continue
    if len(sys.argv) > 1 and role != sys.argv[1]:
        continue
    target = proxy_for.get(address, address)
    yul_path = ATLAS / "decompiled" / f"{role}_yul-decompiled.yul"
    yul = yul_path.read_text() if yul_path.exists() else ""
    rows = []
    for function in catalog[address]["functions"]:
        if function["state_mutability"] != "view" or function["arguments"] not in ("", "address", "uint256", "uint32", "bytes32"):
            continue
        selector = function["selector"]
        argdata, argvalue = encode_arg(function["arguments"])
        row = {"selector": selector, "candidate_signature": function["candidate_signature"], "arguments": function["arguments"], "sample_argument": argvalue, "target": target}
        try:
            trace = rpc("debug_traceCall", [{"to": target, "data": selector + argdata}, hex(PIN), {"disableMemory": True, "disableStorage": True}])
            row["failed"] = trace["failed"]
            row["return_prefix"] = "0x" + trace.get("returnValue", "").removeprefix("0x")[:128]
            reads = []
            for step in trace.get("structLogs", []):
                if step["op"] == "SLOAD" and step.get("stack"):
                    reads.append({"slot": step["stack"][-1].lower(), "pc": step["pc"], "depth": step["depth"]})
            row["sloads"] = reads
            body = case_body(yul, selector)
            base_candidates = {int(x, 16) for x in re.findall(r"mstore\(0x20,\s*(0x[0-9a-f]+)\)", body) if int(x, 16) < 512}
            matches = []
            if argvalue is not None:
                for base in sorted(base_candidates):
                    preimage = argvalue.to_bytes(32, "big") + base.to_bytes(32, "big")
                    digest = int(subprocess.check_output(["cast", "keccak", "0x" + preimage.hex()], text=True).strip(), 16)
                    for read in reads:
                        actual = int(read["slot"], 16)
                        if 0 <= actual - digest <= 32:
                            matches.append({"base_slot": base, "field_offset": actual - digest, "read_slot": read["slot"], "pc": read["pc"]})
            row["mapping_matches"] = matches
            row["direct_slots"] = sorted({int(read["slot"], 16) for read in reads if int(read["slot"], 16) < 512})
        except Exception as exc:
            row["error"] = str(exc)
        rows.append(row)
    results[address] = {"role": role, "target": target, "views": rows}
    print(role, len(rows), sum("error" in r for r in rows), flush=True)

output_path = ATLAS / "storage_trace_catalog.json"
if len(sys.argv) > 1 and output_path.exists():
    existing = json.loads(output_path.read_text())
    existing.update(results)
    results = existing
output_path.write_text(json.dumps(results, indent=2) + "\n")
