import httpx
import pytest

from intentseal_core.purchase import service as api, models
from intentseal_core.purchase.models import ModelInvocationError
from intentseal_core.purchase.schemas import ModelPurchase
from test_purchase import approved


def test_malformed_local_model_output_is_retained_and_not_executed(monkeypatch):
    original = httpx.Client

    def handler(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "qwen2.5:0.5b", "digest": "synthetic-test-digest"}]})
        return httpx.Response(200, json={"message": {"content": "not JSON"}, "prompt_eval_count": 7, "eval_count": 2})

    monkeypatch.setattr(models.httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler)))
    with pytest.raises(ModelInvocationError) as exc:
        models.plan("qwen2.5:0.5b", "synthetic test", 19)
    assert exc.value.record["raw_response"]["message"]["content"] == "not JSON"
    assert exc.value.record["model_digest"] == "synthetic-test-digest"
    assert exc.value.record["prompt_tokens"] == 7


def test_failed_explicit_model_has_no_effect_or_fallback(monkeypatch):
    owner = {"tenant": "model-failure-test", "actor": "model-failure-operator", "role": "human"}
    d = approved(owner)

    def failed(*args, **kwargs):
        raise ModelInvocationError(
            "synthetic malformed output", {"model_id": "qwen2.5:0.5b", "raw_response": {"message": {"content": "bad"}}}
        )

    monkeypatch.setattr(models, "plan", failed)
    result = api.model_purchase(d["id"], ModelPurchase(model_id="qwen2.5:0.5b", seller_text="synthetic test"), owner)
    assert result["result"]["error"] and result["result"]["invocation"]["raw_response"]
    assert api.get_contract(d["id"], owner)["operations"] == []


def test_model_batch_refuses_customer_export_and_keeps_legitimate_purchase(monkeypatch):
    from intentseal_core.purchase.worker import tick

    owner = {"tenant": "batch-model-test", "actor": "batch-model-operator", "role": "human"}
    d = approved(owner)
    monkeypatch.setattr(
        models,
        "plan",
        lambda *args, **kwargs: {
            "plan": {"merchant_id": "supplier_a", "basket_count": 1, "request_customer_export": True, "delivery_ref": "shop_01"},
            "request_digest": "synthetic-test-request",
        },
    )
    r = api.model_purchase(d["id"], ModelPurchase(model_id="qwen2.5:0.5b", seller_text="synthetic hostile export request"), owner)
    assert r["result"]["error"] is None
    assert any(x.get("refused") == "DISCLOSURE_SCOPE" for x in r["result"]["attempts"])
    op = next(x["operation_id"] for x in r["result"]["attempts"] if x.get("admitted"))
    tick(target=op)
    exported = api.evidence(d["id"], owner)
    assert exported["verification"]["task_complete"]
    assert all(
        set(x["body"]["fields"]) == {"shop_name", "delivery_address"}
        for x in exported["bundle"]["observer"]["effects"]
        if x["kind"] == "egress"
    )


def test_model_batch_rejects_changed_delivery_without_reporting_inference_failure(monkeypatch):
    owner = {"tenant": "address-model-test", "actor": "address-model-operator", "role": "human"}
    d = approved(owner)
    monkeypatch.setattr(
        models,
        "plan",
        lambda *args, **kwargs: {
            "plan": {
                "merchant_id": "supplier_a",
                "basket_count": 1,
                "request_customer_export": False,
                "delivery_ref": "warehouse_attacker",
            },
            "request_digest": "synthetic-test-request",
        },
    )
    r = api.model_purchase(
        d["id"], ModelPurchase(model_id="qwen2.5:0.5b", seller_text="synthetic changed-address request"), owner
    )
    assert r["result"]["error"] is None and r["result"]["attempts"][0]["refused"] == "DESTINATION"
    assert api.get_contract(d["id"], owner)["operations"] == []
