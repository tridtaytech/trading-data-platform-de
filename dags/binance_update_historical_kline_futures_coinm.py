from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta

from binance.binance_exchange_info import fetch_and_update_exchange_info
from shared.postgresql_utilitys import cleanup_tables
from binance.binance_kline import fetch_and_update_kline
from binance.binance_utilities import get_symbols   # 👈 your helper

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

postgres_db = {
    "host": "pgdev",
    "port": 5432,
    "dbname": "testdb",
    "user": "test",
    "password": "testpass"
}

with DAG(
    dag_id="binance_update_historical_kline_futures_coinm",
    start_date=datetime(2025, 8, 17),
    schedule="@daily",    # refresh once per day
    catchup=False,
    default_args=default_args,
    tags=["binance", "symbols", "klines", "daily", "v2"],
    max_active_runs=1, 
    max_active_tasks=5,
) as dag:

    # --- expand over symbols ---
    @task(pool="binance_update_historical_kline")
    def fetch_kline_for_symbol(underlying_type: str, symbol: str, interval: str = "1d"):
        return fetch_and_update_kline(
            underlying_type=underlying_type,
            symbol=symbol,
            interval=interval,
            host=postgres_db["host"],
            port=postgres_db["port"],
            dbname=postgres_db["dbname"],
            user=postgres_db["user"],
            password=postgres_db["password"],
        )
        
    fetch_futures_coinm_klines = fetch_kline_for_symbol.partial(underlying_type="futures_coinm").expand(
        symbol=get_symbols(underlying_type="futures_coinm", db_conf=postgres_db)
    )
    
    fetch_futures_coinm_klines
