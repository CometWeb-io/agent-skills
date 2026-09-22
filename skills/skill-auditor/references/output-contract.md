# Output contract

Return:

- `skill_id`, current version/commit, previous version when comparing, and audit mode;
- coverage by audit surface;
- findings with stable IDs, severity, locator, evidence, impact, falsifier, and repair direction;
- semantic-version verdict and direction-aware public contract compatibility;
- for breaking changes: migration guide state plus structured migration plan (`consumer_actions`, `rollback_ref`, `verification_cases`, before/after fixtures when available);
- unsupported or stale host compatibility claims, separating static shape from fresh real-host evidence;
- unknowns/deferred checks;
- package/eval/registry/documentation drift;
- when a regression spans versions, a bounded bisection result using only measurements with the same comparison fingerprint;
- next owner (`skill-creator`, `skill-evaluator`, `quality-loop-operator`, or none).

Never rewrite the audited skill inside the audit result unless a separate authorized update workflow invokes `skill-creator`. Never call a contract change breaking without considering input/output direction.
