# Regression cases

These cases are policy invariants for future edits. A correct audit must preserve the expected
behavior even when platform vocabulary changes.

## Platform-control cases

1. `GPTBot blocked; OAI-SearchBot allowed and fetchable`
   - Must not fail ChatGPT Search discovery merely because GPTBot is blocked.
2. `OAI-SearchBot explicitly blocked on critical public content`
   - May fail GEO-06 with target-specific evidence after freshness verification.
3. `Google-Extended blocked; Google Search pages indexable`
   - Must not equate this with exclusion from AI Overviews/AI Mode.
4. `llms.txt missing`
   - Must not penalize Google Search/Google AI Search readiness.
5. `PerplexityBot allowed; Perplexity-User behavior unknown`
   - Do not claim complete user-fetch control from robots.txt.
6. `Bing index healthy; no dedicated Copilot crawler observed`
   - Do not invent a CopilotBot requirement.

## Content and schema cases

7. `Two H1 elements but clear page structure`
   - No automatic SEO FAIL.
8. `H2 followed by H4`
   - No automatic Google ranking FAIL; treat as structure/accessibility issue only if harmful.
9. `Title 67 characters but clear and useful`
   - No automatic FAIL based on length alone.
10. `Text-only fetch contains no JSON-LD`
    - Do not conclude schema is absent; use rendered/validator evidence or NOT_ASSESSED.
11. `FAQPage missing`
    - Do not claim current Google FAQ rich-result loss from old guidance.
12. `Person schema missing on a low-stakes product page`
    - Do not treat as proof of weak expertise or an automatic failure.

## Measurement cases

13. `No GSC Generative AI report access`
    - Record measurement as unavailable, never zero impressions.
14. `No ChatGPT referral sessions`
    - Do not infer no ChatGPT citations.
15. `One prompt cites the site`
    - Call it sampled evidence, not platform-wide visibility.
16. `Readiness score rises after a content change`
    - Do not claim caused visibility growth without stronger before/after evidence.

## Query fan-out and distribution cases

17. `Google query fan-out suggests many related tasks`
    - Improve genuine task/topic coverage; do not mass-produce thin pages per imagined variant.
18. `Eligible publisher can add Preferred Sources button`
    - Treat as optional audience-distribution tactic, not generic ranking factor or MAXX bonus.

## Scoring integrity cases

19. `Partial pillar audit scores 100`
    - Output Focused readiness 100, never whole-site MAXX 100.
20. `Conditional check appears irrelevant`
    - N/A requires target-specific applicability evidence; otherwise NOT_ASSESSED.
21. `Platform docs are current but target configuration was never tested`
    - Do not score PASS; E1 alone is insufficient.
22. `Same check sampled across 8 pages: 7 pass, 1 fail`
    - Preserve distribution rather than collapsing to a generic PASS.
23. `VERSUS sites have 100% vs 60% evidence coverage`
    - Warn about asymmetric evidence and avoid declaring a clean winner.
24. `Registry version changes between DELTA audits`
    - Mark totals non-comparable unless explicitly normalized/re-run under the same registry.
