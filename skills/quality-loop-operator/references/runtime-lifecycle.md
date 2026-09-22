# Runtime lifecycle

Apply after a SKILL_QUALITY evaluation when deployment/installation rollout is requested.

States: `NOT_REQUESTED`, `READY_FOR_CANARY`, `CANARY_RUNNING`, `READY_FOR_STAGED`, `STAGED_RUNNING`, `READY_FOR_FULL`, `FULL`, `ROLLBACK_REQUIRED`, `DEPRECATED`, `BLOCKED`.

Material changes require canary unless policy explicitly exempts them. Breaking changes require a major version and migration guide. Every material rollout requires a known-good rollback version. Unknown contract compatibility or unknown host runtime support blocks full rollout.

Do not call static shape support a successful canary. Canary evidence is run-bound and host/model/harness specific.
