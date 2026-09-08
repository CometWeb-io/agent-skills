# Repository teardown playbook

## Table of contents

1. Establish repository truth
2. Build architecture map
3. Trace capabilities end to end
4. Inspect engineering systems
5. Detect pattern boundaries
6. Verify production relevance
7. Licensing and reuse
8. Destination transfer checks

## 1. Establish repository truth

Before interpreting architecture, identify:

- repository purpose and active product/component;
- default branch and relevant release/tag/commit;
- language/runtime/package manager;
- monorepo/workspace boundaries;
- build/test commands;
- deployment/runtime model if evidenced;
- license and relevant notices.

Distinguish shipped code, examples, experiments, generated files, vendored code, deprecated code, migrations, and tests.

## 2. Build architecture map

Inspect coarse to fine:

1. manifests/workspaces/build configuration;
2. entrypoints/composition roots;
3. module/service/package boundaries;
4. domain/data/schema definitions;
5. external integration boundaries;
6. async/background/event flows;
7. frontend state/design-system/component boundaries;
8. configuration/feature flags/secrets boundaries;
9. deployment/observability surfaces when relevant.

Do not start from arbitrary leaf files.

## 3. Trace capabilities end to end

For a capability relevant to the teardown, trace when possible:

`UI/API entry -> validation/auth -> orchestration -> domain logic -> persistence/external call -> event/job -> response/state update -> tests -> observability/recovery`

This reveals implementable mechanisms and hidden dependencies better than file summaries.

Record uncertainty when code generation, dynamic dispatch, external services, runtime flags, or missing repositories prevent a complete trace.

## 4. Inspect engineering systems

Inspect only if relevant to transferable patterns:

- critical-path tests/test pyramid;
- CI gates/required checks;
- migrations/backfills;
- release/versioning/change management;
- logs/metrics/tracing/error reporting;
- queues/retries/idempotency;
- caching/performance boundaries;
- feature flags/experimentation;
- local developer setup/fixtures;
- code generation/schema contracts;
- dependency update policy;
- incident/recovery tooling;
- permission/secrets boundary.

Separate "exists" from "is consistently used".

## 5. Detect pattern boundaries

Good repo patterns explain a tradeoff, for example:

- capability boundary that localizes change;
- schema-driven contract preventing drift;
- durable job orchestration isolating slow work;
- adapter layer containing vendor coupling;
- migration strategy preserving compatibility;
- fixture/test abstraction reducing setup cost;
- observability mechanism tied to recovery;
- permission boundary reducing privilege spread.

Bad candidates are library names, style preferences, or isolated utilities with no target problem.

## 6. Verify production relevance

Code presence does not prove production use.

Look for supporting evidence when material:

- registration/wiring from composition root;
- runtime config/feature flag defaults;
- tests covering active path;
- release notes/migrations;
- deployment manifests;
- active references/call sites;
- issue/PR history tied to the capability.

Mark uncertain when a path may be dead, experimental, optional, or disabled.

## 7. Licensing and reuse

Before recommending copying code:

- inspect repository license;
- inspect relevant file notices/headers;
- distinguish permissive, copyleft, source-available, dual-license, and proprietary constraints without overclaiming legal interpretation;
- note attribution/notice obligations evidenced by the license;
- inspect embedded/vendored dependency provenance when relevant.

Prefer semantic reimplementation when the user needs the mechanism and reuse rights are uncertain.

## 8. Destination transfer checks

Before mapping source architecture into target repo, inspect target evidence for:

- equivalent boundary/capability;
- language/runtime/deployment constraints;
- data/schema compatibility;
- auth/permission model;
- scale/latency/reliability requirements;
- observability/support maturity;
- migration burden;
- team ownership/topology.

Do not transplant source architecture because it is sophisticated. Require a target problem and fit.
