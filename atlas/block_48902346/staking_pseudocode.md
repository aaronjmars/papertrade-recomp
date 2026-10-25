# Staking observed behavior at block 48,902,346

The [staking ledger](staking_behavior.json) verifies 45 successful signed calls in 14 historical transactions. It checks calldata, EIP-712 digests, recovered signers, events, token calls, nonce storage, and transaction storage changes. Five distribution transaction prestates and three pinned getter samples provide separate checks. This is reconstructed behavior, not original Solidity source.

The historical Staking proxy deployment delegated selector `0x9ccae24e` with five addresses: Exchange, PAPER, reward token `0x6b9e773128f453f5c2c60935ee2de2cbc5390a24`, original owner `0xa1763a5ff94ebddd417cccb906622ec762ab2e29`, and a zero authorized executor. Its receipt emitted matching `OwnerUpdated` and `AuthorizedExecutorUpdated` events. The [archived creation state diff](deployment_state_diffs.md) also verifies its created proxy code, implementation and admin slots, and all eight application slot writes. This establishes that initializer's deployment path and argument order; its exact source name remains unknown.

## Interface and signature checks

| Selector | Hash-verified signature | Sampled calls |
|---|---|---:|
| `0x83115825` | `stakeBySig(address,uint256,uint256,uint64,uint8,bytes32,bytes32)` | 12 |
| `0xfa2871b5` | `unstakeBySig(address,uint256,uint256,uint64,uint8,bytes32,bytes32)` | 2 |
| `0x9c96d4a1` | `claimBySig(address,uint256,uint64,uint8,bytes32,bytes32)` | 26 |
| `0xf0355460` | `distributeBySig(address,uint256,uint64,uint8,bytes32,bytes32)` | 4 |

The respective type strings are `Stake(address user,uint256 amount,uint256 nonce,uint64 deadline)`, `Unstake(address user,uint256 amount,uint256 nonce,uint64 deadline)`, `Claim(address user,uint256 nonce,uint64 deadline)`, and `Distribute(address user,uint256 nonce,uint64 deadline)`. Their hashes equal the four on-chain typehash getters, including the newly named `DISTRIBUTE_TYPEHASH()`. All 44 EIP-712 digests reproduce the input sent to the EVM signature recovery precompile, and every recovered signer equals the calldata user. Each successful call came from the authorized BatchExecutor.

Every signed call emits `NonceUsed(address,uint256,uint256)` with indexed user and supplied nonce. The third event field is the resulting per-user counter. It is at least `nonce + 1` and agrees with counter slot 12 whenever that slot changes. A separate nested bitmap at base slot 14 marks `nonce & 255` in word `nonce >> 8`; all 44 sampled bits were unset before and set after their transactions. The hash-checked getters `nonceBitmapWord(address,uint256)` and `isNonceUsed(address,uint256)` agree with raw pinned bitmap storage for three sampled users. Both signatures are linked in the selector catalog. The [getter map](staking_getters.md) additionally checks 20 exact names, direct slots, nonzero user mappings, typehash constants, and an unnamed packed flag.

## Storage and token effects

| Proxy slot | Observed meaning |
|---|---|
| 1 | EIP-712 domain separator |
| 2 to 4 | Exchange, PAPER stake token, reward token addresses |
| 5 | `totalStaked` |
| 6 | `accRewardPerShare` |
| 7 | `rewardReserve` |
| 8 | `unallocatedRewards` |
| 9 to 12 | User mappings: staked balance, reward debt, pending rewards, nonce counter |
| 14 | Nested user and word nonce bitmap |
| 15 and 16 | Owner and packed authorized executor / initialization state |

`stakeBySig` emits `Staked(user, amount)`, calls PAPER `transferFrom(user, staking, amount)`, and increases the user's slot-9 balance and slot-5 total by that amount. `unstakeBySig` emits `Unstaked(user, amount)`, calls PAPER `transfer(user, amount)`, and decreases those balances. All 14 sampled token transfers, events, and transaction storage deltas agree.

`claimBySig` emits `Claimed(user, amount)`, returns that amount, and calls Exchange selector `0xe53e3de6(user, amount)`. Its transaction reduces slot-7 `rewardReserve` by the claimed amount. The [Exchange credit ledger](exchange_staking_credit.md) verifies the downstream balance transfer under the hash-checked `creditStakingReward(address,uint256)` name.

The sampled user accounting follows this calculation, with integer division rounded down:

