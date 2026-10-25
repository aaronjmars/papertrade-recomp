# Historical older Exchange debt-open search

The first older Exchange has a locally tested `useDebt=true` signed-open branch. This [offline verifier](../../scripts/atlas_older_debt_history.py) searches its complete creation-to-pin [event capture](../../artifacts/deployer_scope/older_exchange_0_events.json.gz) for historical opens that could have used queued credit. It maintains an event-visible queue amount per user by adding `Enqueued` amounts and subtracting `Harvested` payments in log order. An open is eligible when that visible amount covers its emitted margin.

| Scope | Count |
|---|---:|
| All first older Exchange `PositionOpened` events | 398,945 |
| Opens with enough event-visible queue credit | 15,689 |
| Distinct transactions containing those opens | 4,611 |
| Eligible opens with an unambiguous signed `useDebt=false` flag | 15,689 |
| Opens with one matching payload | 15,685 |
| Opens with two same-flag matching payloads | 4 |
| Eligible opens matched to `useDebt=true` or conflicting flags | 0 |

Every queried `eth_getTransactionByHash` input is saved in the compressed [archive capture](../../artifacts/deployer_scope/older_debt_history.json.gz). Its transaction hash and block match the saved opening event. All 4,611 outer transactions target the first older BatchExecutor. The verifier finds the `openPositionBySig` selector within each input, checks the user, instrument, side, margin, and leverage against the emitted `PositionOpened` event, and reads the signed `useDebt` boolean from calldata word 5. Four opening events each match two payloads with the same false flag. No event has competing true and false matching payloads.

This is an exhaustive check **within the event-visible eligibility set**, not a claim that all 398,945 opening transaction inputs were fetched. It assumes queued credit can only enter through the observed `Enqueued` path. An unlogged queue-credit path would invalidate that eligibility filter. It also does not prove that all `Harvested` events credited ordinary balances; two historical transactions with three such events have direct storage-diff checks. The constructed `useDebt=true` branch remains a local exact-runtime test, and no historical debt-funded opening was found by this search.

Run `python3 scripts/atlas_older_debt_history.py` to verify the saved event and transaction data offline. To refresh the transaction inputs, set `PAPERTRADE_ARCHIVE_RPC` to an archive HyperEVM endpoint and run `python3 scripts/atlas_older_debt_history.py --capture`.
