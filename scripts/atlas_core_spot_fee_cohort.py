#!/usr/bin/env python3
"""Compare Core spot-send fees across the captured older deposit proxy cohort."""

import collections
import gzip
import json
import pathlib

from atlas_older_proxy_core import raw
from atlas_older_proxy_core import verify as verify_proxy_core

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE = ROOT / "artifacts" / "deployer_scope" / "older_proxy_core.json.gz"
RETRIES = ROOT / "artifacts" / "deployer_scope" / "older_sweep_retry_history.json.gz"
OUT = ROOT / "atlas" / "block_48902346" / "core_spot_fee_cohort.json"
SYSTEM = "0x2000000000000000000000000000000000000000"


def saved(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def funding_mode(proxy, ledger, first_outgoing_index):
    mode = None
    for entry in ledger[:first_outgoing_index]:
        delta = entry["delta"]
        if delta.get("destination", "").lower() != proxy:
            continue
        if delta["type"] == "send":
            current = "perp_send" if delta["destinationDex"] == "" else "spot_send"
        elif delta["type"] == "spotTransfer":
            if mode == "perp_send" and delta["user"].lower() == SYSTEM:
                continue
            current = "spot_transfer"
        else:
            continue
        if mode is None:
            mode = current
    assert mode is not None, proxy
    return mode


def build():
    verify_proxy_core()
    core, retries = saved(CORE), saved(RETRIES)
    assert core["pin"] == retries["pin"] == 48_902_346
    assert core["block_hash"] == retries["block_hash"]
    fee_cases = {
        case["proxy"]: case["core"]["delivered_send"]["tx"]["hash"]
        for case in retries["cases"]
    }
    modes = collections.Counter()
    fee_by_mode = collections.Counter()
    fee_counts = collections.Counter()
    group_outgoing = []
    activation_count = 0
    later_fee_zero_after_one = []
    first_fee_rows = []
    all_sends = []

    for group in core["groups"]:
        group_sends = []
        exchange = group["exchange"]
        for row in group["rows"]:
            proxy = row["proxy"]
            ledger = row["through_pin_ledger"]
            assert ledger == sorted(ledger, key=lambda entry: entry["time"])
            activation_count += sum(
                entry["delta"]["type"] == "accountActivationGas" for entry in ledger
            )
            outgoing = [
                (index, entry)
                for index, entry in enumerate(ledger)
                if entry["delta"]["type"] == "spotTransfer"
                and entry["delta"].get("user", "").lower() == proxy
            ]
            assert outgoing, proxy
            mode = funding_mode(proxy, ledger, outgoing[0][0])
            first_fee = raw(outgoing[0][1]["delta"]["fee"])
            modes[mode] += 1
            fee_by_mode[(mode, first_fee)] += 1
            first_fee_rows.append(
                {
                    "proxy": proxy,
                    "first_captured_inbound_mode": mode,
                    "first_outgoing_fee_raw": first_fee,
                    "first_outgoing_hash": outgoing[0][1]["hash"],
                }
            )
            if first_fee == 100_000_000:
                assert proxy in fee_cases
                assert outgoing[0][1]["hash"] == fee_cases[proxy]
                assert not any(
                    entry["delta"]["type"] == "accountActivationGas" for entry in ledger
                )
                later_zero = [
                    entry["hash"]
                    for _, entry in outgoing[1:]
                    if raw(entry["delta"]["fee"]) == 0
                ]
                later_fee_zero_after_one.extend(later_zero)
            for _, entry in outgoing:
                delta = entry["delta"]
                assert delta["destination"].lower() == exchange
                fee = raw(delta["fee"])
                assert fee in (0, 100_000_000)
                fee_counts[fee] += 1
                group_sends.append(entry)
                all_sends.append(entry)
        group_outgoing.append(len(group_sends))

    assert len(first_fee_rows) == 38
    assert modes == {"spot_send": 22, "spot_transfer": 14, "perp_send": 2}
    assert fee_by_mode == {
        ("spot_send", 0): 22,
        ("spot_transfer", 0): 14,
        ("perp_send", 100_000_000): 2,
    }
    assert group_outgoing == [96, 16]
    assert fee_counts == {0: 110, 100_000_000: 2}
    assert activation_count == 12
    assert len(later_fee_zero_after_one) == 1
    assert set(fee_cases) == {
        row["proxy"] for row in first_fee_rows if row["first_outgoing_fee_raw"]
    }

    earlier_exchange_sends = sorted(
        entry["time"]
        for entry in all_sends
        if entry["delta"]["destination"].lower() == core["groups"][1]["exchange"]
    )
    fee_times = sorted(
        entry["time"]
        for entry in all_sends
        if raw(entry["delta"]["fee"]) == 100_000_000
    )
    assert [
        sum(time < fee_time for time in earlier_exchange_sends)
        for fee_time in fee_times
    ] == [13, 15]
    return {
        "pin": core["pin"],
        "block_hash": core["block_hash"],
        "proxy_count": len(first_fee_rows),
        "outgoing_spot_transfer_count": len(all_sends),
        "outgoing_by_exchange": group_outgoing,
        "fee_raw_spot_counts": {str(k): v for k, v in sorted(fee_counts.items())},
        "first_captured_inbound_mode_counts": dict(sorted(modes.items())),
        "first_outgoing_fee_by_inbound_mode": [
            {"mode": mode, "fee_raw_spot": fee, "proxy_count": count}
            for (mode, fee), count in sorted(fee_by_mode.items())
        ],
        "one_usdc_fee_cases": [
            row
            for row in first_fee_rows
            if row["first_outgoing_fee_raw"] == 100_000_000
        ],
        "later_zero_fee_transfer_after_one_usdc_fee": later_fee_zero_after_one,
        "account_activation_gas_entry_count": activation_count,
        "earlier_same_destination_transfers_before_fee_cases": [13, 15],
        "sources": {
            "core_ledger": "../../artifacts/deployer_scope/older_proxy_core.json.gz",
            "retry_trace": "../../artifacts/deployer_scope/older_sweep_retry_history.json.gz",
        },
    }


def verify():
    expected = build()
    assert json.loads(OUT.read_text()) == expected
    return expected


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true", help="rebuild the cohort summary"
    )
    args = parser.parse_args()
    if args.write:
        result = build()
        OUT.write_text(json.dumps(result, indent=2) + "\n")
    else:
        result = verify()
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "proxy_count",
                    "outgoing_spot_transfer_count",
                    "fee_raw_spot_counts",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
