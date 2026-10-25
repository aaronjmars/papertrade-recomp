#!/usr/bin/env python3
"""Verify two Exchange selectors that end in the same fixed revert."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "exchange_disabled_paths_behavior.json"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
ERROR = "0x58f03bf7"
SELECTORS = {
    "0x1afd17e9": {"entry": 0x3d21, "arguments": ["uint32", "bool", "uint128", "uint32"],
                   "canonical_calldata_bytes": 132, "revert_pc": 0x3d67},
    "0x63ca348f": {"entry": 0x247e, "arguments": ["uint32", "bool", "uint128", "uint32", "bool"],
                   "canonical_calldata_bytes": 164, "revert_pc": 0x24d0},
    "0x58d3ec6a": {"entry": 0x27e1, "arguments": ["uint256[]"],
                   "canonical_empty_array_calldata_bytes": 68, "revert_pc": 0x2825},
}


def read(name):
    return json.loads((ATLAS / name).read_text())


def main():
    manifest = read("manifest.json")
    row = manifest["contracts"][IMPLEMENTATION]
    runtime_hex = (ATLAS / row["runtime_file"]).read_text().strip()
    runtime = bytes.fromhex(runtime_hex.removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == row["sha256"]
    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", runtime_hex],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1] for line in disassembly.splitlines()
                    if len(line) > 10 and line[8:10] == ": "}
    expected = {
        "0x1afd17e9": {0x3d21: "JUMPDEST", 0x3d22: "CALLVALUE", 0x3d27: "PUSH1 0x80",
                       0x3d36: "PUSH2 0x3ec9", 0x3d3f: "PUSH2 0x3f02",
                       0x3d48: "PUSH2 0x3f11", 0x3d51: "PUSH2 0x3edc",
                       0x3d5a: "PUSH4 0x58f03bf7", 0x3d67: "REVERT"},
        "0x63ca348f": {0x247e: "JUMPDEST", 0x2480: "CALLVALUE", 0x2485: "PUSH1 0xa0",
                       0x2494: "PUSH2 0x3ec9", 0x249d: "PUSH2 0x3f02",
                       0x24a6: "PUSH2 0x3f11", 0x24af: "PUSH2 0x3edc",
                       0x24b5: "PUSH1 0x84", 0x24b7: "CALLDATALOAD",
                       0x24bb: "SUB", 0x24c3: "PUSH4 0x58f03bf7", 0x24d0: "REVERT"},
        "0x58d3ec6a": {0x27e1: "JUMPDEST", 0x27e3: "CALLVALUE",
                       0x27f4: "PUSH1 0x04", 0x27f6: "CALLDATALOAD",
                       0x280e: "PUSH2 0x3f57", 0x2818: "PUSH4 0x58f03bf7",
                       0x2825: "REVERT"},
    }
    regions = {"0x1afd17e9": (0x3d21, 0x3d68), "0x63ca348f": (0x247e, 0x24d1),
               "0x58d3ec6a": (0x27e1, 0x2826)}
    for selector, info in SELECTORS.items():
        pattern = bytes.fromhex("63" + selector[2:] + "14" + f"61{info['entry']:04x}" + "57")
        assert pattern in runtime[:0x400]
        for pc, op in expected[selector].items():
            assert instructions[pc] == op, (selector, hex(pc), instructions[pc], op)
        lo, hi = regions[selector]
        assert not [instructions[pc] for pc in instructions if lo <= pc < hi
                    and instructions[pc] in ("SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4", "RETURN")]
    helpers = [(0x3ec9, 0x3edc), (0x3edc, 0x3eef), (0x3f02, 0x3f11), (0x3f11, 0x3f27)]
    for lo, hi in helpers:
        assert instructions[lo] == "JUMPDEST"
        assert not [instructions[pc] for pc in instructions if lo <= pc < hi
                    and instructions[pc] in ("SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4")]
    assert instructions[0x3ec9] == "JUMPDEST" and instructions[0x3ece] == "PUSH4 0xffffffff"
    assert instructions[0x3f02] == "JUMPDEST" and instructions[0x3f08] == "ISZERO"
    assert instructions[0x3f11] == "JUMPDEST" and instructions[0x3f1a] == "PUSH1 0x80"
    assert instructions[0x3edc] == "JUMPDEST" and instructions[0x3ee1] == "PUSH4 0xffffffff"
    assert instructions[0x3f57] == "JUMPDEST" and instructions[0x3f65] == "CALLDATALOAD"
    assert instructions[0x3f86] == "JUMP"
    assert not [instructions[pc] for pc in instructions if 0x3f57 <= pc < 0x3f87
                and instructions[pc] in ("SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "DELEGATECALL", "STATICCALL", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4")]
    assert subprocess.run(["cast", "sig", "close(uint256[])"], capture_output=True, text=True, check=True).stdout.strip() == "0x58d3ec6a"

    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": row["sha256"], "error_selector": ERROR,
        "source_error_name_status": "unresolved",
        "selector_behaviors": {selector: {**info, "source_name_status": "hash-matching candidate only" if selector == "0x58d3ec6a" else "unresolved",
                                          **({"public_signature_candidate": "close(uint256[])"} if selector == "0x58d3ec6a" else {}),
                                          "behavior": "canonical nonpayable calldata passes ABI validation and then reverts with 0x58f03bf7; no storage read, write, log, or external call on this path"}
                               for selector, info in SELECTORS.items()},
        "bytecode_evidence": "runtime dispatcher, function entry, ABI validator, and fixed revert instruction offsets checked by atlas_exchange_disabled_paths.py",
        "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json",
        "limits": ["No archived dynamic probe was captured; a port-free local EVM replay exercises canonical calls through the exact pinned proxy and implementation bytecode.",
                   "Invalid ABI words or nonzero msg.value revert through the generic empty-data path.",
                   "The original function and error names remain unknown."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified three fixed-revert Exchange selectors")


if __name__ == "__main__":
    main()
