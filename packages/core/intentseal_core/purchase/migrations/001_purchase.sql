CREATE TABLE IF NOT EXISTS schema_versions(version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS sessions(
 token_hash text PRIMARY KEY, tenant text NOT NULL, actor text NOT NULL, role text NOT NULL CHECK(role IN ('human','agent','evaluator')), csrf text NOT NULL, expires double precision NOT NULL
);
CREATE TABLE IF NOT EXISTS contracts(
 id text PRIMARY KEY, tenant text NOT NULL, owner text NOT NULL, version integer NOT NULL DEFAULT 1,
 epoch bigint NOT NULL DEFAULT 1, state text NOT NULL CHECK(state IN ('DRAFT','ACTIVE','REVOKED')),
 scope jsonb NOT NULL, digest text NOT NULL, nonce_hash text, approved jsonb, history jsonb NOT NULL DEFAULT '[]', created double precision NOT NULL
);
CREATE TABLE IF NOT EXISTS demand_lines(id text PRIMARY KEY, root text NOT NULL REFERENCES contracts(id), name text NOT NULL, UNIQUE(root,name));
CREATE TABLE IF NOT EXISTS slots(id text PRIMARY KEY, root text NOT NULL REFERENCES contracts(id), generation integer NOT NULL DEFAULT 1, UNIQUE(root,generation));
CREATE TABLE IF NOT EXISTS grants(
 id text PRIMARY KEY, root text NOT NULL REFERENCES contracts(id), parent text REFERENCES grants(id), actor text NOT NULL, audience text NOT NULL,
 epoch bigint NOT NULL, expires double precision NOT NULL, scope jsonb NOT NULL, key_version text NOT NULL, signature text NOT NULL
);
CREATE TABLE IF NOT EXISTS quotes(id text PRIMARY KEY, tenant text NOT NULL, root text NOT NULL REFERENCES contracts(id), body jsonb NOT NULL, digest text NOT NULL, expires double precision NOT NULL);
CREATE TABLE IF NOT EXISTS proposals(id text PRIMARY KEY, root text NOT NULL REFERENCES contracts(id), actor text NOT NULL, grant_id text REFERENCES grants(id), body jsonb NOT NULL, digest text NOT NULL);
CREATE TABLE IF NOT EXISTS operations(
 id text PRIMARY KEY, root text NOT NULL REFERENCES contracts(id), slot text NOT NULL REFERENCES slots(id), proposal text NOT NULL REFERENCES proposals(id),
 actor text NOT NULL, grant_id text REFERENCES grants(id), effect jsonb NOT NULL, digest text NOT NULL, contract_version integer NOT NULL, epoch bigint NOT NULL,
 state text NOT NULL CHECK(state IN ('PREPARED','RESERVED','DISPATCHING','UNKNOWN','CONFIRMED','CLOSED_NO_EFFECT')),
 revision bigint NOT NULL DEFAULT 1, created double precision NOT NULL, updated double precision NOT NULL, UNIQUE(proposal)
);
CREATE INDEX IF NOT EXISTS operations_root_state ON operations(root,state);
CREATE TABLE IF NOT EXISTS reservations(
 operation text PRIMARY KEY REFERENCES operations(id), root text NOT NULL REFERENCES contracts(id), money bigint NOT NULL CHECK(money>=0),
 quantities jsonb NOT NULL, bucket text NOT NULL CHECK(bucket IN ('reserved','unknown','captured','closed'))
);
CREATE TABLE IF NOT EXISTS outbox(
 operation text PRIMARY KEY REFERENCES operations(id), state text NOT NULL CHECK(state IN ('PENDING','CLAIMED','DONE','RECONCILE','ESCALATED')),
 generation bigint NOT NULL DEFAULT 0, lease_until double precision NOT NULL DEFAULT 0, attempts integer NOT NULL DEFAULT 0,
 next_attempt double precision NOT NULL DEFAULT 0, error text
);
CREATE TABLE IF NOT EXISTS observations(
 id text PRIMARY KEY, operation text NOT NULL REFERENCES operations(id), source text NOT NULL, event_id text NOT NULL, body jsonb NOT NULL, created double precision NOT NULL,
 UNIQUE(source,event_id)
);
CREATE TABLE IF NOT EXISTS events(
 root text NOT NULL REFERENCES contracts(id), sequence bigint NOT NULL, previous_hash text NOT NULL, hash text NOT NULL, body jsonb NOT NULL, PRIMARY KEY(root,sequence)
);
CREATE TABLE IF NOT EXISTS callbacks(
 source text NOT NULL, message_id text NOT NULL, root text NOT NULL REFERENCES contracts(id), digest text NOT NULL, body jsonb NOT NULL, PRIMARY KEY(source,message_id)
);
CREATE TABLE IF NOT EXISTS exceptions(
 id text PRIMARY KEY, root text NOT NULL REFERENCES contracts(id), effect jsonb NOT NULL, digest text NOT NULL, old_scope jsonb NOT NULL,
 new_scope jsonb NOT NULL, expires double precision NOT NULL, nonce_hash text NOT NULL, state text NOT NULL CHECK(state IN ('PENDING','APPROVED','REJECTED','USED')), version integer NOT NULL
);
CREATE TABLE IF NOT EXISTS lab_runs(id text PRIMARY KEY, tenant text NOT NULL, manifest jsonb NOT NULL, result jsonb NOT NULL, created double precision NOT NULL);
CREATE TABLE IF NOT EXISTS model_runs(id text PRIMARY KEY, tenant text NOT NULL, manifest jsonb NOT NULL, result jsonb NOT NULL, created double precision NOT NULL);
INSERT INTO schema_versions(version) VALUES (1) ON CONFLICT DO NOTHING;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS control text NOT NULL DEFAULT 'adaptive';
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS is_lab boolean NOT NULL DEFAULT false;
