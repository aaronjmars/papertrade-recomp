# Asymmetric-impact haircut and reference notional

This document tests the CertiK BBO pricing incident claim against the exact pinned runtimes: that the winning-close profit haircut multiplies a **fixed reference notional**, so the haircut percentage does not grow with position size while the dollar payout does. The claim is confirmed for the pinned Exchange suite, and the same claim is re-measured against the Exchange implementation deployed at `latest`.

Verdict: the pinned runtime reproduces CertiK's numbers exactly, not only its mechanism, and the haircut percentage is independent of position size in both the pinned and the deployed implementation. The deployed implementation differs only for moves inside the holdback bands the contract-set-2 docs describe, where it pays less while keeping the same size independence.

Pinned suite: Exchange proxy `0x6cd5661646289fb6e65ea5c032310fded797d0a2`, implementation `0x0f3febfc94876b0c895f7acecdc8f5c863b549ee`, linked library `0xcd617f984158a4f5d287ddee0e8eb0fed204916d`, at block 48902346. Every replay below restores the saved mixed-close prestate at block 48901631, etches the exact runtimes, mocks the BBO precompile `0x080e` with the CertiK close read (251080/251090 -> midpoint 251085), writes one ETH-market position with the CertiK entry price 250645 and runs the real signed close `0x2792e706` on the real proxy.

## Where the formula lives

The Exchange builds a nine-word call to the linked library selector `0x82296364` and pairs it with the settlement call `0xef1a27a9`. The saved calls, the pinned instrument record and the local replays agree on the argument map:

```text
0x82296364(entryPrice, exitPrice, margin, leverage, isLong,
            baseRate, rateMultiplier, positionMultiplier, referenceNotional)
0xef1a27a9(margin, user, adjustedPnl, isLong, queueFlag, profitRate, lossRate, x)
```

Only `margin` and `leverage` carry position size; `baseRate` (10%), `rateMultiplier` (15,000), `positionMultiplier` (483.979 for ETH) and `referenceNotional` (100,000) are per-instrument constants read from the instrument record at mapping slot 7. The documented pipeline is

```text
move   = (|exit - entry| - floor(entry / 50000)) / entry     # deadband
rawPnl = margin * leverage * move_units / entry
term1  = 1 / (move * rateMultiplier)
term2  = referenceNotional / (1e6 * move * positionMultiplier)
scale  = (1 - baseRate) / (1 + term1 + term2)
adjustedPnl = rawPnl * scale
winFee = adjustedPnl * 2%
```

The library's integer form reproduces this formula: `term1` and `term2` are `riskInverse/WAD` and `liquidityInverse/WAD` of the pinned model, all 74 saved `0x82296364` calls return the integer form's two words exactly, and the rational evaluation of the published formula agrees with the integer form to better than 1e-9 relative on every replay case, the staged floor divisions accounting for the last digits. Each Forge case asserts the integer form's own numbers.

## Size sweep on the pinned implementation

| Position notional (USDC) | Margin (USDC) | Leverage | Raw PnL (USDC) | Adjusted PnL (USDC) | Win fee (USDC) | Net payout (USDC) | Haircut % | User balance delta (USDC) | Queued (USDC) |
|---|---|---|---|---|---|---|---|---|---|
| 10,000,000 | 20,000 | 500 | 17,355.223523 | 13,494.728986 | 269.894580 | 13,224.834407 | 22.243992 | 33,224.834407 | 0.000000 |
| 500,000 | 1,000 | 500 | 867.761176 | 674.736449 | 13.494729 | 661.241720 | 22.243992 | 1,661.241720 | 0.000000 |
| 50,000 | 100 | 500 | 86.776118 | 67.473645 | 1.349473 | 66.124172 | 22.243992 | 166.124172 | 0.000000 |
| 2,000,000 | 20,000 | 100 | 3,471.044705 | 2,698.945797 | 53.978916 | 2,644.966881 | 22.243992 | 22,644.966881 | 0.000000 |
| 500,000 | 2,000 | 250 | 867.761176 | 674.736449 | 13.494729 | 661.241720 | 22.243992 | 2,661.241720 | 0.000000 |
| 250,000,000 | 500,000 | 500 | 433,880.588083 | 337,368.224659 | 6,747.364493 | 330,620.860166 | 22.243992 | 830,620.860166 | 0.000000 |

