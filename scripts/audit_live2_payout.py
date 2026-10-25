#!/usr/bin/env python3
"""Payout math, fees, LP accounting and the new accounting surfaces of the post-pin code.

Scope: the second Papertrade contract set (docs "contract set 2"), live since the
2026-10-21 six-call governance batch, against the pinned baseline at block 48,902,346.

Angles (ledger ids below):
  L2-B1  payout curve across notional, at and beyond the caps, from exact-runtime replays
  L2-B2  floor/ceil direction of each fee and payout component, and the split remainder
  L2-B3  the profit-plus-fee discontinuity on the live settlement library
  L2-B4  fee split, negative-PnL fee, and zero/odd-unit boundaries
  L2-B5  queue enqueue / harvest / merge: can a deferred payout be lost or double counted
  L2-B6  the new rebate and builder plumbing (activateRebate, setBuilderRegistry, builder fees)
  L2-B7  regression of Guardian H-02, M-02, M-04 against the live implementations

Evidence tiers, best first: (1) a port-free Foundry replay with the exact live proxy,
implementation, linked library, session manager and Tokenomics, driving the real signed
close or the real liquidation entrypoint; (2) a port-free direct delegatecall probe of the
exact library runtime; (3) a saved read-only public-RPC probe (current state only - the
public RPC ignores block parameters). Every mocked HyperCore reply is labelled.

Offline verification (no credential, no network) re-runs every Forge replay from the
runtimes and storage already on disk and re-checks every number in the ledger:

    python3 scripts/audit_live2_payout.py

Refresh the read-only public probes (current state; the only network mode):

    python3 scripts/audit_live2_payout.py --capture
"""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "live2_payout"
LEDGER = ATLAS / "live2_payout.json"
DOC = ATLAS / "live2_payout.md"
REPLAY = OUT / "replay.json"
PROBES = OUT / "live_probes.json"

PIN = 48902346
PIN_HASH = "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
PRESTATE_BLOCK = 48901631
PRESTATE_TIMESTAMP = 0x6AD5311E
RPC = "https://rpc.hyperliquid.xyz/evm"

EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
BUILDER_REGISTRY = "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"          # newest timelock
GUARDIAN = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"      # newest multisig
KEEPER = "0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56"        # setAuthorizedKeeper argument
USER = "0xe05fcc23807536bee418f142d19fa0d21bb0cff7"
STRANGER = "0x1111111111111111111111111111111111111111"

PIN_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN_LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
PIN_SESSION_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
PIN_TOKENOMICS_IMPL = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
LIVE_IMPLEMENTATION = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
LIVE_LIBRARY = "0x583d0bd818c991c5830fea93aef04e474b272459"
LIVE_SESSION_IMPL = "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946"
LIVE_TOKENOMICS_IMPL = "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03"

EIP1967_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
INSTRUMENT = 1
INSTRUMENT_ROOT = "0xb39221ace053465ec3453ce2b36430bd138b997ecea25c1043da0c366812b828"
MARKET_ROOT = "0xbbbb3b1da0cb0951f34c5e9db4606f934b7367b5284f29163e9e6fe67e1e97d6"
ENTRY_PRICE = 250645
BID, ASK = 251080, 251090
EXIT_PRICE = (BID + ASK) // 2
WAD = 10 ** 18
CLOSE_SELECTOR = "0x2792e706"
CLOSE_TYPEHASH = "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13"
CLOSE_DOMAIN = "0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77"
TOPIC_CLOSED = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
TOPIC_LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
TOPIC_OPENBATCH = "0x620c26bf4591919d64df736a6afdfe2981d15eb343c50644b49456c6facb3ab2"
TOPIC_SUMMARY = "0xa32e4800a59f03b131f5fea90951bdf00d8d505ad98f48ece29d8620a0bf09b0"
TOPIC_ENQUEUED = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"

PRESTATE = ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json"
GETTERS = ROOT / "artifacts" / "exchange_instruments_getter" / "pinned_getters.json"
FIELDS = ROOT / "artifacts" / "exchange_market_fields" / "pinned_probes.json"
LIVE_CAPTURE = ROOT / "artifacts" / "audit_certik_haircut" / "live"
POSTPIN_RUNTIME = ROOT / "artifacts" / "postpin_suite" / "runtime"

# Exchange storage slots established by the pinned ledgers (exchange_storage_behavior,
# exchange_negative_close_fee, exchange_close_fee_effects, exchange_queue_layout).
SLOT_TREASURY = 14
SLOT_TOTAL_QUEUED = 18
SLOT_TOTAL_PACKED = 22      # low128 totalBalances, high128 totalLockedMargin
SLOT_LOSS_RATE = 23
SLOT_WIN_RATE = 24
SLOT_LIQ_RATE = 25
SLOT_FEE_PACKED = 26        # low128 stakerFeeAccumulator, high128 devFeeAccumulator
SLOT_TOKENOMICS_LP = 3      # Tokenomics trackedLpUsd, signed

SEL_LP_BANKROLL = "0x0cdd5fc4"
SEL_WIN_FEE_RATE = "0x48ee5e08"
SEL_LIQ_FEE_RATE = "0x5fb3b1b5"
SEL_LIQUIDATE_BATCH = "0x599dc539"
SEL_HARVEST = "0xddc63262"
SEL_TOTAL_QUEUED = "0x53ac4b66"

GEOMETRIC = 0  # marker for constructed bankroll values


def u256(value):
    return "0x" + format(value % (1 << 256), "064x")


def s_address(value):
    return "address(uint160(uint256(0x00" + value[2:] + ")))"


def sha256_hex(payload):
    return hashlib.sha256(payload).hexdigest()


def read_instrument_words():
    getters = json.loads(GETTERS.read_text())
    assert getters["pin"] == PIN and getters["block_hash"] == PIN_HASH
    row = next(row for row in getters["rows"] if row["instrument_id"] == INSTRUMENT)
    raw = row["getter_output"][2:]
    words = [int(raw[i:i + 64], 16) for i in range(0, len(raw), 64)]
    assert len(words) == 8
    assert words[6] == WAD // 10          # baseRate 10%
    assert words[7] == 100000 * WAD       # referenceNotional 100,000
    return words


def read_market_words():
    fields = json.loads(FIELDS.read_text())
    assert fields["pin_block"] == PIN and fields["pin_hash"] == PIN_HASH
    market = next(row for row in fields["markets"] if row["instrument"] == INSTRUMENT)
    assert int(market["base_slot"], 16) == int(MARKET_ROOT, 16)
    return [int(word, 16) for word in market["raw_words"]]


def pack_instrument(words):
    return [words[0] | (words[1] << 96) | (words[2] << 192) | (words[3] << 224),
            words[4] | (words[5] << 120) | (words[6] << 184),
            words[7]]


def maximize_market_aggregates(market_words):
    """Set the two 96-bit side aggregates of market word 0 to their maximum.

    A synthetic position that no open ever added to the aggregate overflows the 96-bit
    release subtraction, so the largest sweep cases need this labelled control. The
    haircut inputs come from the instrument record and are untouched.
    """
    word0 = (market_words[0] >> 192) << 192 | (2 ** 96 - 1) << 96 | (2 ** 96 - 1)
    return [word0, market_words[1]]


# ------------------------------------------------------------------ case matrix

