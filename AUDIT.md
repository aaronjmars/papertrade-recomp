# Papertrade HyperEVM Scoped Security Audit Workpaper

**Status:** Scoped audit with corrections from the [23 October 2026 risk review](RISK_REVIEW_2026-10-23.md). The review distinguishes current observations, saved simulations, and unresolved claims.
**Consolidated Audit Ledger:** 92 machine-checked rows across 8 workstreams in [live2_findings.json](atlas/block_48902346/live2_findings.json) and [live2_audit.md](atlas/block_48902346/live2_audit.md).  
**Verification:** 100% offline reproducible via `python3 scripts/atlas_verify.py` without external RPC secrets.

---

## 1. Executive Summary & Audit Verdict

This workpaper documents a bytecode-level security audit of Papertrade on HyperEVM (Chain 999). Papertrade operates a perpetual and spot exchange on HyperEVM, backed by custody and clearing on HyperCore. Because no verified Solidity source code is published, all findings, storage layouts, execution models, and invariants were reverse-engineered directly from deployed bytecode, historical transaction traces, exact-runtime Foundry replays, and live public state reads.

### 1.1 The High-Level Verdict

- **Current outsider drain:** None established in the checked contract paths. The earlier high `SQ-L2-02` debt-cycle claim was disproved when the replay's missing queue pointers were restored. Its quoted gain and claims excess must not be used as loss estimates.
- **Confirmed user-funds problem:** Two deposit proxies still held 62.150916 USDC on HyperCore at block 49,318,549, with pending requests and zero Exchange credit. No recovery has been observed; irreversibility is not proven.
- **Operational and economic risks:** An outer batch can succeed while an inner action fails. A mismatched Exchange and SessionKeyManager pair can block closes in simulation, though the current pair was matched at block 49,318,444. Large wins can exhaust available LP cash and defer the rest into the payout queue; this is a liquidity mechanism, not a demonstrated accounting mint.
- **Older suites:** Their large internal balance books have very little Core USDC behind them, but whether those units represent real redeemable claims remains unresolved. Their 1-of-2 multisigs create a separate governance trust risk. Do not count the face-value book difference as a proven loss.
- **Scope:** This conclusion is based on sampled settlement checks and exact-runtime replays, not a complete security certification. [The four-area review](RISK_REVIEW_2026-10-23.md) gives the evidence and remaining limits.

---

## 2. Pinned Scope & Target Architecture

The audit covers two contract generations deployed by the canonical deployer:
1. **Pinned Baseline (Block 48,902,346):** Pinned at 2026-10-18 21:02:21 UTC (hash `0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab`). 25 captured addresses in the newest connected suite, plus 38 older direct creations and 38 older user proxies.
2. **Post-Refresh Contract Set 2 (Block 49,265,286 & Head):** Executed on 2026-10-20/21 via a 6-call governance batch. Updated implementations: Exchange `0x0a44049d...`, SessionKeyManager `0x04b5ea4c...`, Tokenomics `0x7c0a72a7...`, linked library `0x583d0bd8...`, and added `BuilderRegistry` `0xfdc65504...`.

```
HyperCore Custody (spotClearinghouseState)
      ▲
      │ (CoreWriter spotTransfer / perp transfers)
      ▼
Deposit Proxies (22,586) ──[sweep]──► Exchange Proxy (0x6cd56616...)
                                         │  ▲ (staticcall 0xd95208cd)
                                         ▼  │
                          SessionKeyManager Proxy (0x8326eb88...)
                                         ▲
                                         │ (settlement & fee accounting)
                                         ▼
                             Tokenomics Proxy (0x75174549...)
                                         │
                                         ▼
                              Staking Proxy (0xaad6c7b0...)
```

### Deployed Contract Roles & Addresses

