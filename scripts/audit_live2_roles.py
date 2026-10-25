#!/usr/bin/env python3
"""Pass-two audit of the semi-trusted Papertrade roles: keeper (authorizedKeeper and
marketKeeper), relayer (BatchExecutor submitter), pause guardian and builder.

Offline by default: it re-verifies the saved runtime bytes, re-runs the set-2 exact-runtime
harness with four added role cases, and writes a machine ledger plus a readable doc.
`--capture` refreshes the small read-only live probe set (public endpoint, no key).

This script owns only artifacts/live2_roles/**, atlas/block_48902346/live2_roles.{json,md}.
It reads pass-one evidence and never edits other workstreams' files.
"""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_live2_intents as I  # noqa: E402  pass-one harness, reused read-only
import audit_signed_intent_failures as F  # noqa: E402

ATLAS = ROOT / "atlas" / "block_48902346"
OUT_DIR = ROOT / "artifacts" / "live2_roles"
LEDGER = ATLAS / "live2_roles.json"
DOC = ATLAS / "live2_roles.md"
PIN = I.PIN
PIN_HASH = I.PIN_HASH

EXCHANGE = I.EXCHANGE
SESSION = I.SESSION
BATCH = I.BATCH
FACTORY = I.FACTORY
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
ORACLE_IMPL = "0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a"
LIBRARY_2 = I.LIBRARY_2
BUILDER_REGISTRY = I.BUILDER_REGISTRY
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
PAUSE_GUARDIAN = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
KEEPER = I.KEEPER                                       # Exchange slot 89, authorizedKeeper
MARKET_KEEPER = "0x3721476de31190dc1af8908026abe20efe25cf99"  # Exchange slot 37
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
PRE_BBO = "0x000000000000000000000000000000000000080e"

# Pinned instrument-0 and market-0 config words (saved read-only probes).
INST0_ROOT = "0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6df"
INST0_WORDS = ["0x000003e8000000000000002c28d1751327a700000000032d26d12e980b600000",
               "0x00016345785d8a00000001b0f51147891600000000084595161401484a000000",
               "0x00000000000000000000000000000000000000000000152d02c7e14af6800000"]
MARKET0_ROOT = "0xb7634ec2165a7280a285aac3ec10cf370eca86d8aa9d3243c90b2151434091ad"
MARKET0_WORDS = ["0x000000000000000a0000006a7b0a8451489ff50800000087e15f8bfb5c98cd37",
                 "0x000000000000006d6f7f9910a100abf8000000000000008e0566e854e34d5335"]


def word(value):
    return f"{value:064x}"


def returndata(*values):
    code = "0x"
    for i, value in enumerate(values):
        code += "7f" + word(value) + "60" + f"{32 * i:02x}" + "52"
    return code + "60" + f"{32 * len(values):02x}" + "6000f3"


BBO_MOCK = returndata(100, 200)  # bid 100, ask 200 -> validated midpoint 150


ROLE_TESTS = r'''
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
        vm.etch(PRE_BBO, hex"@@BBO_MOCK@@");
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
'''


def build_source():
    saved_exchange = json.loads(
        (ROOT / "artifacts" / "exchange_direct_status_local" / "pinned_direct_slots.json").read_text())
    pinned_source = F.build_source(saved_exchange)
    live = json.loads((ROOT / "artifacts" / "postpin_pin" / "raw_reads.json").read_text())
    by_key = {row["key"]: row for row in live["reads"]}
    slot88 = by_key["exchange_authorized_executor_word"]["raw"]["result"]
    registry = "0x" + "00" * 12 + BUILDER_REGISTRY[2:]
    source = I.build_live_source(pinned_source, slot88, registry)
    tests = ROLE_TESTS.replace("@@BBO_MOCK@@", BBO_MOCK[2:])
    assert source.rstrip().endswith("}")
    return source[:source.rstrip().rfind("}")] + tests + "}\n"


def runtime_files(runtimes, base_proxy):
    factory_impl = (ATLAS / runtimes["_manifest"]["contracts"]
                    ["0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0"]["runtime_file"]).read_text().strip()
    user = "0xe05fcc23807536bee418f142d19fa0d21bb0cff7"
    files = {
        "ExchangeProxy": runtimes["ExchangeProxy1"],
        "SessionProxy": runtimes["SessionProxy1"],
        "BatchExecutorProxy": runtimes["BatchExecutorProxy"],
        "BatchExecutorImpl": runtimes["BatchExecutorImpl"],
        "FactoryProxy": runtimes["FactoryProxy"],
        "Library2": runtimes["library"],
        "FactoryImpl": factory_impl,
        "ProxyUser": I.derive_proxy_runtime(base_proxy, user),
        "ExchangeImpl2": runtimes["exchange_impl"],
        "SessionImpl2": runtimes["session_impl"],
        "BuilderRegistry": runtimes["builder_registry"],
        "OracleImpl": (ATLAS / runtimes["_manifest"]["contracts"][ORACLE_IMPL]["runtime_file"]
                       ).read_text().strip(),
        "FactoryProxyOfMock": I.mock_code([int(I.derived_proxy_address(user), 16)]),
    }
    for name, mock in I.MOCKS.items():
        files[name] = I.mock_code(mock[0])
    return files


