#!/usr/bin/env python3
"""Verify signed Exchange withdrawals against logs, balances, and CoreWriter payloads."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
ARTIFACTS = ROOT / "artifacts" / "exchange_core_withdrawal"
PIN = 48902346
PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
CORE_WRITER = "0x3333333333333333333333333333333333333333"
SELECTOR = "0x8d09f23f"
SIGNATURE = "withdrawToCoreBySig(address,uint256,uint256,uint64,uint8,bytes32,bytes32)"
EVENT = "CoreWithdrawal(address,uint256,uint256)"
TOPIC = "0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75"
TRANSACTIONS = (
    (HISTORICAL, "0xb1eb49f49a19b7a786773e4be3b4fc20f201b53a8e98bac16b77902a9b0b1cd5"),
    (ARTIFACTS, "0xe3b515b06932d1f98867772b645367f3924ec239ae2e047fa0a15e3f11152e45"),
    (ARTIFACTS, "0x0f15e1a5d5bcaf5764df51439680fa8b3f748b47240d5c89c31be8d487a49a90"),
)
KECCAK = Keccak()


def words(value):
    assert value.startswith("0x") and (len(value) - 2) % 64 == 0
    return [int(value[i:i + 64], 16) for i in range(2, len(value), 64)]


def descendants(root):
    yield root
    for child in root.get("calls", []):
        yield from descendants(child)


def mapping_slot(user):
    return "0x" + KECCAK(user.to_bytes(32, "big") + (9).to_bytes(32, "big")).hex()


def core_payload(call):
    raw = bytes.fromhex(call["input"][2:])
    assert raw[:4].hex() == "17938e13"
    offset = int.from_bytes(raw[4:36], "big")
    length = int.from_bytes(raw[4 + offset:36 + offset], "big")
    payload = raw[36 + offset:36 + offset + length]
    assert len(payload) == length == 100
    return payload


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    for folder, tx in TRANSACTIONS:
        if folder != ARTIFACTS:
            continue
        for label, method, params in (
            ("calls", "debug_traceTransaction", [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
            ("receipt", "eth_getTransactionReceipt", [tx]),
            ("state_diff", "debug_traceTransaction", [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}]),
        ):
            path = ARTIFACTS / f"{tx}.{label}.json"
            if not path.exists():
                path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")


def verify():
    assert "0x" + KECCAK(SIGNATURE.encode()).hex()[:8] == SELECTOR
    assert "0x" + KECCAK(EVENT.encode()).hex() == TOPIC
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())[IMPLEMENTATION]
    assert SELECTOR in {row["selector"] for row in catalog["functions"]}
    rows = []
    for folder, tx in TRANSACTIONS:
        receipt = json.loads((folder / f"{tx}.receipt.json").read_text())
        call = json.loads((folder / f"{tx}.calls.json").read_text())
        diff = json.loads((folder / f"{tx}.state_diff.json").read_text())
        assert receipt["status"] == "0x1" and int(receipt["blockNumber"], 16) <= PIN
        withdrawal_calls = [node for node in descendants(call)
                            if node.get("type") == "CALL" and node.get("to", "").lower() == PROXY
                            and node.get("input", "")[:10] == SELECTOR]
        assert len(withdrawal_calls) == 1
        withdrawal = withdrawal_calls[0]
        args = words("0x" + withdrawal["input"][10:])
        assert len(args) == 7 and args[4] in (27, 28)
        user, raw_amount = args[:2]
        assert len(withdrawal.get("calls", [])) == 1
        implementation = withdrawal["calls"][0]
        assert implementation["type"] == "DELEGATECALL" and implementation["to"].lower() == IMPLEMENTATION
        assert implementation["input"] == withdrawal["input"]
        logs = [log for log in receipt["logs"]
                if log["address"].lower() == PROXY and log["topics"][0] == TOPIC]
        assert len(logs) == 1 and logs[0]["topics"] == [TOPIC, "0x" + user.to_bytes(32, "big").hex()]
        debit, core_amount = words(logs[0]["data"])
        assert core_amount == raw_amount * 100
        core_calls = [node for node in descendants(withdrawal)
                      if node.get("type") == "CALL" and node.get("to", "").lower() == CORE_WRITER]
        assert len(core_calls) == 1
        payload = core_payload(core_calls[0])
        assert payload[:4].hex() == "01000006"
        assert int.from_bytes(payload[16:36], "big") == user
        assert int.from_bytes(payload[-8:], "big") == core_amount
        slot = mapping_slot(user)
        pre = int(diff.get("pre", {}).get(PROXY, {}).get("storage", {}).get(slot, "0x0"), 16)
        post = int(diff.get("post", {}).get(PROXY, {}).get("storage", {}).get(slot, "0x0"), 16)
        credits = []
        for node in descendants(call):
            if node.get("type") == "CALL" and node.get("to", "").lower() == PROXY \
                    and node.get("input", "")[:10] == "0xe53e3de6":
                recipient, amount = words("0x" + node["input"][10:])
                if recipient == user:
                    credits.append(amount)
        assert pre - post == debit - sum(credits)
        rows.append({"tx": tx, "block": int(receipt["blockNumber"], 16),
                     "user": "0x" + user.to_bytes(20, "big").hex(),
                     "signed_raw_amount": str(raw_amount), "event_internal_debit": str(debit),
                     "event_core_amount": str(core_amount), "core_payload_amount": str(int.from_bytes(payload[-8:], "big")),
                     "user_balance_pre": str(pre), "user_balance_post": str(post),
                     "same_tx_reward_credits": [str(value) for value in credits],
                     "debit_less_sent_18_decimals": str(debit - core_amount * 10**10)})
    assert len(rows) == 3
    assert [int(row["debit_less_sent_18_decimals"]) for row in rows] == [10**18, 0, 0]
    result = {"pin_block": PIN, "exchange_proxy": PROXY, "implementation": IMPLEMENTATION,
              "selector_reconstructions": {SELECTOR: SIGNATURE},
              "event_catalog": [{"topic0": TOPIC, "reconstructed_signature": EVENT,
                                 "status": "observed_historical_and_recent_topic"}],
              "transaction_count": len(rows), "transactions": rows,
              "observed_path": "signed raw amount times 100 is CoreWriter payload and event core amount; event internal debit reconciles with user balance and same-transaction staking reward credits",
              "limitations": ["Three successful withdrawal calls do not establish every fee or queue branch.",
                              "The sampled extra debit correlates with a false HyperCore account-existence read; downstream fee disposition is unverified.",
                              "The reconstructed EIP-712 signature hashes cover selected successful calls; failed signature branches remain untested here."]}
    (ATLAS / "exchange_core_withdrawal_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Exchange Core withdrawal:", len(rows), "signed calls, events, CoreWriter payloads, and balances verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
