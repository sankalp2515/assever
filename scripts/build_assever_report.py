"""Generate the template-aligned submission draft from measured release evidence."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, String, Line

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release"
DATA=ROOT/"outputs/assever-evidence"

TEXT={
"summary":"Assever preserves human-approved purchases across AI-agent delegation, changing merchant messages and uncertain payments using shared entitlements and independently checked effect evidence.",
"website":"Assever keeps an approved purchase intact while AI agents find stock, delegate checkout and recover from uncertain payments. Its first workflow is synthetic kirana procurement: one rice-and-oil basket from approved suppliers, within an all-in budget. A shared ledger enforces both money and item quantities. Immutable operations, conservative recovery and scoped disclosure connect approval to actual effects. A safety lab compares matched controls, and an independent checker reconstructs outcomes from separate commerce, payment and egress records.",
"dpi":"We assume a digital commerce workflow in which an agent discovers a supplier, selects catalog items, obtains a final checkout, confirms an order and learns its payment outcome asynchronously. A kirana operator delegates a bounded replenishment purchase rather than granting a general spending wallet. The owned environment models two suppliers, integer INR payments, correlated commerce messages and minimum delivery disclosure. It is inspired by commerce and payment infrastructure, but does not connect to ONDC, UPI or a live bank. The participating simulator supplies an explicit idempotency, status and closure contract. Those guarantees must be re-established before adapting the system to a real provider.",
"problem":"A per-payment budget can preserve the amount while losing the purchase. Two INR700 baskets fit within an INR1500 cap even when the person approved only one rice-and-oil basket. Parallel workers, new request IDs and child agents can repeat that obligation. Merchant text can propose a larger pack, another recipient or unrelated data disclosure without changing the apparent task. A timeout creates a second problem: a payment may have committed even though its response was lost. Treating that uncertainty as failure can authorize a duplicate replacement. Operators, commerce integrators and security evaluators therefore need one shared account of approved demand, pending obligations and actual effects. Approval receipts alone cannot establish that an order or debit occurred.",
"approach":"The operator reviews a canonical purchase containing exact units, allowed equivalents, suppliers, an all-in gross cap, delivery fields and expiry. Human confirmation binds its hash, version and one-use nonce. The server creates demand identities that agents cannot regenerate by changing transport IDs. Agent grants bind actor, audience, parent, scope, expiry and current authority epoch. Preparing a proposal creates an immutable preview without reserving funds. Committing locks the purchase root and atomically checks authority, money, item quantities and purchase count before reserving capacity and writing an outbox entry. The worker marks dispatch durably before sending stored effect bytes under a stable provider identity and fence. Confirmed, reserved, unknown and closed exposure occupy disjoint buckets. Lost responses and process death retain obligations until terminal evidence supports settlement or closure. Explicitly allowed alternatives can proceed after eligible predecessor closure; uncertainty does not create replacement rights. Separate synthetic commerce, payment and egress records establish what happened. A standard-library checker reconstructs quantities, gross captures, disclosure scope and completion without importing runtime admission predicates. The console presents approved scope, current obligations and actual outcomes together.",
"threat":"The attacker can control seller prose, memory summaries, correlated callback bodies and agent tool arguments. They know the public prompts and implementation, change request or worker identities, create concurrent calls and seek a second basket within the money cap. A valid merchant identity proves the source of a message but does not authorize different quantities, payees, SKUs or disclosure. The model, its summaries and its success claims are untrusted. Trusted roots are the operator's reviewed approval and session, scoped issuer, merchant registry, transactional database, gateway, worker and participating effect services. Service, issuer and observer credentials remain outside agent processes and browser bundles. Private effect routes refuse agent credentials. Human approval routes refuse agent roles, and tenant-scoped lookups hide unrelated records. Revocation is ordered with new admission and does not imply retroactive cancellation of a previously dispatched effect. The simulator's provider profiles distinguish stable-key dedupe, queryable effects without a repeat-send guarantee and opaque outcomes. Physical fulfillment, compromised trusted roots, general product equivalence and genuine bank settlement are outside the executable boundary. Whole-export replacement by a compromised trusted observer is also outside the hash-chain claim.",
"evaluation":"The frozen conformance campaign executes 24 authored families across three provider profiles, two role topologies and five matched controls, producing 720 cells. Controls share the same provider behavior and retain exact binding and provider idempotency where applicable. The strong payment control also uses atomic cumulative money admission. Each cell retains attempts, refusals, errors, independent effect records and an immutable manifest. The offline checker scores money, quantities, disclosure and truthful completion. Separate tests exercise real multi-process contention, process exit after dispatch, restart reconciliation, isolation and corrupt evidence. A separately frozen live study uses twelve tasks, two small local models, five seeds and ordinary/attacked text: 240 model invocations, each replayed against two controls. Those 480 matched replays are not independent model samples. Exploratory protocol results and final revisions remain separate, with failures retained.",
"novelty":"The contribution is an executable purchase profile that joins trusted demand identity, quantities, gross money and uncertainty across agent delegation, together with independent effect reconstruction and a reproducible comparative lab. Capabilities, signed authorization, transactional reservations, idempotency and recovery have established antecedents; AP2, Grantex and relevant agent-security literature are acknowledged. The authored controls do not imply a vendor vulnerability.",
"adoption":"An integrator first registers exact catalog and supplier identities, then routes consequential calls through the typed proposal/prepare/commit boundary. The local stack and model-free planner provide a credential-free adoption path. Before real rails, an adapter must establish immutable checkout binding, participating-sink mediation, dedupe retention, trustworthy status and terminal closure behavior. The offline AP2 projection remains a narrowly tested compatibility preview, while P3P UAT awaits an authorized sandbox account.",
"limits":"Results cover an authored finite catalog and owned synthetic infrastructure. The effect service atomically commits order, payment and disclosure, which simplifies joint-state recovery compared with independently settling real systems. Opaque outcomes may remain unresolved and reduce useful completion. The local models are small Qwen models, so their behavior does not establish frontier-agent performance. Hashes provide tamper evidence, not provider signatures or protection against replacement of all trusted source evidence. Local self-service sessions, sample keys and HTTP configuration require deployment hardening before public hosting. The report records observed latency and its exact boundary rather than claiming a production SLA.",
"reflection":"The hardest problem was defining when a purchase right is consumed. An authorization decision and an actual debit are different facts, and a missing response belongs to neither success nor proven failure. We therefore separated immutable preparation, atomic reservation, durable dispatch, uncertain exposure and evidence-backed settlement. This made recovery more conservative, but it preserved the original purchase while a provider outcome was unresolved. Concurrency also changed the design. A per-statement store could let two workers read the same remaining budget. The new ledger serializes the entire admission against the trusted root and reserves money and quantities together. Tests use actual PostgreSQL processes rather than relying on a Python lock. Independent validation exposed a further subtlety: one captured order whose runtime status remained unknown was initially counted twice by the checker. We corrected the accounting and retained the failing preflight. Repeated service startup exposed an unnecessary DDL-lock race, so applied migrations now avoid replaying schema changes against live purchases. We also tightened catalog ownership, adapter identity and checkout arithmetic. The first small-model study showed that ungrounded identifier strings damaged useful completion even when enforcement remained safe. A revised finite tool schema and fresh seeds separate that integration improvement from the original results. Finally, container artifact capture required binary streaming because Docker Desktop could not copy the tmpfs outputs directly. These difficulties reinforced the same principle: evaluate actual effects and explicit state transitions rather than a convincing success narrative.",
}
LIMITS={"summary":(1,25),"website":(60,100),"dpi":(80,150),"problem":(100,150),"approach":(150,250),"threat":(150,250),"evaluation":(100,200),"limits":(80,150),"reflection":(200,300)}


def main():
    for key,(low,high) in LIMITS.items():
        count=len(TEXT[key].split())
        if not low<=count<=high:raise ValueError((key,count,low,high))
    campaign=json.loads((DATA/"final/campaign/summary.json").read_text())
    live=json.loads((DATA/"final/live-study/summary.json").read_text())
    perf=json.loads((DATA/"http-rehearsal-performance.json").read_text())["performance"]
    release=json.loads((DATA/"release-summary.json").read_text())
    OUT.mkdir(parents=True,exist_ok=True)
    navy=colors.HexColor("#143C68");muted=colors.HexColor("#4C647A");light=colors.HexColor("#EDF4FA")
    body=ParagraphStyle("body",fontName="Helvetica",fontSize=9.8,leading=13.5,textColor=colors.HexColor("#183047"),spaceAfter=10)
    h1=ParagraphStyle("h1",parent=body,fontName="Helvetica-Bold",fontSize=17,leading=21,spaceBefore=8,spaceAfter=15,textColor=navy,keepWithNext=True)
    h2=ParagraphStyle("h2",parent=body,fontName="Helvetica-Bold",fontSize=11.5,leading=15,spaceBefore=10,spaceAfter=8,textColor=navy,keepWithNext=True)
    small=ParagraphStyle("small",parent=body,fontSize=8,leading=10.5,textColor=muted)
    title=ParagraphStyle("title",parent=body,fontName="Times-Roman",fontSize=37,leading=42,textColor=navy,spaceAfter=10)
    story=[];md=[]
    def p(text,style=body):story.append(Paragraph(escape(str(text)).replace("\n","<br/>"),style))
    def heading(text,level=1):story.append(Paragraph(escape(text),h1 if level==1 else h2));md.append(("## " if level==1 else "### ")+text+"\n")
    def paragraph(key):p(TEXT[key]);md.append(TEXT[key]+"\n")
    def table(rows,widths,header=True):
        data=[[Paragraph(escape(str(v)),small if i else small) for v in row] for i,row in enumerate(rows)]
        t=Table(data,colWidths=widths,repeatRows=1 if header else 0,hAlign="LEFT")
        rules=[("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),("LINEBELOW",(0,0),(-1,-1),.3,colors.HexColor("#D8E4EE"))]
        if header:rules.append(("BACKGROUND",(0,0),(-1,0),light))
        t.setStyle(TableStyle(rules));story.append(t);story.append(Spacer(1,12))
    def page():story.append(PageBreak())
    p("Assever",title);p("Purchase integrity for AI agents",h2);p("SAFL India AI Agentic Hackathon | Technical-track submission draft | 31 October 2026",small)
    p("Owner completion required: registered team/contact details, exact participation choices, factual declarations, individual permissions and public links. Video and deployment are excluded from this implementation request.",small)
    heading("1-3 Team, members and participation")
    table([["Required field","Owner input"],["Registered team name / primary contact","To be completed by registered team"],["Contact email / phone / affiliation","To be completed by contact owner"],["One to three registered members","Names, emails and affiliations pending owner input"],["Participation mode / track / challenge","Prepared for Technical / System Resilience; owner verifies registration"]],[165,342])
    heading("4 Project title and public description")
    p("Assever: Purchase integrity for AI agents",h2);paragraph("summary");paragraph("website")
    page();heading("5 DPI assumption and affected problem");heading("Assumed workflow",2);paragraph("dpi");heading("Problem",2);paragraph("problem")
    drawing=Drawing(507,135)
    labels=[("Operator / agents",8,90),("Purchase API",182,90),("Ledger + outbox",356,90),("Worker",182,22),("Private effect store",356,22),("Observer + checker",8,22)]
    for label,x,y in labels:
        drawing.add(Rect(x,y,143,32,fillColor=light,strokeColor=colors.HexColor("#B8CADD"),rx=4,ry=4))
        drawing.add(String(x+8,y+12,label,fontName="Helvetica",fontSize=9,fillColor=navy))
    for x1,y1,x2,y2 in [(151,106,182,106),(325,106,356,106),(253,90,253,54),(325,38,356,38),(427,22,427,8),(427,8,80,8),(80,8,80,22)]:drawing.add(Line(x1,y1,x2,y2,strokeColor=navy,strokeWidth=1))
    story.append(drawing);p("The observer captures actual effects separately. The runtime never borrows hidden observer truth to resolve opaque outcomes.",small)
    page();heading("6 System and research approach");heading("Approach",2);paragraph("approach");heading("Threat model",2);paragraph("threat")
    page();heading("6 Evaluation, findings and contribution");paragraph("evaluation")
    rows=[["Authored control","Cells","Unsafe / FAIL","Unresolved","Task complete","Errors"]]
    for control in ["unrestricted","permission","payment","conservative","adaptive"]:
        r=campaign["controls"][control];rows.append([control,r["cells"],r["verdicts"].get("FAIL",0),r["verdicts"].get("INCOMPLETE",0),r["completed_tasks"],r["errors"]])
    table(rows,[122,45,85,75,95,45])
    measured=[f"Conformance: {campaign['cells']} scored cells. Adaptive enforcement has {campaign['controls']['adaptive']['verdicts'].get('FAIL',0)} unsafe-effect verdicts, with unresolved outcomes reported separately.",f"Database/process regression: {release['purchase_tests']} tests pass; eight-process, 100-attempt admission admits one full basket and refuses 99 duplicate claims.",f"Live protocol v2: {live['actual_invocations']} model invocations; {live['errors']} invocation/execution errors retained. Adaptive replay has {live['per_control']['adaptive']['unsafe_effects']} unsafe-effect verdicts and completes 228/240 tasks: 120/120 ordinary and 108/120 attacked. Payment-only replay produces 67 unsafe outcomes across the same 240 proposals."]
    for value in measured:p("- "+value);md.append("- "+value+"\n")
    p("Live and deterministic denominators are separate. The exploratory first live protocol is retained; final results use the revised finite tool schema and a newly frozen seed set.",small)
    page();heading("6 Contribution, adoption and limitations");heading("Novelty",2);paragraph("novelty");heading("Adoption",2);paragraph("adoption");heading("Limitations",2);paragraph("limits")
    page();heading("7 Difficulty and resolution");paragraph("reflection")
    for line in ["Reserve money, normalized item units and purchase count in one root transaction.","Retain uncertain obligations; reconcile from profile-qualified evidence and terminal closure.","Validate final quote arithmetic, supplier ownership and immutable adapter identity.","Keep failed preflights, model errors, matched controls and independent exports inspectable."]:p("- "+line)
    heading("8 Outputs, development and assistance")
    p("Deliverables: local Docker product; strict API/OpenAPI; typed agent client; canonical contract/catalog; durable ledger/outbox; private effect simulator; safety-lab corpus; independent checker; raw campaign and live-study records; mechanism comparisons; setup/operations/architecture guides; backlog with evidence; this report draft. Video, deployment and publication are excluded from this request.")
    p("Technical implementation, testing and artifact preparation in this workspace: 31 October 2026. The registered team must verify its complete development timeline and participation declarations. Existing license/copyright notices are preserved. Codex assisted planning, implementation, tests and documentation; the exact serving identifier was not exposed beyond the GPT-6 family. Runtime live-study model IDs/digests are in the manifests. Third-party library/model licenses and the assistance record are listed in ATTRIBUTION.md.")
    page();heading("9 Responsible testing and environment")
    p("All buyers, suppliers, addresses, funds and records are synthetic. Testing targets only the owned local simulators and localhost application. No production commerce network, bank settlement, private competitor service or external customer data is involved. Callback and content attacks are authored fixtures. No public-vulnerability claim or disclosure is made from these controls. Effect routes are private, agent credentials cannot invoke them, and each browser visitor has a separate tenant. Source archives exclude environment secrets, local session stores, database backups and downloaded model weights.")
    p("Environment: Python 3.11 image, FastAPI/Pydantic, PostgreSQL 16.4, React/TypeScript/Vite and local Ollama 0.40.13. Docker host: eight CPUs and approximately 16 GB RAM. Admission tests and real process-exit/recovery run in containers. Browser journeys are checked at desktop and mobile widths. Backup/restore compares source and restored table fingerprints.")
    timing=perf.get("core_admission_ms",{})
    p(f"Measured twenty-client latency: core transaction p95 {timing.get('p95','not captured')} ms; end-to-end HTTP p95 {perf['p95_ms']} ms. Provider readiness, transport and core admission are recorded separately. The exact PRD 4-CPU/8-GB host target is not inferred from this larger Docker host.",small)
    heading("10 Individual publication permissions")
    table([["Member","Publication / media / contact choices"],["Member 1","Pending this member's explicit selections"],["Member 2, if registered","Pending this member's explicit selections"],["Member 3, if registered","Pending this member's explicit selections"]],[155,352])
    p("No permission is inferred. The owner completes factual registration fields, public URLs and individual choices, then renames the final report to TeamName_Report.pdf and submits one authorized entry. This draft has not been submitted or published.",small)
    heading("Evidence and sources",2)
    refs=["Official event and judging rubric: https://secureaifutureslab.com/events/india-ai-agentic-hackathon","Supplied SAFL_Submission_Template.docx, sections 1-10; concept note linked in the PRD.","AP2 v0.2: github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/specification.md","Grantex shared wallet governance: docs.grantex.dev/guides/agent-wallet-governance","Actual results: release evidence final/campaign, final/live-study, ablations, test logs and portable checker bundles."]
    for ref in refs:p(ref,small)
    def footer(canvas,doc):
        canvas.setStrokeColor(colors.HexColor("#D8E4EE"));canvas.line(44,40,A4[0]-44,40)
        canvas.setFont("Helvetica",8);canvas.setFillColor(muted);canvas.drawString(44,27,"Assever | Synthetic purchase-integrity research | Owner-completion draft");canvas.drawRightString(A4[0]-44,27,str(doc.page))
    doc=SimpleDocTemplate(str(OUT/"Assever_Report_Draft.pdf"),pagesize=A4,leftMargin=44,rightMargin=44,topMargin=43,bottomMargin=53,title="Assever - SAFL submission draft",author="Assever team; owner details pending")
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    (OUT/"Assever_Report_Content.md").write_text("# Assever submission content\n\n"+"\n".join(md)+"\n\nOwner-controlled sections are in the PDF draft and release checklist.\n",encoding="utf-8")
    (OUT/"Report_Word_Counts.json").write_text(json.dumps({k:{"words":len(TEXT[k].split()),"min":a,"max":b} for k,(a,b) in LIMITS.items()},indent=2),encoding="utf-8")
    print(OUT/"Assever_Report_Draft.pdf")


if __name__=="__main__":main()
