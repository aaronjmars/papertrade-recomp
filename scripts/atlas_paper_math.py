#!/usr/bin/env python3
"""Verify live PaperMath arithmetic against saved calls and pinned probes."""

import argparse
import collections
import glob
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
LIBRARY = "0xe991817199363046da0a28da6fbad0284e4aa492"
TOKENOMICS_PROXY = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
TOKENOMICS_IMPLEMENTATION = "0x600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f"
PAPER_PROXY = "0xe40f17915daa230324030003a197cdaef2261c0e"
OPEN_EVENT = "0x620c26bf4591919d64df736a6afdfe2981d15eb343c50644b49456c6facb3ab2"
LIQUIDATION_EVENT = "0x3050fba19ada85812db26b240c13c72cabec711cbf18c7c6b3554d511e2951ee"
TRANSFER_EVENT = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
SELECTOR = "0x7aac24ba"
PIN = 48902346
MODULUS = 1 << 256
WAD = 10**18
BOUNDARIES = ROOT / "artifacts" / "paper_math" / "pinned_boundaries.json"
EXISTING_PROBES = ROOT / "artifacts" / "tokenomics" / "pinned_math_probes.json"


def calls(node, parent=None):
    yield node, parent
    for child in node.get("calls", []):
        yield from calls(child, node)


def trace(tx):
    paths = glob.glob(str(ROOT / "artifacts" / "*" / f"{tx}.calls*.json"))
    assert paths, tx
    path = sorted(paths, key=lambda item: ("calls_with_logs" not in item, len(item), item))[0]
    return json.loads(pathlib.Path(path).read_text())


def receipt(tx):
    paths = glob.glob(str(ROOT / "artifacts" / "*" / f"{tx}.receipt.json"))
    assert paths, tx
    rows = [json.loads(pathlib.Path(path).read_text()) for path in paths]
    assert all(row == rows[0] for row in rows), tx
    return rows[0]


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[offset:offset + 64], 16) for offset in range(2, len(data), 64)]


def input_words(data):
    assert data.startswith(SELECTOR) and len(data) == 10 + 6 * 64
    return [int(data[offset:offset + 64], 16) for offset in range(10, len(data), 64)]


def signed(value):
    return value if value < MODULUS // 2 else value - MODULUS


def quote(args):
    tracked_word, progress, amount, threshold, rate, scale = args
    tracked = signed(tracked_word)
    flat = min(amount, max(0, threshold - tracked))
    tail = amount - flat
    mint = flat * rate // WAD
    if tail:
        start = scale * WAD // (scale + progress)
        end = scale * WAD // (scale + progress + tail)
        tail_rate = (rate * start // WAD) * end // WAD
        mint += tail_rate * tail // WAD
    return [mint, tail]


def branch(args):
    tracked = signed(args[0])
    flat = min(args[2], max(0, args[3] - tracked))
    return "flat" if flat == args[2] else "tail" if flat == 0 else "crossing"


def boundary_cases():
    return (
        ("zero_amount", [0, 0, 0, 10, 100 * WAD, 120]),
        ("zero_scale_positive_progress", [20, 1, 1, 10, 100 * WAD, 0]),
        ("zero_denominator", [20, 0, 1, 10, 100 * WAD, 0]),
        ("flat_mul_overflow", [0, 0, 2, 3, MODULUS - 1, 120]),
        ("signed_add_overflow", [(1 << 255) - 1, 0, 1, (1 << 255) - 1, 100 * WAD, 120]),
        ("scale_progress_overflow", [20, MODULUS - 1, 1, 10, 100 * WAD, 1]),
    )


def encode(args):
    assert len(args) == 6 and all(0 <= value < MODULUS for value in args)
    return SELECTOR + "".join(value.to_bytes(32, "big").hex() for value in args)


def capture():
    from atlas_tokenomics import rpc

    manifest = json.loads((ATLAS / "manifest.json").read_text())
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    rows = []
    for name, args in boundary_cases():
        data = encode(args)
        result = rpc(url, "debug_traceCall", [{"to": LIBRARY, "data": data}, hex(PIN),
                                               {"tracer": "callTracer"}])
        rows.append({"name": name, "arguments": [str(value) for value in args],
                     "input": data, "error": result.get("error"),
                     "output": result.get("output", "0x")})
    BOUNDARIES.parent.mkdir(parents=True, exist_ok=True)
    BOUNDARIES.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                      "cases": rows}, indent=2) + "\n")


