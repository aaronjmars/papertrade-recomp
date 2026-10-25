#!/usr/bin/env python3
"""Replay sampled Exchange linked-library math and close settlement calls."""

import argparse
import collections
import glob
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "exchange_library"
LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
EXCHANGE_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN = 48902346
WAD = 10**18
MODULUS = 1 << 256
PNL_SELECTOR = "0x82296364"
SETTLEMENT_SELECTOR = "0xef1a27a9"
OTHER_SELECTOR = "0x79810ffe"
CLOSE_SELECTOR = "0x2792e706"
CLOSE_SIGNATURE = "closeBySig(address,uint256[],uint256,uint64,uint8,bytes32,bytes32)"
KECCAK = Keccak()


def signed(value):
    return value if value < (1 << 255) else value - MODULUS


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [signed(int(data[i:i + 64], 16)) for i in range(2, len(data), 64)]


def encode(selector, arguments):
    return selector + "".join((value % MODULUS).to_bytes(32, "big").hex() for value in arguments)


def all_calls(call, parent=None):
    yield call, parent
    for child in call.get("calls", []):
        yield from all_calls(child, call)


def canonical_trace(tx):
    paths = glob.glob(str(ROOT / "artifacts" / "*" / f"{tx}.calls*.json"))
    assert paths, tx
    path = sorted(paths, key=lambda p: ("calls_with_logs" not in p, len(p), p))[0]
    return json.loads(pathlib.Path(path).read_text())


def library_calls():
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    edge = next(row for row in graph["edges"] if row["to_role"] == "exchange_linked_library_live")
    assert edge["call_count"] >= 3 and edge["trace_hashes"]
    records = []
    for tx in edge["trace_hashes"]:
        root = canonical_trace(tx)
        for call, parent in all_calls(root):
            if call.get("to", "").lower() != LIBRARY:
                continue
            assert call.get("error") is None and call.get("output", "0x").startswith("0x")
            records.append({"tx": tx, "selector": call["input"][:10],
                            "parent_selector": parent["input"][:10],
                            "input": call["input"], "output": call["output"],
                            "arguments": words("0x" + call["input"][10:]),
                            "returns": words(call["output"])})
    assert len(records) == edge["call_count"]
    counts = collections.Counter(row["selector"] for row in records)
    assert counts[PNL_SELECTOR] == counts[SETTLEMENT_SELECTOR] > 0
    assert counts[OTHER_SELECTOR] == 1 and sum(counts.values()) == len(records)
    return records


def signed_close_calls():
    graph = json.loads((ATLAS / "observed_call_graph.json").read_text())
    edge = next(row for row in graph["edges"] if row["to_role"] == "exchange_linked_library_live")
    rows = []
    for tx in edge["trace_hashes"]:
        root = canonical_trace(tx)
        for call, _ in all_calls(root):
            if call.get("to", "").lower() != EXCHANGE_IMPLEMENTATION or call.get("input", "")[:10] != CLOSE_SELECTOR:
                continue
            args = words("0x" + call["input"][10:])
            assert args[1] == 224 and args[7] >= 1
            assert len(args) == 8 + args[7]
            child_count = collections.Counter(child["input"][:10] for child in call.get("calls", [])
                                              if child.get("to", "").lower() == LIBRARY)
            assert child_count == {PNL_SELECTOR: args[7], SETTLEMENT_SELECTOR: args[7]}
            rows.append({"tx": tx, "user": f"0x{args[0]:040x}", "position_ids": args[8:],
                         "nonce": args[2], "deadline": args[3],
                         "signature_v": args[4], "library_pairs": args[7]})
    assert rows and sum(row["library_pairs"] for row in rows) == len(
        [row for row in library_calls() if row["selector"] == PNL_SELECTOR])
    return rows


