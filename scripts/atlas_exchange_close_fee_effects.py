#!/usr/bin/env python3
"""Isolate the signed-close profit fee in an archived Exchange replay."""

import argparse
import json
import os
import pathlib

from atlas_exchange_queue_append import BLOCK, BLOCK_HASH, PROXY, assert_baseline, close_call, historical_bbo
from atlas_exchange_queue_harvest import ordered_logs, words
from atlas_exchange_queue_layout import ENQUEUES, TOPIC
from atlas_oracle_behavior import PRE_BBO, returndata
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_close_fee_effects" / "local_probes.json"
BEHAVIOR = ATLAS / "exchange_close_fee_effects_behavior.json"
DIRECT_ARTIFACT = ROOT / "artifacts" / "exchange_close_fee_effects" / "direct_local_probes.json"
POSITION_CLOSED = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
SETTLED = "0xa32e4800a59f03b131f5fea90951bdf00d8d505ad98f48ece29d8620a0bf09b0"
RATE = 2 * 10**16
DIRECT_BLOCK = 48902089
DIRECT_TX = "0x30639f82f9eb58fc815fb48b302ea732eed1bff5e755a92835b0b1f97c818acf"
CASES = {
    "baseline": {23: RATE, 24: RATE, 25: RATE},
    "slot23_zero": {23: 0, 24: RATE, 25: RATE},
    "slot23_double": {23: 2 * RATE, 24: RATE, 25: RATE},
    "slot24_zero": {23: RATE, 24: 0, 25: RATE},
    "slot24_one": {23: RATE, 24: 1, 25: RATE},
    "slot24_three": {23: RATE, 24: 3, 25: RATE},
    "slot24_double": {23: RATE, 24: 2 * RATE, 25: RATE},
    "slot25_zero": {23: RATE, 24: RATE, 25: 0},
}
DIRECT_CASES = {
    "baseline": {23: RATE, 24: RATE, 25: RATE},
    "slot23_zero": {23: 0, 24: RATE, 25: RATE},
    "slot23_double": {23: 2 * RATE, 24: RATE, 25: RATE},
    "slot24_zero": {23: RATE, 24: 0, 25: RATE},
    "slot24_one": {23: RATE, 24: 1, 25: RATE},
    "slot24_three": {23: RATE, 24: 3, 25: RATE},
    "slot24_double": {23: RATE, 24: 2 * RATE, 25: RATE},
    "slot25_zero": {23: RATE, 24: RATE, 25: 0},
}


def word(value):
    return f"0x{value:064x}"


def exchange_logs(root):
    return [row for row in ordered_logs(root) if row["address"].lower() == PROXY]


def descendants(root):
    yield root
    for child in root.get("calls", []):
        yield from descendants(child)


def capture(url):
    archive = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    assert rpc(url, "eth_getBlockByNumber", [hex(BLOCK), False])["hash"] == BLOCK_HASH
    assert rpc(archive, "eth_getBlockByNumber", [hex(BLOCK), False])["hash"] == BLOCK_HASH
    assert int(rpc(url, "eth_blockNumber", []), 16) == BLOCK
    assert int(rpc(url, "eth_chainId", []), 16) == 999
    base = {slot: rpc(archive, "eth_getStorageAt", [PROXY, word(slot), hex(BLOCK)])
            for slot in (23, 24, 25)}
    assert all(int(value, 16) == RATE for value in base.values())
    assert all(rpc(url, "eth_getStorageAt", [PROXY, word(slot), hex(BLOCK)]) == value
               for slot, value in base.items())
    call = close_call()
    bid, ask = historical_bbo()
    rpc(url, "anvil_setCode", [PRE_BBO, returndata(bid, ask)])
    options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
    diff_options = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
    records = []
    try:
        for label, rates in CASES.items():
            for slot, value in rates.items():
                rpc(url, "anvil_setStorageAt", [PROXY, word(slot), word(value)])
            trace = rpc(url, "debug_traceCall", [call, hex(BLOCK), options])
            diff = rpc(url, "debug_traceCall", [call, hex(BLOCK), diff_options])
            records.append({"label": label, "rates": {str(slot): str(value) for slot, value in rates.items()},
                            "trace": trace, "diff": diff})
    finally:
        for slot, value in base.items():
            rpc(url, "anvil_setStorageAt", [PROXY, word(slot), value])
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"block": BLOCK, "block_hash": BLOCK_HASH, "chain_id": 999,
                                    "exchange": PROXY, "source_tx": ENQUEUES[0][0],
                                    "source": "archive-backed Anvil fork with original signed call and mocked historical HyperCore BBO",
                                    "call": call, "historical_bbo": [bid, ask],
                                    "base_slots": {str(slot): value for slot, value in base.items()},
                                    "records": records}, indent=2) + "\n")


