#!/usr/bin/env python3
"""Reconstruct the Papertrade multisig at the pinned block with read-only probes."""

import json
import pathlib
import subprocess

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PIN = 48902346
MULTISIG = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x1111111111111111111111111111111111111111"
ZERO = "0x" + "00" * 32


def word(value):
    return value.to_bytes(32, "big")


def cast(*args):
    return subprocess.run(["cast", *args], check=True, capture_output=True, text=True).stdout.strip()


def view(selector, suffix=""):
    return rpc("eth_call", [{"to": MULTISIG, "data": selector + suffix}, hex(PIN)])


def simulate(data, sender, *, state_overrides=None, tracer="callTracer", with_logs=False):
    options = {"tracer": tracer}
    if tracer == "prestateTracer":
        options["tracerConfig"] = {"diffMode": True}
    if with_logs:
        options["tracerConfig"] = {"withLog": True}
    if state_overrides:
        options["stateOverrides"] = state_overrides
    return rpc("debug_traceCall", [{"from": sender, "to": MULTISIG, "data": data, "gas": "0x989680"},
                                   hex(PIN), options])


def outcome(trace):
    return {"success": not trace.get("error"), "error": trace.get("error"),
            "revert_selector": trace.get("output", "")[:10] if trace.get("error") else None,
            "return_data": trace.get("output", "") if not trace.get("error") else None,
            "child_calls": [{"to": c.get("to"), "selector": c.get("input", "")[:10],
                             "value": c.get("value"), "error": c.get("error"),
                             "revert_selector": c.get("output", "")[:10] if c.get("error") else None}
                            for c in trace.get("calls", [])],
            "events": [{"address": e.get("address"), "topics": e["topics"], "data": e.get("data", "0x")}
                       for e in trace.get("logs", []) if e.get("topics")]}


signers = ["0x" + view(selector)[-40:] for selector in ("0xd98f851a", "0x1a5f66c3", "0x64d62769")]
epoch = int(view("0x900cf0cf"), 16)
count = int(view("0xb77bf600"), 16)
required = int(view("0x82e717f7"), 16)
assert count == 7 and epoch == 1 and required == 2 and len(set(signers)) == 3

records = []
for index in range(count):
    raw = bytes.fromhex(view("0x9ace38c2", word(index).hex())[2:])
    number = lambda position: int.from_bytes(raw[position * 32:(position + 1) * 32], "big")
    offset = number(2)
    payload_size = int.from_bytes(raw[offset:offset + 32], "big")
    payload = raw[offset + 32:offset + 32 + payload_size]
    destination = "0x" + raw[12:32].hex()
    submitter = "0x" + raw[108:128].hex()
    payload_hash = cast("keccak", "0x" + payload.hex())
    formula_hash = cast("keccak", cast("abi-encode", "x(uint256,address,uint256,address,uint256,bytes32,uint256)",
        "999", MULTISIG, str(index), destination, str(number(1)), payload_hash, str(number(4))))
    actual_hash = view("0x27865bb3", word(index).hex())
    base_slot = int(cast("keccak", "0x" + (word(index) + word(5)).hex()), 16)
    storage = [rpc("eth_getStorageAt", [MULTISIG, hex(base_slot + position), hex(PIN)]) for position in range(6)]
    assert formula_hash == actual_hash
    assert int(storage[0], 16) == int(destination, 16)
    assert int(storage[1], 16) == number(1)
    assert int(storage[2], 16) == payload_size * 2 + 1
    assert int(storage[3], 16) == int(submitter, 16)
    assert int(storage[4], 16) == number(4) and int(storage[5], 16) == number(5)
    records.append({"index": index, "destination": destination, "value": number(1),
                    "payload": "0x" + payload.hex(), "payload_bytes": payload_size,
                    "payload_keccak256": payload_hash, "submitter": submitter, "epoch": number(4),
                    "status": number(5), "transaction_hash": actual_hash,
                    "hash_formula_matches": formula_hash == actual_hash,
                    "mapping_base_slot": hex(base_slot), "raw_storage_fields": storage})

