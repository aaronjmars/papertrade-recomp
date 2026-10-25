#!/usr/bin/env python3
"""Replay the pinned governance path that could authorize an Exchange upgrade."""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

import audit_stalled_sweeps as stalled

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "pt01_governance_replay" / "replay.json"
ADDRESSES = {
    "Multisig": "0x696292762fd5ac3677a45edbe54eaece4194d1f6",
    "Timelock": "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
    "ProxyAdmin": "0xe79c91cc682f1bb401a9cab74c900470190f0f8f",
    "ExchangeProxy": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
    "ExchangeImplementation": "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee",
}
TEST_NAMES = {
    "testTwoSignersAndSevenDayDelay",
    "testScheduledDelayReductionThenUpgrade",
}
TEST_SOURCE = """pragma solidity ^0.8.24;
interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function warp(uint256) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract MockUpgradeTarget {
    function marker() external pure returns (uint256) { return 42; }
}
contract Pt01GovernanceTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant MULTISIG = address(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)));
    address constant TIMELOCK = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant ORIGINAL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant SIGNER1 = address(uint160(uint256(0x00aa7577a7a27aa7fcf6d0ec481b87df3ad0f6a88e)));
    address constant SIGNER2 = address(uint160(uint256(0x00e9686c8e11d80c8d78736485fcb6b6d7f4d7692e)));
    address constant SIGNER3 = address(uint160(uint256(0x009028f3b5b6b0d69e4e84ff555ade17114c3d1e72)));
    address constant USER1 = address(uint160(uint256(0x0056cbe78a5cdfa10147927aec550aa7f2fb3d3d01)));
    address constant USER2 = address(uint160(uint256(0x009c8599c32224d7d9956a7def18f7314162f77baf)));
    bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    uint256 constant DELAY = 604800;
    uint256 constant PIN_TIME = 1_792_357_341;
    uint256 constant DELAY_CHANGE_READY = 1_792_447_296;
    bytes32 constant DELAY_CHANGE_ID = 0xc616b8d5f1fccaae8952fd5832306ef7d181cdbf7b3e81fa331593abc6d6a6cb;
    bytes32 constant DELAY_CHANGE_PREDECESSOR = 0x4f6334bb72dc6434598f27bdd8a884e83553a871b874434dba529b894e0b1bc3;
    uint256 constant PENDING1 = 5_005_091_600 | (uint256(48_209_855) << 128);
    uint256 constant PENDING2 = 1_210_000_000 | (uint256(48_091_494) << 128);

    function setUp() public {
        vm.etch(MULTISIG, vm.parseBytes(vm.readFile("runtime/Multisig.hex")));
        vm.etch(TIMELOCK, vm.parseBytes(vm.readFile("runtime/Timelock.hex")));
        vm.etch(ADMIN, vm.parseBytes(vm.readFile("runtime/ProxyAdmin.hex")));
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(ORIGINAL, vm.parseBytes(vm.readFile("runtime/ExchangeImplementation.hex")));
        vm.store(MULTISIG, bytes32(0), bytes32(uint256(uint160(SIGNER1))));
        vm.store(MULTISIG, bytes32(uint256(1)), bytes32(uint256(uint160(SIGNER2))));
        vm.store(MULTISIG, bytes32(uint256(2)), bytes32(uint256(uint160(SIGNER3))));
        vm.store(MULTISIG, bytes32(uint256(3)), bytes32(uint256(1)));
        vm.store(MULTISIG, bytes32(uint256(4)), bytes32(uint256(7)));
        vm.store(TIMELOCK, bytes32(0), bytes32(uint256(uint160(MULTISIG))));
        vm.store(TIMELOCK, bytes32(uint256(1)), bytes32(DELAY));
        vm.store(TIMELOCK, keccak256(abi.encode(DELAY_CHANGE_ID, uint256(2))), bytes32(DELAY_CHANGE_READY));
        vm.store(ADMIN, bytes32(0), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(ORIGINAL))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(EXCHANGE, keccak256(abi.encode(USER1, uint256(33))), bytes32(PENDING1));
        vm.store(EXCHANGE, keccak256(abi.encode(USER2, uint256(33))), bytes32(PENDING2));
        vm.warp(PIN_TIME);
    }

    function submit(address signer, bytes memory data) internal returns (uint256 index) {
        vm.prank(signer);
        (bool ok, bytes memory out) = MULTISIG.call(
            abi.encodeWithSignature("submitTransaction(address,uint256,bytes)", TIMELOCK, 0, data)
        );
        require(ok && out.length == 32, "multisig submit");
        index = abi.decode(out, (uint256));
    }

    function confirm(address signer, uint256 index) internal returns (bool ok) {
        (bool hashOk, bytes memory out) = MULTISIG.staticcall(
            abi.encodeWithSignature("transactionHash(uint256)", index)
        );
        require(hashOk && out.length == 32, "transaction hash");
        vm.prank(signer);
        (ok,) = MULTISIG.call(
            abi.encodeWithSignature("confirmAndExecute(uint256,bytes32)", index, abi.decode(out, (bytes32)))
        );
    }

    function testTwoSignersAndSevenDayDelay() public {
        MockUpgradeTarget target = new MockUpgradeTarget();
        bytes memory upgradeData = abi.encodeWithSignature("upgrade(address,address)", EXCHANGE, address(target));
        bytes memory scheduleData = abi.encodeWithSignature(
            "schedule(address,uint256,bytes,bytes32)", ADMIN, 0, upgradeData, bytes32(0)
        );
        vm.prank(SIGNER1);
        (bool ok,) = TIMELOCK.call(scheduleData);
        require(!ok, "direct signer schedule succeeded");
        vm.prank(SIGNER1);
        (ok,) = ADMIN.call(upgradeData);
        require(!ok, "direct signer upgrade succeeded");
        uint256 scheduleIndex = submit(SIGNER1, scheduleData);
        require(scheduleIndex == 7, "pinned transaction count");
        require(!confirm(SIGNER1, scheduleIndex), "submitter self-confirmed");
        require(confirm(SIGNER2, scheduleIndex), "second signer schedule failed");

        bytes32 id = keccak256(abi.encode(ADMIN, uint256(0), keccak256(upgradeData), bytes32(0)));
        bytes32 operationSlot = keccak256(abi.encode(id, uint256(2)));
        uint256 ready = uint256(vm.load(TIMELOCK, operationSlot));
        require(ready == PIN_TIME + DELAY, "seven-day ready time");
        bytes memory executeData = abi.encodeWithSignature(
            "execute(address,uint256,bytes,bytes32)", ADMIN, 0, upgradeData, bytes32(0)
        );
        uint256 executeIndex = submit(SIGNER1, executeData);
        require(executeIndex == 8, "execute transaction index");
        vm.warp(ready - 1);
        require(!confirm(SIGNER2, executeIndex), "early execution succeeded");
        require(vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(ORIGINAL))), "early upgrade");
        require(uint256(vm.load(TIMELOCK, operationSlot)) == ready, "early execution consumed operation");
        vm.warp(ready);
        require(confirm(SIGNER2, executeIndex), "ready execution failed");
        require(vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(address(target)))), "upgrade target");
        require(uint256(vm.load(TIMELOCK, operationSlot)) == 1, "operation not done");
        require(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER1, uint256(33))))) == PENDING1, "first pending changed");
        require(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER2, uint256(33))))) == PENDING2, "second pending changed");
        (bool markerOk, bytes memory out) = EXCHANGE.staticcall(abi.encodeWithSignature("marker()"));
        require(markerOk && abi.decode(out, (uint256)) == 42, "proxy not using target");
    }

    function testScheduledDelayReductionThenUpgrade() public {
        MockUpgradeTarget target = new MockUpgradeTarget();
        bytes memory delayData = abi.encodeWithSignature("updateMinDelay(uint256)", uint256(86_400));
        require(
            keccak256(abi.encode(TIMELOCK, uint256(0), keccak256(delayData), DELAY_CHANGE_PREDECESSOR)) == DELAY_CHANGE_ID,
            "saved delay operation ID"
        );
        bytes memory delayExecute = abi.encodeWithSignature(
            "execute(address,uint256,bytes,bytes32)", TIMELOCK, 0, delayData, DELAY_CHANGE_PREDECESSOR
        );
        uint256 delayIndex = submit(SIGNER1, delayExecute);
        vm.warp(DELAY_CHANGE_READY - 1);
        require(!confirm(SIGNER2, delayIndex), "early delay change succeeded");
        require(uint256(vm.load(TIMELOCK, bytes32(uint256(1)))) == DELAY, "early delay change wrote state");
        vm.warp(DELAY_CHANGE_READY);
        require(confirm(SIGNER2, delayIndex), "ready delay change failed");
        require(uint256(vm.load(TIMELOCK, bytes32(uint256(1)))) == 86_400, "one-day delay not installed");

        bytes memory upgradeData = abi.encodeWithSignature("upgrade(address,address)", EXCHANGE, address(target));
        bytes memory scheduleData = abi.encodeWithSignature(
            "schedule(address,uint256,bytes,bytes32)", ADMIN, 0, upgradeData, bytes32(0)
        );
        uint256 scheduleIndex = submit(SIGNER1, scheduleData);
        require(confirm(SIGNER2, scheduleIndex), "short-delay schedule failed");
        bytes32 id = keccak256(abi.encode(ADMIN, uint256(0), keccak256(upgradeData), bytes32(0)));
        bytes32 operationSlot = keccak256(abi.encode(id, uint256(2)));
        require(uint256(vm.load(TIMELOCK, operationSlot)) == DELAY_CHANGE_READY + 86_400, "one-day ready time");
        bytes memory executeData = abi.encodeWithSignature(
            "execute(address,uint256,bytes,bytes32)", ADMIN, 0, upgradeData, bytes32(0)
        );
        uint256 executeIndex = submit(SIGNER1, executeData);
        vm.warp(DELAY_CHANGE_READY + 86_400 - 1);
        require(!confirm(SIGNER2, executeIndex), "early short-delay upgrade succeeded");
        vm.warp(DELAY_CHANGE_READY + 86_400);
        require(confirm(SIGNER2, executeIndex), "short-delay upgrade failed");
        require(vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(address(target)))), "upgrade target");
        require(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER1, uint256(33))))) == PENDING1, "first pending changed");
        require(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER2, uint256(33))))) == PENDING2, "second pending changed");
    }
}
"""


