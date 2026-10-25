#!/usr/bin/env python3
"""Capture and verify pinned read-only SessionKeyManager signer branches."""

import argparse
import json
import os
import re
import urllib.request
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_session_keys import descendants, nested_slot, rpc, word

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "session_signer_branches_behavior.json"
ARTIFACT = ROOT / "artifacts" / "session_signer_branches" / "pinned_probes.json"
PIN = 48902346
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
OUTSIDER = "0x000000000000000000000000000000000000dead"
SELECTOR = "0x7f608253"
PRECOMPILE = "0x" + "0" * 39 + "1"


def session_sample():
    behavior = json.loads((ATLAS / "session_signer_expanded_behavior.json").read_text())
    row = max(behavior["calls"], key=lambda item: item["registered_expiry_at_block"])
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    trace = next(item for item in graph["traces"] if item["hash"] == row["tx"])
    root = json.loads((ROOT / "artifacts" / trace["source_directory"] / f"{trace['source_stem']}.calls.json").read_text())
    calls = [call for call in descendants(root) if call.get("to", "").lower() == SESSION
             and call.get("input", "").startswith(SELECTOR)]
    return row, calls[row["call_index"]]["input"]


def direct_user_sample():
    behavior = json.loads((ATLAS / "session_key_behavior.json").read_text())
    row = behavior["registrations"][0]
    tx = row["tx"]
    path = ROOT / "artifacts" / "session_keys" / f"{tx}.calls.json"
    if not path.exists():
        path = ROOT / "artifacts" / "historical" / f"{tx}.calls.json"
    root = json.loads(path.read_text())
    calls = [call for call in descendants(root) if call.get("to", "").lower() == SESSION
             and call.get("input", "").startswith("0x5f76a1d6")]
    assert len(calls) == 1
    args = [int(calls[0]["input"][i:i + 64], 16) for i in range(10, len(calls[0]["input"]), 64)]
    assert len(args) == 9
    user, key, expiry, associated, nonce, deadline, v, r, s = args
    typehash = bytes.fromhex(behavior["register_typehash"][2:])
    struct_hash = Keccak()(typehash + b"".join(value.to_bytes(32, "big") for value in args[:6]))
    data = SELECTOR + "".join(word(value) for value in (user, int.from_bytes(struct_hash, "big"), v, r, s))
    return row, data


def cases():
    session_row, valid = session_sample()
    direct_row, direct = direct_user_sample()
    def mutate(data, index, value):
        begin = 10 + index * 64
        return data[:begin] + word(value) + data[begin + 64:]
    args = [int(valid[i:i + 64], 16) for i in range(10, len(valid), 64)]
    direct_args = [int(direct[i:i + 64], 16) for i in range(10, len(direct), 64)]
    return {"session_valid_exchange": (EXCHANGE, valid),
            "session_valid_outsider": (OUTSIDER, valid),
            "session_changed_user": (EXCHANGE, mutate(valid, 0, args[0] ^ 1)),
            "session_changed_hash": (EXCHANGE, mutate(valid, 1, args[1] ^ 1)),
            "session_invalid_v": (EXCHANGE, mutate(valid, 2, 0)),
            "session_zero_r": (EXCHANGE, mutate(valid, 3, 0)),
            "session_zero_s": (EXCHANGE, mutate(valid, 4, 0)),
            "direct_user_exchange": (EXCHANGE, direct),
            "direct_user_outsider": (OUTSIDER, direct),
            "direct_user_changed_user": (EXCHANGE, mutate(direct, 0, direct_args[0] ^ 1))}, session_row, direct_row


def raw_rpc(url, method, params):
    request = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1,
        "method": method, "params": params}).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def override_cases(session_row, timestamp, baseline_getter):
    user = int(session_row["user"], 16)
    signer = int(session_row["recovered_signer"], 16)
    state = bytes.fromhex(baseline_getter[2:])
    assert len(state) == 64
    expiry = int.from_bytes(state[:32], "big")
    associated = int.from_bytes(state[32:], "big")
    assert expiry > timestamp and associated == 0
    slot = nested_slot(user, signer, 4, Keccak())
    values = {"expiry_before": ((associated << 64) | (timestamp - 1)),
              "expiry_at": ((associated << 64) | timestamp),
              "expiry_after": ((associated << 64) | (timestamp + 1)),
              "revoked_word_zero": 0,
              "associated_nonzero": ((int(OUTSIDER, 16) << 64) | expiry)}
    return slot, values


