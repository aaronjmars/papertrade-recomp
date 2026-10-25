# ProxyAdmin and shared proxy control paths at block 48,902,346

The deployed ProxyAdmin at `0xe79c91cc682f1bb401a9cab74c900470190f0f8f` is owned by the timelock. A historical `transferOwnership(address)` transaction moved its slot-0 owner from the deployer to that timelock, emitted `OwnerUpdated(address)`, and matches its archived state diff. The [behavior ledger](proxy_admin_behavior.json) records that transaction and ten port-free [local replay tests](../../artifacts/proxy_admin_local/replay.json) against exact pinned ProxyAdmin, Exchange proxy, and Exchange implementation runtimes.

```text
owner(): return slot 0 as address

transferOwnership(newOwner):
    require caller == owner
    require newOwner != address(0)
    slot 0 = newOwner
    emit OwnerUpdated(newOwner)

upgrade(proxy, newImplementation):
    require caller == owner
    call proxy.upgradeTo(newImplementation)

upgradeAndCall(proxy, newImplementation, data):
    require caller == owner
    call proxy.upgradeToAndCall(newImplementation, data)

changeProxyAdmin(proxy, newAdmin):
    require caller == owner
    call proxy.changeAdmin(newAdmin)
```

Local calls from an outsider to all four owner-only setters reverted with hash-checked `NotOwner()` (`0x30cd7471`). Zero ownership reverted with `InvalidOwner()` (`0x49e27cff`). An owner upgrade changed the Exchange proxy's EIP-1967 implementation slot. `upgradeAndCall` changed that slot and delegated the supplied setup call, which wrote to proxy storage. `changeProxyAdmin` changed its EIP-1967 admin slot. These tests used a mock new implementation and synthetic calls; they were not historical upgrades. The saved historical trace sample contains no upgrade transaction.

The owner-only `upgrade(address,address)` path also accepted a new implementation address with no code in the local pinned-runtime replay. That can leave the proxy pointing at an address that cannot provide the intended functions until an admin corrects it. No unprivileged upgrade path was observed.

## Upgrade-history limit

All eight EIP-1967 proxies share the same 925-byte runtime. Its executable instructions contain no LOG opcode. The local upgrade, upgrade-and-call, and admin-change paths emitted no proxy event. The [upgrade-history ledger](upgrade_history.json) correctly records zero `Upgraded(address)` logs and matching implementation slots at creation and at the pin. The saved direct ProxyAdmin transaction pages contain only its creation and the historical owner transfer. Four saved timelock logs contain no execution event. That additional evidence makes a successful intermediate upgrade less likely, but the completeness of those external histories is not independently proven here. Zero `Upgraded` logs alone cannot rule out an intermediate upgrade followed by a return to the original implementation or a same-target upgrade.

Five function signatures and `OwnerUpdated(address)` hash-match the observed selectors and topic. Their original Solidity identifiers are not verified. The behavior map does not cover payable value forwarding, invalid proxy targets, or every possible setup-call failure.
