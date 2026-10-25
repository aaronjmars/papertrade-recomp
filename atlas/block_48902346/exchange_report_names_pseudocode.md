# Exchange names recovered from the Guardian report

The [behavior ledger](exchange_report_names_behavior.json) checks names in the [Guardian audit report](https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/) against the live Exchange implementation at block 48,902,346. Each name below has an exact selector hash. The report's source snapshot is inaccessible and has not been matched byte for byte to this runtime.

## Staker fee recipient

Historical transaction `0xb357f09ef042c99d383e702118230d8fde098a78ab433b7a5a06e1b2c6a0bccd` called `setStakerFeeRecipient(address)` (`0xcd2d3811`) from the original owner and set the Staking proxy as recipient. The Exchange proxy delegatecalled the live implementation, wrote proxy storage slot 31, and emitted `StakerFeeRecipientUpdated(address)` (`0xbcd09d92...`) with the recipient as its only indexed field. The pinned `stakerFeeRecipient()` getter (`0xe1f9209b`) reads slot 31 and returns that same address.

```text
observed setStakerFeeRecipient(recipient):
    slot31 = recipient
    emit StakerFeeRecipientUpdated(recipient)

stakerFeeRecipient():
    return slot31
```

The successful owner transaction establishes this path. An unauthorized caller, zero recipient, and later changes have not been tested.

## Available-balance getters

`queueHarvestAvailable()` (`0x138e9de2`) and `lpBankrollAvailable()` (`0x0cdd5fc4`) both return `0x422ff0dc1275e2cfd56e7` at the pin. The former reads direct storage slots 14, 22, and 26; the latter reads 14, 18, 22, and 26. The [pinned override ledger](exchange_availability_behavior.json) distinguishes them in 11 states. `queueHarvestAvailable()` returns `max(treasury - totalBalances - totalLockedMargin - stakerFeeAccumulator - devFeeAccumulator, 0)`; `lpBankrollAvailable()` returns zero whenever `totalQueued > 0`, and otherwise returns that same available amount. Each fee and balance field was changed separately, and both zero and one-unit reserve boundaries were tested. These formulas are strongly supported for the sampled states; they are not a proof of every integer boundary.

## Further exact name leads

`setTradingPaused(bool)` (`0xae69b95b`), `harvest(uint256)` (`0xddc63262`), and `creditStakingReward(address,uint256)` (`0xe53e3de6`) hash to live selectors and appear by name in the audit report. `setTradingPaused(bool)` now has [local control-path evidence](exchange_pause_pseudocode.md). The saved transaction set includes one `harvest` call and 27 `creditStakingReward` calls across seven transactions. The [linked-library harvest reconstruction](exchange_library_harvest.md) checks the historical call and thirteen read-only simulations. The [staking reward credit reconstruction](exchange_staking_credit.md) checks all 27 historical calls against events and balances, plus four pinned read-only branches. Both names are hash-checked and behavior-backed. The original source is unavailable. The report describes a different multisig configuration from the pinned deployment, so matching hashes are useful evidence for names but do not prove source revision identity.
