#!/usr/bin/env python3
"""Classify all saved CoreWithdrawal events and check stratified status traces."""

import argparse
import collections
import concurrent.futures
import json
import pathlib

from atlas_exchange_withdrawal_history import ARTIFACT, ATLAS, EXCHANGE, PIN, TOPIC, rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRACES = ROOT / "artifacts" / "exchange_core_withdrawal" / "status_samples"
OUTPUT = ATLAS / "exchange_withdrawal_event_census.json"
SAMPLE_PER_CLASS = 16
STATUS_PRECOMPILE = "0x0000000000000000000000000000000000000810"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"


def event_rows(saved):
    rows = []
    for window in saved["windows"]:
        for log in window["logs"]:
            data = log["data"]
            assert len(log["topics"]) == 2 and len(data) == 130
            debit = int(data[2:66], 16)
            core_amount = int(data[66:130], 16)
            gap = debit - core_amount * 10**10
            rows.append((log, gap))
    return rows


def chosen_events(rows):
    by_gap = collections.defaultdict(list)
    for log, gap in rows:
        by_gap[gap].append(log)
    assert set(by_gap) == {0, 10**18}
    chosen = []
    for gap in (0, 10**18):
        group = by_gap[gap]
        indices = [j * (len(group) - 1) // (SAMPLE_PER_CLASS - 1)
                   for j in range(SAMPLE_PER_CLASS)]
        chosen.extend((group[index], gap) for index in indices)
    assert len(chosen) == SAMPLE_PER_CLASS * 2
    assert len({log["transactionHash"] for log, _ in chosen}) == len(chosen)
    return chosen


def descendants(node):
    yield node
    for child in node.get("calls", []):
        yield from descendants(child)


def matched_call(trace, event):
    matches = []
    for node in descendants(trace):
        for log in node.get("logs", []):
            if (log.get("address", "").lower() == EXCHANGE and
                    log.get("topics") == event["topics"] and
                    log.get("data") == event["data"]):
                matches.append(node)
    assert len(matches) == 1
    return matches[0]


def verify():
    saved = json.loads(ARTIFACT.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin"] == PIN and saved["block_hash"] == manifest["block_hash"]
    rows = event_rows(saved)
    chosen = chosen_events(rows)
    gaps = collections.Counter(gap for _, gap in rows)
    assert len(rows) == 28643 and gaps == {0: 22652, 10**18: 5991}
    result_rows = []
    for event, gap in chosen:
        tx = event["transactionHash"]
        trace = json.loads((TRACES / f"{tx}.calls.json").read_text())
        call = matched_call(trace, event)
        assert call["type"] == "DELEGATECALL" and call["to"].lower() == IMPLEMENTATION
        selector = call["input"][:10]
        assert selector in ("0x8d09f23f", "0x2792e706")
        status_calls = [n for n in descendants(call)
                        if n.get("to", "").lower() == STATUS_PRECOMPILE]
        assert len(status_calls) == 1
        status_call = status_calls[0]
        status = int(status_call["output"], 16)
        assert status in (0, 1)
        assert gap == (10**18 if status == 0 else 0)
        result_rows.append({
            "tx": tx, "block": int(event["blockNumber"], 16),
            "log_index": int(event["logIndex"], 16),
            "selector": selector, "hypercore_user_status": status,
            "event_debit_gap_18_decimals": str(gap),
        })
    by_selector_status = collections.Counter((row["selector"], row["hypercore_user_status"])
                                            for row in result_rows)
    assert by_selector_status == {("0x8d09f23f", 0): 16,
                                  ("0x8d09f23f", 1): 16}
    output = {
        "pin": PIN, "block_hash": saved["block_hash"], "exchange": EXCHANGE,
        "event_topic0": TOPIC, "event_count": len(rows),
        "gap_definition": "event internal debit minus event Core amount multiplied by 10^10",
        "gap_counts_18_decimals": {str(k): gaps[k] for k in sorted(gaps)},
        "sample_selection": "16 evenly spaced event logs within each debit-gap class in saved chain order; unique transaction hashes",
        "sample_count": len(result_rows), "sample_selector_status_counts": [
            {"selector": selector, "hypercore_user_status": status, "count": count}
            for (selector, status), count in sorted(by_selector_status.items())],
        "status_precompile": STATUS_PRECOMPILE,
        "status_semantic_evidence": "hypercore_user_exists_evidence.json",
        "sampled_events": result_rows,
        "limit": "The full-event census proves the two debit gaps through the pin. HyperCore status and function selector are checked only for the stratified trace sample, not all 28,643 events."
    }
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n")
    print(len(rows), "withdrawal events:", dict(gaps), ";", len(result_rows),
          "status-matched traces:", dict(by_selector_status))
    return output


def capture():
    saved = json.loads(ARTIFACT.read_text())
    chosen = chosen_events(event_rows(saved))
    TRACES.mkdir(parents=True, exist_ok=True)

    def fetch(item):
        event, _ = item
        tx = event["transactionHash"]
        path = TRACES / f"{tx}.calls.json"
        if not path.exists():
            trace = rpc("debug_traceTransaction", [tx, {
                "tracer": "callTracer", "tracerConfig": {"withLog": True}}])
            matched_call(trace, event)
            path.write_text(json.dumps(trace, indent=2) + "\n")
        return tx

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for tx in pool.map(fetch, chosen):
            print("captured", tx, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
