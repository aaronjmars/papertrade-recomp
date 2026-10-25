#!/usr/bin/env python3
"""Map both count-based Exchange queue consolidation adapters with pinned runtimes."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_exchange_library_queue_interleaved_local import source as interleaved_source
from atlas_exchange_library_adapters_local import ATLAS, IMPLEMENTATION, LIBRARY, PROXY

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "exchange_library_queue_count_merge_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_library_queue_count_merge_behavior.json"

COUNT_TESTS = '''
    function checkCountLogs(Vm.Log[] memory logs, bool towardTail, uint256 start, uint256 count, uint256 moved, uint256 target) internal pure {
        require(logs.length == count + 1, "count log length");
        for (uint256 i; i < count; ++i) {
            uint256 sourceId = towardTail ? start + i : start + i + 1;
            uint256 amount = sourceId == 101 ? 300 : (sourceId == 102 ? 700 : 1100);
            require(logs[i].emitter == PROXY && logs[i].topics.length == 4, "count move emitter");
            require(logs[i].topics[0] == MERGE_TOPIC, "count move topic");
            require(logs[i].topics[1] == bytes32(uint256(uint160(USER))), "count move user");
            require(logs[i].topics[2] == bytes32(sourceId) && logs[i].topics[3] == bytes32(target), "count move IDs");
            require(keccak256(logs[i].data) == keccak256(abi.encode(amount)), "count move amount");
        }
        Vm.Log memory summary = logs[count];
        require(summary.emitter == PROXY && summary.topics.length == 4, "count summary emitter");
        require(summary.topics[0] == SUMMARY_TOPIC && summary.topics[1] == bytes32(uint256(uint160(USER))), "count summary topic");
        require(summary.topics[2] == bytes32(start) && summary.topics[3] == bytes32(target), "count summary IDs");
        require(keccak256(summary.data) == keccak256(abi.encode(count, moved)), "count summary amount");
    }
    function checkCoreCount(bool towardTail, uint256 startArg, uint256 limit) internal {
        seedThree();
        uint256 start = startArg == 0 ? 101 : startArg;
        uint256 count = start == 101 ? (limit == 1 ? 1 : 2) : 1;
        uint256 moved = towardTail
            ? (start == 101 ? (count == 1 ? 300 : 1000) : 700)
            : (start == 101 ? (count == 1 ? 700 : 1800) : 1100);
        uint256 target = towardTail ? start + count : start;
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = PROXY.call(abi.encodeWithSelector(
            towardTail ? bytes4(0xae4daf4e) : bytes4(0x4a4d9eea), USER, startArg, limit));
        require(ok && out.length == 96, "count call");
        (uint256 actualCount, uint256 actualMoved, uint256 actualTarget) = abi.decode(out, (uint256,uint256,uint256));
        require(actualCount == count && actualMoved == moved && actualTarget == target, "count result");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == (count == 1 ? 5 : (towardTail ? 9 : 10)), "count writes");
        checkCountLogs(vm.getRecordedLogs(), towardTail, start, count, moved, target);
        uint256 after101 = towardTail ? (start == 101 ? 0 : 300) : (start == 101 ? 300 + moved : 300);
        uint256 after102 = towardTail ? (start == 101 && count == 1 ? 1000 : 0) : (start == 101 ? (count == 1 ? 0 : 0) : 1800);
        if (towardTail && start == 102) after102 = 0;
        uint256 after103 = towardTail ? (start == 101 && count == 1 ? 1100 : (start == 101 ? 2100 : 1800))
                                      : (start == 101 && count == 1 ? 1100 : 0);
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == after101, "count first amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == after102, "count second amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == after103, "count third amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == 2100, "count global total");
        require(uint256(vm.load(PROXY, userSlot(19))) == 2100, "count user total");
    }
    function seedThreshold(uint256 a, uint256 b, uint256 c) internal {
        seedThree();
        vm.store(PROXY, bytes32(uint256(node(101)) + 1), bytes32(a));
        vm.store(PROXY, bytes32(uint256(node(102)) + 1), bytes32(b));
        vm.store(PROXY, bytes32(uint256(node(103)) + 1), bytes32(c));
        vm.store(PROXY, bytes32(uint256(18)), bytes32(a + b + c));
        vm.store(PROXY, userSlot(19), bytes32(a + b + c));
    }
    function checkThreshold(uint256 variant) internal {
        uint256 a;
        uint256 b;
        uint256 c;
        uint256 count;
        uint256 moved;
        uint256 target;
        if (variant == 0) { a = 1e18 - 1; b = 2e18; c = 0; count = 1; moved = a; target = 102; }
        if (variant == 1) { a = 1e18; b = 2e18; c = 4e17; }
        if (variant == 2) { a = 6e17; b = 6e17; c = 6e17; count = 1; moved = a; target = 102; }
        if (variant == 3) { a = 4e17; b = 4e17; c = 4e17; count = 2; moved = a + b; target = 103; }
        if (variant == 4) { a = 4e17; b = 0; c = 4e17; }
        seedThreshold(a,b,c);
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = PROXY.call(abi.encodeWithSelector(bytes4(0xae4daf4e), USER, uint256(101), uint256(0)));
        require(ok && out.length == 96, "threshold call");
        (uint256 gotCount, uint256 gotMoved, uint256 gotTarget) = abi.decode(out, (uint256,uint256,uint256));
        require(gotCount == count && gotMoved == moved && gotTarget == target, "threshold result");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == (count == 0 ? 0 : (count == 1 ? 5 : 9)), "threshold writes");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == (count == 0 ? 0 : count + 1), "threshold logs");
        if (count != 0) {
            require(logs[0].topics[0] == MERGE_TOPIC && logs[count].topics[0] == SUMMARY_TOPIC, "threshold topics");
            require(keccak256(logs[count].data) == keccak256(abi.encode(count, moved)), "threshold summary");
        }
        checkThresholdPost(a, b, c, count);
    }
    function checkThresholdPost(uint256 a, uint256 b, uint256 c, uint256 count) internal view {
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == (count == 0 ? a : 0), "threshold first");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == (count == 0 ? b : (count == 1 ? a + b : 0)), "threshold second");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == (count == 2 ? a + b + c : c), "threshold third");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == a + b + c, "threshold global total");
        require(uint256(vm.load(PROXY, userSlot(19))) == a + b + c, "threshold user total");
    }
    function checkInterleavedCount(bool towardTail) internal {
        seedThroughPinnedLibrary(true);
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = PROXY.call(abi.encodeWithSelector(
            towardTail ? bytes4(0xae4daf4e) : bytes4(0x4a4d9eea), USER, uint256(101), uint256(0)));
        require(ok && out.length == 96, "interleaved count call");
        (uint256 count, uint256 moved, uint256 target) = abi.decode(out, (uint256,uint256,uint256));
        require(count == (towardTail ? 1 : 0) && moved == (towardTail ? 300 : 0) && target == (towardTail ? 103 : 0), "interleaved count result");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == (towardTail ? 5 : 0), "interleaved count writes");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == (towardTail ? 2 : 0), "interleaved count logs");
        if (towardTail) require(logs[0].topics[0] == MERGE_TOPIC && logs[1].topics[0] == SUMMARY_TOPIC, "interleaved count topics");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == (towardTail ? 0 : 300), "interleaved A first");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == 700, "interleaved B untouched");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == (towardTail ? 1400 : 1100), "interleaved A last");
        require(uint256(vm.load(PROXY, bSlot(19))) == 700, "interleaved B total");
    }
    function testQueueAutoHeadOne() public { checkCoreCount(false, 101, 1); }
    function testQueueAutoHeadAll() public { checkCoreCount(false, 101, 0); }
    function testQueueAutoHeadFromSecond() public { checkCoreCount(false, 102, 1); }
    function testQueueAutoTailOne() public { checkCoreCount(true, 101, 1); }
    function testQueueAutoTailAll() public { checkCoreCount(true, 101, 0); }
    function testQueueAutoTailFromSecond() public { checkCoreCount(true, 102, 1); }
    function testQueueAutoHeadStartZero() public { checkCoreCount(false, 0, 0); }
    function testQueueAutoTailStartZero() public { checkCoreCount(true, 0, 0); }
    function testQueueAutoTailBelowThreshold() public { checkThreshold(0); }
    function testQueueAutoTailAtThreshold() public { checkThreshold(1); }
    function testQueueAutoTailStopsAfterAccumulation() public { checkThreshold(2); }
    function testQueueAutoTailContinuesBelowThreshold() public { checkThreshold(3); }
    function testQueueAutoTailStopsAtZeroNeighbor() public { checkThreshold(4); }
    function testQueueAutoHeadInterleavedNoOp() public { checkInterleavedCount(false); }
    function testQueueAutoTailInterleaved() public { checkInterleavedCount(true); }
'''


def source():
    base = interleaved_source()
    anchor = "    function testQueueInterleavedForwardHarvestOne()"
    assert base.count(anchor) == 1
    return base.replace(anchor, COUNT_TESTS + anchor)


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    test_source = source()
    with tempfile.TemporaryDirectory(prefix="papertrade-count-merge-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "CountMerge.t.sol").write_text(test_source)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(
            ["forge", "test", "--root", tmp, "--match-test", "testQueueAuto", "-vv"],
            capture_output=True, text=True, timeout=60,
        )
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (testQueueAuto\w+)\(\)", output))
    expected = sorted([
        "testQueueAutoHeadOne", "testQueueAutoHeadAll", "testQueueAutoHeadFromSecond",
        "testQueueAutoTailOne", "testQueueAutoTailAll", "testQueueAutoTailFromSecond",
        "testQueueAutoHeadStartZero", "testQueueAutoTailStartZero",
        "testQueueAutoTailBelowThreshold", "testQueueAutoTailAtThreshold",
        "testQueueAutoTailStopsAfterAccumulation", "testQueueAutoTailContinuesBelowThreshold",
        "testQueueAutoTailStopsAtZeroNeighbor", "testQueueAutoHeadInterleavedNoOp",
        "testQueueAutoTailInterleaved",
    ])
    if run.returncode or passed != expected:
        raise RuntimeError("count merge replay failed: " + output[-4000:])
    result = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "runtime_hashes": {label: manifest["contracts"][address]["sha256"] for label, address in
                           (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY))},
        "test_names": passed, "forge_result": "15 passed, 0 failed",
        "test_source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "cases": {
            "count_and_direction": ["head_one", "head_all", "head_from_second", "tail_one", "tail_all", "tail_from_second", "head_start_zero", "tail_start_zero"],
            "tail_threshold": ["first_below_1e18", "first_at_1e18", "accumulation_stops", "below_threshold_continues", "zero_neighbor_stops"],
            "interleaved": ["head_noop_on_other_user", "tail_follows_user_link"],
        },
        "measured_vectors": {
            "head_start_101_count_1": {"returned": [1, 700, 101], "node_amounts_after": [1000, 0, 1100]},
            "head_start_101_count_0": {"returned": [2, 1800, 101], "node_amounts_after": [2100, 0, 0]},
            "tail_start_101_count_1": {"returned": [1, 300, 102], "node_amounts_after": [0, 1000, 1100]},
            "tail_start_101_count_0": {"returned": [2, 1000, 103], "node_amounts_after": [0, 0, 2100]},
            "tail_first_below_1e18": {"input_amounts": [10**18 - 1, 2 * 10**18, 0],
                                       "returned": [1, 10**18 - 1, 102],
                                       "node_amounts_after": [0, 3 * 10**18 - 1, 0]},
            "tail_first_at_1e18": {"input_amounts": [10**18, 2 * 10**18, 4 * 10**17],
                                    "returned": [0, 0, 0],
                                    "node_amounts_after": [10**18, 2 * 10**18, 4 * 10**17]},
            "tail_accumulation_stops": {"input_amounts": [6 * 10**17] * 3,
                                         "returned": [1, 6 * 10**17, 102],
                                         "node_amounts_after": [0, 12 * 10**17, 6 * 10**17]},
            "tail_accumulation_continues": {"input_amounts": [4 * 10**17] * 3,
                                             "returned": [2, 8 * 10**17, 103],
                                             "node_amounts_after": [0, 0, 12 * 10**17]},
            "interleaved_head": {"owners": ["A", "B", "A"], "returned": [0, 0, 0],
                                 "node_amounts_after": [300, 700, 1100]},
            "interleaved_tail": {"owners": ["A", "B", "A"], "returned": [1, 300, 103],
                                 "node_amounts_after": [0, 700, 1400]},
        },
        "limits": ["Local synthetic two- and three-node states, plus one interleaved state built with the pinned library enqueue runtime.",
                   "No historical call of these wrappers is saved; original Solidity names and behavior for longer queues remain unresolved."],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": PROXY, "implementation": IMPLEMENTATION, "linked_library": LIBRARY,
        "selectors": {"headward": {"exchange": "0x4a4d9eea", "library": "0xca02ff91"},
                      "tailward": {"exchange": "0xae4daf4e", "library": "0x2448a553"}},
        "replay": "../../artifacts/exchange_library_queue_count_merge_local/replay.json",
        "case_count": len(passed),
        "measured_vectors": result["measured_vectors"],
        "start_zero_behavior": "Zero start resolves to the user's current head in tested states.",
        "count_zero_behavior": "Zero count continues through all available linked nodes in the tested two- and three-node states.",
        "headward_behavior": "Moves later adjacent same-user nodes into the starting node, no amount threshold observed; A,B,A interleaving returns zero without writes.",
        "tailward_behavior": "Moves earlier linked same-user node amounts into a later node while each current amount is strictly below 1e18; reaching or exceeding 1e18, or a zero neighboring amount, stops the sampled traversal.",
        "events": ["0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb",
                   "0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc"],
        "source_name_status": "Both Exchange and linked-library function names unresolved.",
        "limits": result["limits"],
    }
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(len(passed), "exact-runtime count-based queue merge tests passed")


if __name__ == "__main__":
    main()
