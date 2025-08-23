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
        application="/opt/airflow/dags/spark_kafka_stream_funding_fee_rate.py",
        task_id="start_kafka_stream_funding_fee_rate",
        conn_id="spark_default",   # set in Airflow Connections
        name="KafkaIntegration",
        packages= "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0",
        conf={
            "spark.executor.memory": "2g",
            "spark.executor.cores": "2",
            "spark.driver.memory": "1g"
        }
    )
