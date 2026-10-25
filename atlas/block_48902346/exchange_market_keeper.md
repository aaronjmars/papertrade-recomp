# Exchange market keeper at block 48,902,346

`setMarketKeeper(address)` is selector `0x060447aa`. The saved successful transaction `0x3b3eab1fccbd0600aa196edc066d57f2d7a64b5c691f8fb9078457fe9199c79a` passed address `0x3721476de31190dc1af8908026abe20efe25cf99`. It wrote that address into the low 160 bits of Exchange slot 37 and emitted one `MarketKeeperUpdated(address)` log with the address indexed. Both names reproduce the deployed function selector and event topic. The pinned `marketKeeper()` getter reads slot 37 and returns the same address.

The live implementation's dispatcher enters the setter at program counter `0x3e0a`. Its address decoder begins at `0x3eb3`; its shared owner check begins at `0x4a53` and compares `msg.sender` against the owner packed in slot 0. A failed check reverts with `NotOwner()` (`0x30cd7471`). After the check, the function preserves the high bits of slot 37, stores the new address in its low 160 bits, emits the indexed event, and stops. The bytecode has no zero-address or equality check on that final path.

```solidity
// Behavioral pseudocode for the pinned live implementation.
function setMarketKeeper(address next) external onlyOwner {
    marketKeeper = next;
    emit MarketKeeperUpdated(next);
}
```

The [behavior ledger](exchange_market_keeper_behavior.json) records the historical call, receipt, state diff, pinned getter, runtime hash, and exact instruction offsets. Run `python3 scripts/atlas_exchange_market_keeper.py` to verify it offline. The successful historical path is directly observed. The owner failure and zero-address behavior are derived from pinned bytecode; no saved dynamic probe covers those branches.
