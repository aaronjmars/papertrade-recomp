# Three remaining live Exchange library selectors

The pinned live library runtime at `0xcd617f984158a4f5d287ddee0e8eb0fed204916d` was loaded by hash into six assertion-bearing Forge tests. The two stateful selectors ran through `DELEGATECALL` in a local harness with queue mapping base 15. The arithmetic selector ran through `STATICCALL`. The [machine behavior](exchange_library_remaining_behavior.json) and [replay ledger](../../artifacts/exchange_library_remaining_local/replay.json) preserve the runtime hash, test-source hash, state examples, and all 40 arithmetic inputs and outputs. These are synthetic local states, not historical user calls.

| Selector | Observed behavior | Limits |
|---|---|---|
| `0x18958ce2` | With next ID 1, `(15,user,500)` creates node 1, sets global head 1 and next ID 2, increases global and user totals by 500, and emits exact `Enqueued(address,uint256,uint256)` with indexed user and node ID. A second `(15,user,300)` appends node 2, links node 1 to 2 and node 2 back to 1, and produces total 800. Zero amount succeeds without a log or state change. | Exact Solidity name, authorization context, and other branches are unknown. |
| `0x3f4e3626` | `(15,user,500)` clears a single 500-unit node and advances global head to 2. In a two-node 500 + 300 state, `(15,user,200)` reduces the newest node to 100, leaving the older node intact. The event topic is `0x4c672bd1e7444966ce521bc0f053d4f359f1fad9c`, indexed by user, with requested amount as data. A synthetic request for 501 against a 500-unit queue clears the 500 units but emits 501. | The third ABI word is an amount, correcting `cast`'s `bool` guess. The exact source type and event name remain unresolved. The over-request result alone is not a claim about a reachable Exchange exploit. |
| `0xb67f3dd7` | All 40 seven-word `STATICCALL` vectors succeed and return one word. A falling end price uses the absolute price change. Controlled `start = 0` and `prior > 1e18` calls revert with Solidity panic codes `0x12` and `0x11`. | The integer sequence below matches all 40 vectors and an archived opcode trace. Extreme uint256 inputs, every error branch, the economic meaning of all seven words, and the source name remain open. |

For the arithmetic selector, label the seven words `(amount,start,end,prior,factor,denominator,adjustment)` and let `W = 1e18`. In the tested nonnegative range, the exact instruction order is:

```text
delta = abs(end - start)
r = floor(delta * W / start)
m = floor(r * factor / W)
inverse = floor(W * W / m)
a = floor((1e6 * r) * denominator / W)
adjustmentTerm = floor(adjustment * W / a)
D = W + inverse + adjustmentTerm
rate = floor((W - prior) * W / D)
result = floor(amount * rate / W)
```

The previous 31-of-32 candidate subtracted `prior` from `amount`. The [archived opcode trace](../../artifacts/exchange_library_remaining_local/opcode_trace17.json) instead shows `W - prior` before the rate division, followed by multiplication by `amount`. Its checkpoints at program counters `0x1123`, `0x1161`, `0x11b6`, and `0x11bc` match the saved calculation. Eight added vectors separate the two formulas, including a nonzero `prior` with `amount = 2e18` and a falling end price. Equal prices, zero `factor`, zero `denominator`, and `prior = W` return zero in the sampled calls. The argument labels are placeholders; integer overflow and other extreme inputs remain uncharacterized.

The queue state lives in the caller's storage. This harness checks the exact library code and observed state transitions, but does not prove the Exchange wrapper permits every synthetic input or that these tests cover all branches. The `payable` mutability in `cast selectors` is only its inference, not a verified source declaration.

Reproduce offline with `python3 scripts/atlas_exchange_library_remaining_local.py`, then regenerate `atlas_catalog.py`, `atlas_signatures.py`, `atlas_unresolved.py`, `atlas_selector_coverage.py`, and run `atlas_verify.py`.
