#!/usr/bin/env python3
"""Verify a historical zero-available profit enqueue against receipt and storage."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib

from atlas_deployer_scope import call, rpc_batch
from atlas_exchange_library import pnl_model
from atlas_factory_events import Keccak
from atlas_older_settlement_liquidity import (
    OLD_EXCHANGE,
    OLD_IMPLEMENTATION,
    OLD_LIBRARY,
    RUNTIME,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEPL = ROOT / "artifacts" / "deployer_scope"
SCOPE = DEPL / "pinned_capture.json.gz"
OUT = DEPL / "older_settlement_historical_enqueue.json.gz"
TX = "0xc8746368be8bddb68c528f67e18a3d80ad2a113479e47db4dfe006721c7c3e3c"
BLOCK = 42_770_131
OLD_PROXY = OLD_EXCHANGE
OLD_BATCH = "0x4041882573028cb177847c46f82e242024ebde66"
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ENQUEUED = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
POSITION_CLOSED = "0x330ea55ab7d6f2662fc122ba5ed0d3bc3bb56ef7e9387b5aa6a78411b363c013"
SUMMARY = "0x789bd128f86c2eacb5c1fe72f20634891e0ef8020959d2e52a258cf31d42c6b2"


def words(value):
    assert value.startswith("0x")
    raw = bytes.fromhex(value[2:])
    assert len(raw) % 32 == 0
    return [int.from_bytes(raw[index:index + 32], "big") for index in range(0, len(raw), 32)]


def frames(frame):
    yield frame
    for child in frame.get("calls", []):
        yield from frames(child)


def scope():
    saved = json.loads(gzip.decompress(SCOPE.read_bytes()))
    assert saved["pin"] == 48_902_346
    return saved


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    results = rpc_batch(url, [
        call("eth_getTransactionByHash", [TX], 0),
        call("eth_getTransactionReceipt", [TX], 1),
        call("debug_traceTransaction", [TX, {
            "tracer": "callTracer", "tracerConfig": {"withLog": True},
        }], 2),
        call("debug_traceTransaction", [TX, {
            "tracer": "prestateTracer", "tracerConfig": {"diffMode": True},
        }], 3),
    ])
    assert results[0]["hash"].lower() == TX
    assert results[1]["transactionHash"].lower() == TX
    assert int(results[1]["blockNumber"], 16) == BLOCK
    other = rpc_batch(url, [
        call("eth_getBlockByNumber", [hex(BLOCK - 1), False], 0),
        call("eth_call", [{"to": OLD_EXCHANGE, "data": "0x0cdd5fc4"}, hex(BLOCK - 1)], 1),
        call("eth_getCode", [OLD_PROXY, hex(BLOCK)], 2),
        call("eth_getCode", [OLD_IMPLEMENTATION, hex(BLOCK)], 3),
        call("eth_getCode", [OLD_LIBRARY, hex(BLOCK)], 4),
        call("eth_getStorageAt", [OLD_PROXY, IMPL_SLOT, hex(BLOCK)], 5),
        call("eth_getStorageAt", [OLD_PROXY, hex(26), hex(BLOCK - 1)], 6),
        call("eth_call", [{"to": OLD_PROXY, "data": "0xafdf6702"}, hex(BLOCK - 1)], 7),
        call("eth_call", [{"to": OLD_PROXY, "data": "0x7d004aeb"}, hex(BLOCK - 1)], 8),
        call("eth_getStorageAt", [OLD_PROXY, hex(14), hex(BLOCK - 1)], 9),
        call("eth_call", [{"to": OLD_PROXY, "data": "0x61d027b3"}, hex(BLOCK - 1)], 10),
        call("eth_call", [
            {"to": OLD_PROXY, "data": "0x0cdd5fc4"}, hex(BLOCK - 1),
            {OLD_PROXY: {"stateDiff": {
                "0x" + format(18, "064x"): "0x" + "0" * 64,
            }}},
        ], 11),
    ])
    header = other[0]
    payload = {
        "pin": scope()["pin"],
        "pinned_block_hash": scope()["block_hash"],
        "transaction": results[0],
        "receipt": results[1],
        "call_trace": results[2],
        "storage_diff": results[3],
        "prestate_block": {
            key: header[key] for key in ("number", "hash", "timestamp")
        },
        "prestate_lp_bankroll_available": other[1],
        "historical_codes": {
            OLD_PROXY: other[2], OLD_IMPLEMENTATION: other[3], OLD_LIBRARY: other[4],
        },
        "historical_proxy_implementation_slot": other[5],
        "prestate_fee_slot_26": other[6],
        "prestate_staker_fee_getter": other[7],
        "prestate_dev_fee_getter": other[8],
        "prestate_treasury_slot_14": other[9],
        "prestate_treasury_getter": other[10],
        "lp_available_with_only_queue_slot_zeroed": other[11],
    }
    OUT.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), compresslevel=9, mtime=0))
    return verify()


def storage_diff(saved):
    diff = saved["storage_diff"]
    assert set(diff) == {"pre", "post"}
    before = next(value for address, value in diff["pre"].items() if address.lower() == OLD_PROXY)
    after = next(value for address, value in diff["post"].items() if address.lower() == OLD_PROXY)
    pre = {int(slot, 16): int(value, 16) for slot, value in before["storage"].items()}
    post = {int(slot, 16): int(value, 16) for slot, value in after["storage"].items()}
    return pre, post


def verify():
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    pinned = scope()
    assert saved["pin"] == pinned["pin"]
    assert saved["pinned_block_hash"] == pinned["block_hash"]
    tx, receipt, trace = saved["transaction"], saved["receipt"], saved["call_trace"]
    assert tx["hash"].lower() == receipt["transactionHash"].lower() == TX
    assert int(tx["blockNumber"], 16) == int(receipt["blockNumber"], 16) == BLOCK
    assert int(receipt["transactionIndex"], 16) == 0
    assert int(receipt["status"], 16) == 1
    assert tx["blockHash"].lower() == receipt["blockHash"].lower()
    assert int(saved["prestate_block"]["number"], 16) == BLOCK - 1
    assert trace["to"].lower() == tx["to"].lower() == OLD_BATCH
    assert trace["input"].lower() == tx["input"].lower()
    assert not trace.get("error")
    assert saved["historical_proxy_implementation_slot"][-40:].lower() == OLD_IMPLEMENTATION[2:]

    pinned_codes = {
        address: bytes.fromhex(next(row for row in pinned["rows"] if row["address"] == address)["runtime"][2:])
        for address in (OLD_PROXY, OLD_IMPLEMENTATION)
    }
    pinned_codes[OLD_LIBRARY] = bytes.fromhex(RUNTIME.read_text().strip()[2:])
    for address, code in pinned_codes.items():
        historical = bytes.fromhex(saved["historical_codes"][address][2:])
        assert hashlib.sha256(historical).hexdigest() == hashlib.sha256(code).hexdigest()

    fee_word = int(saved["prestate_fee_slot_26"], 16)
    assert fee_word & (2**128 - 1) == int(saved["prestate_staker_fee_getter"], 16)
    assert fee_word >> 128 == int(saved["prestate_dev_fee_getter"], 16)
    treasury = int(saved["prestate_treasury_slot_14"], 16)
    assert treasury == int(saved["prestate_treasury_getter"], 16)

    math, settlement = [
        frame for frame in frames(trace)
        if frame.get("to", "").lower() == OLD_LIBRARY
    ]
    assert math["input"].startswith("0x82296364") and settlement["input"].startswith("0xaa31b143")
    assert not math.get("error") and not settlement.get("error")
    math_args = words("0x" + math["input"][10:])
    math_output = words(math["output"])
    assert len(math_args) == 9 and len(math_output) == 2
    assert math_output == pnl_model(math_args)
    args = words("0x" + settlement["input"][10:])
    output = words(settlement["output"])
    assert len(args) == 7 and len(output) == 6
    user, margin, profit, available = args[1], args[2], args[3], args[6]
    assert math_output[1] == profit > 0
    assert available == int(saved["prestate_lp_bankroll_available"], 16) == 0
    assert args[4:6] == [2 * 10**16, 2 * 10**16]
    assert output == [margin, 0, profit, 0, 0, 0]

    logs = [log for log in receipt["logs"] if log["address"].lower() == OLD_EXCHANGE]
    assert [log["topics"][0].lower() for log in logs] == [ENQUEUED, POSITION_CLOSED, SUMMARY]
    enqueue = logs[0]
    assert int(enqueue["topics"][1], 16) == user
    node_id = int(enqueue["topics"][2], 16)
    assert words(enqueue["data"]) == [profit]
    assert [log["topics"][0].lower() for log in settlement.get("logs", [])] == [ENQUEUED]
    library_enqueue = settlement["logs"][0]
    assert library_enqueue["address"].lower() == enqueue["address"].lower()
    assert [topic.lower() for topic in library_enqueue["topics"]] == [topic.lower() for topic in enqueue["topics"]]
    assert library_enqueue["data"].lower() == enqueue["data"].lower()
    assert words(logs[1]["data"])[2] == profit
    assert words(logs[2]["data"])[1] == profit

    pre, post = storage_diff(saved)
    assert pre[18] > 0
    mask = 2**128 - 1
    reserve_excluding_queue = (
        (pre[22] & mask) + (pre[22] >> 128)
        + (fee_word & mask) + (fee_word >> 128)
    )
    ungated_available = treasury - reserve_excluding_queue
    assert ungated_available > pre[18] > 0
    assert int(saved["lp_available_with_only_queue_slot_zeroed"], 16) == ungated_available
    keccak = Keccak()
    def mapping(key, base):
        return int.from_bytes(keccak(key.to_bytes(32, "big") + base.to_bytes(32, "big")), "big")

    balance_slot, queued_slot = mapping(user, 9), mapping(user, 19)
    node_slot = mapping(node_id, 15)
    assert post[balance_slot] - pre[balance_slot] == margin
    assert post[queued_slot] - pre.get(queued_slot, 0) == profit
    assert post[18] - pre[18] == profit
    assert pre[17] == node_id and post[17] == node_id + 1
    assert post[node_slot] == user and post[node_slot + 1] == profit
    assert (post[22] & mask) - (pre[22] & mask) == margin
    assert (post[22] >> 128) - (pre[22] >> 128) == -margin
    assert 26 not in post
    return {
        "transaction": TX, "block": BLOCK, "position_id": words(logs[1]["data"])[0],
        "user": "0x" + format(user, "040x"), "margin": margin, "profit": profit,
        "available": available, "queued": profit, "node_id": node_id,
        "existing_global_queue": pre[18], "ungated_lp_available": ungated_available,
        "queue_gate_verified_by_slot_override": True,
        "fee_storage_write": False,
        "runtime_hashes_match_pin": True,
        "selected_settlement_receipt_and_storage_match": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="capture historical transaction and prestate")
    args = parser.parse_args()
    result = capture() if args.capture else verify()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
