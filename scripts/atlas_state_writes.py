#!/usr/bin/env python3
"""Map observed transaction storage writes to pinned contract roles."""

import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
TRACES = ROOT / "artifacts" / "historical"
TRACE_DIRS = (TRACES, ROOT / "artifacts" / "session_keys", ROOT / "artifacts" / "exchange_sweeps",
              ROOT / "artifacts" / "factory_creation", ROOT / "artifacts" / "oracle_creation",
              ROOT / "artifacts" / "tokenomics", ROOT / "artifacts" / "exchange_core_withdrawal",
              ROOT / "artifacts" / "exchange_getters",
              ROOT / "artifacts" / "exchange_batch_thresholds", ROOT / "artifacts" / "staking",
              ROOT / "artifacts" / "paper_token", ROOT / "artifacts" / "session_creation")
DIFF_DIRS = TRACE_DIRS + (ROOT / "artifacts" / "liquidation_tokenomics",)
manifest = json.loads((ATLAS / "manifest.json").read_text())
PROXY_CONTROL_SLOTS = {
    "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc": "implementation",
    "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103": "admin",
}
instances = json.loads((ATLAS / "deposit_proxy_instances.json").read_text())
roles = {a: c["role"] for a, c in manifest["contracts"].items()}
roles.update({x["address"]: "user_deposit_proxy" for x in instances["instances"]})
storage_views = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
slot_names = collections.defaultdict(lambda: collections.defaultdict(set))
for contract in storage_views.values():
    for view in contract["views"]:
        if view["arguments"] or not view.get("candidate_signature"):
            continue
        for slot in view.get("direct_slots", []):
            slot_names[contract["target"]][slot].add(view["candidate_signature"].split("|")[0])

saved = {}
for directory in TRACE_DIRS:
    for call_path in sorted(directory.glob("*.calls.json")):
        stem = call_path.name.removesuffix(".calls.json")
        receipt_path = directory / f"{stem}.receipt.json"
        if receipt_path.exists():
            tx = json.loads(receipt_path.read_text())["transactionHash"].lower()
            if stem.startswith("0x"):
                assert stem.lower() == tx
            if tx not in saved:
                saved[tx] = (call_path, receipt_path)
state_diffs = {}
for directory in DIFF_DIRS:
    for path in sorted(directory.glob("*.state_diff.json")):
        stem = path.name.removesuffix(".state_diff.json")
        receipt_path = directory / f"{stem}.receipt.json"
        tx = json.loads(receipt_path.read_text())["transactionHash"].lower() if receipt_path.exists() else stem
        if stem.startswith("0x"):
            assert stem.lower() == tx
        state_diffs.setdefault(tx, path)

transactions = []
summary = collections.defaultdict(lambda: {"transaction_count": 0, "direct_slots": collections.Counter(),
                                      "proxy_control_slots": collections.Counter(), "dynamic_slot_count": 0,
                                      "cleared_direct_slot_count": 0, "cleared_dynamic_slot_count": 0})
for tx_hash, (call_path, receipt_path) in sorted(saved.items()):
    if tx_hash not in state_diffs:
        continue
    data = json.loads(state_diffs[tx_hash].read_text())
    root = json.loads(call_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    changes = []
    pre_accounts = {address.lower(): account for address, account in data.get("pre", {}).items()}
    post_accounts = {address.lower(): account for address, account in data.get("post", {}).items()}
    for address in sorted(set(pre_accounts) | set(post_accounts)):
        before = pre_accounts.get(address, {}).get("storage", {})
        after = post_accounts.get(address, {}).get("storage", {})
        slots = sorted(set(before) | set(after), key=lambda slot: int(slot, 16))
        if not slots:
            continue
        direct = []
        proxy_control = []
        dynamic = []
        cleared_dynamic = []
        role = roles.get(address, "external_or_system")
        for slot in slots:
            previous = int(before.get(slot, "0x0"), 16)
            current = int(after.get(slot, "0x0"), 16)
            if previous == current:
                continue
            entry = {"slot": slot, "value": f"0x{current:064x}",
                     "previous_value": f"0x{previous:064x}",
                     "cleared": previous != 0 and current == 0}
            if slot in PROXY_CONTROL_SLOTS:
                entry["kind"] = PROXY_CONTROL_SLOTS[slot]
                proxy_control.append(entry)
                summary[role]["proxy_control_slots"][entry["kind"]] += 1
            elif int(slot, 16) < 512:
                entry["getter_candidates"] = sorted(slot_names[address].get(int(slot, 16), []))
                direct.append(entry)
                summary[role]["direct_slots"][slot] += 1
                if entry["cleared"]:
                    summary[role]["cleared_direct_slot_count"] += 1
            else:
                dynamic.append(slot)
                if entry["cleared"]:
                    cleared_dynamic.append(slot)
                    summary[role]["cleared_dynamic_slot_count"] += 1
        if not direct and not proxy_control and not dynamic:
            continue
        summary[role]["transaction_count"] += 1
        summary[role]["dynamic_slot_count"] += len(dynamic)
        changes.append({"address": address, "role": role,
                        "direct_slots": direct, "proxy_control_slots": proxy_control,
                        "dynamic_slots": dynamic, "cleared_dynamic_slots": cleared_dynamic})
    root_to = root.get("to")
    assert receipt["transactionHash"].lower() == tx_hash
    creation = root.get("type") in ("CREATE", "CREATE2")
    transactions.append({"tx": tx_hash, "block": int(receipt["blockNumber"], 16),
                         "status": int(receipt["status"], 16), "root_call_type": root.get("type"),
                         "root_selector": None if creation else root.get("input", "")[:10],
                         "root_initcode_prefix": root.get("input", "")[:10] if creation else None,
                         "root_role": roles.get(root_to.lower(), "external_or_system") if root_to else "contract_creation",
                         "changes": changes, "source_directory": call_path.parent.name})
output = {"transactions": transactions,
          "summary": {role: {"transaction_count": item["transaction_count"], "direct_slots": dict(item["direct_slots"]),
                             "proxy_control_slots": dict(item["proxy_control_slots"]),
                             "dynamic_slot_count": item["dynamic_slot_count"],
                             "cleared_direct_slot_count": item["cleared_direct_slot_count"],
                             "cleared_dynamic_slot_count": item["cleared_dynamic_slot_count"]}
                      for role, item in summary.items()},
          "slot_classification": "EIP-1967 implementation and admin slots are listed separately from direct and dynamic application storage",
          "diff_mode_semantics": "A pre-only storage key is a zeroed slot; a post-only key was created. Both are included as writes."}
(ATLAS / "state_write_catalog.json").write_text(json.dumps(output, indent=2) + "\n")
print(len(transactions), "transactions", len(summary), "roles with writes")
