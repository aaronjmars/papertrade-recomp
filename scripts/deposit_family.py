#!/usr/bin/env python3
"""Sample user deposit proxy runtimes at the same pinned block."""

import hashlib
import json
import pathlib

from trace import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "atlas" / "block_48902346"
PIN = 48902346
early = json.loads((ROOT / "artifacts" / "factory_internal_txlist.json").read_text())
recent = json.loads((OUT / "factory_recent_creations.json").read_text())
all_instances = json.loads((OUT / "deposit_proxy_instances.json").read_text())["instances"]
sample_addresses = {x["contractAddress"].lower() for x in early[:5] + recent[:5]}
sample_addresses.update(all_instances[(i * (len(all_instances) - 1)) // 32]["address"] for i in range(33))
samples = [x for x in all_instances if x["address"] in sample_addresses]
records = []
codes = []
for tx in samples:
    address = tx["address"].lower()
    code = bytes.fromhex(rpc("eth_getCode", [address, hex(PIN)])[2:])
    codes.append(code)
    records.append({"address": address, "create2_block": tx["block"], "create2_tx": tx["tx"], "runtime_bytes": len(code), "sha256": hashlib.sha256(code).hexdigest()})
if not codes or len(set(map(len, codes))) != 1:
    raise RuntimeError("sample family has missing or unequal runtime length")

varying = [i for i in range(len(codes[0])) if len({code[i] for code in codes}) > 1]
ranges = []
for i in varying:
    if not ranges or i > ranges[-1][-1] + 1:
        ranges.append([i])
    else:
        ranges[-1].append(i)
for record, code in zip(records, codes):
    record["varying_bytes"] = {f"{r[0]}:{r[-1] + 1}": code[r[0]:r[-1] + 1].hex() for r in ranges}
    normalized = bytearray(code)
    for run in ranges:
        normalized[run[0]:run[-1] + 1] = bytes(len(run))
    record["normalized_sha256"] = hashlib.sha256(normalized).hexdigest()
    if len(set(record["varying_bytes"].values())) != 1:
        raise RuntimeError(f"embedded per-user values differ: {record['address']}")
if len({x["normalized_sha256"] for x in records}) != 1:
    raise RuntimeError("deposit proxy template mismatch")

representative = OUT / "runtime" / f"{records[0]['address']}.hex"
representative.write_text("0x" + codes[0].hex() + "\n")
result = {"pin": PIN, "instance_count": len(all_instances), "sample_count": len(records), "sample_runtime_bytes": len(codes[0]), "varying_byte_ranges": [[r[0], r[-1] + 1] for r in ranges], "normalized_sha256": records[0]["normalized_sha256"], "records": records, "representative_runtime_file": str(representative.relative_to(OUT))}
(OUT / "deposit_proxy_family.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ("sample_count", "sample_runtime_bytes", "varying_byte_ranges")}, indent=2))
