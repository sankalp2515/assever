"""Purchase routes in the existing gateway, using its KeyRing and principals."""

import hashlib
import os
from fastapi import APIRouter, Depends, Request, Header
from intentseal_core.purchase import service as actions
from intentseal_core.purchase.schemas import (
    ModelPurchase,
    Approval,
    Callback,
    Commit,
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
    EditScope,
)
from .security import Principal, require, human_only

router = APIRouter(tags=["purchase integrity"])


def actor(request: Request, p: Principal = require("project")):
    identity = p.name
    if p.agent:
        token = request.headers.get("x-api-key") or request.headers.get("authorization", "").removeprefix("Bearer ")
        identity = "agent:" + hashlib.sha256(token.encode()).hexdigest()[:24]
    tenant = "principal:" + hashlib.sha256((p.org + ":" + p.name).encode()).hexdigest()[:24]
    a = {"tenant": tenant, "actor": identity, "role": "agent" if p.agent else "human", "principal": p.name, "allow_lab": False}
    if p.agent:
        from intentseal_core.purchase.common import db, now

        with db() as c:
            c.execute(
                "INSERT INTO agent_principals VALUES(%s,%s,%s,%s,%s) ON CONFLICT(actor,tenant) DO UPDATE SET expires=excluded.expires",
                (identity, tenant, p.name, "gateway-keyring", now() + 3600),
            )
    request.state.purchase_actor = a
    return a


def human(request: Request, p: Principal = require("project")):
    human_only(p)
    return actor(request, p)


def evaluator(a=Depends(human)):
    actions.require(os.environ.get("LAB_ENABLED") == "1", "LAB_DISABLED", "The local safety lab is disabled.", 403)
    return a


@router.post("/v1/delegations/{wf}/purchase", status_code=201)
def attach_purchase(wf: str, request: Request, p: Principal = require("project")):
    from .delegate_api import owner_only
    from intentseal_core.purchase.integration import attach

    human_only(p)
    return attach(owner_only(request, wf, p), wf, actor(request, p))


@router.get("/v1/delegations/{wf}/purchase")
def purchase_for_workflow(wf: str, request: Request, p: Principal = require("project")):
    from .delegate_api import owner_only
    from intentseal_core.purchase.integration import binding

    owner_only(request, wf, p)
    linked = binding(wf)
    actions.require(linked, "NOT_FOUND", "This work order has no purchase annex.", 404)
    return {**actions.get_contract(linked["root"], actor(request, p)), "workflow_id": wf}


@router.get("/v1/purchases/contracts/{contract_id}")
def purchase_state(contract_id: str, a=Depends(actor)):
    return actions.get_contract(contract_id, a)


@router.post("/v1/purchases/contracts/{contract_id}/approve")
def approve_purchase(contract_id: str, data: Approval, request: Request, p: Principal = require("project")):
    from .delegate_api import owner_only
    from intentseal_core.purchase.integration import approve
    from intentseal_core.purchase.common import db

    human_only(p)
    a = actor(request, p)
    # Check root ownership before revealing the associated workflow.
    actions.get_contract(contract_id, a)
    with db() as c:
        linked = c.execute("SELECT workflow FROM workflow_bindings WHERE root=%s", (contract_id,)).fetchone()
    actions.require(linked, "NOT_FOUND", "Purchase is not attached to a work order.", 404)
    return approve(owner_only(request, linked["workflow"], p), contract_id, data, a)


@router.get("/v1/purchases/identity")
def identity(a=Depends(actor)):
    return {"actor_id": a["actor"], "tenant_id": a["tenant"], "role": a["role"]}


@router.get("/v1/purchases/work-orders")
def work_orders(a=Depends(human)):
    from intentseal_core.purchase.common import db

    with db() as c:
        return c.execute(
            "SELECT w.workflow,w.root,p.state,(SELECT count(*) FROM exceptions e WHERE e.root=p.id AND e.state='PENDING' AND e.expires>extract(epoch from now())) pending FROM workflow_bindings w JOIN contracts p ON p.id=w.root WHERE p.tenant=%s AND p.owner=%s ORDER BY p.created DESC LIMIT 100",
            (a["tenant"], a["actor"]),
        ).fetchall()


