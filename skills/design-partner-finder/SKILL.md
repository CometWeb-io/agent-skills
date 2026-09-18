---
name: design-partner-finder
description: >-
  Find, verify, qualify, compare, and manage companies as design partners, co-development partners, beta partners, paid pilots, lighthouse customers, or early adopters. Use for design-partner discovery, early-adopter shortlists, qualification of an existing candidate list, cohort selection, partner-readiness validation, active-partner review, or revalidation of prior candidates. Go deeper than generic prospecting by optimizing for learning value, urgency, representativeness, implementation feasibility, real user/champion access, mutual commitment, evidence quality, transferability, cohort coverage, and cost-to-learn. Separate desk-research fit from live readiness, preserve evidence lineage/freshness, and prevent prestige or contract size from replacing product-learning quality. Hand off broad lead generation to prospecting, research synthesis to customer-research, and outreach copy to cold-email.
---

# Design Partner Finder

Find the small set of organizations that can reduce product uncertainty quickly and credibly while remaining plausible early customers. Treat a design-partner program as a **learning system with commercial optionality**, not as a lead list or logo-collection exercise.

## Non-negotiable principles

1. Separate **desk-research fit** from **live partner readiness**. Never infer willingness, feedback commitment, user access, procurement approval, or pilot readiness from public evidence alone.
2. Optimize for **learning transferability**, not prestige. A famous company with weak problem evidence is a poor core design partner.
3. Decide the **engagement motion** before scoring. Research partner, design partner, beta partner, paid pilot, and lighthouse customer have different readiness gates.
4. Decide the **learning strategy** before composing a cohort. Narrow validation and deliberate segment exploration are both valid, but they answer different questions.
5. Treat every material claim as `observed`, `confirmed`, `inferred`, `unknown`, or `contradicted`; preserve source lineage and freshness.
6. Use behavior over opinions after activation. Product usage, implementation progress, recurring feedback, and real workflow evidence outrank enthusiasm on calls.
7. Do not let one partner silently become the roadmap. Classify requests by transferability and require explicit exceptions for bespoke work.
8. Preserve rejected and near-miss candidates with reasons so future searches learn instead of repeating bad discovery.
9. Never auto-send outreach, mutate CRM records, accept commercial/legal terms, or promise roadmap work without explicit authorization.

## Boundary with adjacent skills

- Use `design-partner-finder` to determine **who is worth learning/building with and under what partnership design**.
- Use `prospecting` for broad outbound list building once the ICP and selling motion are stable.
- Use `customer-research` to synthesize interviews, transcripts, reviews, support evidence, or cross-partner VOC patterns.
- Use `product-marketing` when validated partner learning should update ICP, positioning, pains, objections, proof points, or switching dynamics.
- Use `cold-email` only after a shortlist exists and outreach copy is requested.
- Use `sales-enablement` for partner decks, one-pagers, ROI material, or demo collateral.
- Use `revops` for CRM lifecycle, routing, handoff, and pipeline automation.
- Use `ai-council` for material trade-offs such as choosing between competing cohort strategies, paid-vs-unpaid partner models, or accepting a strategically unusual partner. Do not invoke it per candidate by default.

## Modes

Infer one or more modes. Run them in this order when combined.

1. **FIND** — discover new candidate organizations.
2. **QUALIFY** — score and diligence a user-provided candidate list without unnecessarily expanding it.
3. **COHORT** — compose either an outreach slate or an active design-partner cohort.
4. **ACTIVATE** — live-qualify a candidate, define mutual commitments, and design the pilot/engagement.
5. **REVIEW** — assess active partner health, learning yield, bespoke pressure, and graduation state.
6. **REFRESH** — revalidate an older shortlist against current evidence while preserving history.

## Context and systems of record

Use the best available context before external discovery.

1. Read `.agents/product-marketing.md` when present; also accept `.claude/product-marketing.md` and legacy `product-marketing-context.md`.
2. For product truth, prefer the active repository and product documentation over old strategy notes. If GitHub is connected and the user names a product/repository, inspect relevant capabilities, integrations, constraints, maturity, and unresolved product questions.
3. For roadmap/tasks, prefer the current execution system such as Linear or the canonical Notion project space.
4. For known relationships, ownership, previous outreach, and commercial history, prefer CRM/email systems such as HubSpot and Gmail when available and relevant.
5. For existing research, inspect the canonical Notion/Drive research artifacts rather than re-deriving context from public web sources.
6. Never send private raw content into public web searches. Convert internal context into minimal non-sensitive search concepts.
7. Ask only for missing information that materially changes the decision; otherwise state assumptions and continue.

