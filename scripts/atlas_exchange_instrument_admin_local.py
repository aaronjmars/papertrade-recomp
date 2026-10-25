#!/usr/bin/env python3
"""Replay the untraced Exchange instrument setter through exact pinned runtimes."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "exchange_instrument_admin_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_instrument_admin_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SETTER = "0x5ca4c0ea"
EVENT = "0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9"
TEST_NAMES = ["testOwnerWritesAndEmits", "testStatefulSecondUpdateAndGetter",
              "testOwnerSecondInstrument", "testOutsiderRejected", "testKeeperRejected",
              "testInvalidInstrument", "testZeroFirst", "testZeroThird", "testRateUpperBound"]

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
contract ExchangeInstrumentAdminTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant KEEPER = address(uint160(uint256(0x003721476de31190dc1af8908026abe20efe25cf99)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 constant EVENT_TOPIC = 0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9;
    bytes4 constant SETTER = 0x5ca4c0ea;
    bytes4 constant GETTER = 0xdc8a47ef;
    function slotFor(uint32 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(7)));
    }
    function setUp() public {
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(PROXY, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        vm.store(PROXY, bytes32(uint256(8)), bytes32(uint256(2)));
        bytes32 s = slotFor(0);
        vm.store(PROXY, s, 0x000003e8000000000000002c28d1751327a700000000032d26d12e980b600000);
        vm.store(PROXY, bytes32(uint256(s) + 1), 0x00016345785d8a00000001b0f51147891600000000084595161401484a000000);
        vm.store(PROXY, bytes32(uint256(s) + 2), 0x00000000000000000000000000000000000000000000152d02c7e14af6800000);
    }
    function callAs(address who, uint32 id, uint128 first, uint96 second, uint96 third, uint64 fourth)
        internal returns (bool, bytes memory) {
        vm.prank(who);
        return PROXY.call(abi.encodeWithSelector(SETTER, id, first, second, third, fourth));
    }
    function getter(uint32 id) internal view returns (uint256[8] memory) {
        (bool ok, bytes memory result) = PROXY.staticcall(abi.encodeWithSelector(GETTER, id));
        require(ok && result.length == 256, "getter");
        return abi.decode(result, (uint256[8]));
    }
    function testOwnerWritesAndEmits() public {
        bytes32 s = slotFor(0);
        uint256 old0 = uint256(vm.load(PROXY, s));
        uint256 old1 = uint256(vm.load(PROXY, bytes32(uint256(s) + 1)));
        uint256 old2 = uint256(vm.load(PROXY, bytes32(uint256(s) + 2)));
        vm.recordLogs();
        (bool ok, bytes memory output) = callAs(OWNER, 0, 123456789, 987654321, 111111111, 10**15);
        require(ok && output.length == 0, "owner update");
        require(uint256(vm.load(PROXY, s)) == ((old0 & (uint256(type(uint64).max) << 192)) | (uint256(987654321) << 96) | 111111111), "word0");
        require(uint256(vm.load(PROXY, bytes32(uint256(s) + 1))) == ((old1 & ~(uint256(type(uint64).max) << 184)) | (uint256(10**15) << 184)), "word1");
        require(uint256(vm.load(PROXY, bytes32(uint256(s) + 2))) == ((old2 & ~uint256(type(uint128).max)) | 123456789), "word2");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY, "log count");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == EVENT_TOPIC && logs[0].topics[1] == bytes32(0), "log topics");
        require(keccak256(logs[0].data) == keccak256(abi.encode(uint128(123456789), uint96(987654321), uint96(111111111), uint64(10**15))), "log data");
    }
    function testStatefulSecondUpdateAndGetter() public {
        (bool firstOk,) = callAs(OWNER, 0, 123456789, 987654321, 111111111, 10**15);
        require(firstOk, "first update");
        (bool secondOk,) = callAs(OWNER, 0, 42, 77, 99, 0);
        require(secondOk, "second update");
        uint256[8] memory values = getter(0);
        require(values[0] == 99 && values[1] == 77 && values[6] == 0 && values[7] == 42, "persisted getter");
        require(values[3] == 1000 && values[4] == 10**25, "unrelated fields");
    }
    function testOwnerSecondInstrument() public {
        bytes32 s = slotFor(1);
        (bool ok,) = callAs(OWNER, 1, 1, 2, 3, 4);
        require(ok, "second instrument");
        require(uint256(vm.load(PROXY, s)) == (uint256(2) << 96) | 3, "second word0");
        require(uint256(vm.load(PROXY, bytes32(uint256(s) + 1))) == uint256(4) << 184, "second word1");
        require(uint256(vm.load(PROXY, bytes32(uint256(s) + 2))) == 1, "second word2");
    }
    function checkError(address who, uint32 id, uint128 first, uint96 second, uint96 third, uint64 fourth, bytes4 errorSelector) internal {
        (bool ok, bytes memory output) = callAs(who, id, first, second, third, fourth);
        require(!ok && output.length == 4 && bytes4(output) == errorSelector, "wrong error");
    }
    function testOutsiderRejected() public { checkError(address(0xbeef), 0, 1, 2, 3, 4, 0x30cd7471); }
    function testKeeperRejected() public { checkError(KEEPER, 0, 1, 2, 3, 4, 0x30cd7471); }
    function testInvalidInstrument() public { checkError(OWNER, 2, 1, 2, 3, 4, 0x67207a88); }
    function testZeroFirst() public { checkError(OWNER, 0, 0, 2, 3, 4, 0xb0cb274d); }
    function testZeroThird() public { checkError(OWNER, 0, 1, 2, 0, 4, 0xb0cb274d); }
    function testRateUpperBound() public { checkError(OWNER, 0, 1, 2, 3, 10**18, 0xb0cb274d); }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    contracts = manifest["contracts"]
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        contract = contracts[address]
        code = (ATLAS / contract["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == contract["sha256"]
        runtimes[label] = code
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-instrument-admin-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ExchangeInstrumentAdmin.t.sol").write_text(TEST_SOURCE)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("instrument admin replay failed: " + output[-4000:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "selector": SETTER, "event_topic": EVENT,
        "runtime_hashes": {label: contracts[address]["sha256"] for label, address in
                           (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
        "test_names": sorted(passed), "forge_result": f"{len(passed)} passed, 0 failed",
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "stateful_case": "two committed updates followed by the pinned getter"
    }, indent=2) + "\n")
    behavior = json.loads(BEHAVIOR.read_text())
    behavior["local_replay"] = "../../artifacts/exchange_instrument_admin_local/replay.json"
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(len(passed), "exact-runtime instrument admin tests passed")


if __name__ == "__main__":
    main()
