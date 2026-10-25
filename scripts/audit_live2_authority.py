#!/usr/bin/env python3
"""Authority, configuration and upgrade-route audit of the post-pin (contract set 2) Papertrade code.

Scope: the three implementations the 2026-10-21 governance batch installed behind the newest proxies
(Exchange `0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723`, SessionKeyManager
`0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946`, Tokenomics
`0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03`), the new `BuilderRegistry`
`0xfdc6550436dd75ce8a0b145f935b7d3a64f53248`, and the upgrade route that controls them.

Everything below rides on one of:
  * the saved set-2 runtime bytes under `artifacts/postpin_suite/runtime/`, SHA-256 checked here;
  * the saved live capture under `artifacts/postpin_suite/` (labelled with its head block);
  * a port-free exact-runtime Forge replay (`artifacts/live2_authority/replay.json`, `--replay`).

`python3 scripts/audit_live2_authority.py` re-checks every static claim offline and needs no RPC credential.
`--capture` refreshes the live reads and stores the raw JSON-RPC responses. `--replay` regenerates the
Forge replay on a machine with forge and solc. No transaction, no deploy, no disclosure.
"""

import argparse
import datetime
import importlib.util
import sys
import gzip
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
POSTPIN = ROOT / "artifacts" / "postpin_suite"
OUT = ROOT / "artifacts" / "live2_authority"
OUTPUT_JSON = ATLAS / "live2_authority.json"
OUTPUT_MD = ATLAS / "live2_authority.md"
CAPTURE_JSON = OUT / "live_capture_raw.json"
REPLAY_JSON = OUT / "replay.json"
REPLAY_SOURCE = OUT / "AuthorityLocal.t.sol"
RPC = "https://rpc.hyperliquid.xyz/evm"

IMPL_SLOT = "360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "b53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"

PIN_BLOCK = 48_902_346
SET2_EXCHANGE = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
SET2_SKM = "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946"
SET2_TOKENOMICS = "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03"
SET2_LIBRARY = "0x583d0bd818c991c5830fea93aef04e474b272459"
BUILDER_REGISTRY = "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248"
PIN_EXCHANGE_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN_SKM_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
PIN_TOKENOMICS_IMPL = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
PIN_LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"

# Saved-runtime registry: role -> (file, expected sha256 from suite_sets.json).
SET2_RUNTIMES = {
    "exchange_implementation_2": (SET2_EXCHANGE, "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723.hex",
                                  "fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268"),
    "session_key_manager_implementation_2": (SET2_SKM, "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946.hex",
                                             "7df05c33597c04820a314fae015aab01b5566aff53e9bded8446962cfd4ad2c9"),
    "tokenomics_implementation_2": (SET2_TOKENOMICS, "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03.hex",
                                    "56caf868c73dbc33b94725972fc101dbcec0fb7b017c4f2f9e8cda49516992e9"),
    "exchange_linked_library_2": (SET2_LIBRARY, "0x583d0bd818c991c5830fea93aef04e474b272459.hex",
                                  "ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440"),
    "builder_registry": (BUILDER_REGISTRY, "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248.hex",
                         "f459de55cb0463912417650fbca7e18109f3820551e4071234109e1e72801d2f"),
}
PINNED_RUNTIMES = {
    "exchange_implementation": (PIN_EXCHANGE_IMPL, "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee.hex"),
    "session_key_manager_implementation": (PIN_SKM_IMPL, "0x8a5069fe303e8f81e91825436e956d595032e558.hex"),
    "tokenomics_implementation": (PIN_TOKENOMICS_IMPL, "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f.hex"),
    "exchange_linked_library": (PIN_LIBRARY, "0xcd617f984158a4f5d287ddee0e8eb0fed204916d.hex"),
}

# Selector sets recovered from the saved bytes. These are asserted, not re-derived.
ADDED = {
    "exchange_implementation_2": ["0x69f9a5f0", "0x9d346583", "0xcbce7532", "0xd970fad5",
                                  "0xe6ac4a74", "0xf009ac03"],
    "session_key_manager_implementation_2": ["0xbd322efa", "0xd95208cd", "0xe737de13"],
    "tokenomics_implementation_2": ["0x122b6689", "0x456db972", "0x4ec7182e", "0x85eb2a08",
                                    "0xeedf4c43"],
    "exchange_linked_library_2": ["0x06c5308a", "0xb9370332"],
}
DROPPED = {
    "exchange_implementation_2": ["0x415f1240"],
    "session_key_manager_implementation_2": [],
    "tokenomics_implementation_2": [],
    "exchange_linked_library_2": ["0x82296364", "0xef1a27a9"],
}

# Per added selector: the caller guard, the storage the dispatched body touches, the events and the
# revert payloads observed at exact program counters. "guard" is what the Forge replay proved.
ADDED_FACTS = {
    ("exchange_implementation_2", "0xcbce7532"): dict(
        guard="none", abi=[], writes=[], events=[],
        note="returns slot 38 >> 160 (a 96-bit accumulator above devFeeRecipient)"),
    ("exchange_implementation_2", "0x9d346583"): dict(
        guard="none", abi=["address"], writes=[], events=[],
        note="returns the slot-39 mapping keccak256(abi.encode(addr, uint256(39)))"),
    ("exchange_implementation_2", "0xf009ac03"): dict(
        guard="none", abi=[], writes=[], events=[],
        note="returns (slot 8 >> 32) & 0xff != 0"),
    ("exchange_implementation_2", "0xe6ac4a74"): dict(
        guard="authorizedKeeper (slot 89 low 160 bits)", abi=["bool"], writes=["slot 8, byte above bits 0..31"],
        events=["0xd8f19a02... (unnamed topic)"], note="revert 0xda96f0b6 for every other caller, owner included"),
    ("exchange_implementation_2", "0x69f9a5f0"): dict(
        guard="none (self-claim)", abi=[], writes=["slot 39 own entry -> 0", "slot 38 high 96 bits -="],
        events=["BuilderFeesClaimed(address,uint256,uint256)"], note="debits the shared slot-38 accumulator"),
    ("exchange_implementation_2", "0xd970fad5"): dict(
        guard="owner (slot 0 bits 16..175, via the shared guard at 0x4500)", abi=["address", "address"],
        writes=["slot 39 entry of arg0 -> 0", "slot 39 entry of arg1 += arg0's amount"],
        events=["0xf764c3f6... (unnamed topic)"],
        note=("owner-only accrual reassignment between two addresses: builderFees(arg0) is moved into "
              "builderFees(arg1) and the shared slot-38 accumulator is not touched")),
    ("session_key_manager_implementation_2", "0xe737de13"): dict(
        guard="none", abi=[], writes=[], events=[], note="returns slot 8 low 160 bits"),
    ("session_key_manager_implementation_2", "0xbd322efa"): dict(
        guard="owner (slot 2 low 160 bits)", abi=["address"], writes=["slot 8 low 160 bits"],
        events=["BuilderRegistryUpdated(address)"], note=""),
    ("session_key_manager_implementation_2", "0xd95208cd"): dict(
        guard="none (the Exchange calls it as a staticcall)", abi=["address", "bytes32", "uint8", "bytes32", "bytes32"],
        writes=[], events=[],
        note=("not a passive getter: the set-2 Exchange calls it as a staticcall on every signed close with "
              "(user, digest, v, r, s) and the pinned SessionKeyManager does not dispatch it at all")),
    ("tokenomics_implementation_2", "0x122b6689"): dict(
        guard="none", abi=[], writes=[], events=[], note="returns slot 9 low 128 bits"),
    ("tokenomics_implementation_2", "0x456db972"): dict(
        guard="none", abi=[], writes=[], events=[], note="returns slot 9 bits 128..191"),
    ("tokenomics_implementation_2", "0x4ec7182e"): dict(
        guard="none", abi=[], writes=[], events=[], note="reads slot 9 and TIMESTAMP"),
    ("tokenomics_implementation_2", "0xeedf4c43"): dict(
        guard="none", abi=[], writes=[], events=[], note="has a revert branch in the zero state (not an access-control error)"),
    ("tokenomics_implementation_2", "0x85eb2a08"): dict(
        guard="owner (slot 0 bits 16..175)", abi=[], writes=["slot 9"], events=["0x302d310a... (unnamed topic)"],
        note="state-gated: 0x6e20dedb when the PAPER pointer is unset, 0xfc6b95ed when already active, then calls PAPER"),
    ("exchange_linked_library_2", "0x06c5308a"): dict(
        guard="undecided", abi=[], writes=[], events=["0xb2f6a0be... (unnamed topic)"],
        note="library entry; delegatecalled from the Exchange"),
    ("exchange_linked_library_2", "0xb9370332"): dict(
        guard="undecided", abi=[], writes=[], events=[], note="library entry; delegatecalled from the Exchange"),
}

# EIP-712 struct typehashes pushed as literal constants by the Exchange, hash-verified here.
TYPEHASHES = {
    "Close(address user,uint256[] positionIds,uint256 nonce,uint64 deadline)":
        "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13",
}
# Candidate names that must NOT be attached to their selector: asserted so no later prose
# revives them. These come from the signed-intents lane's independent name sweep.
REJECTED_NAMES = {
    "SweepSameBlock()": "0xd26ffacb",
    "SweepRateLimited()": "0xfefe83a0",
}
ERROR_SELECTORS = {
    "NotOwner()": "0x30cd7471",
    "ZeroAddress()": "0xd92e233d",
    "InvalidAddress()": "0xe6c4247b",
    "InvalidOwner()": "0x49e27cff",
    "NotSelf()": "0x29c3b7ee",
    "NotOwnerOrGuardian()": "0x2c49223e",
    "FeeRateTooHigh()": "0xe30ce51e",
    "RebateActive()": "0xfc6b95ed",
    "NotPauseAuthority()": "0x49199fb6",
    "SweepBelowMinimum()": "0x329c2b0f",
    "raw 0xda96f0b6 (no candidate signature hashes to it)": "0xda96f0b6",
    "Panic(uint256)": "0x4e487b71",
}
EVENT_TOPICS = {
    "OwnerUpdated(address)": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
    "GuardianUpdated(address)": "0x6bb7ff33e730289800c62ad882105a144a74010d2bdbb9a942544a3005ad55bf",
    "FeeRateUpdated(uint256)": "0x208f1b468d3d61f0f085e975bd9d04367c930d599642faad06695229f3eadcd8",
    "BuilderApproved(address)": "0xccb37c7a8718a6d39a5bfc3a91871e203c2d2f7cddb83cb8cbd12c50e74974ec",
    "BuilderRemoved(address)": "0xc5a4a43135540d5e0967677a1ed86bf147f7c0e7dd757a109f4cff74c945f92e",
    "BuilderFeesClaimed(address,uint256,uint256)": "0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15",
    "BuilderRegistryUpdated(address)": "0x8818669b8fb2aea1f49cabb856432f8bd536ace24e3564983488f5a001bc0cf9",
}
# Topics pushed as literal constants in the set-2 code that no candidate signature hashes to.
UNNAMED_TOPICS = {
    "exchange_new_flag_event": "0xd8f19a0212393b8c603ef0d47c77814e1dbfa1419aa70029ad7a857c18d6ee98",
    "exchange_owner_sweep_event": "0xf764c3f6c1c180f8fee84367cd0d9c7ab202e815d7071af2967eeef800c79380",
}
# BuilderRegistry event topics observed in its own constructor transaction.
REGISTRY_LOG_TOPICS = [
    "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
    "0x6bb7ff33e730289800c62ad882105a144a74010d2bdbb9a942544a3005ad55bf",
    "0x208f1b468d3d61f0f085e975bd9d04367c930d599642faad06695229f3eadcd8",
]

BUILDER_REGISTRY_SELECTORS = {
    "0x452a9320": "guardian()",
    "0x459770f6": "setFeeRate(uint64)",
    "0x54dc2a02": "approveBuilder(address)",
    "0x673448dd": "isApproved(address)",
    "0x8a0dac4a": "setGuardian(address)",
    "0x8da5cb5b": "owner()",
    "0x978bbdb9": "feeRate()",
    "0xd779e270": "feeRateOf(address)",
    "0xec969386": "removeBuilder(address)",
    "0xf2fde38b": "transferOwnership(address)",
}

# --------------------------------------------------------------------------- EVM linear disassembler

OPNAMES = {
    0x00: "STOP", 0x01: "ADD", 0x02: "MUL", 0x03: "SUB", 0x04: "DIV", 0x06: "MOD",
    0x0A: "EXP", 0x10: "LT", 0x11: "GT", 0x12: "SLT", 0x13: "SGT", 0x14: "EQ", 0x15: "ISZERO",
    0x16: "AND", 0x17: "OR", 0x18: "XOR", 0x19: "NOT", 0x1A: "BYTE", 0x1B: "SHL", 0x1C: "SHR",
    0x1D: "SAR", 0x20: "KECCAK256",
    0x30: "ADDRESS", 0x31: "BALANCE", 0x32: "ORIGIN", 0x33: "CALLER", 0x34: "CALLVALUE",
    0x35: "CALLDATALOAD", 0x36: "CALLDATASIZE", 0x37: "CALLDATACOPY", 0x38: "CODESIZE",
    0x39: "CODECOPY", 0x3A: "GASPRICE", 0x3B: "EXTCODESIZE", 0x3C: "EXTCODECOPY",
    0x3D: "RETURNDATASIZE", 0x3E: "RETURNDATACOPY", 0x3F: "EXTCODEHASH",
    0x40: "BLOCKHASH", 0x41: "COINBASE", 0x42: "TIMESTAMP", 0x43: "NUMBER", 0x44: "PREVRANDAO",
    0x45: "GASLIMIT", 0x46: "CHAINID", 0x47: "SELFBALANCE", 0x48: "BASEFEE",
    0x50: "POP", 0x51: "MLOAD", 0x52: "MSTORE", 0x53: "MSTORE8", 0x54: "SLOAD", 0x55: "SSTORE",
    0x56: "JUMP", 0x57: "JUMPI", 0x58: "PC", 0x59: "MSIZE", 0x5A: "GAS", 0x5B: "JUMPDEST",
    0x5C: "TLOAD", 0x5D: "TSTORE", 0x5E: "MCOPY",
    0x5F: "PUSH0",
    0x80: "DUP1", 0x81: "DUP2", 0x82: "DUP3", 0x83: "DUP4", 0x84: "DUP5", 0x85: "DUP6",
    0x86: "DUP7", 0x87: "DUP8", 0x88: "DUP9", 0x89: "DUP10", 0x8A: "DUP11", 0x8B: "DUP12",
    0x8C: "DUP13", 0x8D: "DUP14", 0x8E: "DUP15", 0x8F: "DUP16",
    0x90: "SWAP1", 0x91: "SWAP2", 0x92: "SWAP3", 0x93: "SWAP4", 0x94: "SWAP5", 0x95: "SWAP6",
    0x96: "SWAP7", 0x97: "SWAP8", 0x98: "SWAP9", 0x99: "SWAP10", 0x9A: "SWAP11", 0x9B: "SWAP12",
    0x9C: "SWAP13", 0x9D: "SWAP14", 0x9E: "SWAP15", 0x9F: "SWAP16",
    0xA0: "LOG0", 0xA1: "LOG1", 0xA2: "LOG2", 0xA3: "LOG3", 0xA4: "LOG4",
    0xF0: "CREATE", 0xF1: "CALL", 0xF2: "CALLCODE", 0xF3: "RETURN", 0xF4: "DELEGATECALL",
    0xF5: "CREATE2", 0xFA: "STATICCALL", 0xFD: "REVERT", 0xFE: "INVALID", 0xFF: "SELFDESTRUCT",
}
TERMINALS = {"STOP", "RETURN", "REVERT", "INVALID", "SELFDESTRUCT"}
EFFECT_OPS = {"SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL",
              "CREATE", "CREATE2", "LOG1", "LOG2", "LOG3", "LOG4", "SELFDESTRUCT"}


