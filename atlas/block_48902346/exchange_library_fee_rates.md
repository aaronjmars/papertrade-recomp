# Linked-library close fee inputs

The [rate behavior ledger](exchange_library_fee_rates_behavior.json) verifies 36 saved local fork calls to the live Exchange linked library's close-settlement selector `0xef1a27a9`. Its inputs and six outputs are extracted from three independently verified signed-close replay artifacts: a mixed gain/loss batch, a queued profitable close, and a directly credited profitable close. The unchanged replay baselines match their historical receipts and Exchange state changes.

The historical settlement calls pass the same 2% value in both rate fields, so those alone cannot distinguish the fields. The controlled replays vary Exchange slots 23 and 24 independently, and the nested library calldata changes in lockstep:

```text
input 5 = Exchange slot 24 = positive-PnL rate
input 6 = Exchange slot 23 = negative-PnL rate
fee = floor(abs(adjustedPnl) * selectedRate / 10^18)
```

All 36 six-word outputs match the generalized settlement model. Zeroing input 6 changes only the losing close in the mixed batch; zeroing input 5 changes only its winning close. Rates of one and three units confirm floor rounding on both signs. The positive queue branch with input 7 equal to zero withholds the fee from queued profit without emitting fee split outputs. The directly settled positive and negative branches split the fee with the first share rounded down and the second receiving the remainder. Changing Exchange slot 25 leaves this library call's arguments and outputs unchanged in the tested mixed batch.

The [mixed raw traces](../../artifacts/exchange_negative_close/local_probes.json), [queued-profit traces](../../artifacts/exchange_close_fee_effects/local_probes.json), and [direct-profit traces](../../artifacts/exchange_close_fee_effects/direct_local_probes.json) are the inputs. Run `python3 scripts/atlas_exchange_library_fee_rates.py` from the workbench root to rederive and verify the ledger offline.

The exact source name of `0xef1a27a9` remains unknown. The changed-rate set does not include a queued loss. The library's other seven selectors lack historical calls; four now have narrow [local adapter probes](exchange_library_adapters.md), while deeper behavior remains open.
