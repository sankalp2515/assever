# Local operation

Start from this directory: `docker compose -f compose.assever.yml up --build -d`. Open http://localhost:8088. Readiness is `/health/ready`; interactive OpenAPI is `/docs`. The database and effect service have no published ports. Explicit /24 subnets avoid this workstation's exhausted automatic Docker address pools; change them if they conflict on another host.

Stop without deleting state: `docker compose -f compose.assever.yml stop`. Start again with `up -d`. Do not use `down -v` for normal restarts. Each synthetic visitor receives a random tenant/actor, a 24-hour HttpOnly session and a separate root per purchase. No shared reset API exists. Start another workspace in a separate browser context to test isolation.

The server applies strict DTOs, a 64-KiB request-body limit including chunked input, and an in-process per-identity 300-request/minute limit. These limits are for a local prototype, not distributed abuse protection. Admission requires ledger access and effect-service readiness; no SQLite or permissive fallback exists. Required dependency failure returns an explicit error. Model-free typed planning is always available. Local models, if installed, are explicit optional proposals; a failed invocation is never replaced by a fabricated live response.

`GET /v1/metrics` returns scoped operation counts, exposure, oldest operations, queue state and maximum query attempts. Compare age with `observed_at`. Events and responses include stable IDs; middleware assigns a correlation ID. Access logging is disabled to avoid credential/query leakage. Never print request headers or environment secrets. Keys are injected by environment, versioned issuer keys are named `ISSUER_KEY_V1`, and retired issuer versions fail closed.

The default worker polls every 300 ms. Claims have a 15-second lease. Crash recovery queries prior effects instead of sending again. Query backoff is bounded at 60 seconds. After eight cycles, the operation is escalated while the reservation stays unknown. An operator can request another reconciliation using the current operation revision. A pending local outbox operation may be cancelled only while the root and unclaimed outbox prove no send occurred.

Use `scripts/assever_backup_restore.ps1` to stop API/worker, snapshot both databases, restore into uniquely named verification databases and compare data fingerprints, then restart the stack. Backups remain local artifacts and are excluded from the public code archive. A single PostgreSQL instance is a prototype operational dependency. No public deployment or uptime SLA is included.

## Retention and key handling

The current local research build retains synthetic audit evidence for reproducibility. Use `python -m assever.retention --days 7 --dry-run` to inventory expired raw callbacks/sessions; the explicit `--apply` mode removes expired session records and old callbacks, retaining append-only audit/effect history. Run this inside the API container. Removing source records needed by an old export can weaken future verification; preserve frozen research bundles first. No background retention job silently erases experiment history.

For shared-host preparation, replace all ASSEVER_* local keys, require secure cookies behind HTTPS, disable self-service synthetic enrollment when inappropriate, and scope credentials to distinct services. These are deployment prerequisites, tracked outside this user's requested local implementation. No real personal data is accepted by this finite catalog.
