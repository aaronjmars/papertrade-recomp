#!/usr/bin/env python3
"""Close the untraced Exchange and linked-library selector rows with exact evidence.

Pinned to HyperEVM block 48,902,346. Three offline layers per assigned selector:

1. Static read of the pinned runtime bytes: dispatcher entry, canonical calldata
   length constant, calldata word offsets, caller-guard helper, storage slots,
   log topics and delegatecall targets.
2. Name check: every candidate signature is hashed with the local keccak and only
   kept when the hash equals the selector or topic byte string in the runtime.
3. Port-free exact-runtime Forge replay: the pinned proxy, Exchange
   implementation and linked library runtimes are etched into a fresh EVM with
   pinned storage words and a mock HyperCore BBO precompile. Calldata, revert
   data, storage fingerprints and logs are recorded. Synthetic, not historical.

Run `python3 scripts/atlas_selector_gap_exchange.py` offline; it needs no RPC credential
and never touches the network. The pinned storage words come from the saved
archived state diffs and probe ledgers under artifacts/, because the public RPC
serves current state only.

Outputs, all inside this slice:
  artifacts/selector_gap_exchange/static_analysis.json   static read and name checks
  artifacts/selector_gap_exchange/replay.json            frozen replay expectations
  artifacts/selector_gap_exchange/replay/                generated suite and raw records
  atlas/block_48902346/selector_gap_exchange.json        machine ledger, one row per selector
  atlas/block_48902346/selector_gap_exchange.md          readable behaviour record

`--record` reruns the suite and writes the observed records without checking the
frozen expectations; use it only when the harness itself changes.
"""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "selector_gap_exchange"
STATIC_OUT = ARTIFACTS / "static_analysis.json"
REPLAY_OUT = ARTIFACTS / "replay.json"
LEDGER_OUT = ATLAS / "selector_gap_exchange.json"
DOC_OUT = ATLAS / "selector_gap_exchange.md"

PIN = 48902346
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
PAPER = "0xe40f17915daa230324030003a197cdaef2261c0e"
PAPER_MATH = "0xe991817199363046da0a28da6fbad0284e4aa492"
TOKENOMICS_IMPL = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
PAPER_IMPL = "0x433bd418ec92818a960585f4d5fae563e735bb4a"
ORACLE_IMPL = "0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a"
BBO_PRECOMPILE = "0x000000000000000000000000000000000000080e"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
PAUSE_GUARDIAN = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
MARKET_KEEPER = "0x3721476de31190dc1af8908026abe20efe25cf99"
AUTHORIZED_EXECUTOR = "0x233ff29b239abc1d7748605da9b205c3e008626e"
SESSION_KEY_MANAGER = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
OUTSIDER = "0x00000000000000000000000000000000000beef0"

# The twenty assigned rows: the coverage ledger's nonview selectors without a
# saved historical trace for the Exchange implementation and its linked library.
ASSIGNED = {
    "exchange_implementation": [
        "0x01681a62", "0x2d2451d1", "0x415f1240", "0x4a4d9eea", "0x5ca4c0ea",
        "0x6a3214c9", "0x753a369c", "0x827ad94c", "0xae4daf4e", "0xae69b95b",
        "0xc0c53b8b", "0xd7c7e5fb", "0xe538b280",
    ],
    "exchange_linked_library_live": [
        "0x18958ce2", "0x2448a553", "0x32db40c9", "0x3cf4208d", "0x3f4e3626",
        "0xb67f3dd7", "0xca02ff91",
    ],
}

# Candidate names. Every one is hashed below; a name is used only when its hash
# equals the selector or topic bytes found in the pinned runtime. Sources are
# recorded so a reader can see which are behaviour reconstructions (no registry
# or bytecode name match) rather than proven source identifiers.
NAME_CANDIDATES = {
    "0x01681a62": ("sweep(address)", "behaviour_reconstruction: exchange_sweep_behavior.json"),
    "0x2d2451d1": ("pauseMarket(uint32)", "behaviour_reconstruction: exchange_pause_behavior.json"),
    "0x415f1240": ("liquidate(uint256)", "public_abi_fixture: exchange_interface_evidence.json"),
    "0x4a4d9eea": ("", "unresolved"),
    "0x5ca4c0ea": ("", "unresolved"),
    "0x6a3214c9": ("reconcileSweepCredit(address,uint256)", "behaviour_reconstruction: exchange_sweep_behavior.json"),
    "0x753a369c": ("", "unresolved"),
    "0x827ad94c": ("", "unresolved"),
    "0xae4daf4e": ("", "unresolved"),
    "0xae69b95b": ("setTradingPaused(bool)", "behaviour_reconstruction: exchange_pause_behavior.json"),
    "0xc0c53b8b": ("initialize(address,address,address)", "public_abi_fixture: guardian_report_lead"),
    "0xd7c7e5fb": ("", "unresolved"),
    "0xe538b280": ("setFeeRates(uint256,uint256,uint256)", "behaviour_reconstruction: exchange_fee_rates_behavior.json"),
    "0x18958ce2": ("", "unresolved"),
    "0x2448a553": ("", "unresolved"),
    "0x32db40c9": ("", "unresolved"),
    "0x3cf4208d": ("", "unresolved"),
    "0x3f4e3626": ("", "unresolved"),
    "0xb67f3dd7": ("", "unresolved"),
    "0xca02ff91": ("", "unresolved"),
}

# Error names. `registry` names are the OpenChain candidates saved in
# artifacts/openchain_unverified_error_lookup.json; `behaviour` names are
# hash-checked reconstructions from the existing behaviour maps. Every name is
# re-hashed locally, so a wrong row fails the run instead of entering the ledger.
ERROR_NAMES = {
    "0x30cd7471": ("NotOwner()", "registry"),
    "0x49199fb6": ("NotPauseAuthority()", "registry"),
    "0xcd4e6167": ("FeeTooHigh()", "registry"),
    "0x67207a88": ("InvalidInstrumentId()", "registry"),
    "0x0dc149f0": ("AlreadyInitialized()", "registry"),
    "0x6a426315": ("UnsupportedCollateralDecimals()", "registry"),
    "0x94e88a21": ("PositionNotOpen()", "registry"),
    "0x0984a617": ("NoPendingSweep()", "registry"),
    "0x28ef4314": ("SweepAlreadyPending()", "registry"),
    "0x0d240815": ("MarketAlreadyPaused()", "registry"),
    "0xddeb79ba": ("NotLiquidatable()", "behaviour"),
    "0x329c2b0f": ("SweepBelowMinimum()", "behaviour"),
    "0x0a9e0180": ("NoCoreBalance()", "behaviour"),
}
# Revert selectors with no defensible name: they stay descriptive placeholders.
UNNAMED_ERRORS = {
    "0x5b6d2b7a": "library queue-range or merge-limit error",
    "0x0ce40f51": "instrument ID bound error at helper 0x4af4",
    "0xb0cb274d": "instrument field validation error",
}

# Event signature candidates: hashed locally, never assumed.
EVENT_CANDIDATES = [
    "FeeRatesUpdated(uint256,uint256,uint256)",
    "TradingPausedUpdated(bool)",
    "PauseGuardianUpdated(address)",
    "OwnerUpdated(address)",
    "MarketKeeperUpdated(address)",
    "Enqueued(address,uint256,uint256)",
    "Dequeued(address,uint256,uint256)",
    "SweepRequested(address,address,uint64,uint64,uint32)",
    "Swept(address,uint256)",
    "PendingSweepCleared(address,address)",
    "Harvested(address,uint256)",
    "Liquidated(address,uint256,uint256,uint256,uint256)",
    "Transfer(address,address,uint256)",
]

RUNTIME_ADDRESSES = (
    PROXY, IMPLEMENTATION, LIBRARY, ORACLE, ORACLE_IMPL,
    TOKENOMICS, TOKENOMICS_IMPL, PAPER, PAPER_IMPL, PAPER_MATH,
)

TERMINATORS = {"STOP", "RETURN", "REVERT", "INVALID", "SELFDESTRUCT"}

# Custom errors pushed on caller-rejection branches of the pinned runtimes.
GUARD_ERROR_SELECTORS = {"0x30cd7471", "0x49199fb6", "0x67207a88", "0x0ce40f51", "0xb0cb274d"}

# A slot whose role is known from the pinned getters and storage traces.
SLOT_ROLES = {0: "owner", 1: "pauseGuardian", 8: "instrumentCount",
              37: "marketKeeper", 88: "authorizedExecutor", 89: "authorizedKeeper"}


def keccak(text):
    """Local keccak-256 through cast, matching the repo's hash convention."""
    return "0x" + subprocess.run(["cast", "keccak", text], capture_output=True,
                                 text=True, check=True).stdout.strip().removeprefix("0x")


def selector_of(signature):
    return subprocess.run(["cast", "sig", signature], capture_output=True,
                          text=True, check=True).stdout.strip()


def keccak_bytes(data):
    """keccak-256 of raw bytes; cast keccak accepts the 0x-prefixed hex string."""
    return "0x" + subprocess.run(["cast", "keccak", "0x" + data.hex()], capture_output=True,
                                 text=True, check=True).stdout.strip().removeprefix("0x")


class Runtime:
    """Disassembled pinned runtime with dispatcher entries and region BFS."""

    def __init__(self, address, manifest):
        row = manifest["contracts"][address]
        self.address = address
        self.role = row["role"]
        self.hex = (ATLAS / row["runtime_file"]).read_text().strip()
        self.bytes = bytes.fromhex(self.hex.removeprefix("0x"))
        self.sha256 = hashlib.sha256(self.bytes).hexdigest()
        assert self.sha256 == row["sha256"], (address, self.sha256, row["sha256"])
        self.keccak = row["keccak256"]
        disassembly = json.loads(subprocess.run(
            ["cast", "disassemble", "--json", self.hex],
            capture_output=True, text=True, check=True).stdout)["data"]
        self.insts = {}
        for line in disassembly.splitlines():
            if len(line) > 10 and line[8:10] == ": ":
                self.insts[int(line[:8], 16)] = line.split(": ", 1)[1]
        self.pcs = sorted(self.insts)
        self.index = {pc: i for i, pc in enumerate(self.pcs)}
        self.entries = {}
        for match in re.finditer(rb"\x63(.{4})\x14\x61(.{2})\x57", self.bytes, re.S):
            self.entries["0x" + match.group(1).hex()] = int.from_bytes(match.group(2), "big")
        self.entry_pcs = set(self.entries.values())
        self.current_entry = None

    def prev(self, pc, step=1):
        i = self.index[pc] - step
        return (self.pcs[i], self.insts[self.pcs[i]]) if i >= 0 else (None, "")

    def next(self, pc, step=1):
        i = self.index[pc] + step
        return (self.pcs[i], self.insts[self.pcs[i]]) if i < len(self.pcs) else (None, "")

    def constant(self, text):
        """Integer value of a PUSHn instruction, or None."""
        if not text.startswith("PUSH") or text == "PUSH0":
            return None
        return int(text.split()[1], 16)

    def jump_targets(self, pc, window=8):
        """Addresses a jump can reach: nearest preceding PUSH constant plus one continuation.

        solc compiles an internal call as `PUSH2 return PUSH2 callee JUMP` and a
        direct branch as `PUSH2 target JUMP`; with stack shuffles the pushed
        constants are still within a few instructions of the jump. Only
        JUMPDEST targets are followed, and the region avoids re-entering another
        public function body.
        """
        constants = []
        for step in range(1, window + 1):
            back_pc, back = self.prev(pc, step)
            if back is None:
                break
            # Stop at a terminator or jump: earlier code belongs to another block.
            if back in TERMINATORS or back in ("JUMP", "JUMPI", "JUMPDEST"):
                if back in ("JUMPDEST",):
                    continue
                if constants:
                    break
            value = self.constant(back)
            if value is not None:
                constants.append((back_pc, value))
        targets = []
        for index, (push_pc, value) in enumerate(constants[:2]):
            if value not in self.insts or self.insts[value] != "JUMPDEST":
                continue
            if value in self.entry_pcs and value != self.current_entry:
                continue
            if index == 1:
                # A return address is only credible when it follows a dynamic
                # return jump, the shape `PUSH2 return ... JUMP`.
                before = self.prev(value)[1]
                if before != "JUMP":
                    continue
            targets.append(value)
        return targets

    def region(self, entry, cap=8000):
        """Instructions statically reachable from a function entry.

        Direct jumps and the common internal-call idiom are followed. A jump
        whose target comes from a stack value pushed more than a window earlier
        is not followed, so the region is an under-approximation: absence of an
        opcode here is not proof of absence in the function.
        """
        self.current_entry = entry
        seen = {}
        stack = [entry]
        while stack and len(seen) < cap:
            pc = stack.pop()
            if pc in seen or pc not in self.insts:
                continue
            seen[pc] = self.insts[pc]
            text = self.insts[pc]
            if text in ("JUMP", "JUMPI"):
                for target in self.jump_targets(pc):
                    stack.append(target)
                if text == "JUMPI":
                    nxt = self.next(pc)[0]
                    if nxt is not None:
                        stack.append(nxt)
                continue
            if text in TERMINATORS:
                continue
            nxt = self.next(pc)[0]
            if nxt is not None:
                stack.append(nxt)
        return seen

    def prologue(self, entry, window=0x60, depth=2):
        """Entry block plus the first block of each helper it jumps into."""
        out = {}
        current = {(pc, text) for pc, text in self.region(entry).items() if pc < entry + window}
        frontier = {entry}
        for _ in range(depth):
            helpers = set()
            for pc, text in sorted(current):
                if not text.startswith("PUSH") or text == "PUSH0":
                    continue
                chain, nxt = [pc], self.next(pc)[0]
                while nxt is not None and self.insts[nxt].startswith("PUSH") and self.insts[nxt] != "PUSH0":
                    chain.append(nxt)
                    nxt = self.next(nxt)[0]
                if nxt is not None and self.insts[nxt] in ("JUMP", "JUMPI"):
                    target = self.constant(self.insts[chain[-1]])
                    if target not in self.entry_pcs:
                        helpers.add(target)
            new = set()
            for helper in helpers:
                for pc, text in self.region(helper).items():
                    if pc < helper + window:
                        new.add((pc, text))
            current |= new
            frontier = helpers
            if not helpers:
                break
        return dict(sorted(current)), frontier


