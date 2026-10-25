#!/usr/bin/env python3
"""Replay Exchange harvest after exact-runtime queue consolidation."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_exchange_library_queue_merge_local import source as merge_source
from atlas_exchange_library_adapters_local import ATLAS, IMPLEMENTATION, LIBRARY, PROXY

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "exchange_library_queue_harvest_followup_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_library_queue_harvest_followup_behavior.json"

FOLLOWUP_TESTS = '''
    bytes32 constant HARVESTED_TOPIC = 0x81ca9b2c230070eaa84787556b1aaf18bf1e2f07ea5d3dae4819db77a1a5b224;
    function checkHarvestAfterMerge(bool forward, uint256 nodes, uint256 limit) internal {
        if (nodes == 2) seedQueue(300, 700);
        else seedThree();
        vm.store(PROXY, bytes32(uint256(14)), bytes32(uint256(10000)));
        bytes4 selector = forward ? bytes4(0x753a369c) : bytes4(0x827ad94c);
        vm.prank(USER);
        (bool merged, bytes memory mergeResult) = PROXY.call(
            abi.encodeWithSelector(selector, USER, uint256(101), uint256(100 + nodes), nodes - 1)
        );
        require(merged && mergeResult.length == 96, "merge setup");
        uint256 total = nodes == 2 ? 1000 : 2100;
        bool paid = !forward || limit >= nodes;
        uint256 expectedHead = paid ? 101 + nodes : 101 + limit;
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory result) = PROXY.call(abi.encodeWithSelector(bytes4(0xddc63262), limit));
        require(ok && result.length == 32 && abi.decode(result, (uint256)) == (paid ? total : 0), "harvest result");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == (paid ? 8 : 3), "harvest writes");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == (paid ? 1 : 0), "harvest logs");
        if (paid) {
            require(logs[0].emitter == PROXY && logs[0].topics.length == 2, "harvest emitter");
            require(logs[0].topics[0] == HARVESTED_TOPIC, "harvest topic");
            require(logs[0].topics[1] == bytes32(uint256(uint160(USER))), "harvest user");
            require(keccak256(logs[0].data) == keccak256(abi.encode(total, uint256(0))), "harvest data");
        }
        require(uint256(vm.load(PROXY, bytes32(uint256(16)))) == expectedHead, "global head");
        require(uint256(vm.load(PROXY, bytes32(uint256(17)))) == 101 + nodes, "next ID");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == (paid ? 0 : total), "global total");
        require(uint256(vm.load(PROXY, userSlot(19))) == (paid ? 0 : total), "user total");
        require(uint256(vm.load(PROXY, userSlot(20))) == (paid ? 0 : 100 + nodes), "user head");
        require(uint256(vm.load(PROXY, userSlot(21))) == (paid ? 0 : 100 + nodes), "user tail");
        require(uint256(vm.load(PROXY, keccak256(abi.encode(USER, uint256(9))))) == (paid ? total : 0), "user balance");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == 0, "first node");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == (nodes == 2 && !paid ? total : 0), "second node");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == (nodes == 3 && !paid ? total : 0), "third node");
    }
    function checkFundingAfterForwardMerge(uint256 funds) internal {
        seedThree();
        vm.store(PROXY, bytes32(uint256(14)), bytes32(funds));
        vm.prank(USER);
        (bool merged, bytes memory mergeResult) = PROXY.call(
            abi.encodeWithSelector(bytes4(0x753a369c), USER, uint256(101), uint256(103), uint256(2))
        );
        require(merged && mergeResult.length == 96, "funding merge setup");
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory result) = PROXY.call(abi.encodeWithSelector(bytes4(0xddc63262), uint256(3)));
        require(ok && result.length == 32 && abi.decode(result, (uint256)) == funds, "funding harvest result");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == (funds == 0 ? 0 : 6), "funding writes");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == (funds == 0 ? 0 : 1), "funding logs");
        if (funds != 0) {
            require(logs[0].emitter == PROXY && logs[0].topics.length == 2, "funding emitter");
            require(logs[0].topics[0] == HARVESTED_TOPIC, "funding topic");
            require(logs[0].topics[1] == bytes32(uint256(uint160(USER))), "funding user");
            require(keccak256(logs[0].data) == keccak256(abi.encode(funds, uint256(2100) - funds)), "funding data");
        }
        require(uint256(vm.load(PROXY, bytes32(uint256(16)))) == (funds == 0 ? 101 : 103), "funding global head");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == 2100 - funds, "funding global total");
        require(uint256(vm.load(PROXY, userSlot(19))) == 2100 - funds, "funding user total");
        require(uint256(vm.load(PROXY, userSlot(20))) == 103 && uint256(vm.load(PROXY, userSlot(21))) == 103, "funding user links");
        require(uint256(vm.load(PROXY, keccak256(abi.encode(USER, uint256(9))))) == funds, "funding balance");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == 0, "funding first node");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == 0, "funding second node");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == 2100 - funds, "funding third node");
    }
    function testQueueHarvestAfterMergeForwardThreeNoFunding() public { checkFundingAfterForwardMerge(0); }
    function testQueueHarvestAfterMergeForwardThreePartialFunding() public { checkFundingAfterForwardMerge(1000); }
    function testQueueHarvestAfterMergeForwardTwoLimitOne() public { checkHarvestAfterMerge(true, 2, 1); }
    function testQueueHarvestAfterMergeForwardTwoLimitTwo() public { checkHarvestAfterMerge(true, 2, 2); }
    function testQueueHarvestAfterMergeForwardTwoLimitThree() public { checkHarvestAfterMerge(true, 2, 3); }
    function testQueueHarvestAfterMergeReverseTwoLimitOne() public { checkHarvestAfterMerge(false, 2, 1); }
    function testQueueHarvestAfterMergeForwardThreeLimitOne() public { checkHarvestAfterMerge(true, 3, 1); }
    function testQueueHarvestAfterMergeForwardThreeLimitTwo() public { checkHarvestAfterMerge(true, 3, 2); }
    function testQueueHarvestAfterMergeForwardThreeLimitThree() public { checkHarvestAfterMerge(true, 3, 3); }
    function testQueueHarvestAfterMergeForwardThreeLimitFour() public { checkHarvestAfterMerge(true, 3, 4); }
    function testQueueHarvestAfterMergeReverseThreeLimitOne() public { checkHarvestAfterMerge(false, 3, 1); }
'''


def source():
    return merge_source().rsplit("}", 1)[0] + FOLLOWUP_TESTS + "}\n"


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    test_source = source()
    with tempfile.TemporaryDirectory(prefix="papertrade-merge-harvest-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "MergeHarvest.t.sol").write_text(test_source)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(
            ["forge", "test", "--root", tmp, "--match-test", "testQueueHarvestAfterMerge", "-vv"],
            capture_output=True, text=True, timeout=60,
        )
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (testQueueHarvestAfterMerge\w+)\(\)", output))
    cases = [
        {"direction": "forward", "nodes": 2, "harvest_limit": 1, "paid": 0, "global_head": 102},
        {"direction": "forward", "nodes": 2, "harvest_limit": 2, "paid": 1000, "global_head": 103},
        {"direction": "forward", "nodes": 2, "harvest_limit": 3, "paid": 1000, "global_head": 103},
        {"direction": "reverse", "nodes": 2, "harvest_limit": 1, "paid": 1000, "global_head": 103},
        {"direction": "forward", "nodes": 3, "harvest_limit": 1, "paid": 0, "global_head": 102},
        {"direction": "forward", "nodes": 3, "harvest_limit": 2, "paid": 0, "global_head": 103},
        {"direction": "forward", "nodes": 3, "harvest_limit": 3, "paid": 2100, "global_head": 104},
        {"direction": "forward", "nodes": 3, "harvest_limit": 4, "paid": 2100, "global_head": 104},
        {"direction": "reverse", "nodes": 3, "harvest_limit": 1, "paid": 2100, "global_head": 104},
    ]
    expected = sorted([
        "testQueueHarvestAfterMerge" + case["direction"].title() +
        ("Two" if case["nodes"] == 2 else "Three") +
        "Limit" + {1: "One", 2: "Two", 3: "Three", 4: "Four"}[case["harvest_limit"]]
        for case in cases
    ] + ["testQueueHarvestAfterMergeForwardThreeNoFunding",
         "testQueueHarvestAfterMergeForwardThreePartialFunding"])
    if run.returncode or passed != expected:
        raise RuntimeError("queue harvest follow-up failed: " + output[-4000:])
    result = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "runtime_hashes": {label: manifest["contracts"][address]["sha256"] for label, address in
                           (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY))},
        "merge_replay": "../exchange_library_queue_merge_local/replay.json",
        "test_names": passed, "forge_result": "11 passed, 0 failed",
        "test_source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "cases": cases + [
            {"direction": "forward", "nodes": 3, "harvest_limit": 3, "treasury_funds": 0,
             "paid": 0, "global_head": 101, "remaining_queued": 2100, "writes": 0},
            {"direction": "forward", "nodes": 3, "harvest_limit": 3, "treasury_funds": 1000,
             "paid": 1000, "global_head": 103, "remaining_queued": 1100, "writes": 6},
        ],
        "checked_storage": "Global head/next ID/total, user queued total/head/tail/balance, and all three node amounts",
        "checked_events": "One exact Harvested log on payout, no harvest logs on empty-node-only limits",
        "limits": ["Synthetic one-user two- and three-node queues with 10000 treasury units and zero other reserves.",
                   "Local exact-runtime replays, not historical transactions or proof of all queue shapes.",
                   "Other users interleaved in the global queue, concurrent enqueues, and longer merged ranges remain untested."],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": PROXY, "implementation": IMPLEMENTATION, "linked_library": LIBRARY,
        "merge_selectors": {"forward": {"exchange": "0x753a369c", "library": "0x3cf4208d"},
                            "reverse": {"exchange": "0x827ad94c", "library": "0x32db40c9"}},
        "harvest_selectors": {"exchange": "0xddc63262", "library": "0x79810ffe"},
        "local_replay": "../../artifacts/exchange_library_queue_harvest_followup_local/replay.json",
        "case_count": len(passed),
        "funding_boundaries": {"zero": "harvest returns zero without advancing the empty global head",
                               "partial_1000": "harvest skips two empty nodes, pays 1000 of 2100, and leaves global head at the partially paid node"},
        "forward_effect": "Harvest node limit counts emptied global-head nodes after consolidation; a two-node forward merge needs harvest limit 2 and a three-node forward merge needs limit 3 to reach the surviving amount in one call.",
        "reverse_effect": "Reverse consolidation moves the amount into the first global node, so harvest limit 1 pays it in both tested queue sizes.",
        "empty_head_transition": "With funding available, each skipped empty node advances global head without payment or Harvested log; queued totals and user balance remain unchanged.",
        "source_name_status": "Merge function names and library harvest source name unresolved; Exchange harvest(uint256) is hash checked.",
        "limits": result["limits"],
    }
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(len(passed), "exact-runtime merge-to-harvest tests passed")


if __name__ == "__main__":
    main()
