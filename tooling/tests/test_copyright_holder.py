"""First-party license files and manifests must name the actual copyright holder.

The project is owned by Maciej Zmitrukiewicz; CometWeb is a product name, not a
company. Earlier LICENSE files named "CometWeb Labs" or "CometWeb" instead, and
the plugin manifests repeated that as author and owner. Third-party licenses
kept under capability-packs/ and specialist-profiles/ are not ours to change.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOLDER = "Maciej Zmitrukiewicz"
FIRST_PARTY_LICENSES = (
    ROOT / "LICENSE",
    ROOT / "resources/context/LICENSE",
    *sorted((ROOT / "skills").glob("*/LICENSE")),
)
IDENTITY_MANIFESTS = (
    ("plugin.json", "author"),
    (".claude-plugin/plugin.json", "author"),
    (".cursor-plugin/plugin.json", "author"),
    (".claude-plugin/marketplace.json", "owner"),
    (".cursor-plugin/marketplace.json", "owner"),
)


def test_first_party_licenses_name_the_copyright_holder() -> None:
    assert len(FIRST_PARTY_LICENSES) > 2
    pattern = re.compile(rf"^Copyright \(c\) \d{{4}}(?:-\d{{4}})? {re.escape(HOLDER)}$", re.MULTILINE)
    wrong = [str(path.relative_to(ROOT)) for path in FIRST_PARTY_LICENSES
             if not pattern.search(path.read_text(encoding="utf-8"))]
    assert wrong == []


def test_manifests_name_the_copyright_holder() -> None:
    for relative, field in IDENTITY_MANIFESTS:
        data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        assert data[field]["name"] == HOLDER, relative


def test_notice_names_the_copyright_holder() -> None:
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert f"copyright {HOLDER}" in notice
    assert "licensed by CometWeb Labs" not in notice
