import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "repo_snapshot.py"
spec = importlib.util.spec_from_file_location("repo_snapshot", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_missing_repo_does_not_leak_path(tmp_path):
    result = module.snapshot(tmp_path, "products/insight")
    assert result == {"repo": "products/insight", "status": "missing"}
    assert "path" not in result


def test_include_paths_is_explicit(tmp_path):
    result = module.snapshot(tmp_path, "products/insight", include_paths=True)
    assert result["status"] == "missing"
    assert result["path"].endswith("products/insight")
