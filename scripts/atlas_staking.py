#!/usr/bin/env python3
"""Verify sampled Papertrade staking paths against signed calls and state diffs."""

import argparse
import json
import os
import pathlib

from atlas_factory_events import Keccak
from atlas_tokenomics import rpc

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
ARTIFACTS = ROOT / "artifacts"
STAKING_ARTIFACTS = ARTIFACTS / "staking"
PROXY = "0xaad6c7b0cc3014fc80ffedae0ed7ce5967b0f016"
IMPLEMENTATION = "0xe6e3519455170913c5c3bfe541dd918a2d0cbb15"
EXECUTOR = "0x233ff29b239abc1d7748605da9b205c3e008626e"
DEPLOYMENT_TX = "0xcd107566d243dc4984e0e157b5384018532e8f1b2b2495ebbc720c8e8aca955d"
TOKEN = "0xe40f17915daa230324030003a197cdaef2261c0e"
EXCHANGE = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
TOKENOMICS = "0x75174549dbbd44497d31a47e2e2d7406408d63d9"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
PRECISION = 10**27
KECCAK = Keccak()

SIGNED = {
    "0x83115825": ("stakeBySig(address,uint256,uint256,uint64,uint8,bytes32,bytes32)",
                   "Stake(address user,uint256 amount,uint256 nonce,uint64 deadline)", "0x89ee09f0"),
    "0xfa2871b5": ("unstakeBySig(address,uint256,uint256,uint64,uint8,bytes32,bytes32)",
                   "Unstake(address user,uint256 amount,uint256 nonce,uint64 deadline)", "0x0700cc42"),
    "0x9c96d4a1": ("claimBySig(address,uint256,uint64,uint8,bytes32,bytes32)",
                   "Claim(address user,uint256 nonce,uint64 deadline)", "0x6b0509b1"),
    "0xf0355460": ("distributeBySig(address,uint256,uint64,uint8,bytes32,bytes32)",
                   "Distribute(address user,uint256 nonce,uint64 deadline)", "0x5638b3e5"),
}
EVENTS = {
    "NonceUsed(address,uint256,uint256)": "0x3fde1edb52bbe023081a01c60e06e15396e067be4699a5044fdfa793f67bfc28",
    "Staked(address,uint256)": "0x9e71bc8eea02a63969f509818f2dafb9254532904319f9dbda79b67bd34a5f3d",
    "Unstaked(address,uint256)": "0x0f5bb82176feb1b5e747e28471aa92156a04d9f3ab9f45f28e2d704232b93f75",
    "Claimed(address,uint256)": "0xd8138f8a3f377c5259ca548e70e4c2de94f129f5a11036a15b69513cba2b426a",
    "Distributed(uint256,uint256,uint256,uint256)": "0xf7576d8c2653e9d07af5ef229acf59b339e327d4e0eaddb4a96615534cf148f8",
    "AuthorizedExecutorUpdated(address)": "0x3cfda8ee6e20b237d2949c3d16b6f12822b6f1bc0580f188f932c0771cac729d",
    "OwnerUpdated(address)": "0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b",
}


def all_calls(call):
    yield call
    for child in call.get("calls", []):
        yield from all_calls(child)


def words(data):
    assert data.startswith("0x") and (len(data) - 2) % 64 == 0
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def input_words(call):
    return words("0x" + call["input"][10:])


def word(value):
    return value.to_bytes(32, "big")


def address(value):
    return f"0x{value:040x}"


def mapping_slot(user, base):
    return "0x" + KECCAK(word(user) + word(base)).hex()


def bitmap_slot(user, nonce):
    return "0x" + KECCAK(word(nonce >> 8) + KECCAK(word(user) + word(14))).hex()


def account_storage(diff, side):
    return diff[side].get(PROXY, {}).get("storage", {})


def slot_delta(diff, slot):
    before = account_storage(diff, "pre").get(slot, "0x0")
    after = account_storage(diff, "post").get(slot, "0x0" if slot in account_storage(diff, "pre") else before)
    return int(after, 16) - int(before, 16)


