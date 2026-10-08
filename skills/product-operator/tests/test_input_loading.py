from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "product_operator_kernel_input_loading",
    ROOT / "scripts" / "operator_kernel.py",
)
kernel = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(kernel)


def test_missing_json_path_is_not_parsed_as_inline_json(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        kernel.load_json_arg(str(tmp_path / "ledger.json"))


def test_inline_json_remains_supported() -> None:
    assert kernel.load_json_arg('{"items": []}') == {"items": []}


@pytest.mark.parametrize("payload", [
    {"url": "https://example.org"},
    {"path": "docs/guide.md"},
    [{"url": "https://example.org"}],
    {"long_text": "docs/" * 100},
])
def test_inline_json_content_is_not_a_file_path(payload) -> None:
    assert kernel.load_json_arg(" \n" + json.dumps(payload)) == payload


@pytest.mark.parametrize("prefix", ["", "@"])
def test_file_json_still_loads(tmp_path, prefix) -> None:
    path = tmp_path / "input.json"
    path.write_text('{"url": "https://example.org"}')
    assert kernel.load_json_arg(prefix + str(path)) == {"url": "https://example.org"}


def test_invalid_inline_json_remains_a_json_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        kernel.load_json_arg('{"url": "https://example.org",}')


def test_readiness_cli_accepts_inline_json_with_url() -> None:
    result = subprocess.run([sys.executable, str(ROOT / "scripts/operator_kernel.py"),
                             "readiness", "--input-json", '{"url": "https://example.org"}'],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert isinstance(json.loads(result.stdout), dict)
