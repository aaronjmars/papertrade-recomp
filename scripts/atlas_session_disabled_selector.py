#!/usr/bin/env python3
"""Verify the SessionKeyManager fixed-revert selector from pinned bytecode."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "session_disabled_selector_behavior.json"
PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
IMPLEMENTATION = "0x8a5069fe303e8f81e91825436e956d595032e558"
SELECTOR = "0x17a1678f"
ERROR = "0xd2dd8531"


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    row = manifest["contracts"][IMPLEMENTATION]
    runtime_hex = (ATLAS / row["runtime_file"]).read_text().strip()
    runtime = bytes.fromhex(runtime_hex.removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == row["sha256"]
    assert bytes.fromhex("6317a1678f14610a9757") in runtime[:0x100]
    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", runtime_hex],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1] for line in disassembly.splitlines()
                    if len(line) > 10 and line[8:10] == ": "}
    expected = {0xa97: "JUMPDEST", 0xa99: "CALLVALUE", 0xa9e: "PUSH1 0x60",
                0xaaa: "PUSH2 0x0ab1", 0xaad: "PUSH2 0x0b1b", 0xab0: "JUMP",
                0xab3: "PUSH1 0x24", 0xab5: "CALLDATALOAD", 0xaba: "PUSH1 0x40",
                0xac5: "PUSH1 0x44", 0xac7: "CALLDATALOAD", 0xacc: "PUSH1 0xa0",
                0xad8: "PUSH4 0xd2dd8531", 0xae2: "REVERT",
                0xb1b: "JUMPDEST", 0xb1e: "CALLDATALOAD", 0xb24: "PUSH1 0xa0",
                0xb30: "JUMP"}
    for pc, op in expected.items():
        assert instructions[pc] == op, (hex(pc), instructions[pc], op)
    for lo, hi in ((0xa97, 0xae3), (0xb1b, 0xb31)):
        assert not [instructions[pc] for pc in instructions if lo <= pc < hi
                    and instructions[pc] in ("SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4", "RETURN")]
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    function = next(item for item in catalog[IMPLEMENTATION]["functions"] if item["selector"] == SELECTOR)
    assert function["arguments"] == "address,uint64,address"
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": row["sha256"], "selector": SELECTOR,
        "arguments": ["address", "uint64", "address"],
        "source_name_status": "unresolved", "error_selector": ERROR,
        "error_name_status": "unresolved", "dispatcher_entry_pc": 0xa97,
        "address_decoder_pc": 0xb1b, "revert_pc": 0xae2,
        "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json",
        "behavior": "canonical nonpayable calls validate three ABI words and then revert with 0xd2dd8531, without storage, logs, or external calls",
        "limits": ["No archived dynamic call probe was captured; a port-free local EVM replay exercises canonical calls through the exact pinned proxy and implementation bytecode.",
                   "Malformed ABI words and nonzero msg.value use generic empty-data revert paths.",
                   "The original function and error names remain unknown."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified SessionKeyManager fixed-revert selector")


if __name__ == "__main__":
    main()
