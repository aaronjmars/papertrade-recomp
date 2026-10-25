#!/usr/bin/env python3
"""Capture the small set of historical accounting states used in the assessment."""

import hashlib
import json
import pathlib

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "historical" / "accounting_states.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
SELECTORS = {
    "queue_head": (EXCHANGE, "0x96523644"),
    "total_queued": (EXCHANGE, "0x53ac4b66"),
    "lp_bankroll_available": (EXCHANGE, "0x0cdd5fc4"),
    "queue_harvest_available": (EXCHANGE, "0x138e9de2"),
    "exchange_staker_excess": (EXCHANGE, "0x18715c9a"),
    "tracked_lp": (TOKENOMICS, "0x8cf554a7"),
    "staker_excess": (TOKENOMICS, "0xae745703"),
    "staker_cap": (TOKENOMICS, "0xc16017ca"),
}
BLOCKS = [48170000, 48173880, 48173881, 48173885, 48173887, 48173889, 48173890, 48899300, 48901469, 48902346]


def signed(value):
    return value - (1 << 256) if value >= (1 << 255) else value


def main():
    if int(rpc("eth_chainId", []), 16) != 999:
        raise ValueError("wrong chain")
    rows = []
    for n in BLOCKS:
        block = rpc("eth_getBlockByNumber", [hex(n), False])
        row = {"block": n, "block_hash": block["hash"], "timestamp": int(block["timestamp"], 16)}
        for label, (address, selector) in SELECTORS.items():
            value = int(rpc("eth_call", [{"to": address, "data": selector}, hex(n)]), 16)
            row[label] = str(signed(value) if label == "tracked_lp" else value)
        rows.append(row)
        print(n, row["total_queued"], row["tracked_lp"], row["staker_excess"], flush=True)
    code_checks = {}
    for n in [48170000, 48173881, 48901469]:
        for label, address in [("exchange", EXCHANGE), ("tokenomics", TOKENOMICS)]:
            word = rpc("eth_getStorageAt", [address, IMPLEMENTATION_SLOT, hex(n)])
            implementation = "0x" + word[-40:]
            code = rpc("eth_getCode", [implementation, hex(n)])
            code_checks[f"{label}_{n}"] = {
                "proxy_implementation_slot": word,
                "implementation": implementation,
                "runtime_bytes": (len(code) - 2) // 2,
                "runtime_sha256": hashlib.sha256(bytes.fromhex(code[2:])).hexdigest(),
            }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"chain_id": 999, "selectors": SELECTORS, "states": rows, "historical_implementations": code_checks}, indent=2) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
