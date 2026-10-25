#!/usr/bin/env python3
"""Check pinned developer-fee claims in both older Exchange suites."""

import argparse
import gzip
import json
import os
import pathlib

from atlas_all_suite_claims import OUT as SCALARS
from atlas_exchange_dev_fee_claim import all_logs, balance_slot, slot_key
from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "accounting_claims" / "older_fee_claims.json.gz"
PIN = 48_902_346
LOW128 = (1 << 128) - 1
OUTSIDER = "0x" + "44" * 20
TARGET = "0x" + "33" * 20
SUITES = (
    {
        "exchange": "0x1b534e482b92bb6daff452cd12f2e35219e13493",
        "sender": "0x69b4b92f02ff415e0c966686e00d2783b395d690",
        "recipient": TARGET,
        "staking": "0xfe8f8d20a8e3b6221e93926e5a08a64354a45688",
        "signature": "claimDevFees(address)",
        "event": "DevFeesClaimed(address,uint256)",
        "staker_event": "StakerFeesClaimed(address,uint256)",
        "revert": "0x30cd7471",
    },
    {
        "exchange": "0x2ede04561914c61a5f49212609541934fd7f5901",
        "sender": "0xa5adedffc44d34ffdbcfa2fdd56af8654f1e1e0c",
        "recipient": "0xa5adedffc44d34ffdbcfa2fdd56af8654f1e1e0c",
        "staking": "0x546cb5afbb79dbf1bb70cd1bae5a37e508ed1fc4",
        "signature": "claimDevFees()",
        "event": "DevFeesClaimed(address,uint256,uint256)",
        "staker_event": "StakerFeesClaimed(address,uint256,uint256)",
        "revert": "0x2d016ae6",
    },
)


