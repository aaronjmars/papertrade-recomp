#!/usr/bin/env python3
"""Verify the Exchange signed-open side limits from saved historical opcodes."""

import json
from pathlib import Path

from atlas_exchange_market_fields import mapping_slot


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts"
OUT = ATLAS / "exchange_open_limit_behavior.json"
SAMPLES = (
    ("long_failure", "exchange_open_limit_opcode_trace.json", True, False),
    ("long_success", "exchange_open_limit_success_opcode_trace.json", True, True),
    ("short_failure", "exchange_open_limit_short_failure_opcode_trace.json", False, False),
)


def find(rows, pc, start=0):
    return next(row for row in rows if row["index"] >= start and row["pc"] == pc)


def stack(row, offset):
    return int(row["stack"][offset], 16)


def build():
    signed = json.loads((ATLAS / "session_open_typehash_behavior.json").read_text())
    slot = mapping_slot(0)
    samples = []
    for label, filename, is_long, succeeds in SAMPLES:
        saved = json.loads((ARTIFACTS / filename).read_text())
        assert saved["steps"] > 3000
        matching = [call for call in signed["calls"] if call["tx"] == saved["tx"]
                    and call["instrument_id"] == 0 and call["is_long"] == is_long
                    and (call["result"] == "success") == succeeds]
        assert matching
        rows = saved["rows"]
        base_pc = "0xa1a" if is_long else "0xeb8"
        base_read = next(row for row in rows if row["pc"] == base_pc
                         and row["op"] == "SLOAD" and stack(row, -1) == slot)
        cap_pc = "0xa34" if label == "long_success" else ("0xa35" if is_long else "0xed5")
        cap_read = find(rows, cap_pc, base_read["index"])
        comparison = find(rows, "0xa44" if is_long else "0xedc", cap_read["index"])
        assert base_read["depth"] == cap_read["depth"] == comparison["depth"] == 4
        assert stack(base_read, -1) == slot
        if cap_pc == "0xa34":
            assert cap_read["op"] == "ADD" and stack(cap_read, -1) == slot
            assert stack(cap_read, -2) == 1
        else:
            assert cap_read["op"] == "SLOAD" and stack(cap_read, -1) == slot + 1
        assert comparison["op"] == "GT"
        updated = stack(comparison, -1)
        cap = stack(comparison, -2)
        assert (updated > cap) == (not succeeds)
        if is_long:
            jump = find(rows, "0xa48", comparison["index"])
            assert jump["op"] == "JUMPI" and stack(jump, -1) == 0xea4
            assert stack(jump, -2) == int(not succeeds)
        if not succeeds:
            revert = find(rows, "0xea4", comparison["index"])
            assert revert["depth"] == 4
        samples.append({"label": label, "tx": saved["tx"], "source": f"artifacts/{filename}",
                        "signed_open_call_count_in_tx": len(matching),
                        "side": "long" if is_long else "short", "instrument_id": 0,
                        "base_slot": f"0x{slot:064x}", "cap_slot": f"0x{slot + 1:064x}",
                        "updated_exposure": str(updated), "cap": str(cap),
                        "exceeds_cap": updated > cap, "result": "success" if succeeds else "0x40f92143",
                        "comparison_pc": comparison["pc"],
                        "cap_half": "low uint128" if is_long else "high uint128"})
    assert [row["exceeds_cap"] for row in samples] == [True, False, True]
    result = {"pin": signed["pin"], "block_hash": signed["block_hash"],
              "signed_open_selector": signed["open_selector"],
              "raw_error_selector": "0x40f92143", "market_mapping_base_slot": 36,
              "samples": samples,
              "limits": ["Three sampled execution paths establish the comparison and branch, not every signed-open branch.",
                         "OiCapExceeded() is a hash-verified public registry candidate, but contract source is unverified.",
                         "Exposure is a behavior label inferred from the storage update and cap comparison, not a recovered source field name."]}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    result = build()
    print("signed-open side cap:", [(x["side"], x["result"]) for x in result["samples"]])
