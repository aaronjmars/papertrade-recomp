# Existing older replacement against PT-01 pending state

The second older Exchange already uses replacement implementation `0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb` at the pin. Its observed retry branch reserves 1 USDC. The [cross-set local replay](../../scripts/atlas_pt01_existing_replacement.py) installs those exact runtime bytes behind the newest Exchange proxy through the pinned ProxyAdmin bytecode, then retries each of the two PT-01 pending words. The test also runs the newest original implementation for comparison.

| Pinned proxy Core spot balance | Newest original action 6 send | Older replacement action 6 send | Replacement pending amount | Credit if the reduced send settles and leaves zero or 1 USDC |
|---:|---:|---:|---:|---:|
| 50.050916 USDC | 50.050916 USDC | 49.050916 USDC | 49.050916 USDC | 49.050916 internal USD |
| 12.1 USDC | 12.1 USDC | 11.1 USDC | 11.1 USDC | 11.1 internal USD |

Eight Forge cases pass through the exact newest Exchange proxy, its original implementation or the older replacement, the exact newest ProxyAdmin, and each affected user's fetched deposit proxy runtime. They seed the archived pending words and last-sweep blocks, the pinned factory pointer, and constructed owner/admin and accounting words. Unit slots 3 and 5 are set to their [archived values](exchange_unit_scales_behavior.json), `10^12` and `10^10`. The factory lookup and HyperCore balance precompiles return controlled values equal to the last observed proxy balances. A local CoreWriter recorder receives the actual deposit proxy's action 6 payload, including the newest Exchange destination, token 0, and the amount in the table. The retry updates `pendingSweep` and `lastSweepBlock` accordingly. No Core transfer executes in this test.

Four cases then assume that Core accepts the reduced send and that the proxy's spot USDC is either zero after a 1 USDC fee or 1 USDC after a zero fee in the next EVM block. The two residual values match the [historical older recovery states](older_sweep_retries.md). Under both controlled responses, the replacement emits one `Swept` event for the reduced amount, clears the pending word, and increases the user's internal balance, treasury, and packed total balance by that amount. The CoreWriter call count remains one. This tests the EVM accounting step of a governed recovery route. It does not test Core acceptance, the real residual balance or fee, or an actual upgrade.

This establishes that the deployed older replacement's retry branch can request a 1 USDC-reduced send for both newest pending states **under those controlled inputs**, and that its next-block finalization credits the reduced amount if the assumed Core delivery occurs. It does not establish that the older replacement is safe to install as the newest Exchange implementation. Its other fund, trading, signature, and admin paths are not proven storage-compatible, and it links an older library. The [governance replay](pt01_governance_route.md) establishes how an authorized upgrade could occur, but neither replay proves HyperCore would accept the requested sends or what fee it would charge. The replacement remains installed behind a different Exchange proxy at the pin.

Run `python3 scripts/atlas_pt01_existing_replacement.py` to verify the saved [eight-case result](../../artifacts/pt01_existing_replacement/replay.json) offline. Use `--run` to rebuild the exact-runtime local cases.

## Newest-suite transaction compatibility samples

Two more [exact-runtime local replays](../../scripts/atlas_pt01_replacement_trade_compat.py) and [mixed-transaction replays](../../scripts/atlas_pt01_replacement_mixed_compat.py) start from archived newest-suite transaction prestates. Each test first runs the original newest implementation, then counterfactually points the same Exchange proxy at the already deployed older replacement and installs its pinned linked library. All other captured contract code and storage stay at the historical transaction state. The BBO, account-status, and spot-balance precompiles return the values saved in the original traces.

| Original newest-suite transaction | Batch actions | Replacement matches original receipt logs | Replacement matches original changed storage words |
|---|---|---:|---:|
| `0xbfdbeb1a...e2d0484c`, block 48,902,111 | One successful signed open, one failed batch item | 4 | 11 |
| `0xb1eb49f4...b0b1cd5`, block 48,901,631 | Two signed closes, a signed withdrawal, and staking | 17 | 26 |

The replacement also matches each original transaction's outer call output. The [open ledger](../../artifacts/pt01_replacement_trade_compat/replay.json) and [mixed ledger](../../artifacts/pt01_replacement_mixed_compat/replay.json) pin runtime and generated test-source hashes. `python3 scripts/atlas_pt01_replacement_trade_compat.py --run` and `python3 scripts/atlas_pt01_replacement_mixed_compat.py --run` rerun the Forge cases with local `solc`; default mode verifies the saved evidence offline.

These are two sampled counterfactual transactions, not a deployed upgrade. They increase evidence that the replacement can read and write the newest Exchange's tested trading storage. They do not cover every fund, price, signature, liquidation, or admin branch, and they do not prove Core delivery or a safe production upgrade.

## Pinned getter parity sample

A [saved archive comparison](../../artifacts/pt01_replacement_getter_parity/pinned_calls.json) calls the newest Exchange proxy at block 48,902,346 with its original implementation and with a read-only override of the EIP-1967 implementation slot to the deployed older replacement. An admin-only `implementation()` call from ProxyAdmin returns the original address before the override and the replacement address after it. This control confirms that the archive RPC applied the override. The proxy and both implementation runtimes match the pinned manifest hashes.

All 64 successful read calls across 57 sampled selectors return identical bytes. Inputs include both nonzero PT-01 pending words, a position owner's nonzero internal balance, instruments 0 and 1, position ID 1,394,063, and no-argument accounting and configuration getters. The offline verifier ties the pending words to the separate stalled-sweep capture. The catalog's disabled `unpauseMarket(uint32)` entry is excluded even though it is labeled view.

This is read-only parity at one pinned state for the listed calldata. It does not establish mutation behavior, untested getter inputs, storage compatibility after an upgrade, or Core settlement. Run `python3 scripts/atlas_pt01_replacement_getter_parity.py` to verify the saved calls offline. `--capture` refreshes them with `PAPERTRADE_ARCHIVE_RPC` set to an archive HyperEVM endpoint.
