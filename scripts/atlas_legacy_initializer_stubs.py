#!/usr/bin/env python3
"""Prove three legacy initializer entries are fixed reverts in pinned runtimes."""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "legacy_initializer_stubs_behavior.json"
ERROR = "0xb7b2509c"
EFFECTS = {"SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL",
           "STATICCALL", "CREATE", "CREATE2", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4",
           "SELFDESTRUCT", "RETURN"}

SPECS = {
    "staking_implementation": {
        "address": "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15",
        "selector": "0xc0c53b8b", "dispatcher_pc": 0x126,
        "body_pc": 0x6ae,
        "body_hex": "5b50346103a15760603660031901126103a1576106c8610e3f565b506106d1610e55565b506106da610e6b565b5051632dec942760e21b8152fd",
        "decoder_pcs": (0xe3f, 0xe55, 0xe6b),
        "decoder_hex": (
            "5b600435906001600160a01b03821682036103a15756",
            "5b602435906001600160a01b03821682036103a15756",
            "5b604435906001600160a01b03821682036103a15756"),
        "linked_probe": "staking_initializers_behavior.json",
        "candidate_signature": "initialize(address,address,address)",
    },
    "batch_executor_implementation": {
        "address": "0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262",
        "selector": "0xc0c53b8b", "dispatcher_pc": 0x73,
        "body_pc": 0x15e,
        "body_hex": "5b3461010757606036600319011261010757610177610967565b5061018061097d565b50610189610993565b50604051632dec942760e21b8152600490fd",
        "decoder_pcs": (0x967, 0x97d, 0x993),
        "decoder_hex": (
            "5b600435906001600160a01b03821682036101075756",
            "5b602435906001600160a01b03821682036101075756",
            "5b604435906001600160a01b03821682036101075756"),
        "linked_probe": "batch_control_behavior.json",
        "candidate_signature": "initialize(address,address,address)",
    },
    "deposit_proxy_factory_implementation": {
        "address": "0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0",
        "selector": "0xc4d66de8", "dispatcher_pc": 0x60,
        "body_pc": 0x337,
        "body_hex": "5b503461011c57602036600319011261011c57610351610553565b5051632dec942760e21b8152fd",
        "decoder_pcs": (0x553,),
        "decoder_hex": ("5b600435906001600160a01b038216820361011c5756",),
        "linked_probe": "factory_behavior.json",
        "candidate_signature": "initialize(address)",
    },
}


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert (0x2dec9427 << 2) & 0xffffffff == int(ERROR, 16)
    rows = {}
    for role, spec in SPECS.items():
        address = spec["address"]
        runtime = manifest["contracts"][address]
        assert runtime["role"] == role
        code_hex = (ATLAS / runtime["runtime_file"]).read_text().strip()
        code = bytes.fromhex(code_hex.removeprefix("0x"))
        assert hashlib.sha256(code).hexdigest() == runtime["sha256"]
        dispatcher = bytes.fromhex("63" + spec["selector"][2:] + "1461" + f"{spec['body_pc']:04x}" + "57")
        assert code[spec["dispatcher_pc"]:spec["dispatcher_pc"] + len(dispatcher)] == dispatcher
        body = bytes.fromhex(spec["body_hex"])
        assert code[spec["body_pc"]:spec["body_pc"] + len(body)] == body
        assert body.endswith(bytes.fromhex("632dec942760e21b8152fd")) or body.endswith(
            bytes.fromhex("632dec942760e21b8152600490fd"))
        for pc, decoder_hex in zip(spec["decoder_pcs"], spec["decoder_hex"], strict=True):
            decoder = bytes.fromhex(decoder_hex)
            assert code[pc:pc + len(decoder)] == decoder
        decoded = json.loads(subprocess.run(
            ["cast", "disassemble", "--json", code_hex], capture_output=True, text=True, check=True).stdout)["data"]
        instructions = {int(line[:8], 16): line.split(": ", 1)[1] for line in decoded.splitlines()
                        if len(line) > 10 and line[8:10] == ": "}
        assert instructions[spec["dispatcher_pc"]] == f"PUSH4 {spec['selector']}"
        assert instructions[spec["body_pc"]] == "JUMPDEST"
        assert instructions[spec["body_pc"] + len(body) - 1] == "REVERT"
        spans = [(spec["body_pc"], spec["body_pc"] + len(body))]
        spans += [(pc, pc + len(bytes.fromhex(decoder_hex)))
                  for pc, decoder_hex in zip(spec["decoder_pcs"], spec["decoder_hex"], strict=True)]
        assert all(instructions[start] == "JUMPDEST" for start, _ in spans)
        assert not [instruction for pc, instruction in instructions.items()
                    if any(start <= pc < end for start, end in spans)
                    and instruction.split(" ", 1)[0] in EFFECTS]
        probe = json.loads((ATLAS / spec["linked_probe"]).read_text())
        assert probe["pin"] == manifest["block"]
        if role == "staking_implementation":
            assert ERROR in probe["selector_behaviors"][spec["selector"]]
        elif role == "batch_executor_implementation":
            assert spec["selector"] in probe["simulated_control_selectors"]
            assert any(error["selector"] == ERROR for error in probe["simulated_error_catalog"])
        else:
            assert probe["probes"]["legacy_initialize_current"]["revert_selector"] == ERROR
        rows[role] = {
            "address": address, "runtime_sha256": runtime["sha256"],
            "selector": spec["selector"], "candidate_signature": spec["candidate_signature"],
            "dispatcher_pc": spec["dispatcher_pc"],
            "body_byte_range": [spec["body_pc"], spec["body_pc"] + len(body)],
            "address_decoder_pcs": list(spec["decoder_pcs"]),
            "address_argument_count": len(spec["decoder_pcs"]),
            "linked_probe": spec["linked_probe"],
            "canonical_zero_value_result": ERROR,
            "behavior": "After nonpayable and canonical address decoding, the path has no storage reads, writes, external calls, events, or success exit; it reverts with four error bytes.",
        }
    result = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "error_selector": ERROR, "entries": rows,
        "error_construction": "PUSH4 0x2dec9427 shifted left 226 bits gives 0xb7b2509c as the first four revert bytes",
        "limits": ["Proof covers canonical zero-value calldata on the three exact pinned implementations.",
                   "Malformed calldata and nonzero value can reach generic empty-data revert branches.",
                   "Source function spellings and custom error name are not proved by this bytecode result."],
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("verified 3 fixed-revert legacy initializer entries in pinned bytecode")


if __name__ == "__main__":
    main()
