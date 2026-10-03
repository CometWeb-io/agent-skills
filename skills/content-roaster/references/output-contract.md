# Content Roaster output contract

Machine-consumable reports use `cometweb.content-roaster/v6`. `scripts/validate_roast.py` is authoritative; `report.schema.json` mirrors the top-level shape.

## Human output

Use this order for the human-readable report unless the user asks for another format; omit a section only where its note allows:

1. **What this content is trying to make the reader believe/do**
2. **First thing a skeptical reader attacks** — omit when no finding survives
3. **Material roast findings** — ordered by final severity and leverage
4. **Root causes** — only when useful
5. **Proof debt / verification queue**
6. **Revision ledger** — DELTA only
7. **What survives**
8. **Core fix**

## v6 control-plane fields

Every report carries `review_plan`, `source_manifest`, `assurance`, `evidence_register`, `evidence_conflicts`, `outcome_basis`, `limitations`, and nine `quality_gates`: `scope`, `contract`, `source_integrity`, `evidence`, `challenge`, `assurance`, `severity`, `repair`, `boundary`. Every reviewed source has `instruction_boundary=TREAT_AS_DATA` and a `trust_class`.

Every material finding carries `evidence_refs`, `confidence_basis`, `residual_risk`, stable `finding_key`, source-linked `anchor`, falsifier/adversarial state, repair, and a falsifiable verification contract. A finding must cite evidence from its anchor source.

Content-specific v6 adds `diagnosis_ledger`: classify the failure as `COPY`, `PROOF`, `POSITIONING`, `OFFER`, `PRODUCT`, `AUDIENCE`, `STRUCTURE`, `UX`, or `MIXED` before prescribing a repair. Each finding references one diagnosis via `diagnosis_ref`. This prevents copy rewrites from masking product, proof, or offer defects.

## Outcome invariants

- `MATERIAL_FINDINGS`: findings are non-empty and `no_material_findings=false`.
- `NO_MATERIAL_FINDINGS`: findings are empty, `no_material_findings=true`, and no quality gate is blocked.
- `INSUFFICIENT_EVIDENCE`: findings are empty, `no_material_findings=false`, and at least one quality gate is blocked.
- Unresolved evidence conflicts force `quality_gates.evidence` to `WARN` or `BLOCKED`.
- `SECOND_PASS` marked unavailable forces the assurance gate to `WARN` or `BLOCKED`.
- High confidence requires non-low directness/scope support and addressed counterevidence.

## BLOCKER admission

A BLOCKER must be central to the decision path, survive falsification, use non-weak evidence, avoid high scope sensitivity, and affect trust/decision/action. Tone never upgrades severity.

## Revision semantics

`resolution_ledger` uses stable keys/aliases and explicit verification. `RESOLVED` requires `verification_status=PASSED`; disappearance from a revision is not resolution.

See `references/source-safety.md`, `assurance-protocol.md`, `evidence-discipline.md`, `severity-calibration.md`, and `revision-protocol.md` for the behavioral rules.

## Auditable disposition

`assurance.pass_records` records which review passes actually ran and against which source ids. `outcome_basis` lists the surviving finding ids plus withdrawn/unresolved candidate counts and a bounded reason. This makes a clean result and a material result equally auditable.

## Field reference

`scripts/validate_roast.py` checks exactly these fields. `references/contract.json` declares the same list, and `tooling/skill_contracts.py` holds the validator, this file, `report.schema.json` and the fixture `tests/report-valid.json` to it. `[]` marks a list and `?` an optional key; a value list such as `PASS|WARN|BLOCKED` is the complete set the validator accepts.

