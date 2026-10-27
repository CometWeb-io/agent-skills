# Choose an owner and a small installation

Start with the native model. Add a skill when the task needs its maintained
source bindings, executable checks or receiving contract. Routine editing,
planning and review do not require a specialist process merely because a matching
package exists. Installing the catalog does not mean loading every skill.

## Decision tree

1. **Missing or unstable requirements?** Clarify the task directly. Use
   `brief-architect` when a reusable formal brief or receiving contract is needed.
2. **Missing evidence for a material claim?** Use `evidence-researcher`.
   A supplied document and an admitted Evidence Pack are different inputs.
3. **Need to produce or change an artifact?** Use `content-writer` for an
   informational draft, `ai-humanize` for a requested rewrite, `ebook-publisher`
   for an ebook build, or `longform-publisher` for manuscript/format/edition
   control. Plain proofreading can be done without a skill.
4. **Need an audit?** Match the object and purpose: `content-reviewer` for
   editorial or adversarial content review (`content-roaster` is its compatibility entry),
   `science-roaster` for scientific validity, `repo-roaster` for repository
   failure modes, `web-app-auditor` for observed app behavior, or `skill-auditor`
   for a skill package. These reviews have different contracts.
5. **Accepted findings need repair?** Use `repair-operator` within the authorized
   scope, then return fresh evidence to the relevant reviewer or acceptance owner.
6. **Need a final verdict?** Use `artifact-acceptance` for a knowledge artifact,
   or `release-readiness` for a pinned software candidate and environment.
   `ai-council` owns consequential decisions only when explicitly requested.
7. **Need ongoing operations?** Choose the corresponding product, portfolio,
   customer, competitor or research-program owner in the map below. A whole-repo
   baseline belongs to `repo-to-roadmap`; extracting a product mechanism belongs
   to `product-teardown`.
8. **Need several owners?** `skill-orchestrator` sequences specialist work;
   `quality-loop-operator` governs a frozen quality policy and its acceptance
   stages. For behavioral comparisons use `skill-evaluator`, with
   `rubric-designer` and `benchmark-curator` when the rubric/corpus is missing.
   `feedback-integrator` synthesizes repeated failures after runs.

An unclear choice needs a scope decision, not automatic activation of every
neighboring skill. The [deterministic router](ROUTING.md) is a separate proxy;
this map does not measure native model discovery.

## Installation selections

These are lists of existing packages for the current
[selective installers](../INSTALL.md), not new skill packages. Pick the smallest
selection covering the requested work; add an actual downstream owner when its
step is required. Handoffs do not install consumers automatically.

There is no default multi-skill core. The following is an optional contract-heavy
workflow selection, not a requirement or evidence of superiority over the model:
`brief-architect`, `evidence-researcher`, `skill-orchestrator`.

```bash
./scripts/install-codex.sh --skill brief-architect --skill evidence-researcher --skill skill-orchestrator
```

| Domain selection | Packages to select |
| --- | --- |
| Editorial | `content-writer`, `ai-humanize`, `content-reviewer`, `repair-operator`, `artifact-acceptance` |
| Publication | `ebook-publisher`, `longform-publisher` |
| Product and customers | `repo-to-roadmap`, `product-operator`, `product-teardown`, `design-partner-finder`, `customer-ops` |
| Market monitoring | `competitor-profiling`, `competitive-intelligence`, `seo-geo-aeo-maxxing` |
| Engineering and release | `web-app-auditor`, `repo-roaster`, `release-readiness` |
| Research program | `research-program-operator`, `science-roaster` |
| Skill evaluation | `skill-auditor`, `rubric-designer`, `benchmark-curator`, `skill-evaluator`, `feedback-integrator` |
| Decisions and portfolio | `portfolio-operator`, `ai-council` |
| Workflow control | `quality-loop-operator`, `skill-orchestrator`, `skill-orchestrator-multiagent` |

For example, select the contract and editorial owners required by a particular workflow:

```bash
./scripts/install-codex.sh --skill brief-architect --skill evidence-researcher --skill skill-orchestrator --skill content-writer
```

The same `--skill` arguments work with the other host installers listed in
[INSTALL.md](../INSTALL.md). Use `--dry-run` to preview.
`ai-humanize` and `quality-loop-operator` are optional workflow stages, not default
rewrite/review passes. A requested rewrite may be handled directly; use the former
when its fidelity/Unicode tools are useful, and the latter for an explicit quality
policy and finding lifecycle. Installed Council availability does not invoke the Council or
grant permission for external actions. Standalone [context resources](../resources/context/README.md)
retain source maps and public/private/project boundaries without adding a skill or preflight.

