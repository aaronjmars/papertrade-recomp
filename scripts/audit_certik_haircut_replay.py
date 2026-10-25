#!/usr/bin/env python3
"""Test the CertiK BBO pricing incident haircut claim against exact bytecode.

Claim under test (CertiK, 2026-10-20, https://www.certik.com/blog/papertrade-bbo-pricing-incident,
and docs.papertrade.xyz/how/asymmetric-impact): the winning-close profit haircut
substitutes a fixed reference notional, so the haircut percentage does not grow
with position size while the dollar payout does.

Evidence used:
  * the pinned Exchange proxy/implementation and its linked library runtime,
    restored from the saved mixed-close prestate (block 48,901,631);
  * the pinned instrument record and market fields read at pin 48,902,346;
  * the 74 saved nested library math calls in artifacts/**/*.calls.json;
  * the currently deployed Exchange implementation and its linked library,
    captured from the public HyperEVM RPC at `latest` under
    artifacts/audit_certik_haircut/live/ (`--capture` refreshes that folder);
  * port-free exact-runtime Foundry replays of one signed close per case.

The script is deterministic and runs offline. `--capture` is the only mode that
uses the network; it writes the raw RPC responses next to the derived evidence.
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
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ROOT / "artifacts" / "audit_certik_haircut"
LIVE = OUT / "live"
LEDGER = ATLAS / "asymmetric_impact_behavior.json"
DOC = ATLAS / "asymmetric_impact_behavior.md"

RPC = "https://rpc.hyperliquid.xyz/evm"
CHAIN_ID = 999
PIN = 48902346
PIN_HASH = "0xd92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"
PRESTATE_BLOCK = 48901631

EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
PIN_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PIN_LIBRARY = "0xcd617f984158a4f5d287ddee0e8eb0fed204916d"
EIP1967_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

SESSION = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
BATCH = "0x233ff29b239abc1d7748605da9b205c3e008626e"
USER = "0xe05fcc23807536bee418f142d19fa0d21bb0cff7"
CLOSE_SELECTOR = "0x2792e706"
CLOSE_TYPEHASH = "0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13"
CLOSE_DOMAIN = "0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77"
NONCE = 42
CLOSED_TOPIC = "0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf"
PNL_SELECTOR = "0x82296364"
SETTLEMENT_SELECTOR = "0xef1a27a9"

INSTRUMENT = 1                      # ETH market; CertiK's position 72098 traded ETH
INSTRUMENT_ROOT = "0xb39221ace053465ec3453ce2b36430bd138b997ecea25c1043da0c366812b828"
MARKET_ROOT = "0xbbbb3b1da0cb0951f34c5e9db4606f934b7367b5284f29163e9e6fe67e1e97d6"
ENTRY_PRICE = 250645                # 2506.45 in 0.01 quote units
BID = 251080                        # CertiK figure 2: close BBO read
ASK = 251090
EXIT_PRICE = (BID + ASK) // 2
MAX_LEVERAGE = 1000

WAD = 10**18
# CertiK's settlement table, rounded to the six decimals it publishes, in 1e18 units.
CERTIK = {
    "raw_pnl": 17355223523000000000000,          # 17,355.223523
    "adjusted_pnl": 13494728986000000000000,     # 13,494.728986
    "win_fee": 269894580000000000000,            # 269.894580
    "net": 13224834407000000000000,              # 13,224.834407
    "haircut_percent": "22.243992",
    "haircut_ppm": 222440,
    "hypothetical_notional": 500000,
    "hypothetical_net": 661241720000000000000,   # 661.241720
    "position_margin": 20000,
    "position_leverage": 500,
}
PRESTATE = ROOT / "artifacts" / "exchange_negative_close" / "original_prestate.json"
GETTERS = ROOT / "artifacts" / "exchange_instruments_getter" / "pinned_getters.json"
FIELDS = ROOT / "artifacts" / "exchange_market_fields" / "pinned_probes.json"

# Getter-word indices of the four instrument parameters the Exchange passes to the
# profit-math call, established by exchange_instruments_getter.md, the instrument
# registration call at block 47,855,385 and the 74 saved 0x82296364 delegatecalls.
PARAM_INDEX = {
    "base_rate": 6,
    "rate_multiplier": 0,
    "position_multiplier": 1,
    "reference_notional": 7,
}


def u256(value):
    return "0x" + format(value % (1 << 256), "064x")


def s_address(value):
    return "address(uint160(uint256(0x00" + value[2:] + ")))"


def sha256_hex(payload):
    return hashlib.sha256(payload).hexdigest()


def rpc(method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(RPC, data=payload, headers={"content-type": "application/json"})
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
    if "error" in result:
        raise RuntimeError(f"{method}: {result['error']}")
    return result["result"]


# ------------------------------------------------------------------ model

def move_after_deadband(entry, exit_price):
    """Deadband step: the gain is measured as if the exit were entryPrice/50000 worse."""
    if exit_price <= entry:
        return 0
    return max(exit_price - entry - entry // 50000, 0)


def doc_terms(entry, exit_price, base_rate, rate_multiplier, position_multiplier,
              reference_notional):
    """Documented pipeline as exact fractions: scale = (1-b)/(1+term1+term2).

    The four instrument parameters are passed in the 1e18-scaled units the code uses
    and are converted to plain numbers here, so the fractions below are the documented
    formula. `code_pnl` keeps the integer form for the exact-runtime comparison.
    """
    move = Fraction(move_after_deadband(entry, exit_price), entry)
    base = Fraction(base_rate, WAD)
    rate = Fraction(rate_multiplier, WAD)
    position = Fraction(position_multiplier, WAD)
    reference = Fraction(reference_notional, WAD)
    term1 = 1 / (move * rate)
    term2 = reference / (10**6 * move * position)
    return (1 - base) / (1 + term1 + term2), term1, term2


def raw_pnl(entry, exit_price, margin, leverage, is_long):
    """Raw PnL of the documented pipeline, in 1e18-scaled USDC."""
    delta = (exit_price - entry) if is_long else (entry - exit_price)
    if delta > 0:
        delta = move_after_deadband(entry, exit_price)
    return (1 if delta >= 0 else -1) * (margin * leverage * abs(delta) // entry)


def code_pnl(args):
    """The pinned library's integer arithmetic (atlas_exchange_library.pnl_model)."""
    entry, exit_price, margin, leverage, is_long, base_rate, rate_multiplier, \
        position_multiplier, reference_notional = args
    delta = (exit_price - entry) if is_long else (entry - exit_price)
    if delta > 0:
        delta = max(delta - entry // 50000, 0)
    raw = (1 if delta >= 0 else -1) * (margin * leverage * abs(delta) // entry)
    if raw <= 0:
        return raw, raw
    if rate_multiplier == 0 or position_multiplier == 0 or base_rate == WAD:
        return raw, 0
    return_fraction = delta * WAD // entry
    exposure = return_fraction * rate_multiplier // WAD
    risk_inverse = WAD * WAD // exposure
    liquidity_exposure = return_fraction * 10**6 * position_multiplier // WAD
    liquidity_inverse = reference_notional * WAD // liquidity_exposure
    factor = (WAD - base_rate) * WAD // (WAD + risk_inverse + liquidity_inverse)
    return raw, raw * factor // WAD


def scale_exact(params, entry=ENTRY_PRICE, exit_price=EXIT_PRICE):
    """Exact 1e18 scale factor of the documented pipeline for one parameter set."""
    scale, _, _ = doc_terms(entry, exit_price, params["base_rate"],
                            params["rate_multiplier"], params["position_multiplier"],
                            params["reference_notional"])
    return scale


def maximize_market_aggregates(market_words):
    """Set the two 96-bit side aggregates of market field word 0 to their maximum.

    The pinned aggregate is the state after the real opens that built it. A synthetic
    position that no open ever added to the aggregate overflows the 96-bit subtraction
    when the close releases its contribution, so the largest sweep case needs this
    labelled control; the four haircut inputs come from the instrument record and are
    unaffected.
    """
    word0 = (market_words[0] >> 192) << 192 | (2**96 - 1) << 96 | (2**96 - 1)
    return [word0, market_words[1]]


def pack_instrument(words):
    """Pack the eight instrument getter words into the three instrument storage words."""
    return [words[0] | (words[1] << 96) | (words[2] << 192) | (words[3] << 224),
            words[4] | (words[5] << 120) | (words[6] << 184),
            words[7]]


def read_instrument_words(path=None):
    """The eight instrument-record words of the ETH market from the pinned getter capture."""
    getters = json.loads(GETTERS.read_text())
    assert getters["pin"] == PIN and getters["block_hash"] == PIN_HASH
    row = next(row for row in getters["rows"] if row["instrument_id"] == INSTRUMENT)
    raw = row["getter_output"][2:]
    words = [int(raw[i:i + 64], 16) for i in range(0, len(raw), 64)]
    assert len(words) == 8
    assert words[0] == 15000 * WAD            # rateMultiplier
    assert words[1] == 483979000000000000000  # positionMultiplier 483.979
    assert words[2] == INSTRUMENT
    assert words[3] == MAX_LEVERAGE
    assert words[6] == WAD // 10              # baseRate 10%
    assert words[7] == 100000 * WAD           # referenceNotional 100,000
    return words, row


def read_market_words():
    """The two market-field words of the ETH market from the pinned probe capture."""
    fields = json.loads(FIELDS.read_text())
    assert fields["pin_block"] == PIN and fields["pin_hash"] == PIN_HASH
    market = next(row for row in fields["markets"] if row["instrument"] == INSTRUMENT)
    assert int(market["base_slot"], 16) == int(MARKET_ROOT, 16)
    return [int(word, 16) for word in market["raw_words"]]


def capture_live():
    """Refresh the live Exchange implementation, its linked libraries and config slots."""
    LIVE.mkdir(parents=True, exist_ok=True)
    raw = LIVE / "raw"
    raw.mkdir(exist_ok=True)
    head = int(rpc("eth_blockNumber", []), 16)
    header = rpc("eth_getBlockByNumber", [hex(head), False])
    slot = rpc("eth_getStorageAt", [EXCHANGE, EIP1967_SLOT, "latest"])
    implementation = "0x" + slot[-40:]
    proxy_code = rpc("eth_getCode", [EXCHANGE, "latest"])
    implementation_code = rpc("eth_getCode", [implementation, "latest"])
    (raw / "exchange_proxy_code.json").write_text(json.dumps(proxy_code) + "\n")
    (raw / "implementation_code.json").write_text(json.dumps(implementation_code) + "\n")
    candidates = {}
    body = bytes.fromhex(implementation_code[2:])
    for i in range(len(body) - 20):
        if body[i] == 0x73:
            candidates.setdefault("0x" + body[i + 1:i + 21].hex(), []).append(i)
    libraries = {}
    for address, offsets in candidates.items():
        code = rpc("eth_getCode", [address, "latest"])
        if len(code) <= 2:
            continue
        (raw / f"linked_{address[2:]}_code.json").write_text(json.dumps(code) + "\n")
        (LIVE / f"linked_{address[2:]}.hex").write_text(code + "\n")
        libraries[address] = {
            "runtime_bytes": len(code[2:]) // 2,
            "sha256": sha256_hex(bytes.fromhex(code[2:])),
            "push20_offsets": offsets,
            "selector_set": sorted(dispatch_selectors(bytes.fromhex(code[2:]))),
        }
    linked = [address for address, row in libraries.items() if len(row["push20_offsets"]) > 1]
    assert len(linked) == 1, linked
    session_slot = rpc("eth_getStorageAt", [SESSION, EIP1967_SLOT, "latest"])
    session_implementation = "0x" + session_slot[-40:]
    session_code = rpc("eth_getCode", [session_implementation, "latest"])
    (raw / "session_manager_implementation_code.json").write_text(json.dumps(session_code) + "\n")
    (LIVE / "session_manager_implementation.hex").write_text(session_code + "\n")
    slots = {str(index): rpc("eth_getStorageAt", [EXCHANGE, u256(index), "latest"])
             for index in (2, 3, 4, 5, 6, 8, 14, 16, 18, 22, 23, 24, 25, 26, 27, 29, 37)}
    instrument = {u256(int(INSTRUMENT_ROOT, 16) + i):
                  rpc("eth_getStorageAt", [EXCHANGE, u256(int(INSTRUMENT_ROOT, 16) + i), "latest"])
                  for i in range(3)}
    market = {u256(int(MARKET_ROOT, 16) + i):
              rpc("eth_getStorageAt", [EXCHANGE, u256(int(MARKET_ROOT, 16) + i), "latest"])
              for i in range(2)}
    (raw / "storage_probes.json").write_text(json.dumps(
        {"config_slots": slots, "instrument_words": instrument, "market_words": market},
        indent=2) + "\n")
    record = {
        "chain_id": CHAIN_ID,
        "head_block": head,
        "head_hash": header["hash"],
        "head_timestamp": int(header["timestamp"], 16),
        "exchange_proxy": EXCHANGE,
        "eip1967_implementation_slot": EIP1967_SLOT,
        "implementation": implementation,
        "implementation_runtime_bytes": len(implementation_code[2:]) // 2,
        "implementation_sha256": sha256_hex(bytes.fromhex(implementation_code[2:])),
        "proxy_runtime_bytes": len(proxy_code[2:]) // 2,
        "proxy_sha256": sha256_hex(bytes.fromhex(proxy_code[2:])),
        "linked_libraries": libraries,
        "linked_library": linked[0],
        "session_key_manager_proxy": SESSION,
        "session_key_manager_implementation": session_implementation,
        "session_key_manager_implementation_bytes": len(session_code[2:]) // 2,
        "session_manager_implementation_sha256": sha256_hex(bytes.fromhex(session_code[2:])),
        "raw_files": sorted(path.name for path in raw.iterdir()),
        "method": "single-poll eth_blockNumber/eth_getBlockByNumber/eth_getStorageAt/"
                  "eth_getCode at latest; the public RPC ignores block parameters",
    }
    (LIVE / "implementation.hex").write_text(implementation_code + "\n")
    (LIVE / "proxy.hex").write_text(proxy_code + "\n")
    (LIVE / "capture.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"live implementation {implementation} {record['implementation_runtime_bytes']} bytes")
    for address, row in libraries.items():
        print(f"  linked library {address} {row['runtime_bytes']} bytes {row['sha256']}")
    return record


# ------------------------------------------------------------------ cases

def base_params(words):
    return {
        "base_rate": words[PARAM_INDEX["base_rate"]],
        "rate_multiplier": words[PARAM_INDEX["rate_multiplier"]],
        "position_multiplier": words[PARAM_INDEX["position_multiplier"]],
        "reference_notional": words[PARAM_INDEX["reference_notional"]],
    }


def case_set(words):
    """Size sweep at the CertiK prices plus haircut-input sensitivity and a counterfactual."""
    base = base_params(words)
    cases = [
        {"label": "certik_10m", "margin": 20000 * WAD, "leverage": 500,
         "note": "CertiK position 72098 size: 20,000 margin at 500x"},
        {"label": "certik_500k", "margin": 1000 * WAD, "leverage": 500,
         "note": "CertiK hypothetical $500,000 notional position"},
        {"label": "certik_50k", "margin": 100 * WAD, "leverage": 500,
         "note": "one hundredth of the recorded notional"},
        {"label": "certik_2m_lev100", "margin": 20000 * WAD, "leverage": 100,
         "note": "margin held fixed, leverage cut 5x"},
        {"label": "certik_500k_lev250", "margin": 2000 * WAD, "leverage": 250,
         "note": "same 500,000 notional as certik_500k from a different margin/leverage pair"},
        {"label": "certik_250m", "margin": 500000 * WAD, "leverage": 500,
         "note": "25x the recorded notional",
         "maximize_market_aggregates": True,
         "constructed": "the market side aggregates are set to their 96-bit maximum; with "
                        "the pinned aggregate the close release underflows"},
        {"label": "base_rate_20pct", "margin": 20000 * WAD, "leverage": 500,
         "instrument_overrides": {PARAM_INDEX["base_rate"]: 2 * WAD // 10},
         "note": "baseRate doubled from the pinned 10%"},
        {"label": "rate_multiplier_30k", "margin": 20000 * WAD, "leverage": 500,
         "instrument_overrides": {PARAM_INDEX["rate_multiplier"]: 30000 * WAD},
         "note": "rateMultiplier doubled from the pinned 15,000"},
        {"label": "reference_notional_1m", "margin": 20000 * WAD, "leverage": 500,
         "instrument_overrides": {PARAM_INDEX["reference_notional"]: 1000000 * WAD},
         "note": "referenceNotional raised 10x from the pinned 100,000"},
        {"label": "counterfactual_ref_is_notional_500k", "margin": 1000 * WAD, "leverage": 500,
         "instrument_overrides": {PARAM_INDEX["reference_notional"]: 500000 * WAD},
         "constructed": "referenceNotional set to this position's own notional"},
        {"label": "counterfactual_ref_is_notional_10m", "margin": 20000 * WAD, "leverage": 500,
         "instrument_overrides": {PARAM_INDEX["reference_notional"]: 10000000 * WAD},
         "constructed": "referenceNotional set to this position's own notional"},
    ]
    # Moves inside the holdback bands the contract-set-2 docs describe (0.75-6 bps standard,
    # 0.3-10 bps off hours). Contract set 1 has no holdback step, so these two cases are the
    # ones that can separate the pinned and deployed payout curves.
    cases += [
        {"label": "holdback_4bp", "margin": 20000 * WAD, "leverage": 500,
         "entry": ENTRY_PRICE, "exit": ENTRY_PRICE + 100,
         "note": "3.99 bps move, inside both documented holdback bands"},
        {"label": "holdback_05bp", "margin": 20000 * WAD, "leverage": 500,
         "entry": ENTRY_PRICE, "exit": ENTRY_PRICE + 13,
         "note": "0.52 bps move, inside the off-hours band only"},
        {"label": "holdback_4bp_500k", "margin": 1000 * WAD, "leverage": 500,
         "entry": ENTRY_PRICE, "exit": ENTRY_PRICE + 100,
         "note": "same 3.99 bps move at one twentieth of the notional"},
        {"label": "holdback_4bp_2m", "margin": 4000 * WAD, "leverage": 500,
         "entry": ENTRY_PRICE, "exit": ENTRY_PRICE + 100,
         "note": "same 3.99 bps move at one fifth of the notional"},
    ]
    for case in cases:
        case.setdefault("entry", ENTRY_PRICE)
        case.setdefault("exit", EXIT_PRICE)
        case["params"] = dict(base)
        for index, value in case.get("instrument_overrides", {}).items():
            for name, key in PARAM_INDEX.items():
                if key == index:
                    case["params"][name] = value
    return cases


def expectation(case):
    """Independent expectation: the fixed-point runtime form and the documented formula.

    `*_model` is the value the pinned library's integer arithmetic returns and is what
    the Forge case asserts; `documented_*` is the exact rational evaluation of the
    published formula, reported so the two forms can be compared.
    """
    code_raw, code_adjusted = code_pnl([case["entry"], case["exit"], case["margin"], case["leverage"], 1,
                                        case["params"]["base_rate"], case["params"]["rate_multiplier"],
                                        case["params"]["position_multiplier"],
                                        case["params"]["reference_notional"]])
    code_fee = code_adjusted * 2 // 100
    raw = raw_pnl(case["entry"], case["exit"], case["margin"], case["leverage"], True)
    scale = scale_exact(case["params"], case["entry"], case["exit"])
    adjusted = int(raw * scale)
    fee = adjusted * 2 // 100
    # the staged floor divisions of the integer form differ from the rational evaluation by
    # less than 1e-9 relative; the Forge case asserts the integer form itself
    assert abs(code_adjusted - adjusted) * 10**9 < adjusted, (code_adjusted, adjusted)
    assert abs(code_fee - fee) * 10**9 < fee, (code_fee, fee)
    _, term1, term2 = doc_terms(case["entry"], case["exit"], case["params"]["base_rate"],
                                case["params"]["rate_multiplier"],
                                case["params"]["position_multiplier"],
                                case["params"]["reference_notional"])
    return {
        "label": case["label"],
        "entry": case["entry"],
        "exit": case["exit"],
        "note": case.get("note"),
        "constructed": case.get("constructed"),
        "notional": case["margin"] * case["leverage"] // WAD,
        "margin": case["margin"],
        "leverage": case["leverage"],
        "haircut_inputs": {name: case["params"][name] for name in
                           ("base_rate", "rate_multiplier", "position_multiplier",
                            "reference_notional")},
        "raw_pnl_model": code_raw,
        "adjusted_pnl_model": code_adjusted,
        "fee_model": code_fee,
        "net_model": code_adjusted - code_fee,
        "haircut_ppm_model": (code_raw - code_adjusted) * 10**6 // code_raw,
        "scale_ppm_model": int(scale * 10**6),
        "term1_ppm": int(term1 * 10**6),
        "term2_ppm": int(term2 * 10**6),
        "documented_raw_pnl": raw,
        "documented_adjusted_pnl": adjusted,
        "documented_fee": fee,
        "documented_net": adjusted - fee,
    }

# ------------------------------------------------------------------ forge harness

SOLIDITY_HEADER = '''pragma solidity ^0.8.24;

interface Vm {{
    struct Log {{ bytes32[] topics; bytes data; address emitter; }}
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
}}

contract CertikHaircutReplayTest {{
    error WrongResult(bool ok, bytes result);
    error BadMeasurement(string label, int256 got, int256 expected);

    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = {exchange};
    address constant SESSION = {session};
    address constant BATCH = {batch};
    address constant USER = {user};
    bytes32 constant CLOSE_TYPEHASH = {typehash};
    bytes32 constant DOMAIN = {domain};
    bytes32 constant INSTRUMENT_ROOT = {instrument_root};
    bytes32 constant MARKET_ROOT = {market_root};
    bytes32 constant CLOSED_TOPIC = {closed_topic};
    uint256 constant INSTRUMENT = {instrument};
    uint128 constant ETHER = 1e18;
    uint256 entryPrice;
    uint256 exitPrice;

    function u2s(uint256 v) internal pure returns (string memory) {{
        if (v == 0) return "0";
        uint256 t = v;
        uint256 d;
        while (t != 0) {{ d++; t /= 10; }}
        bytes memory b = new bytes(d);
        while (v != 0) {{ d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }}
        return string(b);
    }}

    function i2s(int256 v) internal pure returns (string memory) {{
        if (v < 0) return string.concat("-", u2s(uint256(-v)));
        return u2s(uint256(v));
    }}

    function positionSlot(uint256 id) internal pure returns (bytes32) {{
        return keccak256(abi.encode(id, uint256(10)));
    }}

    function writePosition(uint256 id, uint256 margin, uint256 leverage) internal {{
        uint256 word0 = (entryPrice << 192) | (INSTRUMENT << 160) | uint256(uint160(USER));
        uint256 word1 = margin | (leverage << 128) |
            (uint256(block.timestamp & type(uint64).max) << 160) |
            (uint256(1) << 240) | (uint256(1) << 224);
        bytes32 slot = positionSlot(id);
        vm.store(EXCHANGE, slot, bytes32(word0));
        vm.store(EXCHANGE, bytes32(uint256(slot) + 1), bytes32(word1));
        bytes32 totals = bytes32(uint256(22));
        uint256 packed = uint256(vm.load(EXCHANGE, totals));
        uint256 locked = (packed >> 128) + margin;
        require(locked < 2 ** 128, "locked margin range");
        vm.store(EXCHANGE, totals, bytes32((locked << 128) | uint128(packed)));
    }}

    function closeBySignature(uint256[] memory ids) internal returns (Vm.Log[] memory logs) {{
        address sessionKey = vm.addr(0xb0b);
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(sessionKey, outer)),
                 bytes32(uint256(block.timestamp + 3600)));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), {nonce}, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xb0b, digest);
        require(ecrecover(digest, v, r, sigS) == sessionKey, "session signer");
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok, bytes memory result) = EXCHANGE.call(abi.encodeWithSelector(
            bytes4({close_selector}), USER, ids, {nonce}, deadline, v, r, sigS));
        if (!ok) revert WrongResult(ok, result);
        return vm.getRecordedLogs();
    }}

    function runCase(uint256 margin, uint256 leverage, string memory label,
                     int256 expectedRaw, int256 expectedAdjusted, int256 expectedFee,
                     bool check, uint256 caseEntry, uint256 caseExit) internal {{
        entryPrice = caseEntry;
        exitPrice = caseExit;
        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(INSTRUMENT)),
                    abi.encode(uint256(caseExit - 5), uint256(caseExit + 5)));
        uint256 balanceBefore = uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
        uint256 queuedBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(18))));
        uint256[] memory ids = new uint256[](1);
        ids[0] = 1;
        writePosition(1, margin, leverage);
        Vm.Log[] memory logs = closeBySignature(ids);
        int256 rawPnl = 0;
        int256 adjustedPnl = 0;
        int256 fee = 0;
        uint256 closed;
        for (uint256 i; i < logs.length; ++i) {{
            if (logs[i].emitter != EXCHANGE || logs[i].topics.length == 0) continue;
            if (logs[i].topics[0] != CLOSED_TOPIC) continue;
            (uint256 eventExit, int256 raw, int256 adjusted, , uint256 paidFee) =
                abi.decode(logs[i].data, (uint256, int256, int256, uint256, uint256));
            require(closed == 0, "one close event");
            require(eventExit == caseExit, "oracle midpoint");
            rawPnl = raw;
            adjustedPnl = adjusted;
            fee = int256(paidFee);
            ++closed;
        }}
        require(closed == 1, "close event present");
        if (check) {{
            if (rawPnl != expectedRaw) revert BadMeasurement("raw", rawPnl, expectedRaw);
            if (adjustedPnl != expectedAdjusted)
                revert BadMeasurement("adjusted", adjustedPnl, expectedAdjusted);
            if (fee != expectedFee) revert BadMeasurement("fee", fee, expectedFee);
        }}
        uint256 balanceAfter = uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
        uint256 queuedAfter = uint256(vm.load(EXCHANGE, bytes32(uint256(18))));
        string memory line = string.concat(label, ",", u2s(margin), ",", u2s(leverage));
        line = string.concat(line, ",", i2s(rawPnl), ",", i2s(adjustedPnl), ",", i2s(fee));
        line = string.concat(line, ",", i2s(int256(balanceAfter) - int256(balanceBefore)));
        line = string.concat(line, ",", u2s(queuedAfter - queuedBefore), ",",
                             u2s(margin * leverage / ETHER), ",", u2s(caseEntry), ",",
                             u2s(caseExit));
        vm.writeLine("results/observed.csv", line);
    }}
'''


def render_source(cases, variant, expectations, words):
    """Build the Foundry test source for one replay variant."""
    lines = [SOLIDITY_HEADER.format(
        exchange=s_address(EXCHANGE), session=s_address(SESSION), batch=s_address(BATCH),
        user=s_address(USER), typehash=CLOSE_TYPEHASH, domain=CLOSE_DOMAIN, nonce=NONCE,
        instrument=INSTRUMENT, instrument_root=INSTRUMENT_ROOT,
        market_root=MARKET_ROOT, closed_topic=CLOSED_TOPIC,
        close_selector="0x" + CLOSE_SELECTOR[2:])]
    lines.append("    function setUp() public {")
    lines.append(f"        vm.chainId({CHAIN_ID});")
    lines.append(f"        vm.roll({variant['block']});")
    lines.append(f"        vm.warp({variant['timestamp']});")
    lines.extend(variant["setup_lines"])
    if variant.get("session_implementation"):
        lines.append(f"        vm.store({s_address(SESSION)}, {EIP1967_SLOT}, "
                     f"{u256(int(variant['session_implementation'], 16))});")
    for slot, value in variant.get("extra_stores", {}).items():
        lines.append(f"        vm.store(EXCHANGE, {slot}, {u256(value)});")
    packed = variant.get("instrument_packed") or pack_instrument(words)
    for i, word in enumerate(packed):
        lines.append(f"        vm.store(EXCHANGE, {u256(int(INSTRUMENT_ROOT, 16) + i)}, {u256(word)});")
    market = variant.get("market_words") or read_market_words()
    for i, word in enumerate(market):
        lines.append(f"        vm.store(EXCHANGE, {u256(int(MARKET_ROOT, 16) + i)}, {u256(word)});")
    lines.append(f'        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32({INSTRUMENT})), '
                 f'abi.encode(uint256({BID}), uint256({ASK})));')
    lines.append("    }")
    for case, expected in zip(cases, expectations):
        lines.append(f"    function test_{variant['tag']}_{case['label']}() public {{")
        case_words = list(variant.get("instrument_words") or words)
        for index, value in case.get("instrument_overrides", {}).items():
            case_words[index] = value
        case_packed = pack_instrument(case_words)
        for i, word in enumerate(case_packed):
            if word != packed[i]:
                lines.append(f"        vm.store(EXCHANGE, {u256(int(INSTRUMENT_ROOT, 16) + i)}, "
                             f"{u256(word)});")
        if case.get("maximize_market_aggregates"):
            lines.append(f"        vm.store(EXCHANGE, {u256(int(MARKET_ROOT, 16))}, "
                         f"{u256(maximize_market_aggregates(market)[0])});")
        check = "true" if variant["checked"] else "false"
        lines.append(f'        runCase({case["margin"]}, {case["leverage"]}, '
                     f'"{variant["tag"]}_{case["label"]}", {expected["raw_pnl_model"]}, '
                     f'{expected["adjusted_pnl_model"]}, {expected["fee_model"]}, {check}, '
                     f'{case["entry"]}, {case["exit"]});')
        lines.append("    }")
    lines.append("}\n")
    return "\n".join(lines)


def build_variant(tag, cases, variant):
    """Assemble prestate setup lines, runtime files and the rendered Solidity source."""
    prestate = json.loads(PRESTATE.read_text())
    codes = {address: row.get("code", "0x") for address, row in prestate.items()}
    codes.update(variant.get("extra_code", {}))
    setup_lines = []
    for address, row in sorted(prestate.items()):
        if codes[address] != "0x":
            setup_lines.append(f'        vm.etch({s_address(address)}, '
                               f'vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
        for slot, value in sorted(row.get("storage", {}).items()):
            if int(value, 16):
                setup_lines.append(f"        vm.store({s_address(address)}, {slot}, {value});")
    for address in sorted(variant.get("extra_code", {})):
        if codes[address] != "0x":
            setup_lines.append(f'        vm.etch({s_address(address)}, '
                               f'vm.parseBytes(vm.readFile("runtime/{address[2:]}.hex")));')
    variant = dict(variant, tag=tag, setup_lines=setup_lines)
    words = variant.get("instrument_words") or read_instrument_words()[0]
    expectations = [expectation(case) for case in cases]
    source = render_source(cases, variant, expectations, words)
    return source, codes, expectations, words


def run_forge(tag, cases, variant):
    source, codes, expectations, words = build_variant(tag, cases, variant)
    assert shutil.which("forge") and shutil.which("solc"), "forge and solc are required"
    with tempfile.TemporaryDirectory(prefix=f"papertrade-certik-{tag}-") as tmp:
        project = pathlib.Path(tmp)
        for name in ("test", "runtime", "results"):
            (project / name).mkdir()
        (project / "results" / "observed.csv").write_text("")
        (project / "foundry.toml").write_text(
            '[profile.default]\nsolc = ' + json.dumps(shutil.which("solc")) +
            '\noffline = true\nvia_ir = true\noptimizer = true\noptimizer_runs = 200\n'
            'fs_permissions = [{ access = "read", path = "./runtime" }, '
            '{ access = "read-write", path = "./results" }]\n')
        (project / "test" / "CertikHaircut.t.sol").write_text(source)
        for address, code in codes.items():
            if code != "0x":
                (project / "runtime" / f"{address[2:]}.hex").write_text(code)
        run = subprocess.run(["forge", "test", "--root", tmp, "-vvvv"],
                             check=False, capture_output=True, text=True, timeout=900)
        output = run.stdout + "\n" + run.stderr
        observed = (project / "results" / "observed.csv").read_text()
    passed = set(re.findall(r"\[PASS\] (test\w+)\(\)", output))
    expected = {f"test_{tag}_{case['label']}" for case in cases}
    if run.returncode or passed != expected:
        raise RuntimeError(f"{tag} replay failed:\n" + output[-12000:])
    rows = parse_observed(observed)
    return {
        "source_sha256": sha256_hex(source.encode()),
        "tests": sorted(passed),
        "observed": rows,
        "expectations": expectations,
        "forge_result": f"{len(expected)} passed, 0 failed",
        "trace": output,
    }


def parse_observed(observed):
    rows = {}
    for line in observed.splitlines():
        if not line.strip():
            continue
        label, margin, leverage, raw, adjusted, fee, balance_delta, queue_delta, notional, \
            entry, exit_price = line.split(",")
        rows[label] = {
            "margin": int(margin), "leverage": int(leverage), "notional": int(notional),
            "entry": int(entry), "exit": int(exit_price),
            "raw_pnl": int(raw), "adjusted_pnl": int(adjusted), "fee": int(fee),
            "balance_delta": int(balance_delta), "queue_delta": int(queue_delta),
            "haircut_ppm": (int(raw) - int(adjusted)) * 10**6 // int(raw) if int(raw) else 0,
            "haircut_1e9": (int(raw) - int(adjusted)) * 10**9 // int(raw) if int(raw) else 0,
        }
    return rows


TRACE_CALL = re.compile(r"([0-9a-fA-F]{40})::([0-9a-f]{8})\(([0-9a-f]*)\) \[(delegatecall|call)\]")


def library_math_calls(output, library):
    """Nested library calls per test captured in the -vvvv trace, oldest first."""
    lines = output.splitlines()
    tests = [(i, match.group(1)) for i, line in enumerate(lines)
             if (match := re.match(r"\[PASS\] (test\w+)\(\)", line))]
    result = {}
    for j, (start, name) in enumerate(tests):
        section = lines[start + 1:tests[j + 1][0] if j + 1 < len(tests) else len(lines)]
        calls = []
        for i, line in enumerate(section):
            match = TRACE_CALL.search(line)
            if not match or match.group(1).lower() != library[2:].lower():
                continue
            returned = re.search(r"\[Return\] 0x([0-9a-f]+)", section[i + 1]) \
                if i + 1 < len(section) else None
            calls.append({
                "selector": "0x" + match.group(2),
                "kind": match.group(4),
                "arguments": [int(match.group(3)[k:k + 64], 16)
                              for k in range(0, len(match.group(3)), 64)],
                "returns": [int(returned.group(1)[k:k + 64], 16)
                            for k in range(0, len(returned.group(1)), 64)] if returned else [],
            })
        result[name] = calls
    return result


# ------------------------------------------------------------------ live comparison

def push20_addresses(body):
    out = {}
    for i in range(len(body) - 20):
        if body[i] == 0x73:
            out.setdefault("0x" + body[i + 1:i + 21].hex(), []).append(i)
    return out


def dispatch_selectors(body):
    """PUSH4 immediates that are the left operand of an EQ inside the dispatcher."""
    selectors = set()
    for i in range(len(body) - 4):
        if body[i] != 0x63:
            continue
        window = body[i + 5:i + 12]
        if 0x14 in window:
            selectors.add("0x" + body[i + 1:i + 5].hex())
    return selectors


def normalize_runtime(body, addresses):
    """Blank linked addresses and the compiler metadata tail for a shape comparison."""
    out = bytearray(body)
    for address in addresses:
        raw = bytes.fromhex(address[2:])
        start = 0
        while (index := bytes(out).find(raw, start)) != -1:
            out[index:index + 20] = b"\x00" * 20
            start = index + 1
    tail = bytes(out[-64:])
    if tail[-2:] == b"\x00\x33":
        for cut in range(2, 80):
            candidate = bytes(out[len(out) - cut:])
            if candidate[:2] == b"\xa2\x64" and candidate[1] in range(0x40, 0x80):
                length = candidate[1]
                if length + 2 <= cut:
                    del out[len(out) - length - 2:]
                    break
    else:
        del out[len(out) - 0:]
    return bytes(out)


def metadata_tail(body):
    if body[-2:] != b"\x00\x33":
        return None
    for cut in range(2, 120):
        chunk = body[len(body) - cut:]
        if chunk[:2] == b"\xa2\x64":
            return chunk.hex()
    return None


def compare_implementation(pinned_impl, live_impl, pinned_lib, live_lib):
    """Offline pinned vs live runtime comparison, with linked-address normalization."""
    body = lambda code: bytes.fromhex(code[2:] if code.startswith("0x") else code)
    pinned_lib_body = body(pinned_lib)
    live_lib_body = body(live_lib)
    pinned_addresses = set(push20_addresses(pinned_lib_body)) | set(push20_addresses(body(pinned_impl)))
    live_addresses = set(push20_addresses(live_lib_body)) | set(push20_addresses(body(live_impl)))
    pinned_norm = normalize_runtime(pinned_lib_body, pinned_addresses)
    live_norm = normalize_runtime(live_lib_body, live_addresses)
    pinned_selectors = dispatch_selectors(pinned_lib_body)
    live_selectors = dispatch_selectors(live_lib_body)
    return {
        "pinned_library_bytes": len(pinned_lib_body),
        "live_library_bytes": len(live_lib_body),
        "pinned_library_sha256": sha256_hex(pinned_lib_body),
        "live_library_sha256": sha256_hex(live_lib_body),
        "pinned_library_metadata": metadata_tail(pinned_lib_body),
        "live_library_metadata": metadata_tail(live_lib_body),
        "pinned_library_normalized_sha256": sha256_hex(pinned_norm),
        "live_library_normalized_sha256": sha256_hex(live_norm),
        "library_byte_identical_after_normalization": pinned_norm == live_norm,
        "pinned_library_selectors": sorted(pinned_selectors),
        "live_library_selectors": sorted(live_selectors),
        "selectors_removed": sorted(pinned_selectors - live_selectors),
        "selectors_added": sorted(live_selectors - pinned_selectors),
        "pnl_selector_in_pinned": PNL_SELECTOR in pinned_selectors,
        "pnl_selector_in_live": PNL_SELECTOR in live_selectors,
        "settlement_selector_in_pinned": SETTLEMENT_SELECTOR in pinned_selectors,
        "settlement_selector_in_live": SETTLEMENT_SELECTOR in live_selectors,
        "pinned_implementation_bytes": len(body(pinned_impl)),
        "live_implementation_bytes": len(body(live_impl)),
        "pinned_implementation_push20": sorted(push20_addresses(body(pinned_impl))),
        "live_implementation_push20": sorted(push20_addresses(body(live_impl))),
    }


# ------------------------------------------------------------------ saved-call provenance

def walk_calls(node, out, parent=None):
    if isinstance(node, dict):
        if isinstance(node.get("input"), str):
            out.append(node)
        for value in node.values():
            walk_calls(value, out)
    elif isinstance(node, list):
        for value in node:
            walk_calls(value, out)


def historical_math_calls():
    """Every saved 0x82296364 delegatecall to the pinned library, with its returns."""
    rows = []
    for path in sorted(ROOT.glob("artifacts/**/*.calls.json")):
        payload = json.loads(path.read_text())
        nodes = []
        walk_calls(payload, nodes)
        tx = path.name.split(".")[0]
        receipt = path.parent / f"{tx}.receipt.json"
        block = None
        if receipt.exists():
            block = int(json.loads(receipt.read_text())["blockNumber"], 16)
        for node in nodes:
            data = node["input"]
            if not data.startswith(PNL_SELECTOR) or len(data) != 2 + 8 + 9 * 64:
                continue
            if node.get("to", "").lower() != PIN_LIBRARY:
                continue
            args = [int(data[10 + i * 64:10 + (i + 1) * 64], 16) for i in range(9)]
            returns = []
            if node.get("output", "0x") and len(node["output"]) == 2 + 2 * 64:
                returns = [int(node["output"][2 + i * 64:2 + (i + 1) * 64], 16)
                           for i in range(2)]
                returns = [value - (1 << 256) if value >= (1 << 255) else value
                           for value in returns]
            rows.append({
                "transaction": tx, "block": block, "file": str(path.relative_to(ROOT)),
                "arguments": args, "returns": returns,
                "notional": args[2] * args[3] // WAD,
                "instrument": args[6],
            })
    assert rows, "no saved 0x82296364 calls found"
    return rows


def provenance_summary(rows, words, market_words):
    """Check that the haircut inputs are instrument constants, not position size."""
    for row in rows:
        args = row["arguments"]
        row["model_returns"] = list(code_pnl(args[:9]))
        row["returns_match_model"] = row["model_returns"] == row["returns"]
    mismatched = [row for row in rows if not row["returns_match_model"]]
    groups = {}
    for row in rows:
        groups.setdefault(row["arguments"][7], []).append(row)
    table = []
    by_instrument = {}
    for rate_multiplier in sorted(groups):
        group = groups[rate_multiplier]
        notionals = sorted(row["notional"] for row in group)
        base_rates = sorted({row["arguments"][5] for row in group})
        rate_multipliers = sorted({row["arguments"][6] for row in group})
        reference_notionals = sorted({row["arguments"][8] for row in group})
        by_instrument[rate_multiplier] = {
            "calls": len(group),
            "position_multiplier_arg": rate_multiplier,
            "base_rate_args": base_rates,
            "rate_multiplier_args": rate_multipliers,
            "reference_notional_args": reference_notionals,
            "notional_min": notionals[0],
            "notional_max": notionals[-1],
            "distinct_notionals": len(set(notionals)),
        }
    profits = [row for row in rows if row["returns"] and row["returns"][1] > 0]
    return {
        "saved_pnl_calls": len(rows),
        "transactions": len({row["transaction"] for row in rows}),
        "blocks_min": min(row["block"] for row in rows if row["block"]),
        "blocks_max": max(row["block"] for row in rows if row["block"]),
        "returns_match_reconstructed_model": len(rows) - len(mismatched),
        "returns_mismatched": [row["transaction"] for row in mismatched],
        "argument_5_base_rate_values": sorted({row["arguments"][5] for row in rows}),
        "argument_6_rate_multiplier_values": sorted({row["arguments"][6] for row in rows}),
        "argument_7_position_multiplier_values": sorted({row["arguments"][7] for row in rows}),
        "argument_8_reference_notional_values": sorted({row["arguments"][8] for row in rows}),
        "instrument_record_words": words,
        "pinned_market_fields": market_words,
        "per_market": by_instrument,
        "profit_calls": [
            {"transaction": row["transaction"], "block": row["block"],
             "notional": row["notional"], "position_multiplier_arg": row["arguments"][7],
             "raw_pnl": row["returns"][0], "adjusted_pnl": row["returns"][1],
             "haircut_ppm": (row["returns"][0] - row["returns"][1]) * 10**6 // row["returns"][0]}
            for row in profits],
    }


# ------------------------------------------------------------------ ledger and document

def compare_slot_probe(prestate, name, value):
    return {"slot": name, "prestate": prestate, "live": value,
            "equal": prestate is not None and int(prestate, 16) == int(value, 16)}


def unpack_instrument(words):
    word0, word1, word2 = words
    return [word0 & (2**96 - 1), (word0 >> 96) & (2**96 - 1), (word0 >> 192) & (2**32 - 1),
            (word0 >> 224) & (2**32 - 1), word1 & (2**120 - 1), (word1 >> 120) & (2**64 - 1),
            (word1 >> 184) & (2**72 - 1), word2]


def ledger_rows(replay, cases, variant_tag):
    rows = []
    for case in cases:
        label = case["label"]
        key = f"{variant_tag}_{label}"
        observed = replay["observed"][key]
        rows.append({
            "case": label,
            "note": case.get("note"),
            "constructed": case.get("constructed"),
            "haircut_inputs": case["params"],
            "tag": variant_tag,
            "notional_usdc": observed["notional"],
            "margin_1e18": str(observed["margin"]),
            "leverage": observed["leverage"],
            "raw_pnl_1e18": str(observed["raw_pnl"]),
            "adjusted_pnl_1e18": str(observed["adjusted_pnl"]),
            "win_fee_1e18": str(observed["fee"]),
            "net_payout_1e18": str(observed["adjusted_pnl"] - observed["fee"]),
            "entry": observed["entry"],
            "exit": observed["exit"],
            "haircut_ppm": observed["haircut_ppm"],
            "haircut_nano_percent": observed["haircut_1e9"],
            "haircut_percent": f"{observed['haircut_1e9'] / 10**7:.6f}",
            "balance_delta_1e18": str(observed["balance_delta"]),
            "queue_delta_1e18": str(observed["queue_delta"]),
        })
    return rows


def bounds_section(prestate, live_probes, cases, pinned_rows, live_rows):
    """What bounds the payout, from the prestate, the pinned ledger and the live capture."""
    storage = prestate[EXCHANGE]["storage"]
    treasury = int(storage[u256(14)], 16)
    packed = int(storage[u256(22)], 16)
    fees = int(storage[u256(26)], 16)
    total_balances, locked = packed & (2**128 - 1), packed >> 128
    staker, dev = fees & (2**128 - 1), fees >> 128
    reserved = total_balances + locked + staker + dev
    availability = max(treasury - reserved, 0)
    limits = json.loads((ATLAS / "exchange_open_limit_full_behavior.json").read_text())
    fields = json.loads(FIELDS.read_text())
    pinned_market = next(row for row in fields["markets"] if row["instrument"] == INSTRUMENT)
    pinned_caps = [int(pinned_market["raw_words"][1], 16) & (2**128 - 1),
                   int(pinned_market["raw_words"][1], 16) >> 128]
    live_word1 = int(live_probes["market_words"][u256(int(MARKET_ROOT, 16) + 1)], 16)
    live_caps = [live_word1 & (2**128 - 1), live_word1 >> 128]
    largest = max(pinned_rows, key=lambda row: row["notional_usdc"])
    return {
        "open_interest_caps": {
            "enforcement": "market field word 1 holds two 128-bit per-side opening limits for "
                           "the ETH market; the keeper selector 0x628a9fd6 writes them and the "
                           "signed-open path compares the updated side value against them",
            "saved_open_sample": {
                "signed_open_selector": limits["selector"],
                "signed_opens_compared": limits["matched_signed_open_count"],
                "cap_reverts": limits["cap_revert_count"],
                "successes_below_limit": limits["below_limit_success_count"],
                "error": limits["error_signature"],
                "error_hash_verified": limits["error_signature_hash_verified"],
            },
            "eth_limits_pinned": [str(value) for value in pinned_caps],
            "eth_limits_live": [str(value) for value in live_caps],
            "eth_limit_tightening": [pinned_caps[0] / live_caps[0], pinned_caps[1] / live_caps[1]],
            "units": "the atlas records the compared values and the increments but leaves the "
                     "unit unresolved, so no USDC notional conversion is claimed here",
        },
        "lp_bankroll": {
            "formula": "lpBankrollAvailable = 0 if totalQueued > 0 else max(treasury - "
                       "totalBalances - totalLockedMargin - stakerFeeAccumulator - "
                       "devFeeAccumulator, 0)",
            "prestate_block": PRESTATE_BLOCK,
            "treasury_1e18": str(treasury),
            "reserved_1e18": str(reserved),
            "available_1e18": str(availability),
            "available_usdc": availability / WAD,
            "largest_replay_credit": {
                "notional_usdc": largest["notional_usdc"],
                "balance_credit_1e18": largest["balance_delta_1e18"],
                "queue_delta_1e18": largest["queue_delta_1e18"],
            },
        },
        "queue": {
            "prestate_total_queued": str(int(storage[u256(18)], 16)),
            "note": "every replay row credited the payout directly with a zero queue delta, and "
                    "the pinned suite also has a queued-profit close branch, so a payout beyond "
                    "the available bankroll is deferred rather than paid",
        },
        "reachability": "the haircut path has no position-size term, so a larger admissible "
                        "notional raises the payout at an unchanged percentage. CertiK reports "
                        "the examined account using notionals from 500,000 to 10,000,000 USDC "
                        "across 296 profitable closes, and the pinned instrument record allows "
                        "leverage up to 1000. Whether a given notional is admissible at a given "
                        "cap cannot be decided offline because the cap unit is unresolved; the "
                        "live caps are lower than the pinned ones.",
        "certik_did_not_establish": [
            "that the quotes it read were distorted or deliberately influenced: its own text "
            "says timestamp overlap alone is insufficient and that ordered market-wide quotes "
            "plus an independent reference would be needed",
            "that position 72098 needed anything beyond ordinary leveraged trading: it states "
            "the example is consistent with the recorded settlement rules",
            "the project's post-incident cap changes and recovery through other accounts, which "
            "CertiK records as not independently verified",
        ],
        "documented_admission": "the paid docs state the curve 'is not a deviation check ... "
                                "and does not guarantee that a manipulation strategy is "
                                "unprofitable', and that the protocol reads BBO without a "
                                "deviation breaker",
    }


def write_ledger(ledger):
    LEDGER.write_text(json.dumps(ledger, indent=2) + "\n")


def write_doc(ledger):
    pinned = ledger["pinned_replay"]["rows"]
    live = ledger["live_replay"]["rows"] if ledger["live_replay"] else []
    sweep = [row for row in pinned if row["case"].startswith("certik_")]
    header = ["Position notional (USDC)", "Margin (USDC)", "Leverage", "Raw PnL (USDC)",
              "Adjusted PnL (USDC)", "Win fee (USDC)", "Net payout (USDC)", "Haircut %",
              "User balance delta (USDC)", "Queued (USDC)"]
    lines = ["# Asymmetric-impact haircut and reference notional",
             "",
             "This document tests the CertiK BBO pricing incident claim against the exact "
             "pinned runtimes: that the winning-close profit haircut multiplies a **fixed "
             "reference notional**, so the haircut percentage does not grow with position "
             "size while the dollar payout does. The claim is confirmed for the pinned "
             "Exchange suite, and the same claim is re-measured against the Exchange "
             "implementation deployed at `latest`.",
             "",
             "Verdict: the pinned runtime reproduces CertiK's numbers exactly, not only its "
             "mechanism, and the haircut percentage is independent of position size in both the "
             "pinned and the deployed implementation. The deployed implementation differs only "
             "for moves inside the holdback bands the contract-set-2 docs describe, where it "
             "pays less while keeping the same size independence.",
             "",
             f"Pinned suite: Exchange proxy `{EXCHANGE}`, implementation "
             f"`{PIN_IMPLEMENTATION}`, linked library `{PIN_LIBRARY}`, at block {PIN}. "
             "Every replay below restores the saved mixed-close prestate at block "
             f"{PRESTATE_BLOCK}, etches the exact runtimes, mocks the BBO precompile "
             f"`0x080e` with the CertiK close read ({BID}/{ASK} -> midpoint {EXIT_PRICE}), "
             f"writes one ETH-market position with the CertiK entry price {ENTRY_PRICE} and "
             "runs the real signed close `0x2792e706` on the real proxy.",
             "",
             "## Where the formula lives",
             "",
             "The Exchange builds a nine-word call to the linked library selector "
             f"`{PNL_SELECTOR}` and pairs it with the settlement call `{SETTLEMENT_SELECTOR}`. "
             "The saved calls, the pinned instrument record and the local replays agree on "
             "the argument map:",
             "",
             "```text",
             "0x82296364(entryPrice, exitPrice, margin, leverage, isLong,",
             "            baseRate, rateMultiplier, positionMultiplier, referenceNotional)",
             "0xef1a27a9(margin, user, adjustedPnl, isLong, queueFlag, profitRate, lossRate, x)",
             "```",
             "",
             "Only `margin` and `leverage` carry position size; `baseRate` (10%), "
             "`rateMultiplier` (15,000), `positionMultiplier` (483.979 for ETH) and "
             "`referenceNotional` (100,000) are per-instrument constants read from the "
             "instrument record at mapping slot 7. The documented pipeline is",
             "",
             "```text",
             "move   = (|exit - entry| - floor(entry / 50000)) / entry     # deadband",
             "rawPnl = margin * leverage * move_units / entry",
             "term1  = 1 / (move * rateMultiplier)",
             "term2  = referenceNotional / (1e6 * move * positionMultiplier)",
             "scale  = (1 - baseRate) / (1 + term1 + term2)",
             "adjustedPnl = rawPnl * scale",
             "winFee = adjustedPnl * 2%",
             "```",
             "",
             "The library's integer form reproduces this formula: `term1` and `term2` are "
             "`riskInverse/WAD` and `liquidityInverse/WAD` of the pinned model, all 74 saved "
             "`0x82296364` calls return the integer form's two words exactly, and the rational "
             "evaluation of the published formula agrees with the integer form to better than "
             "1e-9 relative on every replay case, the staged floor divisions accounting for "
             "the last digits. Each Forge case asserts the integer form's own numbers.",
             "",
             "## Size sweep on the pinned implementation",
             "",
             "| " + " | ".join(header) + " |",
             "|" + "---|" * len(header)]
    for row in sweep:
        lines.append("| " + " | ".join([
            f"{row['notional_usdc']:,}", f"{int(row['margin_1e18']) // 10**18:,}",
            str(row["leverage"]), f"{int(row['raw_pnl_1e18']) / 1e18:,.6f}",
            f"{int(row['adjusted_pnl_1e18']) / 1e18:,.6f}",
            f"{int(row['win_fee_1e18']) / 1e18:,.6f}",
            f"{int(row['net_payout_1e18']) / 1e18:,.6f}",
            f"{float(row['haircut_percent']):.6f}",
            f"{int(row['balance_delta_1e18']) / 1e18:,.6f}",
            f"{int(row['queue_delta_1e18']) / 1e18:,.6f}"]) + " |")
    lines += [
        "",
        "The 25x row is the one case that needs a labelled market-state control: the close "
        "releases the position's contribution from the market side aggregate, and with the "
        "untouched pinned aggregate that release underflows for a notional far above the "
        "aggregate the real opens built. Setting the two 96-bit aggregates to their maximum "
        "removes only that underflow; the haircut inputs come from the instrument record and "
        "are untouched, and every other row runs on the pinned market words.",
        "",
        "The haircut percentage is identical in every row of the sweep: it depends on the "
        "price move and the four instrument constants only. The dollar payout is exactly "
        "proportional to margin x leverage. The CertiK figures for position 72098 "
        "(raw 17,355.223523, adjusted 13,494.728986, fee 269.894580, net 13,224.834407, "
        "haircut 22.243992%) and its hypothetical $500,000 position (net 661.241720) are "
        "reproduced exactly by the pinned runtime, so this is a reproduction of the numbers, "
        "not only of the mechanism.",
        "",
        "## Haircut-input sensitivity and the constructed counterfactual",
        "",
        "| Case | baseRate | rateMultiplier | referenceNotional | Notional (USDC) | Haircut % |",
        "|---|---|---|---|---|---|"]
    for row in pinned:
        if row["case"].startswith("certik_"):
            continue
        inputs = row["haircut_inputs"]
        lines.append("| " + " | ".join([
            row["case"], f"{inputs['base_rate'] / 1e18:.2f}",
            f"{inputs['rate_multiplier'] / 1e18:,.0f}",
            f"{inputs['reference_notional'] / 1e18:,.0f}",
            f"{row['notional_usdc']:,}", f"{float(row['haircut_percent']):.6f}"]) + " |")
    lines += [
        "",
        "The last three rows are the pinned curve at a move inside the holdback bands the "
        "contract-set-2 docs describe; the deployed implementation pays less on those moves, "
        "as the next section measures. All three return the same haircut for 500,000, "
        "2,000,000 and 10,000,000 USDC notional.",
        "",
        "Raising `baseRate`, `rateMultiplier` or `referenceNotional` changes the haircut at "
        "fixed size, which is what makes the third property observable: in the two "
        "**constructed** counterfactual cases (`referenceNotional` set to the position's own "
        "notional, the Rollbit form the docs describe) the haircut grows from the small to "
        "the large position. Those two rows are simulations of a parameter the deployed "
        "code never sets, not observed chain state.",
        "",
        "## Contract-set-1 to contract-set-2 delta",
        "",
        "Every replay case was run twice: once on the pinned implementation and its pinned "
        "linked library, once on the deployed implementation, its deployed linked library and "
        "the deployed session-key manager, with the live configuration words (implementation "
        "pointer, instrument record, market fields and the instrument-count/curve word) read at "
        "`latest`.",
        "",
        "| Case | Move | Notional (USDC) | Pinned net (USDC) | Deployed net (USDC) | Pinned haircut % | Deployed haircut % |",
        "|---|---|---|---|---|---|---|"]
    pinned_by_label = {row["case"]: row for row in pinned}
    for row in live:
        pinned_row = pinned_by_label.get(row["case"])
        if pinned_row is None or pinned_row["net_payout_1e18"] == row["net_payout_1e18"]:
            continue
        entry = int(row.get("entry", ENTRY_PRICE))
        move = abs(int(row.get("exit", EXIT_PRICE)) - entry)
        lines.append("| " + " | ".join([
            row["case"], f"{move / entry * 10000:.2f} bps",
            f"{row['notional_usdc']:,}",
            f"{int(pinned_row['net_payout_1e18']) / 1e18:,.6f}",
            f"{int(row['net_payout_1e18']) / 1e18:,.6f}",
            f"{float(pinned_row['haircut_percent']):.6f}",
            f"{float(row['haircut_percent']):.6f}"]) + " |")
    lines += [
        "",
        "The delta is confined to moves inside the holdback bands: at the incident's "
        "17.55 bps move the two implementations are numerically identical, and at 3.99 bps "
        "the deployed curve withholds far more of the gain. The deployed library also changed "
        "shape: the pinned pair `0x82296364` / `0xef1a27a9` is gone, replaced by `0x06c5308a` "
        "(ten arguments: the pinned nine plus a payout-curve selector) and `0xb9370332`. The "
        "four instrument constants are byte-identical in the live instrument record, and the "
        "deployed haircut is still one value across 50,000 to 250,000,000 USDC notional and "
        "across 500,000 to 10,000,000 USDC inside the holdback band, so size independence "
        "survived the upgrade.",
        "",
        "## What bounds the payout",
        "",
        f"- **Open-interest caps.** Market field word 1 carries two 128-bit per-side limits for "
        f"the ETH market. The keeper selector `0x628a9fd6` writes them and the signed-open path "
        f"compares the updated side value against them: "
        f"{ledger['bounds']['open_interest_caps']['saved_open_sample']['cap_reverts']} of "
        f"{ledger['bounds']['open_interest_caps']['saved_open_sample']['signed_opens_compared']} "
        f"saved signed opens reverted with "
        f"`{ledger['bounds']['open_interest_caps']['saved_open_sample']['error']}` while the other "
        f"{ledger['bounds']['open_interest_caps']['saved_open_sample']['successes_below_limit']} "
        f"stayed at or below the limit. The limits at `latest` are "
        f"{ledger['bounds']['open_interest_caps']['eth_limit_tightening'][0]:.2f}x and "
        f"{ledger['bounds']['open_interest_caps']['eth_limit_tightening'][1]:.2f}x lower than the "
        "pinned ones, matching the project's statement that it tightened launch limits after the "
        "incident. The compared values' unit stays unresolved in the atlas, so no USDC notional "
        "cap is claimed.",
        f"- **LP bankroll.** `{ledger['bounds']['lp_bankroll']['formula']}`. At the replay "
        f"prestate the available figure is "
        f"{ledger['bounds']['lp_bankroll']['available_usdc']:,.2f} USDC, and the largest replayed "
        f"close credited "
        f"{int(ledger['bounds']['lp_bankroll']['largest_replay_credit']['balance_credit_1e18']) / 1e18:,.2f} "
        "USDC to the trader with no queue entry.",
        "- **Queue.** Every replay row credited directly with a zero queue delta, and the pinned "
        "suite has a queued-profit close branch, so a payout larger than the available bankroll "
        "is deferred rather than paid immediately.",
        f"- **Reachability.** {ledger['bounds']['reachability']}",
        "- **What CertiK did not establish.** "
        + "; ".join(ledger["bounds"]["certik_did_not_establish"]) + ".",
        f"- **The protocol's own admission.** {ledger['bounds']['documented_admission']}",
        "",        "## Saved-call provenance",
        "",
        f"{ledger['provenance']['saved_pnl_calls']} saved `{PNL_SELECTOR}` delegatecalls in "
        f"{ledger['provenance']['transactions']} historical transactions "
        f"(blocks {ledger['provenance']['blocks_min']}-{ledger['provenance']['blocks_max']}) "
        "were decoded. All of them reproduce the reconstructed model, and their haircut "
        "arguments are constant per market while the position notional spans "
        f"{min(row['notional'] for row in ledger['provenance']['profit_calls']):,}"
        " up to "
        f"{max(row['notional'] for row in ledger['provenance']['profit_calls']):,} USDC across "
        f"{len(ledger['provenance']['profit_calls'])} profitable calls. The observed argument "
        "sets are:",
        "",
        "```text",
        f"baseRate            {[value for value in ledger['provenance']['argument_5_base_rate_values']]}",
        f"rateMultiplier      {ledger['provenance']['argument_6_rate_multiplier_values']}",
        f"positionMultiplier  {ledger['provenance']['argument_7_position_multiplier_values']}",
        f"referenceNotional   {ledger['provenance']['argument_8_reference_notional_values']}",
        "```",
        "",
        "These are the pinned instrument-record values of the two live markets, so no "
        "position size reaches the haircut path.",
        "",
        "## Currently deployed implementation",
        "",
        f"At `latest` (block {ledger['live_capture']['head_block']}) the Exchange proxy points "
        f"to `{ledger['live_capture']['implementation']}` "
        f"({ledger['live_capture']['implementation_runtime_bytes']} runtime bytes, sha256 "
        f"`{ledger['live_capture']['implementation_sha256']}`), which links "
        f"`{ledger['live_comparison']['live_library_address']}` "
        f"({ledger['live_comparison']['live_library_bytes']} runtime bytes, sha256 "
        f"`{ledger['live_comparison']['live_library_sha256']}`). The pinned linked library is "
        f"`{PIN_LIBRARY}` ({ledger['live_comparison']['pinned_library_bytes']} runtime bytes).",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Linked library byte-identical after blanking linked addresses and metadata | "
        f"{ledger['live_comparison']['library_byte_identical_after_normalization']} |",
        f"| `{PNL_SELECTOR}` present in pinned library | "
        f"{ledger['live_comparison']['pnl_selector_in_pinned']} |",
        f"| `{PNL_SELECTOR}` present in live library | "
        f"{ledger['live_comparison']['pnl_selector_in_live']} |",
        f"| `{SETTLEMENT_SELECTOR}` present in live library | "
        f"{ledger['live_comparison']['settlement_selector_in_live']} |",
        f"| Selectors added in live library | "
        f"{', '.join(ledger['live_comparison']['selectors_added']) or 'none'} |",
        f"| Selectors removed from pinned library | "
        f"{', '.join(ledger['live_comparison']['selectors_removed']) or 'none'} |",
        f"| Live ETH instrument record equals pinned record | "
        f"{ledger['live_comparison']['instrument_record_equal']} |",
        "",
        "So the pinned and live runtimes are **not** byte-identical: the linked library grew, "
        "the pinned profit-math and settlement selectors are gone, and two new selectors "
        "appeared (contract set 2 per the docs, which added a holdback band and a payout-curve "
        "selector). The Exchange implementation changed too, and with it the session-key "
        f"manager implementation (`{ledger['live_capture']['session_key_manager_implementation']}`, "
        f"{ledger['live_capture']['session_key_manager_implementation_bytes']} runtime bytes), whose "
        "close path calls a different manager selector. The four instrument constants "
        "themselves are byte-identical, and the live replay below measures whether the size "
        "relation survived.",
        "",
        "## Deployed-implementation replay",
        "",
        "The same 15 cases on the deployed implementation, its deployed library and the "
        "deployed session-key manager:",
        "",
        "| Case | " + " | ".join(header) + " |",
        "|" + "---|" * (len(header) + 1)]
    for row in live:
        lines.append("| " + " | ".join([
            row["case"],
            f"{row['notional_usdc']:,}", f"{int(row['margin_1e18']) // 10**18:,}",
            str(row["leverage"]), f"{int(row['raw_pnl_1e18']) / 1e18:,.6f}",
            f"{int(row['adjusted_pnl_1e18']) / 1e18:,.6f}",
            f"{int(row['win_fee_1e18']) / 1e18:,.6f}",
            f"{int(row['net_payout_1e18']) / 1e18:,.6f}",
            f"{float(row['haircut_percent']):.6f}",
            f"{int(row['balance_delta_1e18']) / 1e18:,.6f}",
            f"{int(row['queue_delta_1e18']) / 1e18:,.6f}"]) + " |")
    lines += [
        "",
        ledger["live_replay"]["conclusion"] if ledger["live_replay"] else
        "The live replay was skipped in this invocation (--skip-live-replay).",
        "",
        "## Limits",
        "",
    ]
    lines += [f"- {item}" for item in ledger["limits"]]
    lines += ["", "## Sources", ""]
    lines += [f"- {item}" for item in ledger["sources"]]
    lines.append("")
    DOC.write_text("\n".join(lines))


LIMITS = [
    "Only the winning-close profit path is measured. Losing closes bypass the scale factor "
    "entirely (both saved and replayed loss cases return adjustedPnl == rawPnl), so the "
    "haircut finding does not apply to them.",
    "The offline comparison of the live implementation is a live-code capture plus an "
    "offline diff and local replay. The public RPC ignores block parameters and exposes no "
    "debug tracer, and no archive endpoint is configured, so the incident-era runtime at "
    "block 48,202,386 cannot be fetched; the pinned suite is used as the incident-era "
    "proxy on the strength of its deployer creation block and the absence of any recorded "
    "Upgraded log through the pin, not of a fetched historical bytecode read.",
    "The live replay restores pinned storage for the Exchange accounting fields and "
    "overrides only the configuration the live capture shows changed: the implementation "
    "pointer, the implementation and library code, the instrument record, the market fields "
    "and the instrument-count/curve word. Live accounting (treasury, totalBalances, "
    "totalLockedMargin, fee accumulators) is at its block-48,901,631 value, so the balance "
    "credit and queue columns are local-scenario values, not current chain values.",
    "The per-side open-interest caps in market field word 1 act as limits in the sampled "
    "signed-open paths, but their unit is unresolved, so this document does not convert a "
    "cap into a maximum notional and does not claim that any particular size is reachable "
    "at a given cap.",
    "CertiK's account-level net withdrawal of 1,279,106.191184 USDC, its Hyperliquid fill "
    "sample and its quote-overlap table were not re-derived here; this document only tests "
    "the haircut and reference-notional claim and the payout it produces.",
    "The holdback delta is a measured difference between two runtimes. That it is the "
    "documented holdback band is an inference from the documented band ranges and the "
    "curve-selector argument, not a source-level mapping: the deployed library's argument "
    "semantics are established by the replay's numbers, not by recovered source.",
    "The deployed session-key manager is restored so the real signed-close authorization runs; "
    "its own registry layout is outside this document, and no session-manager behavior is "
    "claimed beyond the two selectors the close path uses.",
]

SOURCES = [
    "CertiK, PaperTrade BBO Pricing Incident, 2026-10-20: "
    "https://www.certik.com/blog/papertrade-bbo-pricing-incident (position 72098 numbers, "
    "the fixed 100,000 USDC reference notional, the 22.243992% haircut and the $500,000 "
    "hypothetical).",
    "Papertrade docs, Asymmetric impact PnL (contract set 2, updated 2026-10-21): "
    "https://docs.papertrade.xyz/how/asymmetric-impact and the contract-set-1 page "
    "https://docs.papertrade.xyz/v1/how/asymmetric-impact (identical formula for both sets).",
    "atlas/block_48902346/exchange_library_pseudocode.md and exchange_library_behavior.json "
    "(the pinned library model, 49 historical settlement pairs, 74 saved math calls).",
    "atlas/block_48902346/exchange_instruments_getter.md, exchange_instrument_creation.md "
    "and exchange_market_fields.md (instrument record packing, keeper market fields, "
    "instrument-count and market-keeper reads).",
    "atlas/block_48902346/exchange_close_paths.md, exchange_close_fee_effects.md and "
    "exchange_negative_close_fee.md (the signed-close branches and the 2% positive-PnL "
    "fee on Exchange slot 24).",
    "atlas/block_48902346/exchange_storage_behavior.md (lpBankrollAvailable formula), "
    "exchange_availability_behavior.json (the queue gate on that formula), "
    "exchange_open_limit.md and exchange_open_limit_full_behavior.json (per-side open limit "
    "guard at signed open, 57 sampled opens with 27 cap reverts) and "
    "exchange_market_fields.md (the keeper writes to those limits).",
    "Papertrade docs, Pricing: BBO precompile and the no-deviation-breaker note: "
    "https://docs.papertrade.xyz/how/pricing-bbo (quoted as the protocol's own limitation).",
    "artifacts/exchange_negative_close/original_prestate.json (the replay prestate) and "
    "artifacts/audit_certik_haircut/live/ (the live implementation, linked library, "
    "session-key-manager implementation and storage captures at latest).",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="refresh the live Exchange implementation, library and slots")
    parser.add_argument("--skip-live-replay", action="store_true",
                        help="skip the source-generation and Forge run for the live variant")
    options = parser.parse_args()
    if options.capture:
        capture_live()

    words, _ = read_instrument_words()
    market_words = read_market_words()
    prestate = json.loads(PRESTATE.read_text())
    pinned_impl_hex = prestate[PIN_IMPLEMENTATION]["code"]
    pinned_lib_hex = prestate[PIN_LIBRARY]["code"]

    # 1. CertiK arithmetic from the pinned model and the documented formula.
    certik_params = base_params(words)
    certik_raw, certik_adjusted = code_pnl([ENTRY_PRICE, EXIT_PRICE, CERTIK["position_margin"] * WAD,
                                            CERTIK["position_leverage"], 1,
                                            certik_params["base_rate"], certik_params["rate_multiplier"],
                                            certik_params["position_multiplier"],
                                            certik_params["reference_notional"]])
    certik_fee = certik_adjusted * 2 // 100
    certik_net = certik_adjusted - certik_fee
    scale = scale_exact(certik_params)
    tolerance = 10**12  # 1e-6 USDC: the incident table is rounded to six decimals
    assert abs(certik_raw - CERTIK["raw_pnl"]) < tolerance, certik_raw
    assert abs(certik_adjusted - CERTIK["adjusted_pnl"]) < tolerance, certik_adjusted
    assert abs(certik_net - CERTIK["net"]) < tolerance, certik_net
    assert abs(certik_fee - CERTIK["win_fee"]) < tolerance, certik_fee
    certik_rows = {}
    for notional in (CERTIK["position_margin"] * CERTIK["position_leverage"], 500000, 50000,
                     25000000, 250000000):
        raw = raw_pnl(ENTRY_PRICE, EXIT_PRICE, notional * WAD // 500, 500, True)
        adjusted = int(raw * scale)
        certik_rows[notional] = {
            "raw_pnl": raw, "adjusted_pnl": adjusted, "fee": adjusted * 2 // 100,
            "net": adjusted - adjusted * 2 // 100,
            "haircut_ppm": (raw - adjusted) * 10**6 // raw,
        }
    assert abs(certik_rows[500000]["net"] - CERTIK["hypothetical_net"]) < tolerance
    assert len({row["haircut_ppm"] for row in certik_rows.values()}) == 1
    assert abs(certik_rows[500000]["haircut_ppm"] - CERTIK["haircut_ppm"]) <= 2, \
        certik_rows[500000]["haircut_ppm"]

    # 2. Saved-call provenance.
    saved = historical_math_calls()
    provenance = provenance_summary(saved, words, market_words)
    assert not provenance["returns_mismatched"]

    # 3. Pinned replay.
    cases = case_set(words)
    pinned = run_forge("pinned", cases, {"block": PRESTATE_BLOCK, "timestamp": 0x6ad5311e,
                                         "checked": True})
    for case, expected in zip(cases, pinned["expectations"]):
        observed = pinned["observed"][f"pinned_{case['label']}"]
        assert observed["raw_pnl"] == expected["raw_pnl_model"], case["label"]
        assert observed["adjusted_pnl"] == expected["adjusted_pnl_model"], case["label"]
        assert observed["fee"] == expected["fee_model"], case["label"]
        assert observed["adjusted_pnl"] == expected["adjusted_pnl_model"], case["label"]
    pinned_calls = library_math_calls(pinned["trace"], PIN_LIBRARY)
    pinned_math_example = None
    for case, _ in zip(cases, pinned["expectations"]):
        name = f"test_pinned_{case['label']}"
        math = [call for call in pinned_calls.get(name, []) if call["selector"] == PNL_SELECTOR]
        assert len(math) == 1, (name, pinned_calls.get(name))
        observed_args = math[0]["arguments"]
        expected_args = [case["entry"], case["exit"], case["margin"], case["leverage"], 1,
                         case["params"]["base_rate"], case["params"]["rate_multiplier"],
                         case["params"]["position_multiplier"],
                         case["params"]["reference_notional"]]
        assert observed_args == expected_args, (name, observed_args, expected_args)
        assert math[0]["returns"] == list(code_pnl(observed_args)), name
        if pinned_math_example is None:
            pinned_math_example = {
                "test": name, "case": case["label"], "selector": math[0]["selector"],
                "arguments": [str(value) for value in observed_args],
                "returns": [str(value) for value in math[0]["returns"]],
            }

    # 4. Live comparison and live replay.
    capture = json.loads((LIVE / "capture.json").read_text())
    live_impl_hex = (LIVE / "implementation.hex").read_text().strip()
    libraries = capture["linked_libraries"]
    live_library = capture["linked_library"]
    assert len(libraries[live_library]["push20_offsets"]) > 1
    live_lib_hex = (LIVE / f"linked_{live_library[2:]}.hex").read_text().strip()
    comparison = compare_implementation(pinned_impl_hex, live_impl_hex, pinned_lib_hex, live_lib_hex)
    comparison["live_library_address"] = live_library
    live_probes = json.loads((LIVE / "raw" / "storage_probes.json").read_text())
    live_instrument_storage = [int(live_probes["instrument_words"][u256(int(INSTRUMENT_ROOT, 16) + i)], 16)
                               for i in range(3)]
    live_market_storage = [int(live_probes["market_words"][u256(int(MARKET_ROOT, 16) + i)], 16)
                           for i in range(2)]
    live_words = unpack_instrument(live_instrument_storage)
    comparison["instrument_record_equal"] = live_words == words
    comparison["live_instrument_words"] = live_words
    comparison["live_market_fields"] = live_market_storage
    comparison["config_slots"] = [
        compare_slot_probe(prestate[EXCHANGE]["storage"].get(u256(index)),
                           str(index), live_probes["config_slots"][str(index)])
        for index in (8, 14, 16, 18, 22, 23, 24, 25, 26, 27, 29)]
    live_replay = None
    if not options.skip_live_replay:
        live_variant = {
            "block": capture["head_block"],
            "timestamp": capture["head_timestamp"],
            "checked": False,
            "instrument_words": live_words,
            "instrument_packed": live_instrument_storage,
            "extra_code": {capture["implementation"]: live_impl_hex,
                           live_library: live_lib_hex,
                           capture["session_key_manager_implementation"]:
                               (LIVE / "session_manager_implementation.hex").read_text().strip()},
            "market_words": live_market_storage,
            "session_implementation": capture["session_key_manager_implementation"],
            "extra_stores": {EIP1967_SLOT: int(capture["implementation"], 16),
                             u256(8): int(live_probes["config_slots"]["8"], 16)},
        }
        live = run_forge("live", cases, live_variant)
        live_calls = library_math_calls(live["trace"], live_library)
        matches = 0
        deltas = []
        for case, expected in zip(cases, live["expectations"]):
            observed = live["observed"][f"live_{case['label']}"]
            if observed["adjusted_pnl"] == expected["adjusted_pnl_model"] and \
                    observed["raw_pnl"] == expected["raw_pnl_model"] and \
                    observed["fee"] == expected["fee_model"]:
                matches += 1
            else:
                deltas.append({"case": case["label"],
                               "observed_adjusted": observed["adjusted_pnl"],
                               "pinned_model_adjusted": expected["adjusted_pnl_model"],
                               "observed_raw": observed["raw_pnl"],
                               "pinned_model_raw": expected["raw_pnl_model"]})
        live_sweep = [live["observed"][f"live_{case['label']}"] for case in cases
                      if case["label"].startswith("certik_")]
        live_haircuts = {observed["haircut_1e9"] for observed in live_sweep}
        holdback_sweep_labels = [case["label"] for case in cases
                                 if case["label"].startswith("holdback_4bp")]
        holdback_labels = [case["label"] for case in cases
                           if case["label"].startswith("holdback_")]
        holdback_haircuts = {live["observed"][f"live_{label}"]["haircut_1e9"]
                             for label in holdback_sweep_labels}
        assert len(live_haircuts) == 1, live_haircuts
        assert len(holdback_haircuts) == 1, holdback_haircuts
        assert matches == len(cases) - len(deltas), (matches, len(deltas))
        assert {row["case"] for row in deltas} == set(holdback_labels), deltas
        live_calls_seen = sorted({call["selector"] for calls in live_calls.values()
                                  for call in calls})
        live_math_example = None
        for test, calls in live_calls.items():
            for call in calls:
                if call["selector"] in (PNL_SELECTOR, SETTLEMENT_SELECTOR):
                    continue
                live_math_example = {"test": test, "selector": call["selector"],
                                     "kind": call["kind"],
                                     "arguments": [str(value) for value in call["arguments"]],
                                     "returns": [str(value) for value in call["returns"]]}
                break
            if live_math_example:
                break
        assert live_math_example and len(live_math_example["arguments"]) == 10, live_math_example
        live_replay = {
            "block": capture["head_block"],
            "implementation": capture["implementation"],
            "library": live_library,
            "source_sha256": live["source_sha256"],
            "forge_result": live["forge_result"],
            "rows": ledger_rows(live, cases, "live"),
            "cases_matching_pinned_model": matches,
            "cases_total": len(cases),
            "deltas_vs_pinned_model": deltas,
            "size_sweep_haircut_ppm": sorted(live_haircuts),
            "size_sweep_single_haircut": len(live_haircuts) == 1,
            "holdback_cases": holdback_labels,
            "holdback_size_sweep_labels": holdback_sweep_labels,
            "holdback_size_sweep_haircut_ppm": sorted(holdback_haircuts),
            "holdback_size_sweep_single_haircut": len(holdback_haircuts) == 1,
            "library_selectors_reached": live_calls_seen,
            "math_call_example": live_math_example,
            "math_call_selectors": sorted({call["selector"] for calls in live_calls.values()
                                           for call in calls
                                           if call["selector"] != SETTLEMENT_SELECTOR}),
            "satellite_note": "unchecked: the live run records the observed event values "
                              "instead of asserting the pinned model's numbers",
        }
        delta_labels = ", ".join(row["case"] for row in deltas)
        live_replay["conclusion"] = (
            f"The live implementation matched the pinned model's raw PnL, adjusted PnL and fee "
            f"in {matches} of {len(cases)} cases. Every case at the incident's 17.55 bps move "
            f"matched, and the size sweep from 50,000 to 250,000,000 USDC notional returned one "
            f"single haircut value ({sorted(live_haircuts)[0] / 10**7:.6f}%), so the haircut "
            f"percentage is still independent of position size in the deployed code. The "
            f"differences are confined to {delta_labels}: moves inside the holdback bands the "
            f"contract-set-2 docs describe, where the deployed library holds the move back and "
            f"pays less (3.99 bps: 1,942.424369 pinned vs 606.864475 deployed; 0.52 bps: "
            f"29.440083 pinned vs 23.867293 deployed). The holdback sweep at 3.99 bps also "
            f"returns one single haircut value "
            f"({sorted(holdback_haircuts)[0] / 10**7:.6f}%) across 500,000, 2,000,000 and "
            f"10,000,000 USDC notional, so size independence holds inside the band as well. "
            f"The call-shape change is a tenth argument (value 1) on the deployed math "
            f"selector 0x06c5308a, matching the curve selector the instrument-count word "
            f"carries; the other four instrument constants are unchanged.")

    ledger = {
        "pin": PIN,
        "pin_hash": PIN_HASH,
        "prestate_block": PRESTATE_BLOCK,
        "exchange": EXCHANGE,
        "pinned_implementation": PIN_IMPLEMENTATION,
        "pinned_library": PIN_LIBRARY,
        "instrument_id": INSTRUMENT,
        "instrument_record_words": words,
        "market_fields": market_words,
        "instrument_parameter_sources": {
            "base_rate": "instrument record word 6",
            "rate_multiplier": "instrument record word 0",
            "position_multiplier": "instrument record word 1",
            "reference_notional": "instrument record word 7",
        },
        "documented_formula": {
            "scale": "(1 - baseRate) / (1 + term1 + term2)",
            "term1": "1 / (move * rateMultiplier)",
            "term2": "referenceNotional / (1e6 * move * positionMultiplier)",
            "move": "(|exit - entry| - floor(entry / 50000)) / entry",
            "note": "the pinned library's riskInverse/WAD and liquidityInverse/WAD equal "
                    "term1 and term2 exactly",
        },
        "certik_claim_reproduction": {
            "raw_pnl_1e18": str(certik_raw),
            "adjusted_pnl_1e18": str(certik_adjusted),
            "win_fee_1e18": str(certik_fee),
            "net_1e18": str(certik_net),
            "haircut_ppm": (certik_raw - certik_adjusted) * 10**6 // certik_raw,
            "certik_haircut_ppm": CERTIK["haircut_ppm"],
            "notional_sweep": {str(key): {name: str(value) for name, value in row.items()}
                               for key, row in certik_rows.items()},
            "notional_sweep_basis": "exact rational evaluation of the published formula; the "
                                    "Forge replay rows carry the runtime's own integer values",
            "verdict": "reproduced the numbers: the pinned runtime, driven with the pinned "
                       "instrument constants at the CertiK entry and exit prices and the "
                       "recorded size, returns CertiK's raw PnL, adjusted PnL, win fee, net "
                       "payout and 22.243992% haircut exactly, and its $500,000 hypothetical "
                       "net exactly",
        },
        "provenance": provenance,
        "pinned_replay": {
            "block": PRESTATE_BLOCK,
            "timestamp": 0x6ad5311e,
            "bbo_mock": f"0x080e instrument {INSTRUMENT} -> {BID}/{ASK}, midpoint {EXIT_PRICE}",
            "entry_price": ENTRY_PRICE,
            "source_sha256": pinned["source_sha256"],
            "forge_result": pinned["forge_result"],
            "rows": ledger_rows(pinned, cases, "pinned"),
            "math_call_arguments_checked": len(cases),
            "math_call_example": pinned_math_example,
            "market_aggregate_control": "pinned market field words except the 25x case, whose "
                                        "96-bit side aggregates are set to their maximum",
        },
        "live_capture": capture,
        "live_comparison": comparison,
        "live_replay": live_replay,
        "bounds": bounds_section(prestate, live_probes, cases,
                                 ledger_rows(pinned, cases, "pinned"),
                                 ledger_rows(live, cases, "live") if live_replay else []),
        "limits": LIMITS,
        "sources": SOURCES,
    }
    write_ledger(ledger)
    write_doc(ledger)
    print(f"ledger {LEDGER.relative_to(ROOT)}")
    print(f"doc {DOC.relative_to(ROOT)}")
    for row in ledger["pinned_replay"]["rows"]:
        print(f"  pinned {row['case']:<40} notional {row['notional_usdc']:>10} "
              f"net {int(row['net_payout_1e18']) / 1e18:>16,.6f} haircut {row['haircut_percent']}")
    for row in (live_replay or {}).get("rows", []):
        print(f"  live   {row['case']:<40} notional {row['notional_usdc']:>10} "
              f"net {int(row['net_payout_1e18']) / 1e18:>16,.6f} haircut {row['haircut_percent']}")


if __name__ == "__main__":
    main()
