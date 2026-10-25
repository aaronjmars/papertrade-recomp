#!/usr/bin/env python3
"""Extract confirmed address links from pinned getter traces."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
traces = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
names = ("owner", "signer", "manager", "keeper", "guardian", "token", "exchange", "oracle", "treasury", "factory", "minter", "deployer", "caller", "executor", "staking", "session")
# The Exchange treasury getter is an accounting amount; it only looks like an address because it fits in 160 bits.
non_address_getters = {("exchange_implementation", "treasury()")}
external_roles = {
    "0x6b9e773128f453f5c2c60935ee2de2cbc5390a24": "external_contract",
    "0x3721476de31190dc1af8908026abe20efe25cf99": "eoa_or_native_account",
    "0xe9686c8e11d80c8d78736485fcb6b6d7f4d7692e": "eoa_or_native_account",
    "0xaa7577a7a27aa7fcf6d0ec481b87df3ad0f6a88e": "eoa_or_native_account",
    "0xdf1bda875c9393a663ce69bf6a7fbaa73dfd053d": "eoa_or_native_account",
}
links = []
for address, contract in traces.items():
    for view in contract["views"]:
        signature = view["candidate_signature"].split("|")[0]
        output = view.get("return_prefix", "")
        if view["arguments"] or view.get("failed") or len(output) != 66 or not any(name in signature.lower() for name in names):
            continue
        if (contract["role"], signature) in non_address_getters:
            continue
        if int(output[2:26], 16):
            continue
        target = "0x" + output[-40:].lower()
        if int(target, 16) == 0:
            continue
        links.append({"from": view["target"], "from_role": contract["role"], "getter": signature,
                      "selector": view["selector"], "to": target,
                      "to_role": manifest["contracts"].get(target, {}).get("role", external_roles.get(target, "external_or_eoa")),
                      "storage_slots_read": view.get("direct_slots", []), "pin": 48902346})
        if target in external_roles:
            links[-1]["target_runtime_bytes"] = 2175 if external_roles[target] == "external_contract" else 0
(ATLAS / "state_links.json").write_text(json.dumps(links, indent=2) + "\n")
print(len(links), "address links")
