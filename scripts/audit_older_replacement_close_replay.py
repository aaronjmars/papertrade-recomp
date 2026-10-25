#!/usr/bin/env python3
"""Replay one post-upgrade older Exchange signed close on archived runtime bytes."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

from atlas_exchange_library import pnl_model, settlement_model, words
from atlas_oracle_behavior import returndata
from atlas_tokenomics import rpc
from audit_historical_open_replay import s_address
from audit_older_queue_close_replay import children

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "deployer_scope"
CAPTURE = ARTIFACTS / "older_replacement_signed_close.json.gz"
OUT = ARTIFACTS / "older_replacement_signed_close_replay.json"
SCOPE = ARTIFACTS / "pinned_capture.json.gz"
MANIFEST = ROOT / "atlas" / "block_48902346" / "manifest.json"
TX = "0xd0406da67e146d63014205b5c6b6cb8ada4c870ea7ceab0d17d73f34d5a2e968"
EXCHANGE = "0x2ede04561914c61a5f49212609541934fd7f5901"
REPLACEMENT = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
LIBRARY = "0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388"
BBO = "0x000000000000000000000000000000000000080e"
BLOCK = 48_102_995


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    transaction = rpc(url, "eth_getTransactionByHash", [TX])
    assert int(transaction["blockNumber"], 16) == BLOCK
    receipt = rpc(url, "eth_getTransactionReceipt", [TX])
    call_trace = rpc(url, "debug_traceTransaction", [TX, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
    prestate = rpc(url, "debug_traceTransaction", [TX, {"tracer": "prestateTracer"}])
    storage_diff = rpc(url, "debug_traceTransaction", [TX, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
    block_header = rpc(url, "eth_getBlockByNumber", [hex(BLOCK), False])
    block_header = {key: block_header[key] for key in ("number", "hash", "parentHash", "timestamp")}
    data = {"transaction": transaction, "receipt": receipt, "call_trace": call_trace,
            "prestate": prestate, "storage_diff": storage_diff, "block_header": block_header}
    CAPTURE.write_bytes(gzip.compress(json.dumps(data, separators=(",", ":")).encode(), compresslevel=9, mtime=0))
    return verify(run_local=True, write=True)


def verify(run_local=False, write=False):
    assert not write or run_local
    saved = json.loads(gzip.decompress(CAPTURE.read_bytes()))
    tx, receipt, trace, prestate, diff, header = (
        saved[key] for key in ("transaction", "receipt", "call_trace", "prestate", "storage_diff", "block_header")
    )
    assert tx["hash"].lower() == receipt["transactionHash"].lower() == TX
    assert tx["blockHash"].lower() == receipt["blockHash"].lower() == header["hash"].lower()
    assert int(header["number"], 16) == int(tx["blockNumber"], 16) == BLOCK
    assert int(receipt["transactionIndex"], 16) == int(tx["transactionIndex"], 16) == 3
    assert int(receipt["status"], 16) == 1 and int(tx["value"], 16) == 0
    assert int(tx["chainId"], 16) == 999
    assert trace["from"].lower() == tx["from"].lower()
    assert trace["to"].lower() == tx["to"].lower()
    assert trace["input"].lower() == tx["input"].lower()
    assert not trace.get("error")
    calls = list(children(trace))
    exchange_calls = [node for node in calls if node.get("to", "").lower() == EXCHANGE and node["input"].startswith("0x2792e706")]
    replacement_calls = [node for node in calls if node.get("to", "").lower() == REPLACEMENT and node["input"].startswith("0x2792e706")]
    assert len(exchange_calls) == len(replacement_calls) == 1
    assert not exchange_calls[0].get("error") and not replacement_calls[0].get("error")

    pinned_scope = json.loads(gzip.decompress(SCOPE.read_bytes()))
    pinned = {row["address"].lower(): row["runtime"] for row in pinned_scope["rows"]}
    manifest = json.loads(MANIFEST.read_text())
    for address, row in manifest["contracts"].items():
        if row.get("runtime_file"):
            pinned[address.lower()] = (MANIFEST.parent / row["runtime_file"]).read_text().strip()
    historical = {address.lower(): row["code"] for address, row in prestate.items() if row.get("code", "0x") != "0x"}
    assert len(historical) == 11 and set(historical) <= set(pinned)
    assert EXCHANGE in historical and REPLACEMENT in historical and LIBRARY in historical
    hashes = {}
    for address, code in sorted(historical.items()):
        digest = hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
        assert digest == hashlib.sha256(bytes.fromhex(pinned[address][2:])).hexdigest()
        hashes[address] = digest
    for address, row in diff["pre"].items():
        for slot, value in row.get("storage", {}).items():
            assert int(prestate[address]["storage"][slot], 16) == int(value, 16)
    assert set(diff["post"]) <= set(prestate)

    bbo_calls = [node for node in calls if node.get("to", "").lower() == BBO]
    assert len(bbo_calls) == 1
    bbo_words = words(bbo_calls[0]["output"])
    assert bbo_words == [823140, 823150]
    lib_calls = [node for node in calls if node.get("to", "").lower() == LIBRARY]
    assert len(lib_calls) == 2
    assert [node["input"][:10] for node in lib_calls] == ["0x82296364", "0xef1a27a9"]
    pnl_args = words("0x" + lib_calls[0]["input"][10:])
    settlement_args = words("0x" + lib_calls[1]["input"][10:])
    assert words(lib_calls[0]["output"]) == pnl_model(pnl_args)
    assert words(lib_calls[1]["output"]) == settlement_model(settlement_args)
    assert settlement_args[3] == words(lib_calls[0]["output"])[1]
    assert pnl_args[1] == sum(bbo_words) // 2

    setup_lines = []
    for address, row in sorted(prestate.items()):
        if address in historical:
            setup_lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    expected_logs = receipt["logs"]
    log_lines = [f'        require(logs.length == {len(expected_logs)}, "log count");']
    for i, log in enumerate(expected_logs):
        log_lines.append(f'        require(logs[{i}].emitter == {s_address(log["address"])}, "log {i} emitter");')
        log_lines.append(f'        require(logs[{i}].topics.length == {len(log["topics"])}, "log {i} topics");')
        for j, topic in enumerate(log["topics"]):
            log_lines.append(f'        require(logs[{i}].topics[{j}] == {topic}, "log {i} topic {j}");')
        log_lines.append(f'        require(keccak256(logs[{i}].data) == keccak256(hex"{log["data"][2:]}"), "log {i} data");')
    post_lines = []
    for address, row in sorted(diff["post"].items()):
        for slot, value in sorted(row.get("storage", {}).items()):
            post_lines.append(f'        require(vm.load({s_address(address)}, {slot}) == {value}, "post {address} {slot}");')
    assert len(expected_logs) == 5 and len(post_lines) == 11

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
contract OlderReplacementCloseReplayTest {{
    error WrongResult(bool ok, bytes result);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    function setUp() public {{
        vm.roll({BLOCK});
        vm.warp({int(header["timestamp"], 16)});
        vm.chainId(999);
{chr(10).join(setup_lines)}
        vm.etch({s_address(BBO)}, hex"{returndata(*bbo_words)[2:]}");
    }}
    function testHistoricalSignedClose() public {{
        vm.recordLogs();
        vm.prank({s_address(tx["from"])});
        (bool ok, bytes memory result) = {s_address(tx["to"])}.call(hex"{tx["input"][2:]}");
        if (!ok || keccak256(result) != keccak256(hex"{trace.get("output", "0x")[2:]}"))
            revert WrongResult(ok, result);
        Vm.Log[] memory logs = vm.getRecordedLogs();
{chr(10).join(log_lines)}
{chr(10).join(post_lines)}
    }}
}}
'''
    if run_local:
        assert shutil.which("forge") and shutil.which("solc")
        with tempfile.TemporaryDirectory(prefix="papertrade-older-replacement-close-") as tmp:
            project = pathlib.Path(tmp)
            (project / "test").mkdir()
            (project / "runtime").mkdir()
            (project / "foundry.toml").write_text(
                '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
                '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
            )
            (project / "test" / "OlderReplacementCloseReplay.t.sol").write_text(source)
            for address, code in historical.items():
                (project / "runtime" / f"{address[2:]}.hex").write_text(code)
            run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                                 check=False, capture_output=True, text=True, timeout=90)
        output = run.stdout + "\n" + run.stderr
        if run.returncode or "[PASS] testHistoricalSignedClose()" not in output:
            raise RuntimeError("historical replacement close replay failed: " + output[-9000:])
    result = {
        "transaction": TX,
        "block": BLOCK,
        "block_hash": header["hash"],
        "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "runtime_sha256": hashes,
        "mocked_bbo_output": bbo_calls[0]["output"],
        "pnl_arguments": pnl_args,
        "pnl_result": words(lib_calls[0]["output"]),
        "settlement_arguments": settlement_args,
        "settlement_result": words(lib_calls[1]["output"]),
        "receipt_logs_matched": len(expected_logs),
        "post_storage_words_matched": len(post_lines),
        "forge_result": "1 passed, 0 failed",
        "limits": [
            "The BBO precompile returns its observed archived response.",
            "The prestate tracer captures storage accessed by this transaction, not all historical state.",
            "The local call checks contract storage and logs, not sender nonce or Core settlement.",
            "One successful signed close does not cover all replacement branches or adversarial signatures.",
        ],
    }
    if write:
        OUT.write_text(json.dumps(result, indent=2) + "\n")
    else:
        assert json.loads(OUT.read_text()) == result
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--capture", action="store_true", help="refresh archive capture and local Forge ledger")
    group.add_argument("--run", action="store_true", help="refresh local Forge replay ledger")
    args = parser.parse_args()
    result = capture() if args.capture else verify(run_local=args.run, write=args.run)
    print(json.dumps(result, indent=2))
