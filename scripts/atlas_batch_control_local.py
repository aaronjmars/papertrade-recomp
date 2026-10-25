#!/usr/bin/env python3
"""Check BatchExecutor ownership, relayer and initialization paths against pinned bytecode."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "batch_control_local" / "replay.json"
BEHAVIOR_OUT = ATLAS / "batch_control_behavior.json"
PROXY = "0x233ff29b239abc1d7748605da9b205c3e008626e"
IMPLEMENTATION = "0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262"
ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OLD_OWNER = "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
RELAYER = "0xc916e55b1909be6582bf1b2f017aaf82ad8eb0b4"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
RELAYER_TX = "0x303956400b3cd1c4ed86cf3644975a5f8b1ea2f3e487bad7da21d49689d52b6f"
OWNER_TX = "0xd928f58d081c09d5600715814814b78ed5256ae3b1a54f11d822deaa9c0e2049"
SIGNATURES = {
    "0x0b826190": "sessionKeyManager()",
    "0x29e295c5": "authorizedRelayers(address)",
    "0x8da5cb5b": "owner()",
    "0x9011e5f9": "setAuthorizedRelayer(address,bool)",
    "0xd2f7265a": "exchange()",
    "0xf2fde38b": "transferOwnership(address)",
}
TEST_NAMES = ["testPinnedGetters", "testRelayerSetter", "testRelayerOutsider",
              "testOwnershipTransfer", "testPinnedInitializationReverts",
              "testFreshFiveArgumentInitialization", "testFreshTwoArgumentInitialization",
              "testFreshTwoArgumentRequiresAdmin", "testThreeArgPinned", "testThreeArgFresh"]
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
contract BatchControlTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant IMPL = address(uint160(uint256(0x00e0bc9cc7b067060aafccbaa3e250700c9cdd7262)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant RELAYER = address(uint160(uint256(0x00c916e55b1909be6582bf1b2f017aaf82ad8eb0b4)));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant STAKING = address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 constant RELAYER_SLOT = keccak256(abi.encode(RELAYER, uint256(4)));
    function setUp() public {
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(PROXY, bytes32(uint256(0)), bytes32((uint256(uint160(EXCHANGE)) << 16) | 0x0001));
        vm.store(PROXY, bytes32(uint256(1)), bytes32(uint256(uint160(SESSION))));
        vm.store(PROXY, bytes32(uint256(2)), bytes32(uint256(uint160(STAKING))));
        vm.store(PROXY, bytes32(uint256(3)), bytes32(uint256(uint160(OWNER))));
        vm.store(PROXY, bytes32(uint256(5)), bytes32(uint256(1)));
        vm.store(PROXY, RELAYER_SLOT, bytes32(uint256(1)));
    }
    function callAs(address caller, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return PROXY.call(data);
    }
    function getAddress(bytes4 selector) internal view returns (address) {
        (bool ok, bytes memory out) = PROXY.staticcall(abi.encodeWithSelector(selector));
        require(ok && out.length == 32, "getter failed");
        return abi.decode(out, (address));
    }
    function checkLog(Vm.Log[] memory logs, bytes32 topic, address indexedAddress, bytes memory data) internal pure {
        require(logs.length == 1 && logs[0].emitter == PROXY, "log count or emitter");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == topic, "log topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(indexedAddress))), "log indexed address");
        require(keccak256(logs[0].data) == keccak256(data), "log data");
    }
    function checkInitLogs(Vm.Log[] memory logs) internal pure {
        require(logs.length == 2, "init log count");
        require(logs[0].emitter == PROXY && logs[0].topics.length == 2, "init owner log");
        require(logs[0].topics[0] == keccak256("OwnerUpdated(address)"), "init owner topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(OWNER))) && logs[0].data.length == 0, "init owner data");
        require(logs[1].emitter == PROXY && logs[1].topics.length == 2, "init relayer log");
        require(logs[1].topics[0] == keccak256("AuthorizedRelayerUpdated(address,bool)"), "init relayer topic");
        require(logs[1].topics[1] == bytes32(uint256(uint160(RELAYER))), "init relayer address");
        require(keccak256(logs[1].data) == keccak256(abi.encode(true)), "init relayer data");
    }
    function testPinnedGetters() public view {
        require(getAddress(bytes4(0xd2f7265a)) == EXCHANGE, "exchange");
        require(getAddress(bytes4(0x0b826190)) == SESSION, "session");
        require(getAddress(bytes4(0xd5c539ce)) == STAKING, "staking");
        require(getAddress(bytes4(0x8da5cb5b)) == OWNER, "owner");
        (bool ok, bytes memory out) = PROXY.staticcall(abi.encodeWithSelector(bytes4(0x29e295c5), RELAYER));
        require(ok && abi.decode(out, (bool)), "relayer");
        (ok, out) = PROXY.staticcall(abi.encodeWithSelector(bytes4(0x6090cf16)));
        require(ok && abi.decode(out, (uint256)) == 1, "init flag");
    }
    function testRelayerSetter() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x9011e5f9), RELAYER, false));
        require(ok && vm.load(PROXY, RELAYER_SLOT) == bytes32(0), "relayer clear");
        checkLog(vm.getRecordedLogs(), keccak256("AuthorizedRelayerUpdated(address,bool)"), RELAYER, abi.encode(false));
        vm.recordLogs();
        (ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x9011e5f9), RELAYER, true));
        require(ok && vm.load(PROXY, RELAYER_SLOT) == bytes32(uint256(1)), "relayer set");
        checkLog(vm.getRecordedLogs(), keccak256("AuthorizedRelayerUpdated(address,bool)"), RELAYER, abi.encode(true));
    }
    function testRelayerOutsider() public {
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x9011e5f9), RELAYER, false));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "outsider error");
        require(vm.load(PROXY, RELAYER_SLOT) == bytes32(uint256(1)), "outsider changed relayer");
    }
    function testOwnershipTransfer() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0xf2fde38b), address(0x1234)));
        require(ok && getAddress(bytes4(0x8da5cb5b)) == address(0x1234), "owner transfer");
        checkLog(vm.getRecordedLogs(), keccak256("OwnerUpdated(address)"), address(0x1234), bytes(""));
        (ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x9011e5f9), RELAYER, false));
        require(!ok, "old owner authorized");
        (ok,) = callAs(address(0x1234), abi.encodeWithSelector(bytes4(0x9011e5f9), RELAYER, false));
        require(ok, "new owner unauthorized");
    }
    function testPinnedInitializationReverts() public {
        (bool ok, bytes memory out) = callAs(ADMIN, abi.encodeWithSelector(bytes4(0x0f71c8bc), address(0x1234), RELAYER));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x3f733c4f), "two-arg init error");
        (ok, out) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x9ccae24e), EXCHANGE, SESSION, STAKING, OWNER, RELAYER));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x0dc149f0), "five-arg init error");
        require(vm.load(PROXY, bytes32(uint256(3))) == bytes32(uint256(uint160(OWNER))), "owner changed");
    }
    function testFreshFiveArgumentInitialization() public {
        for (uint256 i = 0; i <= 5; i++) vm.store(PROXY, bytes32(i), bytes32(0));
        vm.store(PROXY, RELAYER_SLOT, bytes32(0));
        vm.recordLogs();
        (bool ok,) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x9ccae24e), EXCHANGE, SESSION, STAKING, OWNER, RELAYER));
        require(ok, "fresh five-arg init failed");
        require(uint256(vm.load(PROXY, bytes32(uint256(0)))) >> 16 == uint256(uint160(EXCHANGE)), "exchange slot");
        require(vm.load(PROXY, bytes32(uint256(1))) == bytes32(uint256(uint160(SESSION))), "session slot");
        require(vm.load(PROXY, bytes32(uint256(2))) == bytes32(uint256(uint160(STAKING))), "staking slot");
        require(vm.load(PROXY, bytes32(uint256(3))) == bytes32(uint256(uint160(OWNER))), "owner slot");
        require(vm.load(PROXY, bytes32(uint256(5))) == bytes32(uint256(1)), "init slot");
        require(vm.load(PROXY, RELAYER_SLOT) == bytes32(uint256(1)), "relayer slot");
        checkInitLogs(vm.getRecordedLogs());
    }
    function testThreeArgPinned() public {
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0xc0c53b8b), EXCHANGE, SESSION, STAKING));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0xb7b2509c), "three-arg pinned error");
    }
    function testThreeArgFresh() public {
        for (uint256 i = 0; i <= 5; i++) vm.store(PROXY, bytes32(i), bytes32(0));
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0xc0c53b8b), EXCHANGE, SESSION, STAKING));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0xb7b2509c), "three-arg fresh error");
    }
    function testFreshTwoArgumentRequiresAdmin() public {
        vm.store(PROXY, bytes32(uint256(3)), bytes32(0));
        vm.store(PROXY, bytes32(uint256(5)), bytes32(0));
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x0f71c8bc), OWNER, RELAYER));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0xc031a0df), "init caller error");
        require(vm.load(PROXY, bytes32(uint256(3))) == bytes32(0), "outsider initialized owner");
    }
    function testFreshTwoArgumentInitialization() public {
        vm.store(PROXY, bytes32(uint256(3)), bytes32(0));
        vm.store(PROXY, bytes32(uint256(5)), bytes32(0));
        vm.store(PROXY, RELAYER_SLOT, bytes32(0));
        vm.recordLogs();
        (bool ok,) = callAs(ADMIN, abi.encodeWithSelector(bytes4(0x0f71c8bc), OWNER, RELAYER));
        require(ok, "fresh two-arg init failed");
        require(vm.load(PROXY, bytes32(uint256(3))) == bytes32(uint256(uint160(OWNER))), "owner slot");
        require(vm.load(PROXY, bytes32(uint256(5))) == bytes32(uint256(1)), "init slot");
        require(vm.load(PROXY, RELAYER_SLOT) == bytes32(uint256(1)), "relayer slot");
        checkInitLogs(vm.getRecordedLogs());
    }
}
'''


def cast(*args):
    return subprocess.run(["cast", *args], check=True, capture_output=True, text=True).stdout.strip()


def historic(hash_):
    folder = ROOT / "artifacts" / "historical"
    return {kind: json.loads((folder / f"{hash_}.{kind}.json").read_text())
            for kind in ("calls", "receipt", "state_diff")}


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    for selector, signature in SIGNATURES.items():
        assert cast("sig", signature) == selector
    assert cast("keccak", "AuthorizedRelayerUpdated(address,bool)") == "0x431c9efc75fd5a8b5d510e3458e1c31ac5c3de0385743f60f76491e1e0867391"
    assert cast("keccak", "OwnerUpdated(address)") == "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b"
    raw = {}
    for name, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        raw[name] = code
    assert catalog[IMPLEMENTATION]["sha256"] == manifest["contracts"][IMPLEMENTATION]["sha256"]
    for selector in SIGNATURES:
        assert selector in {f["selector"] for f in catalog[IMPLEMENTATION]["functions"]}

    archived_prestate = json.loads((ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json").read_text())
    archived_slot0 = archived_prestate[PROXY]["storage"]["0x" + "0" * 64]
    assert archived_slot0 == "0x000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a20001"
    assert (int(archived_slot0, 16) >> 16) & ((1 << 160) - 1) == int(EXCHANGE, 16)
    relayer = historic(RELAYER_TX)
    owner = historic(OWNER_TX)
    relayer_slot = cast("keccak", "0x" + RELAYER[2:].rjust(64, "0") + (4).to_bytes(32, "big").hex())
    assert relayer["calls"]["from"].lower() == OLD_OWNER
    assert relayer["calls"]["to"].lower() == PROXY
    assert relayer["calls"]["input"][:10] == "0x9011e5f9"
    assert relayer["calls"]["input"][10:74].endswith(RELAYER[2:]) and int(relayer["calls"]["input"][74:], 16) == 1
    assert relayer["receipt"]["status"] == "0x1" and len(relayer["receipt"]["logs"]) == 1
    relayer_log = relayer["receipt"]["logs"][0]
    assert relayer_log["topics"] == [cast("keccak", "AuthorizedRelayerUpdated(address,bool)"), "0x" + RELAYER[2:].rjust(64, "0")]
    assert int(relayer_log["data"], 16) == 1
    assert relayer["state_diff"]["post"][PROXY]["storage"][relayer_slot] == "0x" + "0" * 63 + "1"
    assert owner["calls"]["from"].lower() == OLD_OWNER and owner["calls"]["to"].lower() == PROXY
    assert owner["calls"]["input"][:10] == "0xf2fde38b" and owner["calls"]["input"][-40:] == OWNER[2:]
    assert owner["receipt"]["status"] == "0x1" and len(owner["receipt"]["logs"]) == 1
    owner_log = owner["receipt"]["logs"][0]
    assert owner_log["topics"] == [cast("keccak", "OwnerUpdated(address)"), "0x" + OWNER[2:].rjust(64, "0")]
    assert owner_log["data"] == "0x"
    owner_slot = "0x" + "0" * 63 + "3"
    assert owner["state_diff"]["pre"][PROXY]["storage"][owner_slot][-40:] == OLD_OWNER[2:]
    assert owner["state_diff"]["post"][PROXY]["storage"][owner_slot][-40:] == OWNER[2:]

    solc = shutil.which("solc")
    assert solc, "local solc is required"
    with tempfile.TemporaryDirectory(prefix="papertrade-batch-control-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(solc) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "BatchControl.t.sol").write_text(TEST_SOURCE)
        for name, code in raw.items():
            (project / "runtime" / f"{name}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("Batch control replay failed: " + output[-3800:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "runtime_hashes": {name: manifest["contracts"][address]["sha256"] for name, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
        "test_names": sorted(passed), "forge_result": "10 passed, 0 failed",
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "historic_relayer_tx": RELAYER_TX, "historic_owner_tx": OWNER_TX,
        "archived_batch_slot0": archived_slot0,
        "archived_slot0_source": "../../artifacts/exchange_negative_close/original_prestate.json",
        "method": "port-free Forge tests with exact pinned proxy and implementation bytecode; archived packed slot 0 and pinned getter values installed locally; fresh initialization states are synthetic",
    }, indent=2) + "\n")
    BEHAVIOR_OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "address": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": manifest["contracts"][IMPLEMENTATION]["sha256"],
        "selector_reconstructions": SIGNATURES,
        "historical_control_transactions": {"relayer_set": RELAYER_TX, "owner_transfer": OWNER_TX},
        "relayer_mapping_base_slot": 4, "owner_slot": 3, "initialization_status_slot": 5,
        "slot0_layout": "Exchange address in bits 16..175, low byte 0x01 in archived prestate",
        "simulated_initializer_events": ["OwnerUpdated(address)", "AuthorizedRelayerUpdated(address,bool)"],
        "simulated_control_selectors": ["0x0f71c8bc", "0x9ccae24e", "0xc0c53b8b"],
        "locally_checked_existing_getters": ["0x6090cf16", "0xd5c539ce"],
        "event_catalog": [
            {"topic0": cast("keccak", "AuthorizedRelayerUpdated(address,bool)"), "reconstructed_signature": "AuthorizedRelayerUpdated(address,bool)", "historical_tx": RELAYER_TX},
            {"topic0": cast("keccak", "OwnerUpdated(address)"), "reconstructed_signature": "OwnerUpdated(address)", "historical_tx": OWNER_TX},
        ],
        "simulated_error_catalog": [
            {"selector": "0x30cd7471", "reconstructed_signature": "NotOwner()", "probe_paths": ["testRelayerOutsider"]},
            {"selector": "0x3f733c4f", "probe_paths": ["testPinnedInitializationReverts"]},
            {"selector": "0x0dc149f0", "reconstructed_signature": "AlreadyInitialized()", "probe_paths": ["testPinnedInitializationReverts"]},
            {"selector": "0xc031a0df", "probe_paths": ["testFreshTwoArgumentRequiresAdmin"]},
            {"selector": "0xb7b2509c", "probe_paths": ["testThreeArgPinned", "testThreeArgFresh"]}],
        "local_replay_evidence": "../../artifacts/batch_control_local/replay.json",
        "limits": ["Fresh initialization branch tests use synthetic local storage and callers.",
                   "Five-argument and two-argument initializer source names are unresolved.",
                   "Historical relayer-set and owner-transfer observations do not establish every setter branch."],
    }, indent=2) + "\n")
    print("verified BatchExecutor historical control writes and ten local pinned-runtime tests")


if __name__ == "__main__":
    main()
