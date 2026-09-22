# Audit model

## Modes

- **LIGHT**: one skill, bounded structure/routing/reference scan.
- **STANDARD**: full package audit with eval and packaging checks.
- **DEEP**: topology inventory, overlap graph, executable coverage, mutation/branch evidence where available, package-after-unzip verification, and host-claim audit.
- **DELTA**: compare an identified prior version and audit changed plus invalidated surfaces.

## Severity

Use `BLOCKER / MAJOR / MINOR / NOTE`. BLOCKER/MAJOR require concrete evidence and locator. Unknown material evidence yields `DEFER`, not an invented failure or green pass.

## Static vs empirical truth

Static package quality can prove structural properties. It cannot prove that a stochastic model will discover the skill, follow it, or improve task outcomes. Route those questions to `skill-evaluator`.
