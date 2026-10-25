# Exchange instrument field setter at block 48,902,346

Selector `0xd7c7e5fb` changes two fields of an existing instrument. Ten port-free local tests execute the exact pinned Exchange proxy and implementation bytecode. They use the pinned owner and instrument 0 words, plus a controlled instrument 1 word to distinguish the storage masks. The function and event names are unresolved; no historical call of this selector was saved. A [pinned full-history event query](exchange_control_event_history_behavior.json) returned no matching success logs, though it cannot rule out attempted or unlogged calls.

```text
unknown_0xd7c7e5fb(instrumentId, first, second):
    require caller == owner, NotOwner()
    require instrumentId < instrumentCount, InvalidInstrumentId()
    require first != 0 and second != 0 and second <= 2^120 - 1,
        error 0xb0cb274d
    instrument[instrumentId].word0 =
        (oldWord0 & (2^224 - 1)) | (first << 224)
    instrument[instrumentId].word1 =
        (oldWord1 & ~(2^120 - 1)) | second
    emit topic 0x62db1b2b... with indexed instrumentId
        and two unindexed words (first, second)
```

The mapping base is slot 7. Local owner calls for IDs 0 and 1 returned no data and changed only the two packed fields. The ID 1 test starts with an all-ones second word to prove that bits 120..255 are preserved. The emitted log has the exact topic in the [behavior ledger](exchange_instrument_limit_behavior.json), one indexed `uint32` ID, and two data words matching the inputs. The topic has no defensible Solidity event name.

The outsider and market keeper receive `NotOwner()` (`0x30cd7471`). ID 2, above the pinned count of two, receives `InvalidInstrumentId()` (`0x67207a88`). Zero first or second values and a second value of `2^120` receive raw error `0xb0cb274d`. The maximum `uint32` first value and maximum 120-bit second value succeed separately. These are local simulations, not historical transactions. The exact Solidity type of the third argument and the economic meaning of both fields remain unresolved. The tests do not establish downstream trading behavior after the update.

Run `python3 scripts/atlas_exchange_instrument_limit_local.py` to repeat the ten pinned-runtime tests and refresh the [replay record](../../artifacts/exchange_instrument_limit_local/replay.json).
