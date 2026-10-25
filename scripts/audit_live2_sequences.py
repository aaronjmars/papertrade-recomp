#!/usr/bin/env python3
"""Sequences of individually legitimate actions against the live Papertrade set.

Question: does any ordering, repetition, batching or size choice make the books drift, i.e.
let a user end up with more claim than the value they put in, or leave the LP unable to pay
what the state says it owes.

Instrument: a port-free Foundry replay of the exact runtimes loaded on the saved
block-48,901,631 prestate, driving the real signed open 0xec6783f0, the real signed close
0x2792e706, the real signed withdrawal 0x8d09f23f, the real liquidateBatch 0x599dc539, the
real harvest 0xddc63262 and the real BatchExecutor executeBatch 0x251fb27d. The HyperCore BBO
precompile 0x080e and the HyperCore account-status precompile 0x0810 are the only mocked
inputs; every mocked reply is labelled simulated. Positions are created by the venue's own
signed open, never written into storage by hand, so every sequence starts from a state the
venue itself produced.

Value-conservation invariant (established at the pin by atlas_all_suite_claims.py and by the
availability formulas in exchange_storage_behavior.md):

    treasury == ordinary balances + locked margin + total queued
              + staker fee reserve + developer fee reserve
              + signed tracked LP + side bucket

    Exchange slot 14            treasury
    Exchange slot 22 low 128    ordinary balances (totalBalances)
    Exchange slot 22 high 128   locked margin (totalLockedMargin)
    Exchange slot 18            total queued
    Exchange slot 26 low 128    staker fee accumulator
    Exchange slot 26 high 128   developer fee accumulator
    Tokenomics slot 3 (signed)  tracked LP
    Exchange slot 27 (signed)   side bucket

Every step of every sequence records all eight components and the residual
(treasury - claims). Residual zero means no value was created or destroyed on that step; a
nonzero residual names the exact step that broke the books and by how much. The checker is
validated by a negative control that must break it.

Usage:

    python3 scripts/audit_live2_sequences.py              # both variants, offline, no credential
    python3 scripts/audit_live2_sequences.py --variant live
"""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "live2_sequences"
REPLAY_PATH = OUT / "replay.json"

PIN = 48902346
PIN_HASH = "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
PRESTATE_BLOCK = 48901631
PRESTATE_TIMESTAMP = 0x6AD5311E

EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
PAPER = "0xe40f17915daa230324030003a197cdaef2261c0e"
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
USER = "0xe05fcc23807536bee418f142d19fa0d21bb0cff7"
KEEPER = "0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56"
STRANGER = "0x1111111111111111111111111111111111111111"
RELAYER = "0x2222222222222222222222222222222222222222"

LIVE_IMPLEMENTATION = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
LIVE_LIBRARY = "0x583d0bd818c991c5830fea93aef04e474b272459"
LIVE_SESSION_IMPL = "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946"
LIVE_TOKENOMICS_IMPL = "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03"
PIN_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN_LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
PIN_SESSION_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
PIN_TOKENOMICS_IMPL = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"

EIP1967_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
INSTRUMENT_ETH = 1
INSTRUMENT_ROOT_ETH = "0xb39221ace053465ec3453ce2b36430bd138b997ecea25c1043da0c366812b828"
MARKET_ROOT_ETH = "0xbbbb3b1da0cb0951f34c5e9db4606f934b7367b5284f29163e9e6fe67e1e97d6"
ENTRY_PRICE = 251085
BID, ASK = 251080, 251090
WAD = 10 ** 18
SLOT_NEXT_POSITION = 11
SLOT_TREASURY = 14
SLOT_TOTAL_QUEUED = 18
SLOT_TOTAL_BALANCES = 22
SLOT_SIDE_BUCKET = 27
SLOT_FEE_ACCUMULATORS = 26
SLOT_TRACKED_LP = 3
SLOT_PAPER_SUPPLY = 6

OPEN_SELECTOR = "0xec6783f0"
CLOSE_SELECTOR = "0x2792e706"
WITHDRAW_SELECTOR = "0x8d09f23f"
LIQUIDATE_BATCH = "0x599dc539"
HARVEST_SELECTOR = "0xddc63262"
PUSH_STAKER_FEES = "0x7b9f5264"
EXECUTE_BATCH = "0x251fb27d"
LP_BANKROLL = "0x0cdd5fc4"
QUEUE_HARVEST = "0x53ac4b66"      # totalQueued()
SIDE_BUCKET_GETTER = "0x9274682e"
CLOSE_TYPEHASH = "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13"
OPEN_TYPEHASH = "0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983"
WITHDRAW_TYPE_STRING = "WithdrawToCore(address user,uint256 amount,uint256 nonce,uint64 deadline)"
CLOSE_DOMAIN = "0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77"
TOPIC_CLOSED = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
TOPIC_LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
TOPIC_ENQUEUED = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
TOPIC_SIDEBUCKET = "0xc2a40711"
TOPIC_CALL_EXECUTED = "0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad"

PRESTATE = ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json"
PINNED_GETTERS = ROOT / "artifacts" / "exchange_instruments_getter" / "pinned_getters.json"
PINNED_FIELDS = ROOT / "artifacts" / "exchange_market_fields" / "pinned_probes.json"
LIVE_CAPTURE = ROOT / "artifacts" / "audit_certik_haircut" / "live"
POSTPIN_RUNTIME = ROOT / "artifacts" / "postpin_suite" / "runtime"
PIN_RUNTIME = ATLAS / "runtime"

RUNTS = {
    "live": {
        LIVE_IMPLEMENTATION: ("capture", "implementation.hex", "fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268"),
        LIVE_LIBRARY: ("capture", "linked_583d0bd818c991c5830fea93aef04e474b272459.hex", "ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440"),
        LIVE_SESSION_IMPL: ("capture", "session_manager_implementation.hex", "7df05c33597c04820a314fae015aab01b5566aff53e9bded8446962cfd4ad2c9"),
        LIVE_TOKENOMICS_IMPL: ("postpin", "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03.hex", "56caf868c73dbc33b94725972fc101dbcec0fb7b017c4f2f9e8cda49516992e9"),
    },
    "pinned": {
        PIN_IMPLEMENTATION: ("pin", "0f3febfc94876b0c895f7acecdc8f5c863b549ee.hex", None),
        PIN_LIBRARY: ("pin", "cd617f984158a4f5d287ddee0e8eb0fed204916d.hex", None),
        PIN_SESSION_IMPL: ("pin", "8a5069fe303e8f81e91825436e956d595032e558.hex", None),
        PIN_TOKENOMICS_IMPL: ("pin", "600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f.hex", None),
    },
}


def u256(value):
    return "0x" + format(value % (1 << 256), "064x")


def s_address(value):
    return "address(uint160(uint256(0x00" + value[2:] + ")))"


def sha256_hex(payload):
    return hashlib.sha256(payload).hexdigest()


def runtime_hex(kind, name):
    if kind == "capture":
        return (LIVE_CAPTURE / name).read_text().strip()
    if kind == "postpin":
        return (POSTPIN_RUNTIME / name).read_text().strip()
    return (PIN_RUNTIME / f"0x{name}").read_text().strip()


def variants():
    out = {}
    for tag, roles in RUNTS.items():
        files = {}
        for address, (kind, name, digest) in roles.items():
            raw = runtime_hex(kind, name)
            if digest:
                assert sha256_hex(bytes.fromhex(raw[2:])) == digest, address
            files[address] = raw
        out[tag] = {"roles": roles, "files": files}
    return out


def prestate():
    return json.loads(PRESTATE.read_text())


