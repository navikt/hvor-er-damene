from airflow import DAG
from datetime import datetime
from pendulum import timezone
from dataverk_airflow import python_operator


# DAG for å speile Oracle-tabeller til BigQuery


with DAG(
    dag_id="daglig_hr_data_til_bq",
    description="DAG for å speile Oracle-tabeller til BigQuery",
    schedule_interval="0 6 * * *",  # Kjør hver dag kl. 06:00
    start_date=datetime(2025, 6, 12, tzinfo=timezone("Europe/Oslo")),
    catchup=False,
) as dag:

    oracle_til_bigquery = python_operator(
        dag=dag,
        name="oracle_til_bigquery",
        repo="navikt/hvor-er-damene",
        script_path="hr_data/hr_data_til_bq.py",
        requirements_path="requirements_bq.txt",
        use_uv_pip_install=True,
        # slack_channel="#heda",
        allowlist=[
            "secretmanager.googleapis.com",
            "bigquery.googleapis.com",
            "dmv09-scan.adeo.no:1521",  # DVH Prod
        ],
    )

    oracle_til_bigquery
