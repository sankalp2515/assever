CREATE TABLE IF NOT EXISTS sink_operations(
 id text PRIMARY KEY, digest text NOT NULL, effect jsonb NOT NULL, profile text NOT NULL, fence bigint NOT NULL,
 state text NOT NULL CHECK(state IN ('PENDING','COMMITTED','CLOSED')), due double precision NOT NULL, created double precision NOT NULL, dedupe_until double precision NOT NULL
);
CREATE TABLE IF NOT EXISTS sink_effects(
 id text PRIMARY KEY, operation text NOT NULL REFERENCES sink_operations(id), kind text NOT NULL, body jsonb NOT NULL, created double precision NOT NULL,
 UNIQUE(operation,kind)
);
CREATE TABLE IF NOT EXISTS sink_notices(id text PRIMARY KEY, operation text NOT NULL REFERENCES sink_operations(id), kind text NOT NULL, body jsonb NOT NULL);
