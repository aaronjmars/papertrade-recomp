#!/usr/bin/env python3
"""Verify every factory ProxyDeployed event against the CREATE2 formula."""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import os
import pathlib
import subprocess
import time

try:
    from Crypto.Hash import keccak as crypto_keccak
except ImportError:
    crypto_keccak = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
CAPTURED = ROOT / "artifacts" / "factory_creation"
FACTORY = "0x1629b7d46bef6e13ff754174fc9f32dea309b38f"
DEPLOY_TX = "0xddf30f3fd0d78c0516e37f32ed1ece2ef4ab488d7b4be8439c7196878047fb2e"
TOPIC = "0x3d2489efb661e8b1c3679865db649ca1de61d76a71184a1234de2e55786a6aad"
PIN = 48902346
COUNT = 22586


def capture():
    assert os.environ.get("ETHERSCAN_API_KEY"), "set ETHERSCAN_API_KEY"
    stage, first_block = 1, 47855071
    while True:
        last_rows = None
        for page in range(1, 11):
            path = page_path(stage, page)
            if path.exists():
                rows = json.loads(path.read_text())
            else:
                command = ["etherscan", "logs", "get", "--chain", "999", "--address", FACTORY,
                           "--topic0", TOPIC, "--from-block", str(first_block), "--to-block", str(PIN),
                           "--page", str(page), "--offset", "1000"]
                response = subprocess.run(command, capture_output=True, text=True, check=True, timeout=45)
                rows = json.loads(response.stdout)
                assert 0 < len(rows) <= 1000
                path.write_text(json.dumps(rows, indent=2) + "\n")
                print(f"captured stage {stage} page {page}: {len(rows)} logs", flush=True)
                time.sleep(0.25)
            last_rows = rows
            if len(rows) < 1000:
                return
        next_block = int(last_rows[-1]["blockNumber"], 16)
        assert next_block > first_block, "10,000 log window ends in its starting block"
        stage, first_block = stage + 1, next_block


def page_path(stage, page):
    if stage == 1:
        return CAPTURED / f"proxy_deployed_page{page}.json"
    return CAPTURED / f"proxy_deployed_stage{stage}_page{page}.json"


