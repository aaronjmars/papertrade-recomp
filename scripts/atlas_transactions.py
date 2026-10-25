#!/usr/bin/env python3
"""Sample first and last direct transactions for each named Papertrade entrypoint."""

import collections
import json
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
manifest = json.loads((ATLAS / "manifest.json").read_text())
targets = {address: row for address, row in manifest["contracts"].items()
           if row["role"].endswith("_proxy") or row["role"] in ("proxy_admin", "one_of_two_multisig", "timelock")}
results = {}
for address, contract in targets.items():
    txs = {}
    pages = []
    for order in ("asc", "desc"):
        command = ["etherscan", "account", "txlist", address, "--chain", "999",
                   "--startblock", str(contract["origin"].get("block", 47854475)),
                   "--endblock", "48902346", "--sort", order, "--page", "1", "--offset", "1000"]
        run = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
        rows = json.loads(run.stdout)
        pages.append({"order": order, "count": len(rows), "first_block": int(rows[0]["blockNumber"]) if rows else None,
                      "last_block": int(rows[-1]["blockNumber"]) if rows else None})
        for tx in rows:
            if tx.get("to", "").lower() == address and tx.get("input", "0x") != "0x":
                txs[tx["hash"]] = {"hash": tx["hash"], "block": int(tx["blockNumber"]),
                                   "selector": tx["input"][:10], "status": 0 if tx.get("isError") == "1" else 1}
        time.sleep(0.2)
    grouped = collections.defaultdict(list)
    for tx in sorted(txs.values(), key=lambda x: (x["block"], x["hash"])):
        grouped[tx["selector"]].append(tx)
    results[address] = {"role": contract["role"], "pages": pages, "sampled_unique_transactions": len(txs),
                        "selectors": {selector: {"sample_count": len(rows), "first": rows[0], "last": rows[-1]}
                                      for selector, rows in sorted(grouped.items())}}
    print(contract["role"], len(txs), len(grouped), flush=True)
(ATLAS / "direct_transaction_samples.json").write_text(json.dumps(results, indent=2) + "\n")
