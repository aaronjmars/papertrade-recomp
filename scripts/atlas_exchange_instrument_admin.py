#!/usr/bin/env python3
"""Map the untraced Exchange instrument configuration setter at the pin."""

import argparse
import json
import os
import pathlib

from atlas_exchange_queue_layout import KECCAK, PROXY
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "exchange_instrument_admin" / "pinned_probes.json"
BEHAVIOR = ATLAS / "exchange_instrument_admin_behavior.json"
PIN = 48902346
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SETTER = "0x5ca4c0ea"
GETTER = "0xdc8a47ef"
EVENT = "0x76a319771459e5329ebc7830ef30b80fc54d20327f8b4946a9539e53c46018c9"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
KEEPER = "0x3721476de31190dc1af8908026abe20efe25cf99"
OUTSIDER = "0x1111111111111111111111111111111111111111"
CASES = {
    "owner_instrument_0": (OWNER, 0, 123456789, 987654321, 111111111, 10**15),
    "owner_instrument_1_zero_fields": (OWNER, 1, 2**128 - 1, 0, 1, 0),
    "owner_instrument_0_rate_max_below": (OWNER, 0, 123, 456, 789, 10**18 - 1),
    "outsider_instrument_0": (OUTSIDER, 0, 123456789, 987654321, 111111111, 10**15),
    "keeper_instrument_0": (KEEPER, 0, 123456789, 987654321, 111111111, 10**15),
    "owner_invalid_instrument_2": (OWNER, 2, 123456789, 987654321, 111111111, 10**15),
    "owner_zero_first": (OWNER, 0, 0, 987654321, 111111111, 10**15),
    "owner_zero_third": (OWNER, 0, 123456789, 987654321, 0, 10**15),
    "owner_rate_upper_bound": (OWNER, 0, 123456789, 987654321, 111111111, 10**18),
}


def read(name):
    return json.loads((ATLAS / name).read_text())


def word(value):
    return f"0x{value:064x}"


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def mapped(instrument, offset=0):
    key = instrument.to_bytes(32, "big") + (7).to_bytes(32, "big")
    return word(int.from_bytes(KECCAK(key), "big") + offset)


