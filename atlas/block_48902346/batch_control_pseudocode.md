# BatchExecutor control paths at block 48,902,346

The [control ledger](batch_control_behavior.json) checks six selector preimages against the pinned BatchExecutor implementation. Two saved successful transactions independently verify the relayer setter and owner transfer through the proxy. Ten [port-free local tests](../../artifacts/batch_control_local/replay.json) use the exact pinned proxy and implementation runtimes. Fresh initialization states in those tests are synthetic.

```text
exchange(): return address((storage[0] >> 16) & ((1 << 160) - 1))
sessionKeyManager(): return address(storage[1])
paperStaking(): return address(storage[2])
owner(): return address(storage[3])
authorizedRelayers(account): return bool(storage[keccak256(abi.encode(account, 4))])

setAuthorizedRelayer(account, allowed):
    require msg.sender == owner
    storage[keccak256(abi.encode(account, 4))] = allowed
    emit AuthorizedRelayerUpdated(account, allowed)

transferOwnership(newOwner):
    require msg.sender == owner
    storage[3] = newOwner
    emit OwnerUpdated(newOwner)
```

The historical `setAuthorizedRelayer(address,bool)` call enabled one relayer and wrote its mapping word from zero to one. The historical `transferOwnership(address)` call moved slot 3 from the original owner to the timelock. Both receipt events match their exact topic hashes and indexed addresses. Local tests checked relayer enable and disable, outsider rejection with `NotOwner()` (`0x30cd7471`), and that only the new owner can change a relayer after transfer.

An archived transaction prestate contains slot 0 as `0x000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a20001`: the Exchange address occupies bits 16 through 175 and the low byte is `0x01`. The pinned getter returns that Exchange address. Slots 1, 2, and 3 are the SessionKeyManager, PAPER staking, and owner addresses; slot 5's low byte is one in the local pinned-state setup.

Two source-unnamed initialization selectors have distinct checked paths:

- `0x9ccae24e` takes five addresses. With fresh local storage it writes slots 0 through 3, sets slot 5, and enables the fifth address as a relayer. On the archived initialized layout it reverts with hash-matched `AlreadyInitialized()` (`0x0dc149f0`). The fresh-state call succeeded from a non-admin address.
- `0x0f71c8bc` takes owner and relayer addresses. With zero owner and initialization slots, a call from the proxy admin sets owner, initialization status, and relayer, while retaining the first three slots. A non-admin call in that fresh state reverts with raw selector `0xc031a0df`. The initialized state reverts with raw selector `0x3f733c4f`.

Both successful local initializer probes emitted `OwnerUpdated(address)` followed by `AuthorizedRelayerUpdated(address,bool)` with the expected indexed addresses and enabled flag. The exact source names of these two entrypoints and the raw error selectors remain unresolved. The three-address selector `0xc0c53b8b` reverted with raw selector `0xb7b2509c` under both archived initialized and fresh local states. The [pinned bytecode proof](legacy_initializer_stubs.md) shows canonical, zero-value calls cannot succeed through this entry. Its public `initialize(address,address,address)` preimage remains a candidate, not a verified source name. Historical evidence does not establish every zero-address branch or prove the synthetic fresh-state paths were used in deployment.