def pnl_model(args):
    assert len(args) == 9
    entry, exit_price, margin, leverage, is_long, fee, input6, input7, input8 = args
    assert 0 < entry < (1 << 64) and 0 <= exit_price < (1 << 64)
    assert margin >= 0 and leverage >= 0 and is_long in (0, 1)
    delta = (exit_price - entry) if is_long else (entry - exit_price)
    if delta > 0:
        delta = max(delta - entry // 50000, 0)
    raw = (1 if delta >= 0 else -1) * (margin * leverage * abs(delta) // entry)
    if raw <= 0:
        return [raw, raw]
    if input6 == 0 or input7 == 0 or fee == WAD:
        return [raw, 0]
    assert 0 <= fee <= WAD and input6 > 0 and input7 > 0 and input8 >= 0
    return_fraction = delta * WAD // entry
    exposure = return_fraction * input6 // WAD
    assert exposure > 0
    risk_inverse = WAD * WAD // exposure
    liquidity_exposure = return_fraction * 10**6 * input7 // WAD
    assert liquidity_exposure > 0
    liquidity_inverse = input8 * WAD // liquidity_exposure
    factor = (WAD - fee) * WAD // (WAD + risk_inverse + liquidity_inverse)
    return [raw, raw * factor // WAD]


def settlement_model(args):
    assert len(args) == 8
    _, _, margin, adjusted_pnl, flag, profit_rate, loss_rate, branch_value = args
    assert flag == 0 and 0 <= profit_rate <= WAD and 0 <= loss_rate <= WAD
    rate = profit_rate if adjusted_pnl > 0 else loss_rate if adjusted_pnl < 0 else 0
    fee = abs(adjusted_pnl) * rate // WAD
    payout = margin + min(adjusted_pnl, 0)
    if branch_value == 0:
        return [payout, 0, adjusted_pnl - fee if adjusted_pnl > 0 else 0,
                -adjusted_pnl if adjusted_pnl < 0 else 0, 0, 0]
    return [payout, adjusted_pnl - fee if adjusted_pnl > 0 else 0, 0, 0,
            fee // 2 if adjusted_pnl else 0, fee - fee // 2 if adjusted_pnl else 0]


def probe_cases(records):
    gains = [row for row in records if row["selector"] == PNL_SELECTOR and row["returns"][0] > 0]
    losses = [row for row in records if row["selector"] == PNL_SELECTOR and row["returns"][0] < 0]
    assert gains and losses
    base = gains[0]["arguments"]
    probes = [("historical_gain", gains[0]["arguments"]),
              ("historical_loss", losses[0]["arguments"])]
    for is_long in (0, 1):
        for delta in (-100, -5, -4, 0, 4, 5, 100):
            args = base.copy()
            args[1] = args[0] + delta
            args[4] = is_long
            probes.append((f"side_{is_long}_delta_{delta}", args))
    for index, value, label in ((5, 0, "no_fee"), (5, WAD, "full_fee"),
                                (6, 0, "zero_input6"), (6, base[6] // 2, "half_input6"),
                                (7, 0, "zero_input7"), (7, base[7] // 2, "half_input7"),
                                (8, 0, "zero_input8"), (8, base[8] * 2, "double_input8")):
        args = base.copy()
        args[index] = value
        probes.append((label, args))
    assert len(probes) == 24
    return probes


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS / "pinned_math_probes.json"
    if path.exists():
        return
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    samples = []
    for name, arguments in probe_cases(library_calls()):
        data = encode(PNL_SELECTOR, arguments)
        output = rpc(url, "eth_call", [{"to": LIBRARY, "data": data}, hex(PIN)])
        samples.append({"name": name, "arguments": [str(x) for x in arguments],
                        "input": data, "output": output})
        print("library math", name, flush=True)
    path.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                "samples": samples}, indent=2) + "\n")


def verify():
    assert "0x" + KECCAK(CLOSE_SIGNATURE.encode()).hex()[:8] == CLOSE_SELECTOR
    records = library_calls()
    close_calls = signed_close_calls()
    math_calls = [row for row in records if row["selector"] == PNL_SELECTOR]
    settlements = [row for row in records if row["selector"] == SETTLEMENT_SELECTOR]
    other = [row for row in records if row["selector"] == OTHER_SELECTOR]
    assert len(math_calls) == len(settlements) > 0 and len(other) == 1
    branches = collections.Counter()
    ledger = []
    for math, settlement in zip(math_calls, settlements):
        assert math["tx"] == settlement["tx"]
        assert math["parent_selector"] == settlement["parent_selector"] == "0x2792e706"
        assert len(math["arguments"]) == 9 and len(math["returns"]) == 2
        assert len(settlement["arguments"]) == 8 and len(settlement["returns"]) == 6
        assert settlement["arguments"][5:7] == [2 * 10**16, 2 * 10**16]
        assert math["returns"] == pnl_model(math["arguments"])
        assert settlement["arguments"][2] == math["arguments"][2]
        assert settlement["arguments"][3] == math["returns"][1]
        assert settlement["returns"] == settlement_model(settlement["arguments"])
        adjusted = math["returns"][1]
        branch = ("zero_tail_" if settlement["arguments"][7] == 0 else "nonzero_tail_")
        branch += "profit" if adjusted > 0 else "loss" if adjusted < 0 else "flat"
        branches[branch] += 1
        ledger.append({"tx": math["tx"], "entry_price": math["arguments"][0],
                       "exit_price": math["arguments"][1], "margin": str(math["arguments"][2]),
                       "leverage": math["arguments"][3], "is_long": bool(math["arguments"][4]),
                       "raw_pnl": str(math["returns"][0]),
                       "adjusted_pnl": str(adjusted),
                       "settlement_input_tail": str(settlement["arguments"][7]),
                       "settlement_output": [str(x) for x in settlement["returns"]],
                       "checks": {"raw_and_adjusted_pnl": True,
                                  "pnl_passed_to_settlement": True,
                                  "six_settlement_outputs": True}})
    assert sum(branches.values()) == len(settlements)
    assert other[0]["parent_selector"] == "0xddc63262"
    harvest_library = json.loads((ATLAS / "exchange_library_harvest_behavior.json").read_text())
    assert harvest_library["selector"] == OTHER_SELECTOR and harvest_library["historical_count"] == 1
    assert harvest_library["read_only_simulation_count"] == 13
    assert harvest_library["cases"][0]["returns"] == [str(x) for x in other[0]["returns"]]
    trace = json.loads((ARTIFACTS / "pnl_sample_opcode_trace.json").read_text())
    assert trace["trace"]["failed"] is False and len(trace["trace"]["structLogs"]) == 707
    assert trace["trace"]["returnValue"] == trace["historical_output"]
    assert any(row["input"] == trace["input"] and row["output"] == trace["historical_output"]
               for row in math_calls)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    saved = json.loads((ARTIFACTS / "pinned_math_probes.json").read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    assert len(saved["samples"]) == 24
    expected_cases = probe_cases(records)
    for (name, args), sample in zip(expected_cases, saved["samples"]):
        assert sample["name"] == name and sample["input"] == encode(PNL_SELECTOR, args)
        assert sample["arguments"] == [str(x) for x in args]
        assert words(sample["output"]) == pnl_model(args)
    result = {"pin_block": PIN, "library": LIBRARY,
              "exchange_parent_implementation": EXCHANGE_IMPLEMENTATION,
              "exchange_parent_selector_reconstructions": {CLOSE_SELECTOR: CLOSE_SIGNATURE},
              "signed_close_call_count": len(close_calls),
              "signed_close_position_id_count": sum(row["library_pairs"] for row in close_calls),
              "historical_transaction_count": len({row["tx"] for row in records}),
              "historical_library_call_count": len(records),
              "pnl_call_count": len(math_calls), "settlement_call_count": len(settlements),
              "other_observed_call_count": len(other), "pinned_math_probe_count": len(saved["samples"]),
              "settlement_branches": dict(branches),
              "selector_behaviors": {PNL_SELECTOR: "two-word signed raw and adjusted PnL calculation",
                                     SETTLEMENT_SELECTOR: "six-word close-settlement calculation using adjusted PnL",
                                     OTHER_SELECTOR: "queue harvest: first word is total user credit; second is input word 4 plus that credit; one historical and thirteen simulated calls check events and storage"},
              "observed_abi_arguments": {
                  PNL_SELECTOR: "uint64,uint64,uint128,uint32,bool,uint256,uint256,uint256,uint256",
                  SETTLEMENT_SELECTOR: "uint256,address,uint128,int256,bool,uint256,uint256,uint256"},
              "other_observed_call": {"tx": other[0]["tx"], "parent_selector": other[0]["parent_selector"],
                                      "arguments": [str(x) for x in other[0]["arguments"]],
                                      "returns": [str(x) for x in other[0]["returns"]]},
              "signed_close_calls": close_calls,
              "ledger": ledger,
              "limits": [f"All {len(settlements)} historical settlement samples use equal fee-rate inputs; the separate controlled replay ledger checks unequal rates.",
                         "The exact Solidity source names of all ten library selectors remain unknown.",
                         "The remaining seven library selectors have no saved historical call.",
                         "The single historical 0x79810ffe call plus thirteen read-only simulations cover selected queue harvest branches, not every possible queue state.",
                         "Direct math probes simulate execution at the pin; no transactions were sent."]}
    (ATLAS / "exchange_library_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Exchange library: {len(close_calls)} signed closes, {len(math_calls)} exact PnL pairs, "
          f"{len(settlements)} exact settlement outputs, {len(saved['samples'])} pinned probes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
