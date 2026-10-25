#!/usr/bin/env python3
"""Exercise Exchange pause controls through exact pinned proxy and implementation runtimes."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "exchange_pause_local" / "replay.json"
BEHAVIOR_OUT = ATLAS / "exchange_pause_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
GUARDIAN = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
GUARDIAN_TX = "0x24b978eacabde6c6b459011ce8c78b25bf97a74a41d51a486324492fdba48c21"
OLD_OWNER = "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
SIGNATURES = {"0x8da5cb5b": "owner()", "0x24a3d622": "pauseGuardian()",
              "0x48bde20c": "setPauseGuardian(address)", "0x53e23e2e": "tradingPaused()",
              "0xae69b95b": "setTradingPaused(bool)", "0x2d2451d1": "pauseMarket(uint32)"}
TEST_NAMES = ["testPinnedGetters", "testOwnerPauseAndResume", "testGuardianPause",
              "testGuardianResume", "testOutsiderPause", "testInvalidBoolEncoding",
              "testMarketPauseOwner", "testMarketPauseGuardian", "testMarketPauseOutsider",
              "testMarketPauseInvalidId", "testMarketPauseRepeat",
              "testOwnerUpdatesGuardian", "testOutsiderCannotChangeGuardian"]
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
contract MockOracle {
    function getBBO(uint32 asset) external pure returns (uint64 bid, uint64 ask) {
        require(asset == 0, "wrong oracle asset");
        return (1_000_000_000, 1_100_000_000);
    }
}
contract ExchangePauseTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant GUARDIAN = address(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 constant PAUSE_SLOT = bytes32(uint256(29));
    bytes32 constant INSTRUMENT_SLOT0 = 0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6df;
    bytes32 constant INSTRUMENT_SLOT1 = bytes32(uint256(INSTRUMENT_SLOT0) + 1);
    bytes32 constant INSTRUMENT_SLOT2 = bytes32(uint256(INSTRUMENT_SLOT0) + 2);
    bytes32 constant MARKET_PAUSE_SLOT = keccak256(abi.encode(uint256(0), uint256(35)));
    function setUp() public {
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(PROXY, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        vm.store(PROXY, bytes32(uint256(1)), bytes32(uint256(uint160(GUARDIAN))));
        vm.store(PROXY, PAUSE_SLOT, bytes32(uint256(uint160(SESSION)) << 8));
    }
    function callAs(address caller, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return PROXY.call(data);
    }
    function paused() internal view returns (bool) {
        (bool ok, bytes memory out) = PROXY.staticcall(abi.encodeWithSelector(bytes4(0x53e23e2e)));
        require(ok && out.length == 32, "pause getter failed");
        return abi.decode(out, (bool));
    }
    function checkPauseLog(Vm.Log[] memory logs, bool expected) internal pure {
        require(logs.length == 1 && logs[0].emitter == PROXY, "pause log count");
        require(logs[0].topics.length == 1 && logs[0].topics[0] == keccak256("TradingPausedUpdated(bool)"), "pause topic");
        require(keccak256(logs[0].data) == keccak256(abi.encode(expected)), "pause payload");
    }
    function setUpMarket() internal {
        MockOracle oracle = new MockOracle();
        vm.store(PROXY, bytes32(uint256(2)), bytes32(uint256(uint160(address(oracle)))));
        vm.store(PROXY, bytes32(uint256(8)), bytes32(uint256(2)));
        vm.store(PROXY, INSTRUMENT_SLOT0, 0x000003e8000000000000002c28d1751327a700000000032d26d12e980b600000);
        vm.store(PROXY, INSTRUMENT_SLOT1, 0x00016345785d8a00000001b0f51147891600000000084595161401484a000000);
        vm.store(PROXY, INSTRUMENT_SLOT2, 0x00000000000000000000000000000000000000000000152d02c7e14af6800000);
    }
    function testMarketPauseOwner() public {
        setUpMarket();
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)));
        require(ok, "owner market pause");
        uint256 expectedWord = 1 | (uint256(1_000_000_000) << 8) | (uint256(1_100_000_000) << 72) | (uint256(block.timestamp) << 136);
        require(vm.load(PROXY, MARKET_PAUSE_SLOT) == bytes32(expectedWord), "market pause packed word");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY, "market event count");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == 0x25e933a27e6487478d7617f2f4ef2f5c77355faf6cad2e6fd7c4b8d029930d9f, "market event topic");
        require(logs[0].topics[1] == bytes32(0) && logs[0].data.length == 96, "market event shape");
        (uint256 bid, uint256 ask, uint256 timestamp) = abi.decode(logs[0].data, (uint256, uint256, uint256));
        require(bid == 1_000_000_000 && ask == 1_100_000_000 && timestamp == block.timestamp, "market event data");
    }
    function testMarketPauseGuardian() public {
        setUpMarket();
        (bool ok,) = callAs(GUARDIAN, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)));
        require(ok, "guardian market pause");
        require(uint256(vm.load(PROXY, MARKET_PAUSE_SLOT)) & 0xff == 1, "guardian market flag");
    }
    function testMarketPauseOutsider() public {
        setUpMarket();
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x49199fb6), "outsider market error");
    }
    function testMarketPauseRepeat() public {
        setUpMarket();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)));
        require(ok, "first market pause");
        (bool secondOk, bytes memory out) = callAs(GUARDIAN, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)));
        require(!secondOk && out.length == 4 && bytes4(out) == bytes4(0x0d240815), "repeat market error");
    }
    function testMarketPauseInvalidId() public {
        setUpMarket();
        (bool ok, bytes memory out) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(2)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x67207a88), "invalid market error");
    }
    function testOwnerUpdatesGuardian() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0x48bde20c), address(0x1234)));
        require(ok && vm.load(PROXY, bytes32(uint256(1))) == bytes32(uint256(uint160(address(0x1234)))), "guardian slot");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == PROXY && logs[0].topics.length == 2, "guardian event count");
        require(logs[0].topics[0] == keccak256("PauseGuardianUpdated(address)"), "guardian event topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(address(0x1234)))) && logs[0].data.length == 0, "guardian event data");
        (ok,) = callAs(GUARDIAN, abi.encodeWithSelector(bytes4(0xae69b95b), true));
        require(!ok, "old guardian still authorized");
        (ok,) = callAs(address(0x1234), abi.encodeWithSelector(bytes4(0xae69b95b), true));
        require(ok && paused(), "new guardian cannot pause");
    }
    function testOutsiderCannotChangeGuardian() public {
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0x48bde20c), address(0x1234)));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x30cd7471), "guardian setter outsider error");
        require(vm.load(PROXY, bytes32(uint256(1))) == bytes32(uint256(uint160(GUARDIAN))), "outsider changed guardian");
    }
    function testPinnedGetters() public view {
        (bool ok, bytes memory out) = PROXY.staticcall(abi.encodeWithSelector(bytes4(0x8da5cb5b)));
        require(ok && abi.decode(out, (address)) == OWNER, "owner getter");
        (ok, out) = PROXY.staticcall(abi.encodeWithSelector(bytes4(0x24a3d622)));
        require(ok && abi.decode(out, (address)) == GUARDIAN, "guardian getter");
        require(!paused(), "paused at pin");
    }
    function testOwnerPauseAndResume() public {
        vm.recordLogs();
        (bool ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0xae69b95b), true));
        require(ok && paused(), "owner pause");
        require(vm.load(PROXY, PAUSE_SLOT) == bytes32((uint256(uint160(SESSION)) << 8) | 1), "pause slot");
        checkPauseLog(vm.getRecordedLogs(), true);
        vm.recordLogs();
        (ok,) = callAs(OWNER, abi.encodeWithSelector(bytes4(0xae69b95b), false));
        require(ok && !paused(), "owner resume");
        require(vm.load(PROXY, PAUSE_SLOT) == bytes32(uint256(uint160(SESSION)) << 8), "resume slot");
        checkPauseLog(vm.getRecordedLogs(), false);
    }
    function testGuardianPause() public {
        vm.recordLogs();
        (bool ok,) = callAs(GUARDIAN, abi.encodeWithSelector(bytes4(0xae69b95b), true));
        require(ok && paused(), "guardian pause");
        checkPauseLog(vm.getRecordedLogs(), true);
    }
    function testGuardianResume() public {
        vm.store(PROXY, PAUSE_SLOT, bytes32((uint256(uint160(SESSION)) << 8) | 1));
        (bool ok, bytes memory out) = callAs(GUARDIAN, abi.encodeWithSelector(bytes4(0xae69b95b), false));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x49199fb6), "guardian resume error");
        require(paused(), "guardian resumed");
    }
    function testOutsiderPause() public {
        (bool ok, bytes memory out) = callAs(address(0xbeef), abi.encodeWithSelector(bytes4(0xae69b95b), true));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0x49199fb6), "outsider error");
        require(!paused(), "outsider paused");
    }
    function testInvalidBoolEncoding() public {
        (bool ok,) = callAs(OWNER, abi.encodePacked(bytes4(0xae69b95b), bytes32(uint256(2))));
        require(!ok && !paused(), "invalid bool accepted");
    }
}
'''


def cast(*args):
    return subprocess.run(["cast", *args], check=True, capture_output=True, text=True).stdout.strip()


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    for selector, signature in SIGNATURES.items():
        assert cast("sig", signature) == selector
        assert selector in {f["selector"] for f in catalog[IMPLEMENTATION]["functions"]}
    assert cast("sig", "NotOwner()") == "0x30cd7471"
    assert cast("sig", "InvalidInstrumentId()") == "0x67207a88"
    guardian_topic = cast("keccak", "PauseGuardianUpdated(address)")
    assert guardian_topic == "0x6b3ffd50ed0810416007b5dbbae587b9d8801c50bf8065cda8eb82011bed314e"
    historic_folder = ROOT / "artifacts" / "historical"
    guardian_call = json.loads((historic_folder / f"{GUARDIAN_TX}.calls.json").read_text())
    guardian_receipt = json.loads((historic_folder / f"{GUARDIAN_TX}.receipt.json").read_text())
    guardian_diff = json.loads((historic_folder / f"{GUARDIAN_TX}.state_diff.json").read_text())
    assert guardian_call["from"].lower() == OLD_OWNER and guardian_call["to"].lower() == PROXY
    assert guardian_call["input"][:10] == "0x48bde20c" and guardian_call["input"][-40:].lower() == GUARDIAN[2:]
    assert guardian_receipt["status"] == "0x1" and len(guardian_receipt["logs"]) == 1
    assert guardian_receipt["logs"][0]["topics"] == [guardian_topic, "0x" + GUARDIAN[2:].rjust(64, "0")]
    assert guardian_receipt["logs"][0]["data"] == "0x"
    slot1 = "0x" + (1).to_bytes(32, "big").hex()
    assert guardian_diff["pre"][PROXY]["storage"][slot1][-40:].lower() == OLD_OWNER[2:]
    assert guardian_diff["post"][PROXY]["storage"][slot1][-40:].lower() == GUARDIAN[2:]
    topic = cast("keccak", "TradingPausedUpdated(bool)")
    assert topic == "0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e"
    fixture = json.loads((ATLAS / "exchange_interface_evidence.json").read_text())
    assert any(e["signature"] == "TradingPausedUpdated(bool)" and e["topic0"] == topic for e in fixture["events"])
    views = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]["views"]
    assert {v["selector"]: v["return_prefix"] for v in views if v["selector"] in SIGNATURES} == {
        "0x8da5cb5b": "0x" + OWNER[2:].rjust(64, "0"),
        "0x24a3d622": "0x" + GUARDIAN[2:].rjust(64, "0"),
        "0x53e23e2e": "0x" + "0" * 64,
    }
    prestate = json.loads((ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json").read_text())
    archived_slot29 = prestate[PROXY]["storage"]["0x" + (29).to_bytes(32, "big").hex()]
    assert archived_slot29 == "0x" + ((int(SESSION, 16) << 8)).to_bytes(32, "big").hex()
    instrument_artifact = json.loads((ROOT / "artifacts" / "exchange_instrument_admin" / "pinned_probes.json").read_text())
    instrument0 = next(row for row in instrument_artifact["instruments"] if row["id"] == 0)
    assert instrument0["slots"][0] == "0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6df"
    assert instrument0["words"][0] == "0x000003e8000000000000002c28d1751327a700000000032d26d12e980b600000"
    assert instrument0["words"][1] == "0x00016345785d8a00000001b0f51147891600000000084595161401484a000000"
    assert instrument0["words"][2] == "0x00000000000000000000000000000000000000000000152d02c7e14af6800000"
    raw = {}
    for name, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        raw[name] = code
    assert catalog[IMPLEMENTATION]["sha256"] == manifest["contracts"][IMPLEMENTATION]["sha256"]
    solc = shutil.which("solc")
    assert solc, "local solc is required"
    with tempfile.TemporaryDirectory(prefix="papertrade-exchange-pause-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(solc) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "ExchangePause.t.sol").write_text(TEST_SOURCE)
        for name, code in raw.items():
            (project / "runtime" / f"{name}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    if run.returncode or set(passed) != set(TEST_NAMES):
        raise RuntimeError("Exchange pause replay failed: " + output[-3600:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "runtime_hashes": {name: manifest["contracts"][address]["sha256"] for name, address in (("Proxy", PROXY), ("Implementation", IMPLEMENTATION))},
        "test_names": sorted(passed), "forge_result": "13 passed, 0 failed",
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "archived_slot29": archived_slot29,
        "historical_guardian_transaction": GUARDIAN_TX,
        "mock_oracle_getBBO_asset": 0,
        "mock_oracle_bid_ask": [1_000_000_000, 1_100_000_000],
        "method": "port-free Forge tests with exact pinned proxy and implementation bytecode, pinned getter values, and archived packed pause slot",
        "limits": ["No historical setTradingPaused or pauseMarket call is in the saved transaction sample.",
                   "Market-pause success used a mock Oracle; effects on subsequent trading were not tested."],
    }, indent=2) + "\n")
    BEHAVIOR_OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
        "runtime_sha256": manifest["contracts"][IMPLEMENTATION]["sha256"],
        "selector_reconstructions": SIGNATURES,
        "owner_at_pin": OWNER, "pause_guardian_at_pin": GUARDIAN,
        "pause_storage_slot": 29, "pause_storage_field": "low byte; upper bytes preserve SessionKeyManager address shifted by 8",
        "market_pause_mapping_base_slot": 35,
        "market_pause_oracle_asset": 0,
        "market_pause_mock_bid_ask": [1_000_000_000, 1_100_000_000],
        "market_pause_event_payload": "indexed uint32 market ID; unindexed bid uint64, ask uint64, timestamp uint64 by tested values and bytecode widths",
        "market_pause_storage_layout": "mapping(uint32 => packed word) at base slot 35: flag bits 0..7, bid bits 8..71, ask bits 72..135, timestamp bits 136..199",
        "historical_guardian_transaction": GUARDIAN_TX,
        "event_catalog": [
            {"topic0": guardian_topic, "reconstructed_signature": "PauseGuardianUpdated(address)",
             "status": "observed_historical_topic", "historical_tx": GUARDIAN_TX},
            {"topic0": topic, "reconstructed_signature": "TradingPausedUpdated(bool)",
             "status": "simulated_log_only", "probe_paths": ["testOwnerPauseAndResume", "testGuardianPause"]},
            {"topic0": "0x25e933a27e6487478d7617f2f4ef2f5c77355faf6cad2e6fd7c4b8d029930d9f",
             "reconstructed_signature": "", "status": "simulated_log_only", "probe_paths": ["testMarketPauseOwner"]}],
        "simulated_error_catalog": [
            {"selector": "0x30cd7471", "reconstructed_signature": "NotOwner()", "probe_paths": ["testOutsiderCannotChangeGuardian"]},
            {"selector": "0x49199fb6", "probe_paths": ["testGuardianResume", "testOutsiderPause", "testMarketPauseOutsider"]},
            {"selector": "0x67207a88", "reconstructed_signature": "InvalidInstrumentId()", "probe_paths": ["testMarketPauseInvalidId"]},
            {"selector": "0x0d240815", "probe_paths": ["testMarketPauseRepeat"]}],
        "local_replay_evidence": "../../artifacts/exchange_pause_local/replay.json",
        "limits": ["Exact source names of custom errors 0x49199fb6 and 0x0d240815 and market-pause event 0x25e933a2 remain unknown.",
                   "Market pause success used a local mock Oracle, not pinned HyperCore price data.",
                   "No historical call to setTradingPaused or pauseMarket is in the saved sample.",
                   "Source identifiers are hash and behavior reconstructions, not verified Solidity source."],
    }, indent=2) + "\n")
    print("verified thirteen Exchange pause local tests and historical guardian update")


if __name__ == "__main__":
    main()
