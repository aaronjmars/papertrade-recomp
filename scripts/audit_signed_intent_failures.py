#!/usr/bin/env python3
"""Check signed open, close, and withdrawal rejection on pinned runtime bytes."""

import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_oracle_behavior import returndata


ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "audit_signed_intent_failures" / "replay.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
EXCHANGE_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SESSION_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
PIN_TIMESTAMP = 1792357341
EXCHANGE_BATCH_CALLER_SLOT_88 = "0x000000000000000000000000233ff29b239abc1d7748605da9b205c3e008626e"
SESSION_DIRECT_SLOTS = {
    0: "0x0000000000000000000000000000000000000000000000000000000000000001",
    1: "0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77",
    2: "0x000000000000000000000000b915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
    3: "0x0000000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a2",
}

SOURCE = '''pragma solidity ^0.8.24;
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
}
contract CoreWriterMock {
    bytes public lastInput;
    fallback() external { lastInput = msg.data; }
}
contract SignedIntentFailuresTest {
    error UnexpectedResult(bool ok, bytes output);
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant EXCHANGE_IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant SESSION_IMPL = address(uint160(uint256(0x008a5069fe303e8f81e91825436e956d595032e558)));
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
        vm.etch(EXCHANGE_IMPL, vm.parseBytes(vm.readFile("runtime/ExchangeImpl.hex")));
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/SessionProxy.hex")));
        vm.etch(SESSION_IMPL, vm.parseBytes(vm.readFile("runtime/SessionImpl.hex")));
        vm.roll(48902346);
        vm.warp(1792357341);
        vm.chainId(999);
        vm.store(EXCHANGE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(EXCHANGE_IMPL))));
        vm.store(SESSION, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(SESSION_IMPL))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
        vm.store(SESSION, ADMIN_SLOT, bytes32(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
@@EXCHANGE_STORAGE@@
@@SESSION_STORAGE@@
        vm.store(EXCHANGE, keccak256(abi.encode(USER, uint256(9))), bytes32(uint256(100e18)));
        vm.etch(STATUS, hex"@@STATUS_ONE_CODE@@");
        vm.etch(CORE_BALANCE, hex"@@CORE_BALANCE_CODE@@");
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
        if (openOk || !errorIs(openOut, 0x0a4f5a07)) revert UnexpectedResult(openOk, openOut);
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
}
'''


