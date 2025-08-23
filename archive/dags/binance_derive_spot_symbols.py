# # dags/binance_derive_spot_symbols.py
# from airflow import DAG
# from airflow.decorators import task
# from airflow.providers.postgres.hooks.postgres import PostgresHook
# from datetime import datetime, timedelta

# default_args = {
#     "owner": "airflow",
#     "retries": 1,
#     "retry_delay": timedelta(minutes=2),
# }

# with DAG(
#     dag_id="binance_derive_spot_symbols",
#     start_date=datetime(2025, 8, 17),
#     schedule="@daily",    # or "@hourly" if you want more frequent sync
#     catchup=False,
#     default_args=default_args,
#     tags=["binance", "spot", "contracts"],
# ) as dag:

#     @task
#     def derive_spot_from_delivery():
#         """
#         1. Insert delivery contracts into target_symbols with their contract_code (raw)
#         2. Insert normalized spot symbols derived from those same contracts
#         """
#         hook = PostgresHook(postgres_conn_id="pg01-db-stocks")
#         conn = hook.get_conn()
#         cur = conn.cursor()

#         # Ensure table exists
#         cur.execute("""
#         CREATE TABLE IF NOT EXISTS target_symbols (
#             symbol TEXT,
#             underlying_type TEXT,
#             last_updated TIMESTAMPTZ DEFAULT now(),
#             PRIMARY KEY (symbol, underlying_type)
#         );
#         """)
#         cur.execute("TRUNCATE target_symbols;")


#         # 1️⃣ Insert delivery contracts as-is
#         cur.execute("""
#         INSERT INTO target_symbols (symbol, underlying_type, last_updated)
#         SELECT DISTINCT
#             contract_code AS symbol,
#             underlying_type,
#             now() AS last_updated
#         FROM futures_contracts
#         WHERE contract_type NOT IN ('PERPETUAL', 'PERPETUAL DELIVERING')
#         ON CONFLICT (symbol, underlying_type) DO UPDATE
#         SET last_updated = EXCLUDED.last_updated;
#         """)
#         raw_count = cur.rowcount

#         # 2️⃣ Insert derived spot symbols (normalized)
#         cur.execute("""
#         INSERT INTO target_symbols (symbol, underlying_type, last_updated)
#         SELECT DISTINCT
#             CASE
#                 WHEN right(split_part(contract_code, '_', 1), 3) = 'USD'
#                 THEN split_part(contract_code, '_', 1) || 'T'
#                 ELSE split_part(contract_code, '_', 1)
#             END AS symbol,
#             'spot' AS underlying_type,
#             now() AS last_updated
#         FROM futures_contracts
#         WHERE contract_type NOT IN ('PERPETUAL', 'PERPETUAL DELIVERING')
#         ON CONFLICT (symbol, underlying_type) DO UPDATE
#         SET last_updated = EXCLUDED.last_updated;
#         """)
#         spot_count = cur.rowcount
#         # cur.execute("""
#         # INSERT INTO target_symbols (symbol, underlying_type, last_updated)
#         # SELECT DISTINCT
#         #     split_part(contract_code, '_', 1) AS symbol,
#         #     'spot' AS underlying_type,
#         #     now() AS last_updated
#         # FROM futures_contracts
#         # WHERE contract_type NOT IN ('PERPETUAL', 'PERPETUAL DELIVERING')
#         # ON CONFLICT (symbol, underlying_type) DO UPDATE
#         # SET last_updated = EXCLUDED.last_updated;
#         # """)
#         # spot_count = cur.rowcount

#         conn.commit()
#         cur.close()
#         conn.close()

#         return f"Inserted/updated {raw_count} delivery symbols and {spot_count} derived spot symbols"


#     derive_spot_from_delivery()
