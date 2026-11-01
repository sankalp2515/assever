/** Browser port of packages/core/intentseal_core/purchase/consent.py: DEPA-style consent artefact + effect check. Digests match the Python version. */
type Json = null | boolean | number | string | Json[] | { [k: string]: Json };
type Ev = { hash: string; body: { kind: string; timestamp: number; details: Record<string, any> } };
type Bundle = { bundle_digest?: string; contract: any; observer: { observed_at?: number; effects: { operation: string; kind: string; created: number; body: any }[] }; work_order?: any };
export type Artefact = Record<string, any>;
export type ConsentCheck = { verdict: "PASS" | "FAIL"; errors: string[]; checked_effects: number; captured_paise: number; orders: number };

const canon = (v: Json): string => Array.isArray(v) ? `[${v.map(canon).join(",")}]`
  : v && typeof v === "object" ? `{${Object.keys(v).sort().map(k => `${JSON.stringify(k)}:${canon(v[k])}`).join(",")}}` : JSON.stringify(v);
async function digest(v: unknown): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canon(v as Json)));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}
const iso = (ts?: number | null) => ts ? new Date(ts * 1000).toISOString().replace(/\.\d{3}Z$/, "Z") : null;
const event = (c: any, kind: string): Ev | undefined => c.events.find((e: Ev) => e.body.kind === kind);

export async function buildArtefact(b: Bundle, purposeText?: string): Promise<Artefact> {
  const c = b.contract, s = c.scope, approved = event(c, "APPROVED"), revoked = event(c, "REVOKED");
  const start = approved ? approved.body.details.timestamp : null;
  const expired = s.expires_at < (b.observer.observed_at || 0);
  const body: Artefact = {
    ver: "assever-depa-1.0", consentId: c.id,
    status: revoked ? "REVOKED" : expired ? "EXPIRED" : approved ? "ACTIVE" : "PENDING",
    createTimestamp: iso(start),
    dataPrincipal: { id: c.owner, type: "INDIVIDUAL_OR_MSME" },
    dataConsumer: { id: "assever-buyer-agent", type: "AI_AGENT" },
    dataProviders: s.merchants.map((m: string) => ({ id: m, type: "SELLER" })),
    purpose: { code: "PURCHASE", refUri: "assever://profile/kirana-v1", text: purposeText || b.work_order?.contract?.request || "Approved purchase" },
    consentDetail: {
      items: Object.fromEntries(Object.entries(s.lines).map(([k, v]: [string, any]) => [k, { maxUnits: v.max_units, unit: v.unit, skus: v.skus }])),
      maxAmount: { value: s.max_paise, unit: "paise", currency: s.currency, basis: "gross, including fees" },
      frequency: { unit: "PURCHASE", value: s.max_purchases },
      dataFields: s.disclosure_fields, deliveryRef: s.delivery_ref, fetchType: "ONETIME",
      consentStart: iso(start), consentExpiry: iso(s.expires_at),
    },
    revocation: { revokedAt: revoked ? iso(revoked.body.timestamp) : null, effect: "Stops new dispatch; effects already dispatched reconcile and are not retroactively cancelled." },
    binding: { approvalDigest: c.digest, approvalEventHash: approved ? approved.hash : null, bundleDigest: b.bundle_digest ?? null },
    _timestamps: { start, expiry: s.expires_at, revoked: revoked ? revoked.body.timestamp : null },
  };
  body.consentDigest = await digest(body);
  return body;
}

export async function checkConsent(a: Artefact, b: Bundle): Promise<ConsentCheck> {
  const errors: string[] = [];
  const { consentDigest, ...content } = a;
  if (await digest(content) !== consentDigest) errors.push("CONSENT_DIGEST");
  const c = b.contract, approved = event(c, "APPROVED");
  if (a.binding.approvalDigest !== c.digest || (approved && a.binding.approvalEventHash !== approved.hash)) errors.push("CONSENT_BINDING");
  const d = a.consentDetail, ts = a._timestamps;
  if (!approved && b.observer.effects.length) errors.push("EFFECT_WITHOUT_CONSENT");
  const dispatched: Record<string, number> = {};
  for (const e of c.events as Ev[]) if (e.body.kind === "DISPATCHING") dispatched[e.body.details.operation_id] = e.body.timestamp;
  let paid = 0; const orders = new Set<string>(); const units: Record<string, number> = {};
  for (const ef of b.observer.effects) {
    const at = dispatched[ef.operation] ?? ef.created;
    if (ts.start == null || at < ts.start) errors.push("EFFECT_BEFORE_CONSENT");
    if (at > ts.expiry) errors.push("EFFECT_AFTER_EXPIRY");
    if (ts.revoked != null && at > ts.revoked) errors.push("EFFECT_AFTER_REVOCATION");
    if (ef.kind === "payment") paid += ef.body.amount_paise;
    else if (ef.kind === "order") { orders.add(ef.operation); for (const l of ef.body.lines) units[l.line] = (units[l.line] || 0) + l.base_units * l.quantity; }
    else if (ef.kind === "egress") {
      if (!ef.body.fields.every((x: string) => d.dataFields.includes(x))) errors.push("DATA_FIELD_NOT_CONSENTED");
      if (!a.dataProviders.some((p: any) => p.id === ef.body.recipient)) errors.push("RECIPIENT_NOT_CONSENTED");
    }
  }
  if (paid > d.maxAmount.value) errors.push("AMOUNT_EXCEEDS_CONSENT");
  if (orders.size > d.frequency.value) errors.push("FREQUENCY_EXCEEDS_CONSENT");
  for (const [line, total] of Object.entries(units)) if (!d.items[line] || total > d.items[line].maxUnits) errors.push(`UNITS_EXCEED_CONSENT:${line}`);
  const uniq = [...new Set(errors)].sort();
  return { verdict: uniq.length ? "FAIL" : "PASS", errors: uniq, checked_effects: b.observer.effects.length, captured_paise: paid, orders: orders.size };
}
