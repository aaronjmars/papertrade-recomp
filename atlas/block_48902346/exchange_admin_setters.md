# Exchange owner setters at HyperEVM block 48,902,346

The [behavior map](exchange_admin_setters_behavior.json) verifies seven exact setter-name hashes and seven exact event hashes against the live runtime. Its [raw archive capture](../../artifacts/exchange_admin_setters/pinned_setters.json) records read-only calls from the pinned owner and an outsider. Seven saved historical calls independently match the selector, address argument, indexed event, and transaction-level storage effect.

| Setter | Proxy slot and field | Event |
|---|---|---|
| `setSessionKeyManager(address)` | Slot 29, address in bits 8 through 167 | `SessionKeyManagerUpdated(address)` |
| `changeDevFeeAddress(address)` | Slot 38, low 160 bits | `DevFeeRecipientUpdated(address)` |
| `setPaperTokenomics(address)` | Slot 6, low 160 bits | `PaperTokenomicsUpdated(address)` |
| `setAuthorizedExecutor(address)` | Slot 88, low 160 bits | `AuthorizedExecutorUpdated(address)` |
| `setAuthorizedKeeper(address)` | Slot 89, low 160 bits | `AuthorizedKeeperUpdated(address)` |
| `setProxyFactory(address)` | Slot 30, low 160 bits | `ProxyFactoryUpdated(address)` |
| `transferOwnership(address)` | Slot 0, address in bits 16 through 175 | `OwnerUpdated(address)` |

At the pin, the owner can set each field to another nonzero address. Every call changes only the listed Exchange slot and emits one event with the new address as its indexed field. Seven outsider calls revert with hash-verified `NotOwner()` (`0x30cd7471`) and emit no logs. Seven owner calls with `address(0)` succeed and emit the corresponding event, including `transferOwnership(address)`. The zero-address results are read-only simulations; no ownership renunciation is claimed to have occurred on-chain.

The historical owner was `0xa1763a5ff94ebddd417cccb906622ec762ab2e29`. The seven saved transactions include the transfer to the pinned owner `0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f`. The historical authorized-keeper setter passed zero and emitted its event without a storage change because slot 89 was already zero. The separate [getter map](exchange_direct_getters.md) independently checks the current values for the other six target slots. The effects of changing these pointers on downstream trading, fees, and session signatures remain open.