def capture():
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    probes, session_row, direct_row = cases()
    saved = json.loads(ARTIFACT.read_text()) if ARTIFACT.exists() else {
        "pin": PIN, "block_hash": header["hash"], "session_sample_tx": session_row["tx"],
        "direct_sample_tx": direct_row["tx"], "rows": {}}
    assert saved["block_hash"].lower() == manifest["block_hash"]
    for name, (sender, data) in probes.items():
        if name in saved["rows"]:
            assert saved["rows"][name]["from"] == sender and saved["rows"][name]["data"] == data
            continue
        call = {"from": sender, "to": SESSION, "data": data, "gas": "0x1000000"}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN), {"tracer": "callTracer"}])
        saved["rows"][name] = {"from": sender, "data": data, "trace": trace}
        ARTIFACT.write_text(json.dumps(saved, indent=2) + "\n")
        print(name, "error", trace.get("error"), "output", trace.get("output", "")[:30], flush=True)
    getter_data = "0x96ade1f9" + word(int(session_row["user"], 16)) + word(int(session_row["recovered_signer"], 16))
    baseline_getter = rpc(url, "eth_call", [{"to": SESSION, "data": getter_data}, hex(PIN)])
    timestamp = int(header["timestamp"], 16)
    slot, values = override_cases(session_row, timestamp, baseline_getter)
    saved.setdefault("override_basis", {"block_timestamp": timestamp, "baseline_getter": baseline_getter,
                                         "mapping_slot": slot})
    assert saved["override_basis"] == {"block_timestamp": timestamp, "baseline_getter": baseline_getter,
                                         "mapping_slot": slot}
    override_rows = saved.setdefault("override_rows", {})
    for name, value in values.items():
        if name in override_rows:
            assert override_rows[name]["storage_word"] == "0x" + word(value)
            continue
        override = {SESSION: {"stateDiff": {slot: "0x" + word(value)}}}
        getter = raw_rpc(url, "eth_call", [{"to": SESSION, "data": getter_data}, hex(PIN), override])
        signer = raw_rpc(url, "eth_call", [{"from": EXCHANGE, "to": SESSION,
            "data": probes["session_valid_exchange"][1]}, hex(PIN), override])
        override_rows[name] = {"storage_word": "0x" + word(value), "getter": getter, "signer": signer}
        ARTIFACT.write_text(json.dumps(saved, indent=2) + "\n")
        print(name, "getter", getter.get("result", "")[:18], "signer", signer.get("result", "")[:18],
              "error", signer.get("error", {}).get("message", "")[:100], flush=True)


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(ARTIFACT.read_text())
    assert saved["pin"] == PIN and saved["block_hash"].lower() == manifest["block_hash"]
    probes, session_row, direct_row = cases()
    assert saved["session_sample_tx"] == session_row["tx"]
    assert saved["direct_sample_tx"] == direct_row["tx"]
    assert set(saved["rows"]) == set(probes)
    domain = bytes.fromhex(json.loads((ATLAS / "session_key_behavior.json").read_text())["domain_separator"][2:])
    keccak = Keccak()
    records = {}
    for name, (sender, data) in probes.items():
        row = saved["rows"][name]
        assert row["from"].lower() == sender and row["data"].lower() == data
        trace = row["trace"]
        assert trace["to"].lower() == SESSION and trace["input"].lower() == data
        words = [int(data[i:i + 64], 16) for i in range(10, len(data), 64)]
        assert len(words) == 5
        user, struct_hash, v, r, s = words
        digest = keccak(b"\x19\x01" + domain + struct_hash.to_bytes(32, "big"))
        precompile = [call for call in descendants(trace) if call.get("to", "").lower() == PRECOMPILE]
        if precompile:
            assert len(precompile) == 1
            assert precompile[0]["input"].lower() == "0x" + "".join(word(value) for value in
                (int.from_bytes(digest, "big"), v, r, s))
        records[name] = {"from": sender, "user": "0x" + word(user)[-40:],
                         "digest": "0x" + digest.hex(), "precompile_called": bool(precompile),
                         "recovered_signer": "0x" + word(int(precompile[0]["output"], 16))[-40:]
                         if precompile and precompile[0].get("output") else None,
                         "error": trace.get("error"), "output": trace.get("output", "0x"),
                         "child_call_count": len(trace.get("calls", []))}
    success = ("session_valid_exchange", "session_valid_outsider")
    rejected = tuple(name for name in records if name not in success)
    assert len(success) == 2 and len(rejected) == 8
    assert all(records[name]["error"] is None and
               records[name]["recovered_signer"] == session_row["recovered_signer"] and
               int(records[name]["output"], 16) == int(session_row["recovered_signer"], 16)
               for name in success)
    error_signature = "SessionKeyNotAuthorized()"
    error_selector = "0x" + keccak(error_signature.encode())[:4].hex()
    assert error_selector == "0xc5045f22"
    assert all(records[name]["error"] == "execution reverted" and
               records[name]["output"] == error_selector for name in rejected)
    assert all(records[name]["child_call_count"] == 1 for name in records)
    assert records["session_invalid_v"]["precompile_called"] is False
    assert all(records[name]["precompile_called"] and records[name]["recovered_signer"] is None
               for name in ("session_zero_r", "session_zero_s"))
    assert all(records[name]["recovered_signer"] == records[name]["user"]
               for name in ("direct_user_exchange", "direct_user_outsider"))
    assert records["session_valid_exchange"]["output"] == records["session_valid_outsider"]["output"]
    basis = saved["override_basis"]
    slot, values = override_cases(session_row, basis["block_timestamp"], basis["baseline_getter"])
    assert basis["mapping_slot"] == slot and set(saved["override_rows"]) == set(values)
    expiry_signature = "SessionKeyExpired()"
    expiry_selector = "0x" + keccak(expiry_signature.encode())[:4].hex()
    assert expiry_selector == "0xda0700a2"
    override_records = {}
    for name, value in values.items():
        row = saved["override_rows"][name]
        assert row["storage_word"] == "0x" + word(value)
        getter_reply = row["getter"]
        assert "result" in getter_reply and len(bytes.fromhex(getter_reply["result"][2:])) == 64
        state = bytes.fromhex(getter_reply["result"][2:])
        observed_expiry = int.from_bytes(state[:32], "big")
        observed_associated = int.from_bytes(state[32:], "big")
        assert value == (observed_associated << 64) | observed_expiry
        signer_reply = row["signer"]
        if "result" in signer_reply:
            assert int(signer_reply["result"], 16) == int(session_row["recovered_signer"], 16)
            result_kind = "returned_signer"
        else:
            message = signer_reply["error"]["message"]
            match = re.search(r"output: Some\((0x[0-9a-fA-F]{8})\)", message)
            assert match, message
            result_kind = match.group(1).lower()
        override_records[name] = {"stored_expiry": observed_expiry,
                                  "stored_associated_address": "0x" + word(observed_associated)[-40:],
                                  "result": result_kind}
    assert override_records["expiry_before"]["result"] == expiry_selector
    assert override_records["expiry_at"]["result"] == "returned_signer"
    assert override_records["expiry_after"]["result"] == "returned_signer"
    assert override_records["revoked_word_zero"]["result"] == error_selector
    assert override_records["associated_nonzero"]["result"] == "returned_signer"
    result = {"pin": PIN, "block_hash": manifest["block_hash"], "address": SESSION,
              "selector": SELECTOR, "session_sample_tx": session_row["tx"],
              "direct_user_sample_tx": direct_row["tx"], "probe_count": len(records),
              "successful_probe_count": len(success), "rejected_probe_count": len(rejected),
              "simulated_error_catalog": [{"selector": error_selector,
                  "reconstructed_signature": error_signature, "probe_paths": list(rejected),
                  "public_signature_candidates": [error_signature]},
                  {"selector": expiry_selector, "reconstructed_signature": expiry_signature,
                   "probe_paths": ["expiry_before"],
                   "public_signature_candidates": [expiry_signature]}],
              "probes": records, "storage_override_probes": override_records,
              "limits": ["Read-only calls at the pin cover ten signer inputs and five storage overrides; other validation branches remain untested.",
                         "The direct-user signature is taken from a historical registration; it is not a trade authorization."]}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    print(json.dumps(build()["probes"], indent=2))
