#!/usr/bin/env python3
"""Reconstruct the live DepositProxyFactory from pinned bytecode and traces."""

import argparse
import json
import os
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
CREATION = ROOT / "artifacts" / "factory_creation"
PROBES = ROOT / "artifacts" / "factory_probes"
FACTORY = "0x1629b7d46bef6e13ff754174fc9f32dea309b38f"
IMPLEMENTATION = "0x8f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
DEPLOYER = "0xdf1bda875c9393a663ce69bf6a7fbaa73dfd053d"
OUTSIDER = "0x" + "33" * 20
NEW_USER = "0x" + "12" * 20
NEW_OWNER = "0x" + "11" * 20
NEW_DEPLOYER = "0x" + "22" * 20
PIN = 48902346
CREATION_TX = "0xdf3909a903c5e15a5ac770bdcb6cccef77399094b4b99f759ecd4521ed86ae7d"
DEPLOY_TX = "0xddf30f3fd0d78c0516e37f32ed1ece2ef4ab488d7b4be8439c7196878047fb2e"


def cast_keccak(hex_string):
    return subprocess.run(["cast", "keccak", hex_string], capture_output=True,
                          text=True, check=True).stdout.strip().lower()


def mapping_slot(key, base):
    return subprocess.run(["cast", "index", "address", key, str(base)], capture_output=True,
                          text=True, check=True).stdout.strip().lower()


def word(address):
    return address[2:].rjust(64, "0")


def rpc(url, method, params):
    request = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                                                     "params": params}).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def probes():
    existing_user = "0x" + next(iter(json.loads((ATLAS / "deposit_proxy_family.json").read_text())
                                       ["records"][0]["varying_bytes"].values()))
    bootstrap = "0x0f71c8bc" + word(NEW_OWNER) + word(NEW_DEPLOYER)
    return {
        "deploy_authorized_existing": (DEPLOYER, "0xcbd433f4" + word(existing_user), None),
        "deploy_authorized_new": (DEPLOYER, "0xcbd433f4" + word(NEW_USER), None),
        "deploy_owner_new": (OWNER, "0xcbd433f4" + word(NEW_USER), None),
        "deploy_unauthorized_new": (OUTSIDER, "0xcbd433f4" + word(NEW_USER), None),
        "deploy_zero_user": (DEPLOYER, "0xcbd433f4" + word("0x" + "00" * 20), None),
        "set_deployer_owner": (OWNER, "0xc6f881bc" + word(NEW_DEPLOYER), None),
        "set_deployer_outsider": (OUTSIDER, "0xc6f881bc" + word(NEW_DEPLOYER), None),
        "set_deployer_zero": (OWNER, "0xc6f881bc" + word("0x" + "00" * 20), None),
        "transfer_owner_outsider": (OUTSIDER, "0xf2fde38b" + word(NEW_OWNER), None),
        "transfer_owner_zero": (OWNER, "0xf2fde38b" + word("0x" + "00" * 20), None),
        "bootstrap_admin_current": (ADMIN, bootstrap, None),
        "bootstrap_outsider_current": (OUTSIDER, bootstrap, None),
        "bootstrap_admin_uninitialized": (ADMIN, bootstrap, {
            FACTORY: {"stateDiff": {f"0x{3:064x}": "0x" + "00" * 32}}}),
        "legacy_initialize_current": (OUTSIDER, "0xc4d66de8" + word(EXCHANGE), None),
        "three_address_initializer_current": (OUTSIDER, "0x56e8d85b" + word(EXCHANGE)
                                              + word(NEW_OWNER) + word(NEW_DEPLOYER), None),
    }


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    PROBES.mkdir(parents=True, exist_ok=True)
    CREATION.mkdir(parents=True, exist_ok=True)
    for name, method, params in (
        ("transaction", "eth_getTransactionByHash", [CREATION_TX]),
        ("calls", "debug_traceTransaction", [CREATION_TX, {"tracer": "callTracer"}]),
        ("receipt", "eth_getTransactionReceipt", [CREATION_TX]),
    ):
        destination = CREATION / f"{CREATION_TX}.{name}.json"
        if not destination.exists():
            result = rpc(url, method, params)
            destination.write_text(json.dumps(result, indent=2) + "\n")
    for name, (sender, data, override) in probes().items():
        call = {"from": sender, "to": FACTORY, "data": data, "gas": "0x1000000"}
        for suffix, options in (
            ("call", {"tracer": "callTracer", "tracerConfig": {"withLog": True}}),
            ("diff", {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}),
        ):
            destination = PROBES / f"{name}.{suffix}.json"
            if destination.exists():
                continue
            if override:
                options["stateOverrides"] = override
            result = rpc(url, "debug_traceCall", [call, hex(PIN), options])
            destination.write_text(json.dumps(result, indent=2) + "\n")
    destination = PROBES / "compute_new_user.json"
    if not destination.exists():
        result = rpc(url, "eth_call", [{"to": FACTORY, "data": "0xd600539a" + word(NEW_USER)}, hex(PIN)])
        destination.write_text(json.dumps({"user": NEW_USER, "return": result}, indent=2) + "\n")
    destination = PROBES / "pinned_storage_words.json"
    if not destination.exists():
        header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
        manifest = json.loads((ATLAS / "manifest.json").read_text())
        assert header["hash"].lower() == manifest["block_hash"]
        values = {str(slot): rpc(url, "eth_getStorageAt", [FACTORY, hex(slot), hex(PIN)])
                  for slot in (0, 3, 4)}
        destination.write_text(json.dumps({"pin": PIN, "block_hash": header["hash"],
                                           "address": FACTORY, "slots": values}, indent=2) + "\n")
    destination = PROBES / "direct_impl_zero_exchange.call.json"
    if not destination.exists():
        zero_exchange = "0x56e8d85b" + word("0x" + "00" * 20) + word(NEW_OWNER) + word(NEW_DEPLOYER)
        result = rpc(url, "debug_traceCall", [{"from": OUTSIDER, "to": IMPLEMENTATION,
                                                "data": zero_exchange, "gas": "0x1000000"},
                                               hex(PIN), {"tracer": "callTracer"}])
        destination.write_text(json.dumps(result, indent=2) + "\n")


