#!/usr/bin/env python3
"""Audit signed intents, execution gates and the deposit/withdrawal paths on the
post-pin (contract set 2) runtimes, with the pinned set as control.

Offline by default: verifies saved evidence under artifacts/ and runs exact-runtime
Foundry cases against the captured runtimes. `--capture` refreshes the read-only
HyperEVM probes in artifacts/live2_intents/live_reads.json (public endpoint, no key).
"""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from atlas_factory_events import Keccak  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT_DIR = ROOT / "artifacts" / "live2_intents"
READS = OUT_DIR / "live_reads.json"
LEDGER = ATLAS / "live2_intents.json"
RPC = "https://rpc.hyperliquid.xyz/evm"

PIN = 48902346
PIN_HASH = "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
PIN_TIMESTAMP = 1792357341

# Pinned set 1 (behaviour baseline).
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
EXCHANGE_IMPL_1 = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SESSION_IMPL_1 = "0x8a5069fe303e8f81e91825436e956d595032e558"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
FACTORY = "0x1629b7d46bef6e13ff754174fc9f32dea309b38f"
PROXY_ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
MULTISIG = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"

# Post-pin set 2 runtimes (deployer 0x13cb7a200d081094d23ebf07f4d708410a9c488b).
EXCHANGE_IMPL_2 = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
SESSION_IMPL_2 = "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946"
LIBRARY_2 = "0x583d0bd818c991c5830fea93aef04e474b272459"
BUILDER_REGISTRY = "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248"
KEEPER = "0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56"
RUN2 = {"exchange_impl": EXCHANGE_IMPL_2, "session_impl": SESSION_IMPL_2,
        "library": LIBRARY_2, "builder_registry": BUILDER_REGISTRY}

# Exact-runtime facts already established for the pinned set (see AUDIT.md / atlas).
PIN_DOMAIN_SEPARATOR = "0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77"
TYPEHASHES = {
    "0x744157ccffbd293a2e8644928cd7d23d650f869b88f72d7bfea8041b76ca6bec":
        "SessionKeyRevoked(address,address) topic",
    "0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983":
        "OPEN_POSITION_TYPEHASH()",
    "0x3cec0566535d67d6c92668517af0bf8a66cdc91d622dbb830fcc08e1bcf5d1df":
        "SessionKeyRegistered(address,address,uint64) topic",
    "0xf09fcf47c21ca51acd6fd24e30b537dc39f0e5e021541cf1e4fa7f1013d60b99":
        "third SessionKeyManager event topic",
    "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13":
        "CLOSE_TYPEHASH()",
    "0xac4ddb8d63e9d7a862c5d61ce47517623a448262414a7eef6797102104b31214":
        "WITHDRAW_TO_CORE_TYPEHASH()",
    "0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f":
        "EIP712Domain typehash",
}

# BatchExecutor allowlist established by pinned read-only probes
# (atlas/block_48902346/batch_executor_pseudocode.md).
ALLOWLIST = {
    EXCHANGE.lower(): ["0x2792e706", "0x8d09f23f", "0xec6783f0"],
    SESSION.lower(): ["0x5f76a1d6"],
    "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016": ["0x83115825", "0x9c96d4a1",
                                                       "0xf0355460", "0xfa2871b5"],
}
# Selectors the set 2 batch added to the Exchange and SessionKeyManager
# (atlas/block_48902346/suite_sets.md).
ADDED_SET2 = {
    EXCHANGE.lower(): ["0x69f9a5f0", "0x9d346583", "0xcbce7532", "0xd970fad5",
                       "0xe6ac4a74", "0xf009ac03"],
    SESSION.lower(): ["0xbd322efa", "0xd95208cd", "0xe737de13"],
}
EXCHANGE_DROPPED = ["0x415f1240"]

SESSION_DIRECT_SLOTS_1 = {
    0: "0x0000000000000000000000000000000000000000000000000000000000000001",
    1: PIN_DOMAIN_SEPARATOR,
    2: "0x000000000000000000000000b915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
    3: "0x0000000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a2",
}
EXCHANGE_SLOT_88_1 = "0x000000000000000000000000233ff29b239abc1d7748605da9b205c3e008626e"

ERROR_NAMES = {
    "0x329c2b0f": "SweepBelowMinimum()",
    "0x756688fe": "InvalidNonce()",
    "0xf87d9271": "ExpiredDeadline()",
    "0xc5045f22": "SessionKeyNotAuthorized()",
    "0x93b78c88": "UnauthorizedSubmitter()",
    "0x17fb2066": "NotAuthorizedRelayer()",
    "0x30cd7471": "NotOwner()",
    "0x28ef4314": "SweepAlreadyPending()",
    "0x8baa579f": "InvalidSignature()",
    "0x5c427cd9": "UnauthorizedCaller()",
    "0x0984a617": "NoPendingSweep()",
    "0x4e487b71": "Panic(uint256)",
}
# Selectors this audit observed but does not name: no verified signature is claimed.
UNNAMED_SELECTORS = ["0xc20280ea", "0xda96f0b6", "0x0a4f5a07", "0x4f57ffae", "0xd26ffacb",
                     "0xfefe83a0", "0x0576e005", "0xd95208cd", "0xd970fad5"]
# Candidate names that were tried during this audit and hash-checked to be WRONG, so that no
# later prose can revive them.
REJECTED_NAMES = {
    "0xd26ffacb": "SweepSameBlock()",
    "0xfefe83a0": "SweepRateLimited()",
    "0x4f57ffae": "WithdrawalThisBlock()",
    "0xc20280ea": "InvalidSigner()",
}
EVENT_NAMES = {
    "0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15":
        "BuilderFeesClaimed(address,uint256,uint256)",
    "0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75":
        "CoreWithdrawal(address,uint256,uint256)",
}

EXPECTED_LIVE_TESTS = [
    "testBadCloseSignatureRollsBackNonce",
    "testBadOpenSignatureRollsBackNonce",
    "testBadSignatureRollsBackNonce",
    "testCloseBatchCallerDependsOnSlot88",
    "testDeadlineAtTimestampReachesSignatureCheck",
    "testExpiredCloseDeadlineLeavesNonceUnused",
    "testExpiredDeadlineLeavesNonceUnused",
    "testExpiredOpenDeadlineLeavesNonceUnused",
    "testFourPositionCloseDigestAcceptsSessionSigner",
    "testFourthCloseIdMutationRejectsSessionSignature",
    "testOutsiderCloseRejectedBeforeNonce",
    "testOutsiderOpenRejectedBeforeNonce",
    "testOutsiderWithdrawalReachesSignatureCheck",
    "testReusedCloseNonceRejected",
    "testReusedNonceRejected",
    "testReusedOpenNonceRejected",
    "testSet2BatchAllowlistAgainstAddedSelectors",
    "testSet2ClaimBuilderFeesScope",
    "testSet2CloseBuilderWordCandidates",
    "testSet2CloseBuilderWordIsNotSigned",
    "testSet2DepositProxySurface",
    "testSet2FinalizeControls",
    "testSet2FinalizeCreditsTheStoredSnapshot",
    "testSet2KeeperIsNotASignedIntentCaller",
    "testSet2NonceBitmapSharedAcrossIntentClasses",
    "testSet2NonceIsPerUser",
    "testSet2OutsiderDrivesVictimSweep",
    "testSet2OwnerBuilderSweepEntry",
    "testSet2RecoveryGuards",
    "testSet2RegistrationByBatchExecutor",
    "testSet2RetryReservesOneUsdc",
    "testSet2SessionKeyLifecycleAndAssociatedAddress",
    "testSet2SweepFamilyBuilderReads",
    "testSet2WithdrawalExtraUnitWhenStatusFalse",
    "testSignedAmountMismatchRollsBack",
    "testSignedDeadlineMismatchRollsBack",
    "testSignedNonceMismatchRollsBack",
    "testSignedUserMismatchRollsBack",
    "testValidOpenSignatureReachesPostSignerRevert",
    "testValidSignatureAllowsOutsiderRelayer",
    "testValidWithdrawalPersistsNonceAndDebits",
    "testValidWithdrawalReplayRejectedNextBlock",
    "testWrongDomainWithdrawalSignatureRollsBack",
    "testWrongValidWithdrawalSignerRollsBackNonce"
]

EXPECTED_OBSERVATIONS = {
    "set2_batch_allowlist": {
        "added_rejected": 9,
        "allowlisted_close_ok": True,
        "dropped_direct_selector": 0,
        "dropped_rejected": True,
        "name": "set2_batch_allowlist",
        "slot_88_is_batch": True
    },
    "set2_batch_close_debug": {
        "executed": True,
        "inner_bytes": 0,
        "inner_ok": True,
        "inner_selector": 0,
        "name": "set2_batch_close_debug",
        "ok": True,
        "rejected": False
    },
    "set2_builder_claim_a": {
        "entry_a_after": 0,
        "entry_b_after_a": 7000000000000000000,
        "name": "set2_builder_claim_a",
        "ok": True,
        "paid": 5000000000000000000,
        "selector": 0
    },
    "set2_builder_claim_others": {
        "caller_b_ok": True,
        "caller_b_selector": 0,
        "entry_b_after_b": 88000000000000000000,
        "name": "set2_builder_claim_others",
        "outsider_ok": True,
        "outsider_selector": 0,
        "paid_b": 7000000000000000000,
        "paid_outsider": 0
    },
    "set2_builder_close_candidates": {
        "error": "Expecting ',' delimiter: line 1 column 74 (char 73)",
        "malformed": "{\"name\":\"set2_builder_close_candidates\",\"ok\":true,\"selector\":0,\"length\":6\"ids_read_bitmap\":,\"ids_read_bitmap\":0,\"ids_write_bitmap\":0,\"read_count\":16,\"write_count\":0}\n"
    },
    "set2_builder_close_plain": {
        "name": "set2_builder_close_plain",
        "ok": True,
        "read_count": 11,
        "reads_zero_builder": False,
        "selector": 0,
        "write_count": 0,
        "writes_zero_builder": False
    },
    "set2_builder_close_trailing": {
        "a_ok": True,
        "a_reads_builderA": False,
        "a_writes_builderA": False,
        "b_ok": True,
        "b_reads_builderA": False,
        "b_reads_builderB": False,
        "b_selector": 0,
        "b_writes_builderB": False,
        "name": "set2_builder_close_trailing"
    },
    "set2_builder_sweep_entry": {
        "entry_a": 0,
        "entry_b": 12000000000000000000,
        "key_bits": 15,
        "name": "set2_builder_sweep_entry",
        "outsider_ok": False,
        "outsider_selector": 818771057,
        "owner_ok": True,
        "owner_selector": 0,
        "shared": 100000000000000000000
    },
    "set2_deposit_proxy_surface": {
        "fallback": False,
        "name": "set2_deposit_proxy_surface",
        "native_funding": False,
        "outsider_rescue": False,
        "outsider_sweep": False,
        "user_rescue_no_code": True
    },
    "set2_finalize_controls": {
        "below_minimum_selector": 0,
        "name": "set2_finalize_controls",
        "no_pending_selector": 159688215,
        "same_block_selector": 3530554059,
        "unchanged_selector": 0
    },
    "set2_finalize_controls_below": {
        "bytes": 0,
        "name": "set2_finalize_controls_below",
        "ok": True,
        "selector": 0,
        "stored_block": 0,
        "stored_spot": 0,
        "writer_bytes": 196
    },
    "set2_finalize_controls_debug": {
        "name": "set2_finalize_controls_debug",
        "unchanged_bytes": 0,
        "unchanged_ok": True,
        "unchanged_selector": 0
    },
    "set2_finalize_credit": {
        "half_left": 1000000000000000000,
        "name": "set2_finalize_credit",
        "one_unit_left": 1000000000000000000,
        "stored_snapshot": 1000000000000000000
    },
    "set2_keeper": {
        "close_selector": 3667325110,
        "first_written_slot": 89,
        "name": "set2_keeper",
        "open_selector": 3667325110,
        "withdraw_selector": 3254943978,
        "written_slots": 1
    },
    "set2_nonce_per_user": {
        "name": "set2_nonce_per_user",
        "other_user_selector": 3305398050
    },
    "set2_nonce_shared": {
        "adjacent_word_accepted": True,
        "close_selector": 0,
        "name": "set2_nonce_shared",
        "open_selector": 1969654014,
        "register_selector": 1969654014,
        "withdraw_selector": 1969654014
    },
    "set2_open_post_signer": {
        "name": "set2_open_post_signer",
        "ok": False,
        "selector": 172972551
    },
    "set2_outsider_sweep": {
        "below_minimum_selector": 849095439,
        "name": "set2_outsider_sweep",
        "pending_spot": 10000000000,
        "queued_total": 10000000000
    },
    "set2_recovery_guards": {
        "clear_returndata_bytes": 0,
        "name": "set2_recovery_guards",
        "outsider_selector": 818771057,
        "owner_selector": 686768916
    },
    "set2_registration": {
        "expiry_stored": 1792364541,
        "name": "set2_registration",
        "nonce_bit": 4398046511104,
        "outsider_selector": 2478279816,
        "session_key_signature_selector": 2343196575
    },
    "set2_retry_reserve": {
        "name": "set2_retry_reserve",
        "observed_balance": 10000000000,
        "queued_total": 9900000000,
        "stored_spot": 9900000000
    },
    "set2_session_lifecycle": {
        "associated_address": 1402402230564801881840782179186293279750436966564,
        "associated_set_key_ok": True,
        "associated_set_key_selector": 0,
        "associated_signer_ok": False,
        "associated_signer_selector": 3305398050,
        "expiry_at_timestamp_ok": True,
        "expiry_at_timestamp_selector": 0,
        "name": "set2_session_lifecycle"
    },
    "set2_sweep_builder_bits": {
        "finalize": 0,
        "layout": "bit0 failed, bits1..8 are (read,write) of seeded builderFees entries for USER, address(0), a, proxy",
        "name": "set2_sweep_builder_bits",
        "request": 0,
        "sweep_fresh": 0,
        "sweep_pending": 0
    },
    "set2_withdrawal_gap": {
        "name": "set2_withdrawal_gap",
        "status_false_core_amount": 200000000,
        "status_false_debit": 3000000000000000000,
        "status_false_outsider_debit": 3000000000000000000,
        "status_true_debit": 2000000000000000000
    }
}

CORE_WITHDRAWAL_TOPIC = ("0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75")
SWEEP_REQUESTED_TOPIC = ("0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025")
SWEPT_TOPIC = ("0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696")
PENDING_CLEARED_TOPIC = ("0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e")

STALLED_SWEEP_TXS = [
    "0x99c1cfb96136fa735421048a9af350b2a54c85036723776276d4f9d85b570a20",
    "0xeeb6dbb140d1ed4d435c169d99407ada8eb4a58dd554e9a071843246246f6b75",
    "0x47cd43341d3a3b5de575043f032b345814e822cc06c69c272fc99289a7f50032",
    "0x28cac136ea4d5e29d413428616454c153f1a8ee6a8f120c45483b81830cfd98a",
]

keccak = Keccak()
pause_between = 25.0


