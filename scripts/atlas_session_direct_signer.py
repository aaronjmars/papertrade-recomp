#!/usr/bin/env python3
"""Verify the sampled direct-user EIP-712 signer path in SessionKeyManager."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts"
OUT = ATLAS / "session_direct_signer_behavior.json"
PIN = 48902346
SELECTOR = "0xd45167d0"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION_PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SESSION_IMPLEMENTATION = "0x8a5069fe303e8f81e91825436e956d595032e558"
ECRECOVER = "0x" + "0" * 39 + "1"


def calls_with_ancestors(call, ancestors=()):
    yield call, ancestors
    for child in call.get("calls", []):
        yield from calls_with_ancestors(child, ancestors + (call,))


def words(data):
    assert data.startswith(SELECTOR) and len(data) == 10 + 4 * 64
    return [int(data[i:i + 64], 16) for i in range(10, len(data), 64)]


def probe_cases(sample):
    h, v, r, sig_s = (int(sample[key], 16) if key != "v" else sample[key]
                      for key in ("struct_hash", "v", "r", "s"))
    return {
        "valid_exchange": (EXCHANGE, h, v, r, sig_s),
        "valid_outsider": ("0x000000000000000000000000000000000000dead", h, v, r, sig_s),
        "changed_hash": (EXCHANGE, h ^ 1, v, r, sig_s),
        "invalid_v": (EXCHANGE, h, 0, r, sig_s),
        "zero_r": (EXCHANGE, h, v, 0, sig_s),
        "zero_s": (EXCHANGE, h, v, r, 0),
    }


def verify_pinned_probes(manifest, domain, keccak, sample):
    saved = json.loads((ARTIFACTS / "session_direct_signer" / "pinned_probes.json").read_text())
    assert saved["pin"] == PIN and saved["block_hash"].lower() == manifest["block_hash"]
    cases = probe_cases(sample)
    assert set(saved["rows"]) == set(cases)
    checked = {}
    for name, (caller, struct_hash, v_value, r_value, s_value) in cases.items():
        row = saved["rows"][name]
        calldata = SELECTOR + "".join(f"{value:064x}" for value in
                                      (struct_hash, v_value, r_value, s_value))
        assert row["from"].lower() == caller and row["data"].lower() == calldata
        trace = row["trace"]
        assert trace["to"].lower() == SESSION_PROXY and trace["input"].lower() == calldata
        assert not trace.get("error") and len(trace.get("calls", [])) == 1
        delegated = trace["calls"][0]
        assert delegated["type"] == "DELEGATECALL" and delegated["to"].lower() == SESSION_IMPLEMENTATION
        assert delegated["input"].lower() == calldata and delegated["output"] == trace["output"]
        assert not delegated.get("error")
        digest = keccak(b"\x19\x01" + domain + struct_hash.to_bytes(32, "big"))
        precompiles = delegated.get("calls", [])
        if name == "invalid_v":
            assert precompiles == []
        else:
            assert len(precompiles) == 1
            precompile = precompiles[0]
            expected = b"".join(value.to_bytes(32, "big") for value in
                                (int.from_bytes(digest, "big"), v_value, r_value, s_value))
            assert precompile["type"] == "STATICCALL" and precompile["to"].lower() == ECRECOVER
            assert bytes.fromhex(precompile["input"][2:]) == expected
            assert not precompile.get("error")
            if precompile.get("output"):
                assert int(precompile["output"], 16) == int(trace["output"], 16)
            else:
                assert name in ("zero_r", "zero_s") and int(trace["output"], 16) == 0
        recovered = int(trace["output"], 16)
        if name in ("valid_exchange", "valid_outsider"):
            assert recovered == int(sample["user"], 16)
        elif name == "changed_hash":
            assert recovered != 0 and recovered != int(sample["user"], 16)
        else:
            assert recovered == 0
        checked[name] = {"caller": caller, "returned_signer": f"0x{recovered:040x}",
                         "precompile_called": bool(precompiles), "reverted": False}
    return checked


def capture():
    from atlas_session_keys import rpc

    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    sample = json.loads(OUT.read_text())["calls"][0]
    rows = {}
    for name, (caller, struct_hash, v, r, s) in probe_cases(sample).items():
        calldata = SELECTOR + "".join(f"{value:064x}" for value in
                                      (struct_hash, v, r, s))
        tx = {"from": caller, "to": SESSION_PROXY, "data": calldata, "gas": "0x1000000"}
        trace = rpc(url, "debug_traceCall", [tx, hex(PIN), {"tracer": "callTracer"}])
        rows[name] = {"from": caller, "data": calldata, "trace": trace}
    path = ARTIFACTS / "session_direct_signer" / "pinned_probes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pin": PIN, "block_hash": header["hash"],
                                "rows": rows}, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    session = json.loads((ATLAS / "session_key_behavior.json").read_text())
    assert manifest["block"] == PIN
    assert session["pin"] == PIN and session["block_hash"] == manifest["block_hash"]
    assert session["address"] == SESSION_PROXY and session["implementation"] == SESSION_IMPLEMENTATION
    domain = bytes.fromhex(session["domain_separator"][2:])
    assert len(domain) == 32
    keccak = Keccak()
    rows = []
    for trace in graph["traces"]:
        path = ARTIFACTS / trace["source_directory"] / f"{trace['source_stem']}.calls.json"
        root = json.loads(path.read_text())
        for call, ancestors in calls_with_ancestors(root):
            calldata = call.get("input", "").lower()
            if call.get("to", "").lower() != SESSION_PROXY or not calldata.startswith(SELECTOR):
                continue
            assert trace["status"] == 1 and not call.get("error")
            assert call["type"] == "STATICCALL" and call["from"].lower() == EXCHANGE
            exchange_parent = next(parent for parent in reversed(ancestors)
                                   if parent.get("to", "").lower() == EXCHANGE
                                   and parent.get("input", "").startswith("0x8d09f23f"))
            struct_hash, v, r, s = words(calldata)
            assert v in (27, 28)
            digest = keccak(b"\x19\x01" + domain + struct_hash.to_bytes(32, "big"))
            assert len(call.get("calls", [])) == 1
            delegated = call["calls"][0]
            assert delegated["type"] == "DELEGATECALL"
            assert delegated["to"].lower() == SESSION_IMPLEMENTATION
            assert delegated["input"].lower() == calldata and not delegated.get("error")
            assert len(delegated.get("calls", [])) == 1
            precompile = delegated["calls"][0]
            expected_input = b"".join(word.to_bytes(32, "big") for word in
                                      (int.from_bytes(digest, "big"), v, r, s))
            assert precompile["type"] == "STATICCALL" and precompile["to"].lower() == ECRECOVER
            assert bytes.fromhex(precompile["input"][2:]) == expected_input
            assert not precompile.get("error")
            recovered = int(precompile["output"], 16)
            assert recovered > 0 and recovered < (1 << 160)
            assert int(delegated["output"], 16) == int(call["output"], 16) == recovered
            user = int(exchange_parent["input"][10:74], 16)
            assert user == recovered
            rows.append({
                "tx": trace["hash"], "block": trace["block"],
                "source_trace": str(path.relative_to(ROOT)),
                "exchange_parent_selector": "0x8d09f23f",
                "user": f"0x{user:040x}", "struct_hash": f"0x{struct_hash:064x}",
                "digest": "0x" + digest.hex(), "v": v,
                "r": f"0x{r:064x}", "s": f"0x{s:064x}",
                "recovered_signer": f"0x{recovered:040x}",
            })
    rows.sort(key=lambda row: (row["block"], row["tx"]))
    assert len(rows) == len({row["tx"] for row in rows}) == 4
    probes = verify_pinned_probes(manifest, domain, keccak, rows[0])
    return {
        "pin": PIN, "block_hash": manifest["block_hash"],
        "session_proxy": SESSION_PROXY, "session_implementation": SESSION_IMPLEMENTATION,
        "exchange_proxy": EXCHANGE, "selector": SELECTOR,
        "sampled_path": "recover signer from keccak256(0x1901 || DOMAIN_SEPARATOR || structHash), v, r, s; return address",
        "historical_call_count": len(rows), "direct_user_match_count": len(rows),
        "pinned_probe_count": len(probes), "pinned_probes": probes,
        "calls": rows,
        "limits": [
            "Exact Solidity source name and declared ABI types are unresolved.",
            "Only four successful direct-user withdrawal signatures are sampled.",
            "Six pinned read-only probes check caller independence, one changed hash, invalid v, zero r, and zero s. Other malformed signatures remain untested.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh pinned read-only trace probes")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Session direct signer: {result['historical_call_count']} EIP-712 calls matched")