EXPECTED = {
    "role_pause_surface": {
        "guardian_global_pause": 0,
        "guardian_global_resume": 0x49199FB6,
        "guardian_set_pause_byte": 1,
        "keeper_global_pause": 0x49199FB6,
        "keeper_market_pause": 0x49199FB6,
        "marketKeeper_global_pause": 0x49199FB6,
        "marketKeeper_market_pause": 0x49199FB6,
        "outsider_global_pause": 0x49199FB6,
        "owner_global_resume": 0,
    },
    "role_keeper_surface": {
        "keeper_flag": 0,
        "keeper_setFeeRates": 0x30CD7471,
        "keeper_setFeeRates_again": 0x30CD7471,
        "keeper_close": 0xDA96F0B6,
        "marketKeeper_oiCap": 0,
        "marketKeeper_slot28": 0,
        "marketKeeper_instrument": 0x30CD7471,
        "slot24_after": 20000000000000000,
        "slot28_after": str(2**256 - 1),
    },
    "role_keeper_flag_gates": {
        "flip_ok": True, "flag_byte_after": 0, "active_before": 1, "close_ok": True,
        "close_selector": 0, "close_writes": 6, "active_after": 0,
    },
    "role_keeper_liquidation": {
        "healthy_ok": True, "healthy_selector": 0, "healthy_events": 0,
        "healthy_active_after": 1, "ill_ok": True, "ill_events": 1, "ill_active_after": 0,
    },
    "role_global_pause_gates": {
        "close_ok": True, "close_selector": 0, "close_flags_after": 0,
        "close_writes": 6, "liquidate_batch_ok": True, "liquidate_batch_selector": 0,
    },
    "role_builder_plain": {
        "ok": True, "selector": 0, "reads": 39, "writes": 6, "slot39_read_bits": 0,
        "slot39_write_bits": 0, "credited_value": 0, "shared_counter": 0,
        "registry_accesses": 0,
    },
    "role_builder_id7": {
        "ok": True, "selector": 0, "reads": 39, "writes": 6, "slot39_read_bits": 0,
        "slot39_write_bits": 0, "credited_value": 0, "shared_counter": 0,
        "registry_accesses": 0,
    },
    "role_builder_trailing": {
        "ok": True, "selector": 0, "reads": 39, "writes": 6, "slot39_read_bits": 0,
        "slot39_write_bits": 0, "credited_value": 0, "shared_counter": 0,
        "registry_accesses": 0,
    },
    "role_builder_approved": {
        "ok": True, "selector": 0, "reads": 39, "writes": 6, "slot39_read_bits": 0,
        "slot39_write_bits": 0, "credited_value": 0, "shared_counter": 0,
        "registry_accesses": 0,
    },
    "role_builder_loss": {
        "ok": True, "selector": 0, "reads": 35, "writes": 4, "slot39_read_bits": 0,
        "slot39_write_bits": 0, "credited_value": 0, "shared_counter": 0,
        "registry_accesses": 0,
    },
    "role_relayer_batch": {
        "dup_first_ok": True, "dup_second_ok": False, "dup_second_sel": 0x756688FE,
        "wrongids_first_ok": False, "wrongids_first_sel": 0xC5045F22, "wrongids_second_ok": True,
        "retarget_first_sel": 0xC5045F22, "retarget_second_ok": True,
    },
    "role_relayer_order": {
        "order12_price_a": 150, "order12_price_b": 150,
        "order21_price_a": 150, "order21_price_b": 150,
    },
    "role_global_pause_open": {},
    "role_keeper_cap_effect": {},
    "role_relayer_withdraw": {
        "ok": True, "selector": 0, "recipient_is_signed_user": True,
        "retarget_selector": 0xC20280EA,
    },
}

ERRORS = {0x30CD7471: "NotOwner()", 0x49199FB6: "NotPauseAuthority()",
          0xDA96F0B6: "unnamed (not the authorized executor)",
          0x756688FE: "InvalidNonce()", 0xC5045F22: "SessionKeyNotAuthorized()",
          0xC20280EA: "unnamed (signed-field mismatch)", 0x2C49223E: "NotOwnerOrGuardian()",
          0xDDEB79BA: "NotLiquidatable()"}


