# GitHub Customer-to-Engineering Loop v2

## Contents

1. Purpose
2. Repository reconnaissance
3. Dedupe and related work
4. Engineering-readiness gate
5. Symptom vs cause
6. Privacy/publication boundary
7. Issue structure
8. Relationships, sub-issues, dependencies
9. Create/update rules
10. Fix, release, verification
11. Regression handling
12. Feature/feedback boundary
13. Anti-patterns

## 1. Purpose

Convert customer evidence into actionable engineering work **without issue spam, PII
leakage, invented root cause, or premature customer closure**.

One engineering issue should usually represent one underlying defect/problem in a coherent
technical scope, not one customer conversation.

## 2. Repository reconnaissance

Before proposing repository-specific metadata, inspect what the repository actually uses:

- issue templates/forms,
- issue types,
- labels/priorities,
- assignee/team conventions,
- milestones/projects,
- parent/sub-issue/dependency patterns,
- bug-report expectations,
- security reporting policy where relevant.

Do not invent `P0`, `customer`, `incident`, or other labels/types merely because Customer
Ops uses those concepts.

If current GitHub behavior/features are material to the operation, use the available
GitHub tool/current official docs rather than encoding assumptions in this skill.

## 3. Dedupe and related work

Before new issue creation:

1. search open and recently closed issues with symptom/component/error terms;
2. search related PRs when a likely fix already exists;
3. compare customer symptom, trigger, environment/version, error signature, and time window;
4. inspect closest candidates rather than relying on titles alone;
5. decide `LINK_EXISTING | REVIEW_NEAR_DUPLICATE | CREATE_NEW`.

A deterministic `dedupe-key` is only a stable candidate fingerprint for structured input.
It is not semantic proof that two problems are the same.

### Reuse existing issue when

- customer-visible failure is materially the same,
- environment/trigger differences are compatible with the same defect,
- the existing issue remains the right engineering owner/scope.

### Create separate issue when

- failure mode/root scope is materially different,
- apparent regression requires distinct tracking by repo convention,
- existing issue is a broad parent and the new work is a distinct implementation task,
- combining would make verification/ownership ambiguous.

Preserve links either way.

## 4. Engineering-readiness gate

Do not require perfect reproduction for severe credible problems, but make missing evidence
explicit.

Minimum useful issue pack:

```text
customer-visible symptom
expected behavior
actual behavior
reproduction status / diagnostics
affected environment/version when relevant
known breadth: cases + accounts
impact / operational priority rationale
workaround status
source/internal case or cluster IDs
verification / acceptance criteria
dedupe search status
privacy preflight status
```

Use the kernel `case-gate` with `stage=GITHUB_READY` when code execution is available.

Possible readiness:

- `PASS` — enough actionable evidence to create/update.
- `WARN` — creation may be justified by impact but evidence gaps must stay visible.
- `BLOCK` — unsafe publication/identity/target/dedupe state unresolved.

## 5. Symptom vs cause

Write customer-observable facts first.

Good:

```text
Symptom: Export returns an empty CSV for workspaces above ~1,000 rows.
```

Not supported unless engineering evidence exists:

```text
Root cause: database pagination bug.
```

Use labels:

- `suspected cause` for hypothesis,
- `confirmed cause` only after engineering/postmortem evidence.

A high-confidence symptom can justify engineering work without a confirmed cause.

## 6. Privacy and publication boundary

Never include unnecessary:

- access tokens/passwords/cookies/auth headers,
- customer email/phone/name when an internal ID suffices,
- private URLs containing credentials/tokens,
- raw confidential customer datasets,
- contractual/commercial detail unrelated to debugging,
- security exploit detail in a broad/public issue.

Prefer:

```text
CASE-123
ACC-456
restricted evidence: <approved internal reference>
```

Run `privacy-scan` before publishing generated issue text when code execution is available.
Treat it as best-effort only; manually review context/sensitivity.

If private artifacts are necessary for reproduction, link to an approved restricted
location rather than copying them into GitHub.

