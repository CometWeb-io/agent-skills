from __future__ import annotations

import importlib.util
from pathlib import Path

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