def capture_direct(url):
    archive = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    hashes = {name: rpc(rpc_url, "eth_getBlockByNumber", [hex(DIRECT_BLOCK), False])["hash"]
              for name, rpc_url in (("archive", archive), ("local", url))}
    assert hashes["archive"] == hashes["local"]
    assert int(rpc(url, "eth_blockNumber", []), 16) == DIRECT_BLOCK
    assert int(rpc(url, "eth_chainId", []), 16) == 999
    base = {slot: rpc(archive, "eth_getStorageAt", [PROXY, word(slot), hex(DIRECT_BLOCK)])
            for slot in (23, 24, 25, 26)}
    assert all(int(base[slot], 16) == RATE for slot in (23, 24, 25))
    assert all(rpc(url, "eth_getStorageAt", [PROXY, word(slot), hex(DIRECT_BLOCK)]) == value
               for slot, value in base.items())
    original = json.loads((ROOT / "artifacts" / "historical" / f"{DIRECT_TX}.calls.json").read_text())
    precompile = [node for node in descendants(original) if node.get("to", "").lower() == PRE_BBO]
    assert len(precompile) == 1
    pair = words(precompile[0]["output"])
    assert len(pair) == 2 and pair[0] <= pair[1]
    rpc(url, "anvil_setCode", [PRE_BBO, returndata(*pair)])
    call = {"from": original["from"], "to": original["to"],
            "data": original["input"], "gas": "0x989680"}
    options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
    diff_options = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
    records = []
    try:
        for label, rates in DIRECT_CASES.items():
            for slot, value in rates.items():
                rpc(url, "anvil_setStorageAt", [PROXY, word(slot), word(value)])
            records.append({"label": label,
                            "rates": {str(slot): str(value) for slot, value in rates.items()},
                            "trace": rpc(url, "debug_traceCall", [call, hex(DIRECT_BLOCK), options]),
                            "diff": rpc(url, "debug_traceCall", [call, hex(DIRECT_BLOCK), diff_options])})
    finally:
        for slot in (23, 24, 25):
            rpc(url, "anvil_setStorageAt", [PROXY, word(slot), base[slot]])
    DIRECT_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    DIRECT_ARTIFACT.write_text(json.dumps({"block": DIRECT_BLOCK, "block_hashes": hashes,
                                           "chain_id": 999, "exchange": PROXY, "source_tx": DIRECT_TX,
                                           "source": "archive-backed Anvil fork with original signed call and mocked historical HyperCore BBO",
                                           "call": call, "historical_bbo": pair,
                                           "base_slots": {str(slot): value for slot, value in base.items()},
                                           "records": records}, indent=2) + "\n")


