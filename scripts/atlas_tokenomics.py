#!/usr/bin/env python3
"""Capture and reconcile Papertrade Tokenomics mint paths."""

import argparse
import json
import os
import pathlib
import urllib.request

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
SESSION = ROOT / "artifacts" / "session_keys"
ARTIFACTS = ROOT / "artifacts" / "tokenomics"
PIN = 48902346
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
IMPLEMENTATION = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
TOKEN = "0xe40f17915daa230324030003a197cdaef2261c0e"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
OPEN_MINT = "0xed722c96"
OPEN_MINT_SIGNATURE = "onCloseBatch(address,uint256,uint256,uint256)"
LIQUIDATION_MINT = "0x0efdf838"
MATH = "0xe991817199363046da0a28da6fbad0284e4aa492"
TOKEN_IMPLEMENTATION = "0x433bd418ec92818a960585f4d5fae563e735bb4a"
OPEN_EVENT = "0x620c26bf4591919d64df736a6afdfe2981d15eb343c50644b49456c6facb3ab2"
LIQUIDATION_EVENT = "0x3050fba19ada85812db26b240c13c72cabec711cbf18c7c6b3554d511e2951ee"
TRANSFER_EVENT = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ADJUSTMENT_EVENT = "0x09f6ca7b163aa16d9feb37c8882b930e40c3e111f64037cb2b00adf65693e14f"
ADJUSTMENT_EVENT_SIGNATURE = "StakerLpDistributed(uint256,int256,uint256)"
ADJUSTMENT = "0xc218c676"
MODULUS = 1 << 256
PROBES_PATH = ARTIFACTS / "pinned_branch_probes.json"
MATH_PROBES_PATH = ARTIFACTS / "pinned_math_probes.json"
REDEMPTION_PROBES_PATH = ARTIFACTS / "pinned_redemption_probes.json"
WAD = 10**18


def rpc(url, method, params):
    request = urllib.request.Request(
        url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        reply = json.load(response)
    if "error" in reply:
        raise RuntimeError(f"{method}: {reply['error']}")
    return reply["result"]


def descendants(call):
    for child in call.get("calls", []):
        yield child
        yield from descendants(child)


def all_calls(call):
    yield call
    yield from descendants(call)


def input_words(data):
    assert (len(data) - 10) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(10, len(data), 64)]


