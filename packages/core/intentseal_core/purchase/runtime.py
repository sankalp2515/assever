"""Transactional purchase ledger. All admissions lock the same trusted root."""

import hashlib
import hmac
import os
import json
from functools import lru_cache

from .common import CATALOG, MERCHANTS, canonical, digest, jsonb, now, uid


@lru_cache(maxsize=16)
def _builtin_policy_digest(path, modified):
    from ..delegate.model import load_delegate_policy

    return digest(load_delegate_policy("kirana").model_dump())


def business_scope(row, scope):
    if os.environ.get("INTEGRATED_REQUIRE_WORKFLOW") != "1" or row["is_lab"]:
        return
    policy = row.get("business_policy") or {}
    require(
        policy.get("current"),
        "BUSINESS_POLICY_CHANGED",
        "The business policy changed or this older annex needs a registered purchase profile. Stop this task and review a new work order.",
    )
    require(
        policy.get("profile") == "kirana-v1", "BUSINESS_POLICY", "This business has not authorized the purchase profile.", 403
    )
    require(
        scope["max_paise"] <= policy["limit_paise"], "BUSINESS_LIMIT", "The purchase budget exceeds the business policy ceiling."
    )


class Refusal(Exception):
    def __init__(self, code, message, status=409):
        self.code, self.message, self.status = code, message, status


def require(test, code, message, status=409):
    if not test:
        raise Refusal(code, message, status)


def event(c, root, kind, details):
    # Callers hold the root lock, including reads that append audit events.
    last = c.execute("SELECT sequence,hash FROM events WHERE root=%s ORDER BY sequence DESC LIMIT 1", (root,)).fetchone()
    seq, prev = (last["sequence"] + 1, last["hash"]) if last else (1, "0" * 64)
    body = {"kind": kind, "details": details, "timestamp": now()}
    hashed = digest({"root": root, "sequence": seq, "previous_hash": prev, "body": body})
    c.execute("INSERT INTO events VALUES(%s,%s,%s,%s,%s)", (root, seq, prev, hashed, jsonb(body)))
    from .audit import mirror

    mirror(c, root, kind, details, hashed)


def root(c, root_id, actor, lock=True):
    row = c.execute(
        "SELECT * FROM contracts WHERE id=%s AND tenant=%s" + (" FOR UPDATE" if lock else ""), (root_id, actor["tenant"])
    ).fetchone()
    require(row is not None, "NOT_FOUND", "Purchase not found.", 404)
    require(
        actor.get("allow_lab", True) or not row["is_lab"],
        "LAB_ROOT_PRIVATE",
        "Inspect this isolated run through the evaluation record.",
        404,
    )
    if os.environ.get("INTEGRATED_REQUIRE_WORKFLOW") == "1" and not row["is_lab"]:
        binding = c.execute("SELECT * FROM workflow_bindings WHERE root=%s", (root_id,)).fetchone()
        require(binding, "WORKFLOW_BINDING", "A purchase must belong to an existing delegation.")
        current = c.execute(
            "SELECT d.hash,d.status,w.workspace FROM public.delegate_contracts d JOIN public.delegate_workflows w ON w.id=d.workflow_id WHERE d.workflow_id=%s ORDER BY d.version DESC LIMIT 1",
            (binding["workflow"],),
        ).fetchone()
        require(
            current and current["hash"] == binding["contract_hash"],
            "WORK_ORDER_CHANGED",
            "The work order changed; review purchase authority again.",
        )
        if row["state"] == "ACTIVE":
            require(current["status"] == "confirmed", "WORK_ORDER_UNCONFIRMED", "The work order is not confirmed.")
        policy = binding.get("policy_snapshot") or {}
        live_digest = None
        if current["workspace"] == "kirana-procurement":
            from ..config import repo_root

            path = repo_root() / "policies/delegate/kirana.yaml"
            if path.exists():
                live_digest = _builtin_policy_digest(str(path), path.stat().st_mtime_ns)
        elif policy:
            from ..delegate.model import custom_delegate_policy

            registered = c.execute(
                "SELECT policy FROM public.delegate_workspaces WHERE id=%s FOR SHARE", (current["workspace"],)
            ).fetchone()
            if registered:
                live_digest = digest(custom_delegate_policy(json.loads(registered["policy"]), current["workspace"]).model_dump())
        row["business_policy"] = {
            "profile": policy.get("purchase_profile"),
            "limit_paise": policy.get("purchase_limit_paise", 0),
            "digest": binding.get("policy_digest"),
            "current": bool(live_digest and live_digest == binding.get("policy_digest")),
        }
    if actor["role"] == "agent":
        allowed = c.execute(
            "SELECT 1 FROM grants WHERE root=%s AND actor=%s AND epoch=%s AND expires>%s",
            (root_id, actor["actor"], row["epoch"], now()),
        ).fetchone()
        require(allowed, "NOT_FOUND", "Purchase not found.", 404)
    else:
        require(row["owner"] == actor["actor"], "NOT_FOUND", "Purchase not found.", 404)
    return row


