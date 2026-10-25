#!/usr/bin/env python3
"""Verify the saved Tokenomics ownership transfer against packed storage and log."""

import json
from pathlib import Path

from atlas_factory_events import Keccak


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "historical"
OUT = ATLAS / "tokenomics_owner_transfer_behavior.json"
PROXY = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
IMPLEMENTATION = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
TX = "0x507fde69627d8ac0a1eabbb5024c226076406bf2866d4d4f9a9f474eb6403f7f"
SELECTOR = "0xf2fde38b"
SIGNATURE = "transferOwnership(address)"
EVENT = "OwnerUpdated(address)"
ADDRESS_MASK = (1 << 160) - 1


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == 48902346
    assert manifest["contracts"][PROXY]["role"] == "tokenomics_proxy"
    assert manifest["contracts"][IMPLEMENTATION]["role"] == "tokenomics_implementation"
    keccak = Keccak()
    assert "0x" + keccak(SIGNATURE.encode())[:4].hex() == SELECTOR
    topic = "0x" + keccak(EVENT.encode()).hex()
    call = json.loads((ARTIFACTS / f"{TX}.calls.json").read_text())
    receipt = json.loads((ARTIFACTS / f"{TX}.receipt.json").read_text())
    diff = json.loads((ARTIFACTS / f"{TX}.state_diff.json").read_text())
    assert call["to"].lower() == PROXY and call["input"].startswith(SELECTOR)
    assert len(call["input"]) == 74 and not call.get("error") and receipt["status"] == "0x1"
    new_owner = int(call["input"][10:], 16)
    assert new_owner < (1 << 160)
    slot = "0x" + "0" * 64
    before = int(diff["pre"][PROXY]["storage"][slot], 16)
    after = int(diff["post"][PROXY]["storage"][slot], 16)
    old_owner = (before >> 16) & ADDRESS_MASK
    assert old_owner == int(call["from"], 16)
    assert (after >> 16) & ADDRESS_MASK == new_owner
    assert (before & 0xffff) == (after & 0xffff) == 1
    assert before >> 176 == after >> 176
    logs = [log for log in receipt["logs"] if log["address"].lower() == PROXY]
    assert len(logs) == 1
    assert logs[0]["topics"] == [topic, f"0x{new_owner:064x}"] and logs[0]["data"] == "0x"
    storage = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
    owner_getter = next(row for row in storage[IMPLEMENTATION]["views"]
                        if row["selector"] == "0x8da5cb5b")
    assert int(owner_getter["return_prefix"], 16) == new_owner
    assert owner_getter["direct_slots"] == [0]
    return {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "tokenomics_proxy": PROXY, "implementation": IMPLEMENTATION,
        "selector_reconstructions": {SELECTOR: SIGNATURE},
        "event_catalog": [{"topic0": topic, "reconstructed_signature": EVENT}],
        "historical_tx": TX, "old_owner": f"0x{old_owner:040x}",
        "new_owner": f"0x{new_owner:040x}",
        "storage_slot": 0, "owner_bit_offset": 16,
        "initialized_flag_low16_unchanged": True,
        "pinned_owner_getter_matches": True,
        "limits": [
            "One successful historical owner call is checked; outsider and zero-address branches remain untested here.",
            "The event's indexed address and packed storage are exact for this transaction.",
        ],
    }


if __name__ == "__main__":
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("Tokenomics owner transfer: packed slot, event, and pinned getter matched")
