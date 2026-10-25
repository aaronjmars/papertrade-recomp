// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

// Port-free exact-runtime harness for the set-2 (post-pin) authority surface.
// Every runtime is the saved byte string under ./runtime, injected with vm.etch; every storage
// word is written with vm.store from a captured value. No transaction is broadcast, no RPC is
// contacted, and HyperCore is never called (no test reaches a precompile read on a success path).

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function startPrank(address) external;
    function stopPrank() external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external view returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function expectRevert(bytes calldata) external;
}

contract AuthorityLocalTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;

    // ------------------------------------------------------------------ addresses (live / captured)
    address constant EXCHANGE_IMPL2 = address(uint160(uint256(0x000a44049dbbb6b4762a6ba37aa0f7548c0b4a3723)));
    address constant SKM_IMPL2       = address(uint160(uint256(0x0004b5ea4cdd8d6de4bd6e0ef3865266947f043946)));
    address constant TOKENOMICS_IMPL2= address(uint160(uint256(0x007c0a72a788cff4d68cfe9586aecb98e21eb58a03)));
    address constant LIBRARY2        = address(uint160(uint256(0x00583d0bd818c991c5830fea93aef04e474b272459)));
    address constant BUILDER_REGISTRY= address(uint160(uint256(0x00fdc6550436dd75ce8a0b145f935b7d3a64f53248)));
    address constant PAPER_IMPL      = address(uint160(uint256(0x00433bd418ec92818a960585f4d5fae563e735bb4a)));
    address constant STAKING_IMPL    = address(uint160(uint256(0x00e6e3519455170913c5c3bfe541dd918a2d0cbb15)));
    address constant PROXY_ADMIN     = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant TIMELOCK        = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant MULTISIG        = address(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)));
    address constant SHARED_PROXY    = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant KEEPER          = address(uint160(uint256(0x000924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56)));
    address constant OUTSIDER        = address(uint160(uint256(0x00000000000000000000000000000000000000beef)));
    address constant BUILDER         = address(uint160(uint256(0x00000000000000000000000000000000000000b0b1)));
    address constant BUILDER2        = address(uint160(uint256(0x00000000000000000000000000000000000000b0b2)));
    address constant NEW_ADDR        = address(uint160(uint256(0x00000000000000000000000000000000000000c0fe)));

    // ------------------------------------------------------------------ selectors
    bytes4 constant SEL_OWNER                 = 0x8da5cb5b;
    bytes4 constant SEL_TRANSFER_OWNERSHIP    = 0xf2fde38b;
    bytes4 constant SEL_APPROVE_BUILDER       = 0x54dc2a02;
    bytes4 constant SEL_REMOVE_BUILDER        = 0xec969386;
    bytes4 constant SEL_IS_APPROVED           = 0x673448dd;
    bytes4 constant SEL_SET_FEE_RATE          = 0x459770f6;
    bytes4 constant SEL_FEE_RATE              = 0x978bbdb9;
    bytes4 constant SEL_FEE_RATE_OF           = 0xd779e270;
    bytes4 constant SEL_SET_GUARDIAN          = 0x8a0dac4a;
    bytes4 constant SEL_GUARDIAN              = 0x452a9320;
    bytes4 constant SEL_INSTRUMENT_COUNT      = 0xf28bbdb2;
    bytes4 constant SEL_NEW_FLAG_GET          = 0xf009ac03;
    bytes4 constant SEL_NEW_FLAG_SET          = 0xe6ac4a74;
    bytes4 constant SEL_NEW_ACCUM_GET         = 0xcbce7532;
    bytes4 constant SEL_NEW_OWNER_2ARG        = 0xd970fad5;
    bytes4 constant SEL_BUILDER_FEES          = 0x9d346583;
    bytes4 constant SEL_CLAIM_BUILDER_FEES    = 0x69f9a5f0;
    bytes4 constant SEL_SET_KEEPER            = 0xefc1bd46;
    bytes4 constant SEL_SET_BUILDER_REGISTRY  = 0xbd322efa;
    bytes4 constant SEL_BUILDER_REGISTRY_GET  = 0xe737de13;
    bytes4 constant SEL_SET_TRADING_PAUSED    = 0xae69b95b;
    bytes4 constant SEL_SET_PAUSE_GUARDIAN    = 0x48bde20c;
    bytes4 constant SEL_TRADING_PAUSED        = 0x53e23e2e;
    bytes4 constant SEL_PAUSE_GUARDIAN        = 0x24a3d622;
    bytes4 constant SEL_ACTIVATE_REBATE       = 0x85eb2a08;
    bytes4 constant SEL_INSOLVENT_SINCE       = 0x456db972;
    bytes4 constant SEL_TK_NEW_122B           = 0x122b6689;
    bytes4 constant SEL_TK_NEW_4EC7           = 0x4ec7182e;
    bytes4 constant SEL_TK_NEW_EEDF           = 0xeedf4c43;
    bytes4 constant SEL_PAPER_SET_MINTER      = 0xfca3b5aa;
    bytes4 constant SEL_PAPER_SET_STAKING     = 0x9dd373b9;
    bytes4 constant SEL_PAPER_SET_SPENDER     = 0xd311b1a9;
    bytes4 constant SEL_STAKING_SET_EXECUTOR  = 0xd188c049;
    bytes4 constant SEL_PA_UPGRADE            = 0x99a88ec4;
    bytes4 constant SEL_TL_EXECUTE            = 0x88aa4c12;
    bytes4 constant SEL_TL_UPDATE_MIN_DELAY   = 0x8a99d586;
    bytes4 constant SEL_MS_SUBMIT             = 0xc6427474;
    bytes4 constant SEL_MS_CONFIRM            = 0x7b1106de;

    // ------------------------------------------------------------------ topics / errors
    bytes32 constant TOPIC_OWNER_UPDATED      = 0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b;
    bytes32 constant TOPIC_GUARDIAN_UPDATED   = 0x6bb7ff33e730289800c62ad882105a144a74010d2bdbb9a942544a3005ad55bf;
    bytes32 constant TOPIC_FEE_RATE_UPDATED   = 0x208f1b468d3d61f0f085e975bd9d04367c930d599642faad06695229f3eadcd8;
    bytes32 constant TOPIC_BUILDER_APPROVED   = 0xccb37c7a8718a6d39a5bfc3a91871e203c2d2f7cddb83cb8cbd12c50e74974ec;
    bytes32 constant TOPIC_BUILDER_REMOVED    = 0xc5a4a43135540d5e0967677a1ed86bf147f7c0e7dd757a109f4cff74c945f92e;
    bytes32 constant TOPIC_NEW_FLAG_SET       = 0xd8f19a0212393b8c603ef0d47c77814e1dbfa1419aa70029ad7a857c18d6ee98;
    bytes32 constant TOPIC_CLAIM_BUILDER_FEES = 0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15;
    bytes4 constant ERR_NOT_OWNER             = 0x30cd7471;
    bytes4 constant ERR_ZERO_ADDRESS          = 0xd92e233d; // ZeroAddress()
    bytes4 constant ERR_FEE_TOO_HIGH          = 0xe30ce51e;
    bytes4 constant ERR_NOT_OWNER_OR_GUARDIAN = 0x2c49223e;
    bytes4 constant ERR_NOT_AUTHORIZED_CALLER = 0xda96f0b6;
    bytes4 constant ERR_NOT_PAUSE_AUTHORITY   = 0x49199fb6;
    bytes4 constant ERR_NOT_SELF              = 0x29c3b7ee;

    uint256 constant FEE_RATE_LIVE = 5 * 10 ** 15;   // 0.5 %, captured from feeRate()
    uint256 constant FEE_RATE_CAP  = 10 ** 16;       // 1 %, the constant compared in setFeeRate
    uint256 constant INSTRUMENT_COUNT = 42;
    bool constant FLAG_LIVE = true;

    // ------------------------------------------------------------------ setup
    function setUp() public {
        etch("Exchange2", EXCHANGE_IMPL2);
        etch("SessionKeyManager2", SKM_IMPL2);
        etch("Tokenomics2", TOKENOMICS_IMPL2);
        etch("Library2", LIBRARY2);
        etch("BuilderRegistry", BUILDER_REGISTRY);
        etch("PaperImplementation", PAPER_IMPL);
        etch("StakingImplementation", STAKING_IMPL);
        etch("ProxyAdmin", PROXY_ADMIN);
        etch("Timelock", TIMELOCK);
        etch("Multisig", MULTISIG);
        etch("SharedProxy", SHARED_PROXY);

        // Exchange (set-2 implementation address carries the runtime; storage written there)
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(0)), bytes32(uint256(uint160(TIMELOCK)) << 16));
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(88)), bytes32(uint256(uint160(NEW_ADDR))));
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(89)), bytes32(uint256(uint160(KEEPER))));
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(8)),
                 bytes32((uint256(FLAG_LIVE ? 1 : 0) << 32) | INSTRUMENT_COUNT));
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(38)), bytes32(uint256(uint160(NEW_ADDR))));

        // SessionKeyManager (set-2): slot 2 owner, slot 3 authorized caller, slot 8 builder registry
        vm.store(SKM_IMPL2, bytes32(uint256(2)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(SKM_IMPL2, bytes32(uint256(3)), bytes32(uint256(uint160(NEW_ADDR))));
        vm.store(SKM_IMPL2, bytes32(uint256(8)), bytes32(uint256(uint160(BUILDER_REGISTRY))));

        // Tokenomics (set-2): owner packed into slot 0 bits 16..175
        vm.store(TOKENOMICS_IMPL2, bytes32(uint256(0)), bytes32(uint256(uint160(TIMELOCK)) << 16));

        // BuilderRegistry: owner in slot 0, guardian + feeRate packed into slot 1
        vm.store(BUILDER_REGISTRY, bytes32(uint256(0)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(BUILDER_REGISTRY, bytes32(uint256(1)),
                 bytes32((FEE_RATE_LIVE << 160) | uint256(uint160(MULTISIG))));

        // PAPER: owner slot 3, minter slot 4, autoApprovedSpender slot 5, staking slot 9
        vm.store(PAPER_IMPL, bytes32(uint256(3)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(PAPER_IMPL, bytes32(uint256(4)), bytes32(uint256(uint160(TOKENOMICS_IMPL2))));
        vm.store(PAPER_IMPL, bytes32(uint256(5)), bytes32(uint256(uint160(STAKING_IMPL))));
        vm.store(PAPER_IMPL, bytes32(uint256(9)), bytes32(uint256(uint160(STAKING_IMPL))));

        // Staking: owner slot 15, packed authorized executor slot 16
        vm.store(STAKING_IMPL, bytes32(uint256(15)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(STAKING_IMPL, bytes32(uint256(16)), bytes32(uint256(uint160(NEW_ADDR))));

        // Timelock: owner slot 0, minDelay slot 1
        vm.store(TIMELOCK, bytes32(uint256(0)), bytes32(uint256(uint160(MULTISIG))));
        vm.store(TIMELOCK, bytes32(uint256(1)), bytes32(uint256(86400)));

        // ProxyAdmin owner
        vm.store(PROXY_ADMIN, bytes32(uint256(0)), bytes32(uint256(uint160(TIMELOCK))));

        // Shared proxy points at the set-2 Exchange implementation
        vm.store(SHARED_PROXY, IMPL_SLOT, bytes32(uint256(uint160(EXCHANGE_IMPL2))));
    }

    function etch(string memory name, address target) internal {
        bytes memory code = vm.parseBytes(vm.readFile(string.concat("runtime/", name, ".hex")));
        vm.etch(target, code);
    }

    // ------------------------------------------------------------------ helpers
    function callRaw(address to, bytes memory data, address from) internal returns (bool ok, bytes memory ret) {
        vm.prank(from);
        (ok, ret) = to.call(data);
    }

    function sel(bytes memory ret) internal pure returns (bytes4 s) {
        if (ret.length < 4) return bytes4(0);
        assembly { s := mload(add(ret, 32)) }
    }

    function enc1(bytes4 s, address a) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(s, a);
    }

    function encU(bytes4 s, uint256 v) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(s, v);
    }

    function feeWordOf(address who) internal view returns (bytes32) {
        return vm.load(EXCHANGE_IMPL2, keccak256(abi.encode(who, uint256(39))));
    }

    // ================================================================== BuilderRegistry

    function testBuilderRegistryOwnerGate() public {
        (bool ok, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_APPROVE_BUILDER, BUILDER), TIMELOCK);
        assertTrue(ok, "owner approveBuilder");
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, enc1(SEL_IS_APPROVED, BUILDER)), (bool)), true);
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, enc1(SEL_FEE_RATE_OF, BUILDER)), (uint256)), FEE_RATE_LIVE);

        // negative control: a non-owner cannot approve
        (bool ok2, bytes memory r2) = callRaw(BUILDER_REGISTRY, enc1(SEL_APPROVE_BUILDER, BUILDER2), OUTSIDER);
        assertFalse(ok2, "outsider approveBuilder must revert");
        expectSel(sel(r2), ERR_NOT_OWNER);
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, enc1(SEL_IS_APPROVED, BUILDER2)), (bool)), false);
        // feeRateOf of an unapproved address is zero even though a global rate is set
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, enc1(SEL_FEE_RATE_OF, OUTSIDER)), (uint256)), 0);

        // owner remove
        (bool ok3, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_REMOVE_BUILDER, BUILDER), TIMELOCK);
        assertTrue(ok3, "owner removeBuilder");
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, enc1(SEL_IS_APPROVED, BUILDER)), (bool)), false);
    }

    function testBuilderRegistryEvents() public {
        vm.recordLogs();
        callRaw(BUILDER_REGISTRY, enc1(SEL_APPROVE_BUILDER, BUILDER), TIMELOCK);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 1);
        assertEq(logs[0].topics[0], TOPIC_BUILDER_APPROVED);
        assertEq(logs[0].topics[1], bytes32(uint256(uint160(BUILDER))));

        vm.recordLogs();
        callRaw(BUILDER_REGISTRY, enc1(SEL_REMOVE_BUILDER, BUILDER), TIMELOCK);
        logs = vm.getRecordedLogs();
        assertEq(logs.length, 1);
        assertEq(logs[0].topics[0], TOPIC_BUILDER_REMOVED);
        assertEq(logs[0].topics[1], bytes32(uint256(uint160(BUILDER))));

        vm.recordLogs();
        callRaw(BUILDER_REGISTRY, enc1(SEL_SET_GUARDIAN, NEW_ADDR), TIMELOCK);
        logs = vm.getRecordedLogs();
        assertEq(logs[0].topics[0], TOPIC_GUARDIAN_UPDATED);
        assertEq(logs[0].topics[1], bytes32(uint256(uint160(NEW_ADDR))));

        vm.recordLogs();
        callRaw(BUILDER_REGISTRY, encU(SEL_SET_FEE_RATE, FEE_RATE_CAP), TIMELOCK);
        logs = vm.getRecordedLogs();
        assertEq(logs[0].topics[0], TOPIC_FEE_RATE_UPDATED);
        assertEq(abi.decode(logs[0].data, (uint256)), FEE_RATE_CAP);
    }

    function testBuilderRegistryFeeCap() public {
        (bool okCap, ) = callRaw(BUILDER_REGISTRY, encU(SEL_SET_FEE_RATE, FEE_RATE_CAP), TIMELOCK);
        assertTrue(okCap, "cap accepted");
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, abi.encodeWithSelector(SEL_FEE_RATE)), (uint256)), FEE_RATE_CAP);

        (bool ok, bytes memory r) = callRaw(BUILDER_REGISTRY, encU(SEL_SET_FEE_RATE, FEE_RATE_CAP + 1), TIMELOCK);
        assertFalse(ok, "one unit over the cap must revert");
        expectSel(sel(r), ERR_FEE_TOO_HIGH);

        (bool ok2, bytes memory r2) = callRaw(BUILDER_REGISTRY, encU(SEL_SET_FEE_RATE, FEE_RATE_LIVE), OUTSIDER);
        assertFalse(ok2, "outsider setFeeRate must revert");
        expectSel(sel(r2), ERR_NOT_OWNER);
    }

    // The guardian is not inert: removeBuilder accepts the owner OR the guardian, while every other
    // setter is owner-only. The matrix is asserted in both directions (allow and deny).
    function testBuilderRegistryGuardianCapability() public {
        (bool okA, bytes memory rA) = callRaw(BUILDER_REGISTRY, enc1(SEL_APPROVE_BUILDER, BUILDER), MULTISIG);
        assertFalse(okA, "guardian cannot approve");
        expectSel(sel(rA), ERR_NOT_OWNER);

        (bool okS, bytes memory rS) = callRaw(BUILDER_REGISTRY, encU(SEL_SET_FEE_RATE, FEE_RATE_LIVE), MULTISIG);
        assertFalse(okS, "guardian cannot set the fee rate");
        expectSel(sel(rS), ERR_NOT_OWNER);

        (bool okG, bytes memory rG) = callRaw(BUILDER_REGISTRY, enc1(SEL_SET_GUARDIAN, BUILDER), MULTISIG);
        assertFalse(okG, "guardian cannot rotate itself");
        expectSel(sel(rG), ERR_NOT_OWNER);

        (bool okT, bytes memory rT) = callRaw(BUILDER_REGISTRY, enc1(SEL_TRANSFER_OWNERSHIP, BUILDER), MULTISIG);
        assertFalse(okT, "guardian cannot take ownership");
        expectSel(sel(rT), ERR_NOT_OWNER);

        // positive: the guardian reaches removeBuilder
        (bool okApp, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_APPROVE_BUILDER, BUILDER), TIMELOCK);
        assertTrue(okApp, "owner approves first");
        vm.recordLogs();
        (bool okR, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_REMOVE_BUILDER, BUILDER), MULTISIG);
        assertTrue(okR, "guardian can remove a builder");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 1);
        assertEq(logs[0].topics[0], TOPIC_BUILDER_REMOVED);
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, enc1(SEL_IS_APPROVED, BUILDER)), (bool)), false);

        // negative control: a third party that is neither owner nor guardian is rejected
        (bool okX, bytes memory rX) = callRaw(BUILDER_REGISTRY, enc1(SEL_REMOVE_BUILDER, BUILDER), OUTSIDER);
        assertFalse(okX, "outsider cannot remove");
        expectSel(sel(rX), ERR_NOT_OWNER_OR_GUARDIAN);

        // and the owner also reaches it
        (bool okApp2, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_APPROVE_BUILDER, BUILDER), TIMELOCK);
        assertTrue(okApp2, "re-approve");
        (bool okO, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_REMOVE_BUILDER, BUILDER), TIMELOCK);
        assertTrue(okO, "owner can remove");
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, abi.encodeWithSelector(SEL_GUARDIAN)), (address)), MULTISIG);
    }

    function testBuilderRegistryZeroAddressBranches() public {
        (bool ok, bytes memory r) = callRaw(BUILDER_REGISTRY, enc1(SEL_APPROVE_BUILDER, address(0)), TIMELOCK);
        assertFalse(ok, "approveBuilder(0) must revert");
        expectSel(sel(r), ERR_ZERO_ADDRESS);

        (bool ok2, bytes memory r2) = callRaw(BUILDER_REGISTRY, enc1(SEL_TRANSFER_OWNERSHIP, address(0)), TIMELOCK);
        assertFalse(ok2, "transferOwnership(0) must revert");
        expectSel(sel(r2), ERR_ZERO_ADDRESS);

        // setGuardian has no zero-address branch: record the observed behaviour instead of assuming.
        (bool ok3, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_SET_GUARDIAN, address(0)), TIMELOCK);
        assertTrue(ok3, "setGuardian(0) is accepted");
        assertEq(abi.decode(callRead(BUILDER_REGISTRY, abi.encodeWithSelector(SEL_GUARDIAN)), (address)), address(0));
        (bool ok4, ) = callRaw(BUILDER_REGISTRY, enc1(SEL_SET_GUARDIAN, MULTISIG), TIMELOCK);
        assertTrue(ok4, "guardian restored");
    }

    // ================================================================== Exchange added selectors

    function testExchangeAddedGettersAnyCaller() public {
        assertEq(abi.decode(callReadFrom(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_INSTRUMENT_COUNT), OUTSIDER), (uint256)),
                 INSTRUMENT_COUNT);
        assertEq(abi.decode(callReadFrom(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_NEW_FLAG_GET), OUTSIDER), (bool)), FLAG_LIVE);
        assertEq(abi.decode(callReadFrom(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_NEW_ACCUM_GET), OUTSIDER), (uint256)), 0);
        assertEq(abi.decode(callReadFrom(EXCHANGE_IMPL2, enc1(SEL_BUILDER_FEES, OUTSIDER), OUTSIDER), (uint256)), 0);
    }

    function testExchangeKeeperGatedFlag() public {
        bytes32 before = vm.load(EXCHANGE_IMPL2, bytes32(uint256(8)));
        (bool ok, ) = callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 0), KEEPER);
        assertTrue(ok, "keeper can flip the flag");
        bytes32 afterW = vm.load(EXCHANGE_IMPL2, bytes32(uint256(8)));
        assertTrue(before != afterW, "slot 8 must change");
        assertEq(abi.decode(callRead(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_NEW_FLAG_GET)), (bool)), false);
        // the instrument counter keeps reading the same value: the write did not touch bits 0..31
        assertEq(abi.decode(callRead(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_INSTRUMENT_COUNT)), (uint256)), INSTRUMENT_COUNT);
        // restore
        (bool okr, ) = callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 1), KEEPER);
        assertTrue(okr, "keeper can restore the flag");

        // negative controls: owner and outsider are both rejected
        (bool okO, bytes memory rO) = callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 0), TIMELOCK);
        assertFalse(okO, "owner rejected");
        expectSel(sel(rO), ERR_NOT_AUTHORIZED_CALLER);
        (bool okX, bytes memory rX) = callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 0), OUTSIDER);
        assertFalse(okX, "outsider rejected");
        expectSel(sel(rX), ERR_NOT_AUTHORIZED_CALLER);

        // empty slot-89 state also blocks the keeper
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(89)), bytes32(0));
        (bool okZ, ) = callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 0), KEEPER);
        assertFalse(okZ, "keeper blocked when slot 89 is zero");
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(89)), bytes32(uint256(uint160(KEEPER))));

        // non-boolean argument is rejected by the decoder
        (bool okA, ) = callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 2), KEEPER);
        assertFalse(okA, "arg 2 rejected");
    }

    function testExchangeKeeperFlagEvent() public {
        vm.recordLogs();
        callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 0), KEEPER);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 1);
        assertEq(logs[0].topics[0], TOPIC_NEW_FLAG_SET);
        assertEq(logs[0].topics.length, 1);
        assertEq(abi.decode(logs[0].data, (uint256)), 0);
        callRaw(EXCHANGE_IMPL2, encU(SEL_NEW_FLAG_SET, 1), KEEPER);
    }

    // The claim is self-service: any address with a nonzero builderFees entry can call it. It debits
    // the shared slot-38 accumulator by that amount, calls the linked library and emits the event.
    function testExchangeClaimBuilderFeesIsPermissionlessSelfClaim() public {
        bytes32 key = keccak256(abi.encode(OUTSIDER, uint256(39)));
        vm.store(EXCHANGE_IMPL2, key, bytes32(uint256(12345)));
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(38)),
                 bytes32((uint256(10 ** 18) << 160) | uint256(uint160(NEW_ADDR))));

        vm.recordLogs();
        (bool ok, ) = callRaw(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_CLAIM_BUILDER_FEES), OUTSIDER);
        assertTrue(ok, "a non-owner reaches the claim body");
        assertEq(vm.load(EXCHANGE_IMPL2, key), bytes32(0));
        uint256 accumAfter = uint256(vm.load(EXCHANGE_IMPL2, bytes32(uint256(38)))) >> 160;
        assertEq(accumAfter, 10 ** 18 - 12345);
        assertEq(uint256(vm.load(EXCHANGE_IMPL2, keccak256(abi.encode(OUTSIDER, uint256(9))))), 0);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertTrue(logs.length >= 1);
        assertEq(logs[logs.length - 1].topics[0], TOPIC_CLAIM_BUILDER_FEES);
        assertEq(logs[logs.length - 1].topics[1], bytes32(uint256(uint160(OUTSIDER))));

        // control: a zero entry is a no-op success for any caller, including the owner
        vm.recordLogs();
        (bool ok2, ) = callRaw(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_CLAIM_BUILDER_FEES), TIMELOCK);
        assertTrue(ok2, "zero entry no-op");
        assertEq(vm.getRecordedLogs().length, 0);

        // control: an amount larger than the accumulator is rejected by a checked-arithmetic panic
        vm.store(EXCHANGE_IMPL2, key, bytes32(uint256(10 ** 18 + 1)));
        (bool ok3, bytes memory r3) = callRaw(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_CLAIM_BUILDER_FEES), OUTSIDER);
        assertFalse(ok3, "overdraw must revert");
        expectSel(sel(r3), bytes4(0x4e487b71)); // Panic(uint256)
    }

    // 0xd970fad5(a,b) is an owner-only accrual reassignment: it moves a's slot-39 entry into b's and
    // leaves the shared slot-38 accumulator alone. Asserted in both directions plus a negative control.
    function testExchangeNewTwoArgSelectorIsOwnerGatedReassignment() public {
        bytes32 keyA = keccak256(abi.encode(BUILDER, uint256(39)));
        bytes32 keyB = keccak256(abi.encode(BUILDER2, uint256(39)));
        vm.store(EXCHANGE_IMPL2, keyA, bytes32(uint256(5 * 10 ** 18)));
        vm.store(EXCHANGE_IMPL2, keyB, bytes32(uint256(7 * 10 ** 18)));
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(38)),
                 bytes32((uint256(100 * 10 ** 18) << 160) | uint256(uint160(NEW_ADDR))));

        (bool okX, bytes memory rX) = callRaw(EXCHANGE_IMPL2,
            abi.encodeWithSelector(SEL_NEW_OWNER_2ARG, BUILDER, BUILDER2), OUTSIDER);
        assertFalse(okX, "non-owner rejected");
        expectSel(sel(rX), ERR_NOT_OWNER);
        assertEq(uint256(vm.load(EXCHANGE_IMPL2, keyA)), 5 * 10 ** 18);
        assertEq(uint256(vm.load(EXCHANGE_IMPL2, keyB)), 7 * 10 ** 18);

        (bool ok2, ) = callRaw(EXCHANGE_IMPL2,
            abi.encodeWithSelector(SEL_NEW_OWNER_2ARG, BUILDER, BUILDER2), TIMELOCK);
        assertTrue(ok2, "owner reaches the body");
        assertEq(uint256(vm.load(EXCHANGE_IMPL2, keyA)), 0);
        assertEq(uint256(vm.load(EXCHANGE_IMPL2, keyB)), 12 * 10 ** 18);
        assertEq(uint256(vm.load(EXCHANGE_IMPL2, bytes32(uint256(38)))) >> 160, 100 * 10 ** 18);
    }

    function testExchangeOwnerSettersStillOwnerGated() public {
        (bool ok, bytes memory r) = callRaw(EXCHANGE_IMPL2, enc1(SEL_SET_KEEPER, NEW_ADDR), OUTSIDER);
        assertFalse(ok);
        expectSel(sel(r), ERR_NOT_OWNER);
        (bool ok2, ) = callRaw(EXCHANGE_IMPL2, enc1(SEL_SET_KEEPER, NEW_ADDR), TIMELOCK);
        assertTrue(ok2);
        assertEq(address(uint160(uint256(vm.load(EXCHANGE_IMPL2, bytes32(uint256(89)))))), NEW_ADDR);
        vm.store(EXCHANGE_IMPL2, bytes32(uint256(89)), bytes32(uint256(uint160(KEEPER))));
    }

    function testExchangePauseAuthority() public {
        (bool okG, ) = callRaw(EXCHANGE_IMPL2, enc1(SEL_SET_PAUSE_GUARDIAN, MULTISIG), TIMELOCK);
        assertTrue(okG, "owner sets the pause guardian");
        assertEq(abi.decode(callRead(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_PAUSE_GUARDIAN)), (address)), MULTISIG);

        (bool okP, ) = callRaw(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_SET_TRADING_PAUSED, true), MULTISIG);
        assertTrue(okP, "pause guardian can pause");
        assertEq(abi.decode(callRead(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_TRADING_PAUSED)), (bool)), true);

        (bool okR, bytes memory rR) = callRaw(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_SET_TRADING_PAUSED, false), MULTISIG);
        assertFalse(okR, "pause guardian cannot resume");
        expectSel(sel(rR), ERR_NOT_PAUSE_AUTHORITY);

        (bool okX, bytes memory rX) = callRaw(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_SET_TRADING_PAUSED, false), OUTSIDER);
        assertFalse(okX, "outsider cannot resume");
        expectSel(sel(rX), ERR_NOT_PAUSE_AUTHORITY);

        (bool okO, ) = callRaw(EXCHANGE_IMPL2, abi.encodeWithSelector(SEL_SET_TRADING_PAUSED, false), TIMELOCK);
        assertTrue(okO, "owner can resume");
    }

    // ================================================================== SessionKeyManager

    function testSessionKeyManagerSetBuilderRegistryOwnerGate() public {
        (bool ok, bytes memory r) = callRaw(SKM_IMPL2, enc1(SEL_SET_BUILDER_REGISTRY, NEW_ADDR), OUTSIDER);
        assertFalse(ok);
        expectSel(sel(r), ERR_NOT_OWNER);
        (bool ok2, ) = callRaw(SKM_IMPL2, enc1(SEL_SET_BUILDER_REGISTRY, NEW_ADDR), TIMELOCK);
        assertTrue(ok2);
        assertEq(abi.decode(callRead(SKM_IMPL2, abi.encodeWithSelector(SEL_BUILDER_REGISTRY_GET)), (address)), NEW_ADDR);
        // the authorized-caller slot is untouched by the registry setter
        assertEq(address(uint160(uint256(vm.load(SKM_IMPL2, bytes32(uint256(3)))))), NEW_ADDR);
    }

    // ================================================================== Tokenomics

    // activateRebate is owner-gated and additionally state-gated: it needs the PAPER pointer set and
    // an inactive rebate, and its body then calls the configured PAPER token as minter.
    function testTokenomicsActivateRebateAuthority() public {
        (bool ok, bytes memory r) = callRaw(TOKENOMICS_IMPL2, abi.encodeWithSelector(SEL_ACTIVATE_REBATE), OUTSIDER);
        assertFalse(ok, "outsider rejected");
        expectSel(sel(r), ERR_NOT_OWNER);

        // owner with paperToken unset -> 0x6e20dedb (unnamed state error)
        (bool ok2, bytes memory r2) = callRaw(TOKENOMICS_IMPL2, abi.encodeWithSelector(SEL_ACTIVATE_REBATE), TIMELOCK);
        assertFalse(ok2, "state precondition blocks the owner");
        expectSel(sel(r2), bytes4(0x6e20dedb));

        // with paperToken set to a codeless address the body reaches the PAPER call and reverts there
        vm.store(TOKENOMICS_IMPL2, bytes32(uint256(2)), bytes32(uint256(uint160(NEW_ADDR))));
        (bool ok3, bytes memory r3) = callRaw(TOKENOMICS_IMPL2, abi.encodeWithSelector(SEL_ACTIVATE_REBATE), TIMELOCK);
        assertFalse(ok3, "the body calls the configured token");
        assertEq(r3.length, 0);

        // an already-active rebate (slot 9 low 128 bits set) is refused with 0xfc6b95ed
        vm.store(TOKENOMICS_IMPL2, bytes32(uint256(9)), bytes32(uint256(1)));
        (bool ok4, bytes memory r4) = callRaw(TOKENOMICS_IMPL2, abi.encodeWithSelector(SEL_ACTIVATE_REBATE), TIMELOCK);
        assertFalse(ok4, "active rebate refused");
        expectSel(sel(r4), bytes4(0xfc6b95ed));

        // the four unguarded getters answer from any caller in the captured state
        vm.store(TOKENOMICS_IMPL2, bytes32(uint256(9)), bytes32(0));
        callReadMsg(TOKENOMICS_IMPL2, abi.encodeWithSelector(SEL_INSOLVENT_SINCE), "insolventSince");
        callReadMsg(TOKENOMICS_IMPL2, abi.encodeWithSelector(SEL_TK_NEW_122B), "0x122b6689");
        callReadMsg(TOKENOMICS_IMPL2, abi.encodeWithSelector(SEL_TK_NEW_4EC7), "0x4ec7182e");
        // 0xeedf4c43 has a revert branch in the zero state; it is not an access-control error
        (bool okE, bytes memory rE2) = TOKENOMICS_IMPL2.staticcall(abi.encodeWithSelector(SEL_TK_NEW_EEDF));
        if (!okE) {
            assertTrue(sel(rE2) != ERR_NOT_OWNER, "0xeedf4c43 revert is not NotOwner");
        }
    }

    // ================================================================== upgrade route

    function testNoImplementationSlotWriterInNewRuntimes() public view {
        bytes memory implSlotBytes = abi.encodePacked(IMPL_SLOT);
        bytes memory adminSlotBytes = abi.encodePacked(ADMIN_SLOT);
        assertFalse(_contains(codeOf(EXCHANGE_IMPL2), implSlotBytes));
        assertFalse(_contains(codeOf(EXCHANGE_IMPL2), adminSlotBytes));
        assertFalse(_contains(codeOf(SKM_IMPL2), implSlotBytes));
        assertFalse(_contains(codeOf(TOKENOMICS_IMPL2), implSlotBytes));
    }

    function testUpgradeRoutesThroughTimelockOwnedProxyAdmin() public {
        (bool okX, bytes memory rX) = callRaw(PROXY_ADMIN,
            abi.encodeWithSelector(SEL_PA_UPGRADE, SHARED_PROXY, PAPER_IMPL), OUTSIDER);
        assertFalse(okX, "outsider cannot upgrade");
        expectSel(sel(rX), ERR_NOT_OWNER);

        vm.store(SHARED_PROXY, IMPL_SLOT, bytes32(uint256(uint160(EXCHANGE_IMPL2))));
        vm.store(SHARED_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(PROXY_ADMIN))));
        (bool okT, ) = callRaw(PROXY_ADMIN, abi.encodeWithSelector(SEL_PA_UPGRADE, SHARED_PROXY, PAPER_IMPL), TIMELOCK);
        assertTrue(okT, "timelock owner can upgrade");
        assertEq(address(uint160(uint256(vm.load(SHARED_PROXY, IMPL_SLOT)))), PAPER_IMPL);
    }

    function testTimelockSelfGatedAndMultisigGated() public {
        (bool okE, bytes memory rE) = callRaw(TIMELOCK,
            abi.encodeWithSelector(SEL_TL_EXECUTE, address(0), uint256(0), hex"", bytes32(0)), OUTSIDER);
        assertFalse(okE, "outsider cannot execute");
        expectSel(sel(rE), ERR_NOT_OWNER);

        // updateMinDelay is a self-call: the owner (the multisig) is rejected too, so only an executed
        // timelock operation can change the delay.
        (bool okD, bytes memory rD) = callRaw(TIMELOCK, encU(SEL_TL_UPDATE_MIN_DELAY, 1), MULTISIG);
        assertFalse(okD, "the owner cannot call updateMinDelay directly");
        expectSel(sel(rD), ERR_NOT_SELF);
        (bool okD2, bytes memory rD2) = callRaw(TIMELOCK, encU(SEL_TL_UPDATE_MIN_DELAY, 1), TIMELOCK);
        assertTrue(okD2, "the contract can call it on itself");
        assertEq(abi.decode(callRead(TIMELOCK, abi.encodeWithSelector(bytes4(0xc63c4e9b))), (uint256)), 1);

        (bool okS, ) = callRaw(MULTISIG,
            abi.encodeWithSelector(SEL_MS_SUBMIT, address(0), uint256(0), hex""), OUTSIDER);
        assertFalse(okS, "non-signer cannot submit");

        (bool okC, ) = callRaw(MULTISIG,
            abi.encodeWithSelector(SEL_MS_CONFIRM, uint256(0), bytes32(0)), OUTSIDER);
        assertFalse(okC, "non-signer cannot confirm");
    }

    // ================================================================== PAPER and Staking

    function testPaperAdminOwnerGate() public {
        bytes4[3] memory sels = [SEL_PAPER_SET_MINTER, SEL_PAPER_SET_STAKING, SEL_PAPER_SET_SPENDER];
        for (uint256 i = 0; i < sels.length; i++) {
            (bool ok, bytes memory r) = callRaw(PAPER_IMPL, enc1(sels[i], NEW_ADDR), OUTSIDER);
            assertFalse(ok, "outsider rejected");
            expectSel(sel(r), ERR_NOT_OWNER);
            (bool ok2, ) = callRaw(PAPER_IMPL, enc1(sels[i], NEW_ADDR), TIMELOCK);
            assertTrue(ok2, "owner accepted");
        }
        (bool okT, bytes memory rT) = callRaw(PAPER_IMPL, enc1(SEL_TRANSFER_OWNERSHIP, NEW_ADDR), OUTSIDER);
        assertFalse(okT);
        expectSel(sel(rT), ERR_NOT_OWNER);
    }

    function testStakingAdminOwnerGate() public {
        (bool ok, bytes memory r) = callRaw(STAKING_IMPL, enc1(SEL_STAKING_SET_EXECUTOR, NEW_ADDR), OUTSIDER);
        assertFalse(ok);
        expectSel(sel(r), ERR_NOT_OWNER);
        (bool ok2, ) = callRaw(STAKING_IMPL, enc1(SEL_STAKING_SET_EXECUTOR, NEW_ADDR), TIMELOCK);
        assertTrue(ok2);
        (bool okT, bytes memory rT) = callRaw(STAKING_IMPL, enc1(SEL_TRANSFER_OWNERSHIP, NEW_ADDR), OUTSIDER);
        assertFalse(okT);
        expectSel(sel(rT), ERR_NOT_OWNER);
    }

    // ================================================================== read helpers

    function assertTrue(bool c) internal pure { require(c, "assertTrue"); }
    function assertTrue(bool c, string memory m) internal pure { require(c, m); }
    function assertFalse(bool c) internal pure { require(!c, "assertFalse"); }
    function assertFalse(bool c, string memory m) internal pure { require(!c, m); }
    function assertEq(bytes4 a, bytes4 b) internal pure { require(a == b, "assertEq bytes4"); }
    function expectSel(bytes4 got, bytes4 want) internal pure { require(got == want, "unexpected revert selector"); }
    function assertEq(bytes4 a, bytes4 b, string memory m) internal pure { require(a == b, m); }
    function assertEq(uint256 a, uint256 b) internal pure { require(a == b, "assertEq uint256"); }
    function assertEq(bool a, bool b) internal pure { require(a == b, "assertEq bool"); }
    function assertEq(address a, address b) internal pure { require(a == b, "assertEq address"); }
    function assertEq(bytes32 a, bytes32 b) internal pure { require(a == b, "assertEq bytes32"); }

    function callRead(address to, bytes memory data) internal view returns (bytes memory ret) {
        (bool ok, bytes memory out) = to.staticcall(data);
        assertTrue(ok, "read must not revert");
        return out;
    }

    function callReadFrom(address to, bytes memory data, address) internal view returns (bytes memory ret) {
        (bool ok, bytes memory out) = to.staticcall(data);
        assertTrue(ok, "read must not revert");
        return out;
    }

    function callReadMsg(address to, bytes memory data, string memory name) internal view returns (bytes memory ret) {
        (bool ok, bytes memory out) = to.staticcall(data);
        require(ok, name);
        return out;
    }

    function codeOf(address a) internal view returns (bytes memory c) {
        uint256 n; assembly { n := extcodesize(a) }
        c = new bytes(n);
        assembly { extcodecopy(a, add(c, 32), 0, n) }
    }

    function _contains(bytes memory hay, bytes memory needle) internal pure returns (bool) {
        if (needle.length == 0 || hay.length < needle.length) return false;
        for (uint256 i = 0; i + needle.length <= hay.length; i++) {
            bool hit = true;
            for (uint256 j = 0; j < needle.length; j++) {
                if (hay[i + j] != needle[j]) { hit = false; break; }
            }
            if (hit) return true;
        }
        return false;
    }
}