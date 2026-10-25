#!/usr/bin/env python3
"""Verify Exchange position and queue mapping getter names at archived states."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_mapping_getters"
SAVED = ARTIFACTS / "mapping_getters.json"
OUT = ATLAS / "exchange_mapping_getters_behavior.json"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN = 48902346
QUEUE_BLOCK = 48173889
POSITION_IDS = (1394473, 1394058, 1394062, 1394060)
USER_POSITION_ID = 1394060
KECCAK = Keccak()
LOW160 = (1 << 160) - 1
LOW48 = (1 << 48) - 1
LOW128 = (1 << 128) - 1
NAMES = {
    "0x99fbab88": "positions(uint256)",
    "0xa25dc87f": "getUserOpenPositionIds(address)",
    "0xb3060d36": "positionOwner(uint256)",
    "0xdcab7f6a": "userQueueHead(address)",
    "0xe634384f": "queueNode(uint256)",
}


def word(value):
    return int(value, 16).to_bytes(32, "big").hex() if isinstance(value, str) else value.to_bytes(32, "big").hex()


def mapping_slot(key, base):
    return int.from_bytes(KECCAK(bytes.fromhex(word(key) + word(base))), "big")


def outputs(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    pin_header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    queue_header = rpc(url, "eth_getBlockByNumber", [hex(QUEUE_BLOCK), False])
    assert pin_header["hash"].lower() == manifest["block_hash"]

    def getter(selector, key, block, override=None):
        params = [{"to": PROXY, "data": selector + word(key)}, hex(block)]
        if override is not None:
            params.append(override)
        return rpc(url, "eth_call", params)

    def storage(slot, block):
        return rpc(url, "eth_getStorageAt", [PROXY, hex(slot), hex(block)])

    positions = []
    for position_id in POSITION_IDS:
        root = mapping_slot(position_id, 10)
        positions.append({"position_id": position_id, "root_slot": hex(root),
                          "word0": storage(root, PIN), "word1": storage(root + 1, PIN),
                          "positions_output": getter("0x99fbab88", position_id, PIN),
                          "owner_output": getter("0xb3060d36", position_id, PIN)})
    selected = next(row for row in positions if row["position_id"] == USER_POSITION_ID)
    user = "0x" + selected["word0"][-40:]
    array_root = mapping_slot(user, 12)
    array_length = int(storage(array_root, PIN), 16)
    assert array_length <= 32
    array_base = int.from_bytes(KECCAK(array_root.to_bytes(32, "big")), "big")
    ids = [storage((array_base + i) % (1 << 256), PIN) for i in range(array_length)]
    id_position_words = []
    for id_word in ids:
        position_root = mapping_slot(int(id_word, 16), 10)
        id_position_words.append({"position_id": int(id_word, 16),
                                  "word0": storage(position_root, PIN),
                                  "word1": storage(position_root + 1, PIN)})
    open_ids = {"user": user, "root_slot": hex(array_root), "length_word": storage(array_root, PIN),
                "array_base_slot": hex(array_base), "id_words": ids,
                "id_position_words": id_position_words,
                "getter_output": getter("0xa25dc87f", user, PIN)}
    outsider = "0x" + "33" * 20
    empty_ids = {"user": outsider, "root_slot": hex(mapping_slot(outsider, 12)),
                 "length_word": storage(mapping_slot(outsider, 12), PIN),
                 "getter_output": getter("0xa25dc87f", outsider, PIN)}
    enqueues = json.loads((ATLAS / "exchange_queue_layout_behavior.json").read_text())["enqueues"]
    queue = []
    for event in enqueues:
        node_id, user = event["node_id"], event["user"]
        node_root = mapping_slot(node_id, 15)
        head_slot = mapping_slot(user, 20)
        queue.append({"node_id": node_id, "user": user, "amount": event["amount"],
                      "root_slot": hex(node_root), "word0": storage(node_root, QUEUE_BLOCK),
                      "word1": storage(node_root + 1, QUEUE_BLOCK),
                      "node_output": getter("0xe634384f", node_id, QUEUE_BLOCK),
                      "head_slot": hex(head_slot), "head_word": storage(head_slot, QUEUE_BLOCK),
                      "head_output": getter("0xdcab7f6a", user, QUEUE_BLOCK)})
    position = positions[0]
    position_slot = int(position["root_slot"], 16) + 1
    position_word = int(position["word1"], 16)
    position_overrides = {}
    for name, value in (("side_flip", position_word ^ (1 << 224)),
                        ("low_bit1_on", position_word | (1 << 225)),
                        ("secondary_low_on", position_word | (1 << 232)),
                        ("secondary_high_on", position_word | (1 << 239)),
                        ("active_off", position_word & ~(1 << 240))):
        override = {PROXY: {"stateDiff": {"0x" + word(position_slot): "0x" + word(value)}}}
        position_overrides[name] = {"replacement_word": "0x" + word(value),
                                    "getter_output": getter("0x99fbab88", position["position_id"], PIN, override)}
    node = queue[0]
    node_slot = int(node["root_slot"], 16)
    linked_word = int(node["word0"], 16) | (2 << 160) | (3 << 208)
    linked_override = {PROXY: {"stateDiff": {"0x" + word(node_slot): "0x" + word(linked_word)}}}
    queue_override = {"replacement_word": "0x" + word(linked_word),
                      "getter_output": getter("0xe634384f", node["node_id"], QUEUE_BLOCK, linked_override)}
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin_block": PIN, "pin_hash": pin_header["hash"],
                                 "queue_block": QUEUE_BLOCK, "queue_hash": queue_header["hash"],
                                 "positions": positions, "open_ids": open_ids, "empty_ids": empty_ids,
                                 "queue": queue, "position_overrides": position_overrides,
                                 "queue_override": queue_override}, indent=2) + "\n")


def decode_position(raw0, raw1):
    return [raw0 & LOW160, (raw0 >> 160) & ((1 << 32) - 1), (raw0 >> 192) & ((1 << 64) - 1),
            raw1 & LOW128, (raw1 >> 128) & ((1 << 32) - 1), (raw1 >> 160) & ((1 << 64) - 1),
            (raw1 >> 224) & 1, int(bool((raw1 >> 232) & 255)), (raw1 >> 240) & 1]


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert saved["pin_block"] == manifest["block"] == PIN
    assert saved["pin_hash"].lower() == manifest["block_hash"]
    assert saved["queue_block"] == QUEUE_BLOCK and saved["queue_hash"].startswith("0x")
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[IMPLEMENTATION]
    runtime_selectors = {row["selector"] for row in catalog["functions"]}
    traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]
    views = {row["selector"]: row for row in traces["views"]}
    expected_bases = {"0x99fbab88": 10, "0xa25dc87f": 12, "0xb3060d36": 10,
                      "0xdcab7f6a": 20, "0xe634384f": 15}
    for selector, name in NAMES.items():
        assert selector in runtime_selectors
        assert "0x" + KECCAK(name.encode()).hex()[:8] == selector
        assert any(row["base_slot"] == expected_bases[selector]
                   for row in views[selector]["mapping_matches"])
        assert not views[selector]["failed"]
    layout = json.loads((ATLAS / "exchange_position_layout.json").read_text())
    assert layout["mapping_base_slot"] == 10
    assert [row["position_id"] for row in saved["positions"]] == list(POSITION_IDS)
    for row in saved["positions"]:
        root = mapping_slot(row["position_id"], 10)
        assert int(row["root_slot"], 16) == root
        raw0, raw1 = int(row["word0"], 16), int(row["word1"], 16)
        assert outputs(row["positions_output"]) == decode_position(raw0, raw1)
        assert outputs(row["owner_output"]) == [raw0 & LOW160]
        assert (raw1 >> 240) & 1 == 1
    selected = next(row for row in saved["positions"] if row["position_id"] == USER_POSITION_ID)
    array = saved["open_ids"]
    user = "0x" + selected["word0"][-40:]
    assert array["user"] == user
    root = mapping_slot(user, 12)
    assert int(array["root_slot"], 16) == root
    assert int(array["length_word"], 16) == len(array["id_words"]) == 4
    assert int(array["array_base_slot"], 16) == int.from_bytes(KECCAK(root.to_bytes(32, "big")), "big")
    ids = [int(value, 16) for value in array["id_words"]]
    assert outputs(array["getter_output"]) == [32, len(ids), *ids]
    assert [row["position_id"] for row in array["id_position_words"]] == ids
    assert all(int(row["word0"], 16) & LOW160 == int(user, 16)
               and (int(row["word1"], 16) >> 240) & 1 == 1
               for row in array["id_position_words"])
    assert USER_POSITION_ID in ids
    empty = saved["empty_ids"]
    assert int(empty["root_slot"], 16) == mapping_slot(empty["user"], 12)
    assert int(empty["length_word"], 16) == 0
    assert outputs(empty["getter_output"]) == [32, 0]
    ledger = json.loads((ATLAS / "exchange_queue_layout_behavior.json").read_text())
    assert len(saved["queue"]) == len(ledger["enqueues"]) == 3
    for row, event in zip(saved["queue"], ledger["enqueues"], strict=True):
        assert (row["node_id"], row["user"], row["amount"]) == (event["node_id"], event["user"], event["amount"])
        root = mapping_slot(row["node_id"], 15)
        assert int(row["root_slot"], 16) == root
        owner_word, amount_word = int(row["word0"], 16), int(row["word1"], 16)
        assert outputs(row["node_output"]) == [owner_word & LOW160,
                                                 (owner_word >> 160) & LOW48,
                                                 (owner_word >> 208) & LOW48, amount_word]
        assert owner_word & LOW160 == int(row["user"], 16)
        assert amount_word == int(row["amount"])
        assert int(row["head_slot"], 16) == mapping_slot(row["user"], 20)
        assert int(row["head_word"], 16) == outputs(row["head_output"])[0] == row["node_id"]
    base_position = saved["positions"][0]
    original = outputs(base_position["positions_output"])
    variants = saved["position_overrides"]
    assert set(variants) == {"side_flip", "low_bit1_on", "secondary_low_on",
                             "secondary_high_on", "active_off"}
    assert outputs(variants["low_bit1_on"]["getter_output"]) == original
    for name, index, value in (("side_flip", 6, 1 - original[6]),
                               ("secondary_low_on", 7, 1),
                               ("secondary_high_on", 7, 1), ("active_off", 8, 0)):
        observed = outputs(variants[name]["getter_output"])
        expected = original.copy()
        expected[index] = value
        assert observed == expected
    node = saved["queue"][0]
    observed_link = outputs(saved["queue_override"]["getter_output"])
    assert observed_link == [int(node["user"], 16), 2, 3, int(node["amount"])]
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "queue_block": QUEUE_BLOCK, "queue_hash": saved["queue_hash"],
            "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": NAMES,
            "position_samples": saved["positions"], "open_ids": array,
            "empty_ids": empty, "queue_samples": saved["queue"],
            "position_override_count": len(variants), "queue_link_override": saved["queue_override"],
            "limits": ["The five names have exact selector hashes and archived behavior; original Solidity source is unavailable.",
                       "Four active positions, one nonempty user array, and three historical queue nodes sample these getters; other struct states remain open."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange mapping getters: {len(result['selector_reconstructions'])} names, "
          f"{len(result['position_samples'])} positions, {len(result['queue_samples'])} queue nodes")
