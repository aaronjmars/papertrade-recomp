# Exchange queue layout from enqueues and harvest

The [queue ledger](exchange_queue_layout_behavior.json) hash-verifies `Enqueued(address,uint256,uint256)` (`0xb2f6a0be...`) against three historical close receipts. Its indexed fields are user and node ID; the unindexed value is the queued amount. Nodes 1, 2, and 3 each enqueue `7623942182351823589` internal units for a different user, matching the queue increase in the [close ledger](exchange_close_paths.json).

| Proxy storage | Observed field |
|---|---|
| Slot 16 | Global queue head node ID |
| Slot 17 | Next queue node ID |
| Slot 18 | Total queued amount |
| Mapping base 15, key node ID | Node owner at base slot, amount at base slot plus 1 |
| Mapping base 19, key user | User's queued amount |
| Mapping base 20, key user | User queue head node ID |
| Mapping base 21, key user | User queue tail node ID |

The [getter ledger](exchange_getters.md) hash-verifies `userQueuedTotal(address)`, `userQueueHead(address)`, and `userQueueTail(address)` against these three mappings at the archived queued and cleared states.

The first enqueue sets global head to 1. Across the three closes, next ID advances from 1 to 4 and total queued grows by one event amount each time. Each user starts with one node, so that user's head and tail both equal the event node ID. The observed history contains no same-user append; a controlled fork probe checks that branch below.

A later `harvest(32)` in block 48,173,890 returns the full sum of the three amounts. It advances global head from 1 to 4 and clears total queued, all three node amounts, each user's queued amount, and each user's head and tail. The diff tracer omits the zero post words; the ledger checks their nonzero prestates, omitted posts, harvest output, and the adjacent transaction order.

The [partial-harvest ledger](exchange_queue_harvest_behavior.json) covers the full `Enqueued` event history from Exchange deployment through the pin: exactly these three logs, each for a different user. At archived block 48,173,889, read-only `harvest(0)`, `harvest(1)`, `harvest(2)`, and `harvest(3)` calls return zero, one, two, and three node amounts. Each processed node credits its user's balance by its queued amount, lowers total queued by that amount, and advances the global head. Unprocessed nodes have no storage diff. The three-node simulation has the same Exchange storage diff and ordered logs as the recorded `harvest(32)` transaction in the following block.

Each nonzero probe emits one `Harvested(address,uint256,uint256)` event per processed user, then `SideBucketUpdated(uint256)`. Slot 27 falls by each processed amount while nodes remain; when the queue empties, it resets to zero. These partial paths are read-only simulations.

The [same-user append ledger](exchange_queue_append_behavior.json) starts from a separate archive-backed fork at block 48,173,880. With the two historical HyperCore bid and ask words mocked, the saved signed close reproduces its historical Exchange storage diff and all six ordered logs exactly. A synthetic existing queue node of `5 * 10^18` internal units for the same user then makes the identical close append node 2. Node 1 keeps the user address in its low 160 bits and records next ID 2 in bits 160 to 207. Node 2 records previous ID 1 in bits 208 to 255, with its next ID zero. The global head and user head stay at 1; next ID becomes 3, and the user tail becomes 2.

Two further read-only harvest probes use that synthetic post-close state and a local treasury increase to pass the availability gate. `harvest(1)` credits the first amount, moves both the global and user heads to node 2, and clears node 2's previous link. `harvest(2)` credits both amounts and clears the user's head, tail, and queued balance. This establishes the sampled two-node same-user path. A later [exact-runtime interleaved-user replay](exchange_library_queue_interleaved.md) creates A, B, A nodes through the pinned library and checks both consolidation directions and harvest order.

Eight [funding-limited probes](exchange_queue_append_behavior.json) vary available funds across `0`, `3 * 10^18`, `5 * 10^18`, and `7 * 10^18` internal units with harvest limits 1 and 2. With 3 available against a 5-unit first node, harvest credits 3, leaves 2 on that node, and keeps the head in place. At exactly 5, it clears the first node. With 7 available and a limit of 1, it pays only the first 5; a limit of 2 pays another 2 from node 2 and leaves `5623942182351823589` there. Each `Harvested` event carries the amount paid followed by the amount remaining on that node.

An [archive trace at the real three-node queue state](exchange_queue_harvest_behavior.json) repeats the underfunded branch with only treasury overridden to make `3 * 10^18` available. It pays 3 from node 1, leaves `4623942182351823589` on that node, keeps the global head at 1, and lowers slot 27 by the payout. It emits `SideBucketUpdated` with the new slot-27 value. No underfunded harvest or same-user append occurred in the pinned on-chain history; larger queues and concurrent enqueues remain open.
