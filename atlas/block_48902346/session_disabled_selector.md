# SessionKeyManager selector 0x17a1678f at block 48,902,346

The live SessionKeyManager implementation dispatches `0x17a1678f(address,uint64,address)`. The Guardian report names `registerSessionKeyDirect(address,uint64,address)`, which hashes exactly to this selector and matches the recovered ABI shape; its source snapshot has not been matched to the live bytecode. For canonical nonpayable calldata, the deployed bytecode validates all three ABI words, then reverts with raw selector `0xd2dd8531`. It performs no storage read, storage write, log, or external call on this path. The error's source name is also unknown.

```text
registerSessionKeyDirect(address, uint64, address):
    validate ABI
    revert 0xd2dd8531
```

The [behavior ledger](session_disabled_selector_behavior.json) checks the pinned runtime hash, selector dispatch, address decoder, width checks, and fixed revert instruction. Run `python3 scripts/atlas_session_disabled_selector.py` to verify it offline. No archived dynamic probe was captured. A separate [port-free local replay](../../artifacts/fixed_revert_local/replay.json) passed two canonical calls through the exact pinned SessionKeyManager proxy and implementation bytecode. Malformed calldata and nonzero `msg.value` use generic empty-data revert paths.
