#!/usr/bin/env python3
"""Verify every saved SessionKeyManager session-signer call in the call graph."""

import argparse
import collections
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_session_keys import descendants, rpc, word

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "session_signer_expanded"
OUT = ATLAS / "session_signer_expanded_behavior.json"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
ECRECOVER = "0x" + "0" * 39 + "1"
SELECTOR = "0x7f608253"
GETTER = "0x96ade1f9"
PIN = 48902346


def saved_calls():
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    traces = {}
    for trace in graph["traces"]:
        tx = trace["hash"]
        path = ROOT / "artifacts" / trace["source_directory"] / f"{trace['source_stem']}.calls.json"
        root = json.loads(path.read_text())
        calls = [call for call in descendants(root) if call.get("to", "").lower() == SESSION
                 and call.get("input", "").lower().startswith(SELECTOR)]
        if calls:
            assert tx not in traces
            traces[tx] = (trace, calls)
    graph_count = sum(edge.get("selectors", {}).get(SELECTOR, 0) for edge in graph["edges"]
                      if edge["to_role"] == "session_key_manager_proxy")
    assert sum(len(calls) for _, calls in traces.values()) == graph_count == 57
    return traces


def previous_getters():
    path = ROOT / "artifacts" / "session_keys" / "historical_signer_getters.json"
    saved = json.loads(path.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin"] == PIN and saved["pin_hash"].lower() == manifest["block_hash"]
    return {(row["tx"], row["call_index"]): row for row in saved["rows"]}


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    pin = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert pin["hash"].lower() == manifest["block_hash"]
    path = ARTIFACTS / "getters.json"
    saved = json.loads(path.read_text()) if path.exists() else {"pin": PIN, "pin_hash": pin["hash"], "rows": []}
    assert saved["pin"] == PIN and saved["pin_hash"].lower() == manifest["block_hash"]
    old = previous_getters()
    already = {(row["tx"], row["call_index"]) for row in saved["rows"]}
    headers = {}
    for tx, (trace, calls) in sorted(saved_calls().items()):
        block = trace["block"]
        for index, call in enumerate(calls):
            key = (tx, index)
            if key in old or key in already:
                continue
            if block not in headers:
                headers[block] = rpc(url, "eth_getBlockByNumber", [hex(block), False])
                assert int(headers[block]["number"], 16) == block
            user = int(call["input"][10:74], 16)
            signer = int(call["output"], 16)
            data = GETTER + word(user) + word(signer)
            state = rpc(url, "eth_call", [{"to": SESSION, "data": data}, hex(block)])
            assert len(bytes.fromhex(state[2:])) == 64
            saved["rows"].append({"tx": tx, "call_index": index, "block": block,
                                  "block_hash": headers[block]["hash"],
                                  "block_timestamp": int(headers[block]["timestamp"], 16),
                                  "user": "0x" + word(user)[-40:],
                                  "recovered_signer": "0x" + word(signer)[-40:],
                                  "session_key_getter_at_block": state})
            already.add(key)
            path.write_text(json.dumps(saved, indent=2) + "\n")
            print("captured", len(saved["rows"]), "of 39 new calls", flush=True)


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    session = json.loads((ATLAS / "session_key_behavior.json").read_text())
    assert session["block_hash"] == manifest["block_hash"]
    domain = bytes.fromhex(session["domain_separator"][2:])
    keccak = Keccak()
    old = previous_getters()
    fresh = json.loads((ARTIFACTS / "getters.json").read_text())
    assert fresh["pin"] == PIN and fresh["pin_hash"].lower() == manifest["block_hash"]
    by_key = {**old, **{(row["tx"], row["call_index"]): row for row in fresh["rows"]}}
    assert len(by_key) == len(old) + len(fresh["rows"]) == 57
    records = []
    txs = set()
    pairs = set()
    by_directory = collections.Counter()
    for tx, (trace, calls) in sorted(saved_calls().items()):
        assert trace["status"] == 1
        txs.add(tx)
        by_directory[trace["source_directory"]] += len(calls)
        for index, call in enumerate(calls):
            assert call["type"] == "STATICCALL" and call["from"].lower() == EXCHANGE
            assert not call.get("error") and len(call["input"]) == 10 + 5 * 64
            user, struct_hash, v, r, s = (int(call["input"][i:i + 64], 16)
                                          for i in range(10, len(call["input"]), 64))
            assert v in (27, 28) and user < 1 << 160
            digest = keccak(b"\x19\x01" + domain + struct_hash.to_bytes(32, "big"))
            ecrecover = [child for child in descendants(call)
                         if child.get("to", "").lower() == ECRECOVER]
            assert len(ecrecover) == 1
            child = ecrecover[0]
            assert child["type"] == "STATICCALL" and not child.get("error")
            assert child["input"].lower() == "0x" + "".join(word(value) for value in
                (int.from_bytes(digest, "big"), v, r, s))
            recovered = int(child["output"], 16)
            assert recovered != user and recovered == int(call["output"], 16)
            getter = by_key[(tx, index)]
            assert getter["block"] == trace["block"]
            assert int(getter["user"], 16) == user
            assert int(getter["recovered_signer"], 16) == recovered
            state = bytes.fromhex(getter["session_key_getter_at_block"][2:])
            assert len(state) == 64
            expiry = int.from_bytes(state[:32], "big")
            associated = int.from_bytes(state[32:], "big")
            assert expiry > getter["block_timestamp"]
            pairs.add((user, recovered))
            records.append({"tx": tx, "call_index": index, "block": trace["block"],
                            "source_directory": trace["source_directory"],
                            "user": "0x" + word(user)[-40:],
                            "recovered_signer": "0x" + word(recovered)[-40:],
                            "struct_hash": "0x" + word(struct_hash),
                            "digest": "0x" + digest.hex(),
                            "registered_expiry_at_block": expiry,
                            "registered_associated_address_at_block": "0x" + word(associated)[-40:],
                            "block_timestamp": getter["block_timestamp"],
                            "previously_verified": (tx, index) in old})
    assert len(records) == 57 and len(txs) == 24 and len(pairs) == 45
    result = {"pin": PIN, "block_hash": manifest["block_hash"], "address": SESSION,
              "selector": SELECTOR, "call_count": len(records), "transaction_count": len(txs),
              "distinct_user_signer_pairs": len(pairs), "previously_verified_call_count": len(old),
              "newly_verified_call_count": len(fresh["rows"]),
              "call_count_by_artifact_directory": dict(sorted(by_directory.items())),
              "checks": ["EIP-712 digest equals 0x1901, the pinned domain separator, and the supplied struct hash.",
                         "ECRECOVER received the exact digest and signature fields, and its result equals the SessionKeyManager return.",
                         "The returned signer differs from the user and the archived session-key getter has an unexpired entry at the sampled block."],
              "calls": records,
              "limits": ["The archived getter reads end-of-block state; same-transaction intermediate registry state is not independently reconstructed.",
                         "These 57 successful calls do not establish rejection branches or the exact Solidity function name."]}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    print("session signer:", result["call_count"], "calls,", result["transaction_count"], "transactions")
