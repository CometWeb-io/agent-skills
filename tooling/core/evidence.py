"""Evidence kind taxonomy for release and validation metadata.

These labels keep static/unit/deterministic checks distinct from model and host
runtime acceptance so a green harness is never confused with verified skill quality.
"""
from __future__ import annotations

from enum import Enum


class EvidenceKind(str, Enum):
    STATIC = "static_validation"
    UNIT = "unit_test"
    DETERMINISTIC_BEHAVIOR = "deterministic_behavior"
    MODEL_EVAL = "model_eval"
    HOST_RUNTIME = "host_runtime"


DEFAULT_RELEASE_EVIDENCE = {
    EvidenceKind.STATIC.value: "passed",
    EvidenceKind.UNIT.value: "passed",
    EvidenceKind.DETERMINISTIC_BEHAVIOR.value: "passed",
    EvidenceKind.MODEL_EVAL.value: "not_run",
    EvidenceKind.HOST_RUNTIME.value: "not_assessed",
}
