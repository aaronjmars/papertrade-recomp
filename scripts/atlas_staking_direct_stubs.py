#!/usr/bin/env python3
"""Prove four direct Staking entrypoints are fixed-revert paths in pinned code."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "staking_direct_stubs_behavior.json"
PROBES = ROOT / "artifacts" / "staking" / "pinned_direct_probes.json"
PROXY = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
IMPLEMENTATION = "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15"
ERROR = "0xa15ce1ba"
DISPATCH = {
    "0x2e17de78": (0x4a, 0x6e8, 0xe81, 1),
    "0x4e71d92d": (0x6b, 0x5bd, 0xea4, 0),
    "0xa694fc3a": (0x11b, 0x6e8, 0xe81, 1),
    "0xe4fc6b6d": (0x15d, 0x5bd, 0xea4, 0),
}
BODY = {
    0xe81: (0xea4, "5b346103a15760203660031901126103a1576040516350ae70dd60e11b8152600490fd"),
    0xea4: (0xec6, "5b346103a1575f3660031901126103a1576040516350ae70dd60e11b8152600490fd"),
}
EFFECTS = {"SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL",
           "STATICCALL", "CREATE", "CREATE2", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4",
           "SELFDESTRUCT", "RETURN"}


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["contracts"][PROXY]["role"] == "staking_proxy"
    implementation = manifest["contracts"][IMPLEMENTATION]
    code_hex = (ATLAS / implementation["runtime_file"]).read_text().strip()
    code = bytes.fromhex(code_hex.removeprefix("0x"))
    assert hashlib.sha256(code).hexdigest() == implementation["sha256"]
    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", code_hex],
                             capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1] for line in disassembly.splitlines()
                    if len(line) > 10 and line[8:10] == ": "}
    for selector, (dispatch_pc, entry_pc, body_pc, _) in DISPATCH.items():
        assert instructions[dispatch_pc] == f"PUSH4 {selector}"
        assert instructions[dispatch_pc + 5] == "EQ"
        assert instructions[dispatch_pc + 6] == f"PUSH2 0x{entry_pc:04x}"
        assert instructions[dispatch_pc + 9] == "JUMPI"
        assert instructions[entry_pc] == "JUMPDEST"
        assert instructions[entry_pc + 1] == f"PUSH2 0x{body_pc:04x}"
        assert instructions[entry_pc + 4] == "JUMP"
    for start, (end, expected_hex) in BODY.items():
        assert code[start:end].hex() == expected_hex
        assert instructions[start] == "JUMPDEST" and instructions[end - 1] == "REVERT"
        assert not [instructions[pc] for pc in instructions if start <= pc < end
                    and instructions[pc].split(" ", 1)[0] in EFFECTS]
        assert "PUSH4 0x50ae70dd" in [instructions[pc] for pc in instructions if start <= pc < end]
        assert "PUSH1 0xe1" in [instructions[pc] for pc in instructions if start <= pc < end]
    assert (0x50ae70dd << 1) & 0xffffffff == int(ERROR, 16)
    probes = json.loads(PROBES.read_text())
    assert probes["pin_block"] == manifest["block"] and probes["pin_hash"] == manifest["block_hash"]
    assert len(probes["probes"]) == 7
    names = {}
    for probe in probes["probes"]:
        trace = probe["trace"]
        call = probe["call"]
        selector = call["data"][:10]
        assert selector in DISPATCH and trace["input"] == call["data"]
        assert trace["to"].lower() == PROXY and trace["output"] == ERROR
        assert trace["error"] == "execution reverted" and len(trace["calls"]) == 1
        delegated = trace["calls"][0]
        assert delegated["to"].lower() == IMPLEMENTATION and delegated["type"] == "DELEGATECALL"
        assert delegated["input"] == call["data"] and delegated["output"] == ERROR
        assert delegated["error"] == "execution reverted" and not delegated.get("calls")
        assert not trace.get("logs") and not delegated.get("logs")
        names[probe["name"]] = selector
    assert set(names.values()) == set(DISPATCH)
    observed = json.loads((ATLAS / "observed_reverts.json").read_text())["reverts"]
    historical = next(row for row in observed if row["target"] == PROXY and row["revert_selector"] == ERROR)
    assert historical["count_in_saved_traces"] == 1
    assert historical["samples"][0]["called_selector"] == "0x4e71d92d"
    result = {"pin": manifest["block"], "block_hash": manifest["block_hash"],
              "proxy": PROXY, "implementation": IMPLEMENTATION,
              "runtime_sha256": implementation["sha256"],
              "selector_behaviors": {selector: {"entry_pc": entry, "body_pc": body,
                  "minimum_argument_words": words, "behavior": "canonical zero-value input reaches fixed revert"}
                  for selector, (_, entry, body, words) in DISPATCH.items()},
              "error_selector": ERROR, "error_name_status": "unresolved",
              "error_construction": "PUSH4 0x50ae70dd shifted left 225 bits yields 0xa15ce1ba",
              "effect_free_body_byte_ranges": [[start, end] for start, (end, _) in BODY.items()],
              "pinned_probe_count": len(names), "pinned_probe_names": names,
              "historical_revert_tx": historical["samples"][0]["tx"],
              "source_name_status": "unresolved; public stake, unstake, claim, and distribute signatures remain candidates",
              "limits": ["The proof covers the four dispatcher entries and their canonical ABI paths at the pinned runtime.",
                         "Malformed calldata or nonzero value can take generic empty-data revert branches.",
                         "The custom error and source function names remain unresolved."]}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    result = build()
    print("Staking fixed-revert entries:", len(result["selector_behaviors"]))
