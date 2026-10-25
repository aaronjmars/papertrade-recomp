"""Capture and verify a read-only PT-01 preflight against the live Exchange set.

The preflight extends the sweep-family log coverage from the saved live-facts head to a
new head and re-reads every value the recovery sequence depends on. `--capture` reads
live HyperEVM and HyperCore state; the no-argument run re-checks the saved preflight
offline against the live-facts capture, the pinned census and the compiled candidate.
"""

import argparse
import datetime
import decimal
import hashlib
import json
import pathlib

from recovery import live_facts as facts
from recovery.current_rpc import rpc, rpc_call, core, word
from recovery.deploy import address as candidate_address

ROOT = pathlib.Path(__file__).resolve().parents[1]
HERE = pathlib.Path(__file__).resolve().parent
LIVE_FACTS = facts.LIVE_FACTS
OUT = HERE / "preflight_20261022.json"
COMPILED = HERE / "compiled.json"
EXCHANGE = facts.EXCHANGE
TIMELOCK = facts.TIMELOCK
MULTISIG = facts.MULTISIG
PROXY_ADMIN = facts.PROXY_ADMIN
ACTIVE_SLOT = facts.ACTIVE_SLOT


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def capture(path=OUT):
    live = json.loads(LIVE_FACTS.read_text())
    compiled = json.loads(COMPILED.read_text())
    head = rpc("eth_getBlockByNumber", ["latest", False])
    previous = int(live["head"]["number"], 16)
    assert int(head["number"], 16) >= previous
    chunks, logs = facts.log_scan(
        EXCHANGE, facts.SWEEP_TOPICS, live["sweep_log_scan"]["users"],
        previous + 1, int(head["number"], 16))
    implementation = rpc("eth_getStorageAt", [EXCHANGE, facts.IMPLEMENTATION_SLOT, "latest"])
    admin_word = rpc("eth_getStorageAt", [EXCHANGE, facts.ADMIN_SLOT, "latest"])
    proxy_code = rpc("eth_getCode", [EXCHANGE, "latest"])
    created = rpc("eth_call", [{"data": compiled["init_code"]}, "latest"])
    active = rpc("eth_getStorageAt", [EXCHANGE, ACTIVE_SLOT, "latest"])
    governance = {
        "timelock_owner_slot": rpc("eth_getStorageAt", [TIMELOCK, hex(0), "latest"]),
        "timelock_min_delay_word": rpc("eth_getStorageAt", [TIMELOCK, hex(1), "latest"]),
        "multisig_signer_slots": [rpc("eth_getStorageAt", [MULTISIG, hex(index), "latest"])
                                  for index in range(3)],
        "multisig_epoch_word": rpc("eth_getStorageAt", [MULTISIG, hex(3), "latest"]),
        "multisig_transaction_count_word": rpc("eth_getStorageAt", [MULTISIG, hex(4), "latest"]),
        "exchange_owner_call": rpc_call(EXCHANGE, facts.SELECTORS["owner()"])["data"],
        "proxy_admin_owner_call": rpc_call(PROXY_ADMIN, facts.SELECTORS["owner()"])["data"],
    }
    rows = []
    for prior in live["cases"]:
        user, proxy = prior["user"], prior["proxy"]
        arg = "0x" + user[2:].rjust(64, "0")
        code = rpc("eth_getCode", [proxy, "latest"])
        rows.append({
            "user": user,
            "proxy": proxy,
            "pending_call": rpc_call(EXCHANGE, facts.SELECTORS["pendingSweepWord(address)"] + arg[2:])["data"],
            "pending_storage": rpc("eth_getStorageAt", [EXCHANGE, prior["pending_storage_slot"], "latest"]),
            "balance_call": rpc_call(EXCHANGE, facts.SELECTORS["balances(address)"] + arg[2:])["data"],
            "balance_storage": rpc("eth_getStorageAt", [EXCHANGE, prior["balance_storage_slot"], "latest"]),
            "proxy_code_sha256": sha256(bytes.fromhex(code[2:])),
            "spot_precompile": rpc_call("0x0000000000000000000000000000000000000801",
                                        "0x" + proxy[2:].rjust(64, "0") + "00" * 32)["data"],
            "public_core_spot_state": core({"type": "spotClearinghouseState", "user": proxy}),
            "core_ledger_since_live_facts": core({
                "type": "userNonFundingLedgerUpdates",
                "user": proxy,
                "startTime": int(live["head"]["timestamp"], 16) * 1000,
                "endTime": (int(head["timestamp"], 16) + 1) * 1000 - 1,
            }),
        })
    output = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "live_facts": str(LIVE_FACTS.relative_to(ROOT)),
        "live_words": str((LIVE_FACTS.parent / "live_words.json").relative_to(ROOT)),
        "rpc_url": facts.RPC_URL,
        "core_info": facts.CORE_INFO,
        "previous_head": live["head"],
        "head": {key: head[key] for key in ("number", "hash", "timestamp")},
        "implementation_word": implementation,
        "admin_word": admin_word,
        "proxy_code_sha256": sha256(bytes.fromhex(proxy_code[2:])),
        "live_implementation": live["exchange"]["implementation"],
        "candidate": candidate_address(),
        "candidate_code_sha256": compiled["deployed_code_sha256"],
        "candidate_deployment_call_sha256": sha256(bytes.fromhex(created[2:])),
        "candidate_deployment_call_length": (len(created) - 2) // 2,
        "recovery_active_slot": ACTIVE_SLOT,
        "recovery_active_value": active,
        "governance": governance,
        "sweep_log_scan": {
            "address": EXCHANGE,
            "topics": facts.SWEEP_TOPICS,
            "users": live["sweep_log_scan"]["users"],
            "first_block": hex(previous + 1),
            "last_block": head["number"],
            "chunks": chunks,
            "log_count": len(logs),
            "logs": logs,
        },
        "cases": rows,
    }
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    return verify(path)


