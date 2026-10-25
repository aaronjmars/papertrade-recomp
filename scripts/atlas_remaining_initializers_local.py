#!/usr/bin/env python3
"""Probe four unindexed initializer and admin selectors on pinned Papertrade runtimes."""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PROXY = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
STAKING = "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15"
SESSION_PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SESSION = "0x8a5069fe303e8f81e91825436e956d595032e558"
TOKENOMICS_PROXY = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
TOKENOMICS = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
OUT = ROOT / "artifacts" / "remaining_initializers_local" / "replay.json"
STAKING_BEHAVIOR = ATLAS / "staking_initializers_behavior.json"
SESSION_BEHAVIOR = ATLAS / "session_initializer_behavior.json"
TOKENOMICS_BEHAVIOR = ATLAS / "tokenomics_initializer_behavior.json"
TEST_NAMES = {"testProbeStakingAdmin", "testProbeStakingThreeAddress", "testProbeSession",
              "testProbeTokenomics", "testProbeTokenomicsAdminFresh", "testProbeSessionCreationCalldata", "testProbeSessionInitVariants"}
TEST_SOURCE = '''pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function chainId(uint256) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function record() external;
    function accesses(address) external returns (bytes32[] memory, bytes32[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract RemainingInitializerTest {
    event log_named_uint(string key, uint256 val);
    event log_named_bytes(string key, bytes val);
    event log_named_bytes32(string key, bytes32 val);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant STAKING_PROXY = address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016)));
    address constant STAKING = address(uint160(uint256(0x00e6e3519455170913c5c3bfe541dd918a2d0cbb15)));
    address constant SESSION_PROXY = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant SESSION = address(uint160(uint256(0x008a5069fe303e8f81e91825436e956d595032e558)));
    address constant TOKENOMICS_PROXY = address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9)));
    address constant TOKENOMICS = address(uint160(uint256(0x00600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant USER = address(0x1234);
    address constant NEXT_OWNER = address(0x1111);
    address constant NEXT_OTHER = address(0x2222);
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    function setUp() public {
        vm.etch(STAKING_PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(SESSION_PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(TOKENOMICS_PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(STAKING, vm.parseBytes(vm.readFile("runtime/Staking.hex")));
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/Session.hex")));
        vm.etch(TOKENOMICS, vm.parseBytes(vm.readFile("runtime/Tokenomics.hex")));
        vm.store(STAKING_PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(STAKING))));
        vm.store(SESSION_PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(SESSION))));
        vm.store(TOKENOMICS_PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(TOKENOMICS))));
        vm.store(STAKING_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(SESSION_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(TOKENOMICS_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
    }
    function probe(string memory label, address target, address sender, bytes memory input)
        internal returns (bool ok, bytes memory out, Vm.Log[] memory logs) {
        vm.record();
        vm.recordLogs();
        vm.prank(sender);
        (ok, out) = target.call(input);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(target);
        logs = vm.getRecordedLogs();
        emit log_named_uint(string.concat(label,"-ok"), ok ? 1 : 0);
        emit log_named_bytes(string.concat(label,"-out"), out);
        emit log_named_uint(string.concat(label,"-reads"), reads.length);
        emit log_named_uint(string.concat(label,"-writes"), writes.length);
        for (uint256 i; i < writes.length; ++i) {
            emit log_named_bytes32(string.concat(label,"-slot"), writes[i]);
            emit log_named_bytes32(string.concat(label,"-value"), vm.load(target, writes[i]));
        }
        emit log_named_uint(string.concat(label,"-logs"), logs.length);
        for (uint256 i; i < logs.length; ++i) {
            emit log_named_bytes32(string.concat(label,"-topic"), logs[i].topics[0]);
            emit log_named_bytes(string.concat(label,"-data"), logs[i].data);
        }
    }
    function isError(bool ok, bytes memory out, bytes4 selector) internal pure returns (bool) {
        return !ok && out.length == 4 && bytes4(out) == selector;
    }
    function assertTokenomicsInitialized(Vm.Log[] memory logs) internal view {
        require(vm.load(TOKENOMICS_PROXY, bytes32(0)) == bytes32((uint256(uint160(NEXT_OWNER)) << 16) | 1), "tokenomics owner/flag");
        require(vm.load(TOKENOMICS_PROXY, bytes32(uint256(1))) == bytes32(uint256(uint160(NEXT_OTHER))), "tokenomics second address");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(5)))) == 0x01a784379d99db42000000, "tokenomics default 5");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(6)))) == 0x0422ca8b0a00a425000000, "tokenomics default 6");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(7)))) == 0x056bc75e2d63100000, "tokenomics default 7");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(8)))) == 0x6342fd08f00f6378000000, "tokenomics default 8");
        require(logs.length == 2, "tokenomics events");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == keccak256("OwnerUpdated(address)"), "tokenomics owner event");
        require(logs[0].topics[1] == bytes32(uint256(uint160(NEXT_OWNER))) && logs[0].data.length == 0, "tokenomics owner payload");
        require(logs[1].topics.length == 1 && logs[1].topics[0] == keccak256("MintParamsUpdated(uint256,uint256,uint256,uint256)"), "tokenomics params event");
        require(keccak256(logs[1].data) == keccak256(abi.encode(uint256(0x01a784379d99db42000000),
            uint256(0x0422ca8b0a00a425000000), uint256(0x056bc75e2d63100000),
            uint256(0x6342fd08f00f6378000000))), "tokenomics params payload");
    }
    function testProbeStakingAdmin() public {
        bytes memory data = abi.encodeWithSelector(bytes4(0x0f71c8bc), NEXT_OWNER, NEXT_OTHER);
        (bool ok, bytes memory out, Vm.Log[] memory logs) = probe("staking-admin-user", STAKING_PROXY, USER, data);
        require(isError(ok, out, bytes4(0xc031a0df)) && logs.length == 0, "staking outsider");
        (ok, out, logs) = probe("staking-admin-admin", STAKING_PROXY, ADMIN, data);
        require(ok && out.length == 0 && logs.length == 2, "staking fresh admin");
        require(vm.load(STAKING_PROXY, bytes32(uint256(15))) == bytes32(uint256(uint160(NEXT_OWNER))), "staking owner");
        require(vm.load(STAKING_PROXY, bytes32(uint256(16))) == bytes32((uint256(1) << 160) | uint256(uint160(NEXT_OTHER))), "staking executor/flag");
        require(logs[0].topics.length == 2 && logs[0].topics[0] == keccak256("OwnerUpdated(address)"), "staking owner event");
        require(logs[0].topics[1] == bytes32(uint256(uint160(NEXT_OWNER))) && logs[0].data.length == 0, "staking owner topic");
        require(logs[1].topics.length == 2 && logs[1].topics[0] == keccak256("AuthorizedExecutorUpdated(address)"), "staking executor event");
        require(logs[1].topics[1] == bytes32(uint256(uint160(NEXT_OTHER))) && logs[1].data.length == 0, "staking executor topic");
        (ok, out, logs) = probe("staking-admin-repeat", STAKING_PROXY, ADMIN, data);
        require(isError(ok, out, bytes4(0x3f733c4f)) && logs.length == 0, "staking repeat");
    }
    function testProbeStakingThreeAddress() public {
        bytes memory data = abi.encodeWithSelector(bytes4(0xc0c53b8b), NEXT_OWNER, NEXT_OTHER, address(0x3333));
        (bool ok, bytes memory out, Vm.Log[] memory logs) = probe("staking-three-user", STAKING_PROXY, USER, data);
        require(isError(ok, out, bytes4(0xb7b2509c)) && logs.length == 0, "staking three fresh user");
        (ok, out, logs) = probe("staking-three-admin", STAKING_PROXY, ADMIN, data);
        require(isError(ok, out, bytes4(0xb7b2509c)) && logs.length == 0, "staking three fresh admin");
        vm.store(STAKING_PROXY, bytes32(uint256(16)), bytes32(uint256(1) << 160));
        (ok, out, logs) = probe("staking-three-initialized", STAKING_PROXY, USER, data);
        require(isError(ok, out, bytes4(0xb7b2509c)) && logs.length == 0, "staking three initialized");
        require(vm.load(STAKING_PROXY, bytes32(uint256(15))) == bytes32(0), "staking three no owner write");
    }
    function testProbeSession() public {
        vm.chainId(999);
        bytes memory data = abi.encodeWithSelector(bytes4(0x747b8a1c), NEXT_OWNER, "Name", "1", uint256(999), NEXT_OTHER);
        (bool ok, bytes memory out, Vm.Log[] memory logs) = probe("session-user", SESSION_PROXY, USER, data);
        require(isError(ok, out, bytes4(0xf50220aa)) && logs.length == 0, "session fresh user");
        (ok, out, logs) = probe("session-admin", SESSION_PROXY, ADMIN, data);
        require(isError(ok, out, bytes4(0xf50220aa)) && logs.length == 0, "session fresh admin");
        (ok, out, logs) = probe("session-contract-args", SESSION_PROXY, USER,
            abi.encodeWithSelector(bytes4(0x747b8a1c), address(this), "Name", "1", uint256(999), address(this)));
        require(isError(ok, out, bytes4(0xf50220aa)) && logs.length == 0, "session contract args");
        (ok, out, logs) = probe("session-zero-args", SESSION_PROXY, USER,
            abi.encodeWithSelector(bytes4(0x747b8a1c), address(0), "", "", uint256(0), address(0)));
        require(isError(ok, out, bytes4(0xf50220aa)) && logs.length == 0, "session zero args");
        require(vm.load(SESSION_PROXY, bytes32(0)) == bytes32(0), "session rollback");
        vm.store(SESSION_PROXY, bytes32(uint256(0)), bytes32(uint256(1)));
        (ok, out, logs) = probe("session-initialized", SESSION_PROXY, USER, data);
        require(isError(ok, out, bytes4(0x0dc149f0)) && logs.length == 0, "session initialized");
    }
    function testProbeSessionCreationCalldata() public {
        vm.chainId(999);
        bytes memory data = vm.parseBytes(vm.readFile("runtime/SessionInit.hex"));
        address owner = address(uint160(uint256(0x00a1763a5ff94ebddd417cccb906622ec762ab2e29)));
        address exchange = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
        (bool ok, bytes memory out, Vm.Log[] memory logs) = probe("session-historical-args", SESSION_PROXY, owner, data);
        require(ok && out.length == 0 && logs.length == 2, "session historical call");
        require(vm.load(SESSION_PROXY, bytes32(0)) == bytes32(uint256(1)), "session init flag");
        require(vm.load(SESSION_PROXY, bytes32(uint256(1))) ==
            0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77, "session domain");
        require(vm.load(SESSION_PROXY, bytes32(uint256(2))) == bytes32(uint256(uint160(owner))), "session owner");
        require(vm.load(SESSION_PROXY, bytes32(uint256(3))) == bytes32(uint256(uint160(exchange))), "session caller");
        require(logs[0].emitter == SESSION_PROXY && logs[0].topics.length == 2 &&
            logs[0].topics[0] == keccak256("OwnerUpdated(address)") &&
            logs[0].topics[1] == bytes32(uint256(uint160(owner))) && logs[0].data.length == 0,
            "session owner event");
        require(logs[1].emitter == SESSION_PROXY && logs[1].topics.length == 2 &&
            logs[1].topics[0] == keccak256("AuthorizedCallerUpdated(address)") &&
            logs[1].topics[1] == bytes32(uint256(uint160(exchange))) && logs[1].data.length == 0,
            "session caller event");
    }
    function clearSession() internal {
        for (uint256 slot; slot < 4; ++slot) vm.store(SESSION_PROXY, bytes32(slot), bytes32(0));
    }
    function testProbeSessionInitVariants() public {
        vm.chainId(999);
        address owner = address(uint160(uint256(0x00a1763a5ff94ebddd417cccb906622ec762ab2e29)));
        address exchange = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
        bytes memory historic = vm.parseBytes(vm.readFile("runtime/SessionInit.hex"));
        (bool ok, bytes memory out, Vm.Log[] memory logs) = probe("session-variant-sender", SESSION_PROXY, USER, historic);
        require(ok && out.length == 0 && logs.length == 2, "session sender independent");
        clearSession();
        (ok, out, logs) = probe("session-variant-name", SESSION_PROXY, owner,
            abi.encodeWithSelector(bytes4(0x747b8a1c), owner, "Name", "1", uint256(999), exchange));
        require(isError(ok, out, bytes4(0xf50220aa)) && logs.length == 0, "session name restriction");
        clearSession();
        (ok, out, logs) = probe("session-variant-name-same-length", SESSION_PROXY, owner,
            abi.encodeWithSelector(bytes4(0x747b8a1c), owner, "StrinG", "1", uint256(999), exchange));
        require(isError(ok, out, bytes4(0xf50220aa)) && logs.length == 0, "session name bytes restriction");
        clearSession();
        (ok, out, logs) = probe("session-variant-exchange", SESSION_PROXY, owner,
            abi.encodeWithSelector(bytes4(0x747b8a1c), owner, "String", "1", uint256(999), NEXT_OTHER));
        require(ok && out.length == 0 && logs.length == 2 &&
            vm.load(SESSION_PROXY, bytes32(uint256(3))) == bytes32(uint256(uint160(NEXT_OTHER))),
            "session caller argument");
        clearSession();
        (ok, out, logs) = probe("session-variant-owner", SESSION_PROXY, owner,
            abi.encodeWithSelector(bytes4(0x747b8a1c), NEXT_OWNER, "String", "1", uint256(999), exchange));
        require(ok && out.length == 0 && logs.length == 2 &&
            vm.load(SESSION_PROXY, bytes32(uint256(2))) == bytes32(uint256(uint160(NEXT_OWNER))),
            "session owner argument");
        clearSession();
        (ok, out, logs) = probe("session-variant-chain", SESSION_PROXY, owner,
            abi.encodeWithSelector(bytes4(0x747b8a1c), owner, "String", "1", uint256(1000), exchange));
        require(ok && out.length == 0 && logs.length == 2, "session chain argument");
        clearSession();
        (ok, out, logs) = probe("session-variant-version", SESSION_PROXY, owner,
            abi.encodeWithSelector(bytes4(0x747b8a1c), owner, "String", "2", uint256(999), exchange));
        require(isError(ok, out, bytes4(0xf50220aa)) && logs.length == 0, "session version restriction");
    }
    function testProbeTokenomicsAdminFresh() public {
        bytes memory data = abi.encodeWithSelector(bytes4(0x485cc955), NEXT_OWNER, NEXT_OTHER);
        (bool ok, bytes memory out, Vm.Log[] memory logs) = probe("tokenomics-admin-fresh", TOKENOMICS_PROXY, ADMIN, data);
        require(ok && out.length == 0, "tokenomics admin fresh");
        assertTokenomicsInitialized(logs);
    }
    function testProbeTokenomics() public {
        bytes memory data = abi.encodeWithSelector(bytes4(0x485cc955), NEXT_OWNER, NEXT_OTHER);
        (bool ok, bytes memory out, Vm.Log[] memory logs) = probe("tokenomics-user", TOKENOMICS_PROXY, USER, data);
        require(ok && out.length == 0, "tokenomics user fresh");
        assertTokenomicsInitialized(logs);
        (ok, out, logs) = probe("tokenomics-admin", TOKENOMICS_PROXY, ADMIN, data);
        require(isError(ok, out, bytes4(0x0dc149f0)) && logs.length == 0, "tokenomics repeat");
    }

}
'''

