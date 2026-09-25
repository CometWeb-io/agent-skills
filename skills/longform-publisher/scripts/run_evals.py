#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from publication_kernel import check_derived, check_manuscript, infer_stage, validate_report


def base_text() -> str:
    return "# Practical Guide\n\nIn 2026, the workflow may reduce duplicated editing by 37% [1].\n"


def base_report() -> dict:
    text = base_text()
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "protocol_version": "longform-publisher/1",
        "as_of": "2026-09-10T20:30:00+02:00",
        "mode": "BUILD",
        "status": "READY",
        "status_reason": "Current publication gates are satisfied.",
        "publication": {"id": "pub-1", "title": "Practical Guide", "type": "EBOOK", "audience": "Operators", "objective": "Teach a workflow."},
        "source_policy": {"mode": "RESEARCH_EXPAND", "authorized_source_ids": ["src-user", "src-web"]},
        "sources": [
            {"id": "src-user", "system": "USER", "locator": "conversation", "authorized": True, "freshness": "CURRENT", "observed_at": "2026-09-10T20:00:00+02:00"},
            {"id": "src-web", "system": "WEB", "locator": "https://example.com/source", "authorized": True, "freshness": "CURRENT", "observed_at": "2026-09-10T20:00:00+02:00"},
        ],
        "lifecycle": {"brief_complete": True, "sources_admitted": True, "outline_locked": True, "draft_complete": True, "claims_reconciled": True, "edited_complete": True, "master_locked": True, "release_ready": True},
        "current_stage": "RELEASE_READY",
        "canonical_master": {"path": "manuscript.md", "version": "1.0.0", "sha256": h},
        "sections": [{"id": "s1", "heading": "Practical Guide", "status": "COMPLETE"}],
        "claim_uses": [{
            "id": "c1", "section_id": "s1", "claim_text": "The workflow may reduce duplicated editing by 37%.",
            "materiality": "MATERIAL", "claim_kind": "FACT", "support_status": "SUPPORTED", "evidence_refs": ["src-web"],
            "citation_state": "REQUIRED", "citation_marker": "[1]", "volatile_current": False, "freshness_state": "CURRENT"
        }],
        "protected_facts": [
            {"id": "p1", "value": "2026", "required": True},
            {"id": "p2", "value": "may reduce", "required": True},
            {"id": "p3", "value": "37%", "required": True},
        ],
        "fidelity": {"required": False, "passed": True, "checked_at": "2026-09-10T20:20:00+02:00"},
        "edit_history": [],
        "unresolved_gaps": [],
        "derived_artifacts": [{
            "id": "html1", "format": "HTML", "path": "guide.html", "master_sha256": h,
            "generation_status": "COMPLETE", "qa_required": False, "qa_status": "NOT_REQUIRED", "parity_status": "PASS", "direct_material_edit": False
        }],
        "publication_evidence": [],
        "actions": {"blockers": [], "verify_now": [], "decision_now": [], "now": [], "next_milestone": [], "delegate": [], "waiting": [], "stop": []},
    }


