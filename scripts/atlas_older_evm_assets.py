#!/usr/bin/env python3
"""Capture bounded EVM asset holdings for deployer contracts and older user proxies."""

import argparse
import collections
import gzip
import json
import os
import pathlib
import urllib.request

from atlas_deployer_scope import PIN, call, rpc_batch

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_evm_assets.json.gz"
TOKEN_INDEX = (12, 31, 50)
STAKING_INDEX = (14, 33, 52)
REWARD_BRIDGE = "0x6b9e773128f453f5c2c60935ee2de2cbc5390a24"
EXPECTED_STAKED = (
    78_405_369_412_664_783_977_870_135,
    49_241_878_597_153_416_318_359_500,
    8_555_409_857_614_638_237_952_993_078,
)


def saved_json(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def scope_accounts(scope):
    accounts = [
        {"address": row["address"], "set": min(index // 19, 2), "kind": "direct"}
        for index, row in enumerate(scope["rows"])
    ]
    for set_index, deployment in enumerate(scope["earlier_factory_deployments"]):
        for event in deployment["events"]:
            accounts.append(
                {
                    "address": "0x" + event["log"]["topics"][2][-40:].lower(),
                    "set": set_index,
                    "kind": "user_proxy",
                }
            )
    assert len(accounts) == 97
    assert len({row["address"] for row in accounts}) == len(accounts)
    return accounts


def balance_data(owner):
    return "0x70a08231" + int(owner, 16).to_bytes(32, "big").hex()


def reward_balance_probe(url, account):
    payload = call(
        "eth_call",
        [{"to": REWARD_BRIDGE, "data": balance_data(account)}, hex(PIN)],
        9999,
    )
    request = urllib.request.Request(
        url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    assert result["id"] == 9999 and "revert" in result["error"]["message"].lower()
    return {"account": account, "response": result}


def capture():
    scope = saved_json(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    accounts = scope_accounts(scope)
    tokens = [scope["rows"][index]["address"] for index in TOKEN_INDEX]
    staking = [scope["rows"][index]["address"] for index in STAKING_INDEX]
    assert scope["pin"] == manifest["block"] == PIN
    assert scope["block_hash"] == manifest["block_hash"]
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    calls = [call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    for set_index, address in enumerate(staking):
        for offset, slot in enumerate((3, 4, 5)):
            calls.append(
                call(
                    "eth_getStorageAt",
                    [address, hex(slot), hex(PIN)],
                    10 + 3 * set_index + offset,
                )
            )
        calls.append(
            call(
                "eth_call",
                [{"to": address, "data": "0x817b1cd2"}, hex(PIN)],
                40 + set_index,
            )
        )
    for token_index, token in enumerate(tokens):
        calls.append(
            call(
                "eth_call",
                [{"to": token, "data": "0x313ce567"}, hex(PIN)],
                30 + token_index,
            )
        )
    for account_index, account in enumerate(accounts):
        calls.append(
            call("eth_getBalance", [account["address"], hex(PIN)], 1000 + account_index)
        )
        for token_index, token in enumerate(tokens):
            calls.append(
                call(
                    "eth_call",
                    [{"to": token, "data": balance_data(account["address"])}, hex(PIN)],
                    2000 + token_index * len(accounts) + account_index,
                )
            )
    result = rpc_batch(os.environ["PAPERTRADE_ARCHIVE_RPC"], calls)
    assert result[0]["hash"].lower() == manifest["block_hash"]
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "asset_scope": "native HYPE and balanceOf on the three configured PAPER tokens",
        "reward_bridge": REWARD_BRIDGE,
        "reward_balance_probe": reward_balance_probe(
            os.environ["PAPERTRADE_ARCHIVE_RPC"], staking[0]
        ),
        "tokens": [
            {"address": token, "decimals_output": result[30 + index]}
            for index, token in enumerate(tokens)
        ],
        "staking": [
            {
                "address": address,
                "stake_token_slot": result[10 + 3 * index],
                "reward_token_slot": result[11 + 3 * index],
                "total_staked_slot": result[12 + 3 * index],
                "total_staked_getter": result[40 + index],
            }
            for index, address in enumerate(staking)
        ],
        "accounts": [
            {
                **account,
                "native_balance": result[1000 + index],
                "paper_balances": [
                    result[2000 + token_index * len(accounts) + index]
                    for token_index in range(len(tokens))
                ],
            }
            for index, account in enumerate(accounts)
        ],
    }
    summary = verify_payload(payload, scope, manifest)
    OUT.write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return summary


def verify_payload(saved, scope, manifest):
    assert saved["pin"] == scope["pin"] == manifest["block"] == PIN
    assert saved["block_hash"] == scope["block_hash"] == manifest["block_hash"]
    assert (
        saved["asset_scope"]
        == "native HYPE and balanceOf on the three configured PAPER tokens"
    )
    assert saved["reward_bridge"] == REWARD_BRIDGE
    probe = saved["reward_balance_probe"]
    assert probe["account"] == scope["rows"][STAKING_INDEX[0]]["address"]
    assert probe["response"]["id"] == 9999
    assert "revert" in probe["response"]["error"]["message"].lower()
    accounts = scope_accounts(scope)
    tokens = [scope["rows"][index]["address"] for index in TOKEN_INDEX]
    assert [row["address"] for row in saved["tokens"]] == tokens
    assert [int(row["decimals_output"], 16) for row in saved["tokens"]] == [18] * 3
    for index, row in enumerate(saved["staking"]):
        assert row["address"] == scope["rows"][STAKING_INDEX[index]]["address"]
        assert "0x" + row["stake_token_slot"][-40:] == tokens[index]
        assert "0x" + row["reward_token_slot"][-40:] == REWARD_BRIDGE
        assert int(row["total_staked_slot"], 16) == int(row["total_staked_getter"], 16)
    assert len(saved["staking"]) == 3
    assert len(saved["accounts"]) == len(accounts)
    summary = collections.defaultdict(
        lambda: {
            "accounts": 0,
            "nonzero_native": 0,
            "native_raw": 0,
            "nonzero_paper": [0, 0, 0],
            "paper_raw": [0, 0, 0],
        }
    )
    by_address = {}
    for expected, row in zip(accounts, saved["accounts"]):
        assert {key: row[key] for key in ("address", "set", "kind")} == expected
        assert len(row["paper_balances"]) == 3
        native = int(row["native_balance"], 16)
        assert 0 <= native < 1 << 256
        group = summary[f"set_{row['set']}_{row['kind']}"]
        group["accounts"] += 1
        group["nonzero_native"] += native > 0
        group["native_raw"] += native
        for index, value in enumerate(row["paper_balances"]):
            assert len(value) == 66 and value.startswith("0x")
            balance = int(value, 16)
            group["nonzero_paper"][index] += balance > 0
            group["paper_raw"][index] += balance
        by_address[row["address"]] = row
    assert sum(group["accounts"] for group in summary.values()) == 97
    assert [summary[f"set_{index}_direct"]["accounts"] for index in range(3)] == [
        19,
        19,
        21,
    ]
    assert [summary[f"set_{index}_user_proxy"]["accounts"] for index in range(2)] == [
        33,
        5,
    ]
    assert all(
        group["native_raw"] == group["nonzero_native"] == 0
        for group in summary.values()
    )
    staking_comparison = []
    for index, staking_row in enumerate(saved["staking"]):
        held = int(by_address[staking_row["address"]]["paper_balances"][index], 16)
        staked = int(staking_row["total_staked_slot"], 16)
        staking_comparison.append(
            {
                "set": index,
                "staking": staking_row["address"],
                "paper_held_raw": held,
                "total_staked_raw": staked,
                "difference_raw": held - staked,
            }
        )
        assert held == staked == EXPECTED_STAKED[index]
        assert summary[f"set_{index}_direct"]["nonzero_paper"] == [
            int(i == index) for i in range(3)
        ]
        assert summary[f"set_{index}_direct"]["paper_raw"][index] == held
    assert all(
        group["nonzero_paper"] == [0, 0, 0]
        for name, group in summary.items()
        if name.endswith("user_proxy")
    )
    return {
        "pin": PIN,
        "tokens": tokens,
        "groups": dict(summary),
        "staking_comparison": staking_comparison,
    }


def verify():
    scope = saved_json(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    return verify_payload(saved_json(OUT), scope, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="refresh pinned archive reads"
    )
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
