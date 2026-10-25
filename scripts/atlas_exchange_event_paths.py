#!/usr/bin/env python3
"""Tie Exchange event topics to the sampled calls that emitted them."""

import collections
import json
import pathlib
import subprocess

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
BATCH = ROOT / "artifacts" / "batch_executor"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
EXCHANGE_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
HYPERCORE_BBO = "0x000000000000000000000000000000000000080e"
BATCH_PROXY = "0x233ff29b239abc1d7748605da9b205c3e008626e"
CALL_EXECUTED = "0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad"
OPENED = "0x88451ea1189f73b554f0bf39c09868560ed149b3d788fcc933ff66ba926827f3"
CLOSED = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
LIQUIDATED = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
OPEN_SELECTOR = "0xec6783f0"
OPEN_SIGNATURE = "openPositionBySig(address,uint32,bool,uint128,uint32,bool,uint256,uint64,uint8,bytes32,bytes32)"


def decoded(signature, data):
    result = subprocess.run(["cast", "decode-calldata", "--json", signature, data],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)["data"]


def saved(hash_, suffix):
    for folder in (BATCH, HISTORICAL):
        path = folder / f"{hash_}.{suffix}.json"
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError(f"{hash_}.{suffix}.json")


def main():
    assert "0x" + Keccak()(OPEN_SIGNATURE.encode()).hex()[:8] == OPEN_SELECTOR
    behavior = json.loads((ATLAS / "batch_executor_behavior.json").read_text())
    recent = json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text())
    recent_by_tx = collections.defaultdict(list)
    for log in recent:
        recent_by_tx[log["transactionHash"]].append(log)
    receipt_count = 0
    paired = []
    for row in behavior["traced_batches"]:
        hash_ = row["tx"]
        trace = saved(hash_, "calls")
        receipt_path = HISTORICAL / f"{hash_}.receipt.json"
        logs = json.loads(receipt_path.read_text())["logs"] if receipt_path.exists() else recent_by_tx[hash_]
        logs = sorted(logs, key=lambda x: int(x["logIndex"], 16))
        children = trace["calls"][0].get("calls", [])
        assert len(children) == len(row["intents"])
        pending = []
        seen_results = set()
        for log in logs:
            if log["address"].lower() == EXCHANGE:
                pending.append(log)
            elif log["address"].lower() == BATCH_PROXY and log["topics"][0] == CALL_EXECUTED:
                index = int(log["topics"][2], 16)
                assert index not in seen_results
                seen_results.add(index)
                child = children[index]
                for item in pending:
                    topic = item["topics"][0]
                    detail = {"tx": hash_, "batch_index": index, "inner_selector": child["input"][:10],
                              "topic0": topic, "position_id": int(item["topics"][1], 16) if len(item["topics"]) > 1 and topic in (OPENED, CLOSED, LIQUIDATED) else None}
                    if topic == OPENED:
                        assert child["input"][:10] == OPEN_SELECTOR
                        assert not child.get("error")
                        assert int(child["output"], 16) == detail["position_id"]
                        args = decoded("f(address,uint32,bool,uint128,uint32,bool,uint256,uint64,uint8,bytes32,bytes32)", child["input"])
                        fields = [int(item["data"][i:i + 64], 16) for i in range(2, len(item["data"]), 64)]
                        assert len(fields) == 6
                        assert int(item["topics"][2], 16) == int(args[0], 16)
                        assert fields[0] == int(args[1]) and fields[1] == int(bool(args[2]))
                        assert fields[2] == int(bool(args[5]))
                        assert fields[4] == int(args[3]) and fields[5] == int(args[4])
                        implementation_calls = [call for call in child.get("calls", [])
                                                if call.get("to", "").lower() == EXCHANGE_IMPLEMENTATION]
                        assert len(implementation_calls) == 1
                        oracle_calls = [call for call in implementation_calls[0].get("calls", [])
                                        if call.get("to", "").lower() == ORACLE and call["input"][:10] == "0xc0182669"]
                        assert len(oracle_calls) == 1
                        oracle_call = oracle_calls[0]
                        assert int(oracle_call["input"][10:], 16) == int(args[1])
                        midpoint = int(oracle_call["output"], 16)
                        precompile_calls = [call for proxy_call in oracle_call.get("calls", [])
                                            for call in proxy_call.get("calls", [])
                                            if call.get("to", "").lower() == HYPERCORE_BBO]
                        assert len(precompile_calls) == 1
                        bbo = bytes.fromhex(precompile_calls[0]["output"][2:])
                        assert len(bbo) == 64
                        bid, ask = int.from_bytes(bbo[:32], "big"), int.from_bytes(bbo[32:], "big")
                        assert bid > 0 and bid <= ask
                        assert midpoint == (bid + ask) // 2 == fields[3]
                        detail["hypercore_bid"] = bid
                        detail["hypercore_ask"] = ask
                        detail["oracle_midpoint"] = midpoint
                        detail["entry_price_matches_hypercore_midpoint"] = True
                        detail["position_id_matches_return_value"] = True
                        detail["user_instrument_side_flag_margin_leverage_match_input"] = True
                    elif topic == CLOSED:
                        assert child["input"][:10] == "0x2792e706"
                        args = decoded("f(address,uint256[],uint256,uint64,uint8,bytes32,bytes32)", child["input"])
                        ids = {int(x) for x in args[1]}
                        assert detail["position_id"] in ids
                        assert int(item["topics"][2], 16) == int(args[0], 16)
                        detail["position_id_in_signed_close_array"] = True
                        detail["user_matches_signed_input"] = True
                    paired.append(detail)
                pending = []
        assert not pending and len(seen_results) == len(children)
        receipt_count += 1

    direct_liquidations = []
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    for row in graph["traces"]:
        if row["root_role"] != "exchange_proxy" or row["root_selector"] != "0x599dc539":
            continue
        hash_ = row["hash"]
        trace = saved(hash_, "calls")
        receipt = saved(hash_, "receipt")
        ids = {int(x) for x in decoded("liquidateBatch(uint256[])", trace["input"])[0]}
        logs = [x for x in receipt["logs"] if x["address"].lower() == EXCHANGE and x["topics"][0] == LIQUIDATED]
        emitted = {int(x["topics"][1], 16) for x in logs}
        assert emitted and emitted <= ids
        direct_liquidations.append({"tx": hash_, "requested_position_ids": sorted(ids),
                                    "liquidated_position_ids": sorted(emitted)})

    counts = collections.Counter((x["inner_selector"], x["topic0"]) for x in paired)
    result = {
        "pin": 48902346,
        "address": EXCHANGE,
        "implementation": EXCHANGE_IMPLEMENTATION,
        "method": "saved BatchExecutor call traces paired with ordered receipt logs; direct liquidation calldata compared with emitted position IDs",
        "batch_transactions_checked": receipt_count,
        "paired_exchange_events": len(paired),
        "selector_event_pairs": [{"selector": selector, "topic0": topic, "count": count}
                                 for (selector, topic), count in sorted(counts.items())],
        "position_opened_matches_return_id": sum(x.get("position_id_matches_return_value", False) for x in paired),
        "position_opened_matches_signed_fields": sum(x.get("user_instrument_side_flag_margin_leverage_match_input", False) for x in paired),
        "position_opened_matches_hypercore_midpoint": sum(x.get("entry_price_matches_hypercore_midpoint", False) for x in paired),
        "selector_reconstructions": {OPEN_SELECTOR: OPEN_SIGNATURE},
        "position_closed_matches_signed_id_array": sum(x.get("position_id_in_signed_close_array", False) for x in paired),
        "direct_liquidation_batches": direct_liquidations,
        "pairs": paired,
        "limits": [
            "Pairing relies on the observed event order in sampled batches; it does not cover every historical batch.",
            "The exact entry-price equality is established for 25 sampled successful opens; failed opens and alternate pricing modes are untested.",
            "Exact event signatures are recorded separately in exchange_interface_evidence.json.",
            "Liquidation compares requested and emitted IDs in two saved direct transactions only.",
        ],
    }
    output = ATLAS / "exchange_event_paths.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}: {len(paired)} paired Exchange events, {len(direct_liquidations)} liquidation samples")


if __name__ == "__main__":
    main()
