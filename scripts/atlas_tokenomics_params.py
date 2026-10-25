#!/usr/bin/env python3
"""Verify the unexecuted Tokenomics mint-parameter update at the pinned block."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_paper_token import calldata
from atlas_tokenomics import (EXCHANGE, IMPLEMENTATION, MATH, OPEN_EVENT, OPEN_MINT, PIN,
                             TOKEN, TOKENOMICS, descendants, encode_call, input_words, math_quote, rpc)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "tokenomics_params" / "pinned_probes.json"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x1234567890123456789012345678901234567890"
SELECTOR = "0x12baae3b"
SIGNATURE = "setMintParams(uint256,uint256,uint256,uint256)"
EXCESS_GETTER_SIGNATURE = "stakerLpDistributableExcessUsd()"
ADJUSTMENT_SIGNATURE = "distributeLpToStakers(uint256)"
EVENT_SIGNATURE = "MintParamsUpdated(uint256,uint256,uint256,uint256)"
EVENT_TOPIC = "0xdbf6f1878073adede0b153c63f457c1c601a056124755086092f973f19550176"
ERRORS = {"InvalidMintParams()": "0xbad8ef95", "NotOwner()": "0x30cd7471"}
TIMELOCK_OWNER = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
TIMELOCK_EXECUTE = "0x88aa4c12"
CURRENT = [2 * 10**24, 5 * 10**24, 100 * 10**18, 120 * 10**24]
DISTINCT = [3 * 10**24, 6 * 10**24, 110 * 10**18, 130 * 10**24]


def word(value):
    return f"0x{value:064x}"


def execute_calldata(operation, payload):
    encode_word = lambda value: value.to_bytes(32, "big")
    args = (encode_word(int(TOKENOMICS, 16)) + encode_word(0) + encode_word(128)
            + bytes.fromhex(operation["predecessor"][2:]) + encode_word(len(payload))
            + payload.ljust((len(payload) + 31) // 32 * 32, b"\0"))
    return TIMELOCK_EXECUTE + args.hex()


def nested_logs(call):
    result = list(call.get("logs", []))
    for child in call.get("calls", []):
        result.extend(nested_logs(child))
    return result


def cases(scheduled):
    values = {"scheduled": scheduled, "distinct": DISTINCT, "noop_current": CURRENT,
              "outsider_distinct": DISTINCT, "all_zero": [0, 0, 0, 0],
              "equal_threshold_floor": [5 * 10**24, 5 * 10**24, CURRENT[2], CURRENT[3]],
              "threshold_above_floor": [CURRENT[1] + 1, CURRENT[1], CURRENT[2], CURRENT[3]],
              "inverted_distinct": [6 * 10**24, 3 * 10**24, DISTINCT[2], DISTINCT[3]],
              "tiny_rate": [CURRENT[0], CURRENT[1], 1, CURRENT[3]],
              "tiny_scale": [CURRENT[0], CURRENT[1], CURRENT[2], 1],
              "max_rate": [CURRENT[0], CURRENT[1], 2**256 - 1, CURRENT[3]]}
    for index, name in enumerate(("threshold", "floor", "rate", "scale")):
        args = CURRENT.copy()
        args[index] = 0
        values[f"zero_{name}"] = args
    assert len(values) == 15
    return values


def capture():
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    if ARTIFACT.exists():
        return
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    operation = next(row for row in json.loads((ATLAS / "timelock_operations.json").read_text())["operations"]
                     if row["call_selector"] == SELECTOR)
    scheduled = operation["call_arguments_uint256_words"]
    probes = {}
    for name, arguments in cases(scheduled).items():
        sender = OUTSIDER if name == "outsider_distinct" else OWNER
        data = calldata(SELECTOR, *arguments)
        call = {"from": sender, "to": TOKENOMICS, "data": data}
        traced = rpc(url, "debug_traceCall", [call, hex(PIN),
                                                {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        row = {"sender": sender, "arguments": [str(x) for x in arguments], "calldata": data,
               "error": traced.get("error"), "output": traced.get("output", ""),
               "implementation_calls": [{"type": child["type"], "to": child["to"],
                                         "input": child["input"]} for child in traced.get("calls", [])],
               "logs": nested_logs(traced)}
        if name in ("scheduled", "distinct", "noop_current"):
            diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                                                 {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            row["pre_storage"] = diff.get("pre", {}).get(TOKENOMICS, {}).get("storage", {})
            row["post_storage"] = diff.get("post", {}).get(TOKENOMICS, {}).get("storage", {})
        probes[name] = row
    slots = {str(index): rpc(url, "eth_getStorageAt", [TOKENOMICS, hex(index), hex(PIN)])
             for index in range(3, 9)}
    tracked = int(slots["3"], 16)
    floor_probes = []
    for floor in (0, CURRENT[1], scheduled[1], tracked + 1):
        output = rpc(url, "eth_call", [
            {"to": TOKENOMICS, "data": "0xae745703"}, hex(PIN),
            {TOKENOMICS: {"stateDiff": {word(6): word(floor)}}}])
        floor_probes.append({"floor": str(floor), "output": output})
    ARTIFACT.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                    "scheduled_operation_id": operation["operation_id"],
                                    "scheduled_operation_executed_at_pin": operation["is_done_at_pin"],
                                    "probes": probes, "pinned_slots": slots,
                                    "excess_getter_selector": "0xae745703",
                                    "excess_getter_floor_probes": floor_probes}, indent=2) + "\n")


def capture_governance():
    saved = json.loads(ARTIFACT.read_text())
    if "governance_execution" in saved:
        return
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    operation = next(row for row in json.loads((ATLAS / "timelock_operations.json").read_text())["operations"]
                     if row["operation_id"] == saved["scheduled_operation_id"])
    payload = bytes.fromhex(saved["probes"]["scheduled"]["calldata"][2:])
    call = {"from": TIMELOCK_OWNER, "to": OWNER, "data": execute_calldata(operation, payload),
            "gas": "0x989680"}
    trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                                          {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
    target_call = trace["calls"][0]
    implementation_call = target_call["calls"][0]
    saved["governance_execution"] = {
        "sender": TIMELOCK_OWNER, "calldata": call["data"], "error": trace.get("error"),
        "timelock_logs": trace.get("logs", []),
        "target_call": {"type": target_call["type"], "to": target_call["to"],
                        "input": target_call["input"], "error": target_call.get("error"),
                        "logs": target_call.get("logs", [])},
        "implementation_call": {"type": implementation_call["type"],
                                "to": implementation_call["to"],
                                "input": implementation_call["input"],
                                "error": implementation_call.get("error"),
                                "logs": implementation_call.get("logs", [])}}
    ARTIFACT.write_text(json.dumps(saved, indent=2) + "\n")


def capture_downstream():
    saved = json.loads(ARTIFACT.read_text())
    if "downstream_mint_probes" in saved:
        return
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    recipient = int("0x4444444444444444444444444444444444444444", 16)
    call = {"from": EXCHANGE, "to": TOKENOMICS,
            "data": encode_call(OPEN_MINT, [recipient, 0, 10**18, 10**18]), "gas": "0x989680"}
    variants = {"baseline": {}, "scheduled_floor": {6: 10 * 10**24},
                "distinct_parameters": dict(zip(range(5, 9), DISTINCT)),
                "flat_threshold": {5: 6 * 10**24, 6: 10 * 10**24}}
    rows = []
    for name, slots in variants.items():
        opts = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
        if slots:
            opts["stateOverrides"] = {TOKENOMICS: {"stateDiff": {word(k): word(v)
                                                                  for k, v in slots.items()}}}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN), opts])
        children = list(descendants(trace))
        math = next(child for child in children if child.get("to", "").lower() == MATH)
        mint = next(child for child in children if child.get("to", "").lower() == TOKEN
                    and child.get("input", "").startswith("0x40c10f19"))
        event = next(log for log in nested_logs(trace) if log["topics"][0] == OPEN_EVENT)
        rows.append({"name": name, "storage_overrides": {str(k): str(v) for k, v in slots.items()},
                     "error": trace.get("error"), "math_input": math["input"],
                     "math_output": math["output"], "mint_input": mint["input"], "event": event})
    saved["downstream_mint_probes"] = {"call": call, "cases": rows}
    ARTIFACT.write_text(json.dumps(saved, indent=2) + "\n")


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    keccak = Keccak()
    assert "0x" + keccak(SIGNATURE.encode()).hex()[:8] == SELECTOR
    assert "0x" + keccak(EXCESS_GETTER_SIGNATURE.encode()).hex()[:8] == "0xae745703"
    assert "0x" + keccak(ADJUSTMENT_SIGNATURE.encode()).hex()[:8] == "0xc218c676"
    assert "0x" + keccak(EVENT_SIGNATURE.encode()).hex() == EVENT_TOPIC
    assert all("0x" + keccak(signature.encode()).hex()[:8] == selector
               for signature, selector in ERRORS.items())
    saved = json.loads(ARTIFACT.read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert saved["scheduled_operation_executed_at_pin"] is False
    operation = next(row for row in json.loads((ATLAS / "timelock_operations.json").read_text())["operations"]
                     if row["operation_id"] == saved["scheduled_operation_id"])
    scheduled = operation["call_arguments_uint256_words"]
    assert set(saved["probes"]) == set(cases(scheduled))
    assert [int(saved["pinned_slots"][str(index)], 16) for index in range(5, 9)] == CURRENT
    successful = {"scheduled", "distinct", "noop_current", "equal_threshold_floor",
                  "tiny_rate", "tiny_scale", "max_rate"}
    invalid = set(saved["probes"]) - successful - {"outsider_distinct"}
    assert invalid == {"all_zero", "threshold_above_floor", "inverted_distinct",
                       "zero_threshold", "zero_floor", "zero_rate", "zero_scale"}
    for name, row in saved["probes"].items():
        assert row["calldata"] == calldata(SELECTOR, *(int(x) for x in row["arguments"]))
        assert row["implementation_calls"] == [{"type": "DELEGATECALL", "to": IMPLEMENTATION,
                                                "input": row["calldata"]}]
        if name in successful:
            assert row["error"] is None and row["output"] == "" and len(row["logs"]) == 1
            log = row["logs"][0]
            assert log["address"].lower() == TOKENOMICS and log["topics"] == [EVENT_TOPIC]
            assert [int(log["data"][i:i + 64], 16) for i in range(2, len(log["data"]), 64)] == [
                int(x) for x in row["arguments"]]
        else:
            assert row["error"] == "execution reverted" and not row["logs"]
            assert row["output"] == (ERRORS["NotOwner()"] if name == "outsider_distinct" else
                                     ERRORS["InvalidMintParams()"])
    distinct = saved["probes"]["distinct"]
    for index, value in enumerate(DISTINCT, 5):
        assert int(distinct["pre_storage"][word(index)], 16) == CURRENT[index - 5]
        assert int(distinct["post_storage"][word(index)], 16) == value
    scheduled_row = saved["probes"]["scheduled"]
    assert [int(x) for x in scheduled_row["arguments"]] == scheduled
    assert scheduled_row["pre_storage"] == {word(6): word(CURRENT[1])}
    assert scheduled_row["post_storage"] == {word(6): word(scheduled[1])}
    assert saved["probes"]["noop_current"]["post_storage"] == {}
    execution = saved["governance_execution"]
    timelock = json.loads((ATLAS / "timelock_behavior.json").read_text())
    prior_execution = next(row for row in timelock["scheduled_operations"]
                           if row["operation_id"] == saved["scheduled_operation_id"])
    assert execution["sender"] == timelock["owner"] == TIMELOCK_OWNER
    assert execution["calldata"] == execute_calldata(operation, bytes.fromhex(scheduled_row["calldata"][2:]))
    assert execution["error"] is None
    assert [{key: log[key] for key in ("address", "topics", "data")}
            for log in execution["timelock_logs"]] == prior_execution["execute_owner_at_pin"]["events"]
    assert execution["target_call"] == {"type": "CALL", "to": TOKENOMICS,
                                        "input": scheduled_row["calldata"], "error": None,
                                        "logs": []}
    assert execution["implementation_call"] == {"type": "DELEGATECALL", "to": IMPLEMENTATION,
                                                "input": scheduled_row["calldata"], "error": None,
                                                "logs": scheduled_row["logs"]}
    assert prior_execution["simulated_storage_post"][TOKENOMICS] == scheduled_row["post_storage"]
    assert prior_execution["simulated_storage_post"][OWNER] == {
        prior_execution["operation_mapping_slot"]: word(1)}
    downstream = saved["downstream_mint_probes"]
    assert downstream["call"] == {"from": EXCHANGE, "to": TOKENOMICS,
                                  "data": encode_call(OPEN_MINT, [
                                      int("0x4444444444444444444444444444444444444444", 16),
                                      0, 10**18, 10**18]), "gas": "0x989680"}
    expected_variants = {"baseline": {}, "scheduled_floor": {6: 10 * 10**24},
                         "distinct_parameters": dict(zip(range(5, 9), DISTINCT)),
                         "flat_threshold": {5: 6 * 10**24, 6: 10 * 10**24}}
    assert {row["name"] for row in downstream["cases"]} == set(expected_variants)
    minted = {}
    for row in downstream["cases"]:
        slots = expected_variants[row["name"]]
        assert row["storage_overrides"] == {str(k): str(v) for k, v in slots.items()}
        assert row["error"] is None
        math_args = input_words(row["math_input"])
        math_result = [int(row["math_output"][i:i + 64], 16)
                       for i in range(2, len(row["math_output"]), 64)]
        assert len(math_args) == 6 and len(math_result) == 2
        assert math_args[3:] == [slots.get(5, CURRENT[0]), slots.get(7, CURRENT[2]),
                                  slots.get(8, CURRENT[3])]
        assert math_result == math_quote(math_args)
        event = row["event"]
        assert event["address"].lower() == TOKENOMICS and event["topics"][0] == OPEN_EVENT
        event_words = [int(event["data"][i:i + 64], 16)
                       for i in range(2, len(event["data"]), 64)]
        assert len(event_words) == 6 and event_words[4] == math_result[1]
        assert event_words[5] == math_result[0]
        assert input_words(row["mint_input"]) == [
            int("0x4444444444444444444444444444444444444444", 16), math_result[0]]
        minted[row["name"]] = math_result[0]
    assert minted["baseline"] == minted["scheduled_floor"]
    assert minted["distinct_parameters"] != minted["baseline"]
    assert minted["flat_threshold"] == 100 * 10**18
    tracked = int(saved["pinned_slots"]["3"], 16)
    assert len(saved["excess_getter_floor_probes"]) == 4
    assert all(int(row["output"], 16) == max(tracked - int(row["floor"]), 0)
               for row in saved["excess_getter_floor_probes"])
    behavior = {"pin_block": PIN, "tokenomics_proxy": TOKENOMICS,
                "implementation": IMPLEMENTATION, "scheduled_operation_id": operation["operation_id"],
                "scheduled_operation_executed_at_pin": False,
                "selector_reconstructions": {SELECTOR: SIGNATURE,
                                             "0xae745703": EXCESS_GETTER_SIGNATURE,
                                             "0xc218c676": ADJUSTMENT_SIGNATURE},
                "source_name_lead": "https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/",
                "event_catalog": [{"topic0": EVENT_TOPIC, "reconstructed_signature": EVENT_SIGNATURE,
                                   "status": "simulated_log_only"}],
                "simulated_error_catalog": [
                    {"selector": ERRORS["InvalidMintParams()"],
                     "reconstructed_signature": "InvalidMintParams()", "probe_paths": sorted(invalid)},
                    {"selector": ERRORS["NotOwner()"],
                     "reconstructed_signature": "NotOwner()", "probe_paths": ["outsider_distinct"]}],
                "argument_storage_slots": [5, 6, 7, 8],
                "sampled_validation": "all four parameters nonzero and first parameter <= second parameter",
                "probe_count": len(saved["probes"]),
                "excess_getter_floor_probe_count": len(saved["excess_getter_floor_probes"]),
                "slot_6_semantics": "floor subtracted from tracked LP USD, clamped to zero, in selector 0xae745703",
                "governance_execution": {"status": "pinned_read_only_simulation", "success": True,
                                         "nested_call_count": 2, "nested_tokenomics_event_topic": EVENT_TOPIC,
                                         "tokenomics_slot_6_post": scheduled_row["post_storage"][word(6)],
                                         "timelock_operation_post": word(1)},
                "downstream_mint_probes": {"count": len(downstream["cases"]),
                                           "mint_amounts": {key: str(value) for key, value in minted.items()},
                                           "status": "pinned_read_only_storage_overrides"},
                "limits": ["All setter probes are pinned read-only simulations; the scheduled timelock operation was not executed on-chain.",
                           "The sampled validation model does not exclude additional guards for untested extreme values.",
                           "Downstream mint tests use hypothetical storage overrides, not an executed governance transaction."]}
    (ATLAS / "tokenomics_params_behavior.json").write_text(json.dumps(behavior, indent=2) + "\n")
    print("Tokenomics params:", len(saved["probes"]), "setter probes, 4 getter floor probes, 4 mint probes, governance call, event and two errors verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-governance", action="store_true")
    parser.add_argument("--capture-downstream", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
        capture_governance()
        capture_downstream()
    if args.capture_governance:
        capture_governance()
    if args.capture_downstream:
        capture_downstream()
    verify()
