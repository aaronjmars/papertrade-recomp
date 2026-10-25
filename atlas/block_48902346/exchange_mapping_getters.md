# Exchange position and queue mapping getters

The [behavior map](exchange_mapping_getters_behavior.json) checks five selector-name hashes against the live Exchange implementation. Its [archive capture](../../artifacts/exchange_mapping_getters/mapping_getters.json) contains raw storage, getter outputs, and read-only overrides at pinned block 48,902,346 and historical queued block 48,173,889.

| Getter | Storage | Checked result |
|---|---|---|
| `positions(uint256)` | Mapping base 10, two words per ID | Nine returned fields decode from four active position records |
| `positionOwner(uint256)` | Low 160 bits of mapping-10 first word | Matches all four owners |
| `getUserOpenPositionIds(address)` | Dynamic array at mapping base 12 | One user returns four stored IDs, all owned and active; unrelated user returns an empty array |
| `queueNode(uint256)` | Mapping base 15, two words per node | Three historical nodes return owner, next ID, previous ID, and queued amount |
| `userQueueHead(address)` | Mapping base 20 | Three historical users return their corresponding node IDs |

The `positions(uint256)` tuple is `(owner, instrument, entryPrice, margin, leverage, timestamp, side, secondaryFlag, active)` in the tested runtime. Five read-only overrides isolate its packed flags: word1 bit 224 flips `side`; bits 232 and 239 each set `secondaryFlag`; bit 225 has no effect on the tuple; clearing bit 240 clears `active`. The secondary output is a boolean derived from the full byte at bits 232 through 239. A sixth override puts next ID 2 and previous ID 3 into queue node 1, and `queueNode(1)` returns both links with the amount unchanged.

The four active positions and three historical queue nodes are sampled states. Original Solidity source and behavior for other packed values, longer queues, and array updates remain open. The [position ledger](exchange_position_layout.md) and [queue ledger](exchange_queue_layout.md) cover the related writes and transaction effects.
