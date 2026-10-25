"""Build and check exact PT-01 deployment and governance payloads against the live set."""

import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess

from atlas_factory_events import Keccak
from recovery import deploy
from recovery.current_rpc import rpc, rpc_call
from recovery.live_facts import EXCHANGE, IMPLEMENTATION_SLOT, LIVE_FACTS

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "production_plan_20261022.json"
COMPILED = HERE / "compiled.json"
FACTORY = deploy.FACTORY
FACTORY_CODE_SHA256 = "e0af82ad2e5188285db8ba0b2ae054d13f0fd4fe325c48c7f2dace48454404b9"
LIVE_IMPLEMENTATION = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
PINNED_IMPLEMENTATION = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PROXY_ADMIN = "0xe79c91cc682f1bb401a9cab74c900470190f0f8f"
TIMELOCK = "0xb915fa41e824d6aa31bb833ee81220c0f2c8ea0f"
MULTISIG = "0x696292762fd5ac3677a45edbe54eaece4194d1f6"
SKM_PROXY = "0x8326eb8896e358717f10502ec73ce8d28e37b108"
SKM_PENDING_IMPLEMENTATION = "0x0a2db5c7614b714fd9ec12b29bff3b4f4c545d82"
SKM_PREDECESSOR = "0x65a4ca136380fa593c43a77c7189b87d41fb27ee25deafd51efc7de2087ef2c0"
USER1 = "0x56cbe78a5cdfa10147927aec550aa7f2fb3d3d01"
USER2 = "0x9c8599c32224d7d9956a7def18f7314162f77baf"
ZERO = "0x" + "00" * 32


def cast_calldata(signature, *arguments):
    result = subprocess.run(
        ["cast", "calldata", signature, *map(str, arguments)],
        capture_output=True,
        check=True,
        text=True,
        timeout=10,
    )
    value = result.stdout.strip()
    assert value.startswith("0x")
    return value


def operation_id(target, data, predecessor=ZERO):
    encoded = (
        int(target, 16).to_bytes(32, "big")
        + bytes(32)
        + Keccak()(bytes.fromhex(data[2:]))
        + bytes.fromhex(predecessor[2:])
    )
    return "0x" + Keccak()(encoded).hex()


def operation_slot(identifier):
    return "0x" + Keccak()(bytes.fromhex(identifier[2:]) + (2).to_bytes(32, "big")).hex()


def pending_operation():
    """The governance operation already sitting in the timelock, re-derived from its record.

    Multisig record 11 scheduled a SessionKeyManager proxy upgrade, so one timelock slot is
    occupied. It targets a different proxy and carries a non-zero predecessor, so it shares
    no operation id with the eight Exchange recovery operations.
    """
    data = cast_calldata("upgrade(address,address)", SKM_PROXY, SKM_PENDING_IMPLEMENTATION)
    assert data.startswith("0x99a88ec4"), "ProxyAdmin.upgrade(address,address)"
    identifier = operation_id(PROXY_ADMIN, data, SKM_PREDECESSOR)
    return {
        "source": "atlas/block_48902346/live2_authority.md, multisig record 11 schedule payload",
        "target": PROXY_ADMIN,
        "target_calldata": data,
        "target_inner": SKM_PROXY,
        "target_inner_implementation": SKM_PENDING_IMPLEMENTATION,
        "predecessor": SKM_PREDECESSOR,
        "operation_id": identifier,
        "operation_storage_slot": operation_slot(identifier),
        "note": "A SessionKeyManager proxy upgrade. It changes no Exchange storage and shares no "
                "operation id with the eight recovery operations, which use a zero predecessor.",
    }


