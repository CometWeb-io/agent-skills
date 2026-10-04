"""A scaffolded skill must satisfy the repository's own contracts immediately.

Adding a skill meant copying an existing one and discovering the contract by
watching checks fail. A scaffold is only worth having if what it emits actually
passes those checks, so this generates one into a temporary tree and runs the
repository's real validators against it rather than asserting on file names.
The end-to-end case copies the whole checkout, scaffolds and registers a skill
there, and runs `check_all.py --fast` on the copy.
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tooling" / "new_skill.py"

DESCRIPTION = (
    "Scaffold probe skill used to verify that a freshly generated package satisfies the shared "
    "package surface, the adapter icon contract and the executable coverage rule without any "
    "manual editing beforehand."
)


def load_tool(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def scaffolded(tmp_path: Path):
    """Create the package in a private tree, never in this checkout.

    Writing into the real skills/ directory made every repository-wide check
    that ran meanwhile - eval baselines, context budget - see a phantom skill,
    which fails as soon as tests run in parallel.
    """
    skill_id = "scaffold-probe-skill"
    proc = subprocess.run(
        [sys.executable, str(TOOL), skill_id, "--description", DESCRIPTION, "--root", str(tmp_path),
         "--no-register"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    assert not (ROOT / "skills" / skill_id).exists()
    return tmp_path / "skills" / skill_id


@pytest.mark.parametrize("relative", [
    "SKILL.md", "VERSION", "LICENSE", "CHANGELOG.md",
    "assets/icon.svg", "references/output-contract.md",
    "scripts/run_evals.py", "scripts/output_contract.py", "evals/cases.json",
])
def test_scaffold_ships_the_shared_package_surface(scaffolded: Path, relative: str) -> None:
    assert (scaffolded / relative).is_file(), f"scaffold omitted {relative}"


def test_scaffold_passes_the_repository_skill_validator(scaffolded: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tooling" / "validate_skill.py"), str(scaffolded)],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_scaffold_harness_is_executable_and_answers_help(scaffolded: Path) -> None:
    harness = scaffolded / "scripts" / "run_evals.py"
    assert harness.stat().st_mode & 0o111, "harness is not executable"
    proc = subprocess.run([sys.executable, str(harness), "--help"],
                          cwd=scaffolded, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0 and "usage" in proc.stdout.lower()
    proc = subprocess.run([sys.executable, str(harness), "--no-such-option"],
                          cwd=scaffolded, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 2 and "unrecognized arguments: --no-such-option" in proc.stderr


def test_scaffold_harness_passes_and_bites(scaffolded: Path) -> None:
    """It passes as shipped, and fails when the rule it pins is removed."""
    harness = [sys.executable, "-B", "scripts/run_evals.py"]
    proc = subprocess.run(harness, cwd=scaffolded, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    kernel = scaffolded / "scripts" / "output_contract.py"
    source = kernel.read_text(encoding="utf-8")
    weakened = source.replace("if result.get(\"status\") not in STATUSES:", "if False:")
    assert weakened != source
    kernel.write_text(weakened, encoding="utf-8")
    proc = subprocess.run(harness, cwd=scaffolded, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "unknown-status" in proc.stdout


def test_scaffold_harness_holds_every_guard(scaffolded: Path) -> None:
    """eval_strength's floor applies from day one, so every rule must be pinned."""
    strength = load_tool(ROOT / "tooling" / "eval_strength.py", "scaffold_eval_strength")
    row = strength.measure(scaffolded)
    assert row["guards"] >= 5
    assert row["held"] == row["guards"], row["unheld"]
    assert row["modules"] == ["output_contract.py"] and row["unexercised"] == []


