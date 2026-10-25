# Exchange liquidation-price view at HyperEVM block 48,902,346

The unnamed Exchange selector `0x50c23fab(uint256)` returns a calculated liquidation price for a position ID. The [behavior ledger](exchange_liquidation_price_behavior.json) matches 26 archived getter outputs, including four active positions and 22 inactive positions. Its outputs for the four active positions equal the exact success prices measured by the independent [local liquidation probes](exchange_liquidation_pseudocode.md). The Solidity function name is still unknown.

The getter reads the position from mapping slot 10 and its instrument from mapping slot 7. The packed instrument parameter at bits 120..183 of the instrument's second word is a maintenance rate scaled by `10^18`. At the pinned block it is `476041580087574` for instrument 0 and `481304050180130` for instrument 1. For the sampled states, the calculation is:

```text
base = entryPrice - floor(entryPrice / leverage)   if long
base = entryPrice + floor(entryPrice / leverage)   if short
adjustment = floor(base * maintenanceRate / 10^18)
liquidationPrice = base + adjustment                if long
liquidationPrice = base - adjustment                if short
```

Every predicted value matches its archived call exactly. For example, position 1,394,473 is long with entry 809,525 and leverage 100. Its base is 801,430, its adjustment is 381, and the getter returns 801,811. A synthetic Oracle midpoint of 801,811 liquidates it; 801,812 returns `NotLiquidatable()`. Position 1,394,060 is short with entry 235,015 and leverage 33. Its base is 242,136, its adjustment is 116, and the getter returns 242,020. That price liquidates it; 242,019 does not.

The archived outputs and storage words are saved in [the raw getter capture](../../artifacts/exchange_liquidation/pinned_price_getter.json). Run `atlas_exchange_liquidation_price.py` to verify them offline, or `PAPERTRADE_ARCHIVE_RPC=... python3 scripts/atlas_exchange_liquidation_price.py --capture` to recapture. The observed formula covers two instrument rates and sampled positions at one block. Overflow handling, zero leverage, other instrument settings, and the exact function name remain open.
