#!/usr/bin/env python3
"""Check deployed Exchange recovery calls against the pinned stalled sweep state."""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

import audit_stalled_sweeps as stalled
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "audit_sweep_recovery_local" / "replay.json"
BEHAVIOR_OUT = ATLAS / "exchange_sweep_recovery_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
CLEAR_SIGNATURE = "clearPendingSweep(address)"
CLEAR_SELECTOR = "0x2362f4de"
RECONCILE_SIGNATURE = "reconcileSweepCredit(address,uint256)"
RECONCILE_SELECTOR = "0x6a3214c9"
TEST_NAMES = {
    "testAbsentClearSelector",
    "testOwnerReconcilePendingRejected",
    "testSecondPendingReconcileRejected",
    "testOwnerReconcileAfterSyntheticClear",
    "testOutsiderCannotReconcile",
}
TEST_SOURCE = """pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract SweepRecoveryTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPLEMENTATION = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant USER = address(uint160(uint256(0x0056cbe78a5cdfa10147927aec550aa7f2fb3d3d01)));
    address constant USER2 = address(uint160(uint256(0x009c8599c32224d7d9956a7def18f7314162f77baf)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    uint256 constant CREDIT_INPUT = 50_050_916;
    uint256 constant CREDIT_INTERNAL = CREDIT_INPUT * 1e12;
    uint256 constant PENDING_WORD = 5_005_091_600 | (uint256(48_209_855) << 128);
    uint256 constant PENDING_WORD2 = 1_210_000_000 | (uint256(48_091_494) << 128);
    function pendingSlot() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(33)));
    }
    function pendingSlot2() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER2, uint256(33)));
    }
    function balanceSlot() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(9)));
    }
    function setUp() public {
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPLEMENTATION, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.store(EXCHANGE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPLEMENTATION))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(EXCHANGE, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        vm.store(EXCHANGE, bytes32(uint256(3)), bytes32(uint256(1e12)));
        vm.store(EXCHANGE, pendingSlot(), bytes32(PENDING_WORD));
        vm.store(EXCHANGE, balanceSlot(), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(uint256(100e18)));
        vm.store(EXCHANGE, bytes32(uint256(22)), bytes32((uint256(7) << 128) | uint256(100e18)));
    }
    function callAs(address caller, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return EXCHANGE.call(data);
    }
    function testAbsentClearSelector() public {
        vm.recordLogs();
        (bool ok, bytes memory out) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        require(!ok && out.length == 0, "clear selector unexpectedly dispatched");
        require(uint256(vm.load(EXCHANGE, pendingSlot())) == PENDING_WORD, "pending changed");
        require(vm.getRecordedLogs().length == 0, "unknown selector emitted log");
    }
    function testOwnerReconcilePendingRejected() public {
        vm.recordLogs();
        (bool ok, bytes memory out) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, CREDIT_INPUT));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x28ef4314), "pending rejection");
        require(uint256(vm.load(EXCHANGE, pendingSlot())) == PENDING_WORD, "pending changed");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == 5e18, "user credited");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == 100e18, "treasury credited");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) == ((uint256(7) << 128) | uint256(100e18)), "total credited");
        require(vm.getRecordedLogs().length == 0, "failed reconciliation emitted log");
    }
    function testSecondPendingReconcileRejected() public {
        vm.store(EXCHANGE, pendingSlot2(), bytes32(PENDING_WORD2));
        (bool ok, bytes memory out) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER2, 12_100_000));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x28ef4314), "second pending rejection");
        require(uint256(vm.load(EXCHANGE, pendingSlot2())) == PENDING_WORD2, "second pending changed");
        require(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER2, uint256(9))))) == 0, "second user credited");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == 100e18, "second treasury credited");
    }
    function testOwnerReconcileAfterSyntheticClear() public {
        vm.store(EXCHANGE, pendingSlot(), bytes32(0));
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, CREDIT_INPUT));
        require(ok, "owner reconciliation after clear reverted");
        require(uint256(vm.load(EXCHANGE, pendingSlot())) == 0, "pending recreated");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == 5e18 + CREDIT_INTERNAL, "user credit");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == 100e18 + CREDIT_INTERNAL, "treasury credit");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) == ((uint256(7) << 128) | (100e18 + CREDIT_INTERNAL)), "packed total credit");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == EXCHANGE, "reconcile log count");
        require(logs[0].topics.length == 2, "reconcile topics");
        require(logs[0].topics[0] == 0x8da9931e615ce9dfd2d7914e0cee3246839757203d34810cde64e0d0026f75c3, "reconcile topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(USER))), "reconcile user");
        require(abi.decode(logs[0].data, (uint256)) == CREDIT_INTERNAL, "reconcile event amount");
    }
    function testOutsiderCannotReconcile() public {
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x6a3214c9), USER, CREDIT_INPUT));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "outsider error");
        require(uint256(vm.load(EXCHANGE, pendingSlot())) == PENDING_WORD, "pending changed");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == 5e18, "unauthorized credit");
    }
}
"""


