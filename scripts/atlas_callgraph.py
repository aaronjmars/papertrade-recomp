#!/usr/bin/env python3
"""Aggregate observed call edges from saved historical transaction traces."""

import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
TRACES = ROOT / "artifacts" / "historical"
TRACE_DIRS = (TRACES, ROOT / "artifacts" / "session_keys", ROOT / "artifacts" / "exchange_sweeps",
              ROOT / "artifacts" / "factory_creation", ROOT / "artifacts" / "oracle_creation",
              ROOT / "artifacts" / "tokenomics", ROOT / "artifacts" / "exchange_core_withdrawal",
              ROOT / "artifacts" / "exchange_getters",
              ROOT / "artifacts" / "exchange_batch_thresholds", ROOT / "artifacts" / "staking",
              ROOT / "artifacts" / "paper_token", ROOT / "artifacts" / "session_creation")
manifest = json.loads((ATLAS / "manifest.json").read_text())
family = json.loads((ATLAS / "deposit_proxy_instances.json").read_text())
roles = {a: c["role"] for a, c in manifest["contracts"].items()}
roles.update({r["address"]: "user_deposit_proxy" for r in family["instances"]})


def role(address):
    if not address:
        return "contract_creation"
    address = address.lower()
    if address in roles:
        return roles[address]
    if address == "0x3333333333333333333333333333333333333333":
        return "hypercore_write_system_contract"
    if int(address, 16) in range(1, 10):
        return "evm_precompile"
    if address.startswith("0x00000000000000000000000000000000000008"):
        return "hypercore_read_precompile"
    if address == "0x6b9e773128f453f5c2c60935ee2de2cbc5390a24":
        return "external_reward_token_bridge"
    return "external_or_unclassified"


def flatten(call):
    kind = call.get("type")
    prefix = call.get("input", "")[:10]
    creation = kind in ("CREATE", "CREATE2")
    yield {"from": call.get("from"), "to": call.get("to"), "type": kind,
           "selector": None if creation else prefix,
           "initcode_prefix": prefix if creation else None}
    for child in call.get("calls", []):
        yield from flatten(child)


saved = {}
for directory in TRACE_DIRS:
    for path in sorted(directory.glob("*.calls.json")):
        stem = path.name.removesuffix(".calls.json")
        receipt = directory / f"{stem}.receipt.json"
        if receipt.exists():
            receipt_data = json.loads(receipt.read_text())
            tx = receipt_data["transactionHash"].lower()
            assert len(tx) == 66 and tx.startswith("0x")
            if stem.startswith("0x"):
                assert stem.lower() == tx, (path, tx)
            if tx not in saved:
                saved[tx] = (path, receipt)
edges = collections.defaultdict(lambda: {"count": 0, "trace_hashes": set(),
                                        "selectors": collections.Counter(), "initcode_prefixes": collections.Counter()})
traces = []
for tx, (call_path, receipt_path) in sorted(saved.items()):
    root = json.loads(call_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    calls = list(flatten(root))
    if not calls:
        continue
    assert receipt["transactionHash"].lower() == tx
    assert int(receipt["blockNumber"], 16) <= manifest["block"]
    if calls[0]["type"] in ("CREATE", "CREATE2") and receipt.get("contractAddress"):
        assert receipt["contractAddress"].lower() == calls[0]["to"].lower()
    traces.append({"hash": tx, "block": int(receipt["blockNumber"], 16),
                   "root_role": role(calls[0]["to"]), "root_call_type": calls[0]["type"],
                   "root_from_role": role(calls[0]["from"]),
                   "root_selector": calls[0]["selector"],
                   "root_initcode_prefix": calls[0]["initcode_prefix"],
                   "status": int(receipt["status"], 16), "call_count": len(calls),
                   "source_directory": call_path.parent.name,
                   "source_stem": call_path.name.removesuffix(".calls.json")})
    for call in calls[1:]:
        key = (role(call["from"]), role(call["to"]), call["type"])
        row = edges[key]
        row["count"] += 1
        row["trace_hashes"].add(tx)
        if call["selector"] is not None:
            row["selectors"][call["selector"]] += 1
        if call["initcode_prefix"] is not None:
            row["initcode_prefixes"][call["initcode_prefix"]] += 1

result = {"basis": "all paired saved debug_traceTransaction callTracer and receipt artifacts through pin",
          "selector_rule": "CREATE and CREATE2 input is initcode, so its first four bytes are recorded as initcode_prefix, not selector",
          "traces": traces,
          "edges": [{"from_role": a, "to_role": b, "call_type": typ, "call_count": data["count"],
                     "trace_hashes": sorted(data["trace_hashes"]), "selectors": dict(data["selectors"]),
                     "initcode_prefixes": dict(data["initcode_prefixes"])}
                    for (a, b, typ), data in sorted(edges.items())]}
(ATLAS / "observed_call_graph.json").write_text(json.dumps(result, indent=2) + "\n")
print(len(traces), "traces", len(edges), "distinct edges")
