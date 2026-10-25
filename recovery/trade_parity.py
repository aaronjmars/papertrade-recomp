"""Replay a historical signed open through the PT-01 recovery fallback.

The pinned implementation, the live implementation and the candidate are replayed against
the archived prestate, return data, logs and post-transaction storage. The pinned replay
is the historical anchor; the candidate must reproduce the live implementation exactly,
whatever the live set does with this transaction.
"""

import argparse
import hashlib
import json
import pathlib

from atlas_oracle_behavior import returndata
from audit_historical_open_replay import s_address
from recovery import historical_replay
from recovery.deploy import address as candidate_address

ROOT = pathlib.Path(__file__).resolve().parents[1]
HERE = pathlib.Path(__file__).resolve().parent
ATLAS = ROOT / "atlas" / "block_48902346"
REDRIVE = ROOT / "artifacts" / "recovery_redrive"
LIVE_FACTS = REDRIVE / "live_facts.json"
TX = "0xbfdbeb1a73a25264e1467b0f5be6646fb26f8ece631b1e2181133a49e2d0484c"
EVIDENCE = ROOT / "artifacts" / "audit_historical_open"
PRESTATE = EVIDENCE / f"{TX}.prestate.json"
HEADER = EVIDENCE / f"{TX}.header.json"
CALLS = ROOT / "artifacts" / "batch_executor" / f"{TX}.calls.json"
TRANSACTION = ROOT / "artifacts" / "batch_executor" / f"{TX}.tx.json"
RECEIPT = ROOT / "artifacts" / "exchange_positions" / f"{TX}.receipt.json"
DIFF = ROOT / "artifacts" / "exchange_positions" / f"{TX}.state_diff.json"
OUT = HERE / "trade_parity.json"
COMPILED = HERE / "compiled.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
PINNED = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
LIVE = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
RECOVERY = candidate_address()
BBO = "0x000000000000000000000000000000000000080e"
PREFIX = "papertrade-pt01-trade-parity-"
ARCHIVE_TESTS = ("testPinnedReplayMatchesArchive", "testLiveReplayMatchesArchive",
                 "testRecoveryReplayMatchesArchive")
LIMITS = [
    "The candidate and the live implementation are installed counterfactually at the historical block.",
    "The BBO precompile returns its archived observed response.",
    "The prestate tracer captures storage accessed by this transaction, not all historical state.",
    "One signed open does not establish other trading paths, upgrade safety, or Core settlement.",
    "The archive reference describes the pinned implementation; a live mismatch is a live-set change, not a candidate defect.",
]


def descendants(node):
    for child in node.get("calls", []):
        yield child
        yield from descendants(child)


def evidence():
    prestate = json.loads(PRESTATE.read_text())
    header = json.loads(HEADER.read_text())
    calls = json.loads(CALLS.read_text())
    tx = json.loads(TRANSACTION.read_text())
    receipt = json.loads(RECEIPT.read_text())
    diff = json.loads(DIFF.read_text())
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == 48_902_346
    assert tx["hash"].lower() == receipt["transactionHash"].lower() == TX
    assert tx["blockHash"].lower() == receipt["blockHash"].lower() == header["hash"].lower()
    assert calls["input"].lower() == tx["input"].lower()
    assert calls["from"].lower() == tx["from"].lower()
    assert calls["to"].lower() == tx["to"].lower()
    assert receipt["status"] == "0x1" and int(tx["value"], 16) == 0
    first = calls["calls"][0]["calls"][0]
    assert first["to"].lower() == EXCHANGE and first["input"].startswith("0xec6783f0")
    assert first["output"] == "0x" + f"{0x15458f:064x}"
    bbo_calls = [node for node in descendants(calls) if node.get("to", "").lower() == BBO]
    assert len(bbo_calls) == 2 and len({node["output"] for node in bbo_calls}) == 1
    assert len(bbo_calls[0]["output"]) == 130
    bbo_words = [int(bbo_calls[0]["output"][i:i + 64], 16) for i in (2, 66)]
    assert len(bbo_words) == 2

    code_files, setup_lines = {}, []
    for address, row in sorted(prestate.items()):
        code = row.get("code", "0x")
        if code != "0x":
            assert hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() == manifest["contracts"][address]["sha256"]
            code_files[address] = code
            setup_lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    assert len(code_files) == 8 and PINNED in code_files
    compiled = json.loads(COMPILED.read_text())
    live = json.loads(LIVE_FACTS.read_text())
    assert live["exchange"]["implementation"] == LIVE
    candidate_code = compiled["deployed_code"]
    assert hashlib.sha256(bytes.fromhex(candidate_code[2:])).hexdigest() == compiled["deployed_code_sha256"]
    live_code = "0x" + (REDRIVE / live["exchange"]["implementation_runtime_file"]).read_text().strip()[2:]
    assert hashlib.sha256(bytes.fromhex(live_code[2:])).hexdigest() == live["exchange"]["implementation_code_sha256"]
    code_files[LIVE] = live_code
    code_files[RECOVERY] = candidate_code
    setup_lines.append(f'        vm.etch({s_address(LIVE)}, vm.parseBytes(vm.readFile("runtime/{LIVE[2:]}.hex")));')
    setup_lines.append(f'        vm.etch({s_address(RECOVERY)}, vm.parseBytes(vm.readFile("runtime/{RECOVERY[2:]}.hex")));')
    for address, row in diff["pre"].items():
        for slot, value in row.get("storage", {}).items():
            assert int(prestate[address]["storage"][slot], 16) == int(value, 16)
    assert set(diff["post"]) <= set(prestate)
    setup_lines.append(f'        vm.etch({s_address(BBO)}, hex"{returndata(*bbo_words)[2:]}");')

    expected_logs = receipt["logs"]
    archive_lines = [f'require(keccak256(result) == keccak256(hex"{calls.get("output", "0x")[2:]}"), "return data");']
    archive_lines.append(f'require(logs.length == {len(expected_logs)}, "log count");')
    for i, log in enumerate(expected_logs):
        archive_lines.append(f'require(logs[{i}].emitter == {s_address(log["address"])}, "log {i} emitter");')
        archive_lines.append(f'require(logs[{i}].topics.length == {len(log["topics"])}, "log {i} topic count");')
        for j, topic in enumerate(log["topics"]):
            archive_lines.append(f'require(logs[{i}].topics[{j}] == {topic}, "log {i} topic {j}");')
        archive_lines.append(f'require(keccak256(logs[{i}].data) == keccak256(hex"{log["data"][2:]}"), "log {i} data");')
    post_slots = []
    for address, row in sorted(diff["post"].items()):
        for slot in sorted(row.get("storage", {})):
            post_slots.append((s_address(address), slot))
            archive_lines.append(
                f'require(vm.load({s_address(address)}, {slot}) == {row["storage"][slot]}, "post {address} {slot}");')
    assert len(expected_logs) == 4 and len(post_slots) == 11
    return {"header": header, "tx": tx, "calls": calls, "receipt": receipt, "code_files": code_files,
            "setup_lines": setup_lines, "archive_lines": archive_lines, "post_slots": post_slots,
            "bbo_words": bbo_words}


