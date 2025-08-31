from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta, timezone
import requests
from binance_update_future_contracts.refresh_contracts import refresh_contracts
from binance_update_future_contracts.golden_data import golden_data
from shared.postgresql_utilitys import cleanup_tables

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

postgres_db = {
    "host"  : "pg01",
    "port" : 5432,
    "dbname" : "stocks",
    "user" : "airflow",
    "password" : "airflowpass"
}

with DAG(
    dag_id="binance_refresh_future_contracts",
    start_date=datetime(2025, 8, 17),
    schedule="@daily",    # refresh once per day
    catchup=False,
    default_args=default_args,
    tags=["binance", "symbols", "daily"],
) as dag:
        
    @task
    def refresh_usdt_contracts():
        return refresh_contracts(
            url="https://fapi.binance.com/fapi/v1/exchangeInfo",
            underlying_type="usdt",
            host=postgres_db["host"],
            port=postgres_db["port"],
            dbname=postgres_db["dbname"],
            user=postgres_db["user"],
            password=postgres_db["password"],
        )

    @task
    def refresh_coinm_contracts():
        return refresh_contracts(
            url="https://dapi.binance.com/dapi/v1/exchangeInfo",
            underlying_type="coincm",
            host=postgres_db["host"],
            port=postgres_db["port"],
            dbname=postgres_db["dbname"],
            user=postgres_db["user"],
            password=postgres_db["password"],
        )
    
    # clean_old_data_task = clean_old_data()
    usdt_task = refresh_usdt_contracts()
    coinm_task = refresh_coinm_contracts()

    # Dependencies
    # clean_old_data_task >> [usdt_task, coinm_task] >> golden_task
    [usdt_task, coinm_task]
