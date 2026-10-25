#!/usr/bin/env python3
"""Capture and verify Exchange CoreWithdrawal logs through the pinned block."""

import argparse
import collections
import concurrent.futures
import datetime
import json
import os
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_core_withdrawal" / "full_history_event_query.json"
SAMPLE = ARTIFACT.parent / "sample_transactions.json"
PIN = 48902346
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOPIC = "0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75"
CREATION = 47854719
WINDOW = 100000


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(os.environ["PAPERTRADE_ARCHIVE_RPC"], body,
                                     {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            result = json.loads(error.read().decode())
        except json.JSONDecodeError:
            raise
    if "error" in result:
        raise RuntimeError(result["error"])
    return result["result"]


def fetch_range(start, end):
    params = [{"fromBlock": hex(start), "toBlock": hex(end),
               "address": EXCHANGE, "topics": [TOPIC]}]
    try:
        logs = rpc("eth_getLogs", params)
    except RuntimeError as error:
        if "Log response size exceeded" not in str(error) or start == end:
            raise
        midpoint = (start + end) // 2
        return fetch_range(start, midpoint) + fetch_range(midpoint + 1, end)
    assert all(row["address"].lower() == EXCHANGE and row["topics"][0].lower() == TOPIC
               and start <= int(row["blockNumber"], 16) <= end for row in logs)
    return [{"from_block": start, "to_block": end, "logs": logs}]


def capture():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    block_hash = rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"]
    assert block_hash == manifest["block_hash"]
    windows = []
    for start in range(CREATION, PIN + 1, WINDOW):
        windows.extend(fetch_range(start, min(PIN, start + WINDOW - 1)))
        print("captured through", windows[-1]["to_block"], "logs", sum(len(row["logs"]) for row in windows), flush=True)
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({
        "queried_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pin": PIN, "block_hash": block_hash, "contract_creation_block": CREATION,
        "event_topic0": TOPIC, "window_target": WINDOW, "windows": windows,
        "query_limit": "Provider may reject a large log response; each successful window is saved separately."
    }, indent=2) + "\n")



def selected_events(saved):
    selected = []
    for window in saved["windows"]:
        logs = window["logs"]
        if logs:
            indices = sorted({min(len(logs) - 1, j * (len(logs) - 1) // 9)
                              for j in range(10)})
            selected.extend(logs[index] for index in indices)
    return {log["transactionHash"]: log for log in selected}


def capture_sample():
    saved = json.loads(ARTIFACT.read_text())
    selected = selected_events(saved)
    txs = sorted(selected)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        transactions = list(pool.map(lambda tx: rpc("eth_getTransactionByHash", [tx]), txs))
    rows = []
    for tx, transaction in zip(txs, transactions):
        assert transaction and transaction["hash"].lower() == tx.lower()
        log = selected[tx]
        rows.append({"tx": tx, "block": int(log["blockNumber"], 16),
                     "user": "0x" + log["topics"][1][-40:],
                     "root_from": transaction["from"].lower(),
                     "root_to": transaction["to"].lower() if transaction["to"] else None,
                     "root_selector": transaction["input"][:10]})
    SAMPLE.write_text(json.dumps({
        "pin": saved["pin"], "block_hash": saved["block_hash"],
        "selection": "up to ten evenly spaced logs in each saved query window, deduplicated by transaction",
        "sample_size": len(rows), "transactions": rows}, indent=2) + "\n")

def verify():
    saved = json.loads(ARTIFACT.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin"] == PIN and saved["block_hash"] == manifest["block_hash"]
    assert saved["contract_creation_block"] == CREATION and saved["event_topic0"] == TOPIC
    assert manifest["contracts"][EXCHANGE]["origin"]["block"] == CREATION
    cursor = CREATION
    seen = set()
    count = 0
    for window in saved["windows"]:
        start, end = window["from_block"], window["to_block"]
        assert start == cursor and start <= end <= PIN
        cursor = end + 1
        for log in window["logs"]:
            assert log["address"].lower() == EXCHANGE and log["topics"][0].lower() == TOPIC
            assert start <= int(log["blockNumber"], 16) <= end
            key = (log["transactionHash"], log["logIndex"])
            assert key not in seen
            seen.add(key)
            count += 1
    assert cursor == PIN + 1
    selected = selected_events(saved)
    sample = json.loads(SAMPLE.read_text())
    assert sample["pin"] == PIN and sample["block_hash"] == saved["block_hash"]
    assert sample["sample_size"] == len(selected) == len(sample["transactions"]) == 104
    assert {row["tx"] for row in sample["transactions"]} == set(selected)
    assert all(row["block"] == int(selected[row["tx"]]["blockNumber"], 16)
               and row["user"] == "0x" + selected[row["tx"]]["topics"][1][-40:]
               for row in sample["transactions"])
    selectors = collections.Counter(row["root_selector"] for row in sample["transactions"])
    assert selectors == {"0x251fb27d": 103, "0x6a761202": 1}
    assert sum(row["root_from"] == row["user"] for row in sample["transactions"]) == 0
    assert {row["transactionHash"] for window in saved["windows"] for row in window["logs"]
            if row["topics"][1][-40:].lower() == "a90f96b5fcd5bdc0aae788c0485786b0e546d950"} == {
                "0x7c69ba558b4076ef20f880f89d910168cbd92e3cc0a2f70a564b2117f46fa6ac",
                "0xd11efba2b91838576b957f7297677b46676ec7a27db60331377212f4de8ba771"}
    print(count, "CoreWithdrawal logs across", len(saved["windows"]),
          "complete windows;", sample["sample_size"], "sampled transaction roots")
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-sample", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
        capture_sample()
    elif args.capture_sample:
        capture_sample()
    verify()
