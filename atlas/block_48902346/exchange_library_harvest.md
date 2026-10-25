# Live linked-library queue harvest

Exchange `harvest(uint256)` is a hash-checked selector name supported by the observed queue behavior. It calls live library selector `0x79810ffe` through `DELEGATECALL`. The [machine ledger](exchange_library_harvest_behavior.json) checks its one saved historical call and thirteen archive-backed read-only simulations, including zero, partial, full, same-user, and funding-limited queue paths. Each check starts from the saved call trace and compares the library output with receipt or simulated events and Exchange storage diffs.

| Word | Checked meaning |
|---|---|
| Input 0 | Queue-node mapping base `15` |
| Input 1 | Maximum number of nodes to process, forwarded from `harvest(uint256)` |
| Input 2 | Payment cap supplied by Exchange |
| Input 3 | User-balance mapping base `9` |
| Input 4 | Running amount; its economic name is unresolved |
| Return 0 | Total amount credited to users, also returned by `harvest(uint256)` |
| Return 1 | Input 4 plus Return 0 |

In every sampled call, the sum of `Harvested(address,uint256,uint256)` payment fields equals Return 0. Exchange queue total in slot 18 falls by the same amount, and each recipient's balance in mapping 9 rises by that recipient's payment. Return 0 never exceeds Input 2. The second event amount is the amount remaining on the processed node.

```text
paid = 0
for at most maxNodes while a queued node can receive funding:
    payment = min(node.remaining, availableFunding)
    node.remaining -= payment
    balances[node.user] += payment
    totalQueued -= payment
    paid += payment
    availableFunding -= payment
    emit Harvested(node.user, payment, node.remaining)
    if node.remaining == 0: advance queue links and head
return (paid, input4 + paid)
```

This is a behavior sketch for the checked branches. The full three-node historical harvest pays `22,871,826,547,055,470,767` internal units. In one archive-backed state, a `3 * 10^18` cap pays only that amount from the first node and leaves its remainder and global head in place. A synthetic same-user two-node state tests both a one-node payout and partial payment of the second node. Two saved zero-availability Exchange calls skip the library entirely.

A separate [exact-runtime merge-to-harvest replay](exchange_library_queue_harvest_followup.md) shows that a forward merge can leave empty nodes at the global head. With funding available, harvest counts those nodes against its limit before paying the surviving node. The exact source function name, Input 4's economic role, queues longer than three nodes, extreme values, and all error branches remain unresolved. Reproduce the ledger offline with `python3 scripts/atlas_exchange_library_harvest.py`.
