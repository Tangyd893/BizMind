"""
BizMind database setup script.

Run this once to create the bizmind database and user.
Requires the postgres superuser password to be set in
the PGPASSWORD environment variable.

Usage:
    PGPASSWORD=<postgres_password> uv run python scripts/setup_db.py
"""

import os
import sys

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_NAME = "bizmind"
DB_USER = "bizmind"
DB_PASS = "bizmind"
HOST = "127.0.0.1"
PORT = 5432
SUPERUSER = "postgres"


def main() -> None:
    superuser_pass = os.environ.get("PGPASSWORD", "")
    if not superuser_pass:
        print("ERROR: PGPASSWORD environment variable not set.")
        print("Usage: PGPASSWORD=<postgres_password> uv run python scripts/setup_db.py")
        sys.exit(1)

    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        dbname="postgres",
        user=SUPERUSER,
        password=superuser_pass,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Check if user exists
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_USER,))
    if cur.fetchone() is None:
        cur.execute(
            sql.SQL("CREATE ROLE {user} WITH LOGIN PASSWORD %s").format(
                user=sql.Identifier(DB_USER)
            ),
            (DB_PASS,),
        )
        print(f"Created role '{DB_USER}'")
    else:
        print(f"Role '{DB_USER}' already exists")

    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if cur.fetchone() is None:
        cur.execute(
            sql.SQL("CREATE DATABASE {db} OWNER {user}").format(
                db=sql.Identifier(DB_NAME),
                user=sql.Identifier(DB_USER),
            )
        )
        print(f"Created database '{DB_NAME}'")
    else:
        print(f"Database '{DB_NAME}' already exists")

    cur.close()
    conn.close()
    print("Setup complete.")


if __name__ == "__main__":
    main()
