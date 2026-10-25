# Legacy initializer-shaped fixed reverts at block 48,902,346

The exact pinned implementation bytecode proves three initializer-shaped entries have no success path for canonical, zero-value calldata. Each dispatcher enters a body that checks value and calldata length, decodes only canonical address words, and then reverts with four bytes `0xb7b2509c`. The bodies and decoder helpers have no storage read, storage write, external call, event, or return instruction. The [machine-checked byte ranges](legacy_initializer_stubs_behavior.json) include each dispatcher, body, and address decoder, with pinned runtime hashes.

| Implementation | Selector | Decoded input | Existing execution check |
|---|---|---|---|
| Staking | `0xc0c53b8b` | Three addresses | Fresh user, fresh proxy admin, and initialized-state local calls return the same error. |
| BatchExecutor | `0xc0c53b8b` | Three addresses | Archived initialized and fresh-state local calls return the same error. |
| DepositProxyFactory | `0xc4d66de8` | One address | Pinned read-only call returns the same error. |

The public signature preimages `initialize(address,address,address)` and `initialize(address)` are report-backed or candidate names, but the exact original source declarations are not proved. An earlier [initializer map](remaining_initializers.md) left the Staking three-address success branch open after testing only selected states. The bytecode proof closes that branch for well-formed calls at the pin. Malformed calldata or nonzero value can take generic empty-data revert paths instead.

Reproduce offline with `python3 scripts/atlas_legacy_initializer_stubs.py`; the script verifies the runtime hashes, dispatcher targets, exact opcode bytes, effect-free decoder and body ranges, and error construction.
