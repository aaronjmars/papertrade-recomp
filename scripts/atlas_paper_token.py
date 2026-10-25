#!/usr/bin/env python3
"""Verify PAPER token deployment, admin writes, and pinned call branches."""

import argparse
import json
import os
import pathlib
import re

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts" / "paper_token"
HISTORICAL = ROOT / "artifacts" / "historical"
PIN = 48902346
TOKEN = "0xe40f17915daa230324030003a197cdaef2261c0e"
IMPLEMENTATION = "0x433bd418ec92818a960585f4d5fae563e735bb4a"
STAKING = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
MINTER = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
OWNER = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
HOLDER = "0xbbb9512a5843441a8435d8f745fce97eb6a9eebf"
OUTSIDER = "0x1234567890123456789012345678901234567890"
DEPLOYMENT_TX = "0x5e75d563d789f1007d03b187dd2f646b1912aeaf2ff43ac69f9bd2a77cabed74"
ADMIN_TXS = {
    "slot5_setter": ("0x3e080969215f85d41865c022dcad457d02c510aa100d9b737adf107fbb7cebab", "0xd311b1a9", 5, "0x6e54fcdf080b1c188bfc8f26eb9386e78b6cb5428459a86cdd74357de82a33ae"),
    "staking_contract_setter": ("0x8a64598fa90a06cdcd95f581db350c00da9cd829f8b5cb865c24118bee6fe0b0", "0x9dd373b9", 9, "0x6397f5b135542bb3f477cb346cfab5abdec1251d08dc8f8d4efb4ffe122ea0bf"),
    "ownership_transfer": ("0x66c836fe26fbc6d8b4e66cf035cc9a831a1cd4af05b4861ef7e2174b01a30742", "0xf2fde38b", 3, "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b"),
}
KECCAK = Keccak()
SELECTORS = {
    "0x06fdde03": "name()",
    "0x07546172": "minter()",
    "0x095ea7b3": "approve(address,uint256)",
    "0x12bbf044": "autoApprovedSpender()",
    "0x18160ddd": "totalSupply()",
    "0x23b872dd": "transferFrom(address,address,uint256)",
    "0x313ce567": "decimals()",
    "0x40c10f19": "mint(address,uint256)",
    "0x70a08231": "balanceOf(address)",
    "0x8da5cb5b": "owner()",
    "0x8f15b414": "initialize(string,string,address,address)",
    "0x95d89b41": "symbol()",
    "0x9dc29fac": "burn(address,uint256)",
    "0x9dd373b9": "setStakingContract(address)",
    "0xd311b1a9": "setAutoApprovedSpender(address)",
    "0xa9059cbb": "transfer(address,uint256)",
    "0xdd62ed3e": "allowance(address,address)",
    "0xee99205c": "stakingContract()",
    "0xf2fde38b": "transferOwnership(address)",
    "0xfca3b5aa": "setMinter(address)",
}
EVENTS = {
    "AutoApprovedSpenderUpdated(address)": "0x6e54fcdf080b1c188bfc8f26eb9386e78b6cb5428459a86cdd74357de82a33ae",
    "StakingContractUpdated(address)": "0x6397f5b135542bb3f477cb346cfab5abdec1251d08dc8f8d4efb4ffe122ea0bf",
    "OwnerUpdated(address)": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
    "MinterUpdated(address)": "0xad0f299ec81a386c98df0ac27dae11dd020ed1b56963c53a7292e7a3a314539a",
    "Transfer(address,address,uint256)": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    "Approval(address,address,uint256)": "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925",
}
ERRORS = {
    "AlreadyInitialized()": "0x0dc149f0",
    "InsufficientAllowance()": "0x13be252b",
    "NotOwner()": "0x30cd7471",
    "TransferRestricted()": "0xe827105e",
    "InsufficientBalance()": "0xf4d678b8",
    "NotMinter()": "0xf8d2906c",
}


def word(value):
    return (int(value, 16) if isinstance(value, str) else value).to_bytes(32, "big")


def calldata(selector, *args):
    return selector + b"".join(word(arg) for arg in args).hex()


