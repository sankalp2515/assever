"""Owned synthetic effect services; never a production payment connector."""

import hmac
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException

from .common import CATALOG, MERCHANTS, db, digest, jsonb, now, uid
from .migrate import migrate
from .schemas import Strict, QuoteLine


@asynccontextmanager
async def lifespan(app):
    migrate()
    yield


app = FastAPI(title="Assever synthetic effect services", lifespan=lifespan)


def credential(role, value):
    expected = os.environ.get(role, "")
    if not expected or not value or not hmac.compare_digest(value, expected):
        raise HTTPException(403, "Private synthetic service")


def service(x_service_key: str = Header(default="")):
    credential("SERVICE_KEY", x_service_key)


def observer(x_observer_key: str = Header(default="")):
    credential("OBSERVER_KEY", x_observer_key)


def executor(x_dispatch_key: str = Header(default="")):
    credential("DISPATCH_KEY", x_dispatch_key)


class Dispatch(Strict):
    operation_id: str
    effect: dict
    digest: str
    fence: int
    profile: str
    fault: str = "none"


class QuoteRequest(Strict):
    root_id: str
    merchant_id: str
    fees_paise: int = 0
    coupon_paise: int = 0
    lines: list[QuoteLine] | None = None


@app.get("/health/ready")
def health():
    with db() as c:
        c.execute("SELECT 1")
    return {"ready": True, "synthetic": True}


@app.post("/quotes", dependencies=[Depends(service)])
def quote(data: QuoteRequest):
    if data.merchant_id not in MERCHANTS or not (0 <= data.coupon_paise <= 10**12 and 0 <= data.fees_paise <= 10**12):
        raise HTTPException(422, "Invalid quote")
    suffix = "A" if data.merchant_id == "supplier_a" else "B"
    lines = [{"sku": f"RICE_5KG_{suffix}", "quantity": 1}, {"sku": f"OIL_1L_{suffix}", "quantity": 2}]
    if data.lines is not None:
        lines = [line.model_dump() for line in data.lines]
        if (
            not lines
            or len(lines) > 10
            or any(x["sku"] not in CATALOG or CATALOG[x["sku"]]["merchant"] != data.merchant_id for x in lines)
        ):
            raise HTTPException(422, "SKU is outside this supplier's catalog")
    subtotal = sum(CATALOG[x["sku"]]["price"] * x["quantity"] for x in lines)
    if data.coupon_paise > subtotal:
        raise HTTPException(422, "Coupon exceeds item subtotal")
    body = {
        "id": uid("quote"),
        "root_id": data.root_id,
        "merchant_id": data.merchant_id,
        "payee": MERCHANTS[data.merchant_id],
        "lines": lines,
        "subtotal_paise": subtotal,
        "fees_paise": data.fees_paise,
        "coupon_paise": data.coupon_paise,
        "total_paise": subtotal + data.fees_paise - data.coupon_paise,
        "currency": "INR",
        "expires_at": now() + 600,
        "adapter_version": "owned-commerce-v1",
    }
    return {"body": body, "digest": digest(body)}


def materialize(c, row):
    if row["state"] != "PENDING" or row["due"] > now():
        return row
    e = row["effect"]
    records = {
        "payment": {"payee": e["payee"], "amount_paise": e["total_paise"], "currency": e["currency"]},
        "order": {"merchant_id": e["merchant_id"], "lines": e["lines"], "delivery_ref": e["delivery_ref"]},
        "egress": {"recipient": e["merchant_id"], "fields": e["disclosure_fields"], "data_class": "synthetic_delivery"},
    }
    for kind, body in records.items():
        c.execute(
            "INSERT INTO sink_effects VALUES(%s,%s,%s,%s,%s) ON CONFLICT(operation,kind) DO NOTHING",
            (uid("effect"), row["id"], kind, jsonb(body), now()),
        )
    c.execute("UPDATE sink_operations SET state='COMMITTED' WHERE id=%s", (row["id"],))
    row["state"] = "COMMITTED"
    return row


@app.post("/dispatch", dependencies=[Depends(service), Depends(executor)])
def dispatch(data: Dispatch):
    if digest(data.effect) != data.digest or data.profile not in ("dedupe", "queryable", "opaque") or data.fence < 1:
        raise HTTPException(422, "Invalid immutable operation")
    e = data.effect
    required = {
        "root_id",
        "merchant_id",
        "payee",
        "lines",
        "total_paise",
        "currency",
        "delivery_ref",
        "disclosure_fields",
        "quote_digest",
        "adapter_version",
    }
    if set(e) != required or e["currency"] != "INR" or type(e["total_paise"]) is not int or not 0 <= e["total_paise"] <= 10**12:
        raise HTTPException(422, "Unsupported effect projection")
    # This sink validates representation, not the human's scope. Baselines have identical sink behavior.
    with db() as c:
        c.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (data.operation_id,))
        row = c.execute("SELECT * FROM sink_operations WHERE id=%s FOR UPDATE", (data.operation_id,)).fetchone()
        if row:
            if row["digest"] != data.digest or data.fence < row["fence"]:
                raise HTTPException(409, "Payload conflict or stale fence")
            if row["state"] == "CLOSED":
                return {"state": "CLOSED", "closure_barrier": True, "operation_id": row["id"]}
            if data.profile != "dedupe" or now() > row["dedupe_until"]:
                raise HTTPException(409, "Redispatch is not guaranteed by this profile")
            row = materialize(c, row)
        else:
            delay = 2.0 if data.fault == "delay" else 0.0
            state = "CLOSED" if data.fault == "no_effect" else "PENDING"
            c.execute(
                "INSERT INTO sink_operations VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (data.operation_id, data.digest, jsonb(e), data.profile, data.fence, state, now() + delay, now(), now() + 3600),
            )
            row = c.execute("SELECT * FROM sink_operations WHERE id=%s", (data.operation_id,)).fetchone()
            row = materialize(c, row)
        result = {
            "state": row["state"],
            "operation_id": row["id"],
            "digest": row["digest"],
            "closure_barrier": row["state"] == "CLOSED",
        }
    # Commit precedes the simulated lost response.
    if data.fault in ("response_loss", "delay"):
        raise HTTPException(504, "Synthetic response loss; outcome must be reconciled")
    return result


