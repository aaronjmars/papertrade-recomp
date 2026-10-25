# Exchange linked-library queue consolidation at block 48,902,346

The [behavior ledger](exchange_library_queue_merge_behavior.json) and [ten-test replay](../../artifacts/exchange_library_queue_merge_local/replay.json) execute exact pinned Exchange proxy, implementation, and linked-library runtimes. Synthetic states contain two or three adjacent nodes for one user, with valid head, tail, links, and totals. These are local replays, not historical transactions.

| Exchange selector | Library selector | Two-node result | Three-node result at limit 2 or 3 |
|---|---|---|---|
| `0x753a369c` | `0x3cf4208d` | Move node 101 into 102; return `(1, amount from 101, 102)` | Move nodes 101 and 102 into 103; return `(2, 1000, 103)` |
| `0x827ad94c` | `0x32db40c9` | Move node 102 into 101; return `(1, amount from 102, 101)` | Move nodes 102 and 103 into 101; return `(2, 1800, 101)` |

The two-node tests use amounts 500/500 and 300/700 with limits 1 and 2. Both directions make five proxy storage writes and emit two logs. The three-node tests use amounts 300/700/1100 with limits 1, 2, and 3. At limit 1, both directions revert with raw selector `0x5b6d2b7a` and leave storage and logs unchanged. At limits 2 and 3, forward consolidation makes nine writes and reverse makes ten, with three logs each. The sampled final argument therefore bounds the required number of merges, but other argument semantics remain unproven.

Topic `0xb8c6723c...` indexes the user, source node, and target node, with the moved amount in data. The three-node forward path emits moves 101 to 103 for 300, then 102 to 103 for 700. The reverse path emits 102 to 101 for 700, then 103 to 101 for 1100. Topic `0xf949f116...` indexes the user, starting node 101, and resulting node, with merged count and total moved amount in data. Neither topic has a recovered Solidity name. The user queued total in mapping slot 19 and global total in slot 18 remain unchanged in every successful test.

```text
forward(user, start, end, limit):
    require at least the sampled number of merges can fit within limit
    for each tested source from start toward end:
        move source.amount into end.amount
        clear source.amount and update queue links
        emit one move log
    userHead[user] = userTail[user] = end
    emit summary log
    return (mergeCount, totalMoved, end)

reverse(user, start, end, limit):
    require at least the sampled number of merges can fit within limit
    for each tested source after start toward end:
        move source.amount into start.amount
        clear source.amount and update queue links
        emit one move log
    userHead[user] = userTail[user] = start
    emit summary log
    return (mergeCount, totalMoved, start)
```

This pseudocode covers only the tested two- and three-node states. The global queue head in slot 16 stays 101 even after a forward merge empties that node. The [merge-to-harvest replay](exchange_library_queue_harvest_followup.md) checks how the exact Exchange harvest wrapper advances past those empty nodes and pays the surviving amount. A [two-user interleaving replay](exchange_library_queue_interleaved.md) also tests A, B, A node order: forward merge succeeds across B, while reverse merge rejects that range. Ranges over three nodes, caller permissions, full argument semantics, and original function and event names remain unresolved. No historical invocation of either wrapper appears in the saved call graph.

Run `python3 scripts/atlas_exchange_library_queue_merge_local.py` from the workbench root to rebuild the replay and behavior ledger without network access.
