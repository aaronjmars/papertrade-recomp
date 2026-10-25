#!/usr/bin/env python3
"""Check queue consolidation and harvest with two users interleaved by node ID."""

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
OUT = ROOT / "artifacts" / "exchange_library_queue_interleaved_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_library_queue_interleaved_behavior.json"

INTERLEAVED_TESTS = '''
    address constant USER_B = address(0x5678);
    bytes32 constant HARVESTED_TOPIC = 0x81ca9b2c230070eaa84787556b1aaf18bf1e2f07ea5d3dae4819db77a1a5b224;
    function bSlot(uint256 base) internal pure returns (bytes32) {
        return keccak256(abi.encode(USER_B, base));
    }
    function hasRead(bytes32[] memory reads, bytes32 wanted) internal pure returns (bool) {
        for (uint256 i; i < reads.length; ++i) if (reads[i] == wanted) return true;
        return false;
    }
    function seedThroughPinnedLibrary(bool interleaved) internal {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        vm.etch(PROXY, type(EnqueueShim).runtimeCode);
        vm.store(PROXY, bytes32(uint256(17)), bytes32(uint256(101)));
        address[3] memory owners;
        owners[0] = USER;
        owners[1] = interleaved ? USER_B : USER;
        owners[2] = interleaved ? USER : USER_B;
        uint256[3] memory amounts = [uint256(300), 700, 1100];
        for (uint256 i; i < 3; ++i) {
            vm.prank(owners[i]);
            (bool ok, bytes memory out) = PROXY.call(
                abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), owners[i], amounts[i])
            );
            require(ok && out.length == 0, "pinned enqueue");
        }
        require(uint256(vm.load(PROXY, bytes32(uint256(16)))) == 101, "seed global head");
        require(uint256(vm.load(PROXY, bytes32(uint256(17)))) == 104, "seed next ID");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == 2100, "seed total");
        uint256 nextLink = interleaved ? 103 : 102;
        require(vm.load(PROXY, node(101)) == bytes32(uint256(uint160(USER)) | (nextLink << 160)), "seed first link");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == 300, "seed first amount");
        if (interleaved) {
            require(vm.load(PROXY, node(102)) == bytes32(uint256(uint160(USER_B))), "seed other user");
            require(vm.load(PROXY, node(103)) == bytes32(uint256(uint160(USER)) | (uint256(101) << 208)), "seed last link");
            require(uint256(vm.load(PROXY, userSlot(19))) == 1400, "seed A total");
            require(uint256(vm.load(PROXY, bSlot(19))) == 700, "seed B total");
            require(uint256(vm.load(PROXY, userSlot(20))) == 101 && uint256(vm.load(PROXY, userSlot(21))) == 103, "seed A IDs");
            require(uint256(vm.load(PROXY, bSlot(20))) == 102 && uint256(vm.load(PROXY, bSlot(21))) == 102, "seed B IDs");
        } else {
            require(vm.load(PROXY, node(102)) == bytes32(uint256(uint160(USER)) | (uint256(101) << 208)), "seed second link");
            require(vm.load(PROXY, node(103)) == bytes32(uint256(uint160(USER_B))), "seed B tail");
        }
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == 700, "seed second amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == 1100, "seed third amount");
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.store(PROXY, bytes32(uint256(14)), bytes32(uint256(10000)));
    }
    function mergeForward() internal {
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = PROXY.call(
            abi.encodeWithSelector(bytes4(0x753a369c), USER, uint256(101), uint256(103), uint256(1))
        );
        require(ok && out.length == 96, "forward merge");
        (uint256 count, uint256 moved, uint256 target) = abi.decode(out, (uint256,uint256,uint256));
        require(count == 1 && moved == 300 && target == 103, "forward tuple");
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == 5, "forward writes");
        require(!hasRead(reads, node(102)) && !hasRead(reads, bytes32(uint256(node(102)) + 1)), "forward touched B");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 2 && logs[0].topics[0] == MERGE_TOPIC && logs[1].topics[0] == SUMMARY_TOPIC, "forward logs");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == 0, "forward first empty");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == 700, "forward B unchanged");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == 1400, "forward survivor");
        require(uint256(vm.load(PROXY, bSlot(19))) == 700 && uint256(vm.load(PROXY, bSlot(20))) == 102, "forward B queue");
    }
    function checkHarvestLog(Vm.Log memory log, address owner, uint256 amount) internal pure {
        require(log.emitter == PROXY && log.topics.length == 2, "harvest emitter");
        require(log.topics[0] == HARVESTED_TOPIC && log.topics[1] == bytes32(uint256(uint160(owner))), "harvest topic");
        require(keccak256(log.data) == keccak256(abi.encode(amount, uint256(0))), "harvest data");
    }
    function checkForwardHarvest(uint256 limit) internal {
        seedThroughPinnedLibrary(true);
        mergeForward();
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = PROXY.call(abi.encodeWithSelector(bytes4(0xddc63262), limit));
        uint256 paid = limit == 1 ? 0 : (limit == 2 ? 700 : 2100);
        require(ok && out.length == 32 && abi.decode(out, (uint256)) == paid, "harvest amount");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == (limit == 1 ? 3 : (limit == 2 ? 8 : 13)), "harvest writes");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == limit - 1, "harvest log count");
        if (limit >= 2) checkHarvestLog(logs[0], USER_B, 700);
        if (limit == 3) checkHarvestLog(logs[1], USER, 1400);
        require(uint256(vm.load(PROXY, bytes32(uint256(16)))) == 101 + limit, "harvest global head");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == 2100 - paid, "harvest global total");
        require(uint256(vm.load(PROXY, userSlot(19))) == (limit == 3 ? 0 : 1400), "harvest A queued");
        require(uint256(vm.load(PROXY, bSlot(19))) == (limit == 1 ? 700 : 0), "harvest B queued");
        require(uint256(vm.load(PROXY, userSlot(20))) == (limit == 3 ? 0 : 103), "harvest A head");
        require(uint256(vm.load(PROXY, bSlot(20))) == (limit == 1 ? 102 : 0), "harvest B head");
        require(uint256(vm.load(PROXY, keccak256(abi.encode(USER, uint256(9))))) == (limit == 3 ? 1400 : 0), "harvest A balance");
        require(uint256(vm.load(PROXY, keccak256(abi.encode(USER_B, uint256(9))))) == (limit >= 2 ? 700 : 0), "harvest B balance");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == 0, "harvest first amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == (limit == 1 ? 700 : 0), "harvest B amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == (limit == 3 ? 0 : 1400), "harvest A amount");
    }
    function checkReverseRevert(uint256 limit) internal {
        seedThroughPinnedLibrary(true);
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = PROXY.call(
            abi.encodeWithSelector(bytes4(0x827ad94c), USER, uint256(101), uint256(103), limit)
        );
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x5b6d2b7a), "reverse revert");
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == 0 && vm.getRecordedLogs().length == 0, "reverse rollback");
        if (limit == 1) require(reads.length == 2 && !hasRead(reads, node(101)), "reverse early bound");
        else require(reads.length == 6 && hasRead(reads, node(102)) && !hasRead(reads, node(103)), "reverse B lookup");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == 300, "reverse A first");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == 700, "reverse B amount");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == 1100, "reverse A last");
        require(uint256(vm.load(PROXY, bytes32(uint256(18)))) == 2100, "reverse global total");
        require(uint256(vm.load(PROXY, userSlot(19))) == 1400 && uint256(vm.load(PROXY, bSlot(19))) == 700, "reverse user totals");
    }
    function testQueueInterleavedForwardHarvestOne() public { checkForwardHarvest(1); }
    function testQueueInterleavedForwardHarvestTwo() public { checkForwardHarvest(2); }
    function testQueueInterleavedForwardHarvestThree() public { checkForwardHarvest(3); }
    function testQueueInterleavedReverseLimitOne() public { checkReverseRevert(1); }
    function testQueueInterleavedReverseLimitTwo() public { checkReverseRevert(2); }
    function testQueueInterleavedReverseLimitThree() public { checkReverseRevert(3); }
    function testQueueInterleavedContiguousReverseControl() public {
        seedThroughPinnedLibrary(false);
        vm.record();
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = PROXY.call(
            abi.encodeWithSelector(bytes4(0x827ad94c), USER, uint256(101), uint256(102), uint256(1))
        );
        require(ok && out.length == 96, "contiguous reverse");
        (uint256 count, uint256 moved, uint256 target) = abi.decode(out, (uint256,uint256,uint256));
        require(count == 1 && moved == 700 && target == 101, "contiguous tuple");
        (, bytes32[] memory writes) = vm.accesses(PROXY);
        require(writes.length == 5, "contiguous writes");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 2 && logs[0].topics[0] == MERGE_TOPIC && logs[1].topics[0] == SUMMARY_TOPIC, "contiguous logs");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(101)) + 1))) == 1000, "contiguous A survivor");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(102)) + 1))) == 0, "contiguous A emptied");
        require(uint256(vm.load(PROXY, bytes32(uint256(node(103)) + 1))) == 1100, "contiguous B unchanged");
        require(uint256(vm.load(PROXY, bSlot(19))) == 1100 && uint256(vm.load(PROXY, bSlot(20))) == 103, "contiguous B queue");
    }
'''