def disassemble(code):
    """Linear (non-following) EVM disassembly: pc -> (opname, operand)."""
    out = {}
    pc = 0
    n = len(code)
    while pc < n:
        op = code[pc]
        if 0x60 <= op <= 0x7F:
            size = op - 0x5F
            operand = code[pc + 1: pc + 1 + size]
            out[pc] = (f"PUSH{size}", operand)
            pc += 1 + size
        else:
            out[pc] = (OPNAMES.get(op, f"UNKNOWN_0x{op:02x}"), None)
            pc += 1
    return out


def dispatch_targets(dis, code):
    """PUSH4 <selector>, EQ, PUSH2 <dest>, JUMPI entries -> {selector: dest}."""
    pcs = sorted(dis)
    index = {pc: i for i, pc in enumerate(pcs)}
    targets = {}
    for pc, (op, operand) in dis.items():
        if not op.startswith("PUSH4") or operand is None:
            continue
        if len(operand) != 4:
            continue
        window = [dis[pcs[j]] for j in range(index[pc], min(index[pc] + 6, len(pcs)))]
        names = [w[0] for w in window]
        if "EQ" not in names:
            continue
        marker = names.index("EQ")
        for w in window[marker + 1:]:
            if w[0] == "PUSH2" and w[1] is not None:
                targets["0x" + operand.hex()] = int.from_bytes(w[1], "big")
                break
    return targets


def selector_set(dis):
    return set(dispatch_targets(dis, None))


def body_region(dis, dest, ceiling):
    return [(pc, dis[pc]) for pc in sorted(dis) if dest <= pc < ceiling]


def guard_slots(region):
    """Slot constants read directly before an SLOAD in a body, with CALLER proximity."""
    slots = []
    pending = None
    for i, (pc, (op, operand)) in enumerate(region):
        if op == "PUSH0":
            pending = 0
        elif op.startswith("PUSH") and operand is not None:
            pending = int.from_bytes(operand, "big")
        elif op == "SLOAD":
            if pending is not None and pending <= 0x100:
                window = [o for _, (o, _) in region[i:i + 8]]
                slots.append(dict(pc=hex(pc), slot=pending, caller_near="CALLER" in window))
            pending = None
        else:
            pending = None
    return slots


def jump_targets(region):
    """Destinations of JUMP/JUMPI = the last PUSH2 constant pushed before the jump."""
    targets = []
    for _, (op, operand) in region:
        if op == "PUSH2" and operand is not None:
            targets.append(int.from_bytes(operand, "big"))
    return sorted(set(targets))


def pushed_topics(region):
    return sorted({("0x" + o.hex()) for _, (op, o) in region
                   if op == "PUSH32" and o is not None})


def revert_payloads(region):
    """PUSH4 <v>; PUSH1 <shift>; SHL constructions -> the 4-byte selector actually reverted."""
    out = []
    items = list(region)
    for i, (pc, (op, operand)) in enumerate(items):
        if not op.startswith("PUSH4") or operand is None:
            continue
        for op2, o2 in [(o, v) for _, (o, v) in items[i + 1:i + 6]]:
            if op2 == "SHL":
                continue
        for _, (op2, o2) in items[i + 1:i + 6]:
            if op2 == "PUSH1" and o2 is not None:
                shift = int.from_bytes(o2, "big")
                value = int.from_bytes(operand, "big")
                word = (value << shift) % (1 << 256)
                out.append(dict(pc=hex(pc), pushed="0x" + operand.hex(), shift=shift,
                                payload="0x" + word.to_bytes(32, "big")[:4].hex()))
                break
    return out


# --------------------------------------------------------------------------- hashing

def keccak(data):
    if isinstance(data, str):
        data = data.encode()
    try:
        from Crypto.Hash import keccak as _k
    except ImportError:
        # No pycryptodome here: shell out to `cast keccak` over the exact bytes.
        raw = subprocess.run(["cast", "keccak", "0x" + data.hex()],
                             capture_output=True, text=True, check=True).stdout.strip()
        return raw
    h = _k.new(digest_bits=256)
    h.update(data)
    return "0x" + h.hexdigest()


def selector_of(signature):
    return keccak(signature)[:10]


def topic_of(signature):
    return keccak(signature)


# --------------------------------------------------------------------------- static checks

def load_runtime(path):
    text = pathlib.Path(path).read_text().strip()
    assert text.startswith("0x"), path
    return bytes.fromhex(text[2:])


def check_static():
    facts = {}
    for role, (address, filename, expected) in SET2_RUNTIMES.items():
        code = load_runtime(POSTPIN / "runtime" / filename)
        digest = hashlib.sha256(code).hexdigest()
        assert digest == expected, (role, digest, expected)
        facts[role] = dict(address=address, bytes=len(code), sha256=digest)
    for role, (address, filename) in PINNED_RUNTIMES.items():
        code = load_runtime(ATLAS / "runtime" / filename)
        facts[role] = dict(address=address, bytes=len(code),
                           sha256=hashlib.sha256(code).hexdigest())

    # selector diff
    diff = {}
    for role, (address, filename, expected) in SET2_RUNTIMES.items():
        new_code = load_runtime(POSTPIN / "runtime" / filename)
        if role == "builder_registry":
            diff[role] = dict(added=sorted(selector_set(disassemble(new_code))), dropped=[])
            continue
        pin_role = {"exchange_implementation_2": "exchange_implementation",
                    "session_key_manager_implementation_2": "session_key_manager_implementation",
                    "tokenomics_implementation_2": "tokenomics_implementation",
                    "exchange_linked_library_2": "exchange_linked_library"}[role]
        pin_code = load_runtime(ATLAS / "runtime" / PINNED_RUNTIMES[pin_role][1])
        added = sorted(selector_set(disassemble(new_code)) - selector_set(disassemble(pin_code)))
        dropped = sorted(selector_set(disassemble(pin_code)) - selector_set(disassemble(new_code)))
        assert added == sorted(ADDED[role]), (role, added)
        assert dropped == sorted(DROPPED[role]), (role, dropped)
        diff[role] = dict(added=added, dropped=dropped,
                          pinned_selectors=len(selector_set(disassemble(pin_code))),
                          set2_selectors=len(selector_set(disassemble(new_code))))
    assert sorted(selector_set(disassemble(load_runtime(POSTPIN / "runtime" / SET2_RUNTIMES["builder_registry"][1])))) \
        == sorted(BUILDER_REGISTRY_SELECTORS)

    # no implementation-slot writer in any set-2 runtime
    for role in ("exchange_implementation_2", "session_key_manager_implementation_2",
                 "tokenomics_implementation_2", "exchange_linked_library_2"):
        code = load_runtime(POSTPIN / "runtime" / SET2_RUNTIMES[role][1])
        assert bytes.fromhex(IMPL_SLOT) not in code, role
        assert bytes.fromhex(ADMIN_SLOT) not in code, role

    # the set-2 Exchange never dispatches the registry's fee-rate selectors
    ex2 = load_runtime(POSTPIN / "runtime" / SET2_RUNTIMES["exchange_implementation_2"][1])
    lib2 = load_runtime(POSTPIN / "runtime" / SET2_RUNTIMES["exchange_linked_library_2"][1])
    for sel in ("d779e270", "673448dd", "54dc2a02"):
        needle = bytes.fromhex(sel)
        assert needle not in ex2, sel
        assert needle not in lib2, sel
    assert bytes.fromhex(BUILDER_REGISTRY[2:]) not in ex2
    assert bytes.fromhex(BUILDER_REGISTRY[2:]) not in lib2

    # the slot-39 builder-fee idiom exists only in the set-2 Exchange
    pin_ex = load_runtime(ATLAS / "runtime" / PINNED_RUNTIMES["exchange_implementation"][1])
    assert pin_ex.count(bytes.fromhex("6027")) == 0
    assert ex2.count(bytes.fromhex("6027")) == 4
    assert bytes.fromhex("6027602052") in ex2

    # per-added-selector static facts
    per_selector = {}
    for role, selectors in ADDED.items():
        code = load_runtime(POSTPIN / "runtime" / SET2_RUNTIMES[role][1])
        dis = disassemble(code)
        targets = dispatch_targets(dis, code)
        entries = sorted(targets.values())
        for sel in selectors:
            dest = targets[sel]
            following = [t for t in entries if t > dest]
            ceiling = min(following) if following else max(dis) + 1
            region = body_region(dis, dest, ceiling)
            fact = ADDED_FACTS[(role, sel)]
            guard = guard_slots(region)
            payloads = [p["payload"] for p in revert_payloads(region)]
            topics = pushed_topics(region)
            nonpayable = any(op == "CALLVALUE" for _, (op, _) in region[:6])
            per_selector[role + ":" + sel] = dict(
                body_pc=hex(dest), body_instructions=len(region), nonpayable=nonpayable,
                caller_guard_slots=guard[:3], revert_payloads=payloads[:6],
                pushed_topics=topics[:6], jump_targets=jump_targets(region)[:8],
                note=fact["note"], guard=fact["guard"])
            if fact["guard"] == "none":
                assert not any(g["caller_near"] for g in guard), (role, sel, guard)
            if fact["guard"] == "owner (slot 0 bits 16..175)":
                assert any(g["slot"] == 0 for g in guard), (role, sel, guard)
            if fact["guard"].startswith("owner (slot 0 bits 16..175, via"):
                assert 0x4500 in jump_targets(region), (role, sel, jump_targets(region))
            if fact["guard"] == "authorizedKeeper (slot 89 low 160 bits)":
                assert any(g["slot"] == 89 for g in guard), (role, sel, guard)
            if fact["guard"] == "owner (slot 2 low 160 bits)":
                assert any(g["slot"] == 2 for g in guard), (role, sel, guard)
    return facts, diff, per_selector


def check_registry():
    code = load_runtime(POSTPIN / "runtime" / SET2_RUNTIMES["builder_registry"][1])
    dis = disassemble(code)
    assert set(dispatch_targets(dis, code)) == set(BUILDER_REGISTRY_SELECTORS)
    # setFeeRate carries the 1e16 cap constant (PUSH7 0x2386f26fc10000)
    assert bytes.fromhex("662386f26fc10000") in code
    cap = 0x2386F26FC10000
    assert cap == 10 ** 16
    # the fee-too-high payload is constructed as PUSH4 0x7186728f << 225
    assert bytes.fromhex("637186728f60e1") in code
    assert ((0x7186728F << 0xE1) % (1 << 256)).to_bytes(32, "big")[:4].hex() == "e30ce51e"
    # the not-owner-or-guardian payload is PUSH4 0x1624911f << 225
    assert bytes.fromhex("631624911f60e1") in code
    assert ((0x1624911F << 0xE1) % (1 << 256)).to_bytes(32, "big")[:4].hex() == "2c49223e"
    # the owner and zero-address payloads use shift 224, so their selectors are literal
    assert bytes.fromhex("6330cd747160e0") in code
    assert bytes.fromhex("63d92e233d60e0") in code
    # the address mask idiom (2^160 - 1) used by both owner and guardian guards
    assert bytes.fromhex("60a01b03") in code
    return dict(
        address=BUILDER_REGISTRY,
        selectors=BUILDER_REGISTRY_SELECTORS,
        storage_layout={
            "slot_0": "owner (low 160 bits)",
            "slot_1": "guardian (bits 0..159) + feeRate (bits 160..223)",
            "slot_2": "mapping(address => uint8) approved builders",
        },
        fee_rate_cap=cap,
        fee_rate_cap_hex="0x2386f26fc10000",
        owner_capabilities=["approveBuilder(address)", "removeBuilder(address)", "setFeeRate(uint64)",
                            "setGuardian(address)", "transferOwnership(address)"],
        guardian_capabilities=["removeBuilder(address)"],
        observed_owner=live_value("registry_owner"),
        observed_guardian=live_value("registry_guardian"),
        observed_fee_rate=live_value("registry_feeRate"),
        observed_fee_rate_of_keeper=live_value("registry_feeRateOf_keeper"),
    )


def decode_multisig_record(raw_hex):
    """Decode the transactions(uint256) return: (address,uint256,bytes,address,uint256,uint8)."""
    body = raw_hex[2:]
    words = [body[i:i + 64] for i in range(0, len(body), 64)]
    destination = "0x" + words[0][24:]
    value = int(words[1], 16)
    data_offset = int(words[2], 16)
    submitter = "0x" + words[3][24:]
    epoch = int(words[4], 16)
    status = int(words[5], 16)
    start = data_offset * 2
    length = int(body[start:start + 64], 16)
    data = body[start + 64:start + 64 + length * 2]
    return dict(destination=destination, value=value, submitter=submitter, epoch=epoch,
                status=status, data="0x" + data)


def decode_schedule(payload_hex):
    """Decode timelock schedule(address,uint256,bytes,bytes32) calldata."""
    args = payload_hex[2 + 8:]

    def word(index):
        return args[index * 64:(index + 1) * 64]

    target = "0x" + word(0)[24:]
    value = int(word(1), 16)
    data_offset = int(word(2), 16)
    predecessor = "0x" + word(3)
    start = data_offset // 32
    length = int(word(start), 16)
    inner = args[(start + 1) * 64:(start + 1) * 64 + length * 2]
    inner_selector = "0x" + inner[:8]
    inner_args = inner[8:]
    return dict(target=target, value=value, predecessor=predecessor,
                inner_selector=inner_selector, inner_data="0x" + inner,
                inner_words=[inner_args[j * 64:(j + 1) * 64] for j in range(4)])


def check_pending_upgrade():
    """The newest multisig record schedules a ProxyAdmin upgrade of a third SKM implementation."""
    data = live()["capture"]
    raw = data.get("multisig_transactions_11")
    if not raw:
        return dict(status="absent", note="the live capture has no multisig record 11")
    record = decode_multisig_record(raw)
    assert record["destination"].lower() == "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
    assert record["submitter"].lower() == "0xe9686c8e11d80c8d78736485fcb6b6d7f4d7692e"
    assert record["epoch"] == 1
    assert record["status"] == 1, record["status"]
    assert record["data"][:10] == "0xb0e58bc9"
    schedule = decode_schedule(record["data"])
    assert schedule["target"].lower() == "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
    assert schedule["value"] == 0
    assert schedule["inner_selector"] == "0x99a88ec4"          # ProxyAdmin.upgrade(address,address)
    inner_proxy = "0x" + schedule["inner_words"][0][24:]
    inner_impl = "0x" + schedule["inner_words"][1][24:]
    assert inner_proxy.lower() == "0x8326eb8896e358717f10502ec73ce8d28e37b108"
    assert inner_impl.lower() == "0x0a2db5c7614b714fd9ec12b29bff3b4f4c545d82"
    # the proxy has not moved yet
    assert data["proxy_slots"]["skm"]["implementation"].lower().endswith(
        "04b5ea4cdd8d6de4bd6e0ef3865266947f043946")
    code = data.get("pending_impl_code")
    if code:
        assert not isinstance(code, dict), code
        assert len(code) > 2
    return dict(record_index=11, status_value=record["status"],
                destination=record["destination"], submitter=record["submitter"],
                epoch=record["epoch"], payload=record["data"],
                schedule=schedule, inner_proxy=inner_proxy, inner_impl=inner_impl,
                operation_id=data.get("pending_upgrade_operation_id"),
                timelock_operation_word=data.get("pending_upgrade_timelock_word"),
                impl_code_bytes=(len(code) - 2) // 2 if code else None,
                proxy_implementation_now=data["proxy_slots"]["skm"]["implementation"])


