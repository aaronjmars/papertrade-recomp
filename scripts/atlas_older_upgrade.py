#!/usr/bin/env python3
"""Reconcile the second earlier Exchange upgrade against archive storage and traces."""

import argparse
import gzip
import json
import os
import pathlib

from atlas_deployer_scope import IMPLEMENTATION_SLOT, call, rpc_batch
from atlas_factory_events import Keccak
from atlas_older_governance import SIGNER_ONE, SUBMIT, decode_submit

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_exchange_upgrade.json.gz"
PIN = 48_902_346
PROXY = "0x2ede04561914c61a5f49212609541934fd7f5901"
ORIGINAL = "0x6f0e9deab8a4f21344e4c10a35db5027b02a67fa"
REPLACEMENT = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
MULTISIG = "0x324b0547039683c2df146421f3a76083ef130d27"
TIMELOCK = "0xd98adcb9a409e33a658c24e872f37357a85ca484"
ADMIN = "0x15d0a00a5f8ba75012fbf9dc4a0cc31495ea8b72"
SCHEDULE_TX = "0x888b389e7010e988246ac68af3206db504d09eacda7f4db5d83d5514e4e8924b"
EXECUTE_TX = "0xbf5f27e4eb5af59a6b092008bfb045db009b8dab2b68d7f80313e5ab51e7a880"
SCHEDULE_TOPIC = "0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39"
EXECUTE_TOPIC = "0x2a08801cf3674ab09756ae78a3a4833813465af6af958136b360eab6b71c8952"


def scope():
    saved = json.loads(gzip.decompress(SCOPE.read_bytes()))
    assert saved["pin"] == PIN
    return saved


def address(word):
    return "0x" + word[-40:].lower()


def storage_call(proxy, block, identifier=0):
    return call("eth_getStorageAt", [proxy, IMPLEMENTATION_SLOT, hex(block)], identifier)


def capture():
    saved_scope = scope()
    rows = saved_scope["rows"]
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    proxy_indices = [base + offset for base in (0, 19) for offset in range(2, 17, 2)]
    calls = [storage_call(rows[index]["address"], rows[index]["creation_block"], index)
             for index in proxy_indices]
    creation_slots = rpc_batch(url, calls)

    searched = []

    def read_at(block):
        value = rpc_batch(url, [storage_call(PROXY, block)])[0]
        searched.append({"block": block, "word": value})
        return address(value)

    lower, upper = rows[57]["creation_block"] - 1, PIN
    assert read_at(lower) == ORIGINAL and read_at(upper) == REPLACEMENT
    while upper - lower > 1:
        middle = (lower + upper) // 2
        value = read_at(middle)
        if value == ORIGINAL:
            lower = middle
        elif value == REPLACEMENT:
            upper = middle
        else:
            raise RuntimeError(f"unexpected intermediate implementation at {middle}: {value}")

    block = rpc_batch(url, [call("eth_getBlockByNumber", [hex(upper), True], 0)])[0]
    evidence = {}
    for tx_hash in (SCHEDULE_TX, EXECUTE_TX):
        queries = [
            call("eth_getTransactionByHash", [tx_hash], 0),
            call("eth_getTransactionReceipt", [tx_hash], 1),
            call("debug_traceTransaction", [tx_hash, {"tracer": "callTracer",
                                                    "tracerConfig": {"withLog": True}}], 2),
        ]
        fetched = rpc_batch(url, queries)
        tx_block = int(fetched[0]["blockNumber"], 16)
        header = rpc_batch(url, [call("eth_getBlockByNumber", [hex(tx_block), False], 0)])[0]
        evidence[tx_hash] = {
            "transaction": fetched[0], "receipt": fetched[1], "trace": fetched[2],
            "block": {key: header[key] for key in ("number", "hash", "timestamp")},
        }
    state_diff = rpc_batch(url, [call("debug_traceTransaction", [EXECUTE_TX, {
        "tracer": "prestateTracer", "tracerConfig": {"diffMode": True}
    }], 0)])[0]
    payload = {
        "pin": PIN, "block_hash": saved_scope["block_hash"],
        "creation_implementation_slots": {str(index): creation_slots[index] for index in proxy_indices},
        "search": {"old_last_block": lower, "new_first_block": upper, "reads": searched},
        "transition_block": {key: block[key] for key in ("number", "hash", "timestamp", "transactions")},
        "transactions": evidence, "execution_state_diff": state_diff,
    }
    OUT.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(),
                                  compresslevel=9, mtime=0))
    return verify()


def decode_timelock(data):
    head = [int(data[10 + 64 * index:10 + 64 * (index + 1)], 16) for index in range(4)]
    target, value, offset, predecessor = head
    assert value == 0 and offset == 128
    tail = 10 + offset * 2
    length = int(data[tail:tail + 64], 16)
    inner = "0x" + data[tail + 64:tail + 64 + 2 * length].lower()
    assert len(inner) == 2 + 2 * length
    return "0x" + target.to_bytes(20, "big").hex(), inner, predecessor


