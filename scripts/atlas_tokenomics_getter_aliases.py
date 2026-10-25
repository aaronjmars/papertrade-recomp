#!/usr/bin/env python3
"""Prove the two unnamed Tokenomics getter slots and one selector alias offline."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "tokenomics_getter_alias_behavior.json"
REPLAY_OUT = ROOT / "artifacts" / "tokenomics_getter_alias" / "replay.json"
PROXY = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
IMPLEMENTATION = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
SLOT5 = ("0x3886cade", "0xe9ed73e9")
SLOT6 = "0xc16017ca"
TEST_SOURCE = '''pragma solidity ^0.8.24;
interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract TokenomicsGetterAliasTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    address constant TOKENOMICS = address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9)));
    address constant TOKENOMICS_IMPL = address(uint160(uint256(0x00600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f)));
    function setUp() public {
        vm.etch(TOKENOMICS, vm.parseBytes(vm.readFile("runtime/TokenomicsProxy.hex")));
        vm.etch(TOKENOMICS_IMPL, vm.parseBytes(vm.readFile("runtime/TokenomicsImplementation.hex")));
        vm.store(TOKENOMICS, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(TOKENOMICS_IMPL))));
    }
    function check(bytes4 selector, uint256 expected) internal view {
        (bool ok, bytes memory out) = TOKENOMICS.staticcall(abi.encodeWithSelector(selector));
        require(ok && out.length == 32, "wrong call result");
        require(abi.decode(out, (uint256)) == expected, "wrong getter value");
    }
    function testTwoIndependentStorageValues() public {
        vm.store(TOKENOMICS, bytes32(uint256(5)), bytes32(uint256(7)));
        vm.store(TOKENOMICS, bytes32(uint256(6)), bytes32(uint256(11)));
        check(0x3886cade, 7);
        check(0xe9ed73e9, 7);
        check(0xc16017ca, 11);
        vm.store(TOKENOMICS, bytes32(uint256(5)), bytes32(uint256(17)));
        vm.store(TOKENOMICS, bytes32(uint256(6)), bytes32(uint256(29)));
        check(0x3886cade, 17);
        check(0xe9ed73e9, 17);
        check(0xc16017ca, 29);
    }
}
'''


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    proxy_row = manifest["contracts"][PROXY]
    implementation_row = manifest["contracts"][IMPLEMENTATION]
    assert int(proxy_row["eip1967_slots"]["implementation"], 16) == int(IMPLEMENTATION, 16)
    runtime_hex = {}
    for name, row in (("TokenomicsProxy", proxy_row), ("TokenomicsImplementation", implementation_row)):
        raw = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(raw.removeprefix("0x"))).hexdigest() == row["sha256"]
        runtime_hex[name] = raw
    runtime = bytes.fromhex(runtime_hex["TokenomicsImplementation"].removeprefix("0x"))
    for selector, pc in ((SLOT5[0], 0x1f7), (SLOT5[1], 0x1f7), (SLOT6, 0x340)):
        assert bytes.fromhex("63" + selector[2:] + "14" + f"61{pc:04x}" + "57") in runtime[:0x120]
    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", runtime_hex["TokenomicsImplementation"]],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1]
                    for line in disassembly.splitlines() if len(line) > 10 and line[8:10] == ": "}
    expected = {0x1f7: "JUMPDEST", 0x209: "PUSH1 0x20", 0x20c: "PUSH1 0x05",
                0x20e: "SLOAD", 0x214: "RETURN", 0x340: "JUMPDEST",
                0x352: "PUSH1 0x20", 0x355: "PUSH1 0x06", 0x357: "SLOAD",
                0x35d: "RETURN"}
    for pc, op in expected.items():
        assert instructions[pc] == op, (hex(pc), instructions[pc], op)
    catalog = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]
    archived_views = {row["selector"]: row for row in catalog["views"] if row["selector"] in (*SLOT5, SLOT6)}
    assert set(archived_views) == {*SLOT5, SLOT6}
    pinned = json.loads((ROOT / "artifacts" / "tokenomics_params" / "pinned_probes.json").read_text())
    assert pinned["pin_hash"] == manifest["block_hash"]
    for selector, slot in ((SLOT5[0], 5), (SLOT5[1], 5), (SLOT6, 6)):
        row = archived_views[selector]
        assert not row["failed"] and row["direct_slots"] == [slot]
        assert row["return_prefix"] == pinned["pinned_slots"][str(slot)]
        assert any(int(load["slot"], 16) == slot and load["depth"] == 2 for load in row["sloads"])
    solc = shutil.which("solc")
    assert solc, "local solc is required; no compiler download is allowed"
    with tempfile.TemporaryDirectory(prefix="papertrade-tokenomics-getters-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(solc) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "TokenomicsGetterAlias.t.sol").write_text(TEST_SOURCE)
        for name, raw in runtime_hex.items():
            (project / "runtime" / f"{name}.hex").write_text(raw)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                             capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    assert run.returncode == 0 and re.search(r"\[PASS\] testTwoIndependentStorageValues\(\)", output), output[-1600:]
    replay = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "method": "port-free Forge EVM with exact pinned proxy and implementation runtimes and EIP-1967 slot set locally",
        "runtime_hashes": {"proxy": proxy_row["sha256"], "implementation": implementation_row["sha256"]},
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "forge_result": "1 passed, 0 failed", "getters_checked": 3,
        "storage_cases": [{"slot5": 7, "slot6": 11}, {"slot5": 17, "slot6": 29}],
        "canonical_call_count": 6,
    }
    REPLAY_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPLAY_OUT.write_text(json.dumps(replay, indent=2) + "\n")
    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "tokenomics_proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": implementation_row["sha256"],
        "selector_behaviors": {SLOT5[0]: {"direct_slot": 5, "same_entry_as": SLOT5[1], "source_name_status": "unresolved"},
                               SLOT5[1]: {"direct_slot": 5, "candidate_signature": "lpFlatThresholdUsd()", "source_name_status": "hash-matching candidate only"},
                               SLOT6: {"direct_slot": 6, "source_name_status": "unresolved"}},
        "pinned_slot_values": {"5": pinned["pinned_slots"]["5"], "6": pinned["pinned_slots"]["6"]},
        "archived_trace_evidence": "storage_trace_catalog.json",
        "local_replay_evidence": "../../artifacts/tokenomics_getter_alias/replay.json",
        "limits": ["Function names for selectors 0x3886cade and 0xc16017ca remain unknown.",
                   "These direct getters expose mint-parameter slots; their future values can change through governance."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified three Tokenomics getter selectors across two storage overrides")


if __name__ == "__main__":
    main()
