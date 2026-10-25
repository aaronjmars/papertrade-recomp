"""Compare the second older Exchange's original and pinned retry runtimes."""

import gzip
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_exchange_variant_replay.json"
ORIGINAL = "0x6f0e9deab8a4f21344e4c10a35db5027b02a67fa"
REPLACEMENT = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
TEST_NAMES = {
    "testOriginalSpotRetry", "testReplacementSpotRetry",
    "testOriginalMixedRetry", "testReplacementMixedRetry",
    "testOriginalPerpRetry", "testReplacementPerpRetry",
    "testOriginalPartialFinalization", "testReplacementPartialFinalization",
    "testOriginalLegacyBelowMinimum", "testReplacementLegacyBelowMinimum",
    "testOriginalFirstSpotAtMinimum", "testReplacementFirstSpotAtMinimum",
    "testReplacementFirstSpotBelowMinimum", "testReplacementFirstPerpAtMinimum",
}

TEST_SOURCE = '''pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function roll(uint256) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract MockProxy {
    uint64 public spot;
    uint64 public perp;
    uint256 public calls;
    function sweepAllToExchange(uint64 token, uint64 spot_, uint64 perp_) external {
        require(token == 0, "token");
        spot = spot_;
        perp = perp_;
        calls++;
    }
}
contract OlderExchangeVariantTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(0xfeed);
    address constant USER = address(0xaaa);
    address constant FACTORY = address(0xccc);
    bytes32 constant CLEARED = 0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e;
    bytes32 constant REQUESTED = 0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025;
    struct Result { bool ok; bytes output; uint256 pending; uint256 last; uint64 sentSpot; uint64 sentPerp; uint256 calls; Vm.Log[] logs; }

    function run(string memory file, uint64 storedSpot, uint64 storedPerp, uint64 currentSpot, uint64 currentPerp)
        internal returns (Result memory result)
    {
        MockProxy proxy = new MockProxy();
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile(file)));
        vm.roll(100);
        vm.store(EXCHANGE, bytes32(0), bytes32(uint256(1)));
        vm.store(EXCHANGE, bytes32(uint256(30)), bytes32(uint256(uint160(FACTORY))));
        bytes32 pendingSlot = keccak256(abi.encode(USER, uint256(33)));
        bytes32 lastSlot = keccak256(abi.encode(address(proxy), uint256(32)));
        vm.store(EXCHANGE, pendingSlot, bytes32(uint256(storedSpot) | (uint256(storedPerp) << 64) | (uint256(99) << 128)));
        vm.mockCall(FACTORY, abi.encodeWithSelector(bytes4(0xc1a9a508), USER), abi.encode(address(proxy)));
        vm.mockCall(address(0x801), bytes(""), abi.encode(uint256(currentSpot), uint256(0), uint256(0)));
        vm.mockCall(address(0x803), bytes(""), abi.encode(uint256(currentPerp)));
        vm.recordLogs();
        (result.ok, result.output) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        result.logs = vm.getRecordedLogs();
        result.pending = uint256(vm.load(EXCHANGE, pendingSlot));
        result.last = uint256(vm.load(EXCHANGE, lastSlot));
        result.sentSpot = proxy.spot();
        result.sentPerp = proxy.perp();
        result.calls = proxy.calls();
    }

    function request(bool replacement, uint64 currentSpot, uint64 currentPerp, bool shouldSucceed) internal {
        MockProxy proxy = new MockProxy();
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile(replacement ? "runtime/Replacement.hex" : "runtime/Original.hex")));
        vm.roll(100);
        vm.store(EXCHANGE, bytes32(0), bytes32(uint256(1)));
        vm.store(EXCHANGE, bytes32(uint256(30)), bytes32(uint256(uint160(FACTORY))));
        bytes32 pendingSlot = keccak256(abi.encode(USER, uint256(33)));
        bytes32 lastSlot = keccak256(abi.encode(address(proxy), uint256(32)));
        vm.mockCall(FACTORY, abi.encodeWithSelector(bytes4(0xc1a9a508), USER), abi.encode(address(proxy)));
        vm.mockCall(address(0x801), bytes(""), abi.encode(uint256(currentSpot), uint256(0), uint256(0)));
        vm.mockCall(address(0x803), bytes(""), abi.encode(uint256(currentPerp)));
        vm.recordLogs();
        (bool ok, bytes memory output) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x01681a62), USER));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        if (shouldSucceed) {
            require(ok && output.length == 0, "first request reverted");
            require(uint256(vm.load(EXCHANGE, pendingSlot)) ==
                (uint256(currentSpot) | (uint256(currentPerp) << 64) | (uint256(100) << 128)), "first pending");
            require(uint256(vm.load(EXCHANGE, lastSlot)) == 100, "first last block");
            require(proxy.calls() == 1 && proxy.spot() == currentSpot && proxy.perp() == currentPerp,
                "first proxy amount");
            require(logs.length == 1 && logs[0].topics[0] == REQUESTED, "first request log");
            (uint64 loggedSpot, uint64 loggedPerp, uint32 blockNumber) =
                abi.decode(logs[0].data, (uint64,uint64,uint32));
            require(loggedSpot == currentSpot && loggedPerp == currentPerp && blockNumber == 100,
                "first request data");
        } else {
            require(!ok && bytes4(output) == bytes4(0x329c2b0f), "first minimum error");
            require(uint256(vm.load(EXCHANGE, pendingSlot)) == 0, "first pending write");
            require(uint256(vm.load(EXCHANGE, lastSlot)) == 0 && proxy.calls() == 0,
                "first side effect");
            require(logs.length == 0, "first failed log");
        }
    }
    function testOriginalFirstSpotAtMinimum() public { request(false, 1_000_000_000, 0, true); }
    function testReplacementFirstSpotAtMinimum() public { request(true, 1_000_000_000, 0, true); }
    function testReplacementFirstSpotBelowMinimum() public { request(true, 999_999_999, 0, false); }
    function testReplacementFirstPerpAtMinimum() public { request(true, 0, 10_000_000, true); }

    function retry(bool replacement, uint64 storedSpot, uint64 storedPerp, uint64 expectedSpot, uint64 expectedPerp)
        internal
    {
        Result memory r = run(replacement ? "runtime/Replacement.hex" : "runtime/Original.hex",
            storedSpot, storedPerp, storedSpot, storedPerp);
        require(r.ok && r.output.length == 0, "retry reverted");
        require(r.pending == (uint256(expectedSpot) | (uint256(expectedPerp) << 64) | (uint256(100) << 128)), "pending amount");
        require(r.last == 100, "last sweep block");
        require(r.calls == 1 && r.sentSpot == expectedSpot && r.sentPerp == expectedPerp, "proxy call");
        require(r.logs.length == 2 && r.logs[0].topics[0] == CLEARED && r.logs[1].topics[0] == REQUESTED, "events");
        require(r.logs[1].topics[1] == bytes32(uint256(uint160(USER))), "request user");
        (uint64 loggedSpot, uint64 loggedPerp, uint32 blockNumber) = abi.decode(r.logs[1].data, (uint64,uint64,uint32));
        require(loggedSpot == expectedSpot && loggedPerp == expectedPerp && blockNumber == 100, "event amount");
    }

    function testOriginalSpotRetry() public { retry(false, 10_000_000_000, 0, 10_000_000_000, 0); }
    function testReplacementSpotRetry() public { retry(true, 10_000_000_000, 0, 9_900_000_000, 0); }
    function testOriginalMixedRetry() public { retry(false, 1_000_000_000, 90_000_000, 1_000_000_000, 90_000_000); }
    function testReplacementMixedRetry() public { retry(true, 1_000_000_000, 90_000_000, 900_000_000, 90_000_000); }
    function testOriginalPerpRetry() public { retry(false, 0, 100_000_000, 0, 100_000_000); }
    function testReplacementPerpRetry() public { retry(true, 0, 100_000_000, 0, 100_000_000); }

    function checkPartial(bool replacement) internal {
        Result memory r = run(replacement ? "runtime/Replacement.hex" : "runtime/Original.hex",
            10_000_000_000, 0, 1_000_000_000, 0);
        require(r.ok && r.pending == 0 && r.last == 0 && r.calls == 0, "partial finalization");
        require(r.logs.length == 1 && r.logs[0].topics[0] != CLEARED, "partial event");
    }
    function testOriginalPartialFinalization() public { checkPartial(false); }
    function testReplacementPartialFinalization() public { checkPartial(true); }

    function legacy(bool replacement) internal {
        Result memory r = run(replacement ? "runtime/Replacement.hex" : "runtime/Original.hex",
            100_000_000, 0, 100_000_000, 0);
        if (replacement) {
            require(r.ok && r.pending == 0 && r.last == 0 && r.calls == 0, "legacy clear");
            require(r.logs.length == 1 && r.logs[0].topics[0] == CLEARED, "legacy clear event");
        } else {
            require(!r.ok && bytes4(r.output) == bytes4(0x329c2b0f), "legacy error");
            require(r.pending == 100_000_000 | (uint256(99) << 128), "legacy pending changed");
            require(r.last == 0 && r.calls == 0, "legacy side effect");
        }
    }
    function testOriginalLegacyBelowMinimum() public { legacy(false); }
    function testReplacementLegacyBelowMinimum() public { legacy(true); }
}
'''


