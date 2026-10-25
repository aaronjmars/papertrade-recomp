# Newest Exchange withdrawal delivery sample at block 48,902,346

The newest Exchange emitted 28,643 `CoreWithdrawal` events through the pin. This check pairs 32 selected signed withdrawals with saved EVM receipts and public HyperCore transfers. Together with [four earlier checks](../../AUDIT.md#completed-audit-check-sampled-withdrawal-delivery-and-fee), it covers 35 distinct events because one signed transaction appears in both samples. It is a delivery sample, not a full withdrawal settlement census.

## Selection and checks

The [complete event census](exchange_withdrawal_event_census.json) has 22,652 events whose internal debit equals the Core amount and 5,991 events with one extra internal USD. The [sample selector](../../scripts/atlas_exchange_withdrawal_census.py) takes 16 evenly spaced events from each class, including the first and last event in each class. The saved trace census checks these 32 calls against the `coreUserExists` response and CoreWriter payload. These are deterministic strata, not a random or representative rate estimate.

For each selected transaction, the [offline verifier](../../scripts/audit_withdrawal_settlement_stratified.py) checks the pinned block and event against the saved public EVM block header and successful receipt. It requires exactly one receipt log with the same transaction hash, block hash, emitter, topics, and data as the census event. It then requires exactly one matching USDC `spotTransfer` in each of the Exchange sender and indexed recipient Core ledgers, and requires those two transfer records and their hashes to be identical. The transfer must occur within ten seconds after the EVM block timestamp. The event amount must match both Core API amount fields after bounded decimal normalization; the Core fee must equal the extra internal debit, and the native token fee must be zero.

The [compressed raw capture](../../artifacts/audit_withdrawal_settlement_stratified/public_ledger.json.gz) contains all 32 event records, block headers, receipts, both Core ledger responses, query windows, and source endpoints. Offline verification needs no RPC key.

| Saved status class | Selected events | Core USDC delivered | Fee per transfer | Total Core fees |
|---|---:|---:|---:|---:|
| New Core account, status 0 | 16 | 53,606.928071 USDC | 1 USDC | 16 USDC |
| Existing Core account, status 1 | 16 | 1,624,033.126698 USDC | 0 | 0 |
| Total | 32 | 1,677,640.054769 USDC | | 16 USDC |

All 32 transfers appear in both public ledgers. The latest matching transfer is 488 ms after its EVM block timestamp. Across the earlier four and this sample, 35 unique newest-Exchange withdrawals have public Core delivery matches: two direct and 33 signed.

## Provider and coverage limits

The saved `eth_getLogs` event indices disagree with the public receipt's log index in 11 samples and transaction index in 12 samples, although the transaction and block hashes and exact event payload agree. The verifier records these discrepancies and matches the event by its exact receipt payload, requiring a unique match. The source of the index differences is not established.

For one transfer, the public Core API formats both `amount` and `usdcValue` 0.01 raw unit below the integer amount encoded in the EVM event. One raw unit is 0.00000001 USDC. The verifier rounds each public amount to the nearest raw unit only when the residual is at most 0.1 raw unit, and reports the observed maximum residual. This is an API precision limit, not evidence of a value shortfall.

Public Core API ledgers are not cryptographic historical state proofs. The check does not verify recipient balances after the transfer, full internal storage debits for all 32 transactions, the final fee recipient, or delivery for the other 28,608 newest-Exchange withdrawal events. The status and fee split applies to the selected cases only.

Run `python3 scripts/audit_withdrawal_settlement_stratified.py` from the repository root to verify the saved capture. `python3 scripts/atlas_verify.py` includes the same check. To refresh only this public evidence, run `python3 scripts/audit_withdrawal_settlement_stratified.py --capture` with network access; it does not require an API key.