`repo-roaster` is an optional evidence checklist and tooling package, not a routine
extra review pass. Use it when that checklist or its inventory/scanner helpers are needed;
the package does not establish an advantage over a direct model review.

`science-roaster` 6.2.0 is also an optional methodology and evidence checklist.
Use it for relevant scientific risks; its comparative advantage remains unestablished.

`content-reviewer` 1.8.0 is an optional evidence and repair-verification checklist,
not a default extra review pass. Its comparative advantage over direct model
review remains unestablished; use it when the checklist or a receiving contract is useful.

`content-roaster` is an alias for `content-reviewer` with the ADVERSARIAL profile
and retained v6 tools. Select it when preserving an existing call or v6 consumer;
ordinary adversarial prose can use the canonical reviewer directly. Review/v1
and roaster/v6 remain distinct; see [migration and compatibility](CONTENT-REVIEW-COMPATIBILITY.md).

`skill-orchestrator-multiagent` is an alias package for the canonical
`skill-orchestrator` owner with isolated specialist execution; its packaged
payload builder is needed for that interface. It is not a second planning owner. Select `skill-orchestrator` together with
its alias even when omitting other foundation packages. Selective installers now
include canonical alias dependencies automatically.

## Evidence boundaries

Package metadata, schemas, helpers and offline tests describe maintained contracts.
They do not establish task-success lift, native host acceptance or a qualified
default. Read each package's MATURITY.json and the scoped experiment evidence;
absence of comparative evidence is not proof of equivalence or usefulness.
Retire an instruction wrapper only with a bounded reason and a consumer migration;
retain reusable tools and source bindings independently when appropriate.

## Owner → result → next consumer

Each owner remains standalone. The next consumer is a possible subsequent task,
not an automatic dependency, a deployment permission or a promise of wire
compatibility. Read the linked producer contract and the consumer's admission
contract before passing data. Preserve IDs, source provenance and the producer's
original result; the consumer decides its own status.

CW-AIP [v2](../protocol/cw-aip-v2/README.md) and
[v1](../protocol/cw-aip-v1/cw-interchange-v1.md) have distinct wire contracts.
Some outputs are prose plus a sidecar, and the roaster handoff contract currently
has no validator. A common artifact/envelope name alone establishes no semantic
admission or migration. Where the map names a human reviewer, do not substitute
a fictitious skill.

