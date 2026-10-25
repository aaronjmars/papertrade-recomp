#!/usr/bin/env python3
"""Reconcile three saved proxy creation diffs with initializer calldata and pinned code."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "deployment_state_diffs_behavior.json"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
SPECS = {
    "staking": ("deployment", "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016", "0x9ccae24e"),
    "paper_token": ("deployment", "0xe40f17915daa230324030003a197cdaef2261c0e", "0x8f15b414"),
    "session_creation": ("0xe055509195f0ea1b9e30c366c3350d10470d8c1d145bfa51686b49134d36ffbe",
                         "0x8326eb8896e358717f10502ec73ce8d28e37b108", "0x747b8a1c"),
}


def slot(number):
    return f"0x{number:064x}"


def word(data, index):
    return int.from_bytes(data[4 + 32 * index:4 + 32 * (index + 1)], "big")


def address(value):
    assert 0 <= value < 2**160
    return f"0x{value:040x}"


def string_argument(data, index):
    offset = word(data, index)
    assert offset % 32 == 0 and 4 + offset + 32 <= len(data)
    length = int.from_bytes(data[4 + offset:4 + offset + 32], "big")
    assert 4 + offset + 32 + length <= len(data)
    return data[4 + offset + 32:4 + offset + 32 + length].decode()


def short_string_word(value):
    raw = value.encode()
    assert len(raw) <= 31
    return int.from_bytes(raw.ljust(31, b"\0") + bytes([len(raw) * 2]), "big")


def expected_direct(directory, data):
    if directory == "staking":
        args = [address(word(data, i)) for i in range(5)]
        behavior = json.loads((ATLAS / "staking_behavior.json").read_text())
        assert args == behavior["deployment_initializer"]["arguments"]
        assert args[-1] == address(0)
        return {0: 1, 1: int("71706d56c8b436981e93987cd97df512528491b243c6d8d1614cad52659e7eb0", 16),
                2: int(args[0], 16), 3: int(args[1], 16), 4: int(args[2], 16),
                13: 1, 15: int(args[3], 16), 16: (1 << 160) | int(args[4], 16)}
    if directory == "paper_token":
        name, symbol = string_argument(data, 0), string_argument(data, 1)
        owner, minter = address(word(data, 2)), address(word(data, 3))
        behavior = json.loads((ATLAS / "paper_token_behavior.json").read_text())["initializer"]
        assert [name, symbol] == behavior["strings"]
        assert owner == behavior["owner"] and minter == behavior["minter"]
        return {0: 1, 1: short_string_word(name), 2: short_string_word(symbol),
                3: int(owner, 16), 4: int(minter, 16)}
    owner, authorized_caller = address(word(data, 0)), address(word(data, 4))
    name, version, chain_id = string_argument(data, 1), string_argument(data, 2), word(data, 3)
    behavior = json.loads((ATLAS / "session_initializer_behavior.json").read_text())
    assert (owner, name, version, chain_id, authorized_caller) == tuple(
        behavior["historical_creation"]["decoded_arguments"][key]
        for key in ("owner", "name", "version", "chain_id", "authorized_caller"))
    return {0: 1, 1: int(behavior["fresh_state"]["domain_separator_historical"], 16),
            2: int(owner, 16), 3: int(authorized_caller, 16)}


def main():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    writes = json.loads((ATLAS / "state_write_catalog.json").read_text())
    rows = {}
    for directory, (stem, proxy, selector) in SPECS.items():
        folder = ROOT / "artifacts" / directory
        receipt_path = folder / f"{stem}.receipt.json"
        calls_path = folder / f"{stem}.calls.json"
        diff_path = folder / f"{stem}.state_diff.json"
        receipt = json.loads(receipt_path.read_text())
        calls = json.loads(calls_path.read_text())
        diff = json.loads(diff_path.read_text())
        tx = receipt["transactionHash"].lower()
        assert receipt["status"] == "0x1" and receipt["contractAddress"].lower() == proxy
        assert int(receipt["blockNumber"], 16) <= manifest["block"]
        assert calls["type"] == "CREATE" and calls["to"].lower() == proxy
        assert len(calls["calls"]) >= 1
        child = calls["calls"][0]
        assert child["type"] == "DELEGATECALL" and child["input"].startswith(selector)
        assert child["to"].lower() == "0x" + manifest["contracts"][proxy]["eip1967_slots"]["implementation"][-40:]
        assert proxy not in diff["pre"] and proxy in diff["post"]
        post = diff["post"][proxy]
        code = bytes.fromhex(post["code"].removeprefix("0x"))
        assert hashlib.sha256(code).hexdigest() == manifest["contracts"][proxy]["sha256"]
        stored = post["storage"]
        data = bytes.fromhex(child["input"][2:])
        direct = expected_direct(directory, data)
        expected = {slot(index): value for index, value in direct.items()}
        expected[IMPLEMENTATION_SLOT] = int(manifest["contracts"][proxy]["eip1967_slots"]["implementation"], 16)
        expected[ADMIN_SLOT] = int(manifest["contracts"][proxy]["eip1967_slots"]["admin"], 16)
        assert {key: int(value, 16) for key, value in stored.items()} == expected
        assert len(receipt["logs"]) == 2 and all(log["address"].lower() == proxy for log in receipt["logs"])

        graph_row = next(row for row in graph["traces"] if row["hash"] == tx)
        assert graph_row["root_call_type"] == "CREATE" and graph_row["root_selector"] is None
        assert graph_row["source_directory"] == directory
        write_row = next(row for row in writes["transactions"] if row["tx"] == tx)
        assert write_row["root_call_type"] == "CREATE" and write_row["root_selector"] is None
        assert write_row["source_directory"] == directory
        proxy_change = next(change for change in write_row["changes"] if change["address"] == proxy)
        assert {int(item["slot"], 16): int(item["value"], 16)
                for item in proxy_change["direct_slots"]} == direct
        assert {item["kind"] for item in proxy_change["proxy_control_slots"]} == {"implementation", "admin"}
        assert not proxy_change["dynamic_slots"]
        rows[directory] = {
            "transaction_hash": tx, "block": int(receipt["blockNumber"], 16),
            "proxy": proxy, "implementation": child["to"].lower(), "selector": selector,
            "proxy_runtime_sha256": manifest["contracts"][proxy]["sha256"],
            "direct_slot_values": {str(index): hex(value) for index, value in sorted(direct.items())},
            "implementation_slot_value": hex(expected[IMPLEMENTATION_SLOT]),
            "admin_slot_value": hex(expected[ADMIN_SLOT]),
            "event_count": len(receipt["logs"]),
            "artifacts": {kind: f"../../artifacts/{directory}/{stem}.{kind}.json"
                          for kind in ("calls", "receipt", "state_diff")},
            "state_diff_sha256": hashlib.sha256(diff_path.read_bytes()).hexdigest(),
        }
    result = {"pin": manifest["block"], "block_hash": manifest["block_hash"],
              "verified_creations": rows,
              "scope": "Three archived successful creations with saved call traces, receipts, and prestateTracer state diffs; exact created proxy code and every written proxy slot checked"}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("verified 3 archived proxy creation state diffs")


if __name__ == "__main__":
    main()
