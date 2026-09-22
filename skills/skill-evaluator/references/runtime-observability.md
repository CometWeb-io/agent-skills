# Runtime observability and comparative efficiency

Real-host evaluation should record quality, trigger precision/recall, tokens, latency, host/model/harness identity, and judge agreement when an LLM judge is involved.

Do not collapse quality and cost into one arbitrary weighted score. Prefer a Pareto frontier: a candidate is dominated when another candidate is at least as good on quality and no worse on every tracked resource dimension, with a strict improvement on at least one dimension.

Judge agreement is evidence about grading reliability, not artifact quality. Low inter-judge agreement requires adjudication or a stronger deterministic grader before promotion.

Trend/drift claims require identical rubric/benchmark identity and comparable host/model/harness conditions; otherwise rebase.
