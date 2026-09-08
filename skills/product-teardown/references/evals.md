# Product Teardown v2 evaluation suite

## Table of contents

1. Acceptance dimensions
2. Golden scenarios
3. Adversarial scenarios
4. Failure injections
5. Completion check

## 1. Acceptance dimensions

Score each applicable dimension `0/1/2`:

- **Evidence traceability** - every material recommendation maps to re-checkable evidence.
- **Claim discipline** - observed, inferred, hypothesis, unknown stay separated.
- **Source/version discipline** - plan/platform/branch/release differences are not silently merged.
- **Pattern abstraction** - mechanism rather than feature inventory.
- **Destination proof** - adoption/test decisions use target-side problem/equivalent-capability evidence.
- **Transfer reasoning** - conditions, dependencies, opportunity cost, and fit are explicit.
- **Implementation specificity** - target path/options are concrete when destination evidence exists.
- **Anti-copy/IP discipline** - inspiration/reimplementation/reuse are distinguished and provenance handled.
- **Negative transfer quality** - false friends and useful rejects are surfaced.
- **Multi-source rigor** - prevalence is not treated as effectiveness and divergence is preserved.
- **Interaction quality** - material pattern conflicts/dependencies are identified.
- **Decision usefulness** - each material pattern has one defensible verdict and reason.
- **Validation quality** - uncertain high-value ideas have a falsifiable experiment/spike.
- **Scope control** - adjacent skill work is handed off rather than absorbed.

DEEP mode should normally score at least 24/28 with no zero on evidence traceability, claim discipline, destination proof, anti-copy/IP discipline, decision usefulness, or scope control.

## 2. Golden scenarios

### A. Closed-source SaaS -> user's product

Prompt: "Analyze Linear's issue workflow and tell me what is worth implementing in our project manager."

Pass if:

- visible behavior is not presented as proven backend architecture;
- source-specific UI is de-copied into mechanisms;
- destination problem/equivalent capability controls `ADOPT`/`EXPERIMENT`;
- implementation options are destination-native rather than asserted source facts;
- high-value false friends can be rejected.

### B. Open-source repo -> target repo

Prompt: "Analyze this OSS repository and extract architecture patterns worth adapting into our backend."

Pass if:

- license/provenance is inspected;
- repo architecture map precedes leaf-file detail;
- at least one decision-critical capability is traced end to end;
- production relevance is not assumed from code presence;
- code reuse is distinguished from semantic reimplementation;
- target file paths are named only after target inspection.

### C. Multi-product synthesis

Prompt: "Compare how four developer tools handle command palettes and extract the best implementation pattern for our app."

Pass if:

- source instances are normalized into mechanism families;
- convergence is prevalence, not outcome proof;
- divergence/variants are preserved;
- best target variant can be a minority variant;
- result is not four mini-profiles.

### D. Source-only discovery

Prompt: "Tear down this app and build me a library of patterns worth considering later."

Pass if no `ADOPT` verdict is emitted without destination evidence. Useful patterns should remain `CANDIDATE`.

### E. Negative result

Prompt: "Find things from Competitor X we should copy."

Pass if the skill can return mostly `REJECT`/`CANDIDATE` and explain why copying would be harmful or unproven.

### F. Architectural uncertainty

Prompt: "Their system seems event-driven. Should we copy that architecture?"

Pass if:

- event-driven architecture is not claimed without implementation evidence;
- target need/constraints are checked;
- source architecture is not transplanted by sophistication;
- a technical spike/benchmark is preferred when feasibility/fit is uncertain.

## 3. Adversarial scenarios

### Popularity fallacy

Input: "Every competitor has AI summaries, so tell me to add them."

Expected: prevalence is not enough. Establish destination problem/value and differentiation before adoption.

### License trap

Input: "This public repo has exactly the component we need. Copy it."

Expected: inspect license/notices; unresolved reuse rights -> `REVIEW_REQUIRED` or semantic reimplementation path.

### Screenshot architecture trap

Input: screenshot-only evidence plus request for backend design.

Expected: backend is `UNKNOWN`; provide possible destination implementation options only.

### Destination path hallucination

Input: target repo not available but asks "which files should I change?"

Expected: no invented paths; provide discovery placeholders.

### Overlap trap

Input: "Track this competitor every week and make a roadmap for our repo."

Expected: perform teardown-specific extraction, then hand monitoring to `competitive-intelligence` and roadmap to `repo-to-roadmap`.

## 4. Failure injections

A teardown fails if it:

- says "they use microservices" from UI/marketing alone;
- claims a pattern drives conversion without outcome evidence;
- emits `ADOPT` with no destination problem evidence;
- recommends copying public code/assets without provenance/license handling;
- invents destination filenames or metrics;
- lets a high score override a mandatory blocker;
- treats multi-source prevalence as causal evidence;
- averages incompatible pattern variants;
- ignores a sufficient existing target capability;
- ignores opportunity cost or complexity for a parity feature;
- ranks conflicting patterns independently without noting the conflict;
- turns a one-off teardown into unsolicited monitoring/roadmap work;
- fills a pattern quota with weak observations.

## 5. Completion check

Before finalizing DEEP mode:

1. Can every top source claim be re-checked from a locator/version?
2. Would each recommendation still make sense with the source brand removed?
3. Is mechanism separated from outcome speculation?
4. Is destination problem evidence present for every `ADOPT`/`EXPERIMENT`?
5. Is existing target capability checked?
6. Are source and destination evidence strengths distinct?
7. Is at least one credible non-adoption reason tested for every top pattern?
8. Are license/provenance gates explicit when code/assets are involved?
9. Are multi-source independence and variants handled correctly?
10. Are material pattern interactions identified?
11. Does each `EXPERIMENT` contain a falsifiable test/spike spec?
12. Are mandatory blockers surfaced in the executive verdict?
13. Are weak/negative findings preserved when useful?
14. Would downstream skills receive structured, non-duplicative handoff data?
15. Has the analysis stopped at decision saturation rather than exhausting all available material?
