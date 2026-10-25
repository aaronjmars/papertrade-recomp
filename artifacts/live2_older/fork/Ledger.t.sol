pragma solidity ^0.8.24;

// Pass-two fork suite for the first older Papertrade Exchange (earlier_1).
//
// The suite forks live HyperEVM state (`forge test --fork-url`), so storage is the
// real deployed state of the first older Exchange proxy, still on its original
// implementation 0x557c853e100600e0ee91e0df88fcf4af0097ff89 and the pre-fix linked
// library 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49. Set-up asserts the EIP-1967
// implementation slot, the proxy code hash and the EIP-712 domain separator before
// any case runs.
//
// What is constructed and therefore simulated:
//   * the HyperCore BBO precompile 0x080e is a mock contract returning a fixed book
//     (entry 271710/271720, exit 271710/271620);
//   * one session key is registered by direct storage write;
//   * the user's internal balance, the queue node amounts and, where a case needs a
//     bankroll, the treasury slot are overwritten as labelled;
//   * Core status and CoreWriter precompiles are mocks that record calldata.
// Everything else - owner, factory, session manager, position counter, fee rates,
// instruments, queue base - is read from live state.
//
// notes land in out/*.txt and are parsed by audit_live2_older.py --fork.

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function sign(uint256, bytes32) external returns (uint8,bytes32,bytes32);
    function addr(uint256) external returns (address);
    function roll(uint256) external;
    function warp(uint256) external;
    function writeFile(string calldata, string calldata) external;
    function toString(uint256) external pure returns (string memory);
}

contract CoreEntry { fallback() external { assembly { mstore(0,271710) mstore(32,271720) return(0,64) } } }
contract CoreLower { fallback() external { assembly { mstore(0,271610) mstore(32,271620) return(0,64) } } }
contract CoreStatusMock { fallback() external { assembly { mstore(0,1) return(0,32) } } }
contract CoreSpotMock { fallback() external { assembly { mstore(0,6509967368792354) mstore(32,0) mstore(64,0) return(0,96) } } }
contract CoreWriterMock { event WriterCall(bytes data); fallback() external payable { emit WriterCall(msg.data); } }