signer_checks = {address: bool(int(view("0x7df73e27", word(int(address, 16)).hex()), 16))
                 for address in [*signers, OUTSIDER]}
assert all(signer_checks[x] for x in signers) and not signer_checks[OUTSIDER]

pending = records[4]
confirm_data = "0x7b1106de" + word(pending["index"]).hex() + pending["transaction_hash"][2:]
revoke_data = "0x735631ad" + word(pending["index"]).hex()
submit_data = cast("calldata", "submitTransaction(address,uint256,bytes)", OUTSIDER, "0", "0x")

submit_probes = {"signer": outcome(simulate(submit_data, signers[0], with_logs=True)),
                 "outsider": outcome(simulate(submit_data, OUTSIDER))}
submit_diff = simulate(submit_data, signers[0], tracer="prestateTracer")
submit_probes["simulated_multisig_storage_post"] = submit_diff.get("post", {}).get(MULTISIG, {}).get("storage", {})
assert submit_probes["signer"]["success"] and not submit_probes["outsider"]["success"]
assert int(submit_probes["simulated_multisig_storage_post"]["0x" + word(4).hex()], 16) == 8

confirm_probes = {
    "outsider": outcome(simulate(confirm_data, OUTSIDER)),
    "submitter": outcome(simulate(confirm_data, pending["submitter"])),
    "other_signer_one": outcome(simulate(confirm_data, signers[0], with_logs=True)),
    "other_signer_three": outcome(simulate(confirm_data, signers[2])),
    "wrong_hash": outcome(simulate("0x7b1106de" + word(4).hex() + ZERO[2:], signers[0])),
    "invalid_id": outcome(simulate("0x7b1106de" + word(count).hex() + pending["transaction_hash"][2:], signers[0])),
    "revoked": outcome(simulate("0x7b1106de" + word(2).hex() + records[2]["transaction_hash"][2:], signers[0])),
    "executed": outcome(simulate("0x7b1106de" + word(1).hex() + records[1]["transaction_hash"][2:], signers[0])),
    "stale_epoch": outcome(simulate(confirm_data, signers[0],
        state_overrides={MULTISIG: {"stateDiff": {"0x" + word(3).hex(): "0x" + word(epoch + 1).hex()}}})),
}
confirm_opcodes = rpc("debug_traceCall", [{"from": signers[0], "to": MULTISIG, "data": confirm_data,
    "gas": "0x989680"}, hex(PIN), {"disableStorage": True, "disableMemory": True}])["structLogs"]
confirm_order = [{"pc": item["pc"], "op": item["op"],
                  "top_stack": item["stack"][-1] if item.get("stack") else None}
                 for item in confirm_opcodes if item["depth"] == 1 and item["op"] in ("SSTORE", "CALL")]
assert [x["op"] for x in confirm_order] == ["SSTORE", "CALL"]
assert int(confirm_order[0]["top_stack"], 16) == int(pending["mapping_base_slot"], 16) + 5
confirm_probes["root_storage_write_and_call_order"] = confirm_order
successful_confirm_diff = simulate(confirm_data, signers[0], tracer="prestateTracer")
confirm_probes["successful_confirm_storage_post"] = {a: x.get("storage", {})
    for a, x in successful_confirm_diff.get("post", {}).items() if x.get("storage")}
assert confirm_probes["other_signer_one"]["success"] and confirm_probes["other_signer_three"]["success"]
timelock_writes = confirm_probes["successful_confirm_storage_post"][TIMELOCK]
assert len(timelock_writes) == 1
scheduled_slot = next(iter(timelock_writes))
confirm_probes["target_failure"] = outcome(simulate(confirm_data, signers[0],
    state_overrides={TIMELOCK: {"stateDiff": {scheduled_slot: "0x" + word(1).hex()}}}))