def verify_probes(manifest):
    from atlas_tokenomics import math_quote

    old = json.loads(EXISTING_PROBES.read_text())
    assert old["pin_block"] == PIN and old["pin_hash"] == manifest["block_hash"]
    assert len(old["probes"]) == 6
    sampled = []
    for row in old["probes"]:
        args = [int(value) for value in row["arguments"]]
        output = words(row["output"])
        assert len(output) == 2 and output == quote(args) == math_quote(args)
        sampled.append({"name": row["name"], "branch": branch(args),
                        "arguments": row["arguments"], "returns": [str(value) for value in output]})
    assert {row["branch"] for row in sampled} == {"flat", "tail", "crossing"}
    saved = json.loads(BOUNDARIES.read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert len(saved["cases"]) == len(boundary_cases())
    expected_reverts = {"zero_denominator": "0x12", "flat_mul_overflow": "0x11",
                        "signed_add_overflow": "0x11", "scale_progress_overflow": "0x11"}
    checks = []
    for row, (name, args) in zip(saved["cases"], boundary_cases()):
        assert row["name"] == name and row["arguments"] == [str(value) for value in args]
        assert row["input"] == encode(args)
        if name in expected_reverts:
            assert row["error"] == "execution reverted"
            assert row["output"] == "0x4e487b71" + int(expected_reverts[name], 16).to_bytes(32, "big").hex()
        else:
            assert row["error"] is None
            assert words(row["output"]) == quote(args) == math_quote(args)
        checks.append({"name": name, "error": row["error"], "output": row["output"]})
    return sampled, checks


def build():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN and manifest["contracts"][LIBRARY]["role"] == "paper_math_library"
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    edge = next(row for row in graph["edges"] if row["to_role"] == "paper_math_library")
    assert edge["from_role"] == "tokenomics_proxy" and edge["call_type"] == "DELEGATECALL"
    assert edge["selectors"] == {SELECTOR: 91}
    sampled, boundaries = verify_probes(manifest)
    ledger = []
    branches = collections.Counter()
    for tx in edge["trace_hashes"]:
        outputs = []
        for call, parent in calls(trace(tx)):
            if call.get("to", "").lower() != LIBRARY:
                continue
            assert call["type"] == "DELEGATECALL" and call["input"].startswith(SELECTOR)
            assert call.get("error") is None and call["from"].lower() == TOKENOMICS_PROXY
            assert parent and parent["to"].lower() == TOKENOMICS_IMPLEMENTATION
            args = input_words(call["input"])
            output = words(call["output"])
            assert len(output) == 2 and output == quote(args)
            kind = branch(args)
            branches[kind] += 1
            outputs.append(output)
            ledger.append({"tx": tx, "branch": kind, "arguments": [str(value) for value in args],
                           "signed_tracked": str(signed(args[0])),
                           "returns": [str(value) for value in output]})
        logs = receipt(tx)["logs"]
        tokenomics_outputs = []
        paper_mints = []
        for log in logs:
            topic = log["topics"][0].lower() if log["topics"] else ""
            if log["address"].lower() == TOKENOMICS_PROXY and topic in (OPEN_EVENT, LIQUIDATION_EVENT):
                event_words = words(log["data"])
                assert len(event_words) == 6
                if event_words[5] > 0:
                    tokenomics_outputs.append([event_words[5], event_words[4]])
            if log["address"].lower() == PAPER_PROXY and topic == TRANSFER_EVENT:
                assert len(log["topics"]) == 3
                if int(log["topics"][1], 16) == 0:
                    paper_mints.append(int(log["data"], 16))
        assert outputs == tokenomics_outputs, tx
        assert [row[0] for row in outputs] == paper_mints, tx
    assert len(ledger) == edge["call_count"] == 91
    assert branches == {"flat": 1, "tail": 90}
    return {"pin_block": PIN, "block_hash": manifest["block_hash"], "library": LIBRARY,
            "selector": SELECTOR, "observed_abi_arguments": {SELECTOR: "int256,uint256,uint256,uint256,uint256,uint256"},
            "observed_abi_returns": "uint256,uint256", "source_name_status": "unknown",
            "historical_transaction_count": len(edge["trace_hashes"]),
            "historical_call_count": len(ledger), "historical_branches": dict(branches),
            "matched_tokenomics_events": len(ledger), "matched_paper_transfer_mints": len(ledger),
            "prior_read_only_probe_count": len(sampled), "boundary_probe_count": len(boundaries),
            "historical_calls": ledger, "prior_read_only_probes": sampled, "boundary_probes": boundaries,
            "checked_behavior": "signed tracked amount, flat threshold and decaying tail arithmetic with integer floor division; two uint256 returns are mint amount and tail amount",
            "limitations": ["The exact Solidity function name is unknown.",
                            "The model matches 91 successful historical calls and 12 direct read-only probes; these do not exhaust 256-bit arithmetic inputs.",
                            "Only four selected panic boundaries have been checked; other overflow and division paths remain open."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    result = build()
    (ATLAS / "paper_math_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"PaperMath: {result['historical_call_count']} historical calls, "
          f"{result['prior_read_only_probe_count'] + result['boundary_probe_count']} pinned probes verified")
