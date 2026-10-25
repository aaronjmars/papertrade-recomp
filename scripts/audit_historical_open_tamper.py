#!/usr/bin/env python3
"""Test field binding of one archived signed open on pinned contract bytes."""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_factory_events import Keccak
from atlas_oracle_behavior import returndata
from audit_historical_open_replay import (
    BBO,
    CALLS,
    DIFF,
    HEADER,
    PRESTATE,
    RECEIPT,
    ROOT,
    TRANSACTION,
    s_address,
)

ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "audit_historical_open_tamper" / "replay.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
BIT_SLOT = "0x8be7a6db9ae01c1e8a6d06ac7b6ff6174b4a055ae5f4a5c03eefa753e0138970"
COUNTER_SLOT = "0x8cef51a82aa865b5a27446afaa6c44d4027085ad533c5fd8dd3b1c4f6d0be2a1"
ERROR = "0xc5045f22"
ORIGINAL_SIGNER = "0x6c2e9dbf11874a82c10c5841edbb85e550f1163f"


def inputs():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    prestate = json.loads(PRESTATE.read_text())
    header = json.loads(HEADER.read_text())
    calls = json.loads(CALLS.read_text())
    tx = json.loads(TRANSACTION.read_text())
    receipt = json.loads(RECEIPT.read_text())
    diff = json.loads(DIFF.read_text())
    call = calls["calls"][0]["calls"][0]
    assert calls["input"] == tx["input"] and calls["from"].lower() == tx["from"].lower()
    assert receipt["status"] == "0x1" and receipt["blockHash"] == header["hash"]
    assert receipt["blockNumber"] == header["number"]
    assert int(diff["post"][SESSION]["storage"][BIT_SLOT], 16) == 0x100
    assert int(diff["post"][SESSION]["storage"][COUNTER_SLOT], 16) == 1735912713
    assert call["to"].lower() == EXCHANGE and call["from"].lower() == BATCH
    assert call["input"].startswith("0xec6783f0") and len(call["input"]) == 2 + 8 + 11 * 64
    assert int(header["number"], 16) < manifest["block"]
    assert prestate[SESSION]["storage"][BIT_SLOT] == "0x" + "0" * 64
    assert int(prestate[SESSION]["storage"][COUNTER_SLOT], 16) == 1735912703
    code = {address: row["code"] for address, row in prestate.items()
            if row.get("code", "0x") != "0x"}
    for address, runtime in code.items():
        assert hashlib.sha256(bytes.fromhex(runtime[2:])).hexdigest() == manifest["contracts"][address]["sha256"]
    bbo_calls = []
    def visit(node):
        if node.get("to", "").lower() == BBO:
            bbo_calls.append(node)
        for child in node.get("calls", []):
            visit(child)
    visit(call)
    assert len(bbo_calls) == 1
    response = bbo_calls[0]["output"]
    assert len(response) == 130
    bbo_words = [int(response[i:i + 64], 16) for i in (2, 66)]
    words = [int(call["input"][10 + 64*i:10 + 64*(i+1)], 16) for i in range(11)]
    assert words[1] == words[2] == words[5] == 0 and words[7] > int(header["timestamp"], 16)
    mutations = [
        ("user", 0, words[0] + 1),
        ("instrument", 1, 1),
        ("side", 2, 1),
        ("size", 3, words[3] + 1),
        ("leverage", 4, words[4] + 1),
        ("useDebt", 5, 1),
        ("nonce", 6, words[6] + 1),
        ("deadline", 7, words[7] + 1),
    ]
    return manifest, prestate, header, call, code, bbo_words, mutations


