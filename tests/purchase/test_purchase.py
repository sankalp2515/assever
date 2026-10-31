import copy
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import httpx
import pytest

from intentseal_core.purchase import service as api
from intentseal_core.purchase.checker import verify
from intentseal_core.purchase.common import db, digest, now, uid
from intentseal_core.purchase.lab import run_cell
from intentseal_core.purchase.runtime import Refusal, settle
from intentseal_core.purchase.schemas import Approval, Commit, GrantInput, Narrow, Prepare, Proposal, QuoteInput
from intentseal_core.purchase.worker import provider, reconcile_one, tick


@pytest.fixture
def owner():
    return {"tenant": uid("test"), "actor": uid("human"), "role": "human"}


def approved(owner):
    with db() as c:
        d = api.create_draft(c, owner, "1 x 5 kg rice, 2 x 1 L oil up to 1500")
        c.execute("UPDATE contracts SET is_lab=true WHERE id=%s", (d["id"],))
    return api.approve(
        d["id"],
        Approval(version=1, hash=d["digest"], accepted_fields=d["scope"], human_confirmation_nonce=d["human_confirmation_nonce"]),
        owner,
    )


def preview(owner, d, fees=0):
    q = api.quote(QuoteInput(root_id=d["id"], fees_paise=fees), owner)
    lines = [
        {
            "demand_line_id": next(x["id"] for x in d["demand_lines"] if x["name"] == name),
            "sku": sku,
            "quantity": qty,
            "unit": unit,
        }
        for name, sku, qty, unit in [("rice", "RICE_5KG_A", 1, "pack"), ("oil", "OIL_1L_A", 2, "bottle")]
    ]
    p = api.propose(
        Proposal(
            root_id=d["id"],
            merchant_id="supplier_a",
            checkout_ref=q["body"]["id"],
            lines=lines,
            total_paise=q["body"]["total_paise"],
            delivery_ref="shop_01",
        ),
        owner,
    )
    return api.prepare(p["id"], Prepare(expected_contract_version=d["version"], proposal_digest=p["digest"]), owner)


def commit_attempt(value):
    owner, op = value
    try:
        api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
        return "admitted"
    except Refusal as exc:
        return exc.code


def test_prepare_has_no_reservation_or_dispatch(owner):
    d = approved(owner)
    op = preview(owner, d)
    with db() as c:
        assert c.execute("SELECT count(*) n FROM reservations WHERE operation=%s", (op["id"],)).fetchone()["n"] == 0
        assert c.execute("SELECT count(*) n FROM outbox WHERE operation=%s", (op["id"],)).fetchone()["n"] == 0
    assert tick(target=op["id"]) is None


def test_same_operation_parallel_commit_idempotent(owner):
    d = approved(owner)
    op = preview(owner, d)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(commit_attempt, [(owner, op)] * 20))
    assert results == ["admitted"] * 20
    with db() as c:
        assert c.execute("SELECT count(*) n FROM reservations WHERE root=%s", (d["id"],)).fetchone()["n"] == 1


def test_hundred_attempt_real_multiprocess_admission(owner):
    d = approved(owner)
    ops = [preview(owner, d) for _ in range(100)]
    import multiprocessing

    with ProcessPoolExecutor(max_workers=8, mp_context=multiprocessing.get_context("spawn")) as pool:
        outcomes = list(pool.map(commit_attempt, [(owner, op) for op in ops]))
    assert outcomes.count("admitted") == 1
    assert outcomes.count("DEMAND_ALREADY_ENCUMBERED") == 99
    state = api.get_contract(d["id"], owner)
    assert state["money"]["reserved"] == 70000 and state["money"]["captured"] == 0
    assert state["quantities"]["rice"]["remaining"] == 0


