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

Read `references/learning-contract.md`.

Before discovery, define:

- product stage and current product truth,
- target workflow / JTBD and current alternative,
- intended buyer, champion, and actual user,
- learning strategy: `WEDGE_VALIDATION`, `SEGMENT_DISCOVERY`, `HORIZONTAL_TRANSFER`, or `ENTERPRISE_STRESS_TEST`,
- 3–7 material hypotheses or decision questions,
- what evidence would support and falsify each hypothesis,
- which product/market decision changes if the hypothesis is true or false,
- required implementation/data/system access,
- expected time and team capacity for the partner program,
- partner `give` and company `give`,
- disqualifiers, anti-personas, conflict risks, and bespoke-work limits,
- intended outreach-slate size and active-cohort capacity.

Treat the Learning Contract as the governing artifact. A candidate can be excellent in general and still be irrelevant to the current contract.

## Step 2 — Discover candidates

For FIND mode, read `references/discovery-playbook.md`.

Prefer a mixed discovery strategy:

1. **Warm graph** — existing customers, founder/team network, prior opportunities, advisors, investors, partners, users, newsletter/community relationships. Warmth improves access; it does not increase partnerability by itself.
2. **Problem-first public signals** — workarounds, migration pain, job posts, workflow complaints, technical constraints, launch/scale triggers, public initiatives.
3. **Ecosystem adjacency** — users of substitutes, integrations, open-source tools, agencies/consultancies operating the workflow, adjacent vendors with the target user base.
4. **Coverage search** — only after the pain vocabulary and target pattern are understood; use firmographic databases/directories to fill gaps, not to define evidence.

Build a candidate universe roughly 3–5x larger than the desired outreach slate when quality and evidence are sufficient. Stop expanding when another search wave adds little novel evidence or segment coverage.

Never qualify from a search-result snippet alone. Open the underlying source.

## Step 3 — Run Stage A: desk-research Discovery Fit

Read `references/partnerability-rubric.md` and `references/evidence-and-freshness.md`.

Evaluate only what can be credibly researched before contact:

- problem evidence,
- urgency / current trigger,
- representativeness relative to the Learning Contract,
- learning value,
- implementation plausibility,
- stakeholder/contact path,
- credibility and evidence quality,
- commercial optionality,
- reference/network value as a minor tie-breaker,
- customization risk, conflict risk, contradiction risk, and research uncertainty.

Run `scripts/score_candidate.py --stage research` when code execution is available.

Use the research-stage output to choose whom to **contact for discovery**, not to claim they have agreed to be a design partner.

Do not score public enthusiasm as `feedback_commitment`. Do not claim private capacity from a job title or a polished website.

## Step 4 — Diligence evidence and freshness

For every serious candidate:

1. Resolve the canonical entity/domain and aliases.
2. Separate observed/confirmed facts from inference.
3. Record source, publication date when available, and `last_verified_at` for material current claims.
4. Verify the problem/trigger from a distinct lineage where practical.
5. Run a contradiction search for top candidates.
6. Mark duplicate/repackaged evidence as one lineage, not multiple confirmations.
7. Use `CURRENT`, `NEAR_EXPIRY`, `STALE`, or `UNKNOWN` for material current claims; refresh stale trigger/contact/capability evidence before making a current recommendation.
8. Downgrade confidence rather than inventing missing evidence.

A lack of public evidence is not proof that the company lacks the pain. It means `unknown` until live validation.

## Step 5 — Build the outreach slate

Use Stage A scores plus evidence gaps to prioritize who deserves a discovery conversation.

For each top candidate, state:

- why this company / why now,
- which Learning Contract hypotheses it can test,
- what is observed vs inferred,
- highest-value missing fact that could change the ranking,
- buyer/champion/user hypotheses,
- likely implementation blockers,
- customization/conflict concerns,
- the natural professional contact path,
- one low-friction validation question.

When selecting a slate from many similar candidates, use `scripts/select_cohort.py --selection-stage outreach_slate` to reward weighted learning coverage and reduce redundant research effort.

## Step 6 — Run Stage B: live Partner Readiness

