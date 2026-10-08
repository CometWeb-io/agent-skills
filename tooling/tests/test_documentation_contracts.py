"""Keep operator documentation aligned with shipped commands and packages."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

QUALITY_SKILLS = {
    "artifact-acceptance": "1.7.4",
    "benchmark-curator": "1.7.4",
    "brief-architect": "1.8.0",
    "content-reviewer": "1.7.4",
    "content-writer": "1.7.4",
    "feedback-integrator": "1.8.0",
    "quality-loop-operator": "1.7.4",
    "repair-operator": "1.7.4",
    "rubric-designer": "1.7.4",
    "skill-auditor": "1.7.5",
    "skill-evaluator": "1.7.4",
}


def test_quality_readmes_match_shipped_versions() -> None:
    for skill, version in QUALITY_SKILLS.items():
        readme = (ROOT / "skills" / skill / "README.md").read_text(encoding="utf-8")
        shipped = (ROOT / "skills" / skill / "VERSION").read_text(encoding="utf-8").strip()
        assert shipped == version
        assert version in readme, f"{skill}/README.md does not name {version}"


def test_quality_integration_docs_match_shipped_versions() -> None:
    document = (ROOT / "docs" / "QUALITY-SUITE-INTEGRATION.md").read_text(encoding="utf-8")
    for skill, version in QUALITY_SKILLS.items():
        assert f"`{skill}`" in document
        assert f"`{version}`" in document
    for skill in ("content-roaster", "science-roaster", "repo-roaster"):
        assert f"`{skill}`" in document
    assert "`6.1.3`" in document


def test_release_rehearsal_matches_attestation_workflow() -> None:
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    release_section = contributing.split("## Releases", 1)[1]
    workflow = (ROOT / ".github" / "workflows" / "attest-packages.yml").read_text(encoding="utf-8")

    expected = (
        "tooling/validate_local.py",
        "tooling/public_safety.py --root .",
        "tooling/installation_acceptance.py --all --run-helpers --trusted-checkout",
        "tooling/package_skill.py",
        "tooling/sbom.py --dist dist",
    )
    for command in expected:
        assert command in release_section
    assert "tooling/validate_local.py" in workflow
    assert "tooling/check_all.py --ci" not in release_section


def test_documented_operator_paths_exist() -> None:
    for relative in (
        "tooling/audit_contracts.py",
        "fixtures/contract-trace/synthetic-complete.json",
        "tooling/review_skill_evals.py",
        "tooling/run_model_evals.py",
        "tooling/openai_eval_runner.py",
        "evals/model/suite.json",
        "evals/model/continuation-suite.json",
        "docs/SIGNED-COMMITS.md",
    ):
        assert (ROOT / relative).exists(), relative

    signed_commits = (ROOT / "docs" / "SIGNED-COMMITS.md").read_text(encoding="utf-8")
    assert "cd platforms/agent-skills" not in signed_commits


def test_documentation_index_links_affected_topics() -> None:
    index = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    for document in (
        "QUALITY-SUITE-INTEGRATION.md",
        "CONTRACT-TRACE-AND-SKILL-EVALS.md",
        "SIGNED-COMMITS.md",
    ):
        assert f"]({document})" in index


def test_starter_examples_use_explicit_python3() -> None:
    paths = (
        ROOT / "skills" / "ebook-publisher" / "README.md",
        ROOT / "skills" / "ai-humanize" / "evaluation" / "README.md",
    )
    bare_python = re.compile(r"^python(?:\s|$)", re.MULTILINE)
    for path in paths:
        assert not bare_python.search(path.read_text(encoding="utf-8")), path
