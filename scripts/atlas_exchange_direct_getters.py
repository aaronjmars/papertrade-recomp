#!/usr/bin/env python3
"""Verify live Exchange direct storage getters and balance mapping."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_direct_getters"
SAVED = ARTIFACTS / "pinned_getters.json"
OUT = ATLAS / "exchange_direct_getters_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN = 48902346
KECCAK = Keccak()
LOW128 = (1 << 128) - 1
LOW160 = (1 << 160) - 1
DIRECT = {
    "0x01ad056f": ("totalLockedMargin()", 22, "high128"),
    "0x0b826190": ("sessionKeyManager()", 29, "address_shift8"),
    "0x13dd495b": ("authorizedExecutor()", 88, "address"),
    "0x53ac4b66": ("totalQueued()", 18, "uint256"),
    "0x61d027b3": ("treasury()", 14, "uint256"),
    "0x7d004aeb": ("devFeeAccumulator()", 26, "high128"),
    "0x7dc0d1d0": ("oracle()", 2, "address"),
    "0x899346c7": ("nextPositionId()", 11, "uint256"),
    "0x96523644": ("queueHead()", 16, "uint256"),
    "0x9d47d4d3": ("authorizedKeeper()", 89, "address"),
    "0xa69a2ad1": ("totalBalances()", 22, "low128"),
    "0xafdf6702": ("stakerFeeAccumulator()", 26, "low128"),
    "0xc10f1a75": ("proxyFactory()", 30, "address"),
    "0xcbeb5f3d": ("devFeeRecipient()", 38, "address"),
    "0xec0bdcfc": ("collateralScale()", 3, "uint256"),
    "0xed410ee1": ("paperTokenomics()", 6, "address"),
}
BALANCE_SELECTOR = "0x27e235e3"
BALANCE_SIGNATURE = "balances(address)"


def balance_slot(user):
    return "0x" + KECCAK(int(user, 16).to_bytes(32, "big") + (9).to_bytes(32, "big")).hex()


def capture():
    from atlas_tokenomics import rpc

    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]

    def call(selector, user=None):
        data = selector if user is None else selector + int(user, 16).to_bytes(32, "big").hex()
        return rpc(url, "eth_call", [{"to": PROXY, "data": data}, hex(PIN)])

    slots = sorted({slot for _, slot, _ in DIRECT.values()})
    storage = {str(slot): rpc(url, "eth_getStorageAt", [PROXY, hex(slot), hex(PIN)]) for slot in slots}
    getters = {selector: call(selector) for selector in DIRECT}
    credits = json.loads((ATLAS / "exchange_staking_credit_behavior.json").read_text())
    users = []
    for tx in credits["transactions"]:
        for row in tx["recipient_balances"]:
            if row["user"] not in users:
                users.append(row["user"])
            if len(users) == 3:
                break
        if len(users) == 3:
            break
    assert len(users) == 3
    balances = []
    for user in users:
        slot = balance_slot(user)
        balances.append({"user": user, "slot": slot,
                         "storage_value": rpc(url, "eth_getStorageAt", [PROXY, slot, hex(PIN)]),
                         "getter_output": call(BALANCE_SELECTOR, user)})
    word29 = int(storage["29"], 16)
    alternate_manager = int("0x1111111111111111111111111111111111111111", 16)
    slot29 = "0x" + (29).to_bytes(32, "big").hex()
    packed = {}
    for name, value in (("pause_on", word29 | 1),
                        ("alternate_manager", (word29 & ~(LOW160 << 8)) | (alternate_manager << 8))):
        override = {PROXY: {"stateDiff": {slot29: "0x" + value.to_bytes(32, "big").hex()}}}
        params = [{"to": PROXY, "data": "0x0b826190"}, hex(PIN), override]
        pause_params = [{"to": PROXY, "data": "0x53e23e2e"}, hex(PIN), override]
        packed[name] = {"storage_word": override[PROXY]["stateDiff"][slot29],
                        "manager_output": rpc(url, "eth_call", params),
                        "pause_output": rpc(url, "eth_call", pause_params)}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                 "direct_storage": storage, "direct_getters": getters,
                                 "balance_getters": balances, "packed_slot29_overrides": packed}, indent=2) + "\n")


def decode(word, kind):
    if kind == "address":
        return word & LOW160
    if kind == "address_shift8":
        return (word >> 8) & LOW160
    if kind == "low128":
        return word & LOW128
    if kind == "high128":
        return word >> 128
    assert kind == "uint256"
    return word


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert saved["pin_block"] == manifest["block"] == PIN
    assert saved["pin_hash"] == manifest["block_hash"]
    traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]
    assert traces["target"] == PROXY
    by_selector = {row["selector"]: row for row in traces["views"]}
    older = json.loads((ATLAS / "exchange_storage_words.json").read_text())
    assert older["block_hash"] == manifest["block_hash"]
    signatures = {}
    rows = []
    for selector, (signature, slot, kind) in DIRECT.items():
        assert "0x" + KECCAK(signature.encode()).hex()[:8] == selector
        assert by_selector[selector]["direct_slots"] == [slot] and not by_selector[selector]["failed"]
        raw = int(saved["direct_storage"][str(slot)], 16)
        actual = int(saved["direct_getters"][selector], 16)
        assert actual == decode(raw, kind), (selector, actual, raw)
        if str(slot) in older["slots"]:
            assert saved["direct_storage"][str(slot)] == older["slots"][str(slot)]
        signatures[selector] = signature
        rows.append({"selector": selector, "signature": signature, "storage_slot": slot,
                     "field": kind, "raw_word": saved["direct_storage"][str(slot)],
                     "getter_output": saved["direct_getters"][selector]})
    assert "0x" + KECCAK(BALANCE_SIGNATURE.encode()).hex()[:8] == BALANCE_SELECTOR
    assert by_selector[BALANCE_SELECTOR]["mapping_matches"][0]["base_slot"] == 9
    balances = []
    for row in saved["balance_getters"]:
        assert row["slot"] == balance_slot(row["user"])
        assert int(row["storage_value"], 16) == int(row["getter_output"], 16)
        balances.append(row)
    assert len(balances) == 3 and any(int(row["getter_output"], 16) > 0 for row in balances)
    signatures[BALANCE_SELECTOR] = BALANCE_SIGNATURE
    raw29 = int(saved["direct_storage"]["29"], 16)
    packed = saved["packed_slot29_overrides"]
    assert set(packed) == {"pause_on", "alternate_manager"}
    pause_on = packed["pause_on"]
    assert int(pause_on["storage_word"], 16) == raw29 | 1
    assert int(pause_on["manager_output"], 16) == decode(raw29, "address_shift8")
    assert int(pause_on["pause_output"], 16) == 1
    alternate = packed["alternate_manager"]
    alternate_word = int(alternate["storage_word"], 16)
    assert alternate_word & 255 == raw29 & 255
    assert int(alternate["manager_output"], 16) == decode(alternate_word, "address_shift8")
    assert int(alternate["manager_output"], 16) == int("0x1111111111111111111111111111111111111111", 16)
    assert int(alternate["pause_output"], 16) == bool(raw29 & 255)
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": signatures,
            "direct_slot_getters": rows, "balance_mapping_samples": balances,
            "packed_slot29_override_count": len(packed),
            "checked_behavior": "sixteen hash-checked direct and packed storage views plus three pinned user balance mapping reads",
            "limitations": ["Getter names have exact selector hashes and pinned storage behavior, but original Solidity source is unavailable.",
                            "A single pinned state cannot prove every future value or unusual caller branch.",
                            "The treasury getter returns a numeric accounting amount in this runtime; its exact source integer width is not established."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange direct getters: {len(result['selector_reconstructions'])} signatures, "
          f"{len(result['balance_mapping_samples'])} balance mapping checks")
