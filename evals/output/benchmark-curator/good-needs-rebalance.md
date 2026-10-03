# Benchmark curation — meeting-notes-golden r1

## Status

NEEDS_REBALANCE

The kernel reports `classes:missing` (adversarial) and nothing else, so the case contract is sound but coverage is not. Do not freeze this revision.

## Benchmark identity

- Benchmark ID: `meeting-notes-golden`, revision `r1`, mode STANDARD
- benchmark_hash: not issued; the kernel only hashes a `READY_TO_FREEZE` revision
- rubric_hash: none bound
- Target skill: `meeting-notes`

## Taxonomy and splits

- Required classes: discovery, forced, negative-control, adversarial.
- Present: discovery 2, forced 2, negative-control 1, adversarial 0.
- Difficulty: easy 2, medium 2, hard 1; no edge case yet.
- Splits: dev 5, holdout 0. STANDARD mode does not require a holdout; none is claimed.

## Provenance and exposure

- Provenance coverage: MN-02 cites `upload-example-4`; the other four are SYNTHETIC.
- No case was derived from a candidate failure, so no exposure is recorded.

## Duplicates

- MN-01 and MN-02 are near-duplicates in intent (transcript to notes); OPEN until MN-02 is reworded around action items only.

## Leakage

- Leakage status: NOT_REQUIRED. No scan was supplied, which STANDARD mode allows; no holdout claim is made.

## Holdout decisions

- None removed or quarantined; there is no holdout split in r1.

## Coverage gaps

- Missing adversarial class: add at least two cases, for example a transcript that embeds instructions to the note taker, and one with contradictory decisions.
- Only one negative control; routing claims need more than one near-miss.

## Regression cases

- None yet; no production failure has been recorded for `meeting-notes`.

## Next owner

none until r2 adds the adversarial cases; then `rubric-designer`.

## Benchmark manifest

```json
{
  "benchmark_id": "meeting-notes-golden",
  "revision": "r1",
  "objective": "Golden set for meeting-notes forced behavior",
  "target_skill": "meeting-notes",
  "mode": "STANDARD",
  "required_classes": ["discovery", "forced", "negative-control", "adversarial"],
  "cases": [
    {"id": "MN-01", "class": "discovery", "difficulty": "easy", "split": "dev", "contamination_status": "CLEAN", "source_lane": "SYNTHETIC", "prompt": "Turn this call transcript into notes", "expected_behavior": "routes to meeting-notes", "assertions": ["skill triggers"]},
    {"id": "MN-02", "class": "discovery", "difficulty": "medium", "split": "dev", "contamination_status": "CLEAN", "source_lane": "USER_SUPPLIED", "provenance_ref": "upload-example-4", "prompt": "Write up action items from the attached standup", "expected_behavior": "routes to meeting-notes", "assertions": ["skill triggers"]},
    {"id": "MN-03", "class": "forced", "difficulty": "medium", "split": "dev", "contamination_status": "CLEAN", "source_lane": "SYNTHETIC", "prompt": "Use meeting-notes on a transcript with two speakers named Alex", "expected_behavior": "keeps the speakers distinct", "assertions": ["no merged owners"]},
    {"id": "MN-04", "class": "forced", "difficulty": "hard", "split": "dev", "contamination_status": "CLEAN", "source_lane": "SYNTHETIC", "prompt": "Use meeting-notes on a transcript with no decisions", "expected_behavior": "says no decision was made", "assertions": ["no invented decision"]},
    {"id": "MN-05", "class": "negative-control", "difficulty": "easy", "split": "dev", "contamination_status": "CLEAN", "source_lane": "SYNTHETIC", "prompt": "Schedule a meeting with the design team next week", "expected_behavior": "does not trigger", "assertions": ["skill not selected"]}
  ]
}
```
