"""Application operations using Core's ledger; identity is supplied by the existing gateway.

No HTTP application, enrollment, cookies or parallel authentication system lives here.
"""

import hashlib
import hmac
import os
import re
import secrets
import time
import httpx
from .common import CATALOG, db, default_scope, digest, jsonb, now, uid
from .runtime import (
    Refusal,
    active,
    event,
    grant_signature,
    projection,
    require,
    reserve,
    root,
    snapshot,
    validate_scope,
    business_scope,
)
from .schemas import (
    EditScope,
    ModelPurchase,
    Approval,
    Callback,
    Commit,
    Draft,
    ExceptionDecision,
    ExceptionRequest,
    GrantInput,
    LabInput,
    Narrow,
    Prepare,
    Proposal,
    QuoteInput,
    Reconcile,
    Revoke,
)
from .worker import provider, reconcile_one


def create_agent(a):
    # Ephemeral role identities share the existing authenticated delegation owner;
    # they are never enrolled as a second browser or API session.
    human(a)
    actor_id = uid("role")
    with db() as c:
        c.execute(
            "INSERT INTO agent_principals VALUES(%s,%s,%s,%s,%s)",
            (actor_id, a["tenant"], a["actor"], "workflow-role", now() + 86400),
        )
    return {"actor_id": actor_id}


def human(a):
    require(a and a["role"] == "human", "HUMAN_REQUIRED", "This action requires the work-order owner.", 403)
    return a


def create_draft(c, a, text, control="adaptive"):
    scope, contract_id, nonce = (default_scope(), uid("purchase"), secrets.token_urlsafe(24))
    normalized = text.lower()
    grounded = bool(
        re.search("\\b5\\s*kg\\b", normalized)
        and re.search("\\b2\\s*(x\\s*)?1\\s*l\\b", normalized)
        and re.search("\\b1500\\b", normalized)
    )
    c.execute(
        "INSERT INTO contracts(id,tenant,owner,state,scope,digest,nonce_hash,created,control) VALUES(%s,%s,%s,'DRAFT',%s,%s,%s,%s,%s)",
        (contract_id, a["tenant"], a["actor"], jsonb(scope), digest(scope), digest(nonce), now(), control),
    )
    for line in scope["lines"]:
        c.execute("INSERT INTO demand_lines VALUES(%s,%s,%s)", (uid("demand"), contract_id, line))
    c.execute("INSERT INTO slots(id,root) VALUES(%s,%s)", (uid("slot"), contract_id))
    event(
        c,
        contract_id,
        "DRAFT",
        {
            "mode": "constrained_profile",
            "source_text": text,
            "unresolved": [] if grounded else ["Review every structured constraint; free prose does not activate authority."],
        },
    )
    row = c.execute("SELECT * FROM contracts WHERE id=%s", (contract_id,)).fetchone()
    return {
        **snapshot(c, row),
        "human_confirmation_nonce": nonce,
        "grounding": {
            "mode": "constrained_profile",
            "source": text,
            "requires_structured_review": True,
            "recognized_profile": grounded,
        },
    }


def draft(data: Draft, a=None):
    human(a)
    with db() as c:
        return create_draft(c, a, data.request_text)


def list_contracts(a=None):
    with db() as c:
        rows = c.execute(
            "SELECT id,state,created,version FROM contracts WHERE tenant=%s AND owner=%s AND is_lab=false ORDER BY created DESC",
            (a["tenant"], a["actor"]),
        ).fetchall()
    return rows


def get_contract(contract_id: str, a=None):
    with db() as c:
        return snapshot(c, root(c, contract_id, a, False))


def approve(contract_id: str, data: Approval, a=None):
    with db() as c:
        return approve_in(c, contract_id, data, a)


