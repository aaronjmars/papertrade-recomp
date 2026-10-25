#!/usr/bin/env python3
"""Counterfactual newest-suite signed open through the deployed older replacement."""

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile

from atlas_oracle_behavior import returndata
from audit_historical_open_replay import s_address

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
TX = "0xbfdbeb1a73a25264e1467b0f5be6646fb26f8ece631b1e2181133a49e2d0484c"
EVIDENCE = ROOT / "artifacts" / "audit_historical_open"
PRESTATE = EVIDENCE / f"{TX}.prestate.json"
HEADER = EVIDENCE / f"{TX}.header.json"
CALLS = ROOT / "artifacts" / "batch_executor" / f"{TX}.calls.json"
TRANSACTION = ROOT / "artifacts" / "batch_executor" / f"{TX}.tx.json"
RECEIPT = ROOT / "artifacts" / "exchange_positions" / f"{TX}.receipt.json"
DIFF = ROOT / "artifacts" / "exchange_positions" / f"{TX}.state_diff.json"
OUT = ROOT / "artifacts" / "pt01_replacement_trade_compat" / "replay.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
ORIGINAL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
REPLACEMENT = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
LIBRARY = "0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388"
BBO = "0x000000000000000000000000000000000000080e"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"


def descendants(node):
    for child in node.get("calls", []):
        yield child
        yield from descendants(child)


def verify(run_local=False, write=False):
    assert not write or run_local
    prestate = json.loads(PRESTATE.read_text())
    header = json.loads(HEADER.read_text())
    calls = json.loads(CALLS.read_text())
    tx = json.loads(TRANSACTION.read_text())
    receipt = json.loads(RECEIPT.read_text())
    diff = json.loads(DIFF.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == 48_902_346
    assert tx["hash"].lower() == receipt["transactionHash"].lower() == TX
    assert tx["blockHash"].lower() == receipt["blockHash"].lower() == header["hash"].lower()
    assert calls["input"].lower() == tx["input"].lower()
    assert calls["from"].lower() == tx["from"].lower()
    assert calls["to"].lower() == tx["to"].lower()
    assert receipt["status"] == "0x1" and int(tx["value"], 16) == 0
    first = calls["calls"][0]["calls"][0]
    assert first["to"].lower() == EXCHANGE and first["input"].startswith("0xec6783f0")
    assert first["output"] == "0x" + f"{0x15458f:064x}"
    bbo_calls = [node for node in descendants(calls) if node.get("to", "").lower() == BBO]
    assert len(bbo_calls) == 2 and len({node["output"] for node in bbo_calls}) == 1
    assert len(bbo_calls[0]["output"]) == 130
    bbo_words = [int(bbo_calls[0]["output"][i:i + 64], 16) for i in (2, 66)]
    assert len(bbo_words) == 2

    code_files = {}
    setup_lines = []
    for address, row in sorted(prestate.items()):
        code = row.get("code", "0x")
        if code != "0x":
            assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == manifest["contracts"][address]["sha256"]
            code_files[address] = code
            setup_lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    assert len(code_files) == 8 and ORIGINAL in code_files
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
    assert len(expected_logs) == 4 and len(post_lines) == 11

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
contract ReplacementTradeCompatTest {{
    error WrongResult(bool ok, bytes result);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    function setUp() public {{
        vm.roll({int(header["number"], 16)});
        vm.warp({int(header["timestamp"], 16)});
        vm.chainId(999);
{chr(10).join(setup_lines)}
        vm.etch({s_address(BBO)}, hex"{returndata(*bbo_words)[2:]}");
    }}
    function runOpen(bool replacement) internal {{
        if (replacement)
            vm.store({s_address(EXCHANGE)}, {IMPLEMENTATION_SLOT}, bytes32(uint256(uint160({s_address(REPLACEMENT)}))));
        vm.recordLogs();
        vm.prank({s_address(tx["from"])});
        (bool ok, bytes memory result) = {s_address(tx["to"])}.call(hex"{tx["input"][2:]}");
        if (!ok || keccak256(result) != keccak256(hex"{calls.get("output", "0x")[2:]}"))
            revert WrongResult(ok, result);
        Vm.Log[] memory logs = vm.getRecordedLogs();
{chr(10).join(log_lines)}
{chr(10).join(post_lines)}
    }}
    function testOriginalHistoricalOpen() public {{ runOpen(false); }}
    function testReplacementHistoricalOpen() public {{ runOpen(true); }}
}}
'''
    if run_local:
        assert shutil.which("forge") and shutil.which("solc")
        with tempfile.TemporaryDirectory(prefix="papertrade-pt01-trade-compat-") as tmp:
            project = pathlib.Path(tmp)
            (project / "test").mkdir()
            (project / "runtime").mkdir()
            (project / "foundry.toml").write_text(
                '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
                '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
            )
            (project / "test" / "ReplacementTradeCompat.t.sol").write_text(source)
            for address, code in code_files.items():
                (project / "runtime" / f"{address[2:]}.hex").write_text(code)
            run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                                 check=False, capture_output=True, text=True, timeout=90)
        output = run.stdout + "\n" + run.stderr
        for name in ("testOriginalHistoricalOpen", "testReplacementHistoricalOpen"):
            if run.returncode or f"[PASS] {name}()" not in output:
                raise RuntimeError("replacement trade compatibility replay failed: " + output[-9000:])
    result = {
        "source_transaction": TX,
        "historical_block": int(header["number"], 16),
        "historical_block_hash": header["hash"],
        "prestate_sha256": hashlib.sha256(PRESTATE.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "runtime_sha256": {address: hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
                           for address, code in sorted(code_files.items())},
        "replacement_implementation": REPLACEMENT,
        "replacement_library": LIBRARY,
        "mocked_bbo_output": bbo_calls[0]["output"],
        "receipt_logs_matched_each": len(expected_logs),
        "post_storage_words_matched_each": len(post_lines),
        "forge_result": "2 passed, 0 failed",
        "limits": [
            "The replacement is installed counterfactually at the historical newest-suite block.",
            "The BBO precompile returns its observed archived response.",
            "The prestate tracer captures storage accessed by this transaction, not all historical state.",
            "One signed open does not establish other trading paths, upgrade safety, or Core settlement.",
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