class Keccak:
    def __init__(self):
        self.library = None
        self.digest = None
        candidates = ("/opt/homebrew/opt/openssl@4/lib/libcrypto.dylib",
                      "/opt/homebrew/opt/openssl@3/lib/libcrypto.dylib",
                      ctypes.util.find_library("crypto"))
        for path in candidates:
            if not path:
                continue
            try:
                library = ctypes.CDLL(path)
                library.EVP_MD_fetch.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
                library.EVP_MD_fetch.restype = ctypes.c_void_p
                digest = library.EVP_MD_fetch(None, b"KECCAK-256", None)
                if not digest:
                    continue
                library.EVP_Digest.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p,
                                               ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p, ctypes.c_void_p]
                library.EVP_Digest.restype = ctypes.c_int
                self.library, self.digest = library, digest
                break
            except (AttributeError, OSError):
                continue
        self.crypto = None if self.digest else crypto_keccak
        self.backend = ("OpenSSL EVP KECCAK-256" if self.digest else
                        "PyCryptodome KECCAK-256" if self.crypto else "cast keccak fallback")
        assert self(bytes.fromhex("deadbeef")).hex() == "d4fd4e189132273036449fc9e11198c739161b4c0116a9a2dccdfa1c492006f1"

    def __call__(self, value):
        if self.digest:
            source = ctypes.create_string_buffer(value)
            result = ctypes.create_string_buffer(64)
            length = ctypes.c_uint()
            ok = self.library.EVP_Digest(source, len(value), result, ctypes.byref(length), self.digest, None)
            if ok != 1 or length.value != 32:
                raise RuntimeError("OpenSSL Keccak digest failed")
            return result.raw[:32]
        if self.crypto:
            return self.crypto.new(data=value, digest_bits=256).digest()
        result = subprocess.run(["cast", "keccak", "0x" + value.hex()], capture_output=True,
                                text=True, check=True).stdout.strip()
        return bytes.fromhex(result[2:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="capture missing explorer log pages")
    args = parser.parse_args()
    if args.capture:
        capture()
    logs, pages, stages = [], 0, 0
    for stage in range(1, 10):
        stages = stage
        for page in range(1, 11):
            rows = json.loads(page_path(stage, page).read_text())
            assert 0 < len(rows) <= 1000
            logs.extend(rows)
            pages += 1
            if len(rows) < 1000:
                break
        if len(rows) < 1000:
            break
    else:
        raise RuntimeError("deployment log pagination did not terminate")
    instances = json.loads((ATLAS / "deposit_proxy_instances.json").read_text())["instances"]
    assert len(instances) == COUNT
    by_address = {row["address"]: row for row in instances}
    assert len(by_address) == COUNT
    trace = json.loads((ROOT / "artifacts" / "historical" / f"{DEPLOY_TX}.calls.json").read_text())
    create = trace["calls"][0]["calls"][0]
    assert create["type"] == "CREATE2"
    initcode = bytes.fromhex(create["input"][2:])
    assert len(initcode) == 1889
    creation_prefix = initcode[:-32]
    keccak = Keccak()
    records = []
    seen_proxies = set()
    for log in logs:
        assert log["address"].lower() == FACTORY and log["topics"][0].lower() == TOPIC
        assert len(log["topics"]) == 3 and log["data"] == "0x"
        user = "0x" + log["topics"][1][-40:].lower()
        proxy = "0x" + log["topics"][2][-40:].lower()
        if proxy in seen_proxies:
            continue
        seen_proxies.add(proxy)
        tx = log["transactionHash"].lower()
        block = int(log["blockNumber"], 16) if str(log["blockNumber"]).startswith("0x") else int(log["blockNumber"])
        assert block <= PIN
        instance = by_address[proxy]
        assert instance["tx"].lower() == tx and instance["block"] == block
        init_hash = keccak(creation_prefix + bytes.fromhex(user[2:].rjust(64, "0")))
        salt = keccak(bytes.fromhex(user[2:]))
        predicted = "0x" + keccak(b"\xff" + bytes.fromhex(FACTORY[2:]) + salt + init_hash)[-20:].hex()
        assert predicted == proxy, f"CREATE2 mismatch for {user}: {predicted} != {proxy}"
        records.append({"user": user, "proxy": proxy, "tx": tx, "block": block})
    assert len({row["proxy"] for row in records}) == COUNT
    mapping = {row["user"]: row["proxy"] for row in records}
    assert len(mapping) == COUNT, "one user appears in more than one deployment event"
    mapped = ATLAS / "factory_user_proxy_map.json"
    mapped.write_text(json.dumps(records, indent=2) + "\n")
    canonical = "\n".join(f"{row['user']}:{row['proxy']}:{row['tx']}" for row in records).encode()
    result = {
        "pin": PIN, "factory": FACTORY,
        "explorer_pages": pages,
        "block_range_stages": stages,
        "raw_event_rows_including_boundary_overlap": len(logs),
        "boundary_overlap_rows": len(logs) - len(records),
        "event_count": len(records),
        "internal_create2_count": len(instances),
        "distinct_users": len(mapping),
        "event_internal_address_tx_block_matches": COUNT,
        "create2_formula_matches": COUNT,
        "keccak_backend": keccak.backend,
        "source": "Etherscan v2 getLogs in rolling <=10,000-row block windows with inclusive boundary overlap, matched to pinned internal CREATE2 rows",
        "user_proxy_map": str(mapped.relative_to(ATLAS)),
        "canonical_user_proxy_tx_sha256": hashlib.sha256(canonical).hexdigest(),
        "first_three": records[:3], "last_three": records[-3:],
        "limits": [
            "Explorer logs and internal traces are independent API surfaces, but both come from the same chain data provider family.",
            "This validates every recorded CREATE2 deployment address and log through the pin, not every function branch of the factory or deposit proxy.",
        ],
    }
    output = ATLAS / "factory_event_deployments.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}: {len(records)} of {COUNT} CREATE2 addresses match")


if __name__ == "__main__":
    main()