## Step 0 — Classify the engagement motion

Read `references/engagement-modes.md` when the requested motion is ambiguous.

Classify the intended relationship as one of:

- `RESEARCH_PARTNER` — validates problem/workflow with prototypes or manual service; production use is not required.
- `DESIGN_PARTNER` — repeatedly co-shapes product behavior and implementation while the product is still evolving.
- `BETA_PARTNER` — uses a substantially working product and exposes defects, usability gaps, and operational edge cases.
- `PAID_PILOT` — validates value and production feasibility under explicit commercial commitment.
- `LIGHTHOUSE` — provides credible market proof/reference value after product value is real; do not use this label to bypass product-learning gates.

Do not treat these labels as synonyms. Use the earliest motion that can answer the current product question with the least unnecessary friction.

## Step 1 — Build the Learning Contract

Read `references/learning-contract.md` and fill it in before discovery: product truth, engagement motion, learning strategy, hypothesis ledger, partner requirements, mutual value, capacity budget, and stop rules.

Treat the Learning Contract as the governing artifact. A candidate can be excellent in general and still be irrelevant to the current contract.

## Step 2 — Discover candidates

For FIND mode, read `references/discovery-playbook.md` and work the discovery order it defines: warm graph, problem-first public signals, ecosystem adjacency, then coverage search once the pain vocabulary and target pattern are understood.

Warmth improves access; it does not increase partnerability by itself.

Build a candidate universe roughly 3–5x larger than the desired outreach slate when quality and evidence are sufficient. Stop expanding when another search wave adds little novel evidence or segment coverage.

Never qualify from a search-result snippet alone. Open the underlying source.

## Step 3 — Run Stage A: desk-research Discovery Fit

Read `references/partnerability-rubric.md` and `references/evidence-and-freshness.md`. Score only the Stage A dimensions — the ones that can be credibly researched before contact. Run `scripts/score_candidate.py --stage research` when code execution is available.

Use the research-stage output to choose whom to **contact for discovery**, not to claim they have agreed to be a design partner.

Do not score public enthusiasm as `feedback_commitment`. Do not claim private capacity from a job title or a polished website.

## Step 4 — Diligence evidence and freshness

Apply `references/evidence-and-freshness.md` to every serious candidate: resolve the canonical entity and aliases, mark each material claim with a claim state, record lineage and `last_verified_at`, and run a contradiction search for top candidates.

Duplicate or repackaged evidence is one lineage, not multiple confirmations. Refresh stale trigger/contact/capability evidence before making a current recommendation, and downgrade confidence rather than inventing missing evidence.

A lack of public evidence is not proof that the company lacks the pain. It means `unknown` until live validation.

## Step 5 — Build the outreach slate

Use Stage A scores plus evidence gaps to prioritize who deserves a discovery conversation. Write each top candidate up as the dossier in `references/output-contract.md`: why this company and why now, which Learning Contract hypotheses it can test, what is observed versus inferred, the highest-VOI missing fact, buyer/champion/user hypotheses, likely implementation blockers, the natural professional contact path, and one low-friction validation question.

When selecting a slate from many similar candidates, use `scripts/select_cohort.py --selection-stage outreach_slate` to reward weighted learning coverage and reduce redundant research effort.

## Step 6 — Run Stage B: live Partner Readiness

After a real conversation or direct company evidence exists, re-score with `scripts/score_candidate.py --stage live` against the Stage B dimensions and gates in `references/partnerability-rubric.md`. Confirm those dimensions; never infer them from public evidence.

Only a live-qualified candidate may become `PARTNER_READY`. Research-stage fit alone never produces that status.

## Step 7 — Compose the active cohort

Read `references/cohort-and-pilot.md`. Do not take the top N scores mechanically. Choose the cohort strategy from the Learning Contract, then optimize weighted hypothesis coverage, replication, overlap, implementation capacity, and cost-to-learn as that reference defines them. Run `scripts/select_cohort.py --selection-stage active_cohort` when useful.

Assign explicit edge or stress-test roles only when they answer named questions.

If the selected cohort does not cover a must-answer hypothesis, state that the cohort is incomplete instead of padding it with weak candidates.

## Step 8 — Activate with a Partner Charter

