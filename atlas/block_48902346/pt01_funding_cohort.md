# PT-01 first funding and outgoing fee cohort

The [offline verifier](../../scripts/atlas_pt01_funding_cohort.py) joins all 38 captured older deposit proxy Core ledgers to the 29 newest proxy ledgers through block 48,902,346. These are the known older factory cohorts and the 29 newest proxies selected for the nonzero-perp sweep check, not every newest deposit proxy. The [machine summary](pt01_funding_cohort.json) links the saved ledgers and four [public Core explorer transaction details](../../artifacts/pt01_funding_cohort/system_first_funding.json.gz).

| Proxy group | First returned funding fee: 1 USDC | First returned funding fee: 0 | First successful outgoing spot-send fee: 0 | First successful outgoing spot-send fee: 1 USDC | No successful outgoing send |
| --- | ---: | ---: | ---: | ---: | ---: |
| 38 older | 36 | 2 | 36 | 2 | 0 |
| 29 newest | 27 | 2 | 27 | 0 | 2 |

All 63 proxies with a 1 USDC fee on their first returned funding entry have a zero-fee first outgoing spot send. The four zero-fee first funding entries came from the same Core sender, `0x6b9e773128f453f5c2c60935ee2de2cbc5390a24`. Core explorer classifies all four successful first transactions as `SystemSendAssetAction` to the proxy. The two older proxies then had full-balance spot sends rejected with `Insufficient USDC balance for token transfer gas.`, followed by reduced sends that each incurred a 1 USDC fee and were credited. The two newest proxies have only rejected full-balance sends and no successful outgoing send through the pin.

The same sender and action type make a first-use fee explanation more specific than a funding-mode comparison alone. They do not identify the Core validator's exact predicate, prove the four accounts' activation state at the historical send blocks, or establish that a 1 USDC reserve will work for the two newest accounts today. The public Core ledgers and explorer are API responses, not Core state proofs. [Hyperliquid's activation-gas documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/activation-gas-fee) describes a new-account fee, but it does not document the exact `Insufficient USDC balance for token transfer gas.` condition observed here. The two newest proxies completed a CoreWriter class transfer before their rejected spot sends, so the published statement that unactivated accounts cannot send CoreWriter actions does not by itself explain this sequence.

Run `python3 scripts/atlas_pt01_funding_cohort.py` to verify the saved evidence offline. `--capture` refreshes the four public explorer responses; `--write` rebuilds the machine summary from saved inputs.