target_failure_diff = simulate(confirm_data, signers[0], tracer="prestateTracer",
    state_overrides={TIMELOCK: {"stateDiff": {scheduled_slot: "0x" + word(1).hex()}}})
confirm_probes["target_failure_storage_post"] = {a: x.get("storage", {})
    for a, x in target_failure_diff.get("post", {}).items() if x.get("storage")}
assert confirm_probes["target_failure"]["revert_selector"] == "0x15fcd675"
assert not confirm_probes["target_failure_storage_post"]

revoke_probes = {"submitter": outcome(simulate(revoke_data, pending["submitter"], with_logs=True)),
                 "submitter_after_epoch_change": outcome(simulate(revoke_data, pending["submitter"],
                     state_overrides={MULTISIG: {"stateDiff": {"0x" + word(3).hex(): "0x" + word(epoch + 1).hex()}}})),
                 "other_signer": outcome(simulate(revoke_data, signers[0])),
                 "outsider": outcome(simulate(revoke_data, OUTSIDER))}
assert revoke_probes["submitter"]["success"] and revoke_probes["submitter_after_epoch_change"]["success"]

valid_update = cast("calldata", "updateSigners(address,address,address)", *signers)
zero_address = "0x" + "00" * 20
update_probes = {"direct_signer": outcome(simulate(valid_update, signers[0])),
                 "self_valid": outcome(simulate(valid_update, MULTISIG, with_logs=True)),
                 "self_zero": outcome(simulate(cast("calldata", "updateSigners(address,address,address)",
                     zero_address, signers[1], signers[2]), MULTISIG)),
                 "self_duplicate": outcome(simulate(cast("calldata", "updateSigners(address,address,address)",
                     signers[0], signers[0], signers[2]), MULTISIG)),
                 "self_address_as_signer": outcome(simulate(cast("calldata", "updateSigners(address,address,address)",
                     signers[0], signers[1], MULTISIG), MULTISIG))}
update_diff = simulate(valid_update, MULTISIG, tracer="prestateTracer")
update_probes["simulated_storage_post"] = update_diff.get("post", {}).get(MULTISIG, {}).get("storage", {})
assert update_probes["self_valid"]["success"]
assert int(update_probes["simulated_storage_post"]["0x" + word(3).hex()], 16) == epoch + 1

invalid_hash_getter = outcome(simulate("0x27865bb3" + word(count).hex(), OUTSIDER))

selector_reconstructions = {
    "0x1a5f66c3": "signerTwo()",
    "0x27865bb3": "transactionHash(uint256)",
    "0x64d62769": "signerThree()",
    "0x735631ad": "revokeTransaction(uint256)",
    "0x79301c0f": "updateSigners(address,address,address)",
    "0x7b1106de": "confirmAndExecute(uint256,bytes32)",
    "0x7df73e27": "isSigner(address)",
    "0x82e717f7": "requiredConfirmations()",
    "0x900cf0cf": "epoch()",
    "0x9ace38c2": "transactions(uint256)",
    "0xb77bf600": "transactionCount()",
    "0xc6427474": "submitTransaction(address,uint256,bytes)",
    "0xd98f851a": "signerOne()",
}
assert all(cast("sig", signature) == selector for selector, signature in selector_reconstructions.items())

event_signatures = {
    "0xbe411f0729ceed7585127466bac46d523f0ef18ba210980602e861c7a8fe4a7f":
        "TransactionSubmitted(uint256,address,address,uint256,bytes,bytes32)",
    "0xddfe9ff988d8830e7b19e61773b4a39f43d1d98b57f2aef535a4960c0291b0fd":
        "SignersUpdated(address,address,address,uint256)",
    "0xd3fb8b9f824d81f0fe695808b7b28faf553f5e7d8ff92fb5f25e210eb9134aec":
        "TransactionExecuted(uint256,address,address,uint256,bytes)",
    "0x4c4e829c9b8c87162e976ab955be6db24dace1afaa0ebe4308b6c273a92f5875":
        "TransactionRevoked(uint256)",
}
assert all(cast("keccak", signature) == topic for topic, signature in event_signatures.items())
history_rows = json.loads((ATLAS / "multisig_txs.json").read_text())
creation_row = next(x for x in history_rows if (x.get("contractAddress") or "").lower() == MULTISIG)
creation_receipt = rpc("eth_getTransactionReceipt", [creation_row["hash"]])
receipts = [creation_receipt] + [json.loads((ROOT / "artifacts" / "historical" / f"{x['hash']}.receipt.json").read_text())
    for x in history_rows if (x.get("to") or "").lower() == MULTISIG]
