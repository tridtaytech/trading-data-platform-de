from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🔗 Import your ORM tables
from trading_kiwcomp_models.models.binance.data.BinanceSpotExchangeInfoSymbol import BinanceSpotExchangeInfoSymbolTable
from trading_kiwcomp_models.models.binance.data.BinanceFuturesUSDTExchangeInfoSymbol import BinanceFuturesUSDTExchangeInfoSymbolTable
from trading_kiwcomp_models.models.binance.data.BinanceFuturesCOINMExchangeInfoSymbol import BinanceFuturesCOINMExchangeInfoSymbolTable

# --- Registry ---
EXCHANGE_INFO_TABLES = {
    "spot": BinanceSpotExchangeInfoSymbolTable,
    "futures_usdt": BinanceFuturesUSDTExchangeInfoSymbolTable,
    "futures_coinm": BinanceFuturesCOINMExchangeInfoSymbolTable,
}

def get_symbols(underlying_type: str, db_conf: dict) -> list[str]:
    """
    Get all symbols from DB for a given underlying type.
    Returns: ["BTCUSDT", "ETHUSDT", ...]
    """
    if underlying_type not in EXCHANGE_INFO_TABLES:
        raise ValueError(
            f"Unsupported underlying_type={underlying_type}, must be one of {list(EXCHANGE_INFO_TABLES)}"
        )
    Table = EXCHANGE_INFO_TABLES[underlying_type]

    # --- Setup DB session
    engine = create_engine(
        f"postgresql+psycopg2://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['dbname']}"
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        if underlying_type in ("spot", "futures_usdt"):
            rows = session.query(Table.symbol).filter(Table.status != "PENDING_TRADING").all()
        elif underlying_type == "futures_coinm":
            rows = session.query(Table.symbol).all()
        else:
            rows = []

        return [r[0] for r in rows]  # flatten to simple list of strings
    finally:
        session.close()
