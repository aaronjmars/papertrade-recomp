# Public name checks at HyperEVM block 48,902,346

The [gap ledger](public_name_gap_checks.json) records public lookup attempts for the remaining unresolved callable and observed event names. These checks do not assign a name by guesswork.

- The 49 unmatched selector rows represent 45 distinct four-byte values. The [saved OpenChain response](../../artifacts/openchain_unmatched_function_lookup.json) returned no function signature for any of them.
- All four observed unnamed event topics returned no signature in the [saved OpenChain responses](../../artifacts/openchain_unresolved_event_lookup.json).
- The saved [Guardian report HTML](../../artifacts/guardian_papertrade_report.html) contains 524 extracted candidate names. None hashes to those four topics under the eight explicit event argument layouts checked in the gap ledger. Event log words alone cannot distinguish every integer width, and the report source snapshot is not a verified match for the pinned contracts.
- The Exchange instrument-setting event `0x76a31977...` returned no log when the archive provider was queried from block zero through the pin. A control query for the known market-field event returned 29 logs in the last 256 blocks. Both exact `eth_getLogs` requests and responses are saved in the [history query](../../artifacts/exchange_instrument_admin/full_history_event_query.json). An empty log result does not rule out reverted calls.

Run `python3 scripts/atlas_public_name_gaps.py` from the workbench root to rebuild the ledger offline. Set `PAPERTRADE_ARCHIVE_RPC` and pass `--capture-history` only to repeat the two archive queries.