Fill in `references/partner-charter.md` before kickoff and follow `references/partner-lifecycle.md` for the engagement itself. The charter covers roles, learning hypotheses, implementation prerequisites, data/system/security boundaries, feedback cadence, success/failure/stop criteria, mutual commitments, non-goals and the bespoke-work boundary, escalation path, review date, commercial terms where the motion calls for them, and the legal/privacy/IP issues to route for qualified review.

Do not turn the skill into legal counsel. Identify issues and trigger current jurisdiction-specific review when necessary.

## Step 9 — Operate the learning loop

Prefer behavioral evidence over stated enthusiasm: implementation progress, repeated use of the target workflow, task success and time-to-value, support and manual-service burden, and buyer-versus-user disagreement. `references/partner-lifecycle.md` lists what to instrument and how to triage each material request as `CORE`, `SEGMENT`, `EDGE`, `BESPOKE`, or `CONTRADICTS_THESIS`.

A request repeated by independent partners is a signal; one prestigious partner is not. Do not build a material feature solely because one partner asks for it. Require explicit product reasoning or a deliberate experiment.

## Step 10 — Review, graduate, or exit

For active partners, run `scripts/assess_partner_health.py` when code execution is available, and use the graduation outcomes defined in `references/partner-lifecycle.md`: `CONTINUE`, `REPAIR`, `PAUSE`, `EXIT_REVIEW`, or `CONVERSION_CANDIDATE`.

Do not preserve a design partnership indefinitely because the logo is attractive.

Send cross-partner transcript/VOC synthesis to `customer-research`; send validated ICP/positioning changes to `product-marketing`; send normal sales motion to `prospecting`/`cold-email`/`revops` as appropriate.

## REFRESH mode

For an older shortlist or cohort:

1. Preserve prior evidence and prior score; do not rewrite history.
2. Refresh only material current claims first: trigger, capability, role/contact, initiative, company activity, and blockers.
3. Re-score changed dimensions.
4. Show `old -> new` score/status and the evidence that caused the movement.
5. Re-open any recommendation whose binding evidence is stale, contradicted, or materially changed.

## Output contract

Read `references/output-contract.md` before finalizing. It defines the default sequence — Learning Contract, evidence readiness, ranked outreach slate, candidate dossiers, live readiness, recommended cohort, rejections and near misses, activation plan, search parameters and as-of, open unknowns and highest-VOI next actions — and the honest-language vocabulary for describing candidate state.

For large candidate sets, use a file only when requested or appropriate; keep the decision summary in chat.

## Quality gate

Before finalizing, verify all of the following:

- Research-stage outputs never imply agreement, interest, commitment, or readiness that was not directly confirmed.
- Every primary candidate has real evidence beyond firmographic fit.
- Prestige, funding, and logo value remain secondary to problem/learning fit.
- The chosen cohort strategy matches the Learning Contract.
- Core hypotheses have deliberate coverage/replication or are explicitly marked uncovered.
- Observed/confirmed facts and inference are visibly separated.
- Material current claims carry source lineage and freshness state.
- Contradiction search was attempted for top candidates.
- No `PARTNER_READY` candidate is based solely on public research.
- Buyer, champion, sponsor, and actual user are not casually collapsed.
- Bespoke pressure, implementation burden, and cost-to-learn are visible.
- Rejected candidates remain documented with reasons.
- Public professional data only; no leaked/sensitive personal data or bot-protection bypass.
- External actions remain gated behind explicit authorization.

## References

Read only what the current task needs:

- `references/engagement-modes.md` — distinguish research/design/beta/paid-pilot/lighthouse motions.
- `references/learning-contract.md` — hypotheses, decision rules, evidence needs, program capacity.
- `references/discovery-playbook.md` — warm graph, problem-first discovery, search waves, stop rules.
- `references/evidence-and-freshness.md` — evidence states, lineages, contradictions, freshness.
- `references/partnerability-rubric.md` — Stage A and Stage B dimensions, gates, statuses.
- `references/cohort-and-pilot.md` — learning strategies, weighted coverage, replication, portfolio selection.
- `references/partner-charter.md` — mutual commitments and legal/security/privacy issue checklist.
- `references/partner-lifecycle.md` — kickoff, usage/feedback loop, request triage, graduation.
- `references/output-contract.md` — output schemas and dossier templates.
- `references/compliance.md` — public-data, outreach, privacy, platform, and side-effect guardrails.
- `references/method-foundations.md` — durable external frameworks/case studies and where they disagree.
