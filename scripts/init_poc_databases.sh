#!/bin/sh
# Creates the Judge0 database/role alongside the app DB from POSTGRES_DB.
# Runs only on first Postgres data-volume init.
# CREATEDB is required so Judge0's Rails `db:create` entrypoint step succeeds.
set -eu

JUDGE0_PASSWORD="${JUDGE0_POSTGRES_PASSWORD:-judge0_dev_password}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	DO \$\$
	BEGIN
	  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'judge0') THEN
	    CREATE ROLE judge0 LOGIN PASSWORD '${JUDGE0_PASSWORD}' CREATEDB;
	  END IF;
	END
	\$\$;

	SELECT 'CREATE DATABASE judge0 OWNER judge0'
	WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'judge0')\gexec

	GRANT ALL PRIVILEGES ON DATABASE judge0 TO judge0;
EOSQL
