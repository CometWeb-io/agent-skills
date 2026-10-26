# Targeted false-green prompts

Use these prompts for a concrete unresolved failure mode. This is not a mandatory
second review or a requirement to produce another report. Search specifically for
false-green paths in the affected gate.

## Questions to test

Relevant questions:

- Was a required gate omitted rather than passed?
- Was a risk flag set to `no` without evidence?
- Is evidence from another commit/build/environment/configuration?
- Did a green suite skip the actually changed critical path?
- Is a supposedly verified check missing candidate/timestamp binding?
- Is rollback/recovery theoretical rather than operationally credible?
- Can migration/retry/idempotency behavior corrupt data or money?
- Are alerts present but unactionable or unowned?
- Could users be charged incorrectly, lose entitlements, get locked out, or lose data?
- Was a `MAJOR` risk disguised as `PASS_WITH_CONTROLS` without a real control?
- Was risk acceptance used without authority or after expiry?
- Did `N/A` remove inconvenient scope?
- Did a current vendor/platform/security/legal claim rely on stale evidence?
- Did a release after an incident verify the actual regression/failure mode?

## After the red-team

Any new material unknown must re-enter the manifest and gate logic. Update the
manifest and re-run the engine; do not manually override the engine result, and do
not preserve a previous verdict for consistency.