def load_prestate_lines():
    lines = []
    for a, row in sorted(prestate().items()):
        if row.get("code", "0x") != "0x":
            lines.append(f'        vm.etch({s_address(a)}, vm.parseBytes(vm.readFile("runtime/{a[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                lines.append(f"        vm.store({s_address(a)}, {slot}, {value});")
    return lines


def pack_instrument(words):
    """Repack the getter-decoded pinned instrument record into its three storage words."""
    return [words[0] | (words[1] << 96) | (words[2] << 192) | (words[3] << 224),
            words[4] | (words[5] << 120) | (words[6] << 184),
            words[7]]


def pinned_instrument_words():
    getters = json.loads(PINNED_GETTERS.read_text())
    assert getters["pin"] == PIN and getters["block_hash"] == PIN_HASH
    row = next(r for r in getters["rows"] if r["instrument_id"] == INSTRUMENT_ETH)
    raw = row["getter_output"][2:]
    words = [int(raw[i:i + 64], 16) for i in range(0, len(raw), 64)]
    assert words[6] == WAD // 10 and words[7] == 100000 * WAD
    assert [u256(w) for w in pack_instrument(words)] == [u256(int(v, 16)) for v in live_probes()["instrument_words"].values()]
    return pack_instrument(words)


def live_probes():
    return json.loads((LIVE_CAPTURE / "raw" / "storage_probes.json").read_text())


def pinned_market_words():
    fields = json.loads(PINNED_FIELDS.read_text())
    assert fields["pin_block"] == PIN and fields["pin_hash"] == PIN_HASH
    market = next(r for r in fields["markets"] if r["instrument"] == INSTRUMENT_ETH)
    assert int(market["base_slot"], 16) == int(MARKET_ROOT_ETH, 16)
    return [int(word, 16) for word in market["raw_words"]]


def fixture_lines(variant):
    """Runtimes on their proxies, the instrument and market record, and the mocked precompiles."""
    lines = []
    if variant == "live":
        for address, raw in variants()["live"]["files"].items():
            lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
        lines.append(f"        vm.store({s_address(EXCHANGE)}, {EIP1967_SLOT}, {u256(int(LIVE_IMPLEMENTATION, 16))});")
        lines.append(f"        vm.store({s_address(SESSION)}, {EIP1967_SLOT}, {u256(int(LIVE_SESSION_IMPL, 16))});")
        lines.append(f"        vm.store({s_address(TOKENOMICS)}, {EIP1967_SLOT}, {u256(int(LIVE_TOKENOMICS_IMPL, 16))});")
        instrument = pinned_instrument_words()
        market = [int(v, 16) for v in live_probes()["market_words"].values()]
        config = live_probes()["config_slots"]
        lines.append(f"        vm.store({s_address(EXCHANGE)}, {u256(8)}, {u256(int(config['8'], 16))});")
        lines.append(f"        vm.store({s_address(EXCHANGE)}, {u256(25)}, {u256(int(config['25'], 16))});")
    else:
        instrument = pinned_instrument_words()
        market = pinned_market_words()
        lines.append(f"        vm.store({s_address(EXCHANGE)}, {u256(25)}, {u256(2 * 10 ** 16)});")
    for i, word in enumerate(instrument):
        lines.append(f"        vm.store({s_address(EXCHANGE)}, {u256(int(INSTRUMENT_ROOT_ETH, 16) + i)}, {u256(word)});")
    for i, word in enumerate(market):
        lines.append(f"        vm.store({s_address(EXCHANGE)}, {u256(int(MARKET_ROOT_ETH, 16) + i)}, {u256(word)});")
    lines.append('        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(1)), '
                 f'abi.encode(uint256({BID}), uint256({ASK})));')
    return lines


def typehash(signature):
    return "0x" + Keccak()(signature.encode()).hex()


# ------------------------------------------------------------------ solidity

SOLIDITY = r'''pragma solidity ^0.8.24;

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function warp(uint256) external;
    function roll(uint256) external;
    function chainId(uint256) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function sign(uint256, bytes32) external returns (uint8, bytes32, bytes32);
    function addr(uint256) external returns (address);
    function writeLine(string calldata, string calldata) external;
    function record() external;
    function accesses(address) external returns (bytes32[] memory reads, bytes32[] memory writes);
}

contract SequenceTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = ADDR_EXCHANGE;
    address constant SESSION = ADDR_SESSION;
    address constant BATCH = ADDR_BATCH;
    address constant TOKENOMICS = ADDR_TOKENOMICS;
    address constant PAPER = ADDR_PAPER;
    address constant KEEPER = ADDR_KEEPER;
    address constant RELAYER = ADDR_RELAYER;
    address constant STAKING = ADDR_STAKING;
    address constant STRANGER = ADDR_STRANGER;
    address constant OWNER = ADDR_OWNER;
    bytes32 constant CLOSE_TYPEHASH = TH_CLOSE;
    bytes32 constant OPEN_TYPEHASH = TH_OPEN;
    bytes32 constant WITHDRAW_TYPEHASH = TH_WITHDRAW;
    bytes32 constant DOMAIN = DOMAIN_V;
    bytes32 constant CLOSED_TOPIC = TOPIC_CLOSED;
    bytes32 constant LIQUIDATED_TOPIC = TOPIC_LIQ;
    bytes32 constant ENQUEUED_TOPIC = TOPIC_ENQ;
    bytes32 constant CALL_EXECUTED_TOPIC = TOPIC_CE;
    uint256 constant INST = 1;
    uint256 constant WAD = 1e18;
    uint256 constant BIG = 4982012573755118958351370;
    uint256 constant PK = 0xb0b;
    uint256 constant USER_KEY = 0xa11ce;
    address constant STATUS = address(uint160(0x0810));
    // The signed open and close are session-key signed; the signed withdrawal is user signed,
    // so the user is a key this harness holds.
    address USER;

    struct Call { address target; bytes data; bool continueOnFailure; bytes32 intentId; bytes32 extra; }

    function setUp() public {
        vm.chainId(999);
        vm.roll(ROLLV);
        vm.warp(WARPV);
        USER = vm.addr(USER_KEY);
        // The BatchExecutor gates executeBatch on authorizedRelayers (mapping base 4): mirror the
        // pinned state's relayer authorization so the venue's own batch path can be driven.
        vm.store(BATCH, keccak256(abi.encode(RELAYER, uint256(4))), bytes32(uint256(1)));
SETUP
    }

    // ---------------- value-conservation invariant ----------------

    function components() internal view returns (uint256 t, uint256 bal, uint256 lock, uint256 q,
                                                 uint256 stf, uint256 dev, int256 lp, int256 side) {
        uint256 p22 = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        uint256 p26 = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        t = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        bal = uint128(p22);
        lock = p22 >> 128;
        q = uint256(vm.load(EXCHANGE, bytes32(uint256(18))));
        stf = uint128(p26);
        dev = p26 >> 128;
        lp = int256(uint256(vm.load(TOKENOMICS, bytes32(uint256(3)))));
        side = int256(uint256(vm.load(EXCHANGE, bytes32(uint256(27)))));
    }

    // The value-conservation invariant. The side bucket is NOT a claim: at block 48,173,889 the
    // real chain reads treasury - reserved = 400296219202209635129 = trackedLp + totalQueued
    // (377424392655154164362 + 22871826547055470767) while slot 27 holds 400296219202209635129,
    // so adding it would double count the bankroll. `side` is reported separately as an earmark
    // of the spendable LP bankroll.
    function residual() internal view returns (int256) {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        side;
        return int256(t) - (int256(bal) + int256(lock) + int256(q) + int256(stf) + int256(dev) + lp);
    }

    function u2s(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 t = v; uint256 d;
        while (t != 0) { d++; t /= 10; }
        bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }
    function i2s(int256 v) internal pure returns (string memory) {
        return v < 0 ? string.concat("-", u2s(uint256(-v))) : u2s(uint256(v));
    }
    function hx(uint8 v) internal pure returns (bytes1) { return v < 10 ? bytes1(uint8(48 + v)) : bytes1(uint8(87 + v)); }
    function hexs(bytes memory d) internal pure returns (string memory) {
        bytes memory o = new bytes(d.length * 2);
        for (uint256 i; i < d.length; i++) { o[i*2] = hx(uint8(d[i]) >> 4); o[i*2+1] = hx(uint8(d[i]) & 0xf); }
        return string(o);
    }
    function errOf(bytes memory res) internal pure returns (string memory) {
        if (res.length < 4) return "none";
        uint256 v;
        for (uint256 i; i < 4; i++) v = (v << 8) | uint8(res[i]);
        bytes memory b = new bytes(8);
        for (uint256 i; i < 8; i++) b[i] = hx(uint8((v >> (4 * (7 - i))) & 0xf));
        string memory sel = string.concat("0x", string(b));
        // Error(string) and Panic(uint256) carry a payload; keep it for the ledger
        if (res.length >= 68 && v == 0x08c379a0) return string.concat(sel, ":", hexs(res));
        return sel;
    }

    function note2(string memory a, uint256 b) internal pure returns (string memory) {
        return string.concat(a, "=", u2s(b));
    }
    function step(string memory seq, string memory name, bool ok, bytes memory res, string memory note) internal {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        string memory line = string.concat(seq, ",", name, ",", ok ? "1" : "0", ",", errOf(res));
        line = string.concat(line, ",", u2s(t), ",", u2s(bal), ",", u2s(lock), ",", u2s(q));
        line = string.concat(line, ",", u2s(stf), ",", u2s(dev), ",", i2s(lp), ",", i2s(side));
        line = string.concat(line, ",", i2s(residual()), ",", note);
        vm.writeLine("out/steps.csv", line);
    }

    // ---------------- fixtures and readers ----------------

    function userBalance() internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
    }
    function nextPositionId() internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_NEXT_POSITION))));
    }
    function paperSupply() internal view returns (uint256) {
        return uint256(vm.load(PAPER, bytes32(uint256(SLOT_PAPER_SUPPLY))));
    }
    function posSlot(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(10))); }
    function posWord0(uint256 id) internal view returns (uint256) { return uint256(vm.load(EXCHANGE, posSlot(id))); }
    function posWord1(uint256 id) internal view returns (uint256) { return uint256(vm.load(EXCHANGE, bytes32(uint256(posSlot(id)) + 1))); }
    function posMargin(uint256 id) internal view returns (uint256) { return uint128(posWord1(id)); }
    function posLeverage(uint256 id) internal view returns (uint256) { return (posWord1(id) >> 128) & 0xffffffff; }
    function posEntry(uint256 id) internal view returns (uint256) { return posWord0(id) >> 192; }
    function posInstrument(uint256 id) internal view returns (uint256) { return (posWord0(id) >> 160) & 0xffffffff; }
    function posActive(uint256 id) internal view returns (bool) { return (posWord1(id) >> 224) & 1 == 1; }

    // A credited deposit: exactly the Exchange-side book effect of a sweep or a direct
    // credit (exchange_storage_behavior.md: treasury +, totalBalances + by the same amount).
    function creditUser(uint256 amount) internal {
        bytes32 bs = keccak256(abi.encode(USER, uint256(9)));
        vm.store(EXCHANGE, bs, bytes32(uint256(vm.load(EXCHANGE, bs)) + amount));
        uint256 packed = uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_BALANCES))));
        vm.store(EXCHANGE, bytes32(uint256(SLOT_TOTAL_BALANCES)), bytes32((packed & ~uint256(type(uint128).max)) | uint128((packed & type(uint128).max) + amount)));
        vm.store(EXCHANGE, bytes32(uint256(SLOT_TREASURY)), bytes32(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TREASURY)))) + amount));
    }
    // Force lpBankrollAvailable to a chosen value. The LP's tracked equity and the treasury
    // move together, so the identity survives the fixture: treasury = target + reserved and
    // trackedLp = target - queued - side (the LP has deployed the rest of its capital).
    function forceAvail(uint256 target) internal {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        t; lp;
        vm.store(EXCHANGE, bytes32(uint256(SLOT_TREASURY)), bytes32(target + bal + lock + stf + dev));
        side;
        unchecked {
            vm.store(TOKENOMICS, bytes32(uint256(3)), bytes32(uint256(int256(target) - int256(q))));
        }
    }
    function forceQueued(uint256 amount) internal { vm.store(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED)), bytes32(amount)); }
    // The negative control for the invariant checker: locked margin with no matching debit.
    function writeUnfundedPosition(uint256 id, uint256 margin, uint256 leverage, uint256 entry) internal {
        uint256 w0 = (entry << 192) | (INST << 160) | uint256(uint160(USER));
        uint256 w1 = margin | (leverage << 128) | (uint256(block.timestamp & type(uint64).max) << 160) |
                     (uint256(1) << 240) | (uint256(1) << 224);
        vm.store(EXCHANGE, posSlot(id), bytes32(w0));
        vm.store(EXCHANGE, bytes32(uint256(posSlot(id)) + 1), bytes32(w1));
        uint256 packed = uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_BALANCES))));
        vm.store(EXCHANGE, bytes32(uint256(SLOT_TOTAL_BALANCES)), bytes32((((packed >> 128) + margin) << 128) | uint128(packed)));
    }
    // A labelled fixture step, so every fixture write is its own row and the rows around it are
    // pure venue action.
    function fixtureAvail(uint256 target, string memory seq, string memory name) internal {
        forceAvail(target);
        step(seq, name, true, "", string.concat("fixture_lpBankrollAvailable=", u2s(target)));
    }
    function hexw(bytes32 w) internal pure returns (string memory) {
        return string.concat("0x", hexs(abi.encodePacked(w)));
    }
    // The saved prestate is a transaction read-set: the queue pointers (slot 16 head, slot 17 next id)
    // are absent and read as zero, while the live chain reads head 4 at the pin. This fixture writes the
    // pinned pair so a sequence can run against pointer values the chain itself produced.
    function fixtureQueuePointers(uint256 head, uint256 nextId, string memory seq, string memory name) internal {
        vm.store(EXCHANGE, bytes32(uint256(16)), bytes32(head));
        vm.store(EXCHANGE, bytes32(uint256(17)), bytes32(nextId));
        step(seq, name, true, "", string.concat("fixture_queue_head=", u2s(head), ",next=", u2s(nextId)));
    }
    function queueState() internal view returns (string memory) {
        return string.concat("queued=", u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED))))),
               ",userQueued=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(19)))))),
               ",head=", u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(16))))),
               ",next=", u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(17))))),
               ",userHead=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(20)))))),
               ",userTail=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(21)))))),
               ",bal=", u2s(userBalance()));
    }
    function bankroll() internal view returns (uint256) {
        (bool ok, bytes memory res) = EXCHANGE.staticcall(abi.encodeWithSelector(SEL_BANKROLL));
        require(ok && res.length == 32, "bankroll");
        return abi.decode(res, (uint256));
    }
    function mockBbo(uint256 asset, uint64 bid, uint64 ask) internal {
        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(asset)), abi.encode(uint256(bid), uint256(ask)));
    }
    // The withdrawal path reads the HyperCore spot balance at precompile 0x0801 and reverts
    // NoCoreBalance() when the read is empty; this mirrors the pinned read shape (three words).
    function mockSpot(uint256 a, uint256 b, uint256 c) internal {
        bytes memory code = abi.encodePacked(hex"7f", bytes32(a), hex"6000527f", bytes32(b), hex"6020527f", bytes32(c), hex"60405260", hex"60", hex"6000f3");
        vm.etch(address(uint160(0x0801)), code);
    }
    function mockStatus(uint256 value) internal {
        bytes memory code = abi.encodePacked(hex"7f", bytes32(value), hex"60005260206000f3");
        vm.etch(STATUS, code);
    }

    // ---------------- real venue actions ----------------

    function registerSession(uint256 pk) internal {
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(vm.addr(pk), outer)), bytes32(uint256(block.timestamp + 3600)));
    }
    function openSigned(uint256 instrument, bool isLong, uint256 size, uint32 leverage,
                        uint64 nonce, bool useDebt) internal returns (bool, bytes memory) {
        registerSession(PK);
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(instrument), isLong,
            uint128(size), leverage, useDebt, nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, digest);
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(SEL_OPEN, USER, uint32(instrument),
            isLong, uint128(size), leverage, useDebt, nonce, deadline, v, r, s));
    }
    // Open through the venue and report the position id the venue itself assigned.
    function openPosition(bool isLong, uint256 size, uint32 leverage, uint64 nonce, bool useDebt,
                          string memory seq, string memory name) internal returns (uint256 id) {
        (bool ok, bytes memory res) = openSigned(INST, isLong, size, leverage, nonce, useDebt);
        id = type(uint256).max;
        if (ok && nextPositionId() > 0) id = nextPositionId() - 1;
        uint256 sideAgg = uint256(vm.load(EXCHANGE, MARKET_ROOTV)) & ((uint256(1) << 96) - 1);
        string memory note = string.concat("size=", u2s(size), ",lev=", u2s(leverage), ",longside=", u2s(sideAgg),
            ",id=", id == type(uint256).max ? "none" : u2s(id),
            ",locked=", id == type(uint256).max ? "0" : u2s(posMargin(id)),
            ",entry=", id == type(uint256).max ? "0" : u2s(posEntry(id)),
            ",bal=", u2s(userBalance()));
        step(seq, name, ok, res, note);
    }
    function closeSigned(uint256[] memory ids, uint64 nonce) internal returns (bool, bytes memory) {
        registerSession(PK);
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, digest);
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(SEL_CLOSE, USER, ids, nonce, deadline, v, r, s));
    }
    function closeAndLog(uint256[] memory ids, uint64 nonce, string memory seq, string memory name) internal {
        uint256 supplyBefore = paperSupply();
        uint256 balBefore = userBalance();
        vm.recordLogs();
        (bool ok, bytes memory res) = closeSigned(ids, nonce);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        int256 adjusted;
        uint256 exitPrice;
        uint256 queued;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length == 0) continue;
            if (logs[i].topics[0] == CLOSED_TOPIC) {
                (uint256 e, , int256 a, , ) = abi.decode(logs[i].data, (uint256, int256, int256, uint256, uint256));
                exitPrice = e; adjusted = a;
            } else if (logs[i].topics[0] == ENQUEUED_TOPIC && logs[i].data.length == 32) {
                // Enqueued(address indexed user, uint256 indexed nodeId, uint256 amount)
                queued = abi.decode(logs[i].data, (uint256));
            }
        }
        string memory note = string.concat("exit=", u2s(exitPrice), ",adj=", i2s(adjusted),
            ",queued=", u2s(queued), ",baldelta=", i2s(int256(userBalance()) - int256(balBefore)),
            ",mint=", i2s(int256(paperSupply()) - int256(supplyBefore)), ",logs=", u2s(logs.length));
        step(seq, name, ok, res, note);
    }
    function liquidateAndLog(uint256[] memory ids, string memory seq, string memory name) internal {
        vm.recordLogs();
        vm.prank(KEEPER);
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(SEL_LIQ, ids));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        int256 adjusted;
        uint256 exitPrice;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length > 0 && logs[i].topics[0] == LIQUIDATED_TOPIC && logs[i].data.length >= 96) {
                (uint256 e, , int256 a) = abi.decode(logs[i].data, (uint256, int256, int256));
                exitPrice = e; adjusted = a;
            }
        }
        string memory note = string.concat("exit=", u2s(exitPrice), ",adj=", i2s(adjusted),
            ",bal=", u2s(userBalance()), ",logs=", u2s(logs.length));
        step(seq, name, ok, res, note);
    }
    // pushStakerFees() 0x7b9f5264 is permissionless: it moves the staker fee accumulator and the
    // LP surplus above the configured cap to Staking's ordinary balance.
    // Negative control for the selector question: an unknown selector must give the runtime's own
    // unsupported-selector error.
    function unknownSelectorAndLog(string memory seq, string memory name) internal {
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xdeadbeef)));
        step(seq, name, ok, res, "probe_unknown_selector");
    }
    function pushStakerFeesAndLog(string memory seq, string memory name) internal {
        pushStakerFeesAs(seq, name, STRANGER);
    }
    function pushStakerFeesAs(string memory seq, string memory name, address caller) internal {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        t; lock; dev; side;
        vm.prank(caller);
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(SEL_PUSH));
        (uint256 t2, uint256 bal2, uint256 lock2, uint256 q2, uint256 stf2, uint256 dev2, int256 lp2, int256 side2) = components();
        t2; lock2; q2; dev2; side2;
        string memory note = string.concat("caller=", caller == STRANGER ? "stranger" : (caller == KEEPER ? "keeper" : "owner"),
            ",staker_fee_delta=", i2s(int256(stf2) - int256(stf)),
            ",balances_delta=", i2s(int256(bal2) - int256(bal)), ",lp_delta=", i2s(lp2 - lp),
            ",staking_bal=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(STAKING, uint256(9)))))));
        step(seq, name, ok, res, note);
    }
    function harvestAndLog(uint256 n, string memory seq, string memory name) internal {
        vm.prank(USER);
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(SEL_HARVEST, n));
        uint256 paid = (ok && res.length == 32) ? abi.decode(res, (uint256)) : 0;
        step(seq, name, ok, res, string.concat("paid=", u2s(paid), ",bal=", u2s(userBalance())));
    }
    // The signed withdrawal is verified against the user, not a session key.
    function withdrawSigned(uint256 amount, uint64 nonce) internal returns (bool, bytes memory) {
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(WITHDRAW_TYPEHASH, USER, amount, nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(USER_KEY, digest);
        return EXCHANGE.call(abi.encodeWithSelector(SEL_WITHDRAW, USER, amount, nonce, deadline, v, r, s));
    }
    function withdrawAndLog(uint256 amount, uint64 nonce, string memory seq, string memory name) internal {
        uint256 before = userBalance();
        (bool ok, bytes memory res) = withdrawSigned(amount, nonce);
        step(seq, name, ok, res, string.concat("signed=", u2s(amount), ",debit=",
            i2s(int256(before) - int256(userBalance())), ",bal=", u2s(userBalance())));
    }
    // The real BatchExecutor path: the allowlist lives in the saved prestate (slots 0 to 2).
    function runBatch(bytes[] memory payloads) internal returns (bool ok, bytes memory res) {
        Call[] memory calls = new Call[](payloads.length);
        for (uint256 i; i < payloads.length; ++i) {
            calls[i] = Call(EXCHANGE, payloads[i], true, bytes32(0), bytes32(0));
        }
        vm.prank(RELAYER);
        (ok, res) = BATCH.call(abi.encodeWithSelector(SEL_BATCH, calls));
    }
    function closePayload(uint256[] memory ids, uint64 nonce) internal returns (bytes memory) {
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, digest);
        return abi.encodeWithSelector(SEL_CLOSE, USER, ids, nonce, deadline, v, r, s);
    }
    // A debt-funded open, recording every storage word the call writes.
    function openDebt(uint256 size, uint32 leverage, uint64 nonce, string memory seq, string memory name) internal returns (uint256 id) {
        vm.record();
        id = openPosition(true, size, leverage, nonce, true, seq, name);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        reads;
        string memory note = string.concat("recorded_writes=", u2s(writes.length));
        for (uint256 i; i < writes.length && i < 10; i++) {
            note = string.concat(note, ",w", u2s(i), "=", hexw(writes[i]));
        }
        step(seq, string.concat(name, "_writes"), true, "", note);
    }
    // A debt-funded close, recording every storage word the call writes.
    function closeDebt(uint256 id, uint64 nonce, string memory seq, string memory name) internal {
        registerSession(PK);
        vm.record();
        closeAndLog(one(id), nonce, seq, name);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        reads;
        string memory note = string.concat("recorded_writes=", u2s(writes.length));
        for (uint256 i; i < writes.length && i < 8; i++) {
            note = string.concat(note, ",w", u2s(i), "=", hexw(writes[i]));
        }
        step(seq, string.concat(name, "_writes"), true, "", note);
    }
    function one(uint256 id) internal pure returns (uint256[] memory ids) { ids = new uint256[](1); ids[0] = id; }
CASES
}
'''


def render_source(variant):
    source = SOLIDITY
    source = (source
              .replace("CASES", TESTS)
              .replace("ADDR_EXCHANGE", s_address(EXCHANGE))
              .replace("ADDR_SESSION", s_address(SESSION))
              .replace("ADDR_BATCH", s_address(BATCH))
              .replace("ADDR_TOKENOMICS", s_address(TOKENOMICS))
              .replace("ADDR_PAPER", s_address(PAPER))
              .replace("ADDR_USER", s_address(USER))
              .replace("ADDR_KEEPER", s_address(KEEPER))
              .replace("ADDR_RELAYER", s_address(RELAYER))
              .replace("ADDR_STAKING", s_address(STAKING))
              .replace("ADDR_STRANGER", s_address(STRANGER))
              .replace("ADDR_OWNER", s_address(OWNER))
              .replace("SEL_PUSH", f"bytes4({PUSH_STAKER_FEES})")
              .replace("SEL_BANKROLL", f"bytes4({LP_BANKROLL})")
              .replace("TH_CLOSE", CLOSE_TYPEHASH)
              .replace("TH_OPEN", OPEN_TYPEHASH)
              .replace("TH_WITHDRAW", typehash(WITHDRAW_TYPE_STRING))
              .replace("DOMAIN_V", CLOSE_DOMAIN)
              .replace("TOPIC_CLOSED", TOPIC_CLOSED)
              .replace("TOPIC_LIQ", TOPIC_LIQUIDATED)
              .replace("TOPIC_ENQ", TOPIC_ENQUEUED)
              .replace("TOPIC_SB", TOPIC_SIDEBUCKET)
              .replace("TOPIC_CE", TOPIC_CALL_EXECUTED)
              .replace("SEL_CLOSE", f"bytes4({CLOSE_SELECTOR})")
              .replace("SEL_OPEN", f"bytes4({OPEN_SELECTOR})")
              .replace("SEL_WITHDRAW", f"bytes4({WITHDRAW_SELECTOR})")
              .replace("SEL_LIQ", f"bytes4({LIQUIDATE_BATCH})")
              .replace("SEL_HARVEST", f"bytes4({HARVEST_SELECTOR})")
              .replace("SEL_BATCH", f"bytes4({EXECUTE_BATCH})")
              .replace("ENTRY_PRICE_V", str(ENTRY_PRICE))
              .replace("SLOT_TOTAL_QUEUED", str(SLOT_TOTAL_QUEUED))
              .replace("SLOT_TREASURY", str(SLOT_TREASURY))
              .replace("SLOT_TOTAL_BALANCES", str(SLOT_TOTAL_BALANCES))
              .replace("SLOT_SIDE_BUCKET", str(SLOT_SIDE_BUCKET))
              .replace("SLOT_NEXT_POSITION", str(SLOT_NEXT_POSITION))
              .replace("SLOT_PAPER_SUPPLY", str(SLOT_PAPER_SUPPLY))
              .replace("MARKET_ROOTV", MARKET_ROOT_ETH)
              .replace("ROLLV", str(PRESTATE_BLOCK))
              .replace("WARPV", str(PRESTATE_TIMESTAMP))
              .replace("SETUP", "\n".join(load_prestate_lines() + fixture_lines(variant))))
    return source


# ------------------------------------------------------------------ sequences

TESTS = r'''
// s0: the invariant holds on the loaded prestate, and the checker detects a break.
    function test_s0_control_and_negative() public {
        step("s0", "load", true, "", "residual_expected=0");
        writeUnfundedPosition(900001, 20000 * WAD, 500, ENTRY_PRICE_V);
        step("s0", "unfunded_position_negative_control", true, "", "margin_expected_in_residual=20000000000000000000000");
    }

    // s1: open then close at the same quote, five times, from the venue's own opens.
    function test_s1_open_close_same_price_cycles() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        step("s1", "deposit_credit", true, "", note2("credit", 1000000 * WAD));
        for (uint256 cycle; cycle < 5; cycle++) {
            uint256 id = openPosition(true, 5000 * WAD, 100, uint64(1000 + cycle), false,
                                      "s1", cycle == 0 ? "open_0" : "open_n");
            if (id == type(uint256).max) continue;
            closeAndLog(one(id), uint64(2000 + cycle), "s1", cycle == 0 ? "close_same_price_0" : "close_same_price_n");
        }
        step("s1", "final_claim", true, "", string.concat("balance=", u2s(userBalance()), ",locked=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_BALANCES))) >> 128))));
    }

    // s2: a solvent win then a loss, from the venue's own opens (fee, LP debit and mint accounting).
    function test_s2_win_then_loss() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        forceAvail(BIG);
        creditUser(1000000 * WAD);
        uint256 win = openPosition(true, 5000 * WAD, 100, 1100, false, "s2", "open_win");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(win), 1101, "s2", "close_win_solvent");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        uint256 loss = openPosition(true, 5000 * WAD, 100, 1102, false, "s2", "open_loss");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 1005), uint64(ENTRY_PRICE_V - 995));
        closeAndLog(one(loss), 1103, "s2", "close_loss");
        step("s2", "after", true, "", note2("paper_supply", paperSupply()));
    }

    // s3: open then liquidate at the maintenance boundary, LP bankroll funded.
    function test_s3_open_then_liquidate() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        forceAvail(BIG);
        creditUser(1000000 * WAD);
        uint256 id = openPosition(true, 5000 * WAD, 100, 1200, false, "s3", "open");
        mockBbo(INST, uint64(248000), uint64(248010));
        liquidateAndLog(one(id), "s3", "liquidate");
        harvestAndLog(10, "s3", "harvest_empty_queue");
    }

    // s4: a legitimate queued win puts a claim in the queue, then a liquidation runs while the
    // queue is live: the M-02 branch, with the side bucket watched.
    function test_s4_queue_live_liquidation() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 q = openPosition(true, 5000 * WAD, 100, 1300, false, "s4", "open_queued_win");
        uint256 l = openPosition(true, 5000 * WAD, 100, 1301, false, "s4", "open_to_liquidate");
        forceAvail(0);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(q), 1302, "s4", "close_win_queued");
        step("s4", "queue_live", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED))))), ",avail=", u2s(bankroll())));
        mockBbo(INST, uint64(248000), uint64(248010));
        liquidateAndLog(one(l), "s4", "liquidate_while_queue_live");
        forceAvail(BIG);
        harvestAndLog(10, "s4", "harvest");
        harvestAndLog(10, "s4", "harvest_again");
    }

    // s5: a deferred win, then a funded harvest, then a second harvest.
    function test_s5_queued_win_then_harvest() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 id = openPosition(true, 5000 * WAD, 100, 1400, false, "s5", "open");
        forceAvail(0);
        step("s5", "avail_zero", true, "", "lpBankrollAvailable=0");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(id), 1401, "s5", "close_win_queued");
        forceAvail(BIG);
        step("s5", "avail_restored", true, "", "lpBankrollAvailable=big");
        harvestAndLog(10, "s5", "harvest_1");
        harvestAndLog(10, "s5", "harvest_2");
    }

    // s6: a legitimate loss while the queue is live, then a winner into the live queue.
    function test_s6_loss_into_live_queue_then_win() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 fill = openPosition(true, 5000 * WAD, 100, 1500, false, "s6", "open_fill_win");
        uint256 a = openPosition(true, 5000 * WAD, 100, 1501, false, "s6", "open_a");
        uint256 b = openPosition(true, 5000 * WAD, 100, 1502, false, "s6", "open_b");
        forceAvail(0);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(fill), 1503, "s6", "close_fill_win_queued");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 1005), uint64(ENTRY_PRICE_V - 995));
        closeAndLog(one(a), 1504, "s6", "close_a_loss_while_queued");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(b), 1505, "s6", "close_b_win_into_live_queue");
        forceAvail(BIG);
        harvestAndLog(10, "s6", "harvest");
        harvestAndLog(10, "s6", "harvest_again");
    }

    // s7: both sides of one market in one block, closed in two orders.
    function test_s7_both_sides_one_market() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 lng = openPosition(true, 5000 * WAD, 100, 1600, false, "s7", "open_long");
        uint256 sht = openPosition(false, 5000 * WAD, 100, 1601, false, "s7", "open_short");
        uint256[] memory both = new uint256[](2);
        both[0] = lng; both[1] = sht;
        closeAndLog(both, 1602, "s7", "close_both_one_batch");
        uint256 lng2 = openPosition(true, 5000 * WAD, 100, 1603, false, "s7", "open_long_2");
        uint256 sht2 = openPosition(false, 5000 * WAD, 100, 1604, false, "s7", "open_short_2");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 495), uint64(ENTRY_PRICE_V + 505));
        closeAndLog(one(lng2), 1605, "s7", "close_winner_first");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 505), uint64(ENTRY_PRICE_V - 495));
        closeAndLog(one(sht2), 1606, "s7", "close_loser_second");
    }

    // s8: dust margin, the deadband boundary, the leverage bound and the per-side cap.
    function test_s8_boundaries() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 dust = openPosition(true, 1, 1, 1700, false, "s8", "open_one_wei");
        closeAndLog(one(dust), 1701, "s8", "close_one_wei_same_quote");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 5), uint64(ENTRY_PRICE_V + 6));
        uint256 dead = openPosition(true, 5000 * WAD, 100, 1702, false, "s8", "open_deadband");
        closeAndLog(one(dead), 1703, "s8", "close_deadband_move");
        uint256 top = openPosition(true, 1000 * WAD, 1000, 1704, false, "s8", "open_leverage_bound");
        closeAndLog(one(top), 1705, "s8", "close_leverage_bound");
        openPosition(true, 1000 * WAD, 1001, 1706, false, "s8", "open_over_leverage");
        openPosition(true, 20000 * WAD, 100, 1707, false, "s8", "open_margin_20000");
        openPosition(true, 6000 * WAD, 100, 1708, false, "s8", "open_margin_6000");
        openPosition(false, 20000 * WAD, 100, 1709, false, "s8", "open_short_20000");
    }

    // s9: close then withdraw, with both HyperCore account-status replies.
    function test_s9_close_then_withdraw() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        mockSpot(10_000_000_000, 0, 0);
        step("s9", "spot_mock", true, "", "mock 0x0801 returns 10000000000,0,0");
        uint256 id = openPosition(true, 5000 * WAD, 100, 1800, false, "s9", "open");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(id), 1801, "s9", "close_win");
        mockStatus(1);
        step("s9", "status_true", true, "", "mock 0x0810 returns 1");
        withdrawAndLog(2_000_000, 1802, "s9", "withdraw_status_true");
        vm.roll(block.number + 1);
        mockStatus(0);
        step("s9", "status_false", true, "", "mock 0x0810 returns 0, one withdrawal per user per block");
        withdrawAndLog(2_000_000, 1803, "s9", "withdraw_status_false");
    }

    // s10: two closes in one BatchExecutor transaction, through the real allowlist.
    function test_s10_batch_executor_two_closes() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 a = openPosition(true, 5000 * WAD, 100, 1900, false, "s10", "open_a");
        uint256 b = openPosition(false, 5000 * WAD, 100, 1901, false, "s10", "open_b");
        registerSession(PK);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 495), uint64(ENTRY_PRICE_V + 505));
        bytes[] memory payloads = new bytes[](2);
        payloads[0] = closePayload(one(a), 1902);
        payloads[1] = closePayload(one(b), 1903);
        vm.recordLogs();
        (bool ok, bytes memory res) = runBatch(payloads);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        uint256 executed;
        uint256 closed;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length == 0) continue;
            if (logs[i].topics[0] == CALL_EXECUTED_TOPIC && logs[i].emitter == BATCH) executed++;
            if (logs[i].topics[0] == CLOSED_TOPIC) closed++;
        }
        step("s10", "batch_two_closes", ok, res, string.concat("executed=", u2s(executed),
            ",closed_events=", u2s(closed), ",bal=", u2s(userBalance()), ",logs=", u2s(logs.length)));
    }

// s11: a debt-funded open against a coherent queue. The saved transaction read-set omits
// queue pointers, so seed the pinned head and next id before producing the deferred win.
    function test_s11_debt_cycle_coherent_queue() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        fixtureQueuePointers(4, 4, "s11", "fixture_queue_head4_next4");
        uint256 a = openPosition(true, 5000 * WAD, 100, 2400, false, "s11", "open_a");
        fixtureAvail(0, "s11", "fixture_avail_zero");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(a), 2401, "s11", "close_a_win_queued");
        step("s11", "queue_state", true, "", queueState());
        uint256 debt = openDebt(1000 * WAD, 100, 2402, "s11", "open_debt_1000");
        step("s11", "after_open", true, "", queueState());
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeDebt(debt, 2403, "s11", "close_debt_same_quote");
        step("s11", "after_close", true, "", queueState());
        fixtureAvail(BIG, "s11", "fixture_avail_big");
        harvestAndLog(10, "s11", "harvest_once");
        step("s11", "after_harvest", true, "", queueState());
        openDebt(1000 * WAD, 100, 2404, "s11", "second_debt_open");
        step("s11", "end_state", true, "", queueState());
    }

    // s12: the LP surplus path with the LP cursor below its cap and negative.
    function test_s12_push_staker_fees_below_cap() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        forceAvail(0);
        step("s12", "lp_at_zero", true, "", "trackedLP=0");
        uint256 id = openPosition(true, 5000 * WAD, 100, 2100, false, "s12", "open");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(id), 2101, "s12", "close_win_queued");
        step("s12", "lp_negative", true, "", string.concat("trackedLP=",
            i2s(int256(uint256(vm.load(TOKENOMICS, bytes32(uint256(3))))))));
        pushStakerFeesAndLog("s12", "push_stranger_lp_negative");
        pushStakerFeesAndLog("s12", "push_stranger_lp_negative_again");
    }

    // s13: the LP surplus path above the cap, twice, and with a live queue.
    function test_s13_push_staker_fees_above_cap() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        forceAvail(5000000 * WAD + 1000 * WAD);
        step("s13", "lp_above_cap", true, "", "trackedLP=5001000e18");
        unknownSelectorAndLog("s13", "unknown_selector_control");
        pushStakerFeesAndLog("s13", "push_stranger_above_cap_1");
        pushStakerFeesAndLog("s13", "push_stranger_above_cap_2");
        pushStakerFeesAs("s13", "push_keeper_above_cap", KEEPER);
        pushStakerFeesAs("s13", "push_owner_above_cap", OWNER);
        uint256 a = openPosition(true, 5000 * WAD, 100, 2200, false, "s13", "open_a");
        uint256 b = openPosition(true, 5000 * WAD, 100, 2201, false, "s13", "open_b");
        forceAvail(5000000 * WAD + 1000 * WAD);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(a), 2202, "s13", "close_win_queued");
        step("s13", "queue_live_with_excess", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED))))), ",trackedLP=",
            i2s(int256(uint256(vm.load(TOKENOMICS, bytes32(uint256(3))))))));
        pushStakerFeesAndLog("s13", "push_with_live_queue");
        pushStakerFeesAndLog("s13", "push_with_live_queue_again");
        forceAvail(BIG);
        harvestAndLog(10, "s13", "harvest");
        if (b != type(uint256).max) closeAndLog(one(b), 2203, "s13", "close_b");
    }

'''


def build_project(variant, tmp):
    source = render_source(variant)
    project = pathlib.Path(tmp)
    for name in ("test", "runtime", "out"):
        (project / name).mkdir(exist_ok=True)
    (project / "out" / "steps.csv").write_text("")
    (project / "foundry.toml").write_text(
        '[profile.default]\noffline = true\nvia_ir = true\noptimizer = true\noptimizer_runs = 200\n'
        'fs_permissions = [{ access = "read", path = "./runtime" }, '
        '{ access = "read-write", path = "./out" }]\n')
    (project / "test" / "Sequence.t.sol").write_text(source)
    codes = {a: row.get("code", "0x") for a, row in prestate().items()}
    for address, raw in variants()[variant]["files"].items():
        codes[address] = raw
    for a, code in codes.items():
        if code != "0x":
            (project / "runtime" / f"{a[2:]}.hex").write_text(code)
    return source


def source_for(variant):
    with tempfile.TemporaryDirectory(prefix=f"papertrade-live2-src-{variant}-") as tmp:
        return build_project(variant, tmp)


def run_forge(variant):
    assert shutil.which("forge") and shutil.which("solc"), "forge and solc are required"
    with tempfile.TemporaryDirectory(prefix=f"papertrade-live2-seq-{variant}-") as tmp:
        source = build_project(variant, tmp)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=1800)
        output = (run.stdout + "\n" + run.stderr).rstrip() + "\n"
        csv = (pathlib.Path(tmp) / "out" / "steps.csv").read_text()
    return source, output, csv


