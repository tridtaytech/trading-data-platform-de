from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
}

with DAG(
    "spark_kafka_streaming_funding_fee_rate",
    default_args=default_args,
    start_date=datetime(2025, 8, 17),
    schedule=None,   # run on trigger
    catchup=False,
    tags=["binance", "spark", "funding_fee_rate"],
) as dag:
    # https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/stable/_modules/airflow/providers/apache/spark/operators/spark_submit.html#SparkSubmitOperator.application
    start_stream = SparkSubmitOperator(
        application="/opt/airflow/dags/spark_kafka_funding_fee_rate_stream.py",
        task_id="start_kafka_stream_funding_fee_rate",
        conn_id="spark_default",   # set in Airflow Connections
        name="funding_fee_rate",
        packages= "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0",
        executor_cores=1,
        executor_memory="1G",
        driver_memory="1G",
        # conf={
        #     "spark.executor.memory": "1g",
        #     "spark.executor.cores": "1",
        #     "spark.driver.memory": "1g"
        # }
    )