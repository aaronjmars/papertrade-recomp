"""Check first funding and outgoing fees across 67 captured deposit proxies."""

import argparse
import collections
import datetime
import decimal
import gzip
import json
import pathlib

from audit_sweep_settlement import post_json

ROOT = pathlib.Path(__file__).resolve().parents[1]
OLDER = ROOT / "artifacts" / "deployer_scope" / "older_proxy_core.json.gz"
NEWEST = (
    ROOT / "artifacts" / "pt01_newest_fee_controls" / "full_core_ledgers.json.gz"
)
EXPLORER = "https://rpc.hyperliquid.xyz/explorer"
NEWEST_EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
CAPTURE = ROOT / "artifacts" / "pt01_funding_cohort" / "system_first_funding.json.gz"
SUMMARY = ROOT / "atlas" / "block_48902346" / "pt01_funding_cohort.json"
SYSTEM_SENDER = "0x6b9e773128f453f5c2c60935ee2de2cbc5390a24"
SPECIAL = {
    "0x5fa0a115d5f6f56d1b1c7f1df51d88adcb860a6d",
    "0x07d38b03587edade651ee1520dfb619809992337",
    "0x1e8a704179cc6221592c362daa52a341ae20084d",
    "0xf6b60cdf359af5538495831a9f2bbcada23e10e6",
}


def read_gzip(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def cohort_rows():
    older = read_gzip(OLDER)
    newest = read_gzip(NEWEST)
    assert older["pin"] == newest["pin"] == 48_902_346
    assert older["block_hash"] == newest["block_hash"]
    rows = [
        ("older", group["exchange"], row["proxy"], row["through_pin_ledger"])
        for group in older["groups"]
        for row in group["rows"]
    ]
    rows += [
        ("newest", NEWEST_EXCHANGE, proxy, ledger)
        for proxy, ledger in newest["ledgers"].items()
    ]
    assert len(rows) == 67 and len({row[2] for row in rows}) == 67
    return older, newest, rows


def first_funding(ledger, proxy):
    funding = next(
        entry
        for entry in ledger
        if entry["delta"]["type"] in {"send", "internalTransfer", "spotTransfer"}
    )
    assert funding["delta"]["destination"].lower() == proxy
    assert funding["delta"].get("token", "USDC") == "USDC"
    return funding


def first_outgoing(ledger, proxy, exchange):
    return next(
        (
            entry
            for entry in ledger
            if entry["delta"]["type"] == "spotTransfer"
            and entry["delta"].get("user", "").lower() == proxy
            and entry["delta"]["destination"].lower() == exchange
        ),
        None,
    )


def capture():
    older, _, rows = cohort_rows()
    details = {}
    for group, exchange, proxy, ledger in rows:
        funding = first_funding(ledger, proxy)
        if proxy not in SPECIAL:
            continue
        assert decimal.Decimal(funding["delta"]["fee"]) == 0
        details[proxy] = post_json(
            EXPLORER, {"type": "txDetails", "hash": funding["hash"]}
        )
    assert set(details) == SPECIAL
    payload = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "pin": older["pin"],
        "block_hash": older["block_hash"],
        "source": EXPLORER,
        "details": details,
    }
    CAPTURE.parent.mkdir(parents=True, exist_ok=True)
    CAPTURE.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )


def build():
    older, _, rows = cohort_rows()
    captured = read_gzip(CAPTURE)
    assert captured["pin"] == older["pin"]
    assert captured["block_hash"] == older["block_hash"]
    assert captured["source"] == EXPLORER
    assert set(captured["details"]) == SPECIAL
    funding_counts = collections.Counter()
    outgoing_counts = collections.Counter()
    special_rows = []
    for group, exchange, proxy, ledger in rows:
        assert ledger == sorted(ledger, key=lambda entry: entry["time"])
        funding = first_funding(ledger, proxy)
        outgoing = first_outgoing(ledger, proxy, exchange)
        fee = decimal.Decimal(funding["delta"]["fee"])
        assert fee in {0, 1}
        funding_counts[(group, str(fee))] += 1
        outgoing_fee = (
            str(decimal.Decimal(outgoing["delta"]["fee"]))
            if outgoing is not None
            else "none"
        )
        outgoing_counts[(group, outgoing_fee)] += 1
        if fee == 0:
            assert proxy in SPECIAL
            assert funding["delta"]["user"].lower() == SYSTEM_SENDER
            assert funding["delta"]["type"] == "send"
            assert outgoing_fee == ("1.0" if group == "older" else "none")
            details = captured["details"][proxy]
            tx = details["tx"]
            assert tx["hash"].lower() == funding["hash"].lower()
            assert tx["error"] is None
            assert tx["action"] == {
                "type": "SystemSendAssetAction",
                "destination": proxy,
                "fromSubAccount": None,
                "sourceDexOrSpot": None,
                "destinationDexOrSpot": 0,
                "token": 0,
                "wei": int(decimal.Decimal(funding["delta"]["amount"]) * 10**8),
            }
            special_rows.append(
                {
                    "group": group,
                    "proxy": proxy,
                    "funding_hash": funding["hash"],
                    "funding_amount_usdc": funding["delta"]["amount"],
                    "funding_fee_usdc": funding["delta"]["fee"],
                    "first_outgoing_hash": outgoing["hash"] if outgoing else None,
                    "first_outgoing_fee_usdc": (
                        outgoing["delta"]["fee"] if outgoing else None
                    ),
                }
            )
        else:
            assert proxy not in SPECIAL
            assert outgoing_fee == "0.0"
    assert funding_counts == {
        ("older", "1.0"): 36,
        ("older", "0.0"): 2,
        ("newest", "1.0"): 27,
        ("newest", "0.0"): 2,
    }
    assert outgoing_counts == {
        ("older", "0.0"): 36,
        ("older", "1.0"): 2,
        ("newest", "0.0"): 27,
        ("newest", "none"): 2,
    }
    assert len(special_rows) == 4
    return {
        "pin": older["pin"],
        "block_hash": older["block_hash"],
        "proxy_count": len(rows),
        "first_funding_fee_counts": [
            {"group": group, "fee_usdc": fee, "count": count}
            for (group, fee), count in sorted(funding_counts.items())
        ],
        "first_outgoing_fee_counts": [
            {"group": group, "fee_usdc": fee, "count": count}
            for (group, fee), count in sorted(outgoing_counts.items())
        ],
        "system_first_funding_sender": SYSTEM_SENDER,
        "system_first_funding": sorted(special_rows, key=lambda row: row["proxy"]),
        "sources": {
            "older_ledgers": "../../artifacts/deployer_scope/older_proxy_core.json.gz",
            "newest_ledgers": "../../artifacts/pt01_newest_fee_controls/full_core_ledgers.json.gz",
            "explorer": "../../artifacts/pt01_funding_cohort/system_first_funding.json.gz",
        },
    }


def verify():
    expected = build()
    assert json.loads(SUMMARY.read_text()) == expected
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="save four public explorer records")
    parser.add_argument("--write", action="store_true", help="rebuild the offline summary")
    args = parser.parse_args()
    if args.capture:
        capture()
    if args.write or args.capture:
        SUMMARY.write_text(json.dumps(build(), indent=2) + "\n")
    result = verify()
    print(json.dumps({"proxy_count": result["proxy_count"], "system_first_funding": len(result["system_first_funding"])}))


if __name__ == "__main__":
    main()