def build_source(saved_exchange):
    exchange_lines = [f"        vm.store(EXCHANGE, bytes32(uint256({i})), {word});"
                      for i, word in sorted((int(i), v) for i, v in saved_exchange["slots"].items()) if int(word, 16)]
    exchange_lines.append(f"        vm.store(EXCHANGE, bytes32(uint256(88)), {EXCHANGE_BATCH_CALLER_SLOT_88});")
    session_lines = [f"        vm.store(SESSION, bytes32(uint256({i})), {word});"
                     for i, word in SESSION_DIRECT_SLOTS.items()]
    source = SOURCE.replace("@@EXCHANGE_STORAGE@@", "\n".join(exchange_lines))
    source = source.replace("@@SESSION_STORAGE@@", "\n".join(session_lines))
    source = source.replace("@@STATUS_ONE_CODE@@", returndata(1)[2:])
    source = source.replace("@@CORE_BALANCE_CODE@@", returndata(10**12, 0, 0)[2:])
    assert "@@" not in source
    return source


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved_exchange = json.loads((ROOT / "artifacts" / "exchange_direct_status_local"
                                 / "pinned_direct_slots.json").read_text())
    assert manifest["block"] == saved_exchange["pin"] == 48902346
    assert manifest["block_hash"] == saved_exchange["block_hash"]
    assert manifest["timestamp"] == PIN_TIMESTAMP
    assert manifest["contracts"][SESSION]["eip1967_slots"]["implementation"].endswith(SESSION_IMPL[2:])
    assert SESSION_DIRECT_SLOTS[1] == json.loads((ATLAS / "session_key_behavior.json").read_text())["domain_separator"]
    assert SESSION_DIRECT_SLOTS[3].endswith(EXCHANGE[2:])
    assert EXCHANGE_BATCH_CALLER_SLOT_88.endswith(BATCH[2:])
    runtimes = {}
    for label, address in (("ExchangeProxy", EXCHANGE), ("ExchangeImpl", EXCHANGE_IMPL),
                           ("SessionProxy", SESSION), ("SessionImpl", SESSION_IMPL)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"]
        runtimes[label] = code
    source = build_source(saved_exchange)
    withdrawal_typehash = json.loads((ATLAS / "exchange_withdrawal_signature_behavior.json").read_text())["typehash"]
    assert withdrawal_typehash.lower() in source.lower()
    assert shutil.which("forge") and shutil.which("solc")
    with tempfile.TemporaryDirectory(prefix="papertrade-signed-intent-audit-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nfs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "SignedIntentFailures.t.sol").write_text(source)
        for label, code in runtimes.items():
            (project / "runtime" / f"{label}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=60)
    output = run.stdout + "\n" + run.stderr
    passed = re.findall(r"\[PASS\] (test\w+)\(\)", output)
    expected = {"testBadSignatureRollsBackNonce", "testExpiredDeadlineLeavesNonceUnused",
                "testDeadlineAtTimestampReachesSignatureCheck", "testReusedNonceRejected",
                "testBadCloseSignatureRollsBackNonce", "testExpiredCloseDeadlineLeavesNonceUnused",
                "testReusedCloseNonceRejected", "testOutsiderCloseRejectedBeforeNonce",
                "testBadOpenSignatureRollsBackNonce", "testExpiredOpenDeadlineLeavesNonceUnused",
                "testReusedOpenNonceRejected", "testOutsiderOpenRejectedBeforeNonce",
                "testOutsiderWithdrawalReachesSignatureCheck", "testCloseBatchCallerDependsOnSlot88",
                "testWrongValidWithdrawalSignerRollsBackNonce",
                "testValidWithdrawalPersistsNonceAndDebits",
                "testSignedAmountMismatchRollsBack", "testSignedNonceMismatchRollsBack",
                "testSignedDeadlineMismatchRollsBack", "testSignedUserMismatchRollsBack",
                "testValidWithdrawalReplayRejectedNextBlock",
                "testValidSignatureAllowsOutsiderRelayer",
                "testWrongDomainWithdrawalSignatureRollsBack",
                "testFourPositionCloseDigestAcceptsSessionSigner",
                "testFourthCloseIdMutationRejectsSessionSignature",
                "testValidOpenSignatureReachesPostSignerRevert"}
    if run.returncode or set(passed) != expected:
        raise RuntimeError("signed intent replay failed: " + output[-9000:])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "runtime_hashes": {label: manifest["contracts"][address]["sha256"] for label, address in
                           (("ExchangeProxy", EXCHANGE), ("ExchangeImpl", EXCHANGE_IMPL),
                            ("SessionProxy", SESSION), ("SessionImpl", SESSION_IMPL))},
        "session_direct_slots": {str(k): v for k, v in SESSION_DIRECT_SLOTS.items()},
        "session_direct_slots_source": "eth_getStorageAt at pinned block",
        "exchange_batch_caller_slot_88": EXCHANGE_BATCH_CALLER_SLOT_88,
        "exchange_batch_caller_slot_88_source": "eth_getStorageAt at pinned block",
        "exchange_direct_slots_sha256": hashlib.sha256((ROOT / "artifacts" / "exchange_direct_status_local"
                                                           / "pinned_direct_slots.json").read_bytes()).hexdigest(),
        "synthetic_user": "0xe05fcc23807536bee418f142d19fa0d21bb0cff7",
        "synthetic_session_signer": "0x0376aac07ad725e01357b1725b5cec61ae10473c",
        "synthetic_nonce": 42,
        "synthetic_signature": "zeroed failure cases plus locally generated ECDSA signatures; no saved user signature exported",
        "mock_hypercore": "status one; spot balance 10^12 Core raw units; recording CoreWriter",
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "forge_result": f"{len(expected)} passed, 0 failed", "test_names": passed,
        "test_count": len(expected),
        "tested_exchange_selectors": {"open": "0xec6783f0", "close": "0x2792e706",
                                      "withdrawal": "0x8d09f23f"},
        "observed_errors": {"invalid_withdrawal_signature": "0xc20280ea",
                            "invalid_open_or_close_session_signer": "0xc5045f22",
                            "expired_deadline": "0xf87d9271", "reused_nonce": "0x756688fe",
                            "unauthorized_open_or_close_caller": "0xda96f0b6"},
        "observed_nonce_rollback_after_bad_signature": ["open", "close", "withdrawal"],
        "wrong_valid_withdrawal_signer_rejected_and_nonce_rolled_back": True,
        "outsider_signed_withdrawal_reaches_signature_check": True,
        "close_batch_caller_controlled_by_exchange_slot_88": True,
        "deadline_equal_to_timestamp_reaches_signature_check": True,
        "valid_withdrawal_persists_nonce_and_debits_balances": True,
        "valid_withdrawal_replay_rejected_after_next_block": True,
        "valid_withdrawal_outsider_relayer_allowed": True,
        "withdrawal_field_mismatches_rejected": ["user", "amount", "nonce", "deadline", "domain"],
        "four_position_close_call_succeeds_with_empty_synthetic_positions": True,
        "fourth_close_id_mutation_rejected_and_nonce_rolled_back": True,
        "valid_open_signature_post_signer_error": "0x0a4f5a07",
    }, indent=2) + "\n")
    print(f"{len(expected)} local exact-runtime signed intent tests passed")


if __name__ == "__main__":
    main()
