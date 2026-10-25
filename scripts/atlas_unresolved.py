#!/usr/bin/env python3
"""Record unresolved symbols and unexercised paths with their evidence."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
read = lambda name: json.loads((ATLAS / name).read_text())
catalog = read("selector_catalog.json")
library_behavior_path = ATLAS / "exchange_library_behavior.json"
library_behavior = json.loads(library_behavior_path.read_text()) if library_behavior_path.exists() else {}
events = read("event_catalog.json")["events"]
historical_events = read("historical_event_catalog.json")["events"]
observed_reverts = read("observed_reverts.json")["reverts"]
storage = read("storage_trace_catalog.json")
calls = read("observed_call_graph.json")
errors = read("error_candidates.json")
reconstructed_errors = {(row["role"], candidate["selector"]) for row in errors.values()
                        for candidate in row["candidates"] if candidate.get("reconstructed_signature")}
replays = read("replay_comparisons.json")["comparisons"]
disabled_paths = read("exchange_disabled_paths_behavior.json")
disabled_selector = read("exchange_disabled_selector_behavior.json")
session_disabled = read("session_disabled_selector_behavior.json")
staking_direct = read("staking_direct_stubs_behavior.json")
proxy_admin_behavior = read("proxy_admin_behavior.json")
batch_control = read("batch_control_behavior.json")
exchange_pause = read("exchange_pause_behavior.json")
exchange_instrument_limit = read("exchange_instrument_limit_behavior.json")
exchange_initializer = read("exchange_initializer_behavior.json")
exchange_adapters = read("exchange_library_adapters_behavior.json")
exchange_library_remaining = read("exchange_library_remaining_behavior.json")
exchange_library_harvest = read("exchange_library_harvest_behavior.json")
exchange_staking_credit = read("exchange_staking_credit_behavior.json")
paper_math = read("paper_math_behavior.json")
staking_initializers = read("staking_initializers_behavior.json")
legacy_initializers = read("legacy_initializer_stubs_behavior.json")
staking_getters = read("staking_getters_behavior.json")
session_initializer = read("session_initializer_behavior.json")
session_initializer_constants = read("session_initializer_constants_behavior.json")
tokenomics_initializer = read("tokenomics_initializer_behavior.json")
tokenomics_redemption = read("tokenomics_redemption_stub_behavior.json")
tokenomics_seven_word = read("tokenomics_seven_word_stub_behavior.json")
tokenomics_getters = read("tokenomics_getter_alias_behavior.json")
paper_control_history = read("paper_control_history_behavior.json")
assert paper_control_history["admin_event_count"] == 5 and paper_control_history["burn_event_count"] == 0
seen = {}
for edge in calls["edges"]:
    seen.setdefault(edge["to_role"], set()).update(edge["selectors"])
for row in calls["traces"]:
    seen.setdefault(row["root_role"], set()).add(row["root_selector"])
factory_creation = ROOT / "artifacts" / "factory_creation" / "0xdf3909a903c5e15a5ac770bdcb6cccef77399094b4b99f759ecd4521ed86ae7d.calls.json"
if factory_creation.exists():
    factory_behavior = read("factory_behavior.json")
    seen.setdefault("deposit_proxy_factory_implementation", set()).add(factory_behavior["initializer"]["selector"])
oracle_creation = ROOT / "artifacts" / "oracle_creation" / "0x9b66014c5dfeb4d4fe9bd45bbc681f8628edbbbd8a3a2dbe19d155ed5de63f9d.calls.json"
if oracle_creation.exists():
    seen.setdefault("oracle_implementation", set()).add("0xc4d66de8")
staking_creation = ROOT / "artifacts" / "staking" / "deployment.calls.json"
if staking_creation.exists():
    seen.setdefault("staking_implementation", set()).add("0x9ccae24e")
paper_token_creation = ROOT / "artifacts" / "paper_token" / "deployment.calls.json"
if paper_token_creation.exists():
    seen.setdefault("paper_token_implementation", set()).add("0x8f15b414")
session_creation = ROOT / "artifacts" / "session_creation" / "0xe055509195f0ea1b9e30c366c3350d10470d8c1d145bfa51686b49134d36ffbe.calls.json"
if session_creation.exists():
    creation = json.loads(session_creation.read_text())
    assert creation["type"] == "CREATE" and creation["to"].lower() == session_initializer["session_proxy"]
    assert creation["calls"][0]["to"].lower() == session_initializer["implementation"]
    assert creation["calls"][0]["input"].startswith("0x747b8a1c")
    seen.setdefault("session_key_manager_implementation", set()).add("0x747b8a1c")

unmatched = []
ambiguous = []
unobserved_mutations = []
for address, contract in catalog.items():
    role = contract["role"]
    if role.endswith("_proxy") or "variant" in role:
        continue
    for function in contract["functions"]:
        item = {"role": role, "address": address, "selector": function["selector"],
                "inferred_arguments": function["arguments"], "candidate_signature": function["candidate_signature"],
                "reconstructed_signature": function.get("reconstructed_signature", ""),
                "evidence": "selector_catalog.json"}
        if function.get("behavior_evidence"):
            item["behavior_evidence"] = function["behavior_evidence"]
        if function.get("queue_merge_evidence"):
            item["queue_merge_evidence"] = function["queue_merge_evidence"]
            item["local_replay_evidence"] = "../../artifacts/exchange_library_queue_merge_local/replay.json"
            item["observed_behavior"] = "Ten exact-runtime local tests cover two- and three-node merges, a limit-one revert, unchanged queued totals, and two unnamed events"
        if function.get("queue_harvest_followup_evidence"):
            item["queue_harvest_followup_evidence"] = function["queue_harvest_followup_evidence"]
            item["queue_harvest_followup_replay_evidence"] = "../../artifacts/exchange_library_queue_harvest_followup_local/replay.json"
        if function.get("queue_interleaved_evidence"):
            item["queue_interleaved_evidence"] = function["queue_interleaved_evidence"]
            item["queue_interleaved_replay_evidence"] = "../../artifacts/exchange_library_queue_interleaved_local/replay.json"
        if function.get("queue_count_merge_evidence"):
            item["queue_count_merge_evidence"] = function["queue_count_merge_evidence"]
            item["queue_count_merge_replay_evidence"] = "../../artifacts/exchange_library_queue_count_merge_local/replay.json"
        if role == "paper_token_implementation" and function["selector"] in ("0x9dc29fac", "0xfca3b5aa"):
            item["event_absence_evidence"] = "paper_control_history_behavior.json"
            item["full_history_event_lookup"] = "../../artifacts/paper_control_history/event_queries.json"
            item["observed_behavior"] = ("Full-range Transfer-to-zero query returned zero logs; pinned read-only burn mutation succeeds from minter"
                                         if function["selector"] == "0x9dc29fac" else
                                         "Full-range MinterUpdated query found only the deployment initializer event; pinned read-only setMinter mutation succeeds from owner")
        if role == "deposit_proxy_factory_implementation" and function["selector"] == "0x0f71c8bc":
            item["observed_behavior"] = "Admin-only initialization: current state rejects; owner-zero override writes owner and deployer and emits both updates"
        if role == "deposit_proxy_factory_implementation" and function["selector"] == "0xc6f881bc":
            item["observed_behavior"] = "Owner sets authorized deployer in slot 4 and emits update; outsider reverts"
        if role == "staking_implementation" and function["selector"] in ("0xa694fc3a", "0x2e17de78", "0x4e71d92d", "0xe4fc6b6d"):
            item["simulation_evidence"] = "../../artifacts/staking/pinned_direct_probes.json"
            item["observed_behavior"] = "Exact pinned runtime has an effect-free fixed-revert body; seven pinned calls and two local proxy replays per selector return 0xa15ce1ba"
            item["behavior_evidence"] = "staking_direct_stubs_behavior.json"
            item["error_selector"] = "0xa15ce1ba"
        if role == "staking_implementation" and function["selector"] == "0x9ccae24e":
            item["behavior_evidence"] = "staking_behavior.json"
            item["observed_behavior"] = "Historical deployment five-address initializer sets Exchange, stake token, reward token, owner, and executor, with two update events; source name unknown"
        if role == "staking_implementation" and function["selector"] == staking_getters["unnamed_packed_getter"]["selector"]:
            item["behavior_evidence"] = "staking_getters_behavior.json"
            item["observed_behavior"] = "slot-16 byte 20 nonzero flag, checked with off, on, and high-byte storage overrides; source name unknown"
        if role == "session_key_manager_implementation" and function["selector"] == session_initializer_constants["selector"]:
            item["domain_string_evidence"] = "session_initializer_constants_behavior.json"
            item["observed_behavior"] = "Fresh-state name and version hashes must match String and 1; mismatches return 0xf50220aa"
        if role == "session_key_manager_implementation" and function["selector"] == "0xc1e6613d":
            item["observed_behavior"] = "Pinned getter returns associated address from sessionKeys(user,key); matched registration calldata and raw slot 4 in ten samples"
        if role == "oracle_implementation" and function["selector"] in ("0xa7f06462", "0xc0182669"):
            item["observed_behavior"] = read("oracle_behavior.json")["unresolved_selector_semantics"][function["selector"]]
        if role == "paper_math_library" and function["selector"] == paper_math["selector"]:
            item["behavior_evidence"] = "paper_math_behavior.json"
            item["observed_behavior"] = "27 successful historical math calls, 12 pinned direct probes, and four panic boundaries; source name unknown"
        if role == "exchange_linked_library_live" and function["selector"] in library_behavior.get("selector_behaviors", {}):
            item["semantic_evidence"] = "exchange_library_behavior.json"
            item["observed_behavior"] = library_behavior["selector_behaviors"][function["selector"]]
            if function["selector"] == "0xef1a27a9":
                item["fee_rate_evidence"] = "exchange_library_fee_rates_behavior.json"
        if role == "exchange_linked_library_live" and function["selector"] == exchange_library_harvest["selector"]:
            item["simulation_evidence"] = "exchange_library_harvest_behavior.json"
            item["observed_behavior"] = "One historical and thirteen read-only queue harvest calls reconcile both return words, event payments, queue debits, and user balance credits"
        if role == "exchange_linked_library_live" and function["selector"] in exchange_library_remaining["selector_behaviors"]:
            item["simulation_evidence"] = "exchange_library_remaining_behavior.json"
            item["observed_behavior"] = exchange_library_remaining["selector_behaviors"][function["selector"]]
        for evidence_role, behavior, filename in (
            ("staking_implementation", staking_initializers, "staking_initializers_behavior.json"),
            ("session_key_manager_implementation", session_initializer, "session_initializer_behavior.json"),
            ("tokenomics_implementation", tokenomics_initializer, "tokenomics_initializer_behavior.json"),
        ):
            if role == evidence_role and function["selector"] in behavior["selector_behaviors"]:
                item["simulation_evidence"] = filename
                item["observed_behavior"] = behavior["selector_behaviors"][function["selector"]]
        if role == "batch_executor_implementation" and function["selector"] in batch_control["simulated_control_selectors"]:
            item["simulation_evidence"] = "batch_control_behavior.json"
            if function["selector"] == "0xc0c53b8b":
                item["observed_behavior"] = "Three-address selector reverts with 0xb7b2509c under archived and fresh local states"
                item["error_selector"] = "0xb7b2509c"
            else:
                item["observed_behavior"] = "Initialized-state rejection and fresh-state control behavior checked with exact pinned proxy and implementation bytecode"
        if role in legacy_initializers["entries"] and function["selector"] == legacy_initializers["entries"][role]["selector"]:
            item["bytecode_evidence"] = "legacy_initializer_stubs_behavior.json"
            item["observed_behavior"] = "Canonical zero-value calldata reaches an effect-free fixed revert after address decoding; no success branch at the pinned runtime"
            item["error_selector"] = legacy_initializers["error_selector"]
        if role == "paper_token_implementation" and function["selector"] in ("0x9dc29fac", "0xfca3b5aa"):
            item["simulation_evidence"] = "../../artifacts/paper_token/pinned_mutation_traces.json"
        if role == "exchange_implementation" and function["selector"] in ("0x2d2451d1", "0xae69b95b"):
            item["simulation_evidence"] = "exchange_pause_behavior.json"
            item["observed_behavior"] = "Local pinned-runtime owner and pause-guardian controls, storage writes, events, and raw errors"
        if role == "exchange_implementation" and function["selector"] == exchange_instrument_limit["selector"]:
            item["simulation_evidence"] = "exchange_instrument_limit_behavior.json"
            item["observed_behavior"] = "10 exact pinned-runtime local tests map owner control, two packed instrument fields, validation errors, and an unnamed event"
        if role == "exchange_implementation" and function["selector"] == exchange_initializer["selector"]:
            item["simulation_evidence"] = "exchange_initializer_behavior.json"
            item["observed_behavior"] = "6 exact pinned-runtime local tests map fresh initialization, default slots, token decimal scaling, and initialized-state rejection"
        if role == "exchange_implementation" and function["selector"] in exchange_adapters["adapters"]:
            item["simulation_evidence"] = "exchange_library_adapters_behavior.json"
            item["observed_behavior"] = "Exact Exchange bytecode forwards to linked library; spy checks calldata, return widths, and errors; live library checks selected default branches"
        if role == "exchange_linked_library_live" and function["selector"] in exchange_adapters["adapters"].values():
            item["simulation_evidence"] = "exchange_library_adapters_behavior.json"
            item["observed_behavior"] = "Local call through exact Exchange and library runtimes checks selected default and synthetic queue-node branches"
        if function.get("queue_count_merge_evidence"):
            item["observed_behavior"] = "Fifteen exact-runtime tests cover count-bounded headward or threshold-gated tailward consolidation, returns, storage, and events"
        if role == "exchange_implementation" and function["selector"] == "0x415f1240":
            item["simulation_evidence"] = "exchange_liquidation_behavior.json"
            item["fee_effect_evidence"] = "exchange_fee_effects_behavior.json"
        if role == "exchange_implementation" and function["selector"] == "0x50c23fab":
            item["behavior_evidence"] = "exchange_liquidation_price_behavior.json"
            item["observed_behavior"] = "26 pinned outputs match a position and instrument maintenance-rate formula; 4 equal local fork liquidation boundaries"
        if role == "exchange_implementation" and function["selector"] == "0x5ca4c0ea":
            item["simulation_evidence"] = "exchange_instrument_admin_behavior.json"
            item["observed_behavior"] = "9 read-only probes map owner control, adjacent upper bound, three packed instrument words, and an unnamed event"
        if role == "exchange_implementation" and function["selector"] in ("0xe538b280", "0xf1a8786c", "0x48ee5e08"):
            item["behavior_evidence"] = "exchange_fee_rates_behavior.json"
            item["observed_behavior"] = "setFeeRates and event hash-verified; 7 read-only probes map three direct fee slots and inclusive upper bounds"
        if role == "exchange_implementation" and function["selector"] == "0x48ee5e08":
            item["close_fee_effect_evidence"] = "exchange_close_fee_effects_behavior.json"
        if role == "exchange_implementation" and function["selector"] == "0xf1a8786c":
            item["negative_close_fee_effect_evidence"] = "exchange_negative_close_fee_behavior.json"
        if role == "exchange_implementation" and function["selector"] in ("0x6d60ae8e", "0xaf210ecc", "0xc43fbc8c", "0xfdfd905d", "0xff3bc415"):
            item["behavior_evidence"] = "exchange_small_views_behavior.json"
            item["observed_behavior"] = "pinned output and controlled storage behavior verified; source name unresolved"
        if role == "session_key_manager_implementation" and function["selector"] == "0x17a1678f":
            item["behavior_evidence"] = "session_disabled_selector_behavior.json"
            item["observed_behavior"] = "canonical ABI calls unconditionally revert with 0xd2dd8531 in the pinned runtime; source name unresolved"
        if role == "exchange_implementation" and function["selector"] in ("0x1afd17e9", "0x63ca348f"):
            item["behavior_evidence"] = "exchange_disabled_paths_behavior.json"
            item["observed_behavior"] = "pinned runtime validates canonical ABI then always reverts with 0x58f03bf7; source names unresolved"
        if role == "exchange_implementation" and function["selector"] == "0xc8372577":
            item["behavior_evidence"] = "exchange_mapping35_view_behavior.json"
            item["observed_behavior"] = "uint32 key -> bool and three uint64 fields packed in one mapping-35 word; source name and field meanings unresolved"
        if role == "exchange_implementation" and function["selector"] == "0xc88bbcf3":
            item["behavior_evidence"] = "exchange_instrument_creation_behavior.json"
            item["local_replay_evidence"] = "../../artifacts/exchange_instrument_creation_local/replay.json"
            item["observed_behavior"] = "two successful nine-word registrations with saved receipts, traces, and state diffs; local replay checks owner guard, field packing, event input word 2, and sampled input bounds"
        if role == "exchange_implementation" and function["selector"] == "0xfb9f1009":
            item["behavior_evidence"] = "exchange_disabled_selector_behavior.json"
            item["observed_behavior"] = "canonical uint32 calls unconditionally revert with 0xd9d193d3 in the pinned runtime; source names unresolved"
        if role == "exchange_implementation" and function["selector"] in exchange_staking_credit["selector_reconstructions"]:
            item["behavior_evidence"] = "exchange_staking_credit_behavior.json"
            item["observed_behavior"] = "27 historical Staking reward transfers and four pinned read-only branches reconcile events, mapping-9 balances, and raw reverts"
        if role == "exchange_implementation" and function["selector"] == "0x7f99545a":
            item["simulation_evidence"] = "exchange_direct_withdrawal_behavior.json"
            item["observed_behavior"] = "nine local fork probes cover direct Core withdrawal, amount bound, balance, and same-block guard"
        if role == "exchange_implementation" and function["selector"] in ("0x31a39849", "0x70f75ff5", "0x2dcc7fce", "0xbacd9ea0"):
            item["behavior_evidence"] = "exchange_unit_scales_behavior.json"
            item["observed_behavior"] = "40 pinned and storage-override calls match slot-3 and slot-5 unit scaling"
        if role == "exchange_implementation" and function["selector"] in ("0x628a9fd6", "0xcb163b03", "0xf37d3c4f"):
            item["behavior_evidence"] = "exchange_market_fields_behavior.json"
        if role == "exchange_implementation" and function["selector"] in ("0x82f47a3f", "0x1b7c1009"):
            item["behavior_evidence"] = "exchange_pair_params_behavior.json"
        if role == "tokenomics_implementation" and function["selector"] in tokenomics_getters["selector_behaviors"]:
            item["behavior_evidence"] = "tokenomics_getter_alias_behavior.json"
            item["observed_storage_slot"] = tokenomics_getters["selector_behaviors"][function["selector"]]["direct_slot"]
            item["observed_behavior"] = "direct getter for pinned mint-parameter storage word; source name unverified"
        if role == "tokenomics_implementation" and function["selector"] == "0x0efdf838":
            item["behavior_evidence"] = "liquidation_tokenomics_behavior.json"
            item["observed_behavior"] = "67 direct-batch liquidation calls reconcile fees, Tokenomics event, PaperMath mint, PAPER Transfer, and three storage slots; exact source name unresolved"
        if role == "tokenomics_implementation" and function["selector"] == tokenomics_seven_word["selector"]:
            item["behavior_evidence"] = "tokenomics_seven_word_stub_behavior.json"
            item["observed_behavior"] = "at least seven argument words required; canonical calls always revert with 0x32aa90b0"
            item["minimum_calldata_bytes"] = tokenomics_seven_word["minimum_calldata_bytes"]
            item["validated_word_types"] = tokenomics_seven_word["validated_words"]
        if role == "proxy_admin" and function["selector"] in ("0x7eff275e", "0x9623609d", "0x99a88ec4"):
            item["behavior_evidence"] = "proxy_admin_behavior.json"
            item["local_replay_evidence"] = proxy_admin_behavior["local_replay_evidence"]
            item["observed_behavior"] = proxy_admin_behavior["tested_effects"]
        if role == "user_deposit_proxy_representative":
            item["local_replay_evidence"] = "../../artifacts/deposit_proxy_local/replay.json"
            item["observed_behavior"] = "Nineteen exact-runtime local tests cover access checks, token return shapes, sweep action bytes, and writer failure rollback"
        if role == "tokenomics_implementation" and function["selector"] == "0x12baae3b":
            item["simulation_evidence"] = "tokenomics_params_behavior.json"
        if function.get("queue_merge_evidence"):
            item["observed_behavior"] = "Ten exact-runtime local tests cover two- and three-node merges, a limit-one revert, unchanged queued totals, and two unnamed events; eleven subsequent exact-runtime harvest calls show empty global-head nodes use the node limit"
        if function.get("queue_harvest_followup_evidence"):
            item["queue_harvest_followup_evidence"] = function["queue_harvest_followup_evidence"]
            item["queue_harvest_followup_replay_evidence"] = "../../artifacts/exchange_library_queue_harvest_followup_local/replay.json"
        if function.get("queue_interleaved_evidence"):
            item["queue_interleaved_evidence"] = function["queue_interleaved_evidence"]
            item["queue_interleaved_replay_evidence"] = "../../artifacts/exchange_library_queue_interleaved_local/replay.json"
        if function.get("queue_count_merge_evidence"):
            item["queue_count_merge_evidence"] = function["queue_count_merge_evidence"]
            item["queue_count_merge_replay_evidence"] = "../../artifacts/exchange_library_queue_count_merge_local/replay.json"
            item["observed_behavior"] = "Fifteen exact-runtime tests cover count-bounded headward or threshold-gated tailward consolidation, returns, storage, and events"
        if not function["candidate_signature"] and not function.get("reconstructed_signature"):
            unmatched.append(item)
        elif not function.get("reconstructed_signature") and "|" in function["candidate_signature"]:
            ambiguous.append(item)
        if function["state_mutability"] not in ("view", "pure") and function["selector"] not in seen.get(role, set()):
            unobserved_mutations.append(item)

failed_views = []
for address, contract in storage.items():
    for view in contract["views"]:
        if view.get("failed") or "error" in view:
            item = {"role": contract["role"], "address": address, "selector": view["selector"],
                    "candidate_signature": view["candidate_signature"], "sample_argument": view["sample_argument"],
                    "reason": view.get("error", "sampled call reverted"), "evidence": "storage_trace_catalog.json"}
            if contract["role"] == "exchange_implementation" and view["selector"] == "0xfb9f1009":
                item["behavior_evidence"] = "exchange_disabled_selector_behavior.json"
                item["behavior_status"] = "revert path explained by pinned opcode trace"
            failed_views.append(item)

result = {
    "pin": 48902346,
    "unmatched_selector_candidates": unmatched,
    "ambiguous_public_signature_matches": ambiguous,
    "state_changing_selectors_without_saved_historical_trace": unobserved_mutations,
    "signed_intent_branch_gaps": [
        {"role": "exchange_implementation", "selector": "0x8d09f23f",
         "unresolved": "Local exact-runtime tests now cover invalid and tampered withdrawal signatures, a valid synthetic withdrawal, replay rejection, deadlines, and nonce rollback. All 103 sampled withdrawal nonce bits are checked before and after their blocks, and at the pin. Per-transaction storage diffs, unsampled withdrawals, and other signature encodings remain open.",
         "evidence": "exchange_withdrawal_signature_behavior.json",
         "local_evidence": "../../artifacts/audit_signed_intent_failures/replay.json"},
        {"role": "exchange_implementation", "selector": "0x2792e706",
         "unresolved": "Local tests cover invalid signatures, nonce and deadline failures, a four-ID close over empty slots with fourth-ID tampering, and a constructed four-active-position close cloned from one historical template. A full historical transaction replay matches two distinct signed closes. Two same-market and two cross-market four-ID gain/loss orders now reconcile balance, fees, locked margin, events, and nonce on exact runtime; all 16 library outputs in eight cross-market PnL and settlement call pairs match independent integer models and their close events. All 43 sampled close nonce bits persisted across their blocks and at the pin. Other rate, liquidity, queue, and margin boundaries plus historical session-key storage for every signer remain open.",
         "evidence": "session_close_typehash_behavior.json",
         "nonce_evidence": "trading_nonce_history.json",
         "local_evidence": "../../artifacts/audit_signed_intent_failures/replay.json",
         "historical_replay_evidence": "../../artifacts/audit_historical_close/replay.json"},
        {"role": "exchange_implementation", "selector": "0xec6783f0",
         "unresolved": "Synthetic local tests cover invalid open signatures, nonce and deadline failures, and a valid session-key signature reaching raw 0x0a4f5a07 in constructed state. One successful historical open replays from archived prestate with logs and storage writes matched. Eight one-field changes to that signed calldata reject with 0xc5045f22, no logs, and no nonce consumption; replay in the next block rejects with 0x756688fe. Archive storage confirms 30 successful open nonce bits persisted and 28 rejected open bits stayed unset, including 27 nested nonce calls rolled back by their parent. A separate local control copies the original signer authorization to the changed user and confirms the changed digest recovers a different signer; the call still rejects. This copied key is a storage override, not a historical registration. Other open business-rule branches and signature encodings remain open.",
         "evidence": "session_open_typehash_behavior.json",
         "nonce_evidence": "trading_nonce_history.json",
         "local_evidence": "../../artifacts/audit_signed_intent_failures/replay.json",
         "historical_replay_evidence": "../../artifacts/audit_historical_open/replay.json",
         "tamper_replay_evidence": "../../artifacts/audit_historical_open_tamper/replay.json"},
    ],
    "bytecode_proven_initializer_stubs": [
        {"role": role, "selector": row["selector"], "error_selector": legacy_initializers["error_selector"],
         "behavior_evidence": "legacy_initializer_stubs_behavior.json", "linked_probe": row["linked_probe"]}
        for role, row in legacy_initializers["entries"].items()],
    "simulated_events_without_resolved_signature": [{"emitter_role": "exchange_proxy", "topic0": x["topic0"],
                                                     "decoded_layout": x["decoded_layout"],
                                                     "evidence": "exchange_library_queue_merge_behavior.json",
                                                     "local_replay_evidence": "../../artifacts/exchange_library_queue_merge_local/replay.json"}
                                                    for x in read("exchange_library_queue_merge_behavior.json")["event_catalog"]
                                                    if not x["reconstructed_signature"]],
    "observed_events_without_resolved_signature": [{"emitter_role": x["emitter_role"], "topic0": x["topic0"],
                                                  "count_last_256_blocks": x["count_last_256_blocks"], "evidence": "event_catalog.json"}
                                                 for x in events if not x["public_signature_candidates"] and not x.get("reconstructed_signature")]
                                                + [{"emitter_role": x["role"], "topic0": x["topic0"],
                                                    "count_saved_receipts": x["count_in_saved_receipts"], "evidence": "historical_event_catalog.json"}
                                                   for x in historical_events if x["role"] != "external_or_system" and not x["also_seen_last_256_blocks"] and not x["public_signature_candidates"] and not x.get("reconstructed_signature")],
    "unverified_decompiler_error_candidates": {a: {"role": row["role"], "candidates": [x for x in row["candidates"] if x["status"] == "unverified_heimdall_candidate"]}
                                              for a, row in errors.items() if any(x["status"] == "unverified_heimdall_candidate" for x in row["candidates"])},
    "observed_reverts_without_public_signature": [{"role": x["role"], "selector": x["revert_selector"], "count": x["count_in_saved_traces"], "evidence": "observed_reverts.json"}
                                                  for x in observed_reverts if x["revert_selector"] and not x["public_signature_candidates"]
                                                  and (x["role"], x["revert_selector"]) not in reconstructed_errors],
    "reverted_view_probes": failed_views,
    "fixed_revert_paths": sorted([
        {"role": "exchange_implementation", "selector": selector,
         "error_selector": disabled_paths["error_selector"],
         "source_name_status": entry["source_name_status"],
         "public_signature_candidate": entry.get("public_signature_candidate", ""),
         "behavior_evidence": "exchange_disabled_paths_behavior.json",
         "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json"}
        for selector, entry in disabled_paths["selector_behaviors"].items()
    ] + [{"role": "exchange_implementation", "selector": disabled_selector["selector"],
          "error_selector": disabled_selector["simulated_error_catalog"][0]["selector"],
          "source_name_status": disabled_selector["source_name_status"],
          "public_signature_candidate": disabled_selector["public_signature_candidate"],
          "behavior_evidence": "exchange_disabled_selector_behavior.json",
          "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json"},
         {"role": "session_key_manager_implementation", "selector": session_disabled["selector"],
          "error_selector": session_disabled["error_selector"],
          "source_name_status": session_disabled["source_name_status"],
          "public_signature_candidate": "",
          "behavior_evidence": "session_disabled_selector_behavior.json",
          "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json"}] + [
        {"role": "tokenomics_implementation", "selector": selector,
         "error_selector": tokenomics_redemption["error_selector"],
         "source_name_status": tokenomics_redemption["source_name_status"],
         "public_signature_candidate": signature,
         "behavior_evidence": "tokenomics_redemption_stub_behavior.json",
         "local_replay_evidence": tokenomics_redemption["local_replay_evidence"]}
        for selector, signature in tokenomics_redemption["selector_reconstructions"].items()
    ] + [{"role": "staking_implementation", "selector": selector,
           "error_selector": staking_direct["error_selector"],
           "source_name_status": staking_direct["source_name_status"],
           "public_signature_candidate": "",
           "behavior_evidence": "staking_direct_stubs_behavior.json",
           "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json"}
          for selector in staking_direct["selector_behaviors"]
    ] + [{"role": "tokenomics_implementation", "selector": tokenomics_seven_word["selector"],
          "error_selector": tokenomics_seven_word["error_selector"],
          "source_name_status": tokenomics_seven_word["source_name_status"],
          "public_signature_candidate": "",
          "behavior_evidence": "tokenomics_seven_word_stub_behavior.json",
          "local_replay_evidence": tokenomics_seven_word["local_replay_evidence"]}],
        key=lambda row: row["selector"]),
    "replay_storage_mismatches": [{"tx": x["tx"], "selector": x["selector"], "transaction_index": x["transaction_index"],
                                   "evidence": "replay_comparisons.json"} for x in replays if not x["contract_storage_changes_equal"]],
    "limits": ["The 25-address manifest and its selector coverage describe the newest suite only; 38 earlier direct creations and 38 older factory-created user proxies still have code at the pin, and the earlier suites are not behavior-audited. See deployer_scope.md.",
               "No verified Solidity source was available for the 17 nonproxy runtimes checked.",
               f"The call graph is based on {len(calls['traces'])} sampled historical transactions, so unobserved calls and internal branches remain.",
               "The HyperCore boundary ledger covers 482 calls in 170 saved traces, not every historical boundary call or selector.",
               "CoreWriter action submission is visible in EVM traces, but later HyperCore settlement and the one-USD debit disposition are unverified.",
               "Heimdall pseudocode and error candidates are hypotheses until checked against opcode traces.",
               "Only 42 deposit proxy runtimes were fetched directly at the pin; the other 22,544 are derived from deterministic CREATE2 initcode and matching deployment addresses.",
               "Unknown topics emitted by external contracts in saved receipts are retained in the historical event catalog but excluded from Papertrade-specific unresolved topics."],
}
gap_checks = read("public_name_gap_checks.json")
assert gap_checks["openchain_function_selector_count"] == len({row["selector"] for row in unmatched})
assert gap_checks["openchain_event_topic_count"] == len(result["observed_events_without_resolved_signature"])
for item in result["unmatched_selector_candidates"]:
    item["public_name_gap_checks"] = "public_name_gap_checks.json"
for item in result["state_changing_selectors_without_saved_historical_trace"]:
    if item["role"] in {"exchange_implementation", "exchange_linked_library_live"}:
        item["gap_behavior_evidence"] = "selector_gap_exchange.json"
        item["gap_local_replay_evidence"] = "../../artifacts/selector_gap_exchange/replay.json"
        item["gap_static_evidence"] = "../../artifacts/selector_gap_exchange/static_analysis.json"
    else:
        item["gap_behavior_evidence"] = "selector_gap_other.json"
        item["gap_local_replay_evidence"] = "../../artifacts/selector_gap_other/replay.json"
    item["gap_evidence_note"] = ("Exact-runtime behavior record with recovered calldata shape, caller guard, state writes, "
                                 "emitted topics and at least one rejection case. No saved historical call exists for this "
                                 "selector, so the historical-trace gap itself remains open.")
    if item["role"] == "exchange_implementation" and item["selector"] in {
            "0xae69b95b", "0x2d2451d1", "0xe538b280", "0xd7c7e5fb"}:
        item["full_history_event_lookup"] = "../../artifacts/exchange_control_history/event_queries.json"
        item["event_absence_evidence"] = "exchange_control_event_history_behavior.json"
    if item["role"] == "exchange_implementation" and item["selector"] == "0x5ca4c0ea":
        item["full_history_event_lookup"] = "../../artifacts/exchange_instrument_admin/full_history_event_query.json"
        item["local_replay_evidence"] = "../../artifacts/exchange_instrument_admin_local/replay.json"
for item in result["observed_events_without_resolved_signature"]:
    item["public_name_gap_checks"] = "public_name_gap_checks.json"
    if item["emitter_role"] == "exchange_proxy" and item["topic0"] == "0xa065d6ba54c5124cd73ce640fd3fbc0ce6eb8a4f4c9d5155347dcc461ad0cffe":
        item["behavior_evidence"] = "exchange_market_fields_behavior.json"
        item["decoded_layout"] = "indexed uint32 instrument; unindexed uint128 first, uint128 second"
    if item["emitter_role"] == "exchange_proxy" and item["topic0"] == "0x5bcf15b0a82479fbcfcb086707ad8be24c96d445448a1f625310e1c3fe491759":
        item["behavior_evidence"] = "exchange_pair_params_behavior.json"
        item["decoded_layout"] = "unindexed uint128 first, uint128 second; matches packed slot 28"
    if item["emitter_role"] == "tokenomics_proxy" and item["topic0"] == "0x620c26bf4591919d64df736a6afdfe2981d15eb343c50644b49456c6facb3ab2":
        item["behavior_evidence"] = "tokenomics_observed_paths.json"
        item["decoded_layout"] = "indexed address recipient; unindexed debit, mint basis, tracked after debit, tracked after credit, tail delta, PAPER minted"
    if item["emitter_role"] == "tokenomics_proxy" and item["topic0"] == "0x3050fba19ada85812db26b240c13c72cabec711cbf18c7c6b3554d511e2951ee":
        item["behavior_evidence"] = "tokenomics_observed_paths.json"
        item["decoded_layout"] = "indexed address recipient and uint256 position ID; unindexed bool flag, mint basis, tracked before, tracked after, tail delta, PAPER minted"
(ATLAS / "unresolved.json").write_text(json.dumps(result, indent=2) + "\n")
print({k: len(v) for k, v in result.items() if isinstance(v, (list, dict))})