def math_quote(values):
    tracked_word, progress, amount, threshold, rate, scale = values
    tracked = tracked_word if tracked_word < MODULUS // 2 else tracked_word - MODULUS
    flat_amount = min(amount, max(0, threshold - tracked))
    tail_amount = amount - flat_amount
    flat_mint = flat_amount * rate // WAD
    if not tail_amount:
        return [flat_mint, 0]
    start_factor = scale * WAD // (scale + progress)
    end_factor = scale * WAD // (scale + progress + tail_amount)
    tail_rate = (rate * start_factor // WAD) * end_factor // WAD
    return [flat_mint + tail_rate * tail_amount // WAD, tail_amount]


def selected_transactions():
    rows = []
    for path in sorted(HISTORICAL.glob("*.calls.json")):
        root = json.loads(path.read_text())
        selectors = [call.get("input", "")[:10] for call in descendants(root)
                     if call.get("to", "").lower() == TOKENOMICS
                     and call.get("input", "")[:10] in (OPEN_MINT, LIQUIDATION_MINT)]
        if selectors:
            rows.append((path.name.removesuffix(".calls.json"), selectors))
    assert len(rows) == 9
    return rows


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    for tx, selectors in selected_transactions():
        path = ARTIFACTS / f"{tx}.calls_with_logs.json"
        if not path.exists():
            trace = rpc(url, "debug_traceTransaction", [tx, {"tracer": "callTracer",
                                                               "tracerConfig": {"withLog": True}}])
            path.write_text(json.dumps(trace, indent=2) + "\n")
        print(tx, selectors, flush=True)
    capture_probes(url, manifest["block_hash"])
    capture_math_probes(url, manifest["block_hash"])
    capture_adjustments(url)
    capture_redemption_probes(url, manifest["block_hash"])


def encode_call(selector, args):
    return selector + "".join(f"{arg:064x}" for arg in args)


def capture_probes(url, block_hash):
    prior = json.loads(PROBES_PATH.read_text()) if PROBES_PATH.exists() else None
    if prior:
        assert prior["pin_block"] == PIN and prior["pin_hash"] == block_hash
    rows = prior["probes"] if prior else []
    captured = {row["name"] for row in rows}
    recipient = int("0x4444444444444444444444444444444444444444", 16)
    outsider = "0x3333333333333333333333333333333333333333"
    excess = 968649731559005181671
    if "exchange_adjustment_exact" not in captured:
        observed_excess = int(rpc(url, "eth_call", [{"to": TOKENOMICS,
            "data": "0xae745703"}, hex(PIN)]), 16)
        assert observed_excess == excess
    cases = [
        ("outside_open", outsider, OPEN_MINT, [recipient, 0, 10**18, 10**18]),
        ("exchange_open_zero", EXCHANGE, OPEN_MINT, [recipient, 0, 0, 0]),
        ("exchange_open_unequal", EXCHANGE, OPEN_MINT, [recipient, 0, 10**18, 2 * 10**18]),
        ("exchange_open_gain", EXCHANGE, OPEN_MINT, [recipient, 0, 10**18, 10**18]),
        ("outside_liquidation", outsider, LIQUIDATION_MINT, [recipient, 1, 1, 10**18, 98 * 10**16]),
        ("exchange_liquidation_bad_bool", EXCHANGE, LIQUIDATION_MINT, [recipient, 1, 2, 10**18, 98 * 10**16]),
        ("exchange_liquidation_zero", EXCHANGE, LIQUIDATION_MINT, [recipient, 1, 1, 0, 0]),
        ("outside_set_params", outsider, "0x12baae3b", [2 * 10**24, 5 * 10**24, 100 * 10**18, 120 * 10**24]),
        ("outside_adjustment", outsider, ADJUSTMENT, [excess]),
        ("exchange_adjustment_zero", EXCHANGE, ADJUSTMENT, [0]),
        ("exchange_adjustment_over", EXCHANGE, ADJUSTMENT, [excess + 1]),
        ("exchange_adjustment_exact", EXCHANGE, ADJUSTMENT, [excess]),
    ]
    for name, sender, selector, args in cases:
        if name in captured:
            continue
        call = {"from": sender, "to": TOKENOMICS, "data": encode_call(selector, args), "value": "0x0"}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN), {"tracer": "callTracer",
                                                         "tracerConfig": {"withLog": True}}])
        rows.append({"name": name, "call": call, "trace": trace})
        print(name, trace.get("error", "success"), trace.get("output", "")[:10], flush=True)
    PROBES_PATH.write_text(json.dumps({"pin_block": PIN, "pin_hash": block_hash,
                                       "probes": rows}, indent=2) + "\n")


def capture_math_probes(url, block_hash):
    if MATH_PROBES_PATH.exists():
        return
    threshold = 2 * 10**24
    scale = 120 * 10**24
    cases = [
        ("flat", [0, 0, 10**18, threshold, 100 * WAD, scale]),
        ("tail_odd_rate", [5 * 10**24, 236 * 10**24, 123456789123456789, threshold,
                           37 * WAD + 12345, scale]),
        ("tail_zero_progress", [5 * 10**24, 0, 10**18, threshold, 7 * WAD + 3, scale]),
        ("boundary_below", [threshold - 1, 0, 1, threshold, 100 * WAD, scale]),
        ("boundary_at", [threshold, 0, 1, threshold, 100 * WAD, scale]),
        ("boundary_cross", [threshold - 10**18, 0, 2 * 10**18, threshold, 100 * WAD, scale]),
    ]
    rows = []
    for name, values in cases:
        call = {"to": MATH, "data": encode_call("0x7aac24ba", values)}
        result = rpc(url, "eth_call", [call, hex(PIN)])
        rows.append({"name": name, "arguments": [str(value) for value in values],
                     "output": result})
        print("math", name, result[:66], flush=True)
    MATH_PROBES_PATH.write_text(json.dumps({"pin_block": PIN, "pin_hash": block_hash,
                                            "probes": rows}, indent=2) + "\n")


