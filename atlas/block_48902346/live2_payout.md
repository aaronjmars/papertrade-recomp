# Payout math, fees and the new accounting surfaces after the pin

This document tests the payout curve, the fee and split arithmetic, the queue payout path and the accounting regressions on the **second** Papertrade implementation set (docs *contract set 2*, live since the 2026-10-21 governance batch), and compares every case with the pinned baseline at block 48,902,346. It is behavior reconstructed from exact runtimes: port-free Foundry replays that load the live Exchange proxy, implementation and linked library, the live SessionKeyManager, the live Tokenomics proxy and implementation, and the saved prestate storage, then drive the real signed close `0x2792e706` or the real `liquidateBatch(uint256[])` entrypoint. The only mocked input is the HyperCore BBO precompile `0x080e`, answered with the CertiK close read (251080/251090, midpoint 251085). Read-only public-RPC probes of the live contracts are labelled separately; the public RPC ignores block parameters, so every probe is current state, not pinned state.

Ledger: [`live2_payout.json`](live2_payout.json). Raw replay output: [`replay.json`](../../artifacts/live2_payout/replay.json). Public probes: [`live_probes.json`](../../artifacts/live2_payout/live_probes.json). Run `python3 scripts/audit_live2_payout.py` to re-derive everything offline; `--capture` refreshes the public probes.

## Runtimes and pinned comparison

| Role | Address | Bytes | SHA-256 |
|---|---|---:|---|
| Exchange implementation | `0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723` | 23959 | `fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268` |
| Exchange linked library | `0x583d0bd818c991c5830fea93aef04e474b272459` | 6286 | `ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440` |
| SessionKeyManager implementation | `0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946` | 4521 | `7df05c33597c04820a314fae015aab01b5566aff53e9bded8446962cfd4ad2c9` |
| Tokenomics implementation | `0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03` | 6452 | `56caf868c73dbc33b94725972fc101dbcec0fb7b017c4f2f9e8cda49516992e9` |

Both variants ran the same 31 cases. They hash-match on **every** case: 31 live rows, 31 pinned rows, identical raw PnL, adjusted PnL, fee, balance delta, queue delta, Tokenomics debit and credit, and staker/developer accumulation (asserted for all 31 rows). The library call shape did change: the pinned pair `0x82296364` / `0xef1a27a9` is replaced by `0x06c5308a` (ten arguments) and `0xb9370332` (nine arguments), and `0xb9370332` takes the LP bankroll as its last argument, which is what creates the B3 boundary below.

## B1 - the payout curve at and beyond the caps

| Notional (USDC) | Margin (USDC) | Leverage | Raw PnL (USDC) | Adjusted PnL (USDC) | Fee (USDC) | Net payout (USDC) | Haircut % |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 50,000 | 100 | 500 | 86.776118 | 67.473645 | 1.349473 | 66.124172 | 22.243992 |
| 500,000 | 1,000 | 500 | 867.761176 | 674.736449 | 13.494729 | 661.241720 | 22.243992 |
| 10,000,000 | 20,000 | 500 | 17,355.223523 | 13,494.728986 | 269.894580 | 13,224.834407 | 22.243992 |
| 10,000,000 | 10,000 | 1000 | 17,355.223523 | 13,494.728986 | 269.894580 | 13,224.834407 | 22.243992 |
| 250,000,000 | 500,000 | 500 | 433,880.588083 | 337,368.224659 | 6,747.364493 | 330,620.860166 | 22.243992 |
| 500,000,000 | 1,000,000 | 500 | 867,761.176165 | 674,736.449318 | 13,494.728986 | 661,241.720332 | 22.243992 |

The payout is exactly linear in notional: raw per notional is `0.001735522352331` across the 50,000, 500,000 and 10,000,000 rows, and the 250,000,000 and 500,000,000 rows land on the same ratio. The same notional from a different margin and leverage pair returns the same PnL (the 10,000,000 row at leverage 1,000). The haircut percentage is one value across the whole sweep. Nothing in the close path binds the payout: the only control the 250,000,000 row needs is the labelled market-aggregate override (a synthetic position that no open ever added to the 96-bit side aggregate underflows the release subtraction); the OI limits act on open, not on close.

What bounds a payout, quoted from current live reads: `lpBankrollAvailable()` = `0x00000000000000000000000000000000000000000003ffade53188b958fa2c0a` = 4,834,188.713832 USDC, and `queueHarvestAvailable()` = 4,834,189.535893 USDC. A payout above the bankroll is deferred into the queue rather than paid (B3/B5). The per-side open-interest limits live in market-field word 1; their unit is unresolved, so no USDC cap is claimed here.

