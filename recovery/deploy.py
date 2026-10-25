"""CREATE2 derivation for the PT-01 recovery candidate.

The salt is a fixed label, so the deployment address is a pure function of the
compiled init code. `plan.py` re-checks the derived address against the deployed
deterministic factory with a read-only call; nothing here deploys anything.
"""

import json
import pathlib

from atlas_factory_events import Keccak

HERE = pathlib.Path(__file__).resolve().parent
COMPILED = HERE / "compiled.json"
FACTORY = "0x4e59b44847b379578588920ca78fbf26c0b4956c"
SALT_LABEL = b"papertrade-pt01-recovery-candidate-v2-2026-10-22"


def salt():
    return "0x" + Keccak()(SALT_LABEL).hex()


def predicted_address(init_code):
    init = bytes.fromhex(init_code[2:])
    digest = Keccak()(b"\xff" + bytes.fromhex(FACTORY[2:]) + bytes.fromhex(salt()[2:]) + Keccak()(init))
    return "0x" + digest[12:].hex()


def deployment_calldata(init_code):
    return "0x" + salt()[2:] + init_code[2:]


def compiled():
    return json.loads(COMPILED.read_text())


def address():
    return predicted_address(compiled()["init_code"])