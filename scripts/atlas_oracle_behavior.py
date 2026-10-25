#!/usr/bin/env python3
"""Capture read-only PriceOracle branches at the Papertrade pinned block."""

import argparse
import json
import os
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PROBES = ROOT / "artifacts" / "oracle_probes"
CREATION = ROOT / "artifacts" / "oracle_creation"
LOCAL = ROOT / "artifacts" / "oracle_archive_local_replay"
HISTORICAL = ROOT / "artifacts" / "historical"
PIN = 48902346
PROXY = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
IMPLEMENTATION = "0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x" + "33" * 20
NEW_OWNER = "0x" + "11" * 20
CREATE_TX = "0x9b66014c5dfeb4d4fe9bd45bbc681f8628edbbbd8a3a2dbe19d155ed5de63f9d"
TRANSFER_TX = "0xac56a54f03ee74fcdefca55f69a680f39856c5f5730fc1045fd591aa68e8a290"
PRE_ORACLE = "0x" + "00" * 18 + "0807"
PRE_MARK = "0x" + "00" * 18 + "0806"
PRE_BBO = "0x" + "00" * 18 + "080e"


def word(value):
    return f"{value:064x}" if isinstance(value, int) else value.removeprefix("0x").rjust(64, "0")


def returndata(*values):
    code = "0x"
    for i, value in enumerate(values):
        code += "7f" + word(value) + "60" + f"{32 * i:02x}" + "52"
    code += "60" + f"{32 * len(values):02x}" + "6000f3"
    return code


def rpc(url, method, params):
    request = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                                                     "params": params}).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def scalar(selector, asset=0):
    return selector + word(asset)


def array(selector, assets):
    return selector + word(32) + word(len(assets)) + "".join(word(x) for x in assets)


def cases():
    good_bbo = {PRE_BBO: {"code": returndata(100, 200)}}
    all_good = {PRE_ORACLE: {"code": returndata(150)}, PRE_MARK: {"code": returndata(155)}, **good_bbo}
    return {
        "owner_getter": (OUTSIDER, "0x8da5cb5b", None, PROXY),
        "oracle_real_zero": (OUTSIDER, scalar("0x2af78bd1"), None, PROXY),
        "oracle_mock": (OUTSIDER, scalar("0x2af78bd1", 7), {PRE_ORACLE: {"code": returndata(150)}}, PROXY),
        "oracle_mock_zero": (OUTSIDER, scalar("0x2af78bd1"), {PRE_ORACLE: {"code": returndata(0)}}, PROXY),
        "mark_mock": (OUTSIDER, scalar("0xa066fae9", 7), {PRE_MARK: {"code": returndata(155)}}, PROXY),
        "mark_mock_zero": (OUTSIDER, scalar("0xa066fae9"), {PRE_MARK: {"code": returndata(0)}}, PROXY),
        "bbo_mock": (OUTSIDER, scalar("0xfb466481", 7), good_bbo, PROXY),
        "bbo_mock_crossed": (OUTSIDER, scalar("0xfb466481"), {PRE_BBO: {"code": returndata(200, 100)}}, PROXY),
        "bbo_mock_zero": (OUTSIDER, scalar("0xfb466481"), {PRE_BBO: {"code": returndata(0, 0)}}, PROXY),
        "mid_mock": (OUTSIDER, scalar("0xc0182669", 7), good_bbo, PROXY),
        "mid_mock_crossed": (OUTSIDER, scalar("0xc0182669"), {PRE_BBO: {"code": returndata(200, 100)}}, PROXY),
        "mid_mock_zero": (OUTSIDER, scalar("0xc0182669"), {PRE_BBO: {"code": returndata(0, 0)}}, PROXY),
        "snapshot_mock": (OUTSIDER, scalar("0x766cd255", 7), all_good, PROXY),
        "snapshots_empty": (OUTSIDER, array("0xa7f06462", []), all_good, PROXY),
        "snapshots_two": (OUTSIDER, array("0xa7f06462", [0, 7]), all_good, PROXY),
        "transfer_owner_outsider": (OUTSIDER, "0xf2fde38b" + word(NEW_OWNER), None, PROXY),
        "transfer_owner_current": (OWNER, "0xf2fde38b" + word(NEW_OWNER), None, PROXY),
        "transfer_owner_zero": (OWNER, "0xf2fde38b" + word(0), None, PROXY),
        "initialize_proxy_current": (OUTSIDER, "0xc4d66de8" + word(NEW_OWNER), None, PROXY),
        "initialize_implementation": (OUTSIDER, "0xc4d66de8" + word(NEW_OWNER), None, IMPLEMENTATION),
    }


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    PROBES.mkdir(parents=True, exist_ok=True)
    CREATION.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    storage_path = PROBES / "pinned_slot0.json"
    if not storage_path.exists():
        words = {address: rpc(url, "eth_getStorageAt", [address, "0x0", hex(PIN)])
                 for address in (PROXY, IMPLEMENTATION)}
        storage_path.write_text(json.dumps({"pin": PIN, "block_hash": header["hash"],
                                            "slot": 0, "words": words}, indent=2) + "\n")
    for suffix, method in (("transaction", "eth_getTransactionByHash"),
                           ("receipt", "eth_getTransactionReceipt"),
                           ("calls", "debug_traceTransaction")):
        path = CREATION / f"{CREATE_TX}.{suffix}.json"
        if path.exists():
            continue
        params = [CREATE_TX, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}] if suffix == "calls" else [CREATE_TX]
        path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")
    for name, (sender, data, override, target) in cases().items():
        path = PROBES / f"{name}.call.json"
        if path.exists():
            continue
        options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
        if override:
            options["stateOverrides"] = override
        call = {"from": sender, "to": target, "data": data, "gas": "0x1000000"}
        path.write_text(json.dumps(rpc(url, "debug_traceCall", [call, hex(PIN), options]), indent=2) + "\n")
        print(name, flush=True)


