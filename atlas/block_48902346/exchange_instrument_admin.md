# Exchange instrument configuration at HyperEVM block 48,902,346

The unnamed Exchange setter `0x5ca4c0ea(uint32,uint128,uint96,uint96,uint64)` changes four fields of an existing instrument. The [probe ledger](exchange_instrument_admin_behavior.json) records nine read-only archive simulations and the raw pinned instrument words. Three calls from the Exchange owner succeed and emit the same event topic. An unrelated caller and the market keeper receive `NotOwner()`. Instrument ID 2, beyond the pinned count of two, receives `InvalidInstrumentId()`.

The successful calls write three words of the `instruments(uint32)` mapping at base slot 7. The field names remain unknown, so the table uses their argument positions.

| Argument | Storage location | `instruments(uint32)` return index |
|---|---|---:|
| First `uint128` | Word 2, low 128 bits | 7 |
| Second `uint96` | Word 0, bits 96..191 | 1 |
| Third `uint96` | Word 0, bits 0..95 | 0 |
| Fourth `uint64` | Word 1, bits 184..247 | 6 |

Every other bit of those words is preserved in all three successful probes. In particular, the maintenance rate at word 1 bits 120..183, used by the [liquidation-price view](exchange_liquidation_price.md), is unchanged. The simulated event has topic `0x76a31977...`, an indexed `uint32` instrument ID, and four unindexed values in setter argument order. Its Solidity name is unknown.

Readable pseudocode for the tested branches:

```text
setUnnamedInstrumentFields(id, first, second, third, fourth):
    require caller == owner, NotOwner()
    require id < instrumentCount, InvalidInstrumentId()
    require first != 0 and third != 0 and fourth < 10^18, error 0xb0cb274d
    instrument[id].word0 = keepHigh64(word0) | (second << 96) | third
    instrument[id].word1 = keepAllButBits184To247(word1) | (fourth << 184)
    instrument[id].word2 = keepHigh128(word2) | first
    emit UnnamedInstrumentEvent(id, first, second, third, fourth)
```

The function and event labels in this pseudocode describe behavior; their deployed Solidity names are unresolved.

A [nine-test local replay](../../artifacts/exchange_instrument_admin_local/replay.json) installs the exact pinned proxy and implementation bytecode. It reproduces the owner write and event, both access-control errors, the invalid ID and three value errors, and two committed updates followed by `instruments(uint32)` returning the second set of values while unrelated fields remain intact. These tests use synthetic local storage seeded from the pinned instrument words.

The first and third values must be nonzero in the tested cases. A fourth value of `10^18 - 1` succeeds, while `10^18` reverts with raw selector `0xb0cb274d`; zero succeeds. The second value can be zero. Both the owner and keeper checks, the invalid ID, and these boundaries are supported by the [raw call traces and storage diffs](../../artifacts/exchange_instrument_admin/pinned_probes.json). No historical setter call or event was present in the saved sample. A separate [full-chain archive log query](../../artifacts/exchange_instrument_admin/full_history_event_query.json) returned zero logs for this event through the pin, while a known Exchange event returned 29 logs in a 256-block control query. This supports the absence of successful historical event emissions at this proxy, but does not rule out reverted calls. The parameter meanings, untested boundary combinations, and effects on later trading are still open.
