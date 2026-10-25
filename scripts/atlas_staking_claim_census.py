#!/usr/bin/env python3
"""Reconcile pinned Staking reward claims with its Exchange balance."""

import argparse
import collections
import gzip
import json
import os
import pathlib

from atlas_deployer_scope import call
from atlas_exchange_sweeps import word
from atlas_exchange_withdrawal_history import rpc
from atlas_older_event_census import address_shaped_topics, fetch
from atlas_older_positions import rpc_batches
from atlas_staking import EVENTS, PRECISION, PROXY, TOKEN
from atlas_staking_getters import DIRECT, MAPPINGS, user_slot

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "staking_claim_census" / "pinned.json.gz"
BALANCES = ROOT / "artifacts" / "newest_account_census" / "account_balances.json.gz"
PINNED_GETTERS = ROOT / "artifacts" / "staking" / "pinned_getters.json"
PIN = 48_902_346
CREATION = 47_855_135
WINDOW = 100_000
STAKED = EVENTS["Staked(address,uint256)"]
UNSTAKED = EVENTS["Unstaked(address,uint256)"]
CLAIMED = EVENTS["Claimed(address,uint256)"]
DISTRIBUTED = EVENTS["Distributed(uint256,uint256,uint256,uint256)"]
NONCE = EVENTS["NonceUsed(address,uint256,uint256)"]


