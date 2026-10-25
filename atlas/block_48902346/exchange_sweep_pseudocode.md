# Exchange deposit sweep paths

This reconstruction is pinned to HyperEVM block 48,902,346. The machine-readable ledger is [exchange_sweep_behavior.json](exchange_sweep_behavior.json). It checks 13 historical request/finalize pairs, 24 read-only archive-backed local fork cases with controlled HyperCore responses, and pinned archive probes. The pseudocode describes the tested spot and perp paths. It is not recovered Solidity source.

## Storage and units

- `balances[user]` uses mapping base slot 9. Its value, `treasury` at slot 14, and the low 128 bits of slot 22 (`totalBalances`) all increase by the same credited amount.
- `lastSweepBlock[proxy]` uses mapping base slot 32. Its getter takes a **proxy** address. Passing the user address returned zero in the pinned sample.
- `pendingSweep[user]` uses mapping base slot 33. The tested packed word stores `spotRaw` in bits 0:64, `perpRaw` in bits 64:128, and request block in bits 128:160.
- The [getter ledger](exchange_getters.md) hash-verifies `getPendingSweep(address)` and `pendingSweepWord(address)` against all 13 sampled request/finalization pairs. The tuple decodes the packed word and both getters return zero after finalization.
- The request minimum is exactly 1,000,000,000 raw spot-equivalent units in the controlled fork. The Exchange uses `spotRaw + 100 * perpRaw`: spot-only 999,999,999 fails and 1,000,000,000 succeeds; perp-only 9,999,999 fails and 10,000,000 succeeds.
- A successful finalization multiplies the stored spot-equivalent amount by `10^10` before adding it to Exchange accounting. Owner `reconcileSweepCredit(user, amount)` rejects an existing pending sweep. After a simulated direct storage clear, an exact-runtime replay credits `amount * 10^12` for `amount = 50,050,916`; other input boundaries remain untested.

## Tested behavior

```text
requestSweep(user):
    proxy = factory.proxyOf(user)
    require lastSweepBlock[proxy] != block.number
    read proxy HyperCore spot and perp balances
    require spotRaw + 100 * perpRaw >= 1,000,000,000
    pendingSweep[user] = (spotRaw, perpRaw, block.number)
    lastSweepBlock[proxy] = block.number
    proxy.sweepAllToExchange(0, spotRaw, perpRaw)
    emit SweepRequested(user, proxy, spotRaw, perpRaw, block.number)

finalizeSweep(user):
    require pendingSweep[user] exists
    require pending request block < block.number
    read current proxy HyperCore balances
    if tested current spot + 100 * current perp < stored spot + 100 * stored perp:
        clear pendingSweep[user]
        credit = (stored spotRaw + 100 * stored perpRaw) * 10^10
        treasury += credit
        totalBalances += credit
        balances[user] += credit
        emit Swept(user, credit)
    else, when current balance is still above the request minimum:
        emit PendingSweepCleared(user, proxy)
        replace the pending request with current balances and block number
        queue another proxy sweep
        emit SweepRequested(user, proxy, currentSpot, currentPerp, block.number)

sweep(user):
    with no pending request, follows requestSweep(user)
    with a pending request, follows finalizeSweep(user)

reconcileSweepCredit(user, amount):
    require owner
    require pendingSweep[user] == 0
    credit = amount * collateralScale
    for tested amount = 50,050,916 and pinned collateralScale = 10^12,
    credit treasury, totalBalances, and balances[user]; emit an unnamed event
```

The spot retry cases above used unchanged and increased balances of at least 10,000,000,000 raw units. At 100,000,000 raw units, a retry instead reverted with `SweepBelowMinimum()` and left the original pending word intact because the entire simulated call reverted. A local finalization with current spot at one raw unit below the snapshot credited the **full stored snapshot**. The same held for a perp-only snapshot with current perp one raw unit lower, and with the current balance converted to spot at one raw unit below the equivalent amount. An equal amount converted from perp to spot cleared and re-requested, confirming the comparison is in spot-equivalent units. These are observed bytecode paths under mocked HyperCore responses, not proof of an exploitable live credit.

The perp-only request at the minimum enqueued two CoreWriter actions: action 7 for perp-to-spot conversion and action 6 to send 1,000,000,000 raw spot units to Exchange. The historical pairs did not exercise this path.

The 13 historical pairs were all spot-only, with zero perp balance. Every request read the proxy's HyperCore balance, called its sweep function, and queued a CoreWriter spot send. In the next one or two blocks, every finalization read zero proxy balance, cleared the pending word, emitted `Swept`, and credited the exact `spotRaw * 10^10` amount in all three accounting fields. No request changed the accounting fields before finalization.

## Evidence limits

- Archive-backed local fork tests replace the HyperCore read precompiles and CoreWriter code, so they establish EVM control flow but do not reproduce HyperCore settlement. The [fork comparison](exchange_sweep_fork_comparison.json) confirms all 24 call outcomes and ordered logs match the earlier public-fork capture. Three `lastSweepBlock` write deltas differ because the earlier fork started with a zero value while the archive-backed fork starts from block 48,902,092. Treasury, packed balance, and sampled user-balance prestates also differ, so absolute public-fork storage values are not used as pinned evidence.
- The archive RPC cannot reproduce the historical HyperCore precompile reads for a pinned `debug_traceCall`. Its `NoCoreBalance()` result for an outside caller is not an access-control finding. The controlled fork did complete permissionless request and finalization paths.
- The [public HyperCore ledger capture](../../artifacts/audit_sweep_settlement/public_ledger.json) independently records a matching proxy-to-Exchange USDC transfer between request and finalization for each of these 13 sampled spot-only pairs. The [offline audit verifier](../../scripts/audit_sweep_settlement.py) ties their block headers to saved EVM receipts and matches exact eight-decimal amounts to 18-decimal credits. A [later varied 19-case check](spot_settlement_stratified.md) adds exact Core execution, both sender and Exchange ledgers, and 19 archived credit-state diffs, bringing individually paired spot-only credits to 32 of 53,125. These API records do not cover all sweeps or prove partial-transfer behavior. A fresh exact-runtime replay credits the full snapshot after a mocked one raw-unit balance decrease; this remains a constructed-state concern, not a demonstrated live exploit.
- The original 13 sampled request/finalization pairs were spot-only. A later [full event census and perp settlement check](../../FINDINGS.md) found 75 historical nonzero-perp requests: 73 credited after exact Core class conversion and send, and two cleared without a Core send or Exchange credit through the pin. Their last observed spot balances total 62.150916 USDC. The [public Core explorer check](../../scripts/audit_corewriter_rejections.py) identifies insufficient USDC transfer gas as the immediate rejection of both first and last spot sends. The [pinned recovery replay](exchange_sweep_recovery.md) shows that owner reconciliation rejects both saved pending words and `clearPendingSweep(address)` is absent from the deployed dispatcher. The [newest-suite public Core control cohort](pt01_newest_fee_controls.md) checks 27 successful proxy ledgers and the two stalled ledgers: all controls first show a 1 USDC inbound fee and all 84 successful outgoing sends have zero fee, while both stalled accounts first show zero and have no successful outgoing send. The exact rejected-send fee rule, an alternative recovery path, other retry combinations, callers, and overflow boundaries remain untested. The owner reconciliation event topic is known, but its exact signature preimage is unresolved.
