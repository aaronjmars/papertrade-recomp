#!/usr/bin/env python3
"""Verify live SessionKeyManager storage and domain getter names."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "session_getters"
SAVED = ARTIFACTS / "pinned_getters.json"
OUT = ATLAS / "session_direct_getters_behavior.json"
PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
IMPLEMENTATION = "0x8a5069fe303e8f81e91825436e956d595032e558"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
OUTSIDER = "0x" + "33" * 20
PIN = 48902346
KECCAK = Keccak()
LOW160 = (1 << 160) - 1
NAMES = {
    "0x3644e515": "DOMAIN_SEPARATOR()",
    "0x78e890ba": "domainSeparatorV4()",
    "0x7f6e9d4b": "authorizedSubmitters(address)",
    "0x8da5cb5b": "owner()",
    "0x97dc97cb": "authorizedCaller()",
}


def mapping_slot(address):
    return "0x" + KECCAK(int(address, 16).to_bytes(32, "big") + (7).to_bytes(32, "big")).hex()


def call_data(selector, address=None):
    return selector if address is None else selector + int(address, 16).to_bytes(32, "big").hex()


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    storage = {str(i): rpc(url, "eth_getStorageAt", [PROXY, hex(i), hex(PIN)]) for i in (1, 2, 3)}
    direct = {s: rpc(url, "eth_call", [{"to": PROXY, "data": s}, hex(PIN)])
              for s in ("0x3644e515", "0x78e890ba", "0x8da5cb5b", "0x97dc97cb")}
    submitters = []
    for address in (BATCH, OUTSIDER):
        slot = mapping_slot(address)
        submitters.append({"address": address, "slot": slot,
                           "storage_value": rpc(url, "eth_getStorageAt", [PROXY, slot, hex(PIN)]),
                           "getter_output": rpc(url, "eth_call", [{"to": PROXY,
                                  "data": call_data("0x7f6e9d4b", address)}, hex(PIN)])})
    domain_overrides = {}
    for name, slot, value in (("replace_slot1", 1, "0x" + "11" * 32),
                              ("clear_slot3", 3, "0x" + "00" * 32)):
        override = {PROXY: {"stateDiff": {"0x" + slot.to_bytes(32, "big").hex(): value}}}
        domain_overrides[name] = {
            "slot": slot, "replacement": value,
            "domain_separator": rpc(url, "eth_call", [{"to": PROXY, "data": "0x3644e515"}, hex(PIN), override]),
            "domain_separator_v4": rpc(url, "eth_call", [{"to": PROXY, "data": "0x78e890ba"}, hex(PIN), override]),
        }
    registration = json.loads((ATLAS / "session_key_behavior.json").read_text())["registrations"][0]
    original = json.loads((ROOT / "artifacts" / "session_keys" / f"{registration['tx']}.calls.json").read_text())
    def registration_calls(node):
        if node.get("to", "").lower() == PROXY and node.get("input", "").startswith("0x5f76a1d6"):
            yield node
        for child in node.get("calls", []):
            yield from registration_calls(child)
    nested = list(registration_calls(original))
    assert len(nested) == 1 and nested[0]["from"].lower() == BATCH
    simulated = {"from": BATCH, "to": PROXY, "data": nested[0]["input"], "gas": "0x1000000"}
    options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
    baseline = rpc(url, "debug_traceCall", [simulated, hex(registration["block"] - 1), options])
    changed = {**options, "stateOverrides": {PROXY: {"stateDiff": {
        "0x" + (3).to_bytes(32, "big").hex(): "0x" + "00" * 32}}}}
    zero_caller = rpc(url, "debug_traceCall", [simulated, hex(registration["block"] - 1), changed])
    replay = {"source_tx": registration["tx"], "source_block": registration["block"] - 1,
              "caller": BATCH, "calldata": nested[0]["input"],
              "baseline": baseline, "zero_authorized_caller": zero_caller}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin_block": PIN, "block_hash": header["hash"],
                                 "direct_storage": storage, "direct_getters": direct,
                                 "submitter_samples": submitters,
                                 "domain_overrides": domain_overrides,
                                 "registration_replay": replay}, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert saved["pin_block"] == manifest["block"] == PIN
    assert saved["block_hash"].lower() == manifest["block_hash"]
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[IMPLEMENTATION]
    runtime_selectors = {row["selector"] for row in catalog["functions"]}
    for selector, name in NAMES.items():
        assert selector in runtime_selectors
        assert "0x" + KECCAK(name.encode()).hex()[:8] == selector
    traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]
    assert traces["target"] == PROXY
    views = {row["selector"]: row for row in traces["views"]}
    for selector, slot in (("0x3644e515", 1), ("0x8da5cb5b", 2), ("0x97dc97cb", 3)):
        assert views[selector]["direct_slots"] == [slot] and not views[selector]["failed"]
    assert views["0x7f6e9d4b"]["mapping_matches"][0]["base_slot"] == 7
    assert not views["0x78e890ba"]["failed"]
    assert views["0x78e890ba"]["direct_slots"] == [3]
    assert int(saved["direct_getters"]["0x3644e515"], 16) == int(saved["direct_storage"]["1"], 16)
    assert int(saved["direct_getters"]["0x78e890ba"], 16) == int(saved["direct_storage"]["1"], 16)
    assert int(saved["direct_getters"]["0x8da5cb5b"], 16) == int(saved["direct_storage"]["2"], 16) & LOW160
    assert int(saved["direct_getters"]["0x97dc97cb"], 16) == int(saved["direct_storage"]["3"], 16) & LOW160
    behavior = json.loads((ATLAS / "session_key_behavior.json").read_text())
    assert saved["direct_getters"]["0x3644e515"] == behavior["domain_separator"]
    assert behavior["storage_bases"]["authorizedSubmitters"] == 7
    assert [x["address"] for x in saved["submitter_samples"]] == [BATCH, OUTSIDER]
    for row in saved["submitter_samples"]:
        assert row["slot"] == mapping_slot(row["address"])
        assert int(row["storage_value"], 16) == int(row["getter_output"], 16)
    assert [int(x["getter_output"], 16) for x in saved["submitter_samples"]] == [1, 0]
    creation = json.loads((ATLAS / "session_initializer_behavior.json").read_text())["historical_creation"]["decoded_arguments"]
    assert creation["chain_id"] == 999 and creation["authorized_caller"].lower() == "0x" + saved["direct_storage"]["3"][-40:]
    def domain(verifying_contract):
        typehash = KECCAK(b"EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
        payload = typehash + KECCAK(creation["name"].encode()) + KECCAK(creation["version"].encode())
        payload += creation["chain_id"].to_bytes(32, "big") + int(verifying_contract, 16).to_bytes(32, "big")
        return "0x" + KECCAK(payload).hex()
    current_domain = domain(creation["authorized_caller"])
    assert current_domain == saved["direct_getters"]["0x3644e515"] == saved["direct_getters"]["0x78e890ba"]
    overrides = saved["domain_overrides"]
    assert set(overrides) == {"replace_slot1", "clear_slot3"}
    changed_storage = overrides["replace_slot1"]
    assert changed_storage["slot"] == 1 and changed_storage["replacement"] == "0x" + "11" * 32
    assert changed_storage["domain_separator"] == changed_storage["replacement"]
    assert changed_storage["domain_separator_v4"] == current_domain
    changed_caller = overrides["clear_slot3"]
    assert changed_caller["slot"] == 3 and int(changed_caller["replacement"], 16) == 0
    assert changed_caller["domain_separator"] == current_domain
    assert changed_caller["domain_separator_v4"] == domain("0x" + "00" * 20)
    registration = behavior["registrations"][0]
    replay = saved["registration_replay"]
    assert replay["source_tx"] == registration["tx"]
    assert replay["source_block"] == registration["block"] - 1
    assert replay["caller"] == BATCH and replay["calldata"].startswith("0x5f76a1d6")
    assert not replay["baseline"].get("error")
    assert replay["zero_authorized_caller"].get("error") == "execution reverted"
    assert replay["zero_authorized_caller"]["output"] == "0x8baa579f"
    assert "0x" + KECCAK(b"InvalidSignature()").hex()[:8] == "0x8baa579f"
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "session_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": NAMES,
            "direct_storage": saved["direct_storage"],
            "direct_getters": saved["direct_getters"],
            "submitter_samples": saved["submitter_samples"],
            "domain_formula": "keccak256(EIP712Domain typehash, keccak256(name), keccak256(version), chainId, authorizedCaller)",
            "domain_overrides": overrides,
            "registration_domain_replay": {"source_tx": replay["source_tx"], "source_block": replay["source_block"],
                                           "baseline_succeeded": True, "changed_caller_error": "InvalidSignature()"},
            "limits": ["The signed registration replay uses the block before its source transaction; other same-block state and changed-caller signature paths remain untested.",
                       "The two typehash constant selector names remain public candidates until their trade struct preimages are independently checked."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Session getters: {len(result['selector_reconstructions'])} names, {len(result['submitter_samples'])} submitters")
