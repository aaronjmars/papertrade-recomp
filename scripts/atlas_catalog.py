#!/usr/bin/env python3
"""Catalog selectors for each distinct pinned Papertrade runtime."""

import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
previous_catalog_path = ATLAS / "selector_catalog.json"
previous_catalog = json.loads(previous_catalog_path.read_text()) if previous_catalog_path.exists() else {}
reconstructions = {}
for filename, address_key in (("timelock_selector_names_behavior.json", "timelock"), ("proxy_admin_behavior.json", "address"), ("shared_proxy_behavior.json", "address"), ("multisig_behavior.json", "address"), ("batch_executor_behavior.json", "address"), ("batch_control_behavior.json", "address"), ("exchange_interface_evidence.json", "address"), ("exchange_pause_behavior.json", "exchange_proxy"), ("exchange_event_paths.json", "address"), ("exchange_sweep_behavior.json", "address"), ("exchange_liquidation_behavior.json", "exchange_proxy"), ("exchange_batch_summary_behavior.json", "exchange_proxy"), ("exchange_staker_fee_push_behavior.json", "exchange_proxy"), ("exchange_report_names_behavior.json", "exchange_proxy"), ("exchange_side_bucket_behavior.json", "exchange_proxy"), ("exchange_core_withdrawal_behavior.json", "exchange_proxy"), ("exchange_staking_credit_behavior.json", "exchange_proxy"), ("exchange_direct_withdrawal_behavior.json", "exchange_proxy"), ("exchange_getters_behavior.json", "exchange_proxy"), ("exchange_direct_getters_behavior.json", "exchange_proxy"), ("exchange_mapping_getters_behavior.json", "exchange_proxy"), ("exchange_admin_setters_behavior.json", "exchange_proxy"), ("exchange_dev_fee_claim_behavior.json", "exchange_proxy"), ("exchange_fee_rates_behavior.json", "exchange_proxy"), ("exchange_small_views_behavior.json", "exchange_proxy"), ("exchange_market_keeper_behavior.json", "exchange_proxy"), ("exchange_instrument_creation_behavior.json", "exchange_proxy"), ("session_key_behavior.json", "address"), ("session_typehash_behavior.json", "session_proxy"), ("session_direct_getters_behavior.json", "session_proxy"), ("session_initializer_behavior.json", "session_proxy"), ("deposit_proxy_behavior.json", "address"), ("oracle_behavior.json", "oracle_proxy"), ("staking_behavior.json", "staking_proxy"), ("staking_getters_behavior.json", "staking_proxy"), ("staking_admin_behavior.json", "staking_proxy"), ("factory_selector_names_behavior.json", "factory_proxy"), ("paper_token_behavior.json", "token_proxy"), ("tokenomics_params_behavior.json", "tokenomics_proxy"), ("tokenomics_direct_getters_behavior.json", "tokenomics_proxy"), ("tokenomics_initializer_behavior.json", "tokenomics_proxy"), ("tokenomics_paper_admin_behavior.json", "tokenomics_proxy"), ("tokenomics_owner_transfer_behavior.json", "tokenomics_proxy"), ("tokenomics_observed_paths.json", "tokenomics_proxy"), ("tokenomics_redemption_stub_behavior.json", "tokenomics_proxy")):
    path = ATLAS / filename
    if path.exists():
        behavior = json.loads(path.read_text())
        reconstructions.setdefault(behavior.get("implementation", behavior[address_key]), {}).update(behavior.get("selector_reconstructions", {}))
guardian_report = json.loads((ATLAS / "guardian_signature_leads.json").read_text())
assert guardian_report["active_selector_match_count"] == 86
guardian_signatures = {(row["address"], row["selector"]): row["signature"]
                       for row in guardian_report["matches"]}
assert len(guardian_signatures) == 86
report_name_leads = {}
report_path = ATLAS / "exchange_report_names_behavior.json"
if report_path.exists():
    report = json.loads(report_path.read_text())
    report_name_leads[report["implementation"]] = (
        report["selector_reconstructions"] | report["additional_exact_hash_name_leads"])