def parse_steps(text):
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) < 13:
            continue
        rows.append({
            "seq": parts[0], "step": parts[1], "ok": parts[2] == "1", "err": parts[3],
            "treasury": int(parts[4]), "balances": int(parts[5]), "locked": int(parts[6]),
            "queued": int(parts[7]), "staker_fee": int(parts[8]), "dev_fee": int(parts[9]),
            "tracked_lp": int(parts[10]), "side_bucket": int(parts[11]),
            "residual": int(parts[12]), "note": ",".join(parts[13:]),
        })
    return rows


# ------------------------------------------------------------------ analysis


# ------------------------------------------------------------------ analysis

LEDGER = ATLAS / "live2_sequences.json"
DOC = ATLAS / "live2_sequences.md"
HISTORICAL_STATES = ROOT / "artifacts" / "historical" / "accounting_states.json"


def note_map(note):
    out = {}
    for part in note.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key] = value
    return out


def by_seq(rows, seq):
    return [r for r in rows if r["seq"] == seq]


def step_row(rows, seq, name):
    for r in rows:
        if r["seq"] == seq and r["step"] == name:
            return r
    raise KeyError(f"{seq}/{name}")


def deltas(rows, seq, first, second):
    a, b = step_row(rows, seq, first), step_row(rows, seq, second)
    return {k: b[k] - a[k] for k in ("treasury", "balances", "locked", "queued",
                                     "staker_fee", "dev_fee", "tracked_lp", "side_bucket", "residual")}


