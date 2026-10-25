#!/usr/bin/env python3
"""Verify HyperCore execution errors for two pinned uncredited deposit sweeps."""

import argparse
import collections
import datetime
import gzip
import json
import pathlib

import audit_perp_sweep_settlement as perp
import audit_stalled_sweeps as stalled
import audit_sweep_settlement as core

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT = (
    ROOT / "artifacts" / "audit_sweep_event_census" / "corewriter_rejections.json.gz"
)
EXPLORER = "https://rpc.hyperliquid.xyz/explorer"
ERROR = "Insufficient USDC balance for token transfer gas."
CONTROL_REQUEST = "0x026c9e6452aa0b98b62ae3ab661322d83370d18a186186975b18fe75bfaa202e"


def control_row():
    rows = [row for row in perp.credited_rows() if row["tx"] == CONTROL_REQUEST]
    assert len(rows) == 1
    return rows[0]


def conversion_hash(ledger, proxy):
    rows = [
        row
        for row in ledger
        if row["delta"].get("type") == "accountClassTransfer"
        and row["delta"].get("toPerp") is False
    ]
    assert len(rows) == 1, proxy
    return rows[0]["hash"]


def capture_case(proxy, ledger, pin_ms):
    tx_hash = conversion_hash(ledger, proxy)
    details = core.post_json(EXPLORER, {"type": "txDetails", "hash": tx_hash})
    block = details["tx"]["block"]
    return {
        "proxy": proxy,
        "conversion_details": details,
        "execution_block": core.post_json(
            EXPLORER, {"type": "blockDetails", "height": block}
        ),
        "user_details": core.post_json(
            EXPLORER, {"type": "userDetails", "user": proxy}
        ),
        "account_ledger": core.core_ledger(proxy, 0, pin_ms),
    }


def capture():
    saved = json.loads(gzip.decompress(stalled.ARTIFACT.read_bytes()))
    pin_ms = (int(saved["pin_header"]["timestamp"], 16) + 1) * 1000 - 1
    cases = [
        capture_case(row["proxy"], row["core_ledger"], pin_ms) for row in saved["cases"]
    ]
    row = control_row()
    credited = json.loads(gzip.decompress(perp.ARTIFACT.read_bytes()))
    pairs = [
        pair for pair in credited["pairs"] if pair["request_tx"] == CONTROL_REQUEST
    ]
    assert len(pairs) == 1
    control = capture_case(row["proxy"], pairs[0]["core_ledger"], pin_ms)
    payload = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "pin": saved["pin"],
        "block_hash": saved["block_hash"],
        "source": {"core_explorer": EXPLORER, "core_info": core.CORE_INFO},
        "cases": cases,
        "control_request_tx": CONTROL_REQUEST,
        "control": control,
    }
    ARTIFACT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )


def action_bytes(writer_input):
    assert writer_input[:10].lower() == "0x17938e13"
    assert int(writer_input[10:74], 16) == 32
    size = int(writer_input[74:138], 16)
    assert size in (68, 100)
    return writer_input[138 : 138 + size * 2].lower()


def assert_spot_send(tx, proxy, amount, error):
    assert tx["user"].lower() == proxy
    assert tx["action"] == {
        "type": "SystemSpotSendAction",
        "destination": core.EXCHANGE,
        "token": 0,
        "wei": amount,
    }
    assert tx["error"] == error


def check_execution(record, proxy, amount, perp_raw, error, core_ledger):
    assert record["proxy"] == proxy
    conversion = record["conversion_details"]["tx"]
    assert record["conversion_details"]["type"] == "txDetails"
    assert conversion["hash"] == conversion_hash(core_ledger, proxy)
    assert conversion["user"].lower() == proxy
    assert conversion["action"] == {
        "type": "SystemUsdClassTransferAction",
        "ntl": perp_raw,
        "toPerp": False,
    }
    assert conversion["error"] is None
    block = record["execution_block"]["blockDetails"]
    assert record["execution_block"]["type"] == "blockDetails"
    assert block["height"] == conversion["block"]
    assert block["numTxs"] == len(block["txs"])
    assert block["txs"].count(conversion) == 1
    sends = [
        tx
        for tx in block["txs"]
        if tx["user"].lower() == proxy
        and tx["action"]["type"] == "SystemSpotSendAction"
    ]
    assert len(sends) == 1
    assert_spot_send(sends[0], proxy, amount, error)
    return sends[0]


