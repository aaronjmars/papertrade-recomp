# Exchange position storage at HyperEVM block 48,902,346

The Exchange `positions(uint256)` getter reads two consecutive words from mapping base slot 10. The [position ledger](exchange_position_layout.json) checks 25 successful `PositionOpened` events across ten saved transactions against the post-transaction storage diff. All 25 match the stored user, instrument, side, entry price, margin, and leverage. The stored timestamp equals the transaction block timestamp in all ten blocks.

```text
base = keccak256(abi.encode(positionId, uint256(10)))

word at base:
  bits   0..159  user address
  bits 160..191  instrument ID
  bits 192..255  entry price

word at base + 1:
  bits   0..127  margin
  bits 128..159  leverage
  bits 160..223  block timestamp
  bits 224..255  packed flags
```

The lowest flag bit matches the event side in all 25 opens. Bit 240 of the whole second word is set in those opens. It is cleared in all nine sampled signed closes and all six sampled keeper liquidations. Every other bit of that word remains unchanged in those 15 deactivations. This supports interpreting bit 240 as an active flag. The event's third boolean is zero in these samples. The [getter override checks](exchange_mapping_getters.md) show that the eighth `positions(uint256)` output is true when any bit in word1 bits 232 through 239 is set. The exact event-to-storage relationship for nonzero values is still unobserved.

The same ten open transactions also agree with the balance mapping at base slot 9. For each of 23 distinct transaction-user pairs, the user's balance falls by the sum of their opened margins. In each transaction, `totalBalances()` falls by the sum of all opened margins and `totalLockedMargin()` rises by exactly that sum. This verifies the observed open-path transfer from available balance into locked margin, including batches where one user opens more than one position.

In the two saved keeper liquidation batches, all six liquidated users have no change to their available balance. For each position, the event's two fee fields each equal 1% of its stored margin. Across each batch, `totalLockedMargin()` falls by the sum of liquidated margins, `totalBalances()` is unchanged, and both fee accumulators rise by the sums of their corresponding event fees. Eligibility checks and the use of the remaining released margin still need reconstruction.

The ledger is a sampled successful-path reconstruction. The paired [Exchange event path ledger](exchange_event_paths.json) now ties all 25 sampled entry prices to the Oracle midpoint and nested HyperCore bid and ask. This does not establish failed-open behavior, alternate pricing modes, margin checks, payout math, liquidation eligibility, or behavior of other flag values. The [accounting storage ledger](exchange_storage_behavior.json) separately records net changes to balances, locked margin, fees, and queued funds in saved transactions.