def expected_inputs():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    assert manifest["block"] == 48902346
    contract = manifest["contracts"][IMPLEMENTATION]
    code = (ATLAS / contract["runtime_file"]).read_text().strip()
    assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == contract["sha256"]
    assert bytes.fromhex(CLEAR_SELECTOR[2:]) not in bytes.fromhex(code[2:])
    functions = {row["selector"] for row in catalog[IMPLEMENTATION]["functions"]}
    assert CLEAR_SELECTOR not in functions and RECONCILE_SELECTOR in functions
    one_address_mutators = [
        row
        for row in catalog[IMPLEMENTATION]["functions"]
        if row["arguments"] == "address" and row["state_mutability"] != "view"
    ]
    assert len(one_address_mutators) == 13
    assert all(row["reconstructed_signature"] for row in one_address_mutators)
    keccak = Keccak()
    assert "0x" + keccak(CLEAR_SIGNATURE.encode()).hex()[:8] == CLEAR_SELECTOR
    assert "0x" + keccak(RECONCILE_SIGNATURE.encode()).hex()[:8] == RECONCILE_SELECTOR
    assert "0x" + keccak(b"SweepAlreadyPending()").hex()[:8] == "0x28ef4314"
    getters = json.loads((ATLAS / "exchange_direct_getters_behavior.json").read_text())
    scale = next(
        row for row in getters["direct_slot_getters"] if row["selector"] == "0xec0bdcfc"
    )
    assert scale["signature"] == "collateralScale()"
    assert scale["storage_slot"] == 3 and int(scale["raw_word"], 16) == 10**12
    return manifest