def calldata_shape(runtime, entry):
    """Minimum calldata bytes and calldata word offsets read, from the prologue."""
    prologue, _ = runtime.prologue(entry)
    minimum = None
    if any(text == "CALLDATASIZE" for text in prologue.values()):
        for pc, text in sorted(prologue.items()):
            value = runtime.constant(text)
            if value is None or value == 0 or value % 32:
                continue
            # `PUSH1 <argbytes> CALLDATASIZE PUSH1 0x03 NOT ADD SLT`, or the
            # split form where the entry pushes CALLDATASIZE and a helper
            # compares `PUSH1 <argbytes> SWAP1 PUSH1 0x03 NOT ADD SLT`.
            window = [runtime.insts.get(runtime.next(pc, step)[0], "") for step in range(1, 7)]
            if "SLT" in window and "ADD" in window:
                minimum = value if minimum is None else max(minimum, value)
    offsets = sorted({runtime.constant(runtime.prev(pc)[1])
                      for pc, text in prologue.items()
                      if text == "CALLDATALOAD"
                      and runtime.prev(pc)[1].startswith("PUSH1")})
    return minimum, offsets


def guard_facts(runtime, entry, guard_error_selectors=None):
    """Caller-authorization checks reachable from the entry.

    A site counts when CALLER is compared against a value derived from storage
    and the comparison feeds a conditional jump. solc emits two shapes here:
    `SLOAD ... AND CALLER EQ ISZERO JUMPI` for a direct mask, and
    `SLOAD SHIFT ... CALLER SUB JUMPI` for a packed owner field. The exact
    rejection selector is not claimed from these bytes; the replay probes
    record it instead.
    """
    region = runtime.region(entry)
    callers = [pc for pc, text in sorted(region.items()) if text == "CALLER"]
    out = []
    for caller_pc in callers:
        fwd = [runtime.insts.get(runtime.next(caller_pc, step)[0], "") for step in range(1, 11)]
        back = [runtime.prev(caller_pc, step)[1] for step in range(1, 11)]
        if not {"EQ", "SUB", "XOR"} & set(fwd + back):
            continue
        if "JUMPI" not in fwd:
            continue
        if "SLOAD" not in back:
            continue
        slot = None
        for step in range(1, 6):
            back_pc, back_text = runtime.prev(caller_pc, step)
            if back_text == "SLOAD":
                slot_pc, slot_text = runtime.prev(back_pc)
                while slot_text in ("DUP1", "DUP2", "DUP3", "DUP4", "DUP5", "SWAP1", "SWAP2", "SWAP3"):
                    slot_pc, slot_text = runtime.prev(slot_pc)
                    if slot_text is None:
                        break
                if slot_text is not None and (slot_text == "PUSH0" or slot_text.startswith("PUSH1")):
                    slot = 0 if slot_text == "PUSH0" else runtime.constant(slot_text)
                break
        shift = None
        for step in range(1, 10):
            _, back_text = runtime.prev(caller_pc, step)
            if back_text is not None and back_text.startswith("PUSH1") and runtime.constant(back_text) == 0x10:
                shift = 16
                break
        out.append({"caller_pc": caller_pc, "slot": slot, "shift": shift,
                    "comparison_ops": sorted({"EQ", "SUB", "XOR"} & set(fwd + back))})
    return region, out


def guard_role(facts, slot_roles):
    if not facts:
        return "no_caller_check"
    roles = set()
    for fact in facts:
        if fact["slot"] in slot_roles:
            roles.add(slot_roles[fact["slot"]])
        elif fact["slot"] is None and fact["shift"] == 16:
            # slot 0 owner is loaded through a DUP, so its constant is not adjacent;
            # the 16-bit shift of the packed owner field identifies it.
            roles.add("owner")
        else:
            roles.add(f"slot_{fact['slot']}")
    return "+".join(sorted(roles))


# ---------------------------------------------------------------------------
# Port-free replay layer
# ---------------------------------------------------------------------------

# Canonical calldata per assigned selector, built in Solidity from these
# argument expressions. Every call is a synthetic probe, never a historical one.
CANONICAL_ARGS = {
    "0x01681a62": "(USER)",
    "0x2d2451d1": "(uint32(0))",
    "0x415f1240": "(uint256(1394473))",
    "0x4a4d9eea": "(USER, uint256(101), uint256(102))",
    "0x5ca4c0ea": "(uint32(0), uint128(1e18), uint96(1), uint96(1), uint64(1))",
    "0x6a3214c9": "(USER, uint256(1))",
    "0x753a369c": "(USER, uint256(101), uint256(102), uint256(2))",
    "0x827ad94c": "(USER, uint256(101), uint256(102), uint256(2))",
    "0xae4daf4e": "(USER, uint256(101), uint256(102))",
    "0xae69b95b": "(true)",
    "0xc0c53b8b": "(OUTSIDER, ORACLE, PAPER)",
    "0xd7c7e5fb": "(uint32(0), uint32(1), uint256(1))",
    "0xe538b280": "(uint256(1e16), uint256(2e16), uint256(3e16))",
    "0x18958ce2": "(uint256(15), USER, uint256(500))",
    "0x2448a553": "(uint256(15), USER, uint256(1), uint256(2), uint256(1e18))",
    "0x32db40c9": "(uint256(15), USER, uint256(101), uint256(102), uint256(2))",
    "0x3cf4208d": "(uint256(15), USER, uint256(101), uint256(102), uint256(2), uint256(1e18))",
    "0x3f4e3626": "(uint256(15), USER, uint256(100))",
    "0xb67f3dd7": "(uint256(1e18), uint64(100), uint64(110), uint256(0), uint256(1e18), uint256(1e6), uint256(1e18))",
    "0xca02ff91": "(uint256(15), USER, uint256(101), uint256(102))",
}