def find_artifact(tx, suffix):
    paths = [ARTIFACTS / directory / f"{tx}.{suffix}.json"
             for directory in ("session_keys", "tokenomics", "historical")]
    found = [path for path in paths if path.exists()]
    assert len(found) == 1, (tx, suffix, found)
    return found[0]


def trace_paths():
    chosen = {}
    for directory, pattern in (("session_keys", "*.calls.json"),
                               ("tokenomics", "*.calls.json"),
                               ("tokenomics", "*.calls_with_logs.json")):
        for path in sorted((ARTIFACTS / directory).glob(pattern)):
            tx = path.name.split(".")[0]
            root = json.loads(path.read_text())
            if any(call.get("to", "").lower() == PROXY
                   and call.get("input", "")[:10] in SIGNED for call in all_calls(root)):
                chosen[tx] = path
    return chosen


def capture_deployment():
    STAKING_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    for suffix, method, params in (("calls", "debug_traceTransaction", [DEPLOYMENT_TX, {"tracer": "callTracer"}]),
                                   ("receipt", "eth_getTransactionReceipt", [DEPLOYMENT_TX])):
        path = STAKING_ARTIFACTS / f"deployment.{suffix}.json"
        if not path.exists():
            path.write_text(json.dumps(rpc(url, method, params), indent=2) + "\n")


def verify_deployment():
    trace = json.loads((STAKING_ARTIFACTS / "deployment.calls.json").read_text())
    receipt = json.loads((STAKING_ARTIFACTS / "deployment.receipt.json").read_text())
    assert trace["type"] == "CREATE" and trace["to"].lower() == PROXY
    assert len(trace["calls"]) == 1
    init = trace["calls"][0]
    assert init["type"] == "DELEGATECALL" and init["to"].lower() == IMPLEMENTATION
    assert init["input"][:10] == "0x9ccae24e" and len(init["input"]) == 330
    args = [address(x) for x in input_words(init)]
    assert args == [EXCHANGE, TOKEN, "0x6b9e773128f453f5c2c60935ee2de2cbc5390a24",
                    "0xa1763a5ff94ebddd417cccb906622ec762ab2e29", address(0)]
    assert receipt["status"] == "0x1" and receipt["transactionHash"] == DEPLOYMENT_TX
    assert len(receipt["logs"]) == 2
    assert [log["topics"][0] for log in receipt["logs"]] == [EVENTS["OwnerUpdated(address)"],
        EVENTS["AuthorizedExecutorUpdated(address)"]]
    assert receipt["logs"][0]["topics"][1] == "0x" + word(int(args[3], 16)).hex()
    assert receipt["logs"][1]["topics"][1] == "0x" + word(0).hex()
    return {"tx": DEPLOYMENT_TX, "selector": "0x9ccae24e", "arguments": args,
            "event_count": len(receipt["logs"])}


def capture_staking_prestates():
    STAKING_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    header = rpc(url, "eth_getBlockByNumber", [hex(48902346), False])
    assert header["hash"].lower() == manifest["block_hash"]
    for tx, path in trace_paths().items():
        output = STAKING_ARTIFACTS / f"{tx}.prestate.json"
        if not output.exists():
            state = rpc(url, "debug_traceTransaction", [tx, {"tracer": "prestateTracer"}])
            output.write_text(json.dumps(state, indent=2) + "\n")
        print("staking prestate", tx, flush=True)