The 25x row is the one case that needs a labelled market-state control: the close releases the position's contribution from the market side aggregate, and with the untouched pinned aggregate that release underflows for a notional far above the aggregate the real opens built. Setting the two 96-bit aggregates to their maximum removes only that underflow; the haircut inputs come from the instrument record and are untouched, and every other row runs on the pinned market words.

The haircut percentage is identical in every row of the sweep: it depends on the price move and the four instrument constants only. The dollar payout is exactly proportional to margin x leverage. The CertiK figures for position 72098 (raw 17,355.223523, adjusted 13,494.728986, fee 269.894580, net 13,224.834407, haircut 22.243992%) and its hypothetical $500,000 position (net 661.241720) are reproduced exactly by the pinned runtime, so this is a reproduction of the numbers, not only of the mechanism.

## Haircut-input sensitivity and the constructed counterfactual

| Case | baseRate | rateMultiplier | referenceNotional | Notional (USDC) | Haircut % |
|---|---|---|---|---|---|
| base_rate_20pct | 0.20 | 15,000 | 100,000 | 10,000,000 | 30.883548 |
| rate_multiplier_30k | 0.10 | 30,000 | 100,000 | 10,000,000 | 20.931971 |
| reference_notional_1m | 0.10 | 15,000 | 1,000,000 | 10,000,000 | 59.622263 |
| counterfactual_ref_is_notional_500k | 0.10 | 15,000 | 500,000 | 500,000 | 44.909720 |
| counterfactual_ref_is_notional_10m | 0.10 | 15,000 | 10,000,000 | 10,000,000 | 93.046860 |
| holdback_4bp | 0.10 | 15,000 | 100,000 | 10,000,000 | 47.705805 |
| holdback_05bp | 0.10 | 15,000 | 100,000 | 10,000,000 | 90.587998 |
| holdback_4bp_500k | 0.10 | 15,000 | 100,000 | 500,000 | 47.705805 |
| holdback_4bp_2m | 0.10 | 15,000 | 100,000 | 2,000,000 | 47.705805 |

The last three rows are the pinned curve at a move inside the holdback bands the contract-set-2 docs describe; the deployed implementation pays less on those moves, as the next section measures. All three return the same haircut for 500,000, 2,000,000 and 10,000,000 USDC notional.

