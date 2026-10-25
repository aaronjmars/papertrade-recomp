# Exchange open-position index at block 48,902,346

The [behavior ledger](exchange_position_index_behavior.json) checks selector `0xf728fc98`, whose original source name is unknown. The getter reads `mapping(uint256 positionId => uint256)` at Exchange storage base slot 13. Its value is the position's one-based index in that user's open-position ID array at mapping base slot 12.

```text
on sampled open:
    openIds[user].push(positionId)
    indexPlusOne[positionId] = openIds[user].length

on sampled single close or liquidation, final state matches:
    i = indexPlusOne[positionId] - 1
    lastId = openIds[user][openIds[user].length - 1]
    openIds[user][i] = lastId
    indexPlusOne[lastId] = i + 1
    openIds[user].pop()
    delete indexPlusOne[positionId]
```

All 25 sampled opens write a positive value at `keccak256(abi.encode(positionId, 13))`. For each, the element at `keccak256(keccak256(abi.encode(user, 12))) + value - 1` contains the same position ID, and the array length is at least `value`. The 15 sampled closes and liquidations all remove a previously nonzero index word. Thirteen single-removal user groups also shorten the array by one: eleven pop the last element, and two move the last ID into the removed slot and update its index mapping. One transaction removes two IDs from the same user; its final two-element array and moved ID index match two sequential swap-and-pop removals in event order. The saved state diffs and derived slots are in the ledger.

Three archived getter calls at opening block 48,901,640 return 2, 14, and 1 for position IDs 1,392,998 through 1,393,000. Each return equals the raw mapping slot. The [saved RPC responses](../../artifacts/exchange_position_index/historical_getters.json) and `atlas_exchange_position_index.py` reproduce those checks offline.

The samples establish the mapping's role in these opens and removals. They do not establish the exact source name, intermediate write order in the two-removal transaction, or every mutation branch. A block-end getter can differ from the immediate poststate of an earlier transaction in that block.