def capture_nonce_getters():
    output = STAKING_ARTIFACTS / "pinned_nonce_getters.json"
    if output.exists():
        return
    STAKING_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    rows = []
    users = set()
    for _, path in sorted(trace_paths().items()):
        root = json.loads(path.read_text())
        for call in all_calls(root):
            if call.get("to", "").lower() != PROXY or call.get("input", "")[:10] not in SIGNED:
                continue
            args = input_words(call)
            user = args[0]
            nonce = args[2] if len(args) == 7 else args[1]
            if user in users:
                continue
            users.add(user)
            base = word(user).hex()
            bitmap = bitmap_slot(user, nonce)
            counter_slot = mapping_slot(user, 12)
            rows.append({"user": address(user), "nonce": nonce, "word_index": nonce >> 8,
                         "bitmap_slot": bitmap, "counter_slot": counter_slot,
                         "bitmap_getter": rpc(url, "eth_call", [{"to": PROXY,
                             "data": "0xf2f59776" + base + word(nonce >> 8).hex()}, hex(48902346)]),
                         "used_getter": rpc(url, "eth_call", [{"to": PROXY,
                             "data": "0xcab7e8eb" + base + word(nonce).hex()}, hex(48902346)]),
                         "counter_getter": rpc(url, "eth_call", [{"to": PROXY,
                             "data": "0x7ecebe00" + base}, hex(48902346)]),
                         "bitmap_storage": rpc(url, "eth_getStorageAt", [PROXY, bitmap, hex(48902346)]),
                         "counter_storage": rpc(url, "eth_getStorageAt", [PROXY, counter_slot, hex(48902346)])})
            if len(rows) == 3:
                break
        if len(rows) == 3:
            break
    assert len(rows) == 3
    output.write_text(json.dumps({"pin_block": 48902346, "pin_hash": manifest["block_hash"],
                                  "samples": rows}, indent=2) + "\n")
    print("captured pinned staking nonce getters", flush=True)


def verify_nonce_getters():
    saved = json.loads((STAKING_ARTIFACTS / "pinned_nonce_getters.json").read_text())
    assert saved["pin_block"] == 48902346
    assert saved["pin_hash"] == json.loads((ATLAS / "manifest.json").read_text())["block_hash"]
    assert len(saved["samples"]) == 3
    for row in saved["samples"]:
        user, nonce = int(row["user"], 16), row["nonce"]
        assert row["bitmap_slot"] == bitmap_slot(user, nonce)
        assert row["counter_slot"] == mapping_slot(user, 12)
        assert int(row["bitmap_getter"], 16) == int(row["bitmap_storage"], 16)
        assert int(row["bitmap_getter"], 16) & (1 << (nonce & 255))
        assert int(row["used_getter"], 16) == 1
        assert int(row["counter_getter"], 16) == int(row["counter_storage"], 16)
    return len(saved["samples"])


def capture_direct_probes():
    output = STAKING_ARTIFACTS / "pinned_direct_probes.json"
    STAKING_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    user = "0xbbb9512a5843441a8435d8f745fce97eb6a9eebf"
    if output.exists():
        saved = json.loads(output.read_text())
        if "funded_staker_balance" in saved:
            return
        assert saved["pin_hash"] == manifest["block_hash"]
    else:
        saved = None
    outsider = "0x3333333333333333333333333333333333333333"
    cases = [
        ("stake_one", user, "0xa694fc3a", [10**18]),
        ("stake_zero", user, "0xa694fc3a", [0]),
        ("unstake_one", user, "0x2e17de78", [10**18]),
        ("unstake_zero", user, "0x2e17de78", [0]),
        ("claim_user", user, "0x4e71d92d", []),
        ("claim_outsider", outsider, "0x4e71d92d", []),
        ("distribute_user", user, "0xe4fc6b6d", []),
    ]
    if saved is None:
        rows = []
        for name, sender, selector, args in cases:
            call = {"from": sender, "to": PROXY,
                    "data": selector + "".join(word(value).hex() for value in args), "value": "0x0"}
            trace = rpc(url, "debug_traceCall", [call, hex(48902346), {"tracer": "callTracer",
                                                             "tracerConfig": {"withLog": True}}])
            rows.append({"name": name, "call": call, "trace": trace})
            print("staking probe", name, trace.get("error", "success"), trace.get("output", "")[:10], flush=True)
        saved = {"pin_block": 48902346, "pin_hash": manifest["block_hash"],
                 "funded_staker": user, "probes": rows}
    user_word = word(int(user, 16)).hex()
    saved["funded_staker_balance"] = rpc(url, "eth_call", [{"to": TOKEN,
        "data": "0x70a08231" + user_word}, hex(48902346)])
    saved["funded_staker_allowance"] = rpc(url, "eth_call", [{"to": TOKEN,
        "data": "0xdd62ed3e" + user_word + word(int(PROXY, 16)).hex()}, hex(48902346)])
    saved["funded_staker_deposit"] = rpc(url, "eth_call", [{"to": PROXY,
        "data": "0x60217267" + user_word}, hex(48902346)])
    output.write_text(json.dumps(saved, indent=2) + "\n")
    print("captured funded staking probe preconditions", flush=True)


