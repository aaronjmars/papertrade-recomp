# Second earlier Exchange upgrade

The [offline verifier](../../scripts/atlas_older_upgrade.py) checks a compressed [archive capture](../../artifacts/deployer_scope/older_exchange_upgrade.json.gz) of all 16 older EIP-1967 proxy implementation slots at creation, the pinned slots, a bounded historical slot search, the upgrade block, two transactions with receipts and call traces, and the execution's prestate diff.

At creation, the second earlier Exchange proxy `0x2ede04561914c61a5f49212609541934fd7f5901` pointed to `0x6f0e9deab8a4f21344e4c10a35db5027b02a67fa`. At block 48,092,889 it still pointed there. At block **48,092,890**, its slot points to `0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb`, which remains installed at the audit pin. The archive state diff for the only transaction in the transition block has exactly that implementation-slot write for the Exchange. The other 15 older proxies have their original implementation addresses at the pin.

The replacement implementation was deployed at block 48,092,801. SignerOne of the second older one-confirmation multisig submitted a timelock schedule at block 48,092,821, then submitted its execution at block 48,092,890. The schedule event's ready time is 60 seconds after its block timestamp; execution occurred 68 seconds after scheduling. Both events carry operation ID `0xdc41c321578826dc6b576a6fa4061689f63f0457640f799003433a23f85488df`.

The successful execution trace follows this exact call path:

```text
signerOne -> older multisig.submitTransaction(..., true)
          -> older timelock.execute(...)
          -> older ProxyAdmin.upgrade(Exchange, replacement)
          -> Exchange proxy admin upgrade call
          -> EIP-1967 implementation slot changes to 0x93a8...
```

The ProxyAdmin calldata names the Exchange proxy and replacement implementation. The proxy call uses selector `0x4f1ef286`, an empty setup byte string, and emits no proxy log in the saved receipt. The execution diff names the original and replacement words. This establishes a historical governed upgrade, not just a difference between creation and pinned storage.

The 15 unchanged creation-to-pin slots do not rule out upgrades that were later reversed. The bisection and execution trace identify this transition, not every possible past implementation change. The replacement Exchange's own 23,529-byte behavior remains outside the detailed newest-suite audit, and this upgrade does not establish whether any user balance changed or whether the operation was safe for existing state.
