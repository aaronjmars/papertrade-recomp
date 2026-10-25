pragma solidity ^0.8.24;
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
    function writeFile(string calldata, string calldata) external;
    function toString(bytes32) external pure returns (string memory);
    function toString(bytes calldata) external pure returns (string memory);
    function toString(uint256) external pure returns (string memory);
}
contract Delegator {
    function run(address target, bytes memory data) external returns (bool, bytes memory) {
        return target.delegatecall(data);
    }
}
contract ExchangeSelectorGap {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    address constant PROXY = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant LIBRARY = address(uint160(uint256(0x00cd617f984158a4f5d287ddee0e8eb0fed204916d)));
    address constant ORACLE = address(uint160(uint256(0x00a9b4c7b7ca5835652d81e25739c870d49f39cc2e)));
    address constant ORACLE_IMPL = address(uint160(uint256(0x003997ffc8cbd281d4fc8d0548e505ae2fbbbd985a)));
    address constant TOKENOMICS = address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9)));
    address constant TOKENOMICS_IMPL = address(uint160(uint256(0x00600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f)));
    address constant PAPER = address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e)));
    address constant PAPER_IMPL = address(uint160(uint256(0x00433bd418ec92818a960585f4d5fae563e735bb4a)));
    address constant PAPER_MATH = address(uint160(uint256(0x00e991817199363046da0a28da6fbad0284e4aa492)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant PAUSE_GUARDIAN = address(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)));
    address constant MARKET_KEEPER = address(uint160(uint256(0x003721476de31190dc1af8908026abe20efe25cf99)));
    address constant AUTHORIZED_EXECUTOR = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant USER = address(uint160(uint256(0x007822efb68be9e458efa6307d3386921b23ac3ade)));
    address constant OUTSIDER = address(uint160(uint256(0x0000000000000000000000000000000000000beef0)));
    address constant BBO_PRECOMPILE = address(uint160(uint256(0x00000000000000000000000000000000000000080e)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    string resultsPath;

    function node(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(15))); }
    function instrument(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(7))); }
    function position(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(10))); }
    function balanceKey(address user) internal pure returns (bytes32) { return keccak256(abi.encode(user, uint256(9))); }

    function execSlots() internal pure returns (bytes32[] memory slots) {
        slots = new bytes32[](37);
        uint256[15] memory direct = [uint256(0), 1, 2, 8, 14, 18, 19, 22, 23, 24, 25, 26, 29, 37, 88];
        for (uint256 i = 0; i < direct.length; i++) slots[i] = bytes32(direct[i]);
        slots[15] = instrument(0);
        slots[16] = bytes32(uint256(instrument(0)) + 1);
        slots[17] = bytes32(uint256(instrument(0)) + 2);
        slots[18] = instrument(1);
        slots[19] = position(1394473);
        slots[20] = bytes32(uint256(position(1394473)) + 1);
        slots[21] = balanceKey(USER);
        slots[22] = keccak256(abi.encode(uint256(0), uint256(35)));
        slots[23] = keccak256(abi.encode(uint256(0), uint256(33)));
        slots[24] = keccak256(abi.encode(USER, uint256(33)));
        slots[25] = keccak256(abi.encode(uint256(0), uint256(11)));
        slots[26] = keccak256(abi.encode(uint256(0), uint256(31)));
        slots[27] = keccak256(abi.encode(uint256(0), uint256(32)));
        slots[28] = keccak256(abi.encode(uint256(0), uint256(34)));
        slots[29] = keccak256(abi.encode(uint256(0), uint256(36)));
        slots[30] = node(101);
        slots[31] = bytes32(uint256(node(101)) + 1);
        slots[32] = node(102);
        slots[33] = bytes32(uint256(node(102)) + 1);
        slots[34] = keccak256(abi.encode(USER, uint256(19)));
        slots[35] = keccak256(abi.encode(USER, uint256(20)));
        slots[36] = keccak256(abi.encode(USER, uint256(21)));
    }

    function libSlots() internal pure returns (bytes32[] memory slots) {
        slots = new bytes32[](18);
        slots[0] = bytes32(uint256(15));
        slots[1] = bytes32(uint256(16));
        slots[2] = bytes32(uint256(17));
        slots[3] = bytes32(uint256(18));
        slots[4] = node(1);
        slots[5] = bytes32(uint256(node(1)) + 1);
        slots[6] = node(2);
        slots[7] = bytes32(uint256(node(2)) + 1);
        slots[8] = node(3);
        slots[9] = bytes32(uint256(node(3)) + 1);
        slots[10] = keccak256(abi.encode(USER, uint256(19)));
        slots[11] = keccak256(abi.encode(USER, uint256(20)));
        slots[12] = keccak256(abi.encode(USER, uint256(21)));
        slots[13] = keccak256(abi.encode(USER, uint256(22)));
        slots[14] = node(101);
        slots[15] = bytes32(uint256(node(101)) + 1);
        slots[16] = node(102);
        slots[17] = bytes32(uint256(node(102)) + 1);
    }

    function userSlot(uint256 base) internal pure returns (bytes32) { return keccak256(abi.encode(USER, base)); }

    function seedQueue(address target) internal {
        vm.store(target, node(101), bytes32(uint256(uint160(USER)) | (uint256(102) << 160)));
        vm.store(target, bytes32(uint256(node(101)) + 1), bytes32(uint256(300)));
        vm.store(target, node(102), bytes32(uint256(uint160(USER)) | (uint256(101) << 208)));
        vm.store(target, bytes32(uint256(node(102)) + 1), bytes32(uint256(700)));
        vm.store(target, bytes32(uint256(16)), bytes32(uint256(101)));
        vm.store(target, bytes32(uint256(17)), bytes32(uint256(103)));
        vm.store(target, bytes32(uint256(18)), bytes32(uint256(1000)));
        vm.store(target, userSlot(19), bytes32(uint256(1000)));
        vm.store(target, userSlot(20), bytes32(uint256(101)));
        vm.store(target, userSlot(21), bytes32(uint256(102)));
    }

    function snap(address target, bytes32[] memory slots) internal view returns (bytes32) {
        bytes memory buffer = new bytes(slots.length * 32);
        for (uint256 i = 0; i < slots.length; i++) {
            bytes32 value = vm.load(target, slots[i]);
            assembly { mstore(add(add(buffer, 32), mul(i, 32)), value) }
        }
        return keccak256(buffer);
    }

    function dump(address target, bytes32[] memory slots) internal view returns (string memory) {
        string memory out = "";
        for (uint256 i = 0; i < slots.length; i++) {
            out = string.concat(out, i == 0 ? "" : ";",
                vm.toString(slots[i]), ":", vm.toString(vm.load(target, slots[i])));
        }
        return out;
    }

    function logSummary(Vm.Log[] memory logs) internal view returns (string memory) {
        string memory summary = "";
        for (uint256 i = 0; i < logs.length; i++) {
            string memory topic0 = logs[i].topics.length > 0 ? vm.toString(logs[i].topics[0]) : "none";
            summary = string.concat(summary,
                i == 0 ? "" : ";",
                vm.toString(uint256(uint160(logs[i].emitter))),
                ":", topic0, ":", vm.toString(logs[i].topics.length), ":", vm.toString(logs[i].data.length));
        }
        return summary;
    }

    function chain(string memory a, string memory b) internal pure returns (string memory) {
        return bytes(a).length == 0 ? b : string.concat(a, "|", b);
    }

    function run(string memory name, address target, address caller, bytes memory data, bool seeded) internal {
        if (seeded) seedQueue(target);
        bytes32[] memory slots = target == LIBRARY ? libSlots() : execSlots();
        string memory slotsBefore = dump(target, slots);
        bytes32 before = snap(target, slots);
        vm.recordLogs();
        vm.prank(caller);
        (bool ok, bytes memory output) = target.call(data);
        vm.writeFile(string.concat(resultsPath, "/", name, ".txt"),
            string.concat("status=", ok ? "ok" : "revert",
            "\ndata=", vm.toString(output),
            "\nlogs=", logSummary(vm.getRecordedLogs()),
            "\nfp_before=", vm.toString(before),
            "\nfp_after=", vm.toString(snap(target, slots)),
            "\nslots_before=", slotsBefore,
            "\nslots_after=", dump(target, slots)));
    }

    function setUp() public {
        resultsPath = "results";
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        vm.etch(ORACLE, vm.parseBytes(vm.readFile("runtime/Oracle.hex")));
        vm.etch(ORACLE_IMPL, vm.parseBytes(vm.readFile("runtime/OracleImplementation.hex")));
        vm.etch(TOKENOMICS, vm.parseBytes(vm.readFile("runtime/Tokenomics.hex")));
        vm.etch(TOKENOMICS_IMPL, vm.parseBytes(vm.readFile("runtime/TokenomicsImplementation.hex")));
        vm.etch(PAPER, vm.parseBytes(vm.readFile("runtime/Paper.hex")));
        vm.etch(PAPER_IMPL, vm.parseBytes(vm.readFile("runtime/PaperImplementation.hex")));
        vm.etch(PAPER_MATH, vm.parseBytes(vm.readFile("runtime/PaperMath.hex")));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(ORACLE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(ORACLE_IMPL))));
        vm.store(TOKENOMICS, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(TOKENOMICS_IMPL))));
        vm.store(PAPER, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(PAPER_IMPL))));
        // pinned Exchange words
        vm.store(PROXY, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        vm.store(PROXY, bytes32(uint256(1)), bytes32(uint256(uint160(PAUSE_GUARDIAN))));
        vm.store(PROXY, bytes32(uint256(2)), bytes32(uint256(uint160(ORACLE))));
        vm.store(PROXY, bytes32(uint256(6)), bytes32(uint256(uint160(TOKENOMICS))));
        vm.store(PROXY, bytes32(uint256(8)), bytes32(uint256(2)));
        vm.store(PROXY, bytes32(uint256(14)), bytes32(uint256(0x00000000000000000000000000000000000000000035b5849a35d618f5b00800)));
        vm.store(PROXY, bytes32(uint256(18)), 0);
        vm.store(PROXY, bytes32(uint256(22)), bytes32(uint256(0x000000000007be65f23207ad7ea19168000000000029d3d6f9e2192a05b05b45)));
        vm.store(PROXY, bytes32(uint256(23)), bytes32(uint256(2e16)));
        vm.store(PROXY, bytes32(uint256(24)), bytes32(uint256(2e16)));
        vm.store(PROXY, bytes32(uint256(25)), bytes32(uint256(0x00000000000000000000000000000000000000000000000000470de4df820000)));
        vm.store(PROXY, bytes32(uint256(26)), bytes32(uint256(0x00000000000000433b768a255b8b62b9000000000000000564ea03bde8d561b3)));
        vm.store(PROXY, bytes32(uint256(29)), bytes32(uint256(uint160(SESSION)) << 8));
        vm.store(PROXY, bytes32(uint256(37)), bytes32(uint256(uint160(MARKET_KEEPER))));
        vm.store(PROXY, bytes32(uint256(88)), bytes32(uint256(uint160(AUTHORIZED_EXECUTOR))));
        vm.store(PROXY, instrument(0), bytes32(uint256(0x000003e8000000000000002c28d1751327a700000000032d26d12e980b600000)));
        vm.store(PROXY, bytes32(uint256(instrument(0)) + 1), bytes32(uint256(0x00016345785d8a00000001b0f51147891600000000084595161401484a000000)));
        vm.store(PROXY, bytes32(uint256(instrument(0)) + 2), bytes32(uint256(0x00000000000000000000000000000000000000000000152d02c7e14af6800000)));
        vm.store(PROXY, instrument(1), bytes32(uint256(0x000003e8000000010000001a3c8ed044f4c780000000032d26d12e980b600000)));
        vm.store(PROXY, position(1394473), bytes32(uint256(0x00000000000c5a35000000007822efb68be9e458efa6307d3386921b23ac3ade)));
        vm.store(PROXY, bytes32(uint256(position(1394473)) + 1), bytes32(uint256(0x00010001000000006ad5339d000000640000000000000002b5e3af16b1880000)));
        vm.store(PROXY, balanceKey(USER), bytes32(uint256(0x00000000000000000000000000000000000000000000004c63f26b0d02ddab6f)));
        // pinned Tokenomics and PAPER words from the archived liquidation prestate
        vm.store(TOKENOMICS, bytes32(uint256(3)), bytes32(uint256(0x0000000000000000000000000000000000000000000422ff0dc1275e2cfd56e7)));
        vm.store(TOKENOMICS, bytes32(uint256(4)), bytes32(uint256(0x000000000000000000000000000000000000000000c3fa356cc6e9b5a8a1d173)));
        vm.store(TOKENOMICS, bytes32(0), bytes32(uint256(bytes32(uint256(0x00000000000000000000b915fa41e824d6aa31bb833ee81220c0f2c8ea0f0001)))));
        vm.store(TOKENOMICS, bytes32(uint256(1)), bytes32(uint256(0x0000000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a2)));
        vm.store(TOKENOMICS, bytes32(uint256(2)), bytes32(uint256(0x000000000000000000000000e40f17915daa230324030003a197cdaef2261c0e)));
        vm.store(PAPER, bytes32(uint256(3)), bytes32(uint256(0x000000000000000000000000b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
        vm.store(PAPER, bytes32(uint256(4)), bytes32(uint256(0x00000000000000000000000075174549dbbd44497d31a47e2e2d7406408d63d9)));
        vm.store(PAPER, bytes32(uint256(9)), bytes32(uint256(0x000000000000000000000000aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016)));
        vm.store(PAPER, bytes32(uint256(6)), bytes32(uint256(0x00000000000000000000000000000000000000001bdc5b516305a080eebe6597)));
        vm.store(PAPER, 0xe567d5326fdde87864781de7be41927ba45ea21033a6e650bdd93891a6ba1d5c, bytes32(uint256(0x000000000000000000000000000000000000000000000099d9545a7243063852)));
        // library queue baseline for direct library calls
        vm.store(LIBRARY, bytes32(uint256(16)), 0);
        vm.store(LIBRARY, bytes32(uint256(17)), bytes32(uint256(1)));
        vm.store(LIBRARY, bytes32(uint256(18)), 0);
        // default HyperCore BBO response
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
    }

    function runDelegated(string memory name, address caller, bytes memory data, bool seeded) internal {
        Delegator delegator = new Delegator();
        if (seeded) {
            seedQueue(address(delegator));
        } else {
            vm.store(address(delegator), bytes32(uint256(16)), 0);
            vm.store(address(delegator), bytes32(uint256(17)), bytes32(uint256(1)));
            vm.store(address(delegator), bytes32(uint256(18)), 0);
        }
        bytes32[] memory slots = libSlots();
        string memory slotsBefore = dump(address(delegator), slots);
        bytes32 before = snap(address(delegator), slots);
        vm.recordLogs();
        vm.prank(caller);
        (bool ok, bytes memory output) = delegator.run(LIBRARY, data);
        vm.writeFile(string.concat(resultsPath, "/", name, ".txt"),
            string.concat("status=", ok ? "ok" : "revert",
            "\ndata=", vm.toString(output),
            "\nlogs=", logSummary(vm.getRecordedLogs()),
            "\nfp_before=", vm.toString(before),
            "\nfp_after=", vm.toString(snap(address(delegator), slots)),
            "\nslots_before=", slotsBefore,
            "\nslots_after=", dump(address(delegator), slots)));
    }

    function caseFn(string memory name, address target, address caller, bytes memory data, bool seeded) internal {
        if (target == LIBRARY) vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        if (target == address(0)) {
            runDelegated(name, caller, data, seeded);
            return;
        }
        run(name, target, caller, data, seeded);
    }

    function test_short_0x01681a62() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x01681a62", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x01681a62)), false);
    }
    function test_outsider_0x01681a62() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x01681a62", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x01681a62), USER), false);
    }
    function test_short_0x2d2451d1() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x2d2451d1", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x2d2451d1)), false);
    }
    function test_outsider_0x2d2451d1() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f000000000000000000000000000000000000000000000000000000003b9aca006000527f000000000000000000000000000000000000000000000000000000004190ab0060205260406000f3"));
        caseFn("outsider_0x2d2451d1", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)), false);
    }
    function test_short_0x415f1240() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x415f1240", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x415f1240)), false);
    }
    function test_outsider_0x415f1240() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x415f1240", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x415f1240), uint256(1394473)), false);
    }
    function test_short_0x4a4d9eea() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x4a4d9eea", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x4a4d9eea)), false);
    }
    function test_outsider_0x4a4d9eea() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x4a4d9eea", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x4a4d9eea), USER, uint256(101), uint256(102)), false);
    }
    function test_short_0x5ca4c0ea() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x5ca4c0ea", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x5ca4c0ea)), false);
    }
    function test_outsider_0x5ca4c0ea() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x5ca4c0ea", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x5ca4c0ea), uint32(0), uint128(1e18), uint96(1), uint96(1), uint64(1)), false);
    }
    function test_short_0x6a3214c9() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x6a3214c9", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x6a3214c9)), false);
    }
    function test_outsider_0x6a3214c9() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x6a3214c9", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(1)), false);
    }
    function test_short_0x753a369c() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x753a369c", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x753a369c)), false);
    }
    function test_outsider_0x753a369c() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x753a369c", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x753a369c), USER, uint256(101), uint256(102), uint256(2)), false);
    }
    function test_short_0x827ad94c() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x827ad94c", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x827ad94c)), false);
    }
    function test_outsider_0x827ad94c() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x827ad94c", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x827ad94c), USER, uint256(101), uint256(102), uint256(2)), false);
    }
    function test_short_0xae4daf4e() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0xae4daf4e", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xae4daf4e)), false);
    }
    function test_outsider_0xae4daf4e() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0xae4daf4e", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xae4daf4e), USER, uint256(101), uint256(102)), false);
    }
    function test_short_0xae69b95b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0xae69b95b", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xae69b95b)), false);
    }
    function test_outsider_0xae69b95b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0xae69b95b", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xae69b95b), true), false);
    }
    function test_short_0xc0c53b8b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0xc0c53b8b", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xc0c53b8b)), false);
    }
    function test_outsider_0xc0c53b8b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0xc0c53b8b", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xc0c53b8b), OUTSIDER, ORACLE, PAPER), false);
    }
    function test_short_0xd7c7e5fb() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0xd7c7e5fb", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xd7c7e5fb)), false);
    }
    function test_outsider_0xd7c7e5fb() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0xd7c7e5fb", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xd7c7e5fb), uint32(0), uint32(1), uint256(1)), false);
    }
    function test_short_0xe538b280() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0xe538b280", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xe538b280)), false);
    }
    function test_outsider_0xe538b280() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0xe538b280", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xe538b280), uint256(1e16), uint256(2e16), uint256(3e16)), false);
    }
    function test_short_0x18958ce2() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x18958ce2", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x18958ce2)), false);
    }
    function test_outsider_0x18958ce2() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x18958ce2", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, uint256(500)), false);
    }
    function test_delegate_0x18958ce2() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("delegate_0x18958ce2", address(0), OUTSIDER, abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, uint256(500)), false);
    }
    function test_short_0x2448a553() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x2448a553", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x2448a553)), false);
    }
    function test_outsider_0x2448a553() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x2448a553", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x2448a553), uint256(15), USER, uint256(1), uint256(2), uint256(1e18)), false);
    }
    function test_delegate_0x2448a553() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("delegate_0x2448a553", address(0), OUTSIDER, abi.encodeWithSelector(bytes4(0x2448a553), uint256(15), USER, uint256(1), uint256(2), uint256(1e18)), false);
    }
    function test_short_0x32db40c9() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x32db40c9", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x32db40c9)), false);
    }
    function test_outsider_0x32db40c9() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x32db40c9", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x32db40c9), uint256(15), USER, uint256(101), uint256(102), uint256(2)), false);
    }
    function test_delegate_0x32db40c9() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("delegate_0x32db40c9", address(0), OUTSIDER, abi.encodeWithSelector(bytes4(0x32db40c9), uint256(15), USER, uint256(101), uint256(102), uint256(2)), false);
    }
    function test_short_0x3cf4208d() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x3cf4208d", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x3cf4208d)), false);
    }
    function test_outsider_0x3cf4208d() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x3cf4208d", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x3cf4208d), uint256(15), USER, uint256(101), uint256(102), uint256(2), uint256(1e18)), false);
    }
    function test_delegate_0x3cf4208d() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("delegate_0x3cf4208d", address(0), OUTSIDER, abi.encodeWithSelector(bytes4(0x3cf4208d), uint256(15), USER, uint256(101), uint256(102), uint256(2), uint256(1e18)), false);
    }
    function test_short_0x3f4e3626() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0x3f4e3626", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x3f4e3626)), false);
    }
    function test_outsider_0x3f4e3626() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0x3f4e3626", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0x3f4e3626), uint256(15), USER, uint256(100)), false);
    }
    function test_delegate_0x3f4e3626() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("delegate_0x3f4e3626", address(0), OUTSIDER, abi.encodeWithSelector(bytes4(0x3f4e3626), uint256(15), USER, uint256(100)), false);
    }
    function test_short_0xb67f3dd7() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0xb67f3dd7", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0xb67f3dd7)), false);
    }
    function test_outsider_0xb67f3dd7() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0xb67f3dd7", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0xb67f3dd7), uint256(1e18), uint64(100), uint64(110), uint256(0), uint256(1e18), uint256(1e6), uint256(1e18)), false);
    }
    function test_delegate_0xb67f3dd7() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("delegate_0xb67f3dd7", address(0), OUTSIDER, abi.encodeWithSelector(bytes4(0xb67f3dd7), uint256(1e18), uint64(100), uint64(110), uint256(0), uint256(1e18), uint256(1e6), uint256(1e18)), false);
    }
    function test_short_0xca02ff91() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("short_0xca02ff91", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0xca02ff91)), false);
    }
    function test_outsider_0xca02ff91() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("outsider_0xca02ff91", LIBRARY, OUTSIDER, abi.encodeWithSelector(bytes4(0xca02ff91), uint256(15), USER, uint256(101), uint256(102)), false);
    }
    function test_delegate_0xca02ff91() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("delegate_0xca02ff91", address(0), OUTSIDER, abi.encodeWithSelector(bytes4(0xca02ff91), uint256(15), USER, uint256(101), uint256(102)), false);
    }
    function test_owner_0xe538b280() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("owner_0xe538b280", PROXY, OWNER, abi.encodeWithSelector(bytes4(0xe538b280), uint256(1e16), uint256(2e16), uint256(3e16)), false);
    }
    function test_cap_0xe538b280() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("cap_0xe538b280", PROXY, OWNER, abi.encodeWithSelector(bytes4(0xe538b280), uint256(5e17 + 1), uint256(0), uint256(0)), false);
    }
    function test_owner_0xae69b95b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("owner_0xae69b95b", PROXY, OWNER, abi.encodeWithSelector(bytes4(0xae69b95b), true), false);
    }
    function test_guardian_0xae69b95b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("guardian_0xae69b95b", PROXY, PAUSE_GUARDIAN, abi.encodeWithSelector(bytes4(0xae69b95b), true), false);
    }
    function test_guardian_false_0xae69b95b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("guardian_false_0xae69b95b", PROXY, PAUSE_GUARDIAN, abi.encodeWithSelector(bytes4(0xae69b95b), false), false);
    }
    function test_owner_0x2d2451d1() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f000000000000000000000000000000000000000000000000000000003b9aca006000527f000000000000000000000000000000000000000000000000000000004190ab0060205260406000f3"));
        caseFn("owner_0x2d2451d1", PROXY, OWNER, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)), false);
    }
    function test_invalid_0x2d2451d1() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f000000000000000000000000000000000000000000000000000000003b9aca006000527f000000000000000000000000000000000000000000000000000000004190ab0060205260406000f3"));
        caseFn("invalid_0x2d2451d1", PROXY, OWNER, abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(2)), false);
    }
    function test_owner_0xd7c7e5fb() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("owner_0xd7c7e5fb", PROXY, OWNER, abi.encodeWithSelector(bytes4(0xd7c7e5fb), uint32(0), uint32(1), uint256(1)), false);
    }
    function test_zero_0xd7c7e5fb() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("zero_0xd7c7e5fb", PROXY, OWNER, abi.encodeWithSelector(bytes4(0xd7c7e5fb), uint32(0), uint32(0), uint256(1)), false);
    }
    function test_owner_0x5ca4c0ea() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("owner_0x5ca4c0ea", PROXY, OWNER, abi.encodeWithSelector(bytes4(0x5ca4c0ea), uint32(0), uint128(1e18), uint96(1), uint96(1), uint64(1)), false);
    }
    function test_invalid_0x5ca4c0ea() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("invalid_0x5ca4c0ea", PROXY, OWNER, abi.encodeWithSelector(bytes4(0x5ca4c0ea), uint32(2), uint128(1e18), uint96(1), uint96(1), uint64(1)), false);
    }
    function test_initialized_0xc0c53b8b() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("initialized_0xc0c53b8b", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0xc0c53b8b), OUTSIDER, ORACLE, PAPER), false);
    }
    function test_inactive_0x415f1240() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("inactive_0x415f1240", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x415f1240), uint256(999999)), false);
    }
    function test_farprice_0x415f1240() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("farprice_0x415f1240", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x415f1240), uint256(1394473)), false);
    }
    function test_boundary_0x415f1240() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c136000527f00000000000000000000000000000000000000000000000000000000000c3c1360205260406000f3"));
        caseFn("boundary_0x415f1240", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x415f1240), uint256(1394473)), false);
    }
    function test_out_of_bound_0x415f1240() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("out_of_bound_0x415f1240", PROXY, OUTSIDER, abi.encodeWithSelector(bytes4(0x415f1240), type(uint256).max), false);
    }
    function test_owner_0x6a3214c9() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("owner_0x6a3214c9", PROXY, OWNER, abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(1)), false);
    }
    function test_keeper_0x01681a62() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("keeper_0x01681a62", PROXY, MARKET_KEEPER, abi.encodeWithSelector(bytes4(0x01681a62), USER), false);
    }
    function test_merge_0x753a369c() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_0x753a369c", PROXY, USER, abi.encodeWithSelector(bytes4(0x753a369c), USER, uint256(101), uint256(102), uint256(2)), true);
    }
    function test_merge_0x827ad94c() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_0x827ad94c", PROXY, USER, abi.encodeWithSelector(bytes4(0x827ad94c), USER, uint256(101), uint256(102), uint256(2)), true);
    }
    function test_merge_0x4a4d9eea() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_0x4a4d9eea", PROXY, USER, abi.encodeWithSelector(bytes4(0x4a4d9eea), USER, uint256(101), uint256(1)), true);
    }
    function test_merge_0xae4daf4e() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_0xae4daf4e", PROXY, USER, abi.encodeWithSelector(bytes4(0xae4daf4e), USER, uint256(101), uint256(1)), true);
    }
    function test_merge_delegate_0x3cf4208d() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_delegate_0x3cf4208d", address(0), USER, abi.encodeWithSelector(bytes4(0x3cf4208d), uint256(15), USER, uint256(101), uint256(102), uint256(2), uint256(1e18)), true);
    }
    function test_merge_delegate_0x32db40c9() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_delegate_0x32db40c9", address(0), USER, abi.encodeWithSelector(bytes4(0x32db40c9), uint256(15), USER, uint256(101), uint256(102), uint256(2)), true);
    }
    function test_merge_delegate_0xca02ff91() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_delegate_0xca02ff91", address(0), USER, abi.encodeWithSelector(bytes4(0xca02ff91), uint256(15), USER, uint256(101), uint256(1)), true);
    }
    function test_merge_delegate_0x2448a553() public {
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("0x7f00000000000000000000000000000000000000000000000000000000000c3c146000527f00000000000000000000000000000000000000000000000000000000000c3c1460205260406000f3"));
        caseFn("merge_delegate_0x2448a553", address(0), USER, abi.encodeWithSelector(bytes4(0x2448a553), uint256(15), USER, uint256(101), uint256(1), uint256(1e18)), true);
    }}
