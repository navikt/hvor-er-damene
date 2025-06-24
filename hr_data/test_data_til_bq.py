"""
Leser inn test-data (csv) med forventet struktur for å kunne teste frontend

henter data som er laget direkte i pandas og laster opp til BigQuery test-tabell
(prod vs dev environment?)
"""

import csv
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from google.cloud.bigquery import LoadJobConfig

from df_funksjoner import read_test_data_csv

sys.path.append("..")
from teamkatalogen_bq.funksjoner import create_client


def main(dry_run=False):
    logging.basicConfig()

    if dry_run:
        logging.getLogger().setLevel(logging.INFO)

    TEST_DATA_SOURCE = Path("test_data_hr_prossesert.csv")

    PROJECT_ID = "heda-prod-2664"
    SA_KEY_NAME = "heda-access-key"
    DATASET = "hr_data"
    TEST_TABLE_NAME = "test_ansatte_direktoratet"

    bq_client = None

    if not dry_run:
        bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

    df_test_mangfold_data = read_test_data_csv(TEST_DATA_SOURCE, date_column_indexes=[])
    cols_test_mangfold_data = df_test_mangfold_data.columns

    logging.info(f"Kolonner i dataframe som blir brukt: \n{cols_test_mangfold_data}")
    logging.info(f"Generert test dataframe: \n{df_test_mangfold_data.head(10)}")
    logging.info(f"{df_test_mangfold_data.info()}")

    if not dry_run and bq_client:
        # laste data til BQ
        job_config = LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            create_disposition="CREATE_IF_NEEDED",
        )
        bq_dataset = f"{PROJECT_ID}.{DATASET}"
        bq_table = f"{bq_dataset}.{TEST_TABLE_NAME}"

        run_job = bq_client.load_table_from_dataframe(df_test_mangfold_data, bq_table, job_config=job_config)
        run_job.result()

    return None


if __name__ == "__main__":
    dry_run = True
    main(dry_run=dry_run)
