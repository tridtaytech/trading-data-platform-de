from datetime import datetime, timezone
import requests
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.postgresql_connection import get_postgres_connection

def refresh_contracts(
    url: str,
    underlying_type: str,
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
) -> str:
    """
    Fetch Binance Futures contracts and upsert into Postgres.

    Args:
        url (str): Binance API endpoint (default: USDT-M exchangeInfo).
        env_path (str): Path to the .env file for DB credentials.
        underlying_type (str): Label for contract type (usdt/coincm).

    Returns:
        str: Summary of how many contracts were upserted.
    """
    # Fetch contracts from Binance
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    symbols = resp.json().get("symbols", [])

    # Connect using your helper
    conn = get_postgres_connection(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    cur = conn.cursor()

    upserts = 0
    for data in symbols:
        if not data.get("contractType"):  # skip spot-only symbols
            continue

        # Convert timestamps (ms → datetime)
        delivery_date = (
            datetime.fromtimestamp(data["deliveryDate"] / 1000, tz=timezone.utc)
            if data.get("deliveryDate") else None
        )
        onboard_date = (
            datetime.fromtimestamp(data["onboardDate"] / 1000, tz=timezone.utc)
            if data.get("onboardDate") else None
        )

        cur.execute(
            """
            INSERT INTO futures_contracts 
                (contract_code, contract_type, delivery_date, onboard_date, status, underlying_type, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (contract_code) DO UPDATE
            SET contract_type   = EXCLUDED.contract_type,
                delivery_date   = EXCLUDED.delivery_date,
                onboard_date    = EXCLUDED.onboard_date,
                status          = EXCLUDED.status,
                underlying_type = EXCLUDED.underlying_type,
                last_updated    = now();
            """,
            (
                data["symbol"],
                data["contractType"],
                delivery_date,
                onboard_date,
                data.get("status", "TRADING"),
                underlying_type,  # <-- make sure it's set on insert
            ),
        )
        upserts += 1

    conn.commit()
    cur.close()
    conn.close()

    return f"✅ Upserted {upserts} {underlying_type.upper()} contracts"

def run_test():
    conn = get_postgres_connection(
        host="localhost",
        port=5432,
        dbname="airflow",
        user="airflow",
        password="airflow", 
    )
    cur = conn.cursor()

    try:
        print("1️⃣ Ensure test table futures_contracts exists...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS futures_contracts (
                contract_code   TEXT PRIMARY KEY,
                contract_type   TEXT,
                delivery_date   TIMESTAMPTZ,
                onboard_date    TIMESTAMPTZ,
                status          TEXT,
                underlying_type TEXT,
                last_updated    TIMESTAMPTZ DEFAULT now()
            );
        """)
        conn.commit()

        print("2️⃣ Run refresh_contracts for USDT-M...")
        msg_usdt = refresh_contracts(
            url="https://fapi.binance.com/fapi/v1/exchangeInfo",
            underlying_type="usdt",
            host="localhost",
            port=5432,
            dbname="airflow",
            user="airflow",
            password="airflow", 
        )
        print(msg_usdt)

        print("3️⃣ Run refresh_contracts for COIN-M...")
        msg_coinm = refresh_contracts(
            url="https://dapi.binance.com/dapi/v1/exchangeInfo",
            underlying_type="coincm",
            host="localhost",
            port=5432,
            dbname="airflow",
            user="airflow",
            password="airflow", 
        )
        print(msg_coinm)

        print("4️⃣ Query row counts...")
        cur.execute("SELECT COUNT(*) FROM futures_contracts;")
        row_count = cur.fetchone()[0]
        print(f"➡️ Total rows in futures_contracts = {row_count}")

        cur.execute("SELECT COUNT(*) FROM futures_contracts WHERE underlying_type='usdt';")
        usdt_count = cur.fetchone()[0]
        print(f"➡️ USDT contracts = {usdt_count}")

        cur.execute("SELECT COUNT(*) FROM futures_contracts WHERE underlying_type='coincm';")
        coinm_count = cur.fetchone()[0]
        print(f"➡️ COIN-M contracts = {coinm_count}")

        print("✅ Test complete.")

    except Exception as e:
        print("❌ Test failed:", e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_test()