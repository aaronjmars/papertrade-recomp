#!/usr/bin/env python3
"""Behavior record for the non-Exchange selector gap rows at HyperEVM block 48,902,346.

Scope: the rows in `atlas/block_48902346/unresolved.json`
`state_changing_selectors_without_saved_historical_trace` whose runtime role is not
`exchange_implementation` or `exchange_linked_library_live`, plus, kept separate, the
already-proven fixed-revert and initializer-stub selectors of the same runtime families.

Every semantic claim in the output rides on one of:
  * exact pinned runtime bytes (SHA-256 checked against manifest.json) read here, with the
    dispatcher/decoder instruction observed at an exact program counter;
  * a port-free local EVM replay of the exact pinned runtimes
    (`artifacts/selector_gap_other/replay.json`, regenerate with `--replay`);
  * an evidence artifact already saved in the repository, named per row.

Nothing here promotes a decompiler guess or a public signature preimage into a proven name.
Run `python3 scripts/atlas_selector_gap_other.py` for the offline check; it needs no RPC credential.
`--capture` refreshes the live `latest` reads and stores the raw JSON-RPC responses.
"""

import argparse
import datetime
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "selector_gap_other"
OUTPUT_JSON = ATLAS / "selector_gap_other.json"
OUTPUT_MD = ATLAS / "selector_gap_other.md"
REPLAY_JSON = OUT / "replay.json"
REPLAY_SOURCE = OUT / "SelectorGapLocal.t.sol"
RPC = "https://rpc.hyperliquid.xyz/evm"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"

# --------------------------------------------------------------------------- runtimes

RUNTIMES = {
    "paper_token_implementation": "0x433bd418ec92818a960585f4d5fae563e735bb4a",
    "tokenomics_implementation": "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f",
    "session_key_manager_implementation": "0x8a5069fe303e8f81e91825436e956d595032e558",
    "deposit_proxy_factory_implementation": "0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0",
    "batch_executor_implementation": "0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262",
    "staking_implementation": "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15",
    "proxy_admin": "0xe79c91cc682f1bb401a9cab74c900470190f0f8f",
    "timelock": "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
    "user_deposit_proxy_representative": "0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce",
}

# Live EIP-1967 implementation slot of the eight suite proxies, re-read under --capture.
PROXY_SLOT_CHECKS = {
    "paper_token_proxy": "0xe40f17915daa230324030003a197cdaef2261c0e",
    "tokenomics_proxy": "0x75174549dbbd44497d31a47e2e2d7406408d63d9",
    "session_key_manager_proxy": "0x8326eb8896e358717f10502ec73ce8d28e37b108",
    "deposit_proxy_factory_proxy": "0x1629b7d46bef6e13ff754174fc9f32dea309b38f",
    "batch_executor_proxy": "0x233ff29b239abc1d7748605da9b205c3e008626e",
    "staking_proxy": "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016",
    "exchange_proxy": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
}

# --------------------------------------------------------------------------- rows