def inputs():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == 48_902_346
    for address in ADDRESSES.values():
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
    multisig = json.loads((ATLAS / "multisig_behavior.json").read_text())
    timelock = json.loads((ATLAS / "timelock_behavior.json").read_text())
    admin = json.loads((ATLAS / "proxy_admin_behavior.json").read_text())
    assert multisig["signers"] == [
        "0xaa7577a7a27aa7fcf6d0ec481b87df3ad0f6a88e",
        "0xe9686c8e11d80c8d78736485fcb6b6d7f4d7692e",
        "0x9028f3b5b6b0d69e4e84ff555ade17114c3d1e72",
    ]
    assert multisig["transaction_count"] == 7
    assert timelock["owner"] == ADDRESSES["Multisig"]
    assert admin["owner_at_pin"] == ADDRESSES["Timelock"]
    operations = json.loads((ATLAS / "timelock_operations.json").read_text())
    assert operations["min_delay_seconds"] == 604_800
    delay_change = next(
        row
        for row in operations["operations"]
        if row["target"] == ADDRESSES["Timelock"]
    )
    assert (
        delay_change["operation_id"]
        == "0xc616b8d5f1fccaae8952fd5832306ef7d181cdbf7b3e81fa331593abc6d6a6cb"
    )
    assert (
        delay_change["predecessor"]
        == "0x4f6334bb72dc6434598f27bdd8a884e83553a871b874434dba529b894e0b1bc3"
    )
    assert delay_change["ready_timestamp_from_event"] == 1_792_447_296
    assert delay_change["call_arguments_uint256_words"] == [86_400]
    assert delay_change["is_pending_at_pin"] is True
    assert manifest["timestamp"] == 1_792_357_341
    assert (
        json.loads((ATLAS / "upgrade_history.json").read_text())[
            ADDRESSES["ExchangeProxy"]
        ]["pinned_implementation"]
        == ADDRESSES["ExchangeImplementation"]
    )
    stalled_cases = stalled.stalled_rows()
    assert [
        last["spot_raw"] + (last["perp_raw"] << 64) + (last["block"] << 128)
        for _, last in stalled_cases
    ] == [5_005_091_600 | (48_209_855 << 128), 1_210_000_000 | (48_091_494 << 128)]
    return manifest


