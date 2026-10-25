#!/usr/bin/env python3
"""Verify Exchange position words against saved PositionOpened logs."""

import argparse
import collections
import json
import os
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
CAPTURED = ROOT / "artifacts" / "exchange_positions"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOPIC = "0x88451ea1189f73b554f0bf39c09868560ed149b3d788fcc933ff66ba926827f3"


def rpc(url, method, params):
    request = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                                                     "params": params}).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def position_slot(position_id):
    return int(subprocess.run(["cast", "index", "uint256", str(position_id), "10"],
                              capture_output=True, text=True, check=True).stdout.strip(), 16)


def balance_slot(user):
    return int(subprocess.run(["cast", "index", "address", user, "9"],
                              capture_output=True, text=True, check=True).stdout.strip(), 16)


def source_path(tx, suffix):
    historical = HISTORICAL / f"{tx}.{suffix}.json"
    return historical if historical.exists() else CAPTURED / f"{tx}.{suffix}.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="capture missing historical diffs and receipts")
    args = parser.parse_args()
    pairs = json.loads((ATLAS / "exchange_event_paths.json").read_text())["pairs"]
    opens = [row for row in pairs if row.get("inner_selector") == "0xec6783f0" and row.get("position_id")]
    assert len(opens) == 25
    if args.capture:
        CAPTURED.mkdir(parents=True, exist_ok=True)
        url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
        for tx in sorted({row["tx"] for row in opens}):
            for suffix, method, params in (
                ("state_diff", "debug_traceTransaction", [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}]),
                ("receipt", "eth_getTransactionReceipt", [tx]),
            ):
                if source_path(tx, suffix).exists():
                    continue
                result = rpc(url, method, params)
                (CAPTURED / f"{tx}.{suffix}.json").write_text(json.dumps(result, indent=2) + "\n")
        headers = {}
        for tx in sorted({row["tx"] for row in opens}):
            receipt = json.loads(source_path(tx, "receipt").read_text())
            block_hash = receipt["blockHash"].lower()
            if block_hash not in headers:
                header = rpc(url, "eth_getBlockByHash", [block_hash, False])
                assert header["hash"].lower() == block_hash
                headers[block_hash] = {"number": header["number"], "timestamp": header["timestamp"]}
        (CAPTURED / "block_headers.json").write_text(json.dumps(headers, indent=2) + "\n")
    headers = json.loads((CAPTURED / "block_headers.json").read_text())
    records = []
    for tx in sorted({row["tx"] for row in opens}):
        diff = json.loads(source_path(tx, "state_diff").read_text())
        receipt = json.loads(source_path(tx, "receipt").read_text())
        post = diff["post"].get(EXCHANGE, {}).get("storage", {})
        logs = {int(log["topics"][1], 16): log for log in receipt["logs"]
                if log["address"].lower() == EXCHANGE and log["topics"][0].lower() == TOPIC}
        for row in (row for row in opens if row["tx"] == tx):
            position_id = row["position_id"]
            log = logs[position_id]
            words = [int(log["data"][i:i + 64], 16) for i in range(2, len(log["data"]), 64)]
            assert len(words) == 6
            base = position_slot(position_id)
            first = post.get(f"0x{base:064x}")
            second = post.get(f"0x{base + 1:064x}")
            if first is None or second is None:
                records.append({"tx": tx, "position_id": position_id,
                                "status": "position words absent from transaction post diff"})
                continue
            first, second = int(first, 16), int(second, 16)
            decoded = {
                "user": f"0x{first & ((1 << 160) - 1):040x}",
                "instrument": (first >> 160) & ((1 << 32) - 1),
                "entry_price": first >> 192,
                "margin": second & ((1 << 128) - 1),
                "leverage": (second >> 128) & ((1 << 32) - 1),
                "block_timestamp": (second >> 160) & ((1 << 64) - 1),
                "top_32_flags": second >> 224,
            }
            matches = {
                "user": decoded["user"] == "0x" + log["topics"][2][-40:].lower(),
                "instrument": decoded["instrument"] == words[0],
                "side_bit0": (decoded["top_32_flags"] & 1) == words[1],
                "flag_bit1": ((decoded["top_32_flags"] >> 1) & 1) == words[2],
                "entry_price": decoded["entry_price"] == words[3],
                "margin": decoded["margin"] == words[4],
                "leverage": decoded["leverage"] == words[5],
                "block_timestamp": decoded["block_timestamp"] == int(
                    headers[receipt["blockHash"].lower()]["timestamp"], 16),
            }
            assert all(matches.values()), f"position struct mismatch for {position_id}: {matches}"
            records.append({"tx": tx, "position_id": position_id,
                            "mapping_base_slot": f"0x{base:064x}", "decoded": decoded,
                            "event_fields_match": matches, "status": "matched"})
    matched = [row for row in records if row["status"] == "matched"]
    open_accounting = []
    mask128 = (1 << 128) - 1
    for tx in sorted({row["tx"] for row in opens}):
        diff = json.loads(source_path(tx, "state_diff").read_text())
        receipt = json.loads(source_path(tx, "receipt").read_text())
        before = diff["pre"][EXCHANGE]["storage"]
        after = diff["post"][EXCHANGE]["storage"]
        user_margins = collections.defaultdict(int)
        for log in receipt["logs"]:
            if log["address"].lower() != EXCHANGE or log["topics"][0].lower() != TOPIC:
                continue
            user = "0x" + log["topics"][2][-40:].lower()
            margin = int(log["data"][2 + 4 * 64:2 + 5 * 64], 16)
            user_margins[user] += margin
        balance_checks = []
        for user, margin in sorted(user_margins.items()):
            key = f"0x{balance_slot(user):064x}"
            delta = int(after.get(key, "0x0"), 16) - int(before.get(key, "0x0"), 16)
            assert delta == -margin, f"balance/margin mismatch {tx} {user}"
            balance_checks.append({"user": user, "margin_sum": margin, "balance_delta": delta})
        key = f"0x{22:064x}"
        left, right = int(before[key], 16), int(after[key], 16)
        total_margin = sum(user_margins.values())
        total_balances_delta = (right & mask128) - (left & mask128)
        locked_margin_delta = (right >> 128) - (left >> 128)
        assert total_balances_delta == -total_margin and locked_margin_delta == total_margin
        open_accounting.append({"tx": tx, "open_count": len([row for row in opens if row["tx"] == tx]),
                                "user_balance_checks": balance_checks, "total_margin": total_margin,
                                "total_balances_delta": total_balances_delta,
                                "total_locked_margin_delta": locked_margin_delta})
    paths = json.loads((ATLAS / "exchange_event_paths.json").read_text())
    closed = [(row["tx"], row["position_id"], "signed_close") for row in pairs
              if row.get("inner_selector") == "0x2792e706" and row.get("position_id")]
    liquidations = [(batch["tx"], position_id, "keeper_liquidation")
                    for batch in paths["direct_liquidation_batches"]
                    for position_id in batch["liquidated_position_ids"]]
    deactivations = []
    for tx, position_id, path in closed + liquidations:
        diff = json.loads(source_path(tx, "state_diff").read_text())
        base = position_slot(position_id)
        key = f"0x{base + 1:064x}"
        before = int(diff["pre"][EXCHANGE]["storage"][key], 16)
        after = int(diff["post"][EXCHANGE]["storage"][key], 16)
        assert before - after == 1 << 240, f"unexpected position deactivation {tx} {position_id}"
        deactivations.append({"tx": tx, "position_id": position_id, "path": path,
                              "changed_word": key, "cleared_bit": 240,
                              "all_other_bits_unchanged": True})
    assert len(closed) == 9 and len(liquidations) == 6
    liquidation_accounting = []
    fixture = json.loads((ATLAS / "external_exchange_abi_hypermate.json").read_text())["abi"]
    liquidation_topic = next(item["topic0"].lower() for item in fixture
                             if item["type"] == "event" and item["name"] == "Liquidated")
    for batch in paths["direct_liquidation_batches"]:
        tx = batch["tx"]
        diff = json.loads(source_path(tx, "state_diff").read_text())
        receipt = json.loads(source_path(tx, "receipt").read_text())
        before, after = diff["pre"][EXCHANGE]["storage"], diff["post"][EXCHANGE]["storage"]
        logs = [log for log in receipt["logs"] if log["address"].lower() == EXCHANGE
                and log["topics"][0].lower() == liquidation_topic]
        assert {int(log["topics"][1], 16) for log in logs} == set(batch["liquidated_position_ids"])
        positions = []
        for log in logs:
            position_id = int(log["topics"][1], 16)
            user = "0x" + log["topics"][2][-40:].lower()
            data = [int(log["data"][i:i + 64], 16) for i in range(2, len(log["data"]), 64)]
            assert len(data) == 5
            base = position_slot(position_id)
            margin = int(before[f"0x{base + 1:064x}"], 16) & mask128
            key = f"0x{balance_slot(user):064x}"
            user_balance_delta = int(after.get(key, "0x0"), 16) - int(before.get(key, "0x0"), 16)
            assert user_balance_delta == 0
            assert data[3] * 100 == margin and data[4] * 100 == margin
            positions.append({"position_id": position_id, "user": user, "margin": margin,
                              "user_balance_delta": user_balance_delta,
                              "staker_fee": data[3], "dev_fee": data[4],
                              "price": data[0], "bust_price": data[1], "event_flag": data[2]})
        word22 = f"0x{22:064x}"
        left, right = int(before[word22], 16), int(after[word22], 16)
        assert (right & mask128) - (left & mask128) == 0
        assert (right >> 128) - (left >> 128) == -sum(row["margin"] for row in positions)
        word26 = f"0x{26:064x}"
        left, right = int(before[word26], 16), int(after[word26], 16)
        assert (right & mask128) - (left & mask128) == sum(row["staker_fee"] for row in positions)
        assert (right >> 128) - (left >> 128) == sum(row["dev_fee"] for row in positions)
        liquidation_accounting.append({"tx": tx, "positions": positions,
                                       "total_locked_margin_delta": -sum(row["margin"] for row in positions),
                                       "total_balances_delta": 0})
    result = {
        "pin": 48902346,
        "exchange": EXCHANGE,
        "mapping_base_slot": 10,
        "sampled_open_events": len(opens),
        "sampled_transactions": len({row["tx"] for row in opens}),
        "post_diff_words_available": len(matched),
        "all_available_words_match_events": True,
        "top_32_flags_observed": dict(sorted(collections.Counter(hex(row["decoded"]["top_32_flags"])
                                                       for row in matched).items())),
        "records": records,
        "open_accounting": open_accounting,
        "open_balance_pairs_checked": sum(len(row["user_balance_checks"]) for row in open_accounting),
        "all_open_margin_transfers_match": True,
        "signed_close_deactivations": len(closed),
        "keeper_liquidation_deactivations": len(liquidations),
        "deactivations": deactivations,
        "liquidation_accounting": liquidation_accounting,
        "limits": [
            "Open fields and the close/liquidation active-bit transition are covered only for saved successful paths, not every branch.",
            "The upper 32 bits of the second word contain side, the active bit, and other flags; unobserved bits need independent branch evidence.",
            "The 64-bit field next to leverage equals each sampled transaction block timestamp; other possible semantic uses remain unknown.",
        ],
    }
    output = ATLAS / "exchange_position_layout.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}: {len(matched)}/{len(opens)} open positions matched")


if __name__ == "__main__":
    main()
