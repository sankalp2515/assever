# Assever product requirements · integrated edition

Version 1.1 · 31 October 2026 · Local Docker release

Deployment amendment 1.2 · 31 October 2026: the owner authorized project `assever`, Google Cloud deployment and live Gemini qualification. The whole-product requirements remain in force. The deployed profile uses the existing native Docker services on a private 4-vCPU/8-GB Compute Engine runtime, a Cloud Run HTTPS edge, Vertex Gemini through Google Gen AI SDK / Google ADK, Model Armor, Secret Manager and BigQuery. See `GOOGLE_CLOUD_OPERATIONS.md` and `GOOGLE_CLOUD_VALIDATION.md` for the as-built deployment and measured acceptance. This amendment supersedes the earlier deployment exclusion; video, account-owned UAT and mandatory owner facts/permissions remain separately tracked.

This document defines the whole-product boundary. Assever is an AI-agent governance and purchase-integrity platform. `prd_outputs/Assever/Assever_PRD.md` remains the detailed purchase-profile specification and historical planning baseline. The architecture allocation and FR-01–FR-26 traceability in `integrated-design/README.md` apply alongside this document. Measured results and open gates belong in the integrated release status, not in prospective requirement statements.

## Product and users

Assever is the security checkpoint between an organization's AI agents and its business tools. A person delegates work, reviews an explicit work order once, and follows the resulting decisions, exceptions and receipts. Documents and agents can propose information or plans; only the authenticated human can approve authority. Deterministic checks govern consequential actions.

The primary users remain the employee/operator, the security reviewer and the agent/business integrator. Procurement adds a concrete India commerce workflow to the same product. It does not replace office work, customer support, tool screening, business registration, review, investigation, replay or agent connectivity.

## Retained product capabilities

1. **Grounded work orders:** plain-language intake, quoted and validated MAY/NEVER clauses, trusted contact/resource resolution, version/hash-bound human confirmation and safe handling of pasted material. A model draft grants no authority by itself.
2. **Content screening:** extraction of documents/hidden text, rule and local-classifier screening, optional Model Armor, confidential-content controls, source provenance and taint tracing. A model judge can add evidence; it does not override the human approval boundary.
3. **Delegation:** HMAC-bound handoffs preserve workflow identity and untrusted provenance. In-process and remote ADK callbacks and the existing REST/SDK path remain available.
4. **Action enforcement:** registered-tool schemas, recipients, records/resources, undeclared consequential fields, instruction order, amount checks and source-linked refusal. A document-originated scope expansion is stopped without prompting the human on the attacker's behalf.
5. **Human exceptions:** owner-only, exact-action, single-use, expiring approvals; existing Needs you and reviewer workflows.
6. **Accountability:** ordered hash-chained receipts, source-linked explanations, cited reports, original Activity/investigation/replay/review and optional BigQuery analytics.
7. **Integration:** business-policy registration, private work orders, employee/agent key separation, key issuance/revocation, proxy/content APIs and self-contained remote client. Compatibility imports and old routes remain unless explicitly migrated.

## Added purchase capability

The trusted `kirana` business profile participates through the existing workspace-policy registry. It declares `purchase_profile: kirana-v1`, permitted tool actions, trusted contacts/resources and a company ceiling. Custom registered businesses can explicitly opt into the supported profile. An office workspace cannot silently acquire purchase authority. Changing a registered business policy invalidates its frozen purchase policy binding for future admissions; pending work stays visible for recovery.

The initial finite synthetic profile covers 5 kg rice and 2 L oil, two trusted suppliers, enumerated equivalent packs, INR integer-paise gross accounting, a fixed synthetic delivery destination and a minimum disclosure profile. The structured annex is displayed beside the person's words. Every hard field requires review; it is not inferred from arbitrary prose or seller messages. Missing/incorrect defaults can be edited using the supported strict scope API before confirmation. The interface exposes budget editing; all executable fields remain visible for explicit review.

Each purchase attaches to an original delegation and frozen contract/policy versions. A single PostgreSQL transaction confirms the original work order and activates the exact annex. A failed or replayed confirmation cannot leave one part executable while the other remains unconfirmed. Unverified governed prose clauses are not silently promoted to confirmed permissions. The annex is the purchase authority.

The root ledger assigns demand-line identities and shares budget, quantities and purchase count across all agents and attenuated grants. Separate request/order/agent IDs do not reset capacity. Preparation binds immutable projected consequences but neither reserves capacity nor executes tools. Admission rereads current scope, epoch, policy, quote and grant; checks the shared root; reserves disjoint exposure; appends the admission record; and writes the durable outbox in one transaction.

