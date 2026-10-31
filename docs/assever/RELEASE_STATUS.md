# Assever release status

Local product: http://localhost:8088 . No deployment, demo video, public publication or form submission has been performed.

Backlog status: {'Done': 107, 'Excluded': 11, 'Partial': 3}. Original planning estimates are retained; they are not elapsed implementation hours.

## Verification

Product tests: 62 pass. Foundation regressions: 102 pass. Conformance: 720 cells with no adaptive unsafe effects and no execution errors. Live study: 240 invocations, 480 matched replays, 0 invocation errors; adaptive completes 228/240 with 0 unsafe-effect verdicts. Offline verification agrees on all 1,220 bundles. Backup/restore matches twenty tables.

Exact-host latency qualification remains separate from covered safety. See RESULTS.md for measured timing boundaries and all denominators.

## Release gates

| Gate | Status | Evidence |
|---|---|---|
| G1 Reproducible foundation | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G2 Authority and complete mediation | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G3 Conserved purchase entitlement | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G4 Durable effects and recovery | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G5 Useful adaptation | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G6 Current authority and evidence | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G7 Comparative research | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G8 Operator and evaluator experience | Passed | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G9 Operational release quality | Conditional | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G10 Submission packet | Conditional | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |
| G11 Conditional interoperability | Conditional | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |

G9 retains excluded deployment and exact-host performance qualification. G10 is conditional on owner facts/permissions/public links and user-excluded video/deployment. G11 records the exercised offline AP2 subset and owner-excluded P3P UAT. Gate status is scoped to this local release.

## Backlog evidence

