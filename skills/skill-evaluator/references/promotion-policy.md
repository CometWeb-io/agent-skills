# Promotion policy

A challenger is promotion-eligible only when:
- the experiment actually ran;
- candidate and baseline used comparable frozen conditions;
- there are no material invariant regressions;
- the primary success metric clears the predeclared minimum delta;
- trigger precision/recall meet their floors;
- resource usage stays inside the declared budget or the result is explicitly treated as a tradeoff.

`NO_MATERIAL_CHANGE` is a valid result. Do not force every iteration to produce a winner.
