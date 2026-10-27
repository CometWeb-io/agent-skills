# Runtime receipt observability and drift

`tooling/runtime_observability.py` reads existing real-host-eval receipts and
exports a privacy-filtered snapshot or an OTLP/HTTP log request. It never starts
a host, reads an answer/transcript, fetches a price table, sends telemetry or
changes collector configuration. There are no new runtime dependencies.

```bash
uv run python tooling/runtime_observability.py export runs/example > snapshot.json
uv run python tooling/runtime_observability.py export runs/example --format otlp > logs.otlp.json
uv run python tooling/runtime_observability.py drift runs/reference runs/current \
  --thresholds reviewed-thresholds.json > drift.json
```

The reader supports real-host manifest/record/grades v1/v2 and plan v1/v2/v3.
It opens only `manifest.json`, `plan.json`, optional `grades.json`, and each
`runs/*/record.json`. Inputs are bounded; symlink files/directories, malformed
JSON, duplicate keys, duplicate cells and inconsistent available identities are
refused. Missing metadata remains unknown. The plan's self-fingerprint is
checked when present, but underlying source files are not fetched or rehashed.
Receipt hashes establish integrity comparisons, not execution authenticity.

## Exported data and privacy

The JSON snapshot has a fixed allowlist. It contains known execution statuses,
condition, repetition, reported usage/counters, measured elapsed time and
fingerprints of the recorded task/case/source/model/configuration identities.
Unknown values remain JSON `null`. No value is inferred from prompt size,
bytes/4 estimates, requested model names, token assumptions or price tables.

All free-form strings, including model, host version, task, case and run IDs,
leave the reader only as SHA-256 identities. Literal host names and conditions
come from closed enums; arbitrary CLI-version or model strings cannot smuggle
paths or credentials into telemetry. Fingerprints hash canonical JSON strings
or objects, as appropriate. Raw identifiers can be resolved against the locally
retained receipts; the export contains no reverse lookup. These are stable
pseudonyms, not a promise of anonymity against dictionary attacks.

Prompts, fixtures, outputs, command arguments, environment values, error text,
filenames and private paths are never copied to exports. Loading `plan.json`
reads its prompt fields into memory, but only the complete task fingerprint
crosses the export boundary. Errors use fixed redacted diagnostics. Keep source
receipts private and independently review their provenance.

| Field | Source and limit |
| --- | --- |
| `identity.host` | Known host enum, only when a recorded version probe exists |
| `host_version_sha256` | Fingerprint of the recorded version probe, never its free text |
| `model_sha256` | Observed record model; never falls back to `model_requested`; unavailable metadata stays null |
| `input_tokens`, `output_tokens` | Recorded parser counters only; missing counters stay null |
| `elapsed_seconds` | Recorded elapsed measurement, including a failed attempted execution |
| `num_turns` | Recorded turn count, if available |
| `tool_calls`, `retries`, `reasoning_tokens`, `context_tokens`, `peak_memory_bytes` | Explicit recorded counters only; never derived from turn counts or attempt numbers |
| `cost_usd` | Retained only with `cost_source: host_reported`; estimates and unlabelled costs become null |
| `output_contract`, `routing` | Optional matching grade row's pass/fail, only for completed execution |
| `task_success` | Always null: these receipts do not supply independently validated task outcomes |

Host-reported cost does not require a local price table. Without a reported
cost, no monetary measurement is invented. Counts under an unexecuted receipt
are rejected. Supported v3 `resources` fields must agree with legacy top-level
fields when both exist. `output_contract` is explicitly a supplied structural
assessment, not task success or evidence that a cited source exists. Legacy
grades do not bind individual output bytes, so these statuses are exported for
inspection and excluded from drift thresholds.

Every snapshot states `evidence_authentication: not_performed` and
`task_quality: not_assessed`. Explicit synthetic receipt classification is
retained; all other receipts remain `unverified_receipts`. A label, a parser
counter or the exporter cannot independently prove that a model actually ran.

## OTLP/HTTP JSON logs

