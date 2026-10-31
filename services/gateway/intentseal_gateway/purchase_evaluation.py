"""Private owned-environment evaluation process. No public user identity system."""

import hmac
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from intentseal_core.purchase.lab import run_cell
from intentseal_core.purchase.schemas import LabInput
from intentseal_core.purchase.migrate import migrate


@asynccontextmanager
async def lifespan(app):
    migrate()
    yield


app = FastAPI(title="Assever private evaluator", lifespan=lifespan, docs_url=None, openapi_url=None)


class Cell(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spec: LabInput
    tenant: str
    actor: str


@app.get("/readyz")
def ready():
    return {"ready": True, "synthetic": True}


@app.post("/run")
def run(data: Cell, x_lab_key: str = Header(default="")):
    expected = os.environ.get("LAB_KEY", "")
    if os.environ.get("LAB_ENABLED") != "1" or not expected or not hmac.compare_digest(expected, x_lab_key):
        raise HTTPException(403, "Evaluator service identity required")
    return run_cell(data.spec.model_dump(), {"tenant": data.tenant, "actor": data.actor, "role": "human"})