def local_cases():
    good = (returndata(150), returndata(155), returndata(100, 200))
    empty = "0x00"
    return {
        "oracle_good": (scalar("0x2af78bd1", 7), good),
        "oracle_zero": (scalar("0x2af78bd1", 7), (returndata(0), good[1], good[2])),
        "oracle_empty": (scalar("0x2af78bd1", 7), (empty, good[1], good[2])),
        "oracle_revert": (scalar("0x2af78bd1", 7), ("0x60006000fd", good[1], good[2])),
        "oracle_out_of_range": (scalar("0x2af78bd1", 7), (returndata(2**64), good[1], good[2])),
        "mark_good": (scalar("0xa066fae9", 7), good),
        "mark_zero": (scalar("0xa066fae9", 7), (good[0], returndata(0), good[2])),
        "mark_empty": (scalar("0xa066fae9", 7), (good[0], empty, good[2])),
        "bbo_good": (scalar("0xfb466481", 7), good),
        "bbo_crossed": (scalar("0xfb466481", 7), (good[0], good[1], returndata(200, 100))),
        "bbo_zero": (scalar("0xfb466481", 7), (good[0], good[1], returndata(0, 0))),
        "bbo_short": (scalar("0xfb466481", 7), (good[0], good[1], returndata(100))),
        "mid_good": (scalar("0xc0182669", 7), good),
        "mid_odd": (scalar("0xc0182669", 7), (good[0], good[1], returndata(101, 200))),
        "mid_max": (scalar("0xc0182669", 7), (good[0], good[1], returndata(2**64 - 1, 2**64 - 1))),
        "mid_crossed": (scalar("0xc0182669", 7), (good[0], good[1], returndata(200, 100))),
        "mid_zero": (scalar("0xc0182669", 7), (good[0], good[1], returndata(0, 0))),
        "mid_zero_bid": (scalar("0xc0182669", 7), (good[0], good[1], returndata(0, 100))),
        "mid_zero_ask": (scalar("0xc0182669", 7), (good[0], good[1], returndata(100, 0))),
        "snapshot_good": (scalar("0x766cd255", 7), good),
        "snapshot_narrow": (scalar("0x766cd255", 7), (returndata(125), returndata(75), returndata(20, 30))),
        "snapshot_crossed": (scalar("0x766cd255", 7), (good[0], good[1], returndata(200, 100))),
        "snapshot_zero_bbo": (scalar("0x766cd255", 7), (good[0], good[1], returndata(0, 0))),
        "snapshots_empty": (array("0xa7f06462", []), good),
        "snapshots_two": (array("0xa7f06462", [0, 7]), good),
    }


