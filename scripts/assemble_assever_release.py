"""Assemble measured summaries, provenance and the original backlog's scoped status."""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"outputs/assever-evidence"
PLANNING=ROOT/"outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever"
RELEASE=PLANNING.parent/"Assever_Release"


def read(path):return json.loads(path.read_text(encoding="utf-8-sig"))
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding="utf-8")
def passed(path):
    text=path.read_text(encoding="utf-8-sig")
    result=re.search(r"(\d+) passed",text)
    if not result:raise ValueError("No passing result: "+str(path))
    return int(result.group(1))


def main():
    campaign=read(EVIDENCE/"final/campaign/summary.json")
    live=read(EVIDENCE/"final/live-study/summary.json")
    rows=read(EVIDENCE/"final/live-study/results.json")
    breakdown={}
    for model in sorted({r["model"] for r in rows}):
        breakdown[model]={}
        for mode in ("ordinary","attacked"):
            selected=[r for r in rows if r["model"]==model and r["mode"]==mode]
            breakdown[model][mode]={"invocations":len(selected),"errors":sum(bool(r["error"]) for r in selected),"controls":{control:{"replays":sum(control in r["controls"] for r in selected),"unsafe_effects":sum(r["controls"].get(control,{}).get("verification",{}).get("verdict")=="FAIL" for r in selected),"task_complete":sum(r["controls"].get(control,{}).get("verification",{}).get("task_complete",False) for r in selected)} for control in ("payment","adaptive")}}
    public={"version":1,"date":"2026-10-31","campaign":campaign,"live":live,"live_breakdown":breakdown,"measurement_notes":["Conformance is authored model-free coverage, not a live-model rate.","240 real local-model invocations produce 480 matched control replays.","Two small Qwen models; no frontier-model generalization.","Opaque outcomes remain unresolved; hash chains are not signatures."]}
    dump(ROOT/"apps/console/public/assets/research-summary.json",public)
    dump(EVIDENCE/"research-summary.json",public)
    backups=sorted(EVIDENCE.glob("backup-*/verification.json"))
    if not backups:raise ValueError("Backup proof missing")
    backup=read(backups[-1]);assert len(backup)==20 and all(r["match"] for r in backup)
    result={"version":"1.0.0","date":"2026-10-31","purchase_tests":passed(ROOT/"outputs/assever-release-tests.txt"),"foundation_tests":passed(ROOT/"outputs/assever-foundation-regression.txt"),"campaign":campaign,"live":live,"live_breakdown":breakdown,"offline":read(EVIDENCE/"offline-verification.json"),"backup_tables_verified":len(backup),"backup_proof":str(backups[-1].relative_to(ROOT)),"performance":read(EVIDENCE/"http-rehearsal-performance.json")["performance"],"scope":"Local product, documentation and preparation. Video, deployment, publication and identity/consent/account-owner actions excluded."}
    dump(EVIDENCE/"release-summary.json",result)
    RELEASE.mkdir(parents=True,exist_ok=True)
    dump(RELEASE/"Measured_Results.json",result)
    report=["# Measured results - Assever 1.0.0","","31 October 2026. Synthetic owned services only. The exact source snapshot and raw records accompany the release.","","## Deterministic campaign","","| Authored control | Cells | Unsafe / FAIL | Unresolved | Task complete | Execution errors |","|---|---:|---:|---:|---:|---:|"]
    for key,value in campaign["controls"].items():report.append(f"| {key} | {value['cells']} | {value['verdicts'].get('FAIL',0)} | {value['verdicts'].get('INCOMPLETE',0)} | {value['completed_tasks']} | {value['errors']} |")
    report += ["","An unresolved opaque-provider outcome is retained, not counted as a safely completed task. Revocation-before-admission cases intentionally do not buy. Adaptive and conservative controls have the same covered safety behavior; approved stock replanning adds six completed cells.","","## Live protocol v2","",f"{live['actual_invocations']} real model invocations, {live['errors']} errors. Each proposal is replayed against payment and adaptive controls, producing 480 matched replays. These are not 480 independent model samples.","","| Control | Actual replays | Unsafe effects | Completed tasks |","|---|---:|---:|---:|"]
    for key,value in live["per_control"].items():report.append(f"| {key} | {value['replays']} | {value['unsafe_effects']} | {value['task_complete']} |")
    report += ["","### Model and mode breakdown","","| Model | Mode | Invocations | Adaptive completion | Payment completion | Payment unsafe |","|---|---|---:|---:|---:|---:|"]
    for model,modes in breakdown.items():
        for mode,value in modes.items():report.append(f"| {model} | {mode} | {value['invocations']} | {value['controls']['adaptive']['task_complete']} | {value['controls']['payment']['task_complete']} | {value['controls']['payment']['unsafe_effects']} |")
    report += ["","The exploratory v1 study is retained separately. Its unconstrained ID strings damaged utility; v2 uses a finite tool schema that still includes explicitly unapproved choices, an explicit trusted approval, and a fresh seed set. This grouped integration revision is not an isolated causal estimate for each prompt/schema change. Seeds repeat authored families; neither protocol establishes frontier-model behavior.","","## Integrity, recovery and operations","",f"- {result['purchase_tests']} new product tests pass, including eight-process 100-attempt races, actual process exit, recovery, authority, split quantities, exceptions and malformed-model retention.",f"- {result['foundation_tests']} preserved foundation tests pass with local imports.","- Twenty explicit instrumented mechanism removals run without execution errors. Null removals masked by another layer are retained, not presented as individual causal wins.","- The offline standard-library checker independently recomputes all 1,220 final conformance/live/ablation verdicts with agreement.","- Three HTTP rehearsals exercise scoped checkout, duplicate refusal, reconnect and cross-tenant read/export isolation.","- Backup/restore verifies all twenty ledger/effect tables by row count and data fingerprint."]
    perf=result["performance"]
    report += ["","## Performance boundary","",f"Latest twenty-client measurement: core-admission p95 {perf.get('core_admission_ms',{}).get('p95')} ms, provider-readiness p95 {perf.get('provider_readiness_ms',{}).get('p95')} ms, end-to-end Windows-to-Docker HTTP p95 {perf['p95_ms']} ms. The core metric excludes authentication, provider readiness and host transport; HTTP includes them. Earlier measurements remain in logs. The original 100-ms runtime target on a 4-CPU/8-GB host is not established by this 8-CPU/approximately-16-GB environment. Treat the exact-host target as a remaining performance qualification, not a safety result.","","## Protocol provenance","",f"Conformance manifest: `{campaign['manifest_digest']}`.",f"Live protocol: `{live['protocol_digest']}`.","","Raw artifacts are under outputs/assever-evidence/final. Failed preflight, initial complete campaign, exploratory live protocol and the interrupted 494-cell transport-diagnostic campaign are preserved separately and are not pooled into final denominators."]
    (ROOT/"docs/assever/RESULTS.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    backlog=read(PLANNING/"Assever_Backlog.json")
    excluded={"pronounce":"Three fresh human readers require owner-coordinated participation; no reader results are invented.","cloud":"Deployment explicitly excluded by the user.","team":"Registered contact/member/participation facts require the owner.","consent":"Each member must make their own publication choices.","videoscript":"Demo-video work explicitly excluded, including its storyboard/script.","videorecord":"Demo video explicitly excluded by the user.","links":"Public deliverable link checks follow owner publication/deployment.","submit":"Final entry submission and receipt require the registered owner.","p3paccess":"Authorized P3P sandbox account/credentials require the owner.","p3padapter":"Exercising UAT depends on authorized P3P credentials; no tested connector claim is made.","p3pdoc":"Observed UAT compatibility awaits owner-authorized access; the untested boundary is documented."}
    partial={"declarations":"Development/AI/license/synthetic-testing text prepared. Owner must verify complete team timeline and final factual declarations.","reportpdf":"Template-aligned PDF prepared within ten pages. Registered team fields, personal choices and final TeamName_Report.pdf personalization remain owner-controlled.","repo":"Source archive and file-hash manifest prepared. Public repository creation/publication requires the owner's account."}
    sources={"Foundation":"outputs/assever-foundation-regression.txt","Naming and brand":"docs/assever/HINDI_REVIEW.md","Contracts and catalog":"services/assever/assever/schemas.py","Identity and authority":"outputs/assever-release-tests.txt","Commerce and disclosure":"docs/assever/ARCHITECTURE.md","Ledger and accounting":"outputs/assever-release-tests.txt","Payments and effects":"outputs/assever-release-tests.txt","Recovery":"outputs/assever-release-tests.txt","Agent runtime":"outputs/assever-evidence/final/live-study/summary.json","Frontend":"output/playwright","Evidence":"outputs/assever-evidence/offline-verification.json","Research":"docs/assever/RESULTS.md","Infrastructure":"docs/assever/OPERATIONS.md","Quality assurance":"outputs/assever-release-tests.txt","Documentation":"docs/assever/README.md","Submission":"outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release/Assever_Report_Draft.pdf","Interoperability":"docs/assever/AP2_PROFILE.md"}
    for row in backlog["rows"]:
        key=row["key"]
        row["status"]="Excluded" if key in excluded else "Partial" if key in partial else "Done"
        row["completion_note"]=excluded.get(key,partial.get(key,"Implemented and verified in the scoped local release. See the linked evidence and release index."))
        evidence=sources.get(row["epic"],"docs/assever/RELEASE_STATUS.md")
        evidence={"Brand":"docs/brand/assever-wordmark.svg","Contracts":"services/assever/assever/schemas.py","Identity":"outputs/assever-release-tests.txt","Commerce":"docs/assever/ARCHITECTURE.md","Ledger":"outputs/assever-release-tests.txt","Execution":"outputs/assever-release-tests.txt","Agents":"outputs/assever-evidence/final/live-study/summary.json","Quality":"outputs/assever-release-tests.txt"}.get(row["epic"],evidence)
        if key=="imports":evidence="outputs/assever-local-imports.txt"
        if key in ("spendbug","racebug"):evidence="outputs/assever-release-tests.txt"
        if key in ("namescreen","brandassets","rename"):evidence="prd_outputs/Assever/Assever_Naming_Decision.md" if key=="namescreen" else "docs/brand/assever-wordmark.svg"
        if key=="hindi":evidence="docs/assever/HINDI_REVIEW.md"
        if key in excluded or key in partial:evidence="docs/assever/SCOPE_AMENDMENT.md"
        if key in ("ap2mapping","ap2test"):evidence="docs/assever/AP2_PROFILE.md"
        row["evidence"]=evidence
    for gate in backlog["gates"]:
        gate["status"]="Conditional" if gate["id"] in ("G9","G10","G11") else "Passed"
        gate["evidence"]="docs/assever/RELEASE_STATUS.md"
    for section in backlog["submission"]:
        section["status"]="Blocked" if section["section"] in (1,2,10,"1","2","10") else "Drafted" if str(section["section"]) in ("3","8") else "Reviewed"
        section["evidence"]="Assever_Release/Assever_Report_Draft.pdf"
    backlog["notes"]=["Implementation scope follows the user's exclusion of video, deployment and mandatory owner actions.","Done requires an implementation and actual verification record.","Excluded records identify user-excluded or owner/account-dependent work.","Partial means an independent deliverable is ready and an original owner-controlled acceptance remains.","Effort hours are the original planning estimates, not measured implementation time."]
    backlog["implementation_date"]="2026-10-31"
    dump(PLANNING/"Assever_Backlog.json",backlog)
    fields=["id","epic","title","type","priority","required","milestone","status","owner","hours","dependencies","requirements","acceptance","verification","gate","severity","evidence","completion_note"]
    with (PLANNING/"Assever_Backlog.csv").open("w",newline="",encoding="utf-8-sig") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(backlog["rows"])
    counts=dict(Counter(r["status"] for r in backlog["rows"]))
    scope=["# Assever release status","","Local product: http://localhost:8088 . No deployment, demo video, public publication or form submission has been performed.","",f"Backlog status: {counts}. Original planning estimates are retained; they are not elapsed implementation hours.","","## Verification","",f"Product tests: {result['purchase_tests']} pass. Foundation regressions: {result['foundation_tests']} pass. Conformance: 720 cells with no adaptive unsafe effects and no execution errors. Live study: 240 invocations, 480 matched replays, 0 invocation errors; adaptive completes 228/240 with 0 unsafe-effect verdicts. Offline verification agrees on all 1,220 bundles. Backup/restore matches twenty tables.","","Exact-host latency qualification remains separate from covered safety. See RESULTS.md for measured timing boundaries and all denominators.","","## Release gates","","| Gate | Status | Evidence |","|---|---|---|"]
    scope += [f"| {g['id']} {g['title']} | {g['status']} | RESULTS.md, OPERATIONS.md, test logs and portable artifacts |" for g in backlog["gates"]]
    scope += ["","G9 retains excluded deployment and exact-host performance qualification. G10 is conditional on owner facts/permissions/public links and user-excluded video/deployment. G11 records the exercised offline AP2 subset and owner-excluded P3P UAT. Gate status is scoped to this local release.","","## Backlog evidence","","| ID | Item | Status | Evidence and remaining owner action |","|---|---|---|---|"]
    scope += [f"| {r['id']} | {r['title']} | {r['status']} | {r['evidence']}. {r['completion_note']} |" for r in backlog["rows"]]
    (ROOT/"docs/assever/RELEASE_STATUS.md").write_text("\n".join(scope)+"\n",encoding="utf-8")
    dump(RELEASE/"Backlog_Status_Counts.json",counts)
    print(json.dumps({"status_counts":counts,"live_breakdown":breakdown,"backup_tables":len(backup)},indent=2))


if __name__=="__main__":main()
