# Deposit proxy runtime derivation at block 48,902,346

The [machine ledger](deposit_proxy_runtime_derivation.json) derives a 1,646 byte runtime and SHA-256 hash for each of the 22,586 successful factory CREATE2 deployments. The [runtime map](deposit_proxy_derived_runtime_map.json) lists every user, proxy address, and derived hash. `atlas_deposit_proxy_runtime_derivation.py` rebuilds both from saved inputs and checks them offline.

## Constructor and CREATE2 evidence

The historical factory deployment transaction `0xddf30f3f...` contains the full 1,889 byte CREATE2 initcode and its 1,646 byte returned runtime. The initcode has a fixed 1,825 byte creation body and two trailing ABI address words: the Exchange proxy address and the user. Its 179 byte constructor copies the fixed runtime bytes from initcode offset `0xb3`, then inserts the Exchange address at runtime word offsets `0x61` and `0xde` and the user address at `0x37b` and `0x3da`. The address occupies the low 20 bytes of each 32 byte word. The constructor uses code size, code copy, memory, arithmetic, and a call-value check. It has no storage, block, caller, or external-call opcode.

For every saved deployment, the recorded event user and factory address reproduce its observed proxy address with the CREATE2 formula:

```text
salt = keccak256(user as 20 bytes)
initcode = fixed creation prefix || abi.encode(user)
proxy = last20(keccak256(0xff || factory || salt || keccak256(initcode)))
```

The script independently repeats this calculation for all 22,586 records. Their addresses also match the factory internal CREATE2 rows and deployment events in the [event ledger](factory_event_deployments.json). Because all records match the same creation prefix plus their event user, the constructor predicts one runtime per user with only the two embedded user words changing.

The prediction matches the historical CREATE2 trace's complete returned runtime, all 41 fetched runtime SHA-256 hashes from the family sample, the complete fetched representative runtime, and a newly fetched runtime outside that sample. The historically used proxy is already one of the 41 family samples. Two read-only `eth_call` constructor simulations at the pin, for the first and last sampled users, return the exact predicted bytes. The resulting 22,586 runtime hashes are distinct. The representative runtime disassembly contains no `SELFDESTRUCT`, `DELEGATECALL`, or `CALLCODE` opcode.

This is a deployment-wide deterministic derivation, not 22,586 individual `eth_getCode` observations. It assumes ordinary EVM CREATE2 and code immutability semantics and that the 160-bit CREATE2 address matches are collision resistant. Only 42 deployed runtimes were fetched directly at the pin. The derivation establishes deployed code shape, not complete branch behavior of the proxy functions.

To recapture the two pinned creation simulations, set `PAPERTRADE_ARCHIVE_RPC` and run `python3 scripts/atlas_deposit_proxy_runtime_derivation.py --capture` from the workspace root. Run `python3 scripts/atlas_deposit_proxy_runtime_derivation.py` without the flag to regenerate both ledgers entirely from saved evidence.