def capture_local(url):
    LOCAL.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    archived_words = json.loads((PROBES / "pinned_slot0.json").read_text())["words"]
    for address in (PROXY, IMPLEMENTATION):
        actual = rpc(url, "eth_getStorageAt", [address, "0x0", hex(PIN)])
        assert int(actual, 16) == int(archived_words[address], 16), f"local fork differs from pinned archive at {address} slot 0"
    addresses = (PRE_ORACLE, PRE_MARK, PRE_BBO)
    for name, (data, codes) in local_cases().items():
        path = LOCAL / f"{name}.call.json"
        if path.exists():
            continue
        for address, code in zip(addresses, codes, strict=True):
            rpc(url, "anvil_setCode", [address, code])
        call = {"from": OUTSIDER, "to": PROXY, "data": data, "gas": "0x1000000"}
        result = rpc(url, "debug_traceCall", [call, hex(PIN), {"tracer": "callTracer"}])
        path.write_text(json.dumps({"pin": PIN, "block_hash": header["hash"],
                                    "mock_runtime_codes": dict(zip(addresses, codes, strict=True)),
                                    "trace": result}, indent=2) + "\n")
        print(name, "error" if result.get("error") else "success", flush=True)


def read_local(name):
    return json.loads((LOCAL / f"{name}.call.json").read_text())


def local_trace(name):
    return read_local(name)["trace"]


def output_words(node):
    raw = node.get("output", "0x")
    assert len(raw[2:]) % 64 == 0
    return [int(raw[i:i + 64], 16) for i in range(2, len(raw), 64)]


def revert_reason(node):
    raw = bytes.fromhex(node.get("output", "0x")[2:])
    if len(raw) < 68 or raw[:4].hex() != "08c379a0":
        return None
    length = int.from_bytes(raw[36:68], "big")
    return raw[68:68 + length].decode()


def signature_hash(signature, event=False):
    args = ["cast", "keccak" if event else "sig", signature]
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip().lower()


def descendants(node):
    for child in node.get("calls", []):
        yield child
        yield from descendants(child)


