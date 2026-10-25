# Exchange keeper-updated market fields at block 48,902,346

The [behavior ledger](exchange_market_fields_behavior.json) reconstructs selector `0x628a9fd6` without assigning an unverified Solidity name. Its three ABI arguments are `uint32 instrumentId, uint128 first, uint128 second`. A separate [signed-open opcode check](exchange_open_limit.md) shows the two values act as long and short opening limits in all 57 saved signer-reached open paths. Their exact source names, units, and other uses remain unknown.

```text
function unknown_628a9fd6(uint32 instrumentId, uint128 first, uint128 second):
    require msg.sender == owner || msg.sender == marketKeeper
        else revert 0x989c4c7c
    require instrumentId < instrumentCount
        else revert 0x67207a88
    fields[instrumentId].word1 = first | (second << 128)
    emit topic 0xa065d6ba... with indexed instrumentId
         and two unindexed words (first, second)
```

The mapping uses base slot 36. Its first word packs two 96-bit fields and one 64-bit field; its second word packs the two 128-bit values above. Selector `0xcb163b03(uint32)` returns `(first96, second96, first128, second128, last64)`. Selector `0xf37d3c4f(uint32)` returns `(first96, second96, last64, first128, second128)`. Pinned raw words for instrument IDs 0 and 1 match both getters. ID 2 returns five zeros. Earlier opcode traces also show both getters reading mapping slot 36 and its next word.

The historical transaction `0x324a3b9eb75351965b220c16095b56b053f91fbda37525202051604fbd618f7d` calls the setter from the market keeper for instrument 0. Its calldata, event words, and changed storage word agree exactly. All 29 recent events in the saved 256-block window came from direct market-keeper transactions, with the same exact calldata-to-event relationship. Sixteen events target instrument 0 and thirteen target instrument 1.

Five pinned read-only calls test the two authorized senders, an outsider, invalid ID 2, and maximum `uint128` values. The owner and keeper calls emit the same event shape and write only the expected mapping word in diff-mode traces. The outsider reverts with `0x989c4c7c`; ID 2 reverts with `0x67207a88`. Both error names and the event signature preimage remain unresolved. These probes do not prove all possible input bounds or future role changes.
