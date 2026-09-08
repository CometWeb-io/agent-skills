import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "context_plan.py"
spec = importlib.util.spec_from_file_location("context_plan", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_outreach_profile():
    assert module.pick_profile("Przygotuj outreach do design partnera") == "outreach"


def test_delta_mode():
    assert module.pick_mode("Co się zmieniło od ostatniego review?", "auto") == "delta"


def test_weekly_full_mode():
    assert module.pick_profile("Zrób weekly boardroom review") == "weekly"
    assert module.pick_mode("Zrób weekly boardroom review", "auto") == "full"


def test_product_profile():
    assert module.pick_profile("Sprawdź stan repo CometWeb Insight i roadmapę") == "product"


def test_product_and_gtm_include_first_principles():
    profiles = module.load_profiles()
    assert "vault-first-principles" in profiles["product"]
    assert "vault-first-principles" in profiles["gtm"]


def test_profiles_come_from_registry_file():
    profiles = module.load_profiles()
    assert "meeting" in profiles
    assert "calendar" in profiles["meeting"]
