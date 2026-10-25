# Exchange side bucket at block 48,902,346

The [side-bucket ledger](exchange_side_bucket_behavior.json) hash-verifies the `sideBucket()` getter (`0x9274682e`) and `SideBucketUpdated(uint256)` event (`0xc2a40711...`). The pinned getter reads proxy slot 27 and returns zero.

Two adjacent historical blocks show the transition. A signed close in block 48,173,889 writes `400296219202209635129` to slot 27 and emits that value. The next block's `harvest(uint256)` call clears slot 27 and emits zero. The diff tracer omits the zero post word, so the ledger checks the event, previous slot value, and omitted post state together. The harvest also pays queued claims, but these two transactions do not establish every branch that can change the side bucket.
