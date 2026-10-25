"""Check historical open and close nonce commitment on deployed SessionKeyManager storage."""

import argparse
import collections
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_session_keys import PROXY, calldata_words, nested_slot
from atlas_session_open_typehash import descendants, open_calls
from atlas_withdrawal_nonce_history import PIN, rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "trading_nonce_history"
OUT = ATLAS / "trading_nonce_history.json"


def sources():
    opens = json.loads((ATLAS / "session_open_typehash_behavior.json").read_text())
    closes = json.loads((ATLAS / "session_close_typehash_behavior.json").read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert opens["pin"] == closes["pin"] == manifest["block"] == PIN
    assert opens["block_hash"] == closes["block_hash"] == manifest["block_hash"]
    assert opens["open_call_count"] == 58 and closes["matched_close_call_count"] == 43
    rows = []
    trace_calls = {}
    for kind, calls in (("open", opens["calls"]), ("close", closes["calls"])):
        for call in calls:
            nonce_result = None
            if kind == "open":
                tx = call["tx"]
                if tx not in trace_calls:
                    trace_calls[tx] = open_calls(
                        json.loads((ROOT / call["source"]).read_text())
                    )
                source_call = trace_calls[tx][call["call_index"]]
                nonce_calls = [
                    child
                    for child in descendants(source_call)
                    if child.get("to", "").lower() == PROXY
                    and child.get("input", "")[:10] == "0xb002b9fa"
                ]
                assert len(nonce_calls) == 1
                nonce_call = nonce_calls[0]
                assert nonce_call["type"] == "CALL"
                assert calldata_words(nonce_call["input"]) == [
                    int(call["user"], 16),
                    int(call["nonce"]),
                    call["deadline"],
                ]
                nonce_result = "reverted" if nonce_call.get("error") else "returned"
                assert (nonce_result == "reverted") == (call["result"] == "0xf87d9271")
            rows.append(
                {
                    "kind": kind,
                    "tx": call["tx"],
                    "user": call["user"],
                    "nonce": call["nonce"],
                    "result": call["result"] if kind == "open" else "success",
                    "nonce_call_result": nonce_result,
                }
            )
    assert len(rows) == 101
    assert len({(row["user"].lower(), row["nonce"]) for row in rows}) == len(rows)
    return manifest, closes, rows


def receipt_path(tx):
    saved = list((ROOT / "artifacts").glob(f"**/{tx}.receipt.json"))
    assert len(saved) <= 1, tx
    return saved[0] if saved else ARTIFACTS / f"{tx}.receipt.json"


def load_receipts(rows, url=None):
    receipts = {}
    for tx in sorted({row["tx"] for row in rows}):
        path = receipt_path(tx)
        if not path.exists():
            assert url is not None, tx
            reply = rpc(
                url,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getTransactionReceipt",
                    "params": [tx],
                },
            )
            assert "error" not in reply and reply["result"] is not None, tx
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(reply["result"], indent=2) + "\n")
        receipt = json.loads(path.read_text())
        assert receipt["transactionHash"].lower() == tx.lower()
        assert int(receipt["status"], 16) == 1
        receipts[tx] = (int(receipt["blockNumber"], 16), str(path.relative_to(ROOT)))
    return receipts


def expected_rows(receipts):
    _, closes, rows = sources()
    close_blocks = {
        (row["tx"], row["user"], row["nonce"]): row["block"] for row in closes["calls"]
    }
    keccak = Keccak()
    for row in rows:
        block, path = receipts[row["tx"]]
        assert 0 < block <= PIN
        if row["kind"] == "close":
            assert block == close_blocks[row["tx"], row["user"], row["nonce"]]
        nonce = int(row["nonce"])
        row.update(
            {
                "block": block,
                "receipt": path,
                "slot": nested_slot(int(row["user"], 16), nonce >> 8, 6, keccak),
                "bit": nonce & 255,
            }
        )
    return rows


def check(result):
    manifest, _, _ = sources()
    assert result["pin"] == PIN and result["block_hash"] == manifest["block_hash"]
    assert result["session_key_manager_proxy"] == PROXY
    assert result["call_count"] == 101
    assert (
        result["transaction_count"] == len({row["tx"] for row in result["rows"]}) == 34
    )
    expected = expected_rows(load_receipts(result["rows"]))
    assert len(result["rows"]) == len(expected)
    assert result["storage_read_count"] == len(
        {
            (block, row["slot"])
            for row in expected
            for block in (row["block"] - 1, row["block"], PIN)
        }
    )
    counts = collections.Counter()
    for row, want in zip(result["rows"], expected):
        assert all(row[key] == want[key] for key in want)
        mask = 1 << row["bit"]
        before = bool(int(row["before_word"], 16) & mask)
        after = bool(int(row["after_word"], 16) & mask)
        pin = bool(int(row["pin_word"], 16) & mask)
        assert not before, row["tx"]
        assert after == (row["result"] == "success"), row["tx"]
        if after:
            assert pin, row["tx"]
        else:
            assert not pin, row["tx"]
        counts[row["kind"], row["result"], after] += 1
    assert counts["close", "success", True] == 43
    assert counts["open", "success", True] == 30
    assert counts["open", "0x40f92143", False] == 27
    assert counts["open", "0xf87d9271", False] == 1
    assert result["outcome_counts"] == {
        "close_success_committed": 43,
        "open_success_committed": 30,
        "open_rejected_rolled_back": 28,
    }


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest, _, base_rows = sources()
    header = rpc(
        url,
        {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "eth_getBlockByNumber",
            "params": [hex(PIN), False],
        },
    )
    assert header["result"]["hash"].lower() == manifest["block_hash"]
    rows = expected_rows(load_receipts(base_rows, url))
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
        "block_hash": manifest["block_hash"],
        "session_key_manager_proxy": PROXY,
        "call_count": len(rows),
        "transaction_count": len({row["tx"] for row in rows}),
        "storage_read_count": len(lookups),
        "outcome_counts": {
            "close_success_committed": 43,
            "open_success_committed": 30,
            "open_rejected_rolled_back": 28,
        },
        "rows": rows,
        "limits": [
            "Storage is sampled at block boundaries, not at each transaction index within a block.",
            "The open and close calls are saved samples, not every historical signed intent.",
            "A failed call's unset bit at block end does not alone identify which internal branch rejected it.",
        ],
    }
    check(result)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("73 successful trade nonce bits committed; 28 rejected open bits rolled back")


def verify():
    result = json.loads(OUT.read_text())
    check(result)
    print("73 successful trade nonce bits committed; 28 rejected open bits rolled back")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    capture() if args.capture else verify()
