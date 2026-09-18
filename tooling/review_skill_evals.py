#!/usr/bin/env python3
"""Compare explicitly reviewed, matched skill runs; never run or impersonate a model.

Inputs are supplied records, not authenticated execution traces. A statistical
summary does not approve a release and cannot establish market-leading quality.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from audit_contracts import MAX_JSON, HEX64, array, ids, index, loads, obj, require, text

CONDITIONS = ("no_skill", "current", "candidate")
EMPTY_INSTRUCTIONS = hashlib.sha256(b"{}").hexdigest()


def sha(value: Any, where: str) -> str:
    require(isinstance(value, str) and HEX64.fullmatch(value), f"{where}: invalid SHA-256")
    return value


def average(values: list[int]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def experiment_fingerprint(experiment: dict) -> str:
    return hashlib.sha256(json.dumps(experiment, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _compare(data: dict, expected_experiment_sha256: str | None = None) -> dict:
    obj(data, {"schema", "experiment", "runs", "reviews"}, set(), "comparison")
    require(data["schema"] == "cometweb.skill-comparison/v1", "unknown comparison schema")
    exp = obj(data["experiment"], {"id", "suite_sha256", "instruction_sha256", "host", "model",
                                  "capabilities", "dimensions", "cases", "repetitions"}, {"case_rubrics"}, "experiment")
    text(exp["id"], "experiment id", 128)
    text(exp["host"], "host", 128)
    text(exp["model"], "model", 128)
    sha(exp["suite_sha256"], "suite")
    require(isinstance(exp["capabilities"], dict) and type(exp["capabilities"].get("tools")) is bool,
            "explicit tool capability required")
    pinned = obj(exp["instruction_sha256"], set(CONDITIONS), set(), "instruction hashes")
    for name in CONDITIONS:
        sha(pinned[name], "instruction fingerprint")
    require(pinned["no_skill"] == EMPTY_INSTRUCTIONS, "baseline is not an empty skill instruction bundle")
    require(pinned["current"] != pinned["candidate"], "current and candidate are identical")
    dimensions = ids(exp["dimensions"], "dimensions", True)
    require(len(dimensions) <= 12, "too many scoring dimensions")
    cases = index(exp["cases"], "cases", True)
    require(len(cases) <= 500, "case budget exceeded")
    for case in cases.values():
        obj(case, {"id", "fixture_sha256"}, set(), "case")
        sha(case["fixture_sha256"], "fixture fingerprint")
    if "case_rubrics" in exp:
        obj(exp["case_rubrics"], set(cases), set(), "case rubrics")
        for criteria in exp["case_rubrics"].values():
            array(criteria, "rubric", True)
            require(len(criteria) <= 100, "rubric is oversized")
            for criterion in criteria:
                text(criterion, "rubric criterion")
    repetitions = exp["repetitions"]
    require(type(repetitions) is int and 1 <= repetitions <= 20, "invalid repetition count")
    expected = {(c, r, condition) for c in cases for r in range(repetitions) for condition in CONDITIONS}
    require(len(expected) <= 5000, "experiment exceeds bounded record capacity")
    fingerprint = experiment_fingerprint(exp)
    if expected_experiment_sha256 is not None:
        require(sha(expected_experiment_sha256, "experiment pin") == fingerprint, "reviewed experiment changed")
    runs = index(data["runs"], "runs")
    keys, responses = {}, set()
    for run_id, run in runs.items():
        obj(run, {"id", "case_id", "repetition", "condition", "execution_kind", "host", "model",
                  "capabilities", "response_id", "fixture_sha256", "instructions_sha256", "output",
                  "output_sha256", "tokens", "duration_ms"}, set(), "run")
        require(type(run["repetition"]) is int, "repetition must be an integer")
        key = (run["case_id"], run["repetition"], run["condition"])
        require(key in expected and key not in keys, "duplicate or unexpected experiment cell")
        keys[key] = run_id
        require(run["execution_kind"] == "model", "synthetic/mock runs are not model evidence")
        require(run["host"] == exp["host"] and run["model"] == exp["model"]
                and run["capabilities"] == exp["capabilities"], "unmatched model/host/capabilities")
        require(run["fixture_sha256"] == cases[run["case_id"]]["fixture_sha256"]
                and run["instructions_sha256"] == pinned[run["condition"]], "unmatched input fingerprints")
        text(run["response_id"], "response id", 256)
        require(run["response_id"] not in responses, "response ID reused across independent runs")
        responses.add(run["response_id"])
        text(run["output"], "output", 100000)
        require(sha(run["output_sha256"], "output fingerprint") == hashlib.sha256(run["output"].encode()).hexdigest(),
                "run output was changed after fingerprinting")
        for field in ("tokens", "duration_ms"):
            require(run[field] is None or (type(run[field]) is int and run[field] >= 0),
                    "unknown cost is null; known cost must be a nonnegative integer")
    reviews = {}
    for row in array(data["reviews"], "reviews"):
        obj(row, {"run_id", "output_sha256", "reviewer", "review_kind", "scores", "evidence", "flags"}, set(), "review")
        run_id = row["run_id"]
        require(run_id in runs and run_id not in reviews, "unknown or duplicate reviewed run")
        require(row["output_sha256"] == runs[run_id]["output_sha256"], "review does not match the actual output")
        text(row["reviewer"], "reviewer", 128)
        require(row["review_kind"] in {"human", "model_assisted"}, "review kind must not impersonate a human")
        obj(row["scores"], set(dimensions), set(), "scores")
        for score in row["scores"].values():
            require(type(score) is int and 0 <= score <= 4, "scores must be integers 0..4")
        obj(row["evidence"], set(dimensions), set(), "review evidence")
        for dimension in dimensions:
            text(row["evidence"][dimension], "review evidence", 2000)
        ids(row["flags"], "flags")
        reviews[run_id] = row
    missing_cells = sorted(expected - keys.keys())
    missing_reviews = sorted(runs.keys() - reviews.keys())
    base = {
        "schema": "cometweb.skill-comparison-result/v1", "experiment_id": exp["id"],
        "experiment_sha256": fingerprint,
        "experiment_pin": "matched" if expected_experiment_sha256 is not None else "not_requested",
        "provenance": "supplied_records_not_authenticated_executions",
        "planned_runs": len(expected), "recorded_runs": len(runs), "reviewed_runs": len(reviews),
        "missing_cells": [list(x) for x in missing_cells], "missing_reviews": missing_reviews,
        "review_kinds": dict(Counter(r["review_kind"] for r in reviews.values())),
        "runtime_installation_acceptance": "not_assessed", "release_authorization": "not_provided",
        "statistical_inference": "descriptive_only_no_independence_or_significance_claim",
    }
    if missing_cells or missing_reviews:
        return {**base, "comparison_status": "incomplete", "quality_verdict": "not_assessed", "aggregates": None,
                "paired_deltas": None, "candidate_regressions": None}
    aggregates = {}
    for condition in CONDITIONS:
        selected = [run for run in runs.values() if run["condition"] == condition]
        aggregates[condition] = {
            "runs": len(selected),
            "mean_scores": {d: average([reviews[r["id"]]["scores"][d] for r in selected]) for d in dimensions},
            "costs": {field: {"mean": average([r[field] for r in selected]) if all(r[field] is not None for r in selected) else None,
                               "missing": sum(r[field] is None for r in selected)} for field in ("tokens", "duration_ms")},
            "flagged_runs": sum(bool(reviews[r["id"]]["flags"]) for r in selected),
        }
    deltas, regressions = [], []
    for case_id in cases:
        for repetition in range(repetitions):
            candidate = keys[(case_id, repetition, "candidate")]
            for baseline in ("no_skill", "current"):
                other = keys[(case_id, repetition, baseline)]
                difference = {d: reviews[candidate]["scores"][d] - reviews[other]["scores"][d] for d in dimensions}
                deltas.append({"case_id": case_id, "repetition": repetition, "versus": baseline, "scores": difference})
                if any(value < 0 for value in difference.values()):
                    regressions.append({"case_id": case_id, "repetition": repetition, "versus": baseline,
                                        "dimensions": [d for d, value in difference.items() if value < 0]})
            if reviews[candidate]["flags"]:
                regressions.append({"case_id": case_id, "repetition": repetition, "flags": reviews[candidate]["flags"]})
    return {**base, "comparison_status": "reviewed", "quality_verdict": "human_decision_required",
            "aggregates": aggregates, "paired_deltas": deltas, "candidate_regressions": regressions}


def compare(data: dict, expected_experiment_sha256: str | None = None) -> dict:
    try:
        return _compare(data, expected_experiment_sha256)
    except (TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise ValueError("malformed comparison field") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison", type=Path)
    parser.add_argument("--reviews", type=Path, help="Separate completed review file; original packet stays unchanged")
    parser.add_argument("--expected-experiment-sha256", help="Externally retained reviewed experiment pin")
    args = parser.parse_args(argv)
    try:
        with args.comparison.open("rb") as handle:
            data = loads(handle.read(MAX_JSON + 1))
        if args.reviews is not None:
            with args.reviews.open("rb") as handle:
                review_file = loads(handle.read(MAX_JSON + 1))
            obj(review_file, {"schema", "reviews"}, set(), "review file")
            require(review_file["schema"] == "cometweb.skill-reviews/v1" and data.get("reviews") == [],
                    "review file must fill an unreviewed packet without overwriting previous judgments")
            data["reviews"] = review_file["reviews"]
        result = compare(data, args.expected_experiment_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0 if result["comparison_status"] == "reviewed" else 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({"comparison_status": "invalid", "quality_verdict": "not_assessed"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