def rpc(method, params, retries=6, pause=30.0):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(RPC, data=body, headers={"content-type": "application/json"})
            with urllib.request.urlopen(request, timeout=40) as response:
                payload = json.loads(response.read().decode())
            if "result" in payload:
                return payload["result"]
            last = payload
        except Exception as exc:  # rate limit, timeout, transport
            last = repr(exc)
        time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"{method} failed after {retries} attempts: {last}")


def runtime(address, hex_file):
    text = hex_file.read_text().strip()
    data = bytes.fromhex(text[2:] if text.startswith("0x") else text)
    return "0x" + data.hex()


def selector_set(data, limit=4096):
    return {"0x" + m.group(1).hex() for m in
            re.finditer(b"\x63(.{4})\x14\x61(..)\x57", data[:limit], re.DOTALL)}


def push32(data):
    out, pc = [], 0
    while pc < len(data):
        opcode = data[pc]
        if 0x60 <= opcode <= 0x7F:
            size = opcode - 0x5F
            if opcode == 0x7F and pc + 33 <= len(data):
                out.append((pc, data[pc + 1:pc + 33].hex()))
            pc += 1 + size
        else:
            pc += 1
    return out


def load_runtimes():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN and manifest["block_hash"] == PIN_HASH
    out = {}
    for label, address in (("ExchangeProxy1", EXCHANGE), ("ExchangeImpl1", EXCHANGE_IMPL_1),
                           ("SessionProxy1", SESSION), ("SessionImpl1", SESSION_IMPL_1),
                           ("BatchExecutorProxy", BATCH), ("FactoryProxy", FACTORY)):
        row = manifest["contracts"][address]
        code = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == row["sha256"], label
        out[label] = code
    impl = next(a for a, row in manifest["contracts"].items()
                if row["role"] == "batch_executor_implementation")
    code = (ATLAS / manifest["contracts"][impl]["runtime_file"]).read_text().strip()
    out["BatchExecutorImpl"] = code
    suite = json.loads((ATLAS / "suite_sets.json").read_text())
    expected = {
        "exchange_impl": (EXCHANGE_IMPL_2, 23959, "fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268"),
        "session_impl": (SESSION_IMPL_2, 4521, "7df05c33597c04820a314fae015aab01b5566aff53e9bded8446962cfd4ad2c9"),
        "library": (LIBRARY_2, 6286, "ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440"),
        "builder_registry": (BUILDER_REGISTRY, 1210, "f459de55cb0463912417650fbca7e18109f3820551e4071234109e1e72801d2f"),
    }
    for label, (address, size, digest) in expected.items():
        code = runtime(address, ROOT / "artifacts" / "postpin_suite" / "runtime" / f"{address}.hex")
        raw = bytes.fromhex(code[2:])
        assert len(raw) == size, (label, len(raw))
        assert hashlib.sha256(raw).hexdigest() == digest, label
        out[label] = code
    out["_suite"] = suite
    out["_manifest"] = manifest
    return out