def rows(runtimes, observations):
    o = observations

    def ev(name, **extra):
        return {"observation": name, "artifact": "artifacts/live2_roles/replay.json",
                "harness": "artifacts/live2_roles/RoleLocal.t.sol", **extra}

    return [
        {
            "id": "RL-01",
            "title": "The authorized keeper is boxed in: it can flip one opaque byte and nothing else",
            "angle": "Keeper (authorizedKeeper, Exchange slot 89)",
            "invariant": "A5 + proposed A8 (role scope)",
            "actor": "whoever holds Exchange slot 89 (live: 0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56)",
            "precondition": "Exchange slot 89 equals the caller; the live value was wired by the 2026-10-21 batch",
            "trigger": "0xe6ac4a74(bool) from the keeper; and every other selector a keeper might try",
            "impact": "The keeper's only accepted write is the slot-8 byte above bits 0..31 "
                      "(instrumentCount is preserved). It cannot submit an intent (close reverts "
                      "0xDA96F0B6 as a non-executor), cannot set fees (setFeeRates reverts NotOwner "
                      "0x30CD7471 with slot 24 unchanged at 2e16), cannot pause a market or the venue "
                      "(both revert NotPauseAuthority 0x49199FB6), and cannot liquidate a healthy "
                      "position (an eligible check skips it: 0 events, active bit kept). Clearing the "
                      "flag does not change the signed close (it still closes, same 6 writes).",
            "affected": "set2",
            "severity": "none",
            "status": "disproved",
            "evidence_tier": "exact-runtime replay, set 2 runtimes, plus a first-party negative control",
            "evidence": ev("role_keeper_surface, role_keeper_flag_gates, role_pause_surface, "
                           "role_keeper_liquidation",
                           keeper_flag_ok=o["role_keeper_surface"]["keeper_flag"],
                           setFeeRates=hex(o["role_keeper_surface"]["keeper_setFeeRates"]),
                           keeper_close=hex(o["role_keeper_surface"]["keeper_close"]),
                           slot24_unchanged=o["role_keeper_surface"]["slot24_after"],
                           flag_byte_after=o["role_keeper_flag_gates"]["flag_byte_after"],
                           close_writes_with_flag_cleared=o["role_keeper_flag_gates"]["close_writes"],
                           healthy_liquidated_events=o["role_keeper_liquidation"]["healthy_events"],
                           healthy_active_after=o["role_keeper_liquidation"]["healthy_active_after"]),
            "missing_observation": "whether the slot-8 byte gates the open, settlement or a front-end "
                                   "consumer; the open path reverts post-signer (0x0a4f5a07) on set 2 "
                                   "so it could not be driven, and the close is inert",
            "citations": ["atlas/block_48902346/live2_authority.md L2A-02, L2A-10",
                          "atlas/block_48902346/exchange_admin_setters.md",
                          "atlas/block_48902346/exchange_liquidation_pseudocode.md"],
        },
        {
            "id": "RL-02",
            "title": "The market keeper can raise both per-side open caps to maximum, and an exact-runtime "
                     "open the configured cap rejects then succeeds",
            "angle": "Keeper (marketKeeper, Exchange slot 37)",
            "invariant": "A4 (eligibility bounds) + proposed A8",
            "actor": "whoever holds Exchange slot 37 (live: 0x3721476de31190dc1af8908026abe20efe25cf99)",
            "precondition": "Exchange slot 37 equals the caller",
            "trigger": "0x628a9fd6(uint32,uint128,uint128) with both values at type(uint128).max, and "
                       "0x82f47a3f(uint128,uint128) likewise",
            "impact": "Both writes succeed (selector 0, slot 28 reads 2**256-1 afterwards), and the per-side "
                      "cap write changes a live open outcome: a signed open of size 1e20 and another "
                      "of 1e22 both revert OiCapExceeded 0x40f92143 under the configured caps and "
                      "both succeed (selector 0, a position is opened) after the keeper sets both "
                      "caps to type(uint128).max. The cap write therefore removes the configured "
                      "aggregate per-side open-interest bound, which is the sole guard on 57 saved "
                      "opens. It does not remove every bound: a 1e24 open still fails with the public "
                      "candidate PositionTooLarge() 0x543a6e10, which the keeper cannot change, so "
                      "the keeper widens the aggregate exposure rather than creating an unbounded "
                      "single position. Because the per-side limit bounds notional rather than payout "
                      "(pass-one LP-05), the revenue at risk beyond it is a payout that can credit the "
                      "whole LP bankroll and queue the remainder. Neither setter has any bound or gate "
                      "beyond the slot-37 (or owner) check: no timelock, no upper bound below the "
                      "uint128 type ceiling, no rate or delta limit, and the only record is the "
                      "setter's own event (topic 0xa065d6ba for the cap setter, 0x5bcf15b0 for slot "
                      "28), so a maxed cap leaves no state a monitoring job can use beyond that event. "
                      "The change is not retroactive in either direction: the per-side limit is "
                      "compared only on the signed-open path (all 57 saved comparisons are opens), and "
                      "the close updates the market's aggregate OI word without ever reading the "
                      "limit (the close arms write the position word, the market word, the balance "
                      "word and the fee word). A raised cap therefore admits new opens and does not "
                      "change how an existing position settles, so the incremental exposure is "
                      "bounded by what is opened after the change, not by the pre-change book. "
                      "The economic meaning of slot 28's two fields is still unnamed, so its "
                      "max-write is a scope observation. Fee rates, instruments and both pause "
                      "surfaces stay owner or guardian gated.",
            "affected": "both",
            "severity": "medium",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay (the write) on top of pass-one open-path evidence",
            "evidence": ev("role_keeper_surface, role_keeper_cap_effect",
                           oi_cap_selector=o["role_keeper_surface"]["marketKeeper_oiCap"],
                           slot28_selector=o["role_keeper_surface"]["marketKeeper_slot28"],
                           slot28_after=o["role_keeper_surface"]["slot28_after"],
                           instrument_setter=hex(o["role_keeper_surface"]["marketKeeper_instrument"]),
                           cap_effect=o["role_keeper_cap_effect"]),
            "missing_observation": "whether the widened aggregate OI is bounded by anything other than the "
                                   "per-position limit and the LP bankroll (the payout itself is not "
                                   "cap-bounded), and the economic names of the slot-28 fields",
            "citations": ["atlas/block_48902346/exchange_open_limit.md",
                          "atlas/block_48902346/exchange_market_fields.md",
                          "atlas/block_48902346/exchange_pair_params.md",
                          "atlas/block_48902346/live2_pricing.md LP-05"],
        },
        {
            "id": "RL-03",
            "title": "The relayer cannot duplicate, re-target or re-price an intent, and in-block "
                     "ordering leaves every settlement price identical",
            "angle": "Relayer (BatchExecutor submitter)",
            "invariant": "A2 + A10",
            "actor": "an address in the BatchExecutor authorizedRelayers mapping (mapping base 4, owner-set)",
            "precondition": "the relayer is authorised; the Exchange sees only the BatchExecutor as "
                            "msg.sender, so no Exchange state can key on the relayer",
            "trigger": "submit one signed close twice; submit the same signature with a different "
                       "positionIds element or a different user word; submit two closes in both orders",
            "impact": "Duplication is rejected: the first call closes, the second reverts "
                      "InvalidNonce 0x756688FE. Re-targeting is rejected: a signature over id 1 with "
                      "calldata id 2, and a signature over USER with calldata OUTSIDER, both revert "
                      "SessionKeyNotAuthorized 0xC5045F22 while the correct payload still succeeds. "
                      "The withdrawal path binds its Core recipient to the signed user (decoded from "
                      "the CoreWriter payload) and re-targets to 0xC20280EA. Reordering two closes in "
                      "one batch leaves both settlement prices at the same Oracle midpoint (150), "
                      "because the price is read per call from a per-block HyperCore value. The "
                      "allowlist admits only the three Exchange signed selectors, the SessionKeyManager "
                      "registration and four Staking selectors.",
            "affected": "both",
            "severity": "none",
            "status": "disproved",
            "evidence_tier": "exact-runtime replay, set 2 runtimes",
            "evidence": ev("role_relayer_batch, role_relayer_order, role_relayer_withdraw",
                           duplicate_second=hex(o["role_relayer_batch"]["dup_second_sel"]),
                           wrong_ids=hex(o["role_relayer_batch"]["wrongids_first_sel"]),
                           re_target_user=hex(o["role_relayer_batch"]["retarget_first_sel"]),
                           order12=o["role_relayer_order"]["order12_price_a"],
                           order21=o["role_relayer_order"]["order21_price_a"],
                           withdraw_recipient_is_signed_user=o["role_relayer_withdraw"]["recipient_is_signed_user"],
                           withdraw_re_target=hex(o["role_relayer_withdraw"]["retarget_selector"])),
            "missing_observation": "cross-block selective inclusion and delay: the relayer can hold or "
                                   "drop an intent, so its residual power is latency and censorship, "
                                   "bounded by the signed deadline and not by a cap; no on-chain value "
                                   "transfer was found",
            "citations": ["atlas/block_48902346/batch_executor_pseudocode.md",
                          "atlas/block_48902346/live2_intents.md L2-D2-01, L2-D2-02"],
        },
        {
            "id": "RL-04",
            "title": "No signed-close shape credits a builder fee: the credit site is unreachable and "
                     "the registry is never consulted, so the per-close builder skim is zero",
            "angle": "Builder (BuilderRegistry fee) plus the relayer quote on it",
            "invariant": "A10",
            "actor": "any builder, relayer, frontend or the closing user",
            "precondition": "the 0.5 percent registry rate and an approved builder; the signed close "
                            "struct has no builder field (five-field CLOSE_TYPEHASH, unchanged)",
            "trigger": "five exact-runtime fee-paying closes on the set-2 Exchange: plain; a second "
                       "position id; an appended unsigned 8th calldata word naming the keeper; every "
                       "one of fourteen candidate addresses approved in the registry; and a loss close",
            "impact": "Every arm closes successfully with a real fee charged (slot 26 rises, so the "
                      "close is fee-paying) and every one shows zero slot-39 reads, zero slot-39 "
                      "writes, a credited value of zero, an unchanged slot-38 counter and zero "
                      "BuilderRegistry accesses (vm.accesses on the registry is empty). So a gain close, a loss close, an other-id close and three more shapes "
                      "cannot credit any builder: a relayer or frontend cannot steer a builder fee, "
                      "and the maximum a malicious builder can skim per close through this path is 0. "
                      "The 0.5 percent "
                      "rate and the registry itself are inert for trading, which matches pass-one "
                      "L2A-07 (no feeRateOf selector bytes in the Exchange or library).",
            "affected": "set2",
            "severity": "none",
            "status": "disproved",
            "evidence_tier": "exact-runtime replay, set 2 runtimes; the pass-one concern is resolved",
            "evidence": ev("role_builder_plain, role_builder_id7, role_builder_trailing, "
                           "role_builder_approved, role_builder_loss",
                           arms=5,
                           slot39_reads=sum(o[f"role_builder_{a}"]["slot39_read_bits"]
                                            for a in ("plain", "id7", "trailing", "approved", "loss")),
                           slot39_writes=sum(o[f"role_builder_{a}"]["slot39_write_bits"]
                                             for a in ("plain", "id7", "trailing", "approved", "loss")),
                           registry_accesses=sum(o[f"role_builder_{a}"]["registry_accesses"]
                                                 for a in ("plain", "id7", "trailing", "approved",
                                                           "loss")),
                           slot38_after=[o[f"role_builder_{a}"]["shared_counter"]
                                         for a in ("plain", "approved", "loss")],
                           exchange_writes_per_close=o["role_builder_plain"]["writes"]),
            "missing_observation": "which entry does reach the pass-one credit block at 0x32b6 inside "
                                   "the 0x2792e706 region; its only exercised slot-39 touchers remain "
                                   "claimBuilderFees (the caller's own key) and the owner-only 0xd970fad5",
            "citations": ["atlas/block_48902346/live2_authority.md L2A-07, L2A-08, L2A-09",
                          "atlas/block_48902346/live2_intents.md L2-D1-06"],
        },
        {
            "id": "RL-05",
            "title": "The pause guardian's market pause is a free exit option written by the LP: a "
                     "zero or crossed frozen quote lets a holder close at a fake price with no cap",
            "angle": "Guardian (pauseMarket and setTradingPaused)",
            "invariant": "A9 + A4",
            "actor": "the pause guardian (live: the newest 2-of-3 multisig 0x696292...) acting with a "
                     "trading address, or any pre-existing holder who acts on the same knowledge",
            "precondition": "at least two of the three multisig signers; the trader already holds a "
                            "position in the market to be paused (opens are blocked after the pause)",
            "trigger": "pauseMarket(uint32) at a moment when the raw HyperCore BBO the pause stores is "
                       "zero or crossed, then close the position; the close settles from the stored "
                       "snapshot, not from a fresh oracle read",
            "impact": "A pause taken on a zero book makes the next close or liquidation settle at "
                      "price 0 (PT-02, measured on both implementations), so a short close credits "
                      "raw = margin x leverage x (entry - 0) / entry = margin x leverage, a payout the "
                      "LP funds (pass-one LP-05: one cap-legal close can credit the whole available LP "
                      "bankroll and queue the remainder); a "
                      "paused market also rejects new opens while closes still settle. My own arms "
                      "confirm the channel: a paused venue still closes (close succeeds and clears the "
                      "active bit), still liquidates, and the close settles from the Oracle midpoint. "
                      "Because the guardian chooses the moment and the pause cannot be cleared (PT-02), "
                      "the guardian holds a free American option on its own exit price: it can wait for "
                      "the most favourable snapshot and exercise it once per instrument. The counter-"
                      "party is the single protocol LP, and no fee cap, signature or owner gate bounds "
                      "the gain; it is bounded only by the position's payout and the LP bankroll.",
            "affected": "both",
            "severity": "high",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay for the settlement channel; the latency of the live "
                             "trigger rests on pass-one PT-02",
            "evidence": ev("role_global_pause_gates + PT-02",
                           paused_close_ok=o["role_global_pause_gates"]["close_ok"],
                           paused_close_cleared_active=o["role_global_pause_gates"]["close_flags_after"],
                           paused_liquidation_ok=o["role_global_pause_gates"]["liquidate_batch_ok"],
                           zero_snapshot_settles_at_0="PT-02",
                           guardian_can_clear="no (unpauseMarket reverts 0xd9d193d3 for every caller)"),
            "missing_observation": "an archive trace of a liquidation or a close executed while a "
                                   "market was paused, and whether HyperCore has ever returned a zero "
                                   "or crossed raw BBO for a live instrument (raw getBBO accepts both "
                                   "without a check); no market is paused on chain today",
            "citations": ["FINDINGS.md PT-02", "AUDIT.md A9",
                          "atlas/block_48902346/exchange_pause_pseudocode.md",
                          "atlas/block_48902346/live2_pricing.md LP-02, LP-09"],
        },
        {
            "id": "RL-06",
            "title": "The guardian's other powers are bounded: the global pause freezes opens only and "
                     "is guardian-irreversible, and the registry guardian can only deny an accrual",
            "angle": "Guardian (setTradingPaused, BuilderRegistry removeBuilder)",
            "invariant": "A1 + A5",
            "actor": "pause guardian (multisig) / BuilderRegistry guardian",
            "precondition": "Exchange slot 1 = guardian; BuilderRegistry slot 1 bits 0..159 = guardian",
            "trigger": "setTradingPaused(true) from the guardian; the same signed open with and without the "
                       "pause byte; removeBuilder(address) from the guardian",
            "impact": "The guardian can set the venue-wide pause byte but is denied every other pause "
                      "action: the keeper and the market keeper both get NotPauseAuthority 0x49199FB6 "
                      "on setTradingPaused and on pauseMarket, and the guardian itself is denied on "
                      "clearing (resume) while the owner can. With the pause byte set and the session "
                      "address preserved in the upper bits, a signed open that succeeds while unpaused "
                      "reverts with the public-registry candidate TradingPaused() 0x02b874a6, while "
                      "closes and liquidations still settle, so the global pause is an open-side "
                      "freeze, not an exit freeze, and it cannot be undone by the guardian. The "
                      "BuilderRegistry guardian can remove an approved builder but not add one or "
                      "change the rate (pass-one L2A-06), and no registry-approval path reaches the "
                      "Exchange (RL-04), so that power has no trade effect today.",
            "affected": "both",
            "severity": "low",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay plus first-party negative controls",
            "evidence": ev("role_pause_surface, role_global_pause_gates, role_global_pause_open",
                           guardian_pause=o["role_pause_surface"]["guardian_global_pause"],
                           guardian_resume=hex(o["role_pause_surface"]["guardian_global_resume"]),
                           owner_resume=o["role_pause_surface"]["owner_global_resume"],
                           outsider_pause=hex(o["role_pause_surface"]["outsider_global_pause"]),
                           keeper_market_pause=hex(o["role_pause_surface"]["keeper_market_pause"]),
                           close_while_paused=o["role_global_pause_gates"]["close_ok"],
                           open_unpaused=o["role_global_pause_open"]["flag0_selector"],
                           open_paused=o["role_global_pause_open"]["flag1_selector"]),
            "missing_observation": "the source name behind 0x02b874a6 (public-registry candidate "
                                   "TradingPaused(), unverified); and no TradingPausedUpdated log "
                                   "exists in history, so the pause has never been used live",
            "citations": ["atlas/block_48902346/exchange_pause_pseudocode.md",
                          "atlas/block_48902346/live2_authority.md L2A-06, L2A-10"],
        },
        {
            "id": "RL-07",
            "title": "Role ranking: worst-case loss per action, its bound, and whether it repeats",
            "angle": "Ranking across all four roles",
            "invariant": "A4 + A9 + proposed A8",
            "actor": "keeper, market keeper, relayer, pause guardian, builder",
            "precondition": "the live role holders above",
            "trigger": "n/a (consolidated ranking of RL-01..RL-06)",
            "impact": "authorizedKeeper: worst case is flipping one opaque byte, loss 0 (no fee, no "
                      "pause, no intent, no healthy liquidation), bounded by the owner's slot-89 set, "
                      "repeatable per call with no effect. marketKeeper: worst case is maxing the "
                      "per-side open caps so opens the configured cap rejects succeed, loss up to the "
                      "LP bankroll plus an unfunded queue claim, bounded by the per-position size "
                      "limit but by nothing on payout and repeatable on every open. relayer: "
                      "worst case is delay or censorship of a signed intent, loss 0 on chain, bounded "
                      "by the signed deadline, repeatable. pause guardian: worst case is one free "
                      "exit per instrument at a frozen fake price, loss up to margin x leverage (and "
                      "the LP bankroll at a zero snapshot), bounded only by the LP bankroll and by the "
                      "position having to pre-exist, not repeatable within one instrument. builder: "
                      "worst case is 0 through every tested close shape. The single action not bounded "
                      "by a cap, a user signature or an owner gate is the guardian's pauseMarket "
                      "combined with a close.",
            "affected": "both",
            "severity": "info",
            "status": "confirmed_simulation",
            "evidence_tier": "consolidated from the rows above",
            "evidence": ev("RL-01..RL-06 plus pass-one LP-05 and PT-02",
                           unbounded_action="guardian pauseMarket then close (RL-05)",
                           keeper_writes="1 opaque byte", relayer_value_transfer=0,
                           builder_per_close_skim=0,
                           market_keeper_cap_maximum=str(2**128 - 1)),
            "missing_observation": "the LP bankroll and queue state at the moment of any such action "
                                   "(both are live reads, not pinned), and whether the paused-market "
                                   "case has ever occurred",
            "citations": ["FINDINGS.md PT-02", "atlas/block_48902346/live2_pricing.md LP-05",
                          "atlas/block_48902346/live2_authority.md L2A-10"],
        },
    ]