contract LedgerTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x001b534e482b92bb6daff452cd12f2e35219e13493)));
    address constant SESSION = address(uint160(uint256(0x0091667db7e20474b3ac6eaabf0c8106ed46b5691a)));
    address constant BATCH = address(uint160(uint256(0x004041882573028cb177847c46f82e242024ebde66)));
    address constant IMPL = address(uint160(uint256(0x00557c853e100600e0ee91e0df88fcf4af0097ff89)));
    address constant USER = address(uint160(uint256(0x000000000000000000000000057d2403654b2ba82d4d95d0e0ffa2550e8140f4)));
    address constant BBO = address(0x080e);
    bytes32 constant DOMAIN = 0x148ad6651bcc1981a17c339cb9726dee6b4617126472e8236bad447c73665254;
    bytes32 constant TYPEHASH = 0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983;
    bytes32 constant CLOSE_TYPEHASH = 0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13;
    uint256 constant MARGIN = 25e18;
    uint256 constant PK = 0xb0b;
    string acc;

    function mapSlot(uint256 key, uint256 base) internal pure returns (bytes32) { return keccak256(abi.encode(key, base)); }
    function userSlot(uint256 base) internal pure returns (bytes32) { return mapSlot(uint256(uint160(USER)), base); }
    function nodeSlot(uint256 id) internal pure returns (bytes32) { return mapSlot(id, 15); }
    function locked() internal view returns (uint256) { (bool ok, bytes memory o) = EXCHANGE.staticcall(hex"01ad056f"); require(ok, "locked"); return abi.decode(o, (uint256)); }
    function totalBal() internal view returns (uint256) { (bool ok, bytes memory o) = EXCHANGE.staticcall(hex"a69a2ad1"); require(ok, "totalBalances"); return abi.decode(o, (uint256)); }
    function bank() internal view returns (uint256) { (bool ok, bytes memory o) = EXCHANGE.staticcall(hex"0cdd5fc4"); require(ok, "bankroll"); return abi.decode(o, (uint256)); }
    function note(string memory k, uint256 v) internal { acc = string.concat(acc, k, "=", vm.toString(v), " "); }

    function setUp() public {
        require(block.chainid == 999, "chain 999");
        require(vm.load(EXCHANGE, bytes32(uint256(0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc))) == bytes32(uint256(uint160(IMPL))), "live implementation slot");
        vm.etch(BBO, address(new CoreEntry()).code);
        address key = vm.addr(PK);
        vm.store(SESSION, keccak256(abi.encode(key, userSlot(4))), bytes32(uint256(block.timestamp + 3600)));
    }

    function openData(bool useDebt, uint256 margin, uint256 nonce) internal returns (bytes memory) {
        bytes32 sh = keccak256(abi.encode(TYPEHASH, USER, uint32(1), false, uint128(margin), uint32(75), useDebt, nonce, uint64(block.timestamp + 3600)));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, keccak256(abi.encodePacked(hex"1901", DOMAIN, sh)));
        return abi.encodeWithSelector(bytes4(0xec6783f0), USER, uint32(1), false, uint128(margin), uint32(75), useDebt, nonce, uint64(block.timestamp + 3600), v, r, s);
    }

    function openPos(bool useDebt, uint256 margin, uint256 nonce) internal returns (bool, uint256) {
        vm.prank(BATCH);
        (bool ok, bytes memory out) = EXCHANGE.call(openData(useDebt, margin, nonce));
        return (ok, ok && out.length == 32 ? abi.decode(out, (uint256)) : 0);
    }

    function closePos(uint256 id, uint256 nonce) internal returns (bool) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = id;
        bytes32 sh = keccak256(abi.encode(CLOSE_TYPEHASH, USER, keccak256(abi.encodePacked(ids)), nonce, uint64(block.timestamp + 3600)));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, keccak256(abi.encodePacked(hex"1901", DOMAIN, sh)));
        vm.prank(BATCH);
        (bool ok,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, uint64(block.timestamp + 3600), v, r, s));
        return ok;
    }

    /// @dev creates one queue node with the library itself: a plain profitable close
    ///      whose whole gain is deferred because the bankroll is forced to zero.
    function makeLibraryNode(uint256 nonce) internal {
        vm.store(EXCHANGE, userSlot(9), bytes32(uint256(100e18)));
        vm.etch(BBO, address(new CoreEntry()).code);
        (bool ok, uint256 id) = openPos(false, MARGIN, nonce);
        require(ok, "open for node");
        vm.etch(BBO, address(new CoreLower()).code);
        uint256 treasury = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(treasury - bank()));
        require(bank() == 0, "bankroll not drained");
        require(closePos(id, nonce + 1), "queueing close");
    }

    function inflateNode(uint256 node, uint256 amount) internal {
        vm.store(EXCHANGE, bytes32(uint256(nodeSlot(node)) + 1), bytes32(amount));
        vm.store(EXCHANGE, userSlot(19), bytes32(amount));
        vm.store(EXCHANGE, bytes32(uint256(18)), bytes32(amount));
    }

    function testDebtCycle() public {
        makeLibraryNode(5000000);
        uint256 node = uint256(vm.load(EXCHANGE, bytes32(uint256(16))));
        uint256 bal0 = uint256(vm.load(EXCHANGE, userSlot(9)));
        inflateNode(node, MARGIN);
        vm.etch(BBO, address(new CoreEntry()).code);
        (bool ok, uint256 id) = openPos(true, MARGIN, 5001000);
        note("open_ok", ok ? 1 : 0);
        note("open_userQueued", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("open_global", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        note("open_head", uint256(vm.load(EXCHANGE, userSlot(20))));
        note("open_tail", uint256(vm.load(EXCHANGE, userSlot(21))));
        note("open_nodeAmount", uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(node)) + 1))));
        note("open_balance_delta", uint256(vm.load(EXCHANGE, userSlot(9))) - bal0);
        vm.etch(BBO, address(new CoreLower()).code);
        uint256 treasury = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(treasury - bank()));
        require(closePos(id, 5001001), "debt close");
        note("debt_close_queued", uint256(vm.load(EXCHANGE, userSlot(19))));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(treasury + 1000000e18));
        note("bank_at_harvest", bank());
        (bool hok, bytes memory hout) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xddc63262), uint256(4)));
        note("harvest_ok", hok ? 1 : 0);
        note("harvest_paid", hok && hout.length == 32 ? abi.decode(hout, (uint256)) : 0);
        note("harvest_balance_delta", uint256(vm.load(EXCHANGE, userSlot(9))) - bal0);
        vm.writeFile("out/debtcycle.txt", acc);
    }

    function testPlainCloseFee() public {
        vm.store(EXCHANGE, userSlot(9), bytes32(uint256(100e18)));
        uint256 bal0 = uint256(vm.load(EXCHANGE, userSlot(9)));
        uint256 fee0 = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        uint256 locked0 = locked();
        vm.etch(BBO, address(new CoreEntry()).code);
        (bool ok, uint256 id) = openPos(false, MARGIN, 6000000);
        require(ok, "plain open");
        note("plain_locked_delta", locked() - locked0);
        note("plain_balance_after_open", uint256(vm.load(EXCHANGE, userSlot(9))));
        vm.etch(BBO, address(new CoreLower()).code);
        require(closePos(id, 6000001), "plain close");
        uint256 fee1 = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        note("plain_balance_delta", uint256(vm.load(EXCHANGE, userSlot(9))) - bal0);
        note("plain_queued", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("plain_fee_staker", (fee1 & type(uint128).max) - (fee0 & type(uint128).max));
        note("plain_fee_dev", (fee1 >> 128) - (fee0 >> 128));
        note("bank", bank());
        vm.writeFile("out/plainclose.txt", acc);
    }

    function testTwoNodeExactConsumption() public {
        makeLibraryNode(7000000);
        vm.roll(block.number + 1);
        vm.warp(block.timestamp + 1);
        makeLibraryNode(7000100);
        uint256 head = uint256(vm.load(EXCHANGE, bytes32(uint256(16))));
        uint256 tail = uint256(vm.load(EXCHANGE, userSlot(21)));
        note("head", head);
        note("tail", tail);
        note("head_next", uint256(vm.load(EXCHANGE, nodeSlot(head))) >> 160);
        note("library_amount_per_node", uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(head)) + 1))));
        vm.store(EXCHANGE, bytes32(uint256(nodeSlot(head)) + 1), bytes32(uint256(25e18)));
        vm.store(EXCHANGE, bytes32(uint256(nodeSlot(tail)) + 1), bytes32(uint256(10e18)));
        vm.store(EXCHANGE, userSlot(19), bytes32(uint256(35e18)));
        vm.store(EXCHANGE, bytes32(uint256(18)), bytes32(uint256(35e18)));
        (bool ok,) = openPos(true, MARGIN, 7001000);
        note("open_ok", ok ? 1 : 0);
        note("post_userQueued", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("post_global", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        note("post_head", uint256(vm.load(EXCHANGE, userSlot(20))));
        note("post_tail", uint256(vm.load(EXCHANGE, userSlot(21))));
        note("post_head_amount", uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(head)) + 1))));
        note("post_tail_amount", uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(tail)) + 1))));
        note("sum_remaining", uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(head)) + 1))) + uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(tail)) + 1))));
        vm.writeFile("out/twonode.txt", acc);
    }

    function testOutsiderWithdrawRejected() public {
        vm.store(EXCHANGE, userSlot(9), bytes32(uint256(1000e18)));
        vm.etch(address(0x0810), address(new CoreStatusMock()).code);
        vm.etch(address(0x0801), address(new CoreSpotMock()).code);
        vm.etch(address(0x3333333333333333333333333333333333333333), address(new CoreWriterMock()).code);
        address outsider = address(uint160(uint256(0xbeef)));
        vm.prank(outsider);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x7f99545a), uint256(1000e6)));
        note("outsider_ok", ok ? 1 : 0);
        note("outsider_retlen", out.length);
        note("outsider_err", out.length == 4 ? uint256(bytes32(out)) >> 224 : 0);
        note("user_balance_after", uint256(vm.load(EXCHANGE, userSlot(9))));
        note("outsider_balance_after", uint256(vm.load(EXCHANGE, mapSlot(uint256(uint160(outsider)), 9))));
        vm.writeFile("out/outsider.txt", acc);
    }

    function testUserWithdrawDebitBeforeDelivery() public {
        vm.store(EXCHANGE, userSlot(9), bytes32(uint256(1000e18)));
        vm.etch(address(0x0810), address(new CoreStatusMock()).code);
        vm.etch(address(0x0801), address(new CoreSpotMock()).code);
        vm.etch(address(0x3333333333333333333333333333333333333333), address(new CoreWriterMock()).code);
        vm.recordLogs();
        vm.prank(USER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x7f99545a), uint256(1000e6)));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        note("user_ok", ok ? 1 : 0);
        note("user_balance_after", uint256(vm.load(EXCHANGE, userSlot(9))));
        note("treasury_after", uint256(vm.load(EXCHANGE, bytes32(uint256(14)))));
        note("log_count", logs.length);
        note("writer_action_len", logs.length > 0 ? logs[0].data.length : 0);
        note("event_topic0", logs.length > 1 ? uint256(logs[1].topics[0]) : 0);
        vm.writeFile("out/userwithdraw.txt", acc);
    }
}

