#!/usr/bin/env python3
"""Test the deployed older Exchange replacement against the two newest pending sweeps."""

import argparse
import gzip
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

import audit_stalled_sweeps as stalled

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
STALLED = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
OUT = ROOT / "artifacts" / "pt01_existing_replacement" / "replay.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
ORIGINAL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
REPLACEMENT = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
TEST_NAMES = {
    "testOriginalFirstFullSend",
    "testOriginalSecondFullSend",
    "testReplacementFirstReducedSend",
    "testReplacementSecondReducedSend",
    "testReplacementFirstDeliveredCredit",
    "testReplacementSecondDeliveredCredit",
    "testReplacementFirstNoFeeResidualCredit",
    "testReplacementSecondNoFeeResidualCredit",
}
TEST_SOURCE = """pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function roll(uint256) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function clearMockedCalls() external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract MockCoreWriter {
    bytes public lastAction;
    uint256 public calls;
    function sendRawAction(bytes calldata action) external {
        lastAction = action;
        calls++;
    }
}
contract Pt01ReplacementTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant ORIGINAL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant REPLACEMENT = address(uint160(uint256(0x0093a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant TIMELOCK = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant FACTORY = address(uint160(uint256(0x001629b7d46bef6e13ff754174fc9f32dea309b38f)));
    address constant CORE_WRITER = address(0x3333333333333333333333333333333333333333);
    address constant USER1 = address(uint160(uint256(0x0056cbe78a5cdfa10147927aec550aa7f2fb3d3d01)));
    address constant USER2 = address(uint160(uint256(0x009c8599c32224d7d9956a7def18f7314162f77baf)));
    address constant PROXY1 = address(uint160(uint256(0x001e8a704179cc6221592c362daa52a341ae20084d)));
    address constant PROXY2 = address(uint160(uint256(0x00f6b60cdf359af5538495831a9f2bbcada23e10e6)));
    bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    uint256 constant PIN = 48_902_346;
    uint64 constant SPOT1 = 5_005_091_600;
    uint64 constant SPOT2 = 1_210_000_000;
    uint256 constant LAST_BLOCK1 = 48_209_855;
    uint256 constant LAST_BLOCK2 = 48_091_494;

    function setUp() public {
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(ORIGINAL, vm.parseBytes(vm.readFile("runtime/Original.hex")));
        vm.etch(REPLACEMENT, vm.parseBytes(vm.readFile("runtime/Replacement.hex")));
        vm.etch(ADMIN, vm.parseBytes(vm.readFile("runtime/ProxyAdmin.hex")));
        vm.etch(PROXY1, vm.parseBytes(vm.readFile("runtime/UserProxy1.hex")));
        vm.etch(PROXY2, vm.parseBytes(vm.readFile("runtime/UserProxy2.hex")));
        MockCoreWriter writer = new MockCoreWriter();
        vm.etch(CORE_WRITER, address(writer).code);
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(ORIGINAL))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(EXCHANGE, bytes32(0), bytes32((uint256(uint160(TIMELOCK)) << 16) | 1));
        vm.store(EXCHANGE, bytes32(uint256(3)), bytes32(uint256(1e12)));
        vm.store(EXCHANGE, bytes32(uint256(5)), bytes32(uint256(1e10)));
        vm.store(EXCHANGE, bytes32(uint256(30)), bytes32(uint256(uint160(FACTORY))));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(uint256(100e18)));
        vm.store(EXCHANGE, bytes32(uint256(22)), bytes32((uint256(7) << 128) | uint256(100e18)));
        vm.store(EXCHANGE, keccak256(abi.encode(USER1, uint256(9))), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, keccak256(abi.encode(USER2, uint256(9))), bytes32(uint256(5e18)));
        vm.store(ADMIN, bytes32(0), bytes32(uint256(uint160(TIMELOCK))));
        vm.roll(PIN);
    }

    function check(bool replacement, bool first) internal {
        address user = first ? USER1 : USER2;
        address proxy = first ? PROXY1 : PROXY2;
        uint64 spot = first ? SPOT1 : SPOT2;
        uint256 lastBlock = first ? LAST_BLOCK1 : LAST_BLOCK2;
        bytes32 pendingSlot = keccak256(abi.encode(user, uint256(33)));
        bytes32 lastSlot = keccak256(abi.encode(proxy, uint256(32)));
        vm.store(EXCHANGE, pendingSlot, bytes32(uint256(spot) | (lastBlock << 128)));
        vm.store(EXCHANGE, lastSlot, bytes32(lastBlock));
        vm.mockCall(FACTORY, abi.encodeWithSelector(bytes4(0xc1a9a508), user), abi.encode(proxy));
        vm.mockCall(address(0x801), bytes(""), abi.encode(uint256(spot), uint256(0), uint256(0)));
        vm.mockCall(address(0x803), bytes(""), abi.encode(uint256(0)));
        if (replacement) {
            vm.prank(TIMELOCK);
            (bool upgraded,) = ADMIN.call(abi.encodeWithSignature("upgrade(address,address)", EXCHANGE, REPLACEMENT));
            require(upgraded, "admin upgrade");
            require(vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(REPLACEMENT))), "implementation slot");
        }
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSignature("finalizeSweep(address)", user));
        require(ok && out.length == 0, "finalize retry");
        uint64 expected = replacement ? spot - 100_000_000 : spot;
        require(uint256(vm.load(EXCHANGE, pendingSlot)) == uint256(expected) | (PIN << 128), "new pending amount");
        require(uint256(vm.load(EXCHANGE, lastSlot)) == PIN, "last sweep block");
        require(MockCoreWriter(CORE_WRITER).calls() == 1, "writer call count");
        bytes memory action = MockCoreWriter(CORE_WRITER).lastAction();
        require(action.length == 100 && bytes4(action) == bytes4(0x01000006), "action 6 header");
        bytes memory payload = new bytes(96);
        for (uint256 i; i < 96; i++) payload[i] = action[i + 4];
        (address destination, uint64 token, uint64 amount) = abi.decode(payload, (address,uint64,uint64));
        require(destination == EXCHANGE && token == 0 && amount == expected, "CoreWriter spot send");
    }

    function testOriginalFirstFullSend() public { check(false, true); }
    function testOriginalSecondFullSend() public { check(false, false); }
    function testReplacementFirstReducedSend() public { check(true, true); }
    function testReplacementSecondReducedSend() public { check(true, false); }
    function checkDelivery(bool first, uint64 residual) internal {
        check(true, first);
        address user = first ? USER1 : USER2;
        address proxy = first ? PROXY1 : PROXY2;
        uint64 sent = (first ? SPOT1 : SPOT2) - 100_000_000;
        bytes32 pendingSlot = keccak256(abi.encode(user, uint256(33)));
        bytes32 balanceSlot = keccak256(abi.encode(user, uint256(9)));
        uint256 credit = uint256(sent) * 1e10;
        vm.clearMockedCalls();
        vm.mockCall(FACTORY, abi.encodeWithSelector(bytes4(0xc1a9a508), user), abi.encode(proxy));
        vm.mockCall(address(0x801), bytes(""), abi.encode(uint256(residual), uint256(0), uint256(0)));
        vm.mockCall(address(0x803), bytes(""), abi.encode(uint256(0)));
        vm.roll(PIN + 1);
        vm.recordLogs();
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSignature("finalizeSweep(address)", user));
        require(ok && out.length == 0, "delivered finalization");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == EXCHANGE, "one Exchange log");
        require(logs[0].topics.length == 2, "Swept topics");
        require(logs[0].topics[0] == 0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696, "Swept topic");
        require(logs[0].topics[1] == bytes32(uint256(uint160(user))), "Swept user");
        require(abi.decode(logs[0].data, (uint256)) == credit, "Swept amount");
        require(vm.load(EXCHANGE, pendingSlot) == bytes32(0), "pending cleared");
        require(uint256(vm.load(EXCHANGE, balanceSlot)) == 5e18 + credit, "user credit");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == 100e18 + credit, "treasury credit");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) == ((uint256(7) << 128) | (100e18 + credit)), "total credit");
        require(MockCoreWriter(CORE_WRITER).calls() == 1, "no second CoreWriter call");
    }
    function testReplacementFirstDeliveredCredit() public { checkDelivery(true, 0); }
    function testReplacementSecondDeliveredCredit() public { checkDelivery(false, 0); }
    function testReplacementFirstNoFeeResidualCredit() public { checkDelivery(true, 100_000_000); }
    function testReplacementSecondNoFeeResidualCredit() public { checkDelivery(false, 100_000_000); }
}
"""