def write_artifacts(runtimes, observations, source_sha):
    ledger = {
        "audit": "semi-trusted roles (keeper, market keeper, relayer, pause guardian, builder)",
        "pin": PIN,
        "pin_block_hash": PIN_HASH,
        "generated_by": "audit_live2_roles.py",
        "scope": "set-2 runtimes behind the live proxies, compared against the pinned behaviour where "
                 "the pinned runtime is needed; the pinned Exchange is never the target of a role attack",
        "live_set": {
            "exchange_implementation": I.EXCHANGE_IMPL_2,
            "session_key_manager_implementation": I.SESSION_IMPL_2,
            "exchange_linked_library": LIBRARY_2,
            "builder_registry": BUILDER_REGISTRY,
            "runtime_sha256": {"exchange_implementation":
                                   hashlib.sha256(bytes.fromhex(runtimes["exchange_impl"][2:])).hexdigest(),
                               "session_key_manager_implementation":
                                   hashlib.sha256(bytes.fromhex(runtimes["session_impl"][2:])).hexdigest(),
                               "exchange_linked_library":
                                   hashlib.sha256(bytes.fromhex(runtimes["library"][2:])).hexdigest(),
                               "builder_registry":
                                   hashlib.sha256(bytes.fromhex(runtimes["builder_registry"][2:])).hexdigest()},
        },
        "roles_at_head": {
            "owner": {"exchange_session_tokenomics_paper_staking_registry_proxyadmin": OWNER},
            "pause_guardian": PAUSE_GUARDIAN,
            "authorized_executor_slot_88": BATCH,
            "authorized_keeper_slot_89": KEEPER,
            "market_keeper_slot_37": MARKET_KEEPER,
            "builder_registry_fee_rate_raw": "5e15 (0.5 %)",
            "builder_registry_fee_rate_cap_raw": "1e16 (1 %)",
        },
        "error_names": {hex(k): v for k, v in ERRORS.items()},
        "observations": observations,
        "role_ranking": {
            "note": "RL-07 is an informational ranking, not a finding; this workstream's findings are "
                    "RL-02 (medium) and RL-05 (high) only",
            "rows": [
                {"role": "authorizedKeeper", "worst_action": "flip the slot-8 byte",
                 "worst_case_loss": "0", "bound": "owner sets slot 89",
                 "repeats": "every call, no effect"},
                {"role": "marketKeeper", "worst_action": "max both per-side open caps",
                 "worst_case_loss": "opens the configured cap rejects succeed; up to the LP bankroll",
                 "bound": "the per-position size limit only, nothing on payout",
                 "repeats": "every open"},
                {"role": "relayer", "worst_action": "delay or drop a sealed intent",
                 "worst_case_loss": "0 on chain", "bound": "the signed deadline",
                 "repeats": "every intent"},
                {"role": "pause guardian", "worst_action": "pause a market then close",
                 "worst_case_loss": "margin x leverage, up to the LP bankroll",
                 "bound": "the LP bankroll; one shot per instrument",
                 "repeats": "once per instrument"},
                {"role": "builder", "worst_action": "none found", "worst_case_loss": "0",
                 "bound": "n/a", "repeats": "n/a"},
            ],
            "unbounded_action": "the guardian's pauseMarket followed by a close (RL-05): not bounded "
                                "by a cap, a user signature or an owner gate",
        },
        "harness": {"source_sha256": source_sha, "tests": "role arms plus the pass-one set-2 cases",
                    "offline_rebuild": "python3 scripts/audit_live2_roles.py --from-saved re-emits this "
                                       "ledger and doc from the saved forge replay, no Forge run",
                    "forge_replay": "artifacts/live2_roles/replay.json",
                    "generated_solidity": "artifacts/live2_roles/RoleLocal.t.sol"},
        "rows": rows(runtimes, observations),
        "coverage": {
            "keeper": ["RL-01", "RL-02", "RL-07"],
            "relayer": ["RL-03", "RL-04", "RL-07"],
            "guardian": ["RL-05", "RL-06", "RL-07"],
            "builder": ["RL-04", "RL-07"],
            "ranking": ["RL-07"],
        },
        "limits": [
            "Every row is bytecode-level evidence: the closes, liquidations and the registry view are "
            "exact-runtime simulations of the pinned storage with a mocked HyperCore BBO and a stubbed "
            "Tokenomics, so they are simulations, not live observations.",
            "The Tokenomics side contract is replaced by a zero-returning stub so a fee-paying close "
            "can complete; the Exchange-side writes and the absence of any slot-39 or registry access "
            "are the measured facts, and a real Tokenomics cannot make an Exchange-side mapping entry "
            "appear.",
            "The open path reverts post-signer (0x0a4f5a07) on the set-2 runtime under synthetic "
            "state, so the keeper-flag and global-pause effects on opens, and the capped-open "
            "consequence in RL-02, rest on pass-one's 57 saved opens rather than on new arms.",
            "A role address could itself be a contract with more code; the head reads in "
            "atlas/block_48902346/live2_authority.md do not settle that, and nothing here assumes it.",
            "Nothing here was disclosed, filed or executed; no transaction, upgrade or governance "
            "action was performed and no market was paused.",
        ],
        "reduce": [
            "python3 scripts/audit_live2_roles.py",
            "the orchestrator's atlas_verify.py covers the consolidated ledger, not this workstream "
            "file",
        ],
    }
    LEDGER.write_text(json.dumps(ledger, indent=1) + "\n")
    DOC.write_text(render_doc(ledger))
    return ledger


