# Output contract

## Table of contents

1. Human-readable teardown
2. Pattern card
3. Machine-readable ledger v2
4. Confidence decomposition
5. Handoff notes

## 1. Human-readable teardown

Use this structure by default and omit genuinely irrelevant sections.

```markdown
# Product Teardown - [source(s)] -> [destination or source-only]

## Executive verdict
- Shape:
- Mode:
- Scope:
- Evidence quality:
- Destination evidence quality:
- Best transferable idea:
- Most important false friend:
- Action mix: X ADOPT / Y EXPERIMENT / Z CANDIDATE / ...
- Mandatory blockers:

## Source/version map
[What was inspected, versions/dates/plans/platforms, blind spots]

## Destination problem map
[Only when destination exists: problem evidence, existing equivalent, constraints, baseline]

## Relevant system/flow map
[Only the map needed to explain patterns]

## Pattern portfolio / pattern families
### PT-001 - [Pattern name]
- Family:
- Category:
- Problem:
- Source observation:
- Evidence:
- Mechanism hypothesis:
- Destination problem evidence:
- Existing target capability:
- Transfer conditions:
- Chosen transfer mode:
- Adaptation / implementation options:
- Pattern interactions:
- Risks / false-friend test:
- Validation:
- Verdict:
- Confidence:

## Implementation transfer packets
[Top actionable patterns only]

## Rejected patterns / false friends
[High-value negative knowledge]

## Unknowns that can change a verdict
[Only decision-relevant unknowns]

## Handoff packet
[Only when another skill should continue]
```

Surface `REVIEW_REQUIRED` blockers in the executive verdict rather than burying them.

## 2. Pattern card

Minimum useful card:

```text
Pattern ID
Name
Family ID (optional)
Category
Problem
Mechanism
Source evidence IDs
Destination evidence IDs
Transfer conditions
Existing target capability
Transfer mode
Implementation options/path
Interactions
Validation
Verdict
Decision reason
Confidence decomposition
```

## 3. Machine-readable ledger v2

Recommended JSON shape:

```json
{
  "schema_version": "2.0",
  "shape": "SOURCE_TO_TARGET",
  "mode": "STANDARD",
  "as_of": "2026-08-25T21:45:00+02:00",
  "source_targets": [
    {
      "id": "SRC-1",
      "name": "Example",
      "kind": "product",
      "version": "web observed 2026-08-25",
      "observed_at": "2026-08-25T21:00:00+02:00"
    }
  ],
  "destination": {
    "name": "Target Product",
    "kind": "repo_product"
  },
  "evidence": [
    {
      "evidence_id": "E-001",
      "subject": "source",
      "target_id": "SRC-1",
      "source": "https://example.invalid/flow",
      "locator": "settings > recovery state",
      "source_type": "live_product",
      "claim_lane": "source_behavior",
      "claim_state": "OBSERVED",
      "observed_at": "2026-08-25T21:00:00+02:00",
      "note": "Destructive action exposes an undo window.",
      "confidence": 0.95,
      "independence_group": "example-live"
    },
    {
      "evidence_id": "E-101",
      "subject": "destination",
      "target_id": "DEST",
      "source": "target analytics/support/repo",
      "locator": "recovery issue evidence",
      "source_type": "destination_internal",
      "claim_lane": "destination_problem",
      "claim_state": "OBSERVED",
      "observed_at": null,
      "note": "Users cannot recover accidental deletion.",
      "confidence": 0.85,
      "independence_group": "target-support"
    }
  ],
  "patterns": [
    {
      "id": "PT-001",
      "name": "Reversible destructive actions",
      "family_id": null,
      "category": "interaction",
      "problem": "Users need safe recovery from accidental destructive actions.",
      "mechanism": "Delay irreversible commitment and expose a bounded undo path.",
      "source_observation": "Source exposes undo after deletion.",
      "evidence_ids": ["E-001"],
      "target_evidence_ids": ["E-101"],
      "transfer": {
        "problem_fit": 0.9,
        "mechanism_fit": 0.9,
        "source_evidence_strength": 0.9,
        "destination_evidence_strength": 0.8,
        "implementation_feasibility": 0.8,
        "expected_upside": 0.8,
        "reversibility": 0.9,
        "maintenance_fit": 0.8,
        "strategic_fit": 0.8,
        "differentiation": 0.5,
        "dependency_risk": 0.2,
        "complexity_tax": 0.2,
        "opportunity_cost": 0.2,
        "legal_ip_risk": 0.1,
        "security_privacy_risk": 0.1,
        "measurement_risk": 0.2
      },
      "gates": {
        "legal_ip": "clear",
        "security_privacy": "clear"
      },
      "implementation": {
        "transfer_mode": "REIMPLEMENT",
        "target_surfaces": ["delete flow"],
        "prerequisites": ["soft-delete or delayed deletion capability"],
        "steps": ["add reversible state", "surface undo", "instrument recovery"],
        "effort_band": "medium",
        "uncertainty": "medium",
        "success_metric": "recovered accidental deletions / destructive-action support rate",
        "rollback": "disable undo path and retain existing deletion behavior",
        "kill_criteria": "material integrity or permission regression"
      },
      "experiment": null,
      "interactions": {
        "requires": [],
        "enables": [],
        "conflicts_with": [],
        "substitutes_for": [],
        "bundles_with": []
      },
      "confidence": {
        "source": 0.9,
        "mechanism": 0.8,
        "destination": 0.8,
        "execution": 0.75,
        "overall": 0.81
      },
      "verdict": "ADOPT",
      "decision_reason": "Strong target problem evidence and low-risk destination-native reimplementation."
    }
  ]
}
```

