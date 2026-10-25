#!/usr/bin/env python3
"""Replay fixed-revert selectors through exact Papertrade proxy bytecode offline."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "fixed_revert_local" / "replay.json"
ROLES = {
    "ExchangeProxy": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
    "ExchangeImplementation": "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee",
    "SessionProxy": "0x8326eb8896e358717f10502ec73ce8d28e37b108",
    "SessionImplementation": "0x8a5069fe303e8f81e91825436e956d595032e558",
    "StakingProxy": "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016",
    "StakingImplementation": "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15",
    "TokenomicsProxy": "0x75174549dbbd44497d31a47e2e2d7406408d63d9",
    "TokenomicsImplementation": "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f",
}
TEST_NAMES = ["testExchangeUnpause", "testExchangeFourArg", "testExchangeFiveArg",
              "testExchangeDirectClose", "testSessionThreeArg",
              "testTokenomicsQuoteRedemption", "testTokenomicsRedeem",
              "testTokenomicsSevenWord", "testStakingStake", "testStakingUnstake",
               "testStakingClaim", "testStakingDistribute"]
TEST_SOURCE = '''pragma solidity ^0.8.24;
interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function prank(address) external;
}
contract PapertradeFixedRevertTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant EXCHANGE_IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant SESSION_IMPL = address(uint160(uint256(0x008a5069fe303e8f81e91825436e956d595032e558)));
    address constant STAKING = address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016)));
    address constant STAKING_IMPL = address(uint160(uint256(0x00e6e3519455170913c5c3bfe541dd918a2d0cbb15)));
    address constant TOKENOMICS = address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9)));
    address constant TOKENOMICS_IMPL = address(uint160(uint256(0x00600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f)));
    function setUp() public {
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(EXCHANGE_IMPL, vm.parseBytes(vm.readFile("runtime/ExchangeImplementation.hex")));
        vm.store(EXCHANGE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(EXCHANGE_IMPL))));
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/SessionProxy.hex")));
        vm.etch(SESSION_IMPL, vm.parseBytes(vm.readFile("runtime/SessionImplementation.hex")));
        vm.store(SESSION, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(SESSION_IMPL))));
        vm.etch(STAKING, vm.parseBytes(vm.readFile("runtime/StakingProxy.hex")));
        vm.etch(STAKING_IMPL, vm.parseBytes(vm.readFile("runtime/StakingImplementation.hex")));
        vm.store(STAKING, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(STAKING_IMPL))));
        vm.etch(TOKENOMICS, vm.parseBytes(vm.readFile("runtime/TokenomicsProxy.hex")));
        vm.etch(TOKENOMICS_IMPL, vm.parseBytes(vm.readFile("runtime/TokenomicsImplementation.hex")));
        vm.store(TOKENOMICS, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(TOKENOMICS_IMPL))));
    }
    function check(address target, bytes memory data, bytes4 expected) internal {
        (bool ok, bytes memory out) = target.call(data);
        require(!ok, "call unexpectedly succeeded");
        require(out.length == 4, "wrong revert length");
        require(bytes4(out) == expected, "wrong revert selector");
    }
    function testExchangeUnpause() public {
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0xfb9f1009), uint32(0)), 0xd9d193d3);
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0xfb9f1009), type(uint32).max), 0xd9d193d3);
    }
    function testExchangeFourArg() public {
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0x1afd17e9), uint32(0), false, uint128(1), uint32(0)), 0x58f03bf7);
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0x1afd17e9), uint32(1), true, type(uint128).max, type(uint32).max), 0x58f03bf7);
    }
    function testExchangeFiveArg() public {
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0x63ca348f), uint32(0), false, uint128(1), uint32(0), false), 0x58f03bf7);
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0x63ca348f), uint32(1), true, type(uint128).max, type(uint32).max, true), 0x58f03bf7);
    }
    function testExchangeDirectClose() public {
        uint256[] memory empty = new uint256[](0);
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0x58d3ec6a), empty), 0x58f03bf7);
        uint256[] memory ids = new uint256[](2);
        ids[0] = 1; ids[1] = 2;
        check(EXCHANGE, abi.encodeWithSelector(bytes4(0x58d3ec6a), ids), 0x58f03bf7);
    }
    function testSessionThreeArg() public {
        check(SESSION, abi.encodeWithSelector(bytes4(0x17a1678f), address(0), uint64(0), address(0)), 0xd2dd8531);
        check(SESSION, abi.encodeWithSelector(bytes4(0x17a1678f), address(0xdead), type(uint64).max, address(0xbeef)), 0xd2dd8531);
    }
    function testTokenomicsQuoteRedemption() public {
        check(TOKENOMICS, abi.encodeWithSelector(bytes4(0xfe16eae8), uint256(0)), 0x32aa90b0);
        check(TOKENOMICS, abi.encodeWithSelector(bytes4(0xfe16eae8), type(uint256).max), 0x32aa90b0);
    }
    function testTokenomicsRedeem() public {
        check(TOKENOMICS, abi.encodeWithSelector(bytes4(0xdb006a75), uint256(0)), 0x32aa90b0);
        check(TOKENOMICS, abi.encodeWithSelector(bytes4(0xdb006a75), type(uint256).max), 0x32aa90b0);
    }
    function testTokenomicsSevenWord() public {
        check(TOKENOMICS, abi.encodeWithSelector(bytes4(0x7c7df7b4), address(0), uint256(0), uint256(0), uint64(0), uint8(0), uint256(0), uint256(0)), 0x32aa90b0);
        check(TOKENOMICS, abi.encodeWithSelector(bytes4(0x7c7df7b4), address(0xdead), type(uint256).max, uint256(1), type(uint64).max, type(uint8).max, uint256(2), uint256(3)), 0x32aa90b0);
    }
    function testStakingStake() public {
        check(STAKING, abi.encodeWithSelector(bytes4(0xa694fc3a), uint256(0)), 0xa15ce1ba);
        check(STAKING, abi.encodeWithSelector(bytes4(0xa694fc3a), type(uint256).max), 0xa15ce1ba);
    }
    function testStakingUnstake() public {
        check(STAKING, abi.encodeWithSelector(bytes4(0x2e17de78), uint256(0)), 0xa15ce1ba);
        check(STAKING, abi.encodeWithSelector(bytes4(0x2e17de78), type(uint256).max), 0xa15ce1ba);
    }
    function testStakingClaim() public {
        check(STAKING, abi.encodeWithSelector(bytes4(0x4e71d92d)), 0xa15ce1ba);
        vm.prank(address(0xdead));
        check(STAKING, abi.encodeWithSelector(bytes4(0x4e71d92d)), 0xa15ce1ba);
    }
    function testStakingDistribute() public {
        check(STAKING, abi.encodeWithSelector(bytes4(0xe4fc6b6d)), 0xa15ce1ba);
        vm.prank(address(0xdead));
        check(STAKING, abi.encodeWithSelector(bytes4(0xe4fc6b6d)), 0xa15ce1ba);
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    solc = shutil.which("solc")
    assert solc, "local solc is required; no network compiler downloads are allowed"
    runtimes = {}
    for name, address in ROLES.items():
        row = manifest["contracts"][address]
        raw = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(raw.removeprefix("0x"))).hexdigest() == row["sha256"]
        runtimes[name] = {"address": address, "sha256": row["sha256"], "hex": raw}
    with tempfile.TemporaryDirectory(prefix="papertrade-fixed-revert-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(solc) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "PapertradeFixedRevert.t.sol").write_text(TEST_SOURCE)
        for name, data in runtimes.items():
            (project / "runtime" / f"{name}.hex").write_text(data["hex"])
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                             capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("local fixed-revert replay failed: " + output[-1600:])
    result = {"pin": manifest["block"], "block_hash": manifest["block_hash"],
              "method": "port-free Forge in-process EVM; exact pinned proxy and implementation bytecode injected with vm.etch; EIP-1967 implementation slots set with vm.store; local solc and offline mode",
              "runtime_hashes": {name: {k: data[k] for k in ("address", "sha256")}
                                 for name, data in runtimes.items()},
              "test_names": sorted(passed), "canonical_call_count": 24,
              "expected_revert_selectors": {"0xfb9f1009": "0xd9d193d3", "0x1afd17e9": "0x58f03bf7",
                                            "0x63ca348f": "0x58f03bf7", "0x58d3ec6a": "0x58f03bf7",
                                            "0x17a1678f": "0xd2dd8531",
                                             "0xa694fc3a": "0xa15ce1ba", "0x2e17de78": "0xa15ce1ba",
                                             "0x4e71d92d": "0xa15ce1ba", "0xe4fc6b6d": "0xa15ce1ba",
                                            "0xfe16eae8": "0x32aa90b0", "0xdb006a75": "0x32aa90b0",
                                            "0x7c7df7b4": "0x32aa90b0"},
              "forge_result": "12 passed, 0 failed", "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("verified 24 canonical calls across 12 fixed-revert selectors through pinned proxy bytecode")


if __name__ == "__main__":
    main()