def render_doc(ledger):
    o = ledger["observations"]
    lines = [
        "# Semi-trusted roles on the live Papertrade code (pass two)",
        "",
        "Generated by [`audit_live2_roles.py`](../../scripts/audit_live2_roles.py) from the saved set-2 runtime "
        "bytes under `artifacts/postpin_suite/runtime/`, the pinned behaviour where it is the "
        "comparison, and the port-free Forge replay at `artifacts/live2_roles/replay.json`. "
        "`python3 scripts/audit_live2_roles.py` re-checks every claim offline and needs no RPC credential.",
        "",
        "Pass one established who holds each role and which selectors are gated on it. This pass asks "
        "the next question: what can a compromised or greedy role holder do to users or the LP while "
        "staying inside its permissions. Every result below is a simulation of the exact runtimes "
        "against pinned storage with mocked HyperCore reads; a mocked read is never a live "
        "observation. Nothing here is a disclosure and no transaction was sent.",
        "",
        "## The roles at the live head",
        "",
        "| Role | Holder | What the role can reach | Worst case found |",
        "|---|---|---|---|",
        "| owner | timelock `0xb915fa41...` | everything | (pass one, out of scope here) |",
        "| pause guardian | multisig `0x69629276...` (2 of 3) | pause a market, pause the venue, never resume | **RL-05, high**: a free exit at a frozen quote, no cap |",
        "| authorizedExecutor (slot 88) | BatchExecutor `0x233ff29b...` | relay sealed intents | relay only (RL-03) |",
        "| authorizedKeeper (slot 89) | `0x0924736b...` | one slot-8 byte | **RL-01, none** |",
        "| marketKeeper (slot 37) | `0x3721476d...` | per-side open caps, slot 28 | **RL-02, medium** |",
        "| relayer | any `authorizedRelayers` entry | submit allowed selectors | **RL-03, none on chain** |",
        "| builder | any approved address | claim its own accrual | **RL-04, none: no close credits it** |",
        "",
        "Set-2 runtime hashes re-checked on every run: Exchange `"
        + ledger["live_set"]["runtime_sha256"]["exchange_implementation"][:16] + "...`, SessionKeyManager `"
        + ledger["live_set"]["runtime_sha256"]["session_key_manager_implementation"][:16] + "...`, library `"
        + ledger["live_set"]["runtime_sha256"]["exchange_linked_library"][:16] + "...`, BuilderRegistry `"
        + ledger["live_set"]["runtime_sha256"]["builder_registry"][:16] + "...`.",
        "",
        "## Findings ledger",
        "",
        "| ID | Title | Invariant | Actor | Affected | Severity | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in ledger["rows"]:
        lines.append("| `{}` | {} | {} | {} | {} | {} | `{}` |".format(
            row["id"], row["title"], row["invariant"], row["actor"], row["affected"],
            row["severity"], row["status"]))
    lines += ["", "## Angle 1: keeper", "",
              "The keeper role splits in two. `authorizedKeeper` (Exchange slot 89) is the address the "
              "2026-10-21 batch wired, and the only selector it unlocks is the added `0xe6ac4a74(bool)`, "
              "which writes one byte above `instrumentCount` at Exchange slot 8. `marketKeeper` "
              "(slot 37) is the older role that writes the per-side open limits and the two unnamed "
              "slot-28 fields.", ""]
    for row in ledger["rows"]:
        if row["id"] not in ("RL-01", "RL-02"):
            continue
        lines += [f"### `{row['id']}` {row['title']}", "",
                  f"- Angle: {row['angle']}; invariant {row['invariant']}; actor: {row['actor']}",
                  f"- Precondition: {row['precondition']}", f"- Trigger: {row['trigger']}",
                  f"- Impact: {row['impact']}", f"- Evidence: {row['evidence_tier']}",
                  f"- Missing observation: {row['missing_observation']}", ""]
    lines += ["Measured, first hand, on the set-2 runtimes (all in "
              "`artifacts/live2_roles/replay.json`):", "",
              "| Probe | Result |", "|---|---|",
              "| keeper `0xe6ac4a74(true)` | accepted (selector 0), byte written |",
              "| keeper `setFeeRates(1,1,1)` | `NotOwner()` `0x30cd7471`, slot 24 still `2e16` |",
              "| keeper submits a signed close | `0xda96f0b6` (not the authorized executor) |",
              "| keeper / marketKeeper `pauseMarket` | `NotPauseAuthority()` `0x49199fb6` |",
              "| marketKeeper `0x628a9fd6(0, max, max)` | accepted, caps set to maximum |",
              "| marketKeeper `0x82f47a3f(max, max)` | accepted, slot 28 = `2**256-1` |",
              "| marketKeeper `0x5ca4c0ea` instrument setter | `NotOwner()` `0x30cd7471` |",
              "| outsider `liquidateBatch([healthy])` | succeeds, 0 events, active bit kept |",
              "| outsider `liquidateBatch([underwater])` | succeeds, 1 `Liquidated`, active bit cleared |",
              "",
              "So a keeper cannot liquidate a healthy position (the eligibility formula from pass "
              "one's boundary table decides, and the batch silently skips an ineligible id), cannot "
              "move a fee, and cannot take the pause. What the market keeper can do is remove the "
              "configured aggregate per-side open-interest bound, which is the only guard the audit "
              "has found on the signed-open path.",
              "", "## Angle 2: relayer", ""]
    for row in ledger["rows"]:
        if row["id"] != "RL-03":
            continue
        lines += [f"### `{row['id']}` {row['title']}", "",
                  f"- Angle: {row['angle']}; invariant {row['invariant']}; actor: {row['actor']}",
                  f"- Precondition: {row['precondition']}", f"- Trigger: {row['trigger']}",
                  f"- Impact: {row['impact']}", f"- Missing observation: {row['missing_observation']}",
                  ""]
    lines += ["| Probe | Result |", "|---|---|",
              "| Same signed close submitted twice | first closes, second `InvalidNonce()` `0x756688fe` |",
              "| Signature over id 1, calldata id 2 | `SessionKeyNotAuthorized()` `0xc5045f22` |",
              "| Signature over USER, calldata OUTSIDER | `SessionKeyNotAuthorized()` `0xc5045f22` |",
              "| Two closes in order (1,2) vs (2,1) | both settle at the same Oracle midpoint `150` |",
              "| Signed withdrawal, recipient in the CoreWriter payload | the signed user |",
              "| Signed withdrawal with calldata user = OUTSIDER | `0xc20280ea` |",
              "",
              "The structural reason the relayer cannot do more: for a close or an open the Exchange "
              "sees `msg.sender == BatchExecutor`, so the Exchange cannot key any state on the relayer "
              "address, and every field the relayer could change is inside the EIP-712 digest. Its "
              "residual power is choosing when, and whether, to include a sealed intent.",
              "", "## Angle 3: guardian", ""]
    for row in ledger["rows"]:
        if row["id"] not in ("RL-05", "RL-06"):
            continue
        lines += [f"### `{row['id']}` {row['title']}", "",
                  f"- Angle: {row['angle']}; invariant {row['invariant']}; actor: {row['actor']}",
                  f"- Precondition: {row['precondition']}", f"- Trigger: {row['trigger']}",
                  f"- Impact: {row['impact']}", f"- Missing observation: {row['missing_observation']}",
                  ""]
    lines += ["The guardian angle deliberately asks the pass-one PT-02 facts a new question: not "
              "'is the pause broken' but 'who profits from it'. The answer is whoever already "
              "holds a position, and the guardian chooses the moment. The two named hypotheses are "
              "settled in opposite directions: a pause cannot block a rival's exit, because closes "
              "and liquidations still settle while the venue is paused, but a pause can freeze a price "
              "that the guardian's own close then uses, which is the free-option case in RL-05.",
              "", "## Angle 4: builder", ""]
    for row in ledger["rows"]:
        if row["id"] != "RL-04":
            continue
        lines += [f"### `{row['id']}` {row['title']}", "",
                  f"- Angle: {row['angle']}; invariant {row['invariant']}; actor: {row['actor']}",
                  f"- Precondition: {row['precondition']}", f"- Trigger: {row['trigger']}",
                  f"- Impact: {row['impact']}", f"- Missing observation: {row['missing_observation']}",
                  ""]
    lines += ["Five fee-paying closes, each with a real fee charged to slot 26:", "",
              "| Arm | Close | slot-39 reads | slot-39 writes | credited | slot-38 | registry accesses |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for arm, label in (("plain", "plain seven-argument close"), ("id7", "a second position id"),
                       ("trailing", "an appended 8th calldata word naming the keeper"),
                       ("approved", "all fourteen candidate addresses approved in the registry"),
                       ("loss", "a loss close")):
        r = o[f"role_builder_{arm}"]
        lines.append("| `{}` | {} | {} | {} | {} | {} | {} |".format(
            arm, label, r["slot39_read_bits"], r["slot39_write_bits"], r["credited_value"],
            r["shared_counter"], r["registry_accesses"]))
    lines += ["", "The pass-one open question ('whether the signed close binds the builder field') "
              "resolves to a stronger statement than 'it is not signed': the close does not credit a "
              "builder at all, and never calls the registry, so no relayer, frontend or front-end "
              "builder choice can attach a fee to a close and the per-close skim is zero.",
              "", "## Angle 5: ranking", ""]
    for row in ledger["rows"]:
        if row["id"] != "RL-07":
            continue
        lines += [f"### `{row['id']}` {row['title']}", "", f"- Impact: {row['impact']}", ""]
    lines += ["| Role | Worst action | Worst-case loss | Bound | Repeats |", "|---|---|---|---|---|",
              "| authorizedKeeper | flip the slot-8 byte | 0 | owner sets slot 89 | every call, no effect |",
              "| marketKeeper | max both per-side caps | opens the configured cap rejects succeed; up to the LP bankroll | the per-position size limit only, nothing on payout | every open |",
              "| relayer | delay or drop a sealed intent | 0 on chain | the signed deadline | every intent |",
              "| pause guardian | pause a market then close | margin x leverage, up to the LP bankroll | the LP bankroll; one shot per instrument | once per instrument |",
              "| builder | none found | 0 | n/a | n/a |",
              "",
              "One role action is not bounded by a cap, a user signature or an owner gate: the "
              "guardian's `pauseMarket` followed by a close (RL-05). Everything else is bounded by a "
              "cap, a signature, the owner, or turns out to move nothing.",
              "", "## Limits", ""]
    for item in ledger["limits"]:
        lines.append(f"- {item}")
    lines.append("")
    return chr(10).join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--record", action="store_true", help="print observations instead of asserting")
    parser.add_argument("--from-saved", action="store_true",
                        help="rebuild the ledger and doc from the saved forge replay, no Forge run")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.capture:
        print("no live capture is needed for this workstream; the saved pin reads suffice")
        return

    runtimes = I.load_runtimes()
    if args.from_saved:
        saved = json.loads((OUT_DIR / "replay.json").read_text())
        write_artifacts(runtimes, {k: v for k, v in saved["observations"].items()
                                   if k.startswith("role_")}, saved["source_sha256"])
        print("  rebuilt the ledger and doc from artifacts/live2_roles/replay.json (no Forge run)")
        return
    base_proxy = (ATLAS / runtimes["_manifest"]["contracts"]
                  ["0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"]["runtime_file"]).read_text().strip()
    files = runtime_files(runtimes, base_proxy)
    source = build_source()
    (OUT_DIR / "RoleLocal.t.sol").write_text(source)
    files["__source_sha256__"] = None
    del files["__source_sha256__"]
    output, raw_observations = I.run_forge(source, files, "live2-roles", timeout=600,
                                           raise_on_failure=False)
    observations = {}
    for key, value in raw_observations.items():
        base, _, part = key.rpartition("_")
        if part in ("a", "b") and base + "_a" in raw_observations and base + "_b" in raw_observations:
            merged = dict(raw_observations[base + "_a"])
            merged.update({k: v for k, v in raw_observations[base + "_b"].items() if k != "name"})
            merged["name"] = base
            observations[base] = merged
        elif not (part in ("a", "b") and (base + "_" + ("b" if part == "a" else "a")) in raw_observations):
            observations[key] = value
    passed = sorted(re.findall(r"\[PASS\] (test\w+)", output))
    failed = re.findall(r"\[FAIL[^\]]*\]\s*\n?\s*(test\w+)", output)
    result = {"forge": pathlib.Path(shutil.which("forge") or "forge").name, "tests_passed": passed, "tests_failed": failed,
              "observations": observations, "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "runtimes": {k: hashlib.sha256(bytes.fromhex(v[2:])).hexdigest()
                           for k, v in files.items() if isinstance(v, str) and v.startswith("0x")
                           and k in ("ExchangeImpl2", "SessionImpl2", "Library2", "BuilderRegistry")},
              "tail": output[-6000:]}
    role_observations = {k: v for k, v in observations.items() if k.startswith("role_")}
    (OUT_DIR / "replay.json").write_text(json.dumps(result, indent=1) + "\n")
    if failed:
        raise RuntimeError(f"role suite failures: {failed}\n{output[-8000:]}")
    expected_role_tests = {
        "testRoleBuilderApprovedCandidates", "testRoleBuilderKeyFeePayingClose",
        "testRoleBuilderKeyOtherPositionId", "testRoleBuilderLossClose",
        "testRoleBuilderTrailingWord", "testRoleGlobalPauseGates", "testRoleKeeperFlagGates",
        "testRoleKeeperLiquidationBoundary", "testRoleKeeperSurface", "testRolePauseSurface",
        "testRoleRelayerBatch", "testRoleRelayerOrder", "testRoleRelayerWithdrawRecipient",
    }
    assert expected_role_tests <= set(passed), sorted(expected_role_tests - set(passed))
    assert len(passed) >= 55, len(passed)
    for name, expected in EXPECTED.items():
        got = role_observations.get(name)
        assert got is not None, name
        for key, value in expected.items():
            assert got.get(key) == value, (name, key, got.get(key), value)
    assert sorted(role_observations) == sorted(EXPECTED), sorted(set(role_observations) ^ set(EXPECTED))
    assert not observed_extra(role_observations), observed_extra(role_observations)
    ledger = write_artifacts(runtimes, role_observations, result["source_sha256"])
    print(f"  role arms: {len(expected_role_tests)} passed, 0 failed; "
          f"{len(passed)} cases total in the set-2 suite")
    print(f"  runtime hashes: " + ", ".join(f"{k} {v[:12]}" for k, v in
                                            ledger["live_set"]["runtime_sha256"].items()))
    print(f"  builder arms: slot39 reads/writes "
          f"{sum(role_observations[f'role_builder_{a}']['slot39_read_bits'] for a in ('plain','id7','trailing','approved','loss'))}"
          f"/{sum(role_observations[f'role_builder_{a}']['slot39_write_bits'] for a in ('plain','id7','trailing','approved','loss'))}, "
          f"registry accesses "
          f"{sum(role_observations[f'role_builder_{a}']['registry_accesses'] for a in ('plain','id7','trailing','approved','loss'))}")
    print(f"  ledger: {len(ledger['rows'])} rows -> {LEDGER.relative_to(ROOT)} and {DOC.relative_to(ROOT)}")
    for status in ("confirmed_live", "confirmed_simulation", "plausible_unproven", "disproved",
                   "blocked"):
        ids = [r["id"] for r in ledger["rows"] if r["status"] == status]
        if ids:
            print(f"  {status}: {len(ids)} ({', '.join(ids)})")


def observed_extra(observations):
    """Any observation key that is a role arm but not expected."""
    return sorted(k for k in observations if k.startswith("role_builder") and k not in EXPECTED)


if __name__ == "__main__":
    main()