def source_and_codes():
    manifest, prestate, header, call, codes, bbo_words, mutations = inputs()
    lines = []
    for address, row in sorted(prestate.items()):
        if address in codes:
            label = address[2:]
            lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{label}.hex")));')
        for slot, word in sorted(row.get("storage", {}).items()):
            if int(word, 16):
                lines.append(f"        vm.store({s_address(address)}, {slot}, {word});")
    words = [int(call["input"][10 + 64*i:10 + 64*(i+1)], 16) for i in range(11)]
    signed_calls = json.loads((ATLAS / "session_open_typehash_behavior.json").read_text())["calls"]
    signer_rows = [row for row in signed_calls if row["tx"] == json.loads(TRANSACTION.read_text())["hash"]
                   and row["call_index"] == 0]
    assert len(signer_rows) == 1 and signer_rows[0]["recovered_signer"] == ORIGINAL_SIGNER
    keccak = Keccak()
    def key_slot(user):
        outer = keccak(user.to_bytes(32, "big") + (4).to_bytes(32, "big"))
        return "0x" + keccak(int(ORIGINAL_SIGNER, 16).to_bytes(32, "big") + outer).hex()
    original_slot, copied_slot = key_slot(words[0]), key_slot(words[0] + 1)
    expiry_word = prestate[SESSION]["storage"][original_slot]
    assert int(expiry_word, 16) > int(header["timestamp"], 16)
    assert copied_slot not in prestate[SESSION]["storage"]
    typehash = json.loads((ATLAS / "session_open_typehash_behavior.json").read_text())["typehash"]
    domain = json.loads((ATLAS / "session_key_behavior.json").read_text())["domain_separator"]
    copied_control = f'''    function testMutateUserWithCopiedOriginalKey() public {{
        bytes memory data = hex"{call['input'][2:]}";
        assembly {{ mstore(add(data, 36), {words[0] + 1}) }}
        bytes32 structHash = keccak256(abi.encode({typehash},
            address(uint160({words[0] + 1})), uint32({words[1]}), false,
            uint128({words[3]}), uint32({words[4]}), false,
            uint256({words[6]}), uint64({words[7]})));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", bytes32({domain}), structHash));
        address recovered = ecrecover(digest, uint8({words[8]}), bytes32(uint256({words[9]})),
                                     bytes32(uint256({words[10]})));
        require(recovered != address(0) && recovered != {s_address(ORIGINAL_SIGNER)},
                "changed user changes recovered signer");
        vm.store({s_address(SESSION)}, {copied_slot}, {expiry_word});
        require(vm.load({s_address(SESSION)}, {copied_slot}) == {expiry_word},
                "copied authorization word");
        vm.prank({s_address(EXCHANGE)});
        (bool signerOk, bytes memory signerOut) = {s_address(SESSION)}.call(abi.encodeWithSelector(
            bytes4(0x7f608253), address(uint160({words[0] + 1})), structHash,
            uint8({words[8]}), bytes32(uint256({words[9]})), bytes32(uint256({words[10]}))));
        if (signerOk || signerOut.length != 4 || bytes4(signerOut) != bytes4({ERROR}))
            revert WrongResult(signerOk, signerOut);
        vm.recordLogs();
        vm.prank({s_address(BATCH)});
        (bool openOk, bytes memory openOut) = {s_address(EXCHANGE)}.call(data);
        if (openOk || openOut.length != 4 || bytes4(openOut) != bytes4({ERROR}))
            revert WrongResult(openOk, openOut);
        require(vm.getRecordedLogs().length == 0, "copied-key open emitted logs");
        require(vm.load({s_address(SESSION)}, {BIT_SLOT}) == 0, "original user nonce bit changed");
        require(vm.load({s_address(SESSION)}, {copied_slot}) == {expiry_word},
                "copied key word changed");
    }}'''
    functions = []
    for name, index, value in mutations:
        functions.append(f'''    function testMutate{name[0].upper() + name[1:]}() public {{
        bytes memory data = hex"{call['input'][2:]}";
        assembly {{ mstore(add(add(data, 36), mul({index}, 32)), {value}) }}
        vm.recordLogs();
        vm.prank({s_address(BATCH)});
        (bool ok, bytes memory out) = {s_address(EXCHANGE)}.call(data);
        if (ok || out.length != 4 || bytes4(out) != bytes4({ERROR})) revert WrongResult(ok, out);
        require(vm.getRecordedLogs().length == 0, "rejected open emitted logs");
        require(vm.load({s_address(SESSION)}, {BIT_SLOT}) == 0, "nonce bit changed");
        require(vm.load({s_address(SESSION)}, {COUNTER_SLOT}) == {prestate[SESSION]['storage'][COUNTER_SLOT]},
                "nonce counter changed");
    }}''')
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
contract HistoricalOpenTamperTest {{
    error WrongResult(bool ok, bytes output);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    function setUp() public {{
        vm.roll({int(header['number'], 16)});
        vm.warp({int(header['timestamp'], 16)});
        vm.chainId(999);
{chr(10).join(lines)}
        vm.etch({s_address(BBO)}, hex"{returndata(*bbo_words)[2:]}");
    }}
    function testOriginalDirectOpen() public {{
        vm.prank({s_address(BATCH)});
        (bool ok, bytes memory out) = {s_address(EXCHANGE)}.call(hex"{call['input'][2:]}");
        if (!ok || keccak256(out) != keccak256(hex"{call['output'][2:]}"))
            revert WrongResult(ok, out);
        require(vm.load({s_address(SESSION)}, {BIT_SLOT}) == bytes32(uint256(0x100)),
                "successful open nonce bit");
        require(vm.load({s_address(SESSION)}, {COUNTER_SLOT}) == bytes32(uint256(1735912713)),
                "successful open counter");
    }}
    function testOriginalReplayRejectedNextBlock() public {{
        vm.prank({s_address(BATCH)});
        (bool firstOk, bytes memory firstOut) = {s_address(EXCHANGE)}.call(hex"{call['input'][2:]}");
        if (!firstOk || keccak256(firstOut) != keccak256(hex"{call['output'][2:]}"))
            revert WrongResult(firstOk, firstOut);
        vm.roll(block.number + 1);
        vm.warp(block.timestamp + 1);
        vm.recordLogs();
        vm.prank({s_address(BATCH)});
        (bool replayOk, bytes memory replayOut) = {s_address(EXCHANGE)}.call(hex"{call['input'][2:]}");
        if (replayOk || replayOut.length != 4 || bytes4(replayOut) != bytes4(0x756688fe))
            revert WrongResult(replayOk, replayOut);
        require(vm.getRecordedLogs().length == 0, "replay emitted logs");
        require(vm.load({s_address(SESSION)}, {BIT_SLOT}) == bytes32(uint256(0x100)),
                "replay nonce bit changed");
        require(vm.load({s_address(SESSION)}, {COUNTER_SLOT}) == bytes32(uint256(1735912713)),
                "replay counter changed");
    }}
{copied_control}
{chr(10).join(functions)}
}}
'''
    return source, codes, mutations, call, header, manifest


def verify():
    source, codes, mutations, call, header, manifest = source_and_codes()
    saved = json.loads(OUT.read_text())
    assert saved["pin"] == manifest["block"] and saved["block_hash"] == manifest["block_hash"]
    assert saved["historical_block"] == int(header["number"], 16)
    assert saved["historical_block_hash"] == header["hash"]
    assert saved["original_calldata_sha256"] == hashlib.sha256(bytes.fromhex(call["input"][2:])).hexdigest()
    assert saved["source_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    assert saved["runtime_sha256"] == {
        address: hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() for address, code in codes.items()}
    assert saved["mutations"] == [{"field": name, "word_index": index, "replacement": str(value)}
                                  for name, index, value in mutations]
    assert saved["raw_error"] == ERROR
    assert saved["replay_error"] == "0x756688fe"
    assert saved["copied_original_key_control"] == "rejected"
    expected = {"testOriginalDirectOpen", "testOriginalReplayRejectedNextBlock",
                "testMutateUserWithCopiedOriginalKey"} | {
        "testMutate" + name[0].upper() + name[1:] for name, _, _ in mutations}
    assert len(saved["test_names"]) == len(expected) and set(saved["test_names"]) == expected
    assert saved["forge_result"] == f"{len(expected)} passed, 0 failed"
    return {"historical_block": saved["historical_block"],
            "mutations_rejected": len(mutations), "raw_error": ERROR,
            "baseline_direct_open": "success", "next_block_replay": "rejected",
            "copied_original_key_control": "rejected",
            "limits": saved["limits"]}


def run():
    source, codes, mutations, call, header, manifest = source_and_codes()
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-open-tamper-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "HistoricalOpenTamper.t.sol").write_text(source)
        for address, code in codes.items():
            (project / "runtime" / f"{address[2:]}.hex").write_text(code)
        forge = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                               check=False, capture_output=True, text=True, timeout=120)
    output = forge.stdout + "\n" + forge.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    expected = {"testOriginalDirectOpen", "testOriginalReplayRejectedNextBlock",
                "testMutateUserWithCopiedOriginalKey"} | {"testMutate" + name[0].upper() + name[1:]
                                              for name, _, _ in mutations}
    if forge.returncode or set(passed) != expected:
        raise RuntimeError("historical open tamper replay failed: " + output[-9000:])
    payload = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "historical_block": int(header["number"], 16), "historical_block_hash": header["hash"],
        "original_calldata_sha256": hashlib.sha256(bytes.fromhex(call["input"][2:])).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "runtime_sha256": {address: hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
                           for address, code in codes.items()},
        "mutations": [{"field": name, "word_index": index, "replacement": str(value)}
                      for name, index, value in mutations],
        "raw_error": ERROR, "replay_error": "0x756688fe",
        "copied_original_key_control": "rejected",
        "forge_result": f"{len(expected)} passed, 0 failed", "test_names": passed,
        "limits": ["One historical signed open and its archived transaction prestate are tested.",
                   "The local BBO precompile returns the response observed in the original trace.",
                   "Changing one ABI word tests these inputs only; other signature encodings and business states remain open.",
                   "The changed-user case reads an uncaptured session-key mapping; a separate local override copies the original signer authorization to isolate the changed digest.",
                   "The copied authorization is a local storage override, not a historical registration transaction."],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    return verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="rerun exact-runtime Forge cases")
    args = parser.parse_args()
    print(json.dumps(run() if args.run else verify(), indent=2))
