#!/usr/bin/env python3
"""Probe three unobserved selectors in the exact pinned Exchange linked library."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
OUT = ROOT / "artifacts" / "exchange_library_remaining_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_library_remaining_behavior.json"
TEST_NAMES = {"testProbeQueue", "testProbeAppendAndPartial", "testProbeInvalidAmounts", "testProbePure", "testProbePurePriorOverflow", "testProbePureZeroStart"}
PURE_VECTORS = [
    [0,100,110,0,10**6,0,0], [0,100,120,0,10**6,0,0], [0,100,110,0,2*10**6,0,0],
    [10**18,100,110,0,10**6,0,0], [10**18,100,110,10**18,10**6,10**18,10**18],
    [10**18,100,110,10**6,10**6,0,0], [10**18,100,110,0,10**18,10**18,10**18],
    [10**18,100,200,0,10**18,0,0], [0,100,110,0,10**18,10**18,10**18],
    [2*10**18,100,110,0,10**18,10**18,10**18], [10**18,100,105,0,10**18,10**18,10**18],
    [10**18,100,110,0,5*10**17,10**18,10**18], [10**18,100,110,0,2*10**18,10**18,10**18],
    [10**18,100,110,0,10**18,0,10**18], [10**18,100,110,0,10**18,10**18,0],
    [10**18,100,110,0,10**18,5*10**17,10**18], [10**18,100,110,0,10**18,10**18,5*10**17],
    [10**18,100,110,1,10**18,10**18,10**18], [10**18,100,110,10**18,10**18,10**18,10**18],
    [10**18,100,100,0,10**18,10**18,10**18],
    [10**18,100,110,5*10**17,10**18,10**18,10**18],
    [10**18,100,110,9*10**17,10**18,10**18,10**18],
    [10**18,100,110,10**18-1,10**18,10**18,10**18],
    [10**18,100,110,10**18,2*10**18,10**18,10**18],
    [10**18,100,110,0,10**17,10**18,10**18],
    [10**18,100,110,0,10**8,10**18,10**18],
    [10**18,100,110,0,10**6,10**18,10**18],
    [3*10**18,80,100,0,7*10**17,8*10**17,4*10**17],
    [10**18,200,220,0,10**18,10**18,10**18],
    [10**18,100,110,0,10**18,2*10**18,3*10**18],
    [10**18,100,110,0,10**18,10**17,3*10**18],
    [10**18,100,110,0,10**18,10**18,1],
    [2*10**18,100,110,5*10**17,10**18,10**18,10**18],
    [7*10**18,100,110,1,10**18,10**18,10**18],
    [2*10**18,100,110,10**18-1,10**18,10**18,10**18],
    [10**18,100,110,0,10**18,10**18,10**6],
    [10**18,110,100,0,10**18,10**18,10**18],
    [10**18,100,110,0,0,10**18,10**18],
    [3*10**18,80,100,4*10**17,7*10**17,8*10**17,4*10**17],
    [2*10**18,100,110,10**17,5*10**17,2*10**18,3*10**18],
]
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
contract DelegateHarness {
    address constant LIBRARY = address(uint160(uint256(0x00cd617f984158a4f5d287ddee0e8eb0fed204916d)));
    function exec(bytes memory data) external returns (bool, bytes memory) {
        return LIBRARY.delegatecall(data);
    }
}
contract ExchangeRemainingLibraryTest {
    event log_named_uint(string key, uint256 val);
    event log_named_bytes(string key, bytes val);
    event log_named_bytes32(string key, bytes32 val);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant LIBRARY = address(uint160(uint256(0x00cd617f984158a4f5d287ddee0e8eb0fed204916d)));
    address constant USER = address(0x1234);
    DelegateHarness harness;
    function setUp() public {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        harness = new DelegateHarness();
    }
    function nodeSlot(uint256 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(15)));
    }
    function userSlot(uint256 base) internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, base));
    }
    function assertState(uint256 head, uint256 nextId, uint256 total, uint256 userTotal, uint256 userHead, uint256 userTail) internal {
        require(uint256(vm.load(address(harness), bytes32(uint256(16)))) == head, "global head");
        require(uint256(vm.load(address(harness), bytes32(uint256(17)))) == nextId, "next id");
        require(uint256(vm.load(address(harness), bytes32(uint256(18)))) == total, "global total");
        require(uint256(vm.load(address(harness), userSlot(19))) == userTotal, "user total");
        require(uint256(vm.load(address(harness), userSlot(20))) == userHead, "user head");
        require(uint256(vm.load(address(harness), userSlot(21))) == userTail, "user tail");
    }
    function assertEvent(Vm.Log[] memory logs, bytes32 topic, uint256 amount, uint256 indexedCount) internal pure {
        require(logs.length == 1, "log count");
        require(logs[0].topics.length == indexedCount && logs[0].topics[0] == topic, "topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(USER))), "indexed user");
        require(logs[0].data.length == 32 && abi.decode(logs[0].data, (uint256)) == amount, "event amount");
    }
    function inspect(string memory label) internal {
        emit log_named_uint(string.concat(label, "-slot16"), uint256(vm.load(address(harness), bytes32(uint256(16)))));
        emit log_named_uint(string.concat(label, "-slot17"), uint256(vm.load(address(harness), bytes32(uint256(17)))));
        emit log_named_uint(string.concat(label, "-slot18"), uint256(vm.load(address(harness), bytes32(uint256(18)))));
        emit log_named_bytes32(string.concat(label, "-node1-word0"), vm.load(address(harness), nodeSlot(1)));
        emit log_named_bytes32(string.concat(label, "-node1-word1"), vm.load(address(harness), bytes32(uint256(nodeSlot(1)) + 1)));
        emit log_named_uint(string.concat(label, "-user-total"), uint256(vm.load(address(harness), userSlot(19))));
        emit log_named_uint(string.concat(label, "-user-head"), uint256(vm.load(address(harness), userSlot(20))));
        emit log_named_uint(string.concat(label, "-user-tail"), uint256(vm.load(address(harness), userSlot(21))));
    }
    function testProbeQueue() public {
        vm.store(address(harness), bytes32(uint256(17)), bytes32(uint256(1)));
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = harness.exec(abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, uint256(500)));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        emit log_named_uint("enqueue-ok", ok ? 1 : 0);
        emit log_named_bytes("enqueue-out", out);
        emit log_named_uint("enqueue-log-count", logs.length);
        for (uint256 i; i < logs.length; ++i) {
            emit log_named_bytes32("enqueue-topic0", logs[i].topics[0]);
            emit log_named_bytes("enqueue-data", logs[i].data);
        }
        require(ok && out.length == 0, "enqueue return");
        assertEvent(logs, keccak256("Enqueued(address,uint256,uint256)"), 500, 3);
        require(logs[0].topics[2] == bytes32(uint256(1)), "enqueue indexed id");
        assertState(1, 2, 500, 500, 1, 1);
        require(uint256(vm.load(address(harness), nodeSlot(1))) == uint256(uint160(USER)), "node owner");
        require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(1)) + 1))) == 500, "node amount");
        inspect("enqueue");
        vm.recordLogs();
        vm.prank(USER);
        (ok, out) = harness.exec(abi.encodeWithSelector(bytes4(0x3f4e3626), uint256(15), USER, uint256(500)));
        logs = vm.getRecordedLogs();
        emit log_named_uint("remove-ok", ok ? 1 : 0);
        emit log_named_bytes("remove-out", out);
        emit log_named_uint("remove-log-count", logs.length);
        for (uint256 i; i < logs.length; ++i) {
            emit log_named_bytes32("remove-topic0", logs[i].topics[0]);
            emit log_named_bytes("remove-data", logs[i].data);
        }
        require(ok && out.length == 0, "remove return");
        assertEvent(logs, 0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d, 500, 2);
        assertState(2, 2, 0, 0, 0, 0);
        require(uint256(vm.load(address(harness), nodeSlot(1))) == uint256(uint160(USER)), "owner tombstone");
        require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(1)) + 1))) == 0, "removed amount");
        inspect("remove");
    }
    function testProbeAppendAndPartial() public {
        vm.store(address(harness), bytes32(uint256(17)), bytes32(uint256(1)));
        vm.prank(USER);
        harness.exec(abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, uint256(500)));
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = harness.exec(abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, uint256(300)));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        emit log_named_uint("append-ok", ok ? 1 : 0);
        emit log_named_bytes("append-out", out);
        emit log_named_uint("append-log-count", logs.length);
        emit log_named_bytes32("append-node2-word0", vm.load(address(harness), nodeSlot(2)));
        emit log_named_bytes32("append-node2-word1", vm.load(address(harness), bytes32(uint256(nodeSlot(2)) + 1)));
        require(ok && out.length == 0, "append return");
        assertEvent(logs, keccak256("Enqueued(address,uint256,uint256)"), 300, 3);
        require(logs[0].topics[2] == bytes32(uint256(2)), "append indexed id");
        assertState(1, 3, 800, 800, 1, 2);
        require(uint256(vm.load(address(harness), nodeSlot(1))) == uint256(uint160(USER)) + (uint256(2) << 160), "node1 next link");
        require(uint256(vm.load(address(harness), nodeSlot(2))) == uint256(uint160(USER)) + (uint256(1) << 208), "node2 prev link");
        require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(2)) + 1))) == 300, "node2 amount");
        inspect("append");
        vm.recordLogs();
        vm.prank(USER);
        (ok, out) = harness.exec(abi.encodeWithSelector(bytes4(0x3f4e3626), uint256(15), USER, uint256(200)));
        logs = vm.getRecordedLogs();
        emit log_named_uint("partial-ok", ok ? 1 : 0);
        emit log_named_bytes("partial-out", out);
        emit log_named_uint("partial-log-count", logs.length);
        for (uint256 i; i < logs.length; ++i) {
            emit log_named_bytes32("partial-topic0", logs[i].topics[0]);
            emit log_named_bytes("partial-data", logs[i].data);
        }
        emit log_named_bytes32("partial-node2-word0", vm.load(address(harness), nodeSlot(2)));
        emit log_named_bytes32("partial-node2-word1", vm.load(address(harness), bytes32(uint256(nodeSlot(2)) + 1)));
        require(ok && out.length == 0, "partial return");
        assertEvent(logs, 0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d, 200, 2);
        assertState(1, 3, 600, 600, 1, 2);
        require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(1)) + 1))) == 500, "node1 unchanged");
        require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(2)) + 1))) == 100, "tail reduced");
        inspect("partial");
    }
    function testProbeInvalidAmounts() public {
        vm.store(address(harness), bytes32(uint256(17)), bytes32(uint256(1)));
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = harness.exec(abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, uint256(0)));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        emit log_named_uint("enqueue-zero-ok", ok ? 1 : 0);
        emit log_named_bytes("enqueue-zero-out", out);
        emit log_named_uint("enqueue-zero-log-count", logs.length);
        require(ok && out.length == 0 && logs.length == 0, "zero enqueue no-op");
        assertState(0, 1, 0, 0, 0, 0);
        inspect("zero");
        vm.prank(USER);
        harness.exec(abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, uint256(500)));
        vm.recordLogs();
        vm.prank(USER);
        (ok, out) = harness.exec(abi.encodeWithSelector(bytes4(0x3f4e3626), uint256(15), USER, uint256(501)));
        logs = vm.getRecordedLogs();
        emit log_named_uint("remove-over-ok", ok ? 1 : 0);
        emit log_named_bytes("remove-over-out", out);
        emit log_named_uint("remove-over-log-count", logs.length);
        if (logs.length > 0) emit log_named_bytes("remove-over-data", logs[0].data);
        require(ok && out.length == 0, "over remove return");
        assertEvent(logs, 0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d, 501, 2);
        assertState(2, 2, 0, 0, 0, 0);
        require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(1)) + 1))) == 0, "over remove clears node");
        inspect("over");
    }
    function testProbePureZeroStart() public {
        (bool ok, bytes memory out) = LIBRARY.staticcall(abi.encodeWithSelector(bytes4(0xb67f3dd7),
            uint256(1e18), uint256(0), uint256(110), uint256(0), uint256(1e18), uint256(1e18), uint256(1e18)));
        require(!ok && out.length == 36 && bytes4(out) == bytes4(0x4e487b71), "zero start revert");
        uint256 panicCode;
        assembly { panicCode := mload(add(out, 36)) }
        require(panicCode == 0x12, "zero start panic code");
    }
    function testProbePurePriorOverflow() public {
        (bool ok, bytes memory out) = LIBRARY.staticcall(abi.encodeWithSelector(bytes4(0xb67f3dd7),
            uint256(1e18), uint256(100), uint256(110), uint256(1e18 + 1), uint256(1e18), uint256(1e18), uint256(1e18)));
        require(!ok && out.length == 36 && bytes4(out) == bytes4(0x4e487b71), "prior overflow revert");
        uint256 panicCode;
        assembly { panicCode := mload(add(out, 36)) }
        require(panicCode == 0x11, "prior overflow panic code");
    }
    function testProbePure() public {
        uint256[7][40] memory vectors = [
            [uint256(0), 100, 110, 0, 1e6, 0, 0],
            [uint256(0), 100, 120, 0, 1e6, 0, 0],
            [uint256(0), 100, 110, 0, 2e6, 0, 0],
            [uint256(1e18), 100, 110, 0, 1e6, 0, 0],
            [uint256(1e18), 100, 110, 1e18, 1e6, 1e18, 1e18],
            [uint256(1e18), 100, 110, 1e6, 1e6, 0, 0],
            [uint256(1e18), 100, 110, 0, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 200, 0, 1e18, 0, 0],
            [uint256(0), 100, 110, 0, 1e18, 1e18, 1e18],
            [uint256(2e18), 100, 110, 0, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 105, 0, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 5e17, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 2e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 1e18, 0, 1e18],
            [uint256(1e18), 100, 110, 0, 1e18, 1e18, 0],
            [uint256(1e18), 100, 110, 0, 1e18, 5e17, 1e18],
            [uint256(1e18), 100, 110, 0, 1e18, 1e18, 5e17],
            [uint256(1e18), 100, 110, 1, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 1e18, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 100, 0, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 5e17, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 9e17, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 1e18 - 1, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 1e18, 2e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 1e17, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 1e8, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 1e6, 1e18, 1e18],
            [uint256(3e18), 80, 100, 0, 7e17, 8e17, 4e17],
            [uint256(1e18), 200, 220, 0, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 1e18, 2e18, 3e18],
            [uint256(1e18), 100, 110, 0, 1e18, 1e17, 3e18],
            [uint256(1e18), 100, 110, 0, 1e18, 1e18, 1],
            [uint256(2e18), 100, 110, 5e17, 1e18, 1e18, 1e18],
            [uint256(7e18), 100, 110, 1, 1e18, 1e18, 1e18],
            [uint256(2e18), 100, 110, 1e18 - 1, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 1e18, 1e18, 1e6],
            [uint256(1e18), 110, 100, 0, 1e18, 1e18, 1e18],
            [uint256(1e18), 100, 110, 0, 0, 1e18, 1e18],
            [uint256(3e18), 80, 100, 4e17, 7e17, 8e17, 4e17],
            [uint256(2e18), 100, 110, 1e17, 5e17, 2e18, 3e18]
        ];
        for (uint256 i; i < vectors.length; ++i) {
            (bool ok, bytes memory out) = LIBRARY.staticcall(abi.encodeWithSelector(bytes4(0xb67f3dd7),
                vectors[i][0], vectors[i][1], vectors[i][2], vectors[i][3], vectors[i][4], vectors[i][5], vectors[i][6]));
            require(ok && out.length == 32, "math return");
            emit log_named_uint("pure-index", i);
            emit log_named_uint("pure-ok", ok ? 1 : 0);
            emit log_named_bytes("pure-out", out);
        }
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    row = manifest["contracts"][LIBRARY]
    code = (ATLAS / row["runtime_file"]).read_text().strip()
    assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-library-untraced-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ExchangeRemainingLibrary.t.sol").write_text(TEST_SOURCE)
        (project / "runtime" / "Library.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vvv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != TEST_NAMES:
        raise RuntimeError("library probes failed: " + output[-4500:])
    pure = re.findall(r"pure-index: (\d+)\s+pure-ok: (\d+)\s+pure-out: 0x([0-9a-f]{64})", output)
    assert len(pure) == len(PURE_VECTORS) and [int(row[0]) for row in pure] == list(range(len(PURE_VECTORS)))
    assert all(row[1] == "1" for row in pure)
    results = [int(row[2], 16) for row in pure]
    assert results[6] == 90909008264537941 and results[9] == 2 * results[6]
    assert results[14] == 90909090909090909 and results[19] == 0
    WAD = 10**18
    def reconstructed_formula(v):
        amount, start, end, prior, factor, denominator, adjustment = v
        if prior > WAD:
            raise ArithmeticError("prior rate exceeds 1e18")
        if end == start or factor == 0 or denominator == 0 or prior == WAD:
            return 0
        if start == 0:
            raise ZeroDivisionError("start price is zero")
        price_move = abs(end - start) * WAD // start
        weighted_move = price_move * factor // WAD
        if weighted_move == 0:
            return 0
        inverse = WAD * WAD // weighted_move
        adjustment_denominator = (10**6 * price_move) * denominator // WAD
        if adjustment_denominator == 0:
            return 0
        adjustment_term = adjustment * WAD // adjustment_denominator
        total_denominator = WAD + inverse + adjustment_term
        adjusted_rate = (WAD - prior) * WAD // total_denominator
        return amount * adjusted_rate // WAD
    predicted = [reconstructed_formula(v) for v in PURE_VECTORS]
    mismatches = [{"index": i, "actual": actual, "formula": value}
                  for i, (actual, value) in enumerate(zip(results, predicted)) if actual != value]
    assert not mismatches, mismatches
    trace_path = ROOT / "artifacts" / "exchange_library_remaining_local" / "opcode_trace17.json"
    trace_artifact = json.loads(trace_path.read_text())
    assert trace_artifact["pin"] == manifest["block"] and trace_artifact["library"] == LIBRARY
    assert trace_artifact["calldata"] == "0xb67f3dd7" + "".join(f"{x:064x}" for x in PURE_VECTORS[17])
    trace = trace_artifact["trace"]
    assert not trace["failed"] and int(trace["returnValue"], 16) == results[17]
    opcode_checkpoints = {0x1123: {0: 10**17}, 0x1161: {0: 10**19, 1: 10**13},
                          0x11b6: {0: 11000010000000000000, 1: (WAD - 1) * WAD},
                          0x11bc: {0: results[17]}}
    for pc, values in opcode_checkpoints.items():
        steps = [step for step in trace["structLogs"] if step["pc"] == pc]
        assert len(steps) == 1, (hex(pc), len(steps))
        for depth, expected in values.items():
            assert int(steps[0]["stack"][-1-depth], 16) == expected, (hex(pc), depth)
    replay = {"pin": manifest["block"], "block_hash": manifest["block_hash"], "library": LIBRARY,
              "runtime_sha256": row["sha256"], "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
              "forge_result": "6 passed, 0 failed", "test_names": sorted(passed),
              "math_vectors": [{"inputs": vector, "output": result, "formula_output": value}
                               for vector, result, value in zip(PURE_VECTORS, results, predicted)],
              "formula_mismatches": mismatches,
              "opcode_trace": "opcode_trace17.json",
              "opcode_trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(replay, indent=2) + "\n")
    behavior = {"pin": manifest["block"], "block_hash": manifest["block_hash"], "library": LIBRARY,
                "runtime_sha256": row["sha256"], "delegatecall_storage_owner": "local harness with exact pinned library runtime",
                "mapping_base": 15, "local_replay": "../../artifacts/exchange_library_remaining_local/replay.json",
                "selector_behaviors": {
                    "0x18958ce2": "Enqueue amount for user: zero is no-op; positive creates node, updates global/user totals, appends links, emits Enqueued",
                    "0x3f4e3626": "Remove requested amount from user queue tail: partial removal reduces newest node first; full removal clears node amount and advances head; emitted amount is request even if above queued balance in synthetic state",
                    "0xb67f3dd7": "Seven-word arithmetic: 40 successful staticcall vectors and a pinned opcode trace match the reconstructed integer sequence; zero, nonzero, and input-dependent rate branches sampled"},
                "observed_abi_arguments": {"0x3f4e3626": "uint256,address,uint256"},
                "event_topics": {"enqueue": "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7",
                                 "remove": "0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d"},
                "state_examples": {"enqueue_500": {"head": 1, "next_id": 2, "global_total": 500, "user_total": 500, "user_head": 1, "user_tail": 1},
                                   "append_300": {"head": 1, "next_id": 3, "global_total": 800, "user_total": 800, "user_head": 1, "user_tail": 2},
                                   "remove_tail_200": {"head": 1, "next_id": 3, "global_total": 600, "user_total": 600, "node_1_amount": 500, "node_2_amount": 100},
                                   "remove_501_from_500": {"head": 2, "next_id": 2, "global_total": 0, "user_total": 0, "event_amount": 501}},
                "math_vector_count": len(results), "math_nonzero_count": sum(bool(x) for x in results),
                "math_formula": "delta=abs(end-start); r=floor(delta*1e18/start); m=floor(r*factor/1e18); inverse=floor(1e36/m); a=floor((1e6*r)*denominator/1e18); adjustment_term=floor(adjustment*1e18/a); D=1e18+inverse+adjustment_term; rate=floor((1e18-prior)*1e18/D); output=floor(amount*rate/1e18)",
                "math_formula_branch_conditions": "Equal prices, zero factor, zero denominator, or prior==1e18 return zero in tested states; falling prices use absolute delta; start==0 panics with code 0x12 and prior>1e18 panics with code 0x11. Extreme uint256 arithmetic remains uncharacterized",
                "math_formula_exact_vectors": len(results) - len(mismatches),
                "math_formula_mismatches": mismatches,
                "math_opcode_trace": "../../artifacts/exchange_library_remaining_local/opcode_trace17.json",
                "math_panic_branches": [{"input": "start=0,end=110", "selector": "0x4e487b71", "code": "0x12"},
                                        {"input": "prior=1e18+1", "selector": "0x4e487b71", "code": "0x11"}],
                "math_opcode_checkpoints": {hex(pc): {str(depth): value for depth, value in values.items()}
                                            for pc, values in opcode_checkpoints.items()},
                "source_names": "unresolved", "historical_calls_for_these_selectors": 0}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(f"6 exact pinned-library tests passed; exact arithmetic formula matches {len(results)} vectors and archived opcode checkpoints")


if __name__ == "__main__":
    main()