REPLAY_EXPECTATIONS = {
    "boundary_0x415f1240": ("revert", "0x924d25e6", False, ""),
    "cap_0xe538b280": ("revert", "0xcd4e6167", False, ""),
    "delegate_0x18958ce2": ("ok", "0x", True, "491460923342184218035706888008750043977755113263:0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7:3:32"),
    "delegate_0x2448a553": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", False, ""),
    "delegate_0x32db40c9": ("revert", "0x5b6d2b7a", False, ""),
    "delegate_0x3cf4208d": ("revert", "0x5b6d2b7a", False, ""),
    "delegate_0x3f4e3626": ("ok", "0x", True, "491460923342184218035706888008750043977755113263:0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d:2:32"),
    "delegate_0xb67f3dd7": ("ok", "0x0000000000000000000000000000000000000000000000000000001748753a50", False, ""),
    "delegate_0xca02ff91": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", False, ""),
    "farprice_0x415f1240": ("revert", "0xddeb79ba", False, ""),
    "guardian_0xae69b95b": ("ok", "0x", True, "621329955008895694125364835068175551477650542754:0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e:1:32"),
    "guardian_false_0xae69b95b": ("revert", "0x49199fb6", False, ""),
    "inactive_0x415f1240": ("revert", "0x94e88a21", False, ""),
    "initialized_0xc0c53b8b": ("revert", "0x0dc149f0", False, ""),
    "invalid_0x2d2451d1": ("revert", "0x67207a88", False, ""),
    "invalid_0x5ca4c0ea": ("revert", "0x67207a88", False, ""),
    "keeper_0x01681a62": ("revert", "0x967d697b", False, ""),
    "merge_0x4a4d9eea": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000002bc0000000000000000000000000000000000000000000000000000000000000065", True, "621329955008895694125364835068175551477650542754:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;621329955008895694125364835068175551477650542754:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "merge_0x753a369c": ("ok", "0x0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000012c0000000000000000000000000000000000000000000000000000000000000066", True, "621329955008895694125364835068175551477650542754:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;621329955008895694125364835068175551477650542754:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "merge_0x827ad94c": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000002bc0000000000000000000000000000000000000000000000000000000000000065", True, "621329955008895694125364835068175551477650542754:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;621329955008895694125364835068175551477650542754:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "merge_0xae4daf4e": ("ok", "0x0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000012c0000000000000000000000000000000000000000000000000000000000000066", True, "621329955008895694125364835068175551477650542754:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;621329955008895694125364835068175551477650542754:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "merge_delegate_0x2448a553": ("ok", "0x0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000012c0000000000000000000000000000000000000000000000000000000000000066", True, "491460923342184218035706888008750043977755113263:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;491460923342184218035706888008750043977755113263:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "merge_delegate_0x32db40c9": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000002bc0000000000000000000000000000000000000000000000000000000000000065", True, "491460923342184218035706888008750043977755113263:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;491460923342184218035706888008750043977755113263:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "merge_delegate_0x3cf4208d": ("ok", "0x0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000012c0000000000000000000000000000000000000000000000000000000000000066", True, "491460923342184218035706888008750043977755113263:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;491460923342184218035706888008750043977755113263:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "merge_delegate_0xca02ff91": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000002bc0000000000000000000000000000000000000000000000000000000000000065", True, "491460923342184218035706888008750043977755113263:0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb:4:32;491460923342184218035706888008750043977755113263:0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc:4:64"),
    "out_of_bound_0x415f1240": ("revert", "0x94e88a21", False, ""),
    "outsider_0x01681a62": ("revert", "0x967d697b", False, ""),
    "outsider_0x18958ce2": ("revert", "0x", False, ""),
    "outsider_0x2448a553": ("revert", "0x", False, ""),
    "outsider_0x2d2451d1": ("revert", "0x49199fb6", False, ""),
    "outsider_0x32db40c9": ("revert", "0x", False, ""),
    "outsider_0x3cf4208d": ("revert", "0x", False, ""),
    "outsider_0x3f4e3626": ("revert", "0x", False, ""),
    "outsider_0x415f1240": ("revert", "0xddeb79ba", False, ""),
    "outsider_0x4a4d9eea": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", False, ""),
    "outsider_0x5ca4c0ea": ("revert", "0x30cd7471", False, ""),
    "outsider_0x6a3214c9": ("revert", "0x30cd7471", False, ""),
    "outsider_0x753a369c": ("revert", "0x5b6d2b7a", False, ""),
    "outsider_0x827ad94c": ("revert", "0x5b6d2b7a", False, ""),
    "outsider_0xae4daf4e": ("ok", "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", False, ""),
    "outsider_0xae69b95b": ("revert", "0x49199fb6", False, ""),
    "outsider_0xb67f3dd7": ("ok", "0x0000000000000000000000000000000000000000000000000000001748753a50", False, ""),
    "outsider_0xc0c53b8b": ("revert", "0x0dc149f0", False, ""),
    "outsider_0xca02ff91": ("revert", "0x", False, ""),
    "outsider_0xd7c7e5fb": ("revert", "0x30cd7471", False, ""),
    "outsider_0xe538b280": ("revert", "0x30cd7471", False, ""),
    "owner_0x2d2451d1": ("ok", "0x", True, "621329955008895694125364835068175551477650542754:0x25e933a27e6487478d7617f2f4ef2f5c77355faf6cad2e6fd7c4b8d029930d9f:2:96"),
    "owner_0x5ca4c0ea": ("ok", "0x", True, "621329955008895694125364835068175551477650542754:0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9:2:128"),
    "owner_0x6a3214c9": ("ok", "0x", False, ""),
    "owner_0xae69b95b": ("ok", "0x", True, "621329955008895694125364835068175551477650542754:0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e:1:32"),
    "owner_0xd7c7e5fb": ("ok", "0x", True, "621329955008895694125364835068175551477650542754:0x62db1b2b923b6f20043c492d3586df1a823e447c63e44d15dbc90c1a3bc9fcc5:2:64"),
    "owner_0xe538b280": ("ok", "0x", True, "621329955008895694125364835068175551477650542754:0xe4af0531d4ba8c578b5076b042e4505372fb4f4986aea8ebf77f4ff1585e3e75:1:96"),
    "short_0x01681a62": ("revert", "0x", False, ""),
    "short_0x18958ce2": ("revert", "0x", False, ""),
    "short_0x2448a553": ("revert", "0x", False, ""),
    "short_0x2d2451d1": ("revert", "0x", False, ""),
    "short_0x32db40c9": ("revert", "0x", False, ""),
    "short_0x3cf4208d": ("revert", "0x", False, ""),
    "short_0x3f4e3626": ("revert", "0x", False, ""),
    "short_0x415f1240": ("revert", "0x", False, ""),
    "short_0x4a4d9eea": ("revert", "0x", False, ""),
    "short_0x5ca4c0ea": ("revert", "0x", False, ""),
    "short_0x6a3214c9": ("revert", "0x", False, ""),
    "short_0x753a369c": ("revert", "0x", False, ""),
    "short_0x827ad94c": ("revert", "0x", False, ""),
    "short_0xae4daf4e": ("revert", "0x", False, ""),
    "short_0xae69b95b": ("revert", "0x", False, ""),
    "short_0xb67f3dd7": ("revert", "0x", False, ""),
    "short_0xc0c53b8b": ("revert", "0x", False, ""),
    "short_0xca02ff91": ("revert", "0x", False, ""),
    "short_0xd7c7e5fb": ("revert", "0x", False, ""),
    "short_0xe538b280": ("revert", "0x", False, ""),
    "zero_0xd7c7e5fb": ("revert", "0xb0cb274d", False, ""),
}

TEST_CASES = []
for _selector in ASSIGNED["exchange_implementation"]:
    TEST_CASES.append((f"short_{_selector}", "PROXY", "OUTSIDER", f"abi.encodeWithSelector(bytes4({_selector}))", "execSlots", False))
    TEST_CASES.append((f"outsider_{_selector}", "PROXY", "OUTSIDER",
                       f"abi.encodeWithSelector(bytes4({_selector}), {CANONICAL_ARGS[_selector][1:-1]})", "execSlots", False))
for _selector in ASSIGNED["exchange_linked_library_live"]:
    TEST_CASES.append((f"short_{_selector}", "LIBRARY", "OUTSIDER", f"abi.encodeWithSelector(bytes4({_selector}))", "libSlots", False))
    TEST_CASES.append((f"outsider_{_selector}", "LIBRARY", "OUTSIDER",
                       f"abi.encodeWithSelector(bytes4({_selector}), {CANONICAL_ARGS[_selector][1:-1]})", "libSlots", False))
    TEST_CASES.append((f"delegate_{_selector}", "DELEGATOR", "OUTSIDER",
                       f"abi.encodeWithSelector(bytes4({_selector}), {CANONICAL_ARGS[_selector][1:-1]})", "libSlots", False))

EXTRA_CASES = [
    ("owner_0xe538b280", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0xe538b280), uint256(1e16), uint256(2e16), uint256(3e16))", "execSlots", False),
    ("cap_0xe538b280", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0xe538b280), uint256(5e17 + 1), uint256(0), uint256(0))", "execSlots", False),
    ("owner_0xae69b95b", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0xae69b95b), true)", "execSlots", False),
    ("guardian_0xae69b95b", "PROXY", "PAUSE_GUARDIAN", "abi.encodeWithSelector(bytes4(0xae69b95b), true)", "execSlots", False),
    ("guardian_false_0xae69b95b", "PROXY", "PAUSE_GUARDIAN", "abi.encodeWithSelector(bytes4(0xae69b95b), false)", "execSlots", False),
    ("owner_0x2d2451d1", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(0))", "execSlots", False),
    ("invalid_0x2d2451d1", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0x2d2451d1), uint32(2))", "execSlots", False),
    ("owner_0xd7c7e5fb", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0xd7c7e5fb), uint32(0), uint32(1), uint256(1))", "execSlots", False),
    ("zero_0xd7c7e5fb", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0xd7c7e5fb), uint32(0), uint32(0), uint256(1))", "execSlots", False),
    ("owner_0x5ca4c0ea", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0x5ca4c0ea), uint32(0), uint128(1e18), uint96(1), uint96(1), uint64(1))", "execSlots", False),
    ("invalid_0x5ca4c0ea", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0x5ca4c0ea), uint32(2), uint128(1e18), uint96(1), uint96(1), uint64(1))", "execSlots", False),
    ("initialized_0xc0c53b8b", "PROXY", "OUTSIDER", "abi.encodeWithSelector(bytes4(0xc0c53b8b), OUTSIDER, ORACLE, PAPER)", "execSlots", False),
    ("inactive_0x415f1240", "PROXY", "OUTSIDER", "abi.encodeWithSelector(bytes4(0x415f1240), uint256(999999))", "execSlots", False),
    ("farprice_0x415f1240", "PROXY", "OUTSIDER", "abi.encodeWithSelector(bytes4(0x415f1240), uint256(1394473))", "execSlots", False),
    ("boundary_0x415f1240", "PROXY", "OUTSIDER", "abi.encodeWithSelector(bytes4(0x415f1240), uint256(1394473))", "execSlots", False),
    ("out_of_bound_0x415f1240", "PROXY", "OUTSIDER", "abi.encodeWithSelector(bytes4(0x415f1240), type(uint256).max)", "execSlots", False),
    ("owner_0x6a3214c9", "PROXY", "OWNER", "abi.encodeWithSelector(bytes4(0x6a3214c9), USER, uint256(1))", "execSlots", False),
    ("keeper_0x01681a62", "PROXY", "MARKET_KEEPER", "abi.encodeWithSelector(bytes4(0x01681a62), USER)", "execSlots", False),
]
MERGE_CASES = [
    ("merge_0x753a369c", "PROXY", "USER", "abi.encodeWithSelector(bytes4(0x753a369c), USER, uint256(101), uint256(102), uint256(2))", "execSlots", True),
    ("merge_0x827ad94c", "PROXY", "USER", "abi.encodeWithSelector(bytes4(0x827ad94c), USER, uint256(101), uint256(102), uint256(2))", "execSlots", True),
    ("merge_0x4a4d9eea", "PROXY", "USER", "abi.encodeWithSelector(bytes4(0x4a4d9eea), USER, uint256(101), uint256(1))", "execSlots", True),
    ("merge_0xae4daf4e", "PROXY", "USER", "abi.encodeWithSelector(bytes4(0xae4daf4e), USER, uint256(101), uint256(1))", "execSlots", True),
    ("merge_delegate_0x3cf4208d", "DELEGATOR", "USER", "abi.encodeWithSelector(bytes4(0x3cf4208d), uint256(15), USER, uint256(101), uint256(102), uint256(2), uint256(1e18))", "libSlots", True),
    ("merge_delegate_0x32db40c9", "DELEGATOR", "USER", "abi.encodeWithSelector(bytes4(0x32db40c9), uint256(15), USER, uint256(101), uint256(102), uint256(2))", "libSlots", True),
    ("merge_delegate_0xca02ff91", "DELEGATOR", "USER", "abi.encodeWithSelector(bytes4(0xca02ff91), uint256(15), USER, uint256(101), uint256(1))", "libSlots", True),
    ("merge_delegate_0x2448a553", "DELEGATOR", "USER", "abi.encodeWithSelector(bytes4(0x2448a553), uint256(15), USER, uint256(101), uint256(1), uint256(1e18))", "libSlots", True),
]
TEST_CASES.extend(EXTRA_CASES)
TEST_CASES.extend(MERGE_CASES)

# Mock HyperCore BBO precompile runtimes: push bid, push ask, return 64 bytes.
def bbo_code(bid, ask):
    return "0x7f" + hex(bid)[2:].rjust(64, "0") + "6000527f" + hex(ask)[2:].rjust(64, "0") + "60205260406000f3"


PROBE_OVERRIDES = {
    "farprice_0x415f1240": bbo_code(801812, 801812),
    "boundary_0x415f1240": bbo_code(801811, 801811),
    "owner_0x2d2451d1": bbo_code(1_000_000_000, 1_100_000_000),
    "invalid_0x2d2451d1": bbo_code(1_000_000_000, 1_100_000_000),
    "outsider_0x2d2451d1": bbo_code(1_000_000_000, 1_100_000_000),
}
DEFAULT_BBO = bbo_code(801812, 801812)

SOLIDITY_ADDRESSES = {
    "PROXY": PROXY,
    "IMPL": IMPLEMENTATION,
    "LIBRARY": LIBRARY,
    "ORACLE": ORACLE,
    "ORACLE_IMPL": ORACLE_IMPL,
    "TOKENOMICS": TOKENOMICS,
    "TOKENOMICS_IMPL": TOKENOMICS_IMPL,
    "PAPER": PAPER,
    "PAPER_IMPL": PAPER_IMPL,
    "PAPER_MATH": PAPER_MATH,
    "OWNER": OWNER,
    "PAUSE_GUARDIAN": PAUSE_GUARDIAN,
    "MARKET_KEEPER": MARKET_KEEPER,
    "AUTHORIZED_EXECUTOR": AUTHORIZED_EXECUTOR,
    "SESSION": SESSION_KEY_MANAGER,
    "USER": "0x7822efb68be9e458efa6307d3386921b23ac3ade",
    "OUTSIDER": "0x00000000000000000000000000000000000beef0",
    "BBO_PRECOMPILE": BBO_PRECOMPILE,
    "ADMIN": "0xe79c91cc682f1bb401a9cab74c900470190f0f8f",
}
# Pinned storage words, loaded from saved evidence instead of typed by hand:
# the archived liquidation prestate for the Exchange, Tokenomics and PAPER, and
# the pinned instrument probe ledger for the instrument words.
def load_pinned_words():
    """Pinned storage words taken from saved evidence, never typed by hand."""
    liquidation = json.loads((ARTIFACTS.parent / "exchange_liquidation" / "invalid_prices.json").read_text())
    case = next(row for row in liquidation["cases"] if row["name"] == "single_valid")
    watched = case["watched_before"]
    exchange_pre = case["storage_changes"][PROXY]["pre"]
    tokenomics_pre = case["storage_changes"][TOKENOMICS]["pre"]
    paper_pre = case["storage_changes"][PAPER]["pre"]
    instruments = json.loads((ARTIFACTS.parent / "exchange_instrument_admin" / "pinned_probes.json").read_text())["instruments"]
    instrument_0 = next(row for row in instruments if row["id"] == 0)
    instrument_1 = next(row for row in instruments if row["id"] == 1)

    def watched_at(slot):
        return watched["0x" + format(slot, "064x")]

    tokenomics_words = json.loads((ARTIFACTS.parent / "tokenomics_getters" / "pinned_getters.json").read_text())["storage_words"]
    paper_words = json.loads((ARTIFACTS.parent / "paper_token" / "pinned_probes.json").read_text())["slots"]
    words = {
        "position_word_0": watched["0x20fbbd790718f575ee2f828a3b0052c58354260e5f19b5cf02be22a5e604c3aa"],
        "position_word_1": watched["0x20fbbd790718f575ee2f828a3b0052c58354260e5f19b5cf02be22a5e604c3ab"],
        "user_balance": watched["0x37a7cf4208e71d0e3bcc356116ff9d0436609b2cd380019d5adb4ccf576490af"],
        "treasury": watched_at(14),
        "total_balances_and_locked_margin": watched_at(22),
        "liquidation_fee_rate": watched_at(25),
        "fee_accumulators": watched_at(26),
        "instrument_0_word_0": instrument_0["words"][0],
        "instrument_0_word_1": instrument_0["words"][1],
        "instrument_0_word_2": instrument_0["words"][2],
        "instrument_1_word_0": instrument_1["words"][0],
        "tokenomics_slot_0": tokenomics_words["0"],
        "tokenomics_slot_1": tokenomics_words["1"],
        "tokenomics_paper_pointer": "0x" + PAPER[2:].rjust(64, "0"),
        "tokenomics_slot_3": tokenomics_pre["0x" + format(3, "064x")],
        "tokenomics_slot_4": tokenomics_pre["0x" + format(4, "064x")],
        "paper_slot_3_owner": paper_words["3"],
        "paper_slot_4_minter": paper_words["4"],
        "paper_slot_6": paper_pre["0x" + format(6, "064x")],
        "paper_slot_9_staking": paper_words["9"],
        "paper_balance": next(value for key, value in paper_pre.items() if int(key, 16) > 0x100),
    }
    # The archived diffs can trim leading zeros; the raw watched reads must not.
    for name, word in words.items():
        assert re.fullmatch(r"0x[0-9a-f]{64}", word), (name, word)
    assert exchange_pre  # the same case must also carry the proxy diff
    return words


PINNED_WORDS = load_pinned_words()
assert len(PINNED_WORDS) == 21, sorted(PINNED_WORDS)

for _address in SOLIDITY_ADDRESSES.values():
    assert re.fullmatch(r"0x[0-9a-f]{40}", _address), _address
for _name, _word in PINNED_WORDS.items():
    assert re.fullmatch(r"0x[0-9a-f]{64}", _word), (_name, _word)


def address_literal(name):
    return "address(uint160(uint256(0x00" + SOLIDITY_ADDRESSES[name][2:] + ")))"


def word_literal(name):
    return "bytes32(uint256(" + PINNED_WORDS[name] + "))"


ADDRESS_CONSTANTS = "\n".join(
    f"    address constant {name} = {address_literal(name)};" for name in SOLIDITY_ADDRESSES)


