import os
import psycopg2
from psycopg2.extensions import connection

def get_postgres_connection(
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
    ) -> connection:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        conn.autocommit = False
        return conn
    except Exception as e:
        raise RuntimeError(f"Failed to connect to PostgreSQL: {e}")

def run_test():
    try:
        conn = get_postgres_connection(
            host="localhost",
            port=5432,
            dbname="airflow",
            user="airflow",
            password="airflow",                               
        )  # or another .env path
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]

        print("✅ Connection successful!")
        print(f"PostgreSQL version: {version}")

        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Connection failed!")
        print(e)

if __name__ == "__main__":
    run_test()