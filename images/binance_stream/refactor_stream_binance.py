#!/usr/bin/env python3
# binance_to_kafka.py
import os, sys, json, asyncio
from datetime import datetime, timezone
import websockets
from kafka import KafkaProducer
import psycopg2
import logging

BINANCE_WS  = {
    "spot":         "wss://stream.binance.com:9443",
    "futures_usdt": "wss://fstream.binance.com",
    "futures_coin": "wss://dstream.binance.com",
}

class BinanceStreamConfiguration():
    def __init__(
        kafka_url, 
        kafka_topic, 
        interval, 
        final_only, 
        debug,
        market,
        db {
            host :
                port
        }
        ):
        self.name = name
        self.age = age
        self.height = height
        self.email = email

    def __repr__(self):
        return (f'{self.__class__.__name__}(name={self.name}, age={self.age}, height={self.height}, email={self.email})')

class BinanceStreamKafka():
    def __init__(config : BinanceStreamConfiguration):
      self.config = config
    


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
KAFKA_TOPIC = cfg.get("kafka_topic", "binance.stream")
INTERVAL    = cfg.get("interval", "1m")
FINAL_ONLY  = str(cfg.get("final_only", "true")).lower() in {"1","true","yes","on"}
DEBUG       = str(cfg.get("debug", "true")).lower() in {"1","true","yes","on"}
MARKET      = cfg.get("market", "futures_usdt").lower()
DB_CONFIG   = cfg.get("db", {})
USE_DB      = bool(cfg.get("use_db", True))
EVENT_TYPE  = cfg.get("event_type", "kline").lower()  # 👈 choose: kline OR markpriceupdate

BINANCE_WS  = {
    "spot":         "wss://stream.binance.com:9443",
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
            utype_map = {"spot": "spot", "futures_usdt": "usdt", "futures_coin": "coincm"}
            utype = utype_map.get(MARKET, "spot")
            cur.execute("SELECT symbol FROM target_symbols WHERE underlying_type = %s;", (utype,))
            rows = cur.fetchall()
            cur.close(); conn.close()
            symbols = [r[0].lower() for r in rows]
            if symbols:
                print(f"[db] fetched {len(symbols)} symbols for underlying_type={utype}")
                return symbols
        except Exception as e:
            print(f"[db] Failed to fetch symbols: {e}", file=sys.stderr)

    cfg_symbols = [s.lower() for arr in cfg.get("symbols", {}).values() for s in arr]
    print(f"[config] using symbols from config: {cfg_symbols}")
    return cfg_symbols

SYMBOLS = get_symbols()

def iso(ms: int) -> str:
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).isoformat()

def build_url(symbols) -> str:
    if EVENT_TYPE == "markpriceupdate":
        streams = "/".join(f"{s}@markPrice" for s in symbols)
    else:  # default kline
        streams = "/".join(f"{s}@kline_{INTERVAL}" for s in symbols)
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
        if DEBUG: print(f"[kafka] warm-up OK -> {md.topic} p{md.partition} off={md.offset}", flush=True)
    except Exception as e:
        print(f"[kafka] warm-up FAILED: {e}", file=sys.stderr); sys.exit(3)