def verify_direct_probes():
    saved = json.loads((STAKING_ARTIFACTS / "pinned_direct_probes.json").read_text())
    assert saved["pin_block"] == 48902346
    assert saved["pin_hash"] == json.loads((ATLAS / "manifest.json").read_text())["block_hash"]
    assert int(saved["funded_staker_balance"], 16) >= 10**18
    assert int(saved["funded_staker_allowance"], 16) >= 10**18
    assert int(saved["funded_staker_deposit"], 16) >= 10**18
    names = {row["name"] for row in saved["probes"]}
    assert names == {"stake_one", "stake_zero", "unstake_one", "unstake_zero",
                     "claim_user", "claim_outsider", "distribute_user"}
    for row in saved["probes"]:
        trace = row["trace"]
        assert trace.get("error") == "execution reverted"
        assert trace.get("output") == "0xa15ce1ba"
        assert not any(call.get("logs") for call in all_calls(trace))
    return {"count": len(saved["probes"]), "revert_selector": "0xa15ce1ba"}


def capture_reward_getters():
    output = STAKING_ARTIFACTS / "pinned_reward_getters.json"
    if output.exists():
        return
    STAKING_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    url = os.environ["PAPERTRADE_ARCHIVE_RPC"]
    manifest = json.loads((ATLAS / "manifest.json").read_text())
    accumulator = rpc(url, "eth_call", [{"to": PROXY, "data": "0x939d6237"}, hex(48902346)])
    rows = []
    for user in ("0x50652414f490853dc3ba30a25c49eb6ed7bdebc2",
                 "0xf417448e1e73d4b31610a6e23ade1437c1c99970",
                 "0x98438465100a198798b1add373784323c67a8a26"):
        user_word = word(int(user, 16)).hex()
        storage = {}
        for base in (9, 10, 11):
            slot = mapping_slot(int(user, 16), base)
            storage[str(base)] = {"slot": slot,
                                  "value": rpc(url, "eth_getStorageAt", [PROXY, slot, hex(48902346)])}
        pending = rpc(url, "eth_call", [{"to": PROXY,
                                         "data": "0xf40f0f52" + user_word}, hex(48902346)])
        rows.append({"user": user, "storage": storage, "pending_reward_getter": pending})
    output.write_text(json.dumps({"pin_block": 48902346, "pin_hash": manifest["block_hash"],
                                  "acc_reward_per_share": accumulator,
                                  "samples": rows}, indent=2) + "\n")
    print("captured pinned staking reward getters", flush=True)


def verify_reward_getters():
    saved = json.loads((STAKING_ARTIFACTS / "pinned_reward_getters.json").read_text())
    assert saved["pin_block"] == 48902346
    assert saved["pin_hash"] == json.loads((ATLAS / "manifest.json").read_text())["block_hash"]
    assert len(saved["samples"]) == 3
    accumulator = int(saved["acc_reward_per_share"], 16)
    for row in saved["samples"]:
        user = int(row["user"], 16)
        values = {}
        for base in (9, 10, 11):
            field = row["storage"][str(base)]
            assert field["slot"] == mapping_slot(user, base)
            values[base] = int(field["value"], 16)
        expected = values[11] + values[9] * accumulator // PRECISION - values[10]
        assert expected >= 0 and expected == int(row["pending_reward_getter"], 16)
    return len(saved["samples"])


