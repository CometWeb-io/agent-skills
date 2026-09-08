# Multi-target synthesis

## Table of contents

1. Goal
2. Normalize source instances
3. Pattern families
4. Convergence and divergence
5. Independence discipline
6. Destination selection
7. Failure modes

## 1. Goal

The goal of multi-source teardown is not to rank companies or produce mini-profiles. It is to identify mechanism families, contextual variants, and transfer conditions that a destination can act on.

## 2. Normalize source instances

For each source, first create an instance-level candidate:

- source target and version;
- problem addressed;
- observed behavior/implementation;
- mechanism hypothesis;
- evidence IDs;
- local dependencies and constraints;
- observed variant.

Do not cluster source instances that only look visually similar while solving different problems.

## 3. Pattern families

Group candidates into a family only when they share the same underlying problem and materially similar mechanism.

A family should contain:

```text
Family ID / name
Underlying problem
Canonical mechanism
Source instances
Important variants
Shared transfer conditions
Variant-specific conditions
Evidence coverage
Outcome evidence, if any
Destination-relevant variant
Why other variants were not selected
```

Prefer one family with variants over several duplicate patterns.

## 4. Convergence and divergence

Treat convergence as evidence of prevalence or ecosystem convention, not causal effectiveness.

Useful convergence signals:

- multiple independent products arrive at a similar interaction mechanism;
- several repos use equivalent architectural boundaries under similar constraints;
- recurring failure/recovery mechanisms appear across products.

Useful divergence signals:

- enterprise vs self-serve permission models;
- synchronous vs async workflows;
- mobile vs desktop interaction constraints;
- different scale/data/latency assumptions;
- different monetization/value metrics;
- different architecture/team topologies.

Divergence can be more informative than consensus because it reveals transfer conditions.

## 5. Independence discipline

Do not count repeated claims as independent if they originate from:

- the same vendor documentation copied across pages;
- forks of the same codebase;
- wrappers around the same underlying platform;
- articles repeating the same announcement;
- products using the same default library behavior.

Use an `independence_group` in evidence when this matters.

## 6. Destination selection

Do not select the most common variant automatically.

Choose based on:

- destination problem and JTBD;
- target constraints;
- existing capability;
- business model;
- architecture/data model;
- scale/performance needs;
- team and operational capacity;
- differentiation objective;
- reversibility and validation cost.

When two variants are both plausible, emit competing implementation options or an experiment/spike rather than averaging them into an incoherent hybrid.

## 7. Failure modes

Reject these synthesis patterns:

- "3 of 4 products do X, therefore we should do X";
- averaging incompatible designs;
- treating forked codebases as independent evidence;
- ignoring plan/platform/version differences;
- selecting visual similarity over mechanism fit;
- losing minority variants that better match the destination;
- using market prevalence as proof of outcome lift.
