# BatchExecutor behavior at HyperEVM block 48,902,346

The live proxy is `0x233ff29b239abc1d7748605da9b205c3e008626e`; its implementation is `0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262`. This is a behavior reconstruction, not original Solidity. [`batch_executor_behavior.json`](batch_executor_behavior.json) contains the transaction, trace, log, and topic checks.

## `execute((address,bytes,bool,bytes32,bytes32)[])`, selector `0x251fb27d`

The selector is the exact Keccak-256 prefix of the signature above. The captured bytecode dispatches it. Thirty-seven saved batches across six artifact folders decode with this ABI, and all 161 decoded inner calls match the actual call traces in target, calldata, order, success, and return bytes. These include a matching saved trace for every one of the 28 failed inner calls in the recent 256-block log window. The last two tuple fields are a `bool` and `bytes32` by the hash-matched ABI. Every saved batch used `true` and zero respectively.

```text
execute(calls):
    require authorizedRelayers[msg.sender]     // mapping base slot 4
    batchId = keccak256(msg.data)               // includes the 4-byte selector
    successes = 0
    failures = 0

    for index, call in calls in order:
        if target and selector do not pass the allowlist:
            emit CallRejected(batchId, index, call.intentId,
                              bytes("BatchExecutor: selector not allowed"))
            failures += 1
            continue

        (ok, returned) = call.target.call(call.data)
        if !ok and !call.continueOnFailure:
            revert BatchCallFailed(index, returned)
        emit CallExecuted(batchId, index, call.intentId, ok, returned)
        if ok: successes += 1
        else:  failures += 1

    emit BatchExecuted(batchId, len(calls), successes, failures, field4)
```

The pseudocode covers the observed true-flag path and pinned read-only false-flag and allowlist probes. The [exact-runtime field comparison](../../artifacts/batch_executor_field4_local/replay.json) tests five fourth-field values, including zero, one, a matching return hash, a calldata hash, and `uint128.max`, across successful, continued-failure, and rejected calls. All 15 cases preserve the inner target, result bytes, result and summary counts, and fourth summary value of zero; the calldata-derived batch ID changes. A sixteenth case confirms the noncontinuing failure error. The fourth tuple field's purpose and `BatchExecuted`'s fourth numeric field remain unknown outside those paths. The latter was zero in all 466 recent batch summaries. The allowlist is present in the bytecode. The [exact-runtime candidate scan](../../artifacts/batch_allowlist_local/replay.json) tests all 262 distinct captured catalog selectors, the implementation's `PUSH4` operands, and an invalid control across Exchange, SessionKeyManager, Staking, and an unrelated target. Of 1,048 target-selector pairs, only these eight execute; all eight match saved historical call pairs:

| Target | Accepted selectors |
|---|---|
| Exchange | `0x2792e706` close by signature; `0x8d09f23f` withdraw to Core by signature; `0xec6783f0` open by signature |
| SessionKeyManager | `0x5f76a1d6` register session key by signature |
| Staking | `0x83115825` stake by signature; `0x9c96d4a1` claim by signature; `0xf0355460` distribute by signature; `0xfa2871b5` unstake by signature |
| Unrelated target | None of the 262 candidates |

Each rejected pair emits `CallRejected` and a failure summary without calling the mock target. This scan is exhaustive over its recorded candidate set, not every possible 4-byte selector or target address.

The event signatures hash exactly to the observed topics:

| Event | Evidence |
|---|---|
| `CallExecuted(bytes32,uint256,bytes32,bool,bytes)` | 1,272 recent logs, including 28 failed calls. Topics are batch ID, index, and intent ID; payload is success plus exact return or revert bytes. All 161 traced inner calls match their logs; the 28 recent failed-call logs each match a saved trace by transaction and call index. |
| `BatchExecuted(bytes32,uint256,uint256,uint256,uint256)` | 466 recent logs. The first three numeric fields match total, success, and failure counts in every batch. The fourth was always zero. |
| `CallRejected(bytes32,uint256,bytes32,bytes)` | Exact topic hash and payload in pinned read-only invalid-target and invalid-selector probes. No occurrence in the recent log window. |

Pinned read-only probes identify `NotAuthorizedRelayer()` (`0x17fb2066`) for an arbitrary caller and `BatchCallFailed(uint256,bytes)` (`0x651ab1b3`) when the first tuple's bool is changed to false and its inner call reverts. The bool-true variant emits a failed `CallExecuted` and completes. An invalid bool value of two reverts; no semantic claim relies on it.

## Other dispatcher entries

Pinned getter opcode traces support these direct slots: Exchange address at slot 0, SessionKeyManager at slot 1, PAPER staking at slot 2, owner at slot 3, authorized relayers at mapping base slot 4, and an initialization flag in slot 5. `paperStaking()` (`0xd5c539ce`) is hash matched and returns the slot 2 address.

The live implementation has 12 selectors. Six owner, relayer, and getter names now have hash and behavioral support in the [control-path reconstruction](batch_control_pseudocode.md), including two historical admin transactions and ten local tests. The five-address and two-address initializer paths are behavior-mapped under synthetic fresh states, but their source names remain unknown. Selector `0x6090cf16` reads slot 5, while the three-address selector `0xc0c53b8b` reverts under both archived and fresh local states with raw `0xb7b2509c`. The [pinned bytecode proof](legacy_initializer_stubs.md) rules out a success branch for canonical, zero-value calls; its source name remains open. The fourth tuple field and one summary event field also remain open.
