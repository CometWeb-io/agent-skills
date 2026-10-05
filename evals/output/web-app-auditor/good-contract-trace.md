# Audit report — save journey

- Date: 2026-10-05
- Protocol: web-app-auditor 1.1
- Mode / depth: contract-trace / standard
- Persona: signed-in owner
- Viewports: 1280x800
- Capability profile: hybrid
- Environment: staging
- Mutation policy: safe-test-only
- Confidence: high
- Validator: passed
- Verdict: incomplete

## Verdict

Incomplete. The bounded save journey has a structurally valid trace, but this
report does not authorize a shipping verdict.

## Scope

```text
TARGET: https://staging.example.test/save
MODE: contract-trace
DEPTH: standard
IN: save journey
OUT: unrelated journeys
VIEWPORTS: 1280x800
PERSONA: signed-in owner
CAPABILITY: hybrid
ENVIRONMENT: staging
MUTATIONS: safe-test-only
STOP: trace contract recorded
```

Covered: the named save journey and all required scenario kinds.
Skipped/blocked: durable trace authorization remains incomplete.
Sampling rule: none.

## Counts

| blocker | major | minor | nit | needs-repro | recommendations |
|--------:|------:|------:|----:|------------:|----------------:|
| 0 | 0 | 0 | 0 | 0 | 0 |

## Findings

None.

## Evidence manifest

| Evidence | Type | Location | Supports | Redacted |
|---|---|---|---|---|

## Coverage

```text
total in-scope: 5
tested: 5
sampled: 0
policy-blocked: 0
environment-blocked: 0
unreachable: 0
```

## Recommended next audit

Collect the remaining joined runtime evidence before considering an authorizing verdict.

```json
{"schemaVersion":"1.1","target":"https://staging.example.test/save","mode":"contract-trace","depth":"standard","confidence":"high","verdict":"incomplete","validator":"passed","capabilities":{"profile":"hybrid","browser":true,"source":true,"screenshots":true,"console":true,"network":true,"filesystem":true,"codeExecution":true},"environment":{"kind":"staging","mutationPolicy":"safe-test-only"},"scope":{"in":["save journey"],"out":["unrelated journeys"],"viewports":["1280x800"],"persona":"signed-in owner","covered":["save journey"],"skipped":[]},"counts":{"blocker":0,"major":0,"minor":0,"nit":0,"needsRepro":0,"recommendations":0},"findings":[],"evidence":[],"coverage":{"totalInScope":5,"tested":5,"sampled":0,"policyBlocked":0,"environmentBlocked":0,"unreachable":0},"contractTrace":{"trace":{"schema":"cometweb.contract-trace/v1","revision":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","build":"build-1","environment":"staging","journey_id":"save","claim":"incomplete","nodes":[{"id":"ui","kind":"ui"},{"id":"api","kind":"api"},{"id":"job","kind":"job"},{"id":"durable","kind":"durable"}],"evidence":[{"id":"E1","channel":"browser","locator":"browser-run-1"},{"id":"E2","channel":"joined","locator":"joined-run-1"}],"edges":[{"id":"ui-api","from":"ui","to":"api","kind":"request","state":"pass","evidence_ids":["E1"]},{"id":"api-job","from":"api","to":"job","kind":"job","state":"pass","evidence_ids":["E2"]},{"id":"job-durable","from":"job","to":"durable","kind":"durable","state":"pass","evidence_ids":["E2"]}],"scenarios":[{"id":"happy","kind":"happy","status":"pass","evidence_ids":["E2"]},{"id":"null","kind":"null_partial","status":"pass","evidence_ids":["E2"]},{"id":"retry","kind":"retry_duplicate","status":"pass","evidence_ids":["E2"]},{"id":"tenant","kind":"wrong_tenant","status":"pass","evidence_ids":["E2"]},{"id":"rollback","kind":"rollback","status":"pass","evidence_ids":["E2"]}]},"result":{"schema":"cometweb.contract-trace-result/v1","status":"VALID","result":"incomplete","errors":[]}}}
```
