# Exchange direct storage getters at HyperEVM block 48,902,346

The [machine-readable map](exchange_direct_getters_behavior.json) ties 17 exact selector hashes to the live Exchange runtime. The [saved archive capture](../../artifacts/exchange_direct_getters/pinned_getters.json) records getter outputs and raw proxy storage at the pinned block. `atlas_exchange_direct_getters.py` checks each proposed name against its selector hash, each direct getter against its saved opcode trace and storage word, and `balances(address)` against three independently calculated mapping slots.

| Getter | Storage location | Observed return |
|---|---|---|
| `totalLockedMargin()` / `totalBalances()` | Slot 22 | High / low 128 bits |
| `devFeeAccumulator()` / `stakerFeeAccumulator()` | Slot 26 | High / low 128 bits |
| `sessionKeyManager()` | Slot 29 | Address in bits 8 through 167 |
| `authorizedExecutor()` / `authorizedKeeper()` | Slots 88 / 89 | Low 160 bits |
| `oracle()` / `paperTokenomics()` / `proxyFactory()` / `devFeeRecipient()` | Slots 2 / 6 / 30 / 38 | Low 160 bits |
| `collateralScale()` / `nextPositionId()` / `treasury()` / `queueHead()` / `totalQueued()` | Slots 3 / 11 / 14 / 16 / 18 | Full 256-bit word in tested state |
| `balances(address)` | `keccak256(abi.encode(user, uint256(9)))` | Full sampled mapping value |

Two read-only state overrides confirm that slot 29 packs two independent fields. Setting its low byte to one changes the pause getter to true while `sessionKeyManager()` stays the same. Replacing bits 8 through 167 changes the returned manager to `0x1111111111111111111111111111111111111111` while the pause getter stays false. The three sampled `balances(address)` outputs all equal raw mapping storage, including nonzero values.

The `treasury()` getter returns a numeric accounting amount, as the [historical field transitions](exchange_storage_behavior.md) show. A third-party ABI lists its return type as `address`, so that declaration is unreliable. These names have exact selector hashes and sampled behavior, but the original Solidity source, exact source integer types, and untested future branches are unavailable.
