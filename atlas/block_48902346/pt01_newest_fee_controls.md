# PT-01 newest-suite Core fee controls

The [offline verifier](../../scripts/atlas_pt01_newest_fee_controls.py) joins the 73 credited nonzero-perp sweep requests, their saved request-window Core transfers, 27 distinct successful deposit proxies' public Core ledgers from time zero through block 48,902,346, and the two stalled proxies' full ledgers and rejected Core executions. The [full ledger capture](../../artifacts/pt01_newest_fee_controls/full_core_ledgers.json.gz) and [machine summary](pt01_newest_fee_controls.json) retain the raw responses and every compared address, hash, fee, and timestamp.

| Public Core ledger observation | 27 successful proxies | 2 stalled proxies |
| --- | ---: | ---: |
| First recorded inbound funding entry has a 1 USDC `fee` | 27 | 0 |
| First recorded inbound funding entry has a zero `fee` | 0 | 2 |
| First recorded outgoing USDC spot send has a zero `fee` | 27 | No successful send |
| Recorded outgoing USDC spot sends to the newest Exchange | 84, all zero fee | 0 |
| Matched nonzero-perp sweeps delivered and credited | 73, all zero fee | 0 |
| Successful perp-to-spot class transfer recorded | At least one per credited sweep | Both proxies |

The successful proxies' first recorded funding modes were 14 `send`, 11 `internalTransfer`, and two `spotTransfer`. Both stalled proxies first received `send` entries. All 14 successful controls with that same first funding mode show a 1 USDC fee on it, while both stalled entries show zero. Only the two controls first funded by a spot transfer have separate `accountActivationGas` entries in these non-funding ledgers. Successful controls were first funded on October 9 through 18, 2026; the stalled proxies were first funded on October 9 and 10, overlapping the control dates.

[Hyperliquid's activation-gas documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/activation-gas-fee) says a new HyperCore account's first inbound transaction requires one quote token of fees and that unactivated accounts cannot send CoreWriter actions. The saved fee split is consistent with an activation or transfer-gas condition. It does not establish the stalled accounts' activation state or the fee required by their rejected spot sends. Both stalled ledgers contain a successful class transfer before the rejected spot send, and the public API does not expose a successful outgoing send from either account to measure its fee.

The public `userNonFundingLedgerUpdates` response can omit categories, and a time-zero query means the first *returned* funding entry. The Core explorer separately reports that the attempted spot sends failed for insufficient USDC transfer gas. No cryptographic Core state proof or exact fee rule is claimed here. Run `python3 scripts/atlas_pt01_newest_fee_controls.py` to verify the saved evidence offline; `--capture` refreshes the 29 public Core ledgers.