def approve_in(c, contract_id, data, a):
    human(a)
    row = root(c, contract_id, a)
    business_scope(row, row["scope"])
    require(
        row["state"] == "DRAFT" and row["version"] == data.version and (row["digest"] == data.hash),
        "APPROVAL_STALE",
        "The displayed purchase changed.",
    )
    require(
        row["nonce_hash"] == digest(data.human_confirmation_nonce) and data.accepted_fields == row["scope"],
        "APPROVAL_BINDING",
        "Confirm the exact displayed fields.",
    )
    validate_scope(data.accepted_fields)
    approval = {"actor": a["actor"], "digest": data.hash, "version": data.version, "timestamp": now(), "nonce_consumed": True}
    c.execute("UPDATE contracts SET state='ACTIVE',approved=%s,nonce_hash=NULL WHERE id=%s", (jsonb(approval), contract_id))
    event(c, contract_id, "APPROVED", approval)
    return snapshot(c, root(c, contract_id, a))


def review_nonce(contract_id: str, a=None):
    human(a)
    with db() as c:
        row = root(c, contract_id, a)
        require(row["state"] == "DRAFT", "NOT_DRAFT", "Only draft purchases need a new review nonce.")
        nonce = secrets.token_urlsafe(24)
        c.execute("UPDATE contracts SET nonce_hash=%s WHERE id=%s", (digest(nonce), contract_id))
        return {**snapshot(c, row), "human_confirmation_nonce": nonce}


def edit_scope(contract_id: str, data: EditScope, a=None):
    human(a)
    with db() as c:
        row = root(c, contract_id, a)
        require(
            row["state"] == "DRAFT" and row["version"] == data.expected_version,
            "DRAFT_STALE",
            "Only the current draft can be edited.",
        )
        validate_scope(data.scope)
        business_scope(row, data.scope)
        nonce = secrets.token_urlsafe(24)
        c.execute(
            "UPDATE contracts SET scope=%s,digest=%s,version=version+1,nonce_hash=%s WHERE id=%s",
            (jsonb(data.scope), digest(data.scope), digest(nonce), contract_id),
        )
        event(c, contract_id, "DRAFT_EDITED", {"actor": a["actor"], "digest": digest(data.scope), "version": row["version"] + 1})
        return {**snapshot(c, root(c, contract_id, a)), "human_confirmation_nonce": nonce}


def revoke(contract_id: str, data: Revoke, a=None):
    human(a)
    with db() as c:
        row = root(c, contract_id, a)
        require(row["epoch"] == data.expected_epoch and row["state"] == "ACTIVE", "EPOCH_STALE", "Refresh current authority.")
        c.execute("UPDATE contracts SET state='REVOKED',epoch=epoch+1 WHERE id=%s", (contract_id,))
        event(
            c,
            contract_id,
            "REVOKED",
            {"reason": data.reason, "boundary": "New admissions stop. Already dispatched effects require reconciliation."},
        )
        return snapshot(c, root(c, contract_id, a))


def narrow(contract_id: str, data: Narrow, a=None):
    human(a)
    with db() as c:
        row = root(c, contract_id, a)
        active(row)
        require(row["version"] == data.expected_version, "VERSION_STALE", "Refresh current purchase.")
        scope = {**row["scope"], **data.allowed_changes}
        validate_scope(scope)
        old = row["scope"]
        require(
            scope["max_paise"] <= old["max_paise"]
            and scope["max_purchases"] <= old["max_purchases"]
            and (scope["expires_at"] <= old["expires_at"]),
            "EXPANSION",
            "Narrowing cannot expand authority.",
        )
        require(
            set(scope["merchants"]) <= set(old["merchants"]) and set(scope["disclosure_fields"]) <= set(old["disclosure_fields"]),
            "EXPANSION",
            "Narrowing cannot expand suppliers or disclosure.",
        )
        for name, line in scope["lines"].items():
            require(
                line["max_units"] <= old["lines"][name]["max_units"] and set(line["skus"]) <= set(old["lines"][name]["skus"]),
                "EXPANSION",
                "Narrowing cannot expand quantities or equivalents.",
            )
        history = row["history"] + [{"version": row["version"], "scope": old, "approved": row["approved"]}]
        c.execute(
            "UPDATE contracts SET scope=%s,digest=%s,version=version+1,epoch=epoch+1,history=%s WHERE id=%s",
            (jsonb(scope), digest(scope), jsonb(history), contract_id),
        )
        event(
            c,
            contract_id,
            "NARROWED",
            {"old_scope": old, "new_scope": scope, "actor": a["actor"], "previous_obligations_retained": True},
        )
        return snapshot(c, root(c, contract_id, a))