| Role | Proxy Address | Pinned Implementation | Set 2 Implementation |
|---|---|---|---|
| Exchange | `0x6cd5661646289fb6e65ea5c032310fded797d0a2` | `0x0f3febfc94876b0c895f7acecdc8f5c863b549ee` | `0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723` |
| SessionKeyManager | `0x8326eb8896e358717f10502ec73ce8d28e37b108` | `0x8a5069fe303e8f81e91825436e956d595032e558` | `0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946` |
| Tokenomics | `0x75174549dbbd44497d31a47e2e2d7406408d63d9` | `0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f` | `0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03` |
| Linked Library | Direct delegatecall | `0xcd617f984158a4f5d287ddee0e8eb0fed204916d` | `0x583d0bd818c991c5830fea93aef04e474b272459` |
| BatchExecutor | `0x233ff29b239abc1d7748605da9b205c3e008626e` | `0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262` | Unchanged |
| PriceOracle | `0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e` | `0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a` | Unchanged |
| Staking | `0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016` | `0xe6e3519455170913c5c3bfe541dd918a2d0cbb15` | Unchanged |
| PAPER Token | `0xe40f17915daa230324030003a197cdaef2261c0e` | `0x433bd418ec92818a960585f4d5fae563e735bb4a` | Unchanged |
| Deposit Factory | `0x1629b7d46bef6e13ff754174fc9f32dea309b38f` | `0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0` | Unchanged |
| Multisig | `0x696292762fd5ac3677a45edbe54eaece4194d1f6` | 2-of-3 signers (Epoch-tracked) | Unchanged |
| Timelock | `0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f` | Minimum delay 604,800 s (7 days) | Unchanged |
| BuilderRegistry | `0xfdc6550436dd75ce8a0b145f935b7d3a64f53248` | Not deployed at pin | Deployed in Set 2 |

---

## 3. Core Accounting Architecture & The Corrected Invariant

### 3.1 The True Conservation Identity
Internal solvency requires that the Exchange's treasury word strictly equals all liabilities to users, fee accumulators, queued obligations, and LP equity:

$$\text{treasury} = \text{totalBalances} + \text{totalLockedMargin} + \text{totalQueued} + \text{stakerFee} + \text{devFee} + \text{trackedLpUsd}$$

- **Exchange Slot 14:** `treasury()` (`0x61d027b3`)
- **Exchange Slot 22 (low 128):** `totalBalances()` (`0xa69a2ad1`)
- **Exchange Slot 22 (high 128):** `totalLockedMargin()` (`0x01ad056f`)
- **Exchange Slot 18:** `totalQueued()` (`0x53ac4b66`)
- **Exchange Slot 26 (low 128):** `stakerFeeAccumulator()` (`0xafdf6702`)
- **Exchange Slot 26 (high 128):** `devFeeAccumulator()` (`0x7d004aeb`)
- **Tokenomics Slot 3:** `trackedLpUsd()` (`0x8cf554a7`, signed int256)

### 3.2 The Side-Bucket Double-Count Correction (`SQ-L2-03`)
In earlier analysis, the side bucket (Exchange slot 27, getter `sideBucket()` `0x9274682e`) was summed as an additive claim. **This audit proved that formula wrong.**  
Live reads at block 48,173,889 prove that slot 27 held `400296219202209635129` while $\text{treasury} - \text{reserved} = 400296219202209635129 = \text{trackedLp} + \text{totalQueued}$. The side bucket is an **earmark** of the spendable LP bankroll that the queue harvest is authorized to draw upon, not a distinct liability. Summing it double-counted the bankroll whenever nonzero. The pinned baseline only balanced because slot 27 happened to read zero at the pin block.

### 3.3 Saved current-suite accounting snapshot

The saved batched read at block 49,308,072 reconciles treasury with ordinary balances, locked margin, queued claims, fee reserves, and tracked LP to a zero residual. Later batched reads also returned zero. HyperCore and EVM reads are not cryptographically pinned to one common state in this workpaper, and sequential public-RPC reads can straddle blocks. The observed book equality supports the sampled accounting model; it is not a whole-protocol solvency proof.

---

## 4. Comprehensive Findings Matrix (92 Rows Consolidated)

The 92 audit rows consolidate into 5 High, 15 Medium, 16 Low, 28 Informational, and 28 None (16 explicitly disproved negatives).

### 4.1 Corrected false positive

#### `SQ-L2-02`: Previous debt-cycle claim withdrawn

