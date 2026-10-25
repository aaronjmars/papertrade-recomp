# Papertrade live accounting assessment

**Result, 18 October 2026:** The deployed Exchange and Tokenomics runtime bytecode shows the H-02, M-02, and M-04 accounting corrections in the tested paths. Three real queued wins, two real solvent wins, a controlled queue-live liquidation replay, a real queue harvest, and staker distribution replays did not show a second allocation of LP value. This is a scoped bytecode and transaction assessment, not a complete audit or proof of overall solvency.

## Chain and code identity

- Chain: HyperEVM, chain ID 999. Exchange proxy: `0x6cd5661646289fb6e65ea5c032310fded797d0a2`. Tokenomics proxy: `0x75174549dbbd44497d31a47e2e2d7406408d63d9`.
- Exchange implementation: `0x0f3febfc94876b0c895f7acecdc8f5c863b549ee`, runtime SHA-256 `2f2e20ca683b70511fe62178b8090c93df24208b13dbdfa6407f38946fcef0b1`.
- Tokenomics implementation: `0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f`, runtime SHA-256 `ed9d18151a9365c347ac7a9da7e83b53ecedac235d9e67c4b2699503a6bd4a97`.
- The proxy implementation slots and runtime hashes match at block 48,170,000 (12:56 UTC, before the 14:00 trading launch), at queued-win block 48,173,881, and at block 48,901,469. The same hashes appear in the latest capture across blocks 48,902,346 to 48,902,351. This supports the Guardian remediation condition that the corrected code was in place before activation. It does not establish a source-code match or rule out a temporary intervening upgrade.
- The full capture also includes Oracle, Staking, BatchExecutor, governance contracts, and the linked `PaperMathLib` runtime. See [snapshot](artifacts/20261018T210221Z_block48902346/snapshot.json) and [historical identity reads](artifacts/historical/accounting_states.json).
- At every sampled queue-empty block, the Exchange `lpBankrollAvailable()` getter exactly equals the Tokenomics signed LP cursor, including before and after queue harvest and at the positive-surplus block. While the real queue was live, spendable LP bankroll was zero. These are point-in-time accounting checks, not a continuous ledger proof.

## Findings

| Check | Evidence | Result |
|---|---|---|
| H-02, queued wins debit LP equity | At blocks 48,173,881, 885, and 887, each queued win added a claim of 7.623942182351823589 USD and passed that exact amount to `onCloseBatch`. Tokenomics signed `trackedLpUsd` fell by the same amount each time, to -22.871826547055470767 USD. The queue harvest at block 48,173,890 cleared all three claims and did not debit the cursor again. | Fix observed in all three actual queued wins. |
| M-04, solvent win fee is included in LP debit | A 1.014451343462700068 USD winner with a 0.020289026869254001 USD fee and a 52.361676010080092657 USD winner with a 1.047233520201601853 USD fee each passed the full gross adjusted win to `onCloseBatch`. The Tokenomics storage delta matches that gross debit, with the mixed batch's losing-position credit added separately. | Fix observed in two actual solvent wins. |
| M-02, queue-live liquidation credits the full margin | A successful real liquidation of 50 and 10 USD of margin was replayed against its preceding block. Baseline `onLoss` credited 49 and 9.8 USD to LP and reserved 1.2 USD in fees. Changing only Exchange storage slot 18 (`totalQueued`) to 1 wei for a read-only trace caused `onLoss` to credit the full 60 USD and move 60 USD into `sideBucket`, with fees waived. | Correct queue branch observed in a controlled replay. No natural queue-live liquidation occurred in the nine-second queue interval examined. |
| Staker allocation during a real queue | A read-only `pushStakerFees()` call at block 48,173,887 returned zero LP excess and made no Exchange or Tokenomics storage change. In a second replay against the same valid queue, changing only the Tokenomics LP cursor to create a 100 USD surplus added exactly 100 USD to the queue, debited the cursor by 100 USD, and gave no immediate balance credit. | No phantom distribution in the observed state; the queue branch also preserves the synthetic surplus liability. |
| Staker allocation when LP exceeds its cap | At block 48,899,300, the cursor exceeded the 5 million USD cap by 2,056.911227408759981977 USD. A read-only push distributed that exact LP excess plus 70.393845681577034461 USD already in the staker fee reserve, for 2,127.305073090337016438 USD total. It reduced the LP cursor by only the LP excess and cleared the fee reserve. With a synthetic 1 wei queue marker, the same total became a queue liability instead of an immediate balance credit. | The tested distribution separates earned LP excess from already reserved fees. The separate valid launch-queue replay tests the queue path with real queue nodes and an artificial positive LP cursor. |