def build(strict_live, strict_recovery):
    data = evidence()
    return historical_replay.build(
        setup_lines=data["setup_lines"],
        archive_lines=data["archive_lines"],
        calldata=data["tx"]["input"][2:],
        caller=s_address(data["tx"]["from"]),
        proxy=s_address(EXCHANGE),
        target=s_address(data["tx"]["to"]),
        block=int(data["header"]["number"], 16),
        timestamp=int(data["header"]["timestamp"], 16),
        chain_id=999,
        pinned_address=s_address(PINNED),
        live_address=s_address(LIVE),
        recovery_address=s_address(RECOVERY),
        post_slots=data["post_slots"],
        strict_live=strict_live,
        strict_recovery=strict_recovery,
    )


def deterministic(flags):
    data = evidence()
    source = build(*flags)
    return {
        "source_transaction": TX,
        "historical_block": int(data["header"]["number"], 16),
        "historical_block_hash": data["header"]["hash"],
        "prestate_sha256": hashlib.sha256(PRESTATE.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "runtime_sha256": {address: hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
                           for address, code in sorted(data["code_files"].items())},
        "pinned_implementation": PINNED,
        "live_implementation": LIVE,
        "candidate_implementation": RECOVERY,
        "candidate_code_sha256": json.loads(COMPILED.read_text())["deployed_code_sha256"],
        "mocked_bbo_output": "0x" + "".join(f"{word:064x}" for word in data["bbo_words"]),
        "strict_live_archive": flags[0],
        "strict_candidate_archive": flags[1],
        "receipt_logs_matched_each": len(data["receipt"]["logs"]),
        "post_storage_words_matched_each": len(data["post_slots"]),
    }


def run():
    data = evidence()
    outcome, flags = historical_replay.resolve(build, data["code_files"], PREFIX, ARCHIVE_TESTS, LIMITS)
    payload = deterministic(flags)
    assert payload["strict_live_archive"] == payload["strict_candidate_archive"] == flags[0]
    payload.update(outcome)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return verify()


def verify():
    saved = json.loads(OUT.read_text())
    flags = (saved["strict_live_archive"], saved["strict_candidate_archive"])
    calculated = deterministic(flags)
    assert {key: saved[key] for key in calculated} == calculated
    anchor = "testPinnedReplayMatchesArchive"
    assert saved["archive_matched"][anchor] is True
    assert saved["relaxed_rerun"] == (not flags[0])
    assert flags[0] == flags[1]
    assert saved["replay_tests"][anchor] is True
    assert saved["replay_tests"]["testLiveAndRecoveryReplayAgree"] is True
    assert set(saved["replay_tests"]) == ({anchor, "testLiveAndRecoveryReplayAgree"} if saved["relaxed_rerun"]
                                          else set(ARCHIVE_TESTS) | {"testLiveAndRecoveryReplayAgree"})
    assert saved["forge_result"] == f"{len(saved['replay_tests'])} passed, 0 failed"
    assert all(saved["replay_tests"].values())
    assert saved["limits"] == LIMITS
    assert saved["receipt_logs_matched_each"] == 4
    assert saved["post_storage_words_matched_each"] == 11
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="refresh the local Forge replay ledger")
    args = parser.parse_args()
    print(json.dumps(run() if args.run else verify(), indent=2))
