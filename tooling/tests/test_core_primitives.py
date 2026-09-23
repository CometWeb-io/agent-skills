"""Smoke tests for shared tooling.core primitives."""
from __future__ import annotations

from pathlib import Path

from core import (
    DEFAULT_RELEASE_EVIDENCE,
    EvidenceKind,
    build_runner_env,
    canonical_input,
    canonical_output,
    read_git,
)


def test_evidence_taxonomy_defaults_separate_model_from_static() -> None:
    assert EvidenceKind.MODEL_EVAL.value == "model_eval"
    assert DEFAULT_RELEASE_EVIDENCE[EvidenceKind.MODEL_EVAL.value] == "not_run"
    assert DEFAULT_RELEASE_EVIDENCE[EvidenceKind.STATIC.value] == "passed"


def test_runner_env_does_not_inherit_arbitrary_secrets(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "should-not-leak")
    env = build_runner_env({"OPENAI_API_KEY"})
    assert env["OPENAI_API_KEY"] == "sk-test"
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert env["PYTHONNOUSERSITE"] == "1"


def test_canonical_paths_allow_macos_var_style_ancestors(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    target = real / "file.txt"
    target.write_text("ok\n", encoding="utf-8")
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    assert canonical_input(alias / "file.txt") == target.resolve()
    out = canonical_output(alias / "new.txt")
    assert out.parent.resolve() == real.resolve()
    assert out.name == "new.txt"


def test_read_git_works_on_repo_root() -> None:
    root = Path(__file__).resolve().parents[2]
    head = read_git(root, "rev-parse", "HEAD").stdout.decode().strip()
    assert len(head) in {40, 64}
