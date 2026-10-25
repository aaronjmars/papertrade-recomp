#!/usr/bin/env python3
"""Reconstruct the live Exchange market-keeper setter from saved evidence."""

import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
OUT = ATLAS / "exchange_market_keeper_behavior.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
TX = "0x3b3eab1fccbd0600aa196edc066d57f2d7a64b5c691f8fb9078457fe9199c79a"
SETTER = "0x060447aa"
GETTER = "0x21f55a6c"
TOPIC = "0xc76a9da20bd06b6b26d0826dab481a66785c609c15fae99817a557e61229e9c5"
SLOT = "0x" + f"{37:064x}"


def read(name):
    return json.loads((ATLAS / name).read_text())


def historical(suffix):
    return json.loads((HISTORICAL / f"{TX}.{suffix}.json").read_text())


def cast(command, arg):
    return subprocess.run(["cast", command, arg], capture_output=True, text=True, check=True).stdout.strip()


def main():
    manifest = read("manifest.json")
    runtime_path = ATLAS / manifest["contracts"][IMPLEMENTATION]["runtime_file"]
    runtime_hex = runtime_path.read_text().strip()
    runtime = bytes.fromhex(runtime_hex.removeprefix("0x"))
    assert hashlib.sha256(runtime).hexdigest() == manifest["contracts"][IMPLEMENTATION]["sha256"]
    assert cast("sig", "setMarketKeeper(address)") == SETTER
    assert cast("sig", "marketKeeper()") == GETTER
    assert cast("keccak", "MarketKeeperUpdated(address)") == TOPIC
    assert cast("sig", "NotOwner()") == "0x30cd7471"

    call = historical("calls")
    receipt = historical("receipt")
    diff = historical("state_diff")
    summary = historical("summary")
    assert summary["block"] == 47855442 and summary["status"] == 1
    assert call["to"].lower() == EXCHANGE and call["input"][:10] == SETTER
    assert len(call["input"]) == 74
    argument = "0x" + call["input"][-40:]
    assert len(receipt["logs"]) == 1
    log = receipt["logs"][0]
    assert log["address"].lower() == EXCHANGE and log["topics"] == [TOPIC, "0x" + call["input"][10:]]
    assert log["data"] == "0x"
    assert int(diff["post"][EXCHANGE]["storage"][SLOT], 16) == int(argument, 16)
    assert SLOT not in diff["pre"].get(EXCHANGE, {}).get("storage", {})

    storage = read("storage_trace_catalog.json")[IMPLEMENTATION]["views"]
    getter = next(row for row in storage if row["selector"] == GETTER)
    assert getter["target"].lower() == EXCHANGE and getter["direct_slots"] == [37]
    assert int(getter["return_prefix"], 16) == int(argument, 16)

    disassembly = json.loads(subprocess.run(["cast", "disassemble", "--json", runtime_hex],
                                            capture_output=True, text=True, check=True).stdout)["data"]
    instructions = {int(line[:8], 16): line.split(": ", 1)[1] for line in disassembly.splitlines()
                    if len(line) > 10 and line[8:10] == ": "}
    expected = {
        0x3e0a: "JUMPDEST", 0x3e0b: "CALLVALUE", 0x3e1c: "PUSH2 0x3e23",
        0x3e1f: "PUSH2 0x3eb3", 0x3e22: "JUMP", 0x3e24: "PUSH2 0x3e2b",
        0x3e27: "PUSH2 0x4a53", 0x3e2a: "JUMP", 0x3e2c: "PUSH1 0x25",
        0x3e2f: "SLOAD", 0x3e4a: "SSTORE", 0x3e4b: f"PUSH32 {TOPIC}",
        0x3e6e: "LOG2", 0x3e6f: "STOP", 0x3eb3: "JUMPDEST",
        0x3eb6: "CALLDATALOAD", 0x3ec3: "SUB", 0x3ec4: "PUSH2 0x0fdd",
        0x4a53: "JUMPDEST", 0x4a55: "SLOAD", 0x4a58: "SHR",
        0x4a62: "CALLER", 0x4a63: "SUB", 0x4a64: "PUSH2 0x4a69",
        0x4a6d: "PUSH4 0x30cd7471", 0x4a7a: "REVERT",
    }
    for pc, op in expected.items():
        assert instructions[pc] == op, (hex(pc), instructions[pc], op)
    setter_tail = [instructions[pc] for pc in sorted(instructions) if 0x3e2b <= pc < 0x3e70]
    assert "JUMPI" not in setter_tail and "JUMP" not in setter_tail

    behavior = {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION,
        "selector_reconstructions": {SETTER: "setMarketKeeper(address)", GETTER: "marketKeeper()"},
        "event_catalog": [{"topic0": TOPIC, "reconstructed_signature": "MarketKeeperUpdated(address)",
                           "status": "observed_historical_topic", "indexed_arguments": ["address marketKeeper"]}],
        "historical_tx": TX, "historical_block": summary["block"],
        "historical_caller": call["from"], "historical_argument": argument,
        "historical_slot_37_post": diff["post"][EXCHANGE]["storage"][SLOT],
        "pinned_getter_output": getter["return_prefix"],
        "runtime_sha256": hashlib.sha256(runtime).hexdigest(),
        "dispatcher_pc": 0x3e0a, "address_decoder_pc": 0x3eb3, "owner_check_pc": 0x4a53,
        "slot": 37, "owner_error_selector": "0x30cd7471",
        "behavior": "nonpayable; canonical address argument; caller must equal owner packed in slot 0; write argument into low 160 bits of slot 37, preserve high bits, emit indexed MarketKeeperUpdated(address)",
        "zero_address_rule": "No zero-address check occurs after ABI decoding and owner validation in the pinned runtime.",
        "limits": ["One successful historical transaction is saved. Owner and zero-address branches are derived from pinned bytecode and have no saved dynamic probe.",
                   "A later implementation upgrade could change this behavior."],
    }
    OUT.write_text(json.dumps(behavior, indent=2) + "\n")
    print("verified Exchange market keeper setter and getter")


if __name__ == "__main__":
    main()