def inputs():
    scope = json.loads(gzip.decompress(SCOPE.read_bytes()))
    assert scope["pin"] == 48_902_346
    rows = {row["address"]: row for row in scope["rows"]}
    assert rows[ORIGINAL]["runtime"].startswith("0x")
    assert rows[REPLACEMENT]["runtime"].startswith("0x")
    return scope, rows


def static_checks(rows):
    original = bytes.fromhex(rows[ORIGINAL]["runtime"][2:])
    replacement = bytes.fromhex(rows[REPLACEMENT]["runtime"][2:])
    assert len(original) == 23_052 and len(replacement) == 23_529
    dispatcher = re.compile(b"\\x63(.{4})\\x14\\x61(.{2})\\x57", re.DOTALL)
    original_selectors = {match.group(1) for match in dispatcher.finditer(original[:4096])}
    replacement_selectors = {match.group(1) for match in dispatcher.finditer(replacement[:4096])}
    assert original_selectors == replacement_selectors and len(original_selectors) == 98
    assert bytes.fromhex("6d142da1") in original_selectors
    assert original[0x4A2B:0x4A2F] == bytes.fromhex("6147d256")
    assert replacement[0x4A56:0x4A5B] == bytes.fromhex("633b9aca00")
    assert replacement[0x4AD3:0x4AD8] == bytes.fromhex("6305f5e100")
    return {
        "original_sha256": hashlib.sha256(original).hexdigest(),
        "replacement_sha256": hashlib.sha256(replacement).hexdigest(),
        "original_bytes": len(original),
        "replacement_bytes": len(replacement),
        "shared_selector_count": len(original_selectors),
        "original_retry_tail_pc": "0x4a2b",
        "replacement_retry_tail_pc": "0x4a56",
        "replacement_reserve_raw_spot": 100_000_000,
    }


