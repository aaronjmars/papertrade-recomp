#!/usr/bin/env python3
"""Reconstruct the direct Exchange withdrawal on a pinned local HyperEVM fork."""

import argparse
import json
import os
import pathlib
import subprocess

from atlas_exchange_queue_harvest import ordered_logs, words
from atlas_oracle_behavior import returndata
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_direct_withdrawal" / "local_probes.json"
BEHAVIOR = ATLAS / "exchange_direct_withdrawal_behavior.json"
PIN = 48902346
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
USER = "0x78274a46400c83c91b7ad35dea11f01ec3894756"
SELECTOR = "0x7f99545a"
PRECOMPILE_SOURCE_TX = "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5"
HISTORICAL_DIRECT_TXS = (
    "0x7c69ba558b4076ef20f880f89d910168cbd92e3cc0a2f70a564b2117f46fa6ac",
    "0xd11efba2b91838576b957f7297677b46676ec7a27db60331377212f4de8ba771",
)
CORE_WRITER = "0x" + "33" * 20
CORE_WRITER_SELECTOR = "0x17938e13"
CORE_WITHDRAWAL = "0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75"
RAW_CASES = {"zero": 0, "one_raw_unit": 1, "at_one_usd": 1000000,
             "above_one_usd": 1000001, "two_usd": 2000000,
             "near_user_balance": 42000000, "above_user_balance": 43000000}
EXPECTED_ERRORS = {"zero": "0x0a9e0180", "one_raw_unit": "0xad21c3fb",
                   "at_one_usd": "0xad21c3fb", "above_user_balance": "0xa3b9a36c",
                   "same_block": "0x4f57ffae", "zero_core_balance": "0x0a9e0180"}
SUCCESSES = {"above_one_usd", "two_usd", "near_user_balance"}


def read(name):
    return json.loads((ATLAS / name).read_text())


def word(n):
    return f"0x{n:064x}"


def mapped(user, base):
    return subprocess.run(["cast", "index", "address", user, str(base)],
                          capture_output=True, text=True, check=True).stdout.strip().lower()


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def call(amount):
    return {"from": USER, "to": EXCHANGE, "data": SELECTOR + word(amount)[2:], "gas": "0x989680"}


def precompile_responses():
    original = json.loads((ROOT / "artifacts" / "historical" /
                           f"{PRECOMPILE_SOURCE_TX}.calls.json").read_text())
    result = {}
    for suffix in ("0810", "0801"):
        matches = [node for node in descendants(original)
                   if node.get("to", "").lower().endswith(suffix)]
        assert len(matches) == 1 and matches[0].get("output", "0x") != "0x"
        output = matches[0]["output"]
        result[suffix] = {"address": matches[0]["to"], "output": output,
                          "values": [int(output[i:i + 64], 16) for i in range(2, len(output), 64)]}
    return result


def capture(url):
    manifest = read("manifest.json")
    block = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert int(rpc(url, "eth_chainId", []), 16) == 999
    assert int(rpc(url, "eth_blockNumber", []), 16) == PIN
    assert block["hash"] == manifest["block_hash"]
    responses = precompile_responses()
    for row in responses.values():
        rpc(url, "anvil_setCode", [row["address"], returndata(*row["values"])])
    last_slot = mapped(USER, 34)
    last_before = rpc(url, "eth_getStorageAt", [EXCHANGE, last_slot, hex(PIN)])
    balance_slot = mapped(USER, 9)
    balance_before = rpc(url, "eth_getStorageAt", [EXCHANGE, balance_slot, hex(PIN)])
    records = []
    options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
    diff_options = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
    for label, amount in RAW_CASES.items():
        request = call(amount)
        trace = rpc(url, "debug_traceCall", [request, hex(PIN), options])
        row = {"label": label, "raw_amount": amount, "call": request, "trace": trace}
        if label in SUCCESSES:
            row["diff"] = rpc(url, "debug_traceCall", [request, hex(PIN), diff_options])
        records.append(row)
    try:
        rpc(url, "anvil_setStorageAt", [EXCHANGE, last_slot, word(PIN)])
        records.append({"label": "same_block", "raw_amount": 2000000,
                        "last_withdrawal_override": word(PIN),
                        "trace": rpc(url, "debug_traceCall", [call(2000000), hex(PIN), options])})
    finally:
        rpc(url, "anvil_setStorageAt", [EXCHANGE, last_slot, last_before])
    try:
        rpc(url, "anvil_setCode", [responses["0801"]["address"], returndata(0, 0, 0)])
        records.append({"label": "zero_core_balance", "raw_amount": 2000000,
                        "trace": rpc(url, "debug_traceCall", [call(2000000), hex(PIN), options])})
    finally:
        rpc(url, "anvil_setCode", [responses["0801"]["address"],
                                   returndata(*responses["0801"]["values"])])
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin": PIN, "block_hash": block["hash"],
                                    "chain_id": 999, "exchange": EXCHANGE, "user": USER,
                                    "precompile_source_tx": PRECOMPILE_SOURCE_TX,
                                    "precompile_responses": responses,
                                    "last_withdrawal_slot": last_slot,
                                    "last_withdrawal_before": last_before,
                                    "user_balance_slot": balance_slot,
                                    "user_balance_before": balance_before,
                                    "records": records}, indent=2) + "\n")
    verify()


