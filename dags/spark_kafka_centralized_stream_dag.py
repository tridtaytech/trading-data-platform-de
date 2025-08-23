from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
}

with DAG(
    "spark_kafka_streaming_centralized",
    default_args=default_args,
    start_date=datetime(2025, 8, 17),
    schedule=None,   # run on trigger
    catchup=False,
    tags=["binance", "spark", "centralized"],
) as dag:
    # https://airflow.apache.org/docs/apache-airflow-providers-apache-spark/stable/_modules/airflow/providers/apache/spark/operators/spark_submit.html#SparkSubmitOperator.application
    start_stream = SparkSubmitOperator(
        application="/opt/airflow/dags/spark_kafka_centralized_stream.py",
        task_id="start_kafka_stream_centralized",
        conn_id="spark_default",   # set in Airflow Connections
        name="centralized",
        packages= "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0",
        conf={
            "spark.executor.memory": "1g",
            "spark.executor.cores": "1",
            "spark.driver.memory": "1g"
        }
    )