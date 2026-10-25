#!/usr/bin/env python3
"""Attach public event and error candidates to the pinned atlas."""

import json
import pathlib
import subprocess
import time

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
event_catalog = json.loads((ATLAS / "event_catalog.json").read_text())
observed_reverts_path = ATLAS / "observed_reverts.json"
observed_reverts = json.loads(observed_reverts_path.read_text())["reverts"] if observed_reverts_path.exists() else []
registry_path = ROOT / "artifacts" / "openchain_unverified_error_lookup.json"
registry = json.loads(registry_path.read_text())
assert registry["response"]["ok"]
registry_rows = registry["response"]["result"]["function"]
assert set(registry_rows) == set(registry["selectors"])
registry_names = {selector: [row["name"] for row in entries or []]
                  for selector, entries in registry_rows.items()}
assert all("0x" + Keccak()(name.encode())[:4].hex() == selector
           for selector, names in registry_names.items() for name in names)
branch_verified_registry_names = {
    ("exchange_implementation", "0x0d240815"): ("MarketAlreadyPaused()", "testMarketPauseRepeat"),
    ("exchange_implementation", "0x49199fb6"): ("NotPauseAuthority()", "testOutsiderPause"),
    ("exchange_implementation", "0x28ef4314"): ("SweepAlreadyPending()", "testOwnerReconcilePendingRejected"),
    ("exchange_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "testInitializedCall"),
    ("exchange_implementation", "0x6a426315"): ("UnsupportedCollateralDecimals()", "testFreshNineteenDecimals"),
    ("oracle_implementation", "0x30cd7471"): ("NotOwner()", "transfer_owner_outsider"),
    ("tokenomics_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "tokenomics-admin"),
    ("session_key_manager_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "session-initialized"),
    ("deposit_proxy_factory_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "three_address_initializer_current"),
    ("deposit_proxy_factory_implementation", "0x30cd7471"): ("NotOwner()", "set_deployer_outsider"),
    ("timelock", "0x30cd7471"): ("NotOwner()", "batch_probe.schedule_outsider_at_pin"),
}
simulated_probes_by_role = {}
for role, filename in (("timelock", "timelock_behavior.json"), ("proxy_admin", "proxy_admin_behavior.json"), ("one_of_two_multisig", "multisig_behavior.json"), ("batch_executor_implementation", "batch_control_behavior.json"), ("deposit_proxy_factory_implementation", "factory_behavior.json"), ("exchange_implementation", "exchange_sweep_behavior.json"), ("exchange_implementation", "exchange_sweep_recovery_behavior.json"), ("exchange_implementation", "exchange_pause_behavior.json"), ("exchange_implementation", "exchange_liquidation_behavior.json"), ("exchange_implementation", "exchange_market_fields_behavior.json"), ("exchange_implementation", "exchange_initializer_behavior.json"), ("exchange_implementation", "exchange_instrument_creation_behavior.json"), ("exchange_implementation", "exchange_instrument_admin_behavior.json"), ("exchange_implementation", "exchange_fee_rates_behavior.json"), ("exchange_implementation", "exchange_direct_withdrawal_behavior.json"), ("exchange_implementation", "exchange_disabled_selector_behavior.json"), ("exchange_implementation", "exchange_dev_fee_claim_behavior.json"), ("exchange_linked_library_live", "exchange_library_queue_merge_behavior.json"), ("exchange_linked_library_live", "exchange_library_queue_interleaved_behavior.json"), ("session_key_manager_implementation", "session_key_behavior.json"), ("session_key_manager_implementation", "session_signer_branches_behavior.json"), ("session_key_manager_implementation", "session_initializer_behavior.json"), ("staking_implementation", "staking_initializers_behavior.json"), ("tokenomics_implementation", "tokenomics_initializer_behavior.json"), ("user_deposit_proxy_representative", "deposit_proxy_behavior.json"), ("oracle_implementation", "oracle_behavior.json"), ("tokenomics_implementation", "tokenomics_observed_paths.json"), ("tokenomics_implementation", "tokenomics_params_behavior.json"), ("paper_token_implementation", "paper_token_behavior.json")):
    path = ATLAS / filename
    if path.exists():
        role_probes = simulated_probes_by_role.setdefault(role, {})
        for probe in json.loads(path.read_text()).get("simulated_error_catalog", []):
            selector = probe["selector"]
            row = role_probes.setdefault(selector, {"selector": selector, "probe_paths": [],
                                                    "public_signature_candidates": []})
            row["probe_paths"].extend(f"{filename}:{path}" for path in probe["probe_paths"])
            for candidate in probe.get("public_signature_candidates", []):
                if candidate not in row["public_signature_candidates"]:
                    row["public_signature_candidates"].append(candidate)
            signature = probe.get("reconstructed_signature")
            if signature:
                assert not row.get("reconstructed_signature") or row["reconstructed_signature"] == signature
                row["reconstructed_signature"] = signature
batch_error_behavior = json.loads((ATLAS / "batch_executor_behavior.json").read_text())
batch_error_probes = simulated_probes_by_role.setdefault("batch_executor_implementation", {})
for probe in batch_error_behavior["error_catalog"]:
    selector = probe["selector"]
    assert selector not in batch_error_probes
    batch_error_probes[selector] = {
        "selector": selector,
        "probe_paths": ["batch_executor_behavior.json:" + batch_error_behavior["read_only_probe_artifact"]],
        "public_signature_candidates": [],
        "reconstructed_signature": probe["reconstructed_signature"],
    }
reconstructed_events = {}
for filename, address_key in (("timelock_behavior.json", "timelock"), ("proxy_admin_behavior.json", "address"), ("multisig_behavior.json", "address"), ("batch_executor_behavior.json", "address"), ("batch_control_behavior.json", "address"), ("exchange_interface_evidence.json", "address"), ("exchange_pause_behavior.json", "exchange_proxy"), ("exchange_sweep_behavior.json", "address"), ("exchange_batch_summary_behavior.json", "exchange_proxy"), ("exchange_staker_fee_push_behavior.json", "exchange_proxy"), ("exchange_report_names_behavior.json", "exchange_proxy"), ("exchange_side_bucket_behavior.json", "exchange_proxy"), ("exchange_core_withdrawal_behavior.json", "exchange_proxy"), ("exchange_fee_rates_behavior.json", "exchange_proxy"), ("exchange_queue_layout_behavior.json", "exchange_proxy"), ("exchange_admin_setters_behavior.json", "exchange_proxy"), ("exchange_dev_fee_claim_behavior.json", "exchange_proxy"), ("session_key_behavior.json", "address"), ("deposit_proxy_behavior.json", "address"), ("oracle_behavior.json", "oracle_proxy"), ("staking_behavior.json", "staking_proxy"), ("paper_token_behavior.json", "token_proxy"), ("tokenomics_params_behavior.json", "tokenomics_proxy"), ("tokenomics_paper_admin_behavior.json", "tokenomics_proxy"), ("tokenomics_observed_paths.json", "tokenomics_proxy")):
    path = ATLAS / filename
    if not path.exists():
        continue
    behavior = json.loads(path.read_text())
    for event in behavior.get("event_catalog", []):
        signature = event.get("reconstructed_signature")
        if signature:
            topic = subprocess.run(["cast", "keccak", signature], capture_output=True, text=True, check=True).stdout.strip().lower()
            assert topic == event["topic0"].lower()
            reconstructed_events[(behavior[address_key].lower(), topic)] = signature

topics = sorted({event["topic0"] for event in event_catalog["events"]})
matches = {event["topic0"]: event["public_signature_candidates"] for event in event_catalog["events"] if "public_signature_candidates" in event}
for topic in topics:
    if topic in matches:
        continue
    run = subprocess.run(["cast", "4byte-event", "--json", topic], capture_output=True, text=True, timeout=30)
    try:
        value = json.loads(run.stdout)
        matches[topic] = value.get("data") or []
    except json.JSONDecodeError:
        matches[topic] = []
    print(topic[:10], matches[topic], flush=True)
    time.sleep(0.1)
for event in event_catalog["events"]:
    event["public_signature_candidates"] = matches[event["topic0"]]
    event["reconstructed_signature"] = reconstructed_events.get((event["emitter"].lower(), event["topic0"].lower()))
(ATLAS / "event_catalog.json").write_text(json.dumps(event_catalog, indent=2) + "\n")

errors = {}
static_events = {}
for address, contract in manifest["contracts"].items():
    role = contract["role"]
    if role.endswith("_proxy"):
        continue
    abi_path = ATLAS / "decompiled" / f"{role}_sol-abi.json"
    if not abi_path.exists():
        continue
    abi = json.loads(abi_path.read_text())
    probes = simulated_probes_by_role.get(role, {})
    bytecode = (ATLAS / contract["runtime_file"]).read_text().lower()
    error_rows = []
    event_rows = []
    for item in abi:
        if item.get("type") == "error" and item.get("name", "").startswith("CustomError_"):
            selector = "0x" + item["name"].removeprefix("CustomError_")[-8:]
            observed_count = sum(x["count_in_saved_traces"] for x in observed_reverts if x["role"] == role and x["revert_selector"] == selector)
            simulated_count = len(probes.get(selector, {}).get("probe_paths", []))
            error_rows.append({"selector": selector, "runtime_contains_selector": selector[2:] in bytecode,
                               "observed_revert_count": observed_count, "simulated_revert_probe_count": simulated_count,
                               "public_signature_candidates": probes.get(selector, {}).get("public_signature_candidates", []),
                               **({"reconstructed_signature": probes[selector]["reconstructed_signature"]} if probes.get(selector, {}).get("reconstructed_signature") else {}),
                               "status": "observed_revert_selector" if observed_count else ("simulated_revert_selector" if simulated_count else "unverified_heimdall_candidate")})
        elif item.get("type") == "event" and item.get("name", "").startswith("Event_"):
            topic = "0x" + item["name"].removeprefix("Event_")
            event_rows.append({"topic0": topic, "observed_last_256_blocks": any(x["topic0"] == topic for x in event_catalog["events"]), "status": "unverified_heimdall_candidate"})
    if role in ("user_deposit_proxy_representative", "oracle_implementation", "exchange_implementation", "session_key_manager_implementation", "staking_implementation", "paper_token_implementation", "tokenomics_implementation", "proxy_admin", "batch_executor_implementation"):
        filename = {"user_deposit_proxy_representative": "deposit_proxy_behavior.json",
                    "oracle_implementation": "oracle_behavior.json",
                    "exchange_implementation": "exchange_sweep_behavior.json",
                    "session_key_manager_implementation": "session_key_behavior.json",
                    "staking_implementation": "staking_behavior.json",
                    "paper_token_implementation": "paper_token_behavior.json",
                    "tokenomics_implementation": "tokenomics_params_behavior.json",
                    "proxy_admin": "proxy_admin_behavior.json",
                    "batch_executor_implementation": "batch_executor_behavior.json"}[role]
        reconstructed = json.loads((ATLAS / filename).read_text())
        by_topic = {x["topic0"]: x for x in reconstructed["event_catalog"]}
        if role == "batch_executor_implementation":
            for event in by_topic.values():
                event["status"] = "observed_historical_topic" if event["observed_last_256_blocks"] else "simulated_log_only"
            batch_control = json.loads((ATLAS / "batch_control_behavior.json").read_text())
            for event in batch_control["event_catalog"]:
                by_topic[event["topic0"]] = {**event, "status": "observed_historical_topic"}
        if role == "exchange_implementation":
            pause_controls = json.loads((ATLAS / "exchange_pause_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in pause_controls["event_catalog"]})
            market_fields = json.loads((ATLAS / "exchange_market_fields_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in market_fields["event_catalog"]})
            instrument_admin = json.loads((ATLAS / "exchange_instrument_admin_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in instrument_admin["event_catalog"]})
            fee_rates = json.loads((ATLAS / "exchange_fee_rates_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in fee_rates["event_catalog"]})
            batch_summary = json.loads((ATLAS / "exchange_batch_summary_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in batch_summary["event_catalog"]})
            staker_push = json.loads((ATLAS / "exchange_staker_fee_push_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in staker_push["event_catalog"]})
            admin_setters = json.loads((ATLAS / "exchange_admin_setters_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in admin_setters["event_catalog"]})
            dev_fee_claim = json.loads((ATLAS / "exchange_dev_fee_claim_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in dev_fee_claim["event_catalog"]})
        if role == "tokenomics_implementation":
            paper_admin = json.loads((ATLAS / "tokenomics_paper_admin_behavior.json").read_text())
            by_topic.update({x["topic0"]: x for x in paper_admin["event_catalog"]})
        for row in event_rows:
            if row["topic0"] in by_topic:
                row["status"] = "simulated_log_topic" if by_topic[row["topic0"]]["status"] == "simulated_log_only" else "observed_historical_topic"
                row["reconstructed_signature"] = by_topic[row["topic0"]]["reconstructed_signature"]
        existing_topics = {row["topic0"] for row in event_rows}
        for topic, evidence in by_topic.items():
            if topic not in existing_topics:
                event_rows.append({"topic0": topic,
                                   "observed_last_256_blocks": any(x["topic0"] == topic for x in event_catalog["events"]),
                                   "status": "simulated_log_topic" if evidence["status"] == "simulated_log_only" else "observed_historical_topic",
                                   "reconstructed_signature": evidence["reconstructed_signature"]})
    if role == "exchange_linked_library_live":
        queue_merge = json.loads((ATLAS / "exchange_library_queue_merge_behavior.json").read_text())
        merge_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_merge_local" / "replay.json").read_text())
        assert merge_replay["runtime_hashes"]["Library"] == contract["sha256"]
        merge_reverts = [row for row in merge_replay["local_cases"] if row.get("revert_selector") == "0x5b6d2b7a"]
        interleaved = json.loads((ATLAS / "exchange_library_queue_interleaved_behavior.json").read_text())
        interleaved_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_interleaved_local" / "replay.json").read_text())
        assert interleaved_replay["runtime_hashes"]["Library"] == contract["sha256"]
        interleaved_reverts = [row for row in interleaved_replay["cases"] if row.get("error_selector") == "0x5b6d2b7a"]
        assert len(merge_reverts) == 2 and len(interleaved_reverts) == 3
        assert queue_merge["simulated_error_catalog"][0]["selector"] == interleaved["simulated_error_catalog"][0]["selector"] == "0x5b6d2b7a"
        for error_row in error_rows:
            if error_row["selector"] == "0x5b6d2b7a":
                assert error_row["status"] == "simulated_revert_selector" and error_row["simulated_revert_probe_count"] == 5
                error_row["behavior_evidence"] = "exchange_library_queue_merge_behavior.json"
                error_row["local_replay_evidence"] = "../../artifacts/exchange_library_queue_merge_local/replay.json"
                error_row["additional_behavior_evidence"] = "exchange_library_queue_interleaved_behavior.json"
                error_row["additional_local_replay_evidence"] = "../../artifacts/exchange_library_queue_interleaved_local/replay.json"
        remaining = json.loads((ATLAS / "exchange_library_remaining_behavior.json").read_text())
        topics = set(remaining["event_topics"].values())
        present = {row["topic0"] for row in event_rows}
        for row in event_rows:
            if row["topic0"] in topics:
                row["status"] = "simulated_log_topic"
                if row["topic0"] == remaining["event_topics"]["enqueue"]:
                    row["reconstructed_signature"] = "Enqueued(address,uint256,uint256)"
        for topic in topics - present:
            row = {"topic0": topic, "observed_last_256_blocks": False, "status": "simulated_log_topic"}
            if topic == remaining["event_topics"]["enqueue"]:
                row["reconstructed_signature"] = "Enqueued(address,uint256,uint256)"
            event_rows.append(row)
    if probes:
        existing = {x["selector"] for x in error_rows}
        for selector, probe in probes.items():
            if selector not in existing:
                error_rows.append({"selector": selector, "runtime_contains_selector": selector[2:] in bytecode,
                                   "observed_revert_count": 0, "simulated_revert_probe_count": len(probe["probe_paths"]),
                                   "public_signature_candidates": probe.get("public_signature_candidates", []),
                                   **({"reconstructed_signature": probe["reconstructed_signature"]} if probe.get("reconstructed_signature") else {}),
                                   "status": "simulated_revert_selector"})
    if role == "session_key_manager_implementation":
        for error_row in error_rows:
            if error_row["selector"] == "0xd2dd8531":
                error_row["bytecode_evidence"] = "session_disabled_selector_behavior.json"
                if error_row["status"] == "unverified_heimdall_candidate":
                    error_row["status"] = "bytecode_verified_revert_selector"
    if role == "staking_implementation":
        for error_row in error_rows:
            if error_row["selector"] == "0xa15ce1ba":
                error_row["bytecode_evidence"] = "staking_direct_stubs_behavior.json"
    if role == "exchange_implementation":
        open_limit = json.loads((ATLAS / "exchange_open_limit_full_behavior.json").read_text())
        assert "0x" + Keccak()(open_limit["error_signature"].encode())[:4].hex() == open_limit["raw_error"]
        for error_row in error_rows:
            if error_row["selector"] == open_limit["raw_error"]:
                assert open_limit["cap_revert_count"] == 27 and error_row["runtime_contains_selector"]
                error_row["observed_revert_count"] = open_limit["cap_revert_count"]
                error_row["public_signature_candidates"] = [open_limit["error_signature"]]
                error_row["reconstructed_signature"] = open_limit["error_signature"]
                error_row["signature_source"] = open_limit["error_signature_source"]
                error_row["behavior_evidence"] = "exchange_open_limit_full_behavior.json"
                error_row["status"] = "observed_revert_selector"
            if error_row["selector"] == "0x58f03bf7":
                error_row["bytecode_evidence"] = "exchange_disabled_paths_behavior.json"
                if error_row["status"] == "unverified_heimdall_candidate":
                    error_row["status"] = "bytecode_verified_revert_selector"
    if role == "tokenomics_implementation":
        for error_row in error_rows:
            if error_row["selector"] == "0x32aa90b0":
                error_row["bytecode_evidence"] = "tokenomics_redemption_stub_behavior.json"
                error_row["selector_constructed_in_runtime"] = True
                error_row["additional_bytecode_evidence"] = "tokenomics_seven_word_stub_behavior.json"
    for error_row in error_rows:
        names = registry_names.get(error_row["selector"], [])
        if names:
            existing = error_row["public_signature_candidates"]
            existing.extend(name for name in names if name not in existing)
            error_row["public_registry_evidence"] = "../../artifacts/openchain_unverified_error_lookup.json"
        promotion = branch_verified_registry_names.get((role, error_row["selector"]))
        if promotion:
            signature, path_suffix = promotion
            assert signature in names
            matching_probes = [path for path in probes[error_row["selector"]]["probe_paths"]
                               if path.endswith(":" + path_suffix)]
            assert matching_probes and error_row["simulated_revert_probe_count"] > 0
            assert not error_row.get("reconstructed_signature") or error_row["reconstructed_signature"] == signature
            error_row["reconstructed_signature"] = signature
            error_row["signature_source"] = "artifacts/openchain_unverified_error_lookup.json"
            error_row["behavior_evidence"] = matching_probes[0].split(":", 1)[0]
    errors[address] = {"role": role, "candidates": sorted(error_rows, key=lambda x: x["selector"])}
    static_events[address] = {"role": role, "candidates": sorted(event_rows, key=lambda x: x["topic0"])}
(ATLAS / "error_candidates.json").write_text(json.dumps(errors, indent=2) + "\n")
(ATLAS / "static_event_candidates.json").write_text(json.dumps(static_events, indent=2) + "\n")
