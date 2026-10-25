#!/usr/bin/env python3
"""Check every saved signed-open side-cap comparison in historical opcode traces."""

import concurrent.futures
import json
import sys
from collections import defaultdict
from pathlib import Path

from atlas_exchange_market_fields import mapping_slot
from atlas_factory_events import Keccak
from trace import rpc


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
RAW = ROOT / "artifacts" / "exchange_open_limit_all_traces.json"
ERROR_LOOKUP = ROOT / "artifacts" / "openchain_error_40f92143.json"
OUT = ATLAS / "exchange_open_limit_full_behavior.json"
COMPARE = {0xA44: (True, 0xA1A, 0xA35), 0xEDC: (False, 0xEB8, 0xED5)}
ERROR_SIGNATURE = "OiCapExceeded()"
ERROR_SELECTOR = "0x40f92143"


def read(path):
    return json.loads(path.read_text())


def find_prior(logs, at, pc, depth):
    for index in range(at - 1, max(-1, at - 100), -1):
        row = logs[index]
        if row["depth"] == depth and row["pc"] == pc and row["op"] == "SLOAD":
            return row
    return None


def capture_one(tx, instruments):
    trace = rpc("debug_traceTransaction", [tx, {"disableMemory": True,
                                               "disableStorage": True,
                                               "enableReturnData": False}])
    logs = trace["structLogs"]
    keys = {mapping_slot(instrument): instrument for instrument in instruments}
    comparisons = []
    for index, row in enumerate(logs):
        if row["pc"] not in COMPARE or row["op"] != "GT":
            continue
        is_long, base_pc, cap_pc = COMPARE[row["pc"]]
        base = find_prior(logs, index, base_pc, row["depth"])
        cap = find_prior(logs, index, cap_pc, row["depth"])
        if not base or not cap:
            continue
        base_key = int(base["stack"][-1], 16)
        if base_key not in keys or int(cap["stack"][-1], 16) != base_key + 1:
            continue
        updated, limit = (int(word, 16) for word in row["stack"][-1:-3:-1])
        jump_index = next((k for k in range(index + 1, min(index + 5, len(logs)))
                           if logs[k]["depth"] == row["depth"] and logs[k]["op"] == "JUMPI"), None)
        assert jump_index is not None
        jump = logs[jump_index]
        assert int(jump["stack"][-1], 16) == 0xEA4
        assert int(jump["stack"][-2], 16) == int(updated > limit)
        assert logs[jump_index + 1]["pc"] == (0xEA4 if updated > limit else jump["pc"] + 1)
        comparisons.append({"step": index, "depth": row["depth"],
                            "base_sload": {"pc": hex(base["pc"]), "op": base["op"],
                                           "stack_top": base["stack"][-1]},
                            "limit_sload": {"pc": hex(cap["pc"]), "op": cap["op"],
                                            "stack_top": cap["stack"][-1]},
                            "comparison": {"pc": hex(row["pc"]), "op": row["op"],
                                           "stack_top_two": row["stack"][-2:]},
                            "jump": {"pc": hex(jump["pc"]), "op": jump["op"],
                                     "stack_top_two": jump["stack"][-2:],
                                     "next_pc": hex(logs[jump_index + 1]["pc"])}})
    return {"tx": tx, "struct_log_count": len(logs), "comparisons": comparisons}


def capture():
    signed = read(ATLAS / "session_open_typehash_behavior.json")
    by_tx = defaultdict(list)
    for call in signed["calls"]:
        by_tx[call["tx"]].append(call)
    existing = read(RAW) if RAW.exists() else {"schema_version": 2, "transactions": {}}
    if existing.get("schema_version") != 2:
        existing = {"schema_version": 2, "transactions": {}}
    pending = {tx: {call["instrument_id"] for call in calls}
               for tx, calls in by_tx.items() if tx not in existing["transactions"]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(capture_one, tx, instruments): tx for tx, instruments in pending.items()}
        for done in concurrent.futures.as_completed(jobs):
            tx = jobs[done]
            row = done.result()
            existing["transactions"][tx] = row
            RAW.write_text(json.dumps(existing, indent=2) + "\n")
            print(tx, len(row["comparisons"]), "comparisons", flush=True)
    assert set(existing["transactions"]) == set(by_tx)
    return existing


