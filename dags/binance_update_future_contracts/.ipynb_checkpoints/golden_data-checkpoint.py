import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.postgresql_connection import get_postgres_connection

SQL_INSERT_GOLDEN =  """
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

def golden_data(
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
    ) -> str:
    """Build the golden arbitrage table by inserting fresh rows using a direct psycopg2 connection."""
    conn = get_postgres_connection(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    cur = conn.cursor()
    try:
        cur.execute(SQL_INSERT_GOLDEN)
        rows = cur.rowcount
        conn.commit()
        return f"✅ Inserted {rows} rows into binance_spot_future_contract_golden"
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"❌ Failed to build golden table: {e}")
    finally:
        cur.close()
        conn.close()