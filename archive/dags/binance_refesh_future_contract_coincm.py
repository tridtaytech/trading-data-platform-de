# # dags/binance_refresh_contracts_coinm.py
# from airflow import DAG
# from airflow.decorators import task
# from airflow.providers.postgres.hooks.postgres import PostgresHook
# from datetime import datetime, timedelta, timezone
# import requests

# default_args = {
#     "owner": "airflow",
#     "retries": 1,
#     "retry_delay": timedelta(minutes=2),
# }

# # COIN-M (delivery) exchange info endpoint
# EXCHANGE_INFO_URL = "https://dapi.binance.com/dapi/v1/exchangeInfo"

# with DAG(
#     dag_id="binance_refesh_future_contract_coincm",
#     start_date=datetime(2025, 8, 17),
#     schedule="@daily",      # refresh once per day
#     catchup=False,
#     default_args=default_args,
#     tags=["binance", "contracts", "coin-m"],
# ) as dag:

#     @task
#     def refresh_contracts():
#         resp = requests.get(EXCHANGE_INFO_URL, timeout=20)
#         resp.raise_for_status()
#         payload = resp.json()
#         symbols = payload.get("symbols", [])

#         hook = PostgresHook(postgres_conn_id="pg01-db-stocks")
#         conn = hook.get_conn()
#         cur = conn.cursor()

#         upserts = 0
#         for s in symbols:
#             # Skip non-futures just in case
#             ctype = s.get("contractType")  # e.g. PERPETUAL, CURRENT_QUARTER, NEXT_QUARTER
#             if not ctype:
#                 continue

#             # Timestamps (ms) -> aware datetimes
#             delivery_ms = s.get("deliveryDate")
#             onboard_ms  = s.get("onboardDate")
#             delivery_date = (
#                 datetime.fromtimestamp(delivery_ms / 1000, tz=timezone.utc)
#                 if delivery_ms else None
#             )
#             onboard_date = (
#                 datetime.fromtimestamp(onboard_ms / 1000, tz=timezone.utc)
#                 if onboard_ms else None
#             )
            


#             cur.execute(
#                 """
#                 INSERT INTO futures_contracts
#                     (contract_code, contract_type, delivery_date, onboard_date, status, last_updated)
#                 VALUES (%s, %s, %s, %s, %s, now())
#                 ON CONFLICT (contract_code) DO UPDATE
#                 SET contract_type = EXCLUDED.contract_type,
#                     delivery_date = EXCLUDED.delivery_date,
#                     onboard_date  = EXCLUDED.onboard_date,
#                     status        = EXCLUDED.status,
#                     underlying_type   = 'coincm',
#                     last_updated  = now();
#                 """,
#                 (
#                     s.get("symbol"),         # e.g. BTCUSD_250926
#                     ctype,                   # PERPETUAL/CURRENT_QUARTER/NEXT_QUARTER
#                     delivery_date,
#                     onboard_date,
#                     s.get("status", "TRADING"),
#                 ),
#             )
#             upserts += 1

#         conn.commit()
#         cur.close()
#         conn.close()
#         return f"Upserted {upserts} COIN-M contracts"

#     refresh_contracts()
