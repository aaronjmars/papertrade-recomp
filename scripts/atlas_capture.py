#!/usr/bin/env python3
"""Pin Papertrade runtime code and proxy relationships to one HyperEVM block.

Requires PAPERTRADE_ARCHIVE_RPC. Reads the local deployer transaction list created
with etherscan account txlist, then follows EIP-1967 implementation/admin slots.
The RPC URL is never written to artifacts.
"""

import hashlib
import json
import pathlib
import subprocess
import sys

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
PIN = 48902346
OUT = ROOT / "atlas" / f"block_{PIN}"
DEPLOYER_TXLIST = ROOT / "artifacts" / "deployer_txlist.json"
FIRST_PRODUCTION_DEPLOYMENT = 47854475
SLOTS = {
    "implementation": "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
    "admin": "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103",
    "beacon": "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50",
}
ROLES = {
    "0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388": "exchange_linked_library_variant_a",
    "0xcd617f984158a4f5d287ddee0e8eb0fed204916d": "exchange_linked_library_live",
    "0x1629b7d46bef6e13ff754174fc9f32dea309b38f": "deposit_proxy_factory_proxy",
    "0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0": "deposit_proxy_factory_implementation",
    "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb": "exchange_implementation_variant_a",
    "0x4f859b790d34767ea325b4888c8c420c34cf85af": "exchange_implementation_variant_b",
    "0xe79c91cc682f1bb401a9cab74c900470190f0f8f": "proxy_admin",
    "0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a": "oracle_implementation",
    "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e": "oracle_proxy",
    "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee": "exchange_implementation",
    "0x6cd5661646289fb6e65ea5c032310fded797d0a2": "exchange_proxy",
    "0x8a5069fe303e8f81e91825436e956d595032e558": "session_key_manager_implementation",
    "0x8326eb8896e358717f10502ec73ce8d28e37b108": "session_key_manager_proxy",
    "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f": "tokenomics_implementation",
    "0x75174549dbbd44497d31a47e2e2d7406408d63d9": "tokenomics_proxy",
    "0x433bd418ec92818a960585f4d5fae563e735bb4a": "paper_token_implementation",
    "0xe40f17915daa230324030003a197cdaef2261c0e": "paper_token_proxy",
    "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15": "staking_implementation",
    "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016": "staking_proxy",
    "0xe0bc9cc7b067060aafccbaa3e250700c9cdd7262": "batch_executor_implementation",
    "0x233ff29b239abc1d7748605da9b205c3e008626e": "batch_executor_proxy",
    "0x696292762fd5ac3677a45edbe54eaece4194d1f6": "one_of_two_multisig",
    "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f": "timelock",
    "0xe991817199363046da0a28da6fbad0284e4aa492": "paper_math_library",
}


def slot_address(word):
    return "0x" + word[-40:].lower()


def is_nonzero(address):
    return int(address, 16) != 0


def code_entry(address, origin):
    code = rpc("eth_getCode", [address, hex(PIN)])
    if code == "0x":
        return {"address": address, "role": ROLES.get(address, "unclassified"), "origin": origin, "code_present": False}
    data = bytes.fromhex(code[2:])
    filename = f"{address}.hex"
    (OUT / "runtime" / filename).write_text(code + "\n")
    entry = {
        "address": address,
        "role": ROLES.get(address, "unclassified"),
        "origin": origin,
        "code_present": True,
        "runtime_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "keccak256": subprocess.check_output(["cast", "keccak", code], text=True).strip(),
        "runtime_file": f"runtime/{filename}",
    }
    slots = {name: rpc("eth_getStorageAt", [address, slot, hex(PIN)]) for name, slot in SLOTS.items()}
    entry["eip1967_slots"] = slots
    return entry


def main():
    if int(rpc("eth_chainId", []), 16) != 999:
        raise ValueError("wrong chain")
    block = rpc("eth_getBlockByNumber", [hex(PIN), False])
    if not block or int(block["number"], 16) != PIN:
        raise ValueError("pinned block missing")
    txs = json.loads(DEPLOYER_TXLIST.read_text())
    seeds = {}
    for tx in txs:
        if tx.get("contractAddress") and int(tx["blockNumber"]) >= FIRST_PRODUCTION_DEPLOYMENT and int(tx["blockNumber"]) <= PIN:
            seeds[tx["contractAddress"].lower()] = {"kind": "deployer_creation", "block": int(tx["blockNumber"]), "tx": tx["hash"]}
    seeds["0xe991817199363046da0a28da6fbad0284e4aa492"] = {"kind": "linked_library_from_tokenomics_trace"}
    seeds["0xcd617f984158a4f5d287ddee0e8eb0fed204916d"] = {"kind": "push20_linked_library", "from": "exchange_implementation"}
    seeds["0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388"] = {"kind": "push20_linked_library", "from": "exchange_implementation_variant_a"}
    for address in ROLES:
        seeds.setdefault(address, {"kind": "known_papertrade_reference"})
    (OUT / "runtime").mkdir(parents=True, exist_ok=True)
    contracts = {}
    todo = sorted(seeds)
    while todo:
        address = todo.pop(0)
        if address in contracts:
            continue
        entry = code_entry(address, seeds[address])
        contracts[address] = entry
        if entry["code_present"]:
            for name in ("implementation", "admin", "beacon"):
                target = slot_address(entry["eip1967_slots"][name])
                if is_nonzero(target) and target not in contracts and target not in todo:
                    seeds.setdefault(target, {"kind": "eip1967_" + name, "from": address})
                    todo.append(target)
        print(entry["role"], address, entry.get("runtime_bytes", 0), flush=True)
    family_path = OUT / "deposit_proxy_family.json"
    family = json.loads(family_path.read_text()) if family_path.exists() else None
    if family:
        representative = family["records"][0]["address"]
        if representative not in contracts:
            entry = code_entry(representative, {"kind": "factory_create2_representative", "family_file": "deposit_proxy_family.json"})
            entry["role"] = "user_deposit_proxy_representative"
            contracts[representative] = entry
            print(entry["role"], representative, entry["runtime_bytes"], flush=True)
    end_hash = rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"]
    if end_hash != block["hash"]:
        raise RuntimeError("pinned block hash changed during capture")
    manifest = {
        "chain_id": 999,
        "block": PIN,
        "block_hash": block["hash"],
        "timestamp": int(block["timestamp"], 16),
        "sources": ["deployer_txlist.json", "Exchange getter reads", "Tokenomics trace", "EIP-1967 proxy slots", "Exchange implementation PUSH20 references", "deposit_proxy_instances.json"],
        "scope_note": "Newest deployer-created suite, its EIP-1967 proxy targets, linked libraries, and representative user deposit proxy. The separate deployer_scope capture records 38 earlier direct creations and 38 older factory-created user proxies still carrying code at the pin. External token and HyperCore system contracts are dependencies, not counted as Papertrade deployments.",
        "deposit_proxy_family": {"factory": "0x1629b7d46bef6e13ff754174fc9f32dea309b38f", "instance_count": family["instance_count"], "instance_file": "deposit_proxy_instances.json", "sample_template_file": "deposit_proxy_family.json"} if family else None,
        "contracts": contracts,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(OUT / "manifest.json")


if __name__ == "__main__":
    main()
