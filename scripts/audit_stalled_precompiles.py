#!/usr/bin/env python3
"""Show that the public HyperEVM RPC does not serve archived state for PT-01."""

import argparse
import datetime
import gzip
import json
import pathlib
import urllib.request

from atlas_deployer_scope import PIN
from atlas_older_positions import saved

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
STALLED = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
FACTORY = ATLAS / "factory_user_proxy_map.json"
OUT = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_precompiles.json.gz"
RPC = "https://rpc.hyperliquid.xyz/evm"
SPOT_BALANCE = "0x0000000000000000000000000000000000000801"
CORE_USER_EXISTS = "0x0000000000000000000000000000000000000810"
EXPECTED_SPOT = (5_005_091_600, 1_210_000_000)


def rpc(method, params):
    request = urllib.request.Request(
        RPC,
        json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        ).encode(),
        {"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        reply = json.load(response)
    assert "error" not in reply, reply
    return reply["result"]


def call(address, target, block, token=False):
    data = "0x" + int(address, 16).to_bytes(32, "big").hex()
    if token:
        data += (0).to_bytes(32, "big").hex()
    return rpc(
        "eth_call", [{"to": target, "gas": "0x989680", "data": data}, hex(block)]
    )


def output_words(value, count):
    assert value.startswith("0x") and len(value) == 2 + count * 64
    return [
        int(value[2 + index * 64 : 2 + (index + 1) * 64], 16) for index in range(count)
    ]


def capture():
    stalled = saved(STALLED)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert stalled["pin"] == manifest["block"] == PIN
    records = []
    for set_index, case in enumerate(stalled["cases"]):
        for block in (1, PIN):
            records.append(
                {
                    "set": set_index,
                    "proxy": case["proxy"],
                    "block": block,
                    "block_hash": rpc("eth_getBlockByNumber", [hex(block), False])[
                        "hash"
                    ],
                    "evm_code": rpc("eth_getCode", [case["proxy"], hex(block)]),
                    "core_user_exists": call(case["proxy"], CORE_USER_EXISTS, block),
                    "spot_balance": call(
                        case["proxy"], SPOT_BALANCE, block, token=True
                    ),
                }
            )
    payload = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "source": RPC,
        "records": records,
    }
    result = verify_payload(payload, stalled, manifest)
    OUT.write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), mtime=0)
    )
    return result


def verify_payload(payload, stalled, manifest):
    assert payload["pin"] == stalled["pin"] == manifest["block"] == PIN
    assert payload["block_hash"] == stalled["block_hash"] == manifest["block_hash"]
    assert payload["source"] == RPC and len(payload["records"]) == 4
    created = {row["proxy"]: row for row in json.loads(FACTORY.read_text())}
    results = []
    for set_index, case in enumerate(stalled["cases"]):
        factory_row = created[case["proxy"]]
        assert factory_row["user"] == case["user"]
        assert 1 < factory_row["block"] < int(case["first_header"]["number"], 16)
        early, pin = payload["records"][set_index * 2 : set_index * 2 + 2]
        for row, block in ((early, 1), (pin, PIN)):
            assert (row["set"], row["proxy"], row["block"]) == (
                set_index,
                case["proxy"],
                block,
            )
            assert output_words(row["core_user_exists"], 1) == [1]
            assert output_words(row["spot_balance"], 3) == [
                EXPECTED_SPOT[set_index],
                0,
                0,
            ]
            assert row["evm_code"].startswith("0x") and len(row["evm_code"]) > 2
        assert early["block_hash"] != pin["block_hash"]
        assert pin["block_hash"].lower() == manifest["block_hash"].lower()
        assert early["evm_code"] == pin["evm_code"]
        assert early["core_user_exists"] == pin["core_user_exists"]
        assert early["spot_balance"] == pin["spot_balance"]
        assert (
            int(case["pending_word"], 16) & ((1 << 64) - 1) == EXPECTED_SPOT[set_index]
        )
        results.append(
            {
                "proxy": case["proxy"],
                "pre_creation_block": 1,
                "creation_block": factory_row["block"],
                "spot_raw": EXPECTED_SPOT[set_index],
            }
        )
    return results


def verify():
    return verify_payload(
        saved(OUT),
        saved(STALLED),
        json.loads((ATLAS / "manifest.json").read_text()),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), sort_keys=True))


if __name__ == "__main__":
    main()
