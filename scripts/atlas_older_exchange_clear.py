#!/usr/bin/env python3
"""Replay the older Exchange's deployed clearPendingSweep recovery path."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.request

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_exchange_clear_replay.json"
PIN_CALLS = ROOT / "artifacts" / "deployer_scope" / "older_exchange_clear_pin_calls.json"
OLDER_IMPL = "0x557c853e100600e0ee91e0df88fcf4af0097ff89"
OLDER_PROXY = "0x1b534e482b92bb6daff452cd12f2e35219e13493"
FACTORY = "0x36365dc6bd9513692978e4ea8f3117a7bae55f28"
OWNER = "0x69b4b92f02ff415e0c966686e00d2783b395d690"
USER = "0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa"
OUTSIDER = "0x000000000000000000000000000000000000beef"
CLEAR = "0x2362f4de"
RECONCILE = "0x6a3214c9"
EXPECTED_MISSING = {
    "0x1b7c1009", "0x6d60ae8e", "0x82f47a3f", "0x86d506db", "0x88f2aea5", "0xcbeb5f3d"
}
EXPECTED_ADDED = {CLEAR, "0x6155be59", "0xb29af6b0", "0xf92576b1"}
TEST_NAMES = {
    "testOwnerClearsPending", "testOutsiderCannotClear", "testNoPendingRejects", "testClearThenReconcile"
}
TEST_SOURCE = """pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract OlderExchangeClearTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x001b534e482b92bb6daff452cd12f2e35219e13493)));
    address constant IMPLEMENTATION = address(uint160(uint256(0x00557c853e100600e0ee91e0df88fcf4af0097ff89)));
    address constant ADMIN = address(uint160(uint256(0x00140ac259be101d76691c512eb8105911f2f309f1)));
    address constant FACTORY = address(uint160(uint256(0x0036365dc6bd9513692978e4ea8f3117a7bae55f28)));
    address constant OWNER = address(uint160(uint256(0x0069b4b92f02ff415e0c966686e00d2783b395d690)));
    address constant USER = address(uint160(uint256(0x00fb94d3404c1d3d9d6f08f79e58041d5ea95accfa)));
    address constant USER_PROXY = address(uint160(uint256(0x00f2aab37083f0fb7dab82317c92b54249e8591bed)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    uint256 constant PENDING_WORD = 10_000_000_000 | (uint256(48_100_000) << 128);
    function pendingSlot() internal pure returns (bytes32) { return keccak256(abi.encode(USER, uint256(33))); }
    function balanceSlot() internal pure returns (bytes32) { return keccak256(abi.encode(USER, uint256(9))); }
    function setUp() public {
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPLEMENTATION, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.store(EXCHANGE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPLEMENTATION))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(EXCHANGE, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        vm.store(EXCHANGE, bytes32(uint256(3)), bytes32(uint256(1e12)));
        vm.store(EXCHANGE, bytes32(uint256(30)), bytes32(uint256(uint160(FACTORY))));
        vm.store(EXCHANGE, pendingSlot(), bytes32(PENDING_WORD));
        vm.store(EXCHANGE, balanceSlot(), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(uint256(100e18)));
        vm.store(EXCHANGE, bytes32(uint256(22)), bytes32((uint256(7) << 128) | uint256(100e18)));
        vm.mockCall(FACTORY, abi.encodeWithSelector(bytes4(0xc1a9a508), USER), abi.encode(USER_PROXY));
    }
    function asCaller(address caller, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return EXCHANGE.call(data);
    }
    function testOwnerClearsPending() public {
        vm.recordLogs();
        (bool ok, bytes memory out) = asCaller(OWNER, abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        require(ok && out.length == 0, "owner clear failed");
        require(vm.load(EXCHANGE, pendingSlot()) == bytes32(0), "pending not cleared");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == EXCHANGE, "clear log count");
        require(logs[0].topics.length == 3, "clear topic count");
        require(logs[0].topics[0] == 0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e, "clear topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(USER))), "clear user");
        require(logs[0].topics[2] == bytes32(uint256(uint160(USER_PROXY))), "clear proxy");
    }
    function testOutsiderCannotClear() public {
        (bool ok, bytes memory out) = asCaller(address(0xbeef), abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "outsider error");
        require(vm.load(EXCHANGE, pendingSlot()) == bytes32(PENDING_WORD), "outsider changed pending");
    }
    function testNoPendingRejects() public {
        vm.store(EXCHANGE, pendingSlot(), bytes32(0));
        (bool ok, bytes memory out) = asCaller(OWNER, abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x0984a617), "missing pending error");
    }
    function testClearThenReconcile() public {
        (bool ok,) = asCaller(OWNER, abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        require(ok, "clear failed");
        (ok,) = asCaller(OWNER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(50_000_000)));
        require(ok, "reconcile failed");
        require(vm.load(EXCHANGE, pendingSlot()) == bytes32(0), "pending recreated");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == 5e18 + 50e18, "user balance");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == 150e18, "treasury");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) == ((uint256(7) << 128) | uint256(150e18)), "total balance");
    }
}
"""


def runtime_rows():
    scope = json.loads(gzip.decompress(SCOPE.read_bytes()))
    assert scope["pin"] == 48_902_346
    rows = {row["address"]: row for row in scope["rows"]}
    assert rows[OLDER_PROXY]["implementation_word"][-40:] == OLDER_IMPL[2:]
    assert "0x" + Keccak()(b"clearPendingSweep(address)").hex()[:8] == CLEAR
    return scope, rows


def selectors(code):
    return {
        "0x" + found.group(1).hex(): int.from_bytes(found.group(2), "big")
        for found in re.finditer(b"\x63(.{4})\x14\x61(.{2})\x57", code[:4096], re.DOTALL)
    }


def static_checks(rows):
    old = bytes.fromhex(rows[OLDER_IMPL]["runtime"][2:])
    newer = bytes.fromhex(rows["0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"]["runtime"][2:])
    original_second = bytes.fromhex(rows["0x6f0e9deab8a4f21344e4c10a35db5027b02a67fa"]["runtime"][2:])
    pinned_second = bytes.fromhex(rows["0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"]["runtime"][2:])
    old_selectors, new_selectors = selectors(old), selectors(newer)
    assert len(old_selectors) == 96 and len(new_selectors) == 98
    assert set(new_selectors) - set(old_selectors) == EXPECTED_MISSING
    assert set(old_selectors) - set(new_selectors) == EXPECTED_ADDED
    assert set(selectors(original_second)) == set(selectors(pinned_second)) == set(new_selectors)
    assert old_selectors[CLEAR] == 0x3825
    assert CLEAR not in new_selectors
    assert RECONCILE in old_selectors and RECONCILE in new_selectors
    return {
        "older_implementation_sha256": hashlib.sha256(old).hexdigest(),
        "newest_implementation_sha256": hashlib.sha256(newer).hexdigest(),
        "older_selector_count": len(old_selectors),
        "newer_selector_count": len(new_selectors),
        "older_only_selectors": sorted(EXPECTED_ADDED),
        "newer_only_selectors": sorted(EXPECTED_MISSING),
        "clear_dispatch_pc": old_selectors[CLEAR],
    }


def run():
    scope, rows = runtime_rows()
    checked = static_checks(rows)
    solc = shutil.which("solc")
    assert solc
    with tempfile.TemporaryDirectory(prefix="papertrade-older-clear-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "OlderExchangeClear.t.sol").write_text(TEST_SOURCE)
        for name, address in (("Proxy", OLDER_PROXY), ("Implementation", OLDER_IMPL)):
            (project / "runtime" / f"{name}.hex").write_text(rows[address]["runtime"])
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True, text=True, check=False, timeout=60,
        )
    output = result.stdout + "\n" + result.stderr
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    if result.returncode or passed != TEST_NAMES:
        raise RuntimeError("older Exchange clear replay failed: " + output[-5000:])
    payload = {
        "pin": scope["pin"], "block_hash": scope["block_hash"],
        "exchange_proxy": OLDER_PROXY, "implementation": OLDER_IMPL,
        "factory": FACTORY, "clear_selector": CLEAR,
        "reconcile_selector": RECONCILE, "static_checks": checked,
        "test_names": sorted(passed),
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "forge_result": "4 passed, 0 failed",
        "limits": [
            "The owner, proxy, and factory addresses are pinned, while the pending word and accounting amounts are constructed local state.",
            "The factory proxyOf(address) response is mocked to the recorded older user proxy.",
            "The replay proves the older implementation path; it does not add clearPendingSweep to the newest deployed implementation or test a historical clear transaction.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def capture_pinned():
    scope, rows = runtime_rows()
    static_checks(rows)
    assert rows[OLDER_PROXY]["exchange_getters"]["owner"][-40:] == OWNER[2:]
    assert scope["earlier_factory_deployments"][0]["events"][0]["log"]["topics"][1][-40:] == USER[2:]
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    data = CLEAR + USER[2:].rjust(64, "0")
    cases = []
    for sender in (OWNER, OUTSIDER):
        request = {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                   "params": [{"from": sender, "to": OLDER_PROXY, "data": data}, hex(scope["pin"])]}
        web_request = urllib.request.Request(
            url, json.dumps(request).encode(), {"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(web_request, timeout=30) as response:
            result = json.load(response)
        cases.append({"sender": sender, "request": request, "response": result})
    payload = {"pin": scope["pin"], "block_hash": scope["block_hash"],
               "target": OLDER_PROXY, "selector": CLEAR, "user": USER, "cases": cases}
    PIN_CALLS.write_text(json.dumps(payload, indent=2) + "\n")
    return verify_pinned(scope)


def verify_pinned(scope):
    saved = json.loads(PIN_CALLS.read_text())
    assert saved["pin"] == scope["pin"] and saved["block_hash"] == scope["block_hash"]
    assert saved["target"] == OLDER_PROXY and saved["selector"] == CLEAR
    assert saved["user"] == USER and len(saved["cases"]) == 2
    for case, sender, error in zip(saved["cases"], (OWNER, OUTSIDER),
                                   ("0x0984a617", "0x30cd7471")):
        assert case["sender"] == sender
        assert case["request"] == {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
                                   "params": [{"from": sender, "to": OLDER_PROXY,
                                               "data": CLEAR + USER[2:].rjust(64, "0")},
                                              hex(scope["pin"])]}
        assert case["response"]["error"]["code"] == -32603
        assert f"output: Some({error})" in case["response"]["error"]["message"]
    return {"owner_no_pending_error": "0x0984a617", "outsider_error": "0x30cd7471"}


def verify():
    scope, rows = runtime_rows()
    saved = json.loads(OUT.read_text())
    assert saved["pin"] == scope["pin"] and saved["block_hash"] == scope["block_hash"]
    assert saved["exchange_proxy"] == OLDER_PROXY and saved["implementation"] == OLDER_IMPL
    assert saved["factory"] == FACTORY
    assert saved["clear_selector"] == CLEAR and saved["reconcile_selector"] == RECONCILE
    assert saved["static_checks"] == static_checks(rows)
    assert set(saved["test_names"]) == TEST_NAMES
    assert saved["test_source_sha256"] == hashlib.sha256(TEST_SOURCE.encode()).hexdigest()
    assert saved["forge_result"] == "4 passed, 0 failed"
    pinned = verify_pinned(scope)
    return {"older_clear_selector": CLEAR, "test_count": len(TEST_NAMES), **pinned}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="execute exact-runtime local Forge cases")
    parser.add_argument("--capture-pinned", action="store_true", help="save pinned archive eth_call reverts")
    args = parser.parse_args()
    assert not (args.run and args.capture_pinned)
    print(json.dumps(run() if args.run else capture_pinned() if args.capture_pinned else verify(), indent=2))


if __name__ == "__main__":
    main()
