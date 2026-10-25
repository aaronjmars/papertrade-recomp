#!/usr/bin/env python3
"""Pass-two audit of the two older Papertrade suites.

Targets the two suites that still hold user accounting and run pre-fix code:
`earlier_1` (Exchange proxy 0x1b534e482b92bb6daff452cd12f2e35219e13493, still on
its original implementation 0x557c853e100600e0ee91e0df88fcf4af0097ff89 and the
5,873-byte linked library 0xac8ba1307815f74bd13d4d039c96f7b97e81aa49) and
`earlier_2` (Exchange proxy 0x2ede04561914c61a5f49212609541934fd7f5901, now on
the contract-set-2 implementation 0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723).

Owned paths: artifacts/live2_older/**, atlas/block_48902346/live2_older.json and
atlas/block_48902346/live2_older.md.

Modes
-----
offline (default)   re-check every saved artifact and every ledger claim without
                    any network call, then rewrite the ledger and the readable
                    document.
--live              refresh the EVM and HyperCore reads first (raw responses are
                    saved under artifacts/live2_older/).
--fork URL          re-run the exact-runtime Forge fork suite against URL
                    (anvil or a public HyperEVM RPC) and refresh the parsed
                    results.

Nothing here is disclosed, submitted or executed. Live reads are observations at
one head block; fork results are simulations of exact runtime bytes.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "live2_older"
FORK = ART / "fork"
LEDGER = ROOT / "atlas" / "block_48902346" / "live2_older.json"
DOC = ROOT / "atlas" / "block_48902346" / "live2_older.md"

EVM_RPC = "https://rpc.hyperliquid.xyz/evm"
CORE_API = "https://api.hyperliquid.xyz/info"

E1 = "0x1b534e482b92bb6daff452cd12f2e35219e13493"
E2 = "0x2ede04561914c61a5f49212609541934fd7f5901"
E1_IMPL = "0x557c853e100600e0ee91e0df88fcf4af0097ff89"
E2_IMPL_AT_PIN = "0x93a8e8d647f6c1e7b0f9bf4bd86eff3a9f20c3fb"
SET2_IMPL = "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"
E1_LIB = "0xac8ba1307815f74bd13d4d039c96f7b97e81aa49"
E1_SESSION = "0x91667db7e20474b3ac6eaabf0c8106ed46b5691a"
E2_SESSION = "0xe45264507a67d0bbea35299002b68ebd76adba04"
E1_BATCH = "0x4041882573028cb177847c46f82e242024ebde66"
E1_PROXY_ADMIN = "0x140ac259be101d76691c512eb8105911f2f309f1"
E1_MULTISIG = "0x73a83d746c38865960583879bc29bb007a04eacf"
E2_MULTISIG = "0x324b0547039683c2df146421f3a76083ef130d27"
E1_TIMELOCK = "0x69b4b92f02ff415e0c966686e00d2783b395d690"
E2_TIMELOCK = "0xd98adcb9a409e33a658c24e872f37357a85ca484"
LP_CORE_ACCOUNT = "0xd75ffb585ff88d3aa50b7cf9230b27a7eb923c20"
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
PIN_BLOCK = 48_902_346
PIN_SHA = "d92ca32fdafb483c8e83f71c0abdfe4fcb89235b4191d78751f29371340530ab"

# Selectors used by the probes (reconstructed in the pinned catalog or here).
SEL = {
    # reconstructed signatures from atlas/block_48902346/selector_catalog.json; each
    # one is confirmed by the live read returning the value pass one recorded at the pin
    "totalBalances": "a69a2ad1",
    "treasury": "61d027b3",
    "totalLockedMargin": "01ad056f",
    "totalQueued": "53ac4b66",
    "nextPositionId": "899346c7",
    "owner": "8da5cb5b",
    "queueHead": "96523644",
    "lpBankrollAvailable": "0cdd5fc4",
    "reconcileSweepCredit": "6a3214c9",
    "clearPendingSweep": "2362f4de",
    "harvest": "ddc63262",
    "withdrawToCore": "7f99545a",
    # older multisig dispatch, checked live against both older multisigs
    "signerOne": "d98f851a",
    "signerTwo": "1a5f66c3",
    "requiredConfirmations": "82e717f7",
    "transactionCount": "b77bf600",
}
GOV_SEL = {
    "signerOne": SEL["signerOne"],
    "signerTwo": SEL["signerTwo"],
    "requiredConfirmations": SEL["requiredConfirmations"],
    "transactionCount": SEL["transactionCount"],
}

ANGLES = {
    "library-maths": "1 - older library payout and settlement maths",
    "queue-and-debt": "2 - older queue and debt-funded opens",
    "cash-out": "3 - cash-out route for older internal balances",
    "governance": "4 - older governance and signer control",
    "suite-diff": "5 - value-relevant differences from the newest suite",
}

SEVERITIES = {"high", "medium", "low", "info", "none"}
STATUSES = {
    "confirmed_live",
    "confirmed_simulation",
    "plausible_unproven",
    "disproved",
    "blocked",
}
AFFECTED = {"pinned", "set2", "both", "earlier_1", "earlier_2"}
TIERS = {
    "live_state_read",
    "bytecode_static_read",
    "exact_runtime_simulation",
    "saved_archive_replay",
    "public_api_read",
}

ROWS = [
    {
        "id": "OL-01",
        "title": "Earlier_1 library drops the two percent gain fee in a one-fee-wide band below the payout threshold",
        "angle": ANGLES["library-maths"],
        "invariant": "A3 (fee accounting) with a proposed A11 (a close payout must not depend on the LP bankroll in a way a user can select)",
        "actor": "any eligible trader (fee-avoidance side)",
        "precondition": "an open position on the first older Exchange's instrument, a realised gain P, and a live lpBankrollAvailable() in the half-open interval [P, P + 0.02P)",
        "trigger": "close the position while the LP bankroll sits in that one-fee-wide band: the settlement path then credits the whole gain and records no staker or developer fee",
        "impact": "within the band the winning-close fee (two percent of the gain) is neither credited to the staker or developer accumulators nor paid by the user, so it leaves the protocol's revenue entirely; the user's own claim is continuous, so it is a revenue leak rather than user profit",
        "affected": "earlier_1",
        "severity": "low",
        "status": "confirmed_simulation",
        "evidence_tier": "exact_runtime_simulation",
        "evidence": "Saved pass-one direct-library and fork cases in artifacts/deployer_scope/older_settlement_liquidity.t.sol and artifacts/deployer_scope/older_settlement_exchange.t.sol (available = P + F - 1 credits P with no fee; available = P + F credits P - F and records F split equally). Reproduced on a fork of live state in artifacts/live2_older/fork/out/plainclose.txt: with the observed bankroll 4737319422572812500106413 units the close credits 324532940672314897 and records staker 3311560619105254 and dev 3311560619105254, matching P = 331156061910525405, P - F and F/2 exactly.",
        "missing_observation": "a live close that landed inside the band; no historical close in the sampled 136 older closes did",
        "citations": [
            "atlas/block_48902346/older_settlement_liquidity.md",
            "artifacts/deployer_scope/older_settlement_liquidity_replay.json",
            "artifacts/live2_older/fork/out/plainclose.txt",
        ],
    },
    {
        "id": "OL-02",
        "title": "The fee-free band is not deliberately reachable at the live earlier_1 bankroll and caps",
        "angle": ANGLES["library-maths"],
        "invariant": "A3 (fee accounting)",
        "actor": "any eligible trader",
        "precondition": "a position inside the configured per-side exposure cap and a bankroll the user does not control",
        "trigger": "size a position so its realised gain P falls inside (bank/1.02, bank]; the fee is then skipped, but P must reach the same order as the LP bankroll",
        "impact": "no path: reaching the band needs P above 4,644,580 units against a live bankroll of 4,737,319.75 units, and a cap-legal position of 10,000,000 units of notional produces P of about 9,000 units per one percent of BBO move, so the band needs an approximately 46 percent instantaneous BBO move; the measured move used in the control is 0.037 percent",
        "affected": "earlier_1",
        "severity": "none",
        "status": "disproved",
        "evidence_tier": "live_state_read",
        "evidence": "Live reads in artifacts/live2_older/live_reads.json: lpBankrollAvailable(E1) = 4737319753728874410631818 internal units = 4,737,319.753728874410631818 USD, so the band needs P above 4,644,580 units. Fork control in artifacts/live2_older/fork/out/plainclose.txt: margin 25e18, leverage argument 75, BBO move 271715 -> 271615, gain P = 331156061910525405 units, about 9,000 units of gain per one percent of BBO move at a 10,000,000-unit notional. Per-side cap evidence reused from the newest-suite row PR-LP-06 (measured ETH headroom about 1.9e6 to 5.2e6 USD live, and a 10,000,000 USD notional position admitted as cap-legal in PR-LP-05).",
        "missing_observation": "a bankroll state low enough to make the band reachable by an ordinary move; the live bankroll is three orders of magnitude above any reachable gain",
        "citations": [
            "artifacts/live2_older/live_reads.json",
            "artifacts/live2_older/fork/out/plainclose.txt",
            "atlas/block_48902346/live2_findings.json",
        ],
    },
    {
        "id": "OL-03",
        "title": "The older debt close queues the whole margin plus profit with no LP bankroll gate and no fee",
        "angle": ANGLES["queue-and-debt"],
        "invariant": "A3 (liability reconciliation)",
        "actor": "any user holding queue credit (a legitimate state: any earlier close whose proceeds were queued creates it)",
        "precondition": "an open position carrying the useDebt flag and a close at any price; the LP bankroll may be zero",
        "trigger": "close the debt-flagged position: the linked library's queue path queues margin plus signed PnL in full instead of the settlement path's min(gain, bankroll), and records no fee",
        "impact": "the queue claim is created against a bankroll that was never checked, so one debt close can add a claim larger than the LP's available funds and create an unfunded queue entry; the winning-close fee is also skipped on every debt close, not only inside the boundary band, so a user who holds any queue credit can close any debt position fee-free and defer the entire payout into the queue",
        "affected": "earlier_1",
        "severity": "medium",
        "status": "confirmed_simulation",
        "evidence_tier": "exact_runtime_simulation",
        "evidence": "Exact-runtime fork cases. artifacts/live2_older/fork/out/debtclosebank.txt: with the treasury drained so the bankroll reads zero, the debt close still queues 25331156061910525405 units (margin 25e18 plus gain 331156061910525405) with staker fee delta 0, dev fee delta 0 and treasury delta 0, and both queue counters agree at that value. artifacts/live2_older/fork/out/debtcycle.txt: the same margin plus gain is queued and then harvested in full (paid 25331156061910525405, balance credit 25331156061910525405). The settlement-path control on the same fork (artifacts/live2_older/fork/out/plainclose.txt) credits only min(gain, bankroll) and records the two percent fee. Library-level confirmation in artifacts/deployer_scope/older_exchange_library_local.json (margin 500 plus PnL 100 queues 600 with no fee).",
        "missing_observation": "a historical debt close whose queue entry exceeded the contemporaneous bankroll; no historical useDebt=true open exists in the event-visible search (artifacts/deployer_scope/older_debt_history.json.gz)",
        "citations": [
            "artifacts/live2_older/fork/out/debtclosebank.txt",
            "artifacts/live2_older/fork/out/debtcycle.txt",
            "artifacts/deployer_scope/older_exchange_library_local.json",
            "atlas/block_48902346/older_exchange_library.md",
            "atlas/block_48902346/older_settlement_liquidity.md",
        ],
    },
    {
        "id": "OL-04",
        "title": "A debt-funded open consumes queue credit without raising totalLockedMargin or totalBalances, unlike a plain open",
        "angle": ANGLES["queue-and-debt"],
        "invariant": "A3 (liability reconciliation)",
        "actor": "any user holding queue credit",
        "precondition": "a user queue total at or above the 25e18 minimum margin",
        "trigger": "open a position with useDebt=true: the queue node amounts and both queue counters fall by exactly the margin, the position is created with that margin, and totalLockedMargin() and totalBalances() do not move",
        "impact": "the LP's locked-margin counter understates its obligations by the margin of every open debt position, so any accounting that subtracts locked margin (including the lpBankrollAvailable() getter, the payout gate on every winning close) reads a bankroll that ignores debt-funded margin; the debt open's own effect on the getter could not be isolated because the harness perturbs the getter's other inputs",
        "affected": "earlier_1",
        "severity": "low",
        "status": "confirmed_simulation",
        "evidence_tier": "exact_runtime_simulation",
        "evidence": "Exact-runtime A/B on a fork of live state, artifacts/live2_older/fork/out/cleandebt.txt: the debt open with margin 25e18 leaves totalLockedMargin() at 27815598618510431633825980 and totalBalances() at 84448601522052004894103251 (both unchanged from before the open, queued 25e18 -> 0); the plain-open control in the same state raises totalLockedMargin() by exactly 25000000000000000000. Queue consumption itself is exact (artifacts/live2_older/fork/out/twonode.txt).",
        "missing_observation": "the full lpBankrollAvailable() formula; the getter's inputs beyond treasury, locked margin and queue are not identified in the pinned behavioral evidence",
        "citations": [
            "artifacts/live2_older/fork/out/cleandebt.txt",
            "atlas/block_48902346/older_positions.md",
        ],
    },
    {
        "id": "OL-05",
        "title": "Multi-node queue credit is consumed exactly: a hand-built reversed list under-consumes, a library-built list does not",
        "angle": ANGLES["queue-and-debt"],
        "invariant": "A3 (queue liability reconciliation)",
        "actor": "any user holding more than one queue node",
        "precondition": "a user with two queue nodes created by the linked library itself",
        "trigger": "open with useDebt=true and a margin larger than the newest node but at or below the user queue total",
        "impact": "no path: the consumption walks the library's own linkage and debits exactly the margin across both nodes, leaving sum(node amounts) equal to the user queue total exactly; the anomaly seen in a control with hand-built reversed next pointers is a harness artifact, and reporting it would have been wrong",
        "affected": "earlier_1",
        "severity": "none",
        "status": "disproved",
        "evidence_tier": "exact_runtime_simulation",
        "evidence": "Exact-runtime cases on a fork of live state. artifacts/live2_older/fork/out/linkage.txt: the library builds node 8453 with next 8454 and node 8454 as the tail, so next points from the older node to the newer one. artifacts/live2_older/fork/out/twonode.txt: with amounts inflated to 25e18 and 10e18, a 25e18 debt open leaves userQueuedTotal and totalQueued both 10000000000000000000, the head node at 10000000000000000000, the tail at 0 and the user tail at the head, so 10e18 came from the tail and 15e18 from the head and sum(node amounts) equals the counter. Negative control, artifacts/live2_older/fork/out/negative_control_reversed_linkage.txt: a hand-built list whose pointer runs from the newer node to the older one consumes only the newest node (25e18 still in the head node, both user pointers cleared, counter 25e18), which is a state the library never creates and which shows the earlier lead was a harness artifact.",
        "missing_observation": "a live user with two or more simultaneous queue nodes; at the pin every one of the 132 event-derived users had head, tail and total at zero",
        "citations": [
            "artifacts/live2_older/fork/out/twonode.txt",
            "artifacts/live2_older/fork/out/linkage.txt",
            "atlas/block_48902346/older_queue_claims.md",
        ],
    },
    {
        "id": "OL-06",
        "title": "No queue credit can be double spent: counters, node amounts and harvest payments all reconcile",
        "angle": ANGLES["queue-and-debt"],
        "invariant": "A3 (queue liability reconciliation)",
        "actor": "any user holding queue credit",
        "precondition": "queue nodes and a LP bankroll",
        "trigger": "consume credit twice, harvest a node twice, or harvest more than was enqueued",
        "impact": "no path: consumption zeroes the node amount and debits both counters by the same amount, a second debt open with no credit left reverts 0x8e667356, and harvest pays the stored node amounts only and only from the available bankroll, so it cannot pay more than the queue holds",
        "affected": "earlier_1",
        "severity": "none",
        "status": "disproved",
        "evidence_tier": "exact_runtime_simulation",
        "evidence": "Consumption and counters: artifacts/live2_older/fork/out/twonode.txt (sum of node amounts equals the user queue total and totalQueued after the open). No-credit rejection: artifacts/deployer_scope/older_exchange_debt_open_local.json (testSecondOpenCannotReuseQueueCredit reverts 0x8e667356; testExactCreditSetsFlagAndConsumesQueue zeroes the node amount). Harvest: artifacts/live2_older/fork/out/harvestgate.txt shows a drained-treasury harvest reporting success and paying 0 while leaving the queue at 25331156061910525405, then a funded harvest paying exactly that amount, zeroing the queue and crediting the balance by the same amount; artifacts/live2_older/fork/out/debtcycle.txt is the funded case on a fresh cycle. The historical census in atlas/block_48902346/older_queue_claims.md shows 8,452 Enqueued and 8,516 Harvested events summing to 35,346.769143327597213040 internal units on both sides for every one of 132 users.",
        "missing_observation": "a historical harvest that paid more than its node amount; none in the complete event census",
        "citations": [
            "artifacts/live2_older/fork/out/twonode.txt",
            "artifacts/deployer_scope/older_exchange_debt_open_local.json",
            "atlas/block_48902346/older_queue_claims.md",
        ],
    },
    {
        "id": "OL-07",
        "title": "Earlier_1 users can still call the withdrawal path but the cash ceiling is the 0.156176 USDC left in the Exchange's HyperCore account",
        "angle": ANGLES["cash-out"],
        "invariant": "A6 (a Core withdrawal reaches the intended account) with a proposed A12 (internal balances must be redeemable in the asset the venue advertises)",
        "actor": "any earlier_1 user with a nonzero internal balance",
        "precondition": "an internal balance below the Exchange's HyperCore USDC balance",
        "trigger": "call withdrawToCore(amount): the internal balance is debited immediately and a CoreWriter spot send is queued, with no check of the Exchange's HyperCore balance",
        "impact": "the complete HyperCore ledger of the first older Exchange shows 803,211.096176 USDC in and 803,210.94 USDC out since creation (802,761.94 to four addresses, 449 to the LP destination 0xd75ffb58), leaving 0.156176 USDC against 84,448,601.52 units of internal balances, so a request above the residual cannot be delivered on Core while the EVM debit has already been taken; the users' book is unbacked and the last withdrawer takes the residual",
        "affected": "earlier_1",
        "severity": "high",
        "status": "confirmed_live",
        "evidence_tier": "live_state_read",
        "evidence": "Live reads in artifacts/live2_older/core_reads.json and artifacts/live2_older/live_reads.json: spotClearinghouseState(0x1b534e...) = 0.156176 USDC, clearinghouseState accountValue 0.0; the pass-one capture read the same 0.156176 USDC 22 hours after the pin (artifacts/deployer_scope/older_exchange_core.json.gz) and the live read agrees five days later. The complete Core ledger aggregate (98 inbound transfers, 27 outbound, one destination per withdrawal) is in core_reads.json. The EVM debit is reproduced in artifacts/live2_older/fork/out/userwithdraw.txt: with the exact runtime, withdrawToCore(1000e6) debits 1000e18, leaves the 117,183,028.0771 unit treasury unchanged, emits the CoreWithdrawal topic 0x95d1a939... and queues a 288-byte CoreWriter action. The owner-gated pending-word recovery (clearPendingSweep then reconcileSweepCredit) is tested in artifacts/deployer_scope/older_exchange_clear_replay.json.",
        "missing_observation": "a live withdrawal attempt after the Core account was drained; all 27 historical withdrawal events were delivered (artifacts/deployer_scope/older_withdrawal_logs.json.gz)",
        "citations": [
            "artifacts/live2_older/core_reads.json",
            "artifacts/deployer_scope/older_exchange_core.json.gz",
            "artifacts/live2_older/fork/out/userwithdraw.txt",
            "atlas/block_48902346/older_withdrawals.md",
        ],
    },
    {
        "id": "OL-08",
        "title": "Earlier_2 users are on the same unbacked book: 640,390,624.35 internal units against 0.003269 USDC on Core",
        "angle": ANGLES["cash-out"],
        "invariant": "A6 with a proposed A12",
        "actor": "any earlier_2 user with a nonzero internal balance",
        "precondition": "an internal balance below the Exchange's HyperCore USDC balance",
        "trigger": "call the withdrawal path on the second older Exchange, now running the contract-set-2 implementation",
        "impact": "the second older Exchange's HyperCore account holds 0.003269 USDC while its internal book is 640,390,624.35 units, so its users cannot be paid either; the Exchange's implementation was upgraded to set-2 code on 2026-10-21 but the upgrade did not fund the account",
        "affected": "earlier_2",
        "severity": "high",
        "status": "confirmed_live",
        "evidence_tier": "live_state_read",
        "evidence": "Live reads in artifacts/live2_older/core_reads.json: spotClearinghouseState(0x2ede0456...) = 0.003269 USDC; live_reads.json: totalBalances(E2) = 640390624345224166630287802 internal units; the Exchange's EIP-1967 implementation slot reads 0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723 (the set-2 implementation) against 0x93a8e8d647... at the pin. Its own complete Core ledger (23 entries) shows 10,400.103269 in and 10,399.10 out, ending with the same residual.",
        "missing_observation": "a Core top-up from the protocol to either older Exchange after the pin; none appears in either account's complete ledger",
        "citations": [
            "artifacts/live2_older/core_reads.json",
            "artifacts/live2_older/live_reads.json",
        ],
    },
    {
        "id": "OL-09",
        "title": "No older contract lets one user take another user's internal balance",
        "angle": ANGLES["cash-out"],
        "invariant": "A1 (a user balance moves only through an authorized user action or an explicitly privileged accounting path)",
        "actor": "unprivileged outsider",
        "precondition": "a victim with a nonzero balance; the caller controls only their own transaction",
        "trigger": "call every cross-user candidate on the first older Exchange proxy: reconcileSweepCredit(address,uint256), clearPendingSweep(address), withdrawToCore(uint256), harvest(uint256) and the two older-only selectors 0xb29af6b0 and 0xf92576b1",
        "impact": "no path: the reconciliation and clear paths revert 0x30cd7471 (NotOwner) for an outsider, withdrawToCore debits only the caller, harvest pays the node's stored owner rather than the caller, and the two older-only selectors revert 0x30cd7471 as well; only 0x6155be59 answers an unprivileged caller and it writes no balance, treasury or total word",
        "affected": "earlier_1",
        "severity": "none",
        "status": "disproved",
        "evidence_tier": "exact_runtime_simulation",
        "evidence": "Pinned-runtime selector probe in artifacts/live2_older/selector_probe.json (exact proxy and implementation bytes; outsider calls to 0x6a3214c9, 0x2362f4de, 0xb29af6b0 and 0xf92576b1 all revert with 0x30cd7471, the NotOwner error; 0x6155be59 answers an outsider and returns 32 bytes with zero balance, treasury and total deltas) and exact-runtime cases on a fork of live state in artifacts/live2_older/fork/out/outsider.txt (an outsider withdrawToCore reverts, the victim's 1000e18 balance is unchanged, the outsider's own balance stays zero). Owner controls: artifacts/deployer_scope/older_exchange_clear_replay.json (owner clear succeeds and reconcileSweepCredit credits 5e19 for a 50 USDC argument).",
        "missing_observation": "a live outsider call of the same selectors; the probes are local exact-runtime executions",
        "citations": [
            "artifacts/live2_older/selector_probe.json",
            "artifacts/live2_older/fork/out/outsider.txt",
            "artifacts/deployer_scope/older_exchange_clear_replay.json",
        ],
    },
    {
        "id": "OL-10",
        "title": "The one-signer signer-replacement path is still live on both older multisigs, and the value at risk today is the Core residual",
        "angle": ANGLES["governance"],
        "invariant": "A5 (upgrade and parameter authority follows the deployed governance controls)",
        "actor": "one compromised signer of either older 1-of-2 multisig",
        "precondition": "the compromise of signer 0x7ce50a614174a3b26b107f1f9866f88461820626, which still holds its seat in both older multisigs at the latest head with one required confirmation",
        "trigger": "submitTransaction(address(this), 0, updateSigners(newOne,newTwo), true) from that signer, then use the timelock's 60-second minimum delay to schedule and execute ProxyAdmin.upgrade on the Exchange proxy, or call Exchange.reconcileSweepCredit(attacker, amount) as the Exchange's owner before withdrawing",
        "impact": "a single key takes the whole control chain of either older suite (signers, then timelock, then ProxyAdmin and every contract owner) and can replace the Exchange implementation with arbitrary code or credit itself an arbitrary internal balance; the loss ceiling today is the Exchange's HyperCore USDC balance, 0.156176 USDC for earlier_1 and 0.003269 USDC for earlier_2, because the internal books are not backed; the ceiling becomes the full book if the protocol ever funds either older Exchange's Core account again",
        "affected": "both",
        "severity": "medium",
        "status": "confirmed_live",
        "evidence_tier": "live_state_read",
        "evidence": "Live reads in artifacts/live2_older/live_reads.json: signerOne() = 0x7ce50a61..., signerTwo() = 0x8cea98f6..., requiredConfirmations() = 1, transactionCount() = 240 (earlier_1) and 1303 (earlier_2, up from 1299 at the pin); Exchange owner() = the corresponding older timelock, and the timelock owns the ProxyAdmin. The signer replacement itself is the pass-one exact-runtime replay in artifacts/deployer_scope/older_multisig_control_replay.json (2 cases, direct updateSigners reverts, the self-call through submitTransaction succeeds and evicts both signers). Historical one-signer schedule and execute pairs through the 60-second timelock are in artifacts/deployer_scope/older_governance.json.gz.",
        "missing_observation": "a conservative loss figure for a funded older Exchange; the internal book is unbacked today, so an upgraded implementation gains control of contracts whose Core accounts are empty",
        "citations": [
            "artifacts/live2_older/live_reads.json",
            "artifacts/deployer_scope/older_multisig_control_replay.json",
            "atlas/block_48902346/older_multisig_control.md",
            "atlas/block_48902346/older_governance.md",
        ],
    },
    {
        "id": "OL-11",
        "title": "Earlier_1 lacks six newest-suite selectors, and none of the missing ones is an unprivileged-reachable value guard",
        "angle": ANGLES["suite-diff"],
        "invariant": "A5 (upgrade authority and selector scope)",
        "actor": "unprivileged user",
        "precondition": "the first older Exchange proxy, still on its original 22,954-byte implementation",
        "trigger": "compare the 96 dispatched selectors of the original implementation with the 98 of the newest one and drive each difference from an unprivileged caller",
        "impact": "the six selectors the newest suite added are three unresolved views (0x1b7c1009, 0x6d60ae8e, 0x82f47a3f(uint128,uint128)) and the owner-scoped developer-fee trio (0x86d506db changeDevFeeAddress, 0x88f2aea5 claimDevFees, 0xcbeb5f3d devFeeRecipient); the four selectors only the older implementation has are the owner-gated clearPendingSweep (0x2362f4de), two owner-gated selectors (0xb29af6b0, 0xf92576b1) and the unguarded 0x6155be59, which writes no balance, treasury or total word; so no security fix the newest suite added is unsupervised on the older one, and the older one keeps a recovery selector the newest lacks",
        "affected": "earlier_1",
        "severity": "info",
        "status": "confirmed_simulation",
        "evidence_tier": "bytecode_static_read",
        "evidence": "Selector sets and dispatch PCs in artifacts/deployer_scope/older_exchange_clear_replay.json (older 96 selectors, newest 98, older-only {0x2362f4de, 0x6155be59, 0xb29af6b0, 0xf92576b1}, newest-only {0x1b7c1009, 0x6d60ae8e, 0x82f47a3f, 0x86d506db, 0x88f2aea5, 0xcbeb5f3d}) and re-derived in artifacts/live2_older/selector_probe.json with the guard result for every difference (0x6a3214c9 and 0x2362f4de are shared or owner-gated on both sides; the newest-side outsider reconcile also reverts 0x30cd7471). Live implementation slot for the first older Exchange proxy = 0x557c853e100600e0ee91e0df88fcf4af0097ff89 (artifacts/live2_older/live_reads.json), so this is the deployed selector set today.",
        "missing_observation": "behaviour of 0x6155be59 beyond its no-write result and 32-byte return; its decompiled lead is a storage variable bounded by 1e18",
        "citations": [
            "artifacts/deployer_scope/older_exchange_clear_replay.json",
            "artifacts/live2_older/selector_probe.json",
            "artifacts/live2_older/live_reads.json",
        ],
    },
    {
        "id": "OL-12",
        "title": "Only earlier_1 still runs pre-fix code; earlier_2 now runs the set-2 implementation behind its own coupled SessionKeyManager",
        "angle": ANGLES["suite-diff"],
        "invariant": "A5 (upgrade authority and implementation coupling)",
        "actor": "user of either older suite",
        "precondition": "the post-pin governed upgrade batches of both older suites",
        "trigger": "read the implementation slots of both older Exchange proxies at the latest head",
        "impact": "the second older Exchange no longer lacks the newest fixes (its proxy points at the set-2 implementation), while its SessionKeyManager points at 0x0a2db5c7614b714fd9ec12b29bff3b4f4c545d82, which is neither the injected pinned manager nor the newest one, so that pair is upgrade-coupled in the way the newest-suite row AU-L2A-15 records; the first older Exchange still runs the pre-fix library and the older-only settlement and queue selectors, so it is the only older set where the pre-fix payout boundary can still be reached",
        "affected": "earlier_2",
        "severity": "info",
        "status": "confirmed_live",
        "evidence_tier": "live_state_read",
        "evidence": "Live EIP-1967 slots in artifacts/live2_older/live_reads.json: earlier_1 Exchange -> 0x557c853e100600e0ee91e0df88fcf4af0097ff89 (unchanged from the pin), earlier_2 Exchange -> 0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723 (the set-2 implementation, changed from 0x93a8e8d647... at the pin), earlier_2 SessionKeyManager -> 0x0a2db5c7614b714fd9ec12b29bff3b4f4c545d82. The two governed post-pin batches are recorded in atlas/block_48902346/suite_sets.md.",
        "missing_observation": "a log of who deployed the third SessionKeyManager implementation; implementation swaps leave no event",
        "citations": [
            "artifacts/live2_older/live_reads.json",
            "atlas/block_48902346/suite_sets.md",
        ],
    },
]


# --------------------------------------------------------------------------- #
# live reads
# --------------------------------------------------------------------------- #

def _rpc_batch(calls, url=EVM_RPC, chunk=20, retries=6):
    """Send [ (method, params), ... ] and return one response per call."""
    out = []
    for start in range(0, len(calls), chunk):
        part = calls[start:start + chunk]
        request = [
            {"jsonrpc": "2.0", "id": i, "method": m, "params": p}
            for i, (m, p) in enumerate(part)
        ]
        body = json.dumps(request).encode()
        for attempt in range(retries):
            req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=45) as response:
                    data = json.load(response)
            except Exception:  # transport error, retry with backoff
                import time

                time.sleep(2 * (attempt + 1))
                continue
            if isinstance(data, dict):
                data = [data]
            if any(isinstance(d, dict) and d.get("error", {}).get("code") == -32005 for d in data):
                import time

                time.sleep(3 * (attempt + 1))
                continue
            out.extend(data)
            break
        else:
            out.extend([{"error": {"message": "unavailable"}}] * len(part))
    return out


def _core(body):
    req = urllib.request.Request(CORE_API, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.load(response)


def capture_live():
    """Read live EVM state and HyperCore state; save every raw response."""
    ART.mkdir(parents=True, exist_ok=True)
    targets = {
        "E1": E1, "E2": E2, "E1_session": E1_SESSION, "E2_session": E2_SESSION,
        "E1_batch": E1_BATCH, "E1_proxy_admin": E1_PROXY_ADMIN,
        "E1_multisig": E1_MULTISIG, "E2_multisig": E2_MULTISIG,
        "E1_timelock": E1_TIMELOCK, "E2_timelock": E2_TIMELOCK,
    }
    calls, labels = [], []
    exchange_calls = {
        "totalBalances": SEL["totalBalances"],
        "treasury": SEL["treasury"],
        "totalLockedMargin": SEL["totalLockedMargin"],
        "totalQueued": SEL["totalQueued"],
        "nextPositionId": SEL["nextPositionId"],
        "owner": SEL["owner"],
        "queueHead": SEL["queueHead"],
        "lpBankrollAvailable": SEL["lpBankrollAvailable"],
    }
    for name, sel in exchange_calls.items():
        for key in ("E1", "E2"):
            calls.append(("eth_call", [{"to": targets[key], "data": "0x" + sel}, "latest"]))
            labels.append({"call": name, "target": key})
    for name, sel in GOV_SEL.items():
        for key in ("E1_multisig", "E2_multisig"):
            calls.append(("eth_call", [{"to": targets[key], "data": "0x" + sel}, "latest"]))
            labels.append({"call": name, "target": key})
    for key in targets:
        calls.append(("eth_getStorageAt", [targets[key], IMPL_SLOT, "latest"]))
        labels.append({"call": "implementation_slot", "target": key})
    for key in targets:
        calls.append(("eth_getStorageAt", [targets[key], "0x0", "latest"]))
        labels.append({"call": "slot0", "target": key})
    for key in targets:
        calls.append(("eth_getCode", [targets[key], "latest"]))
        labels.append({"call": "code", "target": key})
    calls.append(("eth_blockNumber", []))
    labels.append({"call": "head", "target": ""})
    responses = _rpc_batch(calls)
    entries = []
    for label, response in zip(labels, responses):
        entry = dict(label)
        code = response.get("result") if isinstance(response, dict) else None
        if label["call"] == "code" and isinstance(code, str):
            entry["code_sha256"] = hashlib.sha256(bytes.fromhex(code[2:])).hexdigest()
            entry["code_bytes"] = (len(code) - 2) // 2
            entry["raw"] = code
        else:
            entry["raw"] = code
        entry["error"] = response.get("error") if isinstance(response, dict) else {"message": "no response"}
        entries.append(entry)
    head = None
    for entry in entries:
        if entry["call"] == "head" and entry["raw"]:
            head = int(entry["raw"], 16)
    payload = {
        "endpoint": EVM_RPC,
        "observed_at_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head_block": head,
        "pin_block": PIN_BLOCK,
        "pin_block_hash": PIN_SHA,
        "targets": targets,
        "entries": entries,
        "notes": "eth_call is issued without a block tag because the public endpoint serves current state only; each entry keeps the raw response verbatim.",
    }
    (ART / "live_reads.json").write_text(json.dumps(payload, indent=1) + "\n")

    core = {
        "endpoint": CORE_API,
        "read_types": ["spotClearinghouseState", "clearinghouseState", "userNonFundingLedgerUpdates"],
        "accounts": {},
    }
    for key, address in (("E1", E1), ("E2", E2), ("LP_destination", LP_CORE_ACCOUNT)):
        core["accounts"][key] = {
            "address": address,
            "spot": _core({"type": "spotClearinghouseState", "user": address}),
            "perp": _core({"type": "clearinghouseState", "user": address}),
        }
    for key, address in (("E1", E1), ("E2", E2)):
        ledger = _core({"type": "userNonFundingLedgerUpdates", "user": address})
        inbound, outbound = {}, {}
        for item in ledger:
            delta = item.get("delta", {})
            if delta.get("token") != "USDC":
                continue
            amount = float(delta.get("usdcValue") or delta.get("amount") or 0)
            if str(delta.get("user", "")).lower() == address.lower():
                outbound[delta["destination"].lower()] = round(outbound.get(delta["destination"].lower(), 0.0) + amount, 8)
            else:
                inbound[str(delta["user"]).lower()] = round(inbound.get(str(delta["user"]).lower(), 0.0) + amount, 8)
        core["accounts"][key]["ledger"] = ledger
        core["accounts"][key]["ledger_summary"] = {
            "entries": len(ledger),
            "inbound_total_usdc": round(sum(inbound.values()), 8),
            "inbound_counterparties": len(inbound),
            "outbound_total_usdc": round(sum(outbound.values()), 8),
            "outbound_by_destination": dict(sorted(outbound.items(), key=lambda kv: -kv[1])),
            "inbound_by_source": dict(sorted(inbound.items(), key=lambda kv: -kv[1])),
        }
    (ART / "core_reads.json").write_text(json.dumps(core, indent=1) + "\n")
    return payload, core



# --------------------------------------------------------------------------- #
# selector probe (exact runtime, no chain)
# --------------------------------------------------------------------------- #

PINNED_CAPTURE = ROOT / "artifacts" / "deployer_scope" / "pinned_capture.json.gz"
BASELINE_RUNTIME = ROOT / "atlas" / "block_48902346" / "runtime"
NEWEST_PROXY = "0x6cd5661646289fb6e65ea5c032310fded797d0a2"
NEWEST_IMPL = "0x0f3febfc94876b0c895f7acecdc8f5c863b549ee"
PROBE_SOURCE = ART / "selector_probe.t.sol"

PROBE_TAGS = {
    "reconcile-pendingzero-outsider": "6a3214c9",
    "reconcile-pendingzero-owner": "6a3214c9-owner",
    "reconcile-pendingset-outsider": "6a3214c9-pendingset",
    "oldonly-b29af6b0-outsider": "b29af6b0",
    "oldonly-f92576b1-outsider": "f92576b1",
    "oldonly-6155be59-outsider": "6155be59",
    "oldonly-6155be59-owner": "6155be59-owner",
    "harvest-outsider-empty": "ddc63262",
    "clear-outsider": "2362f4de",
    "clear-owner-empty": "2362f4de-owner",
}


def _dispatch_selectors(code: bytes):
    """Selector -> dispatch PC, from the Solidity dispatcher prologue."""
    return {
        "0x" + found.group(1).hex(): int.from_bytes(found.group(2), "big")
        for found in re.finditer(b"\x63(.{4})\x14\x61(.{2})\x57", code, re.DOTALL)
    }


def capture_probe():
    """Run the pinned-runtime selector probe and save selector_probe.json."""
    solc = shutil.which("solc")
    if not solc:
        raise SystemExit("solc is required for the selector probe")
    scope = json.loads(gzip.decompress(PINNED_CAPTURE.read_bytes()))
    rows = {row["address"]: row for row in scope["rows"]}
    runtimes = {
        "older_proxy.hex": rows[E1]["runtime"],
        "older_implementation.hex": rows[E1_IMPL]["runtime"],
        "newest_proxy.hex": (BASELINE_RUNTIME / f"{NEWEST_PROXY}.hex").read_text().strip(),
        "newest_implementation.hex": (BASELINE_RUNTIME / f"{NEWEST_IMPL}.hex").read_text().strip(),
    }
    older_selectors = _dispatch_selectors(bytes.fromhex(runtimes["older_implementation.hex"][2:]))
    newest_selectors = _dispatch_selectors(bytes.fromhex(runtimes["newest_implementation.hex"][2:]))
    with tempfile.TemporaryDirectory(prefix="papertrade-live2-older-probe-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "runtime").mkdir()
        (project / "out").mkdir()
        (project / "test" / "SelectorProbe.t.sol").write_text(PROBE_SOURCE.read_text())
        for name, runtime in runtimes.items():
            (project / "runtime" / name).write_text(runtime.strip())
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc)
            + '\noffline = true\nfs_permissions = [{ access = "read-write", path = "./out" }, { access = "read", path = "./runtime" }]\n'
        )
        result = subprocess.run(
            ["forge", "test", "--root", tmp, "-vv"],
            capture_output=True, text=True, timeout=300, check=False,
        )
        output = result.stdout + "\n" + result.stderr
        (ART / "selector_probe_forge.txt").write_text(output)
        if result.returncode:
            raise SystemExit("selector probe failed:\n" + output[-4000:])
        parsed = {}
        for produced in (project / "out").glob("*.jsonl"):
            entries = {}
            for line in produced.read_text().splitlines():
                if not line.strip():
                    continue
                item = json.loads(line)
                key = PROBE_TAGS.get(item["tag"])
                if key is None:
                    continue
                entries[key] = {
                    "tag": item["tag"],
                    "ok": item["ok"],
                    "err": int(item["err"]),
                    "balance_delta": int(item["balance_delta"]),
                    "treasury_delta": int(item["treasury_delta"]),
                    "total_delta": int(item["total_delta"]),
                    "return_len": int(item["return_len"]),
                    "return_word": int(item["return_word"]),
                }
            parsed[produced.stem] = entries
    payload = {
        "pin": scope["pin"],
        "block_hash": scope["block_hash"],
        "exchange_proxy": E1,
        "older_implementation": E1_IMPL,
        "older_implementation_sha256": hashlib.sha256(bytes.fromhex(runtimes["older_implementation.hex"][2:])).hexdigest(),
        "newest_proxy": NEWEST_PROXY,
        "newest_implementation": NEWEST_IMPL,
        "newest_implementation_sha256": hashlib.sha256(bytes.fromhex(runtimes["newest_implementation.hex"][2:])).hexdigest(),
        "older_selector_count": len(older_selectors),
        "newer_selector_count": len(newest_selectors),
        "older_only_selectors": sorted(set(older_selectors) - set(newest_selectors)),
        "newer_only_selectors": sorted(set(newest_selectors) - set(older_selectors)),
        "older_dispatch": older_selectors,
        "newer_dispatch": newest_selectors,
        "outsider_calls": parsed.get("older", {}),
        "newest_calls": parsed.get("newest", {}),
        "test_source_sha256": hashlib.sha256(PROBE_SOURCE.read_bytes()).hexdigest(),
        "harness": "port-free Forge with the exact pinned proxy and implementation runtimes etched at their real addresses; owner, factory, pending word, one user balance, a treasury word and the packed total word are constructed local state; no HyperCore precompile is reached",
        "notes": "0x30cd7471 is the NotOwner error; 0x0984a617 is the empty-pending error",
    }
    (ART / "selector_probe.json").write_text(json.dumps(payload, indent=1) + "\n")
    return payload


# --------------------------------------------------------------------------- #
# fork suite
# --------------------------------------------------------------------------- #

FORK_TESTS = ["Ledger.t.sol", "OlderFork.t.sol"]


def capture_fork(url):
    """Run the exact-runtime Forge fork suite against `url` and save the results."""
    solc = shutil.which("solc")
    if not solc:
        raise SystemExit("solc is required for the fork suite")
    if not FORK.exists():
        raise SystemExit(f"missing fork sources under {FORK}")
    target = FORK / "out"
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.glob("*.txt"):
        stale.unlink()
    with tempfile.TemporaryDirectory(prefix="papertrade-live2-older-") as tmp:
        project = pathlib.Path(tmp)
        (project / "test").mkdir()
        (project / "out").mkdir()
        for name in FORK_TESTS:
            shutil.copy(FORK / name, project / "test" / name)
        (project / "foundry.toml").write_text(
            "[profile.default]\nsolc = " + json.dumps(solc)
            + '\nfs_permissions = [{ access = "read-write", path = "./out" }]\n'
        )
        result = subprocess.run(
            ["forge", "test", "--fork-url", url, "-vv"],
            cwd=project, capture_output=True, text=True, timeout=900, check=False,
        )
        output = result.stdout + "\n" + result.stderr
        (FORK / "forge_stdout.txt").write_text(output)
        if result.returncode:
            raise SystemExit("fork suite failed:\n" + output[-5000:])
        for produced in (project / "out").glob("*.txt"):
            shutil.copy(produced, target / produced.name)
    parse_fork_outputs()
    return json.loads((FORK / "results.json").read_text())


def parse_fork_outputs():
    """Turn the key=value notes of the fork suite into one JSON record."""
    outputs = {}
    for produced in sorted((FORK / "out").glob("*.txt")):
        values = {}
        for token in produced.read_text().split():
            if "=" in token:
                key, _, value = token.partition("=")
                values[key] = int(value)
        outputs[produced.stem] = values
    sources = {
        name: hashlib.sha256((FORK / name).read_bytes()).hexdigest() for name in FORK_TESTS
    }
    payload = {
        "fork_url": EVM_RPC,
        "test_sources": sources,
        "outputs": outputs,
        "notes": "Exact pinned runtime bytes for the first older Exchange proxy and implementation; the fork is the live chain state, HyperCore read precompiles are mocked and labelled as mocks, signatures are locally generated with a constructed session key.",
    }
    (FORK / "results.json").write_text(json.dumps(payload, indent=1) + "\n")
    return payload


# --------------------------------------------------------------------------- #
# verification
# --------------------------------------------------------------------------- #

def _live_entries():
    payload = json.loads((ART / "live_reads.json").read_text())
    by_key = {}
    for entry in payload["entries"]:
        by_key[(entry["call"], entry["target"])] = entry
    return payload, by_key


def _u256(entry):
    raw = entry["raw"]
    if not isinstance(raw, str) or not raw.startswith("0x") or len(raw) != 66:
        return None
    return int(raw, 16)


def verify():
    """Re-check every saved artifact and the values the ledger rows cite."""
    problems = []
    for path in (
        ART / "live_reads.json",
        ART / "core_reads.json",
        ART / "selector_probe.json",
        FORK / "results.json",
    ):
        if not path.exists():
            problems.append(f"missing artifact {path.relative_to(ROOT)}")
    if problems:
        raise SystemExit("; ".join(problems))

    live, entries = _live_entries()
    core = json.loads((ART / "core_reads.json").read_text())
    fork = json.loads((FORK / "results.json").read_text())
    probe = json.loads((ART / "selector_probe.json").read_text())

    def need(condition, message):
        if not condition:
            problems.append(message)

    need(live["head_block"] and live["head_block"] > PIN_BLOCK, "live head is not past the pin")
    need(live["pin_block"] == PIN_BLOCK, "pin block mismatch")

    # EVM facts the rows cite. The first older Exchange is frozen, but a live trade
    # could still move these, so the bounds follow the claim (a large unbacked book,
    # a frozen position counter, a live bankroll) rather than an exact replay value;
    # the exact observed numbers are in live_reads.json and in the row text.
    need(_u256(entries[("totalBalances", "E1")]) >= 84_400_000 * 10**18,
         "E1 totalBalances fell below the pinned book")
    need(_u256(entries[("totalBalances", "E2")]) >= 640_000_000 * 10**18,
         "E2 totalBalances fell below the pinned book")
    need(_u256(entries[("totalLockedMargin", "E1")]) >= 27_000_000 * 10**18,
         "E1 locked margin fell below the pinned value")
    need(_u256(entries[("treasury", "E1")]) >= 100_000_000 * 10**18,
         "E1 treasury fell below the pinned value")
    need(_u256(entries[("nextPositionId", "E1")]) >= 398945, "E1 nextPositionId went backwards")
    need(_u256(entries[("lpBankrollAvailable", "E1")]) > 0, "E1 bankroll is not positive")
    need(_u256(entries[("lpBankrollAvailable", "E1")]) < 10_000_000 * 10**18,
         "E1 bankroll grew past the bracket used in the reachability row")
    need(_u256(entries[("totalQueued", "E1")]) == 0, "E1 queue is not empty")
    need(_u256(entries[("queueHead", "E1")]) >= 8453, "E1 queue head went backwards")
    need(entries[("owner", "E1")]["raw"][-40:] == E1_TIMELOCK[2:], "E1 owner is not its timelock")
    need(entries[("owner", "E2")]["raw"][-40:] == E2_TIMELOCK[2:], "E2 owner is not its timelock")
    for key, expected in (
        ("E1", E1_IMPL),
        ("E2", "0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723"),
        ("E1_session", "0x56bfedb00f1ba3ecd4bd3fc1d5c597b6977328d3"),
        ("E2_session", "0x0a2db5c7614b714fd9ec12b29bff3b4f4c545d82"),
    ):
        need(
            entries[("implementation_slot", key)]["raw"][-40:] == expected[2:],
            f"{key} implementation slot mismatch",
        )
    for key, expected_signer in (
        ("E1_multisig", "0x7ce50a614174a3b26b107f1f9866f88461820626"),
        ("E2_multisig", "0x7ce50a614174a3b26b107f1f9866f88461820626"),
    ):
        need(entries[("signerOne", key)]["raw"][-40:] == expected_signer[2:], f"{key} signerOne mismatch")
        need(
            entries[("requiredConfirmations", key)]["raw"].endswith("1"),
            f"{key} confirmations changed",
        )
    need(
        _u256(entries[("transactionCount", "E2_multisig")]) >= 1299,
        "earlier_2 multisig transaction count fell below the pin value",
    )


    # HyperCore facts.
    def spot(key):
        balances = core["accounts"][key]["spot"]["balances"]
        for balance in balances:
            if balance["coin"] == "USDC":
                return float(balance["total"])
        return 0.0

    # the claim is that both older Exchange Core accounts are near-empty while their
    # internal books are tens of millions of units, so bound rather than pin them
    need(0.0 < spot("E1") < 1.0, "E1 Core USDC residual is no longer near-empty")
    need(0.0 < spot("E2") < 1.0, "E2 Core USDC residual is no longer near-empty")
    for key in ("E1", "E2"):
        summary = core["accounts"][key]["ledger_summary"]
        need(summary["inbound_total_usdc"] > 0 and summary["outbound_total_usdc"] > 0,
             f"{key} Core ledger is empty")
    summary_e1 = core["accounts"]["E1"]["ledger_summary"]
    need(abs(summary_e1["inbound_total_usdc"] - 803211.096176) < 1e-6,
         "E1 inbound ledger total changed")
    need(abs(summary_e1["outbound_total_usdc"] - 803210.94) < 1e-6,
         "E1 outbound ledger total changed")
    need(
        abs(summary_e1["inbound_total_usdc"] - summary_e1["outbound_total_usdc"] - 0.156176) < 1e-6,
        "E1 ledger no longer closes to its spot residual",
    )

    # Fork facts.
    out = fork["outputs"]
    debtcycle = out.get("debtcycle", {})
    need(debtcycle.get("debt_close_queued") == 25331156061910525405, "debt close queue changed")
    need(debtcycle.get("harvest_paid") == 25331156061910525405, "debt cycle harvest changed")
    need(debtcycle.get("harvest_balance_delta") == 25331156061910525405, "harvest credit changed")
    gate = out.get("harvestgate", {})
    need(gate.get("drained_harvest_paid") == 0, "drained harvest paid something")
    need(gate.get("drained_queued_after") == gate.get("queued_before_harvest"),
         "drained harvest consumed the queue")
    need(gate.get("funded_harvest_paid") == gate.get("queued_before_harvest"),
         "funded harvest did not pay the whole queue")
    need(gate.get("funded_queued_after") == 0, "funded harvest left a queue remainder")
    need(gate.get("funded_balance_delta") == gate.get("queued_before_harvest"),
         "funded harvest credit changed")
    need(debtcycle.get("open_userQueued") == 0 and debtcycle.get("open_global") == 0,
         "debt open no longer exhausts the queue")
    plain = out.get("plainclose", {})
    need(plain.get("plain_balance_delta") == 324532940672314897, "plain close credit changed")
    need(plain.get("bank") > 4_700_000 * 10**18, "plain close bankroll changed")
    need(plain.get("plain_queued") == 0, "plain close created a queue node")
    need(plain.get("plain_fee_staker") == 3311560619105254, "staker fee changed")
    need(plain.get("plain_fee_dev") == 3311560619105254, "developer fee changed")
    need(plain.get("plain_locked_delta") == 25000000000000000000, "plain open locked margin changed")
    bank = out.get("debtclosebank", {})
    need(bank.get("bank_at_close") == 0, "debt close bank gate case changed")
    need(bank.get("queued_delta") == 25331156061910525405,
         "debt close no longer queues the full margin plus gain with a zero bankroll")
    need(bank.get("global_queued") == bank.get("queued_delta"), "debt close queue counters disagree")
    need(bank.get("fee_staker_delta") == 0 and bank.get("fee_dev_delta") == 0,
         "debt close recorded a fee")
    need(bank.get("treasury_delta") == 0, "debt close moved the treasury")
    two = out.get("twonode", {})
    need(two.get("post_userQueued") == 10000000000000000000, "two-node remainder changed")
    need(two.get("sum_remaining") == two.get("post_userQueued"), "node amounts no longer reconcile")
    need(two.get("post_head_amount") == 10000000000000000000 and two.get("post_tail_amount") == 0,
         "two-node consumption shape changed")
    linkage = out.get("linkage", {})
    need(linkage.get("n2_userHead") == linkage.get("n1_node"), "queue head moved unexpectedly")
    need(linkage.get("n2_userTail") == linkage.get("n2_node"), "queue tail changed")
    need(linkage.get("n2_node1Word0_hi") == linkage.get("n2_node"), "node next pointer changed")
    negative = out.get("negative_control_reversed_linkage", {})
    need(negative.get("open_ok") == 1, "reversed-linkage control open failed")
    need(negative.get("post_userQueued") != 10000000000000000000,
         "reversed-linkage control no longer differs from the library-built case")
    clean = out.get("cleandebt", {})
    need(clean.get("locked_before") >= 27_000_000 * 10**18, "locked margin baseline fell")
    need(clean.get("locked_after") == clean.get("locked_before"), "debt open moved locked margin")
    need(clean.get("tb_before") >= 84_400_000 * 10**18, "total balances baseline fell")
    need(clean.get("tb_after") == clean.get("tb_before"), "debt open moved total balances")
    need(clean.get("queued_before") == 25000000000000000000 and clean.get("queued_after") == 0,
         "debt open queue consumption changed")
    need(clean.get("plain_locked_delta") == 25000000000000000000, "plain open control changed")
    outsider = out.get("outsider", {})
    need(outsider.get("outsider_ok") == 0, "outsider withdrawal no longer reverts")
    need(outsider.get("user_balance_after") == 1000000000000000000000,
         "outsider withdrawal moved the victim balance")
    need(outsider.get("outsider_balance_after") == 0, "outsider credited itself")
    withdraw = out.get("userwithdraw", {})
    need(withdraw.get("user_ok") == 1 and withdraw.get("user_balance_after") == 0,
         "withdrawal no longer debits the caller")
    need(withdraw.get("log_count") == 2 and withdraw.get("writer_action_len") == 288,
         "withdrawal CoreWriter action changed")
    need(withdraw.get("event_topic0") == 67765053407499933956756939398894238837967943672223161754477093898911894888053,
         "withdrawal event topic changed")
    need(withdraw.get("treasury_after") >= 100_000_000 * 10**18,
         "withdrawal changed the treasury")

    # Selector probe facts.
    for selector, tag in (
        ("6a3214c9", "reconcile-pendingzero-outsider"),
        ("2362f4de", "clear-outsider"),
        ("b29af6b0", "oldonly-b29af6b0-outsider"),
        ("f92576b1", "oldonly-f92576b1-outsider"),
    ):
        entry = probe["outsider_calls"].get(selector, {})
        need(entry.get("tag") == tag, f"probe tag for 0x{selector} changed")
        need(entry.get("ok") is False and entry.get("err") == 0x30CD7471,
             f"selector 0x{selector} is no longer owner-gated")
    need(probe["outsider_calls"]["6a3214c9-owner"]["ok"] is True, "owner reconcile no longer succeeds")
    need(probe["outsider_calls"]["6a3214c9-owner"]["balance_delta"] == 5_000_000_000_000_000_000_000,
         "owner reconcile credit changed")
    need(probe["outsider_calls"]["6155be59"]["ok"] is True, "0x6155be59 no longer unguarded")
    need(probe["outsider_calls"]["6155be59"]["balance_delta"] == 0, "0x6155be59 moved a balance")
    need(probe["outsider_calls"]["6155be59"]["return_len"] == 32, "0x6155be59 return changed")
    # the owner-case clear in this probe runs without a factory mock, so it reverts
    # with no data; the owner clear and empty-pending error are covered by
    # artifacts/deployer_scope/older_exchange_clear_replay.json
    need(probe["outsider_calls"]["2362f4de-owner"]["ok"] is False,
         "owner clear unexpectedly succeeded without a factory")
    need(probe["outsider_calls"]["ddc63262"]["ok"] is False, "empty-queue harvest no longer reverts")
    need(probe["newest_calls"]["6a3214c9"]["ok"] is False, "newest reconcile is no longer owner-gated")
    need(probe["older_selector_count"] == 96 and probe["newer_selector_count"] == 98,
         "selector counts changed")
    need(set(probe["older_only_selectors"]) == {"0x2362f4de", "0x6155be59", "0xb29af6b0", "0xf92576b1"},
         "older-only selector set changed")
    need(set(probe["newer_only_selectors"]) == {"0x1b7c1009", "0x6d60ae8e", "0x82f47a3f", "0x86d506db", "0x88f2aea5", "0xcbeb5f3d"},
         "newest-only selector set changed")

    # Ledger shape.
    for required in ("library-maths", "queue-and-debt", "cash-out", "governance", "suite-diff"):
        need(
            any(row["angle"] == ANGLES[required] for row in ROWS),
            f"no ledger row covers angle {required}",
        )
    seen = set()
    for row in ROWS:
        need(row["id"] not in seen, f"duplicate row id {row['id']}")
        seen.add(row["id"])
        for field in (
            "id", "title", "angle", "invariant", "actor", "precondition", "trigger",
            "impact", "affected", "severity", "status", "evidence_tier", "evidence",
            "missing_observation", "citations",
        ):
            need(field in row, f"{row['id']} is missing {field}")
        need(row["affected"] in AFFECTED, f"{row['id']} has affected {row['affected']}")
        need(row["severity"] in SEVERITIES, f"{row['id']} has severity {row['severity']}")
        need(row["status"] in STATUSES, f"{row['id']} has status {row['status']}")
        need(row["evidence_tier"] in TIERS, f"{row['id']} has tier {row['evidence_tier']}")
        need(row["citations"], f"{row['id']} has no citations")
        if row["status"] == "disproved":
            need(row["severity"] in ("none", "info"),
                 f"{row['id']} is disproved but rated {row['severity']}")
        for cited in row["citations"]:
            if cited.startswith("http"):
                continue
            need((ROOT / cited).exists(), f"{row['id']} cites missing {cited}")
        for cited in re.findall(r"artifacts/[\w./-]+", row["evidence"]):
            need((ROOT / cited.rstrip(".,")).exists(), f"{row['id']} evidence cites missing {cited}")

    if problems:
        raise SystemExit("verification failed:\n - " + "\n - ".join(problems))
    return {
        "rows": len(ROWS),
        "angles": sorted({row["angle"] for row in ROWS}),
        "by_status": {s: sum(1 for row in ROWS if row["status"] == s) for s in sorted(STATUSES)},
        "live_head": live["head_block"],
        "fork_tests": sorted(fork["outputs"]),
    }


# --------------------------------------------------------------------------- #
# outputs
# --------------------------------------------------------------------------- #

def write_outputs(summary):
    ledger = {
        "generated_by": "audit_live2_older.py",
        "target": "the two older Papertrade suites (earlier_1, earlier_2)",
        "pin": PIN_BLOCK,
        "pin_block": PIN_BLOCK,
        "live_head_block": summary["live_head"],
        "counts": {
            "rows": summary["rows"],
            "by_status": summary["by_status"],
            "by_severity": {
                s: sum(1 for row in ROWS if row["severity"] == s)
                for s in sorted(SEVERITIES)
            },
            "by_affected": {
                a: sum(1 for row in ROWS if row["affected"] == a) for a in sorted(AFFECTED)
            },
        },
        "rows": ROWS,
        "artifacts": {
            "live_reads": "artifacts/live2_older/live_reads.json",
            "core_reads": "artifacts/live2_older/core_reads.json",
            "selector_probe": "artifacts/live2_older/selector_probe.json",
            "fork_results": "artifacts/live2_older/fork/results.json",
            "fork_sources": ["artifacts/live2_older/fork/Ledger.t.sol", "artifacts/live2_older/fork/OlderFork.t.sol"],
        },
        "limits": [
            "Live reads are one head-block observation each; the public endpoint ignores a block parameter and serves current state only.",
            "Fork results are exact-runtime executions on a fork of live state with mocked HyperCore read precompiles; they are simulations.",
            "No archive RPC is available, so all historical claims come from the saved pass-one captures.",
        ],
        "verify": summary,
    }
    LEDGER.write_text(json.dumps(ledger, indent=1) + "\n")

    head = summary["live_head"]
    lines = [
        "# Pass two of the two older Papertrade suites",
        "",
        f"Generated by [`audit_live2_older.py`](../../scripts/audit_live2_older.py), offline. Machine ledger: [live2_older.json](live2_older.json); raw captures under `artifacts/live2_older/`. Live reads are one head-block observation (block {head:,} on HyperEVM and the same moment on the HyperCore API) and fork rows are exact-runtime simulations on a fork of live state with mocked HyperCore reads.",
        "",
        "Scope: the two suites that still hold user accounting. `earlier_1` (Exchange `0x1b534e48...`) is still on its original 22,954-byte implementation and the pre-fix 5,873-byte library; `earlier_2` (Exchange `0x2ede0456...`) was upgraded to the contract-set-2 implementation post-pin. Both were reconciled at block 48,902,346 in pass one.",
        "",
        "## Counts",
        "",
        "| Severity | Rows |",
        "|---|---:|",
    ]
    for severity in ("high", "medium", "low", "info", "none"):
        lines.append(f"| {severity} | {sum(1 for r in ROWS if r['severity'] == severity)} |")
    lines += ["", "| Status | Rows |", "|---|---:|"]
    for status in ("confirmed_live", "confirmed_simulation", "plausible_unproven", "disproved", "blocked"):
        lines.append(f"| {status} | {sum(1 for r in ROWS if r['status'] == status)} |")
    lines += ["", "| Applies to | Rows |", "|---|---:|"]
    for affected in ("earlier_1", "earlier_2", "both"):
        lines.append(f"| {affected} | {sum(1 for r in ROWS if r['affected'] == affected)} |")
    lines += [
        "",
        "## Findings",
        "",
        "| ID | Angle | Sev | Status | Applies to | Finding |",
        "|---|---|---|---|---|---|",
    ]
    for row in ROWS:
        lines.append(
            f"| `{row['id']}` | {row['angle'].split(' - ')[0]} | {row['severity']} | {row['status']} | "
            f"{row['affected']} | {row['title']} |"
        )
    lines += ["", "## Detail", ""]
    for row in ROWS:
        lines += [
            f"### {row['id']} {row['title']}",
            "",
            f"- Angle {row['angle']}; invariant {row['invariant']}; actor: {row['actor']}",
            f"- Affected: {row['affected']}; severity: {row['severity']}; status: {row['status']}; tier: {row['evidence_tier']}",
            f"- Precondition: {row['precondition']}",
            f"- Trigger: {row['trigger']}",
            f"- Impact: {row['impact']}",
            f"- Evidence: {row['evidence']}",
            f"- Missing observation: {row['missing_observation']}",
            f"- Citations: {', '.join('`' + c + '`' for c in row['citations'])}",
            "",
        ]
    lines += [
        "## The two questions",
        "",
        "- Can an unprivileged user take more than they put in on an older suite? No bounded theft path was found. The cross-user paths are owner-gated or caller-scoped (OL-09), queue credit is consumed exactly and cannot be double spent or over-harvested (OL-05, OL-06), and the fee-free payout band is not reachable at the live bankroll (OL-02). What is real is unbacked: the two older Exchanges hold 0.156176 and 0.003269 USDC on Core against internal books of 84,448,601.52 and 640,390,624.35 units, so the users' money is an accounting claim rather than cash (OL-07, OL-08), and a debt-flagged close can add a queue claim larger than the LP bankroll with no fee (OL-03).",
        "- What can a single signer do? Both older multisigs are still 1-of-2 with the same two signers, so one compromised key replaces both signers immediately, then owns the 60-second timelock and through it the ProxyAdmin and every contract owner, which is enough to install arbitrary Exchange code or credit itself any internal balance (OL-10). The value at risk today is the Core residual of the suite (about 0.16 USDC on earlier_1); the internal book cannot be drained because it is not backed.",
        "",
    ]
    DOC.write_text("\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--probe", action="store_true", help="re-run the pinned-runtime selector probe")
    parser.add_argument("--live", action="store_true", help="refresh EVM and HyperCore reads")
    parser.add_argument("--fork", metavar="RPC_URL", help="re-run the exact-runtime fork suite against RPC_URL")
    args = parser.parse_args(argv)
    if args.probe:
        capture_probe()
    if args.live:
        capture_live()
    if args.fork:
        capture_fork(args.fork)
    summary = verify()
    write_outputs(summary)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())