def capture_adjustments(url):
    recent = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    hashes = sorted({log["transactionHash"] for log in recent
                     if log["address"].lower() == TOKENOMICS
                     and log["topics"][0].lower() == ADJUSTMENT_EVENT})
    assert len(hashes) == 4
    for tx in hashes:
        for suffix, method, options in (
            ("calls", "debug_traceTransaction", {"tracer": "callTracer", "tracerConfig": {"withLog": True}}),
            ("state_diff", "debug_traceTransaction", {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}),
            ("receipt", "eth_getTransactionReceipt", None),
        ):
            path = ARTIFACTS / f"{tx}.{suffix}.json"
            if not path.exists():
                params = [tx, options] if options else [tx]
                path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")
        print("adjustment", tx, flush=True)


def capture_redemption_probes(url, block_hash):
    if REDEMPTION_PROBES_PATH.exists():
        return
    holder = "0x1e48c2f130a95d75b01d1caf4cec7c49c5eb2aab"
    outsider = "0x3333333333333333333333333333333333333333"
    balance = int(rpc(url, "eth_call", [{"to": TOKEN,
        "data": encode_call("0x70a08231", [int(holder, 16)])}, hex(PIN)]), 16)
    assert balance >= WAD
    cases = [
        ("quote_zero", holder, "0xfe16eae8", 0),
        ("quote_one_wei", holder, "0xfe16eae8", 1),
        ("quote_one_paper", holder, "0xfe16eae8", WAD),
        ("redeem_zero", holder, "0xdb006a75", 0),
        ("redeem_one_paper", holder, "0xdb006a75", WAD),
        ("redeem_outsider", outsider, "0xdb006a75", WAD),
    ]
    rows = []
    for name, sender, selector, amount in cases:
        call = {"from": sender, "to": TOKENOMICS,
                "data": encode_call(selector, [amount]), "value": "0x0"}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN), {"tracer": "callTracer",
                                                         "tracerConfig": {"withLog": True}}])
        rows.append({"name": name, "call": call, "trace": trace})
        print("redemption", name, trace.get("error", "success"), trace.get("output", "")[:10], flush=True)
    REDEMPTION_PROBES_PATH.write_text(json.dumps({"pin_block": PIN, "pin_hash": block_hash,
                                                  "holder": holder, "holder_balance": str(balance),
                                                  "probes": rows}, indent=2) + "\n")


def storage_delta(diff, address, slot):
    key = f"0x{slot:064x}"
    before = diff["pre"].get(address, {}).get("storage", {}).get(key, "0x0")
    after = diff["post"].get(address, {}).get("storage", {}).get(key, before)
    return (int(after, 16) - int(before, 16)) % MODULUS


def storage_before(diff, address, slot):
    key = f"0x{slot:064x}"
    return int(diff["pre"].get(address, {}).get("storage", {}).get(key, "0x0"), 16)


def verify_probes():
    saved = json.loads(PROBES_PATH.read_text())
    assert saved["pin_block"] == PIN
    assert saved["pin_hash"] == json.loads((ATLAS / "manifest.json").read_text())["block_hash"]
    probes = {row["name"]: row for row in saved["probes"]}
    assert len(probes) == 12
    expected_errors = {"outside_open": "0xe343677f",
                       "exchange_open_unequal": "0x85c58396",
                       "outside_liquidation": "0xe343677f",
                       "outside_set_params": "0x30cd7471",
                       "outside_adjustment": "0xe343677f",
                       "exchange_adjustment_over": "0xe247b81f"}
    for name, selector in expected_errors.items():
        assert probes[name]["trace"].get("error") == "execution reverted"
        assert probes[name]["trace"].get("output") == selector
    assert probes["exchange_liquidation_bad_bool"]["trace"].get("error") == "execution reverted"
    assert not probes["exchange_liquidation_bad_bool"]["trace"].get("output")
    for name in ("exchange_open_zero", "exchange_open_gain", "exchange_liquidation_zero",
                 "exchange_adjustment_zero", "exchange_adjustment_exact"):
        assert not probes[name]["trace"].get("error")
    def children(row):
        return list(descendants(probes[row]["trace"]))
    assert any(log["topics"][0] == OPEN_EVENT for call in children("exchange_open_zero")
               for log in call.get("logs", []))
    assert not any(call.get("to", "").lower() == MATH for call in children("exchange_open_zero"))
    assert any(call.get("to", "").lower() == MATH for call in children("exchange_open_gain"))
    assert any(call.get("to", "").lower() == TOKEN and call.get("input", "")[:10] == "0x40c10f19"
               for call in children("exchange_open_gain"))
    assert not any(call.get("logs") for call in children("exchange_liquidation_zero"))
    assert not any(call.get("logs") for call in children("exchange_adjustment_zero"))
    adjustment_logs = [log for call in children("exchange_adjustment_exact")
                       for log in call.get("logs", []) if log["topics"][0] == ADJUSTMENT_EVENT]
    assert len(adjustment_logs) == 1
    assert input_words("0x00000000" + adjustment_logs[0]["data"][2:])[:2] == [
        968649731559005181671, 5 * 10**24]
    return {"count": len(probes), "checks": "all_passed"}


