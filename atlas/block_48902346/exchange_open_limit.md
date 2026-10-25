# Exchange signed-open side limit at block 48,902,346

The [full machine ledger](exchange_open_limit_full_behavior.json) verifies all 57 saved signed opens that reached the side-limit comparison across 13 historical transactions. The [three-path excerpt](exchange_open_limit_behavior.json) retains representative opcode stacks. The remaining signed open expired before this comparison. The market mapping is `keccak256(abi.encode(uint32(instrumentId), uint256(36)))`. Its first word holds two 96-bit values. Its second word holds two 128-bit values set by the keeper selector `0x628a9fd6`.

The signed-open path reads the mapping's first word, computes an updated side value, reads the second word, and compares the updated value with one 128-bit limit. The `isLong` branch uses the low half. The short branch uses the high half. An exceeded limit jumps to the sole pinned implementation body emitting `0x40f92143`. The saved [OpenChain lookup](../../artifacts/openchain_error_40f92143.json) returns `OiCapExceeded()`, and `keccak256("OiCapExceeded()")` has the exact four-byte prefix `0x40f92143`.

| Historical path | Updated value | Stored limit | Result |
|---|---:|---:|---|
| Long, `0x52eec72eedb2eb413dd9abb950c715bfe6b9977bf2248a183b27d059d402d0e0` | 2,533,543,364,653,611,099,749 | 2,533,537,756,243,869,928,879 | `0x40f92143` |
| Long, `0x44d34a2ac0a36042f6ecd850ebc63f738b708d0a27d5993f8b7d9250e77c88cb` | 2,557,158,947,954,086,355,518 | 2,619,826,912,335,858,848,565 | Success |
| Short, first failed open in `0x40dfc149333b3ea102864ca92e03c7d7ee6ccdb823460391e794d3b12639c16c` | 1,987,329,120,640,070,378,229 | 1,985,372,238,956,521,175,420 | `0x40f92143` |

For the failed long open, the first word's low 96 bits are `2,533,530,996,321,976,713,072`. The computed increment is `12,368,331,634,386,677`, and their sum is the updated value above. The implementation compares that sum to the second word's low 128 bits at PC `0xa44` and jumps to the error body at `0xea4`. The successful long open follows the same PC with a false comparison. The failed short open compares against the second word's high 128 bits at PC `0xedc` and jumps to the same error body.

The two 128-bit values act as per-side opening limits in all 57 sampled paths. All 27 `0x40f92143` reverts had an updated value above the corresponding limit: 13 long and 14 short. All 30 successes had an updated value at or below the limit: 15 long and 15 short. Forty-five checks used instrument 0 and twelve used instrument 1. This establishes the guard for the saved sample, not the entire chain history. The error name is a hash-verified public registry match that fits the observed branch; no verified Papertrade source confirms it. The exact Solidity field names and unit labels remain unknown.

Run `python3 scripts/atlas_exchange_open_limit_full.py` to rebuild the full ledger from the saved per-transaction comparison trace and signed-open call ledger. Run `python3 scripts/atlas_exchange_open_limit.py` for the three detailed opcode excerpts. The archived comparison trace is `artifacts/exchange_open_limit_all_traces.json`; the detailed excerpts are in `artifacts/exchange_open_limit*_opcode_trace.json` at the workspace root.
