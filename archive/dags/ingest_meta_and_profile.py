# # ingest_meta_and_profile.py
# import json
# from datetime import datetime, timezone, timedelta
# from airflow.providers.postgres.hooks.postgres import PostgresHook
# import psycopg2.extras as extras

# DDL = """
# CREATE TABLE IF NOT EXISTS symbols (
#   ticker text PRIMARY KEY,
#   name text,
#   exchange text,
#   currency text,
#   created_at timestamptz NOT NULL DEFAULT now(),
#   updated_at timestamptz NOT NULL DEFAULT now()
# );

# CREATE TABLE IF NOT EXISTS symbol_profile (
#   ticker text PRIMARY KEY REFERENCES symbols(ticker) ON DELETE CASCADE,
#   short_name text,
#   long_name text,
#   sector text,
#   sector_key text,
#   industry text,
#   industry_key text,
#   website text,
#   phone text,
#   address1 text,
#   city text,
#   state text,
#   zip text,
#   country text,
#   fulltime_employees integer,
#   description text,
#   prev_name text,
#   name_change_at timestamptz,
#   ipo_expected_date date,
#   updated_at timestamptz NOT NULL DEFAULT now()
# );

# CREATE TABLE IF NOT EXISTS company_officers (
#   id bigserial PRIMARY KEY,
#   ticker text NOT NULL REFERENCES symbols(ticker) ON DELETE CASCADE,
#   name text,
#   title text,
#   age integer,
#   fiscal_year integer,
#   total_pay numeric,
#   exercised_value numeric,
#   unexercised_value numeric
# );
# CREATE INDEX IF NOT EXISTS idx_company_officers_ticker ON company_officers(ticker);

# CREATE TABLE IF NOT EXISTS vendor_snapshots (
#   id bigserial PRIMARY KEY,
#   ticker text NOT NULL REFERENCES symbols(ticker) ON DELETE CASCADE,
#   vendor text NOT NULL DEFAULT 'yahoo',
#   snapshot_ts timestamptz NOT NULL DEFAULT now(),
#   payload jsonb NOT NULL
# );
# CREATE INDEX IF NOT EXISTS gin_vendor_snapshots_payload ON vendor_snapshots USING GIN (payload);

# CREATE TABLE IF NOT EXISTS ohlcv_daily (
#   ticker text REFERENCES symbols(ticker) ON DELETE CASCADE,
#   ts_date date NOT NULL,
#   open double precision,
#   high double precision,
#   low double precision,
#   close double precision,
#   adj_close double precision,
#   volume bigint,
#   dividends double precision,
#   stock_splits double precision,
#   PRIMARY KEY (ticker, ts_date)
# );
# """

# def pg():
#     return PostgresHook(postgres_conn_id="pg01-db-stocks").get_conn()

# def ensure_tables(conn):
#     with conn.cursor() as cur:
#         cur.execute(DDL)

# def epoch_to_ts(e):
#     try:
#         return datetime.fromtimestamp(int(e), tz=timezone.utc)
#     except Exception:
#         return None

# def upsert_symbol(conn, ticker, info):
#     name = info.get("displayName") or info.get("longName") or info.get("shortName") or ticker
#     exchange = info.get("fullExchangeName") or info.get("exchange")
#     currency = info.get("currency")
#     with conn.cursor() as cur:
#         cur.execute("""
#             INSERT INTO symbols (ticker, name, exchange, currency, created_at, updated_at)
#             VALUES (%s, %s, %s, %s, now(), now())
#             ON CONFLICT (ticker) DO UPDATE SET
#               name = EXCLUDED.name,
#               exchange = EXCLUDED.exchange,
#               currency = EXCLUDED.currency,
#               updated_at = now();
#         """, (ticker, name, exchange, currency))

# def upsert_profile(conn, ticker, info):
#     row = {
#         "ticker": ticker,
#         "short_name": info.get("shortName"),
#         "long_name": info.get("longName"),
#         "sector": info.get("sector"),
#         "sector_key": info.get("sectorKey"),
#         "industry": info.get("industryDisp") or info.get("industry"),
#         "industry_key": info.get("industryKey"),
#         "website": info.get("website"),
#         "phone": info.get("phone"),
#         "address1": info.get("address1"),
#         "city": info.get("city"),
#         "state": info.get("state"),
#         "zip": info.get("zip"),
#         "country": info.get("country"),
#         "fulltime_employees": info.get("fullTimeEmployees"),
#         "description": info.get("longBusinessSummary"),
#         "prev_name": info.get("prevName"),
#         "name_change_at": epoch_to_ts(info.get("nameChangeDate")),
#         "ipo_expected_date": None if not info.get("ipoExpectedDate") else info["ipoExpectedDate"],
#     }
#     cols = ", ".join(row.keys())
#     placeholders = ", ".join(["%s"]*len(row))
#     updates = ", ".join([f"{k}=EXCLUDED.{k}" for k in row.keys() if k != "ticker"])
#     with conn.cursor() as cur:
#         cur.execute(f"""
#             INSERT INTO symbol_profile ({cols})
#             VALUES ({placeholders})
#             ON CONFLICT (ticker) DO UPDATE SET
#               {updates},
#               updated_at = now();
#         """, list(row.values()))

