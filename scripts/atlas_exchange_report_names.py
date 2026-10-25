#!/usr/bin/env python3
"""Check Guardian name leads against pinned Exchange bytes and saved execution."""

import json
import pathlib

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
SETTER_TX = "0xb357f09ef042c99d383e702118230d8fde098a78ab433b7a5a06e1b2c6a0bccd"
SELECTORS = {
    "0xcd2d3811": "setStakerFeeRecipient(address)",
    "0xe1f9209b": "stakerFeeRecipient()",
    "0x138e9de2": "queueHarvestAvailable()",
    "0x0cdd5fc4": "lpBankrollAvailable()",
}
ADDITIONAL_LEADS = {
    "0xae69b95b": "setTradingPaused(bool)",
    "0xddc63262": "harvest(uint256)",
    "0xe53e3de6": "creditStakingReward(address,uint256)",
}
EVENT_SIGNATURE = "StakerFeeRecipientUpdated(address)"
EVENT_TOPIC = "0xbcd09d92c26e8078d8be2b8380bb7d1ab324d0a9ae6743e158ad8d7f734a84ba"
REPORT = "https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/"


def verify():
    keccak = Keccak()
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[IMPLEMENTATION]
    live = {row["selector"] for row in catalog["functions"]}
    for selector, signature in (SELECTORS | ADDITIONAL_LEADS).items():
        assert "0x" + keccak(signature.encode()).hex()[:8] == selector
        assert selector in live
    assert "0x" + keccak(EVENT_SIGNATURE.encode()).hex() == EVENT_TOPIC

    call = json.loads((HISTORICAL / f"{SETTER_TX}.calls.json").read_text())
    receipt = json.loads((HISTORICAL / f"{SETTER_TX}.receipt.json").read_text())
    diff = json.loads((HISTORICAL / f"{SETTER_TX}.state_diff.json").read_text())
    assert call["to"].lower() == PROXY and call["input"][:10] == "0xcd2d3811"
    assert int(call["input"][10:], 16) == int(STAKING, 16)
    assert call.get("error") is None and len(call["calls"]) == 1
    assert call["calls"][0]["type"] == "DELEGATECALL"
    assert call["calls"][0]["to"].lower() == IMPLEMENTATION
    assert receipt["status"] == "0x1" and len(receipt["logs"]) == 1
    log = receipt["logs"][0]
    assert log["address"].lower() == PROXY
    assert log["topics"] == [EVENT_TOPIC, "0x" + int(STAKING, 16).to_bytes(32, "big").hex()]
    assert log["data"] == "0x"
    slot31 = "0x" + (31).to_bytes(32, "big").hex()
    assert int(diff["post"][PROXY]["storage"][slot31], 16) == int(STAKING, 16)

    traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]["views"]
    views = {row["selector"]: row for row in traces}
    recipient = views["0xe1f9209b"]
    assert not recipient["failed"] and recipient["direct_slots"] == [31]
    assert int(recipient["return_prefix"], 16) == int(STAKING, 16)
    queue = views["0x138e9de2"]
    bankroll = views["0x0cdd5fc4"]
    assert not queue["failed"] and not bankroll["failed"]
    assert set(queue["direct_slots"]) == {14, 22, 26}
    assert set(bankroll["direct_slots"]) == {14, 18, 22, 26}
    assert queue["return_prefix"] == bankroll["return_prefix"]

    result = {
        "pin_block": manifest["block"], "exchange_proxy": PROXY,
        "implementation": IMPLEMENTATION, "source_name_lead": REPORT,
        "selector_reconstructions": SELECTORS,
        "additional_exact_hash_name_leads": ADDITIONAL_LEADS,
        "event_catalog": [{"topic0": EVENT_TOPIC,
                           "reconstructed_signature": EVENT_SIGNATURE,
                           "status": "observed_historical_topic"}],
        "historical_setter_transaction": SETTER_TX,
        "historical_setter_storage_slot": 31,
        "pinned_getters": {
            selector: {"output": views[selector]["return_prefix"],
                       "direct_slots": views[selector]["direct_slots"]}
            for selector in ("0xe1f9209b", "0x138e9de2", "0x0cdd5fc4")},
        "limitations": [
            "The audit report names functions but its source snapshot has not been matched to live runtime bytecode.",
            "The two available-balance getters agree at this pinned state; their divergent branches are mapped separately in exchange_availability_behavior.json.",
            "Additional exact-hash name leads are not promoted to reconstructed behavior here.",
        ],
    }
    (ATLAS / "exchange_report_names_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange report names: 4 behavior-backed selectors, 1 historical event, 3 further name leads")


if __name__ == "__main__":
    verify()
