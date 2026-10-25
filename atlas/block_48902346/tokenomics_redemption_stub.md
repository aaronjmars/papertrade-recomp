# Tokenomics redemption entrypoints at block 48,902,346

The live Tokenomics implementation dispatches `0xfe16eae8` and `0xdb006a75`. `quoteRedemption(uint256)` and `redeem(uint256)` hash to these selectors, but their original Solidity names have not been verified. Both entrypoints check that the call is nonpayable, validate a single `uint256` ABI argument, and then revert with the four-byte error selector `0x32aa90b0`. Their function bodies do not read or write storage, make external calls, return, or emit logs. The original error name is unknown.

```text
selector_0xfe16eae8(uint256):
    validate ABI
    revert 0x32aa90b0

selector_0xdb006a75(uint256):
    validate ABI
    revert 0x32aa90b0
```

The [behavior ledger](tokenomics_redemption_stub_behavior.json) checks dispatcher and function instructions against the pinned 3,324-byte runtime. It also checks six archived calls through the Tokenomics proxy at the pinned block, three per selector. All six reverted with `0x32aa90b0`, including a `redeem` call from a PAPER holder. A separate [port-free local replay](../../artifacts/fixed_revert_local/replay.json) passed four canonical calls through the exact pinned proxy and implementation bytecode, with the EIP-1967 implementation slot set locally.

No redemption success path exists through these two entrypoints in this implementation. This statement applies to the pinned runtime, not future upgrades. Other selectors and any off-chain redemption process are outside this finding.