def grant(data: GrantInput, a=None):
    with db() as c:
        row = root(c, data.root_id, a)
        active(row)
        ids = {r["id"]: r["name"] for r in c.execute("SELECT * FROM demand_lines WHERE root=%s", (data.root_id,)).fetchall()}
        require(set(data.demand_lines) <= ids.keys() and bool(data.demand_lines), "GRANT_SCOPE", "Unknown demand line.", 403)
        require(now() < data.expires_at <= row["scope"]["expires_at"], "GRANT_EXPIRY", "Child grant expires beyond root.", 403)
        if data.parent_id:
            parent = c.execute("SELECT * FROM grants WHERE id=%s AND root=%s", (data.parent_id, data.root_id)).fetchone()
            require(
                parent is not None and parent["epoch"] == row["epoch"] and (parent["expires"] > now()),
                "PARENT_STALE",
                "Parent grant is stale.",
                403,
            )
            require(
                a["role"] == "human" or parent["actor"] == a["actor"],
                "GRANT_IDENTITY",
                "The parent grant belongs to another actor.",
                403,
            )
            require(
                set(data.operations) <= set(parent["scope"]["operations"])
                and {ids[x] for x in data.demand_lines} <= set(parent["scope"]["lines"])
                and (data.expires_at <= parent["expires"]),
                "GRANT_EXPANSION",
                "Child scope exceeds parent.",
                403,
            )
        else:
            require(a["role"] == "human", "HUMAN_REQUIRED", "An agent requires a parent grant.", 403)
        recipient = c.execute(
            "SELECT 1 FROM agent_principals WHERE tenant=%s AND actor=%s AND owner=%s AND expires>%s",
            (a["tenant"], data.actor_id, row["owner"], now()),
        ).fetchone()
        require(recipient is not None, "GRANT_RECIPIENT", "Register the agent in this workspace.", 403)
        body = {
            "id": uid("grant"),
            "root": row["id"],
            "parent": data.parent_id,
            "actor": data.actor_id,
            "audience": data.audience,
            "epoch": row["epoch"],
            "expires": data.expires_at,
            "scope": {"lines": sorted((ids[x] for x in data.demand_lines)), "operations": sorted(data.operations)},
        }
        sig = grant_signature(body, "V1")
        c.execute(
            "INSERT INTO grants VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                body["id"],
                body["root"],
                body["parent"],
                body["actor"],
                body["audience"],
                body["epoch"],
                body["expires"],
                jsonb(body["scope"]),
                "V1",
                sig,
            ),
        )
        event(c, row["id"], "GRANT_ISSUED", {"grant_id": body["id"], "actor_id": data.actor_id, "shared_root": True})
        return {**body, "key_version": "V1", "signature": sig}


def quote(data: QuoteInput, a=None):
    with db() as c:
        row = root(c, data.root_id, a)
        active(row)
        q = provider("POST", "/quotes", json=data.model_dump())
        require(digest(q["body"]) == q["digest"], "QUOTE_DIGEST", "Supplier quote is inconsistent.")
        body = q["body"]
        c.execute(
            "INSERT INTO quotes VALUES(%s,%s,%s,%s,%s,%s)",
            (body["id"], a["tenant"], row["id"], jsonb(body), q["digest"], body["expires_at"]),
        )
        event(c, row["id"], "QUOTE", {"quote_id": body["id"], "digest": q["digest"], "merchant_id": data.merchant_id})
        return q


def propose(data: Proposal, a=None):
    with db() as c:
        row = root(c, data.root_id, a)
        active(row)
        body, proposal_id = (data.model_dump(), uid("proposal"))
        proposal = {"body": body, "grant_id": data.grant_id}
        projection(c, row, proposal, a)
        c.execute(
            "INSERT INTO proposals VALUES(%s,%s,%s,%s,%s,%s)",
            (proposal_id, row["id"], a["actor"], data.grant_id, jsonb(body), digest(body)),
        )
        event(c, row["id"], "PROPOSED", {"proposal_id": proposal_id, "actor": a["actor"], "digest": digest(body)})
        return {"id": proposal_id, "digest": digest(body)}


