"""
Leser inn test-data (csv) med forventet struktur for å kunne teste frontend

henter data som er laget direkte i pandas og laster opp til BigQuery test-tabell
(prod vs dev environment?)
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from google.cloud.bigquery import Client, LoadJobConfig

sys.path.append("../..")
from teamkatalogen_bq.funksjoner import create_client

import hr_data.main_prosessering as settings
from hr_data.hr_data_prosessering.df_funksjoner import read_test_data_csv

logging.basicConfig()


def bigquery_upload_hr_df(
    hr_df: pd.DataFrame | None = None,
    PROJECT_ID=None,
    SA_KEY_NAME=None,
    DATASET=None,
    TABLE_NAME=None,
):
    SA_KEY_NAME = "heda-access-key"
    bq_client: Client = create_client(PROJECT_ID, SA_KEY_NAME)

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


def main(data_source: Path, dry_run: bool = True) -> None:
    if dry_run:
        logging.getLogger().setLevel(logging.INFO)

    df_test_mangfold_data = read_test_data_csv(data_source, date_column_indexes=[])
    cols_test_mangfold_data = df_test_mangfold_data.columns

    logging.info(f"Kolonner i dataframe som blir brukt: \n{cols_test_mangfold_data}")
    logging.info(f"Generert test dataframe: \n{df_test_mangfold_data.head(10)}")
    logging.info(f"{df_test_mangfold_data.info()}")

    if not dry_run:
        bigquery_upload_hr_df(
            hr_df=df_test_mangfold_data,
            # PROJECT_ID=settings.DEV_PROJECT_ID,
            PROJECT_ID=settings.PROD_PROJECT_ID,
            SA_KEY_NAME=settings.SA_KEY_NAME,
            DATASET=settings.DATASET,
            TABLE_NAME=settings.TEST_TABLE_NAME,
        )

    return None


if __name__ == "__main__":
    dry_run = False

    data_source_path = Path(settings.TEST_DATA_PROCESSED_FILENAME).resolve()
    main(data_source_path, dry_run=dry_run)
