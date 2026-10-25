#!/usr/bin/env python3
"""Check internal consistency of the pinned Papertrade atlas artifacts."""

import hashlib
import json
import pathlib

import repo_path  # noqa: F401  makes the recovery package importable

from audit_historical_close_replay import market1_sources
from atlas_exchange_library import pnl_model, settlement_model
from atlas_factory_events import Keccak
from atlas_deployer_scope import verify as verify_deployer_scope
from atlas_suite_sets import verify as verify_suite_sets
from atlas_postpin_pin import verify as verify_postpin_pin
from audit_live2_consolidate import verify as verify_audit_live2
from audit_live2_book_identity import verify as verify_book_identity
from atlas_older_proxy_core import verify as verify_older_proxy_core
from atlas_core_spot_fee_cohort import verify as verify_core_spot_fee_cohort
from atlas_pt01_funding_cohort import verify as verify_pt01_funding_cohort
from atlas_older_evm_assets import verify as verify_older_evm_assets
from atlas_older_withdrawals import verify_logs as verify_older_withdrawal_logs
from atlas_older_withdrawals import verify_core as verify_older_withdrawal_core
from atlas_older_withdrawals import verify_traces as verify_older_withdrawal_traces
from atlas_older_event_census import verify_set as verify_older_event_set
from atlas_older_account_balances import verify_set as verify_older_balance_set
from atlas_older_positions import verify_set as verify_older_position_set
from atlas_older_queue_accounts import verify_set as verify_older_queue_set
from atlas_older_harvest_traces import verify as verify_older_harvest_traces
from atlas_older_exchange_core import verify as verify_older_exchange_core
from atlas_older_exchange_clear import verify as verify_older_exchange_clear
from atlas_older_exchange_variant import verify as verify_older_exchange_variant
from atlas_older_sweep_retry_history import verify as verify_older_sweep_retry_history
from atlas_older_exchange_library import verify as verify_older_exchange_library
from atlas_older_settlement_liquidity import verify as verify_older_settlement_liquidity
from atlas_older_settlement_history import verify as verify_older_settlement_history
from audit_older_queue_close_replay import verify as verify_older_queue_close_replay
from audit_older_replacement_close_replay import verify as verify_older_replacement_close_replay
from atlas_older_exchange_queue import verify as verify_older_exchange_queue
from atlas_older_exchange_queue_replay import verify as verify_older_exchange_queue_replay
from atlas_older_exchange_debt_open import verify as verify_older_exchange_debt_open
from atlas_older_debt_history import verify as verify_older_debt_history
from atlas_older_governance import verify as verify_older_governance
from atlas_older_multisig_control import verify as verify_older_multisig_control
from atlas_older_runtime_links import verify as verify_older_runtime_links
from atlas_older_upgrade import verify as verify_older_upgrade
from atlas_exchange_withdrawal_history import verify as verify_withdrawal_history
from atlas_exchange_withdrawal_census import verify as verify_withdrawal_census
from atlas_hypercore_user_exists import verify as verify_core_user_exists
from atlas_hypercore_boundary import verify as verify_hypercore_boundary
from audit_sweep_settlement import verify as verify_sweep_settlement
from audit_sweep_settlement_stratified import verify as verify_sweep_settlement_stratified
from audit_sweep_accounting_stratified import verify as verify_sweep_accounting_stratified
from atlas_newest_scalar_accounting import verify as verify_newest_scalar_accounting
from atlas_all_suite_claims import verify as verify_all_suite_claims
from atlas_older_fee_claims import verify as verify_older_fee_claims
from atlas_staking_claim_census import verify as verify_staking_claim_census
from atlas_newest_core_assets import verify as verify_newest_core_assets
from atlas_newest_event_census import scan as scan_newest_events
from atlas_newest_account_balances import saved as saved_newest_balances, verify_balances_payload
from audit_sweep_partial_failure_replay import verify as verify_sweep_partial_failure_replay
from audit_sweep_event_census import verify as verify_sweep_event_census
from audit_perp_sweep_settlement import verify as verify_perp_sweep_settlement
from audit_stalled_sweeps import verify as verify_stalled_sweeps
from audit_stalled_precompiles import verify as verify_stalled_precompiles
from audit_corewriter_rejections import verify as verify_corewriter_rejections
from audit_sweep_recovery_local import verify as verify_sweep_recovery_local
from atlas_pt01_governance_replay import verify as verify_pt01_governance_replay
from atlas_pt01_existing_replacement import verify as verify_pt01_existing_replacement
from atlas_pt01_replacement_trade_compat import verify as verify_pt01_replacement_trade_compat
from atlas_pt01_replacement_mixed_compat import verify as verify_pt01_replacement_mixed_compat
from atlas_pt01_replacement_getter_parity import verify as verify_pt01_replacement_getter_parity
from audit_historical_open_tamper import verify as verify_historical_open_tamper
from atlas_pt01_newest_fee_controls import verify as verify_pt01_newest_fee_controls
from atlas_pt01_postpin import LATER_OUT as PT01_LATER_OUT
from atlas_pt01_postpin import CURRENT_OUT as PT01_CURRENT_OUT
from atlas_pt01_postpin import verify as verify_pt01_postpin
from recovery.preflight import verify as verify_pt01_recovery_preflight
from recovery.getter_parity import verify as verify_pt01_recovery_getters
from recovery.plan import verify as verify_pt01_recovery_plan
from recovery.trade_parity import verify as verify_pt01_recovery_trade
from recovery.mixed_parity import verify as verify_pt01_recovery_mixed
from recovery.run_local import verify as verify_pt01_recovery_candidate
from recovery.live_facts import verify as verify_pt01_recovery_live_facts
from audit_withdrawal_settlement import verify as verify_withdrawal_settlement
from audit_withdrawal_settlement_stratified import verify as verify_withdrawal_settlement_stratified
from audit_signed_intent_failures import build_source as build_signed_intent_source
from atlas_exchange_withdrawal_trace_corpus import verify as verify_withdrawal_trace_corpus
from atlas_exchange_withdrawal_signature import verify as verify_withdrawal_signature
from atlas_withdrawal_nonce_history import verify as verify_withdrawal_nonce_history
from atlas_trading_nonce_history import verify as verify_trading_nonce_history
from atlas_paper_control_history import verify as verify_paper_control_history
from atlas_exchange_control_event_history import verify as verify_control_event_history
from atlas_exchange_direct_status_local import source as direct_status_test_source
from atlas_fixed_revert_local import TEST_SOURCE
from atlas_tokenomics_getter_aliases import TEST_SOURCE as TOKENOMICS_GETTER_TEST_SOURCE
from atlas_proxy_admin_local import TEST_SOURCE as PROXY_ADMIN_TEST_SOURCE
from atlas_batch_control_local import TEST_SOURCE as BATCH_CONTROL_TEST_SOURCE
from atlas_batch_executor_field4_local import source as batch_field4_test_source
from atlas_batch_allowlist_local import candidates as batch_allowlist_candidates, source as batch_allowlist_test_source, TARGETS as BATCH_ALLOWLIST_TARGETS
from atlas_exchange_pause_local import TEST_SOURCE as EXCHANGE_PAUSE_TEST_SOURCE
from atlas_exchange_instrument_limit_local import TEST_SOURCE as EXCHANGE_INSTRUMENT_LIMIT_TEST_SOURCE
from atlas_exchange_instrument_creation_local import source as instrument_creation_test_source
from atlas_exchange_initializer_local import TEST_SOURCE as EXCHANGE_INITIALIZER_TEST_SOURCE
from atlas_exchange_library_adapters_local import TEST_SOURCE as EXCHANGE_ADAPTERS_TEST_SOURCE
from atlas_exchange_library_remaining_local import TEST_SOURCE as EXCHANGE_LIBRARY_REMAINING_TEST_SOURCE
from atlas_remaining_initializers_local import TEST_SOURCE as REMAINING_INITIALIZERS_TEST_SOURCE
from atlas_deposit_proxy_local import SOURCE as DEPOSIT_PROXY_LOCAL_SOURCE
from atlas_exchange_library_harvest import build as build_library_harvest
from atlas_exchange_staking_credit import build as build_staking_credit
from atlas_paper_math import build as build_paper_math
from atlas_staking_getters import build as build_staking_getters
from atlas_staking_admin import build as build_staking_admin
from atlas_exchange_direct_getters import build as build_exchange_direct_getters
from atlas_factory_names import build as build_factory_names
from atlas_tokenomics_getters import build as build_tokenomics_getters
from atlas_session_getters import build as build_session_getters
from atlas_session_direct_signer import build as build_session_direct_signer
from atlas_session_signer_expanded import build as build_session_signer_expanded
from atlas_session_signer_branches import build as build_session_signer_branches
from atlas_staking_direct_stubs import build as build_staking_direct_stubs
from atlas_staking_unallocated import build as build_staking_unallocated
from atlas_session_typehashes import build as build_session_typehashes
from atlas_tokenomics_owner_transfer import build as build_tokenomics_owner_transfer
from atlas_exchange_position_index import build as build_exchange_position_index
from atlas_exchange_instruments_getter import build as build_exchange_instruments_getter
from atlas_exchange_mapping_getters import build as build_exchange_mapping_getters
from atlas_exchange_admin_setters import build as build_exchange_admin_setters
from atlas_exchange_dev_fee_claim import build as build_exchange_dev_fee_claim
from atlas_exchange_liquidation import verify as verify_exchange_liquidation
from audit_liquidation_invalid_prices import build as build_liquidation_invalid_prices
from atlas_exchange_batch_summary import verify as verify_exchange_batch_summary
from atlas_exchange_batch_skips import build as build_exchange_batch_skips
from atlas_exchange_batch_thresholds import build as build_exchange_batch_thresholds
from atlas_exchange_batch_branches import build as build_exchange_batch_branches
from atlas_liquidation_tokenomics import build as build_liquidation_tokenomics
from atlas_tokenomics_liquidation_flag import build as build_tokenomics_liquidation_flag
from atlas_deposit_proxy_runtime_derivation import build as build_deposit_proxy_runtime_derivation
from atlas_session_open_typehash import build as build_session_open_typehash
from atlas_session_close_typehash import verify as verify_session_close_typehash
from atlas_exchange_open_limit import build as build_exchange_open_limit
from atlas_exchange_open_limit_full import build as build_exchange_open_limit_full
from atlas_guardian_signature_leads import build as build_guardian_signature_leads
from atlas_public_name_gaps import build as build_public_name_gaps
from atlas_exchange_instrument_admin_local import TEST_SOURCE as EXCHANGE_INSTRUMENT_ADMIN_TEST_SOURCE
from atlas_exchange_library_queue_merge_local import source as exchange_queue_merge_test_source
from atlas_exchange_library_queue_harvest_followup_local import source as exchange_queue_harvest_followup_test_source
from atlas_exchange_library_queue_interleaved_local import source as exchange_queue_interleaved_test_source
from atlas_exchange_library_queue_count_merge_local import source as exchange_queue_count_merge_test_source

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
read = lambda name: json.loads((ATLAS / name).read_text())
manifest = read("manifest.json")
assert manifest["chain_id"] == 999 and manifest["block"] == 48902346
assert manifest["block_hash"] == "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
contracts = manifest["contracts"]
assert len(contracts) == 25
for address, row in contracts.items():
    data = bytes.fromhex((ATLAS / row["runtime_file"]).read_text().strip()[2:])
    assert len(data) == row["runtime_bytes"]
    assert hashlib.sha256(data).hexdigest() == row["sha256"]
    if row["role"].endswith("_proxy"):
        target = "0x" + row["eip1967_slots"]["implementation"][-40:]
        assert target in contracts and contracts[target]["code_present"]

deployer_scope = verify_deployer_scope()
assert deployer_scope["direct_creations"] == 59
assert deployer_scope["older_creations_outside_manifest"] == 38
assert deployer_scope["older_factory_proxy_instances"] == 38
assert deployer_scope["older_runtime_hashes_missing_from_manifest"] == 6
older_proxy_core = verify_older_proxy_core()
assert older_proxy_core["proxy_count"] == 38
assert older_proxy_core["nonzero_spot_proxies"] == 1
older_evm_assets = verify_older_evm_assets()
assert sum(group["accounts"] for group in older_evm_assets["groups"].values()) == 97
assert [row["difference_raw"] for row in older_evm_assets["staking_comparison"]] == [0, 0, 0]
older_withdrawal_logs = verify_older_withdrawal_logs()
assert older_withdrawal_logs["events"] == [27, 6]
older_withdrawal_core = verify_older_withdrawal_core()
assert older_withdrawal_core["matched_transfers"] == 33
older_withdrawal_traces = verify_older_withdrawal_traces()
assert len(older_withdrawal_traces) == 3
older_event_sets = [verify_older_event_set(index) for index in range(2)]
assert [row["logs"] for row in older_event_sets] == [1_216_528, 142_814]
older_balance_sets = [verify_older_balance_set(index) for index in range(2)]
assert [row["unmatched_total_raw"] for row in older_balance_sets] == [0, 0]
assert [row["nonzero_account_count"] for row in older_balance_sets] == [369, 4_208]
older_position_sets = [verify_older_position_set(index) for index in range(2)]
assert [row["active_positions"] for row in older_position_sets] == [20_277, 12]
assert [row["active_storage_checked"] for row in older_position_sets] == [318, 12]
assert [row["queued"] for row in older_position_sets] == [0, 0]
older_queue_sets = [verify_older_queue_set(index) for index in range(2)]
assert [row["enqueue_events"] for row in older_queue_sets] == [8_452, 0]
assert [row["harvest_events"] for row in older_queue_sets] == [8_516, 0]
assert all(row["enqueued_raw"] == row["harvest_paid_raw"] for row in older_queue_sets)
assert [row["total_queued"] for row in older_queue_sets] == [0, 0]
assert all(not any(row["nonzero_user_fields"].values()) for row in older_queue_sets)
older_harvest_traces = verify_older_harvest_traces()
assert [row["harvest_events"] for row in older_harvest_traces] == [1, 2]
assert all(row["paid_raw"] == row["balance_credit_raw"] for row in older_harvest_traces)
older_exchange_core = verify_older_exchange_core()
assert len(older_exchange_core["accounts"]) == 2
older_exchange_clear = verify_older_exchange_clear()
assert older_exchange_clear["test_count"] == 4
older_exchange_variant = verify_older_exchange_variant()
assert older_exchange_variant["test_count"] == 14
assert older_exchange_variant["reserve_raw"] == 100_000_000
older_sweep_retries = verify_older_sweep_retry_history()
core_spot_fee_cohort = verify_core_spot_fee_cohort()
assert core_spot_fee_cohort["proxy_count"] == 38
assert core_spot_fee_cohort["fee_raw_spot_counts"] == {"0": 110, "100000000": 2}
assert [row["delivered_raw_spot"] for row in older_sweep_retries] == [1_050_000_000, 950_000_000]
assert [row["fee_raw_spot"] for row in older_sweep_retries] == [100_000_000, 100_000_000]
assert [row["pinned_residual_raw_spot"] for row in older_sweep_retries] == [0, 100_000_000]
older_exchange_library = verify_older_exchange_library()
older_settlement_liquidity = verify_older_settlement_liquidity()
assert older_settlement_liquidity["local"]["forge_result"] == "9 passed, 0 failed"
assert older_settlement_liquidity["fork"]["forge_result"] == "5 passed, 0 failed"
older_settlement_history = verify_older_settlement_history()
assert older_settlement_history["queued"] == older_settlement_history["profit"] == 903_710_753_436_144
assert older_settlement_history["available"] == 0 and not older_settlement_history["fee_storage_write"]
assert older_settlement_history["existing_global_queue"] > 0
assert older_settlement_history["ungated_lp_available"] > older_settlement_history["existing_global_queue"]
assert older_settlement_history["queue_gate_verified_by_slot_override"] is True
older_queue_close_replay = verify_older_queue_close_replay()
assert older_queue_close_replay["forge_result"] == "1 passed, 0 failed"
assert older_queue_close_replay["receipt_logs_matched"] == 6
assert older_queue_close_replay["post_storage_words_matched"] == 13
older_replacement_close_replay = verify_older_replacement_close_replay()
assert older_replacement_close_replay["forge_result"] == "1 passed, 0 failed"
assert older_replacement_close_replay["receipt_logs_matched"] == 5
assert older_replacement_close_replay["post_storage_words_matched"] == 11
assert older_exchange_library["transaction_count"] == 6
assert older_exchange_library["position_count"] == 24
assert older_exchange_library["local_test_count"] == 5
older_exchange_queue = verify_older_exchange_queue()
assert older_exchange_queue["sampled_positions"] == 136
older_exchange_queue_replay = verify_older_exchange_queue_replay()
older_exchange_debt_open = verify_older_exchange_debt_open()
older_debt_history = verify_older_debt_history()
assert older_debt_history["candidate_transactions"] == 4_611
assert older_debt_history["candidate_opens"] == older_debt_history["matched_use_debt_false"] == 15_689
assert older_debt_history["matched_use_debt_true"] == 0 and not older_debt_history["ambiguous"]
assert older_debt_history["match_multiplicity"] == {1: 15_685, 2: 4}
assert [case["flag"] for case in older_exchange_queue_replay["cases"]] == [0, 1, 2]
older_links = verify_older_runtime_links()
assert older_links["older_direct_novel_runtime_hashes"] == 6
assert len(older_links["equivalent_after_link_or_metadata_normalization"]) == 4
older_governance = verify_older_governance()
assert older_governance["older_multisig_threshold"] == 1
assert len(older_governance["historical_paths"]) == 2
older_multisig_control = verify_older_multisig_control()
assert older_multisig_control["forge_result"] == "2 passed, 0 failed"
assert len(older_multisig_control["addresses"]) == 2
older_upgrade = verify_older_upgrade()
assert older_upgrade["changed_proxy_count"] == 1
assert older_upgrade["upgrade_block"] == 48_092_890

instances = read("deposit_proxy_instances.json")
assert instances["count"] == 22586 == len(instances["instances"])
assert len({x["address"] for x in instances["instances"]}) == instances["count"]
family = read("deposit_proxy_family.json")
assert family["instance_count"] == instances["count"] and family["sample_count"] == 41
assert family["varying_byte_ranges"] == [[903, 923], [998, 1018]]
assert len({x["normalized_sha256"] for x in family["records"]}) == 1
factory_events = read("factory_event_deployments.json")
assert factory_events["event_count"] == factory_events["internal_create2_count"] == instances["count"]
assert factory_events["create2_formula_matches"] == instances["count"]
assert factory_events["event_internal_address_tx_block_matches"] == instances["count"]
assert factory_events["distinct_users"] == instances["count"]
assert factory_events["boundary_overlap_rows"] == 2
factory_map = read("factory_user_proxy_map.json")
assert len(factory_map) == instances["count"]
internal_by_address = {row["address"]: row for row in instances["instances"]}
assert all(internal_by_address[row["proxy"]]["tx"].lower() == row["tx"] and
           internal_by_address[row["proxy"]]["block"] == row["block"] for row in factory_map)
canonical_factory = "\n".join(f"{row['user']}:{row['proxy']}:{row['tx']}" for row in factory_map).encode()
assert hashlib.sha256(canonical_factory).hexdigest() == factory_events["canonical_user_proxy_tx_sha256"]
derived_deposit_runtimes = read("deposit_proxy_runtime_derivation.json")
assert derived_deposit_runtimes == build_deposit_proxy_runtime_derivation()
assert derived_deposit_runtimes["deployment_count"] == instances["count"]
assert derived_deposit_runtimes["fetched_runtime_hash_matches"] == family["sample_count"]
assert derived_deposit_runtimes["directly_fetched_distinct_runtime_count"] == 42
assert derived_deposit_runtimes["additional_unsampled_fetched_runtime_match"]
assert derived_deposit_runtimes["historical_create_output_exact_match"]
exchange_dev_fee_claim = read("exchange_dev_fee_claim_behavior.json")
assert exchange_dev_fee_claim == build_exchange_dev_fee_claim()
assert exchange_dev_fee_claim["selector_reconstructions"] == {"0x88f2aea5": "claimDevFees()"}
assert len(exchange_dev_fee_claim["pinned_case_names"]) == 7
assert next(row for row in read("error_candidates.json")[exchange_dev_fee_claim["implementation"]]["candidates"]
            if row["selector"] == "0x2d016ae6")["reconstructed_signature"] == "NotDevFeeRecipient()"
assert next(row for row in read("selector_evidence_coverage.json")["rows"]
            if row["role"] == "exchange_implementation" and row["selector"] == "0x88f2aea5")["linked_behavior_artifacts"] == ["exchange_dev_fee_claim_behavior.json"]
exchange_admin_setters = read("exchange_admin_setters_behavior.json")
assert exchange_admin_setters == build_exchange_admin_setters()
assert len(exchange_admin_setters["selector_reconstructions"]) == 7
assert len(exchange_admin_setters["event_catalog"]) == 7
assert len(exchange_admin_setters["historical_setter_transactions"]) == 7
assert exchange_admin_setters["owner_zero_success_count"] == 7
assert all(next(row for row in read("historical_event_catalog.json")["events"]
                if row["emitter"] == exchange_admin_setters["exchange_proxy"] and row["topic0"] == event["topic0"])["reconstructed_signature"]
           == event["reconstructed_signature"] for event in exchange_admin_setters["event_catalog"])