creation_events = [{"topic0": x["topics"][0], "data": x["data"]} for x in creation_receipt["logs"]
    if x["address"].lower() == MULTISIG and x["topics"]]
assert len(creation_events) == 1 and creation_events[0]["topic0"] == "0xddfe9ff988d8830e7b19e61773b4a39f43d1d98b57f2aef535a4960c0291b0fd"
event_catalog = [{"topic0": topic, "reconstructed_signature": signature,
                  "historical_count": sum(log["topics"] and log["topics"][0] == topic
                                          for receipt in receipts for log in receipt["logs"] if log["address"].lower() == MULTISIG)}
                 for topic, signature in sorted(event_signatures.items())]

result = {"pin": PIN, "method": "pinned eth_call, raw eth_getStorageAt, historical receipts, and read-only debug_traceCall",
          "address": MULTISIG, "required_confirmations": required, "signers": signers,
          "current_epoch": epoch, "transaction_count": count, "signer_checks": signer_checks,
          "storage_layout": {"slot_0": "signerOne", "slot_1": "signerTwo", "slot_2": "signerThree",
                             "slot_3": "epoch", "slot_4": "transactionCount", "mapping_slot_5":
                             ["destination", "value", "data bytes", "submitter", "epoch", "status"]},
          "status_values": {"0": "pending", "1": "executed", "2": "revoked"},
          "transaction_hash_formula": "keccak256(abi.encode(chainid, address(this), index, destination, value, keccak256(data), epoch))",
          "records": records, "selector_reconstructions": selector_reconstructions,
          "creation": {"tx": creation_row["hash"], "block": int(creation_receipt["blockNumber"], 16),
          "events": creation_events}, "event_catalog": event_catalog, "submit_probes": submit_probes,
          "confirm_probes": confirm_probes, "revoke_probes": revoke_probes,
          "update_signers_probes": update_probes, "invalid_hash_getter_probe": invalid_hash_getter}

public_error_candidates = {"0x137b4559": [], "0x15fcd675": ["ExecutionFailed(bytes)"],
    "0x29c3b7ee": ["NotSelf()"], "0x4e11f906": ["TransactionHashMismatch()"],
    "0x500a07ce": ["InvalidTransaction()"], "0x815e1d64": ["InvalidSigner()"],
    "0x82235d53": ["TransactionNotPending()"], "0xa1b035c8": ["NotSigner()"],
    "0xc5446884": ["NotSubmitter()"], "0xe1577073": ["StaleTransaction()"]}
error_paths = {}


def collect_errors(value, path=""):
    if isinstance(value, dict):
        if value.get("revert_selector"):
            error_paths.setdefault(value["revert_selector"], []).append(path)
        for key, item in value.items():
            if key == "child_calls":
                continue
            collect_errors(item, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            collect_errors(item, f"{path}[{index}]")


collect_errors(result)
assert set(error_paths) <= set(public_error_candidates)
result["simulated_error_catalog"] = [{"selector": selector,
    "public_signature_candidates": public_error_candidates[selector], "probe_paths": paths,
    "status": "observed_in_read_only_simulation"} for selector, paths in sorted(error_paths.items())]
assert len(result["simulated_error_catalog"]) == 10
(ATLAS / "multisig_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
print(count, "stored transactions validated", len(event_catalog), "events", len(error_paths), "errors probed")
