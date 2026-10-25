"""Verify historical close math through the first older Exchange library."""

import collections
import gzip
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_exchange_library import pnl_model, settlement_model

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
LIBRARIES = ROOT / "artifacts" / "deployer_scope" / "older_linked_libraries.json.gz"
TRACES = ROOT / "artifacts" / "deployer_scope" / "older_exchange_library_close_traces.json.gz"
TXLIST = ROOT / "artifacts" / "deployer_scope" / "older_batch_recent_txlist.json.gz"
OUT = ATLAS / "older_exchange_library_behavior.json"
LOCAL = ROOT / "artifacts" / "deployer_scope" / "older_exchange_library_local.json"
OLD_LIBRARY = "0xac8ba1307815f74bd13d4d039c96f7b97e81aa49"
NEW_LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
OLD_IMPLEMENTATION = "0x557c853e100600e0ee91e0df88fcf4af0097ff89"
OLD_PROXY = "0x1b534e482b92bb6daff452cd12f2e35219e13493"
OLD_BATCH_PROXY = "0x4041882573028cb177847c46f82e242024ebde66"
MATH = "0x82296364"
SETTLEMENT = "0xaa31b143"
CLOSE = "0x2792e706"
POSITION_TOPIC = "0x330ea55ab7d6f2662fc122ba5ed0d3bc3bb56ef7e9387b5aa6a78411b363c013"
NONZERO_TOPIC = "0x64afd02d9793c990e8eae9bdefeff49b3ece7e7a2d2eebc011bf39b7eedf5255"
SUMMARY_TOPIC = "0x789bd128f86c2eacb5c1fe72f20634891e0ef8020959d2e52a258cf31d42c6b2"
SELECTOR_PATTERN = re.compile(b"\x63(.{4})\x14\x61(.{2})\x57", re.DOTALL)
TEST_NAMES = {
    "testPositive", "testNegative", "testFlat", "testZeroNet", "testOverLoss",
}
TEST_SOURCE = '''pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract DelegateHarness {
    address constant LIBRARY = address(uint160(uint256(0x00ac8ba1307815f74bd13d4d039c96f7b97e81aa49)));
    function exec(bytes memory data) external returns (bool, bytes memory) { return LIBRARY.delegatecall(data); }
}
contract OlderLibraryLocalTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant LIBRARY = address(uint160(uint256(0x00ac8ba1307815f74bd13d4d039c96f7b97e81aa49)));
    address constant USER = address(0x1234);
    bytes32 constant ENQUEUED = 0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7;
    DelegateHarness harness;
    function setUp() public {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        harness = new DelegateHarness();
        vm.store(address(harness), bytes32(uint256(17)), bytes32(uint256(1)));
    }
    function userSlot(uint256 base) internal pure returns (bytes32) { return keccak256(abi.encode(USER, base)); }
    function nodeSlot(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(15))); }
    function check(int256 pnl, uint256 expected) internal {
        vm.recordLogs();
        (bool ok, bytes memory out) = harness.exec(abi.encodeWithSelector(
            bytes4(0xacbc814f), uint256(15), USER, uint128(500), pnl));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(ok && out.length == 32 && abi.decode(out, (uint256)) == expected, "return amount");
        require(uint256(vm.load(address(harness), bytes32(uint256(17)))) == (expected > 0 ? 2 : 1), "next id");
        require(uint256(vm.load(address(harness), bytes32(uint256(16)))) == (expected > 0 ? 1 : 0), "global head");
        require(uint256(vm.load(address(harness), bytes32(uint256(18)))) == expected, "global total");
        require(uint256(vm.load(address(harness), userSlot(19))) == expected, "user total");
        require(uint256(vm.load(address(harness), userSlot(20))) == (expected > 0 ? 1 : 0), "user head");
        require(uint256(vm.load(address(harness), userSlot(21))) == (expected > 0 ? 1 : 0), "user tail");
        if (expected > 0) {
            require(uint256(vm.load(address(harness), nodeSlot(1))) == uint256(uint160(USER)), "node owner");
            require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(1)) + 1))) == expected, "node amount");
            require(logs.length == 1 && logs[0].emitter == address(harness), "log count");
            require(logs[0].topics.length == 3 && logs[0].topics[0] == ENQUEUED, "event topic");
            require(logs[0].topics[1] == bytes32(uint256(uint160(USER))) && logs[0].topics[2] == bytes32(uint256(1)), "indexed fields");
            require(abi.decode(logs[0].data, (uint256)) == expected, "event amount");
        } else {
            require(uint256(vm.load(address(harness), nodeSlot(1))) == 0, "zero node");
            require(logs.length == 0, "zero logs");
        }
    }
    function testPositive() public { check(100, 600); }
    function testNegative() public { check(-100, 400); }
    function testFlat() public { check(0, 500); }
    function testZeroNet() public { check(-500, 0); }
    function testOverLoss() public { check(-501, 0); }
}
'''


