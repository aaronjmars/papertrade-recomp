#!/usr/bin/env python3
"""Check sampled signed closes against the pinned EIP-712 Close type hash."""

import collections
import json
from pathlib import Path

from atlas_factory_events import Keccak


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "session_close_typehash_behavior.json"
EXCHANGE_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
EXCHANGE_PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION_PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SESSION_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
ECRECOVER = "0x" + "0" * 39 + "1"
CLOSE = "0x2792e706"
NONCE = "0xb002b9fa"
SIGNER = "0x7f608253"
GETTER = "0x208e24fc"


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
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    typehashes = json.loads((ATLAS / "session_typehash_behavior.json").read_text())
    session = json.loads((ATLAS / "session_key_behavior.json").read_text())
    assert graph["traces"] and typehashes["pin"] == session["pin"] == manifest["block"]
    assert typehashes["block_hash"] == session["block_hash"] == manifest["block_hash"]
    assert session["address"].lower() == SESSION_PROXY
    assert session["implementation"].lower() == SESSION_IMPL
    assert session["selector_reconstructions"][NONCE] == "consumeNonce(address,uint256,uint64)"
    getter = typehashes["constant_getters"][GETTER]
    type_string = getter["verified_type_string"]
    assert type_string == "Close(address user,uint256[] positionIds,uint256 nonce,uint64 deadline)"
    keccak = Keccak()
    typehash = keccak(type_string.encode())
    assert "0x" + typehash.hex() == getter["pinned_return"]
    domain = bytes.fromhex(session["domain_separator"][2:])
    assert len(domain) == 32

    rows = []
    for trace in graph["traces"]:
        path = ROOT / "artifacts" / trace["source_directory"] / (trace["source_stem"] + ".calls.json")
        root = json.loads(path.read_text())
        for exchange in descendants(root):
            if exchange.get("type") != "DELEGATECALL" or exchange.get("to", "").lower() != EXCHANGE_IMPL:
                continue
            if exchange.get("input", "")[:10].lower() != CLOSE:
                continue
            assert trace["status"] == 1
            assert exchange.get("from", "").lower() == EXCHANGE_PROXY and not exchange.get("error")
            args = words(exchange["input"], CLOSE)
            assert len(args) >= 9
            user, offset, nonce, deadline, v, r, s, count = args[:8]
            ids = args[8:]
            assert user < 2**160 and offset == 7 * 32 and 1 <= count == len(ids) <= 3
            assert deadline < 2**64 and v in (27, 28) and r > 0 and s > 0
            array_hash = keccak(bytes.fromhex(encoded(ids)))
            struct_hash = keccak(typehash + bytes.fromhex(encoded((user, int.from_bytes(array_hash, "big"), nonce, deadline))))
            digest = keccak(b"\x19\x01" + domain + struct_hash)

            session_calls = [call for call in descendants(exchange)
                             if call.get("to", "").lower() == SESSION_PROXY]
            assert len(session_calls) == 2
            nonce_call, signer_call = session_calls
            assert nonce_call["type"] == "CALL" and signer_call["type"] == "STATICCALL"
            assert nonce_call["from"].lower() == signer_call["from"].lower() == EXCHANGE_PROXY
            assert not nonce_call.get("error") and not signer_call.get("error")
            assert words(nonce_call["input"], NONCE) == [user, nonce, deadline]
            assert words(signer_call["input"], SIGNER) == [user, int.from_bytes(struct_hash, "big"), v, r, s]
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
            signer = int(precompile["output"], 16)
            assert 0 < signer < 2**160
            assert int(delegated["output"], 16) == int(signer_call["output"], 16) == signer
            rows.append({
                "tx": trace["hash"], "block": trace["block"],
                "trace": str(path.relative_to(ROOT)),
                "user": f"0x{user:040x}", "position_ids": [str(value) for value in ids],
                "nonce": str(nonce), "deadline": deadline,
                "position_ids_hash": "0x" + array_hash.hex(),
                "struct_hash": "0x" + struct_hash.hex(),
                "digest": "0x" + digest.hex(),
                "recovered_session_signer": f"0x{signer:040x}",
            })
    counts = dict(sorted(collections.Counter(len(row["position_ids"]) for row in rows).items()))
    assert len(rows) == 43 and sum(int(k) * v for k, v in counts.items()) == 49
    assert len({row["tx"] for row in rows}) == 22
    assert len({(row["user"], row["nonce"]) for row in rows}) == len(rows)
    assert all(row["recovered_session_signer"] != row["user"] for row in rows)
    return {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_selector": CLOSE, "nonce_selector": NONCE,
        "signer_selector": SIGNER, "typehash_getter": GETTER,
        "type_string": type_string, "typehash": "0x" + typehash.hex(),
        "domain_separator_at_pin": "0x" + domain.hex(),
        "matched_close_call_count": len(rows), "distinct_transaction_count": 22,
        "position_id_count": 49,
        "position_array_length_counts": {str(k): v for k, v in counts.items()},
        "distinct_user_nonce_count": len(rows),
        "checks": ["type string hashes to pinned SessionKeyManager typehash getter",
                   "dynamic position ID array hashes to the nested SessionKeyManager struct input",
                   "user, nonce and deadline equal consumeNonce calldata",
                   "recomputed EIP-712 digest and signature equal ECRECOVER calldata",
                   "ECRECOVER and SessionKeyManager return the same nonzero session signer"],
        "calls": rows,
        "limits": ["These 43 calls succeeded in 22 saved transactions; failed close intents and other array lengths are not covered.",
                   "A successful SessionKeyManager call proves acceptance in these traces, but this ledger does not independently reconstruct historical session-key storage for every call.",
                   "The pinned domain separator matched all saved digests; domain changes outside this corpus remain untested."],
    }


def verify():
    result = build()
    assert json.loads(OUT.read_text()) == result
    print(result["matched_close_call_count"], "signed close hashes and ECRECOVER inputs matched")
    return result


if __name__ == "__main__":
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(result["matched_close_call_count"], "signed close hashes and ECRECOVER inputs matched")
