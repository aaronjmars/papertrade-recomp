#!/usr/bin/env python3
"""Verify an additional fixed-revert Tokenomics selector in pinned bytecode."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "tokenomics_seven_word_stub_behavior.json"
IMPLEMENTATION = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
SELECTOR = "0x7c7df7b4"
ERROR = "0x32aa90b0"


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    row = manifest["contracts"][IMPLEMENTATION]
    raw = (ATLAS / row["runtime_file"]).read_text().strip()
    runtime = bytes.fromhex(raw.removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == row["sha256"]
    assert bytes.fromhex("63" + SELECTOR[2:] + "146103f257") in runtime[:0x120]
    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", raw],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1]
                    for line in disassembly.splitlines() if len(line) > 10 and line[8:10] == ": "}
    expected = {
        0x3f2: "JUMPDEST", 0x3f4: "CALLVALUE", 0x3f9: "PUSH1 0xe0",
        0x3fb: "CALLDATASIZE", 0x405: "PUSH2 0x040c",
        0x408: "PUSH2 0x06c2", 0x40b: "JUMP", 0x40c: "JUMPDEST",
        0x40e: "PUSH1 0x64", 0x410: "CALLDATALOAD",
        0x420: "PUSH1 0x84", 0x422: "CALLDATALOAD",
        0x42c: "MLOAD", 0x42d: "PUSH4 0x032aa90b",
        0x432: "PUSH1 0xe4", 0x434: "SHL", 0x436: "MSTORE",
        0x437: "REVERT", 0x6c2: "JUMPDEST", 0x6c3: "PUSH1 0x04",
        0x6c5: "CALLDATALOAD", 0x6d7: "JUMP",
    }
    for pc, op in expected.items():
        assert instructions[pc] == op, (hex(pc), instructions[pc], op)
    forbidden = {"SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE",
                 "DELEGATECALL", "STATICCALL", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4", "RETURN"}
    assert not [(pc, op) for pc, op in instructions.items()
                if (0x3f2 <= pc <= 0x437 or 0x6c2 <= pc <= 0x6d7) and op in forbidden]
    assert (0x032aa90b << 228).to_bytes(32, "big")[:4].hex() == ERROR[2:]
    replay = json.loads((ROOT / "artifacts" / "fixed_revert_local" / "replay.json").read_text())
    assert replay["block_hash"] == manifest["block_hash"]
    assert replay["runtime_hashes"]["TokenomicsImplementation"]["sha256"] == row["sha256"]
    assert replay["expected_revert_selectors"][SELECTOR] == ERROR
    assert "testTokenomicsSevenWord" in replay["test_names"]
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "implementation": IMPLEMENTATION, "runtime_sha256": row["sha256"],
        "selector": SELECTOR, "source_name_status": "unresolved",
        "minimum_calldata_bytes": 228,
        "validated_words": {"0x04": "address", "0x64": "uint64", "0x84": "uint8"},
        "other_word_types": "unresolved; selector tool inferred only five arguments despite the 224-byte argument-length check",
        "error_selector": ERROR, "error_name_status": "unresolved",
        "entry_pc": 0x3f2, "revert_pc": 0x437,
        "behavior": "canonical seven-word calls revert without storage reads, writes, logs, or external calls",
        "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json",
        "limits": ["No archived pinned probe was saved for this selector.",
                   "The result applies to the pinned live implementation; a later upgrade could change behavior."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified Tokenomics seven-word fixed-revert selector")


if __name__ == "__main__":
    main()
