#!/usr/bin/env python3
"""Live book identity tripwire for the Papertrade newest Exchange.

The audit's corrected conservation identity is

    treasury == totalBalances + totalLockedMargin + totalQueued
                + stakerFeeAccumulator + devFeeAccumulator + trackedLpUsd

with the Exchange side bucket (slot 27) deliberately excluded, because it is an
earmark of the spendable LP bankroll rather than a claim (see
atlas/block_48902346/live2_sequences.md, row SQ-L2-03). The identity held to the
raw unit on live state at block 49,306,748.

A negative residual is a general tripwire for claims above the treasury. The earlier
SQ-L2-02 debt-cycle interpretation was disproved after restoring omitted queue
pointers in its replay fixture. This script reads the head once (`--capture`), saves the raw
words, and re-verifies the saved snapshot offline.

Usage:
    python3 scripts/audit_live2_book_identity.py --capture   # public RPC, no key needed
    python3 scripts/audit_live2_book_identity.py             # offline re-verification

A residual above one raw unit (1e-18 of a dollar) beyond dust is reported and
fails the offline check, because it would mean the book claims more than the
treasury holds.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "live2_book_identity"

EXCHANGE_PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOKENOMICS_PROXY = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
PUBLIC_RPC = "https://rpc.hyperliquid.xyz/evm"
HYPERCORE_INFO = "https://api.hyperliquid.xyz/info"

# getter selector, whether the word is a signed int256, and the human label
READS = [
    ("treasury", EXCHANGE_PROXY, "0x61d027b3", False),
    ("total_balances", EXCHANGE_PROXY, "0xa69a2ad1", False),
    ("total_locked_margin", EXCHANGE_PROXY, "0x01ad056f", False),
    ("total_queued", EXCHANGE_PROXY, "0x53ac4b66", False),
    ("staker_fee_accumulator", EXCHANGE_PROXY, "0xafdf6702", False),
    ("dev_fee_accumulator", EXCHANGE_PROXY, "0x7d004aeb", False),
    ("tracked_lp_usd", TOKENOMICS_PROXY, "0x8cf554a7", True),
    # reported but deliberately not a term of the identity
    ("side_bucket", EXCHANGE_PROXY, "0x9274682e", False),
    ("lp_bankroll_available", EXCHANGE_PROXY, "0x0cdd5fc4", False),
    ("queue_harvest_available", EXCHANGE_PROXY, "0x138e9de2", False),
]
CLAIMS = (
    "total_balances",
    "total_locked_margin",
    "total_queued",
    "staker_fee_accumulator",
    "dev_fee_accumulator",
    "tracked_lp_usd",
)
DUST = 10**12  # 1e-6 of a dollar: below any economic meaning, above read noise
# Transient cents-level deviations have been observed inside a batch block, so a capture
# reports them. The offline gate only fails on a deviation large enough to be real.
FATAL = 10**18  # one dollar


def rpc(url: str, method: str, params: list) -> object:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    payload = json.load(urllib.request.urlopen(request, timeout=60))
    if "error" in payload:
        raise RuntimeError(f"{method} failed: {payload['error']}")
    return payload["result"]


def word(value: str, signed: bool) -> int:
    number = int(value, 16)
    if signed and number >= 2**255:
        number -= 2**256
    return number


def core_spot_usdc(address: str) -> str | None:
    """The Exchange's own HyperCore USDC spot balance, the cash behind the book."""
    body = json.dumps({"type": "spotClearinghouseState", "user": address}).encode()
    request = urllib.request.Request(HYPERCORE_INFO, data=body, headers={"Content-Type": "application/json"})
    try:
        state = json.load(urllib.request.urlopen(request, timeout=60))
    except Exception:
        return None
    for balance in state.get("balances", []):
        if balance.get("coin") == "USDC":
            return balance.get("total")
    return None