def all_calls(trace):
    yield trace
    for child in trace.get("calls", []):
        yield from all_calls(child)


def summarize_probe(name):
    call = json.loads((PROBES / f"{name}.call.json").read_text())
    diff = json.loads((PROBES / f"{name}.diff.json").read_text())
    logs = [log for node in all_calls(call) for log in node.get("logs", [])]
    children = [node for node in all_calls(call) if node is not call]
    return {"success": not call.get("error"), "revert_selector": call.get("output", "")[:10] if call.get("error") else None,
            "return_data": call.get("output") if not call.get("error") else None,
            "events": [{"topic0": log["topics"][0].lower(), "topics": log["topics"]} for log in logs],
            "child_types": [node.get("type") for node in children],
            "factory_storage_pre": diff.get("pre", {}).get(FACTORY, {}).get("storage", {}),
            "factory_storage_post": diff.get("post", {}).get(FACTORY, {}).get("storage", {})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="capture missing pinned read-only branch probes")
    args = parser.parse_args()
    if args.capture:
        capture()
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN
    pinned_words = json.loads((PROBES / "pinned_storage_words.json").read_text())
    assert pinned_words["block_hash"].lower() == manifest["block_hash"]
    assert pinned_words["address"] == FACTORY
    slot0 = int(pinned_words["slots"]["0"], 16)
    assert (slot0 >> 16) & ((1 << 160) - 1) == int(EXCHANGE, 16)
    assert slot0 & 0xff == 1
    assert int(pinned_words["slots"]["3"], 16) == int(OWNER, 16)
    assert int(pinned_words["slots"]["4"], 16) == int(DEPLOYER, 16)
    creation = json.loads((CREATION / f"{CREATION_TX}.calls.json").read_text())
    assert creation["type"] == "CREATE" and creation["to"].lower() == FACTORY
    initializer = creation["calls"][0]
    assert initializer["type"] == "DELEGATECALL" and initializer["to"].lower() == IMPLEMENTATION
    assert initializer["input"].lower() == "0x56e8d85b" + word(EXCHANGE) + word(creation["from"].lower()) + word(DEPLOYER)
    initial_receipt = json.loads((CREATION / f"{CREATION_TX}.receipt.json").read_text())
    owner_topic = cast_keccak("OwnerUpdated(address)")
    deployer_topic = cast_keccak("AuthorizedDeployerUpdated(address)")
    deployed_topic = cast_keccak("ProxyDeployed(address,address)")
    assert [log["topics"][0].lower() for log in initial_receipt["logs"]] == [owner_topic, deployer_topic]
    assert initial_receipt["logs"][0]["topics"][1][-40:].lower() == creation["from"][2:].lower()
    assert initial_receipt["logs"][1]["topics"][1][-40:].lower() == DEPLOYER[2:]

    deploy = json.loads((HISTORICAL / f"{DEPLOY_TX}.calls.json").read_text())
    create2 = next(node for node in all_calls(deploy) if node.get("type") == "CREATE2")
    initcode = create2["input"].lower()
    assert len(initcode[2:]) // 2 == 1889
    assert initcode[-128:-64] == word(EXCHANGE)
    user = "0x" + deploy["input"][-40:].lower()
    assert initcode[-64:] == word(user)
    code_prefix = initcode[:-64]

    records = json.loads((ATLAS / "deposit_proxy_family.json").read_text())["records"]
    matches = []
    for row in records:
        values = set(row["varying_bytes"].values())
        assert len(values) == 1
        user = "0x" + next(iter(values))
        user_initcode = code_prefix + word(user)
        salt = cast_keccak(user)
        init_hash = cast_keccak(user_initcode)
        predicted = "0x" + cast_keccak("0xff" + FACTORY[2:] + salt[2:] + init_hash[2:])[-40:]
        assert predicted == row["address"]
        matches.append({"user": user, "deployed_address": row["address"], "predicted_address": predicted,
                        "salt": salt, "initcode_keccak": init_hash})
    assert len(matches) == 41
    all_deployments = json.loads((ATLAS / "factory_event_deployments.json").read_text())
    assert all_deployments["create2_formula_matches"] == 22586
    assert all_deployments["event_internal_address_tx_block_matches"] == 22586
    deploy_receipt = json.loads((HISTORICAL / f"{DEPLOY_TX}.receipt.json").read_text())
    event = next(log for log in deploy_receipt["logs"] if log["address"].lower() == FACTORY)
    assert event["topics"][0].lower() == deployed_topic
    assert "0x" + event["topics"][1][-40:].lower() == "0x" + deploy["input"][-40:].lower()
    assert "0x" + event["topics"][2][-40:].lower() == create2["to"].lower()
    assert "0x" + deploy["output"][-40:].lower() == create2["to"].lower()
    diff = json.loads((HISTORICAL / f"{DEPLOY_TX}.state_diff.json").read_text())
    post = diff["post"][FACTORY]["storage"]
    assert int(post[mapping_slot("0x" + deploy["input"][-40:].lower(), 1)], 16) == int(create2["to"], 16)
    assert int(post[mapping_slot(create2["to"].lower(), 2)], 16) == 1

    observed = {name: summarize_probe(name) for name in probes()}
    existing = observed["deploy_authorized_existing"]
    assert existing["success"] and existing["return_data"] and not existing["factory_storage_post"]
    assert "CREATE2" not in existing["child_types"] and not existing["events"]
    unauthorized = observed["deploy_unauthorized_new"]
    assert not unauthorized["success"] and unauthorized["revert_selector"] == "0x27fba80a"
    assert not unauthorized["factory_storage_post"]
    fresh = observed["deploy_authorized_new"]
    assert fresh["success"] and "CREATE2" in fresh["child_types"]
    assert [event["topic0"] for event in fresh["events"]] == [deployed_topic]
    owner_fresh = observed["deploy_owner_new"]
    assert owner_fresh["success"] and "CREATE2" in owner_fresh["child_types"]
    assert [event["topic0"] for event in owner_fresh["events"]] == [deployed_topic]
    computed = json.loads((PROBES / "compute_new_user.json").read_text())
    new_initcode = code_prefix + word(NEW_USER)
    predicted_new = "0x" + cast_keccak("0xff" + FACTORY[2:] + cast_keccak(NEW_USER)[2:]
                                         + cast_keccak(new_initcode)[2:])[-40:]
    assert "0x" + fresh["return_data"][-40:].lower() == predicted_new
    assert "0x" + owner_fresh["return_data"][-40:].lower() == predicted_new
    assert "0x" + computed["return"][-40:].lower() == predicted_new
    assert len(fresh["factory_storage_post"]) == 2
    zero_user = observed["deploy_zero_user"]
    zero_address = "0x" + "00" * 20
    predicted_zero = "0x" + cast_keccak("0xff" + FACTORY[2:] + cast_keccak(zero_address)[2:]
                                          + cast_keccak(code_prefix + word(zero_address))[2:])[-40:]
    assert zero_user["success"] and "CREATE2" in zero_user["child_types"]
    assert "0x" + zero_user["return_data"][-40:].lower() == predicted_zero
    setter = observed["set_deployer_owner"]
    assert setter["success"] and len(setter["events"]) == 1
    assert setter["events"][0]["topic0"] == deployer_topic
    assert int(setter["factory_storage_post"][f"0x{4:064x}"], 16) == int(NEW_DEPLOYER, 16)
    assert observed["set_deployer_outsider"]["revert_selector"] == "0x30cd7471"
    zero_deployer = observed["set_deployer_zero"]
    assert zero_deployer["success"] and zero_deployer["events"][0]["topic0"] == deployer_topic
    assert int(zero_deployer["factory_storage_pre"][f"0x{4:064x}"], 16) == int(DEPLOYER, 16)
    assert f"0x{4:064x}" not in zero_deployer["factory_storage_post"]
    assert observed["transfer_owner_outsider"]["revert_selector"] == "0x30cd7471"
    assert observed["transfer_owner_zero"]["revert_selector"] == "0x904bc503"
    assert observed["bootstrap_admin_current"]["revert_selector"] == "0x3f733c4f"
    assert observed["bootstrap_outsider_current"]["revert_selector"] == "0xc031a0df"
    bootstrap = observed["bootstrap_admin_uninitialized"]
    assert bootstrap["success"] and [x["topic0"] for x in bootstrap["events"]] == [owner_topic, deployer_topic]
    assert int(bootstrap["factory_storage_post"][f"0x{3:064x}"], 16) == int(NEW_OWNER, 16)
    assert int(bootstrap["factory_storage_post"][f"0x{4:064x}"], 16) == int(NEW_DEPLOYER, 16)
    assert observed["legacy_initialize_current"]["revert_selector"] == "0xb7b2509c"
    assert observed["three_address_initializer_current"]["revert_selector"] == "0x0dc149f0"
    assert cast_keccak("AlreadyInitialized()")[:10] == "0x0dc149f0"
    zero_exchange = json.loads((PROBES / "direct_impl_zero_exchange.call.json").read_text())
    assert zero_exchange["output"][:10] == "0x40892c33" and zero_exchange.get("error")
    assert cast_keccak("InvalidExchange()")[:10] == "0x40892c33"
    error_paths = {
        "0x0dc149f0": ("AlreadyInitialized()", ["three_address_initializer_current"]),
        "0x27fba80a": (None, ["deploy_unauthorized_new"]),
        "0x30cd7471": (None, ["set_deployer_outsider", "transfer_owner_outsider"]),
        "0x3f733c4f": (None, ["bootstrap_admin_current"]),
        "0x40892c33": ("InvalidExchange()", ["direct_impl_zero_exchange"]),
        "0x904bc503": (None, ["transfer_owner_zero"]),
        "0xb7b2509c": (None, ["legacy_initialize_current"]),
        "0xc031a0df": (None, ["bootstrap_outsider_current"]),
    }
    error_catalog = [{"selector": selector, "probe_paths": paths,
                      "public_signature_candidates": [signature] if signature else [],
                      "status": "simulated_revert_selector"}
                     for selector, (signature, paths) in error_paths.items()]

    output = {
        "pin": PIN, "factory_proxy": FACTORY, "implementation": IMPLEMENTATION,
        "source": "pinned runtime, creation and deployment transactions, getter traces, sampled deposit runtimes, read-only probes",
        "external_report": "https://guardian.security/portfolio/papertrade/protocol-review-2026-10-09/",
        "external_report_status": "public audit descriptions only; referenced source repository was inaccessible and has no demonstrated bytecode match",
        "initializer": {"selector": "0x56e8d85b", "argument_shape": "address,address,address",
                        "arguments_at_creation": [EXCHANGE, creation["from"].lower(), DEPLOYER],
                        "topics": [owner_topic, deployer_topic]},
        "admin_only_uninitialized_path": {"selector": "0x0f71c8bc", "argument_shape": "address,address",
                                          "current_revert_selector": "0x3f733c4f",
                                          "hypothetical_owner_zero_probe": bootstrap},
        "create2": {"deployer": FACTORY, "salt_formula": "keccak256(abi.encodePacked(user))",
                    "initcode_formula": "captured Create2DepositProxy creation code with abi.encode(exchange,user) tail",
                    "sampled_matches": len(matches), "sampled_total": len(records),
                    "all_recorded_deployments_matched": all_deployments["create2_formula_matches"],
                    "all_deployments_evidence": "factory_event_deployments.json",
                    "sampled_addresses": matches,
                    "new_user_probe_address": predicted_new,
                    "zero_user_probe_address": predicted_zero},
        "mapping_slots": {"proxyOf(user)": 1, "isProxy(proxy)": 2},
        "direct_storage": {"0": {"raw": pinned_words["slots"]["0"], "exchange_bits": [16, 175],
                                 "low_byte_initialized": slot0 & 0xff},
                           "3": {"raw": pinned_words["slots"]["3"], "owner": OWNER},
                           "4": {"raw": pinned_words["slots"]["4"], "authorized_deployer": DEPLOYER}},
        "event_signatures": {"OwnerUpdated(address)": owner_topic,
                             "AuthorizedDeployerUpdated(address)": deployer_topic,
                             "ProxyDeployed(address,address)": deployed_topic},
        "simulated_error_catalog": error_catalog,
        "probes": observed,
        "limits": [
            "The exact source names for selectors 0x56e8d85b and 0x0f71c8bc remain unknown despite their argument shapes and observed behavior.",
            "All 22,586 recorded CREATE2 addresses are checked in factory_event_deployments.json; runtime-code uniformity is sampled for 41 instances.",
            "The admin-only uninitialized branch uses a hypothetical state override and has not executed on the live initialized proxy.",
            "No inaccessible audit source has been treated as a deployed bytecode match.",
        ],
    }
    path = ATLAS / "factory_behavior.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(f"wrote {path}: {all_deployments['create2_formula_matches']} CREATE2 addresses, {len(observed)} branch probes")


if __name__ == "__main__":
    main()