def mapping_slot(key, base):
    return "0x" + KECCAK(word(key) + word(base)).hex()


def allowance_slot(owner, spender):
    return "0x" + KECCAK(word(spender) + KECCAK(word(owner) + word(8))).hex()


def call_case(url, sender, data, override=None):
    params = [{"to": TOKEN, "from": sender, "data": data}, hex(PIN)]
    if override:
        params.append(override)
    try:
        return {"ok": True, "output": rpc(url, "eth_call", params)}
    except RuntimeError as exc:
        matches = re.findall(r"0x[0-9a-fA-F]{8}", str(exc))
        assert matches, str(exc)
        return {"ok": False, "revert_selector": matches[-1].lower()}


def nested_logs(call):
    logs = list(call.get("logs", []))
    for child in call.get("calls", []):
        logs.extend(nested_logs(child))
    return logs


def capture_mutations():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS / "pinned_mutation_traces.json"
    if path.exists():
        return
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    cases = {
        "owner_set_new_minter": (OWNER, calldata("0xfca3b5aa", OUTSIDER)),
        "outsider_set_new_minter": (OUTSIDER, calldata("0xfca3b5aa", OUTSIDER)),
        "minter_burn_one": (MINTER, calldata("0x9dc29fac", HOLDER, 1)),
        "minter_burn_over_balance": (MINTER, calldata("0x9dc29fac", HOLDER, 2**128)),
    }
    records = {}
    for name, (sender, data) in cases.items():
        call = {"from": sender, "to": TOKEN, "data": data}
        trace = rpc(url, "debug_traceCall", [call, hex(PIN),
                                               {"tracer": "callTracer", "tracerConfig": {"withLog": True}}])
        diff = rpc(url, "debug_traceCall", [call, hex(PIN),
                                              {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}}])
        records[name] = {"sender": sender, "calldata": data,
                         "error": trace.get("error"), "output": trace.get("output"),
                         "implementation_calls": [{"type": child["type"], "to": child["to"],
                                                   "input": child["input"]} for child in trace.get("calls", [])],
                         "logs": nested_logs(trace),
                         "pre_storage": diff.get("pre", {}).get(TOKEN, {}).get("storage", {}),
                         "post_storage": diff.get("post", {}).get(TOKEN, {}).get("storage", {})}
    path.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                "method": "pinned read-only debug_traceCall with callTracer logs and prestateTracer diffMode",
                                "cases": records}, indent=2) + "\n")


