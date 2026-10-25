# Bounded EVM asset inventory at block 48,902,346

The [capture](../../artifacts/deployer_scope/older_evm_assets.json.gz) and [offline verifier](../../scripts/atlas_older_evm_assets.py) cover 97 addresses: all 59 direct creations by the known deployer and all 38 user proxies from its two older factories. Archive calls at the pinned block read native HYPE and `balanceOf(address)` on all three PAPER token proxies. Each Staking proxy's storage slot 3 points to its corresponding PAPER proxy; the three token `decimals()` calls return 18. Each Staking `totalStaked()` getter matches its slot 5 word. The capture checks the block hash against the manifest.

| Set | Direct contracts | Older user proxies | Nonzero native HYPE accounts | Nonzero PAPER account | PAPER held by Staking | `totalStaked` slot 5 |
|---|---:|---:|---:|---|---:|---:|
| Earlier 1 | 19 | 33 | 0 | Staking `0xfe8f8d20a8e3b6221e93926e5a08a64354a45688` | 78,405,369.412664783977870135 | 78,405,369.412664783977870135 |
| Earlier 2 | 19 | 5 | 0 | Staking `0x546cb5afbb79dbf1bb70cd1bae5a37e508ed1fc4` | 49,241,878.5971534163183595 | 49,241,878.5971534163183595 |
| Newest direct creations | 21 | Not checked here | 0 | Staking `0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016` | 8,555,409,857.614638237952993078 | 8,555,409,857.614638237952993078 |

These are the only three nonzero PAPER `balanceOf` results among the 291 token-account calls. All 97 native HYPE balance reads return zero. The three Staking PAPER balances exactly match their pinned `totalStaked` storage words. This checks custody of the configured stake token at the pin; it does not test whether every user can unstake or whether reward and Exchange accounting is solvent.

Each Staking proxy's storage slot 4 points to `0x6b9e773128f453f5c2c60935ee2de2cbc5390a24`. A saved pinned `balanceOf` probe on that reward token address reverts, so it is outside this ERC-20 balance inventory. Other ERC-20 contracts, the newest factory's 22,586 user proxies, linked libraries and addresses created by other deployers are not scanned. HyperCore balances are separate from EVM balances; the [older proxy Core ledger](deployer_scope.md) and [older Exchange Core capture](deployer_scope.md) cover those accounts with their own evidence limits. The large Exchange `totalBalances()` values are internal 18-decimal accounting units, not proven redeemable USDC liabilities and not comparable to PAPER stake-token holdings.

Run `python3 scripts/atlas_older_evm_assets.py` from the repository root to verify the saved evidence offline. To refresh the capture, set `PAPERTRADE_ARCHIVE_RPC` to an archive HyperEVM RPC URL and run `python3 scripts/atlas_older_evm_assets.py --capture`.
