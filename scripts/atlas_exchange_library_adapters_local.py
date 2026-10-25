#!/usr/bin/env python3
"""Verify four Exchange-to-library adapters using exact Exchange runtime and a spy library."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "exchange_library_adapters_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_library_adapters_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
ADAPTERS = {"0x4a4d9eea": "0xca02ff91", "0xae4daf4e": "0x2448a553",
            "0x753a369c": "0x3cf4208d", "0x827ad94c": "0x32db40c9"}
TEST_NAMES = ["testForwardAndReturn", "testMalformedAddress", "testTooShort", "testLiveLibraryDefaultCalls",
              "testLiveLibrarySyntheticNode", "testReturnWidth", "testLibraryErrorBubbles"]

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
    function record() external;
    function accesses(address) external returns (bytes32[] memory, bytes32[] memory);
}
contract SpyLibrary {
    event Routed(bytes data);
    fallback() external payable {
        emit Routed(msg.data);
        assembly {
            mstore(0, 11)
            mstore(0x20, 22)
            mstore(0x40, 33)
            return(0, 0x60)
        }
    }
}
contract SpyLibraryFour {
    fallback() external payable {
        assembly {
            mstore(0, 11)
            mstore(0x20, 22)
            mstore(0x40, 33)
            mstore(0x60, 44)
            return(0, 0x80)
        }
    }
}
contract SpyLibraryShort {
    fallback() external payable {
        assembly {
            mstore(0, 11)
            mstore(0x20, 22)
            return(0, 0x40)
        }
    }
}
contract SpyLibraryRevert {
    fallback() external payable {
        assembly {
            mstore(0, shl(224, 0xdeadbeef))
            revert(0, 4)
        }
    }
}
contract ExchangeLibraryAdaptersTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant LIBRARY = address(uint160(uint256(0x00cd617f984158a4f5d287ddee0e8eb0fed204916d)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant USER = address(0x1234);
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    function setUp() public {
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.etch(LIBRARY, type(SpyLibrary).runtimeCode);
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
    }
    function route(bytes memory outer, bytes memory expected) internal {
        vm.recordLogs();
        (bool ok, bytes memory out) = PROXY.call(outer);
        require(ok, "wrapper failed");
        require(keccak256(out) == keccak256(abi.encode(uint256(11), uint256(22), uint256(33))), "return changed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY, "spy log count");
        require(logs[0].topics.length == 1 && logs[0].topics[0] == keccak256("Routed(bytes)"), "spy topic");
        bytes memory actual = abi.decode(logs[0].data, (bytes));
        require(keccak256(actual) == keccak256(expected), "forwarded calldata");
    }
    function testForwardAndReturn() public {
        route(abi.encodeWithSelector(bytes4(0x4a4d9eea), USER, uint256(101), uint256(202)),
              abi.encodeWithSelector(bytes4(0xca02ff91), uint256(15), USER, uint256(101), uint256(202)));
        route(abi.encodeWithSelector(bytes4(0xae4daf4e), USER, uint256(101), uint256(202)),
              abi.encodeWithSelector(bytes4(0x2448a553), uint256(15), USER, uint256(101), uint256(202), uint256(1e18)));
        route(abi.encodeWithSelector(bytes4(0x753a369c), USER, uint256(101), uint256(202), uint256(303)),
              abi.encodeWithSelector(bytes4(0x3cf4208d), uint256(15), USER, uint256(101), uint256(202), uint256(303), uint256(1e18)));
        route(abi.encodeWithSelector(bytes4(0x827ad94c), USER, uint256(101), uint256(202), uint256(303)),
              abi.encodeWithSelector(bytes4(0x32db40c9), uint256(15), USER, uint256(101), uint256(202), uint256(303)));
    }
    function testMalformedAddress() public {
        vm.recordLogs();
        bytes memory bad = abi.encodePacked(bytes4(0x4a4d9eea), bytes32(uint256(1) << 160), bytes32(uint256(101)), bytes32(uint256(202)));
        (bool ok, bytes memory out) = PROXY.call(bad);
        require(!ok && out.length == 0, "address decoder");
        require(vm.getRecordedLogs().length == 0, "malformed delegated");
    }
    function testTooShort() public {
        vm.recordLogs();
        (bool ok, bytes memory out) = PROXY.call(abi.encodePacked(bytes4(0x827ad94c), bytes32(uint256(uint160(USER)))));
        require(!ok && out.length == 0, "short decoder");
        require(vm.getRecordedLogs().length == 0, "short delegated");
    }
    function outer(uint256 i) internal pure returns (bytes memory) {
        bytes4[4] memory selectors = [bytes4(0x4a4d9eea), bytes4(0xae4daf4e), bytes4(0x753a369c), bytes4(0x827ad94c)];
        return i < 2
            ? abi.encodeWithSelector(selectors[i], USER, uint256(101), uint256(202))
            : abi.encodeWithSelector(selectors[i], USER, uint256(101), uint256(202), uint256(303));
    }
    function testReturnWidth() public {
        for (uint256 i; i < 4; ++i) {
            vm.etch(LIBRARY, type(SpyLibraryFour).runtimeCode);
            (bool ok, bytes memory out) = PROXY.call(outer(i));
            require(ok && keccak256(out) == keccak256(abi.encode(uint256(11), uint256(22), uint256(33))), "four-word return");
            vm.etch(LIBRARY, type(SpyLibraryShort).runtimeCode);
            (ok, out) = PROXY.call(outer(i));
            require(!ok && out.length == 0, "short library return");
        }
    }
    function testLibraryErrorBubbles() public {
        vm.etch(LIBRARY, type(SpyLibraryRevert).runtimeCode);
        for (uint256 i; i < 4; ++i) {
            (bool ok, bytes memory out) = PROXY.call(outer(i));
            require(!ok && out.length == 4 && bytes4(out) == bytes4(0xdeadbeef), "library revert bubble");
        }
    }
    function testLiveLibraryDefaultCalls() public {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        bytes4[4] memory selectors = [bytes4(0x4a4d9eea), bytes4(0xae4daf4e), bytes4(0x753a369c), bytes4(0x827ad94c)];
        bytes32 nodeSlot = keccak256(abi.encode(uint256(101), uint256(15)));
        for (uint256 i; i < selectors.length; ++i) {
            bytes memory data = i == 0 || i == 1
                ? abi.encodeWithSelector(selectors[i], USER, uint256(101), uint256(202))
                : abi.encodeWithSelector(selectors[i], USER, uint256(101), uint256(202), uint256(303));
            vm.record();
            vm.prank(USER);
            (bool ok, bytes memory out) = PROXY.call(data);
            (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(PROXY);
            require(writes.length == 0, "default wrote storage");
            require(reads[0] == IMPLEMENTATION_SLOT, "proxy implementation read");
            if (i < 2) {
                require(ok && keccak256(out) == keccak256(abi.encode(uint256(0), uint256(0), uint256(0))), "default zero return");
                require(reads.length == 2 && reads[1] == nodeSlot, "default node lookup");
            } else {
                require(!ok && out.length == 4 && bytes4(out) == bytes4(0x5b6d2b7a), "default raw error");
                if (i == 2) require(reads.length == 3 && reads[1] == bytes32(uint256(nodeSlot) + 1) && reads[2] == nodeSlot, "range node lookup");
                else require(reads.length == 2 && reads[1] == bytes32(uint256(17)), "next id lookup");
            }
        }
    }
    function testLiveLibrarySyntheticNode() public {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        bytes4[4] memory selectors = [bytes4(0x4a4d9eea), bytes4(0xae4daf4e), bytes4(0x753a369c), bytes4(0x827ad94c)];
        bytes32 nodeSlot = keccak256(abi.encode(uint256(101), uint256(15)));
        bytes32 queuedSlot = keccak256(abi.encode(USER, uint256(19)));
        bytes32 userHeadSlot = keccak256(abi.encode(USER, uint256(20)));
        bytes32 userTailSlot = keccak256(abi.encode(USER, uint256(21)));
        for (uint256 i; i < selectors.length; ++i) {
            vm.store(PROXY, nodeSlot, bytes32(uint256(uint160(USER))));
            vm.store(PROXY, bytes32(uint256(nodeSlot) + 1), bytes32(uint256(500)));
            vm.store(PROXY, bytes32(uint256(16)), bytes32(uint256(101)));
            vm.store(PROXY, bytes32(uint256(17)), bytes32(uint256(102)));
            vm.store(PROXY, bytes32(uint256(18)), bytes32(uint256(500)));
            vm.store(PROXY, queuedSlot, bytes32(uint256(500)));
            vm.store(PROXY, userHeadSlot, bytes32(uint256(101)));
            vm.store(PROXY, userTailSlot, bytes32(uint256(101)));
            bytes memory data = i == 0 || i == 1
                ? abi.encodeWithSelector(selectors[i], USER, uint256(101), uint256(202))
                : abi.encodeWithSelector(selectors[i], USER, uint256(101), uint256(202), uint256(303));
            vm.record();
            vm.prank(USER);
            (bool ok, bytes memory out) = PROXY.call(data);
            (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(PROXY);
            require(writes.length == 0, "synthetic wrote storage");
            if (i < 2) require(ok && keccak256(out) == keccak256(abi.encode(uint256(0), uint256(0), uint256(0))), "synthetic zero return");
            else require(!ok && out.length == 4 && bytes4(out) == bytes4(0x5b6d2b7a), "synthetic raw error");
            require(reads.length == (i == 0 ? 4 : i == 1 ? 6 : i == 2 ? 3 : 2), "synthetic read count");
        }
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-exchange-adapters-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ExchangeLibraryAdapters.t.sol").write_text(TEST_SOURCE)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("Exchange adapter replay failed: " + output[-4000:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                               "adapters": ADAPTERS, "test_names": sorted(passed),
                               "forge_result": "7 passed, 0 failed",
                               "runtime_hashes": {label: manifest["contracts"][address]["sha256"]
                                                  for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY))},
                               "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
                               "spy_library_scope": "Forwarding and return tests use spy bytecode at linked library address; default and synthetic node tests use exact pinned library runtime"}, indent=2) + "\n")
    BEHAVIOR.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                                   "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
                                   "linked_library": LIBRARY, "adapters": ADAPTERS,
                                   "prepend_word": 15, "append_word": {"0xae4daf4e": str(10**18), "0x753a369c": str(10**18)},
                                   "parent_result_words": 3,
                                   "return_adapter_tests": "four library words truncate to first three; two words revert empty; four-byte library error bubbles unchanged",
                                   "live_library_default_inputs": {"user": "0x0000000000000000000000000000000000001234", "node_id": 101,
                                                                   "other_words": [202, 303]},
                                   "live_library_default_results": {"0x4a4d9eea": "three zero words", "0xae4daf4e": "three zero words",
                                                                    "0x753a369c": "revert 0x5b6d2b7a", "0x827ad94c": "revert 0x5b6d2b7a"},
                                   "node_mapping_base_slot": 15,
                                   "synthetic_node_amount": 500,
                                   "synthetic_node_results": "same four outputs as empty state, with no storage writes",
                                   "local_replay": "../../artifacts/exchange_library_adapters_local/replay.json",
                                   "source_name_status": "unresolved"}, indent=2) + "\n")
    print("7 exact-Exchange-runtime adapter tests passed")


if __name__ == "__main__":
    main()
