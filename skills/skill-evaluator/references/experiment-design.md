# Experiment design

Freeze before running:
- candidate version/hash;
- baseline (`NO_SKILL` or prior version/hash);
- eval suite hash and full case IDs;
- host, model, reasoning effort and harness version;
- grader policy;
- run count;
- token/cost/duration budgets;
- exclusions and stop rules.

Maintain separate discovery, forced-invocation and negative-trigger cases. Discovery measures whether the host selects the skill naturally; forced invocation isolates instruction quality after routing succeeds.
