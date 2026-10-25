#!/usr/bin/env python3
"""Extract compiler and IPFS pointers from pinned Solidity metadata trailers."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58(value):
    number = int.from_bytes(value, "big")
    result = ""
    while number:
        number, digit = divmod(number, 58)
        result = alphabet[digit] + result
    return "1" * (len(value) - len(value.lstrip(b"\x00"))) + result


out = {}
for address, contract in manifest["contracts"].items():
    code = bytes.fromhex((ATLAS / contract["runtime_file"]).read_text().strip()[2:])
    size = int.from_bytes(code[-2:], "big")
    if size > len(code) - 2:
        out[address] = {"role": contract["role"], "metadata_present": False}
        continue
    metadata = code[-size-2:-2]
    row = {"role": contract["role"], "metadata_present": True, "metadata_bytes": size}
    marker = metadata.find(b"ipfs\x58\x22")
    if marker >= 0 and metadata[marker + 6:marker + 8] == b"\x12\x20":
        row["ipfs_cid_v0"] = base58(metadata[marker + 6:marker + 40])
    marker = metadata.find(b"solc\x43")
    if marker >= 0:
        version = metadata[marker + 5:marker + 8]
        row["solc_version"] = ".".join(map(str, version))
    out[address] = row
(ATLAS / "compiler_metadata.json").write_text(json.dumps(out, indent=2) + "\n")
print(len(out), "contracts", sum("ipfs_cid_v0" in x for x in out.values()), "IPFS pointers")