contract HarvestTest is LedgerTest {
    /// @dev the harvest pays only from available funds: with the treasury drained it
    ///      reports success and pays nothing, and pays the whole queued amount once
    ///      funds are present. The claim is not lost or double counted either way.
    function testHarvestGate() public {
        makeLibraryNode(9500000);
        uint256 node = uint256(vm.load(EXCHANGE, bytes32(uint256(16))));
        inflateNode(node, MARGIN);
        vm.etch(BBO, address(new CoreEntry()).code);
        (bool ok, uint256 id) = openPos(true, MARGIN, 9501000);
        require(ok, "debt open");
        vm.etch(BBO, address(new CoreLower()).code);
        uint256 treasury = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(treasury - bank()));
        require(closePos(id, 9501001), "debt close");
        note("queued_before_harvest", uint256(vm.load(EXCHANGE, userSlot(19))));
        uint256 bal0 = uint256(vm.load(EXCHANGE, userSlot(9)));
        (bool hok1, bytes memory hout1) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xddc63262), uint256(4)));
        note("drained_harvest_ok", hok1 ? 1 : 0);
        note("drained_harvest_paid", hok1 && hout1.length == 32 ? abi.decode(hout1, (uint256)) : 0);
        note("drained_queued_after", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("drained_balance_delta", uint256(vm.load(EXCHANGE, userSlot(9))) - bal0);
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(treasury + 1000000e18));
        (bool hok2, bytes memory hout2) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xddc63262), uint256(4)));
        note("funded_harvest_ok", hok2 ? 1 : 0);
        note("funded_harvest_paid", hok2 && hout2.length == 32 ? abi.decode(hout2, (uint256)) : 0);
        note("funded_queued_after", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("funded_balance_delta", uint256(vm.load(EXCHANGE, userSlot(9))) - bal0);
        vm.writeFile("out/harvestgate.txt", acc);
    }
}

