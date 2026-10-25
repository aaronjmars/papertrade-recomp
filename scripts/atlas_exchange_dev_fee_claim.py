#!/usr/bin/env python3
"""Verify Exchange developer-fee claim accounting, event, and caller branches."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_dev_fee_claim"
SAVED = ARTIFACTS / "pinned_claim_probes.json"
OUT = ATLAS / "exchange_dev_fee_claim_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
RECIPIENT = "0xeef651e381e04b5ae25393b1367c19bcfd575792"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
ALTERNATE = "0x" + "33" * 20
HISTORICAL_TX = "0x08ef99988867832607e4d50d8eab4b08651b1f89664eeb5fa2ddab89b23761e3"
PIN = 48902346
SELECTOR = "0x88f2aea5"
SIGNATURE = "claimDevFees()"
EVENT_SIGNATURE = "DevFeesClaimed(address,uint256,uint256)"
ERROR_SIGNATURE = "NotDevFeeRecipient()"
KECCAK = Keccak()
LOW128 = (1 << 128) - 1


def slot_key(slot):
    return "0x" + slot.to_bytes(32, "big").hex()


def balance_slot(address):
    return "0x" + KECCAK(int(address, 16).to_bytes(32, "big") + (9).to_bytes(32, "big")).hex()


def all_calls(node):
    yield node
    for child in node.get("calls", []):
        yield from all_calls(child)


def all_logs(node):
    for call in all_calls(node):
        yield from call.get("logs", [])


def event_words(log):
    data = log["data"]
    assert len(data) == 130
    return int(data[2:66], 16), int(data[66:130], 16)


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    raw = {"22": rpc(url, "eth_getStorageAt", [PROXY, hex(22), hex(PIN)]),
           "26": rpc(url, "eth_getStorageAt", [PROXY, hex(26), hex(PIN)]),
           "38": rpc(url, "eth_getStorageAt", [PROXY, hex(38), hex(PIN)]),
           "recipient_balance": rpc(url, "eth_getStorageAt", [PROXY, balance_slot(RECIPIENT), hex(PIN)]),
           "alternate_balance": rpc(url, "eth_getStorageAt", [PROXY, balance_slot(ALTERNATE), hex(PIN)])}
    slot26 = int(raw["26"], 16)
    zero_fee_word = slot26 & LOW128
    one_fee_word = zero_fee_word | (1 << 128)
    alternate_word = int(ALTERNATE, 16)
    overrides = {
        "zero_fee": {PROXY: {"stateDiff": {slot_key(26): "0x" + zero_fee_word.to_bytes(32, "big").hex()}}},
        "one_unit_fee": {PROXY: {"stateDiff": {slot_key(26): "0x" + one_fee_word.to_bytes(32, "big").hex()}}},
        "reassigned": {PROXY: {"stateDiff": {slot_key(38): "0x" + alternate_word.to_bytes(32, "big").hex()}}},
    }
    cases = {}
    for name, sender, override in (
        ("recipient_baseline", RECIPIENT, None),
        ("owner_rejected", OWNER, None),
        ("outsider_rejected", ALTERNATE, None),
        ("recipient_zero_fee", RECIPIENT, overrides["zero_fee"]),
        ("recipient_one_unit", RECIPIENT, overrides["one_unit_fee"]),
        ("alternate_reassigned", ALTERNATE, overrides["reassigned"]),
        ("old_recipient_reassigned", RECIPIENT, overrides["reassigned"]),
    ):
        call = {"from": sender, "to": PROXY, "data": SELECTOR, "gas": "0x1000000"}
        opts = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
        if override:
            opts["stateOverrides"] = override
        trace = rpc(url, "debug_traceCall", [call, hex(PIN), opts])
        case = {"caller": sender, "call": trace}
        if name in ("recipient_baseline", "recipient_zero_fee", "recipient_one_unit", "alternate_reassigned"):
            diff_opts = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
            if override:
                diff_opts["stateOverrides"] = override
            case["diff"] = rpc(url, "debug_traceCall", [call, hex(PIN), diff_opts])
        cases[name] = case
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin_block": PIN, "block_hash": header["hash"],
                                 "storage": raw, "overrides": overrides, "cases": cases}, indent=2) + "\n")


def checked_success(case, recipient, amount, old22=None, old26=None, old_balance=None):
    call = case["call"]
    assert not call.get("error")
    logs = list(all_logs(call))
    if amount == 0:
        assert not logs
        assert not case["diff"].get("post", {}).get(PROXY, {}).get("storage", {})
        return
    assert len(logs) == 1
    log = logs[0]
    assert log["address"].lower() == PROXY
    assert log["topics"] == ["0x" + KECCAK(EVENT_SIGNATURE.encode()).hex(),
                             "0x" + int(recipient, 16).to_bytes(32, "big").hex()]
    assert event_words(log) == (amount, amount)
    pre = case["diff"].get("pre", {}).get(PROXY, {}).get("storage", {})
    post = case["diff"].get("post", {}).get(PROXY, {}).get("storage", {})
    key22, key26, balance_key = slot_key(22), slot_key(26), balance_slot(recipient)
    assert set(post) == {key22, key26, balance_key}
    old22 = int(pre.get(key22, "0x0"), 16) if old22 is None else old22
    old26 = int(pre.get(key26, "0x0"), 16) if old26 is None else old26
    old_balance = int(pre.get(balance_key, "0x0"), 16) if old_balance is None else old_balance
    assert old26 >> 128 == amount
    assert int(post[key26], 16) == old26 & LOW128
    assert int(post[key22], 16) == old22 + amount
    assert int(post[balance_key], 16) == old_balance + amount


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert saved["pin_block"] == manifest["block"] == PIN
    assert saved["block_hash"].lower() == manifest["block_hash"]
    assert "0x" + KECCAK(SIGNATURE.encode()).hex()[:8] == SELECTOR
    topic = "0x" + KECCAK(EVENT_SIGNATURE.encode()).hex()
    assert "0x" + KECCAK(ERROR_SIGNATURE.encode()).hex()[:8] == "0x2d016ae6"
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[IMPLEMENTATION]
    assert SELECTOR in {row["selector"] for row in catalog["functions"]}
    direct = json.loads((ATLAS / "exchange_direct_getters_behavior.json").read_text())
    direct_by_slot = {row["storage_slot"]: row["raw_word"] for row in direct["direct_slot_getters"]}
    assert saved["storage"]["22"] == direct_by_slot[22]
    assert saved["storage"]["26"] == direct_by_slot[26]
    assert saved["storage"]["38"] == direct_by_slot[38]
    assert int(saved["storage"]["38"], 16) == int(RECIPIENT, 16)
    historical = ROOT / "artifacts" / "historical" / HISTORICAL_TX
    trace = json.loads(Path(str(historical) + ".calls.json").read_text())
    receipt = json.loads(Path(str(historical) + ".receipt.json").read_text())
    diff = json.loads(Path(str(historical) + ".state_diff.json").read_text())
    assert trace["to"].lower() == PROXY and trace["from"].lower() == RECIPIENT
    assert trace["input"] == SELECTOR and not trace.get("error")
    assert [call["type"] for call in list(all_calls(trace))[1:]] == ["DELEGATECALL"]
    logs = [log for log in receipt["logs"] if log["address"].lower() == PROXY]
    assert len(logs) == 1 and logs[0]["topics"] == [topic, "0x" + int(RECIPIENT, 16).to_bytes(32, "big").hex()]
    claimed, repeated = event_words(logs[0])
    assert claimed == repeated == 114890275671617164291236
    pre = diff["pre"][PROXY]["storage"]
    post = diff["post"][PROXY]["storage"]
    key22, key26, balance_key = slot_key(22), slot_key(26), balance_slot(RECIPIENT)
    assert set(post) == {key22, key26, balance_key}
    assert int(pre[key26], 16) >> 128 == claimed
    assert int(post[key26], 16) == int(pre[key26], 16) & LOW128
    assert int(post[key22], 16) - int(pre[key22], 16) == claimed
    assert int(post[balance_key], 16) - int(pre[balance_key], 16) == claimed
    cases = saved["cases"]
    assert set(cases) == {"recipient_baseline", "owner_rejected", "outsider_rejected",
                          "recipient_zero_fee", "recipient_one_unit", "alternate_reassigned",
                          "old_recipient_reassigned"}
    amount = int(saved["storage"]["26"], 16) >> 128
    checked_success(cases["recipient_baseline"], RECIPIENT, amount,
                    int(saved["storage"]["22"], 16), int(saved["storage"]["26"], 16),
                    int(saved["storage"]["recipient_balance"], 16))
    checked_success(cases["recipient_zero_fee"], RECIPIENT, 0)
    checked_success(cases["recipient_one_unit"], RECIPIENT, 1,
                    int(saved["storage"]["22"], 16),
                    (int(saved["storage"]["26"], 16) & LOW128) | (1 << 128),
                    int(saved["storage"]["recipient_balance"], 16))
    checked_success(cases["alternate_reassigned"], ALTERNATE, amount,
                    int(saved["storage"]["22"], 16), int(saved["storage"]["26"], 16),
                    int(saved["storage"]["alternate_balance"], 16))
    for name in ("owner_rejected", "outsider_rejected", "old_recipient_reassigned"):
        call = cases[name]["call"]
        assert call.get("error") == "execution reverted" and call.get("output") == "0x2d016ae6"
        assert not list(all_logs(call))
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": {SELECTOR: SIGNATURE},
            "event_catalog": [{"topic0": topic, "reconstructed_signature": EVENT_SIGNATURE,
                               "status": "observed_historical_topic", "historical_tx": HISTORICAL_TX}],
            "simulated_error_catalog": [{"selector": "0x2d016ae6", "reconstructed_signature": ERROR_SIGNATURE,
                                         "probe_paths": ["owner_rejected", "outsider_rejected", "old_recipient_reassigned"]}],
            "historical_claim": {"tx": HISTORICAL_TX, "block": 48901667,
                                 "recipient": RECIPIENT, "claimed_amount": claimed,
                                 "balance_mapping_slot": balance_key,
                                 "no_external_child_call": True},
            "pinned_claim_amount": amount,
            "pinned_case_names": list(cases),
            "limits": ["One historical claim and read-only pinned branch probes support the described path; other states remain untested.",
                       "The two unindexed event words equal the claim amount in the tested cases; their source parameter names are unavailable.",
                       "The sampled path credits internal Exchange balance and does not call an external token transfer."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange dev fee claim: {len(result['pinned_case_names'])} pinned cases, "
          f"historical amount {result['historical_claim']['claimed_amount']}")
