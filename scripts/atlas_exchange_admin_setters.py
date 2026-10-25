#!/usr/bin/env python3
"""Verify seven Exchange owner setters, storage fields, events, and access guards."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_admin_setters"
SAVED = ARTIFACTS / "pinned_setters.json"
OUT = ATLAS / "exchange_admin_setters_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x" + "33" * 20
NEW = "0x" + "11" * 20
ZERO = "0x" + "00" * 20
PIN = 48902346
KECCAK = Keccak()
LOW160 = (1 << 160) - 1
SETTERS = {
    "0x837fa3fd": ("setSessionKeyManager(address)", 29, 8, "SessionKeyManagerUpdated(address)"),
    "0x86d506db": ("changeDevFeeAddress(address)", 38, 0, "DevFeeRecipientUpdated(address)"),
    "0xa0bf0f75": ("setPaperTokenomics(address)", 6, 0, "PaperTokenomicsUpdated(address)"),
    "0xd188c049": ("setAuthorizedExecutor(address)", 88, 0, "AuthorizedExecutorUpdated(address)"),
    "0xefc1bd46": ("setAuthorizedKeeper(address)", 89, 0, "AuthorizedKeeperUpdated(address)"),
    "0xfbddd751": ("setProxyFactory(address)", 30, 0, "ProxyFactoryUpdated(address)"),
    "0xf2fde38b": ("transferOwnership(address)", 0, 16, "OwnerUpdated(address)"),
}


def storage_key(slot):
    return "0x" + slot.to_bytes(32, "big").hex()


def all_logs(node):
    yield from node.get("logs", [])
    for child in node.get("calls", []):
        yield from all_logs(child)


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    slots = sorted({slot for _, slot, _, _ in SETTERS.values()})
    words = {str(slot): rpc(url, "eth_getStorageAt", [PROXY, hex(slot), hex(PIN)]) for slot in slots}
    probes = {}
    for selector in SETTERS:
        cases = {}
        for name, sender, address in (("owner_new", OWNER, NEW),
                                      ("outsider_new", OUTSIDER, NEW),
                                      ("owner_zero", OWNER, ZERO)):
            call = {"from": sender, "to": PROXY,
                    "data": selector + int(address, 16).to_bytes(32, "big").hex(),
                    "gas": "0x1000000"}
            trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                       {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
            entry = {"call": trace}
            if name != "outsider_new":
                entry["diff"] = rpc(url, "debug_traceCall", [call, hex(PIN),
                                  {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            cases[name] = entry
        probes[selector] = cases
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin_block": PIN, "block_hash": header["hash"],
                                 "storage_words": words, "probes": probes}, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert saved["pin_block"] == manifest["block"] == PIN
    assert saved["block_hash"].lower() == manifest["block_hash"]
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[IMPLEMENTATION]
    runtime_selectors = {row["selector"] for row in catalog["functions"]}
    existing = json.loads((ATLAS / "exchange_direct_getters_behavior.json").read_text())
    direct_slots = {row["storage_slot"]: row["raw_word"] for row in existing["direct_slot_getters"]}
    assert saved["storage_words"]["29"] == direct_slots[29]
    assert saved["storage_words"]["38"] == direct_slots[38]
    assert saved["storage_words"]["6"] == direct_slots[6]
    assert saved["storage_words"]["88"] == direct_slots[88]
    assert saved["storage_words"]["89"] == direct_slots[89]
    assert saved["storage_words"]["30"] == direct_slots[30]
    assert (int(saved["storage_words"]["0"], 16) >> 16) & LOW160 == int(OWNER, 16)
    assert json.loads((ATLAS / "exchange_pause_behavior.json").read_text())["owner_at_pin"] == OWNER
    assert "0x" + KECCAK(b"NotOwner()").hex()[:8] == "0x30cd7471"
    historical_events = {}
    topics = {"0x" + KECCAK(event.encode()).hex() for _, _, _, event in SETTERS.values()}
    for receipt_path in (ROOT / "artifacts" / "historical").glob("*.receipt.json"):
        receipt = json.loads(receipt_path.read_text())
        for log in receipt.get("logs", []):
            if log["address"].lower() == PROXY and log["topics"][0] in topics:
                historical_events.setdefault(log["topics"][0], []).append({
                    "tx": receipt["transactionHash"], "block": int(receipt["blockNumber"], 16)})
    names = {}
    events = []
    rows = []
    historical_rows = []
    for selector, (signature, slot, shift, event_signature) in SETTERS.items():
        assert selector in runtime_selectors
        assert "0x" + KECCAK(signature.encode()).hex()[:8] == selector
        topic = "0x" + KECCAK(event_signature.encode()).hex()
        names[selector] = signature
        cases = saved["probes"][selector]
        assert set(cases) == {"owner_new", "outsider_new", "owner_zero"}
        old = int(saved["storage_words"][str(slot)], 16)
        expected_new = (old & ~(LOW160 << shift)) | (int(NEW, 16) << shift)
        expected_zero = old & ~(LOW160 << shift)
        checked = {}
        for name, expected_address, expected_word in (("owner_new", NEW, expected_new),
                                                       ("owner_zero", ZERO, expected_zero)):
            case = cases[name]
            assert not case["call"].get("error")
            logs = list(all_logs(case["call"]))
            assert len(logs) == 1 and logs[0]["address"].lower() == PROXY
            assert logs[0]["topics"] == [topic, "0x" + int(expected_address, 16).to_bytes(32, "big").hex()]
            assert logs[0]["data"] == "0x"
            diff = case["diff"]
            pre = diff.get("pre", {}).get(PROXY, {}).get("storage", {})
            post = diff.get("post", {}).get(PROXY, {}).get("storage", {})
            key = storage_key(slot)
            if old != expected_word:
                assert int(pre.get(key, "0x0"), 16) == old
            assert set(post) <= {key}
            assert int(post.get(key, "0x0"), 16) == expected_word
            checked[name] = {"new_address": expected_address, "post_word": "0x" + expected_word.to_bytes(32, "big").hex(),
                             "topic0": topic, "indexed_address": expected_address}
        outsider = cases["outsider_new"]["call"]
        assert outsider.get("error") == "execution reverted"
        assert outsider.get("output") == "0x30cd7471"
        assert not list(all_logs(outsider))
        rows.append({"selector": selector, "signature": signature, "storage_slot": slot,
                     "address_shift_bits": shift, "old_word": saved["storage_words"][str(slot)],
                     "owner_new": checked["owner_new"], "owner_zero": checked["owner_zero"],
                     "outsider_error": "NotOwner()"})
        matching = historical_events.get(topic, [])
        assert len(matching) == 1
        tx = matching[0]["tx"]
        historical_root = ROOT / "artifacts" / "historical" / tx
        calls = json.loads((Path(str(historical_root) + ".calls.json")).read_text())
        receipt = json.loads((Path(str(historical_root) + ".receipt.json")).read_text())
        state = json.loads((Path(str(historical_root) + ".state_diff.json")).read_text())
        def all_calls(node):
            yield node
            for child in node.get("calls", []):
                yield from all_calls(child)
        contract_calls = [node for node in all_calls(calls) if node.get("to", "").lower() == PROXY
                          and node.get("input", "").startswith(selector)]
        assert len(contract_calls) == 1
        historical_arg = int(contract_calls[0]["input"][10:74], 16)
        assert contract_calls[0]["from"].lower() == "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
        receipt_logs = [log for log in receipt["logs"] if log["address"].lower() == PROXY
                        and log["topics"][0] == topic]
        assert len(receipt_logs) == 1
        assert receipt_logs[0]["topics"] == [topic, "0x" + historical_arg.to_bytes(32, "big").hex()]
        assert receipt_logs[0]["data"] == "0x"
        key = storage_key(slot)
        pre = state.get("pre", {}).get(PROXY, {}).get("storage", {})
        post = state.get("post", {}).get(PROXY, {}).get("storage", {})
        historical_before = int(pre.get(key, "0x0"), 16)
        historical_after = (historical_before & ~(LOW160 << shift)) | (historical_arg << shift)
        assert set(post) <= {key}
        assert int(post.get(key, "0x0"), 16) == historical_after
        historical_rows.append({"selector": selector, "tx": tx, "block": matching[0]["block"],
                                "caller": contract_calls[0]["from"].lower(),
                                "argument": "0x" + historical_arg.to_bytes(20, "big").hex(),
                                "storage_slot": slot, "before_word": "0x" + historical_before.to_bytes(32, "big").hex(),
                                "after_word": "0x" + historical_after.to_bytes(32, "big").hex(),
                                "storage_changed": historical_before != historical_after})
        events.append({"topic0": topic, "reconstructed_signature": event_signature,
                       "status": "observed_historical_topic", "setter_selector": selector,
                       "historical_tx": tx})
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": names, "setter_rows": rows,
            "historical_setter_transactions": historical_rows,
            "event_catalog": events, "owner_new_success_count": len(rows),
            "owner_zero_success_count": len(rows), "outsider_not_owner_count": len(rows),
            "limits": ["Seven historical calls verify actual argument, event, and transaction-level slot effects; owner, outsider, and zero-address branches are read-only simulations at the pin.",
                       "All seven setters accept the zero address in the tested runtime, including ownership transfer; downstream behavior after such a change is untested."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange admin setters: {len(result['selector_reconstructions'])} names, "
          f"{len(result['event_catalog'])} events, {result['owner_zero_success_count']} zero-address calls")
