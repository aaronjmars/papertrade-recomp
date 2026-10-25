#!/usr/bin/env python3
"""Consolidate the four live-code audit ledgers into one findings index.

The audit workstreams write one ledger each under atlas/block_48902346/. This
script merges them, checks the row schema and the citations, and emits the
combined machine ledger plus a readable index. It reads saved evidence only and
needs no RPC credential. Missing workstreams are reported, not invented, so it
can run before every workstream has landed.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
OUT = ATLAS / "live2_findings.json"
MARKDOWN_OUT = ATLAS / "live2_audit.md"

WORKSTREAMS = {
    # name: (ledger file, required for the gate, id prefix)
    "pricing": ("live2_pricing.json", True, "PR"),
    "payout": ("live2_payout.json", True, "PA"),
    "authority": ("live2_authority.json", True, "AU"),
    "intents": ("live2_intents.json", True, "IN"),
    "sequences": ("live2_sequences.json", False, "SQ"),
    "roles": ("live2_roles.json", False, "RL"),
    "older": ("live2_older.json", False, "OL"),
    "proxies": ("live2_proxies.json", False, "PX"),
}

REQUIRED = ("id", "title", "angle", "invariant", "actor", "precondition", "trigger",
            "impact", "affected", "severity", "status", "evidence_tier", "evidence",
            "missing_observation", "citations")

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3, "none": 4}
STATUS_ORDER = ("confirmed_live", "confirmed_simulation", "plausible_unproven",
                "disproved", "blocked")
PATH_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:json|md|gz|hex|py|tsol|sol|inc|t\.sol)")
URL_RE = re.compile(r"https?://[^\s\"',)]+")


ROW_KEYS = ("rows", "ledger", "findings", "results")


def read_json(path):
    return json.loads(path.read_text())


def rows_of(ledger):
    if isinstance(ledger, dict):
        for key in ROW_KEYS:
            rows = ledger.get(key)
            if isinstance(rows, list) and rows:
                return rows
        raise AssertionError(f"ledger has none of {ROW_KEYS}: keys={sorted(ledger)}")
    assert isinstance(ledger, list) and ledger, "ledger has no rows"
    return ledger


def cited_paths(row):
    """Every file-looking token in the row, as repo-relative paths."""
    found = []
    blob = json.dumps(row.get("evidence", "")) + " " + json.dumps(row.get("citations", ""))
    for token in PATH_RE.findall(blob):
        token = token.lstrip("./")
        if token.startswith("atlas/") or token.startswith("artifacts/") or token.startswith("recovery/"):
            found.append(token)
        elif "/" in token:
            found.append(token)
    return sorted(set(found))


def verify(require_all=True):
    """Merge the workstream ledgers, check their shape and citations, write the outputs."""
    missing = [name for name, (filename, required, prefix) in WORKSTREAMS.items()
               if not (ATLAS / filename).exists()]
    required_missing = [name for name, (filename, required, prefix) in WORKSTREAMS.items()
                        if required and not (ATLAS / filename).exists()]
    if require_all and required_missing:
        raise SystemExit("missing required workstream ledgers: " + ", ".join(required_missing))

    rows = []
    sources = {}
    for name, (filename, _required, prefix) in WORKSTREAMS.items():
        path = ATLAS / filename
        if not path.exists():
            continue
        ledger = read_json(path)
        workstream_rows = rows_of(ledger)
        sources[name] = {
            "ledger": str(path.relative_to(ROOT)),
            "rows": len(workstream_rows),
            "pin": ledger.get("pin") if isinstance(ledger, dict) else None,
        }
        for row in workstream_rows:
            missing_fields = [field for field in REQUIRED if field not in row]
            assert not missing_fields, (filename, row.get("id"), missing_fields)
            assert row["severity"] in SEVERITY_ORDER, row["severity"]
            assert row["status"] in STATUS_ORDER, row["status"]
            assert row["affected"] in ("pinned", "set2", "both", "earlier_1", "earlier_2"), row["affected"]
            merged = dict(row)
            merged["workstream"] = name
            merged["id"] = row["id"] if row["id"].startswith(prefix + "-") else f"{prefix}-{row['id']}"
            merged["source_id"] = row["id"]
            merged["cited_paths"] = cited_paths(row)
            merged["cited_paths_resolved"] = [p for p in merged["cited_paths"] if (ROOT / p).exists()]
            merged["cited_urls"] = sorted(set(URL_RE.findall(json.dumps(row.get("citations", ""))
                                                           + json.dumps(row.get("evidence", "")))))
            merged["citation_ok"] = bool(merged["cited_paths_resolved"] or merged["cited_urls"])
            # Severity must match the row's own claim. A negative that reads as "no impact", or a
            # row the audit itself disproved, cannot be reported above informational.
            impact_text = str(row.get("impact", "")).strip().lower()
            negative = row["status"] == "disproved" or impact_text.startswith("no impact") or impact_text.startswith("none:")
            if negative:
                assert row["severity"] in ("none", "info"), (
                    f"{filename} {row['id']} claims no impact or is disproved but is rated {row['severity']}")
            assert not (row["severity"] == "high" and row["status"] == "disproved"), row["id"]
            rows.append(merged)

    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)), "duplicate ids after prefixing"
    unresolved_rows = [row["id"] for row in rows if not row["citation_ok"]]
    assert not unresolved_rows, ("row with no resolvable citation", unresolved_rows)

    rows.sort(key=lambda row: (SEVERITY_ORDER[row["severity"]], row["id"]))

    counts = {
        "rows": len(rows),
        "by_severity": {sev: sum(row["severity"] == sev for row in rows) for sev in SEVERITY_ORDER},
        "by_status": {status: sum(row["status"] == status for row in rows) for status in STATUS_ORDER},
        "by_affected": {scope: sum(row["affected"] == scope for row in rows)
                        for scope in ("pinned", "set2", "both", "earlier_1", "earlier_2")},
        "by_workstream": {name: sum(row["workstream"] == name for row in rows) for name in sources},
    }
    # A live-code audit has to show its negatives; a ledger with none is suspect.
    assert counts["by_status"]["disproved"] >= 1, "no disproved row: negatives are missing"
    assert counts["by_status"]["confirmed_simulation"] >= 1, "no simulated confirmation in the ledger"

    proposed_invariants = sorted({row["invariant"].split()[0].rstrip(":") for row in rows
                                  if row["invariant"] and row["invariant"] not in ("", "none")})
    result = {
        "generated_by": "audit_live2_consolidate.py",
        "scope": "Live-code audit of the Papertrade contract set 2 and its pinned counterparts, "
                 "eight workstreams, staged findings only. No disclosure, no transaction, no deploy.",
        "workstreams_present": sorted(sources),
        "workstreams_missing": sorted(missing),
        "sources": sources,
        "counts": counts,
        "invariants_referenced": proposed_invariants,
        "blocked": [{"id": row["id"], "title": row["title"],
                     "missing_observation": row["missing_observation"]}
                    for row in rows if row["status"] == "blocked"],
        "open_observations": sorted({row["missing_observation"] for row in rows
                                     if row["status"] in ("plausible_unproven", "blocked")
                                     and row["missing_observation"]}),
        "rows": rows,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    lines = ["# Live-code audit of contract set 2", "",
             f"Consolidated from {len(sources)} workstreams: " + ", ".join(sorted(sources)) + ". "
             "Generated by `audit_live2_consolidate.py` from the per-workstream ledgers. "
             "Rows are staged findings only: nothing here was disclosed, submitted or executed.", ""]
    if missing:
        lines += [f"Workstreams not yet landed: {', '.join(sorted(missing))}.", ""]
    lines += ["## Counts", "",
              "| Severity | Rows |", "|---|---:|"]
    lines += [f"| {sev} | {count} |" for sev, count in counts["by_severity"].items() if count]
    lines += ["", "| Status | Rows |", "|---|---:|"]
    lines += [f"| {status} | {count} |" for status, count in counts["by_status"].items() if count]
    lines += ["", "| Applies to | Rows |", "|---|---:|"]
    lines += [f"| {scope} | {count} |" for scope, count in counts["by_affected"].items() if count]
    lines += ["", "## Findings", "",
              "| ID | Workstream | Sev | Status | Applies to | Invariant | Finding |",
              "|---|---|---|---|---|---|---|"]
    for row in rows:
        title = row["title"].replace("|", "/")
        lines.append(f"| `{row['id']}` | {row['workstream']} | {row['severity']} | {row['status']} | "
                     f"{row['affected']} | {row['invariant']} | {title} |")
    lines += ["", "## Open observations", ""]
    if result["open_observations"]:
        lines += [f"- {item}" for item in result["open_observations"]]
    else:
        lines += ["None: every row is either confirmed or disproved."]
    lines += ["", "## Reproduction", "",
              "Each workstream ledger has its own offline verifier at the repo root: "
              "`audit_live2_pricing.py`, `audit_live2_payout.py`, `audit_live2_authority.py`, "
              "`audit_live2_intents.py`. Then run `python3 scripts/audit_live2_consolidate.py --require-all`.", ""]
    MARKDOWN_OUT.write_text("\n".join(lines))
    result["markdown"] = str(MARKDOWN_OUT.relative_to(ROOT))
    return result


def main():
    result = verify(require_all="--require-all" in sys.argv)
    print(json.dumps({"workstreams": result["workstreams_present"],
                      "missing": result["workstreams_missing"], **result["counts"]}, indent=1))


if __name__ == "__main__":
    main()