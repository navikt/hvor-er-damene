"""Støttefunksjoner for å håndtere BigQuery tilkobninger"""

import logging
import sys

import pandas as pd
from google.cloud.bigquery import Client, LoadJobConfig

sys.path.append("..")  # importere fra teamkatalogen_bq
import teamkatalogen_bq.funksjoner as tk_funksjoner


def bigquery_upload_hr_df(
    hr_df: pd.DataFrame | None = None,
    PROJECT_ID: str | None = None,
    SA_KEY_NAME: str | None = None,
    DATASET: str | None = None,
    TABLE_NAME: str | None = None,
    bq_client_premade: Client | None = None,
    write_disposition_setting: str = "WRITE_TRUNCATE",  # NOTE: skriver over tabeller hver gang by default
):
    """
    Wrapper for bigquery methods to take a pandas dataframe in our format and upload to a bigquery table.

    Optionally possible to supply a pre-made client - we use this when fetching data from BQ first and uploading later
    to keep the same client in use

    Possible choices for `write_disposition_setting` as of method being made:
        "WRITE_TRUNCATE", "WRITE_TRUNCATE_DATA", "WRITE_APPEND", "WRITE_EMPTY"

    See https://cloud.google.com/bigquery/docs/reference/rest/v2/Job#jobconfigurationload
    """
    if hr_df is None or PROJECT_ID is None or SA_KEY_NAME is None or DATASET is None or TABLE_NAME is None:
        msg = f"""Must have a dataframe, project id, service account key name, dataset AND table name to upload to BigQuery
Missing parameters: \
{"HR_DF, " if hr_df is None else ""}{"PROJECT_ID, " if PROJECT_ID is None else ""}\
{"SA_KEY_NAME, " if SA_KEY_NAME is None else ""}{"DATASET, " if DATASET is None else ""}\
{"TABLE_NAME" if TABLE_NAME is None else ""}
    """
        raise ValueError(msg)
    if not bq_client_premade:
        bq_client: Client = tk_funksjoner.create_client(PROJECT_ID, SA_KEY_NAME)
    else:
        bq_client: Client = bq_client_premade

    # laste data til BQ
    job_config = LoadJobConfig(
        write_disposition=write_disposition_setting,  # NOTE: skriver over tabeller med mindre bruker endrer
        create_disposition="CREATE_IF_NEEDED",
    )
    bq_dataset = f"{PROJECT_ID}.{DATASET}"
    bq_table = f"{bq_dataset}.{TABLE_NAME}"

    run_job = bq_client.load_table_from_dataframe(hr_df, bq_table, job_config=job_config)
    run_job.result()

    return None


# passer ikke helt, men den brukes til monitorering som skal lastes opp i BigQuery
class ErrorFlagHandler(logging.Handler):
    """Hook into logging library and return True if .error was logged"""

    def __init__(self):
        super().__init__()
        self.error_logged = False

    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.error_logged = True


if __name__ == "__main__":
    # test error message
    bigquery_upload_hr_df(TABLE_NAME="test")
