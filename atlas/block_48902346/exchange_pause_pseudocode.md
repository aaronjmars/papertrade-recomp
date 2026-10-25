# Exchange pause controls at block 48,902,346

The [behavior ledger](exchange_pause_behavior.json) verifies six selector hashes against the live Exchange implementation. A saved transaction installed the pinned pause guardian, and thirteen [local tests](../../artifacts/exchange_pause_local/replay.json) exercise the exact pinned Exchange proxy and implementation runtimes. Local state changes are simulations.

```text
owner(): return address(storage[0] >> 16)
pauseGuardian(): return address(storage[1])
tradingPaused(): return bool(storage[29] & 0xff)

setPauseGuardian(newGuardian):
    require caller == owner, NotOwner()
    storage[1] = newGuardian
    emit PauseGuardianUpdated(newGuardian)

setTradingPaused(paused):
    require caller == owner or (paused and caller == pauseGuardian)
    storage[29] = (storage[29] & ~0xff) | uint8(paused)
    emit TradingPausedUpdated(paused)

pauseMarket(id):
    require caller == owner or caller == pauseGuardian
    require id < instrumentCount
    require marketPause[id].flag == 0
    (bid, ask) = oracle.getBBO(instrument[id].oracleAsset)
    marketPause[id] = packed(flag=1, bid, ask, timestamp)
    emit topic 0x25e933a2...(id indexed, bid, ask, timestamp)
```

The historical `setPauseGuardian(address)` call wrote slot 1 from the original owner address to `0x696292762fd5ac3677a45edbe54eaece4194d1f6` and emitted hash-checked `PauseGuardianUpdated(address)`. Local tests show that only the owner changes the guardian, the old guardian loses pause permission, and the new one gains it. The outsider setter reverts with hash-checked `NotOwner()` (`0x30cd7471`).

The pinned `tradingPaused()` getter returns false from the low byte of slot 29. A saved prestate has the SessionKeyManager address in the upper bytes of that word. The local owner can set and clear the low byte while preserving the address. The pause guardian can set it but receives hash-checked `NotPauseAuthority()` (`0x49199fb6`) when trying to clear it. An unrelated caller receives the same raw error. All successful local calls emit `TradingPausedUpdated(bool)` with the expected payload. No historical call to this setter was saved. A [pinned full-history event query](exchange_control_event_history_behavior.json) returned no `TradingPausedUpdated` logs; this does not rule out reverted calls or unlogged writes.

For market ID 0, local owner and guardian calls succeeded with the pinned instrument words and a mock Oracle returning bid `1,000,000,000` and ask `1,100,000,000` for asset 0. The call writes mapping base slot 35, keyed by market ID. Its packed word holds flag in bits 0..7, bid in 8..71, ask in 72..135, and timestamp in 136..199. One local event had the exact topic `0x25e933a27e6487478d7617f2f4ef2f5c77355faf6cad2e6fd7c4b8d029930d9f`, indexed ID 0, and those bid, ask, and timestamp words. Its original event name is unknown. An invalid ID reverted with hash-checked `InvalidInstrumentId()` (`0x67207a88`); a repeated pause reverted with hash-checked `MarketAlreadyPaused()` (`0x0d240815`); an outsider reverted with `NotPauseAuthority()` (`0x49199fb6`).

The named [`unpauseMarket(uint32)` entrypoint](exchange_disabled_selector.md) always reverts in the pinned runtime. Other possible ways to clear a market pause have not been excluded. Mock Oracle prices establish the local branch and storage format, not the actual HyperCore BBO at the pin or downstream trading effects. The market-pause event name and verified Papertrade source remain unresolved. The same full-history query returned no successful market-pause event logs. The two error names match public registry signatures and the exercised branches.
