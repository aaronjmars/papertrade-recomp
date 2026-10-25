#!/usr/bin/env python3
"""Replay both queue consolidation directions through exact pinned runtimes."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_exchange_library_adapters_local import ATLAS, IMPLEMENTATION, LIBRARY, PROXY, TEST_SOURCE

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "exchange_library_queue_merge_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_library_queue_merge_behavior.json"

MERGE_TESTS = '''
    bytes32 constant MERGE_TOPIC = 0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb;
    bytes32 constant SUMMARY_TOPIC = 0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc;
    function node(uint256 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(15)));
    }
    function userSlot(uint256 base) internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, base));
    }
    function seedQueue(uint256 firstAmount, uint256 secondAmount) internal {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        bytes32 n1 = node(101);
        bytes32 n2 = node(102);
        vm.store(PROXY, n1, bytes32(uint256(uint160(USER)) | (uint256(102) << 160)));
        vm.store(PROXY, bytes32(uint256(n1) + 1), bytes32(firstAmount));
        vm.store(PROXY, n2, bytes32(uint256(uint160(USER)) | (uint256(101) << 208)));
        vm.store(PROXY, bytes32(uint256(n2) + 1), bytes32(secondAmount));
        vm.store(PROXY, bytes32(uint256(16)), bytes32(uint256(101)));
        vm.store(PROXY, bytes32(uint256(17)), bytes32(uint256(103)));
        vm.store(PROXY, bytes32(uint256(18)), bytes32(firstAmount + secondAmount));
        vm.store(PROXY, userSlot(19), bytes32(firstAmount + secondAmount));
        vm.store(PROXY, userSlot(20), bytes32(uint256(101)));
        vm.store(PROXY, userSlot(21), bytes32(uint256(102)));
    }
    function checkState(bool forward, uint256 total) internal view {
        bytes32 n1 = node(101);
        bytes32 n2 = node(102);
        require(vm.load(PROXY, n1) == bytes32(uint256(uint160(USER))), "first links");
        require(vm.load(PROXY, n2) == bytes32(uint256(uint160(USER))), "second links");
        require(uint256(vm.load(PROXY, bytes32(uint256(n1) + 1))) == (forward ? 0 : total), "first amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(n2) + 1))) == (forward ? total : 0), "second amount");
        require(uint256(vm.load(PROXY, userSlot(20))) == (forward ? 102 : 101), "user head");
        require(uint256(vm.load(PROXY, userSlot(21))) == (forward ? 102 : 101), "user tail");
        require(uint256(vm.load(PROXY, userSlot(19))) == total, "user total");
        require(uint256(vm.load(PROXY, bytes32(uint256(16)))) == 101, "global head");
        require(uint256(vm.load(PROXY, bytes32(uint256(17)))) == 103, "next node");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == total, "global total");
    }
    function checkLogs(Vm.Log[] memory logs, bool forward, uint256 moved, uint256 target) internal pure {
        require(logs.length == 2, "log count");
        require(logs[0].emitter == PROXY && logs[1].emitter == PROXY, "log emitter");
        require(logs[0].topics.length == 4 && logs[1].topics.length == 4, "topic count");
        require(logs[0].topics[0] == MERGE_TOPIC && logs[1].topics[0] == SUMMARY_TOPIC, "topic0");
        require(logs[0].topics[1] == bytes32(uint256(uint160(USER))) && logs[1].topics[1] == bytes32(uint256(uint160(USER))), "user topic");
        require(logs[0].topics[2] == bytes32(forward ? uint256(101) : 102), "source topic");
        require(logs[0].topics[3] == bytes32(target), "target topic");
        require(logs[1].topics[2] == bytes32(uint256(101)) && logs[1].topics[3] == bytes32(target), "summary topic");
        require(keccak256(logs[0].data) == keccak256(abi.encode(moved)), "move data");
        require(keccak256(logs[1].data) == keccak256(abi.encode(uint256(1), moved)), "summary data");
    }
    function checkMerge(bool forward, uint256 firstAmount, uint256 secondAmount, uint256 limit) internal {
        seedQueue(firstAmount, secondAmount);
        bytes4 selector = forward ? bytes4(0x753a369c) : bytes4(0x827ad94c);
        uint256 moved = forward ? firstAmount : secondAmount;
        uint256 target = forward ? 102 : 101;
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory result) = PROXY.call(abi.encodeWithSelector(selector, USER, uint256(101), uint256(102), limit));
        require(ok && result.length == 96, "merge success");
        (uint256 count, uint256 amount, uint256 nextId) = abi.decode(result, (uint256,uint256,uint256));
        require(count == 1 && amount == moved && nextId == target, "return tuple");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == 5, "write count");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        checkLogs(logs, forward, moved, target);
        checkState(forward, firstAmount + secondAmount);
    }

    function seedThree() internal {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        vm.store(PROXY, node(101), bytes32(uint256(uint160(USER)) | (uint256(102) << 160)));
        vm.store(PROXY, bytes32(uint256(node(101)) + 1), bytes32(uint256(300)));
        vm.store(PROXY, node(102), bytes32(uint256(uint160(USER)) | (uint256(103) << 160) | (uint256(101) << 208)));
        vm.store(PROXY, bytes32(uint256(node(102)) + 1), bytes32(uint256(700)));
        vm.store(PROXY, node(103), bytes32(uint256(uint160(USER)) | (uint256(102) << 208)));
        vm.store(PROXY, bytes32(uint256(node(103)) + 1), bytes32(uint256(1100)));
        vm.store(PROXY, bytes32(uint256(16)), bytes32(uint256(101)));
        vm.store(PROXY, bytes32(uint256(17)), bytes32(uint256(104)));
        vm.store(PROXY, bytes32(uint256(18)), bytes32(uint256(2100)));
        vm.store(PROXY, userSlot(19), bytes32(uint256(2100)));
        vm.store(PROXY, userSlot(20), bytes32(uint256(101)));
        vm.store(PROXY, userSlot(21), bytes32(uint256(103)));
    }
    function checkThreeState(bool forward, bool succeeded) internal view {
        uint256 first = succeeded ? (forward ? 0 : 2100) : 300;
        uint256 second = succeeded ? 0 : 700;
        uint256 third = succeeded ? (forward ? 2100 : 0) : 1100;
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == first, "three first amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == second, "three second amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == third, "three third amount");
        uint256 end = succeeded ? (forward ? 103 : 101) : 0;
        require(uint256(vm.load(PROXY, userSlot(20))) == (succeeded ? end : 101), "three head");
        require(uint256(vm.load(PROXY, userSlot(21))) == (succeeded ? end : 103), "three tail");
        require(uint256(vm.load(PROXY, userSlot(19))) == 2100, "three user total");
        require(uint256(vm.load(PROXY, bytes32(uint256(16)))) == 101, "three global head");
        require(uint256(vm.load(PROXY, bytes32(uint256(17)))) == 104, "three next ID");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == 2100, "three global total");
    }
    function checkThreeLogs(Vm.Log[] memory logs, bool forward) internal pure {
        require(logs.length == 3, "three log count");
        uint256 target = forward ? 103 : 101;
        uint256 moved = forward ? 1000 : 1800;
        for (uint256 i; i < 2; ++i) {
            require(logs[i].emitter == PROXY && logs[i].topics.length == 4, "three move emitter");
            require(logs[i].topics[0] == MERGE_TOPIC && logs[i].topics[1] == bytes32(uint256(uint160(USER))), "three move topics");
            require(logs[i].topics[2] == bytes32(forward ? 101 + i : 102 + i), "three source");
            require(logs[i].topics[3] == bytes32(target), "three target");
            require(keccak256(logs[i].data) == keccak256(abi.encode(forward ? 300 + 400 * i : 700 + 400 * i)), "three moved data");
        }
        require(logs[2].emitter == PROXY && logs[2].topics.length == 4, "three summary emitter");
        require(logs[2].topics[0] == SUMMARY_TOPIC && logs[2].topics[1] == bytes32(uint256(uint160(USER))), "three summary topic");
        require(logs[2].topics[2] == bytes32(uint256(101)) && logs[2].topics[3] == bytes32(target), "three summary IDs");
        require(keccak256(logs[2].data) == keccak256(abi.encode(uint256(2), moved)), "three summary data");
    }
    function checkThree(bool forward, uint256 limit) internal {
        seedThree();
        bytes4 selector = forward ? bytes4(0x753a369c) : bytes4(0x827ad94c);
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory result) = PROXY.call(abi.encodeWithSelector(selector, USER, uint256(101), uint256(103), limit));
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        if (limit == 1) {
            require(!ok && result.length == 4 && bytes4(result) == bytes4(0x5b6d2b7a), "three limit revert");
            require(writes.length == 0 && logs.length == 0, "three rollback");
            checkThreeState(forward, false);
            return;
        }
        require(ok && result.length == 96, "three merge success");
        (uint256 count, uint256 amount, uint256 nextId) = abi.decode(result, (uint256,uint256,uint256));
        require(count == 2 && amount == (forward ? 1000 : 1800) && nextId == (forward ? 103 : 101), "three return tuple");
        require(writes.length == (forward ? 9 : 10), "three write count");
        checkThreeLogs(logs, forward);
        checkThreeState(forward, true);
    }
    function testQueueMergeThreeForwardLowLimit() public { checkThree(true, 1); }
    function testQueueMergeThreeForwardExactLimit() public { checkThree(true, 2); }
    function testQueueMergeThreeForwardHigherLimit() public { checkThree(true, 3); }
    function testQueueMergeThreeReverseLowLimit() public { checkThree(false, 1); }
    function testQueueMergeThreeReverseExactLimit() public { checkThree(false, 2); }
    function testQueueMergeThreeReverseHigherLimit() public { checkThree(false, 3); }
    function testQueueMergeForwardEqual() public { checkMerge(true, 500, 500, 1); }
    function testQueueMergeReverseEqual() public { checkMerge(false, 500, 500, 1); }
    function testQueueMergeForwardUnequal() public { checkMerge(true, 300, 700, 2); }
    function testQueueMergeReverseUnequal() public { checkMerge(false, 300, 700, 2); }
'''


def source():
    return TEST_SOURCE.rsplit("}", 1)[0] + MERGE_TESTS + "}\n"


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    test_source = source()
    with tempfile.TemporaryDirectory(prefix="papertrade-library-merge-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "QueueMerge.t.sol").write_text(test_source)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-test", "testQueueMerge", "-vv"],
                             capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (testQueueMerge\w+)\(\)", output))
    expected = sorted(["testQueueMergeForwardEqual", "testQueueMergeReverseEqual",
                       "testQueueMergeForwardUnequal", "testQueueMergeReverseUnequal",
                       "testQueueMergeThreeForwardLowLimit", "testQueueMergeThreeForwardExactLimit",
                       "testQueueMergeThreeForwardHigherLimit", "testQueueMergeThreeReverseLowLimit",
                       "testQueueMergeThreeReverseExactLimit", "testQueueMergeThreeReverseHigherLimit"])
    if run.returncode or passed != expected:
        raise RuntimeError("queue merge replay failed: " + output[-4000:])
    result = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "runtime_hashes": {label: manifest["contracts"][address]["sha256"] for label, address in
                           (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY))},
        "exchange_selectors": {"forward": "0x753a369c", "reverse": "0x827ad94c"},
        "linked_library_selectors": {"forward": "0x3cf4208d", "reverse": "0x32db40c9"},
        "node_mapping_base": 15, "user_total_mapping_base": 19,
        "user_head_mapping_base": 20, "user_tail_mapping_base": 21,
        "local_cases": [
            {"test": "testQueueMergeForwardEqual", "first_amount": 500, "second_amount": 500, "limit": 1, "returned": [1, 500, 102]},
            {"test": "testQueueMergeReverseEqual", "first_amount": 500, "second_amount": 500, "limit": 1, "returned": [1, 500, 101]},
            {"test": "testQueueMergeForwardUnequal", "first_amount": 300, "second_amount": 700, "limit": 2, "returned": [1, 300, 102]},
            {"test": "testQueueMergeReverseUnequal", "first_amount": 300, "second_amount": 700, "limit": 2, "returned": [1, 700, 101]},
            {"test": "testQueueMergeThreeForwardLowLimit", "node_amounts": [300, 700, 1100], "limit": 1, "revert_selector": "0x5b6d2b7a", "writes": 0, "logs": 0},
            {"test": "testQueueMergeThreeForwardExactLimit", "node_amounts": [300, 700, 1100], "limit": 2, "returned": [2, 1000, 103], "writes": 9, "logs": 3},
            {"test": "testQueueMergeThreeForwardHigherLimit", "node_amounts": [300, 700, 1100], "limit": 3, "returned": [2, 1000, 103], "writes": 9, "logs": 3},
            {"test": "testQueueMergeThreeReverseLowLimit", "node_amounts": [300, 700, 1100], "limit": 1, "revert_selector": "0x5b6d2b7a", "writes": 0, "logs": 0},
            {"test": "testQueueMergeThreeReverseExactLimit", "node_amounts": [300, 700, 1100], "limit": 2, "returned": [2, 1800, 101], "writes": 10, "logs": 3},
            {"test": "testQueueMergeThreeReverseHigherLimit", "node_amounts": [300, 700, 1100], "limit": 3, "returned": [2, 1800, 101], "writes": 10, "logs": 3},
        ],
        "per_case_storage_checks": "Two-node success writes five slots; three-node success writes nine slots forward or ten reverse. Amounts and user head/tail match the surviving node, with global and user queued totals unchanged. Three-node limit-one failures leave storage unchanged.",
        "per_case_event_topics": ["0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb",
                                  "0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc"],
        "test_names": passed, "forge_result": "10 passed, 0 failed",
        "test_source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "limits": ["Synthetic two-node and three-node queues for one user, with limits 1, 2, and 3.",
                   "No historical invocation of these wrappers is in the saved call graph.",
                   "Solidity source names, ranges over three nodes, caller permissions, and other argument meanings remain unresolved."],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": PROXY, "implementation": IMPLEMENTATION, "linked_library": LIBRARY,
        "selectors": {
            "forward": {"exchange": "0x753a369c", "library": "0x3cf4208d"},
            "reverse": {"exchange": "0x827ad94c", "library": "0x32db40c9"},
        },
        "local_replay": "../../artifacts/exchange_library_queue_merge_local/replay.json",
        "case_count": len(passed), "node_ids": [101, 102, 103],
        "tested_amount_pairs": [[500, 500], [300, 700]],
        "tested_three_node_amounts": [300, 700, 1100], "tested_limits": [1, 2, 3],
        "three_node_limit_boundary": {"needed_merges": 2, "limit_one_revert_selector": "0x5b6d2b7a",
                                      "limit_two_or_three_forward_return": [2, 1000, 103],
                                      "limit_two_or_three_reverse_return": [2, 1800, 101]},
        "forward_result": "move node 101 amount into node 102; clear node 101; user head and tail become 102; return (1,moved,102)",
        "reverse_result": "move node 102 amount into node 101; clear node 102; user head and tail become 101; return (1,moved,101)",
        "unchanged_totals": ["global queue total slot 18", "user queued total mapping slot 19"],
        "simulated_error_catalog": [{"selector": "0x5b6d2b7a",
                                     "probe_paths": ["testQueueMergeThreeForwardLowLimit", "testQueueMergeThreeReverseLowLimit"],
                                     "public_signature_candidates": [], "reconstructed_signature": "",
                                     "local_replay_evidence": "../../artifacts/exchange_library_queue_merge_local/replay.json"}],
        "event_catalog": [
            {"topic0": result["per_case_event_topics"][0], "status": "local_replay_only",
             "decoded_layout": "indexed user, source node ID, target node ID; unindexed moved amount", "reconstructed_signature": ""},
            {"topic0": result["per_case_event_topics"][1], "status": "local_replay_only",
             "decoded_layout": "indexed user, start node ID, resulting node ID; unindexed merged node count, moved amount", "reconstructed_signature": ""},
        ],
        "limits": result["limits"],
    }
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(len(passed), "exact-runtime queue merge tests passed")


if __name__ == "__main__":
    main()
