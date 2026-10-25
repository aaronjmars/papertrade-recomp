#!/usr/bin/env python3
"""Reconstruct Exchange fee and LP excess pushes to Staking."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_tokenomics import EXCHANGE, PIN, TOKENOMICS, descendants, rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_staker_fee_push" / "pinned_probes.json"
TOKENOMICS_ARTIFACTS = ROOT / "artifacts" / "tokenomics"
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
EXCHANGE_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
OUTSIDER = "0x1111111111111111111111111111111111111111"
SELECTOR = "0x7b9f5264"
SIGNATURE = "pushStakerFees()"
FEE_SIGNATURE = "StakerFeesClaimed(address,uint256,uint256)"
FEE_TOPIC = "0x18d8b7951a20bbcb2b5f45b29bb62a81963f4b1f75dac5e2493a885a6de74291"
EXCESS_SIGNATURE = "StakerLpExcessDistributed(address,uint256,uint256,uint256)"
EXCESS_TOPIC = "0x17d88d5ce12b7103190340ee5304ff19dbf970a0289bb2684460e4a87a7b66f9"
TOKENOMICS_ADJUSTMENT = "0x09f6ca7b163aa16d9feb37c8882b930e40c3e111f64037cb2b00adf65693e14f"
STAKING_DISTRIBUTED = "0xf7576d8c2653e9d07af5ef229acf59b339e327d4e0eaddb4a96615534cf148f8"
NO_EXCESS_TX = "0xb27bbadf830f5673211719cf6585d9929e91a446c3f46aee940e6e2e02888cdb"


def word(value):
    return f"0x{value:064x}"


def data_words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[index:index + 64], 16) for index in range(2, len(data), 64)]


def all_logs(call):
    logs = list(call.get("logs", []))
    for child in call.get("calls", []):
        logs.extend(all_logs(child))
    return logs


def fee_slot():
    return int.from_bytes(Keccak()(int(STAKING, 16).to_bytes(32, "big")
                                  + (9).to_bytes(32, "big")), "big")


def capture_missing_history(url):
    paths = {suffix: TOKENOMICS_ARTIFACTS / f"{NO_EXCESS_TX}.{suffix}.json"
             for suffix in ("calls", "receipt", "state_diff")}
    if all(path.exists() for path in paths.values()):
        return
    TOKENOMICS_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    trace = rpc(url, "debug_traceTransaction", [NO_EXCESS_TX,
        {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
    receipt = rpc(url, "eth_getTransactionReceipt", [NO_EXCESS_TX])
    diff = rpc(url, "debug_traceTransaction", [NO_EXCESS_TX,
        {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
    assert trace.get("error") is None and int(receipt["status"], 16) == 1
    assert int(receipt["blockNumber"], 16) <= PIN
    for suffix, value in (("calls", trace), ("receipt", receipt), ("state_diff", diff)):
        paths[suffix].write_text(json.dumps(value, indent=2) + "\n")


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    capture_missing_history(url)
    if ARTIFACT.exists():
        return
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    raw_fee_word = int(rpc(url, "eth_getStorageAt", [EXCHANGE, word(26), hex(PIN)]), 16)
    fee_zero_word = raw_fee_word >> 128 << 128
    cases = {"baseline_staking": (STAKING, False, False),
             "baseline_outsider": (OUTSIDER, False, False),
             "zero_excess": (OUTSIDER, False, True),
             "zero_fee": (OUTSIDER, True, False),
             "both_zero": (OUTSIDER, True, True)}
    rows = {}
    for name, (sender, zero_fee, zero_excess) in cases.items():
        call = {"from": sender, "to": EXCHANGE, "data": SELECTOR, "gas": "0x989680"}
        opts = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
        overrides = {}
        if zero_fee:
            overrides[EXCHANGE] = {"stateDiff": {word(26): word(fee_zero_word)}}
        if zero_excess:
            overrides[TOKENOMICS] = {"stateDiff": {word(3): word(5 * 10**24)}}
        if overrides:
            opts["stateOverrides"] = overrides
        trace = rpc(url, "debug_traceCall", [call, hex(PIN), opts])
        getter_calls = [child for child in descendants(trace)
                        if child.get("to", "").lower() == TOKENOMICS
                        and child.get("input", "")[:10] == "0xae745703"]
        rows[name] = {"sender": sender, "zero_fee_override": zero_fee,
                      "zero_excess_override": zero_excess, "error": trace.get("error"),
                      "logs": all_logs(trace),
                      "excess_getter_outputs": [child["output"] for child in getter_calls]}
        if name == "baseline_staking":
            diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            rows[name]["pre_storage"] = {address: state.get("storage", {})
                                         for address, state in diff.get("pre", {}).items()
                                         if state.get("storage")}
            rows[name]["post_storage"] = {address: state.get("storage", {})
                                          for address, state in diff.get("post", {}).items()
                                          if state.get("storage")}
    ARTIFACT.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                    "fee_word_slot_26": word(raw_fee_word),
                                    "fee_zero_override": word(fee_zero_word),
                                    "cases": rows}, indent=2) + "\n")


def verify():
    keccak = Keccak()
    assert "0x" + keccak(SIGNATURE.encode()).hex()[:8] == SELECTOR
    assert "0x" + keccak(FEE_SIGNATURE.encode()).hex() == FEE_TOPIC
    assert "0x" + keccak(EXCESS_SIGNATURE.encode()).hex() == EXCESS_TOPIC
    saved = json.loads(ARTIFACT.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert int(saved["fee_zero_override"], 16) == (int(saved["fee_word_slot_26"], 16) >> 128 << 128)
    expected = {"baseline_staking": (STAKING, True, True),
                "baseline_outsider": (OUTSIDER, True, True),
                "zero_excess": (OUTSIDER, True, False),
                "zero_fee": (OUTSIDER, False, True),
                "both_zero": (OUTSIDER, False, False)}
    assert set(saved["cases"]) == set(expected)
    pinned_fee = int(saved["fee_word_slot_26"], 16) & (2**128 - 1)
    pinned_excess = 968649731559005181671
    for name, row in saved["cases"].items():
        sender, has_fee, has_excess = expected[name]
        assert row["sender"] == sender and row["error"] is None
        assert row["zero_fee_override"] == (not has_fee)
        assert row["zero_excess_override"] == (not has_excess)
        assert [int(value, 16) for value in row["excess_getter_outputs"]] == (
            [pinned_excess, 0] if has_excess else [0])
        logs = row["logs"]
        fee = [log for log in logs if log["topics"][0] == FEE_TOPIC]
        excess = [log for log in logs if log["topics"][0] == EXCESS_TOPIC]
        adjustment = [log for log in logs if log["topics"][0] == TOKENOMICS_ADJUSTMENT]
        assert len(fee) == int(has_fee)
        assert len(excess) == len(adjustment) == int(has_excess)
        assert len(logs) == int(has_fee) + 2 * int(has_excess)
        if fee:
            assert fee[0]["address"].lower() == EXCHANGE
            assert [int(topic, 16) for topic in fee[0]["topics"][1:]] == [int(STAKING, 16)]
            assert data_words(fee[0]["data"]) == [pinned_fee, pinned_fee]
        if excess:
            assert excess[0]["address"].lower() == EXCHANGE
            assert [int(topic, 16) for topic in excess[0]["topics"][1:]] == [int(STAKING, 16)]
            assert data_words(excess[0]["data"]) == [pinned_excess, pinned_excess, 0]
            assert adjustment[0]["address"].lower() == TOKENOMICS
            assert data_words(adjustment[0]["data"])[0] == pinned_excess
    assert saved["cases"]["baseline_outsider"]["logs"] == saved["cases"]["baseline_staking"]["logs"]
    baseline = saved["cases"]["baseline_staking"]
    pre, post = baseline["pre_storage"], baseline["post_storage"]
    def delta(address, slot, low128=False):
        key = word(slot)
        before = int(pre[address][key], 16)
        after = int(post[address][key], 16)
        return ((after & (2**128 - 1)) - (before & (2**128 - 1))) if low128 else after - before
    assert delta(EXCHANGE, 22, True) == pinned_fee + pinned_excess
    assert delta(EXCHANGE, 26, True) == -pinned_fee
    assert delta(EXCHANGE, fee_slot()) == pinned_fee + pinned_excess
    assert delta(TOKENOMICS, 3) == -pinned_excess

    logs = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    fee_logs = [log for log in logs if log["address"].lower() == EXCHANGE
                and log["topics"][0] == FEE_TOPIC]
    excess_logs = [log for log in logs if log["address"].lower() == EXCHANGE
                   and log["topics"][0] == EXCESS_TOPIC]
    assert len(fee_logs) == 5 and len(excess_logs) == 4
    assert {log["transactionHash"] for log in excess_logs}.issubset(
        {log["transactionHash"] for log in fee_logs})
    historical = []
    for event in fee_logs:
        tx = event["transactionHash"]
        trace = json.loads((TOKENOMICS_ARTIFACTS / f"{tx}.calls.json").read_text())
        receipt = json.loads((TOKENOMICS_ARTIFACTS / f"{tx}.receipt.json").read_text())
        pushes = [child for child in descendants(trace)
                  if child.get("to", "").lower() == EXCHANGE
                  and child.get("input", "")[:10] == SELECTOR]
        assert len(pushes) == 1 and pushes[0].get("error") is None
        push = pushes[0]
        getter = [child for child in descendants(push)
                  if child.get("to", "").lower() == TOKENOMICS
                  and child.get("input", "")[:10] == "0xae745703"]
        assert len(getter) in (1, 2)
        observed_fee = data_words(event["data"])
        assert len(event["topics"]) == 2 and int(event["topics"][1], 16) == int(STAKING, 16)
        assert observed_fee[0] == observed_fee[1] > 0
        other = [log for log in receipt["logs"] if log["address"].lower() == EXCHANGE
                 and log["topics"][0] == EXCESS_TOPIC]
        observed_excess = int(getter[0]["output"], 16)
        assert [int(child["output"], 16) for child in getter] == (
            [observed_excess, 0] if observed_excess else [0])
        assert len(other) == int(observed_excess > 0)
        if other:
            assert data_words(other[0]["data"]) == [observed_excess, observed_excess, 0]
            assert int(other[0]["topics"][1], 16) == int(STAKING, 16)
        distributed = [log for log in receipt["logs"] if log["address"].lower() == STAKING
                       and log["topics"][0] == STAKING_DISTRIBUTED]
        assert len(distributed) == 1
        fields = data_words(distributed[0]["data"])
        assert fields[1] == fields[2] == observed_fee[0] + observed_excess
        historical.append({"tx": tx, "block": int(receipt["blockNumber"], 16),
                           "fee": str(observed_fee[0]), "excess": str(observed_excess),
                           "distributed": str(fields[1])})
    assert sum(row["excess"] == "0" for row in historical) == 1
    assert next(row for row in historical if row["excess"] == "0")["tx"] == NO_EXCESS_TX
    result = {"pin_block": PIN, "exchange_proxy": EXCHANGE,
              "implementation": EXCHANGE_IMPLEMENTATION, "staking_proxy": STAKING,
              "tokenomics_proxy": TOKENOMICS, "selector_reconstructions": {SELECTOR: SIGNATURE},
              "event_catalog": [{"topic0": FEE_TOPIC, "reconstructed_signature": FEE_SIGNATURE,
                                 "status": "observed_historical"},
                                {"topic0": EXCESS_TOPIC, "reconstructed_signature": EXCESS_SIGNATURE,
                                 "status": "observed_historical"}],
              "historical_push_count": len(historical), "historical_excess_count": 4,
              "historical": sorted(historical, key=lambda row: row["tx"]),
              "pinned_probe_count": len(saved["cases"]),
              "pinned_fee": str(pinned_fee), "pinned_excess": str(pinned_excess),
              "pinned_total_credit": str(pinned_fee + pinned_excess),
              "pinned_outsider_allowed": True,
              "pinned_storage_effects": {
                  "total_balances_increase": str(pinned_fee + pinned_excess),
                  "staking_balance_increase": str(pinned_fee + pinned_excess),
                  "staker_fee_accumulator_decrease": str(pinned_fee),
                  "tokenomics_tracked_lp_decrease": str(pinned_excess)},
              "limits": ["The event argument names beyond their checked relationships remain uncertain.",
                         "The permissionless caller probe proves the pinned state only.",
                         "Five historical transactions and five read-only pinned probes do not cover all future balances."]}
    (ATLAS / "exchange_staker_fee_push_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange staker fee push:", len(historical), "historical,",
          len(saved["cases"]), "pinned probes, two event hashes verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