def verify():
    saved_scope = scope()
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    assert saved["pin"] == PIN and saved["block_hash"] == saved_scope["block_hash"]
    rows = saved_scope["rows"]
    proxy_indices = [base + offset for base in (0, 19) for offset in range(2, 17, 2)]
    assert set(saved["creation_implementation_slots"]) == {str(index) for index in proxy_indices}
    changes = []
    for index in proxy_indices:
        row = rows[index]
        created = address(saved["creation_implementation_slots"][str(index)])
        pinned = address(row["implementation_word"])
        assert created == rows[index - 1]["address"]
        if created != pinned:
            changes.append({"proxy": row["address"], "created": created, "pinned": pinned})
    assert changes == [{"proxy": PROXY, "created": ORIGINAL, "pinned": REPLACEMENT}]
    assert rows[57]["address"] == REPLACEMENT and rows[57]["creation_block"] == 48_092_801

    search = saved["search"]
    assert (search["old_last_block"], search["new_first_block"]) == (48_092_889, 48_092_890)
    assert search["new_first_block"] - search["old_last_block"] == 1
    assert len(search["reads"]) >= 20
    assert {item["block"] for item in search["reads"]} >= {48_092_889, 48_092_890, PIN}
    assert all(address(item["word"]) in (ORIGINAL, REPLACEMENT) for item in search["reads"])
    assert next(item for item in search["reads"] if item["block"] == 48_092_889)["word"][-40:] == ORIGINAL[2:]
    assert next(item for item in search["reads"] if item["block"] == 48_092_890)["word"][-40:] == REPLACEMENT[2:]
    block = saved["transition_block"]
    assert int(block["number"], 16) == 48_092_890
    assert len(block["transactions"]) == 1 and block["transactions"][0]["hash"].lower() == EXECUTE_TX
    assert "0x" + Keccak()(b"submitTransaction(address,uint256,bytes,bool)").hex()[:8] == SUBMIT
    assert "0x" + Keccak()(b"upgrade(address,address)").hex()[:8] == "0x99a88ec4"

    operation_ids = []
    for tx_hash, selector, topic in ((SCHEDULE_TX, "0xb0e58bc9", SCHEDULE_TOPIC),
                                     (EXECUTE_TX, "0x88aa4c12", EXECUTE_TOPIC)):
        entry = saved["transactions"][tx_hash]
        transaction, receipt, trace, header = (entry[key] for key in
                                               ("transaction", "receipt", "trace", "block"))
        assert transaction["hash"].lower() == receipt["transactionHash"].lower() == tx_hash
        assert transaction["blockHash"].lower() == receipt["blockHash"].lower() == header["hash"].lower()
        assert transaction["from"].lower() == SIGNER_ONE and transaction["to"].lower() == MULTISIG
        assert receipt["status"] == "0x1"
        target, inner = decode_submit(transaction["input"])
        assert target == TIMELOCK and inner[:10] == selector
        assert trace["from"].lower() == SIGNER_ONE and trace["to"].lower() == MULTISIG
        assert trace["input"].lower() == transaction["input"].lower()
        assert len(trace["calls"]) == 1
        child = trace["calls"][0]
        assert child["type"] == "CALL" and child["from"].lower() == MULTISIG
        assert child["to"].lower() == TIMELOCK and child["input"].lower() == inner
        timelock_logs = [log for log in receipt["logs"] if log["address"].lower() == TIMELOCK]
        assert len(timelock_logs) == 1 and timelock_logs[0]["topics"][0] == topic
        operation_ids.append(timelock_logs[0]["topics"][1])
        decoded_target, decoded_inner, predecessor = decode_timelock(inner)
        assert decoded_target == ADMIN and predecessor != 0
        assert decoded_inner == "0x99a88ec4" + PROXY[2:].rjust(64, "0") + REPLACEMENT[2:].rjust(64, "0")
    assert operation_ids[0] == operation_ids[1]
    schedule = saved["transactions"][SCHEDULE_TX]
    execution = saved["transactions"][EXECUTE_TX]
    scheduled_at = int(schedule["block"]["timestamp"], 16)
    executed_at = int(execution["block"]["timestamp"], 16)
    assert scheduled_at == 1_791_561_020 and executed_at == 1_791_561_088
    assert executed_at - scheduled_at == 68
    schedule_data = next(log for log in schedule["receipt"]["logs"] if log["address"].lower() == TIMELOCK)["data"]
    ready_at = int(schedule_data[2 + 3 * 64:2 + 4 * 64], 16)
    assert ready_at == scheduled_at + 60 and executed_at >= ready_at

    assert len(schedule["trace"]["calls"][0].get("calls", [])) == 0
    timelock_execution = execution["trace"]["calls"][0]
    assert len(timelock_execution["calls"]) == 1
    admin_call = timelock_execution["calls"][0]
    assert admin_call["from"].lower() == TIMELOCK and admin_call["to"].lower() == ADMIN
    assert admin_call["input"].lower() == decoded_inner
    assert len(admin_call["calls"]) == 1
    proxy_call = admin_call["calls"][0]
    assert proxy_call["from"].lower() == ADMIN and proxy_call["to"].lower() == PROXY
    assert proxy_call["input"][:10] == "0x4f1ef286"
    assert proxy_call["input"][10:74] == REPLACEMENT[2:].rjust(64, "0")
    assert int(proxy_call["input"][74:138], 16) == 64
    assert int(proxy_call["input"][138:202], 16) == 0
    diff = saved["execution_state_diff"]
    assert set(diff) == {"pre", "post"}
    assert set(diff["pre"][PROXY]["storage"]) == set(diff["post"][PROXY]["storage"]) == {IMPLEMENTATION_SLOT}
    assert address(diff["pre"][PROXY]["storage"][IMPLEMENTATION_SLOT]) == ORIGINAL
    assert address(diff["post"][PROXY]["storage"][IMPLEMENTATION_SLOT]) == REPLACEMENT
    assert not any(log["address"].lower() == PROXY for log in execution["receipt"]["logs"])
    return {"changed_proxy_count": len(changes), "upgrade_block": 48_092_890,
            "schedule_tx": SCHEDULE_TX, "execute_tx": EXECUTE_TX,
            "operation_id": operation_ids[0], "scheduled_at": scheduled_at,
            "ready_at": ready_at, "executed_at": executed_at,
            "old_implementation": ORIGINAL, "new_implementation": REPLACEMENT}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh archive upgrade evidence")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
