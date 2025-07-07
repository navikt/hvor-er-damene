"""DAG for å speile Oracle-tabeller til BigQuery"""

from datetime import datetime

# ignore: pakkene blir gitt av DAG-løsningen vi bruker
from airflow import DAG  # type: ignore
from dataverk_airflow import python_operator  # type: ignore
from pendulum import timezone  # type: ignore

allowlist = [
    "secretmanager.googleapis.com",
    "bigquery.googleapis.com",
    "dmv09-scan.adeo.no:1521",  # DVH Prod
    "teamkatalog-api.intern.nav.no",
]

default_args = {
    "owner": "heda",
}

with DAG(
    dag_id="daglig_hr_data_til_bq",
    description="DAG for å speile Oracle-tabeller til BigQuery, og prosessere dem",
    default_args=default_args,
    schedule_interval="0 6 * * *",  # Kjør hver dag kl. 06:00
    start_date=datetime(2025, 6, 12, tzinfo=timezone("Europe/Oslo")),
    catchup=False,
) as dag:
    # Speiler Oracle db
    oracle_til_bigquery = python_operator(
        dag=dag,
        name="oracle_til_bigquery",
        repo="navikt/hvor-er-damene",
        script_path="hr_data/hr_data_til_bq.py",
        requirements_path="requirements_bq.txt",
        # use_uv_pip_install=True,
        slack_channel="#team-heda",
        allowlist=allowlist,
    )
    # Prosessering av BigQuery-data, aggregerer og lager nye tabeller
    bigquery_prosessering_aggregering = python_operator(
        dag=dag,
        name="bigquery_prosessering_aggregering",
        repo="navikt/hvor-er-damene",
        script_path="hr_data/main_prosessering.py",
        requirements_path="requirements_bq.txt",
        # use_uv_pip_install=True,
        slack_channel="#team-heda",
        allowlist=allowlist,
        extra_envs={
            "PROD_ENV": "true",
            "DAG_NODE": "true",
        },
    )

    oracle_til_bigquery >> bigquery_prosessering_aggregering  # type: ignore # blir brukt av DAG