## B2 - rounding direction

| Case | Rate word | Adjusted PnL | Fee (raw units) | floor(adj*rate/1e18) | Staker share | Developer share |
|---|---:|---:|---:|---:|---:|---:|
| b2_win_rate1 | 1 | 13494728986365670576511 | 13494 | 13494 | 6747 | 6747 |
| b2_win_rate3 | 3 | 13494728986365670576511 | 40484 | 40484 | 20242 | 20242 |
| b2_win_rate_odd | 333333333333333333 | 13494728986365670576511 | 4498242995455223521005 | 4498242995455223521005 | 2249121497727611760502 | 2249121497727611760503 |

Every component floors. The win fee is `floor(adjusted x slot24 / 1e18)`, the staker share is `floor(fee / 2)` and the developer share is `fee - floor(fee / 2)`, so on an odd fee the extra unit goes to the developer (`2249121497727611760503` against `2249121497727611760502`). A zero rate zeroes the fee and both shares. The deadband floor is also exact: a move equal to `floor(entryPrice/50000)` returns zero profit and one quote unit more returns a nonzero profit (`0` then `39897065570827265654`). No composition rounds in the user's favour.

## B3 - the profit-plus-fee boundary on the live library

| LP bankroll (avail) | Paid now | Queued | Tokenomics debit | Staker+developer |
|---:|---:|---:|---:|---:|
| 0 | 20000000000000000000000 | 13224834406638357164981 | 13224834406638357164981 | 0 |
| 6612417203319178582490 | 26612417203319178582490 | 6612417203319178582491 | 13224834406638357164981 | 0 |
| 13224834406638357164980 | 33224834406638357164980 | 1 | 13224834406638357164981 | 0 |
| 13224834406638357164981 | 33224834406638357164981 | 0 | 13224834406638357164981 | 0 |
| 13494728986365670576511 | 33224834406638357164981 | 0 | 13494728986365670576511 | 269894579727313411530 |
| 4982012573755118958351370 | 33224834406638357164981 | 0 | 13494728986365670576511 | 269894579727313411530 |

The direct payout threshold is `avail >= adjusted - fee` = `13224834406638357164981`; the fee is split to staker and developer only at `avail >= adjusted` = `13494728986365670576511`. Between the two the user is paid the full net win (`33224834406638357164981`) while the staker and developer buckets receive nothing and the LP debit is `13224834406638357164981` instead of `13494728986365670576511`, so the fee `269894579727313411530` is dropped from both. The user's total claim (paid now plus queued) is continuous across the boundary, so there is no user gain; the accounting oddity is on the staker/developer side and the LP debit. Below the payout threshold the payout splits into the margin plus the available bankroll now and the remainder queued, and the LP debit is the queued net win (one case, `b3_avail0`, instead debits the gross adjusted PnL). This reproduces the earlier library's documented boundary shape; the numbers are identical on the pinned runtime.

## B4 - fee split, negative PnL and the zero boundary

| Case | Adjusted PnL | Fee | Staker | Developer | Trader credit | Tokenomics credit |
|---|---:|---:|---:|---:|---:|---:|
| b4_loss | -199485327854136328273 | 3989706557082726565 | 1994853278541363282 | 1994853278541363283 | 19800514672145863671727 | 195495621297053601708 |
| b4_loss_r23_0 | -199485327854136328273 | 0 | 0 | 0 | 19800514672145863671727 | 199485327854136328273 |
| b4_loss_r23_3 | -199485327854136328273 | 598 | 299 | 299 | 19800514672145863671727 | 199485327854136327675 |

A losing close charges `floor(|adjusted| x slot23 / 1e18)`, splits it the same way (floor to staker, remainder to developer), pays the trader `margin + adjusted` under every rate, and calls Tokenomics `onCloseBatch` with debit zero and `mintBasis = credit = |adjusted| - fee`. The fee therefore reduces the LP credit and the PAPER mint basis, never the trader credit. A zero rate zeroes the fee, both shares, and restores the full `|adjusted|` to the LP credit. Identical on the pinned runtime.

## B5 - queue, harvest and deferral

| Step | Value |
|---|---:|
| Close: balance credit | 20000000000000000000000 |
| Close: amount queued | 13224834406638357164981 |
| Close: Tokenomics debit | 13224834406638357164981 |
| harvest(10) returns | 13224834406638357164981 |
| harvest(10) balance credit | 13224834406638357164981 |
| harvest(10) queue debit | -13224834406638357164981 |
| Second harvest(10) returns | 0 |