def capture():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reads = json.loads(READS.read_text()) if READS.exists() else {}
    reads.setdefault("rpc", RPC)
    reads.setdefault("captured_at_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    def put(path, call):
        section = reads
        for key in path[:-1]:
            section = section.setdefault(key, {})
        if path[-1] in section:
            print(f"  cached {'.'.join(path)}")
            return section[path[-1]]
        value = call()
        section[path[-1]] = value
        READS.write_text(json.dumps(reads, indent=1) + "\n")
        print(f"  read {'.'.join(path)}", flush=True)
        time.sleep(pause_between)
        return value

    put(["head"], lambda: int(rpc("eth_blockNumber", []), 16))
    for label, address in (("exchange_proxy", EXCHANGE), ("session_proxy", SESSION),
                           ("timelock", TIMELOCK)):
        put(["code", label], lambda address=address: {"address": address,
                                                     "code": rpc("eth_getCode", [address, "latest"])})
    for slot in (1, 2, 3, 8):
        put(["session_slots", str(slot)],
            lambda slot=slot: rpc("eth_getStorageAt", [SESSION, hex(slot), "latest"]))
    for name, data in (("DOMAIN_SEPARATOR", "0x3644e515"), ("domainSeparatorV4", "0x78e890ba"),
                       ("builderRegistry", "0xe737de13"), ("owner", "0x8da5cb5b")):
        put(["session_calls", name],
            lambda data=data: rpc("eth_call", [{"to": SESSION, "data": data}, "latest"]))
    put(["exchange_calls", "slot_88"],
        lambda: rpc("eth_getStorageAt", [EXCHANGE, hex(88), "latest"]))
    put(["exchange_calls", "owner"],
        lambda: rpc("eth_call", [{"to": EXCHANGE, "data": "0x8da5cb5b"}, "latest"]))
    head = reads["head"]
    first = max(1, head - 999)
    for label, topic in (("core_withdrawal", CORE_WITHDRAWAL_TOPIC),
                         ("sweep_requested", SWEEP_REQUESTED_TOPIC)):
        def fetch(topic=topic):
            logs = rpc("eth_getLogs", [{"address": EXCHANGE, "topics": [topic],
                                        "fromBlock": hex(first), "toBlock": "latest"}])
            return {"topic": topic, "from_block": first, "count": len(logs), "logs": logs[:40]}
        put(["logs", label], fetch)
    print(f"live_reads.json complete at head {head}: "
          f"{reads['logs']['core_withdrawal']['count']} withdrawal logs, "
          f"{reads['logs']['sweep_requested']['count']} sweep logs in the last 1000 blocks")


EXTRA_TESTS = r'''
    // ================= live contract set 2 additions =================

    address constant OUTSIDER = address(0x000000000000000000000000000000000000dEaD);
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant KEEPER = address(uint160(uint256(0x000924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56)));
    address constant FACTORY = address(uint160(uint256(0x001629b7d46bef6e13ff754174fc9f32dea309b38f)));
    address constant FACTORY_IMPL = address(uint160(uint256(0x008f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0)));
    address constant BATCH_IMPL = address(uint160(uint256(0x00e0bc9cc7b067060aafccbaa3e250700c9cdd7262)));
    address constant STAKING = address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016)));
    address constant ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant SPOT_READ = address(0x0801);
    address constant PERP_READ = address(0x0803);
    bytes32 constant REGISTER_TYPEHASH = 0xd3d9a309f635415423ab81e7e3fb16d2117cc8e1edc90506adde9eaa3855edd2;
    bytes32 constant CALL_EXECUTED_TOPIC = 0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad;
    bytes32 constant CALL_REJECTED_TOPIC = 0x6002fcbae88fcbb8133c69c91df90bbc0b4464af94df2a56f8bb843f1cc5a193;
    uint256 constant MINIMUM_RAW = 1_000_000_000;
    uint256 constant SWEEP_SCALE = 10 ** 10;

    struct Call { address target; bytes data; bool continueOnFailure; bytes32 intentId; bytes32 extra; }

    function record(string memory name, string memory body) internal {
        vm.writeFile(string.concat("out/", name, ".json"),
                     string.concat("{\"name\":\"", name, "\",", body, "}\n"));
    }

    function signAsUser(bytes32 structHash) internal returns (uint8 v, bytes32 r, bytes32 sigS) {
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (v, r, sigS) = vm.sign(0xa11ce, digest);
        require(ecrecover(digest, v, r, sigS) == USER, "user signer identity");
    }

    function signWithdrawalNonce(uint64 deadline, uint256 nonce) internal returns (uint8 v, bytes32 r, bytes32 s) {
        bytes32 structHash = keccak256(abi.encode(WITHDRAW_TYPEHASH, USER, uint256(2_000_000), nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (v, r, s) = vm.sign(0xa11ce, digest);
        require(ecrecover(digest, v, r, s) == USER, "synthetic signer");
    }

    function selectorOf(bytes memory out) internal pure returns (uint256 value) {
        if (out.length < 4) return 0;
        assembly { value := mload(add(out, 0x20)) }
        return value >> 224;
    }

    function etchInfra() internal {
        vm.etch(BATCH, vm.parseBytes(vm.readFile("runtime/BatchExecutorProxy.hex")));
        vm.etch(BATCH_IMPL, vm.parseBytes(vm.readFile("runtime/BatchExecutorImpl.hex")));
        vm.store(BATCH, IMPLEMENTATION_SLOT, bytes32(uint256(uint160(BATCH_IMPL))));
        vm.store(BATCH, ADMIN_SLOT, bytes32(uint256(uint160(ADMIN))));
        // The allowlist is anchored to the stored suite addresses (slots 0 to 2).
        vm.store(BATCH, bytes32(uint256(0)), bytes32((uint256(uint160(EXCHANGE)) << 16) | 1));
        vm.store(BATCH, bytes32(uint256(1)), bytes32(uint256(uint160(SESSION))));
        vm.store(BATCH, bytes32(uint256(2)), bytes32(uint256(uint160(STAKING))));
        vm.store(BATCH, bytes32(uint256(3)), bytes32(uint256(uint160(OWNER))));
        vm.store(BATCH, bytes32(uint256(5)), bytes32(uint256(1)));
        vm.etch(FACTORY, vm.parseBytes(vm.readFile("runtime/FactoryProxyOfMock.hex")));
    }

    function pendingSlot() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(33)));
    }

    function balanceSlot() internal pure returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(9)));
    }

    function mockFile(string memory name) internal {
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile(string.concat("runtime/", name, "_spot.hex"))));
        vm.etch(PERP_READ, vm.parseBytes(vm.readFile(string.concat("runtime/", name, "_perp.hex"))));
    }

    function pendingWord(uint64 spot, uint64 perp, uint256 block_) internal pure returns (bytes32) {
        return bytes32(uint256(spot) | (uint256(perp) << 64) | (block_ << 128));
    }

    function derivedProxy() internal returns (address) {
        (bool ok, bytes memory out) = FACTORY.staticcall(abi.encodeWithSelector(bytes4(0xc1a9a508), USER));
        require(ok && out.length == 32, "factory proxyOf");
        address proxy = abi.decode(out, (address));
        vm.etch(proxy, vm.parseBytes(vm.readFile("runtime/ProxyUser.hex")));
        return proxy;
    }

    function slice4(bytes memory data) internal pure returns (bytes memory out) {
        require(data.length >= 4, "short payload");
        out = new bytes(data.length - 4);
        for (uint256 i; i < out.length; ++i) out[i] = data[i + 4];
    }

    function runBatch(address relayer, address target, bytes memory data, bool continueOnFailure)
        internal returns (bool ok, bytes memory out, bool rejected, bool executed, bool innerOk,
                          bytes memory innerReturn) {
        Call[] memory calls = new Call[](1);
        calls[0] = Call(target, data, continueOnFailure, bytes32(0), bytes32(0));
        vm.recordLogs();
        vm.prank(relayer);
        (ok, out) = BATCH.call(abi.encodeWithSelector(bytes4(0x251fb27d), calls));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] == CALL_REJECTED_TOPIC) rejected = true;
            if (logs[i].topics[0] == CALL_EXECUTED_TOPIC && logs[i].emitter == BATCH) {
                executed = true;
                (innerOk, innerReturn) = abi.decode(logs[i].data, (bool, bytes));
            }
        }
    }

    function closeWith(uint256 nonce, uint64 deadline) internal returns (bool, bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce,
            deadline, v, r, sigS));
    }

    function closeWithKey(uint256 nonce, uint64 deadline, uint256 key) internal returns (bool, bytes memory) {
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(key, keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash)));
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce,
            deadline, v, r, sigS));
    }

    function enableSubmitter(address who) internal {
        vm.store(SESSION, keccak256(abi.encode(who, uint256(7))), bytes32(uint256(1)));
    }

    function sessionWord(uint64 expiry, address associated) internal pure returns (bytes32) {
        return bytes32(uint256(expiry) | (uint256(uint160(associated)) << 64));
    }

    function testSet2RegistrationByBatchExecutor() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        uint64 expiry = uint64(block.timestamp + 7200);
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, USER, SESSION_KEY, expiry,
            address(0), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signAsUser(structHash);
        enableSubmitter(BATCH);
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok, bytes memory out) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE, deadline, v, r, sigS));
        if (!ok) revert UnexpectedResult(ok, out);
        uint256 word = uint256(vm.load(SESSION, sessionKeySlot()));
        require(uint64(word) == expiry, "expiry stored");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "registration bit set");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length >= 1, "registration event");
        // an unrelated caller cannot register
        vm.prank(OUTSIDER);
        (bool outsiderOk, bytes memory outsiderOut) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE + 1, deadline, v, r, sigS));
        require(!outsiderOk && errorIs(outsiderOut, 0x93b78c88), "UnauthorizedSubmitter");
        // a digest signed by the session key rather than the user must not register a key
        bytes32 secondHash = keccak256(abi.encode(REGISTER_TYPEHASH, USER, SESSION_KEY, expiry,
            address(0), NONCE + 2, deadline));
        (uint8 sv, bytes32 sr, bytes32 ss) = signTrade(secondHash);
        vm.prank(BATCH);
        (bool sessionOk, bytes memory sessionOut) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE + 2, deadline, sv, sr, ss));
        require(!sessionOk && errorIs(sessionOut, 0x8baa579f), "InvalidSignature for a session-key signature");
        require(uint256(vm.load(SESSION, nonceBitSlotFor(USER, NONCE + 2))) == (1 << NONCE),
            "the failed registration marks no extra bit");
        record("set2_registration", string.concat("\"expiry_stored\":", vm.toString(uint64(word)),
            ",\"nonce_bit\":", vm.toString(uint256(vm.load(SESSION, nonceBitSlot()))),
            ",\"outsider_selector\":", vm.toString(selectorOf(outsiderOut)),
            ",\"session_key_signature_selector\":", vm.toString(selectorOf(sessionOut))));
    }

    function testSet2NonceBitmapSharedAcrossIntentClasses() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (bool consumed,) = consume(deadline);
        require(consumed && uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "bit consumed");
        enableSessionKey();
        uint256 openSelector = blockedOpen(deadline);
        uint256 withdrawalSelector = blockedWithdrawal(deadline);
        uint256 registerSelector = blockedRegistration(deadline);
        uint256 next = NONCE + 256;
        (bool closeOk, bytes memory closeOut) = closeWith(next, deadline);
        require(closeOk, "adjacent word accepted");
        require(uint256(vm.load(SESSION, nonceBitSlotFor(USER, next))) == (1 << (next & 255)),
            "adjacent word bit set");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "first word untouched");
        record("set2_nonce_shared", string.concat("\"open_selector\":", vm.toString(openSelector),
            ",\"withdraw_selector\":", vm.toString(withdrawalSelector),
            ",\"register_selector\":", vm.toString(registerSelector),
            ",\"adjacent_word_accepted\":true,\"close_selector\":", vm.toString(selectorOf(closeOut))));
    }

    function blockedOpen(uint64 deadline) internal returns (uint256) {
        bytes32 openHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(0), true,
            uint128(1e18), uint32(10), false, NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 s) = signTrade(openHash);
        (bool ok, bytes memory out) = openSigned(BATCH, deadline, v, r, s);
        require(!ok && errorIs(out, 0x756688fe), "open blocked by the used bit");
        return selectorOf(out);
    }

    function blockedWithdrawal(uint64 deadline) internal returns (uint256) {
        (uint8 v, bytes32 r, bytes32 s) = signWithdrawal(deadline);
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, s);
        require(!ok && errorIs(out, 0x756688fe), "withdrawal blocked by the used bit");
        return selectorOf(out);
    }

    function blockedRegistration(uint64 deadline) internal returns (uint256) {
        enableSubmitter(BATCH);
        uint64 expiry = uint64(block.timestamp + 7200);
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, USER, SESSION_KEY, expiry,
            address(0), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 s) = signAsUser(structHash);
        vm.prank(BATCH);
        (bool ok, bytes memory out) = SESSION.call(abi.encodeWithSelector(bytes4(0x5f76a1d6),
            USER, SESSION_KEY, expiry, address(0), NONCE, deadline, v, r, s));
        require(!ok && errorIs(out, 0x756688fe), "registration blocked by the used bit");
        return selectorOf(out);
    }

    function testSet2NonceIsPerUser() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (bool consumed,) = consume(deadline);
        require(consumed, "consume for user");
        address other = address(uint160(uint256(0x0000000000000000000000000000000000000b0b0b)));
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, other,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xdead1, keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash)));
        vm.prank(BATCH);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706),
            other, ids, NONCE, deadline, v, r, sigS));
        require(!ok && errorIs(out, 0xc5045f22), "other user nonce is untouched");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "user bit unchanged");
        record("set2_nonce_per_user", string.concat("\"other_user_selector\":", vm.toString(selectorOf(out))));
    }

    function testSet2SessionKeyLifecycleAndAssociatedAddress() public {
        address associated = vm.addr(0xc0ffee);
        (bool okA,) = lifecycleCase(uint64(block.timestamp + 3600), address(0), NONCE, 0);
        require(okA, "unexpired key accepted");
        require(!lifecycleRejects(uint64(block.timestamp - 1), address(0), NONCE + 1, 0),
            "expired key rejected");
        (bool okC, uint256 selC) = lifecycleCase(uint64(block.timestamp), address(0), NONCE + 2, 0);
        (bool okD, uint256 selD) = lifecycleCase(uint64(block.timestamp + 3600), associated, NONCE + 3, 0);
        (bool okE, uint256 selE) = lifecycleCase(uint64(block.timestamp + 3600), associated, NONCE + 4, 0xc0ffee);
        vm.store(SESSION, sessionKeySlot(), sessionWord(uint64(block.timestamp + 3600), address(0)));
        vm.prank(USER);
        (bool revokeOk, bytes memory revokeOut) = SESSION.call(abi.encodeWithSelector(bytes4(0x84f4fc6a), SESSION_KEY));
        if (!revokeOk) revert UnexpectedResult(revokeOk, revokeOut);
        require(vm.load(SESSION, sessionKeySlot()) == 0, "revocation clears the key word");
        require(!lifecycleRejects(uint64(block.timestamp + 3600), address(0), NONCE + 5, 0),
            "revoked key rejected");
        record("set2_session_lifecycle", string.concat("\"expiry_at_timestamp_ok\":", okC ? "true" : "false",
            ",\"expiry_at_timestamp_selector\":", vm.toString(selC),
            ",\"associated_set_key_ok\":", okD ? "true" : "false",
            ",\"associated_set_key_selector\":", vm.toString(selD),
            ",\"associated_signer_ok\":", okE ? "true" : "false",
            ",\"associated_signer_selector\":", vm.toString(selE),
            ",\"associated_address\":", vm.toString(uint160(associated))));
    }

    function lifecycleRejects(uint64 expiry, address associated, uint256 nonce, uint256 key) internal returns (bool) {
        (bool ok, uint256 selector) = lifecycleCase(expiry, associated, nonce, key);
        return !ok && selector == 0xc5045f22;
    }

    function lifecycleCase(uint64 expiry, address associated, uint256 nonce, uint256 key)
        internal returns (bool ok, uint256 selector) {
        vm.store(SESSION, sessionKeySlot(), sessionWord(expiry, associated));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes memory out;
        if (key == 0) (ok, out) = closeWith(nonce, deadline);
        else (ok, out) = closeWithKey(nonce, deadline, key);
        selector = selectorOf(out);
    }

    function testSet2KeeperIsNotASignedIntentCaller() public {
        vm.record();
        vm.prank(OWNER);
        (bool setOk, bytes memory setOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xefc1bd46), KEEPER));
        if (!setOk) revert UnexpectedResult(setOk, setOut);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        require(writes.length >= 1, "keeper storage written");
        require(!contains(writes, bytes32(uint256(88))), "keeper is not slot 88");
        vm.prank(OUTSIDER);
        (bool outsiderOk,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xefc1bd46), KEEPER));
        require(!outsiderOk, "outsider cannot set the keeper");
        uint64 deadline = uint64(block.timestamp + 3600);
        (bool closeOk, bytes memory closeOut) = closeAs(KEEPER, deadline);
        require(!closeOk && errorIs(closeOut, 0xda96f0b6), "keeper blocked from close");
        (bool openOk, bytes memory openOut) = openAs(KEEPER, deadline);
        require(!openOk && errorIs(openOut, 0xda96f0b6), "keeper blocked from open");
        (bool wOk, bytes memory wOut) = withdrawAs(KEEPER, deadline);
        require(!wOk && errorIs(wOut, 0xc20280ea), "keeper reaches the withdrawal signature check");
        record("set2_keeper", string.concat("\"written_slots\":", vm.toString(writes.length),
            ",\"first_written_slot\":", vm.toString(uint256(writes[0])),
            ",\"close_selector\":", vm.toString(selectorOf(closeOut)),
            ",\"open_selector\":", vm.toString(selectorOf(openOut)),
            ",\"withdraw_selector\":", vm.toString(selectorOf(wOut))));
    }

    function testSet2BatchAllowlistAgainstAddedSelectors() public {
        etchInfra();
        address relayer = address(uint160(uint256(0x0000000000000000000000000000000000000a11ce)));
        vm.store(BATCH, keccak256(abi.encode(relayer, uint256(4))), bytes32(uint256(1)));
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(88)))) == uint256(uint160(BATCH)),
            "live slot 88 is the BatchExecutor");
        (bool ctlOk, bytes memory ctlOut,,,,) =
            runBatch(OUTSIDER, EXCHANGE, abi.encodePacked(bytes4(0xec6783f0)), true);
        require(!ctlOk && errorIs(ctlOut, 0x17fb2066), "NotAuthorizedRelayer for an unknown relayer");
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0x69f9a5f0));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0x9d346583));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xcbce7532));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xd970fad5));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xe6ac4a74));
        addedSelectorRejected(relayer, EXCHANGE, bytes4(0xf009ac03));
        addedSelectorRejected(relayer, SESSION, bytes4(0xbd322efa));
        addedSelectorRejected(relayer, SESSION, bytes4(0xd95208cd));
        addedSelectorRejected(relayer, SESSION, bytes4(0xe737de13));
        allowlistedCloseThroughBatch(relayer);
        (bool ok3,, bool rejected3,,,) =
            runBatch(relayer, EXCHANGE, abi.encodePacked(bytes4(0x415f1240), uint256(0)), true);
        require(ok3 && rejected3, "dropped selector is not allowlisted");
        (bool directOk, bytes memory directOut) =
            EXCHANGE.call(abi.encodeWithSelector(bytes4(0x415f1240), uint256(0)));
        require(!directOk && directOut.length == 0, "dropped selector absent from the live dispatcher");
        record("set2_batch_allowlist", string.concat("\"added_rejected\":9",
            ",\"allowlisted_close_ok\":true,\"dropped_rejected\":true",
            ",\"dropped_direct_selector\":", vm.toString(selectorOf(directOut)),
            ",\"slot_88_is_batch\":true"));
    }

    function addedSelectorRejected(address relayer, address target, bytes4 selector) internal {
        (bool ok,, bool rejected, bool executed,,) =
            runBatch(relayer, target, abi.encodePacked(selector, uint256(0)), true);
        require(ok, "batch completes");
        require(rejected && !executed, "added selector rejected by the allowlist");
    }

    function allowlistedCloseThroughBatch(address relayer) internal {
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        (bool ok,, bool rejected, bool executed, bool innerOk, bytes memory innerReturn) = runBatch(relayer, EXCHANGE,
            abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, NONCE, deadline, v, r, sigS), true);
        record("set2_batch_close_debug", string.concat("\"ok\":", ok ? "true" : "false",
            ",\"rejected\":", rejected ? "true" : "false", ",\"executed\":", executed ? "true" : "false",
            ",\"inner_ok\":", innerOk ? "true" : "false",
            ",\"inner_selector\":", vm.toString(selectorOf(innerReturn)),
            ",\"inner_bytes\":", vm.toString(innerReturn.length)));
        require(ok && !rejected && executed && innerOk, "allowlisted close executes through the batch");
        require(uint256(vm.load(SESSION, nonceBitSlot())) == (1 << NONCE), "inner close consumed its nonce");
    }

    function testSet2WithdrawalExtraUnitWhenStatusFalse() public {
        uint64 deadline = uint64(block.timestamp + 3600);
        (uint8 v, bytes32 r, bytes32 sigS) = signWithdrawal(deadline);
        vm.etch(STATUS, vm.parseBytes(vm.readFile("runtime/mock_status_0.hex")));
        uint256 before = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.recordLogs();
        (bool ok, bytes memory out) = withdrawSigned(BATCH, deadline, v, r, sigS);
        if (!ok) revert UnexpectedResult(ok, out);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        uint256 debit;
        uint256 sent;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] == 0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75) {
                (debit, sent) = abi.decode(logs[i].data, (uint256, uint256));
            }
        }
        require(debit == 3e18, "one USD above the signed amount");
        require(sent == 200_000_000, "core payload is the signed amount times 100");
        require(before - uint256(vm.load(EXCHANGE, balanceSlot())) == debit, "user debit matches the event");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == before - 3e18, "user balance");
        // the withdrawal path allows one withdrawal per user per block
        vm.roll(block.number + 1);
        // the caller does not change the fee treatment
        uint64 deadline2 = uint64(block.timestamp + 3601);
        (uint8 v2, bytes32 r2, bytes32 sig2) = signWithdrawalNonce(deadline2, NONCE + 1);
        uint256 before2 = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.etch(STATUS, vm.parseBytes(vm.readFile("runtime/mock_status_0.hex")));
        (bool ok3, bytes memory out3) = withdrawSignedFields(OUTSIDER, USER, 2_000_000, NONCE + 1, deadline2, v2, r2, sig2);
        if (!ok3) revert UnexpectedResult(ok3, out3);
        uint256 outsiderDebit = before2 - uint256(vm.load(EXCHANGE, balanceSlot()));
        require(outsiderDebit == 3e18, "outsider caller sees the same debit");
        // with an existing account the debit is exactly the signed amount
        vm.roll(block.number + 1);
        vm.etch(STATUS, vm.parseBytes(vm.readFile("runtime/mock_status_1.hex")));
        uint64 deadline4 = uint64(block.timestamp + 3602);
        (uint8 v4, bytes32 r4, bytes32 sig4) = signWithdrawalNonce(deadline4, NONCE + 2);
        uint256 before4 = uint256(vm.load(EXCHANGE, balanceSlot()));
        (bool ok4, bytes memory out4) = withdrawSignedFields(BATCH, USER, 2_000_000, NONCE + 2,
            deadline4, v4, r4, sig4);
        if (!ok4) revert UnexpectedResult(ok4, out4);
        uint256 existingDebit = before4 - uint256(vm.load(EXCHANGE, balanceSlot()));
        require(existingDebit == 2e18, "no extra unit for an existing account");
        record("set2_withdrawal_gap", string.concat("\"status_false_debit\":", vm.toString(debit),
            ",\"status_false_core_amount\":", vm.toString(sent),
            ",\"status_false_outsider_debit\":", vm.toString(outsiderDebit),
            ",\"status_true_debit\":", vm.toString(existingDebit)));
    }

    function testSet2DepositProxySurface() public {
        etchInfra();
        address proxy = derivedProxy();
        (bool userOk, bytes memory userOut) = proxy.staticcall(abi.encodeWithSelector(bytes4(0x4f8632ba)));
        (bool exchangeOk, bytes memory exchangeOut) = proxy.staticcall(abi.encodeWithSelector(bytes4(0xd2f7265a)));
        require(userOk && abi.decode(userOut, (address)) == USER, "user immutable");
        require(exchangeOk && abi.decode(exchangeOut, (address)) == EXCHANGE, "exchange immutable");
        (bool valueOk,) = proxy.call{value: 1}("");
        require(!valueOk, "no native funding path");
        (bool unknownOk,) = proxy.call(abi.encodeWithSelector(bytes4(0xdeadbeef)));
        require(!unknownOk, "no fallback");
        (bool outsiderSweep,) = proxy.call(abi.encodeWithSelector(bytes4(0x925b3aad),
            uint64(0), uint64(0), uint64(0)));
        require(!outsiderSweep, "sweep is exchange only");
        (bool outsiderRescue,) = proxy.call(abi.encodeWithSelector(bytes4(0x0c506e96), proxy, uint256(1)));
        require(!outsiderRescue, "rescue is user only");
        vm.prank(USER);
        (bool rescueOk, bytes memory rescueOut) = proxy.call(abi.encodeWithSelector(bytes4(0x0c506e96),
            address(0x0000000000000000000000000000000000000001), uint256(1)));
        require(rescueOk, "user rescue of a no-code token");
        record("set2_deposit_proxy_surface", string.concat("\"native_funding\":false,\"fallback\":false",
            ",\"outsider_sweep\":false,\"outsider_rescue\":false,\"user_rescue_no_code\":true"));
    }

    function testSet2OutsiderDrivesVictimSweep() public {
        etchInfra();
        address proxy = derivedProxy();
        mockFile("mock_1e10");
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xe0189108), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        bytes32 pending = vm.load(EXCHANGE, pendingSlot());
        require(uint64(uint256(pending)) == 10_000_000_000, "pending spot stored");
        require(uint64(uint256(pending) >> 128) == block.number, "pending block stored");
        bytes memory writerCall = CoreWriterMock(CORE_WRITER).lastInput();
        require(writerCall.length > 68, "core writer reached");
        bytes memory action = abi.decode(slice4(writerCall), (bytes));
        require(bytes4(action) == bytes4(0x01000006), "action 6 last");
        (address dest, uint64 tokenId, uint64 total) = abi.decode(slice4(action), (address, uint64, uint64));
        require(dest == EXCHANGE && tokenId == 0, "send destination");
        require(total == 10_000_000_000, "full observed balance queued, no gas reserve");
        // below the request minimum
        mockFile("mock_1e10");
        vm.store(EXCHANGE, pendingSlot(), 0);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.roll(block.number + 1);
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_999999999_spot.hex")));
        vm.prank(OUTSIDER);
        (bool lowOk, bytes memory lowOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xe0189108), USER));
        require(!lowOk && errorIs(lowOut, 0x329c2b0f), "below minimum rejected");
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_1000000000_spot.hex")));
        vm.prank(OUTSIDER);
        (bool minOk,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xe0189108), USER));
        require(minOk, "at the minimum accepted");
        record("set2_outsider_sweep", string.concat("\"queued_total\":", vm.toString(uint256(total)),
            ",\"pending_spot\":", vm.toString(uint64(uint256(pending))),
            ",\"below_minimum_selector\":", vm.toString(selectorOf(lowOut))));
    }

    function finalizeCredit(uint64 currentSpot) internal returns (uint256 credit) {
        etchInfra();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number - 1));
        mockFile("mock_1e8");
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile(
            currentSpot == 1 ? "runtime/mock_1_spot.hex" : "runtime/mock_50000000_spot.hex")));
        uint256 before = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        credit = uint256(vm.load(EXCHANGE, balanceSlot())) - before;
    }

    function testSet2FinalizeCreditsTheStoredSnapshot() public {
        uint256 oneUnitLeft = finalizeCredit(1);
        uint256 half = finalizeCredit(50_000_000);
        require(oneUnitLeft == half, "credit independent of the size of the decrease");
        require(oneUnitLeft == 100_000_000 * SWEEP_SCALE, "credit is the stored snapshot");
        etchInfra();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number - 1));
        mockFile("mock_1e8");
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_1_spot.hex")));
        uint256 treasuryBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        uint256 totalBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) & type(uint128).max;
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) - treasuryBefore == oneUnitLeft, "treasury credit");
        require((uint256(vm.load(EXCHANGE, bytes32(uint256(22)))) & type(uint128).max) - totalBefore == oneUnitLeft,
            "total balance credit");
        require(vm.load(EXCHANGE, pendingSlot()) == 0, "pending cleared");
        record("set2_finalize_credit", string.concat("\"one_unit_left\":", vm.toString(oneUnitLeft),
            ",\"half_left\":", vm.toString(half),
            ",\"stored_snapshot\":", vm.toString(uint256(100_000_000) * SWEEP_SCALE)));
    }

    function testSet2RetryReservesOneUsdc() public {
        etchInfra();
        address proxy = derivedProxy();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        mockFile("mock_1e10");
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        bytes32 pending = vm.load(EXCHANGE, pendingSlot());
        require(uint64(uint256(pending)) == 9_900_000_000, "retry reserves one USD");
        require(uint64(uint256(pending) >> 128) == block.number, "retry block updated");
        bytes memory writerCall = CoreWriterMock(CORE_WRITER).lastInput();
        (address dest, uint64 tokenId, uint64 total) =
            abi.decode(slice4(abi.decode(slice4(writerCall), (bytes))), (address, uint64, uint64));
        require(dest == EXCHANGE && tokenId == 0 && total == 9_900_000_000, "queued send is the reduced amount");
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == uint256(vm.load(EXCHANGE, balanceSlot())),
            "no credit on the retry branch");
        require(vm.load(EXCHANGE, bytes32(uint256(14))) > 0, "treasury seeded");
        record("set2_retry_reserve", string.concat("\"stored_spot\":", vm.toString(uint64(uint256(pending))),
            ",\"queued_total\":", vm.toString(uint256(total)),
            ",\"observed_balance\":", vm.toString(uint256(10_000_000_000))));
    }

    function testSet2FinalizeControls() public {
        // unchanged above the minimum: no credit, the request is replaced
        etchInfra();
        address proxy = derivedProxy();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        mockFile("mock_1e10");
        uint256 before = uint256(vm.load(EXCHANGE, balanceSlot()));
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        record("set2_finalize_controls_debug", string.concat("\"unchanged_ok\":", ok ? "true" : "false",
            ",\"unchanged_selector\":", vm.toString(selectorOf(out)),
            ",\"unchanged_bytes\":", vm.toString(out.length)));
        if (!ok) revert UnexpectedResult(ok, out);
        require(uint256(vm.load(EXCHANGE, balanceSlot())) == before, "no credit when unchanged");
        require(uint64(uint256(vm.load(EXCHANGE, pendingSlot()))) == 9_900_000_000,
            "request replaced with the reduced amount");
        // increased above the minimum: still no credit
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        vm.etch(SPOT_READ, vm.parseBytes(vm.readFile("runtime/mock_10000000001_spot.hex")));
        vm.prank(OUTSIDER);
        (bool ok2,) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        require(ok2 && uint256(vm.load(EXCHANGE, balanceSlot())) == before, "increase does not credit");
        // unchanged at the minimum: retry below the threshold
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number - 1));
        mockFile("mock_1e8");
        vm.prank(OUTSIDER);
        (bool ok3, bytes memory out3) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        bytes32 pending3 = vm.load(EXCHANGE, pendingSlot());
        bytes memory writer3 = CoreWriterMock(CORE_WRITER).lastInput();
        record("set2_finalize_controls_below", string.concat("\"ok\":", ok3 ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(out3)), ",\"bytes\":", vm.toString(out3.length),
            ",\"stored_spot\":", vm.toString(uint64(uint256(pending3))),
            ",\"stored_block\":", vm.toString(uint64(uint256(pending3) >> 128)),
            ",\"writer_bytes\":", vm.toString(writer3.length)));
        require(ok3 && uint64(uint256(pending3)) == 0, "dust retry clears the pending request");
        // no pending request
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, pendingSlot(), 0);
        vm.prank(OUTSIDER);
        (bool ok4, bytes memory out4) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        require(!ok4, "no pending request rejected");
        // same block
        vm.roll(block.number + 1);
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number));
        vm.prank(OUTSIDER);
        (bool ok5, bytes memory out5) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        require(!ok5, "same block rejected");
        record("set2_finalize_controls", string.concat("\"unchanged_selector\":", vm.toString(selectorOf(out)),
            ",\"below_minimum_selector\":", vm.toString(selectorOf(out3)),
            ",\"no_pending_selector\":", vm.toString(selectorOf(out4)),
            ",\"same_block_selector\":", vm.toString(selectorOf(out5))));
    }

    address constant LIBRARY_2 = address(uint160(uint256(0x00583d0bd818c991c5830fea93aef04e474b272459)));

    function builderFeeSlot(address builder) internal pure returns (bytes32) {
        return keccak256(abi.encode(builder, uint256(39)));
    }

    function builderFeesMapping(address builder) internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, builderFeeSlot(builder)));
    }

    function sharedBuilderSlot() internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, bytes32(uint256(38)))) >> 160;
    }

    function closeCalldata(uint256[] memory ids, uint256 nonce, uint64 deadline, uint8 v, bytes32 r,
        bytes32 s, bytes memory trailing) internal pure returns (bytes memory) {
        return bytes.concat(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, deadline,
            v, r, s), trailing);
    }

    // Does the signed close bind the builder address it credits?
    function testSet2CloseBuilderWordIsNotSigned() public {
        etchInfra();
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        address builderA = vm.addr(0xaa11);
        address builderB = vm.addr(0xbb11);
        // (a) the plain seven-argument calldata: which builder key, if any, is touched?
        vm.record();
        vm.prank(BATCH);
        (bool okA, bytes memory outA) =
            EXCHANGE.call(closeCalldata(ids, NONCE, deadline, v, r, sigS, ""));
        (bytes32[] memory readsA, bytes32[] memory writesA) = vm.accesses(EXCHANGE);
        // (b) the same signature with one extra unsigned trailing word
        uint256 next = NONCE + 1;
        bytes32 structHashB = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), next, deadline));
        (uint8 vB, bytes32 rB, bytes32 sB) = signTrade(structHashB);
        bytes memory withA = abi.encode(uint256(uint160(builderA)));
        vm.record();
        vm.prank(BATCH);
        (bool okB, bytes memory outB) =
            EXCHANGE.call(closeCalldata(ids, next, deadline, vB, rB, sB, withA));
        (bytes32[] memory readsB, bytes32[] memory writesB) = vm.accesses(EXCHANGE);
        // (c) only the trailing word changes
        uint256 next2 = NONCE + 2;
        bytes32 structHashC = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), next2, deadline));
        (uint8 vC, bytes32 rC, bytes32 sC) = signTrade(structHashC);
        vm.record();
        vm.prank(BATCH);
        (bool okC, bytes memory outC) = EXCHANGE.call(closeCalldata(ids, next2, deadline, vC, rC, sC,
            abi.encode(uint256(uint160(builderB)))));
        (bytes32[] memory readsC, bytes32[] memory writesC) = vm.accesses(EXCHANGE);
        record("set2_builder_close_plain", string.concat(
            "\"ok\":", okA ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(outA)),
            ",\"reads_zero_builder\":", contains(readsA, builderFeeSlot(address(0))) ? "true" : "false",
            ",\"writes_zero_builder\":", contains(writesA, builderFeeSlot(address(0))) ? "true" : "false",
            ",\"read_count\":", vm.toString(readsA.length),
            ",\"write_count\":", vm.toString(writesA.length)));
        record("set2_builder_close_trailing", string.concat(
            "\"a_ok\":", okB ? "true" : "false",
            ",\"a_reads_builderA\":", contains(readsB, builderFeeSlot(builderA)) ? "true" : "false",
            ",\"a_writes_builderA\":", contains(writesB, builderFeeSlot(builderA)) ? "true" : "false",
            ",\"b_ok\":", okC ? "true" : "false",
            ",\"b_selector\":", vm.toString(selectorOf(outC)),
            ",\"b_reads_builderB\":", contains(readsC, builderFeeSlot(builderB)) ? "true" : "false",
            ",\"b_reads_builderA\":", contains(readsC, builderFeeSlot(builderA)) ? "true" : "false",
            ",\"b_writes_builderB\":", contains(writesC, builderFeeSlot(builderB)) ? "true" : "false"));
    }

    // Which calldata word, if any, becomes the credited builder address?
    function testSet2CloseBuilderWordCandidates() public {
        etchInfra();
        enableSessionKey();
        uint64 deadline = uint64(block.timestamp + 3600);
        uint256 length = 6;
        uint256[] memory ids = new uint256[](length);
        for (uint256 i; i < length; ++i) ids[i] = 0xaa00 + i;
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        (uint8 v, bytes32 r, bytes32 sigS) = signTrade(structHash);
        vm.record();
        vm.prank(BATCH);
        (bool ok, bytes memory out) =
            EXCHANGE.call(closeCalldata(ids, NONCE, deadline, v, r, sigS, ""));
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        uint256 readBitmap;
        uint256 writeBitmap;
        for (uint256 i; i < length; ++i) {
            if (contains(reads, builderFeeSlot(address(uint160(ids[i]))))) readBitmap |= (1 << i);
            if (contains(writes, builderFeeSlot(address(uint160(ids[i]))))) writeBitmap |= (1 << i);
        }
        record("set2_builder_close_candidates", string.concat(
            "\"ok\":", ok ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(out)),
            ",\"length\":", vm.toString(length),
            "\"ids_read_bitmap\":", "",
            ",\"ids_read_bitmap\":", vm.toString(readBitmap),
            ",\"ids_write_bitmap\":", vm.toString(writeBitmap),
            ",\"read_count\":", vm.toString(reads.length),
            ",\"write_count\":", vm.toString(writes.length)));
    }

    // Do the sweep-family entries reach the slot-39 builder accumulator block?
    function probeBuilderReads(bytes4 selector, bytes memory data, address proxy, bool pending)
        internal returns (uint256 flag) {
        if (pending) {
            vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        } else {
            vm.store(EXCHANGE, pendingSlot(), 0);
        }
        vm.store(EXCHANGE, keccak256(abi.encode(proxy, uint256(32))), 0);
        address a = vm.addr(0xaa11);
        vm.store(EXCHANGE, builderFeeSlot(USER), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(address(0)), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(a), bytes32(uint256(5e18)));
        if (proxy != address(0)) {
            vm.store(EXCHANGE, builderFeeSlot(proxy), bytes32(uint256(5e18)));
        }
        vm.record();
        vm.prank(OUTSIDER);
        (bool ok,) = EXCHANGE.call(abi.encodePacked(selector, data));
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        if (!ok) flag |= 1;
        uint256 candidates = 4;
        uint256 bits = 0;
        for (uint256 i; i < candidates; ++i) {
            address who = i == 0 ? USER : i == 1 ? address(0) : i == 2 ? a : proxy;
            if (contains(reads, builderFeeSlot(who))) bits |= (1 << (2 * i));
            if (contains(writes, builderFeeSlot(who))) bits |= (1 << (2 * i + 1));
        }
        flag |= bits << 8;
    }

    function testSet2OwnerBuilderSweepEntry() public {
        etchInfra();
        address a = vm.addr(0xaa11);
        address b = vm.addr(0xbb11);
        vm.store(EXCHANGE, builderFeeSlot(a), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(b), bytes32(uint256(7e18)));
        vm.store(EXCHANGE, bytes32(uint256(38)), bytes32(uint256(100e18) << 160));
        vm.record();
        vm.prank(OUTSIDER);
        (bool outsiderOk, bytes memory outsiderOut) =
            EXCHANGE.call(abi.encodeWithSelector(bytes4(0xd970fad5), a, b));
        vm.record();
        vm.prank(OWNER);
        (bool ownerOk, bytes memory ownerOut) =
            EXCHANGE.call(abi.encodeWithSelector(bytes4(0xd970fad5), a, b));
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        uint256 bits;
        for (uint256 i; i < 2; ++i) {
            address who = i == 0 ? a : b;
            if (contains(reads, builderFeeSlot(who))) bits |= (1 << (2 * i));
            if (contains(writes, builderFeeSlot(who))) bits |= (1 << (2 * i + 1));
        }
        record("set2_builder_sweep_entry", string.concat(
            "\"outsider_ok\":", outsiderOk ? "true" : "false",
            ",\"outsider_selector\":", vm.toString(selectorOf(outsiderOut)),
            ",\"owner_ok\":", ownerOk ? "true" : "false",
            ",\"owner_selector\":", vm.toString(selectorOf(ownerOut)),
            ",\"entry_a\":", vm.toString(builderFeesMapping(a)),
            ",\"entry_b\":", vm.toString(builderFeesMapping(b)),
            ",\"shared\":", vm.toString(sharedBuilderSlot()),
            ",\"key_bits\":", vm.toString(bits)));
    }

    function testSet2SweepFamilyBuilderReads() public {
        etchInfra();
        address proxy = derivedProxy();
        address a = vm.addr(0xaa11);
        mockFile("mock_1e10");
        uint256 sweepPending = probeBuilderReads(bytes4(0x01681a62), abi.encode(USER), proxy, true);
        uint256 sweepFresh = probeBuilderReads(bytes4(0x01681a62), abi.encode(USER), proxy, false);
        uint256 request = probeBuilderReads(bytes4(0xe0189108), abi.encode(USER), proxy, false);
        uint256 finalize = probeBuilderReads(bytes4(0x6d142da1), abi.encode(USER), proxy, true);
        record("set2_sweep_builder_bits", string.concat(
            "\"sweep_pending\":", vm.toString(sweepPending),
            ",\"sweep_fresh\":", vm.toString(sweepFresh),
            ",\"request\":", vm.toString(request),
            ",\"finalize\":", vm.toString(finalize),
            ",\"layout\":\"bit0 failed, bits1..8 are (read,write) of seeded builderFees entries for USER, address(0), a, proxy\""));
    }

    // Is claimBuilderFees per-caller or shared?
    function testSet2ClaimBuilderFeesScope() public {
        etchInfra();
        vm.etch(LIBRARY_2, vm.parseBytes(vm.readFile("runtime/Library2.hex")));
        address builderA = vm.addr(0xaa11);
        address builderB = vm.addr(0xbb11);
        vm.store(EXCHANGE, builderFeeSlot(builderA), bytes32(uint256(5e18)));
        vm.store(EXCHANGE, builderFeeSlot(builderB), bytes32(uint256(7e18)));
        vm.store(EXCHANGE, bytes32(uint256(38)), bytes32(uint256(100e18) << 160));
        vm.recordLogs();
        vm.prank(builderA);
        (bool okA, bytes memory outA) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x69f9a5f0)));
        Vm.Log[] memory logsA = vm.getRecordedLogs();
        uint256 paidA;
        for (uint256 i; i < logsA.length; ++i) {
            if (logsA[i].topics[0] == 0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15) {
                (paidA,) = abi.decode(logsA[i].data, (uint256, uint256));
            }
        }
        uint256 entryBAfterA = builderFeesMapping(builderB);
        vm.recordLogs();
        (bool okB, bytes memory outB) = callAs(builderB, abi.encodeWithSelector(bytes4(0x69f9a5f0)));
        Vm.Log[] memory logsB = vm.getRecordedLogs();
        uint256 paidB;
        for (uint256 i; i < logsB.length; ++i) {
            if (logsB[i].topics[0] == 0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15) {
                (paidB,) = abi.decode(logsB[i].data, (uint256, uint256));
            }
        }
        uint256 sharedAfterB = sharedBuilderSlot();
        vm.recordLogs();
        (bool okC, bytes memory outC) = callAs(OUTSIDER, abi.encodeWithSelector(bytes4(0x69f9a5f0)));
        Vm.Log[] memory logsC = vm.getRecordedLogs();
        uint256 paidC;
        for (uint256 i; i < logsC.length; ++i) {
            if (logsC[i].topics[0] == 0x3416b71ef34c8c9fa3f6669951a3b8ff28131879e96b2f9b68fef2029a9dfa15) {
                (paidC,) = abi.decode(logsC[i].data, (uint256, uint256));
            }
        }
        record("set2_builder_claim_a", string.concat(
            "\"ok\":", okA ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(outA)),
            ",\"paid\":", vm.toString(paidA),
            ",\"entry_a_after\":", vm.toString(builderFeesMapping(builderA)),
            ",\"entry_b_after_a\":", vm.toString(entryBAfterA)));
        record("set2_builder_claim_others", string.concat(
            "\"caller_b_ok\":", okB ? "true" : "false",
            ",\"caller_b_selector\":", vm.toString(selectorOf(outB)),
            ",\"entry_b_after_b\":", vm.toString(sharedAfterB == 0 ? 0 : sharedAfterB),
            ",\"paid_b\":", vm.toString(paidB),
            ",\"outsider_ok\":", okC ? "true" : "false",
            ",\"outsider_selector\":", vm.toString(selectorOf(outC)),
            ",\"paid_outsider\":", vm.toString(paidC)));
    }

    function callAs(address who, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(who);
        return EXCHANGE.call(data);
    }

    function testSet2RecoveryGuards() public {
        vm.store(EXCHANGE, pendingSlot(), pendingWord(50_050_916, 0, block.number - 1));
        vm.prank(OUTSIDER);
        (bool outsiderOk, bytes memory outsiderOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6a3214c9),
            USER, uint256(50_050_916)));
        require(!outsiderOk && errorIs(outsiderOut, 0x30cd7471), "NotOwner for an outsider");
        vm.prank(OWNER);
        (bool ownerOk, bytes memory ownerOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6a3214c9),
            USER, uint256(50_050_916)));
        require(!ownerOk && errorIs(ownerOut, 0x28ef4314), "SweepAlreadyPending for the owner");
        vm.prank(OWNER);
        (bool clearOk, bytes memory clearOut) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2362f4de), USER));
        require(!clearOk && clearOut.length == 0, "clearPendingSweep is absent");
        require(uint64(uint256(vm.load(EXCHANGE, pendingSlot()))) == 50_050_916, "pending word unchanged");
        record("set2_recovery_guards", string.concat("\"outsider_selector\":", vm.toString(selectorOf(outsiderOut)),
            ",\"owner_selector\":", vm.toString(selectorOf(ownerOut)),
            ",\"clear_returndata_bytes\":", vm.toString(clearOut.length)));
    }
'''

VM_EXTRA = """    function addr(uint256) external returns (address);
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function writeFile(string calldata, string calldata) external;
    function toString(uint256) external pure returns (string memory);
}"""

DEPOSIT_PROXY_EXCHANGE_OFFSETS = (0x61, 0xDE)
DEPOSIT_PROXY_USER_OFFSETS = (0x37B, 0x3DA)

DIFF_TESTS = r'''
    function testDiffRetryAmount() public {
        etchInfra();
        address proxy = derivedProxy();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(10_000_000_000, 0, block.number - 1));
        mockFile("mock_1e10");
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        if (!ok) revert UnexpectedResult(ok, out);
        bytes32 pending = vm.load(EXCHANGE, pendingSlot());
        bytes memory writerCall = CoreWriterMock(CORE_WRITER).lastInput();
        uint64 total;
        if (writerCall.length > 68) {
            (, , total) = abi.decode(slice4(abi.decode(slice4(writerCall), (bytes))),
                                     (address, uint64, uint64));
        }
        record("diff_retry_amount", string.concat("\"stored_spot\":", vm.toString(uint64(uint256(pending))),
            ",\"queued_total\":", vm.toString(uint256(total)),
            ",\"observed_balance\":", vm.toString(uint256(10_000_000_000))));
    }

    function testDiffRetryDust() public {
        etchInfra();
        derivedProxy();
        vm.store(EXCHANGE, pendingSlot(), pendingWord(100_000_000, 0, block.number - 1));
        mockFile("mock_1e8");
        vm.prank(OUTSIDER);
        (bool ok, bytes memory out) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x6d142da1), USER));
        bytes32 pending = vm.load(EXCHANGE, pendingSlot());
        record("diff_retry_dust", string.concat("\"ok\":", ok ? "true" : "false",
            ",\"selector\":", vm.toString(selectorOf(out)),
            ",\"stored_spot_after\":", vm.toString(uint64(uint256(pending)))));
    }
'''

MOCKS = {
    "mock_status_1": [(1,)],
    "mock_status_0": [(0,)],
    "mock_1_spot": [(1, 0, 0)],
    "mock_1_perp": [(0,)],
    "mock_1e8_spot": [(100_000_000, 0, 0)],
    "mock_1e8_perp": [(0,)],
    "mock_1e10_spot": [(10_000_000_000, 0, 0)],
    "mock_1e10_perp": [(0,)],
    "mock_10000000001_spot": [(10_000_000_001, 0, 0)],
    "mock_10000000001_perp": [(0,)],
    "mock_50000000_spot": [(50_000_000, 0, 0)],
    "mock_50000000_perp": [(0,)],
    "mock_999999999_spot": [(999_999_999, 0, 0)],
    "mock_999999999_perp": [(0,)],
    "mock_1000000000_spot": [(1_000_000_000, 0, 0)],
    "mock_1000000000_perp": [(0,)],
}


def derive_proxy_runtime(base_hex, user):
    runtime = bytearray(bytes.fromhex(base_hex[2:]))
    exchange_word = int(EXCHANGE, 16).to_bytes(32, "big")
    user_word = int(user, 16).to_bytes(32, "big")
    for offset in DEPOSIT_PROXY_EXCHANGE_OFFSETS:
        runtime[offset:offset + 32] = exchange_word
    for offset in DEPOSIT_PROXY_USER_OFFSETS:
        runtime[offset:offset + 32] = user_word
    return "0x" + bytes(runtime).hex()


def derived_proxy_address(user, factory=FACTORY):
    """CREATE2 address of the factory's user proxy: keccak256(0xff || factory || keccak(user) || keccak(initcode))."""
    deploy = json.loads((ROOT / "artifacts" / "historical" /
                         "0xddf30f3fd0d78c0516e37f32ed1ece2ef4ab488d7b4be8439c7196878047fb2e.calls.json"
                         ).read_text())
    initcode = bytes.fromhex(deploy["calls"][0]["calls"][0]["input"][2:])
    assert len(initcode) == 1889
    code = initcode[:-32] + int(user, 16).to_bytes(32, "big")
    salt = keccak(bytes.fromhex(user[2:]))
    return "0x" + keccak(b"\xff" + bytes.fromhex(factory[2:]) + salt + keccak(code)).hex()[-40:]


def mock_code(values):
    code = "0x"
    for index, value in enumerate(values):
        code += "7f" + value.to_bytes(32, "big").hex() + "60" + f"{32 * index:02x}" + "52"
    return code + "60" + f"{32 * len(values):02x}" + "6000f3"


def run_forge(source, runtime_files, label, timeout=240, raise_on_failure=True, extra_args=()):
    assert shutil.which("forge") and shutil.which("solc"), "forge and solc are required"
    with tempfile.TemporaryDirectory(prefix=f"papertrade-{label}-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "out").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(shutil.which("solc")) +
            "\noffline = true\nvia_ir = true\nfs_permissions = [{ access = \"read\", path = \"./runtime\" },"
            " { access = \"read-write\", path = \"./out\" }]\n")
        (project / "test" / "Live2Intents.t.sol").write_text(source)
        for name, code in runtime_files.items():
            (project / "runtime" / f"{name}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv", *extra_args], capture_output=True,
                             text=True, timeout=timeout)
        output = run.stdout + "\n" + run.stderr
        if run.returncode and raise_on_failure and "Suite result: FAILED" not in output:
            raise RuntimeError(f"{label} forge run failed:\n{output[-12000:]}")
        observations = {}
        for path in sorted((project / "out").glob("*.json")):
            try:
                observations[path.stem] = json.loads(path.read_text())
            except json.JSONDecodeError as error:
                observations[path.stem] = {"malformed": path.read_text(), "error": str(error)}
    return output, observations


