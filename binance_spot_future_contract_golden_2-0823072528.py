from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.contrib.kubernetes.volume_mount import VolumeMount
from airflow.contrib.kubernetes.volume import Volume
from airflow.kubernetes.secret import Secret
from airflow import DAG
from airflow.utils.dates import days_ago

args = {
    "project_id": "binance_spot_future_contract_golden_2-0823072528",
}

dag = DAG(
    "binance_spot_future_contract_golden_2-0823072528",
    default_args=args,
    schedule_interval="@once",
    start_date=days_ago(1),
    description="""
Created with Elyra 3.15.0 pipeline editor using `binance_spot_future_contract_golden_2.py`.
    """,
    is_paused_upon_creation=False,
)


# Operator source: trading-data-platform-de/airflow/binance_spot_future_contract_golden_2.py

op_c9a21fef_b787_47e0_866f_8d24e0e0b420 = KubernetesPodOperator(
    name="binance_spot_future_contract_golden_2",
    namespace="default",
    image="continuumio/anaconda3@sha256:a2816acd3acda208d92e0bf6c11eb41fda9009ea20f24e123dbf84bb4bd4c4b8",
    cmds=["sh", "-c"],
    arguments=[
        "mkdir -p ./jupyter-work-dir/ && cd ./jupyter-work-dir/ && echo 'Downloading https://raw.githubusercontent.com/elyra-ai/elyra/v3.15.0/elyra/airflow/bootstrapper.py' && curl --fail -H 'Cache-Control: no-cache' -L https://raw.githubusercontent.com/elyra-ai/elyra/v3.15.0/elyra/airflow/bootstrapper.py --output bootstrapper.py && echo 'Downloading https://raw.githubusercontent.com/elyra-ai/elyra/v3.15.0/etc/generic/requirements-elyra.txt' && curl --fail -H 'Cache-Control: no-cache' -L https://raw.githubusercontent.com/elyra-ai/elyra/v3.15.0/etc/generic/requirements-elyra.txt --output requirements-elyra.txt && python3 -m pip install packaging && python3 -m pip freeze > requirements-current.txt && python3 bootstrapper.py --pipeline-name 'binance_spot_future_contract_golden_2' --cos-endpoint https://storage.googleapis.com --cos-bucket elyra-test-2 --cos-directory 'binance_spot_future_contract_golden_2-0823072528' --cos-dependencies-archive 'binance_spot_future_contract_golden_2-c9a21fef-b787-47e0-866f-8d24e0e0b420.tar.gz' --file 'trading-data-platform-de/airflow/binance_spot_future_contract_golden_2.py' "
    ],
    task_id="binance_spot_future_contract_golden_2",
    env_vars={
        "ELYRA_RUNTIME_ENV": "airflow",
        "AWS_ACCESS_KEY_ID": "GOOG1EBXQWK6JCFI64Y3WTP3JW3QG3I4GFWWQOC3VOBXLYIY7DWFDFSCFBOSE",
        "AWS_SECRET_ACCESS_KEY": "tcSPfgA+KL895JFnHaQaQIu7PxK6vOo9mnoh34Fu",
        "ELYRA_ENABLE_PIPELINE_INFO": "True",
        "ELYRA_RUN_NAME": "binance_spot_future_contract_golden_2-{{ ts_nodash }}",
    },
    volumes=[],
    volume_mounts=[],
    secrets=[],
    annotations={},
    labels={},
    tolerations=[],
    in_cluster=True,
    config_file="None",
    dag=dag,
)
