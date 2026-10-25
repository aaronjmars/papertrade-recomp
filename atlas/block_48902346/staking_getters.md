# Staking getter reconstruction

At pinned block 48,902,346, the [getter ledger](staking_getters_behavior.json) checks 20 exact selector hashes against live Staking outputs. It compares ten direct getters with raw proxy storage, four user mappings with nonzero account samples, four EIP-712 typehash constants with their type strings, and two derived getters. [Pinned call and storage data](../../artifacts/staking/pinned_getters.json) makes the checks reproducible offline. One typehash name was already reconstructed in the main Staking ledger, so this adds 19 selector names.

| Getter group | Selectors | Checked behavior |
|---|---|---|
| Direct slots | `authorizedExecutor`, `unallocatedRewards`, `DOMAIN_SEPARATOR`, `stakeToken`, `totalStaked`, `owner`, `accRewardPerShare`, `rewardReserve`, `exchange`, `rewardToken` | Equal the named proxy storage words at slots 1 through 8, 15, and 16; address getters use the low 160 bits |
| User mappings | `stakedBalance`, `rewardDebt`, `pendingRewards`, `nonces` | Equal `keccak256(abi.encode(user, baseSlot))` storage at bases 9 through 12 in twelve nonzero pinned samples |
| Typehash constants | `STAKE_TYPEHASH`, `UNSTAKE_TYPEHASH`, `CLAIM_TYPEHASH`, `DISTRIBUTE_TYPEHASH` | Equal Keccak hashes of the four signed-call type strings |
| Derived | `domainSeparatorV4`, `pendingReward` | The former equals the pinned domain separator; the latter matches the previously checked three-user reward equation |

Selector `0x6090cf16` remains unnamed. It reads byte 20 of slot 16 and returns `true` when that byte is nonzero. Three read-only storage overrides set the byte to 0, 1, and 255 and return false, true, and true. The low 160-bit authorized executor address remains the same in all three probes.

The names are exact selector hashes backed by the observed behavior, but the original Solidity source is unavailable. The domain separator alias was checked only at the pinned chain state, and these getter checks do not establish every arithmetic boundary of `pendingReward`.
