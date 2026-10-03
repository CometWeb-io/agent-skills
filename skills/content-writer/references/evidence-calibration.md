# Evidence calibration

When a quality policy supplies an `evidence_floor`, record an ordinal `evidence_grade` for material supported claims. A/B/C/D describe fitness for use, not truth. Critical claims should normally require A; material claims at least B; supporting claims at least C. The floor keys are `critical` (applied to `high_risk` claims), `material` (other material SUPPORTED claims) and `supporting`; the kernel validates all three but applies only the first two, because it does not grade non-material claims. Never self-upgrade a grade to make a draft releasable.