# One row per assigned selector. `evidence_tier` uses the vocabulary of the ledger:
# historical trace / exact-runtime replay / pinned read-only probe / bytecode-only static
# read / fixed revert / undecided. `undecided` names exactly what is still open.
ROWS = [
    dict(
        role="paper_token_implementation",
        selector="0x9dc29fac",
        signature="burn(address,uint256)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address", "uint256"],
        payable=False,
        guard="caller == minter (proxy storage slot 4)",
        writes=["balances mapping base slot 7 for the burned holder", "totalSupply slot 6"],
        reads=["slot 4 (minter)"],
        events=["Transfer(address,address,uint256)"],
        errors=["NotMinter()", "InsufficientBalance()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "../../artifacts/paper_token/pinned_mutation_traces.json",
            "paper_token_behavior.json",
        ],
        replay_tests=["testPaperBurnFromMinter", "testPaperBurnRejections", "testDecodeGuards"],
        undecided=[
            "No successful post-deployment historical call exists: the full-range Transfer-to-zero query in artifacts/paper_control_history/event_queries.json returned zero logs.",
            "Original Solidity identifier and the exact burn-branch boundary conditions (zero address, self-burn) are not recovered.",
        ],
    ),
    dict(
        role="paper_token_implementation",
        selector="0xfca3b5aa",
        signature="setMinter(address)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address"],
        payable=False,
        guard="caller == owner (proxy storage slot 3)",
        writes=["minter slot 4"],
        reads=["slot 3 (owner)"],
        events=["MinterUpdated(address)"],
        errors=["NotOwner()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "../../artifacts/paper_token/pinned_mutation_traces.json",
            "paper_token_behavior.json",
        ],
        replay_tests=["testPaperSetMinter", "testDecodeGuards"],
        undecided=[
            "The only observed MinterUpdated log is the deployment initializer; no later historical setMinter call is saved.",
            "Original Solidity identifier is unverified.",
        ],
    ),
    dict(
        role="tokenomics_implementation",
        selector="0x12baae3b",
        signature="setMintParams(uint256,uint256,uint256,uint256)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["uint256", "uint256", "uint256", "uint256"],
        payable=False,
        guard="caller == owner (proxy storage slot 0, bits 16 through 175)",
        writes=["mint parameter slots 5, 6, 7 and 8, in argument order"],
        reads=["slot 0 (packed owner)"],
        events=["MintParamsUpdated(uint256,uint256,uint256,uint256)"],
        errors=["NotOwner()", "InvalidMintParams()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "tokenomics_params_behavior.json",
            "timelock_operations.json",
        ],
        replay_tests=["testTokenomicsSetMintParams", "testDecodeGuards"],
        undecided=[
            "The timelock operation that schedules this call was ready but not executed at the pin, so no historical success exists.",
            "Downstream mint arithmetic under the changed parameters is not replayed end to end.",
        ],
    ),
    dict(
        role="tokenomics_implementation",
        selector="0x485cc955",
        signature="initialize(address,address)",
        name_status="ambiguous public preimage set; hash-matching candidate only",
        name_candidates=[
            "initialize(address,address)",
            "watch_tg_invmru_7bd442a(uint256,address,uint256)",
            "watch_tg_invmru_10757d42(bool,bool)",
        ],
        abi=["address", "address"],
        payable=False,
        guard="none in fresh state (any caller); initialized state reverts",
        writes=[
            "slot 0 owner field with the low 16-bit initialization word",
            "slot 1 second address (Exchange)",
            "default mint parameter slots 5 through 8",
        ],
        reads=["slot 0 (initialization word)"],
        events=[
            "OwnerUpdated(address)",
            "MintParamsUpdated(uint256,uint256,uint256,uint256)",
        ],
        errors=["AlreadyInitialized()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/remaining_initializers_local/replay.json",
            "tokenomics_initializer_behavior.json",
            "../../artifacts/selector_gap_other/replay.json",
        ],
        replay_tests=["testDecodeGuards"],
        undecided=[
            "Three public 4-byte preimages hash to this selector; the original declaration is not proved.",
            "No historical deployment call is saved for this implementation (the pinned proxy was deployed before it).",
        ],
    ),
    dict(
        role="session_key_manager_implementation",
        selector="0xcf8fbec9",
        signature="setAuthorizedCaller(address)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address"],
        payable=False,
        guard="caller == owner (proxy storage slot 2)",
        writes=["authorized Exchange caller slot 3 only; the cached domain separator in slot 1 is unchanged"],
        reads=["slot 2 (owner)", "slot 3 (previous caller)"],
        events=["AuthorizedCallerUpdated(address)"],
        errors=["NotOwner()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "../../artifacts/session_keys/pinned_auth_probes.json",
            "session_key_behavior.json",
        ],
        replay_tests=["testSessionSetAuthorizedCaller", "testDecodeGuards"],
        undecided=[
            "No historical call is saved; the pinned read-only probe and this local replay are the only executions.",
            "The pinned session proxy now points at a different implementation at latest (see live_drift), so this record describes the pinned runtime only.",
        ],
    ),
    dict(
        role="deposit_proxy_factory_implementation",
        selector="0x0f71c8bc",
        signature=None,
        name_status="undefined: no hash-matching public name and no source",
        abi=["address", "address"],
        payable=False,
        guard=(
            "caller == the proxy's EIP-1967 admin slot AND owner storage slot 3 == 0; "
            "a zero Exchange field in slot 0 additionally reverts"
        ),
        writes=["owner slot 3", "authorized deployer slot 4"],
        reads=[
            "EIP-1967 admin slot " + ADMIN_SLOT,
            "slot 3 (owner)",
            "slot 0 (packed Exchange and initialized word)",
        ],
        events=["OwnerUpdated(address)", "AuthorizedDeployerUpdated(address)"],
        errors=["0xc031a0df (caller is not the proxy admin)", "0x3f733c4f (already initialized)", "InvalidExchange()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "factory_behavior.json",
        ],
        replay_tests=["testFactoryAdminInitializer", "testDecodeGuards"],
        undecided=[
            "Source function name and both admin-path error names are undefined.",
            "The pinned call reverts because the owner is set, so only a synthetic owner-zero test proxy reaches the write path.",
        ],
    ),
    dict(
        role="deposit_proxy_factory_implementation",
        selector="0xc6f881bc",
        signature="setAuthorizedDeployer(address)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address"],
        payable=False,
        guard="caller == owner (proxy storage slot 3)",
        writes=["authorized deployer slot 4"],
        reads=["slot 3 (owner)"],
        events=["AuthorizedDeployerUpdated(address)"],
        errors=["NotOwner()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "factory_selector_names_behavior.json",
        ],
        replay_tests=["testFactorySetAuthorizedDeployer", "testDecodeGuards"],
        undecided=["No historical call is saved; the pinned probes and this replay are the only executions."],
    ),
    dict(
        role="batch_executor_implementation",
        selector="0x0f71c8bc",
        signature=None,
        name_status="undefined: no hash-matching public name and no source",
        abi=["address", "address"],
        payable=False,
        guard="caller == the proxy's EIP-1967 admin slot AND owner slot 3 == 0 AND the slot-5 initialization word is clear",
        writes=["owner slot 3", "initialization word slot 5", "authorized relayer mapping base slot 4"],
        reads=["EIP-1967 admin slot " + ADMIN_SLOT, "slots 3 and 5"],
        events=["OwnerUpdated(address)", "AuthorizedRelayerUpdated(address,bool)"],
        errors=["0xc031a0df (caller is not the proxy admin)", "0x3f733c4f (already initialized)"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/batch_control_local/replay.json",
            "batch_control_behavior.json",
            "../../artifacts/selector_gap_other/replay.json",
        ],
        replay_tests=["testDecodeGuards"],
        undecided=[
            "Source function name and both admin-path error names are undefined.",
            "The write path needs a synthetic fresh-state proxy; the archived layout reverts.",
        ],
    ),
    dict(
        role="batch_executor_implementation",
        selector="0x9ccae24e",
        signature=None,
        name_status="undefined: no hash-matching public name and no source",
        abi=["address", "address", "address", "address", "address"],
        payable=False,
        guard="fresh state only; a set slot-5 initialization word reverts, otherwise any caller is accepted",
        writes=["slots 0 through 3", "initialization word slot 5", "authorized relayer mapping base slot 4"],
        reads=["slots 0, 1, 2, 3 and 5"],
        events=["OwnerUpdated(address)", "AuthorizedRelayerUpdated(address,bool)"],
        errors=["AlreadyInitialized()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/batch_control_local/replay.json",
            "batch_control_behavior.json",
            "../../artifacts/selector_gap_other/replay.json",
        ],
        replay_tests=["testDecodeGuards"],
        undecided=[
            "Source function name is undefined.",
            "The five-address argument order is inferred from the exercised fresh-state call, not from a historical deployment.",
        ],
    ),
    dict(
        role="staking_implementation",
        selector="0x0f71c8bc",
        signature=None,
        name_status="undefined: no hash-matching public name and no source",
        abi=["address", "address"],
        payable=False,
        guard="caller == the proxy's EIP-1967 admin slot AND owner slot 15 == 0 AND the slot-16 initialization flag is clear",
        writes=["owner slot 15", "authorized executor plus initialization flag slot 16"],
        reads=["EIP-1967 admin slot " + ADMIN_SLOT, "slots 15 and 16"],
        events=["OwnerUpdated(address)", "AuthorizedExecutorUpdated(address)"],
        errors=["0xc031a0df (caller is not the proxy admin)", "0x3f733c4f (already initialized)"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/remaining_initializers_local/replay.json",
            "staking_initializers_behavior.json",
            "../../artifacts/selector_gap_other/replay.json",
        ],
        replay_tests=["testDecodeGuards"],
        undecided=[
            "Source function name and both admin-path error names are undefined.",
            "The write path is a synthetic fresh-state test; the pinned state reverts.",
        ],
    ),
    dict(
        role="proxy_admin",
        selector="0x7eff275e",
        signature="changeProxyAdmin(address,address)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address", "address"],
        payable=False,
        guard="caller == owner (slot 0)",
        writes=["EIP-1967 admin slot of the target proxy"],
        reads=["slot 0 (owner)"],
        events=[],
        errors=["NotOwner()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/proxy_admin_local/replay.json",
            "proxy_admin_behavior.json",
        ],
        replay_tests=[],
        undecided=[
            "No historical ProxyAdmin call is saved beyond its creation and owner transfer, so this path is a local pinned-runtime replay only.",
            "The shared proxy runtime has no LOG opcode, so a successful admin change leaves no event.",
        ],
    ),
    dict(
        role="proxy_admin",
        selector="0x9623609d",
        signature="upgradeAndCall(address,address,bytes)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address", "address", "bytes"],
        payable=True,
        guard="caller == owner (slot 0)",
        writes=[
            "EIP-1967 implementation slot of the target proxy",
            "whatever the delegated setup call writes in the target proxy's storage",
        ],
        reads=["slot 0 (owner)"],
        events=[],
        errors=["NotOwner()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/proxy_admin_local/replay.json",
            "proxy_admin_behavior.json",
        ],
        replay_tests=[],
        undecided=[
            "Only a local mock setup call is replayed; no historical upgradeAndCall transaction exists.",
        ],
    ),
    dict(
        role="proxy_admin",
        selector="0x99a88ec4",
        signature="upgrade(address,address)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address", "address"],
        payable=False,
        guard="caller == owner (slot 0)",
        writes=["EIP-1967 implementation slot of the target proxy"],
        reads=["slot 0 (owner)"],
        events=[],
        errors=["NotOwner()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/proxy_admin_local/replay.json",
            "proxy_admin_behavior.json",
        ],
        replay_tests=[],
        undecided=[
            "No historical upgrade transaction is saved; the local replay accepts a no-code target, which is a hazard rather than an observed action.",
        ],
    ),
    dict(
        role="user_deposit_proxy_representative",
        selector="0x0c506e96",
        signature="withdrawStuckToken(address,uint256)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address", "uint256"],
        payable=False,
        guard="msg.sender == the user address embedded in the runtime code",
        writes=["none; the call reaches an arbitrary ERC-20 target"],
        reads=["runtime constants only"],
        events=["StuckTokenWithdrawn(address,address,uint256)"],
        errors=["0x08c379a0 (transfer-failed string revert)"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/deposit_proxy_local/replay.json",
            "deposit_proxy_behavior.json",
        ],
        replay_tests=[],
        undecided=[
            "No historical rescue transaction is saved.",
            "A no-code token target still emits StuckTokenWithdrawn locally, so the event alone does not evidence a token movement.",
        ],
    ),
    dict(
        role="user_deposit_proxy_representative",
        selector="0x925b3aad",
        signature="sweepAllToExchange(uint64,uint64,uint64)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["uint64", "uint64", "uint64"],
        payable=False,
        guard="msg.sender == the exchange address embedded in the runtime code",
        writes=["none; the call enqueues HyperCore CoreWriter actions"],
        reads=["runtime constants only"],
        events=[],
        errors=["CoreAmountOverflow()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/deposit_proxy_local/replay.json",
            "../../artifacts/historical/0xd4ee56dd5d1e271b8fc142e340362d3ab1eede92a9810ab33de4d90a9f798257.calls.json",
            "deposit_proxy_behavior.json",
        ],
        replay_tests=[],
        undecided=[
            "The one historical sweep is a different proxy in the same runtime family; this address has no saved call of its own.",
            "HyperCore settlement after the enqueued action is unverified.",
        ],
    ),
    dict(
        role="timelock",
        selector="0x88aa4c12",
        signature="execute(address,uint256,bytes,bytes32)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address", "uint256", "bytes", "bytes32"],
        payable=True,
        guard="caller == owner (slot 0); the scheduled operation must be ready and msg.value must equal the scheduled value",
        writes=[
            "operation done flag in mapping base slot 2 for the operation id",
            "the target contract's storage, through the executed call",
        ],
        reads=["slot 0 (owner)", "operation timestamp mapping base slot 2"],
        events=["OperationExecuted(bytes32,address,uint256,bytes)"],
        errors=[
            "NotOwner()",
            "OperationNotScheduled()",
            "OperationNotReady()",
            "InvalidValue()",
            "ExecutionFailed(bytes)",
            "0x18d96a80 (already done)",
        ],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "timelock_behavior.json",
            "timelock_pseudocode.md",
        ],
        replay_tests=["testTimelockScheduleSingleAndExecute", "testDecodeGuards"],
        undecided=[
            "No historical execution exists: both scheduled operations were ready but unexecuted at the pin, so the only successes are read-only probes and this local replay.",
            "The predecessor argument is not enforced by this runtime; the record states the observed behavior, not the intended design.",
        ],
    ),
    dict(
        role="timelock",
        selector="0x8a99d586",
        signature="updateMinDelay(uint256)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["uint256"],
        payable=False,
        guard="msg.sender == address(this): self-call only, not the owner",
        writes=["minimum delay slot 1"],
        reads=["none before the guard"],
        events=["MinDelayUpdated(uint256)"],
        errors=["NotSelf()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "timelock_behavior.json",
            "timelock_all_logs.json",
        ],
        replay_tests=["testTimelockSelfGatedSetters", "testDecodeGuards"],
        undecided=[
            "The only historical MinDelayUpdated log came from a self-call during construction of the suite; no later governance execution is saved.",
            "The earlier read-only probe recorded no storage post-state, so the slot-1 write was only assumed until this replay.",
        ],
    ),
    dict(
        role="timelock",
        selector="0x8b07f62b",
        signature="scheduleBatch(address[],uint256[],bytes[],bytes32)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address[]", "uint256[]", "bytes[]", "bytes32"],
        payable=False,
        guard="caller == owner (slot 0); array lengths must agree",
        writes=["ready timestamp for the batch operation id in mapping base slot 2"],
        reads=["slot 0 (owner)", "mapping base slot 2"],
        events=["BatchOperationScheduled(bytes32,uint256,bytes32,uint256)"],
        errors=["NotOwner()", "LengthMismatch()", "OperationAlreadyScheduled()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "timelock_behavior.json",
        ],
        replay_tests=["testTimelockScheduleBatchAndExecuteBatch", "testDecodeGuards"],
        undecided=[
            "No historical batch schedule is saved; the two historical operations used the single-target schedule path.",
        ],
    ),
    dict(
        role="timelock",
        selector="0xa6cc2c8c",
        signature="executeBatch(address[],uint256[],bytes[],bytes32)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["address[]", "uint256[]", "bytes[]", "bytes32"],
        payable=True,
        guard="caller == owner (slot 0); the batch must be ready and msg.value must equal the summed values",
        writes=["batch done flag in mapping base slot 2", "target storage through each executed call"],
        reads=["slot 0 (owner)", "mapping base slot 2"],
        events=["BatchOperationExecuted(bytes32,uint256)"],
        errors=[
            "NotOwner()",
            "OperationNotScheduled()",
            "OperationNotReady()",
            "InvalidValue()",
            "LengthMismatch()",
            "ExecutionFailed(bytes)",
        ],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "timelock_behavior.json",
        ],
        replay_tests=["testTimelockScheduleBatchAndExecuteBatch", "testDecodeGuards"],
        undecided=[
            "No historical batch execution exists; the pinned simulations and this local replay are the only executions.",
            "A failed second target was observed to roll back both targets in the read-only probe; the local replay covers only the success path.",
        ],
    ),
    dict(
        role="timelock",
        selector="0xc4d252f5",
        signature="cancel(bytes32)",
        name_status="hash-verified reconstructed signature; original Solidity identifier unverified",
        abi=["bytes32"],
        payable=False,
        guard="caller == owner (slot 0); the operation must be scheduled and not done",
        writes=["clears the ready timestamp in mapping base slot 2"],
        reads=["slot 0 (owner)", "mapping base slot 2"],
        events=["OperationCancelled(bytes32)"],
        errors=["NotOwner()", "OperationNotScheduled()", "0x18d96a80 (already done)"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "timelock_behavior.json",
        ],
        replay_tests=["testTimelockCancel", "testDecodeGuards"],
        undecided=[
            "No historical cancel transaction is saved; the two scheduled operations were never cancelled at the pin.",
        ],
    ),
    dict(
        role="timelock",
        selector="0xf2fde38b",
        signature="transferOwnership(address)",
        name_status="hash-verified reconstructed signature; the public candidate _SIMONdotBLACK_(...) is a hash collision and is rejected",
        name_candidates=["transferOwnership(address)"],
        rejected_candidates=["_SIMONdotBLACK_(int8[],uint256,address,bytes8,int96)"],
        abi=["address"],
        payable=False,
        guard="msg.sender == address(this): self-call only, not the owner",
        writes=["owner slot 0"],
        reads=["none before the guard"],
        events=["OwnerUpdated(address)"],
        errors=["NotSelf()", "InvalidOwner()"],
        evidence_tier="exact-runtime replay",
        evidence_paths=[
            "../../artifacts/selector_gap_other/replay.json",
            "timelock_behavior.json",
            "timelock_all_logs.json",
        ],
        replay_tests=["testTimelockSelfGatedSetters", "testDecodeGuards"],
        undecided=[
            "The historical owner write happened at construction; the only later historical OwnerUpdated log is the initializer.",
            "A second public 4-byte preimage exists for this selector and is not a real name of this contract.",
        ],
    ),
]

