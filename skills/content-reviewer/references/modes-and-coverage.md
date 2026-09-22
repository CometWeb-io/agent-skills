# Review modes and coverage

Use explicit coverage so a short review is not mistaken for a comprehensive one.

## Modes

- `LIGHT`: inspect the one requested concern plus obvious blockers.
- `STANDARD`: cover the material brief and reader-facing risks.
- `DEEP`: explicitly cover every required review axis and record `COVERED`, `N/A`, or `UNKNOWN`.
- `DELTA`: review only changed surfaces plus interactions that can invalidate previously accepted findings.

Recommended axes: `brief-compliance`, `reader-value`, `structure`, `claim-integrity`, `actionability`, `consistency`, `language-ux`.

## Coverage semantics

`COVERED` means the axis was actually inspected. It does not mean it passed. `N/A` needs a reason. `UNKNOWN` remains an unresolved coverage gap and cannot be silently counted as pass.

## Finding identity

Preserve stable finding identity across re-review. Use `NEW`, `CARRIED`, or `REOPENED`. A carried finding may be treated as current only when it was revalidated against the current candidate.