def prepare(proposal_id: str, data: Prepare, a=None):
    with db() as c:
        p = c.execute("SELECT * FROM proposals WHERE id=%s", (proposal_id,)).fetchone()
        require(p is not None, "NOT_FOUND", "Proposal not found.", 404)
        row = root(c, p["root"], a)
        require(p["actor"] == a["actor"], "ACTOR_BINDING", "Another actor created this proposal.", 403)
        active(row)
        require(
            row["version"] == data.expected_contract_version and p["digest"] == data.proposal_digest,
            "PROPOSAL_STALE",
            "The preview binding changed.",
        )
        old = c.execute("SELECT * FROM operations WHERE proposal=%s", (proposal_id,)).fetchone()
        if old:
            return old
        effect, _ = projection(c, row, p, a)
        op_id = uid("op")
        slot = c.execute("SELECT id FROM slots WHERE root=%s ORDER BY generation LIMIT 1", (row["id"],)).fetchone()["id"]
        c.execute(
            "INSERT INTO operations(id,root,slot,proposal,actor,grant_id,effect,digest,contract_version,epoch,state,created,updated) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PREPARED',%s,%s)",
            (
                op_id,
                row["id"],
                slot,
                proposal_id,
                a["actor"],
                p["grant_id"],
                jsonb(effect),
                digest(effect),
                row["version"],
                row["epoch"],
                now(),
                now(),
            ),
        )
        event(c, row["id"], "PREPARED", {"operation_id": op_id, "digest": digest(effect), "reserved_paise": 0})
        return c.execute("SELECT * FROM operations WHERE id=%s", (op_id,)).fetchone()


def scoped_op(c, operation_id, a):
    op = c.execute("SELECT * FROM operations WHERE id=%s", (operation_id,)).fetchone()
    require(op is not None, "NOT_FOUND", "Operation not found.", 404)
    row = root(c, op["root"], a)
    op = c.execute("SELECT * FROM operations WHERE id=%s", (operation_id,)).fetchone()
    require(a["role"] != "agent" or op["actor"] == a["actor"], "NOT_FOUND", "Operation not found.", 404)
    return (row, op)


def commit(operation_id: str, data: Commit, a=None):
    readiness_start = time.perf_counter()
    provider("GET", "/health/ready")
    readiness_ms = (time.perf_counter() - readiness_start) * 1000
    admission_start = time.perf_counter()
    with db() as c:
        acquired = time.perf_counter()
        row, op = scoped_op(c, operation_id, a)
        require(op["digest"] == data.prepared_digest, "PAYLOAD_CONFLICT", "The prepared purchase changed.")
        bound = time.perf_counter()
        if op["state"] == "PREPARED":
            reserve(c, row, op, a)
        result = c.execute("SELECT * FROM operations WHERE id=%s", (operation_id,)).fetchone()
        sql_end = time.perf_counter()
    return {
        **result,
        "timings": {
            "core_admission_ms": round((time.perf_counter() - admission_start) * 1000, 3),
            "provider_readiness_ms": round(readiness_ms, 3),
            "pool_wait_ms": round((acquired - admission_start) * 1000, 3),
            "binding_and_lock_ms": round((bound - acquired) * 1000, 3),
            "reservation_sql_ms": round((sql_end - bound) * 1000, 3),
            "commit_flush_ms": round((time.perf_counter() - sql_end) * 1000, 3),
        },
    }


def operation(operation_id: str, a=None):
    with db() as c:
        _, op = scoped_op(c, operation_id, a)
        return op


def refund_notice(operation_id: str, a=None):
    human(a)
    with db() as c:
        row, op = scoped_op(c, operation_id, a)
        require(op["state"] == "CONFIRMED", "NOT_CAPTURED", "Only captured synthetic effects can be refunded.")
        observation = provider("POST", "/refund/" + operation_id)
        event(
            c, row["id"], "REFUND_OBSERVED", {"operation_id": operation_id, "notice": observation, "entitlement_restored": False}
        )
    return observation


