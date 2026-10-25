#!/usr/bin/env python3
"""Verify older Papertrade signer, timelock, and upgrade control at the pin."""

import argparse
import gzip
import json
import os
import pathlib

from atlas_deployer_scope import call, rpc_batch
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_governance.json.gz"
PIN = 48_902_346
PAIRS = (
    (
        "0x35fbba5264058d135fb58316b67d6d7cdd433b9449f6af73366ae231ee982411",
        "0xa1f385df5db29fbd8c7c6404d05c0d81593f61c9c36d8a01262f50e3c4056d1b",
    ),
    (
        "0x105b275683e663db0b1e018228b1e143ca7b161357dd2a51ef8caf207c68c419",
        "0x2d5ec3ad25193d60f39165bee14fd84ba3da69ceb454d49aa6e016666d68ef92",
    ),
)
SIGNER_ONE = "0x7ce50a614174a3b26b107f1f9866f88461820626"
SIGNER_TWO = "0x8cea98f6ab3004c762efaf3dfd54876d62912300"
SUBMIT = "0x684dbac7"
SCHEDULE_BATCH = "0x8b07f62b"
EXECUTE_BATCH = "0xa6cc2c8c"
RECONCILE = "0x6a3214c9"
SCHEDULE_TOPIC = "0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f"
EXECUTE_TOPIC = "0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd"
RECONCILE_TOPIC = "0x8da9931e615ce9dfd2d7914e0cee3246839757203d34810cde64e0d0026f75c3"
GETTERS = {
    "multisig_signer_one": (17, "0xd98f851a"),
    "multisig_signer_two": (17, "0x1a5f66c3"),
    "multisig_required_confirmations": (17, "0x82e717f7"),
    "multisig_transaction_count": (17, "0xb77bf600"),
    "timelock_owner": (18, "0x8da5cb5b"),
    "timelock_min_delay": (18, "0xc63c4e9b"),
    "proxy_admin_owner": (0, "0x8da5cb5b"),
    "exchange_owner": (4, "0x8da5cb5b"),
}


def scope():
    result = json.loads(gzip.decompress(SCOPE.read_bytes()))
    assert result["pin"] == PIN
    return result


def address(value):
    return "0x" + value[-40:].lower()


def capture():
    saved_scope = scope()
    rows = saved_scope["rows"]
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    calls = []
    for set_index, base in enumerate((0, 19)):
        for name, (offset, selector) in GETTERS.items():
            calls.append(call("eth_call", [{"to": rows[base + offset]["address"],
                                            "data": selector}, hex(PIN)], len(calls)))
    for address_index, selector in ((55, "0x82e717f7"), (56, "0xc63c4e9b")):
        calls.append(call("eth_call", [{"to": rows[address_index]["address"],
                                        "data": selector}, hex(PIN)], len(calls)))
    results = rpc_batch(url, calls)
    getters = []
    position = 0
    for base in (0, 19):
        values = {}
        for name in GETTERS:
            values[name] = results[position]
            position += 1
        getters.append({"base": base, "values": values})
    newest = {"multisig_required_confirmations": results[position],
              "timelock_min_delay": results[position + 1]}

    transactions = {}
    for tx_hash in (tx for pair in PAIRS for tx in pair):
        queries = [
            call("eth_getTransactionByHash", [tx_hash], 0),
            call("eth_getTransactionReceipt", [tx_hash], 1),
            call("debug_traceTransaction", [tx_hash, {
                "tracer": "callTracer", "tracerConfig": {"withLog": True}
            }], 2),
        ]
        result = rpc_batch(url, queries)
        transaction, receipt, trace = result[0], result[1], result[2]
        assert transaction["hash"].lower() == receipt["transactionHash"].lower() == tx_hash
        block_number = int(transaction["blockNumber"], 16)
        header = rpc_batch(url, [call("eth_getBlockByNumber", [hex(block_number), False], 0)])[0]
        transactions[tx_hash] = {
            "transaction": transaction, "receipt": receipt, "trace": trace,
            "block": {key: header[key] for key in ("number", "hash", "timestamp")},
        }
    payload = {
        "pin": PIN, "block_hash": saved_scope["block_hash"],
        "older_getters": getters, "newest_control": newest,
        "transactions": transactions,
    }
    OUT.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(),
                                  compresslevel=9, mtime=0))
    return verify()


def decode_submit(data):
    assert data[:10].lower() == SUBMIT
    words = [int(data[10 + 64 * index:10 + 64 * (index + 1)], 16) for index in range(4)]
    target, value, offset, execute_now = words
    assert value == 0 and offset == 128 and execute_now == 1
    tail = 10 + offset * 2
    length = int(data[tail:tail + 64], 16)
    inner = "0x" + data[tail + 64:tail + 64 + length * 2].lower()
    assert len(inner) == 2 + 2 * length
    return "0x" + target.to_bytes(20, "big").hex(), inner