exchange_mapping_getters = read("exchange_mapping_getters_behavior.json")
assert exchange_mapping_getters == build_exchange_mapping_getters()
assert len(exchange_mapping_getters["selector_reconstructions"]) == 5
assert len(exchange_mapping_getters["position_samples"]) == 4
assert len(exchange_mapping_getters["queue_samples"]) == 3
assert exchange_mapping_getters["position_override_count"] == 5
session_getters = read("session_direct_getters_behavior.json")
assert session_getters == build_session_getters()
assert len(session_getters["selector_reconstructions"]) == 5
assert len(session_getters["submitter_samples"]) == 2
assert set(session_getters["domain_overrides"]) == {"replace_slot1", "clear_slot3"}
assert session_getters["registration_domain_replay"]["changed_caller_error"] == "InvalidSignature()"
tokenomics_getters = read("tokenomics_direct_getters_behavior.json")
assert tokenomics_getters == build_tokenomics_getters()
assert len(tokenomics_getters["selector_reconstructions"]) == 7
assert len(tokenomics_getters["direct_getter_checks"]) == 7
factory_names = read("factory_selector_names_behavior.json")
assert factory_names == build_factory_names()
assert len(factory_names["selector_reconstructions"]) == 9
assert len(factory_names["deployed_mapping_samples"]) == 3
assert len(factory_names["remaining_unnamed_selectors"]) == 3
factory = read("factory_behavior.json")
assert factory["create2"]["all_recorded_deployments_matched"] == instances["count"]
assert factory["initializer"]["selector"] == "0x56e8d85b"
assert len(factory["probes"]) == 15
assert len(factory["simulated_error_catalog"]) == 8
assert factory["probes"]["deploy_authorized_new"]["success"]
assert factory["probes"]["deploy_owner_new"]["success"]
assert factory["probes"]["deploy_unauthorized_new"]["revert_selector"] == "0x27fba80a"
assert factory["probes"]["bootstrap_admin_current"]["revert_selector"] == "0x3f733c4f"
assert factory["probes"]["bootstrap_admin_uninitialized"]["success"]
factory_error_rows = read("error_candidates.json")["0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0"]["candidates"]
assert len(factory_error_rows) == 8
assert all(x["status"] == "simulated_revert_selector" for x in factory_error_rows)
deposit = read("deposit_proxy_behavior.json")
assert deposit["pin"] == manifest["block"] and deposit["probe_count"] == 17
assert deposit["historical_proxy_normalized_sha256"] == family["normalized_sha256"]
assert deposit["historical_sweep_args"] == [0, 499900000000, 0]
assert deposit["historical_core_writer_log_matches_action"]
assert deposit["selector_reconstructions"]["0x925b3aad"] == "sweepAllToExchange(uint64,uint64,uint64)"
assert len(deposit["event_catalog"]) == len(deposit["simulated_error_catalog"]) == 1
assert deposit["simulated_error_catalog"][0]["reconstructed_signature"] == "CoreAmountOverflow()"
deposit_local = json.loads((ROOT / "artifacts" / "deposit_proxy_local" / "replay.json").read_text())
assert deposit_local["pin"] == manifest["block"] and deposit_local["block_hash"] == manifest["block_hash"]
assert deposit_local["runtime_sha256"] == contracts[deposit_local["address"]]["sha256"]
assert deposit_local["source_sha256"] == hashlib.sha256(DEPOSIT_PROXY_LOCAL_SOURCE.encode()).hexdigest()
assert deposit_local["test_count"] == 19 == len(deposit_local["passed_tests"])
assert {"testRescueBoolMalformed", "testRescueShortReturn", "testWriterRejectsSecondAction"} <= set(deposit_local["passed_tests"])
deposit_errors = read("error_candidates.json")["0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"]["candidates"]
assert deposit_errors[0]["selector"] == "0xfadaa871" and deposit_errors[0]["status"] == "simulated_revert_selector"
deposit_events = read("static_event_candidates.json")["0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"]["candidates"]
assert deposit_events[0]["status"] == "simulated_log_topic"
oracle = read("oracle_behavior.json")
assert oracle["pin"] == manifest["block"] and oracle["block_hash"] == manifest["block_hash"]
assert oracle["pinned_probe_count"] == 20 and oracle["local_replay_count"] == 25
assert oracle["local_replay_source"].startswith("archive-backed Anvil fork")
oracle_forks = read("oracle_fork_comparison.json")
assert oracle_forks["case_count"] == oracle_forks["same_mock_count"] == oracle_forks["same_call_tree_count"] == 25
assert oracle["historical_midpoint_count"] == 20
assert all(x["midpoint"] == (x["bid"] + x["ask"]) // 2 for x in oracle["historical_midpoints"])
assert oracle["snapshot_probe_outputs"]["snapshot_crossed"] == [150, 155, 200, 100, 0]
assert len(oracle["selector_reconstructions"]) == 7 and len(oracle["unresolved_selector_semantics"]) == 2
assert oracle["event_catalog"][0]["reconstructed_signature"] == "OwnerUpdated(address)"
oracle_errors = read("error_candidates.json")["0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a"]["candidates"]
assert all(x["status"] == "simulated_revert_selector" for x in oracle_errors)
sweeps = read("exchange_sweep_behavior.json")
assert sweeps["pin"] == manifest["block"] and sweeps["block_hash"] == manifest["block_hash"]
assert sweeps["sample_count"] == len(sweeps["records"]) == 13
assert sweeps["local_replay_count"] == 24 and sweeps["minimum_request_raw"] == 1000000000
assert sweeps["perp_to_spot_multiplier"] == 100 and sweeps["minimum_perp_only_raw"] == 10000000
assert sweeps["owner_reconcile_credit_scale"] == 10**12
assert sweeps["local_replay_count"] == 24
assert sweeps["local_replay_source"].startswith("archive-backed Anvil fork")
sweep_forks = read("exchange_sweep_fork_comparison.json")
assert sweep_forks["case_count"] == sweep_forks["call_outcome_match_count"] == sweep_forks["ordered_log_match_count"] == 24
assert sweep_forks["storage_delta_match_count"] == 21
assert len(sweep_forks["baseline_differences"]) == 4
assert sweep_forks["minimum_raw"] == {"public": 1000000000, "archive": 1000000000}
assert all(x["perp_raw"] == x["finalize_spot_raw"] == x["finalize_perp_raw"] == 0 for x in sweeps["records"])
assert all(x["credited_internal"] == x["spot_raw"] * 10**10 == x["treasury_delta"] == x["total_balances_delta"] == x["user_balance_delta"] for x in sweeps["records"])
assert len(sweeps["selector_reconstructions"]) == 5 and len(sweeps["event_catalog"]) == 4
assert len(sweeps["simulated_error_catalog"]) == 6
sweep_settlement = verify_sweep_settlement()
assert len(sweep_settlement) == 13 and all(row["matched"] for row in sweep_settlement)
stratified_sweeps = verify_sweep_settlement_stratified()
assert stratified_sweeps["matched"] == 19 and stratified_sweeps["amount_8"] == 404313966855900
stratified_sweep_accounting = verify_sweep_accounting_stratified()
assert stratified_sweep_accounting["matched"] == 19
assert stratified_sweep_accounting["user_credit_18"] == stratified_sweeps["amount_8"] * 10**10
newest_scalar_accounting = verify_newest_scalar_accounting()
assert newest_scalar_accounting["difference_18"] == newest_scalar_accounting["queued_18"] == 0
newest_events = scan_newest_events()
assert newest_events["summary"]["logs"] == 4_301_896
newest_accounts = verify_balances_payload(saved_newest_balances(), newest_events)
assert newest_accounts["candidate_accounts"] == 45_199
assert newest_accounts["nonzero_accounts"] == 17_910
assert newest_accounts["difference_18"] == 0
assert newest_accounts["total_locked_margin_18"] == newest_scalar_accounting["locked_margin_18"]
assert newest_accounts["positions"]["active"] == 3_767
assert newest_accounts["queue"]["total_queued_18"] == 0
all_suite_claims = verify_all_suite_claims()
assert len(all_suite_claims["suites"]) == 3
assert all(suite["queued_18"] == suite["side_bucket_18"] == 0 for suite in all_suite_claims["suites"])
older_fee_claims = verify_older_fee_claims()
assert len(older_fee_claims["rows"]) == 2
for index, row in enumerate(older_fee_claims["rows"]):
    assert row["claim_amount_18"] == all_suite_claims["suites"][index]["dev_fee_18"]
    assert row["staker_fee_push_18"] == all_suite_claims["suites"][index]["staker_fee_18"]
    assert row["staking_reward_credit_tested_raw_units"] == 1
staking_claims = verify_staking_claim_census()
assert staking_claims["candidate_users"] == 14_626
assert staking_claims["sum_pending_rewards_18"] <= staking_claims["reward_reserve_18"]
assert staking_claims["reward_reserve_18"] == all_suite_claims["suites"][2]["staking_exchange_balance_18"]
assert staking_claims["reserve_less_pending_18"] == 31_580
newest_core_assets = verify_newest_core_assets()
assert newest_core_assets["entries"] == 81_842
assert newest_core_assets["pin_second_ledger_entries"] == 0
assert newest_core_assets["postpin_entries"] == 10_519
assert newest_core_assets["core_spot_less_evm_treasury_8"] == 100_000_000
assert newest_core_assets["current_replay_before_observation_8"] == newest_core_assets["current_spot_usdc_8"]
assert newest_core_assets["current_replay_after_observation_8"] == newest_core_assets["current_spot_usdc_8"]
partial_failure_replay = verify_sweep_partial_failure_replay()
assert len(partial_failure_replay["local_cases"]) == 5
assert len(partial_failure_replay["historical_core_rejections"]) == 2
sweep_census = verify_sweep_event_census()
assert sweep_census["counts"] == {"requested": 59027, "swept": 53198, "cleared": 5827}
assert len(sweep_census["nonzero_perp_requests"]) == 75
assert not sweep_census["anomalies"] and len(sweep_census["pending_at_pin"]) == 2
perp_settlement = verify_perp_sweep_settlement()
assert perp_settlement["checked"] == perp_settlement["unique_core_transfers"] == 73
assert perp_settlement["perp_request_outcomes"] == {"credited": 73, "cleared": 2}
assert not perp_settlement["findings"]
stalled_sweeps = verify_stalled_sweeps()
assert len(stalled_sweeps) == 2 and sum(row["pending_raw_spot"] for row in stalled_sweeps) == 6215091600
assert sorted(row["retry_count"] for row in stalled_sweeps) == [28, 5799]
stalled_precompiles = verify_stalled_precompiles()
assert len(stalled_precompiles) == 2 and sum(row["spot_raw"] for row in stalled_precompiles) == 6215091600
core_rejections = verify_corewriter_rejections()
assert [row["rejected_send_executions_in_bounded_history"] for row in core_rejections["cases"]] == [29, 149]
assert len(core_rejections["control_core_tx"]) == 66
newest_fee_controls = verify_pt01_newest_fee_controls()
assert newest_fee_controls["control_first_funding_fee_counts"] == {"1.0": 27}
assert newest_fee_controls["stalled_first_funding_fee_counts"] == {"0.0": 2}
assert newest_fee_controls["all_outgoing_to_exchange_count"] == 84
funding_cohort = verify_pt01_funding_cohort()
assert funding_cohort["proxy_count"] == 67
assert len(funding_cohort["system_first_funding"]) == 4
postpin_pt01 = verify_pt01_postpin()
later_postpin_pt01 = verify_pt01_postpin(PT01_LATER_OUT)
current_postpin_pt01 = verify_pt01_postpin(PT01_CURRENT_OUT)
assert current_postpin_pt01["head_block"] > later_postpin_pt01["head_block"] > postpin_pt01["head_block"]
assert later_postpin_pt01["unchanged_pending"] == current_postpin_pt01["unchanged_pending"] == 2
assert current_postpin_pt01["current_spot_usdc"] == "62.150916"
pt01_recovery_preflight = verify_pt01_recovery_preflight()
assert pt01_recovery_preflight["head_block"] > current_postpin_pt01["head_block"]
assert pt01_recovery_preflight["pending_count"] == 2
assert pt01_recovery_preflight["spot_usdc"] == "62.150916"
pt01_recovery_candidate = verify_pt01_recovery_candidate()
assert pt01_recovery_candidate["forge_result"] == "23 passed, 0 failed"
assert pt01_recovery_candidate["added_selectors"] == ["69f9a5f0", "9d346583", "cbce7532", "d970fad5", "e6ac4a74", "f009ac03"]
pt01_recovery_getters = verify_pt01_recovery_getters()
assert pt01_recovery_getters["matching_successes"] == 72
assert pt01_recovery_getters["removed_selector_still_reverts"] is True
pt01_recovery_trade = verify_pt01_recovery_trade()
assert pt01_recovery_trade["forge_result"] == "4 passed, 0 failed"
assert pt01_recovery_trade["receipt_logs_matched_each"] == 4
assert pt01_recovery_trade["post_storage_words_matched_each"] == 11
assert all(pt01_recovery_trade["archive_matched"].values())
pt01_recovery_mixed = verify_pt01_recovery_mixed()
assert pt01_recovery_mixed["forge_result"] == "2 passed, 0 failed"
# The live implementation emits 10 logs for this archived transaction where the pinned one emitted 17,
# so only the pinned replay reproduces the archive and the candidate reproduces the live behaviour.
assert pt01_recovery_mixed["archive_log_counts"] == {"live": 10, "pinned": 17}
assert pt01_recovery_mixed["archive_matched"]["testPinnedReplayMatchesArchive"] is True
assert pt01_recovery_mixed["archive_matched"]["testLiveReplayMatchesArchive"] is False
pt01_recovery_plan = verify_pt01_recovery_plan()
assert pt01_recovery_plan["operation_count"] == 8
assert pt01_recovery_plan["operation_slots_empty"] == 8
assert pt01_recovery_plan["timelock_delay_seconds"] == 86_400
assert pt01_recovery_plan["pending_governance_slot_occupied"] is True
pt01_recovery_live = verify_pt01_recovery_live_facts()
assert pt01_recovery_live["dispatcher_selectors_old"] == 98 and pt01_recovery_live["dispatcher_selectors_new"] == 103
assert pt01_recovery_live["removed_selectors"] == ["415f1240"]
assert pt01_recovery_live["pending_words_unchanged"] == 2
assert pt01_recovery_live["sweep_logs_since_pin"] == 0
assert pt01_recovery_live["spot_usdc"] == "62.150916"
assert pt01_recovery_live["timelock_min_delay_seconds"] == 86_400
assert postpin_pt01["unchanged_pending"] == 2
assert postpin_pt01["post_pin_sweep_logs"] == 0
assert postpin_pt01["post_pin_core_ledger_entries"] == 0
assert postpin_pt01["current_spot_usdc"] == "62.150916"
sweep_recovery = verify_sweep_recovery_local()
assert sweep_recovery["forge_result"] == "5 passed, 0 failed"
pt01_governance = verify_pt01_governance_replay()
assert pt01_governance["forge_result"] == "2 passed, 0 failed"
assert pt01_governance["earliest_tested_upgrade_timestamp"] == 1_792_533_696
pt01_replacement = verify_pt01_existing_replacement()
assert pt01_replacement["forge_result"] == "8 passed, 0 failed"
assert pt01_replacement["replacement_sent_raw_spot"] == [4_905_091_600, 1_110_000_000]
assert pt01_replacement["conditional_credit_internal"] == [49_050_916 * 10**12, 11_100_000 * 10**12]
pt01_trade_compat = verify_pt01_replacement_trade_compat()
assert pt01_trade_compat["forge_result"] == "2 passed, 0 failed"
assert pt01_trade_compat["receipt_logs_matched_each"] == 4
assert pt01_trade_compat["post_storage_words_matched_each"] == 11
pt01_mixed_compat = verify_pt01_replacement_mixed_compat()
assert pt01_mixed_compat["forge_result"] == "2 passed, 0 failed"
assert pt01_mixed_compat["receipt_logs_matched_each"] == 17
assert pt01_mixed_compat["post_storage_words_matched_each"] == 26
pt01_getter_parity = verify_pt01_replacement_getter_parity()
assert pt01_getter_parity["calls"] == pt01_getter_parity["successful_matching_calls"] == 64
assert pt01_getter_parity["distinct_selectors"] == 57
assert pt01_getter_parity["matching_errors"] == pt01_getter_parity["mismatches"] == 0
withdrawal_settlement = verify_withdrawal_settlement()
assert len(withdrawal_settlement) == 4
assert sorted(row["fee_8"] for row in withdrawal_settlement) == [0, 0, 100000000, 100000000]
withdrawal_settlement_stratified = verify_withdrawal_settlement_stratified()
assert withdrawal_settlement_stratified["pin"] == manifest["block"]
assert withdrawal_settlement_stratified["matched"] == 32
assert withdrawal_settlement_stratified["distinct_with_previous_four"] == 35
assert withdrawal_settlement_stratified["status_fee_counts"] == [
    {"core_user_exists": 0, "fee_8": 100000000, "count": 16},
    {"core_user_exists": 1, "fee_8": 0, "count": 16},
]
assert withdrawal_settlement_stratified["delivered_8"] == 167764005476900
assert withdrawal_settlement_stratified["fee_8"] == 1600000000
assert withdrawal_settlement_stratified["api_amount_precision_cases"] == 1
signed_intent_audit = json.loads((ROOT / "artifacts" / "audit_signed_intent_failures" / "replay.json").read_text())
assert signed_intent_audit["pin"] == manifest["block"] and signed_intent_audit["block_hash"] == manifest["block_hash"]
assert signed_intent_audit["test_count"] == len(set(signed_intent_audit["test_names"])) == 26
assert signed_intent_audit["forge_result"] == "26 passed, 0 failed"
assert signed_intent_audit["source_sha256"] == hashlib.sha256(build_signed_intent_source(
    json.loads((ROOT / "artifacts" / "exchange_direct_status_local" / "pinned_direct_slots.json").read_text())
).encode()).hexdigest()
historical_open_dir = ROOT / "artifacts" / "audit_historical_open"
historical_open = json.loads((historical_open_dir / "replay.json").read_text())
historical_open_tx = historical_open["transaction"]
historical_open_prestate = historical_open_dir / f"{historical_open_tx}.prestate.json"
historical_open_header = json.loads((historical_open_dir / f"{historical_open_tx}.header.json").read_text())
assert historical_open["prestate_sha256"] == hashlib.sha256(historical_open_prestate.read_bytes()).hexdigest()
assert historical_open["block"] == int(historical_open_header["number"], 16)
assert historical_open["block_hash"] == historical_open_header["hash"]
assert historical_open["forge_result"] == "1 passed, 0 failed"
assert historical_open["successful_open_id"] == 1394063
open_tamper = verify_historical_open_tamper()
assert open_tamper["historical_block"] == historical_open["block"]
assert open_tamper["mutations_rejected"] == 8
assert open_tamper["raw_error"] == "0xc5045f22"
assert open_tamper["next_block_replay"] == "rejected"
assert open_tamper["copied_original_key_control"] == "rejected"
assert historical_open["receipt_logs_matched"] == 4
assert historical_open["post_storage_words_matched"] == 11
assert len(historical_open["runtime_sha256"]) == 8
assert all(manifest["contracts"][address]["sha256"] == digest
           for address, digest in historical_open["runtime_sha256"].items())
historical_close = json.loads((ROOT / "artifacts" / "audit_historical_close" / "replay.json").read_text())
assert historical_close["transaction"] == "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5"
assert historical_close["block"] == 48901631
assert historical_close["forge_result"] == "6 passed, 0 failed"
assert historical_close["local_trace_capture"]["command"] == "forge test -vvvv"
assert historical_close["local_trace_capture"]["forge_version"].startswith("forge Version: ")
assert historical_close["local_trace_capture"]["solc_version"].startswith("0.8.")
assert historical_close["receipt_logs_matched"] == 17
assert historical_close["post_storage_words_matched"] == 26
assert historical_close["inner_call_selectors"] == ["0x2792e706", "0x2792e706", "0x8d09f23f", "0x83115825"]
assert historical_close["prestate_sha256"] == hashlib.sha256((
    ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json").read_bytes()).hexdigest()
assert len(historical_close["runtime_sha256"]) == 17
assert all(manifest["contracts"][address]["sha256"] == digest
           for address, digest in historical_close["runtime_sha256"].items()
           if address != "0x3333333333333333333333333333333333333333")
assert historical_close["constructed_four_active_close"]["position_count"] == 4
assert historical_close["mixed_test_sha256"] == hashlib.sha256((
    ROOT / "scripts" / "audit_mixed_four_close.sol.inc").read_bytes()).hexdigest()
mixed_close = historical_close["constructed_four_mixed_pnl_close"]
assert mixed_close["position_count"] == 4
assert mixed_close["gain_template"] == 1392206 and mixed_close["loss_template"] == 1392921
assert mixed_close["orders_tested"] == ["gain_loss_gain_loss", "loss_gain_loss_gain"]
assert all(mixed_close[key] for key in ("same_market", "two_positive_and_two_negative_pnl",
                                        "balance_margin_fee_and_nonce_equations_match"))
cross_market_close = historical_close["constructed_four_cross_market_close"]
assert cross_market_close["position_count"] == 4 and cross_market_close["market_ids"] == [0, 1]
assert cross_market_close["orders_tested"] == ["market0_gain_market1_loss_market0_loss_market1_gain",
                                               "market1_loss_market0_gain_market1_gain_market0_loss"]
assert cross_market_close["mocked_bbo"] == {"0": [808450, 808460], "1": [234895, 234905]}
assert cross_market_close["event_raw_pnl_formula_matches"]
assert cross_market_close["balance_margin_fee_and_nonce_equations_match"]
assert set(cross_market_close["market1_template_sources"]) == {"1394058", "1394060"}
for source in cross_market_close["market1_template_sources"].values():
    assert source["sha256"] == hashlib.sha256((ROOT / source["state_diff"]).read_bytes()).hexdigest()
for prefix in ("market1_config", "market1_fields"):
    assert cross_market_close[prefix + "_sha256"] == hashlib.sha256((
        ROOT / cross_market_close[prefix + "_source"]).read_bytes()).hexdigest()
rendered_mixed = (ROOT / "scripts" / "audit_mixed_four_close.sol.inc").read_text()
replacements, _ = market1_sources(manifest)
for marker, value in replacements.items():
    assert rendered_mixed.count(marker) == 1
    rendered_mixed = rendered_mixed.replace(marker, value)
assert historical_close["cross_market_source_sha256"] == hashlib.sha256(rendered_mixed.encode()).hexdigest()
cross_vectors = cross_market_close["library_math_and_settlement_vectors"]
assert set(cross_vectors) == {"testFourCrossMarketZeroFirstClose",
                             "testFourCrossMarketOneFirstClose"}
for name, expected_markets in (("testFourCrossMarketZeroFirstClose", [0, 1, 0, 1]),
                               ("testFourCrossMarketOneFirstClose", [1, 0, 1, 0])):
    assert len(cross_vectors[name]) == 4
    for i, row in enumerate(cross_vectors[name]):
        math_args = [int(x) for x in row["math_arguments"]]
        math_returns = [int(x) for x in row["math_returns"]]
        settlement_args = [int(x) for x in row["settlement_arguments"]]
        settlement_returns = [int(x) for x in row["settlement_returns"]]
        event = [int(x) for x in row["event_fields"]]
        assert row["position_id"] == i + 1 and row["market_id"] == expected_markets[i]
        assert math_returns == pnl_model(math_args)
        assert settlement_returns == settlement_model(settlement_args)
        assert settlement_args[2:4] == [math_args[2], math_returns[1]]
        assert event[:3] == [math_args[1], *math_returns]
        assert event[4] == settlement_returns[4] + settlement_returns[5]
assert all(historical_close["constructed_four_active_close"][key] for key in
           ("all_active_flags_cleared", "all_four_margins_released",
            "nonce_bit_and_counter_persisted", "four_position_closed_events"))
liquidation = read("exchange_liquidation_behavior.json")
assert liquidation == verify_exchange_liquidation()
assert liquidation["selector_reconstructions"] == {"0x415f1240": "liquidate(uint256)"}
assert liquidation["pin_block"] == manifest["block"]
assert liquidation["sampled_active_positions"] == 4
assert liquidation["single_batch_same_storage_changes"]
assert liquidation["single_batch_same_logs_except_batch_summary"]
assert [(row["position_id"], row["last_success_price"], row["first_success_price"], row["adjacent_failed_price"])
        for row in liquidation["price_boundaries"]] == [
    (1394473, 801811, None, 801812), (1394058, 230425, None, 230426),
    (1394062, 801613, None, 801614), (1394060, None, 242020, 242019)]
assert {row["reconstructed_signature"] for row in liquidation["simulated_error_catalog"]} == {
    "PositionNotOpen()", "NotLiquidatable()"}
invalid_prices = read("exchange_liquidation_invalid_prices.json")
assert invalid_prices == build_liquidation_invalid_prices()
assert invalid_prices["case_count"] == 18 and invalid_prices["invalid_case_count"] == 16
assert all(row["receipt_status"] == "0x0" and row["committed_log_count"] == 0
           and row["watched_exchange_slots_unchanged"] for row in invalid_prices["cases"]
           if row["revert_reason"] is not None)
exchange_library = read("exchange_library_behavior.json")
exchange_event_paths = read("exchange_event_paths.json")
assert exchange_event_paths["selector_reconstructions"] == {
    "0xec6783f0": "openPositionBySig(address,uint32,bool,uint128,uint32,bool,uint256,uint64,uint8,bytes32,bytes32)"}
assert exchange_event_paths["position_opened_matches_return_id"] == 25
assert exchange_event_paths["position_opened_matches_signed_fields"] == 25
assert exchange_event_paths["position_opened_matches_hypercore_midpoint"] == 25
assert all(row["oracle_midpoint"] == (row["hypercore_bid"] + row["hypercore_ask"]) // 2
           for row in exchange_event_paths["pairs"] if row.get("entry_price_matches_hypercore_midpoint"))
assert exchange_library["pin_block"] == manifest["block"]
assert exchange_library["historical_transaction_count"] == 23
assert exchange_library["exchange_parent_selector_reconstructions"] == {
    "0x2792e706": "closeBySig(address,uint256[],uint256,uint64,uint8,bytes32,bytes32)"}
assert exchange_library["signed_close_call_count"] == 43
assert exchange_library["signed_close_position_id_count"] == 49
assert exchange_library["historical_library_call_count"] == 99
assert exchange_library["pnl_call_count"] == exchange_library["settlement_call_count"] == 49
assert exchange_library["other_observed_call_count"] == 1
paper_math = read("paper_math_behavior.json")
assert paper_math == build_paper_math()
assert paper_math["selector"] == "0x7aac24ba" and paper_math["source_name_status"] == "unknown"
assert paper_math["historical_call_count"] == 91 and paper_math["historical_branches"] == {"flat": 1, "tail": 90}
assert paper_math["matched_tokenomics_events"] == paper_math["matched_paper_transfer_mints"] == 91
assert paper_math["prior_read_only_probe_count"] == paper_math["boundary_probe_count"] == 6
assert (ATLAS / "paper_math_pseudocode.md").exists()
harvest_library = read("exchange_library_harvest_behavior.json")
assert harvest_library == build_library_harvest()
assert harvest_library["selector"] == "0x79810ffe" and harvest_library["parent_selector"] == "0xddc63262"
assert harvest_library["exchange_parent_selector_reconstructions"] == {"0xddc63262": "harvest(uint256)"}
parent_harvest_catalog = next(row for row in read("selector_catalog.json")[harvest_library["exchange_parent_implementation"]]["functions"]
                              if row["selector"] == "0xddc63262")
assert parent_harvest_catalog["reconstructed_signature"] == "harvest(uint256)"
assert harvest_library["historical_count"] == 1 and harvest_library["read_only_simulation_count"] == 13
assert len(harvest_library["cases"]) == 14 and all(all(row["checks"].values()) for row in harvest_library["cases"])
assert harvest_library["cases"][0]["returns"] == exchange_library["other_observed_call"]["returns"]
assert all(int(row["returns"][1]) == int(row["arguments"][4]) + int(row["returns"][0])
           for row in harvest_library["cases"])
assert "queue harvest" in exchange_library["selector_behaviors"]["0x79810ffe"]
library_harvest_catalog = next(row for row in read("selector_catalog.json")[harvest_library["library"]]["functions"]
                               if row["selector"] == harvest_library["selector"])
assert library_harvest_catalog["behavior_evidence"] == "exchange_library_harvest_behavior.json"
assert (ATLAS / "exchange_library_harvest.md").exists()
assert exchange_library["pinned_math_probe_count"] == 24
assert exchange_library["settlement_branches"] == {"nonzero_tail_loss": 21,
    "nonzero_tail_profit": 19, "nonzero_tail_flat": 5, "zero_tail_profit": 3, "zero_tail_loss": 1}
assert len(exchange_library["ledger"]) == 49
assert all(all(row["checks"].values()) for row in exchange_library["ledger"])
library_rates = read("exchange_library_fee_rates_behavior.json")
assert library_rates["call_count"] == 36
assert library_rates["calls_by_source"] == {"mixed_gain_loss": 20, "queued_profit": 8, "direct_profit": 8}
assert library_rates["profit_rate_argument_index"] == 5
assert library_rates["loss_rate_argument_index"] == 6
assert library_rates["mixed_slot23_zero_loss_fee"] == "0"
assert library_rates["mixed_slot24_zero_profit_fee"] == "0"
session_typehashes = read("session_typehash_behavior.json")
assert session_typehashes == build_session_typehashes()
assert len(session_typehashes["constant_getters"]) == 3
assert session_typehashes["constant_getters"]["0x6525a680"]["verified_type_string"] == (
    "OpenPosition(address user,uint32 instrumentId,bool isLong,uint128 size,uint32 leverage,bool useDebt,uint256 nonce,uint64 deadline)")
assert set(session_typehashes["selector_reconstructions"]) == {"0x0b4c3a82", "0x208e24fc", "0x6525a680"}
close_typehash = verify_session_close_typehash()
assert close_typehash["matched_close_call_count"] == 43
assert close_typehash["position_id_count"] == 49
assert close_typehash["position_array_length_counts"] == {"1": 38, "2": 4, "3": 1}
open_typehash = read("session_open_typehash_behavior.json")
assert open_typehash == build_session_open_typehash()
verify_trading_nonce_history()
open_limit = read("exchange_open_limit_behavior.json")
assert open_limit == build_exchange_open_limit()
assert [(row["side"], row["exceeds_cap"]) for row in open_limit["samples"]] == [("long", True), ("long", False), ("short", True)]
open_limit_full = read("exchange_open_limit_full_behavior.json")
assert open_limit_full == build_exchange_open_limit_full()
assert (open_limit_full["matched_signed_open_count"], open_limit_full["cap_revert_count"],
        open_limit_full["below_limit_success_count"], open_limit_full["deadline_failure_before_comparison_count"]) == (57, 27, 30, 1)
assert open_limit_full["error_signature"] == "OiCapExceeded()"
assert open_limit_full["error_signature_hash_verified"]
assert open_typehash["open_call_count"] == 58
assert open_typehash["session_signer_call_count"] == 57
assert open_typehash["outcomes"] == {"0x40f92143": 27, "0xf87d9271": 1, "success": 30}
session_direct_signer = read("session_direct_signer_behavior.json")
assert session_direct_signer == build_session_direct_signer()
assert session_direct_signer["historical_call_count"] == 4
assert session_direct_signer["direct_user_match_count"] == 4
assert session_direct_signer["pinned_probe_count"] == 6
assert session_direct_signer["pinned_probes"]["valid_outsider"]["returned_signer"] == session_direct_signer["calls"][0]["user"]
assert session_direct_signer["pinned_probes"]["invalid_v"]["precompile_called"] is False
assert all(session_direct_signer["pinned_probes"][case]["returned_signer"] == "0x" + "0" * 40
           for case in ("invalid_v", "zero_r", "zero_s"))
session = read("session_key_behavior.json")
assert session["pin"] == manifest["block"] and session["block_hash"] == manifest["block_hash"]
assert session["registration_count"] == len(session["registrations"]) == 10
assert session["nonce_call_count"] == len(session["nonce_calls"]) == 19
assert session["historical_signer_call_count"] == len(session["historical_signer_calls"]) == 18
expanded_signer = read("session_signer_expanded_behavior.json")
assert expanded_signer == build_session_signer_expanded()
assert expanded_signer["call_count"] == 57 and expanded_signer["newly_verified_call_count"] == 39
assert expanded_signer["distinct_user_signer_pairs"] == 45
assert all(row["registered_expiry_at_block"] > row["block_timestamp"] for row in expanded_signer["calls"])
signer_branches = read("session_signer_branches_behavior.json")
assert signer_branches == build_session_signer_branches()
assert signer_branches["successful_probe_count"] == 2 and signer_branches["rejected_probe_count"] == 8
assert {row["reconstructed_signature"] for row in signer_branches["simulated_error_catalog"]} == {
    "SessionKeyNotAuthorized()", "SessionKeyExpired()"}
assert {name: row["result"] for name, row in signer_branches["storage_override_probes"].items()} == {
    "expiry_before": "0xda0700a2", "expiry_at": "returned_signer", "expiry_after": "returned_signer",
    "revoked_word_zero": "0xc5045f22", "associated_nonzero": "returned_signer"}
signer_function = next(fn for fn in read("selector_catalog.json")[session["implementation"]]["functions"]
                       if fn["selector"] == "0x7f608253")
assert signer_function["behavior_evidence"] == "session_signer_expanded_behavior.json"
assert signer_function["signer_branch_evidence"] == "session_signer_branches_behavior.json"
assert all(x["registered_expiry_at_block"] > x["block_timestamp"] for x in session["historical_signer_calls"])
assert session["committed_nonce_calls"] == 16 and session["rolled_back_nonce_calls"] == 3
assert sum(x["committed"] for x in session["nonce_calls"]) == 16
assert all(x["recovered_signer"] == x["user"] for x in session["registrations"])
assert len(session["selector_reconstructions"]) == 11
assert len(session["event_catalog"]) == len(session["simulated_error_catalog"]) == 5
tokenomics_owner = read("tokenomics_owner_transfer_behavior.json")
assert tokenomics_owner == build_tokenomics_owner_transfer()
assert tokenomics_owner["storage_slot"] == 0 and tokenomics_owner["owner_bit_offset"] == 16
assert tokenomics_owner["pinned_owner_getter_matches"] is True
assert next(row for row in read("selector_evidence_coverage.json")["rows"]
            if row["active_runtime_at_pin"] and row["role"] == "tokenomics_implementation"
            and row["selector"] == "0xf2fde38b")["linked_behavior_artifacts"] == ["tokenomics_owner_transfer_behavior.json"]
assert next(row for row in read("historical_event_catalog.json")["events"]
            if row["emitter"] == tokenomics_owner["tokenomics_proxy"]
            and row["topic0"] == tokenomics_owner["event_catalog"][0]["topic0"])["reconstructed_signature"] == "OwnerUpdated(address)"
tokenomics = read("tokenomics_observed_paths.json")
liquidation_tokenomics = read("liquidation_tokenomics_behavior.json")
assert liquidation_tokenomics == build_liquidation_tokenomics()
assert liquidation_tokenomics["transaction_count"] == 26
assert liquidation_tokenomics["liquidation_call_count"] == 67
assert liquidation_tokenomics["new_distinct_liquidation_calls"] == 64
assert liquidation_tokenomics["unique_liquidation_calls_across_both_ledgers"] == 70
assert liquidation_tokenomics["storage_reconciled_transaction_count"] == 26
liquidation_flag = read("tokenomics_liquidation_flag_behavior.json")
assert liquidation_flag == build_tokenomics_liquidation_flag()
assert liquidation_flag["positive_opcode_paths_identical"]
assert liquidation_flag["positive_opcode_steps_per_case"] == 1268
params = read("tokenomics_params_behavior.json")
paper_admin = read("tokenomics_paper_admin_behavior.json")
assert paper_admin["storage_slot"] == 2
assert paper_admin["current_value"] == "0xe40f17915daa230324030003a197cdaef2261c0e"
assert paper_admin["probe_count"] == 4 and paper_admin["owner_can_set_zero_at_pin"] is True
assert paper_admin["selector_reconstructions"] == {
    "0x98255e15": "paperToken()", "0xe6ee2285": "setPaperToken(address)"}
assert paper_admin["event_catalog"][0]["reconstructed_signature"] == "PaperTokenUpdated(address)"
assert params["pin_block"] == manifest["block"]
assert params["scheduled_operation_executed_at_pin"] is False
assert params["probe_count"] == 15 and params["excess_getter_floor_probe_count"] == 4
assert params["argument_storage_slots"] == [5, 6, 7, 8]
assert params["selector_reconstructions"]["0x12baae3b"] == "setMintParams(uint256,uint256,uint256,uint256)"
assert params["selector_reconstructions"]["0xae745703"] == "stakerLpDistributableExcessUsd()"
assert params["selector_reconstructions"]["0xc218c676"] == "distributeLpToStakers(uint256)"
assert params["event_catalog"][0]["reconstructed_signature"] == "MintParamsUpdated(uint256,uint256,uint256,uint256)"
assert params["governance_execution"]["success"] is True
assert params["governance_execution"]["nested_tokenomics_event_topic"] == params["event_catalog"][0]["topic0"]
assert int(params["governance_execution"]["timelock_operation_post"], 16) == 1
assert params["downstream_mint_probes"]["count"] == 4
assert params["downstream_mint_probes"]["mint_amounts"]["baseline"] == params["downstream_mint_probes"]["mint_amounts"]["scheduled_floor"]
assert {row["reconstructed_signature"] for row in params["simulated_error_catalog"]} == {
    "InvalidMintParams()", "NotOwner()"}
assert tokenomics["pin_block"] == manifest["block"]
assert tokenomics["transaction_count"] == len(tokenomics["transactions"]) == 20
assert tokenomics["call_count"] == len(tokenomics["calls"]) == 38
assert tokenomics["adjustment_call_count"] == len(tokenomics["adjustments"]) == 4
assert tokenomics["mint_count"] == sum(int(row["minted"]) > 0 for row in tokenomics["calls"]) == 25
assert tokenomics["read_only_branch_probes"]["count"] == 12
assert tokenomics["read_only_math_probes"]["count"] == 6
assert tokenomics["read_only_redemption_probes"]["count"] == 6
assert tokenomics["read_only_redemption_probes"]["revert_selector"] == "0x32aa90b0"
redemption = read("tokenomics_redemption_stub_behavior.json")
assert redemption["pin"] == manifest["block"] and redemption["block_hash"] == manifest["block_hash"]
assert redemption["runtime_sha256"] == contracts[redemption["implementation"]]["sha256"]
assert redemption["selector_reconstructions"] == {
    "0xfe16eae8": "quoteRedemption(uint256)", "0xdb006a75": "redeem(uint256)"}
assert redemption["error_selector"] == "0x32aa90b0" and redemption["error_name_status"] == "unresolved"
assert all(row["pinned_probe_count"] == 3 for row in redemption["selector_entries"].values())
assert redemption["local_replay_evidence"] == "../../artifacts/fixed_revert_local/replay.json"
redemption_functions = read("selector_catalog.json")[redemption["implementation"]]["functions"]
for selector, signature in redemption["selector_reconstructions"].items():
    row = next(row for row in redemption_functions if row["selector"] == selector)
    assert row["reconstructed_signature"] == signature and row["arguments"] == "uint256"
seven_word = read("tokenomics_seven_word_stub_behavior.json")
assert seven_word["pin"] == manifest["block"] and seven_word["block_hash"] == manifest["block_hash"]
assert seven_word["runtime_sha256"] == contracts[seven_word["implementation"]]["sha256"]
assert seven_word["selector"] == "0x7c7df7b4" and seven_word["error_selector"] == "0x32aa90b0"
assert seven_word["minimum_calldata_bytes"] == 228
assert seven_word["validated_words"] == {"0x04": "address", "0x64": "uint64", "0x84": "uint8"}
seven_word_function = next(row for row in redemption_functions if row["selector"] == seven_word["selector"])
assert seven_word_function["minimum_calldata_bytes"] == 228
assert seven_word_function["validated_word_types"] == seven_word["validated_words"]
assert seven_word_function["arguments_status"].startswith("cast_inference_incomplete")
getters = read("tokenomics_getter_alias_behavior.json")
assert getters["pin"] == manifest["block"] and getters["block_hash"] == manifest["block_hash"]
assert getters["runtime_sha256"] == contracts[getters["implementation"]]["sha256"]
assert {selector: row["direct_slot"] for selector, row in getters["selector_behaviors"].items()} == {
    "0x3886cade": 5, "0xe9ed73e9": 5, "0xc16017ca": 6}
assert getters["selector_behaviors"]["0x3886cade"]["same_entry_as"] == "0xe9ed73e9"
for selector, row in getters["selector_behaviors"].items():
    function = next(item for item in redemption_functions if item["selector"] == selector)
    assert function["observed_storage_slot"] == row["direct_slot"]
    expected = "tokenomics_direct_getters_behavior.json" if selector == "0xe9ed73e9" else "tokenomics_getter_alias_behavior.json"
    assert function["behavior_evidence"] == expected
getter_replay = json.loads((ROOT / "artifacts" / "tokenomics_getter_alias" / "replay.json").read_text())
assert getter_replay["block_hash"] == manifest["block_hash"]
assert getter_replay["runtime_hashes"] == {"proxy": contracts[getters["tokenomics_proxy"]]["sha256"],
                                          "implementation": contracts[getters["implementation"]]["sha256"]}
assert getter_replay["test_source_sha256"] == hashlib.sha256(TOKENOMICS_GETTER_TEST_SOURCE.encode()).hexdigest()
assert getter_replay["forge_result"] == "1 passed, 0 failed"
assert getter_replay["storage_cases"] == [{"slot5": 7, "slot6": 11}, {"slot5": 17, "slot6": 29}]
assert getter_replay["canonical_call_count"] == 6
assert tokenomics["event_catalog"][0]["reconstructed_signature"] == "StakerLpDistributed(uint256,int256,uint256)"
assert tokenomics["selector_reconstructions"]["0xed722c96"] == "onCloseBatch(address,uint256,uint256,uint256)"
assert all(all(row["storage_checks"].values()) for row in tokenomics["transactions"])
tokenomics_errors = read("error_candidates.json")[tokenomics["implementation"]]["candidates"]
assert {row["selector"] for row in tokenomics_errors if row["status"] == "simulated_revert_selector"} == {"0xe343677f", "0x85c58396", "0x30cd7471", "0xe247b81f", "0x32aa90b0", "0xbad8ef95", "0x0dc149f0"}
redemption_error = next(row for row in tokenomics_errors if row["selector"] == "0x32aa90b0")
assert redemption_error["bytecode_evidence"] == "tokenomics_redemption_stub_behavior.json"
assert redemption_error["selector_constructed_in_runtime"] is True
assert redemption_error["additional_bytecode_evidence"] == "tokenomics_seven_word_stub_behavior.json"
params_event = read("static_event_candidates.json")[params["implementation"]]["candidates"]
assert any(row["topic0"] == params["event_catalog"][0]["topic0"] and
           row["reconstructed_signature"] == "MintParamsUpdated(uint256,uint256,uint256,uint256)" and
           row["status"] == "simulated_log_topic" for row in params_event)

staking = read("staking_behavior.json")
assert staking["pin_block"] == manifest["block"]
assert staking["sampled_transaction_count"] == len(staking["transactions"]) == 14
assert staking["signed_call_count"] == len(staking["calls"]) == 45
assert staking["call_counts"] == {"0x83115825": 12, "0xfa2871b5": 2, "0x9c96d4a1": 26, "0xf0355460": 5}
assert staking["accounting_storage_field_checks"] == 177 and staking["accounting_claim_amount_checks"] == 26
assert staking["pinned_nonce_getter_samples"] == staking["pinned_reward_getter_samples"] == 3
assert len(staking["distribution_without_tokenomics_adjustment"]) == 1
assert staking["distribution_without_tokenomics_adjustment"][0]["tx"] == "0xb27bbadf830f5673211719cf6585d9929e91a446c3f46aee940e6e2e02888cdb"
assert staking["distribution_without_tokenomics_adjustment"][0]["tokenomics_adjustment_call_count"] == 0
staking_unallocated = read("staking_unallocated_behavior.json")
assert staking_unallocated == build_staking_unallocated()
assert staking_unallocated["unallocated_override"] == 10**18
assert staking_unallocated["baseline_root_call_count"] == 88 and staking_unallocated["baseline_root_log_count"] == 28
assert staking_unallocated["isolated_child_call_count"] == 13 and staking_unallocated["isolated_child_log_count"] == 5
assert staking_unallocated["unallocated_cleared"] and staking_unallocated["other_contract_post_storage_equal"]
assert staking_unallocated["zero_staker_distributed_event_words"] == staking_unallocated["zero_staker_with_prior_distributed_event_words"]
assert staking_unallocated["zero_staker_deferred_rewards"] == staking_unallocated["baseline_distributed_event_words"][1]
assert staking_unallocated["zero_staker_with_prior_deferred_rewards"] == (
    staking_unallocated["zero_staker_deferred_rewards"] + staking_unallocated["unallocated_override"])

assert staking["pinned_direct_probes"] == {"count": 7, "revert_selector": "0xa15ce1ba"}
staking_direct = read("staking_direct_stubs_behavior.json")
assert staking_direct == build_staking_direct_stubs()
assert set(staking_direct["selector_behaviors"]) == {"0x2e17de78", "0x4e71d92d", "0xa694fc3a", "0xe4fc6b6d"}
assert staking_direct["pinned_probe_count"] == 7 and staking_direct["error_selector"] == "0xa15ce1ba"
assert next(row for row in read("error_candidates.json")[staking_direct["implementation"]]["candidates"]
            if row["selector"] == staking_direct["error_selector"])["bytecode_evidence"] == "staking_direct_stubs_behavior.json"
assert all(next(fn for fn in read("selector_catalog.json")[staking_direct["implementation"]]["functions"]
                if fn["selector"] == selector)["behavior_evidence"] == "staking_direct_stubs_behavior.json"
           for selector in staking_direct["selector_behaviors"])
assert len(staking["selector_reconstructions"]) == 7 and len(staking["event_catalog"]) == 7
staking_getters = read("staking_getters_behavior.json")
assert staking_getters == build_staking_getters()
assert len(staking_getters["selector_reconstructions"]) == 20
assert len(staking_getters["mapping_getter_samples"]) == 12
staking_admin = read("staking_admin_behavior.json")
assert staking_admin == build_staking_admin()
assert set(staking_admin["selector_reconstructions"]) == {"0xd188c049", "0xf2fde38b"}
assert len(staking_admin["historical_transactions"]) == 2 and len(staking_admin["read_only_probes"]) == 4
assert (ATLAS / "staking_admin.md").exists()
assert staking_getters["unnamed_packed_getter"]["byte_offset"] == 20
assert {row["selector"] for row in read("selector_catalog.json")[staking["implementation"]]["functions"] if not row["reconstructed_signature"]} == {"0x0f71c8bc", "0x2e17de78", "0x6090cf16", "0x9ccae24e", "0xa694fc3a"}
assert (ATLAS / "staking_getters.md").exists()
assert staking["selector_reconstructions"]["0xcab7e8eb"] == "isNonceUsed(address,uint256)"
assert staking["deployment_initializer"]["selector"] == "0x9ccae24e"
assert staking["deployment_initializer"]["event_count"] == 2
paper_token = read("paper_token_behavior.json")
assert paper_token["pin_block"] == manifest["block"]
assert paper_token["token_proxy"] == "0xe40f17915daa230324030003a197cdaef2261c0e"
paper_control_history = verify_paper_control_history()
assert paper_control_history["admin_event_count"] == 5
assert paper_control_history["burn_event_count"] == 0
assert paper_token["initializer"]["strings"] == ["Paper", "PAPER"]
assert paper_token["pinned_probe_count"] == 28
assert paper_token["mutation_probe_count"] == 4
assert paper_token["mutation_storage_field_checks"] == 3
assert paper_token["mutation_events_verified"] == 2
assert len(paper_token["admin_transactions"]) == 3
assert paper_token["historical_stake_transfer_count"] == 12
assert paper_token["historical_unstake_transfer_count"] == 2
assert paper_token["historical_mint_count"] == 25
assert len(paper_token["selector_reconstructions"]) == 20
assert len(paper_token["event_catalog"]) == 6
assert len(paper_token["simulated_error_catalog"]) == 6
assert all(row["probe_paths"] for row in paper_token["simulated_error_catalog"])

upgrade = read("upgrade_history.json")
assert len(upgrade) == 8 and all(x["upgrade_event_count"] == 0 and x["same_at_creation_and_pin"] for x in upgrade.values())
catalog = read("selector_catalog.json")
assert len(catalog) == 18 and sum(len(x["functions"]) for x in catalog.values()) == 490
assert {row["reconstructed_signature"] for row in catalog[paper_admin["implementation"]]["functions"]
        if row["selector"] in paper_admin["selector_reconstructions"]} == set(paper_admin["selector_reconstructions"].values())
deposit_functions = catalog["0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"]["functions"]
assert {x["reconstructed_signature"] for x in deposit_functions} == set(deposit["selector_reconstructions"].values())
oracle_functions = catalog[oracle["implementation"]]["functions"]
assert {x["reconstructed_signature"] for x in oracle_functions if x["reconstructed_signature"]} == set(oracle["selector_reconstructions"].values())
exchange_close_function = next(x for x in catalog[exchange_library["exchange_parent_implementation"]]["functions"]
                               if x["selector"] == "0x2792e706")
assert exchange_close_function["reconstructed_signature"] == exchange_library["exchange_parent_selector_reconstructions"]["0x2792e706"]
exchange_open_function = next(x for x in catalog[exchange_event_paths["implementation"]]["functions"]
                              if x["selector"] == "0xec6783f0")
assert exchange_open_function["reconstructed_signature"] == exchange_event_paths["selector_reconstructions"]["0xec6783f0"]
paper_token_functions = catalog[paper_token["implementation"]]["functions"]
assert {x["reconstructed_signature"] for x in paper_token_functions if x["reconstructed_signature"]} == set(paper_token["selector_reconstructions"].values())
session_functions = catalog[session["implementation"]]["functions"]
assert {x["reconstructed_signature"] for x in session_functions if x["selector"] in session["selector_reconstructions"]} == set(session["selector_reconstructions"].values())
paper_token_errors = read("error_candidates.json")[paper_token["implementation"]]["candidates"]
assert all(row["reconstructed_signature"] for row in paper_token_errors)
assert all(row["simulated_revert_probe_count"] > 0 for row in paper_token_errors)
exchange_errors = read("error_candidates.json")[exchange_library["exchange_parent_implementation"]]["candidates"]
assert {row["reconstructed_signature"] for row in exchange_errors
        if row["selector"] in ("0x94e88a21", "0xddeb79ba")} == {
    "PositionNotOpen()", "NotLiquidatable()"}
market_fields = read("exchange_market_fields_behavior.json")
assert market_fields["historical_instrument"] == 0
assert market_fields["historical_values"] == ["2533537756243869928879", "2040719088309057190368"]
assert market_fields["recent_event_call_count"] == 29
assert market_fields["storage_layout"]["mapping_base_slot"] == 36
assert market_fields["setter_probe_count"] == 5
assert market_fields["getter_instruments_checked"] == [0, 1, 2]
assert {row["selector"] for row in exchange_errors if row["status"] == "simulated_revert_selector"
        and row["selector"] in market_fields["revert_selectors"].values()} == set(market_fields["revert_selectors"].values())
assert any(row["topic0"] == market_fields["event_topic0"] and row["status"] == "observed_historical_topic"
           for row in read("static_event_candidates.json")[market_fields["implementation"]]["candidates"])
batch_summary = read("exchange_batch_summary_behavior.json")
batch_thresholds = read("exchange_batch_thresholds_behavior.json")
assert batch_thresholds == build_exchange_batch_thresholds()
assert batch_thresholds["transaction_count"] == batch_summary["transaction_count"] == 26
assert batch_thresholds["requested_position_count"] == batch_summary["requested_position_count"] == 69
assert batch_thresholds["historical_liquidation_count"] == batch_summary["completed_position_count"] == 67
assert batch_thresholds["mismatch_count"] == 0
batch_branches = read("exchange_batch_branches_behavior.json")
assert batch_branches == build_exchange_batch_branches()
assert batch_branches["case_count"] == 15
assert {row["name"]: row["summary_counts"] for row in batch_branches["cases"]}["duplicate_eligible"] == [2, 1]
assert {row["name"]: row["oracle_instruments"] for row in batch_branches["cases"]}["mixed_instruments_reversed"] == [1, 0]
assert batch_summary == verify_exchange_batch_summary()
batch_skips = read("exchange_batch_skip_behavior.json")
assert batch_skips == build_exchange_batch_skips()
assert batch_skips["historical_transaction"] == batch_summary["partial_batch"]["tx"]
assert batch_skips["oracle_midpoint"] == 235155
assert [row["liquidation_threshold"] for row in batch_skips["positions"]] == [235149, 235156, 235156]
assert [row["threshold_predicted_eligible"] for row in batch_skips["positions"]] == [True, False, False]
assert batch_summary["selector_reconstructions"] == {"0x599dc539": "liquidateBatch(uint256[])"}
assert batch_summary["summary_signature"] == "LiquidationBatchProcessed(uint256,uint256)"
assert batch_summary["transaction_count"] == 26
assert batch_summary["requested_position_count"] == 69
assert batch_summary["completed_position_count"] == 67
assert batch_summary["partial_batch"]["requested_ids"] == [1392363, 1394076, 1394080]
assert batch_summary["partial_batch"]["liquidated_ids"] == [1392363]
assert any(row["topic0"] == batch_summary["summary_topic0"]
           and row["reconstructed_signature"] == batch_summary["summary_signature"]
           for row in read("event_catalog.json")["events"])
staker_push = read("exchange_staker_fee_push_behavior.json")
assert next(row for row in catalog[exchange_library["exchange_parent_implementation"]]["functions"]
            if row["selector"] == "0x7b9f5264")["reconstructed_signature"] == "pushStakerFees()"
assert staker_push["historical_push_count"] == 5
assert staker_push["historical_excess_count"] == 4
assert staker_push["pinned_probe_count"] == 5
assert staker_push["pinned_outsider_allowed"] is True
assert int(staker_push["pinned_total_credit"]) == int(staker_push["pinned_fee"]) + int(staker_push["pinned_excess"])
assert {row["reconstructed_signature"] for row in staker_push["event_catalog"]} == {
    "StakerFeesClaimed(address,uint256,uint256)",
    "StakerLpExcessDistributed(address,uint256,uint256,uint256)"}
assert all(any(event["topic0"] == row["topic0"] and
               event["reconstructed_signature"] == row["reconstructed_signature"]
               for event in read("event_catalog.json")["events"])
           for row in staker_push["event_catalog"])
session_errors = read("error_candidates.json")[session["implementation"]]["candidates"]
assert all(any(x["selector"] == y["selector"] and x["status"] == "simulated_revert_selector" for x in session_errors) for y in session["simulated_error_catalog"])
assert next(x for x in session_errors if x["selector"] == "0xc5045f22")["reconstructed_signature"] == "SessionKeyNotAuthorized()"
assert next(x for x in session_errors if x["selector"] == "0xda0700a2")["reconstructed_signature"] == "SessionKeyExpired()"
session_events = read("static_event_candidates.json")[session["implementation"]]["candidates"]
assert all(any(x["topic0"] == y["topic0"] for x in session_events) for y in session["event_catalog"])
decompiler = read("decompiler_runs.json")
assert len(decompiler) == 34 and all(x["exit_code"] == 0 for x in decompiler)
sources = read("source_verification.json")
assert len(sources) == 17 and all(x["verified"] is False for x in sources.values())
metadata = read("compiler_metadata.json")
assert len(metadata) == 25 and all(x.get("solc_version") == "0.8.24" for x in metadata.values())

logs = read("event_logs_last_256_blocks.json")
events = read("event_catalog.json")["events"]
assert len(logs) == 4921 and len(events) == 26
assert sum(x["count_last_256_blocks"] for x in events) == len(logs)
historical_events = read("historical_event_catalog.json")
assert historical_events["saved_receipt_count"] == 147
assert any(row["topic0"] == paper_admin["event_catalog"][0]["topic0"]
           and row["reconstructed_signature"] == "PaperTokenUpdated(address)"
           for row in historical_events["events"])
assert len(historical_events["events"]) == 69
assert next(row for row in historical_events["events"]
            if row["emitter"] == "0x8326eb8896e358717f10502ec73ce8d28e37b108"
            and row["topic0"] == "0xfe60173cc964bc674632fcf67031bba24c8a99a4a7d6518c726586978b7e30d3")["reconstructed_signature"] == "AuthorizedCallerUpdated(address)"
assert next(x for x in historical_events["events"] if x["role"] == "deposit_proxy_factory_proxy"
            and x["topic0"].startswith("0x09bdaf5f"))["reconstructed_signature"] == "AuthorizedDeployerUpdated(address)"
assert next(x for x in historical_events["events"] if x["emitter"] == paper_token["token_proxy"]
            and x["topic0"] == "0xad0f299ec81a386c98df0ac27dae11dd020ed1b56963c53a7292e7a3a314539a")["reconstructed_signature"] == "MinterUpdated(address)"
assert next(x for x in historical_events["events"] if x["emitter"] == paper_token["token_proxy"]
            and x["topic0"] == "0x6397f5b135542bb3f477cb346cfab5abdec1251d08dc8f8d4efb4ffe122ea0bf")["reconstructed_signature"] == "StakingContractUpdated(address)"
assert next(x for x in historical_events["events"] if x["emitter"] == oracle["oracle_proxy"]
            and x["topic0"] == oracle["event_catalog"][0]["topic0"])["reconstructed_signature"] == "OwnerUpdated(address)"
assert next(x for x in historical_events["events"] if x["emitter"] == sweeps["address"]
            and x["topic0"] == sweeps["event_signatures"]["SweepRequested(address,address,uint64,uint64,uint32)"])["reconstructed_signature"] == "SweepRequested(address,address,uint64,uint64,uint32)"
storage = read("storage_trace_catalog.json")
assert sum(len(x["views"]) for x in storage.values()) == 152
state_links = read("state_links.json")
assert len(state_links) == 33 and all(x["getter"] != "treasury()" for x in state_links)
call_graph = read("observed_call_graph.json")
assert len(call_graph["traces"]) == 139 and len(call_graph["edges"]) == 37
assert sum(row["root_call_type"] == "CREATE" for row in call_graph["traces"]) == 5
assert all(row["root_selector"] is None and row["root_initcode_prefix"]
           for row in call_graph["traces"] if row["root_call_type"] == "CREATE")
assert all(not row["selectors"] and row["initcode_prefixes"]
           for row in call_graph["edges"] if row["call_type"] in ("CREATE", "CREATE2"))
state_writes = read("state_write_catalog.json")
assert len(state_writes["transactions"]) == 137
assert state_writes["summary"]["exchange_proxy"]["cleared_dynamic_slot_count"] == 308
assert state_writes["diff_mode_semantics"].startswith("A pre-only storage key")
deployment_diffs = read("deployment_state_diffs_behavior.json")
assert deployment_diffs["pin"] == manifest["block"] and deployment_diffs["block_hash"] == manifest["block_hash"]
assert set(deployment_diffs["verified_creations"]) == {"staking", "paper_token", "session_creation"}
assert {role: len(row["direct_slot_values"]) for role, row in deployment_diffs["verified_creations"].items()} == {
    "staking": 8, "paper_token": 5, "session_creation": 4}
for row in deployment_diffs["verified_creations"].values():
    assert row["proxy_runtime_sha256"] == contracts[row["proxy"]]["sha256"]
    assert all((ATLAS / path).exists() for path in row["artifacts"].values())
    assert hashlib.sha256((ATLAS / row["artifacts"]["state_diff"]).read_bytes()).hexdigest() == row["state_diff_sha256"]
    assert any(trace["hash"] == row["transaction_hash"] and trace["source_directory"] in deployment_diffs["verified_creations"]
               for trace in call_graph["traces"])
    assert any(tx["tx"] == row["transaction_hash"] and tx["root_call_type"] == "CREATE"
               for tx in state_writes["transactions"])
assert (ATLAS / "deployment_state_diffs.md").exists()
replays = read("replay_comparisons.json")["comparisons"]
assert len(replays) == 7
assert all(x["call_skeleton_equal"] and x["log_multiset_equal"] for x in replays)
assert all(x["contract_storage_changes_equal"] for x in replays)
sweep_replay = next(x for x in replays if x["selector"] == "0x6d142da1" and x["transaction_index"] == 2)
assert len(sweep_replay["same_block_storage_prestate"]) == 1
sweep_slot = sweep_replay["same_block_storage_prestate"][0]
assert sweep_slot["address"] == "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
assert int(sweep_slot["slot"], 16) == 22
assert len(sweep_slot["earlier_same_block_writes"]) == 2
assert sweep_slot["parent"] == sweep_slot["earlier_same_block_writes"][0]["before"]
assert sweep_slot["earlier_same_block_writes"][0]["after"] == sweep_slot["earlier_same_block_writes"][1]["before"]
assert sweep_slot["pre_transaction"] == sweep_slot["earlier_same_block_writes"][1]["after"]
unresolved = read("unresolved.json")
assert {row["selector"]: row["evidence"] for row in unresolved["signed_intent_branch_gaps"]} == {
    "0x8d09f23f": "exchange_withdrawal_signature_behavior.json",
    "0x2792e706": "session_close_typehash_behavior.json",
    "0xec6783f0": "session_open_typehash_behavior.json"}
assert {row["selector"]: row["event_absence_evidence"] for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
        if row["role"] == "paper_token_implementation"} == {
    "0x9dc29fac": "paper_control_history_behavior.json",
    "0xfca3b5aa": "paper_control_history_behavior.json"}
assert not any(row["role"] == "exchange_implementation" and row["selector"] == "0x40f92143"
               for row in unresolved["observed_reverts_without_public_signature"])
assert next(row for row in read("error_candidates.json")["0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"]["candidates"]
            if row["selector"] == "0x40f92143")["reconstructed_signature"] == "OiCapExceeded()"
assert {row["selector"]: row["observed_storage_slot"]
        for row in unresolved["unmatched_selector_candidates"]
        if row.get("behavior_evidence") == "tokenomics_getter_alias_behavior.json"} == {
    "0x3886cade": 5}
position_index = read("exchange_position_index_behavior.json")
assert position_index == build_exchange_position_index()
assert position_index["opening_count"] == 25 and position_index["removal_count"] == 15
assert position_index["removal_array_group_count"] == 14
assert sum(row["operation"] == "swap_last_then_pop" for row in position_index["removal_array_checks"]) == 2
assert sum(row["operation"] == "tail_pop" for row in position_index["removal_array_checks"]) == 11
assert position_index["historical_getter_count"] == 3
instruments_getter = read("exchange_instruments_getter_behavior.json")
assert instruments_getter == build_exchange_instruments_getter()
assert instruments_getter["sample_count"] == 3 and instruments_getter["return_word_count"] == 8
direct_getters = read("exchange_direct_getters_behavior.json")
assert direct_getters == build_exchange_direct_getters()
assert len(direct_getters["selector_reconstructions"]) == 17
assert len(direct_getters["direct_slot_getters"]) == 16
assert len(direct_getters["balance_mapping_samples"]) == 3
assert direct_getters["packed_slot29_override_count"] == 2
assert (ATLAS / "exchange_direct_getters.md").exists()
guardian_leads = read("guardian_signature_leads.json")
assert guardian_leads == build_guardian_signature_leads()
assert guardian_leads["active_selector_match_count"] == 86
assert len(guardian_leads["matches"]) == 86
assert all("0x" + Keccak()(row["signature"].encode())[:4].hex() == row["selector"]
           for row in guardian_leads["matches"])
promoted_report_names = [(contract["role"], function["selector"], function["reconstructed_signature"])
                         for contract in catalog.values() for function in contract["functions"]
                         if function["signature_status"] == "hash_matched_guardian_report_and_bytecode_layout"]
assert len(promoted_report_names) == 15
assert ("tokenomics_implementation", "0x0efdf838", "onLoss(address,uint256,bool,uint256,uint256)") in promoted_report_names
assert ("session_key_manager_implementation", "0x17a1678f", "registerSessionKeyDirect(address,uint64,address)") in promoted_report_names
name_gaps = read("public_name_gap_checks.json")
assert name_gaps == build_public_name_gaps()
assert name_gaps["openchain_function_selector_count"] == 45
assert name_gaps["openchain_function_selectors_with_candidates"] == 0
assert name_gaps["openchain_event_topic_count"] == 4
assert name_gaps["openchain_event_topics_with_candidates"] == 0
assert name_gaps["guardian_report_event_matches"] == []
assert name_gaps["instrument_event_full_history_log_count"] == 0
assert name_gaps["control_event_last_256_block_log_count"] == 29
assert (ATLAS / "public_name_gaps.md").exists()
coverage = read("selector_evidence_coverage.json")
assert coverage["pin"] == manifest["block"] and coverage["block_hash"] == manifest["block_hash"]
assert len(coverage["rows"]) == coverage["summary"]["all_captured_runtime_selector_rows"] == 490
assert coverage["summary"]["active_runtime_selector_rows"] == 284
assert coverage["summary"]["unused_variant_selector_rows"] == 206
assert coverage["summary"]["active_rows_with_saved_historical_call_graph_evidence"] == 75
assert coverage["summary"]["active_rows_with_saved_view_probe"] == 152
assert coverage["summary"]["active_rows_with_successful_saved_view_probe"] == 139
assert coverage["summary"]["active_rows_with_signature_reconstruction_artifact"] == 232
assert coverage["summary"]["active_rows_with_linked_behavior_artifact"] == 284
signed_audit_rows = [row for row in coverage["rows"] if row["active_runtime_at_pin"]
                     and "local_signed_intent_audit_replay" in row["indexed_evidence"]]
assert coverage["summary"]["active_rows_with_local_signed_intent_audit_replay"] == len(signed_audit_rows) == 5
assert {row["selector"] for row in signed_audit_rows} == {
    "0x8d09f23f", "0x2792e706", "0xec6783f0", "0xb002b9fa", "0x7f608253"}
assert all("../../artifacts/audit_signed_intent_failures/replay.json" in row["linked_behavior_artifacts"]
           for row in signed_audit_rows)
assert coverage["summary"]["active_rows_with_historical_replay_match"] == 7
assert coverage["summary"]["active_rows_with_local_fixed_revert_replay"] == 12
assert coverage["summary"]["active_rows_with_local_proxy_admin_replay"] == 5
assert coverage["summary"]["active_rows_with_local_shared_proxy_replay"] == 4
assert coverage["summary"]["active_rows_with_local_deposit_proxy_replay"] == 4
assert all("../../artifacts/deposit_proxy_local/replay.json" in row["linked_behavior_artifacts"]
           for row in coverage["rows"] if row["role"] == "user_deposit_proxy_representative")
assert coverage["summary"]["active_rows_with_local_batch_control_replay"] == 11
assert coverage["summary"]["active_rows_with_local_batch_field4_replay"] == 1
assert coverage["summary"]["active_rows_with_local_batch_allowlist_replay"] == 1
assert coverage["summary"]["active_rows_with_local_exchange_pause_replay"] == 6
assert coverage["summary"]["active_rows_with_local_exchange_instrument_limit_replay"] == 1
assert coverage["summary"]["active_rows_with_local_exchange_instrument_creation_replay"] == 1
assert coverage["summary"]["active_rows_with_local_exchange_instrument_admin_replay"] == 1
assert coverage["summary"]["active_rows_with_local_exchange_initializer_replay"] == 1
assert coverage["summary"]["active_rows_with_local_exchange_library_adapter_replay"] == 8
assert coverage["summary"]["active_rows_with_local_exchange_library_queue_merge_replay"] == 4
assert coverage["summary"]["active_rows_with_local_exchange_library_queue_harvest_followup_replay"] == 6
assert coverage["summary"]["active_rows_with_local_exchange_library_queue_interleaved_replay"] == 7
assert coverage["summary"]["active_rows_with_local_exchange_library_queue_count_merge_replay"] == 4
assert coverage["summary"]["active_rows_with_local_exchange_library_remaining_replay"] == 3
assert coverage["summary"]["active_rows_with_local_remaining_initializer_replay"] == 4
assert coverage["summary"]["active_untraced_nonview_rows_with_linked_behavior_artifact"] == 41
assert all(row["linked_behavior_artifacts"] for row in coverage["priority_untraced_nonview_selectors"])
assert "staking_unallocated_behavior.json" in next(row for row in coverage["rows"]
    if row["role"] == "staking_implementation" and row["selector"] == "0xf0355460")["linked_behavior_artifacts"]
assert coverage["summary"]["active_rows_without_reconstructed_signature"] == 52
assert "session_open_typehash_behavior.json" in next(row for row in coverage["rows"]
    if row["role"] == "exchange_implementation" and row["selector"] == "0xec6783f0")["linked_behavior_artifacts"]
assert "exchange_open_limit_full_behavior.json" in next(row for row in coverage["rows"]
    if row["role"] == "exchange_implementation" and row["selector"] == "0xec6783f0")["linked_behavior_artifacts"]
for role, selector in (("exchange_implementation", "0xec6783f0"),
                       ("batch_executor_implementation", "0x251fb27d")):
    row = next(row for row in coverage["rows"] if row["role"] == role and row["selector"] == selector)
    assert "historical_signed_open_full_replay" in row["indexed_evidence"]
    assert "../../artifacts/audit_historical_open/replay.json" in row["linked_behavior_artifacts"]
for role, selector in (("exchange_implementation", "0x2792e706"),
                       ("batch_executor_implementation", "0x251fb27d")):
    row = next(row for row in coverage["rows"] if row["role"] == role and row["selector"] == selector)
    assert "historical_signed_close_full_replay" in row["indexed_evidence"]
    assert "../../artifacts/audit_historical_close/replay.json" in row["linked_behavior_artifacts"]
for selector, filename in (("0x415f1240", "exchange_liquidation_behavior.json"),
                           ("0x599dc539", "exchange_batch_summary_behavior.json")):
    row = next(row for row in coverage["rows"]
               if row["role"] == "exchange_implementation" and row["selector"] == selector)
    assert filename in row["linked_behavior_artifacts"]
    assert filename in row["signature_reconstruction_artifacts"]
assert "exchange_batch_skip_behavior.json" in next(
    row for row in coverage["rows"]
    if row["role"] == "exchange_implementation" and row["selector"] == "0x599dc539"
)["linked_behavior_artifacts"]
assert "exchange_batch_thresholds_behavior.json" in next(
    row for row in coverage["rows"]
    if row["role"] == "exchange_implementation" and row["selector"] == "0x599dc539"
)["linked_behavior_artifacts"]
assert "exchange_batch_branches_behavior.json" in next(
    row for row in coverage["rows"]
    if row["role"] == "exchange_implementation" and row["selector"] == "0x599dc539"
)["linked_behavior_artifacts"]
assert "liquidation_tokenomics_behavior.json" in next(
    row for row in coverage["rows"]
    if row["role"] == "tokenomics_implementation" and row["selector"] == "0x0efdf838"
)["linked_behavior_artifacts"]
assert "tokenomics_liquidation_flag_behavior.json" in next(
    row for row in coverage["rows"]
    if row["role"] == "tokenomics_implementation" and row["selector"] == "0x0efdf838"
)["linked_behavior_artifacts"]
paper_math_row = next(row for row in coverage["rows"] if row["role"] == "paper_math_library")
assert paper_math_row["cast_inferred_arguments"] == "uint256,uint256,uint256,uint256,uint256,uint256"
assert paper_math_row["linked_behavior_artifacts"] == ["paper_math_behavior.json"]
assert paper_math_row["reconstructed_signature"] == "" and paper_math_row["arguments_status"] == "observed_from_calldata_and_bytecode"
assert coverage["summary"]["active_rows_without_any_indexed_evidence"] == 0
assert all(row["linked_behavior_artifacts"] for row in coverage["rows"] if row["active_runtime_at_pin"])
assert all((ATLAS / filename).exists() for row in coverage["rows"] if row["active_runtime_at_pin"]
           for filename in row["linked_behavior_artifacts"])
for selector, filename in (("0xf728fc98", "exchange_position_index_behavior.json"),
                           ("0xdc8a47ef", "exchange_instruments_getter_behavior.json")):
    row = next(row for row in coverage["rows"] if row["active_runtime_at_pin"]
               and row["role"] == "exchange_implementation" and row["selector"] == selector)
    assert row["linked_behavior_artifacts"] == [filename]
assert next(row for row in coverage["rows"]
            if row["active_runtime_at_pin"] and row["role"] == "session_key_manager_implementation"
            and row["selector"] == "0xd45167d0")["linked_behavior_artifacts"] == ["session_direct_signer_behavior.json"]
assert next(row for row in coverage["rows"]
            if row["active_runtime_at_pin"] and row["role"] == "session_key_manager_implementation"
            and row["selector"] == "0x7f608253")["linked_behavior_artifacts"] == [
                "../../artifacts/audit_signed_intent_failures/replay.json",
                "session_open_typehash_behavior.json", "session_signer_branches_behavior.json", "session_signer_expanded_behavior.json"]
for selector in session_typehashes["constant_getters"]:
    row = next(row for row in coverage["rows"] if row["active_runtime_at_pin"]
               and row["role"] == "session_key_manager_implementation" and row["selector"] == selector)
    expected = ["session_typehash_behavior.json"]
    if selector == "0x6525a680":
        expected.insert(0, "session_open_typehash_behavior.json")
    assert row["linked_behavior_artifacts"] == expected
    assert bool(row["reconstructed_signature"]) == bool(session_typehashes["constant_getters"][selector]["verified_type_string"])
owner_row = next(row for row in coverage["rows"] if row["active_runtime_at_pin"]
                 and row["role"] == "session_key_manager_implementation" and row["selector"] == "0xf2fde38b")
assert owner_row["reconstructed_signature"] == "transferOwnership(address)"
assert "session_key_behavior.json" in owner_row["linked_behavior_artifacts"]
# Base behavior maps are linked only where they explicitly reconstruct the selector.
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
for role, filenames in base_behavior_files.items():
    for filename in filenames:
        supported = set(read(filename).get("selector_reconstructions", {}))
        for row in coverage["rows"]:
            if row["active_runtime_at_pin"] and row["role"] == role and row["selector"] in supported:
                assert row["linked_behavior_artifacts"], (role, row["selector"], filename)
for role, selector, artifact in (
    ("deposit_proxy_factory_implementation", "0x0f71c8bc", "factory_behavior.json"),
    ("deposit_proxy_factory_implementation", "0xc6f881bc", "factory_selector_names_behavior.json"),
    ("oracle_implementation", "0xa7f06462", "oracle_behavior.json"),
    ("staking_implementation", "0xcab7e8eb", "staking_behavior.json"),
    ("session_key_manager_implementation", "0xc1e6613d", "session_key_behavior.json"),
):
    row = next(row for row in coverage["rows"] if row["role"] == role and row["selector"] == selector)
    assert artifact in row["linked_behavior_artifacts"] or artifact in row["signature_reconstruction_artifacts"]
    assert row["indexed_evidence"]

assert {(row["role"], row["selector"]) for row in coverage["priority_untraced_nonview_selectors"]} == {
    (row["role"], row["selector"]) for row in unresolved["state_changing_selectors_without_saved_historical_trace"]}
assert len({(row["role"], row["selector"]) for row in coverage["rows"]}) == 490
assert all(bool(row["reconstructed_signature"]) == bool(row["signature_reconstruction_artifacts"])
           for row in coverage["rows"] if row["active_runtime_at_pin"])
assert "284 active-runtime selector rows" in (ATLAS / "selector_coverage.md").read_text()
assert len(unresolved["unmatched_selector_candidates"]) == 49
assert len([row for row in unresolved["unmatched_selector_candidates"]
            if row.get("semantic_evidence") == "exchange_library_behavior.json"]) == 3
assert next(row for row in unresolved["unmatched_selector_candidates"]
            if row["role"] == "exchange_linked_library_live" and row["selector"] == "0xef1a27a9")["fee_rate_evidence"] == "exchange_library_fee_rates_behavior.json"
assert len(unresolved["ambiguous_public_signature_matches"]) == 0
assert len(unresolved["unverified_decompiler_error_candidates"]) == 8
assert len(unresolved["state_changing_selectors_without_saved_historical_trace"]) == 41
proxy_admin = read("proxy_admin_behavior.json")
assert proxy_admin["pin"] == manifest["block"] and proxy_admin["block_hash"] == manifest["block_hash"]
assert proxy_admin["runtime_sha256"] == contracts[proxy_admin["address"]]["sha256"]
assert proxy_admin["owner_at_pin"] == "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
assert proxy_admin["shared_proxy_count"] == 8 and proxy_admin["proxy_executable_log_instruction_count"] == 0
assert proxy_admin["tested_effects"]["upgrade_to_no_code_address"] == "accepted in local pinned-runtime replay"
assert "completeness is not independently proven" in proxy_admin["upgrade_history_limit"]
assert proxy_admin["administrative_history_evidence"]["proxy_admin_direct_transaction_pages"] == [2, 2]
assert proxy_admin["administrative_history_evidence"]["saved_timelock_execution_event_count"] == 0
assert len(proxy_admin["selector_reconstructions"]) == 5
assert {row["selector"]: row["reconstructed_signature"]
        for row in catalog[proxy_admin["address"]]["functions"]} == proxy_admin["selector_reconstructions"]
proxy_admin_replay = json.loads((ROOT / "artifacts" / "proxy_admin_local" / "replay.json").read_text())
assert proxy_admin_replay["block_hash"] == manifest["block_hash"]
assert proxy_admin_replay["forge_result"] == "10 passed, 0 failed" and len(proxy_admin_replay["test_names"]) == 10
assert proxy_admin_replay["test_source_sha256"] == hashlib.sha256(PROXY_ADMIN_TEST_SOURCE.encode()).hexdigest()
shared_proxy = read("shared_proxy_behavior.json")
assert shared_proxy["pin"] == manifest["block"] and shared_proxy["block_hash"] == manifest["block_hash"]
assert shared_proxy["runtime_role"] == "deposit_proxy_factory_proxy"
assert shared_proxy["runtime_sha256"] == contracts[shared_proxy["address"]]["sha256"]
assert len(shared_proxy["proxy_addresses"]) == 8 and shared_proxy["executable_log_instruction_count"] == 0
assert {row["selector"]: row["reconstructed_signature"]
        for row in catalog[shared_proxy["address"]]["functions"]} == shared_proxy["selector_reconstructions"]
assert {row["selector"]: row.get("reconstructed_signature")
        for row in shared_proxy["simulated_error_catalog"]} == {
    "0x7bfa4b9f": "NotAdmin()", "0xe6c4247b": None}
assert {row["selector"] for row in coverage["rows"]
        if row["role"] == shared_proxy["runtime_role"] and "local_shared_proxy_replay" in row["indexed_evidence"]} == set(shared_proxy["selector_reconstructions"])
assert (ATLAS / "shared_proxy_pseudocode.md").exists()
assert {row["selector"] for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
        if row["role"] == "proxy_admin" and row.get("behavior_evidence") == "proxy_admin_behavior.json"} == {
    "0x7eff275e", "0x9623609d", "0x99a88ec4"}
assert {row["selector"]: row["reconstructed_signature"] for row in read("error_candidates.json")[proxy_admin["address"]]["candidates"]} == {
    "0x30cd7471": "NotOwner()", "0x49e27cff": "InvalidOwner()"}
assert all(row["status"] == "simulated_revert_selector" for row in read("error_candidates.json")[proxy_admin["address"]]["candidates"])
all_error_rows = [row for contract in read("error_candidates.json").values() for row in contract["candidates"]]
registry = json.loads((ROOT / "artifacts" / "openchain_unverified_error_lookup.json").read_text())
assert registry["response"]["ok"] and len(registry["selectors"]) == 52
registry_rows = registry["response"]["result"]["function"]
assert set(registry_rows) == set(registry["selectors"])
registry_hits = {selector: [entry["name"] for entry in entries or []]
                 for selector, entries in registry_rows.items() if entries}
assert len(registry_hits) == 31
assert all("0x" + Keccak()(name.encode())[:4].hex() == selector
           for selector, names in registry_hits.items() for name in names)
assert sum(bool(row.get("public_registry_evidence")) for row in all_error_rows) == 97
assert sum(row["status"] == "unverified_heimdall_candidate" and bool(row.get("public_registry_evidence"))
           for row in all_error_rows) == 69
assert all(set(registry_hits[row["selector"]]) <= set(row["public_signature_candidates"])
           for row in all_error_rows if row.get("public_registry_evidence"))
assert sum(bool(row.get("reconstructed_signature")) for row in all_error_rows) == 46
branch_names = {
    ("exchange_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "exchange_initializer_behavior.json"),
    ("exchange_implementation", "0x6a426315"): ("UnsupportedCollateralDecimals()", "exchange_initializer_behavior.json"),
    ("exchange_implementation", "0x0d240815"): ("MarketAlreadyPaused()", "exchange_pause_behavior.json"),
    ("exchange_implementation", "0x28ef4314"): ("SweepAlreadyPending()", "exchange_sweep_recovery_behavior.json"),
    ("exchange_implementation", "0x49199fb6"): ("NotPauseAuthority()", "exchange_pause_behavior.json"),
    ("oracle_implementation", "0x30cd7471"): ("NotOwner()", "oracle_behavior.json"),
    ("tokenomics_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "tokenomics_initializer_behavior.json"),
    ("session_key_manager_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "session_initializer_behavior.json"),
    ("deposit_proxy_factory_implementation", "0x0dc149f0"): ("AlreadyInitialized()", "factory_behavior.json"),
    ("deposit_proxy_factory_implementation", "0x30cd7471"): ("NotOwner()", "factory_behavior.json"),
    ("timelock", "0x30cd7471"): ("NotOwner()", "timelock_behavior.json"),
}
error_by_role = {(contract["role"], row["selector"]): row
                 for contract in read("error_candidates.json").values() for row in contract["candidates"]}
assert all(error_by_role[item]["reconstructed_signature"] == name
           and error_by_role[item]["behavior_evidence"] == evidence
           and error_by_role[item]["simulated_revert_probe_count"] > 0
           for item, (name, evidence) in branch_names.items())
assert len(all_error_rows) == 212
assert sum(row["status"] == "unverified_heimdall_candidate" for row in all_error_rows) == 119
assert sum(row["status"] == "simulated_revert_selector" for row in all_error_rows) == 88
assert sum(row["status"] == "bytecode_verified_revert_selector" for row in all_error_rows) == 2
assert sum(row["status"] == "observed_revert_selector" for row in all_error_rows) == 3
assert next(row for row in read("historical_event_catalog.json")["events"]
            if row["emitter"] == proxy_admin["address"] and row["topic0"] == proxy_admin["event_catalog"][0]["topic0"])["reconstructed_signature"] == "OwnerUpdated(address)"
assert {row["selector"] for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
        if row.get("simulation_evidence") == "../../artifacts/paper_token/pinned_mutation_traces.json"} == {
            "0x9dc29fac", "0xfca3b5aa"}
assert {row["selector"] for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
        if row.get("simulation_evidence") == "exchange_liquidation_behavior.json"} == {"0x415f1240"}
assert {row["selector"] for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
        if row.get("simulation_evidence") == "tokenomics_params_behavior.json"} == {"0x12baae3b"}
assert len(unresolved["observed_events_without_resolved_signature"]) == 4
assert len(unresolved["simulated_events_without_resolved_signature"]) == 2
assert {row["topic0"] for row in unresolved["observed_events_without_resolved_signature"]
        if row.get("behavior_evidence") == "tokenomics_observed_paths.json"} == {
            "0x620c26bf4591919d64df736a6afdfe2981d15eb343c50644b49456c6facb3ab2",
            "0x3050fba19ada85812db26b240c13c72cabec711cbf18c7c6b3554d511e2951ee"}
assert all(row.get("decoded_layout") for row in unresolved["observed_events_without_resolved_signature"])
queue_layout = read("exchange_queue_layout_behavior.json")
assert queue_layout["event_catalog"][0]["reconstructed_signature"] == "Enqueued(address,uint256,uint256)"
assert [row["node_id"] for row in queue_layout["enqueues"]] == [1, 2, 3]
assert queue_layout["harvest"]["total_queued_after"] == 0
assert all(row["topic0"] != queue_layout["event_catalog"][0]["topic0"]
           for row in unresolved["observed_events_without_resolved_signature"])
queue_harvest = read("exchange_queue_harvest_behavior.json")
assert queue_harvest["enqueued_history"]["complete_first_page_count"] == 3
assert queue_harvest["enqueued_history"]["all_three_users_distinct"]
assert [row["max_entries"] for row in queue_harvest["partial_harvest_probes"]] == [0, 1, 2, 3]
assert [int(row["returned_amount"]) for row in queue_harvest["partial_harvest_probes"]] == [
    0, 7623942182351823589, 15247884364703647178, 22871826547055470767]
assert all(queue_harvest["full_harvest_replay"].values())
assert queue_harvest["event_catalog"][0]["decoded_layout"] == "indexed user; unindexed amount paid, node amount remaining"
assert next(row for row in read("historical_event_catalog.json")["events"]
            if row["emitter"] == queue_harvest["exchange_proxy"] and row["topic0"] == queue_harvest["event_catalog"][0]["topic0"])["reconstructed_signature"] == "Harvested(address,uint256,uint256)"
assert queue_harvest["partial_node_with_side_bucket"]["node_remaining"] == "4623942182351823589"
assert queue_harvest["partial_node_with_side_bucket"]["global_head_unchanged"]
queue_append = read("exchange_queue_append_behavior.json")
assert queue_append["baseline_replay"] == {"exchange_storage_diff_equal": True,
                                           "all_ordered_logs_equal": True}
assert queue_append["append"]["new_node_id"] == 2
assert queue_append["append"]["total_queued_after"] == "12623942182351823589"
assert [row["returned_amount"] for row in queue_append["same_user_harvest"]] == [
    "5000000000000000000", "12623942182351823589"]
assert [int(row["returned_amount"]) for row in queue_append["partial_node_payouts"]] == [
    0, 0, 3 * 10**18, 3 * 10**18, 5 * 10**18, 5 * 10**18, 5 * 10**18, 7 * 10**18]
assert [row["harvest_events"] for row in queue_append["partial_node_payouts"]] == [
    0, 0, 1, 1, 1, 1, 1, 2]
core_withdrawal = read("exchange_core_withdrawal_behavior.json")
assert core_withdrawal["selector_reconstructions"]["0x8d09f23f"] == "withdrawToCoreBySig(address,uint256,uint256,uint64,uint8,bytes32,bytes32)"
assert core_withdrawal["event_catalog"][0]["reconstructed_signature"] == "CoreWithdrawal(address,uint256,uint256)"
assert core_withdrawal["transaction_count"] == 3
assert [int(row["debit_less_sent_18_decimals"]) for row in core_withdrawal["transactions"]] == [10**18, 0, 0]
staking_credit = read("exchange_staking_credit_behavior.json")
assert staking_credit == build_staking_credit()
assert staking_credit["selector_reconstructions"] == {"0xe53e3de6": "creditStakingReward(address,uint256)"}
assert staking_credit["historical_transaction_count"] == 7 and staking_credit["historical_call_count"] == 27
assert staking_credit["read_only_probe_count"] == 4
assert sum(row["event_count"] for row in staking_credit["transactions"]) == 27
assert all(int(row["staking_balance_delta"]) == -int(row["total_credited"]) for row in staking_credit["transactions"])
assert (ATLAS / "exchange_staking_credit.md").exists()
direct_withdrawal = read("exchange_direct_withdrawal_behavior.json")
assert direct_withdrawal["selector_reconstructions"] == {"0x7f99545a": "withdrawToCore(uint256)"}
assert direct_withdrawal["probe_count"] == 9 and direct_withdrawal["successful_cases"] == 3
assert direct_withdrawal["historical_direct_call_count"] == 2
assert [row["core_user_status_word"] for row in direct_withdrawal["historical_direct_calls"]] == [0, 1]
assert [int(row["extra_debit"]) for row in direct_withdrawal["historical_direct_calls"]] == [10**18, 0]
assert [row["internal_balance_mapping_changed"] for row in direct_withdrawal["historical_direct_calls"]] == [True, True]
assert [row["internal_balance_slot_cleared"] for row in direct_withdrawal["historical_direct_calls"]] == [False, True]
assert [row["internal_balance_post"] for row in direct_withdrawal["historical_direct_calls"]][-1] == "0"
assert direct_withdrawal["local_status_test_count"] == 4
status_replay = json.loads((ROOT / "artifacts" / "exchange_direct_status_local" / "replay.json").read_text())
assert status_replay["forge_result"] == "4 passed, 0 failed"
assert set(status_replay["test_names"]) == {"testStatusZeroHeadroom", "testStatusOneHeadroom",
                                           "testStatusZeroExactBalanceRejected", "testStatusOneExactBalance"}
assert status_replay["test_source_sha256"] == hashlib.sha256(direct_status_test_source().encode()).hexdigest()
assert status_replay["status_one_exact_balance_clears_user_balance"]
second_direct_tx = direct_withdrawal["historical_direct_calls"][1]["tx"]
second_write = next(row for row in state_writes["transactions"] if row["tx"] == second_direct_tx)
assert len(next(change for change in second_write["changes"] if change["role"] == "exchange_proxy")["cleared_dynamic_slots"]) == 1
withdrawal_history = verify_withdrawal_history()
assert sum(len(window["logs"]) for window in withdrawal_history["windows"]) == 28643
withdrawal_census = verify_withdrawal_census()
assert withdrawal_census["gap_counts_18_decimals"] == {"0": 22652, str(10**18): 5991}
assert withdrawal_census["sample_selector_status_counts"] == [
    {"selector": "0x8d09f23f", "hypercore_user_status": 0, "count": 16},
    {"selector": "0x8d09f23f", "hypercore_user_status": 1, "count": 16}]
boundary = verify_hypercore_boundary()
assert boundary["boundary_call_count"] == 482 and boundary["oracle_bbo_midpoint_matches"] == 102
assert boundary["corewriter_action_counts"] == {"spot_send_6": 118, "other": 0}
withdrawal_trace_corpus = verify_withdrawal_trace_corpus()
assert withdrawal_trace_corpus["matched_call_count"] == 103
assert withdrawal_trace_corpus["core_user_exists_counts"] == {"0": 43, "1": 60}
assert withdrawal_trace_corpus["matched_full_history_event_count"] == 103
withdrawal_signature = verify_withdrawal_signature()
assert withdrawal_signature["matched_call_count"] == 103
assert withdrawal_signature["distinct_user_nonce_count"] == 103
verify_withdrawal_nonce_history()
assert withdrawal_signature["typehash"] == read("session_typehash_behavior.json")["constant_getters"]["0x0b4c3a82"]["pinned_return"]
core_user_exists = verify_core_user_exists()
assert core_user_exists["precompile"] == withdrawal_census["status_precompile"]
assert withdrawal_census["status_semantic_evidence"] == "hypercore_user_exists_evidence.json"
verify_control_event_history()
control_history = read("exchange_control_event_history_behavior.json")
assert {row["selector"] for row in control_history["full_history_zero_event_paths"]} == {
    "0xae69b95b", "0x2d2451d1", "0xe538b280", "0xd7c7e5fb"}
assert all(row["successful_event_log_count"] == 0 for row in control_history["full_history_zero_event_paths"])
assert direct_withdrawal["strict_minimum_raw_amount"] == 1000000
assert direct_withdrawal["case_results"]["at_one_usd"]["revert_selector"] == "0xad21c3fb"
assert direct_withdrawal["case_results"]["same_block"]["revert_selector"] == "0x4f57ffae"
assert direct_withdrawal["case_results"]["zero_core_balance"]["revert_selector"] == "0x0a9e0180"
assert all(int(direct_withdrawal["case_results"][label]["extra_debit"]) == 10**18
           for label in ("above_one_usd", "two_usd", "near_user_balance"))
assert next(row for row in catalog[direct_withdrawal["implementation"]]["functions"]
            if row["selector"] == "0x7f99545a")["reconstructed_signature"] == "withdrawToCore(uint256)"
assert not any(row["role"] == "exchange_implementation" and row["selector"] == "0x7f99545a"
               for row in unresolved["state_changing_selectors_without_saved_historical_trace"])
assert next(row for row in coverage["rows"] if row["role"] == "exchange_implementation"
            and row["selector"] == "0x7f99545a")["historical_edge_call_count"] == 2
assert not any(row["role"] == "exchange_implementation" and row["selector"] == "0x7f99545a"
               for row in unresolved["unmatched_selector_candidates"])
direct_errors = read("error_candidates.json")[direct_withdrawal["implementation"]]["candidates"]
assert all(next(row for row in direct_errors if row["selector"] == selector)["simulated_revert_probe_count"] >= count
           for selector, count in (("0x0a9e0180", 2), ("0xad21c3fb", 2),
                                   ("0xa3b9a36c", 1), ("0x4f57ffae", 1)))
exchange_getters = read("exchange_getters_behavior.json")
assert exchange_getters["selector_reconstructions"] == {
    "0x3a21be03": "userQueueTail(address)",
    "0x551306f3": "userQueuedTotal(address)",
    "0x31a4956c": "getPendingSweep(address)",
    "0x7e4174fc": "pendingSweepWord(address)",
    "0x32faa570": "lastCoreWithdrawalBlock(address)",
}
assert exchange_getters["historical_getter_call_count"] == 80
assert exchange_getters["sweep_pair_count"] == 13
assert exchange_getters["signed_core_withdrawal_count"] == 4
getter_functions = read("selector_catalog.json")[exchange_getters["implementation"]]["functions"]
assert all(next(row for row in getter_functions if row["selector"] == selector)["reconstructed_signature"] == signature
           for selector, signature in exchange_getters["selector_reconstructions"].items())
assert all(row["selector"] not in exchange_getters["selector_reconstructions"]
           for row in unresolved["unmatched_selector_candidates"])
price_view = read("exchange_liquidation_price_behavior.json")
assert price_view["selector"] == "0x50c23fab"
assert price_view["sample_count"] == price_view["matched_formula_count"] == 26
assert price_view["fork_boundary_count"] == 4
assert price_view["active_count"] == 4
assert next(row for row in unresolved["unmatched_selector_candidates"]
            if row["role"] == "exchange_implementation" and row["selector"] == price_view["selector"])["behavior_evidence"] == "exchange_liquidation_price_behavior.json"
unit_scales = read("exchange_unit_scales_behavior.json")
assert unit_scales["call_count"] == unit_scales["matched_count"] == 40
assert unit_scales["pinned_slot3"] == 10**12 and unit_scales["pinned_slot5"] == 10**10
assert unit_scales["withdrawal_core_amount_checked"] == 19900000000
assert all(next(row for row in unresolved["unmatched_selector_candidates"]
                if row["role"] == "exchange_implementation" and row["selector"] == selector)["behavior_evidence"] == "exchange_unit_scales_behavior.json"
           for selector in ("0x31a39849", "0x70f75ff5", "0x2dcc7fce", "0xbacd9ea0"))
small_views = read("exchange_small_views_behavior.json")
assert small_views["selector_reconstructions"] == {"0x18715c9a": "stakerLpExcessToDistribute()"}
assert small_views["excess_nested_selector"] == "0xae745703"
assert small_views["override_case_count"] == 5
assert small_views["constant_outputs"] == {"0x6d60ae8e": "1000000000", "0xaf210ecc": "25",
                                            "0xfdfd905d": "1000000000000000000", "0xff3bc415": "64"}
assert next(row for row in catalog[small_views["implementation"]]["functions"]
            if row["selector"] == "0x18715c9a")["reconstructed_signature"] == "stakerLpExcessToDistribute()"
assert not any(row["selector"] == "0x18715c9a" and row["role"] == "exchange_implementation"
               for row in unresolved["unmatched_selector_candidates"])
assert {row["selector"] for row in unresolved["unmatched_selector_candidates"]
        if row.get("behavior_evidence") == "exchange_small_views_behavior.json"} == {
    "0x6d60ae8e", "0xaf210ecc", "0xfdfd905d", "0xff3bc415"}
fixed_replay = json.loads((ROOT / "artifacts" / "fixed_revert_local" / "replay.json").read_text())
assert fixed_replay["block_hash"] == manifest["block_hash"] and fixed_replay["canonical_call_count"] == 24
assert fixed_replay["forge_result"] == "12 passed, 0 failed"
assert fixed_replay["test_source_sha256"] == hashlib.sha256(TEST_SOURCE.encode()).hexdigest()
assert len(fixed_replay["test_names"]) == 12
assert all(fixed_replay["runtime_hashes"][name]["sha256"] == contracts[row["address"]]["sha256"]
           for name, row in fixed_replay["runtime_hashes"].items())
assert {row["selector"]: row["error_selector"] for row in unresolved["fixed_revert_paths"]} == fixed_replay["expected_revert_selectors"]
assert all(row["local_replay_evidence"] == "../../artifacts/fixed_revert_local/replay.json"
           for row in unresolved["fixed_revert_paths"])
disabled_paths = read("exchange_disabled_paths_behavior.json")
assert set(disabled_paths["selector_behaviors"]) == {"0x1afd17e9", "0x63ca348f", "0x58d3ec6a"}
assert disabled_paths["error_selector"] == "0x58f03bf7"
assert [disabled_paths["selector_behaviors"][selector]["canonical_calldata_bytes"]
        for selector in ("0x1afd17e9", "0x63ca348f")] == [132, 164]
assert disabled_paths["selector_behaviors"]["0x58d3ec6a"]["canonical_empty_array_calldata_bytes"] == 68
assert disabled_paths["selector_behaviors"]["0x58d3ec6a"]["public_signature_candidate"] == "close(uint256[])"
assert {row["selector"] for row in unresolved["fixed_revert_paths"]} == {"0xfb9f1009", "0x1afd17e9", "0x63ca348f", "0x58d3ec6a", "0x17a1678f", "0xfe16eae8", "0xdb006a75", "0x7c7df7b4", "0xa694fc3a", "0x2e17de78", "0x4e71d92d", "0xe4fc6b6d"}
legacy_stubs = read("legacy_initializer_stubs_behavior.json")
assert legacy_stubs["pin"] == manifest["block"] and legacy_stubs["block_hash"] == manifest["block_hash"]
assert legacy_stubs["error_selector"] == "0xb7b2509c"
assert {role: row["selector"] for role, row in legacy_stubs["entries"].items()} == {
    "staking_implementation": "0xc0c53b8b", "batch_executor_implementation": "0xc0c53b8b",
    "deposit_proxy_factory_implementation": "0xc4d66de8"}
assert all(manifest["contracts"][row["address"]]["sha256"] == row["runtime_sha256"]
           for row in legacy_stubs["entries"].values())
assert {(row["role"], row["selector"], row["error_selector"])
        for row in unresolved["bytecode_proven_initializer_stubs"]} == {
    (role, entry["selector"], legacy_stubs["error_selector"])
    for role, entry in legacy_stubs["entries"].items()}
assert coverage["summary"]["active_rows_with_pinned_bytecode_fixed_revert"] == 3
assert all("legacy_initializer_stubs_behavior.json" in next(row for row in coverage["rows"]
           if row["role"] == role and row["selector"] == entry["selector"])["linked_behavior_artifacts"]
           for role, entry in legacy_stubs["entries"].items())
assert {row["selector"] for row in unresolved["unmatched_selector_candidates"]
        if row.get("behavior_evidence") == "exchange_disabled_paths_behavior.json"} == set()
assert next(row for row in read("error_candidates.json")[disabled_paths["implementation"]]["candidates"]
            if row["selector"] == "0x58f03bf7")["status"] == "bytecode_verified_revert_selector"
session_disabled = read("session_disabled_selector_behavior.json")
assert session_disabled["selector"] == "0x17a1678f"
assert session_disabled["arguments"] == ["address", "uint64", "address"]
assert session_disabled["error_selector"] == "0xd2dd8531"
assert "session_disabled_selector_behavior.json" in next(row for row in coverage["rows"]
            if row["role"] == "session_key_manager_implementation" and row["selector"] == "0x17a1678f")["linked_behavior_artifacts"]
assert next(row for row in read("error_candidates.json")[session_disabled["implementation"]]["candidates"]
            if row["selector"] == "0xd2dd8531")["status"] == "bytecode_verified_revert_selector"
mapping35 = read("exchange_mapping35_view_behavior.json")
assert mapping35["selector"] == "0xc8372577" and mapping35["mapping_base_slot"] == 35
assert mapping35["return_bytes"] == 128 and len(mapping35["return_layout"]) == 4
assert mapping35["saved_state_write_count_for_keys_0_and_1"] == 0
assert mapping35["saved_key_0_zero_prestates"] >= 5
assert next(row for row in unresolved["unmatched_selector_candidates"]
            if row["role"] == "exchange_implementation" and row["selector"] == "0xc8372577")["behavior_evidence"] == "exchange_mapping35_view_behavior.json"
instrument_creation = read("exchange_instrument_creation_behavior.json")
assert instrument_creation["selector"] == "0xc88bbcf3"
assert instrument_creation["returned_instrument_id"] == 0
assert instrument_creation["instrument_mapping_base_slot"] == 7
assert instrument_creation["market_fields_mapping_base_slot"] == 36
assert instrument_creation["count_slot"] == 8
assert instrument_creation["count_after"] == 1 and instrument_creation["pinned_count"] == 2
assert instrument_creation["second_registration_block"] == 47855387
assert instrument_creation["second_input_words"][2] == "1"
assert instrument_creation["second_evidence"].startswith("saved receipt, call trace, and state diff")
assert instrument_creation["historical_registration_count"] == 2
assert instrument_creation["second_returned_instrument_id"] == 1
assert instrument_creation["second_event_indexed_id"] == instrument_creation["second_event_data_value"] == 1
assert len(instrument_creation["second_trace_artifacts"]) == 4
assert all((ATLAS / path).exists() for path in instrument_creation["second_trace_artifacts"].values())
creation_replay = json.loads((ROOT / "artifacts" / "exchange_instrument_creation_local" / "replay.json").read_text())
assert instrument_creation["local_replay"] == "../../artifacts/exchange_instrument_creation_local/replay.json"
assert creation_replay["pin"] == manifest["block"] and creation_replay["block_hash"] == manifest["block_hash"]
assert creation_replay["source_sha256"] == hashlib.sha256(instrument_creation_test_source().encode()).hexdigest()
assert creation_replay["test_count"] == 8 == len(creation_replay["passed_tests"])
assert instrument_creation["word7_observed_width_bits"] == creation_replay["word7_observed_width_bits"] == 128
assert instrument_creation["sampled_owner_guard_order"] == creation_replay["owner_guard_order"]
assert {"testCreateOwnerGuardBeforeMostWidthChecks", "testCreateWord7ObservedBoundary"} <= set(creation_replay["passed_tests"])
assert creation_replay["successful_registration_cases"] == 7 and creation_replay["required_zero_rejection_cases"] == 5
assert {row["selector"] for row in instrument_creation["simulated_error_catalog"]} == {"0x30cd7471", "0xb0cb274d", "0x924d25e6"}
assert next(row for row in read("historical_event_catalog.json")["events"] if row["emitter"] == instrument_creation["exchange_proxy"] and row["topic0"] == instrument_creation["event_catalog"][0]["topic0"])["count_in_saved_receipts"] == 2
assert next(row for row in coverage["rows"] if row["role"] == "exchange_implementation" and row["selector"] == "0xc88bbcf3")["linked_behavior_artifacts"].count("../../artifacts/exchange_instrument_creation_local/replay.json") == 1
assert instrument_creation["event_catalog"][0]["reconstructed_signature"] == "InstrumentAdded(uint32,uint32)"
assert instrument_creation["selector_reconstructions"] == {"0xf28bbdb2": "instrumentCount()"}
assert next(row for row in catalog[instrument_creation["implementation"]]["functions"]
            if row["selector"] == "0xf28bbdb2")["reconstructed_signature"] == "instrumentCount()"
assert next(row for row in unresolved["unmatched_selector_candidates"]
            if row["role"] == "exchange_implementation" and row["selector"] == "0xc88bbcf3")["behavior_evidence"] == "exchange_instrument_creation_behavior.json"
market_keeper = read("exchange_market_keeper_behavior.json")
assert market_keeper["selector_reconstructions"] == {
    "0x060447aa": "setMarketKeeper(address)", "0x21f55a6c": "marketKeeper()"}
assert market_keeper["slot"] == 37 and market_keeper["owner_error_selector"] == "0x30cd7471"
assert market_keeper["historical_argument"] == "0x3721476de31190dc1af8908026abe20efe25cf99"
assert market_keeper["historical_slot_37_post"].endswith(market_keeper["historical_argument"][2:])
assert market_keeper["pinned_getter_output"].endswith(market_keeper["historical_argument"][2:])
assert {row["selector"]: row["reconstructed_signature"] for row in catalog[market_keeper["implementation"]]["functions"]
        if row["selector"] in market_keeper["selector_reconstructions"]} == market_keeper["selector_reconstructions"]
assert not any(row["selector"] == "0x060447aa" and row["role"] == "exchange_implementation"
               for row in unresolved["unmatched_selector_candidates"])
disabled_selector = read("exchange_disabled_selector_behavior.json")
assert disabled_selector["selector"] == "0xfb9f1009" and disabled_selector["canonical_probe_count"] == 4
assert disabled_selector["source_name_status"] == "unverified; selector hash match only"
assert disabled_selector["runtime_sha256"] == contracts[disabled_selector["implementation"]]["sha256"]
disabled_raw = json.loads((ROOT / "artifacts" / "exchange_disabled_selector" / "pinned_probes.json").read_text())
assert disabled_raw["function_body_hex"] == "5b503461046b57602036600319011261046b57610513613ec9565b5060405163d9d193d360e01b8152600490fd"
assert all(disabled_raw["cases"][name]["output"] == "0xd9d193d3" and not disabled_raw["cases"][name]["effect_ops"]
           for name in ("owner_market_0", "owner_market_1", "owner_market_max", "outsider_market_0"))
assert next(row for row in read("error_candidates.json")[disabled_selector["implementation"]]["candidates"]
            if row["selector"] == "0xd9d193d3")["simulated_revert_probe_count"] == 4
assert next(row for row in unresolved["reverted_view_probes"]
            if row["role"] == "exchange_implementation" and row["selector"] == "0xfb9f1009")["behavior_evidence"] == "exchange_disabled_selector_behavior.json"
instrument_admin = read("exchange_instrument_admin_behavior.json")
assert instrument_admin["setter_selector"] == "0x5ca4c0ea"
assert instrument_admin["probe_count"] == 9 and len(instrument_admin["successes"]) == 3
assert instrument_admin["revert_selectors"]["outsider_instrument_0"] == "0x30cd7471"
assert instrument_admin["revert_selectors"]["owner_invalid_instrument_2"] == "0x67207a88"
assert instrument_admin["revert_selectors"]["owner_rate_upper_bound"] == "0xb0cb274d"
admin_replay = json.loads((ROOT / "artifacts" / "exchange_instrument_admin_local" / "replay.json").read_text())
assert instrument_admin["local_replay"] == "../../artifacts/exchange_instrument_admin_local/replay.json"
assert admin_replay["block_hash"] == manifest["block_hash"] and admin_replay["forge_result"] == "9 passed, 0 failed"
assert len(admin_replay["test_names"]) == 9
assert admin_replay["test_source_sha256"] == hashlib.sha256(EXCHANGE_INSTRUMENT_ADMIN_TEST_SOURCE.encode()).hexdigest()
assert "../../artifacts/exchange_instrument_admin_local/replay.json" in next(row for row in coverage["rows"]
    if row["role"] == "exchange_implementation" and row["selector"] == instrument_admin["setter_selector"])["linked_behavior_artifacts"]
assert next(row for row in unresolved["unmatched_selector_candidates"]
            if row["role"] == "exchange_implementation" and row["selector"] == instrument_admin["setter_selector"])["simulation_evidence"] == "exchange_instrument_admin_behavior.json"
admin_errors = read("error_candidates.json")[instrument_admin["implementation"]]["candidates"]
assert {row["selector"]: row.get("reconstructed_signature") for row in admin_errors
        if row["selector"] in ("0x30cd7471", "0x67207a88")} == {
            "0x30cd7471": "NotOwner()", "0x67207a88": "InvalidInstrumentId()"}
assert next(row for row in read("static_event_candidates.json")[instrument_admin["implementation"]]["candidates"]
            if row["topic0"] == instrument_admin["event_topic0"])["status"] == "simulated_log_topic"
fee_rates = read("exchange_fee_rates_behavior.json")
assert fee_rates["probe_count"] == 7 and len(fee_rates["successes"]) == 3
assert fee_rates["each_rate_max_inclusive"] == 5 * 10**17
assert fee_rates["historical_liquidation_fee_pairs_consistent"] == 6
assert fee_rates["selector_reconstructions"] == {
    "0xe538b280": "setFeeRates(uint256,uint256,uint256)",
    "0x5fb3b1b5": "liquidationFeeRate()"}
assert fee_rates["event_catalog"][0]["reconstructed_signature"] == "FeeRatesUpdated(uint256,uint256,uint256)"
fee_functions = read("selector_catalog.json")[fee_rates["implementation"]]["functions"]
assert all(next(row for row in fee_functions if row["selector"] == selector)["reconstructed_signature"] == signature
           for selector, signature in fee_rates["selector_reconstructions"].items())
fee_errors = read("error_candidates.json")[fee_rates["implementation"]]["candidates"]
assert next(row for row in fee_errors if row["selector"] == "0xcd4e6167")["reconstructed_signature"] == "FeeTooHigh()"
assert next(row for row in fee_errors if row["selector"] == "0x30cd7471")["simulated_revert_probe_count"] == 6
assert next(row for row in read("static_event_candidates.json")[fee_rates["implementation"]]["candidates"]
            if row["topic0"] == fee_rates["event_topic0"])["reconstructed_signature"] == "FeeRatesUpdated(uint256,uint256,uint256)"
assert next(row for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
            if row["role"] == "exchange_implementation" and row["selector"] == fee_rates["setter_selector"])["behavior_evidence"] == "exchange_fee_rates_behavior.json"
fee_effects = read("exchange_fee_effects_behavior.json")
assert fee_effects["case_count"] == 10
assert fee_effects["prior_baseline_logs_match"] and fee_effects["prior_baseline_storage_match"]
assert fee_effects["slot23_or_24_zero_same_as_baseline"]
assert fee_effects["cases"]["short_slot25_one"]["total_fee"] == "315"
assert fee_effects["cases"]["short_slot25_one"]["staker_fee"] == "157"
assert fee_effects["cases"]["short_slot25_one"]["dev_fee"] == "158"
assert fee_effects["cases"]["long_slot25_zero"]["total_fee"] == "0"
assert next(row for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
            if row["role"] == "exchange_implementation" and row["selector"] == "0x415f1240")["fee_effect_evidence"] == "exchange_fee_effects_behavior.json"
close_fee_effects = read("exchange_close_fee_effects_behavior.json")
assert close_fee_effects["case_count"] == 16
assert close_fee_effects["queued_case_count"] == close_fee_effects["direct_case_count"] == 8
assert close_fee_effects["historical_baseline_matches"] and close_fee_effects["direct_historical_baseline_matches"]
assert close_fee_effects["slot23_and_25_variants_same_exchange_logs_and_storage"]
assert close_fee_effects["cases"]["slot24_one"]["fee"] == "7"
assert close_fee_effects["direct_cases"]["slot24_one"]["fee"] == "6"
assert "exchange_close_fee_effects_behavior.json" in next(row for row in coverage["rows"]
            if row["role"] == "exchange_implementation" and row["selector"] == "0x48ee5e08")["linked_behavior_artifacts"]
negative_close_fee = read("exchange_negative_close_fee_behavior.json")
assert negative_close_fee["case_count"] == 10
assert negative_close_fee["historical_baseline_logs_match"]
assert negative_close_fee["historical_baseline_contract_state_match"]
assert negative_close_fee["positive_fee_slot"] == 24 and negative_close_fee["negative_fee_slot"] == 23
assert negative_close_fee["slot25_zero_same_logs_and_state"]
assert negative_close_fee["negative_user_credit_independent_of_fee"]
assert negative_close_fee["cases"]["slot23_zero"][1]["fee"] == "0"
assert negative_close_fee["cases"]["slot23_one"][1]["fee"] == "33"
assert negative_close_fee["cases"]["slot23_three"][1]["fee"] == "100"
assert negative_close_fee["cases"]["slot23_double"][1]["fee"] == "1335435407586015023"
assert negative_close_fee["cases"]["slot24_zero"][0]["fee"] == "0"
assert negative_close_fee["cases"]["slot25_zero"] == negative_close_fee["cases"]["baseline"]
assert all(int(case[1]["tokenomics_mint_basis"]) + int(case[1]["fee"]) ==
           -int(case[1]["adjusted_pnl"]) for case in negative_close_fee["cases"].values())
assert next(row for row in unresolved["unmatched_selector_candidates"]
            if row["role"] == "exchange_implementation" and row["selector"] == "0xf1a8786c")["negative_close_fee_effect_evidence"] == "exchange_negative_close_fee_behavior.json"
pair_params = read("exchange_pair_params_behavior.json")
assert pair_params["pinned_pair"] == ["10000000000000000000", "1000000000000000000000"]
assert pair_params["historical_pair"] == ["1000000000000000000", "5000000000000000000000"]
assert pair_params["historical_update_count"] == 4
assert [row["pair"] for row in pair_params["historical_updates"]] == [
    ["1000000000000000000", "5000000000000000000000"],
    ["100000000000000000000", "10000000000000000000000"],
    ["10000000000000000000", "10000000000000000000000"],
    ["10000000000000000000", "1000000000000000000000"],
]
assert pair_params["probe_count"] == 5 and pair_params["outsider_revert"] == "0x989c4c7c"
assert next(row for row in unresolved["observed_events_without_resolved_signature"]
            if row["topic0"] == pair_params["event_topic0"])["behavior_evidence"] == "exchange_pair_params_behavior.json"
report_names = read("exchange_report_names_behavior.json")
assert report_names["selector_reconstructions"]["0xcd2d3811"] == "setStakerFeeRecipient(address)"
assert report_names["selector_reconstructions"]["0xe1f9209b"] == "stakerFeeRecipient()"
assert report_names["selector_reconstructions"]["0x138e9de2"] == "queueHarvestAvailable()"
assert report_names["event_catalog"][0]["reconstructed_signature"] == "StakerFeeRecipientUpdated(address)"
side_bucket = read("exchange_side_bucket_behavior.json")
assert side_bucket["selector_reconstructions"] == {"0x9274682e": "sideBucket()"}
assert side_bucket["event_catalog"][0]["reconstructed_signature"] == "SideBucketUpdated(uint256)"
assert [int(row["slot_27_post"]) for row in side_bucket["historical_transitions"]] == [400296219202209635129, 0]
assert all(row["topic0"] != core_withdrawal["event_catalog"][0]["topic0"]
           for row in unresolved["observed_events_without_resolved_signature"])
assert all(row["topic0"] != report_names["event_catalog"][0]["topic0"]
           for row in unresolved["observed_events_without_resolved_signature"])
assert all(row["topic0"] != paper_admin["event_catalog"][0]["topic0"]
           for row in unresolved["observed_events_without_resolved_signature"])
assert all(row["topic0"] not in {event["topic0"] for event in staker_push["event_catalog"]}
           for row in unresolved["observed_events_without_resolved_signature"])
assert all(row["topic0"] != batch_summary["summary_topic0"]
           for row in unresolved["observed_events_without_resolved_signature"])
assert any(row["topic0"] == market_fields["event_topic0"] and row.get("behavior_evidence") == "exchange_market_fields_behavior.json"
           for row in unresolved["observed_events_without_resolved_signature"])
assert {row["selector"] for row in unresolved["unmatched_selector_candidates"]
        if row.get("behavior_evidence") == "exchange_market_fields_behavior.json"} == {
    "0x628a9fd6", "0xcb163b03", "0xf37d3c4f"}
assert len(unresolved["replay_storage_mismatches"]) == 0
timelock = read("timelock_operations.json")
assert timelock["min_delay_seconds"] == 604800 and len(timelock["operations"]) == 2
assert [x["is_ready_at_pin"] for x in timelock["operations"]] == [True, False]
assert [x["is_done_at_pin"] for x in timelock["operations"]] == [False, False]
behavior = read("timelock_behavior.json")
timelock_names = read("timelock_selector_names_behavior.json")
assert timelock_names["pin"] == manifest["block"] and timelock_names["block_hash"] == manifest["block_hash"]
assert timelock_names["runtime_sha256"] == contracts[timelock_names["timelock"]]["sha256"]
assert len(timelock_names["selector_reconstructions"]) == 15
assert {row["selector"]: row["reconstructed_signature"]
        for row in catalog[timelock_names["timelock"]]["functions"]} == timelock_names["selector_reconstructions"]
assert behavior["pin"] == 48902346 and len(behavior["scheduled_operations"]) == 2
assert all(x["hash_operation_matches_scheduled_id"] and x["hash_formula_matches_scheduled_id"] for x in behavior["scheduled_operations"])
assert all(not x["predecessor_done_at_pin"] and x["predecessor_mapping_slot"] not in x["root_sload_slots_at_ready"] for x in behavior["scheduled_operations"])
assert behavior["scheduled_operations"][0]["execute_owner_at_pin"]["success"]
assert behavior["scheduled_operations"][1]["execute_owner_at_pin"]["revert_selector"] == "0xf800799b"
assert behavior["batch_probe"]["hash_formula_matches_call"] and behavior["batch_probe"]["execute_with_hypothetical_scheduled_state_at_ready"]["success"]
assert behavior["batch_probe"]["execute_outsider_with_hypothetical_scheduled_state"]["revert_selector"] == "0x30cd7471"
assert int(behavior["batch_probe"]["simulated_schedule_storage_post"][behavior["batch_probe"]["mapping_slot"]], 16) == behavior["batch_probe"]["hypothetical_ready_timestamp"]
assert behavior["status_getter_boundary_probes"]["before_ready"] == {"pending": 1, "ready": 0}
assert behavior["status_getter_boundary_probes"]["at_ready"] == {"pending": 0, "ready": 1}
assert len(behavior["simulated_error_catalog"]) == 10
assert len(behavior["event_catalog"]) == 7 and all(x["public_signature_candidates"] or x["reconstructed_signature"] for x in behavior["event_catalog"])
assert all(x["execution"]["revert_selector"] == "0x15fcd675" and not x["timelock_storage_post"] for x in behavior["failure_probes"].values())
assert int(behavior["multi_target_success_probe"]["execution"]["events"][0]["data"], 16) == 2
assert behavior["batch_value_probe"]["3"]["success"]
assert [x["value"] for x in behavior["batch_value_probe"]["3"]["child_calls"]] == ["0x1", "0x2"]
assert behavior["batch_value_probe"]["2"]["revert_selector"] == behavior["batch_value_probe"]["4"]["revert_selector"] == "0xaa7feadc"
multisig = read("multisig_behavior.json")
assert multisig["required_confirmations"] == 2 and len(multisig["signers"]) == 3
assert multisig["current_epoch"] == 1 and multisig["transaction_count"] == 7
assert all(x["hash_formula_matches"] for x in multisig["records"])
assert [x["status"] for x in multisig["records"]] == [1, 1, 2, 1, 0, 1, 1]
assert len(multisig["selector_reconstructions"]) == 13
assert len(multisig["event_catalog"]) == 4 and len(multisig["simulated_error_catalog"]) == 10
assert multisig["confirm_probes"]["other_signer_one"]["success"]
assert multisig["confirm_probes"]["target_failure"]["revert_selector"] == "0x15fcd675"
assert not multisig["confirm_probes"]["target_failure_storage_post"]
assert multisig["revoke_probes"]["submitter_after_epoch_change"]["success"]
multisig_replays = read("multisig_replays.json")
assert multisig_replays["transaction_count"] == 13
assert multisig_replays["match_counts"] == {"call_skeleton_match": 13, "event_multiset_match": 13, "storage_post_match": 13}
assert all(x["call_skeleton_match"] and x["event_multiset_match"] and x["storage_post_match"] for x in multisig_replays["rows"])

batch_control = read("batch_control_behavior.json")
assert batch_control["pin"] == manifest["block"] and batch_control["block_hash"] == manifest["block_hash"]
assert batch_control["runtime_sha256"] == contracts[batch_control["implementation"]]["sha256"]
assert batch_control["historical_control_transactions"] == {
    "relayer_set": "0x303956400b3cd1c4ed86cf3644975a5f8b1ea2f3e487bad7da21d49689d52b6f",
    "owner_transfer": "0xd928f58d081c09d5600715814814b78ed5256ae3b1a54f11d822deaa9c0e2049"}
assert len(batch_control["selector_reconstructions"]) == 6
assert batch_control["simulated_control_selectors"] == ["0x0f71c8bc", "0x9ccae24e", "0xc0c53b8b"]
assert batch_control["locally_checked_existing_getters"] == ["0x6090cf16", "0xd5c539ce"]
assert batch_control["simulated_initializer_events"] == ["OwnerUpdated(address)", "AuthorizedRelayerUpdated(address,bool)"]
assert batch_control["slot0_layout"].startswith("Exchange address in bits 16..175")
assert {row["selector"]: row["reconstructed_signature"] for row in catalog[batch_control["implementation"]]["functions"]
        if row["selector"] in batch_control["selector_reconstructions"]} == batch_control["selector_reconstructions"]
batch_control_replay = json.loads((ROOT / "artifacts" / "batch_control_local" / "replay.json").read_text())
assert batch_control_replay["block_hash"] == manifest["block_hash"]
assert batch_control_replay["forge_result"] == "10 passed, 0 failed" and len(batch_control_replay["test_names"]) == 10
assert batch_control_replay["test_source_sha256"] == hashlib.sha256(BATCH_CONTROL_TEST_SOURCE.encode()).hexdigest()
assert {row["selector"] for row in read("error_candidates.json")[batch_control["implementation"]]["candidates"]
        if row["status"] == "simulated_revert_selector"} == {"0x0dc149f0", "0x17fb2066", "0x30cd7471", "0x3f733c4f", "0x651ab1b3", "0xb7b2509c", "0xc031a0df"}
assert next(row for row in read("historical_event_catalog.json")["events"]
            if row["emitter"] == batch_control["address"] and row["topic0"] == batch_control["event_catalog"][0]["topic0"])["reconstructed_signature"] == "AuthorizedRelayerUpdated(address,bool)"
assert next(row for row in read("historical_event_catalog.json")["events"]
            if row["emitter"] == batch_control["address"] and row["topic0"] == batch_control["event_catalog"][1]["topic0"])["reconstructed_signature"] == "OwnerUpdated(address)"
assert (ATLAS / "batch_control_pseudocode.md").exists()
assert {row["topic0"]: row["reconstructed_signature"]
        for row in read("static_event_candidates.json")[batch_control["implementation"]]["candidates"]
        if row.get("reconstructed_signature") and row["topic0"] in {e["topic0"] for e in batch_control["event_catalog"]}} == {
    row["topic0"]: row["reconstructed_signature"] for row in batch_control["event_catalog"]}

batch = read("batch_executor_behavior.json")
assert batch["selector_reconstructions"]["0x251fb27d"] == "execute((address,bytes,bool,bytes32,bytes32)[])"
field4_replay = json.loads((ROOT / "artifacts" / "batch_executor_field4_local" / "replay.json").read_text())
assert batch["field4_local_replay_artifact"] == "../../artifacts/batch_executor_field4_local/replay.json"
assert field4_replay["pin"] == manifest["block"] and field4_replay["block_hash"] == manifest["block_hash"]
assert field4_replay["source_sha256"] == hashlib.sha256(batch_field4_test_source().encode()).hexdigest()
assert field4_replay["test_count"] == 4 == len(field4_replay["passed_tests"])
assert [field4_replay[x] for x in ("successful_call_cases", "continued_failure_cases", "rejected_call_cases", "noncontinuing_failure_cases")] == [5, 5, 5, 1]
assert next(row for row in coverage["rows"] if row["role"] == "batch_executor_implementation" and row["selector"] == "0x251fb27d")["linked_behavior_artifacts"].count("../../artifacts/batch_executor_field4_local/replay.json") == 1
allowlist_replay = json.loads((ROOT / "artifacts" / "batch_allowlist_local" / "replay.json").read_text())
assert batch["allowlist_local_replay_artifact"] == "../../artifacts/batch_allowlist_local/replay.json"
assert allowlist_replay["pin"] == manifest["block"] and allowlist_replay["block_hash"] == manifest["block_hash"]
assert allowlist_replay["targets"] == BATCH_ALLOWLIST_TARGETS
assert allowlist_replay["candidate_selectors"] == batch_allowlist_candidates(catalog, (ATLAS / contracts[batch["implementation"]]["runtime_file"]).read_text().strip())
assert allowlist_replay["source_sha256"] == hashlib.sha256(batch_allowlist_test_source(allowlist_replay["candidate_selectors"]).encode()).hexdigest()
assert allowlist_replay["test_count"] == 4 and allowlist_replay["tested_target_selector_pairs"] == 1048
assert allowlist_replay["accepted_pair_count"] == 8 and allowlist_replay["observed_historical_pairs_match"]
assert allowlist_replay["accepted_by_target"] == {"exchange": ["0x2792e706", "0x8d09f23f", "0xec6783f0"], "session": ["0x5f76a1d6"], "staking": ["0x83115825", "0x9c96d4a1", "0xf0355460", "0xfa2871b5"], "other": []}
assert next(row for row in coverage["rows"] if row["role"] == "batch_executor_implementation" and row["selector"] == "0x251fb27d")["linked_behavior_artifacts"].count("../../artifacts/batch_allowlist_local/replay.json") == 1
assert len(batch["traced_batches"]) == 37
assert sum(len(x["intents"]) for x in batch["traced_batches"]) == 161
assert batch["recent_window"]["batches"] == 466
assert batch["recent_window"]["call_results"] == 1272
assert batch["recent_window"]["successful_calls"] == 1244
assert batch["recent_window"]["failed_calls"] == 28
assert batch["recent_window"]["failed_calls_with_matching_saved_trace"] == 28
assert len(batch["event_catalog"]) == 3 and len(batch["error_catalog"]) == 2
assert all(x["summary_fields"][:3] == [len(x["intents"]), sum(y["succeeded"] for y in x["intents"]), sum(not y["succeeded"] for y in x["intents"])] for x in batch["traced_batches"])
probes = read("batch_executor_probes.json")["probes"]
assert len(probes) == 8
assert probes["empty_authorized"]["root_error"] is None
assert probes["empty_unauthorized"]["root_output"] == "0x17fb2066"
assert probes["failed_call_continue_false"]["root_output"].startswith("0x651ab1b3")
assert all(not probes[x]["inner_calls"] for x in ("invalid_target", "invalid_selector"))
batch_impl = next(x for x in catalog.values() if x["role"] == "batch_executor_implementation")
assert next(x for x in batch_impl["functions"] if x["selector"] == "0x251fb27d")["reconstructed_signature"] == batch["selector_reconstructions"]["0x251fb27d"]
assert next(x for x in batch_impl["functions"] if x["selector"] == "0x251fb27d")["state_mutability"] == "nonpayable"
assert next(x for x in events if x["emitter_role"] == "batch_executor_proxy" and x["topic0"].startswith("0x8a23ef"))["reconstructed_signature"] == "CallExecuted(bytes32,uint256,bytes32,bool,bytes)"

exchange_pause = read("exchange_pause_behavior.json")
assert exchange_pause["pin"] == manifest["block"] and exchange_pause["block_hash"] == manifest["block_hash"]
assert exchange_pause["runtime_sha256"] == contracts[exchange_pause["implementation"]]["sha256"]
assert len(exchange_pause["selector_reconstructions"]) == 6
assert exchange_pause["pause_storage_slot"] == 29 and exchange_pause["market_pause_mapping_base_slot"] == 35
assert exchange_pause["market_pause_oracle_asset"] == 0
assert exchange_pause["market_pause_mock_bid_ask"] == [1000000000, 1100000000]
assert exchange_pause["historical_guardian_transaction"] == "0x24b978eacabde6c6b459011ce8c78b25bf97a74a41d51a486324492fdba48c21"
assert {row["selector"]: row["reconstructed_signature"] for row in catalog[exchange_pause["implementation"]]["functions"]
        if row["selector"] in exchange_pause["selector_reconstructions"]} == exchange_pause["selector_reconstructions"]
exchange_pause_replay = json.loads((ROOT / "artifacts" / "exchange_pause_local" / "replay.json").read_text())
assert exchange_pause_replay["block_hash"] == manifest["block_hash"]
assert exchange_pause_replay["forge_result"] == "13 passed, 0 failed" and len(exchange_pause_replay["test_names"]) == 13
assert exchange_pause_replay["test_source_sha256"] == hashlib.sha256(EXCHANGE_PAUSE_TEST_SOURCE.encode()).hexdigest()
assert {row["selector"] for row in read("error_candidates.json")[exchange_pause["implementation"]]["candidates"]
        if row["status"] == "simulated_revert_selector"} >= {"0x0d240815", "0x30cd7471", "0x49199fb6", "0x67207a88"}
assert next(row for row in read("historical_event_catalog.json")["events"]
            if row["emitter"] == exchange_pause["exchange_proxy"] and row["topic0"] == exchange_pause["event_catalog"][0]["topic0"])["reconstructed_signature"] == "PauseGuardianUpdated(address)"
assert {row["status"] for row in read("static_event_candidates.json")[exchange_pause["implementation"]]["candidates"]
        if row["topic0"] in {event["topic0"] for event in exchange_pause["event_catalog"][1:]}} == {"simulated_log_topic"}
assert (ATLAS / "exchange_pause_pseudocode.md").exists()

instrument_limit = read("exchange_instrument_limit_behavior.json")
assert instrument_limit["pin"] == manifest["block"] and instrument_limit["block_hash"] == manifest["block_hash"]
assert instrument_limit["implementation"] == exchange_pause["implementation"]
assert instrument_limit["selector"] == "0xd7c7e5fb"
assert instrument_limit["storage_mapping_base"] == 7
assert instrument_limit["word0_replaced_bits"] == [224, 255]
assert instrument_limit["word1_replaced_bits"] == [0, 119]
instrument_limit_replay = json.loads((ROOT / "artifacts" / "exchange_instrument_limit_local" / "replay.json").read_text())
assert instrument_limit_replay["block_hash"] == manifest["block_hash"]
assert instrument_limit_replay["forge_result"] == "10 passed, 0 failed" and len(instrument_limit_replay["test_names"]) == 10
assert instrument_limit_replay["test_source_sha256"] == hashlib.sha256(EXCHANGE_INSTRUMENT_LIMIT_TEST_SOURCE.encode()).hexdigest()
assert (ATLAS / "exchange_instrument_limit.md").exists()

exchange_initializer = read("exchange_initializer_behavior.json")
assert exchange_initializer["pin"] == manifest["block"] and exchange_initializer["block_hash"] == manifest["block_hash"]
assert exchange_initializer["implementation"] == exchange_pause["implementation"]
assert exchange_initializer["selector"] == "0xc0c53b8b"
assert exchange_initializer["initial_storage"]["23"] == exchange_initializer["initial_storage"]["24"] == exchange_initializer["initial_storage"]["25"] == "20000000000000000"
assert [row["token_decimals"] for row in exchange_initializer["tested_decimal_pairs"]] == [6, 8, 18]
assert {row["selector"]: row["probe_paths"] for row in exchange_initializer["simulated_error_catalog"]} == {
    "0x0dc149f0": ["testInitializedCall"],
    "0x6a426315": ["testFreshNineteenDecimals"],
}
exchange_initializer_replay = json.loads((ROOT / "artifacts" / "exchange_initializer_local" / "replay.json").read_text())
assert exchange_initializer_replay["block_hash"] == manifest["block_hash"]
assert exchange_initializer_replay["forge_result"] == "6 passed, 0 failed" and len(exchange_initializer_replay["test_names"]) == 6
assert exchange_initializer_replay["runtime_hashes"]["Implementation"] == contracts[exchange_initializer["implementation"]]["sha256"]
assert exchange_initializer_replay["test_source_sha256"] == hashlib.sha256(EXCHANGE_INITIALIZER_TEST_SOURCE.encode()).hexdigest()
assert (ATLAS / "exchange_initializer.md").exists()

exchange_adapters = read("exchange_library_adapters_behavior.json")
assert exchange_adapters["pin"] == manifest["block"] and exchange_adapters["block_hash"] == manifest["block_hash"]
assert exchange_adapters["implementation"] == exchange_pause["implementation"]
assert exchange_adapters["prepend_word"] == 15 and exchange_adapters["parent_result_words"] == 3
assert exchange_adapters["adapters"] == {
    "0x4a4d9eea": "0xca02ff91", "0xae4daf4e": "0x2448a553",
    "0x753a369c": "0x3cf4208d", "0x827ad94c": "0x32db40c9"}
assert exchange_adapters["append_word"] == {"0xae4daf4e": str(10**18), "0x753a369c": str(10**18)}
exchange_adapters_replay = json.loads((ROOT / "artifacts" / "exchange_library_adapters_local" / "replay.json").read_text())
assert exchange_adapters_replay["block_hash"] == manifest["block_hash"]
assert exchange_adapters_replay["forge_result"] == "7 passed, 0 failed" and len(exchange_adapters_replay["test_names"]) == 7
assert exchange_adapters_replay["test_source_sha256"] == hashlib.sha256(EXCHANGE_ADAPTERS_TEST_SOURCE.encode()).hexdigest()
assert exchange_adapters_replay["runtime_hashes"]["Library"] == contracts[exchange_adapters["linked_library"]]["sha256"]
assert (ATLAS / "exchange_library_adapters.md").exists()
queue_merge = read("exchange_library_queue_merge_behavior.json")
queue_merge_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_merge_local" / "replay.json").read_text())
assert queue_merge["pin"] == manifest["block"] and queue_merge["block_hash"] == manifest["block_hash"]
assert queue_merge["selectors"] == {
    "forward": {"exchange": "0x753a369c", "library": "0x3cf4208d"},
    "reverse": {"exchange": "0x827ad94c", "library": "0x32db40c9"}}
assert queue_merge["case_count"] == 10 and queue_merge_replay["forge_result"] == "10 passed, 0 failed"
assert queue_merge_replay["test_source_sha256"] == hashlib.sha256(exchange_queue_merge_test_source().encode()).hexdigest()
assert queue_merge_replay["runtime_hashes"]["Library"] == contracts[queue_merge["linked_library"]]["sha256"]
assert [row.get("returned") for row in queue_merge_replay["local_cases"]] == [
    [1, 500, 102], [1, 500, 101], [1, 300, 102], [1, 700, 101],
    None, [2, 1000, 103], [2, 1000, 103], None, [2, 1800, 101], [2, 1800, 101]]
assert [row.get("revert_selector") for row in queue_merge_replay["local_cases"] if row.get("revert_selector")] == ["0x5b6d2b7a"] * 2
assert queue_merge["three_node_limit_boundary"]["needed_merges"] == 2
assert queue_merge["simulated_error_catalog"][0]["probe_paths"] == [
    "testQueueMergeThreeForwardLowLimit", "testQueueMergeThreeReverseLowLimit"]
library_merge_error = next(row for row in read("error_candidates.json")[queue_merge["linked_library"]]["candidates"]
                           if row["selector"] == "0x5b6d2b7a")
assert library_merge_error["status"] == "simulated_revert_selector"
assert library_merge_error["simulated_revert_probe_count"] == 5
assert library_merge_error["behavior_evidence"] == "exchange_library_queue_merge_behavior.json"
assert library_merge_error["local_replay_evidence"] == "../../artifacts/exchange_library_queue_merge_local/replay.json"
assert library_merge_error["additional_behavior_evidence"] == "exchange_library_queue_interleaved_behavior.json"
assert library_merge_error["additional_local_replay_evidence"] == "../../artifacts/exchange_library_queue_interleaved_local/replay.json"
assert {row["topic0"] for row in unresolved["simulated_events_without_resolved_signature"]} == {
    row["topic0"] for row in queue_merge["event_catalog"]}
assert (ATLAS / "exchange_library_queue_merge.md").exists()
queue_harvest_followup = read("exchange_library_queue_harvest_followup_behavior.json")
queue_harvest_followup_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_harvest_followup_local" / "replay.json").read_text())
assert queue_harvest_followup["pin"] == manifest["block"] and queue_harvest_followup["block_hash"] == manifest["block_hash"]
assert queue_harvest_followup["case_count"] == 11 and queue_harvest_followup_replay["forge_result"] == "11 passed, 0 failed"
assert queue_harvest_followup_replay["test_source_sha256"] == hashlib.sha256(exchange_queue_harvest_followup_test_source().encode()).hexdigest()
assert queue_harvest_followup_replay["runtime_hashes"]["Library"] == contracts[queue_harvest_followup["linked_library"]]["sha256"]
assert [(row["direction"], row["nodes"], row["harvest_limit"], row["paid"], row["global_head"])
        for row in queue_harvest_followup_replay["cases"]] == [
    ("forward", 2, 1, 0, 102), ("forward", 2, 2, 1000, 103), ("forward", 2, 3, 1000, 103),
    ("reverse", 2, 1, 1000, 103), ("forward", 3, 1, 0, 102), ("forward", 3, 2, 0, 103),
    ("forward", 3, 3, 2100, 104), ("forward", 3, 4, 2100, 104), ("reverse", 3, 1, 2100, 104),
    ("forward", 3, 3, 0, 101), ("forward", 3, 3, 1000, 103)]
assert (ATLAS / "exchange_library_queue_harvest_followup.md").exists()
queue_interleaved = read("exchange_library_queue_interleaved_behavior.json")
queue_interleaved_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_interleaved_local" / "replay.json").read_text())
assert queue_interleaved["pin"] == manifest["block"] and queue_interleaved["block_hash"] == manifest["block_hash"]
assert queue_interleaved["case_count"] == 7 and queue_interleaved_replay["forge_result"] == "7 passed, 0 failed"
assert queue_interleaved_replay["test_source_sha256"] == hashlib.sha256(exchange_queue_interleaved_test_source().encode()).hexdigest()
assert queue_interleaved_replay["runtime_hashes"]["Library"] == contracts[queue_interleaved["linked_library"]]["sha256"]
assert [row["merge"] for row in queue_interleaved_replay["cases"]] == [
    "forward_success", "forward_success", "forward_success", "reverse_revert", "reverse_revert",
    "reverse_revert", "reverse_success"]
assert [row["global_head"] for row in queue_interleaved_replay["cases"][:3]] == [102, 103, 104]
assert queue_interleaved["simulated_error_catalog"][0]["probe_paths"] == [
    "testQueueInterleavedReverseLimitOne", "testQueueInterleavedReverseLimitTwo",
    "testQueueInterleavedReverseLimitThree"]
assert (ATLAS / "exchange_library_queue_interleaved.md").exists()
count_merge = read("exchange_library_queue_count_merge_behavior.json")
count_merge_replay = json.loads((ROOT / "artifacts" / "exchange_library_queue_count_merge_local" / "replay.json").read_text())
assert count_merge["pin"] == manifest["block"] and count_merge["block_hash"] == manifest["block_hash"]
assert count_merge["case_count"] == 15 and count_merge_replay["forge_result"] == "15 passed, 0 failed"
assert count_merge_replay["test_source_sha256"] == hashlib.sha256(exchange_queue_count_merge_test_source().encode()).hexdigest()
assert count_merge_replay["runtime_hashes"]["Library"] == contracts[count_merge["linked_library"]]["sha256"]
assert count_merge["selectors"] == {"headward": {"exchange": "0x4a4d9eea", "library": "0xca02ff91"},
                                    "tailward": {"exchange": "0xae4daf4e", "library": "0x2448a553"}}
assert count_merge["measured_vectors"] == count_merge_replay["measured_vectors"]
assert count_merge["measured_vectors"]["tail_first_below_1e18"]["returned"] == [1, 10**18 - 1, 102]
assert count_merge["measured_vectors"]["tail_first_at_1e18"]["returned"] == [0, 0, 0]
assert count_merge["measured_vectors"]["interleaved_head"]["returned"] == [0, 0, 0]
assert count_merge["measured_vectors"]["interleaved_tail"]["returned"] == [1, 300, 103]
assert (ATLAS / "exchange_library_queue_count_merge.md").exists()
remaining = read("exchange_library_remaining_behavior.json")
remaining_replay = json.loads((ROOT / "artifacts" / "exchange_library_remaining_local" / "replay.json").read_text())
assert remaining["pin"] == manifest["block"] and remaining["block_hash"] == manifest["block_hash"]
assert remaining["runtime_sha256"] == contracts[remaining["library"]]["sha256"]
assert set(remaining["selector_behaviors"]) == {"0x18958ce2", "0x3f4e3626", "0xb67f3dd7"}
assert remaining["observed_abi_arguments"]["0x3f4e3626"] == "uint256,address,uint256"
assert remaining_replay["forge_result"] == "6 passed, 0 failed" and len(remaining_replay["math_vectors"]) == 40
assert remaining["math_formula_exact_vectors"] == 40 and remaining_replay["formula_mismatches"] == remaining["math_formula_mismatches"] == []
assert all(row["output"] == row["formula_output"] for row in remaining_replay["math_vectors"])
trace_path = ROOT / "artifacts" / "exchange_library_remaining_local" / remaining_replay["opcode_trace"]
assert remaining_replay["opcode_trace_sha256"] == hashlib.sha256(trace_path.read_bytes()).hexdigest()
trace_artifact = json.loads(trace_path.read_text())
assert trace_artifact["pin"] == manifest["block"] and trace_artifact["library"] == remaining["library"]
assert trace_artifact["calldata"] == "0xb67f3dd7" + "".join(f"{x:064x}" for x in remaining_replay["math_vectors"][17]["inputs"])
assert int(trace_artifact["trace"]["returnValue"], 16) == remaining_replay["math_vectors"][17]["output"]
for pc, depths in remaining["math_opcode_checkpoints"].items():
    steps = [row for row in trace_artifact["trace"]["structLogs"] if row["pc"] == int(pc, 16)]
    assert len(steps) == 1
    assert all(int(steps[0]["stack"][-1-int(depth)], 16) == value for depth, value in depths.items())
assert remaining["math_panic_branches"] == [
    {"input": "start=0,end=110", "selector": "0x4e487b71", "code": "0x12"},
    {"input": "prior=1e18+1", "selector": "0x4e487b71", "code": "0x11"}]
assert remaining_replay["math_vectors"][36]["inputs"][1:3] == [110, 100]
assert remaining_replay["math_vectors"][36]["output"] == 83333256944514467
assert remaining_replay["test_source_sha256"] == hashlib.sha256(EXCHANGE_LIBRARY_REMAINING_TEST_SOURCE.encode()).hexdigest()
assert remaining_replay["math_vectors"][6]["output"] == 90909008264537941
assert remaining_replay["math_vectors"][9]["output"] == 181818016529075882
assert all("exchange_library_remaining_behavior.json" in row["linked_behavior_artifacts"]
           for row in coverage["rows"] if row["role"] == "exchange_linked_library_live"
           and row["selector"] in remaining["selector_behaviors"])
assert "exchange_library_harvest_behavior.json" in next(row for row in coverage["rows"]
    if row["role"] == "exchange_linked_library_live" and row["selector"] == "0x79810ffe")["linked_behavior_artifacts"]
assert (ATLAS / "exchange_library_remaining.md").exists()
remaining_init_replay = json.loads((ROOT / "artifacts" / "remaining_initializers_local" / "replay.json").read_text())
assert remaining_init_replay["pin"] == manifest["block"] and remaining_init_replay["block_hash"] == manifest["block_hash"]
assert remaining_init_replay["forge_result"] == "7 passed, 0 failed" and len(remaining_init_replay["test_names"]) == 7
assert remaining_init_replay["test_source_sha256"] == hashlib.sha256(REMAINING_INITIALIZERS_TEST_SOURCE.encode()).hexdigest()
for role, filename, expected in (
    ("staking_implementation", "staking_initializers_behavior.json", {"0x0f71c8bc", "0xc0c53b8b"}),
    ("session_key_manager_implementation", "session_initializer_behavior.json", {"0x747b8a1c"}),
    ("tokenomics_implementation", "tokenomics_initializer_behavior.json", {"0x485cc955"}),
):
    behavior = read(filename)
    assert behavior["pin"] == manifest["block"] and behavior["block_hash"] == manifest["block_hash"]
    assert set(behavior["selector_behaviors"]) == expected
    assert behavior["runtime_sha256"] == contracts[behavior["implementation"]]["sha256"]
    for selector in expected:
        row = next(row for row in coverage["rows"] if row["role"] == role and row["selector"] == selector)
        assert "local_remaining_initializer_replay" in row["indexed_evidence"]
        assert filename in row["linked_behavior_artifacts"]
assert read("tokenomics_initializer_behavior.json")["selector_reconstructions"]["0x485cc955"] == "initialize(address,address)"
session_init = read("session_initializer_behavior.json")
assert session_init["selector_reconstructions"] == {"0x747b8a1c": "initialize(address,string,string,uint256,address)"}
assert session_init["fresh_state"]["domain_separator_historical"] == read("session_key_behavior.json")["domain_separator"]
creation = session_init["historical_creation"]
assert creation["transaction_hash"] == "0xe055509195f0ea1b9e30c366c3350d10470d8c1d145bfa51686b49134d36ffbe"
assert creation["decoded_arguments"]["name"] == "String" and creation["decoded_arguments"]["version"] == "1"
assert creation["decoded_arguments"]["chain_id"] == 999
trace = json.loads((ATLAS / creation["trace"]).read_text())
receipt = json.loads((ATLAS / creation["receipt"]).read_text())
assert trace["type"] == "CREATE" and trace["to"].lower() == session_init["session_proxy"]
assert trace["calls"][0]["type"] == "DELEGATECALL" and trace["calls"][0]["to"].lower() == session_init["implementation"]
assert trace["calls"][0]["input"].startswith("0x747b8a1c")
assert receipt["status"] == "0x1" and receipt["contractAddress"].lower() == session_init["session_proxy"]
assert [row["topics"][0].lower() for row in receipt["logs"]] == [row["topic0"] for row in session_init["event_catalog"]]
assert next(row for row in catalog[session_init["implementation"]]["functions"] if row["selector"] == "0x747b8a1c")["reconstructed_signature"] == session_init["selector_reconstructions"]["0x747b8a1c"]
session_constants = read("session_initializer_constants_behavior.json")
assert session_constants["pin"] == manifest["block"] and session_constants["block_hash"] == manifest["block_hash"]
assert session_constants["runtime_sha256"] == contracts[session_init["implementation"]]["sha256"]
assert session_constants["selector"] == "0x747b8a1c" and session_constants["name"] == "String" and session_constants["version"] == "1"
assert session_constants["name_hash_runtime_offset"] == 0xe5f and session_constants["version_hash_runtime_offset"] == 0xdff
assert session_constants["name_mismatch_jump_pc"] == 0x702 and session_constants["version_mismatch_jump_pc"] == 0x6f5
assert session_constants["mismatch_error_selector"] == "0xf50220aa"
session_coverage = next(row for row in coverage["rows"] if row["role"] == "session_key_manager_implementation" and row["selector"] == "0x747b8a1c")
assert "saved_creation_trace" in session_coverage["indexed_evidence"]
assert "session_initializer_constants_behavior.json" in session_coverage["linked_behavior_artifacts"]
assert all(not (row["role"] == "session_key_manager_implementation" and row["selector"] == "0x747b8a1c")
           for row in unresolved["state_changing_selectors_without_saved_historical_trace"])
assert (ATLAS / "session_initializer_constants.md").exists()
assert (ATLAS / "remaining_initializers.md").exists()


adapter_coverage = [row for row in coverage["rows"] if row["active_runtime_at_pin"]
                    and "local_exchange_library_adapter_replay" in row["indexed_evidence"]]
assert len(adapter_coverage) == 8 and all("exchange_library_adapters_behavior.json" in row["linked_behavior_artifacts"]
                                         for row in adapter_coverage)
merge_coverage = [row for row in coverage["rows"] if row["active_runtime_at_pin"]
                  and "local_exchange_library_queue_merge_replay" in row["indexed_evidence"]]
assert len(merge_coverage) == 4
assert all("exchange_library_queue_merge_behavior.json" in row["linked_behavior_artifacts"]
           and "../../artifacts/exchange_library_queue_merge_local/replay.json" in row["linked_behavior_artifacts"]
           for row in merge_coverage)
followup_coverage = [row for row in coverage["rows"] if row["active_runtime_at_pin"]
                     and "local_exchange_library_queue_harvest_followup_replay" in row["indexed_evidence"]]
assert len(followup_coverage) == 6
assert all("exchange_library_queue_harvest_followup_behavior.json" in row["linked_behavior_artifacts"]
           and "../../artifacts/exchange_library_queue_harvest_followup_local/replay.json" in row["linked_behavior_artifacts"]
           for row in followup_coverage)
interleaved_coverage = [row for row in coverage["rows"] if row["active_runtime_at_pin"]
                        and "local_exchange_library_queue_interleaved_replay" in row["indexed_evidence"]]
assert len(interleaved_coverage) == 7
assert all("exchange_library_queue_interleaved_behavior.json" in row["linked_behavior_artifacts"]
           and "../../artifacts/exchange_library_queue_interleaved_local/replay.json" in row["linked_behavior_artifacts"]
           for row in interleaved_coverage)
count_merge_coverage = [row for row in coverage["rows"] if row["active_runtime_at_pin"]
                        and "local_exchange_library_queue_count_merge_replay" in row["indexed_evidence"]]
assert len(count_merge_coverage) == 4
assert all("exchange_library_queue_count_merge_behavior.json" in row["linked_behavior_artifacts"]
           and "../../artifacts/exchange_library_queue_count_merge_local/replay.json" in row["linked_behavior_artifacts"]
           for row in count_merge_coverage)

exchange_interface = read("exchange_interface_evidence.json")
assert len(exchange_interface["functions"]) == 41 and len(exchange_interface["events"]) == 18
assert len(exchange_interface["event_catalog"]) == 16
assert sum(not x["fixture_indexing_matches_observation"] for x in exchange_interface["events"] if x["status"] != "topic_hash_only") == 10
assert exchange_interface["selector_reconstructions"]["0xdc8a47ef"] == "instruments(uint32)"
assert next(x for x in exchange_interface["functions"] if x["signature"] == "treasury()") ["output_types_status"].startswith("contradicted:")
exchange_words = read("exchange_storage_words.json")
assert exchange_words["block_hash"] == manifest["block_hash"]
exchange_storage = read("exchange_storage_behavior.json")
assert exchange_storage["historical_transition_count"] == 14
assert len(exchange_storage["historical_transitions"]) == 14
values = exchange_storage["getter_values"]
word22 = int(exchange_words["slots"]["22"], 16)
word26 = int(exchange_words["slots"]["26"], 16)
assert word22 & ((1 << 128) - 1) == values["totalBalances()"]
assert word22 >> 128 == values["totalLockedMargin()"]
assert word26 & ((1 << 128) - 1) == values["stakerFeeAccumulator()"]
assert word26 >> 128 == values["devFeeAccumulator()"]
assert values["totalQueued()"] == 0
assert values["treasury()"] - sum(values[x] for x in (
    "totalBalances()", "totalLockedMargin()", "stakerFeeAccumulator()",
    "devFeeAccumulator()")) == exchange_storage["lpBankrollAvailable_at_pin"]
availability = read("exchange_availability_behavior.json")
assert availability["case_count"] == 11 and availability["call_count"] == 22
assert availability["lp_formula"] == "0 if totalQueued > 0 else queueHarvestAvailable()"
exchange_position = read("exchange_position_layout.json")
assert exchange_position["sampled_open_events"] == exchange_position["post_diff_words_available"] == 25
assert exchange_position["sampled_transactions"] == 10
assert all(all(x["event_fields_match"].values()) for x in exchange_position["records"])
assert len(exchange_position["open_accounting"]) == 10
assert exchange_position["open_balance_pairs_checked"] == 23
assert all(x["total_balances_delta"] == -x["total_margin"] and x["total_locked_margin_delta"] == x["total_margin"] for x in exchange_position["open_accounting"])
assert exchange_position["signed_close_deactivations"] == 9
assert exchange_position["keeper_liquidation_deactivations"] == 6
assert len(exchange_position["deactivations"]) == 15
assert len(exchange_position["liquidation_accounting"]) == 2
assert sum(len(x["positions"]) for x in exchange_position["liquidation_accounting"]) == 6
assert all(y["staker_fee"] * 100 == y["dev_fee"] * 100 == y["margin"] for x in exchange_position["liquidation_accounting"] for y in x["positions"])
close_paths = read("exchange_close_paths.json")
assert close_paths["sampled_transactions"] == 7 and close_paths["sampled_positions"] == 9
assert close_paths["case_counts"] == {
    "margin_only_credited": 1,
    "margin_plus_negative_pnl_credited": 2,
    "margin_plus_positive_pnl_minus_fee_credited": 3,
    "margin_returned_net_profit_queued": 3,
}
exchange_paths = read("exchange_event_paths.json")
assert exchange_paths["batch_transactions_checked"] == 19 and exchange_paths["paired_exchange_events"] == 49
assert exchange_paths["position_opened_matches_return_id"] == exchange_paths["position_opened_matches_signed_fields"] == 25
assert exchange_paths["position_closed_matches_signed_id_array"] == 9
assert len(exchange_paths["direct_liquidation_batches"]) == 2
assert sum(len(x["liquidated_position_ids"]) for x in exchange_paths["direct_liquidation_batches"]) == 6
exchange_impl = next(x for x in catalog.values() if x["role"] == "exchange_implementation")
assert next(x for x in exchange_impl["functions"] if x["selector"] == "0xdc8a47ef")["reconstructed_signature"] == "instruments(uint32)"
assert {x["reconstructed_signature"] for x in exchange_impl["functions"] if x["selector"] in sweeps["selector_reconstructions"]} == set(sweeps["selector_reconstructions"].values())
exchange_errors = read("error_candidates.json")[sweeps["implementation"]]["candidates"]
assert all(any(x["selector"] == y["selector"] and x["status"] == "simulated_revert_selector" for x in exchange_errors) for y in sweeps["simulated_error_catalog"])
exchange_static_events = read("static_event_candidates.json")[sweeps["implementation"]]["candidates"]
assert all(any(x["topic0"] == y["topic0"] for x in exchange_static_events) for y in sweeps["event_catalog"])
assert next(x for x in events if x["emitter_role"] == "exchange_proxy" and x["topic0"].startswith("0x88451ea118"))["reconstructed_signature"] == "PositionOpened(uint256,address,uint32,bool,bool,uint64,uint128,uint32)"

suite_sets = verify_suite_sets()
assert suite_sets["set_count"] == 4
assert suite_sets["sets"] == ["earlier_1", "earlier_2", "newest", "postpin_refresh"]
assert suite_sets["newest_moved_proxies"]["exchange_proxy"] == "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
assert suite_sets["head_block"] > 49_200_000
suite_ledger = read("suite_sets.json")
assert suite_ledger["pin"] == manifest["block"] and suite_ledger["block_hash"] == manifest["block_hash"]
postpin = suite_ledger["postpin_deployment"]
postpin_roles = {row["role"]: row for row in postpin.values()}
postpin_hashes = suite_sets["postpin_runtime_sha256"]
assert len(postpin) == 7
assert postpin_roles["exchange_implementation_2"]["runtime_bytes"] == 23_959
assert postpin_roles["exchange_implementation_2"]["address"] == suite_sets["newest_moved_proxies"]["exchange_proxy"]
assert postpin_roles["exchange_linked_library_2"]["runtime_bytes"] == 6_286
# verify_suite_sets recomputes every runtime hash from the saved post-pin code, so these two
# ledgers only need to agree with each other here.
for role in ("exchange_implementation_2", "session_key_manager_implementation_2", "tokenomics_implementation_2"):
    assert postpin_hashes[role] == postpin_roles[role]["sha256"], role
assert postpin_hashes["session_key_manager_implementation_2"] == \
    read("asymmetric_impact_behavior.json")["live_capture"]["session_manager_implementation_sha256"]
set_2_batch = suite_ledger["upgrade_history"]["newest_governance"]["set_2_batch"]
assert set_2_batch["execute_block"] > suite_ledger["pin"]
assert len(set_2_batch["calls"]) == 6
assert sum(call.startswith("0x99a88ec4") for call in set_2_batch["calls"]) == 3
pt01_live = suite_ledger["pt01"]
assert len(pt01_live) == 2
for row in pt01_live.values():
    assert row["pending_sweep_word"] == row["pending_sweep_word_at_pin"]
    assert row["pending_sweep_word_unchanged"] is True
    assert row["exchange_balance_word"] == row["exchange_balance_call"] == "0x" + "00" * 32
    assert row["core_non_funding_ledger_entries_since_pin"] == 0
assert sorted(row["core_spot_usdc"] for row in pt01_live.values()) == ["12.1", "50.050916"]
haircut = read("asymmetric_impact_behavior.json")
assert haircut["pin"] == manifest["block"] and haircut["pin_hash"] == manifest["block_hash"]
certik = haircut["certik_claim_reproduction"]
assert certik["certik_haircut_ppm"] == 222_440 and certik["haircut_ppm"] == 222_439
assert certik["notional_sweep"]["10000000"]["haircut_ppm"] == certik["notional_sweep"]["500000"]["haircut_ppm"] == "222439"
assert certik["notional_sweep"]["500000"]["net"] == "661241720331917861080"
pinned_rows = {row["case"]: row for row in haircut["pinned_replay"]["rows"]}
assert pinned_rows["certik_10m"]["net_payout_1e18"] == "13224834406638357164981"
# The closed-form whole-book model and the replayed bytecode integer path floor in a different
# order, so the 500k case differs in the last wei while agreeing to six decimals.
model_net_500k = int(certik["notional_sweep"]["500000"]["net"])
replay_net_500k = int(pinned_rows["certik_500k"]["net_payout_1e18"])
assert replay_net_500k != model_net_500k and replay_net_500k // 10**12 == model_net_500k // 10**12
size_sweep = ["certik_50k", "certik_500k", "certik_2m_lev100", "certik_500k_lev250", "certik_10m", "certik_250m"]
assert {pinned_rows[case]["haircut_ppm"] for case in size_sweep} == {222_439}
assert {pinned_rows[case]["haircut_ppm"] for case in ("holdback_4bp", "holdback_4bp_500k", "holdback_4bp_2m")} == {477_058}
assert pinned_rows["counterfactual_ref_is_notional_500k"]["haircut_ppm"] != pinned_rows["counterfactual_ref_is_notional_10m"]["haircut_ppm"]
assert haircut["live_replay"]["size_sweep_single_haircut"] is True
assert haircut["live_replay"]["library_selectors_reached"]
assert haircut["live_capture"]["implementation"] == postpin_roles["exchange_implementation_2"]["address"]
assert haircut["live_capture"]["implementation_sha256"] == suite_sets["postpin_runtime_sha256"]["exchange_implementation_2"]
assert haircut["live_comparison"]["library_byte_identical_after_normalization"] is False
assert haircut["limits"]
gap_exchange = read("selector_gap_exchange.json")
assert gap_exchange["pin"] == manifest["block"]
assert gap_exchange["assigned_selector_count"] == len(gap_exchange["rows"]) == 20
assert all(row["abi_shape"] and row["guard"] and row["evidence_tier"] for row in gap_exchange["rows"])
gap_other = read("selector_gap_other.json")
assert gap_other["gap_row_count"] == gap_other["row_count"] == len(gap_other["rows"]) == 21
assert gap_other["counts"]["assigned_rows_closed"] == 21 and gap_other["counts"]["assigned_rows_undecided"] == 0
assert gap_other["counts"]["rows_with_exact_runtime_replay"] == 21
assert len(gap_other["kept_separate_rows"]) == gap_other["counts"]["kept_separate_fixed_reverts"] + gap_other["counts"]["kept_separate_initializer_stubs"] == 11
assert all(row["abi"] is not None and row["guard"] for row in gap_other["rows"])
coverage_summary = read("selector_evidence_coverage.json")["summary"]
assert coverage_summary["active_untraced_nonview_rows_from_unresolved_inventory"] == 41
assert coverage_summary["active_untraced_nonview_rows_with_gap_behavior_artifact"] == 41
unresolved_gap_rows = read("unresolved.json")["state_changing_selectors_without_saved_historical_trace"]
assert len(unresolved_gap_rows) == 41
assert all(row["gap_behavior_evidence"] and row["gap_local_replay_evidence"] for row in unresolved_gap_rows)

# Additive post-refresh pin: the same suite as it stands after the contract-set-2 batch.
postpin_pin = verify_postpin_pin()
assert postpin_pin["verified_offline"] is True
assert postpin_pin["pin"] == 49_265_286
assert postpin_pin["implementations"]["exchange_implementation_2"] == postpin_hashes["exchange_implementation_2"]
assert postpin_pin["implementations"]["session_key_manager_implementation_2"] == postpin_hashes["session_key_manager_implementation_2"]
assert postpin_pin["implementations"]["tokenomics_implementation_2"] == postpin_hashes["tokenomics_implementation_2"]
assert postpin_pin["selector_delta_counts"]["runtimes"] == 5
assert postpin_pin["selector_delta_counts"]["selectors"] == 176
assert postpin_pin["selector_delta_counts"]["added"] == 26
assert postpin_pin["selector_delta_counts"]["removed"] == 3
assert postpin_pin["selector_delta_counts"]["unresolved_added_selectors"] == 10
assert postpin_pin["moved"]["0x6cd5661646289fb6e65ea5c032310fded797d0a2"]["to"] == postpin_roles["exchange_implementation_2"]["address"]
assert set(postpin_pin["moved"]) == {
    "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
    "0x8326eb8896e358717f10502ec73ce8d28e37b108",
    "0x75174549dbbd44497d31a47e2e2d7406408d63d9",
}
postpin_ledger = json.loads((ROOT / "atlas" / "block_49265286" / "manifest.json").read_text())
assert postpin_ledger["block"] == postpin_pin["pin"]
assert postpin_ledger["block_hash"] == postpin_pin["block_hash"]
assert len(postpin_ledger["contracts"]) == 30
assert len(postpin_ledger["adds"]["addresses"]) == 5
assert postpin_ledger["runtime_file_base"] == "repo_root"
new_dir_entries = [row for row in postpin_ledger["contracts"].values()
                   if "block_49265286" in str(row.get("runtime_file", ""))]
assert len(new_dir_entries) == 5
baseline_entries = [row for row in postpin_ledger["contracts"].values()
                    if "block_48902346" in str(row.get("runtime_file", ""))]
assert len(baseline_entries) == 25
for row in postpin_ledger["contracts"].values():
    data = bytes.fromhex((ROOT / row["runtime_file"]).read_text().strip().removeprefix("0x"))
    assert len(data) == row["runtime_bytes"]
    assert hashlib.sha256(data).hexdigest() == row["sha256"]

# Live-code audit of contract set 2: eight workstream ledgers, consolidated and citation-checked.
live2_audit = verify_audit_live2()
assert live2_audit["workstreams_missing"] == []
assert live2_audit["workstreams_present"] == [
    "authority",
    "intents",
    "older",
    "payout",
    "pricing",
    "proxies",
    "roles",
    "sequences",
]
assert live2_audit["counts"]["rows"] == 92
assert live2_audit["counts"]["by_severity"]["high"] == 5
assert live2_audit["counts"]["by_status"]["blocked"] == 2
assert sum(live2_audit["counts"]["by_affected"].values()) == live2_audit["counts"]["rows"]
assert live2_audit["counts"]["by_affected"] == {
    "pinned": 5,
    "set2": 25,
    "both": 51,
    "earlier_1": 9,
    "earlier_2": 2,
}
assert live2_audit["counts"]["by_status"]["disproved"] >= 16
assert live2_audit["counts"]["by_status"]["confirmed_live"] >= 13
assert all(row["citation_ok"] for row in live2_audit["rows"])
live2_rows = {row["id"]: row for row in live2_audit["rows"]}
assert live2_rows["PR-LP-02"]["severity"] == "high"
assert live2_rows["PR-LP-02"]["status"] == "confirmed_simulation"
assert live2_rows["IN-L2-D5-02"]["severity"] == "high"
assert live2_rows["AU-L2A-12"]["status"] == "confirmed_live"
assert live2_rows["IN-L2-D5-01"]["status"] == "plausible_unproven"
# The three pass-two rows that carry the audit's conclusions.
assert live2_rows["SQ-L2-02"]["severity"] == "none"
assert live2_rows["SQ-L2-02"]["status"] == "disproved"
assert live2_rows["SQ-L2-02"]["affected"] == "both"
assert live2_rows["OL-07"]["status"] == "confirmed_live"
assert live2_rows["OL-08"]["status"] == "confirmed_live"
assert live2_rows["RL-04"]["status"] == "disproved"
assert live2_rows["SQ-L2-03"]["status"] == "confirmed_live"
assert len(live2_audit["blocked"]) == 2
verify_book_identity()
print("atlas consistency checks passed")
