#!/usr/bin/env python3
"""Resolve Exchange queue, pending-sweep, and Core-withdrawal getters."""

import argparse
import json
import os
import pathlib

from atlas_exchange_queue_layout import AMOUNT, KECCAK, PROXY, mapped
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_getters"
HISTORICAL = ROOT / "artifacts" / "historical"
SWEEPS = ROOT / "artifacts" / "exchange_sweeps"
CORE = ROOT / "artifacts" / "exchange_core_withdrawal"
PIN = 48902346
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
QUEUE_BLOCK = 48173889
EARLIER_WITHDRAWAL_TX = "0x3b56a71e00561f356eace90ce1a0b2845540aca891cc092cde3b4452567948b7"
EARLIER_WITHDRAWAL_BLOCK = 48783615
SIGNATURES = {
    "0x3a21be03": "userQueueTail(address)",
    "0x551306f3": "userQueuedTotal(address)",
    "0x31a4956c": "getPendingSweep(address)",
    "0x7e4174fc": "pendingSweepWord(address)",
    "0x32faa570": "lastCoreWithdrawalBlock(address)",
    "0xdcab7f6a": "userQueueHead(address)",
}
PATH = ARTIFACTS / "historical_getter_calls.json"


def read(name):
    return json.loads((ATLAS / name).read_text())


def artifact(folder, tx, suffix):
    historical = HISTORICAL / f"{tx}.{suffix}.json"
    return historical if historical.exists() else folder / f"{tx}.{suffix}.json"


def diff_word(diff, phase, slot):
    return int(diff.get(phase, {}).get(PROXY, {}).get("storage", {}).get(slot, "0x0"), 16)


def result_words(result):
    assert result.startswith("0x") and (len(result) - 2) % 64 == 0
    return [int(result[i:i + 64], 16) for i in range(2, len(result), 64)]


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read("manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    queue = read("exchange_queue_layout_behavior.json")["enqueues"]
    sweeps = read("exchange_sweep_behavior.json")["records"]
    withdrawals = read("exchange_core_withdrawal_behavior.json")["transactions"]
    cases = []

    def call(label, user, block, selector):
        data = selector + int(user, 16).to_bytes(32, "big").hex()
        output = rpc(url, "eth_call", [{"to": PROXY, "data": data}, hex(block)])
        cases.append({"label": label, "user": user.lower(), "block": block,
                      "selector": selector, "output": output,
                      "words": [str(value) for value in result_words(output)]})

    for row in queue:
        for label, block in (("queue_before_harvest", QUEUE_BLOCK),
                             ("queue_after_harvest", QUEUE_BLOCK + 1)):
            for selector in ("0x551306f3", "0xdcab7f6a", "0x3a21be03"):
                call(label, row["user"], block, selector)
    for row in sweeps:
        for label, block in (("sweep_after_request", row["request_block"]),
                             ("sweep_after_finalize", row["finalize_block"])):
            for selector in ("0x31a4956c", "0x7e4174fc"):
                call(label, row["user"], block, selector)
    for row in withdrawals:
        for label, block in (("withdrawal_before", row["block"] - 1),
                             ("withdrawal_after", row["block"])):
            call(label, row["user"], block, "0x32faa570")

    earlier_user = sweeps[0]["user"]
    for suffix, method, params in (
        ("receipt", "eth_getTransactionReceipt", [EARLIER_WITHDRAWAL_TX]),
        ("state_diff", "debug_traceTransaction",
         [EARLIER_WITHDRAWAL_TX, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}]),
        ("calls", "debug_traceTransaction",
         [EARLIER_WITHDRAWAL_TX, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
    ):
        path = ARTIFACTS / f"{EARLIER_WITHDRAWAL_TX}.{suffix}.json"
        if not path.exists():
            path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")
    for label, block in (("earlier_withdrawal_before", EARLIER_WITHDRAWAL_BLOCK - 1),
                         ("earlier_withdrawal_after", EARLIER_WITHDRAWAL_BLOCK),
                         ("sweep_user_last_withdrawal_request", sweeps[0]["request_block"]),
                         ("sweep_user_last_withdrawal_final", sweeps[0]["finalize_block"])):
        call(label, earlier_user, block, "0x32faa570")
    PATH.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                "cases": cases}, indent=2) + "\n")
    print("captured", len(cases), "historical Exchange getter outputs")


