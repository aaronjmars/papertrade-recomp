"""Capture and verify the live PT-01 facts against the current Exchange set.

Everything here is a read-only observation of current HyperEVM state through the
public JSON-RPC plus the public HyperCore `info` API. `--capture` refreshes
`../artifacts/recovery_redrive/live_facts.json`; the no-argument run re-checks the
saved capture offline against the pinned audit artifacts.
"""

import argparse
import datetime
import decimal
import gzip
import hashlib
import json
import pathlib
import re
import time

from atlas_factory_events import Keccak
from recovery.current_rpc import CORE_INFO, RPC_URL, core, rpc, rpc_call, slot_of, word

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
CENSUS = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
LIVE_FACTS = ROOT / "artifacts" / "recovery_redrive" / "live_facts.json"
RUNTIME = ROOT / "artifacts" / "recovery_redrive" / "runtime"

EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
OLD_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
NEW_IMPLEMENTATION = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
PROXY_ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
MULTISIG = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"

IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
ACTIVE_SLOT = "0x" + (int.from_bytes(Keccak()(b"papertrade.pt01.rescue.active.v1"), "big") - 1).to_bytes(32, "big").hex()

SELECTORS = {
    "pendingSweepWord(address)": "0x7e4174fc",
    "getPendingSweep(address)": "0x31a4956c",
    "lastSweepBlock(address)": "0xf84a74d3",
    "balances(address)": "0x27e235e3",
    "reconcileSweepCredit(address,uint256)": "0x6a3214c9",
    "sweep(address)": "0x01681a62",
    "requestSweep(address)": "0xe0189108",
    "finalizeSweep(address)": "0x6d142da1",
    "owner()": "0x8da5cb5b",
    "treasury()": "0x61d027b3",
    "totalBalances()": "0xa69a2ad1",
    "collateralScale()": "0xec0bdcfc",
}
CHAIN_TOPICS = [
    "0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025",
    "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696",
    "0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e",
]
SWEEP_TOPICS = [
    "0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025",
    "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696",
    "0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e",
    "0x8da9931e615ce9dfd2d7914e0cee3246839757203d34810cde64e0d0026f75c3",
]
NAMED_ABSENCES = [
    "clearPendingSweep(address)",
    "clearPendingSweeps(address)",
    "cancelPendingSweep(address)",
    "setPendingSweep(address,uint256)",
    "adminSweep(address)",
    "forceSweep(address)",
    "rescueSweep(address)",
    "retrySweep(address)",
    "sweepAll(address)",
    "sweepBatch(address[])",
    "approveSweep(address)",
    "clearSweep(address)",
    "reconcileSweep(address)",
]
BLOCK_RANGE = 1000  # the public RPC refuses a wider eth_getLogs range


def keccak():
    return Keccak()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def dispatcher_selectors(code):
    """4-byte constants compared with EQ: the solc dispatcher table, extracted from bytecode."""
    return sorted({code[m.start() + 1:m.start() + 5].hex()
                   for m in re.finditer(b"\x63(....)\x14", code, re.S)})


def census():
    saved = json.loads(gzip.decompress(CENSUS.read_bytes()))
    assert saved["pin"] == 48_902_346
    return saved


def public_signature_match(selector, attempts=2):
    """A public signature-database lookup for a raw selector. Never proof of a name."""
    import shutil
    import subprocess

    if not shutil.which("cast"):
        return {"lookup": "cast unavailable", "matches": []}
    for _ in range(attempts):
        result = subprocess.run(["cast", "4byte", "0x" + selector.lstrip("0x")],
                                capture_output=True, text=True, timeout=30, check=False)
        text = (result.stdout + result.stderr).strip()
        if "rate limit" in text.lower() or "too many" in text.lower():
            time.sleep(2)
            continue
        if result.returncode:
            return {"lookup": "no public match", "matches": []}
        return {"lookup": "public signature database (4byte); unverified name match",
                "matches": [line.strip() for line in text.splitlines() if line.strip()][:3]}
    return {"lookup": "rate limited", "matches": []}


