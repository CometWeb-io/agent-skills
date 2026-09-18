import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _context_fixtures import load_script

module = load_script("context_plan")


def test_outreach_profile():
    assert module.pick_profile("Przygotuj outreach do design partnera") == "outreach"


def test_delta_mode():
    assert module.pick_mode("Co się zmieniło od ostatniego review?", "auto") == "delta"


def test_weekly_full_mode():
    assert module.pick_profile("Zrób weekly boardroom review") == "weekly"
    assert module.pick_mode("Zrób weekly boardroom review", "auto") == "full"


def test_product_profile():
    assert module.pick_profile("Sprawdź stan repo CometWeb Insight i roadmapę") == "product"


def test_portfolio_profile_for_whole_cometweb():
    goal = "Przeanalizuj całe CometWeb: Insight, CometBase, CometPen, Lens i wszystkie projekty"
    assert module.pick_profile(goal) == "portfolio"
    assert module.pick_mode(goal, "auto") == "full"


def test_cross_system_portfolio_profile():
    assert module.pick_profile("Przeanalizuj Notion, GitHub i wszystkie projekty CometWeb") == "portfolio"


def test_material_gtm_plan_requires_first_principles():
    payload = module.plan("Czy powinniśmy zmienić pricing i packaging CometWeb?")
    assert payload["profile"] == "gtm"
    assert payload["governance"]["first_principles_required"] is True
    assert "vault-first-principles" in payload["source_groups"]


def test_simple_product_state_does_not_force_first_principles():
    payload = module.plan("Sprawdź aktualny stan repo CometWeb Insight")
    assert payload["profile"] == "product"
    assert payload["governance"]["first_principles_required"] is False


def test_generic_cometweb_delta_uses_portfolio_without_forcing_governance():
    payload = module.plan("Co się zmieniło w CometWeb od ostatniego przeglądu?")
    assert payload["profile"] == "portfolio"
    assert payload["mode"] == "delta"
    assert payload["governance"]["first_principles_required"] is False


def test_portfolio_priority_decision_requires_first_principles():
    payload = module.plan("Który projekt CometWeb powinien być teraz priorytetem i na czym mam się skupić?")
    assert payload["profile"] == "portfolio"
    assert payload["governance"]["first_principles_required"] is True
    assert "vault-first-principles" in payload["source_groups"]


def test_plain_full_refresh_is_portfolio_not_weekly():
    payload = module.plan("Zrób pełny refresh całego CometWeb")
    assert payload["profile"] == "portfolio"
    assert payload["mode"] == "full"


def test_two_week_focus_is_standard_portfolio_not_weekly():
    payload = module.plan("Zbierz kontekst do decyzji, na czym skupić się w CometWeb przez najbliższe 2 tygodnie")
    assert payload["profile"] == "portfolio"
    assert payload["mode"] == "standard"
    assert payload["governance"]["first_principles_required"] is True
