# Sampled Exchange close settlement paths

The [close ledger](exchange_close_paths.json) reconciles all nine saved successful `PositionClosed` events across seven transactions with their position margin, user balance mapping, queue total, `PositionsClosed` summary event, and two fee accumulators. It checks transaction-level net changes, so it does not establish internal write order.

| Observed case | Count | User balance change | Other checked change |
|---|---:|---|---|
| Positive PnL credited | 3 | `margin + adjustedPnl - eventFee` | `eventFee` equals the two per-call fee splits; accumulator changes match their transaction sums |
| Negative PnL credited | 2 | `margin + adjustedPnl` | The nonzero fee in one event reduces the Tokenomics LP credit and PAPER mint basis, not the trader credit |
| Margin only | 1 | `margin` | No sampled fee or queue change |
| Net profit queued | 3 | `margin` | `totalQueued` rises by `adjustedPnl - eventFee`; fee accumulators do not change in these transactions |

For every sampled close, the first two `PositionsClosed` data words equal the user's balance change and resulting balance. Its final two words equal that call's staker and developer fee amounts, and their sums match the transaction's packed fee-accumulator changes. The [position layout](exchange_position_layout.md) also shows the active bit cleared for these same nine positions.

The event field names come from a public ABI fixture with some known mistakes. The arithmetic relationships above are checked against raw event data and storage diffs. An [archive-backed fee replay](exchange_close_fee_effects.md) isolates slot 24 as the positive-PnL fee rate in one queued and one direct-payout close, including integer rounding and the direct fee split. A [mixed-close replay](exchange_negative_close_fee.md) isolates slot 23 as the loss fee rate and traces its allocation between Exchange fee accrual and Tokenomics LP credit. Payout caps and why the queue branch was chosen remain open. Three first-node enqueues and their later harvest now have a [separate storage layout](exchange_queue_layout.md).