def offline_plan():
    compiled = json.loads(COMPILED.read_text())
    init = bytes.fromhex(compiled["init_code"][2:])
    assert hashlib.sha256(init).hexdigest() == compiled["init_code_sha256"]
    predicted = deploy.predicted_address(compiled["init_code"])
    assert predicted == deploy.address()
    actions = [
        ("upgrade", PROXY_ADMIN, cast_calldata("upgrade(address,address)", EXCHANGE, predicted)),
        ("enqueue_small", EXCHANGE, cast_calldata("rescueEnqueue(address)", USER2)),
        ("residual_small", EXCHANGE, cast_calldata("rescueEnqueueResidual(address)", USER2)),
        ("finalize_small", EXCHANGE, cast_calldata("rescueFinalize(address)", USER2)),
        ("enqueue_large", EXCHANGE, cast_calldata("rescueEnqueue(address)", USER1)),
        ("residual_large", EXCHANGE, cast_calldata("rescueEnqueueResidual(address)", USER1)),
        ("finalize_large", EXCHANGE, cast_calldata("rescueFinalize(address)", USER1)),
        ("restore_live", PROXY_ADMIN, cast_calldata("upgrade(address,address)", EXCHANGE, LIVE_IMPLEMENTATION)),
    ]
    operations = []
    for name, target, data in actions:
        schedule = cast_calldata("schedule(address,uint256,bytes,bytes32)", target, 0, data, ZERO)
        execute = cast_calldata("execute(address,uint256,bytes,bytes32)", target, 0, data, ZERO)
        operations.append({
            "name": name,
            "target": target,
            "value_wei": 0,
            "target_calldata": data,
            "predecessor": ZERO,
            "operation_id": operation_id(target, data),
            "operation_storage_slot": operation_slot(operation_id(target, data)),
            "timelock_schedule_calldata": schedule,
            "timelock_execute_calldata": execute,
            "multisig_submit_schedule_calldata": cast_calldata(
                "submitTransaction(address,uint256,bytes)", TIMELOCK, 0, schedule
            ),
            "multisig_submit_execute_calldata": cast_calldata(
                "submitTransaction(address,uint256,bytes)", TIMELOCK, 0, execute
            ),
        })
    assert len({row["operation_id"] for row in operations}) == len(operations) == 8
    return {
        "chain_id": 999,
        "compiled_code_sha256": compiled["deployed_code_sha256"],
        "factory": FACTORY,
        "factory_code_sha256": FACTORY_CODE_SHA256,
        "salt": deploy.salt(),
        "salt_label": deploy.SALT_LABEL.decode(),
        "init_code_sha256": compiled["init_code_sha256"],
        "factory_deployment_calldata": deploy.deployment_calldata(compiled["init_code"]),
        "candidate_address": predicted,
        "exchange_proxy": EXCHANGE,
        "live_implementation": LIVE_IMPLEMENTATION,
        "pinned_implementation": PINNED_IMPLEMENTATION,
        "restore_implementation": LIVE_IMPLEMENTATION,
        "proxy_admin": PROXY_ADMIN,
        "timelock": TIMELOCK,
        "multisig": MULTISIG,
        "operations": operations,
        "pending_governance_operation": pending_operation(),
        "approval_gate": "Do not submit deployment, schedule, execute, or CoreWriter actions without explicit maintainer and Papertrade governance approval.",
        "execution_rule": "Schedule operations under the live minimum delay. Execute upgrade, then the smaller enqueue. Verify Core execution and both ledgers before its finalize or residual send. Repeat for the larger case. Restore the live implementation after both active bits and pending words are zero.",
        "confirmation_rule": "After each multisig submit, read transactionHash(index) from the live multisig and have a different signer confirmAndExecute(index, hash). Index and hash cannot be fixed before submission.",
    }


