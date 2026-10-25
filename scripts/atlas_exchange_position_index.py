#!/usr/bin/env python3
"""Verify Exchange's one-based open-position array index mapping."""

import argparse
import collections
import json
import os
from pathlib import Path

from atlas_factory_events import Keccak


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts"
SAVED = ARTIFACTS / "exchange_position_index" / "historical_getters.json"
OUT = ATLAS / "exchange_position_index_behavior.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SELECTOR = "0xf728fc98"
CLOSE_TOPIC = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
LIQUIDATION_TOPIC = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"
SAMPLE_IDS = (1392998, 1392999, 1393000)
MODULUS = 1 << 256
KECCAK = Keccak()


def slot(key, base):
    return "0x" + KECCAK(key.to_bytes(32, "big") + base.to_bytes(32, "big")).hex()


def state_diff(tx):
    paths = sorted(ARTIFACTS.glob(f"**/{tx}.state_diff.json"))
    assert paths, tx
    results = [(path, json.loads(path.read_text())) for path in paths]
    assert all(result == results[0][1] for _, result in results)
    return results[0]


def capture():
    from atlas_session_keys import rpc

    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    pin_header = rpc(url, "eth_getBlockByNumber", [hex(manifest["block"]), False])
    assert pin_header["hash"].lower() == manifest["block_hash"]
    positions = json.loads((ATLAS / "exchange_position_layout.json").read_text())
    by_id = {row["position_id"]: row for row in positions["records"]}
    rows = []
    for position_id in SAMPLE_IDS:
        tx = by_id[position_id]["tx"]
        receipts = list(ARTIFACTS.glob(f"**/{tx}.receipt.json"))
        assert receipts
        receipt = json.loads(receipts[0].read_text())
        block = receipt["blockNumber"]
        header = rpc(url, "eth_getBlockByNumber", [block, False])
        assert header["hash"].lower() == receipt["blockHash"].lower()
        key = slot(position_id, 13)
        calldata = SELECTOR + f"{position_id:064x}"
        raw = rpc(url, "eth_getStorageAt", [EXCHANGE, key, block])
        result = rpc(url, "eth_call", [{"to": EXCHANGE, "data": calldata}, block])
        rows.append({"position_id": position_id, "opening_tx": tx,
                     "block": int(block, 16), "block_hash": header["hash"],
                     "mapping_slot": key, "raw_storage": raw, "getter_output": result})
    SAVED.parent.mkdir(parents=True, exist_ok=True)
    SAVED.write_text(json.dumps({"pin": manifest["block"],
                                 "pin_hash": manifest["block_hash"], "rows": rows}, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    positions = json.loads((ATLAS / "exchange_position_layout.json").read_text())
    storage = json.loads((ATLAS / "storage_trace_catalog.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert manifest["block"] == positions["pin"] == saved["pin"] == 48902346
    assert manifest["block_hash"] == saved["pin_hash"]
    assert positions["exchange"] == EXCHANGE
    view = next(row for row in storage[IMPLEMENTATION]["views"] if row["selector"] == SELECTOR)
    assert view["target"] == EXCHANGE and view["sample_argument"] == 1 and not view["failed"]
    assert view["return_prefix"] == "0x" + "0" * 64
    assert view["mapping_matches"] == [{"base_slot": 13, "field_offset": 0,
                                         "read_slot": slot(1, 13), "pc": 1408}]
    opens = []
    open_by_id = {}
    for position in positions["records"]:
        tx = position["tx"]
        position_id = int(position["position_id"])
        user = int(position["decoded"]["user"], 16)
        path, diff = state_diff(tx)
        before = diff["pre"].get(EXCHANGE, {}).get("storage", {})
        after = diff["post"][EXCHANGE]["storage"]
        index_slot = slot(position_id, 13)
        assert index_slot not in before and index_slot in after
        one_based_index = int(after[index_slot], 16)
        assert one_based_index > 0
        array_root = int(slot(user, 12), 16)
        array_start = int.from_bytes(KECCAK(array_root.to_bytes(32, "big")), "big")
        element_slot = "0x" + ((array_start + one_based_index - 1) % MODULUS).to_bytes(32, "big").hex()
        assert int(after[element_slot], 16) == position_id
        length_slot = f"0x{array_root:064x}"
        assert one_based_index <= int(after[length_slot], 16)
        row = {"tx": tx, "position_id": position_id,
               "user": f"0x{user:040x}", "one_based_index": one_based_index,
               "mapping_slot": index_slot, "array_element_slot": element_slot,
               "state_diff": str(path.relative_to(ROOT))}
        opens.append(row)
        open_by_id[position_id] = row
    assert len(opens) == len(open_by_id) == 25
    removals = []
    groups = collections.defaultdict(list)
    for position in positions["deactivations"]:
        tx = position["tx"]
        position_id = int(position["position_id"])
        path, diff = state_diff(tx)
        before = diff["pre"][EXCHANGE]["storage"]
        after = diff["post"].get(EXCHANGE, {}).get("storage", {})
        key = slot(position_id, 13)
        assert int(before[key], 16) > 0 and key not in after
        receipts = list(ARTIFACTS.glob(f"**/{tx}.receipt.json"))
        assert receipts
        receipt = json.loads(receipts[0].read_text())
        topic = CLOSE_TOPIC if position["path"] == "signed_close" else LIQUIDATION_TOPIC
        matched = [(index, log) for index, log in enumerate(receipt["logs"])
                   if log["address"].lower() == EXCHANGE and log["topics"][0] == topic
                   and int(log["topics"][1], 16) == position_id]
        assert len(matched) == 1 and len(matched[0][1]["topics"]) == 3
        user = int(matched[0][1]["topics"][2], 16)
        row = {"tx": tx, "position_id": position_id,
               "path": position["path"], "old_one_based_index": int(before[key], 16),
               "user": f"0x{user:040x}", "receipt_log_index": matched[0][0],
               "state_diff": str(path.relative_to(ROOT))}
        removals.append(row)
        groups[(tx, user)].append(row)
    assert len(removals) == 15
    assert {row["path"] for row in removals} == {"signed_close", "keeper_liquidation"}
    array_checks = []
    for (tx, user), group in sorted(groups.items()):
        _, diff = state_diff(tx)
        before = diff["pre"][EXCHANGE]["storage"]
        after = diff["post"].get(EXCHANGE, {}).get("storage", {})
        array_root = int(slot(user, 12), 16)
        root_key = f"0x{array_root:064x}"
        array_start = int.from_bytes(KECCAK(array_root.to_bytes(32, "big")), "big")
        element = lambda index: f"0x{(array_start + index) % MODULUS:064x}"
        old_length = int(before[root_key], 16)
        new_length = int(after.get(root_key, "0x0"), 16)
        assert old_length - new_length == len(group)
        ordered = sorted(group, key=lambda row: row["receipt_log_index"])
        if len(group) == 1:
            removed = ordered[0]
            index = removed["old_one_based_index"] - 1
            last = int(before[element(old_length - 1)], 16)
            assert int(before[element(index)], 16) == removed["position_id"]
            assert element(old_length - 1) not in after
            if index == old_length - 1:
                assert last == removed["position_id"]
                operation = "tail_pop"
            else:
                assert int(after[element(index)], 16) == last
                moved_index = slot(last, 13)
                assert int(before[moved_index], 16) == old_length
                assert int(after[moved_index], 16) == index + 1
                operation = "swap_last_then_pop"
        else:
            assert len(group) == 2 and old_length == 4 and new_length == 2
            first, second = ordered
            assert first["old_one_based_index"] == 1
            assert second["old_one_based_index"] == old_length
            assert int(before[element(0)], 16) == first["position_id"]
            assert int(before[element(old_length - 1)], 16) == second["position_id"]
            moved = int(before[element(old_length - 2)], 16)
            assert int(after[element(0)], 16) == moved
            assert element(old_length - 1) not in after and element(old_length - 2) not in after
            moved_index = slot(moved, 13)
            assert int(before[moved_index], 16) == old_length - 1
            assert int(after[moved_index], 16) == 1
            operation = "two_removals_final_state_matches_swap_pop"
        array_checks.append({"tx": tx, "user": f"0x{user:040x}",
                             "removed_ids_in_event_order": [row["position_id"] for row in ordered],
                             "old_length": old_length, "new_length": new_length,
                             "operation": operation})
    assert len(array_checks) == 14
    assert collections.Counter(row["operation"] for row in array_checks) == {
        "tail_pop": 11, "swap_last_then_pop": 2,
        "two_removals_final_state_matches_swap_pop": 1}
    assert {row["position_id"] for row in saved["rows"]} == set(SAMPLE_IDS)
    for row in saved["rows"]:
        position_id = row["position_id"]
        assert row["opening_tx"] == open_by_id[position_id]["tx"]
        assert row["mapping_slot"] == slot(position_id, 13)
        assert row["block"] <= manifest["block"] and len(row["block_hash"]) == 66
        assert int(row["getter_output"], 16) == int(row["raw_storage"], 16)
        assert int(row["getter_output"], 16) == open_by_id[position_id]["one_based_index"]
    return {
        "pin": manifest["block"], "block_hash": manifest["block_hash"],
        "exchange_proxy": EXCHANGE, "implementation": IMPLEMENTATION,
        "selector": SELECTOR, "mapping_base_slot": 13, "user_open_ids_array_base_slot": 12,
        "behavior_label": "one-based index of position ID in its user's open-position array",
        "opening_count": len(opens), "removal_count": len(removals),
        "removal_array_group_count": len(array_checks),
        "historical_getter_count": len(saved["rows"]),
        "openings": opens, "removals": removals, "removal_array_checks": array_checks,
        "historical_getters": saved["rows"],
        "limits": [
            "The selector's original source name is unknown.",
            "Thirteen single-removal groups match swap-and-pop, and one double-removal final state is consistent with it. Intermediate writes in the double-removal transaction are not reconstructed.",
            "Other mutation branches and larger same-user removal batches remain untested.",
            "Historical getter probes use block-end state, which may differ from a transaction's immediate poststate when later transactions share the block.",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh three archived nonzero getter calls")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange position index: {result['opening_count']} opens, "
          f"{result['removal_count']} removals, {result['historical_getter_count']} getter calls")
