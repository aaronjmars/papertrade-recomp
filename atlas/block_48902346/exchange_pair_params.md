# Exchange two-field configuration at block 48,902,346

The [behavior ledger](exchange_pair_params_behavior.json) reconstructs unnamed setter `0x82f47a3f(uint128,uint128)`, getter `0x1b7c1009()`, and event topic `0x5bcf15b0...`. The setter writes both arguments to proxy slot 28: first in the low 128 bits, second in the high 128 bits. The event has no indexed arguments and returns the same two values. The getter reads slot 28 and returns both fields in argument order. Their economic names remain unresolved.

A [full-history event query](../../artifacts/exchange_pair_params/full_history_event_query.json) returned four successful market-keeper calls through the pin. For every call, saved calldata equals the two event values, and the archived prestate diff changes only proxy slot 28. Each prestate equals the previous call's poststate; the last poststate equals the pinned raw word and full getter output.

| Block | First field | Second field |
|---:|---:|---:|
| 47,925,886 | `1 * 10^18` | `5,000 * 10^18` |
| 48,073,909 | `100 * 10^18` | `10,000 * 10^18` |
| 48,073,990 | `10 * 10^18` | `10,000 * 10^18` |
| 48,329,727 | `10 * 10^18` | `1,000 * 10^18` |

The generic storage trace kept only a return prefix and cut off the final byte of the second word, so the full getter output is saved in the [probe artifact](../../artifacts/exchange_pair_params/pinned_probes.json).

Five pinned read-only calls show the current owner and market keeper can set distinct values; the market keeper can also set both fields to zero; and an unrelated caller reverts with `0x989c4c7c`. Successful calls emit the two argument values and show the packed slot-28 poststate. Calling with the current values still emits the event. These probes do not commit a configuration change. The four returned logs reconcile the observed setter sequence, but provider completeness and unlogged writes are not proved by the log query alone.
