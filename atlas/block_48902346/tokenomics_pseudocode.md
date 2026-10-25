# Tokenomics observed behavior at block 48,902,346

This map is reconstructed from the deployed implementation, 38 settlement calls and four adjustment calls in 20 historical transactions, their receipt logs and state diffs, and twelve pinned read-only branch probes. The [machine-readable ledger](tokenomics_observed_paths.json) records every call and check. A separate [direct-liquidation ledger](liquidation_tokenomics_behavior.json) verifies 67 calls in 26 archived Exchange batches, with three calls overlapping the first ledger. It is a behavior map, not recovered Solidity source.

## Observed storage

| Proxy slot | Observed meaning | Evidence |
|---|---|---|
| 0 | Packed initialization and owner | Pinned owner getter and owner transfer |
| 1 | Exchange address | Pinned getter and caller checks |
| 2 | PAPER token address | Historical owner setter and event, pinned getter and mint child calls |
| 3 | Tracked LP USD, a signed accounting quantity stored as a 256-bit word | Pinned getter, 42 call transitions, 20 transaction diffs |
| 4 | Tail progress USD | Pinned getter, math inputs and outputs, 20 transaction diffs |
| 5 to 8 | Mint parameters | Pinned getters and 25 math delegatecalls |

The [direct getter checks](tokenomics_direct_getters.md) hash-verify seven names and match archived return words to pinned storage and opcode traces. The slot-5 alias still lacks a source name. The slot-6 getter has a Guardian report name and exact selector-hash match: `stakerLpRewardCapUsd()`.

At this pin, the math calls pass threshold `2 * 10^24`, flat rate `100 * 10^18`, and tail decay scale `120 * 10^24`. Slot 6 holds a `5 * 10^24` floor for `stakerLpDistributableExcessUsd()` (`0xae745703`). [Getter alias evidence](tokenomics_getter_aliases.md) shows that unnamed selector `0x3886cade` and hash-matching `lpFlatThresholdUsd()` selector `0xe9ed73e9` both return slot 5, while report-backed `stakerLpRewardCapUsd()` (`0xc16017ca`) returns slot 6. A scheduled timelock change to the four parameters had not executed at the pin.

## Two-address initializer

The [exact-runtime local probe](remaining_initializers.md) verifies `initialize(address,address)` at selector `0x485cc955` in synthetic fresh storage. It sets owner and Exchange, writes four default mint parameters to slots 5 through 8, and emits `OwnerUpdated` and `MintParamsUpdated`. A repeated call reverts with `AlreadyInitialized()`. This is a local branch test, not a historical deployment replay.

## PAPER-token admin pointer

The [owner-transfer ledger](tokenomics_owner_transfer_behavior.json) checks one successful historical `transferOwnership(address)` call. The caller equals the old owner packed above the initialization flag in slot 0. The new owner from calldata replaces only that address field; the low initialized flag remains 1. The sole Tokenomics log has the exact `OwnerUpdated(address)` topic and indexed new owner, and the pinned `owner()` getter returns it. Outsider and zero-address transfer branches remain untested in this ledger.

The [admin ledger](tokenomics_paper_admin_behavior.json) hash-verifies `setPaperToken(address)`, `paperToken()`, and `PaperTokenUpdated(address)`. A successful historical call from the original owner set slot 2 from zero to the PAPER proxy and emitted the new address as the event's only indexed field. The pinned getter returns that address. Four read-only pinned calls show the current owner can set another address, zero, or the existing address; the unrelated caller reverts with `NotOwner()`. Setting zero is a simulated accepted call, not an on-chain configuration change. Downstream settlement after changing the pointer was not replayed.

## Governance mint parameters, selector `0x12baae3b`

`setMintParams(uint256,uint256,uint256,uint256)` hashes exactly to the live selector. The [parameter probe ledger](tokenomics_params_behavior.json) checks 15 pinned read-only calls and four excess-getter overrides. A timelock operation scheduled this call with arguments `(2 * 10^24, 10 * 10^24, 100 * 10^18, 120 * 10^24)` and was ready but not executed at the pin. A direct read-only simulation from the timelock changes slot 6 from `5 * 10^24` to `10 * 10^24` and emits `MintParamsUpdated(uint256,uint256,uint256,uint256)`. A separate simulation of the complete timelock execution reaches the same Tokenomics event through the proxy and implementation, updates slot 6, and marks the operation done in timelock storage. The other three scheduled values already equal the pinned slots.

A separate call with four distinct positive values changes slots 5, 6, 7, and 8 in argument order. The event has no indexed fields and contains those four values. The tested validation accepts equality between the first two values and small positive rate and scale values; it rejects zero in any field and a first value above the second with `InvalidMintParams()` (`0xbad8ef95`). An unrelated caller receives `NotOwner()` (`0x30cd7471`). Both error names reproduce their selectors exactly. A maximum `uint256` flat rate passed the setter probe; downstream mint arithmetic with that value was not tested.

