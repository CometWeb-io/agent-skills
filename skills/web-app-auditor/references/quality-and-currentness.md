# Verify user impact and distinguish inspection from proof

Maintainer review: 2026-09-12. This date does not certify live task inputs.

Start with environment, persona, scope, state matrix, permissions, and available
browser/source/network capabilities. Track tested, sampled, policy-blocked,
environment-blocked, and unreachable controls separately. Missing coverage must not
produce a clean shipping verdict. A confirmed blocker can still justify do_not_ship
when other controls remain untested.

Verify the full state transition: action, request, persisted state, response, display,
and recovery. Cover loading, empty, partial, stale, failure, denied access, race,
retries, cancellation, and cross-project/account switching where applicable. Reconcile
UI totals and units with authoritative data. Test cross-tenant access only within
explicitly authorized test accounts and scope; do not expose customer data.

Use a criterion/version and a measured observation for standards findings. WCAG 2.2
AA target size is 24 by 24 CSS pixels with specified exceptions, not a universal
44-pixel rule [wcag22]. WCAG 3 remains a draft, not a replacement conformance baseline
[wcag3-status]. For accessibility review also inspect keyboard/focus, names/roles,
errors, reflow, zoom, contrast, and authentication in the applicable scope.

Heuristics are diagnostic prompts, not automatic defects [usability-heuristics]. Use
versioned ASVS references for security expectations [asvs]. A screenshot cannot prove
keyboard operability, backend authorization, persisted state, or overall conformance.
A valid report structure does not prove its screenshots exist; verify evidence artifacts
and reproduction separately. Dedupe by root symptom and affected job, not scanner count.

## Evidence that would block acceptance

Stop approval when a decisive claim lacks an inspectable source, a required operation
was not executed, a protected invariant changes, or validation fails. Return the
bounded result and the specific missing evidence; do not fill the gap with confidence.

## Task-time source checks

Open the applicable current primary/system-of-record source before relying on a volatile
claim. Record actual version, effective/observed time, scope, and retrieval limitations.
The shared source-review ledger schedules maintenance; it cannot establish currentness
of every operational claim. Stable methodological guidance above is an editorial
operating policy, not a claim of a new universal standard.

- `wcag22`: https://www.w3.org/TR/WCAG22/
- `wcag3-status`: https://www.w3.org/TR/wcag-3.0/
- `asvs`: https://owasp.org/www-project-application-security-verification-standard/
- `usability-heuristics`: https://www.nngroup.com/articles/ten-usability-heuristics/
