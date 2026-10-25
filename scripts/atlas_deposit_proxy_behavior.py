#!/usr/bin/env python3
"""Capture pinned, read-only branches of a Papertrade user deposit proxy."""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PROBES = ROOT / "artifacts" / "deposit_proxy_probes"
PIN = 48902346
PROXY = "0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"
USER = "0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
OUTSIDER = "0x" + "33" * 20
MOCK_TOKEN = "0x" + "44" * 20
CORE_WRITER = "0x" + "33" * 20
HISTORICAL_PROXY = "0x2e38ce35e63bfae2a85bf6db885ffcedaa76e18e"
HISTORICAL_TX = "0xd4ee56dd5d1e271b8fc142e340362d3ab1eede92a9810ab33de4d90a9f798257"
HISTORICAL = ROOT / "artifacts" / "historical"


def word(value):
    return f"{value:064x}" if isinstance(value, int) else value.removeprefix("0x").rjust(64, "0")


def rpc(url, method, params):
    request = urllib.request.Request(
        url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def sweep(spot, perp, token=0):
    return "0x925b3aad" + word(token) + word(spot) + word(perp)


def withdraw(amount):
    return "0x0c506e96" + word(MOCK_TOKEN) + word(amount)


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    PROBES.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    code_path = PROBES / "historical_proxy_code.json"
    if not code_path.exists():
        code = rpc(url, "eth_getCode", [HISTORICAL_PROXY, hex(PIN)])
        code_path.write_text(json.dumps({"pin": PIN, "block_hash": header["hash"],
                                         "address": HISTORICAL_PROXY, "code": code}, indent=2) + "\n")
    # Tiny test contracts only return an ABI bool, or no data. They are installed
    # by debug_traceCall state overrides and never deployed or called on chain.
    mock_true = "0x600160005260206000f3"
    mock_false = "0x600060005260206000f3"
    mock_empty = "0x00"
    cases = {
        "user_getter": (OUTSIDER, "0x4f8632ba", None),
        "exchange_getter": (OUTSIDER, "0xd2f7265a", None),
        "sweep_outsider": (OUTSIDER, sweep(1, 0), None),
        "sweep_exchange_zero": (EXCHANGE, sweep(0, 0), None),
        "sweep_exchange_spot_real": (EXCHANGE, sweep(0x74645CA7, 0), None),
        "sweep_exchange_spot_mock": (EXCHANGE, sweep(123, 0), {CORE_WRITER: {"code": mock_empty}}),
        "sweep_exchange_perp_mock": (EXCHANGE, sweep(123, 4), {CORE_WRITER: {"code": mock_empty}}),
        "sweep_exchange_perp_only_mock": (EXCHANGE, sweep(0, 4), {CORE_WRITER: {"code": mock_empty}}),
        "sweep_exchange_token7_mock": (EXCHANGE, sweep(123, 0, 7), {CORE_WRITER: {"code": mock_empty}}),
        "sweep_exchange_overflow_mul": (EXCHANGE, sweep(0, 2**64 - 1), None),
        "sweep_exchange_overflow_sum": (EXCHANGE, sweep(2**64 - 1, 1), None),
        "withdraw_outsider": (OUTSIDER, withdraw(1), None),
        "withdraw_user_zero": (USER, withdraw(0), None),
        "withdraw_user_true": (USER, withdraw(11), {MOCK_TOKEN: {"code": mock_true}}),
        "withdraw_user_false": (USER, withdraw(11), {MOCK_TOKEN: {"code": mock_false}}),
        "withdraw_user_empty": (USER, withdraw(11), {MOCK_TOKEN: {"code": mock_empty}}),
        "withdraw_user_no_code": (USER, withdraw(11), None),
    }
    for name, (sender, data, override) in cases.items():
        destination = PROBES / f"{name}.call.json"
        if destination.exists():
            continue
        options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
        if override:
            options["stateOverrides"] = override
        call = {"from": sender, "to": PROXY, "data": data, "gas": "0x1000000"}
        result = rpc(url, "debug_traceCall", [call, hex(PIN), options])
        destination.write_text(json.dumps(result, indent=2) + "\n")
        print(name, "error" if result.get("error") else "success", flush=True)


def read_probe(name):
    return json.loads((PROBES / f"{name}.call.json").read_text())


def action(call):
    raw = bytes.fromhex(call["input"][2:])
    assert raw[:4].hex() == "17938e13"
    assert int.from_bytes(raw[4:36], "big") == 32
    length = int.from_bytes(raw[36:68], "big")
    payload = raw[68:68 + length]
    assert len(payload) == length and payload[0] == 1
    assert len(payload[4:]) % 32 == 0
    return {"id": int.from_bytes(payload[1:4], "big"), "version": payload[0],
            "fields": [int.from_bytes(payload[i:i + 32], "big") for i in range(4, len(payload), 32)],
            "raw": "0x" + payload.hex()}


def hash_signature(signature):
    return subprocess.run(["cast", "keccak", signature], capture_output=True,
                          text=True, check=True).stdout.strip().lower()


def selector(signature):
    return subprocess.run(["cast", "sig", signature], capture_output=True,
                          text=True, check=True).stdout.strip().lower()


def find_call(node, prefix):
    if node.get("input", "").startswith(prefix):
        return node
    for child in node.get("calls", []):
        found = find_call(child, prefix)
        if found:
            return found
    return None


def analyze():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    family = json.loads((ATLAS / "deposit_proxy_family.json").read_text())
    history_code = json.loads((PROBES / "historical_proxy_code.json").read_text())
    assert history_code["block_hash"].lower() == manifest["block_hash"]
    code = bytearray.fromhex(history_code["code"][2:])
    assert len(code) == family["sample_runtime_bytes"] == 1646
    embedded_users = []
    for start, end in family["varying_byte_ranges"]:
        embedded_users.append("0x" + code[start:end].hex())
        code[start:end] = bytes(end - start)
    assert embedded_users == ["0x1730a930cfd0da43255081801bf1a3eb0b69ec83"] * 2
    assert hashlib.sha256(code).hexdigest() == family["normalized_sha256"]

    signature_map = {
        "0x0c506e96": "withdrawStuckToken(address,uint256)",
        "0x4f8632ba": "user()",
        "0x925b3aad": "sweepAllToExchange(uint64,uint64,uint64)",
        "0xd2f7265a": "exchange()",
    }
    assert all(selector(sig) == sel for sel, sig in signature_map.items())
    assert hash_signature("StuckTokenWithdrawn(address,address,uint256)") == "0x3d95e1dd133840fdfe95e9a3b6c9fc44f85019531359313e278c6e358ef5b1e0"
    assert selector("CoreAmountOverflow()") == "0xfadaa871"
    assert selector("sendRawAction(bytes)") == "0x17938e13"
    assert int(read_probe("user_getter")["output"], 16) == int(USER, 16)
    assert int(read_probe("exchange_getter")["output"], 16) == int(EXCHANGE, 16)
    assert read_probe("sweep_outsider")["error"] and bytes.fromhex(read_probe("sweep_outsider")["output"][2:]).find(b"only exchange") >= 0
    assert not read_probe("sweep_exchange_zero").get("calls")
    assert not read_probe("sweep_exchange_zero").get("error")
    assert all(read_probe(name)["output"] == "0xfadaa871" for name in
               ("sweep_exchange_overflow_mul", "sweep_exchange_overflow_sum"))
    action_cases = {}
    for name, expected in {
        "sweep_exchange_spot_mock": [(6, [int(EXCHANGE, 16), 0, 123])],
        "sweep_exchange_perp_mock": [(7, [4, 0]), (6, [int(EXCHANGE, 16), 0, 523])],
        "sweep_exchange_perp_only_mock": [(7, [4, 0]), (6, [int(EXCHANGE, 16), 0, 400])],
        "sweep_exchange_token7_mock": [(6, [int(EXCHANGE, 16), 7, 123])],
        "sweep_exchange_spot_real": [(6, [int(EXCHANGE, 16), 0, 0x74645CA7])],
    }.items():
        probe = read_probe(name)
        assert not probe.get("error")
        decoded = [action(child) for child in probe.get("calls", [])]
        assert [(item["id"], item["fields"]) for item in decoded] == expected
        action_cases[name] = decoded

    assert read_probe("withdraw_outsider").get("error") and b"only user" in bytes.fromhex(read_probe("withdraw_outsider")["output"][2:])
    assert read_probe("withdraw_user_zero").get("error") and b"zero amount" in bytes.fromhex(read_probe("withdraw_user_zero")["output"][2:])
    assert read_probe("withdraw_user_false").get("error") and b"transfer failed" in bytes.fromhex(read_probe("withdraw_user_false")["output"][2:])
    withdrawal = {}
    event_topic = hash_signature("StuckTokenWithdrawn(address,address,uint256)")
    for name in ("withdraw_user_true", "withdraw_user_empty", "withdraw_user_no_code"):
        probe = read_probe(name)
        assert not probe.get("error") and len(probe.get("calls", [])) == 1
        call = probe["calls"][0]
        assert call["to"] == MOCK_TOKEN and call["input"] == "0xa9059cbb" + word(USER) + word(11)
        logs = probe["logs"]
        assert len(logs) == 1 and logs[0]["topics"] == [event_topic, "0x" + word(USER), "0x" + word(MOCK_TOKEN)]
        assert int(logs[0]["data"], 16) == 11
        withdrawal[name] = {"token_call": call["input"], "event": {"topics": logs[0]["topics"], "data": logs[0]["data"]}}

    historical = json.loads((HISTORICAL / f"{HISTORICAL_TX}.calls.json").read_text())
    historical_sweep = find_call(historical, "0x925b3aad")
    assert historical_sweep and historical_sweep["to"].lower() == HISTORICAL_PROXY
    args = [int(historical_sweep["input"][10 + 64 * i:74 + 64 * i], 16) for i in range(3)]
    assert args == [0, 499900000000, 0]
    historical_actions = [action(child) for child in historical_sweep["calls"]]
    assert [(item["id"], item["fields"]) for item in historical_actions] == [(6, [int(EXCHANGE, 16), 0, 499900000000])]
    historical_receipt = json.loads((HISTORICAL / f"{HISTORICAL_TX}.receipt.json").read_text())
    assert historical_receipt["status"] == "0x1"
    core_logs = [log for log in historical_receipt["logs"] if log["address"].lower() == CORE_WRITER]
    assert len(core_logs) == 1
    assert core_logs[0]["topics"][1] == "0x" + word(HISTORICAL_PROXY)
    assert bytes.fromhex(core_logs[0]["data"][2:])[64:][:100] == bytes.fromhex(historical_actions[0]["raw"][2:])

    behavior = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "address": PROXY,
        "representative_user": USER,
        "exchange": EXCHANGE,
        "historical_proxy": HISTORICAL_PROXY,
        "historical_proxy_user": embedded_users[0],
        "historical_proxy_normalized_sha256": hashlib.sha256(code).hexdigest(),
        "historical_sweep_tx": HISTORICAL_TX,
        "historical_sweep_args": args,
        "historical_sweep_actions": historical_actions,
        "historical_core_writer_log_matches_action": True,
        "selector_reconstructions": signature_map,
        "event_catalog": [{"topic0": event_topic, "reconstructed_signature": "StuckTokenWithdrawn(address,address,uint256)",
                           "indexed_fields": ["user", "token"], "data_fields": ["amount"],
                           "status": "simulated_log_only"}],
        "simulated_error_catalog": [{"selector": "0xfadaa871", "reconstructed_signature": "CoreAmountOverflow()",
                                     "probe_paths": ["sweep_exchange_overflow_mul", "sweep_exchange_overflow_sum"],
                                     "public_signature_candidates": ["CoreAmountOverflow()"]}],
        "action_cases": action_cases,
        "withdrawal_cases": withdrawal,
        "probe_count": len(list(PROBES.glob("*.call.json"))),
        "limitations": ["Historical sweep shows a CoreWriter enqueue event, not HyperCore settlement.",
                        "The rescue success path was simulated with code overrides, not observed in a historical transaction.",
                        "The historical proxy is in the 41 fetched family samples. One additional unsampled proxy is fetched by the deployment-wide runtime derivation check."],
    }
    (ATLAS / "deposit_proxy_behavior.json").write_text(json.dumps(behavior, indent=2) + "\n")
    print("deposit proxy behavior: 4 selectors,", behavior["probe_count"], "probes, 1 historical sweep")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    analyze()
