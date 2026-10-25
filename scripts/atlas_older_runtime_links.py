#!/usr/bin/env python3
"""Classify older runtime differences and capture their pinned linked libraries."""

import argparse
import collections
import gzip
import hashlib
import json
import os
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SCOPE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "deployer_scope" / "older_linked_libraries.json.gz"
PIN = 48_902_346
OLD_EXCHANGE_LIBRARY = "0xac8ba1307815f74bd13d4d039c96f7b97e81aa49"
OLD_MATH_1 = "0x3c69230dfaf54e0b70f11134429c7ca4e2f11321"
OLD_MATH_2 = "0x261a4113a9bced5d545f8edd340cc9c81dc96c94"
LIBRARIES = (OLD_EXCHANGE_LIBRARY, OLD_MATH_1, OLD_MATH_2)
VARIANT_LIBRARY = "0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388"
LIVE_LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
LIVE_MATH = "0xe991817199363046da0a28da6fbad0284e4aa492"
NOVEL_POSITIONS = {3: "Exchange implementation", 9: "Tokenomics implementation",
                   15: "BatchExecutor implementation", 17: "multisig"}


def saved_inputs():
    scope = json.loads(gzip.decompress(SCOPE.read_bytes()))
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert scope["pin"] == manifest["block"] == PIN
    assert scope["block_hash"] == manifest["block_hash"]
    return scope, manifest


def code(row):
    return bytes.fromhex(row["runtime"][2:])


def sha(value):
    return hashlib.sha256(value).hexdigest()


def push20_sites(runtime, address):
    target = bytes.fromhex(address[2:])
    sites = []
    pc = 0
    while pc < len(runtime):
        opcode = runtime[pc]
        if 0x60 <= opcode <= 0x7F:
            length = opcode - 0x5F
            if length == 20 and runtime[pc + 1:pc + 21] == target:
                sites.append(pc + 1)
            pc += length + 1
        else:
            pc += 1
    return sites


def normalized(runtime, address, count):
    sites = push20_sites(runtime, address)
    assert len(sites) == count, (address, sites)
    result = bytearray(runtime)
    for site in sites:
        result[site:site + 20] = bytes(20)
    return bytes(result), sites


def selectors(runtime):
    return {
        "0x" + match.group(1).hex()
        for match in re.finditer(b"\x63(.{4})\x14\x61(.{2})\x57", runtime[:1500], re.DOTALL)
    }


