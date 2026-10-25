// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function etch(address, bytes calldata) external;
    function record() external;
    function accesses(address) external returns (bytes32[] memory reads, bytes32[] memory writes);
    function sign(uint256, bytes32) external returns (uint8, bytes32, bytes32);
    function addr(uint256) external returns (address);
    function writeLine(string calldata, string calldata) external;
    function snapshot() external returns (uint256);
    function revertTo(uint256) external returns (bool);
}

contract ProbeTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant BATCH = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant BBO = address(0x080e);
    bytes32 constant OPEN_TYPEHASH = 0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983;
    uint256 constant USER_KEY = 0xa11ce;
    uint256 constant PK = 0xb0b;
    uint256 constant INST = 1;
    uint256 constant WAD = 1e18;
    address USER;

    function u2s(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 t = v; uint256 d;
        while (t != 0) { d++; t /= 10; }
        bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }
    function hx(uint8 v) internal pure returns (bytes1) { return v < 10 ? bytes1(uint8(48 + v)) : bytes1(uint8(87 + v)); }
    function hexs(bytes memory d) internal pure returns (string memory) {
        bytes memory o = new bytes(d.length * 2);
        for (uint256 i; i < d.length; i++) { o[i*2] = hx(uint8(d[i]) >> 4); o[i*2+1] = hx(uint8(d[i]) & 0xf); }
        return string(o);
    }
    function hexw(bytes32 w) internal pure returns (string memory) { return string.concat("0x", hexs(abi.encodePacked(w))); }
    function errOf(bytes memory res) internal pure returns (string memory) {
        if (res.length < 4) return "none";
        uint256 v;
        for (uint256 i; i < 4; i++) v = (v << 8) | uint8(res[i]);
        bytes memory b = new bytes(8);
        for (uint256 i; i < 8; i++) b[i] = hx(uint8((v >> (4 * (7 - i))) & 0xf));
        return string.concat("0x", string(b));
    }
    function kv(string memory key, string memory value) internal {
        vm.writeLine("out/probe.json", string.concat("\"", key, "\":\"", value, "\""));
    }
    function emitN(string memory key, uint256 value) internal {
        vm.writeLine("out/probe.json", string.concat("\"", key, "\":\"", u2s(value), "\""));
    }

    function mockBbo(uint64 bid, uint64 ask) internal {
        vm.etch(BBO, abi.encodePacked(hex"7f", bytes32(uint256(bid)), hex"600052",
                                      hex"7f", bytes32(uint256(ask)), hex"602052", hex"60406000f3"));
    }
    function registerSession(uint256 pk) internal {
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(vm.addr(pk), outer)), bytes32(uint256(block.timestamp + 3600)));
    }
    function slotOf(uint256 key, uint256 base) internal pure returns (bytes32) { return keccak256(abi.encode(key, base)); }
    function userSlot(uint256 base) internal view returns (bytes32) { return keccak256(abi.encode(USER, base)); }

    function openDebt(uint256 size, uint32 leverage, uint64 nonce) internal returns (bool ok, bytes memory res, uint256 id) {
        registerSession(PK);
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(INST), true,
            uint128(size), leverage, true, nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", SESSION_DOMAIN(), structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, digest);
        vm.prank(BATCH);
        (ok, res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xec6783f0), USER, uint32(INST),
            true, uint128(size), leverage, true, nonce, deadline, v, r, s));
        id = uint256(vm.load(EXCHANGE, bytes32(uint256(11))));
        if (id > 0) id = id - 1;
    }
    function SESSION_DOMAIN() internal view returns (bytes32) {
        (bool ok, bytes memory res) = SESSION.staticcall(abi.encodeWithSelector(bytes4(0x3644e515)));
        require(ok && res.length == 32, "domain");
        return abi.decode(res, (bytes32));
    }

    function test_probe_fork_a() public {
        emitN("block", block.number);
        emitN("chainid", block.chainid);
        USER = vm.addr(USER_KEY);
        mockBbo(251080, 251090);
        // fixture: point the newest real queue node at the harness user
        uint256 nodeId = 3;
        uint256 amount = 7623942182351823589;
        vm.store(EXCHANGE, slotOf(nodeId, 15), bytes32(uint256(uint160(USER))));
        vm.store(EXCHANGE, userSlot(19), bytes32(amount));
        vm.store(EXCHANGE, userSlot(20), bytes32(nodeId));
        vm.store(EXCHANGE, userSlot(21), bytes32(nodeId));
        emitN("queued_before", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        emitN("user_queued_before", uint256(vm.load(EXCHANGE, userSlot(19))));
        emitN("user_bal_before", uint256(vm.load(EXCHANGE, userSlot(9))));
        emitN("locked_before", uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) >> 128);
        // market aggregate before
        bytes32 mroot = slotOf(INST, 36);
        kv("market_w0_before", hexw(vm.load(EXCHANGE, mroot)));
        // one storage-diff pass to learn the touched slots
        uint256 snap = vm.snapshot();
        vm.record();
        (bool ok, bytes memory res, uint256 id) = openDebt(1e18, 100, 1);
        (, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        kv("open_ok", ok ? "true" : "false");
        kv("open_err", errOf(res));
        kv("open_ret", hexs(res));
        emitN("open_writes", writes.length);
        string memory list = "";
        for (uint256 i; i < writes.length; i++) {
            list = string.concat(list, i == 0 ? "" : ";", hexw(writes[i]));
        }
        kv("write_slots", list);
        emitN("next_id_after", uint256(vm.load(EXCHANGE, bytes32(uint256(11)))));
        kv("market_w0_after", hexw(vm.load(EXCHANGE, mroot)));
        emitN("user_bal_after_open", uint256(vm.load(EXCHANGE, userSlot(9))));
        emitN("user_queued_after_open", uint256(vm.load(EXCHANGE, userSlot(19))));
        emitN("queued_after_open", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        emitN("locked_after_open", uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) >> 128);
        emitN("id", id);
        if (id != type(uint256).max) {
            kv("pos_w0", hexw(vm.load(EXCHANGE, slotOf(id, 10))));
            kv("pos_w1", hexw(vm.load(EXCHANGE, bytes32(uint256(slotOf(id, 10)) + 1))));
        }
        // before/after values for every touched slot, from a clean replay
        kv("diff_start", "");
        vm.revertTo(snap);
        bytes32[] memory before = new bytes32[](writes.length);
        for (uint256 i; i < writes.length; i++) before[i] = vm.load(EXCHANGE, writes[i]);
        snap = vm.snapshot();
        (bool ok2,,) = openDebt(1e18, 100, 1);
        kv("open_ok_replay", ok2 ? "true" : "false");
        for (uint256 i; i < writes.length; i++) {
            kv(string.concat("slot_", u2s(i)), string.concat(hexw(writes[i]), " before=", hexw(before[i]),
                 " after=", hexw(vm.load(EXCHANGE, writes[i]))));
        }
        vm.revertTo(snap);
        emitN("writes_count", writes.length);
    }
}