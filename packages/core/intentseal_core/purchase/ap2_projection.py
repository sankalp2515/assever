"""Optional offline AP2 v0.2 constraint projection; not network certification.

Only a fully disclosed, issuer-signed open-payment envelope is supported. Native
human review and trusted demand are still required; this never activates a root.
"""

import copy
import time
from decimal import Decimal


def project(token, issuer_public_key, expected_agent_jwk, native_scope, trusted_payees):
    import jwt

    header = jwt.get_unverified_header(token)
    if header.get("alg") != "ES256" or header.get("kid") != "fixture-issuer-v1" or header.get("typ") != "example+sd-jwt":
        raise ValueError("Unsupported protected header in offline fixture profile")
    outer = jwt.decode(token, issuer_public_key, algorithms=["ES256"], options={"verify_aud": False})
    if set(outer) != {"delegate_payload", "_sd_alg"} or outer["_sd_alg"] != "sha-256" or len(outer["delegate_payload"]) != 1:
        raise ValueError("Only one fully disclosed open mandate is supported")
    mandate = outer["delegate_payload"][0]
    if set(mandate) != {"vct", "constraints", "cnf", "iat", "exp"} or mandate["vct"] != "mandate.payment.open.1":
        raise ValueError("Unsupported or partially disclosed mandate")
    if mandate["cnf"] != {"jwk": expected_agent_jwk}:
        raise ValueError("Agent key binding mismatch")
    if not (type(mandate["iat"]) is int and type(mandate["exp"]) is int and mandate["iat"] <= time.time() < mandate["exp"]):
        raise ValueError("Expired/future mandate")
    result = copy.deepcopy(native_scope)
    seen = set()
    for constraint in mandate["constraints"]:
        kind = constraint.get("type")
        if kind in seen:
            raise ValueError("Duplicate constraints are unsupported")
        seen.add(kind)
        if kind == "payment.amount_range":
            if set(constraint) != {"type", "min", "max", "currency"} or constraint["currency"] != "INR" or constraint["min"] != 0:
                raise ValueError("Only zero-minimum INR amount range is supported")
            value = Decimal(str(constraint["max"])) * 100
            if not value.is_finite() or value != value.to_integral_value() or not 0 < value <= 10**12:
                raise ValueError("Invalid paise precision or amount")
            result["max_paise"] = min(result["max_paise"], int(value))
        elif kind == "payment.allowed_payees":
            if set(constraint) != {"type", "allowed"} or not constraint["allowed"]:
                raise ValueError("Payee constraints are incomplete")
            mapped = []
            for payee in constraint["allowed"]:
                if (
                    set(payee) != {"id", "name", "website"}
                    or payee["id"] not in trusted_payees
                    or payee != trusted_payees[payee["id"]]
                ):
                    raise ValueError("Unknown or changed payee registry entry")
                mapped.append(payee["id"])
            result["merchants"] = [x for x in result["merchants"] if x in mapped]
            if not result["merchants"]:
                raise ValueError("No approved supplier remains")
        else:
            raise ValueError("Unsupported AP2 constraint: " + str(kind))
    if seen != {"payment.amount_range", "payment.allowed_payees"}:
        raise ValueError("Both supported constraints are mandatory in this profile")
    result["expires_at"] = min(result["expires_at"], mandate["exp"])
    return {
        "scope_preview": result,
        "vct": mandate["vct"],
        "profile": "AP2-v0.2-offline-open-payment-projection-1",
        "requires_native_human_approval": True,
        "checkout_binding": "Not implemented; this preview cannot dispatch.",
    }
