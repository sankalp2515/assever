# Assever on Google Cloud

Deployment authorized by the project owner on 31 October 2026. Project: `assever` (872171487489). Public application: **https://assever-872171487489.us-central1.run.app**. The application comprises a console, gateway, Core engine, SDK, policies and workflows.

## Deployed boundaries

| Resource | Configuration / responsibility |
|---|---|
| Cloud Run `assever` | Public HTTPS transport, private VPC upstream, streaming enabled, maximum two edge instances. No application authority or provider credentials. |
| Compute Engine `assever-runtime` | `us-central1-a`, `e2-custom-4-8192`, four vCPUs / 8 GB. Native Docker gateway, worker, evaluator, synthetic effect adapter and PostgreSQL remain separate containers. |
| Private network | `assever`, subnet `assever-runtime`, `10.61.0.0/24`. Gateway binds `10.61.0.10:8000`. Firewall permits that port only from this subnet. SSH is restricted to IAP's source range. |
| Persistent Disk `assever-data` | 30 GB, mounted at `/srv/assever`. PostgreSQL and gateway state survive application image replacement. Daily snapshots retain seven days. |
| Vertex AI | Gemini `gemini-3.5-flash` and `gemini-3.1-flash-lite`, global endpoint, explicit model selection. Purchase planning uses Google Gen AI SDK; existing office/support agent teams use Google ADK. |
| Model Armor | `projects/assever/locations/us-central1/templates/assever`; screens untrusted content in addition to the original engine. |
| BigQuery | `assever.assever_audit.receipts`, partitioned by receipt creation time. Best-effort analytics is separate from the authoritative PostgreSQL receipt chain and effect evidence. |
| Secret Manager | `assever-runtime-config`; random deployment credentials, fetched using the VM identity. No developer `.env`, user ADC file or service-account private key is uploaded. |

The serving application image is pinned by digest in `deploy/google/configure_runtime.py` and the deployment evidence. Runtime account: `assever-runtime@assever.iam.gserviceaccount.com`; HTTPS edge account: `assever-edge@assever.iam.gserviceaccount.com`. Vertex, screening, logging and audit access are assigned to the runtime. Registry read and secret access use resource-level grants; BigQuery data access is scoped to its dataset.

The public edge disables the Cloud Run invoker IAM check so judges can reach the product. The original gateway still checks API-key identity, roles, ownership, approval and scoped agent grants. Write operations require a project identity. Public read-only UI configuration is not an administrative credential. Trial keys are individually scoped. The worker and test evaluator retain separate dispatch responsibilities and are not public endpoints.

This is a persistent, single-runtime deployment for evaluation. It does not establish multi-node availability, regional failover, real UPI settlement, ONDC certification or P3P UAT. All commerce records, suppliers, addresses and money are synthetic. Model execution uses actual Google APIs; there is no Ollama service or inference fallback in this cloud profile. Model requests use the global Vertex location; this is not an India-only data-residency qualification.

## Validation

The final source-bound Gemini cohort and exact measured counts are recorded in `GOOGLE_CLOUD_VALIDATION.md` and `outputs/assever-google-evidence`. Local Qwen results and earlier cloud trials remain separate. Models propose actions; the approved scope, company policy and deterministic accounting gate retain authority.

Financial summaries render typed provider-qualified purchase receipts with exact gross amounts and citations. Ordinary office/support reports retain the existing checked Gemini writer. The task list tolerates an in-progress model draft and filters by owner before applying its result limit.

Cloud Run reserves `/healthz`; use `/v1/health` for application liveness and `/readyz` for dependency readiness. The private gateway retains the original `/healthz` route. Readiness includes PostgreSQL, policy, the original classifier and private purchase dependencies. Model Armor/API failures and model errors are retained rather than converted into successful runs.

## Operate without exposing secrets

All CLI commands explicitly select `assever`; they do not change the workstation's active project.

```powershell
gcloud run services describe assever --project=assever --region=us-central1
gcloud compute instances describe assever-runtime --project=assever --zone=us-central1-a
gcloud compute ssh assever-runtime --project=assever --zone=us-central1-a --tunnel-through-iap --command="sudo docker compose -f /opt/assever/compose.cloud.json ps"
gcloud compute ssh assever-runtime --project=assever --zone=us-central1-a --tunnel-through-iap --command="sudo python3 /opt/assever/cloud_ops.py progress"
```

Do not print or publish `/opt/assever/compose.cloud.json`: it contains resolved runtime credentials. Do not publish `/srv/assever/backups`. Source and evidence archives exclude them, all `.env` files, downloaded model weights and browser storage.

`deploy/google/qualify_runtime.py` runs the original suite against isolated test schemas, the full product suite through the public HTTPS endpoint, and the twenty-client admission measurement. `scripts/assever_google_study.py` runs inside the private evaluator, captures real Gemini responses, and compares each proposal with the isolated authored payment-budget reference. Start a study only against its frozen source; do not replace the image while it runs. Raw prompts, responses, versions, usage, errors and effect evidence are retained. Provider-reported model-version digests are not weight checksums.

The completed release cohort uses the archived v5 study runner in its evidence package. The current v6 runner checks that an actual plan exists before reference replay, preserving a provider failure without a secondary null-plan error. It writes to a new default directory so its results cannot silently mix with the completed cohort.

Use `deploy/google/verify_backup.py` on the owned VM after stopping active studies. It quiesces application writers, dumps both databases, restores distinct verification databases, compares every public/purchase/effect table fingerprint, and restarts the stack. Verification databases and private dumps are retained for recovery review. The evidence exporter includes the comparison proof, never the dumps.

## Reproduce and update

`scripts/provision_assever_google.py` provisions the named network, identities, disk and initial VM idempotently. `deploy/google/startup.sh` installs Docker and a checksum-verified Compose binary, mounts only the named data disk, and creates private runtime directories. `deploy/google/configure_runtime.py` transforms the existing integrated Compose profile, removes local model containers, resolves Secret Manager credentials and configures the Google integrations. The original local Docker deployment and its volumes remain available independently.

For an update, build and push a new immutable image, update its digest in the deployment configuration, preserve current evidence, and replace the owned stack with readiness checks. Application replacement briefly interrupts the single gateway; browser retries/reconnect restore durable work-order state. Completed ADK sandbox transcripts are exported as evidence; live in-memory agent sessions do not survive a gateway restart. Pending purchase obligations remain in PostgreSQL and reconcile through the private worker.

The Compute Engine runtime stays running to serve the application and worker. Stopping it pauses processing and makes the public application unavailable; the dedicated data disk and its snapshots persist. Cloud resources are intentionally retained after testing for the owner's review and submission.
