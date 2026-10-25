"""Compare full public Core ledgers for successful and stalled newest perp sweeps."""

import argparse
import collections
import concurrent.futures
import datetime
import decimal
import gzip
import json
import pathlib

import audit_corewriter_rejections as rejected
import audit_perp_sweep_settlement as settled
import audit_sweep_settlement as core

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACT = ROOT / "artifacts" / "pt01_newest_fee_controls" / "full_core_ledgers.json.gz"
OUT = ATLAS / "pt01_newest_fee_controls.json"
EXCHANGE = core.EXCHANGE


def inputs():
    pairs = json.loads(gzip.decompress(settled.ARTIFACT.read_bytes()))
    failures = json.loads(gzip.decompress(rejected.ARTIFACT.read_bytes()))
    pin = json.loads(
        gzip.decompress(
            (
                ROOT
                / "artifacts"
                / "audit_sweep_event_census"
                / "stalled_sweeps.json.gz"
            ).read_bytes()
        )
    )
    successful = settled.credited_rows()
    assert settled.verify() == {
        "checked": 73,
        "unique_core_transfers": 73,
        "perp_request_outcomes": {"credited": 73, "cleared": 2},
        "findings": [],
    }
    assert pairs["pin"] == failures["pin"] == pin["pin"] == 48902346
    assert pairs["block_hash"] == failures["block_hash"] == pin["block_hash"]
    assert pin["pin_header"]["hash"].lower() == pin["block_hash"]
    controls = sorted({row["proxy"].lower() for row in successful})
    stalled = sorted({case["proxy"].lower() for case in failures["cases"]})
    assert len(successful) == 73 and len(controls) == 27 and len(stalled) == 2
    assert not set(controls) & set(stalled)
    return pairs, failures, pin, successful, controls, stalled


def capture():
    _, _, pin, _, controls, stalled = inputs()
    end_ms = (int(pin["pin_header"]["timestamp"], 16) + 1) * 1000 - 1
    proxies = controls + stalled
    ledgers = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(core.core_ledger, proxy, 0, end_ms): proxy for proxy in proxies
        }
        for future in concurrent.futures.as_completed(futures):
            proxy = futures[future]
            ledgers[proxy] = future.result()
            print(f"full Core ledgers: {len(ledgers)}/{len(proxies)}", flush=True)
    result = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "pin": pin["pin"],
        "block_hash": pin["block_hash"],
        "pin_end_ms": end_ms,
        "core_info": core.CORE_INFO,
        "core_info_type": "userNonFundingLedgerUpdates",
        "control_proxies": controls,
        "stalled_proxies": stalled,
        "ledgers": {proxy: ledgers[proxy] for proxy in proxies},
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_bytes(
        gzip.compress(
            json.dumps(result, separators=(",", ":")).encode(), compresslevel=9, mtime=0
        )
    )
    OUT.write_text(json.dumps(build(), indent=2) + "\n")
    verify()


def outgoing(ledger, proxy):
    return [
        entry
        for entry in ledger
        if entry.get("delta", {}).get("type") == "spotTransfer"
        and entry["delta"].get("token") == "USDC"
        and entry["delta"].get("user", "").lower() == proxy
    ]


