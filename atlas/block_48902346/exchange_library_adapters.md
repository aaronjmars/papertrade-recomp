# Exchange linked-library adapters at block 48,902,346

Seven local tests cover four Exchange selectors whose pinned implementation delegates into the live linked library. The [replay](../../artifacts/exchange_library_adapters_local/replay.json) hashes and loads the exact proxy, Exchange implementation, and library runtimes. For forwarding and return checks, it replaces the library code at the linked address with a spy. The live-library checks then restore the exact pinned library runtime.

| Exchange selector | Library selector | Forwarded words after selector |
|---|---|---|
| `0x4a4d9eea` | `0xca02ff91` | `15, user, a, b` |
| `0xae4daf4e` | `0x2448a553` | `15, user, a, b, 10^18` |
| `0x753a369c` | `0x3cf4208d` | `15, user, a, b, c, 10^18` |
| `0x827ad94c` | `0x32db40c9` | `15, user, a, b, c` |

All four wrappers return the spy's three words unchanged. When the spy returns four words, the wrappers return only the first three. A two-word reply makes each wrapper revert with empty output, and a raw four-byte library error bubbles through unchanged. The `15` is the base slot of the Exchange queue-node mapping, keyed by node ID in the [historical queue layout](exchange_queue_layout.md). A noncanonical address word and short calldata revert before delegation in the tested wrappers. The deployed Solidity names and the meanings of `a`, `b`, and `c` are unresolved.

With the exact live library runtime and `user = 0x1234, a = 101, b = 202, c = 303`, the first two wrappers return three zero words. The last two revert with raw `0x5b6d2b7a`. The first two read queue-node mapping slot `keccak256(abi.encode(101, 15))`; the third also reads the next word; the fourth reads Exchange slot 17, which the historical queue layout identifies as the next node ID. None of these four local calls writes storage.

A second local state supplies a single synthetic node 101 owned by the user with amount 500 and consistent queue head, tail, and totals. The same four calls produce the same outputs and no storage writes. These are narrow local branches, not historical executions. Separate [count-based consolidation](exchange_library_queue_count_merge.md) and [range-based consolidation](exchange_library_queue_merge.md) replays now reach successful live-library mutation branches for all four wrappers. The count-based tailward path has a checked strict `10^18` amount threshold. Original function names and behavior beyond the sampled queues remain unresolved. The [behavior ledger](exchange_library_adapters_behavior.json) records which results used a spy and which used the pinned library.
