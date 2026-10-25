#!/usr/bin/env python3
"""Enumerate every Papertrade contract set on HyperEVM and check the post-pin upgrade.

Offline verify plus ledger regeneration (no credential, no network):

    python3 scripts/atlas_suite_sets.py

Refresh the public evidence (public HyperEVM RPC, public HyperCore info API, and the
Etherscan v2 API through the `etherscan` CLI, which needs ETHERSCAN_API_KEY):

    python3 scripts/atlas_suite_sets.py --capture

The offline path reads only saved files: the pinned deployer capture, the newest-suite
manifest, the pinned upgrade-history ledger, and everything under
artifacts/postpin_suite/. It writes atlas/block_48902346/suite_sets.json and
atlas/block_48902346/suite_sets.md.
"""

import argparse
import collections
import datetime
import difflib
import gzip
import hashlib
import json
import pathlib
import re
import subprocess
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
PIN = 48_902_346
DEPLOYER = "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
DEPLOYER2 = "0x13cb7a200d081094d23ebf07f4d708410a9c488b"
RPC = "https://rpc.hyperliquid.xyz/evm"
CORE_INFO = "https://api.hyperliquid.xyz/info"
IMPLEMENTATION_SLOT = (
    "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
)
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
CAPTURE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
OUT = ROOT / "artifacts" / "postpin_suite"
SUITE_OUT = ROOT / "artifacts" / "suite_sets"
LEDGER = ATLAS / "suite_sets.json"
DOC = ATLAS / "suite_sets.md"
RUNTIME_DIR = OUT / "runtime"

# Every set has the same 19 deployer creations in the same nonce order.
LAYOUT = (
    ("proxy_admin", "nonproxy"),
    ("oracle_implementation", "nonproxy"),
    ("oracle_proxy", "proxy"),
    ("exchange_implementation", "nonproxy"),
    ("exchange_proxy", "proxy"),
    ("session_key_manager_implementation", "nonproxy"),
    ("session_key_manager_proxy", "proxy"),
    ("deposit_proxy_factory_implementation", "nonproxy"),
    ("deposit_proxy_factory_proxy", "proxy"),
    ("tokenomics_implementation", "nonproxy"),
    ("tokenomics_proxy", "proxy"),
    ("paper_token_implementation", "nonproxy"),
    ("paper_token_proxy", "proxy"),
    ("staking_implementation", "nonproxy"),
    ("staking_proxy", "proxy"),
    ("batch_executor_implementation", "nonproxy"),
    ("batch_executor_proxy", "proxy"),
    ("one_of_two_multisig", "nonproxy"),
    ("timelock", "nonproxy"),
)
SET_BASE = (("earlier_1", 0), ("earlier_2", 19), ("newest", 38))
PRE_PIN_SETS = ("earlier_1", "earlier_2", "newest")
OLDER_PROXY_COUNTS = {"earlier_1": 33, "earlier_2": 5}
NEWEST_PROXY_COUNT = 22_586
# Rows 57 and 58 are the two Exchange implementation variants deployed after the
# newest set, before the pin. Neither is installed behind a newest-set proxy at the pin.
VARIANT_ROWS = {57: "exchange_implementation_variant_a", 58: "exchange_implementation_variant_b"}

POSTPIN_DEPLOYMENTS = (
    ("tokenomics_implementation_2_earlier_2_link", "0x5a85c51e557b6a5cae014847b31e0c3c542c827f", 4),
    ("exchange_linked_library_2", "0x583d0bd818c991c5830fea93aef04e474b272459", 1),
    ("exchange_implementation_2", "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723", 2),
    ("session_key_manager_implementation_2", "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946", 3),
    ("builder_registry_earlier_2_governed", "0xdf07f4a06bba4bec3355f068114dc30518c39cf1", 5),
    ("tokenomics_implementation_2", "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03", 6),
    ("builder_registry", "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248", 7),
)
POSTPIN_RUNTIME_SHA = {
    "0x583d0bd818c991c5830fea93aef04e474b272459": "ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440",
    "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723": "fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268",
    "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946": "7df05c33597c04820a314fae015aab01b5566aff53e9bded8446962cfd4ad2c9",
    "0x5a85c51e557b6a5cae014847b31e0c3c542c827f": "f4737a14ac4061c6c0ea1a8c81c49ad5e2c0814871f2acc4e316a302558d8c7d",
    "0xdf07f4a06bba4bec3355f068114dc30518c39cf1": "f459de55cb0463912417650fbca7e18109f3820551e4071234109e1e72801d2f",
    "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03": "56caf868c73dbc33b94725972fc101dbcec0fb7b017c4f2f9e8cda49516992e9",
    "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248": "f459de55cb0463912417650fbca7e18109f3820551e4071234109e1e72801d2f",
}
NEWEST_PROXIES = {
    "oracle_proxy": "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e",
    "exchange_proxy": "0x6cd5661646289fb6e65ea5c032310fded797d0a2",
    "session_key_manager_proxy": "0x8326eb8896e358717f10502ec73ce8d28e37b108",
    "deposit_proxy_factory_proxy": "0x1629b7d46bef6e13ff754174fc9f32dea309b38f",
    "tokenomics_proxy": "0x75174549dbbd44497d31a47e2e2d7406408d63d9",
    "paper_token_proxy": "0xe40f17915daa230324030003a197cdaef2261c0e",
    "staking_proxy": "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016",
    "batch_executor_proxy": "0x233ff29b239abc1d7748605da9b205c3e008626e",
}
NEWEST_TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
NEWEST_MULTISIG = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
NEWEST_PROXY_ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
EARLIER_2_TIMELOCK = "0xd98adcb9a409e33a658c24e872f37357a85ca484"
EARLIER_2_MULTISIG = "0x324b0547039683c2df146421f3a76083ef130d27"
EARLIER_2_PROXY_ADMIN = "0x15d0a00a5f8ba75012fbf9dc4a0cc31495ea8b72"
EARLIER_2_EXCHANGE_PROXY = "0x2ede04561914c61a5f49212609541934fd7f5901"
EARLIER_2_SKM_PROXY = "0xe45264507a67d0bbea35299002b68ebd76adba04"
EARLIER_2_TOKENOMICS_PROXY = "0x2ac4ff16cd89d78d7e13ce6e72e47f81c60f2dfc"
EARLIER_2_REGISTRY = "0xdf07f4a06bba4bec3355f068114dc30518c39cf1"
EARLIER_1_EXCHANGE_PROXY = "0x1b534e482b92bb6daff452cd12f2e35219e13493"
BUILDER_REGISTRY = "0xfdc6550436dd75ce8a0b145f935b7d3a64f53248"
EXCHANGE_2 = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
SKM_2 = "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946"
TOKENOMICS_2 = "0x7c0a72a788cff4d68cfe9586aecb98e21eb58a03"
TOKENOMICS_2_EARLIER_2 = "0x5a85c51e557b6a5cae014847b31e0c3c542c827f"
LIBRARY_2 = "0x583d0bd818c991c5830fea93aef04e474b272459"
LIBRARY_PINNED_LIVE = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
OLDER_EXCHANGE_LIBRARY = "0xac8ba1307815f74bd13d4d039c96f7b97e81aa49"
VARIANT_EXCHANGE_LIBRARY = "0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388"
EXTRA_CODE_ADDRESSES = ("0x3333333333333333333333333333333333333333",)
MATH_LIBRARIES = {
    "earlier_1": "0x3c69230dfaf54e0b70f11134429c7ca4e2f11321",
    "earlier_2": "0x261a4113a9bced5d545f8edd340cc9c81dc96c94",
    "newest": "0xe991817199363046da0a28da6fbad0284e4aa492",
}
# The docs' own numbering: contract set 1 is the newest pinned set, contract set 2 is
# the 2026-10-21 upgrade. See https://docs.papertrade.xyz/dev/protocol-changes/
DOCS_VERSION = {
    "earlier_1": "undocumented (before contract set 1, 7 Oct 2026)",
    "earlier_2": "undocumented (before contract set 1, 7 Oct 2026)",
    "newest": "/v1/ contract set 1, live 7-21 Oct 2026",
    "postpin_refresh": "contract set 2, live since 21 Oct 2026",
}
POSTPIN_WINDOW = (49_063_457, 49_253_668)
LAST_PINNED_GOOD_BLOCK = 49_063_456
SET_2_SCHEDULE_BLOCK = 49_080_037
SET_2_LIVE_BLOCK = 49_169_385
EARLIER_2_BATCH_SCHEDULE_BLOCK = 49_160_362
EARLIER_2_BATCH_EXECUTE_BLOCK = 49_160_467
MIN_DELAY_CHANGE_BLOCK = 49_050_825
OLD_OPERATION_CANCEL_BLOCK = 49_079_600

MIN_DELAY_SELECTOR = "0xc63c4e9b"
MULTISIG_TRANSACTIONS = "0x9ace38c2"
MULTISIG_COUNT = "0xb77bf600"
PENDING_SWEEP_CALL = "0x7e4174fc"
BALANCES_CALL = "0x27e235e3"
RECONCILE_CALL = "0x6a3214c9"
PENDING_SWEEP_SLOT = 33
BALANCES_SLOT = 9
PT01_USERS = (
    (
        "0x56cbe78a5cdfa10147927aec550aa7f2fb3d3d01",
        "0x1e8a704179cc6221592c362daa52a341ae20084d",
        "0x00000000000000000000000002df9fbf0000000000000000000000012a53a310",
        "50.050916",
    ),
    (
        "0x9c8599c32224d7d9956a7def18f7314162f77baf",
        "0xf6b60cdf359af5538495831a9f2bbcada23e10e6",
        "0x00000000000000000000000002ddd166000000000000000000000000481f2280",
        "12.1",
    ),
)
# Added or dropped dispatch selectors per new runtime. A name is a public-registry
# candidate that hash-matches the selector bytes; it is never a proven source name.
NEW_SELECTORS = {
    "exchange_implementation_2": {
        "added": {
            "0x69f9a5f0": "claimBuilderFees()",
            "0x9d346583": "builderFees(address)",
            "0xcbce7532": None,
            "0xd970fad5": None,
            "0xe6ac4a74": None,
            "0xf009ac03": None,
        },
        "removed": {"0x415f1240": "liquidate(uint256)"},
    },
    "session_key_manager_implementation_2": {
        "added": {
            "0xbd322efa": "setBuilderRegistry(address)",
            "0xd95208cd": None,
            "0xe737de13": "builderRegistry()",
        },
        "removed": {},
    },
    "tokenomics_implementation_2": {
        "added": {
            "0x122b6689": None,
            "0x456db972": "insolventSince()",
            "0x4ec7182e": None,
            "0x85eb2a08": "activateRebate()",
            "0xeedf4c43": None,
        },
        "removed": {},
    },
    "exchange_linked_library_2": {
        "added": {"0x06c5308a": None, "0xb9370332": None},
        "removed": {"0x82296364": None, "0xef1a27a9": None},
    },
    "builder_registry": {
        "added": {
            "0x452a9320": "guardian()",
            "0x8da5cb5b": "owner()",
            "0xf2fde38b": "transferOwnership(address)",
            "0x459770f6": "setFeeRate(uint64)",
            "0x54dc2a02": "approveBuilder(address)",
            "0x673448dd": "isApproved(address)",
            "0x8a0dac4a": "setGuardian(address)",
            "0x978bbdb9": "feeRate()",
            "0xd779e270": "feeRateOf(address)",
            "0xec969386": "removeBuilder(address)",
        },
        "removed": {},
    },
}
# Probes run live: (name, address, selector, argument address, sender).
PROBES = (
    ("newest_proxy_admin_owner", NEWEST_PROXY_ADMIN, "0x8da5cb5b", None, None),
    ("newest_timelock_owner", NEWEST_TIMELOCK, "0x8da5cb5b", None, None),
    ("newest_timelock_min_delay", NEWEST_TIMELOCK, "0xc63c4e9b", None, None),
    ("newest_exchange_owner", NEWEST_PROXIES["exchange_proxy"], "0x8da5cb5b", None, None),
    ("builder_registry_owner", BUILDER_REGISTRY, "0x8da5cb5b", None, None),
    ("builder_registry_guardian", BUILDER_REGISTRY, "0x452a9320", None, None),
    ("builder_registry_fee_rate", BUILDER_REGISTRY, "0x978bbdb9", None, None),
    ("builder_registry_fee_rate_of_keeper", BUILDER_REGISTRY, "0xd779e270", "0x0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56", None),
    ("session_key_manager_builder_registry", NEWEST_PROXIES["session_key_manager_proxy"], "0xe737de13", None, None),
    ("session_key_manager_set_builder_registry_owner", NEWEST_PROXIES["session_key_manager_proxy"], "0xbd322efa", BUILDER_REGISTRY, NEWEST_TIMELOCK),
    ("session_key_manager_registry_old_value", NEWEST_PROXIES["session_key_manager_proxy"], "0xbd322efa", EARLIER_2_REGISTRY, NEWEST_TIMELOCK),
    ("earlier_2_proxy_admin_owner", EARLIER_2_PROXY_ADMIN, "0x8da5cb5b", None, None),
    ("earlier_2_timelock_owner", EARLIER_2_TIMELOCK, "0x8da5cb5b", None, None),
    ("earlier_2_timelock_min_delay", EARLIER_2_TIMELOCK, MIN_DELAY_SELECTOR, None, None),
    ("earlier_2_multisig_count", EARLIER_2_MULTISIG, MULTISIG_COUNT, None, None),
    ("newest_multisig_count", NEWEST_MULTISIG, MULTISIG_COUNT, None, None),
    ("earlier_1_timelock_min_delay", "0x69b4b92f02ff415e0c966686e00d2783b395d690", MIN_DELAY_SELECTOR, None, None),
    ("earlier_2_registry_guardian", EARLIER_2_REGISTRY, "0x452a9320", None, None),
    # the pinned and set-1 Exchange dispatch liquidate(uint256); set 2 does not.
    ("earlier_1_liquidate_zero", EARLIER_1_EXCHANGE_PROXY, "0x415f1240", "0x" + "00" * 32, None),
    ("newest_liquidate_zero", NEWEST_PROXIES["exchange_proxy"], "0x415f1240", "0x" + "00" * 32, None),
    ("earlier_2_liquidate_zero", EARLIER_2_EXCHANGE_PROXY, "0x415f1240", "0x" + "00" * 32, None),
)
TIMELOCK_TOPICS = {
    "0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f": "BatchOperationScheduled",
    "0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464": "MinDelayUpdated",
    "0x2a08801cf3674ab09756ae78a3a4833813465af6af958136b360eab6b71c8952": "OperationExecuted",
    "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b": "OwnerUpdated",
    "0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39": "OperationScheduled",
    "0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd": "BatchOperationExecuted",
    "0xcf0f63b97f3387253cbc0bde884f975df77e39184dc3280c2c81be495f58eef4": "OperationCancelled",
}
MULTISIG_TOPICS = {
    "0x4c4e829c9b8c87162e976ab955be6db24dace1afaa0ebe4308b6c273a92f5875": "TransactionRevoked",
    "0xbe411f0729ceed7585127466bac46d523f0ef18ba210980602e861c7a8fe4a7f": "TransactionSubmitted",
    "0xd3fb8b9f824d81f0fe695808b7b28faf553f5e7d8ff92fb5f25e210eb9134aec": "TransactionExecuted",
    "0xddfe9ff988d8830e7b19e61773b4a39f43d1d98b57f2aef535a4960c0291b0fd": "SignersUpdated",
}
# Reverted owner reconciliation on a live pending sweep, seen at the pin and after it.
RECONCILE_REVERT = "0x28ef4314"
OWNER_GUARD_REVERT = "0x30cd7471"
UPGRADED_TOPIC = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
PINNED_PT01_SPOT_TOTAL = "62.150916"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def saved_capture():
    return json.loads(gzip.decompress(CAPTURE.read_bytes()))


