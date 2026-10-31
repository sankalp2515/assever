"""Twenty synchronized real gateway commits; timing boundaries and actual effects."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
import statistics
import threading
import time
import httpx

ROOT = Path("/app")
BASE = os.environ.get("INTEGRATED_URL", "http://localhost:8000")
OUT = Path("/evidence/google-performance")


def checked(r):
    assert r.status_code in (200, 201, 202), (r.status_code, r.text[:300])
    return r.json()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=BASE, timeout=120, trust_env=False) as c:
        c.headers['Authorization'] = 'Bearer ' + checked(c.post('/v1/trial-keys'))['key']
        catalog = checked(c.get("/v1/purchases/catalog"))["catalog"]
        prepared = []
        for _ in range(20):
            wf = checked(
                c.post(
                    "/v1/delegations",
                    json={
                        "request": "Buy 1 x 5 kg rice and 2 x 1 L oil up to INR 1500.",
                        "workspace": "kirana",
                        "owner": "Synthetic performance operator",
                    },
                )
            )["workflow"]["id"]
            d = checked(c.post(f"/v1/delegations/{wf}/purchase"))
            state = checked(
                c.post(
                    f"/v1/purchases/contracts/{d['id']}/approve",
                    json={
                        "version": d["version"],
                        "hash": d["digest"],
                        "accepted_fields": d["scope"],
                        "human_confirmation_nonce": d["human_confirmation_nonce"],
                    },
                )
            )
            quote = checked(c.post("/v1/purchases/quotes", json={"root_id": d["id"], "merchant_id": "supplier_a"}))
            demand = {line["name"]: line["id"] for line in state["demand_lines"]}
            proposal = checked(
                c.post(
                    "/v1/purchases/proposals",
                    json={
                        "root_id": d["id"],
                        "merchant_id": "supplier_a",
                        "checkout_ref": quote["body"]["id"],
                        "total_paise": quote["body"]["total_paise"],
                        "delivery_ref": state["scope"]["delivery_ref"],
                        "lines": [
                            {
                                "demand_line_id": demand[catalog[x["sku"]]["line"]],
                                "sku": x["sku"],
                                "quantity": x["quantity"],
                                "unit": "pack" if catalog[x["sku"]]["unit"] == "g" else "bottle",
                            }
                            for x in quote["body"]["lines"]
                        ],
                    },
                )
            )
            op = checked(
                c.post(
                    f"/v1/purchases/proposals/{proposal['id']}/prepare",
                    json={"expected_contract_version": state["version"], "proposal_digest": proposal["digest"]},
                )
            )
            prepared.append((wf, d["id"], op))
        barrier = threading.Barrier(20)

        def commit(item):
            wf, rid, op = item
            barrier.wait()
            started = time.perf_counter()
            result = checked(c.post(f"/v1/purchases/operations/{op['id']}/commit", json={"prepared_digest": op["digest"]}))
            return {
                "workflow": wf,
                "root": rid,
                "operation": op["id"],
                "http_ms": (time.perf_counter() - started) * 1000,
                **result["timings"],
            }

        with ThreadPoolExecutor(max_workers=20) as pool:
            rows = list(pool.map(commit, prepared))
        spec = importlib.util.spec_from_file_location("offline", ROOT / "packages/core/intentseal_core/purchase/checker.py")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        for row in rows:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                current = checked(c.get("/v1/purchases/operations/" + row["operation"]))
                if current["state"] == "CONFIRMED":
                    break
                time.sleep(0.15)
            exported = checked(c.get(f"/v1/purchases/contracts/{row['root']}/evidence"))
            verdict = checker.verify(exported["bundle"])
            assert verdict == exported["verification"]
            row["verification"] = verdict
            assert verdict["verdict"] == "PASS" and verdict["task_complete"], row
    summary = {}
    for key in ("core_admission_ms", "provider_readiness_ms", "http_ms"):
        values = [r[key] for r in rows]
        summary[key] = {
            "p50": round(statistics.median(values), 3),
            "p95": round(statistics.quantiles(values, n=100, method="inclusive")[94], 3),
            "max": round(max(values), 3),
        }
    memory_kb = int(next(line for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal:')).split()[1])
    host = [str(os.cpu_count()), str(memory_kb * 1024)]
    result = {
        "clients": 20,
        "schedule": "Twenty prepared operations on twenty independently approved roots; commits released by one barrier.",
        "timing_boundaries": "Core transaction excludes provider readiness and HTTP transport; HTTP measures only commit, not workflow creation, inference or provider settlement.",
        "host": {"docker_cpus": int(host[0]), "docker_memory_bytes": int(host[1])},
        "summary": summary,
        "rows": rows,
        "effect_checks": "All twenty actual-effect bundles independently verify PASS and task complete.",
    }
    (OUT / "performance.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"clients": 20, "host": result["host"], "summary": summary, "effect_checks": 20}, indent=2))


if __name__ == "__main__":
    main()