def capture():
    scope, _ = saved_inputs()
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    calls = [
        {"jsonrpc": "2.0", "id": index, "method": "eth_getCode",
         "params": [address, hex(PIN)]}
        for index, address in enumerate(LIBRARIES)
    ]
    request = urllib.request.Request(
        url, json.dumps(calls).encode(), {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        results = json.load(response)
    assert isinstance(results, list) and len(results) == len(calls)
    libraries = {}
    for row in results:
        assert "error" not in row
        address = LIBRARIES[row["id"]]
        assert address not in libraries and row["result"] != "0x"
        libraries[address] = row["result"]
    payload = {"pin": PIN, "block_hash": scope["block_hash"], "libraries": libraries}
    OUT.write_bytes(
        gzip.compress(json.dumps(payload, separators=(",", ":")).encode(), compresslevel=9, mtime=0)
    )
    return verify()


def verify():
    scope, manifest = saved_inputs()
    saved = json.loads(gzip.decompress(OUT.read_bytes()))
    assert saved["pin"] == PIN and saved["block_hash"] == scope["block_hash"]
    assert set(saved["libraries"]) == set(LIBRARIES)
    libraries = {address: bytes.fromhex(value[2:]) for address, value in saved["libraries"].items()}
    assert len(libraries[OLD_EXCHANGE_LIBRARY]) == 5873
    assert sha(libraries[OLD_EXCHANGE_LIBRARY]) == "86184c390d6f62a8bd0e97080a0959ba7a3860b1358635994f82f61e81ceac8c"
    live_math = bytes.fromhex((ATLAS / manifest["contracts"][LIVE_MATH]["runtime_file"]).read_text().strip()[2:])
    assert sha(live_math) == manifest["contracts"][LIVE_MATH]["sha256"]
    assert libraries[OLD_MATH_1] == libraries[OLD_MATH_2] == live_math
    assert len(live_math) == 585

    rows = scope["rows"]
    known_hashes = {item["sha256"] for item in manifest["contracts"].values()}
    older_by_hash = collections.defaultdict(list)
    for index, row in enumerate(rows[:38]):
        older_by_hash[sha(code(row))].append(index)
    novel = {digest: indices for digest, indices in older_by_hash.items() if digest not in known_hashes}
    assert len(novel) == 6
    assert {index % 19 for indices in novel.values() for index in indices} == set(NOVEL_POSITIONS)
    assert sorted(index for indices in novel.values() for index in indices) == [3, 9, 15, 17, 22, 28, 36]

    normalized_tokenomics = []
    tokenomics_sites = []
    for index, library in ((9, OLD_MATH_1), (28, OLD_MATH_2), (47, LIVE_MATH)):
        reduced, sites = normalized(code(rows[index]), library, 2)
        normalized_tokenomics.append(reduced)
        tokenomics_sites.append(sites)
    assert normalized_tokenomics[0] == normalized_tokenomics[1] == normalized_tokenomics[2]
    assert tokenomics_sites == [[2068, 2727]] * 3

    original_second, original_sites = normalized(code(rows[22]), VARIANT_LIBRARY, 10)
    newest, newest_sites = normalized(code(rows[41]), LIVE_LIBRARY, 10)
    assert original_second == newest and original_sites == newest_sites
    assert original_sites == [2695, 2783, 7039, 8807, 9145, 10586, 14286, 14445, 18017, 20558]

    first_batch, second_batch, newest_batch = (code(rows[index]) for index in (15, 34, 53))
    assert second_batch == newest_batch
    assert len(first_batch) == len(newest_batch) == 3451
    assert first_batch[:3408] == newest_batch[:3408]
    assert first_batch[3440:] == newest_batch[3440:]
    assert first_batch[3408:3440] != newest_batch[3408:3440]
    assert first_batch[3398:3408] == newest_batch[3398:3408] == bytes.fromhex("a2646970667358221220")

    first_multisig, second_multisig, newest_multisig = (code(rows[index]) for index in (17, 36, 55))
    assert first_multisig == second_multisig
    assert len(first_multisig) == 2713 and len(newest_multisig) == 3134
    old_multisig_selectors, new_multisig_selectors = selectors(first_multisig), selectors(newest_multisig)
    assert len(old_multisig_selectors) == 11 and len(new_multisig_selectors) == 13

    old_exchange = code(rows[3])
    old_exchange_sites = push20_sites(old_exchange, OLD_EXCHANGE_LIBRARY)
    assert len(old_exchange_sites) == 11
    assert push20_sites(code(rows[23]), VARIANT_LIBRARY) == []  # proxy, not implementation
    assert len(push20_sites(code(rows[57]), VARIANT_LIBRARY)) == 10
    variant_library = bytes.fromhex((ATLAS / manifest["contracts"][VARIANT_LIBRARY]["runtime_file"]).read_text().strip()[2:])
    live_library = bytes.fromhex((ATLAS / manifest["contracts"][LIVE_LIBRARY]["runtime_file"]).read_text().strip()[2:])
    assert sha(variant_library) == manifest["contracts"][VARIANT_LIBRARY]["sha256"]
    assert sha(live_library) == manifest["contracts"][LIVE_LIBRARY]["sha256"]
    assert len(variant_library) == len(live_library) == 5790
    assert variant_library[19:39] == bytes.fromhex(VARIANT_LIBRARY[2:])
    assert live_library[19:39] == bytes.fromhex(LIVE_LIBRARY[2:])
    assert variant_library[:19] == live_library[:19]
    assert variant_library[39:] == live_library[39:]
    old_library_selectors = selectors(libraries[OLD_EXCHANGE_LIBRARY])
    new_library_selectors = selectors(live_library)
    assert len(old_library_selectors) == 11 and len(new_library_selectors) == 10

    return {
        "older_direct_novel_runtime_hashes": len(novel),
        "novel_direct_roles": {str(position): role for position, role in NOVEL_POSITIONS.items()},
        "equivalent_after_link_or_metadata_normalization": [9, 15, 22, 28],
        "additional_linked_library_addresses": list(LIBRARIES),
        "math_library_runtime_shared": True,
        "second_original_exchange_link_sites": len(original_sites),
        "first_exchange_link_sites": len(old_exchange_sites),
        "first_exchange_library_selector_count": len(old_library_selectors),
        "later_exchange_library_selector_count": len(new_library_selectors),
        "old_multisig_selector_count": len(old_multisig_selectors),
        "new_multisig_selector_count": len(new_multisig_selectors),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="refresh pinned archive library code")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))


if __name__ == "__main__":
    main()