# --------------------------------------------------------------------------- saved live capture

_LIVE = None


def live():
    global _LIVE
    if _LIVE is None:
        raw = {}
        if CAPTURE_JSON.exists():
            raw = json.loads(CAPTURE_JSON.read_text())
        saved = json.loads(gzip.open(POSTPIN / "live_latest.json.gz").read())
        _LIVE = dict(capture=raw, saved=saved)
    return _LIVE


def live_value(name):
    """Own capture first, then the saved post-pin probes."""
    saved_names = {
        "registry_owner": "builder_registry_owner",
        "registry_guardian": "builder_registry_guardian",
        "registry_feeRate": "builder_registry_fee_rate",
        "registry_feeRateOf_keeper": "builder_registry_fee_rate_of_keeper",
        "timelock_minDelay": "newest_timelock_min_delay",
        "session_key_manager_builderRegistry": "session_key_manager_builder_registry",
        "exchange_owner": "newest_exchange_owner",
        "exchange_authorizedKeeper": "pt01_added_0x9d346583_0x9c8599c32224d7d9956a7def18f7314162f77baf",
        "proxyadmin_owner": "newest_proxy_admin_owner",
        "multisig_count": "newest_multisig_count",
    }
    data = live()
    row = data["capture"].get("getters", {}).get(name)
    if isinstance(row, dict):
        row = row.get("result")
    if row is not None:
        return row
    return data["saved"]["probes"].get(saved_names.get(name, name), {}).get("result")


