"""
lager test-data med forventet struktur for å kunne teste frontend

lager test-data direkte i pandas og laster opp til BigQuery test-tabell
(prod vs dev environment?)
"""

import csv
import logging
import sys

import numpy as np
import pandas as pd
from google.cloud.bigquery import LoadJobConfig

sys.path.append("..")
from teamkatalogen_bq.funksjoner import create_client


def main(dry_run=False):
    logging.basicConfig()

    if dry_run:
        logging.getLogger().setLevel(logging.INFO)

    TEST_DATA_SOURCE = "test_data_hr.csv"

    PROJECT_ID = "heda-prod-2664"
    SA_KEY_NAME = "heda-access-key"
    DATASET = "hr_data"
    TEST_TABLE_NAME = "test_ansatte_direktoratet"

    bq_client = None

    if not dry_run:
        bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

    df_test_mangfold_data = pd.read_csv(
        TEST_DATA_SOURCE,
        header=0,
        index_col=False,
        sep=";",
        parse_dates=[1],
        skipinitialspace=True,
        engine="python",
        quoting=csv.QUOTE_MINIMAL,
    )
    cols_test_mangfold_data = [col.strip() for col in df_test_mangfold_data.columns]

    logging.info(f"Kolonner i dataframe som blir brukt: \n{cols_test_mangfold_data}")
    logging.info(f"Generert test dataframe: \n{df_test_mangfold_data.head(10)}")

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
    dry_run = False
    main(dry_run=dry_run)
