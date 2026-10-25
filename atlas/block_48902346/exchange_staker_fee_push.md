# Exchange fee push to Staking at block 48,902,346

`pushStakerFees()` hashes exactly to Exchange selector `0x7b9f5264`. The [behavior ledger](exchange_staker_fee_push_behavior.json) checks five historical distribution calls and five pinned read-only probes. The function was also called successfully from an unrelated address in a pinned simulation, so this path does not require the caller to be Staking at that state.

The Exchange fee event is `StakerFeesClaimed(address,uint256,uint256)` at topic `0x18d8b795...`. The LP excess event is `StakerLpExcessDistributed(address,uint256,uint256,uint256)` at topic `0x17d88d5c...`. Both signatures hash exactly to their live topics. Staking is the indexed address in both. In the five historical fee events, the two data words equal the fee amount. Four calls also emit an excess event with data `(excess, excess, 0)` and call Tokenomics' excess adjustment. The fifth historical call reads zero excess and emits no excess or Tokenomics adjustment event. In every transaction, the Staking `Distributed` event's reward increase equals fee plus excess.

At the pinned state, the isolated call has these net effects:

```text
fee = 99,505,349,031,080,845,747
excess = 968,649,731,559,005,181,671
stakerFeeAccumulator -= fee
totalBalances += fee + excess
balances[Staking] += fee + excess
Tokenomics.trackedLpUsd -= excess
```

The fee comes from the low 128 bits of Exchange slot 26. Total balances use the low 128 bits of slot 22; `balances[Staking]` is mapping base slot 9. Tokenomics tracks LP in slot 3. A second excess getter inside the successful call returns zero after the adjustment.

Pinned overrides exercise all four fee/excess combinations. With zero excess, only `StakerFeesClaimed` emits. With zero fee, only the LP excess and Tokenomics adjustment events emit. With both zero, there are no logs. The two event names are recovered by exact hashes; their argument names beyond the checked relationships remain uncertain. Historical samples do not cover every possible accounting boundary.