def read_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def children(frame):
    yield frame
    for child in frame.get("calls", []):
        yield from children(child)


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    raw = data[2:]
    return [int(raw[i:i + 64], 16) for i in range(0, len(raw), 64)]


def signed(value):
    return value if value < 2**255 else value - 2**256


def dispatchers():
    scope = read_gzip(SCOPE)
    libraries = read_gzip(LIBRARIES)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert scope["pin"] == libraries["pin"] == manifest["block"] == 48_902_346
    assert scope["block_hash"] == libraries["block_hash"] == manifest["block_hash"]
    old = bytes.fromhex(libraries["libraries"][OLD_LIBRARY][2:])
    new = bytes.fromhex((ATLAS / manifest["contracts"][NEW_LIBRARY]["runtime_file"]).read_text().strip()[2:])
    local = bytes.fromhex((ATLAS / "runtime" / (OLD_LIBRARY + ".hex")).read_text().strip()[2:])
    assert old == local and len(old) == 5_873 and len(new) == 5_790
    assert hashlib.sha256(old).hexdigest() == "86184c390d6f62a8bd0e97080a0959ba7a3860b1358635994f82f61e81ceac8c"
    assert hashlib.sha256(new).hexdigest() == manifest["contracts"][NEW_LIBRARY]["sha256"]
    old_selectors = {"0x" + match.group(1).hex() for match in SELECTOR_PATTERN.finditer(old[:1500])}
    new_selectors = {"0x" + match.group(1).hex() for match in SELECTOR_PATTERN.finditer(new[:1500])}
    assert len(old_selectors) == 11 and len(new_selectors) == 10
    assert old_selectors - new_selectors == {SETTLEMENT, "0xacbc814f"}
    assert new_selectors - old_selectors == {"0xef1a27a9"}
    first_impl = next(row for row in scope["rows"] if row["address"] == OLD_IMPLEMENTATION)
    first_proxy = next(row for row in scope["rows"] if row["address"] == OLD_PROXY)
    assert first_proxy["implementation_word"][-40:] == OLD_IMPLEMENTATION[2:]
    first_code = bytes.fromhex(first_impl["runtime"][2:])
    assert bytes.fromhex(OLD_LIBRARY[2:]) in first_code
    assert first_code.count(bytes.fromhex("63aa31b143")) == 1
    assert first_code.count(bytes.fromhex("63acbc814f")) == 1
    return {
        "older_library_sha256": hashlib.sha256(old).hexdigest(),
        "older_implementation_sha256": hashlib.sha256(first_code).hexdigest(),
        "older_only_selectors": sorted(old_selectors - new_selectors),
        "later_only_selectors": sorted(new_selectors - old_selectors),
        "shared_selectors": sorted(old_selectors & new_selectors),
        "older_implementation_unique_selector_push4_sites": {
            SETTLEMENT: hex(first_code.find(bytes.fromhex("63aa31b143"))),
            "0xacbc814f": hex(first_code.find(bytes.fromhex("63acbc814f"))),
        },
    }


