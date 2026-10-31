# Integrated local operations

The active profile is `compose.integrated.yml`; root Compose includes it. Use `docker compose -f compose.integrated.yml up --build --wait -d`, then open http://localhost:8000. The earlier `compose.assever.yml` application and its volumes remain stopped and preserved. No cloud deployment is performed.

## Service boundaries

| Service | Responsibility | Published port |
|---|---|---|
| gateway | Existing API, Core engine, original console, authentication and purchase route orchestration | 127.0.0.1:8000 |
| postgres | Existing delegation/public schema, purchase schema and separate effect database/role | None |
| worker | Private outbox dispatch, reconciliation and durable recovery | None |
| effects | Owned synthetic commerce/payment/disclosure adapter | None |
| evaluator | Private scenario execution and offline/research tooling | None |
| models (optional profile) | Local Qwen inference; no provider account | None |
| agents (optional profile) | Original outside agent-team example | None |

Normal startup restores persistent volumes. Migrations create the purchase schema and advance versioned changes under an advisory lock; applied migrations are not replayed. Existing public tables and historical workflows are preserved. The local integrated database is a separate named volume from the retired standalone application. No destructive migration/reset is part of the correction. A built-in business policy appears from `policies/delegate/kirana.yaml`; registered businesses remain in the original store.

Images retain the original content classifier, OCR and ADK dependencies. The classifier is baked into the image and loaded before readiness. Initial startup takes longer than a warm restart; the health check has a five-minute start period. Gateway/worker/effects/evaluator run without Linux capabilities and with no-new-privileges; application containers use read-only filesystems with explicit writable tmp/data storage. The gateway uses the existing unprivileged identity. PostgreSQL and private services have no published port.

The gateway readiness check includes original database/policy/classifier readiness and purchase database/effect-service readiness. Worker health uses a bounded heartbeat age; an error is logged as a type, not credential-bearing request data. `/v1/purchases/metrics` returns owner-scoped operation/exposure/queue data. Original `/readyz`, `/healthz`, `/v1/whoami` and inspection/integration APIs remain available. Purchase bodies are bounded at 64 KiB before parsing, including chunked input. Existing gateway key/role/rate middleware remains authoritative.

Default Compose credentials are only for the synthetic localhost environment. No `.env` file or cloud credential directory is mounted. A gateway-verified agent identity may be recorded in `purchase.agent_principals`, but that registry issues no login token; key validity/revocation is checked by the original KeyRing on each request. Internal buyer roles share their authenticated owner's tenant/root scope. Public users cannot read or mutate isolated research roots via ordinary purchase routes.

## Purchase lifecycle

Attach a supported annex before confirming a work order. Confirming the original contract without the annex, amending its prose through the old route or reporting `/executed` success is rejected for annex-linked work. Use the exact purchase review/lifecycle APIs. Draft edits issue a new review nonce. Exceptions show old/new scope, expire, and are exact single-use owner actions. Business-policy changes stop future admissions; they do not erase already admitted obligations. A materially new task should receive a new delegation and approval.

Prepare does not execute or reserve. Commit atomically locks current root authority, reserves gross budget/units/count and writes the outbox. The executor preserves stable IDs, exact payloads and fences. After a possibly sent operation, reconcile rather than resubmit. Opaque status stays UNKNOWN and retains exposure. Only proven no-effect closure or fenced unsent cancellation releases it. After bounded repeated reconciliation the item is escalated, not silently closed. Gross entitlement is not restored by a refund notice.

The same transaction that records significant purchase events mirrors their source hashes into original workflow receipts. This joins the work-order report to provider-qualified consequences. The offline bundle includes reviewed original contract, annex, frozen business policy, source effects and both audit chains. Authenticity still depends on trustworthy source capture; the local prototype does not sign exports with KMS. BigQuery configuration remains in the original integration; mirroring creates durable source receipts, but delivery/analytics qualification in Google Cloud is deferred to the later authorized deployment.

## Commands

```powershell
docker compose -f compose.integrated.yml ps
docker compose -f compose.integrated.yml logs --tail 100 gateway worker
docker compose -f compose.integrated.yml stop

# Optional model service and weights (new host):
docker compose -f compose.integrated.yml --profile models up -d models
docker compose -f compose.integrated.yml exec -T models ollama pull qwen2.5:0.5b
docker compose -f compose.integrated.yml exec -T models ollama pull qwen3:0.6b

# Tests against the live gateway/private worker:
docker compose -f compose.integrated.yml exec -T evaluator python -m pytest tests/purchase -q -o cache_dir=/tmp/pytest-cache

# Original regression suite in isolated in-memory test stores:
docker compose -f compose.integrated.yml exec -T -e PURCHASE_ENABLED=0 -e INTENTSEAL_DATABASE_URL= -e INTENTSEAL_DB_PATH=:memory: -e INTENTSEAL_STORE_PREVIEWS=1 gateway python -m pytest tests --ignore=tests/purchase -q -o cache_dir=/tmp/pytest-cache
```

Use `scripts/assever_integrated_backup.py` for a quiesced local backup/restore verification. It stops gateway/worker/evaluator/effects, snapshots both databases, restores uniquely named verification databases, checks every public/purchase/effect table fingerprint, and restarts the stack. It does not remove volumes or restored verification databases. Run it outside an active model/campaign study to avoid interrupting its protocol. Database dumps stay local and are excluded from source/evidence publication archives.

`scripts/assever_capture.py` streams container tar output safely and validates extraction paths; it handles tmpfs artifacts on this Docker Desktop installation. Capture into a workspace evidence directory. Standard `docker cp` did not reliably capture tmpfs in this environment. Test credentials, raw browser storage and database dumps are not publication artifacts.

## Remaining qualification

Exact-host latency, multi-instance deployment, real independently settling adapters, cloud IAM/secret/Model Armor/BigQuery qualification and account-owned interoperability tests are separate gates. Keep local results, supported scope and unresolved outcomes explicit. Do not run cloud deployment commands until the user confirms the Google project and deployment work.

## Local database roles

Fresh installations initialize PostgreSQL with the local administrative role `localdbadmin`; application services connect as the non-superuser `intentseal_app`. The effect service has its own non-superuser role and database. Readiness checks TCP so the temporary initialization server cannot prematurely release dependent services. The existing synthetic development volume was upgraded without deleting its records using `scripts/assever_local_db_role_upgrade.py` with application writers stopped. Retired standalone volumes are untouched. Synthetic local credentials in Compose are development defaults.