def log_scan(address, topics, users, start, end, pace=2.5):
    """`eth_getLogs` in 1000-block chunks; the public endpoint rate limits tight loops."""
    chunks, logs = [], []
    block = start
    while block <= end:
        last = min(block + BLOCK_RANGE - 1, end)
        query = {"fromBlock": hex(block), "toBlock": hex(last), "address": address,
                 "topics": [topics, users]}
        for attempt in range(6):
            try:
                result = rpc("eth_getLogs", [query])
                break
            except RuntimeError as error:
                if "rate limited" not in str(error) or attempt == 5:
                    raise
                time.sleep(3 * (attempt + 1))
        chunks.append({"fromBlock": query["fromBlock"], "toBlock": query["toBlock"],
                       "logs": result})
        logs.extend(result)
        block = last + 1
        time.sleep(pace)
    return chunks, logs


def as_block(value):
    """A block number from either a hex string or an integer field."""
    return int(value, 16) if isinstance(value, str) else int(value)


def middle_evidence():
    """The two saved captures that already cover the middle of the range, re-read from disk."""
    status = json.loads((ROOT / "artifacts" / "pt01_postpin" / "status_20261020_1703.json").read_text())
    query = status["event_query"]
    assert query["address"] == EXCHANGE
    assert set(CHAIN_TOPICS) <= set(query["topics"][0])
    assert status["sweep_logs"] == []
    governance = json.loads(gzip.decompress(
        (ROOT / "artifacts" / "postpin_suite" / "governance_logs.json.gz").read_bytes()))
    key = "proxy_" + EXCHANGE.lower()
    proxy_set = governance["log_sets"][key]
    assert proxy_set["address"].lower() == EXCHANGE
    assert proxy_set["logs"] == []
    return [
        {"path": "artifacts/pt01_postpin/status_20261020_1703.json",
         "filter": "the three recorded sweep-family topics and both affected users",
         "first_block": as_block(query["fromBlock"]), "last_block": as_block(query["toBlock"]),
         "log_count": 0},
        {"path": "artifacts/postpin_suite/governance_logs.json.gz",
         "filter": f"every log from the Exchange proxy ({key})",
         "first_block": as_block(proxy_set["from_block"]),
         "last_block": as_block(governance["head"]), "log_count": 0},
    ]


def case_reads(user, proxy):
    """Every getter-vs-storage pair the candidate depends on, for one affected user."""
    pending_storage = slot_of(int(user, 16), 33)
    last_storage = slot_of(int(proxy, 16), 32)
    balance_storage = slot_of(int(user, 16), 9)
    arg = "0x" + user[2:].rjust(64, "0")
    parg = "0x" + proxy[2:].rjust(64, "0")
    return {
        "user": user,
        "proxy": proxy,
        "pending_storage_slot": pending_storage,
        "pending_storage_word": rpc("eth_getStorageAt", [EXCHANGE, pending_storage, "latest"]),
        "pending_sweep_word_call": rpc_call(EXCHANGE, SELECTORS["pendingSweepWord(address)"] + arg[2:])["data"],
        "get_pending_sweep_call": rpc_call(EXCHANGE, SELECTORS["getPendingSweep(address)"] + arg[2:])["data"],
        "last_sweep_block_storage_slot": last_storage,
        "last_sweep_block_storage_word": rpc("eth_getStorageAt", [EXCHANGE, last_storage, "latest"]),
        "last_sweep_block_call": rpc_call(EXCHANGE, SELECTORS["lastSweepBlock(address)"] + parg[2:])["data"],
        "balance_storage_slot": balance_storage,
        "balance_storage_word": rpc("eth_getStorageAt", [EXCHANGE, balance_storage, "latest"]),
        "balances_call": rpc_call(EXCHANGE, SELECTORS["balances(address)"] + arg[2:])["data"],
        "proxy_code_sha256": sha256(bytes.fromhex(rpc("eth_getCode", [proxy, "latest"])[2:])),
        "spot_precompile": rpc_call("0x0000000000000000000000000000000000000801",
                                    "0x" + proxy[2:].rjust(64, "0") + "00" * 32)["data"],
        "public_core_spot_state": core({"type": "spotClearinghouseState", "user": proxy}),
    }


