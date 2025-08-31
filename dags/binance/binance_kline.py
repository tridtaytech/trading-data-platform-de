import requests
import time
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

# 🔗 Import your existing models
from trading_kiwcomp_models.models.binance.data.BinanceSpotKline import (
    BinanceSpotKlineMapper,
    BinanceSpotKlineTable,
)
from trading_kiwcomp_models.models.binance.data.BinanceFuturesUSDTKline import (
    BinanceFuturesUSDTKlineMapper,
    BinanceFuturesUSDTKlineTable,
)
from trading_kiwcomp_models.models.binance.data.BinanceFuturesCOINMKline import (
    BinanceFuturesCOINMKlineMapper,
    BinanceFuturesCOINMKlineTable,
)

# --- Registry ---
TABLE_MAP = {
    "spot": (BinanceSpotKlineMapper, BinanceSpotKlineTable),
    "futures_usdt": (BinanceFuturesUSDTKlineMapper, BinanceFuturesUSDTKlineTable),
    "futures_coinm": (BinanceFuturesCOINMKlineMapper, BinanceFuturesCOINMKlineTable),
}

URL_MAP = {
    "spot": "https://api.binance.com/api/v3/klines",
    "futures_usdt": "https://fapi.binance.com/fapi/v1/klines",
    "futures_coinm": "https://dapi.binance.com/dapi/v1/klines",
}

# --- Interval ms map (for pagination) ---
BINANCE_INTERVAL_MS = {
    "1m": 60 * 1000,
    "5m": 5 * 60 * 1000,
    "15m": 15 * 60 * 1000,
    "1h": 60 * 60 * 1000,
    "4h": 4 * 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
    "1M": 30 * 24 * 60 * 60 * 1000,  # approx
}

# --- Helpers ---
def upsert_kline(session, Table, row_dict):
    stmt = insert(Table).values(**row_dict)
    stmt = stmt.on_conflict_do_update(
        index_elements=["symbol", "interval", "open_time"],  # unique key for kline
        set_=row_dict,
    )
    session.execute(stmt)


def fetch_and_update_kline(
    underlying_type: str,
    symbol: str,
    interval: str,
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
) -> str:
    """
    Fetch Binance Kline data (full backfill or incremental) and upsert into Postgres.
    Uses startTime/endTime windowing for pagination.
    """
    if underlying_type not in TABLE_MAP:
        raise ValueError(f"Unsupported underlying_type={underlying_type}, must be one of {list(TABLE_MAP)}")

    Mapper, Table = TABLE_MAP[underlying_type]
    url = URL_MAP[underlying_type]

    # --- Setup DB session
    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # --- Find last open_time in DB
    last_open_time = session.query(Table.open_time).filter_by(symbol=symbol, interval=interval) \
                        .order_by(Table.open_time.desc()).limit(1).scalar()

    if last_open_time:
        # Incremental update → continue from last candle + 1 interval
        interval_ms = BINANCE_INTERVAL_MS[interval]
        current_start = int(last_open_time.timestamp() * 1000) + interval_ms
        print(f"⏩ Continue from {datetime.fromtimestamp(current_start/1000, tz=timezone.utc)}")
    else:
        # No data → full backfill from Binance oldest
        probe = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": 1, "startTime": 0}, timeout=15)
        probe.raise_for_status()
        first = probe.json()
        if first:
            current_start = int(first[0][0])  # openTime of oldest candle
            print(f"📥 No data in DB → backfill from Binance oldest available kline ({datetime.fromtimestamp(current_start/1000, tz=timezone.utc)})")
        else:
            raise RuntimeError("Binance returned no historical data")

    end_time = int(time.time() * 1000)
    step = BINANCE_INTERVAL_MS[interval] * 1500  # Binance max window per call
    upserts = 0

    while current_start < end_time:
        current_end = min(current_start + step, end_time)
        print(f"⏳ Fetching {symbol} {interval} window "
            f"{datetime.fromtimestamp(current_start/1000)} → {datetime.fromtimestamp(current_end/1000)}")

        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "endTime": current_end,
            "limit": 1500,
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 400:
                print(f"⚠️ {symbol} not supported anymore → SKIP")
                session.close()
                return f"SKIPPED {symbol} (400 Bad Request)"
            else:
                raise

        if not data:
            print("⚠️ Binance returned no data for this window, stopping.")
            break
        
        print(f"📊 Received {len(data)} klines")
        for idx, raw in enumerate(data, start=1):
            event = Mapper.from_raw(symbol, interval, raw)
            row = Mapper.to_table(event)

            row_dict = row.__dict__.copy()
            row_dict.pop("_sa_instance_state", None)

            upsert_kline(session, Table, row_dict)
            upserts += 1

            # 🔹 print every 100 rows
            if upserts % 100 == 0:
                print(f"📊 Progress: {upserts} rows inserted so far "
                    f"(last at {datetime.fromtimestamp(raw[0]/1000, tz=timezone.utc)})")

        session.commit()

        print(f"✅ {symbol} {interval}: inserted {len(data)} rows "
              f"({datetime.fromtimestamp(data[0][0]/1000)} → {datetime.fromtimestamp(data[-1][0]/1000)})")

        # move window to one candle after last
        current_start = int(data[-1][0]) + BINANCE_INTERVAL_MS[interval]
        time.sleep(0.25)  # avoid rate limit

    session.close()
    return f"🎯 Upserted {upserts} {underlying_type.upper()} klines for {symbol} {interval} into {Table.__tablename__}"


