#!/usr/bin/env python3
"""Check signed Exchange opens against SessionKeyManager's pinned EIP-712 type hash."""

import json
from collections import Counter
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_session_typehashes import KNOWN

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "session_open_typehash_behavior.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
ECRECOVER = "0x" + "0" * 39 + "1"
OPEN = "0xec6783f0"
RECOVER = "0x7f608253"
GETTER = "0x6525a680"
PIN = 48902346


def read(path):
    return json.loads(path.read_text())


def descendants(call):
    yield call
    for child in call.get("calls", []):
        yield from descendants(child)


def word(value):
    return value.to_bytes(32, "big")


def argument_words(data):
    assert data.startswith(OPEN) and len(data) == 10 + 11 * 64
    return [int(data[i:i + 64], 16) for i in range(10, len(data), 64)]


def open_calls(root):
    return [call for call in descendants(root)
            if call.get("type") == "CALL" and call.get("to", "").lower() == EXCHANGE
            and call.get("input", "")[:10] == OPEN]


def saved_calls():
    traces = {}
    duplicate_paths = 0
    for path in sorted((ROOT / "artifacts").glob("*/*.calls.json")):
        root = read(path)
        calls = open_calls(root)
        if not calls:
            continue
        tx = path.name.removesuffix(".calls.json")
        assert len(tx) == 66 and tx.startswith("0x")
        shape = [(call["input"], call.get("error"), call.get("output")) for call in calls]
        if tx in traces:
            assert shape == traces[tx][2], (tx, path, traces[tx][0])
            duplicate_paths += 1
            continue
        traces[tx] = (path, calls, shape)
    return traces, duplicate_paths


def build():
    manifest = read(ATLAS / "manifest.json")
    typehash_behavior = read(ATLAS / "session_typehash_behavior.json")
    session_behavior = read(ATLAS / "session_key_behavior.json")
    assert manifest["block"] == PIN == typehash_behavior["pin"]
    assert typehash_behavior["block_hash"] == session_behavior["block_hash"] == manifest["block_hash"]
    type_string = KNOWN[GETTER][1]
    assert type_string is not None
    keccak = Keccak()
    typehash = keccak(type_string.encode())
    assert "0x" + typehash.hex() == typehash_behavior["constant_getters"][GETTER]["pinned_return"]
    domain = bytes.fromhex(session_behavior["domain_separator"][2:])
    traces, duplicate_paths = saved_calls()
    rows = []
    outcomes = Counter()
    signed = 0
    for tx, (path, calls, _) in sorted(traces.items()):
        for index, call in enumerate(calls):
            args = argument_words(call["input"])
            user, instrument, is_long, size, leverage, use_debt, nonce, deadline, v, r, s = args
            assert user < 1 << 160 and instrument < 1 << 32 and is_long in (0, 1)
            assert size < 1 << 128 and leverage < 1 << 32 and use_debt in (0, 1)
            assert deadline < 1 << 64 and v in (27, 28)
            struct_hash = keccak(typehash + b"".join(word(value) for value in args[:8]))
            signer_calls = [child for child in descendants(call)
                            if child.get("type") == "STATICCALL"
                            and child.get("to", "").lower() == SESSION
                            and child.get("input", "")[:10] == RECOVER]
            assert len(signer_calls) <= 1
            recovered_signer = None
            if signer_calls:
                signed += 1
                signer_call = signer_calls[0]
                assert not signer_call.get("error")
                expected_input = RECOVER + "".join(f"{value:064x}" for value in
                    (user, int.from_bytes(struct_hash, "big"), v, r, s))
                assert signer_call["input"].lower() == expected_input
                digest = keccak(b"\x19\x01" + domain + struct_hash)
                precompiles = [child for child in descendants(signer_call)
                               if child.get("type") == "STATICCALL"
                               and child.get("to", "").lower() == ECRECOVER]
                assert len(precompiles) == 1
                assert precompiles[0]["input"].lower() == "0x" + "".join(
                    f"{value:064x}" for value in (int.from_bytes(digest, "big"), v, r, s))
                assert precompiles[0]["output"] == signer_call["output"]
                recovered_signer = "0x" + signer_call["output"][-40:]
            error = call.get("output", "")[:10] if call.get("error") else None
            if not signer_calls:
                assert error == "0xf87d9271"
            outcome = error or "success"
            outcomes[outcome] += 1
            rows.append({"tx": tx, "source": str(path.relative_to(ROOT)),
                         "call_index": index, "user": "0x" + f"{user:040x}",
                         "instrument_id": instrument, "is_long": bool(is_long),
                         "size": str(size), "leverage": leverage,
                         "use_debt": bool(use_debt), "nonce": str(nonce),
                         "deadline": deadline,
                         "struct_hash": "0x" + struct_hash.hex(),
                         "session_signer_reached": bool(signer_calls),
                         "recovered_signer": recovered_signer,
                         "result": outcome})
    assert rows and signed > 0
    result = {"pin": PIN, "block_hash": manifest["block_hash"],
              "open_selector": OPEN, "typehash_getter": GETTER,
              "type_string": type_string, "typehash": "0x" + typehash.hex(),
              "source_lead": typehash_behavior["open_position_type_source"],
              "unique_transactions": len(traces), "open_call_count": len(rows),
              "session_signer_call_count": signed,
              "duplicate_saved_trace_paths_checked": duplicate_paths,
              "outcomes": dict(sorted(outcomes.items())),
              "calls": rows,
              "limits": ["The SDK supplied the field names, but the type hash and every sampled struct hash were checked against pinned bytecode and saved calls.",
                         "These are sampled saved transactions, not the full history of signed opens.",
                         "This ledger checks signatures; the side-limit trigger and hash-verified OiCapExceeded() name are recorded in exchange_open_limit_full_behavior.json."]}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("signed opens:", len(rows), "calls,", signed, "session signer calls,",
          dict(sorted(outcomes.items())))
    return result


if __name__ == "__main__":
    build()
