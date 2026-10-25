# Exchange unit scaling at HyperEVM block 48,902,346

Four unnamed Exchange views use the same two storage scaling factors. The [behavior ledger](exchange_unit_scales_behavior.json) checks 40 archived read-only calls across the pinned state and one temporary storage override. Storage traces independently identify each slot read. The known `collateralScale()` selector `0xec0bdcfc` reads slot 3; its pinned value is `10^12`. Slot 5 contains `10^10` at the pin.

| Selector | Observed calculation | Slot reads |
|---|---|---|
| `0x31a39849()` | `slot5` | 5 |
| `0x70f75ff5(uint256)` | `input * slot5` | 5 |
| `0x2dcc7fce(uint256)` | `floor(input * slot3 / slot5)` | 3, 5 |
| `0xbacd9ea0(uint256)` | `input * slot3` | 3 |

The pinned factors convert a six-decimal raw amount to an eighteen-decimal internal amount with slot 3, and an eight-decimal raw amount to the same internal unit with slot 5. The ratio view multiplies a six-decimal raw amount by 100 to get the corresponding eight-decimal amount. For a saved signed Core withdrawal, `0x2dcc7fce(199000000)` returns `19900000000`, exactly the CoreWriter payload and Exchange event amount. `0xbacd9ea0(199000000)` returns `199 * 10^18`.

The [raw call capture](../../artifacts/exchange_unit_scales/pinned_calls.json) includes zero, small, and historical amount inputs. In the temporary override, slot 3 is 7 and slot 5 is 3, so the ratio view also checks integer truncation rather than only the pinned exact 100-fold ratio. `atlas_exchange_unit_scales.py` verifies the saved outputs offline and recaptures them with `--capture` and `PAPERTRADE_ARCHIVE_RPC`. The four function names, overflow behavior, and zero-divisor error remain unresolved.