# --- Test Run ---
def test():
    msg = fetch_and_update_kline(
        underlying_type="futures_usdt",
        symbol="BTCUSDT",
        interval="1d",
        host="pgdev.internal.kiwcomp.com",
        port=5432,
        dbname="testdb",
        user="test",
        password="testpass",
    )
    print(msg)


if __name__ == "__main__":
    test()




# import requests
# import time
# from datetime import datetime, timezone
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.dialects.postgresql import insert

# # 🔗 Import your existing models
# from trading_kiwcomp_models.models.binance.data.BinanceSpotKline import (
#     BinanceSpotKlineMapper,
#     BinanceSpotKlineTable,
# )
# from trading_kiwcomp_models.models.binance.data.BinanceFuturesUSDTKline import (
#     BinanceFuturesUSDTKlineMapper,
#     BinanceFuturesUSDTKlineTable,
# )
# from trading_kiwcomp_models.models.binance.data.BinanceFuturesCOINMKline import (
#     BinanceFuturesCOINMKlineMapper,
#     BinanceFuturesCOINMKlineTable,
# )

# # --- Registry ---
# TABLE_MAP = {
#     "spot": (BinanceSpotKlineMapper, BinanceSpotKlineTable),
#     "futures_usdt": (BinanceFuturesUSDTKlineMapper, BinanceFuturesUSDTKlineTable),
#     "futures_coinm": (BinanceFuturesCOINMKlineMapper, BinanceFuturesCOINMKlineTable),
# }

# URL_MAP = {
#     "spot": "https://api.binance.com/api/v3/klines",
#     "futures_usdt": "https://fapi.binance.com/fapi/v1/klines",
#     "futures_coinm": "https://dapi.binance.com/dapi/v1/klines",
# }

# # --- Interval ms map (for pagination) ---
# BINANCE_INTERVAL_MS = {
#     "1m": 60 * 1000,
#     "5m": 5 * 60 * 1000,
#     "15m": 15 * 60 * 1000,
#     "1h": 60 * 60 * 1000,
#     "4h": 4 * 60 * 60 * 1000,
#     "1d": 24 * 60 * 60 * 1000,
#     "1w": 7 * 24 * 60 * 60 * 1000,
#     "1M": 30 * 24 * 60 * 60 * 1000,  # approx
# }

