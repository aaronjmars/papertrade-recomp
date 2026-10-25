#!/usr/bin/env python3
"""Check three deployer-created Papertrade suites at the pinned HyperEVM block."""

import argparse
import collections
import gzip
import hashlib
import json
import os
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
PIN = 48_902_346
DEPLOYER = "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
IMPLEMENTATION_SLOT = (
    "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
)
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
EXCHANGE_INDEX = (4, 23, 42)
PROXY_INDEX = tuple(base + offset for base in (0, 19, 38) for offset in range(2, 17, 2))
GETTERS = {
    "treasury": "0x61d027b3",
    "totalBalances": "0xa69a2ad1",
    "owner": "0x8da5cb5b",
}
FACTORY_TOPIC = "0x3d2489efb661e8b1c3679865db649ca1de61d76a71184a1234de2e55786a6aad"
OLDER_FACTORY_INDEX = (8, 27)
OLDER_PROXY_COUNTS = (33, 5)
EVENT_WINDOW = (47_856_000, 47_856_999)
EVENT_COUNTS = {
    "0x88451ea1189f73b554f0bf39c09868560ed149b3d788fcc933ff66ba926827f3": 6,
    "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf": 6,
    "0xa32e4800a59f03b131f5fea90951bdf00d8d505ad98f48ece29d8620a0bf09b0": 2,
}


def inputs():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    txs = json.loads((ROOT / "artifacts" / "deployer_txlist.json").read_text())
    sent = [row for row in txs if row["from"].lower() == DEPLOYER]
    assert len(sent) == 165
    assert sorted(int(row["nonce"]) for row in sent) == list(range(165))
    created = [row for row in sent if row["contractAddress"]]
    assert all(row["txreceipt_status"] == "1" and row["isError"] == "0" for row in sent)
    assert len(created) == 59
    assert len({row["contractAddress"].lower() for row in created}) == 59
    assert [int(row["blockNumber"]) // 1_000_000 for row in created] == [42] * 19 + [
        47
    ] * 38 + [48] * 2
    assert manifest["block"] == PIN
    return manifest, created


