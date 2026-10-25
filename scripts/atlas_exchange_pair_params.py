#!/usr/bin/env python3
"""Check the unnamed Exchange two-field admin configuration path."""

import argparse
import datetime
import json
import os
import pathlib

from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
ARTIFACT = ROOT / "artifacts" / "exchange_pair_params" / "pinned_probes.json"
HISTORY_ARTIFACT = ARTIFACT.parent / "full_history_event_query.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
HISTORICAL_TX = "0xacb4196d218190144cf1c12c5a2316e4e053cec274ac3981f79f733cb2857d1a"
PIN = 48902346
SETTER = "0x82f47a3f"
GETTER = "0x1b7c1009"
EVENT = "0x5bcf15b0a82479fbcfcb086707ad8be24c96d445448a1f625310e1c3fe491759"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
KEEPER = "0x3721476de31190dc1af8908026abe20efe25cf99"
OUTSIDER = "0x1111111111111111111111111111111111111111"
SLOT = "0x" + (28).to_bytes(32, "big").hex()
MASK = (1 << 128) - 1


def word(value):
    return "0x" + value.to_bytes(32, "big").hex()


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def events(call):
    result = list(call.get("logs", []))
    for child in call.get("calls", []):
        result.extend(events(child))
    return result


def cases(current):
    return {
        "owner_distinct": (OWNER, (12 * 10**18, 2_000 * 10**18)),
        "keeper_distinct": (KEEPER, (13 * 10**18, 3_000 * 10**18)),
        "outsider_distinct": (OUTSIDER, (12 * 10**18, 2_000 * 10**18)),
        "keeper_zero": (KEEPER, (0, 0)),
        "owner_current": (OWNER, current),
    }


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    raw = rpc(url, "eth_getStorageAt", [PROXY, hex(28), hex(PIN)])
    getter = rpc(url, "eth_call", [{"to": PROXY, "data": GETTER}, hex(PIN)])
    current = (int(raw, 16) & MASK, int(raw, 16) >> 128)
    records = {}
    for name, (sender, pair) in cases(current).items():
        data = SETTER + "".join(word(value)[2:] for value in pair)
        call = {"to": PROXY, "from": sender, "data": data}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                    {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        row = {"sender": sender, "pair": [str(x) for x in pair], "calldata": data,
               "error": trace.get("error"), "output": trace.get("output", ""),
               "implementation_calls": [{"type": child["type"], "to": child["to"],
                                          "input": child["input"]} for child in trace.get("calls", [])],
               "logs": events(trace)}
        if name in ("owner_distinct", "keeper_distinct", "keeper_zero", "owner_current"):
            diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                       {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            row["pre_storage"] = diff.get("pre", {}).get(PROXY, {}).get("storage", {})
            row["post_storage"] = diff.get("post", {}).get(PROXY, {}).get("storage", {})
        records[name] = row
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                    "slot_28": raw, "getter_output": getter,
                                    "cases": records}, indent=2) + "\n")



