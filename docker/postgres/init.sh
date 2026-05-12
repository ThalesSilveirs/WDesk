#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE evolution;
    CREATE DATABASE evogo_auth;
    CREATE DATABASE evogo_users;
EOSQL
