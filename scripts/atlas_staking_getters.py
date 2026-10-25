#!/usr/bin/env python3
"""Verify live Staking getter names and storage semantics at the pinned block."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "staking"
OUT = ATLAS / "staking_getters_behavior.json"
SAVED = ARTIFACTS / "pinned_getters.json"
PROXY = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
IMPLEMENTATION = "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15"
PIN = 48902346
KECCAK = Keccak()

DIRECT = {
    "0x13dd495b": ("authorizedExecutor()", 16, "address"),
    "0x2b6fdc7e": ("unallocatedRewards()", 8, "uint256"),
    "0x3644e515": ("DOMAIN_SEPARATOR()", 1, "bytes32"),
    "0x51ed6a30": ("stakeToken()", 3, "address"),
    "0x817b1cd2": ("totalStaked()", 5, "uint256"),
    "0x8da5cb5b": ("owner()", 15, "address"),
    "0x939d6237": ("accRewardPerShare()", 6, "uint256"),
    "0xcab64bcd": ("rewardReserve()", 7, "uint256"),
    "0xd2f7265a": ("exchange()", 2, "address"),
    "0xf7c618c1": ("rewardToken()", 4, "address"),
}
MAPPINGS = {
    "0x31d7a262": ("pendingRewards(address)", 11),
    "0x5873eb9b": ("rewardDebt(address)", 10),
    "0x60217267": ("stakedBalance(address)", 9),
    "0x7ecebe00": ("nonces(address)", 12),
}
TYPEHASHES = {
    "0x0700cc42": ("UNSTAKE_TYPEHASH()", "0xfa2871b5"),
    "0x5638b3e5": ("DISTRIBUTE_TYPEHASH()", "0xf0355460"),
    "0x6b0509b1": ("CLAIM_TYPEHASH()", "0x9c96d4a1"),
    "0x89ee09f0": ("STAKE_TYPEHASH()", "0x83115825"),
}
DERIVED = {"0x78e890ba": "domainSeparatorV4()", "0xf40f0f52": "pendingReward(address)"}
PACKED_SELECTOR = "0x6090cf16"


def user_slot(user, base):
    return "0x" + KECCAK(int(user, 16).to_bytes(32, "big") + base.to_bytes(32, "big")).hex()


def calldata(selector, user=None):
    return selector if user is None else selector + int(user, 16).to_bytes(32, "big").hex()


def capture():
    from atlas_tokenomics import rpc

    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]

    def call(selector, user=None, override=None):
        params = [{"to": PROXY, "data": calldata(selector, user)}, hex(PIN)]
        if override is not None:
            params.append(override)
        return rpc(url, "eth_call", params)

    slot_numbers = sorted({slot for _, slot, _ in DIRECT.values()} | {16})
    storage = {str(slot): rpc(url, "eth_getStorageAt", [PROXY, hex(slot), hex(PIN)])
               for slot in slot_numbers}
    simple_selectors = sorted(set(DIRECT) | set(TYPEHASHES) | {"0x78e890ba", PACKED_SELECTOR})
    simple = {selector: call(selector) for selector in simple_selectors}
    reward_saved = json.loads((ARTIFACTS / "pinned_reward_getters.json").read_text())
    nonce_saved = json.loads((ARTIFACTS / "pinned_nonce_getters.json").read_text())
    reward_users = [row["user"] for row in reward_saved["samples"]]
    nonce_users = [row["user"] for row in nonce_saved["samples"]]
    mapping_rows = []
    for selector, (_, base) in MAPPINGS.items():
        for user in (nonce_users if base == 12 else reward_users):
            slot = user_slot(user, base)
            mapping_rows.append({"selector": selector, "user": user, "base_slot": base,
                                 "storage_slot": slot,
                                 "storage_value": rpc(url, "eth_getStorageAt", [PROXY, slot, hex(PIN)]),
                                 "getter_output": call(selector, user)})
    reward_rows = [{"user": user, "output": call("0xf40f0f52", user)} for user in reward_users]
    raw16 = int(storage["16"], 16)
    slot16 = "0x" + (16).to_bytes(32, "big").hex()
    overrides = {}
    for name, byte in (("off", 0), ("on", 1), ("high", 255)):
        value = (raw16 & ~(255 << 160)) | (byte << 160)
        override = {PROXY: {"stateDiff": {slot16: "0x" + value.to_bytes(32, "big").hex()}}}
        overrides[name] = {"storage_word": override[PROXY]["stateDiff"][slot16],
                           "output": call(PACKED_SELECTOR, override=override),
                           "executor_output": call("0x13dd495b", override=override)}
    SAVED.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                 "direct_storage": storage, "simple_getters": simple,
                                 "mapping_getters": mapping_rows, "pending_reward_getters": reward_rows,
                                 "packed_overrides": overrides}, indent=2) + "\n")


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads(SAVED.read_text())
    assert saved["pin_block"] == manifest["block"] == PIN
    assert saved["pin_hash"] == manifest["block_hash"]
    catalog = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]
    traces = {row["selector"]: row for row in catalog["views"]}
    assert catalog["target"] == PROXY
    signatures = {}
    direct_rows = []
    for selector, (signature, slot, kind) in DIRECT.items():
        assert "0x" + KECCAK(signature.encode()).hex()[:8] == selector
        assert traces[selector]["direct_slots"] == [slot] and not traces[selector]["failed"]
        word = int(saved["direct_storage"][str(slot)], 16)
        expected = word & ((1 << 160) - 1) if kind == "address" else word
        actual = int(saved["simple_getters"][selector], 16)
        assert actual == expected, (selector, actual, expected)
        signatures[selector] = signature
        direct_rows.append({"selector": selector, "signature": signature, "slot": slot,
                            "type": kind, "storage_word": saved["direct_storage"][str(slot)],
                            "output": saved["simple_getters"][selector]})
    staking = json.loads((ATLAS / "staking_behavior.json").read_text())
    typehash_rows = []
    for selector, (signature, bysig_selector) in TYPEHASHES.items():
        assert "0x" + KECCAK(signature.encode()).hex()[:8] == selector
        preimage = staking["typehash_preimages"][bysig_selector]
        actual = saved["simple_getters"][selector]
        assert actual == "0x" + KECCAK(preimage.encode()).hex()
        assert not traces[selector]["failed"] and traces[selector]["direct_slots"] == []
        signatures[selector] = signature
        typehash_rows.append({"selector": selector, "signature": signature,
                              "type_string": preimage, "output": actual})
    reward_saved = json.loads((ARTIFACTS / "pinned_reward_getters.json").read_text())
    nonce_saved = json.loads((ARTIFACTS / "pinned_nonce_getters.json").read_text())
    assert reward_saved["pin_hash"] == nonce_saved["pin_hash"] == manifest["block_hash"]
    reward_by_user = {row["user"]: row for row in reward_saved["samples"]}
    nonce_by_user = {row["user"]: row for row in nonce_saved["samples"]}
    mapping_rows = []
    for row in saved["mapping_getters"]:
        selector = row["selector"]
        signature, base = MAPPINGS[selector]
        assert "0x" + KECCAK(signature.encode()).hex()[:8] == selector
        assert row["base_slot"] == base and row["storage_slot"] == user_slot(row["user"], base)
        assert int(row["getter_output"], 16) == int(row["storage_value"], 16)
        assert any(item["base_slot"] == base for item in traces[selector]["mapping_matches"])
        if base == 12:
            assert row["storage_value"] == nonce_by_user[row["user"]]["counter_storage"]
            assert row["getter_output"] == nonce_by_user[row["user"]]["counter_getter"]
        else:
            assert row["storage_value"] == reward_by_user[row["user"]]["storage"][str(base)]["value"]
        signatures[selector] = signature
        mapping_rows.append(row)
    assert len(mapping_rows) == 12
    domain = saved["simple_getters"]["0x78e890ba"]
    assert "0x" + KECCAK(DERIVED["0x78e890ba"].encode()).hex()[:8] == "0x78e890ba"
    assert domain == saved["simple_getters"]["0x3644e515"]
    signatures["0x78e890ba"] = DERIVED["0x78e890ba"]
    assert "0x" + KECCAK(DERIVED["0xf40f0f52"].encode()).hex()[:8] == "0xf40f0f52"
    for row in saved["pending_reward_getters"]:
        assert row["output"] == reward_by_user[row["user"]]["pending_reward_getter"]
    assert len(saved["pending_reward_getters"]) == 3
    signatures["0xf40f0f52"] = DERIVED["0xf40f0f52"]

    word16 = int(saved["direct_storage"]["16"], 16)
    assert int(saved["simple_getters"][PACKED_SELECTOR], 16) == bool((word16 >> 160) & 255)
    for name, expected in (("off", 0), ("on", 1), ("high", 1)):
        probe = saved["packed_overrides"][name]
        assert int(probe["output"], 16) == expected
        assert int(probe["executor_output"], 16) == (word16 & ((1 << 160) - 1))
    assert "0x6090cf16" not in signatures
    return {"pin_block": PIN, "block_hash": manifest["block_hash"],
            "staking_proxy": PROXY, "implementation": IMPLEMENTATION,
            "selector_reconstructions": signatures,
            "direct_slot_getters": direct_rows, "mapping_getter_samples": mapping_rows,
            "typehash_getters": typehash_rows,
            "domain_separator_alias": {"selector": "0x78e890ba", "output": domain},
            "pending_reward_sample_count": len(saved["pending_reward_getters"]),
            "unnamed_packed_getter": {"selector": PACKED_SELECTOR, "storage_slot": 16,
                                      "byte_offset": 20, "meaning": "whether byte 20 is nonzero",
                                      "probe_outputs": {name: row["output"] for name, row in saved["packed_overrides"].items()}},
            "limitations": ["Names are exact selector hashes with matching storage or typehash behavior; original Solidity source is unavailable.",
                            "The domainSeparatorV4 alias was checked at the pinned chain state only.",
                            "Selector 0x6090cf16 has a verified packed-flag meaning but no source name.",
                            "The derived pendingReward formula is checked in staking_behavior.json for three pinned users and 26 historical claims; extreme arithmetic boundaries remain open."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Staking getters: {len(result['selector_reconstructions'])} signatures, "
          f"{len(result['mapping_getter_samples'])} nonzero mapping checks, packed flag checked")
