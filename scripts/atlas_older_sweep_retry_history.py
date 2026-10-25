#!/usr/bin/env python3
"""Check two live older Exchange sweep retries against EVM and Core execution."""

import argparse
import collections
import gzip
import json
import os
import pathlib

from atlas_deployer_scope import IMPLEMENTATION_SLOT, PIN
from atlas_exchange_sweeps import mapping_slot
from atlas_factory_events import Keccak
from atlas_older_event_census import OUT as EVENTS
from atlas_older_exchange_library import children
from atlas_older_positions import saved, words
from atlas_older_proxy_core import OUT as CORE_LEDGER
from atlas_older_proxy_core import raw, spot_delta
from atlas_older_upgrade import OUT as UPGRADE
from atlas_older_upgrade import PROXY, REPLACEMENT
from atlas_tokenomics import rpc
from audit_corewriter_rejections import ERROR, action_bytes
from audit_sweep_event_census import TOPICS
from audit_sweep_settlement import post_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_sweep_retry_history.json.gz"
EXPLORER = "https://rpc.hyperliquid.xyz/explorer"
WRITER = "0x3333333333333333333333333333333333333333"
TOPUP_HELPER = "0x1b975d2b182ae23d8049fb28fbb19bbfd35e5cc6"
HELPED_PROXY = "0x07d38b03587edade651ee1520dfb619809992337"
SPOT_UNIT = 100_000_000


def sweep_logs(events):
    rows = []
    names = {topic: name for name, topic in TOPICS.items()}
    for window in events["windows"]:
        for log in window["logs"]:
            kind = names.get(log["topics"][0].lower())
            if kind is None:
                continue
            user = "0x" + log["topics"][1][-40:].lower()
            row = {
                "kind": kind,
                "user": user,
                "tx": log["transactionHash"].lower(),
                "block": int(log["blockNumber"], 16),
                "block_hash": log["blockHash"].lower(),
                "index": int(log["logIndex"], 16),
            }
            if kind == "requested":
                row["proxy"] = "0x" + log["topics"][2][-40:].lower()
                spot, perp, recorded_block = words(log["data"])
                assert recorded_block == row["block"]
                row["spot_raw"], row["perp_raw"] = spot, perp
            elif kind == "cleared":
                row["proxy"] = "0x" + log["topics"][2][-40:].lower()
                assert log["data"] == "0x"
            else:
                (row["credit_raw"],) = words(log["data"])
            rows.append(row)
    assert len(rows) == 36
    assert collections.Counter(row["kind"] for row in rows) == {
        "requested": 18,
        "swept": 16,
        "cleared": 2,
    }
    assert rows == sorted(rows, key=lambda row: (row["block"], row["index"]))
    pending = {}
    cases = []
    clearing = {}
    for row in rows:
        user, kind = row["user"], row["kind"]
        if kind == "requested":
            assert user not in pending
            if user in clearing:
                case = clearing.pop(user)
                assert case["clear"]["tx"] == row["tx"]
                assert case["initial"]["proxy"] == row["proxy"]
                case["retry"] = row
                cases.append(case)
            pending[user] = row
        elif kind == "cleared":
            initial = pending.pop(user)
            assert initial["proxy"] == row["proxy"]
            clearing[user] = {"initial": initial, "clear": row}
        else:
            request = pending.pop(user)
            assert (
                row["credit_raw"]
                == (request["spot_raw"] + 100 * request["perp_raw"]) * 10**10
            )
            for case in cases:
                if case.get("retry") is request:
                    case["swept"] = row
    assert not pending and not clearing and len(cases) == 2
    for case in cases:
        initial, retry, swept = case["initial"], case["retry"], case["swept"]
        assert initial["perp_raw"] == 500_000 and retry["perp_raw"] == 0
        assert initial["spot_raw"] + 100 * initial["perp_raw"] == (
            retry["spot_raw"] + SPOT_UNIT
        )
        assert swept["credit_raw"] == retry["spot_raw"] * 10**10
        assert initial["block"] > int(saved(UPGRADE)["transition_block"]["number"], 16)
    return cases


