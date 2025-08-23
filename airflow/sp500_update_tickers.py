# dags/sp500_update_tickers.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import pandas as pd

def sp500_tickers():
    try:
        import yfinance as yf
        syms = yf.tickers_sp500()
        if syms:
            return [s.replace('.', '-').upper() for s in syms]
    except Exception:
        pass

    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    syms = df['Symbol'].astype(str).tolist()
    return [s.replace('.', '-').upper() for s in syms]

def update_ticker_table():
    hook = PostgresHook(postgres_conn_id="pg01-db-stocks")  # set in Airflow Connections UI
    tickers = sp500_tickers()
    
    with hook.get_conn() as conn:
        with conn.cursor() as cur:
            for symbol in tickers:
                cur.execute("""
                    INSERT INTO sp500_tickers (symbol, created_at, updated_at)
                    VALUES (%s, NOW(), NOW())
                    ON CONFLICT (symbol)
                    DO UPDATE SET updated_at = NOW();
                """, (symbol,))
        conn.commit()

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="sp500_update_tickers",
    default_args=default_args,
    start_date=datetime(2025, 8, 14),
    schedule="@daily",
    catchup=False,
) as dag:
    update_task = PythonOperator(
        task_id="update_tickers",
        python_callable=update_ticker_table,
        pool="default_pool"
    )