| Owner | Result and producer contract | Possible next consumer and intake | Evidence basis |
| --- | --- | --- | --- |
| [`ai-council`](../skills/ai-council/SKILL.md) | [Decision Snapshot; DecisionEnvelope / DecisionHandoff](../skills/ai-council/references/output-contract.md) | [repo-to-roadmap](../skills/repo-to-roadmap/references/handoffs.md); decision_ref + conditions; never implementation evidence | documented receiving contract; explicit-only |
| [`ai-humanize`](../skills/ai-humanize/SKILL.md) | [Finished rewritten text / body.md; audit findings](../skills/ai-humanize/SKILL.md) | [ebook-publisher](../skills/ebook-publisher/references/integration.md); fidelity-protected prose; no new factual verification | documented receiving contract |
| [`artifact-acceptance`](../skills/artifact-acceptance/SKILL.md) | [cometweb.artifact-acceptance/v1 acceptance payload/report](../skills/artifact-acceptance/references/output-contract.md) | [quality-loop-operator](../skills/quality-loop-operator/references/output-contract.md); candidate/brief-bound acceptance verdict at acceptance stage | documented stage contract + local sidecar controls |
| [`benchmark-curator`](../skills/benchmark-curator/SKILL.md) | [Frozen benchmark revision/hash, corpus fingerprint, split/leakage/provenance](../skills/benchmark-curator/references/output-contract.md) | [skill-evaluator](../skills/skill-evaluator/references/output-contract.md); benchmark_hash + rubric_hash bound experiment input | documented receiving contract + local hash guards |
| [`brief-architect`](../skills/brief-architect/SKILL.md) | [cometweb.artifact-brief/v1 ArtifactBrief](../skills/brief-architect/references/output-contract.md) | [content-writer](../skills/content-writer/SKILL.md); brief constraints/invariants before draft | documented receiving contract |
| [`competitive-intelligence`](../skills/competitive-intelligence/SKILL.md) | [Material delta brief; baseline/snapshot/delta/watch metadata](../skills/competitive-intelligence/references/output-contract.md) | [evidence-researcher → ai-council (explicit request)](../skills/skill-orchestrator/scripts/orchestrate_kernel.py); SnapshotMetadata in competitive_then_council, followed by evidence admission | explicit executable archetype; external facts not proved |
| [`competitor-profiling`](../skills/competitor-profiling/SKILL.md) | [Competitor profile + competitive_intelligence_handoff](../skills/competitor-profiling/references/output-contract.md) | [competitive-intelligence](../skills/competitive-intelligence/references/integrations.md); normalize factual profile fields into CI snapshot before delta computation | documented receiving mapping; manual normalization |
| [`content-reviewer`](../skills/content-reviewer/SKILL.md) | [cometweb.content-review/v1 review with stable findings and coverage](../skills/content-reviewer/references/output-contract.md) | [repair-operator](../skills/repair-operator/SKILL.md); accepted findings become repair inputs; review is not final acceptance | documented receiving contract |
| [`content-roaster`](../skills/content-roaster/SKILL.md) → `content-reviewer` | [Retained cometweb.content-roaster/v6 report; cometweb.roaster-handoff/v2](../skills/content-roaster/references/output-contract.md) | [repair-operator](../skills/repair-operator/SKILL.md); accepted findings only, retain evidence gaps | compatibility alias; manual handoff, no roaster handoff validator |
| [`content-writer`](../skills/content-writer/SKILL.md) | [Finished prose + cometweb.content-draft/v1 sidecar](../skills/content-writer/references/output-contract.md) | [content-reviewer](../skills/content-reviewer/SKILL.md); draft + brief/claim/invariant evidence before review | documented receiving contract |
| [`customer-ops`](../skills/customer-ops/SKILL.md) | [Customer Ops Queue / Case / Incident / Handoff Watch / Account360; case graph](../skills/customer-ops/references/outputs.md) | [portfolio-operator](../skills/portfolio-operator/references/delegation.md); severity, commitments, customer-visible state, next operational action | documented receiving contract; external actions separate |
| [`design-partner-finder`](../skills/design-partner-finder/SKILL.md) | [Learning Contract; Candidate Dossier; Readiness / Cohort Portfolio / Activation Review](../skills/design-partner-finder/references/output-contract.md) | [portfolio-operator](../skills/portfolio-operator/references/delegation.md); candidate readiness affects allocation; outreach still requires authorization | documented receiving contract |
| [`ebook-publisher`](../skills/ebook-publisher/SKILL.md) | [Requested ebook + editable source, evidence ledger, QA report; cometweb.ebook/v1](../skills/ebook-publisher/SKILL.md) | [Author/user; publication-step caller](../skills/ebook-publisher/references/integration.md); finished publication to user; orchestrator may call publication step, not certify it | human terminal + documented producer-side route |
| [`evidence-researcher`](../skills/evidence-researcher/SKILL.md) | [Evidence Pack; Material Claim Ledger; EvidenceEnvelope](../skills/evidence-researcher/references/output-contract.md) | [ai-council / product-operator / repo-to-roadmap / release-readiness](../skills/evidence-researcher/references/integrations.md); Council/operator/roadmap/release policies admit only task-relevant current claims | documented mappings + shared CW-AIP validation; external truth excluded |
| [`feedback-integrator`](../skills/feedback-integrator/SKILL.md) | [Improvement backlog; proposals/watch/retired/invalid with root-layer evidence](../skills/feedback-integrator/references/output-contract.md) | Maintainer/user; maintainer/user decides changes; no autonomous self-modification consumer proved | human terminal; no verified in-catalog ingestion adapter |
| [`longform-publisher`](../skills/longform-publisher/SKILL.md) | [Finished manuscript/report/playbook; publication control summary; render-manifest projection](../skills/longform-publisher/references/output-contract.md) | Author/user; requested artifact goes to author/user; render-manifest does not substitute manuscript | human terminal; publication authorization separate |
| [`portfolio-operator`](../skills/portfolio-operator/SKILL.md) | [portfolio-report.json; allocation lanes and capacity conflicts](../skills/portfolio-operator/references/output-contract.md) | [Designated specialist → portfolio-operator](../skills/portfolio-operator/references/delegation.md); narrow Goal/Evidence/Question/Return-contract dispatch; re-entry only on material allocation change | documented bidirectional delegation; no automatic specialist ingestion proved |
| [`product-operator`](../skills/product-operator/SKILL.md) | [operator-report.json; VERIFY/DECISION/NOW/NEXT/STOP critical path](../skills/product-operator/references/output-contract.md) | [portfolio-operator](../skills/portfolio-operator/references/delegation.md); current product critical path and blockers as portfolio input | documented receiving contract |
| [`product-teardown`](../skills/product-teardown/SKILL.md) | [Product Teardown; Pattern Ledger / Recon Map; implementation transfer packets](../skills/product-teardown/references/output-contract.md) | [product-operator / repo-to-roadmap](../skills/product-teardown/references/composition.md); bounded pattern transfers to operator/roadmap; observed pattern is not implementation proof | documented producer-side routes; consumer admission not automatically proved |
| [`quality-loop-operator`](../skills/quality-loop-operator/SKILL.md) | [Quality Run Brief; quality sidecar stage/lock/conflict/coverage state](../skills/quality-loop-operator/SKILL.md) | [Required specialist stage / user](../skills/quality-loop-operator/references/output-contract.md); select specialist stages and check exact prior rubric/benchmark hashes; software release NOT_OWNED | documented/executable local quality state; human terminal |
| [`release-readiness`](../skills/release-readiness/SKILL.md) | [Pinned Release Readiness report; GO/GO_WITH_CONTROLS/NO_GO/DEFER; ReleaseEnvelope/DecisionHandoff](../skills/release-readiness/references/output-contract.md) | [portfolio-operator / user](../skills/portfolio-operator/references/delegation.md); candidate/environment-bound verdict, hard gates and controls | documented receiving contract; GO is not permission to publish |
| [`repair-operator`](../skills/repair-operator/SKILL.md) | [cometweb.repair-ledger/v1; finding dispositions/retest/invariants + repaired artifact](../skills/repair-operator/references/output-contract.md) | [quality-loop-operator → review/acceptance owner](../skills/quality-loop-operator/references/output-contract.md); return to review/acceptance stage; repair does not own final acceptance | documented stage contract |
| [`repo-roaster`](../skills/repo-roaster/SKILL.md) | Scoped findings; [cometweb.repo-roaster/v6 report and cometweb.roaster-handoff/v2 when required](../skills/repo-roaster/references/output-contract.md) | [repair-operator](../skills/repair-operator/SKILL.md); accepted defect findings to repair; roadmap/release consumers retain scope | documented/manual handoff; full contract optional; no roaster handoff validator |
| [`repo-to-roadmap`](../skills/repo-to-roadmap/SKILL.md) | [Evidence-based Roadmap v2; Target State Contract, evidence ledger, dependency/acceptance proofs](../skills/repo-to-roadmap/references/output-contract.md) | [product-operator](../skills/repo-to-roadmap/references/handoffs.md); compact snapshot/roadmap IDs/dependencies/claims to product-operator; Council result decision_ref | documented producer-side handoff, recipient must preserve baseline |
| [`research-program-operator`](../skills/research-program-operator/SKILL.md) | [Research program + stage-bound research_handoff](../skills/research-program-operator/references/output-contract.md) | [science-roaster / longform-publisher / next-study owner](../skills/research-program-operator/references/output-contract.md); science-roaster / longform-publisher / next-study target with stage-specific READY requirements | executable producer-side gate; downstream execution not proved |
| [`rubric-designer`](../skills/rubric-designer/SKILL.md) | [Rubric payload with criterion coverage/blockers/anti-gaming and frozen hash](../skills/rubric-designer/references/output-contract.md) | [skill-evaluator / benchmark-curator](../skills/skill-evaluator/references/output-contract.md); rubric_hash-bound experiment input; benchmark also uses frozen rubric | documented receiving contract + local hash guards |
| [`science-roaster`](../skills/science-roaster/SKILL.md) | [cometweb.science-roaster/v6 report; cometweb.roaster-handoff/v2](../skills/science-roaster/references/output-contract.md) | [repair-operator](../skills/repair-operator/SKILL.md); post-arbitration methodological findings only; retain integrity/evidence/assurance limitations | documented/manual handoff; no roaster handoff validator |
| [`seo-geo-aeo-maxxing`](../skills/seo-geo-aeo-maxxing/SKILL.md) | [SEO/GEO/AEO report with scope/as_of, observed visibility, evidence and priorities](../skills/seo-geo-aeo-maxxing/references/output-contract.md) | [product-operator / repo-to-roadmap / release-readiness / competitive-intelligence](../skills/seo-geo-aeo-maxxing/references/composability.md); operator/roadmap findings, release only same candidate scope, CI ongoing watch | documented producer-side routes; outcome claims require live evidence |
| [`skill-auditor`](../skills/skill-auditor/SKILL.md) | [Skill Audit Report/payload; issues, contract/migration gaps, repair path](../skills/skill-auditor/references/output-contract.md) | [quality-loop-operator → skill-evaluator when required](../skills/quality-loop-operator/references/output-contract.md); SKILL_QUALITY audit stage; empirical_eval_required must route to evaluator | documented stage contract; skill-creator is outside this catalog |
| [`skill-evaluator`](../skills/skill-evaluator/SKILL.md) | [ExperimentReport with pinned rubric/benchmark/suite/config/host-model evidence](../skills/skill-evaluator/references/output-contract.md) | [quality-loop-operator](../skills/quality-loop-operator/references/output-contract.md); SKILL_QUALITY evaluation stage with runtime/canary policy; promotion eligibility is not rollout | documented receiving stage + local hash guards; empirical results not exercised |
| [`skill-orchestrator`](../skills/skill-orchestrator/SKILL.md) | [Workflow plan, per-step outputs, Workflow result; append-only workflow ledger](../skills/skill-orchestrator/SKILL.md) | [portfolio-operator / designated step owner](../skills/portfolio-operator/references/delegation.md); final specialist/control-plane result; designated steps receive own contracts | documented receiving contract + five executable nonempty archetypes |
| [`skill-orchestrator-multiagent`](../skills/skill-orchestrator-multiagent/SKILL.md) → `skill-orchestrator` | [Same canonical Workflow plan/result/ledger; isolated_subagents mode](../skills/skill-orchestrator-multiagent/SKILL.md) | [skill-orchestrator](../skills/skill-orchestrator/SKILL.md); load canonical planner; unavailable canonical/Task API stops alias | alias, not independent semantic owner |
| [`web-app-auditor`](../skills/web-app-auditor/SKILL.md) | [Web App Audit findings/report; evidence_manifest; contract-trace sidecar](../skills/web-app-auditor/SKILL.md) | [release-readiness / product-operator / repo-to-roadmap / customer-ops](../skills/web-app-auditor/references/composability.md); release same candidate/environment; operator findings; roadmap gaps; customer reproduction | documented producer-side mappings; actual host audit not exercised |

