# Queue consolidation with interleaved users

The [seven-case exact-runtime replay](../../artifacts/exchange_library_queue_interleaved_local/replay.json) creates node order A, B, A with amounts 300, 700, 1100. It first calls the pinned linked-library enqueue selector `0x18958ce2` three times through a temporary delegatecall shim, then restores the pinned Exchange proxy runtime before calling its consolidation and harvest functions. The library creates global IDs 101, 102, 103 while user A's links connect 101 directly to 103. The [behavior ledger](exchange_library_queue_interleaved_behavior.json) records runtime hashes and cases. This is a reachable local library state, not an observed historical queue.

| Operation | Checked result |
|---|---|
| Forward merge A 101 to 103, limit 1 | Succeeds with `(1, 300, 103)`. Node 103 holds A's 1,400. No read or write touches B's node 102. |
| Harvest limit 1 after forward merge | Skips empty node 101, returns 0, leaves global head at 102. |
| Harvest limit 2 after forward merge | Pays B 700 first, leaves A's 1,400 on node 103. |
| Harvest limit 3 after forward merge | Pays B 700, then A 1,400, in global ID order. Both user totals clear. |
| Reverse merge A 101 to 103, limits 1, 2, 3 | Reverts with raw `0x5b6d2b7a`; no storage writes or logs persist. At limits 2 and 3 it reads B's node 102, then reverts before reading node 103. |
| Reverse control with order A, A, B | Merging adjacent A nodes 101 to 102 succeeds at limit 1 and leaves B's node 103 intact. |

These calls show an asymmetry in the sampled state: forward consolidation follows A's linked nodes past B, while the reverse path's reads follow consecutive global IDs and reject this range. The reverse path's exact source-level precondition remains unknown. The raw error is now cataloged as an exercised linked-library error, without a recovered Solidity name. The successful forward path does not move B's balance or change the later global harvest order.

The replay checks return tuples, node words and amounts, per-user queue fields and balances, global head and total, storage read and write sets, and ordered logs. Other owner orderings, longer queues, partial funding in an interleaved queue, and historical use of either consolidation wrapper remain unresolved. Run `python3 scripts/atlas_exchange_library_queue_interleaved_local.py` from the workbench root to rebuild it offline.
