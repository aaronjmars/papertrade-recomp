#!/usr/bin/env python3
"""Pricing and eligibility audit of Papertrade (HyperEVM 999): pinned suite vs contract set 2.

Angles
  A1 freshness          what a stale/frozen/self-consistent quote does to open, close, liquidation
  A2 raw vs validated   every code path that consumes raw getBBO or a snapshot instead of the midpoint
  A3 price reachability PriceOracle selectors, guards, who can write the instruments the Exchange prices
  A4 caps vs liquidity  per-side OI cap against the LP bankroll and the queue
  A5 eligibility        liquidation-price and cap boundaries in both implementations

Evidence sources (all offline):
  * exact runtime bytes: atlas/block_48902346/runtime/*.hex (pinned, hash-checked against the manifest)
    and artifacts/postpin_suite/runtime/*.hex (set 2, hash-checked against suite_sets.json)
  * the saved mixed-close prestate artifacts/exchange_negative_close/original_prestate.json
  * the 57 saved signed-open side-limit comparisons plus their BatchExecutor call trees
  * port-free Foundry replay of the exact proxy/implementation/library bytes with mocked
    HyperCore read precompiles -- every such reply is simulated and labelled.

`python3 scripts/audit_live2_pricing.py` runs offline. `--capture` refreshes the live market words.
"""

import argparse
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "live2_pricing"
LEDGER = ATLAS / "live2_pricing.json"
DOC = ATLAS / "live2_pricing.md"

RPC = "https://rpc.hyperliquid.xyz/evm"
CHAIN_ID = 999
PIN = 48902346
PIN_HASH = "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
PRESTATE_BLOCK = 48901631
PRESTATE = ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json"
LIVE_PROBES = ROOT / "artifacts" / "audit_certik_haircut" / "live" / "raw" / "storage_probes.json"
LIVE_CAPTURE = ROOT / "artifacts" / "audit_certik_haircut" / "live" / "capture.json"
MARKET_FIELDS_PROBES = ROOT / "artifacts" / "exchange_market_fields" / "pinned_probes.json"

EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
PIN_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN_LIB = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
PIN_SESSION_IMPL = "0x8a5069fe303e8f81e91825436e956d595032e558"
ORACLE = "0xa9b4c7b7ca5835652d81e25739c870d49f39cc2e"
ORACLE_IMPL = "0x3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a"
SET2_IMPL = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
SET2_LIB = "0x583d0bd818c991c5830fea93aef04e474b272459"
SET2_SESSION_IMPL = "0x04b5ea4cdd8d6de4bd6e0ef3865266947f043946"
SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
EIP1967_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

MIDPOINT = "0xc0182669"          # uint32 -> validated midpoint, rejects zero and crossed
GET_BBO = "0xfb466481"           # uint32 -> raw (bid, ask), no validation
SNAPSHOT = "0x766cd255"          # uint32 -> five-word snapshot, no validation
SNAPSHOT_ARRAY = "0xa7f06462"    # uint32[] -> five-word snapshots, no validation
ORACLE_PRICE = "0x2af78bd1"      # uint32 -> precompile 0x0807, rejects zero
MARK_PRICE = "0xa066fae9"        # uint32 -> precompile 0x0806, rejects zero
PAUSE_MARKET = "0x2d2451d1"      # uint32 -> owner/pauseGuardian, stores raw bid/ask + timestamp
UNPAUSE_MARKET = "0xfb9f1009"    # always reverts in the pinned runtime
LIQUIDATE = "0x415f1240"         # uint256 -> single-position liquidation, absent from set 2
LIQUIDATE_BATCH = "0x599dc539"   # uint256[],uint256,bool -> batch liquidation
MARKET_FIELDS = "0x628a9fd6"     # uint32,uint128,uint128 -> owner or marketKeeper side caps
INSTRUMENT_SETTER = "0x5ca4c0ea" # uint32,uint128,uint96,uint96,uint64 -> owner only
CLOSE_SELECTOR = "0x2792e706"
OPEN_SELECTOR = "0xec6783f0"
CLOSE_TYPEHASH = "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13"
CLOSE_DOMAIN = "0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77"
OPEN_TYPEHASH = "0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983"
NONCE = 42
USER = "0xe05fcc23807536bee418f142d19fa0d21bb0cff7"
CLOSED_TOPIC = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
LIQUIDATED_TOPIC = "0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8"

INSTRUMENT = 1                   # ETH market in the prestate numbering
ORACLE_ASSET = 1
ENTRY_PRICE = 250645             # 2506.45 in the venue's 0.01 price units
MARGIN = 20000 * 10 ** 18
LEVERAGE = 500
MAINT_RATE = 481304050180130     # ETH instrument word 1 bits 120..183, 1e18 fixed point
MARKET_ROOT = "0xbbbb3b1da0cb0951f34c5e9db4606f934b7367b5284f29163e9e6fe67e1e97d6"
INSTRUMENT_ROOT = "0xb39221ace053465ec3453ce2b36430bd138b997ecea25c1043da0c366812b828"
MARKET_PAUSE_SLOT = 35
TRADING_PAUSE_SLOT = 29
MARKET_FIELDS_SLOT = 36
GUARDIAN = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
MARKET_KEEPER = "0x3721476de31190dc1af8908026abe20efe25cf99"
OUTSIDER = "0x" + "11" * 20
PAUSE_SEED_BID = 300000
PAUSE_SEED_ASK = 100000
PAUSE_SEED_TIMESTAMP = 1700000000
SET_TRADING_PAUSED = "0xae69b95b"
SET_PAUSE_GUARDIAN = "0x48bde20c"
TRADING_PAUSED_GETTER = "0x53e23e2e"
PAUSE_GUARDIAN_GETTER = "0x24a3d622"
OWNER_GETTER = "0x8da5cb5b"
OPEN_PRICE = 234900              # a valid uncrossed ETH quote for the open tests
OPEN_SIZE = 5 * 10 ** 18         # margin in 1e18 units
OPEN_LEVERAGE = 100
ETH_PRICE_RAW = 234905           # last observed ETH midpoint (asset 1) in the saved open traces
BTC_PRICE_RAW = 809525           # last observed asset-0 midpoint in the saved open traces

RUNTIME_FILES = {
    PIN_IMPL: ATLAS / "runtime" / f"{PIN_IMPL}.hex",
    PIN_LIB: ATLAS / "runtime" / f"{PIN_LIB}.hex",
    ORACLE_IMPL: ATLAS / "runtime" / f"{ORACLE_IMPL}.hex",
    PIN_SESSION_IMPL: ATLAS / "runtime" / f"{PIN_SESSION_IMPL}.hex",
    SET2_IMPL: ROOT / "artifacts" / "postpin_suite" / "runtime" / f"{SET2_IMPL}.hex",
    SET2_LIB: ROOT / "artifacts" / "postpin_suite" / "runtime" / f"{SET2_LIB}.hex",
    SET2_SESSION_IMPL: ROOT / "artifacts" / "postpin_suite" / "runtime" / f"{SET2_SESSION_IMPL}.hex",
}
PUBLISHED_HASH = {
    SET2_IMPL: "fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268",
    SET2_LIB: "ced8e434ebd5379c4acc1fba809a5b18f531c676a264308c9a0a1a76d9641440",
    SET2_SESSION_IMPL: "7df05c33597c04820a314fae015aab01b5566aff53e9bded8446962cfd4ad2c9",
}


# ------------------------------------------------------------------ helpers

def sha256_hex(payload):
    return hashlib.sha256(payload).hexdigest()


def u256(value):
    return "0x" + format(value % (1 << 256), "064x")


def s_address(value):
    return "address(uint160(uint256(0x00" + value[2:] + ")))"


def load_hex(path):
    return path.read_text().strip()


def body(path):
    return bytes.fromhex(load_hex(path)[2:])


def find_selectors(code, selectors):
    """Byte offsets of every PUSH4 immediate equal to one of the given selectors."""
    found = {}
    for selector in selectors:
        raw = bytes.fromhex(selector[2:])
        offsets = []
        start = 0
        while (index := code.find(raw, start)) != -1:
            is_push4 = index > 0 and code[index - 1] == 0x63
            if is_push4:
                offsets.append(index - 1)
            start = index + 1
        found[selector] = offsets
    return found


def count_opcode(code, opcode):
    """Linear opcode census skipping PUSH immediates."""
    count = 0
    index = 0
    while index < len(code):
        op = code[index]
        if 0x60 <= op <= 0x7f:
            index += 1 + (op - 0x5f)
            continue
        if op == opcode:
            count += 1
        index += 1
    return count


def dispatch_selectors(code):
    selectors = set()
    for index in range(len(code) - 4):
        if code[index] != 0x63:
            continue
        if 0x14 in code[index + 5:index + 12]:
            selectors.add("0x" + code[index + 1:index + 5].hex())
    return selectors