def inputs():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    unit_scales = json.loads((ATLAS / "exchange_unit_scales_behavior.json").read_text())
    assert unit_scales["pin"] == manifest["block"]
    assert unit_scales["exchange_proxy"] == EXCHANGE
    assert unit_scales["pinned_slot3"] == 10**12
    assert unit_scales["pinned_slot5"] == 10**10
    scope = json.loads(gzip.decompress(SCOPE.read_bytes()))
    stalled_capture = json.loads(gzip.decompress(STALLED.read_bytes()))
    assert manifest["block"] == scope["pin"] == stalled_capture["pin"] == 48_902_346
    rows = {row["address"]: row for row in scope["rows"]}
    replacement_code = rows[REPLACEMENT]["runtime"]
    replacement_sha = hashlib.sha256(bytes.fromhex(replacement_code[2:])).hexdigest()
    assert (
        replacement_sha
        == "c755794c2d6cf6077dded83c91067b4e9e07fc386e63c322ff7e4389cd697f4d"
    )
    cases = stalled_capture["cases"]
    assert len(cases) == 2
    assert [(row["user"], row["proxy"]) for row in cases] == [
        (
            "0x56cbe78a5cdfa10147927aec550aa7f2fb3d3d01",
            "0x1e8a704179cc6221592c362daa52a341ae20084d",
        ),
        (
            "0x9c8599c32224d7d9956a7def18f7314162f77baf",
            "0xf6b60cdf359af5538495831a9f2bbcada23e10e6",
        ),
    ]
    for row, (_, last) in zip(cases, stalled.stalled_rows(), strict=True):
        assert (
            hashlib.sha256(bytes.fromhex(row["proxy_code"][2:])).hexdigest()
            == row["derived_runtime_sha256"]
        )
        assert int(row["pending_word"], 16) == (
            (int(row["last_sweep_word"], 16) << 128) | last["spot_raw"]
        )
    for address in (EXCHANGE, ORIGINAL, ADMIN):
        entry = manifest["contracts"][address]
        code = (ATLAS / entry["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == entry["sha256"]
    return manifest, replacement_code, replacement_sha, cases


def run():
    manifest, replacement_code, replacement_sha, cases = inputs()
    solc = shutil.which("solc")
    assert solc, "local solc is required"
    with tempfile.TemporaryDirectory(
        prefix="papertrade-pt01-existing-replacement-"
    ) as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = "
            + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "Pt01Replacement.t.sol").write_text(TEST_SOURCE)
        runtime = {
            "Replacement": replacement_code,
            "UserProxy1": cases[0]["proxy_code"],
            "UserProxy2": cases[1]["proxy_code"],
        }
        for name, address in (
            ("ExchangeProxy", EXCHANGE),
            ("Original", ORIGINAL),
            ("ProxyAdmin", ADMIN),
        ):
            runtime[name] = (
                (ATLAS / manifest["contracts"][address]["runtime_file"])
                .read_text()
                .strip()
            )
        for name, code in runtime.items():
            (project / "runtime" / f"{name}.hex").write_text(code)
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True,
            check=False,
            text=True,
            timeout=60,
        )
    output = result.stdout + "\n" + result.stderr
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    if result.returncode or passed != TEST_NAMES:
        raise RuntimeError(
            "PT-01 existing replacement replay failed: " + output[-5000:]
        )
    payload = {
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "replacement": REPLACEMENT,
        "replacement_sha256": replacement_sha,
        "original": ORIGINAL,
        "runtime_hashes": {
            name: manifest["contracts"][address]["sha256"]
            for name, address in (
                ("ExchangeProxy", EXCHANGE),
                ("Original", ORIGINAL),
                ("ProxyAdmin", ADMIN),
            )
        },
        "proxy_runtime_hashes": [row["derived_runtime_sha256"] for row in cases],
        "test_names": sorted(passed),
        "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
        "forge_result": "8 passed, 0 failed",
        "requested_raw_spot": [5_005_091_600, 1_210_000_000],
        "replacement_sent_raw_spot": [4_905_091_600, 1_110_000_000],
        "conditional_credit_internal": [49_050_916 * 10**12, 11_100_000 * 10**12],
        "tested_post_send_residual_raw_spot": [0, 100_000_000],
        "pinned_unit_slots": {"3": 10**12, "5": 10**10},
        "limits": [
            "This is a local implementation swap, not a historical upgrade or a recommended production upgrade.",
            "The Exchange factory and Core balance precompiles are mocked; the CoreWriter is a local recorder, so no HyperCore delivery or fee is tested.",
            "The second finalization assumes an accepted Core send leaving either zero or 1 USDC proxy spot balance; no HyperCore delivery is reproduced.",
            "Only finalizeSweep retry and finalization behavior is exercised; storage-layout and safety equivalence of all other replacement functions is unproved.",
            "The replacement is linked to an older library address and may change unrelated trading and accounting behavior.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    return verify()


def verify():
    manifest, _, replacement_sha, cases = inputs()
    saved = json.loads(OUT.read_text())
    assert (
        saved["pin"] == manifest["block"]
        and saved["block_hash"] == manifest["block_hash"]
    )
    assert (
        saved["replacement"] == REPLACEMENT
        and saved["replacement_sha256"] == replacement_sha
    )
    assert saved["original"] == ORIGINAL
    assert saved["runtime_hashes"] == {
        name: manifest["contracts"][address]["sha256"]
        for name, address in (
            ("ExchangeProxy", EXCHANGE),
            ("Original", ORIGINAL),
            ("ProxyAdmin", ADMIN),
        )
    }
    assert saved["proxy_runtime_hashes"] == [
        row["derived_runtime_sha256"] for row in cases
    ]
    assert set(saved["test_names"]) == TEST_NAMES
    assert (
        saved["test_source_sha256"] == hashlib.sha256(TEST_SOURCE.encode()).hexdigest()
    )
    assert saved["forge_result"] == "8 passed, 0 failed"
    assert saved["requested_raw_spot"] == [5_005_091_600, 1_210_000_000]
    assert saved["replacement_sent_raw_spot"] == [4_905_091_600, 1_110_000_000]
    assert saved["conditional_credit_internal"] == [49_050_916 * 10**12, 11_100_000 * 10**12]
    assert saved["tested_post_send_residual_raw_spot"] == [0, 100_000_000]
    assert saved["pinned_unit_slots"] == {"3": 10**12, "5": 10**10}
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", action="store_true", help="replay the deployed runtimes locally"
    )
    args = parser.parse_args()
    result = run() if args.run else verify()
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("pin", "forge_result", "replacement_sent_raw_spot")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
