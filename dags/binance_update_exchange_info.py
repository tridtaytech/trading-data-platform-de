from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta, timezone
import requests
# from binance_update_future_contracts.refresh_contracts import refresh_contracts
# from binance_update_future_contracts.golden_data import golden_data
from binance.binance_exchange_info import fetch_and_update_exchange_info
from shared.postgresql_utilitys import cleanup_tables

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

postgres_db = {
    "host"  : "pgdev",
    "port" : 5432,
    "dbname" : "testdb",
    "user" : "test",
    "password" : "testpass"
}

with DAG(
    dag_id="binance_update_exchange_info",
    start_date=datetime(2025, 8, 17),
    schedule="@daily",    # refresh once per day
    catchup=False,
    default_args=default_args,
    tags=["binance", "symbols", "daily"],
) as dag:


    @task
    def update_spot_exchange_info():
        return fetch_and_update_exchange_info(
            underlying_type="spot",
            host=postgres_db["host"],
            port=postgres_db["port"],
            dbname=postgres_db["dbname"],
            user=postgres_db["user"],
            password=postgres_db["password"],
        )
        
    @task
    def update_futures_usdt_exchange_info():
        return fetch_and_update_exchange_info(
            underlying_type="futures_usdt",
            host=postgres_db["host"],
            port=postgres_db["port"],
            dbname=postgres_db["dbname"],
            user=postgres_db["user"],
            password=postgres_db["password"],
        )

    @task
    def update_futures_coinm_exchange_info():
        return fetch_and_update_exchange_info(
            underlying_type="futures_coinm",
            host=postgres_db["host"],
            port=postgres_db["port"],
            dbname=postgres_db["dbname"],
            user=postgres_db["user"],
            password=postgres_db["password"],
        )
        
    spot_task = update_spot_exchange_info()
    futures_usdt_task = update_futures_usdt_exchange_info()
    futures_coinm_task = update_futures_coinm_exchange_info()
    [spot_task, futures_usdt_task, futures_coinm_task]