def build():
    static = dispatchers()
    saved = read_gzip(TRACES)
    scope = read_gzip(SCOPE)
    txlist = read_gzip(TXLIST)
    assert saved["pin"] == txlist["endblock"] == 48_902_346
    assert saved["pin_hash"] == scope["block_hash"]
    assert txlist["source"] == "etherscan account txlist"
    assert txlist["chain_id"] == 999 and txlist["address"] == OLD_BATCH_PROXY
    assert txlist["sort"] == "desc" and txlist["page"] == 1 and txlist["offset"] == 100
    assert txlist["startblock"] == 42_134_995 and len(txlist["rows"]) == 100
    assert all(row["to"].lower() == OLD_BATCH_PROXY for row in txlist["rows"])
    assert [int(row["blockNumber"]) for row in txlist["rows"]] == sorted(
        (int(row["blockNumber"]) for row in txlist["rows"]), reverse=True
    )
    close_txs = [row for row in txlist["rows"] if CLOSE[2:] in row["input"].lower()]
    assert len(close_txs) == 20
    selection = [close_txs[index] for index in (0, 4, 8, 12, 16, 19)]
    assert set(saved["transactions"]) == {row["hash"] for row in selection}
    selected = {row["hash"]: row for row in selection}
    cases = []
    pnl_counts = collections.Counter()
    for tx, pair in sorted(saved["transactions"].items()):
        receipt, trace = pair["receipt"], pair["trace"]
        assert receipt["transactionHash"].lower() == tx
        assert int(receipt["blockNumber"], 16) <= saved["pin"]
        assert int(receipt["status"], 16) == 1
        assert trace["to"].lower() == OLD_BATCH_PROXY
        assert trace["input"].lower() == selected[tx]["input"].lower()
        close_frames = [frame for frame in children(trace) if frame.get("to", "").lower() == OLD_IMPLEMENTATION
                        and frame.get("input", "").startswith(CLOSE)]
        assert len(close_frames) == 1 and not close_frames[0].get("error")
        close_frame = close_frames[0]
        library_calls = [frame for frame in children(close_frame)
                         if frame.get("to", "").lower() == OLD_LIBRARY]
        assert len(library_calls) >= 2 and len(library_calls) % 2 == 0
        assert [frame["input"][:10] for frame in library_calls] == [MATH, SETTLEMENT] * (len(library_calls) // 2)
        receipt_topics = collections.Counter(log["topics"][0] for log in receipt["logs"])
        frame_topics = collections.Counter(log["topics"][0] for log in close_frame.get("logs", []))
        position_count = len(library_calls) // 2
        assert frame_topics[POSITION_TOPIC] == receipt_topics[POSITION_TOPIC] == position_count
        assert frame_topics[SUMMARY_TOPIC] == receipt_topics[SUMMARY_TOPIC] == 1
        records = []
        for index in range(position_count):
            math_call, settlement_call = library_calls[2 * index:2 * index + 2]
            assert not math_call.get("error") and not settlement_call.get("error")
            math_args = words("0x" + math_call["input"][10:])
            math_out = [signed(value) for value in words(math_call["output"])]
            settlement_args = words("0x" + settlement_call["input"][10:])
            settlement_args[3] = signed(settlement_args[3])
            settlement_out = words(settlement_call["output"])
            assert len(math_args) == 9 and len(math_out) == 2
            assert len(settlement_args) == 7 and len(settlement_out) == 6
            assert math_out == pnl_model(math_args)
            assert settlement_args[2] == math_args[2]
            assert settlement_args[3] == math_out[1]
            assert settlement_args[4:6] == [2 * 10**16] * 2
            assert settlement_args[6] > 0
            # The older seven-word function corresponds to the newer model's
            # zero-valued fifth word for these saved calls. This checks outputs,
            # not possible library storage writes or unsampled argument branches.
            assert settlement_out == settlement_model(settlement_args[:4] + [0] + settlement_args[4:])
            branch = "profit" if math_out[1] > 0 else "loss" if math_out[1] < 0 else "flat"
            pnl_counts[branch] += 1
            records.append({
                "index": index, "branch": branch,
                "math_args": [str(value) for value in math_args],
                "math_returns_signed": [str(value) for value in math_out],
                "settlement_args_signed_pnl": [str(value) for value in settlement_args],
                "settlement_returns": [str(value) for value in settlement_out],
            })
        assert frame_topics[NONZERO_TOPIC] == receipt_topics[NONZERO_TOPIC] == sum(
            row["branch"] != "flat" for row in records
        )
        cases.append({
            "tx": tx, "block": int(receipt["blockNumber"], 16),
            "receipt_log_count": len(receipt["logs"]),
            "older_exchange_close_logs": len(close_frame.get("logs", [])),
            "position_count": position_count,
            "library_call_selectors": [frame["input"][:10] for frame in library_calls],
            "positions": records,
        })
    assert sum(row["position_count"] for row in cases) == 24
    assert dict(pnl_counts) == {"loss": 6, "profit": 15, "flat": 3}
    return {
        "pin": saved["pin"], "pin_hash": saved["pin_hash"],
        "library": OLD_LIBRARY, "exchange_proxy": OLD_PROXY,
        "exchange_implementation": OLD_IMPLEMENTATION, "batch_proxy": OLD_BATCH_PROXY,
        "static": static, "transaction_count": len(cases), "position_count": 24,
        "pnl_branches": dict(sorted(pnl_counts.items())), "cases": cases,
        "decompiler": {
            "tool": "Heimdall 0.9.2", "source": "pinned runtime", "status": "untrusted hints",
            "older_library_yul": "decompiled/exchange_linked_library_old1_yul-decompiled.yul",
            "older_library_sol": "decompiled/exchange_linked_library_old1_sol-decompiled.sol",
            "older_exchange_yul": "decompiled/exchange_first_old_yul-decompiled.yul",
            "older_exchange_sol": "decompiled/exchange_first_old_sol-decompiled.sol",
        },
        "limits": [
            "Six selected older BatchExecutor transactions contain 24 successful first-suite signed closes; selection is not a full history.",
            "All saved old settlement calls use 2% positive and negative rate inputs and a nonzero seventh word.",
            "Matching six output words does not prove equivalent storage effects, event meanings, or unsampled branches.",
            "Older-only selector 0xacbc814f has no call in this saved close corpus; five constructed-state local cases cover its first-node branch only.",
            "The decompiler misses reachable older library calls in the Exchange implementation; raw traces and runtime bytes are authoritative.",
        ],
    }


def run_local():
    solc = shutil.which("solc")
    assert solc
    with tempfile.TemporaryDirectory(prefix="papertrade-older-library-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "OlderLibraryLocal.t.sol").write_text(TEST_SOURCE)
        (project / "runtime" / "Library.hex").write_text(
            (ATLAS / "runtime" / (OLD_LIBRARY + ".hex")).read_text()
        )
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True, text=True, check=False, timeout=60,
        )
    output = result.stdout + "\n" + result.stderr
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    if result.returncode or passed != TEST_NAMES:
        raise RuntimeError("older library local replay failed: " + output[-5000:])
    LOCAL.write_text(json.dumps({
        "pin": 48_902_346, "library": OLD_LIBRARY,
        "test_names": sorted(passed),
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "selector": "0xacbc814f", "margin": 500,
        "constructed_cases": [
            {"pnl": 100, "returned_and_queued": 600},
            {"pnl": -100, "returned_and_queued": 400},
            {"pnl": 0, "returned_and_queued": 500},
            {"pnl": -500, "returned_and_queued": 0},
            {"pnl": -501, "returned_and_queued": 0},
        ],
        "limits": "Exact library runtime with constructed queue storage and delegatecall harness; no historical invocation or Exchange wrapper path is proven.",
    }, indent=2) + "\n")


def verify():
    expected = build()
    assert json.loads(OUT.read_text()) == expected
    local = json.loads(LOCAL.read_text())
    assert local["pin"] == expected["pin"] and local["library"] == OLD_LIBRARY
    assert set(local["test_names"]) == TEST_NAMES
    assert local["test_source_sha256"] == hashlib.sha256(TEST_SOURCE.encode()).hexdigest()
    assert local["selector"] == "0xacbc814f" and local["margin"] == 500
    assert [row["returned_and_queued"] for row in local["constructed_cases"]] == [600, 400, 500, 0, 0]
    print("First older Exchange library: 6 signed closes, 24 math and settlement pairs, 5 local cases")
    return {"transaction_count": expected["transaction_count"], "position_count": expected["position_count"],
            "local_test_count": len(TEST_NAMES)}


if __name__ == "__main__":
    run_local()
    OUT.write_text(json.dumps(build(), indent=2) + "\n")
    verify()
