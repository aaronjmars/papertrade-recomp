#!/usr/bin/env python3
"""Pin independent source evidence for HyperCore's 0x0810 account-existence read."""

import argparse
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
SOURCE = ROOT / "artifacts" / "external" / "circle_CoreDepositWallet_ffcc9788.sol"
OUTPUT = ATLAS / "hypercore_user_exists_evidence.json"
COMMIT = "ffcc978810fa88884c150ad2d6418aa02c576670"
URL = f"https://raw.githubusercontent.com/circlefin/hyperevm-circle-contracts/{COMMIT}/src/CoreDepositWallet.sol"
SHA256 = "3d8689ea027fd959d0865a1d9744bbfb5733008b6f6fc6afe4ff5173436f089d"
PRECOMPILE = "0x0000000000000000000000000000000000000810"


def capture():
    data = urllib.request.urlopen(URL, timeout=30).read()
    assert hashlib.sha256(data).hexdigest() == SHA256
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    SOURCE.write_bytes(data)


def verify():
    data = SOURCE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SHA256
    source = data.decode()
    assert f"CORE_USER_EXISTS_PRECOMPILE_ADDRESS = {PRECOMPILE}" in source
    assert "DEFAULT_NEW_CORE_ACCOUNT_FEE = 100000000" in source
    assert "CORE_SCALING_FACTOR = 100" in source
    assert "function _coreUserExists(address user) internal view returns (bool)" in source
    assert "CORE_USER_EXISTS_PRECOMPILE_ADDRESS.staticcall(abi.encode(user))" in source
    assert "return abi.decode(result, (CoreUserExists)).exists;" in source
    census = json.loads((ATLAS / "exchange_withdrawal_event_census.json").read_text())
    assert census["sample_selector_status_counts"] == [
        {"selector": "0x8d09f23f", "hypercore_user_status": 0, "count": 16},
        {"selector": "0x8d09f23f", "hypercore_user_status": 1, "count": 16}]
    assert census["gap_counts_18_decimals"] == {"0": 22652, str(10**18): 5991}
    direct = json.loads((ATLAS / "exchange_direct_withdrawal_behavior.json").read_text())
    assert [row["core_user_status_word"] for row in direct["historical_direct_calls"]] == [0, 1]
    assert [int(row["extra_debit"]) for row in direct["historical_direct_calls"]] == [10**18, 0]
    result = {
        "pin": census["pin"], "block_hash": census["block_hash"],
        "precompile": PRECOMPILE, "external_name": "coreUserExists(address)",
        "return_semantics": {"0": "user does not exist on HyperCore", "1": "user exists on HyperCore"},
        "external_protocol_source": {
            "project": "Circle HyperEVM contracts", "commit": COMMIT,
            "url": f"https://github.com/circlefin/hyperevm-circle-contracts/blob/{COMMIT}/src/CoreDepositWallet.sol",
            "sha256": SHA256, "new_account_fee_core_8_decimals": 100000000,
            "core_to_evm_scale": 100,
        },
        "papertrade_evidence": {
            "stratified_signed_call_status_zero": 16,
            "stratified_signed_call_status_one": 16,
            "historical_direct_call_status_zero": 1,
            "historical_direct_call_status_one": 1,
            "status_zero_internal_extra_debit_18_decimals": str(10**18),
            "status_one_internal_extra_debit_18_decimals": "0",
        },
        "limit": "Circle source specifies the HyperCore precompile and a separate integration's new-account fee; it is not Papertrade source and does not prove downstream CoreWriter settlement or fee disposition. Papertrade debit correlation is established by saved traces and local runtime tests."
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print("HyperCore 0x0810 identified as coreUserExists; 34 Papertrade historical status samples agree")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    if args.capture:
        capture()
    verify()
