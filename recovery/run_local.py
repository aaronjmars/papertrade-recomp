"""Rebuild and replay the PT-01 recovery candidate against the live Exchange set."""

import argparse
import gzip
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
HERE = pathlib.Path(__file__).resolve().parent
ATLAS = ROOT / "atlas" / "block_48902346"
STALLED = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
REDRIVE = ROOT / "artifacts" / "recovery_redrive"
LIVE_FACTS = REDRIVE / "live_facts.json"
FIXTURE = REDRIVE / "live_words.json"
OUT = HERE / "replay.json"
COMPILED = HERE / "compiled.json"
SOURCES = ("Pt01Recovery.sol", "Pt01Recovery.t.sol")
OLD_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
LIVE_IMPLEMENTATION = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
ADDRESSES = {
    "Multisig": "0x696292762fd5ac3677a45edbe54eaece4194d1f6",
    "Timelock": "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
    "ExchangeProxy": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
    "ProxyAdmin": "0xe79c91cc682f1bb401a9cab74c900470190f0f8f",
}
EXPECTED_TESTS = {
    "testBothUsersThenRestoreOriginal",
    "testChangedBalanceCannotEnqueue",
    "testDelegatesToLiveImplementation",
    "testEnqueueFirst",
    "testEnqueueSecond",
    "testFallbackGetterParity",
    "testFirstDeliveredWithFee",
    "testFirstDeliveredWithoutFee",
    "testGovernedUpgradeAndRecovery",
    "testLiveAddedSelectorsLeaveRecoveryStateAlone",
    "testLiveDustBranchCannotClearWhileActive",
    "testLiveImplementationHasNoPendingSweepClearRoute",
    "testLiveImplementationIsTheDelegateTarget",
    "testLivePendingLayoutMatchesGetPendingSweep",
    "testLiveReconcileCreditsExactlyThePinnedDeltas",
    "testRejectedCoreSendCannotCredit",
    "testResidualCannotBeCreditedEarly",
    "testResidualWriterFailureRollsBack",
    "testSecondDeliveredWithFee",
    "testSecondDeliveredWithoutFee",
    "testSweeperBlockedWhileActive",
    "testUnauthorizedAndUnknownUser",
    "testWriterFailureRollsBack",
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def census():
    return json.loads(gzip.decompress(STALLED.read_bytes()))


def inputs():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    stalled = census()
    live = json.loads(LIVE_FACTS.read_text())
    assert manifest["block"] == stalled["pin"] == live["pinned"]["pin"] == 48_902_346
    assert manifest["block_hash"] == stalled["block_hash"] == live["pinned"]["pin_hash"]
    assert live["exchange"]["implementation"] == LIVE_IMPLEMENTATION
    assert live["exchange"]["implementation_word"].lower() == "0x" + LIVE_IMPLEMENTATION[2:].rjust(64, "0")
    cases = stalled["cases"]
    assert [(row["user"], row["proxy"]) for row in cases] == [
        (
            "0x56cbe78a5cdfa10147927aec550aa7f2fb3d3d01",
            "0x1e8a704179cc6221592c362daa52a341ae20084d",
        ),
        (
            "0x9c8599c32224d7d9956a7def18f7314162f77baf",
            "0xf6b60cdf359af5538495831a9f2bbcada23e10e6",
        ),
    ]
    runtime = {}
    for name, address in ADDRESSES.items():
        record = manifest["contracts"][address]
        code = (ATLAS / record["runtime_file"]).read_text().strip()
        assert sha256(bytes.fromhex(code[2:])) == record["sha256"]
        runtime[name] = code
    old = (ATLAS / manifest["contracts"][OLD_IMPLEMENTATION]["runtime_file"]).read_text().strip()
    assert sha256(bytes.fromhex(old[2:])) == manifest["contracts"][OLD_IMPLEMENTATION]["sha256"]
    runtime["OldImplementation"] = old
    live_code = (REDRIVE / live["exchange"]["implementation_runtime_file"]).read_text().strip()
    assert sha256(bytes.fromhex(live_code[2:])) == live["exchange"]["implementation_code_sha256"]
    assert live["exchange"]["implementation"] == LIVE_IMPLEMENTATION
    runtime["LiveImplementation"] = "0x" + live_code[2:]
    for index, row in enumerate(cases, 1):
        code = row["proxy_code"]
        assert sha256(bytes.fromhex(code[2:])) == row["derived_runtime_sha256"]
        runtime[f"UserProxy{index}"] = code
    return manifest, cases, runtime, live


def fixture(live, cases, stalled):
    """The `.t.sol` state file: live storage words, keyed exactly as the candidate assumes them."""
    exchange = live["exchange"]
    words = {"exchange": exchange["proxy"],
             "implementation": exchange["implementation"],
             "implementationSlot": exchange["implementation_slot"],
             "adminSlot": exchange["admin_slot"],
             "proxyAdmin": exchange["proxy_admin"],
             "activeSlot": exchange["recovery_active_slot"],
             "activeValue": exchange["recovery_active_value"],
             "timelock": live["governance"]["timelock"],
             "multisig": live["governance"]["multisig"],
             "timelockOwnerSlot0": live["governance"]["timelock_owner_slot"],
             "timelockMinDelay": live["governance"]["timelock_min_delay_word"],
             "adminOwnerSlot0": live["governance"]["proxy_admin_owner_slot"],
             "pinBlock": hex(live["pinned"]["pin"]),
             "pinTimestamp": stalled["pin_header"]["timestamp"]}
    for index in range(32):
        words[f"exchangeSlot{index}"] = exchange["singleton_slots"][str(index)]
    for index, signer in enumerate(live["governance"]["multisig_signer_slots"]):
        words[f"multisigSlot{index}"] = signer
    words["multisigSlot3"] = live["governance"]["multisig_epoch_word"]
    words["multisigSlot4"] = live["governance"]["multisig_transaction_count_word"]
    for index, row in enumerate(cases, 1):
        words[f"pendingSlotUser{index}"] = row["pending_storage_slot"]
        words[f"pendingWordUser{index}"] = row["pending_storage_word"]
        words[f"lastSweepSlotUser{index}"] = row["last_sweep_block_storage_slot"]
        words[f"lastSweepWordUser{index}"] = row["last_sweep_block_storage_word"]
        words[f"balanceSlotUser{index}"] = row["balance_storage_slot"]
        words[f"balanceWordUser{index}"] = row["balance_storage_word"]
    added = live["dispatcher"]["added_selectors"]
    words["addedSelectorCount"] = hex(len(added))
    for index, selector in enumerate(added):
        words[f"addedSelector{index}"] = "0x" + selector + "00" * 28
    return words


def fixture_keys_used(added_selectors):
    """Every fixture key the `.t.sol` reads, so the two cannot drift apart."""
    source = (HERE / "Pt01Recovery.t.sol").read_text()
    used = set()
    for argument in re.findall(r"\bw\((.*?)\)", source):
        for prefix in re.findall(r'string\.concat\("([A-Za-z]+)"', argument):
            if prefix == "exchangeSlot":
                used |= {f"{prefix}{index}" for index in range(32)}
            elif prefix == "multisigSlot":
                used |= {f"{prefix}{index}" for index in range(5)}
            elif prefix == "addedSelector":
                used.add("addedSelectorCount")
                used |= {f"{prefix}{index}" for index in range(added_selectors)}
            else:
                used |= {f"{prefix}1", f"{prefix}2"}
            argument = argument.replace(f'string.concat("{prefix}"', "")
        used |= set(re.findall(r'"([A-Za-z0-9]+)"', argument))
    return used


def source_hashes():
    return {name: sha256((HERE / name).read_bytes()) for name in SOURCES}


def run():
    manifest, cases, runtime, live = inputs()
    solc = shutil.which("solc")
    forge = shutil.which("forge")
    assert solc and forge, "local solc and forge are required"
    words = fixture(live, live["cases"], census())
    with tempfile.TemporaryDirectory(prefix="papertrade-pt01-rescue-") as temp:
        project = pathlib.Path(temp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        for name in SOURCES:
            shutil.copy2(HERE / name, project / "test" / name)
        for name, code in runtime.items():
            (project / "runtime" / f"{name}.hex").write_text(code)
        (project / "runtime" / "live_words.json").write_text(json.dumps(words, indent=2, sort_keys=True) + "\n")
        (project / "foundry.toml").write_text(
            "[profile.default]\n"
            + "solc = " + json.dumps(solc) + "\n"
            + 'evm_version = "cancun"\n'
            + "offline = true\n"
            + 'fs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        result = subprocess.run(
            [forge, "test", "--root", temp, "-vv"],
            capture_output=True,
            check=False,
            text=True,
            timeout=180,
        )
        output = result.stdout + "\n" + result.stderr
        passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
        if result.returncode or passed != EXPECTED_TESTS:
            raise RuntimeError("PT-01 rescue replay failed: " + output[-8000:])
        artifact = json.loads(
            (project / "out" / "Pt01Recovery.sol" / "Pt01Recovery.json").read_text()
        )

    metadata = artifact["metadata"]
    assert metadata["compiler"]["version"] == "0.8.28+commit.7893614a"
    assert metadata["settings"]["evmVersion"] == "cancun"
    assert metadata["settings"]["optimizer"]["enabled"] is False
    init_code = artifact["bytecode"]["object"]
    deployed_code = artifact["deployedBytecode"]["object"]
    assert init_code.startswith("0x") and deployed_code.startswith("0x")
    compiled = {
        "compiler": metadata["compiler"]["version"],
        "evm_version": metadata["settings"]["evmVersion"],
        "optimizer": metadata["settings"]["optimizer"],
        "source_hashes": source_hashes(),
        "init_code": init_code,
        "deployed_code": deployed_code,
        "init_code_sha256": sha256(bytes.fromhex(init_code[2:])),
        "deployed_code_sha256": sha256(bytes.fromhex(deployed_code[2:])),
        "abi": artifact["abi"],
    }
    saved = {
        "pin": manifest["block"],
        "pin_hash": manifest["block_hash"],
        "live_facts": str(LIVE_FACTS.relative_to(ROOT)),
        "live_head": live["head"]["number"],
        "live_implementation": LIVE_IMPLEMENTATION,
        "live_implementation_code_sha256": live["exchange"]["implementation_code_sha256"],
        "source_hashes": source_hashes(),
        "input_runtime_sha256": {
            name: sha256(bytes.fromhex(code[2:])) for name, code in runtime.items()
        },
        "users": [row["user"] for row in cases],
        "proxies": [row["proxy"] for row in cases],
        "requested_raw_spot": [5_005_091_600, 1_210_000_000],
        "first_send_raw_spot": [4_905_091_600, 1_110_000_000],
        "possible_residual_send_raw_spot": 100_000_000,
        "added_selectors": live["dispatcher"]["added_selectors"],
        "test_names": sorted(passed),
        "forge_result": f"{len(passed)} passed, 0 failed",
        "compiled_code_sha256": compiled["deployed_code_sha256"],
        "limits": [
            "The Core-balance precompile and CoreWriter execution are mocked in local tests.",
            "No Core acceptance, exact fee predicate, real delivery, or mainnet upgrade is demonstrated.",
            "Only sampled fallback parity is tested; this code requires independent review before any deployment.",
            "The owner must verify Core execution and both ledgers before finalization.",
        ],
    }
    REDRIVE.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps(words, indent=2, sort_keys=True) + "\n")
    COMPILED.write_text(json.dumps(compiled, indent=2, sort_keys=True) + "\n")
    OUT.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n")
    return verify()


def verify():
    manifest, cases, runtime, live = inputs()
    saved = json.loads(OUT.read_text())
    compiled = json.loads(COMPILED.read_text())
    assert saved["pin"] == manifest["block"]
    assert saved["pin_hash"] == manifest["block_hash"]
    assert saved["live_facts"] == str(LIVE_FACTS.relative_to(ROOT))
    assert saved["live_head"] == live["head"]["number"]
    assert saved["live_implementation"] == live["exchange"]["implementation"] == LIVE_IMPLEMENTATION
    assert saved["live_implementation_code_sha256"] == live["exchange"]["implementation_code_sha256"]
    assert saved["source_hashes"] == compiled["source_hashes"] == source_hashes()
    assert saved["input_runtime_sha256"] == {
        name: sha256(bytes.fromhex(code[2:])) for name, code in runtime.items()
    }
    assert saved["input_runtime_sha256"]["LiveImplementation"] == saved["live_implementation_code_sha256"]
    assert saved["users"] == [row["user"] for row in cases]
    assert saved["proxies"] == [row["proxy"] for row in cases]
    assert saved["requested_raw_spot"] == [5_005_091_600, 1_210_000_000]
    assert saved["first_send_raw_spot"] == [4_905_091_600, 1_110_000_000]
    assert saved["possible_residual_send_raw_spot"] == 100_000_000
    assert saved["added_selectors"] == live["dispatcher"]["added_selectors"]
    assert len(saved["added_selectors"]) == 6
    assert set(saved["test_names"]) == EXPECTED_TESTS
    assert saved["forge_result"] == f"{len(EXPECTED_TESTS)} passed, 0 failed"
    assert compiled["compiler"] == "0.8.28+commit.7893614a"
    assert compiled["evm_version"] == "cancun"
    assert compiled["optimizer"]["enabled"] is False
    assert compiled["init_code"].startswith("0x")
    assert compiled["deployed_code"].startswith("0x")
    assert compiled["init_code_sha256"] == sha256(bytes.fromhex(compiled["init_code"][2:]))
    assert compiled["deployed_code_sha256"] == sha256(bytes.fromhex(compiled["deployed_code"][2:]))
    assert saved["compiled_code_sha256"] == compiled["deployed_code_sha256"]
    assert len(compiled["abi"]) >= 6
    words = fixture(live, live["cases"], census())
    assert json.loads(FIXTURE.read_text()) == words
    assert fixture_keys_used(len(saved["added_selectors"])) == set(words)

    # the candidate must embed the live implementation and never the retired one
    deployed = bytes.fromhex(compiled["deployed_code"][2:])
    assert bytes.fromhex(LIVE_IMPLEMENTATION[2:]) in deployed
    assert bytes.fromhex(OLD_IMPLEMENTATION[2:]) not in deployed
    assert bytes.fromhex(LIVE_IMPLEMENTATION[2:]) in bytes.fromhex(compiled["init_code"][2:])
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="rebuild with local solc and Forge")
    args = parser.parse_args()
    result = run() if args.run else verify()
    print(json.dumps({key: result[key] for key in
                      ("pin", "live_implementation", "forge_result", "compiled_code_sha256")}, indent=2))