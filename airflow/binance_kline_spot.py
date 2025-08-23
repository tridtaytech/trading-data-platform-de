import json
import logging
from airflow.providers.apache.kafka.triggers.msg_queue import KafkaMessageQueueTrigger
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.sdk import DAG, Asset, AssetWatcher, task

trigger = KafkaMessageQueueTrigger(
    topics=["binance.spot"],
    apply_function="shared_apply_function.apply_function",
    kafka_config_id="kafka_test",
    poll_timeout=35,
    poll_interval=35,
)

asset = Asset(
    "kafka_queue_binance_spot",
    watchers=[AssetWatcher(name="kafka_watcher_binance_spot", trigger=trigger)],
)

with DAG(dag_id="binance_kline_spot", schedule=[asset], catchup=False) as dag:
    @task
    def extract_events(triggering_asset_events=None):
        """Flatten Kafka asset events into a list of payloads."""
        all_events = []
        for asset, asset_list in (triggering_asset_events or {}).items():
            logging.info("Asset: %s -> %d events", asset, len(asset_list))
            for event in asset_list:
                payload = (event.extra or {}).get("payload", {})
                logging.info("Event payload: %s", json.dumps(payload, default=str))
                all_events.append(payload)
        return all_events  # list of messages

    @task
    def write_postgres(events):
        """Process one event → parallelized by Airflow dynamic mapping."""
        from write_postgres import write_to_postgres_parallel
        logging.info("Processing single event: %s", json.dumps(events, default=str))
        data = events or {}
        write_to_postgres_parallel(data)

    # Fan out events in parallel
    events = extract_events()
    write_postgres.expand(events=events)

# import json
# import datetime
# import logging
# from airflow.providers.apache.kafka.triggers.msg_queue import KafkaMessageQueueTrigger
# from airflow.providers.standard.operators.empty import EmptyOperator
# from airflow.providers.postgres.hooks.postgres import PostgresHook
# from airflow.sdk import DAG, Asset, AssetWatcher, task

# trigger = KafkaMessageQueueTrigger(
#     topics=["binance.spot"],
#     apply_function="shared_apply_function.apply_function",
#     kafka_config_id="kafka_test",
#     poll_timeout=5,
#     poll_interval=5,
# )

# asset = Asset(
#     "kafka_queue_binance_spot",
#     watchers=[AssetWatcher(name="kafka_watcher_binance_spot", trigger=trigger)],
# )

# with DAG(dag_id="binance_kline_spot", schedule=[asset], catchup=False) as dag:
#     @task
#     def debug_asset_events(triggering_asset_events=None):
#         import logging
#         import json

#         logging.info("Raw triggering_asset_events: %s", json.dumps(
#             triggering_asset_events, default=str, indent=2
#         ))
#     @task
#     def write_postgres(triggering_asset_events=None):
#         import json
#         import logging
#         from write_postgres import write_to_postgres  
#         logging.info("triggering_asset_events (raw): %s", json.dumps(
#             triggering_asset_events, default=str, indent=2
#         ))
#         for asset, asset_list in (triggering_asset_events or {}).items():
#             logging.info("Asset: %s -> %d events", asset, len(asset_list))
#             for event in asset_list:
#                 logging.info("Event payload: %s", json.dumps(
#                     (event.extra or {}).get("payload", {}), default=str
#                 ))
#         data = (triggering_asset_events or {}).items()
#         write_to_postgres(data)
#     debug_asset_events()
#     write_postgres()