# def replace_officers(conn, ticker, officers):
#     with conn.cursor() as cur:
#         cur.execute("DELETE FROM company_officers WHERE ticker = %s", (ticker,))
#     if not officers:
#         return
#     rows = [
#         (
#             ticker,
#             o.get("name"),
#             o.get("title"),
#             o.get("age"),
#             o.get("fiscalYear"),
#             o.get("totalPay"),
#             o.get("exercisedValue"),
#             o.get("unexercisedValue"),
#         )
#         for o in officers
#     ]
#     with conn.cursor() as cur:
#         extras.execute_values(cur, """
#             INSERT INTO company_officers
#               (ticker, name, title, age, fiscal_year, total_pay, exercised_value, unexercised_value)
#             VALUES %s
#         """, rows, page_size=200)

# def insert_snapshot(conn, ticker, payload, vendor="yahoo"):
#     with conn.cursor() as cur:
#         cur.execute("""
#             INSERT INTO vendor_snapshots (ticker, vendor, payload)
#             VALUES (%s, %s, %s::jsonb)
#         """, (ticker, vendor, json.dumps(payload)))

# def get_latest_ts_date(conn, ticker):
#     with conn.cursor() as cur:
#         cur.execute("SELECT max(ts_date) FROM ohlcv_daily WHERE ticker=%s", (ticker,))
#         row = cur.fetchone()
#         return row[0]  # date or None

# def upsert_daily(conn, ticker, df):
#     # Lazy import here to avoid heavy import at DAG parse time
#     import pandas as pd

#     if df is None or getattr(df, "empty", True):
#         return
#     df = df.rename(columns={
#         "Open":"open","High":"high","Low":"low","Close":"close",
#         "Adj Close":"adj_close","Volume":"volume",
#         "Dividends":"dividends","Stock Splits":"stock_splits",
#     })
#     df.index = pd.to_datetime(df.index).tz_localize(None)
#     df["ts_date"] = df.index.date
#     cols = ["ts_date","open","high","low","close","adj_close","volume","dividends","stock_splits"]
#     for c in cols:
#         if c not in df.columns:
#             df[c] = None
#     df = df[cols]
#     rows = [(ticker, *r) for r in df.itertuples(index=False, name=None)]
#     with conn.cursor() as cur:
#         extras.execute_values(cur, """
#             INSERT INTO ohlcv_daily
#               (ticker, ts_date, open, high, low, close, adj_close, volume, dividends, stock_splits)
#             VALUES %s
#             ON CONFLICT (ticker, ts_date) DO UPDATE SET
#               open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low, close=EXCLUDED.close,
#               adj_close=EXCLUDED.adj_close, volume=EXCLUDED.volume,
#               dividends=EXCLUDED.dividends, stock_splits=EXCLUDED.stock_splits;
#         """, rows, page_size=10_000)

# def ingest(ticker: str):
#     # Lazy import to keep DAG parse fast
#     import yfinance as yf

#     ticker = ticker.upper()
#     t = yf.Ticker(ticker)

#     try:
#         info = t.get_info() or {}
#     except Exception:
#         info = {"longName": ticker}

#     with pg() as conn:
#         # ensure_tables(conn)
#         upsert_symbol(conn, ticker, info)
#         upsert_profile(conn, ticker, info)
#         replace_officers(conn, ticker, info.get("companyOfficers", []))
#         insert_snapshot(conn, ticker, info, vendor="yahoo")

#         # Incremental: from last stored date + 1 day → now
#         latest = get_latest_ts_date(conn, ticker)
#         if latest:
#             start = latest + timedelta(days=1)
#             hist = t.history(start=start, interval="1d", auto_adjust=False)
#         else:
#             hist = t.history(period="max", interval="1d", auto_adjust=False)

#         upsert_daily(conn, ticker, hist)
#         conn.commit()