def logs(trace):
    return list(trace.get("logs", [])) + [entry for child in trace.get("calls", []) for entry in logs(child)]


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = read("manifest.json")
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    count = rpc(url, "eth_getStorageAt", [PROXY, hex(8), hex(PIN)])
    instruments = []
    for instrument in (0, 1, 2):
        instruments.append({"id": instrument,
                            "slots": [mapped(instrument, offset) for offset in range(3)],
                            "words": [rpc(url, "eth_getStorageAt", [PROXY, mapped(instrument, offset), hex(PIN)])
                                      for offset in range(3)],
                            "getter": rpc(url, "eth_call", [
                                {"to": PROXY, "data": GETTER + word(instrument)[2:]}, hex(PIN)])})
    probes = {}
    for name, (sender, instrument, first, second, third, fourth) in CASES.items():
        data = SETTER + "".join(word(value)[2:] for value in (instrument, first, second, third, fourth))
        call = {"from": sender, "to": PROXY, "data": data, "gas": hex(10_000_000)}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                                             {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        row = {"sender": sender, "arguments": [instrument, first, second, third, fourth],
               "calldata": data, "error": trace.get("error"), "output": trace.get("output", ""),
               "logs": logs(trace)}
        if name.startswith("owner_instrument_"):
            diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                                                 {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
            row["pre_storage"] = diff.get("pre", {}).get(PROXY, {}).get("storage", {})
            row["post_storage"] = diff.get("post", {}).get(PROXY, {}).get("storage", {})
            overrides = {PROXY: {"stateDiff": row["post_storage"]}}
            row["getter_after_override"] = rpc(url, "eth_call", [
                {"to": PROXY, "data": GETTER + word(instrument)[2:]}, hex(PIN), overrides])
        probes[name] = row
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps({"pin": PIN, "block_hash": manifest["block_hash"],
                                    "proxy": PROXY, "instrument_count": count,
                                    "instruments": instruments, "probes": probes}, indent=2) + "\n")


def verify():
    saved = json.loads(ARTIFACT.read_text())
    manifest = read("manifest.json")
    assert saved["pin"] == PIN and saved["block_hash"] == manifest["block_hash"] and saved["proxy"] == PROXY
    assert int(saved["instrument_count"], 16) == 2
    assert set(saved["probes"]) == set(CASES)
    for instrument in saved["instruments"]:
        assert instrument["slots"] == [mapped(instrument["id"], i) for i in range(3)]
        if instrument["id"] == 2:
            assert all(int(value, 16) == 0 for value in instrument["words"])
            assert words(instrument["getter"]) == [0] * 8
    by_id = {row["id"]: row for row in saved["instruments"]}
    successes = []
    reverts = {}
    for name, (sender, instrument, first, second, third, fourth) in CASES.items():
        row = saved["probes"][name]
        assert row["sender"] == sender and row["arguments"] == [instrument, first, second, third, fourth]
        assert row["calldata"] == SETTER + "".join(word(value)[2:] for value in row["arguments"])
        if name.startswith("owner_instrument_"):
            assert not row["error"] and len(row["logs"]) == 1
            event = row["logs"][0]
            assert event["address"].lower() == PROXY and event["topics"] == [EVENT, word(instrument)]
            assert words(event["data"]) == [first, second, third, fourth]
            before = by_id[instrument]
            assert row["pre_storage"] == dict(zip(before["slots"], before["words"]))
            assert set(row["post_storage"]) == set(before["slots"])
            old = [int(value, 16) for value in before["words"]]
            new = [int(row["post_storage"][slot], 16) for slot in before["slots"]]
            expected = [
                (old[0] & (((1 << 64) - 1) << 192)) | (second << 96) | third,
                (old[1] & ~(((1 << 64) - 1) << 184)) | (fourth << 184),
                (old[2] & ~((1 << 128) - 1)) | first,
            ]
            assert new == expected, (name, new, expected)
            getter_before = words(before["getter"])
            getter_after = words(row["getter_after_override"])
            assert len(getter_before) == len(getter_after) == 8
            changes = {i: (a, b) for i, (a, b) in enumerate(zip(getter_before, getter_after)) if a != b}
            assert changes == {0: (getter_before[0], third), 1: (getter_before[1], second),
                               6: (getter_before[6], fourth), 7: (getter_before[7], first)}, changes
            successes.append(name)
        else:
            assert row["error"] and not row["logs"]
            reverts[name] = row["output"][:10]
    assert "0x" + KECCAK(b"NotOwner()").hex()[:8] == reverts["outsider_instrument_0"]
    assert "0x" + KECCAK(b"InvalidInstrumentId()").hex()[:8] == reverts["owner_invalid_instrument_2"]
    result = {"pin": PIN, "block_hash": manifest["block_hash"], "exchange_proxy": PROXY,
              "implementation": IMPLEMENTATION, "setter_selector": SETTER, "getter_signature": "instruments(uint32)",
              "event_topic0": EVENT, "raw_evidence": "../../artifacts/exchange_instrument_admin/pinned_probes.json",
               "local_replay": "../../artifacts/exchange_instrument_admin_local/replay.json",
              "instrument_count": 2, "probe_count": len(CASES), "successes": successes, "revert_selectors": reverts,
              "storage_layout": {"mapping_base": 7, "word0": "third uint96 low, second uint96 bits 96..191, preserved high64",
                                 "word1": "fourth uint64 bits 184..247, other bits preserved",
                                 "word2": "first uint128 low, high128 preserved"},
              "getter_return_changes": {"third": 0, "second": 1, "fourth": 6, "first": 7},
              "event_layout": "indexed uint32 instrument; unindexed uint128 first, uint96 second, uint96 third, uint64 fourth",
              "event_catalog": [{"topic0": EVENT, "reconstructed_signature": "",
                                 "status": "simulated_log_only"}],
              "simulated_error_catalog": [
                  {"selector": "0x30cd7471", "reconstructed_signature": "NotOwner()",
                   "probe_paths": ["outsider_instrument_0", "keeper_instrument_0"]},
                  {"selector": "0x67207a88", "reconstructed_signature": "InvalidInstrumentId()",
                   "probe_paths": ["owner_invalid_instrument_2"]},
                  {"selector": "0xb0cb274d", "probe_paths": ["owner_zero_first",
                   "owner_zero_third", "owner_rate_upper_bound"]}],
              "limits": ["No historical transaction or emitted event with this setter was found in the saved samples.",
                         "The setter and event names and the four parameter meanings remain unresolved.",
                         "Read-only simulations do not establish later behavior after committing changed instrument values."]}
    BEHAVIOR.write_text(json.dumps(result, indent=2) + "\n")
    print({"probes": len(CASES), "successes": successes, "reverts": reverts})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