def build_scenario(name: str) -> tuple[dict, str]:
    r = deepcopy(base_report())
    text = base_text()
    if name == "build_valid":
        pass
    elif name == "source_bound_valid":
        r["mode"] = "SOURCE_BOUND"; r["source_policy"] = {"mode": "SOURCE_BOUND", "authorized_source_ids": ["src-user"]}
        r["sources"] = [r["sources"][0]]
        r["claim_uses"][0]["evidence_refs"] = ["src-user"]
    elif name == "source_bound_external":
        r["mode"] = "SOURCE_BOUND"; r["source_policy"] = {"mode": "SOURCE_BOUND", "authorized_source_ids": ["src-user"]}
    elif name == "humanize_modal_drift":
        r["edit_history"] = [{"type": "AI_HUMANIZE", "status": "COMPLETE"}]
        r["fidelity"] = {"required": True, "passed": False}
        text = text.replace("may reduce", "will reduce")
        r["canonical_master"]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        r["derived_artifacts"][0]["master_sha256"] = r["canonical_master"]["sha256"]
    elif name == "humanize_number_drift":
        r["edit_history"] = [{"type": "AI_HUMANIZE", "status": "COMPLETE"}]
        r["fidelity"] = {"required": True, "passed": True, "checked_at": "2026-09-10T20:25:00+02:00"}
        text = text.replace(" by 37%", "")
        r["canonical_master"]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        r["derived_artifacts"][0]["master_sha256"] = r["canonical_master"]["sha256"]
    elif name == "docx_missing_visual_qa":
        r["derived_artifacts"] = [{"id": "d1", "format": "DOCX", "path": "guide.docx", "master_sha256": r["canonical_master"]["sha256"], "generation_status": "COMPLETE", "qa_required": True, "qa_status": "MISSING", "parity_status": "PASS", "direct_material_edit": False}]
    elif name == "pdf_missing_visual_requirement":
        r["derived_artifacts"] = [{"id": "p1", "format": "PDF", "path": "guide.pdf", "master_sha256": r["canonical_master"]["sha256"], "generation_status": "COMPLETE", "qa_required": False, "qa_status": "NOT_REQUIRED", "parity_status": "PASS", "direct_material_edit": False}]
    elif name == "pdf_parity_fail":
        r["derived_artifacts"] = [{"id": "p1", "format": "PDF", "path": "guide.pdf", "master_sha256": r["canonical_master"]["sha256"], "generation_status": "COMPLETE", "qa_required": True, "qa_status": "PASS", "parity_status": "FAIL", "direct_material_edit": False}]
    elif name == "stale_current_claim":
        r["claim_uses"][0]["volatile_current"] = True
        r["sources"][1]["freshness"] = "STALE"
    elif name == "scientific_without_readiness":
        r["publication"]["type"] = "SCIENTIFIC_MANUSCRIPT"
    elif name == "scientific_with_readiness":
        r["publication"]["type"] = "SCIENTIFIC_MANUSCRIPT"
        r["scientific_readiness"] = {"status": "PASS", "source": "research-program-operator", "evidence_ref": "src-user"}
    elif name == "invented_marketing_proof":
        r["claim_uses"][0]["support_status"] = "UNRESOLVED"; r["claim_uses"][0]["evidence_refs"] = []
    elif name == "direct_derived_edit":
        r["derived_artifacts"][0]["direct_material_edit"] = True
    elif name == "published_without_evidence":
        r["current_stage"] = "PUBLISHED"
    elif name == "published_with_evidence":
        r["current_stage"] = "PUBLISHED"; r["publication_evidence"] = [{"type": "URL", "locator": "https://example.com/guide"}]
    elif name == "refresh_prior_published":
        r["mode"] = "REFRESH"; r["lifecycle"]["claims_reconciled"] = False; r["lifecycle"]["edited_complete"] = False; r["lifecycle"]["master_locked"] = False; r["lifecycle"]["release_ready"] = False
        r["current_stage"] = "DRAFTED"; r["prior_publication_evidence"] = [{"type": "URL", "locator": "https://example.com/old-guide"}]
    elif name == "citation_missing":
        text = text.replace(" [1]", "")
        r["canonical_master"]["sha256"] = hashlib.sha256(text.encode()).hexdigest(); r["derived_artifacts"][0]["master_sha256"] = r["canonical_master"]["sha256"]
    elif name == "critical_gap_open":
        r["unresolved_gaps"] = [{"id": "g1", "materiality": "CRITICAL", "status": "OPEN"}]
    elif name == "evidence_ref_missing":
        r["claim_uses"][0]["evidence_refs"] = ["src-missing"]
    elif name == "valid_pdf_release":
        r["derived_artifacts"] = [{"id": "p1", "format": "PDF", "path": "guide.pdf", "master_sha256": r["canonical_master"]["sha256"], "generation_status": "COMPLETE", "qa_required": True, "qa_status": "PASS", "parity_status": "PASS", "direct_material_edit": False}]
    elif name == "derived_incomplete":
        r["derived_artifacts"][0]["generation_status"] = "PENDING"
    elif name == "derived_master_mismatch":
        r["derived_artifacts"][0]["master_sha256"] = "0" * 64
    elif name == "source_ready_not_outlined":
        r["lifecycle"]["outline_locked"] = False
        r["current_stage"] = "SOURCE_READY"
    elif name == "locked_placeholder":
        text += "\n[TODO: verify layout]\n"
        h = hashlib.sha256(text.encode()).hexdigest()
        r["canonical_master"]["sha256"] = h
        r["derived_artifacts"][0]["master_sha256"] = h
    else:
        raise ValueError(name)
    return r, text


def run_case(path: Path) -> tuple[bool, str]:
    case = json.loads(path.read_text(encoding="utf-8"))
    report, text = build_scenario(case["scenario"])
    actual = {
        "validation": sorted(validate_report(report)),
        "manuscript": sorted(check_manuscript(report, text)),
        "derived": sorted(check_derived(report)),
        "stage": infer_stage(report),
    }
    expected = case["expect"]
    expected = {
        "validation": sorted(expected.get("validation", [])),
        "manuscript": sorted(expected.get("manuscript", [])),
        "derived": sorted(expected.get("derived", [])),
        "stage": expected.get("stage", actual["stage"]),
    }
    return actual == expected, f"expected={expected} actual={actual}"


def main() -> int:
    cases = sorted((ROOT / "evaluation" / "cases").glob("*.json"))
    failures = 0
    for path in cases:
        ok, detail = run_case(path)
        print(f"{'PASS' if ok else 'FAIL'} {path.name}")
        if not ok:
            failures += 1
            print(detail)
    print(f"RESULT {len(cases) - failures}/{len(cases)} PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
