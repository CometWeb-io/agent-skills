# Acceptance traceability

In DEEP mode every material acceptance criterion must map to one or more evaluated gates, and every required gate must map back to the contract or an explicitly declared policy profile.

Recommended relation:

`criterion_id -> gate_id -> evidence[] -> result -> candidate_id -> verified_at`.

Traceability proves that the gate set covers the contract; it does not prove the evidence itself is true. Missing traceability is a coverage defect. Missing/weak evidence is an evidence defect. Keep them separate.