def check_saved_live():
    saved = live()["saved"]
    probes = saved["probes"]
    assert probes["newest_timelock_min_delay"]["result"].endswith("15180")  # 86,400 s
    assert probes["builder_registry_fee_rate"]["result"].endswith("11c37937e08000")  # 5e15 = 0.5 %
    assert probes["builder_registry_fee_rate_of_keeper"]["result"].endswith("00" * 24 + "00" * 8)
    assert probes["builder_registry_owner"]["result"].lower().endswith(
        "b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert probes["builder_registry_guardian"]["result"].lower().endswith(
        "696292762fd5ac3677a45edbe54eaece4194d1f6")
    assert probes["session_key_manager_builder_registry"]["result"].lower().endswith(
        BUILDER_REGISTRY[2:])
    assert probes["newest_multisig_count"]["result"].endswith("0b")
    assert probes["newest_exchange_owner"]["result"].lower().endswith(
        "b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert probes["newest_proxy_admin_owner"]["result"].lower().endswith(
        "b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    # the moved proxies point at the set-2 implementations
    slots = saved["proxy_slots_at_latest"]["newest"]
    assert slots["exchange_proxy"]["implementation"] == SET2_EXCHANGE
    assert slots["session_key_manager_proxy"]["implementation"] == SET2_SKM
    assert slots["tokenomics_proxy"]["implementation"] == SET2_TOKENOMICS
    # every newest proxy still points at ProxyAdmin
    for name, row in slots.items():
        assert row["admin"].lower() == "0xe79c91cc682f1bb401a9cab74c900470190f0f8f", name

    # governance log facts: no Upgraded log, the batch ran, the delay change executed
    logs = json.loads(gzip.open(POSTPIN / "governance_logs.json.gz").read())
    for name, entry in logs["log_sets"].items():
        if name.startswith("proxy_") or name.endswith("_exchange_proxy"):
            assert entry["logs"] == [], name
    up = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
    for name, entry in logs["log_sets"].items():
        assert up not in [row["topics"][0] for row in entry["logs"]], name
    tl = {row["topics"][0] for row in logs["log_sets"]["newest_timelock"]["logs"]}
    assert "0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd" in tl  # batch executed
    assert "0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464" in tl  # MinDelayUpdated
    assert "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b" in tl  # OwnerUpdated
    # the ProxyAdmin emitted only its own owner events, no upgrade event
    pa = logs["log_sets"]["newest_proxy_admin"]["logs"]
    assert len(pa) == 2
    assert all(row["topics"][0] == "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b"
               for row in pa)
    # the registry constructor emitted OwnerUpdated + GuardianUpdated + FeeRateUpdated
    br = logs["log_sets"]["builder_registry"]["logs"]
    assert [row["topics"][0] for row in br] == REGISTRY_LOG_TOPICS
    assert br[2]["data"].endswith("11c37937e08000")

    explorer = json.loads((POSTPIN / "explorer_facts.json").read_text())
    assert explorer["creation"][BUILDER_REGISTRY]["creator"] == "0x13cb7a200d081094d23ebf07f4d708410a9c488b"
    return dict(saved_head=saved["head"], saved_captured_at=saved["captured_at_utc"])


def check_own_capture():
    if not CAPTURE_JSON.exists():
        return dict(status="absent", note="run --capture to add the live reads")
    data = json.loads(CAPTURE_JSON.read_text())
    g = data["getters"]

    def res(name):
        row = g[name]["result"]
        assert not isinstance(row, dict), (name, row)
        return row.lower()

    assert res("exchange_owner").endswith("b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert res("exchange_authorizedKeeper").endswith("0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56")
    assert res("exchange_authorizedExecutor").endswith("233ff29b239abc1d7748605da9b205c3e008626e")
    assert res("exchange_pauseGuardian").endswith("696292762fd5ac3677a45edbe54eaece4194d1f6")
    assert res("exchange_sessionKeyManager").endswith("8326eb8896e358717f10502ec73ce8d28e37b108")
    assert res("skm_owner").endswith("b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert res("skm_builderRegistry").endswith(BUILDER_REGISTRY[2:])
    assert res("tokenomics_owner").endswith("b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert res("paper_owner").endswith("b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert res("paper_stakingContract").endswith("aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016")
    assert res("staking_owner").endswith("b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert res("registry_owner").endswith("b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert res("registry_guardian").endswith("696292762fd5ac3677a45edbe54eaece4194d1f6")
    assert res("registry_feeRate").endswith("11c37937e08000")
    assert res("timelock_owner").endswith("696292762fd5ac3677a45edbe54eaece4194d1f6")
    assert res("timelock_minDelay").endswith("15180")
    assert res("proxyadmin_owner").endswith("b915fa41e824d6aa31bb833ee81220c0f2c8ea0f")
    assert res("multisig_required").endswith("02")
    assert res("multisig_epoch").endswith("01")
    for name in ("multisig_signerOne", "multisig_signerTwo", "multisig_signerThree"):
        assert res(name).lower().endswith(("aa7577a7a27aa7fcf6d0ec481b87df3ad0f6a88e",
                                           "e9686c8e11d80c8d78736485fcb6b6d7f4d7692e",
                                           "9028f3b5b6b0d69e4e84ff555ade17114c3d1e72")), name
    for name, row in data["proxy_slots"].items():
        assert row["implementation"] is not None and row["admin"] is not None, name
    data = dict(data)
    data.pop("getters")
    return data


def check_replay():
    assert REPLAY_SOURCE.exists(), "artifacts/live2_authority/AuthorityLocal.t.sol is missing"
    source = REPLAY_SOURCE.read_text()
    if not REPLAY_JSON.exists():
        return dict(status="absent", note="run --replay on a machine with forge and solc")
    record = json.loads(REPLAY_JSON.read_text())
    assert record["source_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    declared = sorted(re.findall(r"function (test\w+)\(", source))
    assert record["test_names"] == declared, (record["test_names"], declared)
    assert record["passed_tests"] == declared, (record["passed_tests"], declared)
    assert record["forge_result"].endswith("passed, 0 failed")
    known = {entry[2] for entry in SET2_RUNTIMES.values()}
    for directory in (ATLAS / "runtime", POSTPIN / "runtime"):
        for path in directory.glob("*.hex"):
            known.add(hashlib.sha256(load_runtime(path)).hexdigest())
    for label, entry in record["runtime_hashes"].items():
        assert entry["sha256"] in known, (label, entry["sha256"])
    return record


# --------------------------------------------------------------------------- ledger

def ledger_rows(facts, diff, per_selector, registry):
    return [
        dict(
            id="L2A-01",
            title="Six selectors were added to the Exchange implementation, one dropped",
            angle="C1 new selectors on unaudited code",
            invariant="A5",
            actor="owner (timelock), authorizedKeeper, any caller",
            precondition="The set-2 Exchange implementation is behind the Exchange proxy (proved from the saved bytes and the batch payload).",
            trigger="Any call to the six added selectors.",
            impact="Two are new value-moving surfaces (0x69f9a5f0 claimBuilderFees, 0xd970fad5 owner-only accrual reassignment); one is a new non-owner setter (0xe6ac4a74, authorizedKeeper); three are getters.",
            affected="set2",
            severity="low",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=[f"artifacts/live2_authority/AuthorityLocal.t.sol",
                      "artifacts/live2_authority/replay.json",
                      "artifacts/postpin_suite/runtime/0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723.hex",
                      "ADDED exchange_implementation_2 = " + ",".join(diff["exchange_implementation_2"]["added"]),
                      "DROPPED = " + ",".join(diff["exchange_implementation_2"]["dropped"])],
            missing_observation="A close in which the slot-39 credit actually fires. A four-position set-2 close on the pinned "
                                 "prestate with the live slot-8 flag reproduced writes 12 Exchange slots "
                                 "including the fee accumulator at slot 26 but no slot-39 entry, and leaves "
                                 "slot 38 unchanged (artifacts/live2_authority/close_coupling.json).",
            citations=["atlas/block_48902346/suite_sets.md"],
        ),
        dict(
            id="L2A-02",
            title="0xe6ac4a74(bool) is a non-owner setter gated on authorizedKeeper, writing slot 8",
            angle="C1 new selectors on unaudited code",
            invariant="A5 + proposed A8 (role scope)",
            actor="whichever address holds Exchange slot 89 (authorizedKeeper)",
            precondition="Exchange slot 89 equals msg.sender; the batch set it to 0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56.",
            trigger="call 0xe6ac4a74(0|1) from the keeper",
            impact=("Flipped byte at slot 8 bits 32..40; instrumentCount (bits 0..31) is preserved (asserted), "
                    "so the write cannot corrupt the instrument counter. The flag is returned by 0xf009ac03() "
                    "and is read into the signed-close body's event-data buffer at 0x3001, but it does NOT gate "
                    "the close: with the flag cleared the same constructed set-2 close succeeds and writes an "
                    "identical 12-slot write set. No branch was found where it matters; open, liquidation and "
                    "front-end consumers were not tested."),
            affected="set2",
            severity="low",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["testExchangeKeeperGatedFlag (keeper allowed; owner and outsider both revert 0xda96f0b6)",
                      "testExchangeKeeperFlagEvent (topic 0xd8f19a02..., one word of data)",
                      "testExchangeAddedGettersAnyCaller (instrumentCount unchanged across the write)",
                      "close_coupling.json flag_byte_cleared arm: the close succeeds and writes the same 12 "
                      "slots as with the flag set"],
            missing_observation="Whether the flag gates the open, liquidation or settlement paths; the close "
                                "path is now tested and inert (artifacts/live2_authority/close_coupling.json, "
                                "flag_byte_cleared arm).",
            citations=["atlas/block_48902346/exchange_direct_getters.md"],
        ),
        dict(
            id="L2A-03",
            title="SessionKeyManager added three selectors; only the registry pointer setter writes state and it is owner-gated",
            angle="C1 new selectors on unaudited code",
            invariant="A5",
            actor="owner (timelock)",
            precondition="SessionKeyManager slot 2 holds the owner; the batch installed the set-2 implementation and then set slot 8.",
            trigger="0xbd322efa(address) from the owner; 0xe737de13() from anyone; 0xd95208cd is the staticcall entry the set-2 Exchange uses for every signed close (see row L2A-15).",
            impact="The registry pointer (slot 8) is owner-settable and readable; the wired value is the BuilderRegistry. No new non-owner setter.",
            affected="set2",
            severity="info",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["testSessionKeyManagerSetBuilderRegistryOwnerGate (outsider reverts 0x30cd7471, owner writes slot 8)",
                      "probe session_key_manager_builder_registry = " + str(live_value('session_key_manager_builderRegistry'))],
            missing_observation="0xd95208cd's return words are not decomposed; only its calldata shape (user, digest, v, r, s) and its staticcall use are established.",
            citations=["atlas/block_48902346/selector_gap_other.md"],
        ),
        dict(
            id="L2A-04",
            title="Tokenomics added five selectors; the only state changer is owner-gated and state-gated",
            angle="C1 new selectors on unaudited code",
            invariant="A5",
            actor="owner (timelock)",
            precondition="Tokenomics slot 0 bits 16..175 hold the owner; the rebate must be inactive and the PAPER pointer set.",
            trigger="0x85eb2a08 activateRebate()",
            impact="No new non-owner setter. The owner can activate a rebate path that then calls the configured PAPER token as minter; it refuses when the token is unset (0x6e20dedb) or the rebate is already active (0xfc6b95ed).",
            affected="set2",
            severity="info",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["testTokenomicsActivateRebateAuthority (outsider 0x30cd7471; owner reaches the PAPER call; 0x6e20dedb and 0xfc6b95ed both reproduced)",
                      "0x122b6689 and 0x456db972 read slot 9 low128 / bits128..191; 0xeedf4c43 has a revert branch in the zero state"],
            missing_observation="The economic effect of the activated rebate and the name of 0x6e20dedb.",
            citations=["atlas/block_48902346/tokenomics_pseudocode.md"],
        ),
        dict(
            id="L2A-05",
            title="The linked library changed two entries in each direction and the Exchange dropped liquidate(uint256)",
            angle="C1 new selectors on unaudited code",
            invariant="A5",
            actor="n/a (interface shape)",
            precondition="The set-2 Exchange links 0x583d0bd8... instead of the pinned 0xcd617f98....",
            trigger="n/a",
            impact="The new library adds 0x06c5308a and 0xb9370332 and drops 0x82296364 / 0xef1a27a9; the Exchange no longer dispatches 0x415f1240 (liquidate(uint256)), which the pinned implementation and both pinned variants do.",
            affected="set2",
            severity="info",
            status="confirmed_simulation",
            evidence_tier="bytecode-only static read",
            evidence=["selector diff from the saved set-2 and pinned library bytes",
                      "artifacts/postpin_suite/runtime/0x583d0bd818c991c5830fea93aef04e474b272459.hex"],
            missing_observation="Whether any live caller still sends 0x415f1240 (it would now fall through to the fallback).",
            citations=["atlas/block_48902346/exchange_library_pseudocode.md"],
        ),
        dict(
            id="L2A-06",
            title="BuilderRegistry authority: the owner controls everything except one guardian capability",
            angle="C2 BuilderRegistry",
            invariant="A5 + proposed A8",
            actor="owner (timelock), guardian (newest multisig), any caller",
            precondition="Owner = timelock 0xb915fa41... (slot 0); guardian = 0x696292... (slot 1 bits 0..159).",
            trigger="approveBuilder / removeBuilder / setFeeRate / setGuardian / transferOwnership",
            impact="approveBuilder, setFeeRate, setGuardian and transferOwnership are owner-only (outsider and guardian both revert NotOwner 0x30cd7471). removeBuilder accepts the owner OR the guardian (a third party gets 0x2c49223e NotOwnerOrGuardian). So the guardian can deny a builder its fee accrual but cannot add one or change the rate.",
            affected="set2",
            severity="low",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["testBuilderRegistryGuardianCapability (guardian allowed on removeBuilder, denied on the other four; outsider denied with 0x2c49223e)",
                      "testBuilderRegistryOwnerGate / testBuilderRegistryEvents / testBuilderRegistryZeroAddressBranches"],
            missing_observation="Whether removeBuilder by the guardian has any on-chain precedent (no registry log besides the constructor exists).",
            citations=["atlas/block_48902346/suite_sets.md"],
        ),
        dict(
            id="L2A-07",
            title="BuilderRegistry fee: 0.5 % live, hard-capped at 1 %, and only approved builders report it",
            angle="C2 BuilderRegistry",
            invariant="A5",
            actor="owner (timelock)",
            precondition="slot 1 packs guardian (bits 0..159) and feeRate (bits 160..223).",
            trigger="setFeeRate(uint64) / feeRate() / feeRateOf(address)",
            impact="The live rate is 5e15 raw = 0.5 % (the documented number). setFeeRate accepts exactly 1e16 (1 %) and reverts one unit above with FeeRateTooHigh 0xe30ce51e. feeRateOf returns the global rate only for an approved builder and zero for anyone else, so a fee cannot be attached to an unapproved address through the registry.",
            affected="set2",
            severity="info",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["testBuilderRegistryFeeCap (cap accepted, cap+1 reverts 0xe30ce51e, outsider reverts 0x30cd7471)",
                      "testBuilderRegistryOwnerGate (feeRateOf(approved)=5e15, feeRateOf(unapproved)=0)",
                      "saved probe builder_registry_fee_rate = " + str(live_value('registry_feeRate'))],
            missing_observation="Whether the Exchange ever reads feeRateOf: its runtime and library contain no such selector bytes.",
            citations=["https://docs.papertrade.xyz"],
        ),
        dict(
            id="L2A-08",
            title="claimBuilderFees is permissionless but strictly caller-scoped",
            angle="C2 BuilderRegistry",
            invariant="A1 + A5",
            actor="any address with a nonzero builderFees entry of its own",
            precondition="The set-2 Exchange maps builder fees at slot 39; the slot-39 idiom is absent from the "
                         "pinned implementation (0 occurrences of PUSH1 0x27), so the mechanism is new.",
            trigger="0x69f9a5f0 claimBuilderFees() zeroes keccak256(abi.encode(msg.sender, 39)) and debits the "
                    "shared slot-38 high 96 bits by that amount.",
            impact=("The claim is not access-controlled, but it can only touch the caller's own entry, so no "
                    "caller can take another builder's accrual: with entries 5e18 for A and 7e18 for B, A's "
                    "call pays exactly 5e18 and leaves B's entry intact, B's pays exactly 7e18, the shared "
                    "slot-38 counter falls by exactly the two amounts, and an address with no entry succeeds "
                    "and is paid zero. Cross-caller theft is therefore disproved; the fee is not a bearer "
                    "asset. An amount larger than the slot-38 counter reverts with a checked-arithmetic panic. The only "
                    "entry points that touch slot 39 in any driven shape are this one (caller key) and the "
                    "owner reassignment 0xd970fad5; the sweep family, the close and the open leave it alone."),
            affected="set2",
            severity="low",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["testExchangeClaimBuilderFeesIsPermissionlessSelfClaim (outsider pays out its own entry, "
                      "entry zeroed, slot-38 high 96 bits -= the amount, event 0x3416b71e..., overdraw panics "
                      "0x4e487b71, zero entry is a no-op success)",
                      "peer exact-runtime rows L2-D2-04 in atlas/block_48902346/live2_intents.json "
                      "(two seeded entries: each caller is paid only its own, the other survives)",
                      "peer exact-runtime rows L2-D1-06 and L2-D2-04 in atlas/block_48902346/live2_intents.json "
                      "(sweep family, close and open all leave the seeded slot-39 entries untouched)",
                      "static: pinned Exchange PUSH1 0x27 count = 0; set2 count = 4"],
            missing_observation="Where the paid amount lands after the linked-library call (the Exchange balance "
                                 "mapping at base 9 was unchanged in the replay).",
            citations=["atlas/block_48902346/live2_intents.json"],
        ),
        dict(
            id="L2A-09",
            title="The close's builder-fee credit keys on an unidentified memory word, and the close struct has no builder field",
            angle="C2 BuilderRegistry",
            invariant="A5",
            actor="a closer (the credit site is inside the signed-close body)",
            precondition=("The signed-close struct is Close(address user,uint256[] positionIds,uint256 nonce,"
                          "uint64 deadline): the CLOSE_TYPEHASH constant 0x9cc23a52... is byte-identical in the "
                          "pinned and the set-2 Exchange runtime and hash-matches that signature, so no builder "
                          "field is signed."),
            trigger="A close that accrues a fee reaches the slot-39 credit site at 0x32b6: it loads a word from "
                    "mload(args_base + 0x180), masks it to 160 bits, and does keccak256(., 39) -> SLOAD -> "
                    "checked add -> SSTORE.",
            impact=("The credit site is real in the set-2 bytes, but the source of the keyed word is not "
                    "identified: appending an unsigned 8th calldata word leaves the credited key and the "
                    "Exchange write set unchanged, and a six-element positionIds array does not make any "
                    "element the key. An empty or loss-free close writes nothing, so the block is only entered "
                    "when a fee exists: four driven entry points (0x01681a62 sweep with and without a pending request, "
                    "0xe0189108 requestSweep, 0x6d142da1 finalizeSweep) all left seeded slot-39 entries "
                    "untouched, so no non-fee-paying shape reaches the credit block, and my earlier lead that "
                    "the helper block belongs to entry 0x01681a62 is contradicted by that probe. Nothing here "
                    "shows that a third party can steer a builder fee, and nothing disproves it either."),
            affected="set2",
            severity="info",
            status="plausible_unproven",
            evidence_tier="bytecode-only static read",
            evidence=["static: PUSH1 0x27; PUSH1 0x20; MSTORE; KECCAK256; SLOAD; SSTORE at 0x32b6 inside body "
                      "0x2792e706, with the key loaded from memory at 0x180 + the argument index and masked to "
                      "160 bits at 0x32a6",
                      "CLOSE_TYPEHASH assertion in this script (constant present and hash-matched in both the "
                      "pinned and the set-2 runtime)",
                      "peer exact-runtime rows L2-D1-06 and L2-D2-04 in atlas/block_48902346/live2_intents.json "
                      "(unsigned trailing word accepted, credit key unchanged; sweep family and open leave "
                      "slot 39 untouched; fee-paying shapes not run)"],
            missing_observation="A fee-paying close traced on set 2, to name the memory word the credit keys on.",
            citations=["atlas/block_48902346/live2_intents.json", "audit_live2_intents.py"],
        ),
        dict(
            id="L2A-10",
            title="Live role inventory and blast radius",
            angle="C3 authority inventory on live code",
            invariant="A5 + proposed A8",
            actor="owner (timelock), pause guardian (multisig), authorizedExecutor, authorizedKeeper, marketKeeper, relayer, builder",
            precondition="Values read at the live head (latest, no archive endpoint).",
            trigger="n/a",
            impact="owner = timelock 0xb915fa41... for Exchange, SKM, Tokenomics, PAPER, Staking, ProxyAdmin and BuilderRegistry. pauseGuardian = the newest multisig, and it can pause but not resume (NotPauseAuthority 0x49199fb6). authorizedExecutor (slot 88) = the BatchExecutor proxy, which only relays signed intents. authorizedKeeper (slot 89) = the address the batch wired; it can flip the slot-8 flag. marketKeeper (slot 37) is a separate role. No role other than the owner can change pricing or pointers.",
            affected="both",
            severity="info",
            status="confirmed_live",
            evidence_tier="pinned read-only probe",
            evidence=["artifacts/live2_authority/live_capture_raw.json",
                      "testExchangePauseAuthority (guardian pause allowed, resume denied)",
                      "testExchangeOwnerSettersStillOwnerGated"],
            missing_observation="Whether the keeper or marketKeeper address is a contract with further privileges.",
            citations=["atlas/block_48902346/exchange_admin_setters.md",
                        "atlas/block_48902346/exchange_pause_behavior.json"],
        ),
        dict(
            id="L2A-11",
            title="Upgrade chain today: 2-of-3 multisig, 86,400 s timelock, timelock-owned ProxyAdmin",
            angle="C4 upgrade route",
            invariant="A5",
            actor="two of the three multisig signers",
            precondition="Multisig 0x69629276... (requiredConfirmations 2, epoch 1, signers 0xaa7577a7..., 0xe9686c8e..., 0x9028f3b5...) owns the timelock 0xb915fa41...; the timelock owns the ProxyAdmin 0xe79c91cc...; the ProxyAdmin is the EIP-1967 admin of all eight proxy addresses.",
            trigger="submitTransaction(scheduleBatch) -> confirmAndExecute -> wait minDelay -> executeBatch -> ProxyAdmin.upgrade(proxy, impl)",
            impact="The minimum delay is 86,400 s at the live head (the pin-era 604,800 s updateMinDelay operation executed at block 49,050,825), and the pin-era pending operation was cancelled at 49,079,600. A 12th multisig record exists at the current head where the saved capture recorded 11.",
            affected="both",
            severity="info",
            status="confirmed_live",
            evidence_tier="pinned read-only probe",
            evidence=["probe newest_timelock_min_delay = " + str(live_value('timelock_minDelay')),
                      "governance_logs newest_timelock: MinDelayUpdated 86,400 and OperationExecuted at block 49,050,825; OperationCancelled at 49,079,600",
                      "testUpgradeRoutesThroughTimelockOwnedProxyAdmin, testTimelockSelfGatedAndMultisigGated"],
            missing_observation="The payload of multisig record 11, if the live capture of it is unavailable.",
            citations=["atlas/block_48902346/multisig_pseudocode.md",
                        "atlas/block_48902346/timelock_pseudocode.md"],
        ),
        dict(
            id="L2A-12",
            title="A third SessionKeyManager implementation is staged through the timelock",
            angle="C4 upgrade route",
            invariant="A5",
            actor="two of the three multisig signers",
            precondition="The SKM proxy's EIP-1967 admin is the ProxyAdmin; the ProxyAdmin is owned by the timelock; the timelock delay is 86,400 s.",
            trigger="Multisig record 11 (submitter 0xe9686c8e..., epoch 1, status 1 = executed) calls the timelock's schedule(0xb0e58bc9) with target = the ProxyAdmin, value 0, data = 0x99a88ec4 + the SKM proxy + implementation 0x0a2db5c7614b714fd9ec12b29bff3b4f4c545d82 (4,550 bytes), predecessor 0x65a4ca13....",
            impact="Once the delay elapses, execute() can replace the SessionKeyManager implementation with unaudited 4,550-byte code behind the same proxy, with no proxy Upgraded log. At the capture head the proxy still points at the set-2 implementation 0x04b5ea4c..., so the swap has not happened yet.",
            affected="both",
            severity="medium",
            status="confirmed_live",
            evidence_tier="pinned read-only probe",
            evidence=["artifacts/live2_authority/live_capture_raw.json multisig_transactions_11 decoded "
                      "(destination=timelock, selector 0xb0e58bc9, inner 0x99a88ec4, impl 0x0a2db5c7614b714fd9ec12b29bff3b4f4c545d82, status 1)",
                      "proxy_slots.skm.implementation still 0x04b5ea4c... at the capture head",
                      "pending_impl_code is a non-empty contract (4550 bytes)",
                      "timelock storage keccak256(abi.encode(operationId, 2)) = 0x6adbdb27; the executed "
                      "pin-era operation 0xc616b8d5... reads 1 and the cancelled one 0x51142366... reads 0, "
                      "which confirms the mapping base and the keying"],
            missing_observation=("The schedule block, so the applied delay can be checked: the timelock's entry for "
                                 "this operation id holds 0x6adbdb27 (a ready time about 2.8 days after the "
                                 "capture head), which is much longer than the 86,400 s minimum delay read at "
                                 "the same head. The confirming signer and the reason for the change are also open."),
            citations=["atlas/block_48902346/timelock_pseudocode.md"],
        ),
        dict(
            id="L2A-13",
            title="0xd970fad5 is an owner-only accrual reassignment, not a claim and not a slot-38 debit",
            angle="C2 BuilderRegistry",
            invariant="A5 + proposed A8",
            actor="owner (timelock)",
            precondition="Exchange slot 39 is an address-keyed balance mapping; slot 0 bits 16..175 hold the owner.",
            trigger="0xd970fad5(a, b) from the owner.",
            impact=("The two words are two addresses, not an amount: builderFees(a) goes to zero and "
                    "builderFees(b) rises by a's amount, while the shared slot-38 accumulator is unchanged. "
                    "A non-owner reverts NotOwner 0x30cd7471 and neither entry moves. This is an owner "
                    "reassignment of a builder's accrued balance, so slot 39 is a per-address balance rather "
                    "than a per-call fee; it is also why the credited address for a close cannot be named "
                    "without a fee-paying close."),
            affected="set2",
            severity="low",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["testExchangeNewTwoArgSelectorIsOwnerGatedReassignment (5e18 on a and 7e18 on b: owner "
                      "call gives a -> 0 and b -> 12e18 with slot-38 high 96 bits still 100e18; outsider "
                      "reverts 0x30cd7471 and both entries keep their values)",
                      "peer exact-runtime row L2-D2-05 in atlas/block_48902346/live2_intents.json",
                      "static: the body reads builderFees(arg0) at 0x3eca and its owner guard is the shared "
                      "routine at 0x4500"],
            missing_observation="Whether any third party observation can ever reach this entry (it is "
                                 "owner-gated, and no owner call of it is in the saved history).",
            citations=["atlas/block_48902346/live2_intents.json"],
        ),
        dict(
            id="L2A-14",
            title="The sweep family does not reach the slot-39 block: an earlier lead is disproved",
            angle="C2 BuilderRegistry",
            invariant="A5",
            actor="n/a (entry-point census)",
            precondition="The 0x3af8/0x3eca/0x3eba helper block sits inside the dispatch region attributed to "
                         "entry 0x01681a62 by next-entry heuristics, which my own audit used as a lead.",
            trigger="Driving 0x01681a62 (sweep with and without a pending request), 0xe0189108 (requestSweep) "
                    "and 0x6d142da1 (finalizeSweep) with seeded slot-39 entries.",
            impact=("All four calls succeed and none reads or writes a seeded entry, so the sweep family does "
                    "not enter the slot-39 block and the region-attribution lead is wrong. Recorded as a "
                    "disproved lead so the census of slot-39 touchers stays honest: only claimBuilderFees "
                    "(caller key) and the owner entry 0xd970fad5 touch that mapping."),
            affected="set2",
            severity="none",
            status="disproved",
            evidence_tier="exact-runtime replay",
            evidence=["peer exact-runtime rows L2-D1-06 and L2-D2-04 in atlas/block_48902346/live2_intents.json "
                      "(four driven entry points, seeded entries untouched)",
                      "local: the region-attribution heuristic used no call-graph, so it could not have settled "
                      "this without a probe"],
            missing_observation="None for the disproof; the credited address for a close is still open (L2A-09).",
            citations=["atlas/block_48902346/live2_intents.json"],
        ),
        dict(
            id="L2A-15",
            title="The set-2 Exchange depends on a set-2-only SessionKeyManager entry, so one proxy cannot be upgraded alone",
            angle="C1 new selectors on unaudited code; C4 upgrade route",
            invariant="A5",
            actor="whoever installs a single implementation (the timelock, through the ProxyAdmin)",
            precondition="The set-2 close path (0x2792e706) makes a staticcall to SessionKeyManager selector "
                         "0xd95208cd before it touches a position, after a non-static call to 0xb002b9fa.",
            trigger="Install the set-2 Exchange implementation behind a SessionKeyManager that still dispatches "
                    "the pinned implementation, then attempt a signed close.",
            impact=("A direct signed close call reverts with empty revert data: the trace shows "
                    "0x6cd56616::2792e706 -> 0x8326eb88::b002b9fa (non-static, succeeds) then "
                    "0x8326eb88::d95208cd [staticcall] -> delegatecall into the pinned 0x8a5069fe -> Revert, "
                    "bubbled back out. The identical constructed close succeeds with the set-2 "
                    "SessionKeyManager and writes 12 Exchange slots. The failure mode through a batch is "
                    "different in appearance only: replaying the historical BatchExecutor batch verbatim, the "
                    "outer call succeeds under either SessionKeyManager, but with the pinned one the batch "
                    "writes 4 Exchange slots and both historical positions are STILL ACTIVE, while with the "
                    "set-2 one it writes 22 and closes both. So the batch wrapper masks the inner close "
                    "failure rather than the Exchange tolerating a failed verifier: nothing is closed and no "
                    "position state advances. The pair is only coherent together, so any single-proxy retrofit "
                    "breaks closes, and a recovery candidate that delegates to the pinned Exchange "
                    "implementation must be paired with the pinned SessionKeyManager. The hazard is not "
                    "limited to closes: a mixed pair also changes what counts as a successful deposit sweep "
                    "(row L2A-20)."),
            affected="both",
            severity="medium",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["artifacts/live2_authority/close_coupling.json: direct close with the pinned "
                      "SessionKeyManager reverts and writes 0 slots, with the set-2 one succeeds and writes 12; "
                      "the historical batch writes 4 slots with 2 positions still active under the pinned "
                      "SessionKeyManager and 22 slots with 0 active under the set-2 one",
                      "artifacts/live2_authority/CloseCouplingLocal.t.sol (regenerate with "
                      "python3 scripts/audit_live2_authority.py --close-coupling)",
                      "negative control inside the harness: the pinned-SessionKeyManager run must fail and "
                      "write nothing"],
            missing_observation="A close replayed on set-2-era state rather than the pinned prestate, to confirm "
                                "the dependency on chain state and not only on the pinned storage layout; and "
                                "whether any batch item other than the closes can reach the verifier call.",
            citations=["atlas/block_48902346/suite_sets.md",
                        "atlas/block_48902346/live2_intents.json"],
        ),
        dict(
            id="L2A-16",
            title="A mixed implementation pair also changes sweep success semantics, silently",
            angle="C4 upgrade route (silent failure-semantics change)",
            invariant="A5 + A7",
            actor="whoever installs one implementation without the other; a deposit proxy operator",
            precondition="A deposit proxy holds a dust pending sweep below the 10 USDC minimum; the Exchange "
                         "side carries a mixed pair.",
            trigger="A dust retry under the set-2 Exchange clears the pending word and returns success, while "
                    "the pinned implementation rewrites the word with the full observed balance and reverts "
                    "SweepBelowMinimum (0x329c2b0f, hash-verified here).",
            impact=("The coupling hazard is not confined to signed closes: a mixed pair also changes whether a "
                    "dust sweep retry succeeds or reverts, with no revert to tell the caller that the semantics "
                    "changed. The related credit question — the finalize credit follows the stored snapshot "
                    "rather than the delivered amount, so a Core-side fee or partial send becomes an Exchange "
                    "liability equal to the shortfall — is recorded by the signed-intents lane as "
                    "plausible_unproven and matters directly to the two live PT-01 pending sweeps."),
            affected="both",
            severity="medium",
            status="confirmed_simulation",
            evidence_tier="exact-runtime replay",
            evidence=["cross-referenced, not reproduced here: atlas/block_48902346/live2_intents.json rows "
                      "L2-D4-02 (exact-runtime differential on both implementations plus saved fork diffs: the "
                      "pinned dust retry reverts selector 849095439, the set-2 retry stores "
                      "0x24e160300 and clears) and L2-D5-01",
                      "independent check made here: 849095439 = 0x329c2b0f = keccak('SweepBelowMinimum()')[:10], "
                      "asserted in this script",
                      "row L2A-15 for the same silent-masking shape on the close path"],
            missing_observation="I did not re-run the sweep differential in my own harness; reproducing it there "
                                "(deposit proxy + Exchange prestate) and observing one fee-paying set-2 sweep "
                                "live would close both halves.",
            citations=["atlas/block_48902346/live2_intents.json"],
        ),
        dict(
            id="L2A-17",
            title="No timelock bypass was added: none of the set-2 runtimes writes the implementation slot",
            angle="C4 upgrade route",
            invariant="A5",
            actor="n/a",
            precondition="The ProxyAdmin is the only writer of the EIP-1967 implementation slot.",
            trigger="n/a",
            impact="None of the three new runtimes nor the new library contains the EIP-1967 implementation or admin slot constant, and no added selector writes it; the ProxyAdmin is owner-gated (the timelock). The new Exchange keeps transferOwnership owner-gated. Recorded as a disproved bypass with the control.",
            affected="set2",
            severity="none",
            status="disproved",
            evidence_tier="exact-runtime replay",
            evidence=["testNoImplementationSlotWriterInNewRuntimes",
                      "testUpgradeRoutesThroughTimelockOwnedProxyAdmin (outsider reverts 0x30cd7471; the timelock changes the slot)"],
            missing_observation="An initializer that could be re-entered with a fresh storage layout; the set-2 Exchange still exposes the 0xc0c53b8b stub, whose body was not decoded here.",
            citations=["atlas/block_48902346/proxy_admin_pseudocode.md"],
        ),
        dict(
            id="L2A-18",
            title="Monitoring gap: an implementation swap is invisible in logs",
            angle="C5 missing detection",
            invariant="A5 (detection)",
            actor="any chain observer",
            precondition="The ProxyAdmin writes the EIP-1967 slot with no event; the shared proxy runtime contains no LOG opcode and never emits Upgraded.",
            trigger="an upgrade (hypothetical for the 2026-10-21 batch, which was observed only via the multisig payload and the slot words)",
            impact="An implementation change cannot be detected by log indexing. The new proxies emitted zero Upgraded (0xbc7cd75a...) logs over blocks 49,063,457..49,255,838, and the ProxyAdmin emitted only its two OwnerUpdated events, both before the pin.",
            affected="both",
            severity="low",
            status="confirmed_live",
            evidence_tier="pinned read-only probe",
            evidence=["governance_logs: every proxy_* set has 0 logs; newest_proxy_admin has 2, both OwnerUpdated",
                      "static: no LOG opcode in the 925-byte shared proxy runtime"],
            missing_observation="None for the gap itself; a slot-word poll is the cheap check.",
            citations=["atlas/block_48902346/shared_proxy_pseudocode.md"],
        ),
        dict(
            id="L2A-19",
            title="Cheap detection: poll the implementation slot, do not rely on events",
            angle="C5 missing detection",
            invariant="A5 (detection)",
            actor="any chain observer",
            precondition="The RPC serves eth_getStorageAt at latest.",
            trigger="periodic read of IMPL_SLOT for each proxy (or implementation() from the admin)",
            impact="One storage read per proxy catches an implementation swap within one poll interval; comparing against a stored expected hash also catches a same-address code change.",
            affected="both",
            severity="info",
            status="confirmed_live",
            evidence_tier="pinned read-only probe",
            evidence=["artifacts/live2_authority/live_capture_raw.json proxy_slots",
                      "artifacts/postpin_suite/live_latest.json.gz proxy_slots_at_latest"],
            missing_observation="None.",
            citations=[],
        ),
        dict(
            id="L2A-20",
            title="PAPER and Staking privilege: all admin pointers are owner-only and no owner route redirects assets",
            angle="C6 PAPER and Staking privilege",
            invariant="A1 + A5",
            actor="owner (timelock)",
            precondition="PAPER owner slot 3, minter slot 4, autoApprovedSpender slot 5, stakingContract slot 9; Staking owner slot 15, packed executor slot 16.",
            trigger="setMinter / setStakingContract / setAutoApprovedSpender / transferOwnership on PAPER; setAuthorizedExecutor / transferOwnership on Staking",
            impact="Every one of these is owner-only (outsider reverts NotOwner 0x30cd7471) and the owner is the timelock, so no unprivileged path changes the transfer-eligibility slot or the staking pointers. The Staking owner's only lever is the authorized executor, which relays per-user signed intents, so it cannot move a user's funds without that user's signature.",
            affected="both",
            severity="none",
            status="disproved",
            evidence_tier="exact-runtime replay",
            evidence=["testPaperAdminOwnerGate", "testStakingAdminOwnerGate",
                      "probe paper_stakingContract = " + str(live_value('paper_stakingContract'))],
            missing_observation="Whether zeroing the PAPER staking pointer (owner-settable) can brick transfers; the pinned notes say a zero pointer still restricts transfers.",
            citations=["atlas/block_48902346/paper_token_pseudocode.md",
                        "atlas/block_48902346/staking_admin.md"],
        ),
    ]


# --------------------------------------------------------------------------- outputs

STATUS_ORDER = ["confirmed_live", "confirmed_simulation", "plausible_unproven", "disproved", "blocked"]


def build_md(ledger):
    counts = {}
    for row in ledger["findings"]:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    lines = []
    lines.append("# Authority, configuration and upgrade route on the live Papertrade code")
    lines.append("")
    lines.append("Generated by [`audit_live2_authority.py`](../../scripts/audit_live2_authority.py) from the saved "
                 "set-2 runtime bytes under `artifacts/postpin_suite/runtime/`, the saved live capture under "
                 "`artifacts/postpin_suite/`, and the port-free Forge replay at "
                 "`artifacts/live2_authority/replay.json`. The pinned audit is at block 48,902,346; the live "
                 "code is contract set 2, installed by the 2026-10-21 governance batch. `python3 "
                 "audit_live2_authority.py` re-checks every static claim offline and needs no RPC credential.")
    lines.append("")
    lines.append("Every row below states which implementation it applies to: `set2` is code the batch added "
                 "and is therefore unaudited by the pinned pass; `both` is behaviour that holds on the pinned "
                 "implementation too; `pinned` would be pinned-only (there is no such row here).")
    lines.append("")
    lines.append("| Status | Rows |")
    lines.append("|---|---:|")
    for status in STATUS_ORDER:
        if status in counts:
            lines.append(f"| `{status}` | {counts[status]} |")
    lines.append("")
    lines.append("## Added selectors on the unaudited set-2 code (C1)")
    lines.append("")
    lines.append("| Runtime | Added | Dropped |")
    lines.append("|---|---|---|")
    for role in ("exchange_implementation_2", "session_key_manager_implementation_2",
                 "tokenomics_implementation_2", "exchange_linked_library_2"):
        d = ledger["selector_diff"][role]
        lines.append(f"| `{role}` | {', '.join('`'+s+'`' for s in d['added'])} | "
                     f"{', '.join('`'+s+'`' for s in d['dropped']) or '-'} |")
    lines.append("")
    lines.append("| Runtime:selector | Name (public-registry candidate) | ABI | Caller guard (proved by replay) | Writes | Events |")
    lines.append("|---|---|---|---|---|---|")
    name_by = {
        "exchange_implementation_2:0x69f9a5f0": "`claimBuilderFees()` (hash-matched)",
        "exchange_implementation_2:0x9d346583": "`builderFees(address)` (hash-matched)",
        "exchange_implementation_2:0xcbce7532": "undefined (slot 38 >> 160 getter)",
        "exchange_implementation_2:0xd970fad5": "undefined (address,address)",
        "exchange_implementation_2:0xe6ac4a74": "undefined (bool)",
        "exchange_implementation_2:0xf009ac03": "undefined ()",
        "session_key_manager_implementation_2:0xbd322efa": "`setBuilderRegistry(address)` (hash-matched)",
        "session_key_manager_implementation_2:0xd95208cd": "undefined",
        "session_key_manager_implementation_2:0xe737de13": "`builderRegistry()` (hash-matched)",
        "tokenomics_implementation_2:0x122b6689": "undefined (slot 9 low 128)",
        "tokenomics_implementation_2:0x456db972": "`insolventSince()` (hash-matched)",
        "tokenomics_implementation_2:0x4ec7182e": "undefined (slot 9 + TIMESTAMP)",
        "tokenomics_implementation_2:0x85eb2a08": "`activateRebate()` (hash-matched)",
        "tokenomics_implementation_2:0xeedf4c43": "undefined",
        "exchange_linked_library_2:0x06c5308a": "undefined (library entry)",
        "exchange_linked_library_2:0xb9370332": "undefined (library entry)",
    }
    for key, row in ledger["added_selector_facts"].items():
        abi = row.get("abi", [])
        abi_text = f"{len(abi)} word(s)" if abi else "none"
        lines.append(f"| `{key}` | {name_by.get(key, '')} | {abi_text} | "
                     f"{row['guard']} | {', '.join(row['writes']) or '-'} | "
                     f"{', '.join(row['events']) or '-'} |")
    lines.append("")
    lines.append("`0xe6ac4a74` is the only added selector with a non-owner guard: it is gated on "
                 "`authorizedKeeper` (Exchange slot 89, set by the batch to "
                 "`0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56`). The owner and an unprivileged caller both "
                 "revert `0xda96f0b6` on it.")
    lines.append("")
    lines.append("### The two proxies are coupled: the set-2 Exchange needs the set-2 SessionKeyManager")
    lines.append("")
    lines.append("The set-2 close path calls `SessionKeyManager.0xd95208cd` as a staticcall on every signed "
                 "close (after a non-static `0xb002b9fa`), and the pinned SessionKeyManager does not dispatch "
                 "that selector at all. A direct close then reverts with empty data; the same close inside a "
                 "BatchExecutor batch fails silently, because the outer call still succeeds. Replaying the "
                 "historical batch verbatim makes the difference visible:")
    lines.append("")
    lines.append("| Run | Outer call | Exchange write slots | Historical positions still active |")
    lines.append("|---|---|---:|---:|")
    lines.append("| direct close, pinned SessionKeyManager | reverts (empty data) | 0 | n/a |")
    lines.append("| direct close, set-2 SessionKeyManager | succeeds | 12 | n/a |")
    lines.append("| historical batch, pinned SessionKeyManager | succeeds | 4 | 2 of 2 |")
    lines.append("| historical batch, set-2 SessionKeyManager | succeeds | 22 | 0 of 2 |")
    lines.append("| direct close, set-2 SessionKeyManager, slot-8 flag cleared | succeeds | 12 (identical set) | n/a |")
    lines.append("")
    lines.append("So the wrapper masks the inner failure rather than the Exchange tolerating a failed "
                 "verifier: no position is closed. Reproduce with `python3 scripts/audit_live2_authority.py "
                 "--close-coupling` (five arms, each asserted, including the pinned-SessionKeyManager negative "
                 "control); see `artifacts/live2_authority/close_coupling.json` and row `L2A-15`.")
    lines.append("")
    lines.append("The hazard is not confined to closes: the signed-intents lane's differential shows the same "
                 "silent-success shape on the deposit-sweep retry branch, where the set-2 implementation clears "
                 "a dust pending word and returns success while the pinned one reverts "
                 "`SweepBelowMinimum()` `0x329c2b0f` (cross-referenced in row `L2A-16`). That matters directly "
                 "to the two live PT-01 pending sweeps.")
    lines.append("")
    lines.append("## Live role inventory at the capture head (C3)")
    lines.append("")
    own = ledger.get("own_capture") or {}
    head = own.get("head") or {}
    lines.append(f"Head block {head.get('block')} (timestamp {head.get('timestamp')}), captured "
                 f"{own.get('captured_at_utc')}. These are `latest` reads, not pinned state.")
    lines.append("")
    lines.append("| Role | Contract | Value |")
    lines.append("|---|---|---|")
    for name, contract, key in [
        ("owner", "Exchange / SKM / Tokenomics / PAPER / Staking / BuilderRegistry / ProxyAdmin", "exchange_owner"),
        ("pauseGuardian", "Exchange", "exchange_pauseGuardian"),
        ("tradingPaused", "Exchange", "exchange_tradingPaused"),
        ("authorizedExecutor (slot 88)", "Exchange", "exchange_authorizedExecutor"),
        ("authorizedKeeper (slot 89)", "Exchange", "exchange_authorizedKeeper"),
        ("marketKeeper (slot 37)", "Exchange", "exchange_marketKeeper"),
        ("sessionKeyManager (slot 29)", "Exchange", "exchange_sessionKeyManager"),
        ("instrumentCount", "Exchange", "exchange_instrumentCount"),
        ("new slot-8 flag getter", "Exchange", "exchange_newFlagGet"),
        ("skm owner", "SessionKeyManager", "skm_owner"),
        ("builderRegistry (slot 8)", "SessionKeyManager", "skm_builderRegistry"),
        ("tokenomics owner", "Tokenomics", "tokenomics_owner"),
        ("tokenomics slot-9 low128", "Tokenomics", "tokenomics_rebateLow128"),
        ("insolventSince", "Tokenomics", "tokenomics_insolventSince"),
        ("paper owner / minter", "PAPER", "paper_minter"),
        ("autoApprovedSpender (slot 5)", "PAPER", "paper_autoApprovedSpender"),
        ("stakingContract (slot 9)", "PAPER", "paper_stakingContract"),
        ("staking owner", "Staking", "staking_owner"),
        ("registry owner / guardian", "BuilderRegistry", "registry_guardian"),
        ("registry feeRate", "BuilderRegistry", "registry_feeRate"),
        ("timelock owner / minDelay", "Timelock", "timelock_minDelay"),
        ("proxyAdmin owner", "ProxyAdmin", "proxyadmin_owner"),
        ("multisig required / count / epoch", "Multisig", "multisig_epoch"),
    ]:
        value = live_value(key)
        lines.append(f"| {name} | {contract} | `{value}` |")
    lines.append("")
    lines.append("Signers: `" + str(live_value("multisig_signerOne")) + "`, `"
                 + str(live_value("multisig_signerTwo")) + "`, `" + str(live_value("multisig_signerThree"))
                 + "`.")
    lines.append("")
    lines.append("## BuilderRegistry (C2)")
    lines.append("")
    reg = ledger["builder_registry"]
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| address | `{reg['address']}` |")
    lines.append(f"| owner() | `{reg['observed_owner']}` (the timelock) |")
    lines.append(f"| guardian() | `{reg['observed_guardian']}` (the newest multisig) |")
    lines.append(f"| feeRate() | `{reg['observed_fee_rate']}` = 5e15 raw = 0.5 % |")
    lines.append(f"| feeRate cap | `{reg['fee_rate_cap_hex']}` = 1e16 raw = 1 % (one unit above reverts `FeeRateTooHigh()` `0xe30ce51e`) |")
    lines.append(f"| feeRateOf(keeper) | `{reg['observed_fee_rate_of_keeper']}` (zero: not an approved builder) |")
    lines.append("")
    lines.append("| Entry | Owner | Guardian | Third party |")
    lines.append("|---|---|---|---|")
    lines.append("| `approveBuilder(address)` | allowed | `NotOwner()` `0x30cd7471` | `NotOwner()` |")
    lines.append("| `removeBuilder(address)` | allowed | **allowed** | `NotOwnerOrGuardian()` `0x2c49223e` |")
    lines.append("| `setFeeRate(uint64)` | allowed (<= 1 %) | `NotOwner()` | `NotOwner()` |")
    lines.append("| `setGuardian(address)` | allowed | `NotOwner()` | `NotOwner()` |")
    lines.append("| `transferOwnership(address)` | allowed | `NotOwner()` | `NotOwner()` |")
    lines.append("")
    lines.append("Storage: slot 0 owner; slot 1 packs guardian in bits 0..159 and feeRate in bits 160..223; "
                 "slot 2 is the `approved` mapping. The constructor emitted `OwnerUpdated`, "
                 "`GuardianUpdated` and `FeeRateUpdated(uint256)` (`0x208f1b46...`) in one transaction.")
    lines.append("")
    lines.append("### Who can attach a builder fee, and who can take one")
    lines.append("")
    lines.append("* Through the registry, a fee cannot be turned on for an address by a third party: "
                 "`approveBuilder` is owner-only and `feeRateOf` returns zero for anything unapproved.")
    lines.append("* On the Exchange the close credits its slot-39 mapping at a site that keys on a word loaded "
                 "from `mload(args_base + 0x180)`; the source of that word is not identified (row `L2A-09`), "
                 "and the signed close struct carries no builder field (its `CLOSE_TYPEHASH` `0x9cc23a52...` "
                 "is byte-identical to the pinned constant and hash-matches "
                 "`Close(address user,uint256[] positionIds,uint256 nonce,uint64 deadline)`).")
    lines.append("* `claimBuilderFees()` is callable by anyone, but it is strictly caller-scoped: it pays the "
                 "caller's own entry and leaves every other entry intact, so a builder's accrual cannot be "
                 "taken by another address (row `L2A-08`, disproved sub-claim).")
    lines.append("* `0xd970fad5(a, b)` is the owner-only other half: it reassigns the accrual, moving "
                 "`builderFees(a)` into `builderFees(b)` and leaving the shared slot-38 accumulator untouched, "
                 "which shows slot 39 is an address-keyed balance (row `L2A-13`).")
    lines.append("* Census of slot-39 touchers: only `claimBuilderFees` (its own caller key) and the owner "
                 "reassignment. The sweep family does not reach that block — an earlier region-attribution "
                 "lead of mine was disproved, and the row records it (row `L2A-14`).")
    lines.append("")
    lines.append("## Upgrade route today (C4)")
    lines.append("")
    lines.append("```text")
    lines.append("signer A: multisig.submitTransaction(timelock, 0, scheduleBatch(...))        // record N")
    lines.append("signer B: multisig.confirmAndExecute(N, transactionHash(N))                 // 2 of 3 required")
    lines.append("wait:     timelock.minDelay() = 86,400 s (live; 604,800 s at the pin)")
    lines.append("signer : multisig.submitTransaction(timelock, 0, executeBatch(...)) + confirm")
    lines.append("          -> timelock calls ProxyAdmin.upgrade(proxy, implementation)")
    lines.append("          -> ProxyAdmin (owner = timelock) calls proxy.upgradeToAndCall(impl, \"\")")
    lines.append("          -> EIP-1967 implementation slot written, no event emitted")
    lines.append("```")
    lines.append("")
    lines.append("* Multisig `0x696292762fd5ac3677a45edbe54eaece4194d1f6`: signers "
                 "`0xaa7577a7a27aa7fcf6d0ec481b87df3ad0f6a88e`, "
                 "`0xe9686c8e11d80c8d78736485fcb6b6d7f4d7692e`, "
                 "`0x9028f3b5b6b0d69e4e84ff555ade17114c3d1e72`; `requiredConfirmations()` = 2; epoch 1.")
    lines.append("* Timelock `0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f`: owner = the multisig, "
                 "`minDelay()` = 86,400; `updateMinDelay` and `transferOwnership` are self-calls only "
                 "(`NotSelf()` `0x29c3b7ee` for the owner).")
    lines.append("* ProxyAdmin `0xe79c91cc682f1bb401a9cab74c900470190f0f8f`: owner = the timelock, "
                 "the EIP-1967 admin of all eight proxy addresses.")
    lines.append("* Both pin-era pending operations are resolved: the `updateMinDelay(86,400)` operation "
                 "executed at block 49,050,825 and the stale Tokenomics mint-parameter operation was "
                 "cancelled at 49,079,600.")
    lines.append("")
    pending = ledger.get("pending_upgrade") or {}
    schedule = pending.get("schedule") or {}
    lines.append("### The route is in use right now: a third SessionKeyManager implementation is staged")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| multisig record | index 11, status {pending.get('status_value')} (1 = executed), epoch "
                 f"{pending.get('epoch')}, submitter `{pending.get('submitter')}` |")
    lines.append(f"| outer call | `{pending.get('destination')}` selector `0xb0e58bc9` "
                 "(timelock `schedule(address,uint256,bytes,bytes32)`) |")
    lines.append(f"| scheduled target | ProxyAdmin `{schedule.get('target')}`, value {schedule.get('value')} |")
    lines.append(f"| inner call | `{schedule.get('inner_selector')}` (ProxyAdmin `upgrade(address,address)`) "
                 f"with proxy `{pending.get('inner_proxy')}` and implementation `{pending.get('inner_impl')}` |")
    lines.append(f"| implementation code | {pending.get('impl_code_bytes')} bytes (a third, unaudited "
                 "SessionKeyManager implementation) |")
    lines.append(f"| predecessor | `{schedule.get('predecessor')}` |")
    lines.append(f"| operation id | `{pending.get('operation_id')}` |")
    lines.append(f"| proxy implementation now | `{pending.get('proxy_implementation_now')}` (unchanged) |")
    lines.append("")
    lines.append(f"| timelock entry for the operation id | `{pending.get('timelock_operation_word')}` "
                 "(the word at `keccak256(abi.encode(operationId, 2))`; the executed pin-era operation reads 1 "
                 "and the cancelled one reads 0, which confirms the keying) |")
    lines.append("")
    lines.append("So the concrete chain is already being exercised: one signer submitted the schedule call "
                 "and a second confirmation executed it, and the timelock now holds a scheduled ProxyAdmin "
                 "upgrade that any second signer can execute once the 86,400 s delay has elapsed. Because "
                 "neither the ProxyAdmin nor the proxy emits an event, the only on-chain signal is the "
                 "timelock's own `OperationScheduled` log and the multisig record.")
    lines.append("")
    lines.append("## Monitoring gap (C5)")
    lines.append("")
    lines.append("An implementation swap writes the EIP-1967 slot with no event: the ProxyAdmin emits no "
                 "upgrade event, the 925-byte shared proxy runtime contains no `LOG` opcode, and all eight "
                 "proxy addresses returned zero `Upgraded` (`0xbc7cd75a...`) logs over blocks "
                 "49,063,457..49,255,838. An observer cannot detect the swap from logs. The cheap check is "
                 "one `eth_getStorageAt(proxy, 0x360894a1...)` per proxy per poll, compared against the "
                 "expected implementation, plus a code-hash comparison to catch a same-address change. Both "
                 "checks are already implemented as `proxy_slots` in the capture file.")
    lines.append("")
    lines.append("## Findings ledger")
    lines.append("")
    lines.append("| ID | Title | Invariant | Actor | Affected | Severity | Status | Evidence tier |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in ledger["findings"]:
        lines.append(f"| `{row['id']}` | {row['title']} | {row['invariant']} | {row['actor']} | "
                     f"`{row['affected']}` | {row['severity']} | `{row['status']}` | {row['evidence_tier']} |")
    lines.append("")
    lines.append("## Preconditions and missing observations per row")
    lines.append("")
    for row in ledger["findings"]:
        lines.append(f"### `{row['id']}` {row['title']}")
        lines.append("")
        lines.append(f"- Angle: {row['angle']}")
        lines.append(f"- Precondition: {row['precondition']}")
        lines.append(f"- Trigger: {row['trigger']}")
        lines.append(f"- Impact: {row['impact']}")
        lines.append(f"- Evidence: {'; '.join(row['evidence'])}")
        lines.append(f"- Missing observation: {row['missing_observation']}")
        if row["citations"]:
            lines.append(f"- Citations: {', '.join('`'+c+'`' for c in row['citations'])}")
        lines.append("")
    lines.append("## Reproduce")
    lines.append("")
    lines.append("```sh")
    lines.append("python3 scripts/audit_live2_authority.py            # offline static + saved-capture checks")
    lines.append("python3 scripts/audit_live2_authority.py --replay   # regenerate the Forge replay")
    lines.append("python3 scripts/audit_live2_authority.py --capture  # refresh the live reads (needs RPC)")
    lines.append("python3 scripts/audit_live2_authority.py --close-coupling  # rerun the Exchange/SKM coupling replay")
    lines.append("```")
    lines.append("")
    lines.append("## Limits")
    lines.append("")
    lines.append("- No archive HyperEVM endpoint is available: every live read is `latest` state at the head "
                 "named in the capture file, not pinned state.")
    lines.append("- The Forge replay is a port-free exact-runtime simulation with locally written storage; it "
                 "sends no transaction and its HyperCore reads are never reached on a success path.")
    lines.append("- Public-registry names are hash-matched candidates, never recovered Solidity source names.")
    lines.append("- Three added selectors remain partly undecoded as to effect: Exchange `0xd970fad5` "
                 "(guard and storage are proved, the economic meaning is not), library `0x06c5308a` and "
                 "library `0xb9370332`.")
    lines.append("")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- capture / replay

def rpc_call(method, params, attempts=12):
    last = None
    for attempt in range(attempts):
        try:
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
            request = urllib.request.Request(RPC, data=body, headers={"content-type": "application/json"})
            with urllib.request.urlopen(request, timeout=25) as response:
                row = json.loads(response.read().decode())
            if "error" in row:
                last = row["error"]
                _sleep(attempt)
                continue
            return row["result"]
        except Exception as exc:  # noqa: BLE001 - network retry
            last = str(exc)
            _sleep(attempt)
    return {"__error__": last}


def _sleep(attempt):
    import time
    time.sleep(2.0 + 2.0 * attempt)


def capture():
    pad = lambda x: x[2:].rjust(64, "0")  # noqa: E731
    proxies = {
        "exchange": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
        "skm": "0x8326eb8896e358717f10502ec73ce8d28e37b108",
        "tokenomics": "0x75174549dbbd44497d31a47e2e2d7406408d63d9",
        "paper": "0xe40f17915daa230324030003a197cdaef2261c0e",
        "staking": "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016",
        "oracle": "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e",
        "batch_executor": "0x233ff29b239abc1d7748605da9b205c3e008626e",
        "factory": "0x1629b7d46bef6e13ff754174fc9f32dea309b38f",
    }
    contracts = {"registry": BUILDER_REGISTRY, "timelock": "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
                 "proxyadmin": "0xe79c91cc682f1bb401a9cab74c900470190f0f8f",
                 "multisig": "0x696292762fd5ac3677a45edbe54eaece4194d1f6"}
    getters = {
        "exchange_owner": (proxies["exchange"], "0x8da5cb5b", None),
        "exchange_authorizedExecutor": (proxies["exchange"], "0x13dd495b", None),
        "exchange_authorizedKeeper": (proxies["exchange"], "0x9d47d4d3", None),
        "exchange_marketKeeper": (proxies["exchange"], "0x21f55a6c", None),
        "exchange_pauseGuardian": (proxies["exchange"], "0x24a3d622", None),
        "exchange_tradingPaused": (proxies["exchange"], "0x53e23e2e", None),
        "exchange_sessionKeyManager": (proxies["exchange"], "0x0b826190", None),
        "exchange_instrumentCount": (proxies["exchange"], "0xf28bbdb2", None),
        "exchange_newFlagGet": (proxies["exchange"], "0xf009ac03", None),
        "exchange_newAccumGet": (proxies["exchange"], "0xcbce7532", None),
        "exchange_devFeeRecipient": (proxies["exchange"], "0xcbeb5f3d", None),
        "exchange_devFeeAccumulator": (proxies["exchange"], "0x7d004aeb", None),
        "skm_owner": (proxies["skm"], "0x8da5cb5b", None),
        "skm_builderRegistry": (proxies["skm"], "0xe737de13", None),
        "tokenomics_owner": (proxies["tokenomics"], "0x8da5cb5b", None),
        "tokenomics_rebateLow128": (proxies["tokenomics"], "0x122b6689", None),
        "tokenomics_insolventSince": (proxies["tokenomics"], "0x456db972", None),
        "paper_owner": (proxies["paper"], "0x8da5cb5b", None),
        "paper_minter": (proxies["paper"], "0x07546172", None),
        "paper_autoApprovedSpender": (proxies["paper"], "0x12bbf044", None),
        "paper_stakingContract": (proxies["paper"], "0xee99205c", None),
        "staking_owner": (proxies["staking"], "0x8da5cb5b", None),
        "registry_owner": (contracts["registry"], "0x8da5cb5b", None),
        "registry_guardian": (contracts["registry"], "0x452a9320", None),
        "registry_feeRate": (contracts["registry"], "0x978bbdb9", None),
        "registry_feeRateOf_keeper": (contracts["registry"], "0xd779e270",
                                      "0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56"),
        "timelock_owner": (contracts["timelock"], "0x8da5cb5b", None),
        "timelock_minDelay": (contracts["timelock"], "0xc63c4e9b", None),
        "proxyadmin_owner": (contracts["proxyadmin"], "0x8da5cb5b", None),
        "multisig_required": (contracts["multisig"], "0x82e717f7", None),
        "multisig_count": (contracts["multisig"], "0xb77bf600", None),
        "multisig_epoch": (contracts["multisig"], "0x900cf0cf", None),
        "multisig_signerOne": (contracts["multisig"], "0xd98f851a", None),
        "multisig_signerTwo": (contracts["multisig"], "0x1a5f66c3", None),
        "multisig_signerThree": (contracts["multisig"], "0x64d62769", None),
    }
    out = {"rpc": RPC, "captured_at_utc": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
    head = rpc_call("eth_getBlockByNumber", ["latest", False])
    out["head"] = {"block": int(head["number"], 16), "hash": head["hash"],
                   "timestamp": int(head["timestamp"], 16)}
    out["getters"] = {}
    for name, (to, sel, arg) in getters.items():
        data = sel + (pad(arg) if arg else "")
        out["getters"][name] = {"to": to, "data": data,
                                "result": rpc_call("eth_call", [{"to": to, "data": data}, "latest"])}
    out["proxy_slots"] = {}
    for name, address in proxies.items():
        out["proxy_slots"][name] = {
            "implementation": rpc_call("eth_getStorageAt", [address, "0x" + IMPL_SLOT, "latest"]),
            "admin": rpc_call("eth_getStorageAt", [address, "0x" + ADMIN_SLOT, "latest"]),
        }
    raw_slots = {
        "exchange": (proxies["exchange"], [0, 8, 26, 29, 37, 38, 88, 89]),
        "skm": (proxies["skm"], [0, 1, 2, 3, 8]),
        "tokenomics": (proxies["tokenomics"], [0, 1, 2, 3, 9]),
        "paper": (proxies["paper"], [3, 4, 5, 6, 9]),
        "staking": (proxies["staking"], [15, 16]),
        "registry": (contracts["registry"], [0, 1, 2]),
        "timelock": (contracts["timelock"], [0, 1]),
        "proxyadmin": (contracts["proxyadmin"], [0]),
        "multisig": (contracts["multisig"], [0, 1, 2, 3, 4]),
    }
    out["raw_slots"] = {name: {hex(slot): rpc_call("eth_getStorageAt", [address, hex(slot), "latest"])
                               for slot in slots} for name, (address, slots) in raw_slots.items()}
    count = rpc_call("eth_call", [{"to": contracts["multisig"], "data": "0xb77bf600"}, "latest"])
    for index in range(11, 13):
        out[f"multisig_transactions_{index}"] = rpc_call(
            "eth_call", [{"to": contracts["multisig"], "data": "0x9ace38c2" + pad(hex(index))}, "latest"])
    out["multisig_transaction_count_raw"] = count
    record = decode_multisig_record(out["multisig_transactions_11"]) if out.get("multisig_transactions_11") else None
    if record and record["data"][:10] == "0xb0e58bc9":
        schedule = decode_schedule(record["data"])
        inner_impl = "0x" + schedule["inner_words"][1][24:]
        enc = lambda x: x[2:].rjust(64, "0")  # noqa: E731
        data_hash = keccak(bytes.fromhex(schedule["inner_data"][2:]))
        out["pending_upgrade_operation_id"] = keccak(bytes.fromhex(
            enc(schedule["target"]) + enc(hex(schedule["value"])) + data_hash[2:].rjust(64, "0")
            + enc(schedule["predecessor"])))
        out["pending_upgrade_timelock_word"] = rpc_call(
            "eth_getStorageAt", [contracts["timelock"],
                                 keccak(bytes.fromhex(out["pending_upgrade_operation_id"][2:].rjust(64, "0")
                                                      + ("00" * 31) + "02")), "latest"])
        out["pending_impl_code"] = rpc_call("eth_getCode", [inner_impl, "latest"])
    OUT.mkdir(parents=True, exist_ok=True)
    CAPTURE_JSON.write_text(json.dumps(out, indent=2) + "\n")
    print(f"captured at head {out['head']['block']} -> {CAPTURE_JSON}")
    return out


CLOSE_COUPLING_TEST = r"""
    function closeExternal(uint256[] memory ids) external returns (uint256) {
        executeMixedClose(ids);
        return 1;
    }

    // The set-2 close calls SKM 0xd95208cd (staticcall) which the pinned SKM does not dispatch.
    function testLive2CloseRequiresSet2SessionKeyManager() public {
        MixedState memory st = prepareMixedPositions(false);
        vm.store(EXCHANGE, bytes32(uint256(8)), bytes32((uint256(1) << 32) | 2));
        bytes32 before38 = vm.load(EXCHANGE, bytes32(uint256(38)));
        vm.record();
        bool ok;
        bytes memory err;
        try this.closeExternal(st.ids) { ok = true; } catch (bytes memory r) { err = r; }
        (, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        uint256 slot39;
        bytes32[] memory k39 = new bytes32[](6);
        k39[0] = keccak256(abi.encode(USER, uint256(39)));
        k39[1] = keccak256(abi.encode(BATCH, uint256(39)));
        k39[2] = keccak256(abi.encode(EXCHANGE, uint256(39)));
        k39[3] = keccak256(abi.encode(vm.addr(0xb0b), uint256(39)));
        k39[4] = keccak256(abi.encode(address(0), uint256(39)));
        k39[5] = keccak256(abi.encode(address(uint160(0x3333333333333333333333333333333333333333)), uint256(39)));
        for (uint256 i; i < k39.length; ++i)
            if (uint256(vm.load(EXCHANGE, k39[i])) != 0) slot39 = i + 1;
        revert(string(abi.encodePacked(
            "ok=", ok ? "y" : "n",
            " errlen=", u2s(err.length),
            " writes=", u2s(writes.length),
            " slot39hit=", u2s(slot39),
            " d38=", vm.load(EXCHANGE, bytes32(uint256(38))) == before38 ? "same" : "diff",
            " slots=", dump(writes))));
    }

    function dump(bytes32[] memory slots) internal pure returns (string memory) {
        bytes memory out;
        for (uint256 i; i < slots.length; ++i) out = abi.encodePacked(out, hexw(slots[i]), ",");
        return string(out);
    }

    function u2s(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 t = v; uint256 d;
        while (t != 0) { d++; t /= 10; }
        bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }

    function hexw(bytes32 v) internal pure returns (string memory) {
        bytes memory h = "0123456789abcdef";
        bytes memory o = new bytes(64);
        for (uint256 i; i < 32; ++i) { uint8 c = uint8(v[i]); o[i*2] = h[c >> 4]; o[i*2+1] = h[c & 0xf]; }
        return string(o);
    }
"""


CLOSE_COUPLING_BATCH_TEST = r"""
    // The same historical BatchExecutor batch that the pinned replay asserts on, run verbatim: the outer
    // call succeeds under either SessionKeyManager, so the failure mode is only visible in the Exchange
    // write set and in whether the two historical positions are still active.
    function testLive2BatchWrapperVisibility() public {
        address relayer = address(0xC916E55b1909be6582bF1b2F017AaF82Ad8eB0B4);
        bytes memory input = hex"__BATCH_INPUT__";
        vm.record();
        vm.prank(relayer);
        (bool ok, bytes memory ret) = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e))).call(input);
        (, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        uint256 nz;
        for (uint256 i; i < writes.length; ++i) if (uint256(vm.load(EXCHANGE, writes[i])) != 0) ++nz;
        uint256 active;
        uint256[2] memory ids = [uint256(1392206), uint256(1392921)];
        for (uint256 i; i < 2; ++i) {
            bytes32 slot = keccak256(abi.encode(ids[i], uint256(10)));
            if ((uint256(vm.load(EXCHANGE, bytes32(uint256(slot) + 1))) & (uint256(1) << 240)) != 0) ++active;
        }
        revert(string(abi.encodePacked(
            "outerok=", ok ? "y" : "n", " retlen=", u2s(ret.length),
            " exchWrites=", u2s(writes.length), " nzw=", u2s(nz),
            " positionsStillActive=", u2s(active))));
    }
"""


CLOSE_COUPLING_FLAG_TEST = r"""
    // Same close as the direct arm, but with slot 8's flag byte cleared: does the flag gate anything?
    function testLive2CloseWithFlagCleared() public {
        MixedState memory st = prepareMixedPositions(false);
        vm.store(EXCHANGE, bytes32(uint256(8)), bytes32(uint256(2)));
        vm.record();
        bool ok;
        bytes memory err;
        try this.closeExternal(st.ids) { ok = true; } catch (bytes memory r) { err = r; }
        (, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        revert(string(abi.encodePacked(
            "ok=", ok ? "y" : "n", " errlen=", u2s(err.length),
            " writes=", u2s(writes.length), " slots=", dump(writes))));
    }
"""

CLOSE_COUPLING_JSON = OUT / "close_coupling.json"
CLOSE_COUPLING_SOL = OUT / "CloseCouplingLocal.t.sol"


def extract_close_harness(destination):
    """Rebuild the historical close harness on disk by driving its generator without forge."""
    spec = importlib.util.spec_from_file_location("_close_gen", ROOT / "scripts" / "audit_historical_close_replay.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_close_gen"] = module
    spec.loader.exec_module(module)
    destination.mkdir(parents=True, exist_ok=True)

    class _Tmp:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return str(destination)

        def __exit__(self, *args):
            return False

    class _Run:
        def __init__(self, stdout=""):
            self.stdout, self.stderr, self.returncode = stdout, "", 0

    passes = ["testHistoricalMixedSignedCloses", "testFourConstructedActivePositionsClose",
              "testFourMixedPnlActivePositionsClose", "testFourMixedPnlLossFirstClose",
              "testFourCrossMarketZeroFirstClose", "testFourCrossMarketOneFirstClose"]
    stdout = "\n".join(f"[PASS] {name}()" for name in passes) + "\nforge 1.8.6\nVersion: 0.8.28\n"

    def fake_run(command, **kwargs):
        return _Run(stdout)

    # NOTE: the generator imports the real `tempfile` and `subprocess` modules, so patching its
    # attributes would patch them process-wide; save and restore around the call.
    real_tmpdir = tempfile.TemporaryDirectory
    real_run = subprocess.run
    module.tempfile.TemporaryDirectory = _Tmp
    module.subprocess.run = fake_run
    try:
        module.main()
    except Exception:  # noqa: BLE001 - only the file writes are wanted
        pass
    finally:
        tempfile.TemporaryDirectory = real_tmpdir
        subprocess.run = real_run
    assert (destination / "test" / "HistoricalCloseReplay.t.sol").exists()
    return destination / "test" / "HistoricalCloseReplay.t.sol"


def run_close_coupling():
    """Set-2 Exchange against the pinned SKM, then against the set-2 SKM, on the pinned prestate."""
    import importlib.util as _ilu
    import sys as _sys
    work = pathlib.Path(tempfile.mkdtemp(prefix="live2-close-coupling-"))
    source_path = extract_close_harness(work)
    source = source_path.read_text()
    source = source.replace(
        "    function addr(uint256) external returns (address);",
        "    function addr(uint256) external returns (address);\n"
        "    function record() external;\n"
        "    function accesses(address) external returns (bytes32[] memory reads, bytes32[] memory writes);",
        1)
    source = source.replace(
        "        vm.roll(48901631);",
        '        vm.etch(address(uint160(uint256(0x00583d0bd818c991c5830fea93aef04e474b272459))), '
        'vm.parseBytes(vm.readFile("runtime/583d0bd818c991c5830fea93aef04e474b272459.hex")));\n'
        "        vm.roll(48901631);", 1)
    source = source[:-2] + CLOSE_COUPLING_TEST + "\n}\n"
    source_path.write_text(source)
    (work / "runtime" / "583d0bd818c991c5830fea93aef04e474b272459.hex").write_text(
        (POSTPIN / "runtime" / SET2_RUNTIMES["exchange_linked_library_2"][1]).read_text().strip())
    (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").write_text(
        (ATLAS / "runtime" / PINNED_RUNTIMES["session_key_manager_implementation"][1]).read_text().strip())
    set2_impl = "0f3febfc94876b0c895f7acecdc8f5c863b549ee.hex"
    (work / "runtime" / set2_impl).write_text(
        (POSTPIN / "runtime" / SET2_RUNTIMES["exchange_implementation_2"][1]).read_text().strip())
    shutil.copy(source_path, CLOSE_COUPLING_SOL)
    pinned_skm = (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").read_text()

    def observe():
        run = subprocess.run(["forge", "test", "--root", str(work), "--match-test",
                              "testLive2CloseRequiresSet2SessionKeyManager", "-vv"],
                             capture_output=True, text=True, timeout=600)
        output = run.stdout + "\n" + run.stderr
        match = re.search(r"ok=(\w) errlen=(\d+) writes=(\d+) slot39hit=(\d+) d38=(\w+) slots=([0-9a-f,]*)",
                          output)
        assert match, output[-4000:]
        return dict(ok=match.group(1) == "y", revert_bytes=int(match.group(2)),
                    write_slots=int(match.group(3)), slot39_candidate_hit=int(match.group(4)),
                    slot_38_changed=match.group(5) == "diff",
                    slots=[s for s in match.group(6).split(",") if s])

    with_pinned_skm = observe()
    (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").write_text(
        (POSTPIN / "runtime" / SET2_RUNTIMES["session_key_manager_implementation_2"][1]).read_text().strip())
    with_set2_skm = observe()

    # second arm: the historical BatchExecutor batch verbatim, under both SessionKeyManagers
    batch_calls = json.loads((ROOT / "artifacts" / "historical" /
                              "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5.calls.json"
                              ).read_text())
    batch_input = batch_calls["input"][2:]
    assert [item["input"][:10] for item in batch_calls["calls"][0]["calls"]] == [
        "0x2792e706", "0x2792e706", "0x8d09f23f", "0x83115825"]
    batch_source = source[:-2] + CLOSE_COUPLING_BATCH_TEST.replace("__BATCH_INPUT__", batch_input) + "\n}\n"
    source_path.write_text(batch_source)

    def observe_batch():
        run = subprocess.run(["forge", "test", "--root", str(work), "--match-test",
                              "testLive2BatchWrapperVisibility", "-vv"],
                             capture_output=True, text=True, timeout=600)
        output = run.stdout + "\n" + run.stderr
        match = re.search(r"outerok=(\w) retlen=(\d+) exchWrites=(\d+) nzw=(\d+) positionsStillActive=(\d+)",
                          output)
        assert match, output[-4000:]
        return dict(outer_ok=match.group(1) == "y", return_bytes=int(match.group(2)),
                    exchange_writes=int(match.group(3)), nonzero_writes=int(match.group(4)),
                    positions_still_active=int(match.group(5)))

    # third arm: the flag byte at slot 8 cleared, to test whether it gates the close at all
    # (still with the set-2 SessionKeyManager, written for the previous arm)
    flag_source = source[:-2] + CLOSE_COUPLING_FLAG_TEST + "\n}\n"
    source_path.write_text(flag_source)

    def observe_flag():
        run = subprocess.run(["forge", "test", "--root", str(work), "--match-test",
                              "testLive2CloseWithFlagCleared", "-vv"],
                             capture_output=True, text=True, timeout=600)
        output = run.stdout + "\n" + run.stderr
        match = re.search(r"ok=(\w) errlen=(\d+) writes=(\d+) slots=([0-9a-f,]*)", output)
        assert match, output[-4000:]
        return dict(ok=match.group(1) == "y", revert_bytes=int(match.group(2)),
                    write_slots=int(match.group(3)),
                    slots=sorted(s for s in match.group(4).split(",") if s))

    flag_cleared = observe_flag()
    source_path.write_text(source)
    (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").write_text(pinned_skm)
    assert flag_cleared["ok"] is True, flag_cleared
    assert flag_cleared["write_slots"] == with_set2_skm["write_slots"], (flag_cleared, with_set2_skm)
    assert sorted(with_set2_skm["slots"]) == flag_cleared["slots"], (flag_cleared, with_set2_skm)

    source_path.write_text(batch_source)
    (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").write_text(pinned_skm)
    batch_with_pinned = observe_batch()
    (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").write_text(
        (POSTPIN / "runtime" / SET2_RUNTIMES["session_key_manager_implementation_2"][1]).read_text().strip())
    batch_with_set2 = observe_batch()
    (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").write_text(pinned_skm)
    source_path.write_text(source)

    assert batch_with_pinned["outer_ok"] is True, batch_with_pinned
    assert batch_with_pinned["positions_still_active"] == 2, batch_with_pinned
    assert batch_with_set2["outer_ok"] is True, batch_with_set2
    assert batch_with_set2["positions_still_active"] == 0, batch_with_set2
    assert batch_with_set2["exchange_writes"] > batch_with_pinned["exchange_writes"]
    (work / "runtime" / "8a5069fe303e8f81e91825436e956d595032e558.hex").write_text(pinned_skm)

    assert with_pinned_skm["ok"] is False, with_pinned_skm
    assert with_pinned_skm["write_slots"] == 0, with_pinned_skm
    assert with_set2_skm["ok"] is True, with_set2_skm
    assert with_set2_skm["write_slots"] > 0, with_set2_skm
    assert with_set2_skm["slot39_candidate_hit"] == 0, with_set2_skm
    assert not with_set2_skm["slot_38_changed"], with_set2_skm
    record = dict(
        method=("port-free exact-runtime replay of a constructed four-position set-2 close on the pinned "
                "mixed-close prestate (two real position templates from transaction "
                "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5, ids 1392206 and "
                "1392921, with word0's address bits rewritten to a synthetic user), the set-2 Exchange "
                "implementation and linked library etched at the addresses the pinned prestate expects, "
                "and the SessionKeyManager implementation swapped between the pinned and the set-2 bytes"),
        with_pinned_session_key_manager=with_pinned_skm,
        with_set2_session_key_manager=with_set2_skm,
        batch_with_pinned_session_key_manager=batch_with_pinned,
        batch_with_set2_session_key_manager=batch_with_set2,
        failure_mode=("a direct close call with the pinned SessionKeyManager reverts with empty data (the "
                      "failed verifier staticcall is bubbled), while the same close inside a BatchExecutor "
                      "batch fails silently: the outer call succeeds and the two historical positions stay "
                      "active, so the batch wrapper masks the inner failure rather than tolerating it"),
        flag_byte_cleared=flag_cleared,
        flagged_write_set_identical=True,
        covered_selectors=["0x2792e706", "0xd95208cd", "0xb002b9fa", "0x251fb27d"],
        limits=[
            "The prestate is the pinned mixed-close prestate, not a set-2-era block.",
            "The position templates are real and the signature is locally generated for the synthetic user.",
            "No slot-39 candidate was credited, so the builder-fee credit key is still unobserved.",
        ],
    )
    CLOSE_COUPLING_JSON.write_text(json.dumps(record, indent=2) + "\n")
    print(f"close coupling flag arm: ok={flag_cleared['ok']} writes={flag_cleared['write_slots']} "
          f"identical_to_flagged={sorted(with_set2_skm['slots']) == flag_cleared['slots']}")
    print(f"close coupling: pinned SKM revert={not with_pinned_skm['ok']}, "
          f"set-2 SKM writes={with_set2_skm['write_slots']}; batch writes "
          f"{batch_with_pinned['exchange_writes']} -> {batch_with_set2['exchange_writes']}, "
          f"positions active {batch_with_pinned['positions_still_active']} -> "
          f"{batch_with_set2['positions_still_active']}")
    return record


def run_replay():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    source = REPLAY_SOURCE.read_text()
    wanted = {
        "Exchange2.hex": SET2_EXCHANGE,
        "SessionKeyManager2.hex": SET2_SKM,
        "Tokenomics2.hex": SET2_TOKENOMICS,
        "Library2.hex": SET2_LIBRARY,
        "BuilderRegistry.hex": BUILDER_REGISTRY,
        "PaperImplementation.hex": "0x433bd418ec92818a960585f4d5fae563e735bb4a",
        "StakingImplementation.hex": "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15",
        "ProxyAdmin.hex": "0xe79c91cc682f1bb401a9cab74c900470190f0f8f",
        "Timelock.hex": "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
        "Multisig.hex": "0x696292762fd5ac3677a45edbe54eaece4194d1f6",
        "SharedProxy.hex": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
    }
    with tempfile.TemporaryDirectory(prefix="live2-authority-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(shutil.which("solc")) +
            "\noffline = true\nfs_permissions = [{ access = \"read\", path = \"./runtime\" }]\n")
        (project / "test" / "AuthorityLocal.t.sol").write_text(source)
        hashes = {}
        for filename, address in wanted.items():
            if address in manifest["contracts"]:
                runtime = (ATLAS / manifest["contracts"][address]["runtime_file"]).read_text().strip()
                hashes[filename.removesuffix(".hex")] = dict(
                    address=address, sha256=manifest["contracts"][address]["sha256"])
            else:
                role = next(r for r, v in SET2_RUNTIMES.items() if v[0] == address)
                path = POSTPIN / "runtime" / SET2_RUNTIMES[role][1]
                runtime = path.read_text().strip()
                hashes[filename.removesuffix(".hex")] = dict(
                    address=address, sha256=SET2_RUNTIMES[role][2])
            (project / "runtime" / filename).write_text(runtime)
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-contract",
                              "AuthorityLocalTest", "-vv"], capture_output=True, text=True, timeout=600)
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    expected = sorted(re.findall(r"function (test\w+)\(", source))
    if run.returncode or passed != expected:
        raise RuntimeError(output)
    record = dict(
        pin=manifest["block"],
        method=("port-free in-process Forge EVM; the exact saved set-2 implementation runtimes, the shared "
                "proxy, the ProxyAdmin, the timelock and the multisig are injected with vm.etch; captured "
                "storage words are written with vm.store; no transaction is sent and no RPC is contacted"),
        runtime_hashes=hashes,
        test_names=expected,
        passed_tests=passed,
        forge_result=f"{len(passed)} passed, 0 failed",
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        limits=[
            "Synthetic local state: the storage words were written from captures, not replayed from a block.",
            "The signer sets and pause roles are installed from the pinned records, not re-read here.",
        ],
    )
    REPLAY_JSON.write_text(json.dumps(record, indent=2) + "\n")
    print(f"live2 authority replay: {len(passed)} exact-runtime tests passed")
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true", help="refresh the live latest reads")
    parser.add_argument("--replay", action="store_true", help="regenerate the Forge replay")
    parser.add_argument("--close-coupling", action="store_true",
                        help="rerun the set-2 Exchange / SessionKeyManager coupling experiment")
    args = parser.parse_args()
    if args.capture:
        capture()
    if args.replay:
        run_replay()
    if args.close_coupling:
        run_close_coupling()

    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN_BLOCK
    assert manifest["block_hash"] == "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"

    for name, topic in EVENT_TOPICS.items():
        assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\(.*\)", name), name
        assert re.fullmatch(r"0x[0-9a-f]{64}", topic), (name, topic)
        assert topic_of(name) == topic, (name, topic_of(name), topic)
    for signature, digest in TYPEHASHES.items():
        assert topic_of(signature) == digest, (signature, topic_of(signature), digest)
        for role in ("exchange_implementation_2", "exchange_implementation"):
            filename = (SET2_RUNTIMES.get(role) or PINNED_RUNTIMES[role])[1]
            root = POSTPIN / "runtime" if role.endswith("_2") else ATLAS / "runtime"
            assert bytes.fromhex(digest[2:]) in load_runtime(root / filename), (role, signature)
    for name, sel in REJECTED_NAMES.items():
        assert selector_of(name) != sel, (name, sel, selector_of(name))
    for name, sel in ERROR_SELECTORS.items():
        assert re.fullmatch(r"0x[0-9a-f]{8}", sel), (name, sel)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\(.*\)", name):
            assert selector_of(name) == sel, (name, selector_of(name), sel)
        else:
            assert sel in name, (name, sel)
    for sel, name in BUILDER_REGISTRY_SELECTORS.items():
        assert selector_of(name) == sel, (name, selector_of(name), sel)

    facts, diff, per_selector = check_static()
    registry = check_registry()
    saved = check_saved_live()
    own = check_own_capture()
    pending = check_pending_upgrade()
    replay = check_replay()
    rows = ledger_rows(facts, diff, per_selector, registry)

    ledger = dict(
        pin=PIN_BLOCK,
        block_hash=manifest["block_hash"],
        generated_by="audit_live2_authority.py",
        scope=("Authority, configuration and the upgrade route on the contract set 2 code installed by the "
               "2026-10-21 governance batch: the set-2 Exchange, SessionKeyManager and Tokenomics "
               "implementations, the new BuilderRegistry, and the multisig/timelock/ProxyAdmin chain."),
        set2_runtimes=facts,
        selector_diff=diff,
        added_selector_facts={k: dict(v, **ADDED_FACTS[tuple(k.split(":", 1))])
                              for k, v in per_selector.items()},
        builder_registry=registry,
        saved_capture=saved,
        own_capture={k: v for k, v in own.items() if k not in ("getters",)},
        pending_upgrade=pending,
        close_coupling=(json.loads((OUT / "close_coupling.json").read_text())
                        if (OUT / "close_coupling.json").exists() else None),
        rejected_names={name: {"selector": sel, "note": "hash-asserted as NOT this name"}
                        for name, sel in REJECTED_NAMES.items()},
        cross_references={
            "signed_intents": {
                "artifact": "atlas/block_48902346/live2_intents.json",
                "script": "audit_live2_intents.py",
                "rows_used": ["L2-D1-06", "L2-D2-04", "L2-D2-05", "L2-D4-02", "L2-D5-01", "L2-D1-07"],
                "used_for": ["the close struct has no builder field and an unsigned trailing calldata word does "
                             "not become the slot-39 key (L2A-09)",
                             "claimBuilderFees pays only the caller's own entry (L2A-08)",
                             "the sweep family does not reach the slot-39 block (L2A-14)",
                             "0xd970fad5 reassigns slot-39 accruals and leaves slot 38 alone (L2A-13)",
                             "a mixed pair also changes dust-sweep retry success semantics (L2A-16)"],
                "name_confirmations": [
                    "BuilderFeesClaimed(address,uint256,uint256) = 0x3416b71e... is hash-asserted in both "
                    "audit_live2_authority.py and audit_live2_intents.py",
                    "SweepBelowMinimum() = 0x329c2b0f is hash-asserted in both scripts",
                    "SweepSameBlock() and SweepRateLimited() are asserted here as NOT 0xd26ffacb and "
                    "0xfefe83a0, so neither name may be revived in prose",
                ],
            },
        },
        replay=replay if "test_names" not in replay else dict(
            status="present", forge_result=replay["forge_result"],
            test_names=replay["test_names"], source_sha256=replay["source_sha256"]),
        findings=rows,
        counts=dict(
            rows=len(rows),
            by_status={s: sum(1 for r in rows if r["status"] == s) for s in STATUS_ORDER
                       if any(r["status"] == s for r in rows)},
            by_affected={a: sum(1 for r in rows if r["affected"] == a) for a in ("set2", "both", "pinned")},
            added_selectors=sum(len(v) for v in ADDED.values()),
            dropped_selectors=sum(len(v) for v in DROPPED.values()),
            added_selectors_with_non_owner_guard=1,
        ),
        proposed_invariants={
            "A8": ("A privileged role is limited to the actions its deployment wired it for: no role other "
                   "than the owner can change a price, a pointer or an implementation, and each non-owner "
                   "role's reach is enumerated."),
        },
        limits=[
            "No archive HyperEVM endpoint: live values are latest-state reads at the named head.",
            "The Forge replay is a simulation with locally written storage, not a historical trace.",
            "Public-registry names are hash-matched candidates, not recovered source names.",
            "Exchange 0xd970fad5 and the two library entries are decoded for guard and storage but not "
            "for economic meaning.",
        ],
    )
    OUTPUT_JSON.write_text(json.dumps(ledger, indent=2) + "\n")
    OUTPUT_MD.write_text(build_md(ledger))
    print(f"rows={len(rows)} status={ledger['counts']['by_status']}")
    print(f"wrote {OUTPUT_JSON} and {OUTPUT_MD}")


if __name__ == "__main__":
    main()