## 7. Issue structure

Use `assets/github-issue-template.md` unless the repository provides a required template/
form. Repository template wins.

Good title pattern:

```text
<Customer-visible failure> <scope/context if material>
```

Examples:

- `Export returns empty CSV for large workspaces`
- `OAuth reconnect loops after token expiry`

Avoid:

- customer names,
- urgency theater (`URGENT!!!`),
- guessed root cause,
- unrelated commercial context.

### Body principles

- customer impact before implementation theory,
- known vs suspected scope separated,
- reproduction state explicit,
- case/account counts distinct,
- verification criteria tied to customer outcome,
- internal IDs instead of raw customer data.

## 8. Relationships, sub-issues, dependencies

Modern GitHub environments may support parent/sub-issue and blocked-by/blocking
relationships. Use them **only when the repository/tool currently supports them and the
relationship models real work**.

Useful patterns:

### Problem cluster as parent

Use a parent issue only when the repo uses parent/sub-issue structure and one customer
problem requires multiple independently owned implementation tasks.

### Dependency

Use blocked-by/blocking relationship when an issue truly cannot progress until another work
item completes.

### Do not over-model

Do not create sub-issues for:

- each affected customer,
- each support message,
- trivial checklist steps,
- links that add hierarchy but no ownership/verification value.

If connector/tool support for relationships is unavailable, preserve links in the issue
body/comment instead of claiming a native relationship was created.

## 9. Create/update rules

### Create

Create only when:

- user explicitly requested creation,
- target repo is known,
- dedupe/related-work check completed when search is available,
- privacy publication boundary is clear,
- engineering-readiness is sufficient for impact.

Otherwise return an exact draft under `Needs approval`.

### Update

Good reasons:

- materially larger/smaller breadth,
- new reproduction evidence,
- verified workaround,
- newly confirmed cause,
- regression,
- meaningful customer-impact clarification,
- verification result,
- relationship/dependency update.

Do not spam issue comments with every support interaction. Aggregate customer evidence.

### Labels/assignees/priority

Use repository conventions. If Customer Ops priority has no repo mapping, write it as
context in the body rather than inventing a label.

## 10. Fix, release, verification

Issue/PR state is only one layer:

```text
issue state -> PR merged -> release/deploy -> customer-visible verification -> case closure
```

After engineering says fixed:

1. identify whether the relevant change is deployed/released where needed;
2. re-test original symptom or obtain customer confirmation;
3. check representative affected accounts/environment when breadth was material;
4. update case/cluster/incident exposure outcome;
5. reconcile open commitments;
6. send/prepare customer follow-up when authorized;
7. close customer case only after closure gate passes or approved exception.

Do not use `closed issue`, `merged PR`, or `CI green` as sole proof of customer resolution.

## 11. Regression handling

Preserve lineage:

```text
original case/cluster
 -> issue
 -> fix PR
 -> release/deploy
 -> verification
 -> regression report
 -> reopened issue OR new regression issue
```

Choose reopen vs new issue according to repository practice and whether the engineering
scope is genuinely the same.

A failed customer verification should immediately invalidate "verified fixed" state even
if the original issue remains closed.

## 12. Feature/feedback boundary

Not every requested capability belongs in GitHub engineering backlog.

If evidence is primarily discovery/prioritization:

1. create/update the customer problem cluster;
2. produce a product evidence pack;
3. route product decision-making;
4. create engineering work only after the product/engineering decision requires it.

This prevents support volume from silently turning into roadmap priority.

## 13. Anti-patterns

Do not:

- create one issue per customer for the same defect,
- merge near-duplicates from title similarity alone,
- put raw email threads/customer names/secrets into issues,
- invent repo labels/types/assignees,
- state suspected cause as root cause,
- close customer cases when GitHub closes,
- promise deploy date from a PR estimate,
- use parent/sub-issues/dependencies just because the feature exists,
- convert every feature request directly into engineering work,
- blindly retry issue creation after a timeout without checking whether it succeeded.