# ==== main loop ====
async def main():
    if not SYMBOLS:
        print("SYMBOLS cannot be empty", file=sys.stderr); sys.exit(2)

    url = build_url(SYMBOLS)
    if DEBUG:
        print(f"[debug] event_type={EVENT_TYPE} market={MARKET} ws={url}\n[debug] topic={KAFKA_TOPIC}", flush=True)

    await warmup()

    backoff = 1
    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=60,
                                          open_timeout=20, close_timeout=5) as ws:
                backoff = 1
                async for msg in ws:
                    obj = json.loads(msg)
                    d = obj.get("data") or {}

                    # ---- Funding (markPriceUpdate) ----
                    if EVENT_TYPE == "markpriceupdate":
                        if d.get("e") != "markPriceUpdate": continue
                        rec = {
                            "source": "binance", "type": "funding_rate", "market": MARKET,
                            "symbol": d.get("s"),
                            "event_time": iso(int(d.get("E", 0))),
                            "mark_price": float(d.get("p", 0.0)),
                            "index_price": float(d.get("i", 0.0)),
                            "settle_price": float(d.get("P", 0.0)),
                            "funding_rate": float(d.get("r", 0.0)),
                            "funding_time": iso(int(d.get("T", 0))),
                        }
                        key = rec["symbol"]; payload = rec

                    # ---- Klines ----
                    else:
                        if d.get("e") != "kline": continue
                        k = d.get("k") or {}
                        if FINAL_ONLY and not k.get("x", False): continue
                        rec = {
                            "source": "binance", "type": "kline", "market": MARKET,
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
                        key = rec["symbol"]; payload = {"candle_stick": [rec]}

                    # ---- Send to Kafka ----
                    try:
                        fut = producer.send(KAFKA_TOPIC, value=payload, key=key)
                        md = await asyncio.to_thread(fut.get, 10)
                        print(f"[kafka] sent -> {md.topic} p{md.partition} off={md.offset} ({rec['symbol']})", flush=True)
                    except Exception as e:
                        print(f"[kafka] send error: {e}", file=sys.stderr)

        except Exception as e:
            print(f"[reconnect] {type(e).__name__}: {e}", file=sys.stderr)
            await asyncio.sleep(backoff); backoff = min(backoff * 2, 30)

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass

# #!/usr/bin/env python3
# # binance_to_kafka.py
# import os, sys, json, asyncio
# from datetime import datetime, timezone
# import websockets
# from kafka import KafkaProducer
# import psycopg2
# import logging

# logger = logging.getLogger("binance_to_kafka")
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s"
# )

# CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")

# try:
#     with open(CONFIG_PATH, "r") as f:
#         cfg = json.load(f)
# except Exception as e:
#     print(f"Failed to load config from {CONFIG_PATH}: {e}", file=sys.stderr)
#     sys.exit(1)

# KAFKAURL    = cfg.get("kafka_url", "127.0.0.1:9092")
# KAFKA_TOPIC = cfg.get("kafka_topic", "binance.candles")
# INTERVAL    = cfg.get("interval", "1m")
# FINAL_ONLY  = str(cfg.get("final_only", "true")).lower() in {"1","true","yes","on"}
# DEBUG       = str(cfg.get("debug", "true")).lower() in {"1","true","yes","on"}
# MARKET      = cfg.get("market", "").lower()
# DB_CONFIG   = cfg.get("db", {})
# USE_DB      = bool(cfg.get("", True))
# BINANCE_WS  = {
#     "spot":        "wss://stream.binance.com:9443",
#     "futures_usdt": "wss://fstream.binance.com",
#     "futures_coin": "wss://dstream.binance.com",
# }.get(MARKET, "wss://stream.binance.com:9443")
# EVENT_TYPE = cfg.get("event_type", "").lower()

# # ==== helpers ====
# def get_symbols():
#     print(f"[debug] USE_DB={USE_DB}")
#     if USE_DB:
#         try:
#             conn = psycopg2.connect(
#                 host=DB_CONFIG.get("host", "localhost"),
#                 port=DB_CONFIG.get("port", 5432),
#                 user=DB_CONFIG.get("user", "airflow"),
#                 password=DB_CONFIG.get("password", "airflowpass"),
#                 dbname=DB_CONFIG.get("dbname", "stocks")
#             )
#             cur = conn.cursor()

#             # map MARKET to underlying_type
#             utype_map = {
#                 "spot": "spot",
#                 "futures_usdt": "usdt",
#                 "futures_coin": "coincm"
#             }
#             utype = utype_map.get(MARKET, "spot")

#             cur.execute("SELECT symbol FROM target_symbols WHERE underlying_type = %s;", (utype,))
#             rows = cur.fetchall()
#             cur.close()
#             conn.close()

#             symbols = [r[0].lower() for r in rows]

#             if symbols:
#                 print(f"[db] fetched {len(symbols)} symbols for underlying_type={utype}: {symbols}")
#                 return symbols
#             else:
#                 print(f"[db] no symbols found for underlying_type={utype}, falling back to config")

#         except Exception as e:
#             print(f"[db] Failed to fetch symbols: {e}", file=sys.stderr)
#     # fallback
#     cfg_symbols = [s.lower() for arr in cfg.get("symbols", {}).values() for s in arr]
#     print(f"[config] using symbols from config: {cfg_symbols}")
#     return cfg_symbols


# SYMBOLS     = get_symbols()

# def iso(ms: int) -> str:
#     return datetime.fromtimestamp(ms/1000, tz=timezone.utc).isoformat()

# # def build_url(symbols, interval) -> str:
# #     streams = "/".join(f"{s}@kline_{interval}" for s in symbols)
# #     return f"{BINANCE_WS}/stream?streams={streams}"
# def build_url(symbols) -> str:
#     streams = []
#     if EVENT_TYPE == "markpriceupdate":
#         # Default markPrice stream (3s) OR fast 1s mode if enabled in config
#         use_1s = bool(cfg.get("funding_1s", False))  # new config flag
#         suffix = "@markPrice@1s" if use_1s else "@markPrice"
#         streams = [f"{s}{suffix}" for s in symbols]

#     elif EVENT_TYPE == "kline":
#         streams = [f"{s}@kline_{INTERVAL}" for s in symbols]

#     else:
#         raise ValueError(f"Unsupported event_type={EVENT_TYPE}, must be 'kline' or 'markPriceUpdate'")

#     return f"{BINANCE_WS}/stream?streams={'/'.join(streams)}"


# # ==== Kafka producer ====
# producer = KafkaProducer(
#     bootstrap_servers=[KAFKAURL],
#     value_serializer=lambda v: json.dumps(v).encode("utf-8"),
#     key_serializer=lambda k: None if k is None else str(k).encode("utf-8"),
#     acks="all",
#     retries=3,
#     retry_backoff_ms=500,
#     request_timeout_ms=30000,
#     max_block_ms=60000,
#     api_version_auto_timeout_ms=20000,
# )

# async def warmup():
#     try:
#         md = await asyncio.to_thread(producer.send(KAFKA_TOPIC, {"probe": "ok"}).get, 10)
#         if DEBUG:
#             print(f"[kafka] warm-up OK -> {md.topic} p{md.partition} off={md.offset}", flush=True)
#     except Exception as e:
#         print(f"[kafka] warm-up FAILED: {e}", file=sys.stderr)
#         sys.exit(3)

# # ==== main loop ====
# async def main():
#     if not SYMBOLS:
#         print("SYMBOLS cannot be empty", file=sys.stderr); sys.exit(2)

#     url = build_url(SYMBOLS, INTERVAL)
#     if DEBUG:
#         print(f"[debug] market={MARKET} ws={url}\n[debug] KAFKAURL={KAFKAURL} topic={KAFKA_TOPIC}", flush=True)

#     print(f"[kafka] partitions_for({KAFKA_TOPIC}) = {producer.partitions_for(KAFKA_TOPIC)}", flush=True)
#     await warmup()

#     backoff = 1
#     while True:
#         try:
#             async with websockets.connect(
#                 url,
#                 ping_interval=20,
#                 ping_timeout=60,
#                 open_timeout=20,
#                 close_timeout=5
#             ) as ws:
#                 backoff = 1
#                 async for msg in ws:
#                     obj = json.loads(msg)
#                     d = obj.get("data") or {}
#                     if d.get("e") != "kline":
#                         continue

#                     k = d.get("k") or {}
#                     if FINAL_ONLY and not k.get("x", False):
#                         continue

#                     rec = {
#                         "source": "binance",
#                         "type": "kline",
#                         "market": MARKET,
#                         "symbol": d.get("s"),
#                         "interval": k.get("i"),
#                         "event_time": iso(int(d.get("E", 0))),
#                         "open_time":  iso(int(k.get("t", 0))),
#                         "close_time": iso(int(k.get("T", 0))),
#                         "is_closed": bool(k.get("x", False)),
#                         "open":  float(k.get("o", 0.0)),
#                         "high":  float(k.get("h", 0.0)),
#                         "low":   float(k.get("l", 0.0)),
#                         "close": float(k.get("c", 0.0)),
#                         "volume":       float(k.get("v", 0.0)),
#                         "quote_volume": float(k.get("q", 0.0)),
#                         "trades":       int(k.get("n", 0)),
#                         "taker_buy_base":  float(k.get("V", 0.0)),
#                         "taker_buy_quote": float(k.get("Q", 0.0)),
#                     }
#                     payload = {"candle_stick": [rec]}
#                     key = rec["symbol"]

#                     try:
#                         fut = producer.send(KAFKA_TOPIC, value=payload, key=key)
#                         md = await asyncio.to_thread(fut.get, 10)
#                         print(f"[kafka] sent -> {md.topic} p{md.partition} off={md.offset} "
#                               f"({rec['symbol']} {rec['interval']} {rec['close_time']})", flush=True)
#                     except Exception as e:
#                         print(f"[kafka] send error: {e}", file=sys.stderr)
#         except Exception as e:
#             print(f"[reconnect] {type(e).__name__}: {e}", file=sys.stderr)
#             await asyncio.sleep(backoff)
#             backoff = min(backoff * 2, 30)

# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         pass