def capture():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    stalled = census()
    RUNTIME.mkdir(parents=True, exist_ok=True)
    k = keccak()

    head = rpc("eth_getBlockByNumber", ["latest", False])
    chain_id = rpc("eth_chainId", [])
    implementation_word = rpc("eth_getStorageAt", [EXCHANGE, IMPLEMENTATION_SLOT, "latest"])
    admin_word = rpc("eth_getStorageAt", [EXCHANGE, ADMIN_SLOT, "latest"])
    new_code = rpc("eth_getCode", [NEW_IMPLEMENTATION, "latest"])
    assert implementation_word.lower() == word(NEW_IMPLEMENTATION).lower(), implementation_word
    assert admin_word.lower() == word(PROXY_ADMIN).lower(), admin_word
    new_bytes = bytes.fromhex(new_code[2:])
    (RUNTIME / f"{NEW_IMPLEMENTATION}.hex").write_text(new_code + "\n")

    old_code = (ATLAS / manifest["contracts"][OLD_IMPLEMENTATION]["runtime_file"]).read_text().strip()
    old_selectors = dispatcher_selectors(bytes.fromhex(old_code[2:]))
    new_selectors = dispatcher_selectors(new_bytes)
    absent = {name: "0x" + k(name.encode())[:4].hex() for name in NAMED_ABSENCES}
    dispatcher = {
        "method": "scan runtime for PUSH4 followed by EQ; reproduces all 98 pinned catalog "
                  "selectors of the old implementation with no false positives",
        "old_implementation": OLD_IMPLEMENTATION,
        "old_runtime_sha256": sha256(bytes.fromhex(old_code[2:])),
        "old_selector_count": len(old_selectors),
        "new_implementation": NEW_IMPLEMENTATION,
        "new_runtime_sha256": sha256(new_bytes),
        "new_selector_count": len(new_selectors),
        "added_selectors": sorted(set(new_selectors) - set(old_selectors)),
        "removed_selectors": sorted(set(old_selectors) - set(new_selectors)),
        "sweep_family_present_in_new": sorted(
            selector for selector in new_selectors
            if selector in {value[2:] for value in SELECTORS.values()}),
        "public_signature_matches": {},
        "named_absence_preimages": absent,
        "named_absences_confirmed": sorted(
            name for name, selector in absent.items()
            if selector[2:] not in new_selectors and selector[2:] not in old_selectors),
    }

    users = [row["user"] for row in stalled["cases"]]
    proxies = [row["proxy"] for row in stalled["cases"]]
    for selector in dispatcher["added_selectors"]:
        dispatcher["public_signature_matches"][selector] = public_signature_match(selector)
    delay_change_id = "0xc616b8d5f1fccaae8952fd5832306ef7d181cdbf7b3e81fa331593abc6d6a6cb"
    governance = {
        "timelock": TIMELOCK,
        "timelock_owner_slot": rpc("eth_getStorageAt", [TIMELOCK, hex(0), "latest"]),
        "timelock_min_delay_word": rpc("eth_getStorageAt", [TIMELOCK, hex(1), "latest"]),
        "delay_change_operation_slot": "0x" + k(bytes.fromhex(delay_change_id[2:]) + (2).to_bytes(32, "big")).hex(),
        "multisig": MULTISIG,
        "multisig_signer_slots": [rpc("eth_getStorageAt", [MULTISIG, hex(index), "latest"])
                                  for index in range(3)],
        "multisig_epoch_word": rpc("eth_getStorageAt", [MULTISIG, hex(3), "latest"]),
        "multisig_transaction_count_word": rpc("eth_getStorageAt", [MULTISIG, hex(4), "latest"]),
        "proxy_admin": PROXY_ADMIN,
        "proxy_admin_owner_call": rpc_call(PROXY_ADMIN, SELECTORS["owner()"])["data"],
        "proxy_admin_owner_slot": rpc("eth_getStorageAt", [PROXY_ADMIN, hex(0), "latest"]),
    }
    governance["delay_change_operation_word"] = rpc(
        "eth_getStorageAt", [TIMELOCK, governance["delay_change_operation_slot"], "latest"])
    cases = [case_reads(user, proxy) for user, proxy in zip(users, proxies)]
    pin_start = int(stalled["pin"]) + 1
    pin_time = int(stalled["pin_header"]["timestamp"], 16)
    topic_words = ["0x" + user[2:].rjust(64, "0") for user in users]
    middle = middle_evidence()
    chained_first = min(record["first_block"] for record in middle)
    chained_last = max(record["last_block"] for record in middle)
    gaps = [(pin_start, chained_first - 1), (chained_last + 1, int(head["number"], 16))]
    chunks, logs = [], []
    for first, last in gaps:
        if first > last:
            continue
        part, part_logs = log_scan(EXCHANGE, SWEEP_TOPICS, topic_words, first, last)
        chunks.extend(part)
        logs.extend(part_logs)
    ledgers = [core({"type": "userNonFundingLedgerUpdates", "user": proxy,
                     "startTime": pin_time * 1000,
                     "endTime": (int(head["timestamp"], 16) + 1) * 1000 - 1})
               for proxy in proxies]

    output = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "rpc_url": RPC_URL,
        "core_info": CORE_INFO,
        "methods": ["eth_blockNumber/latest", "eth_getCode", "eth_getStorageAt", "eth_call",
                    "eth_getLogs (1000-block chunks)", "POST /info"],
        "head": {key: head[key] for key in ("number", "hash", "timestamp")},
        "chain_id": chain_id,
        "exchange": {
            "proxy": EXCHANGE,
            "implementation_slot": IMPLEMENTATION_SLOT,
            "implementation_word": implementation_word,
            "implementation": NEW_IMPLEMENTATION,
            "implementation_runtime_file": f"runtime/{NEW_IMPLEMENTATION}.hex",
            "implementation_code_bytes": len(new_bytes),
            "implementation_code_sha256": sha256(new_bytes),
            "admin_slot": ADMIN_SLOT,
            "admin_word": admin_word,
            "proxy_admin": PROXY_ADMIN,
            "owner_call": rpc_call(EXCHANGE, SELECTORS["owner()"])["data"],
            "owner_slot_word": rpc("eth_getStorageAt", [EXCHANGE, word(0), "latest"]),
            "treasury_call": rpc_call(EXCHANGE, SELECTORS["treasury()"])["data"],
            "treasury_storage_word": rpc("eth_getStorageAt", [EXCHANGE, word(14), "latest"]),
            "total_balances_call": rpc_call(EXCHANGE, SELECTORS["totalBalances()"])["data"],
            "total_balances_storage_word": rpc("eth_getStorageAt", [EXCHANGE, word(22), "latest"]),
            "collateral_scale_call": rpc_call(EXCHANGE, SELECTORS["collateralScale()"])["data"],
            "collateral_scale_storage_word": rpc("eth_getStorageAt", [EXCHANGE, word(3), "latest"]),
            "collateral_decimals_storage_word": rpc("eth_getStorageAt", [EXCHANGE, word(5), "latest"]),
            "recovery_active_slot": ACTIVE_SLOT,
            "recovery_active_value": rpc("eth_getStorageAt", [EXCHANGE, ACTIVE_SLOT, "latest"]),
            "singleton_slots": {str(index): rpc("eth_getStorageAt", [EXCHANGE, hex(index), "latest"])
                                for index in range(32)},
            "linked_getters": {
                "oracle()": rpc_call(EXCHANGE, "0x7dc0d1d0")["data"],
                "proxyFactory()": rpc_call(EXCHANGE, "0xc10f1a75")["data"],
                "sessionKeyManager()": rpc_call(EXCHANGE, "0x0b826190")["data"],
                "paperTokenomics()": rpc_call(EXCHANGE, "0xed410ee1")["data"],
            },
            "reconcile_sweep_credit_selector_call": rpc_call(
                EXCHANGE, SELECTORS["reconcileSweepCredit(address,uint256)"]
                + users[0][2:].rjust(64, "0") + "00" * 32),
        },
        "selectors": SELECTORS,
        "dispatcher": dispatcher,
        "governance": governance,
        "cases": cases,
        "core_ledger_since_pin": ledgers,
        "sweep_log_scan": {
            "address": EXCHANGE,
            "topics": SWEEP_TOPICS,
            "chain_topics": CHAIN_TOPICS,
            "users": topic_words,
            "first_block": hex(pin_start),
            "last_block": head["number"],
            "gaps": [{"first_block": hex(first), "last_block": hex(last)} for first, last in gaps],
            "middle_evidence": middle,
            "chunks": chunks,
            "log_count": len(logs),
            "logs": logs,
        },
        "pinned": {
            "pin": stalled["pin"],
            "pin_hash": stalled["block_hash"],
            "old_implementation_runtime_file": manifest["contracts"][OLD_IMPLEMENTATION]["runtime_file"],
            "old_implementation_runtime_sha256": manifest["contracts"][OLD_IMPLEMENTATION]["sha256"],
            "pending_words": [row["pending_word"] for row in stalled["cases"]],
            "last_sweep_words": [row["last_sweep_word"] for row in stalled["cases"]],
            "proxy_runtime_sha256": [row["derived_runtime_sha256"] for row in stalled["cases"]],
        },
    }
    output["exchange"]["total_balances_slot_candidates"] = [
        index for index, value in output["exchange"]["singleton_slots"].items()
        if int(value, 16) & ((1 << 160) - 1) == int(output["exchange"]["total_balances_call"], 16) & ((1 << 160) - 1)]
    linked = dict(output["exchange"]["linked_getters"])
    output["exchange"]["linked_getter_slots"] = {
        name: [index for index, value in output["exchange"]["singleton_slots"].items()
               if int(value, 16) & ((1 << 160) - 1) == int(address, 16)]
        for name, address in linked.items()
    }
    return verify(save=output)