def validate_scope(scope):
    require(
        set(scope)
        == {"max_paise", "currency", "max_purchases", "lines", "merchants", "delivery_ref", "disclosure_fields", "expires_at"},
        "SCOPE_SCHEMA",
        "Unsupported scope fields.",
        422,
    )
    require(type(scope["max_paise"]) is int and 0 < scope["max_paise"] <= 10**12, "MONEY_RANGE", "Invalid gross cap.", 422)
    require(
        scope["currency"] == "INR" and scope["delivery_ref"] == "shop_01",
        "SCOPE_SCHEMA",
        "Unsupported currency or delivery.",
        422,
    )
    require(
        type(scope["max_purchases"]) is int and 1 <= scope["max_purchases"] <= 10, "SCOPE_SCHEMA", "Invalid purchase count.", 422
    )
    require(
        isinstance(scope["expires_at"], (int, float)) and now() < scope["expires_at"] <= now() + 604800,
        "EXPIRY",
        "Expiry must be within seven days.",
        422,
    )
    require(scope["merchants"] and set(scope["merchants"]) <= MERCHANTS.keys(), "MERCHANT", "Unknown supplier.", 422)
    require(
        set(scope["disclosure_fields"]) <= {"shop_name", "delivery_address"},
        "DISCLOSURE",
        "Only synthetic delivery fields are supported.",
        422,
    )
    require(set(scope["lines"]) == {"rice", "oil"}, "SCOPE_SCHEMA", "This profile requires rice and oil demand.", 422)
    for name, line in scope["lines"].items():
        require(
            set(line) == {"max_units", "unit", "skus"} and type(line["max_units"]) is int and 0 < line["max_units"] <= 100000,
            "QUANTITY",
            "Invalid demand units.",
            422,
        )
        require(
            line["skus"]
            and all(s in CATALOG and CATALOG[s]["line"] == name and CATALOG[s]["unit"] == line["unit"] for s in line["skus"]),
            "SKU_UNIT",
            "Invalid SKU equivalence.",
            422,
        )


def active(row):
    require(row["state"] == "ACTIVE", "AUTHORITY_INACTIVE", "This purchase is not active.")
    require(row["scope"]["expires_at"] > now(), "AUTHORITY_EXPIRED", "The approval has expired.")
    business_scope(row, row["scope"])


def grant_signature(data, key_version):
    key = os.environ.get("ISSUER_KEY_" + key_version, "")
    require(bool(key), "ISSUER_RETIRED", "Grant issuer is unavailable.", 403)
    return hmac.new(key.encode(), canonical(data).encode(), hashlib.sha256).hexdigest()


def checked_grant(c, row, actor, grant_id, operation, line_names):
    if actor["role"] != "agent" and not grant_id:
        return
    g = c.execute("SELECT * FROM grants WHERE id=%s AND root=%s", (grant_id, row["id"])).fetchone()
    require(g is not None and g["actor"] == actor["actor"], "GRANT_IDENTITY", "This grant belongs to another actor.", 403)
    signed = {k: g[k] for k in ("id", "root", "parent", "actor", "audience", "epoch", "expires", "scope")}
    require(
        hmac.compare_digest(g["signature"], grant_signature(signed, g["key_version"])), "GRANT_SIGNATURE", "Invalid grant.", 403
    )
    require(
        g["epoch"] == row["epoch"] and g["expires"] > now() and g["audience"] == "purchase-api",
        "GRANT_STALE",
        "The grant is expired or revoked.",
        403,
    )
    require(
        operation in g["scope"]["operations"] and set(line_names) <= set(g["scope"]["lines"]),
        "GRANT_SCOPE",
        "The grant does not permit this work.",
        403,
    )


