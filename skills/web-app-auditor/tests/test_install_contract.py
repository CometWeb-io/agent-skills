from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_validator_dependency_is_documented():
    text = (ROOT / "INSTALL.md").read_text()
    assert "pip install -r requirements.txt" in text
    assert "jsonschema" in text
    assert "only Python" not in text.replace("\n", " ")

def test_installation_does_not_pin_obsolete_skill_version():
    assert "v1.1" not in (ROOT / "INSTALL.md").read_text().splitlines()[0]
