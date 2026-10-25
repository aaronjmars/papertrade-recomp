#!/usr/bin/env python3
"""Replay a mixed gain/loss close batch and isolate its two fee rates."""

import argparse
import json
import os
import pathlib

from atlas_exchange_close_paths import signed
from atlas_exchange_queue_harvest import ordered_logs, words
from atlas_oracle_behavior import returndata
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_negative_close" / "local_probes.json"
BEHAVIOR = ATLAS / "exchange_negative_close_fee_behavior.json"
TX = "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5"
PRIOR = 48901630
TARGET = PRIOR + 1
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
CLOSE_ACCOUNT = "0xed722c96"
POSITION_CLOSED = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
SETTLED = "0xa32e4800a59f03b131f5fea90951bdf00d8d505ad98f48ece29d8620a0bf09b0"
RATE = 2 * 10**16
CASES = {
    "baseline": {23: RATE, 24: RATE, 25: RATE},
    "slot23_zero": {23: 0, 24: RATE, 25: RATE},
    "slot23_one": {23: 1, 24: RATE, 25: RATE},
    "slot23_three": {23: 3, 24: RATE, 25: RATE},
    "slot23_double": {23: 2 * RATE, 24: RATE, 25: RATE},
    "slot24_zero": {23: RATE, 24: 0, 25: RATE},
    "slot24_one": {23: RATE, 24: 1, 25: RATE},
    "slot24_three": {23: RATE, 24: 3, 25: RATE},
    "slot24_double": {23: RATE, 24: 2 * RATE, 25: RATE},
    "slot25_zero": {23: RATE, 24: RATE, 25: 0},
}


def load(path):
    return json.loads(path.read_text())


def word(value):
    return f"0x{value:064x}"


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def call_input(root):
    return {"from": root["from"], "to": root["to"], "data": root["input"], "gas": "0x989680"}


def contract_diff(diff, sender):
    result = json.loads(json.dumps(diff))
    for phase in ("pre", "post"):
        result[phase].pop("0x" + "00" * 20, None)
        result[phase].get(sender.lower(), {}).pop("balance", None)
    return result


