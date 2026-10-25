#!/usr/bin/env python3
"""Exercise the Exchange three-address initializer on pinned proxy bytecode."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
OUT = ROOT / "artifacts" / "exchange_initializer_local" / "replay.json"
BEHAVIOR = ATLAS / "exchange_initializer_behavior.json"
TEST_NAMES = ["testInitializedCall", "testFreshCall", "testFreshBadToken",
              "testFreshEightDecimals", "testFreshEighteenDecimals", "testFreshNineteenDecimals"]
TEST_SOURCE = '''pragma solidity ^0.8.24;
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
contract MockDecimals6 { function decimals() external pure returns (uint8) { return 6; } }
contract MockDecimals8 { function decimals() external pure returns (uint8) { return 8; } }
contract MockDecimals18 { function decimals() external pure returns (uint8) { return 18; } }
contract MockDecimals19 { function decimals() external pure returns (uint8) { return 19; } }
contract ExchangeInitializerTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    function setUp() public {
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(PROXY, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
    }
    function callAs(address sender, address nextOwner, address oracle, address token) internal returns (bool, bytes memory) {
        vm.prank(sender);
        return PROXY.call(abi.encodeWithSelector(bytes4(0xc0c53b8b), nextOwner, oracle, token));
    }
    function testInitializedCall() public {
        MockDecimals6 token = new MockDecimals6();
        (bool ok, bytes memory out) = callAs(OWNER, OWNER, address(0x1234), address(token));
        require(!ok, "initialized should reject");
        require(out.length == 4 && bytes4(out) == bytes4(0x0dc149f0), "initialized error");
    }
    function testFreshCall() public {
        vm.store(PROXY, bytes32(0), bytes32(0));
        MockDecimals6 token = new MockDecimals6();
        vm.recordLogs();
        (bool ok, bytes memory out) = callAs(address(0xbeef), OWNER, address(0x1234), address(token));
        require(ok && out.length == 0, "fresh initialize");
        require(uint256(vm.load(PROXY, bytes32(0))) >> 16 == uint256(uint160(OWNER)), "fresh owner");
        require(uint256(vm.load(PROXY, bytes32(uint256(1)))) & type(uint160).max == uint256(uint160(OWNER)), "fresh guardian");
        require(uint256(vm.load(PROXY, bytes32(uint256(2)))) & type(uint160).max == 0x1234, "fresh oracle");
        require(uint256(vm.load(PROXY, bytes32(0))) & 0xffff == 1, "fresh flags");
        require(uint256(vm.load(PROXY, bytes32(uint256(3)))) == 1_000_000_000_000, "slot3");
        require(uint256(vm.load(PROXY, bytes32(uint256(4)))) & 0xff == 8, "slot4");
        require(uint256(vm.load(PROXY, bytes32(uint256(5)))) == 10_000_000_000, "slot5");
        require(uint256(vm.load(PROXY, bytes32(uint256(17)))) == 1, "slot17");
        for (uint256 slot = 23; slot <= 25; ++slot) {
            require(uint256(vm.load(PROXY, bytes32(slot))) == 20_000_000_000_000_000, "fee default");
        }
        require(uint256(vm.load(PROXY, bytes32(uint256(28)))) == 1_000_000_000_000_000_000, "slot28");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY, "fresh event count");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == keccak256("OwnerUpdated(address)"), "fresh event topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(OWNER))) && logs[0].data.length == 0, "fresh event payload");
    }
    function testFreshBadToken() public {
        vm.store(PROXY, bytes32(0), bytes32(0));
        (bool ok, bytes memory out) = callAs(address(0xbeef), OWNER, address(0x1234), address(0x9999));
        require(!ok && out.length == 0, "bad token decimals");
        require(vm.load(PROXY, bytes32(0)) == bytes32(0), "bad token rollback");
    }
    function testFreshEightDecimals() public {
        vm.store(PROXY, bytes32(0), bytes32(0));
        MockDecimals8 token = new MockDecimals8();
        (bool ok, bytes memory out) = callAs(address(0xbeef), OWNER, address(0x1234), address(token));
        require(ok && out.length == 0, "eight decimals");
        require(uint256(vm.load(PROXY, bytes32(uint256(4)))) & 0xff == 10, "eight slot4");
        require(uint256(vm.load(PROXY, bytes32(uint256(5)))) == 100_000_000, "eight scale");
    }
    function testFreshEighteenDecimals() public {
        vm.store(PROXY, bytes32(0), bytes32(0));
        MockDecimals18 token = new MockDecimals18();
        (bool ok, bytes memory out) = callAs(address(0xbeef), OWNER, address(0x1234), address(token));
        require(ok && out.length == 0, "eighteen decimals");
        require(uint256(vm.load(PROXY, bytes32(uint256(4)))) & 0xff == 18, "eighteen slot4");
        require(uint256(vm.load(PROXY, bytes32(uint256(5)))) == 1, "eighteen scale");
    }
    function testFreshNineteenDecimals() public {
        vm.store(PROXY, bytes32(0), bytes32(0));
        MockDecimals19 token = new MockDecimals19();
        (bool ok, bytes memory out) = callAs(address(0xbeef), OWNER, address(0x1234), address(token));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x6a426315), "nineteen decimals");
        require(vm.load(PROXY, bytes32(0)) == bytes32(0), "nineteen rollback");
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-exchange-initializer-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ExchangeInitializer.t.sol").write_text(TEST_SOURCE)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("Exchange initializer replay failed: " + output[-4000:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                               "selector": "0xc0c53b8b", "test_names": sorted(passed),
                               "forge_result": "6 passed, 0 failed",
                               "runtime_hashes": {label: manifest["contracts"][address]["sha256"]
                                                  for label, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
                               "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest()}, indent=2) + "\n")
    BEHAVIOR.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
        "selector": "0xc0c53b8b", "candidate_signature": "initialize(address,address,address)",
        "source_name_status": "unverified_candidate",
        "local_replay": "../../artifacts/exchange_initializer_local/replay.json",
        "fresh_state": "synthetic proxy with slot 0 reset to zero",
        "argument_roles": ["new owner and guardian", "oracle address", "token queried for decimals()"],
        "initial_storage": {"0": "(owner << 16) | 1", "1": "owner", "2": "oracle",
                            "3": "1000000000000", "17": "1",
                            "23": "20000000000000000", "24": "20000000000000000",
                            "25": "20000000000000000", "28": "1000000000000000000"},
        "tested_decimal_pairs": [{"token_decimals": 6, "slot4_low_byte": 8, "slot5": "10000000000"},
                                 {"token_decimals": 8, "slot4_low_byte": 10, "slot5": "100000000"},
                                 {"token_decimals": 18, "slot4_low_byte": 18, "slot5": "1"}],
        "owner_event": {"topic0": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
                        "signature": "OwnerUpdated(address)", "indexed_argument": "owner"},
        "tested_reverts": {"initialized": "0x0dc149f0", "token_decimals_19": "0x6a426315",
                           "noncontract_token": "0x"},
        "simulated_error_catalog": [
            {"selector": "0x0dc149f0", "probe_paths": ["testInitializedCall"]},
            {"selector": "0x6a426315", "probe_paths": ["testFreshNineteenDecimals"]}],
    }, indent=2) + "\n")
    print("6 exact-runtime Exchange initializer tests passed")


if __name__ == "__main__":
    main()
