# Assever — submission and frontend handoff

## Current deployment

- Live: https://assever-872171487489.us-central1.run.app/
- GitHub: https://github.com/sankalp2515/assever
- Frontend revision: `assever-00003-jlz`, deployed 31 October 2026 (frontend fixes from the live review; see `SUBMISSION_CHECKLIST.md`). Previous: `assever-00002-d8b`.
- Frontend image: `us-central1-docker.pkg.dev/assever/assever/frontend@sha256:995f99dbec6b3f5324d2b9c3634def69458281959d906cbc7daa1cdbf5cd92df`.
- Backend image remains `sha256:7cfb83d1deba3a0b703038c1886bf62b842d9697fbc0d19c3512d85ec7dc574c`. APIs, database, environment, IAM and secrets were not changed for this frontend release.

Claude's frontend edits were retained. The static build is served by the existing HTTPS edge; non-frontend requests continue to the same private gateway. The release ran dependency installation, TypeScript compilation and production builds. No regression suites or transaction tests were rerun for this frontend-only release; Claude should perform the verification below.

## DPI selection — ready to paste

**ONDC-style commerce and UPI-style payments in a team-owned synthetic DPI environment, with cross-cutting AI-agent governance.**

Select ONDC and UPI with the synthetic-environment qualification; select cross-cutting if the form allows it. Aadhaar and DigiLocker are not implemented integrations.

| Demonstration | Code | Deployed UI |
|---|---|---|
| Commerce catalog, suppliers, quotes and order effects | `policies/delegate/kirana.yaml`; `packages/core/intentseal_core/purchase/service.py`; `sink.py` | Tasks → New purchase → reviewed items, suppliers, quantities and delivery |
| Commerce message correlation and lifecycle | `packages/core/intentseal_core/purchase/schemas.py` (`Callback`); `runtime.py` | Purchase operations and independent evidence records |
| INR payment limits, reservations, dispatch and recovery | `runtime.py`; `worker.py`; `sink.py` (`payment`, refunds and status) | Pending obligations, gross captured amount and observed outcomes |
| Cross-cutting consent, identity, scoped delegation and audit | `packages/core/intentseal_core/delegate`; `packages/sdk/intentseal/delegate.py`; `purchase/checker.py` | Work-order approval, Needs you, Activity, Connect, Evaluation and evidence downloads |

These are owned simulators inspired by the commerce/payment workflow. Do not claim live ONDC participation, real UPI settlement, P3P UAT, Aadhaar or DigiLocker connectivity. AP2 support is a limited offline projection, not full interoperability certification.

## Existing measured evidence

See `docs/assever/GOOGLE_CLOUD_VALIDATION.md` and `submission/Assever_Evidence_v1.2.4.zip`.

- 225 foundation tests and 76 purchase/integration tests passed; one optional LangChain test was skipped. Eight console tests passed.
- Four real Google ADK journeys completed office/support work, including compromised-agent cases with the content filter disabled.
- The deployed authored campaign has 720 cells. Adaptive enforcement records zero unsafe effects, 12 unresolved outcomes and 126/144 completed tasks.
- The frozen Gemini cohort has 240 requests, 235 valid responses/completed tasks and five retained capacity errors. Both controls were safe on the 235 matched proposals. Do not present the earlier local Qwen comparison as this Gemini result.
- All 1,195 final effect bundles independently verify. Core admission p95 is 93.856 ms on four vCPUs/8 GB. Backup/restore verifies 45 tables.

Extract the evidence ZIP at repository root and run `python scripts/verify_assever_google_exports.py` using the standard library. Keep the archived executed v5 runner and original failures intact; the current v6 runner fixes null-plan reference handling for future cohorts.

## Claude verification request

1. Hard-refresh the live URL. Confirm the indigo hero, saffron seal/buttons, section order, responsive layout, dark mode and keyboard navigation.
2. Scroll the numbers band into view and allow its count-up animation to finish. Values must come from `/v1/delegate-eval`; do not invent fallback numbers. Clearly distinguish recorded evaluations from the deployed Gemini cohort.
3. Check landing navigation and CTAs: Watch it stop a hijacked agent; Run your own task; Replay a purchase; Connect your agent. Check the actual destination of the purchase CTA against the intended workflow.
4. Verify Tasks, Needs you, Activity, Connect and Evaluation render with the new palette. Exercise one approved Gemini purchase, its provider-qualified outcome, evidence download and cited receipt. Check ownership/approval behavior remains intact.
5. Fix frontend defects without changing backend code, APIs, database, environment, IAM or secrets. Report any backend issue separately. Reuse the existing backend evidence; repeat large cohorts only when a relevant change or failure justifies it.
6. Study the official event, concept note and supplied submission template. Map each submission field and judging criterion to the actual implementation and evidence. Use the System Resilience track, with supporting Trust & Consent and Accountability. Do not claim every suggestive track.

Review deployment copy against the operations document. In particular, the current authority store is PostgreSQL on a dedicated Persistent Disk; the landing stack's Cloud SQL label needs copy review. Keep historical Qwen figures explicitly distinct from Gemini results.

## Deployed screenshots

![Deployed hero](screenshots/hero.png)

![Deployed console](screenshots/console.png)

## Submission preparation

Official event: https://secureaifutureslab.com/events/india-ai-agentic-hackathon

Concept note: https://docs.google.com/document/d/1eADtd3C0S72eCNLZ0RlGl3b43bPrS59iSQvjlf3o9t4/edit

Owner-supplied template: `C:/Users/sanka/Downloads/SAFL_Submission_Template.docx`.

The prepared report and backlog are locally available under `outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Google_Release/`. Review the report against the template: sections 1–10, report within ten pages, required word limits, accurate model/AI-assistance disclosures, live/source links, limitations, responsible testing, team facts and individual permissions. Product branding is **Assever**; use a current-product description rather than a migration narrative. Keep licenses, attribution and factual development declarations accurate. Internal compatibility identifiers are not alternative product names.

The technical rubric is Technical Depth 40%, Novelty & Creativity 20%, Presentation & Communication 20%, Mission Fit 10%, Implementation Feasibility 10%. Cite prior work; present the executable purchase-integrity profile and measured composition as the contribution.

Owner input remains necessary for registered team/contact details, participation/development declarations, individual consents and final submission authority. The demo video, final report personalization and form submission remain separately tracked. Do not infer permissions or fabricate facts. No live production DPI system should be tested.
