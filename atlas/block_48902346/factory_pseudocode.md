# Live DepositProxyFactory behavior at block 48,902,346

The live factory proxy is `0x1629b7d46bef6e13ff754174fc9f32dea309b38f` and delegates to `0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0`. The [behavior ledger](factory_behavior.json) combines its proxy deployment trace, one historical user-proxy creation, pinned storage, and 15 read-only branch probes. The [selector-name checks](factory_selector_names_behavior.json) hash-verify nine names and compare three deployed-user getter sets and a simulated owner transfer against archive storage. The [complete deployment check](factory_event_deployments.json) matches every one of 22,586 `ProxyDeployed` events to an internal CREATE2 record and recomputes its address from the logged user.

## Storage and callable surface

| Selector | Interface or recovered behavior | Evidence |
|---|---|---|
| `0x03b802b6` | `authorizedDeployer()` | Pinned getter reads slot 4 |
| `0x0f71c8bc` | Unnamed `(address,address)` admin-only initialization path | Pinned revert and hypothetical owner-zero read-only probe |
| `0x29710388` | `isProxy(address)` | Pinned getter reads mapping slot 2; deployment writes `true` |
| `0x56e8d85b` | Unnamed `(address,address,address)` constructor initializer | Proxy creation delegatecall with Exchange, initial owner, deployer |
| `0x8da5cb5b` | `owner()` | Pinned getter reads slot 3 |
| `0xc1a9a508` | `proxyOf(address)` | Pinned getter reads mapping slot 1; deployment writes address |
| `0xc4d66de8` | `initialize(address)` has a Guardian report name and exact selector-hash match | [Pinned bytecode](legacy_initializer_stubs.md) proves canonical, zero-value calls always revert with `0xb7b2509c`; source spelling unverified |
| `0xc6f881bc` | `setAuthorizedDeployer(address)` | Owner and outsider probes; slot 4 and event checks |
| `0xcbd433f4` | `deployProxy(address)` | Historical CREATE2 trace; existing, fresh, zero-user, and auth probes |
| `0xd2f7265a` | `exchange()` | Pinned getter decodes slot 0 bits 16 through 175 |
| `0xd600539a` | `computeProxyAddress(address)` | Pinned getter and fresh-user call match CREATE2 computation |
| `0xf2fde38b` | `transferOwnership(address)` | Historical transfer; outsider and zero-owner probes |

Slot 0 packs the Exchange address at bits 16 through 175 and a low-byte initialized flag. Slot 3 holds the owner and slot 4 the authorized deployer. `proxyOf(user)` is mapping base slot 1 and `isProxy(proxy)` is mapping base slot 2. The EIP-1967 implementation and admin slots belong to the proxy, outside this implementation layout.

## Recovered paths

```text
deployProxy(user):
    require caller == owner || caller == authorizedDeployer
    if proxyOf[user] != address(0):
        return proxyOf[user]

    salt = keccak256(abi.encodePacked(user))
    initCode = captured Create2DepositProxy creation code
             ++ abi.encode(exchange, user)
    proxy = CREATE2(value=0, salt, initCode)
    require deployment succeeded
    proxyOf[user] = proxy
    isProxy[proxy] = true
    emit ProxyDeployed(user, proxy)
    return proxy

computeProxyAddress(user):
    return last20(keccak256(0xff ++ factory ++ salt ++ keccak256(initCode)))

setAuthorizedDeployer(next):
    require caller == owner
    authorizedDeployer = next
    emit AuthorizedDeployerUpdated(next)

transferOwnership(next):
    require caller == owner
    require next != address(0)
    owner = next
    emit OwnerUpdated(next)
```

The captured creation transaction calls selector `0x56e8d85b` with `(exchange, initialOwner, authorizedDeployer)`. It stores those values and emits `OwnerUpdated` and `AuthorizedDeployerUpdated`. Repeating it at the live pin reverts with `AlreadyInitialized()` (`0x0dc149f0`). Selector `0x0f71c8bc` is callable only by the proxy admin and only when owner storage is zero. It then writes owner and authorized deployer and emits the same events. At the live pin it reverts because owner is set. Its successful path was exercised only under a read-only owner-zero storage override.

The authorized deployer and owner each successfully create the same deterministic proxy in separate read-only simulations. An outsider gets `0x27fba80a`. A repeat authorized call returns the existing proxy without a CREATE2 call, log, or storage write. The live implementation accepts `address(0)` as a deployment user in simulation. The owner can also set the authorized deployer to zero; the event and cleared slot were observed. An outsider cannot set the deployer or transfer ownership (`NotOwner()`, `0x30cd7471`), and transfer to zero reverts with `0x904bc503`. An outsider also cannot use the admin-only initialization path (`0xc031a0df`). A direct implementation probe with a zero Exchange address reverts with `InvalidExchange()` (`0x40892c33`). All eight factory custom-error selectors from the decompiler candidates have now been exercised in labeled read-only probes.

The three event hashes match `ProxyDeployed(address,address)`, `OwnerUpdated(address)`, and `AuthorizedDeployerUpdated(address)`. Exact source names for the three initializer selectors and several custom errors remain unresolved. The [public Guardian audit report](https://guardian.security/portfolio/papertrade/protocol-review-2026-10-09/) describes a Papertrade source snapshot, but its linked source repository was inaccessible during this run, so it has not been treated as a bytecode match. The 22,586 address checks are exhaustive for recorded deployments through the pin; only 41 deployed runtimes were sampled for code-template uniformity.
