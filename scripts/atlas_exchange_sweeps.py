#!/usr/bin/env python3
"""Reconcile sampled Papertrade Exchange sweep requests and finalizations."""

import argparse
import json
import os
import pathlib
import subprocess
import urllib.request

from atlas_factory_events import Keccak

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
HISTORICAL = ROOT / "artifacts" / "historical"
ARTIFACTS = ROOT / "artifacts" / "exchange_sweeps"
PROBES = ROOT / "artifacts" / "exchange_sweep_probes"
LOCAL = ROOT / "artifacts" / "exchange_sweep_archive_local"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
FACTORY = "0x1629b7d46bef6e13ff754174fc9f32dea309b38f"
PRE_SPOT = "0x" + "00" * 18 + "0801"
PRE_PERP = "0x" + "00" * 18 + "0803"
REQUEST = "0xe0189108"
FINALIZE = "0x6d142da1"
SEEN_REQUEST = "0xd4ee56dd5d1e271b8fc142e340362d3ab1eede92a9810ab33de4d90a9f798257"
SEEN_FINALIZE = "0x2f9333500c9e715e4c974f2c6bc7bb20ad3897ad6135d6d9788805fec95dc4e8"
PIN = 48902346
RELAYER = "0xdf1bda875c9393a663ce69bf6a7fbaa73dfd053d"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
OUTSIDER = "0x" + "33" * 20


def word(value):
    return f"{value:064x}" if isinstance(value, int) else value.removeprefix("0x").rjust(64, "0")


def rpc(url, method, params):
    request = urllib.request.Request(url, json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                                                     "params": params}).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def selected_pairs():
    rows = json.loads((HISTORICAL / "exchange_recent_range_txlist.json").read_text())
    requests = {}
    finalizations = []
    for row in rows:
        data = row.get("input", "")
        if data.startswith(REQUEST):
            requests.setdefault(data[-40:].lower(), []).append(row)
        elif data.startswith(FINALIZE):
            finalizations.append(row)
    pairs = []
    for done in finalizations:
        user = done["input"][-40:].lower()
        candidates = [start for start in requests.get(user, [])
                      if 0 < int(done["blockNumber"]) - int(start["blockNumber"]) < 20]
        if not candidates:
            continue
        start = max(candidates, key=lambda row: int(row["blockNumber"]))
        pairs.append({"user": "0x" + user, "request_tx": start["hash"],
                      "request_block": int(start["blockNumber"]), "finalize_tx": done["hash"],
                      "finalize_block": int(done["blockNumber"])})
    pairs.sort(key=lambda row: (row["request_block"], row["request_tx"], row["finalize_tx"]))
    assert len(pairs) >= 100
    picks = [pairs[round(i * (len(pairs) - 1) / 11)] for i in range(12)]
    if not any(p["request_tx"] == SEEN_REQUEST and p["finalize_tx"] == SEEN_FINALIZE for p in picks):
        picks.append({"user": "0x1730a930cfd0da43255081801bf1a3eb0b69ec83",
                      "request_tx": SEEN_REQUEST, "request_block": 48902092,
                      "finalize_tx": SEEN_FINALIZE, "finalize_block": 48902093})
    return picks


def artifact_path(tx, suffix):
    historical = HISTORICAL / f"{tx}.{suffix}.json"
    return historical if historical.exists() else ARTIFACTS / f"{tx}.{suffix}.json"


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    picks = selected_pairs()
    (ARTIFACTS / "selected_pairs.json").write_text(json.dumps({"sampling": "12 evenly spaced recent pairs plus saved pair",
                                                             "pairs": picks}, indent=2) + "\n")
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(manifest["block"]), False])
    assert header["hash"].lower() == manifest["block_hash"]
    for pair in picks:
        for tx in (pair["request_tx"], pair["finalize_tx"]):
            for suffix, method, params in (
                ("calls", "debug_traceTransaction", [tx, {"tracer": "callTracer", "tracerConfig": {"withLog": True}}]),
                ("receipt", "eth_getTransactionReceipt", [tx]),
                ("state_diff", "debug_traceTransaction", [tx, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}]),
            ):
                path = artifact_path(tx, suffix)
                if path.exists():
                    continue
                result = rpc(url, method, params)
                path.write_text(json.dumps(result, indent=2) + "\n")
        print(pair["request_block"], pair["finalize_block"], pair["user"], flush=True)
    capture_probes(url, picks, header["hash"])


