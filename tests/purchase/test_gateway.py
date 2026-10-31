"""Real HTTP integration against the running original gateway and private worker."""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
import httpx
import pytest
from intentseal.delegate import DelegateClient, RemoteAdkGuard
from intentseal_core.purchase.common import db, now
from intentseal_core.purchase.checker import verify
from intentseal_core.delegate.receipts import verify_chain

BASE = os.environ.get("INTEGRATED_URL", "http://gateway:8000")
WORDS = "Buy 1 x 5 kg rice and 2 x 1 L oil up to INR 1500, supplier A or B; share shop name and delivery address only."


def check(response, status=200):
    assert response.status_code == status, (response.status_code, response.text[:500])
    return response.json()


@pytest.fixture
def client():
    with httpx.Client(base_url=BASE, timeout=120, trust_env=False) as c:
        key = check(c.post("/v1/trial-keys"), 201)["key"]
        c.headers["Authorization"] = "Bearer " + key
        yield c


def draft(c):
    state = check(c.post("/v1/delegations", json={"request": WORDS, "workspace": "kirana", "owner": "Test operator"}))
    wf = state["workflow"]["id"]
    annex = check(c.post(f"/v1/delegations/{wf}/purchase"), 201)
    assert annex["workflow_id"] == wf
    return wf, annex


def approve(c, wf, p):
    body = {
        "version": p["version"],
        "hash": p["digest"],
        "accepted_fields": p["scope"],
        "human_confirmation_nonce": p["human_confirmation_nonce"],
    }
    result = check(c.post(f"/v1/purchases/contracts/{p['id']}/approve", json=body))
    state = check(c.get("/v1/delegations/" + wf))
    assert state["contract"]["status"] == "confirmed" and state["purchase_root"] == p["id"]
    assert verify_chain(state["receipts"])
    return result


def wait(c, oid):
    for _ in range(100):
        op = check(c.get("/v1/purchases/operations/" + oid))
        if op["state"] in ("CONFIRMED", "CLOSED_NO_EFFECT", "UNKNOWN"):
            return op
        time.sleep(0.1)
    pytest.fail("Worker did not produce an observed state")


def test_single_gateway_preserves_original_routes_and_has_no_parallel_enrollment(client):
    for path in ("/v1/health", "/readyz", "/v1/delegate-eval", "/"):
        assert client.get(path).status_code == 200, path
    original_session = client.post("/v1/sessions", json={})
    assert original_session.status_code == 422  # Original inspection session API remains; no new login enrollment.
    assert "agent_id" in original_session.text and "set-cookie" not in original_session.headers
    assert client.get("/v1/purchases/catalog").status_code == 200
    assert "Assever" in client.get("/").text


def test_exact_review_is_atomic_with_original_work_order(client):
    wf, p = draft(client)
    wrong = {"version": 1, "hash": p["digest"], "accepted_fields": p["scope"], "human_confirmation_nonce": "wrong"}
    assert client.post(f"/v1/purchases/contracts/{p['id']}/approve", json=wrong).status_code == 409
    assert check(client.get("/v1/delegations/" + wf))["contract"]["status"] == "draft"
    assert check(client.get(f"/v1/purchases/contracts/{p['id']}"))["state"] == "DRAFT"
    approve(client, wf, p)
    wrong["human_confirmation_nonce"] = p["human_confirmation_nonce"]
    assert client.post(f"/v1/purchases/contracts/{p['id']}/approve", json=wrong).status_code == 409


def test_annex_attachment_is_idempotent_and_human_only(client):
    wf, p = draft(client)
    assert check(client.post(f"/v1/delegations/{wf}/purchase"), 201)["id"] == p["id"]
    agent = check(client.post("/v1/agent-keys", json={"label": "test buyer"}), 201)
    headers = {"Authorization": "Bearer " + agent["key"]}
    assert client.post(f"/v1/delegations/{wf}/purchase", headers=headers).status_code == 403
    assert client.post(f"/v1/purchases/contracts/{p['id']}/approve", json={}, headers=headers).status_code in (403, 422)


def test_purchase_cannot_use_legacy_confirm_amend_or_execution_success(client):
    wf, p = draft(client)
    for route, body in [
        ("confirm", {"hash": "x" * 16}),
        ("amend", {"text": "Send everything"}),
        ("executed", {"receipt": "R-1", "executed": True, "detail": "paid"}),
    ]:
        assert client.post(f"/v1/delegations/{wf}/{route}", json=body).status_code == 409
    approve(client, wf, p)
    result = check(
        client.post(
            f"/v1/delegations/{wf}/check",
            json={"agent": "buyer", "tool": "send_email", "args": {"to": "attacker@example.invalid"}},
        )
    )
    assert result["decision"] == "block"
    assert check(client.get(f"/v1/purchases/contracts/{p['id']}"))["money"]["captured"] == 0