TEST_HEADER = """pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function writeFile(string calldata, string calldata) external;
    function toString(bytes32) external pure returns (string memory);
    function toString(bytes calldata) external pure returns (string memory);
    function toString(uint256) external pure returns (string memory);
}
contract Delegator {
    function run(address target, bytes memory data) external returns (bool, bytes memory) {
        return target.delegatecall(data);
    }
}
contract ExchangeSelectorGap {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    bytes32 constant IMPLEMENTATION_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
%ADDRESS_CONSTANTS%
    string resultsPath;

    function node(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(15))); }
    function instrument(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(7))); }
    function position(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(10))); }
    function balanceKey(address user) internal pure returns (bytes32) { return keccak256(abi.encode(user, uint256(9))); }

    function execSlots() internal pure returns (bytes32[] memory slots) {
        slots = new bytes32[](37);
        uint256[15] memory direct = [uint256(0), 1, 2, 8, 14, 18, 19, 22, 23, 24, 25, 26, 29, 37, 88];
        for (uint256 i = 0; i < direct.length; i++) slots[i] = bytes32(direct[i]);
        slots[15] = instrument(0);
        slots[16] = bytes32(uint256(instrument(0)) + 1);
        slots[17] = bytes32(uint256(instrument(0)) + 2);
        slots[18] = instrument(1);
        slots[19] = position(1394473);
        slots[20] = bytes32(uint256(position(1394473)) + 1);
        slots[21] = balanceKey(USER);
        slots[22] = keccak256(abi.encode(uint256(0), uint256(35)));
        slots[23] = keccak256(abi.encode(uint256(0), uint256(33)));
        slots[24] = keccak256(abi.encode(USER, uint256(33)));
        slots[25] = keccak256(abi.encode(uint256(0), uint256(11)));
        slots[26] = keccak256(abi.encode(uint256(0), uint256(31)));
        slots[27] = keccak256(abi.encode(uint256(0), uint256(32)));
        slots[28] = keccak256(abi.encode(uint256(0), uint256(34)));
        slots[29] = keccak256(abi.encode(uint256(0), uint256(36)));
        slots[30] = node(101);
        slots[31] = bytes32(uint256(node(101)) + 1);
        slots[32] = node(102);
        slots[33] = bytes32(uint256(node(102)) + 1);
        slots[34] = keccak256(abi.encode(USER, uint256(19)));
        slots[35] = keccak256(abi.encode(USER, uint256(20)));
        slots[36] = keccak256(abi.encode(USER, uint256(21)));
    }

    function libSlots() internal pure returns (bytes32[] memory slots) {
        slots = new bytes32[](18);
        slots[0] = bytes32(uint256(15));
        slots[1] = bytes32(uint256(16));
        slots[2] = bytes32(uint256(17));
        slots[3] = bytes32(uint256(18));
        slots[4] = node(1);
        slots[5] = bytes32(uint256(node(1)) + 1);
        slots[6] = node(2);
        slots[7] = bytes32(uint256(node(2)) + 1);
        slots[8] = node(3);
        slots[9] = bytes32(uint256(node(3)) + 1);
        slots[10] = keccak256(abi.encode(USER, uint256(19)));
        slots[11] = keccak256(abi.encode(USER, uint256(20)));
        slots[12] = keccak256(abi.encode(USER, uint256(21)));
        slots[13] = keccak256(abi.encode(USER, uint256(22)));
        slots[14] = node(101);
        slots[15] = bytes32(uint256(node(101)) + 1);
        slots[16] = node(102);
        slots[17] = bytes32(uint256(node(102)) + 1);
    }

    function userSlot(uint256 base) internal pure returns (bytes32) { return keccak256(abi.encode(USER, base)); }

    function seedQueue(address target) internal {
        vm.store(target, node(101), bytes32(uint256(uint160(USER)) | (uint256(102) << 160)));
        vm.store(target, bytes32(uint256(node(101)) + 1), bytes32(uint256(300)));
        vm.store(target, node(102), bytes32(uint256(uint160(USER)) | (uint256(101) << 208)));
        vm.store(target, bytes32(uint256(node(102)) + 1), bytes32(uint256(700)));
        vm.store(target, bytes32(uint256(16)), bytes32(uint256(101)));
        vm.store(target, bytes32(uint256(17)), bytes32(uint256(103)));
        vm.store(target, bytes32(uint256(18)), bytes32(uint256(1000)));
        vm.store(target, userSlot(19), bytes32(uint256(1000)));
        vm.store(target, userSlot(20), bytes32(uint256(101)));
        vm.store(target, userSlot(21), bytes32(uint256(102)));
    }

    function snap(address target, bytes32[] memory slots) internal view returns (bytes32) {
        bytes memory buffer = new bytes(slots.length * 32);
        for (uint256 i = 0; i < slots.length; i++) {
            bytes32 value = vm.load(target, slots[i]);
            assembly { mstore(add(add(buffer, 32), mul(i, 32)), value) }
        }
        return keccak256(buffer);
    }

    function dump(address target, bytes32[] memory slots) internal view returns (string memory) {
        string memory out = "";
        for (uint256 i = 0; i < slots.length; i++) {
            out = string.concat(out, i == 0 ? "" : ";",
                vm.toString(slots[i]), ":", vm.toString(vm.load(target, slots[i])));
        }
        return out;
    }

    function logSummary(Vm.Log[] memory logs) internal view returns (string memory) {
        string memory summary = "";
        for (uint256 i = 0; i < logs.length; i++) {
            string memory topic0 = logs[i].topics.length > 0 ? vm.toString(logs[i].topics[0]) : "none";
            summary = string.concat(summary,
                i == 0 ? "" : ";",
                vm.toString(uint256(uint160(logs[i].emitter))),
                ":", topic0, ":", vm.toString(logs[i].topics.length), ":", vm.toString(logs[i].data.length));
        }
        return summary;
    }

    function chain(string memory a, string memory b) internal pure returns (string memory) {
        return bytes(a).length == 0 ? b : string.concat(a, "|", b);
    }

    function run(string memory name, address target, address caller, bytes memory data, bool seeded) internal {
        if (seeded) seedQueue(target);
        bytes32[] memory slots = target == LIBRARY ? libSlots() : execSlots();
        string memory slotsBefore = dump(target, slots);
        bytes32 before = snap(target, slots);
        vm.recordLogs();
        vm.prank(caller);
        (bool ok, bytes memory output) = target.call(data);
        vm.writeFile(string.concat(resultsPath, "/", name, ".txt"),
            string.concat("status=", ok ? "ok" : "revert",
            "\\ndata=", vm.toString(output),
            "\\nlogs=", logSummary(vm.getRecordedLogs()),
            "\\nfp_before=", vm.toString(before),
            "\\nfp_after=", vm.toString(snap(target, slots)),
            "\\nslots_before=", slotsBefore,
            "\\nslots_after=", dump(target, slots)));
    }

    function setUp() public {
        resultsPath = "results";
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(IMPL, vm.parseBytes(vm.readFile("runtime/Implementation.hex")));
        vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        vm.etch(ORACLE, vm.parseBytes(vm.readFile("runtime/Oracle.hex")));
        vm.etch(ORACLE_IMPL, vm.parseBytes(vm.readFile("runtime/OracleImplementation.hex")));
        vm.etch(TOKENOMICS, vm.parseBytes(vm.readFile("runtime/Tokenomics.hex")));
        vm.etch(TOKENOMICS_IMPL, vm.parseBytes(vm.readFile("runtime/TokenomicsImplementation.hex")));
        vm.etch(PAPER, vm.parseBytes(vm.readFile("runtime/Paper.hex")));
        vm.etch(PAPER_IMPL, vm.parseBytes(vm.readFile("runtime/PaperImplementation.hex")));
        vm.etch(PAPER_MATH, vm.parseBytes(vm.readFile("runtime/PaperMath.hex")));
        vm.store(PROXY, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        vm.store(PROXY, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(IMPL))));
        vm.store(ORACLE, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(ORACLE_IMPL))));
        vm.store(TOKENOMICS, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(TOKENOMICS_IMPL))));
        vm.store(PAPER, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(PAPER_IMPL))));
        // pinned Exchange words
        vm.store(PROXY, bytes32(0), bytes32((uint256(uint160(OWNER)) << 16) | 1));
        vm.store(PROXY, bytes32(uint256(1)), bytes32(uint256(uint160(PAUSE_GUARDIAN))));
        vm.store(PROXY, bytes32(uint256(2)), bytes32(uint256(uint160(ORACLE))));
        vm.store(PROXY, bytes32(uint256(6)), bytes32(uint256(uint160(TOKENOMICS))));
        vm.store(PROXY, bytes32(uint256(8)), bytes32(uint256(2)));
        vm.store(PROXY, bytes32(uint256(14)), %treasury%);
        vm.store(PROXY, bytes32(uint256(18)), 0);
        vm.store(PROXY, bytes32(uint256(22)), %total_balances_and_locked_margin%);
        vm.store(PROXY, bytes32(uint256(23)), bytes32(uint256(2e16)));
        vm.store(PROXY, bytes32(uint256(24)), bytes32(uint256(2e16)));
        vm.store(PROXY, bytes32(uint256(25)), %liquidation_fee_rate%);
        vm.store(PROXY, bytes32(uint256(26)), %fee_accumulators%);
        vm.store(PROXY, bytes32(uint256(29)), bytes32(uint256(uint160(SESSION)) << 8));
        vm.store(PROXY, bytes32(uint256(37)), bytes32(uint256(uint160(MARKET_KEEPER))));
        vm.store(PROXY, bytes32(uint256(88)), bytes32(uint256(uint160(AUTHORIZED_EXECUTOR))));
        vm.store(PROXY, instrument(0), %instrument_0_word_0%);
        vm.store(PROXY, bytes32(uint256(instrument(0)) + 1), %instrument_0_word_1%);
        vm.store(PROXY, bytes32(uint256(instrument(0)) + 2), %instrument_0_word_2%);
        vm.store(PROXY, instrument(1), %instrument_1_word_0%);
        vm.store(PROXY, position(1394473), %position_word_0%);
        vm.store(PROXY, bytes32(uint256(position(1394473)) + 1), %position_word_1%);
        vm.store(PROXY, balanceKey(USER), %user_balance%);
        // pinned Tokenomics and PAPER words from the archived liquidation prestate
        vm.store(TOKENOMICS, bytes32(uint256(3)), %tokenomics_slot_3%);
        vm.store(TOKENOMICS, bytes32(uint256(4)), %tokenomics_slot_4%);
        vm.store(TOKENOMICS, bytes32(0), bytes32(uint256(%tokenomics_slot_0%)));
        vm.store(TOKENOMICS, bytes32(uint256(1)), %tokenomics_slot_1%);
        vm.store(TOKENOMICS, bytes32(uint256(2)), %tokenomics_paper_pointer%);
        vm.store(PAPER, bytes32(uint256(3)), %paper_slot_3_owner%);
        vm.store(PAPER, bytes32(uint256(4)), %paper_slot_4_minter%);
        vm.store(PAPER, bytes32(uint256(9)), %paper_slot_9_staking%);
        vm.store(PAPER, bytes32(uint256(6)), %paper_slot_6%);
        vm.store(PAPER, 0xe567d5326fdde87864781de7be41927ba45ea21033a6e650bdd93891a6ba1d5c, %paper_balance%);
        // library queue baseline for direct library calls
        vm.store(LIBRARY, bytes32(uint256(16)), 0);
        vm.store(LIBRARY, bytes32(uint256(17)), bytes32(uint256(1)));
        vm.store(LIBRARY, bytes32(uint256(18)), 0);
        // default HyperCore BBO response
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("%DEFAULT_BBO%"));
    }

    function runDelegated(string memory name, address caller, bytes memory data, bool seeded) internal {
        Delegator delegator = new Delegator();
        if (seeded) {
            seedQueue(address(delegator));
        } else {
            vm.store(address(delegator), bytes32(uint256(16)), 0);
            vm.store(address(delegator), bytes32(uint256(17)), bytes32(uint256(1)));
            vm.store(address(delegator), bytes32(uint256(18)), 0);
        }
        bytes32[] memory slots = libSlots();
        string memory slotsBefore = dump(address(delegator), slots);
        bytes32 before = snap(address(delegator), slots);
        vm.recordLogs();
        vm.prank(caller);
        (bool ok, bytes memory output) = delegator.run(LIBRARY, data);
        vm.writeFile(string.concat(resultsPath, "/", name, ".txt"),
            string.concat("status=", ok ? "ok" : "revert",
            "\\ndata=", vm.toString(output),
            "\\nlogs=", logSummary(vm.getRecordedLogs()),
            "\\nfp_before=", vm.toString(before),
            "\\nfp_after=", vm.toString(snap(address(delegator), slots)),
            "\\nslots_before=", slotsBefore,
            "\\nslots_after=", dump(address(delegator), slots)));
    }

    function caseFn(string memory name, address target, address caller, bytes memory data, bool seeded) internal {
        if (target == LIBRARY) vm.etch(LIBRARY, vm.parseBytes(vm.readFile("runtime/Library.hex")));
        if (target == address(0)) {
            runDelegated(name, caller, data, seeded);
            return;
        }
        run(name, target, caller, data, seeded);
    }
"""


def build_test_source():
    header = TEST_HEADER.replace("%ADDRESS_CONSTANTS%", ADDRESS_CONSTANTS)
    header = header.replace("%DEFAULT_BBO%", DEFAULT_BBO)
    for name, word in PINNED_WORDS.items():
        header = header.replace(f"%{name}%", word_literal(name))
    assert "%" not in header.split("pragma", 1)[1].replace("%DEFAULT", "%"), header[header.index("%"):header.index("%") + 40]
    lines = [header]
    for name, target, caller, expression, _, seeded in TEST_CASES:
        target_text = "address(0)" if target == "DELEGATOR" else target
        seed_text = "true" if seeded else "false"
        lines.append(f"""
    function test_{name}() public {{
        vm.etch(BBO_PRECOMPILE, vm.parseBytes("{PROBE_OVERRIDES.get(name, DEFAULT_BBO)}"));
        caseFn("{name}", {target_text}, {caller}, {expression}, {seed_text});
    }}""")
    lines.append("}\n")
    return "".join(lines)


