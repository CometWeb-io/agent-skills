"""Adversarial table: no route to GO or GO_WITH_CONTROLS past an unresolved state.

Every row starts from a manifest the engine rates GO (or GO_WITH_CONTROLS for the
accepted-risk rows), applies one adversarial edit, and pins the verdict. A
blocking governance gate, a pending or denied risk acceptance, stale or expired
evidence, and a missing required scope answer must each keep the release from
an authorizing verdict. Unknown scope keys are reported, never silently dropped,
and never move the verdict.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("readiness_engine_safety", ROOT / "scripts" / "readiness_engine.py")
engine = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(engine)
_boot_spec = importlib.util.spec_from_file_location("bootstrap_manifest_safety", ROOT / "scripts" / "bootstrap_manifest.py")
bootstrap = importlib.util.module_from_spec(_boot_spec)
assert _boot_spec.loader is not None
_boot_spec.loader.exec_module(bootstrap)

AS_OF = "2026-08-25T22:03:05+02:00"
LATER = "2026-12-31T00:00:00Z"
EARLIER = "2026-08-01T00:00:00Z"
CANDIDATE = "abc1234" + "0" * 33
AUTHORIZING = {"GO", "GO_WITH_CONTROLS"}


def _evidence(**extra):
    data = {
        "summary": "candidate-specific evidence",
        "last_verified_at": AS_OF,
        "source_type": "ci",
        "environment": "production",
        "candidate_ref": CANDIDATE,
    }
    data.update(extra)
    return data


def _check(check_id, gate, domain, **overrides):
    base = {
        "id": check_id, "gate": gate, "domain": domain, "title": check_id, "status": "pass",
        "severity": "critical", "binding": True, "evidence_level": "verified",
        "required_evidence": "verified", "freshness": "current", "evidence": _evidence(),
    }
    base.update(overrides)
    return base


def _supported(check_id, gate, domain):
    return _check(check_id, gate, domain, severity="major", evidence_level="supported", required_evidence="supported",
                  evidence={"summary": "reviewed", "last_verified_at": AS_OF, "source_type": "docs"})


def green() -> dict:
    return {
        "manifest_version": 2,
        "profile": "saas_web",
        "mode": "standard",
        "release": {"id": "v2.0.0", "commit_sha": CANDIDATE, "environment": "production", "as_of": AS_OF},
        "scope": {
            "audience": "external", "commercial": "free", "risk_assessment_complete": True,
            "governance_surfaces": [], "risk_flags": {k: "no" for k in engine.SCOPE_FLAG_KEYS},
        },
        "checks": [
            _check("product.acceptance", "release_scope_acceptance", "product"),
            _check("qa.candidate", "candidate_verification", "qa"),
            _check("security.release", "security_release", "security"),
            _check("ops.delivery", "release_delivery", "ops"),
            _check("ops.recovery", "recovery_strategy", "ops"),
            _check("ops.observability", "observability", "ops"),
            _supported("docs.operator", "operator_docs", "docs"),
            _supported("support.path", "support_path", "support"),
        ],
        "governance_gates": [],
    }


def _accepted_risk(**acceptance):
    record = {"approved_by": "release manager", "owner": "qa lead", "rationale": "cosmetic only",
              "mitigation": "fix in next patch", "expires_at": LATER}
    record.update(acceptance)
    return {
        "id": "qa.cosmetic", "domain": "qa", "title": "cosmetic glitch", "status": "accepted_risk",
        "severity": "minor", "binding": False, "evidence_level": "supported", "required_evidence": "supported",
        "freshness": "current", "evidence": {"summary": "seen on candidate", "last_verified_at": AS_OF},
        "risk_acceptance": record,
    }


def _controlled(**fields):
    row = {
        "id": "qa.controlled", "domain": "qa", "title": "flagged path", "status": "pass_with_controls",
        "severity": "minor", "binding": False, "evidence_level": "supported", "required_evidence": "supported",
        "freshness": "current", "evidence": {"summary": "seen on candidate", "last_verified_at": AS_OF},
    }
    row.update(fields)
    return row


def _governance(surface, status, **extra):
    row = {"surface": surface, "status": status, "evidence": {"summary": "reviewed", "last_verified_at": AS_OF},
           "rationale": "reviewed"}
    row.update(extra)
    return row


def _with(mutate):
    def build():
        manifest = green()
        mutate(manifest)
        return manifest
    return build


def _set_check(check_id, **fields):
    def mutate(m):
        for c in m["checks"]:
            if c["id"] == check_id:
                c.update(fields)
    return mutate


def _add_check(row):
    return lambda m: m["checks"].append(row)


def _set_scope(**fields):
    return lambda m: m["scope"].update(fields)


def _set_flag(flag, value):
    return lambda m: m["scope"]["risk_flags"].update({flag: value})


def _drop_flag(flag):
    return lambda m: m["scope"]["risk_flags"].pop(flag)


def _gov(*rows, surfaces=()):
    def mutate(m):
        m["governance_gates"] = list(rows)
        m["scope"]["governance_surfaces"] = list(surfaces)
    return mutate


CASES = [
    # Baselines.
    ("green", _with(lambda m: None), "GO"),
    ("accepted-risk-approved", _with(_add_check(_accepted_risk())), "GO_WITH_CONTROLS"),
    ("accepted-risk-status-approved", _with(_add_check(_accepted_risk(status="approved"))), "GO_WITH_CONTROLS"),
    ("accepted-risk-approved-true", _with(_add_check(_accepted_risk(approved=True))), "GO_WITH_CONTROLS"),
    # Unresolved blockers: a BLOCK outranks a perfect score; controls do not clear it.
    ("governance-block", _with(_gov(_governance("legal", "block"))), "NO_GO"),
    ("governance-block-unrouted-surface", _with(_gov(_governance("reputation", "block"))), "NO_GO"),
    ("governance-block-next-to-controls",
     _with(_gov(_governance("privacy", "block"),
                _governance("legal", "clear_with_controls", control="flag", control_owner="ops", control_due=LATER),
                surfaces=("legal",))),
     "NO_GO"),
    ("governance-counsel-required", _with(_gov(_governance("legal", "counsel_required"), surfaces=("legal",))), "DEFER"),
    ("governance-required-not-required", _with(_gov(_governance("legal", "not_required"), surfaces=("legal",))), "DEFER"),
    ("governance-required-missing", _with(_gov(surfaces=("privacy",))), "DEFER"),
    ("binding-fail", _with(_set_check("qa.candidate", status="fail")), "NO_GO"),
    ("binding-fail-with-controls-text",
     _with(_set_check("qa.candidate", status="fail", mitigation="flag", control_owner="ops", control_due=LATER)), "NO_GO"),
    # Human approval of an accepted risk that is not affirmatively given.
    ("accepted-risk-pending", _with(_add_check(_accepted_risk(status="pending"))), "DEFER"),
    ("accepted-risk-denied", _with(_add_check(_accepted_risk(status="denied"))), "DEFER"),
    ("acceptance-approval-status-requested", _with(_add_check(_accepted_risk(approval_status="requested"))), "DEFER"),
    ("accepted-risk-approved-false", _with(_add_check(_accepted_risk(approved=False))), "DEFER"),
    ("accepted-risk-approved-string", _with(_add_check(_accepted_risk(approved="true"))), "DEFER"),
    ("accepted-risk-expired", _with(_add_check(_accepted_risk(expires_at=EARLIER))), "DEFER"),
    ("accepted-risk-no-approver", _with(_add_check(_accepted_risk(approved_by=""))), "DEFER"),
    # A control that is declared but not in force.
    ("controlled-minor-valid", _with(_add_check(_controlled(control_owner="ops", mitigation="flag", control_due=LATER))),
     "GO_WITH_CONTROLS"),
    ("controlled-minor-no-owner", _with(_add_check(_controlled(mitigation="flag", control_due=LATER))), "DEFER"),
    ("controlled-minor-overdue", _with(_add_check(_controlled(control_owner="ops", mitigation="flag", control_due=EARLIER))),
     "DEFER"),
    # Stale evidence.
    ("binding-stale", _with(_set_check("security.release", freshness="stale")), "DEFER"),
    ("binding-expired", _with(_set_check("security.release", evidence=_evidence(expires_at=EARLIER))), "DEFER"),
    ("binding-observed-after-assessment", _with(_set_check("security.release", evidence=_evidence(last_verified_at=LATER))), "DEFER"),
    ("binding-other-environment", _with(_set_check("security.release", evidence=_evidence(environment="staging"))), "DEFER"),
    ("binding-other-candidate", _with(_set_check("security.release", evidence=_evidence(candidate_ref="f" * 40))), "DEFER"),
    ("governance-clear-stale-evidence",
     _with(_gov(_governance("legal", "clear", evidence={"summary": "old", "last_verified_at": AS_OF, "expires_at": EARLIER}),
                surfaces=("legal",))),
     "DEFER"),
    # Missing required answers.
    ("risk-assessment-incomplete", _with(_set_scope(risk_assessment_complete=False)), "DEFER"),
    ("risk-assessment-string-true", _with(_set_scope(risk_assessment_complete="true")), "DEFER"),
    ("audience-unknown", _with(_set_scope(audience="unknown")), "DEFER"),
    ("commercial-missing", _with(lambda m: m["scope"].pop("commercial")), "DEFER"),
    ("commercial-typo", _with(lambda m: m["scope"].update(comercial=m["scope"].pop("commercial"))), "DEFER"),
    ("risk-flag-unknown", _with(_set_flag("auth_change", "unknown")), "DEFER"),
    ("risk-flag-missing", _with(_drop_flag("billing_change")), "DEFER"),
    ("risk-flag-at-scope-top-level",
     _with(lambda m: m["scope"].update(auth_change=m["scope"]["risk_flags"].pop("auth_change"))), "DEFER"),
    ("required-gate-not-applicable",
     _with(_set_check("ops.recovery", applicable=False, na_reason="no state to roll back")), "DEFER"),
]


@pytest.mark.parametrize("name,build,expected", CASES, ids=[c[0] for c in CASES])
def test_decision_safety_table(name, build, expected) -> None:
    result = engine.evaluate(build())
    assert result["verdict"] == expected, result["reason"]
    if result["verdict"] in AUTHORIZING:
        # The invariant every authorizing verdict must satisfy, whatever the route.
        assert not result["governance_blocks"]
        assert not result["governance_unknowns"]
        assert not result["missing_governance_gates"]
        assert not result["blocking_failures"]
        assert not result["binding_unknowns"]
        assert not result["material_unknowns"]
        assert not result["missing_required_gates"]
        assert not result["scope_gaps"]
        assert not result["release_identity_gaps"]
        assert not result["unresolved_conditions"]


@pytest.mark.parametrize("status", ["pending", "denied", "requested", "", "APPROVED?"])
def test_unapproved_acceptance_is_not_accepted_risk(status: str) -> None:
    manifest = green()
    manifest["checks"].append(_accepted_risk(status=status))
    result = engine.evaluate(manifest)
    assert result["check_states"]["qa.cosmetic"] == "unknown"
    assert result["accepted_risks"] == []
    assert [c["id"] for c in result["unresolved_conditions"]] == ["qa.cosmetic"]
    assert result["verdict"] == "DEFER"


@pytest.mark.parametrize("status", ["approved", "Approved", " granted "])
def test_affirmative_acceptance_states_are_accepted(status: str) -> None:
    manifest = green()
    manifest["checks"].append(_accepted_risk(status=status))
    assert engine.evaluate(manifest)["check_states"]["qa.cosmetic"] == "accepted_risk"


@pytest.mark.parametrize(
    "key,suggestion",
    [
        ("comercial", "commercial"),
        ("Commercial", "commercial"),
        ("governance_surface", "governance_surfaces"),
        ("risk_flag", "risk_flags"),
        ("audiance", "audience"),
        ("risk_assesment_complete", "risk_assessment_complete"),
        ("auth_change", "risk_flags.auth_change"),
        ("auth_chnage", "risk_flags.auth_change"),
        ("owner_team", None),
    ],
)
def test_unknown_scope_key_warns_with_suggestion_and_keeps_verdict(key: str, suggestion: str | None) -> None:
    baseline = engine.evaluate(green())
    manifest = green()
    manifest["scope"][key] = "anything"
    result = engine.evaluate(manifest)
    assert result["verdict"] == baseline["verdict"] == "GO"
    assert result["contract_hash"] == baseline["contract_hash"]
    assert [w["key"] for w in result["scope_warnings"]] == [key]
    warning = result["scope_warnings"][0]
    assert warning["code"] == "unknown_scope_key"
    assert warning.get("suggestion") == suggestion
    assert f"scope.{key}" in warning["message"]
    if suggestion:
        assert suggestion in warning["message"]


def test_known_scope_keys_do_not_warn() -> None:
    manifest = green()
    manifest["scope"].update(notes="n/a", commercial_model="free")
    assert engine.evaluate(manifest)["scope_warnings"] == []
    assert set(engine.SCOPE_KEYS) >= set(manifest["scope"])


def test_validate_only_reports_scope_warnings(tmp_path: Path, capsys) -> None:
    manifest = green()
    manifest["scope"]["comercial"] = "paid"
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert engine.main(["--input", str(path), "--validate-only"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["scope_warnings"][0]["suggestion"] == "commercial"


def test_unknown_risk_flag_error_names_the_likely_flag() -> None:
    manifest = green()
    manifest["scope"]["risk_flags"]["billing_chnage"] = "yes"
    with pytest.raises(engine.ManifestError, match="did you mean 'billing_change'"):
        engine.evaluate(manifest)


@pytest.mark.parametrize("policy,expected_exit", [("controlled", 1), ("strict", 1)])
def test_ci_policy_fails_on_governance_block(tmp_path: Path, policy: str, expected_exit: int, capsys) -> None:
    manifest = green()
    manifest["governance_gates"] = [_governance("legal", "block")]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert engine.main(["--input", str(path), "--ci-policy", policy]) == expected_exit
    assert json.loads(capsys.readouterr().out)["verdict"] == "NO_GO"


def test_bootstrap_rejects_risk_flag_outside_risk_flags() -> None:
    context = {
        "profile": "saas_web",
        "release": {"id": "v2.0", "commit_sha": CANDIDATE, "environment": "production", "as_of": AS_OF},
        "scope": {"audience": "external", "commercial": "free", "risk_assessment_complete": True,
                  "auth_change": "yes", "risk_flags": {}},
    }
    with pytest.raises(engine.ManifestError, match="risk flags belong under scope.risk_flags"):
        bootstrap.build(copy.deepcopy(context))


def test_bootstrap_typo_error_names_the_intended_key() -> None:
    context = {"profile": "saas_web", "release": {}, "scope": {"comercial": "paid"}}
    with pytest.raises(engine.ManifestError, match="did you mean scope.commercial"):
        bootstrap.build(context)
