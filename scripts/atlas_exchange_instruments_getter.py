#!/usr/bin/env python3
"""Verify the pinned Exchange instrument struct getter and packed storage words."""

import argparse
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SAVED = ROOT / "artifacts" / "exchange_instruments_getter" / "pinned_getters.json"
OUT = ATLAS / "exchange_instruments_getter_behavior.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SELECTOR = "0xdc8a47ef"
SIGNATURE = "instruments(uint32)"
KECCAK = Keccak()


def mapping_root(instrument_id):
    return int.from_bytes(KECCAK(instrument_id.to_bytes(32, "big") + (7).to_bytes(32, "big")), "big")


def split_words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def capture():
    from atlas_session_keys import rpc

    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    pin = manifest["block"]
    header = rpc(url, "eth_getBlockByNumber", [hex(pin), False])
    assert header["hash"].lower() == manifest["block_hash"]
    rows = []
    for instrument_id in (0, 1, 2):
        root = mapping_root(instrument_id)
        slots = [rpc(url, "eth_getStorageAt", [EXCHANGE, hex(root + i), hex(pin)])
                 for i in range(3)]
        calldata = SELECTOR + f"{instrument_id:064x}"
        output = rpc(url, "eth_call", [{"to": EXCHANGE, "data": calldata}, hex(pin)])
        rows.append({"instrument_id": instrument_id, "mapping_root": f"0x{root:064x}",
                     "storage_words": slots, "getter_output": output})
    SAVED.parent.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin": pin, "block_hash": header["hash"],
                                 "rows": rows}, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    storage = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert manifest["block"] == saved["pin"] == 48902346
    assert manifest["block_hash"] == saved["block_hash"].lower()
    assert "0x" + KECCAK(SIGNATURE.encode())[:4].hex() == SELECTOR
    view = next(row for row in storage[IMPLEMENTATION]["views"] if row["selector"] == SELECTOR)
    assert view["target"] == EXCHANGE and view["sample_argument"] == 1 and not view["failed"]
    assert [item["base_slot"] for item in view["mapping_matches"]] == [7, 7, 7]
    assert [item["field_offset"] for item in view["mapping_matches"]] == [0, 1, 2]
    assert {row["instrument_id"] for row in saved["rows"]} == {0, 1, 2}
    decoded = []
    for row in sorted(saved["rows"], key=lambda item: item["instrument_id"]):
        instrument_id = row["instrument_id"]
        root = mapping_root(instrument_id)
        assert int(row["mapping_root"], 16) == root
        assert len(row["storage_words"]) == 3
        s0, s1, s2 = (int(word, 16) for word in row["storage_words"])
        returned = split_words(row["getter_output"])
        assert len(returned) == 8
        expected = [
            s0 & ((1 << 96) - 1),
            (s0 >> 96) & ((1 << 96) - 1),
            (s0 >> 192) & ((1 << 32) - 1),
            s0 >> 224,
            s1 & ((1 << 120) - 1),
            (s1 >> 120) & ((1 << 64) - 1),
            s1 >> 184,
            s2,
        ]
        assert returned == expected
        if instrument_id in (0, 1):
            assert any(returned)
        else:
            assert returned == [0] * 8
        decoded.append({"instrument_id": instrument_id,
                        "mapping_root": row["mapping_root"],
                        "storage_words": row["storage_words"],
                        "returned_fields": returned})
    return {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION,
        "selector_reconstructions": {SELECTOR: SIGNATURE},
        "mapping_base_slot": 7,
        "sample_count": len(decoded), "return_word_count": 8,
        "field_extraction": ["slot0 low96", "slot0 bits96..191", "slot0 bits192..223",
                             "slot0 bits224..255", "slot1 low120", "slot1 bits120..183",
                             "slot1 bits184..255", "slot2 sampled full word"],
        "samples": decoded,
        "limits": [
            "The sampled third storage word has zero high bits, so its declared source integer width is unresolved.",
            "The business meaning of each returned field is not established by this getter check.",
            "Instrument IDs 0 and 1 are live; ID 2 returned an all-zero tuple at the pin.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh pinned getter and raw storage calls")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange instruments getter: {result['sample_count']} IDs, "
          f"{result['return_word_count']} returned words each")
