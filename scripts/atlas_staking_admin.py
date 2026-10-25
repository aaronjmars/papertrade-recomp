#!/usr/bin/env python3
"""Verify Staking owner and executor setters against history and pinned probes."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_exchange_library import all_calls, canonical_trace

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "staking"
OUT = ATLAS / "staking_admin_behavior.json"
PROBES = ARTIFACTS / "pinned_admin_probes.json"
PROXY = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
IMPLEMENTATION = "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15"
OWNER_BEFORE = "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
OWNER_PIN = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x1111111111111111111111111111111111111111"
PIN = 48902346
KECCAK = Keccak()
SETTERS = {
    "0xd188c049": {"signature": "setAuthorizedExecutor(address)", "slot": 16,
                   "event": "AuthorizedExecutorUpdated(address)",
                   "tx": "0x271fae19ee96703d8ffaab2bb72ce03f167fb7d8fb866bab34c8ed35f3b19d8d"},
    "0xf2fde38b": {"signature": "transferOwnership(address)", "slot": 15,
                   "event": "OwnerUpdated(address)",
                   "tx": "0x4391f966aa09e883317bc3970e4160e9e6971d7c6f6760c40c3635a1d1298645"},
}


def slot_key(slot):
    return "0x" + slot.to_bytes(32, "big").hex()


def calldata(selector, address):
    return selector + int(address, 16).to_bytes(32, "big").hex()


def capture():
    from atlas_tokenomics import rpc

    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    cases = (("executor_outsider", "0xd188c049", OUTSIDER, OUTSIDER),
             ("executor_zero", "0xd188c049", OWNER_PIN, "0x" + "0" * 40),
             ("owner_outsider", "0xf2fde38b", OUTSIDER, OUTSIDER),
             ("owner_zero", "0xf2fde38b", OWNER_PIN, "0x" + "0" * 40))
    rows = []
    for name, selector, sender, arg in cases:
        request = {"from": sender, "to": PROXY, "data": calldata(selector, arg)}
        trace = rpc(url, "debug_traceCall", [request, hex(PIN),
                                               {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        assert len(trace.get("calls", [])) == 1
        child = trace["calls"][0]
        assert child["type"] == "DELEGATECALL" and child["to"].lower() == IMPLEMENTATION
        storage = None
        if trace.get("error") is None:
            diff = rpc(url, "debug_traceCall", [request, hex(PIN),
                                                 {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            storage = {side: diff.get(side, {}).get(PROXY, {}).get("storage", {}) for side in ("pre", "post")}
        rows.append({"name": name, "selector": selector, "from": sender, "argument": arg,
                     "input": request["data"], "error": trace.get("error"),
                     "revert_data": trace.get("output", "0x"),
                     "logs": child.get("logs", []), "staking_storage_diff": storage})
    PROBES.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                  "cases": rows}, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN
    rows = []
    signatures = {}
    for selector, item in SETTERS.items():
        assert "0x" + KECCAK(item["signature"].encode()).hex()[:8] == selector
        topic = "0x" + KECCAK(item["event"].encode()).hex()
        tx = item["tx"]
        root = canonical_trace(tx)
        receipt = json.loads((ROOT / "artifacts" / "historical" / f"{tx}.receipt.json").read_text())
        diff = json.loads((ROOT / "artifacts" / "historical" / f"{tx}.state_diff.json").read_text())
        assert receipt["status"] == "0x1" and int(receipt["blockNumber"], 16) <= PIN
        calls = [call for call, _ in all_calls(root)
                 if call.get("to", "").lower() == PROXY and call.get("input", "")[:10] == selector]
        assert len(calls) == 1
        call = calls[0]
        assert call["type"] == "CALL" and call["from"].lower() == OWNER_BEFORE
        assert len(call.get("calls", [])) == 1
        child = call["calls"][0]
        assert child["type"] == "DELEGATECALL" and child["to"].lower() == IMPLEMENTATION
        assert child["input"] == call["input"] and child.get("error") is None
        argument = int(call["input"][10:], 16)
        assert argument < 1 << 160 and argument != 0
        logs = [log for log in receipt["logs"] if log["address"].lower() == PROXY and log["topics"][0].lower() == topic]
        assert len(logs) == 1 and logs[0]["topics"] == [topic, "0x" + argument.to_bytes(32, "big").hex()]
        assert logs[0]["data"] == "0x"
        slot = slot_key(item["slot"])
        pre = int(diff["pre"][PROXY]["storage"][slot], 16)
        post = int(diff["post"][PROXY]["storage"][slot], 16)
        assert pre & ((1 << 160) - 1) == (0 if item["slot"] == 16 else int(OWNER_BEFORE, 16))
        assert post & ((1 << 160) - 1) == argument
        assert pre >> 160 == post >> 160
        signatures[selector] = item["signature"]
        rows.append({"tx": tx, "block": int(receipt["blockNumber"], 16), "selector": selector,
                     "signature": item["signature"], "caller": OWNER_BEFORE,
                     "new_address": f"0x{argument:040x}", "storage_slot": item["slot"],
                     "pre_word": hex(pre), "post_word": hex(post),
                     "event_topic": topic})
    saved = json.loads(PROBES.read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert len(saved["cases"]) == 4
    probe_rows = []
    for probe in saved["cases"]:
        selector = probe["selector"]
        assert selector in SETTERS and probe["input"] == calldata(selector, probe["argument"])
        if probe["name"].endswith("outsider"):
            assert probe["from"] == OUTSIDER and probe["error"] == "execution reverted"
            assert probe["revert_data"] == "0x30cd7471" and probe["logs"] == []
            assert probe["staking_storage_diff"] is None
        else:
            assert probe["from"] == OWNER_PIN and int(probe["argument"], 16) == 0
            assert probe["error"] is None and len(probe["logs"]) == 1
            assert probe["logs"][0]["topics"] == ["0x" + KECCAK(SETTERS[selector]["event"].encode()).hex(),
                                                     "0x" + "0" * 64]
            assert probe["logs"][0]["data"] == "0x"
            slot = slot_key(SETTERS[selector]["slot"])
            storage = probe["staking_storage_diff"]
            pre = int(storage["pre"][slot], 16)
            post = int(storage["post"].get(slot, "0x0"), 16)
            assert pre & ((1 << 160) - 1) != 0 and post & ((1 << 160) - 1) == 0
            assert pre >> 160 == post >> 160
        probe_rows.append({"name": probe["name"], "selector": selector,
                           "error": probe["error"], "revert_data": probe["revert_data"],
                           "log_count": len(probe["logs"])})
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "staking_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": signatures,
            "historical_transactions": rows, "read_only_probes": probe_rows,
            "checked_behavior": "owner-only address setters, slot-15 owner and slot-16 executor low-160-bit writes, indexed update events, zero-address acceptance at pin",
            "limitations": ["The zero-address successes are read-only simulations, not historical configuration changes.",
                            "These samples do not prove behavior after setting owner to zero or all possible input states.",
                            "Original Solidity source is unavailable; names are exact selector hashes backed by observed behavior."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("Staking admin: 2 historical setters and 4 pinned probes verified")
