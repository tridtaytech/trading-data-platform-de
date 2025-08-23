from airflow import DAG
from airflow.decorators import task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

SQL_INSERT_GOLDEN = """
INSERT INTO binance_spot_future_contract_golden (
    symbol, contract_code, market_type,
    spot_price, futures_price,
    delivery_date, spot_open_time, futures_open_time,
    ttm_days, basis_pct, apy, event_time
)
SELECT
    s.symbol, 
    f.symbol AS contract_code,
    f.market,
    s.close AS spot_price,
    f.close AS futures_price,
    fc.delivery_date AS delivery_date,
    s.open_time AS spot_open_time,
    f.open_time AS futures_open_time,
    ROUND(EXTRACT(EPOCH FROM (fc.delivery_date - now()))/86400, 2) AS ttm_days,
    ROUND((f.close - s.close)/s.close, 4) AS basis_pct,
    ROUND(
        ((f.close - s.close)/s.close) 
        * (365 / NULLIF(EXTRACT(EPOCH FROM (fc.delivery_date - now()))/86400,0)), 
        4
    ) AS apy,
    now() AS event_time
FROM candle_sticks s
JOIN candle_sticks f
  ON (
       -- USDT-M: exact match
       (f.market = 'futures_usdt' AND split_part(f.symbol, '_', 1) = s.symbol)
       OR
       -- COIN-M: normalize USDT → USD
       (f.market = 'futures_coin' AND regexp_replace(s.symbol, 'USDT$', 'USD') = split_part(f.symbol, '_', 1))
     )
 AND s.open_time = f.open_time
JOIN futures_contracts fc
  ON f.symbol = fc.contract_code
WHERE s.market = 'spot'
  AND f.market IN ('futures_usdt','futures_coin')
  AND f.is_closed = true
  AND s.is_closed = true
  AND s.open_time >= (CURRENT_TIMESTAMP AT TIME ZONE 'utc') - interval '2.2 minute'
"""

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

with DAG(
    dag_id="binance_spot_future_contract_golden",
    start_date=datetime(2025, 8, 17),
    schedule="* * * * *",   # รันทุก 1 นาที
    catchup=False,
    default_args=default_args,
    tags=["binance", "golden"],
) as dag:

    @task
    def build_golden_table():
        hook = PostgresHook(postgres_conn_id="pg01-db-stocks")  # Airflow connection ต้องมีชื่อ pg01
        conn = hook.get_conn()
        cur = conn.cursor()
        cur.execute(SQL_INSERT_GOLDEN)
        rows = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return f"Inserted {rows} rows"

    build_golden_table()
