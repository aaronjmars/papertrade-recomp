#!/usr/bin/env python3
"""Check public Core account state for the two earlier Exchanges."""

import argparse
import datetime
import gzip
import json
import pathlib

from atlas_deployer_scope import PIN
from atlas_older_proxy_core import (
    CORE_INFO,
    EXCHANGES,
    core_ledger,
    post,
    raw,
    saved_json,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
STALLED = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_exchange_core.json.gz"


def capture():
    scope, stalled = saved_json(SCOPE), saved_json(STALLED)
    assert scope["pin"] == stalled["pin"] == PIN
    assert scope["block_hash"] == stalled["block_hash"]
    pin_ms = (int(stalled["pin_header"]["timestamp"], 16) + 1) * 1000 - 1
    observed_at_ms = int(datetime.datetime.now(datetime.UTC).timestamp() * 1000)
    accounts = []
    for exchange in EXCHANGES:
        accounts.append(
            {
                "exchange": exchange,
                "after_pin_ledger": core_ledger(exchange, pin_ms + 1, observed_at_ms),
                "observed_spot_state": post(
                    {"type": "spotClearinghouseState", "user": exchange}
                ),
                "observed_perp_state": post(
                    {"type": "clearinghouseState", "user": exchange}
                ),
            }
        )
    payload = {
        "pin": PIN,
        "block_hash": scope["block_hash"],
        "pin_timestamp": stalled["pin_header"]["timestamp"],
        "pin_ms": pin_ms,
        "observed_at_ms": observed_at_ms,
        "source": CORE_INFO,
        "accounts": accounts,
    }
    OUT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    return verify()


def verify():
    scope, stalled, saved = saved_json(SCOPE), saved_json(STALLED), saved_json(OUT)
    assert saved["pin"] == scope["pin"] == stalled["pin"] == PIN
    assert saved["block_hash"] == scope["block_hash"] == stalled["block_hash"]
    assert saved["pin_timestamp"] == stalled["pin_header"]["timestamp"]
    assert saved["pin_ms"] == (int(saved["pin_timestamp"], 16) + 1) * 1000 - 1
    assert saved["source"] == CORE_INFO
    assert len(saved["accounts"]) == len(EXCHANGES)
    results = []
    for exchange, account in zip(EXCHANGES, saved["accounts"]):
        assert account["exchange"] == exchange
        assert all(
            saved["pin_ms"] < entry["time"] <= saved["observed_at_ms"]
            for entry in account["after_pin_ledger"]
        )
        assert account["after_pin_ledger"] == []
        balances = account["observed_spot_state"]["balances"]
        assert len(balances) == 1
        usdc = balances[0]
        assert usdc["coin"] == "USDC" and usdc["token"] == 0
        assert raw(usdc["hold"]) == 0
        perp = account["observed_perp_state"]
        assert perp["assetPositions"] == []
        assert raw(perp["withdrawable"]) == 0
        results.append(
            {"exchange": exchange, "spot_usdc_raw": raw(usdc["total"])}
        )
    assert [row["spot_usdc_raw"] for row in results] == [15_617_600, 326_900]
    return {"observed_at_ms": saved["observed_at_ms"], "accounts": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="refresh public Core account responses"
    )
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
