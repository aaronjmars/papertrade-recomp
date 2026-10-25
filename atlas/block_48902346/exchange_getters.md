# Exchange queue, sweep, and Core-withdrawal getters

The [getter ledger](exchange_getters_behavior.json) hash-verifies five previously unnamed selectors against the pinned Exchange dispatcher. It compares 80 archived `eth_call` outputs with saved queue, sweep, and signed-withdrawal storage diffs. The raw calls are in [historical_getter_calls.json](../../artifacts/exchange_getters/historical_getter_calls.json).

| Selector | Exact signature | Storage | Verified return |
|---|---|---|---|
| `0x551306f3` | `userQueuedTotal(address)` | Mapping base 19 | Total amount queued for a user |
| `0x3a21be03` | `userQueueTail(address)` | Mapping base 21 | Last node ID in a user's queue |
| `0x31a4956c` | `getPendingSweep(address)` | Mapping base 33 | Exists flag, raw spot amount, raw perp amount, request block |
| `0x7e4174fc` | `pendingSweepWord(address)` | Mapping base 33 | The packed pending-sweep storage word |
| `0x32faa570` | `lastCoreWithdrawalBlock(address)` | Mapping base 34 | Block of the user's last signed Core withdrawal |

`userQueueHead(address)` (`0xdcab7f6a`) was already named. Its mapping base is 20. At block 48,173,889, all three historical queue users return the enqueued amount and their node ID from the total, head, and tail getters. All three return zero after the recorded `harvest(32)` in the next block. The [queue ledger](exchange_queue_layout.md) separately proves each mapping write.

For all 13 saved sweep request and finalization pairs, `getPendingSweep` returns `(1, spotRaw, perpRaw, requestBlock)` after the request and four zeros after finalization. `pendingSweepWord` returns `spotRaw | (perpRaw << 64) | (requestBlock << 128)` and then zero. Both outputs match the pending mapping word written and cleared in each [sweep diff](exchange_sweep_behavior.json). These historical sweeps are spot-only; earlier local sweep probes cover selected nonzero perp amounts.

Three saved signed Core withdrawals write mapping base 34 to their transaction block, and `lastCoreWithdrawalBlock` returns each new value. A fourth captured withdrawal in block 48,783,615 writes the same user's slot. The getter still returns that block during a later sampled sweep request and finalization. This is direct evidence for the getter's purpose; its use as a cooldown or authorization gate is not yet established.

All five function names are exact selector preimages. The pending tuple's field widths agree with the deployed return masks and saved raw word. Other caller branches and same-block ordering remain open.
