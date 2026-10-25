#!/usr/bin/env python3
"""Reconstruct newest Exchange Core spot USDC through the EVM audit pin."""

import argparse
import collections
import datetime
import decimal
import gzip
import json
import pathlib
import time
import urllib.error

from atlas_newest_scalar_accounting import verify as scalar_verify
from atlas_older_proxy_core import CORE_INFO, post

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
STALLED = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
OUT = ROOT / "artifacts" / "newest_core_assets" / "exchange_ledger.json.gz"
POSTPIN = OUT.with_name("exchange_postpin.json.gz")
PARTIAL = OUT.with_name("exchange_ledger.partial.json")
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
PIN = 48_902_346
MAX_SAFE_PAGE = 500


def ledger_raw(value):
    """Undo small decimal tails in Core ledger strings at 8-decimal precision."""
    scaled = decimal.Decimal(value) * 100_000_000
    rounded = scaled.to_integral_value(rounding=decimal.ROUND_HALF_UP)
    assert abs(scaled - rounded) <= decimal.Decimal("0.25"), value
    return int(rounded)


def saved(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def post_retry(payload):
    for attempt in range(8):
        try:
            result = post(payload)
            time.sleep(0.25)
            return result
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 7:
                raise
            time.sleep(min(60, 2 ** (attempt + 1)))
    raise AssertionError("unreachable")


def fetch_windows(start, end):
    rows = post_retry(
        {
            "type": "userNonFundingLedgerUpdates",
            "user": EXCHANGE,
            "startTime": start,
            "endTime": end,
        }
    )
    assert isinstance(rows, list)
    if len(rows) >= MAX_SAFE_PAGE:
        assert start < end, (start, end, len(rows))
        midpoint = (start + end) // 2
        yield from fetch_windows(start, midpoint)
        yield from fetch_windows(midpoint + 1, end)
    else:
        assert all(start <= row["time"] <= end for row in rows)
        yield {"from_ms": start, "to_ms": end, "entries": rows}


def capture():
    stalled = saved(STALLED)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert stalled["pin"] == manifest["block"] == PIN
    assert stalled["block_hash"] == manifest["block_hash"]
    pin_timestamp = int(stalled["pin_header"]["timestamp"], 16)
    end = (pin_timestamp + 1) * 1000 - 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if PARTIAL.exists():
        checkpoint = json.loads(PARTIAL.read_text())
        assert (
            checkpoint["pin"] == PIN
            and checkpoint["block_hash"] == manifest["block_hash"]
        )
        assert checkpoint["end_ms"] == end
        windows = checkpoint["windows"]
        cursor = windows[-1]["to_ms"] + 1
        print(f"resuming Core ledger at {cursor}", flush=True)
    else:
        windows = []
        cursor = 0
    count = sum(len(window["entries"]) for window in windows)
    for window in fetch_windows(cursor, end):
        windows.append(window)
        count += len(window["entries"])
        if len(windows) % 20 == 0:
            PARTIAL.write_text(
                json.dumps(
                    {
                        "pin": PIN,
                        "block_hash": manifest["block_hash"],
                        "end_ms": end,
                        "windows": windows,
                    },
                    separators=(",", ":"),
                )
            )
            print(f"Core ledger windows {len(windows)}, entries {count}", flush=True)
    before = datetime.datetime.now(datetime.UTC).isoformat()
    spot_state = post_retry({"type": "spotClearinghouseState", "user": EXCHANGE})
    perp_state = post_retry({"type": "clearinghouseState", "user": EXCHANGE})
    after = datetime.datetime.now(datetime.UTC).isoformat()
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "pin_timestamp": stalled["pin_header"]["timestamp"],
        "exchange": EXCHANGE,
        "source": CORE_INFO,
        "api_type": "userNonFundingLedgerUpdates",
        "safe_page_limit": MAX_SAFE_PAGE,
        "windows": windows,
        "current_observation": {
            "before_utc": before,
            "after_utc": after,
            "spot": spot_state,
            "perp": perp_state,
        },
    }
    OUT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    PARTIAL.unlink(missing_ok=True)
    return verify()


