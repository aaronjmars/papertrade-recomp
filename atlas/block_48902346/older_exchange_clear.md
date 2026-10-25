# Older Exchange pending-sweep clear path

The [exact-runtime verifier](../../scripts/atlas_older_exchange_clear.py) compares four Exchange implementation dispatchers saved at block 48,902,346. The first earlier implementation, `0x557c853e100600e0ee91e0df88fcf4af0097ff89`, has 96 selector branches and dispatches `clearPendingSweep(address)` at selector `0x2362f4de` to PC `0x3825`. The newest implementation, the second earlier set's original implementation, and the second earlier set's pinned replacement do not dispatch that selector. The latter three have the same 98-selector set. The first earlier implementation has four selectors absent from the newest one; the newest has six selectors absent from the first earlier one. These counts compare dispatchers, not full function behavior.

The first earlier Exchange proxy points to that first implementation at the pin. An archive `eth_call` to the proxy as its pinned owner, using the first recorded factory user, reverts with `0x0984a617` because that user's pending word is zero. The same call as an outsider reverts with `0x30cd7471` (`NotOwner()`). The raw [pinned calls](../../artifacts/deployer_scope/older_exchange_clear_pin_calls.json) preserve both requests and responses. The linked proxy exists in the first earlier factory's saved deployment events.

Four port-free Forge tests use the exact pinned earlier proxy and implementation runtime bytes, the pinned owner and factory addresses, a constructed nonzero pending word, and a mocked `factory.proxyOf(user)` response set to the recorded user proxy:

| Case | Exact-runtime result |
|---|---|
| Owner clears a pending word | Succeeds, writes zero to mapping base slot 33, emits one three-topic log with the user and proxy indexed |
| Outsider attempts clear | Reverts `0x30cd7471`; pending word unchanged |
| Owner clears an empty word | Reverts `0x0984a617` |
| Owner clears, then calls `reconcileSweepCredit(address,uint256)` | Both calls succeed; a constructed 50 USDC input adds 50 in 18-decimal internal units to the user balance, treasury, and total balances |

The [replay artifact](../../artifacts/deployer_scope/older_exchange_clear_replay.json) records the runtime hashes, tests, and source hash. This establishes an owner-only clear and accounting reconciliation path in the **first earlier Exchange implementation**. The pending word, user balance, and credit amount in the successful replay are constructed local state. The factory response is mocked. No historical successful clear transaction or Core USDC transfer was verified. The newest Exchange used by PT-01 lacks the clear selector; the older function cannot recover those newest-suite pending sweeps. The presence of this function in an older runtime may explain a recovery description in the Guardian report, but it does not establish which deployed version that report tested.
