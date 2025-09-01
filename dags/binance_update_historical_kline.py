# from airflow import DAG
# from airflow.decorators import task
# from datetime import datetime, timedelta

# from binance.binance_exchange_info import fetch_and_update_exchange_info
# from shared.postgresql_utilitys import cleanup_tables
# from binance.binance_kline import fetch_and_update_kline
# from binance.binance_utilities import get_symbols   # 👈 your helper

# default_args = {
#     "owner": "airflow",
#     "retries": 1,
#     "retry_delay": timedelta(minutes=2),
# }

# postgres_db = {
#     "host": "pgdev",
#     "port": 5432,
#     "dbname": "testdb",
#     "user": "test",
#     "password": "testpass"
# }

# with DAG(
#     dag_id="binance_update_exchange_info_and_klines",
#     start_date=datetime(2025, 8, 17),
#     schedule="@daily",    # refresh once per day
#     catchup=False,
#     default_args=default_args,
#     tags=["binance", "symbols", "klines", "daily", "v2"],
#     max_active_runs=1, 
#     max_active_tasks=5,
# ) as dag:

#     # # --- update exchange info ---
#     # @task
#     # def update_exchange_info(underlying_type: str):
#     #     return fetch_and_update_exchange_info(
#     #         underlying_type=underlying_type,
#     #         host=postgres_db["host"],
#     #         port=postgres_db["port"],
#     #         dbname=postgres_db["dbname"],
#     #         user=postgres_db["user"],
#     #         password=postgres_db["password"],
#     #     )

#     # def get_all_symbols(underlying_type: str):
#     #     return get_symbols(underlying_type, postgres_db)

#     # --- expand over symbols ---
#     @task(pool="binance_update_historical_kline")
#     def fetch_kline_for_symbol(underlying_type: str, symbol: str, interval: str = "1d"):
#         return fetch_and_update_kline(
#             underlying_type=underlying_type,
#             symbol=symbol,
#             interval=interval,
#             host=postgres_db["host"],
#             port=postgres_db["port"],
#             dbname=postgres_db["dbname"],
#             user=postgres_db["user"],
#             password=postgres_db["password"],
#         )

#     # 🔹 Example for Futures USDT
#     # futures_usdt_info = update_exchange_info("futures_usdt")
#     # futures_usdt_symbols = get_all_symbols("futures_usdt")
#     fetch_futures_usdt_klines = fetch_kline_for_symbol.partial(underlying_type="futures_usdt").expand(
#         symbol=get_symbols(underlying_type="futures_usdt", db_conf=postgres_db)
#     )

#     # 🔹 You can do the same for Spot and COIN-M
#     # spot_info = update_exchange_info("spot")
#     # spot_symbols = get_all_symbols("spot")
#     fetch_spot_klines = fetch_kline_for_symbol.partial(underlying_type="spot").expand(
#         symbol=get_symbols(underlying_type="spot", db_conf=postgres_db)
#     )

#     # coinm_info = update_exchange_info("futures_coinm")
#     # coinm_symbols = get_all_symbols("futures_coinm")
#     fetch_futures_coinm_klines = fetch_kline_for_symbol.partial(underlying_type="futures_coinm").expand(
#         symbol=get_symbols(underlying_type="futures_coinm", db_conf=postgres_db)
#     )

#     # --- Dependencies ---
#     # futures_usdt_info >> futures_usdt_symbols >> fetch_usdt_klines
#     # spot_info >> spot_symbols >> fetch_spot_klines
#     # coinm_info >> coinm_symbols >> fetch_coinm_klines
#     # futures_usdt_symbols >> fetch_usdt_klines
#     # spot_symbols >> fetch_spot_klines
#     # coinm_symbols >> fetch_coinm_klines
#     fetch_futures_usdt_klines >> fetch_futures_coinm_klines >> fetch_spot_klines