def capture_probes(url, pairs, block_hash):
    PROBES.mkdir(parents=True, exist_ok=True)
    user = pairs[-1]["user"]
    request_call = json.loads(artifact_path(pairs[-1]["request_tx"], "calls").read_text())
    proxy = next(x["to"] for x in descendants(request_call)
                 if x.get("input", "").startswith("0x925b3aad"))
    keccak = Keccak()
    slot = mapping_slot(proxy, 32, keccak)
    getter_path = PROBES / "pinned_last_sweep_block.json"
    if not getter_path.exists():
        values = {}
        for key in (proxy, user):
            result = rpc(url, "eth_call", [{"to": EXCHANGE, "data": "0xf84a74d3" + word(key)}, hex(PIN)])
            values[key] = result
        storage = rpc(url, "eth_getStorageAt", [EXCHANGE, slot, hex(PIN)])
        getter_path.write_text(json.dumps({"pin": PIN, "block_hash": block_hash,
                                           "proxy": proxy, "user": user, "mapping_slot": slot,
                                           "raw_storage": storage, "getter_returns": values}, indent=2) + "\n")
    cases = {
        "request_outsider": (OUTSIDER, REQUEST + word(user), None),
        "finalize_outsider": (OUTSIDER, FINALIZE + word(user), None),
        "sweep_outsider": (OUTSIDER, "0x01681a62" + word(user), None),
        "reconcile_outsider": (OUTSIDER, "0x6a3214c9" + word(user) + word(1), None),
        "finalize_relayer_no_pending": (RELAYER, FINALIZE + word(user), None),
        "reconcile_owner_zero": (OWNER, "0x6a3214c9" + word(user) + word(0), None),
        "reconcile_owner_one": (OWNER, "0x6a3214c9" + word(user) + word(1), None),
        "finalize_outsider_hypothetical_pending": (
            OUTSIDER, FINALIZE + word(user),
            {EXCHANGE: {"stateDiff": {mapping_slot(user, 33, keccak):
                                         "0x" + word(1 + ((PIN - 1) << 128))}}}),
        "finalize_relayer_hypothetical_pending": (
            RELAYER, FINALIZE + word(user),
            {EXCHANGE: {"stateDiff": {mapping_slot(user, 33, keccak):
                                         "0x" + word(1 + ((PIN - 1) << 128))}}}),
    }
    for name, (sender, data, override) in cases.items():
        path = PROBES / f"{name}.call.json"
        if path.exists():
            continue
        call = {"from": sender, "to": EXCHANGE, "data": data, "gas": "0x1000000"}
        options = {"tracer": "callTracer", "tracerConfig": {"withLog": True}}
        if override:
            options["stateOverrides"] = override
        result = rpc(url, "debug_traceCall", [call, hex(PIN), options])
        path.write_text(json.dumps(result, indent=2) + "\n")
        print(name, "error" if result.get("error") else "success", flush=True)
    diff_path = PROBES / "reconcile_owner_one.diff.json"
    if not diff_path.exists():
        call = {"from": OWNER, "to": EXCHANGE, "data": "0x6a3214c9" + word(user) + word(1),
                "gas": "0x1000000"}
        result = rpc(url, "debug_traceCall", [call, hex(PIN), {"tracer": "prestateTracer",
                                                            "tracerConfig": {"diffMode": True}}])
        diff_path.write_text(json.dumps(result, indent=2) + "\n")


def mock_return(*values):
    code = "0x"
    for index, value in enumerate(values):
        code += "7f" + word(value) + "60" + f"{32 * index:02x}" + "52"
    return code + "60" + f"{32 * len(values):02x}" + "6000f3"


