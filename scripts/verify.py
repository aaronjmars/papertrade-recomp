#!/usr/bin/env python3
"""Offline checks for the saved Papertrade bytecode and accounting traces."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
HIST = ROOT / "artifacts" / "historical"
REPLAYS = HIST / "replays"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
CLOSE_TOPIC = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
QUEUE_TOPIC = "0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7"
QUEUED_WINS = [
    "0x3bc7029ee0d72c5dbacfb74dddc183ddb6206adca6ed702014eb90c28cf2d39e",
    "0xc7ba4aaf1bdda8e24c2c8a228e315f39a879e7c9c87786eb260fa07c09b99940",
    "0x1fc54a082055d35c0b79b6fc5f6c2a7004840531f5bcb9b6ec4450a93be2384f",
]
SOLVENT_WINS = [
    "0xe3a26c590c7b0be9e26e25b2e8fdf797be800b92131c229b5148c7405f69e33d",
    "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5",
]
HARVEST = "0x4214fa14d9c5bf46fade1c7f3ca8d242baefaa52426395b1840f43b626ee8a99"
SLOT_3 = "0x" + format(3, "064x")
SLOT_18 = "0x" + format(18, "064x")
SLOT_22 = "0x" + format(22, "064x")
SLOT_26 = "0x" + format(26, "064x")
SLOT_27 = "0x" + format(27, "064x")
MODULUS = 1 << 256
USD = 10**18


def read(path):
    return json.loads(path.read_text())


def words(data):
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def calls(node):
    yield node
    for child in node.get("calls", []):
        yield from calls(child)


def calls_to(node, address, selector):
    return [c for c in calls(node) if c.get("to", "").lower() == address and c.get("input", "")[:10] == selector]


def slot_delta(diff, address, slot, signed=False):
    pre = int(diff.get("pre", {}).get(address, {}).get("storage", {}).get(slot, "0x0"), 16)
    post = int(diff.get("post", {}).get(address, {}).get("storage", {}).get(slot, "0x0"), 16)
    raw = (post - pre) % MODULUS
    return raw - MODULUS if signed and raw >= MODULUS // 2 else raw


def tx_files(tx):
    return (read(HIST / f"{tx}.calls.json"), read(HIST / f"{tx}.receipt.json"),
            read(HIST / f"{tx}.state_diff.json"))



def main():
    snapshots = sorted((ROOT / "artifacts").glob("*block*/snapshot.json"))
    assert snapshots, "bytecode snapshot missing"
    latest = read(snapshots[-1])
    states = read(HIST / "accounting_states.json")
    for label in ("exchange", "tokenomics"):
        expected = latest["contracts"][label]["implementation"]["sha256"]
        for block in (48170000, 48173881, 48901469):
            assert states["historical_implementations"][f"{label}_{block}"]["runtime_sha256"] == expected
    by_block = {row["block"]: row for row in states["states"]}
    assert int(by_block[48173880]["total_queued"]) == 0
    for block in (48170000, 48173880, 48173890, 48899300, 48901469, 48902346):
        row = by_block[block]
        assert int(row["total_queued"]) == 0
        assert int(row["tracked_lp"]) == int(row["lp_bankroll_available"])
        assert int(row["staker_excess"]) == int(row["exchange_staker_excess"])
    assert int(by_block[48173887]["lp_bankroll_available"]) == 0
    assert int(by_block[48173889]["lp_bankroll_available"]) == 0
    assert int(by_block[48173889]["queue_harvest_available"]) == 400_296_219_202_209_635_129
    assert int(by_block[48899300]["tracked_lp"]) - int(by_block[48899300]["staker_cap"]) == int(by_block[48899300]["staker_excess"])

    scan = read(HIST / "queue_scan.json")
    assert {event["transaction_hash"] for event in scan["events"]} == set(QUEUED_WINS)
    queued_total = 0
    for tx in QUEUED_WINS:
        call, receipt, diff = tx_files(tx)
        amount_logs = [words(log["data"])[0] for log in receipt["logs"]
                       if log["address"].lower() == EXCHANGE and log["topics"][0] == QUEUE_TOPIC]
        close_calls = calls_to(call, TOKENOMICS, "0xed722c96")
        assert len(amount_logs) == len(close_calls) == 1
        amount = amount_logs[0]
        args = [int(close_calls[0]["input"][i:i + 64], 16) for i in range(10, len(close_calls[0]["input"]), 64)]
        assert args[1] == amount and args[2:] == [0, 0]
        assert slot_delta(diff, TOKENOMICS, SLOT_3, signed=True) == -amount
        assert slot_delta(diff, EXCHANGE, SLOT_18) == amount
        queued_total += amount
    assert queued_total == 22_871_826_547_055_470_767
    assert int(by_block[48173887]["total_queued"]) == queued_total
    assert int(by_block[48173887]["tracked_lp"]) == -queued_total

    close, _, close_diff = tx_files("0x20ee69d9f4191bff17d45a850a584d5803ca477986fd1684af985765d64d794b")
    loss_args = [int(close_calls[0]["input"][i:i + 64], 16) for close_calls in [calls_to(close, TOKENOMICS, "0xed722c96")] for i in range(10, len(close_calls[0]["input"]), 64)]
    assert loss_args[1] == 0 and loss_args[2] == loss_args[3] == 400_296_219_202_209_635_129
    assert slot_delta(close_diff, TOKENOMICS, SLOT_3, signed=True) == loss_args[3]
    harvest, _, harvest_diff = tx_files(HARVEST)
    assert not calls_to(harvest, TOKENOMICS, "0xed722c96")
    assert not harvest_diff.get("post", {}).get(TOKENOMICS, {}).get("storage", {})
    assert int(by_block[48173890]["total_queued"]) == 0
    assert int(by_block[48173890]["tracked_lp"]) == loss_args[3] - queued_total

    solvent = []
    for tx in SOLVENT_WINS:
        call, receipt, diff = tx_files(tx)
        winners = [words(log["data"]) for log in receipt["logs"]
                   if log["address"].lower() == EXCHANGE and log["topics"][0] == CLOSE_TOPIC
                   and words(log["data"])[4] > 0 and words(log["data"])[2] < MODULUS // 2]
        on_close = [[int(c["input"][i:i + 64], 16) for i in range(10, len(c["input"]), 64)]
                    for c in calls_to(call, TOKENOMICS, "0xed722c96")]
        assert len(winners) == 1
        gross, fee = winners[0][2], winners[0][4]
        assert fee > 0 and gross > fee
        assert sum(args[1] for args in on_close) == gross
        expected_delta = sum(args[3] - args[1] for args in on_close)
        assert slot_delta(diff, TOKENOMICS, SLOT_3, signed=True) == expected_delta
        solvent.append({"tx": tx, "gross_win_usd": str(gross), "fee_usd": str(fee), "cursor_debit_usd": str(gross)})

    baseline = read(REPLAYS / "liquidation_baseline.calls.json")
    override = read(REPLAYS / "liquidation_queue_override.calls.json")
    base_losses = [[int(c["input"][i:i + 64], 16) for i in range(10, len(c["input"]), 64)]
                   for c in calls_to(baseline, TOKENOMICS, "0x0efdf838")]
    queue_losses = [[int(c["input"][i:i + 64], 16) for i in range(10, len(c["input"]), 64)]
                    for c in calls_to(override, TOKENOMICS, "0x0efdf838")]
    assert len(base_losses) == len(queue_losses) == 2
    for base, queued in zip(base_losses, queue_losses):
        assert base[:4] == queued[:4] and base[2] == 1
        assert base[4] * 100 == base[3] * 98
        assert queued[4] == queued[3]
    base_diff = read(REPLAYS / "liquidation_baseline.state_diff.json")
    queue_diff = read(REPLAYS / "liquidation_queue_override.state_diff.json")
    assert slot_delta(base_diff, TOKENOMICS, SLOT_3) == sum(a[4] for a in base_losses)
    assert slot_delta(queue_diff, TOKENOMICS, SLOT_3) == sum(a[4] for a in queue_losses)
    assert slot_delta(queue_diff, EXCHANGE, SLOT_27) == sum(a[3] for a in queue_losses)
    assert slot_delta(base_diff, EXCHANGE, SLOT_27) == 0

    real_queue_push = read(REPLAYS / "push_during_real_queue.calls.json")
    real_queue_diff = read(REPLAYS / "push_during_real_queue.state_diff.json")
    getter = calls_to(real_queue_push, TOKENOMICS, "0xae745703")
    assert len(getter) == 1 and int(getter[0]["output"], 16) == 0
    assert not real_queue_diff.get("post", {}).get(EXCHANGE, {}).get("storage", {})

    valid_queue_push = read(REPLAYS / "push_real_queue_with_surplus_cursor.calls.json")
    valid_queue_diff = read(REPLAYS / "push_real_queue_with_surplus_cursor.state_diff.json")
    valid_getter = calls_to(valid_queue_push, TOKENOMICS, "0xae745703")
    valid_distribution = calls_to(valid_queue_push, TOKENOMICS, "0xc218c676")
    synthetic_excess = 100 * USD
    assert valid_getter and int(valid_getter[0]["output"], 16) == synthetic_excess
    assert len(valid_distribution) == 1 and int(valid_distribution[0]["input"][10:74], 16) == synthetic_excess
    assert slot_delta(valid_queue_diff, TOKENOMICS, SLOT_3, signed=True) == -synthetic_excess
    assert slot_delta(valid_queue_diff, EXCHANGE, SLOT_18) == synthetic_excess
    assert slot_delta(valid_queue_diff, EXCHANGE, SLOT_22) == 0

    amounts = []
    for label in ("push_surplus_baseline", "push_surplus_queue_override"):
        call = read(REPLAYS / f"{label}.calls.json")
        diff = read(REPLAYS / f"{label}.state_diff.json")
        getter = calls_to(call, TOKENOMICS, "0xae745703")
        distribution = calls_to(call, TOKENOMICS, "0xc218c676")
        assert getter and len(distribution) == 1
        excess = int(getter[0]["output"], 16)
        distributed_lp = int(distribution[0]["input"][10:74], 16)
        assert excess == distributed_lp == 2_056_911_227_408_759_981_977
        assert slot_delta(diff, TOKENOMICS, SLOT_3, signed=True) == -excess
        fee_pre = int(diff["pre"][EXCHANGE]["storage"][SLOT_26], 16) % (1 << 128)
        fee_post = int(diff["post"][EXCHANGE]["storage"][SLOT_26], 16) % (1 << 128)
        assert fee_post == 0
        allocated = excess + fee_pre
        if label.endswith("baseline"):
            assert slot_delta(diff, EXCHANGE, SLOT_22) == allocated
            assert slot_delta(diff, EXCHANGE, SLOT_18) == 0
        else:
            assert slot_delta(diff, EXCHANGE, SLOT_18) == allocated
            assert slot_delta(diff, EXCHANGE, SLOT_22) == 0
        amounts.append(allocated)
    assert amounts[0] == amounts[1] == 2_127_305_073_090_337_016_438

    report = {
        "bytecode_match_before_launch_and_now": True,
        "queued_wins": {"count": 3, "queued_total_usd_wei": str(queued_total), "cursor_delta_usd_wei": str(-queued_total), "harvest_double_debit": False},
        "solvent_wins": solvent,
        "queue_live_liquidation_replay": {"forfeited_margin_usd_wei": str(sum(a[3] for a in queue_losses)), "lp_credit_usd_wei": str(sum(a[4] for a in queue_losses)), "side_bucket_delta_usd_wei": str(slot_delta(queue_diff, EXCHANGE, SLOT_27))},
        "staker_push": {"real_queue_allocated_usd_wei": "0", "surplus_lp_usd_wei": str(2_056_911_227_408_759_981_977), "fee_reserve_usd_wei": str(amounts[0] - 2_056_911_227_408_759_981_977), "total_allocated_usd_wei": str(amounts[0]), "cursor_debit_usd_wei": str(2_056_911_227_408_759_981_977), "synthetic_queue_allocation_is_queued": True, "valid_queue_synthetic_surplus_queued_usd_wei": str(synthetic_excess)},
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