def verify():
    raw = json.loads(ARTIFACT.read_text())
    assert raw["block"] == BLOCK and raw["block_hash"] == BLOCK_HASH and raw["chain_id"] == 999
    assert raw["exchange"] == PROXY and raw["source_tx"] == ENQUEUES[0][0]
    assert raw["call"] == close_call() and raw["historical_bbo"] == historical_bbo()
    assert all(int(value, 16) == RATE for value in raw["base_slots"].values())
    assert len(raw["records"]) == len(CASES)
    assert {row["label"] for row in raw["records"]} == set(CASES)
    baseline = next(row for row in raw["records"] if row["label"] == "baseline")
    assert_baseline({"block": BLOCK, "block_hash": BLOCK_HASH, "call": raw["call"],
                     "bbo_override": raw["historical_bbo"], "trace": baseline["trace"],
                     "diff": baseline["diff"]})
    closed = next(row for tx in json.loads((ATLAS / "exchange_close_paths.json").read_text())["transactions"]
                  if tx["tx"] == ENQUEUES[0][0] for row in tx["positions"])
    adjusted = closed["adjusted_pnl"]
    assert adjusted > 0
    summary = {}
    for row in raw["records"]:
        label = row["label"]
        rates = {int(slot): int(value) for slot, value in row["rates"].items()}
        assert rates == CASES[label]
        assert not row["trace"].get("error")
        logs = exchange_logs(row["trace"])
        queue = [entry for entry in logs if entry["topics"][0] == TOPIC]
        close = [entry for entry in logs if entry["topics"][0] == POSITION_CLOSED]
        assert len(queue) == len(close) == 1
        close_fields = words(close[0]["data"])
        assert close_fields[2] == adjusted
        fee = adjusted * rates[24] // 10**18
        net = adjusted - fee
        assert close_fields[4] == fee
        assert words(queue[0]["data"]) == [net]
        pre = row["diff"]["pre"][PROXY]["storage"]
        post = row["diff"]["post"][PROXY]["storage"]
        assert int(post[word(18)], 16) - int(pre.get(word(18), "0x0"), 16) == net
        summary[label] = {"slot24_rate": str(rates[24]), "adjusted_profit": str(adjusted),
                          "fee": str(fee), "queued_profit": str(net)}
    for label in ("slot23_zero", "slot23_double", "slot25_zero"):
        row = next(row for row in raw["records"] if row["label"] == label)
        assert exchange_logs(row["trace"]) == exchange_logs(baseline["trace"])
        assert row["diff"]["pre"][PROXY]["storage"] == baseline["diff"]["pre"][PROXY]["storage"]
        assert row["diff"]["post"][PROXY]["storage"] == baseline["diff"]["post"][PROXY]["storage"]
    assert summary["slot24_one"]["fee"] == "7"
    assert summary["slot24_three"]["fee"] == "23"
    direct = verify_direct()
    behavior = {"block": BLOCK, "block_hash": BLOCK_HASH, "source_tx": ENQUEUES[0][0],
                "exchange_proxy": PROXY,
                "raw_evidence": "../../artifacts/exchange_close_fee_effects/local_probes.json",
                "direct_raw_evidence": "../../artifacts/exchange_close_fee_effects/direct_local_probes.json",
                "case_count": len(CASES) + len(DIRECT_CASES), "queued_case_count": len(CASES),
                "direct_case_count": len(DIRECT_CASES), "historical_baseline_matches": True,
                "direct_historical_baseline_matches": True,
                "slot23_and_25_variants_same_exchange_logs_and_storage": True,
                "formula": "fee = floor(adjusted positive PnL * slot24 / 10^18); queued profit or direct payout subtracts fee; direct fee is split floor(fee/2) and remainder",
                "cases": summary, "direct_cases": direct,
                "limits": ["The isolated fee paths cover one queued-profit close and one direct-payout close.",
                           "The local fork replays historical calldata and BBO but the changed-rate cases are simulations.",
                           "Slot 23 and the effect of slot 24 on negative PnL or other settlement branches still need separate tests."]}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print({"cases": len(CASES) + len(DIRECT_CASES),
           "queued_one_unit_rate_fee": summary["slot24_one"]["fee"],
           "direct_one_unit_rate_fee": direct["slot24_one"]["fee"],
           "both_historical_baselines_match": True})


