# Exchange signed-close fee at archived HyperEVM blocks

The [close-fee behavior ledger](exchange_close_fee_effects_behavior.json) uses two archived signed closes. One queues positive profit at block 48,173,881; the other credits positive profit directly at block 48,902,090. Each original call is replayed on an archive-backed Anvil fork at the prior block with its historical HyperCore bid and ask. Both baselines match the corresponding historical receipt logs and Exchange storage diffs exactly.

Sixteen read-only replays change fee slots 23, 24, and 25 one at a time. In both tested close branches, slot 24 controls the `PositionClosed` fee:

```text
fee = floor(adjustedPositivePnl * slot24 / 10^18)

queued-profit branch:
    queueAmount = adjustedPositivePnl - fee
    totalQueued += queueAmount

direct-payout branch:
    userPayout = margin + adjustedPositivePnl - fee
    stakerFee = floor(fee / 2)
    devFee = fee - stakerFee
    slot26.low128 += stakerFee
    slot26.high128 += devFee
```

Zeroing slot 24 eliminates the fee; doubling it doubles the fee in both branches. Rates of one and three units show floor rounding: the queued-profit close charges 7 and 23 internal units, while the direct-payout close charges 6 and 20. Zeroing or doubling slot 23, or zeroing slot 25, leaves each tested close's Exchange logs and storage diff identical to baseline. The queued branch emits no staker or developer fee credit in the sampled transaction; the withheld amount stays outside the user's queued profit.

The [queued-profit traces](../../artifacts/exchange_close_fee_effects/local_probes.json) and [direct-payout traces](../../artifacts/exchange_close_fee_effects/direct_local_probes.json) preserve the original signed calls, historical BBO values, event logs, and storage diffs. Run `atlas_exchange_close_fee_effects.py` to verify both offline. To recapture, use separate archive-backed Anvil forks at blocks 48,173,880 and 48,902,089 and pass them with `--local-rpc-url` and `--local-direct-rpc-url`, respectively.

These are two positive-PnL paths under controlled fee changes. The [mixed gain and loss replay](exchange_negative_close_fee.md) separately identifies slot 23 as the negative-PnL fee rate. Other settlement branches remain unresolved. No changed-rate case was executed on the live chain.
