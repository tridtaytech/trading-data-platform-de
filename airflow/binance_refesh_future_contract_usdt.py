# dags/binance_refresh_contracts.py
from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta, timezone
import requests

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="binance_refesh_future_contract_usdt",
    start_date=datetime(2025, 8, 17),
    schedule="@daily",    # refresh contract info once per day
    catchup=False,
    default_args=default_args,
    tags=["binance", "contracts"],
) as dag:

    @task
    def refresh_contracts():
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        symbols = resp.json()["symbols"]

        hook = PostgresHook(postgres_conn_id="pg01-db-stocks")
        conn = hook.get_conn()
        cur = conn.cursor()

        for data in symbols:
            if not data.get("contractType"):  # skip spot-only symbols
                continue

            # convert Binance timestamps (ms) → datetime
            delivery_date = (
                datetime.fromtimestamp(data["deliveryDate"]/1000, tz=timezone.utc)
                if data.get("deliveryDate") else None
            )
            onboard_date = (
                datetime.fromtimestamp(data["onboardDate"]/1000, tz=timezone.utc)
                if data.get("onboardDate") else None
            )

            cur.execute("""
                INSERT INTO futures_contracts 
                    (contract_code, contract_type, delivery_date, onboard_date, status, last_updated)
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (contract_code) DO UPDATE
                SET contract_type = EXCLUDED.contract_type,
                    delivery_date = EXCLUDED.delivery_date,
                    onboard_date = EXCLUDED.onboard_date,
                    status = EXCLUDED.status,
                    underlying_type = 'usdt',
                    last_updated = now();
            """, (
                data["symbol"],
                data["contractType"],
                delivery_date,
                onboard_date,
                data["status"]
            ))

        conn.commit()
        cur.close()
        conn.close()
        return f"Upserted {len(symbols)} contracts"

    refresh_contracts()