def historical_identity():
    """The invariant on a real chain state where the side bucket is nonzero.

    Block 48,173,889 is the close that wrote 400296219202209635129 into Exchange slot 27, and
    48,173,890 is the harvest that cleared it while paying the queue. The archive state captures
    tracked LP, the queue total and the two availability getters, so the claim sum can be checked
    with and without the side bucket.
    """
    states = {row["block"]: row for row in json.loads(HISTORICAL_STATES.read_text())["states"]}
    queued = states[48173889]
    after = states[48173890]
    side_write = 400296219202209635129
    rows = [
        {"block": 48173889, "queue_harvest_available": int(queued["queue_harvest_available"]),
         "tracked_lp": int(queued["tracked_lp"]), "total_queued": int(queued["total_queued"]),
         "side_bucket_after_the_close": side_write,
         "tracked_lp_plus_queued": int(queued["tracked_lp"]) + int(queued["total_queued"]),
         "tracked_lp_plus_queued_plus_side": int(queued["tracked_lp"]) + int(queued["total_queued"]) + side_write},
        {"block": 48173890, "queue_harvest_available": int(after["queue_harvest_available"]),
         "tracked_lp": int(after["tracked_lp"]), "total_queued": int(after["total_queued"]),
         "side_bucket_after_the_harvest": 0,
         "tracked_lp_plus_queued": int(after["tracked_lp"]) + int(after["total_queued"]),
         "tracked_lp_plus_queued_plus_side": int(after["tracked_lp"]) + int(after["total_queued"])},
    ]
    # treasury - reserved (the queue harvest availability) equals trackedLp + totalQueued, not
    # trackedLp + totalQueued + side: the side bucket is an earmark, not a claim.
    assert rows[0]["queue_harvest_available"] == rows[0]["tracked_lp_plus_queued"]
    assert rows[0]["tracked_lp_plus_queued_plus_side"] != rows[0]["queue_harvest_available"]
    assert rows[1]["queue_harvest_available"] == rows[1]["tracked_lp_plus_queued"]
    # the same relation at the pin, where both are zero
    pin_state = states[48902346]
    assert int(pin_state["queue_harvest_available"]) == int(pin_state["tracked_lp"])
    return rows


