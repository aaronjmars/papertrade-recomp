"""Verify the first older Exchange debt-funded position lifecycle."""

import argparse
import gzip
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile

from atlas_exchange_library import pnl_model
from atlas_older_exchange_library import (
    CLOSE,
    OLD_BATCH_PROXY,
    OLD_IMPLEMENTATION,
    OLD_PROXY,
    children,
    read_gzip,
    words,
)
from atlas_session_open_typehash import OPEN

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "deployer_scope"
ATLAS = ROOT / "atlas" / "block_48902346"
SOURCE = ART / "older_open_source.json.gz"
CLOSE_CORPUS = ART / "older_exchange_queue_traces.json.gz"
PAGES = [ART / name for name in (
    "older_batch_recent_txlist.json.gz",
    "older_batch_page2.json.gz",
    "older_batch_page3.json.gz",
)]
TEST = ART / "older_exchange_debt_open.t.sol"
RUN = ART / "older_exchange_debt_open_local.json"
TRACE = ART / "older_exchange_debt_open_forge_trace.txt.gz"
OUT = ATLAS / "older_exchange_debt_open_behavior.json"
TX = "0x07449714737e6a7a1a980e1dbd2fc2683e542ff8902e293e9b4d66c7c336cc10"
FORK_BLOCK = 47_721_328
TEST_NAMES = {
    "testBelowCreditReverts", "testExactCreditSetsFlagAndConsumesQueue",
    "testNoQueueCreditReverts", "testNonDebtOpenDebitsBalance",
    "testPartialQueueCreditLeavesRemainder", "testSecondOpenCannotReuseQueueCredit",
    "testSignatureMutationRejected", "testOpenThenCloseDebtQueuesPayout",
    "testDebtOpenCloseHarvestWithdrawToCore",
    "testDebtCloseLowerPriceQueuesProfit", "testDebtCloseHigherPriceQueuesLoss",
}


def historical_open():
    saved = read_gzip(SOURCE)
    receipt, trace = saved["receipt"], saved["trace"]
    assert saved["tx"] == TX and receipt["transactionHash"].lower() == TX
    assert int(receipt["status"], 16) == 1
    assert int(receipt["blockNumber"], 16) == FORK_BLOCK + 1
    assert trace["to"].lower() == OLD_BATCH_PROXY and not trace.get("error")
    calls = [frame for frame in children(trace)
             if frame.get("to", "").lower() == OLD_IMPLEMENTATION
             and frame.get("input", "").startswith(OPEN)]
    assert len(calls) == 1 and not calls[0].get("error")
    args = words("0x" + calls[0]["input"][10:])
    assert len(args) == 11 and args[5] == 0
    assert args[0] == int("0x057d2403654b2ba82d4d95d0e0ffa2550e8140f4", 16)
    assert args[1:5] == [1, 0, 25 * 10**18, 75]
    assert words(calls[0]["output"]) == [398_939]
    assert any(frame.get("to", "").lower() == OLD_PROXY
               and frame.get("input", "").startswith(OPEN)
               for frame in children(trace))
    bbo = [frame for frame in children(trace)
           if frame.get("to", "").lower() == "0x000000000000000000000000000000000000080e"]
    assert len(bbo) == 1 and words(bbo[0]["output"]) == [271_710, 271_720]
    assert len(receipt["logs"]) == 3
    later_closes = []
    for tx, pair in read_gzip(CLOSE_CORPUS)["transactions"].items():
        for frame in children(pair["trace"]):
            if frame.get("to", "").lower() != OLD_IMPLEMENTATION or not frame.get("input", "").startswith(CLOSE):
                continue
            close_words = words("0x" + frame["input"][10:])
            index = close_words[1] // 32
            ids = close_words[index + 1:index + 1 + close_words[index]]
            if 398_939 in ids:
                assert int(pair["receipt"]["status"], 16) == 1
                later_closes.append({"tx": tx, "block": int(pair["receipt"]["blockNumber"], 16),
                                     "position_ids": ids})
    assert later_closes == [{"tx": "0x3959528af2533bfbd9334ccebfc633a5ac7dd6f566f15f5915b0559c9b992c04",
                             "block": 47_721_622, "position_ids": [398_939, 398_938]}]
    return {
        "tx": TX, "block": FORK_BLOCK + 1, "position_id": 398_939,
        "user": "0x057d2403654b2ba82d4d95d0e0ffa2550e8140f4",
        "margin": args[3], "leverage": args[4], "use_debt": False,
        "bbo": [271_710, 271_720], "receipt_logs": len(receipt["logs"]),
        "later_historical_close": later_closes[0],
    }