@app.get("/status/{operation_id}", dependencies=[Depends(service)])
def status(operation_id: str):
    with db() as c:
        row = c.execute("SELECT * FROM sink_operations WHERE id=%s FOR UPDATE", (operation_id,)).fetchone()
        if not row:
            return {"state": "NOT_FOUND", "closure_barrier": False}
        if row["profile"] == "opaque":
            return {"state": "UNOBSERVABLE", "closure_barrier": False}
        row = materialize(c, row)
        return {
            "state": row["state"],
            "digest": row["digest"],
            "operation_id": operation_id,
            "closure_barrier": row["state"] == "CLOSED",
            "dedupe_until": row["dedupe_until"],
        }


@app.post("/close/{operation_id}", dependencies=[Depends(service), Depends(executor)])
def close(operation_id: str):
    with db() as c:
        row = c.execute("SELECT * FROM sink_operations WHERE id=%s FOR UPDATE", (operation_id,)).fetchone()
        if not row:
            # No negative lookup proof is created for a request that may still arrive.
            return {"state": "NOT_FOUND", "closure_barrier": False}
        row = materialize(c, row)
        if row["state"] == "PENDING":
            c.execute("UPDATE sink_operations SET state='CLOSED' WHERE id=%s", (operation_id,))
            row["state"] = "CLOSED"
        return {
            "state": row["state"],
            "digest": row["digest"],
            "closure_barrier": row["state"] == "CLOSED",
            "operation_id": operation_id,
        }


@app.get("/observe/{root_id}", dependencies=[Depends(observer)])
def observe(root_id: str):
    with db() as c:
        rows = c.execute("SELECT * FROM sink_operations WHERE effect->>'root_id'=%s FOR UPDATE", (root_id,)).fetchall()
        for row in rows:
            materialize(c, row)
        effects = c.execute(
            "SELECT e.* FROM sink_effects e JOIN sink_operations o ON o.id=e.operation WHERE o.effect->>'root_id'=%s ORDER BY e.created,e.id",
            (root_id,),
        ).fetchall()
        rows = c.execute("SELECT * FROM sink_operations WHERE effect->>'root_id'=%s ORDER BY created,id", (root_id,)).fetchall()
        notices = c.execute(
            "SELECT n.* FROM sink_notices n JOIN sink_operations o ON o.id=n.operation WHERE o.effect->>'root_id'=%s ORDER BY n.id",
            (root_id,),
        ).fetchall()
    return {
        "source": "owned-independent-effect-store-v1",
        "root_id": root_id,
        "operations": rows,
        "effects": effects,
        "notices": notices,
        "observed_at": now(),
    }


@app.post("/refund/{operation_id}", dependencies=[Depends(service)])
def refund_notice(operation_id: str):
    with db() as c:
        row = c.execute("SELECT * FROM sink_operations WHERE id=%s FOR UPDATE", (operation_id,)).fetchone()
        if not row or row["state"] != "COMMITTED":
            raise HTTPException(409, "Only a captured synthetic payment can be refunded")
        notice_id = "refund_" + operation_id
        body = {
            "amount_paise": row["effect"]["total_paise"],
            "currency": "INR",
            "synthetic": True,
            "gross_history_retained": True,
        }
        c.execute(
            "INSERT INTO sink_notices VALUES(%s,%s,'REFUND',%s) ON CONFLICT DO NOTHING", (notice_id, operation_id, jsonb(body))
        )
    return {"id": notice_id, "operation_id": operation_id, "kind": "REFUND", "body": body}


@app.post("/faults/{operation_id}/expire-dedupe", dependencies=[Depends(service), Depends(executor)])
def expire_dedupe(operation_id: str):
    if os.environ.get("LAB_ENABLED") != "1":
        raise HTTPException(403, "Synthetic fault hooks are disabled")
    with db() as c:
        row = c.execute(
            "UPDATE sink_operations SET dedupe_until=%s WHERE id=%s RETURNING id", (now() - 1, operation_id)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Unknown synthetic operation")
    return {"operation_id": operation_id, "dedupe_expired": True}