The private worker claims outbox operations, durably records dispatch intent, sends exact stored bytes with stable provider operation identity and fences, and reconciles uncertain outcomes. A possibly sent operation is not blindly resent. UNKNOWN exposure is retained; a negative lookup is not automatically terminal proof of no effect. Refund notices do not recreate gross demand or spending entitlement. Revocation blocks future admissions rather than claiming to undo an external request already admitted.

The existing gate refuses direct governed mutations on an annex-linked workflow. The existing SDK adds purchase prepare/commit/status behavior. Its ADK `assever_purchase` interception returns a pending operation handle and prevents the original raw mutating function from executing a second time. Human and agent credentials remain those of the original gateway. Purchase role registration stores no second login token.

## One console experience

- **Tasks:** retain original sandbox and external-agent tasks; add New purchase and purchase task detail. Show the approved work order, pending exposure, actual effects, exact quote, operations, event records and evidence export. Pending/Unknown is distinct from Ran.
- **Needs you:** retain existing action approvals/reviewer queue; list pending purchase changes and link to the exact old/new scope review in their task.
- **Activity:** retain original decisions, filters, investigation, replay and insights; link purchase work orders and their original receipts to observed effects.
- **Connect:** retain keys, agent/business setup and advanced controls; add SDK purchase integration instructions and adapter capabilities.
- **Evaluation:** retain original authorization benchmark and recorded Gemini results; add isolated, per-workspace purchase comparisons with matched authored controls and raw effects.

Preserve the original Ledger design tokens, stamp mark, typography, paper/night themes, focus states and responsive navigation. Host fonts locally with licenses. English/Hindi structured labels share canonical values; this is not a claim of broad Hindi natural-language security coverage. Keep implementation details in the API/Connect/inspection surfaces rather than replacing the user's task with infrastructure controls.

## Trust and isolation

The original gateway is the only published application. PostgreSQL remains one service, using its original public delegation tables and a separate purchase schema. The effect service uses a distinct database and role. Gateway, worker and evaluator have separate process responsibilities. Only worker/evaluator test identities receive dispatch credentials; no agent or browser receives them. The evaluator is private, separately authenticated, and cannot expose permissive research roots through normal purchase APIs.

The human approval, registered business policy, issuer/service keys, database transactions, gateway/Core, executor and participating adapter are trusted. Models, seller prose, memory, callbacks, client IDs and concurrently acting agents are untrusted. Trusted-operator/key compromise, physical delivery, general item equivalence, live UPI settlement and network-wide ONDC certification are outside the finite executable profile.

Owned adapters model queryable, deduplicating and opaque outcomes. The current synthetic adapter commits order/payment/egress in one private transaction. Independent real merchant and payment settlement requires a qualified adapter and additional joint-state recovery; the simulator does not establish that capability. The limited offline AP2 projection is not full AP2 interoperability. P3P account/UAT work is owner-dependent and excluded from this local scope.

## Evidence and acceptance

Keep three evidence categories distinct: original authorization regressions/benchmarks, shared-Core purchase conformance, and actual gateway/model/worker integration. The standard-library verifier reconstructs money, units and disclosures from independent source records, validates work-order/annex/policy bindings, and checks original receipt links. A recomputable hash chain is tamper evidence, not a provider signature.

Release acceptance requires original workflows and routes to remain functional, additive migrations, cross-owner isolation, exact atomic confirmation, company-policy enforcement, mediated SDK/tool execution, parallel admission, process-exit/recovery, retained uncertainty, original receipt/report integration, isolated evaluation, mobile/keyboard/night/reconnect checks, clean installation and backup/restore. Raw failed exploratory runs remain separate and visible. Freeze source, scenario/model settings and denominators before scoring; retain model errors without fallback or replacement.

Measure core admission, provider readiness and HTTP transport separately. The earlier target is core-admission p95 <=100 ms at twenty clients on a declared 4-CPU/8-GB host. A measurement on this larger Docker host does not qualify that target. Report the observed timing and open gate without weakening accounting or omitting receipt/effect checks to improve the number.

## Delivery scope

Local Docker implementation, tests, operational documentation, architecture, SDK, corpus, portable evidence, reconciled backlog and prepared submission material are included. Deployment is complete. Video, form submission and mandatory owner identity/consent steps remain separately tracked. Preserve accurate work dates, attribution, external licenses and AI-assistance disclosures. The Google Cloud deployment and live Gemini qualification are recorded in GOOGLE_CLOUD_VALIDATION.md.
