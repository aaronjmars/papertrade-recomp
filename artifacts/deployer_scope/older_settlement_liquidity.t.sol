pragma solidity ^0.8.24;

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
    address constant LIBRARY = 0xac8Ba1307815f74bd13d4D039c96f7B97e81AA49;
    function run(bytes memory data) external returns (bool, bytes memory) {
        return LIBRARY.delegatecall(data);
    }
}

contract OlderSettlementLiquidityTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant LIBRARY = 0xac8Ba1307815f74bd13d4D039c96f7B97e81AA49;
    address constant USER = address(0x1234);
    bytes32 constant ENQUEUED = 0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7;
    DelegateHarness harness;

    function setUp() public {
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        harness = new DelegateHarness();
        vm.store(address(harness), bytes32(uint256(17)), bytes32(uint256(1)));
    }

    function userSlot(uint256 base) internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, base));
    }

    function nodeSlot(uint256 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(15)));
    }

    function check(
        int256 pnl, uint256 gainRate, uint256 lossRate, uint256 available,
        uint256 payout, uint256 immediateGain, uint256 queued, uint256 feeOne, uint256 feeTwo
    ) internal {
        vm.recordLogs();
        (bool ok, bytes memory out) = harness.run(abi.encodeWithSelector(
            bytes4(0xaa31b143), uint256(15), USER, uint256(500), pnl,
            gainRate, lossRate, available
        ));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(ok && out.length == 192, "settlement call");
        (uint256 a, uint256 b, uint256 c, uint256 d, uint256 e, uint256 f) =
            abi.decode(out, (uint256, uint256, uint256, uint256, uint256, uint256));
        require(a == payout && b == immediateGain && c == queued && d == 0, "payout words");
        require(e == feeOne && f == feeTwo, "fee words");
        require(uint256(vm.load(address(harness), bytes32(uint256(17)))) == (queued > 0 ? 2 : 1), "next node");
        require(uint256(vm.load(address(harness), bytes32(uint256(18)))) == queued, "global queued");
        require(uint256(vm.load(address(harness), userSlot(19))) == queued, "user queued");
        require(uint256(vm.load(address(harness), bytes32(uint256(16)))) == (queued > 0 ? 1 : 0), "global head");
        require(uint256(vm.load(address(harness), userSlot(20))) == (queued > 0 ? 1 : 0), "user head");
        require(uint256(vm.load(address(harness), userSlot(21))) == (queued > 0 ? 1 : 0), "user tail");
        if (queued > 0) {
            require(uint256(vm.load(address(harness), nodeSlot(1))) == uint256(uint160(USER)), "node owner");
            require(uint256(vm.load(address(harness), bytes32(uint256(nodeSlot(1)) + 1))) == queued, "node amount");
            require(logs.length == 1 && logs[0].emitter == address(harness), "queue log count");
            require(logs[0].topics.length == 3 && logs[0].topics[0] == ENQUEUED, "queue topic");
            require(logs[0].topics[1] == bytes32(uint256(uint160(USER))) && logs[0].topics[2] == bytes32(uint256(1)), "queue indexed fields");
            require(abi.decode(logs[0].data, (uint256)) == queued, "queue log amount");
        } else {
            require(uint256(vm.load(address(harness), nodeSlot(1))) == 0, "unexpected node");
            require(logs.length == 0, "unexpected log");
        }
    }

    function testProfitNoLiquidityQueuesAll() public {
        check(101, 3e16, 7e16, 0, 500, 0, 101, 0, 0);
    }
    function testProfitPartialLiquidityQueuesRemainder() public {
        check(101, 3e16, 7e16, 100, 500, 100, 1, 0, 0);
    }
    function testProfitExactLiquidityPaysWithoutFee() public {
        check(101, 3e16, 7e16, 101, 500, 101, 0, 0, 0);
    }
    function testProfitBelowFeeThresholdPaysWithoutFee() public {
        check(101, 3e16, 7e16, 103, 500, 101, 0, 0, 0);
    }
    function testProfitAtFeeThresholdPaysFee() public {
        check(101, 3e16, 7e16, 104, 500, 98, 0, 1, 2);
    }
    function testProfitUsesGainRate() public {
        check(101, 1e16, 9e16, 200, 500, 100, 0, 0, 1);
    }
    function testLossFeeIndependentOfLiquidity() public {
        check(-101, 3e16, 7e16, 0, 399, 0, 0, 3, 4);
    }
    function testLossUsesLossRate() public {
        check(-101, 1e16, 9e16, 200, 399, 0, 0, 4, 5);
    }
    function testFlatNoLiquidity() public {
        check(0, 3e16, 7e16, 0, 500, 0, 0, 0, 0);
    }
}