## Profiles and framework packs

The four [specialist profiles](../registry/specialist-profiles.json) extend
existing owners: conversion-audit → `web-app-auditor`, experiment-design →
`brief-architect`, activation-onboarding → `product-operator`, and
sop-documentation → `content-writer`. They are opt-in local pilots; a profile ID
is not a skill ID. Read the [owner admission contract](../skills/skill-orchestrator/references/specialist-profile-contract.md).

The three [capability packs](../registry/capability-packs.json) provide optional
framework references for customer research, pricing and offers. They are source
previews, carry FRAMEWORK claims, and do not supply verified facts, a new owner
or authority to execute side effects. Read the
[pack contract](../skills/skill-orchestrator/references/capability-pack-contract.md).

These overlays do not change the task-specific installation selections above.
Structural installation checks and linked output contracts do not prove native
host execution, model quality, external facts or publication readiness.

## Optional contracts and helpers

Use `brief-architect` for an actual ArtifactBrief consumer, not as a prerequisite
for ordinary clarification. `ai-humanize` and `quality-loop-operator` are optional
editing and workflow stages. `release-readiness` is an adapter to declared gates;
its engine does not authenticate evidence or grant deployment authority.
These selection guidelines do not change host invocation policy or establish
behavioral qualification. Keep source maps and executable helpers available when
they are useful without loading their associated workflow instructions.

The [local QA example](../examples/qa-repair-retest/README.md) demonstrates one
bounded audit, repair and fresh retest. A successful synthetic example is not
proof that adding a skill improves the native model.
