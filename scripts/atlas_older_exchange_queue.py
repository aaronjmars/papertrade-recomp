"""Trace the older Exchange signed-close queue branch through archived calls."""

import argparse
import collections
import gzip
import json
import os
import pathlib

from atlas_exchange_library import pnl_model, settlement_model
from atlas_factory_events import Keccak
from atlas_older_exchange_library import (
    CLOSE,
    OLD_BATCH_PROXY,
    OLD_IMPLEMENTATION,
    OLD_LIBRARY,
    SCOPE,
    TRACES,
    TXLIST,
    children,
    read_gzip,
    signed,
    words,
)
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
RAW = ROOT / "artifacts" / "deployer_scope" / "older_exchange_queue_traces.json.gz"
OUT = ATLAS / "older_exchange_queue_behavior.json"
QUEUE = "0xacbc814f"
SETTLEMENT = "0xaa31b143"
MATH = "0x82296364"
OPCODE_TX = "0xe1d903a527ed571e938719d6c16a6580ba699dd9afbc6ca5bf4c1f651ae1be27"
OPCODE_SITES = {0x34C1, 0x34C6, 0x34CA, 0x34CF, 0x34D0, 0x35C2, 0x35C4,
                0x35CA, 0x369D, 0x369F, 0x36A1, 0x36A2, 0x36A3,
                0x36AD, 0x549D, 0x54A4, 0x54A7, 0x54A8, 0x57A8}


