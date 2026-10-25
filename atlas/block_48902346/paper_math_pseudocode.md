# Live PaperMath library

The live Tokenomics proxy delegates to PaperMath at `0xe991817199363046da0a28da6fbad0284e4aa492`. Its only selector is `0x7aac24ba`. The original function name is unknown. The first input is interpreted as signed `int256` by the runtime; the other five inputs and both outputs are unsigned words. The [machine ledger](paper_math_behavior.json) verifies 91 successful historical calls in 41 transactions and 12 direct read-only calls at pinned block 48,902,346.

```text
input: tracked:int256, progress:uint256, amount:uint256,
       threshold:uint256, rate:uint256, scale:uint256
output: mint:uint256, tail:uint256

WAD = 10^18
flat = min(amount, max(0, threshold - tracked))
tail = amount - flat
mint = floor(flat * rate / WAD)
if tail > 0:
    start = floor(scale * WAD / (scale + progress))
    end = floor(scale * WAD / (scale + progress + tail))
    tailRate = floor(floor(rate * start / WAD) * end / WAD)
    mint += floor(tailRate * tail / WAD)
return (mint, tail)
```

One historical call takes the flat branch with a negative tracked value; 90 take the tail branch. All 91 two-word outputs match Tokenomics mint events in receipt order, and all 91 mint amounts match PAPER `Transfer` logs from the zero address. The expanded sample includes 64 additional distinct direct-batch liquidation calls from the [cross-contract ledger](liquidation_tokenomics_behavior.json). Earlier direct probes cover the threshold crossing, exact threshold, odd rate, and zero progress. Six new [boundary traces](../../artifacts/paper_math/pinned_boundaries.json) check zero amount, zero scale with positive progress, and four panic paths. A zero amount returns `(0,0)`. Zero scale with positive progress returns `(0,tail)`. Zero scale and progress together trigger `Panic(0x12)` when the tail is positive. A flat multiplication overflow, signed tracked plus amount overflow, and scale plus progress overflow each trigger `Panic(0x11)`.

The formula describes successful calls within checked arithmetic bounds. The runtime performs checked signed and unsigned arithmetic, so the displayed formula alone must not be used to infer behavior at every 256-bit boundary. No event is recorded in the sampled PaperMath calls; the pinned runtime is classified as pure. Its source name and additional overflow orderings remain unresolved.
