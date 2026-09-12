# Composability and handoffs

Keep this skill diagnostic. Export accepted findings without turning them into roadmap, release, or strategy decisions.

## Evidence handoff contract

For each material exported finding preserve:

- audit subject, mode/profile, target surfaces, and `as_of`;
- check ID/pillar and verdict (`PASS | WEAK | FAIL | N/A | NOT_ASSESSED`);
- evidence objects with source, class, locator/artifact, and freshness;
- sample/template scope and distribution where used;
- coverage/evidence grade and critical-gate state;
- remediation/measurement/experiment label;
- unresolved contradictions and not-assessed gaps.

Do not promote `NOT_ASSESSED` to `FAIL`, or sampled evidence to sitewide proof.

## Route downstream by job

- `product-operator` — convert accepted findings into bounded current actions after reconciling product state and dependencies.
- `repo-to-roadmap` — incorporate verified visibility gaps into a whole-project target-state roadmap.
- `release-readiness` — consume candidate-bound search/visibility findings only when they are actually relevant to a required release gate; this skill does not issue production GO/NO-GO.
- `competitive-intelligence` — own recurring competitor monitoring/delta. This skill may perform a same-rubric VERSUS audit but should not become the temporal watch system.
- `evidence-researcher` — use for consequential disputed platform/policy claims requiring deeper source-lineage/falsifier work.
- `ai-council` — use only when accepted evidence creates a material strategic trade-off; Council consumes the findings rather than re-running the audit.

## Feedback from downstream

If a downstream skill needs stronger proof, re-open only the affected checks/sources. Keep prior audit fingerprints and comparison scope so DELTA/VERSUS remains interpretable.
