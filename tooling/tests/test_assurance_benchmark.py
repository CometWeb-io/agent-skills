"""These tests validate data integrity, not the correctness of LLM-authored oracles."""

from copy import deepcopy
import json

import pytest

from assurance_benchmark import (
    DEFAULT_BUNDLE,
    build_review_packets,
    canonical_sha256,
    main,
    validate_bundle,
)


@pytest.fixture
def bundle(tmp_path):
    for filename in ("manifest.json", "cases.json"):
        (tmp_path / filename).write_bytes((DEFAULT_BUNDLE / filename).read_bytes())
    return tmp_path


def mutate(folder, filename, change):
    path = folder / filename
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value))


def test_frozen_cohort_is_structurally_valid():
    assert validate_bundle() == []


def test_canonical_hash_is_order_independent_and_unicode_sensitive():
    assert canonical_sha256({"a": 1, "b": "ą"}) == canonical_sha256({"b": "ą", "a": 1})
    assert canonical_sha256({"a": 1}) != canonical_sha256({"a": 2})


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda c: c.update(case_id="../../bad"), "invalid case/family/cluster ID"),
        (lambda c: c.update(workflow=[]), "invalid workflow, split or case_type"),
        (lambda c: c.update(split="train"), "invalid workflow, split or case_type"),
        (lambda c: c["task"]["sources"][0].update(content="changed"), "source hash mismatch"),
        (lambda c: c["task"].update(oracle="answer leak"), "unexpected task fields"),
        (lambda c: c["oracle"]["required_outcomes"][0].update(source_ids=["S999"]), "invalid outcome source reference"),
        (lambda c: c["oracle"].update(prohibited_outcomes=[]), "prohibited_outcomes required"),
        (lambda c: c["oracle"].update(required_outcomes=[]), "required_outcomes must be nonempty objects"),
        (lambda c: c["provenance"].update(real_customer_data=True), "provenance real_customer_data mismatch"),
        (lambda c: c["provenance"].update(human_review="passed"), "provenance human_review mismatch"),
        (
            lambda c: c["provenance"].update(independent_validation="passed"),
            "provenance independent_validation mismatch",
        ),
        (lambda c: c["oracle"]["verification"].update(execution_evidence="passed"), "verification limitations missing"),
    ],
)
def test_rejects_corrupt_case_fields(bundle, change, message):
    mutate(bundle, "cases.json", lambda data: change(data["cases"][0]))
    assert any(message in error for error in validate_bundle(bundle))


def test_rejects_duplicate_ids_and_content(bundle):
    def change(data):
        data["cases"][1] = deepcopy(data["cases"][0])

    mutate(bundle, "cases.json", change)
    errors = validate_bundle(bundle)
    assert any("duplicate case_id" in error for error in errors)
    assert any("duplicate task content" in error for error in errors)


def test_rejects_split_leakage_within_cluster(bundle):
    def change(data):
        case = data["cases"][0]
        case["split"] = "development" if case["split"] == "holdout" else "holdout"

    mutate(bundle, "cases.json", change)
    errors = validate_bundle(bundle)
    assert "cluster split leakage" in errors
    assert "family split leakage" in errors
    assert "case split differs from frozen assignment" in errors


def test_manifest_cannot_redirect_corpus_reader(bundle):
    mutate(bundle, "manifest.json", lambda data: data.update(corpus_file="../../secret.json"))
    assert "corpus_file must be cases.json" in validate_bundle(bundle)


def test_rejects_coordinated_split_change_without_original_assignment(bundle):
    def change(data):
        first_cluster = data["cases"][0]["cluster_id"]
        for case in data["cases"]:
            if case["cluster_id"] == first_cluster:
                case["split"] = "development" if case["split"] == "holdout" else "holdout"

    mutate(bundle, "cases.json", change)
    assert "case split differs from frozen assignment" in validate_bundle(bundle)


def test_rejects_missing_workflow_and_minimum_count(bundle):
    mutate(bundle, "cases.json", lambda data: data.update(cases=data["cases"][:34]))
    errors = validate_bundle(bundle)
    assert "at least 100 cases required" in errors
    assert "at least 30 cases per workflow required" in errors
    assert "all case types required per workflow" in errors


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("coverage", {}, "coverage mismatch"),
        ("case_index", [], "case_index mismatch"),
        ("corpus_sha256", "0" * 64, "corpus hash mismatch"),
        ("freeze_stage", "after_trial", "invalid freeze_stage"),
        ("frozen_at", "2026-10-27", "frozen_at requires a timezone"),
        ("candidate_executions", "passed", "manifest candidate_executions must remain not_run"),
        ("independent_validation", "established", "manifest independent_validation must remain not_established"),
    ],
)
def test_rejects_manifest_drift(bundle, key, value, message):
    mutate(bundle, "manifest.json", lambda data: data.update({key: value}))
    assert message in validate_bundle(bundle)


def test_rejects_seed_and_assignment_drift(bundle):
    mutate(bundle, "manifest.json", lambda data: data["split"].update(seed="different"))
    assert "split assignment manifest mismatch" in validate_bundle(bundle)


def test_missing_and_malformed_bundle_return_errors(bundle):
    (bundle / "manifest.json").write_text("{")
    assert validate_bundle(bundle)[0].startswith("bundle unreadable:")
    (bundle / "manifest.json").unlink()
    assert validate_bundle(bundle)[0].startswith("bundle unreadable:")


def test_blind_review_packets_have_sources_but_no_answers_or_arm_identity():
    packets = build_review_packets()
    assert len(packets) == 102
    assert len({p["packet_id"] for p in packets}) == 102
    for packet in packets:
        assert packet["candidate_output"] is None
        assert packet["review_status"] == "not_run"
        assert packet["task"]["sources"]
        assert packet["review_response"]["reviewer_id"] is None
        assert (
            not {
                "oracle",
                "decision",
                "case_id",
                "workflow",
                "split",
                "provenance",
                "arm",
                "model",
                "candidate_version",
                "required_outcomes",
            }
            & packet.keys()
        )


def test_packet_generation_refuses_invalid_bundle(bundle):
    mutate(bundle, "manifest.json", lambda data: data.update(corpus_sha256="wrong"))
    with pytest.raises(ValueError, match="invalid benchmark"):
        build_review_packets(bundle)


def test_cli_emits_packets_and_refuses_overwrite(bundle, tmp_path, monkeypatch, capsys):
    output = tmp_path / "packets.jsonl"
    monkeypatch.setattr("sys.argv", ["assurance_benchmark", str(bundle), "--review-packets", str(output)])
    assert main() == 0
    assert len(output.read_text().splitlines()) == 102
    assert json.loads(capsys.readouterr().out)["structural_validation"] == "passed"
    with pytest.raises(FileExistsError):
        main()


def test_cli_invalid_bundle_never_emits_review_packet(bundle, tmp_path, monkeypatch, capsys):
    output = tmp_path / "packets.jsonl"
    mutate(bundle, "cases.json", lambda data: data.update(cases=[]))
    monkeypatch.setattr("sys.argv", ["assurance_benchmark", str(bundle), "--review-packets", str(output)])
    assert main() == 1
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["structural_validation"] == "failed"
