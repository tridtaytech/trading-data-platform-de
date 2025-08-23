import psycopg2

def cleanup_tables(
        tables: list[str],
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
    ):
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    cur = conn.cursor()
    try:
        for table in tables:
            cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
            print(f"✅ Truncated {table}")
        conn.commit()
        return f"✅ Truncated {len(tables)} tables"
    finally:
        cur.close()
        conn.close()