def evm_capture(url, case):
    transactions = {}
    for name in ("initial", "retry", "swept"):
        item = case[name]
        tx = item["tx"]
        transactions[name] = {
            "receipt": rpc(url, "eth_getTransactionReceipt", [tx]),
            "trace": rpc(
                url,
                "debug_traceTransaction",
                [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}],
            ),
        }
        if name == "swept":
            transactions[name]["state_diff"] = rpc(
                url,
                "debug_traceTransaction",
                [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}],
            )
    retry_block = case["retry"]["block"]
    transactions["archive_state"] = {
        "implementation_word": rpc(
            url, "eth_getStorageAt", [PROXY, IMPLEMENTATION_SLOT, hex(retry_block)]
        ),
        "implementation_code": rpc(url, "eth_getCode", [REPLACEMENT, hex(retry_block)]),
        "proxy_code": rpc(
            url, "eth_getCode", [case["retry"]["proxy"], hex(retry_block)]
        ),
        "helper_code": rpc(url, "eth_getCode", [TOPUP_HELPER, hex(retry_block)])
        if case["retry"]["proxy"] == HELPED_PROXY
        else None,
    }
    return transactions


def core_capture(case, row):
    ledger = row["through_pin_ledger"]
    conversion = [
        entry for entry in ledger if entry["delta"]["type"] == "accountClassTransfer"
    ]
    assert len(conversion) == 1
    converted = post_json(
        EXPLORER, {"type": "txDetails", "hash": conversion[0]["hash"]}
    )
    block = post_json(
        EXPLORER, {"type": "blockDetails", "height": converted["tx"]["block"]}
    )
    initial_amount = case["initial"]["spot_raw"] + 100 * case["initial"]["perp_raw"]
    failed = [
        tx
        for tx in block["blockDetails"]["txs"]
        if tx["user"].lower() == row["proxy"]
        and tx["action"]
        == {
            "type": "SystemSpotSendAction",
            "destination": PROXY,
            "token": 0,
            "wei": initial_amount,
        }
    ]
    assert len(failed) == 1
    outgoing = [
        entry
        for entry in ledger
        if entry["delta"]["type"] == "spotTransfer"
        and entry["delta"]["user"].lower() == row["proxy"]
        and raw(entry["delta"]["amount"]) == case["retry"]["spot_raw"]
    ]
    assert len(outgoing) == 1
    delivered = post_json(EXPLORER, {"type": "txDetails", "hash": outgoing[0]["hash"]})
    topup = [
        entry
        for entry in ledger
        if entry["delta"]["type"] == "spotTransfer"
        and entry["delta"]["user"].lower() == TOPUP_HELPER
        and entry["delta"]["destination"].lower() == row["proxy"]
        and raw(entry["delta"]["amount"]) == SPOT_UNIT
    ]
    assert len(topup) == (1 if row["proxy"] == HELPED_PROXY else 0)
    return {
        "conversion": converted,
        "execution_block": block,
        "topup_send": post_json(
            EXPLORER, {"type": "txDetails", "hash": topup[0]["hash"]}
        )
        if topup
        else None,
        "failed_send": post_json(
            EXPLORER, {"type": "txDetails", "hash": failed[0]["hash"]}
        ),
        "delivered_send": delivered,
    }


def writer_action(frame):
    action = action_bytes(frame["input"])
    prefix = action[0:8]
    body = words("0x" + action[8:])
    if prefix == "01000007":
        assert len(body) == 2 and body[1] == 0
        return {"kind": 7, "amount": body[0]}
    assert prefix == "01000006" and len(body) == 3
    assert body[1] == 0
    return {
        "kind": 6,
        "destination": "0x" + body[0].to_bytes(20, "big").hex(),
        "amount": body[2],
    }


def state_delta(diff, address, slot):
    key = "0x" + slot.to_bytes(32, "big").hex()
    before = int(diff["pre"].get(address, {}).get("storage", {}).get(key, "0x0"), 16)
    after = int(diff["post"].get(address, {}).get("storage", {}).get(key, "0x0"), 16)
    return before, after