- **Severity:** None | **Status:** `disproved` | **Affected:** Pinned and set-2 replays.
- **Correction:** The saved transaction read-set omitted the queue head and next-id pointers in Exchange slots 16 and 17. The old replay defaulted both to zero, creating an incoherent queue and a false payout result. With the pinned pointer values restored, the debt open consumes queued credit, the same-quote close restores it, harvest pays the existing queue once, and another debt open fails. The earlier 3,237.31 USDC gain and 20,000 USDC claims excess are invalid fixture results. See [corrected sequence evidence](atlas/block_48902346/live2_sequences.md).

### 4.2 Remaining High Findings

#### `RL-05`: Pause Market as an LP-Funded Insider Exit Option
- **Severity:** High | **Status:** `confirmed_simulation` | **Affected:** Pinned and Live bytecodes
- **Actor:** Pause Guardian (2-of-3 multisig signers) acting with an affiliated trading account.
- **Root Cause:** Calling `pauseMarket(uint32)` stores an unvalidated raw BBO from HyperCore precompile `0x080e`. While new opens revert with `MarketIsPaused()`, existing positions are permitted to close against the frozen quote with no oracle read. If the market is paused when the raw book is crossed or zero, a pre-existing short position settles at a zero exit price, paying out $\text{margin} \times \text{leverage}$ directly from the LP bankroll.
- **Blast Radius:** Because per-side caps bound notional rather than payout (`PR-LP-05`), an insider can extract the entire spendable LP bankroll into their balance, deferring any excess into the queue as an unfunded claim.

#### `OL-07` & `OL-08`: Older Exchange Suites Unbacked on HyperCore
- **Severity:** High | **Status:** `confirmed_live` | **Affected:** Earlier 1 and Earlier 2 Suites
- **Actor:** Any user with a positive balance in Earlier 1 or Earlier 2 Exchange contracts.
- **Root Cause:** The earlier deployed Exchange contracts maintain independent accounting ledgers and separate HyperCore clearinghouse accounts:
  - **Earlier 1 (`0x1b534e...`):** Holds **0.156176 USDC** on Core against **84,448,601.52 internal units** (total historical ledger: 803,211.10 USDC in, 803,210.94 USDC out across 27 delivered withdrawals).
  - **Earlier 2 (`0x2ede04...`):** Holds **0.003269 USDC** on Core against **640,390,624.35 internal units** (total historical ledger: 10,400.10 USDC in, 10,399.10 USDC out across 6 delivered withdrawals). Upgraded to Set 2 implementation without funding.
- **Impact:** The saved withdrawal path debits the EVM balance before a later Core transfer, and current Core cash is tiny relative to the books. A present-day withdrawal could fail to deliver, but no current failed withdrawal or real-user loss from these balances has been established.
- **Open Qualification:** Whether the 84M and 640M units represent real user deposits or synthetic pre-launch accounting is unresolved; Earlier 2's book is about 61,000 times larger than all USDC that entered its Core account.

#### `PR-LP-02`: Irreversible Quote Freezing via `pauseMarket`
- **Severity:** High | **Status:** `confirmed_simulation` | **Affected:** Both implementations
- **Root Cause:** `pauseMarket(uint32)` records raw `getBBO` words into mapping 35. The contract's `unpauseMarket(uint32)` function reverts in all circumstances in both the pinned and live implementations. An exhaustive brute-force sweep of all 3,255 dispatcher-caller-argument combinations confirmed that no other function clears mapping 35. Once paused, an instrument can never be unpaused, permanently locking position exits at the frozen price.

#### `IN-L2-D5-02`: Two Uncredited PT-01 Deposit Sweeps
- **Severity:** High | **Status:** `confirmed_simulation` | **Affected:** Both implementations
- **Root Cause:** Confirmed live instance of Guardian KV-09. Two user deposit proxies hold 62.150916 USDC stalled since block 48,902,346 due to HyperCore transfer gas rejections. In both pinned and live implementations, owner reconciliation (`reconcileSweepCredit`) reverts on both pending words, and `clearPendingSweep(address)` is absent from the dispatcher. The funds remain uncredited in the observed state. The set-2 code has a reduced-send retry path, but delivery and recovery for these two proxies have not been observed.