def sample_opens():
    pages = []
    all_hashes = set()
    for index, path in enumerate(PAGES, 1):
        saved = read_gzip(path)
        assert saved["chain_id"] == 999 and saved["address"].lower() == OLD_BATCH_PROXY
        assert saved["page"] == index and saved["offset"] == 100 and saved["sort"] == "desc"
        assert len(saved["rows"]) == 100
        with_opens = 0
        opens = 0
        for row in saved["rows"]:
            assert row["to"].lower() == OLD_BATCH_PROXY
            assert row["hash"] not in all_hashes
            all_hashes.add(row["hash"])
            data = row["input"].lower()
            cursor = 0
            found = 0
            while (cursor := data.find(OPEN[2:], cursor)) >= 0:
                raw = data[cursor + 8:cursor + 8 + 11 * 64]
                assert len(raw) == 11 * 64
                args = [int(raw[i:i + 64], 16) for i in range(0, len(raw), 64)]
                assert args[0] < 2**160 and args[1] <= 100
                assert args[2] in (0, 1) and args[3] > 0
                assert args[5] == 0 and args[8] in (27, 28)
                found += 1
                cursor += 8
            opens += found
            with_opens += found > 0
        pages.append({"page": index, "transactions": len(saved["rows"]),
                      "transactions_with_opens": with_opens,
                      "open_payloads": opens, "use_debt_true": 0,
                      "first_block": int(saved["rows"][0]["blockNumber"]),
                      "last_block": int(saved["rows"][-1]["blockNumber"])})
    assert [row["open_payloads"] for row in pages] == [170, 147, 174]
    assert [row["transactions_with_opens"] for row in pages] == [69, 63, 76]
    return pages


def run_live():
    rpc = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    source = TEST.read_bytes()
    with tempfile.TemporaryDirectory(prefix="papertrade-debt-open-") as temp:
        root = pathlib.Path(temp)
        (root / "test").mkdir()
        (root / "test" / "DebtOpen.t.sol").write_bytes(source)
        (root / "foundry.toml").write_text('[profile.default]\nsolc_version = "0.8.28"\n')
        proc = subprocess.run(
            ["forge", "test", "--root", str(root), "--fork-url", rpc,
             "--fork-block-number", str(FORK_BLOCK), "-vvvv"],
            capture_output=True, text=True, check=False,
        )
    output = proc.stdout + proc.stderr
    assert rpc not in output
    if proc.returncode:
        raise RuntimeError(output)
    names = re.findall(r"^\[PASS\] (test\w+)\(\) \(gas: (\d+)\)$", output, re.MULTILINE)
    assert {name for name, _ in names} == TEST_NAMES and len(names) == len(TEST_NAMES)
    assert "11 passed; 0 failed; 0 skipped" in output
    TRACE.write_bytes(gzip.compress(output.encode(), mtime=0))
    RUN.write_text(json.dumps({
        "fork_block": FORK_BLOCK,
        "test_sha256": hashlib.sha256(source).hexdigest(),
        "trace_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "trace_artifact": "older_exchange_debt_open_forge_trace.txt.gz",
        "tests": [{"name": name, "gas": int(gas)} for name, gas in names],
        "suite_passed": True,
        "method": "Forge archive fork; real EIP-712 open and close signatures, constructed authorized session key and queue state; exact Exchange, Session and old library runtime codehash assertions; constructed Core response and CoreWriter boundary mocks",
    }, indent=2) + "\n")

def trace_section(trace, name):
    marker = f"[PASS] {name}()"
    assert trace.count(marker) == 1
    return trace.split(marker, 1)[1].split("[PASS]", 1)[0]


def signed(value):
    return value - 2**256 if value >= 2**255 else value


def price_case(trace, name, price, expected_queue):
    section = trace_section(trace, name)
    math = re.search(r"::82296364\(([0-9a-f]+)\).*?← \[Return\] (0x[0-9a-f]+)", section, re.DOTALL)
    queue = re.search(r"::acbc814f\(([0-9a-f]+)\).*?← \[Return\] (0x[0-9a-f]+)", section, re.DOTALL)
    assert math and queue
    args = [int(math.group(1)[i:i + 64], 16) for i in range(0, len(math.group(1)), 64)]
    output = [signed(value) for value in words(math.group(2))]
    queue_args = [int(queue.group(1)[i:i + 64], 16) for i in range(0, len(queue.group(1)), 64)]
    queued = words(queue.group(2))
    assert len(args) == 9 and len(output) == 2
    assert args[:5] == [271_715, price, 25 * 10**18, 75, 0]
    assert output == pnl_model(args)
    assert len(queue_args) == 4 and queue_args[:3] == [15, int("0x057d2403654b2ba82d4d95d0e0ffa2550e8140f4", 16), 25 * 10**18]
    assert signed(queue_args[3]) == output[1]
    assert queued == [expected_queue] and expected_queue == 25 * 10**18 + output[1]
    return {"test": name, "entry_price": args[0], "close_price": price,
            "math_input": [str(value) for value in args], "math_output": [str(value) for value in output],
            "adjusted_pnl": str(output[1]), "queued_amount": str(expected_queue)}