def run():
    scope, rows = inputs()
    checked = static_checks(rows)
    solc = shutil.which("solc")
    assert solc
    with tempfile.TemporaryDirectory(prefix="papertrade-older-variant-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "OlderExchangeVariant.t.sol").write_text(TEST_SOURCE)
        (project / "runtime" / "Original.hex").write_text(rows[ORIGINAL]["runtime"])
        (project / "runtime" / "Replacement.hex").write_text(rows[REPLACEMENT]["runtime"])
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True, text=True, check=False, timeout=60,
        )
    output = result.stdout + "\n" + result.stderr
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    if result.returncode or passed != TEST_NAMES:
        raise RuntimeError("older Exchange retry comparison failed: " + output[-5000:])
    payload = {
        "pin": scope["pin"], "block_hash": scope["block_hash"],
        "original": ORIGINAL, "replacement": REPLACEMENT,
        "static_checks": checked,
        "test_names": sorted(passed),
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "spot_raw_decimals": 8,
        "normal_spot_retry_raw": {"balance": 10_000_000_000, "original_send_and_pending": 10_000_000_000,
                                  "replacement_send_and_pending": 9_900_000_000},
        "first_request_raw": {"minimum_spot_equivalent": 1_000_000_000,
                              "original_spot_send_at_minimum": 1_000_000_000,
                              "replacement_spot_send_at_minimum": 1_000_000_000,
                              "replacement_perp_send_at_minimum": 10_000_000,
                              "replacement_below_minimum_error": "0x329c2b0f"},
        "mixed_retry_raw": {"spot": 1_000_000_000, "perp": 90_000_000,
                            "original_spot_send_and_pending": 1_000_000_000,
                            "replacement_spot_send_and_pending": 900_000_000,
                            "perp_send_and_pending": 90_000_000},
        "legacy_below_minimum": {"constructed_stored_and_current_spot": 100_000_000,
                                 "original_error": "0x329c2b0f", "replacement_clears": True},
        "limits": [
            "Tests use exact pinned implementation runtimes with constructed Exchange state, mocked HyperCore reads, factory lookup, and proxy call.",
            "The mock proxy records calldata but does not enqueue a CoreWriter action or establish Core settlement.",
            "The legacy below-minimum pending word is constructed; no such word was observed in the older users at the pin.",
            "The reserve is visible in the older replacement retry branch only; the exact Core transfer fee and adequacy of one USDC are unverified.",
            "First requests at the 10 USDC spot-equivalent minimum forward the full spot or perp amount to a mock proxy; no CoreWriter execution is tested.",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    return verify()


def verify():
    scope, rows = inputs()
    saved = json.loads(OUT.read_text())
    assert saved["pin"] == scope["pin"] and saved["block_hash"] == scope["block_hash"]
    assert saved["original"] == ORIGINAL and saved["replacement"] == REPLACEMENT
    assert saved["static_checks"] == static_checks(rows)
    assert set(saved["test_names"]) == TEST_NAMES
    assert saved["test_source_sha256"] == hashlib.sha256(TEST_SOURCE.encode()).hexdigest()
    assert saved["normal_spot_retry_raw"] == {
        "balance": 10_000_000_000, "original_send_and_pending": 10_000_000_000,
        "replacement_send_and_pending": 9_900_000_000,
    }
    assert saved["first_request_raw"] == {
        "minimum_spot_equivalent": 1_000_000_000,
        "original_spot_send_at_minimum": 1_000_000_000,
        "replacement_spot_send_at_minimum": 1_000_000_000,
        "replacement_perp_send_at_minimum": 10_000_000,
        "replacement_below_minimum_error": "0x329c2b0f",
    }
    assert saved["legacy_below_minimum"]["original_error"] == "0x329c2b0f"
    print(f"Older Exchange variant: {len(TEST_NAMES)} exact-runtime cases, 1 USDC retry reserve")
    return {"test_count": len(TEST_NAMES), "reserve_raw": saved["static_checks"]["replacement_reserve_raw_spot"]}


if __name__ == "__main__":
    run()
