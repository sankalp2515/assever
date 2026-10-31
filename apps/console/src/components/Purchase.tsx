import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { call, tasks, type DState, type DReport } from "../api";
import { useEmployee } from "../employee";
import { ErrorNote, Stamp } from "./ui";

type Scope = { max_paise: number; max_purchases: number; currency: string; merchants: string[]; delivery_ref: string;
  disclosure_fields: string[]; expires_at: number; lines: Record<string, { max_units: number; unit: string; skus: string[] }> };
type Operation = { id: string; state: string; revision: number; effect: { total_paise?: number; [key: string]: unknown } };
type Purchase = { id: string; state: string; version: number; epoch: number; digest: string; scope: Scope;
  business_policy?: { current: boolean; limit_paise: number; profile: string };
  human_confirmation_nonce?: string; money: Record<string, number>; quantities: Record<string, unknown>;
  operations: Operation[]; events: { sequence: number; hash: string; body: { kind: string; details: Record<string, unknown> } }[];
  exceptions: { id: string; state: string; digest: string; expires: number; old_scope: Scope; new_scope: Scope; effect: Record<string, unknown> }[] };
const amount = (paise = 0) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(paise / 100);
const labels: Record<string, string> = { RICE_5KG_A: "Sona rice · 5 kg", RICE_5KG_B: "Equivalent rice · 5 kg", OIL_1L_A: "Sunflower oil · 1 L", OIL_1L_B: "Equivalent oil · 1 L", supplier_a: "Supplier A", supplier_b: "Supplier B", shop_name: "Shop name", delivery_address: "Delivery address" };
const post = <T,>(key: string, path: string, body: unknown = {}) => call<T>(path, { method: "POST", body: JSON.stringify(body) }, key);
const path = (id: string) => `/v1/purchases/contracts/${encodeURIComponent(id)}`;

function describeAttempts(attempts: unknown[]): string {
  const lines = attempts.map((a) => {
    const r = a as { operation_id?: string; admitted?: boolean; refused?: string; message?: string };
    if (r.admitted && r.operation_id) return `Admitted ${r.operation_id}; waiting for provider evidence.`;
    if (r.refused) return `Refused (${r.refused})${r.message ? `: ${r.message}` : "."}`;
    return JSON.stringify(a);
  });
  return lines.length ? `Model proposal processed. ${lines.join(" ")}` : "Model proposal processed; no purchase was proposed.";
}

