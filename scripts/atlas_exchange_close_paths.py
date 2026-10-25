#!/usr/bin/env python3
"""Reconcile sampled signed closes with Exchange balance, queue, and fee writes."""

import collections
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
MASK128 = (1 << 128) - 1


def slot(key_type, key, base):
    return f"0x{int(subprocess.run(['cast', 'index', key_type, str(key), str(base)],
                                  capture_output=True, text=True, check=True).stdout.strip(), 16):064x}"


def words(log):
    return [int(log["data"][i:i + 64], 16) for i in range(2, len(log["data"]), 64)]


def signed(value):
    return value if value < 1 << 255 else value - (1 << 256)


def direct_delta(before, after, index):
    key = f"0x{index:064x}"
    return int(after.get(key, "0x0"), 16) - int(before.get(key, "0x0"), 16)


def main():
    paths = json.loads((ATLAS / "exchange_event_paths.json").read_text())
    expected = {row["tx"]: set() for row in paths["pairs"] if row.get("inner_selector") == "0x2792e706"}
    for row in paths["pairs"]:
        if row.get("inner_selector") == "0x2792e706" and row.get("position_id"):
            expected[row["tx"]].add(row["position_id"])
    fixture = json.loads((ATLAS / "external_exchange_abi_hypermate.json").read_text())["abi"]
    topics = {entry["name"]: entry["topic0"].lower() for entry in fixture if entry["type"] == "event"}
    rows = []
    for tx, ids in sorted(expected.items()):
        receipt = json.loads((HISTORICAL / f"{tx}.receipt.json").read_text())
        diff = json.loads((HISTORICAL / f"{tx}.state_diff.json").read_text())
        before = diff["pre"][EXCHANGE]["storage"]
        after = diff["post"][EXCHANGE]["storage"]
        logs = [log for log in receipt["logs"] if log["address"].lower() == EXCHANGE]
        closes = [log for log in logs if log["topics"][0].lower() == topics["PositionClosed"]]
        aggregates = {"0x" + log["topics"][1][-40:].lower(): words(log) for log in logs
                      if log["topics"][0].lower() == topics["PositionsClosed"]}
        assert {int(log["topics"][1], 16) for log in closes} == ids
        assert len(closes) == len(aggregates) == len(ids)
        queue_delta = direct_delta(before, after, 18)
        tx_rows = []
        for log in closes:
            position_id = int(log["topics"][1], 16)
            user = "0x" + log["topics"][2][-40:].lower()
            entry = words(log)
            assert len(entry) == 5
            adjusted_pnl = signed(entry[2])
            fee = entry[4]
            position_word = int(before["0x" + format(int(slot("uint256", position_id, 10), 16) + 1, "064x")], 16)
            margin = position_word & MASK128
            balance_key = slot("address", user, 9)
            balance_before = int(before.get(balance_key, "0x0"), 16)
            balance_after = int(after.get(balance_key, "0x0"), 16)
            balance_delta = balance_after - balance_before
            aggregate = aggregates[user]
            assert len(aggregate) == 4
            assert aggregate[0] == balance_delta and aggregate[1] == balance_after
            if queue_delta > 0:
                assert len(closes) == 1 and adjusted_pnl > 0
                assert balance_delta == margin and queue_delta == adjusted_pnl - fee
                assert aggregate[2:] == [0, 0]
                case = "margin_returned_net_profit_queued"
            elif adjusted_pnl > 0:
                assert balance_delta == margin + adjusted_pnl - fee
                assert aggregate[2] + aggregate[3] == fee
                case = "margin_plus_positive_pnl_minus_fee_credited"
            elif adjusted_pnl < 0:
                assert balance_delta == margin + adjusted_pnl
                assert aggregate[2] + aggregate[3] == fee
                case = "margin_plus_negative_pnl_credited"
            else:
                assert balance_delta == margin and fee == 0
                assert aggregate[2:] == [0, 0]
                case = "margin_only_credited"
            tx_rows.append({"position_id": position_id, "user": user, "case": case,
                            "margin": margin, "exit_price": entry[0], "raw_pnl": signed(entry[1]),
                            "adjusted_pnl": adjusted_pnl, "event_fee": fee,
                            "balance_delta": balance_delta, "balance_after": balance_after,
                            "event_staker_fee": aggregate[2], "event_dev_fee": aggregate[3]})
        fee_key = f"0x{26:064x}"
        fee_before, fee_after = int(before.get(fee_key, "0x0"), 16), int(after.get(fee_key, "0x0"), 16)
        staker_delta = (fee_after & MASK128) - (fee_before & MASK128)
        dev_delta = (fee_after >> 128) - (fee_before >> 128)
        assert staker_delta == sum(row["event_staker_fee"] for row in tx_rows)
        assert dev_delta == sum(row["event_dev_fee"] for row in tx_rows)
        rows.append({"tx": tx, "queue_delta": queue_delta, "staker_fee_delta": staker_delta,
                     "dev_fee_delta": dev_delta, "positions": tx_rows})
    cases = collections.Counter(row["case"] for tx in rows for row in tx["positions"])
    result = {
        "pin": 48902346,
        "exchange": EXCHANGE,
        "sampled_transactions": len(rows),
        "sampled_positions": sum(len(row["positions"]) for row in rows),
        "case_counts": dict(sorted(cases.items())),
        "transactions": rows,
        "limits": [
            "This is a transaction-level reconciliation of nine sampled successful close events, not an exhaustive proof of all close branches.",
            "The public ABI fixture names the signed PnL and fee fields; this ledger verifies their observed arithmetic but not their economic definitions.",
            "One negative-PnL sample credits margin plus adjusted PnL while recording a nonzero fee split; the later mixed-close replay shows that the fee reduces the Tokenomics LP credit and PAPER mint basis.",
        ],
    }
    output = ATLAS / "exchange_close_paths.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}: {result['sampled_positions']} closes in {result['sampled_transactions']} transactions")


if __name__ == "__main__":
    main()
