# Exchange direct withdrawal to HyperCore

The [direct-withdrawal behavior ledger](exchange_direct_withdrawal_behavior.json) reconstructs `withdrawToCore(uint256)` (`0x7f99545a`). The signature hashes exactly to the live selector. Its `uint256` argument was missed by the selector catalog's initial ABI inference; the successful branch, CoreWriter payload, event, and storage writes establish that it is a raw six-decimal withdrawal amount.

The `0x0810` HyperCore read is `coreUserExists(address)`, as identified by [Circle's independently pinned HyperEVM source](hypercore_user_exists_evidence.json). Its decoded boolean is 0 when the user does not exist on HyperCore and 1 when the user exists. Circle's separate integration specifies a one-USDC new-account fee in eight-decimal Core units. This names the external precompile; it is not Papertrade source. A separate public Core ledger capture below now verifies the fee field for one direct new-account withdrawal.

Nine read-only cases run on an archive-backed Anvil fork at pinned block 48,902,346. The local fork uses the HyperCore user-status and Exchange-balance responses captured from an earlier historical withdrawal. Two saved successful on-chain calls from the same Safe account verify the direct selector at earlier blocks. Four additional [port-free exact-runtime tests](../../artifacts/exchange_direct_status_local/replay.json) hold storage and amount fixed while changing the HyperCore status response or available user balance. The local replays never send a transaction to the live chain.

| Tested amount or condition | Result |
|---|---|
| Zero raw amount | `0x0a9e0180` (`NoCoreBalance()`), before a CoreWriter call |
| One raw unit or exactly 1,000,000 raw units | `0xad21c3fb`; the tested minimum is strictly greater than one USD |
| 1,000,001, 2,000,000, or 42,000,000 raw units | Successful CoreWriter call and `CoreWithdrawal` event |
| 43,000,000 raw units with this user's 43.915 internal USD balance | `0xa3b9a36c`, before a CoreWriter call |
| Last-withdrawal mapping overridden to the current block | `0x4f57ffae` |
| Mocked Exchange Core balance set to zero | `0x0a9e0180` (`NoCoreBalance()`) |

For the three successful cases, the event's Core amount is `rawAmount * 100`, matching the final eight bytes of the 100-byte CoreWriter payload. The event's internal debit is `(rawAmount + 1,000,000) * 10^12`, or one internal USD more than the amount sent. The user's balance mapping at base 9, total balances in slot 22, and treasury in slot 14 each fall by that debit. The user's last-withdrawal mapping at base 34 becomes the pinned block. The same-block override confirms a strict block guard.

The two archived direct calls came from Safe `0xa90f96b5fcd5bdc0aae788c0485786b0e546d950`, 245 blocks apart. Both emitted `CoreWithdrawal` and called CoreWriter with `rawAmount * 100`:

| Block | Raw amount | HyperCore user-status word | Internal debit | Safe balance mapping change |
|---:|---:|---:|---:|---:|
| 48,014,383 | 10,000,000 | 0 | `11 * 10^18` | `-11 * 10^18` |
| 48,014,628 | 1,581,398,913 | 1 | `1,581.398913 * 10^18` | `-1,581.398913 * 10^18`, clearing the slot |

In both transactions, Exchange treasury (slot 14) and total balances (slot 22) fall by the event debit, and the Safe's last-withdrawal mapping records the block. The second transaction's balance prestate equals the first transaction's poststate, and its full remaining balance is debited to zero. The zero value is omitted from the `prestateTracer` diff-mode `post` storage map; treating that omission as an unchanged slot would be wrong. In the controlled exact-runtime replay, status 0 charges one extra internal USD and rejects an exact-balance withdrawal with `0xa3b9a36c`. Status 1 charges no extra USD and accepts exact balance. Both successful branches debit the user balance, treasury, and total balances. These checks establish the sampled status branch under identical EVM storage and amount; other status values remain untested. The [signed withdrawal ledger](exchange_core_withdrawal.md) also contains both debit patterns. The three newly exercised raw revert selectors have branch evidence but no verified Solidity error names. The [public Core ledger capture](../../artifacts/audit_withdrawal_settlement/public_ledger.json) and [offline verifier](../../scripts/audit_withdrawal_settlement.py) match both direct Safe withdrawals to identical Exchange-side and recipient-side `spotTransfer` records. The first delivered 10 USDC with a 1 USDC fee; the second delivered 1,581.398913 USDC with zero fee. This supports delivery and explains the extra internal debit for these two calls, but does not identify the fee recipient or cover all direct withdrawals.

The [raw fork traces](../../artifacts/exchange_direct_withdrawal/local_probes.json), [full withdrawal event history](../../artifacts/exchange_core_withdrawal/full_history_event_query.json), and [behavior ledger](exchange_direct_withdrawal_behavior.json) contain the replay and historical evidence. Run `python3 scripts/atlas_exchange_direct_withdrawal.py` from the workbench root to verify them offline. To recapture, start a fresh archive-backed Anvil fork at block 48,902,346 and run `python3 scripts/atlas_exchange_direct_withdrawal.py --local-rpc-url http://127.0.0.1:<port>`. The script installs the two saved HyperCore responses before probing. The current Alchemy HyperEVM endpoint does not serve `eth_getProof`, so it cannot start a new Anvil fork; the port-free status tests run without an RPC fork.
