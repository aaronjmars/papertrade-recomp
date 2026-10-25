#!/usr/bin/env python3
"""Verify the live Exchange mapping-35 four-field getter offline."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "exchange_mapping35_view_behavior.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SELECTOR = "0xc8372577"
PIN = 48902346


def read(name):
    return json.loads((ATLAS / name).read_text())


def cast(*args):
    return subprocess.run(["cast", *args], capture_output=True, text=True, check=True).stdout.strip()


def main():
    manifest = read("manifest.json")
    assert manifest["block"] == PIN
    runtime_row = manifest["contracts"][IMPLEMENTATION]
    runtime_hex = (ATLAS / runtime_row["runtime_file"]).read_text().strip()
    runtime = bytes.fromhex(runtime_hex.removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == runtime_row["sha256"]
    assert bytes.fromhex("63c83725771461172d57") in runtime[:0x400]
    assert runtime[0x172d] == 0x5b

    storage = read("storage_trace_catalog.json")[IMPLEMENTATION]["views"]
    probe = next(row for row in storage if row["selector"] == SELECTOR)
    assert probe["target"].lower() == EXCHANGE and probe["sample_argument"] == 1
    assert not probe["failed"] and int(probe["return_prefix"], 16) == 0
    assert probe["mapping_matches"] == [{"base_slot": 35, "field_offset": 0,
                                          "read_slot": probe["mapping_matches"][0]["read_slot"], "pc": 5979}]
    slot_1 = cast("index", "uint32", "1", "35").lower()
    slot_0 = cast("index", "uint32", "0", "35").lower()
    assert probe["mapping_matches"][0]["read_slot"].lower() == slot_1

    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", runtime_hex],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1] for line in disassembly.splitlines()
                    if len(line) > 10 and line[8:10] == ": "}
    expected = {0x172d: "JUMPDEST", 0x172f: "CALLVALUE", 0x1745: "PUSH4 0xffffffff",
                0x174d: "PUSH2 0x3ec9", 0x1755: "PUSH1 0x23",
                0x175a: "KECCAK256", 0x175b: "SLOAD", 0x1767: "PUSH1 0xff",
                0x176a: "AND", 0x176b: "ISZERO", 0x176c: "ISZERO",
                0x1771: "PUSH1 0x08", 0x1773: "SHR", 0x1774: "AND",
                0x177c: "PUSH1 0x48", 0x177e: "SHR", 0x177f: "AND",
                0x1785: "PUSH1 0x88", 0x1787: "SHR", 0x1788: "AND",
                0x178e: "RETURN"}
    for pc, op in expected.items():
        assert instructions[pc] == op, (hex(pc), instructions[pc], op)
    assert sum(instructions[pc] == "SLOAD" for pc in instructions if 0x172d <= pc < 0x178f) == 1
    assert not [instructions[pc] for pc in instructions if 0x172d <= pc < 0x178f
                and instructions[pc] in ("SSTORE", "TSTORE", "CALL", "DELEGATECALL", "STATICCALL")]

    writes = read("state_write_catalog.json")["transactions"]
    matching_writes = []
    for row in writes:
        if any(slot in change.get("dynamic_slots", []) for change in row["changes"]
               for slot in (slot_0, slot_1)):
            matching_writes.append(row["tx"])
    assert not matching_writes
    prestate_files = sorted((ROOT / "artifacts" / "staking").glob("*.prestate.json"))
    zero_prestates = []
    for path in prestate_files:
        state = json.loads(path.read_text())
        value = state.get(EXCHANGE, {}).get("storage", {}).get(slot_0)
        if value is not None:
            assert int(value, 16) == 0
            zero_prestates.append(path.name)
    assert len(zero_prestates) >= 5

    behavior = {
        "pin": PIN, "block_hash": manifest["block_hash"],
        "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION, "selector": SELECTOR,
        "source_name_status": "unresolved", "raw_evidence": "storage_trace_catalog.json",
        "mapping_base_slot": 35, "sample_key": 1, "sample_storage_slot": slot_1,
        "sample_return_prefix": probe["return_prefix"],
        "runtime_sha256": runtime_row["sha256"], "dispatcher_entry_pc": 0x172d,
        "return_layout": ["bool(word & 0xff)", "uint64((word >> 8) & (2^64 - 1))",
                          "uint64((word >> 72) & (2^64 - 1))",
                          "uint64((word >> 136) & (2^64 - 1))"],
        "return_bytes": 128,
        "saved_state_write_count_for_keys_0_and_1": 0,
        "saved_key_0_zero_prestates": len(zero_prestates),
        "limits": ["The pinned probe records only the first 63 return bytes; the full four-word return and layout come from pinned runtime instructions.",
                   "The sampled key 1 and saved key 0 prestates are zero. Field names and the function that writes mapping slot 35 remain unresolved.",
                   "The absence of writes in the saved trace sample does not prove the mapping is never written."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified Exchange mapping-35 four-field getter")


if __name__ == "__main__":
    main()
