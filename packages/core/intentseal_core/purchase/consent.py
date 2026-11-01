"""DEPA-style consent artefact for an approved purchase, and an offline check of effects against it.

Standard library only, like checker.py. The artefact is derived from the evidence bundle: the human
approval becomes a purpose-bound consent record (purpose, items, gross cap, frequency, data fields,
validity window, revocation). The check joins it with the independent effect records:

* every effect's operation must be dispatched inside the validity window and before any revocation
  (revocation stops new dispatch; effects already dispatched are not retroactively cancelled);
* captured money, order count, units and disclosed fields must stay within the consented limits.

Field names follow the DEPA / account-aggregator consent artefact shape where a counterpart exists.
This is a modelled projection for evaluation, not a ReBIT-certified artefact or a live consent manager.
"""

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone

ARTEFACT_VERSION = "assever-depa-1.0"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None


def _event(contract, kind):
    return next((e for e in contract["events"] if e["body"]["kind"] == kind), None)


def build_artefact(bundle, purpose_text=None):
    contract = bundle["contract"]
    scope = contract["scope"]
    approved = _event(contract, "APPROVED")
    revoked = _event(contract, "REVOKED")
    start = approved["body"]["details"]["timestamp"] if approved else None
    expired = scope["expires_at"] < (bundle["observer"].get("observed_at") or 0)
    status = "REVOKED" if revoked else "EXPIRED" if expired else "ACTIVE" if approved else "PENDING"
    request = ((bundle.get("work_order") or {}).get("contract") or {}).get("request")
    body = {
        "ver": ARTEFACT_VERSION,
        "consentId": contract["id"],
        "status": status,
        "createTimestamp": _iso(start),
        "dataPrincipal": {"id": contract["owner"], "type": "INDIVIDUAL_OR_MSME"},
        "dataConsumer": {"id": "assever-buyer-agent", "type": "AI_AGENT"},
        "dataProviders": [{"id": m, "type": "SELLER"} for m in scope["merchants"]],
        "purpose": {"code": "PURCHASE", "refUri": "assever://profile/kirana-v1", "text": purpose_text or request or "Approved purchase"},
        "consentDetail": {
            "items": {k: {"maxUnits": v["max_units"], "unit": v["unit"], "skus": v["skus"]} for k, v in scope["lines"].items()},
            "maxAmount": {"value": scope["max_paise"], "unit": "paise", "currency": scope["currency"], "basis": "gross, including fees"},
            "frequency": {"unit": "PURCHASE", "value": scope["max_purchases"]},
            "dataFields": scope["disclosure_fields"],
            "deliveryRef": scope["delivery_ref"],
            "fetchType": "ONETIME",
            "consentStart": _iso(start),
            "consentExpiry": _iso(scope["expires_at"]),
        },
        "revocation": {"revokedAt": _iso(revoked["body"]["timestamp"]) if revoked else None,
                       "effect": "Stops new dispatch; effects already dispatched reconcile and are not retroactively cancelled."},
        "binding": {"approvalDigest": contract["digest"], "approvalEventHash": approved["hash"] if approved else None,
                    "bundleDigest": bundle.get("bundle_digest")},
        "_timestamps": {"start": start, "expiry": scope["expires_at"], "revoked": revoked["body"]["timestamp"] if revoked else None},
    }
    body["consentDigest"] = _digest(body)
    return body


def check(artefact, bundle):
    """Return {verdict, errors, checked} for the bundle's effects against the consent artefact."""
    errors = []
    content = {k: v for k, v in artefact.items() if k != "consentDigest"}
    if _digest(content) != artefact.get("consentDigest"):
        errors.append("CONSENT_DIGEST")
    contract = bundle["contract"]
    approved = _event(contract, "APPROVED")
    if artefact["binding"]["approvalDigest"] != contract["digest"] or (approved and artefact["binding"]["approvalEventHash"] != approved["hash"]):
        errors.append("CONSENT_BINDING")
    detail, ts = artefact["consentDetail"], artefact["_timestamps"]
    if not approved and bundle["observer"]["effects"]:
        errors.append("EFFECT_WITHOUT_CONSENT")
    dispatched = {e["body"]["details"]["operation_id"]: e["body"]["timestamp"] for e in contract["events"] if e["body"]["kind"] == "DISPATCHING"}
    paid, orders, units, checked = 0, set(), defaultdict(int), 0
    for effect in bundle["observer"]["effects"]:
        checked += 1
        at = dispatched.get(effect["operation"], effect["created"])
        if ts["start"] is None or at < ts["start"]:
            errors.append("EFFECT_BEFORE_CONSENT")
        if at > ts["expiry"]:
            errors.append("EFFECT_AFTER_EXPIRY")
        if ts["revoked"] is not None and at > ts["revoked"]:
            errors.append("EFFECT_AFTER_REVOCATION")
        body = effect["body"]
        if effect["kind"] == "payment":
            paid += body["amount_paise"]
        elif effect["kind"] == "order":
            orders.add(effect["operation"])
            for line in body["lines"]:
                units[line["line"]] += line["base_units"] * line["quantity"]
        elif effect["kind"] == "egress":
            if not set(body["fields"]) <= set(detail["dataFields"]):
                errors.append("DATA_FIELD_NOT_CONSENTED")
            if body["recipient"] not in {p["id"] for p in artefact["dataProviders"]}:
                errors.append("RECIPIENT_NOT_CONSENTED")
    if paid > detail["maxAmount"]["value"]:
        errors.append("AMOUNT_EXCEEDS_CONSENT")
    if len(orders) > detail["frequency"]["value"]:
        errors.append("FREQUENCY_EXCEEDS_CONSENT")
    for line, total in units.items():
        if line not in detail["items"] or total > detail["items"][line]["maxUnits"]:
            errors.append(f"UNITS_EXCEED_CONSENT:{line}")
    return {"verdict": "FAIL" if errors else "PASS", "errors": sorted(set(errors)), "checked_effects": checked,
            "captured_paise": paid, "orders": len(orders)}


if __name__ == "__main__":
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    bundle = data.get("bundle", data)
    artefact = build_artefact(bundle)
    print(json.dumps({"artefact": artefact, "check": check(artefact, bundle)}, indent=2, ensure_ascii=False))