def verify_hashes():
    views = json.loads((ATLAS / "storage_trace_catalog.json").read_text())[IMPLEMENTATION]["views"]
    observed = {row["selector"]: row["return_prefix"] for row in views if not row["failed"]}
    domain = bytes.fromhex(observed["0x3644e515"][2:])
    assert observed["0x78e890ba"] == observed["0x3644e515"]
    for selector, (signature, type_string, getter) in SIGNED.items():
        assert "0x" + KECCAK(signature.encode())[:4].hex() == selector
        assert "0x" + KECCAK(type_string.encode())[:4].hex() != getter
        assert "0x" + KECCAK(({
            "0x89ee09f0": "STAKE_TYPEHASH()",
            "0x0700cc42": "UNSTAKE_TYPEHASH()",
            "0x6b0509b1": "CLAIM_TYPEHASH()",
            "0x5638b3e5": "DISTRIBUTE_TYPEHASH()",
        }[getter]).encode())[:4].hex() == getter
        assert "0x" + KECCAK(type_string.encode()).hex() == observed[getter]
    for signature, topic in EVENTS.items():
        assert "0x" + KECCAK(signature.encode()).hex() == topic
    assert "0x" + KECCAK(b"nonceBitmapWord(address,uint256)")[:4].hex() == "0xf2f59776"
    assert "0x" + KECCAK(b"isNonceUsed(address,uint256)")[:4].hex() == "0xcab7e8eb"
    return domain


def replay_staking_accounting(tx, root, diff):
    prestate = json.loads((STAKING_ARTIFACTS / f"{tx}.prestate.json").read_text())[PROXY]["storage"]
    changed_before = account_storage(diff, "pre")
    changed_after = account_storage(diff, "post")

    def starting(slot):
        return int(prestate.get(slot, "0x0"), 16)

    def final(slot):
        if slot in changed_after:
            return int(changed_after[slot], 16)
        if slot in changed_before:
            return 0
        return starting(slot)

    accumulator = starting(f"0x{6:064x}")
    total_staked = starting(f"0x{5:064x}")
    reserve = starting(f"0x{7:064x}")
    users = {}
    claims = 0
    for call in all_calls(root):
        selector = call.get("input", "")[:10]
        if call.get("to", "").lower() != PROXY or selector not in SIGNED:
            continue
        args = input_words(call)
        user = args[0]
        if user not in users:
            users[user] = [starting(mapping_slot(user, base)) for base in (9, 10, 11)]
        balance, debt, pending = users[user]
        logs = [log for nested in all_calls(call) for log in nested.get("logs", [])
                if log["address"].lower() == PROXY]
        if selector == "0xf0355460":
            distribution = [log for log in logs
                            if log["topics"][0] == EVENTS["Distributed(uint256,uint256,uint256,uint256)"]]
            assert len(distribution) == 1 and total_staked > 0
            reserve_after, received, allocated, accumulator_after = words(distribution[0]["data"])
            reserve += received
            accumulator += allocated * PRECISION // total_staked
            assert reserve == reserve_after and accumulator == accumulator_after
        elif selector == "0x9c96d4a1":
            claim = pending + balance * accumulator // PRECISION - debt
            assert claim >= 0 and int(call["output"], 16) == claim
            claims += 1
            reserve -= claim
            pending = 0
            debt = balance * accumulator // PRECISION
        else:
            accrued = balance * accumulator // PRECISION - debt
            assert accrued >= 0
            pending += accrued
            amount = args[1]
            delta = amount if selector == "0x83115825" else -amount
            balance += delta
            total_staked += delta
            assert balance >= 0 and total_staked >= 0
            debt = balance * accumulator // PRECISION
        users[user] = [balance, debt, pending]
    checks = 0
    for user, (balance, debt, pending) in users.items():
        for base, expected in ((9, balance), (10, debt), (11, pending)):
            assert final(mapping_slot(user, base)) == expected, (tx, address(user), base)
            checks += 1
    for base, expected in ((5, total_staked), (6, accumulator), (7, reserve)):
        assert final(f"0x{base:064x}") == expected, (tx, base)
        checks += 1
    return {"storage_field_checks": checks, "claim_amount_checks": claims,
            "user_count": len(users)}