Validate persisted ledgers with `scripts/validate_pattern_ledger.py`.

### Field rules the validator enforces

```text
schema_version: "2.0"
shape: SOURCE_ONLY | SOURCE_TO_TARGET | MULTI_SOURCE_TO_TARGET (the last two need destination {name, kind})
mode: SNAPSHOT | STANDARD | DEEP
source_targets[]: id (unique), name, kind
evidence[]:
  evidence_id (unique), source, locator, source_type, note: non-empty
  subject: source | destination
  target_id: a source_targets id, or DEST for destination evidence
  claim_lane: source_behavior | source_implementation | source_rationale | source_outcome
              (source) or destination_problem | destination_existing_capability |
              destination_constraint | destination_baseline (destination)
  claim_state: OBSERVED | INFERRED | HYPOTHESIS | UNKNOWN
  confidence: 0-1
patterns[]:
  id (unique), name, problem, mechanism, source_observation, decision_reason: non-empty
  category: one of the twelve in pattern-transfer.md
  evidence_ids: non-empty, source evidence only
  target_evidence_ids: destination evidence only, may be empty
  transfer: all sixteen dimensions, each 0-1
  gates: {legal_ip, security_privacy}: clear | not_required | review | block | unknown
  implementation:
    transfer_mode: INSPIRE | REIMPLEMENT | INTEGRATE | REUSE_CODE | REUSE_ASSET
    provenance_note: required for REUSE_CODE and REUSE_ASSET
    target_surfaces, prerequisites, steps: string arrays when present
    effort_band, uncertainty: strings when present
    success_metric, rollback, kill_criteria: required for ADOPT
  interactions: {requires, enables, conflicts_with, substitutes_for, bundles_with}: pattern ids
  confidence: {source, mechanism, destination, execution, overall}: each 0-1
  verdict: CANDIDATE | ADOPT | EXPERIMENT | BACKLOG | REJECT | REVIEW_REQUIRED
  experiment: required object for EXPERIMENT, every key non-empty:
    hypothesis, test_type, primary_metric, guardrail, baseline,
    success_rule, timebox_or_sample, kill_criteria, changes_verdict
```

`ADOPT` and `EXPERIMENT` need OBSERVED `destination_problem` evidence, OBSERVED source
behavior or implementation evidence, and clear or `not_required` gates. `ADOPT` also needs
`source_evidence_strength` and `destination_evidence_strength` >= 0.65,
`implementation_feasibility` >= 0.60 and non-empty `steps`. `REVIEW_REQUIRED` needs a
non-clear gate. The validator prints VALID or INVALID with one line per error.

`as_of`, `version`, `observed_at`, `independence_group` and `family_id` are recorded for
readers and synthesis; the validator does not check them.

### Scoring output

`scripts/score_patterns.py` takes one pattern, an array, or a ledger and adds to each
pattern `heuristic_score` (0-100), `gate_state` (clear, review or block; a missing gate
counts as unknown and so review), `suggested_action` (a verdict value) and
`score_components` (`positive`, `penalty`, `target_evidence_ceiling_applied`). Without
`target_evidence_ids` and `destination_evidence_strength` >= 0.35 the suggestion stays
CANDIDATE.

## 4. Confidence decomposition

Do not report one confidence number without knowing what it means.

Use:

- `source` - confidence the source observation/implementation is correctly established;
- `mechanism` - confidence the proposed mechanism explains the relevant behavior/tradeoff;
- `destination` - confidence target problem/fit is established;
- `execution` - confidence the proposed target implementation can be delivered/operated as described;
- `overall` - synthesis, bounded by material critical gaps.

A high source confidence cannot compensate for unknown destination fit.

## 5. Handoff notes

A handoff should contain only accepted teardown outputs and unresolved questions relevant to the downstream skill. Do not pass speculative source architecture as fact.
