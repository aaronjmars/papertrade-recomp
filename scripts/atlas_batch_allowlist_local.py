#!/usr/bin/env python3
"""Probe BatchExecutor target-selector allowlist against exact pinned runtimes."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_batch_control_local import ATLAS, EXCHANGE, IMPLEMENTATION, PROXY, SESSION, STAKING, TEST_SOURCE

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "batch_allowlist_local" / "replay.json"
OTHER = "0x0000000000000000000000000000000000005555"
TARGETS = {"exchange": EXCHANGE, "session": SESSION, "staking": STAKING, "other": OTHER}

MOCK = '''contract AllowlistReturn42 {
    fallback() external payable { assembly { mstore(0, 42) return(0, 32) } }
}
'''
PROBE = '''
    struct AllowCall { address target; bytes data; bool continuing; bytes32 field4; bytes32 intent; }
    bytes32 constant EXECUTED_TOPIC = keccak256("CallExecuted(bytes32,uint256,bytes32,bool,bytes)");
    bytes32 constant REJECTED_TOPIC = keccak256("CallRejected(bytes32,uint256,bytes32,bytes)");
    bytes32 constant SUMMARY_TOPIC = keccak256("BatchExecuted(bytes32,uint256,uint256,uint256,uint256)");
    function checkAllowlist(address target, string memory filename) internal {
        vm.etch(target, type(AllowlistReturn42).runtimeCode);
        bytes4[] memory selectors = new bytes4[](COUNT);
ASSIGN
        bytes memory bitmap = new bytes(selectors.length);
        for (uint256 i; i < selectors.length; ++i) {
            AllowCall[] memory calls = new AllowCall[](1);
            calls[0] = AllowCall(target, abi.encodePacked(selectors[i]), true, bytes32(0), bytes32(uint256(1)));
            vm.recordLogs();
            vm.prank(RELAYER);
            (bool ok,) = PROXY.call(abi.encodeWithSelector(bytes4(0x251fb27d), calls));
            Vm.Log[] memory logs = vm.getRecordedLogs();
            require(ok && logs.length == 2 && logs[1].topics[0] == SUMMARY_TOPIC, "probe failed");
            require(logs[0].topics[0] == EXECUTED_TOPIC || logs[0].topics[0] == REJECTED_TOPIC, "unexpected result");
            uint256 expectedSuccess = logs[0].topics[0] == EXECUTED_TOPIC ? 1 : 0;
            require(keccak256(logs[1].data) == keccak256(abi.encode(uint256(1), expectedSuccess, 1 - expectedSuccess, uint256(0))), "summary mismatch");
            bitmap[i] = expectedSuccess == 1 ? bytes1('1') : bytes1('0');
        }
        vm.writeFile(filename, string(bitmap));
    }
    function testAllowlistExchange() public { checkAllowlist(EXCHANGE, "exchange.txt"); }
    function testAllowlistSession() public { checkAllowlist(SESSION, "session.txt"); }
    function testAllowlistStaking() public { checkAllowlist(STAKING, "staking.txt"); }
    function testAllowlistOther() public { checkAllowlist(address(0x5555), "other.txt"); }
'''


def candidates(catalog, implementation_code):
    selectors = {fn["selector"] for contract in catalog.values() for fn in contract["functions"]}
    code = bytes.fromhex(implementation_code[2:])
    offset = 0
    while offset < len(code):
        opcode = code[offset]
        offset += 1
        if 0x60 <= opcode <= 0x7F:
            width = opcode - 0x5F
            if width == 4:
                selectors.add("0x" + code[offset:offset + 4].hex())
            offset += width
    selectors.add("0xdeadbeef")
    return sorted(selectors)


def source(selectors):
    assignments = "\n".join(f"        selectors[{i}] = bytes4({value});" for i, value in enumerate(selectors))
    probe = PROBE.replace("COUNT", str(len(selectors))).replace("ASSIGN", assignments)
    assert TEST_SOURCE.count("    function parseBytes(string calldata) external pure returns (bytes memory);") == 1
    assert TEST_SOURCE.count("contract BatchControlTest {") == 1
    assert TEST_SOURCE.count("    function testPinnedGetters()") == 1
    return (TEST_SOURCE
            .replace("    function parseBytes(string calldata) external pure returns (bytes memory);",
                     "    function parseBytes(string calldata) external pure returns (bytes memory);\n"
                     "    function writeFile(string calldata, string calldata) external;")
            .replace("contract BatchControlTest {", MOCK + "contract BatchControlTest {")
            .replace("    function testPinnedGetters()", probe + "    function testPinnedGetters()"))


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    runtime = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtime[label] = code
    selectors = candidates(catalog, runtime["Implementation"])
    test_source = source(selectors)
    with tempfile.TemporaryDirectory(prefix="papertrade-batch-allowlist-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read-write", path = "./" }]\n'
        )
        (project / "test" / "BatchAllowlist.t.sol").write_text(test_source)
        for label, code in runtime.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-test", "testAllowlist", "-vv"],
                             capture_output=True, text=True, timeout=60)
        output = run.stdout + "\n" + run.stderr
        passed = sorted(re.findall(r"\[PASS\] (testAllowlist\w+)\(\)", output))
        expected = sorted(re.findall(r"function (testAllowlist\w+)\(", PROBE))
        if run.returncode or passed != expected:
            raise RuntimeError(output)
        bitmaps = {name: (project / f"{name}.txt").read_text().strip() for name in TARGETS}
    assert all(len(bits) == len(selectors) and set(bits) <= {"0", "1"} for bits in bitmaps.values())
    accepted = {name: [selector for selector, bit in zip(selectors, bits) if bit == "1"]
                for name, bits in bitmaps.items()}
    historical = json.loads((ATLAS / "batch_executor_behavior.json").read_text())
    observed_pairs = {(intent["target"].lower(), intent["selector"].lower())
                      for batch in historical["traced_batches"] for intent in batch["intents"]}
    accepted_pairs = {(address.lower(), selector) for name, address in TARGETS.items()
                      for selector in accepted[name]}
    assert accepted_pairs == observed_pairs and len(accepted_pairs) == 8
    record = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": {label: manifest["contracts"][address]["sha256"]
                           for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
        "source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "candidate_basis": "all distinct captured catalog selectors, all exact implementation PUSH4 operands, and 0xdeadbeef",
        "candidate_selectors": selectors,
        "targets": TARGETS,
        "accepted_by_target": accepted,
        "decision_bitmaps": bitmaps,
        "tested_target_selector_pairs": len(selectors) * len(TARGETS),
        "accepted_pair_count": len(accepted_pairs),
        "observed_historical_pairs_match": True,
        "test_count": len(passed), "passed_tests": passed,
        "limit": "The scan is exhaustive only over the recorded candidate set, not every possible bytes4 selector or target address.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, indent=2) + "\n")
    print(f"BatchExecutor allowlist: {len(selectors)} selectors x {len(TARGETS)} targets, {len(accepted_pairs)} accepted pairs")


if __name__ == "__main__":
    main()