def build():
    pairs, failures, pin, successful, controls, stalled = inputs()
    saved = json.loads(gzip.decompress(ARTIFACT.read_bytes()))
    assert saved["pin"] == pin["pin"] and saved["block_hash"] == pin["block_hash"]
    assert (
        saved["pin_end_ms"] == (int(pin["pin_header"]["timestamp"], 16) + 1) * 1000 - 1
    )
    assert saved["core_info"] == core.CORE_INFO
    assert saved["core_info_type"] == "userNonFundingLedgerUpdates"
    assert saved["control_proxies"] == controls and saved["stalled_proxies"] == stalled
    assert set(saved["ledgers"]) == set(controls + stalled)
    assert len(pairs["pairs"]) == len(successful) == 73
    by_proxy = {proxy: collections.defaultdict(list) for proxy in saved["ledgers"]}
    for proxy, ledger in saved["ledgers"].items():
        for entry in ledger:
            by_proxy[proxy][entry["hash"]].append(entry)
    matched_hashes = set()
    for row, pair in zip(successful, pairs["pairs"]):
        proxy = row["proxy"].lower()
        assert pair["request_tx"] == row["tx"]
        candidates = [
            entry
            for entry in pair["core_ledger"]
            if entry.get("delta", {}).get("type") == "spotTransfer"
            and entry["delta"].get("token") == "USDC"
            and entry["delta"].get("user", "").lower() == proxy
            and entry["delta"].get("destination", "").lower() == EXCHANGE
        ]
        assert len(candidates) == 1, row["tx"]
        candidate = candidates[0]
        assert candidate in by_proxy[proxy][candidate["hash"]]
        assert decimal.Decimal(candidate["delta"]["fee"]) == 0
        assert decimal.Decimal(candidate["delta"]["nativeTokenFee"]) == 0
        matched_hashes.add(candidate["hash"])
    assert len(matched_hashes) == 73
    control_rows = []
    for proxy in controls:
        ledger = saved["ledgers"][proxy]
        assert all(entry["time"] <= saved["pin_end_ms"] for entry in ledger)
        sends = outgoing(ledger, proxy)
        assert sends
        exchange_sends = [
            entry
            for entry in sends
            if entry["delta"]["destination"].lower() == EXCHANGE
        ]
        assert exchange_sends
        first = min(sends, key=lambda entry: (entry["time"], entry["hash"]))
        funding = next(
            entry
            for entry in ledger
            if entry["delta"]["type"] in {"send", "internalTransfer", "spotTransfer"}
        )
        control_rows.append(
            {
                "proxy": proxy,
                "ledger_entries": len(ledger),
                "first_recorded_funding_type": funding["delta"]["type"],
                "first_recorded_funding_hash": funding["hash"],
                "first_recorded_funding_time_ms": funding["time"],
                "first_recorded_funding_fee": funding["delta"]["fee"],
                "first_recorded_outgoing_hash": first["hash"],
                "first_recorded_outgoing_fee": first["delta"]["fee"],
                "outgoing_usdc_spot_count": len(sends),
                "outgoing_to_exchange_count": len(exchange_sends),
                "nonzero_outgoing_fees": sum(
                    decimal.Decimal(entry["delta"]["fee"]) != 0 for entry in sends
                ),
                "account_activation_gas_entries": sum(
                    entry["delta"]["type"] == "accountActivationGas" for entry in ledger
                ),
            }
        )
    stalled_rows = []
    rejected_result = rejected.verify()
    assert {case["proxy"].lower() for case in rejected_result["cases"]} == set(stalled)
    for proxy in stalled:
        ledger = saved["ledgers"][proxy]
        original = next(
            case for case in failures["cases"] if case["proxy"].lower() == proxy
        )
        assert ledger == original["account_ledger"]
        assert not outgoing(ledger, proxy)
        assert any(
            entry["delta"]["type"] == "accountClassTransfer"
            and entry["delta"]["toPerp"] is False
            for entry in ledger
        )
        funding = next(
            entry
            for entry in ledger
            if entry["delta"]["type"] in {"send", "internalTransfer", "spotTransfer"}
        )
        stalled_rows.append(
            {
                "proxy": proxy,
                "ledger_entries": len(ledger),
                "first_recorded_funding_type": funding["delta"]["type"],
                "first_recorded_funding_hash": funding["hash"],
                "first_recorded_funding_time_ms": funding["time"],
                "first_recorded_funding_fee": funding["delta"]["fee"],
                "outgoing_usdc_spot_count": 0,
                "account_class_transfer_count": sum(
                    entry["delta"]["type"] == "accountClassTransfer" for entry in ledger
                ),
                "account_activation_gas_entries": sum(
                    entry["delta"]["type"] == "accountActivationGas" for entry in ledger
                ),
            }
        )
    result = {
        "pin": saved["pin"],
        "block_hash": saved["block_hash"],
        "successful_perp_sweep_count": len(successful),
        "successful_proxy_count": len(controls),
        "matched_zero_fee_spot_transfers": len(matched_hashes),
        "stalled_proxy_count": len(stalled),
        "first_recorded_outgoing_fee_counts": dict(
            sorted(
                collections.Counter(
                    row["first_recorded_outgoing_fee"] for row in control_rows
                ).items()
            )
        ),
        "control_first_funding_fee_counts": dict(
            sorted(
                collections.Counter(
                    row["first_recorded_funding_fee"] for row in control_rows
                ).items()
            )
        ),
        "stalled_first_funding_fee_counts": dict(
            sorted(
                collections.Counter(
                    row["first_recorded_funding_fee"] for row in stalled_rows
                ).items()
            )
        ),
        "first_recorded_funding_type_counts": dict(
            sorted(
                collections.Counter(
                    row["first_recorded_funding_type"] for row in control_rows
                ).items()
            )
        ),
        "control_activation_gas_entry_count": sum(
            row["account_activation_gas_entries"] for row in control_rows
        ),
        "control_first_funding_day_counts": dict(
            sorted(
                collections.Counter(
                    datetime.datetime.fromtimestamp(
                        row["first_recorded_funding_time_ms"] / 1000, datetime.UTC
                    )
                    .date()
                    .isoformat()
                    for row in control_rows
                ).items()
            )
        ),
        "stalled_first_funding_day_counts": dict(
            sorted(
                collections.Counter(
                    datetime.datetime.fromtimestamp(
                        row["first_recorded_funding_time_ms"] / 1000, datetime.UTC
                    )
                    .date()
                    .isoformat()
                    for row in stalled_rows
                ).items()
            )
        ),
        "all_outgoing_to_exchange_count": sum(
            row["outgoing_to_exchange_count"] for row in control_rows
        ),
        "all_outgoing_usdc_spot_count": sum(
            row["outgoing_usdc_spot_count"] for row in control_rows
        ),
        "all_nonzero_outgoing_fee_count": sum(
            row["nonzero_outgoing_fees"] for row in control_rows
        ),
        "controls": control_rows,
        "stalled": stalled_rows,
        "limits": [
            "These are public non-funding Core ledger responses, not cryptographic Core state proofs.",
            "A time-zero query identifies the first returned outgoing transfer, subject to public API completeness.",
            "The two stalled proxies have no successful outgoing spot transfer through the pin, so their required transfer gas is not measured.",
            "The first inbound fee correlation does not prove the Core activation state or the payer of that fee.",
            "Fees on successful transfers do not establish the fee on a rejected transfer.",
        ],
    }
    assert result["control_first_funding_fee_counts"] == {"1.0": 27}
    assert result["stalled_first_funding_fee_counts"] == {"0.0": 2}
    assert result["first_recorded_outgoing_fee_counts"] == {"0.0": 27}
    assert result["first_recorded_funding_type_counts"] == {
        "internalTransfer": 11,
        "send": 14,
        "spotTransfer": 2,
    }
    assert result["control_activation_gas_entry_count"] == 2
    assert result["all_outgoing_to_exchange_count"] == 84
    assert result["all_outgoing_usdc_spot_count"] == 84
    assert result["all_nonzero_outgoing_fee_count"] == 0
    assert all(row["first_recorded_funding_type"] == "send" for row in stalled_rows)
    return result


def verify():
    result = build()
    assert json.loads(OUT.read_text()) == result
    print(
        "newest Core fee controls:",
        result["matched_zero_fee_spot_transfers"],
        "zero-fee matched sweeps,",
        result["first_recorded_outgoing_fee_counts"],
        "first outgoing fees",
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    capture() if args.capture else verify()