def core_writer_payload(node):
    data = bytes.fromhex(node["input"][10:])
    offset = int.from_bytes(data[:32], "big")
    size = int.from_bytes(data[offset:offset + 32], "big")
    return data[offset + 32:offset + 32 + size]




def capture_history():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == read("manifest.json")["block_hash"]
    folder = ROOT / "artifacts" / "historical"
    folder.mkdir(parents=True, exist_ok=True)
    for tx in HISTORICAL_DIRECT_TXS:
        for kind, method, params in (
                ("calls", "debug_traceTransaction", [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
                ("receipt", "eth_getTransactionReceipt", [tx]),
                ("state_diff", "debug_traceTransaction", [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}]),
                ("prestate", "debug_traceTransaction", [tx, {"tracer": "prestateTracer"}])):
            path = folder / f"{tx}.{kind}.json"
            if not path.exists():
                path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")

def verify_historical_direct():
    history = json.loads((ROOT / "artifacts" / "exchange_core_withdrawal" /
                          "full_history_event_query.json").read_text())
    assert history["pin"] == PIN and history["block_hash"] == read("manifest.json")["block_hash"]
    history_logs = [row for window in history["windows"] for row in window["logs"]
                    if row["transactionHash"] in HISTORICAL_DIRECT_TXS]
    assert {row["transactionHash"] for row in history_logs} == set(HISTORICAL_DIRECT_TXS)
    rows = []
    for index, tx in enumerate(HISTORICAL_DIRECT_TXS):
        prefix = ROOT / "artifacts" / "historical" / tx
        call_trace = json.loads(pathlib.Path(str(prefix) + ".calls.json").read_text())
        receipt = json.loads(pathlib.Path(str(prefix) + ".receipt.json").read_text())
        diff = json.loads(pathlib.Path(str(prefix) + ".state_diff.json").read_text())
        assert receipt["transactionHash"].lower() == tx
        assert int(receipt["status"], 16) == 1 and int(receipt["blockNumber"], 16) <= PIN
        assert call_trace["to"].lower() == "0xa90f96b5fcd5bdc0aae788c0485786b0e546d950"
        assert call_trace["input"][:10] == "0x6a761202"
        direct = [node for node in descendants(call_trace)
                  if node.get("type") == "CALL" and node.get("to", "").lower() == EXCHANGE
                  and node.get("input", "")[:10] == SELECTOR]
        assert len(direct) == 1 and direct[0].get("error") is None
        withdrawal = direct[0]
        user = withdrawal["from"].lower()
        assert user == call_trace["to"].lower() and len(withdrawal["input"]) == 74
        raw_amount = int(withdrawal["input"][10:], 16)
        implementation = withdrawal["calls"]
        assert len(implementation) == 1 and implementation[0]["type"] == "DELEGATECALL"
        assert implementation[0]["to"].lower() == IMPLEMENTATION
        precompiles = {node["to"][-4:]: node for node in descendants(withdrawal)
                       if node.get("type") == "STATICCALL" and node.get("to", "").lower().endswith(("0810", "0801"))}
        assert set(precompiles) == {"0810", "0801"}
        status = int(precompiles["0810"]["output"], 16)
        assert status == index and int(precompiles["0801"]["output"][2:66], 16) > 0
        logs = [row for row in receipt["logs"] if row["address"].lower() == EXCHANGE
                and row["topics"][0] == CORE_WITHDRAWAL]
        assert len(logs) == 1 and logs[0]["topics"] == [CORE_WITHDRAWAL, word(int(user, 16))]
        assert any(row["transactionHash"] == tx and row["logIndex"] == logs[0]["logIndex"]
                   and row["data"] == logs[0]["data"] for row in history_logs)
        debit, sent = words(logs[0]["data"])
        assert debit == (raw_amount + (1000000 if status == 0 else 0)) * 10**12
        assert sent == raw_amount * 100
        core_calls = [node for node in descendants(withdrawal)
                      if node.get("type") == "CALL" and node.get("to", "").lower() == CORE_WRITER]
        assert len(core_calls) == 1 and core_calls[0]["input"].startswith(CORE_WRITER_SELECTOR)
        payload = core_writer_payload(core_calls[0])
        assert len(payload) == 100 and int.from_bytes(payload[-8:], "big") == sent
        assert payload[16:36].hex() == user[2:]
        before = diff["pre"][EXCHANGE]["storage"]
        after = diff["post"][EXCHANGE]["storage"]
        last_slot = mapped(user, 34)
        balance_slot = mapped(user, 9)
        expected_slots = {word(14), word(22), last_slot, balance_slot}
        assert set(before) | set(after) == expected_slots
        assert (balance_slot not in after) == (status == 1)
        assert int(before[word(14)], 16) - int(after[word(14)], 16) == debit
        assert int(before[word(22)], 16) - int(after[word(22)], 16) == debit
        balance_before = int(before[balance_slot], 16)
        balance_after = int(after.get(balance_slot, "0x0"), 16)
        assert balance_before - balance_after == debit
        if rows:
            assert balance_before == int(rows[-1]["internal_balance_post"])
        assert int(before.get(last_slot, "0x0"), 16) < int(receipt["blockNumber"], 16)
        assert int(after[last_slot], 16) == int(receipt["blockNumber"], 16)
        rows.append({"tx": tx, "block": int(receipt["blockNumber"], 16),
                     "caller": user, "raw_amount": str(raw_amount), "internal_debit": str(debit),
                     "core_amount": str(sent), "extra_debit": str(debit - raw_amount * 10**12),
                     "core_user_status_word": status, "changed_exchange_slots": sorted(set(before) | set(after)),
                     "internal_balance_pre": str(balance_before),
                     "internal_balance_post": str(balance_after),
                     "internal_balance_mapping_changed": True,
                     "internal_balance_slot_cleared": balance_slot not in after,
                     "last_withdrawal_block": int(after[last_slot], 16)})
    assert len(rows) == 2 and rows[0]["caller"] == rows[1]["caller"]
    return rows


def verify():
    raw = json.loads(ARTIFACT.read_text())
    assert raw["pin"] == PIN and raw["block_hash"] == read("manifest.json")["block_hash"]
    assert raw["chain_id"] == 999 and raw["exchange"] == EXCHANGE and raw["user"] == USER
    assert raw["precompile_source_tx"] == PRECOMPILE_SOURCE_TX
    assert raw["precompile_responses"] == precompile_responses()
    assert raw["last_withdrawal_slot"] == mapped(USER, 34)
    assert raw["user_balance_slot"] == mapped(USER, 9)
    assert int(raw["last_withdrawal_before"], 16) < PIN
    assert int(raw["user_balance_before"], 16) >= 43 * 10**18
    assert subprocess.run(["cast", "sig", "withdrawToCore(uint256)"], check=True,
                          capture_output=True, text=True).stdout.strip() == SELECTOR
    rows = {row["label"]: row for row in raw["records"]}
    assert set(rows) == set(RAW_CASES) | {"same_block", "zero_core_balance"}
    assert len(rows) == 9
    expected_topic = read("exchange_core_withdrawal_behavior.json")["event_catalog"][0]["topic0"]
    assert expected_topic == CORE_WITHDRAWAL
    results = {}
    for label, row in rows.items():
        amount = row["raw_amount"]
        assert amount == RAW_CASES.get(label, 2000000)
        if label in RAW_CASES:
            assert row["call"] == call(amount)
        trace = row["trace"]
        if label in EXPECTED_ERRORS:
            assert trace.get("error") == "execution reverted"
            assert trace.get("output", "") == EXPECTED_ERRORS[label]
            assert not ordered_logs(trace)
            results[label] = {"raw_amount": amount, "revert_selector": EXPECTED_ERRORS[label]}
            continue
        assert label in SUCCESSES and not trace.get("error")
        logs = ordered_logs(trace)
        assert len(logs) == 2
        assert logs[0]["address"].lower() == CORE_WRITER
        assert logs[1]["address"].lower() == EXCHANGE
        assert logs[1]["topics"] == [CORE_WITHDRAWAL, word(int(USER, 16))]
        debit, sent = words(logs[1]["data"])
        assert debit == (amount + 1000000) * 10**12
        assert sent == amount * 100
        core_calls = [node for node in descendants(trace)
                      if node.get("to", "").lower() == CORE_WRITER]
        assert len(core_calls) == 1 and core_calls[0]["input"].startswith(CORE_WRITER_SELECTOR)
        payload = core_writer_payload(core_calls[0])
        assert len(payload) == 100
        assert int.from_bytes(payload[-8:], "big") == sent
        assert USER[2:].lower() in payload.hex()
        diff = row["diff"]
        before = diff["pre"][EXCHANGE]["storage"]
        after = diff["post"][EXCHANGE]["storage"]
        balance_slot = raw["user_balance_slot"]
        last_slot = raw["last_withdrawal_slot"]
        assert int(before[balance_slot], 16) - int(after[balance_slot], 16) == debit
        assert int(before[word(14)], 16) - int(after[word(14)], 16) == debit
        mask = 2**128 - 1
        assert (int(before[word(22)], 16) & mask) - (int(after[word(22)], 16) & mask) == debit
        assert int(after[last_slot], 16) == PIN
        assert int(before[last_slot], 16) == int(raw["last_withdrawal_before"], 16)
        results[label] = {"raw_amount": amount, "internal_debit": str(debit),
                          "core_amount": str(sent), "extra_debit": str(debit - amount * 10**12),
                          "last_withdrawal_block": PIN}
    assert rows["same_block"]["last_withdrawal_override"] == word(PIN)
    historical_direct = verify_historical_direct()
    local_status = json.loads((ROOT / "artifacts" / "exchange_direct_status_local" / "replay.json").read_text())
    assert local_status["pin"] == PIN and local_status["block_hash"] == raw["block_hash"]
    assert local_status["forge_result"] == "4 passed, 0 failed"
    behavior = {"pin": PIN, "block_hash": raw["block_hash"], "exchange_proxy": EXCHANGE,
                "implementation": IMPLEMENTATION,
                "selector_reconstructions": {SELECTOR: "withdrawToCore(uint256)"},
                "raw_evidence": "../../artifacts/exchange_direct_withdrawal/local_probes.json",
                "probe_count": len(rows), "successful_cases": len(SUCCESSES),
                "historical_direct_call_count": len(historical_direct),
                "historical_direct_calls": historical_direct,
                "local_status_replay": "../../artifacts/exchange_direct_status_local/replay.json",
                "local_status_test_count": 4,
                "status_branch_observed": {"status_zero_debit": "(rawAmount + 1000000) * 10^12",
                                           "status_one_debit": "rawAmount * 10^12",
                                           "both_debit_internal_balance": True,
                                           "status_zero_exact_balance_reverts": True},
                "strict_minimum_raw_amount": 1000000,
                "case_results": results,
                "simulated_error_catalog": [
                    {"selector": "0x0a9e0180", "reconstructed_signature": "NoCoreBalance()",
                     "probe_paths": ["zero", "zero_core_balance"]},
                    {"selector": "0xad21c3fb", "probe_paths": ["one_raw_unit", "at_one_usd"]},
                    {"selector": "0xa3b9a36c", "probe_paths": ["above_user_balance"]},
                    {"selector": "0x4f57ffae", "probe_paths": ["same_block"]},
                ],
                "limits": ["The success path is a read-only local fork simulation using two historical HyperCore precompile responses.",
                           "Three tested direct withdrawals debit one extra internal USD. Two recent signed withdrawals in the historical ledger did not, so this result is not generalized to every withdrawal path.",
                           "The three new raw revert selectors are tied to observed branches but their Solidity error names remain unknown.",
                           "Two successful historical direct calls from the same Safe have Core user-status words 0 then 1. The second clears the internal user-balance slot to zero, which prestateTracer diffMode omits from the post map. Four same-state exact-runtime tests show status 0 charges one extra USD and rejects an exact-balance withdrawal, while status 1 debits exactly the requested amount and accepts exact balance. Other status values and downstream HyperCore settlement remain unverified."]}
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified nine local probes, four status-boundary tests, and two historical Safe calls")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-rpc-url")
    parser.add_argument("--capture-history", action="store_true")
    args = parser.parse_args()
    if args.capture_history:
        capture_history()
        print("captured two historical direct withdrawals")
    if args.local_rpc_url:
        capture(args.local_rpc_url)
    elif not args.capture_history:
        verify()
