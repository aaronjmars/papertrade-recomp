#!/usr/bin/env python3
"""Decode scheduled timelock operations and query their pinned status."""

import json
import pathlib

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
PIN = 48902346
logs = json.loads((ATLAS / "timelock_all_logs.json").read_text())
catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
manifest = json.loads((ATLAS / "manifest.json").read_text())
names = {}
for address, entry in catalog.items():
    names[address] = {x["selector"]: x["candidate_signature"] for x in entry["functions"]}


def read_uint(selector, operation_id):
    return int(rpc("eth_call", [{"to": TIMELOCK, "data": selector + operation_id[2:]}, hex(PIN)]), 16)


operations = []
for log in logs:
    if log["topics"][0] != "0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39":
        continue
    payload = bytes.fromhex(log["data"][2:])
    word = lambda index: int.from_bytes(payload[index * 32:(index + 1) * 32], "big")
    offset = word(1)
    size = int.from_bytes(payload[offset:offset + 32], "big")
    call_data = payload[offset + 32:offset + 32 + size]
    target = "0x" + log["topics"][2][-40:]
    target_impl = "0x" + manifest["contracts"].get(target, {}).get("eip1967_slots", {}).get("implementation", "0x" + "0" * 64)[-40:]
    selector = "0x" + call_data[:4].hex()
    name = names.get(target_impl, {}).get(selector) or names.get(target, {}).get(selector, "")
    operation_id = log["topics"][1]
    operations.append({"operation_id": operation_id, "scheduled_block": int(log["blockNumber"], 16),
                       "schedule_tx": log["transactionHash"], "target": target,
                       "target_role": manifest["contracts"].get(target, {}).get("role", "external"),
                       "value": word(0), "predecessor": "0x" + word(2).to_bytes(32, "big").hex(),
                       "ready_timestamp_from_event": word(3), "call_selector": selector,
                       "candidate_signature": name, "call_arguments_uint256_words": [int.from_bytes(call_data[i:i + 32], "big") for i in range(4, len(call_data), 32)],
                       "pinned_timestamp": read_uint("0x6cb6a1f7", operation_id),
                       "is_done_at_pin": bool(read_uint("0x2ab0f529", operation_id)),
                       "is_pending_at_pin": bool(read_uint("0x584b153e", operation_id)),
                       "is_ready_at_pin": bool(read_uint("0x13bc9f20", operation_id))})
min_delay = int(rpc("eth_call", [{"to": TIMELOCK, "data": "0xc63c4e9b"}, hex(PIN)]), 16)
(ATLAS / "timelock_operations.json").write_text(json.dumps({"pin": PIN, "min_delay_seconds": min_delay,
    "operations": operations, "source": "timelock_all_logs.json and pinned eth_call getters"}, indent=2) + "\n")
print(len(operations), "scheduled operations", min_delay, "second current minimum delay")
