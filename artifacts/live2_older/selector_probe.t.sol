pragma solidity ^0.8.24;

// Exact-runtime probes for the first older Exchange (earlier_1) against the newest
// pinned Exchange for comparison.
//
// Each case etches the pinned 925-byte proxy runtime at the proxy address and the
// pinned implementation runtime at the implementation's own address, points the
// EIP-1967 slot at it, and seeds an owner word, a factory pointer, a pending word,
// one user balance, a treasury word and a packed total word. No HyperCore
// precompile is reached and no chain is needed (port-free Forge).
//
// out/*.jsonl notes are parsed by audit_live2_older.py --probe into
// artifacts/live2_older/selector_probe.json.

interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function writeFile(string calldata, string calldata) external;
    function toString(uint256) external pure returns (string memory);
}

contract ProbeBase {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address EXCHANGE;
    address IMPLEMENTATION;
    string proxyFile;
    string implementationFile;
    address constant ADMIN = address(uint160(uint256(0x00140ac259be101d76691c512eb8105911f2f309f1)));
    address constant FACTORY = address(uint160(uint256(0x0036365dc6bd9513692978e4ea8f3117a7bae55f28)));
    address constant OWNER = address(uint160(uint256(0x0069b4b92f02ff415e0c966686e00d2783b395d690)));
    address constant USER = address(uint160(uint256(0x00fb94d3404c1d3d9d6f08f79e58041d5ea95accfa)));
    address constant OUTSIDER = address(uint160(uint256(0xbeef)));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    string acc;

    function pendingSlot(address u) internal pure returns (bytes32) { return keccak256(abi.encode(u, uint256(33))); }
    function balanceSlot(address u) internal pure returns (bytes32) { return keccak256(abi.encode(u, uint256(9))); }

    function setupCommon() internal {
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile(proxyFile)));
        vm.etch(IMPLEMENTATION, vm.parseBytes(vm.readFile(implementationFile)));
        vm.store(EXCHANGE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPLEMENTATION))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(EXCHANGE, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        vm.store(EXCHANGE, bytes32(uint256(3)), bytes32(uint256(1e12)));
        vm.store(EXCHANGE, bytes32(uint256(30)), bytes32(uint256(uint160(FACTORY))));
        vm.store(EXCHANGE, balanceSlot(USER), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(uint256(100e18)));
        vm.store(EXCHANGE, bytes32(uint256(22)), bytes32((uint256(7) << 128) | uint256(100e18)));
    }

    function note(string memory tag, address caller, bytes memory data) internal {
        uint256 balBefore = uint256(vm.load(EXCHANGE, balanceSlot(USER)));
        uint256 treasuryBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        uint256 totalBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        vm.prank(caller);
        (bool ok, bytes memory out) = EXCHANGE.call(data);
        uint256 errorSelector = (!ok && out.length == 4) ? uint256(bytes32(out)) >> 224 : 0;
        acc = string.concat(acc, "{\"tag\":\"", tag, "\",\"ok\":", ok ? "true" : "false",
            ",\"err\":\"", vm.toString(errorSelector),
            "\",\"balance_delta\":\"", vm.toString(uint256(vm.load(EXCHANGE, balanceSlot(USER))) - balBefore),
            "\",\"treasury_delta\":\"", vm.toString(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) - treasuryBefore),
            "\",\"total_delta\":\"", vm.toString(uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) - totalBefore),
            "\",\"return_len\":\"", ok ? vm.toString(out.length) : "0",
            "\",\"return_word\":\"", (ok && out.length == 32) ? vm.toString(abi.decode(out, (uint256))) : "0",
            "\"}\n");
    }

    function flush(string memory name) internal {
        vm.writeFile(string.concat("out/", name, ".jsonl"), acc);
    }
}

contract OlderProbe is ProbeBase {
    function testRun() public {
        EXCHANGE = address(uint160(uint256(0x001b534e482b92bb6daff452cd12f2e35219e13493)));
        IMPLEMENTATION = address(uint160(uint256(0x00557c853e100600e0ee91e0df88fcf4af0097ff89)));
        proxyFile = "runtime/older_proxy.hex";
        implementationFile = "runtime/older_implementation.hex";
        setupCommon();
        note("reconcile-pendingzero-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(50e8)));
        note("reconcile-pendingzero-owner", OWNER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(50e8)));
        vm.store(EXCHANGE, pendingSlot(USER), bytes32(uint256(10_000_000_000) | (uint256(48_100_000) << 128)));
        note("reconcile-pendingset-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(50e8)));
        note("oldonly-b29af6b0-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0xb29af6b0), uint256(1e18)));
        note("oldonly-f92576b1-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0xf92576b1), OUTSIDER));
        note("oldonly-6155be59-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0x6155be59), uint256(1e18)));
        note("oldonly-6155be59-owner", OWNER, abi.encodeWithSelector(bytes4(0x6155be59), uint256(2e18)));
        note("harvest-outsider-empty", OUTSIDER, abi.encodeWithSelector(bytes4(0xddc63262), uint256(1)));
        note("clear-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        note("clear-owner-empty", OWNER, abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        flush("older");
    }
}

contract NewestProbe is ProbeBase {
    function testRun() public {
        EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
        IMPLEMENTATION = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
        proxyFile = "runtime/newest_proxy.hex";
        implementationFile = "runtime/newest_implementation.hex";
        setupCommon();
        note("reconcile-pendingzero-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(50e8)));
        note("reconcile-pendingzero-owner", OWNER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(50e8)));
        vm.store(EXCHANGE, pendingSlot(USER), bytes32(uint256(10_000_000_000) | (uint256(48_100_000) << 128)));
        note("reconcile-pendingset-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(50e8)));
        note("harvest-outsider-empty", OUTSIDER, abi.encodeWithSelector(bytes4(0xddc63262), uint256(1)));
        note("clear-outsider", OUTSIDER, abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        flush("newest");
    }
}