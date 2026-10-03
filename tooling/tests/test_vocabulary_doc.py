"""docs/VOCABULARY.md stays the true map of the shared vocabularies.

Thirty-two skills each declare their enums in references/contract.json, and
CW-AIP declares its own in protocol/. The same concept (a verdict, a severity,
a confidence band, a freshness state, a gate status, a run status, an envelope
kind) is spelled differently in several of them, mostly on purpose. The
document records every spelling and why it differs. This test keeps it honest
in both directions:

- every table row names a real skill field or protocol property, and lists
  exactly the values its contract or schema accepts;
- every contract field that carries one of these concepts has a row, so a new
  severity scale or verdict cannot ship without being placed next to the others;
- the one boundary mapping the document states (a Council verdict on a v2
  DecisionEnvelope) still holds against both sides.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))

import skill_contracts as sc  # noqa: E402

DOC = ROOT / "docs" / "VOCABULARY.md"
PROTOCOL = ROOT / "protocol"

# Contract fields that carry a shared concept, matched on the key as
# skill_contracts.all_specs reports it (outputs are prefixed `output:`).
BARE = {"verdict", "review_outcome", "severity", "confidence", "freshness", "freshness_status",
        "gate_status", "gate_statuses", "envelope_out"}
QUALIFIED = {"governance_gates.status", "output:status", "output:result"}

ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|([^|]*)\|")


def concept_field(key: str) -> bool:
    return key in QUALIFIED or key.split(":")[-1].rsplit(".", 1)[-1] in BARE


def doc_rows(text: str) -> list[tuple[str, str, set[str]]]:
    rows = []
    for line in text.splitlines():
        match = ROW.match(line.strip())
        if match:
            owner, field, cell = match.groups()
            rows.append((owner, field, set(re.findall(r"`([^`]+)`", cell))))
    return rows


def skills() -> list[str]:
    return sorted(p.parent.parent.name for p in (ROOT / "skills").glob("*/references/contract.json"))


def contract_enums(skill: str) -> dict[str, set[str]]:
    specs = sc.all_specs(skill, sc.load_contract(skill))
    return {key: {str(v) for v in spec["enum"]} for key, spec in specs.items() if "enum" in spec}


def protocol_enums(rel: str) -> dict[str, set[str]]:
    _, enums = sc.schema_vocabulary(json.loads((PROTOCOL / rel).read_text(encoding="utf-8")))
    return enums


def expected(owner: str, field: str) -> set[str] | None:
    if owner.startswith("cw-aip-"):
        path = PROTOCOL / owner
        return protocol_enums(owner).get(field) if path.is_file() else None
    if owner not in skills():
        return None
    return contract_enums(owner).get(field)


@pytest.fixture(scope="module")
def rows() -> list[tuple[str, str, set[str]]]:
    assert DOC.is_file(), "docs/VOCABULARY.md is missing"
    found = doc_rows(DOC.read_text(encoding="utf-8"))
    assert found, "docs/VOCABULARY.md has no vocabulary rows"
    return found


def test_every_row_matches_its_contract(rows) -> None:
    wrong = []
    for owner, field, values in rows:
        truth = expected(owner, field)
        if truth is None:
            wrong.append(f"{owner} {field}: no such enum")
        elif values != truth:
            wrong.append(f"{owner} {field}: doc {sorted(values)} != contract {sorted(truth)}")
    assert not wrong, "docs/VOCABULARY.md disagrees with the contracts:\n" + "\n".join(wrong)


def test_every_concept_field_is_documented(rows) -> None:
    listed = {(owner, field) for owner, field, _ in rows}
    missing = [f"{skill} {key}" for skill in skills() for key in contract_enums(skill)
               if concept_field(key) and (skill, key) not in listed]
    assert not missing, "concept fields with no row in docs/VOCABULARY.md:\n" + "\n".join(missing)


def test_rows_are_not_repeated(rows) -> None:
    keys = [(owner, field) for owner, field, _ in rows]
    assert len(keys) == len(set(keys))


def test_council_verdict_maps_onto_the_v2_decision_envelope() -> None:
    council = contract_enums("ai-council")["verdict"]
    wire = protocol_enums("cw-aip-v2/decision.schema.json")["verdict"]
    assert {v.replace("-", "_") for v in council} == wire
    assert "NO-GO" in council and "NO_GO" in wire


def test_detector_sees_a_drifted_row(tmp_path: Path) -> None:
    text = "| `release-readiness` | `output:verdict` | `GO` `NO-GO` `DEFER` `GO_WITH_CONTROLS` | |\n"
    owner, field, values = doc_rows(text)[0]
    assert values != expected(owner, field)


MIXED_SPELLING = re.compile(r"\bGO-NO_GO\b|\bGO_NO-GO\b|\bNO GO\b")
RELEASE = re.compile(r"release-readiness|release readiness", re.IGNORECASE)
COUNCIL = re.compile(r"council|ai-council", re.IGNORECASE)


def prose_lines() -> list[tuple[str, int, str]]:
    out = []
    for path in sorted((ROOT / "skills").rglob("*.md")):
        if path.name == "CHANGELOG.md":
            continue  # history records the spelling of its day
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            out.append((path.relative_to(ROOT).as_posix(), number, line))
    return out


def test_release_verdicts_keep_release_readiness_spelling() -> None:
    """Release Readiness says NO_GO; Council says NO-GO. A line about one uses its spelling."""
    wrong = [f"{path}:{number}: {line.strip()}" for path, number, line in prose_lines()
             if "NO-GO" in line and RELEASE.search(line) and not COUNCIL.search(line)]
    wrong += [f"{path}:{number}: {line.strip()}" for path, number, line in prose_lines()
              if MIXED_SPELLING.search(line)]
    assert not wrong, "verdict spelled against its owner's contract:\n" + "\n".join(wrong)
