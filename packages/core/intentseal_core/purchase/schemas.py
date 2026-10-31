from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Draft(Strict):
    request_text: str = Field(min_length=1, max_length=4000)
    catalog_profile: Literal["kirana-v1"] = "kirana-v1"
    locale: Literal["en", "hi"] = "en"


class Approval(Strict):
    version: int
    hash: str
    accepted_fields: dict
    human_confirmation_nonce: str


class Line(Strict):
    demand_line_id: str
    sku: str
    quantity: int = Field(gt=0, le=100)
    unit: Literal["pack", "bottle"]


class Proposal(Strict):
    schema_version: Literal[1] = 1
    root_id: str
    grant_id: str | None = None
    merchant_id: str
    checkout_ref: str
    lines: list[Line] = Field(min_length=1, max_length=10)
    currency: Literal["INR"] = "INR"
    total_paise: int = Field(ge=0, le=10**12)
    delivery_ref: str
    disclosure_profile: Literal["delivery_minimum"] = "delivery_minimum"


class Prepare(Strict):
    expected_contract_version: int
    proposal_digest: str


class Commit(Strict):
    prepared_digest: str


class GrantInput(Strict):
    root_id: str
    parent_id: str | None = None
    actor_id: str
    audience: Literal["purchase-api"] = "purchase-api"
    demand_lines: list[str]
    operations: list[Literal["propose", "commit"]]
    expires_at: float


class Revoke(Strict):
    expected_epoch: int
    reason: str = Field(min_length=1, max_length=300)


class Narrow(Strict):
    expected_version: int
    allowed_changes: dict


class Reconcile(Strict):
    operation_version: int


class ExceptionRequest(Strict):
    root_id: str
    effect: dict
    new_scope: dict


class ExceptionDecision(Strict):
    approve: bool
    expected_action_digest: str
    nonce: str


class QuoteLine(Strict):
    sku: str
    quantity: int = Field(gt=0, le=100)


class EditScope(Strict):
    expected_version: int
    scope: dict


class QuoteInput(Strict):
    root_id: str
    merchant_id: Literal["supplier_a", "supplier_b"] = "supplier_a"
    fees_paise: int = Field(ge=0, le=10**12, default=0)
    coupon_paise: int = Field(ge=0, le=10**12, default=0)
    lines: list[QuoteLine] | None = Field(default=None, min_length=1, max_length=10)


class Callback(Strict):
    root_id: str
    transaction_id: str
    message_id: str
    operation_id: str
    participant: str
    timestamp: float
    observation_type: Literal["search", "select", "init", "confirm", "status"]
    body: dict


class LabInput(Strict):
    family_id: str
    control_id: str = "adaptive"
    profile_id: Literal["dedupe", "queryable", "opaque"] = "dedupe"
    topology: Literal["single", "delegated"] = "single"
    seed: int = Field(ge=0, le=2**31 - 1, default=0)
    manifest_version: Literal[1] = 1


class ModelPurchase(Strict):
    model_id: Literal["qwen2.5:0.5b", "qwen3:0.6b", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
    seller_text: str = Field(max_length=4000)
    seed: int = Field(default=101, ge=0, le=2**31 - 1)
