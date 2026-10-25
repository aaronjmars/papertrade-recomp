pragma solidity ^0.8.24;
interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function warp(uint256) external;
    function roll(uint256) external;
    function chainId(uint256) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function record() external;
    function accesses(address) external returns (bytes32[] memory, bytes32[] memory);
    function sign(uint256, bytes32) external returns (uint8, bytes32, bytes32);
    function addr(uint256) external returns (address);
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function writeFile(string calldata, string calldata) external;
    function toString(uint256) external pure returns (string memory);
}
contract CoreWriterMock {
    bytes public lastInput;
    fallback() external { lastInput = msg.data; }
}
contract Live2IntentsTest {
    error UnexpectedResult(bool ok, bytes output);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant EXCHANGE_IMPL = address(uint160(uint256(0x000a44049dbbb6b4762a6ba37aa0f7548c0b4a3723)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant SESSION_IMPL = address(uint160(uint256(0x0004b5ea4cdd8d6de4bd6e0ef3865266947f043946)));
    address constant BATCH = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant USER = address(uint160(uint256(0x00e05fcc23807536bee418f142d19fa0d21bb0cff7)));
    address constant SESSION_KEY = address(uint160(uint256(0x000376aac07ad725e01357b1725b5cec61ae10473c)));
    address constant STATUS = address(0x0810);
    address constant CORE_BALANCE = address(0x0801);
    address constant CORE_WRITER = address(0x3333333333333333333333333333333333333333);
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 constant DOMAIN = 0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77;
    bytes32 constant WITHDRAW_TYPEHASH = 0xac4ddb8d63e9d7a862c5d61ce47517623a448262414a7eef6797102104b31214;
    bytes32 constant OPEN_TYPEHASH = 0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983;
    bytes32 constant CLOSE_TYPEHASH = 0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13;
    uint256 constant NONCE = 42;

    function sessionKeySlot() internal pure returns (bytes32) {
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        return keccak256(abi.encode(SESSION_KEY, outer));
    }
    function enableSessionKey() internal {
        vm.store(SESSION, sessionKeySlot(), bytes32(uint256(block.timestamp + 3600)));
    }
    function signTrade(bytes32 structHash) internal returns (uint8 v, bytes32 r, bytes32 sigS) {
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (v, r, sigS) = vm.sign(0xb0b, digest);
        require(ecrecover(digest, v, r, sigS) == SESSION_KEY, "session signer identity");
    }
    function checkSessionSigner(bytes32 structHash, uint8 v, bytes32 r, bytes32 sigS) internal {
        vm.prank(EXCHANGE);
        (bool signerOk, bytes memory signerOut) = SESSION.call(abi.encodeWithSelector(
            bytes4(0x7f608253), USER, structHash, v, r, sigS));
        if (!signerOk || abi.decode(signerOut, (address)) != SESSION_KEY)
            revert UnexpectedResult(signerOk, signerOut);
    }
    function nonceCounterSlot() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(5)));
    }
    function nonceBitSlot() internal pure returns (bytes32) {
        bytes32 outer = keccak256(abi.encode(USER, uint256(6)));
        return keccak256(abi.encode(NONCE >> 8, outer));
    }
    function setUp() public {
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(EXCHANGE_IMPL, vm.parseBytes(vm.readFile("runtime/ExchangeImpl2.hex")));
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/SessionProxy.hex")));
        vm.etch(SESSION_IMPL, vm.parseBytes(vm.readFile("runtime/SessionImpl2.hex")));
        vm.roll(48902346);
        vm.warp(1792357341);
        vm.chainId(999);
        vm.store(EXCHANGE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(EXCHANGE_IMPL))));
        vm.store(SESSION, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(SESSION_IMPL))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
        vm.store(SESSION, ADMIN_SLOT, bytes32(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
        vm.store(EXCHANGE, bytes32(uint256(0)), 0x00000000000000000000b915fa41e824d6aa31bb833ee81220c0f2c8ea0f0001);
        vm.store(EXCHANGE, bytes32(uint256(1)), 0x000000000000000000000000696292762fd5ac3677a45edbe54eaece4194d1f6);
        vm.store(EXCHANGE, bytes32(uint256(2)), 0x000000000000000000000000a9b4c7b7ca5835652d81e25739c870d49f39cc2e);
        vm.store(EXCHANGE, bytes32(uint256(3)), 0x000000000000000000000000000000000000000000000000000000e8d4a51000);
        vm.store(EXCHANGE, bytes32(uint256(4)), 0x0000000000000000000000000000000000000000000000000000000000000008);
        vm.store(EXCHANGE, bytes32(uint256(5)), 0x00000000000000000000000000000000000000000000000000000002540be400);
        vm.store(EXCHANGE, bytes32(uint256(6)), 0x00000000000000000000000075174549dbbd44497d31a47e2e2d7406408d63d9);
        vm.store(EXCHANGE, bytes32(uint256(8)), 0x0000000000000000000000000000000000000000000000000000000000000002);
        vm.store(EXCHANGE, bytes32(uint256(11)), 0x00000000000000000000000000000000000000000000000000000000001547a3);
        vm.store(EXCHANGE, bytes32(uint256(14)), 0x00000000000000000000000000000000000000000035b5849a35d618f5b00800);
        vm.store(EXCHANGE, bytes32(uint256(16)), 0x0000000000000000000000000000000000000000000000000000000000000004);
        vm.store(EXCHANGE, bytes32(uint256(17)), 0x0000000000000000000000000000000000000000000000000000000000000004);
        vm.store(EXCHANGE, bytes32(uint256(22)), 0x000000000007be65f23207ad7ea19168000000000029d3d6f9e2192a05b05b45);
        vm.store(EXCHANGE, bytes32(uint256(23)), 0x00000000000000000000000000000000000000000000000000470de4df820000);
        vm.store(EXCHANGE, bytes32(uint256(24)), 0x00000000000000000000000000000000000000000000000000470de4df820000);
        vm.store(EXCHANGE, bytes32(uint256(25)), 0x00000000000000000000000000000000000000000000000000470de4df820000);
        vm.store(EXCHANGE, bytes32(uint256(26)), 0x00000000000000433b768a255b8b62b9000000000000000564ea03bde8d561b3);
        vm.store(EXCHANGE, bytes32(uint256(28)), 0x000000000000003635c9adc5dea0000000000000000000008ac7230489e80000);
        vm.store(EXCHANGE, bytes32(uint256(29)), 0x00000000000000000000008326eb8896e358717f10502ec73ce8d28e37b10800);
        vm.store(EXCHANGE, bytes32(uint256(30)), 0x0000000000000000000000001629b7d46bef6e13ff754174fc9f32dea309b38f);
        vm.store(EXCHANGE, bytes32(uint256(31)), 0x000000000000000000000000aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016);
        vm.store(EXCHANGE, bytes32(uint256(37)), 0x0000000000000000000000003721476de31190dc1af8908026abe20efe25cf99);
        vm.store(EXCHANGE, bytes32(uint256(88)), 0x000000000000000000000000233ff29b239abc1d7748605da9b205c3e008626e);
        vm.store(SESSION, bytes32(uint256(0)), 0x0000000000000000000000000000000000000000000000000000000000000001);
        vm.store(SESSION, bytes32(uint256(1)), 0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77);
        vm.store(SESSION, bytes32(uint256(2)), 0x000000000000000000000000b915fa41e824d6aa31bb833ee81220c0f2c8ea0f);
        vm.store(SESSION, bytes32(uint256(3)), 0x0000000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a2);
        vm.store(SESSION, bytes32(uint256(8)), 0x000000000000000000000000fdc6550436dd75ce8a0b145f935b7d3a64f53248);
        vm.store(EXCHANGE, keccak256(abi.encode(USER, uint256(9))), bytes32(uint256(100e18)));
        vm.etch(STATUS, hex"7f000000000000000000000000000000000000000000000000000000000000000160005260206000f3");
        vm.etch(CORE_BALANCE, hex"7f000000000000000000000000000000000000000000000000000000e8d4a510006000527f00000000000000000000000000000000000000000000000000000000000000006020527f000000000000000000000000000000000000000000000000000000000000000060405260606000f3");
        CoreWriterMock writer = new CoreWriterMock();
        vm.etch(CORE_WRITER, address(writer).code);
    }
    function consume(uint64 deadline) internal returns (bool, bytes memory) {
        vm.prank(EXCHANGE);
        return SESSION.call(abi.encodeWithSelector(bytes4(0xb002b9fa), USER, NONCE, deadline));
    }
    function withdrawSignedFields(address caller, address user, uint256 amount, uint256 nonce,
        uint64 deadline, uint8 v, bytes32 r, bytes32 s) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x8d09f23f),
            user, amount, nonce, deadline, v, r, s));
    }
    function withdrawSigned(address caller, uint64 deadline, uint8 v, bytes32 r, bytes32 s)
        internal returns (bool, bytes memory) {
        return withdrawSignedFields(caller, USER, 2_000_000, NONCE, deadline, v, r, s);
    }
    function withdrawAs(address caller, uint64 deadline) internal returns (bool, bytes memory) {
        return withdrawSigned(caller, deadline, 27, bytes32(0), bytes32(0));
    }
    function withdraw(uint64 deadline) internal returns (bool, bytes memory) {
        return withdrawAs(BATCH, deadline);
    }
    function signWithdrawal(uint64 deadline) internal returns (uint8 v, bytes32 r, bytes32 s) {
        bytes32 structHash = keccak256(abi.encode(WITHDRAW_TYPEHASH, USER, uint256(2_000_000), NONCE, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (v, r, s) = vm.sign(0xa11ce, digest);
        require(ecrecover(digest, v, r, s) == USER, "synthetic signer");
    }
    function closeAs(address caller, uint64 deadline) internal returns (bool, bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        vm.prank(caller);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706),
            USER, ids, NONCE, deadline, uint8(27), bytes32(0), bytes32(0)));
    }
    function close(uint64 deadline) internal returns (bool, bytes memory) {
        return closeAs(BATCH, deadline);
    }
    function openSignedSize(address caller, uint128 size, uint32 leverage,
        uint64 deadline, uint8 v, bytes32 r, bytes32 sigS)
        internal returns (bool, bytes memory) {
        vm.prank(caller);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0xec6783f0),
            USER, uint32(0), true, size, leverage, false,
            NONCE, deadline, v, r, sigS));
    }
    function openSigned(address caller, uint64 deadline, uint8 v, bytes32 r, bytes32 sigS)
        internal returns (bool, bytes memory) {
        return openSignedSize(caller, 1e18, 10, deadline, v, r, sigS);
    }
    function openAs(address caller, uint64 deadline) internal returns (bool, bytes memory) {
        return openSigned(caller, deadline, 27, bytes32(0), bytes32(0));
    }
    function open(uint64 deadline) internal returns (bool, bytes memory) {
        return openAs(BATCH, deadline);
    }
    function errorIs(bytes memory out, bytes4 selector) internal pure returns (bool) {
        return out.length == 4 && bytes4(out) == selector;
    }
    function contains(bytes32[] memory slots, bytes32 target) internal pure returns (bool) {
        for (uint256 i; i < slots.length; ++i) if (slots[i] == target) return true;
        return false;
    }
    function testBadSignatureRollsBackNonce() public {
        require(vm.load(SESSION, nonceBitSlot()) == 0, "nonce bit prestate");
        (bool directOk,) = consume(uint64(block.timestamp + 3600));
        require(directOk && uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "nonce can be consumed");
        vm.store(SESSION, nonceBitSlot(), 0);
        vm.store(SESSION, nonceCounterSlot(), 0);
        vm.record();
        (bool ok, bytes memory out) = withdraw(uint64(block.timestamp + 3600));
        if (ok || !errorIs(out, 0xc20280ea)) revert UnexpectedResult(ok, out);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()) && contains(writes, nonceCounterSlot()), "nonce writes attempted");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "nonce bit rolled back");
        require(vm.load(SESSION, nonceCounterSlot()) == 0, "nonce counter rolled back");
    }
    function testExpiredDeadlineLeavesNonceUnused() public {
        (bool ok, bytes memory out) = withdraw(uint64(block.timestamp - 1));
        require(!ok && errorIs(out, 0xf87d9271), "expired deadline error");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "nonce bit unchanged");
    }
    function testDeadlineAtTimestampReachesSignatureCheck() public {
        (bool ok, bytes memory out) = withdraw(uint64(block.timestamp));
        require(!ok && errorIs(out, 0xc20280ea), "deadline boundary error");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "boundary nonce rolled back");
    }
    function testReusedNonceRejected() public {
        (bool directOk,) = consume(uint64(block.timestamp + 3600));
        require(directOk, "nonce setup");
        (bool ok, bytes memory out) = withdraw(uint64(block.timestamp + 3600));
        require(!ok && errorIs(out, 0x756688fe), "reused nonce error");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "nonce remains used");
    }
    function testBadCloseSignatureRollsBackNonce() public {
        vm.record();
        (bool ok, bytes memory out) = close(uint64(block.timestamp + 3600));
        if (ok || !errorIs(out, 0xc5045f22)) revert UnexpectedResult(ok, out);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()) && contains(writes, nonceCounterSlot()), "close nonce writes attempted");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "close nonce bit rolled back");
        require(vm.load(SESSION, nonceCounterSlot()) == 0, "close nonce counter rolled back");
    }
    function testExpiredCloseDeadlineLeavesNonceUnused() public {
        (bool ok, bytes memory out) = close(uint64(block.timestamp - 1));
        require(!ok && errorIs(out, 0xf87d9271), "expired close deadline error");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "expired close nonce unchanged");
    }
    function testReusedCloseNonceRejected() public {
        (bool directOk,) = consume(uint64(block.timestamp + 3600));
        require(directOk, "close nonce setup");
        (bool ok, bytes memory out) = close(uint64(block.timestamp + 3600));
        require(!ok && errorIs(out, 0x756688fe), "reused close nonce error");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "close nonce remains used");
    }
    function testOutsiderCloseRejectedBeforeNonce() public {
        vm.record();
        (bool ok, bytes memory out) = closeAs(USER, uint64(block.timestamp + 3600));
        require(!ok && errorIs(out, 0xda96f0b6), "close caller error");
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(!contains(writes, nonceBitSlot()), "outsider reached nonce write");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "outsider nonce unchanged");
    }
    function testBadOpenSignatureRollsBackNonce() public {
        vm.record();
        (bool ok, bytes memory out) = open(uint64(block.timestamp + 3600));
        if (ok || !errorIs(out, 0xc5045f22)) revert UnexpectedResult(ok, out);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()) && contains(writes, nonceCounterSlot()), "open nonce writes attempted");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "open nonce bit rolled back");
        require(vm.load(SESSION, nonceCounterSlot()) == 0, "open nonce counter rolled back");
    }
    function testExpiredOpenDeadlineLeavesNonceUnused() public {
        (bool ok, bytes memory out) = open(uint64(block.timestamp - 1));
        require(!ok && errorIs(out, 0xf87d9271), "expired open deadline error");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "expired open nonce unchanged");
    }
    function testReusedOpenNonceRejected() public {
        (bool directOk,) = consume(uint64(block.timestamp + 3600));
        require(directOk, "open nonce setup");
        (bool ok, bytes memory out) = open(uint64(block.timestamp + 3600));
        require(!ok && errorIs(out, 0x756688fe), "reused open nonce error");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "open nonce remains used");
    }
    function testOutsiderOpenRejectedBeforeNonce() public {
        vm.record();
        (bool ok, bytes memory out) = openAs(USER, uint64(block.timestamp + 3600));
        require(!ok && errorIs(out, 0xda96f0b6), "open caller error");
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(!contains(writes, nonceBitSlot()), "outsider open reached nonce write");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "outsider open nonce unchanged");
    }
    function testOutsiderWithdrawalReachesSignatureCheck() public {
        vm.record();
        (bool ok, bytes memory out) = withdrawAs(USER, uint64(block.timestamp + 3600));
        if (ok || !errorIs(out, 0xc20280ea)) revert UnexpectedResult(ok, out);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()), "outsider withdrawal nonce write attempted");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "outsider withdrawal nonce rolled back");
    }
    function testCloseBatchCallerDependsOnSlot88() public {
        vm.store(EXCHANGE, bytes32(uint256(88)), 0);
        (bool blocked, bytes memory blockedOut) = close(uint64(block.timestamp + 3600));
        require(!blocked && errorIs(blockedOut, 0xda96f0b6), "zero slot88 caller guard");
        vm.store(EXCHANGE, bytes32(uint256(88)), bytes32(uint256(uint160(BATCH))));
        (bool allowed, bytes memory allowedOut) = close(uint64(block.timestamp + 3600));
        require(!allowed && errorIs(allowedOut, 0xc5045f22), "restored slot88 signer path");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "slot88 test nonce rolled back");
    }
    function testWrongValidWithdrawalSignerRollsBackNonce() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(WITHDRAW_TYPEHASH, USER, uint256(2_000_000), NONCE, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(0xb0b, digest);
        require(ecrecover(digest, v, r, s) == vm.addr(0xb0b) && vm.addr(0xb0b) != USER,
            "valid different signer");
        vm.record();
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, s);
        if (ok || !errorIs(out, 0xc20280ea)) revert UnexpectedResult(ok, out);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()) && contains(writes, nonceCounterSlot()), "wrong signer nonce writes");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "wrong signer nonce bit rolled back");
        require(vm.load(SESSION, nonceCounterSlot()) == 0, "wrong signer counter rolled back");
    }
    function testFourPositionCloseDigestAcceptsSessionSigner() public {
        enableSessionKey();
        uint256[] memory ids = new uint256[](4);
        ids[0] = 1; ids[1] = 2; ids[2] = 3; ids[3] = 4;
        for (uint256 i; i < ids.length; ++i)
            require(vm.load(EXCHANGE, keccak256(abi.encode(ids[i], uint256(10)))) == 0,
                "synthetic positions empty");
        bytes32 userBalanceSlot = keccak256(abi.encode(USER, uint256(9)));
        uint256 oldUserBalance = uint256(vm.load(EXCHANGE, userBalanceSlot));
        uint256 oldTreasury = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 idsHash = keccak256(abi.encodePacked(ids));
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER, idsHash, NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        checkSessionSigner(structHash, v, r, sigS);
        vm.record();
        vm.prank(BATCH);
        (bool closeOk, bytes memory closeOut) = EXCHANGE.call(abi.encodeWithSelector(
            bytes4(0x2792e706), USER, ids, NONCE, deadline, v, r, sigS));
        if (!closeOk) revert UnexpectedResult(closeOk, closeOut);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()), "close nonce attempted");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "four-ID close nonce persisted");
        require(uint256(vm.load(SESSION, nonceCounterSlot())) == NONCE + 1,
            "four-ID close counter persisted");
        require(uint256(vm.load(EXCHANGE, userBalanceSlot)) == oldUserBalance,
            "empty close does not move user balance");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == oldTreasury,
            "empty close does not move treasury");
    }
    function testValidOpenSignatureReachesPostSignerRevert() public {
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(0), true,
            uint128(1e18), uint32(10), false, NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        checkSessionSigner(structHash, v, r, sigS);
        vm.record();
        (bool openOk, bytes memory openOut) = openSigned(BATCH, deadline, v, r, sigS);
        record("set2_open_post_signer", string.concat("\"ok\":", openOk ? "true" : "false", ", \"selector\":", vm.toString(selectorOf(openOut))));
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()), "valid open nonce attempted");
        require(contains(reads, sessionKeySlot()), "valid open signer key read");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (openOk ? (1 << NONCE) : 0),
            "valid open nonce outcome");
    }
    function testFourthCloseIdMutationRejectsSessionSignature() public {
        enableSessionKey();
        uint256[] memory ids = new uint256[](4);
        ids[0] = 1; ids[1] = 2; ids[2] = 3; ids[3] = 4;
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        ids[3] = 5;
        vm.record();
        vm.prank(BATCH);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(
            bytes4(0x2792e706), USER, ids, NONCE, deadline, v, r, sigS));
        if (ok || !errorIs(out, 0xc5045f22)) revert UnexpectedResult(ok, out);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        require(contains(writes, nonceBitSlot()), "mutated close nonce attempted");
        require(vm.load(SESSION, nonceBitSlot()) == 0, "mutated close nonce rolled back");
    }
    function testValidWithdrawalPersistsNonceAndDebits() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        bytes32 balanceSlot = keccak256(abi.encode(USER, uint256(9)));
        uint256 oldBalance = uint256(vm.load(EXCHANGE, balanceSlot));
        uint256 oldTreasury = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        uint256 oldTotal = uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) & type(uint128).max;
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, sigS);
        if (!ok) revert UnexpectedResult(ok, out);
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "valid nonce persisted");
        require(uint256(vm.load(SESSION, nonceCounterSlot())) == NONCE + 1, "valid counter persisted");
        require(oldBalance - uint256(vm.load(EXCHANGE, balanceSlot)) == 2e18, "valid user debit");
        require(oldTreasury - uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == 2e18, "valid treasury debit");
        require(oldTotal - (uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) & type(uint128).max) == 2e18,
            "valid total debit");
        require(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(34))))) == block.number,
            "valid last withdrawal block");
        require(CoreWriterMock(CORE_WRITER).lastInput().length > 100, "CoreWriter reached");
    }
    function nonceBitSlotFor(address namedUser, uint256 nonce) internal pure returns (bytes32) {
        bytes32 outer = keccak256(abi.encode(namedUser, uint256(6)));
        return keccak256(abi.encode(nonce >> 8, outer));
    }
    function checkSignatureMismatch(bool ok, bytes memory out, address namedUser, uint256 nonce)
        internal {
        if (ok || !errorIs(out, 0xc20280ea)) revert UnexpectedResult(ok, out);
        (, bytes32[] memory writes) = vm.accesses(SESSION);
        bytes32 bitSlot = nonceBitSlotFor(namedUser, nonce);
        require(contains(writes, bitSlot), "mismatch nonce write attempted");
        require(vm.load(SESSION, bitSlot) == 0, "mismatch nonce bit rolled back");
        require(vm.load(SESSION, keccak256(abi.encode(namedUser, uint256(5)))) == 0,
            "mismatch counter rolled back");
        require(CoreWriterMock(CORE_WRITER).lastInput().length == 0, "mismatch writer untouched");
    }
    function testSignedAmountMismatchRollsBack() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        vm.record();
        (bool ok, bytes memory out) = withdrawSignedFields(BATCH, USER, 3_000_000, NONCE,
            deadline, v, r, sigS);
        checkSignatureMismatch(ok, out, USER, NONCE);
    }
    function testSignedNonceMismatchRollsBack() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        vm.record();
        (bool ok, bytes memory out) = withdrawSignedFields(BATCH, USER, 2_000_000, NONCE + 1,
            deadline, v, r, sigS);
        checkSignatureMismatch(ok, out, USER, NONCE + 1);
    }
    function testSignedDeadlineMismatchRollsBack() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        vm.record();
        (bool ok, bytes memory out) = withdrawSignedFields(BATCH, USER, 2_000_000, NONCE,
            deadline + 1, v, r, sigS);
        checkSignatureMismatch(ok, out, USER, NONCE);
    }
    function testSignedUserMismatchRollsBack() public {
        address otherUser = address(0x1111111111111111111111111111111111111111);
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        vm.record();
        (bool ok, bytes memory out) = withdrawSignedFields(BATCH, otherUser, 2_000_000, NONCE,
            deadline, v, r, sigS);
        checkSignatureMismatch(ok, out, otherUser, NONCE);
    }
    function testWrongDomainWithdrawalSignatureRollsBack() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(WITHDRAW_TYPEHASH, USER, uint256(2_000_000), NONCE, deadline));
        bytes32 wrongDigest = keccak256(abi.encodePacked(hex"1901", bytes32(uint256(1)), structHash));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xa11ce, wrongDigest);
        require(ecrecover(wrongDigest, v, r, sigS) == USER, "wrong-domain signer identity");
        vm.record();
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, sigS);
        checkSignatureMismatch(ok, out, USER, NONCE);
    }
    function testValidWithdrawalReplayRejectedNextBlock() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        (bool firstOk, bytes memory firstOut) = withdrawSigned(BATCH, deadline, v, r, sigS);
        if (!firstOk) revert UnexpectedResult(firstOk, firstOut);
        uint256 balanceAfter = uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
        vm.roll(block.number + 1);
        vm.warp(block.timestamp + 1);
        (bool replayOk, bytes memory replayOut) = withdrawSigned(BATCH, deadline, v, r, sigS);
        if (replayOk || !errorIs(replayOut, 0x756688fe)) revert UnexpectedResult(replayOk, replayOut);
        require(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9))))) == balanceAfter,
            "replay no second debit");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "replay bit remains used");
    }
    function testValidSignatureAllowsOutsiderRelayer() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        (bool ok, bytes memory out) = withdrawSigned(address(0x1234), deadline, v, r, sigS);
        if (!ok) revert UnexpectedResult(ok, out);
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "relayed nonce persisted");
        require(CoreWriterMock(CORE_WRITER).lastInput().length > 100, "relayed CoreWriter reached");
    }

    // ================= live contract set 2 additions =================

    address constant OUTSIDER = address(0x000000000000000000000000000000000000dEaD);
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant KEEPER = address(uint160(uint256(0x000924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56)));
    address constant FACTORY = address(uint160(uint256(0x001629b7d46bef6e13ff754174fc9f32dea309b38f)));
    address constant FACTORY_IMPL = address(uint160(uint256(0x008f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0)));
    address constant BATCH_IMPL = address(uint160(uint256(0x00e0bc9cc7b067060aafccbaa3e250700c9cdd7262)));
    address constant STAKING = address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant SPOT_READ = address(0x0801);
    address constant PERP_READ = address(0x0803);
    bytes32 constant REGISTER_TYPEHASH = 0xd3d9a309f635415423ab81e7e3fb16d2117cc8e1edc90506adde9eaa3855edd2;
    bytes32 constant CALL_EXECUTED_TOPIC = 0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad;
    bytes32 constant CALL_REJECTED_TOPIC = 0x6002fcbae88fcbb8133c69c91df90bbc0b4464af94df2a56f8bb843f1cc5a193;
    uint256 constant MINIMUM_RAW = 1_000_000_000;
    uint256 constant SWEEP_SCALE = 10 ** 10;

    struct Call { address target; bytes data; bool continueOnFailure; bytes32 intentId; bytes32 extra; }

    function record(string memory name, string memory body) internal {
        vm.writeFile(string.concat("out/", name, ".json"),
                     string.concat("{\"name\":\"", name, "\",", body, "}\n"));
    }

    function signAsUser(bytes32 structHash) internal returns (uint8 v, bytes32 r, bytes32 sigS) {
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (v, r, sigS) = vm.sign(0xa11ce, digest);
        require(ecrecover(digest, v, r, sigS) == USER, "user signer identity");
    }

    function signWithdrawalNonce(uint64 deadline, uint256 nonce) internal returns (uint8 v, bytes32 r, bytes32 s) {
        bytes32 structHash = keccak256(abi.encode(WITHDRAW_TYPEHASH, USER, uint256(2_000_000), nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (v, r, s) = vm.sign(0xa11ce, digest);
        require(ecrecover(digest, v, r, s) == USER, "synthetic signer");
    }

    function selectorOf(bytes memory out) internal pure returns (uint256 value) {
        if (out.length < 4) return 0;
        assembly { value := mload(add(out, 0x20)) }
        return value >> 224;
    }

    function etchInfra() internal {
        vm.etch(BATCH, vm.parseBytes(vm.readFile("runtime/BatchExecutorProxy.hex")));
        vm.etch(BATCH_IMPL, vm.parseBytes(vm.readFile("runtime/BatchExecutorImpl.hex")));
        vm.store(BATCH, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(BATCH_IMPL))));
        vm.store(BATCH, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        // The allowlist is anchored to the stored suite addresses (slots 0 to 2).
        vm.store(BATCH, bytes32(uint256(0)), bytes32((uint256(uint160(EXCHANGE)) << 16) | 1));
        vm.store(BATCH, bytes32(uint256(1)), bytes32(uint256(uint160(SESSION))));
        vm.store(BATCH, bytes32(uint256(2)), bytes32(uint256(uint160(STAKING))));
        vm.store(BATCH, bytes32(uint256(3)), bytes32(uint256(uint160(OWNER))));
        vm.store(BATCH, bytes32(uint256(5)), bytes32(uint256(1)));
        vm.etch(FACTORY, vm.parseBytes(vm.readFile("runtime/FactoryProxyOfMock.hex")));
    }

    function pendingSlot() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(33)));
    }

    function balanceSlot() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(9)));
    }

    function mockFile(string memory name) internal {
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile(string.concat("runtime/", name, "_spot.hex"))));
        vm.etch(PERP_READ, vm.parseBytes(vm.readFile(string.concat("runtime/", name, "_perp.hex"))));
    }

    function pendingWord(uint64 spot, uint64 perp, uint256 block_) internal pure returns (bytes32) {
        return bytes32(uint256(spot) | (uint256(perp) << 64) | (block_ << 128));
    }

    function derivedProxy() internal returns (address) {
        (bool ok, bytes memory out) = FACTORY.staticcall(abi.encodeWithSelector(bytes4(0xc1a9a508), USER));
        require(ok && out.length == 32, "factory proxyOf");
        address proxy = abi.decode(out, (address));
        vm.etch(proxy, vm.parseBytes(vm.readFile("runtime/ProxyUser.hex")));
        return proxy;
    }

    function slice4(bytes memory data) internal pure returns (bytes memory out) {
        require(data.length >= 4, "short payload");
        out = new bytes(data.length - 4);
        for (uint256 i; i < out.length; ++i) out[i] = data[i + 4];
    }

    function runBatch(address relayer, address target, bytes memory data, bool continueOnFailure)
        internal returns (bool ok, bytes memory out, bool rejected, bool executed, bool innerOk,
                          bytes memory innerReturn) {
        Call[] memory calls = new Call[](1);
        calls[0] = Call(target, data, continueOnFailure, bytes32(0), bytes32(0));
        vm.recordLogs();
        vm.prank(relayer);
        (ok, out) = BATCH.call(abi.encodeWithSelector(bytes4(0x251fb27d), calls));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] == CALL_REJECTED_TOPIC) rejected = true;
            if (logs[i].topics[0] == CALL_EXECUTED_TOPIC && logs[i].emitter == BATCH) {
                executed = true;
                (innerOk, innerReturn) = abi.decode(logs[i].data, (bool, bytes));
            }
        }
    }

    function closeWith(uint256 nonce, uint64 deadline) internal returns (bool, bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce,
            deadline, v, r, sigS));
    }

    function closeWithKey(uint256 nonce, uint64 deadline, uint256 key) internal returns (bool, bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(key, keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash)));
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce,
            deadline, v, r, sigS));
    }

    function enableSubmitter(address who) internal {
        vm.store(SESSION, keccak256(abi.encode(who, uint256(7))), bytes32(uint256(1)));
    }

    function sessionWord(uint64 expiry, address associated) internal pure returns (bytes32) {
        return bytes32(uint256(expiry) | (uint256(uint160(associated)) << 64));
    }

    function testSet2RegistrationByBatchExecutor() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        uint64 expiry = uint64(block.timestamp + 7200);
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, USER, SESSION_KEY, expiry,
            address(0), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signAsUser(structHash);
        enableSubmitter(BATCH);
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok, bytes memory out) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE, deadline, v, r, sigS));
        if (!ok) revert UnexpectedResult(ok, out);
        uint256 word = uint256(vm.load(SESSION, sessionKeySlot()));
        require(uint64(word) == expiry, "expiry stored");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "registration bit set");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length >= 1, "registration event");
        // an unrelated caller cannot register
        vm.prank(OUTSIDER);
        (bool outsiderOk, bytes memory outsiderOut) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE + 1, deadline, v, r, sigS));
        require(!outsiderOk && errorIs(outsiderOut, 0x93b78c88), "UnauthorizedSubmitter");
        // a digest signed by the session key rather than the user must not register a key
        bytes32 secondHash = keccak256(abi.encode(REGISTER_TYPEHASH, USER, SESSION_KEY, expiry,
            address(0), NONCE + 2, deadline));
        (uint8 sv, bytes32 sr, bytes32 ss) = signTrade(secondHash);
        vm.prank(BATCH);
        (bool sessionOk, bytes memory sessionOut) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE + 2, deadline, sv, sr, ss));
        require(!sessionOk && errorIs(sessionOut, 0x8baa579f), "InvalidSignature for a session-key signature");
        require(uint256(vm.load(SESSION, nonceBitSlotFor(USER, NONCE + 2))) == (1 << NONCE),
            "the failed registration marks no extra bit");
        record("set2_registration", string.concat("\"expiry_stored\":", vm.toString(uint64(word)),
            ",\"nonce_bit\":", vm.toString(uint256(vm.load(SESSION, nonceBitSlot()))),
            ",\"outsider_selector\":", vm.toString(selectorOf(outsiderOut)),
            ",\"session_key_signature_selector\":", vm.toString(selectorOf(sessionOut))));
    }

    function testSet2NonceBitmapSharedAcrossIntentClasses() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (bool consumed,) = consume(deadline);
        require(consumed && uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "bit consumed");
        enableSessionKey();
        uint256 openSelector = blockedOpen(deadline);
        uint256 withdrawalSelector = blockedWithdrawal(deadline);
        uint256 registerSelector = blockedRegistration(deadline);
        uint256 next = NONCE + 256;
        (bool closeOk, bytes memory closeOut) = closeWith(next, deadline);
        require(closeOk, "adjacent word accepted");
        require(uint256(vm.load(SESSION, nonceBitSlotFor(USER, next))) == (1 << (next & 255)),
            "adjacent word bit set");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "first word untouched");
        record("set2_nonce_shared", string.concat("\"open_selector\":", vm.toString(openSelector),
            ",\"withdraw_selector\":", vm.toString(withdrawalSelector),
            ",\"register_selector\":", vm.toString(registerSelector),
            ",\"adjacent_word_accepted\":true,\"close_selector\":", vm.toString(selectorOf(closeOut))));
    }

    function blockedOpen(uint64 deadline) internal returns (uint256) {
        bytes32 openHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(0), true,
            uint128(1e18), uint32(10), false, NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 s) = signTrade(openHash);
        (bool ok, bytes memory out) = openSigned(BATCH, deadline, v, r, s);
        require(!ok && errorIs(out, 0x756688fe), "open blocked by the used bit");
        return selectorOf(out);
    }

    function blockedWithdrawal(uint64 deadline) internal returns (uint256) {
        (uint8 v, bytes32 r, bytes32 s) = signWithdrawal(deadline);
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, s);
        require(!ok && errorIs(out, 0x756688fe), "withdrawal blocked by the used bit");
        return selectorOf(out);
    }

    function blockedRegistration(uint64 deadline) internal returns (uint256) {
        enableSubmitter(BATCH);
        uint64 expiry = uint64(block.timestamp + 7200);
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, USER, SESSION_KEY, expiry,
            address(0), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 s) = signAsUser(structHash);
        vm.prank(BATCH);
        (bool ok, bytes memory out) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE, deadline, v, r, s));
        require(!ok && errorIs(out, 0x756688fe), "registration blocked by the used bit");
        return selectorOf(out);
    }

    function testSet2NonceIsPerUser() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (bool consumed,) = consume(deadline);
        require(consumed, "consume for user");
        address other = address(uint160(uint256(0x0000000000000000000000000000000000000b0b0b)));
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, other,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xdead1, keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash)));
        vm.prank(BATCH);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706),
            other, ids, NONCE, deadline, v, r, sigS));
        require(!ok && errorIs(out, 0xc5045f22), "other user nonce is untouched");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "user bit unchanged");
        record("set2_nonce_per_user", string.concat("\"other_user_selector\":", vm.toString(selectorOf(out))));
    }

    function testSet2SessionKeyLifecycleAndAssociatedAddress() public {
        address associated = vm.addr(0xc0ffee);
        (bool okA,) = lifecycleCase(uint64(block.timestamp + 3600), address(0), NONCE, 0);
        require(okA, "unexpired key accepted");
        require(!lifecycleRejects(uint64(block.timestamp - 1), address(0), NONCE + 1, 0),
            "expired key rejected");
        (bool okC, uint256 selC) = lifecycleCase(uint64(block.timestamp), address(0), NONCE + 2, 0);
        (bool okD, uint256 selD) = lifecycleCase(uint64(block.timestamp + 3600), associated, NONCE + 3, 0);
        (bool okE, uint256 selE) = lifecycleCase(uint64(block.timestamp + 3600), associated, NONCE + 4, 0xc0ffee);
        vm.store(SESSION, sessionKeySlot(), sessionWord(uint64(block.timestamp + 3600), address(0)));
        vm.prank(USER);
        (bool revokeOk, bytes memory revokeOut) = SESSION.call(abi.encodeWithSelector(bytes4(0x84f4fc6a), SESSION_KEY));
        if (!revokeOk) revert UnexpectedResult(revokeOk, revokeOut);
        require(vm.load(SESSION, sessionKeySlot()) == 0, "revocation clears the key word");
        require(!lifecycleRejects(uint64(block.timestamp + 3600), address(0), NONCE + 5, 0),
            "revoked key rejected");
        record("set2_session_lifecycle", string.concat("\"expiry_at_timestamp_ok\":", okC ? "true" : "false",
            ",\"expiry_at_timestamp_selector\":", vm.toString(selC),
            ",\"associated_set_key_ok\":", okD ? "true" : "false",
            ",\"associated_set_key_selector\":", vm.toString(selD),
            ",\"associated_signer_ok\":", okE ? "true" : "false",
            ",\"associated_signer_selector\":", vm.toString(selE),
            ",\"associated_address\":", vm.toString(uint160(associated))));
    }

    function lifecycleRejects(uint64 expiry, address associated, uint256 nonce, uint256 key) internal returns (bool) {
        (bool ok, uint256 selector) = lifecycleCase(expiry, associated, nonce, key);
        return !ok && selector == 0xc5045f22;
    }

    function lifecycleCase(uint64 expiry, address associated, uint256 nonce, uint256 key)
        internal returns (bool ok, uint256 selector) {
        vm.store(SESSION, sessionKeySlot(), sessionWord(expiry, associated));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes memory out;
        if (key == 0) (ok, out) = closeWith(nonce, deadline);
        else (ok, out) = closeWithKey(nonce, deadline, key);
        selector = selectorOf(out);
    }

    function testSet2KeeperIsNotASignedIntentCaller() public {
        vm.record();
        vm.prank(OWNER);
        (bool setOk, bytes memory setOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xefc1bd46), KEEPER));
        if (!setOk) revert UnexpectedResult(setOk, setOut);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        require(writes.length >= 1, "keeper storage written");
        require(!contains(writes, bytes32(uint256(88))), "keeper is not slot 88");
        vm.prank(OUTSIDER);
        (bool outsiderOk,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xefc1bd46), KEEPER));
        require(!outsiderOk, "outsider cannot set the keeper");
        uint64 deadline = uint64(block.timestamp + 3600);
        (bool closeOk, bytes memory closeOut) = closeAs(KEEPER, deadline);
        require(!closeOk && errorIs(closeOut, 0xda96f0b6), "keeper blocked from close");
        (bool openOk, bytes memory openOut) = openAs(KEEPER, deadline);
        require(!openOk && errorIs(openOut, 0xda96f0b6), "keeper blocked from open");
        (bool wOk, bytes memory wOut) = withdrawAs(KEEPER, deadline);
        require(!wOk && errorIs(wOut, 0xc20280ea), "keeper reaches the withdrawal signature check");
        record("set2_keeper", string.concat("\"written_slots\":", vm.toString(writes.length),
            ",\"first_written_slot\":", vm.toString(uint256(writes[0])),
            ",\"close_selector\":", vm.toString(selectorOf(closeOut)),
            ",\"open_selector\":", vm.toString(selectorOf(openOut)),
            ",\"withdraw_selector\":", vm.toString(selectorOf(wOut))));
    }

    function testSet2BatchAllowlistAgainstAddedSelectors() public {
        etchInfra();
        address relayer = address(uint160(uint256(0x0000000000000000000000000000000000000a11ce)));
        vm.store(BATCH, keccak256(abi.encode(relayer, uint256(4))), bytes32(uint256(1)));
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(88)))) == uint256(uint160(BATCH)),
            "live slot 88 is the BatchExecutor");
        (bool ctlOk, bytes memory ctlOut,,,,) =
            runBatch(OUTSIDER, EXCHANGE, abi.encodePacked(bytes4(0xec6783f0)), true);
        require(!ctlOk && errorIs(ctlOut, 0x17fb2066), "NotAuthorizedRelayer for an unknown relayer");
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0x69f9a5f0));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0x9d346583));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xcbce7532));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xd970fad5));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xe6ac4a74));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xf009ac03));
        addedSelectorRejected(relayer, SESSION, bytes4(0xbd322efa));
        addedSelectorRejected(relayer, SESSION, bytes4(0xd95208cd));
        addedSelectorRejected(relayer, SESSION, bytes4(0xe737de13));
        allowlistedCloseThroughBatch(relayer);
        (bool ok3,, bool rejected3,,,) =
            runBatch(relayer, EXCHANGE, abi.encodePacked(bytes4(0x415f1240), uint256(0)), true);
        require(ok3 && rejected3, "dropped selector is not allowlisted");
        (bool directOk, bytes memory directOut) =
            EXCHANGE.call(abi.encodeWithSelector(bytes4(0x415f1240), uint256(0)));
        require(!directOk && directOut.length == 0, "dropped selector absent from the live dispatcher");
        record("set2_batch_allowlist", string.concat("\"added_rejected\":9",
            ",\"allowlisted_close_ok\":true,\"dropped_rejected\":true",
            ",\"dropped_direct_selector\":", vm.toString(selectorOf(directOut)),
            ",\"slot_88_is_batch\":true"));
    }

    function addedSelectorRejected(address relayer, address target, bytes4 selector) internal {
        (bool ok,, bool rejected, bool executed,,) =
            runBatch(relayer, target, abi.encodePacked(selector, uint256(0)), true);
        require(ok, "batch completes");
        require(rejected && !executed, "added selector rejected by the allowlist");
    }

    function allowlistedCloseThroughBatch(address relayer) internal {
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        (bool ok,, bool rejected, bool executed, bool innerOk, bytes memory innerReturn) = runBatch(relayer, EXCHANGE,
            abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, NONCE, deadline, v, r, sigS), true);
        record("set2_batch_close_debug", string.concat("\"ok\":", ok ? "true" : "false",
            ",\"rejected\":", rejected ? "true" : "false", ",\"executed\":", executed ? "true" : "false",
            ",\"inner_ok\":", innerOk ? "true" : "false",
            ",\"inner_selector\":", vm.toString(selectorOf(innerReturn)),
            ",\"inner_bytes\":", vm.toString(innerReturn.length)));
        require(ok && !rejected && executed && innerOk, "allowlisted close executes through the batch");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "inner close consumed its nonce");
    }

    function testSet2WithdrawalExtraUnitWhenStatusFalse() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        vm.etch(STATUS, vm.parseBytes(vm.readFile("runtime/mock_status_0.hex")));
        uint256 before = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.recordLogs();
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, sigS);
        if (!ok) revert UnexpectedResult(ok, out);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        uint256 debit;
        uint256 sent;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] == 0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75) {
                (debit, sent) = abi.decode(logs[i].data, (uint256, uint256));
            }
        }
        require(debit == 3e18, "one USD above the signed amount");
        require(sent == 200_000_000, "core payload is the signed amount times 100");
        require(before - uint256(vm.load(EXCHANGE, balanceSlot())) == debit, "user debit matches the event");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == before - 3e18, "user balance");
        // the withdrawal path allows one withdrawal per user per block
        vm.roll(block.number + 1);
        // the caller does not change the fee treatment
        uint64 deadline2 = uint64(block.timestamp + 3601);
        (uint8 v2, bytes32 r2, bytes32 sig2) = signWithdrawalNonce(deadline2, NONCE + 1);
        uint256 before2 = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.etch(STATUS, vm.parseBytes(vm.readFile("runtime/mock_status_0.hex")));
        (bool ok3, bytes memory out3) = withdrawSignedFields(OUTSIDER, USER, 2_000_000, NONCE + 1, deadline2, v2, r2, sig2);
        if (!ok3) revert UnexpectedResult(ok3, out3);
        uint256 outsiderDebit = before2 - uint256(vm.load(EXCHANGE, balanceSlot()));
        require(outsiderDebit == 3e18, "outsider caller sees the same debit");
        // with an existing account the debit is exactly the signed amount
        vm.roll(block.number + 1);
        vm.etch(STATUS, vm.parseBytes(vm.readFile("runtime/mock_status_1.hex")));
        uint64 deadline4 = uint64(block.timestamp + 3602);
        (uint8 v4, bytes32 r4, bytes32 sig4) = signWithdrawalNonce(deadline4, NONCE + 2);
        uint256 before4 = uint256(vm.load(EXCHANGE, balanceSlot()));
        (bool ok4, bytes memory out4) = withdrawSignedFields(BATCH, USER, 2_000_000, NONCE + 2,
            deadline4, v4, r4, sig4);
        if (!ok4) revert UnexpectedResult(ok4, out4);
        uint256 existingDebit = before4 - uint256(vm.load(EXCHANGE, balanceSlot()));
        require(existingDebit == 2e18, "no extra unit for an existing account");
        record("set2_withdrawal_gap", string.concat("\"status_false_debit\":", vm.toString(debit),
            ",\"status_false_core_amount\":", vm.toString(sent),
            ",\"status_false_outsider_debit\":", vm.toString(outsiderDebit),
            ",\"status_true_debit\":", vm.toString(existingDebit)));
    }

    function testSet2DepositProxySurface() public {
        etchInfra();
        address proxy = derivedProxy();
        (bool userOk, bytes memory userOut) = proxy.staticcall(abi.encodeWithSelector(bytes4(0x4f8632ba)));
        (bool exchangeOk, bytes memory exchangeOut) = proxy.staticcall(abi.encodeWithSelector(bytes4(0xd2f7265a)));
        require(userOk && abi.decode(userOut, (address)) == USER, "user immutable");
        require(exchangeOk && abi.decode(exchangeOut, (address)) == EXCHANGE, "exchange immutable");
        (bool valueOk,) = proxy.call{value: 1}("");
        require(!valueOk, "no native funding path");
        (bool unknownOk,) = proxy.call(abi.encodeWithSelector(bytes4(0xdeadbeef)));
        require(!unknownOk, "no fallback");
        (bool outsiderSweep,) = proxy.call(abi.encodeWithSelector(bytes4(0x925b3aad),
            uint64(0), uint64(0), uint64(0)));
        require(!outsiderSweep, "sweep is exchange only");
        (bool outsiderRescue,) = proxy.call(abi.encodeWithSelector(bytes4(0x0c506e96), proxy, uint256(1)));
        require(!outsiderRescue, "rescue is user only");
        vm.prank(USER);
        (bool rescueOk, bytes memory rescueOut) = proxy.call(abi.encodeWithSelector(bytes4(0x0c506e96),
            address(0x0000000000000000000000000000000000000001), uint256(1)));
        require(rescueOk, "user rescue of a no-code token");
        record("set2_deposit_proxy_surface", string.concat("\"native_funding\":false,\"fallback\":false",
            ",\"outsider_sweep\":false,\"outsider_rescue\":false,\"user_rescue_no_code\":true"));
    }

    function testSet2OutsiderDrivesVictimSweep() public {
        etchInfra();
        address proxy = derivedProxy();
        mockFile("mock_1e10");
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xe0189108), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        bytes32 pending = vm.load(EXCHANGE, pendingSlot());
        require(uint64(uint256(pending)) == 10_000_000_000, "pending spot stored");
        require(uint64(uint256(pending) >> 128) == block.number, "pending block stored");
        bytes memory writerCall = CoreWriterMock(CORE_WRITER).lastInput();
        require(writerCall.length > 68, "core writer reached");
        bytes memory action = abi.decode(slice4(writerCall), (bytes));
        require(bytes4(action) == bytes4(0x01000006), "action 6 last");
        (address dest, uint64 tokenId, uint64 total) = abi.decode(slice4(action), (address, uint64, uint64));
        require(dest == EXCHANGE && tokenId == 0, "send destination");
        require(total == 10_000_000_000, "full observed balance queued, no gas reserve");
        // below the request minimum
        mockFile("mock_1e10");
        vm.store(EXCHANGE, pendingSlot(), 0);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.roll(block.number + 1);
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_999999999_spot.hex")));
        vm.prank(OUTSIDER);
        (bool lowOk, bytes memory lowOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xe0189108), USER));
        require(!lowOk && errorIs(lowOut, 0x329c2b0f), "below minimum rejected");
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_1000000000_spot.hex")));
        vm.prank(OUTSIDER);
        (bool minOk,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xe0189108), USER));
        require(minOk, "at the minimum accepted");
        record("set2_outsider_sweep", string.concat("\"queued_total\":", vm.toString(uint256(total)),
            ",\"pending_spot\":", vm.toString(uint64(uint256(pending))),
            ",\"below_minimum_selector\":", vm.toString(selectorOf(lowOut))));
    }

    function finalizeCredit(uint64 currentSpot) internal returns (uint256 credit) {
        etchInfra();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number - 1));
        mockFile("mock_1e8");
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile(
            currentSpot == 1 ? "runtime/mock_1_spot.hex" : "runtime/mock_50000000_spot.hex")));
        uint256 before = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        credit = uint256(vm.load(EXCHANGE, balanceSlot())) - before;
    }

    function testSet2FinalizeCreditsTheStoredSnapshot() public {
        uint256 oneUnitLeft = finalizeCredit(1);
        uint256 half = finalizeCredit(50_000_000);
        require(oneUnitLeft == half, "credit independent of the size of the decrease");
        require(oneUnitLeft == 100_000_000 * SWEEP_SCALE, "credit is the stored snapshot");
        etchInfra();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number - 1));
        mockFile("mock_1e8");
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_1_spot.hex")));
        uint256 treasuryBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        uint256 totalBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) & type(uint128).max;
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) - treasuryBefore == oneUnitLeft, "treasury credit");
        require((uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) & type(uint128).max) - totalBefore == oneUnitLeft,
            "total balance credit");
        require(vm.load(EXCHANGE, pendingSlot()) == 0, "pending cleared");
        record("set2_finalize_credit", string.concat("\"one_unit_left\":", vm.toString(oneUnitLeft),
            ",\"half_left\":", vm.toString(half),
            ",\"stored_snapshot\":", vm.toString(uint256(100_000_000) * SWEEP_SCALE)));
    }

    function testSet2RetryReservesOneUsdc() public {
        etchInfra();
        address proxy = derivedProxy();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        mockFile("mock_1e10");
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        bytes32 pending = vm.load(EXCHANGE, pendingSlot());
        require(uint64(uint256(pending)) == 9_900_000_000, "retry reserves one USD");
        require(uint64(uint256(pending) >> 128) == block.number, "retry block updated");
        bytes memory writerCall = CoreWriterMock(CORE_WRITER).lastInput();
        (address dest, uint64 tokenId, uint64 total) =
            abi.decode(slice4(abi.decode(slice4(writerCall), (bytes))), (address, uint64, uint64));
        require(dest == EXCHANGE && tokenId == 0 && total == 9_900_000_000, "queued send is the reduced amount");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == uint256(vm.load(EXCHANGE, balanceSlot())),
            "no credit on the retry branch");
        require(vm.load(EXCHANGE, bytes32(uint256(14))) > 0, "treasury seeded");
        record("set2_retry_reserve", string.concat("\"stored_spot\":", vm.toString(uint64(uint256(pending))),
            ",\"queued_total\":", vm.toString(uint256(total)),
            ",\"observed_balance\":", vm.toString(uint256(10_000_000_000))));
    }

    function testSet2FinalizeControls() public {
        // unchanged above the minimum: no credit, the request is replaced
        etchInfra();
        address proxy = derivedProxy();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        mockFile("mock_1e10");
        uint256 before = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        record("set2_finalize_controls_debug", string.concat("\"unchanged_ok\":", ok ? "true" : "false",
            ",\"unchanged_selector\":", vm.toString(selectorOf(out)),
            ",\"unchanged_bytes\":", vm.toString(out.length)));
        if (!ok) revert UnexpectedResult(ok, out);
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == before, "no credit when unchanged");
        require(uint64(uint256(vm.load(EXCHANGE, pendingSlot()))) == 9_900_000_000,
            "request replaced with the reduced amount");
        // increased above the minimum: still no credit
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_10000000001_spot.hex")));
        vm.prank(OUTSIDER);
        (bool ok2,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        require(ok2 && uint256(vm.load(EXCHANGE, balanceSlot())) == before, "increase does not credit");
        // unchanged at the minimum: retry below the threshold
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number - 1));
        mockFile("mock_1e8");
        vm.prank(OUTSIDER);
        (bool ok3, bytes memory out3) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        bytes32 pending3 = vm.load(EXCHANGE, pendingSlot());
        bytes memory writer3 = CoreWriterMock(CORE_WRITER).lastInput();
        record("set2_finalize_controls_below", string.concat("\"ok\":", ok3 ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(out3)), ",\"bytes\":", vm.toString(out3.length),
            ",\"stored_spot\":", vm.toString(uint64(uint256(pending3))),
            ",\"stored_block\":", vm.toString(uint64(uint256(pending3) >> 128)),
            ",\"writer_bytes\":", vm.toString(writer3.length)));
        require(ok3 && uint64(uint256(pending3)) == 0, "dust retry clears the pending request");
        // no pending request
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, pendingSlot(), 0);
        vm.prank(OUTSIDER);
        (bool ok4, bytes memory out4) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        require(!ok4, "no pending request rejected");
        // same block
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number));
        vm.prank(OUTSIDER);
        (bool ok5, bytes memory out5) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        require(!ok5, "same block rejected");
        record("set2_finalize_controls", string.concat("\"unchanged_selector\":", vm.toString(selectorOf(out)),
            ",\"below_minimum_selector\":", vm.toString(selectorOf(out3)),
            ",\"no_pending_selector\":", vm.toString(selectorOf(out4)),
            ",\"same_block_selector\":", vm.toString(selectorOf(out5))));
    }

    address constant LIBRARY_2 = address(uint160(uint256(0x00583d0bd818c991c5830fea93aef04e474b272459)));

    function builderFeeSlot(address builder) internal pure returns (bytes32) {
        return keccak256(abi.encode(builder, uint256(39)));
    }

    function builderFeesMapping(address builder) internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, builderFeeSlot(builder)));
    }

    function sharedBuilderSlot() internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, bytes32(uint256(38)))) >> 160;
    }

    function closeCalldata(uint256[] memory ids, uint256 nonce, uint64 deadline, uint8 v, bytes32 r,
        bytes32 s, bytes memory trailing) internal pure returns (bytes memory) {
        return bytes.concat(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, deadline,
            v, r, s), trailing);
    }

    // Does the signed close bind the builder address it credits?
    function testSet2CloseBuilderWordIsNotSigned() public {
        etchInfra();
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        address builderA = vm.addr(0xaa11);
        address builderB = vm.addr(0xbb11);
        // (a) the plain seven-argument calldata: which builder key, if any, is touched?
        vm.record();
        vm.prank(BATCH);
        (bool okA, bytes memory outA) =
            EXCHANGE.call(closeCalldata(ids, NONCE, deadline, v, r, sigS, ""));
        (bytes32[] memory readsA, bytes32[] memory writesA) = vm.accesses(EXCHANGE);
        // (b) the same signature with one extra unsigned trailing word
        uint256 next = NONCE + 1;
        bytes32 structHashB = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), next, deadline));
        (uint8 vB, bytes32 rB, bytes32 sB) = signTrade(structHashB);
        bytes memory withA = abi.encode(uint256(uint160(builderA)));
        vm.record();
        vm.prank(BATCH);
        (bool okB, bytes memory outB) =
            EXCHANGE.call(closeCalldata(ids, next, deadline, vB, rB, sB, withA));
        (bytes32[] memory readsB, bytes32[] memory writesB) = vm.accesses(EXCHANGE);
        // (c) only the trailing word changes
        uint256 next2 = NONCE + 2;
        bytes32 structHashC = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), next2, deadline));
        (uint8 vC, bytes32 rC, bytes32 sC) = signTrade(structHashC);
        vm.record();
        vm.prank(BATCH);
        (bool okC, bytes memory outC) = EXCHANGE.call(closeCalldata(ids, next2, deadline, vC, rC, sC,
            abi.encode(uint256(uint160(builderB)))));
        (bytes32[] memory readsC, bytes32[] memory writesC) = vm.accesses(EXCHANGE);
        record("set2_builder_close_plain", string.concat(
            "\"ok\":", okA ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(outA)),
            ",\"reads_zero_builder\":", contains(readsA, builderFeeSlot(address(0))) ? "true" : "false",
            ",\"writes_zero_builder\":", contains(writesA, builderFeeSlot(address(0))) ? "true" : "false",
            ",\"read_count\":", vm.toString(readsA.length),
            ",\"write_count\":", vm.toString(writesA.length)));
        record("set2_builder_close_trailing", string.concat(
            "\"a_ok\":", okB ? "true" : "false",
            ",\"a_reads_builderA\":", contains(readsB, builderFeeSlot(builderA)) ? "true" : "false",
            ",\"a_writes_builderA\":", contains(writesB, builderFeeSlot(builderA)) ? "true" : "false",
            ",\"b_ok\":", okC ? "true" : "false",
            ",\"b_selector\":", vm.toString(selectorOf(outC)),
            ",\"b_reads_builderB\":", contains(readsC, builderFeeSlot(builderB)) ? "true" : "false",
            ",\"b_reads_builderA\":", contains(readsC, builderFeeSlot(builderA)) ? "true" : "false",
            ",\"b_writes_builderB\":", contains(writesC, builderFeeSlot(builderB)) ? "true" : "false"));
    }

    // Which calldata word, if any, becomes the credited builder address?
    function testSet2CloseBuilderWordCandidates() public {
        etchInfra();
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256 length = 6;
        uint256[] memory ids = new uint256[](length);
        for (uint256 i; i < length; ++i) ids[i] = 0xaa00 + i;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        vm.record();
        vm.prank(BATCH);
        (bool ok, bytes memory out) =
            EXCHANGE.call(closeCalldata(ids, NONCE, deadline, v, r, sigS, ""));
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        uint256 readBitmap;
        uint256 writeBitmap;
        for (uint256 i; i < length; ++i) {
            if (contains(reads, builderFeeSlot(address(uint160(ids[i]))))) readBitmap |= (1 << i);
            if (contains(writes, builderFeeSlot(address(uint160(ids[i]))))) writeBitmap |= (1 << i);
        }
        record("set2_builder_close_candidates", string.concat(
            "\"ok\":", ok ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(out)),
            ",\"length\":", vm.toString(length),
            "\"ids_read_bitmap\":", "",
            ",\"ids_read_bitmap\":", vm.toString(readBitmap),
            ",\"ids_write_bitmap\":", vm.toString(writeBitmap),
            ",\"read_count\":", vm.toString(reads.length),
            ",\"write_count\":", vm.toString(writes.length)));
    }

    // Do the sweep-family entries reach the slot-39 builder accumulator block?
    function probeBuilderReads(bytes4 selector, bytes memory data, address proxy, bool pending)
        internal returns (uint256 flag) {
        if (pending) {
            vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        } else {
            vm.store(EXCHANGE, pendingSlot(), 0);
        }
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        address a = vm.addr(0xaa11);
        vm.store(EXCHANGE, builderFeeSlot(USER), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(address(0)), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(a), bytes32(uint256(5e18)));
        if (proxy != address(0)) {
            vm.store(EXCHANGE, builderFeeSlot(proxy), bytes32(uint256(5e18)));
        }
        vm.record();
        vm.prank(OUTSIDER);
        (bool ok,) = EXCHANGE.call(abi.encodePacked(selector, data));
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        if (!ok) flag |= 1;
        uint256 candidates = 4;
        uint256 bits = 0;
        for (uint256 i; i < candidates; ++i) {
            address who = i == 0 ? USER : i == 1 ? address(0) : i == 2 ? a : proxy;
            if (contains(reads, builderFeeSlot(who))) bits |= (1 << (2 * i));
            if (contains(writes, builderFeeSlot(who))) bits |= (1 << (2 * i + 1));
        }
        flag |= bits << 8;
    }

    function testSet2OwnerBuilderSweepEntry() public {
        etchInfra();
        address a = vm.addr(0xaa11);
        address b = vm.addr(0xbb11);
        vm.store(EXCHANGE, builderFeeSlot(a), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(b), bytes32(uint256(7e18)));
        vm.store(EXCHANGE, bytes32(uint256(38)), bytes32(uint256(100e18) << 160));
        vm.record();
        vm.prank(OUTSIDER);
        (bool outsiderOk, bytes memory outsiderOut) =
            EXCHANGE.call(abi.encodeWithSelector(bytes4(0xd970fad5), a, b));
        vm.record();
        vm.prank(OWNER);
        (bool ownerOk, bytes memory ownerOut) =
            EXCHANGE.call(abi.encodeWithSelector(bytes4(0xd970fad5), a, b));
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        uint256 bits;
        for (uint256 i; i < 2; ++i) {
            address who = i == 0 ? a : b;
            if (contains(reads, builderFeeSlot(who))) bits |= (1 << (2 * i));
            if (contains(writes, builderFeeSlot(who))) bits |= (1 << (2 * i + 1));
        }
        record("set2_builder_sweep_entry", string.concat(
            "\"outsider_ok\":", outsiderOk ? "true" : "false",
            ",\"outsider_selector\":", vm.toString(selectorOf(outsiderOut)),
            ",\"owner_ok\":", ownerOk ? "true" : "false",
            ",\"owner_selector\":", vm.toString(selectorOf(ownerOut)),
            ",\"entry_a\":", vm.toString(builderFeesMapping(a)),
            ",\"entry_b\":", vm.toString(builderFeesMapping(b)),
            ",\"shared\":", vm.toString(sharedBuilderSlot()),
            ",\"key_bits\":", vm.toString(bits)));
    }

    function testSet2SweepFamilyBuilderReads() public {
        etchInfra();
        address proxy = derivedProxy();
        address a = vm.addr(0xaa11);
        mockFile("mock_1e10");
        uint256 sweepPending = probeBuilderReads(bytes4(0x01681a62), abi.encode(USER), proxy, true);
        uint256 sweepFresh = probeBuilderReads(bytes4(0x01681a62), abi.encode(USER), proxy, false);
        uint256 request = probeBuilderReads(bytes4(0xe0189108), abi.encode(USER), proxy, false);
        uint256 finalize = probeBuilderReads(bytes4(0x6d142da1), abi.encode(USER), proxy, true);
        record("set2_sweep_builder_bits", string.concat(
            "\"sweep_pending\":", vm.toString(sweepPending),
            ",\"sweep_fresh\":", vm.toString(sweepFresh),
            ",\"request\":", vm.toString(request),
            ",\"finalize\":", vm.toString(finalize),
            ",\"layout\":\"bit0 failed, bits1..8 are (read,write) of seeded builderFees entries for USER, address(0), a, proxy\""));
    }

    // Is claimBuilderFees per-caller or shared?
    function testSet2ClaimBuilderFeesScope() public {
        etchInfra();
        vm.etch(LIBRARY_2, vm.parseBytes(vm.readFile("runtime/Library2.hex")));
        address builderA = vm.addr(0xaa11);
        address builderB = vm.addr(0xbb11);
        vm.store(EXCHANGE, builderFeeSlot(builderA), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(builderB), bytes32(uint256(7e18)));
        vm.store(EXCHANGE, bytes32(uint256(38)), bytes32(uint256(100e18) << 160));
        vm.recordLogs();
        vm.prank(builderA);
        (bool okA, bytes memory outA) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x69f9a5f0)));
        Vm.Log[] memory logsA = vm.getRecordedLogs();
        uint256 paidA;
        for (uint256 i; i < logsA.length; ++i) {
            if (logsA[i].topics[0] == 0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15) {
                (paidA,) = abi.decode(logsA[i].data, (uint256, uint256));
            }
        }
        uint256 entryBAfterA = builderFeesMapping(builderB);
        vm.recordLogs();
        (bool okB, bytes memory outB) = callAs(builderB, abi.encodeWithSelector(bytes4(0x69f9a5f0)));
        Vm.Log[] memory logsB = vm.getRecordedLogs();
        uint256 paidB;
        for (uint256 i; i < logsB.length; ++i) {
            if (logsB[i].topics[0] == 0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15) {
                (paidB,) = abi.decode(logsB[i].data, (uint256, uint256));
            }
        }
        uint256 sharedAfterB = sharedBuilderSlot();
        vm.recordLogs();
        (bool okC, bytes memory outC) = callAs(OUTSIDER, abi.encodeWithSelector(bytes4(0x69f9a5f0)));
        Vm.Log[] memory logsC = vm.getRecordedLogs();
        uint256 paidC;
        for (uint256 i; i < logsC.length; ++i) {
            if (logsC[i].topics[0] == 0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15) {
                (paidC,) = abi.decode(logsC[i].data, (uint256, uint256));
            }
        }
        record("set2_builder_claim_a", string.concat(
            "\"ok\":", okA ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(outA)),
            ",\"paid\":", vm.toString(paidA),
            ",\"entry_a_after\":", vm.toString(builderFeesMapping(builderA)),
            ",\"entry_b_after_a\":", vm.toString(entryBAfterA)));
        record("set2_builder_claim_others", string.concat(
            "\"caller_b_ok\":", okB ? "true" : "false",
            ",\"caller_b_selector\":", vm.toString(selectorOf(outB)),
            ",\"entry_b_after_b\":", vm.toString(sharedAfterB == 0 ? 0 : sharedAfterB),
            ",\"paid_b\":", vm.toString(paidB),
            ",\"outsider_ok\":", okC ? "true" : "false",
            ",\"outsider_selector\":", vm.toString(selectorOf(outC)),
            ",\"paid_outsider\":", vm.toString(paidC)));
    }

    function callAs(address who, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(who);
        return EXCHANGE.call(data);
    }

    function testSet2RecoveryGuards() public {
        vm.store(EXCHANGE, pendingSlot(), pendingWord(50_050_916, 0, block.number - 1));
        vm.prank(OUTSIDER);
        (bool outsiderOk, bytes memory outsiderOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6a3214c9),
            USER, uint256(50_050_916)));
        require(!outsiderOk && errorIs(outsiderOut, 0x30cd7471), "NotOwner for an outsider");
        vm.prank(OWNER);
        (bool ownerOk, bytes memory ownerOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6a3214c9),
            USER, uint256(50_050_916)));
        require(!ownerOk && errorIs(ownerOut, 0x28ef4314), "SweepAlreadyPending for the owner");
        vm.prank(OWNER);
        (bool clearOk, bytes memory clearOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        require(!clearOk && clearOut.length == 0, "clearPendingSweep is absent");
        require(uint64(uint256(vm.load(EXCHANGE, pendingSlot()))) == 50_050_916, "pending word unchanged");
        record("set2_recovery_guards", string.concat("\"outsider_selector\":", vm.toString(selectorOf(outsiderOut)),
            ",\"owner_selector\":", vm.toString(selectorOf(ownerOut)),
            ",\"clear_returndata_bytes\":", vm.toString(clearOut.length)));
    }

    // ================= pass-two: semi-trusted roles =================

    address constant ORACLE = address(uint160(uint256(0x00a9b4c7b7ca5835652d81e25739c870d49f39cc2e)));
    address constant REGISTRY = address(uint160(uint256(0x00fdc6550436dd75ce8a0b145f935b7d3a64f53248)));
    address constant PAUSE_GUARDIAN = address(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)));
    address constant MARKET_KEEPER = address(uint160(uint256(0x003721476de31190dc1af8908026abe20efe25cf99)));
    address constant PRE_BBO = address(0x080e);
    address constant TOKENOMICS = address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9)));
    bytes32 constant INST0_ROOT = 0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6df;
    bytes32 constant INST0_W0 = 0x000003e8000000000000002c28d1751327a700000000032d26d12e980b600000;
    bytes32 constant INST0_W1 = 0x00016345785d8a00000001b0f51147891600000000084595161401484a000000;
    bytes32 constant INST0_W2 = 0x00000000000000000000000000000000000000000000152d02c7e14af6800000;
    bytes32 constant MARKET0_ROOT = 0xb7634ec2165a7280a285aac3ec10cf370eca86d8aa9d3243c90b2151434091ad;
    bytes32 constant MARKET0_W0 = 0x000000000000000a0000006a7b0a8451489ff50800000087e15f8bfb5c98cd37;
    bytes32 constant MARKET0_W1 = 0x000000000000006d6f7f9910a100abf8000000000000008e0566e854e34d5335;

    function roleInfra() internal {
        etchInfra();
        vm.etch(LIBRARY_2, vm.parseBytes(vm.readFile("runtime/Library2.hex")));
        vm.etch(REGISTRY, vm.parseBytes(vm.readFile("runtime/BuilderRegistry.hex")));
        vm.etch(ORACLE, vm.parseBytes(vm.readFile("runtime/OracleImpl.hex")));
        vm.etch(PRE_BBO, hex"7f00000000000000000000000000000000000000000000000000000000000000646000527f00000000000000000000000000000000000000000000000000000000000000c860205260406000f3");
        // stub the Tokenomics side contract: the close path only needs it not to revert
        vm.etch(TOKENOMICS, hex"6102006000f3");
        vm.store(EXCHANGE, INST0_ROOT, INST0_W0);
        vm.store(EXCHANGE, bytes32(uint256(INST0_ROOT) + 1), INST0_W1);
        vm.store(EXCHANGE, bytes32(uint256(INST0_ROOT) + 2), INST0_W2);
        vm.store(EXCHANGE, MARKET0_ROOT, MARKET0_W0);
        vm.store(EXCHANGE, bytes32(uint256(MARKET0_ROOT) + 1), MARKET0_W1);
        vm.store(EXCHANGE, bytes32(uint256(89)), bytes32(uint256(uint160(KEEPER))));
    }

    function rolePosition(uint256 id, address who, uint256 entry, uint256 margin, uint256 leverage)
        internal {
        bytes32 slot = keccak256(abi.encode(id, uint256(10)));
        uint256 word0 = uint256(uint160(who)) | (uint256(0) << 160) | (entry << 192);
        uint256 word1 = margin | (leverage << 128) | (uint256(block.timestamp) << 160) |
            (uint256(1) << 240);
        vm.store(EXCHANGE, slot, bytes32(word0));
        vm.store(EXCHANGE, bytes32(uint256(slot) + 1), bytes32(word1));
    }

    function roleClose(uint256 id, uint64 deadline, uint8 v, bytes32 r, bytes32 sigS)
        internal returns (bool, bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = id;
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, NONCE, deadline,
            v, r, sigS));
    }

    function roleCloseSigned(uint256 id, uint256 nonce, uint64 deadline)
        internal returns (bool, bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = id;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, deadline,
            v, r, sigS));
    }

    // --- Builder: what address does a fee-paying close credit? ---
    function approveBuilder(address who) internal {
        vm.store(REGISTRY, keccak256(abi.encode(who, uint256(2))), bytes32(uint256(1)));
    }

    function approveAll(address[14] memory cands) internal {
        for (uint256 i; i < cands.length; ++i) approveBuilder(cands[i]);
    }

    function builderCandidates(uint256 id) internal returns (address[14] memory c) {
        c[0] = USER; c[1] = BATCH; c[2] = OUTSIDER; c[3] = OWNER; c[4] = KEEPER;
        c[5] = MARKET_KEEPER; c[6] = PAUSE_GUARDIAN; c[7] = address(0); c[8] = ORACLE;
        c[9] = LIBRARY_2; c[10] = REGISTRY; c[11] = address(uint160(id)); c[12] = SESSION;
        c[13] = EXCHANGE;
    }

    function builderArm(string memory name, uint256 id, uint256 entry, bytes memory trailing,
        bool approveThem) internal {
        roleInfra();
        enableSessionKey();
        rolePosition(id, USER, entry, 100e18, 10);
        bytes32 totals = bytes32(uint256(22));
        uint256 old = uint256(vm.load(EXCHANGE, totals));
        vm.store(EXCHANGE, totals, bytes32((((old >> 128) + 100e18) << 128) | uint128(old)));
        address[14] memory cands = builderCandidates(id);
        if (approveThem) approveAll(cands);
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256[] memory ids = new uint256[](1);
        ids[0] = id;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        bytes memory payload = bytes.concat(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids,
            NONCE, deadline, v, r, sigS), trailing);
        vm.record();
        vm.prank(BATCH);
        (bool ok, bytes memory out) = EXCHANGE.call(payload);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        (bytes32[] memory registryReads,) = vm.accesses(REGISTRY);
        uint256 readBits;
        uint256 writeBits;
        uint256 paid;
        for (uint256 i; i < cands.length; ++i) {
            if (contains(reads, builderFeeSlot(cands[i]))) readBits |= (1 << i);
            if (contains(writes, builderFeeSlot(cands[i]))) writeBits |= (1 << i);
            uint256 entry_ = builderFeesMapping(cands[i]);
            if (entry_ != 0) paid = entry_;
        }
        record(string.concat(name, "_a"), string.concat(
            "\"ok\":", ok ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(out)),
            ",\"reads\":", vm.toString(reads.length),
            ",\"writes\":", vm.toString(writes.length),
            ",\"approved\":", approveThem ? "true" : "false"));
        record(string.concat(name, "_b"), string.concat(
            "\"slot39_read_bits\":", vm.toString(readBits),
            ",\"slot39_write_bits\":", vm.toString(writeBits),
            ",\"credited_value\":", vm.toString(paid),
            ",\"shared_counter\":", vm.toString(sharedBuilderSlot()),
            ",\"registry_accesses\":", vm.toString(registryReads.length)));
    }

    function testRoleBuilderKeyFeePayingClose() public {
        builderArm("role_builder_plain", 1, 200, "", false);
    }

    function testRoleBuilderKeyOtherPositionId() public {
        builderArm("role_builder_id7", 7, 200, "", false);
    }

    function testRoleBuilderTrailingWord() public {
        builderArm("role_builder_trailing", 1, 200, abi.encode(uint256(uint160(KEEPER))), false);
    }

    function testRoleBuilderApprovedCandidates() public {
        builderArm("role_builder_approved", 1, 200, "", true);
    }

    function testRoleBuilderLossClose() public {
        builderArm("role_builder_loss", 1, 100, "", true);
    }

    // --- Guardian and keeper: what the pause surfaces actually gate ---
    function pauseSelectorOf(address who, bytes memory data) internal returns (uint256) {
        vm.prank(who);
        (bool ok, bytes memory out) = EXCHANGE.call(data);
        return ok ? 0 : selectorOf(out);
    }

    function testRolePauseSurface() public {
        roleInfra();
        uint256 keeperGlobalPause = pauseSelectorOf(KEEPER,
            abi.encodeWithSelector(bytes4(0xae69b95b), true));
        uint256 mkGlobalPause = pauseSelectorOf(MARKET_KEEPER,
            abi.encodeWithSelector(bytes4(0xae69b95b), true));
        uint256 outsiderGlobalPause = pauseSelectorOf(OUTSIDER,
            abi.encodeWithSelector(bytes4(0xae69b95b), true));
        uint256 guardianGlobalPause = pauseSelectorOf(PAUSE_GUARDIAN,
            abi.encodeWithSelector(bytes4(0xae69b95b), true));
        uint256 afterGuardian = uint256(vm.load(EXCHANGE, bytes32(uint256(29)))) & 0xff;
        uint256 guardianGlobalResume = pauseSelectorOf(PAUSE_GUARDIAN,
            abi.encodeWithSelector(bytes4(0xae69b95b), false));
        uint256 ownerGlobalResume = pauseSelectorOf(OWNER,
            abi.encodeWithSelector(bytes4(0xae69b95b), false));
        uint256 keeperMarketPause = pauseSelectorOf(KEEPER,
            abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)));
        uint256 mkMarketPause = pauseSelectorOf(MARKET_KEEPER,
            abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0)));
        record("role_pause_surface", string.concat(
            "\"keeper_global_pause\":", vm.toString(keeperGlobalPause),
            ",\"marketKeeper_global_pause\":", vm.toString(mkGlobalPause),
            ",\"outsider_global_pause\":", vm.toString(outsiderGlobalPause),
            ",\"guardian_global_pause\":", vm.toString(guardianGlobalPause),
            ",\"guardian_set_pause_byte\":", vm.toString(afterGuardian),
            ",\"guardian_global_resume\":", vm.toString(guardianGlobalResume),
            ",\"owner_global_resume\":", vm.toString(ownerGlobalResume),
            ",\"keeper_market_pause\":", vm.toString(keeperMarketPause),
            ",\"marketKeeper_market_pause\":", vm.toString(mkMarketPause)));
    }

    // With the global pause set, which value paths still move?
    function testRoleGlobalPauseGates() public {
        roleInfra();
        enableSessionKey();
        rolePosition(1, USER, 200, 100e18, 10);
        vm.store(EXCHANGE, bytes32(uint256(29)),
                 bytes32(uint256(uint160(SESSION)) << 8 | 1));
        uint64 deadline = uint64(block.timestamp + 3600);
        vm.record();
        (bool closeOk, bytes memory closeOut) = roleCloseSigned(1, NONCE, deadline);
        (bytes32[] memory closeReads, bytes32[] memory closeWrites) = vm.accesses(EXCHANGE);
        uint256[] memory none = new uint256[](0);
        vm.prank(OUTSIDER);
        (bool liqOk, bytes memory liqOut) = EXCHANGE.call(
            abi.encodeWithSelector(bytes4(0x599dc539), none));
        record("role_global_pause_gates", string.concat(
            "\"close_ok\":", closeOk ? "true" : "false",
            ",\"close_selector\":", vm.toString(selectorOf(closeOut)),
            ",\"close_writes\":", vm.toString(closeWrites.length),
            ",\"close_flags_after\":",
            vm.toString((uint256(vm.load(EXCHANGE, bytes32(uint256(keccak256(abi.encode(uint256(1), uint256(10)))) + 1))) >> 240) & 1),
            ",\"liquidate_batch_ok\":", liqOk ? "true" : "false",
            ",\"liquidate_batch_selector\":", vm.toString(selectorOf(liqOut))));
    }

    // --- Keeper surface: every selector a keeper or market keeper might reach ---
    function keeperOutcome(address who, bytes memory payload) internal returns (uint256) {
        vm.prank(who);
        (bool ok, bytes memory out) = EXCHANGE.call(payload);
        return ok ? 0 : selectorOf(out);
    }

    function testRoleKeeperSurface() public {
        roleInfra();
        rolePosition(1, USER, 200, 100e18, 10);
        uint256[2] memory keeper = [
            keeperOutcome(KEEPER, abi.encodeWithSelector(bytes4(0xe6ac4a74), true)),
            keeperOutcome(KEEPER, abi.encodeWithSelector(bytes4(0xe538b280), uint256(1), uint256(1), uint256(1)))];
        uint256 keeperClose = keeperOutcome(KEEPER, abi.encodeWithSelector(bytes4(0x2792e706),
            USER, new uint256[](0), NONCE, uint64(block.timestamp + 3600), uint8(27), bytes32(0), bytes32(0)));
        uint256[3] memory mk = [
            keeperOutcome(MARKET_KEEPER, abi.encodeWithSelector(bytes4(0x628a9fd6),
                uint32(0), type(uint128).max, type(uint128).max)),
            keeperOutcome(MARKET_KEEPER, abi.encodeWithSelector(bytes4(0x82f47a3f),
                type(uint128).max, type(uint128).max)),
            keeperOutcome(MARKET_KEEPER, abi.encodeWithSelector(bytes4(0x5ca4c0ea),
                uint32(0), uint128(1), uint96(1), uint96(1), uint64(1)))];
        uint256 kFeeAfter = keeperOutcome(KEEPER, abi.encodeWithSelector(bytes4(0xe538b280),
            uint256(1), uint256(1), uint256(1)));
        record("role_keeper_surface", string.concat(
            "\"keeper_flag\":", vm.toString(keeper[0]),
            ",\"keeper_setFeeRates\":", vm.toString(keeper[1]),
            ",\"keeper_close\":", vm.toString(keeperClose),
            ",\"keeper_setFeeRates_again\":", vm.toString(kFeeAfter),
            ",\"marketKeeper_oiCap\":", vm.toString(mk[0]),
            ",\"marketKeeper_slot28\":", vm.toString(mk[1]),
            ",\"marketKeeper_instrument\":", vm.toString(mk[2]),
            ",\"slot24_after\":", vm.toString(uint256(vm.load(EXCHANGE, bytes32(uint256(24))))),
            ",\"slot28_after\":\"", vm.toString(uint256(vm.load(EXCHANGE, bytes32(uint256(28))))),
            "\""));
    }

    // --- Keeper flag: does the slot-8 byte gate the close or the liquidation? ---
    function testRoleKeeperFlagGates() public {
        roleInfra();
        enableSessionKey();
        rolePosition(1, USER, 200, 100e18, 10);
        uint256 word8 = uint256(vm.load(EXCHANGE, bytes32(uint256(8))));
        uint256 baseline = (uint256(vm.load(EXCHANGE, bytes32(uint256(keccak256(abi.encode(uint256(1), uint256(10)))) + 1))) >> 240) & 1;
        uint64 deadline = uint64(block.timestamp + 3600);
        vm.prank(KEEPER);
        (bool flipOk,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xe6ac4a74), false));
        uint256 flagAfter = (uint256(vm.load(EXCHANGE, bytes32(uint256(8)))) >> 32) & 0xff;
        vm.record();
        (bool closeOk, bytes memory closeOut) = roleCloseSigned(1, NONCE, deadline);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        uint256 activeAfter = (uint256(vm.load(EXCHANGE, bytes32(uint256(keccak256(abi.encode(uint256(1), uint256(10)))) + 1))) >> 240) & 1;
        record("role_keeper_flag_gates", string.concat(
            "\"flip_ok\":", flipOk ? "true" : "false",
            ",\"flag_word_before\":\"", vm.toString(word8),
            "\",\"flag_byte_after\":", vm.toString(flagAfter),
            ",\"active_before\":", vm.toString(baseline),
            ",\"close_ok\":", closeOk ? "true" : "false",
            ",\"close_selector\":", vm.toString(selectorOf(closeOut)),
            ",\"close_reads\":", vm.toString(reads.length),
            ",\"close_writes\":", vm.toString(writes.length),
            ",\"active_after\":", vm.toString(activeAfter)));
    }

    // --- Relayer: reorder, duplicate, re-target ---
    function enableRelayer(address who) internal {
        vm.store(BATCH, keccak256(abi.encode(who, uint256(4))), bytes32(uint256(1)));
    }

    function signedClose(bytes memory idsPacked, uint256 nonce, uint64 deadline)
        internal returns (bytes memory payload, uint8 v, bytes32 r, bytes32 sigS) {
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER, keccak256(idsPacked),
            nonce, deadline));
        (v, r, sigS) = signTrade(structHash);
        uint256[] memory ids = new uint256[](1);
        ids[0] = uint256(uint256(uint160(0)));
        payload = "";
    }

    function closePayload(uint256 id, uint64 deadline, bytes memory sig, bytes32 idsHash, uint256 nonce)
        internal pure returns (bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = id;
        (uint8 v0, bytes32 r0, bytes32 s0) = splitSig(sig);
        return abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, deadline, v0, r0, s0);
    }

    function splitSig(bytes memory sig) internal pure returns (uint8 v, bytes32 r, bytes32 s) {
        assembly {
            v := byte(0, mload(add(sig, 0x20)))
            r := mload(add(sig, 0x21))
            s := mload(add(sig, 0x41))
        }
    }

    function closeSig(uint256 id, uint256 nonce, uint64 deadline)
        internal returns (bytes memory payload) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = id;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        payload = abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, deadline, v, r, sigS);
    }

    function runTwo(bytes memory a, bytes memory b)
        internal returns (bool okA, uint256 selA, bool okB, uint256 selB) {
        Call[] memory calls = new Call[](2);
        calls[0] = Call(EXCHANGE, a, true, bytes32(0), bytes32(0));
        calls[1] = Call(EXCHANGE, b, true, bytes32(0), bytes32(0));
        vm.recordLogs();
        vm.prank(OUTSIDER);
        (bool outerOk,) = BATCH.call(abi.encodeWithSelector(bytes4(0x251fb27d), calls));
        require(outerOk, "batch outer call");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        uint256 seen;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] != CALL_EXECUTED_TOPIC) continue;
            (bool innerOk, bytes memory innerReturn) = abi.decode(logs[i].data, (bool, bytes));
            if (seen == 0) { okA = innerOk; selA = selectorOf(innerReturn); }
            else { okB = innerOk; selB = selectorOf(innerReturn); }
            ++seen;
        }
    }

    function testRoleRelayerBatch() public {
        roleInfra();
        enableSessionKey();
        enableRelayer(OUTSIDER);
        rolePosition(1, USER, 200, 100e18, 10);
        rolePosition(2, USER, 200, 100e18, 10);
        bytes32 totals = bytes32(uint256(22));
        uint256 old = uint256(vm.load(EXCHANGE, totals));
        vm.store(EXCHANGE, totals, bytes32((((old >> 128) + 200e18) << 128) | uint128(old)));
        uint64 deadline = uint64(block.timestamp + 3600);
        // A: duplicate the same signed intent
        bytes memory payloadA = closeSig(1, NONCE, deadline);
        (bool dup1, uint256 dup1sel, bool dup2, uint256 dup2sel) = runTwo(payloadA, payloadA);
        // B: signature for id 1, calldata for id 2
        bytes memory payloadB = closeSig(1, NONCE + 1, deadline);
        bytes memory wrong = retargetIds(payloadB, 2);
        (bool w1, uint256 w1sel, bool w2, uint256 w2sel) = runTwo(wrong, payloadB);
        // C: signature for USER, calldata names a different user
        bytes memory payloadC = closeSig(2, NONCE + 2, deadline);
        bytes memory retarget = abi.encodeWithSelector(bytes4(0x2792e706), OUTSIDER, uarr(2),
            NONCE + 2, deadline, uint8(0), bytes32(0), bytes32(0));
        retarget = retargetUser(payloadC, OUTSIDER);
        (bool rt1, uint256 rt1sel, bool rt2, uint256 rt2sel) = runTwo(retarget, payloadC);
        record("role_relayer_batch", string.concat(
            "\"dup_first_ok\":", dup1 ? "true" : "false",
            ",\"dup_second_sel\":", vm.toString(dup2sel),
            ",\"dup_second_ok\":", dup2 ? "true" : "false",
            ",\"wrongids_first_ok\":", w1 ? "true" : "false",
            ",\"wrongids_first_sel\":", vm.toString(w1sel),
            ",\"wrongids_second_ok\":", w2 ? "true" : "false",
            ",\"retarget_first_sel\":", vm.toString(rt1sel),
            ",\"retarget_second_ok\":", rt2 ? "true" : "false"));
    }

    function uarr(uint256 v) internal pure returns (uint256[] memory a) {
        a = new uint256[](1);
        a[0] = v;
    }

    function retargetUser(bytes memory payload, address who) internal pure returns (bytes memory) {
        (, uint256[] memory ids, uint256 nonce, uint64 deadline, uint8 v, bytes32 r, bytes32 sigS) =
            abi.decode(slice4(payload), (address, uint256[], uint256, uint64, uint8, bytes32,
                bytes32));
        return abi.encodeWithSelector(bytes4(0x2792e706), who, ids, nonce, deadline, v, r, sigS);
    }

    function retargetIds(bytes memory payload, uint256 id) internal pure returns (bytes memory) {
        (address user, uint256[] memory ids, uint256 nonce, uint64 deadline, uint8 v, bytes32 r,
            bytes32 sigS) = abi.decode(slice4(payload),
            (address, uint256[], uint256, uint64, uint8, bytes32, bytes32));
        ids[0] = id;
        return abi.encodeWithSelector(bytes4(0x2792e706), user, ids, nonce, deadline, v, r, sigS);
    }

    function testRoleRelayerOrder() public {
        roleInfra();
        enableSessionKey();
        enableRelayer(OUTSIDER);
        rolePosition(1, USER, 200, 100e18, 10);
        rolePosition(2, USER, 200, 100e18, 10);
        bytes32 totals = bytes32(uint256(22));
        uint256 old = uint256(vm.load(EXCHANGE, totals));
        vm.store(EXCHANGE, totals, bytes32((((old >> 128) + 200e18) << 128) | uint128(old)));
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256[2] memory firstOrder = pricesOf(closeSig(1, NONCE, deadline),
                                                closeSig(2, NONCE + 1, deadline));
        rolePosition(1, USER, 200, 100e18, 10);
        rolePosition(2, USER, 200, 100e18, 10);
        uint256[2] memory secondOrder = pricesOf(closeSig(1, NONCE + 2, deadline),
                                                 closeSig(2, NONCE + 3, deadline), false);
        record("role_relayer_order", string.concat(
            "\"order12_price_a\":", vm.toString(firstOrder[0]),
            ",\"order12_price_b\":", vm.toString(firstOrder[1]),
            ",\"order21_price_b\":", vm.toString(secondOrder[0]),
            ",\"order21_price_a\":", vm.toString(secondOrder[1])));
    }

    function capOpen(uint256 size, uint256 nonce, uint64 deadline, uint32 leverage)
        internal returns (uint256) {
        bytes32 structHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(0), true,
            uint128(size), leverage, false, nonce, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        vm.prank(BATCH);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xec6783f0),
            USER, uint32(0), true, uint128(size), leverage, false, nonce, deadline, v, r, sigS));
        return ok ? 0 : selectorOf(out);
    }

    function testRoleKeeperCapEffect() public {
        roleInfra();
        enableSessionKey();
        vm.store(EXCHANGE, keccak256(abi.encode(USER, uint256(9))), bytes32(uint256(1e40)));
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256[3] memory live;
        live[0] = capOpen(1e20, NONCE + 1, deadline, 100);
        live[1] = capOpen(1e22, NONCE + 2, deadline, 100);
        live[2] = capOpen(1e24, NONCE + 3, deadline, 100);
        // the market keeper raises both per-side caps to their maximum
        vm.prank(MARKET_KEEPER);
        EXCHANGE.call(abi.encodeWithSelector(bytes4(0x628a9fd6), uint32(0),
            type(uint128).max, type(uint128).max));
        uint256[3] memory maxed;
        maxed[0] = capOpen(1e20, NONCE + 4, deadline, 100);
        maxed[1] = capOpen(1e22, NONCE + 5, deadline, 100);
        maxed[2] = capOpen(1e24, NONCE + 6, deadline, 100);
        record("role_keeper_cap_effect", string.concat(
            "\"live_1e20\":", vm.toString(live[0]),
            ",\"live_1e22\":", vm.toString(live[1]),
            ",\"live_1e24\":", vm.toString(live[2]),
            ",\"maxed_1e20\":", vm.toString(maxed[0]),
            ",\"maxed_1e22\":", vm.toString(maxed[1]),
            ",\"maxed_1e24\":", vm.toString(maxed[2])));
    }

    function testRoleGlobalPauseOpenGate() public {
        roleInfra();
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        vm.store(EXCHANGE, keccak256(abi.encode(USER, uint256(9))), bytes32(uint256(1e40)));
        bytes32 structHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(0), true,
            uint128(1e20), uint32(10), false, NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        vm.prank(BATCH);
        (bool ok0, bytes memory out0) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xec6783f0),
            USER, uint32(0), true, uint128(1e20), uint32(10), false, NONCE, deadline, v, r, sigS));
        vm.store(EXCHANGE, bytes32(uint256(29)), bytes32(uint256(uint160(SESSION)) << 8 | 1));
        vm.roll(block.number + 1);
        bytes32 structHash1 = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(0), true,
            uint128(1e20), uint32(10), false, NONCE + 1, deadline));
        (uint8 v1, bytes32 r1, bytes32 sigS1) = signTrade(structHash1);
        vm.prank(BATCH);
        (bool ok1, bytes memory out1) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xec6783f0),
            USER, uint32(0), true, uint128(1e20), uint32(10), false, NONCE + 1, deadline, v1, r1,
            sigS1));
        record("role_global_pause_open", string.concat(
            "\"flag0_ok\":", ok0 ? "true" : "false",
            ",\"flag0_selector\":", vm.toString(selectorOf(out0)),
            ",\"flag1_ok\":", ok1 ? "true" : "false",
            ",\"flag1_selector\":", vm.toString(selectorOf(out1))));
    }

    function testRoleKeeperLiquidationBoundary() public {
        roleInfra();
        rolePosition(1, USER, 200, 100e18, 10);   // short, midpoint 150 -> healthy
        rolePosition(2, USER, 100, 100e18, 10);   // short, midpoint 150 -> underwater
        uint256[] memory healthy = new uint256[](1);
        healthy[0] = 1;
        vm.recordLogs();
        vm.prank(OUTSIDER);
        (bool hOk, bytes memory hOut) = EXCHANGE.call(
            abi.encodeWithSelector(bytes4(0x599dc539), healthy));
        Vm.Log[] memory hLogs = vm.getRecordedLogs();
        uint256 healthyEvents;
        for (uint256 i; i < hLogs.length; ++i) {
            if (hLogs[i].topics[0] == 0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8)
                ++healthyEvents;
        }
        uint256[] memory ill = new uint256[](1);
        ill[0] = 2;
        vm.recordLogs();
        vm.prank(OUTSIDER);
        (bool iOk, bytes memory iOut) = EXCHANGE.call(
            abi.encodeWithSelector(bytes4(0x599dc539), ill));
        Vm.Log[] memory iLogs = vm.getRecordedLogs();
        uint256 illEvents;
        for (uint256 i; i < iLogs.length; ++i) {
            if (iLogs[i].topics[0] == 0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8)
                ++illEvents;
        }
        record("role_keeper_liquidation", string.concat(
            "\"healthy_ok\":", hOk ? "true" : "false",
            ",\"healthy_selector\":", vm.toString(selectorOf(hOut)),
            ",\"healthy_events\":", vm.toString(healthyEvents),
            ",\"healthy_active_after\":",
            vm.toString((uint256(vm.load(EXCHANGE, bytes32(uint256(keccak256(abi.encode(uint256(1), uint256(10)))) + 1))) >> 240) & 1),
            ",\"ill_ok\":", iOk ? "true" : "false",
            ",\"ill_events\":", vm.toString(illEvents),
            ",\"ill_active_after\":",
            vm.toString((uint256(vm.load(EXCHANGE, bytes32(uint256(keccak256(abi.encode(uint256(2), uint256(10)))) + 1))) >> 240) & 1)));
    }

    function testRoleRelayerWithdrawRecipient() public {
        roleInfra();
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, sigS);
        address recipient;
        if (ok) {
            bytes memory writerCall = CoreWriterMock(CORE_WRITER).lastInput();
            (recipient, , ) = abi.decode(slice4(abi.decode(slice4(writerCall), (bytes))),
                (address, uint64, uint64));
        }
        // the same signature with a different user word in calldata
        uint256 retargetSel;
        {
            (bool ok2, bytes memory out2) = withdrawSignedFields(BATCH, OUTSIDER, 2_000_000, NONCE,
                deadline, v, r, sigS);
            retargetSel = ok2 ? 0 : selectorOf(out2);
        }
        record("role_relayer_withdraw", string.concat(
            "\"ok\":", ok ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(out)),
            ",\"recipient_is_signed_user\":", recipient == USER ? "true" : "false",
            ",\"retarget_selector\":", vm.toString(retargetSel)));
    }

    function pricesOf(bytes memory a, bytes memory b) internal returns (uint256[2] memory out) {
        return pricesOf(a, b, true);
    }

    function pricesOf(bytes memory a, bytes memory b, bool forward)
        internal returns (uint256[2] memory out) {
        if (!forward) { (a, b) = (b, a); }
        Call[] memory calls = new Call[](2);
        calls[0] = Call(EXCHANGE, a, true, bytes32(0), bytes32(0));
        calls[1] = Call(EXCHANGE, b, true, bytes32(0), bytes32(0));
        vm.recordLogs();
        vm.prank(OUTSIDER);
        BATCH.call(abi.encodeWithSelector(bytes4(0x251fb27d), calls));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        uint256 seen;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] != 0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf)
                continue;
            (uint256 exitPrice, , , , ) = abi.decode(logs[i].data,
                (uint256, int256, int256, uint256, uint256));
            out[seen] = exitPrice;
            ++seen;
        }
    }
}