def cancel(operation_id: str, a=None):
    human(a)
    with db() as c:
        row, op = scoped_op(c, operation_id, a)
        require(op["state"] == "RESERVED", "CANNOT_CANCEL", "Dispatched or uncertain work requires provider reconciliation.")
        box = c.execute("SELECT * FROM outbox WHERE operation=%s FOR UPDATE", (operation_id,)).fetchone()
        require(
            box["state"] == "PENDING" and box["generation"] == 0,
            "CANNOT_CANCEL",
            "A worker may already have sent this operation.",
        )
        from .runtime import settle

        settle(
            c,
            op,
            {
                "state": "CLOSED",
                "closure_barrier": True,
                "operation_id": operation_id,
                "reason": "fenced_unsent_local_cancellation",
            },
            "local-outbox-fence",
        )
        return {"state": "CLOSED_NO_EFFECT"}


def reconcile(operation_id: str, data: Reconcile, a=None):
    human(a)
    with db() as c:
        _, op = scoped_op(c, operation_id, a)
        require(op["revision"] == data.operation_version, "VERSION_STALE", "Refresh the operation before reconciliation.")
    reconcile_one(operation_id)
    return operation(operation_id, a)


def events(contract_id: str, cursor: int = 0, a=None):
    with db() as c:
        root(c, contract_id, a, False)
        rows = c.execute(
            "SELECT * FROM events WHERE root=%s AND sequence>%s ORDER BY sequence LIMIT 200", (contract_id, cursor)
        ).fetchall()
    return {"events": rows, "cursor": rows[-1]["sequence"] if rows else cursor}


def evidence(contract_id: str, a=None):
    human(a)
    with db() as c:
        row = root(c, contract_id, a)
        state = snapshot(c, row)
        observations = c.execute(
            "SELECT o.* FROM observations o JOIN operations p ON p.id=o.operation WHERE p.root=%s ORDER BY o.created",
            (contract_id,),
        ).fetchall()
        quotes = c.execute("SELECT * FROM quotes WHERE root=%s", (contract_id,)).fetchall()
        grants = c.execute("SELECT * FROM grants WHERE root=%s", (contract_id,)).fetchall()
        reservations = c.execute("SELECT * FROM reservations WHERE root=%s", (contract_id,)).fetchall()
        with httpx.Client(timeout=10, trust_env=False) as client:
            observed = client.get(
                os.environ["SINK_URL"] + "/observe/" + contract_id, headers={"X-Observer-Key": os.environ["OBSERVER_KEY"]}
            )
            observed.raise_for_status()
        bundle = {
            "schema_version": 1,
            "contract": state,
            "observations": observations,
            "quotes": quotes,
            "grants": grants,
            "reservations": reservations,
            "observer": observed.json(),
            "manifest": {
                "synthetic": True,
                "runtime_version": "1.1.0",
                "control": row["control"],
                "exported_at": now(),
                "provider_profiles": ["dedupe", "queryable", "opaque"],
            },
        }
        linked = c.execute("SELECT * FROM workflow_bindings WHERE root=%s", (contract_id,)).fetchone()
        bundle["manifest"]["integrated"] = bool(linked)
        bundle["manifest"]["workflow_receipts"] = bool(linked)
        if linked:
            import json
            from ..delegate.model import DelegationContract

            original = c.execute(
                "SELECT body FROM public.delegate_contracts WHERE workflow_id=%s ORDER BY version DESC LIMIT 1",
                (linked["workflow"],),
            ).fetchone()
            card = json.loads(original["body"])
            canonical = DelegationContract.from_dict(card)
            receipts = c.execute(
                "SELECT * FROM public.delegate_receipts WHERE workflow_id=%s ORDER BY seq", (linked["workflow"],)
            ).fetchall()
            for receipt in receipts:
                receipt["data"] = json.loads(receipt["data"] or "{}")
            principal = c.execute(
                "SELECT principal FROM public.delegate_principals WHERE workflow_id=%s", (linked["workflow"],)
            ).fetchone()
            bundle["work_order"] = {
                "binding": linked,
                "contract": card,
                "canonical_clauses": [cl.as_dict() for cl in canonical.clauses],
                "receipts": receipts,
                "principal": principal["principal"],
            }
        bundle["bundle_digest"] = digest(bundle)
    from .checker import verify

    return {"bundle": bundle, "verification": verify(bundle)}


