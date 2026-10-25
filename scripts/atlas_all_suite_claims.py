#!/usr/bin/env python3
"""Reconcile pinned fee, LP, queue, and Staking scalars in all three suites."""

import argparse
import gzip
import json
import os
import pathlib

from atlas_deployer_scope import call
from atlas_exchange_sweeps import word
from atlas_newest_scalar_accounting import verify as newest_scalar_verify
from atlas_older_positions import rpc_batches

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "accounting_claims" / "pinned_suites.json.gz"
PIN = 48_902_346
BASES = (0, 19, 38)
EXCHANGE_SLOTS = (14, 18, 22, 26, 27, 38)
STAKING_SLOTS = (5, 6, 7, 8)


def saved(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def suites():
    rows = saved(SCOPE)["rows"]
    return [
        {
            "exchange": rows[base + 4]["address"],
            "tokenomics": rows[base + 10]["address"],
            "paper": rows[base + 12]["address"],
            "staking": rows[base + 14]["address"],
            "staking_implementation": "0x"
            + rows[base + 14]["implementation_word"][-40:],
        }
        for base in BASES
    ]


def capture():
    assert os.environ.get("PAPERTRADE_ARCHIVE_RPC")
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    requests = [call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    targets = {}
    for index, suite in enumerate(suites()):
        for slot in EXCHANGE_SLOTS:
            identifier = len(requests)
            requests.append(
                call(
                    "eth_getStorageAt",
                    [suite["exchange"], hex(slot), hex(PIN)],
                    identifier,
                )
            )
            targets[identifier] = (index, "exchange", str(slot))
        identifier = len(requests)
        requests.append(
            call("eth_getStorageAt", [suite["tokenomics"], "0x3", hex(PIN)], identifier)
        )
        targets[identifier] = (index, "tokenomics", "3")
        for slot in STAKING_SLOTS:
            identifier = len(requests)
            requests.append(
                call(
                    "eth_getStorageAt",
                    [suite["staking"], hex(slot), hex(PIN)],
                    identifier,
                )
            )
            targets[identifier] = (index, "staking", str(slot))
        identifier = len(requests)
        requests.append(
            call(
                "eth_call",
                [
                    {
                        "to": suite["exchange"],
                        "data": "0x27e235e3" + word(suite["staking"]),
                    },
                    hex(PIN),
                ],
                identifier,
            )
        )
        targets[identifier] = (index, "getters", "staking_exchange_balance")
        identifier = len(requests)
        requests.append(
            call(
                "eth_call",
                [
                    {
                        "to": suite["paper"],
                        "data": "0x70a08231" + word(suite["staking"]),
                    },
                    hex(PIN),
                ],
                identifier,
            )
        )
        targets[identifier] = (index, "getters", "paper_staking_balance")
    responses = rpc_batches(os.environ["PAPERTRADE_ARCHIVE_RPC"], requests)
    assert responses[0]["hash"].lower() == manifest["block_hash"]
    rows = [
        {
            "addresses": suite,
            "exchange": {},
            "tokenomics": {},
            "staking": {},
            "getters": {},
        }
        for suite in suites()
    ]
    for identifier, value in responses.items():
        if identifier == 0:
            continue
        index, group, key = targets[identifier]
        rows[index][group][key] = value
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(
        gzip.compress(
            json.dumps(
                {"pin": PIN, "block_hash": manifest["block_hash"], "suites": rows},
                separators=(",", ":"),
            ).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    return verify()


def account_total(index):
    if index < 2:
        accounts = saved(
            ROOT
            / "artifacts"
            / "deployer_scope"
            / f"older_exchange_{index}_balances.json.gz"
        )
    else:
        accounts = saved(
            ROOT / "artifacts" / "newest_account_census" / "account_balances.json.gz"
        )
    return accounts, sum(
        int(account["balance_getter"], 16) for account in accounts["accounts"]
    )


def verify():
    payload = saved(OUT)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    scope = saved(SCOPE)
    assert payload["pin"] == scope["pin"] == manifest["block"] == PIN
    assert payload["block_hash"] == scope["block_hash"] == manifest["block_hash"]
    assert len(payload["suites"]) == 3
    staking_impls = {
        suite["addresses"]["staking_implementation"] for suite in payload["suites"]
    }
    assert len(staking_impls) == 3
    implementation_hashes = set()
    for implementation in staking_impls:
        row = next(row for row in scope["rows"] if row["address"] == implementation)
        import hashlib

        implementation_hashes.add(
            hashlib.sha256(bytes.fromhex(row["runtime"][2:])).hexdigest()
        )
    assert len(implementation_hashes) == 1
    results = []
    for index, suite in enumerate(payload["suites"]):
        assert suite["addresses"] == suites()[index]
        exchange = {
            int(key): int(value, 16) for key, value in suite["exchange"].items()
        }
        tokenomics = int(suite["tokenomics"]["3"], 16)
        lp = tokenomics - (1 << 256) if tokenomics >= 1 << 255 else tokenomics
        staking = {int(key): int(value, 16) for key, value in suite["staking"].items()}
        ordinary = exchange[22] & ((1 << 128) - 1)
        margin = exchange[22] >> 128
        staker_fee = exchange[26] & ((1 << 128) - 1)
        dev_fee = exchange[26] >> 128
        accounts, account_sum = account_total(index)
        assert (
            accounts["pin"] == PIN and accounts["block_hash"] == manifest["block_hash"]
        )
        assert accounts["exchange"] == suite["addresses"]["exchange"]
        assert account_sum == ordinary
        if index < 2:
            positions = saved(
                ROOT
                / "artifacts"
                / "deployer_scope"
                / f"older_exchange_{index}_positions.json.gz"
            )
            assert (
                positions["pin"] == PIN
                and positions["block_hash"] == manifest["block_hash"]
            )
            assert int(positions["global"]["totalLockedMargin"], 16) == margin
            assert int(positions["global"]["totalQueued"], 16) == exchange[18]
        else:
            newest = newest_scalar_verify()
            assert newest["ordinary_balances_18"] == ordinary
            assert newest["locked_margin_18"] == margin
            assert newest["treasury_18"] == exchange[14]
            assert newest["staker_fee_18"] == staker_fee
            assert newest["dev_fee_18"] == dev_fee
            assert newest["tracked_lp_18"] == lp
        staking_address = suite["addresses"]["staking"]
        staking_row = next(
            row for row in accounts["accounts"] if row["address"] == staking_address
        )
        staking_balance = int(staking_row["balance_getter"], 16)
        assert staking_balance == int(suite["getters"]["staking_exchange_balance"], 16)
        assert staking[5] == int(suite["getters"]["paper_staking_balance"], 16)
        # The side bucket (slot 27) is NOT a term here: it is an earmark of the spendable LP
        # bankroll, already counted inside tracked LP plus queued, so adding it double counts
        # whenever it is nonzero (live2_sequences.md, SQ-L2-03). It is reported separately.
        assert (
            exchange[14]
            == ordinary
            + margin
            + exchange[18]
            + staker_fee
            + dev_fee
            + lp
        )
        results.append(
            {
                "suite": index,
                "exchange": suite["addresses"]["exchange"],
                "treasury_18": exchange[14],
                "ordinary_balances_18": ordinary,
                "locked_margin_18": margin,
                "queued_18": exchange[18],
                "staker_fee_18": staker_fee,
                "dev_fee_18": dev_fee,
                "tracked_lp_18": lp,
                "side_bucket_18": exchange[27],
                "staking_exchange_balance_18": staking_balance,
                "staking_reward_reserve_18": staking[7],
                "staking_balance_less_reserve_18": staking_balance - staking[7],
                "staking_unallocated_18": staking[8],
                "staked_paper_18": staking[5],
                "dev_fee_recipient": "0x" + f"{exchange[38] & ((1 << 160) - 1):040x}",
            }
        )
    return {
        "pin": PIN,
        "staking_implementation_sha256": next(iter(implementation_hashes)),
        "suites": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
