# Exchange three-address initializer at block 48,902,346

Selector `0xc0c53b8b` accepts three addresses. Its public signature candidate is `initialize(address,address,address)`, but the original Solidity name is not proved. Six local tests run the pinned Exchange proxy and implementation bytecode. Fresh-state results use a synthetic proxy whose slot 0 is reset to zero; no historical deployment initializer trace is saved.

In a fresh state, a call from an unrelated address succeeds with `(owner, oracle, token)`. The third address receives a `decimals()` staticcall. A token address with no code makes the call revert with empty output and rolls back all writes. The successful six-decimal token test writes:

| Slot | Observed value |
|---|---|
| 0 | `(owner << 16) | 1` |
| 1 | owner as pause guardian |
| 2 | oracle address |
| 3 | `10^12` |
| 4 low byte | `8` |
| 5 | `10^10` |
| 17 | `1` |
| 23, 24, 25 | `2 * 10^16` each |
| 28 | `10^18` |

The call emits `OwnerUpdated(address)` with the owner indexed. A repeat call on a synthetic initialized state, with slot 0 set to its pinned owner and flag, reverts with `AlreadyInitialized()` (`0x0dc149f0`). The name is a hash-matched public registry candidate supported by the exact-runtime initialized-state branch. Synthetic tokens with 8 and 18 decimals also initialize: `(slot4 low byte, slot5)` becomes `(10, 10^8)` and `(18, 1)`, respectively. These three samples fit `slot4 = min(tokenDecimals + 2, 18)` and `slot5 = 10^(18 - slot4)`; this is an inference, not a full proof for every token decimal count. A 19-decimal token reverts with `UnsupportedCollateralDecimals()` (`0x6a426315`) and leaves the fresh state unchanged. That name is a hash-matched public registry candidate supported by the exact-runtime 19-decimal branch.

The [behavior ledger](exchange_initializer_behavior.json) separates the synthetic tests from historical evidence. The token address itself was not observed being stored in the tested slots. Other address validation and token behaviors remain open. Run `python3 scripts/atlas_exchange_initializer_local.py` to repeat the [local replay](../../artifacts/exchange_initializer_local/replay.json).