def withdrawal_boundary(trace):
    section = trace_section(trace, "testDebtOpenCloseHarvestWithdrawToCore")
    assert "::acbc814f(" in section and "::79810ffe(" in section
    assert "emit Harvested(" in section
    match = re.search(r"::sendRawAction\((0x[0-9a-f]+)\)", section)
    assert match and "emit WriterCall(" in section
    action = bytes.fromhex(match.group(1)[2:])
    assert len(action) == 100 and action[:4] == bytes.fromhex("01000006")
    assert int.from_bytes(action[4:36], "big") == int("0x057d2403654b2ba82d4d95d0e0ffa2550e8140f4", 16)
    assert action[36:68] == bytes(32)
    assert int.from_bytes(action[68:100], "big") == 2_500_000_000
    assert "0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75" in section
    return {"test": "testDebtOpenCloseHarvestWithdrawToCore", "raw_withdrawal_amount": 25_000_000,
            "user_balance_debit": str(25 * 10**18), "core_writer_selector": "0x17938e13",
            "action_payload": match.group(1), "action_length": len(action),
            "core_amount": 2_500_000_000, "core_withdrawal_event_checked": True,
            "hypercore_execution_or_delivery_proven": False}


def build():
    historical = historical_open()
    pages = sample_opens()
    run = json.loads(RUN.read_text())
    assert run["fork_block"] == FORK_BLOCK and run["suite_passed"] is True
    assert run["test_sha256"] == hashlib.sha256(TEST.read_bytes()).hexdigest()
    assert {case["name"] for case in run["tests"]} == TEST_NAMES
    assert len(run["tests"]) == 11 and all(case["gas"] > 0 for case in run["tests"])
    trace = gzip.decompress(TRACE.read_bytes()).decode()
    assert hashlib.sha256(trace.encode()).hexdigest() == run["trace_sha256"]
    assert run["trace_artifact"] == TRACE.name
    price_cases = [price_case(trace, "testDebtCloseLowerPriceQueuesProfit", 271_615, 25_331_156_061_910_525_405),
                   price_case(trace, "testDebtCloseHigherPriceQueuesLoss", 271_815, 24_309_938_722_558_563_201)]
    boundary = withdrawal_boundary(trace)
    return {
        "historical_open": historical,
        "bounded_batch_sample": {"pages": pages, "transactions": 300,
                                 "transactions_with_opens": 208,
                                 "open_payloads": 491, "use_debt_true": 0},
        "fork_replay": run,
        "price_cases": price_cases, "withdrawal_boundary": boundary,
        "conclusions": [
            "The signed useDebt argument controls the first older Exchange position flag at bits 232 to 239.",
            "A valid useDebt open requires queue credit at least equal to margin and consumes exactly that credit from global and user totals and the queue node; a partial node retains the remainder.",
            "A second signed open cannot reuse queue credit consumed by the first.",
            "A valid signed close of the constructed debt-funded position enqueues the flat-price 25e18 margin; harvest debits the queue and credits the ordinary user balance by 25e18.",
            "A direct 25 USDC withdrawal then debits that harvested balance to zero and calls CoreWriter with a 100-byte action for the user and 2.5 billion Core units.",
            "At two constructed close prices, the old PnL library output matches the independent integer model and the queue receives margin plus adjusted PnL.",
        ],
        "limits": [
            "The only archived open in this capture uses useDebt=false; the 491 sampled open payloads are a bounded three-page BatchExecutor sample, not a full historical census.",
            "The useDebt=true opens use a constructed session-key registration and queue node, but real signatures and exact deployed runtime bytecode. No historical useDebt=true execution is proven.",
            "The close, harvest and direct withdrawal use constructed authorization, queue, and Core precompile responses. CoreWriter is replaced with a recording mock; actual HyperCore execution and delivery are not proven.",
            "Other price and rate boundaries, real debt repayment, and full older-set liabilities remain unresolved.",
        ],
    }


def verify():
    expected = build()
    assert json.loads(OUT.read_text()) == expected
    print("Older Exchange debt lifecycle: 11 fork cases and 491 sampled opens verified")
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live:
        run_live()
        OUT.write_text(json.dumps(build(), indent=2) + "\n")
    verify()
