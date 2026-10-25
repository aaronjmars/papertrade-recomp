#!/usr/bin/env python3
"""Offline exact-runtime replay of a mixed signed-close transaction."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_exchange_library import pnl_model, settlement_model
from atlas_factory_events import Keccak
from atlas_oracle_behavior import returndata
from audit_historical_open_replay import s_address

ROOT = pathlib.Path(__file__).resolve().parents[1]
TX = "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5"
HISTORICAL = ROOT / "artifacts" / "historical"
EVIDENCE = ROOT / "artifacts" / "exchange_negative_close"
OUT = ROOT / "artifacts" / "audit_historical_close" / "replay.json"
MIXED_CASE = ROOT / "scripts" / "audit_mixed_four_close.sol.inc"
MARKET1_GETTERS = ROOT / "artifacts" / "exchange_instruments_getter" / "pinned_getters.json"
MARKET1_FIELDS = ROOT / "artifacts" / "exchange_market_fields" / "pinned_probes.json"
MARKET1_TEMPLATES = {
    1394058: "0xa6b54a591e6031dd4a8e858f0d1d74d60aaa7b9f00d6eabd483ce0d9fb7d6a66",
    1394060: "0x71015d2eb7e87c4a9b8e1c2832eaa6a91c62626675ae268a6be0b43801751989",
}
PRESTATE = EVIDENCE / "original_prestate.json"
CALLS = HISTORICAL / f"{TX}.calls.json"
RECEIPT = HISTORICAL / f"{TX}.receipt.json"
DIFF = HISTORICAL / f"{TX}.state_diff.json"
PROBES = EVIDENCE / "local_probes.json"
PRECOMPILES = {"080e": 2, "0810": 1, "0801": 3}
CORE_WRITER = "0x3333333333333333333333333333333333333333"
EXCHANGE_ADDRESS = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"


def descendants(node):
    for child in node.get("calls", []):
        yield child
        yield from descendants(child)


def market1_sources(manifest):
    getters = json.loads(MARKET1_GETTERS.read_text())
    assert getters["pin"] == manifest["block"]
    assert getters["block_hash"] == manifest["block_hash"]
    keccak = Keccak()
    row = next(row for row in getters["rows"] if row["instrument_id"] == 1)
    assert len(row["storage_words"]) == 3
    assert int(row["mapping_root"], 16) == int.from_bytes(keccak(
        (1).to_bytes(32, "big") + (7).to_bytes(32, "big")), "big")
    replacements = {"__MARKET1_CONFIG_ROOT__": row["mapping_root"]}
    for i, value in enumerate(row["storage_words"]):
        replacements[f"__MARKET1_CONFIG_{i}__"] = value
    fields = json.loads(MARKET1_FIELDS.read_text())
    assert fields["pin_block"] == manifest["block"]
    assert fields["pin_hash"] == manifest["block_hash"]
    market = next(row for row in fields["markets"] if row["instrument"] == 1)
    assert len(market["raw_words"]) == 2
    assert int(market["base_slot"], 16) == int.from_bytes(keccak(
        (1).to_bytes(32, "big") + (36).to_bytes(32, "big")), "big")
    replacements["__MARKET1_FIELDS_ROOT__"] = market["base_slot"]
    for i, value in enumerate(market["raw_words"]):
        replacements[f"__MARKET1_FIELDS_{i}__"] = value
    template_sources = {}
    for position_id, tx in MARKET1_TEMPLATES.items():
        path = ROOT / "artifacts" / "exchange_positions" / f"{tx}.state_diff.json"
        diff = json.loads(path.read_text())
        storage = diff["post"][EXCHANGE_ADDRESS]["storage"]
        assert storage
        slot = int.from_bytes(keccak(position_id.to_bytes(32, "big") + (10).to_bytes(32, "big")), "big")
        word0, word1 = (storage[f"0x{slot + i:064x}"] for i in (0, 1))
        assert (int(word0, 16) >> 160) & (2**32 - 1) == 1
        assert int(word0, 16) >> 192 == 235015
        assert int(word1, 16) >> 240 & 1
        assert (int(word1, 16) >> 224) & 1 == (1 if position_id == 1394058 else 0)
        for i, word in enumerate((word0, word1)):
            replacements[f"__POSITION_{position_id}_WORD{i}__"] = word
        template_sources[str(position_id)] = {"state_diff": str(path.relative_to(ROOT)),
                                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return replacements, template_sources


def trace_words(payload, signed_positions=()):
    assert payload and len(payload) % 64 == 0
    values = [int(payload[i:i + 64], 16) for i in range(0, len(payload), 64)]
    for i in signed_positions:
        if values[i] >= 2**255:
            values[i] -= 2**256
    return values


def cross_market_math_trace(output):
    lines = output.splitlines()
    tests = [(i, match.group(1)) for i, line in enumerate(lines)
             if (match := re.match(r"\[PASS\] (test\w+)\(\)", line))]
    targets = {"testFourCrossMarketZeroFirstClose": [0, 1, 0, 1],
               "testFourCrossMarketOneFirstClose": [1, 0, 1, 0]}
    result = {}
    for j, (start, name) in enumerate(tests):
        if name not in targets:
            continue
        section = lines[start + 1:tests[j + 1][0] if j + 1 < len(tests) else len(lines)]
        math_calls, settlements, events = [], [], []
        for i, line in enumerate(section):
            match = re.search(r"::(82296364|ef1a27a9)\(([0-9a-f]+)\) \[delegatecall\]", line)
            if match:
                returned = re.search(r"\[Return\] 0x([0-9a-f]+)", section[i + 1])
                assert returned, (name, i)
                if match.group(1) == "82296364":
                    args = trace_words(match.group(2))
                    outputs = trace_words(returned.group(1), (0, 1))
                    assert len(args) == 9 and len(outputs) == 2
                    assert outputs == pnl_model(args)
                    math_calls.append((args, outputs))
                else:
                    args = trace_words(match.group(2), (3,))
                    outputs = trace_words(returned.group(1))
                    assert len(args) == 8 and len(outputs) == 6
                    assert outputs == settlement_model(args)
                    settlements.append((args, outputs))
            if "topic 0: 0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf" in line:
                position_id = int(section[i + 1].split("topic 1: 0x")[1], 16)
                event = trace_words(section[i + 3].split("data: 0x")[1], (1, 2))
                assert len(event) == 5
                events.append((position_id, event))
        assert len(math_calls) == len(settlements) == len(events) == 4, name
        rows = []
        for i, ((math_args, math_out), (settlement_args, settlement_out),
                (position_id, event)) in enumerate(zip(math_calls, settlements, events)):
            market = 0 if math_args[1] == 808455 else 1 if math_args[1] == 234900 else -1
            assert market == targets[name][i]
            assert position_id == i + 1 and event[:3] == [math_args[1], *math_out]
            assert settlement_args[2:4] == [math_args[2], math_out[1]]
            assert settlement_out[4] + settlement_out[5] == event[4]
            rows.append({"position_id": position_id, "market_id": market,
                         "math_arguments": [str(x) for x in math_args],
                         "math_returns": [str(x) for x in math_out],
                         "settlement_arguments": [str(x) for x in settlement_args],
                         "settlement_returns": [str(x) for x in settlement_out],
                         "event_fields": [str(x) for x in event]})
        result[name] = rows
    assert set(result) == set(targets)
    return result


def main():
    prestate = json.loads(PRESTATE.read_text())
    calls = json.loads(CALLS.read_text())
    receipt = json.loads(RECEIPT.read_text())
    diff = json.loads(DIFF.read_text())
    probes = json.loads(PROBES.read_text())
    manifest = json.loads((ROOT / "atlas" / "block_48902346" / "manifest.json").read_text())
    assert receipt["transactionHash"].lower() == probes["source_tx"] == TX
    assert int(receipt["blockNumber"], 16) == probes["target_block"] == 48901631
    assert receipt["blockHash"] == probes["target_hash"]
    assert receipt["status"] == "0x1"
    assert calls["input"].startswith("0x251fb27d")
    assert calls["value"] == "0x0"
    assert calls["from"] == probes["call"]["from"]
    assert calls["to"] == probes["call"]["to"]
    assert calls["input"] == probes["call"]["data"]

    inner = calls["calls"][0]["calls"]
    assert [item["input"][:10] for item in inner] == [
        "0x2792e706", "0x2792e706", "0x8d09f23f", "0x83115825"]
    assert all("error" not in item for item in inner)
    for address, row in diff["pre"].items():
        for slot, value in row.get("storage", {}).items():
            assert int(prestate[address]["storage"][slot], 16) == int(value, 16)

    account_code = {address: row["code"] for address, row in prestate.items()
                    if row.get("code", "0x") != "0x"}
    assert len(account_code) == 17
    for address, code in account_code.items():
        digest = hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
        if address != CORE_WRITER:
            assert digest == manifest["contracts"][address]["sha256"]
    assert CORE_WRITER in account_code
    code_files = {address[2:]: code for address, code in account_code.items()}
    setup_lines = []
    for address, row in sorted(prestate.items()):
        if address in account_code:
            setup_lines.append(
                f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    precompile_outputs = {}
    for suffix, expected_words in PRECOMPILES.items():
        nodes = [node for node in descendants(calls)
                 if node.get("to", "").lower().endswith(suffix)]
        outputs = {node["output"] for node in nodes}
        assert nodes and len(outputs) == 1
        output = outputs.pop()
        assert len(output) == 2 + 64 * expected_words
        values = [int(output[i:i + 64], 16)
                  for i in range(2, len(output), 64)]
        precompile_outputs[suffix] = output
        setup_lines.append(
            f'        vm.etch({s_address(nodes[0]["to"])}, hex"{returndata(*values)[2:]}");')

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
            post_lines.append(
                f'        require(vm.load({s_address(address)}, {slot}) == {value}, "post {address} {slot}");')
    assert len(post_lines) == 26

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
    function mockCall(address, bytes calldata, bytes calldata) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function sign(uint256, bytes32) external returns (uint8, bytes32, bytes32);
    function addr(uint256) external returns (address);
}}
contract HistoricalCloseReplayTest {{
    error WrongResult(bool ok, bytes result);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant BATCH = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant USER = address(uint160(uint256(0x00e05fcc23807536bee418f142d19fa0d21bb0cff7)));
    bytes32 constant CLOSE_TYPEHASH = 0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13;
    bytes32 constant DOMAIN = 0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77;
    uint256 constant NONCE = 42;
    function positionSlot(uint256 id) internal pure returns (bytes32) {{
        return keccak256(abi.encode(id, uint256(10)));
    }}
    function setUp() public {{
        vm.roll({probes["target_block"]});
        vm.warp({int(probes["target_timestamp"], 16)});
        vm.chainId(999);
{chr(10).join(setup_lines)}
    }}
    function testHistoricalMixedSignedCloses() public {{
        vm.recordLogs();
        vm.prank({s_address(calls["from"])});
        (bool ok, bytes memory result) = {s_address(calls["to"])}.call(hex"{calls["input"][2:]}");
        if (!ok || keccak256(result) != keccak256(hex"{calls.get("output", "0x")[2:]}"))
            revert WrongResult(ok, result);
        Vm.Log[] memory logs = vm.getRecordedLogs();
{chr(10).join(log_lines)}
{chr(10).join(post_lines)}
    }}
    function testFourConstructedActivePositionsClose() public {{
        address sessionKey = vm.addr(0xb0b);
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(sessionKey, outer)),
                 bytes32(uint256(block.timestamp + 3600)));
        bytes32 originalSlot = positionSlot(1392206);
        uint256 originalWord0 = uint256(vm.load(EXCHANGE, originalSlot));
        uint256 originalWord1 = uint256(vm.load(EXCHANGE, bytes32(uint256(originalSlot) + 1)));
        require(originalWord0 != 0 && (originalWord1 & (uint256(1) << 240)) != 0,
                "active historical position template");
        uint256 margin = uint128(originalWord1);
        uint256[] memory ids = new uint256[](4);
        for (uint256 i; i < 4; ++i) {{
            ids[i] = i + 1;
            bytes32 slot = positionSlot(ids[i]);
            vm.store(EXCHANGE, slot, bytes32((originalWord0 & ~uint256(type(uint160).max)) | uint160(USER)));
            vm.store(EXCHANGE, bytes32(uint256(slot) + 1), bytes32(originalWord1));
        }}
        bytes32 totalsSlot = bytes32(uint256(22));
        uint256 oldTotals = uint256(vm.load(EXCHANGE, totalsSlot));
        uint256 oldLocked = oldTotals >> 128;
        require(oldLocked + 4 * margin < 2**128, "locked margin range");
        vm.store(EXCHANGE, totalsSlot, bytes32(((oldLocked + 4 * margin) << 128) | uint128(oldTotals)));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xb0b, digest);
        require(ecrecover(digest, v, r, sigS) == sessionKey, "session signer");
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok, bytes memory result) = EXCHANGE.call(abi.encodeWithSelector(
            bytes4(0x2792e706), USER, ids, NONCE, deadline, v, r, sigS));
        if (!ok) revert WrongResult(ok, result);
        for (uint256 i; i < 4; ++i) {{
            bytes32 slot = positionSlot(ids[i]);
            require((uint256(vm.load(EXCHANGE, bytes32(uint256(slot) + 1))) & (uint256(1) << 240)) == 0,
                    "active position cleared");
        }}
        require(uint256(vm.load(EXCHANGE, totalsSlot)) >> 128 == oldLocked,
                "four margins released");
        bytes32 nonceOuter = keccak256(abi.encode(USER, uint256(6)));
        bytes32 nonceBitSlot = keccak256(abi.encode(uint256(0), nonceOuter));
        require(uint256(vm.load(SESSION, nonceBitSlot)) == uint256(1) << NONCE,
                "nonce bit persisted");
        require(uint256(vm.load(SESSION, keccak256(abi.encode(USER, uint256(5))))) == NONCE + 1,
                "nonce counter persisted");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        uint256 closedEvents;
        for (uint256 i; i < logs.length; ++i)
            if (logs[i].emitter == EXCHANGE && logs[i].topics.length > 0 &&
                logs[i].topics[0] == 0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf)
                ++closedEvents;
        require(closedEvents == 4, "four close events");
    }}
}}
'''
    assert source.endswith('}\n')
    mixed_source = MIXED_CASE.read_text()
    replacements, template_sources = market1_sources(manifest)
    for marker, value in replacements.items():
        assert mixed_source.count(marker) == 1, marker
        mixed_source = mixed_source.replace(marker, value)
    assert "__MARKET1_" not in mixed_source and "__POSITION_" not in mixed_source
    source = source[:-2] + mixed_source + '\n}\n'
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-historical-close-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "HistoricalCloseReplay.t.sol").write_text(source)
        for label, code in code_files.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vvvv"],
                             check=False, capture_output=True, text=True, timeout=90)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != {"testHistoricalMixedSignedCloses", "testFourConstructedActivePositionsClose", "testFourMixedPnlActivePositionsClose", "testFourMixedPnlLossFirstClose", "testFourCrossMarketZeroFirstClose", "testFourCrossMarketOneFirstClose"}:
        raise RuntimeError("historical close replay failed: " + output[-9000:])
    cross_market_calls = cross_market_math_trace(output)
    forge_version = subprocess.run(["forge", "--version"], check=True,
                                   capture_output=True, text=True).stdout.splitlines()[0]
    solc_version_output = subprocess.run(["solc", "--version"], check=True,
                                         capture_output=True, text=True).stdout
    solc_version = re.search(r"Version: (\S+)", solc_version_output).group(1)
    ledger = {
        "transaction": TX,
        "block": probes["target_block"],
        "block_hash": probes["target_hash"],
        "prestate_sha256": hashlib.sha256(PRESTATE.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "mixed_test_sha256": hashlib.sha256(MIXED_CASE.read_bytes()).hexdigest(),
        "cross_market_source_sha256": hashlib.sha256(mixed_source.encode()).hexdigest(),
        "runtime_sha256": {address: hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
                           for address, code in account_code.items()},
        "mocked_precompile_outputs": precompile_outputs,
        "inner_call_selectors": [item["input"][:10] for item in inner],
        "receipt_logs_matched": len(expected_logs),
        "post_storage_words_matched": len(post_lines),
        "forge_result": "6 passed, 0 failed",
        "local_trace_capture": {"command": "forge test -vvvv",
                                "forge_version": forge_version, "solc_version": solc_version},
        "constructed_four_active_close": {
            "position_count": 4,
            "position_template": 1392206,
            "same_market_and_margin": True,
            "all_active_flags_cleared": True,
            "all_four_margins_released": True,
            "nonce_bit_and_counter_persisted": True,
            "four_position_closed_events": True,
        },
        "constructed_four_mixed_pnl_close": {
            "position_count": 4,
            "gain_template": 1392206,
            "loss_template": 1392921,
            "same_market": True,
            "orders_tested": ["gain_loss_gain_loss", "loss_gain_loss_gain"],
            "two_positive_and_two_negative_pnl": True,
            "balance_margin_fee_and_nonce_equations_match": True,
        },
        "constructed_four_cross_market_close": {
            "position_count": 4,
            "market_ids": [0, 1],
            "orders_tested": ["market0_gain_market1_loss_market0_loss_market1_gain",
                              "market1_loss_market0_gain_market1_gain_market0_loss"],
            "market1_template_sources": template_sources,
            "market1_config_source": str(MARKET1_GETTERS.relative_to(ROOT)),
            "market1_config_sha256": hashlib.sha256(MARKET1_GETTERS.read_bytes()).hexdigest(),
            "market1_fields_source": str(MARKET1_FIELDS.relative_to(ROOT)),
            "market1_fields_sha256": hashlib.sha256(MARKET1_FIELDS.read_bytes()).hexdigest(),
            "mocked_bbo": {"0": [808450, 808460], "1": [234895, 234905]},
            "event_raw_pnl_formula_matches": True,
            "balance_margin_fee_and_nonce_equations_match": True,
            "library_math_and_settlement_vectors": cross_market_calls,
        },
        "limitations": ["HyperCore precompiles replayed with their observed responses",
                        "Archive prestate records transaction reads, not every historical storage slot",
                        "Cross-market positions and market-1 configuration come from later captured blocks and form a synthetic state",
                        "Cross-market BBO responses are controlled; library math models match these eight constructed calls but not all future states or branches"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(ledger, indent=2) + "\n")
    print(f"historical mixed close: {len(passed)} passes, {len(expected_logs)} logs, {len(post_lines)} storage words")


if __name__ == "__main__":
    main()
