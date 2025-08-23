# # dags/sp500_ingest_all.py
# from airflow import DAG
# from airflow.decorators import task
# from airflow.providers.postgres.hooks.postgres import PostgresHook
# from datetime import datetime, timedelta
# # from ingest_meta_and_profile import ingest  # your existing function

# @task
# def get_all_tickers():
#     hook = PostgresHook(postgres_conn_id="pg01-db-stocks")
#     with hook.get_conn() as conn:
#         with conn.cursor() as cur:
#             cur.execute("SELECT symbol FROM sp500_tickers ORDER BY symbol")
#             return [r[0] for r in cur.fetchall()]

# @task
# def ingest_one_ticker(ticker: str):
#     # Lazy import so DAG parse doesn't load heavy modules
#     from ingest_meta_and_profile import ingest
#     ingest(ticker)

# default_args = {
#     "owner": "airflow",
#     "retries": 2,
#     "retry_delay": timedelta(minutes=5),
# }

# with DAG(
#     dag_id="sp500_ingest_all",
#     default_args=default_args,
#     start_date=datetime(2025, 8, 14),
#     schedule="@daily",
#     catchup=False,
#     max_active_runs=1,  # prevents overlapping runs
#     max_active_tasks=2,
# ) as dag:
#     tickers = get_all_tickers()
#     ingest_one_ticker.expand(ticker=tickers)  # dynamic task mapping
