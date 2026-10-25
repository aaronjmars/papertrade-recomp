# Exchange instrument getter at block 48,902,346

The [getter ledger](exchange_instruments_getter_behavior.json) checks `instruments(uint32)` against the pinned proxy for IDs 0, 1, and 2. The selector hashes to `0xdc8a47ef`. It reads three consecutive storage words starting at `keccak256(abi.encode(instrumentId, 7))` and returns eight 32-byte fields.

| Returned field | Observed extraction |
|---:|---|
| 0 | First word, low 96 bits |
| 1 | First word, bits 96 through 191 |
| 2 | First word, bits 192 through 223 |
| 3 | First word, bits 224 through 255 |
| 4 | Second word, low 120 bits |
| 5 | Second word, bits 120 through 183 |
| 6 | Second word, bits 184 through 255 |
| 7 | Third word, sampled value |

All eight values match the [saved raw storage and call outputs](../../artifacts/exchange_instruments_getter/pinned_getters.json) for both live instruments. ID 2 returned an all-zero tuple at the pin. The archive opcode trace independently records the three mapping reads for ID 1.

These samples do not establish the fields' business names or the declared width of the final field, whose sampled high bits are zero.
