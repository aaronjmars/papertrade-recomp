#!/usr/bin/env python3
"""Build a conservative evidence ledger for every captured runtime selector."""

import collections
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "selector_evidence_coverage.json"
MARKDOWN_OUT = ATLAS / "selector_coverage.md"


def read(name):
    return json.loads((ATLAS / name).read_text())


def key(role, selector):
    return role, selector


def main():
    manifest = read("manifest.json")
    catalog = read("selector_catalog.json")
    call_graph = read("observed_call_graph.json")
    storage = read("storage_trace_catalog.json")
    unresolved = read("unresolved.json")
    legacy_initializers = read("legacy_initializer_stubs_behavior.json")
    assert len(legacy_initializers["entries"]) == 3
    session_initializer_constants = read("session_initializer_constants_behavior.json")
    assert session_initializer_constants["selector"] == "0x747b8a1c"
    replay = read("replay_comparisons.json")
    fixed_replay = json.loads((ROOT / "artifacts" / "fixed_revert_local" / "replay.json").read_text())
    getter_replay = json.loads((ROOT / "artifacts" / "tokenomics_getter_alias" / "replay.json").read_text())
    proxy_admin_replay = json.loads((ROOT / "artifacts" / "proxy_admin_local" / "replay.json").read_text())
    deposit_proxy_replay = json.loads((ROOT / "artifacts" / "deposit_proxy_local" / "replay.json").read_text())
    assert deposit_proxy_replay["test_count"] == 19
    batch_control_replay = json.loads((ROOT / "artifacts" / "batch_control_local" / "replay.json").read_text())
    batch_control = read("batch_control_behavior.json")
    batch_field4_replay = json.loads((ROOT / "artifacts" / "batch_executor_field4_local" / "replay.json").read_text())
    assert batch_field4_replay["block_hash"] == manifest["block_hash"] and batch_field4_replay["test_count"] == 4
    batch_allowlist_replay = json.loads((ROOT / "artifacts" / "batch_allowlist_local" / "replay.json").read_text())
    assert batch_allowlist_replay["block_hash"] == manifest["block_hash"] and batch_allowlist_replay["accepted_pair_count"] == 8
    exchange_pause_replay = json.loads((ROOT / "artifacts" / "exchange_pause_local" / "replay.json").read_text())
    exchange_pause = read("exchange_pause_behavior.json")
    instrument_limit_replay = json.loads((ROOT / "artifacts" / "exchange_instrument_limit_local" / "replay.json").read_text())
    instrument_limit = read("exchange_instrument_limit_behavior.json")
    instrument_creation_replay = json.loads((ROOT / "artifacts" / "exchange_instrument_creation_local" / "replay.json").read_text())
    instrument_admin_replay = json.loads((ROOT / "artifacts" / "exchange_instrument_admin_local" / "replay.json").read_text())
    exchange_initializer_replay = json.loads((ROOT / "artifacts" / "exchange_initializer_local" / "replay.json").read_text())
    exchange_initializer = read("exchange_initializer_behavior.json")
    adapter_replay = json.loads((ROOT / "artifacts" / "exchange_library_adapters_local" / "replay.json").read_text())
    adapters = read("exchange_library_adapters_behavior.json")
    merge_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_merge_local" / "replay.json").read_text())
    merge_behavior = read("exchange_library_queue_merge_behavior.json")
    followup_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_harvest_followup_local" / "replay.json").read_text())
    followup_behavior = read("exchange_library_queue_harvest_followup_behavior.json")
    interleaved_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_interleaved_local" / "replay.json").read_text())
    interleaved_behavior = read("exchange_library_queue_interleaved_behavior.json")
    count_merge_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_count_merge_local" / "replay.json").read_text())
    count_merge_behavior = read("exchange_library_queue_count_merge_behavior.json")
    remaining_replay = json.loads((ROOT / "artifacts" / "exchange_library_remaining_local" / "replay.json").read_text())
    remaining = read("exchange_library_remaining_behavior.json")
    initializer_replay = json.loads((ROOT / "artifacts" / "remaining_initializers_local" / "replay.json").read_text())
    signed_audit_replay = json.loads((ROOT / "artifacts" / "audit_signed_intent_failures" / "replay.json").read_text())
    assert signed_audit_replay["block_hash"] == manifest["block_hash"] and signed_audit_replay["test_count"] == 26
    initializer_behaviors = {
        "staking_implementation": read("staking_initializers_behavior.json"),
        "session_key_manager_implementation": read("session_initializer_behavior.json"),
        "tokenomics_implementation": read("tokenomics_initializer_behavior.json"),
    }
    assert fixed_replay["block_hash"] == getter_replay["block_hash"] == proxy_admin_replay["block_hash"] == manifest["block_hash"]
    assert proxy_admin_replay["forge_result"] == "10 passed, 0 failed"
    assert batch_control_replay["block_hash"] == manifest["block_hash"] and batch_control_replay["forge_result"] == "10 passed, 0 failed"
    batch_control_selectors = set(batch_control["selector_reconstructions"]) | set(batch_control["simulated_control_selectors"]) | set(batch_control["locally_checked_existing_getters"])
    assert exchange_pause_replay["block_hash"] == manifest["block_hash"] and exchange_pause_replay["forge_result"] == "13 passed, 0 failed"
    exchange_pause_selectors = set(exchange_pause["selector_reconstructions"])
    assert instrument_limit_replay["block_hash"] == manifest["block_hash"] and instrument_limit_replay["forge_result"] == "10 passed, 0 failed"
    instrument_limit_selector = instrument_limit["selector"]
    assert instrument_creation_replay["block_hash"] == manifest["block_hash"] and instrument_creation_replay["test_count"] == 8
    assert instrument_admin_replay["block_hash"] == manifest["block_hash"] and instrument_admin_replay["forge_result"] == "9 passed, 0 failed"
    instrument_admin_selector = instrument_admin_replay["selector"]
    assert exchange_initializer_replay["block_hash"] == manifest["block_hash"] and exchange_initializer_replay["forge_result"] == "6 passed, 0 failed"
    initializer_selector = exchange_initializer["selector"]
    assert adapter_replay["block_hash"] == manifest["block_hash"] and adapter_replay["forge_result"] == "7 passed, 0 failed"
    assert remaining_replay["block_hash"] == manifest["block_hash"] and remaining_replay["forge_result"] == "6 passed, 0 failed"
    remaining_selectors = {key("exchange_linked_library_live", selector) for selector in remaining["selector_behaviors"]}
    assert initializer_replay["block_hash"] == manifest["block_hash"] and initializer_replay["forge_result"] == "7 passed, 0 failed"
    initializer_selectors = {key(role, selector) for role, behavior in initializer_behaviors.items()
                             for selector in behavior["selector_behaviors"]}
    adapter_selectors = {key("exchange_implementation", parent) for parent in adapters["adapters"]} | {
        key("exchange_linked_library_live", child) for child in adapters["adapters"].values()}
    assert merge_replay["block_hash"] == manifest["block_hash"] and merge_replay["forge_result"] == "10 passed, 0 failed"
    merge_selectors = {key("exchange_implementation", row["exchange"]) for row in merge_behavior["selectors"].values()} | {
        key("exchange_linked_library_live", row["library"]) for row in merge_behavior["selectors"].values()}
    assert len(merge_selectors) == 4
    assert followup_replay["block_hash"] == manifest["block_hash"] and followup_replay["forge_result"] == "11 passed, 0 failed"
    followup_selectors = merge_selectors | {
        key("exchange_implementation", followup_behavior["harvest_selectors"]["exchange"]),
        key("exchange_linked_library_live", followup_behavior["harvest_selectors"]["library"])}
    assert len(followup_selectors) == 6
    assert interleaved_replay["block_hash"] == manifest["block_hash"] and interleaved_replay["forge_result"] == "7 passed, 0 failed"
    interleaved_selectors = followup_selectors | {
        key("exchange_linked_library_live", interleaved_behavior["enqueue_library_selector"])}
    assert len(interleaved_selectors) == 7
    assert count_merge_replay["block_hash"] == manifest["block_hash"] and count_merge_replay["forge_result"] == "15 passed, 0 failed"
    count_merge_selectors = {key("exchange_implementation", row["exchange"]) for row in count_merge_behavior["selectors"].values()} | {
        key("exchange_linked_library_live", row["library"]) for row in count_merge_behavior["selectors"].values()}
    assert len(count_merge_selectors) == 4
    by_role = {row["role"]: (address, row) for address, row in catalog.items()}
    assert len(by_role) == len(catalog)
    index = {key(row["role"], fn["selector"]): (address, row, fn)
             for address, row in catalog.items() for fn in row["functions"]}
    assert len(index) == sum(len(row["functions"]) for row in catalog.values())
    assert len(index) == 490
    signed_audit_selectors = {
        key("exchange_implementation", selector) for selector in
        ("0x8d09f23f", "0x2792e706", "0xec6783f0")
    } | {
        key("session_key_manager_implementation", selector) for selector in
        ("0xb002b9fa", "0x7f608253")
    }
    assert len(signed_audit_selectors) == 5 and signed_audit_selectors <= set(index)
    for address, row in catalog.items():
        assert row["sha256"] == manifest["contracts"][address]["sha256"]

    edge_calls = collections.Counter()
    edge_refs = collections.defaultdict(set)
    for edge in call_graph["edges"]:
        for selector, count in edge["selectors"].items():
            item = key(edge["to_role"], selector)
            if item in index:
                edge_calls[item] += count
                edge_refs[item].add("observed_call_graph.json")
    root_txs = collections.defaultdict(set)
    for trace in call_graph["traces"]:
        role = trace["root_role"]
        if role == "user_deposit_proxy":
            role = "user_deposit_proxy_representative"
        item = key(role, trace["root_selector"])
        if item in index:
            root_txs[item].add(trace["hash"])

    view_probes = {}
    for address, row in storage.items():
        for view in row["views"]:
            item = key(row["role"], view["selector"])
            if item in index:
                view_probes[item] = {
                    "success": not view.get("failed", False) and not view.get("error"),
                    "direct_slots": view.get("direct_slots", []),
                    "evidence": "storage_trace_catalog.json",
                }
    unresolved_maps = {name: {key(row["role"], row["selector"]): row for row in unresolved[name]}
                       for name in ("unmatched_selector_candidates", "ambiguous_public_signature_matches",
                                    "state_changing_selectors_without_saved_historical_trace", "fixed_revert_paths",
                                    "bytecode_proven_initializer_stubs")}
    for name, rows in unresolved_maps.items():
        assert len(rows) == len(unresolved[name])
        assert set(rows) <= set(index), name

    replay_txs = collections.defaultdict(set)
    for comparison in replay["comparisons"]:
        target = manifest["contracts"][comparison["to"]]
        implementation = "0x" + target["eip1967_slots"]["implementation"][-40:]
        role = manifest["contracts"][implementation]["role"] if int(implementation, 16) else target["role"]
        item = key(role, comparison["selector"])
        assert item in index, (comparison["tx"], item)
        if comparison["call_skeleton_equal"] and comparison["log_multiset_equal"] and comparison["contract_storage_changes_equal"]:
            replay_txs[item].add(comparison["tx"])
    creation = {
        key("staking_implementation", "0x9ccae24e"): "../../artifacts/staking/deployment.calls.json",
        key("paper_token_implementation", "0x8f15b414"): "../../artifacts/paper_token/deployment.calls.json",
        key("session_key_manager_implementation", "0x747b8a1c"): "../../artifacts/session_creation/0xe055509195f0ea1b9e30c366c3350d10470d8c1d145bfa51686b49134d36ffbe.calls.json",
    }
    for path in creation.values():
        assert (ATLAS / path).exists()

    reconstruction_artifacts = collections.defaultdict(set)
    for path in ATLAS.glob("*.json"):
        behavior = json.loads(path.read_text())
        if not isinstance(behavior, dict):
            continue
        for selector_field, address_field in (("selector_reconstructions", "implementation"),
                                              ("exchange_parent_selector_reconstructions", "exchange_parent_implementation")):
            signatures = behavior.get(selector_field)
            if not isinstance(signatures, dict):
                continue
            address = behavior.get(address_field) or behavior.get("address") or behavior.get("timelock")
            assert address in manifest["contracts"], (path.name, address)
            target = manifest["contracts"][address]
            if target["role"].endswith("_proxy") and behavior.get("runtime_role") != target["role"]:
                implementation = "0x" + target["eip1967_slots"]["implementation"][-40:]
                target = manifest["contracts"][implementation]
            for selector in signatures:
                item = key(target["role"], selector)
                assert item in index, (path.name, item)
                reconstruction_artifacts[item].add(path.name)
    guardian = read("guardian_signature_leads.json")
    assert guardian["active_selector_match_count"] == len(guardian["matches"]) == 86
    for match in guardian["matches"]:
        item = key(match["role"], match["selector"])
        assert item in index and index[item][0] == match["address"]
        assert index[item][2]["reconstructed_signature"] == match["signature"]
        reconstruction_artifacts[item].add("guardian_signature_leads.json")
    fixed = unresolved_maps["fixed_revert_paths"]
    assert {row["selector"]: row["error_selector"] for row in fixed.values()} == fixed_replay["expected_revert_selectors"]
    getter_selectors = {"0x3886cade", "0xe9ed73e9", "0xc16017ca"}
    assert getter_replay["getters_checked"] == len(getter_selectors)

    hypercore_boundary_selectors = {
        key("exchange_implementation", selector) for selector in
        ("0x8d09f23f", "0x7f99545a", "0xe0189108", "0x6d142da1")
    } | {key("oracle_implementation", "0xc0182669"),
         key("user_deposit_proxy_representative", "0x925b3aad")}
    assert hypercore_boundary_selectors <= set(index)

    rows = []
    for (role, selector), (address, contract, fn) in sorted(index.items()):
        item = key(role, selector)
        variant = "variant" in role
        evidence = []
        if edge_calls[item]:
            evidence.append("historical_call_graph_edge")
        if root_txs[item]:
            evidence.append("historical_root_transaction")
        if item in creation:
            evidence.append("saved_creation_trace")
        if item in view_probes:
            evidence.append("saved_view_probe")
        if replay_txs[item]:
            evidence.append("historical_replay_match")
        if item in fixed:
            evidence.append("local_fixed_revert_replay")
        if item in unresolved_maps["bytecode_proven_initializer_stubs"]:
            evidence.append("pinned_bytecode_fixed_revert")
        if role == "tokenomics_implementation" and selector in getter_selectors:
            evidence.append("local_getter_storage_override")
        if role == "proxy_admin":
            evidence.append("local_proxy_admin_replay")
        if role == "deposit_proxy_factory_proxy":
            evidence.append("local_shared_proxy_replay")
        if role == "user_deposit_proxy_representative":
            evidence.append("local_deposit_proxy_replay")
        if role == "batch_executor_implementation" and selector in batch_control_selectors:
            evidence.append("local_batch_control_replay")
        if role == "batch_executor_implementation" and selector == "0x251fb27d":
            evidence.append("local_batch_field4_replay")
            evidence.append("local_batch_allowlist_replay")
        if role == "exchange_implementation" and selector in exchange_pause_selectors:
            evidence.append("local_exchange_pause_replay")
        if role == "exchange_implementation" and selector == instrument_limit_selector:
            evidence.append("local_exchange_instrument_limit_replay")
        if role == "exchange_implementation" and selector == "0xc88bbcf3":
            evidence.append("local_exchange_instrument_creation_replay")
        if role == "exchange_implementation" and selector == instrument_admin_selector:
            evidence.append("local_exchange_instrument_admin_replay")
        if role == "exchange_implementation" and selector == initializer_selector:
            evidence.append("local_exchange_initializer_replay")
        if item in adapter_selectors:
            evidence.append("local_exchange_library_adapter_replay")
        if item in merge_selectors:
            evidence.append("local_exchange_library_queue_merge_replay")
        if item in followup_selectors:
            evidence.append("local_exchange_library_queue_harvest_followup_replay")
        if item in interleaved_selectors:
            evidence.append("local_exchange_library_queue_interleaved_replay")
        if item in count_merge_selectors:
            evidence.append("local_exchange_library_queue_count_merge_replay")
        if item in remaining_selectors:
            evidence.append("local_exchange_library_remaining_replay")
        if item in initializer_selectors:
            evidence.append("local_remaining_initializer_replay")
        if item in hypercore_boundary_selectors:
            evidence.append("saved_hypercore_boundary_calls")
        if item in signed_audit_selectors:
            evidence.append("local_signed_intent_audit_replay")
        if item in {key("exchange_implementation", "0xec6783f0"),
                    key("batch_executor_implementation", "0x251fb27d")}:
            evidence.append("historical_signed_open_full_replay")
        if item in {key("exchange_implementation", "0x2792e706"),
                    key("batch_executor_implementation", "0x251fb27d")}:
            evidence.append("historical_signed_close_full_replay")
        unresolved_context = {}
        for name, mapping in unresolved_maps.items():
            if item in mapping:
                source = mapping[item]
                unresolved_context[name] = {
                    k: v for k, v in source.items()
                    if k.endswith("evidence") or k in ("observed_behavior", "observed_storage_slot",
                                                       "minimum_calldata_bytes", "validated_word_types", "error_selector")}
        artifact_refs = set()
        if fn.get("behavior_evidence"):
            artifact_refs.add(fn["behavior_evidence"])
        if fn.get("signer_branch_evidence"):
            artifact_refs.add(fn["signer_branch_evidence"])
        if fn.get("open_typehash_evidence"):
            artifact_refs.add(fn["open_typehash_evidence"])
        if fn.get("open_limit_evidence"):
            artifact_refs.add(fn["open_limit_evidence"])
        if fn.get("close_fee_effect_evidence"):
            artifact_refs.add(fn["close_fee_effect_evidence"])
        if fn.get("unallocated_reward_evidence"):
            artifact_refs.add(fn["unallocated_reward_evidence"])
        if fn.get("batch_skip_evidence"):
            artifact_refs.add(fn["batch_skip_evidence"])
        if fn.get("batch_threshold_evidence"):
            artifact_refs.add(fn["batch_threshold_evidence"])
        if fn.get("batch_branch_evidence"):
            artifact_refs.add(fn["batch_branch_evidence"])
        if fn.get("liquidation_tokenomics_evidence"):
            artifact_refs.add(fn["liquidation_tokenomics_evidence"])
        if fn.get("liquidation_flag_evidence"):
            artifact_refs.add(fn["liquidation_flag_evidence"])
        if item in unresolved_maps["bytecode_proven_initializer_stubs"]:
            artifact_refs.add("legacy_initializer_stubs_behavior.json")
        if role == "session_key_manager_implementation" and selector == session_initializer_constants["selector"]:
            artifact_refs.add("session_initializer_constants_behavior.json")
        if item in hypercore_boundary_selectors:
            artifact_refs.add("hypercore_boundary_behavior.json")
        if item in signed_audit_selectors:
            artifact_refs.add("../../artifacts/audit_signed_intent_failures/replay.json")
        if item in {key("exchange_implementation", "0xec6783f0"),
                    key("batch_executor_implementation", "0x251fb27d")}:
            artifact_refs.add("../../artifacts/audit_historical_open/replay.json")
        if item in {key("exchange_implementation", "0x2792e706"),
                    key("batch_executor_implementation", "0x251fb27d")}:
            artifact_refs.add("../../artifacts/audit_historical_close/replay.json")
        if item == key("exchange_implementation", "0x8d09f23f"):
            artifact_refs.add("exchange_withdrawal_trace_corpus.json")
            artifact_refs.add("exchange_withdrawal_signature_behavior.json")
        if item == key("exchange_implementation", "0x2792e706"):
            artifact_refs.add("session_close_typehash_behavior.json")
        if role == "user_deposit_proxy_representative":
            artifact_refs.add("../../artifacts/deposit_proxy_local/replay.json")
        if role == "batch_executor_implementation" and selector in batch_control_selectors:
            artifact_refs.add("batch_control_behavior.json")
        if role == "batch_executor_implementation" and selector == "0x251fb27d":
            artifact_refs.add("../../artifacts/batch_executor_field4_local/replay.json")
            artifact_refs.add("../../artifacts/batch_allowlist_local/replay.json")
        if role == "exchange_implementation" and selector in exchange_pause_selectors:
            artifact_refs.add("exchange_pause_behavior.json")
        if role == "exchange_implementation" and selector == "0x6a3214c9":
            artifact_refs.add("exchange_sweep_recovery_behavior.json")
            artifact_refs.add("../../artifacts/audit_sweep_recovery_local/replay.json")
        if role == "exchange_implementation" and selector == instrument_limit_selector:
            artifact_refs.add("exchange_instrument_limit_behavior.json")
        if role == "exchange_implementation" and selector == "0x7f99545a":
            artifact_refs.add("exchange_direct_withdrawal_behavior.json")
        if role == "exchange_implementation" and selector == "0xc88bbcf3":
            artifact_refs.add("exchange_instrument_creation_behavior.json")
            artifact_refs.add("../../artifacts/exchange_instrument_creation_local/replay.json")
        if role == "exchange_implementation" and selector == instrument_admin_selector:
            artifact_refs.add("../../artifacts/exchange_instrument_admin_local/replay.json")
        if role == "exchange_implementation" and selector == initializer_selector:
            artifact_refs.add("exchange_initializer_behavior.json")
        if item in adapter_selectors:
            artifact_refs.add("exchange_library_adapters_behavior.json")
        if item in merge_selectors:
            artifact_refs.add("exchange_library_queue_merge_behavior.json")
            artifact_refs.add("../../artifacts/exchange_library_queue_merge_local/replay.json")
        if item in followup_selectors:
            artifact_refs.add("exchange_library_queue_harvest_followup_behavior.json")
            artifact_refs.add("../../artifacts/exchange_library_queue_harvest_followup_local/replay.json")
        if item in interleaved_selectors:
            artifact_refs.add("exchange_library_queue_interleaved_behavior.json")
            artifact_refs.add("../../artifacts/exchange_library_queue_interleaved_local/replay.json")
        if item in count_merge_selectors:
            artifact_refs.add("exchange_library_queue_count_merge_behavior.json")
            artifact_refs.add("../../artifacts/exchange_library_queue_count_merge_local/replay.json")
        if item in remaining_selectors:
            artifact_refs.add("exchange_library_remaining_behavior.json")
        if item in initializer_selectors:
            artifact_refs.add({"staking_implementation": "staking_initializers_behavior.json",
                               "session_key_manager_implementation": "session_initializer_behavior.json",
                               "tokenomics_implementation": "tokenomics_initializer_behavior.json"}[role])
        for context in unresolved_context.values():
            artifact_refs.update(value for field, value in context.items()
                                 if field.endswith("_evidence") and isinstance(value, str)
                                 and value != "selector_catalog.json")
        for ref in artifact_refs:
            assert (ATLAS / ref).exists(), (item, ref)
        if artifact_refs:
            evidence.append("linked_behavior_artifact")
        if reconstruction_artifacts[item]:
            evidence.append("signature_reconstruction_artifact")
        row = {
            "role": role, "address": address, "selector": selector,
            "runtime_sha256": contract["sha256"], "active_runtime_at_pin": not variant,
            "same_runtime_addresses": contract["same_runtime_addresses"],
            "cast_inferred_arguments": fn.get("cast_inferred_arguments") or fn["arguments"],
            "arguments_status": fn.get("arguments_status"),
            "cast_inferred_mutability": fn["state_mutability"],
            "candidate_signature": fn["candidate_signature"],
            "reconstructed_signature": fn.get("reconstructed_signature", ""),
            "signature_status": fn["signature_status"],
            "indexed_evidence": evidence,
            "historical_edge_call_count": edge_calls[item],
            "historical_root_transaction_count": len(root_txs[item]),
            "historical_replay_match_count": len(replay_txs[item]),
            "saved_view_probe": view_probes.get(item),
            "creation_trace_evidence": creation.get(item),
            "fixed_revert_error_selector": fixed[item]["error_selector"] if item in fixed else None,
            "linked_behavior_artifacts": sorted(artifact_refs),
            "signature_reconstruction_artifacts": sorted(reconstruction_artifacts[item]),
            "unresolved_context": unresolved_context,
            "branch_coverage_status": "not_established_by_this_ledger",
        }
        rows.append(row)
    active = [row for row in rows if row["active_runtime_at_pin"]]
    nonview_untraced = unresolved_maps["state_changing_selectors_without_saved_historical_trace"]
    assert len(nonview_untraced) == 41
    priority = [row for row in active if key(row["role"], row["selector"]) in nonview_untraced]
    assert len(priority) == 41
    gap_artifact = {item: row.get("gap_behavior_evidence", "") for item, row in nonview_untraced.items()}
    assert set(gap_artifact) == {key(row["role"], row["selector"]) for row in priority}
    assert all(gap_artifact.values()), "every untraced nonview row must link a gap behavior artifact"
    summary = {
        "all_captured_runtime_selector_rows": len(rows),
        "active_runtime_selector_rows": len(active),
        "unused_variant_selector_rows": len(rows) - len(active),
        "active_rows_with_saved_historical_call_graph_evidence": sum(
            bool(row["historical_edge_call_count"] or row["historical_root_transaction_count"]) for row in active),
        "active_rows_with_saved_view_probe": sum(row["saved_view_probe"] is not None for row in active),
        "active_rows_with_successful_saved_view_probe": sum(row["saved_view_probe"] is not None and row["saved_view_probe"]["success"] for row in active),
        "active_rows_with_historical_replay_match": sum(bool(row["historical_replay_match_count"]) for row in active),
        "active_rows_with_local_fixed_revert_replay": sum(row["fixed_revert_error_selector"] is not None for row in active),
        "active_rows_with_pinned_bytecode_fixed_revert": sum("pinned_bytecode_fixed_revert" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_proxy_admin_replay": sum("local_proxy_admin_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_shared_proxy_replay": sum("local_shared_proxy_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_deposit_proxy_replay": sum("local_deposit_proxy_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_batch_control_replay": sum("local_batch_control_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_batch_field4_replay": sum("local_batch_field4_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_batch_allowlist_replay": sum("local_batch_allowlist_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_pause_replay": sum("local_exchange_pause_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_instrument_limit_replay": sum("local_exchange_instrument_limit_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_instrument_creation_replay": sum("local_exchange_instrument_creation_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_instrument_admin_replay": sum("local_exchange_instrument_admin_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_initializer_replay": sum("local_exchange_initializer_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_library_adapter_replay": sum("local_exchange_library_adapter_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_library_queue_merge_replay": sum("local_exchange_library_queue_merge_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_library_queue_harvest_followup_replay": sum("local_exchange_library_queue_harvest_followup_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_library_queue_interleaved_replay": sum("local_exchange_library_queue_interleaved_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_library_queue_count_merge_replay": sum("local_exchange_library_queue_count_merge_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_exchange_library_remaining_replay": sum("local_exchange_library_remaining_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_remaining_initializer_replay": sum("local_remaining_initializer_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_local_signed_intent_audit_replay": sum("local_signed_intent_audit_replay" in row["indexed_evidence"] for row in active),
        "active_rows_with_linked_behavior_artifact": sum(bool(row["linked_behavior_artifacts"]) for row in active),
        "active_rows_with_signature_reconstruction_artifact": sum(bool(row["signature_reconstruction_artifacts"]) for row in active),
        "active_untraced_nonview_rows_from_unresolved_inventory": len(priority),
        "active_untraced_nonview_rows_with_linked_behavior_artifact": sum(bool(row["linked_behavior_artifacts"]) for row in priority),
        "active_untraced_nonview_rows_with_gap_behavior_artifact": sum(bool(gap_artifact[key(row["role"], row["selector"])]) for row in priority),
        "active_rows_without_reconstructed_signature": sum(not row["reconstructed_signature"] for row in active),
        "active_rows_without_any_indexed_evidence": sum(not row["indexed_evidence"] for row in active),
    }
    result = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "basis": ["manifest.json", "selector_catalog.json", "observed_call_graph.json",
                  "storage_trace_catalog.json", "replay_comparisons.json", "unresolved.json",
                  "legacy_initializer_stubs_behavior.json",
                  "session_initializer_constants_behavior.json",
                  "../../artifacts/fixed_revert_local/replay.json",
                  "../../artifacts/tokenomics_getter_alias/replay.json",
                  "../../artifacts/proxy_admin_local/replay.json",
                  "../../artifacts/deposit_proxy_local/replay.json",
                  "../../artifacts/batch_control_local/replay.json",
                  "../../artifacts/batch_executor_field4_local/replay.json",
                  "../../artifacts/batch_allowlist_local/replay.json",
                  "../../artifacts/exchange_pause_local/replay.json",
                  "../../artifacts/exchange_instrument_limit_local/replay.json",
                  "../../artifacts/exchange_instrument_creation_local/replay.json",
                  "../../artifacts/exchange_instrument_admin_local/replay.json",
                  "../../artifacts/exchange_initializer_local/replay.json",
                  "../../artifacts/exchange_library_adapters_local/replay.json",
                  "../../artifacts/exchange_library_queue_merge_local/replay.json",
                  "../../artifacts/exchange_library_remaining_local/replay.json",
                  "../../artifacts/remaining_initializers_local/replay.json",
                  "../../artifacts/audit_signed_intent_failures/replay.json"],
        "summary": summary,
        "scope_note": "One row per selector in each distinct runtime of the newest 25-address manifest. Proxy runtimes are deduplicated by hash. Exchange and library variants not installed behind the newest proxies are flagged separately; one Exchange variant is used by an earlier proxy. Evidence flags say what was indexed, not that other evidence does not exist. Historical call counts are sampled. Branch coverage remains unproven unless a separate behavior artifact explicitly checks the path.",
        "priority_untraced_nonview_selectors": [
            {"role": row["role"], "selector": row["selector"],
             "candidate_signature": row["candidate_signature"],
             "reconstructed_signature": row["reconstructed_signature"],
             "linked_behavior_artifacts": row["linked_behavior_artifacts"],
             "signature_reconstruction_artifacts": row["signature_reconstruction_artifacts"],
             "unresolved_context": row["unresolved_context"]}
            for row in priority],
        "rows": rows,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    by_role = collections.defaultdict(list)
    for row in active:
        by_role[row["role"]].append(row)
    md = ["# Selector evidence coverage at block 48,902,346", "",
          "This page is generated by `atlas_selector_coverage.py` from the pinned [machine ledger](selector_evidence_coverage.json). A row means one selector in one distinct captured runtime. Proxy runtimes shared by eight addresses are counted once. The two Exchange implementations and one library not installed behind the newest proxies are shown only in the machine ledger; one Exchange variant is used by an earlier Exchange proxy.", "",
          "## Indexed evidence", "",
          f"- {summary['active_runtime_selector_rows']} active-runtime selector rows across {len(by_role)} distinct runtime families.",
          f"- {summary['active_rows_with_saved_historical_call_graph_evidence']} have saved sampled historical call-graph evidence; {summary['active_rows_with_saved_view_probe']} have saved view probes, including {summary['active_rows_with_saved_view_probe'] - summary['active_rows_with_successful_saved_view_probe']} failed probes.",
          f"- {summary['active_rows_with_linked_behavior_artifact']} have a linked behavior artifact, which does not prove full branch coverage.",
          f"- {summary['active_rows_with_signature_reconstruction_artifact']} have a hash-checked reconstructed signature; {summary['active_rows_with_historical_replay_match']} have a matching sampled historical replay; {summary['active_rows_with_local_fixed_revert_replay']} have a local fixed-revert replay; {summary['active_rows_with_local_proxy_admin_replay']} have ProxyAdmin local replay evidence; {summary['active_rows_with_local_shared_proxy_replay']} have shared-proxy local replay evidence; {summary['active_rows_with_local_deposit_proxy_replay']} have user deposit proxy local replay evidence; {summary['active_rows_with_local_batch_control_replay']} have BatchExecutor control replay evidence; {summary['active_rows_with_local_batch_field4_replay']} have BatchExecutor fourth-field replay evidence; {summary['active_rows_with_local_batch_allowlist_replay']} have BatchExecutor allowlist replay evidence; {summary['active_rows_with_local_exchange_pause_replay']} have Exchange pause replay evidence; {summary['active_rows_with_local_exchange_instrument_limit_replay']} have Exchange instrument field replay evidence; {summary['active_rows_with_local_exchange_instrument_creation_replay']} have Exchange instrument creation replay evidence; {summary['active_rows_with_local_exchange_instrument_admin_replay']} have Exchange instrument administration replay evidence; {summary['active_rows_with_local_exchange_initializer_replay']} have Exchange initializer replay evidence; {summary['active_rows_with_local_exchange_library_adapter_replay']} have Exchange or library adapter replay evidence; {summary['active_rows_with_local_exchange_library_queue_merge_replay']} have queue consolidation replay evidence; {summary['active_rows_with_local_exchange_library_queue_harvest_followup_replay']} have merge-to-harvest replay evidence; {summary['active_rows_with_local_exchange_library_queue_interleaved_replay']} have interleaved-user queue replay evidence; {summary['active_rows_with_local_exchange_library_queue_count_merge_replay']} have count-based consolidation replay evidence; {summary['active_rows_with_local_exchange_library_remaining_replay']} have remaining live-library replay evidence; {summary['active_rows_with_local_remaining_initializer_replay']} have remaining initializer replay evidence.",
          f"- {summary['active_rows_with_local_signed_intent_audit_replay']} active selectors link to the 26-case exact-runtime signed-intent audit replay.",
          f"- {summary['active_rows_with_pinned_bytecode_fixed_revert']} initializer-shaped selectors have a pinned bytecode proof of fixed revert after canonical address decoding.",
          f"- {summary['active_untraced_nonview_rows_from_unresolved_inventory']} nonview selectors lack a saved historical call trace. {summary['active_untraced_nonview_rows_with_linked_behavior_artifact']} of those have an explicit linked behavior artifact in the unresolved inventory, and {summary['active_untraced_nonview_rows_with_gap_behavior_artifact']} now carry an exact-runtime behavior record with recovered calldata shape, caller guard, writes, events and a rejection case; the missing historical call itself remains the open item.",
          "", "These counts overlap. Signature hashes do not prove original source names. A saved call or view probe does not prove every branch. Other simulations can exist without a selector link in this ledger; an empty indexed-evidence list is a documentation gap, not proof that no analysis exists.", "",
          "## By runtime", "",
          "| Runtime role | Selectors | Reconstructed signatures | Saved historical calls | Saved view probes | Fixed reverts | Nonview without historical trace |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for role, role_rows in sorted(by_role.items()):
        md.append("| `" + role + "` | " + " | ".join(str(value) for value in (
            len(role_rows),
            sum(bool(row["reconstructed_signature"]) for row in role_rows),
            sum(bool(row["historical_edge_call_count"] or row["historical_root_transaction_count"]) for row in role_rows),
            sum(row["saved_view_probe"] is not None for row in role_rows),
            sum(row["fixed_revert_error_selector"] is not None for row in role_rows),
            sum("state_changing_selectors_without_saved_historical_trace" in row["unresolved_context"] for row in role_rows),
        )) + " |")
    remaining_index_text = ("Every active selector has at least one indexed evidence link."
                            if summary["active_rows_without_any_indexed_evidence"] == 0 else
                            f"{summary['active_rows_without_any_indexed_evidence']} active selectors still need an indexed probe or artifact link.")
    md += ["", "## Remaining evidence work", "",
           "The machine ledger lists all 41 nonview selectors without saved historical traces and links any indexed behavior artifact. Exchange has 13 of these selectors and its live linked library has 7; both now have an exact-runtime behavior record in [selector_gap_exchange.md](selector_gap_exchange.md). The other 21 rows, including 6 timelock selectors, have theirs in [selector_gap_other.md](selector_gap_other.md). Timelock single and batch paths additionally have read-only simulation evidence in the separate behavior map. The remaining gap for all 41 is a saved historical call, not the behavior record itself. " + remaining_index_text, "",
           "This ledger measures evidence presence, not decompilation completeness. Storage semantics, errors, events, dynamic targets, and branch coverage remain in the contract behavior maps and [unresolved inventory](unresolved.json).", ""]
    MARKDOWN_OUT.write_text("\n".join(md))
    print(summary)


if __name__ == "__main__":
    main()
