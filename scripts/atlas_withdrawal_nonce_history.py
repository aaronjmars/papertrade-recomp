"""Check saved signed withdrawal nonce bits at the surrounding blocks and pin."""

import argparse
import json
import os
import pathlib
import urllib.request

from atlas_factory_events import Keccak
from atlas_session_keys import PROXY, nested_slot

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SOURCE = ATLAS / "exchange_withdrawal_signature_behavior.json"
OUT = ATLAS / "withdrawal_nonce_history.json"
PIN = 48902346


def rpc(url, payload):
    request = urllib.request.Request(
        url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def inputs():
    source = json.loads(SOURCE.read_text())
    assert source["pin"] == PIN and source["matched_call_count"] == 103
    keccak = Keccak()
    rows = []
    for call in source["calls"]:
        nonce = int(call["nonce"])
        block = call["block"]
        assert 0 < block <= PIN
        rows.append(
            {
                "tx": call["tx"],
                "block": block,
                "user": call["user"],
                "nonce": call["nonce"],
                "slot": nested_slot(int(call["user"], 16), nonce >> 8, 6, keccak),
                "bit": nonce & 255,
                "evidence_tier": call["evidence_tier"],
            }
        )
    assert len({(row["user"], row["nonce"]) for row in rows}) == len(rows)
    return source, rows


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    source, rows = inputs()
    header = rpc(
        url,
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "eth_getBlockByNumber",
            "params": [hex(PIN), False],
        },
    )
    assert header["result"]["hash"].lower() == source["block_hash"]
    lookups = sorted(
        {
            (block, row["slot"])
            for row in rows
            for block in (row["block"] - 1, row["block"], PIN)
        }
    )
    answers = {}
    for start in range(0, len(lookups), 30):
        group = lookups[start : start + 30]
        request = [
            {
                "jsonrpc": "2.0",
                "id": start + index,
                "method": "eth_getStorageAt",
                "params": [PROXY, slot, hex(block)],
            }
            for index, (block, slot) in enumerate(group)
        ]
        response = rpc(url, request)
        assert isinstance(response, list) and len(response) == len(group)
        by_id = {entry["id"]: entry for entry in response}
        assert set(by_id) == {entry["id"] for entry in request}
        for index, lookup in enumerate(group):
            answer = by_id[start + index]
            assert "error" not in answer, (lookup, answer.get("error"))
            answers[lookup] = answer["result"]
        print(
            f"storage reads: {min(start + 30, len(lookups))}/{len(lookups)}", flush=True
        )
    for row in rows:
        row["before_word"] = answers[row["block"] - 1, row["slot"]]
        row["after_word"] = answers[row["block"], row["slot"]]
        row["pin_word"] = answers[PIN, row["slot"]]
    result = {
        "pin": PIN,
        "block_hash": source["block_hash"],
        "session_key_manager_proxy": PROXY,
        "withdrawal_count": len(rows),
        "distinct_transaction_count": source["distinct_transaction_count"],
        "read_count": len(lookups),
        "rows": rows,
        "limits": [
            "Storage is sampled at block boundaries, not at each transaction index within a block.",
            "This checks 103 selected historical withdrawals, not every withdrawal or failed attempt.",
            "A set nonce bit proves commitment by the end of its block; it does not establish HyperCore delivery.",
        ],
    }
    check(result)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"{len(rows)} withdrawal nonce bits persisted through the pin")


def check(result):
    source, expected = inputs()
    assert result["pin"] == PIN and result["block_hash"] == source["block_hash"]
    assert result["session_key_manager_proxy"] == PROXY
    assert result["withdrawal_count"] == len(expected) == 103
    assert result["distinct_transaction_count"] == source["distinct_transaction_count"]
    assert result["read_count"] >= len(expected) * 2
    assert len(result["rows"]) == len(expected)
    for row, want in zip(result["rows"], expected):
        assert all(row[field] == want[field] for field in want)
        mask = 1 << row["bit"]
        assert not int(row["before_word"], 16) & mask, row["tx"]
        assert int(row["after_word"], 16) & mask, row["tx"]
        assert int(row["pin_word"], 16) & mask, row["tx"]


def verify():
    result = json.loads(OUT.read_text())
    check(result)
    print(
        f"{result['withdrawal_count']} saved withdrawal nonce bits persisted through the pin"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    capture() if args.capture else verify()
