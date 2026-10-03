"""Decision-contract values the kernel routes on must be values it knows.

A caller-supplied `reversibility: "irreversible"` read as reversible (lower
mode, lower required confidence), and `risk_surfaces: ["Legal"]` routed no
legal gatekeeper. Both were accepted without a word. Unknown values are now
input errors, the same way an unknown council mode already was.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/council_kernel.py"
spec = importlib.util.spec_from_file_location("council_contract_enums_subject", SCRIPT)
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)

QUESTION = "Czy podnieść cenę planu?"


@pytest.mark.parametrize("context,message", [
    ({"reversibility": "irreversible"}, "reversibility must be one of: hard_to_reverse, reversible"),
    ({"risk_level": "extreme"}, "risk_level must be one of: high, low, medium"),
    ({"decision_type": "acquisition"}, "decision_type must be one of: binary, build_vs_buy, hiring, launch, "
     "m_and_a, market_entry, option_selection, partnership, pricing, product_investment, resource_allocation, "
     "sequencing, shutdown"),
    ({"risk_surfaces": ["Legal"]}, "risk_surfaces must be drawn from: financial, legal, people, privacy, "
     "reputation, responsible_ai, security, technical"),
])
def test_compile_rejects_unknown_contract_values(context, message):
    with pytest.raises(ValueError) as exc:
        k.compile_decision_contract(QUESTION, context)
    assert str(exc.value) == message


def test_documented_values_are_accepted():
    contract = k.compile_decision_contract(QUESTION, {
        "decision_type": "sequencing", "reversibility": "hard_to_reverse",
        "risk_level": "high", "risk_surfaces": ["legal"],
    })
    assert contract["decision_type"] == "sequencing"
    assert "legal" in contract["risk_surfaces"]


@pytest.mark.parametrize("changes,message", [
    ({"primary_domain": "Strategy"}, "primary_domain must be one of: growth, marketing, offer_pricing, "
     "operator, product_customer, sales, strategy"),
    ({"secondary_domains": ["sales", "finance"]}, "secondary_domains must be drawn from: growth, marketing, "
     "offer_pricing, operator, product_customer, sales, strategy"),
    ({"decision_kind": "pricing_change"}, "decision_kind must be one of: growth, marketing, operations, "
     "pricing, product_customer, sales, strategy"),
    ({"risk_level": "extreme"}, "risk_level must be one of: high, low, medium"),
])
def test_plan_rejects_unknown_contract_values(changes, message):
    contract = {**k.compile_decision_contract(QUESTION, {}), **changes}
    with pytest.raises(ValueError) as exc:
        k.plan_council(contract)
    assert str(exc.value) == message


def test_route_rejects_misspelled_risk_surface_instead_of_dropping_the_gate():
    contract = {"question": "bounded test", "primary_domain": "strategy", "risk_surfaces": ["Legal"]}
    with pytest.raises(ValueError):
        k.route_roles(contract, "STANDARD")


def test_mode_and_threshold_reject_unknown_profile_values():
    with pytest.raises(ValueError):
        k.choose_council_mode({"risk_level": "low", "reversibility": "irreversible"})
    with pytest.raises(ValueError):
        k.required_confidence({"risk_level": "severe"}, 0.5)


def test_cli_reports_invalid_contract_without_echoing_it():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "contract", "--query", QUESTION,
         "--context-json", json.dumps({"reversibility": "irreversible"})],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 2
    assert json.loads(proc.stderr) == {"status": "INVALID", "error": "invalid decision input",
                                       "execution_authorized": False}