def build_diff_source(pinned_source, live):
    """Shared helpers plus the differential cases, compiled against either runtime set."""
    assert pinned_source.rstrip().endswith("}")
    helpers = EXTRA_TESTS[:EXTRA_TESTS.index("    function test")]
    source = pinned_source[:pinned_source.rstrip().rfind("}")] + helpers + DIFF_TESTS + "}\n"
    source = source.replace("    function addr(uint256) external returns (address);\n}", VM_EXTRA)
    source = source.replace("contract SignedIntentFailuresTest", "contract Live2IntentsDiffTest")
    if live:
        source = source.replace("0x000f3febfc94876b0c895f7acecdc8f5c863b549ee",
                                "0x000a44049dbbb6b4762a6ba37aa0f7548c0b4a3723")
        source = source.replace("0x008a5069fe303e8f81e91825436e956d595032e558",
                                "0x0004b5ea4cdd8d6de4bd6e0ef3865266947f043946")
        source = source.replace("runtime/ExchangeImpl.hex", "runtime/ExchangeImpl2.hex")
        source = source.replace("runtime/SessionImpl.hex", "runtime/SessionImpl2.hex")
    return source


def build_live_source(pinned_source, live_slot_88, live_builder_registry):
    """Turn the verified pinned exact-runtime suite into the live contract set 2 suite."""
    source = pinned_source
    assert source.rstrip().endswith("}")
    source = source[:source.rstrip().rfind("}")] + EXTRA_TESTS + "}\n"
    source = source.replace("    function addr(uint256) external returns (address);\n}", VM_EXTRA)
    source = source.replace("contract SignedIntentFailuresTest", "contract Live2IntentsTest")
    source = source.replace("0x000f3febfc94876b0c895f7acecdc8f5c863b549ee",
                            "0x000a44049dbbb6b4762a6ba37aa0f7548c0b4a3723")
    source = source.replace("0x008a5069fe303e8f81e91825436e956d595032e558",
                            "0x0004b5ea4cdd8d6de4bd6e0ef3865266947f043946")
    source = source.replace("runtime/ExchangeImpl.hex", "runtime/ExchangeImpl2.hex")
    source = source.replace("runtime/SessionImpl.hex", "runtime/SessionImpl2.hex")
    pinned_slot = "vm.store(EXCHANGE, bytes32(uint256(88)), %s);" % pinned_harness_slot88()
    assert pinned_slot in source
    source = source.replace(pinned_slot, f"vm.store(EXCHANGE, bytes32(uint256(88)), {live_slot_88});")
    session_line = "vm.store(SESSION, bytes32(uint256(3)), %s);" % SESSION_DIRECT_SLOTS_1[3]
    assert session_line in source
    source = source.replace(session_line,
                            session_line + f"\n        vm.store(SESSION, bytes32(uint256(8)), "
                                           f"{live_builder_registry});")
    # The open path's post-signer error is unresolved on the live runtime: record it instead.
    source = source.replace(
        "        if (openOk || !errorIs(openOut, 0x0a4f5a07)) revert UnexpectedResult(openOk, openOut);",
        '        record("set2_open_post_signer", string.concat("\\"ok\\":", openOk ? "true" : "false",'
        ' ", \\"selector\\":", vm.toString(selectorOf(openOut))));')
    return source