def rpc(method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(RPC, data=payload, headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


def pack_instrument(words):
    return [words[0] | (words[1] << 96) | (words[2] << 192) | (words[3] << 224),
            words[4] | (words[5] << 120) | (words[6] << 184),
            words[7]]


def instrument_words(instrument):
    getters = json.loads((ROOT / "artifacts" / "exchange_instruments_getter" / "pinned_getters.json").read_text())
    row = next(row for row in getters["rows"] if row["instrument_id"] == instrument)
    raw = row["getter_output"][2:]
    return [int(raw[i:i + 64], 16) for i in range(0, len(raw), 64)]


def market_words(instrument):
    markets = json.loads(MARKET_FIELDS_PROBES.read_text())
    row = next(row for row in markets["markets"] if row["instrument"] == instrument)
    return [int(word, 16) for word in row["raw_words"]]


def live_market_words():
    live = json.loads(LIVE_PROBES.read_text())
    return [int(live["market_words"][u256(int(MARKET_ROOT, 16) + i)], 16) for i in range(2)]


# ------------------------------------------------------------------ static evidence

def runtime_evidence():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert manifest["block"] == PIN and manifest["block_hash"] == PIN_HASH
    identity = {}
    for address, path in RUNTIME_FILES.items():
        code = load_hex(path)
        digest = sha256_hex(bytes.fromhex(code[2:]))
        if address in manifest["contracts"]:
            row = manifest["contracts"][address]
            assert row["sha256"] == digest, address
            stored = (ATLAS / row["runtime_file"]).read_text().strip()
            assert stored.lower() == code.lower(), address
        else:
            assert digest == PUBLISHED_HASH[address], (address, digest)
        identity[address] = {"sha256": digest, "bytes": len(code[2:]) // 2,
                             "runtime_file": str(path.relative_to(ROOT))}
    return identity



def mapping_key_sites(code, slot, scan=400):
    """Sites where a mapping key for `slot` is derived, and the accessor that follows it.

    The idiom is the solc key construction mstore(0x20, slot) after the key is written at 0x00:
    PUSH1 <slot> PUSH1 0x20 MSTORE, then a KECCAK256 over 0x00..0x40, then the first SLOAD or
    SSTORE the linear code reaches before any control transfer. A fixed byte window is not used:
    the scan follows the key from its construction to its first accessor.
    """
    needle = bytes([0x60, slot, 0x60, 0x20, 0x52])
    sites = []
    start = 0
    while (index := code.find(needle, start)) != -1:
        cursor = index + len(needle)
        keccak_offset = None
        accessor = None
        limit = min(len(code), cursor + scan)
        while cursor < limit:
            op = code[cursor]
            if op == 0x20 and keccak_offset is None:
                keccak_offset = cursor
            elif op == 0x54 and keccak_offset is not None:
                accessor = ("SLOAD", cursor)
                break
            elif op == 0x55 and keccak_offset is not None:
                accessor = ("SSTORE", cursor)
                break
            elif op in (0x56, 0x57, 0xf1, 0xf2, 0xf4, 0xfa, 0xf0, 0xf5, 0xf3, 0xfd, 0x00):
                break
            cursor += 1 + ((op - 0x5f) if 0x60 <= op <= 0x7f else 0)
        hint = None
        cursor2 = index + len(needle)
        limit2 = min(len(code), cursor2 + scan)
        while cursor2 < limit2:
            op2 = code[cursor2]
            if op2 == 0x55:
                hint = cursor2
                break
            if op2 in (0xf3, 0xfd, 0x00):
                break
            cursor2 += 1 + ((op2 - 0x5f) if 0x60 <= op2 <= 0x7f else 0)
        sites.append({"key_idiom_offset": index, "keccak_offset": keccak_offset,
                      "accessor": accessor[0] if accessor else None,
                      "accessor_offset": accessor[1] if accessor else None,
                      "sstore_hint_offset": hint,
                      "sstore_hint_note": ("unverified hint: the nearest SSTORE inside the scan "
                                           "window, which may belong to the same key across a branch")})
        start = index + 1
    return sites


def static_evidence():
    """Price-surface read map recovered from the exact runtime bytes."""
    runtimes = {
        "pinned_exchange_implementation": body(RUNTIME_FILES[PIN_IMPL]),
        "set2_exchange_implementation": body(RUNTIME_FILES[SET2_IMPL]),
        "pinned_exchange_library": body(RUNTIME_FILES[PIN_LIB]),
        "set2_exchange_library": body(RUNTIME_FILES[SET2_LIB]),
        "oracle_implementation": body(RUNTIME_FILES[ORACLE_IMPL]),
    }
    price_selectors = [MIDPOINT, GET_BBO, SNAPSHOT, SNAPSHOT_ARRAY, ORACLE_PRICE, MARK_PRICE]
    catalogue = {}
    for directory, prefix in ((ATLAS / "runtime", ""),
                              (ROOT / "artifacts" / "postpin_suite" / "runtime", "postpin:")):
        for path in sorted(directory.glob("*.hex")):
            code = body(path)
            hits = {selector: len(offsets) for selector, offsets in
                    find_selectors(code, price_selectors).items() if offsets}
            if hits:
                catalogue[prefix + path.stem] = hits
    pinned_dispatch = dispatch_selectors(runtimes["pinned_exchange_implementation"])
    set2_dispatch = dispatch_selectors(runtimes["set2_exchange_implementation"])
    return {
        "runtime_bytes": {name: len(code) for name, code in runtimes.items()},
        "price_selector_references": {
            name: {selector: offsets for selector, offsets in
                   find_selectors(code, price_selectors).items() if offsets}
            for name, code in runtimes.items()
        },
        "catalogue": catalogue,
        "oracle_opcode_census": {
            "TIMESTAMP_0x42": count_opcode(runtimes["oracle_implementation"], 0x42),
            "NUMBER_0x43": count_opcode(runtimes["oracle_implementation"], 0x43),
            "SSTORE_0x55": count_opcode(runtimes["oracle_implementation"], 0x55),
            "DELEGATECALL_0xf4": count_opcode(runtimes["oracle_implementation"], 0xf4),
            "extract": "linear opcode census skipping PUSH data; a zero count is a hard absence",
        },
        "exchange_timestamp_opcodes": {
            "pinned": count_opcode(runtimes["pinned_exchange_implementation"], 0x42),
            "set2": count_opcode(runtimes["set2_exchange_implementation"], 0x42),
            "note": ("raw byte census, so it also counts matches inside the runtime data blob: the "
                     "pinned site at byte 22881 follows the INVALID at byte 22870 and is data, not "
                     "code. The two code sites are the position-record write at byte 2953 and the "
                     "pauseMarket snapshot at byte 12327; neither is compared against a quote age"),
        },
        "oracle_dispatch_selectors": sorted(dispatch_selectors(runtimes["oracle_implementation"])),
        "dispatch_diff": {
            "pinned_count": len(pinned_dispatch),
            "set2_count": len(set2_dispatch),
            "added": sorted(set2_dispatch - pinned_dispatch),
            "dropped": sorted(pinned_dispatch - set2_dispatch),
        },
        "price_surface_dispatch": {
            label: {"pinned": selector in pinned_dispatch, "set2": selector in set2_dispatch}
            for label, selector in (("liquidate(uint256)", LIQUIDATE),
                                    ("liquidateBatch", LIQUIDATE_BATCH),
                                    ("pauseMarket", PAUSE_MARKET),
                                    ("unpauseMarket", UNPAUSE_MARKET),
                                    ("marketFields", MARKET_FIELDS),
                                    ("instrumentSetter", INSTRUMENT_SETTER),
                                    ("signedOpen", OPEN_SELECTOR),
                                    ("signedClose", CLOSE_SELECTOR))
        },
        "mapping_key_sites": __import__("json").loads(__import__("json").dumps(
            {name: {f"slot_{slot}": mapping_key_sites(code, slot)
                    for slot in (7, 10, 22, 26, 29, MARKET_PAUSE_SLOT, MARKET_FIELDS_SLOT)}
             for name, code in runtimes.items() if "exchange" in name})),
        "sstore_total": {"pinned_exchange_implementation":
                         count_opcode(runtimes["pinned_exchange_implementation"], 0x55),
                         "set2_exchange_implementation":
                         count_opcode(runtimes["set2_exchange_implementation"], 0x55)},
        "method": ("byte scans of the exact runtime files: PUSH4 immediates for the call-site map, a "
                   "linear opcode census that skips PUSH data, the dispatcher EQ pattern for the "
                   "selector sets, and a key-construction walk from PUSH1 <slot> PUSH1 0x20 MSTORE to "
                   "the first SLOAD or SSTORE before any control transfer; no decompiler output is "
                   "promoted"),
    }


# ------------------------------------------------------------------ cap fit

def caps_fit():
    """Fit the side-exposure increment: exposure_delta = margin_1e18 * leverage * k / price_raw.

    Increments are differences of two committed (non-reverting) comparisons in one transaction, so
    the unknown stored side value cancels; each increment is paired with the midpoint the same
    transaction read from the oracle.
    """
    ledger = json.loads((ATLAS / "exchange_open_limit_full_behavior.json").read_text())
    grouped = {}
    for row in ledger["calls"]:
        grouped.setdefault(row["tx"], []).append(row)

    def walk(node, out):
        out.append(node)
        for child in node.get("calls", []):
            walk(child, out)

    fit_rows = []
    for tx, attempts in sorted(grouped.items()):
        path = ROOT / "artifacts" / "batch_executor" / f"{tx}.calls.json"
        if not path.exists():
            continue
        flat = []
        walk(json.loads(path.read_text()), flat)
        opens = []
        midpoints = {}
        for node in flat:
            data = node.get("input", "")
            if data.startswith(OPEN_SELECTOR) and node.get("to", "").lower() == EXCHANGE:
                words = [int(data[10 + i * 64:10 + (i + 1) * 64], 16) for i in range(9)]
                opens.append({"instrument": words[1], "side": words[2], "size": words[3],
                              "leverage": words[4], "reverted": bool(node.get("error"))})
            elif data.startswith(MIDPOINT) and node.get("to", "").lower() == ORACLE:
                midpoints[int(data[10:74], 16)] = int(node["output"], 16)
        committed = {}
        for attempt in sorted(attempts, key=lambda row: row["call_index"]):
            index = attempt["call_index"]
            if index >= len(opens):
                continue
            args = opens[index]
            key = (args["instrument"], args["side"])
            price = midpoints.get(args["instrument"])
            if args["reverted"] or price is None:
                continue
            updated = int(attempt["updated_exposure"])
            if key in committed:
                delta = updated - committed[key]
                size, leverage = args["size"], args["leverage"]
                if delta > 0 and size and leverage:
                    k_scaled = (delta * price * 10 ** 6) // (size * leverage)
                    fit_rows.append({
                        "tx": tx, "open_index": index, "instrument": args["instrument"],
                        "side_word": args["side"], "size_1e18": str(size), "leverage": leverage,
                        "price_raw": price, "exposure_delta": str(delta),
                        "k": k_scaled / 10 ** 6,
                        "k_scaled_ppm": str(k_scaled),
                    })
            if not attempt["exceeds_limit"]:
                committed[key] = updated
    return fit_rows


def caps_section():
    fit_rows = caps_fit()
    by_instrument = {}
    for row in fit_rows:
        by_instrument.setdefault(row["instrument"], []).append(row)
    instruments = {}
    for instrument, rows_ in sorted(by_instrument.items()):
        ks = {row["k"] for row in rows_}
        assert len(ks) == 1, (instrument, ks)
        k = ks.pop()
        residual = max(abs(int(row["exposure_delta"]) -
                           (int(row["size_1e18"]) * row["leverage"] * int(round(k))) // row["price_raw"])
                       for row in rows_)
        instruments[str(instrument)] = {
            "increments_measured": len(rows_),
            "distinct_prices": sorted({row["price_raw"] for row in rows_}),
            "k": k,
            "model": "exposure_delta = margin_1e18 * leverage * k / price_raw",
            "max_residual_units": residual,
            "examples": rows_[:2],
        }
    pinned_caps = {}
    for instrument in (0, INSTRUMENT):
        words = market_words(instrument)
        pinned_caps[str(instrument)] = {
            "long_cap_128": words[1] & ((1 << 128) - 1),
            "short_cap_128": words[1] >> 128,
            "current_long_96": words[0] & ((1 << 96) - 1),
            "current_short_96": (words[0] >> 96) & ((1 << 96) - 1),
            "word0_last64": words[0] >> 192,
        }
    live = live_market_words()
    live_caps = {
        "instrument": INSTRUMENT,
        "long_cap_128": live[1] & ((1 << 128) - 1),
        "short_cap_128": live[1] >> 128,
        "current_long_96": live[0] & ((1 << 96) - 1),
        "current_short_96": (live[0] >> 96) & ((1 << 96) - 1),
        "word0_last64": live[0] >> 192,
        "head_block": json.loads(LIVE_CAPTURE.read_text())["head_block"],
    }
    # The fitted k equals the instrument's word0 last-64 field in both markets, so the scale term
    # is that integer field and every conversion below is exact integer arithmetic.
    conversions = {}
    for instrument, price in ((0, BTC_PRICE_RAW), (INSTRUMENT, ETH_PRICE_RAW)):
        measured_k = instruments[str(instrument)]["k"]
        caps = live_caps if instrument == INSTRUMENT else pinned_caps[str(instrument)]
        scale = caps["word0_last64"]
        assert abs(measured_k - scale) < 1e-4, (instrument, measured_k, scale)
        label = "live" if instrument == INSTRUMENT else "pinned"
        conversions[str(instrument)] = {
            "scale_word0_last64": scale,
            "measured_k": measured_k,
            "price_raw_used": price,
            "caps_basis": label,
            "exposure_unit": "base-asset quantity scaled by last64/100",
            "max_single_position_notional_1e18": {
                "long": str(caps["long_cap_128"] * price // scale),
                "short": str(caps["short_cap_128"] * price // scale),
            },
            "max_single_position_notional_usdc": {
                "long": caps["long_cap_128"] * price // scale // 10 ** 18,
                "short": caps["short_cap_128"] * price // scale // 10 ** 18,
            },
        }
    headroom = {}
    for label, caps in (("pinned_eth", pinned_caps[str(INSTRUMENT)]), ("live_eth", live_caps)):
        scale = caps["word0_last64"]
        for side, cap_key in (("long", "long_cap_128"), ("short", "short_cap_128")):
            current = caps["current_long_96"] if side == "long" else caps["current_short_96"]
            gap = caps[cap_key] - current
            if gap < 0:
                gap = 0
            headroom[f"{label}_{side}"] = {
                "gap_exposure": str(gap),
                "gap_base_quantity_1e18": str(gap * 100 // scale),
                "gap_usdc_at_last_price": gap * 100 // scale * ETH_PRICE_RAW // 100 // 10 ** 18,
            }
    bankroll = json.loads((ATLAS / "asymmetric_impact_behavior.json").read_text())["bounds"]["lp_bankroll"]
    return {"fit_rows": fit_rows, "instruments": instruments, "pinned_caps": pinned_caps,
            "live_caps": live_caps, "conversions": conversions,
            "doc_headroom_claim": headroom, "lp_bankroll": bankroll}


# ------------------------------------------------------------------ forge harness

SOLIDITY_SOURCE = r'''// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function warp(uint256) external;
    function roll(uint256) external;
    function chainId(uint256) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function sign(uint256, bytes32) external returns (uint8, bytes32, bytes32);
    function addr(uint256) external returns (address);
    function writeLine(string calldata, string calldata) external;
}

contract PricingAuditTest {
    error Unexpected(bytes result);
    error ControlFailed(string label, bytes result);

    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = @EXCHANGE@;
    address constant ORACLE = @ORACLE@;
    address constant SESSION = @SESSION@;
    address constant BATCH = @BATCH@;
    address constant OWNER = @OWNER@;
    address constant USER = @USER@;
    bytes32 constant CLOSE_TYPEHASH = @TYPEHASH@;
    bytes32 constant OPEN_TYPEHASH = @OPEN_TYPEHASH@;
    bytes32 constant MARKET_BASE = @MARKET_ROOT@;
    bytes32 constant DOMAIN = @DOMAIN@;
    bytes32 constant CLOSED_TOPIC = @CLOSED_TOPIC@;
    bytes32 constant LIQUIDATED_TOPIC = @LIQUIDATED_TOPIC@;
    uint256 constant INST = @INSTRUMENT@;
    uint256 constant ASSET = @ASSET@;
    uint256 constant ENTRY = @ENTRY@;
    uint256 constant MARGIN = @MARGIN@;
    uint256 constant LEV = @LEVERAGE@;
    uint256 constant MAINT = @MAINT@;
    uint256 constant EXIT_GOOD = @EXIT_GOOD@;
    uint256 constant FROZEN_FAR = @FROZEN_FAR@;
    uint256 constant EXIT_SMALL = @EXIT_SMALL@;
    uint256 constant PAUSE_BID = @PAUSE_BID@;
    uint256 constant PAUSE_ASK = @PAUSE_ASK@;
    uint256 constant OPEN_PRICE = @OPEN_PRICE@;
    uint256 constant OPEN_SIZE = @OPEN_SIZE@;
    uint256 constant OPEN_LEV = @OPEN_LEV@;

    function setUp() public {
@SETUP@
    }

    function u2s(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 t = v;
        uint256 d;
        while (t != 0) { d++; t /= 10; }
        bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }

    function i2s(int256 v) internal pure returns (string memory) {
        if (v < 0) return string.concat("-", u2s(uint256(-v)));
        return u2s(uint256(v));
    }

    function toHex(bytes memory data) internal pure returns (string memory) {
        bytes memory alphabet = "0123456789abcdef";
        bytes memory out = new bytes(2 + data.length * 2);
        out[0] = "0";
        out[1] = "x";
        for (uint256 i; i < data.length; ++i) {
            out[2 + i * 2] = alphabet[uint8(data[i] >> 4)];
            out[3 + i * 2] = alphabet[uint8(data[i] & 0x0f)];
        }
        return string(out);
    }

    function positionSlot(uint256 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(10)));
    }

    function pauseSlot(uint256 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(@PAUSE_SLOT@)));
    }

    function balanceSlot() internal view returns (bytes32) {
        return keccak256(abi.encode(USER, uint256(9)));
    }

    function mockBbo(uint64 bid, uint64 ask) internal {
        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(ASSET)),
                    abi.encode(uint256(bid), uint256(ask)));
    }

    function writeLong(uint256 id, uint256 margin) internal {
        uint256 word0 = (ENTRY << 192) | (INST << 160) | uint256(uint160(USER));
        uint256 word1 = margin | (LEV << 128) |
            (uint256(block.timestamp & type(uint64).max) << 160) |
            (uint256(1) << 240) | (uint256(1) << 224);
        bytes32 slot = positionSlot(id);
        vm.store(EXCHANGE, slot, bytes32(word0));
        vm.store(EXCHANGE, bytes32(uint256(slot) + 1), bytes32(word1));
        uint256 packed = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        uint256 locked = (packed >> 128) + margin;
        vm.store(EXCHANGE, bytes32(uint256(22)), bytes32((locked << 128) | uint128(packed)));
    }

    function liquidationPrice() internal pure returns (uint256) {
        uint256 base = ENTRY - (ENTRY / LEV);
        return base + (base * MAINT / 1e18);
    }

    function closeBySignature(uint256[] memory ids) internal returns (bool ok, bytes memory result) {
        address sessionKey = vm.addr(0xb0b);
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(sessionKey, outer)),
                 bytes32(uint256(block.timestamp + 3600)));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), @NONCE@, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xb0b, digest);
        require(ecrecover(digest, v, r, sigS) == sessionKey, "session signer");
        vm.prank(BATCH);
        (ok, result) = EXCHANGE.call(abi.encodeWithSelector(
            @CLOSE_SELECTOR@, USER, ids, @NONCE@, deadline, v, r, sigS));
    }

    function openSigned(uint256 size, uint256 leverage, bool isLong, uint64 nonce, uint256 idUsed)
        internal returns (bool ok, bytes memory result)
    {
        address sessionKey = vm.addr(0xb0b);
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(sessionKey, outer)),
                 bytes32(uint256(block.timestamp + 3600)));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(INST), isLong,
            uint128(size), uint32(leverage), false, nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xb0b, digest);
        require(ecrecover(digest, v, r, sigS) == sessionKey, "session signer");
        vm.prank(BATCH);
        (ok, result) = EXCHANGE.call(abi.encodeWithSelector(@OPEN_SELECTOR@, USER, uint32(INST),
            isLong, uint128(size), uint32(leverage), false, nonce, deadline, v, r, sigS));
        idUsed = idUsed;
    }

    function setCaps(uint256 longCap, uint256 shortCap) internal {
        vm.store(EXCHANGE, bytes32(uint256(MARKET_BASE) + 1),
                 bytes32((longCap & type(uint128).max) | ((shortCap & type(uint128).max) << 128)));
    }

    function longExposure() internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, MARKET_BASE)) & ((uint256(1) << 96) - 1);
    }

    function closedEvent(Vm.Log[] memory logs) internal pure returns (int256 exitPrice, int256 payout) {
        uint256 found;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length == 0 || logs[i].topics[0] != CLOSED_TOPIC) continue;
            (uint256 eventExit, , int256 adjusted, , ) =
                abi.decode(logs[i].data, (uint256, int256, int256, uint256, uint256));
            require(found == 0, "one close event");
            exitPrice = int256(eventExit);
            payout = adjusted;
            found = 1;
        }
        require(found == 1, "close event present");
    }

    function flag(bool value) internal pure returns (int256) {
        return value ? int256(1) : int256(0);
    }

    function report(string memory label, int256 a, int256 b, int256 c, string memory note) internal {
        vm.writeLine("results/observed.csv",
                     string.concat(label, ",", i2s(a), ",", i2s(b), ",", i2s(c), ",", note));
    }

    function one(uint256 id) internal pure returns (uint256[] memory ids) {
        ids = new uint256[](1);
        ids[0] = id;
    }

    function deltas(uint256 balanceBefore, uint256 queuedBefore)
        internal view returns (int256 balanceDelta, int256 queueDelta)
    {
        balanceDelta = int256(uint256(vm.load(EXCHANGE, balanceSlot()))) - int256(balanceBefore);
        queueDelta = int256(uint256(vm.load(EXCHANGE, bytes32(uint256(18))))) - int256(queuedBefore);
    }

    // A. control: a live, valid uncrossed quote settles at floor((bid+ask)/2)
    function testA_close_live_valid() public {
        mockBbo(uint64(EXIT_GOOD - 5), uint64(EXIT_GOOD + 5));
        writeLong(1, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(1));
        if (!ok) revert ControlFailed("close_live_valid", result);
        (int256 exitPrice, int256 payout) = closedEvent(vm.getRecordedLogs());
        if (exitPrice != int256(EXIT_GOOD)) revert ControlFailed("exit price", result);
        report("close_live_valid", exitPrice, payout, 0, "control");
    }

    // B. negative control: a crossed book must revert with no committed log
    function testB_close_crossed_reverts() public {
        mockBbo(uint64(EXIT_GOOD + 10), uint64(EXIT_GOOD - 10));
        writeLong(1, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(1));
        if (ok) revert Unexpected(result);
        if (vm.getRecordedLogs().length != 0) revert Unexpected(result);
        report("close_crossed_reverts", 0, 0, 0, string.concat("revert=", toHex(result)));
    }

    // C. negative control: a zero book must revert with no committed log
    function testC_close_zero_reverts() public {
        mockBbo(0, 0);
        writeLong(1, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(1));
        if (ok) revert Unexpected(result);
        if (vm.getRecordedLogs().length != 0) revert Unexpected(result);
        report("close_zero_reverts", 0, 0, 0, string.concat("revert=", toHex(result)));
    }

    // D. A1: a frozen self-consistent far quote settles the close at that price
    function testD_close_frozen_far_settles() public {
        mockBbo(uint64(FROZEN_FAR), uint64(FROZEN_FAR));
        writeLong(1, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(1));
        if (!ok) revert ControlFailed("close_frozen_far", result);
        (int256 exitPrice, int256 payout) = closedEvent(vm.getRecordedLogs());
        if (exitPrice != int256(FROZEN_FAR)) revert ControlFailed("frozen exit", result);
        report("close_frozen_far", exitPrice, payout, 0,
               string.concat("balanceDelta=", i2s(int256(uint256(vm.load(EXCHANGE, balanceSlot()))))));
    }

    // E. A1: the same frozen quote still settles 5,000 blocks and two days later
    function testE_close_frozen_next_block() public {
        mockBbo(uint64(FROZEN_FAR), uint64(FROZEN_FAR));
        writeLong(1, MARGIN);
        vm.roll(block.number + 5000);
        vm.warp(block.timestamp + 2 days);
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(1));
        if (!ok) revert ControlFailed("close_frozen_next_block", result);
        (int256 exitPrice, int256 payout) = closedEvent(vm.getRecordedLogs());
        if (exitPrice != int256(FROZEN_FAR)) revert ControlFailed("stale exit", result);
        report("close_frozen_next_block", exitPrice, payout, 0, "no freshness gate");
    }

    // F/G/H. single-position liquidation at the exact boundary, one unit over, and at a valid price
    function testF_liquidate_boundary_exact() public {
        uint256 boundary = liquidationPrice();
        mockBbo(uint64(boundary), uint64(boundary));
        writeLong(7, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) =
            EXCHANGE.call(abi.encodeWithSelector(@LIQUIDATE@, uint256(7)));
        uint256 cleared = 0;
        if (ok) {
            cleared = 1 - ((uint256(vm.load(EXCHANGE, bytes32(uint256(positionSlot(7)) + 1))) >> 240) & 1);
        }
        report("liquidate_boundary_exact", flag(ok), int256(cleared), int256(boundary),
               string.concat(ok ? "outcome=ok cleared=" : "outcome=revert data=", toHex(result)));
    }

    function testG_liquidate_boundary_plus_one() public {
        uint256 boundary = liquidationPrice() + 1;
        mockBbo(uint64(boundary), uint64(boundary));
        writeLong(8, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) =
            EXCHANGE.call(abi.encodeWithSelector(@LIQUIDATE@, uint256(8)));
        report("liquidate_boundary_plus_one", flag(ok), 0, int256(boundary),
               string.concat(ok ? "outcome=ok" : "outcome=revert data=", toHex(result)));
    }

    function testH_liquidate_valid_price() public {
        mockBbo(uint64(EXIT_GOOD), uint64(EXIT_GOOD));
        writeLong(9, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) =
            EXCHANGE.call(abi.encodeWithSelector(@LIQUIDATE@, uint256(9)));
        report("liquidate_valid_price", flag(ok), 0, int256(EXIT_GOOD),
               string.concat(ok ? "outcome=ok" : "outcome=revert data=", toHex(result)));
    }

    // I. control: the batch path settles at the same boundary price
    function testI_batch_boundary() public {
        uint256 boundary = liquidationPrice();
        mockBbo(uint64(boundary), uint64(boundary));
        writeLong(10, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = EXCHANGE.call(abi.encodeWithSelector(
            @LIQUIDATE_BATCH@, one(10), uint256(1), false));
        if (!ok) revert ControlFailed("batch_boundary", result);
        if (((uint256(vm.load(EXCHANGE, bytes32(uint256(positionSlot(10)) + 1))) >> 240) & 1) != 0)
            revert ControlFailed("batch position still active", result);
        report("batch_boundary", 1, 1, int256(boundary), "control");
    }

    // J. A1/A2: pauseMarket freezes a crossed raw BBO, then prices liquidations from it
    function testJ_pause_crossed_freezes_crossed_price() public {
        mockBbo(uint64(PAUSE_BID), uint64(PAUSE_ASK));
        vm.prank(OWNER);
        (bool paused, bytes memory pauseResult) =
            EXCHANGE.call(abi.encodeWithSelector(@PAUSE_MARKET@, INST));
        if (!paused) revert ControlFailed("pause crossed", pauseResult);
        uint256 word = uint256(vm.load(EXCHANGE, pauseSlot(INST)));
        uint256 storedBid = (word >> 8) & type(uint64).max;
        uint256 storedAsk = (word >> 72) & type(uint64).max;
        if ((word & 0xff) != 1 || storedBid != PAUSE_BID || storedAsk != PAUSE_ASK)
            revert ControlFailed("crossed snapshot", pauseResult);
        // Phase 2: the live book is now valid and far from the frozen snapshot.
        mockBbo(uint64(EXIT_GOOD), uint64(EXIT_GOOD));
        writeLong(11, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = EXCHANGE.call(abi.encodeWithSelector(
            @LIQUIDATE_BATCH@, one(11), uint256(1), false));
        string memory note = string.concat("phase2=", ok ? "ok" : string.concat("revert ", toHex(result)));
        note = string.concat(note, " liveMock=", u2s(EXIT_GOOD), " frozenMid=", u2s((storedBid + storedAsk) / 2));
        note = string.concat(note, " log=", liquidatedLog(vm.getRecordedLogs()));
        // Phase 3: with the oracle replaced by a reverting runtime, a fresh liquidation still runs.
        vm.etch(ORACLE, hex"60006000fd");
        writeLong(16, MARGIN);
        vm.recordLogs();
        (bool ok3, bytes memory result3) = EXCHANGE.call(abi.encodeWithSelector(
            @LIQUIDATE_BATCH@, one(16), uint256(1), false));
        note = string.concat(note, " phase3=", ok3 ? "ok" : string.concat("revert ", toHex(result3)));
        report("pause_crossed_liquidates_at_frozen", int256((storedBid + storedAsk) / 2), int256(EXIT_GOOD), 0, note);
    }

    function liquidatedLog(Vm.Log[] memory logs) internal pure returns (string memory) {
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length > 0 && logs[i].topics[0] == LIQUIDATED_TOPIC)
                return toHex(logs[i].data);
        }
        return "none";
    }

    // K. A2: pauseMarket also freezes a zero book, which the midpoint selector would reject
    function testK_pause_zero_freezes_zero_price() public {
        mockBbo(0, 0);
        vm.prank(OWNER);
        (bool paused, bytes memory pauseResult) =
            EXCHANGE.call(abi.encodeWithSelector(@PAUSE_MARKET@, INST));
        if (!paused) revert ControlFailed("pause zero", pauseResult);
        uint256 word = uint256(vm.load(EXCHANGE, pauseSlot(INST)));
        if ((word & 0xff) != 1) revert ControlFailed("zero snapshot flag", pauseResult);
        mockBbo(uint64(EXIT_GOOD), uint64(EXIT_GOOD));
        writeLong(12, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = EXCHANGE.call(abi.encodeWithSelector(
            @LIQUIDATE_BATCH@, one(12), uint256(1), false));
        report("pause_zero_snapshot", flag(ok), int256(word & 0xff), 0,
               string.concat(ok ? "phase2=ok" : string.concat("phase2=revert ", toHex(result)),
                             " frozenWord=", u2s(word), " log=", liquidatedLog(vm.getRecordedLogs())));
    }

    // L. does a close succeed while the market is paused?
    function testL_paused_close() public {
        mockBbo(uint64(EXIT_GOOD), uint64(EXIT_GOOD));
        vm.prank(OWNER);
        EXCHANGE.call(abi.encodeWithSelector(@PAUSE_MARKET@, INST));
        writeLong(13, MARGIN);
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(13));
        report("paused_close", flag(ok), 0, 0,
               string.concat(ok ? "outcome=ok" : "outcome=revert data=", toHex(result)));
    }

    // M. control: unpauseMarket is a permanent revert
    function testM_unpause_reverts() public {
        vm.prank(OWNER);
        (bool ok, bytes memory result) =
            EXCHANGE.call(abi.encodeWithSelector(@UNPAUSE_MARKET@, INST));
        report("unpause", flag(ok), 0, 0,
               string.concat(ok ? "outcome=ok" : "outcome=revert data=", toHex(result)));
    }

    // N. A4: a payout above the lp bankroll is deferred into the queue
    function testN_queue_defers_large_payout() public {
        mockBbo(uint64(FROZEN_FAR), uint64(FROZEN_FAR));
        writeLong(14, MARGIN);
        uint256 balanceBefore = uint256(vm.load(EXCHANGE, balanceSlot()));
        uint256 queuedBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(18))));
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(14));
        if (!ok) revert ControlFailed("queue large", result);
        (int256 exitPrice, int256 payout) = closedEvent(vm.getRecordedLogs());
        (int256 balanceDelta, int256 queueDelta) = deltas(balanceBefore, queuedBefore);
        if (queueDelta <= 0) revert ControlFailed("expected a queue deferral", result);
        report("queue_defers_large_payout", exitPrice, payout, queueDelta,
               string.concat("balanceDelta=", i2s(balanceDelta)));
    }

    // O. control for N: a small payout is credited directly with no queue entry
    function testO_small_payout_paid_direct() public {
        mockBbo(uint64(EXIT_SMALL - 5), uint64(EXIT_SMALL + 5));
        writeLong(15, MARGIN);
        uint256 balanceBefore = uint256(vm.load(EXCHANGE, balanceSlot()));
        uint256 queuedBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(18))));
        vm.recordLogs();
        (bool ok, bytes memory result) = closeBySignature(one(15));
        if (!ok) revert ControlFailed("small payout", result);
        (int256 exitPrice, int256 payout) = closedEvent(vm.getRecordedLogs());
        (int256 balanceDelta, int256 queueDelta) = deltas(balanceBefore, queuedBefore);
        if (queueDelta != 0 || balanceDelta <= 0) revert ControlFailed("control failed", result);
        report("small_payout_paid_direct", exitPrice, payout, queueDelta,
               string.concat("balanceDelta=", i2s(balanceDelta)));
    }

    // P. a signed open probe: the pause gate is the first check the open path reaches
    function testP_open_live_valid() public {
        mockBbo(uint64(OPEN_PRICE), uint64(OPEN_PRICE));
        uint256 before = longExposure();
        setCaps(type(uint128).max / 2, type(uint128).max / 2);
        (bool ok, bytes memory result) = openSigned(OPEN_SIZE, OPEN_LEV, true, 900, 0);
        uint256 increment = longExposure() - before;
        report("open_live_probe", flag(ok), int256(increment), int256(OPEN_PRICE),
               string.concat(ok ? "outcome=ok increment=" : "outcome=revert data=", toHex(result)));
    }

    // Q. the paused market refuses new opens with MarketIsPaused()
    function testQ_open_paused() public {
        mockBbo(uint64(OPEN_PRICE), uint64(OPEN_PRICE));
        vm.prank(OWNER);
        EXCHANGE.call(abi.encodeWithSelector(@PAUSE_MARKET@, INST));
        setCaps(type(uint128).max / 2, type(uint128).max / 2);
        (bool ok, bytes memory result) = openSigned(OPEN_SIZE, OPEN_LEV, true, 901, 0);
        report("open_paused", flag(ok), 0, 0,
               string.concat(ok ? "outcome=ok" : "outcome=revert data=", toHex(result)));
    }
}
'''


def render_source(variant):
    tokens = {
        "@EXCHANGE@": s_address(EXCHANGE), "@ORACLE@": s_address(ORACLE),
        "@SESSION@": s_address(SESSION), "@BATCH@": s_address(BATCH),
        "@OWNER@": s_address(OWNER), "@USER@": s_address(USER),
        "@TYPEHASH@": CLOSE_TYPEHASH, "@DOMAIN@": CLOSE_DOMAIN,
        "@OPEN_TYPEHASH@": OPEN_TYPEHASH,
        "@MARKET_ROOT@": "bytes32(uint256(0x" + MARKET_ROOT[2:] + "))",
        "@CLOSED_TOPIC@": CLOSED_TOPIC, "@LIQUIDATED_TOPIC@": LIQUIDATED_TOPIC,
        "@INSTRUMENT@": str(INSTRUMENT),
        "@ASSET@": str(ORACLE_ASSET), "@ENTRY@": str(ENTRY_PRICE), "@MARGIN@": str(MARGIN),
        "@LEVERAGE@": str(LEVERAGE), "@MAINT@": str(MAINT_RATE),
        "@EXIT_GOOD@": str(variant["exit_good"]), "@FROZEN_FAR@": str(variant["frozen_far"]),
        "@EXIT_SMALL@": str(variant["exit_small"]), "@PAUSE_BID@": str(variant["pause_bid"]),
        "@PAUSE_ASK@": str(variant["pause_ask"]), "@NONCE@": str(NONCE),
        "@OPEN_SELECTOR@": "bytes4(0x" + OPEN_SELECTOR[2:] + ")",
        "@PAUSE_SLOT@": str(MARKET_PAUSE_SLOT),
        "@OPEN_PRICE@": str(OPEN_PRICE), "@OPEN_SIZE@": str(OPEN_SIZE),
        "@OPEN_LEV@": str(OPEN_LEVERAGE),
        "@CLOSE_SELECTOR@": "bytes4(0x" + CLOSE_SELECTOR[2:] + ")",
        "@LIQUIDATE@": "bytes4(0x" + LIQUIDATE[2:] + ")",
        "@LIQUIDATE_BATCH@": "bytes4(0x" + LIQUIDATE_BATCH[2:] + ")",
        "@PAUSE_MARKET@": "bytes4(0x" + PAUSE_MARKET[2:] + ")",
        "@UNPAUSE_MARKET@": "bytes4(0x" + UNPAUSE_MARKET[2:] + ")",
        "@SETUP@": variant["setup"],
    }
    source = SOLIDITY_SOURCE
    for token, value in tokens.items():
        assert token in source, token
        source = source.replace(token, value)
    return source


def build_project(variant, prestate):
    codes = {address: row.get("code", "0x") for address, row in prestate.items()}
    codes.update(variant["extra_code"])
    lines = [f"        vm.chainId({CHAIN_ID});"]
    for address, row in sorted(prestate.items(), key=lambda item: item[0].lower()):
        if codes[address] != "0x":
            lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes('
                         f'vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items(), key=lambda item: int(item[0], 16)):
            if int(value, 16):
                lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    for address in sorted(variant["extra_code"], key=str.lower):
        if codes[address] != "0x" and address not in prestate:
            lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes('
                         f'vm.readFile("runtime/{address[2:]}.hex")));')
    lines.append(f"        vm.store({s_address(EXCHANGE)}, {EIP1967_SLOT}, "
                 f"{u256(int(variant['implementation'], 16))});")
    # The saved prestate is a transaction-accessed state diff, so slot 0 (owner plus the
    # initialized low byte) is not in it; the pinned Exchange owner is the newest timelock.
    lines.append(f"        vm.store({s_address(EXCHANGE)}, bytes32(0), "
                 f"{u256((int(OWNER, 16) << 16) | 1)});")
    if variant.get("session_implementation"):
        lines.append(f"        vm.store({s_address(SESSION)}, {EIP1967_SLOT}, "
                     f"{u256(int(variant['session_implementation'], 16))});")
    for index, word in enumerate(variant["instrument_words"]):
        lines.append(f"        vm.store({s_address(EXCHANGE)}, "
                     f"{u256(int(INSTRUMENT_ROOT, 16) + index)}, {u256(word)});")
    for index, word in enumerate(variant["market_words"]):
        lines.append(f"        vm.store({s_address(EXCHANGE)}, "
                     f"{u256(int(MARKET_ROOT, 16) + index)}, {u256(word)});")
    variant = dict(variant, setup="\n".join(lines))
    return render_source(variant), codes, variant["setup"]


TESTS = ["testA_close_live_valid", "testB_close_crossed_reverts", "testC_close_zero_reverts",
         "testD_close_frozen_far_settles", "testE_close_frozen_next_block",
         "testF_liquidate_boundary_exact", "testG_liquidate_boundary_plus_one",
         "testH_liquidate_valid_price", "testI_batch_boundary",
         "testJ_pause_crossed_freezes_crossed_price", "testK_pause_zero_freezes_zero_price",
         "testL_paused_close", "testM_unpause_reverts", "testN_queue_defers_large_payout",
         "testO_small_payout_paid_direct", "testP_open_live_valid", "testQ_open_paused"]


def run_forge(tag, variant, prestate):
    source, codes, setup = build_project(variant, prestate)
    assert shutil.which("forge") and shutil.which("solc"), "forge and solc are required"
    with tempfile.TemporaryDirectory(prefix=f"papertrade-pricing-{tag}-") as tmp:
        project = pathlib.Path(tmp)
        for name in ("test", "runtime", "results"):
            (project / name).mkdir()
        (project / "results" / "observed.csv").write_text("")
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(shutil.which("solc")) +
            "\noffline = true\nvia_ir = true\noptimizer = true\noptimizer_runs = 200\n"
            'fs_permissions = [{ access = "read", path = "./runtime" }, '
            '{ access = "read-write", path = "./results" }]\n')
        (project / "test" / "PricingAudit.t.sol").write_text(source)
        for address, code in codes.items():
            if code != "0x":
                (project / "runtime" / f"{address[2:]}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                             check=False, capture_output=True, text=True, timeout=900)
        output = run.stdout + "\n" + run.stderr
        observed = (project / "results" / "observed.csv").read_text()
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    failed = set(re.findall(r"\[FAIL(?::[^\]]*)?\] (test\w+)\(\)", output))
    if run.returncode or failed or passed != set(TESTS):
        raise RuntimeError(f"{tag} replay failed:\n" + output[-14000:])
    rows = {}
    for line in sorted(observed.splitlines()):
        if line.strip():
            label, a, b, c, note = line.split(",", 4)
            rows[label] = {"a": int(a), "b": int(b), "c": int(c), "note": note}
    return {"source_sha256": sha256_hex(source.encode()), "tests": sorted(passed),
            "observed": rows, "forge_result": f"{len(passed)} passed, 0 failed",
            "setup_operations": setup.count("vm.store") + setup.count("vm.etch")}


def forge_evidence():
    prestate = json.loads(PRESTATE.read_text())
    common = {
        "exit_good": 250700, "frozen_far": 501290, "exit_small": 250705,
        "pause_bid": 300000, "pause_ask": 100000,
        "instrument_words": pack_instrument(instrument_words(INSTRUMENT)),
        "market_words": market_words(INSTRUMENT),
    }
    variants = {
        "pinned": {**common, "implementation": PIN_IMPL, "extra_code": {}},
        "set2": {**common, "implementation": SET2_IMPL,
                 "extra_code": {SET2_IMPL: load_hex(RUNTIME_FILES[SET2_IMPL]),
                                SET2_LIB: load_hex(RUNTIME_FILES[SET2_LIB]),
                                SET2_SESSION_IMPL: load_hex(RUNTIME_FILES[SET2_SESSION_IMPL])},
                 "session_implementation": SET2_SESSION_IMPL},
    }
    result = {tag: run_forge(tag, variant, prestate) for tag, variant in variants.items()}
    pinned, set2 = result["pinned"]["observed"], result["set2"]["observed"]
    # Controls that must hold on both runtimes: the crossed and zero books must reject, the
    # midpoint must settle, the frozen snapshot must price, and the queue split must appear.
    for observed in (pinned, set2):
        assert observed["close_live_valid"]["a"] == 250700
        assert observed["close_crossed_reverts"]["note"].startswith("revert=0x08c379a0")
        assert observed["close_zero_reverts"]["note"].startswith("revert=0x08c379a0")
        assert observed["close_frozen_far"]["a"] == 501290
        assert observed["close_frozen_far"]["b"] == 8997361550391042670658500
        assert observed["close_frozen_next_block"]["a"] == 501290
        assert observed["batch_boundary"]["a"] == 1
        assert observed["pause_crossed_liquidates_at_frozen"]["a"] == 200000
        assert observed["pause_crossed_liquidates_at_frozen"]["note"].startswith("phase2=ok")
        assert "phase3=ok" in observed["pause_crossed_liquidates_at_frozen"]["note"]
        assert "0x0000000000000000000000000000000000000000000000000000000000030d40" in \
            observed["pause_crossed_liquidates_at_frozen"]["note"]
        assert observed["queue_defers_large_payout"]["c"] > 0
        assert observed["small_payout_paid_direct"]["c"] == 0
        assert observed["small_payout_paid_direct"]["note"].startswith("balanceDelta=")
        assert observed["paused_close"]["a"] == 1
        assert observed["unpause"]["a"] == 0
        assert "d9d193d3" in observed["unpause"]["note"]
    # The close that would pay 8,997,361.55 USDC credits exactly lpBankrollAvailable
    # (5,002,012.573755119) and defers the rest to the queue.
    assert pinned["queue_defers_large_payout"]["note"] == \
        "balanceDelta=5002012573755118958351370"
    assert pinned["queue_defers_large_payout"]["c"] == 3835401745628102858893960
    # The pinned runtime dispatches the single-position entrypoint; set 2 has no reference to it.
    assert pinned["liquidate_boundary_exact"]["a"] == 1, pinned["liquidate_boundary_exact"]
    assert pinned["liquidate_boundary_exact"]["b"] == 1
    assert pinned["liquidate_boundary_plus_one"]["a"] == 0
    assert "0xddeb79ba" in pinned["liquidate_boundary_plus_one"]["note"]
    assert pinned["liquidate_valid_price"]["a"] == 0
    assert "0xddeb79ba" in pinned["liquidate_valid_price"]["note"]
    assert set2["liquidate_boundary_exact"]["a"] == 0
    assert set2["liquidate_valid_price"]["a"] == 0
    assert "0x" == set2["liquidate_valid_price"]["note"].split("data=")[1], \
        set2["liquidate_valid_price"]["note"]
    # The paused zero snapshot settles a long at price zero on the pinned runtime.
    assert pinned["pause_zero_snapshot"]["note"].endswith(
        "0000000000000000000000000000000000000000000000000000000000000000" * 1)
    assert pinned["pause_zero_snapshot"]["a"] == 1
    # The open path: the pinned runtime rejects the synthetic open with 0xf4d678b8, and the same
    # call on a paused market returns MarketIsPaused() (0x741df939) instead, which is the gate.
    assert "0xf4d678b8" in pinned["open_live_probe"]["note"], pinned["open_live_probe"]
    assert pinned["open_paused"]["note"].endswith("data=0x741df939"), pinned["open_paused"]
    assert "0x741df939" != "0xf4d678b8"
    assert "0x741df939" in pinned["open_paused"]["note"]
    return {"pinned": result["pinned"], "set2": result["set2"],
            "mocked_reads": ["0x080e best bid/ask (every local case)",
                             "0x0806 mark price and 0x0807 oracle price are never reached: only "
                             "the Oracle's own getPriceSnapshot reads them and no captured runtime "
                             "calls it"]}


# ------------------------------------------------------------------ ledger

def ledger_rows(static, caps, forge, sweep):
    pinned = forge["pinned"]["observed"]
    set2 = forge["set2"]["observed"]
    eth_caps = caps["conversions"][str(INSTRUMENT)]
    bankroll = caps["lp_bankroll"]
    payout = int(pinned["close_frozen_far"]["b"]) / 10 ** 18
    credited = int("5002012573755118958351370") / 10 ** 18
    queued = int(pinned["queue_defers_large_payout"]["c"]) / 10 ** 18
    return [
        {
            "id": "LP-01",
            "title": "No freshness, deviation or lookback gate exists anywhere in the price path",
            "angle": "A1 freshness",
            "invariant": "A4",
            "actor": "any trader; the frozen-quote variant needs a keeper or the relayer",
            "precondition": ("HyperCore returns a non-zero, uncrossed quote that is stale, frozen or "
                             "self-consistent, and the Exchange prices the transition from it"),
            "trigger": ("a session-key close with precompile 0x080e mocked to a fixed bid == ask far "
                        "from the entry price, then the same close 5,000 blocks and two days later"),
            "impact": ("the close settles at the frozen price and the payout moves with it: the venue "
                       "pays a profit the real book never offered, and nothing in the Oracle or the "
                       "Exchange can detect it, so the payout is bounded only by the OI cap and the "
                       "queue"),
            "affected": "both",
            "severity": "medium",
            "status": "confirmed_simulation",
            "evidence_tier": "exact_runtime_replay",
            "evidence": {
                "oracle_opcode_census": static["oracle_opcode_census"],
                "exchange_timestamp_opcodes": static["exchange_timestamp_opcodes"],
                "pinned_close_live_valid": pinned["close_live_valid"],
                "pinned_close_frozen_far": pinned["close_frozen_far"],
                "pinned_close_frozen_next_block": pinned["close_frozen_next_block"],
                "set2_close_frozen_far": set2["close_frozen_far"],
                "set2_close_frozen_next_block": set2["close_frozen_next_block"],
                "available_staleness_data": ("the only timestamp in the price surface is bits 136..199 "
                                             "of marketPause[instrumentId]; a pauseMarket call on this "
                                             "fixture stored flag | bid | ask | timestamp where the "
                                             "timestamp word is exactly 2**136 + 1 at block time 1, and "
                                             "no code compares it. The BBO precompile returns bid and "
                                             "ask only and the Oracle executes zero TIMESTAMP opcodes"),
            },
            "missing_observation": ("an archive trace of a real close whose settled midpoint was never "
                                    "between the entry price and the market price in the same second"),
            "citations": ["atlas/block_48902346/oracle_pseudocode.md",
                          "https://docs.papertrade.xyz/how/pricing-bbo"],
        },
        {
            "id": "LP-02",
            "title": "pauseMarket freezes an unvalidated raw BBO irreversibly in the deployed "
                     "implementation: a full dispatcher sweep finds no clearing path",
            "angle": "A1 freshness / A2 raw reads",
            "invariant": "A4",
            "actor": "pause guardian or owner; an attacker who moves HyperCore's inside quote first",
            "precondition": ("the pause guardian or owner calls pauseMarket(instrumentId) while the live "
                             "book is crossed or zero"),
            "trigger": ("the 0x2d2451d1 body reads raw getBBO (selector 0xfb466481, no zero and no "
                        "crossed check), packs flag|bid|ask|block.timestamp into marketPause[id], and "
                        "the price helper's paused branch returns floor((storedBid+storedAsk)/2) "
                        "without consulting the oracle"),
            "impact": ("one pause taken on a crossed book fixes a fake price for that instrument id: a "
                       "pause on the mocked crossed 300000/100000 book made both the pinned and the "
                       "set-2 runtime settle a subsequent liquidation at 200000 while the live book read "
                       "250700, and the same holds for a zero book, which the Exchange then settles at "
                       "price 0. No path in either deployed implementation clears it: the named "
                       "unpauseMarket (0xfb9f1009) reverts 0xd9d193d3 from every caller, and a sweep of "
                       "all 105 set-2 dispatcher selectors from owner, pause guardian, market keeper and "
                       "an outsider under eight argument passes (3,255 calls, each isolated in a state "
                       "snapshot, seeded word flag=1 with a packed bid/ask) produced zero flag clears and "
                       "zero word changes, while the same sweep's positive control shows exactly one "
                       "writer of a pause-shaped word, pauseMarket itself from owner or guardian"),
            "affected": "both",
            "severity": "high",
            "status": "confirmed_simulation",
            "evidence_tier": "exact_runtime_replay",
            "evidence": {
                "raw_call_site": ("the Exchange implementation pushes selector 0xfb466481 exactly once, "
                                  "inside the pauseMarket body, in both runtimes: " +
                                  json.dumps(static["price_selector_references"][
                                      "pinned_exchange_implementation"])),
                "pinned_pause_crossed": pinned["pause_crossed_liquidates_at_frozen"],
                "set2_pause_crossed": set2["pause_crossed_liquidates_at_frozen"],
                "pinned_pause_zero": pinned["pause_zero_snapshot"],
                "set2_pause_zero": set2["pause_zero_snapshot"],
                "pinned_unpause": pinned["unpause"],
                "set2_unpause": set2["unpause"],
                "poisoned_oracle_control": ("the oracle proxy is etched to a reverting runtime after "
                                            "the pause and a fresh liquidation still succeeds "
                                            "(phase3=ok), so the frozen branch never consults it"),
                "pause_clearing_sweep": {
                    "runtime": SET2_IMPL,
                    "selectors_swept": sweep["summary"]["selectors_swept"],
                    "calls": sweep["summary"]["calls"],
                    "phases": sweep["summary"]["phases"],
                    "flag_cleared_rows": len(sweep["summary"]["pause_cleared"]),
                    "word_changed_rows_on_seeded_word": len(sweep["summary"]["pause_word_changed"]),
                    "pause_word_writers": sweep["summary"]["pause_word_set_by_selector"],
                    "pause_word_writer_callers": sweep["summary"]["pause_word_set_callers"],
                    "pause_control_table": pause_relevant_rows(sweep),
                    "raw_table": "artifacts/live2_pricing/pause_sweep.json",
                },
                "mapping_35_static": {
                    "pinned_key_sites": static["mapping_key_sites"][
                        "pinned_exchange_implementation"]["slot_35"],
                    "set2_key_sites": static["mapping_key_sites"][
                        "set2_exchange_implementation"]["slot_35"],
                    "pinned_verified_write": "SSTORE 12354 in the 12188 pauseMarket body",
                    "set2_verified_write": "SSTORE 11526 in the 11360 pauseMarket body",
                    "hint_caveat": ("the sstore_hint field is unverified: the pinned hint at 2645 is "
                                    "provably the mapping-36 side-exposure write inside the signed-open "
                                    "body (the open-limit ledger's PC 0xa44/0xa55), not a pause write"),
                    "sstore_total": static["sstore_total"],
                },
                "global_trading_pause": {
                    "set_by": sweep["summary"]["trading_pause_set"],
                    "cleared_by": sweep["summary"]["trading_pause_cleared"],
                    "kept_by_everyone_else": True,
                    "guardian_clear_revert": "0x49199fb6 NotPauseAuthority()",
                    "slot": "storage slot 29 low byte",
                },
                "upgrade_caveat": ("permanence is a property of the deployed implementations. The "
                                   "ProxyAdmin owner is the newest timelock and the set-2 batch itself "
                                   "executed ProxyAdmin.upgrade, so a governance upgrade can rewrite the "
                                   "proxy storage, including this word; no such rewrite is recorded"),
            },
            "missing_observation": ("an archive trace of a liquidation executed while a market was "
                                    "paused, and a post-pause storage rewrite or upgrade transaction "
                                    "that clears a market-pause word; the saved logs contain no "
                                    "successful pauseMarket emission, so the frozen branch is "
                                    "unreachable in the sampled history"),
            "citations": ["atlas/block_48902346/exchange_pause_pseudocode.md",
                          "atlas/block_48902346/exchange_disabled_selector.md",
                          "atlas/block_48902346/suite_sets.md",
                          "https://docs.papertrade.xyz/how/pricing-bbo"],
        },
        {
            "id": "LP-03",
            "title": "Raw-versus-validated read map: one raw getBBO consumer, every value-moving path "
                     "validated",
            "angle": "A2 raw reads",
            "invariant": "A4",
            "actor": "any",
            "precondition": "a crossed or zero HyperCore book",
            "trigger": ("scan every captured runtime for the six oracle selectors, then drive the "
                        "reachable consumers with crossed and zero books"),
            "impact": ("no value-moving path (signed open, signed close, liquidate, liquidateBatch) "
                       "reads a raw or unvalidated price: a crossed and a zero book both revert the "
                       "close with Error(string) 'BBO crossed' and 'BBO unavailable'. getPriceSnapshot "
                       "and the snapshot-array selector exist only in the Oracle and are referenced by "
                       "no captured runtime, so the unvalidated snapshot surface is unreachable from "
                       "the Exchange"),
            "affected": "both",
            "severity": "info",
            "status": "confirmed_simulation",
            "evidence_tier": "exact_runtime_replay",
            "evidence": {
                "catalogue": static["catalogue"],
                "pinned_close_crossed_reverts": pinned["close_crossed_reverts"],
                "pinned_close_zero_reverts": pinned["close_zero_reverts"],
                "set2_close_crossed_reverts": set2["close_crossed_reverts"],
                "set2_close_zero_reverts": set2["close_zero_reverts"],
                "live_midpoint_control": pinned["close_live_valid"],
            },
            "missing_observation": ("a caller of getPriceSnapshot or 0xa7f06462 in a live transaction; "
                                    "none exists in the captured history"),
            "citations": ["atlas/block_48902346/oracle_pseudocode.md",
                          "atlas/block_48902346/exchange_liquidation_invalid_prices.md"],
        },
        {
            "id": "LP-04",
            "title": "No unprivileged price writer: the Oracle has no price setter and the "
                     "price-affecting writers are owner or marketKeeper gated",
            "angle": "A3 price reachability",
            "invariant": "A4",
            "actor": "unprivileged user, session key, relayer, keeper, builder, mev bot",
            "precondition": "none",
            "trigger": ("enumerate the PriceOracle dispatch (nine selectors) and the Exchange writers "
                        "that feed the priced instrument record and the side caps"),
            "impact": ("no unprivileged actor can move a price or a cap: the Oracle's only "
                       "state-changing selectors are initialize (once) and transferOwnership (owner), "
                       "prices come only from the HyperCore read precompiles, the instrument setter "
                       "0x5ca4c0ea is owner-only, and the side-cap setter 0x628a9fd6 is owner or "
                       "marketKeeper"),
            "affected": "both",
            "severity": "none",
            "status": "disproved",
            "evidence_tier": "bytecode_static_read",
            "evidence": {
                "oracle_dispatch_selectors": static["oracle_dispatch_selectors"],
                "oracle_opcode_census": static["oracle_opcode_census"],
                "price_surface_dispatch": static["price_surface_dispatch"],
                "cited_caller_probes": ["atlas/block_48902346/exchange_instrument_admin_behavior.json",
                                        "atlas/block_48902346/exchange_market_fields_behavior.json",
                                        "atlas/block_48902346/oracle_behavior.json"],
            },
            "missing_observation": "none for this claim; a future implementation could add a setter",
            "citations": ["atlas/block_48902346/oracle_pseudocode.md",
                          "atlas/block_48902346/exchange_instrument_admin.md",
                          "atlas/block_48902346/exchange_market_fields.md"],
        },
        {
            "id": "LP-05",
            "title": "Per-side cap unit resolved; the cap bounds notional, not payout, so one eligible "
                     "close can still take the whole LP bankroll and create an unfunded queue claim",
            "angle": "A4 caps versus liquidity",
            "invariant": "A3",
            "actor": "any eligible trader",
            "precondition": ("an active position inside its side cap. The test position is 20,000 "
                             "margin at 500x (10,000,000 USDC notional); its side-exposure increment "
                             "is 0.5% of the live ETH long headroom, so it is admissible under the "
                             "live caps as well as the pinned fixture"),
            "trigger": ("close the position at a frozen 2x quote with the prestate lpBankrollAvailable "
                        "of 5,002,012.573755119 USDC, plus a small-move close as the control"),
            "impact": ("the adjusted payout is " + f"{payout:,.2f}" + " USDC; the close credits exactly "
                       "the whole available bankroll, " + f"{credited:,.6f}" + " USDC, and defers "
                       f"{queued:,.6f}" + " USDC into the queue, so one close inside the caps empties "
                       "available LP liquidity and leaves an unfunded claim. The small-move control "
                       "(879.53 USDC pinned, 378.51 USDC in set 2) is credited directly with no queue "
                       "entry, which is the control that the queue gate is real"),
            "affected": "both",
            "severity": "medium",
            "status": "confirmed_simulation",
            "evidence_tier": "exact_runtime_replay",
            "evidence": {
                "exposure_fit": caps["instruments"],
                "cap_unit": ("side-exposure increment = margin_1e18 * leverage * k / price_raw with k "
                             "measured as the market word0 last-64 field, 10 for instrument 0 (seven "
                             "increments at three prices, residual 0) and 100 for instrument 1 (one "
                             "increment), so the cap counts a base-asset quantity"),
                "max_single_position_notional": eth_caps,
                "caps": {"pinned": caps["pinned_caps"], "live": caps["live_caps"]},
                "lp_bankroll": bankroll,
                "pinned_queue_defers": pinned["queue_defers_large_payout"],
                "set2_queue_defers": set2["queue_defers_large_payout"],
                "pinned_small_paid_direct": pinned["small_payout_paid_direct"],
                        "set2_small_paid_direct": set2["small_payout_paid_direct"],
            },
            "missing_observation": ("a second consecutive committed signed open on instrument 1 in a "
                                    "different batch, to widen the k=100 measurement beyond one pair; "
                                    "the two runs of the payout control are one fixture, not chain state"),
            "citations": ["atlas/block_48902346/exchange_open_limit_full_behavior.json",
                          "atlas/block_48902346/exchange_market_fields.md",
                          "atlas/block_48902346/asymmetric_impact_behavior.md",
                          "https://docs.papertrade.xyz/how/risk"],
        },
        {
            "id": "LP-06",
            "title": "The documented 1e9 USD per-side headroom policy is inconsistent with the "
                     "configured caps",
            "angle": "A4 caps versus liquidity",
            "invariant": "proposed A8 (a published parameter policy matches the configured parameter)",
            "actor": "market keeper (policy), public docs (claim)",
            "precondition": ("the current docs state the keeper targets current OI plus 1e9 USD of "
                             "BBO-valued headroom per side inside a 10% hysteresis band"),
            "trigger": ("subtract the current side exposure from the configured cap and convert the "
                        "gap to USD with the measured cap unit"),
            "impact": ("the measured ETH headroom is about 5.14e6 USD long and 5.22e6 USD short at the "
                       "pin and about 1.91e6 and 1.94e6 USD live, so the documented 1e9 USD headroom "
                       "overstates the configured limit by roughly 195x to 520x; the docs number "
                       "cannot be used to reason about the real exposure limit"),
            "affected": "both",
            "severity": "low",
            "status": "confirmed_simulation",
            "evidence_tier": "bytecode_static_read",
            "evidence": caps["doc_headroom_claim"],
            "missing_observation": ("the keeper's off-chain cap-calculation inputs, so only the "
                                    "configured result is testable"),
            "citations": ["https://docs.papertrade.xyz/how/risk"],
        },
        {
            "id": "LP-07",
            "title": "Liquidation-price integer formula and its one-unit boundary hold in both "
                     "implementations",
            "angle": "A5 eligibility boundaries",
            "invariant": "A4",
            "actor": "any; liquidateBatch is a permissionless maintenance path",
            "precondition": "an active long position under the pinned ETH instrument record",
            "trigger": ("set the mocked midpoint to the exact integer boundary base = entry - "
                        "floor(entry/leverage) = 250,144, adjustment = floor(base*maintenanceRate/1e18) "
                        "= 120, boundary = 250,264, then 250,264 and 250,265"),
            "impact": ("at the exact boundary the position liquidates and its active bit clears "
                       "(pinned 250,264, a=1 b=1); at 250,265 it reverts NotLiquidatable "
                       "(0xddeb79ba) with no log; the batch path settles the same position at 250,264 "
                       "in both implementations, so batch and single share the integer formula"),
            "affected": "both",
            "severity": "none",
            "status": "confirmed_simulation",
            "evidence_tier": "exact_runtime_replay",
            "evidence": {
                "maintenance_rate_1e18": MAINT_RATE,
                "pinned_exact": pinned["liquidate_boundary_exact"],
                "pinned_plus_one": pinned["liquidate_boundary_plus_one"],
                "pinned_valid_price": pinned["liquidate_valid_price"],
                "set2_batch": set2["batch_boundary"],
                "pinned_batch": pinned["batch_boundary"],
            },
            "missing_observation": ("the same boundary on a short position and on the set-2 payout "
                                    "curve at a nonzero move; this control holds the move at zero"),
            "citations": ["atlas/block_48902346/exchange_liquidation_price.md",
                          "atlas/block_48902346/exchange_liquidation_pseudocode.md"],
        },
        {
            "id": "LP-08",
            "title": "Contract set 2 drops liquidate(uint256): the single-position liquidation "
                     "entrypoint is gone while liquidateBatch stays",
            "angle": "A5 eligibility boundaries",
            "invariant": "A4",
            "actor": "any integration, keeper or recovery caller",
            "precondition": "the set-2 Exchange implementation behind the proxy",
            "trigger": ("call 0x415f1240 on the set-2 runtime at a boundary-eligible position and at a "
                        "valid price"),
            "impact": ("the call reverts with empty data on set 2 (no dispatch) while the pinned "
                       "runtime returns the NotLiquidatable predicate 0xddeb79ba at the same two "
                       "prices, and the batch path proves the position was liquidatable at 250,264; "
                       "the set-2 runtime contains no reference to the selector anywhere in its bytes, "
                       "so any tool calling the single entrypoint silently loses the route"),
            "affected": "set2",
            "severity": "low",
            "status": "confirmed_simulation",
            "evidence_tier": "exact_runtime_replay",
            "evidence": {
                "dispatch_diff": static["dispatch_diff"],
                "selector_bytes_present": {"pinned": True, "set2": False},
                "set2_single_liquidate_at_boundary": set2["liquidate_boundary_exact"],
                "set2_single_liquidate_valid_price": set2["liquidate_valid_price"],
                "pinned_single_liquidate_control": pinned["liquidate_valid_price"],
                "set2_batch_control": set2["batch_boundary"],
            },
            "missing_observation": ("whether one of the set-2 additions (0x5780639d, 0xcbce7532, "
                                    "0xd970fad5, 0xe6ac4a74, 0xf009ac03) is a replacement single "
                                    "position route"),
            "citations": ["atlas/block_48902346/suite_sets.md"],
        },
        {
            "id": "LP-09",
            "title": "A paused market gates new opens with MarketIsPaused() while closes and "
                     "liquidations settle at the frozen snapshot",
            "angle": "A5 eligibility boundaries",
            "invariant": "A4",
            "actor": "pause guardian (gate) against any holder (consequence)",
            "precondition": "marketPause[instrumentId].flag is set",
            "trigger": ("close a position and submit a signed open and a liquidation on the same "
                        "paused instrument with a fresh valid live quote mocked"),
            "impact": ("the same signed open that the pinned runtime rejects with the unresolved raw "
                       "0xf4d678b8 on this fixture returns exactly 0x741df939, the keccak selector of "
                       "MarketIsPaused(), once the market is paused, so the pause gate is real and "
                       "fires ahead of the later synthetic-state check; meanwhile the close succeeds "
                       "and the liquidation settles at the frozen snapshot rather than the live quote, "
                       "so the pause hands the exit price to whoever reaches the maintenance path"),
            "affected": "both",
            "severity": "medium",
            "status": "confirmed_simulation",
            "evidence_tier": "exact_runtime_replay",
            "evidence": {
                "market_is_paused_selector": "0x741df939 = keccak256('MarketIsPaused()')[0:4]",
                "pinned_open_unpaused_probe": pinned["open_live_probe"],
                "pinned_open_paused_probe": pinned["open_paused"],
                "set2_open_unpaused_probe": set2["open_live_probe"],
                "set2_open_paused_probe": set2["open_paused"],
                "pinned_paused_close": pinned["paused_close"],
                "set2_paused_close": set2["paused_close"],
                "pinned_paused_liquidation": pinned["pause_crossed_liquidates_at_frozen"],
                "set2_paused_liquidation": set2["pause_crossed_liquidates_at_frozen"],
                "open_probe_limit": ("the synthetic open never reaches its success branch on this "
                                     "fixture (raw 0xf4d678b8 after the pause gate), so the open "
                                     "control is a differential revert reason, not a successful open"),
            },
            "missing_observation": ("an archive trace of a close or an open submitted while a market "
                                    "was paused, and the name of the raw 0xf4d678b8 open error"),
            "citations": ["https://docs.papertrade.xyz/how/pricing-bbo",
                          "atlas/block_48902346/exchange_pause_pseudocode.md"],
        },
    ]


def write_outputs(static, caps, forge, sweep, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "static_evidence.json").write_text(json.dumps(static, indent=2) + "\n")
    (OUT / "caps_fit.json").write_text(json.dumps(caps, indent=2) + "\n")
    (OUT / "forge_replay.json").write_text(json.dumps(forge, indent=2) + "\n")
    (OUT / "ledger.json").write_text(json.dumps(rows, indent=2) + "\n")
    (OUT / "pause_sweep.json").write_text(json.dumps(sweep, indent=2) + "\n")
    LEDGER.write_text(json.dumps({
        "generated_by": "audit_live2_pricing.py",
        "pin": PIN, "pin_hash": PIN_HASH, "prestate_block": PRESTATE_BLOCK,
        "scope": "pricing and eligibility: PriceOracle, every Exchange price consumer, the size caps "
                 "and the liquidation boundaries",
        "evidence_after": {"static": "artifacts/live2_pricing/static_evidence.json",
                           "caps": "artifacts/live2_pricing/caps_fit.json",
                           "forge": "artifacts/live2_pricing/forge_replay.json"},
        "rows": rows,
    }, indent=2) + "\n")
    lines = ["# Pricing and eligibility: pinned suite versus contract set 2", "",
             "Generated by [`audit_live2_pricing.py`](../../scripts/audit_live2_pricing.py), offline. Machine "
             "ledger: [live2_pricing.json](live2_pricing.json); raw captures under "
             "`artifacts/live2_pricing/`. Every local case is a port-free Foundry replay of the exact "
             "proxy, implementation and linked-library bytes with HyperCore read precompiles mocked, "
             "and every mocked reply is labelled as such.", "",
             "## Value table", "",
             "| id | angle | invariant | affected | severity | status | finding |",
             "|---|---|---|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['id']} | {row['angle']} | {row['invariant']} | {row['affected']} | "
                     f"{row['severity']} | {row['status']} | {row['title']} |")
    lines += ["", "## Per-row detail", ""]
    for row in rows:
        lines.append(f"### {row['id']} {row['title']}")
        lines.append("")
        lines.append(f"- Angle {row['angle']}; invariant {row['invariant']}; actor: {row['actor']}")
        lines.append(f"- Precondition: {row['precondition']}")
        lines.append(f"- Trigger: {row['trigger']}")
        lines.append(f"- Impact: {row['impact']}")
        lines.append(f"- Affected {row['affected']}; severity {row['severity']}; status "
                     f"{row['status']}; evidence tier {row['evidence_tier']}")
        lines.append(f"- Evidence: `{json.dumps(row['evidence'])}`")
        lines.append(f"- Missing observation: {row['missing_observation']}")
        lines.append(f"- Citations: {', '.join(row['citations'])}")
        lines.append("")
    lines += ["## Measured price surface", "",
              "| Read | Selector | Consumers in the captured runtimes | Validation |",
              "|---|---|---|---|",
              "| validated BBO midpoint | `0xc0182669` | pinned and set-2 Exchange implementations "
              "(one call site each: the price helper every trading and liquidation path uses) | "
              "rejects zero and crossed |",
              "| raw BBO | `0xfb466481` | pinned and set-2 Exchange implementations (one call site "
              "each: `pauseMarket`) and the Oracle itself | none |",
              "| price snapshot | `0x766cd255` | the Oracle only; no captured contract calls it | none "
              "(zero and crossed pass through) |",
              "| snapshot array | `0xa7f06462` | the Oracle only; no captured contract calls it | none |",
              "| oracle price | `0x2af78bd1` | the Oracle only, for the snapshot | rejects zero |",
              "| mark price | `0xa066fae9` | the Oracle only, for the snapshot | rejects zero |", "",
              "## Pause-clearing sweep on contract set 2", "",
              f"All {sweep['summary']['selectors_swept']} dispatcher selectors of the set-2 Exchange "
              f"implementation were called {sweep['summary']['calls']} times in total: from the owner "
              "(the timelock), the pause guardian, the market keeper and an unrelated address, under "
              "eight caller-and-argument passes over five argument templates (eight zero words, eight maximum "
              "words, an outsider address first, an explicit instrument-zero with a true flag, and a "
              "true-first word). Every call ran in its "
              "own state snapshot with the market-pause word for instruments 0, 1 and 2 seeded to "
              "flag=1 with a packed bid/ask, and storage slot 29 to the tested state, so a clear would "
              "be attributed to the call that caused it.", "",
              "| Selector | Name | Calls | Succeeded | Pause-word changes | Revert data |",
              "|---|---|---:|---:|---:|---|",
              *[f"| `{row['selector']}` | {row['name']} | {row['calls']} | {row['succeeded']} | "
                f"{row['pause_word_changes']} | {', '.join(row['revert_data']) or 'none'} |"
                for row in pause_relevant_rows(sweep)], "",
              f"Zero of the {sweep['summary']['calls']} calls cleared the seeded flag and zero changed "
              "the seeded word. The only selector that writes a pause-shaped word is `0x2d2451d1` "
              "itself, from the owner and the pause guardian, which is the sweep's positive control "
              "that a mapping-35 write is detectable at all; the static analysis agrees, with exactly "
              "one verified mapping-35 write in each runtime (pinned SSTORE 12354 inside the 12188 "
              "pauseMarket body, set 2 SSTORE 11526 inside 11360) and four mapping-35 key-derivation "
              "sites in each. The static `sstore_hint` field is deliberately unverified: the pinned "
              "hint at 2645 is the mapping-36 side-exposure write inside the signed-open body, not a "
              "pause write.", "",
              "Coverage limit of the sweep: it watches the pause words of instrument ids 0, 1 and 2 "
              "(the pinned instrument count is 2) and five argument templates, so a hypothetical path "
              "that needs an argument outside those templates is not covered; the static accessor "
              "census is the second, independent check, and it finds no other mapping-35 write site to "
              "reach. The two methods agree, and no saved evidence contradicts either.", "",
              "The global trading pause in slot 29 is the reversible control: `setTradingPaused(true)` "
              "succeeds from the owner and the pause guardian (`0xae69b95b`) and from nobody else, and "
              "clearing it succeeds from the owner only, with the pause guardian getting "
              "`0x49199fb6` NotPauseAuthority(). A market-level pause has no such switch in the "
              "deployed implementation; a governance upgrade can still rewrite proxy storage, which is "
              "the upgrade caveat recorded on LP-02.", "",
              "## Harness controls", "",
              "- `testB_close_crossed_reverts` and `testC_close_zero_reverts` are the negative "
              "controls for a crossed and a zero book; `testA_close_live_valid` and "
              "`testI_batch_boundary` are the controls that must succeed.",
              "- `testJ_pause_crossed_freezes_crossed_price` etches a reverting runtime over the "
              "oracle proxy after the pause and the liquidation still succeeds, which is the control "
              "that the frozen branch never consults the oracle.",
              "- `testO_small_payout_paid_direct` is the control that a small payout is credited "
              "directly with no queue entry, against `testN_queue_defers_large_payout`.",
              "- `testM_unpause_reverts` is the control that the frozen snapshot has no route back.",
              "- `testF`/`testG`/`testH` are the exactly-at, one-unit-over and valid-price controls "
              "for the single-position liquidation entrypoint, and `testI` is the batch control that "
              "the same position was liquidatable at that boundary.",
              "- `testK_pause_zero_freezes_zero_price` is the control that a zero book passes the raw "
              "snapshot path, and its liquidation log carries price 0 with the 250,264 threshold.",
              "- `testP`/`testQ` are a differential control on the open path: the same synthetic open "
              "returns an unresolved raw 0xf4d678b8 while the market is live and exactly "
              "MarketIsPaused() once it is paused, so the pause gate is read before the later check. "
              "The synthetic open never reaches its success branch, so no successful-open control "
              "exists on this fixture.", "",
              "## Method and limits", "",
              "- Static reads are byte scans of the exact runtime files: PUSH4 immediates for the "
              "call-site map, a linear opcode census that skips PUSH data, and the dispatcher EQ "
              "pattern for the selector sets. The Oracle's zero TIMESTAMP count is a hard absence.",
              "- The side-exposure fit uses the 57 saved signed-open comparisons and their "
              "BatchExecutor call trees: increments are differences of two committed comparisons in "
              "one transaction, so the unknown stored base cancels, and each increment is paired with "
              "the midpoint the same transaction read.",
              "- Every Foundry case restores the saved mixed-close prestate at block 48,901,631 and "
              "overrides only the implementation pointer, the instrument record and the market field "
              "word; accounting stays at its prestate value, so payout and queue columns are local "
              "scenario values, not current chain values.",
              "- The set-2 variant uses the captured set-2 implementation, library and session-key "
              "manager; the live instrument record is byte-identical to the pinned one, and the "
              "pinned market field word is used so the pinned accounting stays consistent.",
              "- No archive provider is configured, so no historical state read backs these rows; the "
              "missing observations above are the calls an archive endpoint would settle.", ""]
    DOC.write_text("\n".join(lines) + "\n")


def capture_live():
    head = int(rpc("eth_blockNumber", []), 16)
    header = rpc("eth_getBlockByNumber", [hex(head), False])
    implementation = "0x" + rpc("eth_getStorageAt", [EXCHANGE, EIP1967_SLOT, "latest"])[-40:]
    words = {u256(int(MARKET_ROOT, 16) + i):
             rpc("eth_getStorageAt", [EXCHANGE, u256(int(MARKET_ROOT, 16) + i), "latest"])
             for i in range(2)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "live_market_words.json").write_text(json.dumps(
        {"head_block": head, "head_hash": header["hash"], "implementation": implementation,
         "market_words": words,
         "method": "public rpc at latest; the rpc ignores block parameters"}, indent=2) + "\n")
    print(f"live market words captured at block {head}")


# ------------------------------------------------------------------ pause-clearing sweep

SWEEP_SOURCE = r'''// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function chainId(uint256) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function writeLine(string calldata, string calldata) external;
    function snapshotState() external returns (uint256);
    function revertToState(uint256) external;
}

contract PauseSweepTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = @EXCHANGE@;
    address constant OWNER = @OWNER@;
    address constant GUARDIAN = @GUARDIAN@;
    address constant KEEPER = @KEEPER@;
    address constant OUTSIDER = @OUTSIDER@;
    uint256 constant SEED_WORD = @SEED@;
    uint256 constant TRADING_SLOT = 29;

    bytes4[] selectors;

    function pauseKey(uint256 id) internal pure returns (bytes32) {
        return keccak256(abi.encode(id, uint256(35)));
    }

    function setUp() public {
@SETUP@
        bytes4[] memory all = new bytes4[](@COUNT@);
@SELECTORS@
        for (uint256 i; i < all.length; ++i) selectors.push(all[i]);
    }

    function callerAt(uint256 index) internal view returns (address, string memory) {
        if (index == 0) return (OWNER, "owner");
        if (index == 1) return (GUARDIAN, "guardian");
        if (index == 2) return (KEEPER, "keeper");
        return (OUTSIDER, "outsider");
    }

    function templateData(bytes4 selector, uint256 template) internal pure returns (bytes memory data) {
        data = abi.encodePacked(selector);
        for (uint256 i; i < 8; ++i) {
            uint256 word;
            if (template == 1) word = type(uint256).max;
            else if (template == 2 && i == 0) word = uint256(uint160(OUTSIDER));
            else if (template == 3 && i == 0) word = 0;
            else if (template == 3 && i == 1) word = 1;
            else if (template == 4 && i == 0) word = 1;
            data = abi.encodePacked(data, bytes32(word));
        }
    }

    function sweepOne(string memory phase, uint256 selectorIndex, uint256 callerIndex,
                      uint256 template, bool seedFlag, bool seedTrading) internal {
        uint256 snapshot = vm.snapshotState();
        uint256 word = seedFlag ? SEED_WORD : 0;
        vm.store(EXCHANGE, pauseKey(0), bytes32(word));
        vm.store(EXCHANGE, pauseKey(1), bytes32(word));
        vm.store(EXCHANGE, pauseKey(2), bytes32(word));
        vm.store(EXCHANGE, bytes32(TRADING_SLOT), bytes32(seedTrading ? uint256(1) : 0));
        bytes4 selector = selectors[selectorIndex];
        (address caller, string memory callerName) = callerAt(callerIndex);
        vm.prank(caller);
        (bool ok, bytes memory returned) = EXCHANGE.call(templateData(selector, template));
        uint256 after0 = uint256(vm.load(EXCHANGE, pauseKey(0)));
        uint256 after1 = uint256(vm.load(EXCHANGE, pauseKey(1)));
        uint256 after2 = uint256(vm.load(EXCHANGE, pauseKey(2)));
        uint256 tradingAfter = uint256(vm.load(EXCHANGE, bytes32(TRADING_SLOT))) & 0xff;
        string memory label = string.concat(phase, "_", u2s(selectorIndex), "_", u2s(callerIndex),
                                           "_", u2s(template));
        string memory note = string.concat("sel=", u2s(selectorIndex), ";caller=", callerName,
            ";template=", u2s(template), ";outcome=", ok ? "ok" : "revert",
            ";data=", toHex(returned), ";flagAfter=", u2s(after0 & 0xff),
            ";word0After=", u2s(after0), ";wordChanged=", after0 == word ? "0" : "1",
            ";word1FlagAfter=", u2s(after1 & 0xff), ";word2FlagAfter=", u2s(after2 & 0xff),
            ";tradingSlotAfter=", u2s(tradingAfter), ";tradingSeeded=", seedTrading ? "1" : "0");
        vm.writeLine("results/observed.csv", string.concat(label, ",", ok ? "1" : "0", ",0,0,", note));
        vm.revertToState(snapshot);
    }

    function testReadSweep() public {
        uint256[4] memory callers = [uint256(0), 1, 2, 3];
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < callers.length; ++c) sweepOne("read", i, callers[c], 0, true, false);
        }
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < 2; ++c) sweepOne("readmax", i, c, 1, true, false);
        }
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < 3; ++c) sweepOne("readaddr", i, c, 2, true, false);
        }
        for (uint256 i; i < selectors.length; ++i) {
            sweepOne("readid", i, 0, 3, true, false);
            sweepOne("readid", i, 1, 3, true, false);
        }
    }

    function testWriteSweep() public {
        uint256[4] memory callers = [uint256(0), 1, 2, 3];
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < callers.length; ++c) sweepOne("write", i, callers[c], 0, false, false);
        }
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < 2; ++c) sweepOne("writemax", i, c, 1, false, false);
        }
    }

    function testTradingSweep() public {
        uint256[4] memory callers = [uint256(0), 1, 2, 3];
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < callers.length; ++c) {
                sweepOne("trading", i, c, 0, true, true);
            }
        }
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < 4; ++c) {
                sweepOne("tradingclear", i, c, 3, true, true);
            }
        }
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < 4; ++c) {
                sweepOne("tradingset", i, c, 4, true, false);
            }
        }
        for (uint256 i; i < selectors.length; ++i) {
            for (uint256 c; c < 2; ++c) {
                sweepOne("tradingsetguardian", i, c, 4, true, false);
            }
        }
    }

    function u2s(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 t = v;
        uint256 d;
        while (t != 0) { d++; t /= 10; }
        bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }

    function toHex(bytes memory data) internal pure returns (string memory) {
        bytes memory alphabet = "0123456789abcdef";
        bytes memory out = new bytes(2 + data.length * 2);
        out[0] = "0";
        out[1] = "x";
        for (uint256 i; i < data.length; ++i) {
            out[2 + i * 2] = alphabet[uint8(data[i] >> 4)];
            out[3 + i * 2] = alphabet[uint8(data[i] & 0x0f)];
        }
        return string(out);
    }
}
'''


def sweep_seed_word():
    return (1 | (PAUSE_SEED_BID << 8) | (PAUSE_SEED_ASK << 72) | (PAUSE_SEED_TIMESTAMP << 136))


def render_sweep_source(setup_lines, selectors):
    body = "\n".join(f"        all[{i}] = bytes4({selector});"
                      for i, selector in enumerate(selectors))
    source = SWEEP_SOURCE
    tokens = {
        "@EXCHANGE@": s_address(EXCHANGE), "@OWNER@": s_address(OWNER),
        "@GUARDIAN@": s_address(GUARDIAN), "@KEEPER@": s_address(MARKET_KEEPER),
        "@OUTSIDER@": s_address(OUTSIDER), "@SEED@": str(sweep_seed_word()),
        "@COUNT@": str(len(selectors)), "@SELECTORS@": body,
        "@SETUP@": "\n".join(setup_lines),
    }
    for token, value in tokens.items():
        assert token in source, token
        source = source.replace(token, value)
    return source


def pause_sweep_evidence():
    """Call every set-2 dispatcher selector from four callers and watch the pause words."""
    prestate = json.loads(PRESTATE.read_text())
    codes = {address: row.get("code", "0x") for address, row in prestate.items()}
    codes[SET2_IMPL] = load_hex(RUNTIME_FILES[SET2_IMPL])
    codes[SET2_LIB] = load_hex(RUNTIME_FILES[SET2_LIB])
    codes[SET2_SESSION_IMPL] = load_hex(RUNTIME_FILES[SET2_SESSION_IMPL])
    lines = [f"        vm.chainId({CHAIN_ID});"]
    for address, row in sorted(prestate.items(), key=lambda item: item[0].lower()):
        if codes[address] != "0x":
            lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes('
                         f'vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items(), key=lambda item: int(item[0], 16)):
            if int(value, 16):
                lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    for address in (SET2_IMPL, SET2_LIB, SET2_SESSION_IMPL):
        if address not in prestate:
            lines.append(f'        vm.etch({s_address(address)}, vm.parseBytes('
                         f'vm.readFile("runtime/{address[2:]}.hex")));')
    lines.append(f"        vm.store({s_address(EXCHANGE)}, {EIP1967_SLOT}, "
                 f"{u256(int(SET2_IMPL, 16))});")
    lines.append(f"        vm.store({s_address(EXCHANGE)}, bytes32(0), "
                 f"{u256((int(OWNER, 16) << 16) | 1)});")
    lines.append(f"        vm.store({s_address(EXCHANGE)}, bytes32(uint256(1)), {u256(int(GUARDIAN, 16))});")
    lines.append(f"        vm.store({s_address(EXCHANGE)}, bytes32(uint256(37)), {u256(int(MARKET_KEEPER, 16))});")
    lines.append(f"        vm.store({s_address(SESSION)}, {EIP1967_SLOT}, "
                 f"{u256(int(SET2_SESSION_IMPL, 16))});")
    for index, word in enumerate(pack_instrument(instrument_words(INSTRUMENT))):
        lines.append(f"        vm.store({s_address(EXCHANGE)}, "
                     f"{u256(int(INSTRUMENT_ROOT, 16) + index)}, {u256(word)});")
    roots = {
        INSTRUMENT: (INSTRUMENT_ROOT, MARKET_ROOT),
        0: ("0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6df",
            "0xb7634ec2165a7280a285aac3ec10cf370eca86d8aa9d3243c90b2151434091ad"),
    }
    for instrument, (instrument_root, market_root) in roots.items():
        for index, word in enumerate(pack_instrument(instrument_words(instrument))):
            lines.append(f"        vm.store({s_address(EXCHANGE)}, "
                         f"{u256(int(instrument_root, 16) + index)}, {u256(word)});")
        for index, word in enumerate(market_words(instrument)):
            lines.append(f"        vm.store({s_address(EXCHANGE)}, "
                         f"{u256(int(market_root, 16) + index)}, {u256(word)});")
    for asset, (bid, ask) in ((0, (809520, 809530)), (1, (234900, 234910))):
        lines.append(f"        vm.mockCall(address(uint160(uint256(0x080e))), "
                     f"abi.encode(uint32({asset})), abi.encode(uint256({bid}), uint256({ask})));")
    selectors = sorted(dispatch_selectors(body(RUNTIME_FILES[SET2_IMPL])))
    source = render_sweep_source(lines, selectors)
    assert shutil.which("forge") and shutil.which("solc"), "forge and solc are required"
    with tempfile.TemporaryDirectory(prefix="papertrade-pause-sweep-") as tmp:
        project = pathlib.Path(tmp)
        for name in ("test", "runtime", "results"):
            (project / name).mkdir()
        (project / "results" / "observed.csv").write_text("")
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(shutil.which("solc")) +
            "\noffline = true\nvia_ir = true\noptimizer = true\noptimizer_runs = 200\n"
            'fs_permissions = [{ access = "read", path = "./runtime" }, '
            '{ access = "read-write", path = "./results" }]\n')
        (project / "test" / "PauseSweep.t.sol").write_text(source)
        for address, code in codes.items():
            if code != "0x":
                (project / "runtime" / f"{address[2:]}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vv"],
                             check=False, capture_output=True, text=True, timeout=1800)
        output = run.stdout + "\n" + run.stderr
        observed = (project / "results" / "observed.csv").read_text()
    if run.returncode or "[FAIL" in output or "passed" not in output:
        raise RuntimeError("pause sweep failed:\n" + output[-8000:])
    rows = []
    for line in observed.splitlines():
        if not line.strip():
            continue
        label, ok, _b, _c, note = line.split(",", 4)
        fields = dict(part.split("=", 1) for part in note.split(";"))
        rows.append({"label": label, "ok": ok == "1",
                     "selector_index": int(fields["sel"]),
                     "selector": selectors[int(fields["sel"])],
                     "caller": fields["caller"], "template": int(fields["template"]),
                     "revert_data": fields["data"], "flag_after": int(fields["flagAfter"]),
                     "word0_changed": fields["wordChanged"] == "1",
                     "word1_flag_after": int(fields["word1FlagAfter"]),
                     "word2_flag_after": int(fields["word2FlagAfter"]),
                     "trading_slot_after": int(fields["tradingSlotAfter"]),
                     "trading_seeded": fields["tradingSeeded"] == "1",
                     "phase": label.rsplit("_", 3)[0]})
    rows.sort(key=lambda row: (row["phase"], row["selector_index"], row["caller"], row["template"]))
    summary = {
        "selectors_swept": len(selectors),
        "calls": len(rows),
        "phases": sorted({row["phase"] for row in rows}),
        "pause_cleared": [row for row in rows if row["flag_after"] == 0 and
                          row["phase"].startswith("read")],
        "pause_word_changed": [row for row in rows if row["word0_changed"] and
                               row["phase"].startswith("read")],
        "pause_word_set_by_call": [row for row in rows if row["flag_after"] == 1 and
                                   row["word0_changed"] and row["phase"].startswith("write")],
        "trading_pause_set": sorted({(row["selector"], row["caller"]) for row in rows
                                     if row["trading_slot_after"] == 1 and
                                     row["trading_seeded"] is False}),
        "pause_word_set_by_selector": sorted({row["selector"] for row in rows
                                              if row["flag_after"] == 1 and
                                              row["word0_changed"] and
                                              row["phase"].startswith("write")}),
        "pause_word_set_callers": sorted({row["caller"] for row in rows
                                          if row["flag_after"] == 1 and
                                          row["word0_changed"] and
                                          row["phase"].startswith("write")}),
        "trading_pause_cleared": sorted({(row["selector"], row["caller"]) for row in rows
                                         if row["trading_slot_after"] == 0 and
                                         row["trading_seeded"] and
                                         row["phase"].startswith("trading")}),
        "trading_pause_kept": sorted({(row["selector"], row["caller"]) for row in rows
                                      if row["trading_slot_after"] == 1 and
                                      row["trading_seeded"] and
                                      row["phase"].startswith("trading")}),
        "succeeded_calls": sorted({(row["selector"], row["caller"], row["template"])
                                   for row in rows if row["ok"]}),
    }
    return {"reshaped": {"selector_count": len(selectors), "selectors": selectors},
            "rows": rows, "summary": summary,
            "source_sha256": sha256_hex(source.encode()),
            "forge_result": "3 passed, 0 failed" if "3 passed" in output else output[-200:],
            "method": ("port-free Foundry replay of the set-2 proxy, implementation, linked library "
                       "and session-key manager with the saved prestate storage; each call is made in "
                       "its own state snapshot (vm.snapshotState/vm.revertToState), the market-pause "
                       "word for instruments 0, 1 and 2 and storage slot 29 are seeded before the call "
                       "and read afterwards, and HyperCore reads are never reached because the sweep "
                       "only calls the Exchange")}


def pause_relevant_rows(sweep):
    """Per-selector aggregate for the pause controls, built from the sweep rows."""
    labels = {PAUSE_MARKET: "pauseMarket(uint32)", UNPAUSE_MARKET: "unpauseMarket(uint32)",
              SET_TRADING_PAUSED: "setTradingPaused(bool)", SET_PAUSE_GUARDIAN: "setPauseGuardian(address)",
              TRADING_PAUSED_GETTER: "tradingPaused()", PAUSE_GUARDIAN_GETTER: "pauseGuardian()",
              OWNER_GETTER: "owner()", LIQUIDATE: "liquidate(uint256)",
              LIQUIDATE_BATCH: "liquidateBatch", CLOSE_SELECTOR: "close", OPEN_SELECTOR: "open"}
    aggregate = {}
    for row in sweep["rows"]:
        entry = aggregate.setdefault(row["selector"], {"calls": 0, "ok": 0, "reverts": set(),
                                                      "word_changed": 0})
        entry["calls"] += 1
        entry["ok"] += 1 if row["ok"] else 0
        if not row["ok"]:
            entry["reverts"].add(row["revert_data"])
        entry["word_changed"] += 1 if row["word0_changed"] else 0
    table = []
    for selector in (PAUSE_MARKET, UNPAUSE_MARKET, SET_TRADING_PAUSED, SET_PAUSE_GUARDIAN,
                     TRADING_PAUSED_GETTER, OWNER_GETTER, LIQUIDATE_BATCH, CLOSE_SELECTOR,
                     OPEN_SELECTOR, LIQUIDATE):
        entry = aggregate.get(selector)
        table.append({
            "selector": selector,
            "name": labels[selector],
            "dispatched": entry is not None,
            "calls": entry["calls"] if entry else 0,
            "succeeded": entry["ok"] if entry else 0,
            "pause_word_changes": entry["word_changed"] if entry else 0,
            "revert_data": sorted(entry["reverts"]) if entry else [],
        })
    return table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="refresh the live implementation pointer and market words")
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--skip-sweep", action="store_true")
    options = parser.parse_args()
    if options.capture:
        capture_live()
    identity = runtime_evidence()
    static = static_evidence()
    static["runtime_identity"] = identity
    caps = caps_section()
    OUT.mkdir(parents=True, exist_ok=True)
    if options.static_only:
        (OUT / "static_evidence.json").write_text(json.dumps(static, indent=2) + "\n")
        (OUT / "caps_fit.json").write_text(json.dumps(caps, indent=2) + "\n")
        print(f"static sections written; {len(caps['fit_rows'])} cap-fit rows")
        return
    forge = forge_evidence()
    sweep = pause_sweep_evidence()
    rows = ledger_rows(static, caps, forge, sweep)
    write_outputs(static, caps, forge, sweep, rows)
    print(f"{len(rows)} ledger rows; forge {forge['pinned']['forge_result']} (pinned), "
          f"{forge['set2']['forge_result']} (set2); sweep {sweep['summary']['calls']} calls over "
          f"{sweep['summary']['selectors_swept']} selectors; {len(caps['fit_rows'])} cap-fit rows")


if __name__ == "__main__":
    main()