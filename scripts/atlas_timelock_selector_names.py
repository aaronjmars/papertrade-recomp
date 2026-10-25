#!/usr/bin/env python3
"""Attach hash-checked names to the pinned Timelock behavior reconstruction."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "timelock_selector_names_behavior.json"
ADDRESS = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
SIGNATURES = {
    "0x04d2cd0e": "hashOperationBatch(address[],uint256[],bytes[],bytes32)",
    "0x13bc9f20": "isOperationReady(bytes32)",
    "0x2ab0f529": "isOperationDone(bytes32)",
    "0x584b153e": "isOperationPending(bytes32)",
    "0x6cb6a1f7": "operationTimestamps(bytes32)",
    "0x88aa4c12": "execute(address,uint256,bytes,bytes32)",
    "0x8a99d586": "updateMinDelay(uint256)",
    "0x8b07f62b": "scheduleBatch(address[],uint256[],bytes[],bytes32)",
    "0x8da5cb5b": "owner()",
    "0xa6cc2c8c": "executeBatch(address[],uint256[],bytes[],bytes32)",
    "0xb0e58bc9": "schedule(address,uint256,bytes,bytes32)",
    "0xc4d252f5": "cancel(bytes32)",
    "0xc63c4e9b": "minDelay()",
    "0xec2a5b45": "hashOperation(address,uint256,bytes,bytes32)",
    "0xf2fde38b": "transferOwnership(address)",
}


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    row = manifest["contracts"][ADDRESS]
    assert row["role"] == "timelock"
    raw = (ATLAS / row["runtime_file"]).read_text().strip()
    runtime = bytes.fromhex(raw.removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == row["sha256"]
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[ADDRESS]["functions"]
    assert {fn["selector"] for fn in catalog} == set(SIGNATURES)
    for selector, signature in SIGNATURES.items():
        actual = subprocess.run(["cast", "sig", signature], capture_output=True, text=True, check=True).stdout.strip()
        assert actual == selector, (selector, signature, actual)
        assert bytes.fromhex("63" + selector[2:]) in runtime, selector
        fn = next(fn for fn in catalog if fn["selector"] == selector)
        candidates = fn["candidate_signature"].split("|")
        assert signature in candidates, (selector, signature, candidates)
    behavior = json.loads((ATLAS / "timelock_behavior.json").read_text())
    assert behavior["pin"] == manifest["block"] and behavior["timelock"] == ADDRESS
    assert len(behavior["scheduled_operations"]) == 2
    assert behavior["batch_probe"] and behavior["update_min_delay_probe"]
    assert behavior["transfer_ownership_probe"] and behavior["status_getter_boundary_probes"]
    doc = (ATLAS / "timelock_pseudocode.md").read_text()
    for signature in SIGNATURES.values():
        assert signature.split("(", 1)[0] in doc
    OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "timelock": ADDRESS, "runtime_sha256": row["sha256"],
        "selector_reconstructions": SIGNATURES,
        "signature_status": "hash and observed behavior match; original source names unverified",
        "behavior_evidence": "timelock_behavior.json",
        "pseudocode_evidence": "timelock_pseudocode.md",
        "limits": ["Signature hashes and behavior do not prove the original Solidity identifiers.",
                   "Timelock batch operations were tested in read-only simulations, not seen as on-chain executions."],
    }, indent=2) + "\n")
    print("verified 15 Timelock selector signatures against pinned runtime")


if __name__ == "__main__":
    main()
