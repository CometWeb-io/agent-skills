from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
OUTPUT = (ROOT / "references" / "output-contract.md").read_text(encoding="utf-8")


def test_full_means_retrieval_not_verbosity():
    assert "`full` oznacza pełny zakres źródeł, nie pełny dump do użytkownika" in SKILL


def test_direct_user_does_not_dump_envelope():
    assert "Nie pokazuj pełnego `ContextEnvelope` użytkownikowi domyślnie" in SKILL
    assert "never include raw ContextEnvelope JSON unless explicitly requested" in OUTPUT


def test_response_budgets_are_defined():
    assert "**120 słów**" in SKILL
    assert "**220 słów**" in SKILL
    assert "**320 słów**" in SKILL


def test_downstream_keeps_full_envelope():
    assert "przekaż pełny ContextEnvelope następnemu komponentowi" in SKILL
    assert "Pass the full machine structure downstream" in OUTPUT


def test_output_lanes_exist():
    for lane in ("DIRECT_USER", "DOWNSTREAM", "DEBUG / EXPLICIT_DETAIL"):
        assert lane in SKILL
        assert lane in OUTPUT
