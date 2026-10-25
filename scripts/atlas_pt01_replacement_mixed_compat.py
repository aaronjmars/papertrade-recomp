#!/usr/bin/env python3
"""Counterfactual newest-suite mixed trade through the deployed older replacement."""

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile

from atlas_oracle_behavior import returndata
from audit_historical_close_replay import descendants
from audit_historical_open_replay import s_address

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
TX = "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5"
PRESTATE = ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json"
PROBES = ROOT / "artifacts" / "exchange_negative_close" / "local_probes.json"
CALLS = ROOT / "artifacts" / "historical" / f"{TX}.calls.json"
RECEIPT = ROOT / "artifacts" / "historical" / f"{TX}.receipt.json"
DIFF = ROOT / "artifacts" / "historical" / f"{TX}.state_diff.json"
OUT = ROOT / "artifacts" / "pt01_replacement_mixed_compat" / "replay.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
ORIGINAL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
REPLACEMENT = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
LIBRARY = "0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388"
CORE_WRITER = "0x3333333333333333333333333333333333333333"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
PRECOMPILES = {"080e": 2, "0810": 1, "0801": 3}


def verify(run_local=False, write=False):
    assert not write or run_local
    prestate = json.loads(PRESTATE.read_text())
    probes = json.loads(PROBES.read_text())
    calls = json.loads(CALLS.read_text())
    receipt = json.loads(RECEIPT.read_text())
    diff = json.loads(DIFF.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == 48_902_346
    assert receipt["transactionHash"].lower() == probes["source_tx"] == TX
    assert int(receipt["blockNumber"], 16) == probes["target_block"] == 48_901_631
    assert receipt["blockHash"] == probes["target_hash"]
    assert receipt["status"] == "0x1" and calls["value"] == "0x0"
    assert calls["input"].startswith("0x251fb27d")
    assert calls["from"] == probes["call"]["from"]
    assert calls["to"] == probes["call"]["to"]
    assert calls["input"] == probes["call"]["data"]
    inner = calls["calls"][0]["calls"]
    assert [node["input"][:10] for node in inner] == [
        "0x2792e706", "0x2792e706", "0x8d09f23f", "0x83115825"]
    assert all("error" not in node for node in inner)

    code_files = {}
    setup_lines = []
    for address, row in sorted(prestate.items()):
        code = row.get("code", "0x")
        if code != "0x":
            digest = hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
            if address != CORE_WRITER:
                assert digest == manifest["contracts"][address]["sha256"]
            code_files[address] = code
            setup_lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    assert len(code_files) == 17 and ORIGINAL in code_files and CORE_WRITER in code_files
    for address in (REPLACEMENT, LIBRARY):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        code_files[address] = code
        setup_lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
    for address, row in diff["pre"].items():
        for slot, value in row.get("storage", {}).items():
            assert int(prestate[address]["storage"][slot], 16) == int(value, 16)
    assert set(diff["post"]) <= set(prestate)

    precompile_outputs = {}
    for suffix, word_count in PRECOMPILES.items():
        nodes = [node for node in descendants(calls) if node.get("to", "").lower().endswith(suffix)]
        outputs = {node["output"] for node in nodes}
        assert nodes and len(outputs) == 1
        output = outputs.pop()
        assert len(output) == 2 + 64 * word_count
        values = [int(output[i:i + 64], 16) for i in range(2, len(output), 64)]
        precompile_outputs[suffix] = output
        setup_lines.append(f'        vm.etch({s_address(nodes[0]["to"])}, hex"{returndata(*values)[2:]}");')

    expected_logs = receipt["logs"]
    log_lines = [f'        require(logs.length == {len(expected_logs)}, "log count");']
    for i, log in enumerate(expected_logs):
        log_lines.append(f'        require(logs[{i}].emitter == {s_address(log["address"])}, "log {i} emitter");')
        log_lines.append(f'        require(logs[{i}].topics.length == {len(log["topics"])}, "log {i} topic count");')
        for j, topic in enumerate(log["topics"]):
            log_lines.append(f'        require(logs[{i}].topics[{j}] == {topic}, "log {i} topic {j}");')
        log_lines.append(f'        require(keccak256(logs[{i}].data) == keccak256(hex"{log["data"][2:]}"), "log {i} data");')
    post_lines = []
    for address, row in sorted(diff["post"].items()):
        for slot, value in sorted(row.get("storage", {}).items()):
            post_lines.append(f'        require(vm.load({s_address(address)}, {slot}) == {value}, "post {address} {slot}");')
    assert len(expected_logs) == 17 and len(post_lines) == 26

    source = f'''pragma solidity ^0.8.24;
interface Vm {{
    struct Log {{ bytes32[] topics; bytes data; address emitter; }}
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function warp(uint256) external;
    function roll(uint256) external;
    function chainId(uint256) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
}}
contract ReplacementMixedCompatTest {{
    error WrongResult(bool ok, bytes result);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    function setUp() public {{
        vm.roll({probes["target_block"]});
        vm.warp({int(probes["target_timestamp"], 16)});
        vm.chainId(999);
{chr(10).join(setup_lines)}
    }}
    function runMixed(bool replacement) internal {{
        if (replacement)
            vm.store({s_address(EXCHANGE)}, {IMPLEMENTATION_SLOT}, bytes32(uint256(uint160({s_address(REPLACEMENT)}))));
        vm.recordLogs();
        vm.prank({s_address(calls["from"])});
        (bool ok, bytes memory result) = {s_address(calls["to"])}.call(hex"{calls["input"][2:]}");
        if (!ok || keccak256(result) != keccak256(hex"{calls.get("output", "0x")[2:]}"))
            revert WrongResult(ok, result);
        Vm.Log[] memory logs = vm.getRecordedLogs();
{chr(10).join(log_lines)}
{chr(10).join(post_lines)}
    }}
    function testOriginalHistoricalMixed() public {{ runMixed(false); }}
    function testReplacementHistoricalMixed() public {{ runMixed(true); }}
}}
'''
    if run_local:
        assert shutil.which("forge") and shutil.which("solc")
        with tempfile.TemporaryDirectory(prefix="papertrade-pt01-mixed-compat-") as tmp:
            project = pathlib.Path(tmp)
            (project / "test").mkdir()
            (project / "runtime").mkdir()
            (project / "foundry.toml").write_text(
                '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
                '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
            )
            (project / "test" / "ReplacementMixedCompat.t.sol").write_text(source)
            for address, code in code_files.items():
                (project / "runtime" / f"{address[2:]}.hex").write_text(code)
            run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                                 check=False, capture_output=True, text=True, timeout=90)
        output = run.stdout + "\n" + run.stderr
        for name in ("testOriginalHistoricalMixed", "testReplacementHistoricalMixed"):
            if run.returncode or f"[PASS] {name}()" not in output:
                raise RuntimeError("replacement mixed compatibility replay failed: " + output[-9000:])
    result = {
        "source_transaction": TX,
        "historical_block": probes["target_block"],
        "historical_block_hash": probes["target_hash"],
        "prestate_sha256": hashlib.sha256(PRESTATE.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "runtime_sha256": {address: hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
                           for address, code in sorted(code_files.items())},
        "replacement_implementation": REPLACEMENT,
        "replacement_library": LIBRARY,
        "mocked_precompile_outputs": precompile_outputs,
        "receipt_logs_matched_each": len(expected_logs),
        "post_storage_words_matched_each": len(post_lines),
        "forge_result": "2 passed, 0 failed",
        "limits": [
            "The replacement is installed counterfactually at the historical newest-suite block.",
            "The HyperCore precompiles return their observed archived responses.",
            "The prestate tracer captures storage accessed by this transaction, not all historical state.",
            "One mixed transaction does not establish all trading paths, upgrade safety, or Core settlement.",
        ],
    }
    if write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2) + "\n")
    else:
        assert json.loads(OUT.read_text()) == result
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="refresh local Forge replay ledger")
    args = parser.parse_args()
    print(json.dumps(verify(run_local=args.run, write=args.run), indent=2))