observed_argument_overrides = {}
library_behavior_path = ATLAS / "exchange_library_behavior.json"
if library_behavior_path.exists():
    library_behavior = json.loads(library_behavior_path.read_text())
    reconstructions.setdefault(library_behavior["exchange_parent_implementation"], {}).update(
        library_behavior["exchange_parent_selector_reconstructions"])
    observed_argument_overrides[library_behavior["library"]] = library_behavior["observed_abi_arguments"]
harvest_behavior_path = ATLAS / "exchange_library_harvest_behavior.json"
if harvest_behavior_path.exists():
    harvest_behavior = json.loads(harvest_behavior_path.read_text())
    reconstructions.setdefault(harvest_behavior["exchange_parent_implementation"], {}).update(
        harvest_behavior["exchange_parent_selector_reconstructions"])
LIBRARY_REMAINING_ADDRESS = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
remaining_library_path = ATLAS / "exchange_library_remaining_behavior.json"
if remaining_library_path.exists():
    remaining_library = json.loads(remaining_library_path.read_text())
    observed_argument_overrides.setdefault(remaining_library["library"], {}).update(
        remaining_library["observed_abi_arguments"])
paper_math_path = ATLAS / "paper_math_behavior.json"
if paper_math_path.exists():
    paper_math = json.loads(paper_math_path.read_text())
    observed_argument_overrides[paper_math["library"]] = paper_math["observed_abi_arguments"]
seen = set()
catalog = {}

