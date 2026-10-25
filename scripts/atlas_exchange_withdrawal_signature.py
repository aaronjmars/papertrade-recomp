#!/usr/bin/env python3
"""Rebuild every saved signed Core withdrawal EIP-712 hash and nonce call."""

import collections
import json
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_exchange_withdrawal_trace_corpus import build as build_withdrawal_corpus


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "exchange_withdrawal_signature_behavior.json"
EXCHANGE_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
EXCHANGE_PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION_PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SESSION_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
ECRECOVER = "0x" + "0" * 39 + "1"
WITHDRAW = "0x8d09f23f"
NONCE = "0xb002b9fa"
SIGNER = "0xd45167d0"
TYPEHASH_GETTER = "0x0b4c3a82"


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def words(data, selector=None):
    if selector is not None:
        assert data[:10].lower() == selector
        data = "0x" + data[10:]
    assert data.startswith("0x") and len(data[2:]) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def encoded(values):
    return "".join(f"{value:064x}" for value in values)


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    typehashes = json.loads((ATLAS / "session_typehash_behavior.json").read_text())
    session = json.loads((ATLAS / "session_key_behavior.json").read_text())
    corpus = build_withdrawal_corpus()
    assert typehashes["pin"] == session["pin"] == corpus["pin"] == manifest["block"]
    assert typehashes["block_hash"] == session["block_hash"] == corpus["block_hash"] == manifest["block_hash"]
    assert session["address"].lower() == SESSION_PROXY
    assert session["implementation"].lower() == SESSION_IMPL
    assert session["selector_reconstructions"][NONCE] == "consumeNonce(address,uint256,uint64)"
    getter = typehashes["constant_getters"][TYPEHASH_GETTER]
    type_string = getter["verified_type_string"]
    assert type_string == "WithdrawToCore(address user,uint256 amount,uint256 nonce,uint64 deadline)"
    keccak = Keccak()
    typehash = keccak(type_string.encode())
    assert "0x" + typehash.hex() == getter["pinned_return"]
    domain = bytes.fromhex(session["domain_separator"][2:])
    assert len(domain) == 32

    traces = {}
    rows = []
    for entry in corpus["calls"]:
        tx = entry["tx"]
        path = ROOT / entry["trace"]
        if tx not in traces:
            traces[tx] = (path, json.loads(path.read_text()))
        assert traces[tx][0] == path
        root = traces[tx][1]
        candidates = [call for call in descendants(root)
                      if call.get("type") == "DELEGATECALL"
                      and call.get("to", "").lower() == EXCHANGE_IMPL
                      and call.get("input", "")[:10].lower() == WITHDRAW
                      and int(call["input"][10:74], 16) == int(entry["user"], 16)
                      and int(call["input"][74:138], 16) == int(entry["raw_amount_6_decimals"])]
        assert len(candidates) == 1, (tx, len(candidates))
        exchange = candidates[0]
        assert not exchange.get("error") and exchange.get("from", "").lower() == EXCHANGE_PROXY
        user, amount, nonce, deadline, v, r, s = words(exchange["input"], WITHDRAW)
        assert user < 2**160 and amount > 0 and nonce < 2**256 and deadline < 2**64
        assert v in (27, 28) and r > 0 and s > 0
        struct_hash = keccak(typehash + bytes.fromhex(encoded((user, amount, nonce, deadline))))
        digest = keccak(b"\x19\x01" + domain + struct_hash)

        session_calls = [call for call in descendants(exchange)
                         if call.get("to", "").lower() == SESSION_PROXY]
        assert len(session_calls) == 2
        nonce_call, signer_call = session_calls
        assert nonce_call["type"] == "CALL" and not nonce_call.get("error")
        assert signer_call["type"] == "STATICCALL" and not signer_call.get("error")
        assert nonce_call["from"].lower() == signer_call["from"].lower() == EXCHANGE_PROXY
        assert words(nonce_call["input"], NONCE) == [user, nonce, deadline]
        assert words(signer_call["input"], SIGNER) == [int.from_bytes(struct_hash, "big"), v, r, s]
        assert len(signer_call.get("calls", [])) == 1
        delegated = signer_call["calls"][0]
        assert delegated["type"] == "DELEGATECALL" and delegated["to"].lower() == SESSION_IMPL
        assert delegated["input"] == signer_call["input"] and not delegated.get("error")
        precompiles = [call for call in descendants(delegated)
                       if call.get("type") == "STATICCALL" and call.get("to", "").lower() == ECRECOVER]
        assert len(precompiles) == 1
        precompile = precompiles[0]
        assert not precompile.get("error")
        assert precompile["input"].lower() == "0x" + digest.hex() + encoded((v, r, s))
        assert int(precompile["output"], 16) == int(delegated["output"], 16) == int(signer_call["output"], 16) == user
        rows.append({
            "tx": tx, "block": entry["block"], "trace": entry["trace"],
            "evidence_tier": entry["evidence_tier"],
            "user": entry["user"], "raw_amount_6_decimals": str(amount),
            "nonce": str(nonce), "deadline": deadline,
            "struct_hash": "0x" + struct_hash.hex(),
            "digest": "0x" + digest.hex(),
            "recovered_signer": entry["user"],
        })
    tiers = dict(sorted(collections.Counter(row["evidence_tier"] for row in rows).items()))
    assert len(rows) == corpus["matched_call_count"] == 103
    assert tiers == corpus["evidence_tier_counts"]
    assert len({(row["user"], row["nonce"]) for row in rows}) == len(rows)
    return {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_selector": WITHDRAW, "nonce_selector": NONCE, "signer_selector": SIGNER,
        "typehash_getter": TYPEHASH_GETTER, "type_string": type_string,
        "typehash": "0x" + typehash.hex(),
        "domain_separator_at_pin": "0x" + domain.hex(),
        "matched_call_count": len(rows), "distinct_transaction_count": len(traces),
        "distinct_user_count": len({row["user"] for row in rows}),
        "distinct_user_nonce_count": len({(row["user"], row["nonce"]) for row in rows}),
        "evidence_tier_counts": tiers,
        "checks": ["type string hashes to pinned SessionKeyManager typehash getter",
                   "withdrawal user, nonce and deadline equal consumeNonce calldata",
                   "recomputed struct hash equals SessionKeyManager signer calldata",
                   "recomputed EIP-712 digest and signature equal ECRECOVER calldata",
                   "ECRECOVER, delegatecall and signer return the withdrawal user"],
        "calls": rows,
        "limits": ["These are 103 selected successful calls, not every historical signed withdrawal or failed attempt.",
                   "The 99 call-only traces lack saved transaction storage diffs; withdrawal_nonce_history.json separately checks their block-boundary nonce bits.",
                   "The EIP-712 domain separator is pinned; a changed domain at other blocks is not reconstructed here."],
    }


def verify():
    result = build()
    assert json.loads(OUT.read_text()) == result
    print(result["matched_call_count"], "signed withdrawal hashes and ECRECOVER inputs matched")
    return result


if __name__ == "__main__":
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(result["matched_call_count"], "signed withdrawal hashes and ECRECOVER inputs matched")