Raising `baseRate`, `rateMultiplier` or `referenceNotional` changes the haircut at fixed size, which is what makes the third property observable: in the two **constructed** counterfactual cases (`referenceNotional` set to the position's own notional, the Rollbit form the docs describe) the haircut grows from the small to the large position. Those two rows are simulations of a parameter the deployed code never sets, not observed chain state.

## Contract-set-1 to contract-set-2 delta

Every replay case was run twice: once on the pinned implementation and its pinned linked library, once on the deployed implementation, its deployed linked library and the deployed session-key manager, with the live configuration words (implementation pointer, instrument record, market fields and the instrument-count/curve word) read at `latest`.

| Case | Move | Notional (USDC) | Pinned net (USDC) | Deployed net (USDC) | Pinned haircut % | Deployed haircut % |
|---|---|---|---|---|---|---|
| holdback_4bp | 3.99 bps | 10,000,000 | 1,942.424369 | 606.864475 | 47.705805 | 83.661918 |
| holdback_05bp | 0.52 bps | 10,000,000 | 29.440083 | 23.867293 | 90.587998 | 92.369620 |
| holdback_4bp_500k | 3.99 bps | 500,000 | 97.121218 | 30.343224 | 47.705805 | 83.661918 |
| holdback_4bp_2m | 3.99 bps | 2,000,000 | 388.484874 | 121.372895 | 47.705805 | 83.661918 |

The delta is confined to moves inside the holdback bands: at the incident's 17.55 bps move the two implementations are numerically identical, and at 3.99 bps the deployed curve withholds far more of the gain. The deployed library also changed shape: the pinned pair `0x82296364` / `0xef1a27a9` is gone, replaced by `0x06c5308a` (ten arguments: the pinned nine plus a payout-curve selector) and `0xb9370332`. The four instrument constants are byte-identical in the live instrument record, and the deployed haircut is still one value across 50,000 to 250,000,000 USDC notional and across 500,000 to 10,000,000 USDC inside the holdback band, so size independence survived the upgrade.

## What bounds the payout

- **Open-interest caps.** Market field word 1 carries two 128-bit per-side limits for the ETH market. The keeper selector `0x628a9fd6` writes them and the signed-open path compares the updated side value against them: 27 of 57 saved signed opens reverted with `OiCapExceeded()` while the other 30 stayed at or below the limit. The limits at `latest` are 2.23x and 2.95x lower than the pinned ones, matching the project's statement that it tightened launch limits after the incident. The compared values' unit stays unresolved in the atlas, so no USDC notional cap is claimed.
- **LP bankroll.** `lpBankrollAvailable = 0 if totalQueued > 0 else max(treasury - totalBalances - totalLockedMargin - stakerFeeAccumulator - devFeeAccumulator, 0)`. At the replay prestate the available figure is 5,002,012.57 USDC, and the largest replayed close credited 830,620.86 USDC to the trader with no queue entry.
- **Queue.** Every replay row credited directly with a zero queue delta, and the pinned suite has a queued-profit close branch, so a payout larger than the available bankroll is deferred rather than paid immediately.
- **Reachability.** the haircut path has no position-size term, so a larger admissible notional raises the payout at an unchanged percentage. CertiK reports the examined account using notionals from 500,000 to 10,000,000 USDC across 296 profitable closes, and the pinned instrument record allows leverage up to 1000. Whether a given notional is admissible at a given cap cannot be decided offline because the cap unit is unresolved; the live caps are lower than the pinned ones.
- **What CertiK did not establish.** that the quotes it read were distorted or deliberately influenced: its own text says timestamp overlap alone is insufficient and that ordered market-wide quotes plus an independent reference would be needed; that position 72098 needed anything beyond ordinary leveraged trading: it states the example is consistent with the recorded settlement rules; the project's post-incident cap changes and recovery through other accounts, which CertiK records as not independently verified.
- **The protocol's own admission.** the paid docs state the curve 'is not a deviation check ... and does not guarantee that a manipulation strategy is unprofitable', and that the protocol reads BBO without a deviation breaker

## Saved-call provenance

74 saved `0x82296364` delegatecalls in 32 historical transactions (blocks 48173881-48902330) were decoded. All of them reproduce the reconstructed model, and their haircut arguments are constant per market while the position notional spans 4,777 up to 4,455,000 USDC across 37 profitable calls. The observed argument sets are:

```text
baseRate            [100000000000000000]
rateMultiplier      [15000000000000000000000]
positionMultiplier  [483979000000000000000, 814598000000000000000]
referenceNotional   [100000000000000000000000]
```

These are the pinned instrument-record values of the two live markets, so no position size reaches the haircut path.

## Currently deployed implementation

At `latest` (block 49258776) the Exchange proxy points to `0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723` (23959 runtime bytes, sha256 `fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268`), which links `0x583d0bd818c991c5830fea93aef04e474b272459` (6286 runtime bytes, sha256 `ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440`). The pinned linked library is `0xcd617f984158a4f5d287ddee0e8eb0fed204916d` (5790 runtime bytes).

| Check | Result |
|---|---|
| Linked library byte-identical after blanking linked addresses and metadata | False |
| `0x82296364` present in pinned library | True |
| `0x82296364` present in live library | False |
| `0xef1a27a9` present in live library | False |
| Selectors added in live library | 0x06c5308a, 0xb9370332 |
| Selectors removed from pinned library | 0x82296364, 0xef1a27a9 |
| Live ETH instrument record equals pinned record | True |

So the pinned and live runtimes are **not** byte-identical: the linked library grew, the pinned profit-math and settlement selectors are gone, and two new selectors appeared (contract set 2 per the docs, which added a holdback band and a payout-curve selector). The Exchange implementation changed too, and with it the session-key manager implementation (`0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946`, 4521 runtime bytes), whose close path calls a different manager selector. The four instrument constants themselves are byte-identical, and the live replay below measures whether the size relation survived.

## Deployed-implementation replay

The same 15 cases on the deployed implementation, its deployed library and the deployed session-key manager:

| Case | Position notional (USDC) | Margin (USDC) | Leverage | Raw PnL (USDC) | Adjusted PnL (USDC) | Win fee (USDC) | Net payout (USDC) | Haircut % | User balance delta (USDC) | Queued (USDC) |
|---|---|---|---|---|---|---|---|---|---|---|
| certik_10m | 10,000,000 | 20,000 | 500 | 17,355.223523 | 13,494.728986 | 269.894580 | 13,224.834407 | 22.243992 | 33,224.834407 | 0.000000 |
| certik_500k | 500,000 | 1,000 | 500 | 867.761176 | 674.736449 | 13.494729 | 661.241720 | 22.243992 | 1,661.241720 | 0.000000 |
| certik_50k | 50,000 | 100 | 500 | 86.776118 | 67.473645 | 1.349473 | 66.124172 | 22.243992 | 166.124172 | 0.000000 |
| certik_2m_lev100 | 2,000,000 | 20,000 | 100 | 3,471.044705 | 2,698.945797 | 53.978916 | 2,644.966881 | 22.243992 | 22,644.966881 | 0.000000 |
| certik_500k_lev250 | 500,000 | 2,000 | 250 | 867.761176 | 674.736449 | 13.494729 | 661.241720 | 22.243992 | 2,661.241720 | 0.000000 |
| certik_250m | 250,000,000 | 500,000 | 500 | 433,880.588083 | 337,368.224659 | 6,747.364493 | 330,620.860166 | 22.243992 | 830,620.860166 | 0.000000 |
| base_rate_20pct | 10,000,000 | 20,000 | 500 | 17,355.223523 | 11,995.314655 | 239.906293 | 11,755.408361 | 30.883548 | 31,755.408361 | 0.000000 |
| rate_multiplier_30k | 10,000,000 | 20,000 | 500 | 17,355.223523 | 13,722.433220 | 274.448664 | 13,447.984556 | 20.931971 | 33,447.984556 | 0.000000 |
| reference_notional_1m | 10,000,000 | 20,000 | 500 | 17,355.223523 | 7,007.646563 | 140.152931 | 6,867.493632 | 59.622263 | 26,867.493632 | 0.000000 |
| counterfactual_ref_is_notional_500k | 500,000 | 1,000 | 500 | 867.761176 | 478.052057 | 9.561041 | 468.491016 | 44.909720 | 1,468.491016 | 0.000000 |
| counterfactual_ref_is_notional_10m | 10,000,000 | 20,000 | 500 | 17,355.223523 | 1,206.732899 | 24.134658 | 1,182.598241 | 93.046860 | 21,182.598241 | 0.000000 |
| holdback_4bp | 10,000,000 | 20,000 | 500 | 3,790.221229 | 619.249464 | 12.384989 | 606.864475 | 83.661918 | 20,606.864475 | 0.000000 |
| holdback_05bp | 10,000,000 | 20,000 | 500 | 319.176525 | 24.354381 | 0.487088 | 23.867293 | 92.369620 | 20,023.867293 | 0.000000 |
| holdback_4bp_500k | 500,000 | 1,000 | 500 | 189.511061 | 30.962473 | 0.619249 | 30.343224 | 83.661918 | 1,030.343224 | 0.000000 |
| holdback_4bp_2m | 2,000,000 | 4,000 | 500 | 758.044246 | 123.849893 | 2.476998 | 121.372895 | 83.661918 | 4,121.372895 | 0.000000 |

The live implementation matched the pinned model's raw PnL, adjusted PnL and fee in 11 of 15 cases. Every case at the incident's 17.55 bps move matched, and the size sweep from 50,000 to 250,000,000 USDC notional returned one single haircut value (22.243992%), so the haircut percentage is still independent of position size in the deployed code. The differences are confined to holdback_4bp, holdback_05bp, holdback_4bp_500k, holdback_4bp_2m: moves inside the holdback bands the contract-set-2 docs describe, where the deployed library holds the move back and pays less (3.99 bps: 1,942.424369 pinned vs 606.864475 deployed; 0.52 bps: 29.440083 pinned vs 23.867293 deployed). The holdback sweep at 3.99 bps also returns one single haircut value (83.661918%) across 500,000, 2,000,000 and 10,000,000 USDC notional, so size independence holds inside the band as well. The call-shape change is a tenth argument (value 1) on the deployed math selector 0x06c5308a, matching the curve selector the instrument-count word carries; the other four instrument constants are unchanged.

## Limits

- Only the winning-close profit path is measured. Losing closes bypass the scale factor entirely (both saved and replayed loss cases return adjustedPnl == rawPnl), so the haircut finding does not apply to them.
- The offline comparison of the live implementation is a live-code capture plus an offline diff and local replay. The public RPC ignores block parameters and exposes no debug tracer, and no archive endpoint is configured, so the incident-era runtime at block 48,202,386 cannot be fetched; the pinned suite is used as the incident-era proxy on the strength of its deployer creation block and the absence of any recorded Upgraded log through the pin, not of a fetched historical bytecode read.
- The live replay restores pinned storage for the Exchange accounting fields and overrides only the configuration the live capture shows changed: the implementation pointer, the implementation and library code, the instrument record, the market fields and the instrument-count/curve word. Live accounting (treasury, totalBalances, totalLockedMargin, fee accumulators) is at its block-48,901,631 value, so the balance credit and queue columns are local-scenario values, not current chain values.
- The per-side open-interest caps in market field word 1 act as limits in the sampled signed-open paths, but their unit is unresolved, so this document does not convert a cap into a maximum notional and does not claim that any particular size is reachable at a given cap.
- CertiK's account-level net withdrawal of 1,279,106.191184 USDC, its Hyperliquid fill sample and its quote-overlap table were not re-derived here; this document only tests the haircut and reference-notional claim and the payout it produces.
- The holdback delta is a measured difference between two runtimes. That it is the documented holdback band is an inference from the documented band ranges and the curve-selector argument, not a source-level mapping: the deployed library's argument semantics are established by the replay's numbers, not by recovered source.
- The deployed session-key manager is restored so the real signed-close authorization runs; its own registry layout is outside this document, and no session-manager behavior is claimed beyond the two selectors the close path uses.

## Sources

- CertiK, PaperTrade BBO Pricing Incident, 2026-10-20: https://www.certik.com/blog/papertrade-bbo-pricing-incident (position 72098 numbers, the fixed 100,000 USDC reference notional, the 22.243992% haircut and the $500,000 hypothetical).
- Papertrade docs, Asymmetric impact PnL (contract set 2, updated 2026-10-21): https://docs.papertrade.xyz/how/asymmetric-impact and the contract-set-1 page https://docs.papertrade.xyz/v1/how/asymmetric-impact (identical formula for both sets).
- atlas/block_48902346/exchange_library_pseudocode.md and exchange_library_behavior.json (the pinned library model, 49 historical settlement pairs, 74 saved math calls).
- atlas/block_48902346/exchange_instruments_getter.md, exchange_instrument_creation.md and exchange_market_fields.md (instrument record packing, keeper market fields, instrument-count and market-keeper reads).
- atlas/block_48902346/exchange_close_paths.md, exchange_close_fee_effects.md and exchange_negative_close_fee.md (the signed-close branches and the 2% positive-PnL fee on Exchange slot 24).
- atlas/block_48902346/exchange_storage_behavior.md (lpBankrollAvailable formula), exchange_availability_behavior.json (the queue gate on that formula), exchange_open_limit.md and exchange_open_limit_full_behavior.json (per-side open limit guard at signed open, 57 sampled opens with 27 cap reverts) and exchange_market_fields.md (the keeper writes to those limits).
- Papertrade docs, Pricing: BBO precompile and the no-deviation-breaker note: https://docs.papertrade.xyz/how/pricing-bbo (quoted as the protocol's own limitation).
- artifacts/exchange_negative_close/original_prestate.json (the replay prestate) and artifacts/audit_certik_haircut/live/ (the live implementation, linked library, session-key-manager implementation and storage captures at latest).