The optional format is a JSON-encoded `ExportLogsServiceRequest`, with one log
record per receipt. It follows the official OTLP JSON mapping: lowerCamelCase
protobuf fields, decimal strings for 64-bit integers, and the standard
`resourceLogs` / `scopeLogs` / `logRecords` envelope. Transport uses an HTTP POST
to `/v1/logs` with `Content-Type: application/json`.
[OTLP specification](https://opentelemetry.io/docs/specs/otlp/#json-protobuf-encoding),
[collector logs request definition](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/collector/logs/v1/logs_service.proto).

The structured body uses the protocol's `AnyValue` / `KeyValueList` types.
A snapshot null becomes an empty `AnyValue`, rather than a zero or an invented
string value. `observedTimeUnixNano` records the exporter's actual collection
time; the original event timestamp is omitted because the receipts do not
record it. No trace/span identity is invented. These are application-specific
log bodies, not new OpenTelemetry semantic conventions or native metric streams.
[AnyValue definition](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/common/v1/common.proto),
[log record definition](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/logs/v1/logs.proto).

A local standard collector can receive the generated file using its OTLP HTTP
receiver and a log pipeline. For example, with that receiver already listening
on localhost:

```bash
curl --fail-with-body -H 'Content-Type: application/json' \
  --data-binary @logs.otlp.json http://127.0.0.1:4318/v1/logs
```

This is an explicit sending command for the operator; the Python exporter
never sends it. Inspect the response body for partial rejection as well as
HTTP status. Replaying a file can duplicate logs; no delivery, deduplication or
remote-retention guarantee is provided. Export in bounded run directories to
stay within the collector's request-size policy.

A synthetic payload from this implementation was received by official
`otelcol` **0.164.0** over localhost with HTTP 200, no rejected log records, and
its debug exporter read back the structured counters and redacted identities.
The downloaded Darwin ARM64 release archive matched SHA-256
`8d8acf4ffce7fe1af35932d573d877d6a5ef395c29a18fda760711b800757e7d`.
This establishes local collector ingestion of a synthetic export, not model
execution, task quality, authentication, or acceptance by every collector.
No collector binary or dependency was added to the repository.

## Drift contract

Thresholds are explicit, nonnegative absolute increases in the mean of a
**single metric within a single condition**, across exactly matched task/repeat
cells. Smaller values are treated as preferable for this resource monitor;
that does not mean a shorter answer or fewer tool calls is a better answer.
Different conditions and different metrics never cancel each other out.

```json
{
  "input_tokens": {"max_increase": 100},
  "elapsed_seconds": {"max_increase": 0.5}
}
```

Allowed metric names are the resource fields listed above. Every chosen metric
must be present in every compared cell. Cost thresholds require reported costs
on both sides. There is no default threshold or composite quality/cost score.
Threshold arithmetic uses decimal values before JSON display, avoiding false
regressions from binary float subtraction or lost large integer deltas.

The comparator requires exact, non-missing identities for plan, candidate,
payload, rubric, benchmark, host configuration, run configuration, observed
host/version, task, case/source and observed model. It also requires the same
condition/repeat cells, a complete nonempty receipt inventory and completed
execution in every cell. V3 adds required harness, bundled tool and per-condition
payload fingerprints. A mismatch or absent identity/measurement produces
`comparison_status: blocked`; no resource delta or threshold verdict is emitted.
Use the standalone snapshot export to inspect raw available measurements.

This deliberately compares repeated observations of the **same candidate and
configuration**, not different software releases or models. A new candidate,
case, provider model identifier or configuration belongs to a separately
reviewed experiment. Missing metadata cannot be made comparable by omission.

For a compatible comparison, each condition/metric axis independently returns
its two means, absolute delta, supplied maximum increase, and
`within_threshold` or `threshold_exceeded`. There is no scalar score. Such a
result is descriptive over supplied receipts: unmeasured hardware load,
provider revision, effort and receipt authenticity prevent causal or general
model-performance claims. The result explicitly withholds model qualification
and task-quality assessment. Independent `task_outcome.py` evidence could be
integrated in a later capture contract; this reader does not infer it.

API entry points are `read_receipts(path)`, `export_otlp(path)` and
`compare_receipts(reference, current, thresholds)`. The CLI exits 0 for a valid
export or a comparable drift observation with every selected axis within its
threshold; 1 for blocked/exceeded drift; 2 for invalid input. Exit 0 never
provides release authority or establishes task success.