@pytest.mark.parametrize(
    "family",
    [
        "clean",
        "equivalent",
        "stock_replanning",
        "duplicate_basket",
        "child_duplication",
        "concurrent",
        "payee_mutation",
        "sku_mutation",
        "fee_mutation",
        "disclosure",
        "poisoned_memory",
        "downstream_change",
        "direct_bypass",
        "response_loss",
        "delayed_commit",
        "crash_recovery",
        "dedupe_expiry",
        "revoke_before",
        "revoke_after",
        "supplier_unknown",
        "corrupt_evidence",
    ],
)
def test_scenario_covered_safety(owner, family):
    r = run_cell(
        {
            "family_id": family,
            "control_id": "adaptive",
            "profile_id": "dedupe",
            "topology": "delegated",
            "seed": 101,
            "manifest_version": 1,
        },
        owner,
    )
    assert r["result"]["error"] is None, r["result"]["error"]
    assert r["result"]["verification"]["verdict"] == "PASS", r["result"]["verification"]
    if family != "revoke_before":
        assert r["result"]["verification"]["task_complete"]


@pytest.mark.parametrize("profile", ["queryable", "opaque"])
def test_uncertainty_not_released_on_missing_status(owner, profile):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick(profile, "crash_before_send", op["id"])
    reconcile_one(op["id"])
    state = api.get_contract(d["id"], owner)
    assert state["money"]["unknown"] == 70000 and state["money"]["captured"] == 0
    assert commit_attempt((owner, preview(owner, d))) == "DEMAND_ALREADY_ENCUMBERED"


def test_opaque_captured_truth_not_leaked_to_recovery(owner):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick("opaque", "response_loss", op["id"])
    reconcile_one(op["id"])
    assert api.get_contract(d["id"], owner)["money"]["unknown"] == 70000
    exported = api.evidence(d["id"], owner)
    assert exported["verification"]["gross_captured_paise"] == 70000
    assert exported["verification"]["verdict"] == "INCOMPLETE"
    assert api.get_contract(d["id"], owner)["money"]["unknown"] == 70000


def test_cancellation_requires_unsent_fence(owner):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    api.cancel(op["id"], owner)
    assert tick(target=op["id"]) is None
    assert api.get_contract(d["id"], owner)["money"]["remaining"] == 150000
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick("dedupe", "crash_before_send", op["id"])
    with pytest.raises(Refusal):
        api.cancel(op["id"], owner)


def test_repeated_settlement_and_conflict(owner):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick(target=op["id"])
    observation = provider("GET", "/status/" + op["id"])
    with db() as c:
        c.execute("SELECT id FROM contracts WHERE id=%s FOR UPDATE", (d["id"],))
        current = c.execute("SELECT * FROM operations WHERE id=%s", (op["id"],)).fetchone()
        settle(c, current, observation)
        with pytest.raises(Refusal):
            settle(c, current, {"state": "CLOSED", "closure_barrier": True})
    assert api.get_contract(d["id"], owner)["money"]["captured"] == 70000


def test_epoch_and_narrow_preserve_spend(owner):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick(target=op["id"])
    state = api.narrow(d["id"], Narrow(expected_version=1, allowed_changes={"max_paise": 80000}), owner)
    assert state["money"]["captured"] == 70000 and state["money"]["remaining"] == 10000
    assert api.evidence(d["id"], owner)["verification"]["verdict"] == "PASS"
    with pytest.raises(Refusal):
        api.narrow(d["id"], Narrow(expected_version=2, allowed_changes={"max_paise": 90000}), owner)


def test_cross_tenant_hides_content(owner):
    d = approved(owner)
    for role in ("human", "agent", "evaluator"):
        outsider = {"tenant": uid("other"), "actor": uid("actor"), "role": role}
        with pytest.raises(Refusal) as err:
            api.get_contract(d["id"], outsider)
        assert err.value.status == 404


def test_agent_cannot_self_approve_or_cross_actor_grant(owner):
    d = approved(owner)
    registered = api.create_agent(owner)
    agent = {**owner, "actor": registered["actor_id"], "role": "agent"}
    with pytest.raises(Refusal):
        api.human(agent)
    g = api.grant(
        GrantInput(
            root_id=d["id"],
            actor_id=agent["actor"],
            demand_lines=[x["id"] for x in d["demand_lines"]],
            operations=["propose"],
            expires_at=float(now() + 300),
        ),
        owner,
    )
    other = api.create_agent(owner)
    with pytest.raises(Refusal):
        api.grant(
            GrantInput(
                root_id=d["id"],
                parent_id=g["id"],
                actor_id=other["actor_id"],
                demand_lines=[x["id"] for x in d["demand_lines"]],
                operations=["propose", "commit"],
                expires_at=float(now() + 200),
            ),
            agent,
        )