def capture_postpin():
    payload = saved(OUT)
    observation = payload["current_observation"]
    start = (int(payload["pin_timestamp"], 16) + 1) * 1000
    end = int(
        datetime.datetime.fromisoformat(observation["after_utc"]).timestamp() * 1000
    )
    windows = []
    for window in fetch_windows(start, end):
        windows.append(window)
        if len(windows) % 20 == 0:
            print(f"postpin Core ledger windows {len(windows)}", flush=True)
    POSTPIN.write_bytes(
        gzip.compress(
            json.dumps(
                {
                    "pin": PIN,
                    "block_hash": payload["block_hash"],
                    "exchange": EXCHANGE,
                    "from_ms": start,
                    "to_ms": end,
                    "windows": windows,
                },
                separators=(",", ":"),
            ).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    return verify()


def spot_delta(entry):
    delta = entry["delta"]
    kind = delta["type"]
    if kind in ("spotTransfer", "send"):
        assert delta["token"] == "USDC"
        source = delta["user"].lower()
        destination = delta["destination"].lower()
        assert (source == EXCHANGE) != (destination == EXCHANGE)
        amount = ledger_raw(delta["amount"])
        if destination == EXCHANGE:
            if kind == "send" and delta.get("destinationDex") != "spot":
                return 0
            return amount
        if kind == "send" and delta.get("sourceDex") != "spot":
            return 0
        fee = ledger_raw(delta.get("fee", "0"))
        if fee:
            assert delta.get("feeToken") == "USDC"
        return -amount - fee
    if kind == "accountClassTransfer":
        amount = ledger_raw(delta["usdc"])
        return -amount if delta["toPerp"] else amount
    if kind == "accountActivationGas":
        assert delta["token"] == "USDC"
        return -ledger_raw(delta["amount"])
    raise AssertionError((kind, entry))


def verify():
    payload = saved(OUT)
    stalled = saved(STALLED)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert payload["pin"] == stalled["pin"] == manifest["block"] == PIN
    assert payload["block_hash"] == stalled["block_hash"] == manifest["block_hash"]
    assert payload["pin_timestamp"] == stalled["pin_header"]["timestamp"]
    assert payload["exchange"] == EXCHANGE and payload["source"] == CORE_INFO
    assert payload["api_type"] == "userNonFundingLedgerUpdates"
    assert payload["safe_page_limit"] == MAX_SAFE_PAGE
    pin_sec = int(payload["pin_timestamp"], 16)
    cursor = 0
    prev_time = -1
    counts = collections.Counter()
    balance = 0
    before_second = None
    within_second = []
    for window in payload["windows"]:
        start, end = window["from_ms"], window["to_ms"]
        assert start == cursor and start <= end <= (pin_sec + 1) * 1000 - 1
        cursor = end + 1
        assert len(window["entries"]) < MAX_SAFE_PAGE
        for entry in window["entries"]:
            assert start <= entry["time"] <= end and entry["time"] >= prev_time
            prev_time = entry["time"]
            if before_second is None and entry["time"] >= pin_sec * 1000:
                before_second = balance
            balance += spot_delta(entry)
            assert balance >= 0, entry
            counts[entry["delta"]["type"]] += 1
            if entry["time"] >= pin_sec * 1000:
                within_second.append(balance)
    assert cursor == (pin_sec + 1) * 1000
    if before_second is None:
        before_second = balance
    observed = payload["current_observation"]
    usdc = [
        row
        for row in observed["spot"]["balances"]
        if row["coin"] == "USDC" and row["token"] == 0
    ]
    assert len(usdc) == 1
    scalar = scalar_verify()
    assert scalar["treasury_18"] % 10**10 == 0
    treasury_8 = scalar["treasury_18"] // 10**10
    result = {
        "entries": sum(counts.values()),
        "entry_types": dict(counts),
        "pin_second_ledger_entries": len(within_second),
        "core_usdc_before_pin_second_8": before_second,
        "core_usdc_after_pin_second_8": balance,
        "core_usdc_min_during_pin_second_8": min([before_second, *within_second]),
        "core_usdc_max_during_pin_second_8": max([before_second, *within_second]),
        "evm_treasury_18": scalar["treasury_18"],
        "core_spot_less_evm_treasury_8": balance - treasury_8,
        "current_spot_usdc_8": ledger_raw(usdc[0]["total"]),
        "current_spot_hold_8": ledger_raw(usdc[0]["hold"]),
        "current_perp_withdrawable_8": ledger_raw(observed["perp"]["withdrawable"]),
        "current_perp_positions": len(observed["perp"]["assetPositions"]),
        "current_observation_window_utc": [
            observed["before_utc"],
            observed["after_utc"],
        ],
    }
    if POSTPIN.exists():
        after_pin = saved(POSTPIN)
        assert after_pin["pin"] == PIN
        assert after_pin["block_hash"] == payload["block_hash"]
        assert after_pin["exchange"] == EXCHANGE
        assert after_pin["from_ms"] == cursor
        before_ms = int(
            datetime.datetime.fromisoformat(observed["before_utc"]).timestamp() * 1000
        )
        after_ms = int(
            datetime.datetime.fromisoformat(observed["after_utc"]).timestamp() * 1000
        )
        assert before_ms <= after_ms == after_pin["to_ms"]
        current = balance
        before_observation = None
        during_observation = []
        post_count = 0
        for window in after_pin["windows"]:
            start, end = window["from_ms"], window["to_ms"]
            assert start == cursor and start <= end <= after_ms
            assert len(window["entries"]) < MAX_SAFE_PAGE
            cursor = end + 1
            for entry in window["entries"]:
                assert start <= entry["time"] <= end and entry["time"] >= prev_time
                prev_time = entry["time"]
                if before_observation is None and entry["time"] >= before_ms:
                    before_observation = current
                current += spot_delta(entry)
                assert current >= 0
                post_count += 1
                if entry["time"] >= before_ms:
                    during_observation.append(current)
        assert cursor == after_ms + 1
        if before_observation is None:
            before_observation = current
        possible = [before_observation, *during_observation]
        assert min(possible) <= result["current_spot_usdc_8"] <= max(possible)
        result.update(
            {
                "postpin_entries": post_count,
                "current_replay_before_observation_8": before_observation,
                "current_replay_after_observation_8": current,
                "current_replay_min_observation_8": min(possible),
                "current_replay_max_observation_8": max(possible),
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-postpin", action="store_true")
    args = parser.parse_args()
    assert not (args.capture and args.capture_postpin)
    result = (
        capture()
        if args.capture
        else capture_postpin()
        if args.capture_postpin
        else verify()
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