def capture():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert rpc(url, "eth_getBlockByNumber", [hex(PIN), False])["hash"] == manifest["block_hash"]
    deployment = ARTIFACTS / "deployment.calls.json"
    if not deployment.exists():
        deployment.write_text(json.dumps(rpc(url, "debug_traceTransaction", [DEPLOYMENT_TX, {"tracer": "callTracer"}]), indent=2) + "\n")
    deployment_receipt = ARTIFACTS / "deployment.receipt.json"
    if not deployment_receipt.exists():
        deployment_receipt.write_text(json.dumps(rpc(url, "eth_getTransactionReceipt", [DEPLOYMENT_TX]), indent=2) + "\n")
    path = ARTIFACTS / "pinned_probes.json"
    if path.exists():
        return
    getters = {}
    for name, selector in (("owner", "0x8da5cb5b"), ("minter", "0x07546172"),
                           ("slot5", "0x12bbf044"), ("staking_contract", "0xee99205c"),
                           ("total_supply", "0x18160ddd"), ("holder_balance", calldata("0x70a08231", HOLDER)),
                           ("staking_balance", calldata("0x70a08231", STAKING)),
                           ("holder_staking_allowance", calldata("0xdd62ed3e", HOLDER, STAKING))):
        getters[name] = rpc(url, "eth_call", [{"to": TOKEN, "data": selector}, hex(PIN)])
    slots = {str(n): rpc(url, "eth_getStorageAt", [TOKEN, hex(n), hex(PIN)]) for n in (3, 4, 5, 6, 9)}
    balance_slot = mapping_slot(HOLDER, 7)
    staking_balance_slot = mapping_slot(STAKING, 7)
    approval_slot = allowance_slot(HOLDER, STAKING)
    outsider_approval_slot = allowance_slot(HOLDER, OUTSIDER)
    slots["holder_balance"] = rpc(url, "eth_getStorageAt", [TOKEN, balance_slot, hex(PIN)])
    slots["staking_balance"] = rpc(url, "eth_getStorageAt", [TOKEN, staking_balance_slot, hex(PIN)])
    slots["holder_staking_allowance"] = rpc(url, "eth_getStorageAt", [TOKEN, approval_slot, hex(PIN)])
    max_approval_override = {TOKEN: {"stateDiff": {outsider_approval_slot: "0x" + word(2**256 - 1).hex()}}}
    zero_approval_override = {TOKEN: {"stateDiff": {approval_slot: "0x" + word(0).hex()}}}
    unstaked_override = {TOKEN: {"stateDiff": {"0x" + word(9).hex(): "0x" + word(0).hex()}}}
    unstaked_with_approval_override = {TOKEN: {"stateDiff": {"0x" + word(9).hex(): "0x" + word(0).hex(),
                                                                 outsider_approval_slot: "0x" + word(2**256 - 1).hex()}}}
    new_staking_override = {TOKEN: {"stateDiff": {"0x" + word(9).hex(): "0x" + word(OUTSIDER).hex(),
                                                         outsider_approval_slot: "0x" + word(2**256 - 1).hex()}}}
    cases = {
        "holder_transfer": (HOLDER, calldata("0xa9059cbb", OUTSIDER, 1), None),
        "holder_zero_transfer": (HOLDER, calldata("0xa9059cbb", OUTSIDER, 0), None),
        "staking_transfer": (STAKING, calldata("0xa9059cbb", OUTSIDER, 1), None),
        "staking_zero_transfer": (STAKING, calldata("0xa9059cbb", OUTSIDER, 0), None),
        "staking_overdraw": (STAKING, calldata("0xa9059cbb", HOLDER, int(getters["staking_balance"], 16) + 1), None),
        "staking_pull_into_staking": (STAKING, calldata("0x23b872dd", HOLDER, STAKING, 1), None),
        "staking_pull_elsewhere": (STAKING, calldata("0x23b872dd", HOLDER, OUTSIDER, 1), None),
        "outsider_pull_without_allowance": (OUTSIDER, calldata("0x23b872dd", HOLDER, STAKING, 1), None),
        "outsider_pull_to_staking_with_allowance": (OUTSIDER, calldata("0x23b872dd", HOLDER, STAKING, 1), max_approval_override),
        "outsider_pull_elsewhere_with_allowance": (OUTSIDER, calldata("0x23b872dd", HOLDER, OUTSIDER, 1), max_approval_override),
        "staking_pull_without_allowance": (STAKING, calldata("0x23b872dd", HOLDER, STAKING, 1), zero_approval_override),
        "holder_transfer_with_slot9_zero": (HOLDER, calldata("0xa9059cbb", OUTSIDER, 1), unstaked_override),
        "outsider_pull_with_slot9_zero_and_allowance": (OUTSIDER, calldata("0x23b872dd", HOLDER, OUTSIDER, 1), unstaked_with_approval_override),
        "outsider_pull_as_new_staking_contract": (OUTSIDER, calldata("0x23b872dd", HOLDER, OUTSIDER, 1), new_staking_override),
        "holder_transfer_to_new_staking_contract": (HOLDER, calldata("0xa9059cbb", OUTSIDER, 1), new_staking_override),
        "old_staking_transfer_after_reassignment": (STAKING, calldata("0xa9059cbb", HOLDER, 1), new_staking_override),
        "holder_approve": (HOLDER, calldata("0x095ea7b3", OUTSIDER, 1), None),
        "owner_slot5_setter": (OWNER, calldata("0xd311b1a9", STAKING), None),
        "outsider_slot5_setter": (OUTSIDER, calldata("0xd311b1a9", STAKING), None),
        "owner_staking_setter": (OWNER, calldata("0x9dd373b9", STAKING), None),
        "outsider_staking_setter": (OUTSIDER, calldata("0x9dd373b9", STAKING), None),
        "minter_mint": (MINTER, calldata("0x40c10f19", HOLDER, 1), None),
        "owner_mint": (OWNER, calldata("0x40c10f19", HOLDER, 1), None),
        "minter_burn": (MINTER, calldata("0x9dc29fac", HOLDER, 1), None),
        "holder_burn": (HOLDER, calldata("0x9dc29fac", HOLDER, 1), None),
        "owner_set_minter": (OWNER, calldata("0xfca3b5aa", MINTER), None),
        "outsider_set_minter": (OUTSIDER, calldata("0xfca3b5aa", MINTER), None),
        "initializer_again": (OWNER, json.loads(deployment.read_text())["calls"][0]["input"], None),
    }
    probes = {name: call_case(url, sender, data, override) for name, (sender, data, override) in cases.items()}
    path.write_text(json.dumps({"pin_block": PIN, "pin_hash": manifest["block_hash"],
                                "getters": getters, "slots": slots,
                                "balance_slot": balance_slot, "staking_balance_slot": staking_balance_slot,
                                "allowance_slot": approval_slot,
                                "outsider_allowance_slot": outsider_approval_slot,
                                "probes": probes}, indent=2) + "\n")


