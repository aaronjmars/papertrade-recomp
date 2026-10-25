#!/usr/bin/env python3
"""Census older Exchange withdrawals and match their public Core transfers."""

import argparse
import collections
import concurrent.futures
import gzip
import hashlib
import json
import os
import pathlib

from atlas_deployer_scope import IMPLEMENTATION_SLOT, PIN, call, rpc_batch
from atlas_exchange_sweeps import mapping_slot
from atlas_exchange_withdrawal_history import TOPIC
from atlas_factory_events import Keccak
from atlas_older_proxy_core import CORE_INFO, core_ledger, raw

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
LOGS = ROOT / "artifacts" / "deployer_scope" / "older_withdrawal_logs.json.gz"
CORE = ROOT / "artifacts" / "deployer_scope" / "older_withdrawal_core.json.gz"
TRACES = ROOT / "artifacts" / "deployer_scope" / "older_withdrawal_traces.json.gz"
WINDOW = 100_000
EXCHANGE_INDEX = (4, 23)
SAMPLES = (
    (0, "0x1c26dac60ac6bcae71fb40b6058b07fb15ed938cd570b90e20405b129f787e75", 3),
    (1, "0x0a5159ae289b0a411dfd36e3888da4fde364d849f34239f89b8c931bb97538e8", 22),
    (1, "0xe7d77a34c68dd7485a9d5a36005be28a0c7ed5d47b9b023157d12440fac31fd5", 57),
)
CORE_WRITER = "0x" + "33" * 20
MASK_128 = (1 << 128) - 1


def saved_json(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def write_json(path, payload):
    path.write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )


def exchanges(scope):
    return [scope["rows"][index] for index in EXCHANGE_INDEX]


def event_rows(saved):
    for window in saved["windows"]:
        for log in window["logs"]:
            yield window["set"], log


def event_key(set_index, log):
    return (set_index, log["transactionHash"].lower(), log["logIndex"])


def event_values(log):
    assert len(log["topics"]) == 2 and len(log["data"]) == 130
    debit = int(log["data"][2:66], 16)
    core_amount = int(log["data"][66:130], 16)
    gap = debit - core_amount * 10**10
    return {
        "user": "0x" + log["topics"][1][-40:].lower(),
        "debit_18": debit,
        "core_amount_8": core_amount,
        "gap_18": gap,
    }


