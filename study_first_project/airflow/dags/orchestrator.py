import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime ,timedelta

sys.path.append('/opt/airflow/api_request')

def callable_main():
    from insert_records import main
    return main()

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
        python_callable = callable_main
    )