---

### 4.3 Key Medium Findings

| ID | Title | Scope | Actor | Mechanism & Impact |
|---|---|---|---|---|
| `RL-02` | Market Keeper Uncapped Open Limits | Both | Market Keeper (Slot 37) | `0x628a9fd6` and `0x82f47a3f` allow the keeper to set per-side open caps and slot-28 parameters to `uint128.max` without timelock. Opens previously rejected with `OiCapExceeded()` (`0x40f92143`) succeed immediately. |
| `OL-10` | Single-Signer Governance Takeover on Older Suites | Both Older | 1 Signer | Earlier 1 and Earlier 2 multisigs are 1-of-2. A single signer key can invoke `replaceSigner` to replace both signers, then execute timelock calls (60 s delay) to seize ProxyAdmin and contract ownership. |
| `OL-03` | Unfunded Older Library Debt Close | Earlier 1 | User | In the older linked library, a debt-flagged close queues margin plus full profit with the bankroll forced to zero and zero fee. Harvest pays it in full once funded. |
| `AU-L2A-15` / `IN-L2-D1-07` | Cross-Proxy Implementation Coupling | Set 2 | Deployer / Upgrader | Set 2 Exchange calls SessionKeyManager entry `0xd95208cd` on every close. The pinned SessionKeyManager reverts on this call. Upgrading one proxy without the other halts all trading. |
| `PR-LP-01` | Absence of Oracle Validation & Freshness Gates | Both | Market / Relayer | Exchange consumes raw precompile midpoint without freshness checks, deviation limits, or lookback windows. Crossed and zero books are accepted by raw `getBBO`. |
| `PR-LP-05` | Per-Side Cap Restricts Notional, Not Payout | Both | Trader | Per-side caps enforce $\text{size} \le \text{cap}$, but payout is $\text{margin} + \text{PnL}$. A winning position with high leverage can realize payouts far exceeding the cap, draining the entire LP bankroll into queue claims. |
| `IN-L2-D4-01` | Outsider Sweep Driving | Both | Stranger | Anyone can call `sweep(address)` on any user proxy, forcing an immediate queue of the entire balance with no EVM funding route into the proxy. |
| `IN-L2-D4-02` | Set 2 Retry Clears Dust Sweeps | Set 2 | Relayer / User | Set 2 sweep retry reserves 1 USD and clears dust requests instead of reverting, altering sweep finalization semantics. |
| `AU-L2A-12` | Staged 3rd SessionKeyManager Implementation | Both | Timelock | A third SessionKeyManager implementation is currently staged in the timelock queue. Implementation replacement emits no log event. |
| `AU-L2A-16` | Asymmetric Sweep Semantics in Mixed Pairs | Both | Deployer | Deploying mismatched proxy-implementation pairs silently alters deposit sweep success conditions. |

---

### 4.4 Ruled-Out Attack Vectors (16 Disproved Rows)

To ensure audit honesty, paths that were actively targeted for exploitation and proved secure are cataloged:

1. **No Cross-Suite Intent Replay (`PX-L2P-05`, `PX-L2P-06`):** All three suites (Newest, Earlier 1, Earlier 2) construct distinct EIP-712 domain separators bound to their own Exchange proxy address. A historical withdrawal signature recovered under the other domains produces invalid signers.
2. **No Proxy or Factory Redirection (`PX-L2P-01`, `PX-L2P-02`, `PX-L2P-03`, `PX-L2P-04`):** All 22,586 factory deployments re-derived. The CREATE2 salt (`keccak256(user)`), recorded user, and bytecode word are cryptographically bound; no attacker can deploy a proxy that credits to their address.
3. **No Builder Fee Theft or Skimming (`RL-04`):** Five fee-paying close shapes (standard close, alternate position ID, appended 8th word, registry-approved address, loss close) each charged real fees while showing **zero reads or writes to slot 39, zero BuilderRegistry calls, and an unchanged slot-38 counter**. The builder fee skimming lead (`A10`) is conclusively disproved.
4. **No Relayer Exploitation (`RL-03`):** Relayers cannot duplicate intents (`InvalidNonce`), re-target intents (`SessionKeyNotAuthorized`), or modify prices (in-block ordering leaves execution prices identical).
5. **Authorized Keeper Strict Containment (`RL-01`):** The authorized keeper can only flip a single opaque byte in slot 8; it has zero access to fees, pauses, intents, or liquidations.
6. **No Cross-User Balance Theft in Older Suites (`OL-09`):** Cross-user balance modification functions are strictly gated by `NotOwner()` (`0x30cd7471`) or caller scoping.
7. **Queue Credit Conservation (`OS-L2-05`, `OS-L2-06`):** Multi-node queue credit cannot be double-spent; counters, node amounts, and harvest payouts reconcile exactly.
8. **Neutral Sequence Invariance (`SQ-L2-04`):** Five same-quote cycles, two-stage harvests, solvent and queue-live liquidations, dual-market batch closes, one-wei dust boundary tests, and deadband floor boundaries all conserved value to 0 residual.

