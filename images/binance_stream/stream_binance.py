#!/usr/bin/env python3
# binance_to_kafka.py
import os, sys, json, asyncio
from datetime import datetime, timezone
import websockets
from kafka import KafkaProducer
import psycopg2
import logging

logger = logging.getLogger("binance_to_kafka")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")

try:
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
except Exception as e:
    print(f"Failed to load config from {CONFIG_PATH}: {e}", file=sys.stderr)
    sys.exit(1)

KAFKAURL    = cfg.get("kafka_url", "127.0.0.1:9092")
KAFKA_TOPIC = cfg.get("kafka_topic", "binance.candles")
INTERVAL    = cfg.get("interval", "1m")
FINAL_ONLY  = str(cfg.get("final_only", "true")).lower() in {"1","true","yes","on"}
DEBUG       = str(cfg.get("debug", "true")).lower() in {"1","true","yes","on"}
MARKET      = cfg.get("market", "futures_coin").lower()
DB_CONFIG   = cfg.get("db", {})  # {host, port, user, password, dbname}
USE_DB      = bool(cfg.get("use_db", True))

BINANCE_WS  = {
    "spot":        "wss://stream.binance.com:9443",
    "futures_usdt": "wss://fstream.binance.com",
    "futures_coin": "wss://dstream.binance.com",
}.get(MARKET, "wss://stream.binance.com:9443")
# ==== helpers ====
def get_symbols():
    print(f"[debug] USE_DB={USE_DB}")
    if USE_DB:
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG.get("host", "localhost"),
                port=DB_CONFIG.get("port", 5432),
                user=DB_CONFIG.get("user", "airflow"),
                password=DB_CONFIG.get("password", "airflowpass"),
                dbname=DB_CONFIG.get("dbname", "stocks")
            )
            cur = conn.cursor()

            # map MARKET to underlying_type
            utype_map = {
                "spot": "spot",
                "futures_usdt": "usdt",
                "futures_coin": "coincm"
            }
            utype = utype_map.get(MARKET, "spot")

            cur.execute("SELECT symbol FROM target_symbols WHERE underlying_type = %s;", (utype,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            symbols = [r[0].lower() for r in rows]

            if symbols:
                print(f"[db] fetched {len(symbols)} symbols for underlying_type={utype}: {symbols}")
                return symbols
            else:
                print(f"[db] no symbols found for underlying_type={utype}, falling back to config")

        except Exception as e:
            print(f"[db] Failed to fetch symbols: {e}", file=sys.stderr)
    # fallback
    cfg_symbols = [s.lower() for arr in cfg.get("symbols", {}).values() for s in arr]
    print(f"[config] using symbols from config: {cfg_symbols}")
    return cfg_symbols


SYMBOLS     = get_symbols()

def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).isoformat()

def build_url(symbols, interval) -> str:
    streams = "/".join(f"{s}@kline_{interval}" for s in symbols)
    return f"{BINANCE_WS}/stream?streams={streams}"

# ==== Kafka producer ====
producer = KafkaProducer(
    bootstrap_servers=[KAFKAURL],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: None if k is None else str(k).encode("utf-8"),
    acks="all",
    retries=3,
    retry_backoff_ms=500,
    request_timeout_ms=30000,
    max_block_ms=60000,
    api_version_auto_timeout_ms=20000,
)

async def warmup():
    try:
        md = await asyncio.to_thread(producer.send(KAFKA_TOPIC, {"probe": "ok"}).get, 10)
        if DEBUG:
            print(f"[kafka] warm-up OK -> {md.topic} p{md.partition} off={md.offset}", flush=True)
    except Exception as e:
        print(f"[kafka] warm-up FAILED: {e}", file=sys.stderr)
        sys.exit(3)

# ==== main loop ====
async def main():
    if not SYMBOLS:
        print("SYMBOLS cannot be empty", file=sys.stderr); sys.exit(2)

    url = build_url(SYMBOLS, INTERVAL)
    if DEBUG:
        print(f"[debug] market={MARKET} ws={url}\n[debug] KAFKAURL={KAFKAURL} topic={KAFKA_TOPIC}", flush=True)

    print(f"[kafka] partitions_for({KAFKA_TOPIC}) = {producer.partitions_for(KAFKA_TOPIC)}", flush=True)
    await warmup()

    backoff = 1
    while True:
        try:
            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=60,
                open_timeout=20,
                close_timeout=5
            ) as ws:
                backoff = 1
                async for msg in ws:
                    obj = json.loads(msg)
                    d = obj.get("data") or {}
                    if d.get("e") != "kline":
                        continue

                    k = d.get("k") or {}
                    if FINAL_ONLY and not k.get("x", False):
                        continue

                    rec = {
                        "source": "binance",
                        "type": "kline",
                        "market": MARKET,
                        "symbol": d.get("s"),
                        "interval": k.get("i"),
                        "event_time": iso(int(d.get("E", 0))),
                        "open_time":  iso(int(k.get("t", 0))),
                        "close_time": iso(int(k.get("T", 0))),
                        "is_closed": bool(k.get("x", False)),
                        "open":  float(k.get("o", 0.0)),
                        "high":  float(k.get("h", 0.0)),
                        "low":   float(k.get("l", 0.0)),
                        "close": float(k.get("c", 0.0)),
                        "volume":       float(k.get("v", 0.0)),
                        "quote_volume": float(k.get("q", 0.0)),
                        "trades":       int(k.get("n", 0)),
                        "taker_buy_base":  float(k.get("V", 0.0)),
                        "taker_buy_quote": float(k.get("Q", 0.0)),
                    }
                    payload = {"candle_stick": [rec]}
                    key = rec["symbol"]

                    try:
                        fut = producer.send(KAFKA_TOPIC, value=payload, key=key)
                        md = await asyncio.to_thread(fut.get, 10)
                        print(f"[kafka] sent -> {md.topic} p{md.partition} off={md.offset} "
                              f"({rec['symbol']} {rec['interval']} {rec['close_time']})", flush=True)
                    except Exception as e:
                        print(f"[kafka] send error: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[reconnect] {type(e).__name__}: {e}", file=sys.stderr)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
