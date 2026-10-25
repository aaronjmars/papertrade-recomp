#!/usr/bin/env python3
"""Replay user deposit proxy edge cases against the exact pinned runtime."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUTPUT = ROOT / "artifacts" / "deposit_proxy_local" / "replay.json"
PROXY = "0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"

SOURCE = '''pragma solidity ^0.8.24;
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
contract MockWriter {
    uint256 public calls;
    uint256 public failAt;
    event RawAction(bytes action);
    function sendRawAction(bytes calldata action) external {
        calls++;
        if (calls == failAt) revert("writer failed");
        emit RawAction(action);
    }
}
contract DepositProxyLocalTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x00f1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce)));
    address constant USER = address(uint160(uint256(0x00fb94d3404c1d3d9d6f08f79e58041d5ea95accfa)));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant CORE = address(0x3333333333333333333333333333333333333333);
    address constant TOKEN = address(0x4444444444444444444444444444444444444444);
    bytes32 constant WITHDRAW_TOPIC = keccak256("StuckTokenWithdrawn(address,address,uint256)");
    bytes32 constant ACTION_TOPIC = keccak256("RawAction(bytes)");
    function setUp() public {
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(CORE, type(MockWriter).runtimeCode);
    }
    function rescue(uint256 amount) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x0c506e96), TOKEN, amount);
    }
    function sweep(uint64 token, uint64 spot, uint64 perp) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x925b3aad), token, spot, perp);
    }
    function checkRevert(bytes memory data, address actor) internal {
        vm.recordLogs();
        vm.prank(actor);
        (bool ok,) = PROXY.call(data);
        require(!ok, "expected revert");
        require(vm.getRecordedLogs().length == 0, "revert emitted log");
    }
    function testGetters() public {
        (bool a, bytes memory u) = PROXY.call(hex"4f8632ba");
        (bool b, bytes memory e) = PROXY.call(hex"d2f7265a");
        require(a && b && abi.decode(u, (address)) == USER && abi.decode(e, (address)) == EXCHANGE, "immutable getters");
    }
    function testUnauthorizedRescue() public { checkRevert(rescue(11), EXCHANGE); }
    function testZeroRescue() public { checkRevert(rescue(0), USER); }
    function testRescueBoolTrue() public { checkRescue(hex"600160005260206000f3"); }
    function testRescueNoReturn() public { checkRescue(hex"00"); }
    function testRescueNoCode() public { checkRescue(hex""); }
    function checkRescue(bytes memory tokenCode) internal {
        vm.etch(TOKEN, tokenCode);
        vm.recordLogs();
        vm.prank(USER);
        (bool ok,) = PROXY.call(rescue(11));
        require(ok, "rescue failed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY, "rescue log count");
        require(logs[0].topics.length == 3 && logs[0].topics[0] == WITHDRAW_TOPIC, "rescue topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(USER))), "rescue user");
        require(logs[0].topics[2] == bytes32(uint256(uint160(TOKEN))), "rescue token");
        require(abi.decode(logs[0].data, (uint256)) == 11, "rescue amount");
    }
    function testRescueBoolFalse() public {
        vm.etch(TOKEN, hex"600060005260206000f3");
        checkRevert(rescue(11), USER);
    }
    function testRescueBoolMalformed() public {
        vm.etch(TOKEN, hex"600260005260206000f3");
        checkRevert(rescue(11), USER);
    }
    function testRescueShortReturn() public {
        vm.etch(TOKEN, hex"600160005360016000f3");
        checkRevert(rescue(11), USER);
    }
    function testRescueTokenRevert() public {
        vm.etch(TOKEN, hex"60006000fd");
        checkRevert(rescue(11), USER);
    }
    function testUnauthorizedSweep() public { checkRevert(sweep(0, 1, 0), USER); }
    function testZeroSweep() public {
        vm.recordLogs();
        vm.prank(EXCHANGE);
        (bool ok,) = PROXY.call(sweep(0, 0, 0));
        require(ok && vm.getRecordedLogs().length == 0, "zero sweep");
        require(uint256(vm.load(CORE, bytes32(0))) == 0, "zero writer calls");
    }
    function testSpotSweep() public { checkSweep(7, 123, 0); }
    function testPerpSweep() public { checkSweep(7, 123, 4); }
    function testPerpOnlySweep() public { checkSweep(7, 0, 4); }
    function checkSweep(uint64 token, uint64 spot, uint64 perp) internal {
        vm.recordLogs();
        vm.prank(EXCHANGE);
        (bool ok,) = PROXY.call(sweep(token, spot, perp));
        require(ok, "sweep failed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == (perp == 0 ? 1 : 2), "action count");
        require(uint256(vm.load(CORE, bytes32(0))) == logs.length, "writer calls");
        for (uint256 i; i < logs.length; ++i) {
            require(logs[i].emitter == CORE && logs[i].topics.length == 1 && logs[i].topics[0] == ACTION_TOPIC, "action emitter");
            bytes memory raw = abi.decode(logs[i].data, (bytes));
            bytes memory expected = perp != 0 && i == 0
                ? abi.encodePacked(bytes4(0x01000007), abi.encode(perp, false))
                : abi.encodePacked(bytes4(0x01000006), abi.encode(EXCHANGE, token, uint64(uint256(spot) + uint256(perp) * 100)));
            require(keccak256(raw) == keccak256(expected), "action payload");
        }
    }
    function testSweepOverflowMultiply() public { checkRevert(sweep(0, 0, type(uint64).max), EXCHANGE); }
    function testSweepOverflowSum() public { checkRevert(sweep(0, type(uint64).max, 1), EXCHANGE); }
    function testWriterRejectsFirstAction() public {
        vm.store(CORE, bytes32(uint256(1)), bytes32(uint256(1)));
        checkRevert(sweep(7, 123, 4), EXCHANGE);
        require(uint256(vm.load(CORE, bytes32(0))) == 0, "writer rollback");
    }
    function testWriterRejectsSecondAction() public {
        vm.store(CORE, bytes32(uint256(1)), bytes32(uint256(2)));
        vm.recordLogs();
        vm.prank(EXCHANGE);
        (bool ok,) = PROXY.call(sweep(7, 123, 4));
        require(!ok, "second writer call must revert");
        require(vm.getRecordedLogs().length == 1, "first action reached writer");
        require(uint256(vm.load(CORE, bytes32(0))) == 0, "writer rollback");
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    row = manifest["contracts"][PROXY]
    runtime = (ATLAS / row["runtime_file"]).read_text().strip()
    assert hashlib.sha256(bytes.fromhex(runtime[2:])).hexdigest() == row["sha256"]
    with tempfile.TemporaryDirectory(prefix="papertrade-deposit-proxy-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "DepositProxy.t.sol").write_text(SOURCE)
        (project / "runtime" / "Proxy.hex").write_text(runtime)
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-contract", "DepositProxyLocalTest", "-vv"],
                             capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    expected = sorted(re.findall(r"function (test\w+)\(", SOURCE))
    if run.returncode or passed != expected:
        raise RuntimeError(output)
    record = {"pin": manifest["block"], "block_hash": manifest["block_hash"],
              "address": PROXY, "runtime_sha256": row["sha256"],
              "source_sha256": hashlib.sha256(SOURCE.encode()).hexdigest(),
              "test_count": len(passed), "passed_tests": passed,
              "scope": "exact pinned proxy runtime with local mock ERC20 and CoreWriter; no HyperCore settlement"}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, indent=2) + "\n")
    print(f"deposit proxy local: {len(passed)} exact-runtime tests passed")


if __name__ == "__main__":
    main()
