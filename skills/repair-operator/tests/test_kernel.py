from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


KERNEL_PATH = Path(__file__).parents[1] / "scripts" / "kernel.py"
KERNEL_SPEC = importlib.util.spec_from_file_location("repair_operator_kernel", KERNEL_PATH)
assert KERNEL_SPEC is not None and KERNEL_SPEC.loader is not None
kernel = importlib.util.module_from_spec(KERNEL_SPEC)
KERNEL_SPEC.loader.exec_module(kernel)


def test_reopened_repair_rejects_ghost_origin() -> None:
    result = kernel.validate(
        {
            "items": [
                {
                    "finding_ids": ["f1"],
                    "repair_class": "PATCH",
                    "repair_id": "r1",
                    "reopen_of": "ghost",
                    "status": "REOPENED",
                }
            ]
        }
    )

    assert result["status"] == "INVALID"
    assert result["errors"] == ["0:reopened-with-missing-origin:ghost"]


def test_reopened_repair_accepts_existing_origin() -> None:
    result = kernel.validate(
        {
            "items": [
                {
                    "finding_ids": ["f1"],
                    "repair_class": "PATCH",
                    "repair_id": "r1",
                    "status": "OPEN",
                },
                {
                    "finding_ids": ["f2"],
                    "repair_class": "PATCH",
                    "repair_id": "r2",
                    "reopen_of": "r1",
                    "status": "REOPENED",
                },
            ]
        }
    )

    assert result["status"] == "VALID"
    assert result["open"] == 2
    assert result["errors"] == []


@pytest.mark.parametrize("value", [[], {}, None, 0])
@pytest.mark.parametrize("field,error", [
    ("status", "status"), ("repair_class", "repair-class"),
    ("patch_risk", "patch-risk"), ("effort_band", "effort-band"),
    ("blast_radius", "blast-radius"), ("reversibility", "reversibility"),
])
def test_malformed_item_enums_fail_closed(field, error, value):
    item = {
        "repair_id": "r1", "finding_ids": ["f1"], "status": "OPEN",
        "repair_class": "PATCH", "patch_risk": "LOW", "effort_band": "S",
        "blast_radius": "LOCAL", "reversibility": "EASY",
    }
    item[field] = value
    result = kernel.validate({"portfolio_mode": True, "items": [item]})
    assert result["status"] == "INVALID"
    assert result["errors"] == [f"0:{error}"]
