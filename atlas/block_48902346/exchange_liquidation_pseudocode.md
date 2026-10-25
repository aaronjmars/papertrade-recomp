# Exchange liquidation at HyperEVM block 48,902,346

`liquidate(uint256)` hashes to the live selector `0x415f1240`, appears in the pinned public ABI fixture, and is exercised by the saved local fork probes. This is an evidence-backed interface name, not recovered original source.

The [local probe ledger](../../artifacts/exchange_liquidation/pinned_local_probes.json) executes `liquidate(uint256)` on an archive-backed Anvil fork at the pinned block. The HyperCore BBO read precompile is replaced with a fixed two-word return value for each read-only probe. Four positions from the sampled open ledger are active in the archive state. The [compact behavior ledger](exchange_liquidation_behavior.json) records their one-unit price boundaries.

| Position | Side | Entry price | Leverage | Success boundary | Adjacent failure |
|---|---|---:|---:|---:|---:|
| 1,394,473 | Long | 809,525 | 100 | 801,811 is the highest successful price | 801,812 |
| 1,394,058 | Long | 235,015 | 50 | 230,425 is the highest successful price | 230,426 |
| 1,394,062 | Long | 809,325 | 100 | 801,613 is the highest successful price | 801,614 |
| 1,394,060 | Short | 235,015 | 33 | 242,020 is the lowest successful price | 242,019 |

Each adjacent failure returns selector `0xddeb79ba`, the exact hash of `NotLiquidatable()`. An inactive position ID returns `0x94e88a21`, the exact hash of `PositionNotOpen()`. All four success probes emit `Liquidated` with the tested price and position ID, clear bit 240 of the second position word, and emit fee fields equal to 1% of the stored margin each at the pinned rate. The [fee-effect replay](exchange_fee_effects.md) isolates slot 25 and checks the general integer split for two active positions. This is a checked set of boundaries, not a general liquidation formula.

For position 1,394,473 at a synthetic midpoint of 800,000, `liquidate(id)` and `liquidateBatch([id])` produce identical storage changes across Exchange, Tokenomics, and PAPER. Their ordered logs also match after removing one extra batch summary log. This supports a shared one-position settlement path for the tested case. The other three price boundaries were checked through the single-position entrypoint only.

The [batch branch probes](exchange_batch_branches_behavior.json) support this sampled control flow:

```text
completed = 0
for id in requestedIds:
    if the stored position is inactive: continue
    read the instrument midpoint, once per distinct instrument in the tested arrays
    if the position is outside its liquidation price boundary: continue
    settle and deactivate the position
    completed += 1
emit LiquidationBatchProcessed(requestedIds.length, completed)
return completed
```

An empty array succeeds with `(0,0)`; an inactive or ineligible ID is skipped; a duplicate eligible ID is settled once. Two eligible IDs settle in input order. These are observed branch outcomes, not a complete recovery of the source loop or its cache implementation.

The public HyperEVM RPC and the archive RPC return the same pinned block hash but differ by the active bit of position 1,394,473 at the same storage slot. The archive-backed local fork matches the archive word; a public-RPC fork does not. The crosscheck is saved in the probe ledger. A block hash match alone is insufficient to establish state fidelity for this position.

The probes use synthetic BBO values and never send a transaction. They do not prove live liquidation eligibility for other positions or the meaning of every settlement field. The 26 archived direct batches contain 67 real liquidations and two price-boundary skips; two separately saved nested batches contain six liquidation events. The sampled historical and local checks support the stated threshold formula, while other inputs and branches remain open.
