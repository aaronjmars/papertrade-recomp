#!/usr/bin/env python3
"""Verify SessionKeyManager's three pinned typehash constant getters."""

import json
from pathlib import Path

from atlas_factory_events import Keccak


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "session_typehash_behavior.json"
IMPLEMENTATION = "0x8a5069fe303e8f81e91825436e956d595032e558"
PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
EIP1967_IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
KNOWN = {
    "0x0b4c3a82": ("WITHDRAW_TO_CORE_TYPEHASH()",
                   "WithdrawToCore(address user,uint256 amount,uint256 nonce,uint64 deadline)"),
    "0x208e24fc": ("CLOSE_TYPEHASH()",
                   "Close(address user,uint256[] positionIds,uint256 nonce,uint64 deadline)"),
    "0x6525a680": ("OPEN_POSITION_TYPEHASH()",
                   "OpenPosition(address user,uint32 instrumentId,bool isLong,uint128 size,uint32 leverage,bool useDebt,uint256 nonce,uint64 deadline)"),
}


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    storage = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
    assert manifest["block"] == 48902346
    runtime = (ATLAS / manifest["contracts"][IMPLEMENTATION]["runtime_file"]).read_text().strip()
    code = bytes.fromhex(runtime[2:])
    views = {row["selector"]: row for row in storage[IMPLEMENTATION]["views"]}
    keccak = Keccak()
    constants = {}
    names = {}
    for selector, (candidate_name, preimage) in KNOWN.items():
        row = views[selector]
        assert row["target"] == PROXY and not row["failed"] and row["arguments"] == ""
        assert row["sloads"] == [{"slot": EIP1967_IMPLEMENTATION_SLOT, "pc": 781, "depth": 1}]
        result = row["return_prefix"]
        assert len(result) == 66
        literal = bytes.fromhex(result[2:])
        marker = b"\x7f" + literal
        assert code.count(marker) == 1
        offset = code.index(marker)
        # The bytecode stores the PUSH32 literal into memory and returns it.
        assert b"\x52\xf3" in code[offset + 33:offset + 45]
        assert "0x" + keccak(candidate_name.encode())[:4].hex() == selector
        if preimage is not None:
            assert "0x" + keccak(preimage.encode()).hex() == result
            names[selector] = candidate_name
        constants[selector] = {
            "pinned_return": result,
            "runtime_push32_offset": offset,
            "candidate_signature": candidate_name,
            "verified_type_string": preimage,
            "name_status": "hash_checked_type_string" if preimage is not None else "candidate_only",
        }
    return {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "session_proxy": PROXY, "implementation": IMPLEMENTATION,
        "selector_reconstructions": names, "constant_getters": constants,
        "open_position_type_source": "https://github.com/nirholas/papertrade-sdk/blob/483a760ef596564e5ad799357a92e5726dada9ba/src/typed-data.ts",
        "limits": [
            "The independent SDK supplied the open-position field names; the exact type string was then checked against the pinned on-chain constant.",
            "A hash-checked type string supports a reconstructed getter name; original contract source is unavailable.",
        ],
    }


if __name__ == "__main__":
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Session typehashes: {len(result['constant_getters'])} constants, "
          f"{len(result['selector_reconstructions'])} type strings matched")
