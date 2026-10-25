#!/usr/bin/env python3
"""Capture and verify pinned Papertrade SessionKeyManager behavior."""

import argparse
import json
import os
import pathlib
import urllib.request

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "session_keys"
HISTORICAL = ROOT / "artifacts" / "historical"
PIN = 48902346
PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
IMPLEMENTATION = "0x8a5069fe303e8f81e91825436e956d595032e558"
REGISTER_TOPIC = "0x3cec0566535d67d6c92668517af0bf8a66cdc91d622dbb830fcc08e1bcf5d1df"


def word(value):
    return f"{value:064x}" if isinstance(value, int) else value.removeprefix("0x").rjust(64, "0")


def descendants(call):
    for child in call.get("calls", []):
        yield child
        yield from descendants(child)


def calldata_words(data):
    assert (len(data) - 10) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(10, len(data), 64)]


def mapping_slot(key, base, keccak):
    return "0x" + keccak(key.to_bytes(32, "big") + base.to_bytes(32, "big")).hex()


def nested_slot(outer, inner, base, keccak):
    first = keccak(outer.to_bytes(32, "big") + base.to_bytes(32, "big"))
    return "0x" + keccak(inner.to_bytes(32, "big") + first).hex()


def rpc(url, method, params):
    request = urllib.request.Request(
        url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        reply = json.load(response)
    if "error" in reply:
        raise RuntimeError(f"{method}: {reply['error']}")
    return reply["result"]


def registration_transactions():
    logs = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    rows = [log for log in logs if log["address"].lower() == PROXY
            and log["topics"][0].lower() == REGISTER_TOPIC]
    assert len(rows) == 10 and len({row["transactionHash"] for row in rows}) == 10
    return rows


def artifact(tx, suffix):
    old = HISTORICAL / f"{tx}.{suffix}.json"
    return old if old.exists() else ARTIFACTS / f"{tx}.{suffix}.json"


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    for log in registration_transactions():
        tx = log["transactionHash"]
        for suffix, method, params in (
            ("calls", "debug_traceTransaction", [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
            ("receipt", "eth_getTransactionReceipt", [tx]),
            ("state_diff", "debug_traceTransaction", [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}]),
        ):
            path = artifact(tx, suffix)
            if not path.exists():
                path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")
        print(int(log["blockNumber"], 16), tx, flush=True)
    capture_nonce_diffs(url)
    capture_probes(url, manifest["block_hash"])
    capture_auth_probes(url, manifest["block_hash"])
    capture_signer_getters(url, manifest["block_hash"])


def capture_nonce_diffs(url):
    for trace_path in sorted(HISTORICAL.glob("*.calls.json")):
        root = json.loads(trace_path.read_text())
        if not any(call.get("to", "").lower() == PROXY and call.get("input", "").startswith("0xb002b9fa")
                   for call in descendants(root)):
            continue
        tx = trace_path.name.split(".")[0]
        path = artifact(tx, "state_diff")
        if not path.exists():
            result = rpc(url, "debug_traceTransaction", [tx, {"tracer": "prestateTracer",
                                                          "tracerConfig": {"diffMode": True}}])
            path.write_text(json.dumps(result, indent=2) + "\n")
            print("nonce state diff", tx, flush=True)


def capture_probes(url, block_hash):
    keccak = Keccak()
    path = ARTIFACTS / "pinned_session_getters.json"
    if not path.exists():
        rows = []
        for log in registration_transactions():
            tx = log["transactionHash"]
            root = json.loads(artifact(tx, "calls").read_text())
            registration = [c for c in descendants(root) if c.get("to", "").lower() == PROXY
                            and c.get("input", "").startswith("0x5f76a1d6")]
            assert len(registration) == 1
            user, key, expiry, parent = calldata_words(registration[0]["input"])[:4]
            args = word(user) + word(key)
            slot = nested_slot(user, key, 4, keccak)
            pair = rpc(url, "eth_call", [{"to": PROXY, "data": "0x96ade1f9" + args}, hex(PIN)])
            parent_out = rpc(url, "eth_call", [{"to": PROXY, "data": "0xc1e6613d" + args}, hex(PIN)])
            raw = rpc(url, "eth_getStorageAt", [PROXY, slot, hex(PIN)])
            rows.append({"tx": tx, "user": "0x" + word(user)[-40:], "session_key": "0x" + word(key)[-40:],
                         "registered_expiry": expiry, "registered_associated_address": "0x" + word(parent)[-40:],
                         "mapping_slot": slot, "getter_session_keys": pair,
                         "getter_associated_address": parent_out, "raw_storage": raw})
        path.write_text(json.dumps({"pin": PIN, "block_hash": block_hash, "rows": rows}, indent=2) + "\n")

    path = ARTIFACTS / "pinned_nonce_getters.json"
    if not path.exists():
        rows = []
        for trace_path in sorted(HISTORICAL.glob("*.calls.json")):
            root = json.loads(trace_path.read_text())
            for call in descendants(root):
                if call.get("to", "").lower() != PROXY or not call.get("input", "").startswith("0xb002b9fa"):
                    continue
                user, nonce, expiry = calldata_words(call["input"])
                slot = nested_slot(user, nonce >> 8, 6, keccak)
                used = rpc(url, "eth_call", [{"to": PROXY,
                                              "data": "0xcab7e8eb" + word(user) + word(nonce)}, hex(PIN)])
                raw = rpc(url, "eth_getStorageAt", [PROXY, slot, hex(PIN)])
                current = rpc(url, "eth_call", [{"to": PROXY,
                                                 "data": "0x7ecebe00" + word(user)}, hex(PIN)])
                rows.append({"tx": trace_path.name.split(".")[0], "user": "0x" + word(user)[-40:],
                             "nonce": nonce, "expiry": expiry, "bitmap_slot": slot,
                             "bitmap_word": raw, "is_nonce_used": used, "nonces_getter": current})
        path.write_text(json.dumps({"pin": PIN, "block_hash": block_hash, "rows": rows}, indent=2) + "\n")
    saved = json.loads(path.read_text())
    if any("nonce_bitmap_getter" not in row for row in saved["rows"]):
        for row in saved["rows"]:
            if "nonce_bitmap_getter" not in row:
                row["nonce_bitmap_getter"] = rpc(url, "eth_call", [
                    {"to": PROXY, "data": "0xf2f59776" + word(row["user"]) + word(row["nonce"] >> 8)},
                    hex(PIN)])
        path.write_text(json.dumps(saved, indent=2) + "\n")


def capture_auth_probes(url, block_hash):
    path = ARTIFACTS / "pinned_auth_probes.json"
    outsider = "0x" + "33" * 20
    owner = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
    executor = "0x233ff29b239abc1d7748605da9b205c3e008626e"
    exchange = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
    sample = next(x for x in registration_transactions() if x["transactionHash"].startswith("0x04b0"))
    root = json.loads(artifact(sample["transactionHash"], "calls").read_text())
    registration = next(c for c in descendants(root) if c.get("to", "").lower() == PROXY
                        and c.get("input", "").startswith("0x5f76a1d6"))
    user, key = calldata_words(registration["input"])[:2]
    nonce_root = json.loads((HISTORICAL / "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5.calls.json").read_text())
    consumed = next(c for c in descendants(nonce_root) if c.get("to", "").lower() == PROXY
                    and c.get("input", "").startswith("0xb002b9fa"))
    nonce_user, nonce, expiry = calldata_words(consumed["input"])
    cases = {
        "register_outsider": (outsider, registration["input"]),
        "register_authorized_replay": (executor, registration["input"]),
        "set_submitter_outsider": (outsider, "0x5197a0d3" + word(executor) + word(0)),
        "set_submitter_owner": (owner, "0x5197a0d3" + word(executor) + word(0)),
        "set_caller_outsider": (outsider, "0xcf8fbec9" + word(exchange)),
        "set_caller_owner": (owner, "0xcf8fbec9" + word(exchange)),
        "revoke_outsider": (outsider, "0x84f4fc6a" + word(key)),
        "revoke_user": ("0x" + word(user)[-40:], "0x84f4fc6a" + word(key)),
        "consume_outsider": (outsider, consumed["input"]),
        "consume_replay": (exchange, consumed["input"]),
        "consume_unused": (exchange, "0xb002b9fa" + word(nonce_user) + word(nonce ^ 128) + word(expiry)),
        "consume_expired": (exchange, "0xb002b9fa" + word(nonce_user) + word(nonce ^ 128) + word(0)),
    }
    rows = json.loads(path.read_text())["rows"] if path.exists() else {}
    for name, (sender, data) in cases.items():
        if name in rows:
            continue
        call = {"from": sender, "to": PROXY, "data": data, "gas": "0x1000000"}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                                              {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        rows[name] = {"sender": sender, "data": data, "trace": trace}
        print(name, trace.get("output", "success")[:10], flush=True)
    path.write_text(json.dumps({"pin": PIN, "block_hash": block_hash, "rows": rows}, indent=2) + "\n")


def capture_signer_getters(url, block_hash):
    path = ARTIFACTS / "historical_signer_getters.json"
    if path.exists():
        return
    rows = []
    headers = {}
    for call_path in sorted(HISTORICAL.glob("*.calls.json")):
        root = json.loads(call_path.read_text())
        tx = call_path.name.split(".")[0]
        signer_calls = [call for call in descendants(root) if call.get("to", "").lower() == PROXY
                        and call.get("input", "").startswith("0x7f608253")]
        if not signer_calls:
            continue
        receipt = json.loads(artifact(tx, "receipt").read_text())
        block = int(receipt["blockNumber"], 16)
        if block not in headers:
            headers[block] = rpc(url, "eth_getBlockByNumber", [hex(block), False])
        for index, call in enumerate(signer_calls):
            user = calldata_words(call["input"])[0]
            signer = int(call["output"], 16)
            state = rpc(url, "eth_call", [{"to": PROXY,
                                           "data": "0x96ade1f9" + word(user) + word(signer)}, hex(block)])
            rows.append({"tx": tx, "call_index": index, "block": block,
                         "block_hash": headers[block]["hash"],
                         "block_timestamp": int(headers[block]["timestamp"], 16),
                         "user": "0x" + word(user)[-40:], "recovered_signer": "0x" + word(signer)[-40:],
                         "session_key_getter_at_block": state})
    path.write_text(json.dumps({"pin": PIN, "pin_hash": block_hash, "rows": rows}, indent=2) + "\n")


def walk_with_ancestors(call, ancestors=()):
    yield call, ancestors
    for child in call.get("calls", []):
        yield from walk_with_ancestors(child, ancestors + (call,))


def analyze():
    keccak = Keccak()
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN
    views = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]["views"]
    constants = {row["selector"]: bytes.fromhex(row["return_prefix"][2:]) for row in views}
    register_typehash = constants["0x2bc9ed54"]
    domain = constants["0x3644e515"]
    assert domain == constants["0x78e890ba"]
    event_signatures = {
        "SessionKeyRegistered(address,address,uint64)": REGISTER_TOPIC,
        "SessionKeyRevoked(address,address)": "0x744157ccffbd293a2e8644928cd7d23d650f869b88f72d7bfea8041b76ca6bec",
        "AuthorizedSubmitterUpdated(address,bool)": "0xf09fcf47c21ca51acd6fd24e30b537dc39f0e5e021541cf1e4fa7f1013d60b99",
        "OwnerUpdated(address)": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
        "AuthorizedCallerUpdated(address)": "0xfe60173cc964bc674632fcf67031bba24c8a99a4a7d6518c726586978b7e30d3",
    }
    for signature, topic in event_signatures.items():
        assert "0x" + keccak(signature.encode()).hex() == topic
    getter_rows = json.loads((ARTIFACTS / "pinned_session_getters.json").read_text())
    assert getter_rows["block_hash"] == manifest["block_hash"] and len(getter_rows["rows"]) == 10
    by_tx = {row["tx"]: row for row in getter_rows["rows"]}
    records = []
    for log in registration_transactions():
        tx = log["transactionHash"]
        root = json.loads(artifact(tx, "calls").read_text())
        receipt = json.loads(artifact(tx, "receipt").read_text())
        diff = json.loads(artifact(tx, "state_diff").read_text())
        registrations = [call for call in descendants(root) if call.get("to", "").lower() == PROXY
                         and call.get("input", "").startswith("0x5f76a1d6")]
        assert len(registrations) == 1 and receipt["status"] == "0x1"
        registration = registrations[0]
        assert registration["from"].lower() == "0x233ff29b239abc1d7748605da9b205c3e008626e"
        words = calldata_words(registration["input"])
        assert len(words) == 9
        user, key, expiry, parent, nonce, deadline, v, r, s = words
        assert expiry < 1 << 64 and deadline < 1 << 64 and v in (27, 28)
        block_time = int(log["blockTimestamp"], 16)
        assert expiry > block_time and deadline > block_time
        struct_hash = keccak(register_typehash + b"".join(x.to_bytes(32, "big") for x in words[:6]))
        digest = keccak(b"\x19\x01" + domain + struct_hash)
        ecrecover = [call for call in descendants(registration)
                     if call.get("to", "").lower() == "0x" + "0" * 39 + "1"]
        assert len(ecrecover) == 1
        assert bytes.fromhex(ecrecover[0]["input"][2:]) == b"".join(
            x.to_bytes(32, "big") for x in (int.from_bytes(digest, "big"), v, r, s))
        assert int(ecrecover[0]["output"], 16) == user
        event = [row for row in receipt["logs"] if row["address"].lower() == PROXY
                 and row["topics"][0].lower() == REGISTER_TOPIC]
        assert len(event) == 1
        assert event[0]["topics"] == [REGISTER_TOPIC, "0x" + word(user), "0x" + word(key)]
        assert int(event[0]["data"], 16) == expiry
        assert int(log["blockNumber"], 16) == int(receipt["blockNumber"], 16)
        session_slot = nested_slot(user, key, 4, keccak)
        nonce_slot = nested_slot(user, nonce >> 8, 6, keccak)
        counter_slot = mapping_slot(user, 5, keccak)
        pre = diff["pre"].get(PROXY, {}).get("storage", {})
        post = diff["post"][PROXY]["storage"]
        packed = expiry | (parent << 64)
        assert int(post[session_slot], 16) == packed
        bit = 1 << (nonce & 255)
        assert not int(pre.get(nonce_slot, "0x0"), 16) & bit
        assert int(post[nonce_slot], 16) & bit
        if counter_slot in post:
            assert int(post[counter_slot], 16) == nonce + 1
            assert int(pre.get(counter_slot, "0x0"), 16) <= nonce
        pinned = by_tx[tx]
        assert pinned["mapping_slot"] == session_slot and int(pinned["raw_storage"], 16) == packed
        getter = bytes.fromhex(pinned["getter_session_keys"][2:])
        assert len(getter) == 64 and int.from_bytes(getter[:32], "big") == expiry
        assert int.from_bytes(getter[32:], "big") == parent
        assert int(pinned["getter_associated_address"], 16) == parent
        records.append({"tx": tx, "block": int(log["blockNumber"], 16), "user": pinned["user"],
                        "session_key": pinned["session_key"], "expiry": expiry,
                        "associated_address": pinned["registered_associated_address"], "nonce": nonce, "deadline": deadline,
                        "digest": "0x" + digest.hex(), "recovered_signer": "0x" + word(user)[-40:],
                        "session_slot": session_slot, "session_word": "0x" + word(packed),
                        "nonce_bitmap_slot": nonce_slot, "nonce_bit": nonce & 255,
                        "nonce_counter_slot": counter_slot,
                        "nonce_counter_pre": pre.get(counter_slot), "nonce_counter_post": post.get(counter_slot)})
    assert len(records) == 10 and len({x["tx"] for x in records}) == 10

    pinned_nonces = json.loads((ARTIFACTS / "pinned_nonce_getters.json").read_text())
    assert pinned_nonces["block_hash"] == manifest["block_hash"]
    by_nonce = {(row["tx"], row["user"].lower(), row["nonce"]): row for row in pinned_nonces["rows"]}
    nonce_records = []
    for path in sorted(HISTORICAL.glob("*.calls.json")):
        root = json.loads(path.read_text())
        tx = path.name.split(".")[0]
        for call, ancestors in walk_with_ancestors(root):
            if call.get("to", "").lower() != PROXY or not call.get("input", "").startswith("0xb002b9fa"):
                continue
            user, nonce, expiry = calldata_words(call["input"])
            assert call["from"].lower() == "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
            committed = not any(node.get("error") for node in (call,) + ancestors)
            user_address = "0x" + word(user)[-40:]
            pinned = by_nonce[(tx, user_address, nonce)]
            bitmap_slot = nested_slot(user, nonce >> 8, 6, keccak)
            assert pinned["bitmap_slot"] == bitmap_slot
            assert int(pinned["nonce_bitmap_getter"], 16) == int(pinned["bitmap_word"], 16)
            bit_set = bool(int(pinned["bitmap_word"], 16) & (1 << (nonce & 255)))
            assert bit_set == bool(int(pinned["is_nonce_used"], 16)) == committed
            diff = json.loads(artifact(tx, "state_diff").read_text())
            before = diff["pre"].get(PROXY, {}).get("storage", {})
            after = diff["post"].get(PROXY, {}).get("storage", {})
            bit = 1 << (nonce & 255)
            assert not int(before.get(bitmap_slot, "0x0"), 16) & bit
            assert bool(int(after.get(bitmap_slot, "0x0"), 16) & bit) == committed
            nonce_records.append({"tx": tx, "user": user_address, "nonce": nonce, "deadline": expiry,
                                  "committed": committed, "bitmap_slot": bitmap_slot,
                                  "bit_index": nonce & 255, "used_at_pin": bit_set,
                                  "nonce_counter_at_pin": int(pinned["nonces_getter"], 16)})
    assert len(nonce_records) == len(pinned_nonces["rows"]) == 19
    assert sum(x["committed"] for x in nonce_records) == 16

    signer_getters = json.loads((ARTIFACTS / "historical_signer_getters.json").read_text())
    assert signer_getters["pin_hash"] == manifest["block_hash"]
    by_signer = {(row["tx"], row["call_index"]): row for row in signer_getters["rows"]}
    signer_records = []
    for path in sorted(HISTORICAL.glob("*.calls.json")):
        tx = path.name.split(".")[0]
        root = json.loads(path.read_text())
        calls = [call for call in descendants(root) if call.get("to", "").lower() == PROXY
                 and call.get("input", "").startswith("0x7f608253")]
        for index, call in enumerate(calls):
            user, struct_hash, v, r, s = calldata_words(call["input"])
            assert call["from"].lower() == "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
            assert v in (27, 28)
            digest = keccak(b"\x19\x01" + domain + struct_hash.to_bytes(32, "big"))
            ecrecover = [child for child in descendants(call)
                         if child.get("to", "").lower() == "0x" + "0" * 39 + "1"]
            assert len(ecrecover) == 1
            assert bytes.fromhex(ecrecover[0]["input"][2:]) == b"".join(
                value.to_bytes(32, "big") for value in (int.from_bytes(digest, "big"), v, r, s))
            recovered = int(ecrecover[0]["output"], 16)
            assert recovered == int(call["output"], 16) and recovered != user
            getter = by_signer[(tx, index)]
            assert int(getter["user"], 16) == user and int(getter["recovered_signer"], 16) == recovered
            state = bytes.fromhex(getter["session_key_getter_at_block"][2:])
            assert len(state) == 64
            expiry, associated = int.from_bytes(state[:32], "big"), int.from_bytes(state[32:], "big")
            assert expiry > getter["block_timestamp"]
            signer_records.append({"tx": tx, "call_index": index, "user": getter["user"],
                                   "recovered_signer": getter["recovered_signer"],
                                   "struct_hash": "0x" + word(struct_hash), "digest": "0x" + digest.hex(),
                                   "registered_expiry_at_block": expiry,
                                   "registered_associated_address_at_block": "0x" + word(associated)[-40:],
                                   "block": getter["block"], "block_timestamp": getter["block_timestamp"]})
    assert len(signer_records) == len(signer_getters["rows"]) == 18

    owner_tx = "0x8e2f5ebbecd7f6fc9fc32315fb9dea2f1f578c7ab921e99f519a9f4cc3561c6b"
    submitter_tx = "0x9adf6092169b38b21ff764acd71e57b575d5182bca390ea7002c24c1d622648b"
    revoke_tx = "0x9f01a632f7262f067542a1df78892453e17c1304c431d0cc5b4d80c26adf99cc"
    owner_call = json.loads(artifact(owner_tx, "calls").read_text())
    owner_receipt = json.loads(artifact(owner_tx, "receipt").read_text())
    owner_diff = json.loads(artifact(owner_tx, "state_diff").read_text())
    assert owner_call["input"].startswith("0xf2fde38b") and not owner_call.get("error")
    new_owner = int(owner_call["input"][10:], 16)
    assert int(owner_diff["pre"][PROXY]["storage"]["0x" + word(2)], 16) == int(owner_call["from"], 16)
    assert int(owner_diff["post"][PROXY]["storage"]["0x" + word(2)], 16) == new_owner
    assert any(log["topics"] == [event_signatures["OwnerUpdated(address)"], "0x" + word(new_owner)]
               for log in owner_receipt["logs"] if log["address"].lower() == PROXY)
    submitter_call = json.loads(artifact(submitter_tx, "calls").read_text())
    submitter_receipt = json.loads(artifact(submitter_tx, "receipt").read_text())
    submitter_diff = json.loads(artifact(submitter_tx, "state_diff").read_text())
    submitter, enabled = calldata_words(submitter_call["input"])
    assert enabled == 1 and int(submitter_diff["post"][PROXY]["storage"][mapping_slot(submitter, 7, keccak)], 16) == 1
    assert any(log["topics"] == [event_signatures["AuthorizedSubmitterUpdated(address,bool)"], "0x" + word(submitter)]
               and int(log["data"], 16) == 1 for log in submitter_receipt["logs"]
               if log["address"].lower() == PROXY)
    revoke_call = json.loads(artifact(revoke_tx, "calls").read_text())
    revoke_receipt = json.loads(artifact(revoke_tx, "receipt").read_text())
    revoke_diff = json.loads(artifact(revoke_tx, "state_diff").read_text())
    revoked_key = int(revoke_call["input"][10:], 16)
    revoked_user = int(revoke_call["from"], 16)
    revoked_slot = nested_slot(revoked_user, revoked_key, 4, keccak)
    assert int(revoke_diff["pre"][PROXY]["storage"][revoked_slot], 16) > 0
    assert revoked_slot not in revoke_diff["post"][PROXY].get("storage", {})
    assert any(log["topics"] == [event_signatures["SessionKeyRevoked(address,address)"],
                                 "0x" + word(revoked_user), "0x" + word(revoked_key)]
               for log in revoke_receipt["logs"] if log["address"].lower() == PROXY)

    auth = json.loads((ARTIFACTS / "pinned_auth_probes.json").read_text())
    assert auth["block_hash"] == manifest["block_hash"]
    error_probes = {
        "UnauthorizedSubmitter()": ("0x93b78c88", ["register_outsider"]),
        "InvalidNonce()": ("0x756688fe", ["register_authorized_replay", "consume_replay"]),
        "NotOwner()": ("0x30cd7471", ["set_submitter_outsider", "set_caller_outsider"]),
        "UnauthorizedCaller()": ("0x5c427cd9", ["consume_outsider"]),
        "ExpiredDeadline()": ("0xf87d9271", ["consume_expired"]),
    }
    for signature, (selector, names) in error_probes.items():
        assert "0x" + keccak(signature.encode())[:4].hex() == selector
        for name in names:
            trace = auth["rows"][name]["trace"]
            assert trace.get("error") and trace.get("output") == selector
    for name in ("set_submitter_owner", "set_caller_owner", "revoke_outsider", "revoke_user", "consume_unused"):
        assert not auth["rows"][name]["trace"].get("error")
    assert any(log["topics"][0] == event_signatures["AuthorizedCallerUpdated(address)"]
               for call in descendants(auth["rows"]["set_caller_owner"]["trace"])
               for log in call.get("logs", []))

    selector_reconstructions = {
        "0x2bc9ed54": "REGISTER_SESSION_KEY_TYPEHASH()",
        "0x5f76a1d6": "registerSessionKeyBySig(address,address,uint64,address,uint256,uint64,uint8,bytes32,bytes32)",
        "0xb002b9fa": "consumeNonce(address,uint256,uint64)",
        "0xf2f59776": "nonceBitmapWord(address,uint256)",
        "0x7ecebe00": "nonces(address)",
        "0xcab7e8eb": "isNonceUsed(address,uint256)",
        "0x96ade1f9": "sessionKeys(address,address)",
        "0x5197a0d3": "setAuthorizedSubmitter(address,bool)",
        "0x84f4fc6a": "revokeSessionKey(address)",
        "0xcf8fbec9": "setAuthorizedCaller(address)",
        "0xf2fde38b": "transferOwnership(address)",
    }
    for selector, signature in selector_reconstructions.items():
        assert "0x" + keccak(signature.encode())[:4].hex() == selector
    event_catalog = [
        {"topic0": topic, "reconstructed_signature": signature,
         "status": "simulated_log_only" if signature == "AuthorizedCallerUpdated(address)" else "observed_historical"}
        for signature, topic in event_signatures.items()
    ]
    error_catalog = [
        {"selector": selector, "reconstructed_signature": signature, "probe_paths": names,
         "public_signature_candidates": [signature]}
        for signature, (selector, names) in error_probes.items()
    ]
    result = {"pin": PIN, "block_hash": manifest["block_hash"], "address": PROXY,
              "implementation": IMPLEMENTATION,
              "registration_count": len(records), "nonce_call_count": len(nonce_records),
              "historical_signer_call_count": len(signer_records),
              "committed_nonce_calls": 16, "rolled_back_nonce_calls": 3,
              "register_typehash": "0x" + register_typehash.hex(),
              "domain_separator": "0x" + domain.hex(),
              "selector_reconstructions": selector_reconstructions,
              "event_catalog": event_catalog, "simulated_error_catalog": error_catalog,
              "storage_bases": {"sessionKeys_user_key": 4, "nonces_user": 5,
                                "nonceBitmap_user_wordIndex": 6, "authorizedSubmitters": 7},
              "registrations": records, "nonce_calls": nonce_records,
              "historical_signer_calls": signer_records,
              "limits": ["Some selector source names and the registration type string remain unresolved.",
                         "The purpose of the signed associated address is not established by these samples.",
                         "The ten registrations are a recent sample, not complete registration history.",
                         "The 18 signer calls validate an unexpired registered key at each sampled block but do not cover direct-user signatures or all rejection branches.",
                         "Three nonce calls returned inside Exchange paths that later reverted; their bits were rolled back.",
                         "Read-only simulated owner changes and revocations did not alter pinned chain state."]}
    (ATLAS / "session_key_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("session keys:", len(records), "registrations,", len(nonce_records), "nonce calls")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    analyze()
