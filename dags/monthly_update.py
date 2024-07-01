from datetime import datetime
from airflow import DAG

from dataverk_airflow import python_operator, quarto_operator
from airflow.models import Variable


dag_name = "monthly_update"
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
        script_path="teamkatalogen_bq/monthly_snapshot.py",
        repo="navikt/hvor-er-damene",
        branch="main",
        #slack_channel="#heda",
        allowlist=allowlist,
        requirements_path = "requirements.txt"
    )
    process_snapshot = python_operator(
        dag=dag,
        name="process_snapshot",
        script_path="teamkatalogen_bq/process_snapshot.py",
        repo="navikt/hvor-er-damene",
        branch="main",
        #slack_channel="#heda",
        allowlist=allowlist,
        requirements_path = "requirements.txt"
    )
    aggregate = python_operator(
        dag=dag,
        name="aggregate",
        script_path="teamkatalogen_bq/aggregate.py",
        repo="navikt/hvor-er-damene",
        branch="main",
        #slack_channel="#heda",
        allowlist=allowlist,
        requirements_path = "requirements.txt"
    )

    make_quarto = quarto_operator(
        dag=dag,
        name="make_quarto",
        allowlist=allowlist + ["storage-component.googleapis.com"],
        retries=0,
        repo="navikt/hvor-er-damene",
        quarto={
            "path": "quarto/make_dashboard.qmd",
            "format": "dashboard",
            "env": "prod",
            "id": "7ea943c9-ae07-4d75-9b65-d775c05230dc",
            "token": Variable.get("team_token"),
        },
        requirements_path="requirements.txt",
    )

insert_monthly_snapshot_raw >> process_snapshot >> aggregate >> make_quarto