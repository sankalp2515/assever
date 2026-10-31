CREATE ROLE intentseal_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD 'synthetic-local-only';
ALTER DATABASE intentseal OWNER TO intentseal_app;
REVOKE CONNECT ON DATABASE intentseal FROM PUBLIC;
GRANT CONNECT ON DATABASE intentseal TO intentseal_app;
CREATE ROLE purchase_effects LOGIN PASSWORD 'synthetic-effects-local-only';
CREATE DATABASE purchase_effects OWNER purchase_effects;
REVOKE CONNECT ON DATABASE purchase_effects FROM PUBLIC;
GRANT CONNECT ON DATABASE purchase_effects TO purchase_effects;
