# PT-01 later status through HyperEVM block 49,002,272

The [saved snapshot](../../artifacts/pt01_postpin/status.json) checks the two PT-01 users after the audit pin at block 48,902,346. It uses the Hyperliquid mainnet archive JSON-RPC for EVM headers, logs, storage, calls, and proxy code, plus the public HyperCore info API for each proxy's non-funding ledger and current spot balance. The snapshot was captured on 2026-10-20 at 00:20:33 UTC; the EVM head was block 49,002,272 at 00:20:29 UTC.

| Check | Result at the saved read |
|---|---|
| Exchange sweep events for either user from block 48,902,347 through 49,002,272 | Zero `SweepRequested`, `Swept`, or `PendingSweepCleared` logs in one complete archive RPC query |
| `pendingSweepWord(address)` and raw mapping slot 33 | Both still equal the pinned pending words |
| Exchange EIP-1967 implementation slot | Still points to the pinned implementation `0x0f3febfc94876b0c895f7acecdc8f5c863b549ee` |
| Affected proxy code | Both current SHA-256 hashes equal the pinned deposit proxy runtimes |
| Each proxy's public non-funding Core ledger from the pin timestamp through the EVM head timestamp | Zero returned entries |
| Public current Core spot USDC | 50.050916 and 12.1 USDC, totaling 62.150916 USDC |

The unchanged pending words and zero matched sweep events show no sweep-based resolution through that EVM head. The Core API read shows the same USDC amounts still in the proxy spot accounts shortly after the head. This later snapshot does not change the pinned-block finding. It does not prove the exact transfer-gas rule, exclude a separate EVM credit without a sweep event, or establish any recovery after capture. The Core account state is not block-pinned or cryptographically proven by this capture, and the two APIs were read at slightly different times. An unchanged implementation slot does not prove there was no intervening upgrade and reversal.

Run `python3 scripts/atlas_pt01_postpin.py` to verify the saved snapshot offline. To refresh the later state, set `PAPERTRADE_ARCHIVE_RPC` to a Hyperliquid mainnet archive endpoint and run `python3 scripts/atlas_pt01_postpin.py --capture`. The script does not save the endpoint or its credential.

## Second read on 2026-10-20

A second [saved snapshot](../../artifacts/pt01_postpin/status_20261020_later.json) at HyperEVM block 49,050,036, captured at 13:23:33 UTC, repeats the same checks. The complete post-pin archive query still returns no matched sweep events for either user. Both pending storage words, proxy runtime hashes, and the Exchange implementation slot still match the pin. Both proxy non-funding Core ledgers have no returned post-pin entry, and the public current spot reads still total 62.150916 USDC. The Core balance reads were made after the EVM head and are subject to the same timing and public API limits as the first snapshot. `atlas_verify.py` checks both saved reads offline.

## Third read on 2026-10-20

A third [saved snapshot](../../artifacts/pt01_postpin/status_20261020_1703.json) at HyperEVM block 49,063,456, captured at 17:03:34 UTC, again finds the original Exchange implementation, both exact pending words, no matched post-pin sweep events or public Core ledger entries, and 62.150916 USDC across the two proxy spot accounts. The later [recovery preflight](../../recovery/preflight_20261020.json) at block 49,064,506 also confirms the two live spot-balance precompile values equal the public Core reads, the timelock owns both Exchange and ProxyAdmin, its minimum delay is now 86,400 seconds, and the proposed recovery storage slot is zero. These are read-only observations.
