# Exchange recovery controls at block 48,902,346

The [local replay](../../scripts/audit_sweep_recovery_local.py) runs the exact pinned Exchange proxy and implementation runtimes. Its [result](../../artifacts/audit_sweep_recovery_local/replay.json) and [behavior ledger](exchange_sweep_recovery_behavior.json) check the owner recovery path against both stalled users' saved pending words. The replay seeds the pinned `collateralScale()` value of `10^12` at slot 3. Owner, treasury, total-balance, and user-balance words are constructed test state; no HyperCore transfer is simulated.

| Call | Exact-runtime result |
|---|---|
| Owner `clearPendingSweep(address)` with the first stalled user | Selector `0x2362f4de` is absent from the implementation dispatcher and its runtime bytes. The low-level call reverts with empty data; pending storage and logs are unchanged. |
| Owner `reconcileSweepCredit(address,uint256)` with either saved pending word | Reverts with `0x28ef4314`, which hash-matches `SweepAlreadyPending()`. The tested pending word and accounting fields remain unchanged. |
| Owner reconciliation after a direct simulated storage clear | Succeeds for input `50,050,916` six-decimal units, adds `50.050916 * 10^18` internal units to the user balance, treasury, and packed total-balance low word, and emits the reconciliation event. The high packed word is unchanged. The clear was a test override, not an available owner call. |
| Unrelated caller reconciliation with pending | Reverts with hash-checked `NotOwner()` (`0x30cd7471`); pending storage and user balance remain unchanged. |

The [Guardian report](../../artifacts/guardian_papertrade_report.html) describes `clearPendingSweep` plus `reconcileSweepCredit` as an owner recovery process. The common `clearPendingSweep(address)` signature is not present in the pinned deployment. All 13 cataloged state-changing Exchange selectors with one address argument have other identified behavior. A different multi-argument recovery call has not been ruled out. The archive-backed [sweep branch probes](exchange_sweep_pseudocode.md) show that a failed send followed by an unchanged Core balance clears and immediately re-requests the sweep, leaving a pending word.

These checks establish that the named owner reconciliation call cannot credit either live pending case as pinned. They do not establish that governance could not upgrade the Exchange, that no other contract or HyperCore account action could recover the assets, or that the team did not act after the pin. An internal credit alone would not move the USDC still held by the deposit proxies.