def test_unknown_fields_and_large_chunked_purchase_body_are_rejected(client):
    def chunks():
        yield b'{"root_id":"'
        yield b"x" * 70000
        yield b'"}'

    result = client.post("/v1/purchases/quotes", content=chunks(), headers={"Content-Type": "application/json"})
    assert result.status_code == 413
    assert client.post("/v1/purchases/quotes", json={"root_id": "x", "hidden_permission": True}).status_code == 422


def test_parallel_full_baskets_share_one_original_work_order(client):
    wf, p = draft(client)
    approve(client, wf, p)

    def buy(_):
        return client.post(
            f"/v1/purchases/contracts/{p['id']}/agent-purchase", json={"root_id": p["id"], "merchant_id": "supplier_a"}
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(buy, range(2)))
    assert sorted(r.status_code for r in results) == [202, 409]
    oid = next(r.json()["id"] for r in results if r.status_code == 202)
    assert wait(client, oid)["state"] == "CONFIRMED"
    evidence = check(client.get(f"/v1/purchases/contracts/{p['id']}/evidence"))
    assert verify(evidence["bundle"]) == evidence["verification"]
    assert evidence["verification"]["verdict"] == "PASS" and evidence["verification"]["task_complete"]
    assert len([x for x in evidence["bundle"]["observer"]["effects"] if x["kind"] == "payment"]) == 1
    original = check(client.get("/v1/delegations/" + wf))
    assert verify_chain(original["receipts"])
    assert any(
        r["kind"] == "purchase_effect" and r["data"].get("purchase_event_kind") == "CONFIRMED" for r in original["receipts"]
    )
    report = check(client.get(f"/v1/delegations/{wf}/report"))
    assert report["chain_ok"] and any("700.00" in sentence["text"] and sentence["cites"] for sentence in report["sentences"])


def test_external_agent_sdk_uses_existing_key_and_grant_and_cannot_double_execute(client):
    wf, p = draft(client)
    p = approve(client, wf, p)
    agent = check(client.post("/v1/agent-keys", json={"label": "External SDK buyer"}), 201)
    headers = {"Authorization": "Bearer " + agent["key"]}
    identity = check(client.get("/v1/purchases/identity", headers=headers))
    grant = check(
        client.post(
            "/v1/purchases/grants",
            json={
                "root_id": p["id"],
                "actor_id": identity["actor_id"],
                "demand_lines": [x["id"] for x in p["demand_lines"]],
                "operations": ["propose", "commit"],
                "expires_at": float(now() + 300),
            },
        ),
        201,
    )

    async def exercise():
        sdk = DelegateClient(BASE, agent["key"])
        try:
            guard = RemoteAdkGuard(sdk, wf, "external-buyer")
            tool = type("Tool", (), {"name": "assever_purchase"})()
            result = await guard.before_tool(tool, {"grant_id": grant["id"], "merchant_id": "supplier_b"})
            assert result["status"] == "pending" and result["operation_id"]
            assert await guard.after_tool(tool, {"grant_id": grant["id"]}, None, {"executed": True}) is None
            return result["operation_id"]
        finally:
            await sdk.aclose()

    oid = asyncio.run(exercise())
    assert wait(client, oid)["state"] == "CONFIRMED"
    assert (
        client.post(
            f"/v1/purchases/contracts/{p['id']}/revoke",
            json={"expected_epoch": 1, "reason": "agent cannot revoke"},
            headers=headers,
        ).status_code
        == 403
    )
    evidence = check(client.get(f"/v1/purchases/contracts/{p['id']}/evidence"))
    assert evidence["verification"]["gross_captured_paise"] == 70000
    assert evidence["verification"]["task_complete"]


def test_other_owners_cannot_read_purchase_or_evidence(client):
    wf, p = draft(client)
    with httpx.Client(base_url=BASE, timeout=60, trust_env=False) as other:
        key = check(other.post("/v1/trial-keys"), 201)["key"]
        other.headers["Authorization"] = "Bearer " + key
        for path in (
            f"/v1/delegations/{wf}",
            f"/v1/delegations/{wf}/purchase",
            f"/v1/purchases/contracts/{p['id']}",
            f"/v1/purchases/contracts/{p['id']}/evidence",
        ):
            assert other.get(path).status_code == 404, path
        assert all(x["root"] != p["id"] for x in check(other.get("/v1/purchases/work-orders")))