---

## 5. Active Leads & Anomalies

### 5.1 Sequential-read residual lead

Earlier sequential public-RPC reads showed cents-level differences during busy batch blocks. Those reads were not atomic, and a later batched same-block read returned a zero accounting residual. No on-chain imbalance is established from the sequential values. A pinned block replay would be needed before promoting this lead.

### 5.2 Queue availability

Three historical `Enqueued` events occurred during a short interval when the LP bankroll read zero. This is the setting in which debt-funded opens can use queued credit. The coherent queue replay above disproves the specific repeatable mint previously attributed to this interval.

### 5.3 Nature of Older Exchange Internal Books (Lead 3)
The discrepancy between HyperCore spot cash (15 cents and 0.3 cents) and internal balances (84.4M and 640.4M units) on Earlier 1 and Earlier 2 remains unresolved:
- Earlier 2 holds 640.4M internal units, but its historical HyperCore ledger recorded a cumulative total of only 10,400.10 USDC inbound since inception.
- This 61,000x ratio strongly indicates that Earlier 2 was used for paper-trading or simulated volume with synthetic balance allocations that were never backed by deposited cash. However, because both suites retain live code and allow withdrawals to be initiated, any user attempt to exit destroys their EVM balance without delivering funds.

---

## 6. Security Invariants & Audit Status Matrix

| ID | Invariant Description | Boundary Contracts | Status | Key Evidence & Findings |
|---|---|---|---|---|
| **A1** | Balance movements require authorization or explicit privileged logic. | Exchange, BatchExecutor, SessionKeyManager | Partial | Direct balance theft was not found in checked paths; the previously claimed debt-cycle mint is disproved. Untested paths remain. |
| **A2** | Nonces strictly prevent replay; failed intents do not consume nonces. | Exchange, SessionKeyManager | Verified | 26 exact-runtime local cases, historical open/close replays, domain separation confirmed. |
| **A3** | Liabilities reconcile across balances, margin, queue, fees, and LP. | Exchange, Tokenomics, Staking | Verified (Corrected) | Conservation identity corrected (`SQ-L2-03`). Live book balances to 0 residual at head. |
| **A4** | Oracle and price gates prevent unauthorized position transitions. | Oracle to Exchange | Compromised | No price freshness/lookback gates (`PR-LP-01`); uncapped keeper setters (`RL-02`); pause freeze (`PR-LP-02`). |
| **A5** | Upgrades and parameters obey established governance controls. | Multisig, Timelock, ProxyAdmin | Vulnerable | Earlier multisigs are 1-of-2 (`OL-10`); proxy implementation coupling (`AU-L2A-15`). |
| **A6** | Core withdrawals debit EVM storage and deliver exact funds to HyperCore. | Exchange to CoreWriter | Sampled | 35 distinct withdrawals verified against public Core ledgers; other events are not individually paired. |
| **A7** | Deposit sweeps deliver funds or preserve recovery routes. | Deposit Proxy to CoreWriter to Exchange | Failed | PT-01 deposits remain uncredited (`IN-L2-D5-02`); older suite book units greatly exceed Core cash, with claim status unresolved. |
| **A8** | Documented protocol parameters match deployed on-chain values. | Docs vs Bytecode Storage | Violated | Documented 1e9 USD open cap overstates live configured caps by 195x to 520x. |
| **A9** | Privileged actions are recoverable; quotes are verified at execution. | Guardian, Oracle, Exchange | Violated | Irreversible pause freeze (`PR-LP-02`); pause used as insider exit option (`RL-05`). |
| **A10** | Builder fees and rebates account for value and respect authorization. | BuilderRegistry, Exchange | Verified Negative | No builder fee credited across any close shape (`RL-04` disproved); rebate is owner-only. |

