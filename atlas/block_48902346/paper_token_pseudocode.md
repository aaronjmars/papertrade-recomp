# PAPER token behavior at block 48,902,346

The [token ledger](paper_token_behavior.json) checks the proxy deployment initializer, three historical admin writes, 28 pinned read-only call branches, four pinned mutation traces, and the token paths already observed in Staking and Tokenomics. It identifies all 20 implementation selector preimages. Three slot-5 names came from a [Guardian audit report](https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/) and were checked against the deployed selector and event hashes; the audited source snapshot has not been matched to this runtime. The code below is a behavior model, not original Solidity source.

## Deployment and storage

The proxy's historical creation trace contains a delegatecall to `initialize(string,string,address,address)` with `"Paper"`, `"PAPER"`, original owner `0xa1763a5ff94ebddd417cccb906622ec762ab2e29`, and minter `0x75174549dbbd44497d31a47e2e2d7406408d63d9` (Tokenomics). The token uses 18 decimals. The deployment receipt emitted `OwnerUpdated(address)` and `MinterUpdated(address)` with the same addresses. The [archived creation state diff](deployment_state_diffs.md) verifies the created proxy code, implementation and admin slots, and all five initialized application slots. Historical owner transfer changed the owner to the timelock `0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f` at the pin. A [complete event scan](paper_control_history_behavior.json) from creation through the pin found exactly five PAPER admin events: the two initializer events and these three saved setter or ownership transactions. `MinterUpdated` appears only at deployment. A separate full-range `Transfer` query with zero recipient returned no logs, so there is no observed successful burn event through the pin. The scan does not see reverted calls or hypothetical unlogged writes.

| Proxy storage | Observed meaning |
|---|---|
| Slots 1 and 2 | Token name and symbol strings |
| Slot 3 | Owner |
| Slot 4 | Minter |
| Slot 5 | `autoApprovedSpender` privileged spender address |
| Slot 6 | Total supply |
| Mapping base 7 | Account balances |
| Nested mapping base 8 | Ordinary allowances |
| Slot 9 | Staking contract address used by transfer restrictions |

At the pin, both slot 5 and slot 9 contain Staking `0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016`. The hash-verified `stakingContract()` getter reads slot 9. The hash-verified `autoApprovedSpender()` getter (`0x12bbf044`) reads slot 5. A historical `setAutoApprovedSpender(address)` call (`0xd311b1a9`) by the original owner wrote slot 5 and emitted `AutoApprovedSpenderUpdated(address)` with the new address indexed. `setStakingContract(address)` separately wrote slot 9 and emitted `StakingContractUpdated(address)`. A later `transferOwnership(address)` call wrote slot 3 and emitted `OwnerUpdated(address)`.

The owner's `setMinter(address)` and both staking-address setters succeed in pinned simulations. A separate [read-only mutation trace](../../artifacts/paper_token/pinned_mutation_traces.json) sets the minter to a different address: slot 4 changes to that address and `MinterUpdated` emits its indexed value. A minter-authorized burn of one unit reduces both the holder's balance at mapping base 7 and total supply at slot 6 by one, and emits `Transfer(holder, address(0), 1)`. The same trace set confirms `NotOwner()` for an unrelated setter caller and `InsufficientBalance()` for a burn above the holder balance. An unrelated caller receives `0x30cd7471`. `mint(address,uint256)` and `burn(address,uint256)` succeed from the pinned minter; the owner or a holder receives `0xf8d2906c`. Tokenomics' 25 sampled historical mints have matching PAPER `Transfer` events and supply changes in the [Tokenomics ledger](tokenomics_pseudocode.md). Twelve sampled stakes call PAPER `transferFrom`, and two unstakes call `transfer`, all matching Staking events and amounts in the [Staking ledger](staking_pseudocode.md).

## Transfer gate

The tested paths behave as follows:

```text
allowance(holder, spender):
    if spender == autoApprovedSpender: return 2^256 - 1
    return storedAllowance[holder][spender]

transferFrom(holder, recipient, amount):
    if caller != autoApprovedSpender: require storedAllowance[holder][caller] >= amount
    move(holder, recipient, amount)

move(sender, recipient, amount):
    require caller == slot9
    require sender == slot9 or recipient == slot9
    update balances and emit Transfer
```

This model matches the checked branches. The pinned holder has a positive PAPER balance. Its direct `transfer` reverts with `0xe827105e`, even for amount zero or a Staking recipient. Staking can transfer its own PAPER out, or pull a holder's PAPER into Staking with `transferFrom`. Staking cannot pull that holder's PAPER directly to an unrelated address. An unrelated caller with a simulated maximum ordinary allowance still cannot pull into Staking or elsewhere; it reaches `0xe827105e` after the allowance check. Without that allowance it reverts earlier with `0x13be252b`.

For the pinned holder, `allowance(holder, Staking)` returns `2^256 - 1` while the nested raw allowance slot is zero. A zero allowance override still lets Staking pull into itself. This distinguishes the privileged allowance from a stored approval. An override changing slot 9 to an unrelated address lets that address pull to itself when its ordinary allowance is also set to maximum, while the old Staking address loses its direct transfer path. In two tested calls, setting slot 9 to zero still causes transfer restriction reverts. These are read-only state overrides; no on-chain state changed.

Six custom error names hash to their exercised selectors: `AlreadyInitialized()` (`0x0dc149f0`), `InsufficientAllowance()` (`0x13be252b`), `NotOwner()` (`0x30cd7471`), `TransferRestricted()` (`0xe827105e`), `InsufficientBalance()` (`0xf4d678b8`), and `NotMinter()` (`0xf8d2906c`). Repeat initialization and transfer overdraw were simulated at the pin; the other four errors occur in the role and transfer probes above.

## Remaining uncertainty

The Guardian report names the privileged spender, but its linked source repository was inaccessible and no source-to-runtime bytecode match was established. Its governance description also differs from the pinned three-signer multisig, so the report is a lead for names, not proof that the audited snapshot is the deployed code. The full event scans found no post-deployment `MinterUpdated` or Transfer-to-zero event. The token's `initialize`, `burn`, and `setMinter` selectors have no saved successful historical transaction after deployment; their role checks and the two successful mutation effects were tested by pinned read-only simulations. The observed transfer branches do not prove every zero-address, self-transfer, amount-boundary, or future configuration case. The current owner controls both staking-address slots and the minter role, so changes to those slots can alter who can move PAPER; this is a control capability, not a demonstrated exploit. No verified source was available for the implementation.