def selected_txs():
    txlist = read_gzip(TXLIST)
    assert txlist["address"] == OLD_BATCH_PROXY
    assert txlist["endblock"] == 48_902_346
    close_txs = [row for row in txlist["rows"] if CLOSE[2:] in row["input"].lower()]
    assert len(close_txs) == 20
    return close_txs


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    scope = read_gzip(SCOPE)
    assert rpc(url, "eth_getBlockByNumber", [hex(scope["pin"]), False])["hash"] == scope["block_hash"]
    saved = read_gzip(TRACES)
    old = read_gzip(RAW) if RAW.exists() else {}
    transactions = {}
    for row in selected_txs():
        tx = row["hash"]
        if tx in old.get("transactions", {}):
            pair = old["transactions"][tx]
        elif tx in saved["transactions"]:
            pair = saved["transactions"][tx]
        else:
            pair = {
                "receipt": rpc(url, "eth_getTransactionReceipt", [tx]),
                "trace": rpc(url, "debug_traceTransaction", [tx, {
                    "tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
            }
        transactions[tx] = pair
        print(tx, "block", row["blockNumber"], flush=True)
    opcode = rpc(url, "debug_traceTransaction", [OPCODE_TX, {
        "disableMemory": True, "disableStorage": True, "disableStack": False}])
    assert not opcode["failed"]
    opcode_steps = [{"pc": hex(step["pc"]), "op": step["op"],
                     "depth": step["depth"], "stack": step["stack"]}
                    for step in opcode["structLogs"] if step["pc"] in OPCODE_SITES]
    payload = {
        "pin": scope["pin"], "pin_hash": scope["block_hash"],
        "source": "20 signed-close-containing inputs in first 100 older BatchExecutor transactions before pin",
        "transactions": transactions,
        "opcode_sample": {"tx": OPCODE_TX, "steps": opcode_steps,
                          "trace_options": {"disableMemory": True, "disableStorage": True,
                                            "disableStack": False}},
    }
    RAW.write_bytes(gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0))


def build():
    scope = read_gzip(SCOPE)
    raw = read_gzip(RAW)
    assert raw["pin"] == scope["pin"] and raw["pin_hash"] == scope["block_hash"]
    txs = selected_txs()
    assert set(raw["transactions"]) == {row["hash"] for row in txs}
    cases = []
    totals = {MATH: 0, SETTLEMENT: 0, QUEUE: 0}
    pnl_branches = collections.Counter()
    rate_pairs = collections.Counter()
    for row in txs:
        tx = row["hash"]
        pair = raw["transactions"][tx]
        trace, receipt = pair["trace"], pair["receipt"]
        assert receipt["transactionHash"].lower() == tx
        assert int(receipt["blockNumber"], 16) == int(row["blockNumber"])
        assert int(receipt["status"], 16) == 1
        assert trace["to"].lower() == OLD_BATCH_PROXY
        assert trace["input"].lower() == row["input"].lower()
        close_frames = [frame for frame in children(trace)
                        if frame.get("to", "").lower() == OLD_IMPLEMENTATION
                        and frame.get("input", "").startswith(CLOSE)]
        assert len(close_frames) >= 1
        calls = [call for frame in close_frames for call in children(frame)
                 if call.get("to", "").lower() == OLD_LIBRARY]
        selectors = [call["input"][:10] for call in calls]
        assert set(selectors) <= {MATH, SETTLEMENT, QUEUE}
        assert selectors.count(MATH) == selectors.count(SETTLEMENT) + selectors.count(QUEUE)
        assert all(not frame.get("error") for frame in close_frames + calls)
        for math_call, settle_call in zip(calls[::2], calls[1::2]):
            assert math_call["input"][:10] == MATH
            assert settle_call["input"][:10] == SETTLEMENT
            math_args = words("0x" + math_call["input"][10:])
            math_out = [signed(value) for value in words(math_call["output"])]
            settle_args = words("0x" + settle_call["input"][10:])
            settle_args[3] = signed(settle_args[3])
            settle_out = words(settle_call["output"])
            assert len(math_args) == 9 and len(math_out) == 2
            assert len(settle_args) == 7 and len(settle_out) == 6
            assert math_out == pnl_model(math_args)
            assert settle_args[2] == math_args[2]
            assert settle_args[3] == math_out[1]
            assert settle_args[6] > 0
            assert settle_out == settlement_model(settle_args[:4] + [0] + settle_args[4:])
            pnl_branches["profit" if math_out[1] > 0 else "loss" if math_out[1] < 0 else "flat"] += 1
            rate_pairs[(settle_args[4], settle_args[5])] += 1
        for selector in selectors:
            totals[selector] += 1
        cases.append({"tx": tx, "block": int(row["blockNumber"]),
                      "close_frames": len(close_frames), "library_selectors": selectors})
    opcode_steps = raw["opcode_sample"]["steps"]
    assert raw["opcode_sample"]["tx"] == OPCODE_TX
    assert OPCODE_TX in raw["transactions"]
    branch_steps = [step for step in opcode_steps if step["pc"] == "0x54a7"]
    assert len(branch_steps) == 1 and branch_steps[0]["depth"] == 4
    assert int(branch_steps[0]["stack"][-1], 16) == 0x57A8
    assert int(branch_steps[0]["stack"][-2], 16) == 0
    shift_steps = [step for step in opcode_steps if step["pc"] == "0x36a1"]
    shifted = [step for step in opcode_steps if step["pc"] == "0x36a2"]
    assert len(shift_steps) == len(shifted) == 1
    packed = int(shift_steps[0]["stack"][-2], 16)
    assert int(shift_steps[0]["stack"][-1], 16) == 0xE8
    assert int(shifted[0]["stack"][-1], 16) == packed >> 232
    assert int(shifted[0]["stack"][-2], 16) == 0xFF
    assert packed >> 232 & 0xFF == 0
    sample_close = [call for call in children(raw["transactions"][OPCODE_TX]["trace"])
                    if call.get("to", "").lower() == OLD_IMPLEMENTATION
                    and call.get("input", "").startswith(CLOSE)]
    assert len(sample_close) == 1
    call_words = words("0x" + sample_close[0]["input"][10:])
    array_offset = call_words[1] // 32
    assert call_words[array_offset] == 1
    position_id = call_words[array_offset + 1]
    position_base = int.from_bytes(Keccak()(position_id.to_bytes(32, "big")
                                            + (10).to_bytes(32, "big")), "big")
    position_slot = (position_base + 1) % (2**256)
    storage_steps = [step for step in opcode_steps if step["pc"] == "0x34cf"]
    storage_return = [step for step in opcode_steps if step["pc"] == "0x34d0"]
    assert len(storage_steps) == len(storage_return) == 1
    assert int(storage_steps[0]["stack"][-1], 16) == position_slot
    assert int(storage_return[0]["stack"][-1], 16) == packed
    first_code = bytes.fromhex(next(row["runtime"][2:] for row in scope["rows"]
                                    if row["address"] == OLD_IMPLEMENTATION))
    assert first_code[0x34C0:0x34D1].hex() == "8a52600a60205260408a20600181015491"
    assert first_code[0x369D:0x36A4].hex() == "878760e81c1690"
    assert first_code[0x36AD:0x36B1].hex() == "61549d56"
    assert first_code[0x549D:0x54A8].hex() == "5b91909360a0526157a857"
    assert first_code[0x57A8:0x57B6].hex() == "5b60405163acbc814f60e01b8152"
    return {
        "pin": scope["pin"], "pin_hash": scope["block_hash"],
        "exchange_implementation": OLD_IMPLEMENTATION,
        "library": OLD_LIBRARY, "batch_proxy": OLD_BATCH_PROXY,
        "sampled_batch_transactions": len(cases),
        "sampled_close_frames": sum(case["close_frames"] for case in cases),
        "sampled_positions": totals[MATH],
        "library_call_counts": totals,
        "pnl_branches": dict(sorted(pnl_branches.items())),
        "settlement_rate_pairs": [{"positive": str(pair[0]), "negative": str(pair[1]),
                                   "calls": count} for pair, count in sorted(rate_pairs.items())],
        "queue_branch": {
            "caller_entry_pc": "0x36ad", "helper_entry_pc": "0x549d",
            "condition_pc": "0x54a7", "queue_destination_pc": "0x57a8",
            "sampled_position_id": position_id,
            "sampled_storage_slot": hex(position_slot),
            "source_word_in_sample": hex(packed),
            "sampled_branch_byte_at_bits_232_to_239": packed >> 232 & 0xFF,
            "sampled_jumppi_condition": int(branch_steps[0]["stack"][-2], 16),
            "interpretation": "The sampled close reads the packed word from keccak256(abi.encode(position_id, 10)) + 1. Its byte at bits 232 to 239 is zero, so the settlement path runs. A nonzero byte reaches the older-only queue delegatecall by bytecode control flow. A separate signed-open fork replay sets this byte from useDebt=true; no sampled historical close has it set.",
        },
        "cases": cases,
        "limits": [
            "This is a 20-transaction census of close-containing inputs within the first 100 older BatchExecutor transactions before the pin, not a census of all historical closes.",
            "All sampled closes take the settlement path. A separate exact Exchange caller replay covers constructed nonzero position bytes, but no historical invocation of that queue branch is known.",
        ],
    }


def verify():
    expected = build()
    assert json.loads(OUT.read_text()) == expected
    assert expected["sampled_batch_transactions"] == 20
    assert expected["sampled_close_frames"] == 22
    assert expected["sampled_positions"] == 136
    assert expected["library_call_counts"] == {MATH: 136, SETTLEMENT: 136, QUEUE: 0}
    assert expected["pnl_branches"] == {"flat": 35, "loss": 33, "profit": 68}
    print("Older Exchange close corpus:", expected["library_call_counts"])
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
        OUT.write_text(json.dumps(build(), indent=2) + "\n")
    verify()