# Selectors of the same families that already have a proof and stay separate here: the
# fixed-revert entrypoints and the initializer-shaped stubs. `expected_error` is the
# hash-checked revert payload, `expected_words` the decoded ABI head word count.
KEPT_SEPARATE = [
    dict(
        role="session_key_manager_implementation",
        selector="0x17a1678f",
        kind="fixed revert",
        expected_error="0xd2dd8531",
        expected_words=3,
        source_name_status="unresolved; the report candidate registerSessionKeyDirect(address,uint64,address) is hash-matching only",
        proof_evidence="session_disabled_selector_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="staking_implementation",
        selector="0x2e17de78",
        kind="fixed revert",
        expected_error="0xa15ce1ba",
        expected_words=1,
        source_name_status="unresolved; public unstake(uint256) remains a candidate",
        proof_evidence="staking_direct_stubs_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="staking_implementation",
        selector="0xa694fc3a",
        kind="fixed revert",
        expected_error="0xa15ce1ba",
        expected_words=1,
        source_name_status="unresolved; public stake(uint256) remains a candidate",
        proof_evidence="staking_direct_stubs_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="staking_implementation",
        selector="0x4e71d92d",
        kind="fixed revert",
        expected_error="0xa15ce1ba",
        expected_words=0,
        source_name_status="unresolved; public claim() remains a candidate",
        proof_evidence="staking_direct_stubs_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="staking_implementation",
        selector="0xe4fc6b6d",
        kind="fixed revert",
        expected_error="0xa15ce1ba",
        expected_words=0,
        source_name_status="unresolved; public distribute() remains a candidate",
        proof_evidence="staking_direct_stubs_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="tokenomics_implementation",
        selector="0xdb006a75",
        kind="fixed revert",
        expected_error="0x32aa90b0",
        expected_words=1,
        source_name_status="unresolved; public redeem(uint256) is hash-matching only",
        proof_evidence="tokenomics_redemption_stub_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="tokenomics_implementation",
        selector="0xfe16eae8",
        kind="fixed revert",
        expected_error="0x32aa90b0",
        expected_words=1,
        source_name_status="unresolved; public quoteRedemption(uint256) is hash-matching only",
        proof_evidence="tokenomics_redemption_stub_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="tokenomics_implementation",
        selector="0x7c7df7b4",
        kind="fixed revert",
        expected_error="0x32aa90b0",
        expected_words=7,
        source_name_status="unresolved; the selector tool's five-argument inference is incomplete",
        proof_evidence="tokenomics_seven_word_stub_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
    dict(
        role="staking_implementation",
        selector="0xc0c53b8b",
        kind="initializer stub",
        expected_error="0xb7b2509c",
        expected_words=3,
        source_name_status="unresolved; report candidate initialize(address,address,address) is hash-matching only",
        proof_evidence="legacy_initializer_stubs_behavior.json",
        replay_evidence="../../artifacts/remaining_initializers_local/replay.json",
    ),
    dict(
        role="batch_executor_implementation",
        selector="0xc0c53b8b",
        kind="initializer stub",
        expected_error="0xb7b2509c",
        expected_words=3,
        source_name_status="unresolved; report candidate initialize(address,address,address) is hash-matching only",
        proof_evidence="legacy_initializer_stubs_behavior.json",
        replay_evidence="../../artifacts/batch_control_local/replay.json",
    ),
    dict(
        role="deposit_proxy_factory_implementation",
        selector="0xc4d66de8",
        kind="initializer stub",
        expected_error="0xb7b2509c",
        expected_words=1,
        source_name_status="unresolved; report candidate initialize(address) is hash-matching only",
        proof_evidence="legacy_initializer_stubs_behavior.json",
        replay_evidence="../../artifacts/fixed_revert_local/replay.json",
    ),
]

# Bytes-level expectations observed in this session from the pinned runtimes. `push` is the
# PC of the PUSH4 <selector> dispatch compare, `target` the PC it jumps to, `body` the
# executed body PC after any trampoline, `form` the dispatch idiom.
STATIC = {
    ("0x433bd418ec92818a960585f4d5fae563e735bb4a", "0x9dc29fac"): dict(push=0xA2, target=0x32F, body=0x32F, form="EQ"),
    ("0x433bd418ec92818a960585f4d5fae563e735bb4a", "0xfca3b5aa"): dict(push=0xEE, target=0xFB, body=0xFB, form="EQ"),
    ("0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f", "0x12baae3b"): dict(push=0x29, target=0x597, body=0x597, form="EQ"),
    ("0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f", "0x485cc955"): dict(push=0x4A, target=0x438, body=0x438, form="EQ"),
    ("0x8a5069fe303e8f81e91825436e956d595032e558", "0xcf8fbec9"): dict(push=0xFA, target=0x215, body=0x215, form="EQ"),
    ("0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0", "0x0f71c8bc"): dict(push=0x29, target=0x49F, body=0x49F, form="EQ"),
    ("0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0", "0xc6f881bc"): dict(push=0x6B, target=0x2D1, body=0x2D1, form="EQ"),
    ("0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262", "0x0f71c8bc"): dict(push=0x26, target=0x83A, body=0x83A, form="EQ"),
    ("0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262", "0x9ccae24e"): dict(push=0x68, target=0x19C, body=0x19C, form="EQ"),
    ("0xe6e3519455170913c5c3bfe541dd918a2d0cbb15", "0x0f71c8bc"): dict(push=0x29, target=0xD29, body=0xD29, form="EQ"),
    ("0xe79c91cc682f1bb401a9cab74c900470190f0f8f", "0x7eff275e"): dict(push=0x1E, target=0x28B, body=0x28B, form="EQ"),
    ("0xe79c91cc682f1bb401a9cab74c900470190f0f8f", "0x9623609d"): dict(push=0x35, target=0x194, body=0x194, form="EQ"),
    ("0xe79c91cc682f1bb401a9cab74c900470190f0f8f", "0x99a88ec4"): dict(push=0x40, target=0xE6, body=0xE6, form="EQ"),
    ("0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f", "0x88aa4c12"): dict(push=0x5C, target=0x566, body=0x570, form="EQ"),
    ("0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f", "0x8a99d586"): dict(push=0x67, target=0x50B, body=0x50B, form="EQ"),
    ("0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f", "0x8b07f62b"): dict(push=0x72, target=0x43B, body=0x43B, form="EQ"),
    ("0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f", "0xa6cc2c8c"): dict(push=0x88, target=0x2E6, body=0x2F0, form="EQ"),
    ("0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f", "0xc4d252f5"): dict(push=0x9E, target=0x194, body=0x194, form="EQ"),
    ("0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f", "0xf2fde38b"): dict(push=0xBE, target=0xC8, body=0xC8, form="SUB"),
    ("0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce", "0x0c506e96"): dict(push=0x1F, target=0x3AA, body=0x3AA, form="EQ"),
    ("0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce", "0x925b3aad"): dict(push=0x36, target=0x94, body=0x94, form="EQ"),
    # kept-separate rows
    ("0x8a5069fe303e8f81e91825436e956d595032e558", "0x17a1678f"): dict(push=0x29, target=0xA97, body=0xA97, form="EQ"),
    ("0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0", "0xc4d66de8"): dict(push=0x60, target=0x337, body=0x337, form="EQ"),
    ("0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262", "0xc0c53b8b"): dict(push=0x73, target=0x15E, body=0x15E, form="EQ"),
    ("0xe6e3519455170913c5c3bfe541dd918a2d0cbb15", "0xc0c53b8b"): dict(push=0x126, target=0x6AE, body=0x6AE, form="EQ"),
    ("0xe6e3519455170913c5c3bfe541dd918a2d0cbb15", "0x2e17de78"): dict(push=0x4A, target=0x6E8, body=0xE81, form="EQ"),
    ("0xe6e3519455170913c5c3bfe541dd918a2d0cbb15", "0xa694fc3a"): dict(push=0x11B, target=0x6E8, body=0xE81, form="EQ"),
    ("0xe6e3519455170913c5c3bfe541dd918a2d0cbb15", "0x4e71d92d"): dict(push=0x6B, target=0x5BD, body=0xEA4, form="EQ"),
    ("0xe6e3519455170913c5c3bfe541dd918a2d0cbb15", "0xe4fc6b6d"): dict(push=0x15D, target=0x5BD, body=0xEA4, form="EQ"),
    ("0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f", "0xdb006a75"): dict(push=0xB8, target=0x2A0, body=0x2A0, form="EQ"),
    ("0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f", "0xfe16eae8"): dict(push=0xF9, target=0x106, body=0x106, form="EQ"),
    ("0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f", "0x7c7df7b4"): dict(push=0x55, target=0x3F2, body=0x3F2, form="EQ"),
}

# Event signature -> topic0, and error name -> selector, hash-checked here with cast keccak.
EVENT_TOPICS = {
    "Transfer(address,address,uint256)": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    "MinterUpdated(address)": "0xad0f299ec81a386c98df0ac27dae11dd020ed1b56963c53a7292e7a3a314539a",
    "OwnerUpdated(address)": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
    "AuthorizedDeployerUpdated(address)": "0x09bdaf5fdab1e55bea2219aeaa3c7334e422f842e1fb25dc319e8a2b3d5e0167",
    "AuthorizedCallerUpdated(address)": "0xfe60173cc964bc674632fcf67031bba24c8a99a4a7d6518c726586978b7e30d3",
    "AuthorizedRelayerUpdated(address,bool)": "0x431c9efc75fd5a8b5d510e3458e1c31ac5c3de0385743f60f76491e1e0867391",
    "AuthorizedExecutorUpdated(address)": "0x3cfda8ee6e20b237d2949c3d16b6f12822b6f1bc0580f188f932c0771cac729d",
    "MintParamsUpdated(uint256,uint256,uint256,uint256)": "0xdbf6f1878073adede0b153c63f457c1c601a056124755086092f973f19550176",
    "StuckTokenWithdrawn(address,address,uint256)": "0x3d95e1dd133840fdfe95e9a3b6c9fc44f85019531359313e278c6e358ef5b1e0",
    "OperationScheduled(bytes32,address,uint256,bytes,bytes32,uint256)": "0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39",
    "BatchOperationScheduled(bytes32,uint256,bytes32,uint256)": "0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f",
    "OperationExecuted(bytes32,address,uint256,bytes)": "0x2a08801cf3674ab09756ae78a3a4833813465af6af958136b360eab6b71c8952",
    "BatchOperationExecuted(bytes32,uint256)": "0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd",
    "OperationCancelled(bytes32)": "0xcf0f63b97f3387253cbc0bde884f975df77e39184dc3280c2c81be495f58eef4",
    "MinDelayUpdated(uint256)": "0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464",
}
ERROR_SELECTORS = {
    "NotOwner()": "0x30cd7471",
    "NotMinter()": "0xf8d2906c",
    "InsufficientBalance()": "0xf4d678b8",
    "InvalidExchange()": "0x40892c33",
    "AlreadyInitialized()": "0x0dc149f0",
    "InvalidMintParams()": "0xbad8ef95",
    "NotSelf()": "0x29c3b7ee",
    "InvalidOwner()": "0x49e27cff",
    "OperationNotScheduled()": "0x27c0d610",
    "OperationNotReady()": "0xf800799b",
    "InvalidValue()": "0xaa7feadc",
    "LengthMismatch()": "0xff633a38",
    "OperationAlreadyScheduled()": "0x9b382476",
    "ExecutionFailed(bytes)": "0x15fcd675",
    "CoreAmountOverflow()": "0xfadaa871",
    "0x08c379a0 (transfer-failed string revert)": "0x08c379a0",
    "0xc031a0df (caller is not the proxy admin)": "0xc031a0df",
    "0x3f733c4f (already initialized)": "0x3f733c4f",
    "0x18d96a80 (already done)": "0x18d96a80",
}
TERMINALS = {"RETURN", "REVERT", "STOP", "INVALID", "SELFDESTRUCT"}
EFFECT_OPS = {
    "SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL",
    "CREATE", "CREATE2", "LOG1", "LOG2", "LOG3", "LOG4", "RETURN", "SELFDESTRUCT",
}
def keccak(text):
    return subprocess.run(["cast", "keccak", text], capture_output=True, text=True,
                          check=True).stdout.strip()


def selector_of(signature):
    return keccak(signature)[:10]


def disassemble(runtime_hex):
    raw = subprocess.run(["cast", "disassemble", "--json", runtime_hex],
                         capture_output=True, text=True, check=True).stdout
    lines = json.loads(raw)["data"].splitlines()
    instructions = {}
    for line in lines:
        if len(line) > 10 and line[8:10] == ": ":
            instructions[int(line[:8], 16)] = line.split(": ", 1)[1]
    return instructions


class Runtime:
    def __init__(self, manifest, address):
        self.address = address
        row = manifest["contracts"][address]
        self.row = row
        self.path = ATLAS / row["runtime_file"]
        self.hex = self.path.read_text().strip()
        self.bytes = bytes.fromhex(self.hex[2:])
        assert hashlib.sha256(self.bytes).hexdigest() == row["sha256"], address
        self.instructions = disassemble(self.hex)
        self.pcs = sorted(self.instructions)
        self.index = {pc: i for i, pc in enumerate(self.pcs)}
        self.targets = {}
        for pc, op in self.instructions.items():
            if not op.startswith("PUSH4 "):
                continue
            window = [self.instructions[self.pcs[j]]
                      for j in range(self.index[pc], min(self.index[pc] + 6, len(self.pcs)))]
            if "EQ" in window or "SUB" in window:
                form = "EQ" if "EQ" in window else "SUB"
                marker = window.index(form)
                if form == "EQ":
                    for following in window[marker + 1:]:
                        if following.startswith("PUSH2 "):
                            self.targets[(op.split()[1], form, pc)] = int(following.split()[1], 16)
                            break
                else:
                    tail = self.pcs[self.index[pc] + marker + 1:]
                    jumpi = next(p for p in tail if self.instructions[p] == "JUMPI")
                    self.targets[(op.split()[1], form, pc)] = jumpi + 1
    def idiom_bytes(self, pc, length=12):
        return self.bytes[pc:pc + length].hex()
    def extent(self, lo, hi):
        return [(pc, self.instructions[pc]) for pc in self.pcs if lo <= pc < hi]
    def resolve_body(self, target, ceiling):
        """Follow a jump-only entry stub to the body the stub transfers control to."""
        stub = []
        for pc, op in self.extent(target, ceiling):
            stub.append((pc, op))
            if op.startswith("PUSH2 "):
                continue
            if op in TERMINALS:
                break
            if op in EFFECT_OPS:
                break
            if op == "JUMP":
                # `PUSH2 <resume>; [CALLDATASIZE]; PUSH2 <decoder>; JUMP` resumes at <resume>.
                ordered = [int(o.split()[1], 16) for _, o in stub if o.startswith("PUSH2 ")]
                if any(o == "CALLDATASIZE" for _, o in stub):
                    return ordered[0], "decoder-resume"
                return ordered[-1], "tail-call"
            if op == "JUMPI":
                break
        return target, "inline"


def build_static(manifest):
    findings = {}
    for (address, selector), expected in STATIC.items():
        runtime = CACHE.get(address) or Runtime(manifest, address)
        CACHE[address] = runtime
        hits = [(key, value) for key, value in runtime.targets.items() if key[0] == selector]
        assert len(hits) == 1, (address, selector, hits)
        (key, target) = hits[0]
        _, form, push_pc = key
        assert push_pc == expected["push"], (address, selector, hex(push_pc))
        assert form == expected["form"], (address, selector, form)
        assert target == expected["target"], (address, selector, hex(target))
        following = [t for t in runtime.targets.values() if t > target]
        ceiling = min(following) if following else max(runtime.pcs) + 1
        body, resolution = runtime.resolve_body(target, ceiling)
        assert body == expected["body"], (address, selector, hex(body), resolution)
        below = [t for t in runtime.targets.values() if t > body]
        body_ceiling = min(below) if below else max(runtime.pcs) + 1
        region = runtime.extent(body, body_ceiling)
        guard_region = region[:8]
        nonpayable = any(op == "CALLVALUE" for _, op in guard_region)
        effects = [(hex(pc), op) for pc, op in region if op in EFFECT_OPS]
        reads, writes = [], []
        indirect_reads = indirect_writes = 0
        pending = None
        for pc, op in region:
            if op.startswith("PUSH") and len(op.split()) > 1:
                pending = op.split()[1]
            elif op in ("SLOAD", "SSTORE"):
                value = None
                if pending is not None:
                    value = int(pending, 16)
                plausible = (value is not None and value <= 0x60) or pending == ADMIN_SLOT
                entry = (hex(pc), pending if plausible else None)
                if not plausible:
                    if op == "SLOAD":
                        indirect_reads += 1
                    else:
                        indirect_writes += 1
                (reads if op == "SLOAD" else writes).append(entry)
        errors = []
        for i, (pc, op) in enumerate(region):
            if not op.startswith("PUSH4 "):
                continue
            for pc2, op2 in region[i + 1:i + 6]:
                if not op2.startswith("PUSH1 ") or not any(o == "SHL" for _, o in region[i + 1:i + 6]):
                    continue
                value = int(op.split()[1], 16)
                shift = int(op2.split()[1], 16)
                word = ((value << shift) % (1 << 256)).to_bytes(32, "big")
                errors.append(dict(pc=hex(pc), pushed=op.split()[1], shift=shift,
                                   payload="0x" + word[:4].hex()))
                break
        # The compiler inlines the decoded ABI head length for some entrypoints as
        # `PUSH1 <32 * width>; CALLDATASIZE; ...; SLT`. Record it when it is visible in the
        # dispatched body; None means the constant lives in shared dispatcher/decoder code.
        guard_words = None
        for i, (pc, op) in enumerate(region[:16]):
            window = [o for _, o in region[i:i + 8]]
            if "CALLDATASIZE" not in window or not ("SLT" in window or "LT" in window):
                continue
            if op == "PUSH0" and window[:2] == ["PUSH0", "CALLDATASIZE"]:
                guard_words = 0
                break
            if op.startswith("PUSH1 ") and int(op.split()[1], 16) != 0x03:
                guard_words = int(op.split()[1], 16) // 32
                break
        revert_pc = next((pc for pc, op in region if op == "REVERT"), None)
        revert_effects = None
        revert_range = None
        if revert_pc is not None:
            revert_range = [hex(body), hex(revert_pc + 1)]
            revert_effects = [(hex(pc), op) for pc, op in runtime.extent(body, revert_pc + 1)
                              if op in EFFECT_OPS]
        findings[(runtime.address, selector)] = dict(
            inline_guard_word_count=guard_words,
            revert_only_range=revert_range, revert_only_effect_opcodes=revert_effects,
            selector_push_pc=push_pc, dispatch_form=form, dispatch_target_pc=target,
            body_pc=body, body_resolution=resolution,
            dispatch_idiom_bytes=runtime.idiom_bytes(push_pc), nonpayable=nonpayable,
            body_region=[hex(body), hex(body_ceiling)], effect_opcodes=effects,
            static_sload_candidates=reads, static_sstore_candidates=writes,
            static_slot_constants_indirect=dict(reads=indirect_reads, writes=indirect_writes),
            error_constructions=errors,
        )
    return findings


CACHE = {}


def verify_names(findings):
    for name, topic in EVENT_TOPICS.items():
        assert keccak(name) == topic, (name, keccak(name), topic)
    for name, selector in ERROR_SELECTORS.items():
        assert re.fullmatch(r"0x[0-9a-f]{8}", selector), (name, selector)
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\(.*\)", name):
            assert selector_of(name) == selector, (name, selector_of(name), selector)
        else:
            assert selector in name, (name, selector)
    for row in ROWS:
        if row["signature"]:
            assert selector_of(row["signature"]) == row["selector"], row["signature"]
    for row in KEPT_SEPARATE:
        if row["source_name_status"].startswith("unresolved; public"):
            candidate = row["source_name_status"].split("public ", 1)[1].split(" ", 1)[0]
            assert selector_of(candidate) == row["selector"], (candidate, row["selector"])
    for row in ROWS:
        for candidate in row.get("name_candidates", []):
            if candidate in ("watch_tg_invmru_7bd442a(uint256,address,uint256)",
                             "watch_tg_invmru_10757d42(bool,bool)",
                             "_SIMONdotBLACK_(int8[],uint256,address,bytes8,int96)"):
                assert selector_of(candidate) == row["selector"], candidate
            else:
                assert selector_of(candidate) == row["selector"], candidate


def verify_evidence(findings):
    """Check the saved artifacts the rows cite, and the row's bytecode claims."""
    deposit = json.loads((ATLAS / "deposit_proxy_behavior.json").read_text())
    topic = deposit["event_catalog"][0]["topic0"]
    assert topic == keccak("StuckTokenWithdrawn(address,address,uint256)"), topic
    EVENT_TOPICS["StuckTokenWithdrawn(address,address,uint256)"] = topic

    ledger_events = {
        "paper_token_behavior.json": "event_catalog",
        "session_key_behavior.json": "event_catalog",
        "batch_control_behavior.json": "event_catalog",
        "proxy_admin_behavior.json": "event_catalog",
        "tokenomics_owner_transfer_behavior.json": "event_catalog",
    }
    for name, key in ledger_events.items():
        data = json.loads((ATLAS / name).read_text())
        for event in data[key]:
            signature = event.get("reconstructed_signature")
            if signature and signature in EVENT_TOPICS:
                assert event["topic0"] == EVENT_TOPICS[signature], (name, signature)

    for row in ROWS:
        for error in row["errors"]:
            assert re.fullmatch(r"0x[0-9a-f]{8}", ERROR_SELECTORS[error]), error
        for channel in row["evidence_paths"]:
            assert (ATLAS / channel).resolve().exists(), (row["selector"], channel)
    for row in KEPT_SEPARATE:
        assert (ATLAS / row["proof_evidence"]).resolve().exists(), row["selector"]
        assert (ATLAS / row["replay_evidence"]).resolve().exists(), row["selector"]

    # Kept-separate rows: the revert payload and the decoder requirement must be visible in
    # the pinned bytes, and the body must be effect-free.
    for row in KEPT_SEPARATE:
        key = (RUNTIMES[row["role"]], row["selector"])
        static = findings[key]
        payloads = {entry["payload"] for entry in static["error_constructions"]}
        assert row["expected_error"] in payloads, (row["selector"], payloads)
        assert static["revert_only_effect_opcodes"] == [], (
            row["selector"], static["revert_only_effect_opcodes"])
        guard_words = static["inline_guard_word_count"]
        if guard_words is not None:
            assert guard_words == row["expected_words"], (row["selector"], guard_words)
    for row in ROWS:
        key = (RUNTIMES[row["role"]], row["selector"])
        static = findings[key]
        assert static["nonpayable"] != row["payable"], (row["selector"], row["payable"])
        guard_words = static["inline_guard_word_count"]
        if guard_words is not None:
            assert guard_words == len(row["abi"]), (row["selector"], guard_words, row["abi"])
    return findings


def verify_replay():
    assert REPLAY_SOURCE.exists(), (
        "artifacts/selector_gap_other/SelectorGapLocal.t.sol is missing; it is the replay source "
        "recorded in replay.json")
    assert REPLAY_JSON.exists(), (
        "artifacts/selector_gap_other/replay.json is missing; run "
        "python3 scripts/atlas_selector_gap_other.py --replay on a machine with forge")
    record = json.loads(REPLAY_JSON.read_text())
    source = REPLAY_SOURCE.read_text()
    assert record["source_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    assert record["test_source_sha256"] == record["source_sha256"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    for label, entry in record["runtime_hashes"].items():
        assert manifest["contracts"][entry["address"]]["sha256"] == entry["sha256"], label
    expected = sorted(re.findall(r"function (test\w+)\(", source))
    assert record["passed_tests"] == expected, (record["passed_tests"], expected)
    assert record["pin"] == manifest["block"] and record["block_hash"] == manifest["block_hash"]
    covered = set()
    for row in ROWS:
        covered.update(row["replay_tests"])
    assert covered <= set(record["passed_tests"]), sorted(covered - set(record["passed_tests"]))
    return record


def run_replay():
    """Regenerate the exact-runtime replay with a port-free in-process Forge EVM."""
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    source = REPLAY_SOURCE.read_text()
    wanted = {
        "SharedProxy.hex": "0x1629b7d46bef6e13ff754174fc9f32dea309b38f",
        "PaperProxy.hex": "0xe40f17915daa230324030003a197cdaef2261c0e",
        "PaperImplementation.hex": "0x433bd418ec92818a960585f4d5fae563e735bb4a",
        "SessionImplementation.hex": "0x8a5069fe303e8f81e91825436e956d595032e558",
        "FactoryImplementation.hex": "0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0",
        "TokenomicsImplementation.hex": "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f",
        "Timelock.hex": "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
        "BatchProxy.hex": "0x233ff29b239abc1d7748605da9b205c3e008626e",
        "BatchImplementation.hex": "0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262",
        "ProxyAdmin.hex": "0xe79c91cc682f1bb401a9cab74c900470190f0f8f",
    }
    with tempfile.TemporaryDirectory(prefix="papertrade-selector-gap-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(shutil.which("solc")) +
            "\noffline = true\nfs_permissions = [{ access = \"read\", path = \"./runtime\" }]\n")
        (project / "test" / "SelectorGapLocal.t.sol").write_text(source)
        hashes = {}
        for filename, address in wanted.items():
            runtime = (ATLAS / manifest["contracts"][address]["runtime_file"]).read_text().strip()
            (project / "runtime" / filename).write_text(runtime)
            hashes[filename.removesuffix(".hex")] = dict(
                address=address, sha256=manifest["contracts"][address]["sha256"])
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-contract",
                              "SelectorGapLocalTest", "-vv"],
                             capture_output=True, text=True, timeout=300)
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    expected = sorted(re.findall(r"function (test\w+)\(", source))
    if run.returncode or passed != expected:
        raise RuntimeError(output)
    record = dict(
        pin=manifest["block"], block_hash=manifest["block_hash"],
        method=("port-free in-process Forge EVM; exact pinned proxy, implementation, timelock "
                "and ProxyAdmin runtimes injected with vm.etch; pinned owner and EIP-1967 slots "
                "set with vm.store; fresh initialization states are synthetic; no transaction sent"),
        runtime_hashes=hashes, test_names=expected, passed_tests=passed,
        forge_result=f"{len(passed)} passed, 0 failed",
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        test_source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        covered_selectors=sorted({row["selector"] for row in ROWS if row["replay_tests"]}),
        limits=[
            "Synthetic local state: the fresh-state initializer paths were never executed on chain.",
            "No historical transaction is replayed by this harness; it exercises exact runtime code only.",
        ],
    )
    REPLAY_JSON.write_text(json.dumps(record, indent=2) + "\n")
    print(f"selector gap local replay: {len(passed)} exact-runtime tests passed")
    return record


