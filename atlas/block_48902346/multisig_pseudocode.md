# Multisig reconstruction at block 48,902,346

Runtime: `0x696292762fd5ac3677a45edbe54eaece4194d1f6`, Solidity 0.8.24. All 13 runtime selector names now have exact hash matches and are recorded in the machine evidence. This is a behavior reconstruction, not recovered source. [Machine evidence](multisig_behavior.json) comes from pinned getters, raw storage, historical receipts, and read-only EVM probes. [Historical replays](multisig_replays.json) cover all 13 observed interactions after creation.

## Storage and interface

```text
slot 0: signerOne
slot 1: signerTwo
slot 2: signerThree
slot 3: epoch
slot 4: transactionCount
slot 5: transactions mapping(uint256 => Transaction)
        field 0: destination address
        field 1: value in wei
        field 2: dynamic calldata bytes
        field 3: submitter address
        field 4: signer epoch at submission
        field 5: status, 0 pending, 1 executed, 2 revoked
```

`requiredConfirmations()` returns the constant `2`. Three signer addresses are stored, so a transaction uses its submitter and a different current signer. `signerOne()`, `signerTwo()`, `signerThree()`, `epoch()`, and `transactionCount()` read the slots above. `isSigner(address)` compares the argument against the three current signer slots. `transactions(index)` returns the six record fields.

## Core pseudocode

```text
transactionHash(index):
    require index < transactionCount
    tx = transactions[index]
    return keccak256(abi.encode(
        block.chainid, address(this), index, tx.destination,
        tx.value, keccak256(tx.data), tx.epoch
    ))

submitTransaction(destination, value, data):
    require isSigner(msg.sender)
    index = transactionCount
    transactionCount += 1
    transactions[index] = Transaction(destination, value, data,
                                      msg.sender, epoch, pending)
    emit TransactionSubmitted(index, msg.sender, destination,
                              value, data, transactionHash(index))
    return index

confirmAndExecute(index, expectedHash):
    require isSigner(msg.sender)
    require index < transactionCount
    tx = transactions[index]
    require tx.status == pending
    require tx.epoch == epoch
    require msg.sender != tx.submitter
    require expectedHash == transactionHash(index)
    tx.status = executed
    (success, returnData) = tx.destination.call{value: tx.value}(tx.data)
    if not success: revert ExecutionFailed(returnData)
    emit TransactionExecuted(index, msg.sender, tx.destination,
                             tx.value, tx.data)
    return returnData

revokeTransaction(index):
    require isSigner(msg.sender)
    require index < transactionCount
    tx = transactions[index]
    require tx.submitter == msg.sender
    require tx.status == pending
    tx.status = revoked
    emit TransactionRevoked(index)

updateSigners(one, two, three):
    require msg.sender == address(this)
    require all three addresses are nonzero, pairwise distinct,
            and different from address(this)
    epoch += 1
    signerOne, signerTwo, signerThree = one, two, three
    emit SignersUpdated(one, two, three, epoch)
```

The `transactionHash` formula matched all seven pinned records. It binds the approval to chain 999, this multisig address, the transaction index, target, value, calldata hash, and submission epoch. The submitter and status are not in the hash. A signer change increases the current epoch and makes older pending records fail execution. A proposer can still revoke a pending record after an epoch change in the tested state.

## Evidence and limits

- Pinned state has three signers, epoch `1`, and seven stored transactions: five executed, one revoked, one pending. Raw storage and `transactions(index)` agree on all six fields for every record.
- Every observed post-creation interaction was replayed from the previous block with original block metadata. All 13 call skeletons, event payload sets, and storage write sets matched the historical transaction.
- A direct submit from a signer succeeded; an outsider was rejected. A pending transaction executed from either other signer, while its submitter and an outsider were rejected. Wrong hash, invalid index, completed status, and stale epoch all produced distinct revert selectors.
- The EVM writes `executed` to the transaction's status slot before the external call. A simulated failure in the target timelock call was wrapped by `ExecutionFailed(bytes)` and left no net storage writes.
- `updateSigners` succeeded only as a self-call. Zero, repeated, or self signer addresses were rejected. Reapplying the same valid signer set still increased the epoch.
- All four event signatures reproduce their exact observed topic hashes: `SignersUpdated`, `TransactionSubmitted`, `TransactionExecuted`, and `TransactionRevoked`. Ten multisig error selectors were exercised. The canonical name of selector `0x137b4559`, observed when a submitter tries to confirm their own transaction, is still unknown.

The simulated calls did not send transactions or change pinned state. Unobserved branches, including target calls with nonzero native value and unusual dynamic calldata, still need independent checks.
