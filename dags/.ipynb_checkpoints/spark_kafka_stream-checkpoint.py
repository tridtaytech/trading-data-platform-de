#!/usr/bin/env python3
import logging
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, explode
from pyspark.sql.types import *

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kafka_stream")

spark = SparkSession.builder \
    .appName("binance_candle_sticks") \
    .getOrCreate()

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribePattern", "binance.*") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()
    # .option("subscribe", "binance.spot") \
    # .option("subscribe", "binance.spot,binance.future_usdt,binance.futures_coin") \


candle_schema = StructType([
    StructField("source", StringType()),
    StructField("type", StringType()),
    StructField("market", StringType()),
    StructField("symbol", StringType()),
    StructField("interval", StringType()),
    StructField("event_time", StringType()),
    StructField("open_time", StringType()),
    StructField("close_time", StringType()),
    StructField("is_closed", BooleanType()),
    StructField("open", DoubleType()),
    StructField("high", DoubleType()),
    StructField("low", DoubleType()),
    StructField("close", DoubleType()),
    StructField("volume", DoubleType()),
    StructField("quote_volume", DoubleType()),
    StructField("trades", LongType()),
    StructField("taker_buy_base", DoubleType()),
    StructField("taker_buy_quote", DoubleType()),
])

payload_schema = StructType([
    StructField("candle_stick", ArrayType(candle_schema))
])

json_df = df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), payload_schema).alias("data"))

candles = json_df.select(explode(col("data.candle_stick")).alias("c")).select("c.*")

def write_to_postgres(batch_df, batch_id):
    rows = batch_df.collect()
    if not rows:
        logger.info("No rows in this batch.")
        return

    conn = psycopg2.connect(
        # host="pg01.internal.kiwcomp.com",
        host="pg01",
        port=5432,
        dbname="stocks",
        user="airflow",
        password="airflowpass",
    )
    cur = conn.cursor()

    inserted = 0
    for row in rows:
        rec = row.asDict()
        cur.execute(
            """
            INSERT INTO candle_sticks (
                source, type, market, symbol, interval,
                event_time, open_time, close_time, is_closed,
                open, high, low, close, volume,
                quote_volume, trades,
                taker_buy_base, taker_buy_quote
            )
            VALUES (
                %(source)s, %(type)s, %(market)s, %(symbol)s, %(interval)s,
                %(event_time)s, %(open_time)s, %(close_time)s, %(is_closed)s,
                %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s,
                %(quote_volume)s, %(trades)s,
                %(taker_buy_base)s, %(taker_buy_quote)s
            )
            ON CONFLICT DO NOTHING;
            """,
            rec,
        )
        inserted += 1

    conn.commit()
    logger.info(f"Inserted {inserted} rows into candle_sticks")
    cur.close()
    conn.close()

query = candles.writeStream \
    .outputMode("append") \
    .foreachBatch(write_to_postgres) \
    .start()

query.awaitTermination()
