"""Cross-check an independent Papertrade intent decoder against pinned local evidence.

The decoder is an unofficial community project. Its semantic labels and ABI shapes
remain hypotheses until checked against execution; they are not recovered source.
"""

import collections
import json
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
ATLAS = BASE / "atlas" / "block_48902346"
HISTORICAL = BASE / "artifacts" / "historical"
TRACE_DIRS = (HISTORICAL, BASE / "artifacts" / "exchange_core_withdrawal")
SOURCE_COMMIT = "5912298a6f66247607891c6dab0a42f6ebd2f976"
SOURCE_URL = (
    "https://github.com/nirholas/papertrade-explorer/blob/"
    f"{SOURCE_COMMIT}/src/calldata.ts"
)

# The shape names come from the public decoder, not a contract ABI.
SHAPES = {
    "0x251fb27d": ("batch_executor_implementation", "batch of target/data/flagA/flagB/intentId tuples", None),
    "0x2792e706": ("exchange_implementation", "signed close intent", None),
    "0xec6783f0": ("exchange_implementation", "signed open-position intent", 11),
    "0x8d09f23f": ("exchange_implementation", "signed withdraw-to-Core intent", 7),
    "0x83115825": ("staking_implementation", "signed stake or unstake intent", 7),
    "0x9c96d4a1": ("staking_implementation", "signed claim or distribute intent", 6),
    "0x5f76a1d6": ("session_key_manager_implementation", "signed register-session-key intent", 9),
}
EVENT = "0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad"


def calls(node):
    if not isinstance(node, dict):
        return
    yield node
    for child in node.get("calls", []):
        yield from calls(child)


def main():
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    by_role = {v["role"]: v for v in catalog.values()}
    evidence = {}
    for selector, (role, meaning, static_words) in SHAPES.items():
        entry = next((f for f in by_role[role]["functions"] if f["selector"] == selector), None)
        if entry is None:
            raise ValueError(f"{selector} absent from pinned {role} bytecode")
        evidence[selector] = {
            "role": role,
            "independent_decoder_meaning": meaning,
            "pinned_dispatcher_present": True,
            "local_decompiler_arguments": entry.get("cast_inferred_arguments") or entry["arguments"],
            "reconstructed_signature": entry.get("reconstructed_signature", ""),
            "local_decompiler_mutability": entry["state_mutability"],
            "historical_transactions": [],
            "historical_trace_call_count_including_proxy_delegatecall": 0,
            "historical_calldata_lengths_bytes": {},
            "shape_checks": [],
        }

    txs = {s: set() for s in SHAPES}
    lengths = {s: collections.Counter() for s in SHAPES}
    checks = {s: [] for s in SHAPES}
    for path in sorted(p for directory in TRACE_DIRS for p in directory.glob("*.calls.json")):
        tx = path.name.split(".")[0]
        for call in calls(json.loads(path.read_text())):
            data = call.get("input", "")
            selector = data[:10].lower()
            if selector not in SHAPES:
                continue
            txs[selector].add(tx)
            lengths[selector][(len(data) - 2) // 2] += 1
            static_words = SHAPES[selector][2]
            if static_words is not None:
                checks[selector].append(len(data) == 10 + 64 * static_words)
            elif selector == "0x2792e706":
                try:
                    raw = bytes.fromhex(data[2:])
                    array_offset = int.from_bytes(raw[4 + 32 : 4 + 64], "big")
                    count = int.from_bytes(raw[4 + array_offset : 4 + array_offset + 32], "big")
                    checks[selector].append(array_offset == 7 * 32 and len(raw) == 4 + 7 * 32 + 32 + count * 32)
                except (ValueError, IndexError):
                    checks[selector].append(False)

    for selector in SHAPES:
        evidence[selector]["historical_transactions"] = sorted(txs[selector])
        evidence[selector]["historical_trace_call_count_including_proxy_delegatecall"] = sum(lengths[selector].values())
        evidence[selector]["historical_calldata_lengths_bytes"] = dict(sorted(lengths[selector].items()))
        evidence[selector]["shape_checks"] = checks[selector]
        evidence[selector]["shape_check_status"] = (
            "all_sampled_calls_match" if checks[selector] and all(checks[selector]) else
            "no_historical_call_or_no_shape_check" if not checks[selector] else
            "mismatch"
        )
        if not all(checks[selector]):
            raise ValueError(f"{selector} historical calldata disagrees with decoder shape")

    event_lengths = collections.Counter()
    first_words = collections.Counter()
    event_txs = set()
    for path in sorted(p for directory in TRACE_DIRS for p in directory.glob("*.receipt.json")):
        for log in json.loads(path.read_text()).get("logs", []):
            if log.get("topics", [None])[0].lower() != EVENT:
                continue
            event_txs.add(path.name.split(".")[0])
            event_lengths[(len(log["topics"]), (len(log["data"]) - 2) // 2)] += 1
            first_words[int(log["data"][2:66], 16)] += 1

    result = {
        "pin": 48902346,
        "source": SOURCE_URL,
        "source_status": "unofficial community decoder; names and layouts are independent hypotheses",
        "limits": [
            "Selector presence proves bytecode dispatch, not a Solidity function name.",
            "Most local traces duplicate external calls at the proxy and implementation delegatecall layers.",
            "Calldata length and dynamic offset checks support a layout but do not prove argument meaning or authorization branches.",
            "The decoder distinguishes some intent kinds by EIP-712 signature recovery; this script does not independently verify those signatures.",
            "The BatchExecutor tuple flags and event tail fields are not semantically decoded here.",
        ],
        "selectors": evidence,
        "batch_intent_result_event": {
            "topic0": EVENT,
            "decoder_claim": "topics [signature,batchId,index,intentId]; first data word is success flag",
            "historical_transactions": sorted(event_txs),
            "observed_topic_count_and_data_bytes": {f"{a} topics, {b} data bytes": n for (a, b), n in sorted(event_lengths.items())},
            "observed_first_data_words": dict(sorted(first_words.items())),
        },
    }
    output = ATLAS / "external_decoder_evidence.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}: {len(SHAPES)} selectors, {sum(event_lengths.values())} saved event logs")


if __name__ == "__main__":
    main()