def rpc_batch(url, calls):
    results = {}
    for start in range(0, len(calls), 10):
        chunk = calls[start : start + 10]
        request = urllib.request.Request(
            url,
            json.dumps(chunk).encode(),
            {"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            reply = json.load(response)
        assert isinstance(reply, list) and len(reply) == len(chunk), reply
        for row in reply:
            assert "error" not in row, row
            assert row["id"] not in results
            results[row["id"]] = row["result"]
    assert set(results) == {call["id"] for call in calls}
    return results


def call(method, params, index):
    return {"jsonrpc": "2.0", "id": index, "method": method, "params": params}


def factory_logs(factory, first_block):
    assert os.environ.get("ETHERSCAN_API_KEY")
    command = [
        "etherscan",
        "logs",
        "get",
        "--chain",
        "999",
        "--address",
        factory,
        "--topic0",
        FACTORY_TOPIC,
        "--from-block",
        str(first_block),
        "--to-block",
        str(PIN),
        "--page",
        "1",
        "--offset",
        "1000",
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, check=True, timeout=45
    )
    logs = json.loads(result.stdout)
    assert isinstance(logs, list) and len(logs) < 1000
    return logs


def normalized_proxy_sha(code):
    normalized = bytearray(code)
    for offset in (0x61, 0xDE, 0x37B, 0x3DA):
        normalized[offset : offset + 32] = bytes(32)
    return hashlib.sha256(normalized).hexdigest()


def capture():
    manifest, created = inputs()
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    addresses = [row["contractAddress"].lower() for row in created]
    older_factory_logs = [
        factory_logs(addresses[index], int(created[index]["blockNumber"]))
        for index in OLDER_FACTORY_INDEX
    ]
    assert [len(logs) for logs in older_factory_logs] == list(OLDER_PROXY_COUNTS)
    older_proxy_addresses = [
        "0x" + log["topics"][2][-40:].lower()
        for logs in older_factory_logs
        for log in logs
    ]
    assert len(older_proxy_addresses) == len(set(older_proxy_addresses)) == 38
    calls = [call("eth_getBlockByNumber", [hex(PIN), False], 0)]
    calls.append(call("eth_getTransactionCount", [DEPLOYER, hex(PIN)], 1))
    for index, address in enumerate(addresses):
        calls.append(call("eth_getCode", [address, hex(PIN)], 100 + index))
    for index, address in enumerate(older_proxy_addresses):
        calls.append(call("eth_getCode", [address, hex(PIN)], 1000 + index))
    for index in PROXY_INDEX:
        for slot_index, slot in enumerate((IMPLEMENTATION_SLOT, ADMIN_SLOT)):
            calls.append(
                call(
                    "eth_getStorageAt",
                    [addresses[index], slot, hex(PIN)],
                    200 + index * 2 + slot_index,
                )
            )
    for index in EXCHANGE_INDEX:
        for getter_index, selector in enumerate(GETTERS.values()):
            calls.append(
                call(
                    "eth_call",
                    [{"to": addresses[index], "data": selector}, hex(PIN)],
                    300 + index * 3 + getter_index,
                )
            )
        for slot_index, slot in enumerate((14, 22)):
            calls.append(
                call(
                    "eth_getStorageAt",
                    [addresses[index], hex(slot), hex(PIN)],
                    500 + index * 2 + slot_index,
                )
            )
    calls.append(
        call(
            "eth_getLogs",
            [
                {
                    "address": addresses[23],
                    "fromBlock": hex(EVENT_WINDOW[0]),
                    "toBlock": hex(EVENT_WINDOW[1]),
                }
            ],
            900,
        )
    )
    responses = rpc_batch(url, calls)
    assert responses[0]["hash"].lower() == manifest["block_hash"]
    assert int(responses[1], 16) == 165
    payload = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "deployer": DEPLOYER,
        "deployer_nonce_at_pin": 165,
        "creation_count": len(created),
        "rows": [
            {
                "address": address,
                "creation_tx": created[index]["hash"].lower(),
                "creation_block": int(created[index]["blockNumber"]),
                "runtime": responses[100 + index],
                "implementation_word": responses[200 + index * 2]
                if index in PROXY_INDEX
                else None,
                "admin_word": responses[201 + index * 2]
                if index in PROXY_INDEX
                else None,
                "exchange_getters": {
                    name: responses[300 + index * 3 + getter_index]
                    for getter_index, name in enumerate(GETTERS)
                }
                if index in EXCHANGE_INDEX
                else None,
                "accounting_slots": {
                    "14": responses[500 + index * 2],
                    "22": responses[501 + index * 2],
                }
                if index in EXCHANGE_INDEX
                else None,
            }
            for index, address in enumerate(addresses)
        ],
        "earlier_factory_deployments": [
            {
                "factory": addresses[factory_index],
                "from_block": int(created[factory_index]["blockNumber"]),
                "to_block": PIN,
                "topic0": FACTORY_TOPIC,
                "page_size": 1000,
                "events": [
                    {"log": log, "runtime": responses[1000 + offset + index]}
                    for index, log in enumerate(logs)
                ],
            }
            for factory_index, offset, logs in (
                (OLDER_FACTORY_INDEX[0], 0, older_factory_logs[0]),
                (
                    OLDER_FACTORY_INDEX[1],
                    len(older_factory_logs[0]),
                    older_factory_logs[1],
                ),
            )
        ],
        "prior_exchange_log_window": {
            "from_block": EVENT_WINDOW[0],
            "to_block": EVENT_WINDOW[1],
            "logs": responses[900],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(
        gzip.compress(
            json.dumps(payload, separators=(",", ":")).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    return verify()


def verify():
    manifest, created = inputs()
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    assert saved["pin"] == PIN and saved["block_hash"] == manifest["block_hash"]
    assert saved["deployer"] == DEPLOYER and saved["deployer_nonce_at_pin"] == 165
    assert saved["creation_count"] == len(saved["rows"]) == 59
    rows = saved["rows"]
    for index, (row, tx) in enumerate(zip(rows, created)):
        address = tx["contractAddress"].lower()
        assert row["address"] == address
        assert row["creation_tx"] == tx["hash"].lower()
        assert row["creation_block"] == int(tx["blockNumber"])
        assert row["runtime"].startswith("0x")
        code = bytes.fromhex(row["runtime"][2:])
        assert code
        sha = hashlib.sha256(code).hexdigest()
        if address in manifest["contracts"]:
            assert sha == manifest["contracts"][address]["sha256"]
        if index in PROXY_INDEX:
            assert len(code) == 925
            assert row["implementation_word"] and row["admin_word"]
        else:
            assert row["implementation_word"] is None and row["admin_word"] is None
    assert sum(row["address"] in manifest["contracts"] for row in rows) == 21
    older_hashes = {
        hashlib.sha256(bytes.fromhex(row["runtime"][2:])).hexdigest()
        for row in rows[:38]
    }
    manifest_hashes = {row["sha256"] for row in manifest["contracts"].values()}
    assert len(older_hashes) == 15 and len(older_hashes - manifest_hashes) == 6
    for base in (0, 19, 38):
        assert all(
            rows[index]["creation_block"] >= rows[base]["creation_block"]
            for index in range(base, min(base + 19, len(rows)))
        )
        for offset in range(2, 17, 2):
            index = base + offset
            impl = "0x" + rows[index]["implementation_word"][-40:]
            admin = "0x" + rows[index]["admin_word"][-40:]
            assert impl in {row["address"] for row in rows}
            assert admin == rows[base]["address"]
    assert "0x" + rows[4]["implementation_word"][-40:] == rows[3]["address"]
    assert "0x" + rows[23]["implementation_word"][-40:] == rows[57]["address"]
    assert "0x" + rows[42]["implementation_word"][-40:] == rows[41]["address"]
    assert rows[57]["address"] == "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
    factory_hashes = {
        hashlib.sha256(bytes.fromhex(rows[index]["runtime"][2:])).hexdigest()
        for index in (7, 26, 45)
    }
    assert len(factory_hashes) == 1
    older_deployments = saved["earlier_factory_deployments"]
    assert len(older_deployments) == 2
    family = json.loads(
        (ATLAS / manifest["deposit_proxy_family"]["sample_template_file"]).read_text()
    )
    reference = bytes.fromhex(
        (ATLAS / family["representative_runtime_file"]).read_text().strip()[2:]
    )
    reference_hash = normalized_proxy_sha(reference)
    older_proxy_addresses = set()
    for group, factory_index, exchange_index, expected_count in zip(
        older_deployments, OLDER_FACTORY_INDEX, EXCHANGE_INDEX[:2], OLDER_PROXY_COUNTS
    ):
        assert group["factory"] == rows[factory_index]["address"]
        assert group["from_block"] == rows[factory_index]["creation_block"]
        assert group["to_block"] == PIN and group["topic0"] == FACTORY_TOPIC
        assert group["page_size"] == 1000 and len(group["events"]) == expected_count
        for item in group["events"]:
            log = item["log"]
            assert log["address"].lower() == group["factory"]
            assert len(log["topics"]) == 3 and log["topics"][0] == FACTORY_TOPIC
            assert group["from_block"] <= int(log["blockNumber"], 16) <= PIN
            user = "0x" + log["topics"][1][-40:].lower()
            proxy = "0x" + log["topics"][2][-40:].lower()
            assert proxy not in older_proxy_addresses
            older_proxy_addresses.add(proxy)
            code = bytes.fromhex(item["runtime"][2:])
            assert len(code) == 1646 and normalized_proxy_sha(code) == reference_hash
            for offset in (0x61, 0xDE):
                assert code[offset : offset + 32] == bytes.fromhex(
                    "00" * 12 + rows[exchange_index]["address"][2:]
                )
            for offset in (0x37B, 0x3DA):
                assert code[offset : offset + 32] == bytes.fromhex("00" * 12 + user[2:])
    assert len(older_proxy_addresses) == 38
    newest_proxy_addresses = {
        row["address"]
        for row in json.loads((ATLAS / "deposit_proxy_instances.json").read_text())[
            "instances"
        ]
    }
    assert not older_proxy_addresses & newest_proxy_addresses
    assert (
        int(older_deployments[0]["events"][-1]["log"]["blockNumber"], 16) == 46_776_477
    )
    assert (
        int(older_deployments[1]["events"][-1]["log"]["blockNumber"], 16) == 48_154_937
    )
    assert 48_154_937 > rows[58]["creation_block"]
    for index, timelock_index in zip(EXCHANGE_INDEX, (18, 37, 56)):
        getters = rows[index]["exchange_getters"]
        slots = rows[index]["accounting_slots"]
        assert getters["owner"] == "0x" + "0" * 24 + rows[timelock_index]["address"][2:]
        assert int(getters["treasury"], 16) == int(slots["14"], 16) > 0
        assert int(getters["totalBalances"], 16) == int(slots["22"], 16) & (
            (1 << 128) - 1
        )
        assert int(getters["totalBalances"], 16) > 0
    assert (
        int(rows[4]["exchange_getters"]["treasury"], 16) == 117184028077123000000000000
    )
    assert (
        int(rows[23]["exchange_getters"]["treasury"], 16) == 641709999003269000000000000
    )
    window = saved["prior_exchange_log_window"]
    assert (window["from_block"], window["to_block"]) == EVENT_WINDOW
    logs = window["logs"]
    assert len(logs) == 14
    assert all(row["address"].lower() == rows[23]["address"] for row in logs)
    assert all(
        rows[42]["creation_block"] < int(row["blockNumber"], 16) <= PIN for row in logs
    )
    assert collections.Counter(row["topics"][0] for row in logs) == EVENT_COUNTS
    assert int(logs[0]["blockNumber"], 16) == 47_856_471
    assert int(logs[-1]["blockNumber"], 16) == 47_856_767
    return {
        "pin": PIN,
        "deployer_transactions": 165,
        "direct_creations": 59,
        "captured_manifest_creations": 21,
        "older_creations_outside_manifest": 38,
        "older_factory_proxy_instances": len(older_proxy_addresses),
        "older_factory_proxy_instances_by_set": list(OLDER_PROXY_COUNTS),
        "older_distinct_runtime_hashes": len(older_hashes),
        "older_runtime_hashes_missing_from_manifest": len(
            older_hashes - manifest_hashes
        ),
        "older_exchange_post_new_suite_logs_in_sample": len(logs),
        "older_exchange_proxy_uses_later_implementation": rows[23][
            "implementation_word"
        ][-40:],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture",
        action="store_true",
        help="refresh pinned archive and explorer evidence",
    )
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
