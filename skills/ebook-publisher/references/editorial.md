# Editorial and meaning-preservation standard

## Shape the ebook around reader work

Open with who the ebook is for, the task it helps complete, prerequisites, limitations,
and how to use it. Prefer a concrete promise supported by the actual chapters. Avoid
"everything you need to know", fabricated authority, and unsupported commercial outcomes.

An outline should progress from understanding the problem to evaluating it, acting,
and verifying the outcome when that fits the topic. A conceptual chapter may use an
argument and examples rather than an artificial checklist. Explain terminology before
relying on it. Include an honest section on common mistakes and limits of tools.

For procedural chapters, check these fields where useful:
question → prerequisites → steps → worked example → acceptance criterion → evidence to
save → boundary of interpretation. Distinguish instruction from an already completed test.
Link repeated concepts rather than duplicating paragraphs across chapters. A useful
appendix may contain a reusable worksheet; it should not be padding.

## Language and voice

Default CometWeb voice: clear practical Polish, precise technical terms, ordinary verbs,
concrete examples, no inflated claims. Explain expert vocabulary when the target audience
needs it. No forced synonyms for canonical terms; maintain a glossary/term decisions.
Use complete readable sentences, purposeful headings, and varied paragraph length driven
by meaning. Do not turn every paragraph into bullets or every concept into a callout.

Remove assistant leakage ("poniżej przedstawiam", "jako AI"), repetitive openings,
empty conclusions, ornamental contrast formulas, and generic hype. Do not invent anecdotes,
testimonial quotes, personal experience, tiny errors, or fake uncertainty to appear natural.
Do not promise higher rankings, conversions, accessibility compliance, or energy savings
without adequate evidence and scope. Product mentions must be current, modest, and relevant.
CometWeb is a product business; do not quietly rewrite it as a service agency.

## Pre-edit contract

Before a substantial rewrite, preserve a baseline manuscript and list protected spans:
claims/counterclaims; uncertainty; negation; quantifiers; numbers/units; dates/versions;
causality; attribution; quotations; code/identifiers; URLs/citations; legal/normative verbs;
conditions, exceptions, and thresholds. Preserve intent, not sentence-by-sentence wording.
A concise rewrite may omit detail only when allowed by the requested scope, with coverage
checked afterwards. Translation is a semantic transformation, not simply a style pass.

Load `ai-humanize` and its appropriate PL/EN and fidelity references when available.
Use its actual scripts when compatible and record execution. If absent, do the same
baseline/diff/claim comparison manually and mark the fallback in QA. Never invent a run.

## Post-edit adversarial checks

Read changed claims against sources, not merely against the previous wording. Ask:
Did "may" become "will"? Did a lab demonstration become field evidence? Did correlation
become causation? Did "some websites" become "all websites"? Did a recommendation become
an obligation? Did a decrease become a pass despite still failing the criterion? Did a
new sentence introduce an unsupported benefit? Did a footnote drift away from its claim?

Recompute examples, totals, percentages, unit conversions, and chart labels with tools.
Execute code where feasible in a safe environment, never against production without consent.
Otherwise label it untested and explain limitations. Keep illustrative data visibly synthetic.
A rewritten tutorial must not silently change command order, flags, versions, or outputs.

## Review pass

Perform a separate sceptical pass over the complete draft after chapter-level work.
Look for omissions, contradictions, repetition, terminology drift, misleading confidence,
poor practical instructions, and unsupported product claims. Record issue location,
severity, evidence, fix, retest, and disposition. Do not judge only the introduction.

A role switch in the same conversation is a self-review. Call a reviewer independent only
when a genuinely separate reviewer/context performed the work. Independent expertise may
still be needed for high-stakes material; do not fabricate expert sign-off.

Accept the manuscript when it answers its scoped questions, practical examples work or
are transparently limited, material claims map to evidence, and no unresolved critical
editorial issue remains. A numeric quality score cannot compensate for a false claim.