def test_recomputed_corrupt_exports_rejected(owner):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick(target=op["id"])
    b = api.evidence(d["id"], owner)["bundle"]
    assert verify(b)["task_complete"]
    for mutate in [
        lambda x: x["observer"]["effects"].pop(),
        lambda x: x["contract"]["events"].reverse(),
        lambda x: x["observer"]["effects"][0]["body"].update({"amount_paise": 999999}),
        lambda x: x["contract"]["operations"].clear(),
    ]:
        bad = copy.deepcopy(b)
        mutate(bad)
        bad["bundle_digest"] = digest({k: v for k, v in bad.items() if k != "bundle_digest"})
        assert verify(bad)["verdict"] == "FAIL"


def test_real_process_exit_after_send_recovered_by_new_process(owner):
    import subprocess, sys

    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    code = (
        "from intentseal_core.purchase.worker import tick;import os;tick('dedupe','crash_after_send',"
        + repr(op["id"])
        + ");os._exit(77)"
    )
    result = subprocess.run([sys.executable, "-c", code], check=False)
    assert result.returncode == 77
    assert api.get_contract(d["id"], owner)["operations"][0]["state"] == "DISPATCHING"
    subprocess.run(
        [sys.executable, "-c", "from intentseal_core.purchase.worker import reconcile_one;reconcile_one(" + repr(op["id"]) + ")"],
        check=True,
    )
    assert api.evidence(d["id"], owner)["verification"]["task_complete"]


def test_expired_dedupe_and_payload_conflicts(owner):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick(target=op["id"])
    request = {
        "operation_id": op["id"],
        "effect": op["effect"],
        "digest": op["digest"],
        "fence": 1,
        "profile": "dedupe",
        "fault": "none",
    }
    assert provider("POST", "/dispatch", json=request)["state"] == "COMMITTED"
    provider("POST", "/faults/" + op["id"] + "/expire-dedupe")
    with pytest.raises(httpx.HTTPStatusError):
        provider("POST", "/dispatch", json=request)
    assert api.evidence(d["id"], owner)["verification"]["orders"] == 1


def test_private_effect_routes_reject_agent_credentials():
    with httpx.Client(base_url=os.environ["SINK_URL"], trust_env=False) as c:
        for method, path in [
            ("POST", "/dispatch"),
            ("POST", "/close/unknown"),
            ("GET", "/status/unknown"),
            ("GET", "/observe/unknown"),
            ("POST", "/quotes"),
            ("POST", "/faults/unknown/expire-dedupe"),
        ]:
            r = c.request(method, path, headers={"Authorization": "Bearer agent-token"}, json={})
            assert r.status_code == 403, (path, r.status_code)


def test_refund_does_not_mint_new_purchase_right(owner):
    d = approved(owner)
    op = preview(owner, d)
    api.commit(op["id"], Commit(prepared_digest=op["digest"]), owner)
    tick(target=op["id"])
    api.refund_notice(op["id"], owner)
    api.refund_notice(op["id"], owner)
    assert api.get_contract(d["id"], owner)["money"]["captured"] == 70000
    assert commit_attempt((owner, preview(owner, d))) == "DEMAND_ALREADY_ENCUMBERED"
    b = api.evidence(d["id"], owner)
    assert b["verification"]["gross_captured_paise"] == 70000
    assert len(b["bundle"]["observer"]["notices"]) == 1


def test_already_applied_migration_does_not_lock_live_purchases(owner):
    from intentseal_core.purchase.migrate import migrate

    d = approved(owner)
    with db() as c:
        c.execute("SELECT id FROM contracts WHERE id=%s FOR UPDATE", (d["id"],))
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(migrate).result(timeout=5)


def test_two_nine_hundred_payments_share_atomic_fifteen_hundred_cap(owner):
    d = approved(owner)
    ops = [preview(owner, d, fees=20000) for _ in range(2)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(commit_attempt, [(owner, op) for op in ops]))
    assert results.count("admitted") == 1
    assert results.count("BUDGET_ENCUMBERED") == 1
    assert api.get_contract(d["id"], owner)["money"]["reserved"] == 90000


