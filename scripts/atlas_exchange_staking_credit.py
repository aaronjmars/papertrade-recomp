#!/usr/bin/env python3
"""Reconcile historical Staking-to-Exchange reward credits with saved state diffs."""

import argparse
import collections
import glob
import json
import os
import pathlib

from atlas_exchange_library import all_calls, canonical_trace
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
SELECTOR = "0xe53e3de6"
SIGNATURE = "creditStakingReward(address,uint256)"
EVENT = "StakingRewardCredited(address,uint256)"
TOPIC = "0xe7fd56edb8bf641db0dc0a89a9d7d3a10da1fedab015ab0c51f1c418d2bc15b0"
TXS = (
    "0x0f15e1a5d5bcaf5764df51439680fa8b3f748b47240d5c89c31be8d487a49a90",
    "0x44d34a2ac0a36042f6ecd850ebc63f738b708d0a27d5993f8b7d9250e77c88cb",
    "0x644027ab726d170cb459be3154fcaf2b74f52874484a45b781d268736f3c6c43",
    "0x726340c233749d1bdb8bea903e4c8cc6ab17923527ed51abc77c91f0e7b3e22e",
    "0x94192d521e62d362196076f7b0e03ea403aca75f4ec40257ef6ce259bf563a4d",
    "0xac4e0883756cb4912c51f20d7d8ce84d798ccdda4e455c2c6242af5a8f139009",
    "0xe3a26c590c7b0be9e26e25b2e8fdf797be800b92131c229b5148c7405f69e33d",
)
KECCAK = Keccak()
PROBES = ROOT / "artifacts" / "exchange_staking_credit" / "pinned_probes.json"


def artifact(tx, suffix):
    paths = glob.glob(str(ROOT / "artifacts" / "*" / f"{tx}.{suffix}.json"))
    assert paths, (tx, suffix)
    values = [json.loads(pathlib.Path(path).read_text()) for path in paths]
    assert all(value == values[0] for value in values), (tx, suffix)
    return values[0]


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def balance_slot(address):
    return "0x" + KECCAK(int(address, 16).to_bytes(32, "big") + (9).to_bytes(32, "big")).hex()


def storage_delta(diff, address):
    slot = balance_slot(address)
    pre = diff["pre"].get(EXCHANGE, {}).get("storage", {})
    post = diff["post"].get(EXCHANGE, {}).get("storage", {})
    assert slot in pre, (address, slot)
    return int(post.get(slot, "0x0"), 16) - int(pre[slot], 16), slot