A deferred payout is paid exactly once, in full: the close pays the margin and enqueues exactly `adjusted - fee`; the first harvest pays that amount to the ordinary balance and reduces `totalQueued` by the same amount; a second harvest pays zero. Nothing is lost and nothing is double counted. The library's merge and consolidation selectors are only reached through their Exchange wrappers in the tested two-node states, where they revert; the enqueue path and the harvest path are the two that the real close path uses.

## B6 / B8 - the new rebate and builder surfaces

All rows below are saved read-only public-RPC probes at current head unless marked local.

| Selector | Caller | Result |
|---|---|---|
| `br_feeRate` | any | `0x0000000000000000000000000000000000000000000000000011c37937e08000` |
| `br_setFeeRate_owner_1` | timelock owner | `0x` |
| `br_setFeeRate_guard` | guardian multisig | `revert` |
| `br_approveBuilder_owner` | timelock owner | `0x` |
| `br_approveBuilder_guard` | guardian multisig | `revert` |
| `skm_setBuilderRegistry_rand` | stranger | `revert` |
| `skm_setBuilderRegistry_owner_zero` | timelock owner | `0x` |
| `skm_builderRegistry` | any | `0x000000000000000000000000fdc6550436dd75ce8a0b145f935b7d3a64f53248` |
| `ex_authorizedKeeper` | any | `0x0000000000000000000000000924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56` |
| `ex_treasury` | any | `0x000000000000000000000000000000000000000000206cf8425249a455dce800` |
| `ex_lpBankrollAvailable` | any | `0x00000000000000000000000000000000000000000003ffade53188b958fa2c0a` |

| Local exact-runtime probe | Caller | ok | Revert | Storage writes | Logs | Return |
|---|---|---:|---|---:|---:|---|
| `tk_activateRebate_stranger` | local | 0 | `0000000000000000000000000000000000000000000000000000000030cd7471` | 0 | 0 | `0000000000000000000000000000000000000000000000000000000030cd7471` |
| `tk_eedf4c43` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `11308874160667646130` |
| `tk_456db972` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `0` |
| `tk_122b6689` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `1311699483804150265469851653` |
| `tk_4ec7182e` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `1000000000000000000` |
| `ex_69f9a5f0_owner` | local | 1 | `none` | 0 | 0 | `empty` |
| `ex_69f9a5f0_stranger` | local | 1 | `none` | 0 | 0 | `empty` |
| `ex_9d346583_owner` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `0` |
| `ex_f009ac03_owner` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `0` |
| `ex_cbce7532_owner` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `0` |
| `ex_d970fad5_owner` | local | 0 | `none` | 0 | 0 | `empty` |
| `ex_e6ac4a74_owner` | local | 0 | `none` | 0 | 0 | `empty` |
| `ex_5780639d_owner` | local | 0 | `none` | 0 | 0 | `empty` |
| `skm_builderRegistry` | local | 1 | `0000000000000000000000000000000000000000000000000000000000000000` | 0 | 0 | `0` |
| `skm_setBuilderRegistry_owner` | local | 0 | `0000000000000000000000000000000000000000000000000000000030cd7471` | 0 | 0 | `0000000000000000000000000000000000000000000000000000000030cd7471` |
| `reg_setFeeRate_owner` | local | 0 | `0000000000000000000000000000000000000000000000000000000030cd7471` | 0 | 0 | `0000000000000000000000000000000000000000000000000000000030cd7471` |


The local rows run on the saved prestate storage, so a value that lives in post-pin constructor state reads zero or NotOwner locally: `skm_builderRegistry` and the BuilderRegistry owner are of that kind, and the read-only probe table above is authoritative for them. The Exchange and Tokenomics selectors are exercised against the real delegated implementations.

The rebate surface, from a local exact-runtime replay of the live Tokenomics: `activateRebate()` takes no argument, reverts `0x30cd7471` for a stranger and for the guardian multisig, and from the owner writes exactly one slot and emits one four-word event.

| Tokenomics read | Before activateRebate | After activateRebate |
|---|---:|---:|
| slot 9 | 0 | 1311699483804150265469851653 |
| getter 0x122b6689 | 0 | 1311699483804150265469851653 |
| PAPER total supply | 8621543501618220608396651701 | 8621543501618220608396651701 |

The PAPER supply is unchanged, no Tokenomics settlement path runs and no Exchange or Staking storage is written, so the rebate activation mints no token and credits no balance. The live getter `0x122b6689` is already nonzero on chain (0x0000000000000000000000000000000000000000038eba31582a5470aaca7592), so the batch's rebate call has taken effect.

## B8 - the builder surface

