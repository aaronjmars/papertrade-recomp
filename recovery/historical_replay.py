"""Shared Forge driver for the historical PT-01 parity replays.

Each parity script supplies archived data; this module generates a self-contained test
that replays one archived transaction with a chosen implementation installed behind the
Exchange proxy, then runs it with the local toolchain only. No RPC, no transaction.
"""

import json
import pathlib
import re
import shutil
import subprocess
import tempfile

FAIL = re.compile(r"\[FAIL[^\]]*\] (test\w+)\(\)")
PASS = re.compile(r"\[PASS\] (test\w+)\(\)")

VM_INTERFACE = """interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
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
    function snapshot() external returns (uint256);
    function revertTo(uint256) external returns (bool);
}"""


def run_tests(source, code_files, prefix, timeout=180):
    """Return ({test name: passed}, raw output) for one generated test contract."""
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix=prefix) as temp:
        project = pathlib.Path(temp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(shutil.which("solc")) +
            '\nevm_version = "cancun"\noffline = true\n'
            'fs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        (project / "test" / "Parity.t.sol").write_text(source)
        for address, code in code_files.items():
            (project / "runtime" / f"{address[2:]}.hex").write_text(code)
        result = subprocess.run(["forge", "test", "--root", temp, "-vv"],
                                check=False, capture_output=True, text=True, timeout=timeout)
    output = result.stdout + "\n" + result.stderr
    passed, failed = set(PASS.findall(output)), set(FAIL.findall(output))
    assert passed or failed, "the generated parity contract did not compile: " + output[-6000:]
    return {name: name in passed for name in sorted(passed | failed)}, output


def build(
    *,
    setup_lines,
    archive_lines,
    calldata,
    caller,
    proxy,
    target,
    block,
    timestamp,
    chain_id,
    pinned_address,
    live_address,
    recovery_address,
    post_slots,
    strict_live,
    strict_recovery,
):
    """The generated replay contract for one archived transaction."""
    post_loads = [f"vm.load({address}, {slot})" for address, slot in post_slots]
    post_checks = "\n".join(
        f'        require(vm.load({address}, {slot}) == snapshotWords[{index}], "trajectory {index}");'
        for index, (address, slot) in enumerate(post_slots)
    )
    strict_tests = []
    if strict_live:
        strict_tests.append("""    function testLiveReplayMatchesArchive() public {
        (Vm.Log[] memory logs, bool ok, bytes memory result) = replay(LIVE);
        require(ok, "live replay reverted");
{archive}
    }
""".replace("{archive}", "\n".join("        " + line for line in archive_lines)))
    if strict_recovery:
        strict_tests.append("""    function testRecoveryReplayMatchesArchive() public {
        (Vm.Log[] memory logs, bool ok, bytes memory result) = replay(RECOVERY);
        require(ok, "recovery replay reverted");
{archive}
    }
""".replace("{archive}", "\n".join("        " + line for line in archive_lines)))
    return f'''pragma solidity ^0.8.24;

{VM_INTERFACE}

contract RecoveryParityTest {{
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = {proxy};
    address constant TARGET = {target};
    address constant PINNED = {pinned_address};
    address constant LIVE = {live_address};
    address constant RECOVERY = {recovery_address};
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;

    function setUp() public {{
        vm.roll({block});
        vm.warp({timestamp});
        vm.chainId({chain_id});
{chr(10).join(setup_lines)}
    }}

    function replay(address implementation) internal returns (Vm.Log[] memory logs, bool ok, bytes memory result) {{
        vm.store(EXCHANGE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(implementation))));
        vm.recordLogs();
        vm.prank({caller});
        (ok, result) = TARGET.call(hex"{calldata}");
        logs = vm.getRecordedLogs();
    }}

    function testPinnedReplayMatchesArchive() public {{
        (Vm.Log[] memory logs, bool ok, bytes memory result) = replay(PINNED);
        require(ok, "pinned replay reverted");
{chr(10).join("        " + line for line in archive_lines)}
    }}

{chr(10).join(strict_tests)}
    /// @dev The candidate and the live implementation must behave identically on this
    ///      archived transaction, whatever the live implementation does.
    function testLiveAndRecoveryReplayAgree() public {{
        uint256 snap = vm.snapshot();
        (Vm.Log[] memory liveLogs, bool liveOk, bytes memory liveResult) = replay(LIVE);
        require(liveOk, "live replay reverted");
        bytes32[{len(post_slots)}] memory snapshotWords = [{", ".join(post_loads)}];
        vm.revertTo(snap);
        (Vm.Log[] memory recoveryLogs, bool recoveryOk, bytes memory recoveryResult) = replay(RECOVERY);
        require(recoveryOk, "recovery replay reverted");
        require(keccak256(liveResult) == keccak256(recoveryResult), "return data");
        require(liveLogs.length == recoveryLogs.length, "log count");
        for (uint256 i; i < liveLogs.length; i++) {{
            require(liveLogs[i].emitter == recoveryLogs[i].emitter, "log emitter");
            require(liveLogs[i].topics.length == recoveryLogs[i].topics.length, "log topic count");
            for (uint256 j; j < liveLogs[i].topics.length; j++)
                require(liveLogs[i].topics[j] == recoveryLogs[i].topics[j], "log topic");
            require(keccak256(liveLogs[i].data) == keccak256(recoveryLogs[i].data), "log data");
        }}
{post_checks}
    }}
}}
'''


LOG_COUNT_PROBE = """
    function testProbeLogCount() public {
        (Vm.Log[] memory logs, bool ok,) = replay(%s);
        require(ok, "probe replay reverted");
        revert(string.concat("log count=", vm.toString(logs.length)));
    }
}
"""


def log_count(source, code_files, prefix, implementation="LIVE"):
    """How many logs one implementation emits, for a ledger whose archive comparison diverged."""
    assert implementation in ("LIVE", "PINNED", "RECOVERY")
    if "function toString(" not in source:
        source = source.replace(
            "    function revertTo(uint256) external returns (bool);",
            "    function revertTo(uint256) external returns (bool);\n"
            "    function toString(uint256) external pure returns (string memory);")
    source = source[:source.rstrip().rfind("}")] + LOG_COUNT_PROBE % implementation
    _, output = run_tests(source, code_files, prefix + "probe-")
    found = re.search(r"log count=(\d+)", output)
    assert found, "the log-count probe did not report: " + output[-3000:]
    return int(found.group(1))


def resolve(build, code_files, prefix, archive_tests, limits):
    """Run the strict form; re-run without an archive test that the live set no longer meets.

    The pinned implementation must always reproduce the archive, and the candidate must
    always reproduce the live implementation. `archive_tests` records, per test, whether
    the strict archive comparison was met on the first pass.
    """
    anchor, agreement = "testPinnedReplayMatchesArchive", "testLiveAndRecoveryReplayAgree"
    optional = [name for name in archive_tests if name != anchor]
    results, output = run_tests(build(True, True), code_files, prefix)
    assert results.get(anchor), "the pinned implementation must reproduce the archive: " + output[-4000:]
    assert results.get(agreement), "candidate must match the live implementation: " + output[-4000:]
    archive = {name: bool(results.get(name)) for name in archive_tests}
    relaxed = not all(archive[name] for name in optional)
    if relaxed:
        results, output = run_tests(build(False, False), code_files, prefix)
        assert results.get(anchor) and results.get(agreement), \
            "relaxed parity replay failed: " + output[-4000:]
    return {
        "archive_matched": archive,
        "relaxed_rerun": relaxed,
        "replay_tests": results,
        "forge_result": f"{sum(results.values())} passed, 0 failed",
        "limits": limits,
    }, (not relaxed, not relaxed)