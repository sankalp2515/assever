"""Render the corrected target design in the existing Assever architecture's style.

Documentation only: this does not change the application or deployment.
"""

from html import escape
from pathlib import Path
import textwrap
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/assever/integrated-design"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 3600, 2240
ink, subtle, green, blue, amber = "#101826", "#586475", "#1D5E46", "#1855D8", "#8A5D00"
parts = [
    f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">Assever: agent governance and purchase integrity</title>
<desc id="desc">Target architecture retaining Assever's console, gateway, core, SDK and managed-service boundaries. Extend annotations identify upgrades to existing components. New annotations identify purchase accounting and projections inside the core, a separate execution worker, and isolated evaluation infrastructure. This integration is proposed, not yet validated.</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{green}"/></marker><marker id="gray" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{subtle}"/></marker></defs>
<style>text{{font-family:'Segoe UI',Arial,sans-serif;fill:{ink}}}.mono{{font-family:Consolas,'Courier New',monospace}}.section{{font-weight:700;letter-spacing:2px;fill:{subtle}}}</style>
<rect width="3600" height="2240" fill="#F3F4F1"/>'''
]


def text(x, y, value, size=26, fill=ink, weight="400", cls=""):
    parts.append(
        f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" style="fill:{fill}" class="{cls}">{escape(value)}</text>'
    )


def para(x, y, value, width, size=25, fill=subtle, line=34):
    lines = textwrap.wrap(value, width=max(10, int(width / (size * 0.52))))
    for i, value in enumerate(lines):
        text(x, y + i * line, value, size, fill)
    return y + len(lines) * line


def box(x, y, w, h, title, body, state="KEEP", footer="", number=None, emphasis=False):
    bg = "#E5F0EA" if emphasis else "#FFFFFF"
    stroke = green if emphasis else "#D4DAE2"
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{bg}" stroke="{stroke}" stroke-width="{3 if emphasis else 2}"/>'
    )
    if number:
        parts.append(f'<circle cx="{x}" cy="{y + 43}" r="26" fill="{green if emphasis else ink}"/>')
        text(x - 8, y + 53, str(number), 27, "#FFFFFF", "700")
    color, chipbg = {"KEEP": (green, "#E5F0EA"), "EXTEND": (amber, "#FBF3DF"), "NEW": (blue, "#E8EFFF")}[state]
    chipw = 118 if state == "EXTEND" else 88
    title_size = min(31, (w - chipw - 80) / (len(title) * 0.54))
    text(x + 30, y + 49, title, title_size, weight="700")
    parts.append(f'<rect x="{x + w - chipw - 24}" y="{y + 17}" width="{chipw}" height="31" rx="6" fill="{chipbg}"/>')
    text(x + w - chipw - 13, y + 40, state, 19, color, "700", "mono")
    size = 23 if w < 900 else 25
    while True:
        line = size + 8
        count = len(textwrap.wrap(body, width=int((w - 60) / (size * 0.52))))
        if y + 87 + (count - 1) * line <= y + h - (44 if footer else 20):
            break
        size -= 1
        assert size >= 19, (title, "insufficient space")
    end = para(x + 30, y + 87, body, w - 60, size, line=line) - line
    if footer:
        footer_size = min(20, (w - 60) / (len(footer) * 0.53))
        text(x + 30, y + h - 22, footer, footer_size, green)
    assert end <= y + h - (44 if footer else 20), (title, end, y + h)


def arrow(path, label="", x=0, y=0, dashed=False, gray=False):
    color = subtle if gray else green
    parts.append(
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round" {"stroke-dasharray=" + chr(34) + "8 7" + chr(34) if dashed else ""} marker-end="url(#{"gray" if gray else "arrow"})"/>'
    )
    if label:
        text(x, y, label, 21, color, cls="mono")


text(48, 61, "Assever", 43, green, "700")
text(248, 60, "Assever runtime · integrated target architecture", 31, weight="600")
text(
    48,
    105,
    "Same product, console, gateway, core and SDK. Purchase integrity becomes an additional governed workflow.",
    26,
    subtle,
)
for x, state, color in [
    (48, "KEEP · existing boundary / capability", green),
    (670, "EXTEND · modify the existing component", amber),
    (1375, "NEW · integrate the added capability", blue),
]:
    text(x, 155, state, 23, color, "600", "mono")
text(2380, 155, "DESIGN FOR CORRECTION · integration not yet verified", 22, subtle, cls="mono")

# Four columns and cloud boundary mirror docs/architecture.png.
parts.append(
    '<rect x="740" y="205" width="2140" height="1680" rx="35" fill="#F0F4F6" stroke="#98B5FF" stroke-width="4" stroke-dasharray="12 10"/>'
)
text(788, 237, "GOOGLE CLOUD · existing service boundaries retained", 25, "#487BEB", "700")
text(48, 245, "PEOPLE · SAME CONSOLE", 27, cls="section")
text(2935, 245, "YOUR BUSINESS", 27, cls="section")
parts.append(f'<rect x="790" y="269" width="1390" height="1575" rx="30" fill="#FFFFFF" stroke="{green}" stroke-width="4"/>')
text(825, 319, "Assever checkpoint · existing Assever gateway", 34, weight="700")
text(825, 353, "services/gateway + packages/core · one authority boundary", 23, green, cls="mono")
text(2230, 290, "MANAGED / PRIVATE SERVICES", 24, cls="section")

box(
    48,
    280,
    580,
    225,
    "Employee",
    "Keeps Tasks, Needs you and Receipts. Reviews one work order; sees approved scope, pending obligations and verified outcomes in the same task.",
    "EXTEND",
    footer="Human confirms · agents never approve",
)
box(
    48,
    527,
    580,
    195,
    "Security team",
    "Keeps Activity, review, replay and Evaluation. Adds linked order/payment/disclosure evidence and export verification.",
    "EXTEND",
)
text(48, 790, "AI AGENTS · OUTSIDE CHECKPOINT", 25, cls="section")
box(
    48,
    823,
    580,
    205,
    "Gemini agents · Google ADK",
    "Retain Reader → Resolver team and live agents. Procurement adds planner / buyer roles; alternatives stay within the reviewed work order.",
    "EXTEND",
)
box(
    48,
    1050,
    580,
    205,
    "Your agents · same SDK / REST",
    "Keep ADK callbacks and remote clients. A purchase proposal returns an operation ID; callers poll status instead of reporting payment success.",
    "EXTEND",
    footer="Agent key: can propose, never approve",
)
box(
    48,
    1277,
    580,
    180,
    "Untrusted content",
    "Tickets, PDFs, invoices, seller messages, memory and callbacks remain data. None can amend the employee’s work order.",
    "KEEP",
)
box(
    48,
    1480,
    580,
    240,
    "Same information architecture",
    "Tasks: purchase detail within a work order. Needs you: exact exceptions. Activity: effects and investigation. Connect: existing agents, businesses and adapter setup.",
    "EXTEND",
    footer="Same design tokens, stamps and navigation",
)

box(
    825,
    390,
    1320,
    178,
    "Work-order compiler + grounded review",
    "Retain grounded MAY / NEVER clauses and human confirmation. Add a typed purchase annex: demand IDs, units, alternatives, suppliers, all-in cap, delivery fields and expiry.",
    "EXTEND",
    number=1,
    footer="One workflow ID · one owner · one reviewed contract version",
)
box(
    825,
    585,
    1320,
    145,
    "Read screening",
    "Keep rules, local classifier, provenance/taint tracking and optional Model Armor. Purchase content passes through the same read boundary.",
    "KEEP",
    number=2,
)
box(
    825,
    747,
    1320,
    145,
    "Sealed handoffs",
    "Keep HMAC-sealed workflow provenance. Add recipient/audience/expiry-bound, attenuated grants; child agents share the same root quantities and budget.",
    "EXTEND",
    number=3,
)
box(
    825,
    909,
    1320,
    213,
    "Action gate · existing deterministic enforcement point",
    "Keep recipient, record, field and content-tracing checks. Purchase calls additionally validate the final checkout and atomically reserve root money, quantities and purchase count before queueing execution.",
    "EXTEND",
    number=4,
    emphasis=True,
    footer="Read/draft stay local · STOPPED: refused · WAITS: approval · ADMITTED: queued, not yet RAN",
)
box(
    825,
    1139,
    1320,
    155,
    "Bound approvals + lifecycle",
    "Keep owner-only exact, single-use, expiring approvals. Bind purchase exceptions to old/new scope and checkout bytes. Narrowing or revocation changes the root epoch for future admissions.",
    "EXTEND",
    number=5,
)
box(
    825,
    1311,
    1320,
    174,
    "Proof · existing receipts + actual outcomes",
    "Keep chained receipts, source-linked explanations and citation-checked reports. Link durable operation IDs to provider observations; unknown stays unknown until supported by evidence.",
    "EXTEND",
    number=6,
    footer="RAN only after a verified effect · no agent self-attestation of payment success",
)
box(
    825,
    1507,
    640,
    278,
    "N1 · Root entitlement ledger",
    "New core module, stored in the existing PostgreSQL service. Integer money / units; shared demand IDs; locked admission; disjoint reserved / unknown / captured / closed buckets.",
    "NEW",
    footer="One transaction: root checks + reservation + outbox",
)
box(
    1485,
    1507,
    660,
    278,
    "N2 · Consequence projection",
    "New typed core / adapter interface. Binds final quote, seller/payee, quantities, fees, disclosures, adapter version and exact request digest. Unsupported effects are refused.",
    "NEW",
    footer="An LLM proposes; deterministic code decides",
)

box(
    2230,
    330,
    590,
    180,
    "Vertex AI · Gemini / ADK",
    "Keep compiler, agent team, explanations and receipt roles. Models do not sign authority or settle accounting.",
    "KEEP",
)
box(
    2230,
    530,
    590,
    145,
    "Model Armor",
    "Retain optional screening. Content detection adds a layer; enforcement still checks actions.",
    "KEEP",
)
box(
    2230,
    695,
    590,
    200,
    "PostgreSQL · same service",
    "Retain work orders, approvals and receipts. Add purchase roots, grants, reservations, operation bindings and transactional outbox via versioned migrations.",
    "EXTEND",
)
box(
    2230,
    925,
    590,
    275,
    "N3 · Execution / recovery",
    "New worker container; no second public app. Claims the durable outbox, uses stable operation IDs and provider credentials, reconciles before any retry; preserves unknown exposure.",
    "NEW",
    footer="Worker reaches participating tools · private network",
)
box(
    2230,
    1222,
    590,
    205,
    "Audit · IAM · build pipeline",
    "Keep BigQuery receipt streaming, Secret Manager/IAM and existing image/build boundaries. Add effect joins, worker roles and health/queue metrics.",
    "EXTEND",
)
box(
    2230,
    1449,
    590,
    330,
    "N4 · Independent verifier",
    "Isolated evaluator reads read-only provider observations and approved scope. Reconstructs money, units and disclosure effects; exports a standard-library checker. Extend the existing Evaluation surface with the shared corpus and matched controls.",
    "NEW",
    footer="Provider truth for evaluation ≠ authority for recovery",
)

box(
    2935,
    280,
    615,
    260,
    "Business tools · same integrations",
    "Retain email, refunds, invoices, records and files. Purchase-capable adapters gain a private executor path and typed consequence projection. Only the executor holds purchase/provider credentials.",
    "EXTEND",
    footer="No direct agent route to consequential purchase APIs",
)
box(
    2935,
    595,
    615,
    240,
    "N5 · Owned DPI test adapters",
    "Separate synthetic commerce, payment and disclosure records. ONDC/Beckn-inspired message subset; UPI-style INR effects. Queryable, deduplicating and opaque provider profiles.",
    "NEW",
    footer="Test service only · no live DPI / money / personal data",
)
box(
    2935,
    857,
    615,
    190,
    "Business policy",
    "Keep tools, contacts, records and company rules. Add trusted catalog units, merchant/payee mapping, allowed delivery fields and adapter capabilities.",
    "EXTEND",
)
text(2935, 1110, "WHAT THIS ADDS TO ABIDE", 25, cls="section")
box(
    2935,
    1140,
    615,
    180,
    "Preserve the whole purchase",
    "Two ₹700 baskets fit ₹1,500. Shared demand accounting admits one approved basket, not two purchases with different request IDs.",
    "NEW",
)
box(
    2935,
    1342,
    615,
    180,
    "Keep useful work moving",
    "Allow reviewed alternatives when stock changes. A hidden instruction still cannot change destination, units, supplier scope or data sharing.",
    "NEW",
)
box(
    2935,
    1544,
    615,
    235,
    "Recover without inventing success",
    "A lost response does not free the budget or trigger a blind resend. Reconcile actual effects; retain unknown exposure for opaque providers.",
    "NEW",
    footer="Revocation stops new admissions, not past effects",
)

# Routing corridors keep arrows off component text.
arrow("M633 385H700V478H816", "words + review", 643, 366, gray=True)
arrow("M633 927H690V1015H816", "tool proposal", 640, 995)
arrow("M633 1175H690V1015", gray=False)
arrow("M633 1365H658V657H816", dashed=True, gray=True)
text(650, 805, "read", 20, subtle, cls="mono")
arrow("M2145 1008H2221", "outbox", 2152, 985)
arrow("M2820 1030H2895V408H2926")
text(2840, 570, "effects", 20, green, cls="mono")
arrow("M2927 720H2895V1610H2829", dashed=True, gray=True)
text(2840, 1582, "observe", 18, subtle, cls="mono")
arrow("M2230 1580H2199V1396H2154", dashed=True, gray=True)

text(48, 1900, "THE DEMONSTRATION · ONE EXISTING TASK, FOUR PRESSURES", 25, cls="section")
for x, title, body in [
    (48, "01 · Hidden instruction", "Existing filter + action gate stop the off-order call and retain its source."),
    (935, "02 · Concurrent purchase", "New atomic root ledger stops a second basket even when the money cap fits."),
    (1822, "03 · Response loss", "New worker reconciles; pending exposure remains reserved until evidence resolves it."),
    (2709, "04 · Approved adaptation", "Agents choose a permitted alternative; receipts show what actually finished."),
]:
    box(x, 1930, 843, 175, title, body, "KEEP" if x == 48 else "NEW")
text(48, 2150, "SUBMISSION FOCUS", 22, green, "700", "mono")
text(355, 2150, "System Resilience · Trust & Consent · Accountability · legible English/Hindi purchase fields", 25)
text(
    48,
    2195,
    "Target design only. Existing purchase test results are component evidence; the integrated Assever → Assever product requires fresh end-to-end validation.",
    24,
    subtle,
)
parts.append("</svg>")
svg = "\n".join(parts)
name = "Assever_Integrated_Architecture"
if "--implemented" in sys.argv:
    name = "Assever_Local_Architecture"
    for before, after in {
        "Target architecture retaining Assever's console, gateway, core, SDK and managed-service boundaries.": "Implemented local architecture retaining Assever's console, gateway, core and SDK boundaries.",
        "This integration is proposed, not yet validated.": "See current release status for local verification and remaining qualification gates.",
        "Keep compiler, agent team, explanations and": "Local Qwen via private Ollama. Existing Vertex",
        "receipt roles. Models do not sign authority": "AI / ADK adapters remain optional. Model",
        "or settle accounting.": "outputs never grant authority or settle money.",
        "Keep BigQuery receipt streaming, Secret": "Optional: BigQuery receipt streaming, Secret",
        "Assever runtime · integrated target architecture": "Assever runtime · integrated local architecture",
        "DESIGN FOR CORRECTION · integration not yet verified": "LOCAL DOCKER · original gateway + integrated purchase profile",
        "GOOGLE CLOUD · existing service boundaries retained": "LOCAL DOCKER · existing service boundaries retained",
        "Target design only. Existing purchase test results are component evidence; the integrated Assever → Assever product requires fresh end-to-end validation.": "Integrated local release. See INTEGRATED_RELEASE_STATUS.md for verification, exact denominators, qualification gaps and cloud exclusions.",
        "New core module, stored in the existing": "Core module, stored in the existing",
        "New typed core / adapter interface.": "Typed core / adapter interface.",
        "New worker container; no second public app.": "Private worker container; same public gateway.",
        "Isolated evaluator reads read-only provider observations": "Private evaluator reads read-only provider observations",
        "Vertex AI · Gemini / ADK": "Vertex AI · Gemini / ADK (optional)",
        "Keep compiler, agent team, explanations and receipt roles. Models do not sign authority or settle accounting.": "Cloud integrations retained; local default uses explicit deterministic roles. Optional Qwen proposals remain untrusted.",
        "Model Armor</text>": "Model Armor (optional)</text>",
        "Retain optional screening. Content detection adds a layer; enforcement still checks actions.": "Existing integration retained for later configuration. Local rule / classifier screening remains active.",
    }.items():
        svg = svg.replace(before, after)
if "--google" in sys.argv:
    name = "Assever_Google_Architecture"
    for before, after in {
        "integrated local architecture": "deployed Google Cloud architecture",
        "Implemented local architecture": "Deployed Google Cloud architecture",
        "LOCAL DOCKER · original gateway + integrated purchase profile": "GOOGLE CLOUD · HTTPS edge + private Docker runtime",
        "LOCAL DOCKER · existing service boundaries retained": "GOOGLE CLOUD · existing service boundaries retained",
        "Vertex AI · Gemini / ADK (optional)": "Gemini · Gen AI SDK / ADK",
        "Model providers · optional": "Gemini · Gen AI SDK / ADK",
        "Local Qwen via private Ollama. Existing Vertex": "Vertex Gemini via runtime identity. Gen AI SDK",
        "AI / ADK adapters remain optional. Model": "and Google ADK drive live agents. Model",
        "Model Armor (optional)": "Model Armor · connected",
        "Optional: BigQuery receipt streaming, Secret": "BigQuery receipts, Secret Manager / runtime",
        "Manager/IAM and existing image/build": "IAM and digest-pinned application images.",
        "boundaries. Add effect joins, worker roles": "Effect joins, private worker roles",
        "Integrated local release. See INTEGRATED_RELEASE_STATUS.md for verification, exact denominators, qualification gaps and cloud exclusions.": "Deployed Google Cloud evaluation. See GOOGLE_CLOUD_VALIDATION.md for exact results, source digests and qualification boundaries.",
    }.items():
        svg=svg.replace(before,after)
(OUT / (name + ".svg")).write_text(svg, encoding="utf-8")
(OUT / (name + ".html")).write_text(
    '<!doctype html><html lang="en"><meta charset="utf-8"><title>Assever integrated architecture</title><style>html,body{margin:0;background:#F3F4F1}svg{display:block;width:3600px;height:2240px}</style>'
    + svg
    + "</html>",
    encoding="utf-8",
)
print(OUT / (name + ".svg"))