def projection(c, row, proposal, actor):
    p, scope = proposal["body"], row["scope"]
    q = c.execute("SELECT * FROM quotes WHERE id=%s AND root=%s", (p["checkout_ref"], row["id"])).fetchone()
    require(
        q is not None and q["expires"] > now() and digest(q["body"]) == q["digest"],
        "QUOTE_STALE",
        "Obtain a current immutable quote.",
    )
    quote = q["body"]
    require(
        quote.get("adapter_version") == "owned-commerce-v1",
        "ADAPTER_VERSION",
        "The checkout uses an unsupported adapter binding.",
    )
    require(
        type(quote.get("fees_paise")) is int
        and type(quote.get("coupon_paise")) is int
        and 0 <= quote["fees_paise"] <= 10**12
        and 0 <= quote["coupon_paise"] <= 10**12,
        "QUOTE_ARITHMETIC",
        "Unsupported fee or coupon representation.",
    )
    subtotal = sum(CATALOG.get(x["sku"], {}).get("price", -(10**12)) * x["quantity"] for x in quote["lines"])
    require(
        subtotal == quote["subtotal_paise"]
        and quote["total_paise"] == subtotal + quote["fees_paise"] - quote["coupon_paise"]
        and quote["coupon_paise"] <= subtotal,
        "QUOTE_ARITHMETIC",
        "The checkout arithmetic does not match the catalog.",
    )
    require(
        p["merchant_id"] == quote["merchant_id"]
        and p["total_paise"] == quote["total_paise"]
        and p["currency"] == quote["currency"],
        "CHECKOUT_CHANGED",
        "The proposed checkout differs from the supplier quote.",
    )
    requested = sorted([{"sku": x["sku"], "quantity": x["quantity"]} for x in p["lines"]], key=lambda x: x["sku"])
    require(requested == sorted(quote["lines"], key=lambda x: x["sku"]), "CHECKOUT_CHANGED", "The checkout lines changed.")
    quantities, lines = {}, []
    line_ids = {x["id"]: x["name"] for x in c.execute("SELECT * FROM demand_lines WHERE root=%s", (row["id"],)).fetchall()}
    for line in p["lines"]:
        sku = CATALOG.get(line["sku"])
        require(
            sku is not None and line_ids.get(line["demand_line_id"]) == sku["line"],
            "DEMAND_IDENTITY",
            "Use the approved demand line.",
        )
        require(line["unit"] == ("pack" if sku["unit"] == "g" else "bottle"), "PACK_UNIT", "Pack size or unit does not match.")
        require(sku["merchant"] == p["merchant_id"], "SKU_MERCHANT", "The SKU does not belong to this supplier's catalog.")
        name = sku["line"]
        quantities[name] = quantities.get(name, 0) + sku["base_units"] * line["quantity"]
        lines.append(
            {
                "demand_line_id": line["demand_line_id"],
                "line": name,
                "sku": line["sku"],
                "quantity": line["quantity"],
                "base_units": sku["base_units"],
                "unit": sku["unit"],
            }
        )
    checked_grant(c, row, actor, proposal["grant_id"], "propose", quantities)
    if row["control"] != "unrestricted":
        require(
            p["merchant_id"] in scope["merchants"] and quote["payee"] == MERCHANTS[p["merchant_id"]],
            "MERCHANT_SCOPE",
            "The supplier/payee is outside approval.",
        )
        require(p["delivery_ref"] == scope["delivery_ref"], "DESTINATION", "Delivery destination is outside approval.")
        require(
            all(x["sku"] in scope["lines"][x["line"]]["skus"] for x in lines),
            "SKU_SCOPE",
            "The item is not an approved equivalent.",
        )
        require(p["total_paise"] <= scope["max_paise"], "BUDGET", "The all-in total exceeds approval.")
    effect = {
        "root_id": row["id"],
        "merchant_id": p["merchant_id"],
        "payee": quote["payee"],
        "lines": lines,
        "total_paise": p["total_paise"],
        "currency": "INR",
        "delivery_ref": p["delivery_ref"],
        "disclosure_fields": scope["disclosure_fields"],
        "quote_digest": q["digest"],
        "adapter_version": quote["adapter_version"],
    }
    return effect, quantities


