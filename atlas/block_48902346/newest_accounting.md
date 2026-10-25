# Newest Exchange accounting at the pinned block

This is a pinned internal-accounting reconciliation at HyperEVM block 48,902,346. It does not by itself establish USDC custody or redeemability.

[`atlas_newest_scalar_accounting.py`](../../scripts/atlas_newest_scalar_accounting.py) ties saved raw Exchange slots to the independently captured getter outputs and the Tokenomics `trackedLpUsd()` getter. All captures have the same pinned block hash. The exact 18-decimal identity is:

| Field | Internal USD units |
|---|---:|
| `totalBalances` | 50,566,343.541298993602517829 |
| `totalLockedMargin` | 9,361,610.942219029227606376 |
| Staker fee reserve | 99.505349031080845747 |
| Dev fee reserve | 1,240.216616927083848377 |
| Tokenomics tracked LP | 5,000,968.649731559005181671 |
| **Sum and Exchange treasury** | **64,930,262.85521554** |

The difference is zero at raw integer precision, and `totalQueued` is zero at the pin. This checks aggregate book entries only. The [19-case deposit transition check](spot_settlement_stratified.md) independently verifies that each sampled credit raises a user's balance, `totalBalances`, and treasury by the same amount after Core delivery.

## Full event and account census

[`atlas_newest_event_census.py`](../../scripts/atlas_newest_event_census.py) replays all 4,301,896 Exchange logs from deployment block 47,854,719 through the pin. The saved [index](../../artifacts/newest_account_census/events_index.json) hashes each compressed chunk, covers every block without gaps, and lets CI verify one chunk at a time. Event topics expose 45,182 address-shaped indexed words, including all 22,586 factory users. Adding pinned manifest addresses yields 45,199 candidate accounts.

[`atlas_newest_account_balances.py`](../../scripts/atlas_newest_account_balances.py) checks each candidate's pinned `balances(address)` getter. All 17,910 nonzero getters match their raw slot-9 mapping words. The remaining 27,289 getters are zero. The saved [account capture](../../artifacts/newest_account_census/account_balances.json.gz) also contains independent scalar getters and the raw packed total and margin word.

| Account group | Nonzero accounts | Sum, internal USD units |
|---|---:|---:|
| Factory users | 17,908 | 45,245,922.141312234714584043 |
| Other event or manifest addresses | 2 | 5,320,421.399986758887933786 |
| **All candidate balances** | **17,910** | **50,566,343.541298993602517829** |
| **Exchange `totalBalances()`** | | **50,566,343.541298993602517829** |

The difference is zero at raw integer precision. One of the two non-factory nonzero entries is the newest Staking proxy, with 5,320,421.399986263009764974 internal units. That entry is part of the ordinary-balance total, not an additional asset.

The event replay finds 1,394,595 position opens, 1,275,392 closes, and 115,436 liquidations, leaving 3,767 active positions. Position IDs advance without a gap, and each terminal event removes an open ID with the same user. The remaining opening margins sum to 9,361,610.942219029227606376, exactly matching `totalLockedMargin()` and the high half of raw slot 22. Three queue enqueues and three harvests match by user and amount, totaling 22.871826547055470767 internal units on each side. The pinned `totalQueued()` and raw slot 18 are both zero.

These are checks of the captured Exchange book at one EVM block. Address candidates come from indexed events, the factory, and the manifest, so an unobserved address with a balance is outside the direct getter census. The exact sum leaves no positive omitted balance if `totalBalances` tracks all nonnegative entries correctly. The separate [claim and Core comparison](accounting_claims_and_core_assets.md) now classifies fee, reward, and debt routes and reconstructs a same-second public Core ledger balance; it lists why this still cannot establish whole-protocol solvency or general redeemability. Run `python3 scripts/atlas_newest_account_balances.py` to verify the saved event and balance data offline; `atlas_verify.py` runs the same checks in CI.
