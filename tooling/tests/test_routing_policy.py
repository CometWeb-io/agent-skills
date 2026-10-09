import json
import sys
from pathlib import Path
import pytest
TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from route_skill import route, normalize, negated_spans, mask_negated
from run_policy_evals import evaluate

POLICY = json.loads((TOOLS.parent / "registry/routing-policy.json").read_text())


def registry():
    return {"skills": [
        {"id":"ai-council", "lifecycle":"active", "explicit_only":True, "routing_signals":[[10,"ai council|what price should we charge|pricing decision still current|material options|strategic go|champion.challenger|council:"]]},
        {"id":"ai-humanize", "lifecycle":"active", "routing_signals":[[10,"humanize"],[5,"fix typos"]]},
        {"id":"evidence-researcher", "lifecycle":"active", "routing_signals":[[10,"evidence pack"]]},
        {"id":"competitive-intelligence", "lifecycle":"active", "routing_signals":[[10,"one-time deep profile of .* pricing|competitor watchlist"],[7,"competitor delta"]]},
        {"id":"competitor-profiling", "lifecycle":"active", "routing_signals":[[20,"one-time deep profile|first deep competitor dossier"]]},
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


def test_near_tie_incompatible_specialists_are_ambiguous():
    data = registry()
    data["skills"].extend([
        {
            "id": "product-operator",
            "lifecycle": "active",
            "routing_signals": [[10, "what should we do this week"]],
        },
        {
            "id": "repo-to-roadmap",
            "lifecycle": "active",
            "routing_signals": [[9, "full roadmap from scratch"]],
        },
    ])
    result = route(
        "Create a full roadmap from scratch and also what should we do this week",
        data,
        POLICY,
    )
    assert result["status"] == "ambiguous"
    assert result["primary_skill"] is None
    assert set(result["candidates"]) == {"product-operator", "repo-to-roadmap"}


def test_use_skill_id_is_explicit_invocation():
    data = registry()
    data["skills"].append({
        "id": "product-operator",
        "lifecycle": "active",
        "routing_signals": [[10, "what should we do this week"]],
    })
    result = route(
        "Use product-operator to compare this repo with the roadmap.",
        data,
        POLICY,
    )
    assert result["status"] == "single_skill"
    assert result["primary_skill"] == "product-operator"


def test_polish_normalization_including_l_stroke():
    assert normalize("ŁÓDŹ Żółć") == "lodz zolc"


def test_eval_rejects_empty_suite():
    with pytest.raises(ValueError):
        evaluate(registry(), POLICY, {"cases":[]})


def test_unknown_policy_fails_closed():
    with pytest.raises(ValueError):
        route("humanize", registry(), {"schema":"unknown"})


def _without_negation():
    policy = json.loads(json.dumps(POLICY))
    policy.pop("negation")
    return policy


def test_negation_suppresses_a_signal_only_inside_the_negated_clause():
    assert route("Do not humanize this paragraph.", registry(), _without_negation())["primary_skill"] == "ai-humanize"
    assert route("Do not humanize this paragraph.", registry(), POLICY)["status"] == "no_skill"
    assert route("Fix the intro, then humanize this paragraph.", registry(), POLICY)["primary_skill"] == "ai-humanize"


@pytest.mark.parametrize("prompt", [
    "find what's not working, humanize it",          # a bare "not" is no cue
    "sprawdz, czy strona nie dziala; humanize",      # mid-clause "nie" + non-listed verb
    "don't ship until you humanize it",              # "until" closes the scope
    "don't hold back: humanize it",                  # punctuation closes the scope
    "nie oszczedzaj mnie, humanize",
])
def test_negation_scope_ends_at_the_clause(prompt):
    assert route(prompt, registry(), POLICY)["primary_skill"] == "ai-humanize"


def test_greedy_signal_cannot_reach_into_a_negated_clause():
    data = registry()
    data["skills"].append({"id": "repo-roaster", "lifecycle": "active", "routing_signals": [[10, "roast.*codebase"]]})
    prompt = "Roast only the README claims; do not review the codebase."
    assert route(prompt, data, _without_negation())["primary_skill"] == "repo-roaster"
    assert "repo-roaster" not in route(prompt, data, POLICY)["scores"]


def test_negated_spans_are_capped_and_offsets_preserved():
    policy = json.loads(json.dumps(POLICY))
    policy["negation"]["max_scope_chars"] = 5
    text = normalize("Do not humanize this paragraph")
    [(start, end)] = negated_spans(text, policy)
    assert end - start == 5
    masked = mask_negated(text, policy)
    assert masked == "do not     nize this paragraph"


def test_negated_exception_does_not_lift_a_narrow_guard():
    report = route("Don't humanize it, just fix typos", registry(), POLICY)
    assert report["blocked"].get("ai-humanize") == "outside_declared_scope"


@pytest.mark.parametrize("mutate", [
    lambda n: n.update(max_scope_chars=0),
    lambda n: n.update(max_scope_chars=True),
    lambda n: n.update(cues=[]),
    lambda n: n.pop("boundary"),
    lambda n: n.update(cues=["(?:do not\\s+)+"]),   # nested quantifier
    lambda n: n.update(boundary="x" * 5000),         # length cap
])
def test_invalid_negation_rules_are_rejected(mutate):
    policy = json.loads(json.dumps(POLICY))
    mutate(policy["negation"])
    with pytest.raises(ValueError):
        route("hello", registry(), policy)


# Multi-skill requests: different specialists win different steps -> workflow skill.

def test_two_specialists_in_sequence_route_to_the_workflow_skill():
    report = route("Click-through the signup flow, then run the release gate.", registry(), POLICY)
    assert (report["status"], report["primary_skill"]) == ("workflow", "skill-orchestrator")
    assert report["candidates"] == ["skill-orchestrator"]
    assert report["sequence"] == ["web-app-auditor", "release-readiness"]


def test_polish_connectors_cut_steps_too():
    report = route("Zrób click-through rejestracji, a po nim release gate.", registry(), POLICY)
    assert report["primary_skill"] == "skill-orchestrator"
    report = route("Click-through rejestracji, na tej podstawie release gate.", registry(), POLICY)
    assert report["primary_skill"] == "skill-orchestrator"


def test_the_same_specialist_in_every_step_stays_a_single_skill():
    report = route("Build an evidence pack, then extend the evidence pack.", registry(), POLICY)
    assert (report["status"], report["primary_skill"]) == ("single_skill", "evidence-researcher")
    assert "sequence" not in report


def test_a_negated_step_does_not_count():
    report = route("Click-through the signup flow, then do not run the release gate.", registry(), POLICY)
    assert (report["status"], report["primary_skill"]) == ("single_skill", "web-app-auditor")


def test_without_a_connector_two_specialists_stay_ambiguous():
    report = route("click-through and release gate", registry(), POLICY)
    assert report["status"] == "ambiguous"


def test_an_explicit_only_skill_named_by_its_signals_counts_as_a_step():
    report = route("Refresh the competitor watchlist, then take it to the ai council.", registry(), POLICY)
    assert report["primary_skill"] == "skill-orchestrator"
    assert report["sequence"] == ["competitive-intelligence", "ai-council"]
    # Without the second step the Council alone still needs an explicit invocation.
    assert route("Take it to the ai council.", registry(), POLICY)["status"] == "no_skill"


def test_host_invocation_and_excluded_workflow_skip_the_sequence_rule():
    prompt = "Click-through the signup flow, then run the release gate."
    invoked = route(prompt, registry(), POLICY, invoked=("web-app-auditor",))
    assert invoked["primary_skill"] == "web-app-auditor"
    excluded = route("Without skill-orchestrator: " + prompt, registry(), POLICY)
    assert excluded["primary_skill"] != "skill-orchestrator"
    assert excluded["blocked"]["skill-orchestrator"] == "explicitly_excluded"


def test_steps_below_the_minimum_score_do_not_count():
    policy = json.loads(json.dumps(POLICY))
    policy["sequence"]["min_step_score"] = 11
    report = route("Click-through the signup flow, then run the release gate.", registry(), policy)
    assert report["status"] == "ambiguous"
    del policy["sequence"]
    assert route("Click-through the signup flow, then run the release gate.", registry(), policy)["status"] == "ambiguous"


@pytest.mark.parametrize("rules", [
    {"connector": "then"},
    {"connector": "then", "min_step_score": 0},
    {"connector": "then", "min_step_score": True},
    {"connector": "(a+)+", "min_step_score": 7},
    "then",
])
def test_malformed_sequence_rules_are_rejected(rules):
    policy = json.loads(json.dumps(POLICY))
    policy["sequence"] = rules
    with pytest.raises(ValueError):
        route("hello", registry(), policy)
