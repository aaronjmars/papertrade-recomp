#!/usr/bin/env python3
"""Verify the first older Exchange settlement library's liquidity branch."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

from atlas_deployer_scope import call, rpc_batch
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
DEPL = ROOT / "artifacts" / "deployer_scope"
HISTORY = DEPL / "older_exchange_queue_replay.json.gz"
SOURCE = DEPL / "older_settlement_liquidity.t.sol"
ARCHIVE = DEPL / "older_settlement_liquidity_getter.json"
REPLAY = DEPL / "older_settlement_liquidity_replay.json"
FORK_SOURCE = DEPL / "older_settlement_exchange.t.sol"
BASE_SOURCE = DEPL / "older_exchange_debt_open.t.sol"
FORK_TRACE = DEPL / "older_settlement_exchange_trace.txt.gz"
FORK_REPLAY = DEPL / "older_settlement_exchange_replay.json"
OLD_EXCHANGE = "0x1b534e482b92bb6daff452cd12f2e35219e13493"
OLD_IMPLEMENTATION = "0x557c853e100600e0ee91e0df88fcf4af0097ff89"
OLD_LIBRARY = "0xac8ba1307815f74bd13d4d039c96f7b97e81aa49"
SETTLEMENT = "0xaa31b143"
AVAILABLE = "0x0cdd5fc4"
RUNTIME = ATLAS / "runtime" / f"{OLD_LIBRARY}.hex"
WAD = 10**18
TEST_NAMES = {
    "testProfitNoLiquidityQueuesAll",
    "testProfitPartialLiquidityQueuesRemainder",
    "testProfitExactLiquidityPaysWithoutFee",
    "testProfitBelowFeeThresholdPaysWithoutFee",
    "testProfitAtFeeThresholdPaysFee",
    "testProfitUsesGainRate",
    "testLossFeeIndependentOfLiquidity",
    "testLossUsesLossRate",
    "testFlatNoLiquidity",
}
FORK_NAMES = {
    "testTightZeroQueuesGain": (0, 0, 331_156_061_910_525_405),
    "testTightPartialQueuesRemainder": (331_156_061_910_525_404, 331_156_061_910_525_404, 1),
    "testTightExactGainPaysWithoutFee": (331_156_061_910_525_405, 331_156_061_910_525_405, 0),
    "testTightBelowFeeThresholdPaysWithoutFee": (337_779_183_148_735_912, 331_156_061_910_525_405, 0),
    "testTightAtFeeThresholdPaysFee": (337_779_183_148_735_913, 324_532_940_672_314_897, 0),
}
CASES = [
    ("profit_no_liquidity", 101, 3, 7, 0),
    ("profit_partial", 101, 3, 7, 100),
    ("profit_exact", 101, 3, 7, 101),
    ("profit_below_fee_threshold", 101, 3, 7, 103),
    ("profit_at_fee_threshold", 101, 3, 7, 104),
    ("profit_unequal_rates", 101, 1, 9, 200),
    ("loss_no_liquidity", -101, 3, 7, 0),
    ("loss_unequal_rates", -101, 1, 9, 200),
    ("flat_no_liquidity", 0, 3, 7, 0),
]


def frames(frame):
    yield frame
    for child in frame.get("calls", []):
        yield from frames(child)


def history():
    saved = json.loads(gzip.decompress(HISTORY.read_bytes()))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["fork_block"] == 47_572_842
    assert saved["chain_id"] == manifest["chain_id"] == 999
    assert int(saved["source_receipt"]["blockNumber"], 16) == saved["fork_block"] + 1
    assert int(saved["source_receipt"]["transactionIndex"], 16) == 0
    assert saved["source_receipt"]["transactionHash"].lower() == saved["source_tx"]
    library_calls = [
        frame for frame in frames(saved["source_trace"])
        if frame.get("to", "").lower() == OLD_LIBRARY
        and frame.get("input", "").startswith(SETTLEMENT)
    ]
    assert len(library_calls) == 1
    data = library_calls[0]["input"]
    assert len(data) == 2 + 8 + 7 * 64
    arguments = [int(data[10 + 64 * i:10 + 64 * (i + 1)], 16) for i in range(7)]
    assert arguments[0] == 15 and arguments[6] > 0
    runtime = bytes.fromhex(RUNTIME.read_text().strip()[2:])
    runtime_sha256 = hashlib.sha256(runtime).hexdigest()
    assert runtime_sha256 == "86184c390d6f62a8bd0e97080a0959ba7a3860b1358635994f82f61e81ceac8c"
    assert saved["runtime_hashes"][OLD_LIBRARY] == runtime_sha256
    keccak = Keccak()
    assert keccak(runtime).hex() == "23d9559d8bcf93e21027b102fbee55eba98f291ed237d2d24c62001e43b9b63a"
    scope = json.loads(gzip.decompress((DEPL / "pinned_capture.json.gz").read_bytes()))
    implementation = next(row for row in scope["rows"] if row["address"] == OLD_IMPLEMENTATION)
    implementation_runtime = bytes.fromhex(implementation["runtime"][2:])
    assert hashlib.sha256(implementation_runtime).hexdigest() == saved["runtime_hashes"][OLD_IMPLEMENTATION]
    assert keccak(implementation_runtime).hex() == "4fb669a254fa857e1c52da492625e2f4aa4f970f9f3ff8f80db8ecf41ac175bd"
    return saved, arguments, runtime_sha256


def capture():
    saved, arguments, _ = history()
    results = rpc_batch(os.environ["PAPERTRADE_ARCHIVE_RPC"], [
        call("eth_getBlockByNumber", [hex(saved["fork_block"]), False], 0),
        call("eth_call", [{"to": OLD_EXCHANGE, "data": AVAILABLE}, hex(saved["fork_block"])], 1),
        call("eth_getStorageAt", [OLD_EXCHANGE, hex(26), hex(saved["fork_block"])], 2),
        call("eth_call", [{"to": OLD_EXCHANGE, "data": "0xafdf6702"}, hex(saved["fork_block"])], 3),
        call("eth_call", [{"to": OLD_EXCHANGE, "data": "0x7d004aeb"}, hex(saved["fork_block"])], 4),
    ])
    header, getter_output = results[0], results[1]
    assert header["hash"].lower() == saved["fork_block_hash"]
    assert int(getter_output, 16) == arguments[6]
    fee_word = int(results[2], 16)
    assert fee_word & (2**128 - 1) == int(results[3], 16)
    assert fee_word >> 128 == int(results[4], 16)
    ARCHIVE.write_text(json.dumps({
        "source_tx": saved["source_tx"],
        "source_block": saved["fork_block"] + 1,
        "source_transaction_index": 0,
        "prestate_block": saved["fork_block"],
        "prestate_block_hash": saved["fork_block_hash"],
        "exchange": OLD_EXCHANGE,
        "getter_selector": AVAILABLE,
        "getter_output": getter_output,
        "settlement_selector": SETTLEMENT,
        "settlement_argument_7": str(arguments[6]),
        "fee_slot_26": results[2],
        "staker_fee_getter_selector": "0xafdf6702",
        "staker_fee_getter_output": results[3],
        "dev_fee_getter_selector": "0x7d004aeb",
        "dev_fee_getter_output": results[4],
    }, indent=2) + "\n")
    return verify_archive()


def verify_archive():
    saved, arguments, _ = history()
    capture = json.loads(ARCHIVE.read_text())
    assert capture["source_tx"] == saved["source_tx"]
    assert capture["source_block"] == saved["fork_block"] + 1
    assert capture["source_transaction_index"] == 0
    assert capture["prestate_block"] == saved["fork_block"]
    assert capture["prestate_block_hash"] == saved["fork_block_hash"]
    assert capture["exchange"] == OLD_EXCHANGE
    assert capture["getter_selector"] == AVAILABLE
    assert capture["settlement_selector"] == SETTLEMENT
    assert int(capture["getter_output"], 16) == arguments[6]
    assert int(capture["settlement_argument_7"]) == arguments[6]
    fee_word = int(capture["fee_slot_26"], 16)
    assert capture["staker_fee_getter_selector"] == "0xafdf6702"
    assert capture["dev_fee_getter_selector"] == "0x7d004aeb"
    assert fee_word & (2**128 - 1) == int(capture["staker_fee_getter_output"], 16)
    assert fee_word >> 128 == int(capture["dev_fee_getter_output"], 16)
    return capture


def model(pnl, gain_rate_percent, loss_rate_percent, available):
    margin = 500
    rate = gain_rate_percent if pnl > 0 else loss_rate_percent if pnl < 0 else 0
    fee = abs(pnl) * (rate * 10**16) // WAD
    if pnl > 0:
        if available >= pnl + fee:
            return [margin, pnl - fee, 0, 0, fee // 2, fee - fee // 2], 0
        immediate = min(pnl, available)
        queued = pnl - immediate
        return [margin, immediate, queued, 0, 0, 0], queued
    if pnl < 0:
        assert margin + pnl >= 0
        return [margin + pnl, 0, 0, 0, fee // 2, fee - fee // 2], 0
    return [margin, 0, 0, 0, 0, 0], 0


def modeled_cases():
    return [
        {
            "name": name,
            "margin": 500,
            "adjusted_pnl": pnl,
            "gain_rate_percent": gain_rate,
            "loss_rate_percent": loss_rate,
            "available": available,
            "return_words": words,
            "queued": queued,
        }
        for name, pnl, gain_rate, loss_rate, available in CASES
        for words, queued in [model(pnl, gain_rate, loss_rate, available)]
    ]


def run():
    saved, _, runtime_sha256 = history()
    verify_archive()
    solc = shutil.which("solc")
    assert solc, "local solc is required"
    with tempfile.TemporaryDirectory(prefix="papertrade-older-settlement-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc)
            + '\noffline = true\nvia_ir = true\noptimizer = true\n'
            + 'fs_permissions = [{ access = "read", path = "./runtime" }]\n'
        )
        shutil.copyfile(SOURCE, project / "test" / "OlderSettlement.t.sol")
        shutil.copyfile(RUNTIME, project / "runtime" / "Library.hex")
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True, check=False, text=True, timeout=60,
        )
    output = result.stdout + "\n" + result.stderr
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    if result.returncode or passed != TEST_NAMES:
        raise RuntimeError("older settlement replay failed: " + output[-5000:])
    REPLAY.write_text(json.dumps({
        "pin": 48_902_346,
        "source_tx": saved["source_tx"],
        "runtime_sha256": runtime_sha256,
        "test_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "test_names": sorted(passed),
        "forge_result": "9 passed, 0 failed",
        "cases": modeled_cases(),
        "limits": [
            "The sampled 47,572,843 transaction identifies the argument; a separate 42,770,131 trace proves a zero-available enqueue during a queue backlog.",
            "The nine exact-runtime tests use a constructed 500-unit margin and an empty queue in a delegatecall harness.",
            "Exchange caller reachability, real fee avoidance, and Core delivery are not proved by this replay.",
        ],
    }, indent=2) + "\n")
    return verify_local()


def verify_local():
    saved, _, runtime_sha256 = history()
    verify_archive()
    replay = json.loads(REPLAY.read_text())
    assert replay["pin"] == 48_902_346
    assert replay["source_tx"] == saved["source_tx"]
    assert replay["runtime_sha256"] == runtime_sha256
    assert replay["test_source_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert set(replay["test_names"]) == TEST_NAMES
    assert replay["forge_result"] == "9 passed, 0 failed"
    assert replay["cases"] == modeled_cases()
    return replay


def parse_fork_trace(output):
    matches = list(re.finditer(r"^\[PASS\] (testTight\w+)\(\) \(gas: (\d+)\)$", output, re.MULTILINE))
    assert {match.group(1) for match in matches} == set(FORK_NAMES)
    records = []
    for index, match in enumerate(matches):
        name, gas = match.group(1), int(match.group(2))
        target, credit, queued = FORK_NAMES[name]
        end = matches[index + 1].start() if index + 1 < len(matches) else len(output)
        section = output[match.end():end]
        library = re.search(r"::aa31b143\(([0-9a-f]+)\).*?← \[Return\] (0x[0-9a-f]+)", section, re.DOTALL)
        assert library, name
        input_hex, output_hex = library.groups()
        arguments = [int(input_hex[i:i + 64], 16) for i in range(0, len(input_hex), 64)]
        values = [int(output_hex[i:i + 64], 16) for i in range(2, len(output_hex), 64)]
        gain = 331_156_061_910_525_405
        fee = gain - credit - queued
        assert len(arguments) == 7 and len(values) == 6
        assert arguments[0] == 15 and arguments[2:7] == [25 * WAD, gain, 2 * 10**16, 2 * 10**16, target]
        assert values == [25 * WAD, credit, queued, 0, fee // 2, fee - fee // 2]
        event = re.search(
            r"emit TightClose\(available: (\d+).*?credited: (\d+).*?queued: (\d+).*?"
            r"feeWordBefore: (\d+).*?feeWordAfter: (\d+)", section, re.DOTALL,
        )
        assert event, name
        available, event_credit, event_queue, before, after = map(int, event.groups())
        assert (available, event_credit, event_queue) == (target, credit, queued)
        mask = 2**128 - 1
        assert (after & mask) - (before & mask) == fee // 2
        assert (after >> 128) - (before >> 128) == fee - fee // 2
        assert ("0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7" in section) == (queued > 0)
        records.append({
            "test": name, "gas": gas, "available_argument": target,
            "adjusted_pnl": gain, "credited_gain": credit, "queued_gain": queued,
            "return_words": values,
            "staker_fee_delta": fee // 2, "dev_fee_delta": fee - fee // 2,
            "enqueued_event": queued > 0,
        })
    assert "5 passed; 0 failed" in output
    return sorted(records, key=lambda record: record["test"])


def run_fork():
    history()
    verify_archive()
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    with tempfile.TemporaryDirectory(prefix="papertrade-older-settlement-fork-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "foundry.toml").write_text('[profile.default]\nsolc_version = "0.8.28"\n')
        shutil.copyfile(BASE_SOURCE, project / "test" / "DebtOpen.t.sol")
        shutil.copyfile(FORK_SOURCE, project / "test" / "OlderSettlementExchange.t.sol")
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "--fork-url", url,
             "--fork-block-number", "47721328", "--match-contract", "OlderSettlementExchangeTest",
             "--match-test", "testTight", "-vvvv"],
            capture_output=True, check=False, text=True, timeout=90,
        )
    output = result.stdout + "\n" + result.stderr
    assert url not in output
    if result.returncode:
        raise RuntimeError("older Exchange settlement fork failed: " + output[-5000:])
    records = parse_fork_trace(output)
    FORK_TRACE.write_bytes(gzip.compress(output.encode(), compresslevel=9, mtime=0))
    FORK_REPLAY.write_text(json.dumps({
        "fork_block": 47_721_328,
        "base_source_sha256": hashlib.sha256(BASE_SOURCE.read_bytes()).hexdigest(),
        "test_source_sha256": hashlib.sha256(FORK_SOURCE.read_bytes()).hexdigest(),
        "trace_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "forge_result": "5 passed, 0 failed",
        "cases": records,
        "limits": [
            "The historical fork state is retained, but signer authorization and the close price are locally constructed.",
            "Treasury slot 14 is overridden to force selected LP bankroll values; this does not show that a user can cause those values on-chain.",
            "The replay verifies internal balance, queue and fee storage, not HyperCore delivery or a profitable attack.",
        ],
    }, indent=2) + "\n")
    return verify_fork()


def verify_fork():
    saved = json.loads(FORK_REPLAY.read_text())
    trace = gzip.decompress(FORK_TRACE.read_bytes()).decode()
    assert saved["fork_block"] == 47_721_328
    assert saved["base_source_sha256"] == hashlib.sha256(BASE_SOURCE.read_bytes()).hexdigest()
    assert saved["test_source_sha256"] == hashlib.sha256(FORK_SOURCE.read_bytes()).hexdigest()
    assert saved["trace_sha256"] == hashlib.sha256(trace.encode()).hexdigest()
    assert saved["forge_result"] == "5 passed, 0 failed"
    assert saved["cases"] == parse_fork_trace(trace)
    return saved


def verify():
    local = verify_local()
    fork = verify_fork()
    return {"local": local, "fork": fork}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="capture historical archive getter")
    parser.add_argument("--run", action="store_true", help="run exact-runtime Forge tests")
    parser.add_argument("--fork-run", action="store_true", help="run five Exchange archive fork cases")
    args = parser.parse_args()
    if args.capture:
        result = capture()
    elif args.run:
        result = run()
    elif args.fork_run:
        result = run_fork()
    else:
        result = verify()
    print(json.dumps({
        "checked": "archive getter" if args.capture else result["forge_result"] if args.run or args.fork_run
        else {"local": result["local"]["forge_result"], "fork": result["fork"]["forge_result"]},
    }, indent=2))


if __name__ == "__main__":
    main()