@pytest.mark.parametrize("skill_id,description,reason", [
    ("Bad Id", DESCRIPTION, "invalid skill id"),
    ("fine-id", "too short", "at least 80 characters"),
    ("fine-id", "x" * 1100, "1024"),
])
def test_scaffold_rejects_input_the_validators_would_reject(skill_id, description, reason) -> None:
    proc = subprocess.run([sys.executable, str(TOOL), skill_id, "--description", description],
                          cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode != 0
    assert reason in (proc.stdout + proc.stderr)


def test_register_refuses_a_tree_without_a_registry(tmp_path: Path) -> None:
    proc = subprocess.run([sys.executable, str(TOOL), "lonely-skill", "--description", DESCRIPTION,
                           "--root", str(tmp_path)], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode != 0
    assert "--no-register" in proc.stdout + proc.stderr


def test_force_refuses_a_symlinked_skill_directory(tmp_path: Path) -> None:
    skills = tmp_path / "skills"
    skills.mkdir()
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "KEEP").write_text("KEEP\n", encoding="utf-8")
    (skills / "symlinked-skill").symlink_to(victim, target_is_directory=True)

    proc = subprocess.run(
        [sys.executable, str(TOOL), "symlinked-skill", "--description", DESCRIPTION,
         "--root", str(tmp_path), "--no-register", "--force"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )

    assert proc.returncode != 0
    assert "must not be a symlink" in proc.stdout + proc.stderr
    assert [path.name for path in victim.iterdir()] == ["KEEP"]
    assert (victim / "KEEP").read_text(encoding="utf-8") == "KEEP\n"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True,
                          timeout=120).stdout


@pytest.fixture
def checkout_copy(tmp_path: Path) -> Path:
    """Tracked and non-ignored files of this checkout, committed in a fresh repo."""
    listed = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                            capture_output=True, check=True, timeout=120).stdout.decode().split("\0")
    copy = tmp_path / "checkout"
    for relative in filter(None, listed):
        source = ROOT / relative
        if not source.is_file():
            continue  # deleted in the working tree but still in the index
        target = copy / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    git(copy, "init", "-q")
    git(copy, "add", "-A")
    git(copy, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "core.hooksPath=/dev/null", "commit", "-qm", "baseline")
    return copy


def test_new_skill_passes_every_fast_gate_out_of_the_box(checkout_copy: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "-B", "tooling/new_skill.py", "scaffold-probe", "--description", DESCRIPTION],
        cwd=checkout_copy, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    changed = {line[3:] for line in git(checkout_copy, "status", "--porcelain", "-uall").splitlines()}
    for expected in ("registry/skills.json", "registry/readme-catalog.json", "evals/routing/suite.json",
                     "registry/context-baseline.json", "registry/eval-strength.json", "README.md",
                     "skills/scaffold-probe/SKILL.md", "skills/scaffold-probe/agents/openai.yaml",
                     "evals/behavior/scaffold-probe/suite.json"):
        assert expected in changed, f"new_skill.py did not write {expected}"

    # One --fix run proves both halves. The generators agree with what
    # new_skill.py wrote, because the tree is unchanged afterwards; so the fast
    # gates that then pass ran on exactly the tree new_skill.py left behind.
    before = git(checkout_copy, "status", "--porcelain", "-uall") + git(checkout_copy, "diff")
    proc = subprocess.run([sys.executable, "-B", "tooling/check_all.py", "--fast", "--fix"], cwd=checkout_copy,
                          capture_output=True, text=True, timeout=600)
    assert git(checkout_copy, "status", "--porcelain", "-uall") + git(checkout_copy, "diff") == before
    assert proc.returncode == 0, proc.stdout[-6000:]
    assert "0 failed" in proc.stdout

    registry = json.loads((checkout_copy / "registry" / "skills.json").read_text(encoding="utf-8"))
    entry = next(s for s in registry["skills"] if s["id"] == "scaffold-probe")
    assert entry["routing_signals"], "a registered skill must be routable"


