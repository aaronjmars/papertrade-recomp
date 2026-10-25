# Earlier multisig signer control

Both earlier governance multisigs have identical 2,713 byte runtime code at pinned block 48,902,346, with SHA-256 `4c8ecb8092028b3931dc3b8e2852278aa7f81ea0e8e4a418a4e0490d84e87bde`. The [pinned capture](../../artifacts/deployer_scope/pinned_capture.json.gz) contains both runtimes. A separate [raw slot capture](../../artifacts/deployer_scope/older_multisig_slots.json) reads slots 0 to 2 from each contract at the pin; these match the saved `signerOne()`, `signerTwo()`, and `transactionCount()` getters. Both have the same two signers and require one confirmation. Transaction counts are 240 and 1,299.

The [replay generator](../../scripts/atlas_older_multisig_control.py) checks the selector hashes and runs [two tests](../../artifacts/deployer_scope/older_multisig_control.t.sol) against the exact runtime, seeded with those pinned slots. The [result ledger](../../artifacts/deployer_scope/older_multisig_control_replay.json) records the runtime hash, test source hash, slot inputs, and passing cases. Each multisig produces the same result:

1. A direct `updateSigners(address,address)` call from signer one reverts, and an outsider cannot submit the self-call.
2. Signer one alone submits `submitTransaction(address(this),0,abi.encodeWithSignature("updateSigners(address,address)",newOne,newTwo),true)` successfully. Slots 0 and 1 change to the two new signers and the transaction count increases by one.
3. The original signer can no longer submit. The replacement signer can submit.

This confirms the signer eviction behavior in Guardian's saved report, [L-04](../../artifacts/guardian_papertrade_report.html#l-04), against both deployed runtimes. The Papertrade team accepted L-04 as a Low governance trust assumption. The self-call changes multisig signers immediately. Subsequent governed Exchange or ProxyAdmin actions still pass through the older timelocks' 60-second delay, as the [historical governance traces](older_governance.md) show. The replay does not show a historical signer eviction, signer compromise, or a new finding.

Run `PAPERTRADE_ARCHIVE_RPC=<archive URL> python3.12 atlas_older_multisig_control.py --capture` to refresh the raw slots, then `python3.12 atlas_older_multisig_control.py --run` for the Forge replay. `python3.12 atlas_older_multisig_control.py` verifies saved artifacts offline. The tests seed only the three direct slots and exercise this signer-change branch; other multisig transaction and error branches remain outside this local replay.
