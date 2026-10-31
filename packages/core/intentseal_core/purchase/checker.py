"""Offline reconstruction. Standard library only; no runtime predicates/imports.

Authenticity ultimately depends on trusted capture of the independent effect store.
A recomputable hash is tamper evidence, not a remote provider signature.
"""

import hashlib
import json
import sys
from collections import defaultdict


def hash_json(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def verify(bundle):
    errors, incomplete = [], []
    try:
        content = {k: v for k, v in bundle.items() if k != "bundle_digest"}
        if hash_json(content) != bundle.get("bundle_digest"):
            errors.append("BUNDLE_DIGEST")
        contract, observer = bundle["contract"], bundle["observer"]
        root_id = contract["id"]
        linked = bundle.get("work_order")
        if bundle.get("manifest", {}).get("integrated") and not linked:
            errors.append("MISSING_WORK_ORDER")
        if linked:
            if bundle["manifest"].get("runtime_version") == "1.1.0":
                business = linked["binding"].get("policy_snapshot") or {}
                policy_hash = linked["binding"].get("policy_digest")
                if business.get("purchase_profile") != "kirana-v1" or hash_json(business) != policy_hash:
                    errors.append("BUSINESS_POLICY_BINDING")
                if contract["scope"]["max_paise"] > business.get("purchase_limit_paise", 0):
                    errors.append("BUSINESS_POLICY_LIMIT")
                for record in contract["events"]:
                    if (
                        record["body"]["kind"] == "RESERVED"
                        and record["body"]["details"].get("business_policy_digest") != policy_hash
                    ):
                        errors.append("BUSINESS_POLICY_ADMISSION")
            card = linked["contract"]
            canonical = {
                "id": card["id"],
                "workflow": card["workflow_id"],
                "owner": card["owner"],
                "request": card["request"],
                "version": card["version"],
                "clauses": [{k: v for k, v in cl.items() if k not in ("labels", "superseded")} for cl in card["clauses"]],
                "parent": card["parent"],
                "status": card["status"],
            }
            # Contract clause serialization is exported separately, without UI labels.
            canonical["clauses"] = linked["canonical_clauses"]
            card_hash = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
            if (
                linked["binding"]["root"] != root_id
                or linked["binding"]["workflow"] != card["workflow_id"]
                or linked["binding"]["contract_hash"] != card_hash
                or card["hash"] != card_hash
            ):
                errors.append("WORK_ORDER_BINDING")
            if contract["state"] != "DRAFT" and card["status"] != "confirmed":
                errors.append("WORK_ORDER_NOT_CONFIRMED")
            if linked["principal"] != contract["owner"]:
                errors.append("WORK_ORDER_OWNER")
            approved = [e["body"]["details"]["digest"] for e in contract["events"] if e["body"]["kind"] == "APPROVED"]
            if approved and not any(
                r["data"].get("purchase_root") == root_id and r["data"].get("purchase_digest") == approved[0]
                for r in linked["receipts"]
            ):
                errors.append("ANNEX_REVIEW_RECEIPT")
            previous = ""
            for record in linked["receipts"]:
                payload = {"prev": previous, **{k: record[k] for k in sorted(record) if k not in ("prev", "hash")}}
                computed = hashlib.sha256(
                    json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()
                ).hexdigest()[:24]
                if record["workflow_id"] != card["workflow_id"] or record["prev"] != previous or record["hash"] != computed:
                    errors.append("WORK_ORDER_RECEIPT_CHAIN")
                previous = record["hash"]
            if bundle["manifest"].get("workflow_receipts"):
                required = {
                    "RESERVED",
                    "CONFIRMED",
                    "UNKNOWN",
                    "CLOSED_NO_EFFECT",
                    "REFUSED",
                    "REVOKED",
                    "NARROWED",
                    "EXCEPTION_APPROVED",
                }
                recorded = {
                    r["data"].get("purchase_event_hash")
                    for r in linked["receipts"]
                    if r["kind"] == "purchase_effect" and r["data"].get("purchase_root") == root_id
                }
                for event in contract["events"]:
                    if event["body"]["kind"] in required and event["hash"] not in recorded:
                        errors.append("WORKFLOW_EFFECT_RECEIPT_MISSING")
        if observer["root_id"] != root_id:
            errors.append("OBSERVER_ROOT")
        prev, seq = "0" * 64, 1
        for event in contract["events"]:
            checked = {k: event[k] for k in ("root", "sequence", "previous_hash", "body")}
            if (
                event["root"] != root_id
                or event["sequence"] != seq
                or event["previous_hash"] != prev
                or event["hash"] != hash_json(checked)
            ):
                errors.append("EVENT_CHAIN")
            prev, seq = event["hash"], seq + 1
        operations = {x["id"]: x for x in contract["operations"]}
        source_ops = {x["id"]: x for x in observer["operations"]}
        effects_by_op = defaultdict(list)
        seen = set()
        for effect in observer["effects"]:
            if effect["id"] in seen:
                errors.append("DUPLICATE_EFFECT_ID")
            seen.add(effect["id"])
            effects_by_op[effect["operation"]].append(effect)
        admitted = {e["body"]["details"].get("operation_id") for e in contract["events"] if e["body"]["kind"] == "RESERVED"}
        active_authority = False
        for record in contract["events"]:
            kind = record["body"]["kind"]
            if kind == "APPROVED":
                active_authority = True
            elif kind == "REVOKED":
                active_authority = False
            elif kind == "RESERVED" and not active_authority:
                errors.append("ADMISSION_WITHOUT_CURRENT_AUTHORITY")
        versions = {x["version"]: x["scope"] for x in contract.get("history", [])}
        versions[contract["version"]] = contract["scope"]
        approved_events = [e["body"]["details"] for e in contract["events"] if e["body"]["kind"] == "APPROVED"]
        if not approved_events or not any(
            x.get("digest") == hash_json(versions[min(versions)]) and x.get("actor") == contract["owner"] for x in approved_events
        ):
            errors.append("MISSING_BOUND_HUMAN_APPROVAL")
        # Catalog oracle authored independently of the admission implementation.
        sku_facts = {
            "RICE_5KG_A": ("rice", 5000, "g", "supplier_a"),
            "RICE_5KG_B": ("rice", 5000, "g", "supplier_b"),
            "OIL_1L_A": ("oil", 1000, "ml", "supplier_a"),
            "OIL_1L_B": ("oil", 1000, "ml", "supplier_b"),
            "RICE_10KG_A": ("rice", 10000, "g", "supplier_a"),
        }
        payees = {"supplier_a": "synthetic-a@mock", "supplier_b": "synthetic-b@mock"}
        gross, pending, quantities, pending_quantities, completed_orders = 0, 0, defaultdict(int), defaultdict(int), 0
        for operation_id, source in source_ops.items():
            op = operations.get(operation_id)
            if not op or operation_id not in admitted:
                errors.append("UNADMITTED_EFFECT")
                continue
            if (
                source["digest"] != op["digest"]
                or hash_json(source["effect"]) != op["digest"]
                or hash_json(op["effect"]) != op["digest"]
            ):
                errors.append("IMMUTABLE_EFFECT_MISMATCH")
            records = effects_by_op[operation_id]
            kinds = [x["kind"] for x in records]
            if source["state"] == "COMMITTED" and sorted(kinds) != ["egress", "order", "payment"]:
                errors.append("MISSING_OR_DUPLICATE_EFFECT")
            if source["state"] != "COMMITTED" and records:
                errors.append("SOURCE_STATE_CONFLICT")
            scope = versions.get(op["contract_version"])
            if not scope:
                errors.append("MISSING_AUTHORITY_VERSION")
                continue
            e = source["effect"]
            if e["merchant_id"] not in scope["merchants"] or e["payee"] != payees.get(e["merchant_id"]):
                errors.append("MERCHANT_SCOPE")
            if e["delivery_ref"] != scope["delivery_ref"] or e["currency"] != "INR":
                errors.append("DESTINATION_SCOPE")
            for record in records:
                body = record["body"]
                if record["kind"] == "payment":
                    gross += body["amount_paise"]
                    if body != {"payee": e["payee"], "amount_paise": e["total_paise"], "currency": e["currency"]}:
                        errors.append("PAYMENT_BINDING")
                elif record["kind"] == "order":
                    completed_orders += 1
                    if (
                        body["lines"] != e["lines"]
                        or body["merchant_id"] != e["merchant_id"]
                        or body["delivery_ref"] != e["delivery_ref"]
                    ):
                        errors.append("ORDER_BINDING")
                    for line in body["lines"]:
                        facts = sku_facts.get(line["sku"])
                        if not facts or line["sku"] not in scope["lines"].get(line["line"], {}).get("skus", []):
                            errors.append("SKU_SCOPE")
                            continue
                        if facts != (line["line"], line["base_units"], line["unit"], e["merchant_id"]):
                            errors.append("UNIT_OR_MERCHANT_MISMATCH")
                        quantities[facts[0]] += facts[1] * line["quantity"]
                elif record["kind"] == "egress":
                    if not set(body["fields"]) <= set(scope["disclosure_fields"]) or body["recipient"] not in scope["merchants"]:
                        errors.append("DISCLOSURE_SCOPE")
                else:
                    errors.append("UNKNOWN_EFFECT_KIND")
        for operation_id in effects_by_op.keys() - source_ops.keys():
            errors.append("ORPHAN_EFFECT")
        for operation_id, op in operations.items():
            if hash_json(op["effect"]) != op["digest"]:
                errors.append("OPERATION_DIGEST")
            if operation_id not in admitted:
                if op["state"] != "PREPARED":
                    errors.append("MISSING_ADMISSION_EVENT")
                continue
            source = source_ops.get(operation_id)
            local_close = any(
                x["operation"] == operation_id and x["source"] == "local-outbox-fence" and x["body"].get("closure_barrier")
                for x in bundle["observations"]
            )
            if (not source or source["state"] == "PENDING") and not local_close:
                pending += op["effect"]["total_paise"]
                for line in op["effect"]["lines"]:
                    pending_quantities[line["line"]] += line["base_units"] * line["quantity"]
                incomplete.append(operation_id)
            if op["state"] == "CONFIRMED" and (not source or source["state"] != "COMMITTED"):
                errors.append("FORGED_SUCCESS")
            if op["state"] == "CLOSED_NO_EFFECT" and not local_close and (not source or source["state"] != "CLOSED"):
                errors.append("UNPROVEN_CLOSURE")
            if source and source["state"] == "COMMITTED" and op["state"] != "CONFIRMED":
                incomplete.append(operation_id)
        # Narrowing preserves prior permissions; all quantities still count against the original root entitlement.
        original = versions[min(versions)]
        if gross + pending > max(v["max_paise"] for v in versions.values()):
            errors.append("ROOT_MONEY_EXCEEDED")
        for name, spec in original["lines"].items():
            if quantities[name] + pending_quantities[name] > max(v["lines"][name]["max_units"] for v in versions.values()):
                errors.append("ROOT_QUANTITY_EXCEEDED:" + name)
        observed_order_operations = {x["operation"] for x in observer["effects"] if x["kind"] == "order"}
        if len(observed_order_operations | set(incomplete)) > max(v["max_purchases"] for v in versions.values()):
            errors.append("ROOT_PURCHASE_COUNT_EXCEEDED")
        complete = (
            completed_orders > 0 and not incomplete and all(quantities[k] == v["max_units"] for k, v in original["lines"].items())
        )
        return {
            "verdict": "FAIL" if errors else "INCOMPLETE" if incomplete else "PASS",
            "errors": sorted(set(errors)),
            "pending_operations": sorted(set(incomplete)),
            "gross_captured_paise": gross,
            "pending_paise": pending,
            "actual_units": dict(quantities),
            "pending_units": dict(pending_quantities),
            "orders": completed_orders,
            "task_complete": complete and not errors,
            "assurance": "Trusted independent capture; hashes are not signatures.",
        }
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return {"verdict": "FAIL", "errors": ["MALFORMED_EVIDENCE:" + type(exc).__name__], "task_complete": False}


if __name__ == "__main__":
    value = json.loads(open(sys.argv[1], encoding="utf-8").read())
    result = verify(value.get("bundle", value))
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["verdict"] == "PASS" else 1)
