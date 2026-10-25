# Exchange liquidation fee split at HyperEVM block 48,902,346

The [local replay ledger](exchange_fee_effects_behavior.json) isolates Exchange fee slots 23 to 25 on an archive-backed Anvil fork. Ten read-only `liquidate(uint256)` calls use synthetic HyperCore prices for two positions that are active in the archived pinned state. The fork's block hash, position active bit, and original fee words match the archive. Its unchanged-rate replay matches the earlier independent liquidation probe's ordered logs and contract storage changes exactly.

For the tested liquidation path, slot 25 alone controls the two `Liquidated` fee fields:

```text
totalFee = floor(position.margin * slot25 / 10^18)
stakerFee = floor(totalFee / 2)
devFee = totalFee - stakerFee

slot26.low128 += stakerFee
slot26.high128 += devFee
```

At the pinned rate of 2%, each field is 1% of margin. Zeroing slot 25 makes both fees zero; doubling it doubles both. Zeroing slot 23 or slot 24 leaves the tested long liquidation's ordered logs and storage changes identical to baseline. On a short position with margin `315340000000000000000`, setting slot 25 to one unit yields a total fee of 315 internal units. The staker field receives 157 and the dev field 158, proving the remainder goes to the second field. All ten event pairs and accumulator deltas match the formula.

The [raw fork traces](../../artifacts/exchange_fee_effects/local_probes.json) contain every mock price, changed rate, ordered log, and storage diff. Run `atlas_exchange_fee_effects.py` to verify them offline. To recapture, start a new Anvil fork at block 48,902,346 using `PAPERTRADE_ARCHIVE_RPC`, then run `atlas_exchange_fee_effects.py --local-rpc-url http://127.0.0.1:<port>` with the same archive variable set. The original local fork was stopped after capture.

The slot-25 dependence and rounding are proven for these two sampled positions under synthetic prices. Slots 23 and 24 may affect other paths. No saved historical transaction changed the three fee rates.
