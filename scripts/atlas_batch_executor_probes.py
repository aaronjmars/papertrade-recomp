#!/usr/bin/env python3
"""Read-only branch probes for the pinned BatchExecutor proxy."""

import json
import os
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
BATCH = ROOT / "artifacts" / "batch_executor"
SOURCE_TX = "0x25c6a939b07062ebf0f6e577959734a4beb28e59a5dfcf66a6b0994b322c442c"
PIN = 48902346
PROXY = "0x233ff29b239abc1d7748605da9b205c3e008626e"
EXECUTED = "0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad"
SUMMARY = "0x9d65322d939fd0a2d0032c87248c8e9f9b14cc177e27b2c049cb4b0356e5160b"
REJECTED = "0x6002fcbae88fcbb8133c69c91df90bbc0b4464af94df2a56f8bb843f1cc5a193"


def rpc(method, params):
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    response = json.load(urllib.request.urlopen(request, timeout=50))
    if "error" in response:
        raise RuntimeError(response["error"])
    return response["result"]


def trace(sender, data):
    result = rpc("debug_traceCall", [
        {"from": sender, "to": PROXY, "gas": "0x989680", "data": data}, hex(PIN),
        {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
    ])
    implementation = result.get("calls", [{}])[0]
    return {
        "root_error": result.get("error"),
        "root_output": result.get("output", ""),
        "inner_calls": [{"target": x.get("to"), "selector": x.get("input", "")[:10],
                         "error": x.get("error"), "output": x.get("output", ""),
                         "value": x.get("value")} for x in implementation.get("calls", [])],
        "events": [{"topic0": x["topics"][0], "topics": x["topics"], "data": x["data"]}
                   for x in implementation.get("logs", [])],
    }


def event_data_words(event):
    data = event["data"]
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def main():
    assert subprocess.run(["cast", "sig", "NotAuthorizedRelayer()"], capture_output=True, text=True, check=True).stdout.strip() == "0x17fb2066"
    assert subprocess.run(["cast", "sig", "BatchCallFailed(uint256,bytes)"], capture_output=True, text=True, check=True).stdout.strip() == "0x651ab1b3"
    tx = json.loads((BATCH / f"{SOURCE_TX}.tx.json").read_text())
    raw = bytearray.fromhex(tx["input"][2:])
    word = lambda i: int.from_bytes(raw[i:i + 32], "big")
    array = 4 + word(4)
    first = array + 32 + word(array + 32)
    inner_data = first + word(first + 32) + 32
    assert word(array) == 1 and word(first + 64) == 1 and word(first + 96) == 0

    def replace(offset, data):
        output = bytearray(raw)
        output[offset:offset + len(data)] = data
        return "0x" + output.hex()

    empty = "0x251fb27d" + (32).to_bytes(32, "big").hex() + bytes(32).hex()
    cases = {
        "empty_authorized": (tx["from"], empty),
        "empty_unauthorized": ("0x000000000000000000000000000000000000dEaD", empty),
        "failed_call_continue_true": (tx["from"], tx["input"]),
        "failed_call_continue_false": (tx["from"], replace(first + 64, bytes(32))),
        "invalid_bool_two": (tx["from"], replace(first + 64, (2).to_bytes(32, "big"))),
        "field4_one": (tx["from"], replace(first + 96, (1).to_bytes(32, "big"))),
        "invalid_target": (tx["from"], replace(first, (1).to_bytes(32, "big"))),
        "invalid_selector": (tx["from"], replace(inner_data, bytes.fromhex("deadbeef"))),
    }
    probes = {name: trace(sender, data) for name, (sender, data) in cases.items()}
    assert probes["empty_authorized"]["root_error"] is None
    assert [x["topic0"] for x in probes["empty_authorized"]["events"]] == [SUMMARY]
    assert event_data_words(probes["empty_authorized"]["events"][0]) == [0, 0, 0, 0]
    assert probes["empty_unauthorized"]["root_output"] == "0x17fb2066"
    assert probes["failed_call_continue_true"]["root_error"] is None
    assert [x["topic0"] for x in probes["failed_call_continue_true"]["events"]] == [EXECUTED, SUMMARY]
    assert probes["failed_call_continue_false"]["root_output"].startswith("0x651ab1b3")
    assert probes["invalid_bool_two"]["root_error"]
    assert probes["field4_one"]["root_error"] is None
    for name in ("invalid_target", "invalid_selector"):
        probe = probes[name]
        assert probe["root_error"] is None and not probe["inner_calls"]
        assert [x["topic0"] for x in probe["events"]] == [REJECTED, SUMMARY]
        assert b"BatchExecutor: selector not allowed" in bytes.fromhex(probe["events"][0]["data"][2:])
        assert event_data_words(probe["events"][1]) == [1, 0, 1, 0]
    output = ATLAS / "batch_executor_probes.json"
    output.write_text(json.dumps({"pin": PIN, "method": "debug_traceCall callTracer withLog at pinned block",
                                  "baseline_transaction": SOURCE_TX, "probes": probes}, indent=2) + "\n")
    print(f"wrote {output}: {len(probes)} pinned read-only branch probes")


if __name__ == "__main__":
    main()
