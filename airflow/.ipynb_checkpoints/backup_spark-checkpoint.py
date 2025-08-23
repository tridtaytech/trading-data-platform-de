from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .getOrCreate()
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:29092") \
    .option("startingOffsets", "earliest") \
    .option("subscribe", "binance.spot") \
    .option("failOnDataLoss", "false") \
    .load()

query = df.selectExpr("CAST(value AS STRING)") \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()