def verify():
    data = json.loads(gzip.decompress(ARTIFACT.read_bytes()))
    stalled_data = json.loads(gzip.decompress(stalled.ARTIFACT.read_bytes()))
    assert data["pin"] == stalled_data["pin"] == 48902346
    assert data["block_hash"] == stalled_data["block_hash"]
    assert data["source"] == {"core_explorer": EXPLORER, "core_info": core.CORE_INFO}
    assert len(data["cases"]) == len(stalled_data["cases"]) == 2
    results = []
    for record, saved in zip(data["cases"], stalled_data["cases"]):
        first, last = stalled.stalled_rows()[len(results)]
        proxy = saved["proxy"]
        first_actions = [
            action_bytes(x) for x in stalled.writer_actions(saved["first_trace"])
        ]
        assert len(first_actions) == 2
        assert first_actions[0][:8] == "01000007"
        assert int(first_actions[0][8:72], 16) == first["perp_raw"]
        assert int(first_actions[0][72:136], 16) == 0
        assert first_actions[1][:8] == "01000006"
        amount = first["spot_raw"] + 100 * first["perp_raw"]
        assert int(first_actions[1][8:72], 16) == int(core.EXCHANGE, 16)
        assert int(first_actions[1][72:136], 16) == 0
        assert int(first_actions[1][136:200], 16) == amount
        failed = check_execution(
            record, proxy, amount, first["perp_raw"], ERROR, saved["core_ledger"]
        )
        assert not any(
            x["delta"].get("type") == "spotTransfer"
            and x["delta"].get("user", "").lower() == proxy
            and x["delta"].get("destination", "").lower() == core.EXCHANGE
            for x in saved["core_ledger"]
        )
        history = record["user_details"]["txs"]
        assert record["user_details"]["type"] == "userDetails"
        assert history and history[0]["user"].lower() == proxy
        last_amount = last["spot_raw"] + 100 * last["perp_raw"]
        assert_spot_send(history[0], proxy, last_amount, ERROR)
        assert history[0]["time"] >= int(saved["last_header"]["timestamp"], 16) * 1000
        assert (
            history[0]["time"] < (int(saved["last_header"]["timestamp"], 16) + 2) * 1000
        )
        counts = collections.Counter(
            (tx["action"]["type"], tx["error"])
            for tx in history
            if tx["action"]["type"] == "SystemSpotSendAction"
        )
        error_count = counts[("SystemSpotSendAction", ERROR)]
        queued_count = counts[("SystemSpotSendAction", None)]
        assert error_count == queued_count
        assert error_count >= 1
        assert failed in record["execution_block"]["blockDetails"]["txs"]
        ledger = record["account_ledger"]
        assert ledger
        first_funding = ledger[0]["delta"]
        assert first_funding["destination"].lower() == proxy
        assert first_funding["token"] == "USDC"
        assert first_funding["destinationDex"] == ""
        assert first_funding["fee"] == "0.0"
        results.append(
            {
                "proxy": proxy,
                "first_rejected_core_tx": failed["hash"],
                "last_rejected_core_tx": history[0]["hash"],
                "rejected_send_executions_in_bounded_history": error_count,
                "queued_sends_in_bounded_history": queued_count,
                "core_error": ERROR,
            }
        )
    assert data["control_request_tx"] == CONTROL_REQUEST
    row = control_row()
    credited = json.loads(gzip.decompress(perp.ARTIFACT.read_bytes()))
    pair = next(x for x in credited["pairs"] if x["request_tx"] == CONTROL_REQUEST)
    amount = row["spot_raw"] + 100 * row["perp_raw"]
    success = check_execution(
        data["control"],
        row["proxy"],
        amount,
        row["perp_raw"],
        None,
        pair["core_ledger"],
    )
    assert any(x["hash"] == success["hash"] for x in pair["core_ledger"])
    return {"cases": results, "control_core_tx": success["hash"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture", action="store_true", help="refresh public Core explorer evidence"
    )
    args = parser.parse_args()
    if args.capture:
        capture()
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
