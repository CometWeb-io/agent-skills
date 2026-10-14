# Runtime observability and comparative efficiency

Real-host evaluation should record quality, trigger precision/recall, tokens, latency, host/model/harness identity, and judge agreement when an LLM judge is involved.

Do not collapse quality and cost into one arbitrary weighted score. Prefer a Pareto frontier: a candidate is dominated when another candidate is at least as good on quality and no worse on every tracked resource dimension, with a strict improvement on at least one dimension.

Judge agreement is evidence about grading reliability, not artifact quality. Low inter-judge agreement requires adjudication or a stronger deterministic grader before promotion.

Trend/drift claims require identical rubric/benchmark identity and comparable host/model/harness conditions; otherwise rebase.

## Judge calibration before substantive grading

Before trusting model grading, independently check each judge on frozen contrast
anchors with known task evidence and authorization boundaries. Include a permitted
same-project evidence gap, an impermissible request for an unrelated protected
source, a supported useful answer and fabricated evidence. Record the anchor/rubric
hashes, decisions, disagreements and who adjudicated them. Independent agreement
alone is not ground-truth calibration or proof that a criterion measures its target.

Keep epistemic gaps, source requests, executed reads and disclosures separate.
A critical privacy/access finding needs the exact protected value or source/action
and the frozen authorization rule it violates. Merely naming missing relevant
aggregate evidence does not establish unauthorized access. Correctly identifying
such a gap must not become a refusal or access violation solely because the
resource was unavailable.

If calibration or construct validity is unresolved, retain original grades and
mark the comparison insufficient for promotion. Fixing a flawed criterion creates
a new revision for future tests; it does not turn known outputs into a clean
holdout or permit silently rescoring the earlier study.