Four state overrides confirm `stakerLpDistributableExcessUsd()` (`0xae745703`) returns `max(trackedLpUsd - slot6, 0)`, including a floor above the tracked value. The [Guardian audit report](https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/) also uses `stakerLpExcessToDistribute()` elsewhere; that name hashes to `0x18715c9a`. It does not match this Tokenomics getter, but a later [Exchange view trace](exchange_small_views.md) proves the Exchange selector `0x18715c9a` forwards to the Tokenomics getter. The audited source snapshot has not been matched to this runtime. The setter behavior and event are simulations; the scheduled governance operation did not execute.

Four more read-only mint calls use the same pinned tracked state and override parameter slots. The baseline and scheduled slot-6-only values both mint `11,303,568,816,826,005,791` units for a one-PAPER basis. Changing all four parameters to the distinct tested values mints `13,808,026,739,943,372,833`; raising the threshold to `6 * 10^24` enters the flat branch and mints `100 * 10^18`. In each case, the nested PaperMath inputs, its two outputs, the Tokenomics event, and the PAPER mint call agree with the recovered formula. The scheduled floor change can still affect later minting indirectly through the excess adjustment path; an ordered governance, adjustment, and mint sequence has not been replayed.

## Exchange settlement path, `onCloseBatch(address,uint256,uint256,uint256)` (`0xed722c96`)

```text
require caller == Exchange
input: recipient, debit, mintBasis, credit
trackedAfterDebit = trackedLpUsd - debit
trackedLpUsd = trackedAfterDebit + credit

if mintBasis > 0:
    (mintAmount, tailDelta) = PaperMath(trackedAfterDebit,
                                        tailProgressUsd, mintBasis,
                                        threshold, flatRate, decayScale)
    tailProgressUsd += tailDelta
    PAPER.mint(recipient, mintAmount)
else:
    mintAmount = 0
    tailDelta = 0

emit topic 0x620c26bf... with indexed recipient and
     (debit, mintBasis, trackedAfterDebit, trackedLpUsd,
      tailDelta, mintAmount)
```

All 32 historical calls followed this shape. Thirteen calls had no mint. The other 19 minted PAPER. For all 32, the event's tracked values agree with the call inputs and prior state. The signed slot-3 change equals `credit - debit`, including samples whose raw word represents a negative value. In the sampled mint calls, `credit == mintBasis`; one also has a nonzero debit. A pinned probe shows `credit > mintBasis` reverts with selector `0x85c58396`. The wider accepted relationship between those values still needs branch tests.

The [mixed gain and loss close replay](exchange_negative_close_fee.md) isolates the Exchange loss-fee rate in slot 23. On the losing close, Exchange calls `onCloseBatch` with `debit = 0` and `mintBasis = credit = abs(adjustedPnl) - fee`. The trader receives `margin + adjustedPnl` regardless of the rate. Thus the fee reduces Tokenomics tracked LP credit and PAPER mint basis while Exchange accrues the fee for staker and developer. In the same batch's profitable close, `debit = adjustedPnl` and `mintBasis = credit = 0` even when the separate slot-24 profit fee changes.

## Liquidation path, `onLoss(address,uint256,bool,uint256,uint256)` (`0x0efdf838`)

```text
require caller == Exchange
input: recipient, positionId, boolFlag, mintBasis, credit
before = trackedLpUsd
trackedLpUsd += credit
(mintAmount, tailDelta) = PaperMath(before, tailProgressUsd,
                                    mintBasis, threshold, flatRate, decayScale)
tailProgressUsd += tailDelta
PAPER.mint(recipient, mintAmount)
emit topic 0x3050fba1... with indexed recipient and positionId,
     then (boolFlag, mintBasis, before, trackedLpUsd,
           tailDelta, mintAmount)
```

The Guardian report names `onLoss(address,uint256,bool,uint256,uint256)`, an exact selector-hash and argument-layout match; its source snapshot has not been matched to the live bytecode. The first sampled ledger contains six historical liquidation calls from two keeper transactions. The [direct-liquidation ledger](liquidation_tokenomics_behavior.json) checks 67 calls in 26 direct Exchange batches, three overlapping those six, for 70 distinct sampled liquidation calls. All 67 direct-batch calls have `boolFlag == true`, `credit < mintBasis`, and a positive tail mint. For each, `mintBasis - credit` equals the sum of the two fee fields in the matching Exchange `Liquidated` event. A pinned call with `boolFlag == 2` reverts at ABI decoding. A zero basis and zero credit call succeeds without an event or mint, so the pseudocode above covers only the positive branch.

The [flag branch ledger](tokenomics_liquidation_flag_behavior.json) compares six read-only calls at the same pinned state: true and false flags with a positive basis, with zero basis and zero credit, and with credit but no basis. The two positive calls follow the same 1,268-opcode path through the proxy, implementation, PaperMath, and PAPER mint. Their storage differences, nested calls, and PAPER Transfer are identical. Only the first word of the Tokenomics liquidation event changes from 1 to 0. Both zero cases return with no logs or Tokenomics or PAPER writes. Both credit-only cases revert with raw selector `0x85c58396` and no contract writes. These are synthetic pinned calls; no historical false-flag execution has been found, and the opcode comparison covers only the tested positive inputs.

