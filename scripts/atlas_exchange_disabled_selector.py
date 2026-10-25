#!/usr/bin/env python3
"""Check the live Exchange selector 0xfb9f1009 against pinned bytecode."""

import argparse
import hashlib
import json
import pathlib
import subprocess

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
RAW = ROOT / "artifacts" / "exchange_disabled_selector" / "pinned_probes.json"
BEHAVIOR = ATLAS / "exchange_disabled_selector_behavior.json"
PIN = 48902346
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x000000000000000000000000000000000000dead"
SELECTOR = "0xfb9f1009"
ERROR = "0xd9d193d3"
BODY_START, BODY_END = 1273, 1318
HELPER_START, HELPER_END = 16073, 16092
EFFECT_OPS = {"SLOAD", "SSTORE", "TLOAD", "TSTORE", "CALL", "CALLCODE", "DELEGATECALL", "STATICCALL", "CREATE", "CREATE2", "LOG0", "LOG1", "LOG2", "LOG3", "LOG4", "SELFDESTRUCT"}


def load_manifest():
    return json.loads((ATLAS / "manifest.json").read_text())


def runtime():
    row = load_manifest()["contracts"][IMPLEMENTATION]
    return bytes.fromhex((ATLAS / row["runtime_file"]).read_text().strip().removeprefix("0x"))


def digest_path(path):
    return hashlib.sha256(json.dumps(path, separators=(",", ":")).encode()).hexdigest()


def cases():
    return {
        "owner_market_0": (OWNER, SELECTOR + f"{0:064x}"),
        "owner_market_1": (OWNER, SELECTOR + f"{1:064x}"),
        "owner_market_max": (OWNER, SELECTOR + f"{2**32 - 1:064x}"),
        "outsider_market_0": (OUTSIDER, SELECTOR + f"{0:064x}"),
        "noncanonical_uint32": (OWNER, SELECTOR + f"{2**32:064x}"),
        "short_calldata": (OWNER, SELECTOR),
    }


def capture():
    block = rpc("eth_getBlockByNumber", [hex(PIN), False])
    assert block["hash"] == load_manifest()["block_hash"]
    code = runtime()
    assert hashlib.sha256(code).hexdigest() == load_manifest()["contracts"][IMPLEMENTATION]["sha256"]
    rows = {}
    for name, (sender, data) in cases().items():
        call = {"from": sender, "to": PROXY, "input": data, "gas": "0x989680"}
        trace = rpc("debug_traceCall", [call, hex(PIN), {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        op_trace = rpc("debug_traceCall", [call, hex(PIN), {"disableMemory": True, "disableStorage": True}])
        delegate = [(step["pc"], step["op"]) for step in op_trace["structLogs"] if step["depth"] == 2]
        rows[name] = {
            "from": sender, "calldata": data, "error": trace.get("error"), "output": trace.get("output", "0x"),
            "delegate_error": trace.get("calls", [{}])[0].get("error"),
            "delegate_output": trace.get("calls", [{}])[0].get("output", "0x"),
            "logs": trace.get("logs", []), "delegate_steps": len(delegate),
            "delegate_path_sha256": digest_path(delegate),
            "effect_ops": [(pc, op) for pc, op in delegate if op in EFFECT_OPS],
            "delegate_tail": delegate[-45:],
        }
        if name == "owner_market_0":
            rows[name]["delegate_path"] = delegate
        print(name, rows[name]["output"], rows[name]["delegate_steps"], flush=True)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({"pin": PIN, "block_hash": block["hash"], "exchange": PROXY,
                               "implementation": IMPLEMENTATION, "selector": SELECTOR,
                               "runtime_sha256": hashlib.sha256(code).hexdigest(),
                               "function_body_hex": code[BODY_START:BODY_END].hex(),
                               "abi_helper_hex": code[HELPER_START:HELPER_END].hex(),
                               "cases": rows}, indent=2) + "\n")


def verify():
    raw = json.loads(RAW.read_text())
    manifest = load_manifest()
    assert raw["pin"] == PIN and raw["block_hash"] == manifest["block_hash"]
    assert raw["exchange"] == PROXY and raw["implementation"] == IMPLEMENTATION
    assert raw["selector"] == SELECTOR and set(raw["cases"]) == set(cases())
    code = runtime()
    assert raw["runtime_sha256"] == hashlib.sha256(code).hexdigest() == manifest["contracts"][IMPLEMENTATION]["sha256"]
    assert raw["function_body_hex"] == code[BODY_START:BODY_END].hex()
    assert raw["abi_helper_hex"] == code[HELPER_START:HELPER_END].hex()
    assert raw["function_body_hex"] == "5b503461046b57602036600319011261046b57610513613ec9565b5060405163d9d193d360e01b8152600490fd"
    assert raw["abi_helper_hex"] == "5b6004359063ffffffff82168203610fdd5756"
    canonical = ("owner_market_0", "owner_market_1", "owner_market_max", "outsider_market_0")
    first = raw["cases"][canonical[0]]
    assert digest_path(first["delegate_path"]) == first["delegate_path_sha256"]
    assert [1273, "JUMPDEST"] in first["delegate_path"]
    assert [16073, "JUMPDEST"] in first["delegate_path"]
    assert first["delegate_path"][-1] == [1317, "REVERT"]
    for name in canonical:
        row = raw["cases"][name]
        assert row["error"] == row["delegate_error"] == "execution reverted"
        assert row["output"] == row["delegate_output"] == ERROR
        assert row["delegate_path_sha256"] == first["delegate_path_sha256"]
        assert not row["effect_ops"] and not row["logs"]
    for name in ("noncanonical_uint32", "short_calldata"):
        row = raw["cases"][name]
        assert row["error"] == "execution reverted" and row["output"] == "0x"
        assert not row["effect_ops"] and not row["logs"]
    assert subprocess.run(["cast", "sig", "unpauseMarket(uint32)"], check=True,
                          capture_output=True, text=True).stdout.strip() == SELECTOR
    behavior = {
        "pin": PIN, "block_hash": raw["block_hash"], "exchange_proxy": PROXY,
        "implementation": IMPLEMENTATION, "selector": SELECTOR,
        "public_signature_candidate": "unpauseMarket(uint32)",
        "source_name_status": "unverified; selector hash match only",
        "raw_evidence": "../../artifacts/exchange_disabled_selector/pinned_probes.json",
        "local_replay_evidence": "../../artifacts/fixed_revert_local/replay.json",
        "runtime_sha256": raw["runtime_sha256"],
        "function_body_pc": [BODY_START, BODY_END], "abi_helper_pc": [HELPER_START, HELPER_END],
        "canonical_probe_count": len(canonical),
        "behavior": "For nonpayable, canonically encoded uint32 calls, ABI validation returns directly to a four-byte revert with 0xd9d193d3. The function body has no caller, storage, or external-call dependency.",
        "malformed_behavior": "Short calldata and a noncanonical uint32 revert without error data.",
        "error_name_status": "unresolved",
        "simulated_error_catalog": [{"selector": ERROR, "probe_paths": list(canonical),
                                     "public_signature_candidates": []}],
        "limits": ["The public signature candidate has the correct selector hash, but the original source name is unverified.",
                   "The bytecode conclusion applies to the live implementation at the pinned block; it says nothing about an upgrade or a different implementation."],
    }
    BEHAVIOR.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified selector 0xfb9f1009 pinned revert path")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
