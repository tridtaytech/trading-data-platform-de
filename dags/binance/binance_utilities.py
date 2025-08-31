from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 🔗 Import your ORM tables
from trading_kiwcomp_models.models.binance.data.BinanceSpotExchangeInfoSymbol import BinanceSpotExchangeInfoSymbolTable
from trading_kiwcomp_models.models.binance.data.BinanceFutureUSDTExchangeInfoSymbol import BinanceFutureUSDTExchangeInfoSymbolTable
from trading_kiwcomp_models.models.binance.data.BinanceFutureCOINMExchangeInfoSymbol import BinanceFutureCOINMExchangeInfoSymbolTable

# --- Registry ---
EXCHANGE_INFO_TABLES = {
    "spot": BinanceSpotExchangeInfoSymbolTable,
    "futures_usdt": BinanceFutureUSDTExchangeInfoSymbolTable,
    "futures_coinm": BinanceFutureCOINMExchangeInfoSymbolTable,
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
        rows = session.query(Table.symbol).all()
        return [r[0] for r in rows]  # flatten to simple list of strings
    finally:
        session.close()
