#!/usr/bin/env python3
"""Verify the two live Tokenomics redemption selectors are fixed reverts."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
RAW = ROOT / "artifacts" / "tokenomics" / "pinned_redemption_probes.json"
OUT = ATLAS / "tokenomics_redemption_stub_behavior.json"
PROXY = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
IMPLEMENTATION = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
ERROR = "0x32aa90b0"
SELECTORS = {"0xfe16eae8": {"signature": "quoteRedemption(uint256)", "entry": 0x106, "revert_pc": 0x123},
             "0xdb006a75": {"signature": "redeem(uint256)", "entry": 0x2a0, "revert_pc": 0x2be}}


def cast(*args):
    return subprocess.run(["cast", *args], capture_output=True, text=True, check=True).stdout.strip()


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    row = manifest["contracts"][IMPLEMENTATION]
    runtime_hex = (ATLAS / row["runtime_file"]).read_text().strip()
    runtime = bytes.fromhex(runtime_hex.removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == row["sha256"]
    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", runtime_hex],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1] for line in disassembly.splitlines()
                    if len(line) > 10 and line[8:10] == ": "}
    expected = {
        "0xfe16eae8": {0x106: "JUMPDEST", 0x107: "CALLVALUE", 0x10c: "PUSH1 0x20",
                       0x118: "MLOAD", 0x119: "PUSH4 0x032aa90b", 0x11e: "PUSH1 0xe4",
                       0x120: "SHL", 0x122: "MSTORE", 0x123: "REVERT"},
        "0xdb006a75": {0x2a0: "JUMPDEST", 0x2a2: "CALLVALUE", 0x2a7: "PUSH1 0x20",
                       0x2b3: "MLOAD", 0x2b4: "PUSH4 0x032aa90b", 0x2b9: "PUSH1 0xe4",
                       0x2bb: "SHL", 0x2bd: "MSTORE", 0x2be: "REVERT"},
    }
    regions = {"0xfe16eae8": (0x106, 0x124), "0xdb006a75": (0x2a0, 0x2bf)}
    for selector, info in SELECTORS.items():
        assert cast("sig", info["signature"]) == selector
        pattern = bytes.fromhex("63" + selector[2:] + "14" + f"61{info['entry']:04x}" + "57")
        assert pattern in runtime[:0x120]
        for pc, op in expected[selector].items():
            assert instructions[pc] == op, (selector, hex(pc), instructions[pc], op)
        lo, hi = regions[selector]
        assert not [instructions[pc] for pc in instructions if lo <= pc < hi
                    and instructions[pc] in ("SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4", "RETURN")]
    assert (0x032aa90b << 228).to_bytes(32, "big")[:4].hex() == ERROR[2:]
    raw = json.loads(RAW.read_text())
    assert raw["pin_block"] == manifest["block"] and raw["pin_hash"] == manifest["block_hash"]
    assert len(raw["probes"]) == 6
    counts = {selector: 0 for selector in SELECTORS}
    for probe in raw["probes"]:
        selector = probe["call"]["data"][:10]
        assert selector in SELECTORS and probe["call"]["to"].lower() == PROXY
        assert probe["trace"]["error"] == "execution reverted" and probe["trace"]["output"] == ERROR
        assert len(probe["trace"].get("calls", [])) == 1
        assert probe["trace"]["calls"][0]["to"].lower() == IMPLEMENTATION
        counts[selector] += 1
    assert counts == {selector: 3 for selector in SELECTORS}
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "tokenomics_proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": row["sha256"],
        "selector_reconstructions": {selector: info["signature"] for selector, info in SELECTORS.items()},
        "error_selector": ERROR, "error_name_status": "unresolved",
        "source_name_status": "hash-matching selector preimages; original Solidity names unverified",
        "selector_entries": {selector: {"entry_pc": info["entry"], "revert_pc": info["revert_pc"],
                                        "pinned_probe_count": counts[selector]}
                             for selector, info in SELECTORS.items()},
        "error_encoding": "PUSH4 0x032aa90b, shift left by 228 bits, store and revert with the first four bytes 0x32aa90b0",
        "behavior": "canonical nonpayable uint256 calls revert without storage reads, writes, logs, or external calls",
        "archived_probe_evidence": "../../artifacts/tokenomics/pinned_redemption_probes.json",
        "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json",
        "limits": ["The result applies to the pinned live implementation. No successful redemption path exists through these two entrypoints in that runtime.",
                   "The source name of error 0x32aa90b0 is unknown; an upgrade could change behavior."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified Tokenomics redemption fixed-revert paths")


if __name__ == "__main__":
    main()