def run():
    manifest = expected_inputs()
    solc = shutil.which("solc")
    assert solc, "local solc is required"
    with tempfile.TemporaryDirectory(prefix="papertrade-sweep-recovery-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = "
            + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "SweepRecovery.t.sol").write_text(TEST_SOURCE)
        for name, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
            row = manifest["contracts"][address]
            code = (ATLAS / row["runtime_file"]).read_text().strip()
            assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
            (project / "runtime" / f"{name}.hex").write_text(code)
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
        raise RuntimeError("sweep recovery replay failed: " + output[-4000:])
    rows = stalled.stalled_rows()
    first, last = rows[0]
    assert first["user"] == "0x56cbe78a5cdfa10147927aec550aa7f2fb3d3d01"
    pending_word = last["spot_raw"] + (last["perp_raw"] << 64) + (last["block"] << 128)
    assert pending_word == 5_005_091_600 | (48_209_855 << 128)
    second_first, second_last = rows[1]
    assert second_first["user"] == "0x9c8599c32224d7d9956a7def18f7314162f77baf"
    second_pending_word = (
        second_last["spot_raw"]
        + (second_last["perp_raw"] << 64)
        + (second_last["block"] << 128)
    )
    assert second_pending_word == 1_210_000_000 | (48_091_494 << 128)
    payload = {
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "runtime_hashes": {
            name: manifest["contracts"][address]["sha256"]
            for name, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))
        },
        "stalled_user": first["user"],
        "stalled_pending_word": hex(pending_word),
        "second_stalled_user": second_first["user"],
        "second_stalled_pending_word": hex(second_pending_word),
        "clear_selector": CLEAR_SELECTOR,
        "reconcile_selector": RECONCILE_SELECTOR,
        "reconcile_input_micro_usdc": 50_050_916,
        "reconcile_credit_internal": 50_050_916 * 10**12,
        "test_names": sorted(passed),
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "forge_result": "5 passed, 0 failed",
        "limits": [
            "Local state uses the pinned pending word but constructed owner, accounting, and user-balance slots.",
            "The successful owner reconciliation uses a simulated direct storage clear; no deployed clear transaction was executed.",
            "No HyperCore transfer executes in this port-free replay; Core delivery and later governance actions are not tested.",
            "Absence is established for clearPendingSweep(address), not for every possible alternative recovery selector.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    BEHAVIOR_OUT.write_text(json.dumps(behavior(payload), indent=2) + "\n")
    return payload


def behavior(replay):
    return {
        "pin": replay["pin"],
        "block_hash": replay["block_hash"],
        "exchange_proxy": PROXY,
        "implementation": IMPLEMENTATION,
        "selector_reconstructions": {RECONCILE_SELECTOR: RECONCILE_SIGNATURE},
        "report_clear_signature": CLEAR_SIGNATURE,
        "report_clear_selector": CLEAR_SELECTOR,
        "report_clear_selector_in_runtime": False,
        "other_one_address_mutator_count": 13,
        "pending_reconcile_error": "0x28ef4314",
        "pending_reconcile_error_signature": "SweepAlreadyPending()",
        "simulated_error_catalog": [
            {
                "selector": "0x28ef4314",
                "reconstructed_signature": "SweepAlreadyPending()",
                "probe_paths": [
                    "testOwnerReconcilePendingRejected",
                    "testSecondPendingReconcileRejected",
                ],
            }
        ],
        "owner_reconcile_requires_simulated_clear": True,
        "owner_reconcile_credit_scale": 10**12,
        "pending_words_after_failed_reconcile": [
            replay["stalled_pending_word"],
            replay["second_stalled_pending_word"],
        ],
        "local_replay_evidence": "../../artifacts/audit_sweep_recovery_local/replay.json",
        "limits": replay["limits"],
    }


def verify():
    manifest = expected_inputs()
    saved = json.loads(OUT.read_text())
    assert saved["pin"] == manifest["block"]
    assert saved["block_hash"] == manifest["block_hash"]
    assert saved["runtime_hashes"] == {
        name: manifest["contracts"][address]["sha256"]
        for name, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))
    }
    first, last = stalled.stalled_rows()[0]
    assert saved["stalled_user"] == first["user"]
    assert int(saved["stalled_pending_word"], 16) == last["spot_raw"] + (
        last["perp_raw"] << 64
    ) + (last["block"] << 128)
    second_first, second_last = stalled.stalled_rows()[1]
    assert saved["second_stalled_user"] == second_first["user"]
    assert int(saved["second_stalled_pending_word"], 16) == second_last["spot_raw"] + (
        second_last["perp_raw"] << 64
    ) + (second_last["block"] << 128)
    assert (
        saved["clear_selector"] == CLEAR_SELECTOR
        and saved["reconcile_selector"] == RECONCILE_SELECTOR
    )
    assert saved["reconcile_input_micro_usdc"] == 50_050_916
    assert saved["reconcile_credit_internal"] == 50_050_916 * 10**12
    assert set(saved["test_names"]) == TEST_NAMES
    assert (
        saved["test_source_sha256"] == hashlib.sha256(TEST_SOURCE.encode()).hexdigest()
    )
    assert saved["forge_result"] == "5 passed, 0 failed"
    assert json.loads(BEHAVIOR_OUT.read_text()) == behavior(saved)
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", action="store_true", help="replay pinned runtime locally"
    )
    args = parser.parse_args()
    result = run() if args.run else verify()
    print(
        json.dumps(
            {key: result[key] for key in ("pin", "test_names", "forge_result")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
