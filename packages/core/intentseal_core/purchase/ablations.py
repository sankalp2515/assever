"""Explicitly instrumented offline mechanism removals. Never installed on API routes."""

import json
from pathlib import Path

from . import service as api, runtime, worker
from .common import digest, uid
from .lab import run_cell

CASES = [
    ("trusted_demand_identity", "new_identity", {"DEMAND_IDENTITY"}),
    ("quantity_and_purchase_count", "duplicate_basket", {"DEMAND_ALREADY_ENCUMBERED", "PURCHASE_COUNT"}),
    ("current_authority", "revoke_before", {"AUTHORITY_INACTIVE", "PREVIEW_STALE", "GRANT_STALE"}),
    ("commit_digest_binding", "downstream_change", {"PAYLOAD_CONFLICT"}),
    ("uncertainty_retention", "supplier_unknown", set()),
]


def main():
    out = Path("/tmp/ablations")
    out.mkdir(exist_ok=True)
    original_require, original_api_require, original_settle = runtime.require, api.require, worker.settle
    rows = []
    for mechanism, family, codes in CASES:
        for profile in ("dedupe", "opaque"):
            for condition in ("full", "removed"):

                def instrumented(test, code, message, status=409):
                    if condition == "removed" and code in codes:
                        return
                    return original_require(test, code, message, status)

                def unsafe_release(c, op, observation, source="provider-status"):
                    if (
                        condition == "removed"
                        and mechanism == "uncertainty_retention"
                        and observation.get("state") == "RESPONSE_LOST"
                    ):
                        observation = {
                            "state": "CLOSED",
                            "closure_barrier": True,
                            "operation_id": op["id"],
                            "digest": op["digest"],
                            "synthetic_ablation": "timeout_is_failure",
                        }
                        source = "unproven-ablation-closure"
                    return original_settle(c, op, observation, source)

                runtime.require = api.require = instrumented
                worker.settle = unsafe_release
                owner = {"tenant": uid("ablation"), "actor": uid("operator"), "role": "human"}
                spec = {
                    "family_id": family,
                    "control_id": "adaptive",
                    "profile_id": profile,
                    "topology": "single",
                    "seed": 211,
                    "manifest_version": 1,
                }
                try:
                    result = run_cell(spec, owner)
                    row = {
                        "mechanism": mechanism,
                        "condition": condition,
                        "disabled_reason_codes": sorted(codes),
                        "spec": spec,
                        "run": result,
                    }
                    (out / f"{mechanism}-{profile}-{condition}.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
                    rows.append(
                        {
                            "mechanism": mechanism,
                            "condition": condition,
                            "profile": profile,
                            "run_id": result["id"],
                            "verification": result["result"]["verification"],
                            "attempts": result["result"]["attempts"],
                            "error": result["result"]["error"],
                        }
                    )
                finally:
                    runtime.require, api.require, worker.settle = original_require, original_api_require, original_settle
    summary = {
        "measurement": "instrumented-offline-ablation",
        "cells": len(rows),
        "rows": rows,
        "rows_digest": digest(rows),
        "interpretation": "Null removals can be masked by other enforcing layers. Quantity/count and current-authority checks are grouped mechanisms; no individual causal effect is inferred for every check. Transport identities remain server-rooted even when the line-ID guard is removed. Immutable dispatch still uses stored bytes even when commit's digest comparison is removed.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"cells": len(rows), "errors": sum(bool(x["error"]) for x in rows)}))


if __name__ == "__main__":
    main()
