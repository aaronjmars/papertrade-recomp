# Exchange selector 0xfb9f1009 at block 48,902,346

The live Exchange implementation dispatches selector `0xfb9f1009` with one canonical `uint32` argument. `unpauseMarket(uint32)` occurs in the Guardian report and hashes exactly to this selector. The report source snapshot has not been matched to the live bytecode. The pinned bytecode does not read the caller or storage and does not call another contract on this path.

For a nonpayable call with at least one canonical ABI word, the dispatcher enters the function at program counter 1273, checks the calldata length, calls the `uint32` decoder at program counter 16073, then returns to program counter 1299 and reverts with the four-byte selector `0xd9d193d3`. There is no success branch after the decoder. The error's source name is unknown.

```solidity
// Behavioral pseudocode for the live runtime, not recovered source.
function unpauseMarket(uint32) external {
    revert UnknownError_0xd9d193d3();
}
```

The [probe record](../../artifacts/exchange_disabled_selector/pinned_probes.json) includes the runtime hash, exact function and decoder byte slices, a full opcode path for one case, path hashes for five more cases, and call outputs. Owner calls with arguments 0, 1, and `2^32 - 1`, plus an outsider call with 0, follow the same path and return the same error. Short calldata and a noncanonical `uint32` revert without error data. All six calls were read-only simulations at the pinned block. A separate [port-free local replay](../../artifacts/fixed_revert_local/replay.json) passed two canonical calls through the exact pinned Exchange proxy and implementation bytecode. The runtime byte slices and opcode paths support the broader conclusion for any canonical `uint32` value and caller in this deployed implementation.

This proves the behavior of the pinned live bytecode only. It does not establish the intended feature or behavior after an upgrade.

Reproduce the archive capture with `PAPERTRADE_ARCHIVE_RPC` set and `python3 scripts/atlas_exchange_disabled_selector.py --capture`. Run `python3 scripts/atlas_exchange_disabled_selector.py` to verify the saved record offline.
