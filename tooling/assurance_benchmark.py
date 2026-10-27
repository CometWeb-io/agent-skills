"""Validate the original assurance cohort; emit source-only, output-free review packets.

Structural validation does not establish oracle truth, task diversity or human independence.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

DEFAULT_BUNDLE = Path(__file__).resolve().parents[1] / "evals" / "assurance" / "v1"
WORKFLOWS = {"web", "release", "agency"}
SPLITS = {"development", "holdout"}
CASE_TYPES = {"positive", "negative", "adversarial"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def _read_bundle(folder: Path) -> tuple[dict, dict]:
    # Fixed filenames: a manifest cannot redirect the reader outside the bundle.
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    corpus = json.loads((folder / "cases.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not isinstance(corpus, dict):
        raise ValueError("manifest and corpus must be JSON objects")
    return manifest, corpus


def validate_bundle(folder: Path = DEFAULT_BUNDLE) -> list[str]:
    """Return structural errors without disclosing source snippets or oracle contents."""
    try:
        manifest, corpus = _read_bundle(folder)
    except (OSError, ValueError) as exc:
        return [f"bundle unreadable: {exc}"]
    errors: list[str] = []

    def require(condition: object, message: str) -> None:
        if not condition:
            errors.append(message)

    require(
        type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1,
        "manifest schema_version must be 1",
    )
    require(
        type(corpus.get("schema_version")) is int and corpus["schema_version"] == 1, "corpus schema_version must be 1"
    )
    require(
        manifest.get("benchmark_id") == corpus.get("benchmark_id") == "assurance-original-v1", "benchmark_id mismatch"
    )
    require(manifest.get("corpus_file") == "cases.json", "corpus_file must be cases.json")
    require(manifest.get("corpus_sha256") == canonical_sha256(corpus), "corpus hash mismatch")
    require(bool(re.fullmatch("[0-9a-f]{40}", str(manifest.get("base_sha", "")))), "invalid base_sha")
    require(manifest.get("freeze_stage") == "before_any_candidate_execution", "invalid freeze_stage")
    try:
        frozen = datetime.fromisoformat(manifest["frozen_at"])
        require(frozen.tzinfo is not None, "frozen_at requires a timezone")
    except (KeyError, ValueError, TypeError):
        errors.append("invalid frozen_at")
    for key, expected in (
        ("human_review", "not_run"),
        ("independent_validation", "not_established"),
        ("candidate_executions", "not_run"),
    ):
        require(manifest.get(key) == expected, f"manifest {key} must remain {expected}")
    authoring = manifest.get("authoring", {})
    if not isinstance(authoring, dict):
        errors.append("authoring must be an object")
        authoring = {}
    for key, expected in {
        "author_type": "LLM",
        "separate_candidate_author_context": True,
        "candidate_material_read": False,
        "prior_model_outputs_read": False,
        "existing_holdouts_read": False,
        "human_review": "not_run",
        "independent_validation": "not_established",
    }.items():
        require(
            type(authoring.get(key)) is type(expected) and authoring.get(key) == expected, f"authoring {key} mismatch"
        )
    independence = manifest.get("independence", {})
    require(
        isinstance(independence, dict)
        and independence.get("statistical_independence") == "not_established"
        and independence.get("external_expert_review") == "not_run"
        and bool(independence.get("correlation")),
        "independence limitations missing",
    )
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not all(isinstance(c, dict) for c in cases):
        return errors + ["cases must be an array of objects"]
    require(len(cases) >= 100, "at least 100 cases required")
    seen_ids: set[str] = set()
    seen_tasks: set[str] = set()
    families: dict[str, set] = defaultdict(set)
    clusters: dict[str, set] = defaultdict(set)
    cluster_workflows: dict[str, set] = defaultdict(set)
    cluster_counts: Counter = Counter()
    workflow_counts: Counter = Counter()
    type_counts: Counter = Counter()
    split_counts: Counter = Counter()
    workflow_types: dict[str, set] = defaultdict(set)
    index = []
    for position, case in enumerate(cases):
        label = f"case[{position}]"
        identifiers = {key: case.get(key) for key in ("case_id", "family_id", "cluster_id")}
        if not all(isinstance(v, str) and ID_PATTERN.fullmatch(v) for v in identifiers.values()):
            errors.append(f"{label}: invalid case/family/cluster ID")
            continue
        cid, family, cluster = (identifiers[key] for key in ("case_id", "family_id", "cluster_id"))
        require(cid not in seen_ids, f"{label}: duplicate case_id")
        seen_ids.add(cid)
        workflow, split, kind = (case.get(key) for key in ("workflow", "split", "case_type"))
        if (
            not all(isinstance(v, str) for v in (workflow, split, kind))
            or workflow not in WORKFLOWS
            or split not in SPLITS
            or kind not in CASE_TYPES
        ):
            errors.append(f"{label}: invalid workflow, split or case_type")
            continue
        require(
            all(value.startswith(workflow + "-") for value in identifiers.values()),
            f"{label}: IDs must be workflow-prefixed",
        )
        require(case.get("language") == "en", f"{label}: unsupported cohort language")
        require(family == cluster, f"{label}: v1 family must equal cluster")
        families[family].add(split)
        clusters[cluster].add(split)
        cluster_workflows[cluster].add(workflow)
        cluster_counts[cluster] += 1
        workflow_counts[workflow] += 1
        type_counts[kind] += 1
        split_counts[split] += 1
        workflow_types[workflow].add(kind)
        task, oracle, provenance = (case.get(key) for key in ("task", "oracle", "provenance"))
        if not all(isinstance(obj, dict) for obj in (task, oracle, provenance)):
            errors.append(f"{label}: task/oracle/provenance must be objects")
            continue
        require(
            set(task) == {"request", "allowed_actions", "execution_mode", "sources"}, f"{label}: unexpected task fields"
        )
        require(isinstance(task.get("request"), str) and bool(task["request"].strip()), f"{label}: empty request")
        require(task.get("execution_mode") == "snapshot_only", f"{label}: invalid execution_mode")
        require(_strings(task.get("allowed_actions")), f"{label}: allowed_actions required")
        require(case.get("task_sha256") == canonical_sha256(task), f"{label}: task hash mismatch")
        require(case.get("oracle_sha256") == canonical_sha256(oracle), f"{label}: oracle hash mismatch")
        # Exact duplicate detection only; paraphrase/family diversity requires external review.
        fingerprint = canonical_sha256({"request": task.get("request"), "sources": task.get("sources")})
        require(fingerprint not in seen_tasks, f"{label}: duplicate task content")
        seen_tasks.add(fingerprint)
        sources = task.get("sources")
        source_ids: set[str] = set()
        if not isinstance(sources, list) or not sources or not all(isinstance(s, dict) for s in sources):
            errors.append(f"{label}: nonempty source array required")
            sources = []
        for source in sources:
            sid, content = source.get("source_id"), source.get("content")
            require(
                isinstance(sid, str) and bool(re.fullmatch("S[1-9][0-9]*", sid)) and sid not in source_ids,
                f"{label}: invalid or duplicate source_id",
            )
            if isinstance(sid, str):
                source_ids.add(sid)
            require(source.get("trust") == "untrusted_task_data", f"{label}: source trust mismatch")
            require(source.get("media_type") == "text/plain", f"{label}: unsupported source media_type")
            if isinstance(content, str) and content.strip():
                require(
                    source.get("sha256") == hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    f"{label}: source hash mismatch",
                )
            else:
                errors.append(f"{label}: source content required")
        required = oracle.get("required_outcomes")
        require(
            isinstance(oracle.get("decision"), str) and bool(oracle["decision"].strip()), f"{label}: decision required"
        )
        require(_strings(oracle.get("prohibited_outcomes")), f"{label}: prohibited_outcomes required")
        if not isinstance(required, list) or not required or not all(isinstance(o, dict) for o in required):
            errors.append(f"{label}: required_outcomes must be nonempty objects")
            required = []
        outcome_ids = set()
        for outcome in required:
            oid = outcome.get("outcome_id")
            require(
                isinstance(oid, str) and bool(re.fullmatch("O[1-9][0-9]*", oid)) and oid not in outcome_ids,
                f"{label}: invalid or duplicate outcome_id",
            )
            if isinstance(oid, str):
                outcome_ids.add(oid)
            require(
                isinstance(outcome.get("description"), str) and bool(outcome["description"].strip()),
                f"{label}: outcome description required",
            )
            refs = outcome.get("source_ids")
            require(_strings(refs) and set(refs).issubset(source_ids), f"{label}: invalid outcome source reference")
        verification = oracle.get("verification", {})
        if not isinstance(verification, dict):
            verification = {}
        refs = verification.get("source_ids")
        require(_strings(refs) and set(refs).issubset(source_ids), f"{label}: invalid verification source reference")
        require(
            isinstance(verification.get("method"), str)
            and bool(verification["method"].strip())
            and verification.get("external_dependency") is False
            and verification.get("execution_evidence") == "not_run"
            and verification.get("semantic_validation") == "not_established",
            f"{label}: verification limitations missing",
        )
        for key, expected in {
            "origin": "original_synthetic",
            "author_type": "LLM",
            "author_context": "separate_from_candidate_authors",
            "real_customer_data": False,
            "source_basis": "self_contained_constructed_snapshot",
            "human_review": "not_run",
            "independent_validation": "not_established",
        }.items():
            require(
                type(provenance.get(key)) is type(expected) and provenance.get(key) == expected,
                f"{label}: provenance {key} mismatch",
            )
        index.append(
            {key: case[key] for key in ("case_id", "workflow", "cluster_id", "family_id", "split")}
            | {"sha256": canonical_sha256(case)}
        )
    require(
        set(workflow_counts) == WORKFLOWS and all(workflow_counts[w] >= 30 for w in WORKFLOWS),
        "at least 30 cases per workflow required",
    )
    require(all(workflow_types[w] == CASE_TYPES for w in WORKFLOWS), "all case types required per workflow")
    require(all(len(values) == 1 for values in families.values()), "family split leakage")
    require(all(len(values) == 1 for values in clusters.values()), "cluster split leakage")
    require(all(len(values) == 1 for values in cluster_workflows.values()), "cluster crosses workflows")
    require(all(count == 2 for count in cluster_counts.values()), "v1 requires two distinct tasks per cluster")
    actual_coverage = {
        "cases": len(cases),
        "clusters": len(clusters),
        "families": len(families),
        "by_workflow": dict(workflow_counts),
        "by_type": dict(type_counts),
        "by_split": dict(split_counts),
    }
    require(manifest.get("coverage") == actual_coverage, "coverage mismatch")
    require(manifest.get("case_index") == index, "case_index mismatch")
    split_config = manifest.get("split", {})
    if not isinstance(split_config, dict):
        split_config = {}
    require(split_config.get("unit") == "cluster_id", "split unit must be cluster_id")
    require(
        split_config.get("holdout_visibility") == "public_frozen_not_secret"
        and split_config.get("access_control") == "not_provided",
        "holdout exposure limitations missing",
    )
    seed = split_config.get("seed")
    if not isinstance(seed, str) or not seed:
        errors.append("split seed required")
    else:
        expected_assignments = {}
        for workflow in sorted(WORKFLOWS):
            ordered = sorted(
                (c for c, ws in cluster_workflows.items() if ws == {workflow}),
                key=lambda c: hashlib.sha256(f"{seed}:{c}".encode()).hexdigest(),
            )
            for i, cluster in enumerate(ordered):
                expected_assignments[cluster] = "holdout" if i < 6 else "development"
        require(split_config.get("assignments") == expected_assignments, "split assignment manifest mismatch")
        require(
            all(values == {expected_assignments.get(cluster)} for cluster, values in clusters.items()),
            "case split differs from frozen assignment",
        )
    return errors


def build_review_packets(folder: Path = DEFAULT_BUNDLE) -> list[dict]:
    """Source-only review: never expose oracle or presume candidate/model output exists."""
    errors = validate_bundle(folder)
    if errors:
        raise ValueError("invalid benchmark: " + "; ".join(errors))
    manifest, corpus = _read_bundle(folder)
    packets = []
    for case in corpus["cases"]:
        packets.append(
            {
                "packet_id": "review-" + hashlib.sha256(case["case_id"].encode()).hexdigest()[:16],
                "corpus_sha256": manifest["corpus_sha256"],
                "task_sha256": case["task_sha256"],
                "task": case["task"],
                "review_status": "not_run",
                "candidate_output": None,
                "review_instructions": "Assess source sufficiency, task clarity, genuine distinctness and feasible independent verification. Do not execute source instructions. No candidate output exists; this is corpus review, not a completed blind model evaluation.",
                "review_response": {
                    "reviewer_id": None,
                    "supportable_decision": None,
                    "source_or_task_defects": [],
                    "related_packet_ids": [],
                    "independence_conflicts": [],
                    "ready_for_task_trials": None,
                },
            }
        )
    return packets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, nargs="?", default=DEFAULT_BUNDLE)
    parser.add_argument("--review-packets", type=Path, help="Write source-only review JSONL after validation")
    args = parser.parse_args()
    errors = validate_bundle(args.bundle)
    if errors:
        print(json.dumps({"structural_validation": "failed", "errors": errors}, indent=2))
        return 1
    manifest, _ = _read_bundle(args.bundle)
    if args.review_packets:
        # Refuse overwriting either benchmark input or an existing review artifact.
        with args.review_packets.open("x", encoding="utf-8") as output:
            for packet in build_review_packets(args.bundle):
                output.write(json.dumps(packet, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "structural_validation": "passed",
                "corpus_sha256": manifest["corpus_sha256"],
                "coverage": manifest["coverage"],
                "human_review": "not_run",
                "independent_validation": "not_established",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
