"""Check a later PT-01 status against saved pinned evidence and public Core reads."""

import argparse
import datetime
import decimal
import gzip
import hashlib
import json
import os
import pathlib
import urllib.request

import audit_sweep_event_census as sweep_census
from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "pt01_postpin" / "status.json"
LATER_OUT = ROOT / "artifacts" / "pt01_postpin" / "status_20261020_later.json"
CURRENT_OUT = ROOT / "artifacts" / "pt01_postpin" / "status_20261020_1703.json"
STALLED = ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz"
CORE_INFO = "https://api.hyperliquid.xyz/info"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
PENDING_SELECTOR = "0x7e4174fc"
TOPICS = {
    "requested": "0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025",
    "swept": "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696",
    "cleared": "0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e",
}


def post(url, payload):
    request = urllib.request.Request(
        url, json.dumps(payload).encode(), {"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    except (OSError, json.JSONDecodeError) as error:
        # The archive URL may contain an API key. Never include it in an error.
        raise RuntimeError(f"request failed: {type(error).__name__}") from None


def rpc(method, params):
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    response = post(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in response:
        error = response["error"]
        raise RuntimeError(f"{method} failed: {error.get('code')} {error.get('message')}")
    return response["result"]


def core(payload):
    return post(CORE_INFO, payload)


def cases():
    saved = json.loads(gzip.decompress(STALLED.read_bytes()))
    assert saved["pin"] == 48902346 and len(saved["cases"]) == 2
    return saved


def event_filter(start, end, users):
    return {
        "fromBlock": hex(start),
        "toBlock": hex(end),
        "address": EXCHANGE,
        "topics": [list(TOPICS.values()), ["0x" + user[2:].rjust(64, "0") for user in users]],
    }


def capture(path=OUT):
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    stalled = cases()
    pin_header = rpc("eth_getBlockByNumber", [hex(manifest["block"]), False])
    assert pin_header["hash"].lower() == manifest["block_hash"]
    head = rpc("eth_getBlockByNumber", ["latest", False])
    block = int(head["number"], 16)
    assert block > manifest["block"]
    users = sorted(row["user"].lower() for row in stalled["cases"])
    query = event_filter(manifest["block"] + 1, block, users)
    logs = rpc("eth_getLogs", [query])
    implementation = rpc("eth_getStorageAt", [EXCHANGE, IMPLEMENTATION_SLOT, hex(block)])
    rows = []
    for case in sorted(stalled["cases"], key=lambda row: row["user"]):
        user, proxy = case["user"].lower(), case["proxy"].lower()
        pending_call = rpc(
            "eth_call",
            [{"to": EXCHANGE, "data": PENDING_SELECTOR + user[2:].rjust(64, "0")}, hex(block)],
        )
        pending_storage = rpc(
            "eth_getStorageAt", [EXCHANGE, case["pending_slot"], hex(block)]
        )
        code = rpc("eth_getCode", [proxy, hex(block)])
        ledger = core({
            "type": "userNonFundingLedgerUpdates",
            "user": proxy,
            "startTime": int(pin_header["timestamp"], 16) * 1000,
            "endTime": (int(head["timestamp"], 16) + 1) * 1000 - 1,
        })
        spot_state = core({"type": "spotClearinghouseState", "user": proxy})
        rows.append({
            "user": user,
            "proxy": proxy,
            "pending_call": pending_call,
            "pending_storage": pending_storage,
            "proxy_code_sha256": hashlib.sha256(bytes.fromhex(code[2:])).hexdigest(),
            "post_pin_core_ledger": ledger,
            "current_core_spot_state": spot_state,
        })
    output = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "pin": manifest["block"],
        "pin_hash": manifest["block_hash"],
        "pin_header": {key: pin_header[key] for key in ("number", "hash", "timestamp")},
        "head": {key: head[key] for key in ("number", "hash", "timestamp")},
        "archive_rpc": "Hyperliquid mainnet archive JSON-RPC; credential omitted",
        "core_info": CORE_INFO,
        "event_query": query,
        "sweep_logs": logs,
        "exchange_implementation_slot": implementation,
        "cases": rows,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


def verify(path=OUT):
    saved = json.loads(path.read_text())
    stalled = cases()
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin"] == stalled["pin"] == manifest["block"]
    assert TOPICS == sweep_census.TOPICS
    assert saved["pin_hash"] == stalled["block_hash"] == manifest["block_hash"]
    assert saved["pin_header"]["hash"].lower() == manifest["block_hash"]
    assert int(saved["pin_header"]["number"], 16) == manifest["block"]
    assert int(saved["pin_header"]["timestamp"], 16) == manifest["timestamp"]
    assert saved["archive_rpc"] == "Hyperliquid mainnet archive JSON-RPC; credential omitted"
    assert saved["core_info"] == CORE_INFO
    head = saved["head"]
    head_block = int(head["number"], 16)
    assert head_block > manifest["block"] and int(head["timestamp"], 16) >= manifest["timestamp"]
    assert len(head["hash"]) == 66
    users = sorted(row["user"].lower() for row in stalled["cases"])
    assert saved["event_query"] == event_filter(manifest["block"] + 1, head_block, users)
    assert saved["sweep_logs"] == []
    assert saved["exchange_implementation_slot"].lower() == manifest["contracts"][EXCHANGE]["eip1967_slots"]["implementation"].lower()
    assert len(saved["cases"]) == 2
    assert sorted(row["user"] for row in saved["cases"]) == users
    keccak = Keccak()
    assert "0x" + keccak(b"pendingSweepWord(address)")[:4].hex() == PENDING_SELECTOR
    spot_total = decimal.Decimal(0)
    for case in stalled["cases"]:
        user, proxy = case["user"].lower(), case["proxy"].lower()
        row = next(row for row in saved["cases"] if row["user"] == user)
        assert row["proxy"] == proxy
        slot = "0x" + keccak(
            int(user, 16).to_bytes(32, "big") + (33).to_bytes(32, "big")
        ).hex()
        assert case["pending_slot"].lower() == slot
        assert row["pending_call"].lower() == row["pending_storage"].lower() == case["pending_word"].lower()
        assert row["proxy_code_sha256"] == case["derived_runtime_sha256"]
        assert row["post_pin_core_ledger"] == []
        state = row["current_core_spot_state"]
        usdc = [entry for entry in state["balances"] if entry["coin"] == "USDC" and entry["token"] == 0]
        assert len(usdc) == 1
        balance = decimal.Decimal(usdc[0]["total"])
        assert int(balance * 10**8) == (int(case["pending_word"], 16) & ((1 << 64) - 1))
        spot_total += balance
    assert spot_total == decimal.Decimal("62.150916")
    return {"head_block": head_block, "head_hash": head["hash"],
            "captured_at_utc": saved["captured_at_utc"],
            "unchanged_pending": 2, "post_pin_sweep_logs": 0,
            "post_pin_core_ledger_entries": 0, "current_spot_usdc": str(spot_total)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh later archive and public Core reads")
    parser.add_argument("--out", type=pathlib.Path, default=OUT, help="capture and verify this output path")
    args = parser.parse_args()
    if args.capture:
        capture(args.out)
    print(verify(args.out))
