# Exchange gain and loss close fees

The [mixed-close behavior ledger](exchange_negative_close_fee_behavior.json) replays a historical four-action batch at block 48,901,631. It contains one profitable close, one losing close, a signed Core withdrawal, and a staking action. The transaction was second in its block. The replay restores its saved transaction prestate, the exact historical HyperCore BBO and balance responses, and the target block timestamp and base fee. Its baseline matches all 17 receipt logs and every contract state change. Gas balance bookkeeping differs because the local call is a trace rather than a mined transaction.

Ten read-only cases change Exchange fee slots 23, 24, and 25. Each close keeps the same adjusted PnL. For these two positions:

```text
positive close fee = floor(adjusted positive PnL * slot24 / 10^18)
negative close fee = floor(abs(adjusted negative PnL) * slot23 / 10^18)

positive user credit = margin + adjusted positive PnL - fee
negative user credit = margin - abs(adjusted negative PnL)
staker fee = floor(fee / 2)
developer fee = fee - staker fee

negative Tokenomics tracked LP credit = abs(adjusted negative PnL) - fee
negative Tokenomics PAPER mint basis = tracked LP credit
```

| Rate case | Positive fee, 18 decimals | Negative fee, 18 decimals | Negative Tokenomics LP credit |
|---|---:|---:|---:|
| Historical 2% rates | 1.047233520201601853 | 0.667717703793007511 | 32.718167485857368080 |
| Slot 23 zero | 1.047233520201601853 | 0 | 33.385885189650375591 |
| Slot 23 one unit | 1.047233520201601853 | 0.000000000000000033 | 33.385885189650375558 |
| Slot 23 three units | 1.047233520201601853 | 0.000000000000000100 | 33.385885189650375491 |
| Slot 23 4% | 1.047233520201601853 | 1.335435407586015023 | 32.050449782064360568 |
| Slot 24 zero | 0 | 0.667717703793007511 | 32.718167485857368080 |
| Slot 24 4% | 2.094467040403203706 | 0.667717703793007511 | 32.718167485857368080 |
| Slot 25 zero | 1.047233520201601853 | 0.667717703793007511 | 32.718167485857368080 |

For the loss close, the user receives the same `margin - loss` amount under every slot-23 change. The Exchange fee accumulator changes, and the `onCloseBatch(address,uint256,uint256,uint256)` call to Tokenomics passes `loss - fee` as both mint basis and tracked LP credit. This identifies the fee's source in EVM accounting: it reduces the LP share of the trader loss. The PAPER mint and Tokenomics tracked totals change with that basis. The loss fee is not an extra debit from the trader's returned margin.

The [raw local probes](../../artifacts/exchange_negative_close/local_probes.json), [original transaction prestate](../../artifacts/exchange_negative_close/original_prestate.json), and [prior-block differences](../../artifacts/exchange_negative_close/prestate_differences.json) preserve the replay inputs. Run `python3 scripts/atlas_exchange_negative_close_fee.py` from the workbench root to verify them offline. To recapture, start an archive-backed Anvil fork at block 48,901,630, set `PAPERTRADE_ARCHIVE_RPC`, and run `python3 scripts/atlas_exchange_negative_close_fee.py --local-rpc-url http://127.0.0.1:<port>`. The script applies the recorded earlier-transaction state changes, installs the two historical HyperCore responses, mines the target block locally, and captures ten cases.

This is one mixed batch with controlled local rate changes. The positive and negative formulas are established for these branches. Other close paths, changed rates on the live chain, and HyperCore settlement remain outside this replay.
