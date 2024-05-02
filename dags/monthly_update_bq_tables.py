from datetime import datetime
from airflow import DAG

from dataverk_airflow import python_operator

image = "ghcr.io/navikt/dvh-images/airflow-etl-spenn:2024-02-22-e47954f"

dag_name = "monthly_update_bq_tables"
default_args = {
    "owner": "heda",
    "start_date": datetime(2024, 5, 2),
    "depends_on_past": False,
}

allowlist = ["secretmanager.googleapis.com", "bigquery.googleapis.com", "teamkatalog-api.intern.nav.no"]

with DAG(
    dag_name,
    default_args=default_args,
    schedule_interval="0 0 1 * *",
) as dag:

    insert_monthly_snapshot_raw = python_operator(
        dag=dag,
        name="insert_monthly_snapshot_raw",
        script_path="monthly_snapshot.py",
        repo="navikt/hvor-er-damene",
        branch="main",
        #slack_channel="#heda",
        allowlist=allowlist,
        image=image,
    )
    process_snapshot = python_operator(
        dag=dag,
        name="process_snapshot",
        script_path="process_snapshot.py",
        repo="navikt/hvor-er-damene",
        branch="main",
        #slack_channel="#heda",
        allowlist=allowlist,
        image=image,
    )
    aggregate = python_operator(
        dag=dag,
        name="aggregate",
        script_path="aggregate.py",
        repo="navikt/hvor-er-damene",
        branch="main",
        #slack_channel="#heda",
        allowlist=allowlist,
        image=image,
    )

insert_monthly_snapshot_raw >> process_snapshot >> aggregate