# Three archived proxy creation state diffs

The [checked behavior ledger](deployment_state_diffs_behavior.json) joins the saved deployment call trace, receipt, and archive `prestateTracer` state diff for Staking, PAPER, and SessionKeyManager. In each transaction, the created proxy is absent from the prestate; its poststate code hashes to the exact shared proxy runtime captured at block 48,902,346. Its EIP-1967 implementation and admin slots match the manifest, and every application storage slot written at creation matches the delegated initializer calldata and existing behavior map.

| Created proxy | Application slots written | Checked initializer effect |
|---|---:|---|
| Staking | 8 | Initialization and domain words; Exchange, PAPER, reward token, owner, and zero executor with its packed flag. |
| PAPER | 5 | Initialization flag, short-string encoded `Paper` and `PAPER`, owner, and Tokenomics minter. |
| SessionKeyManager | 4 | Initialization flag, EIP-712 domain separator, owner, and authorized Exchange caller. |

Each receipt has two initializer events. The [call graph](observed_call_graph.json) now includes the three `CREATE` roots and their implementation delegatecalls. The [state-write catalog](state_write_catalog.json) includes all three transactions and lists EIP-1967 control slots separately from application storage. Creation input prefixes are recorded as initcode, not function selectors.

Reproduce offline with `python3 scripts/atlas_callgraph.py`, `python3 scripts/atlas_state_writes.py`, and `python3 scripts/atlas_deployment_state_diffs.py`. The raw receipt, call trace, and state diff paths and state-diff hashes are recorded in the behavior ledger.
