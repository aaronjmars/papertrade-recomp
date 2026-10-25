#!/usr/bin/env python3
"""Recheck exact-runtime partial and failed deposit finalization branches."""

import argparse
import gzip
import hashlib
import json
import pathlib
import tempfile

import atlas_exchange_sweeps as sweep
from audit_corewriter_rejections import verify as verify_core_rejections

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = (
    ROOT
    / "artifacts"
    / "audit_sweep_settlement_stratified"
    / "partial_failure_replay.json.gz"
)
CASES = (
    "finalize_decreased_above_minimum",
    "finalize_partial_above_minimum",
    "finalize_unchanged_above_minimum",
    "finalize_unchanged",
    "finalize_one_unit_decrease_above_minimum",
)
SWEPT = "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696"
CLEARED = "0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e"
REQUESTED = "0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025"


def run(local_rpc_url):
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    implementation = next(
        address
        for address, row in manifest["contracts"].items()
        if row["role"] == "exchange_implementation"
    )
    runtime_hashes = {}
    for address in (sweep.EXCHANGE, implementation):
        code = sweep.rpc(local_rpc_url, "eth_getCode", [address, hex(sweep.PIN)])
        digest = hashlib.sha256(bytes.fromhex(code.removeprefix("0x"))).hexdigest()
        assert digest == manifest["contracts"][address]["sha256"]
        runtime_hashes[address] = digest
    with tempfile.TemporaryDirectory(prefix="papertrade-partial-replay-") as directory:
        original = sweep.LOCAL
        sweep.LOCAL = pathlib.Path(directory)
        try:
            sweep.capture_local(local_rpc_url)
            evidence = {}
            for name in CASES[:-1]:
                evidence[name] = {
                    "call": json.loads((sweep.LOCAL / f"{name}.call.json").read_text()),
                    "diff": json.loads((sweep.LOCAL / f"{name}.diff.json").read_text()),
                }
            base = evidence["finalize_partial_above_minimum"]["call"]
            full = 10_000_000_000
            sweep.rpc(
                local_rpc_url,
                "anvil_setStorageAt",
                [
                    sweep.EXCHANGE,
                    base["pending_slot"],
                    "0x" + sweep.word(base["pending_override"]),
                ],
            )
            sweep.rpc(
                local_rpc_url,
                "anvil_setCode",
                [sweep.PRE_SPOT, sweep.mock_return(full - 1, 0, 0)],
            )
            sweep.rpc(
                local_rpc_url, "anvil_setCode", [sweep.PRE_PERP, sweep.mock_return(0)]
            )
            request = {
                "from": sweep.OUTSIDER,
                "to": sweep.EXCHANGE,
                "data": sweep.FINALIZE + sweep.word(base["user"]),
                "gas": "0x1000000",
            }
            common = {
                key: base[key]
                for key in (
                    "pin",
                    "block_hash",
                    "user",
                    "proxy",
                    "pending_slot",
                    "last_sweep_slot",
                    "pending_override",
                    "last_sweep_override",
                )
            }
            common["mock_spot"] = full - 1
            common["mock_perp"] = 0
            evidence[CASES[-1]] = {
                "call": {
                    **common,
                    "trace": sweep.rpc(
                        local_rpc_url,
                        "debug_traceCall",
                        [
                            request,
                            hex(sweep.PIN),
                            {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
                        ],
                    ),
                },
                "diff": {
                    **common,
                    "trace": sweep.rpc(
                        local_rpc_url,
                        "debug_traceCall",
                        [
                            request,
                            hex(sweep.PIN),
                            {
                                "tracer": "prestateTracer",
                                "tracerConfig": {"diffMode": True},
                            },
                        ],
                    ),
                },
            }
        finally:
            sweep.LOCAL = original
    payload = {
        "pin": manifest["block"],
        "block_hash": manifest["block_hash"],
        "runtime_sha256": runtime_hashes,
        "source": "fresh archive-backed Anvil fork with pinned Exchange runtime and controlled Core reads",
        "cases": evidence,
    }
    OUT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )


def storage_delta(diff, slot, mask=None):
    contract = {
        side: diff[side].get(sweep.EXCHANGE, {}).get("storage", {})
        for side in ("pre", "post")
    }
    before = int(contract["pre"].get(slot, "0x0"), 16)
    after = int(contract["post"].get(slot, "0x0"), 16)
    if mask is not None:
        before &= mask
        after &= mask
    return after - before