Findings: BuilderRegistry `feeRate()` is 0.5% on the 1e18 scale; `setFeeRate` and `approveBuilder` succeed from the timelock owner and revert for the guardian multisig and a stranger, so the builder fee is owner-only. SessionKeyManager `setBuilderRegistry` is owner-only, and `builderRegistry()` returns the live registry `0xfdc6550436dd75ce8a0b145f935b7d3a64f53248`. The added Exchange selector `0xf009ac03` takes an address and returns a bool; `builderFees(address)` reads zero for both stalled-sweep users; `claimBuilderFees(address)` succeeded from the owner and from a stranger at that zero balance and moved no storage and emitted no log. No builder was attached to any close in these replays, so whether a builder fee creates a credit the LP accounting did not pay for stays **plausible-unproven**; a real close carrying a builder and a nonzero `builderFees` balance would settle it. The local replay sets the Tokenomics owner word (slot 0, owner at bit 16) so the owner-guarded rows are exercised as the real owner.

## B7 - Guardian H-02, M-02 and M-04 on the live implementations

| Check | Live result | Pinned result |
|---|---|---|
| H-02 queued win Tokenomics debit | 13224834406638357164981 | 13224834406638357164981 |
| H-02 queued amount | 13224834406638357164981 | 13224834406638357164981 |
| M-04 solvent win Tokenomics debit | 13494728986365670576511 | 13494728986365670576511 |
| M-04 fee split | 134947289863656705765 + 134947289863656705765 | same |
| M-02 liquidation, totalQueued 0: LP credit | 19600000000000000000000 | 19600000000000000000000 |
| M-02 liquidation, totalQueued 0: staker | 200000000000000000000 | same |
| M-02 liquidation, totalQueued 1: LP credit | 20000000000000000000000 | 20000000000000000000000 |
| M-02 liquidation, totalQueued 1: staker | 0 | same |

All three fixes hold on the live implementations with numbers identical to the pinned ones. H-02: a queued win debits Tokenomics by exactly the queued claim, so LP equity moves with the claim. M-04: a solvent win debits the gross adjusted win, fee included, and the fee is separately split to staker and developer. M-02 reproduces: with `totalQueued` zero the liquidation credits the margin less the 2% liquidation fee (split to staker and developer) and with `totalQueued` one wei it credits the full margin with the fee waived. The Exchange side bucket (slot 27) stays zero in both liquidation replays, so the side-bucket allocation REPORT.md measured in its archive replay is not reproduced here; the M-02 branch itself is decided, the side bucket is not.

## Ledger

| Id | Title | Invariant | Actor | Affected | Severity | Status |
|---|---|---|---|---|---|---|
| L2-B1 | Payout is linear in notional from 50,000 to 500,000,000 USDC | A3 price and eligibility bounds | unprivileged user | both | info | confirmed_simulation |
| L2-B2 | Every payout and fee component floors; the split remainder goes to the developer | A3 price and eligibility bounds | unprivileged user | both | info | confirmed_simulation |
| L2-B3 | Fee accrual starts one fee above the payout threshold, so the fee is dropped between the two | A4 liability reconciliation | LP / keeper (no unprivileged trigger found) | both | low | confirmed_simulation |
| L2-B4 | Losing close: fee floors from the loss, split floors equally, and the LP credit is the loss less the fee | A4 liability reconciliation | unprivileged user | both | info | confirmed_simulation |
| L2-B5 | A deferred payout is paid exactly once, in full, at harvest | A4 liability reconciliation | unprivileged user | both | info | confirmed_simulation |
| L2-B6 | activateRebate is owner-only, sets one Tokenomics slot, and mints nothing | A5 upgrade authority | owner (timelock), unprivileged user | set2 | info | confirmed_simulation |
| L2-B7 | Guardian H-02, M-02 and M-04 all behave identically on the set-2 implementations | A4 liability reconciliation | unprivileged user / keeper | both | info | confirmed_simulation |
| L2-B8 | Builder fee plumbing is owner-guarded; whether a builder fee is LP-funded is not settled | A5 upgrade authority | owner (timelock), builder, unprivileged user | set2 | low | plausible_unproven |

## Limits

Every replay is a port-free Foundry execution of the exact live runtimes against the saved block-48,901,631 prestate storage, with the HyperCore BBO precompile mocked. Balance credits, queue columns and Tokenomics deltas are therefore local-scenario values built on pinned accounting, not current chain values; the current live figures quoted (treasury, lpBankrollAvailable, queueHarvestAvailable, fee rates, owner, keeper) are labelled read-only public-RPC probes. The public RPC ignores block parameters, so nothing here is a historical state read. No archive endpoint is configured, so a pre-pin incident-era fetch is not repeated. The OI-cap unit, the builder-fee plumbing on a real builder-carrying close, and the side-bucket allocation are the three open observations.
