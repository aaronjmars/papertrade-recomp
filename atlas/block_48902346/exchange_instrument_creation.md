# Exchange instrument registration at block 48,902,346

Selector `0xc88bbcf3` is an instrument registration path. Its exact Solidity name and declared argument types remain unresolved. Two saved successful calls at blocks 47,855,385 and 47,855,387 passed nine static ABI words and returned IDs 0 and 1. Their receipts, call traces, and state diffs verify both increments of the low 32 bits of slot 8, the three instrument words at mapping base slot 7, the two market words at mapping base slot 36, and `InstrumentAdded(uint32,uint32)` logs. The second transaction is `0xa527dea1cef73784e42ba989c8763f103fce30432b25c423921cb8f04d3d71c5`; its [saved call trace](../../artifacts/historical/0xa527dea1cef73784e42ba989c8763f103fce30432b25c423921cb8f04d3d71c5.calls.json) and [state diff](../../artifacts/historical/0xa527dea1cef73784e42ba989c8763f103fce30432b25c423921cb8f04d3d71c5.state_diff.json) confirm the earlier pinned-word inference. The pinned `instrumentCount()` getter returns two.

For either saved successful call, let `id` be its returned instrument ID and `a0` through `a8` its input words. The [behavior ledger](exchange_instrument_creation_behavior.json) verifies these storage values:

```text
instruments[id].word0 = a0 | (a1 << 96) | (a2 << 192) | (a3 << 224)
instruments[id].word1 = a4 | (a5 << 120) | (a6 << 184)
instruments[id].word2 = a7
marketFields[id].word0 = a8 << 192
marketFields[id].word1 = 2^256 - 1
instrumentCount = id + 1
return id
```

The two historical logs contain `(indexed ID, unindexed value)` pairs `(0,0)` and `(1,1)`. The [exact-runtime local replay](../../artifacts/exchange_instrument_creation_local/replay.json) separates these values: with a fresh ID 0 and `a2 = 7`, it emits `(0,7)`. The unindexed field is input word 2. The runtime dispatches to program counter `0x14ee` and calls the shared owner-check helper at `0x4a53`; a local outsider call reverts with hash-matched `NotOwner()` (`0x30cd7471`).

Readable pseudocode for the saved path:

```text
selector_0xc88bbcf3(a0, ..., a8):
    require caller == owner
    require a0, a3, a4, a7 != 0  // tested zero cases revert 0xb0cb274d
    require a8 != 0               // tested zero case reverts 0x924d25e6
    validate remaining inputs     // other boundaries not fully reconstructed
    id = instrumentCount
    instrumentCount = id + 1
    instruments[id] = packed fields above
    marketFields[id] = initialized words above
    emit InstrumentAdded(id, a2)
    return id
```

The local replay runs eight assertion-bearing tests: two sequential historical inputs, a divergent event-field input, owner rejection, zero-input checks, and sampled high-bit boundaries. Zero is accepted in words 1, 2, 5, and 6. The tested high bits at positions 96, 96, 32, 32, 120, 64, 72, and 64 for words 0, 1, 2, 3, 4, 5, 6, and 8 revert with empty data. Word 7 accepts bit 127 and rejects bit 128 with empty revert data. An outsider supplying the sampled overflowing values gets `NotOwner()` for words 0 through 7, while an overflow in word 8 returns empty data before the owner check. These are observed boundaries and check-order results, not proof of the original ABI type spellings. Field meanings, exact source name, narrower acceptance limits, and other rejection branches remain open. Run `python3 scripts/atlas_exchange_instrument_creation.py` for saved historical evidence and `python3 scripts/atlas_exchange_instrument_creation_local.py` for local replay.
