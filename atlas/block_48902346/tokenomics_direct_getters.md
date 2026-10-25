# Tokenomics direct getters at HyperEVM block 48,902,346

The [machine-readable map](tokenomics_direct_getters_behavior.json) and [saved archive capture](../../artifacts/tokenomics_getters/pinned_getters.json) establish seven exact selector-name hashes. Each archived getter output equals the field read from pinned proxy storage, and its saved opcode trace reads the stated slot.

| Getter | Storage slot | Returned field |
|---|---:|---|
| `owner()` | 0 | Address in bits 16 through 175, beside the initialized flag |
| `exchange()` | 1 | Low 160-bit address |
| `trackedLpUsd()` | 3 | Signed accounting word, returned as 256 bits |
| `tailProgressUsd()` | 4 | Full word |
| `lpFlatThresholdUsd()` | 5 | Full word |
| `flatRate()` | 7 | Full word |
| `tailDecayScaleUsd()` | 8 | Full word |

Unnamed selector `0x3886cade` returns the same slot-5 word as `lpFlatThresholdUsd()`. The existing [alias tests](tokenomics_getter_aliases.md) establish this shared entry path; they do not establish the alias's source name. Selector `0xc16017ca` reads slot 6 and also remains unnamed. The separate [parameter setter checks](tokenomics_pseudocode.md) show that slots 5 through 8 can change through governance. The exact source-language integer widths and untested future states remain open.
