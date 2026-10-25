#!/usr/bin/env python3
"""Flip the HyperCore status word on identical pinned Exchange bytecode and storage."""

import argparse
import concurrent.futures
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_oracle_behavior import returndata

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "exchange_direct_status_local" / "replay.json"
STORAGE = OUT.parent / "pinned_direct_slots.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SAFE = "0xa90f96b5fcd5bdc0aae788c0485786b0e546d950"
FIRST_TX = "0x7c69ba558b4076ef20f880f89d910168cbd92e3cc0a2f70a564b2117f46fa6ac"
SECOND_TX = "0xd11efba2b91838576b957f7297677b46676ec7a27db60331377212f4de8ba771"
AMOUNT = 1_581_398_913

SOURCE_TEMPLATE = '''pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function roll(uint256) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract CoreWriterMock {
    bytes public lastInput;
    fallback() external { lastInput = msg.data; }
}
contract ExchangeDirectStatusTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant SAFE = address(uint160(uint256(0x00a90f96b5fcd5bdc0aae788c0485786b0e546d950)));
    address constant STATUS = address(0x0810);
    address constant CORE_BALANCE = address(0x0801);
    address constant CORE_WRITER = address(0x3333333333333333333333333333333333333333);
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 constant EVENT = 0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75;
    uint256 constant AMOUNT = 1581398913;
    function userSlot(uint256 base) internal pure returns (bytes32) {
        return keccak256(abi.encode(SAFE, base));
    }
    function setUp() public {
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.roll(48014628);
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(PROXY, ADMIN_SLOT, @@ADMIN_SLOT@@);
@@DIRECT_STORAGE@@
        vm.store(PROXY, userSlot(9), @@USER_BALANCE@@);
        vm.store(PROXY, userSlot(34), @@LAST_WITHDRAWAL@@);
        vm.etch(STATUS, hex"@@STATUS_ZERO_CODE@@");
        vm.etch(CORE_BALANCE, hex"@@CORE_BALANCE_CODE@@");
        CoreWriterMock writer = new CoreWriterMock();
        vm.etch(CORE_WRITER, address(writer).code);
    }
    function probe(uint256 status, uint256 expectedDebit, bool balanceMoves) internal {
        bytes32 balanceSlot = userSlot(9);
        bytes32 lastSlot = userSlot(34);
        uint256 oldBalance = uint256(vm.load(PROXY, balanceSlot));
        uint256 oldTreasury = uint256(vm.load(PROXY, bytes32(uint256(14))));
        uint256 oldTotal = uint256(vm.load(PROXY, bytes32(uint256(22))));
        vm.recordLogs();
        vm.prank(SAFE);
        (bool ok, bytes memory result) = PROXY.call(abi.encodeWithSelector(bytes4(0x7f99545a), AMOUNT));
        require(ok && result.length == 0, "withdrawal failed");
        require(oldTreasury - uint256(vm.load(PROXY, bytes32(uint256(14)))) == expectedDebit, "treasury debit");
        require(oldTotal - uint256(vm.load(PROXY, bytes32(uint256(22)))) == expectedDebit, "total debit");
        require(oldBalance - uint256(vm.load(PROXY, balanceSlot)) == (balanceMoves ? expectedDebit : 0), "user debit");
        require(uint256(vm.load(PROXY, lastSlot)) == block.number, "last withdrawal");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY, "log count");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == EVENT && logs[0].topics[1] == bytes32(uint256(uint160(SAFE))), "event topics");
        (uint256 debit, uint256 sent) = abi.decode(logs[0].data, (uint256, uint256));
        require(debit == expectedDebit && sent == AMOUNT * 100, "event values");
        bytes memory writerInput = CoreWriterMock(CORE_WRITER).lastInput();
        require(writerInput.length > 100 && writerInput[0] == 0x17 && writerInput[1] == 0x93 && writerInput[2] == 0x8e && writerInput[3] == 0x13, "CoreWriter call");
        require(status <= 1, "status assertion");
    }
    function testStatusZeroHeadroom() public {
        vm.store(PROXY, userSlot(9), @@HEADROOM_BALANCE@@);
        probe(0, (AMOUNT + 1000000) * 1e12, true);
    }
    function testStatusOneHeadroom() public {
        vm.store(PROXY, userSlot(9), @@HEADROOM_BALANCE@@);
        vm.etch(STATUS, hex"@@STATUS_ONE_CODE@@");
        probe(1, AMOUNT * 1e12, true);
    }
    function testStatusZeroExactBalanceRejected() public {
        vm.prank(SAFE);
        (bool ok, bytes memory out) = PROXY.call(abi.encodeWithSelector(bytes4(0x7f99545a), AMOUNT));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0xa3b9a36c), "zero-status exact balance error");
    }
    function testStatusOneExactBalance() public {
        vm.etch(STATUS, hex"@@STATUS_ONE_CODE@@");
        probe(1, AMOUNT * 1e12, true);
    }
}
'''


