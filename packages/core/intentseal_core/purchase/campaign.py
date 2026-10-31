import argparse
import json
from collections import Counter
from pathlib import Path

from .common import digest, uid
from .lab import FAMILIES, CONTROLS, manifest, run_cell
from .migrate import migrate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="/tmp/campaign")
    parser.add_argument("--controls", nargs="*", default=[c["id"] for c in CONTROLS])
    parser.add_argument("--families", nargs="*", default=[f[0] for f in FAMILIES])
    args = parser.parse_args()
    migrate()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    frozen = manifest()
    (output / "manifest.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    owner = {"tenant": uid("campaign"), "actor": uid("operator"), "role": "human"}
    rows = []
    for family in args.families:
        for profile in frozen["profiles"]:
            for topology in frozen["topologies"]:
                for control in args.controls:
                    spec = {
                        "family_id": family,
                        "control_id": control,
                        "profile_id": profile,
                        "topology": topology,
                        "seed": 101,
                        "manifest_version": 1,
                    }
                    row = run_cell(spec, owner)
                    (output / f"{row['id']}.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
                    small = {"id": row["id"], **spec, **{k: v for k, v in row["result"].items() if k != "bundle"}}
                    rows.append(small)
                    if len(rows) % 20 == 0:
                        print(json.dumps({"completed": len(rows), "latest": spec, "error": small["error"]}), flush=True)
    summary = {
        "manifest_digest": frozen["digest"],
        "cells": len(rows),
        "controls": {
            c: {
                "cells": sum(x["control_id"] == c for x in rows),
                "verdicts": dict(Counter(x["verification"]["verdict"] for x in rows if x["control_id"] == c)),
                "errors": sum(bool(x["error"]) for x in rows if x["control_id"] == c),
                "completed_tasks": sum(bool(x["verification"].get("task_complete")) for x in rows if x["control_id"] == c),
            }
            for c in args.controls
        },
        "rows_digest": digest(rows),
    }
    (output / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