def test_original_non_purchase_task_still_confirms_and_reports(client):
    state = check(
        client.post(
            "/v1/delegations",
            json={"request": "Read the quote and draft a reply. Do not send it.", "workspace": "workspace", "owner": "Employee"},
        )
    )
    wf = state["workflow"]["id"]
    result = check(client.post(f"/v1/delegations/{wf}/confirm", json={"hash": state["contract"]["hash"], "accept": []}))
    assert result["status"] == "confirmed"
    report = check(client.get(f"/v1/delegations/{wf}/report"))
    assert report["chain_ok"]


def test_private_dispatch_requires_worker_credential(client):
    with httpx.Client(timeout=5, trust_env=False) as c:
        r = c.post(os.environ["SINK_URL"] + "/dispatch", json={}, headers={"X-Service-Key": os.environ["SERVICE_KEY"]})
        assert r.status_code == 403


def test_database_schema_preserves_original_and_purchase_tables():
    with db() as c:
        for name in (
            "public.delegate_workflows",
            "public.delegate_contracts",
            "public.delegate_receipts",
            "purchase.contracts",
            "purchase.outbox",
            "purchase.workflow_bindings",
        ):
            assert c.execute("SELECT to_regclass(%s) p", (name,)).fetchone()["p"], name


def test_office_business_cannot_silently_gain_purchase_authority(client):
    state = check(client.post("/v1/delegations", json={"request": WORDS, "workspace": "workspace", "owner": "Office operator"}))
    r = client.post("/v1/delegations/" + state["workflow"]["id"] + "/purchase")
    assert r.status_code == 403 and r.json()["code"] == "BUSINESS_POLICY"


def test_human_review_cannot_exceed_company_purchase_ceiling(client):
    wf, p = draft(client)
    invalid = {**p["scope"], "max_paise": 500001}
    r = client.post(f"/v1/purchases/contracts/{p['id']}/edit", json={"expected_version": p["version"], "scope": invalid})
    assert r.status_code == 409 and r.json()["code"] == "BUSINESS_LIMIT"
    assert check(client.get(f"/v1/purchases/contracts/{p['id']}"))["scope"]["max_paise"] == 150000


def test_registered_business_policy_change_stops_new_purchase_admission(client):
    import uuid

    policy = check(client.get("/v1/delegate-workspaces/kirana"))["policy"]
    name = "kirana-" + uuid.uuid4().hex[:12]
    check(
        client.post(
            "/v1/delegate-workspaces", json={"id": name, "description": "Synthetic policy lifecycle test", "policy": policy}
        ),
        201,
    )
    state = check(client.post("/v1/delegations", json={"request": WORDS, "workspace": name, "owner": "Business operator"}))
    wf = state["workflow"]["id"]
    p = check(client.post(f"/v1/delegations/{wf}/purchase"), 201)
    approve(client, wf, p)
    policy["purchase_limit_paise"] = 100000
    check(
        client.post("/v1/delegate-workspaces", json={"id": name, "description": "Narrowed company ceiling", "policy": policy}),
        201,
    )
    r = client.post("/v1/purchases/quotes", json={"root_id": p["id"]})
    assert r.status_code == 409 and r.json()["code"] == "BUSINESS_POLICY_CHANGED"
    current = check(client.get(f"/v1/delegations/{wf}/purchase"))
    assert not current["business_policy"]["current"] and current["money"]["captured"] == 0


def test_isolated_evaluator_returns_scoped_real_effect_record(client):
    r = check(
        client.post(
            "/v1/purchases/lab/runs",
            json={
                "family_id": "duplicate_basket",
                "control_id": "adaptive",
                "profile_id": "dedupe",
                "topology": "delegated",
                "seed": 101,
                "manifest_version": 1,
            },
        ),
        202,
    )
    assert r["result"]["error"] is None
    assert r["result"]["verification"]["verdict"] == "PASS"
    assert r["result"]["model_calls"] == 0
    saved = check(client.get("/v1/purchases/lab/runs/" + r["id"]))
    assert saved["id"] == r["id"]
    lab_root = r["result"]["root_id"]
    assert client.get("/v1/purchases/contracts/" + lab_root).status_code == 404
    assert client.post("/v1/purchases/quotes", json={"root_id": lab_root}).status_code == 404
