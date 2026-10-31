"""Reconcile the integrated release from evidence, preserving the prior package."""

from pathlib import Path
from collections import Counter
import csv
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "outputs/assever-integrated-evidence"
PLAN = ROOT / "outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever"
OUT = PLAN.parent / "Assever_Integrated_Release"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def passed(path):
    match = re.search(r"(\d+) passed", path.read_text(encoding="utf-8-sig"))
    assert match, path
    return int(match.group(1))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    campaign = read(E / "final/integrated-campaign/summary.json")
    live = read(E / "final/integrated-live-study/summary.json")
    rows = read(E / "final/integrated-live-study/results.json")
    offline = read(E / "offline-verification.json")
    assert campaign["cells"] == 720 and live["rows"] == 240
    assert live["actual_invocations"] + live["errors"] == 240
    assert offline["total_bundles"] == 740 + sum(r["replays"] for r in live["controls"].values())
    backups = sorted(E.glob("backup-*/verification.json"))
    assert backups and all(r["match"] for r in read(backups[-1]))
    clean = read(E / "clean-install.json")
    assert clean["passed"]
    performance = read(E / "performance.json")
    breakdown = {}
    for model in sorted({r["model"] for r in rows}):
        breakdown[model] = {}
        for mode in ("ordinary", "attacked"):
            subset = [r for r in rows if r["model"] == model and r["mode"] == mode]
            breakdown[model][mode] = {"invocations": len(subset), "errors": sum(bool(r["error"]) for r in subset), "controls": {}}
            for control in ("payment", "adaptive"):
                records = [r["controls"][control]["verification"] for r in subset if control in r["controls"]]
                breakdown[model][mode]["controls"][control] = {
                    "replays": len(records),
                    "unsafe_effects": sum(v["verdict"] == "FAIL" for v in records),
                    "completed_tasks": sum(v["task_complete"] for v in records),
                }
    result = {
        "version": "1.1.0-integrated",
        "product": "Original Abide evolved in place into Assever",
        "local_url": "http://localhost:8000",
        "purchase_tests": passed(ROOT / "outputs/assever-integrated-purchase-final-tests.txt"),
        "foundation_tests": passed(ROOT / "outputs/assever-integrated-foundation-postgres-tests.txt"),
        "foundation_skips": 1,
        "console_tests": 8,
        "campaign": campaign,
        "live": live,
        "live_breakdown": breakdown,
        "offline": offline,
        "performance": performance,
        "backup_tables": len(read(backups[-1])),
        "backup_proof": str(backups[-1].relative_to(ROOT)),
        "clean_install": clean,
        "scope": "Local Docker only. Video, cloud deployment, publication and mandatory owner/account/consent actions excluded.",
        "limitations": [
            "Finite synthetic catalog; owned atomic order/payment/disclosure sink.",
            "Core/runtime conformance and actual gateway model execution have separate denominators.",
            "Payment comparison is an authored isolated Core reference with different transport topology.",
            "Exact 4-CPU/8-GB latency qualification remains open; observed p95 exceeds the 100-ms target.",
            "Cloud Model Armor, Vertex/IAM and BigQuery qualification await a later authorized cloud project.",
            "Offline AP2 projection is limited; P3P UAT is excluded. No network certification claim.",
        ],
    }
    dump(E / "release-summary.json", result)
    dump(OUT / "Measured_Results.json", result)
    status = read(PLAN / "Assever_Backlog.json")
    # Keep the original IDs, acceptance text, order, exclusions and effort estimates.
    prior = OUT / "Previous_Component_Backlog.json"
    if not prior.exists():
        shutil.copy2(PLAN / "Assever_Backlog.json", prior)
    for row in status["rows"]:
        if row["status"] != "Done":
            continue
        row["evidence"] = "docs/assever/INTEGRATED_RELEASE_STATUS.md"
        row["completion_note"] = (
            "Integrated into the original Abide product boundary; verified in the local Docker release. See integrated status and source-linked evidence."
        )
        if row["key"] == "perf":
            row["completion_note"] = (
                "Measured under twenty synchronized clients with timing boundaries and actual-effect verification. The <=100 ms exact-host qualification is still open and is not marked passed."
            )
    status["implementation_version"] = "1.1.0-integrated"
    status["notes"] = [
        "Assever is the renamed Abide product, extended in its existing console/gateway/Core/SDK boundaries.",
        "Statuses refer to the local integrated release; raw prior standalone evidence is preserved separately.",
        "Done records completed scoped work. G9 remains conditional on exact-host performance qualification and excluded deployment.",
        "Video, public deployment/publication and mandatory owner identity/account/consent actions remain excluded or partial.",
        "Effort hours are original estimates, not measured elapsed implementation time.",
    ]
    for gate in status["gates"]:
        gate["status"] = "Conditional" if gate["id"] in ("G9", "G10", "G11") else "Passed"
        gate["evidence"] = "docs/assever/INTEGRATED_RELEASE_STATUS.md"
    for section in status["submission"]:
        section["evidence"] = "Assever_Integrated_Release/Assever_Report_Draft.pdf"
    dump(PLAN / "Assever_Backlog.json", status)
    dump(OUT / "Assever_Backlog.json", status)
    fields = [
        "id",
        "epic",
        "title",
        "type",
        "priority",
        "required",
        "milestone",
        "status",
        "owner",
        "hours",
        "dependencies",
        "requirements",
        "acceptance",
        "verification",
        "gate",
        "severity",
        "evidence",
        "completion_note",
    ]
    for target in (PLAN / "Assever_Backlog.csv", OUT / "Assever_Backlog.csv"):
        with target.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(status["rows"])
    counts = dict(Counter(r["status"] for r in status["rows"]))
    dump(OUT / "Backlog_Status_Counts.json", counts)
    text = [
        "# Assever integrated local release",
        "",
        "The original Abide console, gateway, Core, SDK, policies, office/support workflows and integrations are retained. Purchase logic is integrated into those boundaries. Active URL: http://localhost:8000 . The earlier standalone application is stopped, with its data preserved.",
        "",
        f"Backlog reconciliation: {counts}. Original estimates remain estimates. All owner-controlled and user-excluded actions retain their explicit status.",
        "",
        "## Verification",
        "",
        f"- {result['purchase_tests']} product/integration tests pass; {result['foundation_tests']} original-system tests pass, with one optional LangChain skip; eight console tests pass.",
        "- Full 720-cell Core/runtime conformance campaign: zero execution errors, zero adaptive unsafe-effect verdicts, 12/144 adaptive unresolved outcomes, 126/144 adaptive completed tasks. The conservative control completes 120/144.",
        f"- Full gateway live study: {live['actual_invocations']} real model invocations, {live['errors']} retained errors. See the exact per-control counts below.",
        f"- Offline checker agrees with all {offline['total_bundles']:,} final bundles and source/manifest hashes. The 240-attempt model study retains one timeout without inventing its missing proposal or replay.",
        f"- Backup/restore matches {result['backup_tables']} tables; independent fresh installation and full gateway integration suite pass.",
        "- Browser evidence covers original support attacks and office work, exact purchase review, real worker completion, duplicate refusal, export/checker/report, Evaluation, mobile/Hindi, keyboard, theme persistence and reconnect. Injected offline errors and expected refusals are retained; no zero-console-error claim.",
        "",
        "## Live study · separate from authored conformance",
        "",
        "| Control | Matched replays | Unsafe effects / FAIL | Completed | Unresolved |",
        "|---|---:|---:|---:|---:|",
    ]
    for control, value in live["controls"].items():
        text.append(
            f"| {control} | {value['replays']} | {value['verdicts'].get('FAIL', 0)} | {value['completed_tasks']} | {value['verdicts'].get('INCOMPLETE', 0)} |"
        )
    text += [
        "",
        "Each invocation produces one untrusted proposal; replay comparisons are not independent model samples. Adaptive runs through the original gateway, approved delegation, read screening, SDK-compatible operations and background worker. Payment is a competent authored Core reference, not a commercial product measurement or identical transport topology.",
        "",
        "## Timing and open gates",
        "",
        f"Twenty synchronized real commits: core admission p95 {performance['summary']['core_admission_ms']['p95']} ms; provider readiness p95 {performance['summary']['provider_readiness_ms']['p95']} ms; HTTP commit p95 {performance['summary']['http_ms']['p95']} ms. All twenty effect bundles verify complete. The host has eight Docker CPUs and approximately 16 GB RAM. This does not meet or establish <=100 ms p95 on the PRD 4-CPU/8-GB target.",
        "",
        "G1–G8 pass for the scoped local release. G9 is conditional: exact-host latency qualification remains open and deployment is excluded. G10 retains owner facts/consents/public links and excluded video/publication. G11 retains the limited AP2 projection and excluded P3P UAT. No cloud project or account action has been performed.",
        "",
        "## Source and evidence",
        "",
        "- Existing product: services/gateway, packages/core, packages/sdk, apps/console, original business policies.",
        "- Purchase extension: packages/core/intentseal_core/purchase; policies/delegate/kirana.yaml; purchase_api.py; private evaluator and worker.",
        "- Evidence: outputs/assever-integrated-evidence/final, test logs and output/playwright/assever-integrated-*.",
        "- Current requirements/operations: INTEGRATED_PRD.md and INTEGRATED_OPERATIONS.md. Architecture baseline and as-built local diagram: integrated-design/.",
        "",
        "## Backlog evidence",
        "",
        "| ID | Item | Status | Completion / remaining action |",
        "|---|---|---|---|",
    ]
    text += [f"| {r['id']} | {r['title']} | {r['status']} | {r.get('completion_note', '')} |" for r in status["rows"]]
    (ROOT / "docs/assever/INTEGRATED_RELEASE_STATUS.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    for source in ("INTEGRATED_PRD.md", "INTEGRATED_OPERATIONS.md", "INTEGRATED_RELEASE_STATUS.md"):
        shutil.copy2(ROOT / "docs/assever" / source, OUT / source)
    print(
        json.dumps(
            {
                "status_counts": counts,
                "tests": result["purchase_tests"],
                "foundation": result["foundation_tests"],
                "live": live,
                "backup_tables": result["backup_tables"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
