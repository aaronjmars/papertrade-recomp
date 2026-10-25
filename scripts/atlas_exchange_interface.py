#!/usr/bin/env python3
"""Cross-check a public Exchange ABI fixture against pinned bytecode and logs."""

import collections
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
SOURCE_COMMIT = "98a4480caaebd29a2b33500818a2b9cf2662e330"
SOURCE = f"https://github.com/jihanwi/hypermate-bot/blob/{SOURCE_COMMIT}/tests/fixtures/papertrade_exchange_abi.json"
ADAPTER_COMMIT = "835c4f8ff6329f9b42ba50c8f76f0473c0f292ca"
ADAPTER = f"https://github.com/LimeChain/gofin-cli/blob/{ADAPTER_COMMIT}/crates/gofin-papertrade/src/proof.rs"
ADAPTER_EXCHANGE_CODE_HASH = "0x9d20287df886415035d53344a0dc8a1044949308cc3283ee0fe7ea5f3ea28d92"


def cast(*args):
    return subprocess.run(["cast", *args], capture_output=True, text=True, check=True).stdout.strip().lower()


def canonical(item):
    return item["name"] + "(" + ",".join(entry["type"] for entry in item["inputs"]) + ")"


def main():
    fixture = json.loads((ATLAS / "external_exchange_abi_hypermate.json").read_text())
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    exchange = catalog[IMPLEMENTATION]
    assert exchange["role"] == "exchange_implementation"
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    runtime = (ATLAS / manifest["contracts"][IMPLEMENTATION]["runtime_file"]).read_text().strip()
    runtime_keccak = cast("keccak", runtime)
    assert runtime_keccak == ADAPTER_EXCHANGE_CODE_HASH
    selectors = {item["selector"]: item for item in exchange["functions"]}
    getter = next(x for x in json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]["views"] if x["selector"] == "0xdc8a47ef")
    assert not getter["failed"] and {x["base_slot"] for x in getter["mapping_matches"]} == {7}
    recent = [x for x in json.loads((ATLAS / "event_logs_last_256_blocks.json").read_text()) if x["address"].lower() == EXCHANGE]
    historical = []
    for path in HISTORICAL.glob("*.receipt.json"):
        historical.extend(x for x in json.loads(path.read_text()).get("logs", []) if x["address"].lower() == EXCHANGE)
    by_topic_recent = collections.defaultdict(list)
    by_topic_historical = collections.defaultdict(list)
    for row in recent:
        by_topic_recent[row["topics"][0].lower()].append(row)
    for row in historical:
        by_topic_historical[row["topics"][0].lower()].append(row)

    functions = []
    events = []
    event_catalog = []
    for entry in fixture["abi"]:
        signature = canonical(entry)
        if entry["type"] == "function":
            selector = cast("sig", signature)
            assert selector in selectors, f"{signature} absent from pinned dispatcher"
            current = selectors[selector]
            functions.append({"selector": selector, "signature": signature,
                              "already_named_by_public_signature_database": bool(current["candidate_signature"]),
                              "pinned_getter_trace": selector == "0xdc8a47ef",
                              "fixture_outputs": [x["type"] for x in entry.get("outputs", [])],
                              "output_types_status": ("contradicted: pinned slot 14 and accounting identity show a numeric amount; see exchange_storage_behavior.json"
                                                      if signature == "treasury()" else "fixture inference; not independently validated here")})
            continue
        if entry["type"] != "event":
            continue
        topic = cast("keccak", signature)
        assert topic == entry["topic0"].lower(), f"fixture topic mismatch: {signature}"
        logs = by_topic_recent[topic] + by_topic_historical[topic]
        observed_shapes = collections.Counter((len(x["topics"]), (len(x["data"]) - 2) // 64) for x in logs)
        expected_indexed = sum(x.get("indexed", False) for x in entry["inputs"])
        static_word_count_compatible = all(topics - 1 + words == len(entry["inputs"]) for topics, words in observed_shapes)
        assert static_word_count_compatible, f"{signature} has incompatible observed payload width"
        fixture_shape_compatible = all(topics == expected_indexed + 1 for topics, _ in observed_shapes)
        observed_indexed_counts = sorted({topics - 1 for topics, _ in observed_shapes})
        status = "observed_topic_hash_and_payload_width" if logs else "topic_hash_only"
        row = {"topic0": topic, "signature": signature, "status": status,
               "count_last_256_blocks": len(by_topic_recent[topic]),
               "count_in_saved_receipts": len(by_topic_historical[topic]),
               "observed_shapes": [{"topics": pair[0], "data_words": pair[1], "count": count}
                                   for pair, count in sorted(observed_shapes.items())],
               "fixture_indexed_count": expected_indexed,
               "fixture_indexing_matches_observation": fixture_shape_compatible,
               "observed_indexed_counts": observed_indexed_counts,
               "argument_names_status": "fixture inference, not established by event hash"}
        events.append(row)
        if logs:
            event_catalog.append({"topic0": topic, "reconstructed_signature": signature,
                                  "historical_log_count": len(by_topic_historical[topic]),
                                  "recent_log_count": len(by_topic_recent[topic]),
                                  "indexing_note": "fixture indexing disagrees with receipts" if not fixture_shape_compatible else "fixture indexing agrees with receipts"})

    result = {
        "pin": 48902346,
        "address": EXCHANGE,
        "implementation": IMPLEMENTATION,
        "source": SOURCE,
        "source_status": "unofficial ABI fixture derived from independent topic and selector research",
        "independent_adapter_crosscheck": {
            "source": ADAPTER,
            "reported_exchange_runtime_keccak": ADAPTER_EXCHANGE_CODE_HASH,
            "locally_computed_runtime_keccak": runtime_keccak,
            "matches_pinned_runtime": True,
        },
        "selector_reconstructions": {"0xdc8a47ef": "instruments(uint32)"},
        "functions": functions,
        "events": events,
        "event_catalog": event_catalog,
        "limits": [
            "Hash matches and observed payload widths support event signatures but do not prove parameter names or signedness beyond the signature preimage.",
            "Several fixture indexed flags disagree with saved receipts; use observed topic counts and mark which argument is indexed as unresolved where more than one placement fits.",
            "Function output types come from a third-party fixture; treasury() is contradicted by pinned storage and accounting checks in exchange_storage_behavior.json.",
            "Unobserved event signatures have only a hash match and must not be treated as emitted paths at the pinned block.",
        ],
    }
    output = ATLAS / "exchange_interface_evidence.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}: {len(functions)} function hashes, {len(events)} event hashes, {len(event_catalog)} observed event signatures")


if __name__ == "__main__":
    main()
