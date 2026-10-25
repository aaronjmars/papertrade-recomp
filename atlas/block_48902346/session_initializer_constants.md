# SessionKeyManager initializer strings at block 48,902,346

The archived deployment call to selector `0x747b8a1c` succeeded with `initialize(address,string,string,uint256,address)`, name `String`, and version `1`. The [exact-runtime replay](../../artifacts/remaining_initializers_local/replay.json) succeeds with those strings. It returns raw error `0xf50220aa` when the name is changed to `Name` or the same-length `StrinG`, or when the version is changed to `2`.

The [bytecode check](session_initializer_constants_behavior.json) identifies a constant table after the executable runtime's `INVALID` marker. It contains `keccak256("String")` at byte offset `0xe5f` and `keccak256("1")` at `0xdff`. On the fresh-state initializer path, `CODECOPY` loads those constants, `KECCAK256` hashes the supplied string bytes, and a mismatch jumps to a body returning `0xf50220aa`. The checked compare and mismatch instruction ranges are recorded in the behavior ledger.

This establishes the accepted name and version bytes on the tested fresh-state path. Initialized-state calls can revert earlier. Other owner, authorized-caller, and chain-ID values succeeded in sampled fresh-state replay, while the source declaration remains unavailable.

Reproduce offline with `python3 scripts/atlas_remaining_initializers_local.py` and `python3 scripts/atlas_session_initializer_constants.py`.