def analyze(result):
    live = result["variants"]["live"]["steps"]
    pinned = result["variants"]["pinned"]["steps"]
    for tag in ("live", "pinned"):
        variant = result["variants"][tag]
        assert not variant["failed"], (tag, variant["failed"])
        assert len(variant["passed"]) == 14, (tag, variant["passed"])

    live_keys = {(r["seq"], r["step"]) for r in live}
    pinned_keys = {(r["seq"], r["step"]) for r in pinned}
    assert live_keys == pinned_keys
    identical = [k for k in sorted(live_keys)
                 if all(step_row(live, *k)[f] == step_row(pinned, *k)[f]
                        for f in ("treasury", "balances", "locked", "queued", "staker_fee",
                                  "dev_fee", "tracked_lp", "side_bucket", "residual"))]

    rows = []

    # --- conservation and the corrected debt lifecycle ----------------------
    controls = {
        "load_residual": step_row(live, "s0", "load")["residual"],
        "negative_control_residual": step_row(live, "s0", "unfunded_position_negative_control")["residual"],
        "negative_control_expected": -20000 * 10 ** 18,
    }
    assert controls["load_residual"] == 0
    assert controls["negative_control_residual"] == controls["negative_control_expected"], controls
    breaches = [r for r in live if r["residual"] != 0
                and not (r["seq"] == "s0" and r["step"] == "unfunded_position_negative_control")]
    assert {r["seq"] for r in breaches} == {"s11"}, breaches
    assert all(r["residual"] == 1000 * 10 ** 18 for r in breaches), breaches
    assert not any(r["residual"] < 0 for r in live
                   if not (r["seq"] == "s0" and r["step"] == "unfunded_position_negative_control"))
    clean_steps = len(live) - len(breaches) - 1
    queue_before = step_row(live, "s11", "queue_state")
    debt_open = step_row(live, "s11", "open_debt_1000")
    debt_close = step_row(live, "s11", "close_debt_same_quote")
    after_close = step_row(live, "s11", "after_close")
    harvest = step_row(live, "s11", "harvest_once")
    after_harvest = step_row(live, "s11", "after_harvest")
    second_open = step_row(live, "s11", "second_debt_open")
    end_state = step_row(live, "s11", "end_state")
    margin = 1000 * 10 ** 18
    assert debt_open["ok"] and debt_open["queued"] == queue_before["queued"] - margin
    assert debt_open["residual"] == margin
    assert debt_close["ok"] and note_map(debt_close["note"])["adj"] == "0"
    assert after_close["queued"] == queue_before["queued"] and after_close["residual"] == 0
    assert harvest["ok"] and int(note_map(harvest["note"])["paid"]) == queue_before["queued"]
    assert after_harvest["queued"] == 0 and after_harvest["residual"] == 0
    assert after_harvest["balances"] - queue_before["balances"] == queue_before["queued"]
    assert not second_open["ok"] and second_open["err"] == "0x8e667356"
    assert end_state["residual"] == 0 and end_state["queued"] == 0

    rows.append({
        "id": "SQ-L2-01",
        "title": "Tested settled sequences conserve value; a debt open temporarily removes its margin from the listed claims",
        "angle": "A1 value conservation under sequences; A2 size and boundary extremes; A3 self-impact; A4 queue interaction",
        "invariant": "A3",
        "actor": "unprivileged user, keeper",
        "precondition": "exact pinned and set-2 runtimes on a saved transaction read-set, with mocked HyperCore responses and a coherently seeded queue",
        "trigger": "same-quote cycles, wins, losses, liquidations, harvests, boundaries, withdrawals, batches and one debt-funded lifecycle",
        "impact": f"The book identity holds on {clean_steps} of {len(live)} steps. The only non-control deviation is a positive 1000 USDC residual while debt margin is open; the same-quote close restores the queued claim and zero residual. No negative residual or extra payout appears in the coherent lifecycle.",
        "affected": "both", "severity": "info", "status": "confirmed_simulation",
        "evidence_tier": "port-free Forge replay against both exact runtimes with queue pointers seeded from pinned state",
        "evidence": {"live_steps": len(live), "steps_with_residual_zero": clean_steps,
                     "debt_open_residual_raw": debt_open["residual"],
                     "debt_close_residual_raw": debt_close["residual"],
                     "negative_control_residual": controls["negative_control_residual"],
                     "rows_identical_live_vs_pinned": len(identical),
                     "steps_csv": "artifacts/live2_sequences/steps_live.csv",
                     "steps_csv_pinned": "artifacts/live2_sequences/steps_pinned.csv"},
        "missing_observation": "The replay uses a saved transaction read-set and mocked HyperCore replies; it is not a full-state live fork or an exhaustive proof of every queue state.",
        "citations": ["atlas/block_48902346/exchange_queue_layout.md",
                      "atlas/block_48902346/accounting_claims_and_core_assets.md"],
    })
    rows.append({
        "id": "SQ-L2-02",
        "title": "The claimed repeatable debt-cycle mint came from omitted queue pointers in the replay fixture",
        "angle": "A3 false-positive correction",
        "invariant": "A3",
        "actor": "auditor (fixture correction, no attacker)",
        "precondition": "the saved transaction read-set omitted queue head and next-id slots 16 and 17; the corrected run seeds their pinned values",
        "trigger": "compare the previously reported cycle with the coherent queue lifecycle",
        "impact": "The coherent replay consumes 1000 USDC of queued credit on debt open, restores the claim on a zero-PnL close, pays the existing queue once, and rejects a second debt open. The earlier 3237.31 USDC gain and 20000 USDC excess are artifacts of the incomplete fixture and are withdrawn.",
        "affected": "both", "severity": "none", "status": "disproved",
        "evidence_tier": "corrected exact-runtime replay against both pinned and set-2 implementations",
        "evidence": {"queue_before_raw": queue_before["queued"],
                     "after_debt_open_raw": debt_open["queued"],
                     "after_close_raw": after_close["queued"],
                     "harvest_paid_raw": int(note_map(harvest["note"])["paid"]),
                     "second_open_error": second_open["err"],
                     "end_residual_raw": end_state["residual"],
                     "steps_csv": "artifacts/live2_sequences/steps_live.csv"},
        "missing_observation": "No full-state live fork was run; this disproof applies to the specific previously claimed repeatable cycle.",
        "citations": ["atlas/block_48902346/exchange_queue_layout.md",
                      "artifacts/live2_sequences/steps_live.csv"],
    })

    # --- the side bucket is an earmark, not a claim --------------------------
    hist = historical_identity()
    s4_liq = step_row(live, "s4", "liquidate_while_queue_live")
    s6_loss = step_row(live, "s6", "close_a_loss_while_queued")
    memo_identity = {
        "s4_after_liquidation": {"side": s4_liq["side_bucket"], "tracked_lp_plus_queued":
                                 s4_liq["tracked_lp"] + s4_liq["queued"]},
        "s6_after_loss_with_live_queue": {"side": s6_loss["side_bucket"], "tracked_lp_plus_queued":
                                         s6_loss["tracked_lp"] + s6_loss["queued"]},
    }
    assert memo_identity["s4_after_liquidation"]["side"] == memo_identity["s4_after_liquidation"]["tracked_lp_plus_queued"]
    assert (memo_identity["s6_after_loss_with_live_queue"]["side"]
            == memo_identity["s6_after_loss_with_live_queue"]["tracked_lp_plus_queued"])
    rows.append({
        "id": "SQ-L2-03",
        "title": "The Exchange side bucket is an earmark of the spendable LP bankroll, not a claim, so the repo's conservation identity double counts it whenever it is nonzero",
        "angle": "A1 value conservation (model correction)",
        "invariant": "A3",
        "actor": "auditor (identity correction, no attacker)",
        "precondition": "the real chain state at block 48,173,889, saved in artifacts/historical/accounting_states.json, "
                        "plus the live replay of the queue-live branches",
        "trigger": "compare treasury - reserved with trackedLp + totalQueued and with trackedLp + totalQueued + side",
        "impact": "at block 48,173,889 the close wrote "
                  + str(hist[0]["side_bucket_after_the_close"]) + " into Exchange slot 27, and the archive reads "
                  "queue harvest availability = " + str(hist[0]["queue_harvest_available"]) + " = trackedLp "
                  + str(hist[0]["tracked_lp"]) + " + totalQueued " + str(hist[0]["total_queued"]) + ", while "
                  "trackedLp + totalQueued + side would be " + str(hist[0]["tracked_lp_plus_queued_plus_side"]) + ". "
                  "The side bucket is the bankroll the queue harvest is allowed to draw on, so it is already counted "
                  "in trackedLp + totalQueued and must not be added again. In the live replay the same relation holds "
                  "at both side-bucket writes (side == trackedLp + totalQueued after the queue-live liquidation and "
                  "after the loss with a live queue). The repo's atlas_all_suite_claims.py identity adds the side "
                  "bucket; it reconciles only because the pinned side bucket is zero",
        "affected": "both", "severity": "medium", "status": "confirmed_live",
        "evidence_tier": "saved archive getter reads at a real block plus exact-runtime replay",
        "evidence": {"block_48173889": {k: str(v) for k, v in hist[0].items()},
                     "block_48173890": {k: str(v) for k, v in hist[1].items()},
                     "replay_side_bucket_equals_bankroll": {k: {kk: str(vv) for kk, vv in v.items()}
                                                            for k, v in memo_identity.items()}},
        "missing_observation": "no archive capture of every book field at 48,173,889 (only the availability getters, "
                               "tracked LP and the queue total); the correction rests on those getters, which are "
                               "defined as treasury less the reserved claims",
        "citations": ["artifacts/historical/accounting_states.json",
                      "atlas/block_48902346/exchange_queue_layout.md",
                      "atlas/block_48902346/exchange_side_bucket.md"],
    })

    # --- the strongest negatives and the guards that stopped each path -------
    s1_first, s1_last = step_row(live, "s1", "deposit_credit"), step_row(live, "s1", "final_claim")
    s1_closes = [r for r in live if r["seq"] == "s1" and r["step"].startswith("close_same_price")]
    assert all(note_map(r["note"])["adj"] == "0" for r in s1_closes), s1_closes
    assert all(int(note_map(r["note"])["baldelta"]) == 5000 * 10 ** 18 for r in s1_closes)
    balance_after_cycles = int(note_map(s1_last["note"])["balance"])
    s2_win = step_row(live, "s2", "close_win_solvent")
    s2_loss = step_row(live, "s2", "close_loss")
    s3_liq = step_row(live, "s3", "liquidate")
    s3_harvest = step_row(live, "s3", "harvest_empty_queue")
    s5_close, s5_harvest, s5_again = (step_row(live, "s5", s) for s in
                                      ("close_win_queued", "harvest_1", "harvest_2"))
    s7_batch = step_row(live, "s7", "close_both_one_batch")
    s8_dust = step_row(live, "s8", "close_one_wei_same_quote")
    s8_dead = step_row(live, "s8", "close_deadband_move")
    s8_lev = step_row(live, "s8", "open_over_leverage")
    s8_cap = step_row(live, "s8", "open_margin_6000")
    s9_true, s9_false = step_row(live, "s9", "withdraw_status_true"), step_row(live, "s9", "withdraw_status_false")
    s10 = step_row(live, "s10", "batch_two_closes")
    assert int(note_map(s5_harvest["note"])["paid"]) == s5_close["queued"], (s5_harvest, s5_close)
    assert deltas(live, "s5", "avail_restored", "harvest_1")["tracked_lp"] == 0, "a harvest must not debit tracked LP again"
    assert s5_again["err"] == "0x75e52f4f" and s5_again["residual"] == s5_harvest["residual"]
    rows.append({
        "id": "SQ-L2-04",
        "title": "Every other sequence is neutral: five same-quote cycles, a win, a loss, a liquidation, "
                 "harvests, both sides of one market, dust and boundary sizes, close then withdraw, and a "
                 "two-close BatchExecutor batch all reconcile exactly, and each blocked path names its guard",
        "angle": "A1 sequences; A2 extremes; A3 self-impact; A4 queue interaction; A5 double payment",
        "invariant": "A3, A4, A6, A7",
        "actor": "unprivileged user, keeper, relayer",
        "precondition": "the live set-2 runtimes on the saved prestate",
        "trigger": "the twelve sequences of the harness; each guard row below quotes the raw revert selector returned",
        "impact": "the user's claim returns to exactly its starting value after five same-quote open/close cycles "
                  f"({balance_after_cycles} == the 1000000e18 credit); a same-quote close settles adj = 0 with no fee "
                  "and no mint; a deferred win is paid exactly once at harvest with tracked LP already debited at the "
                  "close (the harvest is a pure queue-to-balance reclassification, tracked LP delta zero) and a second "
                  "harvest reverts QueueEmpty() (0x75e52f4f); a liquidation on an empty queue reverts the same; a "
                  "one-wei margin opens and closes with a one-unit balance delta and no rounding leak; the deadband "
                  "boundary settles at exactly zero; both sides of one market closed in one batch at the same quote "
                  "settle at zero; two closes through the real BatchExecutor allowlist both execute with the residual "
                  "at zero; the withdrawal with a true account status debits exactly the signed amount; and the guards "
                  "are: OiCapExceeded() 0x40f92143 when the per-side aggregate would pass the configured limit, "
                  "LeverageTooHigh() 0x0a4f5a07 above leverage 1000, QueueEmpty() 0x75e52f4f on an empty harvest, "
                  "the one-withdrawal-per-user-per-block gate, and the no-queued-credit debt open 0x8e667356",
        "affected": "both", "severity": "none", "status": "disproved",
        "evidence_tier": "port-free Forge replay, exact live and pinned runtimes",
        "evidence": {"s1_balance_after_five_cycles": str(balance_after_cycles),
                     "s1_same_quote_closes": len(s1_closes),
                     "s2_solvent_win": s2_win["note"], "s2_loss": s2_loss["note"],
                     "s3_liquidation": s3_liq["note"], "s3_empty_harvest_error": s3_harvest["err"],
                     "s5_queued_win": s5_close["note"], "s5_harvest": s5_harvest["note"],
                     "s5_second_harvest": {"err": s5_again["err"], "paid_note": s5_again["note"]},
                     "s7_batch_close": s7_batch["note"], "s8_dust_close": s8_dust["note"],
                     "s8_deadband_close": s8_dead["note"], "s8_over_leverage_error": s8_lev["err"],
                     "s8_oi_cap_error": s8_cap["err"], "s9_withdraw_true": s9_true["note"],
                     "s9_withdraw_false_after_roll": s9_false["note"], "s10_batch": s10["note"],
                     "s4_live_queue_liquidation": s4_liq["note"], "s6_live_queue_loss": s6_loss["note"]},
        "missing_observation": "the notional unit behind the OI cap stays unresolved: the aggregate the open compares "
                               "with is a 96-bit market word and the limit a 128-bit word, so the boundary is quoted "
                               "as the measured raw aggregate (the s8 opens), not as a USDC notional",
        "citations": ["atlas/block_48902346/exchange_open_limit.md",
                      "atlas/block_48902346/live2_payout.md",
                      "artifacts/live2_sequences/steps_live.csv"],
    })

    # --- the paths this replay could not reach -------------------------------
    pushes = [r for r in live if r["step"].startswith("push_")]
    unknown = step_row(live, "s13", "unknown_selector_control")
    pinned_pushes = [r for r in pinned if r["step"].startswith("push_")]
    assert pushes and all(not r["ok"] for r in pushes), pushes
    assert unknown["err"] == "none", unknown
    rows.append({
        "id": "SQ-L2-05",
        "title": "pushStakerFees (the LP-surplus distribution) is unreachable from a stranger, the keeper and the owner in this replay: raw 0x538ccdfd on set 2 and 0x64cd1788 pinned, while an unknown selector reverts with empty data",
        "angle": "A5 extracting the LP's excess share early",
        "invariant": "A3",
        "actor": "stranger, keeper, owner (all attempted)",
        "precondition": "the LP cursor forced above the 5,000,000 USDC cap with a totalQueued of zero, and a second "
                        "state with a negative LP cursor and a live queue",
        "trigger": "pushStakerFees() 0x7b9f5264 from a stranger, the keeper and the owner, plus a control call to an "
                   "unknown selector in the same state",
        "impact": "every caller gets a custom error (0x538ccdfd on set 2, 0x64cd1788 pinned) with no storage write and "
                  "no log, so the LP-excess and staker-fee distribution cannot be exercised from this prestate; the "
                  "control shows the selector exists (an unknown selector reverts with empty data), so the failure is "
                  "a state check rather than a missing entry point. The LP-surplus path therefore stays unproven here, "
                  "and the pass-one read-only pin probe that allowed an unrelated caller is not reproduced",
        "affected": "both", "severity": "info", "status": "blocked",
        "evidence_tier": "port-free Forge replay, exact live and pinned runtimes",
        "evidence": {"live_errors": sorted({r["err"] for r in pushes}),
                     "pinned_errors": sorted({r["err"] for r in pinned_pushes}),
                     "unknown_selector_control": {"ok": unknown["ok"], "err": unknown["err"]},
                     "callers": sorted({note_map(r["note"]).get("caller", "?") for r in pushes}),
                     "storage_writes_and_lp_delta": sorted({note_map(r["note"]).get("lp_delta", "?") for r in pushes})},
        "missing_observation": "the saved prestate is a transaction read-set, so the pointer or flag pushStakerFees "
                               "checks is absent; the name of 0x538ccdfd and 0x64cd1788 is unresolved",
        "citations": ["atlas/block_48902346/exchange_staker_fee_push.md",
                      "atlas/block_48902346/live2_payout.md"],
    })

    result["ledger"] = rows
    result["historical_identity"] = hist
    result["variant_compare"] = {"steps": len(live), "rows_identical_live_vs_pinned": len(identical)}
    return rows