def rpc(method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(RPC, data=payload, headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def capture():
    """Refresh the live latest-state reads and store every raw JSON-RPC response."""
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = OUT / "live" / stamp
    directory.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    head = rpc("eth_blockNumber", [])
    (directory / "eth_blockNumber.json").write_text(json.dumps(head, indent=2) + "\n")
    slots = {}
    for label, address in PROXY_SLOT_CHECKS.items():
        call = rpc("eth_getStorageAt", [address, IMPLEMENTATION_SLOT, "latest"])
        (directory / f"implementation_slot_{label}.json").write_text(json.dumps(call, indent=2) + "\n")
        slots[label] = dict(proxy=address, implementation="0x" + call["result"][-40:])
    for label in ("session_key_manager_proxy", "tokenomics_proxy", "deposit_proxy_factory_proxy"):
        call = rpc("eth_getStorageAt", [PROXY_SLOT_CHECKS[label], ADMIN_SLOT, "latest"])
        (directory / f"admin_slot_{label}.json").write_text(json.dumps(call, indent=2) + "\n")

    def live_code(address, name):
        """Fetch code at latest. The stored `runtime_bytes` never claims to be pinned state."""
        call = rpc("eth_getCode", [address, "latest"])
        (directory / f"eth_getCode_{name}.json").write_text(json.dumps(call, indent=2) + "\n")
        code = bytes.fromhex(call["result"][2:]) if call.get("result", "0x") != "0x" else b""
        return dict(address=address, runtime_bytes=len(code), sha256=hashlib.sha256(code).hexdigest())

    differences = {}
    for label, entry in slots.items():
        row = manifest["contracts"][entry["proxy"]]
        pinned = "0x" + row["eip1967_slots"]["implementation"][-40:]
        changed = entry["implementation"].lower() != pinned.lower()
        item = dict(proxy=entry["proxy"], pinned_implementation=pinned,
                    live_implementation=entry["implementation"], changed=changed)
        if changed:
            live = live_code(entry["implementation"], f"{label}_implementation")
            item.update(live_runtime_bytes=live["runtime_bytes"], live_sha256=live["sha256"])
        else:
            item.update(live_runtime_bytes=row["runtime_bytes"], live_sha256=row["sha256"],
                        note="live code hash not re-fetched because the slot still matches the pin")
        differences[label] = item
    for label in ("timelock", "proxy_admin"):
        address = RUNTIMES[label]
        row = manifest["contracts"][address]
        live = live_code(address, label)
        differences[label] = dict(
            proxy=None, pinned_implementation=address, live_implementation=address,
            changed=live["sha256"] != row["sha256"],
            live_runtime_bytes=live["runtime_bytes"], live_sha256=live["sha256"],
            pinned_runtime_bytes=row["runtime_bytes"], pinned_sha256=row["sha256"])
    record = dict(
        captured_at=stamp,
        latest_block=int(head["result"], 16),
        note=("latest-state reads only; the RPC ignores historical block numbers, so these values "
              "are not the pinned state"),
        implementation_slots=slots,
        pinned_vs_live=differences,
    )
    (directory / "summary.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"captured latest state at block {record['latest_block']} into {directory}")
    return record


def load_capture():
    directory = OUT / "live"
    if not directory.exists():
        return None
    stamps = sorted(entry for entry in directory.iterdir() if entry.is_dir())
    if not stamps:
        return None
    return json.loads((stamps[-1] / "summary.json").read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", action="store_true", help="regenerate the Forge replay")
    parser.add_argument("--capture", action="store_true", help="refresh the live latest reads")
    args = parser.parse_args()
    if args.replay:
        run_replay()
    if args.capture:
        capture()

    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == 48902346
    assert manifest["block_hash"] == "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
    unresolved = json.loads((ATLAS / "unresolved.json").read_text())
    gap = [row for row in unresolved["state_changing_selectors_without_saved_historical_trace"]
           if row["role"] not in ("exchange_implementation", "exchange_linked_library_live")]
    assigned = {(row["role"], row["selector"]) for row in gap}
    recorded = {(row["role"], row["selector"]) for row in ROWS}
    assert recorded == assigned, sorted(assigned ^ recorded)

    for address in RUNTIMES.values():
        CACHE[address] = Runtime(manifest, address)
    findings = build_static(manifest)
    verify_names(findings)
    verify_evidence(findings)
    replay = verify_replay()
    live = load_capture()

    for row in ROWS:
        key = (RUNTIMES[row["role"]], row["selector"])
        row["address"] = RUNTIMES[row["role"]]
        row["static_evidence"] = findings[key]
        row["static_evidence"]["source"] = "pinned runtime bytecode read in this script"
        row["event_topics"] = {name: EVENT_TOPICS[name] for name in row["events"]} if row["events"] else {}
        row["error_selectors"] = {name: ERROR_SELECTORS[name] for name in row["errors"]}
        row["decoded_head_words"] = len(row["abi"])
        if row["static_evidence"]["inline_guard_word_count"] is not None:
            row["inline_guard_constant_words"] = row["static_evidence"]["inline_guard_word_count"]
    for row in KEPT_SEPARATE:
        static = findings[(RUNTIMES[row["role"]], row["selector"])]
        row["address"] = RUNTIMES[row["role"]]
        row["revert_payload_construction"] = {
            entry["pc"]: entry for entry in static["error_constructions"]
            if entry["payload"] == row["expected_error"]}
        row["decoder_requirement_words"] = row["expected_words"]
        row["decoder_requirement_source"] = (
            "read from the pinned entry bytes and equal to the cited proof"
            if static["inline_guard_word_count"] == row["expected_words"]
            else "cited proof only; the inline width constant is not visible in the dispatched body")
        row["static_evidence"] = dict(
            selector_push_pc=static["selector_push_pc"],
            inline_guard_word_count=static["inline_guard_word_count"],
            revert_only_range=static["revert_only_range"],
            revert_only_effect_opcodes=static["revert_only_effect_opcodes"],
            dispatch_target_pc=static["dispatch_target_pc"],
            body_pc=static["body_pc"],
            dispatch_idiom_bytes=static["dispatch_idiom_bytes"],
            nonpayable=static["nonpayable"],
            effect_opcodes=static["effect_opcodes"],
            source_name_status=row["source_name_status"],
        )

    closed = [row for row in ROWS if row["evidence_tier"] != "undecided"]
    undecided = [row for row in ROWS if row["evidence_tier"] == "undecided"]
    families = {}
    for row in ROWS:
        families.setdefault(row["role"], []).append(row["selector"])
    ledger = dict(
        pin=manifest["block"],
        block_hash=manifest["block_hash"],
        generated_by="atlas_selector_gap_other.py",
        scope=(
            "The rows of unresolved.json state_changing_selectors_without_saved_historical_trace "
            "whose runtime role is not exchange_implementation or exchange_linked_library_live, plus "
            "the already-proven fixed-revert and initializer-stub selectors of the same families, kept "
            "separate. Exchange rows are covered by the sibling workstream."
        ),
        gap_row_count=len(gap),
        row_count=len(ROWS),
        counts=dict(
            assigned_rows=len(ROWS),
            assigned_rows_closed=len(closed),
            assigned_rows_undecided=len(undecided),
            kept_separate_fixed_reverts=len([r for r in KEPT_SEPARATE if r["kind"] == "fixed revert"]),
            kept_separate_initializer_stubs=len([r for r in KEPT_SEPARATE if r["kind"] == "initializer stub"]),
            rows_with_exact_runtime_replay=len([r for r in ROWS if "exact-runtime replay" == r["evidence_tier"]]),
            rows_by_family={role: len(items) for role, items in sorted(families.items())},
            rows_with_hash_verified_name=len([r for r in ROWS if r["signature"]]),
            rows_with_undefined_source_name=len([r for r in ROWS
                                                 if r["name_status"].startswith("undefined")]),
            rows_with_ambiguous_public_preimage=len([r for r in ROWS
                                                     if "ambiguous" in r["name_status"]]),
            rows_without_saved_historical_trace=len(ROWS),
        ),
        rows=ROWS,
        kept_separate_rows=KEPT_SEPARATE,
        local_replay=replay,
        live_latest_state=live,
        evidence_vocabulary=[
            "historical trace: a saved sampled historical call graph or trace in artifacts/",
            "exact-runtime replay: the pinned runtime bytes executed in a local EVM (this artifact) or saved pinned-state debug trace with storage diff",
            "pinned read-only probe: an eth_call or debug_traceCall against the pinned state",
            "bytecode-only static read: a claim read from the pinned bytes at a named program counter",
            "fixed revert: a canonical call that always reverted with a hash-checked payload",
        ],
        limits=[
            "No archive HyperEVM endpoint is available, so no historical refetch was possible; the pinned captures under atlas/block_48902346/runtime and artifacts/ are the only historical state.",
            "The record describes the pinned runtimes. Two proxies (SessionKeyManager and Tokenomics) point at different implementations at latest; see live_latest_state.",
            "Local replay successes are synthetic executions of exact code with local storage, not on-chain transactions.",
            "Decompiler output and public signature preimages are never promoted to proven names here.",
        ],
    )
    OUTPUT_JSON.write_text(json.dumps(ledger, indent=2) + "\n")
    write_markdown(ledger)
    print(f"selector gap other: {len(ROWS)} assigned rows, {len(closed)} closed, "
          f"{len(undecided)} undecided, {len(KEPT_SEPARATE)} kept separate")


def write_markdown(ledger):
    lines = []
    lines.append(f"# Non-Exchange selector gap rows at block {ledger['pin']:,}")
    lines.append("")
    lines.append(
        "This page is generated by `atlas_selector_gap_other.py` from the "
        f"[machine ledger](selector_gap_other.json). It covers the {ledger['row_count']} rows of "
        "[unresolved.json](unresolved.json) `state_changing_selectors_without_saved_historical_trace` "
        "whose runtime role is not Exchange, plus the already-proven fixed-revert and "
        f"initializer-stub selectors of the same families kept separate ({len(ledger['kept_separate_rows'])} rows). "
        "Every name here is either hash-verified against its selector or declared undefined; no "
        "decompiler guess or public preimage is promoted. Each row's bytecode facts are re-read from "
        "the pinned runtime bytes at a named program counter on every run.")
    lines.append("")
    counts = ledger["counts"]
    lines.append(
        f"{counts['assigned_rows_closed']} of {counts['assigned_rows']} assigned rows now carry a "
        "complete behavior record (ABI shape, guard, storage effects, events, evidence tier); "
        f"{counts['assigned_rows_undecided']} remain at evidence tier undecided. "
        f"{counts['rows_with_hash_verified_name']} rows carry a hash-verified reconstructed signature, "
        f"{counts['rows_with_undefined_source_name']} have no name at all and "
        f"{counts['rows_with_ambiguous_public_preimage']} of the signed rows resolve only to an "
        "ambiguous public preimage set. "
        f"All {counts['rows_without_saved_historical_trace']} still lack a saved historical call trace, "
        "which is the gap that keeps them on the unresolved list; the behavior itself is now evidenced.")
    lines.append("")
    lines.append("## Assigned rows")
    lines.append("")
    lines.append("| Role | Selector | Name | ABI shape | Guard | Writes | Events | Tier |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in ledger["rows"]:
        name = row["signature"] or "undefined"
        shape = ",".join(row["abi"]) + ("" if row["payable"] else " (nonpayable)")
        writes = "; ".join(row["writes"]) or "none"
        events = ", ".join(row["events"]) or "none"
        lines.append(f"| `{row['role']}` | `{row['selector']}` | `{name}` | `{shape}` | {row['guard']} "
                     f"| {writes} | {events} | {row['evidence_tier']} |")
    lines.append("")
    lines.append("## Bytecode shape per assigned row")
    lines.append("")
    lines.append("| Role | Selector | Push PC | Dispatch form | Body PC | Idiom bytes | Inline guard words "
                 "| Nonpayable | Effect opcodes in body | Linear-scan slot constants (approx) |")
    lines.append("|---|---|---:|---|---:|---|---|---|---|")
    for row in ledger["rows"]:
        static = row["static_evidence"]
        reads = ", ".join(f"SLOAD@{pc}:{slot}" for pc, slot in static["static_sload_candidates"]) or "none"
        writes = ", ".join(f"SSTORE@{pc}:{slot}" for pc, slot in static["static_sstore_candidates"]) or "none"
        effects = ", ".join(f"{op}@{pc}" for pc, op in static["effect_opcodes"][:6]) or "none"
        guard_words = static["inline_guard_word_count"]
        lines.append(
            f"| `{row['role']}` | `{row['selector']}` | {static['selector_push_pc']} "
            f"| {static['dispatch_form']} | {static['body_pc']} | `{static['dispatch_idiom_bytes']}` "
            f"| {'—' if guard_words is None else guard_words} "
            f"| {'yes' if static['nonpayable'] else 'no'} | {effects} | {reads} / {writes} |")
    lines.append("")
    lines.append("`Inline guard words` is the decoded ABI head length the compiler compares CALLDATASIZE "
                 "against when that constant is visible in the dispatched body; a dash means it lives in "
                 "shared dispatcher or decoder code, and the shape then rides on the exercised calldata "
                 "and the shared decode-guard replay test, which rejects a calldata prefix one head word "
                 "short with empty revert data. The linear-scan slot constants are read from the "
                 "dispatched body region with the nearest PUSH constant; only small slot numbers and the "
                 "EIP-1967 admin slot constant are shown, and the remaining "
                 "indirect counts (static_slot_constants_indirect) are recorded per row in the ledger. They "
                 "corroborate the guard and write list but are not a control-flow-proof decode; the "
                 "guard, write and event columns also ride on the exact-runtime replay.")
    lines.append("")
    lines.append("## Fixed-revert and initializer-stub rows kept separate")
    lines.append("")
    lines.append("| Role | Selector | Kind | Revert payload | Payload construction | Decoded head words | "
                 "Width source | Effect opcodes | Source name |")
    lines.append("|---|---|---|---|---:|---|---:|---|")
    for row in ledger["kept_separate_rows"]:
        construction = ", ".join(f"{pc}: {entry['pushed']} << {entry['shift']}"
                                 for pc, entry in sorted(row["revert_payload_construction"].items())) or "none"
        lines.append(
            f"| `{row['role']}` | `{row['selector']}` | {row['kind']} | `{row['expected_error']}` "
            f"| {construction} | {row['decoder_requirement_words']} "
            f"| {'pinned bytes' if row['static_evidence']['inline_guard_word_count'] == row['decoder_requirement_words'] else 'cited proof'} "
            f"| {len(row['static_evidence']['revert_only_effect_opcodes'])} | {row['source_name_status']} |")
    lines.append("")
    lines.append("Every listed body is effect-free in its dispatched region: no storage read, storage "
                 "write, log, external call or success exit. The payload is reconstructed here from the "
                 "`PUSH4`/`SHL` pair at the named program counter. These rows are unchanged by this "
                 "artifact; they are listed so the gap inventory can keep them apart from the undecided "
                 "behavior rows.")
    lines.append("")
    lines.append("## Local exact-runtime replay")
    lines.append("")
    replay = ledger["local_replay"]
    lines.append(f"`artifacts/selector_gap_other/{REPLAY_SOURCE.name}` runs {len(replay['passed_tests'])} "
                 "assertion-bearing tests through the exact pinned runtimes in a port-free in-process "
                 "Forge EVM (`forge test` reported "
                 f"`{replay['forge_result']}`). Tests: "
                 + ", ".join(f"`{name}`" for name in replay["test_names"]) + ".")
    lines.append("")
    lines.append("The suite covers: minter-gated PAPER burn with supply and balance effects; owner-gated "
                 "`setMinter`; owner-gated Tokenomics `setMintParams` including both validation errors; "
                 "the SessionKeyManager caller setter with an explicit check that the cached domain word "
                 "in slot 1 does not move; the factory deployer setter and the admin-only owner-zero "
                 "initializer on a synthetic fresh proxy; the timelock self-gated `updateMinDelay` and "
                 "`transferOwnership`; single and batch schedule, execute and cancel with child-call "
                 "ordering, done flags and events; and a shared decode-guard test that rejects a "
                 "selector-only call and a calldata prefix one head word short with empty revert data.")
    lines.append("")
    lines.append("## Live drift after the pin")
    lines.append("")
    if ledger["live_latest_state"]:
        live = ledger["live_latest_state"]
        lines.append(f"Latest-state reads were captured at block {live['latest_block']:,} on "
                     f"{live['captured_at']}. They are current state only: the RPC ignores historical "
                     "block numbers, so they are not the pinned state.")
        lines.append("")
        lines.append("| Proxy | Pinned implementation | Live implementation | Live runtime bytes | Changed |")
        lines.append("|---|---|---|---:|---|")
        for label, entry in sorted(live["pinned_vs_live"].items()):
            lines.append(f"| `{label}` | `{entry['pinned_implementation']}` | `{entry['live_implementation']}` "
                         f"| {entry['live_runtime_bytes']} | {'yes' if entry['changed'] else 'no'} |")
        lines.append("")
        lines.append("The SessionKeyManager and Tokenomics rows above therefore describe the pinned "
                     "runtime only; their live behavior may differ. The factory, batch executor, staking, "
                     "PAPER token, ProxyAdmin and timelock rows still describe the live code.")
    else:
        lines.append("No live capture is stored. Run `python3 scripts/atlas_selector_gap_other.py --capture` to "
                     "refresh the EIP-1967 implementation slots and the live runtime hashes.")
    lines.append("")
    lines.append("## Reproduce")
    lines.append("")
    lines.append("`python3 scripts/atlas_selector_gap_other.py` re-runs every bytecode and hash check offline and "
                 "rebuilds this page. `--replay` regenerates the exact-runtime replay with Foundry, and "
                 "`--capture` refreshes the live `latest` reads, storing each raw JSON-RPC response under "
                 "`artifacts/selector_gap_other/live/<timestamp>/`. No RPC credential is needed for the "
                 "default run.")
    lines.append("")
    lines.append("## Limits")
    lines.append("")
    for limit in ledger["limits"]:
        lines.append(f"- {limit}")
    lines.append("")
    OUTPUT_MD.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()