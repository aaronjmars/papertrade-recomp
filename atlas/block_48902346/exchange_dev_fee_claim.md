# Exchange developer fee claim

The [behavior map](exchange_dev_fee_claim_behavior.json) matches `claimDevFees()` (`0x88f2aea5`), `DevFeesClaimed(address,uint256,uint256)`, and `NotDevFeeRecipient()` to their exact selector or topic hashes. The [saved claim transaction](../../artifacts/historical/0x08ef99988867832607e4d50d8eab4b08651b1f89664eeb5fa2ddab89b23761e3.receipt.json) and [seven read-only pinned probes](../../artifacts/exchange_dev_fee_claim/pinned_claim_probes.json) support these observed paths.

```text
claimDevFees():
    require msg.sender == devFeeRecipient, else NotDevFeeRecipient()
    amount = devFeeAccumulator
    if amount == 0:
        return
    devFeeAccumulator = 0
    totalBalances += amount
    balances[devFeeRecipient] += amount
    emit DevFeesClaimed(devFeeRecipient, amount, amount)
```

In the saved transaction at block 48,901,667, the configured recipient claimed `114890275671617164291236` internal units. The high 128 bits of slot 26 fell by that amount to zero while the low 128-bit staker accumulator stayed fixed. The low 128-bit `totalBalances` field in slot 22 and the recipient's mapping-9 balance rose by the same amount. The event indexed the recipient and contained the amount in both unindexed words. The saved call tree contains the proxy delegatecall and no external token transfer.

At the pinned block, the recipient succeeds; the owner and an unrelated address both revert with `NotDevFeeRecipient()` (`0x2d016ae6`). A read-only override reducing the developer fee to zero returns without logs or storage changes. A one-unit override credits one unit and emits two one-unit event words. Changing the recipient address in a read-only override lets the new address claim and makes the old recipient fail. These tests support the pseudocode for sampled states; the source parameter names of the two equal event words and unusual integer boundaries remain open.
