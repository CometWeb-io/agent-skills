# Connector playbook

Use the minimum connector reads that can make the product decision-ready.

## GitHub

### First-pass reads
1. Resolve exact repository and default branch.
2. Read repository metadata and relevant README/manifests only if they help scope.
3. Read recent relevant PRs/commits/issues for the current goal/release.
4. Read CI/workflow/release state when verification/shipping matters.
5. Search code only for unresolved implementation claims, then fetch exact files.

### Do not
- infer current implementation from an old branch;
- treat open issue text as code truth;
- scan the entire repository before knowing the question;
- equate merged PR with deployment.

## Notion

### First-pass reads
1. Search named product/roadmap/release/decision.
2. Fetch candidate pages in full before relying on snippets.
3. Fetch database/data-source schema before SQL/view queries.
4. Query only rows relevant to current horizon/scope/status.
5. Preserve last-edited information when available.

### Do not
- use stale snippets as current planning truth;
- hardcode private database IDs in a public skill;
- treat `Done` as implementation evidence.

## Product context

Prefer explicit user directive or named canonical context. `.agents/product-marketing.md` is a strong default
when available. If only README/landing copy exists, mark intent `INFERRED` unless explicitly authoritative.

## Outcome data

Only retrieve outcome evidence if the current decision depends on it. Avoid expensive broad analytics/customer
research when the immediate bottleneck is implementation or release verification.

## Retrieval expansion rule

Expand from metadata -> targeted records -> exact artifacts. Expand further only if a missing dependency,
contradiction, or evidence gap can change BLOCKER/VERIFY NOW/NOW/NEXT.
