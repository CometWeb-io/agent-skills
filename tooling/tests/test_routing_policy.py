import json
import sys
from pathlib import Path
import pytest
TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from route_skill import route, normalize
from run_policy_evals import evaluate

POLICY = json.loads((TOOLS.parent / "registry/routing-policy.json").read_text())


def registry():
    return {"skills": [
        {"id":"ai-council", "lifecycle":"active", "explicit_only":True, "routing_signals":[[10,"ai council|what price should we charge|pricing decision still current|material options|strategic go|champion.challenger|council:"]]},
        {"id":"ai-humanize", "lifecycle":"active", "routing_signals":[[10,"humanize"],[5,"fix typos"]]},
        {"id":"evidence-researcher", "lifecycle":"active", "routing_signals":[[10,"evidence pack"]]},
        {"id":"competitive-intelligence", "lifecycle":"active", "routing_signals":[[10,"one-time deep profile of .* pricing|competitor watchlist"],[7,"competitor delta"]]},
        {"id":"skill-orchestrator", "lifecycle":"active", "routing_signals":[[16,"zorkiestruj"]]},
        {"id":"skill-orchestrator-multiagent", "lifecycle":"active", "alias_of":"skill-orchestrator", "routing_signals":[[20,"one subagent per skill"]]},
        {"id":"cometweb-context", "lifecycle":"active", "routing_signals":[[12,"odswiez.*kontekst"]]},
        {"id":"release-readiness", "lifecycle":"active", "routing_signals":[[10,"release gate"]]},
        {"id":"web-app-auditor", "lifecycle":"active", "routing_signals":[[10,"click-through"]]},
        {"id":"seo-geo-aeo-maxxing", "lifecycle":"active", "routing_signals":[[12,"seo/geo/aeo"]]},
    ]}


SUITE = json.loads((TOOLS.parent / "evals/routing/policy-suite.json").read_text())


@pytest.mark.parametrize("case", SUITE["cases"], ids=lambda c: c["id"])
def test_policy_cases_against_synthetic_registry(case):
    report = evaluate(registry(), POLICY, {"cases":[case]})
    assert report["passed"] == 1, report


def test_inactive_skill_never_routes():
    data = registry()
    data["skills"][1]["lifecycle"] = "retired"
    assert route("humanize", data, POLICY)["status"] == "no_skill"


def test_unknown_explicit_id_fails():
    with pytest.raises(ValueError):
        route("hello", registry(), POLICY, invoked=("missing",))


def test_registry_order_does_not_break_ties():
    data = registry()
    first = route("humanize evidence pack", data, POLICY)
    data["skills"].reverse()
    assert route("humanize evidence pack", data, POLICY) == first
    assert first["status"] == "ambiguous"


def test_polish_normalization_including_l_stroke():
    assert normalize("ŁÓDŹ Żółć") == "lodz zolc"


def test_eval_rejects_empty_suite():
    with pytest.raises(ValueError):
        evaluate(registry(), POLICY, {"cases":[]})


def test_unknown_policy_fails_closed():
    with pytest.raises(ValueError):
        route("humanize", registry(), {"schema":"unknown"})