def capture(url):
    archive = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    original = load(ROOT / "artifacts" / "historical" / f"{TX}.calls.json")
    receipt = load(ROOT / "artifacts" / "historical" / f"{TX}.receipt.json")
    prestate = load(ARTIFACT.parent / "original_prestate.json")
    differences = load(ARTIFACT.parent / "prestate_differences.json")
    assert receipt["transactionIndex"] == "0x1" and int(receipt["blockNumber"], 16) == TARGET
    assert differences["block"] == PRIOR and differences["tx"] == TX
    assert int(rpc(url, "eth_chainId", []), 16) == 999
    assert int(rpc(url, "eth_blockNumber", []), 16) == PRIOR
    prior = rpc(archive, "eth_getBlockByNumber", [hex(PRIOR), False])
    target = rpc(archive, "eth_getBlockByNumber", [hex(TARGET), False])
    assert rpc(url, "eth_getBlockByNumber", [hex(PRIOR), False])["hash"] == prior["hash"]
    assert receipt["blockHash"] == target["hash"]

    for row in differences["differences"]:
        address = row["address"]
        assert address in prestate
        for slot, values in row["storage"].items():
            assert prestate[address]["storage"][slot] == values["archive_tx_pre"]
            assert rpc(url, "eth_getStorageAt", [address, slot, hex(PRIOR)]) == values["prior_block_fork"]
            rpc(url, "anvil_setStorageAt", [address, slot, values["archive_tx_pre"]])
        for field, values in row["account"].items():
            assert prestate[address][field] == values["archive_tx_pre"]
            assert field == "balance"
            assert rpc(url, "eth_getBalance", [address, hex(PRIOR)]) == values["prior_block_fork"]
            rpc(url, "anvil_setBalance", [address, values["archive_tx_pre"]])

    mock_responses = {}
    for suffix in ("080e", "0801"):
        nodes = [node for node in descendants(original)
                 if node.get("to", "").lower().endswith(suffix)]
        outputs = {node["output"] for node in nodes}
        assert len(outputs) == 1 and nodes
        output = next(iter(outputs))
        values = [int(output[i:i + 64], 16) for i in range(2, len(output), 64)]
        assert len(values) == (2 if suffix == "080e" else 3)
        rpc(url, "anvil_setCode", [nodes[0]["to"], returndata(*values)])
        mock_responses[suffix] = {"address": nodes[0]["to"], "output": output}

    rpc(url, "anvil_setNextBlockTimestamp", [int(target["timestamp"], 16)])
    rpc(url, "anvil_setNextBlockBaseFeePerGas", [target["baseFeePerGas"]])
    rpc(url, "evm_mine", [])
    local_target = rpc(url, "eth_getBlockByNumber", [hex(TARGET), False])
    assert int(rpc(url, "eth_blockNumber", []), 16) == TARGET
    assert all(local_target[key] == target[key] for key in ("number", "timestamp", "baseFeePerGas"))
    assert all(int(rpc(url, "eth_getStorageAt", [EXCHANGE, word(slot), hex(TARGET)]), 16) == RATE
               for slot in (23, 24, 25))

    call = call_input(original)
    records = []
    try:
        for label, rates in CASES.items():
            for slot, value in rates.items():
                rpc(url, "anvil_setStorageAt", [EXCHANGE, word(slot), word(value)])
            records.append({"label": label, "rates": {str(k): str(v) for k, v in rates.items()},
                            "trace": rpc(url, "debug_traceCall", [call, hex(TARGET),
                                          {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
                            "diff": rpc(url, "debug_traceCall", [call, hex(TARGET),
                                         {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])})
    finally:
        for slot in (23, 24, 25):
            rpc(url, "anvil_setStorageAt", [EXCHANGE, word(slot), word(RATE)])
    ARTIFACT.write_text(json.dumps({"source_tx": TX, "prior_block": PRIOR,
                                    "prior_hash": prior["hash"], "target_block": TARGET,
                                    "target_hash": target["hash"],
                                    "target_timestamp": target["timestamp"],
                                    "target_base_fee": target["baseFeePerGas"],
                                    "local_target_hash": local_target["hash"],
                                    "prestate_difference_file": "prestate_differences.json",
                                    "mock_responses": mock_responses, "call": call,
                                    "records": records}, indent=2) + "\n")
    verify()


def verify():
    raw = load(ARTIFACT)
    original = load(ROOT / "artifacts" / "historical" / f"{TX}.calls.json")
    receipt = load(ROOT / "artifacts" / "historical" / f"{TX}.receipt.json")
    historical_diff = load(ROOT / "artifacts" / "historical" / f"{TX}.state_diff.json")
    close_paths = load(ATLAS / "exchange_close_paths.json")
    tx_paths = next(row for row in close_paths["transactions"] if row["tx"] == TX)
    assert raw["source_tx"] == TX and raw["prior_block"] == PRIOR and raw["target_block"] == TARGET
    assert raw["target_hash"] == receipt["blockHash"] and raw["call"] == call_input(original)
    assert len(raw["records"]) == len(CASES)
    baseline = next(row for row in raw["records"] if row["label"] == "baseline")
    assert not baseline["trace"].get("error")
    baseline_logs = ordered_logs(baseline["trace"])
    assert [(x["address"].lower(), x["topics"], x["data"]) for x in baseline_logs] == [
        (x["address"].lower(), x["topics"], x["data"]) for x in receipt["logs"]]
    assert contract_diff(baseline["diff"], original["from"]) == contract_diff(historical_diff, original["from"])

    summary = {}
    base_balances = None
    for row in raw["records"]:
        label = row["label"]
        rates = {int(k): int(v) for k, v in row["rates"].items()}
        assert rates == CASES[label]
        assert not any(node.get("error") for node in descendants(row["trace"]))
        logs = ordered_logs(row["trace"])
        closes = [x for x in logs if x["topics"][0].lower() == POSITION_CLOSED]
        settled = [x for x in logs if x["topics"][0].lower() == SETTLED]
        assert len(closes) == len(settled) == 2
        by_user = {"0x" + x["topics"][1][-40:].lower(): words(x["data"]) for x in settled}
        accounting_calls = [node for node in descendants(row["trace"])
                            if node.get("to", "").lower() == TOKENOMICS
                            and node.get("input", "").startswith(CLOSE_ACCOUNT)]
        assert len(accounting_calls) == 2
        accounting = {}
        for node in accounting_calls:
            data = node["input"]
            fields = [int(data[i:i + 64], 16) for i in range(10, len(data), 64)]
            assert len(fields) == 4
            accounting["0x" + f"{fields[0]:040x}"] = fields[1:]
        positions = []
        for log in closes:
            position_id = int(log["topics"][1], 16)
            path = next(x for x in tx_paths["positions"] if x["position_id"] == position_id)
            values = words(log["data"])
            assert signed(values[2]) == path["adjusted_pnl"]
            pnl = path["adjusted_pnl"]
            fee = abs(pnl) * rates[24 if pnl > 0 else 23] // 10**18
            assert values[4] == fee
            aggregate = by_user[path["user"]]
            assert aggregate[2] == fee // 2 and aggregate[3] == fee - fee // 2
            expected_credit = path["margin"] + pnl - (fee if pnl > 0 else 0)
            assert aggregate[0] == expected_credit
            debit, mint_basis, tracked_credit = accounting[path["user"]]
            if pnl > 0:
                assert (debit, mint_basis, tracked_credit) == (pnl, 0, 0)
            else:
                assert (debit, mint_basis, tracked_credit) == (0, -pnl - fee, -pnl - fee)
            positions.append({"position_id": position_id, "adjusted_pnl": str(pnl),
                              "fee": str(fee), "user_balance_credit": str(aggregate[0]),
                              "staker_fee": str(aggregate[2]), "dev_fee": str(aggregate[3]),
                              "tokenomics_debit": str(debit), "tokenomics_mint_basis": str(mint_basis),
                              "tokenomics_tracked_credit": str(tracked_credit)})
        assert [x["position_id"] for x in positions] == [1392206, 1392921]
        balances = [x["user_balance_credit"] for x in positions]
        if label == "baseline":
            base_balances = balances
        if label.startswith("slot23"):
            assert balances[0] == base_balances[0] and balances[1] == base_balances[1]
        if label.startswith("slot24"):
            assert balances[1] == base_balances[1]
        if label == "slot25_zero":
            assert [(x["address"], x["topics"], x["data"]) for x in logs] == [
                (x["address"], x["topics"], x["data"]) for x in baseline_logs]
            assert row["diff"] == baseline["diff"]
        summary[label] = positions

    behavior = {"source_tx": TX, "target_block": TARGET, "target_hash": raw["target_hash"],
                "case_count": len(CASES), "historical_baseline_logs_match": True,
                "historical_baseline_contract_state_match": True,
                "positive_fee_slot": 24, "negative_fee_slot": 23,
                "fee_denominator": str(10**18), "slot25_zero_same_logs_and_state": True,
                "negative_user_credit_independent_of_fee": True,
                "negative_loss_allocation": "trader loss = Exchange fee accrual + Tokenomics tracked LP credit; PAPER mint basis equals tracked LP credit",
                "cases": summary,
                "limits": ["The HyperCore BBO and balance precompiles were mocked with their archived responses.",
                           "The EVM accounting source of the loss fee is the LP share of the trader loss. HyperCore settlement is separate and was not verified here.",
                           "This verifies one historical mixed gain/loss batch and controlled local rate changes, not every close branch."]}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print(f"verified {len(CASES)} mixed-close cases; historical logs and contract state match")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-rpc-url")
    args = parser.parse_args()
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    else:
        verify()
