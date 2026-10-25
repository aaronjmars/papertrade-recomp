# Additional Tokenomics fixed-revert selector at block 48,902,346

The live Tokenomics implementation dispatches `0x7c7df7b4`. Its original function name and full argument types are unknown. Bytecode requires at least 224 bytes of ABI arguments, or seven 32-byte words after the selector. It validates an address at offset `0x04`, a `uint64` at offset `0x64`, and a `uint8` at offset `0x84`, then always reverts with four-byte selector `0x32aa90b0`. The other four words are not read on this path. The selector tool inferred only five arguments, so its argument list is incomplete.

The [behavior ledger](tokenomics_seven_word_stub_behavior.json) checks the dispatcher, decoder, and revert instructions against the pinned implementation runtime. The function and address decoder contain no storage reads, writes, logs, or external calls. A [port-free local replay](../../artifacts/fixed_revert_local/replay.json) passed two canonical seven-word calls through the exact pinned proxy and implementation bytecode with the EIP-1967 implementation slot set locally. There is no saved archived pinned probe for this selector.

This fixed revert applies to the pinned runtime. A later upgrade could change the behavior. The error's original name is unknown.