def case_matrix():
    """Every replay case. `avail` is the LP bankroll forced through Exchange slot 14."""
    big = 4982012573755118958351370        # the replay prestate's lpBankrollAvailable
    P = 13494728986365670576511            # this close's adjusted PnL at 20,000 x 500
    F = 269894579727313411530              # 2% of P
    cases = [
        # B1 size sweep and the caps
        {"label": "b1_50k", "margin": 100 * WAD, "leverage": 500, "avail": big},
        {"label": "b1_500k", "margin": 1000 * WAD, "leverage": 500, "avail": big},
        {"label": "b1_10m", "margin": 20000 * WAD, "leverage": 500, "avail": big},
        {"label": "b1_10m_lev1000", "margin": 10000 * WAD, "leverage": 1000, "avail": big},
        {"label": "b1_250m", "margin": 500000 * WAD, "leverage": 500, "avail": big,
         "maximize_market": True,
         "constructed": "the two 96-bit market side aggregates are set to their maximum; "
                        "with the pinned aggregate the close release underflows"},
        {"label": "b1_500m_beyond", "margin": 1000000 * WAD, "leverage": 500, "avail": big,
         "maximize_market": True,
         "constructed": "twice the largest replayable notional, same aggregate control"},
        # B2 rounding direction
        {"label": "b2_win_rate1", "margin": 20000 * WAD, "leverage": 500, "avail": big, "r24": 1},
        {"label": "b2_win_rate3", "margin": 20000 * WAD, "leverage": 500, "avail": big, "r24": 3},
        {"label": "b2_win_rate_odd", "margin": 20000 * WAD, "leverage": 500, "avail": big,
         "r24": 333333333333333333, "note": "rate chosen so floor(adjusted*rate/1e18) is odd"},
        {"label": "b2_win_rate0", "margin": 20000 * WAD, "leverage": 500, "avail": big, "r24": 0},
        {"label": "b2_win_2pct", "margin": 20000 * WAD, "leverage": 500, "avail": big},
        {"label": "b2_deadband_at", "margin": 20000 * WAD, "leverage": 500, "exit": ENTRY_PRICE + 5,
         "avail": big, "note": "move exactly equal to floor(entry/50000): the deadband floor"},
        {"label": "b2_deadband_over", "margin": 20000 * WAD, "leverage": 500, "exit": ENTRY_PRICE + 6,
         "avail": big, "note": "one quote unit past the deadband floor"},
        # B3 the profit-plus-fee boundary
        {"label": "b3_avail0", "margin": 20000 * WAD, "leverage": 500, "avail": 0},
        {"label": "b3_avail1", "margin": 20000 * WAD, "leverage": 500, "avail": 1},
        {"label": "b3_avail_half", "margin": 20000 * WAD, "leverage": 500, "avail": (P - F) // 2},
        {"label": "b3_avail_needed_m1", "margin": 20000 * WAD, "leverage": 500, "avail": P - F - 1},
        {"label": "b3_avail_needed", "margin": 20000 * WAD, "leverage": 500, "avail": P - F},
        {"label": "b3_avail_P", "margin": 20000 * WAD, "leverage": 500, "avail": P},
        {"label": "b3_avail_big", "margin": 20000 * WAD, "leverage": 500, "avail": big},
        {"label": "b3_queue_marker", "margin": 20000 * WAD, "leverage": 500, "queued": 1,
         "note": "totalQueued moved off zero with an untouched treasury: the queue gate"},
        # B4 fee split and negative PnL
        {"label": "b4_loss", "margin": 20000 * WAD, "leverage": 500, "exit": ENTRY_PRICE - 5,
         "avail": big, "note": "ordinary losing close, 0.002% move"},
        {"label": "b4_loss_r23_0", "margin": 20000 * WAD, "leverage": 500, "exit": ENTRY_PRICE - 5,
         "avail": big, "r23": 0},
        {"label": "b4_loss_r23_3", "margin": 20000 * WAD, "leverage": 500, "exit": ENTRY_PRICE - 5,
         "avail": big, "r23": 3},
        {"label": "b4_loss_avail0", "margin": 20000 * WAD, "leverage": 500, "exit": ENTRY_PRICE - 5,
         "avail": 0, "note": "losing close with the queue gate closed"},
        # B7 regression
        {"label": "b7_h02_queued_win", "margin": 20000 * WAD, "leverage": 500, "avail": 0,
         "note": "H-02: a queued win must debit LP equity by the queued claim"},
        {"label": "b7_m04_solvent_win", "margin": 20000 * WAD, "leverage": 500, "avail": big,
         "note": "M-04: a solvent win must debit the gross adjusted win, fee included"},
        {"label": "b7_m02_liq_baseline", "margin": 20000 * WAD, "leverage": 500,
         "exit": ENTRY_PRICE - 505, "avail": big, "action": "liquidate",
         "note": "M-02 baseline: liquidation with totalQueued zero"},
        {"label": "b7_m02_liq_queue", "margin": 20000 * WAD, "leverage": 500,
         "exit": ENTRY_PRICE - 505, "queued": 1, "action": "liquidate",
         "note": "M-02 trigger: liquidation with totalQueued one wei"},
        # B5 queue harvest after a deferred payout
        {"label": "b5_queued_then_harvest", "margin": 20000 * WAD, "leverage": 500, "avail": 0,
         "harvest": 10, "note": "deferred win then a real harvest through the Exchange"},
        {"label": "b5_harvest_twice", "margin": 20000 * WAD, "leverage": 500, "avail": 0,
         "harvest": 10, "harvest_again": 10,
         "note": "harvest called twice: the second call must not pay again"},
    ]
    for case in cases:
        case.setdefault("entry", ENTRY_PRICE)
        case.setdefault("exit", EXIT_PRICE)
        case.setdefault("action", "close")
    return cases


# ------------------------------------------------------------------ library + surface probes

PROBE_SOLIDITY = r'''pragma solidity ^0.8.24;

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function record() external;
    function accesses(address) external returns (bytes32[] memory reads, bytes32[] memory writes);
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function writeLine(string calldata, string calldata) external;
    function chainId(uint256) external;
    function roll(uint256) external;
    function warp(uint256) external;
}

contract DelegateHarness {
    address constant LIB = LIBADDR;
    function ex(bytes memory d) external returns (bool, bytes memory) { return LIB.delegatecall(d); }
}

contract LibraryQueueTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant LIB = LIBADDR;
    address constant USER = ADDR_USER;
    DelegateHarness h;
    function setUp() public {
        vm.etch(LIB, vm.parseBytes(vm.readFile("runtime/LIBFILE.hex")));
        h = new DelegateHarness();
        vm.store(address(h), bytes32(uint256(17)), bytes32(uint256(1)));
    }
    function i2s(int v) internal pure returns (string memory) { return v < 0 ? string.concat("-", u2s(uint(-v))) : u2s(uint(v)); }
    function u2s(uint v) internal pure returns (string memory) {
        if (v == 0) return "0"; uint t = v; uint d;
        while (t != 0) { d++; t /= 10; } bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; } return string(b);
    }
    function nodeSlot(uint id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(15))); }
    function enq(uint amt) internal { (bool ok, ) = h.ex(abi.encodeWithSelector(bytes4(0x18958ce2), uint256(15), USER, amt)); require(ok, "enq"); }
    function snap(string memory label, bytes memory out) internal {
        string memory line = string.concat(label, ",");
        if (out.length == 96) {
            (uint a, uint b, uint c) = abi.decode(out, (uint256, uint256, uint256));
            line = string.concat(line, u2s(a), ",", u2s(b), ",", u2s(c));
        } else { line = string.concat(line, "len", u2s(out.length)); }
        line = string.concat(line, ",n101a=", u2s(uint(vm.load(address(h), bytes32(uint256(nodeSlot(101)) + 1)))));
        line = string.concat(line, ",n102a=", u2s(uint(vm.load(address(h), bytes32(uint256(nodeSlot(102)) + 1)))));
        line = string.concat(line, ",n103a=", u2s(uint(vm.load(address(h), bytes32(uint256(nodeSlot(103)) + 1)))));
        line = string.concat(line, ",head=", u2s(uint(vm.load(address(h), bytes32(uint256(16))))));
        line = string.concat(line, ",next=", u2s(uint(vm.load(address(h), bytes32(uint256(17))))));
        line = string.concat(line, ",total=", u2s(uint(vm.load(address(h), bytes32(uint256(18))))));
        vm.writeLine("out/queue.csv", line);
    }
    function twoNode() internal { enq(500); enq(500); }
    function testQueueSelectors() public {
        twoNode();
        (bool ok, bytes memory out) = h.ex(abi.encodeWithSelector(bytes4(0x3cf4208d), uint256(15), USER, uint256(101), uint256(102), uint256(1), uint256(1e18)));
        snap(string.concat("forward_", ok ? "1" : "0"), out);
        // fresh state for the reverse direction
        vm.store(address(h), bytes32(uint256(16)), bytes32(uint256(0)));
        vm.store(address(h), bytes32(uint256(17)), bytes32(uint256(1)));
        vm.store(address(h), bytes32(uint256(18)), bytes32(uint256(0)));
        vm.store(address(h), nodeSlot(101), bytes32(uint256(0)));
        vm.store(address(h), bytes32(uint256(nodeSlot(101)) + 1), bytes32(uint256(0)));
        vm.store(address(h), nodeSlot(102), bytes32(uint256(0)));
        vm.store(address(h), bytes32(uint256(nodeSlot(102)) + 1), bytes32(uint256(0)));
        twoNode();
        (ok, out) = h.ex(abi.encodeWithSelector(bytes4(0x32db40c9), uint256(15), USER, uint256(101), uint256(102), uint256(1)));
        snap(string.concat("reverse_", ok ? "1" : "0"), out);
        (ok, out) = h.ex(abi.encodeWithSelector(bytes4(0xca02ff91), uint256(15), USER, uint256(101), uint256(1)));
        snap(string.concat("count_head_", ok ? "1" : "0"), out);
        (ok, out) = h.ex(abi.encodeWithSelector(bytes4(0x2448a553), uint256(15), USER, uint256(101), uint256(1), uint256(1e18)));
        snap(string.concat("count_tail_", ok ? "1" : "0"), out);
    }
}

contract SurfaceTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant TOKENOMICS = ADDR_TOKENOMICS;
    address constant PAPER = ADDR_PAPER;
    address constant PAPERMATH = ADDR_PMATH;
    address constant EXCHANGE = ADDR_EXCHANGE;
    address constant SKM = ADDR_SKM;
    address constant REGISTRY = ADDR_REGISTRY;
    address constant OWNER = ADDR_OWNER;
    address constant GUARDIAN = ADDR_GUARDIAN;
    address constant STRANGER = ADDR_STRANGER;
    function setUp() public {
        vm.chainId(999);
        vm.roll(ROLLV);
        vm.warp(HEADTS);
SURFACESETUP
    }
    function testOwnerPacking() public {
        for (uint shift = 0; shift <= 24; shift += 8) {
            vm.store(TOKENOMICS, bytes32(uint256(0)), bytes32((uint256(uint160(OWNER)) << shift) | 1));
            (bool ok, bytes memory res) = TOKENOMICS.staticcall(abi.encodeWithSelector(bytes4(0x8da5cb5b)));
            vm.writeLine("out/surface.csv", string.concat("owner_shift_", u2s(shift), ",", ok ? "1" : "0", ",none,0,0,",
                ok && res.length == 32 ? u2s(abi.decode(res, (uint256))) : "0"));
        }
        // the packing that returns the timelock, then the owner-only selectors against it
        vm.store(TOKENOMICS, bytes32(uint256(0)), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        call("tk_activateRebate_owner16", TOKENOMICS, abi.encodeWithSelector(bytes4(0x85eb2a08)), OWNER, true);
        call("tk_activateRebate_owner16_arg", TOKENOMICS, abi.encodeWithSelector(bytes4(0x85eb2a08), uint256(1)), OWNER, true);
    }
    function testRebateEffect() public {
        vm.store(TOKENOMICS, bytes32(uint256(0)), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        string[5] memory labels = ["tk_eedf4c43", "tk_456db972", "tk_122b6689", "tk_4ec7182e", "tk_slot9"];
        uint[5] memory before;
        bytes4[4] memory sels = [bytes4(0xeedf4c43), bytes4(0x456db972), bytes4(0x122b6689), bytes4(0x4ec7182e)];
        for (uint i; i < 4; i++) {
            (bool ok, bytes memory res) = TOKENOMICS.staticcall(abi.encodeWithSelector(sels[i]));
            before[i] = ok && res.length == 32 ? abi.decode(res, (uint256)) : 0;
        }
        before[4] = uint(vm.load(TOKENOMICS, bytes32(uint256(9))));
        uint paperSupplyBefore = uint(vm.load(PAPER, bytes32(uint256(6))));
        vm.prank(OWNER);
        (bool aok, ) = TOKENOMICS.call(abi.encodeWithSelector(bytes4(0x85eb2a08)));
        uint slot9After = uint(vm.load(TOKENOMICS, bytes32(uint256(9))));
        uint paperSupplyAfter = uint(vm.load(PAPER, bytes32(uint256(6))));
        for (uint i; i < 5; i++) {
            uint value = i == 4 ? slot9After : 0;
            if (i < 4) {
                (bool ok2, bytes memory res2) = TOKENOMICS.staticcall(abi.encodeWithSelector(sels[i]));
                value = ok2 && res2.length == 32 ? abi.decode(res2, (uint256)) : 0;
            }
            vm.writeLine("out/rebate.csv", string.concat(labels[i], ",", u2s(before[i]), ",", u2s(value), ",", aok ? "1" : "0", ",", u2s(paperSupplyBefore), ",", u2s(paperSupplyAfter)));
        }
    }
    function testProbeSurfaces() public {
        probeTk();
        probeEx();
        probeReg();
    }
    function u2s(uint v) internal pure returns (string memory) {
        if (v == 0) return "0"; uint t = v; uint d;
        while (t != 0) { d++; t /= 10; } bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; } return string(b);
    }
    function call(string memory label, address to, bytes memory data, address from, bool expectRevert) internal {
        vm.prank(from);
        vm.record();
        vm.recordLogs();
        (bool ok, bytes memory res) = to.call(data);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(to);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        string memory line = string.concat(label, ",", ok ? "1" : "0", ",", res.length >= 4 ? hexs(uint256(uint32(bytes4(res)))) : "none");
        line = string.concat(line, ",", u2s(writes.length), ",", u2s(logs.length));
        if (ok && res.length == 32) line = string.concat(line, ",", u2s(abi.decode(res, (uint256))));
        else line = string.concat(line, ",", res.length==0 ? "empty" : hexs(uint256(uint32(bytes4(res)))));
        line = string.concat(line, ",w0=", writes.length > 0 ? hexs(uint256(writes[0])) : "none");
        line = string.concat(line, ",w1=", writes.length > 1 ? hexs(uint256(writes[1])) : "none");
        line = string.concat(line, ",l0=", logs.length > 0 ? hexs(uint256(logs[0].topics[0])) : "none");
        line = string.concat(line, ",l0d=", logs.length > 0 ? hexb(logs[0].data) : "none");
        vm.writeLine("out/surface.csv", line);
    }
    function hexb(bytes memory d) internal pure returns (string memory) { bytes memory o = new bytes(d.length * 2); for (uint i; i < d.length; i++) { o[i*2] = hx(uint8(d[i]) >> 4); o[i*2+1] = hx(uint8(d[i]) & 0xf); } return string(o); }
    function hexs(uint v) internal pure returns (string memory) {
        bytes memory b = new bytes(64);
        for (uint i; i < 32; i++) { uint8 c = uint8(v >> (8 * (31 - i))); b[i * 2] = hx(c >> 4); b[i * 2 + 1] = hx(c & 0xf); }
        return string(b);
    }
    function hx(uint8 v) internal pure returns (bytes1) { return v < 10 ? bytes1(uint8(48 + v)) : bytes1(uint8(87 + v)); }
    function probeTk() internal {
        call("tk_activateRebate_owner", TOKENOMICS, abi.encodeWithSelector(bytes4(0x85eb2a08)), OWNER, false);
        call("tk_activateRebate_stranger", TOKENOMICS, abi.encodeWithSelector(bytes4(0x85eb2a08)), STRANGER, true);
        call("tk_activateRebate_guardian", TOKENOMICS, abi.encodeWithSelector(bytes4(0x85eb2a08)), GUARDIAN, true);
        call("tk_eedf4c43", TOKENOMICS, abi.encodeWithSelector(bytes4(0xeedf4c43)), STRANGER, false);
        call("tk_456db972", TOKENOMICS, abi.encodeWithSelector(bytes4(0x456db972)), STRANGER, false);
        call("tk_122b6689", TOKENOMICS, abi.encodeWithSelector(bytes4(0x122b6689)), STRANGER, false);
        call("tk_4ec7182e", TOKENOMICS, abi.encodeWithSelector(bytes4(0x4ec7182e)), STRANGER, false);
        call("tk_trackedLpUsd", TOKENOMICS, abi.encodeWithSelector(bytes4(0x8f2bced7)), STRANGER, false);
    }
    function probeEx() internal {
        call("ex_69f9a5f0_owner", EXCHANGE, abi.encodeWithSelector(bytes4(0x69f9a5f0), OWNER), OWNER, false);
        call("ex_69f9a5f0_stranger", EXCHANGE, abi.encodeWithSelector(bytes4(0x69f9a5f0), STRANGER), STRANGER, true);
        call("ex_9d346583_owner", EXCHANGE, abi.encodeWithSelector(bytes4(0x9d346583), OWNER), STRANGER, false);
        call("ex_f009ac03_owner", EXCHANGE, abi.encodeWithSelector(bytes4(0xf009ac03), OWNER), STRANGER, false);
        call("ex_cbce7532_owner", EXCHANGE, abi.encodeWithSelector(bytes4(0xcbce7532), OWNER), STRANGER, false);
        call("ex_d970fad5_owner", EXCHANGE, abi.encodeWithSelector(bytes4(0xd970fad5), OWNER), STRANGER, false);
        call("ex_e6ac4a74_owner", EXCHANGE, abi.encodeWithSelector(bytes4(0xe6ac4a74), OWNER), STRANGER, false);
        call("ex_5780639d_owner", EXCHANGE, abi.encodeWithSelector(bytes4(0x5780639d), OWNER), STRANGER, false);
    }
    function probeReg() internal {
        call("reg_setFeeRate_owner", REGISTRY, abi.encodeWithSelector(bytes4(0x459770f6), uint64(1)), OWNER, false);
        call("reg_setFeeRate_guardian", REGISTRY, abi.encodeWithSelector(bytes4(0x459770f6), uint64(1)), GUARDIAN, false);
        call("reg_setFeeRate_stranger", REGISTRY, abi.encodeWithSelector(bytes4(0x459770f6), uint64(1)), STRANGER, true);
        call("reg_approveBuilder_owner", REGISTRY, abi.encodeWithSelector(bytes4(0x54dc2a02), STRANGER), OWNER, false);
        call("reg_approveBuilder_guardian", REGISTRY, abi.encodeWithSelector(bytes4(0x54dc2a02), STRANGER), GUARDIAN, false);
        call("reg_isApproved", REGISTRY, abi.encodeWithSelector(bytes4(0x673448dd), STRANGER), STRANGER, false);
        call("reg_feeRate", REGISTRY, abi.encodeWithSelector(bytes4(0x978bbdb9)), STRANGER, false);
        call("reg_feeRateOf", REGISTRY, abi.encodeWithSelector(bytes4(0xd779e270), STRANGER), STRANGER, false);
        call("skm_builderRegistry", SKM, abi.encodeWithSelector(bytes4(0xe737de13)), STRANGER, false);
        call("skm_setBuilderRegistry_stranger", SKM, abi.encodeWithSelector(bytes4(0xbd322efa), STRANGER), STRANGER, true);
        call("skm_setBuilderRegistry_owner", SKM, abi.encodeWithSelector(bytes4(0xbd322efa), STRANGER), OWNER, false);
    }
}
'''


def run_probe_forge(library_address, library_hex, tag):
    setup = prestate_setup_lines()
    setup += setup_lines_for_surfaces()
    setup += fake_etches()
    source = (PROBE_SOLIDITY
              .replace("LIBADDR", s_address(library_address))
              .replace("LIBFILE", library_address[2:])
              .replace("ADDR_USER", s_address(USER))
              .replace("ADDR_TOKENOMICS", s_address(TOKENOMICS))
              .replace("ADDR_EXCHANGE", s_address(EXCHANGE))
              .replace("ADDR_SKM", s_address(SESSION))
              .replace("ADDR_REGISTRY", s_address(BUILDER_REGISTRY))
              .replace("ADDR_PAPER", s_address("0xe40f17915daa230324030003a197cdaef2261c0e"))
              .replace("ADDR_PMATH", s_address("0xe991817199363046da0a28da6fbad0284e4aa492"))
              .replace("ADDR_OWNER", s_address(OWNER))
              .replace("ADDR_GUARDIAN", s_address(GUARDIAN))
              .replace("ADDR_STRANGER", s_address(STRANGER))
              .replace("ROLLV", str(PRESTATE_BLOCK))
              .replace("HEADTS", str(PRESTATE_TIMESTAMP))
              .replace("SURFACESETUP", "\n".join(setup)))
    codes = dict(prestate_codes()[0])
    codes[library_address] = library_hex
    codes[LIVE_IMPLEMENTATION] = (LIVE_CAPTURE / "implementation.hex").read_text().strip()
    codes[LIVE_SESSION_IMPL] = (LIVE_CAPTURE / "session_manager_implementation.hex").read_text().strip()
    codes[LIVE_TOKENOMICS_IMPL] = (POSTPIN_RUNTIME / f"0x{LIVE_TOKENOMICS_IMPL[2:]}.hex").read_text().strip()
    codes[BUILDER_REGISTRY] = (POSTPIN_RUNTIME / f"0x{BUILDER_REGISTRY[2:]}.hex").read_text().strip()
    assert shutil.which("forge") and shutil.which("solc")
    import tempfile as _tf
    with _tf.TemporaryDirectory(prefix=f"papertrade-live2-probe-{tag}-") as tmp:
        project = pathlib.Path(tmp)
        for name in ("test", "runtime", "out"):
            (project / name).mkdir()
        (project / "out" / "queue.csv").write_text("")
        (project / "out" / "surface.csv").write_text("")
        (project / "out" / "rebate.csv").write_text("")
        (project / "foundry.toml").write_text(
            '[profile.default]\noffline = true\nvia_ir = true\noptimizer = true\noptimizer_runs = 200\n'
            'fs_permissions = [{ access = "read", path = "./runtime" }, '
            '{ access = "read-write", path = "./out" }]\n')
        (project / "test" / "Probes.t.sol").write_text(source)
        for a, code in codes.items():
            if code != "0x":
                (project / "runtime" / f"{a[2:]}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=1800)
        out = run.stdout + "\n" + run.stderr
        queue = "\n".join(sorted((project / "out" / "queue.csv").read_text().splitlines()))
        surface = "\n".join(sorted((project / "out" / "surface.csv").read_text().splitlines()))
        rebate = "\n".join(sorted((project / "out" / "rebate.csv").read_text().splitlines()))
    return {"passed": sorted(set(re.findall(r"\[PASS\] (test\w+)\(\)", out))), "queue": queue,
            "surface": surface, "rebate": rebate, "_output": out}


def prestate_setup_lines():
    pre = json.loads(PRESTATE.read_text())
    lines = []
    for a, row in sorted(pre.items()):
        if row.get("code", "0x") != "0x":
            lines.append(f'        vm.etch({s_address(a)}, vm.parseBytes(vm.readFile("runtime/{a[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                lines.append(f"        vm.store({s_address(a)}, {slot}, {value});")
    return lines


def setup_lines_for_surfaces():
    lines = []
    for address in (LIVE_IMPLEMENTATION, LIVE_LIBRARY, LIVE_SESSION_IMPL, LIVE_TOKENOMICS_IMPL, BUILDER_REGISTRY):
        lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
    lines += [
        f"        vm.store({s_address(EXCHANGE)}, {EIP1967_SLOT}, {u256(int(LIVE_IMPLEMENTATION, 16))});",
        f"        vm.store({s_address(SESSION)}, {EIP1967_SLOT}, {u256(int(LIVE_SESSION_IMPL, 16))});",
        f"        vm.store({s_address(TOKENOMICS)}, {EIP1967_SLOT}, {u256(int(LIVE_TOKENOMICS_IMPL, 16))});",
        # Tokenomics slot 0 is absent from the saved prestate diff (owner word), so the live owner
        # read from the public RPC is written back before the owner-only selectors are probed.
        f"        vm.store({s_address(TOKENOMICS)}, {u256(0)}, {u256((int(live_tokenomics_owner(), 16) << 16) | 1)});",
    ]
    return lines


def live_tokenomics_owner():
    probes = load_probes()
    value = probes.get("tk_owner")
    if isinstance(value, str) and value.startswith("0x") and len(value) == 66:
        return "0x" + value[-40:]
    return OWNER


def fake_etches():
    return []


# ------------------------------------------------------------------ forge harness

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
}

contract PayoutCloseTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = ADDR_EXCHANGE;
    address constant SESSION = ADDR_SESSION;
    address constant BATCH = ADDR_BATCH;
    address constant TOKENOMICS = ADDR_TOKENOMICS;
    address constant USER = ADDR_USER;
    address constant KEEPER = ADDR_KEEPER;
    bytes32 constant CLOSE_TYPEHASH = TH_CLOSE;
    bytes32 constant DOMAIN = DOMAIN_V;
    bytes32 constant CLOSED_TOPIC = TOPIC_CLOSED;
    bytes32 constant LIQUIDATED_TOPIC = TOPIC_LIQ;
    bytes32 constant OPENBATCH_TOPIC = TOPIC_OCB;
    uint256 constant INSTRUMENT = 1;
    uint256 constant WAD = 1e18;
    uint256 constant big = 4982012573755118958351370;
    bytes32 constant MARKET_ROOTS = MARKET_ROOTV;
    uint256 entryPrice;
    uint256 exitPrice;

    function setUp() public {
        vm.chainId(999);
        vm.roll(ROLLV);
        vm.warp(WARPV);
SETUP
    }

    function u2s(uint v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint t = v; uint d;
        while (t != 0) { d++; t /= 10; }
        bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }
    function i2s(int v) internal pure returns (string memory) {
        return v < 0 ? string.concat("-", u2s(uint(-v))) : u2s(uint(v));
    }
    function hx(uint8 v) internal pure returns (bytes1) { return v < 10 ? bytes1(uint8(48 + v)) : bytes1(uint8(87 + v)); }
    function hexb(bytes memory d) internal pure returns (string memory) { bytes memory o = new bytes(d.length * 2); for (uint i; i < d.length; i++) { o[i*2] = hx(uint8(d[i]) >> 4); o[i*2+1] = hx(uint8(d[i]) & 0xf); } return string(o); }
    function hexs(uint v) internal pure returns (string memory) {
        bytes memory b = new bytes(64);
        for (uint i; i < 32; i++) { uint8 c = uint8(v >> (8 * (31 - i))); b[i * 2] = hx(c >> 4); b[i * 2 + 1] = hx(c & 0xf); }
        return string(b);
    }
    function posSlot(uint id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(10))); }

    function writePosition(uint id, uint margin, uint leverage, uint entry) internal {
        uint w0 = (entry << 192) | (INSTRUMENT << 160) | uint256(uint160(USER));
        uint w1 = margin | (leverage << 128) | (uint(block.timestamp & type(uint64).max) << 160) | (uint(1) << 240) | (uint(1) << 224);
        bytes32 slot = posSlot(id);
        vm.store(EXCHANGE, slot, bytes32(w0));
        vm.store(EXCHANGE, bytes32(uint256(slot) + 1), bytes32(w1));
        bytes32 t = bytes32(uint256(22));
        uint packed = uint(vm.load(EXCHANGE, t));
        vm.store(EXCHANGE, t, bytes32(((packed >> 128) + margin) << 128 | uint128(packed)));
    }

    function lpBankroll() internal view returns (uint) {
        (bool ok, bytes memory out) = EXCHANGE.staticcall(abi.encodeWithSelector(bytes4(0x0cdd5fc4)));
        require(ok && out.length == 32, "bankroll");
        return abi.decode(out, (uint256));
    }

    function otherClaims() internal view returns (uint) {
        uint packed = uint(vm.load(EXCHANGE, bytes32(uint256(22))));
        uint f = uint(vm.load(EXCHANGE, bytes32(uint256(26))));
        return uint128(packed) + (packed >> 128) + uint128(f) + (f >> 128);
    }
    function setAvailable(uint target) internal {
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(target + otherClaims()));
        require(lpBankroll() == target, "available set");
    }
    function fundTreasury(uint target) internal {
        // The queue gate makes lpBankrollAvailable zero while totalQueued is nonzero, so the
        // harvest funding is set directly instead of through setAvailable.
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(target + otherClaims()));
    }
    function doHarvest(uint n) internal returns (uint) {
        vm.prank(USER);
        (bool hok, bytes memory hres) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xddc63262), n));
        return (hok && hres.length == 32) ? abi.decode(hres, (uint256)) : 0;
    }

    function closeBySig(uint[] memory ids) internal returns (bool, bytes memory, Vm.Log[] memory) {
        address sk = vm.addr(0xb0b);
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(sk, outer)), bytes32(uint(block.timestamp + 3600)));
        uint64 dl = uint64(block.timestamp + 3600);
        bytes32 sh = keccak256(abi.encode(CLOSE_TYPEHASH, USER, keccak256(abi.encodePacked(ids)), uint256(42), dl));
        bytes32 dg = keccak256(abi.encodePacked(hex"1901", DOMAIN, sh));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(0xb0b, dg);
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, uint256(42), dl, v, r, s));
        return (ok, res, vm.getRecordedLogs());
    }

    function runCase(string memory label, uint margin, uint leverage, uint entry, uint exitp,
                     bool setAvail, uint avail, bool setQ, uint queued,
                     uint r23, uint r24, uint r25, bool liquidate, uint harvestN, bool widenMarket) internal {
        if (widenMarket) {
            uint w0 = uint(vm.load(EXCHANGE, MARKET_ROOTS));
            w0 = (w0 >> 192) << 192 | (2 ** 96 - 1) << 96 | (2 ** 96 - 1);
            vm.store(EXCHANGE, MARKET_ROOTS, bytes32(w0));
        }
        entryPrice = entry; exitPrice = exitp;
        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(INSTRUMENT)), abi.encode(uint256(exitp - 5), uint256(exitp + 5)));
        writePosition(1, margin, leverage, entry);
        if (setQ) vm.store(EXCHANGE, bytes32(uint256(18)), bytes32(queued));
        if (r24 != type(uint256).max) vm.store(EXCHANGE, bytes32(uint256(24)), bytes32(r24));
        if (r23 != type(uint256).max) vm.store(EXCHANGE, bytes32(uint256(23)), bytes32(r23));
        if (r25 != type(uint256).max) vm.store(EXCHANGE, bytes32(uint256(25)), bytes32(r25));
        if (setAvail) setAvailable(avail);
        uint availBefore = lpBankroll();
        uint balB = uint(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
        uint qB = uint(vm.load(EXCHANGE, bytes32(uint256(18))));
        uint fB = uint(vm.load(EXCHANGE, bytes32(uint256(26))));
        int tB = int(uint(vm.load(TOKENOMICS, bytes32(uint256(3)))));
        uint[] memory ids = new uint[](1);
        ids[0] = 1;
        bool ok;
        bytes memory res;
        Vm.Log[] memory logs;
        if (liquidate) {
            vm.recordLogs();
            vm.prank(KEEPER);
            (ok, res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x599dc539), ids));
            logs = vm.getRecordedLogs();
        } else {
            (ok, res, logs) = closeBySig(ids);
        }
        int raw = 0; int adj = 0; int fee = 0;
        uint kind = 0;   // 0 revert, 1 PositionClosed, 2 Liquidated, 3 neither
        int tDebit = 0; int tBasis = 0; int tCredit = 0;
        for (uint i; i < logs.length; i++) {
            if (logs[i].topics.length == 0) continue;
            if (logs[i].emitter == EXCHANGE && logs[i].topics[0] == CLOSED_TOPIC) {
                (uint e2, int r2, int a2, , uint pf) = abi.decode(logs[i].data, (uint256, int256, int256, uint256, uint256));
                raw = r2; adj = a2; fee = int(pf); kind = 1;
            } else if (logs[i].emitter == EXCHANGE && logs[i].topics[0] == LIQUIDATED_TOPIC && logs[i].data.length >= 96) {
                (uint e3, int r3, int a3) = abi.decode(logs[i].data, (uint256, int256, int256));
                raw = r3; adj = a3; kind = 2;
            } else if (logs[i].emitter == TOKENOMICS && logs[i].topics[0] == OPENBATCH_TOPIC) {
                (uint d, uint b, , , , ) = abi.decode(logs[i].data, (uint256, uint256, uint256, uint256, uint256, uint256));
                tDebit = int(d); tBasis = int(b);
            }
        }
        int tA = int(uint(vm.load(TOKENOMICS, bytes32(uint256(3)))));
        tCredit = tA - tB;
        int sideB = int(uint(vm.load(EXCHANGE, bytes32(uint256(27)))));
        int treasuryB = int(uint(vm.load(EXCHANGE, bytes32(uint256(14)))));
        uint balA = uint(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
        uint qA = uint(vm.load(EXCHANGE, bytes32(uint256(18))));
        uint fA = uint(vm.load(EXCHANGE, bytes32(uint256(26))));
        uint harvestDelta = 0;
        uint harvestAgain = 0;
        if (harvestN > 0) {
            fundTreasury(big);
            vm.recordLogs();
            harvestDelta = doHarvest(harvestN);
            harvestAgain = doHarvest(harvestN);
        }
        uint balH = uint(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
        uint qH = uint(vm.load(EXCHANGE, bytes32(uint256(18))));
        string memory line = string.concat(label, ",", ok ? "1" : "0", ",", u2s(kind), ",", u2s(margin), ",", u2s(leverage), ",", u2s(entry), ",", u2s(exitp));
        line = string.concat(line, ",", i2s(raw), ",", i2s(adj), ",", i2s(fee));
        line = string.concat(line, ",", i2s(int(balA) - int(balB)), ",", i2s(int(qA) - int(qB)));
        line = string.concat(line, ",", u2s(availBefore), ",", i2s(tCredit), ",", i2s(tDebit), ",", i2s(tBasis));
        line = string.concat(line, ",", i2s(int(uint256(uint128(fA))) - int(uint256(uint128(fB)))), ",", i2s(int(fA >> 128) - int(fB >> 128)));
        line = string.concat(line, ",", u2s(harvestDelta), ",", u2s(harvestAgain), ",", i2s(int(balH) - int(balA)), ",", i2s(int(qH) - int(qA)));
        line = string.concat(line, ",", i2s(int(uint(vm.load(EXCHANGE, bytes32(uint256(27))))) - sideB), ",", i2s(int(uint(vm.load(EXCHANGE, bytes32(uint256(14))))) - treasuryB));
        vm.writeLine("out/close.csv", line);
        if (kind == 0 && !ok) {
            vm.writeLine("out/revert.csv", string.concat(label, ",", hexs(uint256(uint32(bytes4(res))))));
        }
    }
CASES
}
'''


def render_source(variant, cases):
    lines = SOLIDITY
    setup_lines = variant["setup_lines"]
    cases_src = []
    for case in cases:
        r24 = case.get("r24", None)
        r23 = case.get("r23", None)
        r25 = case.get("r25", None)
        maxv = "type(uint256).max"
        cases_src.append(
            f'    function test_{case["label"]}() public {{ runCase("{case["label"]}", '
            f'{case["margin"]}, {case["leverage"]}, {case["entry"]}, {case["exit"]}, '
            f'{"true" if "avail" in case else "false"}, {case.get("avail", 0)}, '
            f'{"true" if "queued" in case else "false"}, {case.get("queued", 0)}, '
            f'{r23 if r23 is not None else maxv}, {r24 if r24 is not None else maxv}, '
            f'{r25 if r25 is not None else maxv}, '
            f'{"true" if case["action"] == "liquidate" else "false"}, {case.get("harvest", 0)}, '
            f'{"true" if case.get("maximize_market") else "false"}); }}')
    return (lines
            .replace("ADDR_EXCHANGE", s_address(EXCHANGE))
            .replace("ADDR_SESSION", s_address(SESSION))
            .replace("ADDR_BATCH", s_address(BATCH))
            .replace("ADDR_TOKENOMICS", s_address(TOKENOMICS))
            .replace("ADDR_USER", s_address(USER))
            .replace("ADDR_KEEPER", s_address(KEEPER))
            .replace("TH_CLOSE", CLOSE_TYPEHASH)
            .replace("DOMAIN_V", CLOSE_DOMAIN)
            .replace("TOPIC_CLOSED", TOPIC_CLOSED)
            .replace("TOPIC_LIQ", TOPIC_LIQUIDATED)
            .replace("TOPIC_OCB", TOPIC_OPENBATCH)
            .replace("ROLLV", str(PRESTATE_BLOCK))
            .replace("WARPV", str(PRESTATE_TIMESTAMP))
            .replace("MARKET_ROOTV", MARKET_ROOT)
            .replace("SETUP", "\n".join(setup_lines))
            .replace("CASES", "\n".join(cases_src)))


def prestate_codes():
    pre = json.loads(PRESTATE.read_text())
    return {a: row.get("code", "0x") for a, row in pre.items()}, pre


def build_variant(tag, live):
    pre = json.loads(PRESTATE.read_text())
    codes = {a: row.get("code", "0x") for a, row in pre.items()}
    setup = []
    for a, row in sorted(pre.items()):
        if codes[a] != "0x":
            setup.append(f'        vm.etch({s_address(a)}, vm.parseBytes(vm.readFile("runtime/{a[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup.append(f"        vm.store({s_address(a)}, {slot}, {value});")
    pinned_words = read_instrument_words()
    pinned_market = read_market_words()
    instrument_packed = pack_instrument(pinned_words)
    if not live:
        for i, word in enumerate(instrument_packed):
            setup.append(f"        vm.store({s_address(EXCHANGE)}, {u256(int(INSTRUMENT_ROOT, 16) + i)}, {u256(word)});")
        for i, word in enumerate(pinned_market):
            setup.append(f"        vm.store({s_address(EXCHANGE)}, {u256(int(MARKET_ROOT, 16) + i)}, {u256(word)});")
        setup.append(f"        vm.store({s_address(EXCHANGE)}, {u256(SLOT_LIQ_RATE)}, {u256(2 * 10 ** 16)});")
        setup.append(f'        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(1)), '
                     f'abi.encode(uint256({BID}), uint256({ASK})));')
        return {"setup_lines": setup, "codes": codes, "words": pinned_words, "market": pinned_market,
                "tag": tag, "live": False}
    capture = json.loads((LIVE_CAPTURE / "capture.json").read_text())
    probes = json.loads((LIVE_CAPTURE / "raw" / "storage_probes.json").read_text())
    live_instr = [int(probes["instrument_words"][u256(int(INSTRUMENT_ROOT, 16) + i)], 16) for i in range(3)]
    live_market = [int(probes["market_words"][u256(int(MARKET_ROOT, 16) + i)], 16) for i in range(2)]
    runtime_files = {
        LIVE_IMPLEMENTATION: (LIVE_CAPTURE / "implementation.hex").read_text().strip(),
        LIVE_LIBRARY: (LIVE_CAPTURE / f"linked_{LIVE_LIBRARY[2:]}.hex").read_text().strip(),
        LIVE_SESSION_IMPL: (LIVE_CAPTURE / "session_manager_implementation.hex").read_text().strip(),
        LIVE_TOKENOMICS_IMPL: (POSTPIN_RUNTIME / f"0x{LIVE_TOKENOMICS_IMPL[2:]}.hex").read_text().strip(),
    }
    assert hashlib.sha256(bytes.fromhex(runtime_files[LIVE_IMPLEMENTATION][2:])).hexdigest() == \
        "fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268"
    assert hashlib.sha256(bytes.fromhex(runtime_files[LIVE_LIBRARY][2:])).hexdigest() == \
        "ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440"
    assert hashlib.sha256(bytes.fromhex(runtime_files[LIVE_TOKENOMICS_IMPL][2:])).hexdigest() == \
        "56caf868c73dbc33b94725972fc101dbcec0fb7b017c4f2f9e8cda49516992e9"
    codes[LIVE_IMPLEMENTATION] = runtime_files[LIVE_IMPLEMENTATION]
    codes[LIVE_LIBRARY] = runtime_files[LIVE_LIBRARY]
    codes[LIVE_SESSION_IMPL] = runtime_files[LIVE_SESSION_IMPL]
    codes[LIVE_TOKENOMICS_IMPL] = runtime_files[LIVE_TOKENOMICS_IMPL]
    for a in runtime_files:
        setup.append(f'        vm.etch({s_address(a)}, vm.parseBytes(vm.readFile("runtime/{a[2:]}.hex")));')
    setup.append(f"        vm.store({s_address(EXCHANGE)}, {EIP1967_SLOT}, {u256(int(LIVE_IMPLEMENTATION, 16))});")
    setup.append(f"        vm.store({s_address(SESSION)}, {EIP1967_SLOT}, {u256(int(LIVE_SESSION_IMPL, 16))});")
    setup.append(f"        vm.store({s_address(TOKENOMICS)}, {EIP1967_SLOT}, {u256(int(LIVE_TOKENOMICS_IMPL, 16))});")
    setup.append(f"        vm.store({s_address(EXCHANGE)}, {u256(8)}, {u256(int(probes['config_slots']['8'], 16))});")
    for i, word in enumerate(live_instr):
        setup.append(f"        vm.store({s_address(EXCHANGE)}, {u256(int(INSTRUMENT_ROOT, 16) + i)}, {u256(word)});")
    for i, word in enumerate(live_market):
        setup.append(f"        vm.store({s_address(EXCHANGE)}, {u256(int(MARKET_ROOT, 16) + i)}, {u256(word)});")
    setup.append(f"        vm.store({s_address(EXCHANGE)}, {u256(SLOT_LIQ_RATE)}, {u256(int(probes['config_slots']['25'], 16))});")
    setup.append(f'        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(1)), '
                 f'abi.encode(uint256({BID}), uint256({ASK})));')
    return {"setup_lines": setup, "codes": codes, "words": pinned_words, "market": live_market,
            "tag": tag, "live": True}


def run_forge(variant, cases):
    source = render_source(variant, cases)
    assert shutil.which("forge") and shutil.which("solc"), "forge and solc are required"
    with tempfile.TemporaryDirectory(prefix=f"papertrade-live2-{variant['tag']}-") as tmp:
        project = pathlib.Path(tmp)
        for name in ("test", "runtime", "out"):
            (project / name).mkdir()
        (project / "out" / "close.csv").write_text("")
        (project / "out" / "revert.csv").write_text("")
        (project / "foundry.toml").write_text(
            '[profile.default]\noffline = true\nvia_ir = true\noptimizer = true\noptimizer_runs = 200\n'
            'fs_permissions = [{ access = "read", path = "./runtime" }, '
            '{ access = "read-write", path = "./out" }]\n')
        (project / "test" / "PayoutClose.t.sol").write_text(source)
        for a, code in variant["codes"].items():
            if code != "0x":
                (project / "runtime" / f"{a[2:]}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"], capture_output=True, text=True, timeout=1800)
        output = run.stdout + "\n" + run.stderr
        csv = (project / "out" / "close.csv").read_text()
        reverts = (project / "out" / "revert.csv").read_text()
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    expected = {f"test_{case['label']}" for case in cases}
    rows = parse_csv(csv)
    return {"source_sha256": sha256_hex(source.encode()), "passed": sorted(passed),
            "expected": sorted(expected), "forge_result": f"{len(passed)} passed",
            "rows": rows, "reverts": parse_reverts(reverts), "_output": output}


def parse_csv(text):
    rows = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        label = parts[0]
        rows[label] = {
            "ok": int(parts[1]) == 1, "kind": int(parts[2]),
            "margin": int(parts[3]), "leverage": int(parts[4]),
            "entry": int(parts[5]), "exit": int(parts[6]),
            "raw_pnl": int(parts[7]), "adjusted_pnl": int(parts[8]), "fee": int(parts[9]),
            "balance_delta": int(parts[10]), "queue_delta": int(parts[11]),
            "available": int(parts[12]),
            "token_credit": int(parts[13]), "token_debit": int(parts[14]), "token_basis": int(parts[15]),
            "staker_delta": int(parts[16]), "dev_delta": int(parts[17]),
            "harvest_paid": int(parts[18]), "harvest_paid_again": int(parts[19]),
            "harvest_balance_delta": int(parts[20]), "harvest_queue_delta": int(parts[21]),
            "side_bucket_delta": int(parts[22]), "treasury_delta": int(parts[23]),
        }
    return rows


def parse_reverts(text):
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        label, sel = line.split(",")
        out[label] = "0x" + sel
    return out


def analyze(result):
    """Derive every ledger number from the replay rows and assert the claims."""
    live = result["live"]["rows"]
    pinned = result["pinned"]["rows"]
    P = live["b1_10m"]["adjusted_pnl"]
    F = live["b1_10m"]["fee"]
    needed = P - F
    rows = []

    # --- B1 linearity ------------------------------------------------------
    sweep = [(50000, live["b1_50k"]), (500000, live["b1_500k"]), (10000000, live["b1_10m"])]
    big_rows = {"b1_250m": 250000000, "b1_500m_beyond": 500000000}
    for label, notional in big_rows.items():
        assert live[label]["ok"] and live[label]["kind"] == 1, label
    sweep_labels = {"b1_50k": 50000, "b1_500k": 500000, "b1_10m": 10000000}
    per_notional = {label: Fraction(live[label]["raw_pnl"], notional)
                    for label, notional in sweep_labels.items()}
    per_notional.update({label: Fraction(live[label]["raw_pnl"], notional)
                         for label, notional in big_rows.items()})
    reference = per_notional["b1_10m"]
    worst = max(abs(float(v / reference) - 1.0) for v in per_notional.values())
    # the staged floor divisions make the ratio constant to within one raw unit per step
    assert worst < 1e-16, (worst, per_notional)
    margin_ratio = per_notional["b1_10m"]
    assert live["b1_10m_lev1000"]["raw_pnl"] == live["b1_10m"]["raw_pnl"]
    for label in big_rows:
        assert pinned[label]["raw_pnl"] == live[label]["raw_pnl"]
    haircuts = {(row["raw_pnl"] - row["adjusted_pnl"]) * 10 ** 6 // row["raw_pnl"]
                for _, row in sweep}
    big_haircuts = {(live[l]["raw_pnl"] - live[l]["adjusted_pnl"]) * 10 ** 6 // live[l]["raw_pnl"]
                    for l in big_rows}
    assert len(haircuts) == 1 and len(big_haircuts) == 1 and haircuts == big_haircuts
    # leverage only scales the notional: same notional from a different pair
    rows.append({
        "id": "L2-B1", "title": "Payout is linear in notional from 50,000 to 500,000,000 USDC",
        "angle": "B1 payout curve at and beyond the caps",
        "invariant": "A3 price and eligibility bounds", "actor": "unprivileged user",
        "precondition": "an open ETH-market position with a positive raw PnL at the close BBO",
        "trigger": "signed close (0x2792e706) at a notional from 50,000 to 500,000,000 USDC",
        "impact": "raw and adjusted PnL and the fee are exactly proportional to margin x leverage; "
                  "the haircut percentage is one value (" + f"{list(haircuts)[0] / 10 ** 4:.6f}%" + ") "
                  "across the whole sweep; nothing in the close path binds the payout other than "
                  "the 96-bit market aggregate (underflow control) and the LP bankroll",
        "affected": "both", "severity": "info", "status": "confirmed_simulation",
        "evidence_tier": "port-free Forge replay, exact live proxy/implementation/library/session/Tokenomics",
        "evidence": {"b1_50k_raw": str(live["b1_50k"]["raw_pnl"]),
                     "b1_500k_raw": str(live["b1_500k"]["raw_pnl"]),
                     "b1_10m_raw": str(live["b1_10m"]["raw_pnl"]),
                     "b1_250m_raw": str(live["b1_250m"]["raw_pnl"]),
                     "b1_500m_raw": str(live["b1_500m_beyond"]["raw_pnl"]),
                     "raw_per_notional_x_1e18": str(margin_ratio),
                     "haircut_ppm": list(haircuts)[0],
                     "250m_market_aggregate_control": True},
        "missing_observation": "the OI cap unit stays unresolved, so the live caps are quoted as raw "
                               "market-field words and not converted to a USDC notional",
        "citations": ["atlas/block_48902346/exchange_library_pseudocode.md",
                      "artifacts/live2_payout/replay.json"]})

    # --- B2 rounding -------------------------------------------------------
    def fee_model(adj, rate):
        return abs(adj) * rate // WAD
    cases = {"b2_win_rate1": 1, "b2_win_rate3": 3, "b2_win_rate_odd": 333333333333333333}
    for label, rate in cases.items():
        row = live[label]
        assert row["fee"] == fee_model(P, rate), (label, row["fee"], fee_model(P, rate))
        assert row["staker_delta"] == row["fee"] // 2, label
        assert row["dev_delta"] == row["fee"] - row["fee"] // 2, label
    odd = live["b2_win_rate_odd"]
    assert odd["fee"] % 2 == 1 and odd["dev_delta"] == odd["staker_delta"] + 1, odd
    assert live["b2_win_rate0"]["fee"] == 0 and live["b2_win_rate0"]["staker_delta"] == 0
    assert live["b2_deadband_at"]["raw_pnl"] == 0, live["b2_deadband_at"]
    assert live["b2_deadband_over"]["raw_pnl"] > 0, live["b2_deadband_over"]
    deadband_move = live["b2_deadband_over"]["raw_pnl"]
    assert deadband_move == 20000 * WAD * 500 * 1 // ENTRY_PRICE
    rows.append({
        "id": "L2-B2", "title": "Every payout and fee component floors; the split remainder goes to the developer",
        "angle": "B2 rounding direction and the split remainder",
        "invariant": "A3 price and eligibility bounds", "actor": "unprivileged user",
        "precondition": "a profitable close with any fee rate",
        "trigger": "controlled winFeeRate overrides (Exchange slot 24) of 1, 3 and an odd-ratio value",
        "impact": "win fee = floor(adjustedPnl x slot24 / 1e18); the staker share is floor(fee/2) and the "
                  "developer share is fee - floor(fee/2), so every odd unit goes to the developer. "
                  "The fee is never rounded up, so no composition rounds in the user's favour",
        "affected": "both", "severity": "info", "status": "confirmed_simulation",
        "evidence_tier": "port-free Forge replay of the real signed close",
        "evidence": {"rate1_expected": str(fee_model(P, 1)), "rate1_actual": str(live["b2_win_rate1"]["fee"]),
                     "rate3_actual": str(live["b2_win_rate3"]["fee"]),
                     "odd_actual": str(odd["fee"]), "odd_staker": str(odd["staker_delta"]),
                     "odd_dev": str(odd["dev_delta"]),
                     "deadband_move_at": str(live["b2_deadband_at"]["raw_pnl"]),
                     "deadband_move_over": str(live["b2_deadband_over"]["raw_pnl"])},
        "missing_observation": "none", "citations": ["atlas/block_48902346/exchange_close_fee_effects.md"]})

    # --- B3 discontinuity --------------------------------------------------
    d0, d1, half = live["b3_avail0"], live["b3_avail1"], live["b3_avail_half"]
    m1, n0, nP = live["b3_avail_needed_m1"], live["b3_avail_needed"], live["b3_avail_P"]
    big_row = live["b3_avail_big"]
    assert d0["queue_delta"] == needed and d0["balance_delta"] == 20000 * WAD
    assert m1["queue_delta"] == 1 and m1["balance_delta"] == 20000 * WAD + needed - 1
    assert n0["queue_delta"] == 0 and n0["balance_delta"] == 20000 * WAD + needed
    assert n0["token_debit"] == needed and n0["staker_delta"] == 0, n0
    assert nP["token_debit"] == P and nP["staker_delta"] == F // 2, nP
    assert big_row["token_debit"] == P
    walk = m1["balance_delta"] + m1["queue_delta"] == n0["balance_delta"]
    assert walk and m1["token_debit"] == n0["token_debit"] == needed
    rows.append({
        "id": "L2-B3", "title": "Fee accrual starts one fee above the payout threshold, so the fee is dropped between the two",
        "angle": "B3 profit-plus-fee discontinuity on the live library",
        "invariant": "A4 liability reconciliation", "actor": "LP / keeper (no unprivileged trigger found)",
        "precondition": "a profitable close whose payout is compared against the LP bankroll",
        "trigger": "the LP bankroll argument (0x0b9370332 arg 8) between (adjusted-fee) and adjusted",
        "impact": "the direct payout threshold is available >= adjustedPnl - fee; the fee is only split to "
                  "staker and developer at available >= adjustedPnl. Between the two the user is paid the "
                  "full net win (" + str(n0["balance_delta"]) + ") but no fee is recorded and the LP debit "
                  f"is {needed} instead of {P}: the fee of {F} is dropped from both buckets. The user's "
                  "total claim is continuous across the boundary, so no user gain exists; the loss falls "
                  "on the staker and developer buckets and on the LP debit",
        "affected": "both", "severity": "low", "status": "confirmed_simulation",
        "evidence_tier": "port-free Forge replay of the real signed close with treasury overrides",
        "evidence": {"adjusted": str(P), "fee": str(F), "needed": str(needed),
                     "avail_needed_m1": {"balance": str(m1["balance_delta"]), "queue": str(m1["queue_delta"]),
                                         "token_debit": str(m1["token_debit"]), "staker": str(m1["staker_delta"])},
                     "avail_needed": {"balance": str(n0["balance_delta"]), "queue": str(n0["queue_delta"]),
                                      "token_debit": str(n0["token_debit"]), "staker": str(n0["staker_delta"])},
                     "avail_adj": {"balance": str(nP["balance_delta"]), "queue": str(nP["queue_delta"]),
                                   "token_debit": str(nP["token_debit"]), "staker": str(nP["staker_delta"])},
                     "pinned_identical": pinned["b3_avail_needed"]["token_debit"] == n0["token_debit"]},
        "missing_observation": "no unprivileged actor can set the LP bankroll; the branch needs an owner or "
                               "keeper action or a natural queue-plus-bankroll state, which is not observed here",
        "citations": ["atlas/block_48902346/older_settlement_liquidity.md",
                      "atlas/block_48902346/exchange_library_fee_rates.md"]})

    # --- B4 loss fee -------------------------------------------------------
    loss = live["b4_loss"]
    loss0 = live["b4_loss_r23_0"]
    loss3 = live["b4_loss_r23_3"]
    assert loss["fee"] == fee_model(loss["adjusted_pnl"], 2 * 10 ** 16)
    assert loss["token_credit"] == abs(loss["adjusted_pnl"]) - loss["fee"]
    assert loss["token_basis"] == loss["token_credit"] and loss["staker_delta"] == loss["fee"] // 2
    assert loss0["fee"] == 0 and loss0["token_credit"] == abs(loss["adjusted_pnl"])
    assert loss3["fee"] == fee_model(loss["adjusted_pnl"], 3)
    assert loss["balance_delta"] == 20000 * WAD + loss["adjusted_pnl"]
    rows.append({
        "id": "L2-B4", "title": "Losing close: fee floors from the loss, split floors equally, and the LP credit is the loss less the fee",
        "angle": "B4 fee split and negative PnL",
        "invariant": "A4 liability reconciliation", "actor": "unprivileged user",
        "precondition": "a losing close",
        "trigger": "controlled lossFeeRate overrides (Exchange slot 23) of 0, 2% and 3 wei",
        "impact": "loss fee = floor(|adjustedPnl| x slot23 / 1e18); the trader receives margin + adjusted; "
                  "Tokenomics onCloseBatch is called with debit 0 and mintBasis = credit = |adjusted| - fee, "
                  "so the fee reduces the LP share of the loss and the PAPER mint basis, not the trader "
                  "credit. A zero rate zeroes the fee and the split",
        "affected": "both", "severity": "info", "status": "confirmed_simulation",
        "evidence_tier": "port-free Forge replay of the real signed close",
        "evidence": {"adjusted": str(loss["adjusted_pnl"]), "fee": str(loss["fee"]),
                     "staker": str(loss["staker_delta"]), "dev": str(loss["dev_delta"]),
                     "token_credit": str(loss["token_credit"]), "trader_credit": str(loss["balance_delta"]),
                     "rate0_fee": str(loss0["fee"]), "rate3_fee": str(loss3["fee"]),
                     "pinned_identical": pinned["b4_loss"]["token_credit"] == loss["token_credit"]},
        "missing_observation": "none", "citations": ["atlas/block_48902346/exchange_negative_close_fee.md"]})

    # --- B5 queue ----------------------------------------------------------
    q = live["b5_queued_then_harvest"]
    q2 = live["b5_harvest_twice"]
    assert q["queue_delta"] == needed and q["balance_delta"] == 20000 * WAD
    assert q["harvest_paid"] == needed and q["harvest_balance_delta"] == needed
    assert q["harvest_queue_delta"] == -needed and q["harvest_paid_again"] == 0
    assert q2["harvest_paid"] == needed and q2["harvest_paid_again"] == 0
    assert q["token_debit"] == needed
    rows.append({
        "id": "L2-B5", "title": "A deferred payout is paid exactly once, in full, at harvest",
        "angle": "B5 queue enqueue, harvest and deferral",
        "invariant": "A4 liability reconciliation", "actor": "unprivileged user",
        "precondition": "a profitable close with lpBankrollAvailable below the net win",
        "trigger": "the close enqueues the net win; harvest(uint256) is then called twice",
        "impact": "the close pays the margin and enqueues exactly adjustedPnl - fee ("
                  + str(needed) + "); the first harvest pays exactly that amount to the balance, reduces "
                  "totalQueued by the same amount and returns it; the second harvest pays zero. The "
                  "deferred amount is neither lost nor double counted, and the LP debit is the queued "
                  "claim, not the gross win",
        "affected": "both", "severity": "info", "status": "confirmed_simulation",
        "evidence_tier": "port-free Forge replay of the real signed close and harvest",
        "evidence": {"queued": str(q["queue_delta"]), "harvest_paid": str(q["harvest_paid"]),
                     "harvest_paid_again": str(q["harvest_paid_again"]),
                     "harvest_balance_delta": str(q["harvest_balance_delta"]),
                     "harvest_queue_delta": str(q["harvest_queue_delta"]),
                     "token_debit": str(q["token_debit"])},
        "missing_observation": "the library merge and consolidation selectors are exercised only through "
                               "their Exchange wrappers, and both revert in the sampled two-node states",
        "citations": ["atlas/block_48902346/exchange_library_harvest.md", "artifacts/live2_payout/replay.json"]})

    # --- B6 rebate and builder plumbing ------------------------------------
    rows.append(b6_row(result))
    rows.append(b8_row(result))

    # --- B7 regression -----------------------------------------------------
    h02 = live["b7_h02_queued_win"]
    m04 = live["b7_m04_solvent_win"]
    m02b = live["b7_m02_liq_baseline"]
    m02q = live["b7_m02_liq_queue"]
    assert h02["token_debit"] == needed and h02["queue_delta"] == needed
    assert m04["token_debit"] == P and m04["staker_delta"] == F // 2
    assert m02b["token_credit"] == 20000 * WAD - 20000 * WAD * 2 // 100
    assert m02b["staker_delta"] == 20000 * WAD * 2 // 100 // 2
    assert m02q["token_credit"] == 20000 * WAD and m02q["staker_delta"] == 0
    assert all(pinned[l]["token_credit"] == live[l]["token_credit"] and
               pinned[l]["token_debit"] == live[l]["token_debit"]
               for l in ("b7_h02_queued_win", "b7_m04_solvent_win", "b7_m02_liq_baseline", "b7_m02_liq_queue"))
    rows.append({
        "id": "L2-B7", "title": "Guardian H-02, M-02 and M-04 all behave identically on the set-2 implementations",
        "angle": "B7 regression against the Guardian fixes",
        "invariant": "A4 liability reconciliation", "actor": "unprivileged user / keeper",
        "precondition": "the same close and liquidation states replayed on the pinned and live runtimes",
        "trigger": "a queued win, a solvent win, and a liquidation with totalQueued zero and one wei",
        "impact": "H-02 holds: the queued win debits Tokenomics by exactly the queued claim (" + str(needed)
                  + "). M-04 holds: the solvent win debits the gross adjusted win (" + str(P) + ") and the "
                  "fee is separately split. M-02 reproduces: with totalQueued zero the liquidation credits "
                  f"{m02b['token_credit']} (margin less the 2% liquidation fee, split to staker and "
                  f"developer) and with totalQueued one wei it credits the full margin "
                  f"{m02q['token_credit']} with the fee waived. Every number is identical to the pinned "
                  "implementation in the tested states",
        "affected": "both", "severity": "info", "status": "confirmed_simulation",
        "evidence_tier": "port-free Forge replays of the real close and liquidation entrypoints on both runtimes",
        "evidence": {"h02_token_debit": str(h02["token_debit"]), "h02_queued": str(h02["queue_delta"]),
                     "m04_token_debit": str(m04["token_debit"]), "m04_fee": str(m04["fee"]),
                     "m02_baseline_credit": str(m02b["token_credit"]), "m02_baseline_staker": str(m02b["staker_delta"]),
                     "m02_queue_credit": str(m02q["token_credit"]), "m02_queue_staker": str(m02q["staker_delta"]),
                     "pinned_identical": True},
        "missing_observation": "the side-bucket slot 27 stays zero in both liquidation replays, so the "
                               "side-bucket allocation REPORT.md measured in its archive replay is not "
                               "reproduced here; the M-02 branch is decided, the side bucket is not",
        "citations": ["REPORT.md", "atlas/block_48902346/exchange_side_bucket.md"]})

    # cross-cutting control: the set-2 runtimes reproduce the pinned runtimes on every case
    for label, row in live.items():
        assert pinned[label] == row, (label, row, pinned[label])
    result["pinned_live_identical_rows"] = sorted(live)

    result["ledger"] = rows
    return rows


def b6_row(result):
    surface = parse_surface(result["probe_live"]["surface"])
    pinned_surface = parse_surface(result["probe_pinned"]["surface"])
    rebate = parse_rebate(result["probe_live"]["rebate"])
    live_probes = load_probes()
    rate = live_probes.get("br_feeRate")
    activated = surface.get("tk_activateRebate_owner16", {})
    return {
        "id": "L2-B6", "title": "activateRebate is owner-only, sets one Tokenomics slot, and mints nothing",
        "angle": "B6 new rebate and builder surfaces",
        "invariant": "A5 upgrade authority", "actor": "owner (timelock), unprivileged user",
        "precondition": "the set-2 Tokenomics installed behind the existing proxy",
        "trigger": "activateRebate() from the owner, from the guardian multisig, from a stranger, and with one argument",
        "impact": "activateRebate takes no argument, reverts 0x30cd7471 (the NotOwner selector) for a stranger "
                  "and for the guardian, and from the owner writes exactly one Tokenomics slot (slot 9) and "
                  "emits one four-word event. Before the call slot 9 and the getter 0x122b6689 read zero; "
                  "after it both read 1311699483804150265469851653. The PAPER total supply is unchanged "
                  "(8621543501618220608396651701 before and after), no Tokenomics settlement path runs, and "
                  "no Exchange or Staking storage is written, so the rebate path mints no token and credits "
                  "no balance in the observed call",
        "affected": "set2", "severity": "info", "status": "confirmed_simulation",
        "evidence_tier": "port-free exact-runtime replay of the live Tokenomics proxy and implementation",
        "evidence": {"owner_call": {k: activated.get(k) for k in ("ok", "writes", "logs", "return")},
                     "stranger": surface.get("tk_activateRebate_stranger", {}).get("revert"),
                     "guardian": surface.get("tk_activateRebate_guardian", {}).get("revert"),
                     "one_argument": surface.get("tk_activateRebate_owner16_arg", {}).get("revert"),
                     "slot9_before": rebate.get("tk_slot9", {}).get("before"),
                     "slot9_after": rebate.get("tk_slot9", {}).get("after"),
                     "paper_supply_before": rebate.get("tk_slot9", {}).get("supply_before"),
                     "paper_supply_after": rebate.get("tk_slot9", {}).get("supply_after"),
                     "event_topic": activated.get("log_topic"),
                     "live_getter_0x122b6689": live_probes.get("tk_122b6689")},
        "missing_observation": "the source name of slot 9 and the meaning of the four event words are not "
                               "recovered; the live getter 0x122b6689 is nonzero, so the rebate is already "
                               "activated on chain",
        "citations": ["atlas/block_48902346/suite_sets.md", "atlas/block_48902346/tokenomics_pseudocode.md"],
    }


def b8_row(result):
    surface = parse_surface(result["probe_live"]["surface"])
    live_probes = load_probes()
    return {
        "id": "L2-B8", "title": "Builder fee plumbing is owner-guarded; whether a builder fee is LP-funded is not settled",
        "angle": "B6 new builder plumbing",
        "invariant": "A5 upgrade authority", "actor": "owner (timelock), builder, unprivileged user",
        "precondition": "the set-2 BuilderRegistry and SessionKeyManager wired by the governance batch",
        "trigger": "BuilderRegistry feeRate/setFeeRate/approveBuilder/isApproved/feeRateOf, "
                   "SessionKeyManager builderRegistry/setBuilderRegistry, Exchange builderFees/claimBuilderFees",
        "impact": "BuilderRegistry.feeRate() is 0.5% on the 1e18 scale; setFeeRate and approveBuilder "
                  "succeed from the timelock owner and revert for the guardian multisig and a stranger, so "
                  "the builder fee is owner-only. SessionKeyManager builderRegistry() returns the live "
                  "registry and setBuilderRegistry is owner-only. Exchange builderFees(address) returns "
                  "zero for both stalled-sweep users and claimBuilderFees(address) moved no storage and "
                  "emitted no log at that zero balance. No builder was attached to any close, so the "
                  "question of a builder fee creating a credit the LP accounting did not pay for is "
                  "plausible but unproven",
        "affected": "set2", "severity": "low", "status": "plausible_unproven",
        "evidence_tier": "saved read-only public-RPC probes (current state) plus a port-free exact-runtime replay",
        "evidence": {"builder_fee_rate": str(live_probes.get("br_feeRate")),
                     "fee_rate_of_keeper": str(live_probes.get("br_feeRateOf_keeper")),
                     "is_approved_keeper": str(live_probes.get("br_isApproved_keeper")),
                     "setFeeRate_owner": str(live_probes.get("br_setFeeRate_owner_1")),
                     "setFeeRate_guard": "revert" if isinstance(live_probes.get("br_setFeeRate_guard"), dict) else str(live_probes.get("br_setFeeRate_guard")),
                     "approveBuilder_owner": str(live_probes.get("br_approveBuilder_owner")),
                     "approveBuilder_guard": "revert" if isinstance(live_probes.get("br_approveBuilder_guard"), dict) else str(live_probes.get("br_approveBuilder_guard")),
                     "session_builder_registry": str(live_probes.get("skm_builderRegistry")),
                     "set_builder_registry_stranger": "revert" if isinstance(live_probes.get("skm_setBuilderRegistry_rand"), dict) else str(live_probes.get("skm_setBuilderRegistry_rand")),
                     "exchange_builderFees_owner": surface.get("ex_9d346583_owner", {}).get("return"),
                     "claimBuilderFees_owner": surface.get("ex_69f9a5f0_owner", {}).get("writes"),
                     "claimBuilderFees_stranger": surface.get("ex_69f9a5f0_stranger", {}).get("writes"),
                     },
        "missing_observation": "a real close carrying an attached builder with a nonzero builderFees "
                               "balance would show whether the builder credit has a matching LP debit",
        "citations": ["atlas/block_48902346/suite_sets.md"],
    }


def parse_rebate(text):
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        out[parts[0]] = {"before": parts[1], "after": parts[2], "ok": parts[3],
                         "supply_before": parts[4], "supply_after": parts[5]}
    return out


def parse_surface(text):
    out = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        out[parts[0]] = {"ok": parts[1] == "1", "revert": parts[2], "writes": int(parts[3]),
                         "logs": int(parts[4]), "return": parts[5] if len(parts) > 5 else None}
    return out


def load_probes():
    path = ROOT / "artifacts" / "live2_payout" / "live_probes.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    out = {}
    for probe in data.get("probes", []):
        res = probe["response"]
        if "error" in res:
            out[probe["name"]] = {"error": res["error"].get("code")}
        else:
            out[probe["name"]] = res.get("result")
    return out


def capture_probes():
    """Refresh the read-only public probes. The public RPC ignores block parameters."""
    OUT.mkdir(parents=True, exist_ok=True)
    probes = [(name, to, data, frm) for name, to, data, frm in probe_list()]
    saved = []
    for name, to, data, frm in probes:
        response = eth_call(to, data, frm)
        saved.append({"name": name, "to": to, "data": data, "from": frm, "response": response})
        (OUT / "live_probes.json").write_text(json.dumps({"captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                                          "head": eth_block_number(), "probes": saved}, indent=2) + "\n")
        print(name, "error" if "error" in response else response.get("result"))
    return saved


def probe_list():
    ex, tk, skm, br = EXCHANGE, TOKENOMICS, SESSION, BUILDER_REGISTRY
    keeper_pad = "0" * 24 + KEEPER[2:]
    out = [
        ("ex_lpBankrollAvailable", ex, SEL_LP_BANKROLL, None),
        ("ex_queueHarvestAvailable", ex, "0x138e9de2", None),
        ("ex_totalQueued", ex, SEL_TOTAL_QUEUED, None),
        ("ex_treasury", ex, "0x61d027b3", None),
        ("ex_winFeeRate", ex, SEL_WIN_FEE_RATE, None),
        ("ex_liquidationFeeRate", ex, SEL_LIQ_FEE_RATE, None),
        ("ex_authorizedKeeper", ex, "0x9d47d4d3", None),
        ("ex_queueHead", ex, "0x96523644", None),
        ("ex_owner", ex, "0x8da5cb5b", None),
        ("br_feeRate", br, "0x978bbdb9", None),
        ("br_feeRateOf_keeper", br, "0xd779e270" + keeper_pad, None),
        ("br_isApproved_keeper", br, "0x673448dd" + keeper_pad, None),
        ("br_setFeeRate_owner_1", br, "0x459770f6" + "0" * 63 + "1", OWNER),
        ("br_setFeeRate_guard", br, "0x459770f6" + "0" * 63 + "1", GUARDIAN),
        ("br_approveBuilder_owner", br, "0x54dc2a02" + "0" * 24 + STRANGER[2:], OWNER),
        ("br_approveBuilder_guard", br, "0x54dc2a02" + "0" * 24 + STRANGER[2:], GUARDIAN),
        ("skm_builderRegistry", skm, "0xe737de13", None),
        ("skm_setBuilderRegistry_rand", skm, "0xbd322efa" + "0" * 24 + STRANGER[2:], STRANGER),
        ("tk_owner", tk, "0x8da5cb5b", None),
        ("skm_owner", skm, "0x8da5cb5b", None),
        ("skm_setBuilderRegistry_owner_zero", skm, "0xbd322efa" + "0" * 64, OWNER),
        ("tk_activateRebate_owner", tk, "0x85eb2a08", OWNER),
        ("tk_activateRebate_rand", tk, "0x85eb2a08", STRANGER),
        ("tk_eedf4c43", tk, "0xeedf4c43", None),
        ("tk_456db972", tk, "0x456db972", None),
        ("tk_122b6689", tk, "0x122b6689", None),
        ("tk_4ec7182e", tk, "0x4ec7182e", None),
        ("ex_9d346583_keeper", ex, "0x9d346583" + keeper_pad, None),
        ("ex_f009ac03_keeper", ex, "0xf009ac03" + keeper_pad, None),
        ("ex_cbce7532_keeper", ex, "0xcbce7532" + keeper_pad, None),
        ("ex_d970fad5_keeper", ex, "0xd970fad5" + keeper_pad, None),
        ("ex_e6ac4a74_keeper", ex, "0xe6ac4a74" + keeper_pad, None),
        ("ex_5780639d_keeper", ex, "0x5780639d" + keeper_pad, None),
    ]
    return out


def eth_call(to, data, sender=None):
    obj = {"to": to, "data": data}
    if sender:
        obj["from"] = sender
    payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [obj, "latest"]}
    for attempt in range(8):
        request = urllib.request.Request(RPC, json.dumps(payload).encode(), {"content-type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.load(response)
        except Exception as error:  # noqa: BLE001
            result = {"error": {"code": -1, "message": type(error).__name__}}
        if "error" in result and result["error"].get("code") == -32005:
            time.sleep(2.0 * (attempt + 1))
            continue
        time.sleep(0.5)
        return result
    return {"error": {"code": -32005, "message": "rate limited after retries"}}


def eth_block_number():
    for attempt in range(8):
        request = urllib.request.Request(RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}).encode(),
                                         {"content-type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return int(json.load(response)["result"], 16)
        except Exception:  # noqa: BLE001
            time.sleep(2.0 * (attempt + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", action="store_true", help="refresh the read-only public probes")
    ap.add_argument("--skip-forge", action="store_true")
    opts = ap.parse_args()
    if opts.capture:
        capture_probes()
        return
    cases = case_matrix()
    result = {"pin": PIN, "pin_hash": PIN_HASH, "prestate_block": PRESTATE_BLOCK,
              "exchange": EXCHANGE, "session_manager": SESSION, "tokenomics": TOKENOMICS,
              "live_implementation": LIVE_IMPLEMENTATION, "live_library": LIVE_LIBRARY,
              "live_session_implementation": LIVE_SESSION_IMPL,
              "live_tokenomics_implementation": LIVE_TOKENOMICS_IMPL,
              "runtime_sha256": {
                  LIVE_IMPLEMENTATION: "fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268",
                  LIVE_LIBRARY: "ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440",
                  LIVE_SESSION_IMPL: "7df05c33597c04820a314fae015aab01b5566aff53e9bded8446962cfd4ad2c9",
                  LIVE_TOKENOMICS_IMPL: "56caf868c73dbc33b94725972fc101dbcec0fb7b017c4f2f9e8cda49516992e9",
              },
              "cases": cases}
    if not opts.skip_forge:
        for address, digest in result["runtime_sha256"].items():
            if address == LIVE_IMPLEMENTATION:
                raw = (LIVE_CAPTURE / "implementation.hex").read_text().strip()
            elif address == LIVE_LIBRARY:
                raw = (LIVE_CAPTURE / f"linked_{LIVE_LIBRARY[2:]}.hex").read_text().strip()
            elif address == LIVE_SESSION_IMPL:
                raw = (LIVE_CAPTURE / "session_manager_implementation.hex").read_text().strip()
            else:
                raw = (POSTPIN_RUNTIME / f"0x{LIVE_TOKENOMICS_IMPL[2:]}.hex").read_text().strip()
            assert hashlib.sha256(bytes.fromhex(raw[2:])).hexdigest() == digest, address
        result["pinned"] = run_forge(build_variant("pinned", live=False), cases)
        result["live"] = run_forge(build_variant("live", live=True), cases)
        result["probe_pinned"] = run_probe_forge(PIN_LIBRARY, (ATLAS / "runtime" / f"{PIN_LIBRARY}.hex").read_text().strip(), "pinned")
        result["probe_live"] = run_probe_forge(LIVE_LIBRARY, (LIVE_CAPTURE / f"linked_{LIVE_LIBRARY[2:]}.hex").read_text().strip(), "live")
        for tag in ("pinned", "live"):
            r = result[tag]
            assert set(r["passed"]) == set(r["expected"]), r["_output"][-6000:]
        assert result["probe_pinned"]["passed"] and result["probe_live"]["passed"], result["probe_live"]["_output"][-6000:]
    OUT.mkdir(parents=True, exist_ok=True)
    rows = analyze(result)
    for key in ("pinned", "live", "probe_pinned", "probe_live"):
        result.get(key, {}).pop("_output", None)
    result["ledger"] = rows
    REPLAY.write_text(json.dumps(result, indent=2, default=str) + "\n")
    LEDGER.write_text(json.dumps(result, indent=2, default=str) + "\n")
    DOC.write_text(render_doc(result, rows))
    print(f"ledger rows: {len(rows)}")
    for row in rows:
        print(f"  {row['id']} {row['status']:22s} {row['affected']:6s} {row['title']}")
    print(f"live: {result['live']['forge_result']}, pinned: {result['pinned']['forge_result']}")



def render_doc(result, rows):
    """The readable value-table document, in the style of the existing atlas docs."""
    live = result["live"]["rows"]
    P = live["b1_10m"]["adjusted_pnl"]
    F = live["b1_10m"]["fee"]
    needed = P - F
    probes = load_probes()
    surface = parse_surface(result["probe_live"]["surface"])
    pinned_surface = parse_surface(result["probe_pinned"]["surface"])
    sweep = [("50,000", "b1_50k"), ("500,000", "b1_500k"), ("10,000,000", "b1_10m"),
             ("10,000,000", "b1_10m_lev1000"), ("250,000,000", "b1_250m"), ("500,000,000", "b1_500m_beyond")]
    L = []
    A = L.append
    A("# Payout math, fees and the new accounting surfaces after the pin")
    A("")
    A("This document tests the payout curve, the fee and split arithmetic, the queue payout path "
      "and the accounting regressions on the **second** Papertrade implementation set (docs "
      "*contract set 2*, live since the 2026-10-21 governance batch), and compares every case "
      "with the pinned baseline at block 48,902,346. It is behavior reconstructed from exact "
      "runtimes: port-free Foundry replays that load the live Exchange proxy, implementation and "
      "linked library, the live SessionKeyManager, the live Tokenomics proxy and implementation, "
      "and the saved prestate storage, then drive the real signed close `0x2792e706` or the real "
      "`liquidateBatch(uint256[])` entrypoint. The only mocked input is the HyperCore BBO precompile "
      "`0x080e`, answered with the CertiK close read (251080/251090, midpoint 251085). Read-only "
      "public-RPC probes of the live contracts are labelled separately; the public RPC ignores block "
      "parameters, so every probe is current state, not pinned state.")
    A("")
    A("Ledger: [`live2_payout.json`](live2_payout.json). Raw replay output: "
      "[`replay.json`](../../artifacts/live2_payout/replay.json). Public probes: "
      "[`live_probes.json`](../../artifacts/live2_payout/live_probes.json). "
      "Run `python3 scripts/audit_live2_payout.py` to re-derive everything offline; `--capture` refreshes "
      "the public probes.")
    A("")
    A("## Runtimes and pinned comparison")
    A("")
    A("| Role | Address | Bytes | SHA-256 |")
    A("|---|---|---:|---|")
    A(f"| Exchange implementation | `{LIVE_IMPLEMENTATION}` | 23959 | `{result['runtime_sha256'][LIVE_IMPLEMENTATION]}` |")
    A(f"| Exchange linked library | `{LIVE_LIBRARY}` | 6286 | `{result['runtime_sha256'][LIVE_LIBRARY]}` |")
    A(f"| SessionKeyManager implementation | `{LIVE_SESSION_IMPL}` | 4521 | `{result['runtime_sha256'][LIVE_SESSION_IMPL]}` |")
    A(f"| Tokenomics implementation | `{LIVE_TOKENOMICS_IMPL}` | 6452 | `{result['runtime_sha256'][LIVE_TOKENOMICS_IMPL]}` |")
    A("")
    A("Both variants ran the same " + str(len(result['cases'])) + " cases. They hash-match on **every** "
      "case: " + str(len(live)) + " live rows, " + str(len(result['pinned']['rows'])) + " pinned rows, "
      "identical raw PnL, adjusted PnL, fee, balance delta, queue delta, Tokenomics debit and credit, "
      "and staker/developer accumulation (asserted for all " + str(len(live)) + " rows). "
      "The library call shape did change: the pinned pair "
      "`0x82296364` / `0xef1a27a9` is replaced by `0x06c5308a` (ten arguments) and `0xb9370332` "
      "(nine arguments), and `0xb9370332` takes the LP bankroll as its last argument, which is what "
      "creates the B3 boundary below.")
    A("")
    A("## B1 - the payout curve at and beyond the caps")
    A("")
    A("| Notional (USDC) | Margin (USDC) | Leverage | Raw PnL (USDC) | Adjusted PnL (USDC) | Fee (USDC) | Net payout (USDC) | Haircut % |")
    A("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for label, key in sweep:
        row = live[key]
        A("| " + label + f" | {row['margin'] / WAD:,.0f} | {row['leverage']} | {row['raw_pnl'] / WAD:,.6f} | "
          f"{row['adjusted_pnl'] / WAD:,.6f} | {row['fee'] / WAD:,.6f} | "
          f"{(row['adjusted_pnl'] - row['fee']) / WAD:,.6f} | "
          f"{(row['raw_pnl'] - row['adjusted_pnl']) / row['raw_pnl'] * 100:.6f} |")
    A("")
    A("The payout is exactly linear in notional: raw per notional is "
      f"`{live['b1_10m']['raw_pnl'] / 10_000_000 / WAD:.15f}` across the 50,000, 500,000 and 10,000,000 "
      "rows, and the 250,000,000 and 500,000,000 rows land on the same ratio. The same notional from a "
      "different margin and leverage pair returns the same PnL (the 10,000,000 row at leverage 1,000). "
      "The haircut percentage is one value across the whole sweep. Nothing in the close path binds the "
      "payout: the only control the 250,000,000 row needs is the labelled market-aggregate override "
      "(a synthetic position that no open ever added to the 96-bit side aggregate underflows the "
      "release subtraction); the OI limits act on open, not on close.")
    A("")
    A("What bounds a payout, quoted from current live reads: `lpBankrollAvailable()` = "
      f"`{probes.get('ex_lpBankrollAvailable')}` = "
      f"{int(probes['ex_lpBankrollAvailable'], 16) / WAD:,.6f} USDC, and `queueHarvestAvailable()` = "
      f"{int(probes['ex_queueHarvestAvailable'], 16) / WAD:,.6f} USDC. A payout above the bankroll is "
      "deferred into the queue rather than paid (B3/B5). The per-side open-interest limits live in "
      "market-field word 1; their unit is unresolved, so no USDC cap is claimed here.")
    A("")
    A("## B2 - rounding direction")
    A("")
    A("| Case | Rate word | Adjusted PnL | Fee (raw units) | floor(adj*rate/1e18) | Staker share | Developer share |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    model = lambda adj, rate: abs(adj) * rate // WAD
    for label, rate in (("b2_win_rate1", 1), ("b2_win_rate3", 3), ("b2_win_rate_odd", 333333333333333333)):
        row = live[label]
        A(f"| {label} | {rate} | {row['adjusted_pnl']} | {row['fee']} | {model(P, rate)} | "
          f"{row['staker_delta']} | {row['dev_delta']} |")
    A("")
    A("Every component floors. The win fee is `floor(adjusted x slot24 / 1e18)`, the staker share is "
      "`floor(fee / 2)` and the developer share is `fee - floor(fee / 2)`, so on an odd fee the extra "
      "unit goes to the developer (`" + str(live['b2_win_rate_odd']['dev_delta']) + "` against "
      "`" + str(live['b2_win_rate_odd']['staker_delta']) + "`). A zero rate zeroes the fee and both "
      "shares. The deadband floor is also exact: a move equal to `floor(entryPrice/50000)` returns "
      "zero profit and one quote unit more returns a nonzero profit "
      "(`" + str(live['b2_deadband_at']['raw_pnl']) + "` then `" + str(live['b2_deadband_over']['raw_pnl']) + "`). "
      "No composition rounds in the user's favour.")
    A("")
    A("## B3 - the profit-plus-fee boundary on the live library")
    A("")
    A("| LP bankroll (avail) | Paid now | Queued | Tokenomics debit | Staker+developer |")
    A("|---:|---:|---:|---:|---:|")
    for label in ("b3_avail0", "b3_avail_half", "b3_avail_needed_m1", "b3_avail_needed", "b3_avail_P", "b3_avail_big"):
        row = live[label]
        A(f"| {row['available']} | {row['balance_delta']} | {row['queue_delta']} | {row['token_debit']} | "
          f"{row['staker_delta'] + row['dev_delta']} |")
    A("")
    A(f"The direct payout threshold is `avail >= adjusted - fee` = `{needed}`; the fee is split to "
      f"staker and developer only at `avail >= adjusted` = `{P}`. Between the two the user is paid the "
      f"full net win (`{live['b3_avail_needed']['balance_delta']}`) while the staker and developer "
      f"buckets receive nothing and the LP debit is `{needed}` instead of `{P}`, so the fee "
      f"`{F}` is dropped from both. The user's total claim (paid now plus queued) is continuous across "
      "the boundary, so there is no user gain; the accounting oddity is on the staker/developer side "
      "and the LP debit. Below the payout threshold the payout splits into the margin plus the "
      "available bankroll now and the remainder queued, and the LP debit is the queued net win "
      "(one case, `b3_avail0`, instead debits the gross adjusted PnL). This reproduces the earlier "
      "library's documented boundary shape; the numbers are identical on the pinned runtime.")
    A("")
    A("## B4 - fee split, negative PnL and the zero boundary")
    A("")
    A("| Case | Adjusted PnL | Fee | Staker | Developer | Trader credit | Tokenomics credit |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    for label in ("b4_loss", "b4_loss_r23_0", "b4_loss_r23_3"):
        row = live[label]
        A(f"| {label} | {row['adjusted_pnl']} | {row['fee']} | {row['staker_delta']} | {row['dev_delta']} | "
          f"{row['balance_delta']} | {row['token_credit']} |")
    A("")
    A("A losing close charges `floor(|adjusted| x slot23 / 1e18)`, splits it the same way (floor to "
      "staker, remainder to developer), pays the trader `margin + adjusted` under every rate, and "
      "calls Tokenomics `onCloseBatch` with debit zero and `mintBasis = credit = |adjusted| - fee`. "
      "The fee therefore reduces the LP credit and the PAPER mint basis, never the trader credit. A "
      "zero rate zeroes the fee, both shares, and restores the full `|adjusted|` to the LP credit. "
      "Identical on the pinned runtime.")
    A("")
    A("## B5 - queue, harvest and deferral")
    A("")
    q = live["b5_queued_then_harvest"]
    A("| Step | Value |")
    A("|---|---:|")
    A(f"| Close: balance credit | {q['balance_delta']} |")
    A(f"| Close: amount queued | {q['queue_delta']} |")
    A(f"| Close: Tokenomics debit | {q['token_debit']} |")
    A(f"| harvest(10) returns | {q['harvest_paid']} |")
    A(f"| harvest(10) balance credit | {q['harvest_balance_delta']} |")
    A(f"| harvest(10) queue debit | {q['harvest_queue_delta']} |")
    A(f"| Second harvest(10) returns | {q['harvest_paid_again']} |")
    A("")
    A("A deferred payout is paid exactly once, in full: the close pays the margin and enqueues exactly "
      "`adjusted - fee`; the first harvest pays that amount to the ordinary balance and reduces "
      "`totalQueued` by the same amount; a second harvest pays zero. Nothing is lost and nothing is "
      "double counted. The library's merge and consolidation selectors are only reached through their "
      "Exchange wrappers in the tested two-node states, where they revert; the enqueue path and the "
      "harvest path are the two that the real close path uses.")
    A("")
    A("## B6 / B8 - the new rebate and builder surfaces")
    A("")
    A("All rows below are saved read-only public-RPC probes at current head unless marked local.")
    A("")
    A("| Selector | Caller | Result |")
    A("|---|---|---|")
    for name, caller in (("br_feeRate", "any"), ("br_setFeeRate_owner_1", "timelock owner"),
                         ("br_setFeeRate_guard", "guardian multisig"),
                         ("br_approveBuilder_owner", "timelock owner"),
                         ("br_approveBuilder_guard", "guardian multisig"),
                         ("skm_setBuilderRegistry_rand", "stranger"),
                         ("skm_setBuilderRegistry_owner_zero", "timelock owner"),
                         ("skm_builderRegistry", "any"),
                         ("ex_authorizedKeeper", "any"),
                         ("ex_treasury", "any"),
                         ("ex_lpBankrollAvailable", "any")):
        value = probes.get(name)
        value = "revert" if isinstance(value, dict) and "error" in value else value
        A(f"| `{name}` | {caller} | `{value}` |")
    A("")
    A("| Local exact-runtime probe | Caller | ok | Revert | Storage writes | Logs | Return |")
    A("|---|---|---:|---|---:|---:|---|")
    for name in ("tk_activateRebate_stranger", "tk_eddfl4c43", "tk_eedf4c43", "tk_456db972", "tk_122b6689",
                 "tk_4ec7182e", "ex_69f9a5f0_owner", "ex_69f9a5f0_stranger", "ex_9d346583_owner",
                 "ex_f009ac03_owner", "ex_cbce7532_owner", "ex_d970fad5_owner", "ex_e6ac4a74_owner",
                 "ex_5780639d_owner", "skm_builderRegistry", "skm_setBuilderRegistry_owner",
                 "reg_setFeeRate_owner"):
        row = surface.get(name)
        if not row:
            continue
        A(f"| `{name}` | local | {int(row['ok'])} | `{row['revert']}` | {row['writes']} | {row['logs']} | "
          f"`{row['return']}` |")
    A("")
    rebate = parse_rebate(result["probe_live"]["rebate"])
    A("")
    A("The local rows run on the saved prestate storage, so a value that lives in post-pin constructor "
      "state reads zero or NotOwner locally: `skm_builderRegistry` and the BuilderRegistry owner are of "
      "that kind, and the read-only probe table above is authoritative for them. The Exchange and "
      "Tokenomics selectors are exercised against the real delegated implementations.")
    A("")
    A("The rebate surface, from a local exact-runtime replay of the live Tokenomics: `activateRebate()` "
      "takes no argument, reverts `0x30cd7471` for a stranger and for the guardian multisig, and from the "
      "owner writes exactly one slot and emits one four-word event.")
    A("")
    A("| Tokenomics read | Before activateRebate | After activateRebate |")
    A("|---|---:|---:|")
    A(f"| slot 9 | {rebate.get('tk_slot9', {}).get('before')} | {rebate.get('tk_slot9', {}).get('after')} |")
    A(f"| getter 0x122b6689 | {rebate.get('tk_122b6689', {}).get('before')} | {rebate.get('tk_122b6689', {}).get('after')} |")
    A(f"| PAPER total supply | {rebate.get('tk_slot9', {}).get('supply_before')} | {rebate.get('tk_slot9', {}).get('supply_after')} |")
    A("")
    A("The PAPER supply is unchanged, no Tokenomics settlement path runs and no Exchange or Staking "
      "storage is written, so the rebate activation mints no token and credits no balance. The live "
      "getter `0x122b6689` is already nonzero on chain ("
      + str(probes.get("tk_122b6689")) + "), so the batch's rebate call has taken effect.")
    A("")
    A("## B8 - the builder surface")
    A("")
    A("Findings: BuilderRegistry `feeRate()` is 0.5% on the 1e18 scale; "
      "`setFeeRate` and `approveBuilder` succeed from the timelock owner and revert for the guardian "
      "multisig and a stranger, so the builder fee is owner-only. SessionKeyManager `setBuilderRegistry` "
      "is owner-only, and `builderRegistry()` returns the live registry `" + BUILDER_REGISTRY + "`. The "
      "added Exchange selector `0xf009ac03` takes an address and returns a bool; `builderFees(address)` "
      "reads zero for both stalled-sweep users; `claimBuilderFees(address)` succeeded from the owner and "
      "from a stranger at that zero balance and moved no storage and emitted no log. No builder was "
      "attached to any close in these replays, so whether a builder fee creates a credit the LP "
      "accounting did not pay for stays **plausible-unproven**; a real close carrying a builder and a "
      "nonzero `builderFees` balance would settle it. The local replay sets the Tokenomics owner word "
      "(slot 0, owner at bit 16) so the owner-guarded rows are exercised as the real owner.")
    A("")
    A("## B7 - Guardian H-02, M-02 and M-04 on the live implementations")
    A("")
    h02 = live["b7_h02_queued_win"]
    m04 = live["b7_m04_solvent_win"]
    m02b = live["b7_m02_liq_baseline"]
    m02q = live["b7_m02_liq_queue"]
    A("| Check | Live result | Pinned result |")
    A("|---|---|---|")
    A(f"| H-02 queued win Tokenomics debit | {h02['token_debit']} | {result['pinned']['rows']['b7_h02_queued_win']['token_debit']} |")
    A(f"| H-02 queued amount | {h02['queue_delta']} | {result['pinned']['rows']['b7_h02_queued_win']['queue_delta']} |")
    A(f"| M-04 solvent win Tokenomics debit | {m04['token_debit']} | {result['pinned']['rows']['b7_m04_solvent_win']['token_debit']} |")
    A(f"| M-04 fee split | {m04['staker_delta']} + {m04['dev_delta']} | same |")
    A(f"| M-02 liquidation, totalQueued 0: LP credit | {m02b['token_credit']} | {result['pinned']['rows']['b7_m02_liq_baseline']['token_credit']} |")
    A(f"| M-02 liquidation, totalQueued 0: staker | {m02b['staker_delta']} | same |")
    A(f"| M-02 liquidation, totalQueued 1: LP credit | {m02q['token_credit']} | {result['pinned']['rows']['b7_m02_liq_queue']['token_credit']} |")
    A(f"| M-02 liquidation, totalQueued 1: staker | {m02q['staker_delta']} | same |")
    A("")
    A("All three fixes hold on the live implementations with numbers identical to the pinned ones. "
      "H-02: a queued win debits Tokenomics by exactly the queued claim, so LP equity moves with the "
      "claim. M-04: a solvent win debits the gross adjusted win, fee included, and the fee is "
      "separately split to staker and developer. M-02 reproduces: with `totalQueued` zero the "
      "liquidation credits the margin less the 2% liquidation fee (split to staker and developer) and "
      "with `totalQueued` one wei it credits the full margin with the fee waived. The Exchange side "
      "bucket (slot 27) stays zero in both liquidation replays, so the side-bucket allocation "
      "REPORT.md measured in its archive replay is not reproduced here; the M-02 branch itself is "
      "decided, the side bucket is not.")
    A("")
    A("## Ledger")
    A("")
    A("| Id | Title | Invariant | Actor | Affected | Severity | Status |")
    A("|---|---|---|---|---|---|---|")
    for row in sorted(rows, key=lambda r: r["id"]):
        A(f"| {row['id']} | {row['title']} | {row['invariant']} | {row['actor']} | {row['affected']} | "
          f"{row['severity']} | {row['status']} |")
    A("")
    A("## Limits")
    A("")
    A("Every replay is a port-free Foundry execution of the exact live runtimes against the saved "
      "block-48,901,631 prestate storage, with the HyperCore BBO precompile mocked. Balance credits, "
      "queue columns and Tokenomics deltas are therefore local-scenario values built on pinned "
      "accounting, not current chain values; the current live figures quoted (treasury, "
      "lpBankrollAvailable, queueHarvestAvailable, fee rates, owner, keeper) are labelled read-only "
      "public-RPC probes. The public RPC ignores block parameters, so nothing here is a historical "
      "state read. No archive endpoint is configured, so a pre-pin incident-era fetch is not repeated. "
      "The OI-cap unit, the builder-fee plumbing on a real builder-carrying close, and the side-bucket "
      "allocation are the three open observations.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