def parse_results(directory):
    results = {}
    for path in sorted(directory.glob("*.txt")):
        fields = {}
        for line in path.read_text().splitlines():
            key, _, value = line.partition("=")
            fields[key] = value
        results[path.stem] = fields
    return results


def run_forge(runtime_files, test_source, extra_dirs=()):
    """Execute the generated suite in a throwaway offline Foundry project."""
    foundry = shutil.which("forge")
    solc = shutil.which("solc")
    assert foundry and solc, "forge and solc are required for the replay layer"
    with tempfile.TemporaryDirectory(prefix="papertrade-selector-gap-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "results").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc) +
            "\noffline = true\noptimizer = true\nvia_ir = true\nfs_permissions = [{ access = \"read\", path = \"./runtime\" },"
            " { access = \"write\", path = \"./results\" }]\n")
        (project / "test" / "ExchangeSelectorGap.t.sol").write_text(test_source)
        for name, code in runtime_files.items():
            (project / "runtime" / f"{name}.hex").write_text(code)
        run = subprocess.run([foundry, "test", "--root", tmp, "-vv"], capture_output=True,
                             text=True, timeout=600)
        output = run.stdout + "\n" + run.stderr
        passed = set(re.findall(r"\[PASS\] (test_\w+)\(\)", output))
        expected = {f"test_{case[0]}" for case in TEST_CASES}
        if run.returncode or passed != expected:
            raise RuntimeError("selector gap replay failed: " + output[-5000:])
        results = parse_results(project / "results")
        # keep a copy of the generated suite and the raw records
        (ARTIFACTS / "replay").mkdir(parents=True, exist_ok=True)
        (ARTIFACTS / "replay" / "ExchangeSelectorGap.t.sol").write_text(test_source)
        for name, fields in results.items():
            (ARTIFACTS / "replay" / f"{name}.txt").write_text(
                "\n".join(f"{k}={v}" for k, v in fields.items()) + "\n")
    return passed, results, output


# ---------------------------------------------------------------------------
# Per-selector record: documented behaviour plus what this run established
# ---------------------------------------------------------------------------

EXTRA_PROBES = {
    "0x01681a62": ["keeper_0x01681a62"],
    "0x2d2451d1": ["invalid_0x2d2451d1"],
    "0x415f1240": ["inactive_0x415f1240", "farprice_0x415f1240", "boundary_0x415f1240", "out_of_bound_0x415f1240"],
    "0x5ca4c0ea": ["invalid_0x5ca4c0ea"],
    "0x6a3214c9": ["owner_0x6a3214c9"],
    "0xae69b95b": ["guardian_0xae69b95b", "guardian_false_0xae69b95b"],
    "0xc0c53b8b": ["initialized_0xc0c53b8b"],
    "0xd7c7e5fb": ["zero_0xd7c7e5fb"],
    "0xe538b280": ["cap_0xe538b280"],
}