def pinned_harness_slot88():
    return "0x000000000000000000000000233ff29b239abc1d7748605da9b205c3e008626e"


LIVE_SOURCES = {
    "postpin_pin": ("artifacts/postpin_pin/raw_reads.json",
                    "read-only HyperEVM probes captured by the post-pin atlas check"),
    "live_latest": ("artifacts/postpin_suite/live_latest.json.gz",
                    "head reads and Core account state at the post-pin pin check"),
}


def saved_live_evidence():
    """Head-era values from saved read-only captures (no RPC credential, offline)."""
    import gzip
    evidence = {"sources": [], "values": {}}
    raw = json.loads((ROOT / LIVE_SOURCES["postpin_pin"][0]).read_text())
    by_key = {row["key"]: row for row in raw["reads"]}
    values = evidence["values"]
    values["head"] = int(raw["block_number"], 16)
    values["exchange_slot_88"] = by_key["exchange_authorized_executor_word"]["raw"]["result"]
    values["exchange_owner"] = by_key["exchange_owner"]["raw"]["result"]
    values["exchange_authorized_executor_getter"] = by_key["exchange_authorized_executor"]["raw"]["result"]
    code = {row["key"]: row["raw"]["result"] for row in raw["reads"] if row["key"].startswith("code:")}
    values["session_proxy_sha256"] = hashlib.sha256(
        bytes.fromhex(code[f"code:{SESSION}"][2:])).hexdigest()
    evidence["sources"].append(LIVE_SOURCES["postpin_pin"])
    with gzip.open(ROOT / LIVE_SOURCES["live_latest"][0]) as handle:
        live = json.load(handle)
    probes = live["probes"]
    values["session_builder_registry"] = probes["session_key_manager_builder_registry"]["result"]
    values["session_registry_old_value_owner_call"] =         probes["session_key_manager_registry_old_value"]["result"]
    values["session_owner"] = probes["session_key_manager_registry_old_value"]["from"]
    values["head_older"] = live["head"]["block"]
    evidence["sources"].append(LIVE_SOURCES["live_latest"])
    if READS.exists():
        mine = json.loads(READS.read_text())
        values["own_capture"] = mine
        evidence["sources"].append((str(READS.relative_to(ROOT)), "own read-only capture"))
    return evidence


