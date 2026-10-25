# Live Exchange linked library at block 48,902,346

The [library ledger](exchange_library_behavior.json) extracts 99 successful delegatecalls in 23 saved historical transactions. Forty-nine calls to `0x82296364` are each followed by a call to `0xef1a27a9` inside Exchange selector `0x2792e706`. One call to `0x79810ffe` appears under Exchange selector `0xddc63262`. The exact source names of all ten library selectors remain unknown. This document describes checked behavior, not original Solidity.

The parent selector hashes exactly to `closeBySig(address,uint256[],uint256,uint64,uint8,bytes32,bytes32)`. Forty-three saved Exchange implementation calls have a dynamic position-ID array with one to three IDs, 49 IDs total. Each ID produces one PnL and settlement pair. The [signed-close hash ledger](session_close_typehash_behavior.json) independently rebuilds all 43 sampled EIP-712 intent digests and checks nested signer calls. Rejection branches remain outside these successful calls.

## Two-word PnL calculation, `0x82296364`

The 40 observed calls carry nine 32-byte argument words. Opcode checks constrain the first five to `uint64 entryPrice`, `uint64 exitPrice`, `uint128 margin`, `uint32 leverage`, and `bool isLong`. The last four are unsigned words whose source names remain unknown. The first is a fraction, and the others modify positive payouts. The function returns signed `rawPnl` and `adjustedPnl`.

The following integer model exactly matches both return words in all 49 historical calls and all 24 pinned direct-call probes. `floor` means integer division toward zero for the nonnegative quantities shown; `W = 10^18`.

```text
directionalMove = isLong ? exitPrice - entryPrice : entryPrice - exitPrice
if directionalMove > 0:
    directionalMove = max(directionalMove - floor(entryPrice / 50_000), 0)
rawPnl = sign(directionalMove) * floor(margin * leverage * abs(directionalMove) / entryPrice)

if rawPnl <= 0:
    adjustedPnl = rawPnl
else if input6 == 0 or input7 == 0 or input5 == W:
    adjustedPnl = 0
else:
    returnFraction = floor(directionalMove * W / entryPrice)
    exposure = floor(returnFraction * input6 / W)
    inverseExposure = floor(W * W / exposure)
    liquidityExposure = floor(returnFraction * 10^6 * input7 / W)
    inverseLiquidity = floor(input8 * W / liquidityExposure)
    factor = floor((W - input5) * W / (W + inverseExposure + inverseLiquidity))
    adjustedPnl = floor(rawPnl * factor / W)
```

Profit below the `floor(entryPrice / 50,000)` threshold becomes zero; losing moves use the full price difference. The saved [opcode trace](../../artifacts/exchange_library/pnl_sample_opcode_trace.json) reproduces a historical call's two return words and confirms the staged division order. The pinned probes vary direction, profit and loss, the threshold, the fraction, and each of the three adjustment inputs. They are read-only simulations.

## Six-word close settlement, `0xef1a27a9`

Every sampled `0xef1a27a9` call takes its third word from the position margin and its fourth word from the preceding `adjustedPnl`. Its six output words match the model below for all 49 historical pairs. In those transactions, input word 4 is zero and words 5 and 6 are both `2 * 10^16`. The [controlled rate ledger](exchange_library_fee_rates.md) verifies 36 additional local replay calls with independent rate changes: input 5 is the positive-PnL rate from Exchange slot 24, and input 6 is the negative-PnL rate from slot 23.

```text
rate = adjustedPnl > 0 ? input5 : adjustedPnl < 0 ? input6 : 0
fee = floor(abs(adjustedPnl) * rate / W)
output0 = margin + min(adjustedPnl, 0)

if input7 == 0:
    output1 = 0
    output2 = adjustedPnl - fee if adjustedPnl > 0 else 0
    output3 = -adjustedPnl if adjustedPnl < 0 else 0
    output4 = output5 = 0
else:
    output1 = adjustedPnl - fee if adjustedPnl > 0 else 0
    output2 = output3 = 0
    output4 = floor(fee / 2) if adjustedPnl != 0 else 0
    output5 = fee - output4
```

The historical calls cover 21 losses, 19 profits, and five flat results with nonzero input 7, plus three profits and one loss with input 7 equal to zero. The controlled replay covers positive PnL with and without a queue, and directly settled negative PnL. The model checks output words; it does not assign source-level meanings to all six fields or prove the Exchange's subsequent accounting writes.

## Other paths and limits

The [queue-harvest library path](exchange_library_harvest.md) now checks the single historical `0x79810ffe` call and thirteen archived read-only simulations. Both return words reconcile with the parent result, `Harvested` events, queue debits, and user balance credits in the sampled branches. The other seven library selectors have no saved historical call. Four are exercised through their [Exchange adapters](exchange_library_adapters.md) in narrow local states. The [three remaining selectors](exchange_library_remaining.md) now have direct exact-runtime local probes: two queue mutations and a seven-word arithmetic function. The library is linked to the live Exchange implementation and executes stateful paths by `DELEGATECALL`, so those paths operate on Exchange storage. Exact source names and untested queue branches remain open. The seven-word arithmetic selector now has an [opcode-supported integer sequence](exchange_library_remaining.md) matching 40 local vectors; extreme arithmetic remains untested.