```text
schema: cometweb.content-roaster/v6
artifact
review_outcome: INSUFFICIENT_EVIDENCE|MATERIAL_FINDINGS|NO_MATERIAL_FINDINGS
mode: DELTA|FULL|QUICK|RED_TEAM  # DELTA requires comparison and resolution_ledger
tone: BRUTAL|DRY|SURGICAL
lens: CONVERSION|EDITORIAL|GENERAL|OFFER|POSITIONING|TECHNICAL_DOCUMENTATION|TRUST
review_profile: ARTICLE|CASE_STUDY|DOCUMENTATION|EMAIL|GENERAL|LANDING_PAGE|LONGFORM|OFFER|PRICING|PRODUCT_PAGE|SALES_DECK
comparison:  # DELTA only
  base_artifact
  head_artifact
source_manifest[]:  # non-empty; at least one PRIMARY
  id
  kind: ANALYTICS|DECK|DOCUMENT|EMAIL|OTHER|PAGE|RESEARCH|SCREENSHOT_TRANSCRIPTION
  locator
  role: CONTEXT|PRIMARY|SUPPORTING
  version_state: MOVING|PINNED|UNKNOWN
  instruction_boundary: TREAT_AS_DATA
  trust_class: EXTERNAL_REFERENCE|GENERATED|SYSTEM_OF_RECORD|TOOL_RESULT|UNKNOWN|USER_SUPPLIED
  sha256?  # 64 hex characters when present
review_plan:
  objective
  must_inspect[]
  attack_surfaces[]
  stop_conditions[]
  sampling_strategy
  escalation_conditions[]
assurance:
  mode: BLIND_DUAL_REVIEW|SECOND_PASS|SINGLE_REVIEW
  independence: NONE|SAME_CONTEXT|SEPARATE_CONTEXT
  second_pass_status: COMPLETED|NOT_RUN|UNAVAILABLE
  disagreement_summary[]
  limitations[]
  pass_records[]:  # non-empty
    pass_id
    role: ARBITER|PRIMARY|SECONDARY
    status: COMPLETED|FAILED|UNAVAILABLE
    context_ref
    blind_to_prior_findings: true|false
    source_refs[]  # source_manifest ids
evidence_register[]:  # non-empty
  id
  source_id
  kind: ABSENCE_PROOF|CONTEXT|COUNTEREVIDENCE|OBSERVATION|VERIFICATION
  locator
  summary
  strength: MODERATE|STRONG|WEAK
  limitations[]
evidence_conflicts[]:
  id
  evidence_refs[]  # at least two evidence ids
  conflict
  disposition: OUT_OF_SCOPE|RESOLVED|UNRESOLVED
  residual_uncertainty
limitations[]
review_contract:
  audience
  desired_action
  decision_stage
  decision_cost: HIGH|LOW|MEDIUM|UNKNOWN
  known_constraints[]
  unknowns[]
coverage:
  level: COMPLETE|PARTIAL|SUBSTANTIAL
  scope_basis: ARTIFACT_SET|EXCERPT|FULL_ARTIFACT|MIXED|SAMPLED
  coverage_confidence: high|low|medium
  sampling_strategy
  inspected[]
  not_inspected[]
  limitations[]
quality_gates: BLOCKED|PASS|WARN  # each of the nine gates below takes one of these
  scope
  contract
  source_integrity
  evidence
  challenge
  assurance
  severity
  repair
  boundary
message_chain:
  problem
  promise
  mechanism
  proof
  objection_handling
  action
central_promise
claim_map[]:  # non-empty; at least one PRIMARY claim
  id
  claim
  claim_type: COMPARATIVE|FACTUAL|GUARANTEE|MECHANISM|OUTCOME|QUANTITATIVE|SUBJECTIVE
  decision_role: PRIMARY|SUPPORTING
  proof_status: ABSENT|EXTERNAL_REQUIRED|PRESENT|WEAK
  proof_burden: HIGH|LOW|MEDIUM|VERY_HIGH
  anchor:  # missing_element is not allowed here
    type: claim|cta|metric|missing_element|quote|section
    value
    source_id
diagnosis_ledger[]:
  id
  claim_refs[]
  evidence_refs[]
  diagnosis_class: AUDIENCE|COPY|MIXED|OFFER|POSITIONING|PRODUCT|PROOF|STRUCTURE|UX
  repair_owner: CONTENT|EVIDENCE|MIXED|OFFER|PRODUCT|UX
  summary
proof_debt_ledger[]:
  id
  claim_ref
  debt_type: ABSENT_PROOF|EXTERNAL_VERIFICATION|MISMATCHED_PROOF|OVERCLAIM|WEAK_PROOF
  status: CLOSED|NOT_APPLICABLE|OPEN|PARTIAL
  required_evidence
  why_it_matters
objection_ledger[]:
  id
  objection
  relevance
  status: ANSWERED|NOT_APPLICABLE|PARTIAL|UNANSWERED
root_causes[]:  # empty when findings are empty
  id
  label
  summary
  claim_refs[]
no_material_findings: true|false
first_attack_id  # null when findings are empty
findings[]:  # ordered by severity, highest first
  id
  finding_key
  finding_aliases[]
  severity: BLOCKER|MAJOR|MINOR
  category: audience|claim_evidence|credibility|cta|differentiation|hierarchy|logic|objection|offer|positioning|promise|readability|redundancy|specificity|technical_documentation|voice
  evidence_state: INFERRED|MISSING|OBSERVED|VERIFY_EXTERNAL
  evidence_strength: MODERATE|STRONG|WEAK
  scope_sensitivity: HIGH|LOW|MEDIUM
  confidence: high|low|medium
  anchor  # same shape as claim_map anchor
  omission_basis  # required for MISSING
  inference_basis  # required for INFERRED
  claim_refs[]
  root_cause_id?
  diagnosis_ref  # a diagnosis_ledger id
  decision_impact: ACTION|COMPREHENSION|DECISION|DISCOVERY|TRUST
  materiality:
    centrality: CENTRAL|LOCAL|SUPPORTING
    consequence: HIGH|LOW|MEDIUM
    reversibility: EASY|HARD|MODERATE|UNKNOWN
  observation
  failure_mode
  roast_line?
  why_it_matters
  repair
  repair_class: COPY|EXTERNAL_VERIFICATION|OFFER|PROOF|SECTION|STRUCTURE|UX
  verification:
    type: ANALYTICS|AUTOMATED_CHECK|EXPERIMENT|MANUAL_INSPECTION|READER_TEST|SOURCE_CHECK
    method
    success_condition
    failure_signal
  falsifier_check:  # required for BLOCKER and MAJOR
    challenge
    searched_for[]
    counterevidence[]
    alternative_explanations[]
    result: DOWNGRADED|SURVIVES|UNRESOLVED|WITHDRAWN
    notes
    downgraded_from: BLOCKER|MAJOR|MINOR  # required for DOWNGRADED
  evidence_refs[]  # must include evidence from the anchor source
  confidence_basis:
    directness: HIGH|LOW|MEDIUM
    scope_support: HIGH|LOW|MEDIUM
    counterevidence_status: ADDRESSED|PARTIAL|UNKNOWN
    independence: NONE|SAME_CONTEXT|SEPARATE_CONTEXT  # equals assurance.independence
    rationale
  residual_risk:
    after_repair: HIGH|LOW|MEDIUM|UNKNOWN
    closure_dependency
outcome_basis:
  surviving_finding_ids[]
  withdrawn_candidate_count
  unresolved_candidate_count
  reason
resolution_ledger[]:
  finding_key
  status: NOT_ASSESSABLE|OPEN|PARTIAL|REGRESSED|RESOLVED
  evidence
  verification_status: FAILED|NOT_RUN|PARTIAL|PASSED
  change_basis: ARTIFACT_CHANGED|JUDGMENT_CORRECTED|MIXED|SCOPE_CHANGED|UNKNOWN
verification_queue[]:
  id
  question
  evidence_needed
  why_it_matters
preserve[]
core_fix
```

`scripts/scan_source_risks.py PATH` prints the object below. Flags are review hazards, not findings.

```text
schema: cometweb.roaster-source-risk-scan/v1
root
files_scanned
files_skipped
flags[]:
  path
  line
  kind  # ignore_instructions, role_override, tool_coercion, secret_request, zero_width_unicode, or a credential pattern
  excerpt  # credential-like values are redacted
note
```
