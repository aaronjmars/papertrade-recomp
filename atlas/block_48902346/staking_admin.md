# Staking owner and executor controls

The [behavior ledger](staking_admin_behavior.json) verifies two successful historical Staking admin transactions and four [read-only pinned probes](../../artifacts/staking/pinned_admin_probes.json). The names `setAuthorizedExecutor(address)` and `transferOwnership(address)` hash exactly to the live selectors `0xd188c049` and `0xf2fde38b`.

The original owner called each setter once. `setAuthorizedExecutor` changed only the low 160 bits of proxy slot 16 from zero to the BatchExecutor address and emitted `AuthorizedExecutorUpdated(address)` with the new address indexed. `transferOwnership` changed only the low 160 bits of slot 15 to the current timelock and emitted `OwnerUpdated(address)` with that address indexed. The upper bits of each slot were preserved.

Pinned simulations from an unrelated caller revert with raw `0x30cd7471` for both functions. Simulations from the current owner setting either address to zero succeed, change the corresponding slot's low 160 bits to zero, and emit the matching indexed update event. These simulations sent no transaction; the live owner and executor at the pin were nonzero.

The error name `NotOwner()` hashes to `0x30cd7471`, but these checks do not cover subsequent behavior after a zero owner or executor is set. The original Solidity source is unavailable.