DOCUMENTED = {
    "0x01681a62": {
        "name_status": "behaviour_reconstruction_not_registry",
        "behaviour": "sweep(user) follows requestSweep when no pending request exists and finalizeSweep otherwise; both paths are reconstructed in exchange_sweep_pseudocode.md.",
        "writes": ["pendingSweep mapping (base 33) and lastSweepBlock mapping (base 32) on the request path",
                   "treasury (14), totalBalances (22 low 128 bits) and balances[user] mapping (base 9) on the finalization path"],
        "events": ["0x02d61879 site SweepRequested(address,address,uint64,uint64,uint32)",
                   "0xc36b5179 site Swept(address,uint256)",
                   "0x28f3adb5 site PendingSweepCleared(address,address)"],
        "refs": ["atlas/block_48902346/exchange_sweep_pseudocode.md", "atlas/block_48902346/exchange_sweep_behavior.json",
                 "artifacts/exchange_sweep_archive_local/", "atlas/block_48902346/exchange_getters.md"],
        "undecided": ["No saved historical call of selector 0x01681a62 exists in the sampled transaction history.",
                      "The success path needs the factory proxy and mocked HyperCore reads, so this replay only records the rejection branch."],
    },
    "0x2d2451d1": {
        "name_status": "behaviour_reconstruction_not_registry",
        "behaviour": "pauseMarket(id) sets a per-market packed pause word after reading the market price from the oracle.",
        "writes": ["marketPause mapping (keccak(abi.encode(id, 35))): flag bits 0..7, bid 8..71, ask 72..135, timestamp 136..199"],
        "events": ["0x25e933a2 site unnamed (indexed uint32 id, three unindexed words)"],
        "refs": ["atlas/block_48902346/exchange_pause_pseudocode.md", "artifacts/exchange_pause_local/replay.json"],
        "undecided": ["The event's Solidity name is unknown; the full-history log query returned no successful emission."],
    },
    "0x415f1240": {
        "name_status": "hash_matched_public_abi_fixture",
        "behaviour": "liquidate(id) settles one active position that is outside its price boundary; liquidateBatch shares the settlement path.",
        "writes": ["position mapping (base 10) second word bit 240 cleared, accounting slots and the Tokenomics/PAPER side on the settlement path"],
        "events": ["Liquidated on the settlement path, plus PAPER Transfer and the Tokenomics liquidation event"],
        "refs": ["atlas/block_48902346/exchange_liquidation_pseudocode.md", "artifacts/exchange_liquidation/pinned_local_probes.json",
                 "artifacts/exchange_liquidation/invalid_prices.json"],
        "undecided": ["No historical single-position liquidate call is saved; all 26 saved batch traces are for liquidateBatch.",
                      "The port-free run passes the price predicate at the documented boundary price and then reverts with 0x924d25e6, a four-byte value that appears in no captured runtime, so the successful settlement stays with the archive-backed probe."],
    },
    "0x4a4d9eea": {
        "name_status": "unresolved",
        "behaviour": "Delegatecalls the linked library selector 0xca02ff91 with words (15, user, start, count): headward count-based queue consolidation.",
        "writes": ["queue node mapping (base 15) at the delegatecall target: merged node amount and packed links; this replay reproduces five proxy writes in a two-node state"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_adapters.md", "atlas/block_48902346/exchange_library_queue_count_merge.md"],
        "undecided": ["Both the Exchange wrapper and the library function keep their source names.", "Argument semantics beyond the tested counts remain unproven."],
    },
    "0x5ca4c0ea": {
        "name_status": "unresolved",
        "behaviour": "Owner-only instrument update writing four fields of instruments(id) in one call.",
        "writes": ["instruments mapping (base 7) word 0 bits 0..191, word 1 bits 184..247, word 2 low 128 bits"],
        "events": ["0x76a31977 site unnamed (indexed uint32 id, four unindexed values)"],
        "refs": ["atlas/block_48902346/exchange_instrument_admin.md", "artifacts/exchange_instrument_admin_local/replay.json"],
        "undecided": ["Function and event names, and the economic meaning of the four fields, remain unresolved."],
    },
    "0x6a3214c9": {
        "name_status": "behaviour_reconstruction_not_registry",
        "behaviour": "Owner-only reconciliation that credits amount * collateralScale after the pending sweep word is clear.",
        "writes": ["treasury (14), totalBalances (22) and balances[user] (base 9) on the documented credit path"],
        "events": ["one unnamed credit event in the documented probe"],
        "refs": ["atlas/block_48902346/exchange_sweep_recovery.md", "artifacts/audit_sweep_recovery_local/replay.json"],
        "undecided": ["In this run's fresh synthetic state the owner call returns success with no write and no log, so the credit precondition is not reproduced here.",
                      "The historical recovery need is open: both saved pending users reject owner reconciliation and clearPendingSweep(address) is absent."],
    },
    "0x753a369c": {
        "name_status": "unresolved",
        "behaviour": "Delegatecalls the linked library selector 0x3cf4208d with words (15, user, start, end, limit, 10^18): forward range merge.",
        "writes": ["queue node mapping (base 15) at the target: five proxy writes in the two-node case, nine in the three-node case; this replay reproduces the five-write two-node case"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_queue_merge.md", "atlas/block_48902346/exchange_library_queue_interleaved.md"],
        "undecided": ["Names stay unresolved; the fixed 10^18 word and the last argument's full meaning remain unproven."],
    },
    "0x827ad94c": {
        "name_status": "unresolved",
        "behaviour": "Delegatecalls the linked library selector 0x32db40c9 with words (15, user, start, end, limit): reverse range merge.",
        "writes": ["queue node mapping (base 15) at the target: five proxy writes in the two-node case, ten in the three-node case; this replay reproduces the five-write two-node case"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_queue_merge.md", "atlas/block_48902346/exchange_library_queue_interleaved.md"],
        "undecided": ["Names stay unresolved; the reverse direction rejects an A, B, A range in the sampled state."],
    },
    "0xae4daf4e": {
        "name_status": "unresolved",
        "behaviour": "Delegatecalls the linked library selector 0x2448a553 with words (15, user, start, count, 10^18): tailward count-based queue consolidation.",
        "writes": ["queue node mapping (base 15) at the target on the merge paths; this replay reproduces five writes in a two-node state"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_queue_count_merge.md"],
        "undecided": ["Names stay unresolved; the strict 10^18 amount threshold is checked only in the sampled states."],
    },
    "0xae69b95b": {
        "name_status": "behaviour_reconstruction_not_registry",
        "behaviour": "setTradingPaused(bool): owner may set and clear, the pause guardian may only set.",
        "writes": ["slot 29 low byte; upper bytes keep the SessionKeyManager address shifted by 8"],
        "events": ["0xa4abec92 site TradingPausedUpdated(bool), one unindexed word"],
        "refs": ["atlas/block_48902346/exchange_pause_pseudocode.md", "artifacts/exchange_pause_local/replay.json"],
        "undecided": ["No historical call or successful emission exists through the pin; attempted or reverted calls cannot be excluded."],
    },
    "0xc0c53b8b": {
        "name_status": "hash_matched_public_abi_fixture",
        "behaviour": "initialize(owner, oracle, token) in a fresh proxy: writes owner, pause guardian, oracle, decimal scale and fee defaults after a token decimals() call.",
        "writes": ["slots 0, 1, 2, 3, 4 low byte, 5, 17, 23, 24, 25, 28 in the documented fresh state"],
        "events": ["OwnerUpdated(address)"],
        "refs": ["atlas/block_48902346/exchange_initializer.md", "artifacts/exchange_initializer_local/replay.json"],
        "undecided": ["The exact alias source names are not proven; the token address is not observed inside the tested slots.",
                      "The pin's proxy is already initialized, so only the rejection branch is replayed here."],
    },
    "0xd7c7e5fb": {
        "name_status": "unresolved",
        "behaviour": "Owner-only setter replacing two packed fields of instruments(id).",
        "writes": ["instruments mapping (base 7) word 0 bits 224..255 and word 1 bits 0..119"],
        "events": ["0x62db1b2b site unnamed (indexed uint32 id, two unindexed words)"],
        "refs": ["atlas/block_48902346/exchange_instrument_limit.md", "artifacts/exchange_instrument_limit_local/replay.json"],
        "undecided": ["Function, event and field names remain unresolved."],
    },
    "0xe538b280": {
        "name_status": "behaviour_reconstruction_not_registry",
        "behaviour": "Owner-only setFeeRates(first, second, third), each rate at most 0.5 * 10^18.",
        "writes": ["slots 23, 24 and 25"],
        "events": ["0xe4af0531 site FeeRatesUpdated(uint256,uint256,uint256), three unindexed words"],
        "refs": ["atlas/block_48902346/exchange_fee_rates.md", "atlas/block_48902346/exchange_fee_rates_behavior.json"],
        "undecided": ["Slot 23's getter name stays unknown; slot 24's name comes from the Guardian report, not from a bytecode match.",
                      "No historical call or successful emission exists through the pin."],
    },
    "0x18958ce2": {
        "name_status": "unresolved",
        "behaviour": "Library enqueue(base, user, amount): creates a queue node, links it, and adds to the global and user totals.",
        "writes": ["global head/tail/next-id/total words, the node mapping at the base slot, and the user head/tail/total words"],
        "events": ["Enqueued(address,uint256,uint256) at topic 0xb2f6a0be, hash-checked and present in the library runtime"],
        "refs": ["atlas/block_48902346/exchange_library_remaining.md", "artifacts/exchange_library_remaining_local/replay.json",
                 "artifacts/historical/replays/"],
        "undecided": ["The source name stays unresolved; the arithmetic selector beside it is the only library row with a plain success on a direct call."],
    },
    "0x2448a553": {
        "name_status": "unresolved",
        "behaviour": "Library tailward count-based merge, called by Exchange 0xae4daf4e with a fixed 10^18 word.",
        "writes": ["queue node amounts and packed links at the base slot; this replay reproduces five writes in a two-node state"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_queue_count_merge.md", "artifacts/exchange_library_queue_count_merge_local/replay.json"],
        "undecided": ["Names stay unresolved; the strict 10^18 boundary is checked in sampled amounts only."],
    },
    "0x32db40c9": {
        "name_status": "unresolved",
        "behaviour": "Library reverse range merge, called by Exchange 0x827ad94c.",
        "writes": ["queue node amounts and packed links at the base slot; this replay reproduces five writes in a two-node state"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_queue_merge.md"],
        "undecided": ["Names stay unresolved; the range bound and its error mapping are sampled."],
    },
    "0x3cf4208d": {
        "name_status": "unresolved",
        "behaviour": "Library forward range merge, called by Exchange 0x753a369c.",
        "writes": ["queue node amounts and packed links at the base slot; this replay reproduces five writes in a two-node state"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_queue_merge.md"],
        "undecided": ["Names stay unresolved; larger ranges and the limit-1 rejection are the only checked bounds."],
    },
    "0x3f4e3626": {
        "name_status": "unresolved",
        "behaviour": "Library dequeue(base, user, amount): clears or reduces the user's newest queue node and advances the global head.",
        "writes": ["global head and next-id words plus the node amount at the base slot"],
        "events": ["0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d, indexed by user with the requested amount as data"],
        "refs": ["atlas/block_48902346/exchange_library_remaining.md"],
        "undecided": ["The event name and its exact source type remain unresolved; an over-request emits the requested amount, not the cleared amount."],
    },
    "0xb67f3dd7": {
        "name_status": "unresolved",
        "behaviour": "Seven-word arithmetic function returning one word; the checked integer order matches 40 vectors and an archived opcode trace.",
        "writes": [],
        "events": [],
        "refs": ["atlas/block_48902346/exchange_library_remaining.md", "artifacts/exchange_library_remaining_local/opcode_trace17.json"],
        "undecided": ["Argument labels are placeholders; extreme inputs and the source name remain open.",
                      "cast classifies it payable, but both a direct call and a delegatecall return a word and write nothing."],
    },
    "0xca02ff91": {
        "name_status": "unresolved",
        "behaviour": "Library headward count-based merge, called by Exchange 0x4a4d9eea.",
        "writes": ["queue node amounts and packed links at the base slot on the merge paths"],
        "events": ["0xb8c6723c site merge move", "0xf949f116 site merge summary"],
        "refs": ["atlas/block_48902346/exchange_library_queue_count_merge.md"],
        "undecided": ["Names stay unresolved; a later node belonging to another user stops the count-based path in the sampled states."],
    },
}

GUARD_EVIDENCE = {
    "0x01681a62": "an outsider and the pinned market keeper both reach the same 0x967d697b rejection, so no caller check is in front of the path",
    "0x2d2451d1": "owner and pause guardian succeed, an outsider gets NotPauseAuthority()",
    "0x415f1240": "an outsider reaches the price predicate, so the entrypoint is caller-permissionless in the tested state",
    "0x4a4d9eea": "an outsider call succeeds and returns the library words, so no caller check guards the wrapper",
    "0x5ca4c0ea": "an outsider gets NotOwner()",
    "0x6a3214c9": "an outsider gets NotOwner()",
    "0x753a369c": "an outsider call reaches the library range error, not an authorization error",
    "0x827ad94c": "an outsider call reaches the library range error, not an authorization error",
    "0xae4daf4e": "an outsider call succeeds and returns the library words, so no caller check guards the wrapper",
    "0xae69b95b": "owner and pause guardian may pause, the guardian and an outsider get NotPauseAuthority() when clearing",
    "0xc0c53b8b": "any caller reaches the initialized-state rejection, so the entry has no caller check",
    "0xd7c7e5fb": "an outsider gets NotOwner()",
    "0xe538b280": "an outsider gets NotOwner()",
    "0x18958ce2": "zero CALLER instructions exist in the whole library runtime; a direct call reverts while a delegatecall executes",
    "0x2448a553": "zero CALLER instructions exist in the whole library runtime; a direct call reverts while a delegatecall executes",
    "0x32db40c9": "zero CALLER instructions exist in the whole library runtime; a direct call reverts while a delegatecall executes",
    "0x3cf4208d": "zero CALLER instructions exist in the whole library runtime; a direct call reverts while a delegatecall executes",
    "0x3f4e3626": "zero CALLER instructions exist in the whole library runtime; a direct call reverts while a delegatecall executes",
    "0xb67f3dd7": "zero CALLER instructions exist in the whole library runtime; this pure path succeeds on a direct call as well",
    "0xca02ff91": "zero CALLER instructions exist in the whole library runtime; a direct call reverts while a delegatecall executes",
}

def mapping_slot(base, key):
    """keccak256(abi.encode(key, base)) for a mapping stored in a direct slot."""
    key_word = format(int(key), "064x")
    base_word = format(int(base), "064x")
    digest = subprocess.run(["cast", "keccak", "0x" + key_word + base_word],
                            capture_output=True, text=True, check=True).stdout.strip()
    return "0x" + digest.removeprefix("0x")


def slot_labels():
    labels = {key: value for key, value in ROLE_LABELS.items()}
    user = int("7822efb68be9e458efa6307d3386921b23ac3ade", 16)
    for base, name in ((33, "pendingSweep mapping"), (35, "marketPause mapping"),
                       (36, "market field mapping"), (32, "lastSweepBlock mapping"),
                       (31, "mapping 31"), (34, "mapping 34")):
        labels[int(mapping_slot(str(base), "0"), 16)] = f"{name} key 0"
    for base in (19, 20, 21, 22):
        labels[int(mapping_slot(base, user), 16)] = f"queue user word at mapping base {base}"
    for node_id in (1, 2, 3, 101, 102):
        packed = int(mapping_slot(15, node_id), 16)
        labels[packed] = f"queue node {node_id} packed links"
        labels[packed + 1] = f"queue node {node_id} amount"
    for position_id in (1394473,):
        packed = int(mapping_slot(10, position_id), 16)
        labels[packed] = f"position {position_id} word 0"
        labels[packed + 1] = f"position {position_id} word 1"
    for instrument_id in (0, 1):
        packed = int(mapping_slot(7, instrument_id), 16)
        for offset in range(3):
            labels[packed + offset] = f"instruments({instrument_id}) word {offset}"
    return labels


LABELS = {}


def slot_label(slot):
    value = int(slot, 16)
    return ROLE_LABELS.get(value) or LABELS.get(value, "")


ROLE_LABELS = {
    0: "slot 0 packed owner and initialized flag", 1: "slot 1 pause guardian", 8: "slot 8 instrument count",
    15: "slot 15 queue node mapping base", 16: "slot 16 queue global head", 17: "slot 17 queue next node id",
    18: "slot 18 queue global total",
    14: "slot 14 treasury", 18: "slot 18 total queued", 19: "slot 19 balances mapping key",
    22: "slot 22 total balances and locked margin", 23: "slot 23 fee rate (unnamed)",
    24: "slot 24 fee rate (guardian report name winFeeRate)", 25: "slot 25 liquidation fee rate",
    26: "slot 26 staker and dev fee accumulators", 29: "slot 29 packed trading-paused word",
    37: "slot 37 market keeper", 88: "slot 88 authorized executor",
}

def value_pairs(text):
    return {key: value for key, value in (item.split(":", 1) for item in text.split(";") if item)}


def changed_slots(record):
    before = value_pairs(record.get("slots_before", ""))
    after = value_pairs(record.get("slots_after", ""))
    out = []
    for key in before:
        if before[key] != after.get(key):
            out.append({"slot": key, "before": before[key], "after": after.get(key)})
    return out


def log_entries(record):
    entries = []
    for item in record.get("logs", "").split(";"):
        if not item:
            continue
        emitter, topic0, topic_count, data_length = item.split(":")
        entries.append({"emitter": emitter, "topic0": topic0,
                        "topic_count": int(topic_count), "data_bytes": int(data_length)})
    return entries


def case_name(prefix, selector):
    return f"{prefix}_{selector}"


def build_rows(static, replay):
    rows = []
    for role, selectors in ASSIGNED.items():
        for selector in selectors:
            facts = static["rows"][selector]
            documented = DOCUMENTED[selector]
            outsider = replay[case_name("outsider", selector)]
            short = replay[case_name("short", selector)]
            owner_case = replay.get(case_name("owner", selector))
            delegate = replay.get(case_name("delegate", selector))
            rejection = {
                "short_calldata_probe": case_name("short", selector),
                "short_calldata_outcome": short["status"],
                "short_calldata_revert_data": short["data"],
                "caller_probe": case_name("outsider", selector),
                "caller_probe_outcome": outsider["status"],
                "caller_probe_revert_data": outsider["data"],
                "state_changed": outsider["fp_before"] != outsider["fp_after"],
            }
            merge_names = (case_name("merge", selector), "merge_delegate_" + selector, "merge_" + selector)
            merge_cases = list(dict.fromkeys(name for name in merge_names if name in replay))
            probes = [(case_name("outsider", selector), outsider),
                      (case_name("owner", selector), owner_case),
                      (case_name("delegate", selector), delegate)] + \
                     [(name, replay[name]) for name in merge_cases]
            writes = []
            for name, record in probes:
                if not record:
                    continue
                for change in changed_slots(record):
                    label = slot_label(change["slot"])
                    writes.append({"probe": name, "slot": change["slot"], "slot_label": label,
                                   "before": change["before"], "after": change["after"],
                                   "source": "this replay"})
            events = []
            for name, record in probes:
                if not record:
                    continue
                for entry in log_entries(record):
                    if entry["emitter"] == "0":
                        continue
                    events.append({"probe": name, "topic0": entry["topic0"],
                                   "topic_count": entry["topic_count"], "data_bytes": entry["data_bytes"],
                                   "name_status": "unnamed" if entry["topic0"] not in TOPIC_NAMES else TOPIC_NAMES[entry["topic0"]],
                                   "source": "this replay"})
            abi = {
                "calldata_words": facts["calldata_words"],
                "calldata_min_bytes": facts["calldata_min_bytes"],
                "calldata_offsets_read": facts["calldata_offsets_read"],
                "return_words": (len(outsider["data"]) - 2) // 64 if outsider["status"] == "ok" else None,
                "source": "canonical ABI length constant and calldata offsets in the pinned runtime bytes, checked by the replay",
            }
            guard = {
                "role": facts["guard"]["role"],
                "evidence": GUARD_EVIDENCE[selector],
                "static_caller_checks": facts["guard"]["checks"],
                "library_caller_instructions": static["caller_census"]["library_caller_instructions"] if role == "exchange_linked_library_live" else None,
                "source": "exact-runtime caller probes plus the caller check sites recovered from the pinned bytes",
            }
            probe_outcomes = {}
            for name in ("short_" + selector, "outsider_" + selector, "owner_" + selector,
                         "delegate_" + selector) + tuple(merge_cases) + tuple(EXTRA_PROBES.get(selector, [])):
                record = replay.get(name)
                if record is None:
                    continue
                probe_outcomes[name] = {"status": record["status"], "output_or_revert": record["data"],
                                        "state_changed": record["fp_before"] != record["fp_after"],
                                        "log_count": len(log_entries(record))}
            row = {
                "role": role,
                "address": facts["runtime_address"],
                "selector": selector,
                "runtime_sha256": facts["runtime_sha256"],
                "entry_pc": facts["entry_pc"],
                "name_status": documented["name_status"],
                "candidate_signature": NAME_CANDIDATES[selector][0],
                "name_hash_checked": static["name_checks"][selector]["hash_checked"],
                "name_source": NAME_CANDIDATES[selector][1],
                "abi_shape": abi,
                "guard": guard,
                "documented_behaviour": documented["behaviour"],
                "writes": writes if writes else [{"source": "none observed in this replay"}],
                "documented_writes": documented["writes"],
                "events": events if events else [{"source": "none observed in this replay"}],
                "documented_events": documented["events"],
                "evidence_tier": "exact_runtime_replay",
                "evidence_tier_reason": (
                    "no saved historical call graph or root transaction for this selector exists in the "
                    "sampled history, so the behaviour record rests on the pinned-byte static read plus "
                    "this port-free replay"),
                "rejection_branch": rejection,
                "probe_outcomes": probe_outcomes,
                "evidence_refs": documented["refs"] + ["artifacts/selector_gap_exchange/replay/" + name + ".txt"
                                                       for name in probe_outcomes],
                "undecided": documented["undecided"] + ([] if writes else
                                                        ["No write set is observed on the probed path; the documented write set comes from the cited artifacts."]),
                "synthetic": True,
            }
            rows.append(row)
    return rows


TOPIC_NAMES = {
    "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7": "Enqueued(address,uint256,uint256) (hash-checked, present in the library runtime)",
    "0xe4af0531d4ba8c578b5076b042e4505372fb4f4986aea8ebf77f4ff1585e3e75": "FeeRatesUpdated(uint256,uint256,uint256) (behaviour reconstruction, hash-checked)",
    "0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e": "TradingPausedUpdated(bool) (behaviour reconstruction, hash-checked)",
    "0x6b3ffd50ed0810416007b5dbbae587b9d8801c50bf8065cda8eb82011bed314e": "PauseGuardianUpdated(address) (hash-checked)",
    "0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d": "unnamed library dequeue event",
}


def render_doc(ledger, observed_reverts):
    lines = [
        f"# Untraced Exchange and linked-library selector behaviour at block {ledger['pin']}",
        "",
        "This page records the "
        f"{ledger['assigned_selector_count']} selectors that the [coverage ledger](selector_coverage.md) lists as "
        "non-view selectors without a saved historical trace, for the Exchange implementation and the live linked "
        "library. The machine ledger is [selector_gap_exchange.json](selector_gap_exchange.json). It is generated by "
        "`atlas_selector_gap_exchange.py`, which runs offline.",
        "",
        "Each row rests on three layers, in this order of strength: an exact-runtime replay of the pinned proxy, "
        "implementation and linked library in a port-free Forge EVM (synthetic, never a historical transaction); a "
        "disassembly read of the pinned runtime bytes for the calldata shape, the caller guards and the constant "
        "data; and the behaviour artifacts already in the atlas. No assigned selector has a saved historical call "
        "graph or root transaction, so no row claims historical-trace evidence.",
        "",
        "## Assigned rows",
        "",
        "| Selector | Runtime role | Name status | Calldata words | Guard | Writes in the replay | Events in the replay |",
        "|---|---|---|---:|---|---:|---:|",
    ]
    for row in ledger["rows"]:
        writes = len([entry for entry in row["writes"] if "slot" in entry])
        events = len([entry for entry in row["events"] if "topic0" in entry])
        lines.append(f"| `{row['selector']}` | `{row['role']}` | {row['name_status']} | "
                     f"{row['abi_shape']['calldata_words']} | {row['guard']['role']} | {writes} | {events} |")
    lines += [
        "",
        "Every row also has a short-calldata probe that reverts with empty data, so the canonical ABI length check "
        "is exercised for all twenty selectors.",
        "",
        "## Per-selector records",
        "",
    ]
    for row in ledger["rows"]:
        title = row["candidate_signature"] or "unnamed"
        lines += [f"### `{row['selector']}` {title} ({row['role']})", "",
                  f"- Name: {row['name_status']}; candidate `{row['candidate_signature'] or 'none'}`, "
                  f"hash-checked against the selector: {row['name_hash_checked']}. Source: {row['name_source']}.",
                  f"- ABI shape: {row['abi_shape']['calldata_words']} argument word(s), at least "
                  f"{row['abi_shape']['calldata_min_bytes']} calldata bytes, offsets read "
                  f"{row['abi_shape']['calldata_offsets_read']}; return words on the accepted probe: "
                  f"{row['abi_shape']['return_words']}.",
                  f"- Guard: {row['guard']['role']}; {row['guard']['evidence']}."]
        if row["guard"]["static_caller_checks"]:
            checks = "; ".join(f"pc {hex(check['caller_pc'])} slot {check['slot']} shift {check['shift']}"
                               for check in row["guard"]["static_caller_checks"])
            lines.append(f"- Caller check sites in the pinned bytes: {checks}.")
        writes = [entry for entry in row["writes"] if "slot" in entry]
        if writes:
            for entry in writes:
                label = entry["slot_label"] or "unlabelled slot"
                lines.append(f"- Write seen in probe `{entry['probe']}`: `{entry['slot']}` ({label}) "
                             f"{entry['before']} to {entry['after']}.")
        else:
            lines.append("- Writes: none observed on the probed paths; documented writes are "
                         + "; ".join(row["documented_writes"]) + ".")
        events = [entry for entry in row["events"] if "topic0" in entry]
        if events:
            for entry in events:
                lines.append(f"- Event seen in probe `{entry['probe']}`: topic0 `{entry['topic0']}` "
                             f"({entry['name_status']}), {entry['topic_count']} topics, {entry['data_bytes']} data bytes.")
        else:
            lines.append("- Events: none observed on the probed paths; documented topics are "
                         + "; ".join(row["documented_events"]) + ".")
        lines.append(f"- Behaviour: {row['documented_behaviour']}")
        outcome_rows = ", ".join(f"`{name}` {record['status']} {record['output_or_revert'] or '0x'}"
                                 for name, record in row["probe_outcomes"].items())
        lines.append(f"- Replay probes: {outcome_rows}.")
        lines.append(f"- Caller probe: `{row['rejection_branch']['caller_probe']}` -> "
                     f"{row['rejection_branch']['caller_probe_outcome']} "
                     f"{row['rejection_branch']['caller_probe_revert_data']}; short-calldata rejection "
                     f"`{row['rejection_branch']['short_calldata_probe']}` -> "
                     f"{row['rejection_branch']['short_calldata_outcome']} with empty data; state changed: "
                     f"{row['rejection_branch']['state_changed']}.")
        lines.append("- Still undecided: " + " ".join(row["undecided"]))
        lines.append("")
    lines += [
        "## Method and limits",
        "",
        "- Static layer: `cast disassemble` of the two pinned runtimes, a dispatcher byte-pattern scan for each "
        "entry point, the canonical calldata length constant, the calldata offsets actually read, the caller checks "
        "reachable from the entry (slot, comparison site) and every constant that the region touches. The linked "
        "library runtime contains zero `CALLER` instructions; its preamble compares `ADDRESS` with its own address, "
        "so a direct call reverts with empty data while a delegatecall executes.",
        "- Replay layer: one generated Foundry suite etches the pinned proxy, the Exchange implementation, the linked "
        "library, the Oracle, Tokenomics and PAPER runtimes, seeds the pinned storage words that the saved artifacts "
        "hold, replaces the 0x080e price address with a two-word mock, and records calldata, revert data, log topics, "
        "log sizes and the before/after value of every watched slot.",
        "- This page describes the pinned implementation only. The Exchange proxy's implementation changed after the "
        "pin on the live chain; post-pin behaviour is outside this record.",
        "- Observed revert values, with the exact byte evidence in the pinned runtimes: "
        + "; ".join(f"`{value}` ({entry['name'] or 'unnamed'}; bytes at exchange offset "
                    f"{entry['exchange']['byte_offset']}, library offset {entry['library']['byte_offset']})"
                    for value, entry in sorted(observed_reverts.items())) + ".",
        "- Six of those values (0x0dc149f0, 0x49199fb6, 0x67207a88, 0x5b6d2b7a, 0xddeb79ba, 0x924d25e6) appear as no "
        "contiguous byte string in either runtime, so they are assembled rather than embedded; a byte-presence check "
        "cannot confirm their names, and 0x924d25e6 stays entirely unestablished.",
        "- The full library dequeue topic0 is "
        "0x4c672bd1e7444966ce521bc0f053d4f359f1fad9cfe6a43011c00baac6278e4d; "
        "[exchange_library_remaining.md](exchange_library_remaining.md) prints a truncated value.",
        "- Every probe is synthetic. The liquidation success path needs more pinned state than the archived diff "
        "holds, so its settlement writes stay with the archive-backed probe in "
        "[exchange_liquidation_pseudocode.md](exchange_liquidation_pseudocode.md).",
        "- Custom error names are used only when the local keccak of the candidate equals the selector and, for the "
        "registry names, the saved OpenChain response lists the same signature. Error selectors "
        + ", ".join(f"`{name}`" for name in ledger["unnamed_error_selectors"]) + " stay unnamed.",
        "",
        "Run `python3 scripts/atlas_selector_gap_exchange.py` offline to rebuild the static read, the replay and this page.",
        "",
    ]
    return "\n".join(lines)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true",
                        help="write the observed replay records without freezing expectations")
    args = parser.parse_args()

    global LABELS
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    LABELS = slot_labels()
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    coverage = json.loads((ATLAS / "selector_evidence_coverage.json").read_text())
    unresolved = json.loads((ATLAS / "unresolved.json").read_text())

    # Ledger agreement: every assigned selector is still a recorded row.
    gap_rows = {(row["role"], row["selector"])
                for row in unresolved["state_changing_selectors_without_saved_historical_trace"]}
    coverage_rows = {(row["role"], row["selector"]): row for row in coverage["rows"]
                     if row["active_runtime_at_pin"]}
    for role, selectors in ASSIGNED.items():
        for selector in selectors:
            assert (role, selector) in gap_rows, (role, selector)
            assert (role, selector) in coverage_rows, (role, selector)
            assert coverage_rows[(role, selector)]["historical_edge_call_count"] == 0
            assert coverage_rows[(role, selector)]["historical_root_transaction_count"] == 0

    exchange = Runtime(IMPLEMENTATION, manifest)
    library = Runtime(LIBRARY, manifest)
    runtimes = {IMPLEMENTATION: exchange, LIBRARY: library}

    # Selector presence in the pinned dispatcher and catalog.
    for role, selectors in ASSIGNED.items():
        address = IMPLEMENTATION if role == "exchange_implementation" else LIBRARY
        runtime = runtimes[address]
        catalogued = {fn["selector"] for fn in catalog[address]["functions"]}
        for selector in selectors:
            assert selector in runtime.entries, (address, selector)
            assert selector in catalogued, (address, selector)
            assert runtime.insts[runtime.entries[selector]] == "JUMPDEST", (address, selector)

    # Name candidates are hash-checked; mismatches are rejected outright.
    name_check = {}
    for selector, (signature, source) in NAME_CANDIDATES.items():
        if not signature:
            name_check[selector] = {"signature": "", "hash_checked": False,
                                    "status": "unresolved", "source": source}
            continue
        digest = selector_of(signature)
        assert digest == selector, (selector, signature, digest)
        name_check[selector] = {"signature": signature, "hash_checked": True,
                                "status": "hash_matches_selector", "source": source}

    registry = json.loads((ROOT / "artifacts" / "openchain_unverified_error_lookup.json").read_text())
    registry_functions = registry["response"]["result"]["function"]
    known_errors = {}
    for selector, (signature, source) in ERROR_NAMES.items():
        digest = selector_of(signature)
        assert digest == selector, (selector, signature, digest)
        if source == "registry":
            rows = registry_functions.get(selector) or []
            names = [entry["name"] for entry in rows]
            assert signature in names, (selector, signature, names)
        known_errors[selector] = {"signature": signature, "name_source": source}
    for selector in UNNAMED_ERRORS:
        assert selector not in known_errors
    known_topics = {signature: keccak(signature) for signature in EVENT_CANDIDATES}
    # The two published topics of the control selectors must hash to their
    # documented bytes without any registry help.
    assert known_topics["FeeRatesUpdated(uint256,uint256,uint256)"] == \
        "0xe4af0531d4ba8c578b5076b042e4505372fb4f4986aea8ebf77f4ff1585e3e75"
    assert known_topics["TradingPausedUpdated(bool)"] == \
        "0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e"
    assert known_topics["PauseGuardianUpdated(address)"] == \
        "0x6b3ffd50ed0810416007b5dbbae587b9d8801c50bf8065cda8eb82011bed314e"
    topic_lookup = {digest: signature for signature, digest in known_topics.items()}

    static = {
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "method": "cast disassemble of the pinned runtime bytes plus local keccak name checks",
        "runtimes": {address: {"role": manifest["contracts"][address]["role"],
                               "sha256": runtimes[address].sha256 if address in runtimes else manifest["contracts"][address]["sha256"],
                               "runtime_bytes": len(runtimes[address].bytes) if address in runtimes else manifest["contracts"][address]["runtime_bytes"]}
                     for address in (IMPLEMENTATION, LIBRARY)},
        "rows": {},
        "limits": [
            "Statically reachable regions follow direct jumps; a caller check reached only through a jump whose target comes from a stack value would be missed.",
            "Absence of CALLER instructions is exact only for the whole runtime, not per function.",
        ],
    }

    # Whole-runtime caller census: the linked library has no caller check at all.
    library_callers = [pc for pc, text in library.insts.items() if text == "CALLER"]
    exchange_callers = [pc for pc, text in exchange.insts.items() if text == "CALLER"]
    static["caller_census"] = {
        "library_caller_instructions": len(library_callers),
        "exchange_caller_instructions": len(exchange_callers),
        "library_note": "zero CALLER instructions in the whole linked-library runtime",
    }

    slot_roles = SLOT_ROLES

    for role, selectors in ASSIGNED.items():
        address = IMPLEMENTATION if role == "exchange_implementation" else LIBRARY
        runtime = runtimes[address]
        for selector in selectors:
            entry = runtime.entries[selector]
            minimum, offsets = calldata_shape(runtime, entry)
            region, caller_facts = guard_facts(runtime, entry, GUARD_ERROR_SELECTORS)
            prologue, helpers = runtime.prologue(entry)
            sstores = []
            for pc, text in sorted(region.items()):
                if text != "SSTORE":
                    continue
                slot_pc, slot_text = runtime.prev(pc)
                while slot_text in ("DUP1", "DUP2", "DUP3", "DUP4", "DUP5", "SWAP1", "SWAP2", "SWAP3"):
                    slot_pc, slot_text = runtime.prev(slot_pc)
                slot = 0 if slot_text == "PUSH0" else runtime.constant(slot_text)
                sstores.append({"pc": pc, "slot": slot})
            sloads = []
            for pc, text in sorted(region.items()):
                if text != "SLOAD":
                    continue
                slot_pc, slot_text = runtime.prev(pc)
                while slot_text in ("DUP1", "DUP2", "DUP3", "DUP4", "DUP5", "SWAP1", "SWAP2", "SWAP3"):
                    slot_pc, slot_text = runtime.prev(slot_pc)
                sloads.append({"pc": pc, "slot": 0 if slot_text == "PUSH0" else runtime.constant(slot_text)})
            log_sites = [{"pc": pc, "log_n": int(text[3:])}
                         for pc, text in sorted(region.items()) if text.startswith("LOG")]
            topic_constants = []
            for pc, text in sorted(region.items()):
                if text.startswith("PUSH32"):
                    value = text.split()[1]
                    topic_constants.append({"pc": pc, "topic": value,
                                            "matched_signature": topic_lookup.get(value, "")})
            calls = []
            for pc, text in sorted(region.items()):
                if text not in ("CALL", "DELEGATECALL", "STATICCALL"):
                    continue
                target, call_selector = None, None
                for step in range(1, 14):
                    _, back_text = runtime.prev(pc, step)
                    if back_text.startswith("PUSH20"):
                        target = back_text.split()[1]
                    if back_text.startswith("PUSH4"):
                        call_selector = back_text.split()[1]
                calls.append({"pc": pc, "kind": text, "target": target, "selector": call_selector})
            errors = []
            for pc, text in sorted(prologue.items()):
                if text.startswith("PUSH4"):
                    value = text.split()[1]
                    errors.append(value)
            static["rows"][selector] = {
                "role": role,
                "runtime_address": address,
                "runtime_sha256": runtime.sha256,
                "entry_pc": entry,
                "calldata_min_bytes": None if minimum is None else minimum + 4,
                "calldata_words": None if minimum is None else minimum // 32,
                "calldata_offsets_read": offsets,
                "guard": {
                    "role": guard_role(caller_facts, slot_roles),
                    "checks": [dict(fact) for fact in caller_facts],
                    "note": "no CALLER instruction reachable from this entry inside the pinned runtime"
                            if not caller_facts else "",
                },
                "sstore_sites": sstores,
                "sload_sites": sloads[:12],
                "log_sites": log_sites,
                "topic_constants": topic_constants,
                "external_calls": calls,
                "prologue_error_selectors": sorted(set(errors)),
                "prologue_helpers": sorted(helpers),
                "region_instruction_count": len(region),
            }

    # Ground truth from the existing behaviour maps, asserted against the static read.
    expected = {
        "0x01681a62": {"words": 1, "guard": "no_caller_check"},
        "0x2d2451d1": {"words": 1, "guard": "owner+pauseGuardian"},
        "0x415f1240": {"words": 1, "guard": "no_caller_check"},
        "0x4a4d9eea": {"words": 3, "guard": "no_caller_check"},
        "0x5ca4c0ea": {"words": 5, "guard": "owner"},
        "0x6a3214c9": {"words": 2, "guard": "owner"},
        "0x753a369c": {"words": 4, "guard": "no_caller_check"},
        "0x827ad94c": {"words": 4, "guard": "no_caller_check"},
        "0xae4daf4e": {"words": 3, "guard": "no_caller_check"},
        "0xae69b95b": {"words": 1, "guard": "owner+pauseGuardian"},
        "0xc0c53b8b": {"words": 3, "guard": "no_caller_check"},
        "0xd7c7e5fb": {"words": 3, "guard": "owner"},
        "0xe538b280": {"words": 3, "guard": "owner"},
        "0x18958ce2": {"words": 3, "guard": "no_caller_check"},
        "0x2448a553": {"words": 5, "guard": "no_caller_check"},
        "0x32db40c9": {"words": 5, "guard": "no_caller_check"},
        "0x3cf4208d": {"words": 6, "guard": "no_caller_check"},
        "0x3f4e3626": {"words": 3, "guard": "no_caller_check"},
        "0xb67f3dd7": {"words": 7, "guard": "no_caller_check"},
        "0xca02ff91": {"words": 4, "guard": "no_caller_check"},
    }
    for selector, want in expected.items():
        row = static["rows"][selector]
        assert row["calldata_words"] == want["words"], (selector, row["calldata_words"], want)
        assert row["guard"]["role"] == want["guard"], (selector, row["guard"]["role"], want)

    # Documented write slots and event topics must appear in the static read.
    write_expectations = {
        "0xe538b280": [23, 24, 25],
        "0xae69b95b": [29],
        "0x6a3214c9": None,
    }
    for selector, slots in write_expectations.items():
        if slots is None:
            continue
        found = {site["slot"] for site in static["rows"][selector]["sstore_sites"]}
        assert set(slots) <= found, (selector, sorted(found), slots)
    # Documented event topics must exist as exact byte strings in the pinned
    # runtime. A selector's own region may not reach a shared emitter helper, so
    # the census is taken over the whole runtime and the per-selector field stays
    # a supporting observation.
    documented_topics = {
        "0xe4af0531d4ba8c578b5076b042e4505372fb4f4986aea8ebf77f4ff1585e3e75": "FeeRatesUpdated(uint256,uint256,uint256)",
        "0xa4abec9259618fb7d014c89824b2887f61e3ab2b382d4a48a42dfde43cec5d6e": "TradingPausedUpdated(bool)",
        "0x6b3ffd50ed0810416007b5dbbae587b9d8801c50bf8065cda8eb82011bed314e": "PauseGuardianUpdated(address)",
        "0x62db1b2b923b6f20043c492d3586df1a823e447c63e44d15dbc90c1a3bc9fcc5": "unnamed instrument-field event",
        "0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9": "unnamed instrument admin event",
        "0x25e933a27e6487478d7617f2f4ef2f5c77355faf6cad2e6fd7c4b8d029930d9f": "unnamed market pause event",
    }
    census = {}
    for topic, label in documented_topics.items():
        offset = exchange.bytes.find(bytes.fromhex(topic[2:]))
        census[topic] = {"label": label, "runtime_byte_offset": offset}
        assert offset >= 0, (topic, label)
    library_topics = {}
    for topic, label in {
        "0xb8c6723c829f797c1498cb75af97462c6cb9f3784fe7c0c47bcd42cf42ca94fb": "queue move",
        "0xf949f11686e63f08cadf672fb6db7f7b859cb0fe11f2bf80c57db5429453f0cc": "queue merge summary",
    }.items():
        offset = library.bytes.find(bytes.fromhex(topic[2:]))
        library_topics[topic] = {"label": label, "runtime_byte_offset": offset}
        assert offset >= 0, (topic, label)
    static["runtime_topic_census"] = {"exchange": census, "library": library_topics}
    enqueued_topic = known_topics["Enqueued(address,uint256,uint256)"]
    assert library.bytes.find(bytes.fromhex(enqueued_topic[2:])) >= 0, enqueued_topic
    static["runtime_topic_census"]["library"][enqueued_topic] = {
        "label": "Enqueued(address,uint256,uint256), hash-checked and present in the library runtime",
        "runtime_byte_offset": library.bytes.find(bytes.fromhex(enqueued_topic[2:])),
    }

    runtime_files = {
        "Proxy": PROXY,
        "Implementation": IMPLEMENTATION,
        "Library": LIBRARY,
        "Oracle": ORACLE,
        "OracleImplementation": ORACLE_IMPL,
        "Tokenomics": TOKENOMICS,
        "TokenomicsImplementation": TOKENOMICS_IMPL,
        "Paper": PAPER,
        "PaperImplementation": PAPER_IMPL,
        "PaperMath": PAPER_MATH,
    }
    runtime_hex = {}
    for name, address in runtime_files.items():
        row = manifest["contracts"][address]
        hexcode = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(hexcode.removeprefix("0x"))).hexdigest() == row["sha256"]
        runtime_hex[name] = hexcode
    if args.record:
        test_source = build_test_source()
        (ARTIFACTS / "replay").mkdir(parents=True, exist_ok=True)
        (ARTIFACTS / "replay" / "ExchangeSelectorGap.t.sol").write_text(test_source)
        _, results, _ = run_forge(runtime_hex, test_source)
        (ARTIFACTS / "observed_replay.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(results, indent=1))
        return

    static["name_checks"] = name_check
    static["error_name_checks"] = known_errors
    static["unnamed_error_selectors"] = UNNAMED_ERRORS
    static["topic_name_checks"] = known_topics
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    STATIC_OUT.write_text(json.dumps(static, indent=2) + "\n")

    # Port-free replay, checked against the frozen expectations.
    test_source = build_test_source()
    passed, replay, _ = run_forge(runtime_hex, test_source)
    assert len(passed) == len(TEST_CASES)
    for name, (status, data, changed, logs) in REPLAY_EXPECTATIONS.items():
        record = replay[name]
        assert record["status"] == status, (name, record["status"], status)
        assert record["data"] == data, (name, record["data"], data)
        assert (record["fp_before"] != record["fp_after"]) == changed, (name, "state change")
        assert record["logs"] == logs, (name, record["logs"], logs)
    REPLAY_OUT.write_text(json.dumps({
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "method": "port-free Forge tests that etch the pinned proxy, implementations and linked library and seed pinned storage words; the 0x080e HyperCore BBO read address is replaced by a two-word mock",
        "test_count": len(passed),
        "test_names": sorted(passed),
        "test_source_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
        "runtime_hashes": {name: {"sha256": hashlib.sha256(bytes.fromhex(code.removeprefix("0x"))).hexdigest()}
                           for name, code in runtime_hex.items()},
        "synthetic": True,
        "expectations_frozen": {name: {"status": status, "data": data, "state_changed": changed, "logs": logs}
                                for name, (status, data, changed, logs) in sorted(REPLAY_EXPECTATIONS.items())},
        "limits": [
            "Every probe is synthetic: no historical transaction was executed.",
            "The 0x080e price address is a mock; live HyperCore prices are not reproduced.",
            "The liquidation success path needs more pinned state than the archived diff holds, so its settlement writes come from the archive-backed probe.",
        ],
    }, indent=2) + "\n")

    # Every 4-byte revert value this run observed, with the exact place the bytes
    # sit in the pinned runtimes: a PUSH4 immediate in a function, or a byte
    # string that only exists in the constant data pool.
    observed_reverts = {}
    for name, record in replay.items():
        data = record["data"]
        if record["status"] != "revert" or len(data) != 10:
            continue
        value = data.lower()
        entry = {"selectors": sorted({name.rsplit("_", 1)[-1] for name in replay if replay[name]["data"].lower() == value
                                      and replay[name]["status"] == "revert"})}
        for label, runtime in (("exchange", exchange), ("library", library)):
            immediate = [pc for pc, text in runtime.insts.items() if text == f"PUSH4 {value}"]
            offset = runtime.bytes.find(bytes.fromhex(value[2:]))
            entry[label] = {"push4_immediates": immediate, "byte_offset": offset}
        entry["name"] = ERROR_NAMES.get(value, (None, ""))[0] or UNNAMED_ERRORS.get(value, "")
        observed_reverts[value] = entry
    rows = build_rows(static, replay)
    ledger = {
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "scope": "untraced state-changing selectors of the Exchange implementation and the live linked library",
        "assigned_roles": {role: len(selectors) for role, selectors in ASSIGNED.items()},
        "assigned_selector_count": sum(len(selectors) for selectors in ASSIGNED.values()),
        "evidence_tiers": sorted({row["evidence_tier"] for row in rows}),
        "rows": rows,
        "method": {
            "static": "cast disassemble of the pinned runtime bytes, local keccak name checks, caller-check and calldata-shape recovery",
            "replay": "../../artifacts/selector_gap_exchange/replay.json",
            "static_analysis": "../../artifacts/selector_gap_exchange/static_analysis.json",
            "replay_records": "../../artifacts/selector_gap_exchange/replay/",
            "recording_step": "../../artifacts/selector_gap_exchange/observed_replay.json (written by --record before the expectations were frozen)",
        },
        "caller_census": static["caller_census"],
        "runtime_topic_census": static["runtime_topic_census"],
        "unnamed_error_selectors": static["unnamed_error_selectors"],
        "observed_revert_selectors": observed_reverts,
        "limits": [
            "No assigned selector has a saved historical trace, so no row claims historical-trace evidence.",
            "The static region walk follows direct jumps only and can miss a check reached through a computed jump.",
            "Names taken from the public ABI fixture or the resolved caller-check table stay candidates, not verified source.",
            "Every replay result is a simulation on etched pinned bytecode, never an on-chain execution.",
        ],
    }
    # The ledger is its own check: every assigned selector has one row with every
    # required field, and no row claims a stronger tier than it holds.
    assert len(rows) == ledger["assigned_selector_count"]
    covered = {(row["role"], row["selector"]) for row in rows}
    assert covered == {(role, selector) for role, selectors in ASSIGNED.items() for selector in selectors}
    allowed_tiers = {"historical_trace", "exact_runtime_replay", "bytecode_only_static_read", "undecided"}
    for row in rows:
        assert row["evidence_tier"] in allowed_tiers
        for field in ("name_status", "abi_shape", "guard", "writes", "events", "rejection_branch", "undecided"):
            assert row[field], (row["selector"], field)
        assert row["abi_shape"]["calldata_words"] >= 1
        assert row["guard"]["role"] and row["guard"]["evidence"]
        assert row["rejection_branch"]["short_calldata_outcome"] == "revert"
        assert row["rejection_branch"]["short_calldata_revert_data"] == "0x"
        if row["evidence_tier"] == "historical_trace":
            raise AssertionError("no assigned selector has a saved historical trace")
        assert row["name_hash_checked"] or row["name_status"] == "unresolved"
    LEDGER_OUT.write_text(json.dumps(ledger, indent=2) + "\n")
    DOC_OUT.write_text(render_doc(ledger, observed_reverts))
    print(f"verified {ledger['assigned_selector_count']} rows, {len(passed)} replay cases")
    for row in rows:
        print(f"  {row['selector']} {row['role'][:12]:12s} guard={row['guard']['role']:22s} "
              f"tier={row['evidence_tier']} writes={len([w for w in row['writes'] if 'slot' in w])} "
              f"events={len([e for e in row['events'] if 'topic0' in e])}")


if __name__ == "__main__":
    main()
