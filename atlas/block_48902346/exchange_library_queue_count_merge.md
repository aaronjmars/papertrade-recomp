# Count-based linked-library queue consolidation

Two Exchange wrappers that previously returned zero on isolated nodes have successful consolidation paths. The [15-case exact-runtime replay](../../artifacts/exchange_library_queue_count_merge_local/replay.json) uses the pinned Exchange proxy, implementation, and live linked library. It checks two- and three-node queues and an A, B, A interleaved state built through the pinned library enqueue function. The [behavior ledger](exchange_library_queue_count_merge_behavior.json) records selectors and test scope.

| Direction | Exchange to library selector | Sampled result |
|---|---|---|
| Headward | `0x4a4d9eea` to `0xca02ff91` | From node 101, count 1 moves node 102's 700 into 101 and returns `(1, 700, 101)`; count 0 moves nodes 102 and 103, returning `(2, 1800, 101)`. |
| Tailward | `0xae4daf4e` to `0x2448a553` | From node 101, count 1 moves its 300 into node 102 and returns `(1, 300, 102)`; count 0 also moves node 102's 700 into 103 and returns `(2, 1000, 103)`. |

The first argument after the user is a starting node ID in sampled calls. Zero resolves to the user's current head. The final argument bounds the number of merges when positive; zero continues through the available linked nodes in tested same-user queues. Each successful merge emits topic `0xb8c6723c...` with indexed user, source ID, target ID and the source amount. A summary topic `0xf949f116...` indexes user, start ID, final ID and carries merge count and total original amount moved. Both topics still lack recovered Solidity names. Queued totals remain unchanged because consolidation only moves value between nodes.

The tailward wrapper forwards a fixed `10^18` word to its library function. Local amounts show a strict boundary: a current node of `10^18 - 1` merges, while one of exactly `10^18` does not. In three-node tests, amounts of `0.6 * 10^18` each produce one merge because the next current node becomes `1.2 * 10^18`; amounts of `0.4 * 10^18` each produce two. A zero neighboring amount also stops the sampled path. The headward wrapper has no sampled amount threshold and merges a later `2 * 10^18` node into the start node.

On a reachable A, B, A queue, the headward wrapper returns zero without writes when asked to start at A's node 101: the next global ID belongs to B. The tailward wrapper follows A's user link from 101 to 103 and moves 300 without changing B's node 102. This matches the direction difference found in the [range-based consolidation replay](exchange_library_queue_interleaved.md).

```text
headward(user, start, count):
    if start == 0: start = userHead[user]
    merge later adjacent same-user nodes into start, up to count
    stop when the next sampled node is absent or belongs to another user
    return (mergedCount, originalAmountsMoved, start)

tailward(user, start, count):
    if start == 0: start = userHead[user]
    while current amount is positive and below 10^18, and a linked next node is usable:
        merge current node toward the final surviving node, up to count
    return (mergedCount, originalAmountsMoved, survivingNode)
```

These sketches cover the checked states, not every branch or original source name. Larger queues, other interleavings, caller permissions, and unusual amount bounds remain unresolved. Run `python3 scripts/atlas_exchange_library_queue_count_merge_local.py` to rebuild the replay offline.
