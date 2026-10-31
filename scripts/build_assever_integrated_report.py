"""Use the verified seven-page template layout with the integrated product/evidence."""

import importlib.util
import inspect
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Integrated_Release"
E = ROOT / "outputs/assever-integrated-evidence"


def main():
    spec = importlib.util.spec_from_file_location("report_layout", ROOT / "scripts/build_assever_report.py")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    release = json.loads((E / "release-summary.json").read_text())
    actual = release["live"]
    bridge = OUT / "_work/report-data"
    for folder in ("final/campaign", "final/live-study"):
        (bridge / folder).mkdir(parents=True, exist_ok=True)
    (bridge / "final/campaign/summary.json").write_text(json.dumps(release["campaign"]))
    live = {
        **actual,
        "per_control": {
            name: {"unsafe_effects": r["verdicts"].get("FAIL", 0), "completed_tasks": r["completed_tasks"]}
            for name, r in actual["controls"].items()
        },
    }
    (bridge / "final/live-study/summary.json").write_text(json.dumps(live))
    perf = release["performance"]["summary"]
    (bridge / "http-rehearsal-performance.json").write_text(
        json.dumps({"performance": {**perf, "p95_ms": perf["http_ms"]["p95"]}})
    )
    (bridge / "release-summary.json").write_text(json.dumps(release))
    base.OUT = OUT
    base.DATA = bridge
    base.TEXT.update(
        {
            "summary": "Assever binds AI-agent work to human-approved orders, preserving purchase quantities, budget and disclosure through delegation, parallel execution and uncertain outcomes.",
            "website": "Assever is a checkpoint between AI agents and business tools. A person approves a grounded work order; deterministic gates screen subsequent actions, preserve untrusted provenance and record cited receipts. The same product now supports synthetic kirana procurement with exact item quantities, a shared gross budget, limited delivery disclosure and durable execution. A private worker reconciles uncertain outcomes, while independent source records establish what happened. The existing task interface brings approval, pending obligations and actual effects together for operators and evaluators.",
            "approach": "Assever extends the existing Abide console, gateway, Core engine, SDK and business-policy registry. Office and support workflows retain grounded work orders, screened reads, sealed handoffs, deterministic action checks and owner-only exceptions. Procurement is an additional registered business profile, not a separate application. The person reviews exact quantities, equivalent packs, suppliers, fees, gross cap, delivery fields and expiry. One PostgreSQL transaction confirms the original work order and activates its exact purchase annex. The frozen company policy additionally limits executable authority. Typed projections bind the final checkout bytes; shared root demand identities survive new request IDs and attenuated child grants. Admission locks that root and atomically reserves integer money, quantities and purchase count while inserting a durable outbox operation. Only a private executor holds dispatch credentials. It records dispatch intent before sending and reconciles uncertain effects rather than blindly retrying. Reserved, unknown, captured and closed exposure are disjoint. Provider-qualified outcomes append to the original receipt chain and cited report. An independent standard-library checker joins human approval, policy, workflow receipts and separate order/payment/disclosure records. The original Tasks, Needs you, Activity, Connect and Evaluation pages expose the extension using the original visual system.",
            "evaluation": "We rerun the original authorization regression suite and test the actual gateway, existing identities, company policy, atomic confirmation, remote SDK and private worker over HTTP. A separate frozen Core/runtime campaign covers 24 authored families, three provider profiles, two role topologies and five controls: 720 cells. All effects, errors and unresolved obligations remain in source-linked bundles. An independent checker reconstructs gross money, quantities, disclosure and completion. The new live study uses twelve content tasks, two local Qwen models, five seeds and ordinary/attacked modes: 240 attempts, 239 captured model responses and one retained timeout. Adaptive execution traverses the original work order, read screening, gateway and background worker. Each untrusted proposal is also replayed against an isolated competent payment-budget Core reference. These are matched proposals, not 480 independent model samples; the reference has a different transport topology. Exploratory runs, mechanism removals, latency, fresh installation, backup/restore and browser journeys have separate records.",
            "adoption": "A buyer-side commerce integrator registers one supported business profile and typed purchase adapter, then extends its existing agent client with proposal, preparation, commit and status methods. Agents keep the existing scoped keys; provider credentials stay private. The owned local environment and conformance kit support a sandbox-first adoption step. IndiaAI Safety Institute or MeitY evaluators could reuse the corpus as an evaluation pilot; this is a proposed path, not an endorsement. Real rails require independently qualified settlement, status and closure contracts.",
            "limits": "The commerce profile is finite and synthetic. Its provider atomically commits order, payment and minimum disclosure; independently settling real rails need additional adapter and joint-state qualification. Opaque outcomes remain unresolved and can stop useful replanning. The live models are small Qwen models, not frontier-agent evidence. The payment reference shares proposals but uses a different transport topology. Hashes provide tamper evidence, not provider signatures or protection against a compromised trusted source. English classifier behavior does not establish multilingual security; Hindi coverage is structured labels. The measured twenty-client admission p95 exceeds the target, and exact 4-CPU/8-GB qualification remains open. Cloud integrations, live DPI and account-owned interoperability are not qualified by local testing.",
            "reflection": "The hardest boundary was the difference between approving an action and establishing its consequence. The original delegation system already grounded human instructions, screened documents, checked tool calls and preserved provenance. Extending that gate with a payment cap initially appeared sufficient. However, two affordable baskets can satisfy the same cap while violating one approved demand. A permission receipt also cannot distinguish a rejected payment from a committed payment whose response disappeared. Releasing capacity after a timeout creates duplicate replacement rights, while retaining it indefinitely sacrifices useful completion. Adding another language model would not resolve this accounting question because the proposal and its explanation can both be influenced by seller content. We therefore made purchase identity, normalized quantities and pending obligations explicit and transactional. The difficult integration decision was keeping one product authority boundary: a second application, login system or receipt-only ledger would leave ambiguous ownership and bypass paths. We moved the purchase modules into the existing Core, tied them to original workflows and business policy, and made confirmation atomic. A private executor became the only dispatch path; existing tool wrappers return an operation handle instead of executing again. Actual outcomes are mirrored into the original receipt chain and independently reconstructed. This gives up general purchasing semantics and seamless recovery for opaque providers in exchange for an executable, inspectable contract. Safe preapproved alternatives remain useful, but uncertainty is never relabeled as success merely to improve completion statistics.",
        }
    )
    base.TEXT["evaluation"] = base.TEXT["evaluation"].replace("not 480 independent model samples", "478 replays, not independent model samples")
    code = inspect.getsource(base.main)
    code = (
        code.replace("#143C68", "#1D5E46")
        .replace("#4C647A", "#4A5466")
        .replace("#EDF4FA", "#E5F0EA")
        .replace("#183047", "#101826")
    )
    code = code.replace("Purchase integrity for AI agents", "Work-order governance and purchase integrity").replace(
        "Assever: Purchase integrity for AI agents", "Assever: Work-order governance and purchase integrity"
    )
    code = code.replace('("Purchase API",182,90)', '("Existing gateway",182,90)').replace(
        '("Ledger + outbox",356,90)', '("Core ledger + outbox",356,90)'
    )
    old = "f\"Live protocol v2: {live['actual_invocations']} model invocations; {live['errors']} invocation/execution errors retained. Adaptive replay has {live['per_control']['adaptive']['unsafe_effects']} unsafe-effect verdicts and completes 228/240 tasks: 120/120 ordinary and 108/120 attacked. Payment-only replay produces 67 unsafe outcomes across the same 240 proposals.\""
    new = "f\"Integrated live protocol v4: {live['actual_invocations']} real model invocations; {live['errors']} retained errors. Adaptive gateway execution has {live['per_control']['adaptive']['unsafe_effects']} unsafe-effect verdicts and completes {live['per_control']['adaptive']['completed_tasks']}/240 tasks. The matched payment reference produces {live['per_control']['payment']['unsafe_effects']} unsafe outcomes across 239 captured proposals; one of 240 attempts timed out.\""
    assert old in code
    code = code.replace(old, new)
    code = code.replace("Database/process regression:", "Integrated gateway / database / process regression:")
    code = code.replace(
        "Live and deterministic denominators are separate. The exploratory first live protocol is retained; final results use the revised finite tool schema and a newly frozen seed set.",
        f"Original-system regression: {release['foundation_tests']} passed, one optional LangChain skip; console: eight passed. Live and conformance denominators are separate; exploratory runs are retained.",
    )
    code = code.replace(
        "Deliverables: local Docker product;",
        "Deliverables: existing Abide evolved into Assever in local Docker; original console/gateway/Core/SDK and workflows retained;",
    )
    code = code.replace("Local self-service sessions", "Existing scoped gateway keys")
    code = code.replace("with unresolved outcomes reported separately.", "with unresolved outcomes reported separately.")
    code = code.replace("purchase_tests']} tests pass; eight-process", "purchase_tests']} tests pass; eight-process")
    code = code.replace(
        "Actual results: release evidence final/campaign, final/live-study, ablations, test logs and portable checker bundles.",
        "Actual results: outputs/assever-integrated-evidence/final; integrated test logs, source manifests and portable checker bundles.",
    )
    code = code.replace("Synthetic purchase-integrity research", "Integrated work-order and purchase research")
    code = code.replace(
        "and each browser visitor has a separate tenant.", "and each authenticated work-order owner has isolated purchase scope."
    )
    exec(compile(code, "integrated_report_layout", "exec"), base.__dict__)
    base.main()


if __name__ == "__main__":
    main()