def capture_local(url):
    LOCAL.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(PIN), False])
    assert header["hash"].lower() == manifest["block_hash"]
    archived_words = json.loads((ATLAS / "exchange_storage_words.json").read_text())["slots"]
    for slot in (14, 22):
        actual = rpc(url, "eth_getStorageAt", [EXCHANGE, hex(slot), hex(PIN)])
        assert int(actual, 16) == int(archived_words[str(slot)], 16), f"local fork differs from pinned archive at slot {slot}"
    pair = selected_pairs()[-1]
    user = pair["user"]
    req = load(pair["request_tx"], "calls")
    proxy = next(x["to"] for x in descendants(req) if x.get("input", "").startswith("0x925b3aad"))
    keccak = Keccak()
    pending_slot = mapping_slot(user, 33, keccak)
    last_slot = mapping_slot(proxy, 32, keccak)
    original_last = rpc(url, "eth_getStorageAt", [EXCHANGE, last_slot, hex(PIN)])
    amount = 100000000
    large = 10000000000
    cases = {
        "request_good": (REQUEST + word(user), 0, 0, amount, 0),
        "request_same_block": (REQUEST + word(user), 0, PIN, amount, 0),
        "request_no_balance": (REQUEST + word(user), 0, 0, 0, 0),
        "sweep_good": ("0x01681a62" + word(user), 0, 0, amount, 0),
        "finalize_no_pending": (FINALIZE + word(user), 0, 0, 0, 0),
        "finalize_same_block": (FINALIZE + word(user), amount + (PIN << 128), 0, 0, 0),
        "finalize_unchanged": (FINALIZE + word(user), amount + ((PIN - 1) << 128), 0, amount, 0),
        "finalize_decreased": (FINALIZE + word(user), amount + ((PIN - 1) << 128), 0, 0, 0),
        "finalize_partial": (FINALIZE + word(user), amount + ((PIN - 1) << 128), 0, 1, 0),
        "finalize_increased": (FINALIZE + word(user), amount + ((PIN - 1) << 128), 0, amount + 1, 0),
        "sweep_with_pending": ("0x01681a62" + word(user), amount + ((PIN - 1) << 128), 0, 0, 0),
        "request_above_minimum": (REQUEST + word(user), 0, 0, large, 0),
        "sweep_above_minimum": ("0x01681a62" + word(user), 0, 0, large, 0),
        "finalize_unchanged_above_minimum": (FINALIZE + word(user), large + ((PIN - 1) << 128), 0, large, 0),
        "finalize_decreased_above_minimum": (FINALIZE + word(user), large + ((PIN - 1) << 128), 0, 0, 0),
        "finalize_partial_above_minimum": (FINALIZE + word(user), large + ((PIN - 1) << 128), 0, 1, 0),
        "finalize_increased_above_minimum": (FINALIZE + word(user), large + ((PIN - 1) << 128), 0, large + 1, 0),
        "request_perp_below_minimum": (REQUEST + word(user), 0, 0, 0, 9999999),
        "request_perp_at_minimum": (REQUEST + word(user), 0, 0, 0, 10000000),
        "finalize_perp_zero": (FINALIZE + word(user), (100000000 << 64) + ((PIN - 1) << 128), 0, 0, 0),
        "finalize_perp_partial": (FINALIZE + word(user), (100000000 << 64) + ((PIN - 1) << 128), 0, 0, 1),
        "finalize_perp_unchanged": (FINALIZE + word(user), (100000000 << 64) + ((PIN - 1) << 128), 0, 0, 100000000),
        "finalize_perp_equal_normalized_spot": (FINALIZE + word(user), (100000000 << 64) + ((PIN - 1) << 128), 0, 10000000000, 0),
        "finalize_perp_spot_below_normalized": (FINALIZE + word(user), (100000000 << 64) + ((PIN - 1) << 128), 0, 9999999999, 0),
    }
    for name, (data, pending, last_override, spot, perp) in cases.items():
        call_path = LOCAL / f"{name}.call.json"
        diff_path = LOCAL / f"{name}.diff.json"
        if call_path.exists() and diff_path.exists():
            continue
        rpc(url, "anvil_setStorageAt", [EXCHANGE, pending_slot, "0x" + word(pending)])
        rpc(url, "anvil_setStorageAt", [EXCHANGE, last_slot,
                                        "0x" + word(last_override) if last_override else original_last])
        rpc(url, "anvil_setCode", [PRE_SPOT, mock_return(spot, 0, 0)])
        rpc(url, "anvil_setCode", [PRE_PERP, mock_return(perp)])
        rpc(url, "anvil_setCode", ["0x" + "33" * 20, "0x00"])
        call = {"from": OUTSIDER, "to": EXCHANGE, "data": data, "gas": "0x1000000"}
        for suffix, options, path in (
            ("call", {"tracer": "callTracer", "tracerConfig": {"withLog": True}}, call_path),
            ("diff", {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}, diff_path),
        ):
            if path.exists():
                continue
            result = rpc(url, "debug_traceCall", [call, hex(PIN), options])
            path.write_text(json.dumps({"pin": PIN, "block_hash": header["hash"], "user": user,
                                        "proxy": proxy, "pending_slot": pending_slot,
                                        "last_sweep_slot": last_slot, "mock_spot": spot,
                                        "mock_perp": perp, "pending_override": pending,
                                        "last_sweep_override": last_override,
                                        "trace": result}, indent=2) + "\n")
        print(name, "error" if json.loads(call_path.read_text())["trace"].get("error") else "success", flush=True)
    capture_local_minimum(url, user, pending_slot, last_slot, original_last, header["hash"])


