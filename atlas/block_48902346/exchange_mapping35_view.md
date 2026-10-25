# Exchange four-field mapping getter at block 48,902,346

Selector `0xc8372577(uint32)` is a read-only getter over mapping base slot 35. The pinned call with key 1 reads `keccak256(abi.encode(uint32(1), uint256(35)))` and its saved return prefix is zero. Its original Solidity name and the economic meaning of the fields are unknown.

The pinned runtime enters at program counter `0x172d`. After decoding a canonical `uint32`, it reads one storage word and returns 128 bytes. The bytecode extracts these fields:

```text
word = storage[keccak256(abi.encode(key, uint256(35)))]
return (
    (word & 0xff) != 0,
    uint64(word >> 8),
    uint64(word >> 72),
    uint64(word >> 136)
)
```

The first return is a boolean; the next three are 64-bit values. The saved generic getter probe kept only the first 63 return bytes, so the full four-word return is established by the deployed opcode sequence. Nine saved transaction prestates read key 0 as zero. None of the 132 saved state-write transactions changes mapping keys 0 or 1. These samples do not show which function writes this mapping or whether other keys have values.

The [behavior ledger](exchange_mapping35_view_behavior.json) checks the runtime hash, instruction offsets, storage slot derivation, saved probe, and sampled writes. Run `python3 scripts/atlas_exchange_mapping35_view.py` to verify it offline.