def exception_request(data: ExceptionRequest, a=None):
    with db() as c:
        row = root(c, data.root_id, a)
        active(row)
        validate_scope(data.new_scope)
        business_scope(row, data.new_scope)
        ex_id, nonce = (uid("exception"), secrets.token_urlsafe(24))
        binding = digest({"effect": data.effect, "new_scope": data.new_scope, "version": row["version"]})
        c.execute(
            "INSERT INTO exceptions VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'PENDING',%s)",
            (
                ex_id,
                row["id"],
                jsonb(data.effect),
                binding,
                jsonb(row["scope"]),
                jsonb(data.new_scope),
                now() + 900,
                digest(nonce),
                row["version"],
            ),
        )
        event(c, row["id"], "EXCEPTION_REQUESTED", {"exception_id": ex_id, "digest": binding})
    return {"id": ex_id, "digest": binding, "nonce": nonce}


def exception_decide(exception_id: str, data: ExceptionDecision, a=None):
    human(a)
    with db() as c:
        ex = c.execute("SELECT * FROM exceptions WHERE id=%s", (exception_id,)).fetchone()
        require(ex is not None, "NOT_FOUND", "Exception not found.", 404)
        row = root(c, ex["root"], a)
        active(row)
        ex = c.execute("SELECT * FROM exceptions WHERE id=%s FOR UPDATE", (exception_id,)).fetchone()
        require(
            ex["state"] == "PENDING" and ex["expires"] > now() and (ex["version"] == row["version"]),
            "EXCEPTION_STALE",
            "The exception is used, expired or stale.",
        )
        require(
            ex["digest"] == data.expected_action_digest and ex["nonce_hash"] == digest(data.nonce),
            "EXCEPTION_BINDING",
            "Review the exact requested change.",
        )
        if data.approve:
            history = row["history"] + [{"version": row["version"], "scope": row["scope"], "approved": row["approved"]}]
            c.execute(
                "UPDATE contracts SET scope=%s,digest=%s,version=version+1,epoch=epoch+1,history=%s,approved=%s WHERE id=%s",
                (
                    jsonb(ex["new_scope"]),
                    digest(ex["new_scope"]),
                    jsonb(history),
                    jsonb({"actor": a["actor"], "exception": ex["id"], "digest": ex["digest"], "timestamp": now()}),
                    row["id"],
                ),
            )
        c.execute("UPDATE exceptions SET state=%s WHERE id=%s", ("USED" if data.approve else "REJECTED", exception_id))
        event(c, row["id"], "EXCEPTION_DECIDED", {"exception_id": exception_id, "approved": data.approve, "digest": ex["digest"]})
        return snapshot(c, root(c, row["id"], a))


def exception_review_nonce(exception_id: str, a=None):
    human(a)
    with db() as c:
        ex = c.execute("SELECT * FROM exceptions WHERE id=%s", (exception_id,)).fetchone()
        require(ex is not None, "NOT_FOUND", "Exception not found.", 404)
        row = root(c, ex["root"], a)
        active(row)
        require(
            ex["state"] == "PENDING" and ex["expires"] > now() and (ex["version"] == row["version"]),
            "EXCEPTION_STALE",
            "This change is used, expired or stale.",
        )
        nonce = secrets.token_urlsafe(24)
        c.execute("UPDATE exceptions SET nonce_hash=%s WHERE id=%s", (digest(nonce), exception_id))
        return {"id": exception_id, "nonce": nonce, "digest": ex["digest"]}


