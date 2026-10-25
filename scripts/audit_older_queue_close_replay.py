#!/usr/bin/env python3
"""Replay a historical older Exchange queue-gated close on captured runtime bytes."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

from atlas_older_settlement_history import OLD_LIBRARY, RUNTIME, SCOPE, TX, words
from atlas_older_settlement_history import OUT as HISTORY
from atlas_oracle_behavior import returndata
from atlas_tokenomics import rpc
from audit_historical_open_replay import s_address

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "deployer_scope"
PRESTATE = ARTIFACTS / "older_settlement_historical_prestate.json.gz"
HEADER = ARTIFACTS / "older_settlement_historical_header.json"
OUT = ARTIFACTS / "older_settlement_historical_replay.json"
BBO = "0x000000000000000000000000000000000000080e"


def children(node):
    for child in node.get("calls", []):
        yield child
        yield from children(child)


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    value = rpc(url, "debug_traceTransaction", [TX, {"tracer": "prestateTracer"}])
    PRESTATE.write_bytes(
        gzip.compress(json.dumps(value, separators=(",", ":")).encode(), compresslevel=9, mtime=0)
    )
    header = rpc(url, "eth_getBlockByNumber", [hex(42_770_131), False])
    HEADER.write_text(
        json.dumps({key: header[key] for key in ("number", "hash", "parentHash", "timestamp")}, indent=2)
        + "\n"
    )
    return verify(run_local=True, write=True)


def verify(run_local=False, write=False):
    assert not write or run_local
    saved = json.loads(gzip.decompress(HISTORY.read_bytes()))
    prestate = json.loads(gzip.decompress(PRESTATE.read_bytes()))
    header = json.loads(HEADER.read_text())
    scope = json.loads(gzip.decompress(SCOPE.read_bytes()))
    tx, receipt, trace, diff = (
        saved[key] for key in ("transaction", "receipt", "call_trace", "storage_diff")
    )
    assert tx["hash"].lower() == receipt["transactionHash"].lower() == TX
    assert tx["blockHash"].lower() == receipt["blockHash"].lower() == header["hash"].lower()
    assert header["parentHash"].lower() == saved["prestate_block"]["hash"].lower()
    assert int(header["number"], 16) == int(tx["blockNumber"], 16) == 42_770_131
    assert int(receipt["transactionIndex"], 16) == 0
    assert int(tx["value"], 16) == 0 and int(receipt["status"], 16) == 1
    assert trace["from"].lower() == tx["from"].lower()
    assert trace["to"].lower() == tx["to"].lower()
    assert trace["input"].lower() == tx["input"].lower()
    assert not trace.get("error")

    historical = {
        address.lower(): row["code"]
        for address, row in prestate.items()
        if row.get("code", "0x") != "0x"
    }
    pinned = {row["address"].lower(): row["runtime"] for row in scope["rows"]}
    pinned[OLD_LIBRARY] = RUNTIME.read_text().strip()
    assert len(historical) == 11 and set(historical) <= set(pinned)
    hashes = {}
    for address, code in historical.items():
        digest = hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
        assert digest == hashlib.sha256(bytes.fromhex(pinned[address][2:])).hexdigest()
        hashes[address] = digest
    for address, row in diff["pre"].items():
        for slot, value in row.get("storage", {}).items():
            assert int(prestate[address]["storage"][slot], 16) == int(value, 16)
    assert set(diff["post"]) <= set(prestate)

    bbo_calls = [node for node in children(trace) if node.get("to", "").lower() == BBO]
    assert len(bbo_calls) == 1 and len(bbo_calls[0]["output"]) == 130
    bbo_words = words(bbo_calls[0]["output"])
    assert len(bbo_words) == 2
    setup_lines = []
    for address, row in sorted(prestate.items()):
        if address in historical:
            setup_lines.append(
                f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));'
            )
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    expected_logs = receipt["logs"]
    log_lines = [f'        require(logs.length == {len(expected_logs)}, "log count");']
    for i, log in enumerate(expected_logs):
        log_lines.append(
            f'        require(logs[{i}].emitter == {s_address(log["address"])}, "log {i} emitter");'
        )
        log_lines.append(
            f'        require(logs[{i}].topics.length == {len(log["topics"])}, "log {i} topics");'
        )
        for j, topic in enumerate(log["topics"]):
            log_lines.append(
                f'        require(logs[{i}].topics[{j}] == {topic}, "log {i} topic {j}");'
            )
        log_lines.append(
            f'        require(keccak256(logs[{i}].data) == keccak256(hex"{log["data"][2:]}"), "log {i} data");'
        )
    post_lines = []
    for address, row in sorted(diff["post"].items()):
        for slot, value in sorted(row.get("storage", {}).items()):
            post_lines.append(
                f'        require(vm.load({s_address(address)}, {slot}) == {value}, "post {address} {slot}");'
            )
    assert len(expected_logs) == 6 and len(post_lines) == 13

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
contract OlderQueueCloseReplayTest {{
    error WrongResult(bool ok, bytes result);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    function setUp() public {{
        vm.roll({int(header["number"], 16)});
        vm.warp({int(header["timestamp"], 16)});
        vm.chainId(999);
{chr(10).join(setup_lines)}
        vm.etch({s_address(BBO)}, hex"{returndata(*bbo_words)[2:]}");
    }}
    function testHistoricalQueueGatedClose() public {{
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
        with tempfile.TemporaryDirectory(prefix="papertrade-older-queue-close-") as tmp:
            project = pathlib.Path(tmp)
            (project / "test").mkdir()
            (project / "runtime").mkdir()
            (project / "foundry.toml").write_text(
                '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
                '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
            )
            (project / "test" / "OlderQueueCloseReplay.t.sol").write_text(source)
            for address, code in historical.items():
                (project / "runtime" / f"{address[2:]}.hex").write_text(code)
            run = subprocess.run(
                ["forge", "test", "--root", tmp, "-vv"],
                check=False, capture_output=True, text=True, timeout=90,
            )
        output = run.stdout + "\n" + run.stderr
        if run.returncode or "[PASS] testHistoricalQueueGatedClose()" not in output:
            raise RuntimeError("historical older queue close replay failed: " + output[-9000:])
    result = {
        "transaction": TX,
        "block": int(header["number"], 16),
        "block_hash": header["hash"],
        "prestate_sha256": hashlib.sha256(PRESTATE.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "runtime_sha256": hashes,
        "mocked_bbo_output": bbo_calls[0]["output"],
        "receipt_logs_matched": len(expected_logs),
        "post_storage_words_matched": len(post_lines),
        "forge_result": "1 passed, 0 failed",
        "limits": [
            "The BBO precompile returns its observed archived response.",
            "The prestate tracer captures storage accessed by this transaction, not all historical state.",
            "The local call checks contract storage and logs, not sender nonce or Core settlement.",
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
    group.add_argument("--capture", action="store_true", help="capture transaction prestate and header")
    group.add_argument("--run", action="store_true", help="refresh local Forge replay ledger")
    args = parser.parse_args()
    result = capture() if args.capture else verify(run_local=args.run, write=args.run)
    print(json.dumps(result, indent=2))
