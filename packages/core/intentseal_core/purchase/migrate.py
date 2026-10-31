"""Versioned additive purchase migrations in an isolated schema of existing PostgreSQL."""

import os
from pathlib import Path
import psycopg
from .common import db


def migrate():
    sink = os.environ.get("SERVICE_MODE") == "sink"
    schema = "purchase_effects" if sink else "purchase"
    with psycopg.connect(os.environ["DATABASE_URL"]) as c:
        c.execute("SELECT pg_advisory_xact_lock(471980)")
        c.execute("CREATE SCHEMA IF NOT EXISTS " + schema)
    path = Path(__file__).parent / "migrations"
    with db() as c:
        c.execute("SELECT pg_advisory_xact_lock(471980)")
        if sink:
            if not c.execute("SELECT to_regclass('purchase_effects.sink_operations') p").fetchone()["p"]:
                c.execute((path / "002_sink.sql").read_text())
        else:
            if not c.execute("SELECT to_regclass('purchase.schema_versions') p").fetchone()["p"]:
                c.execute((path / "001_purchase.sql").read_text())
            if not c.execute("SELECT 1 FROM schema_versions WHERE version=2").fetchone():
                c.execute("""CREATE TABLE workflow_bindings(
                    root text PRIMARY KEY REFERENCES contracts(id), workflow text UNIQUE NOT NULL,
                    contract_hash text NOT NULL, created double precision NOT NULL)""")
                c.execute("INSERT INTO schema_versions(version) VALUES(2)")
            if not c.execute("SELECT 1 FROM schema_versions WHERE version=3").fetchone():
                c.execute("""CREATE TABLE agent_principals(
                    actor text NOT NULL, tenant text NOT NULL, owner text NOT NULL,
                    source text NOT NULL, expires double precision NOT NULL,
                    PRIMARY KEY(actor,tenant))""")
                c.execute("INSERT INTO schema_versions(version) VALUES(3)")
            if not c.execute("SELECT 1 FROM schema_versions WHERE version=4").fetchone():
                c.execute("ALTER TABLE workflow_bindings ADD COLUMN policy_snapshot jsonb")
                c.execute("ALTER TABLE workflow_bindings ADD COLUMN policy_digest text")
                c.execute("INSERT INTO schema_versions(version) VALUES(4)")
            if not c.execute("SELECT 1 FROM schema_versions WHERE version=5").fetchone():
                for statement in (
                    "CREATE INDEX ix_purchase_reservations_root_bucket ON reservations(root,bucket)",
                    "CREATE INDEX ix_purchase_quotes_root_digest ON quotes(root,digest)",
                    "CREATE INDEX ix_purchase_grants_actor_epoch ON grants(root,actor,epoch,expires)",
                    "CREATE INDEX ix_purchase_proposals_root ON proposals(root)",
                    "CREATE INDEX ix_purchase_exception_review ON exceptions(root,state,expires)",
                    "CREATE INDEX ix_purchase_root_owner ON contracts(tenant,owner,created DESC)",
                    "CREATE INDEX ix_purchase_lab_owner ON lab_runs(tenant,created DESC)",
                    "CREATE INDEX ix_purchase_model_owner ON model_runs(tenant,created DESC)",
                    "CREATE INDEX ix_purchase_outbox_schedule ON outbox(state,next_attempt)",
                ):
                    c.execute(statement)
                if c.execute("SELECT to_regclass('public.delegate_contracts') p").fetchone()["p"]:
                    c.execute(
                        "CREATE INDEX IF NOT EXISTS ix_delegate_contract_workflow_version ON public.delegate_contracts(workflow_id,version DESC)"
                    )
                c.execute("INSERT INTO schema_versions(version) VALUES(5)")


if __name__ == "__main__":
    migrate()
