# Signed withdrawal nonce history

At HyperEVM block 48,902,346, the saved signed-withdrawal corpus contains 103 successful calls in 35 transactions. The signature ledger identifies each user and nonce from the calldata and matches the nested `consumeNonce(address,uint256,uint64)` call.

For each call, `atlas_withdrawal_nonce_history.py` computes the SessionKeyManager bitmap slot as `keccak256(abi.encode(nonce >> 8, keccak256(abi.encode(user, uint256(6)))))`. The bit is `nonce & 255`. It reads the deployed proxy's raw storage at the block before the withdrawal, at the end of the withdrawal block, and at the pinned block. The pinned block hash is checked first. The 103 triples require 308 distinct archive storage reads because one lookup is shared.

All 103 bits were unset before their transaction block, set at the end of that block, and still set at the pin. This includes the 99 calls whose saved call traces lack transaction storage diffs. The [machine-readable ledger](withdrawal_nonce_history.json) retains every address, nonce, slot, bit, block, and raw word. Run `python3 scripts/atlas_withdrawal_nonce_history.py` to verify it offline. To recapture, provide `PAPERTRADE_ARCHIVE_RPC` and run `python3 scripts/atlas_withdrawal_nonce_history.py --capture`.

These are block-level observations. They do not isolate a transaction index within a block, test failed withdrawals, cover the full withdrawal history, or establish HyperCore delivery. The sampled calls have matching on-chain withdrawal events in the [withdrawal trace corpus](exchange_withdrawal_trace_corpus.json).
