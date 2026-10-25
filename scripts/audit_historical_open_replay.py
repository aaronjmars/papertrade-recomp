#!/usr/bin/env python3
"""Offline exact-runtime replay of a historical successful signed open."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_oracle_behavior import returndata


ROOT = pathlib.Path(__file__).resolve().parents[1]
TX = "0xbfdbeb1a73a25264e1467b0f5be6646fb26f8ece631b1e2181133a49e2d0484c"
EVIDENCE = ROOT / "artifacts" / "audit_historical_open"
PRESTATE = EVIDENCE / f"{TX}.prestate.json"
HEADER = EVIDENCE / f"{TX}.header.json"
CALLS = ROOT / "artifacts" / "batch_executor" / f"{TX}.calls.json"
TRANSACTION = ROOT / "artifacts" / "batch_executor" / f"{TX}.tx.json"
RECEIPT = ROOT / "artifacts" / "exchange_positions" / f"{TX}.receipt.json"
DIFF = ROOT / "artifacts" / "exchange_positions" / f"{TX}.state_diff.json"
OUT = EVIDENCE / "replay.json"
BBO = "0x000000000000000000000000000000000000080e"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"


def s_address(value):
    return "address(uint160(uint256(0x00" + value[2:] + ")))"


def main():
    prestate = json.loads(PRESTATE.read_text())
    header = json.loads(HEADER.read_text())
    calls = json.loads(CALLS.read_text())
    tx = json.loads(TRANSACTION.read_text())
    receipt = json.loads(RECEIPT.read_text())
    diff = json.loads(DIFF.read_text())
    manifest = json.loads((ROOT / "atlas" / "block_48902346" / "manifest.json").read_text())
    assert tx["hash"].lower() == TX
    assert receipt["blockHash"].lower() == header["hash"]
    assert receipt["blockNumber"] == header["number"]
    assert calls["input"].lower() == tx["input"].lower()
    assert calls["from"].lower() == tx["from"].lower()
    assert calls["to"].lower() == tx["to"].lower()
    assert int(tx["value"], 16) == 0
    assert receipt["status"] == "0x1"

    first = calls["calls"][0]["calls"][0]
    assert first["to"].lower() == EXCHANGE
    assert first["input"].startswith("0xec6783f0")
    assert first["output"] == "0x" + f"{0x15458f:064x}"
    bbo_calls = []

    def visit(node):
        if node.get("to", "").lower() == BBO:
            bbo_calls.append(node)
        for child in node.get("calls", []):
            visit(child)

    visit(first)
    assert len(bbo_calls) == 1 and bbo_calls[0]["output"].startswith("0x")
    bbo_words = [int(bbo_calls[0]["output"][i:i + 64], 16) for i in (2, 66)]
    assert len(bbo_calls[0]["output"]) == 130

    account_code = {address: row["code"] for address, row in prestate.items()
                    if row.get("code", "0x") != "0x"}
    for address, code in account_code.items():
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == manifest["contracts"][address]["sha256"]
    for address, row in diff["pre"].items():
        for slot, value in row.get("storage", {}).items():
            assert int(prestate[address]["storage"][slot], 16) == int(value, 16)
    code_files = {}
    store_lines = []
    for address, row in sorted(prestate.items()):
        if address in account_code:
            label = address[2:]
            code_files[label] = account_code[address]
            store_lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{label}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                store_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    for address, row in sorted(diff["post"].items()):
        if "storage" not in row:
            continue
        assert address in prestate
    post_lines = []
    for address, row in sorted(diff["post"].items()):
        for slot, value in sorted(row.get("storage", {}).items()):
            post_lines.append(
                f'        require(vm.load({s_address(address)}, {slot}) == {value}, "post {address} {slot}");')
    assert len(post_lines) == 11

    expected_logs = receipt["logs"]
    log_lines = [f'        require(logs.length == {len(expected_logs)}, "log count");']
    for i, log in enumerate(expected_logs):
        log_lines.append(f'        require(logs[{i}].emitter == {s_address(log["address"])}, "log {i} emitter");')
        log_lines.append(f'        require(logs[{i}].topics.length == {len(log["topics"])}, "log {i} topics count");')
        for j, topic in enumerate(log["topics"]):
            log_lines.append(f'        require(logs[{i}].topics[{j}] == {topic}, "log {i} topic {j}");')
        log_lines.append(f'        require(keccak256(logs[{i}].data) == keccak256(hex"{log["data"][2:]}"), "log {i} data");')

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
contract HistoricalOpenReplayTest {{
    error WrongResult(bool ok, bytes result);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    function setUp() public {{
        vm.roll({int(header["number"], 16)});
        vm.warp({int(header["timestamp"], 16)});
        vm.chainId(999);
{chr(10).join(store_lines)}
        vm.etch({s_address(BBO)}, hex"{returndata(*bbo_words)[2:]}");
    }}
    function testHistoricalSignedOpen() public {{
        vm.recordLogs();
        vm.prank({s_address(tx["from"])});
        (bool ok, bytes memory result) = {s_address(tx["to"])}.call(hex"{tx["input"][2:]}");
        if (!ok || keccak256(result) != keccak256(hex"{calls.get("output", "0x")[2:]}"))
            revert WrongResult(ok, result);
        Vm.Log[] memory logs = vm.getRecordedLogs();
{chr(10).join(log_lines)}
{chr(10).join(post_lines)}
    }}
}}
'''
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-historical-open-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "HistoricalOpenReplay.t.sol").write_text(source)
        for label, code in code_files.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                             capture_output=True, text=True, timeout=90)
    output = run.stdout + "\n" + run.stderr
    if run.returncode or "[PASS] testHistoricalSignedOpen()" not in output:
        raise RuntimeError("historical open replay failed: " + output[-9000:])
    ledger = {
        "transaction": TX,
        "block": int(header["number"], 16),
        "block_hash": header["hash"],
        "successful_open_id": int(first["output"], 16),
        "prestate_sha256": hashlib.sha256(PRESTATE.read_bytes()).hexdigest(),
        "prestate_capture": "archive debug_traceTransaction prestateTracer by public transaction hash",
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "runtime_sha256": {address: hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
                           for address, code in account_code.items()},
        "runtime_identity": "all eight archived contract runtimes match the pinned manifest SHA-256 hashes",
        "mocked_precompile": BBO,
        "mocked_precompile_response": bbo_calls[0]["output"],
        "post_storage_words_matched": len(post_lines),
        "receipt_logs_matched": len(expected_logs),
        "forge_result": "1 passed, 0 failed",
        "limitations": ["HyperCore BBO precompile replayed with its observed response",
                        "Archive prestate records storage read by this transaction, not every historical slot"],
    }
    OUT.write_text(json.dumps(ledger, indent=2) + "\n")
    print(f"historical signed open: 1 pass, {len(expected_logs)} logs, {len(post_lines)} storage words")


if __name__ == "__main__":
    main()
