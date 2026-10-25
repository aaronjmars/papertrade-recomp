# Invalid BBO liquidation replay at HyperEVM block 48,902,346

The [18-case result](exchange_liquidation_invalid_prices.json) tests the pinned newest Exchange through `liquidate(uint256)` and `liquidateBatch(uint256[])`. The [raw evidence](../../artifacts/exchange_liquidation/invalid_prices.json) contains each mock runtime, request, call tree, storage diff, local transaction receipt, and watched storage words before and after the transaction. The Exchange, Oracle, Tokenomics, and PAPER proxy and implementation runtimes, plus PaperMath, match the nine SHA-256 hashes in the pinned manifest. Both positions are active in the archive-backed fork and their flag words match the earlier independent archive capture.

| Input at HyperCore BBO read | Single liquidation | One-position batch | Mixed two-market batch |
|---|---|---|---|
| No return bytes or precompile revert | `BBO read failed` | `BBO read failed` | `BBO read failed` |
| Zero bid and ask | `BBO unavailable` | `BBO unavailable` | `BBO unavailable` |
| Zero bid or zero ask | `BBO unavailable` | Not sampled | Not sampled |
| Bid above ask | `BBO crossed` | `BBO crossed` | `BBO crossed` |

Two success controls use valid synthetic BBOs: a single market-0 liquidation and a batch that liquidates one eligible position in each of markets 0 and 1. Sixteen invalid cases revert. The mixed cases put a valid, eligible market-0 position before a bad market-1 read, then reverse the request order. In the first order, the call tree shows one Tokenomics settlement call before the second Oracle read fails. In the reverse order, the first Oracle read fails before any settlement call.

Every invalid case has an empty committed receipt log list, an empty contract storage diff, and unchanged watched Exchange words in a snapshotted local transaction. The watched words include both positions, both users' balance slots, treasury, total queued, the packed total balances and locked margin, the liquidation fee rate, and the packed staker and developer fee accumulators. This is evidence that the first settlement in a mixed batch rolls back when a later price read fails. The single and batch calls do not skip an active position with an invalid BBO in these cases.

These are local simulations with controlled HyperCore precompile code. The read-only call traces use the exact pinned block; transaction receipts are from the next local block and are reverted to a snapshot after each case. The mock responses contain no update time, so this check cannot establish whether nonzero but stale HyperCore prices are accepted, or whether HyperCore itself enforces freshness. It also does not cover every position, instrument, later implementation, or live transaction.

Run `python3 scripts/audit_liquidation_invalid_prices.py` to verify the saved cases offline. To recapture, start an archive-backed Anvil fork at block 48,902,346 and run `python3 scripts/audit_liquidation_invalid_prices.py --local-rpc-url http://127.0.0.1:<port>`. The recapture checks the saved runtime bytes and active position words before the probes.