def verify(path=OUT):
    live = json.loads(LIVE_FACTS.read_text())
    compiled = json.loads(COMPILED.read_text())
    saved = json.loads(path.read_text())
    census = facts.census()
    assert saved["live_facts"] == str(LIVE_FACTS.relative_to(ROOT))
    assert saved["live_words"] == str((LIVE_FACTS.parent / "live_words.json").relative_to(ROOT))
    assert saved["rpc_url"] == facts.RPC_URL and saved["core_info"] == facts.CORE_INFO
    assert saved["previous_head"] == live["head"]
    assert int(saved["head"]["number"], 16) > int(live["head"]["number"], 16)
    assert len(saved["head"]["hash"]) == 66

    manifest = json.loads((facts.ATLAS / "manifest.json").read_text())
    assert saved["proxy_code_sha256"] == manifest["contracts"][EXCHANGE]["sha256"], \
        "the Exchange proxy runtime itself must be unchanged"
    assert saved["admin_word"].lower() == word(PROXY_ADMIN).lower()
    assert saved["implementation_word"].lower() == word(live["exchange"]["implementation"]).lower()
    assert int(saved["implementation_word"], 16) == int(live["exchange"]["implementation"], 16)
    assert saved["candidate"] == candidate_address()
    assert saved["candidate_code_sha256"] == compiled["deployed_code_sha256"]
    assert saved["candidate_deployment_call_sha256"] == compiled["deployed_code_sha256"], \
        "the read-only deployment call must return the compiled runtime"
    assert saved["candidate_deployment_call_length"] == (len(compiled["deployed_code"]) - 2) // 2
    assert int(saved["recovery_active_slot"], 16) == int(live["exchange"]["recovery_active_slot"], 16)
    assert int(saved["recovery_active_value"], 16) == 0

    governance = saved["governance"]
    assert int(governance["timelock_owner_slot"], 16) == int(MULTISIG, 16)
    assert governance["timelock_min_delay_word"] == live["governance"]["timelock_min_delay_word"]
    assert int(governance["timelock_min_delay_word"], 16) == 86_400
    assert governance["multisig_signer_slots"] == live["governance"]["multisig_signer_slots"]
    assert int(governance["multisig_epoch_word"], 16) >= int(live["governance"]["multisig_epoch_word"], 16)
    assert int(governance["multisig_transaction_count_word"], 16) >= \
        int(live["governance"]["multisig_transaction_count_word"], 16)
    assert int(governance["exchange_owner_call"], 16) == int(TIMELOCK, 16)
    assert int(governance["proxy_admin_owner_call"], 16) == int(TIMELOCK, 16)

    scan = saved["sweep_log_scan"]
    assert scan["topics"] == facts.SWEEP_TOPICS == live["sweep_log_scan"]["topics"]
    assert scan["users"] == live["sweep_log_scan"]["users"]
    assert scan["log_count"] == 0 and scan["logs"] == []
    assert int(scan["chunks"][0]["fromBlock"], 16) == int(live["head"]["number"], 16) + 1
    assert int(scan["chunks"][-1]["toBlock"], 16) == int(saved["head"]["number"], 16)
    for index, chunk in enumerate(scan["chunks"]):
        assert chunk["logs"] == []
        assert int(chunk["toBlock"], 16) - int(chunk["fromBlock"], 16) + 1 <= facts.BLOCK_RANGE
        if index:
            assert int(chunk["fromBlock"], 16) == int(scan["chunks"][index - 1]["toBlock"], 16) + 1

    assert len(saved["cases"]) == len(census["cases"]) == 2
    spot_total = decimal.Decimal(0)
    for prior, row in zip(census["cases"], saved["cases"]):
        assert row["user"] == prior["user"] and row["proxy"] == prior["proxy"]
        assert row["pending_call"].lower() == row["pending_storage"].lower() == prior["pending_word"].lower()
        assert row["balance_call"].lower() == row["balance_storage"].lower() == "0x" + "00" * 32
        assert row["proxy_code_sha256"] == prior["derived_runtime_sha256"]
        assert row["core_ledger_since_live_facts"] == []
        output = row["spot_precompile"]
        assert len(output) == 194 and output[66:194] == "00" * 64
        raw = int(output[2:66], 16)
        assert raw == int(prior["pending_word"], 16) & ((1 << 64) - 1)
        usdc = [entry for entry in row["public_core_spot_state"]["balances"]
                if entry["coin"] == "USDC" and entry["token"] == 0]
        assert len(usdc) == 1
        assert raw == int(decimal.Decimal(usdc[0]["total"]) * 10**8)
        spot_total += decimal.Decimal(usdc[0]["total"])
    assert spot_total == decimal.Decimal("62.150916")
    return {
        "head_block": int(saved["head"]["number"], 16),
        "captured_at_utc": saved["captured_at_utc"],
        "pending_count": 2,
        "spot_usdc": str(spot_total),
        "live_implementation": saved["live_implementation"],
        "candidate": saved["candidate"],
        "owner": TIMELOCK,
        "governance_delay_seconds": int(governance["timelock_min_delay_word"], 16),
        "multisig_transaction_count": int(governance["multisig_transaction_count_word"], 16),
        "deployment_simulated": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="refresh live HyperEVM, HyperCore and log-range reads")
    parser.add_argument("--out", type=pathlib.Path, default=OUT)
    args = parser.parse_args()
    print(json.dumps(capture(args.out) if args.capture else verify(args.out), indent=2))