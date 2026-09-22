# Migrations and regression bisection

Use this reference for versioned skill releases.

## Breaking changes

A breaking public contract requires more than a MAJOR version and a prose note. Require a migration plan with:

- explicit affected consumers or contract surfaces;
- concrete consumer actions;
- rollback reference to a known-good version;
- before/after contract regression cases;
- verification cases after migration;
- deprecation/removal timing when applicable.

## Regression localization

When behavior regresses across versions, compare only measurements with the same comparison fingerprint: rubric, benchmark, host, model, harness, and material configuration. If those drift, rebase before attributing the regression to the skill version.

For an ordered sequence of comparable versions, locate the last known good and first known bad. A good result after a bad result is non-monotonic and should not be reported as a clean bisection boundary.

When suite tooling is available, use:

- `tooling/migration_planner.py`
- `tooling/regression_bisect.py`
