#!/usr/bin/env python3
"""Replay Papertrade accounting branches without submitting transactions."""

import json
import pathlib

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "historical" / "replays"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
LIQUIDATION_TX = "0xff619c8c3758e4a04ea9fbf0b16fabbdf503244418c3bdc5e82c70081d9b2ce6"
QUEUE_BLOCK = 48173887
SURPLUS_BLOCK = 48899300
QUEUE_SLOT = "0x" + format(18, "064x")
ONE_WEI = "0x" + format(1, "064x")
CURSOR_SLOT = "0x" + format(3, "064x")
SYNTHETIC_CURSOR = "0x" + format(5_000_100 * 10**18, "064x")


def save(label, call, block, overrides=None):
    params = [call, hex(block), {"tracer": "callTracer"}]
    if overrides:
        params[2]["stateOverrides"] = overrides
    call_trace = rpc("debug_traceCall", params)
    if call_trace.get("error"):
        raise RuntimeError(f"{label}: {call_trace['error']}")
    diff_options = {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}
    if overrides:
        diff_options["stateOverrides"] = overrides
    state_diff = rpc("debug_traceCall", [call, hex(block), diff_options])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{label}.calls.json").write_text(json.dumps(call_trace, indent=2) + "\n")
    (OUT / f"{label}.state_diff.json").write_text(json.dumps(state_diff, indent=2) + "\n")
    return {"label": label, "block": block, "call": call, "state_overrides": overrides or {},
            "call_trace": f"{label}.calls.json", "state_diff": f"{label}.state_diff.json"}


def main():
    if int(rpc("eth_chainId", []), 16) != 999:
        raise ValueError("wrong chain")
    tx = rpc("eth_getTransactionByHash", [LIQUIDATION_TX])
    if not tx or tx["to"].lower() != EXCHANGE:
        raise ValueError("liquidation transaction missing or changed")
    liquidation_block = int(tx["blockNumber"], 16) - 1
    if int(rpc("eth_getStorageAt", [EXCHANGE, QUEUE_SLOT, hex(liquidation_block)]), 16):
        raise ValueError("liquidation baseline already has a queue")
    liquidation_call = {key: tx[key] for key in ("from", "to", "input", "value", "gas")}
    queue_override = {EXCHANGE: {"stateDiff": {QUEUE_SLOT: ONE_WEI}}}
    rows = [
        save("liquidation_baseline", liquidation_call, liquidation_block),
        save("liquidation_queue_override", liquidation_call, liquidation_block, queue_override),
    ]
    push_call = {"from": "0x89ab620bee7e1ec675eec5291cba3686d9e059bf", "to": EXCHANGE,
                 "input": "0x7b9f5264", "gas": hex(2_000_000), "value": "0x0"}
    cursor_override = {TOKENOMICS: {"stateDiff": {CURSOR_SLOT: SYNTHETIC_CURSOR}}}
    rows.extend([
        save("push_during_real_queue", push_call, QUEUE_BLOCK),
        save("push_real_queue_with_surplus_cursor", push_call, QUEUE_BLOCK, cursor_override),
        save("push_surplus_baseline", push_call, SURPLUS_BLOCK),
        save("push_surplus_queue_override", push_call, SURPLUS_BLOCK, queue_override),
    ])
    manifest = {"chain_id": 999, "liquidation_transaction": LIQUIDATION_TX,
                "queue_slot": QUEUE_SLOT, "queue_override_value": ONE_WEI, "replays": rows,
                "note": "debug_traceCall is read-only. Each override changes only the named storage slot for that simulated call. The launch queue replay retains its real queue nodes and overrides only the Tokenomics LP cursor."}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(OUT / "manifest.json")


if __name__ == "__main__":
    main()