def capture_history():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    block_hash = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"]
    assert block_hash == manifest["block_hash"]
    params = [{"fromBlock": "0x0", "toBlock": hex(PIN), "address": PROXY, "topics": [EVENT]}]
    logs = rpc(url, "eth_getLogs", params)
    assert all(log["address"].lower() == PROXY and log["topics"] == [EVENT] for log in logs)
    HISTORY_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    HISTORICAL.mkdir(parents=True, exist_ok=True)
    HISTORY_ARTIFACT.write_text(json.dumps({
        "queried_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pin": PIN, "block_hash": block_hash, "method": "eth_getLogs", "params": params,
        "result": logs}, indent=2) + "\n")
    for log in logs:
        tx = log["transactionHash"]
        paths = {"calls": HISTORICAL / f"{tx}.calls.json",
                 "receipt": HISTORICAL / f"{tx}.receipt.json",
                 "state_diff": HISTORICAL / f"{tx}.state_diff.json"}
        if all(path.exists() for path in paths.values()):
            continue
        call = rpc(url, "debug_traceTransaction", [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        receipt = rpc(url, "eth_getTransactionReceipt", [tx])
        diff = rpc(url, "debug_traceTransaction", [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
        assert call["to"].lower() == PROXY and call["input"][:10] == SETTER
        assert receipt["transactionHash"].lower() == tx.lower() and int(receipt["status"], 16) == 1
        assert any(row["logIndex"] == log["logIndex"] and row["topics"] == [EVENT]
                   and row["data"] == log["data"] for row in receipt["logs"])
        assert SLOT in diff["post"][PROXY]["storage"]
        for kind, data in (("calls", call), ("receipt", receipt), ("state_diff", diff)):
            if not paths[kind].exists():
                paths[kind].write_text(json.dumps(data, indent=2) + "\n")

def verify():
    saved = json.loads(ARTIFACT.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    current = (int(saved["slot_28"], 16) & MASK, int(saved["slot_28"], 16) >> 128)
    assert words(saved["getter_output"]) == list(current)
    trace_catalog = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
    getter = next(row for row in trace_catalog[IMPLEMENTATION]["views"] if row["selector"] == GETTER)
    assert getter["direct_slots"] == [28] and not getter["failed"]
    assert saved["getter_output"].startswith(getter["return_prefix"])

    historical_call = json.loads((HISTORICAL / f"{HISTORICAL_TX}.calls.json").read_text())
    historical_receipt = json.loads((HISTORICAL / f"{HISTORICAL_TX}.receipt.json").read_text())
    historical_diff = json.loads((HISTORICAL / f"{HISTORICAL_TX}.state_diff.json").read_text())
    assert historical_call["to"].lower() == PROXY and historical_call["from"].lower() == KEEPER
    assert historical_call["input"][:10] == SETTER
    historical_pair = words("0x" + historical_call["input"][10:])
    assert historical_pair == [10**18, 5_000 * 10**18]
    historical_post = int(historical_diff["post"][PROXY]["storage"][SLOT], 16)
    assert historical_post == historical_pair[0] | (historical_pair[1] << 128)
    historical_logs = [log for log in historical_receipt["logs"] if log["topics"][0] == EVENT]
    assert len(historical_logs) == 1 and historical_logs[0]["topics"] == [EVENT]
    assert words(historical_logs[0]["data"]) == historical_pair

    history = json.loads(HISTORY_ARTIFACT.read_text())
    assert history["pin"] == PIN and history["block_hash"] == manifest["block_hash"]
    assert history["method"] == "eth_getLogs"
    assert history["params"] == [{"fromBlock": "0x0", "toBlock": hex(PIN),
                                  "address": PROXY, "topics": [EVENT]}]
    logs = history["result"]
    assert len(logs) == 4 and logs[0]["transactionHash"] == HISTORICAL_TX
    assert [int(row["blockNumber"], 16) for row in logs] == sorted(int(row["blockNumber"], 16) for row in logs)
    assert len({row["transactionHash"] for row in logs}) == len(logs)
    updates = []
    for log in logs:
        tx = log["transactionHash"]
        call = json.loads((HISTORICAL / f"{tx}.calls.json").read_text())
        receipt = json.loads((HISTORICAL / f"{tx}.receipt.json").read_text())
        diff = json.loads((HISTORICAL / f"{tx}.state_diff.json").read_text())
        pair = words(log["data"])
        expected_input = SETTER + "".join(word(value)[2:] for value in pair)
        assert log["address"].lower() == PROXY and log["topics"] == [EVENT]
        assert len(pair) == 2 and all(0 <= value < 2**128 for value in pair)
        assert call["to"].lower() == PROXY and call["from"].lower() == KEEPER
        assert call["input"] == expected_input and len(call.get("calls", [])) == 1
        assert call["calls"][0]["type"] == "DELEGATECALL"
        assert call["calls"][0]["to"].lower() == IMPLEMENTATION
        assert receipt["transactionHash"].lower() == tx and int(receipt["status"], 16) == 1
        assert int(receipt["blockNumber"], 16) == int(log["blockNumber"], 16)
        assert any(row["logIndex"] == log["logIndex"] and row["topics"] == [EVENT]
                   and row["data"] == log["data"] for row in receipt["logs"])
        assert set(diff["post"][PROXY]["storage"]) == {SLOT}
        pre = int(diff["pre"][PROXY]["storage"][SLOT], 16)
        post = int(diff["post"][PROXY]["storage"][SLOT], 16)
        assert post == pair[0] | (pair[1] << 128) and pre != post
        if updates:
            assert pre == int(updates[-1]["post_word"], 16)
        updates.append({"tx": tx, "block": int(log["blockNumber"], 16),
                        "caller": call["from"].lower(), "pair": [str(value) for value in pair],
                        "pre_word": word(pre), "post_word": word(post)})
    assert updates[0]["pair"] == [str(value) for value in historical_pair]
    assert updates[-1]["pair"] == [str(value) for value in current]
    assert int(updates[-1]["post_word"], 16) == int(saved["slot_28"], 16)

    probes = saved["cases"]
    assert set(probes) == set(cases(current))
    for name, (sender, pair) in cases(current).items():
        row = probes[name]
        assert row["sender"] == sender and [int(x) for x in row["pair"]] == list(pair)
        assert row["calldata"] == SETTER + "".join(word(value)[2:] for value in pair)
        assert len(row["implementation_calls"]) == 1
        child = row["implementation_calls"][0]
        assert child["type"] == "DELEGATECALL" and child["to"].lower() == IMPLEMENTATION
        assert child["input"] == row["calldata"]
    for name in ("owner_distinct", "keeper_distinct", "keeper_zero", "owner_current"):
        row = probes[name]
        assert row["error"] is None
        logs = [log for log in row["logs"] if log["address"].lower() == PROXY]
        assert len(logs) == 1 and logs[0]["topics"] == [EVENT]
        assert words(logs[0]["data"]) == [int(x) for x in row["pair"]]
        expected = int(row["pair"][0]) | (int(row["pair"][1]) << 128)
        actual = int(row["post_storage"].get(SLOT, saved["slot_28"] if name == "owner_current" else "0x0"), 16)
        assert actual == expected, name
    outsider = probes["outsider_distinct"]
    assert outsider["error"] == "execution reverted" and outsider["output"][:10] == "0x989c4c7c"
    assert not outsider["logs"]
    result = {"pin_block": PIN, "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
              "setter_selector": SETTER, "getter_selector": GETTER, "event_topic0": EVENT,
              "storage_slot": 28, "layout": "first uint128 low; second uint128 high",
              "historical_transaction": HISTORICAL_TX, "historical_pair": [str(x) for x in historical_pair],
              "historical_update_count": len(updates), "historical_updates": updates,
              "historical_event_query": "../../artifacts/exchange_pair_params/full_history_event_query.json",
              "pinned_pair": [str(x) for x in current], "probe_count": len(probes),
              "authorized_callers_tested": [OWNER, KEEPER], "outsider_revert": "0x989c4c7c",
              "evidence": "../../artifacts/exchange_pair_params/pinned_probes.json",
              "limitations": ["Economic field and event source names remain unresolved.",
                              "Pinned role and zero-value calls are read-only simulations.",
                              "The four returned logs account for the saved setter sequence through the pin, but provider completeness and unlogged writes cannot be proved from this query alone."]}
    (ATLAS / "exchange_pair_params_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange pair params:", len(updates), "historical keeper writes and", len(probes), "pinned probes verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-history", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    if args.capture_history:
        capture_history()
    verify()