def saved(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def event_users(windows):
    users = set()
    for window in windows:
        for log in window["logs"]:
            users.update(address_shaped_topics(log))
    return sorted(users)


def capture():
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert (
        rpc("eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    )
    windows = []
    for start in range(CREATION, PIN + 1, WINDOW):
        windows.extend(fetch(PROXY, start, min(PIN, start + WINDOW - 1)))
        print(f"staking through block {windows[-1]['to_block']}", flush=True)
    users = event_users(windows)
    requests = []
    targets = {}

    def request(method, params, target):
        identifier = len(requests)
        requests.append(call(method, params, identifier))
        targets[identifier] = target

    for selector, (signature, slot, _) in DIRECT.items():
        if signature in (
            "totalStaked()",
            "accRewardPerShare()",
            "rewardReserve()",
            "unallocatedRewards()",
        ):
            request(
                "eth_call",
                [{"to": PROXY, "data": selector}, hex(PIN)],
                ("global", signature),
            )
            request(
                "eth_getStorageAt",
                [PROXY, hex(slot), hex(PIN)],
                ("raw_global", signature),
            )
    for user in users:
        for selector, (signature, base) in MAPPINGS.items():
            if signature == "nonces(address)":
                continue
            request(
                "eth_call",
                [{"to": PROXY, "data": selector + word(user)}, hex(PIN)],
                (user, signature),
            )
            request(
                "eth_getStorageAt",
                [PROXY, user_slot(user, base), hex(PIN)],
                (user, "raw_" + signature),
            )
        request(
            "eth_call",
            [{"to": PROXY, "data": "0xf40f0f52" + word(user)}, hex(PIN)],
            (user, "pendingReward(address)"),
        )
    request(
        "eth_call",
        [{"to": TOKEN, "data": "0x70a08231" + word(PROXY)}, hex(PIN)],
        ("global", "paperBalanceOfStaking"),
    )
    results = rpc_batches(os.environ["PAPERTRADE_ARCHIVE_RPC"], requests)
    reads = {}
    for identifier, value in results.items():
        owner, field = targets[identifier]
        reads.setdefault(owner, {})[field] = value
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "staking": PROXY,
        "creation_block": CREATION,
        "window_target": WINDOW,
        "windows": windows,
        "reads": reads,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    return verify()


def verify():
    payload = saved(OUT)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    prior = json.loads(PINNED_GETTERS.read_text())
    assert payload["pin"] == prior["pin_block"] == manifest["block"] == PIN
    assert payload["block_hash"] == prior["pin_hash"] == manifest["block_hash"]
    assert payload["staking"] == PROXY and payload["creation_block"] == CREATION
    assert payload["window_target"] == WINDOW
    cursor = CREATION
    previous = (-1, -1)
    counts = collections.Counter()
    staked = collections.Counter()
    claimed = collections.Counter()
    distributed = 0
    users = set()
    for window in payload["windows"]:
        start, end = window["from_block"], window["to_block"]
        assert start == cursor and start <= end <= PIN and len(window["logs"]) < 10_000
        cursor = end + 1
        for log in window["logs"]:
            assert log["address"].lower() == PROXY and log["removed"] is False
            block, index = int(log["blockNumber"], 16), int(log["logIndex"], 16)
            assert start <= block <= end and (block, index) > previous
            previous = (block, index)
            topic = log["topics"][0].lower()
            counts[topic] += 1
            users.update(address_shaped_topics(log))
            if topic in (STAKED, UNSTAKED, CLAIMED):
                assert len(log["topics"]) == 2 and len(log["data"]) == 66
                user = "0x" + log["topics"][1][-40:].lower()
                amount = int(log["data"], 16)
                if topic == STAKED:
                    staked[user] += amount
                elif topic == UNSTAKED:
                    staked[user] -= amount
                    assert staked[user] >= 0
                else:
                    claimed[user] += amount
            elif topic == DISTRIBUTED:
                assert len(log["topics"]) == 1 and len(log["data"]) == 258
                fields = [int(log["data"][i : i + 64], 16) for i in range(2, 258, 64)]
                assert fields[1] == fields[2]
                distributed += fields[1]
            elif topic == NONCE:
                assert len(log["topics"]) == 3
    assert cursor == PIN + 1
    assert sorted(users) == event_users(payload["windows"])
    reads = payload["reads"]
    assert set(reads) == users | {"global", "raw_global"}
    globals_ = reads["global"]
    for signature, slot in (
        ("totalStaked()", 5),
        ("accRewardPerShare()", 6),
        ("rewardReserve()", 7),
        ("unallocatedRewards()", 8),
    ):
        assert int(globals_[signature], 16) == int(reads["raw_global"][signature], 16)
        assert (
            globals_[signature]
            == prior["simple_getters"][
                next(
                    selector for selector, row in DIRECT.items() if row[0] == signature
                )
            ]
        )
        assert int(globals_[signature], 16) == int(
            prior["direct_storage"][str(slot)], 16
        )
    total_staked = int(globals_["totalStaked()"], 16)
    acc = int(globals_["accRewardPerShare()"], 16)
    reserve = int(globals_["rewardReserve()"], 16)
    unallocated = int(globals_["unallocatedRewards()"], 16)
    assert total_staked == int(globals_["paperBalanceOfStaking"], 16)
    assert sum(staked.values()) == total_staked
    assert distributed - sum(claimed.values()) == reserve
    pending_sum = 0
    nonzero_pending = 0
    for user in sorted(users):
        row = reads[user]
        for signature in (
            "stakedBalance(address)",
            "rewardDebt(address)",
            "pendingRewards(address)",
        ):
            assert int(row[signature], 16) == int(row["raw_" + signature], 16)
        stake = int(row["stakedBalance(address)"], 16)
        debt = int(row["rewardDebt(address)"], 16)
        pending = int(row["pendingRewards(address)"], 16)
        claim = pending + stake * acc // PRECISION - debt
        assert claim >= 0 and claim == int(row["pendingReward(address)"], 16)
        assert stake == staked[user]
        pending_sum += claim
        nonzero_pending += claim > 0
    balances = saved(BALANCES)
    staking_account = next(
        row for row in balances["accounts"] if row["address"] == PROXY
    )
    assert (
        int(staking_account["balance_getter"], 16)
        == int(staking_account["balance_storage"], 16)
        == reserve
    )
    assert pending_sum <= reserve
    return {
        "event_count": sum(counts.values()),
        "event_topics": dict(counts),
        "candidate_users": len(users),
        "stakers_with_positive_stake": sum(value > 0 for value in staked.values()),
        "users_with_positive_pending_reward": nonzero_pending,
        "staked_paper_18": total_staked,
        "distributed_rewards_18": distributed,
        "claimed_rewards_18": sum(claimed.values()),
        "reward_reserve_18": reserve,
        "sum_pending_rewards_18": pending_sum,
        "reserve_less_pending_18": reserve - pending_sum,
        "unallocated_rewards_18": unallocated,
        "staking_exchange_balance_18": int(staking_account["balance_getter"], 16),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