def verify_payload(payload, events, ledger, scope, manifest):
    assert payload["pin"] == events["pin"] == scope["pin"] == manifest["block"] == PIN
    assert (
        payload["block_hash"]
        == events["block_hash"]
        == scope["block_hash"]
        == manifest["block_hash"]
    )
    cases = sweep_logs(events)
    assert len(payload["cases"]) == len(cases) == 2
    proxy_rows = {row["proxy"]: row for row in ledger["groups"][1]["rows"]}
    deployed = {
        "0x" + event["log"]["topics"][2][-40:].lower(): event["runtime"]
        for event in scope["earlier_factory_deployments"][1]["events"]
    }
    replacement_code = next(
        row["runtime"] for row in scope["rows"] if row["address"] == REPLACEMENT
    )
    assert TOPUP_HELPER not in {row["address"] for row in scope["rows"]}
    results = []
    for case, captured in zip(cases, payload["cases"], strict=True):
        assert captured["proxy"] == case["retry"]["proxy"]
        proxy = captured["proxy"]
        row = proxy_rows[proxy]
        assert row["user"] == case["retry"]["user"]
        archive = captured["evm"]["archive_state"]
        assert archive["implementation_word"][-40:].lower() == REPLACEMENT[2:]
        assert archive["implementation_code"] == replacement_code
        assert archive["proxy_code"] == deployed[proxy]
        if proxy == HELPED_PROXY:
            assert (
                archive["helper_code"].startswith("0x")
                and len(archive["helper_code"]) > 2
            )
        else:
            assert archive["helper_code"] is None
        for name in ("initial", "retry", "swept"):
            item, tx = case[name], captured["evm"][name]
            receipt, trace = tx["receipt"], tx["trace"]
            assert receipt["transactionHash"].lower() == item["tx"]
            assert receipt["blockHash"].lower() == item["block_hash"]
            assert int(receipt["status"], 16) == 1
            assert not trace.get("error")
            if name == "retry" and proxy == HELPED_PROXY:
                assert trace["to"].lower() == TOPUP_HELPER
                direct = trace.get("calls", [])
                helper_writer = [
                    index
                    for index, frame in enumerate(direct)
                    if frame.get("to", "").lower() == WRITER
                ]
                exchange_calls = [
                    index
                    for index, frame in enumerate(direct)
                    if frame.get("to", "").lower() == PROXY
                    and frame.get("input", "").startswith("0x01681a62")
                ]
                assert (
                    len(helper_writer) == len(exchange_calls) == 1
                    and helper_writer[0] < exchange_calls[0]
                )
                assert writer_action(direct[helper_writer[0]]) == {
                    "kind": 6,
                    "destination": proxy,
                    "amount": SPOT_UNIT,
                }
            else:
                assert trace["to"].lower() == PROXY
            assert any(
                log["address"].lower() == PROXY
                and log["topics"][0].lower() == TOPICS[item["kind"]]
                and int(log["logIndex"], 16) == item["index"]
                for log in receipt["logs"]
            )
            if name == "swept":
                continue
            selector = (
                "0xe0189108"
                if name == "initial"
                else "0x01681a62"
                if proxy == HELPED_PROXY
                else "0x6d142da1"
            )
            implementation = [
                frame
                for frame in children(trace)
                if frame.get("type") == "DELEGATECALL"
                and frame.get("to", "").lower() == REPLACEMENT
                and frame.get("input", "").startswith(selector)
            ]
            assert len(implementation) == 1
            proxy_calls = [
                frame
                for frame in children(implementation[0])
                if frame.get("to", "").lower() == proxy
                and frame.get("input", "").startswith("0x925b3aad")
            ]
            assert len(proxy_calls) == 1
            assert words("0x" + proxy_calls[0]["input"][10:]) == [
                0,
                item["spot_raw"],
                item["perp_raw"],
            ]
            actions = [
                writer_action(frame)
                for frame in children(proxy_calls[0])
                if frame.get("to", "").lower() == WRITER
            ]
            if name == "initial":
                assert actions == [
                    {"kind": 7, "amount": item["perp_raw"]},
                    {
                        "kind": 6,
                        "destination": PROXY,
                        "amount": item["spot_raw"] + 100 * item["perp_raw"],
                    },
                ]
            else:
                assert actions == [
                    {"kind": 6, "destination": PROXY, "amount": item["spot_raw"]}
                ]
        core = captured["core"]
        failed, delivered = core["failed_send"]["tx"], core["delivered_send"]["tx"]
        conversion = core["conversion"]["tx"]
        assert conversion["error"] is None
        assert conversion["user"].lower() == proxy
        assert conversion["action"] == {
            "type": "SystemUsdClassTransferAction",
            "ntl": 500_000,
            "toPerp": False,
        }
        block = core["execution_block"]["blockDetails"]
        assert block["height"] == conversion["block"] == failed["block"]
        assert any(tx["hash"] == failed["hash"] for tx in block["txs"])
        assert failed["user"].lower() == delivered["user"].lower() == proxy
        assert failed["error"] == ERROR and delivered["error"] is None
        assert failed["action"] == {
            "type": "SystemSpotSendAction",
            "destination": PROXY,
            "token": 0,
            "wei": case["initial"]["spot_raw"] + 100 * case["initial"]["perp_raw"],
        }
        assert delivered["action"] == {
            "type": "SystemSpotSendAction",
            "destination": PROXY,
            "token": 0,
            "wei": case["retry"]["spot_raw"],
        }
        outgoing = [
            entry
            for entry in row["through_pin_ledger"]
            if entry["hash"] == delivered["hash"]
        ]
        assert len(outgoing) == 1
        assert raw(outgoing[0]["delta"]["fee"]) == SPOT_UNIT
        assert raw(outgoing[0]["delta"]["amount"]) == case["retry"]["spot_raw"]
        topup = core["topup_send"]
        if proxy == HELPED_PROXY:
            assert topup["tx"]["error"] is None
            assert topup["tx"]["block"] == delivered["block"]
            assert topup["tx"]["action"] == {
                "type": "SystemSpotSendAction",
                "destination": proxy,
                "token": 0,
                "wei": SPOT_UNIT,
            }
            assert any(
                entry["hash"] == topup["tx"]["hash"]
                for entry in row["through_pin_ledger"]
            )
        else:
            assert topup is None
        diff = captured["evm"]["swept"]["state_diff"]
        keccak = Keccak()
        user_slot = int(mapping_slot(case["retry"]["user"], 9, keccak), 16)
        pending_slot = int(mapping_slot(case["retry"]["user"], 33, keccak), 16)
        credit = case["swept"]["credit_raw"]
        user_before, user_after = state_delta(diff, PROXY, user_slot)
        treasury_before, treasury_after = state_delta(diff, PROXY, 14)
        packed_before, packed_after = state_delta(diff, PROXY, 22)
        pending_before, pending_after = state_delta(diff, PROXY, pending_slot)
        assert user_after - user_before == treasury_after - treasury_before == credit
        assert (packed_after & ((1 << 128) - 1)) - (
            packed_before & ((1 << 128) - 1)
        ) == credit
        assert (packed_after >> 128) == (packed_before >> 128)
        assert pending_before != 0 and pending_after == 0
        residual = sum(
            spot_delta(proxy, entry, PROXY) for entry in row["through_pin_ledger"]
        )
        assert residual == (SPOT_UNIT if proxy == HELPED_PROXY else 0)
        results.append(
            {
                "proxy": proxy,
                "helper_topup_raw_spot": SPOT_UNIT if proxy == HELPED_PROXY else 0,
                "pinned_residual_raw_spot": residual,
                "first_request_block": case["initial"]["block"],
                "retry_block": case["retry"]["block"],
                "delivered_raw_spot": case["retry"]["spot_raw"],
                "fee_raw_spot": SPOT_UNIT,
                "credited_internal": credit,
            }
        )
    assert [row["delivered_raw_spot"] for row in results] == [
        1_050_000_000,
        950_000_000,
    ]
    return results


def capture():
    events, ledger, scope = saved(EVENTS[1]), saved(CORE_LEDGER), saved(SCOPE)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert (
        events["block_hash"]
        == ledger["block_hash"]
        == scope["block_hash"]
        == manifest["block_hash"]
    )
    proxy_rows = {row["proxy"]: row for row in ledger["groups"][1]["rows"]}
    cases = []
    for case in sweep_logs(events):
        proxy = case["retry"]["proxy"]
        cases.append(
            {
                "proxy": proxy,
                "evm": evm_capture(os.environ["PAPERTRADE_ARCHIVE_RPC"], case),
                "core": core_capture(case, proxy_rows[proxy]),
            }
        )
    payload = {"pin": PIN, "block_hash": manifest["block_hash"], "cases": cases}
    summary = verify_payload(payload, events, ledger, scope, manifest)
    OUT.write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return summary


def verify():
    return verify_payload(
        saved(OUT),
        saved(EVENTS[1]),
        saved(CORE_LEDGER),
        saved(SCOPE),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), sort_keys=True))


if __name__ == "__main__":
    main()
