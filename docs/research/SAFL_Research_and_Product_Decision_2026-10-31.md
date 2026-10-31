# Assever purchase integrity research and product decision

Research cut off: 31 October 2026, Asia/Kolkata. This is a design decision and proposed evaluation, not a report of implemented results.

## Decision

Build **Assever — Purchase Integrity for AI Agents**. Preserve the existing authorization foundation and add a trusted purchase contract, shared purchase-entitlement ledger, execution and recovery controller, and a reproducible commerce safety lab. The product protects an approved deal while agents dynamically change their plans.

The primary challenge area is System Resilience. Trust and Consent and Accountability are supporting outcomes of the same implementation. The first adopter is a commerce application or buyer-side integrator adding autonomous procurement. A second adopter is an evaluator testing integrations against a published safety profile.

The thesis is that token validity, authorized spending, a correct basket, and a successful user task are separate facts. An agent can spend within its limit and still buy an unwanted duplicate, substitute the wrong pack size, disclose unnecessary customer data, or report a purchase that never completed. A useful system preserves the approved purchase across planning, delegation, merchant callbacks, payment dispatch, and recovery.

Retain the purchase profile’s private adapter, canonical checkout binding, integer-money ledger, and provider-derived outcomes. Move the center of the submission from payment authorization to purchase integrity and measurable safe adaptation.

## Research findings that changed the design

### Payment mandates are established infrastructure

Google AP2 specifies linked checkout/payment mandates and deterministic verification at the relevant roles [S1]. Pine Labs announced P3P on 11 June 2026 [S2]. Its current documentation describes resource-bound payment tokens, receipt exchange, and UPI ReservePay support [S3]. Its quickstart exposes a sandbox integration path [S4]. These are integration targets and reference designs, rather than features to claim as inventions.

Grantex's current wallet-governance documentation already describes shared budget groups, database-locked reservations, exact approvals, stop controls, and retained reservations for certain external effects [S5]. Most relevant to our design, it distinguishes integrity-bound purpose labels from independent evidence that the caller selected the correct purpose. Assever should derive purchase identity and purpose from a trusted user-approved workflow, rather than trusting a model-supplied label. That is an explicit complement to the authorization layer, not an allegation against it.

### Recent research covers the original runtime proposal closely

The February 2026 zero-trust runtime verification paper studies context binding and consume-once execution [S6]. Bounded Agents, dated 16 August 2026, formalizes delegated authority restrictions and stateful action composition [S7]. The 22 October Permission to Retry preprint separates current authority, external effects, reconciliation, and retained uncertainty [S8]. The 11 October revocation outcome-contract paper distinguishes notification progress from effect prevention [S9]. Matoi, dated 15 October, separates reusable consequence evidence, current authority, and durable occurrence history [S10].

Accordingly, context binding, revocation, replay protection, and conservative recovery are foundations to implement and cite. The proposed research contribution is a concrete commerce-domain conformance profile and measured composition, including trusted demand identity, quantity consumption, dynamic substitutions, information disclosure, and independently observed payment effects. A broad first-in-field algorithm claim is unnecessary.

### Dynamic task completion must be measured

AgentDyn evaluates defenses on open-ended tasks with useful third-party instructions and finds important security/utility tensions [S11]. ComboShoppingBench distinguishes a semantically suitable basket from one that satisfies deterministic transactional constraints [S12]. Agentic Commerce Bench examines financial loss even when counterparty identity is correct [S13]. These works support evaluating the actual deal and legitimate completion, alongside the attack result.

Our proposed task oracle accepts any basket satisfying the user's explicit constraints. It must not require one preselected SKU sequence. In the initial closed catalog, hard constraints are deterministic; an LLM judges neither authorization nor financial safety.

## Dated developments and incident evidence

