#!/usr/bin/env python3
"""Decode pinned Exchange accounting words and saved transaction deltas."""

import argparse
import collections
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
BLOCK = 48902346
BLOCK_HASH = "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
SLOTS = (11, 14, 16, 18, 22, 26)
MASK128 = (1 << 128) - 1
WORDS = ATLAS / "exchange_storage_words.json"


def rpc(url, method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(url, payload, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    block = rpc(url, "eth_getBlockByNumber", [hex(BLOCK), False])
    assert block["hash"].lower() == BLOCK_HASH
    words = {str(slot): rpc(url, "eth_getStorageAt", [EXCHANGE, hex(slot), hex(BLOCK)]).lower()
             for slot in SLOTS}
    assert all(len(word) == 66 for word in words.values())
    WORDS.write_text(json.dumps({"chain_id": 999, "block": BLOCK, "block_hash": BLOCK_HASH,
                                 "address": EXCHANGE, "slots": words}, indent=2) + "\n")


def fields(words):
    values = {slot: int(words[str(slot)], 16) for slot in SLOTS}
    return {
        "nextPositionId()": values[11],
        "treasury()": values[14],
        "queueHead()": values[16],
        "totalQueued()": values[18],
        "totalBalances()": values[22] & MASK128,
        "totalLockedMargin()": values[22] >> 128,
        "stakerFeeAccumulator()": values[26] & MASK128,
        "devFeeAccumulator()": values[26] >> 128,
    }


def trace_getters():
    views = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]["views"]
    return {view["candidate_signature"].split("|")[0]: view for view in views if not view["failed"]}


def transitions():
    catalog = {row["tx"]: row for row in json.loads((ATLAS / "state_write_catalog.json").read_text())["transactions"]}
    topics = {entry["topic0"].lower(): entry["name"] for entry in
              json.loads((ATLAS / "external_exchange_abi_hypermate.json").read_text())["abi"]
              if entry["type"] == "event"}
    rows = []
    for path in sorted(HISTORICAL.glob("*.state_diff.json")):
        tx = path.name.split(".")[0]
        diff = json.loads(path.read_text())
        before = diff["pre"].get(EXCHANGE, {}).get("storage", {})
        after = diff["post"].get(EXCHANGE, {}).get("storage", {})
        deltas = {}
        for slot in SLOTS:
            key = f"0x{slot:064x}"
            if key not in before and key not in after:
                continue
            # Geth diff-mode omits a zero-valued side of a storage change.
            left, right = int(before.get(key, "0x0"), 16), int(after.get(key, "0x0"), 16)
            if slot in (22, 26):
                names = ("totalBalances()", "totalLockedMargin()") if slot == 22 else (
                    "stakerFeeAccumulator()", "devFeeAccumulator()")
                deltas[names[0]] = (right & MASK128) - (left & MASK128)
                deltas[names[1]] = (right >> 128) - (left >> 128)
            else:
                name = {11: "nextPositionId()", 14: "treasury()", 16: "queueHead()",
                        18: "totalQueued()"}[slot]
                deltas[name] = right - left
        if not deltas:
            continue
        receipt = json.loads((HISTORICAL / f"{tx}.receipt.json").read_text())
        observed = collections.Counter(topics.get(log["topics"][0].lower(), "unknown")
                                       for log in receipt.get("logs", []) if log["address"].lower() == EXCHANGE)
        meta = catalog[tx]
        rows.append({"tx": tx, "block": meta["block"], "root_selector": meta["root_selector"],
                     "root_role": meta["root_role"], "exchange_events": dict(sorted(observed.items())),
                     "deltas": deltas})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh raw words from the pinned archive block")
    args = parser.parse_args()
    if args.capture:
        capture()
    snapshot = json.loads(WORDS.read_text())
    assert snapshot["block"] == BLOCK and snapshot["block_hash"] == BLOCK_HASH
    assert snapshot["address"] == EXCHANGE and set(snapshot["slots"]) == set(map(str, SLOTS))
    decoded = fields(snapshot["slots"])
    getters = trace_getters()
    for name, value in decoded.items():
        assert int(getters[name]["return_prefix"], 16) == value, f"{name} raw word vs opcode trace"
    reserve = sum(decoded[name] for name in ("totalBalances()", "totalLockedMargin()",
                                              "stakerFeeAccumulator()", "devFeeAccumulator()"))
    queue_available = max(decoded["treasury()"] - reserve, 0)
    assert decoded["totalQueued()"] == 0
    assert int(getters["lpBankrollAvailable()"]["return_prefix"], 16) == queue_available
    rows = transitions()
    result = {
        "pin": BLOCK, "block_hash": BLOCK_HASH, "address": EXCHANGE,
        "raw_words": "exchange_storage_words.json",
        "layout": {
            "11": "nextPositionId() uint256",
            "14": "treasury() numeric accounting amount; source integer width unresolved",
            "16": "queueHead() uint256",
            "18": "totalQueued() uint256",
            "22": "totalBalances() low 128 bits; totalLockedMargin() high 128 bits",
            "26": "stakerFeeAccumulator() low 128 bits; devFeeAccumulator() high 128 bits",
        },
        "getter_values": decoded,
        "lpBankrollAvailable_formula": "0 if totalQueued > 0 else max(treasury - totalBalances - totalLockedMargin - stakerFeeAccumulator - devFeeAccumulator, 0)",
        "lpBankrollAvailable_at_pin": queue_available,
        "availability_override_evidence": "exchange_availability_behavior.json",
        "fixture_correction": "treasury() returns an amount; the third-party ABI address output and prior state-address link are contradicted by pinned storage and exact accounting arithmetic",
        "historical_transition_count": len(rows),
        "historical_transitions": rows,
        "limits": [
            "Raw storage and return values prove the six-slot layout at the pin, not the Solidity variable names or types in source.",
            "Pinned storage establishes the base reserve identity; 11 separate storage-override states test the queue gate and saturation branches in exchange_availability_behavior.json.",
            "Transaction deltas are decoded only for saved historical state diffs; they do not establish every write path or update ordering.",
            "A pre or post word omitted by the diff-mode tracer is decoded as zero; this occurs in three saved slot transitions.",
            "Exchange event names are hash-checked against a third-party ABI fixture; some indexed declarations in that fixture are wrong.",
        ],
    }
    output = ATLAS / "exchange_storage_behavior.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}: {len(rows)} historical Exchange accounting transitions")


if __name__ == "__main__":
    main()