for address, contract in manifest["contracts"].items():
    if not contract["code_present"] or contract["sha256"] in seen:
        continue
    seen.add(contract["sha256"])
    code = (ATLAS / contract["runtime_file"]).read_text().strip()
    raw = subprocess.run(["cast", "selectors", "--json", code], capture_output=True, text=True, check=True)
    parsed = json.loads(raw.stdout)
    prior = previous_catalog.get(address, {})
    if prior.get("sha256") == contract["sha256"]:
        names = {function["selector"]: function["candidate_signature"]
                 for function in prior["functions"] if function["candidate_signature"]}
    else:
        resolved = subprocess.run(["cast", "selectors", "-r", code], capture_output=True, text=True)
        if resolved.returncode:
            raise RuntimeError(f"cast selector lookup failed for {contract['role']}: "
                               f"{resolved.stderr[:240]}")
        names = {}
        for line in resolved.stdout.splitlines():
            cells = line.split("\t")
            if len(cells) >= 4:
                names[cells[0]] = cells[3].strip()
    functions = []
    for item in parsed["data"]:
        behavior_reconstructed = reconstructions.get(address, {}).get(item["selector"], "")
        guardian_signature = guardian_signatures.get((address, item["selector"]), "")
        assert not behavior_reconstructed or not guardian_signature or behavior_reconstructed == guardian_signature
        reconstructed = behavior_reconstructed or guardian_signature
        mutability = "nonpayable" if contract["role"] == "batch_executor_implementation" and item["selector"] == "0x251fb27d" else item["state_mutability"]
        observed_arguments = observed_argument_overrides.get(address, {}).get(item["selector"])
        exact_arguments = reconstructed.split("(", 1)[1].rsplit(")", 1)[0] if reconstructed else (observed_arguments or item["arguments"])
        functions.append({**item, "arguments": exact_arguments, "cast_inferred_arguments": item["arguments"] if exact_arguments != item["arguments"] else None,
                          "arguments_status": ("local_exact_runtime_amount_word" if address == LIBRARY_REMAINING_ADDRESS and item["selector"] == "0x3f4e3626" else "observed_from_calldata_and_bytecode") if observed_arguments else None,
                          "state_mutability": mutability, "candidate_signature": names.get(item["selector"], ""),
                          "reconstructed_signature": reconstructed,
                          "audit_report_name_lead": report_name_leads.get(address, {}).get(item["selector"]),
                          "guardian_report_signature_evidence": "guardian_signature_leads.json" if guardian_signature else None,
                          "signature_status": "reconstructed_from_bytecode_and_behavior" if behavior_reconstructed else ("hash_matched_guardian_report_and_bytecode_layout" if guardian_signature else ("candidate_from_public_signature_database" if names.get(item["selector"]) else "unresolved"))})
    if contract["role"] == "tokenomics_implementation":
        direct_tokenomics = json.loads((ATLAS / "tokenomics_direct_getters_behavior.json").read_text())
        for function in functions:
            if function["selector"] in ("0x3886cade", "0xe9ed73e9", "0xc16017ca"):
                function["observed_storage_slot"] = 6 if function["selector"] == "0xc16017ca" else 5
                function["behavior_evidence"] = "tokenomics_getter_alias_behavior.json"
            if function["selector"] in direct_tokenomics["selector_reconstructions"]:
                function["behavior_evidence"] = "tokenomics_direct_getters_behavior.json"
            if function["selector"] == "0x7c7df7b4":
                function["minimum_calldata_bytes"] = 228
                function["validated_word_types"] = {"0x04": "address", "0x64": "uint64", "0x84": "uint8"}
                function["arguments_status"] = "cast_inference_incomplete; bytecode requires seven argument words"
    if contract["role"] == "exchange_implementation":
        sweep_behavior = json.loads((ATLAS / "exchange_sweep_behavior.json").read_text())
        direct_getters = json.loads((ATLAS / "exchange_direct_getters_behavior.json").read_text())
        mapping_getters = json.loads((ATLAS / "exchange_mapping_getters_behavior.json").read_text())
        admin_setters = json.loads((ATLAS / "exchange_admin_setters_behavior.json").read_text())
        dev_fee_claim = json.loads((ATLAS / "exchange_dev_fee_claim_behavior.json").read_text())
        liquidation = json.loads((ATLAS / "exchange_liquidation_behavior.json").read_text())
        batch_summary = json.loads((ATLAS / "exchange_batch_summary_behavior.json").read_text())
        for function in functions:
            if function["selector"] in sweep_behavior["selector_reconstructions"]:
                function["behavior_evidence"] = "exchange_sweep_behavior.json"
            if function["selector"] in direct_getters["selector_reconstructions"]:
                function["behavior_evidence"] = "exchange_direct_getters_behavior.json"
            if function["selector"] in mapping_getters["selector_reconstructions"]:
                function["behavior_evidence"] = "exchange_mapping_getters_behavior.json"
            if function["selector"] in admin_setters["selector_reconstructions"]:
                function["behavior_evidence"] = "exchange_admin_setters_behavior.json"
            if function["selector"] in dev_fee_claim["selector_reconstructions"]:
                function["behavior_evidence"] = "exchange_dev_fee_claim_behavior.json"
            if function["selector"] in liquidation["selector_reconstructions"]:
                function["behavior_evidence"] = "exchange_liquidation_behavior.json"
            if function["selector"] in batch_summary["selector_reconstructions"]:
                function["behavior_evidence"] = "exchange_batch_summary_behavior.json"
                function["batch_skip_evidence"] = "exchange_batch_skip_behavior.json"
                function["batch_threshold_evidence"] = "exchange_batch_thresholds_behavior.json"
                function["batch_branch_evidence"] = "exchange_batch_branches_behavior.json"
                function["liquidation_tokenomics_evidence"] = "liquidation_tokenomics_behavior.json"
            if function["selector"] == "0xe53e3de6":
                function["behavior_evidence"] = "exchange_staking_credit_behavior.json"
            if function["selector"] == "0xf728fc98":
                index = json.loads((ATLAS / "exchange_position_index_behavior.json").read_text())
                assert index["selector"] == function["selector"] and index["opening_count"] == 25
                function["behavior_evidence"] = "exchange_position_index_behavior.json"
            if function["selector"] == "0xdc8a47ef":
                instruments = json.loads((ATLAS / "exchange_instruments_getter_behavior.json").read_text())
                assert instruments["selector_reconstructions"][function["selector"]] == "instruments(uint32)"
                function["behavior_evidence"] = "exchange_instruments_getter_behavior.json"
            if function["selector"] == "0xec6783f0":
                open_hashes = json.loads((ATLAS / "session_open_typehash_behavior.json").read_text())
                assert open_hashes["open_selector"] == function["selector"] and open_hashes["session_signer_call_count"] > 0
                function["open_typehash_evidence"] = "session_open_typehash_behavior.json"
                open_limit = json.loads((ATLAS / "exchange_open_limit_full_behavior.json").read_text())
                assert open_limit["selector"] == function["selector"] and open_limit["matched_signed_open_count"] == 57
                function["open_limit_evidence"] = "exchange_open_limit_full_behavior.json"
        base_exchange_behavior_files = (
            ("exchange_market_keeper_behavior.json", "selector_reconstructions"),
            ("exchange_report_names_behavior.json", "selector_reconstructions"),
            ("exchange_small_views_behavior.json", "selector_reconstructions"),
            ("exchange_library_behavior.json", "exchange_parent_selector_reconstructions"),
            ("exchange_getters_behavior.json", "selector_reconstructions"),
            ("exchange_fee_rates_behavior.json", "selector_reconstructions"),
            ("exchange_staker_fee_push_behavior.json", "selector_reconstructions"),
            ("exchange_core_withdrawal_behavior.json", "selector_reconstructions"),
            ("exchange_side_bucket_behavior.json", "selector_reconstructions"),
            ("exchange_library_harvest_behavior.json", "exchange_parent_selector_reconstructions"),
            ("exchange_event_paths.json", "selector_reconstructions"),
            ("exchange_instrument_creation_behavior.json", "selector_reconstructions"),
        )
        for filename, selector_key in base_exchange_behavior_files:
            supported = json.loads((ATLAS / filename).read_text()).get(selector_key, {})
            for function in functions:
                if function["selector"] in supported:
                    function.setdefault("behavior_evidence", filename)
        for function in functions:
            if function["selector"] == "0x48ee5e08":
                function.setdefault("behavior_evidence", "exchange_fee_rates_behavior.json")
                function["close_fee_effect_evidence"] = "exchange_close_fee_effects_behavior.json"
            if function["selector"] == "0xc43fbc8c":
                function.setdefault("behavior_evidence", "exchange_small_views_behavior.json")
            if function["selector"] == "0x5ca4c0ea":
                function.setdefault("behavior_evidence", "exchange_instrument_admin_behavior.json")
    if contract["role"] == "timelock":
        timelock_behavior = json.loads((ATLAS / "timelock_behavior.json").read_text())
        assert timelock_behavior["timelock"] == address
        for function in functions:
            function["behavior_evidence"] = "timelock_behavior.json"
    if contract["role"] == "paper_math_library":
        for function in functions:
            if function["selector"] == "0x7aac24ba":
                function["behavior_evidence"] = "paper_math_behavior.json"
    if contract["role"] == "exchange_linked_library_live":
        for function in functions:
            if function["selector"] == "0x79810ffe":
                function["behavior_evidence"] = "exchange_library_harvest_behavior.json"
    if contract["role"] in ("exchange_implementation", "exchange_linked_library_live"):
        queue_merge = json.loads((ATLAS / "exchange_library_queue_merge_behavior.json").read_text())
        followup = json.loads((ATLAS / "exchange_library_queue_harvest_followup_behavior.json").read_text())
        interleaved = json.loads((ATLAS / "exchange_library_queue_interleaved_behavior.json").read_text())
        count_merge = json.loads((ATLAS / "exchange_library_queue_count_merge_behavior.json").read_text())
        field = "exchange" if contract["role"] == "exchange_implementation" else "library"
        selectors = {row[field] for row in queue_merge["selectors"].values()}
        followup_selectors = selectors | {followup["harvest_selectors"][field]}
        interleaved_selectors = followup_selectors | (
            {interleaved["enqueue_library_selector"]} if field == "library" else set())
        count_merge_selectors = {row[field] for row in count_merge["selectors"].values()}
        for function in functions:
            if function["selector"] in selectors:
                function["queue_merge_evidence"] = "exchange_library_queue_merge_behavior.json"
            if function["selector"] in followup_selectors:
                function["queue_harvest_followup_evidence"] = "exchange_library_queue_harvest_followup_behavior.json"
            if function["selector"] in interleaved_selectors:
                function["queue_interleaved_evidence"] = "exchange_library_queue_interleaved_behavior.json"
            if function["selector"] in count_merge_selectors:
                function["queue_count_merge_evidence"] = "exchange_library_queue_count_merge_behavior.json"
    if contract["role"] == "user_deposit_proxy_representative":
        deposit_behavior = json.loads((ATLAS / "deposit_proxy_behavior.json").read_text())
        for function in functions:
            if function["selector"] in deposit_behavior["selector_reconstructions"]:
                function["behavior_evidence"] = "deposit_proxy_behavior.json"
    if contract["role"] == "deposit_proxy_factory_implementation":
        factory_behavior = json.loads((ATLAS / "factory_behavior.json").read_text())
        factory_names = json.loads((ATLAS / "factory_selector_names_behavior.json").read_text())
        assert factory_behavior["admin_only_uninitialized_path"]["selector"] == "0x0f71c8bc"
        assert all(name in factory_behavior["probes"] for name in
                   ("bootstrap_admin_current", "bootstrap_admin_uninitialized", "set_deployer_owner", "set_deployer_outsider"))
        for function in functions:
            if function["selector"] in factory_names["selector_reconstructions"]:
                function["behavior_evidence"] = "factory_selector_names_behavior.json"
            else:
                function["behavior_evidence"] = "factory_behavior.json"
    if contract["role"] == "staking_implementation":
        staking_getters = json.loads((ATLAS / "staking_getters_behavior.json").read_text())
        staking_admin = json.loads((ATLAS / "staking_admin_behavior.json").read_text())
        staking_initializers = json.loads((ATLAS / "staking_initializers_behavior.json").read_text())
        for function in functions:
            if function["selector"] in staking_initializers["selector_behaviors"]:
                function["behavior_evidence"] = "staking_initializers_behavior.json"
            if function["selector"] in staking_getters["selector_reconstructions"] or function["selector"] == staking_getters["unnamed_packed_getter"]["selector"]:
                function["behavior_evidence"] = "staking_getters_behavior.json"
            if function["selector"] in staking_admin["selector_reconstructions"]:
                function["behavior_evidence"] = "staking_admin_behavior.json"
            if function["selector"] in ("0xa694fc3a", "0x2e17de78", "0x4e71d92d", "0xe4fc6b6d"):
                direct_stubs = json.loads((ATLAS / "staking_direct_stubs_behavior.json").read_text())
                assert function["selector"] in direct_stubs["selector_behaviors"]
                function["behavior_evidence"] = "staking_direct_stubs_behavior.json"
            if function["selector"] == "0x9ccae24e":
                function["behavior_evidence"] = "staking_behavior.json"
            if function["selector"] == "0xf0355460":
                unallocated = json.loads((ATLAS / "staking_unallocated_behavior.json").read_text())
                assert unallocated["selector"] == function["selector"] and unallocated["unallocated_override"] > 0
                function["unallocated_reward_evidence"] = "staking_unallocated_behavior.json"
    if contract["role"] == "tokenomics_implementation":
        tokenomics_initializer = json.loads((ATLAS / "tokenomics_initializer_behavior.json").read_text())
        for function in functions:
            if function["selector"] in tokenomics_initializer["selector_behaviors"]:
                function["behavior_evidence"] = "tokenomics_initializer_behavior.json"
            if function["selector"] == "0x0efdf838":
                function["behavior_evidence"] = "liquidation_tokenomics_behavior.json"
                flag = json.loads((ATLAS / "tokenomics_liquidation_flag_behavior.json").read_text())
                assert flag["selector"] == function["selector"] and flag["positive_opcode_paths_identical"]
                function["liquidation_flag_evidence"] = "tokenomics_liquidation_flag_behavior.json"
            if function["selector"] == "0xf2fde38b":
                owner_transfer = json.loads((ATLAS / "tokenomics_owner_transfer_behavior.json").read_text())
                assert owner_transfer["selector_reconstructions"][function["selector"]] == "transferOwnership(address)"
                function["behavior_evidence"] = "tokenomics_owner_transfer_behavior.json"
    if contract["role"] == "session_key_manager_implementation":
        session_getters = json.loads((ROOT / "artifacts" / "session_keys" / "pinned_session_getters.json").read_text())
        assert session_getters["rows"] and all(row["getter_associated_address"] for row in session_getters["rows"])
        session_initializer = json.loads((ATLAS / "session_initializer_behavior.json").read_text())
        session_getter_names = json.loads((ATLAS / "session_direct_getters_behavior.json").read_text())
        session_typehashes = json.loads((ATLAS / "session_typehash_behavior.json").read_text())
        for function in functions:
            if function["selector"] in session_typehashes["constant_getters"]:
                function["behavior_evidence"] = "session_typehash_behavior.json"
            if function["selector"] == "0x6525a680":
                function["open_typehash_evidence"] = "session_open_typehash_behavior.json"
            if function["selector"] in session_initializer["selector_behaviors"]:
                function["behavior_evidence"] = "session_initializer_behavior.json"
            if function["selector"] in session_getter_names["selector_reconstructions"]:
                function["behavior_evidence"] = "session_direct_getters_behavior.json"
            if function["selector"] == "0xc1e6613d":
                function["behavior_evidence"] = "session_key_behavior.json"
            if function["selector"] == "0x7f608253":
                signer_behavior = json.loads((ATLAS / "session_signer_expanded_behavior.json").read_text())
                assert signer_behavior["selector"] == function["selector"] and signer_behavior["call_count"] == 57
                function["behavior_evidence"] = "session_signer_expanded_behavior.json"
                signer_branches = json.loads((ATLAS / "session_signer_branches_behavior.json").read_text())
                assert signer_branches["selector"] == function["selector"] and signer_branches["probe_count"] == 10
                function["signer_branch_evidence"] = "session_signer_branches_behavior.json"
                function["open_typehash_evidence"] = "session_open_typehash_behavior.json"
            if function["selector"] == "0xd45167d0":
                direct_signer = json.loads((ATLAS / "session_direct_signer_behavior.json").read_text())
                assert direct_signer["selector"] == function["selector"] and direct_signer["historical_call_count"] == 4
                function["behavior_evidence"] = "session_direct_signer_behavior.json"
            if function["selector"] == "0xcf8fbec9":
                session_behavior = json.loads((ATLAS / "session_key_behavior.json").read_text())
                assert session_behavior["selector_reconstructions"]["0xcf8fbec9"] == "setAuthorizedCaller(address)"
                function["behavior_evidence"] = "session_key_behavior.json"
    if contract["role"] == "oracle_implementation":
        oracle_behavior = json.loads((ATLAS / "oracle_behavior.json").read_text())
        for function in functions:
            if function["selector"] in oracle_behavior["unresolved_selector_semantics"]:
                function["behavior_evidence"] = "oracle_behavior.json"
    base_behavior_files = {
        "paper_token_implementation": ("paper_token_behavior.json",),
        "one_of_two_multisig": ("multisig_behavior.json",),
        "oracle_implementation": ("oracle_behavior.json",),
        "session_key_manager_implementation": ("session_key_behavior.json",),
        "staking_implementation": ("staking_behavior.json",),
        "tokenomics_implementation": ("tokenomics_observed_paths.json",
                                       "tokenomics_params_behavior.json",
                                       "tokenomics_paper_admin_behavior.json"),
        "batch_executor_implementation": ("batch_executor_behavior.json",),
        "deposit_proxy_factory_proxy": ("shared_proxy_behavior.json",),
        "proxy_admin": ("proxy_admin_behavior.json",),
    }
    for filename in base_behavior_files.get(contract["role"], ()):
        behavior = json.loads((ATLAS / filename).read_text())
        supported = set(behavior.get("selector_reconstructions", {}))
        for function in functions:
            if function["selector"] in supported:
                function.setdefault("behavior_evidence", filename)
    catalog[address] = {
        "role": contract["role"],
        "sha256": contract["sha256"],
        "runtime_bytes": contract["runtime_bytes"],
        "functions": functions,
        "cast_warnings": parsed.get("warnings", []),
        "same_runtime_addresses": [a for a, c in manifest["contracts"].items() if c.get("sha256") == contract["sha256"]],
    }
    print(contract["role"], len(functions), flush=True)

(ATLAS / "selector_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
print(ATLAS / "selector_catalog.json")
