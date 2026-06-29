"""
ETL Pipeline DAG - processes daily user event data.

Expected behavior:
- Runs daily at midnight UTC
- Processes data for the current day's interval
- No backfill (only future runs)
- Non-blocking sensor
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor


default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["alerts@company.com"],
}

dag = DAG(
    dag_id="etl_pipeline",
    default_args=default_args,
    catchup=True,
    start_date=datetime.now(),
    schedule_interval="0 0 * * *",
    max_active_runs=1,
    description="Daily ETL pipeline for user event data",
)


def extract_data(**context):
    """Extract data for the current processing window."""
    execution_date = context["execution_date"]
    processing_date = execution_date.strftime("%Y-%m-%d")

    print(f"Extracting data for date: {processing_date}")
    with open(f"/tmp/extracted_{processing_date}.json", "w") as f:
        f.write(f'{{"date": "{processing_date}", "records": 1000}}')

    return processing_date


def transform_data(**context):
    """Transform extracted data."""
    processing_date = context["ti"].xcom_pull(task_ids="extract")
    print(f"Transforming data for: {processing_date}")
    with open(f"/tmp/transformed_{processing_date}.json", "w") as f:
        f.write(f'{{"date": "{processing_date}", "records": 950, "status": "clean"}}')


def load_data(**context):
    """Load transformed data to warehouse."""
    processing_date = context["ti"].xcom_pull(task_ids="extract")
    print(f"Loading data for: {processing_date}")


wait_for_source = FileSensor(
    task_id="wait_for_source_file",
    filepath="/tmp/source_data_ready.flag",
    poke_interval=10,
    timeout=3600,
    mode="poke",
    dag=dag,
)

extract = PythonOperator(
    task_id="extract",
    python_callable=extract_data,
    dag=dag,
)

transform = PythonOperator(
    task_id="transform",
    python_callable=transform_data,
    dag=dag,
)

load = PythonOperator(
    task_id="load",
    python_callable=load_data,
    dag=dag,
)

wait_for_source >> extract >> transform >> load
