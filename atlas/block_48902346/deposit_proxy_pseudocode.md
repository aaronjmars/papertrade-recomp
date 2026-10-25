# User deposit proxy behavior at block 48,902,346

The [machine-readable behavior map](deposit_proxy_behavior.json) is derived from the pinned runtime, 17 read-only `debug_traceCall` probes, and one successful historical sweep. The historical proxy is among the 41 sampled family members; its only varying bytes encode its user address twice. The [constructor derivation](deposit_proxy_runtime_derivation.md) now predicts the exact runtime bytes and SHA-256 hash for all 22,586 recorded deployments from deterministic CREATE2 initcode and each event user. One additional unsampled runtime was fetched and matched. Thus 42 deployed runtimes were fetched directly at the pin, while the rest are bytecode-derived rather than individually observed.

## Callable interface

```solidity
address immutable user;
address immutable exchange;

function user() external view returns (address);
function exchange() external view returns (address);

function sweepAllToExchange(uint64 tokenId, uint64 spotAmount, uint64 perpAmount) external {
    require(msg.sender == exchange, "only exchange");
    uint256 total = uint256(spotAmount) + uint256(perpAmount) * 100;
    if (total > type(uint64).max) revert CoreAmountOverflow();

    if (perpAmount != 0) {
        CoreWriter.sendRawAction(
            abi.encodePacked(bytes4(0x01000007), abi.encode(perpAmount, false))
        );
    }
    if (total != 0) {
        CoreWriter.sendRawAction(
            abi.encodePacked(bytes4(0x01000006), abi.encode(exchange, tokenId, uint64(total)))
        );
    }
}

function withdrawStuckToken(address token, uint256 amount) external {
    require(msg.sender == user, "only user");
    require(amount != 0, "zero amount");
    (bool ok, bytes memory result) = token.call(
        abi.encodeWithSelector(0xa9059cbb, user, amount)
    );
    require(ok && (result.length == 0 || abi.decode(result, (bool))), "transfer failed");
    emit StuckTokenWithdrawn(user, token, amount);
}
```

The signatures and the `StuckTokenWithdrawn(address,address,uint256)` and `CoreAmountOverflow()` names reproduce the selector or topic hashes exactly. The pseudocode expresses tested behavior, not recovered Solidity source. The event indexes `user` and `token`; `amount` is data. The `user` and `exchange` getters return the constructor values embedded in runtime code, with no storage reads in the pinned traces.

The sweep calls the HyperCore `CoreWriter` at `0x3333333333333333333333333333333333333333` through `sendRawAction(bytes)`. [Hyperliquid's action format](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore) defines action 7 as USD class transfer `(uint64 ntl, bool toPerp)` and action 6 as spot send `(address destination, uint64 token, uint64 wei)`. The pinned perp probe sends action 7 with `toPerp = false`, then action 6 to Exchange with the computed total. An all-zero sweep succeeds without a CoreWriter call. Both overflow probes revert with `CoreAmountOverflow()` before a writer call.

The successful [historical transaction](../../artifacts/historical/0xd4ee56dd5d1e271b8fc142e340362d3ab1eede92a9810ab33de4d90a9f798257.calls.json) called a different proxy in the same normalized runtime family with `(tokenId=0, spotAmount=499900000000, perpAmount=0)`. Its CoreWriter call and emitted log carry the exact action 6 payload expected from the pseudocode. That log proves the action was enqueued by HyperEVM. It does not prove that HyperCore later delivered the funds.

For token rescue, a mock token returning true, a mock token returning no bytes, and an address with no code all produced a successful call and the same event. A mock token returning false reverted with `"transfer failed"`. This means a rescue call to a no-code address can emit `StuckTokenWithdrawn` even though no ERC-20 moved. This is a pinned, read-only simulation; no historical rescue transaction is saved. The function is restricted to the proxy's immutable user.

The [exact-runtime local replay](../../artifacts/deposit_proxy_local/replay.json) runs 19 assertion-bearing cases against the pinned 1,646-byte proxy code. It reproduces both getters, access checks, zero amount, true/no-return/no-code/false token responses, sweep payloads, zero sweep, and both overflow paths. It additionally checks that malformed 32-byte bool return data, short return data, and a reverting token all make rescue revert. A mock CoreWriter failure on either action makes the sweep revert; when the second action fails, the first action is reached but its storage effects roll back. Foundry's log recorder includes the first action even after the outer revert, so that recorded log is an execution trace, not a persisted transaction log. The local writer is a mock and does not establish HyperCore settlement.