def capture_local_minimum(url, user, pending_slot, last_slot, original_last, block_hash):
    path = LOCAL / "minimum_threshold.json"
    if path.exists():
        return
    rpc(url, "anvil_setStorageAt", [EXCHANGE, pending_slot, "0x" + word(0)])
    rpc(url, "anvil_setStorageAt", [EXCHANGE, last_slot, original_last])
    rpc(url, "anvil_setCode", [PRE_PERP, mock_return(0)])
    rpc(url, "anvil_setCode", ["0x" + "33" * 20, "0x00"])
    def probe(amount):
        rpc(url, "anvil_setCode", [PRE_SPOT, mock_return(amount, 0, 0)])
        return rpc(url, "debug_traceCall", [
            {"from": OUTSIDER, "to": EXCHANGE, "data": REQUEST + word(user), "gas": "0x1000000"},
            hex(PIN), {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
    lower, upper = 100000000, 10000000000
    assert probe(lower).get("output") == "0x329c2b0f"
    assert not probe(upper).get("error")
    while lower + 1 < upper:
        middle = (lower + upper) // 2
        if probe(middle).get("error"):
            lower = middle
        else:
            upper = middle
    failed = probe(lower)
    passed = probe(upper)
    assert lower == 999999999 and upper == 1000000000
    assert failed.get("output") == "0x329c2b0f" and not passed.get("error")
    path.write_text(json.dumps({"pin": PIN, "block_hash": block_hash,
                                "controlled_mock": "HyperCore spot balance and CoreWriter code",
                                "maximum_failure_raw": lower, "minimum_success_raw": upper,
                                "maximum_failure_revert_selector": failed["output"],
                                "minimum_success_events": [log for call in descendants(passed)
                                                           for log in call.get("logs", [])
                                                           if log["address"].lower() == EXCHANGE]}, indent=2) + "\n")
    print("minimum request balance:", upper, "raw spot units", flush=True)


def load(tx, suffix):
    return json.loads(artifact_path(tx, suffix).read_text())


def descendants(node):
    for child in node.get("calls", []):
        yield child
        yield from descendants(child)


def mapping_slot(key, base, keccak):
    return "0x" + keccak(bytes.fromhex(word(key)) + base.to_bytes(32, "big")).hex()


def output_words(data):
    assert len(data[2:]) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def signature_selector(signature):
    return subprocess.run(["cast", "sig", signature], capture_output=True,
                          text=True, check=True).stdout.strip().lower()


def analyze():
    keccak = Keccak()
    selected = json.loads((ARTIFACTS / "selected_pairs.json").read_text())["pairs"]
    assert len(selected) == 13
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN
    assert signature_selector("requestSweep(address)") == REQUEST
    assert signature_selector("finalizeSweep(address)") == FINALIZE
    assert signature_selector("lastSweepBlock(address)") == "0xf84a74d3"
    request_topic = "0x" + keccak(b"SweepRequested(address,address,uint64,uint64,uint32)").hex()
    swept_topic = "0x" + keccak(b"Swept(address,uint256)").hex()
    assert request_topic == "0x02d61879cd72906e0951e3a96096407dd2b1f2cd2d063dae983bb20216cf3025"
    assert swept_topic == "0xc36b5179cb9c303b200074996eab2b3473eac370fdd7eba3bec636fe35109696"

    records = []
    for pair in selected:
        user = pair["user"]
        request = load(pair["request_tx"], "calls")
        finalize = load(pair["finalize_tx"], "calls")
        request_receipt = load(pair["request_tx"], "receipt")
        finalize_receipt = load(pair["finalize_tx"], "receipt")
        request_diff = load(pair["request_tx"], "state_diff")
        finalize_diff = load(pair["finalize_tx"], "state_diff")
        assert request["to"].lower() == finalize["to"].lower() == EXCHANGE
        assert request["input"] == REQUEST + word(user)
        assert finalize["input"] == FINALIZE + word(user)
        assert request_receipt["status"] == finalize_receipt["status"] == "0x1"
        assert int(request_receipt["blockNumber"], 16) == pair["request_block"]
        assert int(finalize_receipt["blockNumber"], 16) == pair["finalize_block"]
        request_calls = list(descendants(request))
        finalize_calls = list(descendants(finalize))
        proxy_calls = [x for x in request_calls if x.get("input", "").startswith("0x925b3aad")]
        assert len(proxy_calls) == 1
        proxy = proxy_calls[0]["to"].lower()
        assert proxy_calls[0]["from"].lower() == EXCHANGE
        factory_calls = [x for x in request_calls if x.get("to", "").lower() == FACTORY
                         and x.get("input", "").startswith("0xc1a9a508")]
        assert len(factory_calls) == 1 and int(factory_calls[0]["output"], 16) == int(proxy, 16)
        raw_spot = [x for x in request_calls if x.get("to", "").lower() == PRE_SPOT]
        raw_perp = [x for x in request_calls if x.get("to", "").lower() == PRE_PERP]
        assert len(raw_spot) == len(raw_perp) == 1
        assert output_words(raw_spot[0]["input"]) == [int(proxy, 16), 0]
        assert output_words(raw_perp[0]["input"]) == [int(proxy, 16)]
        spot = output_words(raw_spot[0]["output"])[0]
        perp = output_words(raw_perp[0]["output"])[0]
        assert spot > 0 and perp == 0
        sweep_args = [int(proxy_calls[0]["input"][10 + i * 64:74 + i * 64], 16) for i in range(3)]
        assert sweep_args == [0, spot, perp]
        core_calls = [x for x in descendants(proxy_calls[0]) if x.get("to", "").lower() == "0x" + "33" * 20]
        assert len(core_calls) == 1 and core_calls[0]["input"].startswith("0x17938e13")
        encoded = bytes.fromhex(core_calls[0]["input"][2:])
        raw_action = encoded[68:68 + int.from_bytes(encoded[36:68], "big")]
        assert raw_action[:4].hex() == "01000006"
        assert output_words("0x" + raw_action[4:].hex()) == [int(EXCHANGE, 16), 0, spot]
        request_logs = [x for x in request_receipt["logs"] if x["address"].lower() == EXCHANGE
                        and x["topics"][0].lower() == request_topic]
        assert len(request_logs) == 1
        assert request_logs[0]["topics"] == [request_topic, "0x" + word(user), "0x" + word(proxy)]
        assert output_words(request_logs[0]["data"]) == [spot, perp, pair["request_block"]]

        pending_slot = mapping_slot(user, 33, keccak)
        last_slot = mapping_slot(proxy, 32, keccak)
        balance_slot = mapping_slot(user, 9, keccak)
        req_post = request_diff["post"][EXCHANGE]["storage"]
        assert int(req_post[pending_slot], 16) == spot + (perp << 64) + (pair["request_block"] << 128)
        assert int(req_post[last_slot], 16) == pair["request_block"]
        assert "0x" + word(14) not in req_post and "0x" + word(22) not in req_post
        assert balance_slot not in req_post

        fin_spot = [x for x in finalize_calls if x.get("to", "").lower() == PRE_SPOT]
        fin_perp = [x for x in finalize_calls if x.get("to", "").lower() == PRE_PERP]
        assert len(fin_spot) == len(fin_perp) == 1
        current_spot = output_words(fin_spot[0]["output"])[0]
        current_perp = output_words(fin_perp[0]["output"])[0]
        assert current_spot == current_perp == 0
        swept_logs = [x for x in finalize_receipt["logs"] if x["address"].lower() == EXCHANGE
                      and x["topics"][0].lower() == swept_topic]
        assert len(swept_logs) == 1 and swept_logs[0]["topics"] == [swept_topic, "0x" + word(user)]
        credited = spot * 10**10
        assert output_words(swept_logs[0]["data"]) == [credited]
        fin_pre = finalize_diff["pre"][EXCHANGE]["storage"]
        fin_post = finalize_diff["post"][EXCHANGE]["storage"]
        assert int(fin_pre[pending_slot], 16) == int(req_post[pending_slot], 16)
        assert pending_slot not in fin_post
        slot14, slot22 = "0x" + word(14), "0x" + word(22)
        treasury_delta = int(fin_post[slot14], 16) - int(fin_pre[slot14], 16)
        balance_delta = int(fin_post[balance_slot], 16) - int(fin_pre.get(balance_slot, "0x0"), 16)
        before22, after22 = int(fin_pre[slot22], 16), int(fin_post[slot22], 16)
        total_balance_delta = (after22 & ((1 << 128) - 1)) - (before22 & ((1 << 128) - 1))
        locked_margin_delta = (after22 >> 128) - (before22 >> 128)
        assert treasury_delta == total_balance_delta == balance_delta == credited
        assert locked_margin_delta == 0
        records.append({"user": user, "proxy": proxy, "request_tx": pair["request_tx"],
                        "request_block": pair["request_block"], "finalize_tx": pair["finalize_tx"],
                        "finalize_block": pair["finalize_block"], "spot_raw": spot, "perp_raw": perp,
                        "finalize_spot_raw": current_spot, "finalize_perp_raw": current_perp,
                        "credited_internal": credited, "pending_slot": pending_slot,
                        "last_sweep_block_slot": last_slot, "user_balance_slot": balance_slot,
                        "treasury_delta": treasury_delta, "total_balances_delta": total_balance_delta,
                        "user_balance_delta": balance_delta, "locked_margin_delta": locked_margin_delta})
    assert len({x["request_tx"] for x in records}) == len(records)
    assert signature_selector("sweep(address)") == "0x01681a62"
    assert signature_selector("reconcileSweepCredit(address,uint256)") == "0x6a3214c9"
    cleared_topic = "0x" + keccak(b"PendingSweepCleared(address,address)").hex()
    assert cleared_topic == "0x28f3adb5fa23ae5c83c811e67caf2ec192a816e4ef898c7f90d1484f65a9717e"
    reconcile_topic = "0x8da9931e615ce9dfd2d7914e0cee3246839757203d34810cde64e0d0026f75c3"
    pinned_getter = json.loads((PROBES / "pinned_last_sweep_block.json").read_text())
    assert pinned_getter["block_hash"] == manifest["block_hash"]
    assert int(pinned_getter["getter_returns"][pinned_getter["proxy"]], 16) == int(pinned_getter["raw_storage"], 16) == 48902092
    assert int(pinned_getter["getter_returns"][pinned_getter["user"]], 16) == 0
    simulated_errors = {
        "0x0a9e0180": ("NoCoreBalance()", ["request_outsider", "sweep_outsider", "finalize_outsider_hypothetical_pending", "finalize_relayer_hypothetical_pending"]),
        "0x0984a617": ("NoPendingSweep()", ["finalize_outsider", "finalize_relayer_no_pending"]),
        "0x30cd7471": (None, ["reconcile_outsider"]),
        "0x329c2b0f": ("SweepBelowMinimum()", ["request_good", "request_no_balance", "sweep_good", "finalize_unchanged", "finalize_increased", "request_perp_below_minimum"]),
        "0xd26ffacb": ("SweepStillPending()", ["finalize_same_block"]),
        "0xfefe83a0": ("SweepAlreadyRequestedThisBlock()", ["request_same_block"]),
    }
    for selector, (signature, paths) in simulated_errors.items():
        if signature:
            assert signature_selector(signature) == selector
        for name in paths:
            directory = LOCAL if (LOCAL / f"{name}.call.json").exists() else PROBES
            trace = json.loads((directory / f"{name}.call.json").read_text())
            if directory == LOCAL:
                assert trace["block_hash"] == manifest["block_hash"]
                trace = trace["trace"]
            assert trace.get("output") == selector and trace.get("error")
    local_expectations = {
        "request_above_minimum": [request_topic],
        "sweep_above_minimum": [request_topic],
        "finalize_decreased": [swept_topic],
        "finalize_partial": [swept_topic],
        "finalize_decreased_above_minimum": [swept_topic],
        "finalize_partial_above_minimum": [swept_topic],
        "sweep_with_pending": [swept_topic],
        "finalize_unchanged_above_minimum": [cleared_topic, request_topic],
        "finalize_increased_above_minimum": [cleared_topic, request_topic],
        "request_perp_at_minimum": [request_topic],
        "finalize_perp_zero": [swept_topic],
        "finalize_perp_partial": [swept_topic],
        "finalize_perp_unchanged": [cleared_topic, request_topic],
        "finalize_perp_equal_normalized_spot": [cleared_topic, request_topic],
        "finalize_perp_spot_below_normalized": [swept_topic],
    }
    for name, expected in local_expectations.items():
        row = json.loads((LOCAL / f"{name}.call.json").read_text())
        trace = row["trace"]
        assert row["block_hash"] == manifest["block_hash"] and not trace.get("error")
        topics = [log["topics"][0] for call in descendants(trace)
                  for log in call.get("logs", []) if log["address"].lower() == EXCHANGE]
        assert topics == expected, (name, topics)
        if swept_topic in expected:
            swept_log = next(log for call in descendants(trace) for log in call.get("logs", [])
                             if log["address"].lower() == EXCHANGE and log["topics"][0] == swept_topic)
            pending_spot = row["pending_override"] & ((1 << 64) - 1)
            pending_perp = (row["pending_override"] >> 64) & ((1 << 64) - 1)
            assert output_words(swept_log["data"]) == [(pending_spot + 100 * pending_perp) * 10**10]
        if name in ("request_perp_at_minimum", "finalize_perp_unchanged", "finalize_perp_equal_normalized_spot"):
            requested = [log for call in descendants(trace) for log in call.get("logs", [])
                         if log["address"].lower() == EXCHANGE and log["topics"][0] == request_topic]
            assert len(requested) == 1
            assert output_words(requested[0]["data"]) == {
                "request_perp_at_minimum": [0, 10000000, PIN],
                "finalize_perp_unchanged": [0, 100000000, PIN],
                "finalize_perp_equal_normalized_spot": [10000000000, 0, PIN],
            }[name]
        if name == "request_perp_at_minimum":
            writer_calls = [call for call in descendants(trace) if call.get("to", "").lower() == "0x" + "33" * 20]
            assert len(writer_calls) == 2
            actions = []
            for call in writer_calls:
                payload = bytes.fromhex(call["input"][2:])
                actions.append(payload[68:68 + int.from_bytes(payload[36:68], "big")])
            assert [action[:4].hex() for action in actions] == ["01000007", "01000006"]
            assert output_words("0x" + actions[1][4:].hex()) == [int(EXCHANGE, 16), 0, 1000000000]
    local_count = len(list(LOCAL.glob("*.call.json")))
    assert local_count == 24
    minimum = json.loads((LOCAL / "minimum_threshold.json").read_text())
    assert minimum["pin"] == PIN and minimum["block_hash"] == manifest["block_hash"]
    assert minimum["maximum_failure_raw"] == 999999999
    assert minimum["minimum_success_raw"] == 1000000000
    assert minimum["maximum_failure_revert_selector"] == "0x329c2b0f"
    assert [x["topics"][0] for x in minimum["minimum_success_events"]] == [request_topic]
    reconcile = json.loads((PROBES / "reconcile_owner_one.call.json").read_text())
    reconcile_logs = [log for call in descendants(reconcile) for log in call.get("logs", [])
                      if log["address"].lower() == EXCHANGE]
    assert not reconcile.get("error") and len(reconcile_logs) == 1
    assert reconcile_logs[0]["topics"] == [reconcile_topic, "0x" + word(pinned_getter["user"])]
    assert output_words(reconcile_logs[0]["data"]) == [10**12]
    reconcile_diff = json.loads((PROBES / "reconcile_owner_one.diff.json").read_text())
    pre, post = (reconcile_diff[k][EXCHANGE]["storage"] for k in ("pre", "post"))
    reconcile_balance = mapping_slot(pinned_getter["user"], 9, keccak)
    slot14, slot22 = "0x" + word(14), "0x" + word(22)
    assert int(post[slot14], 16) - int(pre[slot14], 16) == 10**12
    assert int(post[reconcile_balance], 16) - int(pre[reconcile_balance], 16) == 10**12
    assert (int(post[slot22], 16) & ((1 << 128) - 1)) - (int(pre[slot22], 16) & ((1 << 128) - 1)) == 10**12
    assert int(post[slot22], 16) >> 128 == int(pre[slot22], 16) >> 128
    error_catalog = [{"selector": selector, "reconstructed_signature": signature,
                      "probe_paths": paths,
                      "public_signature_candidates": [signature] if signature else []}
                     for selector, (signature, paths) in sorted(simulated_errors.items())]
    event_catalog = [
        {"topic0": request_topic, "reconstructed_signature": "SweepRequested(address,address,uint64,uint64,uint32)",
         "indexed_fields": ["user", "proxy"], "data_fields": ["spotRaw", "perpRaw", "block"], "status": "observed_historical"},
        {"topic0": swept_topic, "reconstructed_signature": "Swept(address,uint256)",
         "indexed_fields": ["user"], "data_fields": ["creditedInternal"], "status": "observed_historical"},
        {"topic0": cleared_topic, "reconstructed_signature": "PendingSweepCleared(address,address)",
         "indexed_fields": ["user", "proxy"], "data_fields": [], "status": "simulated_log_only"},
        {"topic0": reconcile_topic, "reconstructed_signature": None,
         "indexed_fields": ["user"], "data_fields": ["creditedInternal"], "status": "simulated_log_only"},
    ]
    result = {"pin": PIN, "block_hash": manifest["block_hash"], "sample_count": len(records),
              "selection": "12 evenly spaced paired transactions from the saved recent-range txlist plus one previously traced pair",
              "address": EXCHANGE, "implementation": manifest["contracts"][EXCHANGE]["implementation"] if "implementation" in manifest["contracts"][EXCHANGE] else next(a for a, c in manifest["contracts"].items() if c["role"] == "exchange_implementation"),
              "event_signatures": {"SweepRequested(address,address,uint64,uint64,uint32)": request_topic,
                                   "Swept(address,uint256)": swept_topic,
                                   "PendingSweepCleared(address,address)": cleared_topic},
              "event_catalog": event_catalog,
              "selector_reconstructions": {REQUEST: "requestSweep(address)", FINALIZE: "finalizeSweep(address)",
                                            "0xf84a74d3": "lastSweepBlock(address)",
                                            "0x01681a62": "sweep(address)",
                                            "0x6a3214c9": "reconcileSweepCredit(address,uint256)"},
              "simulated_error_catalog": error_catalog,
              "local_replay_count": local_count,
              "local_replay_source": "archive-backed Anvil fork; baseline slots 14 and 22 checked against pinned archive capture",
              "fork_comparison": "exchange_sweep_fork_comparison.json",
              "minimum_request_raw": minimum["minimum_success_raw"],
              "perp_to_spot_multiplier": 100, "minimum_perp_only_raw": 10000000,
              "owner_reconcile_credit_scale": 10**12,
              "owner_reconcile_event_name_status": "unresolved",
              "mapping_bases": {"balances": 9, "lastSweepBlock_proxy": 32, "pendingSweep_user": 33},
              "records": records,
              "limits": ["All sampled historical requests had spot token 0 and zero perp balance; the Exchange perp branch is supported by controlled local fork cases only.",
                         "A CoreWriter enqueue event and a later zero proxy balance do not prove Exchange-side HyperCore receipt.",
                         "The sample is deterministic and spread across a recent explorer window; it is not all 22,586 proxies or all sweeps."]}
    (ATLAS / "exchange_sweep_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("exchange sweeps:", len(records), "request/finalize pairs reconciled")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--local-rpc-url", help="Local Anvil fork with anvil_setCode, not live chain URL")
    args = parser.parse_args()
    if args.capture:
        capture()
    if args.local_rpc_url:
        capture_local(args.local_rpc_url)
    analyze()
