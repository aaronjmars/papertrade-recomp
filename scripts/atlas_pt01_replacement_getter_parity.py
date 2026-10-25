#!/usr/bin/env python3
"""Compare pinned newest Exchange reads under its original and older replacement."""

import argparse
import concurrent.futures
import gzip
import hashlib
import json
import os
import pathlib
import urllib.request

from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "pt01_replacement_getter_parity" / "pinned_calls.json"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
ORIGINAL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
REPLACEMENT = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
BLOCK = 48_902_346
TRADER = "0xe284a7f6bb1b157f9df589a0a7709d22f82e762b"
STALLED_USERS = ["0x56cbe78a5cdfa10147927aec550aa7f2fb3d3d01",
                 "0x9c8599c32224d7d9956a7def18f7314162f77baf"]
STALLED_PROXIES = ["0x1e8a704179cc6221592c362daa52a341ae20084d",
                   "0xf6b60cdf359af5538495831a9f2bbcada23e10e6"]
POSITION_ID = 1_394_063


def encode_word(value):
    return f"{int(value, 16) if isinstance(value, str) else value:064x}"


def cases():
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    rows = catalog[ORIGINAL]["functions"]
    result = []
    for row in rows:
        if row["state_mutability"] not in ("view", "pure"):
            continue
        selector, shape = row["selector"], row["arguments"]
        if selector == "0xfb9f1009":
            continue  # unpauseMarket(uint32) is a disabled mutation despite its catalog label
        if shape == "":
            inputs = [()]
        elif shape == "address":
            if selector in ("0x31a4956c", "0x7e4174fc"):
                inputs = [(user,) for user in STALLED_USERS]
            elif selector == "0xf84a74d3":
                inputs = [(proxy,) for proxy in STALLED_PROXIES]
            else:
                inputs = [(TRADER,)]
        elif shape == "uint32":
            inputs = [(0,), (1,)]
        elif shape == "uint256":
            inputs = [(POSITION_ID,)]
        else:
            continue
        for values in inputs:
            result.append({"selector": selector, "arguments": shape,
                           "signature": row.get("reconstructed_signature", ""),
                           "inputs": list(values),
                           "calldata": selector + "".join(encode_word(value) for value in values)})
    assert len(result) >= 55
    assert len({row["selector"] for row in result}) >= 50
    return result


def call(url, calldata, replacement, caller=None):
    target = {"to": EXCHANGE, "data": calldata}
    if caller is not None:
        target["from"] = caller
    request = {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
               "params": [target, hex(BLOCK)]}
    if replacement:
        request["params"].append({EXCHANGE: {"stateDiff": {
            IMPLEMENTATION_SLOT: "0x" + encode_word(REPLACEMENT)}}})
    req = urllib.request.Request(url, json.dumps(request).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        reply = json.load(response)
    if "error" in reply:
        error = reply["error"]
        return {"status": "error", "code": error.get("code"),
                "message": error.get("message"), "data": error.get("data")}
    return {"status": "success", "data": reply["result"]}


def capture():
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(BLOCK), False])
    implementation_word = rpc(url, "eth_getStorageAt", [EXCHANGE, IMPLEMENTATION_SLOT, hex(BLOCK)])
    assert header["hash"].lower() == manifest["block_hash"]
    assert int(implementation_word, 16) == int(ORIGINAL, 16)
    control = {"original": call(url, "0x5c60da1b", False, ADMIN),
               "replacement": call(url, "0x5c60da1b", True, ADMIN)}
    assert control["original"] == {"status": "success", "data": "0x" + encode_word(ORIGINAL)}
    assert control["replacement"] == {"status": "success", "data": "0x" + encode_word(REPLACEMENT)}
    probes = cases()
    def paired(row):
        return {**row, "original": call(url, row["calldata"], False),
                "replacement": call(url, row["calldata"], True)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(paired, probes))
    payload = {"pin": BLOCK, "block_hash": header["hash"],
               "implementation_word": implementation_word,
               "replacement": REPLACEMENT, "override_slot": IMPLEMENTATION_SLOT,
               "override_control": control, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    return verify()


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    payload = json.loads(OUT.read_text())
    assert payload["pin"] == manifest["block"] == BLOCK
    assert payload["block_hash"].lower() == manifest["block_hash"].lower()
    assert int(payload["implementation_word"], 16) == int(ORIGINAL, 16)
    assert payload["replacement"] == REPLACEMENT
    assert payload["override_slot"] == IMPLEMENTATION_SLOT
    assert payload["override_control"] == {
        "original": {"status": "success", "data": "0x" + encode_word(ORIGINAL)},
        "replacement": {"status": "success", "data": "0x" + encode_word(REPLACEMENT)},
    }
    assert payload["rows"] and len(payload["rows"]) == len(cases())
    for address in (EXCHANGE, ORIGINAL, REPLACEMENT):
        row = manifest["contracts"][address]
        runtime = (ATLAS / row["runtime_file"]).read_text().strip()
        assert hashlib.sha256(bytes.fromhex(runtime[2:])).hexdigest() == row["sha256"]
    assert [{k: row[k] for k in ("selector", "arguments", "signature", "inputs", "calldata")}
            for row in payload["rows"]] == cases()
    matched = [row for row in payload["rows"] if row["original"] == row["replacement"]]
    mismatched = [row for row in payload["rows"] if row["original"] != row["replacement"]]
    success = [row for row in matched if row["original"]["status"] == "success"]
    errors = [row for row in matched if row["original"]["status"] == "error"]
    assert len(success) == len(payload["rows"]) and not errors and not mismatched
    balance = next(row for row in success if row["selector"] == "0x27e235e3"
                   and row["inputs"] == [TRADER])
    assert int(balance["original"]["data"], 16) > 0
    stalled_capture = json.loads(gzip.decompress((ROOT / "artifacts" /
        "audit_sweep_event_census" / "stalled_sweeps.json.gz").read_bytes()))
    assert stalled_capture["pin"] == BLOCK
    for case in stalled_capture["cases"]:
        pending = next(row for row in success if row["selector"] == "0x7e4174fc"
                       and row["inputs"] == [case["user"]])
        assert int(pending["original"]["data"], 16) == int(case["pending_word"], 16) > 0
    return {"pin": BLOCK, "calls": len(payload["rows"]),
            "distinct_selectors": len({row["selector"] for row in payload["rows"]}),
            "successful_matching_calls": len(success),
            "matching_errors": len(errors), "mismatches": len(mismatched),
            "runtime_hashes": {address: manifest["contracts"][address]["sha256"]
                               for address in (EXCHANGE, ORIGINAL, REPLACEMENT)},
            "limits": [
                "The replacement is installed by a read-only EIP-1967 state override at the audit pin.",
                "Only the listed calldata shapes and pinned state are compared; the disabled unpauseMarket selector is excluded.",
                "Matching getters do not establish mutation, upgrade, or Core settlement safety.",
            ]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh archive read comparison")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))
