# Shared EIP-1967 proxy runtime at block 48,902,346

All eight named Papertrade suite proxies share the same 925-byte runtime hash. Their EIP-1967 admin slots point to ProxyAdmin at the pin. The [behavior ledger](shared_proxy_behavior.json) checks the four selector hashes, embedded storage-slot constants, and absence of executable LOG instructions. Ten [local tests](../../artifacts/proxy_admin_local/replay.json) run the exact pinned ProxyAdmin and Exchange proxy runtimes with the pinned slots installed. The [fixed-revert replay](../../artifacts/fixed_revert_local/replay.json) also reaches implementation selectors through this proxy runtime.

```text
admin():
    require caller == storage[ADMIN_SLOT]
    return storage[ADMIN_SLOT]

implementation():
    require caller == storage[ADMIN_SLOT]
    return storage[IMPLEMENTATION_SLOT]

changeAdmin(newAdmin):
    require caller == storage[ADMIN_SLOT]
    require newAdmin != address(0)
    storage[ADMIN_SLOT] = newAdmin

upgradeToAndCall(newImplementation, data):
    require caller == storage[ADMIN_SLOT]
    storage[IMPLEMENTATION_SLOT] = newImplementation
    if data is nonempty:
        delegatecall newImplementation with data
        revert if that call fails

other selectors and fallback:
    delegatecall storage[IMPLEMENTATION_SLOT] with original calldata
    return or revert with implementation result
```

Local calls by the current admin read both pinned slots. A non-admin call to each of the four special selectors reverted with hash-checked `NotAdmin()` (`0x7bfa4b9f`). Setting the admin to zero reverted with raw selector `0xe6c4247b`; its original error name is unknown. Admin changes and upgrades produced no log. An empty-data upgrade accepted a target address with no code in a local test. A nonempty upgrade call delegated a mock setup function and wrote to proxy storage.

The same runtime is installed at all eight suite proxy addresses, but their implementation slots differ. The local tests used the Exchange proxy as representative. Successful admin changes and upgrades were simulations, not historical transactions. The [ProxyAdmin map](proxy_admin_pseudocode.md) explains owner checks and why absent `Upgraded` logs alone cannot settle upgrade history.