def verify():
    for selector, signature in SIGNATURES.items():
        assert "0x" + KECCAK(signature.encode()).hex()[:8] == selector
    manifest = read("manifest.json")
    assert manifest["block"] == PIN and manifest["contracts"][PROXY]["eip1967_slots"]["implementation"][-40:] == IMPLEMENTATION[2:]
    catalog = read("selector_catalog.json")[IMPLEMENTATION]
    assert set(SIGNATURES) <= {row["selector"] for row in catalog["functions"]}
    saved = json.loads(PATH.read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    cases = saved["cases"]
    index = {(row["label"], row["user"], row["block"], row["selector"]): row for row in cases}
    assert len(index) == len(cases) == 80
    assert all(result_words(row["output"]) == [int(value) for value in row["words"]] for row in cases)

    def output(label, user, block, selector):
        return [int(value) for value in index[(label, user.lower(), block, selector)]["words"]]

    storage = read("storage_trace_catalog.json")[IMPLEMENTATION]["views"]
    views = {row["selector"]: row for row in storage}
    expected_bases = {"0x551306f3": 19, "0xdcab7f6a": 20, "0x3a21be03": 21,
                      "0x31a4956c": 33, "0x7e4174fc": 33, "0x32faa570": 34}
    for selector, base in expected_bases.items():
        assert any(row["base_slot"] == base and row["field_offset"] == 0
                   for row in views[selector]["mapping_matches"])

    queue = read("exchange_queue_layout_behavior.json")["enqueues"]
    for row in queue:
        user, node_id = row["user"], row["node_id"]
        assert output("queue_before_harvest", user, QUEUE_BLOCK, "0x551306f3") == [AMOUNT]
        assert output("queue_before_harvest", user, QUEUE_BLOCK, "0xdcab7f6a") == [node_id]
        assert output("queue_before_harvest", user, QUEUE_BLOCK, "0x3a21be03") == [node_id]
        assert all(output("queue_after_harvest", user, QUEUE_BLOCK + 1, selector) == [0]
                   for selector in ("0x551306f3", "0xdcab7f6a", "0x3a21be03"))

    sweeps = read("exchange_sweep_behavior.json")["records"]
    for row in sweeps:
        user, request_block, finalize_block = row["user"], row["request_block"], row["finalize_block"]
        spot, perp = row["spot_raw"], row["perp_raw"]
        packed = spot | (perp << 64) | (request_block << 128)
        assert output("sweep_after_request", user, request_block, "0x31a4956c") == [
            1, spot, perp, request_block]
        assert output("sweep_after_request", user, request_block, "0x7e4174fc") == [packed]
        assert output("sweep_after_finalize", user, finalize_block, "0x31a4956c") == [0, 0, 0, 0]
        assert output("sweep_after_finalize", user, finalize_block, "0x7e4174fc") == [0]
        request = json.loads(artifact(SWEEPS, row["request_tx"], "state_diff").read_text())
        finalize = json.loads(artifact(SWEEPS, row["finalize_tx"], "state_diff").read_text())
        assert diff_word(request, "post", row["pending_slot"]) == packed
        assert diff_word(finalize, "pre", row["pending_slot"]) == packed
        assert diff_word(finalize, "post", row["pending_slot"]) == 0

    withdrawals = read("exchange_core_withdrawal_behavior.json")["transactions"]
    for row in withdrawals:
        user, block, tx = row["user"], row["block"], row["tx"]
        slot_key = mapped(int(user, 16), 34)
        diff = json.loads(artifact(CORE, tx, "state_diff").read_text())
        before = output("withdrawal_before", user, block - 1, "0x32faa570")[0]
        after = output("withdrawal_after", user, block, "0x32faa570")[0]
        assert before == diff_word(diff, "pre", slot_key)
        assert after == diff_word(diff, "post", slot_key) == block

    earlier_user = sweeps[0]["user"]
    receipt = json.loads((ARTIFACTS / f"{EARLIER_WITHDRAWAL_TX}.receipt.json").read_text())
    diff = json.loads((ARTIFACTS / f"{EARLIER_WITHDRAWAL_TX}.state_diff.json").read_text())
    call = json.loads((ARTIFACTS / f"{EARLIER_WITHDRAWAL_TX}.calls.json").read_text())
    core_topic = read("exchange_core_withdrawal_behavior.json")["event_catalog"][0]["topic0"]
    assert int(receipt["blockNumber"], 16) == EARLIER_WITHDRAWAL_BLOCK and receipt["status"] == "0x1"
    assert call["from"].lower() == receipt["from"].lower()
    assert any(log["address"].lower() == PROXY and log["topics"][:2] == [
        core_topic, "0x" + int(earlier_user, 16).to_bytes(32, "big").hex()]
        for log in receipt["logs"])
    slot_key = mapped(int(earlier_user, 16), 34)
    assert output("earlier_withdrawal_before", earlier_user, EARLIER_WITHDRAWAL_BLOCK - 1,
                  "0x32faa570") == [diff_word(diff, "pre", slot_key)]
    assert output("earlier_withdrawal_after", earlier_user, EARLIER_WITHDRAWAL_BLOCK,
                  "0x32faa570") == [diff_word(diff, "post", slot_key)] == [EARLIER_WITHDRAWAL_BLOCK]
    assert output("sweep_user_last_withdrawal_request", earlier_user,
                  sweeps[0]["request_block"], "0x32faa570") == [EARLIER_WITHDRAWAL_BLOCK]
    assert output("sweep_user_last_withdrawal_final", earlier_user,
                  sweeps[0]["finalize_block"], "0x32faa570") == [EARLIER_WITHDRAWAL_BLOCK]

    result = {"pin_block": PIN, "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
              "selector_reconstructions": {selector: signature for selector, signature in SIGNATURES.items()
                                           if selector != "0xdcab7f6a"},
              "already_named_selector": {"0xdcab7f6a": SIGNATURES["0xdcab7f6a"]},
              "mapping_bases": {"user_queue_total": 19, "user_queue_head": 20,
                                "user_queue_tail": 21, "pending_sweep": 33,
                                "last_core_withdrawal_block": 34},
              "queue_user_count": len(queue), "sweep_pair_count": len(sweeps),
              "signed_core_withdrawal_count": len(withdrawals) + 1,
              "historical_getter_call_count": len(cases),
              "pending_sweep_tuple": "exists, spotRaw uint64, perpRaw uint64, requestBlock uint32",
              "pending_sweep_raw": "spotRaw in bits 0-63, perpRaw in bits 64-127, requestBlock in bits 128-159",
              "limitations": ["Function names are exact selector preimages checked against observed storage and return values.",
                              "The sampled pending sweeps are spot-only; perp word placement is supported by linked sweep fork probes.",
                              "Historical block-level getters do not prove same-block transaction ordering or every caller branch."]}
    (ATLAS / "exchange_getters_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange getters: 5 new exact names, 13 pending sweep pairs, and 4 Core withdrawal blocks verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