def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtimes = {}
    for label, address in (("Proxy", PROXY), ("Staking", STAKING), ("Session", SESSION), ("Tokenomics", TOKENOMICS)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-remaining-init-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "RemainingInitializer.t.sol").write_text(TEST_SOURCE)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        creation_trace = json.loads((ROOT / "artifacts" / "session_creation" /
            "0xe055509195f0ea1b9e30c366c3350d10470d8c1d145bfa51686b49134d36ffbe.calls.json").read_text())
        init_call = creation_trace["calls"][0]
        assert init_call["type"] == "DELEGATECALL" and init_call["to"].lower() == SESSION
        assert init_call["input"].startswith("0x747b8a1c")
        creation_dir = ROOT / "artifacts" / "session_creation"
        creation_hash = "0xe055509195f0ea1b9e30c366c3350d10470d8c1d145bfa51686b49134d36ffbe"
        receipt = json.loads((creation_dir / f"{creation_hash}.receipt.json").read_text())
        transaction = json.loads((creation_dir / f"{creation_hash}.transaction.json").read_text())
        owner = "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
        exchange = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
        assert creation_trace["type"] == "CREATE" and creation_trace["to"].lower() == SESSION_PROXY
        assert receipt["transactionHash"].lower() == creation_hash and receipt["status"] == "0x1"
        assert receipt["contractAddress"].lower() == SESSION_PROXY and receipt["from"].lower() == owner
        assert transaction["hash"].lower() == creation_hash and transaction["from"].lower() == owner and transaction["to"] is None
        payload = bytes.fromhex(init_call["input"][2:])
        assert len(payload) == 292
        words = [int.from_bytes(payload[4+i*32:4+(i+1)*32], "big") for i in range(5)]
        assert words == [int(owner, 16), 160, 224, 999, int(exchange, 16)]
        assert payload[4+words[1]:4+words[1]+64] == (6).to_bytes(32, "big") + b"String".ljust(32, b"\0")
        assert payload[4+words[2]:4+words[2]+64] == (1).to_bytes(32, "big") + b"1".ljust(32, b"\0")
        assert [(log["address"].lower(), log["topics"][0].lower(), int(log["topics"][1], 16), log["data"])
                for log in receipt["logs"]] == [
            (SESSION_PROXY, "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b", int(owner, 16), "0x"),
            (SESSION_PROXY, "0xfe60173cc964bc674632fcf67031bba24c8a99a4a7d6518c726586978b7e30d3", int(exchange, 16), "0x")]
        (project / "runtime" / "SessionInit.hex").write_text(init_call["input"])
        run = subprocess.run(["forge", "test", "--root", tmp, "-vvv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    if run.returncode:
        raise RuntimeError(output[-6000:])
    for line in output.splitlines():
        if "session-historical-args" in line or "session-variant-" in line:
            print(line.strip())
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    assert passed == TEST_NAMES, (passed, output[-3000:])
    assert re.search(r"7 tests passed, 0 failed", output), output[-3000:]
    replay_path = "../../artifacts/remaining_initializers_local/replay.json"
    runtime_hashes = {label: manifest["contracts"][address]["sha256"] for label, address in
                      (("Proxy", PROXY), ("Staking", STAKING), ("Session", SESSION), ("Tokenomics", TOKENOMICS))}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"pin": manifest["block"], "block_hash": manifest["block_hash"],
                               "runtime_hashes": runtime_hashes, "test_source_sha256": hashlib.sha256(TEST_SOURCE.encode()).hexdigest(),
                               "forge_result": "7 passed, 0 failed", "test_names": sorted(passed),
                               "scope": "Exact pinned proxy and implementation runtimes in synthetic fresh and initialized storage; SessionKeyManager creation call and receipt captured from archive"}, indent=2) + "\n")
    common = {"pin": manifest["block"], "block_hash": manifest["block_hash"], "local_replay": replay_path}
    STAKING_BEHAVIOR.write_text(json.dumps({**common, "staking_proxy": PROXY, "implementation": STAKING,
        "runtime_sha256": runtime_hashes["Staking"],
        "selector_behaviors": {
            "0x0f71c8bc": "Two-address admin-only setup: outsider returns 0xc031a0df; proxy admin in fresh state writes owner to slot 15 and authorized executor plus initialization flag to slot 16, emits OwnerUpdated and AuthorizedExecutorUpdated; repeat returns 0x3f733c4f",
            "0xc0c53b8b": "Three-address calldata returns 0xb7b2509c with no persisted writes or logs for user and proxy admin in fresh state and for user with slot-16 initialized flag"},
        "fresh_state": {"owner_slot": 15, "executor_and_flag_slot": 16,
                        "executor_address_bits": [0, 159], "initialized_flag_bit": 160},
        "simulated_error_catalog": [
            {"selector": "0xc031a0df", "probe_paths": ["staking-admin-user"]},
            {"selector": "0x3f733c4f", "probe_paths": ["staking-admin-repeat"]},
            {"selector": "0xb7b2509c", "probe_paths": ["staking-three-user", "staking-three-admin", "staking-three-initialized"]}],
        "source_names": "unresolved", "historical_calls_for_these_selectors": 0}, indent=2) + "\n")
    SESSION_BEHAVIOR.write_text(json.dumps({**common, "session_proxy": SESSION_PROXY, "implementation": SESSION,
        "runtime_sha256": runtime_hashes["Session"], "selector_behaviors": {
            "0x747b8a1c": "Historical deployment calldata initializes slot 0, domain separator slot 1, owner slot 2, authorized caller slot 3, and emits OwnerUpdated and AuthorizedCallerUpdated. In fresh state, changing name String (including same-length StrinG) or version 1 reverts with 0xf50220aa, while changing sender, owner, authorized caller, or domain chain ID succeeds. A repeat returns AlreadyInitialized()"},
        "simulated_error_catalog": [
            {"selector": "0xf50220aa", "probe_paths": ["session-user", "session-admin", "session-contract-args", "session-zero-args"]},
            {"selector": "0x0dc149f0", "probe_paths": ["session-initialized"], "public_signature_candidates": ["AlreadyInitialized()"]}],
        "selector_reconstructions": {"0x747b8a1c": "initialize(address,string,string,uint256,address)"},
        "historical_creation": {"transaction_hash": creation_hash, "block": int(receipt["blockNumber"], 16),
            "trace": "../../artifacts/session_creation/" + creation_hash + ".calls.json",
            "receipt": "../../artifacts/session_creation/" + creation_hash + ".receipt.json",
            "transaction": "../../artifacts/session_creation/" + creation_hash + ".transaction.json",
            "decoded_arguments": {"owner": owner, "name": "String", "version": "1", "chain_id": 999,
                "authorized_caller": exchange}},
        "fresh_state": {"initialized_flag_slot": 0, "domain_separator_slot": 1,
            "domain_separator_historical": "0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77",
            "owner_slot": 2, "authorized_caller_slot": 3},
        "event_catalog": [
            {"topic0": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
             "reconstructed_signature": "OwnerUpdated(address)", "status": "historical_creation_and_local_replay"},
            {"topic0": "0xfe60173cc964bc674632fcf67031bba24c8a99a4a7d6518c726586978b7e30d3",
             "reconstructed_signature": "AuthorizedCallerUpdated(address)", "status": "historical_creation_and_local_replay"}],
        "source_name_status": "selector hash, archive creation call, and exact-runtime replay verified; source unavailable",
        "historical_creation_calls_for_selector": 1}, indent=2) + "\n")
    TOKENOMICS_BEHAVIOR.write_text(json.dumps({**common, "tokenomics_proxy": TOKENOMICS_PROXY,
        "implementation": TOKENOMICS, "runtime_sha256": runtime_hashes["Tokenomics"],
        "selector_reconstructions": {"0x485cc955": "initialize(address,address)"},
        "selector_behaviors": {"0x485cc955": "Fresh state accepts either arbitrary user or proxy admin as caller, sets owner and second address, writes four default mint parameter words, emits OwnerUpdated and MintParamsUpdated; repeat returns AlreadyInitialized()"},
        "fresh_state": {"owner_slot": 0, "owner_bits": [16,175], "initialized_flag_bit": 0,
                        "second_address_slot": 1,
                        "default_parameter_slots": {str(slot): hex(value) for slot,value in ((5,0x01a784379d99db42000000),
                            (6,0x0422ca8b0a00a425000000), (7,0x056bc75e2d63100000), (8,0x6342fd08f00f6378000000))}},
        "event_catalog": [
            {"topic0": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
             "reconstructed_signature": "OwnerUpdated(address)", "status": "simulated_log_only"},
            {"topic0": "0xdbf6f1878073adede0b153c63f457c1c601a056124755086092f973f19550176",
             "reconstructed_signature": "MintParamsUpdated(uint256,uint256,uint256,uint256)", "status": "simulated_log_only"}],
        "simulated_error_catalog": [
            {"selector": "0x0dc149f0", "probe_paths": ["tokenomics-admin"],
             "public_signature_candidates": ["AlreadyInitialized()"]}],
        "historical_calls_for_selector": 0,
        "source_name_status": "signature hash and behavior verified; original source unavailable"}, indent=2) + "\n")
    print("7 exact-runtime initializer tests passed across Staking, SessionKeyManager, and Tokenomics")

if __name__ == "__main__":
    main()