| Date | Source and evidence type | Design implication |
| --- | --- | --- |
| 24 June 2025 | CaMeL v2, research paper: system-level separation of trusted instructions and untrusted data [S14] | Keep authority outside model behavior; provenance is supporting evidence, not permission |
| 9 October 2025 | Unit 42 memory-poisoning research demonstration [S15] | Stored memories and agent summaries remain untrusted on later runs |
| 3 March 2026 | Unit 42 telemetry report on web-based indirect prompt injections observed in the wild [S16] | Exercise merchant pages, callbacks and tool data as attack entry points; payload observation alone does not establish successful loss |
| 11 June 2026 | Pine Labs P3P launch announcement [S2] | Agentic UPI-style purchasing is a concrete integration context |
| 6 July 2026 | Noma GitLost research demonstration with a deliberately configured workflow [S17] | Public content must not borrow the agent's broader credentials or disclosure authority; do not describe it as a confirmed widespread breach |
| 1 September 2026 | Reuters report citing sources about planned UPI agentic payment infrastructure [S18] | Strong contextual relevance; retain its reported/planned status rather than treating it as an official release |
| 24 September 2026 | Pine Labs/Google Cloud collaboration announcement [S19] | A merchant-integrator adoption story matches active industry investment |
| 11–22 October 2026 | Revocation, consequence evidence and retry/recovery preprints [S8–S10] | Position the contribution around the domain profile and integrated experiment, rather than the existence of an execution ledger |

Search discovery also surfaced dramatic incident summaries whose dates and claims were weaker than their primary sources. Those summaries are excluded from the product's evidence. A search result describing NPCI circular 227A as agentic-payment guidance was not adopted: the official search listing identified MyUPI support. No regulatory interpretation rests on that result.

## Alternatives considered

These are qualitative product judgments, not predicted judge scores.

| Direction | Strength | Decision |
| --- | --- | --- |
| Generic prompt-injection filter | Direct attack story; existing filtering code | Supporting defense; established area with less distinctive outcome evidence |
| the purchase profile payment gateway | Concrete financial effects and concurrency tests | Retain its essential mechanics inside the broader purchase contract |
| Delegation-only authorization system | Close to existing provenance and identity foundation | Use constrained child grants; published delegation research supplies the foundation |
| Revocation/recovery-only system | Timely October literature and strong distributed-systems content | Include as required behavior; recent work directly covers the framing |
| Broad multi-DPI governance platform | Wide mission narrative | Focus on commerce plus payments so the result stays inspectable |
| Purchase integrity runtime plus conformance lab | Connects user intent, dynamic utility, authority, quantities and actual effects | Selected product and research artifact |

## Differentiation and prior-work boundary

The defendable submission claim is:

> We implemented and evaluated an executable purchase-integrity profile connecting a human-approved basket contract to constrained agent actions, asynchronous commerce messages, and independently observed payment effects under compromise and recovery.

The original artifact is the explicit domain mapping, its implementation, the adversarial/benign corpus, and comparative results. Its individual cryptographic, transactional and authorization techniques have established antecedents.

Specific experiments ask whether a payment-scoped integration preserves item quantities and purchase identity across new order IDs; whether all layers agree on merchant, basket and final amount; whether recovery preserves both money and purchase entitlements; and whether safe replanning retains useful task completion. The comparison must include competent payment controls and identify mechanisms faithfully.

## Hackathon alignment

The official rubric assigns Technical Depth 40%, Novelty and Creativity 20%, Presentation and Communication 20%, Mission Fit 10%, and Implementation Feasibility 10% [S20]. The selected direction makes each assessable:

- Technical depth: a real trusted contract, PostgreSQL admission, separate effect services, crash/retry tests and a reconstruction checker.
- Novelty: the scoped commerce profile, compound scenarios and source-linked measured contribution.
- Communication: the approved deal beside actual order/payment evidence, followed by a safe completed purchase.
- Mission fit: owned ONDC-inspired commerce and UPI-style payment simulators, with explicit protocol mappings.
- Feasibility: a buyer-side integration package, sandbox adapter contract and conformance runner.

The supplied SAFL template limits the report to ten pages and the recommended video to two minutes. It accepts team-built test environments. The design is a mock environment first; protocol conformity and external sandbox results receive separate labels.

## Research questions and intended evidence

1. **Purchase preservation:** Do per-payment controls admit duplicate or substituted purchases that satisfy spending limits but violate a trusted basket contract?
2. **Safe adaptation:** Can agents finish after benign stock, fee or availability changes using preapproved alternatives?
3. **Recovery:** Are monetary and quantity reservations conserved across response loss, worker crashes, revocation and retries?
4. **Evidence:** Can an independent checker reconstruct the same verdict from human authorization, commerce records and provider effects, and detect corrupted exports?
5. **Composition:** Which additional failures arise when two mechanisms interact, such as an unknown payment followed by a supplier switch?

