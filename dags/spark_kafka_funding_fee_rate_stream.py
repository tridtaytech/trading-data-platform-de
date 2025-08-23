#!/usr/bin/env python3
import logging
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kafka_stream")

# -----------------------------
# Spark Session
# -----------------------------
spark = SparkSession.builder \
    .appName("funding_fee_rate") \
    .getOrCreate()

# -----------------------------
# Read from Kafka
# -----------------------------
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("subscribe", "funding_rate") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# -----------------------------
# Define Schema for Kafka Message
# -----------------------------
funding_schema = StructType([
    StructField("exchange", StringType()),
    StructField("symbol", StringType()),
    StructField("funding_time", TimestampType()),
    StructField("funding_rate", DoubleType()),
    StructField("mark_price", DoubleType())
])

# -----------------------------
# Parse JSON from Kafka
# -----------------------------
json_df = df.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), funding_schema).alias("data"))

funding_rates = json_df.select("data.*")

# -----------------------------
# Write to PostgreSQL
# -----------------------------
def write_to_postgres(batch_df, batch_id):
    rows = batch_df.collect()
    if not rows:
        logger.info("No rows in this batch.")
        return

    conn = psycopg2.connect(
        host="pg01",          # 👈 host ของคุณ
        port=5432,
        dbname="kimtest",     # 👈 dbname
        user="postgres",      # 👈 user
        password="yourpass",  # 👈 password
    )
    cur = conn.cursor()

    inserted = 0
    for row in rows:
        rec = row.asDict()
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
        inserted += 1

    conn.commit()
    logger.info(f"Inserted {inserted} rows into funding_rate_history")
    cur.close()
    conn.close()

# -----------------------------
# Start Streaming Query
# -----------------------------
query = funding_rates.writeStream \
    .outputMode("append") \
    .foreachBatch(write_to_postgres) \
    .start()

query.awaitTermination()
