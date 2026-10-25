#!/usr/bin/env python3
"""Capture all factory CREATE2 deployment addresses through the pinned block."""

import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
FACTORY = "0x1629b7d46bef6e13ff754174fc9f32dea309b38f"
PIN = 48902346
CACHED = {
    1: ROOT / "artifacts" / "factory_internal_txlist.json",
    2: ATLAS / "factory_creations_page2.json",
    10: ATLAS / "factory_creations_page10.json",
    20: ATLAS / "factory_creations_page20.json",
    22: ATLAS / "factory_creations_page22.json",
    23: ATLAS / "factory_creations_page23.json",
}
instances = []
for page in range(1, 24):
    if page in CACHED:
        rows = json.loads(CACHED[page].read_text())
    else:
        command = ["etherscan", "account", "txlistinternal", "--address", FACTORY,
                   "--chain", "999", "--startblock", "47855071", "--endblock", str(PIN),
                   "--sort", "asc", "--page", str(page), "--offset", "1000"]
        run = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
        rows = json.loads(run.stdout)
        time.sleep(0.3)
    expected = 586 if page == 23 else 1000
    if len(rows) != expected:
        raise RuntimeError(f"page {page}: expected {expected}, got {len(rows)}")
    for row in rows:
        if row.get("type") != "create2" or row.get("isError") != "0" or not row.get("contractAddress"):
            raise RuntimeError(f"non-successful CREATE2 row on page {page}")
        instances.append({"address": row["contractAddress"].lower(), "block": int(row["blockNumber"]), "tx": row["hash"]})
    print(page, len(rows), flush=True)
if len({x["address"] for x in instances}) != len(instances):
    raise RuntimeError("duplicate deployed address")
if instances[-1]["block"] > PIN:
    raise RuntimeError("out-of-range factory creation")
result = {"chain_id": 999, "through_block": PIN, "factory": FACTORY,
          "source": "Etherscan v2 txlistinternal for factory, pages 1-23, ascending, 1000 per page",
          "count": len(instances), "instances": instances}
(ATLAS / "deposit_proxy_instances.json").write_text(json.dumps(result, indent=2) + "\n")
print("total", len(instances))