def verify(save=None):
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    stalled = census()
    saved = save if save is not None else json.loads(LIVE_FACTS.read_text())
    if save is not None:
        LIVE_FACTS.parent.mkdir(parents=True, exist_ok=True)
        LIVE_FACTS.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n")
    k = keccak()

    assert saved["rpc_url"] == RPC_URL and saved["core_info"] == CORE_INFO
    assert saved["chain_id"] == "0x3e7"
    assert int(saved["head"]["number"], 16) > saved["pinned"]["pin"]
    assert len(saved["head"]["hash"]) == 66

    exchange = saved["exchange"]
    assert exchange["proxy"] == EXCHANGE
    assert exchange["implementation_word"].lower() == word(NEW_IMPLEMENTATION).lower()
    assert exchange["implementation"] == NEW_IMPLEMENTATION
    assert int(exchange["implementation_word"], 16) != int(OLD_IMPLEMENTATION, 16)
    assert exchange["admin_word"].lower() == word(PROXY_ADMIN).lower()
    assert int(exchange["owner_call"], 16) == int(TIMELOCK, 16)
    assert exchange["owner_slot_word"].lower() == "0x" + f"{int(TIMELOCK, 16) << 16 | 1:064x}"
    pinned_slots = manifest["contracts"][EXCHANGE]["eip1967_slots"]
    assert pinned_slots["implementation"].lower() == word(OLD_IMPLEMENTATION).lower()
    assert pinned_slots["admin"].lower() == word(PROXY_ADMIN).lower()
    assert int(exchange["treasury_call"], 16) == int(exchange["treasury_storage_word"], 16)
    assert int(exchange["collateral_scale_call"], 16) == int(exchange["collateral_scale_storage_word"], 16)
    assert int(exchange["collateral_decimals_storage_word"], 16) == 10**10, \
        "slot 5 is the 1e10 credit scale the candidate multiplies by"
    assert int(exchange["total_balances_call"], 16) > 0
    assert int(exchange["recovery_active_value"], 16) == 0
    assert exchange["reconcile_sweep_credit_selector_call"]["status"] == "error", \
        "owner reconciliation must still revert for an empty pending word"

    # totalBalances() is not a plain singleton read: record which slots could hold it.
    assert exchange["total_balances_slot_candidates"] == [
        index for index, value in exchange["singleton_slots"].items()
        if int(value, 16) & ((1 << 160) - 1) == int(exchange["total_balances_call"], 16) & ((1 << 160) - 1)]
    slots = exchange["singleton_slots"]
    assert sorted(slots, key=int) == [str(index) for index in range(32)]
    assert slots["0"] == exchange["owner_slot_word"]
    assert slots["3"] == exchange["collateral_scale_storage_word"]
    assert slots["5"] == exchange["collateral_decimals_storage_word"]
    assert slots["14"] == exchange["treasury_storage_word"]
    for name, indexes in exchange["linked_getter_slots"].items():
        value = int(exchange["linked_getters"][name], 16)
        assert all(int(slots[index], 16) & ((1 << 160) - 1) == value for index in indexes)
        if value and not indexes:
            # a packed word still has to contain the address it reports
            assert any(value.to_bytes(20, "big") in bytes.fromhex(word_value[2:])
                       for word_value in slots.values()), f"{name} appears in no live singleton slot"

    governance = saved["governance"]
    assert int(governance["timelock_owner_slot"], 16) == int(MULTISIG, 16)
    assert int(governance["timelock_min_delay_word"], 16) == 86_400
    assert int(governance["delay_change_operation_word"], 16) != 0, \
        "the pinned delay-change operation still occupies its timelock slot"
    signers = [int(word_value, 16) for word_value in governance["multisig_signer_slots"]]
    assert len(signers) == len(set(signers)) == 3
    assert all(signer != 0 for signer in signers)
    assert int(governance["multisig_epoch_word"], 16) > 0
    assert int(governance["multisig_transaction_count_word"], 16) >= 10
    assert int(governance["proxy_admin_owner_call"], 16) == int(TIMELOCK, 16)
    assert int(governance["proxy_admin_owner_slot"], 16) == int(TIMELOCK, 16)

    # the new runtime must be the one this capture measured, byte for byte
    runtime_file = RUNTIME / f"{NEW_IMPLEMENTATION}.hex"
    runtime = bytes.fromhex(runtime_file.read_text().strip()[2:])
    assert sha256(runtime) == exchange["implementation_code_sha256"]
    assert len(runtime) == exchange["implementation_code_bytes"] == 23_959

    # dispatcher: the scan must reproduce every pinned selectors of the old implementation
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    pinned_selectors = sorted(row["selector"][2:] for row in catalog[OLD_IMPLEMENTATION]["functions"])
    dispatcher = saved["dispatcher"]
    old_code = bytes.fromhex((ATLAS / manifest["contracts"][OLD_IMPLEMENTATION]["runtime_file"]).read_text().strip()[2:])
    assert sha256(old_code) == dispatcher["old_runtime_sha256"]
    scanned_old = dispatcher_selectors(old_code)
    scanned_new = dispatcher_selectors(runtime)
    assert scanned_old == pinned_selectors
    assert len(scanned_old) == dispatcher["old_selector_count"]
    assert len(scanned_new) == dispatcher["new_selector_count"]
    assert dispatcher["added_selectors"] == sorted(set(scanned_new) - set(scanned_old))
    assert dispatcher["removed_selectors"] == sorted(set(scanned_old) - set(scanned_new))
    assert len(dispatcher["added_selectors"]) == 6
    assert dispatcher["removed_selectors"] == ["415f1240"]  # liquidate(uint256) in the pinned catalog
    for name in ("sweep(address)", "requestSweep(address)", "finalizeSweep(address)",
                 "reconcileSweepCredit(address,uint256)"):
        assert SELECTORS[name][2:] in dispatcher["sweep_family_present_in_new"]
    assert dispatcher["named_absences_confirmed"] == sorted(NAMED_ABSENCES)

    # the candidate's block list must be exactly the live sweep-family dispatcher entries
    guarded = {SELECTORS[name][2:] for name in
               ("sweep(address)", "requestSweep(address)", "finalizeSweep(address)",
                "reconcileSweepCredit(address,uint256)")}
    assert guarded <= set(dispatcher_selectors(runtime))

    # getter-versus-storage layout proofs, per affected user
    assert len(saved["cases"]) == len(stalled["cases"]) == 2
    spot_total = decimal.Decimal(0)
    for prior, row in zip(stalled["cases"], saved["cases"]):
        user, proxy = prior["user"].lower(), prior["proxy"].lower()
        assert row["user"] == user and row["proxy"] == proxy
        assert row["pending_storage_slot"].lower() == prior["pending_slot"].lower()
        assert row["pending_storage_word"].lower() == row["pending_sweep_word_call"].lower()
        word_value = int(row["pending_storage_word"], 16)
        pending_struct = row["get_pending_sweep_call"]
        assert len(pending_struct) == 2 + 4 * 64, "getPendingSweep returns four words"
        fields = [int(pending_struct[2 + 64 * i:2 + 64 * (i + 1)], 16) for i in range(4)]
        assert fields[0] == 1, "getPendingSweep flags an existing request"
        assert fields[1] == word_value & ((1 << 64) - 1)
        assert fields[2] == 0, "getPendingSweep reserved word is zero"
        assert fields[3] == word_value >> 128 & ((1 << 32) - 1)
        assert word_value >> 64 & ((1 << 64) - 1) == 0
        assert row["pending_storage_word"].lower() == prior["pending_word"].lower()
        assert int(row["pending_storage_word"], 16) & ((1 << 64) - 1) != 0
        assert int(row["pending_storage_word"], 16) >> 160 == 0
        assert row["last_sweep_block_storage_word"].lower() == row["last_sweep_block_call"].lower()
        assert row["last_sweep_block_storage_word"].lower() == prior["last_sweep_word"].lower()
        assert row["balance_storage_word"].lower() == row["balances_call"].lower() == "0x" + "00" * 32
        assert row["proxy_code_sha256"] == prior["derived_runtime_sha256"]
        output = row["spot_precompile"]
        assert len(output) == 194
        raw = int(output[2:66], 16)
        assert output[66:194] == "00" * 64
        assert int(row["pending_storage_word"], 16) & ((1 << 64) - 1) == raw
        usdc = [entry for entry in row["public_core_spot_state"]["balances"]
                if entry["coin"] == "USDC" and entry["token"] == 0]
        assert len(usdc) == 1
        assert raw == int(decimal.Decimal(usdc[0]["total"]) * 10**8)
        spot_total += decimal.Decimal(usdc[0]["total"])
    assert spot_total == decimal.Decimal("62.150916")

    for ledger in saved["core_ledger_since_pin"]:
        assert ledger == []

    scan = saved["sweep_log_scan"]
    assert scan["log_count"] == 0 and scan["logs"] == []
    assert scan["first_block"] == hex(saved["pinned"]["pin"] + 1)
    assert scan["last_block"] == saved["head"]["number"]
    assert set(scan["chain_topics"]) <= set(scan["topics"]), "chained topics are a subset"
    assert scan["chain_topics"] == CHAIN_TOPICS
    recorded = middle_evidence()
    assert scan["middle_evidence"] == recorded, "the chained captures must still say what they said"
    chained_first = min(record["first_block"] for record in recorded)
    chained_last = max(record["last_block"] for record in recorded)
    for record in recorded:
        assert chained_first <= record["first_block"] <= record["last_block"] <= chained_last
        assert record["log_count"] == 0
    head_block = int(saved["head"]["number"], 16)
    pin_start = saved["pinned"]["pin"] + 1
    assert chained_first >= pin_start and chained_last < head_block, \
        "the chained captures must sit inside the pin-to-head range"
    # our own scans must fill exactly the two gaps the chained captures leave
    runs = [gap for gap in ((pin_start, chained_first - 1), (chained_last + 1, head_block))
            if gap[0] <= gap[1]]
    assert runs, "the chained captures already cover the whole range"
    segments = []
    for index, chunk in enumerate(scan["chunks"]):
        assert chunk["logs"] == []
        start, last = int(chunk["fromBlock"], 16), int(chunk["toBlock"], 16)
        assert last - start + 1 <= BLOCK_RANGE
        if index:
            assert start == segments[index - 1][1] + 1, "our chunks are contiguous"
        assert any(first <= start and last <= boundary for first, boundary in runs), \
            "our chunks must stay inside the gaps"
        segments.append((start, last))
    covered = sum(last - first + 1 for first, last in segments)
    assert segments[0][0] == runs[0][0] and segments[-1][1] == runs[-1][1]
    assert covered == sum(last - first + 1 for first, last in runs)
    assert scan["gaps"] == [{"first_block": hex(first), "last_block": hex(last)}
                            for first, last in ((pin_start, chained_first - 1),
                                                (chained_last + 1, head_block))]

    assert saved["pinned"]["pin"] == stalled["pin"]
    assert saved["pinned"]["pin_hash"] == stalled["block_hash"]
    assert saved["pinned"]["pending_words"] == [row["pending_word"] for row in stalled["cases"]]
    assert saved["pinned"]["proxy_runtime_sha256"] == [row["derived_runtime_sha256"] for row in stalled["cases"]]

    return {
        "head_block": int(saved["head"]["number"], 16),
        "head_hash": saved["head"]["hash"],
        "captured_at_utc": saved["captured_at_utc"],
        "implementation": exchange["implementation"],
        "implementation_code_sha256": exchange["implementation_code_sha256"],
        "implementation_code_bytes": exchange["implementation_code_bytes"],
        "old_implementation_code_sha256": dispatcher["old_runtime_sha256"],
        "dispatcher_selectors_old": dispatcher["old_selector_count"],
        "dispatcher_selectors_new": dispatcher["new_selector_count"],
        "added_selectors": dispatcher["added_selectors"],
        "removed_selectors": dispatcher["removed_selectors"],
        "named_absences_confirmed": dispatcher["named_absences_confirmed"],
        "pending_words_unchanged": 2,
        "balances_zero": 2,
        "active_slot_value": exchange["recovery_active_value"],
        "sweep_logs_since_pin": scan["log_count"],
        "core_ledger_entries_since_pin": 0,
        "spot_usdc": str(spot_total),
        "log_scan_chunks": len(scan["chunks"]),
        "log_scan_gaps": [f'{hex(pin_start)}..{hex(chained_first - 1)}',
                          f'{hex(chained_last + 1)}..{hex(head_block)}'],
        "log_scan_chained": f'{hex(chained_first)}..{hex(chained_last)}', 
        "timelock_min_delay_seconds": int(governance["timelock_min_delay_word"], 16),
        "multisig_signers": [word(value) for value in signers],
        "multisig_transaction_count": int(governance["multisig_transaction_count_word"], 16),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="read live HyperEVM and HyperCore state (slow: sweeps the log range)")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))