def install(app):
    import httpx
    from fastapi.responses import JSONResponse
    from psycopg import OperationalError, InterfaceError
    from psycopg_pool import PoolTimeout
    from intentseal_core.purchase.runtime import Refusal, event, root
    from intentseal_core.purchase.common import db
    from intentseal_core.purchase.boundaries import RequestLimit

    app.add_middleware(RequestLimit, prefix="/v1/purchases/")

    async def refusal(request, exc):
        a = getattr(request.state, "purchase_actor", None)
        rid = request.path_params.get("contract_id") or getattr(request.state, "purchase_root", None)
        if a:
            try:
                with db() as c:
                    if not rid:
                        for parameter, table in [("operation_id", "operations"), ("proposal_id", "proposals")]:
                            identifier = request.path_params.get(parameter)
                            if identifier:
                                record = c.execute("SELECT root FROM " + table + " WHERE id=%s", (identifier,)).fetchone()
                                rid = record["root"] if record else None
                    if rid:
                        root(c, rid, a)
                        event(
                            c,
                            rid,
                            "REFUSED",
                            {"code": exc.code, "actor": a["actor"], "request_id": request.headers.get("x-request-id", "")[:64]},
                        )
            except (Refusal, OperationalError, InterfaceError, PoolTimeout):
                pass
        return JSONResponse({"code": exc.code, "message": exc.message, "retryable": False}, status_code=exc.status)

    async def unavailable(request, exc):
        return JSONResponse(
            {
                "code": "DEPENDENCY_UNAVAILABLE",
                "message": "A required dependency is unavailable. No purchase outcome is inferred.",
                "retryable": True,
            },
            status_code=503,
        )

    app.add_exception_handler(Refusal, refusal)
    for error in (OperationalError, InterfaceError, PoolTimeout, httpx.HTTPError):
        app.add_exception_handler(error, unavailable)
    app.include_router(router)


@router.get("/v1/purchases/catalog")
def catalog(a=Depends(actor)):
    return actions.catalog(a)


@router.post("/v1/purchases/contracts/{contract_id}/review-nonce")
def review_nonce(contract_id: str, a=Depends(human)):
    return actions.review_nonce(contract_id, a)


@router.post("/v1/purchases/contracts/{contract_id}/edit")
def edit_scope(contract_id: str, data: EditScope, a=Depends(human)):
    return actions.edit_scope(contract_id, data, a)


@router.post("/v1/purchases/contracts/{contract_id}/revoke")
def revoke(contract_id: str, data: Revoke, a=Depends(human)):
    return actions.revoke(contract_id, data, a)


@router.post("/v1/purchases/contracts/{contract_id}/narrow")
def narrow(contract_id: str, data: Narrow, a=Depends(human)):
    return actions.narrow(contract_id, data, a)


@router.post("/v1/purchases/grants", status_code=201)
def grant(data: GrantInput, request: Request, a=Depends(actor)):
    request.state.purchase_root = data.root_id
    return actions.grant(data, a)


@router.post("/v1/purchases/quotes", status_code=201)
def quote(data: QuoteInput, request: Request, a=Depends(actor)):
    request.state.purchase_root = data.root_id
    return actions.quote(data, a)


@router.post("/v1/purchases/proposals", status_code=201)
def propose(data: Proposal, request: Request, a=Depends(actor)):
    request.state.purchase_root = data.root_id
    return actions.propose(data, a)


@router.post("/v1/purchases/proposals/{proposal_id}/prepare", status_code=201)
def prepare(proposal_id: str, data: Prepare, a=Depends(actor)):
    return actions.prepare(proposal_id, data, a)


@router.post("/v1/purchases/operations/{operation_id}/commit", status_code=202)
def commit(operation_id: str, data: Commit, a=Depends(actor)):
    return actions.commit(operation_id, data, a)


@router.get("/v1/purchases/operations/{operation_id}")
def operation(operation_id: str, a=Depends(actor)):
    return actions.operation(operation_id, a)


@router.post("/v1/purchases/operations/{operation_id}/refund-notice")
def refund_notice(operation_id: str, a=Depends(human)):
    return actions.refund_notice(operation_id, a)


@router.post("/v1/purchases/operations/{operation_id}/cancel")
def cancel(operation_id: str, a=Depends(human)):
    return actions.cancel(operation_id, a)


