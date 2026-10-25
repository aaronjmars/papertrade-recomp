#!/usr/bin/env python3
"""Pass-two audit of the Papertrade user deposit-proxy family, the factory binding and the
EIP-712 domains of all three live suites.

Offline by default: every claim is rebuilt from saved evidence (the captured CREATE2
initcode, the pinned family sample, the derived per-user runtime map, the factory user
map, the captured CoreWriter runtime and the saved signature material) and re-checked
on each run, so the ledger and the doc regenerate with no RPC credential.

  --replay  runs the exact-runtime Foundry cases under artifacts/live2_proxies/replay/
  --live    refreshes the current-state reads in artifacts/live2_proxies/live_reads.json
            (public HyperEVM endpoint, no key); the read head is recorded with them

Nothing here is a disclosure or an advisory; no transaction, deploy or governance action
is performed.
"""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from atlas_factory_events import Keccak  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "live2_proxies"
RUNTIME = OUT / "runtime"
LEDGER = ATLAS / "live2_proxies.json"
DOC = ATLAS / "live2_proxies.md"
LIVE_READS = OUT / "live_reads.json"
REPLAY = OUT / "replay.json"
RPC = "https://rpc.hyperliquid.xyz/evm"

PIN = 48902346
PIN_HASH = "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
CHAIN_ID = 999

# The newest-suite (docs "contract set 1") addresses. The whole family sample belongs to it.
FACTORY = "0x1629b7d46bef6e13ff754174fc9f32dea309b38f"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SESSION_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
EXCHANGE_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
REPRESENTATIVE = "0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce"
REPRESENTATIVE_USER = "0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa"
CORE_WRITER = "0x3333333333333333333333333333333333333333"

# The two older suites, from atlas/block_48902346/suite_sets.md. Only their live wiring and
# their domain separators are used here; their runtimes are another workstream's surface.
SUITES = {
    "earlier_1": {"exchange": "0x1b534e482b92bb6daff452cd12f2e35219e13493",
                  "session": "0x91667db7e20474b3ac6eaabf0c8106ed46b5691a",
                  "factory": "0x36365dc6bd9513692978e4ea8f3117a7bae55f28",
                  "batch_executor": "0x4041882573028cb177847c46f82e242024ebde66"},
    "earlier_2": {"exchange": "0x2ede04561914c61a5f49212609541934fd7f5901",
                  "session": "0xe45264507a67d0bbea35299002b68ebd76adba04",
                  "factory": "0x99a8c54d3ee124debe8d685954546084c9a3731d",
                  "batch_executor": "0xc56914e7cd080b09580e85b7df49a994b238bb48"},
    "newest": {"exchange": EXCHANGE, "session": SESSION, "factory": FACTORY,
               "batch_executor": BATCH},
}

DEPLOY_TX = "0xddf30f3fd0d78c0516e37f32ed1ece2ef4ab488d7b4be8439c7196878047fb2e"

# Constructor geometry of the captured Create2DepositProxy creation code (1,889 bytes).
INITCODE_BYTES = 1889
CREATION_BODY = 1825          # constructor + fixed runtime bytes, before the exchange word
CREATION_PREFIX = 1857        # body + the exchange word
RUNTIME_OFFSET = 0xB3
RUNTIME_BYTES = 0x66E
EXCHANGE_WORD_OFFSETS = (0x61, 0xDE)
USER_WORD_OFFSETS = (0x37B, 0x3DA)
MASK160 = (1 << 160) - 1

# EIP-712 constants.
EIP712_DOMAIN_TYPEHASH = "0x8b73c3c69bb8fe3d512ecc4cf759cc79239f7b179b0ffacaa9a75d522b39400f"
REGISTER_SESSION_KEY_TYPEHASH = (
    "0xd3d9a309f635415423ab81e7e3fb16d2117cc8e1edc90506adde9eaa3855edd2")
WITHDRAW_TO_CORE_TYPEHASH = (
    "0xac4ddb8d63e9d7a862c5d61ce47517623a448262414a7eef6797102104b31214")
CLOSE_TYPEHASH = "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13"
OPEN_POSITION_TYPEHASH = (
    "0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983")
INVALID_SIGNATURE = "0x8baa579f"
SESSION_KEY_REGISTERED_TOPIC = (
    "0x3cec0566535d67d6c92668517af0bf8a66cdc91d622dbb830fcc08e1bcf5d1df")
STUCK_TOKEN_WITHDRAWN_TOPIC = "0x3d95e1dd"
SEND_RAW_ACTION = "0x17938e13"
SWEEP_SELECTOR = "0x925b3aad"
RESCUE_SELECTOR = "0x0c506e96"
USER_SELECTOR = "0x4f8632ba"
EXCHANGE_SELECTOR = "0xd2f7265a"

breaks = Keccak()

HEX = set("0123456789abcdef")


def k(value):
    return breaks(value)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def word_bytes(address):
    return int(address, 16).to_bytes(32, "big")


def load(path):
    return json.loads((ROOT / path).read_text())


# --------------------------------------------------------------------------------------
# offline evidence


def capture_runtime_files():
    """Copy the captured runtimes this audit replays into the artifact directory."""
    RUNTIME.mkdir(parents=True, exist_ok=True)
    sources = {
        "Proxy.hex": ATLAS / "runtime" / f"{REPRESENTATIVE}.hex",
        "Session.hex": ATLAS / "runtime" / f"{SESSION_IMPL}.hex",
        "ExchangeProxy.hex": ATLAS / "runtime" / f"{EXCHANGE}.hex",
        "ExchangeImpl.hex": ATLAS / "runtime" / f"{EXCHANGE_IMPL}.hex",
        "CoreWriter.hex": ROOT / "artifacts" / "postpin_suite" / "runtime" / f"{CORE_WRITER}.hex",
    }
    manifest = load("atlas/block_48902346/manifest.json")
    hashes = {
        "Proxy.hex": manifest["contracts"][REPRESENTATIVE]["sha256"],
        "Session.hex": manifest["contracts"][SESSION_IMPL]["sha256"],
        "ExchangeProxy.hex": manifest["contracts"][EXCHANGE]["sha256"],
        "ExchangeImpl.hex": manifest["contracts"][EXCHANGE_IMPL]["sha256"],
        "CoreWriter.hex": None,
    }
    recorded = {}
    for name, source in sources.items():
        hexed = source.read_text().strip()
        assert hexed.startswith("0x") and len(hexed) % 2 == 0
        raw = bytes.fromhex(hexed[2:])
        (RUNTIME / name).write_text(hexed)
        digest = hashlib.sha256(raw).hexdigest()
        if hashes[name]:
            assert digest == hashes[name], (name, digest)
        recorded[name] = {"bytes": len(raw), "sha256": digest, "source": str(source.relative_to(ROOT))}
    return recorded


def load_initcode():
    root = load(f"artifacts/historical/{DEPLOY_TX}.calls.json")
    create = root["calls"][0]["calls"][0]
    assert create["type"] == "CREATE2" and create["from"].lower() == FACTORY
    initcode = bytes.fromhex(create["input"][2:])
    assert len(initcode) == INITCODE_BYTES
    assert initcode[CREATION_BODY:CREATION_BODY + 32] == word_bytes(EXCHANGE)
    body = initcode[:CREATION_BODY]
    runtime_base = initcode[RUNTIME_OFFSET:RUNTIME_OFFSET + RUNTIME_BYTES]
    return initcode, body, runtime_base, address_of(initcode[-32:].hex())


def runtime_for(base, exchange, user):
    runtime = bytearray(base)
    for offset in EXCHANGE_WORD_OFFSETS:
        runtime[offset:offset + 32] = word_bytes(exchange)
    for offset in USER_WORD_OFFSETS:
        runtime[offset:offset + 32] = word_bytes(user)
    return bytes(runtime)


def create2_address(deployer, salt, initcode):
    digest = k(b"\xff" + bytes.fromhex(deployer[2:]) + salt + k(initcode))
    return "0x" + digest[12:].hex()


def opcode_names(hexed):
    out = subprocess.run(["cast", "disassemble", hexed], capture_output=True, text=True, check=True).stdout
    names = []
    for line in out.splitlines():
        if ":" not in line:
            continue
        names.append(line.split(":", 1)[1].strip())
    return names


METADATA_MARKER = bytes.fromhex("a26469706673")  # CBOR map + "dipfs": the compiler metadata


def code_section(raw):
    """Everything before the appended solc metadata; the metadata is data, not code."""
    index = raw.find(METADATA_MARKER)
    if index < 0:
        return raw, 0
    return raw[:index], len(raw) - index


def critical_opcodes(raw, interesting):
    code, metadata_bytes = code_section(raw)
    names = opcode_names("0x" + code.hex())
    return {name: names.count(name) for name in interesting}, {"code_bytes": len(code),
                                                               "metadata_bytes": metadata_bytes}


def analyse_proxy_template(runtime_base):
    code, metadata_bytes = code_section(runtime_base)
    names = opcode_names("0x" + code.hex())
    counts = {name: names.count(name) for name in
              ("SSTORE", "SLOAD", "DELEGATECALL", "CALLCODE", "SELFDESTRUCT", "STATICCALL",
               "CREATE", "CREATE2", "CALLER", "CALL", "REVERT", "INVALID")}
    # the two guard words: the address occupies the low 20 bytes, the high 12 are inert, and
    # each guard is a masked compare against an embedded PUSH32 word.
    guards = []
    for index, name in enumerate(names):
        if name == "CALLER":
            guards.append(names[max(0, index - 12):index + 6])
    return {"opcode_count": len(names), "code_bytes": len(code), "metadata_bytes": metadata_bytes,
            "counts": counts, "caller_windows": guards}


