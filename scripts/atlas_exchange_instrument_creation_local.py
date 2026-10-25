#!/usr/bin/env python3
"""Replay Exchange instrument registration and validation on exact pinned code."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_exchange_instrument_limit_local import ATLAS, IMPLEMENTATION, PROXY, TEST_SOURCE

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "exchange_instrument_creation_local" / "replay.json"

TESTS = '''
    bytes32 constant ADDED_TOPIC = keccak256("InstrumentAdded(uint32,uint32)");
    bytes4 constant CREATE_SELECTOR = 0xc88bbcf3;
    function marketSlot(uint32 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(36)));
    }
    function firstArgs() internal pure returns (uint256[9] memory a) {
        a = [uint256(15000000000000000000000), 814598000000000000000, uint256(0), uint256(1000),
             10000000000000000000000000, 476041580087574, 100000000000000000,
             100000000000000000000000, uint256(10)];
    }
    function secondArgs() internal pure returns (uint256[9] memory a) {
        a = [uint256(15000000000000000000000), 483979000000000000000, uint256(1), uint256(1000),
             10000000000000000000000000, 481304050180130, 100000000000000000,
             100000000000000000000000, uint256(100)];
    }
    function invoke(address actor, uint256[9] memory a)
        internal returns (bool ok, bytes memory out, Vm.Log[] memory logs) {
        bytes memory data = abi.encodeWithSelector(CREATE_SELECTOR,
            a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],a[8]);
        vm.recordLogs();
        vm.prank(actor);
        (ok,out) = PROXY.call(data);
        logs = vm.getRecordedLogs();
    }
    function checkSuccess(uint32 id, uint256[9] memory a) internal {
        (bool ok, bytes memory out, Vm.Log[] memory logs) = invoke(OWNER, a);
        require(ok && out.length == 32 && abi.decode(out,(uint256)) == id, "created ID");
        require(uint256(vm.load(PROXY, bytes32(uint256(8)))) == uint256(id) + 1, "count");
        bytes32 instrument = slotFor(id);
        uint256 w0 = a[0] | a[1] << 96 | a[2] << 192 | a[3] << 224;
        uint256 w1 = a[4] | a[5] << 120 | a[6] << 184;
        require(uint256(vm.load(PROXY, instrument)) == w0, "instrument word0");
        require(uint256(vm.load(PROXY, bytes32(uint256(instrument)+1))) == w1, "instrument word1");
        require(uint256(vm.load(PROXY, bytes32(uint256(instrument)+2))) == a[7], "instrument word2");
        bytes32 market = marketSlot(id);
        require(uint256(vm.load(PROXY, market)) == a[8] << 192, "market word0");
        require(vm.load(PROXY, bytes32(uint256(market)+1)) == bytes32(type(uint256).max), "market word1");
        require(logs.length == 1 && logs[0].emitter == PROXY && logs[0].topics.length == 2, "event envelope");
        require(logs[0].topics[0] == ADDED_TOPIC && logs[0].topics[1] == bytes32(uint256(id)), "event topics");
        require(keccak256(logs[0].data) == keccak256(abi.encode(a[2])), "event second field");
    }
    function testCreateHistoricalPair() public {
        vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
        checkSuccess(0, firstArgs());
        checkSuccess(1, secondArgs());
    }
    function testCreateEventUsesThirdArgument() public {
        vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
        uint256[9] memory a = firstArgs();
        a[2] = 7;
        checkSuccess(0, a);
    }
    function testCreateOutsiderRejected() public {
        vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
        (bool ok, bytes memory out, Vm.Log[] memory logs) = invoke(address(0xbeef), firstArgs());
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "owner guard");
        require(logs.length == 0 && vm.load(PROXY, bytes32(uint256(8))) == bytes32(0), "outsider effect");
    }
    function testCreateRequiredNonzeroWords() public {
        uint256[9] memory a = firstArgs();
        uint256[5] memory required = [uint256(0),3,4,7,8];
        for (uint256 i; i < required.length; ++i) {
            uint256 index = required[i];
            uint256 old = a[index];
            a[index] = 0;
            vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
            (bool ok, bytes memory out, Vm.Log[] memory logs) = invoke(OWNER, a);
            bytes4 expectedError = index == 8 ? bytes4(0x924d25e6) : bytes4(0xb0cb274d);
            require(!ok && out.length == 4 && bytes4(out) == expectedError, "required word error");
            require(logs.length == 0 && vm.load(PROXY, bytes32(uint256(8))) == bytes32(0), "required word effect");
            a[index] = old;
        }
    }
    function testCreateOptionalZeroWords() public {
        uint256[9] memory a = firstArgs();
        uint256[4] memory optional = [uint256(1),2,5,6];
        for (uint256 i; i < optional.length; ++i) {
            uint256 index = optional[i];
            uint256 old = a[index];
            a[index] = 0;
            vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
            checkSuccess(0, a);
            a[index] = old;
        }
    }
    function testCreateOwnerGuardBeforeMostWidthChecks() public {
        uint256[9] memory a = firstArgs();
        uint256[9] memory width = [uint256(96),96,32,32,120,64,72,128,uint256(64)];
        for (uint256 i; i < width.length; ++i) {
            uint256 old = a[i];
            a[i] = uint256(1) << width[i];
            (bool ok, bytes memory out, Vm.Log[] memory logs) = invoke(address(0xbeef), a);
            require(!ok && logs.length == 0, "outsider width effect");
            if (i == 8) require(out.length == 0, "last word checked before owner");
            else require(out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "owner checked before width");
            a[i] = old;
        }
    }
    function testCreateWord7ObservedBoundary() public {
        uint256[9] memory a = firstArgs();
        a[7] = uint256(1) << 127;
        vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
        checkSuccess(0, a);
        a[7] = uint256(1) << 128;
        vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
        (bool ok, bytes memory out, Vm.Log[] memory logs) = invoke(OWNER, a);
        require(!ok && out.length == 0, "word7 upper boundary");
        require(logs.length == 0 && vm.load(PROXY, bytes32(uint256(8))) == bytes32(0), "word7 overflow effect");
    }
    function testCreateWidthOverflowsReject() public {
        uint256[9] memory a = firstArgs();
        uint256[9] memory width = [uint256(96),96,32,32,120,64,72,0,uint256(64)];
        for (uint256 i; i < width.length; ++i) {
            if (width[i] == 0) continue;
            uint256 old = a[i];
            a[i] = uint256(1) << width[i];
            vm.store(PROXY, bytes32(uint256(8)), bytes32(0));
            (bool ok, bytes memory out, Vm.Log[] memory logs) = invoke(OWNER, a);
            require(!ok && out.length == 0, "word-width overflow");
            require(logs.length == 0 && vm.load(PROXY, bytes32(uint256(8))) == bytes32(0), "overflow effect");
            a[i] = old;
        }
    }
'''


def source():
    anchor = "    function testOwnerUpdatesPackedFields()"
    assert TEST_SOURCE.count(anchor) == 1
    return TEST_SOURCE.replace(anchor, TESTS + anchor)


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtime = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtime[label] = code
    test_source = source()
    with tempfile.TemporaryDirectory(prefix="papertrade-instrument-create-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "InstrumentCreation.t.sol").write_text(test_source)
        for label, code in runtime.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-test", "testCreate", "-vv"],
                             capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (testCreate\w+)\(\)", output))
    expected = sorted(re.findall(r"function (testCreate\w+)\(", TESTS))
    if run.returncode or passed != expected:
        raise RuntimeError(output)
    record = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": {label: manifest["contracts"][address]["sha256"]
                           for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
        "source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "test_count": len(passed), "passed_tests": passed,
        "successful_registration_cases": 7,
        "required_zero_rejection_cases": 5,
        "overflow_rejection_cases": 9,
        "word7_observed_width_bits": 128,
        "owner_guard_order": "words 0 through 7: owner guard before sampled width rejection; word 8: width rejection before owner guard",
        "event_second_field": "input word 2, demonstrated when new ID is 0 and input word 2 is 7",
        "limits": ["Synthetic initial state, exact pinned proxy and implementation runtimes.",
                   "Boundary probes show 127th bit accepted and 128th bit rejected for word 7. This is an observed input boundary, not proof of the original ABI spelling.",
                   "Other tested width overflows revert with empty data; narrower acceptance limits remain unresolved."],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, indent=2) + "\n")
    print(f"Exchange instrument creation: {len(passed)} exact-runtime tests passed")


if __name__ == "__main__":
    main()