def test_rules_live_in_a_module_eval_strength_measures(scaffolded: Path) -> None:
    """Logic written inside run_evals.py is never mutated, so the rules must sit
    in a module the harness names."""
    strength = load_tool(ROOT / "tooling" / "eval_strength.py", "scaffold_eval_strength_kernels")
    assert strength.kernels(scaffolded) == [scaffolded / "scripts" / "output_contract.py"]


def test_next_steps_name_every_placeholder_file_the_scaffold_writes(scaffolded: Path) -> None:
    new_skill = load_tool(TOOL, "scaffold_new_skill")
    text = new_skill.next_steps("scaffold-probe-skill")
    for relative, _ in new_skill.PLACEHOLDER_FILES:
        assert (scaffolded / relative).is_file(), f"PLACEHOLDER_FILES names an unwritten file: {relative}"
        assert f"skills/scaffold-probe-skill/{relative}" in text
    assert "scaffold-probe-skill-scaffold-*" in text
    assert "plugin_release.py --bump minor" in text


def test_cli_prints_every_file_it_wrote(tmp_path: Path) -> None:
    proc = subprocess.run([sys.executable, str(TOOL), "listed-skill", "--description", DESCRIPTION,
                           "--root", str(tmp_path), "--no-register"],
                          cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    written = {p.relative_to(tmp_path).as_posix() for p in (tmp_path / "skills").rglob("*") if p.is_file()}
    printed = {line.strip() for line in proc.stdout.splitlines() if line.startswith("  skills/")}
    assert written and printed == written


def test_contributing_walkthrough_names_every_placeholder_file() -> None:
    # The walkthrough has one home, CONTRIBUTING; the README links to it.
    new_skill = load_tool(TOOL, "scaffold_new_skill_readme")
    guide = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    start = guide.index("## Adding a skill")
    section = guide[start:guide.index("\n## ", start + 1)]
    for relative, _ in new_skill.PLACEHOLDER_FILES:
        assert relative in section, f"CONTRIBUTING walkthrough omits {relative}"
    assert "plugin version" in section.lower()


def test_every_file_stating_the_skill_count_is_generated() -> None:
    """A hand-maintained count breaks the suite when a skill is added; each file
    that repeats it must be rewritten by generate_adapters.py."""
    adapters = load_tool(ROOT / "tooling" / "generate_adapters.py", "scaffold_generate_adapters")
    registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    count = len(registry["skills"])
    stating = re.compile(rf"\({count} packages\)|skills-{count}-|contains {count} reusable|OK: {count} Claude Code")
    candidates = [*ROOT.glob("*.md"), *ROOT.glob(".*-plugin/*.json"), ROOT / "plugin.json"]
    found = {p for p in candidates if p.is_file() and stating.search(p.read_text(encoding="utf-8"))}
    assert found, "pattern matched nothing; the count wording changed"
    generated = set(adapters.expected_artifacts(registry["skills"]))
    assert found <= generated, f"files repeat the skill count but are not generated: {sorted(found - generated)}"


def test_scaffold_ships_the_untrusted_content_contract(scaffolded: Path) -> None:
    """Every skill keeps the shared untrusted-content block on its front door and
    tags it in tests/front-door-rules.json; a scaffold without them failed the
    full suite on the day it was created."""
    inventory = json.loads((scaffolded / "tests" / "front-door-rules.json").read_text(encoding="utf-8"))
    assert inventory["skill"] == scaffolded.name
    facets = {rule.get("facet") for rule in inventory["rules"]}
    assert {"data-not-instructions", "no-embedded-execution", "no-exfiltration", "no-credential-entry",
            "confirm-side-effects"} <= facets
    skill_md = " ".join((scaffolded / "SKILL.md").read_text(encoding="utf-8").split())
    assert "## Untrusted content" in (scaffolded / "SKILL.md").read_text(encoding="utf-8")
    for rule in inventory["rules"]:
        assert rule["where"] == "SKILL.md"
        assert " ".join(rule["text"].split()) in skill_md, rule["id"]