export function NewPurchase({ apiKey, onCreated }: { apiKey: string; onCreated: (wf: string) => void }) {
  const [words, setWords] = useState("Buy 1 x 5 kg rice and 2 x 1 L oil, up to INR 1500 including fees, from supplier A or supplier B. Share only the shop name and delivery address.");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return <section className="card p-6 space-y-5">
    <div><p className="section-label">New task · purchase</p><h2 className="h2">Put the purchase in writing.</h2>
      <p className="subtle text-sm">Your words stay with this work order. Review every purchase field before the buyer can act. This workspace uses owned ONDC-style supplier and UPI-style payment simulators with synthetic money.</p></div>
    <form className="space-y-4" onSubmit={async e => { e.preventDefault(); setBusy(true); setError(""); try {
      const s = await post<DState>(apiKey, "/v1/delegations", { request: words, owner: "Procurement operator", workspace: "kirana" });
      await post(apiKey, `/v1/delegations/${s.workflow.id}/purchase`); onCreated(s.workflow.id);
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }}>
      <label className="block space-y-2"><span className="text-sm font-semibold">What should your buyer do?</span><textarea className="input words w-full" rows={5} value={words} onChange={e => setWords(e.target.value)} required maxLength={4000} /></label>
      {error && <ErrorNote>{error}</ErrorNote>}
      <button className="pill pill-primary" disabled={busy || !words.trim()}>{busy ? "Preparing the work order…" : "Review purchase work order"}</button>
    </form>
  </section>;
}

function ScopeView({ scope, hindi = false }: { scope: Scope; hindi?: boolean }) {
  return <dl className="grid grid-cols-[minmax(90px,0.4fr)_minmax(0,1fr)] gap-x-4 gap-y-3 text-sm break-words">
    <dt className="subtle">{hindi ? "सामान" : "Items"}</dt><dd>{Object.entries(scope.lines).map(([name, line]) => <div key={name}>{name === "rice" ? "Rice" : "Oil"} · {line.max_units.toLocaleString("en-IN")} {line.unit}<span className="subtle block text-xs">{line.skus.map(s => labels[s] || s).join(" / ")}</span></div>)}</dd>
    <dt className="subtle">{hindi ? "कुल सीमा" : "All-in limit"}</dt><dd className="mono">{amount(scope.max_paise)} · gross, including fees</dd>
    <dt className="subtle">{hindi ? "खरीद" : "Approved purchases"}</dt><dd>{scope.max_purchases}</dd>
    <dt className="subtle">{hindi ? "विक्रेता" : "Suppliers"}</dt><dd>{scope.merchants.map(s => labels[s] || s).join(" / ")}</dd>
    <dt className="subtle">{hindi ? "पता" : "Delivery"}</dt><dd>{scope.delivery_ref} · synthetic shop</dd>
    <dt className="subtle">{hindi ? "साझा जानकारी" : "Share only"}</dt><dd>{scope.disclosure_fields.map(s => labels[s] || s).join(", ")}</dd>
    <dt className="subtle">{hindi ? "समाप्ति" : "Expires"}</dt><dd>{new Date(scope.expires_at * 1000).toLocaleString()}</dd>
  </dl>;
}

export function PurchaseTask({ apiKey, wf, words }: { apiKey: string; wf: string; words: string }) {
  const [p, setP] = useState<Purchase | null>(null);
  const [nonce, setNonce] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [seller, setSeller] = useState("supplier_a");
  const [hindi, setHindi] = useState(false);
  const [cap, setCap] = useState("1500");
  const [bundle, setBundle] = useState<Record<string, unknown> | null>(null);
  const [verdict, setVerdict] = useState("");
  const [model, setModel] = useState("gemini-3.5-flash");
  const [sellerText, setSellerText] = useState("");
  const [notice, setNotice] = useState("");
  const [report, setReport] = useState<DReport | null>(null);
  const load = async () => {
    const next = await call<Purchase>(`/v1/delegations/${encodeURIComponent(wf)}/purchase`, undefined, apiKey);
    setP(next); return next;
  };
  useEffect(() => {
    let alive = true;
    setP(null); setAccepted(false); setError(""); setBundle(null); setVerdict("");
    const refresh = async (initial = false) => { try {
      const next = await call<Purchase>(`/v1/delegations/${encodeURIComponent(wf)}/purchase`, undefined, apiKey);
      if (!alive) return;
      setP(next); setError("");
      if (initial && next.state === "DRAFT") {
        const reviewed = await post<Purchase>(apiKey, `${path(next.id)}/review-nonce`);
        if (alive) { setP(reviewed); setNonce(reviewed.human_confirmation_nonce || ""); setCap(String(reviewed.scope.max_paise / 100)); }
      }
    } catch (e) { if (alive) setError((e as Error).message); } };
    void refresh(true); const timer = setInterval(() => { if (!document.hidden) void refresh(); }, 1500);
    return () => { alive = false; clearInterval(timer); };
  }, [wf, apiKey]);
  async function act(fn: () => Promise<unknown>) { setBusy(true); setError(""); setNotice(""); try { await fn(); await load(); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  if (!p) return error ? <ErrorNote>{error}</ErrorNote> : <p role="status" className="subtle">Opening purchase work order…</p>;
  return <div className="space-y-6">
    <div className="flex items-center justify-between gap-3"><span className="section-label">Purchase · {wf}</span><button className="pill pill-sm" onClick={() => setHindi(!hindi)}>{hindi ? "English" : "हिन्दी"}</button></div>
    {error && <ErrorNote>{error}</ErrorNote>}{notice && <p role="status" className="card p-4 text-sm">{notice}</p>}
    <section className="card p-6 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="h2">{p.state === "DRAFT" ? "Check the work order" : "Your approved purchase"}</h2><Stamp kind={p.state === "DRAFT" ? "wait" : p.state === "REVOKED" ? "stopped" : "quiet"}>{p.state === "ACTIVE" ? "Approved" : p.state === "DRAFT" ? "Waits for you" : "Stopped"}</Stamp></div>
      <p className="words text-lg">“{words}”</p><ScopeView scope={p.scope} hindi={hindi} />
      {p.business_policy && <p className="text-sm subtle">Business policy ceiling: <span className="mono">{amount(p.business_policy.limit_paise)}</span>. {p.business_policy.current ? "This annex is bound to the registered procurement policy." : "The business policy changed or this older annex needs review. New admissions are stopped."}</p>}
      <p className="mono subtle break-all">Purchase v{p.version} · {p.digest}</p>
      {p.state === "DRAFT" && <div className="space-y-4 border-t pt-4" style={{ borderColor: "var(--line)" }}>
        <label className="flex flex-col gap-2 text-sm">All-in budget (INR)<input className="input max-w-48" type="number" min="1" max="100000" step="0.01" value={cap} onChange={e => { setCap(e.target.value); setAccepted(false); }} /></label>
        {Number(cap) * 100 !== p.scope.max_paise && <button className="pill" disabled={busy} onClick={() => act(async () => {
          const next = await post<Purchase>(apiKey, `${path(p.id)}/edit`, { expected_version: p.version, scope: { ...p.scope, max_paise: Math.round(Number(cap) * 100) } }); setP(next); setNonce(next.human_confirmation_nonce || ""); setAccepted(false);
        })}>Update budget for review</button>}
        <label className="flex items-start gap-3 text-sm"><input className="mt-1" type="checkbox" checked={accepted} onChange={e => setAccepted(e.target.checked)} />I reviewed the items, units, alternatives, suppliers, gross budget, delivery fields and expiry shown above.</label>
        <button className="pill pill-primary" disabled={busy || !accepted || !nonce || Number(cap) * 100 !== p.scope.max_paise} onClick={() => act(() => post(apiKey, `${path(p.id)}/approve`, { version: p.version, hash: p.digest, accepted_fields: p.scope, human_confirmation_nonce: nonce }))}>{busy ? "Confirming…" : "Confirm this work order"}</button>
      </div>}
    </section>
    <div className="grid gap-4 sm:grid-cols-2">
      <section className="card p-5 space-y-3"><h3 className="h3">Pending obligations</h3><p className="text-sm subtle">Uncertain work keeps its allowance until evidence resolves it.</p><p className="mono">Reserved {amount(p.money.reserved)} · Unknown {amount(p.money.unknown)}</p></section>
      <section className="card p-5 space-y-3"><h3 className="h3">Observed outcomes</h3><p className="mono">Gross captured {amount(p.money.captured)}</p><p className="text-sm subtle">A preview or an agent’s success message does not count as a purchase.</p></section>
    </div>
    {p.state === "ACTIVE" && <section className="card p-5 space-y-4"><h3 className="h3">Your buyer</h3><p className="subtle text-sm">Uses scoped planner, supplier and checkout roles. Every proposal shares this purchase’s remaining allowance.</p>
      <div className="flex flex-wrap gap-3"><label className="sr-only" htmlFor="purchase-supplier">Approved supplier</label><select id="purchase-supplier" className="input" value={seller} onChange={e => setSeller(e.target.value)}>{p.scope.merchants.map(m => <option key={m} value={m}>{labels[m] || m}</option>)}</select>
        <button className="pill pill-primary" disabled={busy || !p.business_policy?.current} onClick={() => act(async () => { const op = await post<Operation>(apiKey, `${path(p.id)}/agent-purchase`, { root_id: p.id, merchant_id: seller }); setNotice(`Purchase queued: ${op.id}. Waiting for provider evidence.`); })}>Ask buyer to purchase</button>
        <button className="pill" disabled={busy} onClick={() => act(() => post(apiKey, `${path(p.id)}/revoke`, { expected_epoch: p.epoch, reason: "Operator stopped new purchase admissions" }))}>Stop new purchases</button></div>
      <details className="border-t pt-4" style={{ borderColor: "var(--line)" }}><summary className="cursor-pointer text-sm font-semibold">Use a Gemini agent</summary><div className="space-y-3 pt-4">
        <p className="subtle text-sm">The deterministic buyer above needs no model. These optional models make untrusted proposals through the same purchase boundary.</p>
        <label className="block text-sm">Model<select className="input ml-3" value={model} onChange={e => setModel(e.target.value)}><option>gemini-3.5-flash</option><option>gemini-3.1-flash-lite</option><option value="qwen2.5:0.5b">qwen2.5:0.5b (local Docker only)</option><option value="qwen3:0.6b">qwen3:0.6b (local Docker only)</option></select></label>
        <label className="block text-sm">Seller message (untrusted)<textarea className="input mt-2 w-full" rows={3} maxLength={4000} value={sellerText} onChange={e => setSellerText(e.target.value)} /></label>
        <button className="pill" disabled={busy} onClick={() => act(async () => { const run = await post<{ id: string; result: { error: unknown; attempts: unknown[] } }>(apiKey, `${path(p.id)}/model-purchase`, { model_id: model, seller_text: sellerText, seed: 101 }); setNotice(run.result.error ? `Model invocation failed; no fallback was used. ${JSON.stringify(run.result.error)}` : describeAttempts(run.result.attempts)); })}>Run model proposal</button>
      </div></details>
    </section>}
    <section className="card p-5 space-y-4"><h3 className="h3">Purchase operations</h3>
      {p.operations.filter(o => o.state !== "PREPARED").length === 0 && <p className="subtle text-sm">No purchase has been admitted.</p>}
      {p.operations.filter(o => o.state !== "PREPARED").map(o => <div key={o.id} className="space-y-3 border-t pt-4" style={{ borderColor: "var(--line)" }}>
        <div className="flex flex-wrap items-center gap-3"><Stamp kind={o.state === "CONFIRMED" ? "ran" : o.state === "CLOSED_NO_EFFECT" ? "quiet" : "wait"}>{o.state === "CONFIRMED" ? "Ran" : o.state === "UNKNOWN" ? "Unknown" : o.state === "CLOSED_NO_EFFECT" ? "No effect" : "Pending"}</Stamp><span className="mono break-all">{o.id}</span></div>
        {o.state === "UNKNOWN" && <button className="pill pill-sm" disabled={busy} onClick={() => act(() => post(apiKey, `/v1/purchases/operations/${o.id}/reconcile`, { operation_version: o.revision }))}>Reconcile outcome</button>}
        {o.state === "RESERVED" && <button className="pill pill-sm" disabled={busy} onClick={() => act(() => post(apiKey, `/v1/purchases/operations/${o.id}/cancel`))}>Cancel if not dispatched</button>}
        <details><summary className="cursor-pointer text-sm">Inspect bound checkout</summary><pre className="mt-3 overflow-auto text-xs">{JSON.stringify(o.effect, null, 2)}</pre></details>
      </div>)}
    </section>
    <PurchaseExceptions apiKey={apiKey} purchase={p} refresh={load} />
    <section className="card p-5 space-y-4"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="h3">Purchase evidence</h3><button className="pill pill-sm" disabled={busy} onClick={() => act(async () => {
      const result = await call<{ bundle: Record<string, unknown>; verification: { verdict: string; task_complete: boolean } }>(`${path(p.id)}/evidence`, undefined, apiKey); setBundle(result.bundle); setVerdict(`${result.verification.verdict} · task ${result.verification.task_complete ? "complete" : "not complete"}`);
    })}>Verify actual effects</button></div><p className="subtle text-sm">Independent source records checked against approved quantities, gross debits and disclosure scope. Hash chains are tamper-evident records, not signatures.</p>
      {verdict && <p role="status" className="mono">{verdict}</p>}{bundle && <><button className="pill" onClick={() => { const url = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" })); const a = document.createElement("a"); a.href = url; a.download = `${wf}-purchase-evidence.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }}>Download evidence bundle</button><details><summary className="cursor-pointer text-sm">Inspect quotes and actual effect records</summary><pre className="mt-3 max-h-96 overflow-auto text-xs">{JSON.stringify(bundle, null, 2)}</pre></details></>}
      <ol className="space-y-2">{p.events.map(e => <li key={e.sequence} className="text-sm"><span className="mono subtle">{e.sequence} · </span>{e.body.kind}<details><summary className="cursor-pointer subtle text-xs">Record</summary><pre className="overflow-auto text-xs">{JSON.stringify(e.body.details, null, 2)}</pre></details></li>)}</ol>
    </section>
    <section className="card p-5 space-y-4"><div className="flex flex-wrap items-center justify-between gap-3"><h3 className="h3">Work receipt</h3><button className="pill pill-sm" disabled={busy} onClick={() => act(async () => setReport(await tasks.report(apiKey,wf)))}>Write the receipt</button></div>
      <p className="subtle text-sm">The same work-order receipt chain now includes purchase admissions, stops and provider-qualified outcomes. Every report sentence cites its records.</p>
      {report && <><ul className="space-y-3">{report.sentences.map((s,i) => <li key={i} className="text-sm">{s.text} {s.cites.map(c => <span key={c} className="mono subtle">[{c}] </span>)}</li>)}</ul><Stamp kind={report.chain_ok ? "ran" : "stopped"}>{report.chain_ok ? "Chain intact" : "Chain broken"}</Stamp></>}
    </section>
  </div>;
}

function PurchaseExceptions({ apiKey, purchase: p, refresh }: { apiKey: string; purchase: Purchase; refresh: () => Promise<unknown> }) {
  const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const pending = p.exceptions.filter(e => e.state === "PENDING");
  if (!pending.length) return null;
  return <section className="card p-5 space-y-5"><h3 className="h3">Needs you · exact purchase change</h3>{error && <ErrorNote>{error}</ErrorNote>}{pending.map(ex => <div key={ex.id} className="space-y-4">
    <p className="subtle text-sm">Expires {new Date(ex.expires * 1000).toLocaleString()}. This answer is single use and changes the purchase scope shown below.</p><div className="grid gap-4 md:grid-cols-2"><div><h4 className="h3 mb-3">Currently approved</h4><ScopeView scope={ex.old_scope} /></div><div><h4 className="h3 mb-3">Proposed change</h4><ScopeView scope={ex.new_scope} /></div></div>
    <details><summary className="cursor-pointer text-sm font-semibold">Action accompanying this change</summary><pre className="mt-3 overflow-auto text-xs">{JSON.stringify(ex.effect,null,2)}</pre></details>
    <div className="flex gap-3">{[false, true].map(approve => <button key={String(approve)} className={`pill ${approve ? "pill-primary" : ""}`} disabled={busy || ex.expires * 1000 < Date.now()} onClick={async () => { setBusy(true); setError(""); try { const n = await post<{ nonce: string }>(apiKey, `/v1/purchases/exceptions/${ex.id}/review-nonce`); await post(apiKey, `/v1/purchases/exceptions/${ex.id}/decide`, { approve, expected_action_digest: ex.digest, nonce: n.nonce }); await refresh(); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }}>{approve ? "Approve this exact change" : "Decline"}</button>)}</div>
  </div>)}</section>;
}

export function PurchaseActivity({ pendingOnly = false }: { pendingOnly?: boolean }) {
  const employee = useEmployee(); const [rows, setRows] = useState<{ workflow: string; root: string; state: string; pending: number }[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { if (!employee) return; let alive = true; const load = () => call<typeof rows>("/v1/purchases/work-orders", undefined, employee.key).then(r => { if (alive) { setRows(r); setError(""); } }).catch(e => { if (alive) setError(e.message); }); void load(); const t = setInterval(load, 4000); return () => { alive = false; clearInterval(t); }; }, [employee?.key]);
  const shown = pendingOnly ? rows.filter(r => r.pending > 0) : rows;
  if (!employee || (!shown.length && !error)) return null;
  return <section className="card p-5 space-y-3"><h2 className="h3">{pendingOnly ? "Purchase changes waiting for you" : "Purchase work orders"}</h2>{error && <ErrorNote>{error}</ErrorNote>}{shown.map(r => <div key={r.root} className="flex flex-wrap items-center justify-between gap-3 border-t pt-3 text-sm" style={{ borderColor: "var(--line)" }}><Link className="text-link mono" to={`/tasks?task=${r.workflow}`}>{r.workflow}</Link><span>{r.state} · {r.pending} waiting changes</span></div>)}</section>;
}

type LabRun = { id: string; manifest: { family_id: string; control_id: string; profile_id: string }; result: { error: unknown; verification: { verdict: string; task_complete: boolean }; duration_ms: number; attempts: unknown[]; bundle: unknown } };
export function PurchaseLab() {
  const employee = useEmployee();
  const [manifest, setManifest] = useState<{ families: { id: string; title: string }[]; controls: { id: string; label?: string; title?: string }[] } | null>(null);
  const [family, setFamily] = useState("duplicate_basket"); const [profile, setProfile] = useState("dedupe");
  const [runs, setRuns] = useState<LabRun[]>([]); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { if (!employee) return; let alive = true; Promise.all([
    call<typeof manifest>("/v1/purchases/lab/manifest", undefined, employee.key),
    call<LabRun[]>("/v1/purchases/lab/runs", undefined, employee.key),
  ]).then(([m, r]) => { if (alive) { setManifest(m); setRuns(r); } }).catch(e => { if (alive) setError(e.message); }); return () => { alive = false; }; }, [employee?.key]);
  return <section className="card p-6 space-y-5"><div><p className="section-label">Purchase integrity · isolated test environment</p><h2 className="h2">Same purchase. Same pressure. Different controls.</h2></div>
    <p className="subtle text-sm">Runs the shared Core and private adapters in a separate evaluator process. These authored conformance cases are model-free. Normal work orders stay isolated; incomplete and failed cases remain in the record.</p>
    {!employee ? <p className="text-sm"><Link to="/tasks" className="text-link">Open your workspace</Link> to run purchase comparisons.</p> : <>
      {error && <ErrorNote>{error}</ErrorNote>}
      <div className="flex flex-wrap items-end gap-4"><label className="text-sm space-y-2"><span className="block">Scenario</span><select className="input max-w-full" value={family} onChange={e => setFamily(e.target.value)}>{manifest?.families.map(f => <option key={f.id} value={f.id}>{f.title}</option>)}</select></label>
        <label className="text-sm space-y-2"><span className="block">Provider behavior</span><select className="input" value={profile} onChange={e => setProfile(e.target.value)}><option value="dedupe">Deduplicating</option><option value="queryable">Queryable</option><option value="opaque">Opaque outcome</option></select></label>
        <button className="pill pill-primary" disabled={busy || !manifest} onClick={async () => { setBusy(true); setError(""); try { const captured: LabRun[] = []; for (const control of manifest!.controls) {
          const r = await post<LabRun>(employee.key, "/v1/purchases/lab/runs", { family_id: family, control_id: control.id, profile_id: profile, topology: "delegated", seed: 101, manifest_version: 1 }); captured.push(r); setRuns(old => [r, ...old]);
        } } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }}>{busy ? "Running matched controls…" : "Run all controls"}</button>
      </div>
      <div className="overflow-auto"><table className="table w-full"><thead><tr><th>Scenario / provider</th><th>Control</th><th>Actual-effect verdict</th><th>Task complete</th><th>Record</th></tr></thead><tbody>{runs.slice(0, 30).map(r => <tr key={r.id}><td>{r.manifest.family_id}<span className="subtle block text-xs">{r.manifest.profile_id}</span></td><td>{r.manifest.control_id}</td><td>{r.result.error ? "Execution error retained" : r.result.verification.verdict}</td><td>{r.result.verification.task_complete ? "Yes" : "No"}</td><td><details><summary className="cursor-pointer">Inspect</summary><pre className="max-h-72 max-w-md overflow-auto text-xs">{JSON.stringify(r, null, 2)}</pre></details></td></tr>)}</tbody></table></div>
      <p className="subtle text-xs">Controls are authored references, not measurements of commercial products. A PASS verdict and completed work are separate facts. Provider observations used for evaluation do not grant runtime recovery knowledge.</p>
    </>}
  </section>;
}

export function PurchaseConnect() {
  return <section className="card p-6 space-y-4"><p className="section-label">Purchase-capable agents</p><h2 className="h2">Keep your existing client and work orders.</h2>
    <p className="subtle text-sm">Issue an agent key below. The employee attaches and confirms the purchase annex, then issues a scoped grant to the agent identity. Provider credentials stay with the private executor.</p>
    <pre className="overflow-auto rounded border p-4 text-xs" style={{ borderColor: "var(--line)" }}>{`from intentseal.delegate import DelegateClient\n\nclient = DelegateClient("http://localhost:8000", agent_key)\noperation = await client.purchase_submit(\n    workflow_id, merchant_id="supplier_a", grant_id=grant_id\n)\n# Admission is pending. Read provider-qualified status:\nstatus = await client.purchase_operation(operation["id"])`}</pre>
    <p className="text-sm">For ADK callbacks, expose a tool named <code>assever_purchase</code> with only <code>merchant_id</code> and <code>grant_id</code>. The existing remote guard intercepts it and returns an operation handle; it never invokes a second payment tool.</p>
    <a className="text-link text-sm" href="/docs" target="_blank" rel="noreferrer">Gateway API reference</a><span className="subtle mx-2">·</span><a className="text-link text-sm" href="/v1/sdk/assever.py">Download the existing SDK with purchase support</a>
  </section>;
}