@router.post("/v1/purchases/operations/{operation_id}/reconcile", status_code=202)
def reconcile(operation_id: str, data: Reconcile, a=Depends(human)):
    return actions.reconcile(operation_id, data, a)


@router.get("/v1/purchases/contracts/{contract_id}/events")
def events(contract_id: str, cursor: int = 0, a=Depends(actor)):
    return actions.events(contract_id, cursor, a)


@router.get("/v1/purchases/contracts/{contract_id}/evidence")
def evidence(contract_id: str, a=Depends(human)):
    return actions.evidence(contract_id, a)


@router.post("/v1/purchases/exceptions", status_code=201)
def exception_request(data: ExceptionRequest, request: Request, a=Depends(actor)):
    request.state.purchase_root = data.root_id
    return actions.exception_request(data, a)


@router.post("/v1/purchases/exceptions/{exception_id}/decide")
def exception_decide(exception_id: str, data: ExceptionDecision, a=Depends(human)):
    return actions.exception_decide(exception_id, data, a)


@router.post("/v1/purchases/exceptions/{exception_id}/review-nonce")
def exception_review_nonce(exception_id: str, a=Depends(human)):
    return actions.exception_review_nonce(exception_id, a)


@router.post("/v1/purchases/callbacks/{adapter}", status_code=202)
def callback(adapter: str, data: Callback, x_callback_signature: str = Header(default="")):
    return actions.callback(adapter, data, x_callback_signature)


@router.post("/v1/purchases/contracts/{contract_id}/agent-purchase", status_code=202)
def agent_purchase(contract_id: str, data: QuoteInput, a=Depends(human)):
    return actions.agent_purchase(contract_id, data, a)


@router.get("/v1/purchases/metrics")
def metrics(a=Depends(human)):
    return actions.metrics(a)


@router.post("/v1/purchases/lab/runs", status_code=202)
def lab_run(data: LabInput, a=Depends(evaluator)):
    import httpx

    with httpx.Client(timeout=120, trust_env=False) as client:
        response = client.post(
            os.environ["LAB_URL"] + "/run",
            headers={"X-Lab-Key": os.environ["LAB_KEY"]},
            json={"spec": data.model_dump(), "tenant": a["tenant"], "actor": a["actor"]},
        )
        response.raise_for_status()
        return response.json()


@router.get("/v1/purchases/lab/runs")
def lab_runs(a=Depends(evaluator)):
    return actions.lab_runs(a)


@router.get("/v1/purchases/lab/runs/{run_id}")
def lab_result(run_id: str, a=Depends(evaluator)):
    return actions.lab_result(run_id, a)


@router.get("/v1/purchases/lab/manifest")
def manifest(a=Depends(evaluator)):
    return actions.manifest(a)


@router.post("/v1/purchases/contracts/{contract_id}/model-purchase", status_code=202)
async def model_purchase(contract_id: str, data: ModelPurchase, request: Request, p: Principal = require("project")):
    import asyncio
    from .delegate_api import owner_only
    from intentseal_core.purchase.common import db
    from intentseal_core.purchase.runtime import root, event

    human_only(p)
    a = actor(request, p)
    actions.get_contract(contract_id, a)
    with db() as c:
        linked = c.execute("SELECT workflow FROM workflow_bindings WHERE root=%s", (contract_id,)).fetchone()
    actions.require(linked, "WORKFLOW_BINDING", "Model purchase requires an existing work order.")
    svc = owner_only(request, linked["workflow"], p)
    screened = await svc.read(
        linked["workflow"], "merchant-interaction", data.seller_text or "No seller message.", "Synthetic seller message"
    )
    with db() as c:
        root(c, contract_id, a)
        event(
            c,
            contract_id,
            "READ_SCREENED",
            {"workflow_id": linked["workflow"], "receipt": screened["receipt"], "flagged": screened["flagged"]},
        )
    proposal = data.model_copy(update={"seller_text": screened.get("content") or "Seller message withheld by read screening."})
    return await asyncio.to_thread(actions.model_purchase, contract_id, proposal, a)


@router.get("/v1/purchases/model-runs")
def model_run_history(a=Depends(human)):
    return actions.model_run_history(a)
