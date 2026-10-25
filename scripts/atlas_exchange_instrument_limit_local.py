#!/usr/bin/env python3
"""Exercise the untraced Exchange instrument limit setter on pinned runtime."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "exchange_instrument_limit_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_instrument_limit_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
KEEPER = "0x3721476de31190dc1af8908026abe20efe25cf99"
SELECTOR = "0xd7c7e5fb"
EVENT = "0x62db1b2b923b6f20043c492d3586df1a823e447c63e44d15dbc90c1a3bc9fcc5"
TEST_NAMES = ["testOwnerUpdatesPackedFields", "testOwnerSecondInstrument", "testFirstMax", "testSecondMax", "testNonOwnerRejected",
              "testKeeperRejected", "testInvalidInstrument", "testZeroFirstValue",
              "testZeroSecondValue", "testThirdValueAbove120Bits"]

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
contract ExchangeInstrumentLimitTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant KEEPER = address(uint160(uint256(0x003721476de31190dc1af8908026abe20efe25cf99)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 constant EVENT_TOPIC = 0x62db1b2b923b6f20043c492d3586df1a823e447c63e44d15dbc90c1a3bc9fcc5;
    bytes4 constant SETTER = 0xd7c7e5fb;
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
    function callAs(address who, uint32 id, uint32 first, uint128 second) internal returns (bool, bytes memory) {
        vm.prank(who);
        return PROXY.call(abi.encodeWithSelector(SETTER, id, first, second));
    }
    function testOwnerUpdatesPackedFields() public {
        bytes32 s = slotFor(0);
        uint256 old0 = uint256(vm.load(PROXY, s));
        uint256 old1 = uint256(vm.load(PROXY, bytes32(uint256(s) + 1)));
        bytes32 old2 = vm.load(PROXY, bytes32(uint256(s) + 2));
        vm.recordLogs();
        (bool ok, bytes memory out) = callAs(OWNER, 0, 123, 456);
        require(ok && out.length == 0, "owner update");
        require(uint256(vm.load(PROXY, s)) == ((old0 & type(uint224).max) | (uint256(123) << 224)), "word0");
        require(uint256(vm.load(PROXY, bytes32(uint256(s) + 1))) == ((old1 & ~uint256(type(uint120).max)) | 456), "word1");
        require(vm.load(PROXY, bytes32(uint256(s) + 2)) == old2, "word2");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY, "log count");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == EVENT_TOPIC && logs[0].topics[1] == bytes32(0), "log topics");
        require(keccak256(logs[0].data) == keccak256(abi.encode(uint32(123), uint128(456))), "log data");
    }
    function testOwnerSecondInstrument() public {
        bytes32 s = slotFor(1);
        vm.store(PROXY, bytes32(uint256(s) + 1), bytes32(type(uint256).max));
        (bool ok,) = callAs(OWNER, 1, 789, 1023);
        require(ok, "second instrument");
        require(uint256(vm.load(PROXY, s)) == uint256(789) << 224, "second word0");
        require(uint256(vm.load(PROXY, bytes32(uint256(s) + 1))) == (~uint256(type(uint120).max) | 1023), "second word1");
    }
    function testFirstMax() public {
        (bool ok, bytes memory out) = callAs(OWNER, 0, type(uint32).max, 456);
        require(ok && out.length == 0, "first max");
    }
    function testSecondMax() public {
        (bool ok, bytes memory out) = callAs(OWNER, 0, 123, type(uint120).max);
        require(ok && out.length == 0, "second max");
    }
    function checkError(address who, uint32 id, uint32 first, uint128 second, bytes4 err) internal {
        (bool ok, bytes memory out) = callAs(who, id, first, second);
        require(!ok && out.length == 4 && bytes4(out) == err, "wrong error");
    }
    function testNonOwnerRejected() public { checkError(address(0xbeef), 0, 123, 456, 0x30cd7471); }
    function testKeeperRejected() public { checkError(KEEPER, 0, 123, 456, 0x30cd7471); }
    function testInvalidInstrument() public { checkError(OWNER, 2, 123, 456, 0x67207a88); }
    function testZeroFirstValue() public { checkError(OWNER, 0, 0, 456, 0xb0cb274d); }
    function testZeroSecondValue() public { checkError(OWNER, 0, 123, 0, 0xb0cb274d); }
    function testThirdValueAbove120Bits() public {
        vm.prank(OWNER);
        (bool ok, bytes memory out) = PROXY.call(abi.encodePacked(SETTER, bytes32(0), bytes32(uint256(123)), bytes32(uint256(1) << 120)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0xb0cb274d), "noncanonical third word");
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    contract_rows = manifest["contracts"]
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = contract_rows[address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-instrument-limit-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ExchangeInstrumentLimit.t.sol").write_text(TEST_SOURCE)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("instrument limit replay failed: " + output[-4000:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                               "selector": SELECTOR, "event_topic": EVENT,
                               "runtime_hashes": {label: contract_rows[address]["sha256"] for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
                               "test_names": sorted(passed), "forge_result": "10 passed, 0 failed",
                               "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest()}, indent=2) + "\n")
    BEHAVIOR.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                                   "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
                                   "selector": SELECTOR, "event_topic": EVENT,
                                   "validated_fields": ["instrument id is uint32", "first value is uint32", "second value is nonzero and at most uint120 max"],
                                   "storage_mapping_base": 7,
                                   "word0_replaced_bits": [224, 255], "word1_replaced_bits": [0, 119],
                                   "local_replay": "../../artifacts/exchange_instrument_limit_local/replay.json",
                                   "tested_errors": {"non_owner": "0x30cd7471", "invalid_instrument": "0x67207a88", "zero_value": "0xb0cb274d"},
                                   "source_name_status": "unresolved"}, indent=2) + "\n")
    print("10 exact-runtime Exchange instrument limit tests passed")


if __name__ == "__main__":
    main()
