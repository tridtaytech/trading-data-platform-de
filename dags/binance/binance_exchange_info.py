import requests
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from trading_kiwcomp_models.models.binance.data.BinanceFutureCOINMExchangeInfoSymbol import (
    BinanceFutureCOINMExchangeInfoSymbolMapper,
    BinanceFutureCOINMExchangeInfoSymbolTable,
)
from trading_kiwcomp_models.models.binance.data.BinanceFutureUSDTExchangeInfoSymbol import (
    BinanceFutureUSDTExchangeInfoSymbolMapper,
    BinanceFutureUSDTExchangeInfoSymbolTable,
)
from trading_kiwcomp_models.models.binance.data.BinanceSpotExchangeInfoSymbol import (
    BinanceSpotExchangeInfoSymbolMapper,
    BinanceSpotExchangeInfoSymbolTable,
)

TABLE_MAP = {
    "futures_usdt": (BinanceFutureUSDTExchangeInfoSymbolMapper, BinanceFutureUSDTExchangeInfoSymbolTable),
    "futures_coinm": (BinanceFutureCOINMExchangeInfoSymbolMapper, BinanceFutureCOINMExchangeInfoSymbolTable),
    "spot": (BinanceSpotExchangeInfoSymbolMapper, BinanceSpotExchangeInfoSymbolTable),
}
URL_MAP = {
    "futures_usdt": "https://fapi.binance.com/fapi/v1/exchangeInfo",
    "futures_coinm": "https://dapi.binance.com/dapi/v1/exchangeInfo", 
    "spot": "https://api.binance.com/api/v3/exchangeInfo",
}

def upsert_symbol(session, Table, row_dict):
    stmt = insert(Table).values(**row_dict)
    stmt = stmt.on_conflict_do_update(
        index_elements=['symbol'],  # unique column
        set_=row_dict
    )
    session.execute(stmt)

def fetch_and_update_exchange_info(
    underlying_type: str,
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
) -> str:
    """
    Fetch Binance ExchangeInfo and upsert into Postgres for the right table.
    """
    if underlying_type not in TABLE_MAP:
        raise ValueError(f"Unsupported underlying_type={underlying_type}, must be one of {list(TABLE_MAP)}")

    Mapper, Table = TABLE_MAP[underlying_type]
    url = URL_MAP[underlying_type]

    # 1️⃣ Fetch from Binance
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    symbols = resp.json().get("symbols", [])

    # 2️⃣ Setup DB session
    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")
    Session = sessionmaker(bind=engine)
    session = Session()
    
    upserts = 0
    for raw in symbols:
        event = Mapper.from_raw(raw)
        row = Mapper.to_table(event) 

        row = Mapper.to_table(event)
        row_dict = row.__dict__.copy()
        row_dict.pop("_sa_instance_state", None)
        upsert_symbol(session, Table, row_dict)
        upserts += 1
        print(f"[UPSERT {upserts}] {row_dict.get('symbol')} into {Table.__tablename__}")

    session.commit()
    session.close()

    return f"✅ Upserted {upserts} {underlying_type.upper()} symbols into {Table.__tablename__}"

def test():
    msg = fetch_and_update_exchange_info(
        # underlying_type="spot",
        # underlying_type="futures_coinm",
        underlying_type="futures_usdt",
        host="pgdev.internal.kiwcomp.com",
        port=5432,
        dbname="testdb",
        user="test",
        password="testpass",
    )
    print(msg)

if __name__ == "__main__":
    test()