def verify():
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    assert all("0x" + KECCAK(signature.encode()).hex()[:8] == selector
               for selector, signature in SELECTORS.items())
    assert all("0x" + KECCAK(signature.encode()).hex() == topic
               for signature, topic in EVENTS.items())
    assert all("0x" + KECCAK(signature.encode()).hex()[:8] == selector
               for signature, selector in ERRORS.items())
    deployment = json.loads((ARTIFACTS / "deployment.calls.json").read_text())
    assert deployment["type"] == "CREATE" and deployment["to"].lower() == TOKEN
    init = deployment["calls"][0]
    assert init["type"] == "DELEGATECALL" and init["to"].lower() == IMPLEMENTATION
    data = bytes.fromhex(init["input"][2:])
    assert data[:4].hex() == "8f15b414"
    arguments = [int.from_bytes(data[4 + i * 32:4 + (i + 1) * 32], "big") for i in range(4)]
    strings = []
    for offset in arguments[:2]:
        size = int.from_bytes(data[4 + offset:4 + offset + 32], "big")
        strings.append(data[4 + offset + 32:4 + offset + 32 + size].decode())
    assert strings == ["Paper", "PAPER"]
    assert f"0x{arguments[2]:040x}" == "0xa1763a5ff94ebddd417cccb906622ec762ab2e29"
    assert f"0x{arguments[3]:040x}" == MINTER
    deployment_receipt = json.loads((ARTIFACTS / "deployment.receipt.json").read_text())
    assert deployment_receipt["status"] == "0x1" and len(deployment_receipt["logs"]) == 2
    for log, signature, target in zip(deployment_receipt["logs"],
                                      ("OwnerUpdated(address)", "MinterUpdated(address)"),
                                      arguments[2:4]):
        assert log["address"].lower() == TOKEN
        assert log["topics"] == [EVENTS[signature], "0x" + word(target).hex()]
        assert log["data"] == "0x"
    for name, (tx, selector, slot, topic) in ADMIN_TXS.items():
        call = json.loads((HISTORICAL / f"{tx}.calls.json").read_text())
        receipt = json.loads((HISTORICAL / f"{tx}.receipt.json").read_text())
        diff = json.loads((HISTORICAL / f"{tx}.state_diff.json").read_text())
        assert call["to"].lower() == TOKEN and call["input"][:10] == selector
        target = int(call["input"][10:], 16)
        assert len(receipt["logs"]) == 1
        log = receipt["logs"][0]
        assert log["topics"] == [topic, "0x" + word(target).hex()] and log["data"] == "0x"
        assert int(diff["post"][TOKEN]["storage"]["0x" + word(slot).hex()], 16) == target
    saved = json.loads((ARTIFACTS / "pinned_probes.json").read_text())
    assert saved["pin_block"] == PIN and saved["pin_hash"] == manifest["block_hash"]
    getters, slots = saved["getters"], saved["slots"]
    for getter, slot in (("owner", "3"), ("minter", "4"), ("slot5", "5"),
                         ("staking_contract", "9"), ("total_supply", "6"),
                         ("holder_balance", "holder_balance"), ("staking_balance", "staking_balance")):
        assert int(getters[getter], 16) == int(slots[slot], 16)
    assert int(getters["owner"], 16) == int(OWNER, 16)
    assert int(getters["minter"], 16) == int(MINTER, 16)
    assert int(getters["slot5"], 16) == int(getters["staking_contract"], 16) == int(STAKING, 16)
    assert int(getters["holder_balance"], 16) > 0
    assert int(getters["holder_staking_allowance"], 16) == 2**256 - 1
    assert int(slots["holder_staking_allowance"], 16) == 0
    assert saved["balance_slot"] == mapping_slot(HOLDER, 7)
    assert saved["staking_balance_slot"] == mapping_slot(STAKING, 7)
    assert saved["allowance_slot"] == allowance_slot(HOLDER, STAKING)
    assert saved["outsider_allowance_slot"] == allowance_slot(HOLDER, OUTSIDER)
    probes = saved["probes"]
    ok = {"staking_transfer", "staking_zero_transfer", "staking_pull_into_staking",
          "staking_pull_without_allowance",
          "outsider_pull_as_new_staking_contract",
          "holder_approve", "owner_slot5_setter", "owner_staking_setter",
          "minter_mint", "minter_burn", "owner_set_minter"}
    assert set(probes) == ok | {"holder_transfer", "holder_zero_transfer", "staking_pull_elsewhere",
                                 "staking_overdraw", "initializer_again",
                                 "outsider_pull_without_allowance", "outsider_pull_to_staking_with_allowance",
                                 "outsider_pull_elsewhere_with_allowance",
                                 "holder_transfer_with_slot9_zero",
                                 "outsider_pull_with_slot9_zero_and_allowance",
                                 "holder_transfer_to_new_staking_contract",
                                 "old_staking_transfer_after_reassignment",
                                 "outsider_slot5_setter", "outsider_staking_setter", "owner_mint",
                                 "holder_burn", "outsider_set_minter"}
    assert all(probes[name]["ok"] for name in ok)
    assert all(int(probes[name]["output"], 16) == 1 for name in ok
               if name in {"staking_transfer", "staking_zero_transfer", "staking_pull_into_staking",
                           "staking_pull_without_allowance",
                           "outsider_pull_as_new_staking_contract",
                           "holder_approve"})
    errors = {"holder_transfer": "0xe827105e", "holder_zero_transfer": "0xe827105e",
              "staking_overdraw": "0xf4d678b8", "initializer_again": "0x0dc149f0",
              "staking_pull_elsewhere": "0xe827105e", "outsider_pull_without_allowance": "0x13be252b",
              "outsider_pull_to_staking_with_allowance": "0xe827105e",
              "outsider_pull_elsewhere_with_allowance": "0xe827105e",
              "holder_transfer_with_slot9_zero": "0xe827105e",
              "outsider_pull_with_slot9_zero_and_allowance": "0xe827105e",
              "holder_transfer_to_new_staking_contract": "0xe827105e",
              "old_staking_transfer_after_reassignment": "0xe827105e",
              "outsider_slot5_setter": "0x30cd7471", "outsider_staking_setter": "0x30cd7471",
              "owner_mint": "0xf8d2906c", "holder_burn": "0xf8d2906c",
              "outsider_set_minter": "0x30cd7471"}
    assert all(probes[name] == {"ok": False, "revert_selector": selector}
               for name, selector in errors.items())
    mutation_path = ARTIFACTS / "pinned_mutation_traces.json"
    mutations = json.loads(mutation_path.read_text())
    assert mutations["pin_block"] == PIN and mutations["pin_hash"] == manifest["block_hash"]
    cases = mutations["cases"]
    assert set(cases) == {"owner_set_new_minter", "outsider_set_new_minter",
                          "minter_burn_one", "minter_burn_over_balance"}
    for row in cases.values():
        assert len(row["implementation_calls"]) == 1
        child = row["implementation_calls"][0]
        assert child["type"] == "DELEGATECALL" and child["to"].lower() == IMPLEMENTATION
        assert child["input"] == row["calldata"]
    slot4, slot6, holder_slot = "0x" + word(4).hex(), "0x" + word(6).hex(), mapping_slot(HOLDER, 7)
    set_minter = cases["owner_set_new_minter"]
    assert set_minter["error"] is None
    assert int(set_minter["pre_storage"][slot4], 16) == int(MINTER, 16)
    assert int(set_minter["post_storage"][slot4], 16) == int(OUTSIDER, 16)
    assert len(set_minter["logs"]) == 1
    assert set_minter["logs"][0]["address"].lower() == TOKEN
    assert set_minter["logs"][0]["topics"] == [EVENTS["MinterUpdated(address)"],
                                                "0x" + word(OUTSIDER).hex()]
    assert set_minter["logs"][0]["data"] == "0x"
    burn = cases["minter_burn_one"]
    assert burn["error"] is None
    assert int(burn["pre_storage"][slot6], 16) - int(burn["post_storage"][slot6], 16) == 1
    assert int(burn["pre_storage"][holder_slot], 16) - int(burn["post_storage"][holder_slot], 16) == 1
    assert len(burn["logs"]) == 1
    assert burn["logs"][0]["address"].lower() == TOKEN
    assert burn["logs"][0]["topics"] == [EVENTS["Transfer(address,address,uint256)"],
                                        "0x" + word(HOLDER).hex(), "0x" + word(0).hex()]
    assert int(burn["logs"][0]["data"], 16) == 1
    for name, selector in (("outsider_set_new_minter", ERRORS["NotOwner()"]),
                           ("minter_burn_over_balance", ERRORS["InsufficientBalance()"] )):
        row = cases[name]
        assert row["error"] == "execution reverted" and row["output"][:10] == selector
        assert not row["logs"] and not row["post_storage"]
    staking = json.loads((ATLAS / "staking_behavior.json").read_text())
    tokenomics = json.loads((ATLAS / "tokenomics_observed_paths.json").read_text())
    assert staking["call_counts"]["0x83115825"] == 12
    assert staking["call_counts"]["0xfa2871b5"] == 2
    assert tokenomics["mint_count"] == 25
    result = {"pin_block": PIN, "token_proxy": TOKEN, "implementation": IMPLEMENTATION,
              "initializer": {"signature": SELECTORS["0x8f15b414"], "strings": strings,
                              "owner": f"0x{arguments[2]:040x}", "minter": MINTER},
              "admin_transactions": {name: tx for name, (tx, _, _, _) in ADMIN_TXS.items()},
              "pinned_probe_count": len(probes), "mutation_probe_count": len(cases),
              "mutation_storage_field_checks": 3, "mutation_events_verified": 2,
              "historical_stake_transfer_count": 12,
              "historical_unstake_transfer_count": 2, "historical_mint_count": 25,
              "selector_reconstructions": SELECTORS,
              "event_catalog": [{"topic0": topic, "reconstructed_signature": signature,
                                 "status": "observed_historical_topic"} for signature, topic in EVENTS.items()],
              "simulated_error_catalog": [{"selector": selector, "reconstructed_signature": signature,
                                           "probe_paths": [name for name, row in probes.items()
                                                           if row.get("revert_selector") == selector]}
                                          for signature, selector in ERRORS.items()],
              "auto_approved_spender_storage_slot": 5,
              "source_name_lead": "https://www.guardian.security/portfolio/papertrade/protocol-review-2026-10-09/",
              "limitations": ["The audit report is a source-name lead; no exact audited-source-to-runtime bytecode match has been established.",
                              "Pinned eth_call probes simulate execution and do not commit state.",
                              "State override results show one allowance branch, not every transfer boundary."]}
    (ATLAS / "paper_token_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PAPER token:", len(probes), "pinned call branches,", len(cases), "mutation traces, six exercised errors, three historical admin writes, deployment initializer, 20 selector preimages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-mutations", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    if args.capture_mutations:
        capture_mutations()
    verify()
