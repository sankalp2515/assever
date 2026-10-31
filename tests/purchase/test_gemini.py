"""Google SDK failure and malformed output must never reach execution."""
import json
from types import SimpleNamespace
import pytest
from intentseal_core.purchase import models


@pytest.mark.parametrize('failure', ['transport', 'invalid_boolean'])
def test_vertex_failure_retains_request_without_fallback(monkeypatch, failure):
    from google import genai
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs['vertexai'] and kwargs['project'] == 'synthetic-sdk-test'
            assert kwargs['http_options'].retry_options.attempts == 1
            self.models = self

        def __enter__(self): return self
        def __exit__(self, *args): return False

        def generate_content(self, **kwargs):
            calls.append(kwargs)
            if failure == 'transport': raise TimeoutError('synthetic SDK timeout')
            raw = {'merchant_id':'supplier_a','basket_count':True,'request_customer_export':False,'delivery_ref':'shop_01'}
            return SimpleNamespace(text=json.dumps(raw), model_version='synthetic-version', usage_metadata=None,
                                   model_dump=lambda **kwargs: {'synthetic_response':raw})

    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT', 'synthetic-sdk-test')
    monkeypatch.setattr(genai, 'Client', FakeClient)
    with pytest.raises(models.ModelInvocationError) as caught:
        models.plan('gemini-3.5-flash', 'Untrusted synthetic seller', 607)
    record = caught.value.record
    assert len(calls) == 1 and record['plan'] is None
    assert record['request']['options']['seed'] == 607
    assert record['request_digest'] == models.digest(record['request'])
    assert record['provider'] == 'vertex' and record['error']