def saved(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def calldata(suite):
    selector = "0x" + Keccak()(suite["signature"].encode()).hex()[:8]
    if suite["signature"] == "claimDevFees(address)":
        return selector + suite["recipient"][2:].rjust(64, "0")
    return selector


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    rows = []
    for suite in SUITES:
        cases = {}
        for name, sender in (("authorized", suite["sender"]), ("outsider", OUTSIDER)):
            call = {
                "from": sender,
                "to": suite["exchange"],
                "data": calldata(suite),
                "gas": hex(16_000_000),
            }
            trace = rpc(
                url,
                "debug_traceCall",
                [
                    call,
                    hex(PIN),
                    {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
                ],
            )
            item = {"sender": sender, "trace": trace}
            if name == "authorized":
                item["diff"] = rpc(
                    url,
                    "debug_traceCall",
                    [
                        call,
                        hex(PIN),
                        {
                            "tracer": "prestateTracer",
                            "tracerConfig": {"diffMode": True},
                        },
                    ],
                )
            cases[name] = item
        push_call = {
            "from": OUTSIDER,
            "to": suite["exchange"],
            "data": "0x7b9f5264",
            "gas": hex(16_000_000),
        }
        push = {
            "trace": rpc(
                url,
                "debug_traceCall",
                [
                    push_call,
                    hex(PIN),
                    {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
                ],
            ),
            "diff": rpc(
                url,
                "debug_traceCall",
                [
                    push_call,
                    hex(PIN),
                    {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}},
                ],
            ),
        }
        reward_call = {
            "to": suite["exchange"],
            "data": "0xe53e3de6" + TARGET[2:].rjust(64, "0") + f"{1:064x}",
            "gas": hex(16_000_000),
        }
        reward_cases = {}
        for name, sender in (("staking", suite["staking"]), ("outsider", OUTSIDER)):
            call = {**reward_call, "from": sender}
            item = {
                "trace": rpc(
                    url,
                    "debug_traceCall",
                    [
                        call,
                        hex(PIN),
                        {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
                    ],
                )
            }
            if name == "staking":
                item["diff"] = rpc(
                    url,
                    "debug_traceCall",
                    [
                        call,
                        hex(PIN),
                        {
                            "tracer": "prestateTracer",
                            "tracerConfig": {"diffMode": True},
                        },
                    ],
                )
            reward_cases[name] = item
        rows.append(
            {
                "suite": suite,
                "cases": cases,
                "staker_push": push,
                "reward_credit": reward_cases,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(
        gzip.compress(
            json.dumps(
                {"pin": PIN, "block_hash": header["hash"], "rows": rows},
                separators=(",", ":"),
            ).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    return verify()


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    scalars = saved(SCALARS)
    payload = saved(OUT)
    assert payload["pin"] == scalars["pin"] == manifest["block"] == PIN
    assert payload["block_hash"] == scalars["block_hash"] == manifest["block_hash"]
    assert len(payload["rows"]) == len(SUITES)
    result = []
    for index, (row, suite) in enumerate(zip(payload["rows"], SUITES)):
        assert row["suite"] == suite
        assert set(row["cases"]) == {"authorized", "outsider"}
        assert calldata(suite).startswith(
            "0x" + Keccak()(suite["signature"].encode()).hex()[:8]
        )
        exchange = suite["exchange"]
        raw = scalars["suites"][index]["exchange"]
        amount = int(raw["26"], 16) >> 128
        assert amount > 0
        authorized = row["cases"]["authorized"]
        assert authorized["sender"] == suite["sender"]
        trace = authorized["trace"]
        assert trace["to"].lower() == exchange
        assert trace["input"] == calldata(suite)
        assert not trace.get("error")
        logs = list(all_logs(trace))
        assert len(logs) == 1
        event = logs[0]
        assert event["address"].lower() == exchange
        assert event["topics"] == [
            "0x" + Keccak()(suite["event"].encode()).hex(),
            "0x" + suite["recipient"][2:].rjust(64, "0"),
        ]
        assert int(event["data"][2:66], 16) == amount
        if index == 0:
            assert len(event["data"]) == 66
        else:
            assert len(event["data"]) == 130
            assert int(event["data"][66:130], 16) == amount
        balance_key = balance_slot(suite["recipient"])
        pre = authorized["diff"]["pre"][exchange]["storage"]
        post = authorized["diff"]["post"][exchange]["storage"]
        assert set(post) == {slot_key(22), slot_key(26), balance_key}
        assert int(pre[slot_key(22)], 16) == int(raw["22"], 16)
        assert int(pre[slot_key(26)], 16) == int(raw["26"], 16)
        assert int(post[slot_key(22)], 16) == int(pre[slot_key(22)], 16) + amount
        assert int(post[slot_key(26)], 16) == int(pre[slot_key(26)], 16) & LOW128
        assert (
            int(post[balance_key], 16) == int(pre.get(balance_key, "0x0"), 16) + amount
        )
        outsider = row["cases"]["outsider"]
        assert outsider["sender"] == OUTSIDER
        assert outsider["trace"].get("error") == "execution reverted"
        assert outsider["trace"].get("output") == suite["revert"]
        assert not list(all_logs(outsider["trace"]))
        staker_fee = int(raw["26"], 16) & LOW128
        push = row["staker_push"]
        push_trace = push["trace"]
        assert push_trace["to"].lower() == exchange
        assert push_trace["input"] == "0x7b9f5264"
        assert not push_trace.get("error")
        push_logs = list(all_logs(push_trace))
        assert len(push_logs) == 1
        push_event = push_logs[0]
        assert push_event["address"].lower() == exchange
        assert push_event["topics"] == [
            "0x" + Keccak()(suite["staker_event"].encode()).hex(),
            "0x" + suite["staking"][2:].rjust(64, "0"),
        ]
        assert int(push_event["data"][2:66], 16) == staker_fee
        if index == 0:
            assert len(push_event["data"]) == 66
        else:
            assert len(push_event["data"]) == 130
            assert int(push_event["data"][66:130], 16) == staker_fee
        push_pre = push["diff"]["pre"][exchange]["storage"]
        push_post = push["diff"]["post"][exchange]["storage"]
        staking_key = balance_slot(suite["staking"])
        assert set(push_post) == {slot_key(22), slot_key(26), staking_key}
        assert int(push_pre[slot_key(22)], 16) == int(raw["22"], 16)
        assert int(push_pre[slot_key(26)], 16) == int(raw["26"], 16)
        assert (
            int(push_post[slot_key(22)], 16)
            == int(push_pre[slot_key(22)], 16) + staker_fee
        )
        assert (
            int(push_post[slot_key(26)], 16)
            == int(push_pre[slot_key(26)], 16) & ~LOW128
        )
        assert (
            int(push_post[staking_key], 16)
            == int(push_pre.get(staking_key, "0x0"), 16) + staker_fee
        )
        reward = row["reward_credit"]
        assert set(reward) == {"staking", "outsider"}
        credit = reward["staking"]["trace"]
        assert credit["from"].lower() == suite["staking"]
        assert credit["to"].lower() == exchange
        assert credit["input"] == "0xe53e3de6" + TARGET[2:].rjust(64, "0") + f"{1:064x}"
        assert not credit.get("error")
        credit_logs = list(all_logs(credit))
        assert len(credit_logs) == 1
        assert credit_logs[0]["topics"] == [
            "0x" + Keccak()(b"StakingRewardCredited(address,uint256)").hex(),
            "0x" + TARGET[2:].rjust(64, "0"),
        ]
        assert int(credit_logs[0]["data"], 16) == 1
        credit_pre = reward["staking"]["diff"]["pre"][exchange]["storage"]
        credit_post = reward["staking"]["diff"]["post"][exchange]["storage"]
        target_key = balance_slot(TARGET)
        assert set(credit_post) == {staking_key, target_key}
        assert int(credit_post[staking_key], 16) == int(credit_pre[staking_key], 16) - 1
        assert (
            int(credit_post[target_key], 16)
            == int(credit_pre.get(target_key, "0x0"), 16) + 1
        )
        outsider_credit = reward["outsider"]["trace"]
        assert outsider_credit.get("error") == "execution reverted"
        assert outsider_credit.get("output") == "0x538ccdfd"
        assert not list(all_logs(outsider_credit))
        result.append(
            {
                "suite": index,
                "signature": suite["signature"],
                "recipient": suite["recipient"],
                "claim_amount_18": amount,
                "ordinary_balance_credit_18": amount,
                "staker_fee_push_18": staker_fee,
                "staking_reward_credit_tested_raw_units": 1,
                "external_transfer": False,
            }
        )
    return {"pin": PIN, "rows": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
