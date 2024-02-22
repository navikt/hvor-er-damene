"""A liveness prober dag for monitoring composer.googleapis.com/environment/healthy."""
import airflow
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import timedelta
from scripts import monthly_snapshot

default_args = {
    'start_date': airflow.utils.dates.days_ago(0),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    'monthly_snapshot_run',
    default_args=default_args,
    description='kopierer til bigquery månedlig',
    schedule_interval='@once',
    max_active_runs=2,
    catchup=False,
    dagrun_timeout=timedelta(minutes=10)) as dag:


    snapshot = PythonOperator(
        task_id='snapshot',
        python_callable=monthly_snapshot.main,
        dag=dag,
        depends_on_past=False,
        do_xcom_push=False)