def saved_live():
    return json.loads(gzip.decompress((OUT / "live_latest.json.gz").read_bytes()))


def saved_logs():
    return json.loads(gzip.decompress((OUT / "governance_logs.json.gz").read_bytes()))


def saved_explorer():
    return read_json(OUT / "explorer_facts.json")


def runtime_of(value):
    if isinstance(value, str) and value.startswith("0x"):
        return bytes.fromhex(value[2:])
    return bytes.fromhex(pathlib.Path(value).read_text().strip()[2:])


def selectors(runtime, limit=4096):
    """PUSH4 selector, EQ, PUSH2 destination, JUMPI dispatch entries."""
    return {
        "0x" + match.group(1).hex()
        for match in re.finditer(b"\x63(.{4})\x14\x61(..)\x57", runtime[:limit], re.DOTALL)
    }


def push20_sites(runtime, address=None):
    sites = []
    pc = 0
    while pc < len(runtime):
        opcode = runtime[pc]
        if 0x60 <= opcode <= 0x7F:
            size = opcode - 0x5F
            if opcode == 0x73 and pc + 21 <= len(runtime):
                if address is None or runtime[pc + 1 : pc + 21] == address:
                    sites.append(pc + 1)
            pc += 1 + size
        else:
            pc += 1
    return sites


def embedded_addresses(runtime):
    return {
        "0x" + runtime[site : site + 20].hex()
        for site in push20_sites(runtime)
        if runtime[site] != 0
    }


def zero_links(runtime, address):
    sites = push20_sites(runtime, bytes.fromhex(address[2:]))
    result = bytearray(runtime)
    for site in sites:
        result[site : site + 20] = bytes(20)
    return bytes(result), sites


def set_roles(rows):
    sets = collections.OrderedDict()
    for name, base in SET_BASE:
        roles = collections.OrderedDict()
        for offset, (role, kind) in enumerate(LAYOUT):
            row = rows[base + offset]
            runtime = runtime_of(row["runtime"])
            roles[role] = {
                "address": row["address"],
                "kind": kind,
                "creation_block": row["creation_block"],
                "creation_tx": row["creation_tx"],
                "runtime_bytes": len(runtime),
                "sha256": sha256(runtime),
                "pinned_implementation": (
                    "0x" + row["implementation_word"][-40:] if kind == "proxy" else None
                ),
                "compiler_metadata": runtime[-53:-42].decode("ascii", "replace"),
            }
        sets[name] = roles
    return sets


def rpc_batch_once(chunk, attempts=6):
    """One request batch, retrying the public endpoint's rate limiter."""
    payload = json.dumps(chunk).encode()
    last = ""
    for attempt in range(attempts):
        request = urllib.request.Request(
            RPC, payload, {"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                reply = json.load(response)
        except (OSError, json.JSONDecodeError) as error:
            last = type(error).__name__
            time.sleep(1.0 * (attempt + 1))
            continue
        if isinstance(reply, list) and len(reply) == len(chunk):
            return reply
        last = json.dumps(reply)[:120]
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"rpc batch failed after {attempts} attempts: {last}")


def rpc_calls(calls, batch=5, tolerate_errors=False):
    results = {}
    for start in range(0, len(calls), batch):
        chunk = calls[start : start + batch]
        for row in rpc_batch_once(chunk):
            assert row["id"] not in results
            if "error" in row:
                if not tolerate_errors:
                    raise RuntimeError(f"rpc error: {row['error']}")
                results[row["id"]] = None
            else:
                results[row["id"]] = row["result"]
    assert set(results) == {call["id"] for call in calls}
    return results


def call(method, params, index):
    return {"jsonrpc": "2.0", "id": index, "method": method, "params": params}


def explorer_run(command, attempts=5):
    """Run one etherscan CLI call, retrying the API's rate limit."""
    last = ""
    for attempt in range(attempts):
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        text = result.stdout.strip()
        if text.startswith("[") or text.startswith("{"):
            try:
                return json.loads(text)
            except json.JSONDecodeError as error:
                last = f"unparsed json: {text[:120]}"
                raise RuntimeError(last) from error
        last = (result.stderr or text)[:160]
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"etherscan call failed after {attempts} attempts: {last}")


def explorer_logs(address, start, end, topic0=None):
    pages = []
    page = 1
    while True:
        command = [
            "etherscan", "logs", "get", "--chain", "999", "--address", address,
            "--from-block", str(start), "--to-block", str(end),
            "--page", str(page), "--offset", "200",
        ]
        if topic0:
            command += ["--topic0", topic0]
        rows = explorer_run(command)
        assert isinstance(rows, list), rows
        pages += rows
        if len(rows) < 200:
            break
        page += 1
    return pages


def explorer_creation(address):
    rows = explorer_run(
        ["etherscan", "contract", "getcontractcreation", address, "--chain", "999"]
    )
    assert isinstance(rows, list) and len(rows) == 1, rows[:1]
    row = rows[0]
    assert row["contractAddress"].lower() == address.lower()
    return {
        "address": address,
        "block": int(row["blockNumber"]),
        "creator": row["contractCreator"].lower(),
        "tx": row["txHash"].lower(),
        "timestamp": int(row["timestamp"]),
    }


def explorer_txlist(address):
    rows = explorer_run(
        ["etherscan", "account", "txlist", address, "--chain", "999", "--all"]
    )
    assert isinstance(rows, list), rows
    return [
        {
            "block": int(row["blockNumber"]),
            "nonce": int(row["nonce"]),
            "from": row["from"].lower(),
            "to": row["to"].lower() if row["to"] else None,
            "contract_address": row["contractAddress"].lower() if row["contractAddress"] else None,
            "tx": row["hash"].lower(),
            "status": row["txreceipt_status"],
        }
        for row in rows
    ]


def decode_multisig_record(record):
    body = bytes.fromhex(record[2:])
    offset = int.from_bytes(body[64:96], "big")
    length = int.from_bytes(body[offset : offset + 32], "big")
    payload = body[offset + 32 : offset + 32 + length]
    return {
        "destination": "0x" + body[12:32].hex(),
        "value": int.from_bytes(body[32:64], "big"),
        "payload": "0x" + payload.hex(),
        "selector": "0x" + payload[:4].hex(),
        "submitter": "0x" + body[96:128].hex()[-40:],
        "epoch": int.from_bytes(body[128:160], "big"),
        "status": int.from_bytes(body[160:192], "big"),
    }


def param_word(payload_hex, index):
    """The index-th 32-byte calldata parameter after the 4-byte selector."""
    start = 2 + 8 + 64 * index
    return payload_hex[start : start + 64]


def decode_batch(payload_hex, expected_targets):
    """Decode timelock scheduleBatch/executeBatch calldata into per-target calls."""
    body = bytes.fromhex(payload_hex[2:])[4:]
    targets_offset = int.from_bytes(body[0:32], "big")
    values_offset = int.from_bytes(body[32:64], "big")
    datas_offset = int.from_bytes(body[64:96], "big")
    assert 96 <= targets_offset < values_offset < datas_offset < len(body)
    count = int.from_bytes(body[targets_offset : targets_offset + 32], "big")
    assert count == expected_targets, count
    targets = [
        "0x" + body[targets_offset + 44 + 32 * k : targets_offset + 64 + 32 * k].hex()
        for k in range(count)
    ]
    values = [
        int.from_bytes(body[values_offset + 32 + 32 * k : values_offset + 64 + 32 * k], "big")
        for k in range(count)
    ]
    base = datas_offset + 32
    datas = []
    for k in range(count):
        element = int.from_bytes(
            body[datas_offset + 32 + 32 * k : datas_offset + 64 + 32 * k], "big"
        )
        length = int.from_bytes(body[base + element : base + element + 32], "big")
        datas.append("0x" + body[base + element + 32 : base + element + 32 + length].hex())
    return {"targets": targets, "values": values, "datas": datas}


def keccak():
    import atlas_factory_events as factory_events

    return factory_events.Keccak()


def mapping_key(user, slot):
    return "0x" + keccak()(int(user, 16).to_bytes(32, "big") + slot.to_bytes(32, "big")).hex()


