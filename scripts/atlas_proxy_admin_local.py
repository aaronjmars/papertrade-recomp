#!/usr/bin/env python3
"""Replay ProxyAdmin control paths through exact pinned admin and proxy bytecode."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "proxy_admin_local" / "replay.json"
BEHAVIOR_OUT = ATLAS / "proxy_admin_behavior.json"
SHARED_PROXY_OUT = ATLAS / "shared_proxy_behavior.json"
ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
HISTORICAL_TX = "0xd0e33b23f464c5ae6089ad86d9c2bb1cd8f627dc5eef5f756ae598225f93e145"
SIGNATURES = {"0x7eff275e": "changeProxyAdmin(address,address)",
              "0x8da5cb5b": "owner()",
              "0x9623609d": "upgradeAndCall(address,address,bytes)",
              "0x99a88ec4": "upgrade(address,address)",
              "0xf2fde38b": "transferOwnership(address)"}
PROXY_SIGNATURES = {"0x4f1ef286": "upgradeToAndCall(address,bytes)",
                    "0x5c60da1b": "implementation()",
                    "0x8f283970": "changeAdmin(address)",
                    "0xf851a440": "admin()"}
TEST_NAMES = ["testPinnedOwnerAndOutsider", "testUpgrade", "testUpgradeAndCall",
              "testChangeProxyAdmin", "testTransferOwnership", "testRejectZeroOwner",
              "testAllowsNoCodeImplementation", "testProxyAdminViews",
              "testProxyNonAdminSelectors", "testRejectZeroProxyAdmin"]
TEST_SOURCE = '''pragma solidity ^0.8.24;
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
contract MockImplementation {
    function setX(uint256 value) external payable {
        assembly { sstore(0, value) }
    }
}
contract ProxyAdminLocalTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant ORIGINAL_IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    MockImplementation mock;
    function setUp() public {
        vm.etch(ADMIN, vm.parseBytes(vm.readFile("runtime/ProxyAdmin.hex")));
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(ORIGINAL_IMPL, vm.parseBytes(vm.readFile("runtime/ExchangeImplementation.hex")));
        vm.store(ADMIN, bytes32(0), bytes32(uint256(uint160(OWNER))));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(ORIGINAL_IMPL))));
        mock = new MockImplementation();
    }
    function callAs(address caller, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return ADMIN.call(data);
    }
    function proxyCallAs(address caller, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return PROXY.call(data);
    }
    function owner() internal view returns (address) {
        (bool ok, bytes memory out) = ADMIN.staticcall(abi.encodeWithSelector(bytes4(0x8da5cb5b)));
        require(ok && out.length == 32, "owner call failed");
        return abi.decode(out, (address));
    }
    function checkNoLogs(Vm.Log[] memory logs) internal pure {
        require(logs.length == 0, "proxy emitted unexpected log");
    }
    function checkLog(Vm.Log[] memory logs, address emitter, bytes32 topic) internal pure {
        require(logs.length == 1, "unexpected log count");
        require(logs[0].emitter == emitter && logs[0].topics[0] == topic, "wrong log");
    }
    function testPinnedOwnerAndOutsider() public {
        require(owner() == OWNER, "wrong pinned owner");
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x99a88ec4), PROXY, address(mock)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "outsider error");
        require(vm.load(PROXY, IMPLEMENTATION_SLOT) == bytes32(uint256(uint160(ORIGINAL_IMPL))), "outsider changed impl");
        (ok, out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x9623609d), PROXY, address(mock), bytes("")));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "outsider upgradeAndCall error");
        (ok, out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x7eff275e), PROXY, address(0x1234)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "outsider admin error");
        (ok, out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0xf2fde38b), address(0x9876)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "outsider owner error");
        require(vm.load(PROXY, IMPLEMENTATION_SLOT) == bytes32(uint256(uint160(ORIGINAL_IMPL))), "outsider changed impl after checks");
    }
    function testAllowsNoCodeImplementation() public {
        require(address(0x1234).code.length == 0, "target unexpectedly has code");
        vm.recordLogs();
        (bool ok, bytes memory out) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x99a88ec4), PROXY, address(0x1234)));
        require(ok && out.length == 0, "no-code upgrade failed");
        require(vm.load(PROXY, IMPLEMENTATION_SLOT) == bytes32(uint256(uint160(address(0x1234)))), "no-code impl not installed");
        checkNoLogs(vm.getRecordedLogs());
    }
    function testUpgrade() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x99a88ec4), PROXY, address(mock)));
        require(ok, "upgrade failed");
        require(vm.load(PROXY, IMPLEMENTATION_SLOT) == bytes32(uint256(uint160(address(mock)))), "wrong impl");
        checkNoLogs(vm.getRecordedLogs());
    }
    function testUpgradeAndCall() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x9623609d), PROXY, address(mock), abi.encodeCall(MockImplementation.setX, (123))));
        require(ok, "upgradeAndCall failed");
        require(vm.load(PROXY, IMPLEMENTATION_SLOT) == bytes32(uint256(uint160(address(mock)))), "wrong impl");
        require(vm.load(PROXY, bytes32(0)) == bytes32(uint256(123)), "delegatecall did not write proxy");
        checkNoLogs(vm.getRecordedLogs());
    }
    function testChangeProxyAdmin() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x7eff275e), PROXY, address(0x1234)));
        require(ok, "changeProxyAdmin failed");
        require(vm.load(PROXY, ADMIN_SLOT) == bytes32(uint256(uint160(address(0x1234)))), "wrong proxy admin");
        checkNoLogs(vm.getRecordedLogs());
    }
    function testTransferOwnership() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0xf2fde38b), address(0x9876)));
        require(ok && owner() == address(0x9876), "owner transfer failed");
        checkLog(vm.getRecordedLogs(), ADMIN, keccak256("OwnerUpdated(address)"));
        (ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x99a88ec4), PROXY, address(mock)));
        require(!ok, "old owner stayed authorized");
        (ok,) = callAs(address(0x9876), abi.encodeWithSelector(bytes4(0x99a88ec4), PROXY, address(mock)));
        require(ok, "new owner not authorized");
    }
    function testProxyAdminViews() public {
        vm.prank(ADMIN);
        (bool ok, bytes memory out) = PROXY.staticcall(abi.encodeWithSelector(bytes4(0xf851a440)));
        require(ok && out.length == 32 && abi.decode(out, (address)) == ADMIN, "proxy admin getter");
        vm.prank(ADMIN);
        (ok, out) = PROXY.staticcall(abi.encodeWithSelector(bytes4(0x5c60da1b)));
        require(ok && out.length == 32 && abi.decode(out, (address)) == ORIGINAL_IMPL, "proxy implementation getter");
    }
    function testProxyNonAdminSelectors() public {
        (bool ok, bytes memory out) = proxyCallAs(address(0xbeef), abi.encodeWithSelector(bytes4(0xf851a440)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x7bfa4b9f), "admin getter auth");
        (ok, out) = proxyCallAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x5c60da1b)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x7bfa4b9f), "implementation getter auth");
        (ok, out) = proxyCallAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x8f283970), address(0x1234)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x7bfa4b9f), "change admin auth");
        (ok, out) = proxyCallAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x4f1ef286), address(mock), bytes("")));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x7bfa4b9f), "upgrade auth");
    }
    function testRejectZeroProxyAdmin() public {
        (bool ok, bytes memory out) = proxyCallAs(ADMIN, abi.encodeWithSelector(bytes4(0x8f283970), address(0)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0xe6c4247b), "zero proxy admin error");
        require(vm.load(PROXY, ADMIN_SLOT) == bytes32(uint256(uint160(ADMIN))), "zero admin changed slot");
    }
    function testRejectZeroOwner() public {
        (bool ok, bytes memory out) = callAs(OWNER, abi.encodeWithSelector(bytes4(0xf2fde38b), address(0)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x49e27cff), "zero owner error");
        require(owner() == OWNER, "zero owner changed state");
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[ADMIN]["functions"]
    assert {fn["selector"] for fn in catalog} == set(SIGNATURES)
    for selector, signature in SIGNATURES.items():
        assert subprocess.run(["cast", "sig", signature], capture_output=True, text=True, check=True).stdout.strip() == selector
        assert signature in next(fn for fn in catalog if fn["selector"] == selector)["candidate_signature"].split("|")
    pinned = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[ADMIN]
    owner_view = next(row for row in pinned["views"] if row["selector"] == "0x8da5cb5b")
    assert owner_view["return_prefix"] == "0x" + "00" * 12 + OWNER[2:]
    runtimes = {}
    for name, address in (("ProxyAdmin", ADMIN), ("ExchangeProxy", PROXY), ("ExchangeImplementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        raw = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(raw.removeprefix("0x"))).hexdigest() == row["sha256"]
        runtimes[name] = {"address": address, "sha256": row["sha256"], "hex": raw}
    assert int(manifest["contracts"][PROXY]["eip1967_slots"]["admin"], 16) == int(ADMIN, 16)
    assert int(manifest["contracts"][PROXY]["eip1967_slots"]["implementation"], 16) == int(IMPLEMENTATION, 16)
    proxy_runtime = bytes.fromhex(runtimes["ExchangeProxy"]["hex"][2:])
    admin_slot = "b53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
    implementation_slot = "360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
    assert proxy_runtime[0x328:0x348].hex() == admin_slot
    assert proxy_runtime[0x348:0x368].hex() == implementation_slot
    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", runtimes["ExchangeProxy"]["hex"]],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    executable_logs = [line for line in disassembly.splitlines() if len(line) > 10 and line[8:10] == ": "
                       and int(line[:8], 16) < 0x327 and line.split(": ", 1)[1].split(" ", 1)[0].startswith("LOG")]
    assert not executable_logs
    proxy_catalog = json.loads((ATLAS / "selector_catalog.json").read_text())["0x1629b7d46bef6e13ff754174fc9f32dea309b38f"]
    assert len(proxy_catalog["same_runtime_addresses"]) == 8
    assert {fn["selector"] for fn in proxy_catalog["functions"]} == set(PROXY_SIGNATURES)
    for selector, signature in PROXY_SIGNATURES.items():
        assert subprocess.run(["cast", "sig", signature], capture_output=True, text=True, check=True).stdout.strip() == selector
        assert signature in next(fn for fn in proxy_catalog["functions"] if fn["selector"] == selector)["candidate_signature"].split("|")
    assert all(manifest["contracts"][address]["sha256"] == runtimes["ExchangeProxy"]["sha256"]
               for address in proxy_catalog["same_runtime_addresses"])
    history = json.loads((ATLAS / "upgrade_history.json").read_text())
    assert len(history) == 8 and all(row["upgrade_event_count"] == 0 and row["same_at_creation_and_pin"]
                                    for row in history.values())
    admin_direct = json.loads((ATLAS / "direct_transaction_samples.json").read_text())[ADMIN]
    assert [page["count"] for page in admin_direct["pages"]] == [2, 2]
    assert admin_direct["sampled_unique_transactions"] == 1
    assert set(admin_direct["selectors"]) == {"0xf2fde38b"}
    assert admin_direct["selectors"]["0xf2fde38b"]["first"]["hash"] == HISTORICAL_TX
    timelock_logs = json.loads((ATLAS / "timelock_all_logs.json").read_text())
    executed_topics = {subprocess.run(["cast", "keccak", signature], capture_output=True, text=True, check=True).stdout.strip()
                       for signature in ("OperationExecuted(bytes32,address,uint256,bytes)",
                                         "BatchOperationExecuted(bytes32,uint256)")}
    assert len(timelock_logs) == 4 and not any(log["topics"][0] in executed_topics for log in timelock_logs)
    receipt = json.loads((ROOT / "artifacts" / "historical" / f"{HISTORICAL_TX}.receipt.json").read_text())
    call = json.loads((ROOT / "artifacts" / "historical" / f"{HISTORICAL_TX}.calls.json").read_text())
    diff = json.loads((ROOT / "artifacts" / "historical" / f"{HISTORICAL_TX}.state_diff.json").read_text())
    owner_event = subprocess.run(["cast", "keccak", "OwnerUpdated(address)"], capture_output=True, text=True, check=True).stdout.strip()
    assert call["to"].lower() == ADMIN and call["input"][:10] == "0xf2fde38b"
    assert call["input"][-40:].lower() == OWNER[2:] and receipt["status"] == "0x1"
    assert len(receipt["logs"]) == 1 and receipt["logs"][0]["address"].lower() == ADMIN
    assert receipt["logs"][0]["topics"] == [owner_event, "0x" + "00" * 12 + OWNER[2:]]
    assert receipt["logs"][0]["data"] == "0x"
    before_owner = "0x" + diff["pre"][ADMIN]["storage"]["0x" + "00" * 32][-40:]
    after_owner = "0x" + diff["post"][ADMIN]["storage"]["0x" + "00" * 32][-40:]
    assert before_owner.lower() == call["from"].lower() and after_owner == OWNER
    solc = shutil.which("solc")
    assert solc, "local solc is required; no compiler download is allowed"
    with tempfile.TemporaryDirectory(prefix="papertrade-proxy-admin-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(solc) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ProxyAdminLocal.t.sol").write_text(TEST_SOURCE)
        for name, row in runtimes.items():
            (project / "runtime" / f"{name}.hex").write_text(row["hex"])
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                             capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("ProxyAdmin local replay failed: " + output[-2200:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "method": "port-free Forge EVM with exact pinned ProxyAdmin, Exchange proxy, and Exchange implementation runtimes injected; pinned owner and EIP-1967 slots set locally; mock new implementation used only as upgrade target",
        "runtime_hashes": {name: {key: row[key] for key in ("address", "sha256")} for name, row in runtimes.items()},
        "test_names": sorted(passed), "forge_result": "10 passed, 0 failed",
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "observed_paths": ["owner getter", "outsider owner checks", "proxy admin views", "proxy NotAdmin checks", "zero proxy admin rejection", "upgrade", "upgradeAndCall delegatecall",
                           "changeProxyAdmin", "transferOwnership", "zero-owner rejection",
                           "no-code implementation accepted", "eventless proxy upgrades"],
        "limits": ["The mock implementation is a local test target, not a Papertrade deployment.",
                   "The saved historical call-graph sample contains no ProxyAdmin upgrade transaction."],
    }, indent=2) + "\n")
    BEHAVIOR_OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "address": ADMIN, "runtime_sha256": runtimes["ProxyAdmin"]["sha256"],
        "owner_at_pin": OWNER, "owner_storage_slot": 0,
        "selector_reconstructions": SIGNATURES,
        "historical_owner_transfer": {"tx": HISTORICAL_TX, "from": before_owner,
                                      "to": after_owner, "event_topic0": owner_event,
                                      "receipt_evidence": f"../../artifacts/historical/{HISTORICAL_TX}.receipt.json",
                                      "state_diff_evidence": f"../../artifacts/historical/{HISTORICAL_TX}.state_diff.json"},
        "event_catalog": [{"topic0": owner_event, "reconstructed_signature": "OwnerUpdated(address)",
                           "status": "observed_historical_topic"}],
        "simulated_error_catalog": [
            {"selector": "0x30cd7471", "reconstructed_signature": "NotOwner()",
             "probe_paths": ["testPinnedOwnerAndOutsider"]},
            {"selector": "0x49e27cff", "reconstructed_signature": "InvalidOwner()",
             "probe_paths": ["testRejectZeroOwner"]}],
        "proxy_runtime_sha256": runtimes["ExchangeProxy"]["sha256"],
        "shared_proxy_count": len(proxy_catalog["same_runtime_addresses"]),
        "proxy_executable_log_instruction_count": len(executable_logs),
        "proxy_admin_slot": "0x" + admin_slot,
        "proxy_implementation_slot": "0x" + implementation_slot,
        "local_replay_evidence": "../../artifacts/proxy_admin_local/replay.json",
        "tested_effects": {"upgrade": "sets proxy implementation slot without a log",
                           "upgradeAndCall": "sets proxy implementation slot and delegates setup call into proxy storage without a log",
                           "changeProxyAdmin": "sets proxy admin slot without a log",
                           "upgrade_to_no_code_address": "accepted in local pinned-runtime replay"},
        "administrative_history_evidence": {
            "proxy_admin_direct_transaction_pages": [2, 2],
            "direct_call_selectors": ["0xf2fde38b"],
            "saved_timelock_log_count": len(timelock_logs),
            "saved_timelock_execution_event_count": 0,
            "direct_transaction_source": "direct_transaction_samples.json",
            "timelock_event_source": "timelock_all_logs.json"},
        "upgrade_history_limit": "All eight proxies have zero Upgraded logs and creation/pin slots match, but the shared runtime emits no upgrade log. The saved direct ProxyAdmin pages contain only an owner transfer and the saved timelock logs contain no execution. Those additional records make an intermediate upgrade less likely, but their completeness is not independently proven here.",
        "limits": ["Successful upgrade targets and setup calldata in local tests are synthetic; no upgrade transaction is in the saved historical trace sample.",
                   "Source identifiers are hash-matching behavioral reconstructions, not verified Solidity source."],
    }, indent=2) + "\n")
    SHARED_PROXY_OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "address": "0x1629b7d46bef6e13ff754174fc9f32dea309b38f",
        "runtime_role": "deposit_proxy_factory_proxy",
        "runtime_sha256": runtimes["ExchangeProxy"]["sha256"],
        "proxy_addresses": proxy_catalog["same_runtime_addresses"],
        "selector_reconstructions": PROXY_SIGNATURES,
        "admin_slot": "0x" + admin_slot, "implementation_slot": "0x" + implementation_slot,
        "executable_log_instruction_count": len(executable_logs),
        "local_replay_evidence": "../../artifacts/proxy_admin_local/replay.json",
        "fallback_replay_evidence": "../../artifacts/fixed_revert_local/replay.json",
        "selector_behaviors": {
            "0xf851a440": "admin-only getter returns admin slot",
            "0x5c60da1b": "admin-only getter returns implementation slot",
            "0x8f283970": "admin-only setter changes admin slot; zero address reverts with 0xe6c4247b",
            "0x4f1ef286": "admin-only upgrade changes implementation slot; nonempty data delegatecalls into proxy storage; empty data accepts no-code target"},
        "simulated_error_catalog": [
            {"selector": "0x7bfa4b9f", "reconstructed_signature": "NotAdmin()",
             "probe_paths": ["testProxyNonAdminSelectors"]},
            {"selector": "0xe6c4247b", "probe_paths": ["testRejectZeroProxyAdmin"]}],
        "limits": ["The source name of error 0xe6c4247b is unresolved.",
                   "Upgrade and admin-change successes are local simulations, not historical transactions.",
                   "The mock upgrade target is not a Papertrade deployment."],
    }, indent=2) + "\n")
    print("verified ten admin and proxy local tests through pinned runtimes")


if __name__ == "__main__":
    main()