def capture():
    plan = offline_plan()
    live = json.loads(LIVE_FACTS.read_text())
    head = rpc("eth_getBlockByNumber", ["latest", False])
    tag = "latest"
    factory_code = rpc("eth_getCode", [FACTORY, tag])
    existing_code = rpc("eth_getCode", [plan["candidate_address"], tag])
    simulated = rpc_call(FACTORY, plan["factory_deployment_calldata"])["data"]
    delay = rpc("eth_getStorageAt", [TIMELOCK, "0x1", tag])
    implementation = rpc("eth_getStorageAt", [EXCHANGE, IMPLEMENTATION_SLOT, tag])
    plan["read_only_preflight"] = {
        "captured_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "live_facts": str(LIVE_FACTS.relative_to(ROOT)),
        "head": {key: head[key] for key in ("number", "hash", "timestamp")},
        "factory_code_sha256": hashlib.sha256(bytes.fromhex(factory_code[2:])).hexdigest(),
        "factory_code_bytes": (len(factory_code) - 2) // 2,
        "predicted_address_current_code_bytes": (len(existing_code) - 2) // 2,
        "simulated_factory_return": simulated,
        "live_implementation_word": implementation,
        "timelock_min_delay_seconds": int(delay, 16),
        "operation_timestamp_words": {
            row["name"]: rpc("eth_getStorageAt", [TIMELOCK, row["operation_storage_slot"], tag])
            for row in plan["operations"]
        },
        "pending_operation_word": rpc(
            "eth_getStorageAt",
            [TIMELOCK, plan["pending_governance_operation"]["operation_storage_slot"], tag]),
    }
    OUT.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    return verify()


def verify():
    saved = json.loads(OUT.read_text())
    live = json.loads(LIVE_FACTS.read_text())
    preflight = saved["read_only_preflight"]
    calculated = offline_plan()
    assert {key: saved[key] for key in calculated} == calculated
    assert saved["candidate_address"] == deploy.address()
    assert saved["restore_implementation"] == saved["live_implementation"] == LIVE_IMPLEMENTATION
    assert saved["live_implementation"] == live["exchange"]["implementation"]
    assert int(saved["pinned_implementation"], 16) != int(saved["live_implementation"], 16)
    assert int(preflight["head"]["number"], 16) >= int(live["head"]["number"], 16)
    assert preflight["live_facts"] == str(LIVE_FACTS.relative_to(ROOT))
    assert preflight["factory_code_sha256"] == FACTORY_CODE_SHA256
    assert preflight["factory_code_bytes"] == 69
    assert preflight["predicted_address_current_code_bytes"] == 0
    assert preflight["simulated_factory_return"].lower() == saved["candidate_address"]
    assert preflight["live_implementation_word"].lower() == "0x" + LIVE_IMPLEMENTATION[2:].rjust(64, "0")
    assert preflight["timelock_min_delay_seconds"] == 86_400
    assert set(preflight["operation_timestamp_words"]) == {row["name"] for row in saved["operations"]}
    assert all(int(value, 16) == 0 for value in preflight["operation_timestamp_words"].values()), \
        "every timelock operation slot must still be empty"
    assert len(preflight["operation_timestamp_words"]) == 8
    pending = saved["pending_governance_operation"]
    assert pending == pending_operation()
    assert pending["operation_storage_slot"] not in {
        row["operation_storage_slot"] for row in saved["operations"]}
    assert pending["predecessor"] != ZERO
    assert int(preflight["pending_operation_word"], 16) != 0, \
        "the in-flight SessionKeyManager operation must still occupy its timelock slot"
    return {
        "candidate_address": saved["candidate_address"],
        "compiled_code_sha256": saved["compiled_code_sha256"],
        "live_implementation": saved["live_implementation"],
        "operation_count": len(saved["operations"]),
        "operation_slots_empty": 8,
        "pending_governance_operation": saved["pending_governance_operation"]["operation_id"],
        "pending_governance_slot_occupied": int(preflight["pending_operation_word"], 16) != 0,
        "timelock_delay_seconds": preflight["timelock_min_delay_seconds"],
        "captured_at_utc": preflight["captured_at_utc"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true",
                        help="read live factory, timelock and proxy state")
    args = parser.parse_args()
    print(json.dumps(capture() if args.capture else verify(), indent=2))