#!/usr/bin/env python3
"""Probe Papertrade timelock paths at the pinned block without sending transactions."""

import json
import pathlib
import subprocess

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PIN = 48902346
TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OWNER = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
OUTSIDER = "0x1111111111111111111111111111111111111111"
ZERO = "0x" + "00" * 32


def word(value):
    return value.to_bytes(32, "big")


def cast(*args):
    return subprocess.run(["cast", *args], check=True, capture_output=True, text=True).stdout.strip()


def mapping_slot(operation_id):
    return cast("keccak", "0x" + (bytes.fromhex(operation_id[2:]) + word(2)).hex())


def single_args(target, value, payload, predecessor):
    return (bytes.fromhex(target[2:]).rjust(32, b"\x00") + word(value) + word(128)
            + bytes.fromhex(predecessor[2:]) + word(len(payload))
            + payload.ljust((len(payload) + 31) // 32 * 32, b"\x00"))


def call(selector_and_args, sender=OWNER, *, time=None, state_diff=None, value=0, balance_override=None,
         tracer="callTracer", with_logs=False):
    tx = {"from": sender, "to": TIMELOCK, "data": selector_and_args, "gas": "0x989680"}
    if value:
        tx["value"] = hex(value)
    opts = {"tracer": tracer} if tracer else {"disableStorage": True, "disableMemory": True}
    if with_logs:
        opts["tracerConfig"] = {"withLog": True}
    if tracer == "prestateTracer":
        opts["tracerConfig"] = {"diffMode": True}
    if time is not None:
        opts["blockOverrides"] = {"time": hex(time)}
    overrides = {}
    if state_diff:
        overrides[TIMELOCK] = {"stateDiff": state_diff}
    if balance_override is not None:
        overrides[sender] = {"balance": hex(balance_override)}
    if overrides:
        opts["stateOverrides"] = overrides
    return rpc("debug_traceCall", [tx, hex(PIN), opts])


def outcome(trace):
    return {"success": not trace.get("error"), "error": trace.get("error"),
            "revert_selector": trace.get("output", "")[:10] if trace.get("error") else None,
            "child_calls": [{"to": x.get("to"), "selector": x.get("input", "")[:10],
                             "value": x.get("value"), "error": x.get("error")} for x in trace.get("calls", [])],
            "event_topics": [x["topics"][0] for x in trace.get("logs", []) if x.get("topics")],
            "events": [{"address": x.get("address"), "topics": x["topics"], "data": x.get("data", "0x")}
                       for x in trace.get("logs", []) if x.get("topics")]}


manifest = json.loads((ATLAS / "manifest.json").read_text())
operations = json.loads((ATLAS / "timelock_operations.json").read_text())["operations"]
logs = json.loads((ATLAS / "timelock_all_logs.json").read_text())
rows = []
for operation in operations:
    log = next(x for x in logs if len(x["topics"]) > 1 and x["topics"][1] == operation["operation_id"])
    data = bytes.fromhex(log["data"][2:])
    offset = int.from_bytes(data[32:64], "big")
    size = int.from_bytes(data[offset:offset + 32], "big")
    payload = data[offset + 32:offset + 32 + size]
    encoded = single_args(operation["target"], operation["value"], payload, operation["predecessor"])
    hash_result = rpc("eth_call", [{"to": TIMELOCK, "data": "0xec2a5b45" + encoded.hex()}, hex(PIN)])
    payload_hash = cast("keccak", "0x" + payload.hex())
    formula_hash = cast("keccak", cast("abi-encode", "x(address,uint256,bytes32,bytes32)",
        operation["target"], str(operation["value"]), payload_hash, operation["predecessor"]))
    predecessor_timestamp = int(rpc("eth_call", [{"to": TIMELOCK,
        "data": "0x6cb6a1f7" + operation["predecessor"][2:]}, hex(PIN)]), 16)
    predecessor_done = bool(int(rpc("eth_call", [{"to": TIMELOCK,
        "data": "0x2ab0f529" + operation["predecessor"][2:]}, hex(PIN)]), 16))
    execute_data = "0x88aa4c12" + encoded.hex()
    owner_at_pin = call(execute_data, with_logs=True)
    outsider_at_pin = call(execute_data, sender=OUTSIDER)
    before_ready = None
    if not operation["is_ready_at_pin"]:
        before_ready = outcome(call(execute_data, time=operation["ready_timestamp_from_event"] - 1))
    execution_time = max(manifest["timestamp"], operation["ready_timestamp_from_event"])
    owner_at_ready = call(execute_data, time=execution_time, with_logs=True)
    opcodes = call(execute_data, time=execution_time, tracer=None)["structLogs"]
    root_sloads = ["0x" + x["stack"][-1].removeprefix("0x").zfill(64)
                   for x in opcodes if x["depth"] == 1 and x["op"] == "SLOAD"]
    root_sstores = ["0x" + x["stack"][-1].removeprefix("0x").zfill(64)
                    for x in opcodes if x["depth"] == 1 and x["op"] == "SSTORE"]
    state = call(execute_data, time=execution_time, tracer="prestateTracer")
    cancel_data = "0xc4d252f5" + operation["operation_id"][2:]
    done_override = {mapping_slot(operation["operation_id"]): "0x" + word(1).hex()}
    row = {
        "operation_id": operation["operation_id"], "payload_keccak256": payload_hash,
        "hash_operation_matches_scheduled_id": hash_result == operation["operation_id"],
        "hash_formula_matches_scheduled_id": formula_hash == operation["operation_id"],
        "predecessor": operation["predecessor"], "predecessor_timestamp_at_pin": predecessor_timestamp,
        "predecessor_done_at_pin": predecessor_done,
        "operation_mapping_slot": mapping_slot(operation["operation_id"]),
        "predecessor_mapping_slot": mapping_slot(operation["predecessor"]),
        "execute_owner_at_pin": outcome(owner_at_pin), "execute_outsider_at_pin": outcome(outsider_at_pin),
        "execute_owner_before_ready": before_ready, "execute_owner_at_ready": outcome(owner_at_ready),
        "execution_time_used": execution_time,
        "root_sload_slots_at_ready": root_sloads, "root_sstore_slots_at_ready": root_sstores,
        "simulated_storage_post": {a: v.get("storage", {}) for a, v in state.get("post", {}).items() if v.get("storage")},
        "cancel_owner_at_pin": outcome(call(cancel_data, with_logs=True)),
        "cancel_outsider_at_pin": outcome(call(cancel_data, sender=OUTSIDER)),
        "cancel_hypothetical_done_operation": outcome(call(cancel_data, state_diff=done_override)),
        "schedule_duplicate_owner_at_pin": outcome(call("0xb0e58bc9" + encoded.hex())),
        "execute_wrong_value_owner_at_pin": outcome(call(execute_data, value=1, balance_override=1)),
        "execute_hypothetical_done_operation": outcome(call(execute_data, state_diff=done_override)),
    }
    assert row["hash_operation_matches_scheduled_id"] and row["hash_formula_matches_scheduled_id"]
    assert row["operation_mapping_slot"] in root_sloads and row["operation_mapping_slot"] in root_sstores
    assert row["predecessor_mapping_slot"] not in root_sloads
    assert row["execute_owner_at_ready"]["success"]
    rows.append(row)

def read_status(selector, operation_id, *, time=None, state_diff=None):
    trace = call(selector + operation_id[2:], sender=OUTSIDER, time=time, state_diff=state_diff)
    assert not trace.get("error")
    return int(trace["output"], 16)


pending_operation = operations[1]
ready_time = pending_operation["ready_timestamp_from_event"]
status_boundary = {"operation_id": pending_operation["operation_id"],
    "before_ready": {"pending": read_status("0x584b153e", pending_operation["operation_id"], time=ready_time - 1),
                     "ready": read_status("0x13bc9f20", pending_operation["operation_id"], time=ready_time - 1)},
    "at_ready": {"pending": read_status("0x584b153e", pending_operation["operation_id"], time=ready_time),
                 "ready": read_status("0x13bc9f20", pending_operation["operation_id"], time=ready_time)}}
done_operation_id = operations[0]["operation_id"]
done_state = {mapping_slot(done_operation_id): "0x" + word(1).hex()}
status_boundary["hypothetical_done"] = {"timestamp": read_status("0x6cb6a1f7", done_operation_id, state_diff=done_state),
    "pending": read_status("0x584b153e", done_operation_id, state_diff=done_state),
    "ready": read_status("0x13bc9f20", done_operation_id, state_diff=done_state),
    "done": read_status("0x2ab0f529", done_operation_id, state_diff=done_state)}
assert status_boundary["before_ready"] == {"pending": 1, "ready": 0}
assert status_boundary["at_ready"] == {"pending": 0, "ready": 1}
assert status_boundary["hypothetical_done"] == {"timestamp": 1, "pending": 0, "ready": 0, "done": 1}


payload = "0x8a99d586" + word(86400).hex()
batch_args = [f"[{TIMELOCK}]", "[0]", f"[{payload}]", ZERO]
batch_hash_call = cast("calldata", "hashOperationBatch(address[],uint256[],bytes[],bytes32)", *batch_args)
batch_id = rpc("eth_call", [{"to": TIMELOCK, "data": batch_hash_call}, hex(PIN)])
batch_payload_hash = cast("keccak", payload)
batch_formula_hash = cast("keccak", cast("abi-encode", "x(address[],uint256[],bytes32[],bytes32)",
    f"[{TIMELOCK}]", "[0]", f"[{batch_payload_hash}]", ZERO))
batch_schedule = cast("calldata", "scheduleBatch(address[],uint256[],bytes[],bytes32)", *batch_args)
batch_execute = cast("calldata", "executeBatch(address[],uint256[],bytes[],bytes32)", *batch_args)
ready = manifest["timestamp"] + 604800
batch_override = {mapping_slot(batch_id): "0x" + word(ready).hex()}
mismatch_args = [f"[{TIMELOCK}]", "[0,0]", f"[{payload}]", ZERO]
empty_args = ["[]", "[]", "[]", ZERO]
batch = {
    "sample": "one target, the timelock itself, calling updateMinDelay(86400); no transaction was sent",
    "operation_id": batch_id, "hash_formula_matches_call": batch_formula_hash == batch_id,
    "hypothetical_ready_timestamp": ready, "mapping_slot": mapping_slot(batch_id),
    "schedule_owner_at_pin": outcome(call(batch_schedule, with_logs=True)),
    "schedule_outsider_at_pin": outcome(call(batch_schedule, sender=OUTSIDER)),
    "execute_without_schedule_at_pin": outcome(call(batch_execute)),
    "execute_outsider_with_hypothetical_scheduled_state": outcome(call(batch_execute, sender=OUTSIDER,
        time=ready, state_diff=batch_override)),
    "schedule_length_mismatch": outcome(call(cast("calldata", "scheduleBatch(address[],uint256[],bytes[],bytes32)", *mismatch_args))),
    "execute_length_mismatch": outcome(call(cast("calldata", "executeBatch(address[],uint256[],bytes[],bytes32)", *mismatch_args))),
    "schedule_empty_batch": outcome(call(cast("calldata", "scheduleBatch(address[],uint256[],bytes[],bytes32)", *empty_args))),
    "execute_with_hypothetical_scheduled_state_at_ready": outcome(call(batch_execute, time=ready,
        state_diff=batch_override, with_logs=True)),
}
batch_schedule_state = call(batch_schedule, tracer="prestateTracer")
batch["simulated_schedule_storage_post"] = batch_schedule_state.get("post", {}).get(TIMELOCK, {}).get("storage", {})
assert int(batch["simulated_schedule_storage_post"][mapping_slot(batch_id)], 16) == ready
batch_opcodes = call(batch_execute, time=ready, state_diff=batch_override, tracer=None)["structLogs"]
batch["root_state_write_and_call_order"] = [{"pc": x["pc"], "op": x["op"]} for x in batch_opcodes
    if x["depth"] == 1 and x["op"] in ("SSTORE", "CALL")]
batch_state = call(batch_execute, time=ready, state_diff=batch_override, tracer="prestateTracer")
batch["simulated_timelock_storage_post"] = batch_state.get("post", {}).get(TIMELOCK, {}).get("storage", {})
assert batch["hash_formula_matches_call"] and batch["schedule_owner_at_pin"]["success"]
assert batch["execute_with_hypothetical_scheduled_state_at_ready"]["success"]

update_data = "0x8a99d586" + word(86400).hex()
update_min_delay = {"owner_direct": outcome(call(update_data)),
                    "self_direct": outcome(call(update_data, sender=TIMELOCK))}
assert not update_min_delay["owner_direct"]["success"] and update_min_delay["self_direct"]["success"]

new_owner = "0x1111111111111111111111111111111111111111"
transfer_data = "0xf2fde38b" + bytes.fromhex(new_owner[2:]).rjust(32, b"\x00").hex()
zero_owner_data = "0xf2fde38b" + ZERO[2:]
transfer_ownership = {"owner_direct": outcome(call(transfer_data)),
                      "self_valid": outcome(call(transfer_data, sender=TIMELOCK, with_logs=True)),
                      "self_zero": outcome(call(zero_owner_data, sender=TIMELOCK))}
transfer_state = call(transfer_data, sender=TIMELOCK, tracer="prestateTracer")
transfer_ownership["simulated_storage_post"] = transfer_state.get("post", {}).get(TIMELOCK, {}).get("storage", {})
assert not transfer_ownership["owner_direct"]["success"] and transfer_ownership["self_valid"]["success"]

def hypothetical_batch(args, *, value=0, balance_override=None, with_logs=False):
    operation_id = rpc("eth_call", [{"to": TIMELOCK, "data": cast("calldata",
        "hashOperationBatch(address[],uint256[],bytes[],bytes32)", *args)}, hex(PIN)])
    data = cast("calldata", "executeBatch(address[],uint256[],bytes[],bytes32)", *args)
    state = {mapping_slot(operation_id): "0x" + word(manifest["timestamp"]).hex()}
    trace = call(data, state_diff=state, value=value, balance_override=balance_override, with_logs=with_logs)
    return operation_id, data, state, trace


second_delay = "0x8a99d586" + word(43200).hex()
success_args = [f"[{TIMELOCK},{TIMELOCK}]", "[0,0]", f"[{payload},{second_delay}]", ZERO]
success_id, success_data, success_state, success_trace = hypothetical_batch(success_args, with_logs=True)
success_post = call(success_data, state_diff=success_state, tracer="prestateTracer")
multi_target_success = {"operation_id": success_id, "execution": outcome(success_trace),
    "simulated_timelock_storage_post": success_post.get("post", {}).get(TIMELOCK, {}).get("storage", {})}
assert multi_target_success["execution"]["success"]
assert len(multi_target_success["execution"]["child_calls"]) == 2
assert int(multi_target_success["execution"]["events"][0]["data"], 16) == 2
assert int(multi_target_success["simulated_timelock_storage_post"]["0x" + word(1).hex()], 16) == 43200

value_args = ["[0x1111111111111111111111111111111111111111,0x2222222222222222222222222222222222222222]",
              "[1,2]", "[0x,0x]", ZERO]
value_results = {}
for sent in (2, 3, 4):
    _, _, _, trace = hypothetical_batch(value_args, value=sent, balance_override=4)
    value_results[str(sent)] = outcome(trace)
assert value_results["2"]["revert_selector"] == "0xaa7feadc"
assert value_results["3"]["success"] and len(value_results["3"]["child_calls"]) == 2
assert value_results["4"]["revert_selector"] == "0xaa7feadc"


def failure_probe(hash_signature, execute_signature, args):
    hash_data = cast("calldata", hash_signature, *args)
    operation_id = rpc("eth_call", [{"to": TIMELOCK, "data": hash_data}, hex(PIN)])
    execute_data = cast("calldata", execute_signature, *args)
    ready_state = {mapping_slot(operation_id): "0x" + word(manifest["timestamp"]).hex()}
    trace = call(execute_data, state_diff=ready_state)
    diff = call(execute_data, state_diff=ready_state, tracer="prestateTracer")
    return {"operation_id": operation_id, "target_call_count": len(trace.get("calls", [])),
            "execution": outcome(trace), "timelock_storage_post": diff.get("post", {}).get(TIMELOCK, {}).get("storage", {})}


failure_probes = {
    "single_self_call_transfer_ownership_to_zero": failure_probe(
        "hashOperation(address,uint256,bytes,bytes32)",
        "execute(address,uint256,bytes,bytes32)", [TIMELOCK, "0", zero_owner_data, ZERO]),
    "two_target_batch_second_call_fails": failure_probe(
        "hashOperationBatch(address[],uint256[],bytes[],bytes32)",
        "executeBatch(address[],uint256[],bytes[],bytes32)",
        [f"[{TIMELOCK},{TIMELOCK}]", "[0,0]", f"[{payload},{zero_owner_data}]", ZERO]),
}
assert all(not x["execution"]["success"] and x["execution"]["revert_selector"] == "0x15fcd675"
           and not x["timelock_storage_post"] for x in failure_probes.values())


result = {"pin": PIN, "method": "eth_call and read-only debug_traceCall at pinned state; batch execute uses an explicit hypothetical storage and time override",
          "timelock": TIMELOCK, "owner": OWNER, "storage_layout": {"owner_slot": 0, "min_delay_slot": 1,
          "operation_timestamp_mapping_base_slot": 2, "unscheduled_value": 0, "done_value": 1},
          "scheduled_operations": rows, "status_getter_boundary_probes": status_boundary,
          "batch_probe": batch, "update_min_delay_probe": update_min_delay,
          "transfer_ownership_probe": transfer_ownership, "failure_probes": failure_probes,
          "multi_target_success_probe": multi_target_success, "batch_value_probe": value_results,
          "cancel_unscheduled_owner_at_pin": outcome(call("0xc4d252f5" + ZERO[2:]))}
public_error_candidates = {
    "0x15fcd675": ["ExecutionFailed(bytes)"], "0x18d96a80": [],
    "0x27c0d610": ["OperationNotScheduled()"], "0x29c3b7ee": ["NotSelf()"],
    "0x30cd7471": ["NotOwner()"], "0x49e27cff": ["InvalidOwner()"],
    "0x9b382476": ["OperationAlreadyScheduled()"], "0xaa7feadc": ["InvalidValue()"],
    "0xf800799b": ["OperationNotReady()"], "0xff633a38": ["LengthMismatch()"],
}
observed_error_paths = {}


def find_errors(value, path=""):
    if isinstance(value, dict):
        if value.get("revert_selector"):
            observed_error_paths.setdefault(value["revert_selector"], []).append(path)
        for key, item in value.items():
            find_errors(item, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            find_errors(item, f"{path}[{index}]")


find_errors(result)
assert set(observed_error_paths) <= set(public_error_candidates)
public_event_candidates = {
    "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b": ["OwnerUpdated(address)"],
    "0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464": ["MinDelayUpdated(uint256)"],
    "0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39": ["OperationScheduled(bytes32,address,uint256,bytes,bytes32,uint256)"],
    "0x2a08801cf3674ab09756ae78a3a4833813465af6af958136b360eab6b71c8952": ["OperationExecuted(bytes32,address,uint256,bytes)"],
    "0xcf0f63b97f3387253cbc0bde884f975df77e39184dc3280c2c81be495f58eef4": ["OperationCancelled(bytes32)"],
    "0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f": [],
    "0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd": ["BatchOperationExecuted(bytes32,uint256)"],
}
simulated_event_paths = {}


def find_events(value, path=""):
    if isinstance(value, dict):
        if "event_topics" in value:
            for topic in value["event_topics"]:
                simulated_event_paths.setdefault(topic, []).append(path)
        for key, item in value.items():
            find_events(item, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            find_events(item, f"{path}[{index}]")


find_events(result)
assert set(simulated_event_paths) <= set(public_event_candidates)
historical_topic_counts = {topic: sum(x["topics"][0] == topic for x in logs)
                           for topic in public_event_candidates}
reconstructed_events = {"0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f":
    "BatchOperationScheduled(bytes32,uint256,bytes32,uint256)"}
assert all(cast("keccak", signature) == topic for topic, signature in reconstructed_events.items())
result["event_catalog"] = [{"topic0": topic, "public_signature_candidates": signatures,
    "reconstructed_signature": reconstructed_events.get(topic),
    "historical_log_count": historical_topic_counts[topic],
    "simulated_probe_paths": simulated_event_paths.get(topic, [])}
    for topic, signatures in sorted(public_event_candidates.items())]
result["simulated_error_catalog"] = [{"selector": selector,
    "public_signature_candidates": public_error_candidates[selector],
    "probe_paths": paths, "status": "observed_in_read_only_simulation"}
    for selector, paths in sorted(observed_error_paths.items())]
(ATLAS / "timelock_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
print(len(rows), "scheduled operations probed; batch schedule and execute simulated")
