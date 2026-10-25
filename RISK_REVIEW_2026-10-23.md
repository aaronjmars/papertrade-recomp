# Papertrade risk review, 23 October 2026

This review covers four fund-safety questions across the current contract set and the two older sets. It uses saved exact-runtime replays, historical receipts and public read-only state. No transaction or recovery action was sent. The newest live reads are at HyperEVM blocks 49,318,444 to 49,318,549. Public HyperCore API reads followed the EVM reads and are not an atomic state proof.

**Verdict:** The checked paths establish no external-user drain or large realized loss in the current pool. Two deposits totaling **62.150916 USDC** are still inaccessible as Exchange credit. The earlier claimed repeatable debt-funded payout mint (`SQ-L2-02`) was an incomplete-fixture false positive. This is a scoped result, not a security certification.

| Area | Established result | Remaining risk |
|---|---|---|
| Deposit and withdrawal settlement | Two deposit proxies still hold 50.050916 and 12.1 USDC on HyperCore, with pending Exchange requests and zero user credit. All 35 individually checked withdrawals reached the intended users. | Recovery of the two deposits is unproved. The other 28,608 withdrawal events at the original pin have not been individually paired with Core delivery. No failed withdrawal or loss was established. |
| Liquidation and payout accounting | A coherent queue-pointer replay shows one debt open consumes queued credit, its same-quote close restores the claim, harvest pays the existing queue once, and a second debt open fails. The prior 3,237.31 USDC gain and 20,000 USDC claims excess were fixture artifacts. | Winning payouts can exceed immediately available LP cash and enter the queue. Current-set behavior for a mixed liquidation batch with an invalid price has not been checked. No additional mint was established. |
| Session keys and batches | Tested signatures, recipient binding and nonce rollback held. In a sampled 256-block window, 28 of 1,272 inner batch calls failed, all signed opens. No failed close was seen. | An outer batch can succeed while an inner action fails. Whether the product checks each inner result and final position state remains unverified. |
| Upgrades and older sets | At block 49,318,444 the current Exchange and SessionKeyManager implementations were paired correctly. A third SessionKeyManager implementation was staged but not installed. Both older governance multisigs still had the same two signers, with one confirmation required by their deployed code. | A mismatched upgrade can block signed closes in simulation. Older Exchange internal balances total 84,448,601.522052 and 640,390,624.345224 units, while their Core spot accounts held 0.156176 and 0.003269 USDC near block 49,318,487. Whether those balances are real redeemable claims or synthetic pre-launch accounting is unresolved. Do not count the difference as a proven loss. |

## Corrections to earlier audit claims

- `SQ-L2-02` is `disproved`, severity `none`. The saved transaction read-set omitted queue head and next-id slots 16 and 17, which defaulted to zero in the original replay. The corrected replay seeds the pinned values and does not reproduce the claimed repeatable mint. The temporary positive 1,000 USDC book residual while debt margin is open returns to zero on close; it is not an extra withdrawal claim.
- A 1 USDC HyperCore sender fee alone does not establish deposit overcredit. Two observed older reduced retries delivered and credited the same amount while paying that fee separately. A balance decrease without equal delivery remains a conditional, unobserved concern.
- The two stuck deposits have no observed recovery, but irreversibility has not been proved. The current implementation has a reduced-send retry path; Core acceptance for these two proxies has not been observed.
- The older books are accounting units until deposit origin and redemption rights are established. Their face totals are not a measured current-pool loss.

## Evidence and limits

- [Corrected debt lifecycle](atlas/block_48902346/live2_sequences.md) and [queue layout](atlas/block_48902346/exchange_queue_layout.md).
- [Deposit finding](FINDINGS.md), [spot settlement samples](atlas/block_48902346/spot_settlement_stratified.md), and [withdrawal settlement samples](atlas/block_48902346/withdrawal_settlement_stratified.md). Hyperliquid documents [CoreWriter enqueue and later Core execution](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore).
- [Batch behavior](atlas/block_48902346/batch_executor_pseudocode.md), [signed-intent checks](atlas/block_48902346/live2_intents.md), and [upgrade coupling](atlas/block_48902346/live2_authority.md).
- [Older account census](atlas/block_48902346/older_accounts.md), [older withdrawals](atlas/block_48902346/older_withdrawals.md), and [older governance](atlas/block_48902346/older_governance.md).

The highest-value unresolved checks are a real delivery and credit outcome for the two pending deposits, broader withdrawal delivery reconciliation, current-set mixed liquidation behavior, compatibility of the staged SessionKeyManager, and the origin of older internal balances. Each requires its own evidence before changing the verdict.
