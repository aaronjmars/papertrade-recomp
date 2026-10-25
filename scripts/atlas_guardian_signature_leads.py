#!/usr/bin/env python3
"""Hash names in Guardian's public Papertrade report against pinned selectors."""

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from atlas_factory_events import Keccak


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas" / "block_48902346"
REPORT = ROOT / "artifacts" / "guardian_papertrade_report.html"
OUT = ATLAS / "guardian_signature_leads.json"
URL = "https://guardian.security/portfolio/papertrade/protocol-review-2026-10-09/"
IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
CALLED = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.code = 0
        self.all_parts = []
        self.code_parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "code":
            self.code += 1

    def handle_endtag(self, tag):
        if tag == "code":
            self.code -= 1
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.all_parts.append(data)
            if self.code:
                self.code_parts.append(data)


def build():
    raw = REPORT.read_bytes()
    text = VisibleText()
    text.feed(raw.decode())
    visible = " ".join(text.all_parts)
    code = " ".join(text.code_parts)
    names = {word for word in IDENTIFIER.findall(code) if len(word) > 2}
    names.update(CALLED.findall(visible))
    names.update(word for word in IDENTIFIER.findall(visible)
                 if len(word) > 3 and any(letter.isupper() for letter in word[1:]))
    catalog = json.loads((ATLAS / "selector_catalog.json").read_text())
    keccak = Keccak()
    matches = []
    for address, contract in catalog.items():
        role = contract["role"]
        if "variant" in role or role.endswith("_proxy"):
            continue
        for function in contract["functions"]:
            for name in sorted(names):
                signature = f"{name}({function['arguments']})"
                if "0x" + keccak(signature.encode())[:4].hex() != function["selector"]:
                    continue
                current = function.get("reconstructed_signature") or ""
                assert not current or current == signature, (role, function["selector"], current, signature)
                matches.append({"role": role, "address": address,
                                "selector": function["selector"], "signature": signature,
                                "arguments": function["arguments"],
                                "name_in_code": name in IDENTIFIER.findall(code),
                                "name_called_in_visible_text": name in CALLED.findall(visible)})
    assert len({(row["role"], row["selector"]) for row in matches}) == len(matches)
    result = {"report_url": URL, "report_sha256": hashlib.sha256(raw).hexdigest(),
              "candidate_name_count": len(names), "active_selector_match_count": len(matches),
              "matches": sorted(matches, key=lambda row: (row["role"], row["selector"])),
              "limits": ["The public report describes an audit source snapshot, not a verified match to pinned deployed bytecode.",
                         "A four-byte selector hash match and inferred ABI layout identify a signature candidate; runtime behavior is checked in separate atlas artifacts.",
                         "Disabled entrypoints retain their names but revert in the pinned production runtime."]}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    row = build()
    print(row["active_selector_match_count"], "matching selectors")
