<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/brand/assever-logo-dark.svg">
  <img alt="Assever" src="docs/brand/assever-logo-light.svg" width="420">
</picture>

### Purchase integrity for AI agents on India's commerce and payment rails

**Approve once. Every purchase stays exactly what you approved.** In budget isn't the same as approved: Assever stops the second basket, the swapped supplier and the extra data share, even when a seller's message talks the agent into it.

[![CI](https://github.com/sankalp2515/assever/actions/workflows/ci.yml/badge.svg)](https://github.com/sankalp2515/assever/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-1F2A6B)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-1F2A6B)](packages/core/pyproject.toml)
[![Live on Google Cloud](https://img.shields.io/badge/live-Google%20Cloud-4285F4?logo=googlecloud&logoColor=white)](https://assever-872171487489.us-central1.run.app)
[![Gemini](https://img.shields.io/badge/Gemini-Vertex%20AI-8E75B2?logo=googlegemini&logoColor=white)](docs/assever/GOOGLE_CLOUD_VALIDATION.md)
[![Model Armor](https://img.shields.io/badge/screening-Model%20Armor-4285F4)](docs/assever/GOOGLE_CLOUD_VALIDATION.md)

[**Try the live attack**](https://assever-872171487489.us-central1.run.app/#/red-team) ·
[Start a purchase](https://assever-872171487489.us-central1.run.app/#/tasks?task=new-purchase) ·
[Evidence](#evidence) ·
[Quick start](#quick-start) ·
[Consent record](#depa-style-consent-record) ·
[Report (PDF)](docs/submission/report/Helios_Report.pdf)

<img src="docs/hero.gif" alt="Live: a Gemini buyer is fooled into proposing two baskets; Assever lets exactly one ₹700 order through" width="760">

<sub>Recorded on the live deployment: a real Vertex Gemini buyer falls for a fake "transit safety" notice and proposes two baskets. Assever admits one ₹700 order, exactly what was approved.</sub>

</div>

---

## Why Assever

AI agents are starting to buy for businesses: restocking a kirana, paying a supplier, booking a delivery. Every payment rail checks one thing: **is this payment authorised, and within limit?**

That is not enough. Two ₹700 baskets fit inside a ₹1,500 cap even when the owner approved one. A seller's message ("oil must ship in two baskets", "supplier B is deprecated", "send the customer list") can redirect the agent without breaking any limit. Parallel workers and child agents can repeat a purchase with fresh request IDs. And a payment that timed out may have succeeded, so retrying it pays twice.

**Assever isn't another agent or another filter.** It sits between agents and business tools and asks a different question. A budget guard asks *"is this payment within limit?"*; Assever asks *"is this exactly the purchase the person approved, and did that, and only that, actually happen?"*

<div align="center">

| Deployed system · same proposals | Unsafe purchases | Tasks completed |
|---|:---:|:---:|
| No guard | 54 / 144 | – |
| Budget-only guard | 36 / 144 | 92 / 144 |
| **Assever** | **0 / 144** | **126 / 144** |

</div>

<sub>720-case authored campaign on the deployed Google Cloud system: 24 attack families × 3 provider profiles × 2 role topologies, 144 cells per control. Assever's 12 unknown provider outcomes are held, never retried and never counted as success. Our own suite, so zero is not proof of safety. [Method and limits →](docs/assever/GOOGLE_CLOUD_VALIDATION.md)</sub>

## How it works

<div align="center"><img src="docs/assever/integrated-design/Assever_Google_Architecture.png" alt="Assever architecture on Google Cloud" width="900"></div>

1. **Say it once.** The owner writes the task in plain words: *"Buy 1 × 5 kg rice and 2 × 1 L oil, up to ₹1,500 including fees, from supplier A or B. Share only the shop name and delivery address."* Assever turns it into an exact work order: items and units, equivalent packs, suppliers, all-in gross cap, number of purchases, delivery point, permitted data fields and expiry.
2. **Approve once.** The owner reviews every field and confirms. Confirmation and activation happen in one PostgreSQL transaction, bound to the order's digest. An agent key can never approve.
3. **Every proposal is tied to one approved demand.** Whichever agent, worker or delegated child proposes a purchase, it maps back to the same root demand. New request IDs cannot create a second basket.
4. **Money and stock are reserved together.** Admission locks the root and reserves integer paise, quantities and purchase count in one step, writing a durable outbox record. Reserved, unknown, captured and closed amounts never overlap.
5. **Only a private executor can act.** It holds the supplier and payment credentials, records intent before sending, and reconciles uncertain outcomes instead of blindly retrying.
6. **Outcomes are proven, not claimed.** A standard-library checker rebuilds what happened from separate order, payment and disclosure records and joins them with the approval. Every step is a hash-chained receipt.

<table>
<tr>
<td width="50%"><img src="docs/snapshots/1-work-order.png" alt="Work order"><br><sub><b>The owner's words become an exact work order</b></sub></td>
<td width="50%"><img src="docs/snapshots/2-red-team.png" alt="Red team"><br><sub><b>Red team: a Gemini attacker vs a Gemini buyer, 120 sessions</b></sub></td>
</tr>
<tr>
<td><img src="docs/snapshots/3-consent.png" alt="Consent record"><br><sub><b>DEPA-style consent record, every effect checked against it</b></sub></td>
<td><img src="docs/snapshots/4-evaluation.png" alt="Evaluation"><br><sub><b>Evaluation dashboard on the live deployment</b></sub></td>
</tr>
</table>

## Quick start

### 1 · Try it live (no sign-up)

- **[Red team](https://assever-872171487489.us-central1.run.app/#/red-team):** press **Generate a new attack** to have the Gemini attacker write a fresh one on the backend (each next round sees what the buyer did), or **Run attack on live Assever** to replay it. The recorded winning attack goes to real Vertex Gemini; when the buyer proposes two baskets, Assever lets exactly one ₹700 order through. Write your own attack in the same box.
- **[New purchase](https://assever-872171487489.us-central1.run.app/#/tasks?task=new-purchase):** a private 7-day trial key is created for you. Review and confirm the work order, run a Gemini proposal, run it again (the second is refused with `DEMAND_ALREADY_ENCUMBERED`), then **Verify actual effects** to see the independent check and the consent record.

### 2 · Run it locally (Docker)

```bash
docker compose -f compose.integrated.yml up --build --wait -d
```

Open <http://localhost:8000>: Tasks, Needs you, Activity, Connect, Evaluation and Red team. The local stack runs the gateway and console, PostgreSQL, the private purchase worker, owned ONDC-style supplier and UPI-style payment simulators, and an isolated evaluator. No Google project, paid key, payment account or personal data is needed; cloud models are replaced by clearly labelled scripted agents.

```bash
docker compose -f compose.integrated.yml ps
docker compose -f compose.integrated.yml stop      # volumes keep state; avoid down -v
```

Optional local models for the historical study: `docker compose -f compose.integrated.yml --profile models up -d models`, then pull `qwen2.5:0.5b` and `qwen3:0.6b` into the `models` service.

### 3 · Verify the evidence offline

```bash
python scripts/verify_assever_google_exports.py                      # every bundle, standard library only
python packages/core/intentseal_core/purchase/checker.py evidence.json
python -m intentseal_core.purchase.consent evidence.json             # consent artefact + check
```

## Bring your own agent

Your agent keeps its scoped agent key and never sees supplier or payment credentials. It proposes; Assever decides; the private executor acts.

| Step | API |
|---|---|
| Describe the task | `POST /v1/delegations` |
| Draft the purchase work order | `POST /v1/delegations/{workflow}/purchase` |
| Owner confirms (human only) | `POST /v1/purchases/contracts/{id}/approve` |
| Agent or model proposes | `POST /v1/purchases/contracts/{id}/model-purchase` or the SDK's proposal, prepare and commit calls |
| Check what actually happened | `GET /v1/purchases/contracts/{id}/evidence` |

The Python SDK in [`packages/sdk`](packages/sdk) wraps these calls and includes a Google ADK guard. Integration guide: [docs/INTEGRATE.md](docs/INTEGRATE.md).

## Evidence

All results are from the deployed Google Cloud system, each cohort reported separately, with every error kept in the denominator.

| Study | Budget-only guard | Assever |
|---|---|---|
| 720-case authored campaign (144 per control) | 36 unsafe, 92 completed | **0 unsafe**, 126 completed, 12 unknown held |
| Adaptive red team: Gemini attacker vs Gemini buyer, 120 sessions, ≤ 4 rounds | 1 unsafe (2 baskets, ₹1,400) | **0 unsafe**, 116 / 120 completed |
| Gemini cohort: 240 attempts, 235 valid, 5 provider errors | 0 unsafe | 0 unsafe, 235 completed |
| Consent check over every red-team round | 1 fail (frequency, units) | **476 / 476 within consent** |

| Engineering | Result |
|---|---|
| Eight-process race, 100 attempts | 1 basket admitted, 99 duplicates refused |
| Effect bundles re-verified offline | 1,195 |
| Core admission p95 (4 vCPU / 8 GB, 20 clients) | 93.9 ms |
| Deployed test suites | 225 foundation · 76 purchase/integration · 8 console |

**Reading the numbers honestly.** In the red team, Gemini 3.5 Flash resisted all 60 of its sessions and Gemini 3.1 Flash-Lite was fooled once. Rare, but one slip is enough to pay twice under a budget-only guard, and Assever's guarantee doesn't depend on the model resisting. The Gemini cohort's proposals were safe under both controls, so it shows Assever doesn't block useful work; it is not claimed as a safety gap. A separate historical local study with small Qwen models found 53 / 239 unsafe under the budget guard and 0 / 239 under Assever. Full method: [cloud validation](docs/assever/GOOGLE_CLOUD_VALIDATION.md) · red-team engine: [`scripts/assever_google_redteam.py`](scripts/assever_google_redteam.py) · summaries: [`docs/assever/evidence`](docs/assever/evidence).

## DEPA-style consent record

Each approval can be exported as a purpose-bound consent artefact modelled on India's DEPA framework: purpose, data principal, the AI agent as data consumer, sellers as providers, items, gross cap, frequency, permitted data fields, validity window and revocation, sealed with a digest bound to the approval. The checker tests every supplier, payment and disclosure record against it. Anything dispatched after revocation or expiry, or beyond the consented amount, count, units or fields, fails. Withdraw consent with **Stop new purchases**; effects already dispatched reconcile and are not retroactively cancelled.

Code: [`consent.py`](packages/core/intentseal_core/purchase/consent.py) (standard library) and its browser twin [`consent.ts`](apps/console/src/consent.ts). Modelled for evaluation; not a ReBIT-certified artefact or a live consent manager.

## Built on Google Cloud

| Service | What it does in Assever |
|---|---|
| **Vertex AI · Gemini 3.5 Flash / 3.1 Flash-Lite** | Buyer proposals, the adaptive red-team attacker, plain-language explanations |
| **Google Gen AI SDK · Google ADK** | Model calls and the live agent journeys with tool-call guards |
| **Model Armor** | Screens seller content and documents agents read |
| **Cloud Run** | HTTPS edge serving the console |
| **Compute Engine · PostgreSQL** | Private runtime: gateway, purchase worker, effect services; PostgreSQL on a dedicated Persistent Disk with daily snapshots |
| **BigQuery** | Audit copy of receipts for analysis |
| **Secret Manager · IAM** | Service credentials, kept out of agents and browsers |

## Security model, plainly

**Assever guarantees**
- A purchase outside the confirmed work order is not admitted.
- One approved demand can be fulfilled at most as approved, across agents, workers and retries.
- An agent key can't confirm, widen or approve.
- Unknown outcomes are held, never relabelled as success or blindly retried.
- The receipt chain shows any edit.

**Not claimed**
- No live ONDC, UPI, bank, Aadhaar or DigiLocker connection; suppliers and payments are owned simulators with synthetic data.
- Receipts are hash-chained, not provider-signed. Model versions are provider-reported, not weight checksums.
- The evaluation and red team are our own; the global Vertex endpoint does not prove India-only data residency.
- No AP2 interoperability, P3P UAT or payment-network certification.

Report a vulnerability: [SECURITY.md](SECURITY.md).

## Repository

| Path | Contents |
|---|---|
| [`packages/core/intentseal_core/purchase/`](packages/core/intentseal_core/purchase) | Purchase profile, ledger and outbox, executor and recovery, adapters, checker, consent artefact, evaluation |
| [`packages/core/intentseal_core/delegate/`](packages/core/intentseal_core/delegate) | Work-order compiler, action gate, provenance, handoffs, approvals, receipts |
| [`services/gateway/`](services/gateway) | FastAPI gateway: authentication, purchase routes, private evaluator entry point |
| [`apps/console/`](apps/console) | React console: Tasks, Needs you, Activity, Connect, Evaluation, Red team |
| [`packages/sdk/`](packages/sdk) | Python client and Google ADK guard |
| [`scripts/`](scripts) | Red-team engine, studies, evidence capture and offline verification |
| [`deploy/google/`](deploy/google) | Google Cloud deployment (Cloud Run edge, Compute Engine runtime) |
| [`docs/`](docs) | Architecture, validation, evidence summaries, submission report |

Internal Python packages use the `intentseal_*` namespace for import compatibility; they are all part of Assever.

<details>
<summary><b>Development</b></summary>

```bash
docker compose -f compose.integrated.yml exec -T evaluator python -m pytest tests/purchase -q
docker compose -f compose.integrated.yml exec -T evaluator python -m intentseal_core.purchase.campaign --output /tmp/campaign
cd apps/console && npm ci && npx tsc --noEmit && npm test && npm run build
```
</details>

## Team and attribution

Built by **Team Helios** (Sankalp Kailash Wanjari, independent) for the SAFL India Agentic AI Security Hackathon, System Resilience track. Licensed under [Apache-2.0](LICENSE); third-party licences and models are listed in [`docs/assever/ATTRIBUTION.md`](docs/assever/ATTRIBUTION.md) and [NOTICE](NOTICE).
