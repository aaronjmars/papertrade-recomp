# Exchange accounting storage at HyperEVM block 48,902,346

The live Exchange proxy is `0x6cd5661646289fb6e65ea5c032310fded797d0a2`. [Raw pinned words](exchange_storage_words.json) and [decoded evidence](exchange_storage_behavior.json) agree with nine saved getter opcode traces. The snapshot uses the pinned block hash in the atlas manifest. The [direct getter map](exchange_direct_getters.md) independently checks 16 slot getters and three `balances(address)` samples against archive reads.

| Slot | Observed fields |
|---|---|
| 11 | `nextPositionId()` |
| 14 | `treasury()`, a numeric accounting amount |
| 16 | `queueHead()` |
| 18 | `totalQueued()` |
| 22 | Low 128 bits: `totalBalances()`; high 128 bits: `totalLockedMargin()` |
| 27 | `sideBucket()`, established by a pinned getter trace and two historical writes in the [side-bucket ledger](exchange_side_bucket.md) |
| 26 | Low 128 bits: `stakerFeeAccumulator()`; high 128 bits: `devFeeAccumulator()` |

At the pin, `totalQueued()` is zero and both availability getters return `5000968649731559005181671`. [Eleven pinned storage-override states](exchange_availability_behavior.json) distinguish their formulas:

```text
reserved = totalBalances + totalLockedMargin
         + stakerFeeAccumulator + devFeeAccumulator
queueHarvestAvailable = max(treasury - reserved, 0)
lpBankrollAvailable = 0 if totalQueued > 0 else queueHarvestAvailable
```

A one-unit queued claim makes LP availability zero while queue-harvest availability stays positive. Overrides separately increased each packed reserve field by 100 units and tested the exact zero and one-unit treasury boundaries. These are read-only simulations. The earlier single-state identity subtracted `totalQueued` as an amount; that was incorrect because the pinned queue was zero.

The third-party Exchange ABI fixture labels `treasury()` as returning an `address`. Its pinned value changes by `4999000000000000000000` in a saved `Swept` transaction, and the same amount enters `totalBalances()`. It is an accounting amount in this runtime. The earlier state-link artifact mistakenly interpreted the value as an address because it fits in 160 bits; that link has been removed. The exact source-language integer width remains unproven.

Saved transaction state diffs show these net changes:

| Path | Observed changes |
|---|---|
| Three-position open | `nextPositionId +3`, `totalBalances -650000000000000000000`, `totalLockedMargin +650000000000000000000` |
| Sweep | `treasury +4999000000000000000000`, `totalBalances +4999000000000000000000` |
| One-position close | `totalLockedMargin -2500000000000000000000`, `totalBalances +2506729337817564909731`, two fee accumulators each rise by about `68666712424131731` |
| Three-position liquidation | `totalLockedMargin -5110300000000000000000`, both fee accumulators `+51103000000000000000`; `totalBalances` unchanged |
| [Dev fee claim](exchange_dev_fee_claim.md) | `devFeeAccumulator -114890275671617164291236`, `totalBalances +114890275671617164291236`, recipient balance credited by the same amount |

The [machine-readable ledger](exchange_storage_behavior.json) contains 14 transactions with changes to these fields, their root selectors, and Exchange event counts. These are transaction-level net deltas. Some batches contain several inner calls, so they do not prove the calculation or write order of any individual function. The `positions(uint256)` mapping has a separate [two-word layout and deactivation check](exchange_position_layout.md). The `balances(address)` mapping matches margin transfers for 23 transaction-user pairs on the sampled open path. The sampled [close settlement](exchange_close_paths.md) and [liquidation](exchange_position_layout.md) paths now have field-level checks; eligibility rules, queue entry layout, withdrawals, and unsampled payout branches still need replay. Three diff-mode sides are omitted and decoded as zero in the ledger.