The [offline verification output](artifacts/historical/verification.json) records the exact integer amounts. Raw receipts, call traces, and state diffs are under [`artifacts/historical`](artifacts/historical); the controlled replay parameters are in the [replay manifest](artifacts/historical/replays/manifest.json). All dollar values use 18 decimals in contract accounting.

## Method and limits

The assessment uses EIP-1967 proxy slot reads, exact runtime hashes, HyperEVM archive `debug_traceTransaction` receipts and storage diffs, and read-only `debug_traceCall` state overrides. Heimdall Yul output was used only to navigate selectors and storage; its control-flow reconstruction is incomplete and is not treated as evidence. The accounting assertions are executable in [`verify.py`](scripts/verify.py).

The tests establish behavior for the sampled transactions and controlled branch replays. They do not prove every reachable state, every fee or debt-funded path, the correctness of the entire Staking contract, or the amount of USDC in the HyperCore account at every historical block. No natural queue-live liquidation or queue-live positive-surplus staker push occurred in the short launch queue interval examined; those branches were replayed with single-slot overrides. A complete solvency proof would need a full ledger reconstruction, a valid queue plus liquidation fork test, and economic tests against the live midpoint oracle. Guardian lists midpoint manipulation and distribution without reserving unrealized winning PnL as accepted protocol risks; these fixes do not remove those risks. See the [Guardian report](https://guardian.security/portfolio/papertrade/protocol-review-2026-10-09/) and [Hyperliquid HyperCore interaction documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore).

## Reproduce

Python 3, `cast`, and an archive HyperEVM RPC endpoint are required. Set `PAPERTRADE_ARCHIVE_RPC` in the environment. `capture.py` uses the official public RPC for a fresh runtime snapshot. The archive RPC URL is never written to an artifact.

```sh
python3 scripts/capture.py
python3 scripts/historical_state.py
python3 scripts/scan_queue.py 48173500 48175000
python3 scripts/trace.py \
  0x3bc7029ee0d72c5dbacfb74dddc183ddb6206adca6ed702014eb90c28cf2d39e \
  0xc7ba4aaf1bdda8e24c2c8a228e315f39a879e7c9c87786eb260fa07c09b99940 \
  0x1fc54a082055d35c0b79b6fc5f6c2a7004840531f5bcb9b6ec4450a93be2384f \
  0x20ee69d9f4191bff17d45a850a584d5803ca477986fd1684af985765d64d794b \
  0x4214fa14d9c5bf46fade1c7f3ca8d242baefaa52426395b1840f43b626ee8a99 \
  0xe3a26c590c7b0be9e26e25b2e8fdf797be800b92131c229b5148c7405f69e33d \
  0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5
python3 scripts/replay.py
python3 scripts/verify.py
```

`verify.py` checks the saved artifacts without network access. A later upgrade that changes the runtime hash will make its identity check fail, prompting a fresh assessment.

## Addendum, 23 October 2026: corrected scoped review

The second-pass ledger has 92 rows across eight workstreams. The [four-area risk review](RISK_REVIEW_2026-10-23.md) records the latest settlement, liquidation, session-key, batch, upgrade and older-suite checks. Its main correction is that `SQ-L2-02`, the alleged repeatable debt-funded payout mint, was a false positive from a saved prestate that omitted queue pointers. The corrected exact-runtime replay consumes queued credit on debt open, restores the claim on a same-quote close, pays the existing queue once, and rejects a second debt open. The earlier 3,237.31 USDC gain and 20,000 USDC claims excess are not valid loss estimates. See the [corrected sequence ledger](atlas/block_48902346/live2_sequences.md).

The accounting identity still excludes the Exchange side bucket, which is an earmark of the LP bankroll rather than another claim. Two deposits totaling 62.150916 USDC remain uncredited at the latest checked head. Large older-suite internal books remain unclassified as real claims or synthetic balances. Tested signature and nonce boundaries held; batch-level success does not guarantee every inner trade succeeded. No external-user drain or large current-pool loss was established in these checked paths.
