"""Upgrade only the known synthetic local integrated volume to a non-superuser app role.

Run with gateway/worker/evaluator stopped, after evidence capture. Does not alter
the retired standalone volumes. Fresh installs already use this role separation.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", str(ROOT / "compose.integrated.yml")]


def main():
    container = subprocess.run(COMPOSE + ["ps", "-q", "postgres"], capture_output=True, text=True, check=True).stdout.strip()
    assert container, "Local PostgreSQL container required"
    expected = subprocess.run(
        ["docker", "inspect", container, "--format", '{{index .Config.Labels "com.docker.compose.project"}}'],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert expected == "assever-integrated", "Only the synthetic integrated project is supported"
    running = subprocess.run(
        COMPOSE + ["ps", "--status", "running", "--services"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert not set(running) & {"gateway", "worker", "evaluator"}, "Stop application writers before changing ownership"
    sql = """
DO $$ BEGIN
 IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='intentseal_app') THEN
   CREATE ROLE intentseal_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD 'synthetic-local-only';
 END IF;
END $$;
ALTER DATABASE intentseal OWNER TO intentseal_app;
REVOKE CONNECT ON DATABASE intentseal FROM PUBLIC;
GRANT CONNECT ON DATABASE intentseal TO intentseal_app;
ALTER SCHEMA public OWNER TO intentseal_app;
ALTER SCHEMA purchase OWNER TO intentseal_app;
DO $$ DECLARE item record; BEGIN
 FOR item IN SELECT schemaname,tablename FROM pg_tables WHERE schemaname IN ('public','purchase') LOOP
   EXECUTE format('ALTER TABLE %I.%I OWNER TO intentseal_app',item.schemaname,item.tablename);
 END LOOP;
END $$;
"""
    subprocess.run(
        ["docker", "exec", "-i", container, "psql", "-U", "localdbadmin", "-d", "intentseal", "-v", "ON_ERROR_STOP=1"],
        input=sql,
        text=True,
        check=True,
    )
    print("Existing synthetic integrated data preserved; application tables now owned by non-superuser intentseal_app.")


if __name__ == "__main__":
    main()
