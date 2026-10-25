#!/usr/bin/env python3
"""Check SessionKeyManager's initializer name and version constraints in pinned code."""

import hashlib
import json
from pathlib import Path

from atlas_factory_events import Keccak

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "session_initializer_constants_behavior.json"
IMPLEMENTATION = "0x8a5069fe303e8f81e91825436e956d595032e558"
PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SELECTOR = "0x747b8a1c"
ERROR = "0xf50220aa"
NAME_OFFSET = 0xe5f
VERSION_OFFSET = 0xdff

# The two CODECOPY sequences load 32-byte constants from the runtime's data table.
# Each sequence is followed by a KECCAK256 comparison and a mismatch jump.
COMPARISON_HEX = (
    "5f80516020610e5f8339815191529060ff8a60081c1615998a610710575b50602081519101200361070257"
    "8060205f80516020610dff8339815191529251910120036106f557"
)
MISMATCH_HEX = "5b51637a81105560e11b8152fd5b5051637a81105560e11b8152fd"


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    row = manifest["contracts"][IMPLEMENTATION]
    assert row["role"] == "session_key_manager_implementation"
    code_hex = (ATLAS / row["runtime_file"]).read_text().strip()
    code = bytes.fromhex(code_hex.removeprefix("0x"))
    assert hashlib.sha256(code).hexdigest() == row["sha256"]
    keccak = Keccak()
    assert code[0xdde] == 0xfe  # INVALID separates executable code from the constant table.
    expected_name_hash = keccak(b"String")
    expected_version_hash = keccak(b"1")
    assert code[NAME_OFFSET:NAME_OFFSET + 32] == expected_name_hash
    assert code[VERSION_OFFSET:VERSION_OFFSET + 32] == expected_version_hash
    comparison = bytes.fromhex(COMPARISON_HEX)
    mismatch = bytes.fromhex(MISMATCH_HEX)
    assert code[0x64f:0x64f + len(comparison)] == comparison
    assert code[0x6f5:0x6f5 + len(mismatch)] == mismatch
    assert (0x7a811055 << 1) & 0xffffffff == int(ERROR, 16)

    initializer = json.loads((ATLAS / "session_initializer_behavior.json").read_text())
    assert initializer["implementation"] == IMPLEMENTATION
    assert initializer["selector_reconstructions"][SELECTOR] == "initialize(address,string,string,uint256,address)"
    historical = initializer["historical_creation"]
    assert historical["decoded_arguments"]["name"] == "String"
    assert historical["decoded_arguments"]["version"] == "1"
    assert historical["decoded_arguments"]["chain_id"] == 999
    assert historical["decoded_arguments"]["authorized_caller"] == "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
    assert any(error["selector"] == ERROR for error in initializer["simulated_error_catalog"])
    replay = json.loads((ATLAS / initializer["local_replay"]).read_text())
    assert replay["block_hash"] == manifest["block_hash"]
    assert "testProbeSessionCreationCalldata" in replay["test_names"]
    assert "testProbeSessionInitVariants" in replay["test_names"]

    result = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": row["sha256"], "selector": SELECTOR,
        "selector_reconstructions": {SELECTOR: "initialize(address,string,string,uint256,address)"},
        "name": "String", "name_hash": "0x" + expected_name_hash.hex(),
        "name_hash_runtime_offset": NAME_OFFSET,
        "version": "1", "version_hash": "0x" + expected_version_hash.hex(),
        "version_hash_runtime_offset": VERSION_OFFSET,
        "comparison_byte_range": [0x64f, 0x64f + len(comparison)],
        "name_mismatch_jump_pc": 0x702, "version_mismatch_jump_pc": 0x6f5,
        "mismatch_body_byte_range": [0x6f5, 0x6f5 + len(mismatch)],
        "mismatch_error_selector": ERROR,
        "historical_success_evidence": historical,
        "local_replay": initializer["local_replay"],
        "observed_behavior": "Fresh-state initializer hashes the supplied name and version bytes and compares them to hardcoded keccak256(String) and keccak256(1); a mismatch reverts with 0xf50220aa.",
        "limits": ["The input constraint is proved for the fresh-state path at the pinned runtime; initialized-state calls can revert earlier.",
                   "Keccak equality gives a unique practical preimage but is not a formal proof that no hash collision exists.",
                   "The selector hash, deployment calldata, and exact runtime support the reconstructed signature; original source is unavailable."],
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("verified SessionKeyManager initializer name and version constants")


if __name__ == "__main__":
    main()
