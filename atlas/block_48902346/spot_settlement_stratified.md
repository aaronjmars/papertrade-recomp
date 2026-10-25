# Stratified spot deposit settlement and accounting

At HyperEVM block 48,902,346, the full sweep event census contains 53,125 credited spot-only requests. The earlier recent-history check paired 13 of them with public HyperCore transfers. This check adds 19 distinct cases selected from the complete event history: eight time octiles, the smallest and largest amounts, two other amount ranks, four long request-to-credit delays, and three additional fractional amounts. Duplicate picks were removed. The selected amounts range from 10 USDC to 4,000,000 USDC, and finalization occurs one to 12 EVM blocks after request. This is a deterministic varied sample, not a random sample or census.

[`audit_sweep_settlement_stratified.py`](../../scripts/audit_sweep_settlement_stratified.py) regenerates the selection from the saved event census and verifies the [public EVM, Core info, and Core explorer capture](../../artifacts/audit_sweep_settlement_stratified/public_ledger.json.gz). For each case it checks:

1. The exact `SweepRequested` and `Swept` payloads in successful EVM receipts, pinned to public block headers.
2. A CoreWriter action 6 enqueue log from the deposit proxy for the exact USDC amount and Exchange destination.
3. One successful HyperCore `SystemSpotSendAction` execution with the same sender, destination, token, and amount.
4. The same exact USDC transfer in the deposit proxy and Exchange public Core ledgers between request and finalization.
5. Exchange credit equal to the sent eight-decimal amount scaled to the contract's 18-decimal accounting unit.

All 19 match, totaling **4,043,139.668559 USDC**. All sampled Core transfer fees are zero. The Core transfers occur 354 to 480 ms after the request block's whole-second timestamp. Twelve sampled transactions have a log-index difference between the saved census provider and public receipt provider; exact contract, transaction, topics, data, and block hash still match. Combined with the 13 earlier distinct pairs, **32 of 53,125 credited spot-only sweeps** have individual public Core delivery links, totaling **4,057,995.980810 USDC**.

## Accounting transition

[`audit_sweep_accounting_stratified.py`](../../scripts/audit_sweep_accounting_stratified.py) verifies [archive prestate diffs](../../artifacts/audit_sweep_settlement_stratified/accounting_diffs.json.gz) for all 19 request and finalization transactions. Every request writes the user's pending sweep word without changing that user's balance, treasury, or `totalBalances`. Every finalization clears that pending word and raises the user's balance by its exact `Swept` amount. Treasury and the low 128 bits of `totalBalances` rise by the sum of all `Swept` events in each finalization transaction. The high 128-bit locked-margin field does not change. One selected finalization contains two `Swept` events, so its aggregate fields rise by both credits while the selected user's balance rises by only their own credit. These are transaction-level storage checks; they do not establish the complete outstanding liability of the Exchange.

## Partial and failed delivery branches

[`audit_sweep_partial_failure_replay.py`](../../scripts/audit_sweep_partial_failure_replay.py) reran the deployed Exchange bytecode in a fresh archive-backed Anvil fork at the pin, with controlled HyperCore balance reads. With a pending snapshot of 100 USDC, zero residual, one raw USDC unit residual, and a balance just one raw unit below the snapshot each emitted a 100 USDC `Swept` event and added the full snapshot to the user's balance, treasury, and `totalBalances`. With an unchanged 100 USDC Core balance, the finalization credited nothing and queued another request. A smaller unchanged balance below the request minimum reverted without an Exchange storage write. The [saved local traces](../../artifacts/audit_sweep_settlement_stratified/partial_failure_replay.json.gz) are checked offline by the main verifier. Independently, the [PT-01 Core explorer evidence](../../FINDINGS.md) proves two actual rejected Core sends with no matched transfer or credit through the recorded status checks.

The one-unit-decrease replay shows that a decline of only 0.00000001 USDC is enough to credit the 100 USDC snapshot under mocked reads. If that decline were the only delivered amount, the hypothetical credit gap would be 99.99999999 USDC. No observed Core transaction in this sample made a partial transfer, and the replay does not establish that HyperCore can execute one. The failed-send replay uses controlled Core reads; the two PT-01 rejections provide the actual failed-execution evidence but do not prove every recovery branch.

## Evidence limits and next accounting work

| Link | Evidence status |
|---|---|
| EVM request, CoreWriter enqueue, Core execution, transfer in both Core ledgers, EVM credit event, and transaction-level storage credit for each of the 19 new cases | Verified against the saved public API records and archive state diffs |
| Delivery for the other 53,093 credited spot-only requests | Not individually paired |
| A real partial Core spot send that leaves a smaller proxy balance and causes a full Exchange credit | Not observed; the five local branches control the Core balance read |
| A successful recovery of the two PT-01 rejected sends | Not observed through the recorded post-pin status checks |
| Cryptographic Core state proof or a same-time whole-Exchange Core asset balance | Not captured |

The Core execution and ledger links are Hyperliquid public API records, not cryptographic state proofs. The EVM receipt shows the action was queued, while the separate Core explorer and two Core ledgers support execution and delivery. The sample does not cover the remaining 53,093 spot-only credits individually, every failure mode, or the exact Core transfer-gas predicate. The live PT-01 proxies' 62.150916 USDC and pending state still need an actual governed or Core-side recovery check.

The 19 storage transitions reconcile deposit crediting. The [newest pinned account census](newest_accounting.md) now matches ordinary balances, opening margins, and observed queue claims to their Exchange totals. Reward, fee and debt redemption claims still need classification, followed by a same-time comparison with Core assets and explicit withdrawal semantics. The older suites have separate ordinary-balance and margin reconciliations, but their other claims and USDC backing remain open.
