# Assever — submission readiness checklist

Prepared 31 October 2026 against the SAFL submission template, the official event page and `HANDOFF.md`. Deadline (as extended): 1 November 2026. Submit once per team at bit.ly/saflhacksubmission.

Legend: ✅ ready · ⚠️ needs a fix or decision · 👤 owner fact or consent required (not inferred here).

The concept note (Google Doc) needs a sign-in and could not be read; the template and event page were used instead. Please skim the concept note for anything the template does not repeat.

## Live verification (31 Oct, production revision `assever-00002-d8b`)

| Check | Result |
|---|---|
| Hard refresh: indigo hero, saffron seal and buttons, section order | ✅ |
| 375 px layout | ✅ no page-level horizontal scroll (evidence table scrolls inside its card) |
| Dark mode | ✅ renders; see focus fix below |
| Keyboard | ⚠️ focus ring was indigo-on-indigo in the hero and final CTA band — fixed in source |
| Numbers band after animation | ⚠️ headline values stayed "—" although `/v1/delegate-eval` returned data (`CountUp` never showed the arrived value until it re-intersected) — fixed in source |
| CTAs | ✅ Hijacked agent → `/tasks?task=new&preset=attack`; Run your own task → `/delegate`; Connect your agent → Developers section · ⚠️ "Replay a purchase" opened the generic task sandbox — now "Start a purchase" → `/tasks?task=new-purchase` |
| Console pages: Tasks, Needs you, Activity, Connect, Evaluation | ✅ render with new palette, no console errors |
| Deterministic buyer purchase (`wf-c89cd94f9f`) | ✅ ₹700 captured, 14-record chain, verifier PASS · task complete, receipt cites R-2…R-4, chain intact |
| Approved **Gemini 3.5 Flash** purchase (`wf-aa47db7ce9`, op `op_c376b72a…`) | ✅ admitted, ₹700 captured, verifier PASS · task complete, receipt cites R-2/R-4/R-5, chain intact |
| Duplicate Gemini proposal on the same approval | ✅ refused `DEMAND_ALREADY_ENCUMBERED`; captured stays ₹700 |
| Evidence download | ✅ button present after verification and built from the fetched bundle (file save not exercised in the test browser) |
| Ownership across users | Not re-tested; covered by the existing 76-test suite |

### Frontend fixes made in source (need a frontend-only redeploy)

- `pages/Overview.tsx`: `CountUp` shows real values; stack label and two copy lines now say PostgreSQL on a dedicated Persistent Disk instead of Cloud SQL; proof strip leads with the deployed campaign and Gemini cohort and labels the Qwen study as historical and separate; trust row and objection copy describe owned ONDC/UPI-style simulators; purchase CTA fixed.
- `components/Purchase.tsx`: "local workspace" copy corrected; Qwen options labelled "local Docker only"; model results shown in plain language instead of raw JSON.
- `landing.css`: saffron focus ring on the dark bands.
- Backend, APIs, database, environment, secrets and IAM untouched. `tsc --noEmit` passes; no test suites were run.

Redeploy instruction for Codex: build `apps/console` (`npm ci && npm run build`) and redeploy the frontend image exactly as for `assever-00002-d8b`; change nothing else.

## Template sections

### 1. Team information — 👤
| Field | Status |
|---|---|
| Team name | 👤 |
| Primary contact name, registered email, phone/WhatsApp | 👤 must match registration |
| Team size | 👤 |

### 2. Team members — 👤
Full name, email, institution (or "Independent"), background for each member. 👤

### 3. How you took part
| Field | Status |
|---|---|
| Participation mode | 👤 IIT Delhi / Bengaluru / online only |
| Track | ✅ Technical |
| Challenge area | ✅ System Resilience (supporting Trust & Consent and Accountability in prose only; pick one in the form) |

### 4. Project overview
| Field | Status |
|---|---|
| Title | ✅ Assever (suggest: "Assever: purchase integrity for AI agents on India's commerce and payment rails") |
| One-line summary (≤25 words) | ✅ 20 words in `Assever_Report_Content.md` |
| Website description (60–100) | ✅ 86 words |

### 5. The problem
| Field | Status |
|---|---|
| DPI systems | ✅ ONDC and UPI, qualified as **team-owned synthetic simulators**; cross-cutting if allowed. No Aadhaar/DigiLocker. |
| Broken DPI assumption (80–150) | ✅ 103 words |
| Problem and who is affected (100–150) | ✅ 115 words |

