#!/usr/bin/env python3
"""Catalog event topics seen in saved historical transaction receipts."""

import collections
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
TRACES = ROOT / "artifacts" / "historical"
EXTRA_RECEIPTS = (ROOT / "artifacts" / "exchange_positions", ROOT / "artifacts" / "factory_creation", ROOT / "artifacts" / "oracle_creation", ROOT / "artifacts" / "exchange_sweeps", ROOT / "artifacts" / "session_keys", ROOT / "artifacts" / "tokenomics", ROOT / "artifacts" / "staking", ROOT / "artifacts" / "paper_token", ROOT / "artifacts" / "session_creation", ROOT / "artifacts" / "exchange_core_withdrawal", ROOT / "artifacts" / "exchange_getters", ROOT / "artifacts" / "exchange_batch_thresholds")
manifest = json.loads((ATLAS / "manifest.json").read_text())
recent = json.loads((ATLAS / "event_catalog.json").read_text())["events"]
known = {x["topic0"]: x["public_signature_candidates"] for x in recent}
previous_catalog = ATLAS / "historical_event_catalog.json"
if previous_catalog.exists():
    for event in json.loads(previous_catalog.read_text()).get("events", []):
        known.setdefault(event["topic0"], event.get("public_signature_candidates", []))
reconstructed = {}
for filename, address_key in (("timelock_behavior.json", "timelock"), ("proxy_admin_behavior.json", "address"), ("multisig_behavior.json", "address"), ("batch_executor_behavior.json", "address"), ("batch_control_behavior.json", "address"), ("exchange_interface_evidence.json", "address"), ("exchange_pause_behavior.json", "exchange_proxy"), ("exchange_sweep_behavior.json", "address"), ("exchange_batch_summary_behavior.json", "exchange_proxy"), ("exchange_staker_fee_push_behavior.json", "exchange_proxy"), ("exchange_report_names_behavior.json", "exchange_proxy"), ("exchange_side_bucket_behavior.json", "exchange_proxy"), ("exchange_core_withdrawal_behavior.json", "exchange_proxy"), ("exchange_queue_layout_behavior.json", "exchange_proxy"), ("exchange_queue_harvest_behavior.json", "exchange_proxy"), ("exchange_admin_setters_behavior.json", "exchange_proxy"), ("exchange_dev_fee_claim_behavior.json", "exchange_proxy"), ("session_key_behavior.json", "address"), ("session_initializer_behavior.json", "session_proxy"), ("oracle_behavior.json", "oracle_proxy"), ("staking_behavior.json", "staking_proxy"), ("paper_token_behavior.json", "token_proxy"), ("tokenomics_paper_admin_behavior.json", "tokenomics_proxy"), ("tokenomics_owner_transfer_behavior.json", "tokenomics_proxy"), ("tokenomics_observed_paths.json", "tokenomics_proxy")):
    path = ATLAS / filename
    if path.exists():
        behavior = json.loads(path.read_text())
        for event in behavior.get("event_catalog", []):
            if event.get("reconstructed_signature"):
                reconstructed[(behavior[address_key], event["topic0"])] = event["reconstructed_signature"]
factory = ATLAS / "factory_behavior.json"
if factory.exists():
    behavior = json.loads(factory.read_text())
    for signature, topic in behavior["event_signatures"].items():
        reconstructed[(behavior["factory_proxy"], topic)] = signature
for (_, topic) in reconstructed:
    known.setdefault(topic, [])
grouped = collections.defaultdict(list)
receipt_paths = list(TRACES.glob("*.receipt.json"))
for directory in EXTRA_RECEIPTS:
    receipt_paths.extend(directory.glob("*.receipt.json"))
seen_receipts = set()
for path in receipt_paths:
    receipt = json.loads(path.read_text())
    if receipt["transactionHash"] in seen_receipts:
        continue
    seen_receipts.add(receipt["transactionHash"])
    for log in receipt.get("logs", []):
        if log.get("topics"):
            grouped[(log["address"].lower(), log["topics"][0].lower())].append({"tx": receipt["transactionHash"],
                "block": int(receipt["blockNumber"], 16), "topic_count": len(log["topics"]),
                "data_bytes": (len(log["data"]) - 2) // 2})
rows = []
for (address, topic), samples in sorted(grouped.items()):
    if topic not in known:
        run = subprocess.run(["cast", "4byte-event", "--json", topic], capture_output=True, text=True, timeout=30)
        try:
            known[topic] = json.loads(run.stdout).get("data") or []
        except json.JSONDecodeError:
            known[topic] = []
        time.sleep(0.1)
    rows.append({"emitter": address, "role": manifest["contracts"].get(address, {}).get("role", "external_or_system"),
                 "topic0": topic, "count_in_saved_receipts": len(samples), "samples": samples[:3],
                 "public_signature_candidates": known[topic], "reconstructed_signature": reconstructed.get((address, topic)),
                 "also_seen_last_256_blocks": any(x["emitter"] == address and x["topic0"] == topic for x in recent)})
(ATLAS / "historical_event_catalog.json").write_text(json.dumps({"saved_receipt_count": len(seen_receipts), "events": rows}, indent=2) + "\n")
print(len(rows), "emitter-topic pairs", sum(not x["also_seen_last_256_blocks"] for x in rows), "not in recent window")