def verify_math_probes():
    saved = json.loads(MATH_PROBES_PATH.read_text())
    assert saved["pin_block"] == PIN
    assert saved["pin_hash"] == json.loads((ATLAS / "manifest.json").read_text())["block_hash"]
    probes = saved["probes"]
    assert {row["name"] for row in probes} == {"flat", "tail_odd_rate", "tail_zero_progress",
                                                   "boundary_below", "boundary_at", "boundary_cross"}
    for row in probes:
        values = [int(value) for value in row["arguments"]]
        output = input_words("0x00000000" + row["output"][2:])
        assert output == math_quote(values), row["name"]
    return {"count": len(probes), "checks": "all_passed"}


def verify_redemption_probes():
    saved = json.loads(REDEMPTION_PROBES_PATH.read_text())
    assert saved["pin_block"] == PIN
    assert saved["pin_hash"] == json.loads((ATLAS / "manifest.json").read_text())["block_hash"]
    assert int(saved["holder_balance"]) >= WAD
    probes = saved["probes"]
    assert {row["name"] for row in probes} == {"quote_zero", "quote_one_wei", "quote_one_paper",
                                                   "redeem_zero", "redeem_one_paper", "redeem_outsider"}
    for row in probes:
        assert row["trace"].get("error") == "execution reverted"
        assert row["trace"].get("output") == "0x32aa90b0"
        assert not any(call.get("logs") for call in descendants(row["trace"]))
    return {"count": len(probes), "revert_selector": "0x32aa90b0",
            "holder_balance": saved["holder_balance"]}


