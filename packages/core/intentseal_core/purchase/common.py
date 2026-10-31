import hashlib
import json
import os
import uuid
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

_pools = {}
_pool_lock = threading.Lock()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def uid(prefix):
    return f"{prefix}_{uuid.uuid4().hex}"


def now():
    return datetime.now(timezone.utc).timestamp()


@contextmanager
def db():
    identity = (os.getpid(), os.environ["DATABASE_URL"])
    if identity not in _pools:
        with _pool_lock:
            if identity not in _pools:
                minimum = int(os.environ.get("PURCHASE_POOL_MIN", "1"))
                if not 1 <= minimum <= 24:
                    raise ValueError("PURCHASE_POOL_MIN must be between 1 and 24")
                pool = ConnectionPool(
                    identity[1],
                    min_size=minimum,
                    open=True,
                    max_size=24,
                    timeout=8,
                    max_idle=30,
                    kwargs={
                        "row_factory": dict_row,
                        "options": "-c search_path="
                        + ("purchase_effects" if os.environ.get("SERVICE_MODE") == "sink" else "purchase")
                        + ",public",
                    },
                )
                pool.wait(timeout=15)
                _pools[identity] = pool
    with _pools[identity].connection() as conn:
        yield conn


def jsonb(value):
    return Jsonb(value)


CATALOG = {
    "RICE_5KG_A": {
        "line": "rice",
        "base_units": 5000,
        "unit": "g",
        "price": 30000,
        "merchant": "supplier_a",
        "label": "Sona rice · 5 kg",
    },
    "OIL_1L_A": {
        "line": "oil",
        "base_units": 1000,
        "unit": "ml",
        "price": 20000,
        "merchant": "supplier_a",
        "label": "Sunflower oil · 1 L",
    },
    "RICE_5KG_B": {
        "line": "rice",
        "base_units": 5000,
        "unit": "g",
        "price": 32000,
        "merchant": "supplier_b",
        "label": "Equivalent rice · 5 kg",
    },
    "OIL_1L_B": {
        "line": "oil",
        "base_units": 1000,
        "unit": "ml",
        "price": 19000,
        "merchant": "supplier_b",
        "label": "Equivalent oil · 1 L",
    },
    "RICE_10KG_A": {
        "line": "rice",
        "base_units": 10000,
        "unit": "g",
        "price": 50000,
        "merchant": "supplier_a",
        "label": "Rice · 10 kg (outside approval)",
    },
}
MERCHANTS = {"supplier_a": "synthetic-a@mock", "supplier_b": "synthetic-b@mock"}
PROFILES = ("dedupe", "queryable", "opaque")


def default_scope():
    return {
        "max_paise": 150000,
        "currency": "INR",
        "max_purchases": 1,
        "lines": {
            "rice": {"max_units": 5000, "unit": "g", "skus": ["RICE_5KG_A", "RICE_5KG_B"]},
            "oil": {"max_units": 2000, "unit": "ml", "skus": ["OIL_1L_A", "OIL_1L_B"]},
        },
        "merchants": ["supplier_a", "supplier_b"],
        "delivery_ref": "shop_01",
        "disclosure_fields": ["shop_name", "delivery_address"],
        "expires_at": now() + 86400,
    }
