#!/usr/bin/env python3
"""Check EIP-1967 proxy upgrade events through the pinned block."""

import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
TOPIC = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
out = {}
for address, contract in manifest["contracts"].items():
    if not contract["role"].endswith("_proxy"):
        continue
    creation = contract["origin"].get("block", 47854475)
    command = ["etherscan", "logs", "get", "--address", address, "--from-block", str(creation),
               "--to-block", "48902346", "--topic0", TOPIC, "--page", "1", "--offset", "1000", "--chain", "999"]
    run = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
    logs = json.loads(run.stdout)
    if len(logs) >= 1000:
        raise RuntimeError(f"upgrade event page full: {address}")
    out[address] = {"role": contract["role"], "creation_block": creation,
                    "pinned_implementation": "0x" + contract["eip1967_slots"]["implementation"][-40:],
                    "upgrade_event_count": len(logs), "events": [{"block": int(x["blockNumber"], 16),
                    "tx": x["transactionHash"], "implementation": "0x" + x["topics"][1][-40:] if len(x["topics"]) > 1 else None} for x in logs]}
    print(contract["role"], len(logs), flush=True)
    time.sleep(0.2)
(ATLAS / "upgrade_history.json").write_text(json.dumps(out, indent=2) + "\n")
