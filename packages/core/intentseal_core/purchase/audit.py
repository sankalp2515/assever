"""Append purchase outcomes to the original workflow receipt chain atomically.

The root lock serializes purchase writers. Savepoint retries also interoperate
with the existing receipt writer's optimistic primary-key concurrency protocol.
No mirrored receipt grants authority or settles money.
"""

import json
import os
from psycopg.errors import UniqueViolation
from .common import now
from ..delegate.receipts import chain_hash

KINDS = {
    "RESERVED": "pending",
    "CONFIRMED": "executed",
    "UNKNOWN": "unknown",
    "CLOSED_NO_EFFECT": "not-executed",
    "REFUSED": "block",
    "REVOKED": "stopped",
    "NARROWED": "narrowed",
    "EXCEPTION_APPROVED": "approved",
}


def mirror(c, root_id, kind, details, event_hash):
    if os.environ.get("INTEGRATED_REQUIRE_WORKFLOW") != "1" or kind not in KINDS:
        return
    linked = c.execute("SELECT workflow FROM workflow_bindings WHERE root=%s", (root_id,)).fetchone()
    if not linked:
        return
    operation = details.get("operation_id")
    effect = None
    if operation:
        row = c.execute("SELECT effect FROM operations WHERE id=%s AND root=%s", (operation, root_id)).fetchone()
        effect = row["effect"] if row else None
    messages = {
        "RESERVED": "Approved purchase admitted; waiting for provider evidence.",
        "CONFIRMED": "Provider confirmed the purchase effect.",
        "UNKNOWN": "Purchase outcome is unknown; exposure remains reserved.",
        "CLOSED_NO_EFFECT": "Purchase closed with no effect.",
        "REFUSED": "Purchase request stopped by the deterministic gate.",
        "REVOKED": "The owner stopped new purchase admissions.",
        "NARROWED": "The owner narrowed purchase authority.",
        "EXCEPTION_APPROVED": "The owner approved one exact purchase change.",
    }
    data = {
        "purchase_root": root_id,
        "purchase_event_hash": event_hash,
        "purchase_event_kind": kind,
        "details": details,
        "effect": effect,
    }
    for _ in range(16):
        last = c.execute(
            "SELECT seq,hash FROM public.delegate_receipts WHERE workflow_id=%s ORDER BY seq DESC LIMIT 1", (linked["workflow"],)
        ).fetchone()
        seq = last["seq"] + 1 if last else 1
        prev = last["hash"] if last else ""
        record = {
            "workflow_id": linked["workflow"],
            "seq": seq,
            "rid": f"R-{seq}",
            "kind": "purchase_effect",
            "agent": "purchase-executor" if kind in ("CONFIRMED", "UNKNOWN", "CLOSED_NO_EFFECT") else "purchase-gate",
            "tool": "assever_purchase",
            "decision": KINDS[kind],
            "reason": messages[kind],
            "data": data,
            "created": round(now(), 3),
        }
        hashed = chain_hash(prev, record)
        c.execute("SAVEPOINT purchase_receipt")
        try:
            c.execute(
                "INSERT INTO public.delegate_receipts VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    record["workflow_id"],
                    seq,
                    record["rid"],
                    record["kind"],
                    record["agent"],
                    record["tool"],
                    record["decision"],
                    record["reason"],
                    json.dumps(data, ensure_ascii=False, default=str),
                    record["created"],
                    prev,
                    hashed,
                ),
            )
        except UniqueViolation:
            c.execute("ROLLBACK TO SAVEPOINT purchase_receipt")
            c.execute("RELEASE SAVEPOINT purchase_receipt")
            continue
        c.execute("RELEASE SAVEPOINT purchase_receipt")
        return
    raise RuntimeError("Workflow receipt contention exceeded its bounded retry budget")
