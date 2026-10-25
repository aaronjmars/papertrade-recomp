# SessionKeyManager direct getters at HyperEVM block 48,902,346

The [machine-readable map](session_direct_getters_behavior.json) and [saved archive capture](../../artifacts/session_getters/pinned_getters.json) verify five selector-name hashes against the pinned runtime. Their archived outputs agree with proxy storage and saved opcode traces.

| Getter | Storage evidence | Pinned result |
|---|---|---|
| `DOMAIN_SEPARATOR()` | Slot 1 | Stored EIP-712 domain hash |
| `domainSeparatorV4()` | Trace reads slot 3 | Returns the same domain hash as slot 1 |
| `owner()` | Slot 2 | Low 160-bit owner address |
| `authorizedCaller()` | Slot 3 | Low 160-bit Exchange address |
| `authorizedSubmitters(address)` | Mapping base slot 7 | BatchExecutor is true; unrelated address is false |

The BatchExecutor and unrelated-address results each equal raw storage at `keccak256(abi.encode(address, uint256(7)))`. The domain hash also matches the value used to reconstruct ten saved registration signatures. Two read-only overrides separate the getters: replacing slot 1 changes only `DOMAIN_SEPARATOR()`, while clearing the authorized caller in slot 3 changes only `domainSeparatorV4()`. The latter output in both states matches `keccak256(abi.encode(EIP712Domain typehash, keccak256("String"), keccak256("1"), 999, authorizedCaller))`. The cached slot-1 hash and dynamically recomputed value agree at the pin. A read-only prior-block replay of one saved registration succeeds with the original state. Clearing slot 3 in that replay produces `InvalidSignature()` (`0x8baa579f`), while slot 1 remains stored. This shows that the tested signature path depends on the dynamic domain. The effect of a real authorized-caller change and other signed paths remains untested. Two typehash constant selectors have hash-matching public names but were left as candidates because their trade struct preimages have not been independently checked.
