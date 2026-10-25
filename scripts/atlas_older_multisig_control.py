#!/usr/bin/env python3
"""Capture and replay the pinned signer-change path of both older multisigs."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_deployer_scope import call, rpc_batch
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
GOVERNANCE = ROOT / "artifacts" / "deployer_scope" / "older_governance.json.gz"
SOURCE = ROOT / "artifacts" / "deployer_scope" / "older_multisig_control.t.sol"
SLOTS = ROOT / "artifacts" / "deployer_scope" / "older_multisig_slots.json"
REPLAY = ROOT / "artifacts" / "deployer_scope" / "older_multisig_control_replay.json"
MULTISIG_INDICES = (17, 36)
TEST_NAMES = {
    "testFirstOlderMultisigOneSignerSelfUpdate",
    "testSecondOlderMultisigOneSignerSelfUpdate",
}
SIGNATURES = {
    "submitTransaction(address,uint256,bytes,bool)": "0x684dbac7",
    "updateSigners(address,address)": "0xde43590d",
    "transactionCount()": "0xb77bf600",
}


def inputs():
    scope = json.loads(gzip.decompress(SCOPE.read_bytes()))
    governance = json.loads(gzip.decompress(GOVERNANCE.read_bytes()))
    assert scope["pin"] == governance["pin"] == 48_902_346
    assert scope["block_hash"] == governance["block_hash"]
    rows = [scope["rows"][index] for index in MULTISIG_INDICES]
    assert [row["address"] for row in rows] == [
        "0x73a83d746c38865960583879bc29bb007a04eacf",
        "0x324b0547039683c2df146421f3a76083ef130d27",
    ]
    runtimes = [bytes.fromhex(row["runtime"][2:]) for row in rows]
    assert runtimes[0] == runtimes[1]
    runtime_sha256 = hashlib.sha256(runtimes[0]).hexdigest()
    assert runtime_sha256 == "4c8ecb8092028b3931dc3b8e2852278aa7f81ea0e8e4a418a4e0490d84e87bde"
    assert len(runtimes[0]) == 2713
    keccak = Keccak()
    for signature, selector in SIGNATURES.items():
        assert "0x" + keccak(signature.encode())[:4].hex() == selector
        assert bytes.fromhex(selector[2:]) in runtimes[0]
    return scope, governance, rows, runtime_sha256


def expected_slots(governance, index):
    values = governance["older_getters"][index]["values"]
    assert governance["older_getters"][index]["base"] == (0, 19)[index]
    assert int(values["multisig_required_confirmations"], 16) == 1
    return [
        values["multisig_signer_one"],
        values["multisig_signer_two"],
        values["multisig_transaction_count"],
    ]


def capture():
    scope, governance, rows, _ = inputs()
    queries = [
        call("eth_getStorageAt", [row["address"], hex(slot), hex(scope["pin"])], index * 3 + slot)
        for index, row in enumerate(rows)
        for slot in range(3)
    ]
    results = rpc_batch(os.environ["PAPERTRADE_ARCHIVE_RPC"], queries)
    entries = []
    for index, row in enumerate(rows):
        slots = [results[index * 3 + slot].lower() for slot in range(3)]
        assert slots == expected_slots(governance, index)
        entries.append({"address": row["address"], "slots_0_to_2": slots})
    SLOTS.write_text(json.dumps({
        "pin": scope["pin"],
        "block_hash": scope["block_hash"],
        "entries": entries,
    }, indent=2) + "\n")
    return verify_slots()


def verify_slots():
    scope, governance, rows, _ = inputs()
    saved = json.loads(SLOTS.read_text())
    assert saved["pin"] == scope["pin"]
    assert saved["block_hash"] == scope["block_hash"]
    assert [entry["address"] for entry in saved["entries"]] == [row["address"] for row in rows]
    for index, entry in enumerate(saved["entries"]):
        assert entry["slots_0_to_2"] == expected_slots(governance, index)
    return saved


def run():
    scope, _, rows, runtime_sha256 = inputs()
    slots = verify_slots()
    solc = shutil.which("solc")
    assert solc, "local solc is required"
    with tempfile.TemporaryDirectory(prefix="papertrade-older-multisig-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        shutil.copyfile(SOURCE, project / "test" / "OldMultisig.t.sol")
        (project / "runtime" / "Multisig.hex").write_text(rows[0]["runtime"])
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True, check=False, text=True, timeout=60,
        )
    output = result.stdout + "\n" + result.stderr
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    if result.returncode or passed != TEST_NAMES:
        raise RuntimeError("older multisig replay failed: " + output[-5000:])
    REPLAY.write_text(json.dumps({
        "pin": scope["pin"],
        "block_hash": scope["block_hash"],
        "addresses": [row["address"] for row in rows],
        "runtime_sha256": runtime_sha256,
        "slots_0_to_2": [entry["slots_0_to_2"] for entry in slots["entries"]],
        "test_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "test_names": sorted(passed),
        "forge_result": "2 passed, 0 failed",
        "limits": [
            "Exact pinned runtime and direct slots 0-2 are seeded locally; other state is not reproduced.",
            "The replay tests a constructed signer update, not a historical takeover.",
            "Signer changes bypass the timelock, while later governed target actions still use it.",
        ],
    }, indent=2) + "\n")
    return verify()


def verify():
    scope, _, rows, runtime_sha256 = inputs()
    slots = verify_slots()
    saved = json.loads(REPLAY.read_text())
    assert saved["pin"] == scope["pin"]
    assert saved["block_hash"] == scope["block_hash"]
    assert saved["addresses"] == [row["address"] for row in rows]
    assert saved["runtime_sha256"] == runtime_sha256
    assert saved["slots_0_to_2"] == [entry["slots_0_to_2"] for entry in slots["entries"]]
    assert saved["test_source_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert set(saved["test_names"]) == TEST_NAMES
    assert saved["forge_result"] == "2 passed, 0 failed"
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="capture pinned raw slots")
    parser.add_argument("--run", action="store_true", help="replay pinned runtime locally")
    args = parser.parse_args()
    if args.capture:
        result = capture()
    elif args.run:
        result = run()
    else:
        result = verify()
    print(json.dumps({key: result[key] for key in ("pin", "block_hash")}, indent=2))


if __name__ == "__main__":
    main()
