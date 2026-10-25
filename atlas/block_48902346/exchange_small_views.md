# Exchange excess and small views

The [behavior ledger](exchange_small_views_behavior.json) verifies six Exchange views at pinned HyperEVM block 48,902,346 and five controlled state overrides. The [raw calls and traces](../../artifacts/exchange_small_views/pinned_calls.json) preserve each output and the nested call path.

| Selector | Verified behavior | Pinned output |
|---|---|---:|
| `0x18715c9a` | Calls Tokenomics `0xae745703`, returning `max(trackedLpUsd - rewardCapUsd, 0)` | 968649731559005181671 |
| `0x6d60ae8e` | Returns the literal `10^9` | 1000000000 |
| `0xaf210ecc` | Returns the literal `25` | 25 |
| `0xc43fbc8c` | Returns the low byte of Exchange slot 4 | 8 |
| `0xfdfd905d` | Returns the literal `10^18` | 1000000000000000000 |
| `0xff3bc415` | Returns the literal `64` | 64 |

The Exchange `0x18715c9a` trace contains one static call to the Tokenomics proxy with selector `0xae745703`, the already verified `stakerLpDistributableExcessUsd()` getter. Three Tokenomics storage overrides produce 400, 0, and 0 from tracked and cap pairs `(1000,600)`, `(1000,1000)`, and `(600,1000)`. [Guardian's Papertrade audit](https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/) uses the name `stakerLpExcessToDistribute()`, which hashes exactly to `0x18715c9a`. The report's audited source commit has not been matched to this runtime, so the name is supported by the hash, report context, and observed forwarding path rather than a source build match.

Two slot-4 overrides preserve unrelated high bits while changing the low byte, and the getter returns precisely that byte. The Guardian report names the slot-4 low-byte getter `coreCollateralDecimals()` (`0xc43fbc8c`), an exact selector-hash match. Its source snapshot has not been matched to the live bytecode. Pinned opcode traces show that the four literal getters read no application storage. Their source names and economic labels remain unresolved as well. The separate [direct-withdrawal replay](exchange_direct_withdrawal.md) resolves the nonpayable selector `0x7f99545a` and corrects its initially missed `uint256` argument.

Run `python3 scripts/atlas_exchange_small_views.py` from the workbench root to verify the saved evidence offline. With `PAPERTRADE_ARCHIVE_RPC` set, pass `--capture` to recapture the read-only pinned calls and overrides.