def capture():
    from atlas_tokenomics import rpc

    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    block = rpc(url, "eth_getBlockByNumber", [hex(manifest["block"]), False])
    assert block["hash"] == manifest["block_hash"]
    sample = canonical_trace(TXS[1])
    user = next(words("0x" + call["input"][10:])[0] for call, _ in all_calls(sample)
                if call.get("to", "").lower() == EXCHANGE and call.get("input", "")[:10] == SELECTOR)
    cases = (("staking_one", STAKING, 1), ("staking_zero", STAKING, 0),
             ("staking_huge", STAKING, 1 << 255),
             ("outsider", "0x1111111111111111111111111111111111111111", 1))
    rows = []
    for name, sender, amount in cases:
        data = SELECTOR + user.to_bytes(32, "big").hex() + amount.to_bytes(32, "big").hex()
        request = {"from": sender, "to": EXCHANGE, "data": data}
        trace = rpc(url, "debug_traceCall", [request, hex(manifest["block"]),
                                             {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        assert len(trace.get("calls", [])) == 1
        child = trace["calls"][0]
        assert child["to"].lower() == IMPLEMENTATION and child["type"] == "DELEGATECALL"
        diff = None
        if not trace.get("error"):
            state = rpc(url, "debug_traceCall", [request, hex(manifest["block"]),
                                                 {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            diff = {side: state.get(side, {}).get(EXCHANGE, {}).get("storage", {}) for side in ("pre", "post")}
        rows.append({"name": name, "from": sender, "recipient": f"0x{user:040x}",
                     "amount": str(amount), "input": data, "error": trace.get("error"),
                     "revert_data": trace.get("output", "0x"), "logs": child.get("logs", []),
                     "exchange_storage_diff": diff})
    PROBES.parent.mkdir(parents=True, exist_ok=True)
    PROBES.write_text(json.dumps({"block": manifest["block"], "block_hash": manifest["block_hash"],
                                  "cases": rows}, indent=2) + "\n")


def verify_probes(manifest):
    saved = json.loads(PROBES.read_text())
    assert saved["block"] == manifest["block"] and saved["block_hash"] == manifest["block_hash"]
    cases = {row["name"]: row for row in saved["cases"]}
    assert set(cases) == {"staking_one", "staking_zero", "staking_huge", "outsider"}
    assert all(row["input"] == SELECTOR + int(row["recipient"], 16).to_bytes(32, "big").hex()
               + int(row["amount"]).to_bytes(32, "big").hex() for row in cases.values())
    one = cases["staking_one"]
    assert one["from"] == STAKING and one["error"] is None and len(one["logs"]) == 1
    log = one["logs"][0]
    assert log["topics"] == [TOPIC, "0x" + int(one["recipient"], 16).to_bytes(32, "big").hex()]
    assert words(log["data"]) == [1]
    diff = {side: {EXCHANGE: {"storage": one["exchange_storage_diff"][side]}}
            for side in ("pre", "post")}
    assert storage_delta(diff, STAKING)[0] == -1
    assert storage_delta(diff, one["recipient"])[0] == 1
    zero = cases["staking_zero"]
    assert zero["from"] == STAKING and zero["error"] is None and zero["logs"] == []
    assert zero["exchange_storage_diff"] == {"pre": {}, "post": {}}
    assert cases["staking_huge"]["error"] == cases["outsider"]["error"] == "execution reverted"
    assert cases["staking_huge"]["revert_data"] == "0xf4d678b8"
    assert cases["outsider"]["revert_data"] == "0x538ccdfd"
    assert all(cases[name]["logs"] == [] and cases[name]["exchange_storage_diff"] is None
               for name in ("staking_huge", "outsider"))
    return saved


def build():
    assert "0x" + KECCAK(SIGNATURE.encode()).hex()[:8] == SELECTOR
    assert "0x" + KECCAK(EVENT.encode()).hex() == TOPIC
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == 48902346
    probes = verify_probes(manifest)
    withdrawal = json.loads((ATLAS / "exchange_core_withdrawal_behavior.json").read_text())
    mixed = next(row for row in withdrawal["transactions"] if row["tx"] == TXS[0])
    rows = []
    for tx in TXS:
        trace = canonical_trace(tx)
        receipt = artifact(tx, "receipt")
        diff = artifact(tx, "state_diff")
        assert receipt["status"] == "0x1" and int(receipt["blockNumber"], 16) <= manifest["block"]
        calls = []
        for call, parent in all_calls(trace):
            if call.get("to", "").lower() != EXCHANGE or call.get("input", "")[:10] != SELECTOR:
                continue
            assert call["type"] == "CALL" and call["from"].lower() == STAKING
            assert call.get("error") is None and call.get("output", "0x") == "0x"
            assert len(call.get("calls", [])) == 1
            child = call["calls"][0]
            assert child["type"] == "DELEGATECALL" and child["to"].lower() == IMPLEMENTATION
            assert child["input"] == call["input"] and child.get("error") is None
            args = words("0x" + call["input"][10:])
            assert len(args) == 2 and args[0] < 1 << 160 and args[1] > 0
            calls.append((f"0x{args[0]:040x}", args[1]))
        assert calls, tx
        events = []
        for log in receipt["logs"]:
            if log["address"].lower() != EXCHANGE or log["topics"][0].lower() != TOPIC:
                continue
            assert len(log["topics"]) == 2 and len(words(log["data"])) == 1
            assert int(log["topics"][1], 16) < 1 << 160
            events.append((f"0x{int(log['topics'][1], 16):040x}", words(log["data"])[0]))
        assert calls == events, (tx, calls, events)
        total = sum(amount for _, amount in calls)
        staking_delta, staking_slot = storage_delta(diff, STAKING)
        assert staking_delta == -total, (tx, staking_delta, total)
        credits = collections.Counter()
        for user, amount in calls:
            credits[user] += amount
        recipients = []
        for user, amount in sorted(credits.items()):
            actual, slot = storage_delta(diff, user)
            same_tx_withdrawal = int(mixed["event_internal_debit"]) if tx == TXS[0] and user == mixed["user"] else 0
            assert actual == amount - same_tx_withdrawal, (tx, user, actual, amount, same_tx_withdrawal)
            recipients.append({"user": user, "slot": slot, "credited": str(amount),
                               "same_tx_withdrawal": str(same_tx_withdrawal), "observed_delta": str(actual)})
        rows.append({"tx": tx, "block": int(receipt["blockNumber"], 16),
                     "call_count": len(calls), "event_count": len(events),
                     "total_credited": str(total), "staking_balance_slot": staking_slot,
                     "staking_balance_delta": str(staking_delta),
                     "calls": [{"user": user, "amount": str(amount)} for user, amount in calls],
                     "recipient_balances": recipients})
    assert len(rows) == 7 and sum(row["call_count"] for row in rows) == 27
    return {"pin_block": manifest["block"], "block_hash": manifest["block_hash"],
            "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION, "staking_proxy": STAKING,
            "selector_reconstructions": {SELECTOR: SIGNATURE},
            "event_catalog": [{"topic0": TOPIC, "reconstructed_signature": EVENT,
                               "status": "observed_historical_topic"}],
            "historical_transaction_count": len(rows), "historical_call_count": 27,
            "read_only_probe_count": len(probes["cases"]),
            "probe_results": {row["name"]: {"error": row["error"], "revert_data": row["revert_data"],
                                           "log_count": len(row["logs"])} for row in probes["cases"]},
            "transactions": rows,
            "checked_behavior": ["all historical calls originate from the Staking proxy", "each call delegates to the pinned Exchange implementation", "call arguments match StakingRewardCredited logs in order", "Staking balance at mapping base 9 falls by the sum of credits", "recipient balances at mapping base 9 rise by each credit, adjusted for one same-transaction signed withdrawal", "pinned read-only probes verify one-unit transfer, zero-amount no-op, outsider rejection, and overdraw rejection"],
            "limitations": ["Historical transactions cover only successful positive credits; boundary branches use read-only simulations.", "The caller and balance error selectors are checked as raw revert bytes; their source names remain unverified for this function.", "The public name is hash-matched and behavior-backed but original Solidity source is unavailable."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    (ATLAS / "exchange_staking_credit_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange staking credit: {result['historical_call_count']} calls in {result['historical_transaction_count']} transactions verified")
