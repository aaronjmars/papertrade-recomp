// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

import "./Pt01Recovery.sol";

interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function roll(uint256) external;
    function warp(uint256) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function clearMockedCalls() external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function parseJsonUint(string calldata, string calldata) external pure returns (uint256);
    function toString(uint256) external pure returns (string memory);
    function snapshot() external returns (uint256);
    function revertTo(uint256) external returns (bool);
}

contract RecoveryWriter {
    bytes public lastAction;
    uint256 public calls;
    bool public fail;

    function setFail(bool value) external { fail = value; }

    function sendRawAction(bytes calldata action) external {
        require(!fail, "writer failed");
        lastAction = action;
        calls++;
    }
}

contract Pt01RecoveryTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address private constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address private constant LIVE = address(uint160(uint256(0x000a44049dbbb6b4762a6ba37aa0f7548c0b4a3723)));
    address private constant OLD = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    address private constant MULTISIG = address(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)));
    address private constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address private constant TIMELOCK = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address private constant SIGNER1 = address(uint160(uint256(0x00aa7577a7a27aa7fcf6d0ec481b87df3ad0f6a88e)));
    address private constant SIGNER2 = address(uint160(uint256(0x00e9686c8e11d80c8d78736485fcb6b6d7f4d7692e)));
    address private constant SIGNER3 = address(uint160(uint256(0x009028f3b5b6b0d69e4e84ff555ade17114c3d1e72)));
    address private constant FACTORY = address(uint160(uint256(0x001629b7d46bef6e13ff754174fc9f32dea309b38f)));
    address private constant WRITER = address(0x3333333333333333333333333333333333333333);
    address private constant USER1 = address(uint160(uint256(0x0056cbe78a5cdfa10147927aec550aa7f2fb3d3d01)));
    address private constant USER2 = address(uint160(uint256(0x009c8599c32224d7d9956a7def18f7314162f77baf)));
    address private constant PROXY1 = address(uint160(uint256(0x001e8a704179cc6221592c362daa52a341ae20084d)));
    address private constant PROXY2 = address(uint160(uint256(0x00f6b60cdf359af5538495831a9f2bbcada23e10e6)));
    bytes32 private constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 private constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 private constant ACTIVE_SLOT = bytes32(uint256(keccak256("papertrade.pt01.rescue.active.v1")) - 1);
    bytes4 private constant PENDING_SWEEP_WORD = 0x7e4174fc;
    bytes4 private constant GET_PENDING_SWEEP = 0x31a4956c;
    bytes4 private constant RECONCILE_SWEEP_CREDIT = 0x6a3214c9;
    /// @dev A selector neither the proxy nor the live implementation defines. 0x5c60da1b
    ///      (implementation()) is not usable as this reference: the proxy answers it itself
    ///      for a non-admin caller with its own four-byte error, not the implementation's
    ///      empty fallback revert.
    bytes4 private constant UNKNOWN_SELECTOR = 0xdeadbeef;
    uint64 private constant SPOT1 = 5_005_091_600;
    uint64 private constant SPOT2 = 1_210_000_000;
    uint64 private constant RESERVE = 100_000_000;

    string private words;
    address private recovery;

    function w(string memory key) private view returns (uint256) {
        return vm.parseJsonUint(words, string.concat(".", key));
    }

    function load(string memory slotKey) private view returns (bytes32) {
        return vm.load(EXCHANGE, bytes32(w(slotKey)));
    }

    function setUp() public {
        words = vm.readFile("runtime/live_words.json");
        require(w("exchange") == uint256(uint160(EXCHANGE)), "fixture exchange");
        require(w("implementation") == uint256(uint160(LIVE)), "fixture live implementation");
        require(w("implementationSlot") == uint256(IMPL_SLOT), "implementation slot");
        require(w("adminSlot") == uint256(ADMIN_SLOT), "admin slot");
        require(w("proxyAdmin") == uint256(uint160(ADMIN)), "proxy admin");
        require(w("timelock") == uint256(uint160(TIMELOCK)), "timelock");
        require(w("multisig") == uint256(uint160(MULTISIG)), "multisig");
        require(w("multisigSlot0") == uint256(uint160(SIGNER1)), "signer 1");
        require(w("multisigSlot1") == uint256(uint160(SIGNER2)), "signer 2");
        require(w("multisigSlot2") == uint256(uint160(SIGNER3)), "signer 3");
        require(w("timelockMinDelay") == 86_400, "live governance delay");
        require(w("timelockOwnerSlot0") == uint256(uint160(MULTISIG)), "timelock owner");
        require(w("adminOwnerSlot0") == uint256(uint160(TIMELOCK)), "admin owner");
        require(w("exchangeSlot0") == (uint256(uint160(TIMELOCK)) << 16) | 1, "exchange owner word");
        require(w("activeSlot") == uint256(ACTIVE_SLOT), "active slot");
        require(w("activeValue") == 0, "active slot is empty on live storage");
        require(uint64(w("pendingWordUser1")) == SPOT1, "user 1 pending amount");
        require(uint64(w("pendingWordUser2")) == SPOT2, "user 2 pending amount");
        require(w("balanceWordUser1") == w("balanceWordUser2") , "user balances");
        require(w("balanceWordUser1") == 0, "user balances are zero live");

        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(LIVE, vm.parseBytes(vm.readFile("runtime/LiveImplementation.hex")));
        vm.etch(OLD, vm.parseBytes(vm.readFile("runtime/OldImplementation.hex")));
        vm.etch(MULTISIG, vm.parseBytes(vm.readFile("runtime/Multisig.hex")));
        vm.etch(TIMELOCK, vm.parseBytes(vm.readFile("runtime/Timelock.hex")));
        vm.etch(ADMIN, vm.parseBytes(vm.readFile("runtime/ProxyAdmin.hex")));
        vm.etch(PROXY1, vm.parseBytes(vm.readFile("runtime/UserProxy1.hex")));
        vm.etch(PROXY2, vm.parseBytes(vm.readFile("runtime/UserProxy2.hex")));
        RecoveryWriter writer = new RecoveryWriter();
        vm.etch(WRITER, address(writer).code);

        // Live non-mapping storage, read from the public RPC capture.
        for (uint256 index; index < 32; index++) {
            vm.store(EXCHANGE, bytes32(index), bytes32(w(string.concat("exchangeSlot", vm.toString(index)))));
        }
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(LIVE))));
        vm.store(EXCHANGE, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(EXCHANGE, ACTIVE_SLOT, bytes32(w("activeValue")));
        vm.store(ADMIN, bytes32(0), bytes32(w("adminOwnerSlot0")));
        vm.store(TIMELOCK, bytes32(0), bytes32(w("timelockOwnerSlot0")));
        vm.store(TIMELOCK, bytes32(uint256(1)), bytes32(w("timelockMinDelay")));
        for (uint256 index; index < 5; index++) {
            vm.store(MULTISIG, bytes32(index), bytes32(w(string.concat("multisigSlot", vm.toString(index)))));
        }
        _seed(1);
        _seed(2);

        vm.roll(w("pinBlock"));
        vm.warp(w("pinTimestamp"));

        recovery = address(new Pt01Recovery());
        vm.prank(TIMELOCK);
        (bool ok,) = ADMIN.call(abi.encodeWithSignature("upgrade(address,address)", EXCHANGE, recovery));
        require(ok && vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(recovery))), "upgrade");
    }

    function _seed(uint256 index) private {
        vm.store(EXCHANGE, bytes32(w(string.concat("pendingSlotUser", vm.toString(index)))),
            bytes32(w(string.concat("pendingWordUser", vm.toString(index)))));
        vm.store(EXCHANGE, bytes32(w(string.concat("lastSweepSlotUser", vm.toString(index)))),
            bytes32(w(string.concat("lastSweepWordUser", vm.toString(index)))));
        vm.store(EXCHANGE, bytes32(w(string.concat("balanceSlotUser", vm.toString(index)))),
            bytes32(w(string.concat("balanceWordUser", vm.toString(index)))));
    }

    function _mock(address user, address proxy, uint64 spot) private {
        vm.mockCall(FACTORY, abi.encodeWithSelector(bytes4(0xc1a9a508), user), abi.encode(proxy));
        vm.mockCall(address(0x801), abi.encode(proxy, uint64(0)), abi.encode(uint256(spot), uint256(0), uint256(0)));
        vm.mockCall(address(0x803), bytes(""), abi.encode(uint256(0)));
    }

    function _enqueue(address user, address proxy, uint64 spot) private {
        _mock(user, proxy, spot);
        vm.prank(TIMELOCK);
        (bool ok, bytes memory output) = EXCHANGE.call(abi.encodeWithSignature("rescueEnqueue(address)", user));
        require(ok && output.length == 0, "enqueue");
    }

    /// @dev The candidate's assumed storage keys, proved against the live-derived slots.
    function _keys(address user) private view returns (uint256 pendingSlot, uint256 lastSweepSlot, uint256 balanceSlot) {
        bool first = user == USER1;
        pendingSlot = w(first ? "pendingSlotUser1" : "pendingSlotUser2");
        lastSweepSlot = w(first ? "lastSweepSlotUser1" : "lastSweepSlotUser2");
        balanceSlot = w(first ? "balanceSlotUser1" : "balanceSlotUser2");
    }

    function _checkQueued(address user, address proxy, uint64 spot, uint256 mask) private view {
        (uint256 pendingSlot, uint256 lastSweepSlot,) = _keys(user);
        require(keccak256(abi.encode(user, uint256(33))) == bytes32(pendingSlot), "pending slot key");
        require(keccak256(abi.encode(proxy, uint256(32))) == bytes32(lastSweepSlot), "last sweep slot key");
        uint64 amount = spot - RESERVE;
        uint256 pin = w("pinBlock");
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(mask), "active bit");
        require(uint256(vm.load(EXCHANGE, bytes32(pendingSlot))) == uint256(amount) | (pin << 128), "pending amount");
        require(uint256(vm.load(EXCHANGE, bytes32(lastSweepSlot))) == pin, "last block");
        require(RecoveryWriter(WRITER).calls() == 1, "writer call count");
        bytes memory action = RecoveryWriter(WRITER).lastAction();
        require(action.length == 100 && bytes4(action) == bytes4(0x01000006), "action header");
        bytes memory data = new bytes(96);
        for (uint256 i; i < 96; i++) data[i] = action[i + 4];
        (address recipient, uint64 token, uint64 sent) = abi.decode(data, (address, uint64, uint64));
        require(recipient == EXCHANGE && token == 0 && sent == amount, "action amount");
    }

    function testEnqueueFirst() public {
        _enqueue(USER1, PROXY1, SPOT1);
        _checkQueued(USER1, PROXY1, SPOT1, 1);
    }

    function testEnqueueSecond() public {
        _enqueue(USER2, PROXY2, SPOT2);
        _checkQueued(USER2, PROXY2, SPOT2, 2);
    }

    function testUnauthorizedAndUnknownUser() public {
        _mock(USER1, PROXY1, SPOT1);
        (bool unauthorized,) = EXCHANGE.call(abi.encodeWithSignature("rescueEnqueue(address)", USER1));
        require(!unauthorized, "unauthorized enqueue");
        vm.prank(TIMELOCK);
        (bool unknown,) = EXCHANGE.call(abi.encodeWithSignature("rescueEnqueue(address)", address(0x1234)));
        require(!unknown, "unknown user");
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(0), "no active bit");
    }

    function testChangedBalanceCannotEnqueue() public {
        _mock(USER1, PROXY1, SPOT1 - 1);
        vm.prank(TIMELOCK);
        (bool ok,) = EXCHANGE.call(abi.encodeWithSignature("rescueEnqueue(address)", USER1));
        require(!ok && vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(0), "balance guard");
    }

    function testWriterFailureRollsBack() public {
        _mock(USER1, PROXY1, SPOT1);
        RecoveryWriter(WRITER).setFail(true);
        vm.prank(TIMELOCK);
        (bool ok,) = EXCHANGE.call(abi.encodeWithSignature("rescueEnqueue(address)", USER1));
        require(!ok, "writer failure");
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(0), "active rollback");
        require(load("pendingSlotUser1") == bytes32(w("pendingWordUser1")), "pending rollback");
    }

    function testSweeperBlockedWhileActive() public {
        _enqueue(USER1, PROXY1, SPOT1);
        bytes4[4] memory selectors = [bytes4(0x01681a62), bytes4(0xe0189108), bytes4(0x6d142da1), bytes4(0x6a3214c9)];
        for (uint256 i; i < selectors.length; i++) {
            bytes memory expected = abi.encodeWithSignature("Error(string)", "PT01: recovery active");
            (bool ok, bytes memory result) = EXCHANGE.call(abi.encodeWithSelector(selectors[i], USER1));
            require(!ok && keccak256(result) == keccak256(expected), "sweeper blocked");
            (ok, result) = EXCHANGE.call(abi.encodePacked(abi.encodeWithSelector(selectors[i], USER1), bytes32(0)));
            require(!ok && keccak256(result) == keccak256(expected), "padded sweeper blocked");
        }
        require(RecoveryWriter(WRITER).calls() == 1, "no repeat send");
    }

    /// @dev The live set-2 sweep path clears the pending word outright when the observed
    ///      balance is at its dust threshold, without calling the deposit proxy. While
    ///      recovery is active the candidate must keep that branch unreachable for the
    ///      affected user, and the pending word the candidate wrote must survive.
    function testLiveDustBranchCannotClearWhileActive() public {
        _enqueue(USER1, PROXY1, SPOT1);
        (uint256 pendingSlot,,) = _keys(USER1);
        bytes32 queued = vm.load(EXCHANGE, bytes32(pendingSlot));
        require(queued != 0, "candidate queued a pending word");
        vm.clearMockedCalls();
        _mock(USER1, PROXY1, 100_000_000);

        uint256 snap = vm.snapshot();
        vm.roll(w("pinBlock") + 1);
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(LIVE))));
        vm.prank(TIMELOCK);
        (bool reachable,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x01681a62), USER1));
        require(reachable && vm.load(EXCHANGE, bytes32(pendingSlot)) == 0,
            "the live dust branch clears the pending word when it is reachable");
        vm.revertTo(snap);

        _mock(USER1, PROXY1, 100_000_000);
        vm.roll(w("pinBlock") + 1);
        bytes memory expected = abi.encodeWithSignature("Error(string)", "PT01: recovery active");
        vm.prank(TIMELOCK);
        (bool ok, bytes memory data) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x01681a62), USER1));
        require(!ok && keccak256(data) == keccak256(expected), "dust branch blocked while active");
        require(vm.load(EXCHANGE, bytes32(pendingSlot)) == queued, "queued pending word preserved");
    }

    function testRejectedCoreSendCannotCredit() public {
        _enqueue(USER2, PROXY2, SPOT2);
        uint256 beforeBalance = uint256(load("balanceSlotUser2"));
        vm.roll(w("pinBlock") + 1);
        vm.prank(TIMELOCK);
        (bool ok,) = EXCHANGE.call(abi.encodeWithSignature("rescueFinalize(address)", USER2));
        require(!ok, "unchanged Core balance rejects finalization");
        require(uint256(load("balanceSlotUser2")) == beforeBalance, "no credit");
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(uint256(2)), "still active");
    }

    function testResidualCannotBeCreditedEarly() public {
        _enqueue(USER1, PROXY1, SPOT1);
        vm.clearMockedCalls();
        _mock(USER1, PROXY1, RESERVE);
        vm.roll(w("pinBlock") + 1);
        vm.prank(TIMELOCK);
        (bool ok,) = EXCHANGE.call(abi.encodeWithSignature("rescueFinalize(address)", USER1));
        require(!ok, "residual blocks credit");
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(uint256(1)), "still active");
    }

    function testResidualWriterFailureRollsBack() public {
        _enqueue(USER1, PROXY1, SPOT1);
        vm.clearMockedCalls();
        _mock(USER1, PROXY1, RESERVE);
        RecoveryWriter(WRITER).setFail(true);
        vm.roll(w("pinBlock") + 1);
        vm.prank(TIMELOCK);
        (bool ok,) = EXCHANGE.call(abi.encodeWithSignature("rescueEnqueueResidual(address)", USER1));
        require(!ok, "residual writer failure");
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(uint256(1)), "phase rollback");
        require(uint64(uint256(load("pendingSlotUser1"))) == SPOT1 - RESERVE, "pending rollback");
        require(RecoveryWriter(WRITER).calls() == 1, "no residual action");
    }

    function _delivered(address user, address proxy, uint64 spot, uint64 residual) private {
        _enqueue(user, proxy, spot);
        (uint256 pendingSlot, uint256 lastSweepSlot, uint256 balanceSlot) = _keys(user);
        require(keccak256(abi.encode(user, uint256(33))) == bytes32(pendingSlot), "pending slot key");
        require(keccak256(abi.encode(proxy, uint256(32))) == bytes32(lastSweepSlot), "last sweep slot key");
        require(keccak256(abi.encode(user, uint256(9))) == bytes32(balanceSlot), "balance slot key");
        _checkQueued(user, proxy, spot, user == USER1 ? 1 : 2);
        vm.clearMockedCalls();
        _mock(user, proxy, residual);
        vm.roll(w("pinBlock") + 1);
        if (residual == RESERVE) {
            vm.prank(TIMELOCK);
            (bool queued,) = EXCHANGE.call(abi.encodeWithSignature("rescueEnqueueResidual(address)", user));
            require(queued, "residual queued");
            require(uint64(uint256(vm.load(EXCHANGE, bytes32(pendingSlot)))) == RESERVE, "residual pending");
            require(RecoveryWriter(WRITER).calls() == 2, "second writer call");
            vm.clearMockedCalls();
            _mock(user, proxy, 0);
            vm.roll(w("pinBlock") + 2);
        }
        vm.prank(TIMELOCK);
        (bool ok, bytes memory output) = EXCHANGE.call(abi.encodeWithSignature("rescueFinalize(address)", user));
        require(ok && output.length == 0, "finalize");
        uint256 credit = uint256(residual == RESERVE ? spot : spot - RESERVE) * 1e10;
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(0), "inactive");
        require(vm.load(EXCHANGE, bytes32(pendingSlot)) == bytes32(0), "pending cleared");
        require(uint256(vm.load(EXCHANGE, bytes32(balanceSlot))) == credit, "user credited");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == uint256(w("exchangeSlot14")) + credit, "treasury credited");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) == uint256(w("exchangeSlot22")) + credit, "total credited");
        require(RecoveryWriter(WRITER).calls() == (residual == RESERVE ? 2 : 1), "writer count");
        vm.prank(TIMELOCK);
        (bool again,) = EXCHANGE.call(abi.encodeWithSignature("rescueFinalize(address)", user));
        require(!again, "exactly once");
    }

    function testFirstDeliveredWithFee() public { _delivered(USER1, PROXY1, SPOT1, 0); }
    function testFirstDeliveredWithoutFee() public { _delivered(USER1, PROXY1, SPOT1, RESERVE); }
    function testSecondDeliveredWithFee() public { _delivered(USER2, PROXY2, SPOT2, 0); }
    function testSecondDeliveredWithoutFee() public { _delivered(USER2, PROXY2, SPOT2, RESERVE); }

    function testFallbackGetterParity() public {
        bytes memory callData = abi.encodeWithSignature("pendingSweepWord(address)", USER1);
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(LIVE))));
        (bool okBefore, bytes memory beforeData) = EXCHANGE.call(callData);
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(recovery))));
        (bool okAfter, bytes memory afterData) = EXCHANGE.call(callData);
        require(okBefore && okAfter && keccak256(beforeData) == keccak256(afterData), "getter fallback parity");
        require(abi.decode(beforeData, (uint256)) == w("pendingWordUser1"), "live getter value");
    }

    /// @dev Any delegate to the retired implementation now reverts, so ordinary calls that
    ///      still succeed prove the fallback targets the live implementation.
    function testDelegatesToLiveImplementation() public {
        vm.etch(OLD, hex"60006000fd");
        (bool ok, bytes memory data) = EXCHANGE.call(abi.encodeWithSelector(PENDING_SWEEP_WORD, USER1));
        require(ok, "live delegation");
        require(abi.decode(data, (uint256)) == w("pendingWordUser1"), "live getter value");
    }

    /// @dev Poisoning the live implementation must break ordinary calls: nothing else serves them.
    function testLiveImplementationIsTheDelegateTarget() public {
        vm.etch(LIVE, hex"60006000fd");
        (bool ok,) = EXCHANGE.call(abi.encodeWithSelector(PENDING_SWEEP_WORD, USER1));
        require(!ok, "poisoned live implementation must break ordinary calls");
        vm.etch(OLD, hex"60006000fd");
        (ok,) = EXCHANGE.call(abi.encodeWithSelector(PENDING_SWEEP_WORD, USER1));
        require(!ok, "the retired implementation is not a fallback either");
    }

    /// @dev A raw call whose outcome is recorded only through the surrounding assertions.
    function _probe(bytes memory callData) private {
        (bool ok, bytes memory result) = EXCHANGE.call(callData);
        ok;
        result;
    }

    /// @dev The live dispatcher gained six selectors and has no pending-sweep clear route:
    ///      none of them may move any pending, balance or active word for a third party or an
    ///      affected user. Owner-gated entries are probed from non-owner callers, so a gate
    ///      cannot hide a state change.
    function testLiveAddedSelectorsLeaveRecoveryStateAlone() public {
        uint256 count = w("addedSelectorCount");
        for (uint256 index; index < count; index++) {
            bytes4 selector = bytes4(bytes32(w(string.concat("addedSelector", vm.toString(index)))));
            for (uint256 shape; shape < 3; shape++) {
                bytes memory callData = abi.encodePacked(
                    selector,
                    bytes32(uint256(uint160(USER1))),
                    bytes32(uint256(shape)));
                vm.prank(WRITER);
                _probe(callData);
                vm.prank(USER2);
                _probe(callData);
            }
            require(load("pendingSlotUser1") == bytes32(w("pendingWordUser1")), "user 1 pending untouched");
            require(load("pendingSlotUser2") == bytes32(w("pendingWordUser2")), "user 2 pending untouched");
            require(load("lastSweepSlotUser1") == bytes32(w("lastSweepWordUser1")), "user 1 sweep block untouched");
            require(load("lastSweepSlotUser2") == bytes32(w("lastSweepWordUser2")), "user 2 sweep block untouched");
            require(load("balanceSlotUser1") == 0 && load("balanceSlotUser2") == 0, "no credit to either user");
            require(vm.load(EXCHANGE, ACTIVE_SLOT) == 0, "active slot untouched");
        }
    }

    /// @dev Hash-checked absence: no live route clears a pending sweep. Every named clear or
    ///      reconciliation preimage reverts exactly like an undefined selector, even for the owner.
    function testLiveImplementationHasNoPendingSweepClearRoute() public {
        vm.prank(TIMELOCK);
        (bool undefinedOk, bytes memory undefinedRevert) = EXCHANGE.call(abi.encodeWithSelector(UNKNOWN_SELECTOR));
        require(!undefinedOk, "undefined selector reference");
        bytes4[13] memory absent = [
            bytes4(0x2362f4de), // clearPendingSweep(address)
            bytes4(0x9a7f1729), // clearPendingSweeps(address)
            bytes4(0x1db3a6f0), // clearPendingSweep(address,uint256)
            bytes4(0xd6c3f90a), // cancelPendingSweep(address)
            bytes4(0x9a3fbad6), // setPendingSweep(address,uint256)
            bytes4(0xb7bf46af), // adminSweep(address)
            bytes4(0xff55eda1), // forceSweep(address)
            bytes4(0xff512968), // rescueSweep(address)
            bytes4(0xd3df89c2), // retrySweep(address)
            bytes4(0xc18cfe86), // sweepAll(address)
            bytes4(0xa2a3fbc6), // sweepBatch(address[])
            bytes4(0x24681c5a), // clearSweep(address)
            bytes4(0x954ab7d3)  // approveSweep(address)
        ];
        for (uint256 index; index < absent.length; index++) {
            bytes[2] memory shapes = [
                abi.encodeWithSelector(absent[index], USER1),
                abi.encodeWithSelector(absent[index], USER1, uint256(0))
            ];
            for (uint256 shape; shape < shapes.length; shape++) {
                vm.prank(TIMELOCK);
                (bool ok, bytes memory result) = EXCHANGE.call(shapes[shape]);
                require(!ok && keccak256(result) == keccak256(undefinedRevert), "no such route");
            }
        }
        require(load("pendingSlotUser1") == bytes32(w("pendingWordUser1")), "pending untouched");
    }

    /// @dev The candidate assumes the pending word layout the live implementation itself reads.
    function testLivePendingLayoutMatchesGetPendingSweep() public {
        uint256 raw1 = w("pendingWordUser1");
        uint256 raw2 = w("pendingWordUser2");
        _checkPendingShape(USER1, raw1);
        _checkPendingShape(USER2, raw2);
    }

    /// @dev The live `getPendingSweep(address)` returns four words: a flag, the amount, a zero
    ///      word, and the request block. All four must agree with the raw pending word.
    function _checkPendingShape(address user, uint256 raw) private {
        (bool ok, bytes memory data) = EXCHANGE.call(abi.encodeWithSelector(GET_PENDING_SWEEP, user));
        require(ok && data.length == 128, "getPendingSweep");
        (uint256 exists, uint256 amount, uint256 reserved, uint256 requestBlock) =
            abi.decode(data, (uint256, uint256, uint256, uint256));
        require(exists == 1, "pending flag");
        require(amount == uint64(raw), "pending amount layout");
        require(reserved == 0, "pending reserved word");
        require(requestBlock == uint32(raw >> 128), "pending request block layout");
        require(raw >> 64 & type(uint64).max == 0, "pending middle bits empty");
        require(raw >> 160 == 0, "pending high bits empty");
    }

    /// @dev The live implementation's reconciliation, called exactly as the candidate calls it
    ///      (pending word already cleared), must move exactly the three expected words.
    function testLiveReconcileCreditsExactlyThePinnedDeltas() public {
        uint256 balanceSlot = w("balanceSlotUser1");
        uint256 before = uint256(vm.load(EXCHANGE, bytes32(balanceSlot)));
        uint256 treasury = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        uint256 totals = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        vm.store(EXCHANGE, bytes32(w("pendingSlotUser1")), bytes32(0));
        vm.prank(TIMELOCK);
        (bool ok, bytes memory result) = EXCHANGE.call(
            abi.encodeWithSelector(RECONCILE_SWEEP_CREDIT, USER1, uint256(49_050_916)));
        require(ok && result.length == 0, "live reconcile call");
        uint256 credit = uint256(4_905_091_600) * 1e10;
        require(uint256(vm.load(EXCHANGE, bytes32(balanceSlot))) == before + credit, "user credit delta");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) == treasury + credit, "treasury delta");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) == totals + credit, "total delta");
    }

    function _multisigCall(bytes memory data) private {
        vm.prank(SIGNER1);
        (bool submitted, bytes memory indexBytes) = MULTISIG.call(
            abi.encodeWithSignature("submitTransaction(address,uint256,bytes)", TIMELOCK, 0, data)
        );
        require(submitted && indexBytes.length == 32, "multisig submit");
        uint256 index = abi.decode(indexBytes, (uint256));
        (bool hashed, bytes memory hashBytes) = MULTISIG.staticcall(
            abi.encodeWithSignature("transactionHash(uint256)", index)
        );
        require(hashed && hashBytes.length == 32, "multisig hash");
        vm.prank(SIGNER2);
        (bool confirmed,) = MULTISIG.call(
            abi.encodeWithSignature("confirmAndExecute(uint256,bytes32)", index, abi.decode(hashBytes, (bytes32)))
        );
        require(confirmed, "multisig confirm");
    }

    function _schedule(address target, bytes memory data) private {
        _multisigCall(abi.encodeWithSignature("schedule(address,uint256,bytes,bytes32)", target, 0, data, bytes32(0)));
        bytes32 id = keccak256(abi.encode(target, uint256(0), keccak256(data), bytes32(0)));
        bytes32 slot = keccak256(abi.encode(id, uint256(2)));
        require(uint256(vm.load(TIMELOCK, slot)) == w("pinTimestamp") + w("timelockMinDelay"), "operation ready");
    }

    function _execute(address target, bytes memory data) private {
        _multisigCall(abi.encodeWithSignature("execute(address,uint256,bytes,bytes32)", target, 0, data, bytes32(0)));
    }

    function testGovernedUpgradeAndRecovery() public {
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(LIVE))));
        bytes memory upgrade = abi.encodeWithSignature("upgrade(address,address)", EXCHANGE, recovery);
        bytes memory enqueue = abi.encodeWithSignature("rescueEnqueue(address)", USER2);
        bytes memory finalize = abi.encodeWithSignature("rescueFinalize(address)", USER2);
        _schedule(ADMIN, upgrade);
        _schedule(EXCHANGE, enqueue);
        _schedule(EXCHANGE, finalize);
        vm.warp(w("pinTimestamp") + w("timelockMinDelay") - 1);
        vm.prank(SIGNER1);
        (bool early,) = TIMELOCK.call(
            abi.encodeWithSignature("execute(address,uint256,bytes,bytes32)", ADMIN, 0, upgrade, bytes32(0))
        );
        require(!early && vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(LIVE))), "early upgrade blocked");
        vm.warp(w("pinTimestamp") + w("timelockMinDelay"));
        _execute(ADMIN, upgrade);
        require(vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(recovery))), "governed upgrade");
        _mock(USER2, PROXY2, SPOT2);
        _execute(EXCHANGE, enqueue);
        _checkQueued(USER2, PROXY2, SPOT2, 2);
        vm.clearMockedCalls();
        _mock(USER2, PROXY2, 0);
        vm.roll(w("pinBlock") + 1);
        _execute(EXCHANGE, finalize);
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(0), "governed finalize");
        require(uint256(load("balanceSlotUser2")) == uint256(SPOT2 - RESERVE) * 1e10, "governed credit");
    }

    function testBothUsersThenRestoreOriginal() public {
        _enqueue(USER2, PROXY2, SPOT2);
        _enqueue(USER1, PROXY1, SPOT1);
        require(vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(uint256(3)), "both active");
        require(RecoveryWriter(WRITER).calls() == 2, "both sends queued");
        vm.clearMockedCalls();
        _mock(USER1, PROXY1, 0);
        _mock(USER2, PROXY2, 0);
        vm.roll(w("pinBlock") + 1);
        vm.prank(TIMELOCK);
        (bool small,) = EXCHANGE.call(abi.encodeWithSignature("rescueFinalize(address)", USER2));
        require(small && vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(uint256(1)), "small finalized");
        vm.prank(TIMELOCK);
        (bool large,) = EXCHANGE.call(abi.encodeWithSignature("rescueFinalize(address)", USER1));
        require(large && vm.load(EXCHANGE, ACTIVE_SLOT) == bytes32(0), "large finalized");
        vm.prank(TIMELOCK);
        (bool restored,) = ADMIN.call(abi.encodeWithSignature("upgrade(address,address)", EXCHANGE, OLD));
        require(restored && vm.load(EXCHANGE, IMPL_SLOT) == bytes32(uint256(uint160(OLD))), "pinned implementation restored");
        (bool getter, bytes memory pending) = EXCHANGE.call(abi.encodeWithSignature("pendingSweepWord(address)", USER1));
        require(getter && abi.decode(pending, (uint256)) == 0, "restored getter");
    }
}