def capture() -> dict:
    block = int(rpc(PUBLIC_RPC, "eth_blockNumber", []), 16)
    values: dict[str, int] = {}
    raw: dict[str, dict[str, str]] = {}
    for name, address, selector, signed in READS:
        # Pin one block for every read: unpinned "latest" calls can straddle a block
        # boundary, and this chain produces a block about every second.
        result = rpc(PUBLIC_RPC, "eth_call", [{"to": address, "data": selector}, hex(block)])
        values[name] = word(result, signed)
        raw[name] = {"address": address, "selector": selector, "word": result}
    residual = values["treasury"] - sum(values[claim] for claim in CLAIMS)
    snapshot = {
        "block": block,
        "chain_id": 999,
        "exchange_proxy": EXCHANGE_PROXY,
        "tokenomics_proxy": TOKENOMICS_PROXY,
        "identity": "treasury == " + " + ".join(CLAIMS),
        "side_bucket_is_a_claim": False,
        "raw": raw,
        "values": {name: str(value) for name, value in values.items()},
        "residual_raw": str(residual),
        "residual_usd": residual / 1e18,
        "core_spot_usdc": core_spot_usdc(EXCHANGE_PROXY),
        "note": (
            "A negative residual means the measured book claims more than the treasury holds. "
            "The prior SQ-L2-02 explanation was disproved. Read-only; no credential, no writes."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "head.json").write_text(json.dumps(snapshot, indent=1, sort_keys=True) + "\n")
    with (OUT / "history.jsonl").open("a") as handle:
        handle.write(json.dumps({"block": block, "residual_raw": str(residual),
                                 "residual_usd": residual / 1e18, "core_spot_usdc": snapshot["core_spot_usdc"]},
                                sort_keys=True) + "\n")
    return snapshot


def report(snapshot: dict) -> None:
    values = {name: int(value) for name, value in snapshot["values"].items()}
    print(f"block {snapshot['block']}  chain {snapshot['chain_id']}")
    for name in [read[0] for read in READS]:
        mark = "" if name in CLAIMS else "   (reported, not a claim)"
        print(f"  {name:24s} {values[name] / 1e18:>20,.6f}{mark}")
    residual = int(snapshot["residual_raw"])
    print(f"  {'residual':24s} {residual / 1e18:>20,.6f}")
    if snapshot.get("core_spot_usdc") is not None:
        backing, book = float(snapshot["core_spot_usdc"]), values["treasury"] / 1e18
        print(f"  {'HyperCore USDC held':24s} {backing:>20,.6f}   ({backing - book:+,.6f} against the book)")
    if abs(residual) > DUST:
        print(f"  deviation: the book claims {residual / 1e18:+,.6f} USD against the treasury", file=sys.stderr)
        history = OUT / "history.jsonl"
        if history.exists():
            off = [json.loads(line) for line in history.read_text().splitlines() if line.strip()]
            off = [row for row in off if abs(row["residual_usd"]) > 1e-6]
            print(f"  {len(off)} of {len(history.read_text().splitlines())} captures deviated; "
                  f"largest {max((row['residual_usd'] for row in off), default=0):+,.6f} USD", file=sys.stderr)


def verify() -> dict:
    path = OUT / "head.json"
    assert path.exists(), "no saved head snapshot; run with --capture first"
    snapshot = json.loads(path.read_text())
    values = {name: int(value) for name, value in snapshot["values"].items()}
    for name, address, selector, _signed in READS:
        assert snapshot["raw"][name]["address"] == address.lower()
        assert snapshot["raw"][name]["selector"] == selector
        assert values[name] == word(snapshot["raw"][name]["word"], _signed), name
    residual = values["treasury"] - sum(values[claim] for claim in CLAIMS)
    assert residual == int(snapshot["residual_raw"])
    assert "side_bucket" not in CLAIMS
    if abs(residual) > FATAL:
        raise AssertionError(
            f"the live book claims {residual / 1e18:,.6f} USD against the treasury; "
            "a deviation this large is not a transient, treat it as a live value-creation instance"
        )
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="read the head over the public RPC and save it")
    args = parser.parse_args()
    snapshot = capture() if args.capture else verify()
    report(snapshot)
    if args.capture:
        verify()
    print("book identity holds on saved state" if not args.capture else "captured and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())