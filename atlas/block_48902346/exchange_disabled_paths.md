# Three fixed-revert Exchange selectors at block 48,902,346

The live Exchange implementation dispatches selectors `0x1afd17e9`, `0x63ca348f`, and `0x58d3ec6a`. The Guardian report uses `openPosition(uint32,bool,uint128,uint32)`, `openPosition(uint32,bool,uint128,uint32,bool)`, and `close(uint256[])`; each signature hashes exactly to its respective selector and matches the recovered ABI shape. The report source snapshot has not been matched to the live bytecode, so these are report-backed names rather than verified original source. For canonical, nonpayable calls, all three functions validate the ABI words and then revert with the four-byte selector `0x58f03bf7`. No storage, log, or external-call instruction occurs on any path. The error's original name is unknown.

```text
openPosition(uint32, bool, uint128, uint32):
    validate ABI
    revert 0x58f03bf7

openPosition(uint32, bool, uint128, uint32, bool):
    validate ABI
    revert 0x58f03bf7

close(uint256[] memory):
    validate ABI array offset, length, and bounds
    revert 0x58f03bf7
```

The [behavior ledger](exchange_disabled_paths_behavior.json) records the runtime hash and dispatch, decoder, and revert offsets. Run `python3 scripts/atlas_exchange_disabled_paths.py` to check those instructions against the pinned runtime. Invalid ABI words and nonzero `msg.value` take generic empty-data revert paths. No archived dynamic probe was captured. A separate [port-free local replay](../../artifacts/fixed_revert_local/replay.json) passed six canonical calls through the exact pinned Exchange proxy and implementation bytecode. A later implementation upgrade could change it.
