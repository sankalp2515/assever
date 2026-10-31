"""Bind the purchase annex to the original delegation and confirmation transaction."""

import json
from dataclasses import replace
from .common import db, now, digest, jsonb
from .runtime import require, root, snapshot
from .service import create_draft, approve_in
from ..delegate.receipts import chain_hash
from ..delegate.model import GOVERNED


def binding(workflow):
    with db() as c:
        return c.execute("SELECT * FROM workflow_bindings WHERE workflow=%s", (workflow,)).fetchone()


def attach(svc, workflow, actor):
    require(
        svc.policy.purchase_profile == "kirana-v1" and any(tool.action == "purchase" for tool in svc.policy.tools.values()),
        "BUSINESS_POLICY",
        "This business has not registered the supported purchase profile.",
        403,
    )
    cur = svc.contract(workflow)
    with db() as c:
        c.execute("SELECT id FROM public.delegate_workflows WHERE id=%s FOR UPDATE", (workflow,))
        previous = c.execute("SELECT * FROM workflow_bindings WHERE workflow=%s", (workflow,)).fetchone()
        if previous:
            return {**snapshot(c, root(c, previous["root"], actor)), "workflow_id": workflow}
        require(cur.status == "draft", "ALREADY_CONFIRMED", "Attach the purchase annex before confirming this work order.")
        result = create_draft(c, actor, cur.request)
        policy = svc.policy.model_dump()
        c.execute(
            "INSERT INTO workflow_bindings(root,workflow,contract_hash,created,policy_snapshot,policy_digest) VALUES(%s,%s,%s,%s,%s,%s)",
            (result["id"], workflow, cur.hash, now(), jsonb(policy), digest(policy)),
        )
        return {**result, "workflow_id": workflow}


def approve(svc, contract_id, data, actor):
    with db() as c:
        row = root(c, contract_id, actor)
        linked = c.execute("SELECT * FROM workflow_bindings WHERE root=%s", (contract_id,)).fetchone()
        require(linked, "WORKFLOW_BINDING", "Purchase is not attached to a delegation.")
        workflow = linked["workflow"]
        c.execute("SELECT id FROM public.delegate_workflows WHERE id=%s FOR UPDATE", (workflow,))
        cur = svc.contract(workflow)
        require(
            cur.hash == linked["contract_hash"] and row["state"] == "DRAFT",
            "APPROVAL_STALE",
            "Refresh the work order before approving.",
        )
        # Original human review and annex activation commit together in the same DB.
        clauses = tuple(cl for cl in cur.clauses if cl.verified or cl.effect == "prohibit" or cl.action not in GOVERNED)
        confirmed = replace(cur, version=cur.version + 1, parent=cur.hash, status="confirmed", clauses=clauses)
        c.execute(
            "INSERT INTO public.delegate_contracts VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                confirmed.id,
                confirmed.version,
                workflow,
                confirmed.hash,
                confirmed.parent,
                confirmed.status,
                json.dumps(confirmed.as_dict(svc.policy), ensure_ascii=False),
                confirmed.created_at,
            ),
        )
        c.execute("UPDATE workflow_bindings SET contract_hash=%s WHERE root=%s", (confirmed.hash, contract_id))
        result = approve_in(c, contract_id, data, actor)
        last = c.execute(
            "SELECT seq,hash FROM public.delegate_receipts WHERE workflow_id=%s ORDER BY seq DESC LIMIT 1", (workflow,)
        ).fetchone()
        seq = last["seq"] + 1 if last else 1
        receipt = {
            "workflow_id": workflow,
            "seq": seq,
            "rid": f"R-{seq}",
            "kind": "contract",
            "agent": "employee",
            "tool": "",
            "decision": "confirmed",
            "reason": "Human confirmed the work order and exact purchase annex",
            "data": {"hash": confirmed.hash, "purchase_root": contract_id, "purchase_digest": data.hash},
            "created": round(now(), 3),
        }
        prev = last["hash"] if last else ""
        hashed = chain_hash(prev, receipt)
        c.execute(
            "INSERT INTO public.delegate_receipts VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                workflow,
                seq,
                receipt["rid"],
                "contract",
                "employee",
                "",
                "confirmed",
                receipt["reason"],
                json.dumps(receipt["data"]),
                receipt["created"],
                prev,
                hashed,
            ),
        )
        return {**result, "workflow_id": workflow}
