# Exchange event paths at HyperEVM block 48,902,346

The live proxy is `0x6cd5661646289fb6e65ea5c032310fded797d0a2`; its implementation is `0x0f3febfc94876b0c895f7acecdc8f5c863b549ee`. This is an observed path map, not a full decompilation of the Exchange. Exact signature hashes, payload widths, and source limits are in [exchange_interface_evidence.json](exchange_interface_evidence.json). Call-to-event checks are in [exchange_event_paths.json](exchange_event_paths.json).

## Signed open, selector `0xec6783f0`

```text
on a successful signed open:
    the Exchange returns a newly allocated positionId
    emit PositionOpened(positionId, user, instrumentId, side, flag,
                        entryPrice, margin, leverage)
```

`openPositionBySig(address,uint32,bool,uint128,uint32,bool,uint256,uint64,uint8,bytes32,bytes32)` hashes exactly to selector `0xec6783f0`. `PositionOpened(uint256,address,uint32,bool,bool,uint64,uint128,uint32)` hashes exactly to topic `0x88451ea118...`. In 25 sampled successful calls, the indexed position ID equals the return value. The indexed user and the event's instrument, side, third flag, margin, and leverage match the signed call arguments in every sample. In all 25 samples, the event entry price equals the Oracle midpoint returned inside that Exchange call, and the midpoint equals `floor((HyperCore bid + HyperCore ask) / 2)` from the nested read precompile. The signed EIP-712 type string names the third flag `useDebt` and the fourth argument `size`; the tested event and stored margin equal that `size` argument. The [signed-open hash ledger](session_open_typehash_behavior.json) verifies 58 saved calls, including 28 failed intents, against the pinned SessionKeyManager type hash. The [signed-open side-limit check](exchange_open_limit.md) matches all 27 sampled `OiCapExceeded()` (`0x40f92143`) reverts to a per-side cap guard, while all 30 sampled successes stay below the cap. The name comes from a hash-verified public registry entry rather than verified Papertrade source. The downstream debt behavior, other failed-open checks, and alternate pricing modes remain unresolved. The [position ledger](exchange_position_layout.md) checks the two stored words and balance-to-margin transfer for these 25 opens. Eligibility checks and failure branches remain unresolved.

## Signed close, selector `0x2792e706`

```text
on a successful signed close batch:
    for each observed closed position:
        emit PositionClosed(positionId, user, exitPrice, rawPnl,
                            adjustedPnl, flag, fee)
    emit PositionsClosed(user, aggregate0, aggregate1, aggregate2, aggregate3)
```

`PositionClosed(uint256,address,uint64,int256,int256,bool,uint256)` and `PositionsClosed(address,uint256,uint256,uint256,uint256)` hash exactly to their observed topics. In nine sampled close events, each indexed position ID is present in the signed input array and the indexed user matches the call. The nine aggregate events were emitted by the same close calls. The [sampled close ledger](exchange_close_paths.md) now checks nine settlements against user balances, queued profit, and packed fee accumulators. The [signed-close hash ledger](session_close_typehash_behavior.json) checks 43 successful calls in 22 transactions, including 49 IDs across arrays of length one to three; every nonce call, array hash, struct hash, EIP-712 digest, and returned signer matches the saved nested trace. The economic reason for each branch and the funding of a nonzero fee in one loss case remain unresolved.

## Keeper liquidation, selector `0x599dc539`

```text
liquidateBatch(positionIds):
    for each observed liquidated position:
        emit Liquidated(positionId, user, price, bustPrice, flag, feeA, feeB)
```

`Liquidated(uint256,address,uint64,uint64,bool,uint256,uint256)` hashes exactly to topic `0x0c859bc5db...`. The two saved direct liquidation transactions requested six position IDs total, and the six emitted IDs match those requests exactly. The [position and liquidation ledger](exchange_position_layout.md) now verifies six active-bit clears, no user balance credit, locked-margin release, and two 1% margin fee fields. Liquidation eligibility, price checks, use of remaining margin, and write ordering remain to be reconstructed.

## Interface limits

A pinned public ABI fixture supplies 18 exact event signature preimages and 41 function signature preimages. All 41 function selectors occur in the captured Exchange dispatcher. The newly named `instruments(uint32)` getter reads three words of mapping base slot 7 in a pinned opcode trace. Sixteen event signatures have matching observed topics and payload widths. Ten fixture `indexed` flags disagree with saved receipts, including the one-argument governance update events; the [evidence ledger](exchange_interface_evidence.json) records each mismatch. Argument names and most function output types from the fixture are leads, not recovered source. Its `treasury()` output is contradicted by [pinned accounting storage](exchange_storage_behavior.md), and the [position mapping](exchange_position_layout.md) now ties 25 opens and 15 deactivations to exact storage words.

The [unresolved inventory](unresolved.json) remains authoritative for unnamed selectors, events, errors, and unexercised paths. In particular, the Exchange's linked library and the economic state transitions inside open, close, and liquidation are still incomplete.