---

## 7. Historical Replay & Settlement Verification Records

The following offline verification replays are permanently embedded in the test harness:

1. **Invalid Liquidation Prices ([exchange_liquidation_invalid_prices.md](atlas/block_48902346/exchange_liquidation_invalid_prices.md)):** 18 exact-runtime cases on pinned runtimes. 16 invalid-BBO cases revert cleanly with zero committed logs and zero storage mutations.
2. **Signed Intent Nonce Integrity (`audit_signed_intent_failures.py`):** 26 local Forge tests on pinned Exchange and SessionKeyManager runtimes confirm signature rejection, domain binding, and nonce rollback across synthetic and real calldata.
3. **Historical Open & Close Replays:**
   - Transaction `0xbfdbeb1a...` replayed from block 48,902,111 prestate: reproduces signed open with position ID 1,394,063 and all 4 logs. 8 field-tamper mutations reject cleanly (`audit_historical_open_tamper.py`).
   - Transaction `0xb1eb49f4...` replayed from block 48,901,631: reproduces 2 signed closes, 1 signed withdrawal, and 1 staking call matching all 17 receipt logs and 26 storage words.
4. **Stratified Withdrawal Settlement (`audit_withdrawal_settlement_stratified.py`):** 32 distinct signed withdrawals linked directly to HyperCore `userNonFundingLedgerUpdates`. 16 new-account withdrawals confirm the exact 1 USDC Core transfer fee; 16 existing-account withdrawals confirm 0 fee.
5. **Stratified Deposit Settlement (`audit_sweep_settlement.py`):** 32 spot-only sweeps delivering 4,057,995.98 USDC paired with exact CoreWriter actions and matching HyperCore ledger entries.

---

## 8. Reproducibility & Offline Verification Pipeline

All evidence in this workpaper can be independently verified on a clean machine without network access or API credentials.

```sh
# Run the complete integrity verifier (gates all 92 rows, schema, and live identity)
python3 scripts/atlas_verify.py

# Re-verify the live book identity tripwire against saved snapshot
python3 scripts/audit_live2_book_identity.py

# Re-run all pass-two audit workstream assertions from saved artifacts
python3 scripts/audit_live2_pricing.py --from-saved
python3 scripts/audit_live2_payout.py --from-saved
python3 scripts/audit_live2_authority.py --from-saved
python3 scripts/audit_live2_intents.py --from-saved
python3 scripts/audit_live2_roles.py --from-saved
python3 scripts/audit_live2_proxies.py
python3 scripts/audit_live2_sequences.py
python3 scripts/audit_live2_older.py

# Re-run historical settlement verifiers
python3 scripts/audit_withdrawal_settlement_stratified.py
python3 scripts/audit_sweep_settlement.py
python3 scripts/audit_historical_open_replay.py
python3 scripts/audit_historical_close_replay.py
```

---

## 9. Remaining Verification

1. Observe a successful Core delivery and matching Exchange credit, or another recovery outcome, for both stuck deposit proxies.
2. Reconcile more withdrawal events against final Core delivery and determine what happens when a Core send fails after the EVM debit.
3. Check current-set mixed liquidation batches at price boundaries and verify that each inner result is surfaced to users.
4. Verify the staged SessionKeyManager against the current Exchange before any upgrade, and classify the origin and redemption rights of the older internal balances.

The [23 October risk review](RISK_REVIEW_2026-10-23.md) records the four investigations and their evidence tiers. No transaction or governance action was sent for this review.
