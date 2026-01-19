import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from datetime import datetime ,timedelta
from docker.types import Mount as mount

sys.path.append('/opt/airflow/api_request')

from insert_records import main

default_args = {
    'description': 'A DAG to write dolar values into the database every day',
    'start_date' : datetime(2025,7,27),
    'catchup': False,
}


dag = DAG(
    'dolar_api_orchestrator',
    default_args = default_args,
    schedule = timedelta(days=1)
)

with dag:
    task1 = PythonOperator(
        task_id = 'data_ingestion_dolar_api',
        python_callable = main
    )

    task2 = DockerOperator(
        task_id='transform_data',
        image='ghcr.io/dbt-labs/dbt-postgres:1.9.latest',
        mounts=[
            mount(source = '/home/caroli/lakehouse-workspace/study_first_project/dbt/my_project',
            target = '/usr/app',
            type = 'bind'),
            mount(source = '/home/caroli/lakehouse-workspace/study_first_project/dbt/my_project/profiles.yml',target = '/root/.dbt/profiles.yml',type = 'bind')
        ],
        auto_remove='success',
        command='run --project-dir /usr/app --profiles-dir /root/.dbt',
        docker_url='unix://var/run/docker.sock',
        network_mode='study_first_project_my-network')
    
    task1 >> task2