#!/usr/bin/env python3
"""Verify Exchange queue history and partial harvests at an archived state."""

import argparse
import json
import os
import pathlib
import subprocess

from atlas_exchange_queue_layout import AMOUNT, ENQUEUES, HARVEST, KECCAK, PROXY, TOPIC, mapped, slot, storage
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_queue"
HISTORICAL = ROOT / "artifacts" / "historical"
PIN = 48902346
PROBE_BLOCK = 48173889
DEPLOY_BLOCK = 47854719
SENDER = "0x423c409deb1777960f99a72b11b976df01c40f63"
HARVESTED = "Harvested(address,uint256,uint256)"
HARVESTED_TOPIC = "0x81ca9b2c230070eaa84787556b1aaf18bf1e2f07ea5d3dae4819db77a1a5b224"
SIDE_BUCKET = "SideBucketUpdated(uint256)"
SIDE_BUCKET_TOPIC = "0xc2a40711b646c786b80242364fa8e26da64c5a4dfb2bf8fff83692db43600d89"


def probe_path(n):
    return ARTIFACTS / f"harvest_{n}_probe.json"


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    logs_path = ARTIFACTS / "enqueued_page1.json"
    query_path = ARTIFACTS / "enqueued_query.json"
    if not logs_path.exists() or not query_path.exists():
        assert os.environ.get("ETHERSCAN_API_KEY"), "set ETHERSCAN_API_KEY"
        command = ["etherscan", "logs", "get", "--chain", "999", "--address", PROXY,
                   "--topic0", TOPIC,
                   "--from-block", str(DEPLOY_BLOCK), "--to-block", str(PIN), "--page", "1", "--offset", "1000"]
        rows = json.loads(subprocess.run(command, check=True, capture_output=True, text=True, timeout=60).stdout)
        assert len(rows) < 1000, "paginate Enqueued history before treating page 1 as complete"
        logs_path.write_text(json.dumps(rows, indent=2) + "\n")
        query_path.write_text(json.dumps({"chain_id": 999, "address": PROXY,
                                          "topic0": TOPIC, "from_block": DEPLOY_BLOCK,
                                          "to_block": PIN, "page": 1, "offset": 1000,
                                          "result_count": len(rows)}, indent=2) + "\n")
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    header = rpc(url, "eth_getBlockByNumber", [hex(PROBE_BLOCK), False])
    slots = {str(i): rpc(url, "eth_getStorageAt", [PROXY, hex(i), hex(PROBE_BLOCK)])
             for i in (16, 17, 18)}
    assert [int(slots[str(i)], 16) for i in (16, 17, 18)] == [1, 4, 3 * AMOUNT]
    for n in range(4):
        path = probe_path(n)
        if path.exists():
            continue
        call = {"from": SENDER, "to": PROXY, "data": "0xddc63262" + n.to_bytes(32, "big").hex()}
        result = {"block": PROBE_BLOCK, "block_hash": header["hash"], "prestate_slots": slots, "call": call}
        for label, method, params in (
            ("output", "eth_call", [call, hex(PROBE_BLOCK)]),
            ("trace", "debug_traceCall", [call, hex(PROBE_BLOCK),
                                           {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
            ("diff", "debug_traceCall", [call, hex(PROBE_BLOCK),
                                          {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}]),
        ):
            result[label] = rpc(url, method, params)
        path.write_text(json.dumps(result, indent=2) + "\n")
    original = {str(i): int(rpc(url, "eth_getStorageAt", [PROXY, slot(i), hex(PROBE_BLOCK)]), 16)
                for i in (14, 16, 18, 22, 26, 27)}
    mask128 = (1 << 128) - 1
    reserve = (original["22"] & mask128) + (original["22"] >> 128)
    reserve += (original["26"] & mask128) + (original["26"] >> 128)
    available = 3 * 10**18
    treasury = reserve + available
    override = {PROXY: {"stateDiff": {slot(14): slot(treasury)}}}
    call = {"from": SENDER, "to": PROXY,
            "data": "0xddc63262" + (1).to_bytes(32, "big").hex(), "gas": "0x200000"}
    getter = {"to": PROXY, "data": "0x138e9de2", "gas": "0x200000"}
    partial = {"block": PROBE_BLOCK, "block_hash": header["hash"],
               "original_slots": {key: str(value) for key, value in original.items()},
               "reserve": str(reserve), "availability": str(available),
               "treasury_override": str(treasury), "call": call,
               "getter_trace": rpc(url, "debug_traceCall", [getter, hex(PROBE_BLOCK),
                                  {"tracer": "callTracer", "stateOverrides": override}]),
               "trace": rpc(url, "debug_traceCall", [call, hex(PROBE_BLOCK),
                             {"tracer": "callTracer", "tracerConfig": {"withLog": True},
                              "stateOverrides": override}]),
               "diff": rpc(url, "debug_traceCall", [call, hex(PROBE_BLOCK),
                            {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True},
                             "stateOverrides": override}])}
    (ARTIFACTS / "partial_node_historical_state.json").write_text(json.dumps(partial, indent=2) + "\n")


def ordered_logs(node):
    found = list(node.get("logs", []))
    for child in node.get("calls", []):
        found.extend(ordered_logs(child))
    return sorted(found, key=lambda row: int(row["index"], 16))


def words(value):
    return [int(value[i:i + 64], 16) for i in range(2, len(value), 64)]


def verify_partial_node(probe_hash, user):
    probe = json.loads((ARTIFACTS / "partial_node_historical_state.json").read_text())
    assert probe["block"] == PROBE_BLOCK and probe["block_hash"] == probe_hash
    original = {int(key): int(value) for key, value in probe["original_slots"].items()}
    assert set(original) == {14, 16, 18, 22, 26, 27}
    assert original[16] == 1 and original[18] == 3 * AMOUNT and original[27] > 3 * AMOUNT
    mask128 = (1 << 128) - 1
    reserve = (original[22] & mask128) + (original[22] >> 128)
    reserve += (original[26] & mask128) + (original[26] >> 128)
    paid = 3 * 10**18
    assert int(probe["reserve"]) == reserve
    assert int(probe["availability"]) == paid
    assert int(probe["treasury_override"]) == reserve + paid
    assert not probe["getter_trace"].get("error")
    assert int(probe["getter_trace"]["output"], 16) == paid
    assert probe["call"] == {"from": SENDER, "to": PROXY,
                              "data": "0xddc63262" + (1).to_bytes(32, "big").hex(),
                              "gas": "0x200000"}
    trace, diff = probe["trace"], probe["diff"]
    assert not trace.get("error") and int(trace["output"], 16) == paid
    user_int = int(user, 16)
    assert storage(diff, "pre", slot(18)) == 3 * AMOUNT
    assert storage(diff, "post", slot(18)) == 3 * AMOUNT - paid
    assert storage(diff, "post", slot(22)) - storage(diff, "pre", slot(22)) == paid
    assert storage(diff, "pre", slot(27)) == original[27]
    assert storage(diff, "post", slot(27)) == original[27] - paid
    assert storage(diff, "pre", mapped(1, 15, 1)) == AMOUNT
    assert storage(diff, "post", mapped(1, 15, 1)) == AMOUNT - paid
    assert storage(diff, "post", mapped(user_int, 9)) - storage(diff, "pre", mapped(user_int, 9)) == paid
    assert storage(diff, "pre", mapped(user_int, 19)) == AMOUNT
    assert storage(diff, "post", mapped(user_int, 19)) == AMOUNT - paid
    assert slot(16) not in diff["pre"][PROXY]["storage"]
    logs = ordered_logs(trace)
    assert len(logs) == 2
    assert logs[0]["topics"] == [HARVESTED_TOPIC, slot(user_int)]
    assert words(logs[0]["data"]) == [paid, AMOUNT - paid]
    assert logs[1]["topics"] == [SIDE_BUCKET_TOPIC]
    assert words(logs[1]["data"]) == [original[27] - paid]
    return {"available": str(paid), "returned_amount": str(paid),
            "node_remaining": str(AMOUNT - paid),
            "side_bucket_after": str(original[27] - paid),
            "global_head_unchanged": True,
            "evidence": "../../artifacts/exchange_queue/partial_node_historical_state.json"}


def verify():
    assert "0x" + KECCAK(HARVESTED.encode()).hex() == HARVESTED_TOPIC
    assert "0x" + KECCAK(SIDE_BUCKET.encode()).hex() == SIDE_BUCKET_TOPIC
    layout = json.loads((ATLAS / "exchange_queue_layout_behavior.json").read_text())
    users = [row["user"].lower() for row in layout["enqueues"]]
    page = json.loads((ARTIFACTS / "enqueued_page1.json").read_text())
    query = json.loads((ARTIFACTS / "enqueued_query.json").read_text())
    assert query == {"chain_id": 999, "address": PROXY,
                     "topic0": layout["event_catalog"][0]["topic0"],
                     "from_block": DEPLOY_BLOCK, "to_block": PIN,
                     "page": 1, "offset": 1000, "result_count": len(page)}
    assert len(page) == 3 < 1000
    assert [row["transactionHash"].lower() for row in page] == [row[0] for row in ENQUEUES]
    assert all(row["address"].lower() == PROXY and row["topics"][0] == layout["event_catalog"][0]["topic0"]
               and int(row["blockNumber"], 16) <= PIN for row in page)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN
    assert manifest["contracts"][PROXY]["origin"]["block"] == DEPLOY_BLOCK
    actual_receipt = json.loads((HISTORICAL / f"{HARVEST}.receipt.json").read_text())
    actual_diff = json.loads((HISTORICAL / f"{HARVEST}.state_diff.json").read_text())
    actual_logs = [(row["topics"], row["data"]) for row in actual_receipt["logs"]
                   if row["address"].lower() == PROXY]
    assert actual_receipt["status"] == "0x1" and int(actual_receipt["blockNumber"], 16) == PROBE_BLOCK + 1
    rows = []
    baseline_bucket = None
    probe_hash = None
    for n in range(4):
        probe = json.loads(probe_path(n).read_text())
        assert probe["block"] == PROBE_BLOCK and probe["block_hash"].startswith("0x")
        if probe_hash is None:
            probe_hash = probe["block_hash"]
        assert probe["block_hash"] == probe_hash
        assert [int(probe["prestate_slots"][str(i)], 16) for i in (16, 17, 18)] == [1, 4, 3 * AMOUNT]
        assert probe["call"] == {"from": SENDER, "to": PROXY,
                                 "data": "0xddc63262" + n.to_bytes(32, "big").hex()}
        assert not probe["trace"].get("error") and int(probe["output"], 16) == n * AMOUNT
        assert probe["trace"]["output"] == probe["output"]
        diff = probe["diff"]
        logs = ordered_logs(probe["trace"])
        before = diff.get("pre", {}).get(PROXY, {}).get("storage", {})
        after = diff.get("post", {}).get(PROXY, {}).get("storage", {})
        if n == 0:
            assert not before and not after and not logs
            rows.append({"max_entries": n, "returned_amount": "0", "head_after": 1,
                         "queued_after": str(3 * AMOUNT), "processed_users": [], "logs": 0})
            continue
        bucket_before = storage(diff, "pre", slot(27))
        if baseline_bucket is None:
            baseline_bucket = bucket_before
        assert bucket_before == baseline_bucket
        bucket_after = baseline_bucket - n * AMOUNT if n < 3 else 0
        assert storage(diff, "post", slot(16)) == 1 + n
        assert storage(diff, "pre", slot(18)) == 3 * AMOUNT
        assert storage(diff, "post", slot(18)) == (3 - n) * AMOUNT
        assert storage(diff, "post", slot(27)) == bucket_after
        balances_before = storage(diff, "pre", slot(22))
        balances_after = storage(diff, "post", slot(22))
        assert balances_after - balances_before == n * AMOUNT
        assert balances_after >> 128 == balances_before >> 128
        assert len(logs) == n + 1
        for index, user in enumerate(users[:n]):
            user_int = int(user, 16)
            node_id = index + 1
            key = mapped(user_int, 9)
            assert storage(diff, "post", key) - storage(diff, "pre", key) == AMOUNT
            assert storage(diff, "pre", mapped(node_id, 15, 1)) == AMOUNT
            assert storage(diff, "post", mapped(node_id, 15, 1)) == 0
            assert storage(diff, "pre", mapped(user_int, 19)) == AMOUNT
            assert storage(diff, "post", mapped(user_int, 19)) == 0
            assert storage(diff, "pre", mapped(user_int, 20)) == node_id
            assert storage(diff, "post", mapped(user_int, 20)) == 0
            assert storage(diff, "pre", mapped(user_int, 21)) == node_id
            assert storage(diff, "post", mapped(user_int, 21)) == 0
            event = logs[index]
            assert event["topics"] == [HARVESTED_TOPIC, slot(user_int)]
            assert words(event["data"]) == [AMOUNT, 0]
        for index, user in enumerate(users[n:], n + 1):
            user_int = int(user, 16)
            assert all(key not in before and key not in after for key in
                       (mapped(index, 15, 1), mapped(user_int, 9), mapped(user_int, 19),
                        mapped(user_int, 20), mapped(user_int, 21)))
        assert logs[-1]["topics"] == [SIDE_BUCKET_TOPIC]
        assert words(logs[-1]["data"]) == [bucket_after]
        if n == 3:
            assert diff["pre"][PROXY]["storage"] == actual_diff["pre"][PROXY]["storage"]
            assert diff["post"][PROXY]["storage"] == actual_diff["post"][PROXY]["storage"]
            assert [(row["topics"], row["data"]) for row in logs] == actual_logs
        rows.append({"max_entries": n, "returned_amount": str(n * AMOUNT),
                     "head_after": 1 + n, "queued_after": str((3 - n) * AMOUNT),
                     "total_balances_delta": str(n * AMOUNT), "side_bucket_after": str(bucket_after),
                     "processed_users": users[:n], "logs": len(logs)})
    result = {"pin_block": PIN, "probe_block": PROBE_BLOCK, "probe_block_hash": probe_hash,
              "historical_harvest_tx": HARVEST, "exchange_proxy": PROXY,
              "enqueued_history": {"from_block": DEPLOY_BLOCK, "to_block": PIN,
                                    "complete_first_page_count": len(page),
                                    "all_three_users_distinct": len(set(users)) == 3,
                                    "evidence": "../../artifacts/exchange_queue/enqueued_page1.json"},
              "event_catalog": [{"topic0": HARVESTED_TOPIC, "reconstructed_signature": HARVESTED,
                                 "decoded_layout": "indexed user; unindexed amount paid, node amount remaining"},
                                {"topic0": SIDE_BUCKET_TOPIC, "reconstructed_signature": SIDE_BUCKET}],
              "partial_harvest_probes": rows,
              "partial_node_with_side_bucket": verify_partial_node(probe_hash, users[0]),
              "full_harvest_replay": {"storage_diff_equal": True, "ordered_logs_equal": True},
              "limitations": ["No same-user queue append occurred in complete observed history through the pin.",
                              "Partial harvest results are read-only simulations at an archived state.",
                              "The underfunded node payout uses a treasury storage override; larger queues remain untested."]}
    (ATLAS / "exchange_queue_harvest_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange queue: complete 3-event enqueue history and partial harvest limits 0-3 verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