def verify_direct():
    raw = json.loads(DIRECT_ARTIFACT.read_text())
    assert raw["block"] == DIRECT_BLOCK and set(raw["block_hashes"].values()) == {raw["block_hashes"]["archive"]}
    assert raw["chain_id"] == 999 and raw["exchange"] == PROXY and raw["source_tx"] == DIRECT_TX
    assert len(raw["records"]) == len(DIRECT_CASES)
    assert {row["label"] for row in raw["records"]} == set(DIRECT_CASES)
    assert all(int(raw["base_slots"][str(slot)], 16) == RATE for slot in (23, 24, 25))
    original = json.loads((ROOT / "artifacts" / "historical" / f"{DIRECT_TX}.calls.json").read_text())
    receipt = json.loads((ROOT / "artifacts" / "historical" / f"{DIRECT_TX}.receipt.json").read_text())
    historical_diff = json.loads((ROOT / "artifacts" / "historical" / f"{DIRECT_TX}.state_diff.json").read_text())
    assert int(receipt["blockNumber"], 16) == DIRECT_BLOCK + 1
    assert raw["call"] == {"from": original["from"], "to": original["to"],
                           "data": original["input"], "gas": "0x989680"}
    precompile = [node for node in descendants(original) if node.get("to", "").lower() == PRE_BBO]
    assert len(precompile) == 1 and raw["historical_bbo"] == words(precompile[0]["output"])
    baseline = next(row for row in raw["records"] if row["label"] == "baseline")
    assert not baseline["trace"].get("error")
    actual_logs = [(row["address"].lower(), row["topics"], row["data"])
                   for row in ordered_logs(baseline["trace"])]
    expected_logs = [(row["address"].lower(), row["topics"], row["data"])
                     for row in receipt["logs"]]
    assert actual_logs == expected_logs
    for phase in ("pre", "post"):
        assert baseline["diff"][phase][PROXY]["storage"] == historical_diff[phase][PROXY]["storage"]
    closed = next(row for tx in json.loads((ATLAS / "exchange_close_paths.json").read_text())["transactions"]
                  if tx["tx"] == DIRECT_TX for row in tx["positions"])
    assert closed["case"] == "margin_plus_positive_pnl_minus_fee_credited"
    summary = {}
    for row in raw["records"]:
        label = row["label"]
        rates = {int(slot): int(value) for slot, value in row["rates"].items()}
        assert rates == DIRECT_CASES[label] and not row["trace"].get("error")
        logs = exchange_logs(row["trace"])
        close = [entry for entry in logs if entry["topics"][0] == POSITION_CLOSED]
        settled = [entry for entry in logs if entry["topics"][0] == SETTLED]
        assert len(close) == len(settled) == 1
        close_fields, settlement = words(close[0]["data"]), words(settled[0]["data"])
        assert close_fields[2] == closed["adjusted_pnl"]
        fee = closed["adjusted_pnl"] * rates[24] // 10**18
        staker, dev = fee // 2, fee - fee // 2
        assert close_fields[4] == fee
        payout = closed["margin"] + closed["adjusted_pnl"] - fee
        assert settlement[0] == payout and settlement[2:] == [staker, dev]
        storage = row["diff"]
        pre = storage["pre"][PROXY]["storage"]
        post = storage["post"][PROXY]["storage"]
        fee_before = int(pre.get(word(26), raw["base_slots"]["26"]), 16)
        fee_after = int(post.get(word(26), raw["base_slots"]["26"]), 16)
        mask = (1 << 128) - 1
        assert (fee_after & mask) - (fee_before & mask) == staker
        assert (fee_after >> 128) - (fee_before >> 128) == dev
        summary[label] = {"slot24_rate": str(rates[24]), "adjusted_profit": str(closed["adjusted_pnl"]),
                          "fee": str(fee), "payout": str(payout),
                          "staker_fee": str(staker), "dev_fee": str(dev)}
    for label in ("slot23_zero", "slot23_double", "slot25_zero"):
        row = next(row for row in raw["records"] if row["label"] == label)
        assert exchange_logs(row["trace"]) == exchange_logs(baseline["trace"])
        for phase in ("pre", "post"):
            assert row["diff"][phase][PROXY]["storage"] == baseline["diff"][phase][PROXY]["storage"]
    assert summary["slot24_one"]["fee"] == "6"
    assert summary["slot24_three"]["fee"] == "20"
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-rpc-url", help="Archive-backed Anvil URL at block 48,173,880")
    parser.add_argument("--local-direct-rpc-url", help="Archive-backed Anvil URL at block 48,902,089")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    if args.local_direct_rpc_url:
        capture_direct(args.local_direct_rpc_url)
    verify()
