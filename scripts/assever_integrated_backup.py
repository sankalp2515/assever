"""Quiesced local backup/restore verification; never publishes database dumps."""

from pathlib import Path
from datetime import datetime, timezone
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", str(ROOT / "compose.integrated.yml")]


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def query(container, database, sql):
    return run(
        ["docker", "exec", container, "psql", "-U", "localdbadmin", "-d", database, "-Atc", sql], capture_output=True, text=True
    ).stdout.strip()


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    out = (ROOT / "outputs/assever-integrated-evidence" / ("backup-" + stamp)).resolve()
    assert ROOT in out.parents
    out.mkdir(parents=True, exist_ok=False)
    container = run(COMPOSE + ["ps", "-q", "postgres"], capture_output=True, text=True).stdout.strip()
    assert container
    apps = ["gateway", "worker", "evaluator", "effects"]
    run(COMPOSE + ["stop"] + apps, capture_output=True)
    proof = []
    try:
        for database in ("intentseal", "purchase_effects"):
            dump = out / (database + ".dump")
            with dump.open("wb") as stream:
                run(["docker", "exec", container, "pg_dump", "-U", "localdbadmin", "-Fc", database], stdout=stream)
            restored = "integrated_verify_" + database + "_" + stamp
            run(["docker", "exec", container, "createdb", "-U", "localdbadmin", restored])
            with dump.open("rb") as stream:
                run(
                    ["docker", "exec", "-i", container, "pg_restore", "-U", "localdbadmin", "-d", restored],
                    stdin=stream,
                )
            tables = query(
                container,
                database,
                "SELECT schemaname||'.'||tablename FROM pg_tables WHERE schemaname IN ('public','purchase','purchase_effects') ORDER BY 1",
            ).splitlines()
            for table in tables:
                assert re.fullmatch(r"[a-z_][a-z_0-9]*\.[a-z_][a-z_0-9]*", table)
                sql = f"SELECT count(*)::text||':'||coalesce(md5(string_agg(row_to_json(t)::text,',' ORDER BY row_to_json(t)::text)),'empty') FROM {table} t"
                before = query(container, database, sql)
                after = query(container, restored, sql)
                assert before == after, (database, table)
                proof.append({"database": database, "table": table, "source": before, "restored": after, "match": True})
        (out / "verification.json").write_text(json.dumps(proof, indent=2))
        print(json.dumps({"tables_verified": len(proof), "proof": str(out / "verification.json")}))
    finally:
        run(COMPOSE + ["up", "--wait", "-d"] + apps)


if __name__ == "__main__":
    main()
