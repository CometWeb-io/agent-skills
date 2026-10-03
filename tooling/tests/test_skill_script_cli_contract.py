"""Every executable script bundled in a skill keeps the same command-line contract.

Users and hosts run these scripts directly, usually after reading only `--help`.
Eleven eval harnesses answered `--help` with exit 2, and three entrypoints
accepted any argument and ran anyway, so a mistyped flag looked like a pass.

The contract checked for every script that has a `__main__` block:

* `--help` exits 0 and prints a usage line;
* an unknown option exits non-zero with a message and no traceback;
* neither run writes into the working directory or the skill package.

Modules without a `__main__` block are libraries. They are not skipped (the
local gate treats a skip as unproven); each must instead be imported from
somewhere in its own package, so a script cannot drop out of the sweep by
losing its main block. The sweep also pins the dependency side of the contract: a
script may import only the standard library, its own siblings, or a module the
skill declares in RUNTIME.json — and every skill that declares one is exercised
by the runtime matrix workflow.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAIN_BLOCK = re.compile(r"^if __name__\s*==\s*['\"]__main__['\"]\s*:", re.MULTILINE)
UNKNOWN_OPTION = "--definitely-not-a-real-option"

# Import name -> distribution name, for the dependencies RUNTIME.json may declare.
DISTRIBUTION_FOR_IMPORT = {"jsonschema": "jsonschema", "pypdf": "pypdf"}


def bundled_scripts() -> list[Path]:
    return sorted(p for p in ROOT.glob("skills/*/scripts/**/*.py") if "__pycache__" not in p.parts)


def is_cli(path: Path) -> bool:
    return bool(MAIN_BLOCK.search(path.read_text(encoding="utf-8")))


def script_id(path: Path) -> str:
    return path.relative_to(ROOT / "skills").as_posix()


def tree_listing(directory: Path) -> set[str]:
    return {
        p.relative_to(directory).as_posix()
        for p in directory.rglob("*")
        if "__pycache__" not in p.parts and not p.name.endswith(".pyc")
    }


def run(script: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=60, check=False,
    )


def entrypoints() -> list[Path]:
    return [p for p in bundled_scripts() if is_cli(p)]


def library_modules() -> list[Path]:
    return [p for p in bundled_scripts() if not is_cli(p)]


@pytest.mark.parametrize("script", entrypoints(), ids=script_id)
def test_cli_help_and_unknown_option(script: Path, tmp_path: Path) -> None:
    skill_dir = ROOT / "skills" / script.relative_to(ROOT / "skills").parts[0]
    before = tree_listing(skill_dir)

    shown = run(script, "--help", cwd=tmp_path)
    assert shown.returncode == 0, f"--help exited {shown.returncode}: {shown.stderr.strip()[-400:]}"
    assert "Traceback" not in shown.stderr, shown.stderr[-800:]
    assert "usage" in (shown.stdout + shown.stderr).lower(), "--help printed no usage line"

    rejected = run(script, UNKNOWN_OPTION, cwd=tmp_path)
    assert rejected.returncode != 0, f"an unknown option was accepted: {rejected.stdout.strip()[-400:]}"
    assert "Traceback" not in rejected.stderr, rejected.stderr[-800:]
    assert (rejected.stderr + rejected.stdout).strip(), "an unknown option was rejected without a message"

    assert not any(tmp_path.iterdir()), f"wrote into the working directory: {sorted(os.listdir(tmp_path))}"
    assert tree_listing(skill_dir) == before, "wrote into the skill package"


@pytest.mark.parametrize("module", library_modules(), ids=script_id)
def test_library_module_is_reached_from_its_package(module: Path) -> None:
    # A module without a __main__ block has no command line to sweep. That is
    # only acceptable when something in its own package imports it: otherwise
    # it is either dead code or an entrypoint that lost its main block.
    scripts_dir = ROOT / "skills" / module.relative_to(ROOT / "skills").parts[0] / "scripts"
    name = module.parent.name if module.name == "__init__.py" else module.stem
    importers = [
        other for other in scripts_dir.rglob("*.py")
        if other != module and re.search(rf"\b{re.escape(name)}\b", other.read_text(encoding="utf-8"))
    ]
    if not importers:
        # A package-level kernel is loaded by its eval harness through importlib.
        harness_dirs = [scripts_dir.parent / "evals", scripts_dir.parent / "tests"]
        importers = [p for d in harness_dirs if d.is_dir() for p in d.rglob("*.py")
                     if re.search(rf"\b{re.escape(name)}\b", p.read_text(encoding="utf-8"))]
    assert importers, f"{script_id(module)} has no __main__ block and nothing in its package imports it"


def test_sweep_sees_every_entrypoint() -> None:
    # The CLI sweep must cover the scripts users are told to run; if discovery
    # broke, the parametrization above would quietly shrink.
    clis = entrypoints()
    assert len(clis) >= 60
    assert {p.parents[1].name for p in clis if p.parent.name == "scripts"} >= {
        "web-app-auditor", "ebook-publisher", "skill-orchestrator-multiagent", "seo-geo-aeo-maxxing",
    }


def runtime_dependencies(skill_dir: Path) -> set[str]:
    path = skill_dir / "RUNTIME.json"
    if not path.is_file():
        return set()
    runtime = json.loads(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for group in (runtime.get("dependencies") or {}).values():
        for requirement in group:
            names.add(re.split(r"[<>=!~;\[ ]", requirement, maxsplit=1)[0].strip().lower())
    return names


def imported_top_level_names(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def skills_with_scripts() -> list[str]:
    return sorted({p.relative_to(ROOT / "skills").parts[0] for p in bundled_scripts()})


@pytest.mark.parametrize("skill", skills_with_scripts())
def test_scripts_import_only_stdlib_siblings_or_declared_deps(skill: str) -> None:
    scripts_dir = ROOT / "skills" / skill / "scripts"
    local = {p.stem for p in scripts_dir.rglob("*.py")} | {p.name for p in scripts_dir.rglob("*") if p.is_dir()}
    declared = runtime_dependencies(scripts_dir.parent)
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    undeclared: dict[str, list[str]] = {}
    for path in sorted(scripts_dir.rglob("*.py")):
        for name in sorted(imported_top_level_names(path) - stdlib - local):
            if DISTRIBUTION_FOR_IMPORT.get(name, name).lower() not in declared:
                undeclared.setdefault(name, []).append(path.relative_to(scripts_dir).as_posix())
    assert not undeclared, f"imports not declared in RUNTIME.json: {undeclared}"


def test_runtime_matrix_covers_every_skill_that_declares_dependencies() -> None:
    workflow = (ROOT / ".github" / "workflows" / "runtime-matrix.yml").read_text(encoding="utf-8")
    in_matrix = set(re.findall(r"^\s*- skill: ([a-z0-9-]+)\s*$", workflow, re.MULTILINE))
    declaring = {d.name for d in (ROOT / "skills").iterdir() if runtime_dependencies(d)}
    assert declaring <= in_matrix, f"RUNTIME.json dependencies with no runtime-matrix job: {sorted(declaring - in_matrix)}"
    # The stdlib-only job leaves those skills out; a skill dropped from that
    # list without a job of its own would stop being tested on old Pythons.
    ignored = set(re.findall(r"--ignore=skills/([a-z0-9-]+)", workflow))
    assert ignored == declaring, f"stdlib job ignores {sorted(ignored)}, declared deps in {sorted(declaring)}"
    assert '"3.10"' in workflow and '"3.13"' in workflow


# --- wrongly typed nested fields -------------------------------------------
#
# test_validators_survive_malformed_input.py covers malformed *roots*. A
# type-mutation sweep over the bundled fixtures found entrypoints that still
# died with AttributeError/TypeError tracebacks on one wrongly typed nested
# field. Each case below starts from a valid bundled fixture, breaks exactly one
# field, and expects a reported rejection: non-zero exit, a message, no
# traceback.

def _set(data, path, value):
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return data


MAXX_AUDIT = "seo-geo-aeo-maxxing/tests/sample_audit.json"
LONGFORM_REPORT = "longform-publisher/examples/example-report.json"
OPERATOR_BRIEF = "product-operator/examples/brief.synthetic.pl.json"

NESTED_CASES = [
    ("seo-geo-aeo-maxxing/scripts/score_maxx.py", MAXX_AUDIT, ("checks", 0, "evidence", 0, "class"), [], ["{f}"]),
    ("seo-geo-aeo-maxxing/scripts/score_maxx.py", MAXX_AUDIT, ("checks", 0, "id"), {}, ["{f}"]),
    ("seo-geo-aeo-maxxing/scripts/score_maxx.py", MAXX_AUDIT, ("active_pillars", 0), None, ["{f}"]),
    ("seo-geo-aeo-maxxing/scripts/score_maxx.py", MAXX_AUDIT, ("target_surfaces", 0), 3, ["{f}"]),
    ("longform-publisher/scripts/publication_kernel.py", LONGFORM_REPORT, ("sources",), "x",
     ["validate", "--report-json", "{f}"]),
    ("longform-publisher/scripts/publication_kernel.py", LONGFORM_REPORT, ("claim_uses", 0, "evidence_refs", 0), [],
     ["validate", "--report-json", "{f}"]),
    ("longform-publisher/scripts/publication_kernel.py", LONGFORM_REPORT, ("lifecycle",), 3,
     ["check-derived", "--report-json", "{f}"]),
    ("longform-publisher/scripts/publication_kernel.py", LONGFORM_REPORT, ("claim_uses", 0, "citation_marker"), 3,
     ["check-manuscript", "--report-json", "{f}", "--manuscript-file", "{f}"]),
    ("longform-publisher/scripts/publication_kernel.py", LONGFORM_REPORT, ("actions",), {"now": 3},
     ["render-manifest", "--report-json", "{f}", "--output", "{out}"]),
    ("product-operator/scripts/operator_kernel.py", OPERATOR_BRIEF, ("coverage",), 3, ["plan", "--input-json", "{f}"]),
    ("product-operator/scripts/operator_kernel.py", OPERATOR_BRIEF, ("candidates", 0, "depends_on"), 3,
     ["plan", "--input-json", "{f}"]),
    ("product-operator/scripts/prepare_brief.py", OPERATOR_BRIEF, ("coverage",), [], ["--input", "{f}"]),
]


@pytest.mark.parametrize("script,fixture,path,value,args", NESTED_CASES,
                         ids=[f"{c[0].split('/')[-1]}:{'.'.join(map(str, c[2]))}={c[3]!r}" for c in NESTED_CASES])
def test_wrongly_typed_nested_field_is_reported(script, fixture, path, value, args, tmp_path: Path) -> None:
    data = json.loads((ROOT / "skills" / fixture).read_text(encoding="utf-8"))
    broken = tmp_path / "input.json"
    broken.write_text(json.dumps(_set(data, path, value)), encoding="utf-8")
    out = tmp_path / "out.md"
    argv = [a.format(f=broken, out=out) for a in args]
    result = run(ROOT / "skills" / script, *argv, cwd=tmp_path)
    assert "Traceback" not in result.stderr, result.stderr[-800:]
    assert result.returncode != 0, result.stdout[-400:]
    assert (result.stdout + result.stderr).strip()
    assert not out.exists(), "a rejected report still rendered a manifest"


def test_prepare_brief_treats_null_coverage_as_absent(tmp_path: Path) -> None:
    data = json.loads((ROOT / "skills" / OPERATOR_BRIEF).read_text(encoding="utf-8"))
    data["coverage"] = None
    source = tmp_path / "input.json"
    source.write_text(json.dumps(data), encoding="utf-8")
    result = run(ROOT / "skills" / "product-operator/scripts/prepare_brief.py", "--input", str(source), cwd=tmp_path)
    assert result.returncode == 0, result.stderr[-400:] or result.stdout[-400:]


def _maxx_score(**overrides):
    score = {
        "scoring_engine_version": "1", "registry_version": "1", "profile": "balanced", "weights": {},
        "active_pillars": ["foundation"], "target_surfaces": [], "score_name": "MAXX", "maxx": 50.0,
        "overall_coverage": 80.0, "pillars": {"foundation": {"score": 50.0, "coverage": 80.0}},
        "check_results": [{"id": "FND-01", "verdict": "PASS", "points": 1.0}],
        "gates_applied": [], "freshness_used": [{"group": "g", "state": "CURRENT"}],
    }
    score.update(overrides)
    return score


@pytest.mark.parametrize("override", [
    {"pillars": {"foundation": "x"}},
    {"pillars": []},
    {"active_pillars": None},
    {"maxx": []},
    {"check_results": [{"verdict": "PASS"}]},
    {"freshness_used": [{"group": None}]},
    {"gates_applied": "x"},
], ids=lambda o: next(iter(o)))
def test_compare_scores_rejects_malformed_score_files(override, tmp_path: Path) -> None:
    script = ROOT / "skills" / "seo-geo-aeo-maxxing/scripts/compare_scores.py"
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps(_maxx_score()), encoding="utf-8")
    bad.write_text(json.dumps(_maxx_score(**override)), encoding="utf-8")
    assert run(script, str(good), str(good), cwd=tmp_path).returncode == 0
    for argv in ((good, bad), (bad, good)):
        result = run(script, *map(str, argv), cwd=tmp_path)
        assert result.returncode == 1 and "Traceback" not in result.stderr, result.stderr[-800:]
        assert "score:" in result.stderr


def test_jsonschema_validator_without_jsonschema_explains_instead_of_crashing(tmp_path: Path) -> None:
    # The declared dependency may be missing on a host. --help must still work
    # and validation must fail closed with an install hint, not an ImportError.
    blocker = tmp_path / "blocker"
    blocker.mkdir()
    (blocker / "sitecustomize.py").write_text(
        "import sys\nsys.modules['jsonschema'] = None\n", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(blocker), "PYTHONDONTWRITEBYTECODE": "1"}
    script = ROOT / "skills" / "web-app-auditor/scripts/validate_report.py"
    report = ROOT / "skills" / "web-app-auditor/tests/report-valid.json"

    def call(*args):
        return subprocess.run([sys.executable, str(script), *args], cwd=tmp_path, env=env,
                              capture_output=True, text=True, timeout=60, check=False)

    shown = call("--help")
    assert shown.returncode == 0 and "usage" in shown.stdout
    result = call(str(report))
    assert result.returncode == 2, result.stdout
    assert "Traceback" not in result.stderr and "jsonschema" in result.stderr