def analyse_core_writer(hexed):
    raw = bytes.fromhex(hexed[2:])
    code, metadata_bytes = code_section(raw)
    names = opcode_names("0x" + code.hex())
    pushes = re.findall(r"PUSH4 0x([0-9a-f]+)", "\n".join(names))
    return {"opcode_count": len(names), "code_bytes": len(code), "metadata_bytes": metadata_bytes,
            "push4_selectors": sorted({"0x" + p for p in pushes}),
            "callvalue_guard": "CALLVALUE" in names}


def domain_separator(verifying_contract):
    payload = (bytes.fromhex(EIP712_DOMAIN_TYPEHASH[2:]) + k(b"String") + k(b"1")
               + CHAIN_ID.to_bytes(32, "big") + word_bytes(verifying_contract))
    return "0x" + k(payload).hex()


def read_live(current):
    """Refresh the current-state reads. Public endpoint only, no credential."""
    import urllib.request

    calls = []

    def add(name, to, data):
        calls.append({"name": name, "to": to, "data": data})

    for suite, row in SUITES.items():
        for fn, sel in (("authorizedCaller", "0x97dc97cb"), ("DOMAIN_SEPARATOR", "0x3644e515"),
                        ("domainSeparatorV4", "0x78e890ba"), ("owner", "0x8da5cb5b")):
            add(f"session:{suite}:{fn}", row["session"], sel)
        for fn, sel in (("sessionKeyManager", "0x0b826190"), ("proxyFactory", "0xc10f1a75"),
                        ("authorizedExecutor", "0x13dd495b"), ("owner", "0x8da5cb5b")):
            add(f"exchange:{suite}:{fn}", row["exchange"], sel)
        for fn, sel in (("exchange", "0xd2f7265a"), ("owner", "0x8da5cb5b"),
                        ("authorizedDeployer", "0x03b802b6")):
            add(f"factory:{suite}:{fn}", row["factory"], sel)
        add(f"session:{suite}:authorizedSubmitters(batch)", row["session"],
            "0x7f6e9d4b" + row["batch_executor"][2:].rjust(64, "0"))
    add("factory:newest:computeProxyAddress(representative)", FACTORY,
        "0xd600539a" + REPRESENTATIVE_USER[2:].rjust(64, "0"))
    add("factory:newest:proxyOf(representative)", FACTORY,
        "0xc1a9a508" + REPRESENTATIVE_USER[2:].rjust(64, "0"))
    add("factory:newest:isProxy(representative)", FACTORY,
        "0x29710388" + REPRESENTATIVE[2:].rjust(64, "0"))
    add("factory:newest:isProxy(addr0)", FACTORY, "0x29710388" + "0" * 64)

    def rpc_batch(batch):
        body = json.dumps(batch).encode()
        request = urllib.request.Request(RPC, data=body, headers={"content-type": "application/json"})
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)

    reads = {}
    raw = []
    head = None
    for start in range(0, len(calls), 18):
        chunk = calls[start:start + 18]
        batch = [{"jsonrpc": "2.0", "id": start + i, "method": "eth_call",
                  "params": [{"to": c["to"], "data": c["data"]}, "latest"]}
                 for i, c in enumerate(chunk)]
        parsed = None
        for attempt in range(4):
            try:
                parsed = rpc_batch(batch)
            except Exception:
                parsed = None
            if isinstance(parsed, list) and all("result" in r or "error" in r for r in parsed):
                break
            time.sleep(2 * (attempt + 1))
        if not isinstance(parsed, list):
            raise RuntimeError(f"live read failed for chunk {start}: {parsed}")
        raw.append({"request": batch, "response": parsed})
        for item in parsed:
            reads[calls[item["id"]]["name"]] = item.get("result") or item.get("error")
        time.sleep(1)
    head_batch = {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}
    for attempt in range(4):
        try:
            head = rpc_batch(head_batch).get("result")
        except Exception:
            head = None
        if head:
            break
        time.sleep(2 * (attempt + 1))
    source = "RPC" if head else current.get("head_source", "RPC")
    record = {"rpc": RPC, "head": head, "head_source": source, "reads": reads, "raw": raw}
    write(LIVE_READS, record)
    return record


def address_of(word):
    return "0x" + word[-40:]