def verify():
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert saved["pin"] == manifest["block"] == sweep.PIN
    assert saved["block_hash"] == manifest["block_hash"]
    assert saved["source"].startswith("fresh archive-backed Anvil fork")
    assert saved["runtime_sha256"] == {
        address: manifest["contracts"][address]["sha256"]
        for address in saved["runtime_sha256"]
    }
    assert {
        manifest["contracts"][address]["role"] for address in saved["runtime_sha256"]
    } == {"exchange_proxy", "exchange_implementation"}
    assert set(saved["cases"]) == set(CASES)
    full = 10_000_000_000
    expected = full * 10**10
    outcomes = []
    for name in CASES:
        item = saved["cases"][name]
        call, diff = item["call"], item["diff"]
        assert call["block_hash"] == diff["block_hash"] == manifest["block_hash"]
        assert call["pending_override"] == diff["pending_override"]
        assert call["pending_override"] & ((1 << 64) - 1) == (
            100_000_000 if name == "finalize_unchanged" else full
        )
        assert call["mock_perp"] == 0
        assert (
            call["mock_spot"]
            == {
                "finalize_decreased_above_minimum": 0,
                "finalize_partial_above_minimum": 1,
                "finalize_unchanged_above_minimum": full,
                "finalize_unchanged": 100_000_000,
                "finalize_one_unit_decrease_above_minimum": full - 1,
            }[name]
        )
        trace = call["trace"]
        prepost = diff["trace"]
        logs = [
            log
            for child in sweep.descendants(trace)
            for log in child.get("logs", [])
            if log["address"].lower() == sweep.EXCHANGE
        ]
        topics = [log["topics"][0].lower() for log in logs]
        treasury = storage_delta(prepost, "0x" + sweep.word(14))
        total = storage_delta(prepost, "0x" + sweep.word(22), (1 << 128) - 1)
        user_slot = next(
            (
                slot
                for slot in prepost.get("post", {})
                .get(sweep.EXCHANGE, {})
                .get("storage", {})
                if slot
                not in (
                    "0x" + sweep.word(14),
                    "0x" + sweep.word(22),
                    call["pending_slot"],
                    call["last_sweep_slot"],
                )
            ),
            None,
        )
        if name in (
            "finalize_decreased_above_minimum",
            "finalize_partial_above_minimum",
            "finalize_one_unit_decrease_above_minimum",
        ):
            assert not trace.get("error") and topics == [SWEPT]
            assert sweep.output_words(logs[0]["data"]) == [expected]
            assert treasury == total == expected
            assert (
                user_slot is not None and storage_delta(prepost, user_slot) == expected
            )
            assert call["pending_slot"] not in prepost["post"].get(
                sweep.EXCHANGE, {}
            ).get("storage", {})
            outcome = "full snapshot credited after observed Core balance decrease"
        elif name == "finalize_unchanged_above_minimum":
            assert not trace.get("error") and topics == [CLEARED, REQUESTED]
            assert treasury == total == 0 and user_slot is None
            assert call["pending_slot"] in prepost["post"][sweep.EXCHANGE]["storage"]
            outcome = "no credit, retry requested after unchanged Core balance"
        else:
            assert trace.get("error") and trace.get("output") == "0x329c2b0f"
            assert not topics and not prepost.get("post", {}).get(
                sweep.EXCHANGE, {}
            ).get("storage")
            outcome = "reverted below minimum with pending state unchanged"
        outcomes.append(
            {
                "case": name,
                "mock_core_balance_8": call["mock_spot"],
                "credited_18": treasury,
                "outcome": outcome,
            }
        )
    real_failures = verify_core_rejections()
    assert len(real_failures["cases"]) == 2
    return {
        "local_cases": outcomes,
        "historical_core_rejections": [
            {"proxy": x["proxy"], "error": x["core_error"]}
            for x in real_failures["cases"]
        ],
        "limit": "Core balance mocks do not prove that a partial HyperCore transfer occurred or that an unchanged balance persists after every failed action.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local-rpc-url", help="fresh archive-backed Anvil fork at block 48,902,346"
    )
    args = parser.parse_args()
    if args.local_rpc_url:
        run(args.local_rpc_url)
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
