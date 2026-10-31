"""Durable outbox, deliberately conservative at the send/crash boundary."""

import os
import time
from pathlib import Path

import httpx

from .common import db, now
from .migrate import migrate
from .runtime import Refusal, event, settle

_provider_clients = {}


def provider(method, path, **kwargs):
    # A thread-safe pool is owned by each OS process; no connection is shared across a fork.
    pid = os.getpid()
    if pid not in _provider_clients:
        _provider_clients[pid] = httpx.Client(
            timeout=5, trust_env=False, limits=httpx.Limits(max_connections=40, max_keepalive_connections=40)
        )
    headers = {"X-Service-Key": os.environ["SERVICE_KEY"]}
    if path == "/dispatch" or path.startswith(("/close/", "/faults/")):
        headers["X-Dispatch-Key"] = os.environ.get("DISPATCH_KEY", "")
    response = _provider_clients[pid].request(method, os.environ["SINK_URL"] + path, headers=headers, **kwargs)
    response.raise_for_status()
    return response.json()


def reconcile_one(operation_id, close=False):
    with db() as c:
        lookup = c.execute("SELECT root FROM operations WHERE id=%s", (operation_id,)).fetchone()
        if not lookup:
            return
        c.execute("SELECT id FROM contracts WHERE id=%s FOR UPDATE", (lookup["root"],))
        op = c.execute("SELECT * FROM operations WHERE id=%s FOR UPDATE", (operation_id,)).fetchone()
        if op["state"] not in ("UNKNOWN", "DISPATCHING"):
            return
        try:
            observation = provider("POST" if close else "GET", ("/close/" if close else "/status/") + operation_id)
        except httpx.HTTPError:
            observation = {"state": "QUERY_ERROR", "operation_id": operation_id, "closure_barrier": False}
        settle(c, op, observation)
        c.execute(
            "UPDATE outbox SET attempts=attempts+1,next_attempt=%s,error=%s WHERE operation=%s",
            (
                now() + min(60, 2 ** min(6, op["revision"])),
                None if observation["state"] != "QUERY_ERROR" else "PROVIDER_QUERY_ERROR",
                operation_id,
            ),
        )
        c.execute("UPDATE outbox SET state='ESCALATED' WHERE operation=%s AND state='RECONCILE' AND attempts>=8", (operation_id,))


def tick(profile="dedupe", fault="none", target=None):
    op = None
    # Root first, then outbox: same lock ordering as commit/reconcile/cancel.
    with db() as c:
        candidate = c.execute(
            "SELECT o.root,o.id FROM operations o JOIN outbox b ON b.operation=o.id JOIN contracts p ON p.id=o.root WHERE b.state='PENDING'"
            + (" AND o.id=%s" if target else " AND p.is_lab=false")
            + " ORDER BY o.created LIMIT 1",
            (target,) if target else (),
        ).fetchone()
        if candidate:
            c.execute("SELECT id FROM contracts WHERE id=%s FOR UPDATE", (candidate["root"],))
            box = c.execute("SELECT * FROM outbox WHERE operation=%s FOR UPDATE", (candidate["id"],)).fetchone()
            if box["state"] == "PENDING":
                op = c.execute("SELECT * FROM operations WHERE id=%s FOR UPDATE", (candidate["id"],)).fetchone()
                fence = box["generation"] + 1
                c.execute(
                    "UPDATE outbox SET state='CLAIMED',generation=%s,lease_until=%s,attempts=attempts+1 WHERE operation=%s",
                    (fence, now() + 15, op["id"]),
                )
                c.execute(
                    "UPDATE operations SET state='DISPATCHING',revision=revision+1,updated=%s WHERE id=%s", (now(), op["id"])
                )
                event(c, op["root"], "DISPATCHING", {"operation_id": op["id"], "fence": fence, "digest": op["digest"]})
    if op:
        # Claim is durable before network I/O. A claimed operation is never blindly redispatched.
        if fault == "crash_before_send":
            return op["id"]
        try:
            observation = provider(
                "POST",
                "/dispatch",
                json={
                    "operation_id": op["id"],
                    "effect": op["effect"],
                    "digest": op["digest"],
                    "fence": fence,
                    "profile": profile,
                    "fault": fault,
                },
            )
        except httpx.HTTPError:
            observation = {"state": "RESPONSE_LOST", "operation_id": op["id"], "closure_barrier": False}
        if fault == "crash_after_send":
            return op["id"]
        with db() as c:
            c.execute("SELECT id FROM contracts WHERE id=%s FOR UPDATE", (op["root"],))
            current = c.execute("SELECT * FROM operations WHERE id=%s FOR UPDATE", (op["id"],)).fetchone()
            box = c.execute("SELECT * FROM outbox WHERE operation=%s FOR UPDATE", (op["id"],)).fetchone()
            if box["generation"] == fence and box["state"] == "CLAIMED":
                settle(c, current, observation, "dispatch-response")
        return op["id"]
    return None


def recover_expired():
    with db() as c:
        candidates = c.execute(
            "SELECT b.operation FROM outbox b JOIN operations o ON o.id=b.operation JOIN contracts p ON p.id=o.root WHERE b.state='CLAIMED' AND b.lease_until<%s AND p.is_lab=false",
            (now(),),
        ).fetchall()
    for candidate in candidates:
        reconcile_one(candidate["operation"])
    with db() as c:
        candidates = c.execute(
            "SELECT b.operation FROM outbox b JOIN operations o ON o.id=b.operation JOIN contracts p ON p.id=o.root WHERE b.state='RECONCILE' AND b.next_attempt<%s AND p.is_lab=false ORDER BY b.next_attempt LIMIT 20",
            (now(),),
        ).fetchall()
    for candidate in candidates:
        reconcile_one(candidate["operation"])


def main():
    migrate()
    while True:
        try:
            tick()
            recover_expired()
        except (httpx.HTTPError, Refusal, OSError) as exc:
            print({"event": "worker_error", "type": type(exc).__name__}, flush=True)
        finally:
            Path("/tmp/assever-worker-heartbeat").write_text(str(now()))
        time.sleep(0.3)


if __name__ == "__main__":
    main()
