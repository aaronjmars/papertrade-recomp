#!/usr/bin/env python3
"""Capture Papertrade runtime bytecode and proxy slots from HyperEVM.

The official public RPC exposes state at latest only. The snapshot records its
start/end blocks, so callers can see the small interval covered by the reads.
"""

import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import urllib.request

RPC = "https://rpc.hyperliquid.xyz/evm"
ROOT = pathlib.Path(__file__).resolve().parents[1]
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
PROXIES = {
    "exchange": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
    "tokenomics": "0x75174549dbbd44497d31a47e2e2d7406408d63d9",
    "oracle": "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e",
    "staking": "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016",
    "batch_executor": "0x233ff29b239abc1d7748605da9b205c3e008626e",
}
OTHERS = {
    "timelock": "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f",
    "governor": "0x696292762fd5ac3677a45edbe54eaece4194d1f6",
    "paper_math_library": "0xe991817199363046da0a28da6fbad0284e4aa492",
}


def rpc(method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(RPC, data=payload, headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def address_from_slot(word):
    return "0x" + word[-40:]


def save_code(folder, label, address):
    code = rpc("eth_getCode", [address, "latest"])
    if not code.startswith("0x") or len(code) <= 2:
        raise ValueError(f"{label}: missing runtime bytecode")
    raw = bytes.fromhex(code[2:])
    (folder / f"{label}.hex").write_text(code + "\n")
    keccak = subprocess.check_output(["cast", "keccak", code], text=True).strip()
    return {
        "address": address,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "keccak256": keccak,
        "file": f"{label}.hex",
    }


def main():
    started = dt.datetime.now(dt.timezone.utc)
    start_block = int(rpc("eth_blockNumber", []), 16)
    chain_id = int(rpc("eth_chainId", []), 16)
    if chain_id != 999:
        raise ValueError(f"wrong chain: {chain_id}")
    folder = ROOT / "artifacts" / f"{started:%Y%m%dT%H%M%SZ}_block{start_block}"
    folder.mkdir(parents=True, exist_ok=False)

    contracts = {}
    for label, address in PROXIES.items():
        implementation_word = rpc("eth_getStorageAt", [address, IMPLEMENTATION_SLOT, "latest"])
        implementation = address_from_slot(implementation_word)
        if int(implementation, 16) == 0:
            raise ValueError(f"{label}: zero implementation slot")
        contracts[label] = {
            "proxy": save_code(folder, f"{label}_proxy", address),
            "implementation_slot": implementation_word,
            "implementation": save_code(folder, f"{label}_implementation", implementation),
        }
    for label, address in OTHERS.items():
        contracts[label] = save_code(folder, label, address)

    end_block = int(rpc("eth_blockNumber", []), 16)
    block = rpc("eth_getBlockByNumber", [hex(end_block), False])
    snapshot = {
        "rpc": RPC,
        "chain_id": chain_id,
        "started_utc": started.isoformat(),
        "ended_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "start_block": start_block,
        "end_block": end_block,
        "end_block_hash": block["hash"],
        "note": "Official RPC provides latest-state eth_getCode and eth_getStorageAt only; calls span the recorded block interval.",
        "contracts": contracts,
    }
    (folder / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    print(folder)
    print(json.dumps({label: value.get("implementation", value)["keccak256"] for label, value in contracts.items()}, indent=2))


if __name__ == "__main__":
    main()