SHIM = '''
contract EnqueueShim {
    address constant LIBRARY = address(uint160(uint256(0x00cd617f984158a4f5d287ddee0e8eb0fed204916d)));
    fallback() external payable {
        (bool ok, bytes memory out) = LIBRARY.delegatecall(msg.data);
        if (!ok) assembly { revert(add(out, 32), mload(out)) }
        assembly { return(add(out, 32), mload(out)) }
    }
}
'''


def source():
    return merge_source().rsplit("}", 1)[0] + INTERLEAVED_TESTS + "}\n" + SHIM


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    test_source = source()
    with tempfile.TemporaryDirectory(prefix="papertrade-interleaved-queue-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "InterleavedQueue.t.sol").write_text(test_source)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(
            ["forge", "test", "--root", tmp, "--match-test", "testQueueInterleaved", "-vv"],
            capture_output=True, text=True, timeout=60,
        )
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (testQueueInterleaved\w+)\(\)", output))
    expected = sorted([
        "testQueueInterleavedForwardHarvestOne", "testQueueInterleavedForwardHarvestTwo",
        "testQueueInterleavedForwardHarvestThree", "testQueueInterleavedReverseLimitOne",
        "testQueueInterleavedReverseLimitTwo", "testQueueInterleavedReverseLimitThree",
        "testQueueInterleavedContiguousReverseControl",
    ])
    if run.returncode or passed != expected:
        raise RuntimeError("interleaved queue replay failed: " + output[-4000:])
    cases = [
        {"test": "testQueueInterleavedForwardHarvestOne", "merge": "forward_success", "harvest_limit": 1, "paid_A": 0, "paid_B": 0, "global_head": 102},
        {"test": "testQueueInterleavedForwardHarvestTwo", "merge": "forward_success", "harvest_limit": 2, "paid_A": 0, "paid_B": 700, "global_head": 103},
        {"test": "testQueueInterleavedForwardHarvestThree", "merge": "forward_success", "harvest_limit": 3, "paid_A": 1400, "paid_B": 700, "global_head": 104},
        {"test": "testQueueInterleavedReverseLimitOne", "merge": "reverse_revert", "merge_limit": 1, "error_selector": "0x5b6d2b7a"},
        {"test": "testQueueInterleavedReverseLimitTwo", "merge": "reverse_revert", "merge_limit": 2, "error_selector": "0x5b6d2b7a"},
        {"test": "testQueueInterleavedReverseLimitThree", "merge": "reverse_revert", "merge_limit": 3, "error_selector": "0x5b6d2b7a"},
        {"test": "testQueueInterleavedContiguousReverseControl", "merge": "reverse_success", "node_order": ["A", "A", "B"], "returned": [1, 700, 101]},
    ]
    result = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "runtime_hashes": {label: manifest["contracts"][address]["sha256"] for label, address in
                           (("Proxy", PROXY), ("Implementation", IMPLEMENTATION), ("Library", LIBRARY))},
        "setup": "Pinned library enqueue selector 0x18958ce2 builds nodes 101-103 through a temporary delegatecall shim at the proxy address; the pinned proxy runtime is restored before merge and harvest.",
        "test_names": passed, "forge_result": "7 passed, 0 failed",
        "test_source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "cases": cases,
        "limits": ["Synthetic two-user interleaving is reachable through the pinned library but was not observed on chain at the pin.",
                   "The reverse rejection is supported by exact runtime and storage reads; the original source-level precondition is unknown.",
                   "More than three queue nodes, partial funding, and interleaved users with other orderings remain open."],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": PROXY, "implementation": IMPLEMENTATION, "linked_library": LIBRARY,
        "enqueue_library_selector": "0x18958ce2",
        "forward_merge_selectors": {"exchange": "0x753a369c", "library": "0x3cf4208d"},
        "reverse_merge_selectors": {"exchange": "0x827ad94c", "library": "0x32db40c9"},
        "harvest_selectors": {"exchange": "0xddc63262", "library": "0x79810ffe"},
        "local_replay": "../../artifacts/exchange_library_queue_interleaved_local/replay.json",
        "case_count": len(passed),
        "forward_effect": "For node owners A,B,A and A user links 101->103, forward merge moves 300 from 101 to 103 without reading B node 102; harvest processes empty 101, then pays B 700, then A 1400 as limits increase.",
        "reverse_effect": "For A,B,A, reverse merge from 101 to 103 reverts 0x5b6d2b7a at limits 1-3 without writes; limits 2-3 read B node 102 before reverting. A,A,B contiguous control succeeds from 101 to 102 at limit 1.",
        "source_name_status": "Merge source names and raw error name unresolved.",
        "simulated_error_catalog": [{"selector": "0x5b6d2b7a",
                                     "probe_paths": ["testQueueInterleavedReverseLimitOne",
                                                     "testQueueInterleavedReverseLimitTwo",
                                                     "testQueueInterleavedReverseLimitThree"],
                                     "public_signature_candidates": [], "reconstructed_signature": "",
                                     "local_replay_evidence": "../../artifacts/exchange_library_queue_interleaved_local/replay.json"}],
        "limits": result["limits"],
    }
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(len(passed), "exact-runtime interleaved queue tests passed")


if __name__ == "__main__":
    main()