def analyze():
    rows = []
    adjustments = []
    transaction_rows = []
    files = (list(ARTIFACTS.glob("*.calls_with_logs.json")) +
             list(ARTIFACTS.glob("*.calls.json")) + list(SESSION.glob("*.calls.json")))
    assert len(list(ARTIFACTS.glob("*.calls_with_logs.json"))) == 9
    assert len(list(ARTIFACTS.glob("*.calls.json"))) == 5
    for path in sorted(files):
        tx = path.name.split(".")[0]
        trace = json.loads(path.read_text())
        calls = [call for call in all_calls(trace)
                 if call.get("to", "").lower() == TOKENOMICS
                 and call.get("input", "")[:10] in (OPEN_MINT, LIQUIDATION_MINT, ADJUSTMENT)]
        if not calls:
            continue
        diff_paths = (list(HISTORICAL.glob(f"{tx}.state_diff.json")) +
                      list(SESSION.glob(f"{tx}.state_diff.json")) +
                      list(ARTIFACTS.glob(f"{tx}.state_diff.json")))
        assert len(diff_paths) == 1
        diff = json.loads(diff_paths[0].read_text())
        tracked_state = storage_before(diff, TOKENOMICS, 3)
        tail_state = storage_before(diff, TOKENOMICS, 4)
        total_tracked_delta = 0
        total_tail_delta = 0
        total_minted = 0
        for ordinal, call in enumerate(calls):
            selector = call["input"][:10]
            args = input_words(call["input"])
            if selector == ADJUSTMENT:
                assert len(args) == 1 and call["from"].lower() == EXCHANGE
                assert not call.get("error")
                impls = [child for child in call.get("calls", [])
                         if child.get("to", "").lower() == IMPLEMENTATION]
                assert len(impls) == 1
                adjustment_logs = [log for log in impls[0].get("logs", [])
                                   if log["topics"][0].lower() == ADJUSTMENT_EVENT]
                assert len(adjustment_logs) == 1
                event = adjustment_logs[0]
                assert event["address"].lower() == TOKENOMICS and len(event["topics"]) == 1
                fields = input_words("0x00000000" + event["data"][2:])
                assert len(fields) == 3 and fields[0] == args[0]
                assert fields[1] == (tracked_state - args[0]) % MODULUS
                assert fields[1] == 5 * 10**24 and fields[2] == tail_state
                adjustments.append({"tx": tx, "ordinal": ordinal, "selector": selector,
                                    "amount": str(args[0]), "before": str(tracked_state),
                                    "after": str(fields[1]), "tail_progress": str(fields[2]),
                                    "event_topic": ADJUSTMENT_EVENT})
                tracked_state = fields[1]
                total_tracked_delta -= args[0]
                continue
            assert len(args) == (4 if selector == OPEN_MINT else 5)
            assert call["from"].lower() == EXCHANGE and not call.get("error")
            recipient = f"0x{args[0]:040x}"
            impls = [child for child in call.get("calls", [])
                     if child.get("to", "").lower() == IMPLEMENTATION]
            assert len(impls) == 1 and not impls[0].get("error")
            event_hash = OPEN_EVENT if selector == OPEN_MINT else LIQUIDATION_EVENT
            logs = [log for log in impls[0].get("logs", [])
                    if log["topics"][0].lower() == event_hash]
            assert len(logs) == 1
            event = logs[0]
            assert event["address"].lower() == TOKENOMICS
            assert len(event["topics"]) == (2 if selector == OPEN_MINT else 3)
            assert int(event["topics"][1], 16) == args[0]
            event_words = input_words("0x00000000" + event["data"][2:])
            assert len(event_words) == 6
            assert (event_words[3] - event_words[2]) % MODULUS == (
                args[3] if selector == OPEN_MINT else args[4])
            if selector == OPEN_MINT:
                assert event_words[:2] == args[1:3]
                assert event_words[4] in (0, args[2])
                assert event_words[2] == (tracked_state - args[1]) % MODULUS
                total_tracked_delta += -args[1] + args[3]
            else:
                assert int(event["topics"][2], 16) == args[1]
                assert event_words[:2] == args[2:4]
                assert event_words[4] == args[3]
                assert event_words[2] == tracked_state
                total_tracked_delta += args[4]
            tracked_state = event_words[3]
            mint_calls = [child for child in descendants(call)
                          if child.get("to", "").lower() == TOKEN
                          and child.get("input", "")[:10] == "0x40c10f19"]
            minted = event_words[5]
            assert len(mint_calls) == (1 if minted else 0)
            if minted:
                mint_args = input_words(mint_calls[0]["input"])
                assert mint_args == [args[0], minted]
                token_impls = [child for child in mint_calls[0].get("calls", [])
                               if child.get("to", "").lower() == TOKEN_IMPLEMENTATION]
                assert len(token_impls) == 1
                transfer = token_impls[0]["logs"]
                assert len(transfer) == 1 and transfer[0]["topics"][0].lower() == TRANSFER_EVENT
                assert transfer[0]["address"].lower() == TOKEN
                assert int(transfer[0]["topics"][1], 16) == 0
                assert int(transfer[0]["topics"][2], 16) == args[0]
                assert int(transfer[0]["data"], 16) == minted
            math_calls = [child for child in descendants(call)
                          if child.get("to", "").lower() == MATH
                          and child.get("input", "")[:10] == "0x7aac24ba"]
            assert len(math_calls) == (1 if minted else 0)
            math_args = None
            if math_calls:
                math_args = input_words(math_calls[0]["input"])
                math_output = input_words("0x00000000" + math_calls[0]["output"][2:])
                assert len(math_args) == 6 and math_output == [minted, event_words[4]]
                assert math_output == math_quote(math_args)
                assert math_args[0] == event_words[2]
                assert math_args[1] == tail_state
                assert math_args[2] == (args[2] if selector == OPEN_MINT else args[3])
                assert math_args[3:] == [2 * 10**24, 100 * 10**18, 120 * 10**24]
            tail_state += event_words[4]
            total_tail_delta += event_words[4]
            total_minted += minted
            rows.append({"tx": tx, "ordinal": ordinal, "selector": selector,
                         "recipient": recipient, "arguments": [str(v) for v in args[1:]],
                         "event_topic": event_hash, "event_words": [str(v) for v in event_words],
                         "minted": str(minted), "math_arguments":
                         [str(v) for v in math_args] if math_args else None})
        checks = {"tracked_lp_usd_slot_3": storage_delta(diff, TOKENOMICS, 3) == total_tracked_delta % MODULUS,
                  "tail_progress_usd_slot_4": storage_delta(diff, TOKENOMICS, 4) == total_tail_delta,
                  "paper_total_supply_slot_6": storage_delta(diff, TOKEN, 6) == total_minted}
        assert all(checks.values()), (tx, checks)
        assert tracked_state == (storage_before(diff, TOKENOMICS, 3) + total_tracked_delta) % MODULUS
        assert tail_state == storage_before(diff, TOKENOMICS, 4) + total_tail_delta
        tx_adjustments = [row for row in adjustments if row["tx"] == tx]
        if tx_adjustments:
            assert len(tx_adjustments) == 1
            excess_getters = [call for call in all_calls(trace)
                              if call.get("to", "").lower() == TOKENOMICS
                              and call.get("input", "")[:10] == "0xae745703"]
            assert len(excess_getters) == 2
            assert [int(call["output"], 16) for call in excess_getters] == [
                int(tx_adjustments[0]["amount"]), 0]
        transaction_rows.append({"tx": tx, "call_count": len(calls), "minted": str(total_minted),
                                 "tracked_delta_signed": str(total_tracked_delta),
                                 "tail_delta": str(total_tail_delta), "storage_checks": checks})
    assert len(rows) == 38 and len(transaction_rows) == 20
    assert len(adjustments) == 4
    assert "0x" + Keccak()(ADJUSTMENT_EVENT_SIGNATURE.encode()).hex() == ADJUSTMENT_EVENT
    assert "0x" + Keccak()(OPEN_MINT_SIGNATURE.encode()).hex()[:8] == OPEN_MINT
    assert sum(row["selector"] == OPEN_MINT for row in rows) == 32
    assert sum(row["selector"] == LIQUIDATION_MINT for row in rows) == 6
    mint_count = sum(int(row["minted"]) > 0 for row in rows)
    assert mint_count == 25
    error_catalog = [
        {"selector": selector, "probe_paths": paths, "public_signature_candidates": []}
        for selector, paths in (
            ("0xe343677f", ["outside_open", "outside_liquidation", "outside_adjustment"]),
            ("0x85c58396", ["exchange_open_unequal"]),
            ("0x30cd7471", ["outside_set_params"]),
            ("0xe247b81f", ["exchange_adjustment_over"]),
            ("0x32aa90b0", ["quote_zero", "quote_one_wei", "quote_one_paper",
                            "redeem_zero", "redeem_one_paper", "redeem_outsider"]),
        )
    ]
    result = {"pin_block": PIN, "transaction_count": len(transaction_rows),
              "tokenomics_proxy": TOKENOMICS, "implementation": IMPLEMENTATION,
              "call_count": len(rows), "adjustment_call_count": len(adjustments),
              "mint_count": mint_count,
              "read_only_branch_probes": verify_probes(),
              "read_only_math_probes": verify_math_probes(),
              "read_only_redemption_probes": verify_redemption_probes(),
              "transactions": transaction_rows, "calls": rows, "adjustments": adjustments,
              "selector_reconstructions": {OPEN_MINT: OPEN_MINT_SIGNATURE},
              "event_catalog": [{"topic0": ADJUSTMENT_EVENT,
                                 "reconstructed_signature": ADJUSTMENT_EVENT_SIGNATURE,
                                 "status": "observed_historical_topic"}],
              "simulated_error_catalog": error_catalog,
              "limitations": ["Two mint event names and the liquidation mint function name are unresolved.",
                              "The PaperMath formula matches sampled tail, flat, and crossing paths; other input bounds remain untested.",
                              "Samples contain no executed mint-parameter update or redemption; all six pinned valid redemption calls reverted."]}
    output = ATLAS / "tokenomics_observed_paths.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Verified {len(rows)} settlement calls and {len(adjustments)} adjustments in "
          f"{len(transaction_rows)} transactions; {mint_count} PAPER mints")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    analyze()
