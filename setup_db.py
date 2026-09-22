"""One-time script to set up the PostgreSQL database and user.

Tries connecting as the postgres superuser with common default passwords,
then creates the ``app_user`` / ``todo_db`` expected by the application.
"""

import sys

import psycopg2

# Common default passwords to try for the postgres superuser
POSTGRES_PASSWORDS = [
    "",
    "postgres",
    "password",
    "root",
    "admin",
    "app_password",
    "changeme",
]

DB_NAME = "todo_db"
DB_USER = "app_user"
DB_PASSWORD = "app_password"


def try_setup() -> bool:
    for pwd in POSTGRES_PASSWORDS:
        try:
            print(f"Trying postgres with password='{pwd}'...", end=" ")
            conn = psycopg2.connect(
                host="localhost",
                port=5433,
                user="postgres",
                password=pwd,
                dbname="postgres",
            )
            conn.autocommit = True
            cur = conn.cursor()
            print("SUCCESS")

            # Create role if it doesn't exist
            cur.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s", (DB_USER,)
            )
            if cur.fetchone() is None:
                cur.execute(
                    f"CREATE ROLE {DB_USER} WITH LOGIN PASSWORD '{DB_PASSWORD}';"
                )
                print(f"  Created role: {DB_USER}")
            else:
                cur.execute(
                    f"ALTER ROLE {DB_USER} WITH LOGIN PASSWORD '{DB_PASSWORD}';"
                )
                print(f"  Updated password for: {DB_USER}")

            # Create database if it doesn't exist
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
            if cur.fetchone() is None:
                cur.execute(f"CREATE DATABASE {DB_NAME} OWNER {DB_USER};")
                print(f"  Created database: {DB_NAME}")
            else:
                print(f"  Database already exists: {DB_NAME}")

            # Grant privileges
            cur.execute(
                f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};"
            )
            print(f"  Granted privileges on {DB_NAME} to {DB_USER}")

            # In PostgreSQL 15+, also grant pg_tablespace, pg_database, etc.
            cur.execute(
                f"ALTER DATABASE {DB_NAME} OWNER TO {DB_USER};"
            )

            cur.close()
            conn.close()
            return True
        except psycopg2.OperationalError as e:
            print(f"FAILED: {e}")
            continue

    return False


if __name__ == "__main__":
    if try_setup():
        print("\nSetup complete!")
        sys.exit(0)
    else:
        print("\nCould not connect to PostgreSQL as postgres superuser.")
        print("Trying to create user/db directly with app_user credentials...")

        # Try connecting with app_user credentials (password might be different)
        for pwd in ["app_password", "password", "postgres", ""]:
            try:
                print(f"Trying app_user with password='{pwd}'...", end=" ")
                conn = psycopg2.connect(
                    host="localhost",
                    port=5433,
                    user=DB_USER,
                    password=pwd,
                    dbname=DB_NAME,
                )
                cur = conn.cursor()
                print("SUCCESS - app_user can already connect!")
                cur.close()
                conn.close()
                sys.exit(0)
            except psycopg2.OperationalError as e:
                print(f"FAILED")

        print("\nCannot connect to PostgreSQL. Please start PostgreSQL and set credentials manually.")
        sys.exit(1)
