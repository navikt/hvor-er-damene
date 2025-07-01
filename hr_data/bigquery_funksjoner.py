"""Støttefunksjoner for å håndtere BigQuery tilkobninger"""

import sys

import pandas as pd
from google.cloud.bigquery import Client, LoadJobConfig

sys.path.append("..")  # importere fra teamkatalogen_bq
import teamkatalogen_bq.funksjoner as tk_funksjoner


def bigquery_upload_hr_df(
    hr_df: pd.DataFrame | None = None,
    PROJECT_ID=None,
    SA_KEY_NAME=None,
    DATASET=None,
    TABLE_NAME=None,
    bq_client_premade: Client | None = None,
):
    # optionally possible to supply a pre-made client - we use this when fetching data from BQ first and uploading later
    if not bq_client_premade:
        bq_client: Client = tk_funksjoner.create_client(PROJECT_ID, SA_KEY_NAME)
    else:
        bq_client: Client = bq_client_premade

    # laste data til BQ
    job_config = LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # NOTE: skriver over tabeller hver gang
        create_disposition="CREATE_IF_NEEDED",
    )
    bq_dataset = f"{PROJECT_ID}.{DATASET}"
    bq_table = f"{bq_dataset}.{TABLE_NAME}"

    run_job = bq_client.load_table_from_dataframe(hr_df, bq_table, job_config=job_config)
    run_job.result()

    return None
