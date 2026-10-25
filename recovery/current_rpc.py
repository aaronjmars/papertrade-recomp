"""Read-only helpers for the public current-state HyperEVM and HyperCore endpoints.

The public HyperEVM JSON-RPC serves current state only: it ignores historical block
tags and rejects `debug_*`. Every read here is therefore an unauthenticated
`latest` read of live state, used only behind an explicit `--capture` flag.
"""

import json
import os
import time
import urllib.error
import urllib.request

RPC_URL = os.environ.get("PAPERTRADE_RPC_URL", "https://rpc.hyperliquid.xyz/evm")
CORE_INFO = "https://api.hyperliquid.xyz/info"
ATTEMPTS = 6


def post(url, payload, timeout=45, allow_revert=False):
    """One JSON-RPC reply. With `allow_revert`, an execution-revert error is returned
    as an error object instead of raising, which is how the node reports `eth_call` reverts."""
    body = json.dumps(payload).encode()
    for attempt in range(ATTEMPTS):
        request = urllib.request.Request(url, body, {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                reply = json.load(response)
        except (urllib.error.URLError, OSError, json.JSONDecodeError):
            if attempt == ATTEMPTS - 1:
                raise
            time.sleep(1 + attempt)
            continue
        if "error" not in reply:
            return reply
        error = reply["error"]
        if error.get("code") == -32005:  # rate limited
            time.sleep(1 + attempt)
            continue
        if allow_revert and error.get("code") == 3:
            return reply
        raise RuntimeError(f"rpc error {error.get('code')}: {error.get('message')}")
    raise RuntimeError("rpc rate limited")


def rpc(method, params):
    """One JSON-RPC result. Raises on any JSON-RPC error other than rate limiting."""
    reply = post(RPC_URL, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    return reply["result"]


def rpc_call(to, data, block="latest", state_override=None, sender=None):
    """An `eth_call` result, or a structured revert record instead of raising."""
    call = {"to": to, "data": data}
    if sender is not None:
        call["from"] = sender
    params = [call, block]
    if state_override is not None:
        params.append(state_override)
    reply = post(RPC_URL, {"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": params},
                 allow_revert=True)
    if "error" in reply:
        error = reply["error"]
        return {"status": "error", "code": error.get("code"),
                "message": error.get("message"), "data": error.get("data")}
    return {"status": "success", "data": reply["result"]}


def core(payload):
    return post(CORE_INFO, payload)


def word(value):
    """A 32-byte word hex string for an int, an address or a 0x-hex string."""
    if isinstance(value, str):
        value = int(value, 16)
    return "0x" + f"{value:064x}"


def slot_of(key, index):
    """`mapping(key => value)` at slot `index` for a 32-byte key."""
    from atlas_factory_events import Keccak

    if isinstance(key, str):
        key = int(key, 16)
    return "0x" + Keccak()(key.to_bytes(32, "big") + index.to_bytes(32, "big")).hex()