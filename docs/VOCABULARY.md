# Shared vocabulary

Several concepts recur across the skills: a verdict, a severity, a confidence
band, a freshness state, a gate status, the status a script returns, and the
envelope kind a step hands on. Each skill spells them in its own
`references/contract.json`, and CW-AIP spells them in `protocol/`. This page
lists every spelling side by side and says why each one differs.

Two rules apply everywhere:

- **A token belongs to its contract.** Write the exact value the owning skill's
  contract lists, in its case, when you name that skill's result. Release
  Readiness says `NO_GO`; AI Council says `NO-GO`. A line about one uses that
  one's spelling.
- **Normalize at the boundary, never in the middle.** When a value crosses into
  an envelope, the envelope's schema decides the spelling (CW-AIP v1 enums are
  upper case, v2 payload enums mostly lower case). A skill's own report keeps
  its own spelling.

`tooling/tests/test_vocabulary_doc.py` reads every table row below and fails
when a row disagrees with the contract or schema it names, or when a contract
gains a verdict, severity, confidence, freshness, gate status, run status or
envelope field that has no row here. Changing a value means changing the
contract, then this page.

## Verdicts

The answer a skill gives to the question it was asked. They differ because the
questions differ; none is a synonym of another.

| Owner | Field | Values | Why it differs |
| --- | --- | --- | --- |
| `ai-council` | `verdict` | `GO` `NO-GO` `TEST` `DEFER` | Strategic decision. `TEST` (run a bounded experiment) has no release equivalent. Hyphenated in its contract; see [Boundary mappings](#boundary-mappings). |
| `release-readiness` | `output:verdict` | `GO` `GO_WITH_CONTROLS` `NO_GO` `DEFER` | Production gate for one named candidate. `GO_WITH_CONTROLS` ships under named controls. |
| `artifact-acceptance` | `output:verdict` | `READY` `READY_WITH_CONTROLS` `NOT_READY` `DEFER` | Acceptance of a document or other artifact against its brief, not a deploy. |
| `web-app-auditor` | `verdict` | `ship` `ship_with_fixes` `do_not_ship` `incomplete` | QA opinion handed to Release Readiness as evidence, not a release verdict. Its validator accepts only these lower-case tokens. |
| `seo-geo-aeo-maxxing` | `verdict` | `PASS` `WEAK` `FAIL` `N/A` `NOT_ASSESSED` | Per-check visibility rating, not a decision. |
| `product-teardown` | `verdict` | `CANDIDATE` `ADOPT` `EXPERIMENT` `BACKLOG` `REJECT` `REVIEW_REQUIRED` | Disposition of one extracted mechanism. |
| `content-roaster` | `review_outcome` | `MATERIAL_FINDINGS` `NO_MATERIAL_FINDINGS` `INSUFFICIENT_EVIDENCE` | Shared roaster pack: a roast reports findings and does not issue a ship or publish decision. |
| `repo-roaster` | `review_outcome` | `MATERIAL_FINDINGS` `NO_MATERIAL_FINDINGS` `INSUFFICIENT_EVIDENCE` | Same shared roaster pack. |
| `science-roaster` | `review_outcome` | `MATERIAL_FINDINGS` `NO_MATERIAL_FINDINGS` `INSUFFICIENT_EVIDENCE` | Same shared roaster pack. |
| `cw-aip-v2/decision.schema.json` | `verdict` | `GO` `NO_GO` `TEST` `DEFER` | Wire form of a Council verdict. |
| `cw-aip-v2/release.schema.json` | `verdict` | `GO` `GO_WITH_CONTROLS` `NO_GO` `DEFER` | Wire form of a release verdict; identical to Release Readiness. |

## Severity

Four families, kept apart on purpose:

- **Review scale** `BLOCKER` `MAJOR` `MINOR` `NOTE`: findings that block,
  matter, or are optional. Five reviewing and gating skills share it.
- **Roaster scales** have three levels, without `NOTE`, and name the top tier
  for their domain: `BLOCKER` for content, `CRITICAL` for code, `FATAL` for
  research.
- **Priority scale** `critical` `high` `medium` `low`: how urgent a roadmap
  item or a competitor change is, rather than how bad a defect is.
- **Materiality** `critical` `material` `supporting`: how much a claim or gap
  matters to a conclusion. Evidence Researcher grades gaps with `minor` instead
  of `supporting`; the two lists are separate constants in its kernel
  (`MATERIALITIES` and `GAP_SEVERITIES`).

| Owner | Field | Values | Why it differs |
| --- | --- | --- | --- |
| `artifact-acceptance` | `findings.severity` | `BLOCKER` `MAJOR` `MINOR` `NOTE` | Review scale. |
| `artifact-acceptance` | `controls.severity` | `MINOR` `NOTE` | A control carries only a minor residual; an open blocking `BLOCKER` or `MAJOR` finding makes the verdict `NOT_READY`. |
| `content-reviewer` | `severity` | `BLOCKER` `MAJOR` `MINOR` `NOTE` | Review scale. |
| `feedback-integrator` | `severity` | `NOTE` `MINOR` `MAJOR` `BLOCKER` | Review scale. |
| `quality-loop-operator` | `severity` | `BLOCKER` `MAJOR` `MINOR` `NOTE` | Review scale. |
| `skill-auditor` | `checks.severity` | `BLOCKER` `MAJOR` `MINOR` `NOTE` | Review scale. |
| `content-roaster` | `severity` | `BLOCKER` `MAJOR` `MINOR` | Roaster, content. |
| `repo-roaster` | `severity` | `CRITICAL` `MAJOR` `MINOR` | Roaster, code. |
| `science-roaster` | `severity` | `FATAL` `MAJOR` `MINOR` | Roaster, research. |
| `release-readiness` | `severity` | `blocker` `critical` `major` `minor` | Release manifest, lower case like the rest of that manifest. Accepted risk cannot clear a `blocker` or `critical` issue. |
| `web-app-auditor` | `findings.severity` | `blocker` `major` `minor` `nit` `n/a` | QA report, lower case like its verdict. `nit` is a confirmed polish defect; `n/a` belongs to a recommendation or a needs-repro item, where no defect is proven. |
| `repo-to-roadmap` | `severity` | `critical` `high` `medium` `low` | Priority scale. |
| `competitive-intelligence` | `output:severity` | `CRITICAL` `HIGH` `MEDIUM` `LOW` `NOISE` | Priority scale for a competitor change; `NOISE` (score 0-24) is not promoted to an intelligence event. |
| `evidence-researcher` | `contradictions.severity` | `critical` `material` `supporting` | Materiality. |
| `evidence-researcher` | `gaps.severity` | `critical` `material` `minor` | Materiality, with `minor` for the lowest gap. |
| `cw-aip-v2/finding.schema.json` | `severity` | `blocker` `high` `medium` `low` `info` | Wire form of a finding. No skill maps onto it yet; see [Boundary mappings](#boundary-mappings). |

## Confidence

Every band is `high` `medium` `low`. Content Reviewer alone writes it in
capitals, matching the rest of its upper-case report. The CW-AIP v1 core
leaves `confidence` free (a number or a band), so no envelope rejects either
case.

| Owner | Field | Values | Why it differs |
| --- | --- | --- | --- |
| `cometweb-context` | `confidence` | `high` `medium` `low` | |
| `content-roaster` | `confidence` | `high` `medium` `low` | |
| `evidence-researcher` | `confidence` | `high` `medium` `low` | |
| `repo-roaster` | `confidence` | `high` `medium` `low` | |
| `science-roaster` | `confidence` | `high` `medium` `low` | |
| `web-app-auditor` | `confidence` | `high` `medium` `low` | |
| `web-app-auditor` | `findings.confidence` | `high` `medium` `low` | |
| `content-reviewer` | `confidence` | `HIGH` `MEDIUM` `LOW` | Upper case, like its report. |
| `cw-aip-v2/context.schema.json` | `confidence` | `high` `medium` `low` | |

## Freshness

The core states are `CURRENT` `STALE` `SUPERSEDED` `UNKNOWN`; skills add the
states their decision needs.

| Owner | Field | Values | Why it differs |
| --- | --- | --- | --- |
| `longform-publisher` | `freshness` | `CURRENT` `NEAR_EXPIRY` `STALE` `SUPERSEDED` `UNKNOWN` `NOT_REQUIRED` | Adds `NEAR_EXPIRY` (usable, refresh soon) and `NOT_REQUIRED` (claim is not time-sensitive). |
| `product-operator` | `freshness_status` | `CURRENT` `NEAR_EXPIRY` `STALE` `SUPERSEDED` `UNKNOWN` `NOT_REQUIRED` | Same set. |
| `repo-to-roadmap` | `freshness` | `CURRENT` `NEAR_EXPIRY` `NOT_TIME_SENSITIVE` `STALE` `SUPERSEDED` `UNKNOWN` | `NOT_TIME_SENSITIVE` is the same idea as `NOT_REQUIRED`, named for a project fact rather than a citation. Kept: renaming it would make the kernel reject baselines already written with it. |
| `content-writer` | `freshness_status` | `CURRENT` `NEAR_EXPIRY` | Only the states a freshness-sensitive `SUPPORTED` claim may carry. |
| `release-readiness` | `freshness` | `current` `stale` `mismatched` `unknown` | Evidence against a pinned candidate: `mismatched` means it was gathered on another build. Lower case, like its manifest. |
| `cometweb-context` | `freshness` | `fresh` `aging` `stale` `unknown` | Age of a context source, matching the v2 context envelope. |
| `skill-orchestrator-multiagent` | `freshness` | `CURRENT` `NOT_YET_EFFECTIVE` `STALE` `SUPERSEDED` `UNKNOWN` | The CW-AIP v1 core set, checked on every envelope. |
| `cw-aip-v1/schemas/envelope.core.schema.json` | `freshness` | `CURRENT` `NOT_YET_EFFECTIVE` `STALE` `SUPERSEDED` `UNKNOWN` | v1 wire form. |
| `cw-aip-v2/context.schema.json` | `freshness` | `fresh` `aging` `stale` `unknown` | v2 wire form for context sources. |

## Gate status

One governance gate vocabulary, `NOT_REQUIRED` `CLEAR` `CLEAR_WITH_CONTROLS`
`COUNSEL_REQUIRED` `BLOCK`.

| Owner | Field | Values | Why it differs |
| --- | --- | --- | --- |
| `ai-council` | `gate_statuses` | `NOT_REQUIRED` `CLEAR` `CLEAR_WITH_CONTROLS` `COUNSEL_REQUIRED` `BLOCK` | The reference set. |
| `release-readiness` | `governance_gates.status` | `not_required` `clear` `clear_with_controls` `counsel_required` `block` | Same set, lower case like its manifest. |
| `repo-to-roadmap` | `gate_status` | `NOT_REQUIRED` `CLEAR` `CLEAR_WITH_CONTROLS` `UNVERIFIED` `BLOCK` | No `COUNSEL_REQUIRED`; adds `UNVERIFIED` for a gate nobody has checked yet. |
| `cw-aip-v2/decision.schema.json` | `gates.status` | `NOT_REQUIRED` `CLEAR` `CLEAR_WITH_CONTROLS` `COUNSEL_REQUIRED` `BLOCK` | Wire form. |

## Run status

What a skill's script returns. Each describes that script's own state machine,
so the sets are not meant to line up; the shared words keep one meaning:
`INVALID` means the input broke the contract, `BLOCKED` means a gate stops the
next step, `DEFER` means decide later with named evidence, and
`CHANGES_REQUIRED` means the work must change before it passes.

| Owner | Field | Values | Why it differs |
| --- | --- | --- | --- |
| `ai-council` | `output:status` | `VALID` `WATCH` `REOPEN` `REFRESH_REQUIRED` `STALE` `SUPERSEDED` `DRAFT` `CURRENT` `NEAR_EXPIRY` `NOT_YET_EFFECTIVE` `UNKNOWN` `CLEAR` | Validity of a stored decision and of its evidence. |
| `ai-humanize` | `output:status` | `automated_pass` `review` `missing_output` `invalid_output` | Rewrite check; lower case like its report. |
| `benchmark-curator` | `output:status` | `READY_TO_FREEZE` `NEEDS_REBALANCE` `NEEDS_REVISION` `CONTAMINATED` `INVALID` | Corpus freeze gate. |
| `brief-architect` | `output:status` | `READY` `PROVISIONAL` `BLOCKED` `INVALID` `CHANGED` `UNCHANGED` | Brief readiness, plus diff results. |
| `content-reviewer` | `output:status` | `REVIEWED` `CHANGES_REQUIRED` `INVALID` | |
| `content-writer` | `output:status` | `PASS` `FAIL` | |
| `customer-ops` | `output:status` | `PASS` `WARN` `BLOCK` `OK` `AT_RISK` `BREACHED` `MET` `PAUSED` `FIXED` `UNKNOWN` `OPEN` `DUE_SOON` `OVERDUE` `FULFILLED` `RENEGOTIATED` `CANCELLED` `FINDINGS` `NO_OBVIOUS_FINDINGS` `error` | One value set across the kernel's subcommands; `error` is the CLI failure. |
| `design-partner-finder` | `output:status` | `PRIORITY_DISCOVERY` `DISCOVERY` `WATCHLIST` `HOLD_VERIFY` `REJECT` `PARTNER_READY` `ALIGNMENT_REQUIRED` `PAUSE` `CONTINUE` `REPAIR` `EXIT_REVIEW` `CONVERSION_CANDIDATE` | Candidate and partnership states. |
| `ebook-publisher` | `output:result` | `RECORDS_COMPLETE` `BLOCKED` `INPUT_ERROR` `INITIALIZED_DRAFT` | |
| `feedback-integrator` | `output:status` | `NO_SIGNAL` `WATCH` `PROPOSED` `PROMOTE` `HOLD` `RETIRED` `INVALID` | |
| `product-operator` | `output:status` | `PASS` `WARN` `FAIL` | |
| `quality-loop-operator` | `output:status` | `READY_FOR_NEXT` `CHANGES_REQUIRED` `NEEDS_RECONCILIATION` `BLOCKED` `READY_FOR_ROLLOUT` `COMPLETE` `INVALID` | |
| `repair-operator` | `output:status` | `VALID` `INVALID` | |
| `rubric-designer` | `output:status` | `READY_TO_FREEZE` `NEEDS_REVISION` `INVALID` | Same freeze words as `benchmark-curator`. |
| `skill-auditor` | `output:status` | `PASS` `CHANGES_REQUIRED` `DEFER` `INVALID` | |
| `skill-evaluator` | `output:status` | `IMPROVED` `NO_MATERIAL_CHANGE` `REGRESSION` `TRADEOFF` `DESIGN_READY` `INSUFFICIENT_EVIDENCE` `INVALID` | |

## Envelope kinds

| Owner | Field | Values | Why it differs |
| --- | --- | --- | --- |
| `skill-orchestrator` | `output:envelope_out` | `ArtifactEnvelope` `EvidenceEnvelope` `DecisionHandoff` `FindingEnvelope` `SpecialistHandoff` `SnapshotMetadata` | Planned per step; the v1 kinds the archetypes use. |
| `skill-orchestrator-multiagent` | `output:envelope_out` | `ArtifactEnvelope` `EvidenceEnvelope` `DecisionHandoff` `FindingEnvelope` `SpecialistHandoff` `SnapshotMetadata` | Same planner. |
| `cw-aip-v1/schemas/envelope.core.schema.json` | `type` | `ArtifactEnvelope` `EvidenceEnvelope` `FindingEnvelope` `DecisionHandoff` `SpecialistHandoff` `SnapshotMetadata` | v1 kinds. |
| `cw-aip-v2/core.schema.json` | `type` | `ContextEnvelope` `EvidenceEnvelope` `FindingEnvelope` `DecisionEnvelope` `RoadmapEnvelope` `ReleaseEnvelope` `SpecialistHandoff` `ArtifactEnvelope` `SnapshotMetadata` | v2 splits `DecisionHandoff` into `DecisionEnvelope` (Council) and `ReleaseEnvelope` (Release Readiness), and adds context and roadmap kinds. |

Which kind a step emits: Evidence Researcher `EvidenceEnvelope`; Web App
Auditor `FindingEnvelope`; AI Council and Release Readiness `DecisionHandoff`
in v1, `DecisionEnvelope` and `ReleaseEnvelope` in v2; Competitive Intelligence
`SnapshotMetadata`; Product Operator `SpecialistHandoff`; CometWeb Context
`ContextEnvelope` (v2 only). The orchestrator's gate accepts a v2
`DecisionEnvelope` or `ReleaseEnvelope` where its plan says `DecisionHandoff`.

## Not applicable

Five spellings for one idea, each fixed by its contract: `N/A`
(`seo-geo-aeo-maxxing` verdict, `artifact-acceptance` state, `content-reviewer`
coverage), `N_A` (`skill-auditor` checks), `na` (`release-readiness` checks),
`n/a` (`web-app-auditor` severity) and `NOT_APPLICABLE` (the roaster ledgers
and `repo-to-roadmap`). Use the owner's spelling; do not convert between them
inside a report.

## Boundary mappings

- **Council verdict on a v2 `DecisionEnvelope`.** AI Council's contract says
  `NO-GO`; the v2 decision schema accepts `NO_GO`. A producer writing the
  envelope writes `NO_GO` and keeps `GO`, `TEST` and `DEFER` unchanged; the
  Council kernel's `gate` reports that spelling as `envelope_verdict`. The
  test checks that this one substitution maps the Council set onto the schema
  set exactly.
- **Gate status into v2.** Release Readiness writes gate statuses in lower case;
  the v2 decision schema's `gates[].status` is upper case. The orchestrator's
  gate already compares them case-insensitively when it rejects an authorizing
  verdict.
- **Finding severity into v2.** `cw-aip-v2/finding.schema.json` uses
  `blocker` `high` `medium` `low` `info`, which matches no skill's scale. No
  mapping is defined, so no skill emits a v2 `FindingEnvelope` yet; Web App
  Auditor findings travel as v1 `FindingEnvelope`, whose payload is the
  producer's own.
