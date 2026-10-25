# Harvest after linked-library queue consolidation

The [eleven-case exact-runtime replay](../../artifacts/exchange_library_queue_harvest_followup_local/replay.json) starts with the same synthetic two- and three-node queues as the [consolidation replay](exchange_library_queue_merge.md). It executes a forward or reverse merge through the pinned Exchange proxy, implementation, and linked library, then calls the real Exchange `harvest(uint256)` wrapper on that resulting storage. The [behavior ledger](exchange_library_queue_harvest_followup_behavior.json) records the selectors, runtime hashes, and case matrix.

All cases use one user and IDs starting at 101. Nine fully funded cases set 10,000 treasury units against 1,000 or 2,100 queued units; two additional cases test zero and 1,000 units of funding after a three-node forward merge. Each test checks the harvest return, storage writes, `Harvested` log, global head and total, user queue fields and credited balance, and every node amount.

| Merge direction | Queue nodes | Harvest limit | Paid | Global head after harvest |
|---|---:|---:|---:|---:|
| Forward | 2 | 1 | 0 | 102 |
| Forward | 2 | 2 or 3 | 1,000 | 103 |
| Reverse | 2 | 1 | 1,000 | 103 |
| Forward | 3 | 1 | 0 | 102 |
| Forward | 3 | 2 | 0 | 103 |
| Forward | 3 | 3 or 4 | 2,100 | 104 |
| Reverse | 3 | 1 | 2,100 | 104 |
| Forward, zero funding | 3 | 3 | 0 | 101 |
| Forward, 1,000 funding | 3 | 3 | 1,000 | 103 |

Forward consolidation moves the amount into the final node but leaves the global head at empty node 101. With funding available, harvest advances past each empty global-head node without payment or a `Harvested` log. Those nodes count toward the supplied node limit. A three-node forward merge followed by `harvest(2)` reaches node 103 but leaves its 2,100 units queued; `harvest(3)` pays them. Reverse consolidation keeps the amount at node 101, so `harvest(1)` pays it in both tested queue sizes. Each successful payout emits one `Harvested` log and credits the user's mapping-9 balance by the exact return amount. The sampled merge does not strand the amount, but a low harvest node limit can defer its payment.

With zero available funding, the Exchange wrapper returns zero before advancing the empty global head. With 1,000 available, it skips the two empty nodes, credits 1,000, leaves 1,100 on node 103, and keeps that node as global head. These are local synthetic states, not historical executions. One [interleaved-user queue](exchange_library_queue_interleaved.md) is now checked: harvest pays B's node before A's surviving node. Other owner orderings, longer ranges, and concurrent enqueues remain open. Run `python3 scripts/atlas_exchange_library_queue_harvest_followup_local.py` from the workbench root to rebuild the replay and ledger offline.