## Exchange adjustment path, `distributeLpToStakers(uint256)` (`0xc218c676`)

Four recent successful batch transactions call `stakerLpDistributableExcessUsd()` (`0xae745703`), then `distributeLpToStakers(uint256)` (`0xc218c676`), then the getter again. The first getter returns `trackedLpUsd - 5 * 10^24`; the adjustment amount equals that excess. The adjustment reduces slot 3 to exactly `5 * 10^24` and leaves tail progress unchanged. The second getter returns zero. Its hash-verified `StakerLpDistributed(uint256,int256,uint256)` event (`0x09f6ca7b...`) carries three unindexed words: amount, signed new tracked value, and tail progress. The same batches later call the settlement mint path. Pinned probes show an outsider reverts with `0xe343677f`, zero amount succeeds without an event, one unit above the available excess reverts with `0xe247b81f`, and the exact excess succeeds with the expected event. Both names hash exactly to the live selectors and fit the observed call sequence; the Guardian report supplied the name lead.

## PAPER mint and math checks

Every one of the 25 positive calls delegates to the linked PaperMath runtime at `0xe991817199363046da0a28da6fbad0284e4aa492`. Its first output equals both the Tokenomics event mint amount and the nested PAPER `mint(address,uint256)` input. The PAPER implementation emits `Transfer(0, recipient, amount)` with the same amount. The second math output equals the Tokenomics event's tail delta and the transaction's slot-4 increase. The PAPER total supply slot-6 increase equals the sum of mints in each transaction.

The additional 67 direct-batch liquidation calls pass the same six PaperMath inputs and have matching two-word outputs, Tokenomics event payloads, PAPER mint calls, and receipt `Transfer` logs. Across all 26 transactions, Tokenomics slot 3 rises by the summed credits, slot 4 by summed tail deltas, and PAPER supply slot 6 by summed minted amounts. Each storage difference matches exactly.

One older call takes a flat branch: `mintAmount == mintBasis * 100` and `tailDelta == 0`. The 24 later positive calls use the tail branch. The following integer calculation reproduces all 25 historical math outputs and six independent pinned calls, including a threshold crossing and an odd rate:

```text
WAD = 10^18
flat = min(amount, max(0, threshold - signed(tracked)))
tail = amount - flat
mint = floor(flat * rate / WAD)
if tail > 0:
    start = floor(scale * WAD / (scale + progress))
    end = floor(scale * WAD / (scale + progress + tail))
    tailRate = floor(floor(rate * start / WAD) * end / WAD)
    mint += floor(tailRate * tail / WAD)
return (mint, tail)
```

At `tracked == threshold`, even a one-unit amount enters the tail branch. A call that crosses the threshold splits its amount between the flat and tail branches. The standalone [PaperMath library map](paper_math_pseudocode.md) verifies all 91 saved delegatecalls and six additional pinned boundary probes. It confirms the zero-scale and selected overflow and division panic paths. Other 256-bit boundary orderings remain open. The linked library's decompiler output omits or misstates branches and is not used as proof.

## Redemption selectors at the pin

`quoteRedemption(uint256)` and `redeem(uint256)` hash to the two selectors, but their original Solidity names remain unverified. The [pinned runtime proof](tokenomics_redemption_stub.md) shows that each entrypoint validates one `uint256` argument and then always reverts with four-byte selector `0x32aa90b0`. Neither function body reads or writes storage, calls another contract, emits a log, or returns. Six archived pinned calls and four local calls through the exact pinned proxy and implementation bytecode confirm this behavior. No redemption success path exists through either entrypoint in this runtime. The error name is unresolved, and a later upgrade could change the behavior.

## Additional fixed-revert selector

Selector `0x7c7df7b4` also reaches `0x32aa90b0` after ABI validation. Its [bytecode proof](tokenomics_seven_word_stub.md) shows a minimum of seven argument words, with validated address, `uint64`, and `uint8` positions; the other word types and source name remain unresolved. Two canonical local calls through the pinned proxy and implementation confirm the revert. The selector tool's five-argument inference is incomplete.

## Access and limits

Pinned read-only probes show both mint selectors reject an outsider with `0xe343677f`. `setMintParams(uint256,uint256,uint256,uint256)` rejects an outsider with `0x30cd7471`. The Exchange caller can make a zero settlement call with an event, and a positive settlement call that mints. The zero liquidation call returns without logs. No transaction was sent during these probes.

The liquidation mint function name, two mint event signatures, downstream math behavior under changed parameters, redemption error name, and unobserved input boundaries remain unresolved. The two redemption entrypoints are fixed reverts in the pinned runtime. The sampled settlement calls establish observed state and call effects, not every reachable branch.