def test_reviewed_split_purchase_accepts_two_suppliers_without_extra_units(owner):
    from intentseal_core.purchase.schemas import EditScope

    with db() as c:
        d = api.create_draft(c, owner, "Split the exact basket between approved suppliers, up to INR1500")
        c.execute("UPDATE contracts SET is_lab=true WHERE id=%s", (d["id"],))
    scope = {**d["scope"], "max_purchases": 2}
    d = api.edit_scope(d["id"], EditScope(expected_version=1, scope=scope), owner)
    api.approve(
        d["id"],
        Approval(version=2, hash=d["digest"], accepted_fields=d["scope"], human_confirmation_nonce=d["human_confirmation_nonce"]),
        owner,
    )
    for merchant, sku, quantity in [("supplier_a", "RICE_5KG_A", 1), ("supplier_b", "OIL_1L_B", 2)]:
        op = api.agent_purchase(
            d["id"], QuoteInput(root_id=d["id"], merchant_id=merchant, lines=[{"sku": sku, "quantity": quantity}]), owner
        )
        tick(target=op["id"])
    v = api.evidence(d["id"], owner)["verification"]
    assert v["verdict"] == "PASS" and v["orders"] == 2 and v["task_complete"]
    assert v["gross_captured_paise"] == 68000


def test_retired_issuer_cannot_authorize_agent_work(owner, monkeypatch):
    from intentseal_core.purchase.runtime import checked_grant, root

    d = approved(owner)
    registered = api.create_agent(owner)
    agent = {**owner, "actor": registered["actor_id"], "role": "agent"}
    g = api.grant(
        GrantInput(
            root_id=d["id"],
            actor_id=agent["actor"],
            demand_lines=[x["id"] for x in d["demand_lines"]],
            operations=["propose"],
            expires_at=float(now() + 300),
        ),
        owner,
    )
    monkeypatch.setenv("ISSUER_KEY_V1", "")
    with db() as c:
        row = root(c, d["id"], owner)
        with pytest.raises(Refusal) as exc:
            checked_grant(c, row, agent, g["id"], "propose", ["rice"])
        assert exc.value.code == "ISSUER_RETIRED"


def test_exact_exception_reconnect_and_single_use(owner):
    from intentseal_core.purchase.schemas import ExceptionRequest, ExceptionDecision

    d = approved(owner)
    ex = api.exception_request(
        ExceptionRequest(
            root_id=d["id"], effect={"change": "cap", "new_paise": 160000}, new_scope={**d["scope"], "max_paise": 160000}
        ),
        owner,
    )
    renewed = api.exception_review_nonce(ex["id"], owner)
    with pytest.raises(Refusal):
        api.exception_decide(
            ex["id"], ExceptionDecision(approve=True, expected_action_digest=ex["digest"], nonce=ex["nonce"]), owner
        )
    with pytest.raises(Refusal):
        api.exception_decide(
            ex["id"], ExceptionDecision(approve=True, expected_action_digest="changed", nonce=renewed["nonce"]), owner
        )
    body = ExceptionDecision(approve=True, expected_action_digest=ex["digest"], nonce=renewed["nonce"])
    state = api.exception_decide(ex["id"], body, owner)
    assert state["scope"]["max_paise"] == 160000 and state["version"] == 2
    with pytest.raises(Refusal):
        api.exception_decide(ex["id"], body, owner)


def test_expired_exception_refused(owner):
    from intentseal_core.purchase.schemas import ExceptionRequest, ExceptionDecision

    d = approved(owner)
    ex = api.exception_request(
        ExceptionRequest(root_id=d["id"], effect={"change": "cap"}, new_scope={**d["scope"], "max_paise": 160000}), owner
    )
    with db() as c:
        c.execute("UPDATE exceptions SET expires=%s WHERE id=%s", (now() - 1, ex["id"]))
    with pytest.raises(Refusal):
        api.exception_decide(
            ex["id"], ExceptionDecision(approve=True, expected_action_digest=ex["digest"], nonce=ex["nonce"]), owner
        )