def verify_pair(saved, pair, multisig, timelock, exchange, implementation):
    operations = []
    for tx_hash, method, topic in zip(pair, (SCHEDULE_BATCH, EXECUTE_BATCH),
                                      (SCHEDULE_TOPIC, EXECUTE_TOPIC)):
        evidence = saved["transactions"][tx_hash]
        transaction, receipt, trace, header = (evidence[key] for key in
                                               ("transaction", "receipt", "trace", "block"))
        assert transaction["hash"].lower() == tx_hash
        assert transaction["from"].lower() == SIGNER_ONE
        assert transaction["to"].lower() == multisig
        assert transaction["blockHash"].lower() == receipt["blockHash"].lower() == header["hash"].lower()
        assert transaction["blockNumber"] == receipt["blockNumber"] == header["number"]
        assert receipt["status"] == "0x1" and int(header["number"], 16) <= PIN
        target, inner = decode_submit(transaction["input"])
        assert target == timelock and inner[:10] == method
        assert trace["type"] == "CALL" and trace["from"].lower() == SIGNER_ONE
        assert trace["to"].lower() == multisig and trace["input"].lower() == transaction["input"].lower()
        assert len(trace["calls"]) == 1
        child = trace["calls"][0]
        assert child["type"] == "CALL" and child["from"].lower() == multisig
        assert child["to"].lower() == timelock and child["input"].lower() == inner
        timelock_logs = [item for item in receipt["logs"] if item["address"].lower() == timelock]
        assert len(timelock_logs) == 1 and timelock_logs[0]["topics"][0] == topic
        operations.append((evidence, timelock_logs[0]["topics"][1]))
    schedule, operation_id = operations[0]
    execution, executed_id = operations[1]
    assert operation_id == executed_id
    schedule_log = next(item for item in schedule["receipt"]["logs"]
                        if item["address"].lower() == timelock)
    data_words = [int(schedule_log["data"][2 + index * 64:2 + (index + 1) * 64], 16)
                  for index in range(3)]
    scheduled_at = int(schedule["block"]["timestamp"], 16)
    executed_at = int(execution["block"]["timestamp"], 16)
    assert data_words[0] == 1 and data_words[2] == scheduled_at + 60
    assert executed_at >= data_words[2]
    assert executed_at - scheduled_at in (63, 115)
    assert schedule["trace"]["calls"][0].get("calls", []) == []
    timelock_call = execution["trace"]["calls"][0]
    assert len(timelock_call["calls"]) == 1
    exchange_call = timelock_call["calls"][0]
    assert exchange_call["type"] == "CALL" and exchange_call["from"].lower() == timelock
    assert exchange_call["to"].lower() == exchange and exchange_call["input"][:10] == RECONCILE
    assert len(exchange_call["calls"]) == 1
    impl_call = exchange_call["calls"][0]
    assert impl_call["type"] == "DELEGATECALL" and impl_call["to"].lower() == implementation
    assert impl_call["input"].lower() == exchange_call["input"].lower()
    assert any(log["address"].lower() == exchange and log["topics"][0] == RECONCILE_TOPIC
               for log in execution["receipt"]["logs"])
    return {"operation_id": operation_id, "scheduled_at": scheduled_at,
            "ready_at": data_words[2], "executed_at": executed_at,
            "delay_seconds": executed_at - scheduled_at,
            "schedule_tx": pair[0], "execute_tx": pair[1]}


def verify():
    saved_scope = scope()
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    assert saved["pin"] == PIN and saved["block_hash"] == saved_scope["block_hash"]
    rows = saved_scope["rows"]
    assert len(saved["older_getters"]) == 2
    results = []
    for index, base in enumerate((0, 19)):
        exchange, admin, multisig, timelock = (rows[base + offset]["address"]
                                               for offset in (4, 0, 17, 18))
        entry = saved["older_getters"][index]
        assert entry["base"] == base and set(entry["values"]) == set(GETTERS)
        values = entry["values"]
        assert address(values["multisig_signer_one"]) == SIGNER_ONE
        assert address(values["multisig_signer_two"]) == SIGNER_TWO
        assert int(values["multisig_required_confirmations"], 16) == 1
        assert int(values["multisig_transaction_count"], 16) == (240, 1299)[index]
        assert address(values["timelock_owner"]) == multisig
        assert int(values["timelock_min_delay"], 16) == 60
        assert address(values["proxy_admin_owner"]) == timelock
        assert address(values["exchange_owner"]) == timelock
        for offset in (2, 4, 6, 8, 10, 12, 14, 16):
            assert address(rows[base + offset]["admin_word"]) == admin
        implementation = rows[base + 3]["address"] if index == 0 else rows[57]["address"]
        path = verify_pair(saved, PAIRS[index], multisig, timelock, exchange, implementation)
        results.append({"set": index + 1, "multisig": multisig, "timelock": timelock,
                        "proxy_admin": admin, "exchange": exchange, **path})
    assert "0x" + Keccak()(b"submitTransaction(address,uint256,bytes,bool)").hex()[:8] == SUBMIT
    assert int(saved["newest_control"]["multisig_required_confirmations"], 16) == 2
    assert int(saved["newest_control"]["timelock_min_delay"], 16) == 604800
    return {"older_multisig_threshold": 1, "older_delay_seconds": 60,
            "newest_multisig_threshold": 2, "newest_delay_seconds": 604800,
            "historical_paths": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh archive state and historical traces")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