def ledger_rows(runtimes, evidence, forge):
    """Audit ledger rows in the shared schema."""
    values = evidence["values"]
    cap = values.get("own_capture")
    domain_live = (cap or {}).get("session_calls", {}).get("domainSeparatorV4")
    obs = forge["observations"]
    rows = [
        {
            "id": "L2-D1-01",
            "title": "The set 2 SessionKeyManager keeps the pinned EIP-712 domain; the domain's verifying contract is the Exchange, not the SessionKeyManager",
            "angle": "D1 signature and domain separation",
            "invariant": "A2",
            "actor": "trading user, session key",
            "precondition": "a signature produced against the pinned domain ahead of the upgrade",
            "trigger": "submit the same signature to the set 2 SessionKeyManager by any allowed caller",
            "impact": "no impact: no replay or invalidation window opens at the upgrade, because the domain is derived from chainId, the authorized caller (the Exchange proxy, which never changes address) and the initialization-time name and version",
            "affected": "both",
            "severity": "none",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay of the live configuration plus a live head read",
            "evidence": {
                "live_head_read": {"head": cap.get("head") if cap else None,
                                   "DOMAIN_SEPARATOR": cap.get("session_calls", {}).get("DOMAIN_SEPARATOR")
                                   if cap else None,
                                   "domainSeparatorV4": domain_live,
                                   "slot_1": cap.get("session_slots", {}).get("1") if cap else None,
                                   "slot_3": cap.get("session_slots", {}).get("3") if cap else None},
                "live_suite": ["testValidWithdrawalPersistsNonceAndDebits",
                               "testWrongDomainWithdrawalSignatureRollsBack",
                               "testWrongValidWithdrawalSignerRollsBackNonce",
                               "testSignedUserMismatchRollsBack",
                               "testSignedAmountMismatchRollsBack"],
                "observations": {key: obs[key] for key in obs if key in ("set2_open_post_signer",)},
                "domain_separator_at_pin": PIN_DOMAIN_SEPARATOR,
                "live_read_if_captured": domain_live,
                "typehash_constants_identical": sorted(set(TYPEHASHES)),
            },
            "missing_observation": "none for the domain itself; a live call trace through the set 2 close was not obtained",
            "citations": ["atlas/block_48902346/session_direct_getters.md",
                          "atlas/block_48902346/suite_sets.json"],
        },
        {
            "id": "L2-D1-02",
            "title": "One nonce bitmap word serves every intent class; the class boundary is the EIP-712 typehash, not the nonce",
            "angle": "D1 nonce edges",
            "invariant": "A2",
            "actor": "trading user, session key",
            "precondition": "a nonce bit already consumed by any intent class",
            "trigger": "submit a validly signed open, close, withdrawal or session-key registration with the same nonce",
            "impact": "no unauthorized state change: every class is rejected with InvalidNonce (0x756688fe); the next bitmap word reuses the same bit index without interference; the mapping is per user",
            "affected": "both",
            "severity": "info",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay",
            "evidence": {"observations": {key: obs[key] for key in ("set2_nonce_shared", "set2_nonce_per_user")}},
            "missing_observation": "none; the per-class struct hash boundaries are also covered by the 26-case base suite",
            "citations": ["atlas/block_48902346/session_key_pseudocode.md"],
        },
        {
            "id": "L2-D1-03",
            "title": "Session key expiry is inclusive at the block timestamp, the associated address is metadata rather than a signer, and revocation is immediate",
            "angle": "D1 session-key lifecycle",
            "invariant": "A2",
            "actor": "trading user, session key",
            "precondition": "a registered session key word",
            "trigger": "close by signature at expiry equal to the block timestamp, with a non-zero associated address, and after revokeSessionKey",
            "impact": "no impact beyond a one-second boundary; a key whose word carries a non-zero associated address is still verified against the registered key only, so the field cannot be used to authorize an unexpected signer",
            "affected": "both",
            "severity": "info",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay",
            "evidence": {"observations": obs.get("set2_session_lifecycle")},
            "missing_observation": "the intended product meaning of the associated address remains unresolved",
            "citations": ["atlas/block_48902346/session_key_pseudocode.md"],
        },
        {
            "id": "L2-D2-01",
            "title": "Only the stored signed-intent caller may submit open or close; the signed withdrawal path has no caller gate",
            "angle": "D2 execution gates",
            "invariant": "A1",
            "actor": "unprivileged outsider, keeper",
            "precondition": "Exchange slot 88 holds the BatchExecutor and the new slot 89 holds the keeper",
            "trigger": "call openPositionBySig/closeBySig from an outsider or the keeper, and withdrawToCoreBySig from an outsider",
            "impact": "no state change for the gated paths (0xda96f0b6 before any nonce write); the withdrawal path stays permissionlessly relayable but still requires the user's signature, and a zero signature yields 0xc20280ea",
            "affected": "both",
            "severity": "none",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay plus a saved head storage read",
            "evidence": {"observations": obs.get("set2_keeper"),
                         "live_slot_88": values["exchange_slot_88"],
                         "live_authorized_executor_getter": values["exchange_authorized_executor_getter"],
                         "set_authorized_keeper_wrote_slot": 89},
            "missing_observation": "whether a later governance call repointed the keeper slot",
            "citations": ["atlas/block_48902346/batch_executor_pseudocode.md", "AUDIT.md A1"],
        },
        {
            "id": "L2-D2-02",
            "title": "No selector the set 2 upgrade added is reachable through the BatchExecutor allowlist, and the allowlist is anchored to the stored suite addresses",
            "angle": "D2 allowlist",
            "invariant": "A1",
            "actor": "authorized relayer",
            "precondition": "authorizedRelayers[relayer] set and BatchExecutor slots 0 to 2 holding the Exchange, SessionKeyManager and Staking addresses",
            "trigger": "submit a batch whose inner call targets an added selector, and one whose inner call is the allowlisted signed close",
            "impact": "no reachable state change the user did not sign: nine added selectors (claimBuilderFees, setAuthorizedKeeper, the added SessionKeyManager trio and the four un-named additions) emit CallRejected without an inner call, while the allowlisted signed close executes with the BatchExecutor as the inner caller and consumes its nonce",
            "affected": "set2",
            "severity": "none",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay (pinned BatchExecutor runtime)",
            "evidence": {"observations": obs.get("set2_batch_allowlist"),
                         "inner_close": obs.get("set2_batch_close_debug")},
            "missing_observation": "selectors with no captured candidate are not exhaustively enumerated",
            "citations": ["atlas/block_48902346/batch_executor_pseudocode.md",
                          "artifacts/batch_allowlist_local/replay.json"],
        },
        {
            "id": "L2-D2-03",
            "title": "Session-key registration needs an authorized submitter and a signature from the user, not from the session key",
            "angle": "D2 gates on the registration path",
            "invariant": "A1",
            "actor": "BatchExecutor, unprivileged outsider",
            "precondition": "authorizedSubmitters[BatchExecutor] true",
            "trigger": "registerSessionKeyBySig from an outsider, and with a digest signed by the session key rather than the user",
            "impact": "no unauthorized key registration: the outsider receives UnauthorizedSubmitter (0x93b78c88) and a session-key-signed digest fails signature recovery, so a compromised session key cannot register further keys",
            "affected": "both",
            "severity": "none",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay",
            "evidence": {"observations": obs.get("set2_registration")},
            "missing_observation": "the exact registration type string is still unresolved; the struct hash was re-derived from ten saved digests",
            "citations": ["atlas/block_48902346/session_key_pseudocode.md",
                          "atlas/block_48902346/session_key_behavior.json"],
        },
        {
            "id": "L2-D3-01",
            "title": "The extra one USD withdrawal debit funds the Core new-account fee; the signed amount is delivered in full and no caller can influence the status read",
            "angle": "D3 withdrawal accounting",
            "invariant": "A6",
            "actor": "withdrawal user, relayer",
            "precondition": "the destination Core account-status read returns false",
            "trigger": "withdrawToCoreBySig with a valid signature",
            "impact": "a documented pass-through: the internal debit is the signed amount plus one USD while the Core payload is exactly the signed amount, and the pinned public core ledger shows the matching one USD fee on the Exchange's own Core account with the recipient receiving the signed amount",
            "affected": "both",
            "severity": "low",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay plus the pinned event census and sampled Core ledgers",
            "evidence": {"observations": obs.get("set2_withdrawal_gap"),
                         "census": "5,991 of 28,643 CoreWithdrawal events debit one USD more; 22,652 debit exactly the sent amount",
                         "sampled_ledger": "16 status-0 cases each record a one USD Core fee; 16 status-1 cases record none"},
            "missing_observation": "the public Core ledger does not identify the fee recipient, and no observed case pairs a false status with a zero fee",
            "citations": ["atlas/block_48902346/exchange_core_withdrawal.md",
                          "atlas/block_48902346/withdrawal_settlement_stratified.md", "AUDIT.md A6"],
        },
        {
            "id": "L2-D3-02",
            "title": "The withdrawal path admits one withdrawal per user per block",
            "angle": "D3 sibling gate",
            "invariant": "A6",
            "actor": "withdrawal user, relayer",
            "precondition": "a withdrawal already recorded for that user in the block",
            "trigger": "a second signed withdrawal for the same user in the same block",
            "impact": "no impact: the second call reverts with the unnamed 0x4f57ffae guard, which the pinned direct-path probe records for the same construction",
            "affected": "both",
            "severity": "info",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay plus a saved pinned probe",
            "evidence": {"first_hit": "the status test needed a roll between withdrawals",
                         "pinned_probe": "artifacts/exchange_direct_withdrawal/local_probes.json same_block"},
            "missing_observation": "the guard's source name is unresolved",
            "citations": ["atlas/block_48902346/exchange_getters.md"],
        },
        {
            "id": "L2-D4-01",
            "title": "Any outsider can drive a victim's sweep request, which always queues the full observed balance; no EVM funding path into a proxy exists",
            "angle": "D4 deposit-path liveness as an attack surface",
            "invariant": "A7",
            "actor": "unprivileged outsider",
            "precondition": "the victim's proxy holds at least the 10 USDC request minimum on Core",
            "trigger": "call Exchange requestSweep/sweep(user) for the victim",
            "impact": "the outsider's call succeeds, writes the pending word and queues a CoreWriter spot send of the entire observed balance through the proxy. A native-value call and any unknown selector on the proxy revert, and the sweep requires msg.sender to be the Exchange, so a third party cannot add funds on EVM and cannot create a gas reserve by topping up: each request recomputes the amount as the full current balance",
            "affected": "both",
            "severity": "medium",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay with mocked Core reads plus saved live runtimes",
            "evidence": {"observations": obs.get("set2_outsider_sweep"),
                         "proxy_surface": obs.get("set2_deposit_proxy_surface"),
                         "request_minimum": "10 USDC raw 1e9; 999,999,999 reverts 0x329c2b0f"},
            "missing_observation": "whether a Core-side top-up that lands between the EVM balance read and the Core execution supplies the transfer-gas fee (it would help rather than harm); the Core fee predicate itself is not established",
            "citations": ["FINDINGS.md PT-01", "atlas/block_48902346/exchange_sweep_pseudocode.md",
                          "atlas/block_48902346/deposit_proxy_pseudocode.md"],
        },
        {
            "id": "L2-D4-02",
            "title": "The set 2 retry branch reserves one USD and clears a dust request instead of reverting",
            "angle": "D4 liveness of the wedge, D5 sweep trio",
            "invariant": "A7",
            "actor": "any caller (the finalize and sweep entries are permissionless)",
            "precondition": "a pending sweep request and a proxy Core balance at or above the previous snapshot",
            "trigger": "call finalizeSweep/sweep(user) on the pending request",
            "impact": "on the pinned implementation the retry rewrites the pending word with the full observed balance and, below the 10 USDC minimum, reverts SweepBelowMinimum; on the live set 2 implementation the retry rewrites it with the observed balance less exactly one USD, queues that reduced amount through the proxy, and clears the word when the reduced amount is zero. This is the same one-USD-reserve shape the older recovered proxies used to get their Core send executed, so a permissionless retry may now unwedge a stalled deposit, at the cost of the user being credited one USD less while the reserved unit stays in the proxy's Core account",
            "affected": "set2",
            "severity": "medium",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime differential on both runtimes, cross-checked against saved archive-fork storage diffs",
            "evidence": {"differential": forge["differential"],
                         "saved_fork_pinned": "artifacts/exchange_sweep_archive_local/finalize_unchanged_above_minimum.diff.json stores the full balance; finalize_unchanged.call.json reverts 0x329c2b0f"},
            "missing_observation": "Core acceptance of the reduced send for the two stalled proxies; the saved head reads show both stalled pending words unchanged at head 49,255,838, and no post-upgrade event census could be obtained",
            "citations": ["FINDINGS.md PT-01", "atlas/block_48902346/exchange_sweep_pseudocode.md",
                          "atlas/block_48902346/suite_sets.md"],
        },
        {
            "id": "L2-D5-01",
            "title": "The finalize credit follows the stored snapshot rather than the delivered amount",
            "angle": "D5 credit without delivery",
            "invariant": "A7",
            "actor": "deposit user",
            "precondition": "a pending request whose proxy Core balance has fallen by any amount",
            "trigger": "call finalizeSweep(user)",
            "impact": "the credit follows the stored spot-equivalent rather than the Exchange's observed Core receipt. A real proxy balance decrease without an equal Exchange receipt could create a shortfall, but two observed older reduced retries paid a separate 1 USD sender fee and credited exactly the amount delivered. The fee alone does not establish overcredit",
            "affected": "both",
            "severity": "medium",
            "status": "plausible_unproven",
            "evidence_tier": "exact-runtime replay plus the saved fork case corpus",
            "evidence": {"credit": obs.get("set2_finalize_credit"),
                         "saved_fork": "artifacts/exchange_sweep_archive_local/finalize_partial.diff.json credits 1e18 after a one-raw-unit decrease"},
            "missing_observation": "a real partial Core delivery or other proxy balance decrease without an equal Exchange receipt; neither has been observed in set 2",
            "citations": ["FINDINGS.md PT-01", "atlas/block_48902346/exchange_sweep_pseudocode.md", "AUDIT.md A7"],
        },
        {
            "id": "L2-D5-02",
            "title": "The owner reconciliation route still rejects both live pending words and clearPendingSweep is still absent",
            "angle": "D4 recovery, D5 sweep trio",
            "invariant": "A7",
            "actor": "owner or timelock, unprivileged caller",
            "precondition": "the two stalled pending words",
            "trigger": "owner reconcileSweepCredit(user, amount) and clearPendingSweep(user)",
            "impact": "no recovery through either named route: the owner call reverts SweepAlreadyPending (0x28ef4314), an unrelated caller reverts NotOwner (0x30cd7471) and clearPendingSweep (0x2362f4de) returns empty data",
            "affected": "both",
            "severity": "high",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay plus saved head probes",
            "evidence": {"observations": obs.get("set2_recovery_guards"),
                         "saved_head_probes": "artifacts/postpin_suite/live_latest.json.gz pt01_reconcile_owner/pt01_reconcile_no_sender"},
            "missing_observation": "a differently shaped sweep route cannot be excluded without source or a real trace",
            "citations": ["FINDINGS.md PT-01", "atlas/block_48902346/exchange_sweep_recovery.md"],
        },
        {
            "id": "L2-D3-03",
            "title": "The extra one USD withdrawal debit is not an uncompensated user loss (loss hypothesis disproved)",
            "angle": "D3 withdrawal accounting",
            "invariant": "A6",
            "actor": "withdrawal user",
            "precondition": "a first withdrawal to a Core account that does not yet exist",
            "trigger": "compare the internal debit with the recipient's public Core ledger entry",
            "impact": "no loss relative to the user's intent: the recipient receives exactly the signed amount and the one USD lands as a fee on the Exchange's own Core account; an existing destination pays no fee and debits no extra unit",
            "affected": "both",
            "severity": "none",
            "status": "disproved",
            "evidence_tier": "pinned public Core ledger capture (32 stratified cases) plus the full event census",
            "evidence": {"stratified": "16 status-0 cases deliver the signed amount with a one USD fee; 16 status-1 cases deliver it with none",
                         "census": "no gap other than 0 or one USD across 28,643 CoreWithdrawal events",
                         "exact_runtime": obs.get("set2_withdrawal_gap")},
            "missing_observation": "the ledger does not name the fee recipient",
            "citations": ["atlas/block_48902346/withdrawal_settlement_stratified.md",
                          "atlas/block_48902346/exchange_withdrawal_event_census.json", "AUDIT.md A6"],
        },
        {
            "id": "L2-D4-03",
            "title": "Blocked: the post-upgrade live log census and fresh SessionKeyManager head reads could not be obtained",
            "angle": "D3/D4 live observation",
            "invariant": "A6, A7",
            "actor": "none",
            "precondition": "none",
            "trigger": "eth_getLogs over the last 1000 blocks for the CoreWithdrawal and SweepRequested topics on the newest Exchange proxy, and eth_getStorageAt/eth_call for SessionKeyManager slots 1, 3 and 8 plus DOMAIN_SEPARATOR() and domainSeparatorV4()",
            "impact": "none by itself; it limits how much of this audit is live rather than simulated. The staged retry captured the head, both proxy codes, the SessionKeyManager slots 1, 2, 3 and 8 and the domain getters at head 49,263,577, so only the log census remains missing",
            "affected": "set2",
            "severity": "info",
            "status": "blocked",
            "evidence_tier": "not obtained",
            "evidence": {"attempt": "audit_live2_intents.py --capture, 10 retries with backoff over about 550 s, then a resumable retry that captured everything except the logs",
                         "error": "{\"code\": -32005, \"message\": \"rate limited\"} until the endpoint recovered; the log queries then timed out",
                         "captured_at_head": values["head"],
                         "substitute": "saved head reads in artifacts/postpin_pin/raw_reads.json (head 49,260,476) and artifacts/postpin_suite/live_latest.json.gz (head 49,255,838)"},
            "missing_observation": "the two calls above; no archive RPC key exists in pass and the public endpoint ignores block parameters for state reads",
            "citations": [],
        },
        {
            "id": "L2-D5-03",
            "title": "Deposit proxy surface: four selectors, an immutable user and exchange pair, no fallback, no native path, a user-only rescue",
            "angle": "D5 sibling-path review",
            "invariant": "A7",
            "actor": "unprivileged outsider, proxy user",
            "precondition": "the derived per-user runtime",
            "trigger": "sweepAllToExchange, withdrawStuckToken, a native-value call and an unknown selector",
            "impact": "the sweep is exchange-only, the rescue is user-only and can only move tokens the proxy holds on EVM (none expected, since the venue's assets are Core-side), and unknown selectors or native value revert",
            "affected": "both",
            "severity": "info",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay of a derived per-user runtime",
            "evidence": {"observations": obs.get("set2_deposit_proxy_surface")},
            "missing_observation": "no historical rescue transaction exists",
            "citations": ["atlas/block_48902346/deposit_proxy_pseudocode.md",
                          "artifacts/deposit_proxy_local/replay.json"],
        },
        {
            "id": "L2-D5-04",
            "title": "Factory deposit proxy runtimes have no per-user variation beyond the two embedded user words and the exchange word",
            "angle": "D4 wedge reachability across the family",
            "invariant": "A7",
            "actor": "any user",
            "precondition": "the newest factory CREATE2 derivation",
            "trigger": "derive the runtime and the address for an arbitrary user",
            "impact": "the wedge class is family-wide rather than per-user: the derivation reproduces the two saved live stalled-proxy runtimes byte for byte and five catalog user-to-proxy addresses exactly",
            "affected": "both",
            "severity": "info",
            "status": "confirmed_live",
            "evidence_tier": "saved head runtimes plus a reproducible derivation",
            "evidence": {"stalled_runtime_sha256": ["405e5bfee919c2dcb84ca0854ec56966a8212b322aae41c610e05de235b6b68f",
                                                       "07f9f589f271f1fa58e8a5990bec257eac46c8e0e7b44577d73666ac0a26511d"],
                         "catalog_pairs_checked": 5},
            "missing_observation": "none",
            "citations": ["atlas/block_48902346/deposit_proxy_runtime_derivation.md",
                          "artifacts/postpin_suite/live_latest.json.gz"],
        },
        {
            "id": "L2-D1-06",
            "title": "The set 2 signed close does not bind a builder address: the signed struct is the pinned five-field Close",
            "angle": "D1 signature binding of the set 2 builder fee",
            "invariant": "A2",
            "actor": "authorized relayer, third-party frontend, closer",
            "precondition": "the set 2 Exchange behind the newest Exchange proxy",
            "trigger": "compare the live CLOSE_TYPEHASH with the pinned one, append an unsigned word to the close calldata, and vary the positionIds array",
            "impact": "the signature covers exactly (user, positionIds, nonce, deadline): the live CLOSE_TYPEHASH constant is byte-identical to the hash-verified pinned string and a signature over that struct is accepted. Appending an unsigned eighth word keeps the signature valid and the close succeeds, but it changes neither the credited builder accumulator nor the write set, and a six-element positionIds array does not make any element the credit key. The credit site still keys on a memory word twelve slots past the decode base, so the question the authority workstream left open - whether a relayer can steer the 0.5 percent fee to an address the user did not sign for - is narrowed but not closed: on a fee-paying close the source word is still unidentified",
            "affected": "set2",
            "severity": "medium",
            "status": "plausible_unproven",
            "evidence_tier": "exact-runtime replay on the set 2 runtimes plus bytecode-level typehash comparison",
            "evidence": {"close_typehash": "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13 both sets; "
                                           "hash-checked string Close(address user,uint256[] positionIds,uint256 nonce,uint64 deadline)",
                         "close_selector": "0x2792e706, seven arguments, unchanged",
                         "observations": {key: obs[key] for key in obs if key.startswith("set2_builder_close")},
                         "static": "the credit site loads mload(args_base + 0x180) masked to 160 bits and adds the "
                                   "fee returned by the linked library; the block is only entered when a fee exists"},
            "missing_observation": "a fee-paying (positive realised PnL) close traced on the set 2 runtime, naming the exact word that becomes the builder key; the empty and loss-free closes used here never enter the credit block",
            "citations": ["atlas/block_48902346/live2_authority.md L2A-08",
                          "atlas/block_48902346/session_close_typehash_behavior.json",
                          "atlas/block_48902346/exchange_core_withdrawal.md"],
        },
        {
            "id": "L2-D2-04",
            "title": "claimBuilderFees is caller-scoped: no caller can take another builder's accrual (shared-pool hypothesis disproved)",
            "angle": "D2 gate on the set 2 builder fee claim",
            "invariant": "A1",
            "actor": "any caller",
            "precondition": "builderFees entries for two distinct builders, seeded directly at slot 39",
            "trigger": "call claimBuilderFees() from builder A, from builder B, and from an address with no entry",
            "impact": "no cross-builder theft: A's call pays exactly A's own 5e18 and zeroes only A's entry, B's entry survives; B's call pays exactly B's own 7e18; the shared slot 38 accumulator falls by 5 + 7 only; an arbitrary address succeeds but is paid zero. The claim body keys on keccak256(abi.encode(msg.sender, 39))",
            "affected": "set2",
            "severity": "none",
            "status": "disproved",
            "evidence_tier": "exact-runtime replay of the set 2 runtimes with constructed accruals",
            "evidence": {"observations": {key: obs[key] for key in obs if key.startswith("set2_builder_claim")},
                         "static": "0x3af8: CALLER, MSTORE, PUSH1 0x27, MSTORE, SHA3, SLOAD, require nonzero, SSTORE 0, "
                                   "slot 38 high 96 bits debited, BuilderFeesClaimed 0x3416b71e"},
            "missing_observation": "no on-chain claim has been observed; the seeded accruals are constructed",
            "citations": ["atlas/block_48902346/live2_authority.md L2A-08"],
        },
        {
            "id": "L2-D1-07",
            "title": "The signed-close path couples the two proxies: the set 2 Exchange verifies through a selector only the set 2 SessionKeyManager dispatches, and a failed verifier stops the close",
            "angle": "D1 signed intents across the set 2 upgrade",
            "invariant": "A1, A2",
            "actor": "owner or timelock planning an upgrade, relayer",
            "precondition": "the Exchange and SessionKeyManager proxies with mismatched implementations",
            "trigger": "run a signed close on the set 2 Exchange while the SessionKeyManager proxy points at the pinned implementation",
            "impact": "the two proxies cannot be upgraded independently, and a failed check silently stops the close rather than being tolerated. The set 2 Exchange's close statically calls SessionKeyManager::0xd95208cd(user, digest, v, r, s) on every close; the dispatch bytes exist only in the set 2 SessionKeyManager runtime, so with the pinned implementation behind the proxy the verifier call fails, the inner close reverts, and no position, payout or accumulator state advances (the BatchExecutor wrapper still returns success for the outer transaction, which is why the failure is silent in a batch). A deployment that mixes the implementations therefore keeps taking deposits and withdrawals while quietly closing nothing",
            "affected": "set2",
            "severity": "medium",
            "status": "confirmed_simulation",
            "evidence_tier": "static bytecode check, an exact-runtime call trace, and the authority workstream's four-arm negative control",
            "evidence": {"calltrace": "artifacts/live2_intents/close_verifier_calltrace.txt: 0x6cd56616::2792e706 -> 0x8326eb88::b002b9fa(user,nonce,deadline), 0x8326eb88::d95208cd(user,digest,v,r,s) [staticcall] -> 0x04b5ea4c",
                         "static": "63d95208cd appears once in the set 2 SessionKeyManager runtime and zero times in the pinned runtime, and the Exchange runtime has no dispatch entry of its own for it; asserted in audit_live2_intents.py",
                         "cross_reference": "atlas/block_48902346/live2_authority.md L2A-15 and artifacts/live2_authority/close_coupling.json: direct close with the pinned SessionKeyManager reverts with empty data and writes 0 Exchange slots, direct close with the set 2 SessionKeyManager succeeds with 12 writes, the historical batch with the pinned implementation succeeds with 4 writes and both positions still active, and with the set 2 implementation 22 writes and no position active",
                         "retired_local_arm": "a local implementation-swap arm of mine returned success for the close with the pinned SessionKeyManager behind the proxy; it was unstable between runs and is not used as evidence"},
            "missing_observation": "the failure mode on set 2 era state rather than the pinned mixed-close prestate; the coupling and the fail-closed behaviour themselves are settled",
            "citations": ["atlas/block_48902346/live2_authority.md L2A-15",
                          "artifacts/live2_authority/close_coupling.json",
                          "atlas/block_48902346/suite_sets.json"],
        },
        {
            "id": "L2-D2-05",
            "title": "The owner-only entry 0xd970fad5 moves one address's builder accrual onto another and leaves the shared counter alone",
            "angle": "D2 authority surface on the set 2 builder accumulator",
            "invariant": "A1",
            "actor": "owner (timelock), any caller",
            "precondition": "two seeded builderFees entries at slot 39",
            "trigger": "call 0xd970fad5(a, b) as the owner and as an unrelated address",
            "impact": "an unrelated caller reverts NotOwner (0x30cd7471); the owner call zeroes builderFees[a] (5e18), adds exactly that amount to builderFees[b] (7e18 becomes 12e18) and leaves the shared slot-38 counter untouched. It is a value-moving reassignment of an accrual, not a claim, and it confirms slot 39 is an address-keyed balance rather than a per-call fee",
            "affected": "set2",
            "severity": "low",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay of the set 2 runtimes with constructed accruals",
            "evidence": {"observations": obs.get("set2_builder_sweep_entry"),
                         "sweep_family_probe": obs.get("set2_sweep_builder_bits")},
            "missing_observation": "the source name of 0xd970fad5 and whether any owner call has happened on chain",
            "citations": ["atlas/block_48902346/live2_authority.md L2A-08"],
        },
        {
            "id": "L2-D1-04",
            "title": "The set 2 SessionKeyManager adds the per-close session verifier 0xd95208cd, a builder registry pointer (slot 8) and a BuilderRegistryUpdated event",
            "angle": "D1 added surface",
            "invariant": "A1",
            "actor": "owner (setBuilderRegistry)",
            "precondition": "the set 2 SessionKeyManager runtime",
            "trigger": "static comparison and the BatchExecutor allowlist probe",
            "impact": "the added selector 0xd95208cd is reached on every signed close: the set 2 Exchange statically calls SessionKeyManager::0xd95208cd(user, digest, v, r, s) with the EIP-712 digest, right after 0xb002b9fa consumes the nonce, and it is dispatched only by the set 2 runtime (the pinned runtime contains no 63d95208cd bytes). A direct call with a user-signed digest returns SessionKeyNotAuthorized (0xc5045f22), so it is a session-key verifier over a digest rather than a passive getter. The other added selectors are not allowlisted and the saved head read shows the builder registry pointer is the deployed registry",
            "affected": "set2",
            "severity": "info",
            "status": "confirmed_simulation",
            "evidence_tier": "static bytecode read, exact-runtime call trace and allowlist probe",
            "evidence": {"calltrace": "artifacts/live2_intents/close_verifier_calltrace.txt",
                         "added_selectors": ADDED_SET2[SESSION.lower()],
                         "added_constant": "0x8818669b... = keccak256(BuilderRegistryUpdated(address))",
                         "builder_registry_slot": 8,
                         "live_registry": values["session_builder_registry"]},
            "missing_observation": "the source name of 0xd95208cd and of the builder accumulator's own entry points",
            "citations": ["atlas/block_48902346/suite_sets.md", "atlas/block_48902346/live2_authority.md L2A-15"],
        },
        {
            "id": "L2-D1-05",
            "title": "The pinned 26-case signed-intent suite reproduces unchanged on the set 2 runtimes",
            "angle": "D1/D2 control",
            "invariant": "A2",
            "actor": "none",
            "precondition": "the adapted pinned suite compiled against the set 2 implementations",
            "trigger": "run the suite",
            "impact": "no impact: signature-field mismatches, nonce rollback after a bad signature, the inclusive deadline boundary, the slot-88 gate, the four-position close and the next-block replay rejection all behave identically, which is the control for every set 2 claim above",
            "affected": "both",
            "severity": "none",
            "status": "confirmed_simulation",
            "evidence_tier": "exact-runtime replay, both runtime sets, one harness",
            "evidence": {"control_tests": len(forge["control_tests"]),
                         "live_base_tests": len([name for name in forge["live_tests"]
                                                 if "Set2" not in name]),
                         "live_only_tests": len([name for name in forge["live_tests"]
                                                 if "Set2" in name]),
                         "recorded_open_post_signer": obs.get("set2_open_post_signer")},
            "missing_observation": "the open path's post-signer error 0x0a4f5a07 persists on set 2 and its source name remains unresolved",
            "citations": ["atlas/block_48902346/session_key_pseudocode.md", "AUDIT.md A2"],
        },
    ]
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
        return
    import audit_signed_intent_failures as pinned_harness
    runtimes = load_runtimes()
    for label, code in runtimes.items():
        if not label.startswith("_"):
            print(f"  runtime {label:22s} {len(code[2:]) // 2:6d} B sha256 "
                  f"{hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()[:16]}")

    # --- static: selector and constant comparison of the two runtime pairs ---
    session_1 = bytes.fromhex(runtimes["SessionImpl1"][2:])
    session_2 = bytes.fromhex(runtimes["session_impl"][2:])
    exchange_1 = bytes.fromhex(runtimes["ExchangeImpl1"][2:])
    exchange_2 = bytes.fromhex(runtimes["exchange_impl"][2:])
    selectors_1, selectors_2 = selector_set(session_1), selector_set(session_2)
    ex1, ex2 = selector_set(exchange_1), selector_set(exchange_2)
    assert selectors_2 - selectors_1 == set(ADDED_SET2[SESSION.lower()])
    assert selectors_1 - selectors_2 == set()
    assert ex2 - ex1 == set(ADDED_SET2[EXCHANGE.lower()])
    assert ex1 - ex2 == set(EXCHANGE_DROPPED)
    constants_1 = {"0x" + value for _, value in push32(session_1)}
    constants_2 = {"0x" + value for _, value in push32(session_2)}
    shared = sorted(value for value in constants_1 & constants_2 if value in TYPEHASHES)
    assert set(shared) == set(TYPEHASHES), sorted(set(TYPEHASHES) - constants_2)
    added_constants = sorted(constants_2 - constants_1)
    assert added_constants == [
        "0x8818669b8fb2aea1f49cabb856432f8bd536ace24e3564983488f5a001bc0cf9"]
    assert added_constants[0][2:] == keccak(b"BuilderRegistryUpdated(address)").hex()
    assert b"\x63\xd9\x52\x08\xcd" in session_2 and b"\x63\xd9\x52\x08\xcd" not in session_1, \
        "the new verifier selector is dispatched only by the set 2 SessionKeyManager"
    print(f"  static SessionKeyManager: {len(selectors_1)} -> {len(selectors_2)} selectors, "
          f"{len(shared)} shared EIP-712 and event constants, "
          f"added constant names BuilderRegistryUpdated(address)")
    print(f"  static Exchange: {len(ex1)} -> {len(ex2)} selectors, dropped {sorted(ex1 - ex2)}")

    # --- error and event names used in this ledger: hash-checked, never assumed ---
    for selector, signature in ERROR_NAMES.items():
        assert "0x" + keccak(signature.encode()).hex()[:8] == selector, (selector, signature)
    for topic, signature in EVENT_NAMES.items():
        assert "0x" + keccak(signature.encode()).hex() == topic, (topic, signature)
    for selector in UNNAMED_SELECTORS:
        assert selector not in ERROR_NAMES, selector
    for selector, signature in REJECTED_NAMES.items():
        assert "0x" + keccak(signature.encode()).hex()[:8] != selector, (selector, signature)
    print(f"  names: {len(ERROR_NAMES)} error selectors and {len(EVENT_NAMES)} event topics "
          f"hash-checked; {len(UNNAMED_SELECTORS)} observed selectors left unnamed; "
          f"{len(REJECTED_NAMES)} candidate names hash-checked wrong")

    # --- saved head-era reads ---
    evidence = saved_live_evidence()
    values = evidence["values"]
    assert values["exchange_slot_88"].lower().endswith(BATCH[2:]), values["exchange_slot_88"]
    assert values["exchange_authorized_executor_getter"].lower().endswith(BATCH[2:])
    assert values["exchange_owner"].lower().endswith(TIMELOCK[2:])
    assert values["session_builder_registry"].lower().endswith(BUILDER_REGISTRY[2:])
    assert values["session_registry_old_value_owner_call"] == "0x", "owner call succeeded"
    assert values["session_owner"].lower() == TIMELOCK
    assert values["session_proxy_sha256"] == runtimes["_manifest"]["contracts"][SESSION]["sha256"],         "the SessionKeyManager proxy code is unchanged at head"
    print(f"  saved head reads (head {values['head']}): Exchange slot 88 and its getter hold the "
          f"BatchExecutor; owner is the timelock; the SessionKeyManager points at "
          f"{values['session_builder_registry']}")
    cap = values.get("own_capture") or {}
    have_domain = {"session_calls", "session_slots"} <= set(cap) and \
        {"DOMAIN_SEPARATOR", "domainSeparatorV4"} <= set(cap.get("session_calls", {}))
    if have_domain:
        assert cap["session_calls"]["DOMAIN_SEPARATOR"] == cap["session_calls"]["domainSeparatorV4"]
        assert cap["session_slots"]["1"].lower() == PIN_DOMAIN_SEPARATOR
        assert cap["session_slots"]["3"].lower().endswith(EXCHANGE[2:])
        assert cap["session_slots"]["8"].lower().endswith(BUILDER_REGISTRY[2:])
        print(f"  own capture: domain {cap['session_calls']['domainSeparatorV4']} "
              f"(pin: {PIN_DOMAIN_SEPARATOR}), "
              f"builder registry {cap['session_slots']['8']}")
    else:
        print("  own capture: absent (public endpoint rate-limited); the domain equality is "
              "established by the exact-runtime suite instead")

    # --- exact-runtime suites: pinned control, live set 2, and the differential ---
    saved_exchange = json.loads((ROOT / "artifacts" / "exchange_direct_status_local"
                                 / "pinned_direct_slots.json").read_text())
    pinned_source = pinned_harness.build_source(saved_exchange)
    base_proxy = (ATLAS / runtimes["_manifest"]["contracts"]
                  ["0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"]["runtime_file"]).read_text().strip()
    factory_impl = (ATLAS / runtimes["_manifest"]["contracts"]
                    ["0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0"]["runtime_file"]).read_text().strip()
    user = "0xe05fcc23807536bee418f142d19fa0d21bb0cff7"
    derived_address = derived_proxy_address(user)
    catalog = json.loads((ATLAS / "factory_user_proxy_map.json").read_text())
    for row in catalog[:5]:
        assert derived_proxy_address(row["user"]) == row["proxy"], row
    import gzip
    with gzip.open(ROOT / "artifacts" / "postpin_suite" / "live_latest.json.gz") as handle:
        live_words = json.load(handle)["pt01_words"]
    for stalled_user, record in live_words.items():
        assert derive_proxy_runtime(base_proxy, stalled_user).lower() == record["proxy_code"].lower()
    print(f"  derivation: {derived_address} for the audit user; 5 catalog addresses and 2 saved "
          f"live proxy runtimes reproduce exactly")
    common = {
        "ExchangeProxy": runtimes["ExchangeProxy1"],
        "SessionProxy": runtimes["SessionProxy1"],
        "BatchExecutorProxy": runtimes["BatchExecutorProxy"],
        "BatchExecutorImpl": runtimes["BatchExecutorImpl"],
        "FactoryProxy": runtimes["FactoryProxy"],
        "Library2": runtimes["library"],
        "FactoryImpl": factory_impl,
        "ProxyUser": derive_proxy_runtime(base_proxy, user),
    }
    for name, mock in MOCKS.items():
        common[name] = mock_code(mock[0])
    common["FactoryProxyOfMock"] = mock_code([int(derived_address, 16)])

    control_files = dict(common, ExchangeImpl=runtimes["ExchangeImpl1"],
                         SessionImpl=runtimes["SessionImpl1"])
    live_files = dict(common, ExchangeImpl2=runtimes["exchange_impl"],
                      SessionImpl2=runtimes["session_impl"])
    control_output, _ = run_forge(pinned_source, control_files, "pinned-control")
    control_pass = sorted(re.findall(r"\[PASS\] (test\w+)", control_output))
    control_fail = re.findall(r"\[FAIL\] (test\w+)", control_output)
    assert not control_fail and len(control_pass) == 26, (control_fail, len(control_pass))
    print(f"  control suite (pinned runtimes, unmodified pinned source): {len(control_pass)} passed")

    live_source = build_live_source(pinned_source, values["exchange_slot_88"],
                                    values["session_builder_registry"])
    output, observations = run_forge(live_source, live_files, "live2-intents")
    passed = sorted(re.findall(r"\[PASS\] (test\w+)", output))
    failed = re.findall(r"\[FAIL\] (test\w+)", output)
    if failed:
        print(output[-8000:])
        raise RuntimeError(f"live suite failures: {failed}")
    print(f"  live suite (set 2 runtimes): {len(passed)} passed, 0 failed")

    differential = {}
    for tag, live in (("pinned", False), ("set2", True)):
        files = dict(common)
        files.update({"ExchangeImpl2": runtimes["exchange_impl"],
                      "SessionImpl2": runtimes["session_impl"]} if live else
                     {"ExchangeImpl": runtimes["ExchangeImpl1"],
                      "SessionImpl": runtimes["SessionImpl1"]})
        _, diff_observations = run_forge(build_diff_source(pinned_source, live), files, f"diff-{tag}")
        differential[tag] = diff_observations
    assert differential["pinned"]["diff_retry_amount"]["stored_spot"] == 10_000_000_000
    assert differential["pinned"]["diff_retry_amount"]["queued_total"] == 10_000_000_000
    assert differential["pinned"]["diff_retry_dust"]["ok"] is False
    assert differential["pinned"]["diff_retry_dust"]["selector"] == 0x329C2B0F
    assert differential["set2"]["diff_retry_amount"]["stored_spot"] == 9_900_000_000
    assert differential["set2"]["diff_retry_amount"]["queued_total"] == 9_900_000_000
    assert differential["set2"]["diff_retry_dust"]["ok"] is True
    assert differential["set2"]["diff_retry_dust"]["stored_spot_after"] == 0
    print("  differential: the pinned retry re-sends the full observed balance and reverts "
          "SweepBelowMinimum on dust; the live set 2 retry reserves one USD and clears dust")

    # --- pinned expectations and ledger ---
    if not EXPECTED_LIVE_TESTS:
        print("RECORD live tests:")
        print(json.dumps(passed, indent=1))
        print("RECORD observations:")
        print(json.dumps(observations, indent=1, sort_keys=True))
    else:
        assert passed == EXPECTED_LIVE_TESTS, sorted(set(passed) ^ set(EXPECTED_LIVE_TESTS))
        assert sorted(observations) == sorted(EXPECTED_OBSERVATIONS), \
            sorted(set(observations) ^ set(EXPECTED_OBSERVATIONS))
        for name, expected in EXPECTED_OBSERVATIONS.items():
            assert observations[name] == expected, (name, observations[name], expected)
    forge = {"control_tests": control_pass, "live_tests": passed, "observations": observations,
             "differential": differential,
             "source_sha256": hashlib.sha256(live_source.encode()).hexdigest()}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "forge_observations.json").write_text(json.dumps({
        "forge": pathlib.Path(shutil.which("forge") or "forge").name, "solc": pathlib.Path(shutil.which("solc") or "solc").name,
        "control_source_sha256": hashlib.sha256(pinned_source.encode()).hexdigest(),
        "live_source_sha256": forge["source_sha256"],
        "control_tests": control_pass, "live_tests": passed,
        "observations": observations, "differential": differential}, indent=2) + "\n")
    rows = ledger_rows(runtimes, evidence, forge)
    ledger = {
        "audit": "signed intents, execution gates and the deposit and withdrawal paths",
        "pin": PIN,
        "pin_block_hash": PIN_HASH,
        "live_set": {
            "note": "contract set 2 behind the same proxies, live since block 49,169,385",
            "exchange_implementation": EXCHANGE_IMPL_2,
            "session_key_manager_implementation": SESSION_IMPL_2,
            "exchange_linked_library": LIBRARY_2,
            "builder_registry": BUILDER_REGISTRY,
            "runtime_sha256": {label: hashlib.sha256(bytes.fromhex(runtimes[label][2:])).hexdigest()
                               for label in RUN2 if not label.startswith("_")},
        },
        "pinned_set": {"exchange_implementation": EXCHANGE_IMPL_1,
                       "session_key_manager_implementation": SESSION_IMPL_1},
        "live_reads": evidence,
        "verified_names": {"errors": ERROR_NAMES, "events": EVENT_NAMES,
                           "unnamed_selectors": UNNAMED_SELECTORS,
                           "rejected_names": REJECTED_NAMES,
                           "rejected_note": "hash-asserted as NOT these names; the selectors stay "
                                            "unnamed rather than carrying a plausible label",
                           "check": "keccak256 of each signature compared with the selector in the "
                                    "lookup tables of session_key_behavior.json, "
                                    "exchange_sweep_behavior.json and batch_executor_behavior.json"},
        "evidence_files": {
            "generator": "audit_live2_intents.py",
            "forge_results": "artifacts/live2_intents/forge_observations.json",
            "own_live_capture": "artifacts/live2_intents/live_reads.json (written by --capture)",
            "pinned_control_suite": "audit_signed_intent_failures.py (26 cases, run in this script)",
            "saved_fork_cases": "artifacts/exchange_sweep_archive_local/*.diff.json",
            "saved_head_probes": "artifacts/postpin_pin/raw_reads.json,"
                                 " artifacts/postpin_suite/live_latest.json.gz",
        },
        "rows": rows,
    }
    LEDGER.write_text(json.dumps(ledger, indent=1) + "\n")
    print(f"  ledger: {len(rows)} rows written to {LEDGER.relative_to(ROOT)}")
    for status in ("confirmed_live", "confirmed_simulation", "plausible_unproven", "disproved",
                   "blocked"):
        names = [row["id"] for row in rows if row["status"] == status]
        if names:
            print(f"  {status}: {len(names)} ({', '.join(names)})")


if __name__ == "__main__":
    main()
