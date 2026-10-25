#!/usr/bin/env python3
"""Recover the Exchange queue node layout from three enqueues and a harvest."""

import json
import pathlib

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
AMOUNT = 7623942182351823589
EVENT = "Enqueued(address,uint256,uint256)"
TOPIC = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
ENQUEUES = (
    ("0x3bc7029ee0d72c5dbacfb74dddc183ddb6206adca6ed702014eb90c28cf2d39e", 1, 48173881),
    ("0xc7ba4aaf1bdda8e24c2c8a228e315f39a879e7c9c87786eb260fa07c09b99940", 2, 48173885),
    ("0x1fc54a082055d35c0b79b6fc5f6c2a7004840531f5bcb9b6ec4450a93be2384f", 3, 48173887),
)
HARVEST = "0x4214fa14d9c5bf46fade1c7f3ca8d242baefaa52426395b1840f43b626ee8a99"
KECCAK = Keccak()


def slot(index):
    return "0x" + index.to_bytes(32, "big").hex()


def mapped(key, base, offset=0):
    return slot(int.from_bytes(KECCAK(key.to_bytes(32, "big") + base.to_bytes(32, "big")), "big") + offset)


def storage(diff, phase, key):
    return int(diff.get(phase, {}).get(PROXY, {}).get("storage", {}).get(key, "0x0"), 16)


def verify():
    assert "0x" + KECCAK(EVENT.encode()).hex() == TOPIC
    close_paths = {row["tx"]: row for row in json.loads((ATLAS / "exchange_close_paths.json").read_text())["transactions"]}
    rows = []
    for tx, node_id, block in ENQUEUES:
        receipt = json.loads((HISTORICAL / f"{tx}.receipt.json").read_text())
        call = json.loads((HISTORICAL / f"{tx}.calls.json").read_text())
        diff = json.loads((HISTORICAL / f"{tx}.state_diff.json").read_text())
        assert receipt["status"] == "0x1" and int(receipt["blockNumber"], 16) == block
        assert call["input"][:10] == "0x251fb27d"
        events = [log for log in receipt["logs"]
                  if log["address"].lower() == PROXY and log["topics"][0] == TOPIC]
        assert len(events) == 1
        event = events[0]
        assert len(event["topics"]) == 3 and event["topics"][2] == slot(node_id)
        user = int(event["topics"][1], 16)
        assert int(event["data"], 16) == AMOUNT
        assert close_paths[tx]["queue_delta"] == AMOUNT
        assert storage(diff, "post", slot(17)) == node_id + 1
        assert storage(diff, "post", slot(18)) == node_id * AMOUNT
        if node_id == 1:
            assert storage(diff, "post", slot(16)) == 1
        assert storage(diff, "post", mapped(node_id, 15)) == user
        assert storage(diff, "post", mapped(node_id, 15, 1)) == AMOUNT
        assert storage(diff, "post", mapped(user, 19)) == AMOUNT
        assert storage(diff, "post", mapped(user, 20)) == node_id
        assert storage(diff, "post", mapped(user, 21)) == node_id
        rows.append({"tx": tx, "block": block, "user": "0x" + user.to_bytes(20, "big").hex(),
                     "node_id": node_id, "amount": str(AMOUNT),
                     "node_owner_slot": mapped(node_id, 15),
                     "node_amount_slot": mapped(node_id, 15, 1),
                     "user_queued_amount_slot": mapped(user, 19),
                     "user_head_slot": mapped(user, 20), "user_tail_slot": mapped(user, 21)})

    receipt = json.loads((HISTORICAL / f"{HARVEST}.receipt.json").read_text())
    call = json.loads((HISTORICAL / f"{HARVEST}.calls.json").read_text())
    diff = json.loads((HISTORICAL / f"{HARVEST}.state_diff.json").read_text())
    assert receipt["status"] == "0x1" and int(receipt["blockNumber"], 16) == 48173890
    assert call["to"].lower() == PROXY and call["input"][:10] == "0xddc63262"
    assert int(call["input"][10:], 16) == 32 and int(call["output"], 16) == 3 * AMOUNT
    assert storage(diff, "pre", slot(16)) == 1 and storage(diff, "post", slot(16)) == 4
    assert storage(diff, "pre", slot(18)) == 3 * AMOUNT and storage(diff, "post", slot(18)) == 0
    cleared = []
    for row in rows:
        user = int(row["user"], 16)
        node_id = row["node_id"]
        for key in (mapped(node_id, 15, 1), mapped(user, 19), mapped(user, 20), mapped(user, 21)):
            assert storage(diff, "pre", key) in (AMOUNT, node_id)
            assert storage(diff, "post", key) == 0
        cleared.append(node_id)
    result = {"pin_block": 48902346, "exchange_proxy": PROXY,
              "event_catalog": [{"topic0": TOPIC, "reconstructed_signature": EVENT,
                                 "status": "observed_historical_topic"}],
              "global_slots": {"16": "queue head node id", "17": "next queue node id",
                               "18": "total queued amount"},
              "mapping_layout": {"15": "node[id] owner at base slot; amount at base slot + 1",
                                 "19": "user queued amount", "20": "user queue head id",
                                 "21": "user queue tail id"},
              "enqueues": rows,
              "harvest": {"tx": HARVEST, "max_entries": 32, "returned_amount": str(3 * AMOUNT),
                          "head_after": 4, "total_queued_after": 0, "cleared_node_ids": cleared},
              "limitations": ["The three historical enqueues each create a first node for a distinct user; a synthetic same-user append is verified separately in exchange_queue_append_behavior.json.",
                              "The historical harvest proves the sampled three-node clear path; partial entry counts, same-user harvests, and underfunded node payouts are checked separately with read-only simulations.",
                              "Diff-mode omitted zero post words are interpreted using the prestate and event sequence."]}
    (ATLAS / "exchange_queue_layout_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange queue: 3 enqueues, 5 mapping roots, and 3-node harvest verified")


if __name__ == "__main__":
    verify()
