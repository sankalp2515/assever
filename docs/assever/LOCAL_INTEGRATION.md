# Assever

**AI agent governance and purchase integrity.**

Hand off the task. Approve it once. Keep the work within your words—from screened reads and sealed handoffs to durable purchase execution and independently verified outcomes.

The original console, gateway, Core engine, SDK, business policies, agent connectors, work orders, approvals and receipts remain the product foundation. Assever adds a purchase annex, shared money/quantity accounting, a private executor, independent effect verification and an isolated commerce safety lab. Compatibility imports and existing client routes remain available.

## Run locally in Docker

```powershell
docker compose -f compose.integrated.yml up --build --wait -d
```

Open **http://localhost:8000**. This is the original console with Tasks, Needs you, Activity, Connect and Evaluation. Start an original office/support task, connect your agent, or choose **New purchase** in Tasks. Review the exact purchase annex before confirming. The default basket is 5 kg rice and 2 L oil, with INR 1,500 including fees; two affordable baskets still exceed one approved demand.

The local stack runs the existing gateway/console, PostgreSQL, a private purchase worker, owned effect adapters and an isolated evaluator. No Google project, paid API key, live payment account or personal data is needed. The original office/support sandbox uses explicitly labeled scripted agents when cloud models are unavailable. Its Google ADK/Vertex integrations remain in place for later configuration.

```powershell
docker compose -f compose.integrated.yml ps
docker compose -f compose.integrated.yml stop
```

Volumes preserve state. Do not use `down -v` for a normal restart. The classifier is baked into the image and loaded before readiness; allow the startup grace period. Fonts are hosted locally. The gateway is the only published application port. Local subnet ranges are 10.203.94.0/24 and 10.203.95.0/24; adjust these if they conflict on another host.

Default credentials are explicitly synthetic localhost credentials. The profile does not load an `env_file` or mount cloud credentials. Cloud deployment is a separate future operation requiring the owner's confirmation; none is performed here.

## Architecture and source boundaries

- `apps/console`: original application and visual language; purchase capabilities extend existing pages.
- `services/gateway/intentseal_gateway`: original gateway/authentication plus purchase routes and a private evaluator entry point.
- `packages/core/intentseal_core/delegate`: original compiler, gate, provenance, handoffs, approvals and receipts.
- `packages/core/intentseal_core/purchase`: typed profile, ledger/outbox, execution/recovery, adapters, checker and evaluation logic.
- `packages/sdk/intentseal`: existing client/ADK guard with purchase submission/status methods; old paths remain compatibility aliases.
- `compose.integrated.yml`: active local stack; root `docker-compose.yml` includes it.

The corrected architecture and requirements mapping are in `docs/assever/integrated-design/README.md`. The original explanation in `docs/ARCHITECTURE.md` and Ledger visual system in `docs/DESIGN.md` describe the retained foundation. The standalone implementation under `services/assever`, its Compose file and old archives remain reference artifacts. They are not the active application; their completion counts do not certify the integration.

## Optional local models

```powershell
docker compose -f compose.integrated.yml --profile models up -d models
docker compose -f compose.integrated.yml exec -T models ollama pull qwen2.5:0.5b
docker compose -f compose.integrated.yml exec -T models ollama pull qwen3:0.6b
```

Qwen models make untrusted proposals using the actual reviewed scope. Seller messages first pass through the original read-screening/provenance path. The ledger checks every consequential proposal. Invocation errors are retained; no scripted response is presented as a live model output.

## Verify

```powershell
docker compose -f compose.integrated.yml exec -T evaluator python -m pytest tests/purchase -q
docker compose -f compose.integrated.yml exec -T evaluator python -m intentseal_core.purchase.campaign --output /tmp/integrated-campaign
python scripts/assever_capture.py assever-integrated-evaluator-1 /tmp/integrated-campaign outputs/assever-integrated-evidence
```

The offline checker uses only the standard library:

```powershell
python packages/core/intentseal_core/purchase/checker.py purchase-evidence.json
```

The full gateway live study runs `/app/scripts/assever_integrated_study.py` in the private evaluator after model setup. Actual invocations, matched Core references, authored conformance cells and original authorization benchmarks have separate denominators. Read current integrated release evidence before citing results. Unknown outcomes remain unresolved; hashes provide tamper evidence rather than signed provider authenticity.

## Attribution

Retain LICENSE, NOTICE, dependency/model/font licenses and `docs/assever/ATTRIBUTION.md`. The earlier foundation README is preserved in `docs/history/FOUNDATION_README.md`. Renaming does not change source ownership, actual development facts or license obligations.
