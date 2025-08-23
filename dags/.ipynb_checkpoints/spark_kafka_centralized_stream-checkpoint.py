#!/usr/bin/env python3
import logging
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, explode
from pyspark.sql.types import *

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kafka_stream")

# -----------------------------
# Spark Session
# -----------------------------
spark = SparkSession.builder \
    .appName("multi_stream") \
    .getOrCreate()

# -----------------------------
# Stream 1: funding_rate
# -----------------------------
funding_schema = StructType([
    StructField("exchange", StringType()),
    StructField("symbol", StringType()),
    StructField("funding_time", TimestampType()),
    StructField("funding_rate", DoubleType()),
    StructField("mark_price", DoubleType())
])

funding_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "funding_rate") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

funding_json = funding_df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), funding_schema).alias("data"))

funding_rates = funding_json.select("data.*")

# -----------------------------
# Stream 2: binance_candle_sticks
# -----------------------------
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

candle_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribePattern", "binance.*") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

candle_json = candle_df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), payload_schema).alias("data"))

candles = candle_json.select(explode(col("data.candle_stick")).alias("c")).select("c.*")

# -----------------------------
# Shared writer to Postgres
# -----------------------------
def write_to_postgres(batch_df, batch_id, table, host, port, dbname, user, password):
    rows = batch_df.collect()
    if not rows:
        logger.info(f"No rows in this batch for {table}.")
        return

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    cur = conn.cursor()

    inserted = 0
    for row in rows:
        rec = row.asDict()
        if table == "funding_rate_history":
            cur.execute(
                """
                INSERT INTO funding_rate_history (
                    exchange, symbol, funding_time, funding_rate, mark_price
                )
                VALUES (
                    %(exchange)s, %(symbol)s, %(funding_time)s, %(funding_rate)s, %(mark_price)s
                )
                ON CONFLICT DO NOTHING;
                """,
                rec,
            )
        elif table == "candle_sticks":
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
    logger.info(f"Inserted {inserted} rows into {table}")
    cur.close()
    conn.close()

# -----------------------------
# Start both queries
# -----------------------------
query1 = funding_rates.writeStream \
    .outputMode("append") \
    .foreachBatch(lambda df, batch_id: write_to_postgres(df, batch_id, "funding_rate_history",host="pgdev",port=5432,dbname="kimtest",user="kiwadmin",password="kiwpass@1689")) \
    .start()

query2 = candles.writeStream \
    .outputMode("append") \
    .foreachBatch(lambda df, batch_id: write_to_postgres(df, batch_id, "candle_sticks", host="pg01",port=5432,dbname="stocks",user="airflow",password="airflowpass")) \
    .start()

spark.streams.awaitAnyTermination()