### 6. Approach and findings
| Field | Status |
|---|---|
| Approach (150–250) | ✅ 198 words |
| Threat model under exposure (150–250) | ✅ 183 words. Must say plainly that nothing depends on secrecy except service credentials. |
| Evaluation (100–200) | ✅ 162 words |
| Key results (2–4 bullets) | ⚠️ add the discriminating result — see below |
| What's new | ✅ executable purchase-integrity profile; cite AP2, P3P, Grantex, the 2026 runtime-verification papers |
| Who could use it | ✅ buyer-side integrators and payment apps adding agentic checkout; first step: wrap purchase tools with the SDK and run the conformance kit |
| Limitations (80–150) | ✅ 117 words |

**Key results — recommended wording (keeps cohorts separate):**
- Deployed authored campaign (720 cells, 144 per control): payment-budget control 36 unsafe effects, permission control 36, unrestricted 54; Assever adaptive **0**, completing 126/144 vs 92/144.
- Deployed Gemini cohort (Vertex, 240 attempts, 235 valid plans, 5 errors retained): Assever 0 unsafe, 235 tasks completed. Gemini proposals were also safe under the payment control, so this cohort shows utility under real models, not a safety gap.
- Historical local study (Qwen 0.5B/0.6B, separate run): payment control 53/239 unsafe, Assever 0/239.
- 1,195 effect bundles independently re-verified; core admission p95 93.9 ms on 4 vCPU / 8 GB; eight-process race admits 1 basket and refuses 99 duplicates.

The current draft's results section omits the 36-vs-0 campaign comparison, which is the strongest evidence. Add it.

### 7. Reflection
| Field | Status |
|---|---|
| Difficulty (200–300) | ✅ 263 words |
| How you overcame it | ✅ check it states trade-offs given up |

### 8. Deliverables and declarations
| Field | Status |
|---|---|
| Main file `TeamName_Report.pdf` (≤10 pages) | ⚠️ draft is 7 pages as `Assever_Report_Draft.pdf`; rename after 👤 team name, add the key-results fix, re-export, upload with public link |
| Code repository + README | ✅ github.com/sankalp2515/assever — confirm public and the README reproduces results |
| Demo video (≤2 min) | ⚠️ not made yet — recommended; record after the frontend redeploy |
| Other artifacts | ✅ `Assever_Evidence_v1.2.4.zip` + `scripts/verify_assever_google_exports.py` — host publicly |
| Done during the hackathon? | 👤 "Built on earlier work" is likely correct: the governance foundation (work orders, gate, receipts) predates the purchase-integrity work. Owner must state what existed before and when. |
| AI tools used | 👤 confirm exact list. Known: Codex (GPT-6 family, research/implementation/tests/docs), ChatGPT (earlier planning docs), Claude Opus 5.5 via Claude Code (frontend redesign, landing copy, review, this checklist). In-product: Gemini 3.5 Flash and 3.1 Flash-Lite (Vertex), Qwen 2.5 0.5B / Qwen3 0.6B (historical local study). |
| External code/models/datasets + licences | ✅ from `docs/assever/ATTRIBUTION.md` (ProtectAI DeBERTa Apache-2.0, FastAPI/React MIT, psycopg LGPL-3.0, PostgreSQL licence, fonts OFL, etc.) |
| All links public without login | 👤 verify in a private window: repo, report PDF, evidence ZIP, video, live app |

### 9. Responsible testing
| Field | Status |
|---|---|
| No real personal data | ✅ Yes — all suppliers, shops, money synthetic |
| Responsible disclosure | ✅ Yes — no real-system weakness found or published |
| Environment | ✅ "Team-owned ONDC-style commerce and UPI-style payment simulators on our Google Cloud project (Cloud Run edge, Compute Engine runtime, PostgreSQL on Persistent Disk, Vertex AI Gemini). No live ONDC, UPI, bank or Aadhaar system was touched." |

### 10. Permissions — 👤
Each member must answer Q1 (feature project) and Q2 (names/institutions) individually. Not inferred.

## Consistency rules for every material

- Product name is **Assever** only. `intentseal_*` are internal package identifiers, not product names.
- Never merge the Qwen and Gemini numbers; label Qwen "historical local study".
- Storage is PostgreSQL on a dedicated Persistent Disk (Compute Engine), not Cloud SQL. Other docs still saying Cloud SQL (e.g. the older `docs/ARCHITECTURE.md`) should be updated or marked historical.
- ONDC/UPI are owned simulators; no P3P UAT, live ONDC participation, UPI settlement, Aadhaar or DigiLocker claims; AP2 is a limited offline projection.

## Questions for the owner

1. Team name, primary contact (name, registered email, phone), team size, and each member's name, email, institution, background.
2. Participation mode (Jam site or online).
3. What existed before 12 Aug 2026 and what was built during the hackathon, with approximate dates.
4. Complete AI-tool list with versions, as each member used them.
5. Each member's Yes/No on permissions Q1 and Q2.
6. Who will submit the form, and confirmation that the repo, report, evidence ZIP and video links are public.