| ID | Item | Status | Evidence and remaining owner action |
|---|---|---|---|
| ASV-001 | Repair copied environment and local module resolution | Done | outputs/assever-local-imports.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-002 | Separate allowed checks from actual spending | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-003 | Replace non-atomic cumulative admission | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-004 | Record baseline source and regression inventory | Done | outputs/assever-foundation-regression.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-005 | Freeze requirements and committed submission scope | Done | outputs/assever-foundation-regression.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-006 | Complete Assever market and namespace decision | Done | prd_outputs/Assever/Assever_Naming_Decision.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-007 | Test name pronunciation and spelling with fresh readers | Excluded | docs/assever/SCOPE_AMENDMENT.md. Three fresh human readers require owner-coordinated participation; no reader results are invented. |
| ASV-008 | Create consistent wordmark and product language | Done | docs/brand/assever-wordmark.svg. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-009 | Remove legacy public branding with attribution intact | Done | docs/brand/assever-wordmark.svg. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-010 | Build synthetic catalog and trusted merchant registry | Done | services/assever/assever/schemas.py. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-011 | Define canonical versioned purchase contract | Done | services/assever/assever/schemas.py. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-012 | Connect drafting and grounded validation | Done | services/assever/assever/schemas.py. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-013 | Implement trusted contract approval | Done | services/assever/assever/schemas.py. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-014 | Generate trusted demand lines and purchase slots | Done | services/assever/assever/schemas.py. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-015 | Canonicalize immutable quotes and effect projections | Done | services/assever/assever/schemas.py. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-016 | Implement scoped human agent and service authentication | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-017 | Enforce tenant owner and workflow isolation | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-018 | Protect browser sessions and approval requests | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-019 | Implement attenuated child grants | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-020 | Implement contract epochs narrowing and revocation | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-021 | Implement exact single-use exception decisions | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-022 | Version issuer keys and verify grants | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-023 | Build separate commerce simulator and order store | Done | docs/assever/ARCHITECTURE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-024 | Implement authenticated correlated callbacks | Done | docs/assever/ARCHITECTURE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-025 | Pin ONDC-inspired callback profile and fixtures | Done | docs/assever/ARCHITECTURE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-026 | Implement approved equivalent and stock replanning | Done | docs/assever/ARCHITECTURE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-027 | Validate pack sizes fees coupons and all-in totals | Done | docs/assever/ARCHITECTURE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-028 | Build typed disclosure adapter and observer sink | Done | docs/assever/ARCHITECTURE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-029 | Resolve source authenticity versus purchase authority | Done | docs/assever/ARCHITECTURE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-030 | Create transactional ledger schema and migrations | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-031 | Implement explicit transaction and root lock repository | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-032 | Implement disjoint monetary accounting buckets | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-033 | Implement quantity and purchase-count reservations | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-034 | Bind new order and retry identities to demand | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-035 | Implement preview and atomic commit API | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-036 | Implement idempotent evidence-backed settlement | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-037 | Define refunds cancellations and entitlement restoration | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-038 | Build private INR payment simulator | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-039 | Implement three explicit provider behavior profiles | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-040 | Persist atomic committed-operation outbox | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-041 | Implement worker claim leases and fencing | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-042 | Dispatch immutable bytes through trusted adapters | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-043 | Inventory and test complete mediation | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-044 | Enforce stable operation and incompatible retry conflicts | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-045 | Add deterministic response loss delay and crash hooks | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-046 | Implement durable UNKNOWN and reconciliation controller | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-047 | Implement terminal non-execution and closure barriers | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-048 | Handle dedupe expiration and opaque outcomes | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-049 | Join order and payment obligations without conflating them | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-050 | Qualify revocation at local and sink boundaries | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-051 | Implement recovery backoff queue and operator escalation | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-052 | Connect model planner and role-specific tools | Done | outputs/assever-evidence/final/live-study/summary.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-053 | Implement arbitrary-call and content-poisoning modes | Done | outputs/assever-evidence/final/live-study/summary.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-054 | Keep persistent memory and summaries outside authority | Done | outputs/assever-evidence/final/live-study/summary.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-055 | Capture model version parameters and invocation errors | Done | outputs/assever-evidence/final/live-study/summary.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-056 | Build product shell navigation and semantic layout | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-057 | Build purchase draft review and approval flow | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-058 | Build approved obligations and actual-outcome view | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-059 | Build inspectable event timeline and quote detail | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-060 | Build exact exception and stop controls | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-061 | Handle event cursors reconnect and repeated messages | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-062 | Implement all operational empty and error states | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-063 | Build matched-run safety lab controls and scorecard | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-064 | Build evidence export and verification interaction | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-065 | Create authentic public product introduction | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-066 | Add reviewed Hindi structured-field rendering | Done | docs/assever/HINDI_REVIEW.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-067 | Verify keyboard responsive and announced state changes | Done | output/playwright. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-068 | Persist correlated append-only audit events | Done | outputs/assever-evidence/offline-verification.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-069 | Build read-only independent effect observer | Done | outputs/assever-evidence/offline-verification.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-070 | Define versioned portable evidence export | Done | outputs/assever-evidence/offline-verification.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-071 | Implement separate reconstruction checker | Done | outputs/assever-evidence/offline-verification.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-072 | Test omitted conflicting reordered and forged evidence | Done | outputs/assever-evidence/offline-verification.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-073 | Generate result tables from saved run records | Done | outputs/assever-evidence/offline-verification.json. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-074 | Freeze 24 scenario families and supported invariants | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-075 | Build independent valid-basket and completion oracle | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-076 | Implement five matched runtime reference controls | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-077 | Build isolated campaign runner and immutable manifests | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-078 | Freeze holdout tasks seeds and attacker budgets | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-079 | Execute full deterministic campaign and investigate errors | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-080 | Run targeted mechanism ablations | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-081 | Run separately labeled live agent study | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-082 | Review denominators uncertainty and validity boundaries | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-083 | Write sourced contribution and prior-work comparison | Done | docs/assever/RESULTS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-084 | Create isolated local stack and deterministic seed reset | Done | docs/assever/OPERATIONS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-085 | Add CI lint schema regression and UI build checks | Done | docs/assever/OPERATIONS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-086 | Deploy scoped public demo environment | Excluded | docs/assever/SCOPE_AMENDMENT.md. Deployment explicitly excluded by the user. |
| ASV-087 | Configure secrets service identities and redaction | Done | docs/assever/OPERATIONS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-088 | Implement readiness resource limits and rate limits | Done | docs/assever/OPERATIONS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-089 | Expose correlated operational metrics and queue age | Done | docs/assever/OPERATIONS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-090 | Verify backup restore and restart durability | Done | docs/assever/OPERATIONS.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-091 | Measure runtime and UI performance under declared load | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-092 | Run complete operator and evaluator browser journeys | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-093 | Exercise real multi-process races and crash boundaries | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-094 | Review complete-mediation and isolation boundaries | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-095 | Triage and resolve submission-blocking defects | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-096 | Rehearse fresh start simultaneous visitors and demo replay | Done | outputs/assever-release-tests.txt. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-097 | Write installation integration and model-free replay guide | Done | docs/assever/README.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-098 | Publish architecture trust boundaries and invariants | Done | docs/assever/README.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-099 | Publish canonical schemas OpenAPI and adapter contracts | Done | docs/assever/README.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-100 | Publish campaign protocol results and independent verification | Done | docs/assever/README.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-101 | Inventory licenses attribution and AI assistance | Done | docs/assever/README.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-102 | Document supported scope operations and adoption path | Done | docs/assever/README.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-103 | Collect registered team contact participation and track details | Excluded | docs/assever/SCOPE_AMENDMENT.md. Registered contact/member/participation facts require the owner. |
| ASV-104 | Write title summary and website description within limits | Done | outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release/Assever_Report_Draft.pdf. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-105 | Write DPI assumption and affected-problem sections | Done | outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release/Assever_Report_Draft.pdf. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-106 | Write approach threat evaluation findings and novelty | Done | outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release/Assever_Report_Draft.pdf. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-107 | Write factual difficulty and resolution reflection | Done | outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release/Assever_Report_Draft.pdf. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-108 | Prepare factual development testing and disclosure declarations | Partial | docs/assever/SCOPE_AMENDMENT.md. Development/AI/license/synthetic-testing text prepared. Owner must verify complete team timeline and final factual declarations. |
| ASV-109 | Collect individual member publication permissions | Excluded | docs/assever/SCOPE_AMENDMENT.md. Each member must make their own publication choices. |
| ASV-110 | Produce template-complete report within ten pages | Partial | docs/assever/SCOPE_AMENDMENT.md. Template-aligned PDF prepared within ten pages. Registered team fields, personal choices and final TeamName_Report.pdf personalization remain owner-controlled. |
| ASV-111 | Storyboard and script authentic two-minute video | Excluded | docs/assever/SCOPE_AMENDMENT.md. Demo-video work explicitly excluded, including its storyboard/script. |
| ASV-112 | Record edit caption and publish demo video | Excluded | docs/assever/SCOPE_AMENDMENT.md. Demo video explicitly excluded by the user. |
| ASV-113 | Prepare public repository release and code archive | Partial | docs/assever/SCOPE_AMENDMENT.md. Source archive and file-hash manifest prepared. Public repository creation/publication requires the owner's account. |
| ASV-114 | Verify every public deliverable without authentication | Excluded | docs/assever/SCOPE_AMENDMENT.md. Public deliverable link checks follow owner publication/deployment. |
| ASV-115 | Review claims rubric coverage and complete submission packet | Done | outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release/Assever_Report_Draft.pdf. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-116 | Submit authorized entry and retain receipt | Excluded | docs/assever/SCOPE_AMENDMENT.md. Final entry submission and receipt require the registered owner. |
| ASV-117 | Establish permitted P3P UAT credentials and profile | Excluded | docs/assever/SCOPE_AMENDMENT.md. Authorized P3P sandbox account/credentials require the owner. |
| ASV-118 | Implement and exercise P3P UAT adapter | Excluded | docs/assever/SCOPE_AMENDMENT.md. Exercising UAT depends on authorized P3P credentials; no tested connector claim is made. |
| ASV-119 | Publish observed P3P compatibility and recovery boundary | Excluded | docs/assever/SCOPE_AMENDMENT.md. Observed UAT compatibility awaits owner-authorized access; the untested boundary is documented. |
| ASV-120 | Define supported AP2 mandate translation subset | Done | docs/assever/AP2_PROFILE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
| ASV-121 | Exercise AP2 compatibility fixtures and evidence | Done | docs/assever/AP2_PROFILE.md. Implemented and verified in the scoped local release. See the linked evidence and release index. |
