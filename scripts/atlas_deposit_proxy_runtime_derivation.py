#!/usr/bin/env python3
"""Derive the deployed runtime of every recorded Papertrade user proxy."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from atlas_factory_events import Keccak
from trace import rpc

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "deposit_runtime_derivation"
DEPLOY_TX = "0xddf30f3fd0d78c0516e37f32ed1ece2ef4ab488d7b4be8439c7196878047fb2e"
FACTORY = "0x1629b7d46bef6e13ff754174fc9f32dea309b38f"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
PIN = 48902346
RUNTIME_OFFSET = 0xB3
RUNTIME_BYTES = 0x66E
EXCHANGE_WORD_OFFSETS = (0x61, 0xDE)
USER_WORD_OFFSETS = (0x37B, 0x3DA)
SAMPLE_OUTPUT = ARTIFACTS / "pinned_constructor_calls.json"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def word(address):
    return int(address, 16).to_bytes(32, "big")


def initcode_and_history():
    root = read(ROOT / "artifacts" / "historical" / f"{DEPLOY_TX}.calls.json")
    create = root["calls"][0]["calls"][0]
    assert create["type"] == "CREATE2" and create["from"].lower() == FACTORY
    assert create["value"] == "0x0" and not create.get("error")
    initcode = bytes.fromhex(create["input"][2:])
    assert len(initcode) == 1889 and len(create["output"]) == 2 + RUNTIME_BYTES * 2
    assert initcode[-64:-32] == word(EXCHANGE)
    assert len(initcode[:-32]) == 1857
    return initcode, create


def constructor_instructions(constructor):
    assert len(constructor) == RUNTIME_OFFSET
    assert hashlib.sha256(constructor).hexdigest() == (
        "ec9306ba34061baa4ca3a0d7cc650203d4702486293305fc15275a554e37d2a7")
    output = subprocess.run(["cast", "disassemble", "0x" + constructor.hex()],
                            capture_output=True, text=True, check=True).stdout
    instructions = {int(line.split(":", 1)[0], 16): line.split(":", 1)[1].strip()
                    for line in output.splitlines() if ":" in line}
    expected = {0x5D: "PUSH2 0x066e", 0x62: "PUSH2 0x00b3", 0x66: "CODECOPY",
                0x6D: "PUSH1 0x61", 0x70: "MSTORE", 0x71: "PUSH1 0xde",
                0x74: "MSTORE", 0x7B: "PUSH2 0x037b", 0x7F: "MSTORE",
                0x80: "PUSH2 0x03da", 0x84: "MSTORE", 0x85: "RETURN"}
    for pc, opcode in expected.items():
        assert instructions[pc] == opcode, (pc, instructions[pc])
    safe = {"CALLVALUE", "CODESIZE", "CODECOPY", "MLOAD", "MSTORE", "ADD", "SUB",
            "SHL", "AND", "NOT", "GT", "LT", "SLT", "OR", "JUMP", "JUMPI",
            "JUMPDEST", "RETURN", "REVERT", "INVALID"}
    for instruction in instructions.values():
        opcode = instruction.split()[0]
        assert opcode in safe or opcode.startswith(("PUSH", "DUP", "SWAP")), opcode
    return len(instructions)


def runtime_for(base, user):
    runtime = bytearray(base)
    for offset in EXCHANGE_WORD_OFFSETS:
        runtime[offset:offset + 32] = word(EXCHANGE)
    for offset in USER_WORD_OFFSETS:
        runtime[offset:offset + 32] = word(user)
    return bytes(runtime)


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    manifest = read(ATLAS / "manifest.json")
    header = rpc("eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    initcode, _ = initcode_and_history()
    prefix = initcode[:-32]
    family = read(ATLAS / "deposit_proxy_family.json")
    by_proxy = {row["proxy"]: row["user"]
                for row in read(ATLAS / "factory_user_proxy_map.json")}
    if SAMPLE_OUTPUT.exists():
        saved = read(SAMPLE_OUTPUT)
        assert saved["block_hash"].lower() == header["hash"].lower()
    else:
        samples = [family["records"][0], family["records"][-1]]
        rows = []
        for sample in samples:
            user = by_proxy[sample["address"]]
            call = {"from": "0x3333333333333333333333333333333333333333",
                    "data": "0x" + (prefix + word(user)).hex(), "gas": "0x989680"}
            output = rpc("eth_call", [call, hex(PIN)])
            rows.append({"proxy": sample["address"], "user": user,
                         "runtime": output, "sha256": hashlib.sha256(bytes.fromhex(output[2:])).hexdigest()})
            print("simulated constructor", sample["address"], flush=True)
        saved = {"pin": PIN, "block_hash": header["hash"], "rows": rows}
    if "direct_unsampled_runtime" not in saved:
        unsampled = read(ATLAS / "factory_user_proxy_map.json")[12345]
        assert unsampled["proxy"] not in {row["address"] for row in family["records"]}
        code = rpc("eth_getCode", [unsampled["proxy"], hex(PIN)])
        saved["direct_unsampled_runtime"] = {
            "proxy": unsampled["proxy"], "user": unsampled["user"], "runtime": code,
            "sha256": hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()}
        print("fetched unsampled runtime", unsampled["proxy"], flush=True)
    write(SAMPLE_OUTPUT, saved)


def build():
    manifest = read(ATLAS / "manifest.json")
    initcode, create = initcode_and_history()
    instruction_count = constructor_instructions(initcode[:RUNTIME_OFFSET])
    base = initcode[RUNTIME_OFFSET:RUNTIME_OFFSET + RUNTIME_BYTES]
    assert len(base) == RUNTIME_BYTES
    assert RUNTIME_OFFSET + RUNTIME_BYTES == len(initcode) - 64
    first_user = "0x" + initcode[-20:].hex()
    assert bytes.fromhex(create["output"][2:]) == runtime_for(base, first_user)
    runtime_disassembly = subprocess.run(
        ["cast", "disassemble", create["output"]], capture_output=True, text=True,
        check=True).stdout
    assert not any(line.split()[-1] in ("SELFDESTRUCT", "DELEGATECALL", "CALLCODE")
                   for line in runtime_disassembly.splitlines() if line.strip())
    family = read(ATLAS / "deposit_proxy_family.json")
    deployments = read(ATLAS / "factory_event_deployments.json")
    mapping = read(ATLAS / "factory_user_proxy_map.json")
    assert deployments["event_count"] == len(mapping) == family["instance_count"] == 22586
    assert deployments["create2_formula_matches"] == len(mapping)
    by_proxy = {row["proxy"]: row["user"] for row in mapping}
    assert len(by_proxy) == len(mapping)
    assert by_proxy[create["to"].lower()] == first_user
    sample_matches = 0
    for sample in family["records"]:
        user = by_proxy[sample["address"]]
        runtime = runtime_for(base, user)
        assert len(runtime) == sample["runtime_bytes"] == RUNTIME_BYTES
        assert hashlib.sha256(runtime).hexdigest() == sample["sha256"]
        assert all(runtime[start:end].hex() == sample["varying_bytes"][f"{start}:{end}"]
                   for start, end in family["varying_byte_ranges"])
        normalized = bytearray(runtime)
        for start, end in family["varying_byte_ranges"]:
            normalized[start:end] = bytes(end - start)
        assert hashlib.sha256(normalized).hexdigest() == family["normalized_sha256"]
        sample_matches += 1
    representative = bytes.fromhex((ATLAS / family["representative_runtime_file"]).read_text().strip()[2:])
    assert representative == runtime_for(base, by_proxy[family["records"][0]["address"]])
    historical = read(ROOT / "artifacts" / "deposit_proxy_probes" / "historical_proxy_code.json")
    assert historical["block_hash"].lower() == manifest["block_hash"]
    historical_user = by_proxy[historical["address"].lower()]
    assert bytes.fromhex(historical["code"][2:]) == runtime_for(base, historical_user)
    assert historical["address"].lower() in {row["address"] for row in family["records"]}
    simulated = read(SAMPLE_OUTPUT)
    assert simulated["pin"] == PIN and simulated["block_hash"].lower() == manifest["block_hash"]
    assert len(simulated["rows"]) == 2
    for row in simulated["rows"]:
        assert by_proxy[row["proxy"]] == row["user"]
        assert bytes.fromhex(row["runtime"][2:]) == runtime_for(base, row["user"])
        assert row["sha256"] == hashlib.sha256(runtime_for(base, row["user"])).hexdigest()
    extra = simulated["direct_unsampled_runtime"]
    assert extra["proxy"] not in {row["address"] for row in family["records"]}
    assert by_proxy[extra["proxy"]] == extra["user"]
    assert bytes.fromhex(extra["runtime"][2:]) == runtime_for(base, extra["user"])
    assert extra["sha256"] == hashlib.sha256(runtime_for(base, extra["user"])).hexdigest()
    keccak = Keccak()
    runtime_rows = []
    distinct_hashes = set()
    prefix = initcode[:-32]
    for row in mapping:
        user, proxy = row["user"], row["proxy"]
        creation_hash = keccak(prefix + word(user))
        salt = keccak(bytes.fromhex(user[2:]))
        predicted = "0x" + keccak(b"\xff" + bytes.fromhex(FACTORY[2:]) + salt + creation_hash)[-20:].hex()
        assert predicted == proxy
        digest = hashlib.sha256(runtime_for(base, user)).hexdigest()
        assert digest not in distinct_hashes
        distinct_hashes.add(digest)
        runtime_rows.append({"proxy": proxy, "user": user, "runtime_sha256": digest})
    map_path = ATLAS / "deposit_proxy_derived_runtime_map.json"
    write(map_path, {"pin": PIN, "runtime_bytes": RUNTIME_BYTES,
                     "source": "deterministic captured CREATE2 initcode plus event user",
                     "rows": runtime_rows})
    report = {"pin": PIN, "block_hash": manifest["block_hash"],
              "factory": FACTORY, "exchange": EXCHANGE,
              "deployment_count": len(runtime_rows),
              "derived_runtime_count": len(distinct_hashes),
              "runtime_bytes": RUNTIME_BYTES,
              "constructor_bytes": RUNTIME_OFFSET,
              "constructor_sha256": hashlib.sha256(initcode[:RUNTIME_OFFSET]).hexdigest(),
              "constructor_instruction_count": instruction_count,
              "creation_prefix_bytes": len(prefix),
              "runtime_template_sha256": family["normalized_sha256"],
              "exchange_word_offsets": list(EXCHANGE_WORD_OFFSETS),
              "user_word_offsets": list(USER_WORD_OFFSETS),
              "historical_create_output_exact_match": True,
              "fetched_runtime_hash_matches": sample_matches,
              "fetched_representative_bytes_match": True,
              "additional_unsampled_fetched_runtime_match": True,
              "directly_fetched_distinct_runtime_count": sample_matches + 1,
              "pinned_constructor_simulations_match": len(simulated["rows"]),
              "all_create2_addresses_recomputed": len(runtime_rows),
              "runtime_has_no_selfdestruct_delegatecall_or_callcode": True,
              "derived_runtime_map": map_path.name,
              "limitations": ["Only 42 distinct deployed runtimes were fetched at the pin.",
                              "The remaining pinned code bodies are derived from deterministic initcode and matching CREATE2 addresses, not individually fetched.",
                              "This does not prove every factory or user proxy function branch."]}
    write(ATLAS / "deposit_proxy_runtime_derivation.json", report)
    print("derived", len(runtime_rows), "runtimes; matched", sample_matches,
          "fetched hashes and", len(simulated["rows"]), "pinned constructor simulations")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    build()
