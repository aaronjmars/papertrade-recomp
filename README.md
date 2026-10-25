# Papertrade - Bytecode Analysis

Independent security and transparency research on the Papertrade contract suite deployed on HyperEVM (chain 999). The main pin is block **48,902,346** (2026-10-18 21:02:21 UTC, hash `0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab`), with a second pin at block **49,265,286** (2026-10-23) for the code that is live after the contract-set-2 upgrade.

Main contracts at the first pin:

| Contract | Address |
|---|---|
| Exchange (proxy) | `0x6cd5661646289fb6e65ea5c032310fded797d0a2` |
| SessionKeyManager (proxy) | `0x8326eb8896e358717f10502ec73ce8d28e37b108` |
| Tokenomics (proxy) | `0x75174549dbbd44497d31a47e2e2d7406408d63d9` |
| Oracle (proxy) | `0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e` |
| Staking (proxy) | `0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016` |
| PAPER token (proxy) | `0xe40f17915daa230324030003a197cdaef2261c0e` |
| BatchExecutor (proxy) | `0x233ff29b239abc1d7748605da9b205c3e008626e` |
| ProxyAdmin | `0xe79c91cc682f1bb401a9cab74c900470190f0f8f` |
| Timelock | `0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f` |
| Multisig | `0x696292762fd5ac3677a45edbe54eaece4194d1f6` |

The full list (25 addresses, plus 22,586 user deposit proxies and the older contract sets from the same deployer) is in the [manifest](atlas/block_48902346/manifest.json) and the [deployer scope check](atlas/block_48902346/deployer_scope.md).

## What this is

A reconstruction of the suite's behavior, derived from its publicly deployed bytecode and its public transaction history. It maps selectors, storage layout, events and errors, and checks the important paths against archived traces and exact-runtime local replays. It is intended for security review, education, and interoperability research.

## What this is not

- Not the original source code. Function names, storage names, pseudocode and structure are inferred and may differ from the authors' implementation. Each name records how it was recovered (selector hash match, public ABI, audit report text, or unnamed).
- Not affiliated with, endorsed by, or reviewed by Papertrade or its auditors.
- Not an audit or a security certification. The checks are sampled and scoped, and their limits are written down next to each result. Do not deploy or rely on this code.

## Method

1. Runtime and creation bytecode, storage, logs, receipts and traces retrieved from chain at fixed blocks, through an archive HyperEVM RPC and the public `rpc.hyperliquid.xyz/evm` endpoint, plus public HyperCore `info` API reads for the Core side. Every saved response is in `artifacts/`.
2. Decompiled with Heimdall 0.9.2 and Panoramix 0.6.1 for hints only. Decompiler output is kept in `atlas/block_48902346/decompiled/` and is not treated as trusted.
3. Selector names checked by Keccak hash against public signature registries (OpenChain), public ABI fixtures, and the public [Guardian audit report](https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/).
4. Behavior checked with Foundry 1.8.5 (`forge`, `anvil`, `cast`): exact deployed runtimes replayed locally against archived prestates, with storage writes, logs and return data compared to what happened on chain.
5. Manually annotated to document function behavior and storage layout.

## Disclosure

No outsider-exploitable issues were found in the checked paths. The open findings are privileged-role and governance risks (a market pause that freezes the price and cannot be undone, 1-of-2 multisigs on the older contract sets), liquidity limits, and small amounts of user funds left uncredited after failed HyperCore sends, a live case of an issue Guardian's audit already lists as an accepted risk. They are written up in [FINDINGS.md](FINDINGS.md) and [AUDIT.md](AUDIT.md), with a correction log in the [23 October risk review](RISK_REVIEW_2026-10-23.md).

The team was not contacted before release because Papertrade has no security channel (no security contact, security.txt, or bug bounty program).

## Contact / Takedown

If you are the contract author and have concerns about this publication, contact me on X at [@aaronjmars](https://x.com/aaronjmars). I will respond promptly.

## Repository layout

- [ATLAS.md](ATLAS.md): start here. Pinned contracts, reconstructed behavior, evidence strength, reproduction steps, and open paths.
- [FINDINGS.md](FINDINGS.md), [AUDIT.md](AUDIT.md), [REPORT.md](REPORT.md): findings, the scoped audit workpaper, and an accounting review.
- [NEXT.md](NEXT.md): open work, in priority order.
- `atlas/`: per-pin bytecode, selector and storage maps, behavior ledgers, pseudocode, and coverage inventory.
- `artifacts/`: saved traces, receipts, storage diffs, log queries, and local replay outputs.
- `scripts/`: capture, reconstruction, replay, and offline verification scripts (Python, with Foundry for local replays).
- `recovery/`: a draft governed recovery for the two uncredited deposits, tested locally only. No live action was taken.

## Verify

From the repository root:

```sh
python3 scripts/atlas_verify.py
```

The verifier re-checks all saved evidence offline, without any RPC credential, in about a minute. It needs Python 3 and a Keccak-256 backend (OpenSSL, `pip install pycryptodome`, or Foundry's `cast`). [CI](.github/workflows/atlas.yml) runs the same command on a clean Ubuntu checkout with pinned Python and Foundry versions.

Capture and some replay scripts need network access: `PAPERTRADE_ARCHIVE_RPC` (an archive HyperEVM RPC URL), `PAPERTRADE_RPC_URL` (optional, current-state RPC), and `ETHERSCAN_API_KEY` (explorer API). Heimdall is only needed to regenerate decompiler hints (`HEIMDALL` or `heimdall` on `PATH`). Credentials are read from the environment and are not part of this repository.

## License and third-party content

Code and documentation are released under the [MIT License](LICENSE). On-chain data is public. `artifacts/guardian_papertrade_report.html` and `artifacts/papertrade_home.html` are saved copies of public third-party web pages, kept unchanged as cited evidence; their content belongs to their owners.