def source():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(STORAGE.read_text())
    assert saved["pin"] == manifest["block"] and saved["block_hash"] == manifest["block_hash"]
    assert saved["exchange_proxy"] == PROXY and len(saved["slots"]) == 38
    from atlas_exchange_direct_withdrawal import mapped
    first = json.loads((ROOT / "artifacts" / "historical" / f"{FIRST_TX}.state_diff.json").read_text())
    second_prestate = json.loads((ROOT / "artifacts" / "historical" / f"{SECOND_TX}.prestate.json").read_text())
    historical_slots = second_prestate[PROXY]["storage"]
    direct_values = {index: historical_slots.get(f"0x{index:064x}", saved["slots"][str(index)])
                     for index in range(38)}
    lines = [f"        vm.store(PROXY, bytes32(uint256({index})), {value});"
             for index, value in direct_values.items() if int(value, 16)]
    balance = historical_slots[mapped(SAFE, 9)]
    last_withdrawal = historical_slots[mapped(SAFE, 34)]
    headroom_balance = first["pre"][PROXY]["storage"][mapped(SAFE, 9)]
    second = json.loads((ROOT / "artifacts" / "historical" / f"{SECOND_TX}.calls.json").read_text())
    def walk(node):
        yield node
        for child in node.get("calls", []):
            yield from walk(child)
    core = next(node for node in walk(second) if node.get("to", "").lower().endswith("0801"))
    values = [int(core["output"][i:i + 64], 16) for i in range(2, len(core["output"]), 64)]
    admin = manifest["contracts"][PROXY]["eip1967_slots"]["admin"]
    output = SOURCE_TEMPLATE
    for before, after in {
        "@@ADMIN_SLOT@@": admin,
        "@@DIRECT_STORAGE@@": "\n".join(lines),
        "@@USER_BALANCE@@": balance,
        "@@HEADROOM_BALANCE@@": headroom_balance,
        "@@LAST_WITHDRAWAL@@": last_withdrawal,
        "@@STATUS_ZERO_CODE@@": returndata(0)[2:],
        "@@STATUS_ONE_CODE@@": returndata(1)[2:],
        "@@CORE_BALANCE_CODE@@": returndata(*values)[2:],
    }.items():
        assert output.count(before) == (2 if before in {"@@STATUS_ONE_CODE@@", "@@HEADROOM_BALANCE@@"} else 1)
        output = output.replace(before, after)
    return output


def capture_storage():
    from atlas_tokenomics import rpc
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(manifest["block"]), False])["hash"] == manifest["block_hash"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        values = list(pool.map(lambda index: rpc(url, "eth_getStorageAt", [PROXY, hex(index), hex(manifest["block"])]), range(38)))
    assert all(len(value) == 66 for value in values)
    STORAGE.parent.mkdir(parents=True, exist_ok=True)
    STORAGE.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                                   "exchange_proxy": PROXY,
                                   "slots": {str(index): value for index, value in enumerate(values)}}, indent=2) + "\n")


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    test_source = source()
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-direct-status-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ExchangeDirectStatus.t.sol").write_text(test_source)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != {"testStatusZeroHeadroom", "testStatusOneHeadroom", "testStatusZeroExactBalanceRejected", "testStatusOneExactBalance"}:
        raise RuntimeError("direct status replay failed: " + output[-5000:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                               "proxy": PROXY, "implementation": IMPLEMENTATION,
                               "runtime_hashes": {label: manifest["contracts"][address]["sha256"]
                                                  for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
                               "test_source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
                               "forge_result": "4 passed, 0 failed", "test_names": passed,
                               "same_state_raw_amount": AMOUNT,
                               "historical_prestate_transaction": SECOND_TX,
                               "historical_prestate_sha256": hashlib.sha256((ROOT / "artifacts" / "historical" / f"{SECOND_TX}.prestate.json").read_bytes()).hexdigest(),
                               "pinned_storage_sha256": hashlib.sha256(STORAGE.read_bytes()).hexdigest(),
                               "status_zero_expected_debit": str((AMOUNT + 1000000) * 10**12),
                               "status_one_expected_debit": str(AMOUNT * 10**12),
                               "status_zero_exact_balance_reverts": "0xa3b9a36c",
                               "status_one_exact_balance_clears_user_balance": True}, indent=2) + "\n")
    print("4 exact-runtime status and balance-boundary tests passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture_storage()
    main()
