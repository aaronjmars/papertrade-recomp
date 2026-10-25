#!/usr/bin/env python3
"""Compare BatchExecutor tuple field 4 on exact-runtime call paths."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_batch_control_local import ATLAS, IMPLEMENTATION, PROXY, TEST_SOURCE

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "batch_executor_field4_local" / "replay.json"

MOCKS = '''
contract Field4SuccessTarget {
    uint256 public calls;
    event Hit(bytes data);
    fallback() external payable {
        calls++;
        emit Hit(msg.data);
        assembly { mstore(0, 42) return(0, 32) }
    }
}
contract Field4FailureTarget {
    fallback() external payable {
        assembly { mstore(0, shl(224, 0xdeadbeef)) revert(0, 4) }
    }
}
'''

TESTS = '''
    struct Field4Call { address target; bytes data; bool continueOnFailure; bytes32 field4; bytes32 intentId; }
    bytes32 constant EXECUTED_TOPIC = keccak256("CallExecuted(bytes32,uint256,bytes32,bool,bytes)");
    bytes32 constant SUMMARY_TOPIC = keccak256("BatchExecuted(bytes32,uint256,uint256,uint256,uint256)");
    bytes32 constant REJECTED_TOPIC = keccak256("CallRejected(bytes32,uint256,bytes32,bytes)");
    bytes32 constant INTENT = bytes32(uint256(123));
    function fieldValues() internal pure returns (bytes32[5] memory values) {
        values[0] = bytes32(0);
        values[1] = bytes32(uint256(1));
        values[2] = keccak256(abi.encode(uint256(42)));
        values[3] = keccak256(hex"ec6783f0");
        values[4] = bytes32(uint256(type(uint128).max));
    }
    function executeOne(address target, bool continuing, bytes32 field4)
        internal returns (bool ok, bytes memory out, Vm.Log[] memory logs, bytes32 batchId) {
        Field4Call[] memory calls = new Field4Call[](1);
        calls[0] = Field4Call(target, hex"ec6783f0", continuing, field4, INTENT);
        bytes memory data = abi.encodeWithSelector(bytes4(0x251fb27d), calls);
        batchId = keccak256(data);
        vm.recordLogs();
        (ok, out) = callAs(RELAYER, data);
        logs = vm.getRecordedLogs();
    }
    function checkSummary(Vm.Log memory summary, bytes32 batchId, uint256 successes, uint256 failures) internal pure {
        require(summary.emitter == PROXY && summary.topics.length == 2, "summary envelope");
        require(summary.topics[0] == SUMMARY_TOPIC && summary.topics[1] == batchId, "summary topics");
        require(keccak256(summary.data) == keccak256(abi.encode(uint256(1), successes, failures, uint256(0))), "summary fields");
    }
    function checkExecuted(Vm.Log memory entry, bytes32 batchId, bool success, bytes memory expectedReturn) internal pure {
        require(entry.emitter == PROXY && entry.topics.length == 4, "result envelope");
        require(entry.topics[0] == EXECUTED_TOPIC && entry.topics[1] == batchId, "result topics");
        require(entry.topics[2] == bytes32(0) && entry.topics[3] == INTENT, "result index or intent");
        (bool gotSuccess, bytes memory gotReturn) = abi.decode(entry.data, (bool, bytes));
        require(gotSuccess == success && keccak256(gotReturn) == keccak256(expectedReturn), "result data");
    }
    function testField4SuccessVariants() public {
        vm.etch(EXCHANGE, type(Field4SuccessTarget).runtimeCode);
        bytes32[5] memory values = fieldValues();
        for (uint256 i; i < values.length; ++i) {
            (bool ok, bytes memory out, Vm.Log[] memory logs, bytes32 batchId) = executeOne(EXCHANGE, true, values[i]);
            require(ok && out.length == 0 && logs.length == 3, "success call");
            require(logs[0].emitter == EXCHANGE && logs[0].topics[0] == keccak256("Hit(bytes)"), "inner success call");
            require(keccak256(abi.decode(logs[0].data, (bytes))) == keccak256(hex"ec6783f0"), "inner calldata");
            checkExecuted(logs[1], batchId, true, abi.encode(uint256(42)));
            checkSummary(logs[2], batchId, 1, 0);
            require(uint256(vm.load(EXCHANGE, bytes32(0))) == i + 1, "inner call count");
        }
    }
    function testField4FailureVariants() public {
        vm.etch(EXCHANGE, type(Field4FailureTarget).runtimeCode);
        bytes32[5] memory values = fieldValues();
        for (uint256 i; i < values.length; ++i) {
            (bool ok, bytes memory out, Vm.Log[] memory logs, bytes32 batchId) = executeOne(EXCHANGE, true, values[i]);
            require(ok && out.length == 0 && logs.length == 2, "continued failure");
            checkExecuted(logs[0], batchId, false, hex"deadbeef");
            checkSummary(logs[1], batchId, 0, 1);
        }
    }
    function testField4RejectedVariants() public {
        bytes32[5] memory values = fieldValues();
        for (uint256 i; i < values.length; ++i) {
            (bool ok, bytes memory out, Vm.Log[] memory logs, bytes32 batchId) = executeOne(address(1), true, values[i]);
            require(ok && out.length == 0 && logs.length == 2, "rejected call");
            require(logs[0].emitter == PROXY && logs[0].topics.length == 4, "rejection envelope");
            require(logs[0].topics[0] == REJECTED_TOPIC && logs[0].topics[1] == batchId, "rejection topics");
            require(logs[0].topics[2] == bytes32(0) && logs[0].topics[3] == INTENT, "rejection index or intent");
            require(keccak256(abi.decode(logs[0].data, (bytes))) == keccak256(bytes("BatchExecutor: selector not allowed")), "rejection reason");
            checkSummary(logs[1], batchId, 0, 1);
        }
    }
    function testField4NonContinuingFailure() public {
        vm.etch(EXCHANGE, type(Field4FailureTarget).runtimeCode);
        (bool ok, bytes memory out, Vm.Log[] memory logs,) = executeOne(EXCHANGE, false, bytes32(uint256(1)));
        require(!ok && out.length >= 4 && bytes4(out) == bytes4(0x651ab1b3), "failure error");
        require(logs.length == 0, "failed batch logs");
        bytes memory payload = new bytes(out.length - 4);
        for (uint256 i; i < payload.length; ++i) payload[i] = out[i + 4];
        (uint256 index, bytes memory reason) = abi.decode(payload, (uint256, bytes));
        require(index == 0 && keccak256(reason) == keccak256(hex"deadbeef"), "failure payload");
    }
'''


def source():
    assert TEST_SOURCE.count("contract BatchControlTest {") == 1
    assert TEST_SOURCE.count("    function testPinnedGetters()") == 1
    return (TEST_SOURCE.replace("contract BatchControlTest {", MOCKS + "contract BatchControlTest {")
            .replace("    function testPinnedGetters()", TESTS + "    function testPinnedGetters()"))


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    test_source = source()
    with tempfile.TemporaryDirectory(prefix="papertrade-batch-field4-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "BatchField4.t.sol").write_text(test_source)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-test", "testField4", "-vv"],
                             capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (testField4\w+)\(\)", output))
    expected = sorted(re.findall(r"function (testField4\w+)\(", TESTS))
    if run.returncode or passed != expected:
        raise RuntimeError(output)
    record = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": {label: manifest["contracts"][address]["sha256"]
                           for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
        "source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "field4_values": ["zero", "one", "keccak256(success return uint256 42)",
                          "keccak256(inner calldata)", "uint128 max"],
        "successful_call_cases": 5, "continued_failure_cases": 5, "rejected_call_cases": 5,
        "noncontinuing_failure_cases": 1,
        "test_count": len(passed), "passed_tests": passed,
        "finding": "For these sampled branches, field4 changes only the batch ID because it is part of calldata; call targets, return data, result events, and summary counters remain the same. This does not prove the field is globally unused.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, indent=2) + "\n")
    print(f"BatchExecutor field4: {len(passed)} exact-runtime tests, 16 cases passed")


if __name__ == "__main__":
    main()