def analyze():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    expected_hash = manifest["block_hash"]
    for name in local_cases():
        assert read_local(name)["block_hash"].lower() == expected_hash
    sigs = {
        "0x2af78bd1": "getOraclePrice(uint32)",
        "0x766cd255": "getPriceSnapshot(uint32)",
        "0x8da5cb5b": "owner()",
        "0xa066fae9": "getMarkPrice(uint32)",
        "0xc4d66de8": "initialize(address)",
        "0xf2fde38b": "transferOwnership(address)",
        "0xfb466481": "getBBO(uint32)",
    }
    assert all(signature_hash(sig) == sel for sel, sig in sigs.items())
    owner_topic = signature_hash("OwnerUpdated(address)", event=True)
    assert owner_topic == "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b"
    assert signature_hash("AlreadyInitialized()") == "0x0dc149f0"
    slot = json.loads((PROBES / "pinned_slot0.json").read_text())
    assert slot["block_hash"].lower() == expected_hash
    proxy_word = int(slot["words"][PROXY], 16)
    assert (proxy_word >> 16) & ((1 << 160) - 1) == int(OWNER, 16)
    assert proxy_word & 0xffff == 1
    assert int(slot["words"][IMPLEMENTATION], 16) == 0

    assert output_words(local_trace("oracle_good")) == [150]
    assert output_words(local_trace("mark_good")) == [155]
    assert revert_reason(local_trace("oracle_zero")) == "Oracle price is zero"
    assert revert_reason(local_trace("oracle_empty")) == "Oracle read failed"
    assert revert_reason(local_trace("oracle_revert")) == "Oracle read failed"
    assert local_trace("oracle_out_of_range").get("error")
    assert revert_reason(local_trace("mark_zero")) == "Mark price is zero"
    assert revert_reason(local_trace("mark_empty")) == "Mark price read failed"
    for name, expected in {"bbo_good": [100, 200], "bbo_crossed": [200, 100],
                           "bbo_zero": [0, 0]}.items():
        assert output_words(local_trace(name)) == expected
    assert revert_reason(local_trace("bbo_short")) == "BBO read failed"
    assert output_words(local_trace("mid_good")) == [150]
    assert output_words(local_trace("mid_odd")) == [150]
    assert output_words(local_trace("mid_max")) == [2**64 - 1]
    assert revert_reason(local_trace("mid_crossed")) == "BBO crossed"
    for name in ("mid_zero", "mid_zero_bid", "mid_zero_ask"):
        assert revert_reason(local_trace(name)) == "BBO unavailable"
    snapshots = {name: output_words(local_trace(name)) for name in
                 ("snapshot_good", "snapshot_narrow", "snapshot_crossed", "snapshot_zero_bbo",
                  "snapshots_empty", "snapshots_two")}
    assert snapshots["snapshot_good"] == [150, 155, 100, 200, 100]
    assert snapshots["snapshot_narrow"] == [125, 75, 20, 30, 10]
    assert snapshots["snapshot_crossed"] == [150, 155, 200, 100, 0]
    assert snapshots["snapshot_zero_bbo"] == [150, 155, 0, 0, 0]
    assert snapshots["snapshots_empty"] == [32, 0]
    assert snapshots["snapshots_two"] == [32, 2] + snapshots["snapshot_good"] * 2
    for name, target in (("oracle_good", PRE_ORACLE), ("mark_good", PRE_MARK),
                         ("bbo_good", PRE_BBO), ("mid_good", PRE_BBO)):
        calls = [x for x in descendants(local_trace(name)) if x.get("to", "").lower() == target]
        assert len(calls) == 1 and int(calls[0]["input"], 16) == 7
    snapshot_calls = [x["to"].lower() for x in descendants(local_trace("snapshot_good"))
                      if x.get("to", "").lower() in (PRE_ORACLE, PRE_MARK, PRE_BBO)]
    assert snapshot_calls == [PRE_ORACLE, PRE_MARK, PRE_BBO]

    creation_call = json.loads((CREATION / f"{CREATE_TX}.calls.json").read_text())
    initializer = next(x for x in creation_call["calls"] if x["to"].lower() == IMPLEMENTATION)
    initial_owner = "0x" + initializer["input"][-40:]
    assert initializer["input"].startswith("0xc4d66de8")
    assert initial_owner == "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
    creation_receipt = json.loads((CREATION / f"{CREATE_TX}.receipt.json").read_text())
    assert creation_receipt["status"] == "0x1"
    assert creation_receipt["logs"][0]["topics"] == [owner_topic, "0x" + word(initial_owner)]
    assert json.loads((PROBES / "initialize_proxy_current.call.json").read_text())["output"] == "0x0dc149f0"
    impl_init = json.loads((PROBES / "initialize_implementation.call.json").read_text())
    assert not impl_init.get("error") and impl_init["logs"][0]["topics"][0] == owner_topic
    assert json.loads((PROBES / "transfer_owner_outsider.call.json").read_text())["output"] == "0x30cd7471"
    for name, recipient in (("transfer_owner_current", NEW_OWNER),
                            ("transfer_owner_zero", "0x" + "00" * 20)):
        probe = json.loads((PROBES / f"{name}.call.json").read_text())
        assert not probe.get("error")
        logs = [x for x in descendants(probe) if x.get("logs")]
        assert len(logs) == 1 and logs[0]["logs"][0]["topics"] == [owner_topic, "0x" + word(recipient)]

    transfer = json.loads((HISTORICAL / f"{TRANSFER_TX}.calls.json").read_text())
    assert transfer["input"] == "0xf2fde38b" + word(OWNER)
    transfer_receipt = json.loads((HISTORICAL / f"{TRANSFER_TX}.receipt.json").read_text())
    assert transfer_receipt["status"] == "0x1"
    assert transfer_receipt["logs"][0]["topics"] == [owner_topic, "0x" + word(OWNER)]
    transfer_diff = json.loads((HISTORICAL / f"{TRANSFER_TX}.state_diff.json").read_text())
    assert int(transfer_diff["post"][PROXY]["storage"]["0x" + "00" * 32], 16) == proxy_word

    historical_midpoints = []
    for path in sorted(HISTORICAL.glob("*.calls.json")):
        root = json.loads(path.read_text())
        for call in descendants(root):
            if call.get("to", "").lower() != PROXY or not call.get("input", "").startswith("0xc0182669"):
                continue
            precompiles = [x for x in descendants(call) if x.get("to", "").lower() == PRE_BBO]
            assert len(precompiles) == 1 and len(precompiles[0]["output"]) == 130
            bid, ask = output_words(precompiles[0])
            midpoint = int(call["output"], 16)
            assert 0 < bid <= ask and midpoint == (bid + ask) // 2
            historical_midpoints.append({"tx": path.name.split(".")[0], "asset": int(call["input"][10:74], 16),
                                         "bid": bid, "ask": ask, "midpoint": midpoint})
    assert len(historical_midpoints) >= 14

    behavior = {
        "pin": PIN, "block_hash": expected_hash, "oracle_proxy": PROXY, "implementation": IMPLEMENTATION,
        "owner": OWNER, "initial_owner": initial_owner, "slot0": slot["words"][PROXY],
        "owner_field_bits": [16, 175], "initialized_low_byte": 1,
        "selector_reconstructions": sigs,
        "unresolved_selector_semantics": {
            "0xc0182669": "uint32 asset -> validated BBO midpoint uint64, floor((bid+ask)/2)",
            "0xa7f06462": "uint32[] assets -> five-word price snapshot array",
        },
        "precompile_paths": {"getOraclePrice": PRE_ORACLE, "getMarkPrice": PRE_MARK,
                             "getBBO": PRE_BBO},
        "snapshot_fields": ["oracle", "mark", "bid", "ask", "max(ask-bid,0)"],
        "snapshot_probe_outputs": snapshots,
        "historical_midpoint_count": len(historical_midpoints),
        "historical_midpoints": historical_midpoints,
        "creation_tx": CREATE_TX, "historical_owner_transfer_tx": TRANSFER_TX,
        "event_catalog": [{"topic0": owner_topic, "reconstructed_signature": "OwnerUpdated(address)",
                           "indexed_fields": ["newOwner"], "data_fields": [], "status": "observed_historical"}],
        "simulated_error_catalog": [
            {"selector": "0x0dc149f0", "reconstructed_signature": "AlreadyInitialized()",
             "probe_paths": ["initialize_proxy_current"], "public_signature_candidates": ["AlreadyInitialized()"]},
            {"selector": "0x30cd7471", "reconstructed_signature": None,
             "probe_paths": ["transfer_owner_outsider"], "public_signature_candidates": []},
        ],
        "pinned_probe_count": len(list(PROBES.glob("*.call.json"))),
        "local_replay_count": len(list(LOCAL.glob("*.call.json"))),
        "local_replay_source": "archive-backed Anvil fork; baseline slot 0 checked against pinned archive capture",
        "fork_comparison": "oracle_fork_comparison.json",
        "limitations": ["The archive RPC does not reproduce historical HyperCore read precompile output in debug_traceCall.",
                        "Local Anvil uses mock precompile code on the pinned EVM fork; these branches are simulations.",
                        "Historical trading transactions independently verify the BBO midpoint path only.",
                        "Exact source names for selectors 0xc0182669 and 0xa7f06462 remain unknown."],
    }
    (ATLAS / "oracle_behavior.json").write_text(json.dumps(behavior, indent=2) + "\n")
    print("oracle behavior: 9 selectors,", behavior["local_replay_count"], "local replays,",
          len(historical_midpoints), "historical midpoint calls")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--local-rpc-url", help="Local Anvil fork with anvil_setCode; never a live chain URL")
    args = parser.parse_args()
    if args.capture:
        capture()
    if args.local_rpc_url:
        capture_local(args.local_rpc_url)
    if args.capture and not args.local_rpc_url and not all(
        (LOCAL / f"{name}.call.json").exists() for name in local_cases()
    ):
        print("archive capture complete; local fork replays are still needed")
    else:
        analyze()
