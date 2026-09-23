"""Deterministic accounting tests; none of these fixtures are model reviews."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/coverage_inventory.py"
spec = importlib.util.spec_from_file_location("roadmap_coverage_inventory", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def git(repo, *args, data=None):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.invalid", GIT_COMMITTER_NAME="Test",
               GIT_COMMITTER_EMAIL="test@example.invalid", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return subprocess.run(["git", "-C", str(repo), *args], input=data, capture_output=True, env=env, check=True).stdout


@pytest.fixture
def checkout(tmp_path):
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "src").mkdir()
    (repo / "src/main.py").write_text("print('fixture')\n")
    (repo / "README.md").write_text("# Fixture\n")
    (repo / ".env").write_text("PRIVATE_CONTENT_MUST_NOT_APPEAR_IN_INVENTORY\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "fixture")
    commit = git(repo, "rev-parse", "HEAD").decode().strip()
    return repo, commit


@pytest.fixture
def inv(checkout):
    repo, commit = checkout
    return m.from_git(repo, "example/fixture", commit)


def reviewed(inv):
    data = m.review_template(inv)
    for row in data["rows"]:
        row.pop("reason")
        row.update(status="INSPECTED", reviewer="synthetic-fixture", reviewed_at="2026-01-01T00:00:00Z",
                   summary="Synthetic review record, not an actual model assessment", evidence_ref="fixture:001")
    return data


def test_real_git_tree_hash_and_no_contents(inv, checkout):
    assert m.validate_inventory(inv) == inv
    assert inv["tree_sha"] == git(checkout[0], "rev-parse", checkout[1] + "^{tree}").decode().strip()
    assert {r["path"] for r in inv["entries"]} == {".env", "README.md", "src", "src/main.py"}
    assert "PRIVATE_CONTENT" not in m.canonical(inv).decode()
    assert inv["commit_binding"] == "local_git_object"


@pytest.mark.parametrize("removed", ["README.md", "src/main.py", "src", ".env"])
def test_omitted_entries_never_prove_complete(inv, removed):
    entries = [r for r in inv["entries"] if r["path"] != removed]
    with pytest.raises(m.InventoryError):
        m.verify_tree(entries, inv["tree_sha"], "sha1")


def test_entire_subtree_omission_rejected(inv):
    with pytest.raises(m.InventoryError):
        m.verify_tree([r for r in inv["entries"] if not r["path"].startswith("src")], inv["tree_sha"], "sha1")


@pytest.mark.parametrize("field,value", [("mode", "100755"), ("sha", "a" * 40), ("path", "renamed")])
def test_changed_tree_entry_rejected(inv, field, value):
    rows = copy.deepcopy(inv["entries"])
    rows[0][field] = value
    with pytest.raises(m.InventoryError):
        m.verify_tree(rows, inv["tree_sha"], "sha1")


@pytest.mark.parametrize("field,value", [("mode", "100600"), ("type", "tree"), ("sha", "abcdef0"), ("path", "../x"), ("path", "/x"), ("path", "x//a"), ("path", ".git/a"), ("path", "x/./a")])
def test_invalid_entry_rejected(inv, field, value):
    rows = copy.deepcopy(inv["entries"])
    rows[0][field] = value
    with pytest.raises(m.InventoryError):
        m.verify_tree(rows, inv["tree_sha"], "sha1")


def test_duplicate_entry_rejected(inv):
    with pytest.raises(m.InventoryError):
        m.verify_tree(inv["entries"] + [inv["entries"][0]], inv["tree_sha"], "sha1")


def test_git_tree_sort_order_and_odd_names(checkout):
    repo, _ = checkout
    for name in ["a", "a.c", "a0", "a-", "zażółć", "with\ttab", "with\nnewline", "literal\\backslash"]:
        (repo / name).write_text(name)
    (repo / "a-dir").mkdir()
    (repo / "a-dir/child").write_text("x")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "odd paths")
    result = m.from_git(repo, "example/fixture", git(repo, "rev-parse", "HEAD").decode().strip())
    assert m.validate_inventory(result) == result
    assert b"with\\nnewline" in m.canonical(result)


def test_uncommitted_changes_are_not_confused_with_commit(checkout, inv):
    repo, commit = checkout
    (repo / "src/main.py").unlink()
    (repo / "new.py").write_text("uncommitted")
    status = git(repo, "status", "--porcelain")
    result = m.from_git(repo, "example/fixture", commit)
    assert result["entries"] == inv["entries"]
    assert git(repo, "status", "--porcelain") == status


def test_ignore_poisoned_git_environment(monkeypatch, checkout, inv, tmp_path):
    other = tmp_path / "different-repo"
    other.mkdir()
    git(other, "init", "-q")
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    result = m.from_git(checkout[0], "example/fixture", checkout[1])
    assert result["tree_sha"] == inv["tree_sha"]


def test_no_filters_or_hooks_run(checkout, tmp_path):
    repo, _ = checkout
    sentinel = tmp_path / "should-not-exist"
    hook = repo / ".git/hooks/post-checkout"
    hook.write_text("#!/bin/sh\ntouch " + str(sentinel) + "\n")
    hook.chmod(0o755)
    git(repo, "config", "filter.fixture.smudge", "touch " + str(sentinel))
    (repo / ".gitattributes").write_text("*.py filter=fixture\n")
    git(repo, "add", ".gitattributes")
    git(repo, "commit", "-qm", "attributes")
    m.from_git(repo, "example/fixture", git(repo, "rev-parse", "HEAD").decode().strip())
    assert not sentinel.exists()


@pytest.mark.parametrize("pin", ["HEAD", "main", "abc1234", "--help", "x" * 40])
def test_only_full_commit_pins(checkout, pin):
    with pytest.raises(m.InventoryError):
        m.from_git(checkout[0], "example/fixture", pin)


def test_tree_is_not_a_commit(checkout, inv):
    with pytest.raises(m.InventoryError):
        m.from_git(checkout[0], "example/fixture", inv["tree_sha"])


def test_git_binary_absent(monkeypatch, checkout):
    monkeypatch.setenv("PATH", "/no-such-tools")
    with pytest.raises(m.InventoryError):
        m.from_git(checkout[0], "example/fixture", checkout[1])


def test_submodule_is_always_unexpanded(checkout):
    repo, commit = checkout
    git(repo, "update-index", "--add", "--cacheinfo", "160000," + commit + ",submodule")
    git(repo, "commit", "-qm", "gitlink")
    inv = m.from_git(repo, "example/fixture", git(repo, "rev-parse", "HEAD").decode().strip())
    ledger = m.review_template(inv)
    assert m.audit(inv, ledger)["submodule_paths"] == ["submodule"]
    fake = reviewed(inv)
    with pytest.raises(m.InventoryError):
        m.audit(inv, fake)


def test_symlink_target_not_opened(checkout, tmp_path):
    repo, _ = checkout
    secret = tmp_path / "not-in-repo"
    secret.write_text("DO_NOT_READ_TARGET_CONTENT")
    (repo / "link").symlink_to(secret)
    git(repo, "add", "link")
    git(repo, "commit", "-qm", "symlink")
    inv = m.from_git(repo, "example/fixture", git(repo, "rev-parse", "HEAD").decode().strip())
    result = m.audit(inv, reviewed(inv))
    assert result["symlink_paths"] == ["link"]
    assert "DO_NOT_READ_TARGET_CONTENT" not in m.canonical(inv).decode()
    assert "not followed" in result["note"]


def test_sha256_repository(tmp_path):
    repo = tmp_path / "sha256-repo"
    repo.mkdir()
    git(repo, "init", "-q", "--object-format=sha256")
    (repo / "a.txt").write_text("test")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "sha256")
    inv = m.from_git(repo, "example/sha256", git(repo, "rev-parse", "HEAD").decode().strip())
    assert inv["object_format"] == "sha256"
    assert len(inv["tree_sha"]) == 64
    m.validate_inventory(inv)


def test_empty_tree_not_successful_review(tmp_path):
    repo = tmp_path / "empty"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "commit", "--allow-empty", "-qm", "empty")
    inv = m.from_git(repo, "example/empty", git(repo, "rev-parse", "HEAD").decode().strip())
    report = m.audit(inv, m.review_template(inv))
    assert report["file_count"] == 0
    assert report["result"] == "EMPTY_SCOPE"


def test_github_import_checks_full_tree(inv):
    data = {"sha": inv["tree_sha"], "truncated": False, "tree": inv["entries"]}
    result = m.from_github(data, repository=inv["repository"], commit=inv["commit_sha"], expected_tree=inv["tree_sha"])
    assert result["entries"] == inv["entries"]
    assert result["commit_binding"] == "asserted_connector_pin"


@pytest.mark.parametrize("flag", [True, "false", 0, None])
def test_github_truncated_must_be_false(inv, flag):
    data = {"sha": inv["tree_sha"], "truncated": flag, "tree": inv["entries"]}
    with pytest.raises(m.InventoryError):
        m.from_github(data, repository=inv["repository"], commit=inv["commit_sha"], expected_tree=inv["tree_sha"])


def test_github_lied_about_truncation(inv):
    data = {"sha": inv["tree_sha"], "truncated": False, "tree": inv["entries"][:-1]}
    with pytest.raises(m.InventoryError):
        m.from_github(data, repository=inv["repository"], commit=inv["commit_sha"], expected_tree=inv["tree_sha"])


def test_template_is_never_passing(inv):
    result = m.audit(inv, m.review_template(inv))
    assert result["result"] == "EXHAUSTIVE_NOT_PROVEN"
    assert result["counts"] == {"UNAVAILABLE": 3}
    assert result["accounted_count"] == 3
    assert result["runtime_verification"] == "not_performed"


def test_complete_records_are_not_runtime_verification(inv):
    result = m.audit(inv, reviewed(inv), expected=inv["inventory_sha256"])
    assert result["result"] == "INSPECTION_RECORDS_COMPLETE"
    assert result["anchor"] == "matched_external_pin"
    assert result["review_authentication"] == "not_performed"
    assert result["runtime_verification"] == "not_performed"


def test_missing_review_row_exposed(inv):
    ledger = reviewed(inv)
    missing = ledger["rows"].pop()["path"]
    result = m.audit(inv, ledger)
    assert result["unaccounted_paths"] == [missing]
    assert result["result"] == "EXHAUSTIVE_NOT_PROVEN"


@pytest.mark.parametrize("key", ["summary", "reviewer", "evidence_ref", "reviewed_at"])
def test_inspection_requires_full_record(inv, key):
    ledger = reviewed(inv)
    ledger["rows"][0].pop(key)
    with pytest.raises(m.InventoryError):
        m.audit(inv, ledger)


@pytest.mark.parametrize("change", [{"sha": "f" * 40}, {"status": "COMPLETE"}, {"path": "ghost"}, {"reviewed_at": "2999-01-01T00:00:00Z"}, {"reviewed_at": "2026-01-01"}])
def test_invalid_review_rows(inv, change):
    ledger = reviewed(inv)
    ledger["rows"][0].update(change)
    with pytest.raises(m.InventoryError):
        m.audit(inv, ledger)


def test_duplicate_review_rows(inv):
    ledger = reviewed(inv)
    ledger["rows"].append(ledger["rows"][0])
    with pytest.raises(m.InventoryError):
        m.audit(inv, ledger)


def test_exclusions_disclosed_not_complete_inspection(inv):
    ledger = reviewed(inv)
    ledger["rows"][0] = {"path": ledger["rows"][0]["path"], "sha": ledger["rows"][0]["sha"],
                         "status": "EXCLUDED_GENERATED", "reason": "fixture only", "scope_basis": "approved-fixture-policy", "evidence_ref": "fixture:002"}
    result = m.audit(inv, ledger)
    assert result["result"] == "ACCOUNTED_WITH_EXCLUSIONS"
    assert len(result["excluded_paths"]) == 1


@pytest.mark.parametrize("status", ["EXCLUDED_GENERATED", "EXCLUDED_VENDOR"])
def test_exclusion_without_scope_basis_invalid(inv, status):
    ledger = m.review_template(inv)
    ledger["rows"][0].update(status=status, evidence_ref="example")
    with pytest.raises(m.InventoryError):
        m.audit(inv, ledger)


def test_external_hash_rejects_rewritten_inventory(inv):
    modified = copy.deepcopy(inv)
    modified["repository"] = "example/different"
    modified["inventory_sha256"] = m.digest({k: v for k, v in modified.items() if k != "inventory_sha256"})
    with pytest.raises(m.InventoryError):
        m.validate_inventory(modified, inv["inventory_sha256"])


def test_empty_ledger_accounts_for_nothing(inv):
    ledger = m.review_template(inv)
    ledger["rows"] = []
    result = m.audit(inv, ledger)
    assert len(result["unaccounted_paths"]) == 3
    assert result["result"] == "EXHAUSTIVE_NOT_PROVEN"


def test_delta_handles_new_removed_mode_changes(checkout, inv):
    repo, _ = checkout
    (repo / "README.md").unlink()
    (repo / "new.txt").write_text("new")
    git(repo, "update-index", "--chmod=+x", "src/main.py")
    git(repo, "add", "README.md", "new.txt")
    git(repo, "commit", "-qm", "changed")
    newer = m.from_git(repo, "example/fixture", git(repo, "rev-parse", "HEAD").decode().strip())
    report = m.delta(inv, newer)
    assert report["added_paths"] == ["new.txt"]
    assert report["removed_paths"] == ["README.md"]
    assert report["modified_paths"] == ["src/main.py"]
    assert report["unchanged_content_paths"] == [".env"]
    assert report["review_required_paths"] == ["new.txt", "src/main.py"]
    with pytest.raises(m.InventoryError):
        m.audit(newer, reviewed(inv))


def test_delta_does_not_guess_renames(checkout, inv):
    repo, _ = checkout
    git(repo, "mv", "README.md", "renamed.md")
    git(repo, "commit", "-qm", "rename")
    newer = m.from_git(repo, "example/fixture", git(repo, "rev-parse", "HEAD").decode().strip())
    diff = m.delta(inv, newer)
    assert diff["removed_paths"] == ["README.md"]
    assert diff["added_paths"] == ["renamed.md"]


def test_delta_rejects_cross_repository(inv):
    b = m.make_inventory(inv["entries"], repository="another/repo", commit=inv["commit_sha"], tree=inv["tree_sha"])
    with pytest.raises(m.InventoryError):
        m.delta(inv, b)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}', b'{', b'"\\ud800"'])
def test_strict_json(raw):
    with pytest.raises(m.InventoryError):
        m.loads(raw)


def test_cli_end_to_end_and_no_overwrite(checkout, tmp_path):
    repo, commit = checkout
    def run(*args):
        return subprocess.run([sys.executable, "-S", str(SCRIPT), *map(str, args)], capture_output=True)
    inventory = tmp_path / "inventory.json"
    ledger = tmp_path / "ledger.json"
    proc = run("inventory", "--repo", repo, "--repository", "example/fixture", "--commit", commit, "--output", inventory)
    assert proc.returncode == 0, proc.stderr
    original = inventory.read_bytes()
    assert run("template", "--inventory", inventory, "--output", ledger).returncode == 0
    assert run("audit", "--inventory", inventory, "--ledger", ledger).returncode == 1
    assert run("inventory", "--repo", repo, "--repository", "example/fixture", "--commit", commit, "--output", inventory).returncode == 2
    assert inventory.read_bytes() == original
    ledger.write_text(json.dumps(reviewed(m.read_json(inventory))))
    assert run("audit", "--inventory", inventory, "--ledger", ledger, "--require-inspected").returncode == 0
    ledger.write_text('{}')
    assert run("audit", "--inventory", inventory, "--ledger", ledger).returncode == 2


def test_output_allows_symlink_parent(tmp_path):
    """Parent symlinks must not block output (macOS /var-style ancestry)."""
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    m.output_json({"x": 1}, alias / "ok.json")
    assert (actual / "ok.json").is_file()


def test_output_rejects_symlink_leaf(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    target = actual / "ok.json"
    target.write_text("{}")
    link = tmp_path / "alias.json"
    link.symlink_to(target)
    with pytest.raises(m.InventoryError):
        m.output_json({"x": 1}, link)


def test_future_inventory_timestamp_rejected(inv):
    with pytest.raises(m.InventoryError):
        m.make_inventory(inv["entries"], repository=inv["repository"], commit=inv["commit_sha"], tree=inv["tree_sha"], observed_at="2999-01-01T00:00:00Z")


@pytest.mark.parametrize("algorithm", [None, [], {}, 1, "sha512"])
def test_invalid_algorithm_has_documented_error(inv, algorithm):
    with pytest.raises(m.InventoryError):
        m.verify_tree(inv["entries"], inv["tree_sha"], algorithm)


def test_empty_nested_tree_is_included(checkout):
    repo, _ = checkout
    empty_tree = git(repo, "mktree", data=b"").decode().strip()
    tree = git(repo, "mktree", data=("040000 tree " + empty_tree + "\tempty-dir\n").encode()).decode().strip()
    commit = git(repo, "commit-tree", tree, "-m", "empty subtree").decode().strip()
    result = m.from_git(repo, "example/fixture", commit)
    assert result["entries"] == [{"path": "empty-dir", "mode": "040000", "type": "tree", "sha": empty_tree}]
    with pytest.raises(m.InventoryError):
        m.verify_tree([], tree, "sha1")


def test_out_of_order_inventory_rejected(inv):
    inv["entries"].reverse()
    inv["inventory_sha256"] = m.digest({k: v for k, v in inv.items() if k != "inventory_sha256"})
    with pytest.raises(m.InventoryError):
        m.validate_inventory(inv)


def test_hash_mismatch_rejected(inv):
    inv["inventory_sha256"] = "f" * 64
    with pytest.raises(m.InventoryError):
        m.validate_inventory(inv)


def test_symlink_json_input_is_rejected(tmp_path):
    path = tmp_path / "source.json"
    path.write_text('{}')
    link = tmp_path / "alias.json"
    link.symlink_to(path)
    with pytest.raises(m.InventoryError):
        m.read_json(link)


def test_byte_budget(monkeypatch, tmp_path):
    path = tmp_path / "huge.json"
    path.write_text('"' + 'a' * 50 + '"')
    monkeypatch.setattr(m, "MAX_BYTES", 10)
    with pytest.raises(m.InventoryError):
        m.read_json(path)


def test_require_inspected_rejects_exclusions_cli(inv, tmp_path):
    ledger = reviewed(inv)
    ledger["rows"][0].update(status="EXCLUDED_VENDOR", reason="fixture", scope_basis="fixture policy")
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(inv))
    b.write_text(json.dumps(ledger))
    args = [sys.executable, "-S", str(SCRIPT), "audit", "--inventory", str(a), "--ledger", str(b)]
    assert subprocess.run(args, capture_output=True).returncode == 0
    assert subprocess.run(args + ["--require-inspected"], capture_output=True).returncode == 1


def test_input_is_not_mutated_by_apis(inv):
    ledger = reviewed(inv)
    saved = copy.deepcopy((inv, ledger))
    m.audit(inv, ledger)
    m.delta(inv, inv)
    m.review_template(inv)
    assert (inv, ledger) == saved