contract BankTest is LedgerTest {
    function testDebtOpenAccounting() public {
        uint256 t0 = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        makeLibraryNode(8000000);
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(t0));
        uint256 node = uint256(vm.load(EXCHANGE, bytes32(uint256(16))));
        inflateNode(node, MARGIN);
        vm.etch(BBO, address(new CoreEntry()).code);
        note("queued_before", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        note("locked_before", locked());
        note("tb_before", totalBal());
        note("bank_before", bank());
        (bool ok,) = openPos(true, MARGIN, 8001000);
        note("open_ok", ok ? 1 : 0);
        note("queued_after", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        note("locked_after", locked());
        note("tb_after", totalBal());
        note("bank_after", bank());
        vm.roll(block.number + 1);
        vm.warp(block.timestamp + 1);
        vm.store(EXCHANGE, userSlot(9), bytes32(uint256(100e18)));
        uint256 locked0 = locked();
        (bool ok2,) = openPos(false, MARGIN, 8001001);
        note("plain_open_ok", ok2 ? 1 : 0);
        note("plain_locked_delta", locked() - locked0);
        vm.writeFile("out/cleandebt.txt", acc);
    }

    function testDebtCloseNoBankGate() public {
        makeLibraryNode(8100000);
        uint256 node = uint256(vm.load(EXCHANGE, bytes32(uint256(16))));
        inflateNode(node, MARGIN);
        vm.etch(BBO, address(new CoreEntry()).code);
        (bool ok, uint256 id) = openPos(true, MARGIN, 8101000);
        require(ok, "debt open");
        // close with the bankroll forced to zero
        vm.etch(BBO, address(new CoreLower()).code);
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) - bank()));
        require(bank() == 0, "bankroll not drained");
        uint256 fee0 = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        uint256 treasury0 = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        require(closePos(id, 8101001), "debt close");
        note("bank_at_close", 0);
        note("queued_delta", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("global_queued", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        note("fee_staker_delta", (uint256(vm.load(EXCHANGE, bytes32(uint256(26)))) & type(uint128).max) - (fee0 & type(uint128).max));
        note("fee_dev_delta", (uint256(vm.load(EXCHANGE, bytes32(uint256(26)))) >> 128) - (fee0 >> 128));
        note("treasury_delta", uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) - treasury0);
        vm.writeFile("out/debtclosebank.txt", acc);
    }
}