The target corpus and release gates are specified in the companion blueprint. All numerical targets are prospective until measured. Frameworks and vendor protocols are represented by actual integrations or explicitly named reference controls, never by attributed straw-man implementations.

## Sources

Sources were retrieved on 31 October 2026. The literature comparison used relevant threat-model, design, evaluation and limitation sections. Papers are identified by the version inspected; preprint claims remain attributed to their authors. Vendor announcements/documentation describe vendor capabilities, not independently audited deployments.

- **S1** Google AP2 specification v0.2: https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/specification.md
- **S2** Pine Labs P3P launch, 11 June 2026: https://www.pinelabs.com/media-analyst/the-ai-agent-can-now-pay-pine-labs-launches-p3p-indias-first-agentic-payment-protocol-built-on-upi
- **S3** P3P overview: https://www.pinelabs.com/docs/online-payments/ai/p3p
- **S4** P3P quickstart and sandbox path: https://www.pinelabs.com/docs/online-payments/ai/p3p/quickstart
- **S5** Grantex wallet governance: https://docs.grantex.dev/guides/agent-wallet-governance
- **S6** Zero-Trust Runtime Verification for Agentic Payment Protocols, v1, 6 February 2026: https://arxiv.org/html/2602.06345v1
- **S7** Bounded Agents, v1, 16 August 2026: https://arxiv.org/html/2608.15888v1
- **S8** Permission to Retry, v1, 22 October 2026: https://arxiv.org/html/2610.31916v1
- **S9** Revocation Is Not Complete at Receipt, v1, 11 October 2026: https://arxiv.org/html/2610.15991v1
- **S10** Matoi, v1, 15 October 2026: https://arxiv.org/html/2610.21394
- **S11** AgentDyn, v3, 7 May 2026: https://arxiv.org/html/2602.03117v3
- **S12** ComboShoppingBench, v1, 10 August 2026: https://arxiv.org/html/2608.09282v1
- **S13** Agentic Commerce Bench, v1, 27 September 2026: https://arxiv.org/html/2609.35886v1
- **S14** CaMeL, v2, 24 June 2025: https://arxiv.org/html/2503.18813v2
- **S15** Unit 42 memory-poisoning research, 9 October 2025: https://unit42.paloaltonetworks.com/indirect-prompt-injection-poisons-ai-longterm-memory/
- **S16** Unit 42 web IDPI telemetry, 3 March 2026: https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/
- **S17** Noma GitLost, 6 July 2026: https://noma.security/noma-labs/gitlost-how-we-tricked-githubs-ai-agent-into-leaking-private-repos
- **S18** Reuters planned UPI framework report, 1 September 2026: https://www.reuters.com/world/india/india-preparing-rollout-agentic-payments-upi-sources-say-2026-09-01/
- **S19** Pine Labs/Google Cloud collaboration, 24 September 2026: https://www.pinelabs.com/media-analyst/pine-labs-and-google-cloud-collaborate-to-advance-agentic-commerce-in-india
- **S20** SAFL event and rubric: https://secureaifutureslab.com/events/india-ai-agentic-hackathon
- **S21** SAFL concept note: https://docs.google.com/document/d/1eADtd3C0S72eCNLZ0RlGl3b43bPrS59iSQvjlf3o9t4/edit?tab=t.0
- **S22** ONDC technical resources: https://www.ondc.org/pages/resources-tech.html
- **S23** ONDC log-validation source: https://github.com/ONDC-Official/log-validation-utility . Its inspected README/history indicates the hosted utility was discontinued; use versioned source as reference rather than promising an active hosted service.

## Existing foundation evidence

The preceding local review ran 102 delegation-related tests against this workspace's modules. It also exercised two isolated in-memory probes: allowed-but-failed execution retained logical spend, and forced concurrent spending snapshots allowed two 900-unit checks under a 1,500-unit limit. These are authorization probes, not live payment exploits. They motivate a dedicated effect ledger and do not substitute for the proposed commerce evaluation.

The copied virtual environment contains editable references to a different checkout. Any future validation must explicitly resolve modules from this workspace or recreate the environment. The prior 102-test run explicitly resolved the local modules.
