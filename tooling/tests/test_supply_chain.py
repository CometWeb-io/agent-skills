"""SBOM, dependency audit coverage and the SAST gate's configuration.

The SAST rules themselves are tested by `semgrep --test` inside the gate; these
tests pin what makes that gate trustworthy without running the engine: it uses
the locked engine in an isolated environment, local rules only, no telemetry,
and every rule has cases.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"cw_supply_{name}", ROOT / "tooling" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


sbom = load("sbom")
audit = load("audit_deps")
sast = load("sast")


# --- SBOM -----------------------------------------------------------------

def shipped() -> list[str]:
    return sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))


def test_sbom_lists_every_skill_at_its_version_and_validates() -> None:
    bom = sbom.build(ROOT)
    sbom.validate(bom)
    skills = {c["name"]: c["version"] for c in bom["components"] if c["type"] == "application"}
    assert sorted(skills) == shipped()
    for name, version in skills.items():
        assert version == (ROOT / "skills" / name / "VERSION").read_text(encoding="utf-8").strip()
    plugin = bom["metadata"]["component"]
    assert plugin["version"] == (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert bom["dependencies"][0] == {"ref": "plugin", "dependsOn": sorted(f"skill:{n}@{v}" for n, v in skills.items())}


def test_sbom_runtime_libraries_come_from_runtime_json() -> None:
    bom = sbom.build(ROOT)
    libraries = {c["name"]: c for c in bom["components"] if c["type"] == "library"}
    declared = set()
    for path in (ROOT / "skills").glob("*/RUNTIME.json"):
        for group in json.loads(path.read_text(encoding="utf-8"))["dependencies"].values():
            declared |= {re.split(r"[<>=!~ ]", req, maxsplit=1)[0].lower() for req in group}
    assert set(libraries) == declared
    for lib in libraries.values():
        assert lib["scope"] == "optional" and lib["purl"] == f"pkg:pypi/{lib['name']}"
    edges = {d["ref"]: d["dependsOn"] for d in bom["dependencies"]}
    assert edges["skill:ebook-publisher@" + (ROOT / "skills/ebook-publisher/VERSION").read_text().strip()] == [
        "pypi:pypdf#vers:pypi/>=4|<7"]


def test_sbom_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1790000000")
    first, second = sbom.render(sbom.build(ROOT)), sbom.render(sbom.build(ROOT))
    assert first == second
    assert json.loads(first)["metadata"]["timestamp"] == "2026-09-21T14:13:20Z"


def test_sbom_serial_changes_with_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1790000000")
    root = mini_repo(tmp_path)
    before = sbom.build(root)["serialNumber"]
    (root / "skills" / "alpha" / "VERSION").write_text("1.0.1\n", encoding="utf-8")
    assert sbom.build(root)["serialNumber"] != before


def mini_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "skills" / "alpha").mkdir(parents=True)
    shutil.copy(ROOT / "LICENSE", root / "LICENSE")
    (root / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    skill = root / "skills" / "alpha"
    (skill / "SKILL.md").write_text("---\nname: alpha\n---\n", encoding="utf-8")
    (skill / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    shutil.copy(ROOT / "LICENSE", skill / "LICENSE")
    return root


def test_sbom_hashes_the_built_packages(tmp_path: Path) -> None:
    root = mini_repo(tmp_path)
    dist = tmp_path / "dist"
    (dist / "alpha" / "1.0.0").mkdir(parents=True)
    (dist / "alpha" / "1.0.0" / "skill.zip").write_bytes(b"zip bytes")
    bom = sbom.build(root, dist)
    sbom.validate(bom)
    (alpha,) = [c for c in bom["components"] if c["name"] == "alpha"]
    assert alpha["hashes"] == [{"alg": "SHA-256", "content": hashlib.sha256(b"zip bytes").hexdigest()}]


def test_sbom_refuses_a_missing_package_and_an_unknown_license(tmp_path: Path) -> None:
    root = mini_repo(tmp_path)
    with pytest.raises(sbom.SbomError, match="missing package"):
        sbom.build(root, tmp_path / "empty-dist")
    (root / "skills" / "alpha" / "LICENSE").write_text("Proprietary\n", encoding="utf-8")
    with pytest.raises(sbom.SbomError, match="unrecognised license"):
        sbom.build(root)


@pytest.mark.parametrize(("text", "expected"), [
    ("pypdf>=4,<7", ("pypdf", "vers:pypi/>=4|<7")),
    ("jsonschema>=4.18,<5", ("jsonschema", "vers:pypi/>=4.18|<5")),
    ("Referencing_Lib==0.28.4", ("referencing-lib", "vers:pypi/=0.28.4")),
    ("pyyaml", ("pyyaml", "vers:pypi/*")),
])
def test_requirement_to_vers(text: str, expected: tuple[str, str]) -> None:
    assert sbom.parse_requirement(text) == expected


@pytest.mark.parametrize("text", ["pypdf~=4.0", "pkg==1.*", "not a requirement!"])
def test_requirement_without_a_vers_equivalent_is_refused(text: str) -> None:
    with pytest.raises(sbom.SbomError):
        sbom.parse_requirement(text)


def test_sbom_check_mode_writes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert sbom.main(["--check"]) == 0
    assert capsys.readouterr().out.startswith("OK: CycloneDX 1.6 SBOM valid")


# --- Dependency audit coverage --------------------------------------------

def test_repository_runtime_dependencies_are_locked() -> None:
    assert audit.coverage_errors(ROOT) == []
    sources = {source for source, _ in audit.declared_runtime(ROOT)}
    assert "skills/web-app-auditor/requirements.txt" in sources
    assert "skills/ebook-publisher/RUNTIME.json" in sources


def audit_repo(tmp_path: Path, requirement: str, locked: str = "jsonschema") -> Path:
    root = tmp_path / "repo"
    (root / "skills" / "beta").mkdir(parents=True)
    (root / "skills" / "beta" / "RUNTIME.json").write_text(json.dumps({
        "schema": "cometweb.skill-runtime/v1", "python": ">=3.10",
        "dependencies": {"validate": [requirement]}}), encoding="utf-8")
    (root / "uv.lock").write_text(
        f'version = 1\n\n[[package]]\nname = "{locked}"\nversion = "4.26.0"\n', encoding="utf-8")
    return root


def test_runtime_dependency_missing_from_the_lock_fails(tmp_path: Path) -> None:
    root = audit_repo(tmp_path, "pypdf>=4,<7")
    (error,) = audit.coverage_errors(root)
    assert "pypdf is not in uv.lock" in error and "RUNTIME.json" in error


def test_locked_version_outside_the_declared_range_fails(tmp_path: Path) -> None:
    (error,) = audit.coverage_errors(audit_repo(tmp_path, "jsonschema>=4.18,<4.20"))
    assert "uv.lock has jsonschema 4.26.0" in error


def test_locked_version_inside_the_range_and_name_normalisation_pass(tmp_path: Path) -> None:
    assert audit.coverage_errors(audit_repo(tmp_path, "JSONSchema>=4.18,<5")) == []


def test_requirements_txt_is_covered_too(tmp_path: Path) -> None:
    root = audit_repo(tmp_path, "jsonschema>=4.18,<5")
    (root / "skills" / "beta" / "requirements.txt").write_text("# comment\npypdf>=4\n", encoding="utf-8")
    (error,) = audit.coverage_errors(root)
    assert error.startswith("skills/beta/requirements.txt: pypdf is not in uv.lock")


def test_every_audited_group_is_a_locked_dependency_group() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert set(audit.GROUPS) == set(project["dependency-groups"])


def test_lock_carries_a_hash_for_every_registry_artifact() -> None:
    """`--require-hashes` relies on this: a hashless entry would fail the audit, not skip it."""
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    for package in lock["package"]:
        if package.get("source", {}).get("registry"):
            artifacts = [*package.get("wheels", []), *([package["sdist"]] if "sdist" in package else [])]
            assert artifacts, package["name"]
            for artifact in artifacts:
                assert artifact.get("hash", "").startswith("sha256:"), package["name"]


# --- SAST gate configuration -----------------------------------------------

def test_sast_engine_is_pinned_exactly_and_isolated_from_dev() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    (engine,) = project["dependency-groups"]["sast"]
    assert re.fullmatch(r"semgrep==\d+\.\d+\.\d+", engine)
    assert [{"group": "dev"}, {"group": "sast"}] in project["tool"]["uv"]["conflicts"]
    argv = sast.semgrep_argv("scan")
    assert argv[:2] == ["uv", "run"] and {"--isolated", "--frozen"} <= set(argv)
    assert argv[argv.index("--only-group") + 1] == "sast"


def test_sast_runs_local_rules_without_telemetry(tmp_path: Path) -> None:
    env = sast.environment(tmp_path)
    assert env["SEMGREP_SEND_METRICS"] == "off" and env["SEMGREP_ENABLE_VERSION_CHECK"] == "0"
    for key in ("SEMGREP_SETTINGS_FILE", "SEMGREP_LOG_FILE"):
        assert Path(env[key]).parent == tmp_path
    source = (ROOT / "tooling" / "sast.py").read_text(encoding="utf-8")
    assert "--metrics=off" in source and "p/" not in re.findall(r'"--config", "([^"]+)"', source)


def test_sast_scope_skips_tests_fixtures_and_rule_cases() -> None:
    targets = sast.tracked_targets()
    assert "scripts/install-cursor.sh" in targets and "tooling/check_all.py" in targets
    assert not [t for t in targets if t.startswith("tooling/sast/") or "/tests/" in t or "/fixtures/" in t]


@pytest.mark.parametrize(("rules", "cases"), [("python.yml", "python.py"), ("shell.yml", "shell.sh")])
def test_every_sast_rule_has_positive_and_negative_cases(rules: str, cases: str) -> None:
    ids = [rule["id"] for rule in yaml.safe_load((ROOT / "tooling" / "sast" / rules).read_text())["rules"]]
    assert set(ids) and len(ids) == len(set(ids))
    text = (ROOT / "tooling" / "sast" / "tests" / cases).read_text(encoding="utf-8")
    for rule_id in ids:
        assert f"ruleid: {rule_id}" in text, f"{rule_id} has no positive case"
        assert f"ok: {rule_id}" in text, f"{rule_id} has no negative case"
    assert set(sast.RULE_FILES) == {"python.yml", "shell.yml"}


def _sast_tree(root: Path) -> None:
    for name in ("tooling/sast/python.yml", "tooling/sast/tests/python.py", "uv.lock", "tooling/sast.py", "a.py"):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(f"{name}\n", encoding="utf-8")


@pytest.mark.parametrize("changed", ["a.py", "tooling/sast/python.yml", "tooling/sast/tests/python.py",
                                     "uv.lock", "tooling/sast.py"])
def test_sast_cache_key_covers_every_input(tmp_path: Path, changed: str) -> None:
    _sast_tree(tmp_path)
    before = sast.inputs_key(["a.py"], tmp_path)
    assert sast.inputs_key(["a.py"], tmp_path) == before
    (tmp_path / changed).write_text("edited\n", encoding="utf-8")
    assert sast.inputs_key(["a.py"], tmp_path) != before


def test_sast_cache_key_covers_the_scan_scope(tmp_path: Path) -> None:
    """A newly tracked file changes the key even before anyone edits it."""
    _sast_tree(tmp_path)
    (tmp_path / "b.py").write_text("x = 1\n", encoding="utf-8")
    assert sast.inputs_key(["a.py"], tmp_path) != sast.inputs_key(["a.py", "b.py"], tmp_path)


def test_sast_reuses_only_a_clean_result_and_never_under_no_cache(tmp_path: Path, monkeypatch, capsys) -> None:
    runs: list[str] = []
    codes = {"--test": 0, "scan": 1}

    def fake_run(argv, env):
        step = "--test" if "--test" in argv else "scan"
        runs.append(step)
        return codes[step]

    monkeypatch.setattr(sast, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(sast, "run", fake_run)
    monkeypatch.setattr(sast, "tracked_targets", lambda: ["tooling/sast.py"])
    # A finding is never recorded, so the next run scans again.
    assert sast.main([]) == 1
    assert sast.main([]) == 1
    assert runs.count("scan") == 2
    codes["scan"] = 0
    assert sast.main([]) == 0
    runs.clear()
    assert sast.main([]) == 0
    assert runs == [] and "inputs unchanged" in capsys.readouterr().out
    assert sast.main(["--no-cache"]) == 0
    assert runs == ["--test", "scan"]


def test_ci_never_reuses_a_recorded_sast_result() -> None:
    check_all = load("check_all")
    gate = next(g for g in check_all.GATES if g.id == "sast")
    assert "--no-cache" in check_all.gate_argv(gate, ci=True)
    assert "--no-cache" not in check_all.gate_argv(gate, ci=False)


def test_sast_skips_a_tracked_file_deleted_in_the_working_tree(tmp_path: Path) -> None:
    """semgrep exits 2 on a path that does not exist, which read as "findings"
    while a contributor had merely deleted a file and not yet committed."""
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(tmp_path)}
    for name in ("kept.py", "deleted.py"):
        (tmp_path / name).write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, env={**os.environ, **env})
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, env={**os.environ, **env})
    (tmp_path / "deleted.py").unlink()
    assert sast.tracked_targets(tmp_path) == ["kept.py"]


# --- Release workflow --------------------------------------------------------

WORKFLOWS = ROOT / ".github" / "workflows"


def steps(name: str) -> list[dict]:
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    return [step for job in data["jobs"].values() for step in job.get("steps", [])]


def test_release_workflow_writes_attests_and_uploads_the_sbom() -> None:
    release = steps("attest-packages.yml")
    runs = [step.get("run", "") for step in release]
    sbom_at = next(i for i, run in enumerate(runs) if "tooling/sbom.py --dist dist --output dist/agent-skills.cdx.json" in run)
    build_at = next(i for i, run in enumerate(runs) if "tooling/package_skill.py" in run)
    assert build_at < sbom_at, "the SBOM hashes the packages, so it is written after they are built"
    attests = [step["with"] for step in release if step.get("uses", "").startswith("actions/attest@")]
    assert {"subject-path": "dist/**/skill.zip"} in attests
    assert {"subject-path": "dist/*/*/skill.zip", "sbom-path": "dist/agent-skills.cdx.json"} in attests
    (upload,) = [step["with"] for step in release if step.get("uses", "").startswith("actions/upload-artifact@")]
    assert "dist/agent-skills.cdx.json" in upload["path"] and upload["if-no-files-found"] == "error"


# Installs that do not come from uv.lock. The runtime matrix resolves each skill's
# declared range fresh on purpose: it tests what a user's resolver picks on
# Python 3.10-3.13, which the lock (Python >= 3.12) cannot describe.
UNLOCKED_INSTALLS = {"runtime-matrix.yml"}


@pytest.mark.parametrize("path", sorted(WORKFLOWS.glob("*.y*ml")), ids=lambda p: p.name)
def test_package_installs_come_from_the_lock(path: Path) -> None:
    for step in steps(path.name):
        run = step.get("run", "")
        if re.search(r"\b(pip install|uv pip install|uv tool install|uvx|pipx)\b", run):
            assert path.name in UNLOCKED_INSTALLS, f"{path.name}: {step.get('name')} installs outside uv.lock"
        if "uv sync" in run or "uv run" in run:
            assert "uv sync --frozen" in run or "uv sync" not in run, f"{path.name}: {step.get('name')}"


def test_security_policy_states_support_and_timeline() -> None:
    text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "| Version | Supported | How fixes arrive |" in text
    assert "### Disclosure timeline" in text and "| Acknowledge the report | 5 working days |" in text
    # The documented controls name the tools that implement them.
    for tool in ("tooling/audit_deps.py", "tooling/sast.py", "tooling/sbom.py", "gh attestation verify"):
        assert tool in text, tool


def test_a_release_tag_must_name_the_plugin_version() -> None:
    """A `v*` tag on a commit whose VERSION says otherwise would attest packages
    under a version no manifest carries."""
    release = steps("attest-packages.yml")
    names = [step.get("name", "") for step in release]
    check_at = next(i for i, step in enumerate(release)
                    if "VERSION" in step.get("run", "") and step.get("env", {}).get("TAG") == "${{ github.ref_name }}")
    assert release[check_at].get("if") == "startsWith(github.ref, 'refs/tags/v')"
    assert "${{" not in release[check_at]["run"], "pass the tag through env, never inline into the script"
    assert check_at < names.index("Build skill packages")