# # --- Helpers ---
# def upsert_kline(session, Table, row_dict):
#     stmt = insert(Table).values(**row_dict)
#     stmt = stmt.on_conflict_do_update(
#         index_elements=["symbol", "interval", "open_time"],  # unique key for kline
#         set_=row_dict,
#     )
#     session.execute(stmt)

# def fetch_and_update_kline(
#     underlying_type: str,
#     symbol: str,
#     interval: str,
#     host: str,
#     port: int,
#     dbname: str,
#     user: str,
#     password: str,
# ) -> str:
#     """
#     Fetch Binance Kline data (full backfill or incremental) and upsert into Postgres.
#     Uses startTime/endTime windowing.
#     """
#     if underlying_type not in TABLE_MAP:
#         raise ValueError(f"Unsupported underlying_type={underlying_type}, must be one of {list(TABLE_MAP)}")

#     Mapper, Table = TABLE_MAP[underlying_type]
#     url = URL_MAP[underlying_type]

#     # --- Setup DB session
#     engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")
#     Session = sessionmaker(bind=engine)
#     session = Session()

#     # --- Find last open_time in DB
#     last_open_time = session.query(Table.open_time).filter_by(symbol=symbol, interval=interval) \
#                         .order_by(Table.open_time.desc()).limit(1).scalar()

#     if last_open_time:
#         interval_ms = BINANCE_INTERVAL_MS[interval]
#         current_start = int(last_open_time.timestamp() * 1000) + interval_ms
#         print(f"⏩ Continue from {datetime.fromtimestamp(current_start/1000, tz=timezone.utc)}")
#     else:
#         # ask Binance for the oldest available candle
#         probe = requests.get(url, params={"symbol": symbol, "interval": interval, "limit": 1, "startTime": 0}, timeout=15)
#         probe.raise_for_status()
#         first = probe.json()
#         if first:
#             current_start = first[0][0]  # openTime of very first candle
#             print(f"📥 No data in DB → backfill from Binance's oldest available kline ({datetime.fromtimestamp(current_start/1000, tz=timezone.utc)})")
#         else:
#             raise RuntimeError("Binance returned no historical data")


#     end_time = int(time.time() * 1000)
#     step = BINANCE_INTERVAL_MS[interval] * 1500  # Binance max window per call

#     upserts = 0

#     while current_start < end_time:
#         current_end = min(current_start + step, end_time)

#         params = {
#             "symbol": symbol,
#             "interval": interval,
#             "startTime": current_start,
#             "endTime": current_end,
#             "limit": 1500,
#         }

#         resp = requests.get(url, params=params, timeout=30)
#         resp.raise_for_status()
#         data = resp.json()

#         if not data:
#             break

#         for raw in data:
#             event = Mapper.from_raw(symbol, interval, raw)
#             row = Mapper.to_table(event)

#             row_dict = row.__dict__.copy()
#             row_dict.pop("_sa_instance_state", None)

#             upsert_kline(session, Table, row_dict)
#             upserts += 1

#         session.commit()
#         print(f"✅ {symbol} {interval}: inserted {len(data)} rows ({datetime.fromtimestamp(current_start/1000)} → {datetime.fromtimestamp(current_end/1000)})")

#         # move window
#         current_start = int(data[-1][0]) + BINANCE_INTERVAL_MS[interval]
#         time.sleep(0.25)  # avoid rate limit

#     session.close()
#     return f"🎯 Upserted {upserts} {underlying_type.upper()} klines for {symbol} {interval} into {Table.__tablename__}"

# # --- Test Run ---
# def test():
#     msg = fetch_and_update_kline(
#         underlying_type="futures_usdt",
#         symbol="BTCUSDT",
#         interval="1d",
#         host="pgdev.internal.kiwcomp.com",
#         port=5432,
#         dbname="testdb",
#         user="test",
#         password="testpass",
#     )
#     print(msg)

# if __name__ == "__main__":
#     test()