def analyze():
    domain = verify_hashes()
    calls_out = []
    tx_out = []
    replay_checks = 0
    claim_checks = 0
    zero_excess_distributions = []
    sources = trace_paths()
    assert len(sources) == 14
    for tx, path in sorted(sources.items()):
        root = json.loads(path.read_text())
        diff = json.loads(find_artifact(tx, "state_diff").read_text())
        receipt = json.loads(find_artifact(tx, "receipt").read_text())
        assert int(receipt["status"], 16) == 1
        signed_calls = [call for call in all_calls(root)
                        if call.get("to", "").lower() == PROXY
                        and call.get("input", "")[:10] in SIGNED]
        expected_staked = 0
        expected_reserve = 0
        expected_staked_by_user = {}
        counters = {}
        for ordinal, call in enumerate(signed_calls):
            selector = call["input"][:10]
            signature, type_string, _ = SIGNED[selector]
            args = input_words(call)
            with_amount = selector in ("0x83115825", "0xfa2871b5")
            assert len(args) == (7 if with_amount else 6)
            user = args[0]
            amount = args[1] if with_amount else None
            nonce, deadline, v, r, s = args[2:] if with_amount else args[1:]
            assert call["from"].lower() == EXECUTOR and not call.get("error")
            assert deadline <= (1 << 64) - 1 and v in (27, 28)
            struct_values = [user, amount, nonce, deadline] if with_amount else [user, nonce, deadline]
            struct_hash = KECCAK(KECCAK(type_string.encode()) + b"".join(word(x) for x in struct_values))
            digest = KECCAK(b"\x19\x01" + domain + struct_hash)
            recovered = [child for child in all_calls(call)
                         if child.get("to", "").lower() == "0x0000000000000000000000000000000000000001"]
            assert len(recovered) == 1
            assert bytes.fromhex(recovered[0]["input"][2:]) == digest + word(v) + word(r) + word(s)
            assert int(recovered[0]["output"], 16) == user
            logs = [log for nested in all_calls(call) for log in nested.get("logs", [])]
            staking_logs = [log for log in logs if log["address"].lower() == PROXY]
            nonce_logs = [log for log in staking_logs if log["topics"][0] == EVENTS["NonceUsed(address,uint256,uint256)"]]
            assert len(nonce_logs) == 1
            nonce_log = nonce_logs[0]
            assert len(nonce_log["topics"]) == 3
            assert int(nonce_log["topics"][1], 16) == user
            assert int(nonce_log["topics"][2], 16) == nonce
            counter = int(nonce_log["data"], 16)
            assert counter >= nonce + 1
            counter_slot = mapping_slot(user, 12)
            if user not in counters and counter_slot in account_storage(diff, "pre"):
                counters[user] = int(account_storage(diff, "pre")[counter_slot], 16)
            if user in counters:
                counters[user] = max(counters[user], nonce + 1)
                assert counter == counters[user]
            bitmap = bitmap_slot(user, nonce)
            before_bitmap = int(account_storage(diff, "pre").get(bitmap, "0x0"), 16)
            after_bitmap = int(account_storage(diff, "post").get(bitmap, "0x0"), 16)
            assert not before_bitmap & (1 << (nonce & 255))
            assert after_bitmap & (1 << (nonce & 255))
            expected_event = {
                "0x83115825": "Staked(address,uint256)",
                "0xfa2871b5": "Unstaked(address,uint256)",
                "0x9c96d4a1": "Claimed(address,uint256)",
                "0xf0355460": "Distributed(uint256,uint256,uint256,uint256)",
            }[selector]
            action_logs = [log for log in staking_logs if log["topics"][0] == EVENTS[expected_event]]
            assert len(action_logs) == 1
            action = action_logs[0]
            nested_calls = list(all_calls(call))
            outcome = None
            if with_amount:
                assert len(action["topics"]) == 2 and int(action["topics"][1], 16) == user
                assert int(action["data"], 16) == amount
                token_selector = "0x23b872dd" if selector == "0x83115825" else "0xa9059cbb"
                token_calls = [item for item in nested_calls if item.get("to", "").lower() == TOKEN
                               and item.get("input", "")[:10] == token_selector]
                assert len(token_calls) == 1 and int(token_calls[0]["output"], 16) == 1
                token_args = input_words(token_calls[0])
                assert token_args == ([user, int(PROXY, 16), amount] if selector == "0x83115825"
                                      else [user, amount])
                transfer_logs = [log for log in logs if log["address"].lower() == TOKEN
                                 and log["topics"][0] == TRANSFER]
                assert len(transfer_logs) == 1
                src, dst = (user, int(PROXY, 16)) if selector == "0x83115825" else (int(PROXY, 16), user)
                assert [int(x, 16) for x in transfer_logs[0]["topics"][1:]] == [src, dst]
                assert int(transfer_logs[0]["data"], 16) == amount
                sign = 1 if selector == "0x83115825" else -1
                expected_staked += sign * amount
                expected_staked_by_user[user] = expected_staked_by_user.get(user, 0) + sign * amount
                outcome = amount
            elif selector == "0x9c96d4a1":
                assert len(action["topics"]) == 2 and int(action["topics"][1], 16) == user
                outcome = int(action["data"], 16)
                assert int(call["output"], 16) == outcome
                exchange_calls = [item for item in nested_calls if item.get("to", "").lower() == EXCHANGE
                                  and item.get("input", "")[:10] == "0xe53e3de6"]
                assert len(exchange_calls) == 1 and input_words(exchange_calls[0]) == [user, outcome]
                expected_reserve -= outcome
            else:
                assert len(action["topics"]) == 1
                fields = words(action["data"])
                assert len(fields) == 4 and fields[1] == fields[2]
                exchange_calls = [item for item in nested_calls if item.get("to", "").lower() == EXCHANGE
                                  and item.get("input", "")[:10] == "0x7b9f5264"]
                assert len(exchange_calls) == 1
                adjustments = [item for item in nested_calls if item.get("to", "").lower() == TOKENOMICS
                               and item.get("input", "")[:10] == "0xc218c676"]
                assert len(adjustments) <= 1
                if not adjustments:
                    excess_getters = [item for item in nested_calls if item.get("to", "").lower() == TOKENOMICS
                                      and item.get("input", "")[:10] == "0xae745703"]
                    assert len(excess_getters) == 1 and int(excess_getters[0]["output"], 16) == 0
                    assert TOKENOMICS not in diff.get("pre", {}) and TOKENOMICS not in diff.get("post", {})
                    zero_excess_distributions.append({"tx": tx, "event_fields": fields,
                                                      "tokenomics_excess_getter_output": 0,
                                                      "tokenomics_adjustment_call_count": 0})
                assert fields[0] == int(account_storage(diff, "post")[f"0x{7:064x}"], 16)
                assert fields[3] == int(account_storage(diff, "post")[f"0x{6:064x}"], 16)
                prestate = json.loads((STAKING_ARTIFACTS / f"{tx}.prestate.json").read_text())
                storage = prestate[PROXY]["storage"]
                total_staked = int(storage[f"0x{5:064x}"], 16)
                assert total_staked > 0
                assert int(storage[f"0x{8:064x}"], 16) == 0
                assert fields[2] * PRECISION // total_staked == slot_delta(diff, f"0x{6:064x}")
                expected_reserve += fields[1]
                outcome = fields
            calls_out.append({"tx": tx, "ordinal": ordinal, "selector": selector,
                              "reconstructed_signature": signature, "user": address(user),
                              "nonce": nonce, "deadline": deadline, "digest": "0x" + digest.hex(),
                              "recovered_signer": address(int(recovered[0]["output"], 16)),
                              "nonce_counter_after": counter, "event_topic": action["topics"][0],
                              "amount_or_distribution_fields": outcome})
        assert slot_delta(diff, f"0x{5:064x}") == expected_staked
        assert slot_delta(diff, f"0x{7:064x}") == expected_reserve
        for user, delta in expected_staked_by_user.items():
            assert slot_delta(diff, mapping_slot(user, 9)) == delta, (
                tx, address(user), delta, slot_delta(diff, mapping_slot(user, 9)))
        for user, counter in counters.items():
            slot = mapping_slot(user, 12)
            if slot in account_storage(diff, "post"):
                assert int(account_storage(diff, "post")[slot], 16) == counter
        replay = replay_staking_accounting(tx, root, diff)
        replay_checks += replay["storage_field_checks"]
        claim_checks += replay["claim_amount_checks"]
        tx_out.append({"tx": tx, "block": int(receipt["blockNumber"], 16),
                       "signed_call_count": len(signed_calls), "staked_delta": str(expected_staked),
                       "reward_reserve_delta": str(expected_reserve),
                       "accounting_replay": replay,
                       "storage_checks": "passed"})
    counts = {selector: sum(row["selector"] == selector for row in calls_out) for selector in SIGNED}
    assert len(calls_out) == 45 and len(tx_out) == 14
    assert [row["tx"] for row in zero_excess_distributions] == [
        "0xb27bbadf830f5673211719cf6585d9929e91a446c3f46aee940e6e2e02888cdb"]
    assert replay_checks == 177 and claim_checks == 26
    assert counts == {"0x83115825": 12, "0xfa2871b5": 2, "0x9c96d4a1": 26, "0xf0355460": 5}
    result = {"pin_block": 48902346, "staking_proxy": PROXY, "implementation": IMPLEMENTATION,
              "sampled_transaction_count": len(tx_out), "signed_call_count": len(calls_out),
              "accounting_storage_field_checks": replay_checks,
              "accounting_claim_amount_checks": claim_checks,
              "pinned_nonce_getter_samples": verify_nonce_getters(),
              "pinned_direct_probes": verify_direct_probes(),
              "pinned_reward_getter_samples": verify_reward_getters(),
              "distribution_without_tokenomics_adjustment": zero_excess_distributions,
              "deployment_initializer": verify_deployment(),
              "selector_reconstructions": {selector: row[0] for selector, row in SIGNED.items()} |
                                          {"0x5638b3e5": "DISTRIBUTE_TYPEHASH()",
                                           "0xf2f59776": "nonceBitmapWord(address,uint256)",
                                           "0xcab7e8eb": "isNonceUsed(address,uint256)"},
              "typehash_preimages": {selector: row[1] for selector, row in SIGNED.items()},
              "event_catalog": [{"topic0": topic, "reconstructed_signature": signature,
                                 "status": "observed_historical"} for signature, topic in EVENTS.items()],
              "call_counts": counts, "transactions": tx_out, "calls": calls_out,
              "limitations": ["Signed call samples cover four active paths and do not prove all input boundaries.",
                              "Reward-debt and pending-reward equations match sampled calls; unusual states remain untested.",
                              "Both initializer names and one packed-state getter name remain open; the five-address initializer has one verified deployment trace."]}
    (ATLAS / "staking_behavior.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Verified {len(calls_out)} signed staking calls in {len(tx_out)} transactions")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture_deployment()
        capture_staking_prestates()
        capture_nonce_getters()
        capture_direct_probes()
        capture_reward_getters()
    analyze()