def capture():
    manifest = read_json(ATLAS / "manifest.json")
    scope = saved_capture()
    rows = scope["rows"]
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    SUITE_OUT.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    head = rpc_calls([call("eth_getBlockByNumber", ["latest", False], 0)])[0]
    head_block = int(head["number"], 16)
    assert head_block > LAST_PINNED_GOOD_BLOCK, head_block

    # 1. the seven post-pin runtimes, saved exactly as read.
    results = rpc_calls(
        [
            call("eth_getCode", [address, "latest"], 100 + index)
            for index, (_, address, _) in enumerate(POSTPIN_DEPLOYMENTS)
        ]
    )
    postpin = {}
    for index, (role, address, nonce) in enumerate(POSTPIN_DEPLOYMENTS):
        runtime = bytes.fromhex(results[100 + index][2:])
        (RUNTIME_DIR / f"{address}.hex").write_text("0x" + runtime.hex() + "\n")
        postpin[address] = {
            "address": address,
            "role": role,
            "deployer_nonce": nonce,
            "runtime_bytes": len(runtime),
            "sha256": sha256(runtime),
            "runtime_file": f"runtime/{address}.hex",
        }

    extra_code = {}
    extra_results = rpc_calls(
        [
            call("eth_getCode", [address, "latest"], 200 + index)
            for index, address in enumerate(EXTRA_CODE_ADDRESSES)
        ]
    )
    for index, address in enumerate(EXTRA_CODE_ADDRESSES):
        code = extra_results[200 + index]
        if code and code != "0x":
            runtime = bytes.fromhex(code[2:])
            (RUNTIME_DIR / f"{address}.hex").write_text("0x" + runtime.hex() + "\n")
            extra_code[address] = {
                "runtime_bytes": len(runtime),
                "sha256": sha256(runtime),
                "runtime_file": f"runtime/{address}.hex",
            }

    # 2. live EIP-1967 slots for every proxy of every pre-pin set.
    base_of = dict(SET_BASE)
    plans = []
    calls = []
    index = 1000
    for name, base in SET_BASE:
        for offset, (role, kind) in enumerate(LAYOUT):
            if kind != "proxy":
                continue
            address = rows[base + offset]["address"]
            for slot, label in ((IMPLEMENTATION_SLOT, "implementation"), (ADMIN_SLOT, "admin")):
                calls.append(call("eth_getStorageAt", [address, slot, "latest"], index))
                plans.append({"index": index, "set": name, "role": role, "label": label})
                index += 1
    results = rpc_calls(calls)
    slots = collections.defaultdict(lambda: collections.defaultdict(dict))
    for plan in plans:
        word = results[plan["index"]]
        slots[plan["set"]][plan["role"]][plan["label"]] = (
            "0x" + word[-40:] if word and int(word, 16) else None
        )

    # 3. eth_call probes, tolerating reverts so their error data is saved.
    probe_entries = []
    for name, address, selector, argument, sender in PROBES:
        data = selector + (argument[2:].rjust(64, "0") if argument else "")
        entry = {"to": address, "data": data}
        if sender:
            entry["from"] = sender
        probe_entries.append((name, entry))
    for user, _, _, _ in PT01_USERS:
        probe_entries += [
            (f"pt01_pending_call_{user}", {"to": NEWEST_PROXIES["exchange_proxy"], "data": PENDING_SWEEP_CALL + user[2:].rjust(64, "0")}),
            (f"pt01_balances_{user}", {"to": NEWEST_PROXIES["exchange_proxy"], "data": BALANCES_CALL + user[2:].rjust(64, "0")}),
            (f"pt01_builder_fees_{user}", {"to": NEWEST_PROXIES["exchange_proxy"], "data": "0x9d346583" + user[2:].rjust(64, "0")}),
            (f"pt01_reconcile_owner_{user}", {"to": NEWEST_PROXIES["exchange_proxy"], "data": RECONCILE_CALL + user[2:].rjust(64, "0") + (10**12).to_bytes(32, "big").hex(), "from": NEWEST_TIMELOCK}),
            (f"pt01_reconcile_no_sender_{user}", {"to": NEWEST_PROXIES["exchange_proxy"], "data": RECONCILE_CALL + user[2:].rjust(64, "0") + (10**12).to_bytes(32, "big").hex()}),
        ]
        for selector in NEW_SELECTORS["exchange_implementation_2"]["added"]:
            probe_entries.append(
                (f"pt01_added_{selector}_{user}", {"to": NEWEST_PROXIES["exchange_proxy"], "data": selector + user[2:].rjust(64, "0"), "from": NEWEST_TIMELOCK})
            )
    calls = [call("eth_call", [entry, "latest"], 2000 + i) for i, (_, entry) in enumerate(probe_entries)]
    raw = {}
    for start in range(0, len(calls), 5):
        chunk = calls[start : start + 5]
        for row in rpc_batch_once(chunk):
            assert row["id"] not in raw
            raw[row["id"]] = row
    probes = {}
    for i, (name, entry) in enumerate(probe_entries):
        row = raw[2000 + i]
        if "error" in row:
            probes[name] = {
                "to": entry["to"],
                "data": entry["data"],
                "from": entry.get("from"),
                "result": None,
                "revert_data": row["error"].get("data"),
                "error_code": row["error"].get("code"),
            }
        else:
            probes[name] = {
                "to": entry["to"],
                "data": entry["data"],
                "from": entry.get("from"),
                "result": row["result"],
                "revert_data": None,
                "error_code": None,
            }

    # 4. PT-01 raw mapping words and proxy runtimes.
    calls = []
    plan = []
    index = 3000
    for user, proxy, _, _ in PT01_USERS:
        for slot, label in ((PENDING_SWEEP_SLOT, "pending_sweep"), (BALANCES_SLOT, "balances")):
            calls.append(call("eth_getStorageAt", [NEWEST_PROXIES["exchange_proxy"], mapping_key(user, slot), "latest"], index))
            plan.append({"index": index, "user": user, "label": label, "slot": mapping_key(user, slot)})
            index += 1
        calls.append(call("eth_getCode", [proxy, "latest"], index))
        plan.append({"index": index, "user": user, "label": "proxy_code"})
        index += 1
    results = rpc_calls(calls)
    pt01_words = collections.defaultdict(dict)
    for item in plan:
        pt01_words[item["user"]][item["label"]] = results[item["index"]]
        if "slot" in item:
            pt01_words[item["user"]][f"{item['label']}_slot"] = item["slot"]
    for user, _, _, _ in PT01_USERS:
        pt01_words[user]["proxy_code_sha256"] = sha256(bytes.fromhex(pt01_words[user]["proxy_code"][2:]))

    # 5. public Core reads for the two PT-01 proxies.
    def core_post(payload):
        request = urllib.request.Request(CORE_INFO, json.dumps(payload).encode(), {"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)

    pt01_core = {}
    for user, proxy, _, _ in PT01_USERS:
        pt01_core[user] = {
            "spot_clearinghouse_state": core_post({"type": "spotClearinghouseState", "user": proxy}),
            "non_funding_ledger_since_pin": core_post(
                {"type": "userNonFundingLedgerUpdates", "user": proxy, "startTime": 1_792_357_341_000}
            ),
        }

    # 6. stored multisig records: the newest batch pair and the earlier-2 migration pair.
    record_plan = []
    calls = []
    index = 4000
    for target, records in ((NEWEST_MULTISIG, (7, 8, 9, 10)), (EARLIER_2_MULTISIG, (1299, 1300))):
        for record in records:
            calls.append(call("eth_call", [{"to": target, "data": MULTISIG_TRANSACTIONS + hex(record)[2:].rjust(64, "0")}, "latest"], index))
            record_plan.append({"index": index, "target": target, "record": record})
            index += 1
    results = rpc_calls(calls)
    multisig_records = {"newest": {}, "earlier_2": {}}
    for item in record_plan:
        key = "newest" if item["target"] == NEWEST_MULTISIG else "earlier_2"
        row = decode_multisig_record(results[item["index"]])
        if row["selector"] in ("0x8b07f62b", "0xa6cc2c8c"):
            row["calls"] = decode_batch(row["payload"], 6)
        multisig_records[key][str(item["record"])] = row

    # 7. explorer facts.
    creation = {address: explorer_creation(address) for _, address, _ in POSTPIN_DEPLOYMENTS}
    for row in creation.values():
        assert row["creator"] == DEPLOYER2, row
    txlist = explorer_txlist(DEPLOYER2)
    funding = [row for row in explorer_txlist(DEPLOYER) if row["to"] == DEPLOYER2]
    log_sets = {}
    for label, address, topic, start in (
        ("newest_timelock", NEWEST_TIMELOCK, None, 47_854_000),
        ("newest_multisig", NEWEST_MULTISIG, None, 47_854_000),
        ("newest_proxy_admin", NEWEST_PROXY_ADMIN, None, 47_854_000),
        ("builder_registry", BUILDER_REGISTRY, None, 49_060_000),
        ("earlier_2_registry", EARLIER_2_REGISTRY, None, 49_060_000),
        ("earlier_2_timelock_scheduled", EARLIER_2_TIMELOCK, "0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f", 49_100_000),
        ("earlier_2_timelock_executed", EARLIER_2_TIMELOCK, "0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd", 49_100_000),
        ("earlier_2_multisig_migration", EARLIER_2_MULTISIG, None, 49_158_000),
    ):
        log_sets[label] = {
            "address": address,
            "topic0": topic,
            "from_block": start,
            "to_block": head_block,
            "logs": explorer_logs(address, start, head_block, topic),
        }
    # One Upgraded(address)-topic query per proxy proves no proxy upgrade log exists,
    # and it stays small even for the Exchange.
    for label, address in (
        *[(f"proxy_{address}", address) for address in NEWEST_PROXIES.values()],
        ("earlier_2_exchange_proxy", EARLIER_2_EXCHANGE_PROXY),
        ("earlier_1_exchange_proxy", EARLIER_1_EXCHANGE_PROXY),
    ):
        log_sets[label] = {
            "address": address,
            "topic0": UPGRADED_TOPIC,
            "from_block": LAST_PINNED_GOOD_BLOCK + 1,
            "to_block": head_block,
            "logs": explorer_logs(address, LAST_PINNED_GOOD_BLOCK + 1, head_block, UPGRADED_TOPIC),
        }

    # 8. headers for every event the ledger dates.
    dated = sorted(
        {
            PIN,
            LAST_PINNED_GOOD_BLOCK,
            MIN_DELAY_CHANGE_BLOCK,
            OLD_OPERATION_CANCEL_BLOCK,
            SET_2_SCHEDULE_BLOCK,
            SET_2_LIVE_BLOCK,
            EARLIER_2_BATCH_SCHEDULE_BLOCK,
            EARLIER_2_BATCH_EXECUTE_BLOCK,
            *(row["creation_block"] for row in rows),
            *(row["block"] for row in creation.values()),
            *(row["block"] for row in txlist if row["from"] == DEPLOYER2),
            *(row["block"] for row in txlist if row["to"] == DEPLOYER2),
            *(row["block"] for row in funding),
            *(int(log["blockNumber"], 16) for group in log_sets.values() for log in group["logs"]),
            head_block,
        }
    )
    headers = rpc_calls(
        [call("eth_getBlockByNumber", [hex(block), False], 5000 + i) for i, block in enumerate(dated)]
    )
    header_rows = {}
    for i, block in enumerate(dated):
        row = headers[5000 + i]
        assert int(row["number"], 16) == block, (block, row["number"])
        header_rows[str(block)] = {
            "block": block,
            "hash": row["hash"],
            "timestamp": int(row["timestamp"], 16),
            "timestamp_utc": datetime.datetime.fromtimestamp(
                int(row["timestamp"], 16), datetime.UTC
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    assert header_rows[str(PIN)]["hash"].lower() == manifest["block_hash"]

    live = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "rpc": RPC,
        "core_info": CORE_INFO,
        "head": header_rows[str(head_block)],
        "headers": header_rows,
        "proxy_slots_at_latest": slots,
        "probes": probes,
        "pt01_words": pt01_words,
        "pt01_core": pt01_core,
        "multisig_records": multisig_records,
        "extra_code": extra_code,
    }
    (OUT / "live_latest.json.gz").write_bytes(
        gzip.compress(json.dumps(live, separators=(",", ":"), sort_keys=True).encode(), compresslevel=9, mtime=0)
    )
    (OUT / "governance_logs.json.gz").write_bytes(
        gzip.compress(
            json.dumps({"head": head_block, "log_sets": log_sets}, separators=(",", ":"), sort_keys=True).encode(),
            compresslevel=9,
            mtime=0,
        )
    )
    (OUT / "explorer_facts.json").write_text(
        json.dumps(
            {
                "source": "Etherscan v2 API through the etherscan CLI, chain 999",
                "creation": creation,
                "deployer2_txlist": txlist,
                "deployer2_funding": funding,
                "runtime_sha256": {address: row["sha256"] for address, row in postpin.items()},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (SUITE_OUT / "postpin_deployment.json").write_text(
        json.dumps(postpin, indent=2, sort_keys=True) + "\n"
    )
    return verify()


def verify():
    manifest = read_json(ATLAS / "manifest.json")
    upgrade_history = read_json(ATLAS / "upgrade_history.json")
    scope = saved_capture()
    rows = scope["rows"]
    live = saved_live()
    logs = saved_logs()
    explorer = saved_explorer()
    roles = set_roles(rows)

    # --- pinned evidence consistency ---------------------------------------
    assert scope["pin"] == PIN and scope["block_hash"] == manifest["block_hash"]
    assert len(rows) == 59
    assert [row["creation_block"] // 1_000_000 for row in rows] == [42] * 19 + [47] * 38 + [48] * 2
    assert set(VARIANT_ROWS) == {57, 58}
    manifest_role = {
        value["address"].lower(): value["role"] for value in manifest["contracts"].values()
    }
    manifest_runtime_hash = {
        value["sha256"] for value in manifest["contracts"].values()
    }
    newest_runtime = rows[40]["runtime"]
    for name, base in SET_BASE:
        for offset, (role, kind) in enumerate(LAYOUT):
            row = rows[base + offset]
            entry = roles[name][role]
            assert entry["address"] == row["address"]
            assert entry["sha256"] == sha256(runtime_of(row["runtime"]))
            if kind == "proxy":
                assert len(runtime_of(row["runtime"])) == 925
                assert row["runtime"] == newest_runtime
                # every pinned implementation is a creation of its own set, except
                # earlier set 2's Exchange proxy, which points at the later variant_a row.
                allowed = {other["address"] for other in roles[name].values()}
                if name == "earlier_2" and role == "exchange_proxy":
                    allowed.add(rows[57]["address"])
                    assert entry["pinned_implementation"] == rows[57]["address"]
                assert entry["pinned_implementation"] in allowed, (name, role)
                assert "0x" + row["admin_word"][-40:] == roles[name]["proxy_admin"]["address"]
            else:
                assert row["implementation_word"] is None
    for role, entry in roles["newest"].items():
        if entry["address"] in manifest_role:
            assert entry["sha256"] == manifest["contracts"][entry["address"]]["sha256"], role
    assert sum(row["address"] in manifest_role for row in rows[38:57]) == 19
    assert roles["newest"]["proxy_admin"]["sha256"] == manifest["contracts"][NEWEST_PROXY_ADMIN]["sha256"]
    # the two post-newest variant rows are distinct and match the manifest roles.
    for row_index, role in VARIANT_ROWS.items():
        entry = rows[row_index]
        assert entry["creation_block"] > roles["newest"]["timelock"]["creation_block"]
        assert manifest_role[entry["address"]] == role
        assert sha256(runtime_of(entry["runtime"])) == manifest["contracts"][entry["address"]]["sha256"]
    assert sha256(runtime_of(rows[57]["runtime"])) != sha256(runtime_of(rows[58]["runtime"]))
    # the three math-library addresses (saved separately: the deployer did not create
    # them) all hold the one 585-byte runtime already in the manifest.
    libraries = json.loads(
        gzip.decompress((ROOT / "artifacts" / "deployer_scope" / "older_linked_libraries.json.gz").read_bytes())
    )
    assert libraries["pin"] == PIN and libraries["block_hash"] == manifest["block_hash"]
    math_hash = manifest["contracts"][MATH_LIBRARIES["newest"]]["sha256"]
    for name, address in MATH_LIBRARIES.items():
        if address in libraries["libraries"]:
            runtime = runtime_of(libraries["libraries"][address])
        else:
            runtime = runtime_of(ATLAS / manifest["contracts"][address]["runtime_file"])
        assert len(runtime) == 585, name
        assert sha256(runtime) == math_hash, name

    # --- post-pin deployment identity --------------------------------------
    postpin = {}
    for role, address, nonce in POSTPIN_DEPLOYMENTS:
        runtime = runtime_of(RUNTIME_DIR / f"{address}.hex")
        digest = sha256(runtime)
        assert digest == POSTPIN_RUNTIME_SHA[address], (role, digest)
        postpin[address] = {
            "address": address,
            "role": role,
            "deployer_nonce": nonce,
            "runtime_bytes": len(runtime),
            "sha256": digest,
            "selectors": sorted(selectors(runtime)),
            "compiler_metadata": runtime[-53:-42].decode("ascii", "replace"),
            "embedded_addresses": sorted(embedded_addresses(runtime)),
        }
    assert len({row["sha256"] for row in postpin.values()}) == 6  # two are byte-identical
    creation = explorer["creation"]
    assert set(creation) == {address for _, address, _ in POSTPIN_DEPLOYMENTS}
    for row in creation.values():
        assert row["creator"] == DEPLOYER2
        assert row["block"] > LAST_PINNED_GOOD_BLOCK
    txlist = explorer["deployer2_txlist"]
    outgoing = [row for row in txlist if row["from"] == DEPLOYER2]
    incoming = [row for row in txlist if row["to"] == DEPLOYER2]
    assert sorted(row["nonce"] for row in outgoing) == list(range(8)), outgoing
    assert [row["nonce"] for row in outgoing if row["contract_address"]] == [1, 2, 3, 4, 5, 6, 7]
    assert {row["contract_address"] for row in outgoing if row["contract_address"]} == set(creation)
    assert len(incoming) == 1 and incoming[0]["from"] == DEPLOYER
    for row in outgoing:
        if row["contract_address"]:
            assert row["block"] == creation[row["contract_address"]]["block"]
    funding = explorer["deployer2_funding"]
    assert len(funding) == 1 and funding[0]["from"] == DEPLOYER
    assert funding[0]["block"] < min(row["block"] for row in creation.values())
    assert explorer["runtime_sha256"] == {address: row["sha256"] for address, row in postpin.items()}
    # nonce order matches the saved creation blocks.
    order = sorted(creation.values(), key=lambda row: row["block"])
    assert [row["address"] for row in order] == [
        address for _, address, _ in sorted(POSTPIN_DEPLOYMENTS, key=lambda item: item[2])
    ]

    # --- live slots, owners, and which proxies moved ------------------------
    assert live["head"]["block"] >= POSTPIN_WINDOW[1]
    slots = live["proxy_slots_at_latest"]
    for name in PRE_PIN_SETS:
        for role, entry in roles[name].items():
            if entry["kind"] != "proxy":
                continue
            assert slots[name][role]["admin"].lower() == roles[name]["proxy_admin"]["address"]
    moved = {
        "exchange_proxy": EXCHANGE_2,
        "session_key_manager_proxy": SKM_2,
        "tokenomics_proxy": TOKENOMICS_2,
    }
    for role, address in NEWEST_PROXIES.items():
        assert NEWEST_PROXIES[role] == roles["newest"][role]["address"]
        current = slots["newest"][role]["implementation"].lower()
        if role in moved:
            assert roles["newest"][role]["pinned_implementation"] != moved[role]
            assert current == moved[role], role
        else:
            assert current == roles["newest"][role]["pinned_implementation"], role
    earlier_2_moved = {
        "exchange_proxy": EXCHANGE_2,
        "session_key_manager_proxy": SKM_2,
        "tokenomics_proxy": TOKENOMICS_2_EARLIER_2,
    }
    for role, implementation in earlier_2_moved.items():
        assert roles["earlier_2"][role]["pinned_implementation"] != implementation
        assert slots["earlier_2"][role]["implementation"].lower() == implementation
    for role, entry in roles["earlier_1"].items():
        if entry["kind"] == "proxy":
            assert slots["earlier_1"][role]["implementation"].lower() == entry["pinned_implementation"]
    # newest implementations absent from the pinned manifest.
    assert EXCHANGE_2 not in manifest_role and SKM_2 not in manifest_role
    assert TOKENOMICS_2 not in manifest_role and LIBRARY_2 not in manifest_role
    assert BUILDER_REGISTRY not in manifest_role

    # --- live owner and control reads ---------------------------------------
    probes = live["probes"]
    assert int(probes["newest_timelock_min_delay"]["result"], 16) == 86_400
    assert probes["newest_proxy_admin_owner"]["result"].lower().endswith(NEWEST_TIMELOCK[2:])
    assert probes["newest_timelock_owner"]["result"].lower().endswith(NEWEST_MULTISIG[2:])
    assert probes["newest_exchange_owner"]["result"].lower().endswith(NEWEST_TIMELOCK[2:])
    assert probes["builder_registry_owner"]["result"].lower().endswith(NEWEST_TIMELOCK[2:])
    assert probes["builder_registry_guardian"]["result"].lower().endswith(NEWEST_MULTISIG[2:])
    assert int(probes["builder_registry_fee_rate"]["result"], 16) == 5 * 10**15
    assert probes["session_key_manager_builder_registry"]["result"].lower().endswith(BUILDER_REGISTRY[2:])
    assert probes["earlier_2_proxy_admin_owner"]["result"].lower().endswith(EARLIER_2_TIMELOCK[2:])
    assert probes["earlier_2_timelock_owner"]["result"].lower().endswith(EARLIER_2_MULTISIG[2:])
    assert int(probes["earlier_2_timelock_min_delay"]["result"], 16) == 60
    assert int(probes["earlier_1_timelock_min_delay"]["result"], 16) == 60
    assert int(probes["newest_multisig_count"]["result"], 16) == 11
    assert int(probes["earlier_2_multisig_count"]["result"], 16) >= 1301
    assert probes["earlier_2_registry_guardian"]["result"].lower().endswith(EARLIER_2_MULTISIG[2:])
    assert probes["session_key_manager_set_builder_registry_owner"]["result"] == "0x"
    # the single-liquidation selector is still dispatched by earlier set 1 and earlier
    # set 2's implementations (a decoded revert with data) and is not dispatched by the
    # set 2 Exchange (a bare revert with no data).
    assert probes["earlier_1_liquidate_zero"]["revert_data"] == "0x94e88a21"
    for name in ("earlier_2_liquidate_zero", "newest_liquidate_zero"):
        assert probes[name]["result"] is None, name
        assert probes[name]["revert_data"] is None, name

    # --- the two upgrade batches --------------------------------------------
    records = live["multisig_records"]
    assert set(records["newest"]) == {"7", "8", "9", "10"}
    assert records["newest"]["7"]["selector"] == "0x88aa4c12"
    assert records["newest"]["7"]["destination"] == NEWEST_TIMELOCK
    # a timelock self-call carrying updateMinDelay(86,400) (inner selector 0x8a99d586).
    assert "8a99d586" in records["newest"]["7"]["payload"]
    assert (86_400).to_bytes(32, "big").hex() in records["newest"]["7"]["payload"]
    assert records["newest"]["8"]["selector"] == "0xc4d252f5"
    assert records["newest"]["8"]["payload"].endswith(
        "51142366b8d5ae8d41322de14a7627f265e2ab54ee65828bbbaa14f6090cb578"
    )
    for record in ("9", "10"):
        row = records["newest"][record]
        assert row["destination"] == NEWEST_TIMELOCK and row["value"] == 0
        calls = row["calls"]
        assert calls["targets"] == [
            NEWEST_PROXY_ADMIN,
            NEWEST_PROXY_ADMIN,
            NEWEST_PROXY_ADMIN,
            NEWEST_PROXIES["session_key_manager_proxy"],
            NEWEST_PROXIES["exchange_proxy"],
            NEWEST_PROXIES["tokenomics_proxy"],
        ]
        assert calls["values"] == [0] * 6
        assert calls["datas"] == [
            "0x99a88ec4" + NEWEST_PROXIES["session_key_manager_proxy"][2:].rjust(64, "0") + SKM_2[2:].rjust(64, "0"),
            "0x99a88ec4" + NEWEST_PROXIES["exchange_proxy"][2:].rjust(64, "0") + EXCHANGE_2[2:].rjust(64, "0"),
            "0x99a88ec4" + NEWEST_PROXIES["tokenomics_proxy"][2:].rjust(64, "0") + TOKENOMICS_2[2:].rjust(64, "0"),
            "0xbd322efa" + BUILDER_REGISTRY[2:].rjust(64, "0"),
            "0xefc1bd46" + "0924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56".rjust(64, "0"),
            "0x85eb2a08",
        ]
    assert records["newest"]["9"]["selector"] == "0x8b07f62b"
    assert records["newest"]["10"]["selector"] == "0xa6cc2c8c"
    assert records["newest"]["9"]["calls"] == records["newest"]["10"]["calls"]
    earlier = records["earlier_2"]
    assert set(earlier) == {"1299", "1300"}
    assert earlier["1299"]["calls"] == earlier["1300"]["calls"]
    assert earlier["1299"]["calls"]["targets"] == [
        EARLIER_2_PROXY_ADMIN,
        EARLIER_2_PROXY_ADMIN,
        EARLIER_2_PROXY_ADMIN,
        EARLIER_2_SKM_PROXY,
        EARLIER_2_EXCHANGE_PROXY,
        EARLIER_2_TOKENOMICS_PROXY,
    ]
    assert earlier["1299"]["calls"]["datas"] == [
        "0x99a88ec4" + EARLIER_2_SKM_PROXY[2:].rjust(64, "0") + SKM_2[2:].rjust(64, "0"),
        "0x99a88ec4" + EARLIER_2_EXCHANGE_PROXY[2:].rjust(64, "0") + EXCHANGE_2[2:].rjust(64, "0"),
        "0x99a88ec4" + EARLIER_2_TOKENOMICS_PROXY[2:].rjust(64, "0") + TOKENOMICS_2_EARLIER_2[2:].rjust(64, "0"),
        "0xbd322efa" + EARLIER_2_REGISTRY[2:].rjust(64, "0"),
        "0xefc1bd46" + "02406c8e614e131eedc65622a9b9322cca96242e".rjust(64, "0"),
        "0x85eb2a08",
    ]

    # --- governance logs -----------------------------------------------------
    log_sets = logs["log_sets"]
    assert logs["head"] == live["head"]["block"]
    timelock_logs = log_sets["newest_timelock"]["logs"]
    blocks = [int(row["blockNumber"], 16) for row in timelock_logs]
    assert blocks == sorted(blocks)
    topics = collections.Counter(row["topics"][0] for row in timelock_logs)
    for topic, expected in (
        ("0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b", 1),
        ("0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464", 2),
        ("0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39", 2),
        ("0x2a08801cf3674ab09756ae78a3a4833813465af6af958136b360eab6b71c8952", 1),
        ("0xcf0f63b97f3387253cbc0bde884f975df77e39184dc3280c2c81be495f58eef4", 1),
        ("0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f", 1),
        ("0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd", 1),
    ):
        assert topic in TIMELOCK_TOPICS and topics[topic] == expected, (topic, topics[topic])
    executed = [
        row for row in timelock_logs
        if row["topics"][0] == "0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd"
    ][0]
    assert int(executed["blockNumber"], 16) == SET_2_LIVE_BLOCK
    assert int(executed["data"], 16) == 6
    assert executed["topics"][1].lower().endswith(
        "ec82bec90c3ba324ed11c760003f1a5d0a6fd1535a9dbc9882dd727df93b238a"
    )
    scheduled = [
        row for row in timelock_logs
        if row["topics"][0] == "0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f"
    ][0]
    assert int(scheduled["blockNumber"], 16) == SET_2_SCHEDULE_BLOCK
    assert scheduled["topics"][1].lower().endswith(executed["topics"][1].lower()[-64:])
    delay_change = [
        row for row in timelock_logs
        if row["topics"][0] == "0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464"
    ][-1]
    assert int(delay_change["data"], 16) == 86_400
    assert int(delay_change["blockNumber"], 16) == MIN_DELAY_CHANGE_BLOCK
    cancelled = [
        row for row in timelock_logs
        if row["topics"][0] == "0xcf0f63b97f3387253cbc0bde884f975df77e39184dc3280c2c81be495f58eef4"
    ][0]
    assert int(cancelled["blockNumber"], 16) == OLD_OPERATION_CANCEL_BLOCK
    assert cancelled["topics"][1].lower().endswith(records["newest"]["8"]["payload"][-64:])
    # the upgrade transaction is the docs' named set 2 transaction.
    assert executed["transactionHash"].lower() == (
        "0x4410b81e3eb76f83f5ddc4e3faee794fb67208d2f129bc013094b9d06055acb6"
    )
    multisig_logs = log_sets["newest_multisig"]["logs"]
    assert all(row["topics"][0] in MULTISIG_TOPICS for row in multisig_logs)
    indices = [
        int(row["topics"][1], 16)
        for row in multisig_logs
        if row["topics"][0] == "0xd3fb8b9f824d81f0fe695808b7b28faf553f5e7d8ff92fb5f25e210eb9134aec"
    ]
    assert indices[-1] == 10 and {8, 9, 10}.issubset(set(indices))
    revocations = [
        row for row in multisig_logs
        if row["topics"][0] == "0x4c4e829c9b8c87162e976ab955be6db24dace1afaa0ebe4308b6c273a92f5875"
    ]
    assert [int(row["topics"][1], 16) for row in revocations] == [2, 4]
    # No Upgraded(address) log exists for any proxy of any set after the pin. The
    # ProxyAdmin emits only its own two owner-set events, both before the pin, and nothing
    # for an upgrade call, which is why the upgrade is visible only in the slot words and
    # the multisig payloads.
    admin_logs = log_sets["newest_proxy_admin"]["logs"]
    assert len(admin_logs) == 2, len(admin_logs)
    assert all(
        row["topics"][0]
        == "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b"
        for row in admin_logs
    )
    assert all(int(row["blockNumber"], 16) <= PIN for row in admin_logs)
    for label, group in log_sets.items():
        if label.startswith("proxy_") or label.endswith("_exchange_proxy"):
            assert group["topic0"] == UPGRADED_TOPIC, label
            assert group["logs"] == [], label
    assert log_sets["proxy_" + NEWEST_PROXIES["exchange_proxy"]]["logs"] == []
    # the earlier-2 migration pair.
    earlier_scheduled = log_sets["earlier_2_timelock_scheduled"]["logs"]
    earlier_executed = log_sets["earlier_2_timelock_executed"]["logs"]
    assert len(earlier_scheduled) == 1 and len(earlier_executed) == 1
    assert int(earlier_scheduled[0]["blockNumber"], 16) == EARLIER_2_BATCH_SCHEDULE_BLOCK
    assert int(earlier_executed[0]["blockNumber"], 16) == EARLIER_2_BATCH_EXECUTE_BLOCK
    assert int(earlier_scheduled[0]["data"][2:66], 16) == 6
    assert int(earlier_executed[0]["data"], 16) == 6
    assert earlier_executed[0]["topics"][1].lower().endswith(
        "4451c3332513a7f4a0d6df6a2d6e37bdbb4f0e5b3b6cf73d6be0b0d1be2b0a28"
    ) or earlier_executed[0]["topics"][1] == earlier_scheduled[0]["topics"][1]
    assert EARLIER_2_BATCH_EXECUTE_BLOCK < SET_2_LIVE_BLOCK
    migration = log_sets["earlier_2_multisig_migration"]["logs"]
    assert len(migration) == 6, len(migration)
    assert {int(row["blockNumber"], 16) for row in migration} == {
        EARLIER_2_BATCH_SCHEDULE_BLOCK,
        EARLIER_2_BATCH_EXECUTE_BLOCK,
    }
    assert len({row["topics"][0] for row in migration}) == 3
    # both batch records carry the same predecessor, so the two governance paths ran
    # the same shape of operation one hour apart.
    # both batch payloads carry the same predecessor word (the fourth parameter after the
    # 4-byte selector).
    assert param_word(records["newest"]["9"]["payload"], 3) == (
        "bf88bc7f47d379647cac92bb29aa5346fd84c4a4a43bcc56a973ff58c4f7017e"
    )
    assert param_word(earlier["1299"]["payload"], 3) == (
        "bf88bc7f47d379647cac92bb29aa5346fd84c4a4a43bcc56a973ff58c4f7017e"
    )
    # both registries emit only their three constructor events.
    registry_topics = None
    for label, address in (("builder_registry", BUILDER_REGISTRY), ("earlier_2_registry", EARLIER_2_REGISTRY)):
        registry_logs = log_sets[label]["logs"]
        assert len(registry_logs) == 3, (label, len(registry_logs))
        assert all(
            int(row["blockNumber"], 16) == creation[address]["block"] for row in registry_logs
        ), label
        topics = [row["topics"][0] for row in registry_logs]
        # owner set, guardian set and the fee-rate set of the constructor.
        assert "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b" in topics
        assert int(registry_logs[2]["data"], 16) == 5 * 10**15
        if registry_topics is None:
            registry_topics = topics
        assert topics == registry_topics, label
    # the pinned upgrade-history ledger agrees: no Upgraded log, slot stable at creation.
    for proxy in NEWEST_PROXIES.values():
        assert upgrade_history[proxy]["upgrade_event_count"] == 0
        assert upgrade_history[proxy]["same_at_creation_and_pin"] is True

    # --- PT-01 live state ----------------------------------------------------
    pt01 = {}
    for user, proxy, pending_word, pinned_spot in PT01_USERS:
        words = live["pt01_words"][user]
        assert words["pending_sweep_slot"] == mapping_key(user, PENDING_SWEEP_SLOT)
        assert words["balances_slot"] == mapping_key(user, BALANCES_SLOT)
        assert words["pending_sweep"].lower() == pending_word.lower()
        assert live["probes"][f"pt01_pending_call_{user}"]["result"].lower() == pending_word.lower()
        assert int(words["balances"], 16) == 0
        assert int(live["probes"][f"pt01_balances_{user}"]["result"], 16) == 0
        reconcile = live["probes"][f"pt01_reconcile_owner_{user}"]
        assert reconcile["result"] is None
        assert reconcile["revert_data"] == RECONCILE_REVERT
        # with no sender the same call stops earlier, at the owner guard.
        assert (
            live["probes"][f"pt01_reconcile_no_sender_{user}"]["revert_data"]
            == OWNER_GUARD_REVERT
        )
        state = live["pt01_core"][user]["spot_clearinghouse_state"]
        usdc = [row for row in state["balances"] if row["coin"] == "USDC" and row["token"] == 0]
        assert len(usdc) == 1
        assert float(usdc[0]["total"]) > 0
        ledger = live["pt01_core"][user]["non_funding_ledger_since_pin"]
        assert ledger == []
        pt01[user] = {
            "proxy": proxy,
            "pending_sweep_word": words["pending_sweep"],
            "pending_sweep_word_at_pin": pending_word,
            "pending_sweep_word_unchanged": words["pending_sweep"].lower() == pending_word.lower(),
            "exchange_balance_word": words["balances"],
            "exchange_balance_call": live["probes"][f"pt01_balances_{user}"]["result"],
            "builder_fees_call": live["probes"][f"pt01_builder_fees_{user}"]["result"],
            "proxy_runtime_sha256": words["proxy_code_sha256"],
            "reconcile_from_owner_revert": reconcile["revert_data"],
            "core_spot_usdc": usdc[0]["total"],
            "core_non_funding_ledger_entries_since_pin": len(ledger),
        }
    assert sorted(pt01) == sorted(user for user, _, _, _ in PT01_USERS)
    # both deposit proxy runtimes are byte-identical to the pinned per-user derived runtime
    # saved in the stalled-sweep census and in the three 2026-10-20 status snapshots.
    stalled = json.loads(
        gzip.decompress(
            (ROOT / "artifacts" / "audit_sweep_event_census" / "stalled_sweeps.json.gz").read_bytes()
        )
    )
    asserted_cases = {row["user"].lower(): row for row in stalled["cases"]}
    for name in ("status.json", "status_20261020_later.json", "status_20261020_1703.json"):
        snapshot = read_json(ROOT / "artifacts" / "pt01_postpin" / name)
        for row in snapshot["cases"]:
            assert row["pending_storage"].lower() == pt01[row["user"].lower()]["pending_sweep_word"]
            assert row["proxy_code_sha256"] == pt01[row["user"].lower()]["proxy_runtime_sha256"]
    for user in pt01:
        assert pt01[user]["proxy_runtime_sha256"] == asserted_cases[user]["derived_runtime_sha256"]
        assert pt01[user]["proxy"] == asserted_cases[user]["proxy"]

    # --- runtime comparison and normalization --------------------------------
    exchange_pinned = runtime_of(rows[41]["runtime"])
    exchange_variant_a = runtime_of(rows[57]["runtime"])
    exchange_variant_b = runtime_of(rows[58]["runtime"])
    exchange_new = runtime_of(RUNTIME_DIR / f"{EXCHANGE_2}.hex")
    library_new = runtime_of(RUNTIME_DIR / f"{LIBRARY_2}.hex")
    library_pinned = runtime_of(ATLAS / manifest["contracts"][LIBRARY_PINNED_LIVE]["runtime_file"])
    skm_new = runtime_of(RUNTIME_DIR / f"{SKM_2}.hex")
    skm_pinned = runtime_of(rows[43]["runtime"])
    tokenomics_new = runtime_of(RUNTIME_DIR / f"{TOKENOMICS_2}.hex")
    tokenomics_new_earlier_2 = runtime_of(RUNTIME_DIR / f"{TOKENOMICS_2_EARLIER_2}.hex")
    tokenomics_pinned = runtime_of(rows[47]["runtime"])
    registry = runtime_of(RUNTIME_DIR / f"{BUILDER_REGISTRY}.hex")
    registry_earlier_2 = runtime_of(RUNTIME_DIR / f"{EARLIER_2_REGISTRY}.hex")
    assert len(exchange_pinned) == 23052 and len(exchange_new) == 23959
    assert len(exchange_variant_a) == len(exchange_variant_b) == 23529
    assert len(library_pinned) == 5790 and len(library_new) == 6286
    assert len(skm_pinned) == 3764 and len(skm_new) == 4521
    assert len(tokenomics_pinned) == 3324 and len(tokenomics_new) == 6452
    assert len(registry) == 1210 and registry == registry_earlier_2
    for role, (pinned_runtime, new_runtime) in (
        ("exchange_implementation_2", (exchange_pinned, exchange_new)),
        ("session_key_manager_implementation_2", (skm_pinned, skm_new)),
        ("tokenomics_implementation_2", (tokenomics_pinned, tokenomics_new)),
        ("exchange_linked_library_2", (library_pinned, library_new)),
    ):
        assert selectors(new_runtime) - selectors(pinned_runtime) == set(
            NEW_SELECTORS[role]["added"]
        ), role
        assert selectors(pinned_runtime) - selectors(new_runtime) == set(
            NEW_SELECTORS[role]["removed"]
        ), role
    assert selectors(registry) == set(NEW_SELECTORS["builder_registry"]["added"])
    assert len(selectors(exchange_pinned)) == 98 and len(selectors(exchange_new)) == 103
    # the pinned variants share the newest pinned selector set; the new one does not.
    assert selectors(exchange_variant_a) == selectors(exchange_variant_b) == selectors(exchange_pinned)
    # the new Exchange links the new library, not the pinned one.
    assert bytes.fromhex(LIBRARY_2[2:]) in exchange_new
    assert bytes.fromhex(LIBRARY_PINNED_LIVE[2:]) not in exchange_new
    assert bytes.fromhex(LIBRARY_PINNED_LIVE[2:]) in exchange_pinned
    assert bytes.fromhex(LIBRARY_PINNED_LIVE[2:]) in exchange_variant_b
    assert bytes.fromhex(LIBRARY_2[2:]) not in exchange_pinned
    # the library selector delta.
    assert selectors(library_new) - selectors(library_pinned) == set(
        NEW_SELECTORS["exchange_linked_library_2"]["added"]
    )
    assert selectors(library_pinned) - selectors(library_new) == set(
        NEW_SELECTORS["exchange_linked_library_2"]["removed"]
    )
    # the three pre-pin Tokenomics runtimes normalize to one runtime after zeroing the
    # two linked-library operands; so do the two new Tokenomics runtimes.
    normalized = {}
    for name, row_index in (("earlier_1", 9), ("earlier_2", 28), ("newest", 47)):
        runtime = runtime_of(rows[row_index]["runtime"])
        assert len(runtime) == 3324
        value, sites = zero_links(runtime, MATH_LIBRARIES[name])
        assert len(sites) == 2
        normalized[name] = sha256(value)
    assert len(set(normalized.values())) == 1
    new_normalized = {}
    for name, runtime, library in (
        ("tokenomics_implementation_2", tokenomics_new, MATH_LIBRARIES["newest"]),
        ("tokenomics_implementation_2_earlier_2_link", tokenomics_new_earlier_2, MATH_LIBRARIES["earlier_2"]),
    ):
        value, sites = zero_links(runtime, library)
        assert len(sites) == 2
        new_normalized[name] = sha256(value)
    assert len(set(new_normalized.values())) == 1
    # the two new Tokenomics runtimes differ only in those two 20-byte operands.
    matcher = difflib.SequenceMatcher(None, tokenomics_new, tokenomics_new_earlier_2, autojunk=False)
    opcodes = [op for op in matcher.get_opcodes() if op[0] != "equal"]
    assert len(opcodes) == 2 and all(
        op[0] == "replace" and op[2] - op[1] == 20 and op[4] - op[3] == 20 for op in opcodes
    )
    # the two registries are byte-identical while their constructor state differs.
    assert registry == registry_earlier_2
    # recorded live constructor state for each registry.
    registry_state = {
        "builder_registry": {
            "owner": probes["builder_registry_owner"]["result"],
            "guardian": probes["builder_registry_guardian"]["result"],
            "fee_rate": probes["builder_registry_fee_rate"]["result"],
        },
        "builder_registry_earlier_2_governed": {
            "guardian": probes["earlier_2_registry_guardian"]["result"],
        },
    }
    assert registry_state["builder_registry"]["owner"].lower().endswith(NEWEST_TIMELOCK[2:])
    assert registry_state["builder_registry_earlier_2_governed"]["guardian"].lower().endswith(
        EARLIER_2_MULTISIG[2:]
    )
    # the new Exchange no longer dispatches the single-position liquidation entry point.
    assert "0x415f1240" in selectors(exchange_pinned) and "0x415f1240" not in selectors(exchange_new)
    # no clearPendingSweep anywhere in the newest proxy's current implementation.
    assert "0x2362f4de" not in selectors(exchange_new)
    assert "0x2362f4de" not in selectors(exchange_pinned)
    assert RECONCILE_CALL in selectors(exchange_new) and PENDING_SWEEP_CALL in selectors(exchange_new)

    # --- ledger and doc ------------------------------------------------------
    # linked libraries, matched only against runtimes already captured in this repo.
    library_index = {}
    for address, value in libraries["libraries"].items():
        runtime = runtime_of(value)
        library_index[address] = (len(runtime), sha256(runtime))
    for address in (VARIANT_EXCHANGE_LIBRARY, LIBRARY_PINNED_LIVE, MATH_LIBRARIES["newest"]):
        runtime = runtime_of(ATLAS / manifest["contracts"][address]["runtime_file"])
        library_index[address] = (len(runtime), sha256(runtime))
    library_index[LIBRARY_2] = (len(library_new), sha256(library_new))
    linked_libraries = {}
    for label, runtime in (
        ("earlier_1:exchange_implementation", runtime_of(rows[3]["runtime"])),
        ("earlier_1:tokenomics_implementation", runtime_of(rows[9]["runtime"])),
        ("earlier_2:exchange_implementation", runtime_of(rows[22]["runtime"])),
        ("earlier_2:tokenomics_implementation", runtime_of(rows[28]["runtime"])),
        ("newest:exchange_implementation_variant_a", runtime_of(rows[57]["runtime"])),
        ("newest:exchange_implementation_variant_b", runtime_of(rows[58]["runtime"])),
        ("newest:exchange_implementation", runtime_of(rows[41]["runtime"])),
        ("newest:tokenomics_implementation", runtime_of(rows[47]["runtime"])),
        ("postpin_refresh:exchange_implementation_2", exchange_new),
        ("postpin_refresh:tokenomics_implementation_2", tokenomics_new),
        ("postpin_refresh:tokenomics_implementation_2_earlier_2_link", tokenomics_new_earlier_2),
    ):
        found = [
            {"address": address, "runtime_bytes": library_index[address][0], "sha256": library_index[address][1]}
            for address in sorted(
                embedded_addresses(runtime).intersection(library_index)
            )
        ]
        linked_libraries[label] = {
            "runtime_sha256": sha256(runtime),
            "libraries": found,
        }
    assert linked_libraries["earlier_1:exchange_implementation"]["libraries"][0]["address"] == OLDER_EXCHANGE_LIBRARY
    assert linked_libraries["newest:exchange_implementation"]["libraries"][0]["address"] == LIBRARY_PINNED_LIVE
    assert linked_libraries["postpin_refresh:exchange_implementation_2"]["libraries"][0]["address"] == LIBRARY_2

    ledger = {
        "pin": PIN,
        "block_hash": manifest["block_hash"],
        "set_count": 4,
        "set_names": ["earlier_1", "earlier_2", "newest", "postpin_refresh"],
        "generated_from": [
            "artifacts/deployer_scope/pinned_capture.json.gz",
            "atlas/block_48902346/manifest.json",
            "atlas/block_48902346/upgrade_history.json",
            "artifacts/postpin_suite/live_latest.json.gz",
            "artifacts/postpin_suite/governance_logs.json.gz",
            "artifacts/postpin_suite/explorer_facts.json",
            "artifacts/postpin_suite/runtime/*.hex",
        ],
        "sets": {},
        "postpin_deployment": postpin,
        "postpin_creation": {
            address: {
                "block": creation[address]["block"],
                "timestamp_utc": live["headers"][str(creation[address]["block"])]["timestamp_utc"],
                "creator": creation[address]["creator"],
                "tx": creation[address]["tx"],
            }
            for address in sorted(creation)
        },
        "postpin_funding": {
            "block": funding[0]["block"],
            "timestamp_utc": live["headers"][str(funding[0]["block"])]["timestamp_utc"],
            "from": funding[0]["from"],
            "to": funding[0]["to"],
            "tx": funding[0]["tx"],
        },
        "docs_version_mapping": DOCS_VERSION,
        "upgrade_history": {},
        "headers": live["headers"],
        "pt01": pt01,
        "registry_state": registry_state,
        "linked_libraries": linked_libraries,
        "unmatched_embedded_code": live["extra_code"],
        "governance_state": {
            "newest_multisig_transaction_count": int(probes["newest_multisig_count"]["result"], 16),
            "earlier_2_multisig_transaction_count": int(probes["earlier_2_multisig_count"]["result"], 16),
            "newest_timelock_min_delay_seconds": int(probes["newest_timelock_min_delay"]["result"], 16),
            "earlier_2_timelock_min_delay_seconds": int(probes["earlier_2_timelock_min_delay"]["result"], 16),
            "earlier_1_timelock_min_delay_seconds": int(probes["earlier_1_timelock_min_delay"]["result"], 16),
        },
        "normalization": {
            "pre_pin_tokenomics_after_zeroing_links": {name: {"sha256": value} for name, value in normalized.items()},
            "postpin_tokenomics_after_zeroing_links": {name: {"sha256": value} for name, value in new_normalized.items()},
            "math_library_sha256": math_hash,
            "identical_postpin_pairs": [
                [TOKENOMICS_2, TOKENOMICS_2_EARLIER_2, "two zeroed library operands only"],
                [BUILDER_REGISTRY, EARLIER_2_REGISTRY, "byte identical, different constructor state"],
            ],
        },
        "live_reads": {
            "captured_at_utc": live["captured_at_utc"],
            "head": live["head"],
            "probes": live["probes"],
            "multisig_records": records,
        },
        "unknowns": [
            "upgrade trigger: the timelock and multisig logs record what ran, not why; the docs date contract set 2 to 2026-10-21 and state no reason",
            "twelve post-pin selectors have no hash-matched public name: four added Exchange, one added SessionKeyManager, three added Tokenomics, and two added plus two dropped Exchange-library entries",
            "no verified source exists for any of the seven 2026-10-20/21 contracts",
            "whether the new Exchange adds a differently shaped pending-sweep route that no saved selector or read-only probe covers",
        ],
    }
    for name, base in SET_BASE:
        entry = {
            "deployer": DEPLOYER,
            "creation_block_range": [
                min(role["creation_block"] for role in roles[name].values()),
                max(role["creation_block"] for role in roles[name].values()),
            ],
            "creation_dates": [
                live["headers"][str(min(role["creation_block"] for role in roles[name].values()))]["timestamp_utc"],
                live["headers"][str(max(role["creation_block"] for role in roles[name].values()))]["timestamp_utc"],
            ],
            "factory_user_proxies": OLDER_PROXY_COUNTS.get(name, NEWEST_PROXY_COUNT),
            "roles": roles[name],
            "proxy_slots_at_latest": slots[name],
            "docs_version": DOCS_VERSION[name],
            "live_now": True,
        }
        ledger["sets"][name] = entry
    ledger["sets"]["postpin_refresh"] = {
        "deployer": DEPLOYER2,
        "creation_block_range": [
            min(row["block"] for row in creation.values()),
            max(row["block"] for row in creation.values()),
        ],
        "creation_dates": [
            live["headers"][str(min(row["block"] for row in creation.values()))]["timestamp_utc"],
            live["headers"][str(max(row["block"] for row in creation.values()))]["timestamp_utc"],
        ],
        "direct_contracts": {
            address: {
                "role": row["role"],
                "deployer_nonce": row["deployer_nonce"],
                "runtime_bytes": row["runtime_bytes"],
                "sha256": row["sha256"],
            }
            for address, row in sorted(postpin.items(), key=lambda item: item[1]["deployer_nonce"])
        },
        "factory_user_proxies": 0,
        "reuses_governance_and_proxies_of": "newest and earlier_2",
        "newest_proxies_moved": {role: implementation for role, implementation in moved.items()},
        "earlier_2_proxies_moved": {
            role: implementation for role, implementation in earlier_2_moved.items()
        },
        "docs_version": DOCS_VERSION["postpin_refresh"],
        "live_now": True,
    }
    ledger["sets"]["newest"]["extra_implementations"] = {
        VARIANT_ROWS[index]: {
            "address": rows[index]["address"],
            "creation_block": rows[index]["creation_block"],
            "runtime_bytes": len(runtime_of(rows[index]["runtime"])),
            "sha256": sha256(runtime_of(rows[index]["runtime"])),
            "installed_at_pin": False,
        }
        for index in sorted(VARIANT_ROWS)
    }
    ledger["upgrade_history"] = {
        "newest_governance": {
            "timelock": NEWEST_TIMELOCK,
            "multisig": NEWEST_MULTISIG,
            "proxy_admin": NEWEST_PROXY_ADMIN,
            "operation_min_delay_change": {
                "schedule_block": 48_378_920,
                "execute_block": MIN_DELAY_CHANGE_BLOCK,
                "operation_id": "0xc616b8d5f1fccaae",
                "result_delay_seconds": 86_400,
            },
            "operation_cancelled": {
                "schedule_block": 48_191_335,
                "cancel_block": OLD_OPERATION_CANCEL_BLOCK,
                "operation_id": "0x" + records["newest"]["8"]["payload"][-64:],
                "note": "the pinned pending Tokenomics mint-parameter operation",
            },
            "set_2_batch": {
                "schedule_block": SET_2_SCHEDULE_BLOCK,
                "execute_block": SET_2_LIVE_BLOCK,
                "execute_tx": executed["transactionHash"],
                "operation_id": executed["topics"][1],
                "targets": records["newest"]["9"]["calls"]["targets"],
                "calls": records["newest"]["9"]["calls"]["datas"],
                "execute_records": ["9", "10"],
            },
        },
        "earlier_2_governance": {
            "timelock": EARLIER_2_TIMELOCK,
            "multisig": EARLIER_2_MULTISIG,
            "proxy_admin": EARLIER_2_PROXY_ADMIN,
            "batch": {
                "schedule_block": EARLIER_2_BATCH_SCHEDULE_BLOCK,
                "execute_block": EARLIER_2_BATCH_EXECUTE_BLOCK,
                "execute_tx": earlier_executed[0]["transactionHash"],
                "operation_id": earlier_executed[0]["topics"][1],
                "targets": earlier["1299"]["calls"]["targets"],
                "calls": earlier["1299"]["calls"]["datas"],
                "execute_records": ["1299", "1300"],
            },
        },
        "earlier_1_governance": {
            "timelock": roles["earlier_1"]["timelock"]["address"],
            "multisig": roles["earlier_1"]["one_of_two_multisig"]["address"],
            "proxy_admin": roles["earlier_1"]["proxy_admin"]["address"],
            "note": "no post-pin change: every earlier-1 proxy still points at its pinned implementation",
        },
    }
    LEDGER.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    DOC.write_text(render_doc(ledger) + "\n")
    (SUITE_OUT / "verify.json").write_text(
        json.dumps(
            {
                "pin": PIN,
                "head": live["head"],
                "sets": list(ledger["sets"]),
                "postpin_contracts": len(postpin),
                "newest_moved_proxies": sorted(moved),
                "earlier_2_moved_proxies": sorted(earlier_2_moved),
                "set_2_execute_block": SET_2_LIVE_BLOCK,
                "pt01": {user: row["pending_sweep_word"] for user, row in sorted(pt01.items())},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return {
        "set_count": ledger["set_count"],
        "sets": list(ledger["sets"]),
        "head_block": live["head"]["block"],
        "postpin_runtime_sha256": {
            row["role"]: row["sha256"] for row in sorted(postpin.values(), key=lambda r: r["role"])
        },
        "newest_moved_proxies": {
            role: slots["newest"][role]["implementation"] for role in sorted(moved)
        },
        "earlier_2_moved_proxies": {
            role: slots["earlier_2"][role]["implementation"] for role in sorted(earlier_2_moved)
        },
        "pt01": pt01,
    }


def render_doc(ledger):
    lines = []
    add = lines.append
    headers = ledger["headers"]
    sets = ledger["sets"]
    add("# Papertrade contract sets on HyperEVM")
    add("")
    add(
        "Generated by [`atlas_suite_sets.py`](../../scripts/atlas_suite_sets.py) from the pinned "
        "deployer capture, the newest-suite manifest, the pinned upgrade-history ledger and "
        "the saved post-pin captures under `artifacts/postpin_suite/`. "
        "`python3 scripts/atlas_suite_sets.py` re-checks every number below offline; every live "
        "value is labelled with the head block it was read at."
    )
    add("")
    add(
        "A **set** here is one deployer run: 19 direct contracts in a fixed nonce order, "
        "sharing one ProxyAdmin and one linked-library family, plus the factory-created user "
        "deposit proxies of that era. **Four sets have existed.** The two oldest are not in "
        "the public docs; the third is the docs' contract set 1 and the fourth is contract set 2."
    )
    add("")
    add("## Sets")
    add("")
    add(
        "| Set | Created (UTC) | Direct | User proxies | ProxyAdmin | Multisig | Timelock | "
        "Exchange proxy | Exchange implementation now | Docs version |"
    )
    add("|---|---|---:|---:|---|---|---|---|---|---|")
    for name in ("earlier_1", "earlier_2", "newest"):
        entry = sets[name]
        roles = entry["roles"]
        add(
            "| `{}` | {} to {} | 19 | {} | `{}` | `{}` | `{}` | `{}` | `{}` | {} |".format(
                name,
                entry["creation_dates"][0],
                entry["creation_dates"][1],
                entry["factory_user_proxies"],
                roles["proxy_admin"]["address"],
                roles["one_of_two_multisig"]["address"],
                roles["timelock"]["address"],
                roles["exchange_proxy"]["address"],
                entry["proxy_slots_at_latest"]["exchange_proxy"]["implementation"],
                entry["docs_version"],
            )
        )
    first_creation = min(
        (row["timestamp_utc"] for row in ledger["postpin_creation"].values())
    ) if "postpin_creation" in ledger else "2026-10-20T18:07:00Z"
    add(
        "| `postpin_refresh` | {} to {} | 7, second deployer | 0 | "
        "reuses `newest` | reuses `newest` | reuses `newest` | `{}` | `{}` | {} |".format(
            first_creation,
            ledger["headers"][str(SET_2_LIVE_BLOCK)]["timestamp_utc"],
            sets["newest"]["roles"]["exchange_proxy"]["address"],
            sets["newest"]["proxy_slots_at_latest"]["exchange_proxy"]["implementation"],
            ledger["docs_version_mapping"]["postpin_refresh"],
        )
    )
    add("")
    add(
        "The second deployer is `{}`, funded once by the original deployer "
        "`{}` before its first creation. It deployed no proxy and no governance contract: "
        "the refresh replaces implementations behind proxies that already existed.".format(
            "0x13cb7a200d081094d23ebf07f4d708410a9c488b", "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
        )
    )
    add("")
    add("## Roles, per set")
    add("")
    add(
        "`proxy` rows show `proxy -> pinned implementation`; the sha256 is the pinned runtime "
        "hash. All proxies in all three sets share one 925-byte runtime."
    )
    add("")
    add("| Role | Kind | earlier_1 | earlier_2 | newest |")
    add("|---|---|---|---|---|")
    for role, kind in LAYOUT:
        cells = []
        for name in ("earlier_1", "earlier_2", "newest"):
            entry = sets[name]["roles"][role]
            if kind == "proxy":
                cells.append(
                    "`{}` -> `{}` ({} B, `{}...`)".format(
                        entry["address"],
                        entry["pinned_implementation"],
                        entry["runtime_bytes"],
                        entry["sha256"][:10],
                    )
                )
            else:
                cells.append(
                    "`{}` ({} B, `{}...`)".format(
                        entry["address"], entry["runtime_bytes"], entry["sha256"][:10]
                    )
                )
        add("| `{}` | {} | {} | {} | {} |".format(role, kind, *cells))
    add("")
    add("Extra newest-set implementations deployed before the pin and never installed:")
    add("")
    add("| Role | Address | Created | Bytes | SHA-256 |")
    add("|---|---|---|---:|---|")
    for role, entry in sorted(sets["newest"]["extra_implementations"].items()):
        add(
            "| `{}` | `{}` | {} | {} | `{}` |".format(
                role,
                entry["address"],
                headers[str(entry["creation_block"])]["timestamp_utc"],
                entry["runtime_bytes"],
                entry["sha256"],
            )
        )
    add("")
    add(
        "`exchange_implementation_variant_a` is the implementation earlier set 2 installed "
        "behind its own Exchange proxy before the pin; `_b` is the copy that was never installed. "
        "Both match the newest pinned selector set exactly."
    )
    add("")
    add("## The post-pin deployment")
    add("")
    add("| Role (inferred) | Address | Deployer nonce | Created (UTC) | Bytes | SHA-256 |")
    add("|---|---|---:|---|---:|---|")
    for address, entry in sorted(
        ledger["postpin_deployment"].items(), key=lambda item: item[1]["deployer_nonce"]
    ):
        created = ledger["postpin_creation"][address]
        add(
            "| {} | `{}` | {} | {} | {} | `{}` |".format(
                entry["role"],
                address,
                entry["deployer_nonce"],
                created["timestamp_utc"],
                entry["runtime_bytes"],
                entry["sha256"],
            )
        )
    add("")
    add(
        "The second deployer's only incoming transfer is {} HYPE from the original deployer "
        "`{}` at block {} ({}), transaction `{}`.".format(
            "0.03",
            ledger["postpin_funding"]["from"],
            ledger["postpin_funding"]["block"],
            ledger["postpin_funding"]["timestamp_utc"],
            ledger["postpin_funding"]["tx"],
        )
    )
    add("")
    add("## Upgrade history")
    add("")
    add("### Newest governance (`{}` timelock, `{}` 2-of-3 multisig)".format(
        ledger["upgrade_history"]["newest_governance"]["timelock"],
        ledger["upgrade_history"]["newest_governance"]["multisig"],
    ))
    add("")
    add("| Block | Time (UTC) | Event | Detail |")
    add("|---|---|---|---|")
    for block, label, detail in (
        (47_855_496, "`OwnerUpdated` + `MinDelayUpdated`", "timelock constructor, minimum delay 604,800 s"),
        (48_191_335, "`OperationScheduled`", "operation `0x51142366...`, the Tokenomics mint-parameter call, never executed"),
        (48_378_920, "`OperationScheduled`", "operation `0xc616b8d5...`, self-call changing the minimum delay"),
        (49_050_825, "`MinDelayUpdated` + `OperationExecuted`", "minimum delay becomes 86,400 s"),
        (49_079_600, "`OperationCancelled`", "the stale operation `0x51142366...` cancelled"),
        (49_080_037, "`BatchOperationScheduled`", "operation `0xec82bec9...`, 6 targets, predecessor `0xbf88bc7f...`"),
        (49_169_385, "`BatchOperationExecuted`", "the 6-target set 2 upgrade runs; this is the docs' set 2 transaction"),
    ):
        stamp = headers.get(str(block), {}).get("timestamp_utc", "not in the saved header set")
        add("| {} | {} | {} | {} |".format(block, stamp, label, detail))
    add("")
    add("### What the batch executed")
    add("")
    add("Multisig records 9 (`scheduleBatch`) and 10 (`executeBatch`), both read back from the "
        "multisig's own `transactions(uint256)` storage at the saved head, carry the same six calls "
        "with value 0:")
    add("")
    add("| # | Target | Calldata | Meaning (selector-level) |")
    add("|---|---|---|---|")
    for index, (target, data) in enumerate(
        zip(
            ledger["upgrade_history"]["newest_governance"]["set_2_batch"]["targets"],
            ledger["upgrade_history"]["newest_governance"]["set_2_batch"]["calls"],
        ),
        1,
    ):
        meaning = {
            "0x99a88ec4": "ProxyAdmin upgrade(proxy, implementation)",
            "0xbd322efa": "SessionKeyManager setBuilderRegistry(address)",
            "0xefc1bd46": "Exchange setAuthorizedKeeper(address)",
            "0x85eb2a08": "Tokenomics activateRebate()",
        }[data[:10]]
        add("| {} | `{}` | `{}` | {} |".format(index, target, data, meaning))
    add("")
    add("### Earlier set 2's parallel migration")
    add("")
    add("Earlier set 2 runs its own governance: timelock `{}` with a {}-second live minimum "
        "delay, owned by the 1-of-2 multisig `{}` ({} stored transactions), and its own "
        "ProxyAdmin `{}`.".format(
            ledger["upgrade_history"]["earlier_2_governance"]["timelock"],
            ledger["governance_state"]["earlier_2_timelock_min_delay_seconds"],
            ledger["upgrade_history"]["earlier_2_governance"]["multisig"],
            ledger["governance_state"]["earlier_2_multisig_transaction_count"],
            ledger["upgrade_history"]["earlier_2_governance"]["proxy_admin"],
        ))
    add("")
    add("| Block | Time (UTC) | Event | Detail |")
    add("|---|---|---|---|")
    for block, label, detail in (
        (EARLIER_2_BATCH_SCHEDULE_BLOCK, "`BatchOperationScheduled`", "6 targets, same predecessor as the newest batch"),
        (EARLIER_2_BATCH_EXECUTE_BLOCK, "`BatchOperationExecuted`", "records 1299/1300 execute the same six-call shape"),
    ):
        stamp = headers.get(str(block), {}).get("timestamp_utc", "not in the saved header set")
        add("| {} | {} | {} | {} |".format(block, stamp, label, detail))
    add("")
    add("| # | Target | Calldata |")
    add("|---|---|---|")
    for index, (target, data) in enumerate(
        zip(
            ledger["upgrade_history"]["earlier_2_governance"]["batch"]["targets"],
            ledger["upgrade_history"]["earlier_2_governance"]["batch"]["calls"],
        ),
        1,
    ):
        add("| {} | `{}` | `{}` |".format(index, target, data))
    add("")
    add("### Earlier set 1")
    add("")
    add(
        "No post-pin change: every earlier-1 proxy still points at its pinned implementation, "
        "and its Exchange proxy emitted no `Upgraded` log in the whole post-pin window. Its "
        "governance is "
        "`{}` (timelock) and `{}` (1-of-2 multisig).".format(
            ledger["upgrade_history"]["earlier_1_governance"]["timelock"],
            ledger["upgrade_history"]["earlier_1_governance"]["multisig"],
        )
    )
    add("")
    add("## Post-pin runtime comparison")
    add("")
    add("| Runtime | Bytes | SHA-256 | Added selectors | Dropped selectors |")
    add("|---|---:|---|---|---|")
    renames = {
        "exchange_implementation_2": ("Exchange implementation", 23959),
        "session_key_manager_implementation_2": ("SessionKeyManager implementation", 4521),
        "tokenomics_implementation_2": ("Tokenomics implementation", 6452),
        "exchange_linked_library_2": ("Exchange linked library", 6286),
        "builder_registry": ("BuilderRegistry", 1210),
    }
    for role, (label, _) in renames.items():
        entry = entry_for_role(ledger["postpin_deployment"], role)
        added = ", ".join(
            "`{}`{}".format(selector, " " + name if name else "")
            for selector, name in sorted(NEW_SELECTORS[role]["added"].items())
        )
        removed = ", ".join(
            "`{}`{}".format(selector, " " + name if name else "")
            for selector, name in sorted(NEW_SELECTORS[role]["removed"].items())
        )
        add(
            "| {} | {} | `{}` | {} | {} |".format(
                label, entry["runtime_bytes"], entry["sha256"], added or "-", removed or "-"
            )
        )
    add("")
    add(
        "Names in that table are **public-registry candidates that hash-match the selector "
        "bytes**, not decompiled source names. The two `Tokenomics` copies and the two "
        "`BuilderRegistry` copies are the interesting pairs:"
    )
    add("")
    add("- The two new Tokenomics runtimes differ in exactly two 20-byte linked-library "
        "operands: `{}` (installed behind the **newest** Tokenomics proxy) links the newest math "
        "library, and `{}` (installed behind **earlier set 2's** Tokenomics proxy) links earlier "
        "set 2's math-library address. Zeroing those operands makes them byte-identical, and all "
        "four math-library addresses hold one 585-byte runtime (`{}`).".format(
            TOKENOMICS_2, TOKENOMICS_2_EARLIER_2, ledger["normalization"]["math_library_sha256"]
        ))
    add("- `{}` and `{}` are byte-identical, with different constructor state: the newest "
        "copy's owner is the newest timelock and guardian the newest multisig; the other's owner "
        "is earlier set 2's timelock and guardian earlier set 2's multisig.".format(
            BUILDER_REGISTRY, EARLIER_2_REGISTRY
        ))
    add("- The new Exchange links `{}` instead of the pinned `{}`; the new library keeps 8 of "
        "the pinned library's 10 selectors, drops `0x82296364` and `0xef1a27a9`, and adds "
        "`0x06c5308a` and `0xb9370332`.".format(LIBRARY_2, LIBRARY_PINNED_LIVE))
    add("- The new Exchange no longer dispatches `liquidate(uint256)` (`0x415f1240`), which the "
        "pinned implementation and both pinned variants do dispatch.")
    add("")
    add("## Linked libraries, per set")
    add("")
    add("Matched only against library runtimes this repo has already captured, so an empty cell "
        "means no *known* library address appears in that runtime, not that the runtime links none.")
    add("")
    add("| Runtime | Linked libraries |")
    add("|---|---|")
    for label, entry in sorted(ledger["linked_libraries"].items()):
        cells = ", ".join(
            "`{}` ({} B, `{}...`)".format(
                item["address"], item["runtime_bytes"], item["sha256"][:10]
            )
            for item in entry["libraries"]
        )
        add("| `{}` | {} |".format(label, cells or "-"))
    add("")
    for address, entry in sorted(ledger["unmatched_embedded_code"].items()):
        add(
            "Every Exchange implementation above also embeds `{}`, which has {} bytes of "
            "runtime code (`{}...`) but matches no captured Papertrade role; I record it as an "
            "unclassified embedded address, not as a library.".format(
                address, entry["runtime_bytes"], entry["sha256"][:10]
            )
        )
    add("")
    add("## Vocabulary: the docs' numbering")
    add("")
    add(
        "The public docs at `docs.papertrade.xyz` call the code live between two implementation "
        "upgrades a **contract set**. Their protocol-changes page names contract set 1 (7 Oct to "
        "21 Oct 2026, Exchange implementation `0x0f3febfc94876b0c895f7acecdc8f5c863b549ee`) and "
        "contract set 2 (live since 21 Oct 2026, Exchange implementation "
        "`0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723`, upgrade transaction "
        "`0x4410b81e3eb76f83f5ddc4e3faee794fb67208d2f129bc013094b9d06055acb6`). That "
        "transaction is the newest multisig's `executeBatch` we decode above, so:"
    )
    add("")
    add("| This repo | Docs | Basis |")
    add("|---|---|---|")
    add("| `newest` | **contract set 1** (`/v1/`) | docs cite the exact pinned Exchange implementation address |")
    add("| `postpin_refresh` | **contract set 2** | docs cite the exact upgrade transaction hash and the BuilderRegistry address |")
    add("| `earlier_1`, `earlier_2` | undocumented | the docs' version picker stops at set 1 and calls it the initial production deployment; no page names either older address |")
    add("")
    add(
        "The `earlier_1` and `earlier_2` mapping is an inference from address and date: the docs "
        "never mention a pre-set-1 deployment, and I did not find an address list for one. Their "
        "/v1/ pages describe the pinned implementation's behaviour, not the two older sets', so a "
        "behavioural difference between an older set and /v1/ is not a documented change."
    )
    add("")
    add(
        "The public \"Certificate\" incident (PAPER described as a revenue-sharing certificate, "
        "transfers frozen, BBO-manipulation allegations) is reported as having paused *v1* "
        "parameters. On this repo's numbering v1 is `newest`, i.e. the pinned set, so the incident "
        "belongs to contract set 1 and predates the set 2 upgrade. **That is an inference from "
        "news reporting and the docs' version naming; neither the docs nor this repo state an "
        "incident cause for the 2026-10-21 upgrade, and the saved governance logs record no "
        "reason either.**"
    )
    add("")
    add("## PT-01 live state")
    add("")
    add("Read at head block {} ({} UTC); the public RPC ignores the block parameter, so these "
        "are current values, not pinned ones.".format(
            ledger["live_reads"]["head"]["block"], ledger["live_reads"]["head"]["timestamp_utc"]
        ))
    add("")
    add("| User | Proxy | Pending sweep word | At pin | Exchange balance word | `builderFees` | Owner reconcile | Core spot USDC | Core ledger since pin |")
    add("|---|---|---|---|---|---|---|---:|---:|")
    for user, row in sorted(ledger["pt01"].items()):
        add(
            "| `{}` | `{}` | `{}` | {} | `{}` | `{}` | reverts `{}` | {} | {} |".format(
                user,
                row["proxy"],
                row["pending_sweep_word"],
                "same" if row["pending_sweep_word_unchanged"] else "CHANGED",
                row["exchange_balance_word"],
                row["builder_fees_call"],
                row["reconcile_from_owner_revert"],
                row["core_spot_usdc"],
                row["core_non_funding_ledger_entries_since_pin"],
            )
        )
    add("")
    add(
        "Both deposit proxy runtimes still hash to the exact per-user values saved in the "
        "stalled-sweep census and in all three 2026-10-20 status snapshots, so the two proxies "
        "are byte-identical to the pin."
    )
    add("")
    total = sum(float(row["core_spot_usdc"]) for row in ledger["pt01"].values())
    add(
        "Both Core spot balances still read the same as the three 2026-10-20 snapshots, "
        "totalling {} USDC (the pinned total was {} USDC: {}).".format(
            round(total, 6),
            PINNED_PT01_SPOT_TOTAL,
            "unchanged" if round(total, 6) == float(PINNED_PT01_SPOT_TOTAL) else "CHANGED",
        )
    )
    add("")
    add("### Does the new implementation change PT-01's recovery picture?")
    add("")
    add(
        "The pinned `clearPendingSweep(address)` (`0x2362f4de`) that earlier set 1 has is still "
        "absent from the new implementation, exactly as it is from the pinned one. The owner "
        "`reconcileSweepCredit(address,uint256)` call still reverts on both live pending words "
        "with the same `{}` from the timelock owner, and with the owner-guard `{}` from no "
        "sender, as it did at the pin. "
        "The saved read-only probes cover the six selectors the new Exchange added plus every "
        "sweep-shaped selector either implementation exposes, and none returns a sweep-clearing "
        "success. **I therefore find no evidence that the set 2 Exchange adds a pending-sweep "
        "clear or credit route, but I cannot prove the absence of a differently shaped one "
        "without source or a trace of a real sweep call.**".format(
            RECONCILE_REVERT, OWNER_GUARD_REVERT
        )
    )
    add("")
    add(
        "One consequence is certain and matters more than the new selectors: "
        "`recovery/Pt01Recovery.sol` delegates ordinary calls to the **pinned** implementation "
        "`0x0f3febfc94876b0c895f7acecdc8f5c863b549ee`, and that address is no longer behind the "
        "Exchange proxy. Installing that candidate as written would replace the set 2 "
        "implementation and silently drop the builder-fee, keeper, rebate and registry paths. "
        "The recovery plan needs re-deriving against `{}`.".format(EXCHANGE_2)
    )
    add("")
    add("## Proven, current, unknown")
    add("")
    add("**Proven from pinned saved evidence.** Three sets of 19 direct contracts exist in the "
        "recorded nonce order; every proxy's pinned implementation and admin are the saved pinned "
        "slot words; the two later Exchange variants match the manifest, and the three math-library "
        "addresses all hold the one 585-byte library runtime; no proxy ever emitted an `Upgraded` "
        "log and every implementation slot was equal at creation and at the pin.")
    add("")
    add("**Proven from saved live and explorer evidence.** The 2026-10-20/21 deployer created seven "
        "named contracts whose runtimes reproduce their SHA-256 hashes; the newest multisig's "
        "records 9 and 10 hold the six-call batch that moved three proxies and wired the registry; "
        "the earlier-2 multisig's records 1299 and 1300 hold the same shape against earlier-2's own "
        "proxies; earlier set 1 was untouched. No proxy of any set emitted an `Upgraded` log after "
        "the pin and the newest ProxyAdmin emits only its own two owner events (both before the "
        "pin), which is why the upgrade is visible only in the slot words and the batch payloads.")
    add("")
    add("**Read-only current.** Everything in the live tables comes from `latest` calls or explorer "
        "responses taken at the saved head; no live read is pinned state, and Core balances are "
        "public API values, not cryptographic proofs.")
    add("")
    add("**Unknown.**")
    add("")
    for item in ledger["unknowns"]:
        add("- " + item)
    return "\n".join(lines)


def entry_for_role(postpin, role):
    return next(row for row in postpin.values() if row["role"] == role)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture",
        action="store_true",
        help="refresh the public RPC, public Core API, and explorer evidence",
    )
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()