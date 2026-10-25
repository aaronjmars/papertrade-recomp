"""Compare the live Exchange getters with the recovery candidate under a read-only override.

Both sides are called at the same live head: once through the proxy with the live
implementation installed, once with the candidate's code and an EIP-1967
implementation-slot override. This is read-only parity, not a mutation or upgrade proof.
"""

import argparse
import concurrent.futures
import hashlib
import json
import pathlib

from atlas_pt01_replacement_getter_parity import (
    ADMIN,
    EXCHANGE,
    TRADER,
    cases as pinned_cases,
    encode_word,
)
from recovery.current_rpc import rpc, rpc_call, word
from recovery.deploy import address as candidate_address

ROOT = pathlib.Path(__file__).resolve().parents[1]
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "getter_parity.json"
COMPILED = HERE / "compiled.json"
LIVE_FACTS = ROOT / "artifacts" / "recovery_redrive" / "live_facts.json"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
PINNED_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
REMOVED_SELECTOR = "0x415f1240"  # liquidate(uint256) in the pinned catalog, dropped by the live set
CANDIDATE = candidate_address()
USER_ARGUMENT = {"name": "address", "values": [TRADER]}
USER_AND_ZERO = {"name": "address,uint256", "values": [TRADER, 0]}


def live_facts():
    return json.loads(LIVE_FACTS.read_text())


def cases():
    """The pinned view sample, plus the live dispatcher's added and removed selectors."""
    live = live_facts()
    rows = [{**row, "kind": "pinned_catalog"} for row in pinned_cases()]
    for selector in live["dispatcher"]["added_selectors"]:
        for argument in (USER_ARGUMENT, USER_AND_ZERO):
            rows.append({
                "kind": "added_selector",
                "selector": "0x" + selector,
                "arguments": argument["name"],
                "signature": live["dispatcher"]["public_signature_matches"][selector]["matches"][0]
                             if live["dispatcher"]["public_signature_matches"][selector]["matches"] else "",
                "inputs": argument["values"],
                "calldata": "0x" + selector + "".join(encode_word(value) for value in argument["values"]),
            })
    rows.append({
        "kind": "removed_selector",
        "selector": REMOVED_SELECTOR,
        "arguments": "uint256",
        "signature": "",
        "inputs": [1_394_063],
        "calldata": REMOVED_SELECTOR + encode_word(1_394_063),
    })
    return rows


def override(compiled):
    return {
        EXCHANGE: {"stateDiff": {IMPLEMENTATION_SLOT: word(CANDIDATE)}},
        CANDIDATE: {"code": compiled["deployed_code"]},
    }


def capture():
    compiled = json.loads(COMPILED.read_text())
    live = live_facts()
    head = rpc("eth_getBlockByNumber", ["latest", False])
    implementation = rpc("eth_getStorageAt", [EXCHANGE, IMPLEMENTATION_SLOT, "latest"])
    assert implementation.lower() == word(live["exchange"]["implementation"]).lower()
    assert int(implementation, 16) != int(PINNED_IMPLEMENTATION, 16)
    assert hashlib.sha256(bytes.fromhex(compiled["deployed_code"][2:])).hexdigest() == \
        compiled["deployed_code_sha256"]
    control = {
        "without_override": rpc_call(EXCHANGE, "0x5c60da1b", sender=ADMIN),
        "with_override": rpc_call(EXCHANGE, "0x5c60da1b", sender=ADMIN, state_override=override(compiled)),
    }

    def paired(row):
        return {**row,
                "live": rpc_call(EXCHANGE, row["calldata"]),
                "candidate": rpc_call(EXCHANGE, row["calldata"], state_override=override(compiled))}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(paired, cases()))
    saved = {
        "head": {key: head[key] for key in ("number", "hash", "timestamp")},
        "live_facts": str(LIVE_FACTS.relative_to(ROOT)),
        "implementation_word": implementation,
        "live_implementation": live["exchange"]["implementation"],
        "pinned_implementation": PINNED_IMPLEMENTATION,
        "candidate": CANDIDATE,
        "candidate_code_sha256": compiled["deployed_code_sha256"],
        "override_slot": IMPLEMENTATION_SLOT,
        "override_control": control,
        "added_selector_public_signatures": live["dispatcher"]["public_signature_matches"],
        "rows": rows,
        "limits": [
            "The candidate is installed only by a live eth_call state and code override.",
            "Getter parity does not establish mutation, Core settlement, or production upgrade safety.",
            "Selector names from public signature databases are unverified hints.",
        ],
    }
    OUT.write_text(json.dumps(saved, indent=2, sort_keys=True) + "\n")
    return verify()


def verify():
    compiled = json.loads(COMPILED.read_text())
    live = live_facts()
    saved = json.loads(OUT.read_text())
    assert saved["live_facts"] == str(LIVE_FACTS.relative_to(ROOT))
    assert int(saved["head"]["number"], 16) >= int(live["head"]["number"], 16), \
        "the parity capture cannot predate the live-facts capture"
    assert len(saved["head"]["hash"]) == 66
    assert saved["implementation_word"].lower() == word(live["exchange"]["implementation"]).lower()
    assert saved["live_implementation"] == live["exchange"]["implementation"]
    assert int(saved["implementation_word"], 16) != int(saved["pinned_implementation"], 16)
    assert saved["override_slot"] == IMPLEMENTATION_SLOT
    assert saved["candidate"] == CANDIDATE == candidate_address()
    assert saved["candidate_code_sha256"] == compiled["deployed_code_sha256"]
    assert hashlib.sha256(bytes.fromhex(compiled["deployed_code"][2:])).hexdigest() == \
        saved["candidate_code_sha256"]
    assert saved["added_selector_public_signatures"] == live["dispatcher"]["public_signature_matches"]
    control = saved["override_control"]
    assert int(control["without_override"]["data"], 16) == int(live["exchange"]["implementation"], 16)
    assert int(control["with_override"]["data"], 16) == int(CANDIDATE, 16)
    assert control["without_override"]["status"] == control["with_override"]["status"] == "success"

    expected = cases()
    assert len(saved["rows"]) == len(expected) == 64 + 12 + 1
    succeeded = rejected = 0
    for row, case in zip(saved["rows"], expected, strict=True):
        assert {key: row[key] for key in case} == case
        assert row["live"] == row["candidate"], f"{row['kind']} {row['selector']} differs"
        if row["kind"] == "pinned_catalog":
            assert row["live"]["status"] == "success", f"pinned getter {row['selector']} failed"
            succeeded += 1
        elif row["kind"] == "added_selector":
            # the live set's added selectors may accept or reject these argument shapes
            succeeded += row["live"]["status"] == "success"
            rejected += row["live"]["status"] == "error"
        else:
            assert row["kind"] == "removed_selector"
            assert row["live"]["status"] == "error", "the live set dropped liquidate(uint256)"
            rejected += 1
    assert succeeded + rejected == len(saved["rows"])
    assert rejected == 5, "two added selectors reject both probed shapes, plus the removed one"
    assert succeeded >= 64
    assert len({row["selector"] for row in saved["rows"]}) >= 55
    return {
        "head_block": int(saved["head"]["number"], 16),
        "live_implementation": saved["live_implementation"],
        "candidate": saved["candidate"],
        "calls": len(saved["rows"]),
        "distinct_selectors": len({row["selector"] for row in saved["rows"]}),
        "matching_successes": succeeded,
        "matching_rejections": rejected,
        "removed_selector_still_reverts": True,
        "candidate_code_sha256": saved["candidate_code_sha256"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="run live read-only comparisons through the public RPC")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))