After a real conversation or direct company evidence exists, re-score with `scripts/score_candidate.py --stage live`.

Confirm rather than infer:

- problem severity and cost of status quo,
- urgency and why now,
- actual user + champion access,
- implementation readiness and required data/systems,
- feedback cadence and time commitment,
- decision authority / procurement feasibility appropriate to the engagement motion,
- mutual value alignment,
- pilot measurability,
- transferability beyond this one company,
- material legal/security/privacy blockers where relevant.

Only a live-qualified candidate may become `PARTNER_READY`. Research-stage fit alone never produces that status.

## Step 7 — Compose the active cohort

Read `references/cohort-and-pilot.md`.

Do not take the top N scores mechanically. Choose the cohort strategy from the Learning Contract, then optimize for:

- weighted hypothesis coverage,
- enough replication on core questions to avoid overreacting to one idiosyncratic partner,
- acceptable overlap/confounding,
- implementation/support capacity,
- expected learning per unit of team effort,
- explicit edge/stress-test roles only when they answer named questions.

Run `scripts/select_cohort.py --selection-stage active_cohort` when useful.

If the selected cohort does not cover a must-answer hypothesis, state that the cohort is incomplete instead of padding it with weak candidates.

## Step 8 — Activate with a Partner Charter

Read `references/partner-charter.md` and `references/partner-lifecycle.md`.

Before kickoff, define:

- sponsor/champion/actual-user roles,
- specific learning hypotheses,
- implementation owner and prerequisites,
- data/system/security boundaries,
- expected feedback/usage cadence,
- success, failure, and stop criteria,
- company and partner commitments,
- non-goals and bespoke-work boundary,
- escalation path,
- engagement length/review date,
- commercial terms only when appropriate to the selected motion,
- confidentiality, IP, data-processing, reference/publicity, and contractual issues to route for qualified review when material.

Do not turn the skill into legal counsel. Identify issues and trigger current jurisdiction-specific review when necessary.

## Step 9 — Operate the learning loop

Prefer behavioral evidence:

- activation and implementation progress,
- repeated product usage in the target workflow,
- task success/failure and time-to-value,
- qualitative feedback tied to an observed workflow event,
- support burden and founder/manual-service dependence,
- recurring requests across independent partners,
- churn/inaction reasons,
- buyer vs user disagreement.

For every material request, classify it as:

- `CORE` — supports the current product thesis and transfers broadly,
- `SEGMENT` — useful to a deliberate target segment,
- `EDGE` — valid but not roadmap-defining,
- `BESPOKE` — primarily serves one partner,
- `CONTRADICTS_THESIS` — evidence that the current product/ICP assumption may be wrong.

Do not build a material feature solely because one prestigious partner requests it. Require explicit product reasoning or a deliberate experiment.

## Step 10 — Review, graduate, or exit

For active partners, run `scripts/assess_partner_health.py` when code execution is available.

Use outcomes:

- `CONTINUE` — learning yield and engagement justify more work,
- `REPAIR` — valuable partner but a recoverable engagement/implementation issue exists,
- `PAUSE` — timing/capacity makes continued work inefficient,
- `EXIT_REVIEW` — low learning, bespoke pressure, or persistent non-engagement warrants exit,
- `CONVERSION_CANDIDATE` — product value is demonstrated and the company may move into a normal commercial motion.

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

Read `references/output-contract.md` before finalizing.

Default output:

1. **Learning Contract** — product stage, motion, strategy, hypotheses, gates.
2. **Evidence readiness** — what is confirmed, inferred, stale, or missing.
3. **Ranked outreach slate** — Stage A score/status/action.
4. **Top candidate dossiers** — evidence, hypothesis coverage, risks, next fact to validate.
5. **Live readiness** — only for candidates with direct evidence.
6. **Recommended cohort** — unique learning role + coverage/replication summary.
7. **Rejected / near-miss candidates** — concise reason and reconsideration trigger.
8. **Activation plan** — charter/pilot requirements when requested.
9. **Search parameters + as-of** — reproducibility.
10. **Open unknowns + highest-VOI next actions**.

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