def callback(adapter: str, data: Callback, x_callback_signature: str = ""):
    from .common import canonical

    require(adapter == "owned-commerce-v1", "ADAPTER", "Unsupported adapter.", 422)
    expected = hmac.new(os.environ["CALLBACK_KEY"].encode(), canonical(data.model_dump()).encode(), hashlib.sha256).hexdigest()
    require(hmac.compare_digest(expected, x_callback_signature), "CALLBACK_SIGNATURE", "Callback authentication failed.", 401)
    require(abs(now() - data.timestamp) < 300, "CALLBACK_EXPIRED", "Callback timestamp expired.")
    with db() as c:
        row = c.execute("SELECT * FROM contracts WHERE id=%s FOR UPDATE", (data.root_id,)).fetchone()
        require(row and data.transaction_id == data.root_id, "CALLBACK_CORRELATION", "Unknown transaction.")
        op = c.execute("SELECT * FROM operations WHERE id=%s AND root=%s", (data.operation_id, data.root_id)).fetchone()
        require(
            op and op["effect"]["merchant_id"] == data.participant, "CALLBACK_CORRELATION", "Participant or order does not match."
        )
        hashed = digest(data.model_dump())
        old = c.execute(
            "SELECT * FROM callbacks WHERE source=%s AND message_id=%s", (data.participant, data.message_id)
        ).fetchone()
        if old:
            require(old["digest"] == hashed, "CALLBACK_CONFLICT", "A conflicting callback requires investigation.")
            return {"deduplicated": True}
        c.execute(
            "INSERT INTO callbacks VALUES(%s,%s,%s,%s,%s)",
            (data.participant, data.message_id, data.root_id, hashed, jsonb(data.model_dump())),
        )
        event(c, row["id"], "CALLBACK_UNTRUSTED", {"message_id": data.message_id, "body": data.body, "authority_changed": False})
    return {"accepted_as_observation": True, "authority_changed": False}


def agent_purchase(contract_id: str, data: QuoteInput, a=None):
    human(a)
    require(contract_id == data.root_id, "ROOT_BINDING", "Purchase IDs differ.")
    current = get_contract(contract_id, a)
    roles = []
    for name in ("planner", "merchant-interaction", "checkout"):
        registered = create_agent(a)
        scoped = {**a, "role": "agent", "actor": registered["actor_id"]}
        g = grant(
            GrantInput(
                root_id=contract_id,
                actor_id=scoped["actor"],
                demand_lines=[d["id"] for d in current["demand_lines"]],
                operations=["propose", "commit"] if name == "checkout" else ["propose"],
                expires_at=float(min(now() + 3600, current["scope"]["expires_at"])),
            ),
            a,
        )
        roles.append((name, scoped, g))
        with db() as c:
            root(c, contract_id, a)
            event(
                c,
                contract_id,
                "AGENT_ROLE",
                {"role": name, "actor_id": scoped["actor"], "mode": "deterministic_typed_planner", "grant_id": g["id"]},
            )
    q = quote(data, roles[1][1])
    lines = [
        {
            "demand_line_id": next((d["id"] for d in current["demand_lines"] if d["name"] == CATALOG[x["sku"]]["line"])),
            "sku": x["sku"],
            "quantity": x["quantity"],
            "unit": "pack" if CATALOG[x["sku"]]["unit"] == "g" else "bottle",
        }
        for x in q["body"]["lines"]
    ]
    _, checkout, g = roles[2]
    p = propose(
        Proposal(
            root_id=contract_id,
            grant_id=g["id"],
            merchant_id=data.merchant_id,
            checkout_ref=q["body"]["id"],
            lines=lines,
            total_paise=q["body"]["total_paise"],
            delivery_ref=current["scope"]["delivery_ref"],
        ),
        checkout,
    )
    op = prepare(p["id"], Prepare(expected_contract_version=current["version"], proposal_digest=p["digest"]), checkout)
    return commit(op["id"], Commit(prepared_digest=op["digest"]), checkout)


def ready():
    with db() as c:
        version = c.execute("SELECT max(version) AS version FROM schema_versions").fetchone()["version"]
    with httpx.Client(timeout=2, trust_env=False) as client:
        client.get(os.environ["SINK_URL"] + "/health/ready").raise_for_status()
    return {"ready": True, "schema_version": version, "synthetic": True}


def metrics(a=None):
    human(a)
    with db() as c:
        rows = c.execute(
            "SELECT o.state,count(*) AS count,COALESCE(sum(r.money),0) AS exposure_paise,min(o.created) AS oldest FROM operations o LEFT JOIN reservations r ON r.operation=o.id JOIN contracts p ON p.id=o.root WHERE p.tenant=%s GROUP BY o.state",
            (a["tenant"],),
        ).fetchall()
        queue = c.execute(
            "SELECT b.state,count(*) AS count,max(b.attempts) AS max_attempts FROM outbox b JOIN operations o ON o.id=b.operation JOIN contracts p ON p.id=o.root WHERE p.tenant=%s GROUP BY b.state",
            (a["tenant"],),
        ).fetchall()
    return {"operations": rows, "queue": queue, "schema_version": 1, "observed_at": now()}


