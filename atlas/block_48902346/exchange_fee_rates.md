# Exchange fee rates at HyperEVM block 48,902,346

The live Exchange hashes `setFeeRates(uint256,uint256,uint256)` to `0xe538b280`. Its simulated event topic hashes exactly to `FeeRatesUpdated(uint256,uint256,uint256)`. The [behavior ledger](exchange_fee_rates_behavior.json) verifies seven pinned read-only setter probes, three direct storage slots, three getters, and event payloads.

```text
setFeeRates(first, second, third):
    require caller == owner, NotOwner()
    require first <= 0.5 * 10^18, FeeTooHigh()
    require second <= 0.5 * 10^18, FeeTooHigh()
    require third <= 0.5 * 10^18, FeeTooHigh()
    slot23 = first
    slot24 = second
    slot25 = third
    emit FeeRatesUpdated(first, second, third)
```

All three pinned slots and their getters return `2 * 10^16`, or 2% on an `10^18` scale. The getter for slot 25 hashes exactly to `liquidationFeeRate()` (`0x5fb3b1b5`). The slot-23 getter name remains unknown. The Guardian report names the slot-24 getter `winFeeRate()` (`0x48ee5e08`), an exact selector-hash match; its source snapshot has not been matched to the live bytecode. The three successful simulations use distinct rates, zero rates, and the inclusive `0.5 * 10^18` upper bound. Setting any one rate to one unit above that bound reverts with `FeeTooHigh()` (`0xcd4e6167`). An unrelated caller receives `NotOwner()`.

The six saved historical liquidation events each contain two fees of 1% of margin. Their sum equals margin times the pinned 2% rate. The [fee-effect replay](exchange_fee_effects.md) isolates slot 25 on an archive-backed fork: zeroing it zeros both fees, doubling it doubles both, and zeroing slots 23 or 24 leaves the tested liquidation unchanged. An odd total fee confirms the integer split. The [raw setter traces](../../artifacts/exchange_fee_rates/pinned_probes.json) contain the setter storage diffs, event data, and getter overrides. Run `atlas_exchange_fee_rates.py` to verify them offline, or recapture with `--capture` and `PAPERTRADE_ARCHIVE_RPC`. A separate [signed-close fee replay](exchange_close_fee_effects.md) shows that slot 24 charges a percentage of adjusted positive PnL in both queued-profit and direct-payout closes. The [mixed-close replay](exchange_negative_close_fee.md) shows that slot 23 charges a percentage of adjusted negative PnL, reducing the LP credit and PAPER mint basis. No saved historical transaction called the setter. A [pinned full-history event query](exchange_control_event_history_behavior.json) returned no `FeeRatesUpdated` logs; attempted or unlogged calls are not excluded.
