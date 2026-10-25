# Sequences of legitimate actions against the live Papertrade set

The phase-two hunt for value created or destroyed by *sequences* rather than single calls. The instrument is a port-free Foundry replay of the exact live runtimes (Exchange `0x0a44049d...`, linked library `0x583d0bd8...`, SessionKeyManager `0x04b5ea4c...`, Tokenomics `0x7c0a72a7...`) and the pinned set, loaded on the saved block-48,901,631 prestate, driving the venue's own signed open `0xec6783f0`, signed close `0x2792e706`, signed withdrawal `0x8d09f23f`, `liquidateBatch(uint256[])` `0x599dc539`, `harvest(uint256)` `0xddc63262` and the real BatchExecutor `execute` `0x251fb27d` with its saved allowlist. Positions are created by the venue's open, never written into storage by hand. The only mocked inputs are the HyperCore BBO precompile `0x080e`, the account status precompile `0x0810` and the spot-balance precompile `0x0801`; every mocked reply is labelled simulated.

Ledger: [`live2_sequences.json`](live2_sequences.json). Per-step raw rows: [`steps_live.csv`](../../artifacts/live2_sequences/steps_live.csv) and [`steps_pinned.csv`](../../artifacts/live2_sequences/steps_pinned.csv); full forge output in `artifacts/live2_sequences/forge_{live,pinned}.txt`. Run `python3 scripts/audit_live2_sequences.py` to re-derive everything offline; no credential and no network are used.

## The invariant and its correction

```text
treasury == totalBalances + totalLockedMargin + totalQueued
            + stakerFeeAccumulator + devFeeAccumulator + trackedLpUsd
```

Exchange slot 14 is the treasury, slot 22 low and high 128 bits are ordinary balances and locked margin, slot 18 is the queue, slot 26 low and high 128 bits are the staker and developer fee accumulators, and Tokenomics slot 3 is the signed tracked LP. The **side bucket (Exchange slot 27) is not a claim**: it is an earmark of the spendable LP bankroll. At block 48,173,889, the real close that wrote 400296219202209635129 into slot 27 coexists with `treasury - reserved` = 400296219202209635129 = trackedLp 377424392655154164362 + totalQueued 22871826547055470767`, whereas adding the side bucket would give 800592438404419270258. Adding it double counts the bankroll, and the pass-one identity (`atlas_all_suite_claims.py`) reconciles only because the pinned side bucket is zero.

The checker is validated by a negative control: writing 20,000 USDC of locked margin without a funding debit moves the residual to -20,000e18. Across the corrected replay, the only non-control deviation is a **positive** 1,000 USDC residual while debt margin is open. The same-quote close returns it to zero; every other settled step reconciles.

## SQ-L2-02: the reported debt-cycle mint is disproved

The earlier replay used a saved transaction read-set that omitted queue head and next-id slots 16 and 17. They defaulted to zero even though the pinned chain state had both at 4. With those pointers seeded coherently, the same exact runtimes consume queued credit on the debt open and restore it on a zero-PnL close. Harvest pays the existing queue once, and another debt open fails after that credit is gone.

| Stage | Queued credit | Accounting residual |
|---|---:|---:|
| before debt open | 1634.850990 | 0.000000 |
| debt margin open | 634.850990 | 1000.000000 |
| after same-quote close | 1634.850990 | 0.000000 |
| after harvest | 0.000000 | 0.000000 |
| after rejected repeat | 0.000000 | 0.000000 |

The earlier 3,237.31 USDC gain and 20,000 USDC claims excess were fixture artifacts. SQ-L2-02 is now `disproved` with severity `none`. This corrected replay rules out the claimed repeatable cycle; it is not an exhaustive proof of all queue states.

## Guards and negatives that held

| Sequence | Observed | Guard |
|---|---|---|
| open then close at the same quote, five times | adj = 0, balance credits 5000 USDC each, no mint, no fee, residual 0 | the user's claim returns to exactly the starting credit |
| deferred win then harvest twice | first harvest pays 1634.8510 USDC with tracked LP delta 0, second reverts `0x75e52f4f` | the queue claim was already debited at the close |
| liquidation with an empty queue | residual 0, margin less the 2 % fee split to stakers and developer | onLoss on the solvent branch |
| liquidation and a loss with a live queue | side bucket = trackedLp + queued in both, residual 0 | the side bucket is an earmark of the bankroll, not a second claim |
| both sides of one market closed in one batch at one quote | adj = 0 each, residual 0 | no self-impact |
| one-wei margin open and close | balance delta one raw unit, residual 0 | no rounding leak at the dust bound |
| close one quote unit past the deadband floor | adj = 0 exactly at floor(entry/50000), nonzero one unit later | the deadband floor is exact |
| open at leverage 1001 | reverts `0x0a4f5a07` | leverage bound 1000 |
| open 6,000e18 margin after the side aggregate grew | reverts `0x40f92143` | OiCapExceeded, the per-side 96/128-bit limit |
| withdraw with a true account status | debit exactly the signed 2 USDC, residual 0 | the signed amount is delivered in full |
| withdraw twice in one block | second reverts; after rolling one block, debit = signed amount + 1 USDC | one withdrawal per user per block |
| two closes in one BatchExecutor transaction | both inner calls execute, two PositionClosed events, residual 0 | the allowlist accepts close |

## Limits

Every replay runs on the saved prestate, so the pinned rows use the saved implementations and the live rows override the proxy implementation slots with the live runtimes; the raw rows for both are saved and 99 of 107 rows agree on all nine book fields. The prestate is a transaction read-set, not a full state, which is why `pushStakerFees` cannot be exercised (see SQ-L2-05). Mocked precompiles are labelled; no Core transfer is observed. The OI-cap unit stays unresolved, so the cap boundary is quoted as the measured raw aggregate.

## Ledger

| Id | Title | Invariant | Actor | Affected | Severity | Status |
|---|---|---|---|---|---|---|
| SQ-L2-01 | Tested settled sequences conserve value; a debt open temporarily removes its margin from the listed claims | A3 | unprivileged user, keeper | both | info | confirmed_simulation |
| SQ-L2-02 | The claimed repeatable debt-cycle mint came from omitted queue pointers in the replay fixture | A3 | auditor (fixture correction, no attacker) | both | none | disproved |
| SQ-L2-03 | The Exchange side bucket is an earmark of the spendable LP bankroll, not a claim, so the repo's conservation identity double counts it whenever it is nonzero | A3 | auditor (identity correction, no attacker) | both | medium | confirmed_live |
| SQ-L2-04 | Every other sequence is neutral: five same-quote cycles, a win, a loss, a liquidation, harvests, both sides of one market, dust and boundary sizes, close then withdraw, and a two-close BatchExecutor batch all reconcile exactly, and each blocked path names its guard | A3, A4, A6, A7 | unprivileged user, keeper, relayer | both | none | disproved |
| SQ-L2-05 | pushStakerFees (the LP-surplus distribution) is unreachable from a stranger, the keeper and the owner in this replay: raw 0x538ccdfd on set 2 and 0x64cd1788 pinned, while an unknown selector reverts with empty data | A3 | stranger, keeper, owner (all attempted) | both | info | blocked |