def render_doc(result, rows):
    live = result["variants"]["live"]["steps"]
    pinned = result["variants"]["pinned"]["steps"]
    hist = result["historical_identity"]
    L = []
    A = L.append
    A("# Sequences of legitimate actions against the live Papertrade set")
    A("")
    A("The phase-two hunt for value created or destroyed by *sequences* rather than single calls. The instrument is a "
      "port-free Foundry replay of the exact live runtimes (Exchange `0x0a44049d...`, linked library `0x583d0bd8...`, "
      "SessionKeyManager `0x04b5ea4c...`, Tokenomics `0x7c0a72a7...`) and the pinned set, loaded on the saved "
      "block-48,901,631 prestate, driving the venue's own signed open `0xec6783f0`, signed close `0x2792e706`, signed "
      "withdrawal `0x8d09f23f`, `liquidateBatch(uint256[])` `0x599dc539`, `harvest(uint256)` `0xddc63262` and the real "
      "BatchExecutor `execute` `0x251fb27d` with its saved allowlist. Positions are created by the venue's open, never "
      "written into storage by hand. The only mocked inputs are the HyperCore BBO precompile `0x080e`, the account "
      "status precompile `0x0810` and the spot-balance precompile `0x0801`; every mocked reply is labelled simulated.")
    A("")
    A("Ledger: [`live2_sequences.json`](live2_sequences.json). Per-step raw rows: "
      "[`steps_live.csv`](../../artifacts/live2_sequences/steps_live.csv) and "
      "[`steps_pinned.csv`](../../artifacts/live2_sequences/steps_pinned.csv); full forge output in "
      "`artifacts/live2_sequences/forge_{live,pinned}.txt`. Run `python3 scripts/audit_live2_sequences.py` to re-derive "
      "everything offline; no credential and no network are used.")
    A("")
    A("## The invariant and its correction")
    A("")
    A("```text")
    A("treasury == totalBalances + totalLockedMargin + totalQueued")
    A("            + stakerFeeAccumulator + devFeeAccumulator + trackedLpUsd")
    A("```")
    A("")
    A("Exchange slot 14 is the treasury, slot 22 low and high 128 bits are ordinary balances and locked margin, slot "
      "18 is the queue, slot 26 low and high 128 bits are the staker and developer fee accumulators, and Tokenomics "
      "slot 3 is the signed tracked LP. The **side bucket (Exchange slot 27) is not a claim**: it is an earmark of the "
      "spendable LP bankroll. At block 48,173,889, the real close that wrote "
      f"{hist[0]['side_bucket_after_the_close']} into slot 27 coexists with `treasury - reserved` = "
      f"{hist[0]['queue_harvest_available']} = trackedLp {hist[0]['tracked_lp']} + totalQueued "
      f"{hist[0]['total_queued']}`, whereas adding the side bucket would give "
      f"{hist[0]['tracked_lp_plus_queued_plus_side']}. Adding it double counts the bankroll, and the pass-one identity "
      "(`atlas_all_suite_claims.py`) reconciles only because the pinned side bucket is zero.")
    A("")
    A("The checker is validated by a negative control: writing 20,000 USDC of locked margin without a funding debit moves the residual to -20,000e18. Across the corrected replay, the only non-control deviation is a **positive** 1,000 USDC residual while debt margin is open. The same-quote close returns it to zero; every other settled step reconciles.")
    A("")
    A("## SQ-L2-02: the reported debt-cycle mint is disproved")
    A("")
    A("The earlier replay used a saved transaction read-set that omitted queue head and next-id slots 16 and 17. They defaulted to zero even though the pinned chain state had both at 4. With those pointers seeded coherently, the same exact runtimes consume queued credit on the debt open and restore it on a zero-PnL close. Harvest pays the existing queue once, and another debt open fails after that credit is gone.")
    A("")
    A("| Stage | Queued credit | Accounting residual |")
    A("|---|---:|---:|")
    for label, step_name in (("before debt open", "queue_state"),
                             ("debt margin open", "after_open"),
                             ("after same-quote close", "after_close"),
                             ("after harvest", "after_harvest"),
                             ("after rejected repeat", "end_state")):
        row = step_row(live, "s11", step_name)
        A(f"| {label} | {row['queued'] / 10 ** 18:.6f} | {row['residual'] / 10 ** 18:.6f} |")
    A("")
    A("The earlier 3,237.31 USDC gain and 20,000 USDC claims excess were fixture artifacts. SQ-L2-02 is now `disproved` with severity `none`. This corrected replay rules out the claimed repeatable cycle; it is not an exhaustive proof of all queue states.")
    A("")
    A("## Guards and negatives that held")
    A("")
    A("| Sequence | Observed | Guard |")
    A("|---|---|---|")
    s1 = [r for r in live if r["seq"] == "s1" and r["step"].startswith("close_same_price")]
    A(f"| open then close at the same quote, five times | adj = 0, balance credits {int(note_map(s1[0]['note'])['baldelta']) / 10 ** 18:.0f} USDC each, "
      f"no mint, no fee, residual 0 | the user's claim returns to exactly the starting credit |")
    s5h = next(r for r in live if r["step"] == "harvest_1")
    A(f"| deferred win then harvest twice | first harvest pays {int(note_map(s5h['note'])['paid']) / 10 ** 18:.4f} USDC with tracked LP delta 0, "
      "second reverts `0x75e52f4f` | the queue claim was already debited at the close |")
    A(f"| liquidation with an empty queue | residual 0, margin less the 2 % fee split to stakers and developer | onLoss on the "
      "solvent branch |")
    A(f"| liquidation and a loss with a live queue | side bucket = trackedLp + queued in both, residual 0 | the side bucket is an "
      "earmark of the bankroll, not a second claim |")
    A(f"| both sides of one market closed in one batch at one quote | adj = 0 each, residual 0 | no self-impact |")
    A(f"| one-wei margin open and close | balance delta one raw unit, residual 0 | no rounding leak at the dust bound |")
    A(f"| close one quote unit past the deadband floor | adj = 0 exactly at floor(entry/50000), nonzero one unit later | the deadband "
      "floor is exact |")
    A(f"| open at leverage 1001 | reverts `0x0a4f5a07` | leverage bound 1000 |")
    A(f"| open 6,000e18 margin after the side aggregate grew | reverts `0x40f92143` | OiCapExceeded, the per-side 96/128-bit limit |")
    A(f"| withdraw with a true account status | debit exactly the signed 2 USDC, residual 0 | the signed amount is delivered in full |")
    A(f"| withdraw twice in one block | second reverts; after rolling one block, debit = signed amount + 1 USDC | one withdrawal per user per block |")
    A(f"| two closes in one BatchExecutor transaction | both inner calls execute, two PositionClosed events, residual 0 | the allowlist accepts close |")
    A("")
    A("## Limits")
    A("")
    A("Every replay runs on the saved prestate, so the pinned rows use the saved implementations and the live rows "
      "override the proxy implementation slots with the live runtimes; the raw rows for both are saved and "
      f"{result['variant_compare']['rows_identical_live_vs_pinned']} of {len(live)} rows agree on all nine book fields. "
      "The prestate is a transaction read-set, not a full state, which is why `pushStakerFees` cannot be exercised (see "
      "SQ-L2-05). Mocked precompiles are labelled; no Core transfer is observed. The OI-cap unit stays unresolved, so "
      "the cap boundary is quoted as the measured raw aggregate.")
    A("")
    A("## Ledger")
    A("")
    A("| Id | Title | Invariant | Actor | Affected | Severity | Status |")
    A("|---|---|---|---|---|---|---|")
    for row in rows:
        A(f"| {row['id']} | {row['title']} | {row['invariant']} | {row['actor']} | {row['affected']} | "
          f"{row['severity']} | {row['status']} |")
    A("")
    return chr(10).join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="both", choices=("both", "live", "pinned"))
    ap.add_argument("--skip-forge", action="store_true")
    opts = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"pin": PIN, "pin_hash": PIN_HASH, "prestate_block": PRESTATE_BLOCK,
              "exchange": EXCHANGE, "session_manager": SESSION, "tokenomics": TOKENOMICS,
              "batch_executor": BATCH, "user": USER, "keeper": KEEPER,
              "runtime_sha256": {a: d for a, (_, _, d) in RUNTS["live"].items() if d},
              "variants": {}}
    tags = ("live", "pinned") if opts.variant == "both" else (opts.variant,)
    for tag in tags:
        if opts.skip_forge:
            # Offline re-verification: rebuild everything from the saved rows and logs.
            csv = (OUT / f"steps_{tag}.csv").read_text()
            output = (OUT / f"forge_{tag}.txt").read_text()
            source = source_for(tag)
        else:
            source, output, csv = run_forge(tag)
            (OUT / "Sequence.t.sol").write_text(source)
        passed = sorted(set(re.findall(r"\[PASS\] (test\w+)\(\)", output)))
        failed = sorted(set(re.findall(r"\[FAIL\] (test\w+)\(\)", output)))
        rows = parse_steps(csv)
        if not opts.skip_forge:
            (OUT / f"steps_{tag}.csv").write_text(csv)
        result["variants"][tag] = {
            "source_sha256": sha256_hex(source.encode()), "passed": passed, "failed": failed,
            "steps": rows, "_output": output}
        with open(OUT / f"forge_{tag}.txt", "w") as handle:
            handle.write(output)
        print(f"[{tag}] {len(passed)} passed, {len(failed)} failed, {len(rows)} steps")
        for name in failed:
            print(f"  FAIL {name}")
        for row in rows:
            print(f"  {row['seq']:4s} {row['step']:36s} ok={int(row['ok'])} {row['err'][:22]:22s} "
                  f"res={row['residual']:>24d} q={row['queued']:>6d} side={row['side_bucket']:>6d} {row['note'][:150]}")
    if "live" in result["variants"] and "pinned" in result["variants"]:
        rows = analyze(result)
        for variant in result["variants"].values():
            variant.pop("_output", None)
        REPLAY_PATH.write_text(json.dumps(result, indent=2) + "\n")
        LEDGER.write_text(json.dumps(result, indent=2) + "\n")
        DOC.write_text(render_doc(result, rows))
        print(f"ledger rows: {len(rows)}")
        for row in rows:
            print(f"  {row['id']} {row['status']:20s} {row['affected']:6s} {row['severity']:7s} {row['title']}")
    else:
        (OUT / "replay.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()