```text
earned = floor(stakedBalance * accRewardPerShare / 10^27) - rewardDebt
pendingReward(user) = pendingRewards + earned

on stake or unstake:
    pendingRewards += earned
    stakedBalance += signed stake change
    rewardDebt = floor(stakedBalance * accRewardPerShare / 10^27)

on claim:
    paid = pendingRewards + earned
    pendingRewards = 0
    rewardDebt = floor(stakedBalance * accRewardPerShare / 10^27)
    rewardReserve -= paid
```

Replaying this against all 14 archived transaction prestates matches 171 final staking storage fields and all 26 claim outputs. Three independent pinned `pendingReward` getters match the same equation using raw storage words.

`distributeBySig` calls Exchange selector `0x7b9f5264`, then reads Tokenomics tracked-LP excess. Four sampled calls with positive excess also call Tokenomics to adjust it. A fifth saved call reads zero excess and makes no Tokenomics adjustment; its reward increase comes from the Exchange fee path. Its four-word `Distributed` event has word 0 equal to the resulting reward reserve and word 3 equal to the resulting `accRewardPerShare`. In all five sampled calls, words 1 and 2 are equal, and word 1 equals the reserve increase. The archived transaction prestates confirm `accRewardPerShareIncrease = floor(word2 * 10^27 / totalStakedBefore)` in all five cases. `unallocatedRewards` was zero in those historical samples. A [read-only replay with a positive slot-8 override](staking_unallocated_behavior.json) starts from a first-in-block transaction whose 88 calls and 28 logs replay exactly. Its isolated Staking distribution also matches the saved 13-call path and five logs. Injecting `10^18` into slot 8 changes no nested call or other contract's storage writes. Event word 1 (new rewards) and reward reserve slot 7 stay fixed; event word 2 rises by exactly `10^18`, reward-per-share slot 6 rises by `floor(10^18 * 10^27 / totalStakedBefore)`, and slot 8 is cleared. Two more read-only overrides set `totalStaked` to zero, first with no prior unallocated balance and then with `10^18` already in slot 8. Both keep event word 2 at zero and leave the accumulator unchanged. Slot 8 ends at `newRewards` in the first case and `newRewards + 10^18` in the second; the reserve still rises by the current rewards. This supports the sampled branches:

```text
newRewards = rewards received from the current Exchange path
rewardReserve += newRewards
if totalStaked == 0:
    unallocatedRewards += newRewards
    allocated = 0
else:
    allocated = newRewards + unallocatedRewards
    unallocatedRewards = 0
    accRewardPerShare += floor(allocated * 10^27 / totalStaked)
emit Distributed(rewardReserve, newRewards, allocated, accRewardPerShare)
```

The nonzero slot-8 and zero-staker states were synthetic; no historical successful distribution with either state was sampled.

## Direct entrypoints and limits

The [direct-entrypoint stub ledger](staking_direct_stubs_behavior.json) proves from the pinned runtime dispatcher that selectors `0xa694fc3a` and `0x2e17de78` share a minimum one-word calldata guard and fixed-revert body; `0x4e71d92d` and `0xe4fc6b6d` share a selector-only minimum guard and another fixed-revert body. Both bodies build `0xa15ce1ba` from a shifted constant, then revert without storage reads, writes, logs, or external calls. Seven pinned read-only probes return this selector, including calls from a funded staker; one historical direct `0x4e71d92d` call did too. Eight more canonical calls passed through exact pinned proxy and implementation code in a local Forge EVM. Short calldata and nonzero value take generic empty-data revert branches. `claim()` and `distribute()` have exact Guardian report name and selector-hash matches; `stake(uint256)` and `unstake(uint256)` remain hash-matching name candidates, and the custom error name is unresolved.

The [admin control ledger](staking_admin.md) verifies the historical owner and executor setters, their slot writes, and four pinned access and zero-address probes. The [Exchange reward credit ledger](exchange_staking_credit.md) separately checks 27 nested `creditStakingReward(address,uint256)` calls and their balance transfers. All seven observed staking event signatures are hash-verified, including `AuthorizedExecutorUpdated(address)`. The two initializer variants now have narrow exact-runtime local probes in the [remaining initialization map](remaining_initializers.md). The two- and five-address initializer source names, the packed-state getter name, uncommon nonce and signature rejection branches, and further Exchange settlement branches remain unresolved. The three-address `initialize(address,address,address)` name is report-backed and hash-matched. Its [pinned bytecode body](legacy_initializer_stubs.md) is a fixed revert for canonical, zero-value calls; the report source snapshot has not been matched to the live bytecode.
