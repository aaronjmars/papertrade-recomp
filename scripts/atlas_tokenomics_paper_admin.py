#!/usr/bin/env python3
"""Verify the Tokenomics PAPER-token admin setter, getter, and event."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_tokenomics import IMPLEMENTATION, PIN, TOKEN, TOKENOMICS, rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "tokenomics_paper_admin" / "pinned_probes.json"
TX = "0xbc7591dde3758def9f7e8c9453f1626e7bbb171c76b29c49f45b10cb270ee15f"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
ORIGINAL_OWNER = "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
OUTSIDER = "0x1111111111111111111111111111111111111111"
OTHER = "0x4444444444444444444444444444444444444444"
ZERO = "0x0000000000000000000000000000000000000000"
SETTER = "0xe6ee2285"
GETTER = "0x98255e15"
EVENT = "0x430bfdc2fc284dd0409a30c5119cc184eb9971421e45c37bc9904ce47fb2ffef"
SETTER_SIGNATURE = "setPaperToken(address)"
GETTER_SIGNATURE = "paperToken()"
EVENT_SIGNATURE = "PaperTokenUpdated(address)"


def word(value):
    return f"0x{value:064x}"


def calldata(address):
    return SETTER + f"{int(address, 16):064x}"


def nested_logs(call):
    logs = list(call.get("logs", []))
    for child in call.get("calls", []):
        logs.extend(nested_logs(child))
    return logs


def cases():
    return {"owner_other": (OWNER, OTHER), "outsider_other": (OUTSIDER, OTHER),
            "owner_zero": (OWNER, ZERO), "owner_current": (OWNER, TOKEN)}


def capture():
    if ARTIFACT.exists():
        return
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    current_getter = rpc(url, "eth_call", [{"to": TOKENOMICS, "data": GETTER}, hex(PIN)])
    current_slot = rpc(url, "eth_getStorageAt", [TOKENOMICS, word(2), hex(PIN)])
    probes = {}
    for name, (sender, address) in cases().items():
        call = {"from": sender, "to": TOKENOMICS, "data": calldata(address)}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN),
            {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        row = {"sender": sender, "target": address, "calldata": call["data"],
               "error": trace.get("error"), "output": trace.get("output", ""),
               "logs": nested_logs(trace),
               "implementation_calls": [{"type": child["type"], "to": child["to"],
                                          "input": child["input"]}
                                         for child in trace.get("calls", [])]}
        if name in ("owner_other", "owner_zero", "owner_current"):
            diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            row["pre_storage"] = diff.get("pre", {}).get(TOKENOMICS, {}).get("storage", {})
            row["post_storage"] = diff.get("post", {}).get(TOKENOMICS, {}).get("storage", {})
        probes[name] = row
    ARTIFACT.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                    "getter_output": current_getter,
                                    "slot_2": current_slot, "probes": probes}, indent=2) + "\n")


def verify():
    keccak = Keccak()
    assert "0x" + keccak(SETTER_SIGNATURE.encode()).hex()[:8] == SETTER
    assert "0x" + keccak(GETTER_SIGNATURE.encode()).hex()[:8] == GETTER
    assert "0x" + keccak(EVENT_SIGNATURE.encode()).hex() == EVENT
    saved = json.loads(ARTIFACT.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert int(saved["getter_output"], 16) == int(saved["slot_2"], 16) == int(TOKEN, 16)
    links = json.loads((ATLAS / "state_links.json").read_text())
    assert any(row["from"].lower() == TOKENOMICS and row["getter"] == GETTER_SIGNATURE
               and row["to"].lower() == TOKEN and row["storage_slots_read"] == [2]
               for row in links)
    trace = json.loads((ROOT / "artifacts" / "historical" / f"{TX}.calls.json").read_text())
    diff = json.loads((ROOT / "artifacts" / "historical" / f"{TX}.state_diff.json").read_text())
    receipt = json.loads((ROOT / "artifacts" / "historical" / f"{TX}.receipt.json").read_text())
    assert trace["from"].lower() == ORIGINAL_OWNER and trace["to"].lower() == TOKENOMICS
    assert trace["input"] == calldata(TOKEN) and trace.get("error") is None
    assert len(trace["calls"]) == 1 and trace["calls"][0]["to"].lower() == IMPLEMENTATION
    event = next(log for log in receipt["logs"] if log["address"].lower() == TOKENOMICS
                 and log["topics"][0] == EVENT)
    assert event["topics"] == [EVENT, word(int(TOKEN, 16))] and event["data"] == "0x"
    assert word(2) not in diff.get("pre", {}).get(TOKENOMICS, {}).get("storage", {})
    assert diff["post"][TOKENOMICS]["storage"][word(2)] == word(int(TOKEN, 16))
    assert set(saved["probes"]) == set(cases())
    for name, row in saved["probes"].items():
        sender, address = cases()[name]
        assert row["sender"] == sender and row["target"] == address
        assert row["calldata"] == calldata(address)
        assert row["implementation_calls"] == [{"type": "DELEGATECALL", "to": IMPLEMENTATION,
                                                "input": row["calldata"]}]
        if name == "outsider_other":
            assert row["error"] == "execution reverted" and row["output"] == "0x30cd7471"
            assert row["logs"] == []
        else:
            assert row["error"] is None and row["output"] == "" and len(row["logs"]) == 1
            assert row["logs"][0]["address"].lower() == TOKENOMICS
            assert row["logs"][0]["topics"] == [EVENT, word(int(address, 16))]
            assert row["logs"][0]["data"] == "0x"
            expected_post = {} if name in ("owner_current", "owner_zero") else {
                word(2): word(int(address, 16))}
            assert row["post_storage"] == expected_post
            if name != "owner_current":
                assert row["pre_storage"] == {word(2): word(int(TOKEN, 16))}
    result = {"pin_block": PIN, "tokenomics_proxy": TOKENOMICS,
              "implementation": IMPLEMENTATION, "historical_transaction": TX,
              "selector_reconstructions": {SETTER: SETTER_SIGNATURE, GETTER: GETTER_SIGNATURE},
              "event_catalog": [{"topic0": EVENT, "reconstructed_signature": EVENT_SIGNATURE,
                                 "status": "observed_historical", "indexed_fields": ["paperToken"],
                                 "data_fields": []}],
              "storage_slot": 2, "current_value": TOKEN, "probe_count": len(saved["probes"]),
              "owner_can_set_zero_at_pin": True,
              "simulated_error_catalog": [{"selector": "0x30cd7471",
                                           "reconstructed_signature": "NotOwner()",
                                           "probe_paths": ["outsider_other"]}],
              "limits": ["Zero-address acceptance is a pinned read-only simulation, not an on-chain update.",
                         "The setter's downstream behavior after changing the token address was not replayed."]}
    (ATLAS / "tokenomics_paper_admin_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Tokenomics PAPER admin: historical slot write, event, getter, and 4 probes verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
