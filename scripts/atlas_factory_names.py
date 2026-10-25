#!/usr/bin/env python3
"""Verify factory selector names against pinned getters and a read-only owner transfer."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_behavior import FACTORY, IMPLEMENTATION, PIN, rpc, word
from atlas_factory_events import Keccak

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "factory_names"
SAVED = ARTIFACTS / "pinned_factory_names.json"
OUT = ATLAS / "factory_selector_names_behavior.json"
KECCAK = Keccak()
LOW160 = (1 << 160) - 1
NAMES = {
    "0x03b802b6": "authorizedDeployer()",
    "0x29710388": "isProxy(address)",
    "0x8da5cb5b": "owner()",
    "0xc1a9a508": "proxyOf(address)",
    "0xc6f881bc": "setAuthorizedDeployer(address)",
    "0xcbd433f4": "deployProxy(address)",
    "0xd2f7265a": "exchange()",
    "0xd600539a": "computeProxyAddress(address)",
    "0xf2fde38b": "transferOwnership(address)",
}
DIRECT = {"0x03b802b6": (4, 0), "0x8da5cb5b": (3, 0), "0xd2f7265a": (0, 16)}


def mapping_slot(address, base):
    return "0x" + KECCAK(int(address, 16).to_bytes(32, "big") + base.to_bytes(32, "big")).hex()


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    words = {str(slot): rpc(url, "eth_getStorageAt", [FACTORY, hex(slot), hex(PIN)]) for slot in (0, 3, 4)}
    direct = {selector: rpc(url, "eth_call", [{"to": FACTORY, "data": selector}, hex(PIN)]) for selector in DIRECT}
    deployed = json.loads((ATLAS / "factory_user_proxy_map.json").read_text())
    assert len(deployed) == 22586
    selected = [deployed[i] for i in (0, len(deployed) // 2, len(deployed) - 1)]
    samples = []
    for row in selected:
        user, proxy = row["user"], row["proxy"]
        user_slot = mapping_slot(user, 1)
        proxy_slot = mapping_slot(proxy, 2)
        samples.append({
            "user": user, "proxy": proxy,
            "proxy_of_slot": user_slot,
            "proxy_of_storage": rpc(url, "eth_getStorageAt", [FACTORY, user_slot, hex(PIN)]),
            "proxy_of_output": rpc(url, "eth_call", [{"to": FACTORY, "data": "0xc1a9a508" + word(user)}, hex(PIN)]),
            "is_proxy_slot": proxy_slot,
            "is_proxy_storage": rpc(url, "eth_getStorageAt", [FACTORY, proxy_slot, hex(PIN)]),
            "is_proxy_output": rpc(url, "eth_call", [{"to": FACTORY, "data": "0x29710388" + word(proxy)}, hex(PIN)]),
            "computed_output": rpc(url, "eth_call", [{"to": FACTORY, "data": "0xd600539a" + word(user)}, hex(PIN)]),
        })
    new_owner = "0x" + "11" * 20
    call = {"from": "0x" + words["3"][-40:], "to": FACTORY,
            "data": "0xf2fde38b" + word(new_owner), "gas": "0x1000000"}
    transfer_call = rpc(url, "debug_traceCall", [call, hex(PIN),
        {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
    transfer_diff = rpc(url, "debug_traceCall", [call, hex(PIN),
        {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin_block": PIN, "block_hash": header["hash"],
                                 "storage_words": words, "direct_outputs": direct,
                                 "deployed_samples": samples,
                                 "transfer_call": transfer_call, "transfer_diff": transfer_diff}, indent=2) + "\n")


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
    assert traces["target"] == FACTORY
    views = {row["selector"]: row for row in traces["views"]}
    old_words = json.loads((ATLAS / "factory_behavior.json").read_text())["direct_storage"]
    for selector, (slot, shift) in DIRECT.items():
        assert views[selector]["direct_slots"] == [slot] and not views[selector]["failed"]
        raw = int(saved["storage_words"][str(slot)], 16)
        assert saved["storage_words"][str(slot)] == old_words[str(slot)]["raw"]
        assert int(saved["direct_outputs"][selector], 16) == (raw >> shift) & LOW160
    assert views["0xc1a9a508"]["mapping_matches"][0]["base_slot"] == 1
    assert views["0x29710388"]["mapping_matches"][0]["base_slot"] == 2
    assert views["0xd600539a"]["direct_slots"] == [0]
    deployed = json.loads((ATLAS / "factory_user_proxy_map.json").read_text())
    expected = [deployed[i] for i in (0, len(deployed) // 2, len(deployed) - 1)]
    for sample, row in zip(saved["deployed_samples"], expected, strict=True):
        user, proxy = row["user"], row["proxy"]
        assert (sample["user"], sample["proxy"]) == (user, proxy)
        assert sample["proxy_of_slot"] == mapping_slot(user, 1)
        assert sample["is_proxy_slot"] == mapping_slot(proxy, 2)
        assert int(sample["proxy_of_storage"], 16) == int(sample["proxy_of_output"], 16) == int(proxy, 16)
        assert int(sample["is_proxy_storage"], 16) == int(sample["is_proxy_output"], 16) == 1
        assert int(sample["computed_output"], 16) == int(proxy, 16)
    assert len(saved["deployed_samples"]) == 3
    factory = json.loads((ATLAS / "factory_behavior.json").read_text())
    probes = factory["probes"]
    assert probes["deploy_authorized_new"]["success"] and probes["deploy_owner_new"]["success"]
    assert probes["deploy_unauthorized_new"]["revert_selector"] == "0x27fba80a"
    assert probes["set_deployer_owner"]["success"]
    assert probes["set_deployer_outsider"]["revert_selector"] == "0x30cd7471"
    call = saved["transfer_call"]
    diff = saved["transfer_diff"]
    assert not call.get("error") and call.get("output", "0x") == "0x"
    topic = "0x" + KECCAK(b"OwnerUpdated(address)").hex()
    assert len(call["calls"]) == 1 and call["calls"][0]["type"] == "DELEGATECALL"
    logs = call["calls"][0]["logs"]
    assert len(logs) == 1
    assert logs[0]["topics"] == [topic, "0x" + word("0x" + "11" * 20)]
    slot = "0x" + (3).to_bytes(32, "big").hex()
    pre = diff["pre"][FACTORY]["storage"]
    post = diff["post"][FACTORY]["storage"]
    assert int(pre[slot], 16) == int(saved["storage_words"]["3"], 16)
    assert int(post[slot], 16) == int("11" * 20, 16)
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "factory_proxy": FACTORY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": NAMES,
            "direct_getter_count": len(DIRECT),
            "deployed_mapping_samples": saved["deployed_samples"],
            "read_only_owner_transfer": {"new_owner": "0x" + "11" * 20,
                                         "event_topic": topic, "old_owner": "0x" + pre[slot][-40:]},
            "remaining_unnamed_selectors": ["0x0f71c8bc", "0x56e8d85b", "0xc4d66de8"],
            "limits": ["The three initializer names remain candidates because success or revert behavior does not establish source spelling.",
                       "Three deployed users sample getter behavior; the separate factory event ledger verifies all 22,586 deployment addresses."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Factory names: {len(result['selector_reconstructions'])}, mapping samples: {len(result['deployed_mapping_samples'])}")
