#!/usr/bin/env python3
"""Second, additive atlas pin: the post-refresh (docs contract set 2) suite as it stands now.

Offline verify and regeneration from saved evidence (no credential, no network):

    python3 scripts/atlas_postpin_pin.py

Refresh the read-only public evidence over the public HyperEVM RPC:

    python3 scripts/atlas_postpin_pin.py --capture

The public endpoint rate-limits hard, so --capture checkpoints every reply under
artifacts/postpin_pin/partial_reads.json and a re-run with --resume continues from it
without re-reading what it already has; the ledger records which values were reused and
when each one was read. The checkpoint file is removed once a capture completes.

    python3 scripts/atlas_postpin_pin.py --rebuild

rewrites the pin's files from the saved ledger without touching the network.

The offline path reads only saved files: the ledger this script captured under
artifacts/postpin_pin/, the audited baseline under atlas/block_48902346/, its selector
catalog, the post-refresh suite ledger, the post-pin runtimes under
artifacts/postpin_suite/runtime/, and the explorer creation facts. It rebuilds
atlas/block_<pin>/manifest.json, selector_catalog.json, runtime/*.hex and repin.md and
asserts that the on-disk copies are byte-identical to the rebuild, so every hash in the
new pin is recomputable without a credential.

The baseline at atlas/block_48902346/ is not touched: this pin is additive and points
its unchanged runtimes at the baseline's saved files instead of copying them.

The public RPC ignores the block parameter, so every value under the new pin is a
current-state read taken at the head recorded in the ledger, not archive state. The
selector catalog and the runtime hashes are exact (they are computed from the saved
bytes); the owner, delay, threshold and balance rows are read-only-current.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PIN_ATLAS = ROOT / "atlas" / "block_48902346"
POSTPIN_SUITE = ROOT / "artifacts" / "postpin_suite"
ARTIFACTS = ROOT / "artifacts" / "postpin_pin"
LEDGER_PATH = ARTIFACTS / "state_reads.json"
RAW_PATH = ARTIFACTS / "raw_reads.json"
CHECKPOINT = ARTIFACTS / "partial_reads.json"
CODE_DIR = ARTIFACTS / "code"
RPC = "https://rpc.hyperliquid.xyz/evm"
CHAIN_ID = 999
BASELINE_PIN = 48_902_346
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
ZERO_WORD = "0x" + "00" * 32
DISPATCH = re.compile(rb"\x63(.{4})\x14\x61(.{2})\x57", re.S)

# Suites, as mapped by atlas/block_48902346/suite_sets.md. Dates are the recorded
# creation spans; the set names are this repo's, not the docs'.
SETS = (
    ("earlier_1", "0xa1763a5ff94ebddd417cccb906622ec762ab2e29",
     "2026-08-02T19:35:00Z to 2026-08-02T20:27:46Z", "undocumented"),
    ("earlier_2", "0xa1763a5ff94ebddd417cccb906622ec762ab2e29",
     "2026-10-05T10:40:00Z to 2026-10-05T11:04:31Z", "undocumented"),
    ("newest", "0xa1763a5ff94ebddd417cccb906622ec762ab2e29",
     "2026-10-06T22:43:00Z to 2026-10-06T22:59:45Z", "/v1/ contract set 1, live 7-21 Oct 2026"),
    ("postpin_refresh", "0x13cb7a200d081094d23ebf07f4d708410a9c488b",
     "2026-10-20T18:07:00Z to 2026-10-21T22:00:02Z", "contract set 2, live since 21 Oct 2026"),
)

# The eight EIP-1967 proxies of the newest suite. Only the first three moved.
PROXIES = (
    ("exchange_proxy", "0x6cd5661646289fb6e65ea5c032310fded797d0a2", "exchange_implementation"),
    ("session_key_manager_proxy", "0x8326eb8896e358717f10502ec73ce8d28e37b108",
     "session_key_manager_implementation"),
    ("tokenomics_proxy", "0x75174549dbbd44497d31a47e2e2d7406408d63d9", "tokenomics_implementation"),
    ("oracle_proxy", "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e", "oracle_implementation"),
    ("staking_proxy", "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016", "staking_implementation"),
    ("paper_token_proxy", "0xe40f17915daa230324030003a197cdaef2261c0e", "paper_token_implementation"),
    ("batch_executor_proxy", "0x233ff29b239abc1d7748605da9b205c3e008626e",
     "batch_executor_implementation"),
    ("deposit_proxy_factory_proxy", "0x1629b7d46bef6e13ff754174fc9f32dea309b38f",
     "deposit_proxy_factory_implementation"),
)
PROXY_ADDRESSES = {address: role for role, address, _ in PROXIES}
PROXY_ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
MULTISIG = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
EXCHANGE_PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"

# The five contracts the 2026-10-20/21 refresh added, and the pinned implementation
# (or pinned runtime) each one supersedes. builder_registry has no pinned counterpart.
POST_REFRESH = (
    ("0x583d0bd818c991c5830fea93aef04e474b272459", "exchange_linked_library_2",
     "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"),
    ("0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723", "exchange_implementation_2",
     "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"),
    ("0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946", "session_key_manager_implementation_2",
     "0x8a5069fe303e8f81e91825436e956d595032e558"),
    ("0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03", "tokenomics_implementation_2",
     "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"),
    ("0xfdc6550436dd75ce8a0b145f935b7d3a64f53248", "builder_registry", None),
)
POST_REFRESH_ADDRESSES = [row[0] for row in POST_REFRESH]
# The post-refresh contracts that dispatch selectors; the catalog covers these.
CATALOG_ROLES = {row[0]: row[1] for row in POST_REFRESH}

# PT-01. Both users are the pair the stalled-sweep census identified; the two storage
# slots are the Exchange's pendingSweepWord (33) and balances (9) mappings as the
# pinned setter/getter evidence places them.
PT01_USERS = ("0x56cbe78a5cdfa10147927aec550aa7f2fb3d3d01",
              "0x9c8599c32224d7d9956a7def18f7314162f77baf")
PT01_SLOTS = (("pending_sweep", 33), ("balances", 9))
ORACLE_PIN_NOTE = ("Every read under this pin is a current-state `latest` read; the public RPC "
                   "ignores the block parameter, so no value here is archive state.")

STATE_CALLS = (
    ("proxy_admin_owner", "ProxyAdmin owner()", PROXY_ADMIN, "0x8da5cb5b", "address"),
    ("exchange_owner", "Exchange owner() through the proxy", EXCHANGE_PROXY, "0x8da5cb5b", "address"),
    ("exchange_authorized_executor", "Exchange authorizedExecutor() through the proxy",
     EXCHANGE_PROXY, "0x13dd495b", "address"),
    ("timelock_owner", "newest timelock owner()", TIMELOCK, "0x8da5cb5b", "address"),
    ("timelock_min_delay", "newest timelock getMinDelay()", TIMELOCK, "0xc63c4e9b", "integer"),
    ("multisig_required_confirmations", "newest multisig requiredConfirmations()",
     MULTISIG, "0x82e717f7", "integer"),
    ("multisig_signer_one", "newest multisig signerOne()", MULTISIG, "0xd98f851a", "address"),
    ("multisig_signer_two", "newest multisig signerTwo()", MULTISIG, "0x1a5f66c3", "address"),
    ("multisig_signer_three", "newest multisig signerThree()", MULTISIG, "0x64d62769", "address"),
    ("multisig_transaction_count", "newest multisig transactionCount()", MULTISIG, "0xb77bf600",
     "integer"),
    ("builder_registry_owner", "BuilderRegistry owner()", "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248",
     "0x8da5cb5b", "address"),
    ("builder_registry_guardian", "BuilderRegistry guardian()",
     "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248", "0x452a9320", "address"),
)
# Selector names for the reads above, carried from the pinned catalog where the baseline
# reconstructed them from its own saved bytes and behavior; otherwise unresolved.
READ_SIGNATURE_CITATIONS = {
    "0x8da5cb5b": ("owner()", "reconstructed_from_bytecode_and_behavior", "atlas/block_48902346/selector_catalog.json"),
    "0x82e717f7": ("requiredConfirmations()", "reconstructed_from_bytecode_and_behavior",
                   "atlas/block_48902346/multisig_behavior.json"),
    "0xd98f851a": ("signerOne()", "reconstructed_from_bytecode_and_behavior",
                   "atlas/block_48902346/multisig_behavior.json"),
    "0x1a5f66c3": ("signerTwo()", "reconstructed_from_bytecode_and_behavior",
                   "atlas/block_48902346/multisig_behavior.json"),
    "0x64d62769": ("signerThree()", "reconstructed_from_bytecode_and_behavior",
                   "atlas/block_48902346/multisig_behavior.json"),
    "0xb77bf600": ("transactionCount()", "reconstructed_from_bytecode_and_behavior",
                   "atlas/block_48902346/multisig_behavior.json"),
    "0xc63c4e9b": ("getMinDelay()", "reconstructed_from_bytecode_and_behavior",
                   "atlas/block_48902346/timelock_behavior.json"),
    "0x13dd495b": ("authorizedExecutor()", "reconstructed_from_bytecode_and_behavior",
                   "atlas/block_48902346/selector_catalog.json"),
    "0x452a9320": ("guardian()", "public_registry_candidate_hash_matched", None),
}

# Public-registry candidate names for the selectors the refresh added or dropped, taken
# from the NEW_SELECTORS table of atlas_suite_sets.py. Each candidate is re-hash-checked
# here against the selector bytes; a None name stays unresolved.
CANDIDATE_NAMES = {
    "0x69f9a5f0": "claimBuilderFees()",
    "0x9d346583": "builderFees(address)",
    "0xbd322efa": "setBuilderRegistry(address)",
    "0xe737de13": "builderRegistry()",
    "0x456db972": "insolventSince()",
    "0x85eb2a08": "activateRebate()",
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
    "0x415f1240": "liquidate(uint256)",
}


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def write_json(path, payload):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def hexbytes(text):
    return bytes.fromhex(text.strip().removeprefix("0x"))


def runtime_text(code):
    code = code.strip()
    assert "\n" not in code and code.startswith("0x")
    return code + "\n"


def word_to_address(word):
    return "0x" + word.strip().removeprefix("0x").lower()[-40:]


def word_to_int(word):
    return int(word, 16)


def keccak():
    import atlas_factory_events

    return atlas_factory_events.Keccak()


def mapping_slot_index(user, slot):
    return "0x" + keccak()(int(user, 16).to_bytes(32, "big") + slot.to_bytes(32, "big")).hex()


def selector_of(signature):
    return "0x" + keccak()(signature.encode()).hex()[:8]


def dispatcher_entries(code):
    return {"0x" + match.group(1).hex(): int.from_bytes(match.group(2), "big")
            for match in DISPATCH.finditer(code)}


def run_cast(arguments):
    """Run a local cast command on saved bytes, retrying transient failures."""
    last = None
    for attempt in range(6):
        last = subprocess.run(["cast", *arguments], capture_output=True, text=True)
        if last.returncode == 0:
            return last
        time.sleep(1 + attempt)
    raise RuntimeError(f"cast {' '.join(arguments[:2])} failed: rc={last.returncode} "
                       f"stderr={last.stderr[:200]!r}")


def disassembly(code_hex):
    insts = {}
    for line in json.loads(run_cast(["disassemble", "--json", code_hex]).stdout)["data"].splitlines():
        if len(line) > 10 and line[8:10] == ": ":
            insts[int(line[:8], 16)] = line.split(": ", 1)[1]
    return insts


def cast_selectors(code_hex):
    parsed = json.loads(run_cast(["selectors", "--json", "--", code_hex]).stdout)
    return {row["selector"]: row for row in parsed["data"]}, parsed.get("warnings", [])


def calldata_guard(insts, ordered, index, entry):
    """Static calldata bytes the entry itself demands, or None.

    solc emits the same shape for every argument count:
    `PUSH<n> CALLDATASIZE PUSH1 0x03 NOT ADD SLT PUSH2 <revert> JUMPI`, where n is the
    argument head in bytes (PUSH0 for zero arguments). Only the entry's own first block
    is scanned, so a neighbouring function's guard cannot leak in.
    """
    start = index[entry]
    for position in range(start, min(start + 16, len(ordered) - 4)):
        if insts[ordered[position]] != "CALLDATASIZE":
            continue
        back = insts[ordered[position - 1]]
        if back != "PUSH0" and not back.startswith("PUSH"):
            continue
        forward = [insts[ordered[position + step]] for step in range(1, 5)]
        if forward[:3] == ["PUSH1 0x03", "NOT", "ADD"] and forward[3] == "SLT":
            return 0 if back == "PUSH0" else int(back.split()[1], 16)
    return None


def widths_from_cast(arguments):
    """Per-argument widths from `cast selectors` inference on the same saved bytes."""
    if not arguments:
        return [], []
    widths, dynamic = [], []
    for item in arguments.split(","):
        item = item.strip()
        if not item:
            continue
        if item.endswith("]") or item == "bytes" or item == "string":
            widths.append(None)
            dynamic.append(item)
        else:
            widths.append(32)
    return widths, dynamic


class Runtime:
    """One saved runtime: exact bytes plus the dispatcher decode from those bytes."""

    def __init__(self, address, role, code_hex, runtime_file, pinned_counterpart):
        self.address = address
        self.role = role
        self.code_hex = code_hex
        self.bytes = hexbytes(code_hex)
        self.runtime_file = runtime_file
        self.pinned_counterpart = pinned_counterpart
        self.entries = dispatcher_entries(self.bytes)
        self.insts = disassembly(code_hex)
        self.ordered = sorted(self.insts)
        self.index = {pc: i for i, pc in enumerate(self.ordered)}
        self.cast, self.warnings = cast_selectors(code_hex)

    def rows(self, pinned_rows, pinned_entries):
        out = []
        for selector, entry in sorted(self.entries.items()):
            guard = calldata_guard(self.insts, self.ordered, self.index, entry)
            inferred, dynamic = widths_from_cast(self.cast.get(selector, {}).get("arguments", ""))
            if guard is not None and guard % 32 == 0:
                widths = [32] * (guard // 32)
                source = "observed_calldatasize_guard_on_saved_bytes"
            else:
                widths = inferred
                source = "cast_inference_on_saved_bytes"
            baseline = pinned_rows.get(selector)
            if baseline is not None:
                candidate = baseline["candidate_signature"] or baseline["reconstructed_signature"]
                status = ("baseline_name_carried_not_reproven_on_this_runtime"
                          if candidate else "unresolved")
                evidence = baseline.get("behavior_evidence")
                baseline_status = baseline["signature_status"]
            else:
                candidate = CANDIDATE_NAMES.get(selector)
                if candidate is None:
                    status, evidence, baseline_status = "unresolved", None, None
                else:
                    assert selector_of(candidate) == selector, (self.address, selector, candidate)
                    status = "public_registry_candidate_hash_matched"
                    evidence = "atlas_suite_sets.py NEW_SELECTORS"
                    baseline_status = None
            out.append({
                "selector": selector,
                "entry_pc": entry,
                "argument_widths_bytes": widths,
                "argument_word_count": len(widths) if widths else 0,
                "argument_width_source": source,
                "observed_calldatasize_guard_bytes": guard,
                "cast_inferred_arguments": self.cast.get(selector, {}).get("arguments", ""),
                "cast_inferred_dynamic_types": dynamic,
                "state_mutability": self.cast.get(selector, {}).get("state_mutability", ""),
                "candidate_signature": candidate or "",
                "name_status": status,
                "baseline_signature_status": baseline_status,
                "name_evidence": evidence,
                "in_pinned_counterpart": selector in pinned_entries,
                "pinned_entry_pc": pinned_entries.get(selector),
            })
        return out


def runtime_delta(baseline_entries, rows, pinned_rows):
    added = [row["selector"] for row in rows if not row["in_pinned_counterpart"]]
    removed = sorted(set(baseline_entries) - {row["selector"] for row in rows})
    changed = [{"selector": row["selector"], "pinned_entry_pc": row["pinned_entry_pc"],
                "entry_pc": row["entry_pc"]}
               for row in rows if row["pinned_entry_pc"] is not None
               and row["pinned_entry_pc"] != row["entry_pc"]]
    same = [row["selector"] for row in rows if row["pinned_entry_pc"] is not None
            and row["pinned_entry_pc"] == row["entry_pc"]]
    names = {row["selector"]: row["candidate_signature"] for row in rows}
    return {
        "runtime": None,
        "pinned_counterpart": None,
        "pinned_selectors": len(baseline_entries),
        "selectors": len(rows),
        "added": [{"selector": selector, "entry_pc": names_pc(rows, selector),
                   "candidate_signature": names.get(selector, "")} for selector in sorted(added)],
        "removed": [{"selector": selector,
                     "candidate_signature": pinned_rows[selector]["candidate_signature"]
                     or pinned_rows[selector]["reconstructed_signature"]}
                    for selector in removed],
        "changed_entry_pc": changed,
        "same_entry_pc": sorted(same),
        "counts": {"added": len(added), "removed": len(removed),
                   "changed_entry_pc": len(changed), "same_entry_pc": len(same)},
    }


def names_pc(rows, selector):
    return next(row["entry_pc"] for row in rows if row["selector"] == selector)


PACE = [2.0]


def rpc(method, params):
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    request = urllib.request.Request(RPC, json.dumps([payload]).encode(),
                                     {"Content-Type": "application/json"})
    for attempt in range(60):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                reply = json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            PACE[0] = min(PACE[0] * 1.2, 25.0)
            time.sleep(PACE[0])
            continue
        rows = reply if isinstance(reply, list) else [reply]
        if all(isinstance(row, dict) and row.get("error") for row in rows):
            message = str(rows[0]["error"].get("message", "")).lower()
            assert "rate limit" in message, reply
            PACE[0] = min(PACE[0] * 1.2, 25.0)
            time.sleep(PACE[0])
            continue
        assert isinstance(reply, list) and len(reply) == 1, reply
        assert "error" not in reply[0], reply[0]
        PACE[0] = max(PACE[0] * 0.9, 1.2)
        time.sleep(PACE[0])
        return {"request": payload, "response": reply[0], "at_utc": now_utc()}
    raise RuntimeError(f"RPC refused {method} after retries")


def ledger_from_raw():
    """Rebuild the pin ledger from the saved raw reads, so the ledger is checkable."""
    raw = read_json(RAW_PATH)
    by_key = {row["key"]: row for row in raw["reads"]}
    first = by_key["head_first"]["raw"]["result"]
    last = by_key["head_last"]["raw"]["result"]
    times = [row["at_utc"] for row in raw["reads"]]
    return {
        "pin": {"block": int(first["number"], 16),
                "block_hash": first["hash"],
                "timestamp": int(first["timestamp"], 16),
                "timestamp_utc": datetime.datetime.fromtimestamp(
                    int(first["timestamp"], 16), datetime.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "kind": "current_state_head_pin",
                "note": ORACLE_PIN_NOTE},
        "rpc": raw["rpc"],
        "chain_id_allowed": [CHAIN_ID],
        "chain_id_read": raw["chain_id"],
        "block_number_read": raw["block_number"],
        "capture_window": {"first_block": int(first["number"], 16), "first_hash": first["hash"],
                           "last_block": int(last["number"], 16), "last_hash": last["hash"]},
        "read_time_span": {"first": min(times), "last": max(times)},
        "captured_at_utc": raw["read_at_utc"],
        "checkpointed_reads": len(raw.get("reused_from_checkpoint", [])),
        "values": {row["key"]: row["raw"]["result"] for row in raw["reads"]
                   if not row["key"].startswith("code:")},
        "read_times": {row["key"]: row["at_utc"] for row in raw["reads"]},
        "raw_read": "artifacts/postpin_pin/raw_reads.json",
        "code_dir": "artifacts/postpin_pin/code",
    }


def load_ledger():
    """The saved ledger, cross-checked against the raw reads it was derived from."""
    derived = ledger_from_raw()
    if LEDGER_PATH.exists():
        assert read_json(LEDGER_PATH) == derived, "the ledger does not match the raw reads"
    return derived


def expected_keys():
    """Every ledger key one complete capture must hold."""
    keys = ["chain_id", "block_number", "head_first", "head_last", "exchange_owner_word",
            "exchange_authorized_executor_word"]
    keys += [f"code:{address}" for address in sorted(POST_REFRESH_ADDRESSES + list(PROXY_ADDRESSES))]
    for _, address, _ in PROXIES:
        keys += [f"implementation_word:{address}", f"admin_word:{address}"]
    for user in PT01_USERS:
        keys += [f"pt01_{label}_word:{user}" for label, _ in PT01_SLOTS]
        keys += [f"exchange_balances:{user}", f"exchange_pending_sweep_word:{user}",
                 f"exchange_get_pending_sweep:{user}"]
    keys += [key for key, _, _, _, _ in STATE_CALLS]
    return keys


def capture(resume=False):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    CODE_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint = read_json(CHECKPOINT) if resume and CHECKPOINT.exists() else {}
    reads = []
    reused = []
    failures = []

    def fetch(key, method, params, cacheable=True):
        """One value, one RPC call, raw reply saved. Reuses a checkpointed reply only
        when --resume was asked for; a value the endpoint will not serve this pass is
        recorded as a failure and the pass carries on to the next value."""
        was_reused = cacheable and key in checkpoint
        if was_reused:
            call = checkpoint[key]
            reused.append({"key": key, "at_utc": call["at_utc"]})
        else:
            try:
                call = rpc(method, params)
            except RuntimeError as error:
                failures.append({"key": key, "error": str(error)[:120]})
                return None
            if cacheable:
                checkpoint[key] = call
                write_json(CHECKPOINT, checkpoint)
        reads.append({"key": key, "method": method, "params": params, "at_utc": call["at_utc"],
                      "reused_from_checkpoint": was_reused, "raw": call["response"]})
        return call["response"]["result"]

    chain_id = fetch("chain_id", "eth_chainId", [], cacheable=False)
    block_number = fetch("block_number", "eth_blockNumber", [], cacheable=False)
    first_block = fetch("head_first", "eth_getBlockByNumber", ["latest", False], cacheable=False)
    if first_block is None:
        raise RuntimeError("the pin head could not be read; nothing written")

    # Code reads: the five post-refresh runtimes (this pin's own proof that the live code
    # still hashes to the saved bytes) and the eight proxies (proof they were not
    # replaced). The 25 unchanged implementations keep the baseline's captured runtimes,
    # already hash-pinned there.
    code_keys = sorted(POST_REFRESH_ADDRESSES + list(PROXY_ADDRESSES))
    codes = {}
    for stale in CODE_DIR.glob("*.hex"):
        if stale.stem not in code_keys:
            stale.unlink()
    for address in code_keys:
        result = fetch(f"code:{address}", "eth_getCode", [address, "latest"])
        if result is None:
            continue
        assert result != "0x", address
        codes[address] = result
        (CODE_DIR / f"{address}.hex").write_text(runtime_text(result))

    for _, address, _ in PROXIES:
        fetch(f"implementation_word:{address}", "eth_getStorageAt",
              [address, IMPLEMENTATION_SLOT, "latest"])
        fetch(f"admin_word:{address}", "eth_getStorageAt", [address, ADMIN_SLOT, "latest"])
    fetch("exchange_owner_word", "eth_getStorageAt", [EXCHANGE_PROXY, hex(0), "latest"])
    fetch("exchange_authorized_executor_word", "eth_getStorageAt",
          [EXCHANGE_PROXY, hex(88), "latest"])
    for user in PT01_USERS:
        for label, slot in PT01_SLOTS:
            fetch(f"pt01_{label}_word:{user}", "eth_getStorageAt",
                  [EXCHANGE_PROXY, mapping_slot_index(user, slot), "latest"])

    for key, _, target, calldata, _ in STATE_CALLS:
        fetch(key, "eth_call", [{"to": target, "data": calldata}, "latest"])
    for user in PT01_USERS:
        padded = user[2:].rjust(64, "0")
        fetch(f"exchange_balances:{user}", "eth_call",
              [{"to": EXCHANGE_PROXY, "data": "0x27e235e3" + padded}, "latest"])
        fetch(f"exchange_pending_sweep_word:{user}", "eth_call",
              [{"to": EXCHANGE_PROXY, "data": "0x7e4174fc" + padded}, "latest"])
        fetch(f"exchange_get_pending_sweep:{user}", "eth_call",
              [{"to": EXCHANGE_PROXY, "data": "0x31a4956c" + padded}, "latest"])

    last_block = fetch("head_last", "eth_getBlockByNumber", ["latest", False], cacheable=False)
    if last_block is None:
        raise RuntimeError("the closing head could not be read; nothing written")

    missing = sorted(set(expected_keys()) - {row["key"] for row in reads})
    if failures or missing:
        raise RuntimeError(
            f"{len(failures)} reads failed and {len(missing)} are still missing this pass "
            f"(re-run with --resume): failed={[row['key'] for row in failures][:8]} "
            f"missing={missing[:8]}")

    raw = {"rpc": RPC, "read_at_utc": now_utc(), "chain_id": chain_id,
           "block_number": block_number, "reads": reads,
           "reused_from_checkpoint": reused}
    RAW_PATH.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")

    ledger = ledger_from_raw()
    files, summary = build(ledger, codes)
    check(files, ledger, codes)
    write(files)
    write_json(LEDGER_PATH, ledger)
    return summary


def pinned_runtime_file(pinned_manifest, address):
    """The baseline manifest's runtime_file is relative to its own directory; this pin's
    manifest uses repo-root-relative paths, so resolve through the baseline directory."""
    relative = pinned_manifest["contracts"][address]["runtime_file"]
    assert relative.startswith("runtime/"), relative
    return f"atlas/block_{BASELINE_PIN}/{relative}"


def pinned_dispatcher_entries(pinned_manifest, address):
    return dispatcher_entries(hexbytes((ROOT / pinned_runtime_file(pinned_manifest, address)).read_text()))


def pinned_rows(path, address):
    catalog = read_json(path)
    if address not in catalog:
        return {}
    return {row["selector"]: row for row in catalog[address]["functions"]}


def build(ledger, codes):
    """Pure rebuild from the ledger plus the saved repo evidence."""
    pin = ledger["pin"]
    block = pin["block"]
    pinned_manifest = read_json(PIN_ATLAS / "manifest.json")
    suites = read_json(PIN_ATLAS / "suite_sets.json")
    postpin = suites["postpin_deployment"]
    explorer = read_json(POSTPIN_SUITE / "explorer_facts.json")["creation"]
    parity = read_json(ROOT / "artifacts" / "pt01_replacement_getter_parity" / "pinned_calls.json")
    values = ledger["values"]

    pin_time_words = {}
    for row in parity["rows"]:
        if row["selector"] == "0x7e4174fc":
            pin_time_words[word_to_address(row["calldata"])] = row["original"]["data"]

    contracts = {}
    # Unchanged addresses: recompute the hash from the baseline's saved runtime file and
    # point this pin's manifest at that file instead of copying it.
    for address, row in sorted(pinned_manifest["contracts"].items()):
        relative = pinned_runtime_file(pinned_manifest, address)
        code = (ROOT / relative).read_text()
        data = hexbytes(code)
        digest = hashlib.sha256(data).hexdigest()
        assert digest == row["sha256"], (address, digest, row["sha256"])
        assert "0x" + keccak()(data).hex() == row["keccak256"], address
        assert len(data) == row["runtime_bytes"], address
        contracts[address] = {
            "address": address,
            "role": row["role"],
            "address_status": "unchanged_from_pinned_manifest",
            "code_present": True,
            "runtime_bytes": row["runtime_bytes"],
            "sha256": row["sha256"],
            "keccak256": row["keccak256"],
            "runtime_file": relative,
            "runtime_file_base": "repo_root",
            "runtime_source": "atlas/block_48902346/runtime (pinned baseline, not copied)",
            "origin": row["origin"],
            "pinned_implementation": row["eip1967_slots"]["implementation"],
            "current_implementation": None,
            "eip1967_slots": row["eip1967_slots"],
            "eip1967_reads": {},
            "runtime_verified_against_live_code_read": None,
        }
    # Post-refresh addresses: runtime copied into this pin's own directory from the
    # captured code read; hash cross-checked against the post-pin capture and the suite
    # ledger.
    for address, role, supersedes in POST_REFRESH:
        code = runtime_text(codes[address])
        data = hexbytes(code)
        digest = hashlib.sha256(data).hexdigest()
        saved = (POSTPIN_SUITE / "runtime" / f"{address}.hex").read_text()
        assert code == saved, address
        assert digest == postpin[address]["sha256"], address
        assert len(data) == postpin[address]["runtime_bytes"], address
        contracts[address] = {
            "address": address,
            "role": role,
            "address_status": "added_by_the_post_refresh_governance_batch",
            "code_present": True,
            "runtime_bytes": len(data),
            "sha256": digest,
            "keccak256": "0x" + keccak()(data).hex(),
            "runtime_file": f"atlas/block_{block}/runtime/{address}.hex",
            "runtime_file_base": "repo_root",
            "runtime_source": "captured eth_getCode at this pin (see runtime_verified_against_live_code_read)",
            "origin": {"kind": "deployer_creation", "deployer": explorer[address]["creator"],
                       "block": explorer[address]["block"], "tx": explorer[address]["tx"],
                       "timestamp": explorer[address]["timestamp"],
                       "deployer_nonce": postpin[address]["deployer_nonce"]},
            "pinned_implementation": None,
            "current_implementation": None,
            "replaces": {"role": pinned_manifest["contracts"][supersedes]["role"],
                         "address": supersedes,
                         "sha256": pinned_manifest["contracts"][supersedes]["sha256"],
                         "runtime_file": pinned_runtime_file(pinned_manifest, supersedes)}
            if supersedes else None,
            "added_note": ("no pinned counterpart: the newest suite had no BuilderRegistry "
                           "before the 2026-10-21 batch" if supersedes is None else
                           "supersedes the pinned target recorded in `replaces`"),
            "eip1967_slots": {"implementation": ZERO_WORD, "admin": ZERO_WORD,
                              "beacon": ZERO_WORD},
            "eip1967_reads": {},
            "runtime_verified_against_live_code_read": f"code:{address}",
        }
    # Proxy slots: the live implementation and admin words, plus the pinned target.
    moved = {}
    for role, address, implementation_role in PROXIES:
        row = contracts[address]
        implementation_word = values[f"implementation_word:{address}"]
        admin_word = values[f"admin_word:{address}"]
        row["eip1967_slots"] = {"implementation": implementation_word, "admin": admin_word,
                                "beacon": ZERO_WORD}
        row["eip1967_reads"] = {"implementation": f"implementation_word:{address}",
                                "admin": f"admin_word:{address}"}
        row["current_implementation"] = word_to_address(implementation_word)
        row["current_implementation_role"] = (
            contracts[row["current_implementation"]]["role"]
            if row["current_implementation"] in contracts else None)
        row["implementation_role"] = implementation_role
        row["runtime_verified_against_live_code_read"] = f"code:{address}"
        if row["current_implementation"] != word_to_address(row["pinned_implementation"]):
            moved[address] = {"role": role, "implementation_role": implementation_role,
                              "from": word_to_address(row["pinned_implementation"]),
                              "to": row["current_implementation"],
                              "to_sha256": contracts[row["current_implementation"]]["sha256"],
                              "to_runtime_bytes": contracts[row["current_implementation"]]["runtime_bytes"]}
    assert len(moved) == 3, moved

    manifest = {
        "chain_id": CHAIN_ID,
        "block": block,
        "block_hash": pin["block_hash"],
        "timestamp": pin["timestamp"],
        "timestamp_utc": pin["timestamp_utc"],
        "pin_kind": "current_state_head_pin_additive_to_the_audited_baseline",
        "rpc": ledger["rpc"],
        "captured_at_utc": ledger["captured_at_utc"],
        "capture_window_blocks": [ledger["capture_window"]["first_block"],
                                  ledger["capture_window"]["last_block"]],
        "read_time_span_utc": [ledger["read_time_span"]["first"], ledger["read_time_span"]["last"]],
        "state_read_note": ORACLE_PIN_NOTE,
        "runtime_file_base": "repo_root",
        "unchanged_code_read_note": ("this pin re-read code only for the five post-refresh "
                                     "addresses and the eight proxies; the 25 unchanged "
                                     "implementations keep the audited baseline's captured "
                                     "runtime files, whose hashes are recomputed here rather "
                                     "than re-read from the chain"),
        "sources": [
            "artifacts/postpin_pin/raw_reads.json",
            "artifacts/postpin_pin/state_reads.json",
            "artifacts/postpin_pin/code/*.hex",
            "atlas/block_48902346/manifest.json",
            "atlas/block_48902346/selector_catalog.json",
            "atlas/block_48902346/suite_sets.json",
            "artifacts/postpin_suite/runtime/*.hex",
            "artifacts/postpin_suite/explorer_facts.json",
        ],
        "scope_note": ("The newest suite (docs contract set 1) as it stands after the "
                       "2026-10-21 contract-set-2 batch: its own 19 direct contracts, the "
                       "governance contracts behind it, the linked libraries, and the five "
                       "contracts the refresh added. Unchanged runtimes are not duplicated; "
                       "their runtime_file points at the audited baseline. Proxy "
                       "implementation and admin words are current-state reads, not archive "
                       "state, and the two implementation variants never installed are "
                       "carried from the baseline."),
        "supersedes": {
            "manifest": "atlas/block_48902346/manifest.json",
            "pin": BASELINE_PIN,
            "block_hash": pinned_manifest["block_hash"],
            "relationship": "additive pin; the audited baseline is not replaced or rewritten",
            "previous_pin_implementation_change": moved,
            "unchanged_proxy_implementations": {
                role: contracts[address]["pinned_implementation"]
                for role, address, _ in PROXIES if address not in moved},
        },
        "adds": {
            "addresses": POST_REFRESH_ADDRESSES,
            "note": ("three implementations, one linked library and one registry the refresh "
                     "added; every other address here is the baseline's"),
            "selector_catalog": f"atlas/block_{block}/selector_catalog.json",
        },
        "deposit_proxy_family": pinned_manifest["deposit_proxy_family"],
        "contracts": contracts,
    }

    catalog = {"block": block, "chain_id": CHAIN_ID, "block_hash": pin["block_hash"],
               "runtime_file_base": "repo_root",
               "method": ("dispatcher decoded on the exact saved runtime bytes as "
                          "PUSH4 <selector> EQ PUSH2 <entry> JUMPI; argument widths from the "
                          "entry's own calldatasize guard, falling back to cast inference on "
                          "the same bytes"),
               "baseline": {"manifest": "atlas/block_48902346/manifest.json",
                            "catalog": "atlas/block_48902346/selector_catalog.json",
                            "pin": BASELINE_PIN},
               "catalogs": {}, "delta": {}, "counts": {}, "unknowns": []}
    for address, role in sorted(CATALOG_ROLES.items()):
        supersedes = dict((a, s) for a, _, s in POST_REFRESH)[address]
        baseline_rows = (pinned_rows(PIN_ATLAS / "selector_catalog.json", supersedes)
                         if supersedes else {})
        baseline_entries = {}
        if supersedes:
            baseline_entries = pinned_dispatcher_entries(pinned_manifest, supersedes)
            assert sorted(baseline_rows) == sorted(baseline_entries), (
                supersedes, "the baseline catalog and the dispatcher decode disagree")
        rows = Runtime(address, role, codes[address].strip(),
                       contracts[address]["runtime_file"], supersedes).rows(
            baseline_rows, baseline_entries)
        delta = runtime_delta(baseline_entries, rows, baseline_rows)
        delta["runtime"] = address
        delta["pinned_counterpart"] = supersedes
        catalog["catalogs"][address] = {
            "role": role,
            "sha256": contracts[address]["sha256"],
            "runtime_bytes": contracts[address]["runtime_bytes"],
            "runtime_file": contracts[address]["runtime_file"],
            "pinned_counterpart": supersedes,
            "counts": {"selectors": len(rows),
                       "observed_calldatasize_guard": sum(
                           1 for row in rows if row["observed_calldatasize_guard_bytes"] is not None),
                       "hash_matched_name_candidates": sum(
                           1 for row in rows
                           if row["name_status"] == "public_registry_candidate_hash_matched"),
                       "unresolved_names": sum(1 for row in rows if row["name_status"] == "unresolved"),
                       "names_carried_from_baseline": sum(
                           1 for row in rows
                           if row["name_status"] == "baseline_name_carried_not_reproven_on_this_runtime"),
                       "in_pinned_counterpart": sum(1 for row in rows if row["in_pinned_counterpart"])},
            "cast_warnings": [],
            "functions": rows,
        }
        catalog["delta"][address] = delta
    unresolved_added = sorted(selector for address, delta in catalog["delta"].items()
                              for row in delta["added"] for selector in [row["selector"]]
                              if not row["candidate_signature"])
    unresolved_removed = sorted(selector for address, delta in catalog["delta"].items()
                                for row in delta["removed"] for selector in [row["selector"]]
                                if not row["candidate_signature"])
    catalog["counts"] = {
        "runtimes": len(catalog["catalogs"]),
        "selectors": sum(entry["counts"]["selectors"] for entry in catalog["catalogs"].values()),
        "added": sum(entry["counts"]["added"] for entry in catalog["delta"].values()),
        "removed": sum(entry["counts"]["removed"] for entry in catalog["delta"].values()),
        "changed_entry_pc": sum(entry["counts"]["changed_entry_pc"]
                                for entry in catalog["delta"].values()),
        "same_entry_pc": sum(entry["counts"]["same_entry_pc"] for entry in catalog["delta"].values()),
        "unresolved_added_selectors": len(unresolved_added),
        "unresolved_removed_selectors": len(unresolved_removed),
    }
    catalog["counts"]["unresolved_added"] = unresolved_added
    catalog["counts"]["unresolved_removed"] = unresolved_removed
    catalog["unknowns"] = [
        (f"{len(unresolved_added) + len(unresolved_removed)} selectors the refresh moved have no "
         f"hash-matched public name: {', '.join(unresolved_added)} added, "
         f"{', '.join(unresolved_removed)} dropped"),
        "no verified source exists for any post-refresh runtime; candidate names only "
        "hash-match the selector bytes",
        "the baseline's reconstructed names are carried as hypotheses for the new runtimes; "
        "they were derived from the pinned bytes and are not re-proven here",
    ]

    state = {"pin": pin, "rpc": ledger["rpc"], "chain_id": CHAIN_ID,
             "capture_window": ledger["capture_window"],
             "captured_at_utc": ledger["captured_at_utc"],
             "checkpointed_reads": ledger.get("checkpointed_reads", 0),
             "read_times": ledger.get("read_times", {}),
             "note": ORACLE_PIN_NOTE,
             "raw_read": ledger["raw_read"],
             "rows": [], "pt01": {}, "infrastructure": {}}

    def value_of(key):
        return values[key]

    def signature(key, selector):
        name, status, evidence = READ_SIGNATURE_CITATIONS.get(
            selector, ("", "unresolved", None))
        return {"selector": selector, "candidate_signature": name,
                "signature_status": status, "evidence": evidence, "read": key}

    infrastructure = state["infrastructure"]
    infrastructure["proxy_admin_owner"] = {
        **signature("proxy_admin_owner", "0x8da5cb5b"),
        "address": PROXY_ADMIN, "value": word_to_address(value_of("proxy_admin_owner")),
        "raw": value_of("proxy_admin_owner"),
        "meaning": "the ProxyAdmin behind every newest-suite proxy is owned by the newest timelock"}
    infrastructure["timelock"] = {
        "address": TIMELOCK,
        "owner": {**signature("timelock_owner", "0x8da5cb5b"),
                  "value": word_to_address(value_of("timelock_owner")),
                  "raw": value_of("timelock_owner")},
        "minimum_delay_seconds": {**signature("timelock_min_delay", "0xc63c4e9b"),
                                  "value": word_to_int(value_of("timelock_min_delay")),
                                  "raw": value_of("timelock_min_delay")},
        "minimum_delay_history": ("604800 s set at creation (block 47855496), lowered to "
                                  "86400 s at block 49050825; see "
                                  "atlas/block_48902346/suite_sets.md"),
    }
    signers = [word_to_address(value_of(f"multisig_signer_{name}"))
               for name in ("one", "two", "three")]
    infrastructure["multisig"] = {
        "address": MULTISIG,
        "threshold": {**signature("multisig_required_confirmations", "0x82e717f7"),
                      "value": word_to_int(value_of("multisig_required_confirmations")),
                      "raw": value_of("multisig_required_confirmations")},
        "signer_count": len(signers),
        "signers": signers,
        "signer_reads": {f"signer_{name}": f"multisig_signer_{name}"
                         for name in ("one", "two", "three")},
        "transaction_count": {**signature("multisig_transaction_count", "0xb77bf600"),
                              "value": word_to_int(value_of("multisig_transaction_count")),
                              "raw": value_of("multisig_transaction_count")},
        "pinned_comparison": {
            "required_confirmations": read_json(PIN_ATLAS / "multisig_behavior.json")["required_confirmations"],
            "signers": read_json(PIN_ATLAS / "multisig_behavior.json")["signers"],
            "evidence": "atlas/block_48902346/multisig_behavior.json",
        },
    }
    infrastructure["exchange_authorized_executor"] = {
        "address": EXCHANGE_PROXY,
        "storage_slot": 88,
        "storage_read": "exchange_authorized_executor_word",
        "storage_word": value_of("exchange_authorized_executor_word"),
        "call": {**signature("exchange_authorized_executor", "0x13dd495b"),
                 "raw": value_of("exchange_authorized_executor"),
                 "value": word_to_address(value_of("exchange_authorized_executor"))},
        "pinned_word": next(row["old_word"] for row in
                            read_json(PIN_ATLAS / "exchange_admin_setters_behavior.json")["setter_rows"]
                            if row["selector"] == "0xd188c049"),
        "pinned_evidence": "atlas/block_48902346/exchange_admin_setters_behavior.json "
                           "(setAuthorizedExecutor is storage slot 88)",
    }
    for name in ("owner", "guardian"):
        value = word_to_address(value_of(f"builder_registry_{name}"))
        infrastructure[f"builder_registry_{name}"] = {
            **signature(f"builder_registry_{name}", "0x8da5cb5b" if name == "owner" else "0x452a9320"),
            "address": "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248",
            "value": value, "raw": value_of(f"builder_registry_{name}")}

    for role, address, _ in PROXIES:
        row = contracts[address]
        state["rows"].append({
            "kind": "proxy", "role": role, "address": address,
            "implementation_read": row["eip1967_reads"]["implementation"],
            "implementation_word": row["eip1967_slots"]["implementation"],
            "implementation": row["current_implementation"],
            "implementation_role": row["current_implementation_role"],
            "admin_read": row["eip1967_reads"]["admin"],
            "admin_word": row["eip1967_slots"]["admin"],
            "admin": word_to_address(row["eip1967_slots"]["admin"]),
            "pinned_implementation": word_to_address(row["pinned_implementation"]),
            "moved": address in moved,
        })
    state["rows"].append({
        "kind": "nonproxy", "role": "exchange_owner_slot",
        "address": EXCHANGE_PROXY, "storage_slot": 0,
        "storage_read": "exchange_owner_word", "storage_word": value_of("exchange_owner_word"),
        "call_read": "exchange_owner", "call_word": value_of("exchange_owner"),
        "owner": word_to_address(value_of("exchange_owner")),
        "owner_shift_bits": 16,
        "pinned_evidence": "atlas/block_48902346/exchange_admin_setters_behavior.json "
                           "(transferOwnership is storage slot 0, 16-bit shift)",
    })

    for user in PT01_USERS:
        pending = value_of(f"pt01_pending_sweep_word:{user}")
        balances = value_of(f"pt01_balances_word:{user}")
        getter = value_of(f"exchange_get_pending_sweep:{user}")
        words = [int(getter[2:][i:i + 64], 16) for i in range(0, len(getter) - 2, 64)]
        state["pt01"][user] = {
            "deposit_proxy": suites["pt01"][user]["proxy"],
            "deposit_proxy_evidence": "atlas/block_48902346/suite_sets.json pt01",
            "pending_sweep_mapping_slot": 33,
            "pending_sweep_key": mapping_slot_index(user, 33),
            "pending_sweep_read": f"pt01_pending_sweep_word:{user}",
            "pending_sweep_word": pending,
            "pending_sweep_call_read": f"exchange_pending_sweep_word:{user}",
            "pending_sweep_call": value_of(f"exchange_pending_sweep_word:{user}"),
            "get_pending_sweep_read": f"exchange_get_pending_sweep:{user}",
            "get_pending_sweep_raw": getter,
            "get_pending_sweep_words": ["0x%064x" % word for word in words],
            "get_pending_sweep_shape": ("four words: [count, amount, zero, block]; the packed "
                                        "pendingSweepWord equals amount | (block << 128), "
                                        "verified on both users and not a decoded source name"),
            "get_pending_sweep_reconstructs_pending_word":
                (words[3] << 128) | words[1] == int(pending, 16),
            "balances_mapping_slot": 9,
            "balances_key": mapping_slot_index(user, 9),
            "balances_read": f"pt01_balances_word:{user}",
            "balances_word": balances,
            "balances_call_read": f"exchange_balances:{user}",
            "balances_call": value_of(f"exchange_balances:{user}"),
            "pending_sweep_word_at_pin": pin_time_words.get(user),
            "pending_sweep_word_at_pin_evidence":
                "artifacts/pt01_replacement_getter_parity/pinned_calls.json (pendingSweepWord call at pin 48902346)",
            "balance_word_at_pin": suites["pt01"][user]["exchange_balance_word"],
            "balance_word_at_pin_evidence": "atlas/block_48902346/suite_sets.json pt01",
            "clear_pending_sweep_dispatched": "0x2362f4de" in dispatcher_entries(
                hexbytes(runtime_text(codes["0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"]))),
        }

    files = {
        f"atlas/block_{block}/manifest.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        f"atlas/block_{block}/selector_catalog.json": json.dumps(catalog, indent=2, sort_keys=True) + "\n",
        f"atlas/block_{block}/state_reads.json": json.dumps(state, indent=2, sort_keys=True) + "\n",
    }
    for address, _, _ in POST_REFRESH:
        files[f"atlas/block_{block}/runtime/{address}.hex"] = runtime_text(codes[address])
    files[f"atlas/block_{block}/repin.md"] = render_doc(manifest, catalog, state)
    summary = {
        "pin": block, "block_hash": pin["block_hash"], "timestamp_utc": pin["timestamp_utc"],
        "implementations": {row[1]: contracts[row[0]]["sha256"] for row in POST_REFRESH},
        "selector_delta_counts": catalog["counts"],
        "moved": moved,
    }
    return files, summary


def render_doc(manifest, catalog, state):
    lines = []
    block = manifest["block"]

    def add(text=""):
        lines.append(text)

    add(f"# Post-refresh pin at block {block}")
    add("")
    add(f"Generated by [`atlas_postpin_pin.py`](../../scripts/atlas_postpin_pin.py); "
        f"`python3 scripts/atlas_postpin_pin.py` re-checks every number below offline from the saved "
        f"reads under `artifacts/postpin_pin/`.")
    add("")
    add(f"Pin block **{block}** (`{manifest['block_hash']}`, {manifest['timestamp_utc']}), "
        f"the head captured by this pin. It is a second, additive pin: the audited baseline at "
        f"block {BASELINE_PIN} stays as it is, and every runtime this pin did not have to "
        f"re-capture keeps pointing at `atlas/block_{BASELINE_PIN}/runtime/`.")
    add("")
    add(f"_{ORACLE_PIN_NOTE}_")
    add("")
    span = manifest["read_time_span_utc"]
    add(f"The head above is the block the capture closed on. The value reads the tables below "
        f"quote were taken between {span[0]} and {span[1]} UTC "
        f"(`read_time_span_utc` in `manifest.json`); the RPC answers each `latest` read at "
        f"whatever block is then current, and `raw_reads.json` carries the time of every read.")
    add("")
    if state.get("checkpointed_reads"):
        add(f"Because the public endpoint rate-limits hard, "
            f"{state['checkpointed_reads']} of the {len(state.get('read_times', {}))} reads were "
            f"reused from an earlier capture pass of the same window; `raw_reads.json` marks each "
            f"reused reply, and `check()` re-checks the whole ledger against those raw replies.")
        add("")
    add("## The sets and their dates")
    add("")
    add("| Set | Deployer | Created (UTC) | Direct | Docs version |")
    add("|---|---|---|---:|---|")
    for name, deployer, dates, docs in SETS:
        direct = 7 if name == "postpin_refresh" else 19
        add(f"| `{name}` | `{deployer}` | {dates} | {direct} | {docs} |")
    add("")
    add("`newest` is the docs' contract set 1 and `postpin_refresh` is contract set 2. The two "
        "later sets share the `newest` proxies, ProxyAdmin, timelock and multisig; the refresh "
        "deployed no proxy and no governance contract. Source: "
        "`atlas/block_48902346/suite_sets.md`.")
    add("")
    add("## What moved and what did not")
    add("")
    add("| Proxy | Role | Pinned implementation | Implementation now | Impl. bytes | Impl. SHA-256 |")
    add("|---|---|---|---|---:|---|")
    for role, address, _ in PROXIES:
        row = manifest["contracts"][address]
        current = manifest["contracts"][row["current_implementation"]]
        add(f"| `{address}` | `{role}` | `{word_to_address(row['pinned_implementation'])}` | "
            f"`{row['current_implementation']}` | {current['runtime_bytes']} | "
            f"`{current['sha256'][:12]}...` |")
    add("")
    add("Three proxies moved, in the 2026-10-21 batch that the newest timelock executed at block "
        "49169385 (multisig records 9 and 10, transaction "
        "`0x4410b81e3eb76f83f5ddc4e3faee794fb67208d2f129bc013094b9d06055acb6`): the Exchange, "
        "SessionKeyManager and Tokenomics proxies. The oracle, staking, PAPER, batch-executor and "
        "deposit-factory proxies still point at their pinned implementations, byte for byte.")
    add("")
    add("Five runtimes were added to the atlas by this pin:")
    add("")
    add("| Role | Address | Bytes | SHA-256 | Supersedes |")
    add("|---|---|---:|---|---|")
    for address, role, supersedes in POST_REFRESH:
        row = manifest["contracts"][address]
        add(f"| `{role}` | `{address}` | {row['runtime_bytes']} | `{row['sha256'][:12]}...` | "
            f"{('`%s`' % supersedes) if supersedes else 'nothing pinned (registry is new)'} |")
    add("")
    add("Every non-proxy runtime is unchanged from the baseline, including the two Exchange "
        "variants that were never installed. Full hashes and the file each hash recomputes from "
        f"are in `manifest.json`; the unchanged rows point at "
        f"`atlas/block_{BASELINE_PIN}/runtime/` so nothing is duplicated. This pin re-read the "
        "eight proxy runtimes from the chain and each still hashes to the baseline's 925-byte "
        "`ee856dd4cb...`, so no proxy was replaced; the other unchanged rows keep the baseline's "
        "captured bytes, already hash-pinned there.")
    add("")
    add("## Selectors on the new runtimes")
    add("")
    add("Decoded on the exact saved bytes. `entry` is the JUMPDEST the dispatcher's `PUSH4 <sel> "
        "EQ PUSH2 <entry> JUMPI` reaches; widths come from the entry's own calldatasize guard "
        "where solc emitted one, and from `cast` inference on the same bytes otherwise.")
    add("")
    add("| Runtime | Selectors | Added | Removed | Same entry pc | Changed entry pc | No name on this runtime |")
    add("|---|---:|---:|---:|---:|---:|---|")
    for address, entry in sorted(catalog["catalogs"].items()):
        delta = catalog["delta"][address]
        add(f"| `{entry['role']}` ({entry['runtime_bytes']} B) | {entry['counts']['selectors']} | "
            f"{delta['counts']['added']} | {delta['counts']['removed']} | "
            f"{delta['counts']['same_entry_pc']} | {delta['counts']['changed_entry_pc']} | "
            f"{entry['counts']['unresolved_names']} |")
    add("")
    add("`No name on this runtime` counts every selector the catalog could not name, including "
        "carried-over selectors the baseline also left unnamed (the Exchange linked library is "
        "unnamed in the pinned catalog too). The selectors the refresh itself moved are listed "
        "below.")
    add("")
    add("Selector counts in total: "
        + ", ".join(f"{key} {value}" for key, value in sorted(catalog["counts"].items())
                    if not key.startswith("unresolved_added")
                    and not key.startswith("unresolved_removed")) + ".")
    add("")
    add("Added selectors, with the name evidence the catalog carries for each:")
    add("")
    add("| Runtime | Selector | Entry pc | Candidate name | Name status |")
    add("|---|---|---:|---|---|")
    for address, delta in sorted(catalog["delta"].items()):
        rows = {row["selector"]: row for row in catalog["catalogs"][address]["functions"]}
        for row in delta["added"]:
            source = rows[row["selector"]]
            add(f"| `{catalog['catalogs'][address]['role']}` | `{row['selector']}` | "
                f"{hex(row['entry_pc'])} | {('`%s`' % row['candidate_signature']) or 'unresolved'} | "
                f"{source['name_status']} |")
    add("")
    add("Removed selectors:")
    add("")
    add("| Runtime | Selector | Name evidence at the baseline |")
    add("|---|---|---|")
    for address, delta in sorted(catalog["delta"].items()):
        for row in delta["removed"]:
            add(f"| `{catalog['catalogs'][address]['role']}` | `{row['selector']}` | "
                f"{('`%s`' % row['candidate_signature']) or 'unresolved'} |")
    add("")
    add("A candidate name is only a hash match on the public signature database: it proves some "
        "function with that signature exists there, not that this contract implements it. The "
        "pinned baseline's reconstructed names, carried over for selectors that already existed, "
        "were derived from the pinned bytes and behaviour and are not re-proven on these runtimes.")
    add("")
    add("## Pinned read-only state")
    add("")
    add("Owners and governance:")
    add("")
    add("| Value | Address | Reading | Cite |")
    add("|---|---|---|---|")
    infrastructure = state["infrastructure"]
    add(f"| ProxyAdmin owner | `{PROXY_ADMIN}` | `{infrastructure['proxy_admin_owner']['value']}` | "
        f"`{infrastructure['proxy_admin_owner']['read']}` |")
    add(f"| Timelock owner | `{infrastructure['timelock']['address']}` | "
        f"`{infrastructure['timelock']['owner']['value']}` | `{infrastructure['timelock']['owner']['read']}` |")
    add(f"| Timelock minimum delay | `{infrastructure['timelock']['address']}` | "
        f"{infrastructure['timelock']['minimum_delay_seconds']['value']} s | "
        f"`{infrastructure['timelock']['minimum_delay_seconds']['read']}` |")
    add(f"| Multisig threshold | `{infrastructure['multisig']['address']}` | "
        f"{infrastructure['multisig']['threshold']['value']} of "
        f"{infrastructure['multisig']['signer_count']} | `{infrastructure['multisig']['threshold']['read']}` |")
    add(f"| Multisig transaction count | `{infrastructure['multisig']['address']}` | "
        f"{infrastructure['multisig']['transaction_count']['value']} | "
        f"`{infrastructure['multisig']['transaction_count']['read']}` |")
    add(f"| BuilderRegistry owner | `{infrastructure['builder_registry_owner']['address']}` | "
        f"`{infrastructure['builder_registry_owner']['value']}` | "
        f"`{infrastructure['builder_registry_owner']['read']}` |")
    add(f"| BuilderRegistry guardian | `{infrastructure['builder_registry_guardian']['address']}` | "
        f"`{infrastructure['builder_registry_guardian']['value']}` | "
        f"`{infrastructure['builder_registry_guardian']['read']}` |")
    add(f"| Exchange owner | `{EXCHANGE_PROXY}` | "
        f"`{next(row['owner'] for row in state['rows'] if row.get('owner'))}` | "
        f"slot 0 word + `exchange_owner` |")
    add("")
    add(f"Multisig signers: " + ", ".join(f"`{signer}`" for signer in infrastructure["multisig"]["signers"])
        + f"; the pinned multisig records the same "
        f"{infrastructure['multisig']['pinned_comparison']['required_confirmations']}-of-"
        f"{len(infrastructure['multisig']['pinned_comparison']['signers'])} and the same signers "
        f"(`{infrastructure['multisig']['pinned_comparison']['evidence']}`).")
    add("")
    add("Proxy implementation words (the EIP-1967 implementation slot, read at this pin):")
    add("")
    add("| Role | Proxy | Implementation word | Implied address | Pinned target | Moved |")
    add("|---|---|---|---|---|---|")
    for row in state["rows"]:
        if row["kind"] != "proxy":
            continue
        add(f"| `{row['role']}` | `{row['address']}` | `{row['implementation_word']}` | "
            f"`{row['implementation']}` | `{row['pinned_implementation']}` | "
            f"{'yes' if row['moved'] else 'no'} |")
    add("")
    authorized = infrastructure["exchange_authorized_executor"]
    add(f"Exchange `authorizedExecutor` (storage slot {authorized['storage_slot']}): "
        f"word `{authorized['storage_word']}` and call `{authorized['call']['value']}` agree; "
        f"the pinned word was `{authorized['pinned_word']}`, "
        f"{'unchanged' if authorized['pinned_word'] == authorized['storage_word'] else 'changed since the pin'} "
        f"(`{authorized['pinned_evidence']}`).")
    add("")
    add("PT-01 pending sweep and balance words:")
    add("")
    add("| User | Pending sweep word | At pin | Balance word | `balances(user)` | "
        "`getPendingSweep` words | `clearPendingSweep` dispatched |")
    add("|---|---|---|---|---|---|---|")
    for user, row in sorted(state["pt01"].items()):
        add(f"| `{user}` | `{row['pending_sweep_word']}` | `{row['pending_sweep_word_at_pin']}` | "
            f"`{row['balances_word']}` | `{row['balances_call']}` | "
            f"`{', '.join('0x%x' % int(word, 16) for word in row['get_pending_sweep_words'])}` | "
            f"{'yes' if row['clear_pending_sweep_dispatched'] else 'no'} |")
    add("")
    add("`getPendingSweep(user)` returns four words `[count, amount, zero, block]`, and the packed "
        "`pendingSweepWord(user)` recomputes as `amount | (block << 128)` for both users; the "
        "slot-33 mapping word, the `pendingSweepWord` call and the packed word inside "
        "`getPendingSweep` all agree.")
    add("")
    add("Both pending words are byte-identical to the pin-time `pendingSweepWord` reads "
        "(`artifacts/pt01_replacement_getter_parity/pinned_calls.json`, pin "
        f"{BASELINE_PIN}) and both balance words are zero, as they were at the pin "
        "(`atlas/block_48902346/suite_sets.json` pt01). The pending words are the same "
        "accounting state PT-01 opened with: a sweep left uncredited. `clearPendingSweep` "
        "(`0x2362f4de`) is still absent from the Exchange dispatcher on the new implementation.")
    add("")
    add("## Proven, read-only-current, unknown")
    add("")
    add("**Exact (hash-checked off the saved bytes).** The five runtime hashes, their sizes, and "
        "the keccak-256 in `manifest.json` recompute from the files this pin saved; each of those "
        "files is byte-identical to the matching file under `artifacts/postpin_suite/runtime/` "
        "and to the SHA-256 recorded in `atlas/block_48902346/suite_sets.json` "
        "(`postpin_deployment`), so the live code has not changed since that capture. The 25 "
        "unchanged addresses recompute to the baseline's recorded hashes from the baseline's own "
        "files. The dispatcher decode, entry pcs, argument widths and the added/removed sets are "
        "computed here from those bytes, and the three moved proxies are exactly the three "
        "`ProxyAdmin.upgrade` targets in the multisig's executed batch.")
    add("")
    add("**Read-only-current.** Every owner, delay, threshold, signer, storage word and balance "
        "quoted above comes from a `latest` read, taken from the public HyperEVM RPC. "
        "The RPC ignores the block parameter and offers no `debug_traceTransaction` or "
        "`debug_traceCall`, so none of these are archive or pinned-state values; they are what "
        "the chain answers now, bounded by the capture window recorded in the ledger.")
    add("")
    add("**Unknown.**")
    add("")
    for item in (
        catalog["unknowns"][0],
        "no verified source exists for the five post-refresh contracts; Heimdall output and "
        "public-registry signatures are navigation hints, not evidence",
        "the upgrade trigger and the reason for the 2026-10-21 batch: the timelock and multisig "
        "records carry what ran, not why, and the docs state no reason",
        "delivery is unmeasured: no saved transaction exercises the added builder-fee, rebate or "
        "registry selectors, so nothing here shows the new paths working end to end",
        "no archive HyperEVM RPC and no debug trace: historical state at or before this pin could "
        "not be re-derived, so this pin adds no new historical claim",
        "whether the new Exchange adds a differently shaped pending-sweep clear or credit route "
        "outside the dispatched selector set; the owner `reconcileSweepCredit` path still reverts",
        "`recovery/Pt01Recovery.sol` still delegates to the pinned implementation "
        "`0x0f3febfc94876b0c895f7acecdc8f5c863b549ee`, which is no longer behind the Exchange "
        "proxy, so that candidate needs re-deriving against the live implementation",
    ):
        add(f"- {item}")
    add("")
    return "\n".join(lines)


def check(files, ledger, codes):
    """Assert the rebuilt files against the ledger and the saved repo evidence."""
    pin = ledger["pin"]
    block = pin["block"]
    values = ledger["values"]
    manifest = json.loads(files[f"atlas/block_{block}/manifest.json"])
    catalog = json.loads(files[f"atlas/block_{block}/selector_catalog.json"])
    state = json.loads(files[f"atlas/block_{block}/state_reads.json"])
    pinned_manifest = read_json(PIN_ATLAS / "manifest.json")
    suites = read_json(PIN_ATLAS / "suite_sets.json")

    def text_of(relative):
        """Rebuilt files come from memory; every other path stays on disk."""
        return files[relative] if relative in files else (ROOT / relative).read_text()

    # 0. the captured code reads are exactly the addresses this pin read
    assert sorted(path.stem for path in CODE_DIR.glob("*.hex")) == sorted(
        POST_REFRESH_ADDRESSES + list(PROXY_ADDRESSES))

    # 1. the pin head itself, straight out of the saved raw response
    assert ledger["chain_id_allowed"] == [CHAIN_ID]
    assert int(ledger["chain_id_read"], 16) == CHAIN_ID
    window = ledger["capture_window"]
    assert window["first_block"] == block and window["first_hash"] == pin["block_hash"]
    assert abs(int(ledger["block_number_read"], 16) - window["first_block"]) <= 16, ledger["block_number_read"]
    assert ledger["read_time_span"]["first"] <= ledger["read_time_span"]["last"]
    assert 0 <= window["last_block"] - window["first_block"] < 64, window
    assert manifest["block_hash"] == pin["block_hash"] and manifest["block"] == block
    assert manifest["read_time_span_utc"] == [ledger["read_time_span"]["first"],
                                              ledger["read_time_span"]["last"]]

    # 2. every manifest hash recomputes from a saved runtime file
    for address, row in manifest["contracts"].items():
        data = hexbytes(text_of(row["runtime_file"]))
        assert hashlib.sha256(data).hexdigest() == row["sha256"], address
        assert "0x" + keccak()(data).hex() == row["keccak256"], address
        assert len(data) == row["runtime_bytes"], address
        assert row["code_present"] is True
        assert row["runtime_file_base"] == "repo_root"
    # ... and this pin's own runtime files are byte-identical to the post-pin capture
    for address, role, _ in POST_REFRESH:
        row = manifest["contracts"][address]
        text = text_of(row["runtime_file"])
        assert text == (POSTPIN_SUITE / "runtime" / f"{address}.hex").read_text(), address
        assert row["sha256"] == suites["postpin_deployment"][address]["sha256"], address
        assert row["runtime_bytes"] == suites["postpin_deployment"][address]["runtime_bytes"], address
        assert runtime_text(codes[address]) == text, address
    # ... and the proxies this pin read still carry the baseline's 925-byte runtime
    for role, address, _ in PROXIES:
        row = manifest["contracts"][address]
        assert hashlib.sha256(hexbytes(runtime_text(codes[address]))).hexdigest() == row["sha256"], address
        assert row["runtime_bytes"] == 925, address
    for address, row in pinned_manifest["contracts"].items():
        assert manifest["contracts"][address]["sha256"] == row["sha256"], address
        assert manifest["contracts"][address]["runtime_file"].startswith(
            f"atlas/block_{BASELINE_PIN}/runtime/"), address

    # 3. proxy slots against the ledger, the pinned manifest and the executed batch
    moved = {}
    for role, address, implementation_role in PROXIES:
        row = manifest["contracts"][address]
        assert row["eip1967_slots"]["implementation"] == values[f"implementation_word:{address}"]
        assert row["eip1967_slots"]["admin"] == values[f"admin_word:{address}"]
        assert row["pinned_implementation"] == pinned_manifest["contracts"][address]["eip1967_slots"]["implementation"]
        assert row["eip1967_slots"]["admin"] == pinned_manifest["contracts"][address]["eip1967_slots"]["admin"], address
        assert word_to_address(values[f"admin_word:{address}"]) == PROXY_ADMIN, address
        if row["current_implementation"] != word_to_address(row["pinned_implementation"]):
            moved[address] = row["current_implementation"]
        assert row["current_implementation"] in manifest["contracts"] or row["current_implementation"] in POST_REFRESH_ADDRESSES
    assert {PROXY_ADDRESSES[address]: implementation
            for address, implementation in moved.items()} == \
        suites["sets"]["postpin_refresh"]["newest_proxies_moved"], moved

    # 4. the batch payload the newest multisig executed names those same three targets
    import gzip
    live = json.load(gzip.open(POSTPIN_SUITE / "live_latest.json.gz"))
    calls = live["multisig_records"]["newest"]["10"]["calls"]["datas"]
    payload = "0x99a88ec4"
    for address, implementation in sorted(moved.items()):
        encoded = payload + address[2:].rjust(64, "0") + implementation[2:].rjust(64, "0")
        assert encoded in calls, (address, implementation)
    # the registry wiring and the keeper call are in the same batch
    assert "0xbd322efa" + "fdc6550436dd75ce8a0b145f935b7d3a64f53248".rjust(64, "0") in calls
    assert "0xefc1bd46" + "0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56".rjust(64, "0") in calls

    # 5. read-only state cross-checks
    assert word_to_address(values["proxy_admin_owner"]) == TIMELOCK
    assert word_to_address(values["timelock_owner"]) == MULTISIG
    assert word_to_int(values["timelock_min_delay"]) == 86_400
    assert 0 < word_to_int(values["multisig_required_confirmations"]) <= 3
    signers = [word_to_address(values[f"multisig_signer_{name}"]) for name in ("one", "two", "three")]
    assert len(set(signers)) == 3 and all(int(signer, 16) for signer in signers)
    pinned_multisig = read_json(PIN_ATLAS / "multisig_behavior.json")
    assert signers == pinned_multisig["signers"], signers
    assert word_to_int(values["multisig_required_confirmations"]) == pinned_multisig["required_confirmations"]
    registry = "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248"
    assert word_to_address(values["builder_registry_owner"]) == TIMELOCK
    assert word_to_address(values["builder_registry_guardian"]) == MULTISIG
    exchange_owner = word_to_address(values["exchange_owner"])
    assert exchange_owner == TIMELOCK
    assert values["exchange_owner_word"].endswith(exchange_owner[2:]) or exchange_owner[2:] in values["exchange_owner_word"]
    # authorizedExecutor: the call and the slot word must agree
    assert word_to_address(values["exchange_authorized_executor"]) == word_to_address(
        values["exchange_authorized_executor_word"])
    slot88_pinned = next(row["old_word"] for row in
                         read_json(PIN_ATLAS / "exchange_admin_setters_behavior.json")["setter_rows"]
                         if row["selector"] == "0xd188c049")
    assert word_to_address(values["exchange_authorized_executor_word"]) == "0x233ff29b239abc1d7748605da9b205c3e008626e"
    assert slot88_pinned == values["exchange_authorized_executor_word"], (
        "authorizedExecutor slot 88 changed since the pin; record the delta instead of asserting")

    # 6. PT-01
    parity = read_json(ROOT / "artifacts" / "pt01_replacement_getter_parity" / "pinned_calls.json")
    pin_time = {word_to_address(row["calldata"]): row["original"]["data"]
                for row in parity["rows"] if row["selector"] == "0x7e4174fc"}
    for user in PT01_USERS:
        word = values[f"pt01_pending_sweep_word:{user}"]
        assert word == pin_time[user], user
        assert word == values[f"exchange_pending_sweep_word:{user}"], user
        getter = values[f"exchange_get_pending_sweep:{user}"]
        words = [int(getter[2:][i:i + 64], 16) for i in range(0, len(getter) - 2, 64)]
        assert len(words) == 4 and words[0] > 0, user
        assert (words[3] << 128) | words[1] == int(word, 16), user
        assert values[f"pt01_balances_word:{user}"] == ZERO_WORD, user
        assert values[f"exchange_balances:{user}"] == ZERO_WORD, user
        assert json.loads(files[f"atlas/block_{block}/state_reads.json"])["pt01"][user][
            "get_pending_sweep_reconstructs_pending_word"] is True, user
    # the sweep-clear route the earlier set had is still not dispatched
    assert state["pt01"][PT01_USERS[0]]["clear_pending_sweep_dispatched"] is False

    # 7. selector catalog: re-decode from the saved bytes and compare
    for address, entry in catalog["catalogs"].items():
        row = manifest["contracts"][address]
        assert entry["sha256"] == row["sha256"], address
        runtime = Runtime(address, entry["role"], codes[address].strip(),
                          row["runtime_file"], entry["pinned_counterpart"])
        baseline_entries = {}
        if entry["pinned_counterpart"]:
            baseline_entries = pinned_dispatcher_entries(pinned_manifest, entry["pinned_counterpart"])
        assert {selector: value for selector, value in runtime.entries.items()} == {
            item["selector"]: item["entry_pc"] for item in entry["functions"]}, address
        expected = suites["postpin_deployment"][address]["selectors"]
        assert sorted(expected) == sorted(runtime.entries), address
        for item in entry["functions"]:
            if item["observed_calldatasize_guard_bytes"] is not None:
                assert item["observed_calldatasize_guard_bytes"] % 32 == 0
                assert item["argument_width_source"] == "observed_calldatasize_guard_on_saved_bytes"
                assert item["argument_word_count"] == item["observed_calldatasize_guard_bytes"] // 32
            if item["candidate_signature"] and item["name_status"] == "public_registry_candidate_hash_matched":
                assert selector_of(item["candidate_signature"]) == item["selector"]
            if item["pinned_entry_pc"] is not None:
                assert item["in_pinned_counterpart"] is True
        delta = catalog["delta"][address]
        current = {item["selector"] for item in entry["functions"]}
        assert delta["counts"]["added"] == len(current - set(baseline_entries)), address
        assert delta["counts"]["removed"] == len(set(baseline_entries) - current), address
        assert delta["counts"]["same_entry_pc"] + delta["counts"]["changed_entry_pc"] == len(
            current & set(baseline_entries)), address
        assert delta["counts"]["added"] == len(delta["added"])
        assert delta["counts"]["removed"] == len(delta["removed"])
    counts = catalog["counts"]
    assert counts["unresolved_added_selectors"] == 10, counts["unresolved_added"]
    assert counts["unresolved_removed_selectors"] == 2, counts["unresolved_removed"]
    assert counts["unresolved_added_selectors"] + counts["unresolved_removed_selectors"] == 12
    assert counts["runtimes"] == len(POST_REFRESH)
    assert counts["selectors"] == sum(entry["counts"]["selectors"]
                                      for entry in catalog["catalogs"].values())
    # the two named Exchange additions and the three named SessionKeyManager/Tokenomics ones
    exchange = catalog["delta"]["0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"]
    assert exchange["counts"]["added"] == 6 and exchange["counts"]["removed"] == 1
    assert {row["selector"] for row in exchange["added"]} == {
        "0x69f9a5f0", "0x9d346583", "0xcbce7532", "0xd970fad5", "0xe6ac4a74", "0xf009ac03"}
    assert [row["selector"] for row in exchange["removed"]] == ["0x415f1240"]
    assert catalog["delta"]["0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946"]["counts"]["added"] == 3
    assert catalog["delta"]["0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03"]["counts"]["added"] == 5
    library = catalog["delta"]["0x583d0bd818c991c5830fea93aef04e474b272459"]
    assert library["counts"]["added"] == 2 and library["counts"]["removed"] == 2
    registry_delta = catalog["delta"][registry]
    assert registry_delta["counts"] == {"added": 10, "removed": 0, "changed_entry_pc": 0, "same_entry_pc": 0}
    assert registry_delta["pinned_counterpart"] is None
    return True


def write(files):
    for relative, text in files.items():
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        print(f"wrote {relative}", file=sys.stderr, flush=True)


def rebuild():
    """Regenerate the pin's files from the saved ledger, offline, and verify them."""
    ledger = load_ledger()
    codes = {address: (CODE_DIR / f"{address}.hex").read_text().strip()
             for address in sorted(POST_REFRESH_ADDRESSES + list(PROXY_ADDRESSES))}
    files, summary = build(ledger, codes)
    check(files, ledger, codes)
    write(files)
    summary["generated_files"] = sorted(files)
    summary["verified_offline"] = True
    return summary


def verify():
    ledger = load_ledger()
    codes = {address: (CODE_DIR / f"{address}.hex").read_text().strip()
             for address in sorted(POST_REFRESH_ADDRESSES + list(PROXY_ADDRESSES))}
    files, summary = build(ledger, codes)
    for relative, text in files.items():
        on_disk = ROOT / relative
        assert on_disk.exists(), f"missing {relative}"
        assert on_disk.read_text() == text, f"{relative} does not match the rebuild"
    check(files, ledger, codes)
    summary["generated_files"] = sorted(files)
    summary["verified_offline"] = True
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="read the read-only public RPC and rewrite the pin evidence")
    parser.add_argument("--resume", action="store_true",
                        help="with --capture, reuse reads already saved in "
                             "artifacts/postpin_pin/partial_reads.json")
    parser.add_argument("--rebuild", action="store_true",
                        help="regenerate the pin's files from the saved ledger, offline, and "
                             "verify them (no RPC)")
    args = parser.parse_args()
    if args.capture:
        result = capture(resume=args.resume)
        CHECKPOINT.unlink(missing_ok=True)
    elif args.rebuild:
        result = rebuild()
    else:
        result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()