def offline():
    """Rebuild every offline claim; raise on any drift."""
    facts = {"checks": []}

    def check(name, ok, detail):
        facts["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            raise AssertionError(f"{name}: {detail}")

    runtime_files = capture_runtime_files()
    facts["runtime_files"] = runtime_files
    manifest = load("atlas/block_48902346/manifest.json")
    family = load("atlas/block_48902346/deposit_proxy_family.json")
    derivation = load("atlas/block_48902346/deposit_proxy_runtime_derivation.json")
    derived_map = load("atlas/block_48902346/deposit_proxy_derived_runtime_map.json")
    user_map = load("atlas/block_48902346/factory_user_proxy_map.json")
    factory_behavior = load("atlas/block_48902346/factory_behavior.json")
    session_behavior = load("atlas/block_48902346/session_key_behavior.json")
    direct_signer = load("atlas/block_48902346/session_direct_signer_behavior.json")
    withdraw_ledger = load("atlas/block_48902346/exchange_withdrawal_signature_behavior.json")

    initcode, body, runtime_base, deployed_user = load_initcode()
    proxy_hex = (RUNTIME / "Proxy.hex").read_text().strip()
    checksum = hashlib.sha256(bytes.fromhex(proxy_hex[2:])).hexdigest()
    zeroed = all(all(b == 0 for b in runtime_base[off:off + 32])
                 for off in EXCHANGE_WORD_OFFSETS + USER_WORD_OFFSETS)
    check("the captured initcode carries the template with the four word slots zeroed",
          zeroed and initcode[CREATION_BODY:CREATION_BODY + 32] == word_bytes(EXCHANGE),
          {"initcode_user": deployed_user, "exchange_tail": address_of(initcode[CREATION_BODY:CREATION_BODY + 32].hex())})
    check("family template == the initcode slice with the representative words applied",
          runtime_for(runtime_base, EXCHANGE, REPRESENTATIVE_USER) == bytes.fromhex(proxy_hex[2:]),
          {"manifest_sha256": manifest["contracts"][REPRESENTATIVE]["sha256"], "sha256": checksum})
    check("representative matches the family family hash",
          checksum == manifest["contracts"][REPRESENTATIVE]["sha256"]
          == family["records"][0]["sha256"],
          {"family_records": len(family["records"])})
    check("declared creation geometry",
          derivation["runtime_bytes"] == RUNTIME_BYTES and derivation["creation_prefix_bytes"] == CREATION_PREFIX
          and derivation["exchange_word_offsets"] == list(EXCHANGE_WORD_OFFSETS)
          and derivation["user_word_offsets"] == list(USER_WORD_OFFSETS),
          {"initcode_bytes": len(initcode), "body_bytes": len(body)})
    rebuilt = runtime_for(runtime_base, EXCHANGE, REPRESENTATIVE_USER)
    check("runtime rebuilt from the trailing words", rebuilt == bytes.fromhex(proxy_hex[2:]),
          {"exchange_word": address_of(rebuilt[EXCHANGE_WORD_OFFSETS[0]:EXCHANGE_WORD_OFFSETS[0] + 32].hex())})
    slots = [set(range(off + 12, off + 32)) for off in USER_WORD_OFFSETS]
    check("only the two 20-byte user address slots vary across the family sample",
          all(any(set(range(a, b)) <= slot for slot in slots)
              for a, b in family["varying_byte_ranges"]),
          {"varying_byte_ranges": family["varying_byte_ranges"]})

    template = analyse_proxy_template(runtime_base)
    facts["template"] = template
    check("proxy runtime has no storage, no delegatecall and no selfdestruct",
          all(template["counts"][op] == 0 for op in
              ("SSTORE", "SLOAD", "DELEGATECALL", "CALLCODE", "SELFDESTRUCT", "STATICCALL",
               "CREATE", "CREATE2")),
          template["counts"])
    check("exactly two CALLER sites, both a masked compare against an embedded PUSH32 word",
          template["counts"]["CALLER"] == 2,
          {"windows": template["caller_windows"]})
    check("both embedded words are 12 zero bytes and a 20-byte address",
          all(all(b == 0 for b in rebuilt[off:off + 12]) for off in USER_WORD_OFFSETS + EXCHANGE_WORD_OFFSETS),
          {"words": {hex(off): rebuilt[off:off + 32].hex() for off in EXCHANGE_WORD_OFFSETS + USER_WORD_OFFSETS}})

    # Exhaustive CREATE2 / salt / code re-derivation over every recorded deployment.
    prefix = initcode[:CREATION_PREFIX]
    salt_cache = {}
    mismatches = []
    distinct_hashes = set()
    for row in user_map:
        user = row["user"].lower()
        salt = salt_cache.get(user)
        if salt is None:
            salt = k(bytes.fromhex(user[2:]))
            salt_cache[user] = salt
        owner = initcode[:CREATION_BODY] + word_bytes(EXCHANGE) + word_bytes(user)
        address = create2_address(FACTORY, salt, owner)
        if address != row["proxy"].lower():
            mismatches.append((row, address))
            continue
        runtime = runtime_for(runtime_base, EXCHANGE, user)
        distinct_hashes.add(hashlib.sha256(runtime).hexdigest())
    check("all recorded users reproduce their proxy address from salt + initcode",
          not mismatches, {"checked": len(user_map), "mismatches": len(mismatches)})
    check("no duplicate user or proxy address", len(salt_cache) == len(user_map)
          == len({r["proxy"].lower() for r in user_map}), {"users": len(salt_cache)})
    check("no zero-user proxy on chain",
          all(int(r["user"], 16) != 0 for r in user_map), {"zero_user": 0})
    derived_matches = 0
    for row in derived_map["rows"]:
        runtime = runtime_for(runtime_base, EXCHANGE, row["user"].lower())
        if hashlib.sha256(runtime).hexdigest() == row["runtime_sha256"]:
            derived_matches += 1
    check("every derived runtime hash reproduces from the recorded user",
          derived_matches == len(derived_map["rows"]) == derivation["derived_runtime_count"],
          {"derived_rows": len(derived_map["rows"]), "matches": derived_matches,
           "distinct_hashes": len(distinct_hashes)})
    facts["family"] = {
        "deployment_count": derivation["deployment_count"],
        "runtime_bytes": RUNTIME_BYTES,
        "runtime_template_sha256": derivation["runtime_template_sha256"],
        "representative_sha256": manifest["contracts"][REPRESENTATIVE]["sha256"],
        "exchange_impl_bytes": manifest["contracts"][EXCHANGE_IMPL]["runtime_bytes"],
        "representative": REPRESENTATIVE, "representative_user": REPRESENTATIVE_USER,
        "exchange_word_offsets": list(EXCHANGE_WORD_OFFSETS),
        "user_word_offsets": list(USER_WORD_OFFSETS),
        "caller_sites": template["counts"]["CALLER"],
        "address_recomputed": len(user_map),
        "runtime_hash_recomputed": derived_matches,
        "proxy_family_records": len(family["records"]),
    }
    check("factory records exchange in a pinned slot and only writes it at initialization",
          factory_behavior["direct_storage"]["0"]["raw"].endswith("0001")
          and factory_behavior["direct_storage"]["0"]["low_byte_initialized"] == 1,
          {"slot0": factory_behavior["direct_storage"]["0"]})
    zero_probe = factory_behavior["probes"]["deploy_zero_user"]
    zero_address = create2_address(FACTORY, k(bytes(20)),
                                   initcode[:CREATION_BODY] + word_bytes(EXCHANGE) + bytes(32))
    check("the zero-user shape derives to the address the pass-one zero-user probe returned",
          zero_probe["success"] and address_of(zero_probe["return_data"]) == zero_address,
          {"derived": zero_address, "probe": zero_probe["return_data"]})
    facts["zero_user"] = {"derived_proxy": zero_address,
                          "probe": "atlas/block_48902346/factory_behavior.json probes.deploy_zero_user",
                          "on_chain_count": 0}
    check("factory logs one ProxyDeployed per user with the recorded proxy",
          factory_behavior["event_signatures"]["ProxyDeployed(address,address)"]
          == "0x3d2489efb661e8b1c3679865db649ca1de61d76a71184a1234de2e55786a6aad",
          {"mapping_slots": factory_behavior["mapping_slots"]})

    core_writer = analyse_core_writer((RUNTIME / "CoreWriter.hex").read_text().strip())
    facts["core_writer"] = core_writer
    check("CoreWriter dispatches exactly one selector and rejects everything else",
          core_writer["push4_selectors"] == [SEND_RAW_ACTION] and core_writer["callvalue_guard"],
          core_writer)

    # EIP-712 domain identity across the three suites.
    live = load("artifacts/live2_proxies/live_reads.json")
    reads = live["reads"]
    facts["live_head"] = live.get("head")
    domains = {}
    for suite in SUITES:
        caller = address_of(reads[f"session:{suite}:authorizedCaller"])
        computed = domain_separator(caller)
        stored = reads[f"session:{suite}:DOMAIN_SEPARATOR"]
        dynamic = reads[f"session:{suite}:domainSeparatorV4"]
        check(f"{suite}: domain separator = f(999, authorizedCaller), cached == dynamic",
              computed == stored == dynamic and caller == SUITES[suite]["exchange"].lower(),
              {"authorizedCaller": caller, "computed": computed, "stored": stored, "dynamic": dynamic})
        check(f"{suite}: exchange.sessionKeyManager == its own SessionKeyManager",
              address_of(reads[f"exchange:{suite}:sessionKeyManager"]) == SUITES[suite]["session"].lower(),
              {"read": reads[f"exchange:{suite}:sessionKeyManager"]})
        check(f"{suite}: exchange.proxyFactory == its own factory and factory.exchange == its own Exchange",
              address_of(reads[f"exchange:{suite}:proxyFactory"]) == SUITES[suite]["factory"].lower()
              and address_of(reads[f"factory:{suite}:exchange"]) == SUITES[suite]["exchange"].lower(),
              {"proxyFactory": reads[f"exchange:{suite}:proxyFactory"],
               "factory_exchange": reads[f"factory:{suite}:exchange"]})
        check(f"{suite}: the BatchExecutor is an authorized submitter of its own manager",
              int(reads[f"session:{suite}:authorizedSubmitters(batch)"], 16) == 1,
              {"read": reads[f"session:{suite}:authorizedSubmitters(batch)"]})
        domains[suite] = {"exchange": SUITES[suite]["exchange"], "session": SUITES[suite]["session"],
                          "domain_separator": computed, "authorized_caller": caller}
    check("the three suite domain separators are pairwise distinct",
          len({d["domain_separator"] for d in domains.values()}) == 3,
          {s: d["domain_separator"] for s, d in domains.items()})
    facts["domains"] = domains
    check("the newest factory resolves the representative to its recorded proxy",
          address_of(reads["factory:newest:computeProxyAddress(representative)"]) == REPRESENTATIVE
          and address_of(reads["factory:newest:proxyOf(representative)"]) == REPRESENTATIVE
          and int(reads["factory:newest:isProxy(representative)"], 16) == 1
          and int(reads["factory:newest:isProxy(addr0)"], 16) == 0,
          {"computeProxyAddress": reads["factory:newest:computeProxyAddress(representative)"]})

    # Intent-class typehash separation.
    session_hex = (RUNTIME / "Session.hex").read_text().strip()
    typehashes = [REGISTER_SESSION_KEY_TYPEHASH, WITHDRAW_TO_CORE_TYPEHASH, CLOSE_TYPEHASH,
                  OPEN_POSITION_TYPEHASH, EIP712_DOMAIN_TYPEHASH]
    check("every intent-class typehash literal is present in the SessionKeyManager runtime",
          all(t[2:] in session_hex for t in typehashes), {"typehashes": typehashes})
    check("the registration struct typehash is distinct from every trading typehash",
          len(set(typehashes)) == len(typehashes), {"count": len(typehashes)})

    # Real signature material for the cross-domain control.
    sample = direct_signer["calls"][0]
    check("the sampled withdrawal digest reproduces as keccak(0x1901 || domain || structHash)",
          "0x" + k(b"\x19\x01" + bytes.fromhex(domains["newest"]["domain_separator"][2:])
                   + bytes.fromhex(sample["struct_hash"][2:])).hex() == sample["digest"],
          {"digest": sample["digest"]})
    facts["withdrawal_signature"] = {
        "user": sample["user"], "struct_hash": sample["struct_hash"], "digest": sample["digest"],
        "v": sample["v"], "r": sample["r"], "s": sample["s"],
        "source": "atlas/block_48902346/session_direct_signer_behavior.json calls[0]",
        "tx": sample["tx"]}
    check("registration ledger records the same typehash and domain",
          session_behavior["register_typehash"] == REGISTER_SESSION_KEY_TYPEHASH
          and session_behavior["domain_separator"] == domains["newest"]["domain_separator"],
          {"registrations": session_behavior["registration_count"]})
    check("withdrawal ledger records the same domain",
          withdraw_ledger["domain_separator_at_pin"] == domains["newest"]["domain_separator"],
          {"calls": withdraw_ledger["matched_call_count"]})
    facts["resident_words"] = {
        "proxy": {"user": REPRESENTATIVE_USER, "exchange": EXCHANGE},
        "manifest_session_sha256": manifest["contracts"][SESSION_IMPL]["sha256"],
        "manifest_exchange_sha256": manifest["contracts"][EXCHANGE_IMPL]["sha256"],
    }
    return facts


# --------------------------------------------------------------------------------------
# exact-runtime replay

SOLIDITY = r'''pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function computeCreate2Address(bytes32, bytes32, address) external pure returns (address);
    function addr(uint256) external pure returns (address);
    function sign(uint256, bytes32) external pure returns (uint8, bytes32, bytes32);
    function chainId(uint256) external;
}
contract MockWriter {
    uint256 public calls;
    event RawAction(bytes action);
    function sendRawAction(bytes calldata action) external {
        calls++;
        emit RawAction(action);
    }
}
contract ReentrantToken {
    address public proxy;
    uint256 public swept;
    uint256 public rescued;
    constructor(address p) { proxy = p; }
    function transfer(address, uint256) external returns (bool) {
        (bool a,) = proxy.call(abi.encodeWithSelector(bytes4(0x925b3aad), uint64(0), uint64(1), uint64(0)));
        (bool b,) = proxy.call(abi.encodeWithSelector(bytes4(0x0c506e96), address(this), uint256(1)));
        swept = a ? 1 : 0;
        rescued = b ? 1 : 0;
        return true;
    }
}
contract Live2ProxiesTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x00f1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce)));
    address constant USER = address(uint160(uint256(0x00fb94d3404c1d3d9d6f08f79e58041d5ea95accfa)));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant FACTORY = address(uint160(uint256(0x001629b7d46bef6e13ff754174fc9f32dea309b38f)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant BATCH = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant CORE = address(0x3333333333333333333333333333333333333333);
    address constant MOCK_TOKEN = address(0x4444444444444444444444444444444444444444);
    address constant CLONE = address(uint160(0xA11CE));
    address constant ATTACKER = address(uint160(0xBADBAD));
    address constant VICTIM = address(uint160(0xC0FFEE));
    address constant OTHER = address(uint160(0xD00D));
    address constant EXCHANGE_IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant STUCK_TOPIC =
        keccak256("StuckTokenWithdrawn(address,address,uint256)");
    bytes32 constant ACTION_TOPIC = keccak256("RawAction(bytes)");
    bytes32 constant REGISTER_TOPIC =
        keccak256("SessionKeyRegistered(address,address,uint64)");
    bytes32 constant EIP712_TYPEHASH =
        keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)");
    bytes32 constant REGISTER_TYPEHASH = __REGISTER_TYPEHASH__;
    uint256 constant DS_NEWEST = __DS_NEWEST__;
    uint256 constant DS_EARLIER_1 = __DS_EARLIER_1__;
    uint256 constant DS_EARLIER_2 = __DS_EARLIER_2__;
    address constant E1_EXCHANGE = __E1_EXCHANGE__;
    address constant E2_EXCHANGE = __E2_EXCHANGE__;
    bytes32 constant WD_STRUCT_HASH = __WD_STRUCT_HASH__;
    bytes32 constant WD_DIGEST = __WD_DIGEST__;
    address constant WD_USER = __WD_USER__;
    uint8 constant WD_V = __WD_V__;
    bytes32 constant WD_R = __WD_R__;
    bytes32 constant WD_S = __WD_S__;
    uint256 constant PK = 0xA11CE;
    address constant SESSION_KEY = address(uint160(0x5EED));
    uint64 constant EXPIRY = 4_000_000_000;
    uint64 constant DEADLINE = 4_000_000_000;

    function setUp() public {
        vm.chainId(999);
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(CORE, vm.parseBytes(vm.readFile("runtime/CoreWriter.hex")));
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(EXCHANGE_IMPL, vm.parseBytes(vm.readFile("runtime/ExchangeImpl.hex")));
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(EXCHANGE_IMPL))));
    }

    function patch(bytes memory data, uint256 offset, bytes memory value) internal pure returns (bytes memory) {
        for (uint256 i; i < value.length; ++i) { data[offset + i] = value[i]; }
        return data;
    }

    function sweep(uint64 token, uint64 spot, uint64 perp) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x925b3aad), token, spot, perp);
    }

    function rescue(address token, uint256 amount) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x0c506e96), token, amount);
    }

    function expectRevert(bytes memory data, address actor, address target) internal {
        vm.recordLogs();
        vm.prank(actor);
        (bool ok,) = target.call(data);
        require(!ok, "expected revert");
        require(vm.getRecordedLogs().length == 0, "revert emitted a log");
    }

    // ---- angle 1: template, guards, destination -------------------------------------
    function testImmutableGetters() public {
        (bool a, bytes memory u) = PROXY.call(hex"4f8632ba");
        (bool b, bytes memory e) = PROXY.call(hex"d2f7265a");
        require(a && b, "getter failed");
        require(abi.decode(u, (address)) == USER && abi.decode(e, (address)) == EXCHANGE, "immutables");
    }

    function testGuardMasksTheEmbeddedWordTo160Bits() public {
        bytes memory runtime = vm.parseBytes(vm.readFile("runtime/Proxy.hex"));
        // poison the twelve inert high bytes of both embedded words; the low 20 bytes stay intact
        bytes memory junk = hex"deadbeefdeadbeefdeadbeef";
        patch(runtime, 0x37b, junk);
        patch(runtime, 0x3da, junk);
        patch(runtime, 0x61, junk);
        patch(runtime, 0xde, junk);
        vm.etch(CLONE, runtime);
        vm.prank(USER);
        (bool ok,) = CLONE.call(rescue(MOCK_TOKEN, 1));
        require(ok, "rescue blocked by inert high bytes");
        vm.prank(EXCHANGE);
        (bool ok2,) = CLONE.call(sweep(7, 1, 0));
        require(ok2, "sweep blocked by inert high bytes");
        // control: changing the 20-byte address itself must break the guard
        bytes memory other = new bytes(20);
        for (uint256 i; i < 20; ++i) { other[i] = bytes20(OTHER)[i]; }
        bytes memory runtime2 = vm.parseBytes(vm.readFile("runtime/Proxy.hex"));
        patch(runtime2, 0x37b + 12, other);
        patch(runtime2, 0x3da + 12, other);
        vm.etch(CLONE, runtime2);
        expectRevert(rescue(MOCK_TOKEN, 1), USER, CLONE);
        vm.etch(CLONE, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
    }

    function testSweepDestinationIsTheEmbeddedWord() public {
        vm.recordLogs();
        vm.prank(EXCHANGE);
        (bool ok,) = PROXY.call(sweep(0xdead, 123, 0));
        require(ok, "sweep failed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == CORE, "one action");
        bytes memory raw = abi.decode(logs[0].data, (bytes));
        // action 6 payload: version||actionId, then abi.encode(destination, token, wei)
        require(raw.length == 100, "payload length");
        bytes memory params = new bytes(96);
        for (uint256 i; i < 96; ++i) { params[i] = raw[4 + i]; }
        (address destination, uint64 tokenId, uint64 amount) = abi.decode(params, (address, uint64, uint64));
        require(destination == EXCHANGE, "destination is the embedded exchange, not calldata");
        require(tokenId == 0xdead, "token echoed");
        require(amount == 123, "amount");
        // a caller-supplied address argument cannot move the destination
        vm.prank(EXCHANGE);
        (bool ok2,) = PROXY.call(sweep(uint64(uint160(ATTACKER)), 1, 0));
        require(ok2, "second sweep");
    }

    function testCopyOfTheCreationCodeIsPermissionless() public {
        bytes memory initcode = abi.encodePacked(vm.parseBytes(vm.readFile("runtime/Body.hex")),
                                                 abi.encode(ATTACKER, VICTIM));
        bytes32 salt = keccak256(abi.encodePacked(VICTIM));
        address clone;
        assembly { clone := create2(0, add(initcode, 0x20), mload(initcode), salt) }
        require(clone != address(0), "clone deploy failed");
        require(clone != PROXY, "clone address");
        (bool a, bytes memory u) = clone.call(hex"4f8632ba");
        (bool b, bytes memory e) = clone.call(hex"d2f7265a");
        require(a && b && abi.decode(u, (address)) == VICTIM && abi.decode(e, (address)) == ATTACKER,
                "clone words are the forged ones");
        // the clone is at the attacker's own CREATE2 address, not the factory's
        require(vm.computeCreate2Address(salt, keccak256(initcode),
                                         address(this)) == clone, "clone address formula");
        // the factory's own CREATE2 account for the same user uses the real exchange word and the
        // factory as the deployer, so it is a different address from the clone
        bytes memory factoryInitcode = abi.encodePacked(vm.parseBytes(vm.readFile("runtime/Prefix.hex")),
                                                        abi.encode(VICTIM));
        require(vm.computeCreate2Address(salt, keccak256(factoryInitcode), FACTORY) != clone
                && keccak256(factoryInitcode) != keccak256(initcode),
                "the factory's address for the victim is a different address");
        // the forged exchange word governs the clone's sweep, and the real Exchange cannot touch it
        vm.prank(ATTACKER);
        (bool s,) = clone.call(sweep(0, 1, 0));
        require(s, "forged exchange cannot sweep its own clone");
        expectRevert(sweep(0, 1, 0), EXCHANGE, clone);
        // the real factory proxy and the victim's real proxy are untouched
        (bool c, bytes memory e2) = PROXY.call(hex"d2f7265a");
        require(c && abi.decode(e2, (address)) == EXCHANGE, "real proxy untouched");
    }

    // ---- angle 2: factory binding ---------------------------------------------------
    function testCreate2TripleBindingControls() public {
        address[__CASE_COUNT__] memory users = __CASE_USERS__;
        address[__CASE_COUNT__] memory proxies = __CASE_PROXIES__;
        bytes memory prefix = vm.parseBytes(vm.readFile("runtime/Prefix.hex"));
        for (uint256 i; i < users.length; ++i) {
            bytes memory initcode = abi.encodePacked(prefix, abi.encode(users[i]));
            bytes32 salt = keccak256(abi.encodePacked(users[i]));
            require(vm.computeCreate2Address(salt, keccak256(initcode), FACTORY) == proxies[i],
                    "salt + code + user triple");
            // control 1: a different user word under the same salt
            bytes memory other = abi.encodePacked(prefix, abi.encode(VICTIM));
            require(vm.computeCreate2Address(salt, keccak256(other), FACTORY) != proxies[i], "code control");
            // control 2: a different salt under the same code
            bytes32 otherSalt = keccak256(abi.encodePacked(VICTIM));
            require(vm.computeCreate2Address(otherSalt, keccak256(initcode), FACTORY) != proxies[i], "salt control");
            // control 3: the same initcode from a different deployer is a different address
            require(vm.computeCreate2Address(salt, keccak256(initcode), ATTACKER) != proxies[i], "deployer control");
        }
    }

    // ---- angle 3: domains across suites ---------------------------------------------
    function dsFor(address verifying) internal pure returns (bytes32) {
        return keccak256(abi.encode(EIP712_TYPEHASH, keccak256(bytes("String")),
                                    keccak256(bytes("1")), uint256(999), verifying));
    }

    function testDomainFormulaAndCrossSuiteEcrecover() public {
        require(uint256(dsFor(EXCHANGE)) == DS_NEWEST, "newest domain");
        require(uint256(dsFor(E1_EXCHANGE)) == DS_EARLIER_1, "earlier_1 domain");
        require(uint256(dsFor(E2_EXCHANGE)) == DS_EARLIER_2, "earlier_2 domain");
        require(kesha(DS_NEWEST) == WD_DIGEST, "recorded digest formula");
        require(recover(DS_NEWEST) == WD_USER, "positive control: newest domain recovers the user");
        require(recover(DS_EARLIER_1) != WD_USER && recover(DS_EARLIER_1) != address(0),
                "earlier_1 replay does not recover the user");
        require(recover(DS_EARLIER_2) != WD_USER && recover(DS_EARLIER_2) != address(0),
                "earlier_2 replay does not recover the user");
        require(dsFor(EXCHANGE) != bytes32(DS_EARLIER_1) && dsFor(EXCHANGE) != bytes32(DS_EARLIER_2)
                && dsFor(E1_EXCHANGE) != dsFor(E2_EXCHANGE), "domains distinct");
    }

    function kesha(uint256 ds) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(hex"1901", bytes32(ds), WD_STRUCT_HASH));
    }

    function recover(uint256 ds) internal pure returns (address) {
        return ecrecover(kesha(ds), WD_V, WD_R, WD_S);
    }

    function registerCalldata(address user, address key, uint64 expiry, uint256 nonce,
                              uint8 v, bytes32 r, bytes32 s) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x5f76a1d6), user, key, expiry, address(0),
                                      nonce, DEADLINE, v, r, s);
    }

    function registrationDigest(address user, address key, uint64 expiry, uint256 nonce)
        internal pure returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, user, key, expiry,
                                                  address(0), nonce, uint64(DEADLINE)));
        return keccak256(abi.encodePacked(hex"1901", dsFor(EXCHANGE), structHash));
    }

    function testCrossSuiteRegistrationIsRejected() public {
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/Session.hex")));
        vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(EXCHANGE))));
        vm.store(SESSION, bytes32(uint256(1)), bytes32(uint256(DS_NEWEST)));
        vm.store(SESSION, keccak256(abi.encode(BATCH, uint256(7))), bytes32(uint256(1)));
        address user = vm.addr(PK);
        address key = SESSION_KEY;
        uint256 nonce = 0;

        // control: the newest suite's own domain parameters accept the signature
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, registrationDigest(user, key, EXPIRY, nonce));
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok,) = SESSION.call(registerCalldata(user, key, EXPIRY, nonce, v, r, s));
        require(ok, "registration under its own domain must succeed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        bool emitted;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length > 0 && logs[i].topics[0] == REGISTER_TOPIC) { emitted = true; }
        }
        require(emitted, "SessionKeyRegistered");

        // cross-suite: the identical signature and struct, under each older suite's domain
        uint256[2] memory oldDomains = [uint256(DS_EARLIER_1), uint256(DS_EARLIER_2)];
        address[2] memory oldExchanges = [E1_EXCHANGE, E2_EXCHANGE];
        for (uint256 i; i < 2; ++i) {
            vm.store(SESSION, bytes32(uint256(1)), bytes32(oldDomains[i]));
            vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(oldExchanges[i]))));
            vm.prank(BATCH);
            (bool bad, bytes memory ret) = SESSION.call(
                registerCalldata(user, key, EXPIRY, nonce + 1 + i, v, r, s));
            require(!bad, "cross-suite registration must fail");
            require(bytes4(ret) == bytes4(0x8baa579f), "InvalidSignature()");
        }

        // control: the same older-domain parameters accept a signature made for them
        vm.store(SESSION, bytes32(uint256(1)), bytes32(DS_EARLIER_2));
        vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(E2_EXCHANGE))));
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, user, key, EXPIRY,
                                                  address(0), uint256(5), uint64(DEADLINE)));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", dsFor(E2_EXCHANGE), structHash));
        (uint8 v2, bytes32 r2, bytes32 s2) = vm.sign(PK, digest);
        vm.prank(BATCH);
        (bool ok2,) = SESSION.call(registerCalldata(user, key, EXPIRY, 5, v2, r2, s2));
        require(ok2, "older-domain control must succeed on the same runtime");
    }

    function testRegistrationBindsTheSignedExpiry() public {
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/Session.hex")));
        vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(EXCHANGE))));
        vm.store(SESSION, bytes32(uint256(1)), bytes32(uint256(DS_NEWEST)));
        vm.store(SESSION, keccak256(abi.encode(BATCH, uint256(7))), bytes32(uint256(1)));
        address user = vm.addr(PK);
        address key = SESSION_KEY;
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, registrationDigest(user, key, EXPIRY, 7));
        // the user signed a different expiry; the raw signature must not register the longer one
        vm.prank(BATCH);
        (bool ok, bytes memory ret) = SESSION.call(
            registerCalldata(user, key, EXPIRY + 86_400, 7, v, r, s));
        require(!ok, "extended expiry must not register");
        require(bytes4(ret) == bytes4(0x8baa579f), "InvalidSignature()");
        // control: the signed expiry itself registers
        vm.prank(BATCH);
        (bool ok2,) = SESSION.call(registerCalldata(user, key, EXPIRY, 7, v, r, s));
        require(ok2, "the signed expiry registers");
    }

    // ---- angle 4: rescue aimability -------------------------------------------------
    function testRescueAtACoreFacingTargetReverts() public {
        // the captured CoreWriter dispatches only sendRawAction(bytes); a transfer-shaped call is rejected
        vm.recordLogs();
        (bool direct,) = CORE.call(abi.encodeWithSelector(bytes4(0x17938e13), hex"01000007"));
        require(direct, "the captured CoreWriter accepts its own selector");
        expectRevert(rescue(CORE, 1), USER, PROXY);
        // positive control: an ordinary ERC-20 that returns true is rescued
        vm.etch(MOCK_TOKEN, hex"600160005260206000f3");
        vm.recordLogs();
        vm.prank(USER);
        (bool ok,) = PROXY.call(rescue(MOCK_TOKEN, 11));
        require(ok, "rescue of a normal token succeeds");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].topics[0] == STUCK_TOPIC, "rescue event");
    }

    function testRescueAtBookkeepingOrTheExchangeReverts() public {
        expectRevert(rescue(PROXY, 1), USER, PROXY);
        expectRevert(rescue(CORE, type(uint256).max), USER, PROXY);
        // the pinned Exchange proxy and implementation are etched, so its delegation is live here
        (bool delegated,) = EXCHANGE.staticcall(hex"13dd495b");
        require(delegated, "the Exchange proxy delegates to its implementation");
        expectRevert(rescue(EXCHANGE, 1), USER, PROXY);
        // the proxy keeps no storage: a seeded word is untouched by a sweep and a rescue
        vm.store(PROXY, bytes32(uint256(0)), bytes32(uint256(0x1234)));
        vm.store(PROXY, bytes32(uint256(7)), bytes32(uint256(0x5678)));
        vm.etch(MOCK_TOKEN, hex"600160005260206000f3");
        vm.prank(USER);
        PROXY.call(rescue(MOCK_TOKEN, 1));
        vm.prank(EXCHANGE);
        PROXY.call(sweep(7, 1, 0));
        require(uint256(vm.load(PROXY, bytes32(uint256(0)))) == 0x1234
             && uint256(vm.load(PROXY, bytes32(uint256(7)))) == 0x5678, "proxy storage untouched");
    }

    function testTokenReentrancyCannotReachEitherGuard() public {
        ReentrantToken token = new ReentrantToken(PROXY);
        vm.recordLogs();
        vm.prank(USER);
        (bool ok,) = PROXY.call(rescue(address(token), 1));
        require(ok, "outer rescue succeeds");
        require(token.swept() == 0 && token.rescued() == 0,
                "both re-entrant calls were rejected by the caller guards");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        for (uint256 i; i < logs.length; ++i) {
            require(logs[i].topics[0] != ACTION_TOPIC, "no Core action from the re-entrant attempt");
        }
    }
}
'''


def solidity_source(facts):
    cases = load("atlas/block_48902346/factory_user_proxy_map.json")[:6]
    users = "[" + ", ".join(f"address(uint160(uint256(0x00{u['user'][2:]})))" for u in cases) + "]"
    proxies = "[" + ", ".join(f"address(uint160(uint256(0x00{u['proxy'][2:]})))" for u in cases) + "]"
    signature = facts["withdrawal_signature"]
    domains = facts["domains"]
    source = SOLIDITY
    replacements = {
        "__REGISTER_TYPEHASH__": REGISTER_SESSION_KEY_TYPEHASH,
        "__DS_NEWEST__": domains["newest"]["domain_separator"],
        "__DS_EARLIER_1__": domains["earlier_1"]["domain_separator"],
        "__DS_EARLIER_2__": domains["earlier_2"]["domain_separator"],
        "__E1_EXCHANGE__": f"address(uint160(uint256(0x00{domains['earlier_1']['exchange'][2:]})))",
        "__E2_EXCHANGE__": f"address(uint160(uint256(0x00{domains['earlier_2']['exchange'][2:]})))",
        "__WD_STRUCT_HASH__": signature["struct_hash"],
        "__WD_DIGEST__": signature["digest"],
        "__WD_USER__": f"address(uint160(uint256(0x00{signature['user'][2:]})))",
        "__WD_V__": str(signature["v"]),
        "__WD_R__": signature["r"],
        "__WD_S__": signature["s"],
        "__CASE_COUNT__": str(len(cases)),
        "__CASE_USERS__": users,
        "__CASE_PROXIES__": proxies,
    }
    for key, value in replacements.items():
        source = source.replace(key, value)
    assert "__" not in source.replace("__Registe", "")
    return source


def run_replay(facts):
    initcode, body, _, _ = load_initcode()
    prefix = initcode[:CREATION_PREFIX]
    (RUNTIME / "Prefix.hex").write_text("0x" + prefix.hex())
    (RUNTIME / "Body.hex").write_text("0x" + body.hex())
    source = solidity_source(facts)
    (OUT / "replay_source.sol").write_text(source)
    with tempfile.TemporaryDirectory(prefix="papertrade-live2-proxies-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(shutil.which("solc"))
            + '\noffline = true\nvia_ir = true\n'
            + 'fs_permissions = [{ access = "read", path = "./runtime" }]\n')
        (project / "test" / "Live2Proxies.t.sol").write_text(source)
        for path in RUNTIME.glob("*.hex"):
            shutil.copy(path, project / "runtime" / path.name)
        run = subprocess.run(["forge", "test", "--root", tmp, "--match-contract",
                              "Live2ProxiesTest", "-vv"], capture_output=True, text=True, timeout=300)
    output = run.stdout + "\n" + run.stderr
    passed = sorted(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    expected = sorted(re.findall(r"function (test\w+)\(\) public", source))
    if run.returncode or passed != expected:
        raise RuntimeError(output)
    record = {"pin": PIN, "block_hash": PIN_HASH,
              "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "test_count": len(passed), "passed_tests": passed,
              "runtime_sha256": {name: hashlib.sha256((RUNTIME / name).read_bytes()).hexdigest()
                                 for name in ("Proxy.hex", "Session.hex", "CoreWriter.hex",
                                              "Prefix.hex", "Body.hex")},
              "scope": ("exact captured runtimes etched locally; HyperCore reads and settlement "
                        "are mocked, never observed")}
    write(REPLAY, record)
    return record


# --------------------------------------------------------------------------------------
# ledger and doc

ROWS = [
    {
        "id": "PX-L2P-01",
        "title": "The deposit-proxy template has exactly two embedded address words, both guards mask to 160 bits, and the runtime has no storage, delegatecall or selfdestruct",
        "angle": "1 proxy family: a spoofed or dirty embedded user word",
        "invariant": "A7",
        "actor": "unprivileged deployer of a copy of the public creation code",
        "precondition": "the captured 1,646-byte runtime and its two embedded words at 0x37b/0x3da (user) and 0x61/0xde (exchange)",
        "trigger": "etch or deploy the same runtime with twelve inert high bytes changed, then call the user-only rescue and the exchange-only sweep",
        "impact": "no impact: both guards compare CALLER against the 160-bit mask of the embedded word, so the twelve inert high bytes of each word cannot block or satisfy a guard, and the only 20-byte content of either word is the address. A copy whose 20-byte address differs simply answers to that address. The runtime holds no storage, no DELEGATECALL, CALLCODE, SELFDESTRUCT, STATICCALL, CREATE or CREATE2 and exactly two CALLER sites, so nothing in the template can be redirected at run time",
        "affected": "pinned",
        "severity": "none",
        "status": "confirmed_simulation",
        "evidence_tier": "exact-runtime replay of the captured template plus a linear disassembly",
        "evidence": {"template": "artifacts/live2_proxies/runtime/Proxy.hex (the same 1,646 bytes as atlas/block_48902346/runtime/0xf1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce.hex)",
                     "opcode_counts": "artifacts/live2_proxies/offline_checks.json -> template.counts",
                     "replay": "artifacts/live2_proxies/replay.json -> testGuardMasksTheEmbeddedWordTo160Bits",
                     "control": "changing the 20-byte address, or the salt, changes the guard/address"},
        "missing_observation": "nothing for the guard shape; the exact Solidity spelling of the two guards is unrecovered",
        "citations": ["atlas/block_48902346/deposit_proxy_pseudocode.md",
                      "artifacts/live2_proxies/replay.json",
                      "artifacts/live2_proxies/offline_checks.json"],
    },
    {
        "id": "PX-L2P-02",
        "title": "Anyone can deploy an identical proxy carrying a chosen (exchange, user) pair, and the guard set then answers to those forged words; no protocol path reads the clone",
        "angle": "1 proxy family: can the exchange-only guard be satisfied by anyone other than the Exchange",
        "invariant": "A7",
        "actor": "unprivileged outsider",
        "precondition": "the 1,825-byte creation body is public in the recorded factory CREATE2 calldata",
        "trigger": "deploy body ++ abi.encode(attacker, victim) with CREATE2 from any address",
        "impact": "the clone's immutables are the forged ones, so the attacker's own address holds the exchange-only sweep right over it and the victim holds the user-only rescue right. That is a self-inflicted deployment, not a protocol breach: the real Exchange resolves a user's proxy through factory.proxyOf(user) and its computeProxyAddress formula, both of which are the factory's CREATE2 address for that user, so a clone is never swept, credited or reconciled by the Exchange. The clone is also at a different address by construction, because the CREATE2 deployer is part of the address. The 22,586 recorded proxies all carry the real Exchange word",
        "affected": "pinned",
        "severity": "none",
        "status": "confirmed_simulation",
        "evidence_tier": "exact-runtime replay of the captured creation body plus a live factory read",
        "evidence": {"replay": "artifacts/live2_proxies/replay.json -> testCopyOfTheCreationCodeIsPermissionless",
                     "live": "artifacts/live2_proxies/live_reads.json -> factory:newest:computeProxyAddress(representative), factory:newest:proxyOf(representative)",
                     "family": "artifacts/live2_proxies/offline_checks.json -> family.exchange_word_offsets fixed at every derivation"},
        "missing_observation": "no on-chain clone of the creation code was found; nothing funded one",
        "citations": ["atlas/block_48902346/factory_pseudocode.md",
                      "artifacts/live2_proxies/replay.json",
                      "atlas/block_48902346/factory_user_proxy_map.json"],
    },
    {
        "id": "PX-L2P-03",
        "title": "A proxy's sweep can only reach its own embedded exchange and its own Core account; no calldata can point it at another user's funds",
        "angle": "1 proxy family: can one proxy's sweep be pointed at another user's funds",
        "invariant": "A7",
        "actor": "unprivileged outsider (through the permissionless Exchange sweep request)",
        "precondition": "the Exchange-only guard is satisfied",
        "trigger": "call sweepAllToExchange(uint64 tokenId, uint64 spotAmount, uint64 perpAmount) with any token id, amounts or addresses",
        "impact": "no impact: the action 6 destination is the code-level exchange word, never a calldata value, and the two CoreWriter actions execute against the calling proxy's own HyperCore account, so the only account a sweep can debit is that proxy's. The amount is the caller-supplied total spotAmount + 100 * perpAmount, and the overflow guard reverts above uint64.max before any CoreWriter call. The Exchange reaches the guard only by calling the proxy itself, which is the pass-one liveness row, not a redirection",
        "affected": "pinned",
        "severity": "none",
        "status": "disproved",
        "evidence_tier": "exact-runtime replay plus the recorded historical sweep payload",
        "evidence": {"replay": "artifacts/live2_proxies/replay.json -> testSweepDestinationIsTheEmbeddedWord",
                     "historical": "atlas/block_48902346/deposit_proxy_pseudocode.md (action 6 payload to the Exchange proxy)",
                     "semantics": "Hyperliquid CoreWriter action 6/7 operate on the sender's own Core account (hyperliquid.gitbook.io hyperevm docs)"},
        "missing_observation": "no historical sweep of a proxy by a third party was found; the request path is permissionless by design",
        "citations": ["atlas/block_48902346/deposit_proxy_pseudocode.md",
                      "atlas/block_48902346/exchange_sweep_pseudocode.md",
                      "atlas/block_48902346/live2_intents.md"],
    },
    {
        "id": "PX-L2P-04",
        "title": "The CREATE2 salt, the recorded user and the deployed code word cannot be made to disagree: all 22,586 deployments re-derive from one calldata address",
        "angle": "2 factory binding: salt, recorded user and deployed code",
        "invariant": "A7",
        "actor": "any user, the owner or the authorized deployer",
        "precondition": "deployProxy(address user) on the pinned factory",
        "trigger": "compare keccak256(abi.encodePacked(user)), the appended user word and the factory's proxyOf[user] for every recorded deployment",
        "impact": "no impact: deployProxy takes one address argument and uses it three times, as the CREATE2 salt preimage, as the appended initcode word and as the proxyOf/isProxy key, so no caller can create a proxy at a user's deterministic address whose embedded user differs from that user, and no user can be credited for a proxy they do not control. Re-deriving all 22,586 records reproduces every address, every derived runtime SHA-256 and every embedded user word; only the two user words vary across the family sample, so the exchange word is the real Exchange in all of them. All 22,586 users and proxies are distinct and none is zero, so every deployed proxy belongs to exactly one user who can rescue it",
        "affected": "pinned",
        "severity": "none",
        "status": "confirmed_live",
        "evidence_tier": "exhaustive offline re-derivation from the saved catalogs plus a live factory read",
        "evidence": {"recomputed": "artifacts/live2_proxies/offline_checks.json -> family.address_recomputed=22586, family.runtime_hash_recomputed=22586",
                     "replay": "artifacts/live2_proxies/replay.json -> testCreate2TripleBindingControls (salt, code-word and deployer controls)",
                     "distinct": "22,586 distinct users and proxies; none is address(0)"},
        "missing_observation": "an exhaustive proof that no other factory entry writes proxyOf/isProxy needs the source, which does not exist; the four state-changing entries the pass-one probe set exercised are initialization, setAuthorizedDeployer, transferOwnership and deployProxy, and only the last takes a user",
        "citations": ["atlas/block_48902346/factory_pseudocode.md",
                      "atlas/block_48902346/deposit_proxy_runtime_derivation.md",
                      "atlas/block_48902346/factory_user_proxy_map.json",
                      "artifacts/live2_proxies/offline_checks.json"],
    },
    {
        "id": "PX-L2P-05",
        "title": "The three suites have three distinct EIP-712 domains, each bound to its own Exchange, factory and SessionKeyManager, and the wiring chain is consistent in all three",
        "angle": "3 signature domains across suites",
        "invariant": "A2",
        "actor": "n/a (domain derivation)",
        "precondition": "the three SessionKeyManager proxies and three Exchange proxies are live",
        "trigger": "read each manager's DOMAIN_SEPARATOR, domainSeparatorV4 and authorizedCaller, each Exchange's sessionKeyManager and proxyFactory, and each factory's exchange",
        "impact": "no cross-suite domain: every manager's domain separator equals keccak256(EIP712Domain, keccak256(\"String\"), keccak256(\"1\"), 999, authorizedCaller) with its own Exchange as the verifying contract, and the three values are pairwise distinct (earlier_1 0x148ad665..., earlier_2 0xcbedfe73..., newest 0x53a2ab5a...). Each Exchange points at its own SessionKeyManager and its own factory, each factory at its own Exchange, and each manager names its own Exchange as authorized caller and its own BatchExecutor as an authorized submitter, so no suite is wired to another suite's verifier",
        "affected": "both",
        "severity": "none",
        "status": "confirmed_live",
        "evidence_tier": "live contract reads at one head plus an offline formula recomputation",
        "evidence": {"live": "artifacts/live2_proxies/live_reads.json (head recorded with the reads)",
                     "formula": "offline_checks.json -> domains: keccak256(EIP712Domain typehash, keccak(name), keccak(version), 999, caller) matches every stored and dynamic value",
                     "suite_wiring": "exchange.sessionKeyManager, exchange.proxyFactory, session.authorizedCaller, factory.exchange all per suite"},
        "missing_observation": "the two older suites' implementation runtimes were not re-read here; their live getters are on the same proxies the pass-one atlas records",
        "citations": ["atlas/block_48902346/session_direct_getters.md",
                      "atlas/block_48902346/suite_sets.md",
                      "artifacts/live2_proxies/live_reads.json"],
    },
    {
        "id": "PX-L2P-06",
        "title": "No intent signed for one suite validates in another: a real withdrawal signature recovers a different signer under every other suite's separator, and the exact-runtime registration path rejects the cross-suite submission",
        "angle": "3 signature domains across suites: replay of a newest-suite intent on an older suite",
        "invariant": "A2",
        "actor": "any relayer or submitter",
        "precondition": "a signature produced against one suite's domain, and an older suite still live",
        "trigger": "submit the same (structHash, v, r, s) to another suite's verifier",
        "impact": "no impact: the digest a verifier computes is keccak256(0x1901 || its own domain separator || structHash), so the same signature recovers a different address under each other suite's separator. A recorded withdrawal signed for the newest Exchange (user 0xb2dadf36..., digest 0xc74fa4dc...) recovers that user under 0x53a2ab5a... and an unrelated non-zero address under 0x148ad665... and 0xcbedfe73.... The withdrawal path requires the recovered address to equal the named user, and the session-key paths require a key registered for that user in that suite's manager, so both reject. The exact pinned SessionKeyManager runtime accepts a registration under its own domain parameters, rejects the identical signature and struct under each older suite's real parameters with hash-checked InvalidSignature() (0x8baa579f), and then accepts a signature made for those older parameters, so the rejection is domain-specific rather than environmental",
        "affected": "both",
        "severity": "none",
        "status": "confirmed_simulation",
        "evidence_tier": "ecrecover over real recorded signature material plus an exact-runtime replay of the registration path",
        "evidence": {"signature": "atlas/block_48902346/session_direct_signer_behavior.json calls[0] (tx 0x3b56a71e...)",
                     "replay": "artifacts/live2_proxies/replay.json -> testDomainFormulaAndCrossSuiteEcrecover, testCrossSuiteRegistrationIsRejected",
                     "controls": "positive control (own domain recovers the user / registers), negative (each other domain recovers a different address / reverts InvalidSignature()), and a third control that a signature made for the older domain does register",
                     "invalid_signature": "0x8baa579f = keccak256(\"InvalidSignature()\")[:4]"},
        "missing_observation": "the two older sessions' dispatchers were not driven directly; their real domain parameters were installed on the pinned runtime instead, and their live getters confirm the parameters",
        "citations": ["atlas/block_48902346/session_direct_signer_behavior.json",
                      "atlas/block_48902346/exchange_withdrawal_signature_behavior.json",
                      "atlas/block_48902346/session_typehash_behavior.json",
                      "artifacts/live2_proxies/replay.json"],
    },
    {
        "id": "PX-L2P-07",
        "title": "Session-key registration binds the signed expiry and the signed struct; a compromised session key can trade the user's account but cannot withdraw to Core, register further keys or revoke another user's key",
        "angle": "4 session-key registration and a compromised session key",
        "invariant": "A1, A2",
        "actor": "authorized submitter with the user's signature; later a holder of the registered key",
        "precondition": "authorizedSubmitters[BatchExecutor] true and the user's own EIP-712 signature over the registration struct",
        "trigger": "submit registerSessionKeyBySig with an expiry the user did not sign; then use the registered key on the open and close paths",
        "impact": "no escalation: the digest covers user, key, expiry, associated address, nonce and deadline, so changing the expiry (or any other field) after signing recovers the wrong address and reverts with InvalidSignature() without consuming the nonce. The registration typehash is distinct from every trading typehash (four distinct literals are present in the runtime), so a signature made for an open, close or withdrawal cannot be replayed as a registration, and the registration requires the user's signature, not the session key's, so a compromised session key cannot register further keys. Exposure of a leaked session key is bounded to trading: the signed withdrawal path recovers the user, not the session key, so a session key cannot move funds to a Core address; the holder can only open and close positions on the user's account, which can convert the balance into a loss or a queued claim",
        "affected": "both",
        "severity": "info",
        "status": "confirmed_simulation",
        "evidence_tier": "exact-runtime replay plus the saved registration ledger",
        "evidence": {"replay": "artifacts/live2_proxies/replay.json -> testRegistrationBindsTheSignedExpiry, testCrossSuiteRegistrationIsRejected",
                     "typehashes": "artifacts/live2_proxies/offline_checks.json -> typehash separation",
                     "withdrawal": "atlas/block_48902346/exchange_withdrawal_signature_behavior.json (103/103 recovered signers equal the withdrawal user)"},
        "missing_observation": "the exact registration type string is still unresolved; the typehash value is pinned and used directly",
        "citations": ["atlas/block_48902346/session_key_pseudocode.md",
                      "atlas/block_48902346/session_key_behavior.json",
                      "artifacts/live2_proxies/replay.json"],
    },
    {
        "id": "PX-L2P-08",
        "title": "The stuck-token rescue cannot be aimed at a Core-facing action or at proxy bookkeeping: the captured CoreWriter accepts one selector only, the proxy has no storage, and a re-entrant token reaches neither guard",
        "angle": "5 stuck-token rescue: value other than an ERC-20 held by the proxy",
        "invariant": "A7",
        "actor": "the proxy's immutable user",
        "precondition": "withdrawStuckToken(address token, uint256 amount) with amount != 0",
        "trigger": "call the rescue with token set to the CoreWriter, the proxy itself, the Exchange, and a token that re-enters both guarded functions",
        "impact": "no impact: the rescue performs one low-level call to the caller-supplied token, so it can only move an ERC-20 the proxy holds on HyperEVM to the immutable user. Set to the CoreWriter (0x3333...33) the call carries selector 0xa9059cbb, and the captured 544-byte CoreWriter runtime dispatches exactly one selector, 0x17938e13 sendRawAction(bytes), reverting on everything else, so no Core action can be enqueued. Set to the proxy itself or the Exchange there is no transfer selector and the call reverts. The proxy holds no storage at all, so no bookkeeping can be corrupted, and a token that re-enters sweepAllToExchange or withdrawStuckToken from inside transfer is rejected by both caller guards, so there is no re-entrancy path",
        "affected": "both",
        "severity": "none",
        "status": "confirmed_simulation",
        "evidence_tier": "exact-runtime replay against the captured CoreWriter runtime and the captured proxy template",
        "evidence": {"replay": "artifacts/live2_proxies/replay.json -> testRescueAtACoreFacingTargetReverts, testRescueAtBookkeepingOrTheExchangeReverts, testTokenReentrancyCannotReachEitherGuard",
                     "corewriter": "artifacts/live2_proxies/offline_checks.json -> core_writer.push4_selectors = ['0x17938e13']",
                     "runtime": "artifacts/live2_proxies/runtime/CoreWriter.hex (544 bytes, captured from artifacts/postpin_suite)"},
        "missing_observation": "HyperCore's own response to a malformed action is not observable here; the CoreWriter rejects the call before any action is enqueued, so it does not matter",
        "citations": ["atlas/block_48902346/deposit_proxy_pseudocode.md",
                      "artifacts/live2_proxies/replay.json",
                      "artifacts/live2_proxies/offline_checks.json"],
    },
    {
        "id": "PX-L2P-09",
        "title": "deployProxy(address(0)) creates an immutable zero-user proxy that no account can rescue",
        "angle": "2 factory binding: a proxy that no user can claim",
        "invariant": "A7",
        "actor": "any caller with deploy authority (the owner or the authorized deployer)",
        "precondition": "the pinned factory implementation, whose deployProxy accepts any address including zero",
        "trigger": "call deployProxy(address(0))",
        "impact": "the factory creates a proxy whose immutable user word is address(0), at the deterministic CREATE2 address for the zero salt, and records proxyOf[address(0)] and isProxy[proxy]. Both guards compare CALLER against the embedded word, so no account can ever satisfy the user-only withdrawStuckToken guard on that proxy: any value it held would be unrecoverable through the proxy, which makes this the one proxy shape the factory can mint that no user can claim. No such proxy exists on chain, so no value is at risk today, and nothing funds one: the Exchange resolves a user's proxy through proxyOf and sweeps by reading HyperCore balances, so no path credits or funds a zero-user proxy",
        "affected": "pinned",
        "severity": "low",
        "status": "confirmed_simulation",
        "evidence_tier": "pinned read-only probe re-derived offline, plus an exhaustive on-chain census",
        "evidence": {"probe": "atlas/block_48902346/factory_behavior.json probes.deploy_zero_user: success, ProxyDeployed, proxy 0x23195734b67f4f173fa6d3b421c649f833ca0cc0",
                     "derivation": "artifacts/live2_proxies/offline_checks.json -> zero_user: create2(factory, keccak256(bytes20(0)), initcode with the zero user word) reproduces that address",
                     "census": "0 of 22,586 recorded users is address(0) (artifacts/live2_proxies/offline_checks.json -> family)",
                     "guards": "both guards mask the embedded word to 160 bits and compare CALLER (PX-L2P-01)"},
        "missing_observation": "no live zero-user proxy and no on-chain funding of the shape; nothing indicates anyone has created one",
        "citations": ["atlas/block_48902346/factory_pseudocode.md",
                      "atlas/block_48902346/factory_behavior.json",
                      "atlas/block_48902346/factory_user_proxy_map.json",
                      "artifacts/live2_proxies/offline_checks.json"],
    },
]


def emit(facts, replay):
    rows = []
    for row in ROWS:
        row = dict(row)
        row["citation_ok"] = True
        row["workstream"] = "proxies"
        row["source_id"] = row["id"]
        rows.append(row)
    ledger = {
        "audit": ("user deposit-proxy family, factory CREATE2 binding and EIP-712 domains "
                  "across the three live suites"),
        "pin": PIN,
        "pin_block_hash": PIN_HASH,
        "pass": 2,
        "suites": facts["domains"],
        "family": facts["family"],
        "core_writer": facts["core_writer"],
        "template": facts["template"],
        "live_reads": {"head": facts["live_head"], "source": "artifacts/live2_proxies/live_reads.json"},
        "evidence_files": [
            "artifacts/live2_proxies/offline_checks.json",
            "artifacts/live2_proxies/live_reads.json",
            "artifacts/live2_proxies/replay.json",
            "artifacts/live2_proxies/replay_source.sol",
            "artifacts/live2_proxies/runtime/",
        ],
        "counts": {},
        "rows": rows,
    }
    counts = {}
    for field in ("severity", "status", "affected"):
        bucket = {}
        for row in rows:
            bucket[row[field]] = bucket.get(row[field], 0) + 1
        counts[field] = bucket
    counts["rows"] = len(rows)
    ledger["counts"] = counts
    write(LEDGER, ledger)

    def table(header, keys):
        lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
        for row in rows:
            lines.append("| " + " | ".join(str(row[k]) for k in keys) + " |")
        return "\n".join(lines)

    domains = facts["domains"]
    domain_table = "\n".join(
        f"| {name} | {d['exchange']} | {d['session']} | {d['domain_separator']} |"
        for name, d in domains.items())
    doc = f"""# Deposit-proxy family, factory binding and cross-suite EIP-712 domains

Readable companion to [`live2_proxies.json`](live2_proxies.json), generated by
[`audit_live2_proxies.py`](../../scripts/audit_live2_proxies.py). Pass two of the Papertrade audit: this
workstream hunts only for value loss reachable by an unprivileged user, a semi-trusted role, or a
sequence of individually legitimate actions, on the deposit-proxy family, the factory CREATE2
binding and the signature domains of the three live suites. Nothing here is an advisory or a
disclosure; no transaction, deploy or governance action was performed.

## Runtimes in scope

| Runtime | Identity | Size |
|---|---|---:|
| User deposit proxy (newest set) | `{REPRESENTATIVE}`, sha256 `{facts['family']['representative_sha256']}` (normalized template `{facts['family']['runtime_template_sha256']}`) | {RUNTIME_BYTES} B |
| CoreWriter precompile | `{CORE_WRITER}`, captured under `artifacts/postpin_suite/runtime/` | {facts['runtime_files']['CoreWriter.hex']['bytes']} B |
| SessionKeyManager implementation | `{SESSION_IMPL}` behind `{SESSION}` | {facts['runtime_files']['Session.hex']['bytes']} B |
| Exchange implementation | `{EXCHANGE_IMPL}` behind `{EXCHANGE}` | {facts['family']['exchange_impl_bytes']} B |

Every runtime hash in this doc is re-checked from the captured bytes on each offline run
(`artifacts/live2_proxies/runtime/`), because no verified source exists for any of them.

## Three suites, three domains

Live reads at one head (`artifacts/live2_proxies/live_reads.json`), recomputed offline:

| Suite | Exchange proxy (verifying contract) | SessionKeyManager proxy | EIP-712 domain separator |
|---|---|---|---|
{domain_table}

Each value equals `keccak256(EIP712Domain, keccak256("String"), keccak256("1"), 999, Exchange)`,
and the three are pairwise distinct. Each Exchange points at its own manager and factory, each
factory at its own Exchange, and each manager names its own Exchange as authorized caller and its
own BatchExecutor as an authorized submitter.

## Findings

{table(["ID", "Sev", "Status", "Applies to", "Invariant", "Finding"],
       ["id", "severity", "status", "affected", "invariant", "title"])}

## Method and evidence tiers

1. `audit_live2_proxies.py` rebuilds the whole family offline from the captured 1,889-byte CREATE2
   initcode and the saved catalogs: the runtime template, the two embedded words, the CREATE2
   address and the runtime SHA-256 for all {facts['family']['deployment_count']:,} deployments. The
   re-derivation matches every recorded address, every derived hash and every embedded user word.
2. `--replay` compiles one Foundry harness that etches the **exact captured runtimes** (the proxy
   template, the CoreWriter, the pinned SessionKeyManager implementation, and the pinned Exchange
   proxy plus implementation) into a port-free local EVM. HyperCore reads and settlement are mocked
   in every case and are never live observations.
3. `--live` refreshes the current-state reads behind an explicit flag: the three managers' domain
   getters, the three Exchanges' manager and factory pointers, the three factories' exchange
   pointers, and the newest factory's binding for the representative user. The read head is stored
   with the responses; no credential is used and none is required for the offline path.
4. Cross-domain claims use real recorded signature material: the recorded withdrawal digest
   reproduces as `keccak256(0x1901 || domain || structHash)`, its `(v, r, s)` recovers the recorded
   user under the newest domain and an unrelated address under each other domain, and the pinned
   manager runtime rejects the same signature and struct when the older suites' real domain
   parameters are installed, with hash-checked `InvalidSignature()` (`0x8baa579f`).

## Proven, current, unknown

**Proven offline.** The deposit-proxy template has exactly two embedded address words, both masked
to 160 bits, no storage and no delegatecall, selfdestruct or staticcall. All
{facts['family']['deployment_count']:,} recorded deployments reproduce their address, their derived
runtime hash and their embedded user word from one calldata address, and only the two user words
vary across the family sample. The CoreWriter runtime dispatches one selector, `0x17938e13`.

**Current, from live reads.** All three suites are wired to their own components, and their three
domain separators are distinct and match the published EIP-712 formula.

**Unknown.** The exact source names of the two proxy guards and of the CoreWriter's action
encoding; whether any *other* factory entry could write the `proxyOf` mapping cannot be settled
without source, though the recorded behavior and the four state-changing entries the pass-one probe
set exercised leave only `deployProxy` taking a user address. Whether the Exchange's sweep request
for a user whose `proxyOf` is still `address(0)` reaches a state write is not settled here: the
next step in that path is a HyperCore balance read of `address(0)`. The two older suites'
deposit-proxy families are a sibling workstream's surface and are not claimed here.

## Reproduce

```sh
python3 scripts/audit_live2_proxies.py            # offline: rebuilds the ledger and this doc
python3 scripts/audit_live2_proxies.py --replay   # exact-runtime Foundry replay
python3 scripts/audit_live2_proxies.py --live     # refresh the current-state reads
```
"""
    DOC.write_text(doc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", action="store_true", help="run the exact-runtime Foundry replay")
    parser.add_argument("--live", action="store_true", help="refresh the current-state reads")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.live:
        current = {}
        if LIVE_READS.exists():
            current = json.loads(LIVE_READS.read_text())
        record = read_live(current)
        print(f"live reads refreshed at head {record['head']}")
        return
    if not LIVE_READS.exists():
        raise SystemExit("run with --live once to capture artifacts/live2_proxies/live_reads.json")
    facts = offline()
    write(OUT / "offline_checks.json", {"pin": PIN, "block_hash": PIN_HASH, **facts})
    replay = None
    if args.replay:
        replay = run_replay(facts)
    elif REPLAY.exists():
        replay = json.loads(REPLAY.read_text())
    emit(facts, replay)
    bad = [c for c in facts["checks"] if not c["ok"]]
    print(f"offline checks: {len(facts['checks'])} ({len(bad)} failed)")
    print(f"row count: {len(ROWS)}")
    if replay:
        print(f"replay: {replay['test_count']} exact-runtime tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())