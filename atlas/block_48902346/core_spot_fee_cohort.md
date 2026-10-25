# Core spot-send fee cohort at block 48,902,346

The [offline verifier](../../scripts/atlas_core_spot_fee_cohort.py) compares saved public Core ledger responses from time zero through the pin for 38 older factory deposit proxies. It checks all 112 recorded proxy-to-Exchange USDC spot transfers, including the two recovered retries.

| First captured inbound transfer | Proxies | Fee on first outgoing spot transfer |
|---|---:|---:|
| Spot-wallet `send` | 22 | 0 USDC in all 22 |
| Incoming Core `spotTransfer` | 14 | 0 USDC in all 14 |
| `send` into the perp wallet, then a class transfer before outgoing spot | 2 | 1 USDC in both |

Across all 112 outgoing spot transfers, 110 have a zero fee and two have a 1 USDC fee. Those two are exactly the [historical recovered retry transactions](older_sweep_retries.md). One of their proxies later sent another 10 USDC to the same Exchange with a zero fee. The second fee-paying proxy also received an external spot top-up before its first successful outgoing transfer, so merely seeing an incoming spot credit does not explain the fee difference.

The 38 ledgers separately contain 12 `accountActivationGas` entries, none in either one-fee proxy ledger. Before the first one-fee send, the destination Exchange had already received 13 spot transfers from captured older proxies. Hyperliquid's [activation-fee documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/activation-gas-fee) specifies the "first transaction which has the new account as destination address." That documented destination condition does not explain a new-account fee for an Exchange that had already received these earlier transfers. It does not settle whether a different sender or token-ledger initialization charge caused the observed fee.

This is a correlation within a bounded public `userNonFundingLedgerUpdates` capture, not a protocol fee rule or a cryptographic Core state proof. The API can omit funding categories, so the table describes the first **captured** inbound transfer. The two [newest stalled proxies](../../FINDINGS.md) have no successful proxy-to-Exchange send through the pin; this cohort cannot prove the fee they would pay on a future send or that a 1 USDC reserve would suffice.

Run `python3 scripts/atlas_core_spot_fee_cohort.py` to recompute and verify the [machine summary](core_spot_fee_cohort.json) from saved ledgers. No network or key is needed.
