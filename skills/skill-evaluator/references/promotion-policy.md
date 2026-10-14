# Promotion policy

A challenger is promotion-eligible only when:
- the experiment actually ran;
- candidate and baseline used comparable frozen conditions;
- there are no material invariant regressions;
- the primary success metric has a positive delta and clears the predeclared minimum;
- performed model grading declares CALIBRATED after independent ground-truth calibration;
- trigger precision/recall meet their floors;
- resource usage stays inside the declared budget or the result is explicitly treated as a tradeoff.

`NO_MATERIAL_CHANGE` is a valid result. Do not force every iteration to produce a winner.

Calibration contrasts must distinguish permissible requests for missing task-relevant evidence from unauthorized retrieval or disclosure. Judge agreement measures consistency, not the validity of a criterion. The validator checks supplied declarations, not authentic calibration or source truth. Invalid flags, absent case identities and nonfinite policy values cannot become promotion evidence.
