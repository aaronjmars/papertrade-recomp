# PriceOracle behavior at block 48,902,346

The [machine-readable map](oracle_behavior.json) combines the pinned proxy runtime, its constructor and owner-transfer receipts, 20 saved trading calls, 20 pinned read-only probes, and 25 local fork replays. The archive-backed local fork replaced HyperCore read precompiles with controlled return data. All 25 controlled call trees match the earlier public-fork capture exactly in the [fork comparison](oracle_fork_comparison.json), and the canonical replay folder uses the archive-backed state. The archive RPC's historical `debug_traceCall` returned read failures for those precompiles even where saved transactions prove a successful read. Local fork cases are labeled simulations.

## Interface and behavior

Seven names reproduce their function selectors exactly. Two other selectors have recovered ABI shape and behavior but unknown exact Solidity names.

```solidity
address owner; // packed into storage slot 0, bits 16..175
bool initialized; // low byte of slot 0

function initialize(address initialOwner) external {
    if (initialized) revert AlreadyInitialized();
    owner = initialOwner;
    initialized = true;
    emit OwnerUpdated(initialOwner);
}

function transferOwnership(address newOwner) external {
    if (msg.sender != owner) revert NotOwner(); // selector 0x30cd7471
    owner = newOwner; // zero address accepted in a pinned read-only probe
    emit OwnerUpdated(newOwner);
}

function getOraclePrice(uint32 asset) external view returns (uint64 price) {
    price = readUint64(0x0000000000000000000000000000000000000807, abi.encode(asset));
    require(price != 0, "Oracle price is zero");
}

function getMarkPrice(uint32 asset) external view returns (uint64 price) {
    price = readUint64(0x0000000000000000000000000000000000000806, abi.encode(asset));
    require(price != 0, "Mark price is zero");
}

function getBBO(uint32 asset) external view returns (uint64 bid, uint64 ask) {
    (bid, ask) = readPair(0x000000000000000000000000000000000000080e, abi.encode(asset));
    // No zero or crossed-book check here.
}

function selector_0xc0182669(uint32 asset) external view returns (uint64 midpoint) {
    (uint64 bid, uint64 ask) = getBBO(asset);
    require(bid != 0 && ask != 0, "BBO unavailable");
    require(ask >= bid, "BBO crossed");
    midpoint = uint64((uint256(bid) + uint256(ask)) / 2);
}

function getPriceSnapshot(uint32 asset) external view returns (uint64[5] memory values) {
    uint64 oracle = getOraclePrice(asset);
    uint64 mark = getMarkPrice(asset);
    (uint64 bid, uint64 ask) = getBBO(asset);
    return [oracle, mark, bid, ask, ask > bid ? ask - bid : 0];
}

function selector_0xa7f06462(uint32[] calldata assets)
    external view returns (uint64[5][] memory snapshots)
{
    for (uint256 i; i < assets.length; ++i) snapshots[i] = getPriceSnapshot(assets[i]);
}
```

This is behavioral pseudocode, not recovered Solidity. The exact return type declarations for the two unnamed selectors remain inferred from ABI output. The `getPriceSnapshot(uint32)` return words are oracle, mark, bid, ask, and the nonnegative spread. A crossed or zero BBO returns a snapshot with spread zero; `getBBO(uint32)` also returns those raw values. The midpoint selector rejects zero and crossed books. The max `uint64` bid and ask pair returns the max value, so midpoint addition has no 64-bit overflow.

The snapshot array selector returns an ABI dynamic array with five words per asset in input order. Empty input returns an empty array. Controlled reads for two assets confirmed the array layout. The precompile addresses and raw return format are consistent with [Hyperliquid's read-precompile documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore).

The 20 original saved `0xc0182669` calls read bid and ask from precompile `0x080e` and return `floor((bid + ask) / 2)` for assets 0 and 1. The [expanded boundary ledger](hypercore_boundary_behavior.json) checks the same equation for 102 saved calls across 61 transactions, 57 instrument-0 and 45 instrument-1 reads, and 37 distinct instrument/midpoint pairs. These are actual historical trading paths, not mock reads. The other price functions have no saved successful call in this atlas, so their success behavior rests on pinned-bytecode execution in the local fork.

The proxy constructor delegatecalled `initialize(address)` with owner `0xa1763a5ff94ebddd417cccb906622ec762ab2e29` and emitted `OwnerUpdated(address)`. A later saved transaction transferred ownership to the timelock `0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f`; its receipt topic and slot-0 poststate agree. Reinitializing the live proxy reverts with `AlreadyInitialized()`. Directly initializing the standalone implementation succeeds in a read-only probe and only affects implementation storage, which is zero at the pinned block.