def reserve(c, row, op, actor):
    active(row)
    require(
        op["digest"] == digest(op["effect"]) and row["version"] == op["contract_version"] and row["epoch"] == op["epoch"],
        "PREVIEW_STALE",
        "Review a new preview after the authority changed.",
    )
    quantities = {}
    for line in op["effect"]["lines"]:
        quantities[line["line"]] = quantities.get(line["line"], 0) + line["quantity"] * line["base_units"]
    checked_grant(c, row, actor, op["grant_id"], "commit", quantities)
    # Quote freshness is rechecked at admission; dispatch always uses stored immutable bytes.
    quote = c.execute(
        "SELECT expires FROM quotes WHERE digest=%s AND root=%s", (op["effect"]["quote_digest"], row["id"])
    ).fetchone()
    require(quote and quote["expires"] > now(), "QUOTE_STALE", "Obtain a fresh quote.")
    reservations = c.execute("SELECT * FROM reservations WHERE root=%s AND bucket<>'closed'", (row["id"],)).fetchall()
    scope, control = row["scope"], row["control"]
    if control in ("payment", "conservative", "adaptive"):
        require(
            sum(r["money"] for r in reservations) + op["effect"]["total_paise"] <= scope["max_paise"],
            "BUDGET_ENCUMBERED",
            "The remaining budget is already committed or pending.",
        )
    if control in ("conservative", "adaptive"):
        for name, qty in quantities.items():
            used = sum(r["quantities"].get(name, 0) for r in reservations)
            require(
                used + qty <= scope["lines"][name]["max_units"],
                "DEMAND_ALREADY_ENCUMBERED",
                "These items are already pending or purchased.",
            )
        require(
            len(reservations) < scope["max_purchases"], "PURCHASE_COUNT", "The approved purchase is already pending or complete."
        )
    c.execute(
        "INSERT INTO reservations VALUES(%s,%s,%s,%s,'reserved')",
        (op["id"], row["id"], op["effect"]["total_paise"], jsonb(quantities)),
    )
    c.execute("UPDATE operations SET state='RESERVED',revision=revision+1,updated=%s WHERE id=%s", (now(), op["id"]))
    c.execute("INSERT INTO outbox(operation,state) VALUES(%s,'PENDING')", (op["id"],))
    event(
        c,
        row["id"],
        "RESERVED",
        {
            "operation_id": op["id"],
            "money_paise": op["effect"]["total_paise"],
            "quantities": quantities,
            "business_policy_digest": (row.get("business_policy") or {}).get("digest"),
        },
    )


def settle(c, op, observation, source="provider-status"):
    require(
        observation.get("operation_id", op["id"]) == op["id"],
        "OBSERVATION_CONFLICT",
        "The observation belongs to another operation.",
    )
    if observation.get("digest"):
        require(observation["digest"] == op["digest"], "OBSERVATION_CONFLICT", "The provider's bytes differ from the admission.")
    state = observation.get("state")
    terminal = (
        "CONFIRMED"
        if state == "COMMITTED"
        else "CLOSED_NO_EFFECT"
        if state == "CLOSED" and observation.get("closure_barrier")
        else "UNKNOWN"
    )
    if op["state"] in ("CONFIRMED", "CLOSED_NO_EFFECT"):
        require(terminal == op["state"], "OBSERVATION_CONFLICT", "Contradictory terminal evidence requires investigation.")
        return
    event_id = digest({"operation": op["id"], "observation": observation})
    c.execute(
        "INSERT INTO observations VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(source,event_id) DO NOTHING",
        (uid("obs"), op["id"], source, event_id, jsonb(observation), now()),
    )
    c.execute("UPDATE operations SET state=%s,revision=revision+1,updated=%s WHERE id=%s", (terminal, now(), op["id"]))
    bucket = {"CONFIRMED": "captured", "CLOSED_NO_EFFECT": "closed", "UNKNOWN": "unknown"}[terminal]
    c.execute("UPDATE reservations SET bucket=%s WHERE operation=%s", (bucket, op["id"]))
    c.execute("UPDATE outbox SET state=%s WHERE operation=%s", ("RECONCILE" if terminal == "UNKNOWN" else "DONE", op["id"]))
    event(c, op["root"], terminal, {"operation_id": op["id"], "observation_ref": event_id, "source": source})


def snapshot(c, row):
    operations = c.execute("SELECT * FROM operations WHERE root=%s ORDER BY created,id", (row["id"],)).fetchall()
    reservations = c.execute("SELECT * FROM reservations WHERE root=%s", (row["id"],)).fetchall()
    money = {k: sum(x["money"] for x in reservations if x["bucket"] == k) for k in ("captured", "reserved", "unknown", "closed")}
    money["remaining"] = row["scope"]["max_paise"] - sum(money[k] for k in ("captured", "reserved", "unknown"))
    quantities = {}
    for name, spec in row["scope"]["lines"].items():
        values = {
            k: sum(x["quantities"].get(name, 0) for x in reservations if x["bucket"] == k)
            for k in ("captured", "reserved", "unknown")
        }
        quantities[name] = {**spec, **values, "remaining": spec["max_units"] - sum(values.values())}
    public = {k: v for k, v in row.items() if k != "nonce_hash"}
    return {
        **public,
        "money": money,
        "quantities": quantities,
        "operations": operations,
        "demand_lines": c.execute("SELECT id,name FROM demand_lines WHERE root=%s ORDER BY name", (row["id"],)).fetchall(),
        "events": c.execute("SELECT * FROM events WHERE root=%s ORDER BY sequence", (row["id"],)).fetchall(),
        "exceptions": c.execute(
            "SELECT id,effect,digest,old_scope,new_scope,expires,state,version FROM exceptions WHERE root=%s", (row["id"],)
        ).fetchall(),
    }
