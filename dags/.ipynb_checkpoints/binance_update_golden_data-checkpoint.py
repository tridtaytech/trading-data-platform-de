from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta, timezone
from binance_update_future_contracts.golden_data import golden_data

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
    dag_id="binance_golden_data",
    start_date=datetime(2025, 8, 17),
     schedule="* * * * *",    # refresh once per day
    catchup=False,
    default_args=default_args,
    tags=["binance", "contracts", "real-time"],
) as dag:

    @task
    def build_golden_table():
        return golden_data(
            host=postgres_db["host"],
            port=postgres_db["port"],
            dbname=postgres_db["dbname"],
            user=postgres_db["user"],
            password=postgres_db["password"],
        ) 
    
    golden_task = build_golden_table()