def lab_run(data: LabInput, a=None):
    from .lab import run_cell

    return run_cell(data.model_dump(), a)


def lab_runs(a=None):
    with db() as c:
        return c.execute("SELECT * FROM lab_runs WHERE tenant=%s ORDER BY created DESC LIMIT 200", (a["tenant"],)).fetchall()


def lab_result(run_id: str, a=None):
    with db() as c:
        row = c.execute("SELECT * FROM lab_runs WHERE id=%s AND tenant=%s", (run_id, a["tenant"])).fetchone()
    require(row is not None, "NOT_FOUND", "Run not found.", 404)
    return row


def manifest(a=None):
    from .lab import manifest

    return manifest()


def model_purchase(contract_id: str, data: ModelPurchase, a=None):
    human(a)
    from .models import plan

    current = get_contract(contract_id, a)
    active(current)
    run_id = uid("modelrun")
    started = now()
    manifest = {
        "model_id": data.model_id,
        "seed": data.seed,
        "root_id": contract_id,
        "mode": "live_vertex_gemini" if data.model_id.startswith("gemini-") else "live_local_model",
        "entry_point": "seller_text",
    }
    result = {"error": None, "attempts": []}
    try:
        output = plan(data.model_id, data.seller_text, data.seed, scope=current["scope"])
        result["invocation"] = output
        proposed = output["plan"]
        with db() as c:
            root(c, contract_id, a)
            event(
                c,
                contract_id,
                "MODEL_PROPOSAL",
                {"run_id": run_id, "model_id": data.model_id, "plan": proposed, "request_digest": output["request_digest"]},
            )
        if proposed["request_customer_export"]:
            result["attempts"].append(
                {"refused": "DISCLOSURE_SCOPE", "message": "Unrelated customer export was refused; no disclosure ran."}
            )
            with db() as c:
                root(c, contract_id, a)
                event(
                    c, contract_id, "DISCLOSURE_REFUSED", {"run_id": run_id, "effect_count": 0, "source": "untrusted_model_plan"}
                )
        for index in range(proposed["basket_count"]):
            try:
                require(
                    proposed["delivery_ref"] == current["scope"]["delivery_ref"],
                    "DESTINATION",
                    "The model proposed an unapproved delivery address.",
                )
                op = agent_purchase(contract_id, QuoteInput(root_id=contract_id, merchant_id=proposed["merchant_id"]), a)
                result["attempts"].append({"operation_id": op["id"], "admitted": True})
            except (Refusal, ValueError) as exc:
                result["attempts"].append(
                    {"refused": getattr(exc, "code", "SCHEMA_INVALID"), "message": getattr(exc, "message", str(exc))[:200]}
                )
                with db() as c:
                    root(c, contract_id, a)
                    event(
                        c,
                        contract_id,
                        "REFUSED",
                        {
                            "run_id": run_id,
                            "attempt": index,
                            "code": getattr(exc, "code", "SCHEMA_INVALID"),
                            "source": "untrusted_model_plan",
                        },
                    )
    except Exception as exc:
        if hasattr(exc, "record"):
            result["invocation"] = exc.record
        result["error"] = {
            "type": type(exc).__name__,
            "code": getattr(exc, "code", "MODEL_INVOCATION_FAILED"),
            "message": getattr(exc, "message", "The explicitly selected model invocation failed; no fallback was used."),
        }
    result["duration_ms"] = round((now() - started) * 1000, 2)
    with db() as c:
        c.execute("INSERT INTO model_runs VALUES(%s,%s,%s,%s,%s)", (run_id, a["tenant"], jsonb(manifest), jsonb(result), now()))
    return {"id": run_id, "manifest": manifest, "result": result}


def model_run_history(a=None):
    human(a)
    with db() as c:
        return c.execute("SELECT * FROM model_runs WHERE tenant=%s ORDER BY created DESC LIMIT 50", (a["tenant"],)).fetchall()


def catalog(a=None):
    from .common import MERCHANTS

    return {"catalog": CATALOG, "merchants": MERCHANTS, "version": "kirana-v1", "synthetic": True}