def run():
    manifest = inputs()
    solc = shutil.which("solc")
    assert solc, "local solc is required"
    with tempfile.TemporaryDirectory(prefix="papertrade-pt01-governance-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = "
            + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "Pt01Governance.t.sol").write_text(TEST_SOURCE)
        for name, address in ADDRESSES.items():
            row = manifest["contracts"][address]
            (project / "runtime" / f"{name}.hex").write_text(
                (ATLAS / row["runtime_file"]).read_text().strip()
            )
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True,
            check=False,
            text=True,
            timeout=60,
        )
    output = result.stdout + "\n" + result.stderr
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    if result.returncode or passed != TEST_NAMES:
        raise RuntimeError("PT-01 governance replay failed: " + output[-5000:])
    payload = {
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "runtime_hashes": {
            name: manifest["contracts"][address]["sha256"]
            for name, address in ADDRESSES.items()
        },
        "test_names": sorted(passed),
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "forge_result": "2 passed, 0 failed",
        "direct_upgrade_delay_seconds": 604_800,
        "scheduled_delay_change_ready_timestamp": 1_792_447_296,
        "subsequent_upgrade_delay_seconds": 86_400,
        "earliest_tested_upgrade_timestamp": 1_792_447_296 + 86_400,
        "pinned_pending_words_unchanged_by_upgrade": True,
        "limits": [
            "The mock upgrade target is not deployed Papertrade code and contains no recovery logic.",
            "Pinned governance slots and both pending words are seeded locally; other state is not reproduced.",
            "The replay proves two authorized upgrade paths and their delays in the tested state, not HyperCore delivery or a safe upgrade implementation.",
            "It does not establish whether governance acted after the pin or whether an emergency Core-side remedy exists.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    return verify()


def verify():
    manifest = inputs()
    saved = json.loads(OUT.read_text())
    assert saved["pin"] == manifest["block"]
    assert saved["block_hash"] == manifest["block_hash"]
    assert saved["runtime_hashes"] == {
        name: manifest["contracts"][address]["sha256"]
        for name, address in ADDRESSES.items()
    }
    assert set(saved["test_names"]) == TEST_NAMES
    assert (
        saved["test_source_sha256"] == hashlib.sha256(TEST_SOURCE.encode()).hexdigest()
    )
    assert saved["forge_result"] == "2 passed, 0 failed"
    assert saved["direct_upgrade_delay_seconds"] == 604_800
    assert saved["scheduled_delay_change_ready_timestamp"] == 1_792_447_296
    assert saved["subsequent_upgrade_delay_seconds"] == 86_400
    assert saved["earliest_tested_upgrade_timestamp"] == 1_792_533_696
    assert saved["pinned_pending_words_unchanged_by_upgrade"] is True
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", action="store_true", help="replay pinned runtimes locally"
    )
    args = parser.parse_args()
    result = run() if args.run else verify()
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("pin", "forge_result", "earliest_tested_upgrade_timestamp")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
