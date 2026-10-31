import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from intentseal_core.purchase.ap2_projection import project
from intentseal_core.purchase.common import default_scope


def fixture():
    key = ec.generate_private_key(ec.SECP256R1())
    agent = {"kty": "EC", "crv": "P-256", "x": "synthetic-agent-x", "y": "synthetic-agent-y"}
    payee = {"id": "supplier_a", "name": "Supplier A", "website": "https://supplier-a.example"}
    mandate = {
        "vct": "mandate.payment.open.1",
        "constraints": [
            {"type": "payment.amount_range", "min": 0, "max": 1000, "currency": "INR"},
            {"type": "payment.allowed_payees", "allowed": [payee]},
        ],
        "cnf": {"jwk": agent},
        "iat": int(time.time()) - 1,
        "exp": int(time.time()) + 600,
    }
    return key, dict(agent), {"supplier_a": dict(payee)}, mandate


def signed(key, m):
    return jwt.encode(
        {"delegate_payload": [m], "_sd_alg": "sha-256"},
        key,
        algorithm="ES256",
        headers={"typ": "example+sd-jwt", "kid": "fixture-issuer-v1"},
    )


def test_valid_projection_is_narrow_preview_only():
    key, agent, payees, m = fixture()
    value = project(signed(key, m), key.public_key(), agent, default_scope(), payees)
    assert value["scope_preview"]["max_paise"] == 100000
    assert value["scope_preview"]["merchants"] == ["supplier_a"]
    assert value["requires_native_human_approval"]


@pytest.mark.parametrize(
    "change", ["version", "expired", "agent", "unknown_constraint", "currency", "precision", "payee", "selective", "no_limit"]
)
def test_unsupported_or_mismatched_mandate_refused(change):
    key, agent, payees, m = fixture()
    if change == "version":
        m["vct"] = "mandate.payment.open.2"
    if change == "expired":
        m["exp"] = int(time.time()) - 10
    if change == "agent":
        m["cnf"]["jwk"] = {"kty": "other"}
    if change == "unknown_constraint":
        m["constraints"].append({"type": "payment.reference", "conditional_transaction_id": "not-verified"})
    if change == "currency":
        m["constraints"][0]["currency"] = "USD"
    if change == "precision":
        m["constraints"][0]["max"] = 1.001
    if change == "payee":
        m["constraints"][1]["allowed"][0]["website"] = "https://attacker.example"
    if change == "selective":
        m["constraints"] = [{"...": "undisclosed-digest"}]
    if change == "no_limit":
        m["constraints"] = m["constraints"][1:]
    with pytest.raises(ValueError):
        project(signed(key, m), key.public_key(), agent, default_scope(), payees)


def test_different_issuer_cannot_sign():
    key, agent, payees, m = fixture()
    other = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(jwt.InvalidSignatureError):
        project(signed(other, m), key.public_key(), agent, default_scope(), payees)