def build():
    signed = read(ATLAS / "session_open_typehash_behavior.json")
    saved = read(RAW)
    lookup = read(ERROR_LOOKUP)
    assert lookup["response"]["ok"]
    names = [row["name"] for row in lookup["response"]["result"]["function"][ERROR_SELECTOR]]
    assert names == [ERROR_SIGNATURE]
    assert "0x" + Keccak()(ERROR_SIGNATURE.encode())[:4].hex() == ERROR_SELECTOR
    assert saved["schema_version"] == 2
    by_tx = defaultdict(list)
    for call in signed["calls"]:
        by_tx[call["tx"]].append(call)
    assert set(saved["transactions"]) == set(by_tx)
    matched = []
    for tx, calls in sorted(by_tx.items()):
        transaction_path = ROOT / calls[0]["source"].replace(".calls.json", ".tx.json")
        if not transaction_path.exists():
            transaction_path = ROOT / calls[0]["source"].replace(".calls.json", ".receipt.json")
        transaction = read(transaction_path)
        block_number = int(transaction["blockNumber"], 16)
        assert transaction.get("hash", transaction.get("transactionHash")) == tx
        assert block_number <= signed["pin"]
        expected = [call for call in calls if call["session_signer_reached"]]
        transaction_trace = saved["transactions"][tx]
        assert transaction_trace["tx"] == tx
        comparisons = transaction_trace["comparisons"]
        assert len(comparisons) == len(expected), (tx, len(comparisons), len(expected))
        assert all(left["step"] < right["step"] for left, right in zip(comparisons, comparisons[1:]))
        assert all(row["step"] < transaction_trace["struct_log_count"] for row in comparisons)
        for call, raw in zip(expected, comparisons):
            is_long = call["is_long"]
            base_pc = "0xa1a" if is_long else "0xeb8"
            limit_pc = "0xa35" if is_long else "0xed5"
            comparison_pc = "0xa44" if is_long else "0xedc"
            base_slot = mapping_slot(call["instrument_id"])
            assert raw["base_sload"] == {"pc": base_pc, "op": "SLOAD",
                                          "stack_top": f"0x{base_slot:x}"}
            assert raw["limit_sload"] == {"pc": limit_pc, "op": "SLOAD",
                                           "stack_top": f"0x{base_slot + 1:x}"}
            gt = raw["comparison"]
            assert gt["pc"] == comparison_pc and gt["op"] == "GT"
            assert len(gt["stack_top_two"]) == 2
            limit, updated = (int(word, 16) for word in gt["stack_top_two"])
            jump = raw["jump"]
            assert jump["pc"] == ("0xa48" if is_long else "0xee0")
            assert jump["op"] == "JUMPI" and len(jump["stack_top_two"]) == 2
            assert int(jump["stack_top_two"][-1], 16) == 0xea4
            assert int(jump["stack_top_two"][-2], 16) == int(updated > limit)
            assert jump["next_pc"] == ("0xea4" if updated > limit else hex(int(jump["pc"], 16) + 1))
            assert (updated > limit) == (call["result"] == ERROR_SELECTOR)
            assert call["result"] in ("success", ERROR_SELECTOR)
            matched.append({"tx": tx, "block_number": block_number,
                            "call_index": call["call_index"], "result": call["result"],
                            "step": raw["step"], "depth": raw["depth"],
                            "instrument_id": call["instrument_id"], "is_long": is_long,
                            "base_slot": f"0x{base_slot:064x}",
                            "updated_exposure": str(updated), "limit": str(limit),
                            "exceeds_limit": updated > limit,
                            "comparison_pc": comparison_pc, "jump_pc": jump["pc"]})
    assert len(matched) == signed["session_signer_call_count"]
    result = {"pin": signed["pin"], "block_hash": signed["block_hash"],
              "selector": signed["open_selector"], "raw_error": ERROR_SELECTOR,
              "error_signature": ERROR_SIGNATURE,
              "error_signature_source": "artifacts/openchain_error_40f92143.json",
              "error_signature_lookup_url": lookup["url"],
              "error_signature_hash_verified": True,
              "transaction_count": len(by_tx), "matched_signed_open_count": len(matched),
              "cap_revert_count": sum(row["exceeds_limit"] for row in matched),
              "below_limit_success_count": sum(not row["exceeds_limit"] for row in matched),
              "deadline_failure_before_comparison_count": signed["open_call_count"] - len(matched),
              "calls": matched,
              "limits": ["Saved call traces cover sampled historical transactions, not all on-chain opens.",
                         "The error name is a hash-verified public registry match, not verified contract source; storage field source names remain unknown.",
                         "The comparison establishes a limit guard; other state checks and exact units are unresolved."]}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    if "--capture" in sys.argv:
        capture()
    result = build()
    print(result["matched_signed_open_count"], "signed opens,",
          result["cap_revert_count"], "cap reverts,",
          result["below_limit_success_count"], "successes")