def capture_logs():
    scope = saved_json(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert scope["block_hash"] == manifest["block_hash"]
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    windows = []
    calls = [call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    for set_index, exchange in enumerate(exchanges(scope)):
        for start in range(exchange["creation_block"], PIN + 1, WINDOW):
            end = min(PIN, start + WINDOW - 1)
            rpc_id = len(windows) + 1
            windows.append(
                {
                    "set": set_index,
                    "from_block": start,
                    "to_block": end,
                    "rpc_id": rpc_id,
                }
            )
            calls.append(
                call(
                    "eth_getLogs",
                    [
                        {
                            "fromBlock": hex(start),
                            "toBlock": hex(end),
                            "address": exchange["address"],
                            "topics": [TOPIC],
                        }
                    ],
                    rpc_id,
                )
            )
    result = rpc_batch(os.environ["PAPERTRADE_ARCHIVE_RPC"], calls)
    assert result[0]["hash"].lower() == manifest["block_hash"]
    for window in windows:
        window["logs"] = result[window.pop("rpc_id")]
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "topic0": TOPIC,
        "window_target": WINDOW,
        "windows": windows,
    }
    summary = verify_logs_payload(payload, scope, manifest)
    write_json(LOGS, payload)
    return summary


def verify_logs_payload(saved, scope, manifest):
    assert saved["pin"] == scope["pin"] == manifest["block"] == PIN
    assert saved["block_hash"] == scope["block_hash"] == manifest["block_hash"]
    assert saved["topic0"] == TOPIC and saved["window_target"] == WINDOW
    cursors = [row["creation_block"] for row in exchanges(scope)]
    factory_users = [
        {"0x" + event["log"]["topics"][1][-40:].lower() for event in group["events"]}
        for group in scope["earlier_factory_deployments"]
    ]
    counts = [collections.Counter(), collections.Counter()]
    users = [set(), set()]
    seen = set()
    for window in saved["windows"]:
        set_index, start, end = (
            window["set"],
            window["from_block"],
            window["to_block"],
        )
        assert set_index in (0, 1)
        assert start == cursors[set_index]
        assert start <= end == min(PIN, start + WINDOW - 1)
        cursors[set_index] = end + 1
        exchange = exchanges(scope)[set_index]["address"]
        assert len(window["logs"]) < 10_000
        for log in window["logs"]:
            assert log["address"].lower() == exchange
            assert log["topics"][0].lower() == TOPIC
            assert log["removed"] is False
            assert start <= int(log["blockNumber"], 16) <= end
            key = event_key(set_index, log)
            assert key not in seen
            seen.add(key)
            values = event_values(log)
            assert values["user"] in factory_users[set_index]
            assert values["core_amount_8"] > 0
            counts[set_index][values["gap_18"]] += 1
            users[set_index].add(values["user"])
    assert cursors == [PIN + 1, PIN + 1]
    assert len(saved["windows"]) == 80
    assert [sum(counter.values()) for counter in counts] == [27, 6]
    assert len({tx for _, tx, _ in seen}) == len(seen)
    assert counts[0] == {0: 27}
    assert counts[1] == {0: 5, 10**18: 1}
    assert [len(group) for group in users] == [5, 3]
    return {
        "windows": len(saved["windows"]),
        "events": [sum(counter.values()) for counter in counts],
        "withdrawal_users": [len(group) for group in users],
        "debit_gap_counts": [dict(counter) for counter in counts],
    }


def verify_logs():
    return verify_logs_payload(
        saved_json(LOGS),
        saved_json(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def core_sample(args):
    set_index, log, header, exchange = args
    values = event_values(log)
    start_ms = int(header["timestamp"], 16) * 1000
    window = [start_ms - 2000, start_ms + 5000]
    return {
        "set": set_index,
        "transaction_hash": log["transactionHash"].lower(),
        "log_index": log["logIndex"],
        "block_number": int(log["blockNumber"], 16),
        "header": header,
        "query_window_ms": window,
        "exchange_ledger": core_ledger(exchange, *window),
        "recipient_ledger": core_ledger(values["user"], *window),
    }


def capture_core():
    saved = saved_json(LOGS)
    scope = saved_json(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    verify_logs_payload(saved, scope, manifest)
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    events = list(event_rows(saved))
    blocks = sorted({int(log["blockNumber"], 16) for _, log in events})
    result = rpc_batch(
        os.environ["PAPERTRADE_ARCHIVE_RPC"],
        [call("eth_getBlockByNumber", [hex(block), False], block) for block in blocks],
    )
    headers = {
        block: {key: result[block][key] for key in ("number", "hash", "timestamp")}
        for block in blocks
    }
    args = [
        (
            set_index,
            log,
            headers[int(log["blockNumber"], 16)],
            exchanges(scope)[set_index]["address"],
        )
        for set_index, log in events
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        samples = list(pool.map(core_sample, args))
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "core_info": CORE_INFO,
        "samples": samples,
    }
    summary = verify_core_payload(payload, saved, scope, manifest)
    write_json(CORE, payload)
    return summary


def matching_transfer(entry, exchange, user, amount_8, start_ms):
    delta = entry.get("delta", {})
    return (
        start_ms <= entry.get("time", -1) < start_ms + 1000
        and delta.get("type") == "spotTransfer"
        and delta.get("token") == "USDC"
        and delta.get("user", "").lower() == exchange
        and delta.get("destination", "").lower() == user
        and raw(delta["amount"]) == amount_8
    )


def verify_core_payload(saved, logs, scope, manifest):
    assert saved["pin"] == logs["pin"] == scope["pin"] == manifest["block"] == PIN
    assert saved["block_hash"] == logs["block_hash"] == manifest["block_hash"]
    assert saved["core_info"] == CORE_INFO
    events = list(event_rows(logs))
    assert len(saved["samples"]) == len(events) == 33
    delivered = [0, 0]
    fees = [0, 0]
    seen_core_hashes = set()
    for sample, (set_index, log) in zip(saved["samples"], events):
        values = event_values(log)
        exchange = exchanges(scope)[set_index]["address"]
        assert (
            sample["set"],
            sample["transaction_hash"],
            sample["log_index"],
        ) == event_key(set_index, log)
        assert sample["block_number"] == int(log["blockNumber"], 16)
        header = sample["header"]
        assert int(header["number"], 16) == sample["block_number"]
        assert header["hash"].lower() == log["blockHash"].lower()
        start_ms = int(header["timestamp"], 16) * 1000
        assert sample["query_window_ms"] == [start_ms - 2000, start_ms + 5000]
        matches = []
        for ledger in (sample["exchange_ledger"], sample["recipient_ledger"]):
            matches.append(
                [
                    entry
                    for entry in ledger
                    if matching_transfer(
                        entry,
                        exchange,
                        values["user"],
                        values["core_amount_8"],
                        start_ms,
                    )
                ]
            )
        assert len(matches[0]) == len(matches[1]) == 1
        transfer = matches[0][0]
        assert transfer == matches[1][0]
        assert transfer["hash"] not in seen_core_hashes
        seen_core_hashes.add(transfer["hash"])
        delta = transfer["delta"]
        assert raw(delta["usdcValue"]) == values["core_amount_8"]
        fee = raw(delta["fee"])
        assert fee * 10**10 == values["gap_18"]
        assert raw(delta["nativeTokenFee"]) == 0
        assert delta["feeToken"] == ("USDC" if fee else "")
        delivered[set_index] += values["core_amount_8"]
        fees[set_index] += fee
    assert delivered == [80_321_094_000_000, 1_039_910_000_000]
    assert fees == [0, 100_000_000]
    return {
        "matched_transfers": len(seen_core_hashes),
        "matched_by_set": [27, 6],
        "delivered_8_by_set": delivered,
        "fee_8_by_set": fees,
    }


def verify_core():
    return verify_core_payload(
        saved_json(CORE),
        saved_json(LOGS),
        saved_json(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def writer_payload(node):
    data = bytes.fromhex(node["input"][10:])
    offset = int.from_bytes(data[:32], "big")
    length = int.from_bytes(data[offset : offset + 32], "big")
    return data[offset + 32 : offset + 32 + length]


def capture_traces():
    scope = saved_json(SCOPE)
    logs = saved_json(LOGS)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    verify_logs_payload(logs, scope, manifest)
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    by_tx = {log["transactionHash"].lower(): log for _, log in event_rows(logs)}
    samples = []
    for set_index, tx, implementation_index in SAMPLES:
        log = by_tx[tx]
        exchange = exchanges(scope)[set_index]["address"]
        implementation = scope["rows"][implementation_index]["address"]
        block = int(log["blockNumber"], 16)
        result = rpc_batch(
            url,
            [
                call("eth_getTransactionByHash", [tx], 0),
                call("eth_getTransactionReceipt", [tx], 1),
                call(
                    "debug_traceTransaction",
                    [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}],
                    2,
                ),
                call(
                    "debug_traceTransaction",
                    [
                        tx,
                        {
                            "tracer": "prestateTracer",
                            "tracerConfig": {"diffMode": True},
                        },
                    ],
                    3,
                ),
                call("eth_getCode", [exchange, hex(block)], 4),
                call("eth_getCode", [implementation, hex(block)], 5),
                call(
                    "eth_getStorageAt", [exchange, IMPLEMENTATION_SLOT, hex(block)], 6
                ),
            ],
        )
        samples.append(
            {
                "set": set_index,
                "tx": tx,
                "implementation": implementation,
                "transaction": result[0],
                "receipt": result[1],
                "call_trace": result[2],
                "state_diff": result[3],
                "proxy_code_sha256": hashlib.sha256(
                    bytes.fromhex(result[4][2:])
                ).hexdigest(),
                "implementation_code_sha256": hashlib.sha256(
                    bytes.fromhex(result[5][2:])
                ).hexdigest(),
                "implementation_slot": result[6],
            }
        )
    payload = {"pin": PIN, "block_hash": manifest["block_hash"], "samples": samples}
    summary = verify_traces_payload(payload, logs, scope, manifest)
    write_json(TRACES, payload)
    return summary


def verify_traces_payload(saved, logs, scope, manifest):
    assert saved["pin"] == logs["pin"] == scope["pin"] == manifest["block"] == PIN
    assert saved["block_hash"] == logs["block_hash"] == manifest["block_hash"]
    assert len(saved["samples"]) == len(SAMPLES)
    event_by_tx = {log["transactionHash"].lower(): log for _, log in event_rows(logs)}
    results = []
    for sample, (set_index, tx, implementation_index) in zip(saved["samples"], SAMPLES):
        log = event_by_tx[tx]
        values = event_values(log)
        exchange = exchanges(scope)[set_index]["address"]
        implementation = scope["rows"][implementation_index]["address"]
        transaction, receipt = sample["transaction"], sample["receipt"]
        assert (sample["set"], sample["tx"], sample["implementation"]) == (
            set_index,
            tx,
            implementation,
        )
        assert transaction["hash"].lower() == receipt["transactionHash"].lower() == tx
        assert int(receipt["status"], 16) == 1
        assert receipt["blockHash"].lower() == log["blockHash"].lower()
        assert int(receipt["blockNumber"], 16) == int(log["blockNumber"], 16)
        assert any(
            row["address"].lower() == exchange
            and row["topics"] == log["topics"]
            and row["data"] == log["data"]
            and row["logIndex"] == log["logIndex"]
            for row in receipt["logs"]
        )
        assert sample["implementation_slot"][-40:].lower() == implementation[2:]
        for name, address in (("proxy", exchange), ("implementation", implementation)):
            code = next(
                row["runtime"] for row in scope["rows"] if row["address"] == address
            )
            expected = hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
            assert sample[f"{name}_code_sha256"] == expected
        root = sample["call_trace"]
        assert root["to"].lower() == transaction["to"].lower()
        assert root["input"].lower() == transaction["input"].lower()
        selector = "0x7f99545a" if values["gap_18"] else "0x8d09f23f"
        if selector == "0x7f99545a":
            assert transaction["to"].lower() == exchange
        else:
            assert transaction["input"].startswith("0x251fb27d")
        delegates = [
            node
            for node in descendants(root)
            if node.get("type") == "DELEGATECALL"
            and node.get("to", "").lower() == implementation
            and node.get("input", "").startswith(selector)
        ]
        assert len(delegates) == 1
        delegate = delegates[0]
        assert delegate["from"].lower() == exchange and not delegate.get("error")
        status_calls = [
            node
            for node in descendants(delegate)
            if node.get("to", "").lower().endswith("0810")
        ]
        assert len(status_calls) == 1
        status = int(status_calls[0]["output"], 16)
        assert status in (0, 1)
        assert values["gap_18"] == (10**18 if status == 0 else 0)
        writers = [
            node
            for node in descendants(delegate)
            if node.get("type") == "CALL"
            and node.get("to", "").lower() == CORE_WRITER
            and node.get("input", "").startswith("0x17938e13")
        ]
        assert len(writers) == 1
        payload = writer_payload(writers[0])
        assert len(payload) == 100
        assert payload[-8:] == values["core_amount_8"].to_bytes(8, "big")
        assert values["user"][2:] in payload.hex()
        state_diff = sample["state_diff"]
        before = state_diff["pre"][exchange]["storage"]
        after = state_diff["post"][exchange]["storage"]
        user_slot = mapping_slot(values["user"], 9, Keccak())
        slot14 = f"0x{14:064x}"
        slot22 = f"0x{22:064x}"
        assert (
            int(before[user_slot], 16) - int(after.get(user_slot, "0x0"), 16)
            == values["debit_18"]
        )
        assert (
            int(before[slot14], 16) - int(after.get(slot14, "0x0"), 16)
            == values["debit_18"]
        )
        assert (int(before[slot22], 16) & MASK_128) - (
            int(after.get(slot22, "0x0"), 16) & MASK_128
        ) == values["debit_18"]
        results.append(
            {
                "set": set_index,
                "tx": tx,
                "selector": selector,
                "implementation": implementation,
                "core_user_exists": bool(status),
                "debit_18": values["debit_18"],
                "sent_8": values["core_amount_8"],
            }
        )
    return results


def verify_traces():
    return verify_traces_payload(
        saved_json(TRACES),
        saved_json(LOGS),
        saved_json(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture-logs", action="store_true", help="refresh pinned EVM logs"
    )
    parser.add_argument(
        "--capture-core", action="store_true", help="refresh public Core ledgers"
    )
    parser.add_argument(
        "--capture-traces", action="store_true", help="refresh selected archive traces"
    )
    args = parser.parse_args()
    if args.capture_logs:
        capture_logs()
    if args.capture_core:
        capture_core()
    if args.capture_traces:
        capture_traces()
    print(
        json.dumps(
            {
                "logs": verify_logs(),
                "core": verify_core() if CORE.exists() else None,
                "traces": verify_traces() if TRACES.exists() else None,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
