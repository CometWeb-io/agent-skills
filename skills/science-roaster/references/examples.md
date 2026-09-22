# Science Roaster examples

## Strong MAJOR finding

**Observed:** Methods state that the reference instrument was not independently calibrated.

**Risk:** absolute validity inherits unknown reference uncertainty.

**Falsifier pass:** searched calibration appendix and uncertainty reporting; none present in reviewed scope.

**Repair:** characterize uncertainty and propagate it into the validation result.

## Bad finding

> The authors clearly did not calibrate the device properly.

Why it fails: if calibration is merely unreported, `NOT_REPORTED` is required. The statement silently converts missing reporting into missing method.

## Withdrawn finding

Initial concern: no multiple-comparison control. Falsifier pass finds the relevant analysis is explicitly exploratory and no confirmatory familywise claim is made. Withdraw or narrow the criticism.

## Fatality discipline

A FATAL issue must kill the central inference, not merely annoy a reviewer. Typo, missing citation detail, or weak prose cannot become FATAL because the requested tone is harsh.

## Inferential-type mismatch

A descriptive four-device fixture can support a `DESCRIPTIVE` claim about those tested profiles. It does not automatically support a `TRANSPORT` claim about hardware classes in general. The problem is the inferential jump, not the existence of the descriptive result.

## REVISION review

A reviewer asks for uncertainty propagation. The revision adds a paragraph saying uncertainty is a limitation but adds no analysis. Keep the stable finding key and mark it `OPEN`; prose acknowledgment is not the requested scientific repair.

## Challenger / Defender / Arbiter example

**Challenger:** repeated observations are analyzed as independent and the reported uncertainty may therefore be too narrow.

**Defender search:** inspect model specification, clustering, random effects, resampling unit, sensitivity analyses, supplement, and any explicit estimand that makes the dependence irrelevant.

**Arbiter:** keep MAJOR only if the dependence affects a material claim and no adequate correction or robustness analysis defeats the concern. Otherwise narrow or withdraw it.

The final report contains the post-arbitration inference, not the harshest available wording.
