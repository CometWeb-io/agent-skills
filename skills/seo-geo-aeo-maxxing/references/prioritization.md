# Prioritization

The report must tell a team what to do first, based on dependencies, business exposure, evidence,
and implementation effort.

## 1. Gates and prerequisites first

Active critical gates outrank normal sorting. Resolve causes before downstream symptoms: indexability
before copy polish, canonical/template duplication before more duplicate pages, inaccessible content
before GEO formatting experiments.

## 2. Score Impact, Confidence, Ease

Use 1-5 and calculate:

```text
ICE = Impact * Confidence * Ease
```

ICE is a sorting aid, not a causal model.

### Impact

Judge both business criticality and affected scope:

- 5: discovery/indexing blocker, critical revenue/lead flow, or broad measured visibility loss;
- 4: major issue across important template/directory or strong business path;
- 3: meaningful page/template improvement with plausible visibility effect;
- 2: local/secondary surface or limited affected scope;
- 1: cosmetic/speculative.

A tiny issue on 80% of product pages can outrank a severe issue on one low-value URL. State affected
sample/template scope when it changes priority.

### Confidence

Cap by the best evidence class actually supporting the action:

- E1/E2: up to 5;
- E3/E4: up to 4;
- E5: up to 3;
- E6: up to 2;
- E7: up to 1.

For a site-specific fix, generic E1 platform documentation alone is insufficient; target evidence
still matters.

### Ease

- 5: isolated low-risk change;
- 4: straightforward template/content change;
- 3: moderate implementation/coordination;
- 2: substantial engineering/content/approval work;
- 1: migration, architecture, or organization-wide dependency.

## 3. Separate action types

Label each recommendation as one of:

- `REMEDIATION`: fix an evidenced defect;
- `MEASUREMENT`: obtain data that could change the decision;
- `EXPERIMENT`: test a plausible but non-established tactic.

Do not let an easy experiment outrank a proven blocker.

## 4. Dependency order

If action B cannot produce value until A is fixed, A comes first even if B has a higher raw ICE.
Mention dependencies explicitly.

## 5. Output bands

### This week

Return up to 3 actions with finding/check ID, evidence, affected scope, causal rationale, exact next
step, Impact/Confidence/Ease/ICE, action type, and likely owner.

### This month

Return 5-7 compact actions when enough evidence-backed work exists.

### Backlog / experiments

Keep lower-impact or lower-confidence items compact and label experiments. Never pad a band to hit a
count.
