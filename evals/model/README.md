# Text behavior cases

`hard-all34-suite.json` retains its historical filename and now contains 66 synthetic development cases for 33 active skill labels: one difficult
material task and one narrow scope control per skill label, including the
multiagent alias. Source conflicts, calculations, tenant/version identity,
embedded instructions and permission gates require a useful answer within the
supplied evidence. Cases and outcome obligations were checked before execution;
their presence is not evidence of model success.
Fixture text is wrapped in an object for this runner's schema. This export has
not been executed or qualified through the public model runner.

Context-skill retirement removed its active cases without changing remaining task outcomes; old experiment artifacts are not rescored.

Fixture revision 2 clarified source timezones in the now-retired `h-06` and distinguishes the
scope boundary from a mandatory disclaimer in `h-27`. These additions received
separate design review before new execution. Original ambiguous-run outcomes
remain unknown; the revised fixtures do not retrospectively change their scores.

Grade material task outcomes against the supplied prompt and fixture, without
rewarding skill-specific headings or preferred phrasing. Keep control formatting
requirements explicit, preserve every raw answer, repeat stochastic cases and
lock separate anonymous judgments before exchange. Alias instruction preparation
also includes its registered canonical front door; a missing, cyclic or unsafe
dependency stops preparation. Standalone fixtures without a registry retain
their original single-package behavior.

These cases cover text behavior after instructions are supplied. They do not
measure native discovery, connector actions, production acceptance, token costs
or universal compatibility. The no-skill arm has an empty instruction bundle;
shared host metadata may still expose general skill knowledge. Related skills
and repeated answers are not independent observations. Corpus coverage cannot
establish a release or a claim of superiority.

Inspect the suite without a runner; this command never invokes a model:

```bash
uv run python tooling/run_model_evals.py --suite evals/model/hard-all34-suite.json
```
