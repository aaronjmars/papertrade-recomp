# Governance of the two earlier deployed suites

The [pinned archive verifier](../../scripts/atlas_older_governance.py) checks each earlier multisig, timelock, ProxyAdmin, and Exchange getter, every earlier proxy's EIP-1967 admin slot, and two historical schedule and execute pairs. Each earlier Exchange and ProxyAdmin is owned by its corresponding timelock. Each timelock is owned by its older multisig. The two older multisigs share identical bytecode and the same two pinned signers, `0x7ce50a614174a3b26b107f1f9866f88461820626` and `0x8cea98f6ab3004c762efaf3dfd54876d62912300`.

| Set | Multisig | Pinned required confirmations | Timelock | Pinned minimum delay | Pinned multisig transaction count |
|---|---|---:|---|---:|---:|
| Earlier 1 | `0x73a83d746c38865960583879bc29bb007a04eacf` | 1 of 2 signers | `0x69b4b92f02ff415e0c966686e00d2783b395d690` | 60 seconds | 240 |
| Earlier 2 | `0x324b0547039683c2df146421f3a76083ef130d27` | 1 of 2 signers | `0xd98adcb9a409e33a658c24e872f37357a85ca484` | 60 seconds | 1,299 |
| Newest suite control | `0x696292762fd5ac3677a45edbe54eaece4194d1f6` | 2 of 3 signers | `0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f` | 604,800 seconds | Separate [newest governance map](multisig_pseudocode.md) |

Both earlier historical pairs use `submitTransaction(address,uint256,bytes,bool)` (`0x684dbac7`) with the final flag set to `true`. The signerOne address above sends both the schedule and execute calls. The calldata's dynamic bytes exactly match the multisig's child call to its timelock. The timelock emits the same operation ID at schedule and execution. The schedule event's ready time is its block timestamp plus 60 seconds. The execution traces then call the corresponding Exchange's `reconcileSweepCredit(address,uint256)` through its proxy and installed implementation.

| Set | Schedule transaction | Execute transaction | Time between calls | Traced target |
|---|---|---|---:|---|
| Earlier 1 | `0x35fbba5264058d135fb58316b67d6d7cdd433b9449f6af73366ae231ee982411` | `0xa1f385df5db29fbd8c7c6404d05c0d81593f61c9c36d8a01262f50e3c4056d1b` | 63 seconds | First earlier Exchange, implementation `0x557c...` |
| Earlier 2 | `0x105b275683e663db0b1e018228b1e143ca7b161357dd2a51ef8caf207c68c419` | `0x2d5ec3ad25193d60f39165bee14fd84ba3da69ceb454d49aa6e016666d68ef92` | 115 seconds | Second earlier Exchange, pinned replacement `0x93a8...` |

This proves one signer historically scheduled and executed these two timelock operations after the stated delay. The pinned owner chain also gives the timelocks control of the older ProxyAdmins, whose addresses occupy all eight proxy admin slots in each set. This is a material governance difference from the newest suite, whose control path requires two signer confirmations and a seven-day timelock. It is not evidence that either signer is compromised or that every possible admin operation was executed. A [separate exact-runtime replay](older_multisig_control.md) proves that one signer can replace both older multisig signers immediately through a self-call. Other multisig branches and any timelock ownership changes before the pin remain outside this verification. A [separate archive trace](older_exchange_upgrade.md) establishes one governed upgrade to the second earlier Exchange, but a complete upgrade history remains open.
