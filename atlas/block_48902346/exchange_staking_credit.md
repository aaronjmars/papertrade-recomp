# Exchange staking reward credit

At pinned HyperEVM block 48,902,346, the live Exchange implementation exposes `creditStakingReward(address,uint256)` at selector `0xe53e3de6`. The name hashes exactly to the selector and appears in the Guardian audit report. This is a behavior reconstruction from live bytecode and calls, not recovered Solidity source. [Machine ledger](exchange_staking_credit_behavior.json) and [pinned probe results](../../artifacts/exchange_staking_credit/pinned_probes.json) hold the checks.

```text
creditStakingReward(user, amount):
    require msg.sender == stakerFeeRecipient  // Exchange slot 31, Staking proxy at pin
    if amount == 0: return
    require balances[msg.sender] >= amount     // mapping base 9
    balances[msg.sender] -= amount
    balances[user] += amount
    emit StakingRewardCredited(user, amount)
```

Seven saved transactions contain 27 successful nested calls from the Staking proxy. Every call delegates to the pinned Exchange implementation. The ordered `(user, amount)` arguments equal the 27 `StakingRewardCredited(address,uint256)` logs. In every transaction, Staking's Exchange balance falls by the sum of credited amounts. Each recipient's Exchange balance rises by its credited total. One batch also withdraws from the same recipient, and its observed net change equals reward credit minus the independently checked signed withdrawal debit.

Four read-only `debug_traceCall` probes at the pin verify a one-unit transfer, a zero-amount no-op with no event or Exchange storage write, an outsider revert with raw selector `0x538ccdfd`, and an overdraw revert with raw selector `0xf4d678b8`. The successful one-unit probe emits one event and changes exactly the Staking and recipient mapping-9 balance slots. No transaction was sent for these probes.

The raw revert selectors are observed here, but their original custom-error names are not established by these checks. Other integer boundaries and changes to the authorized Staking address remain untested.
