# Tokenomics mint-parameter getter aliases at block 48,902,346

Three zero-argument Tokenomics selectors return mint-parameter storage words directly:

| Selector | Pinned proxy slot | Pinned value | Name evidence |
|---|---:|---:|---|
| `0x3886cade` | 5 | `2 * 10^24` | Original name unknown |
| `0xe9ed73e9` | 5 | `2 * 10^24` | `lpFlatThresholdUsd()` hashes to this selector; original name unverified |
| `0xc16017ca` | 6 | `5 * 10^24` | Guardian report `stakerLpRewardCapUsd()` exactly hashes to this selector |

The first two selectors dispatch to the same bytecode entry at PC `0x1f7`, which reads slot 5 and returns its 32-byte value. The third dispatches to PC `0x340`, which reads slot 6 and returns its value. [Archived pinned traces](storage_trace_catalog.json) show those reads and outputs through the Tokenomics proxy. A [port-free local replay](../../artifacts/tokenomics_getter_alias/replay.json) uses the exact pinned proxy and implementation bytecode, sets slots 5 and 6 to `(7, 11)` and then `(17, 29)`, and checks all three getters after each change. All six calls return the expected values.

The [behavior ledger](tokenomics_getter_alias_behavior.json) links the selector, bytecode, trace, and replay evidence. Slot 5 is the mint threshold parameter and slot 6 is the LP excess floor in the recovered Tokenomics behavior map. A future governance update can change their values. The slot-5 alias `0x3886cade` remains unmatched in the signature inventory. The Guardian report source snapshot has not been matched to the live bytecode.
