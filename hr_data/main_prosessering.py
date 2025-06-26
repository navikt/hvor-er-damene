"""
Entry point - kjører alt av prosessering for å håndtere hr_data i BigQuery.

Skiller mellom dev og prod environments, med prod env variabel = true kjøres ekte data som ligger på prod-gcp-prosjekt,
ellers (ingen variabel) kjøres dev ved å først generere falsk data som så lastes opp til tabell - foreløpig også i prod-gcp

skriptet `hr_data_til_bq.py` er ikke relatert
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.append("..")  # importere fra teamkatalogen_bq
from teamkatalogen_bq.funksjoner import get_teamkatalogen_data

from hr_data.hr_data_prosessering.df_funksjoner import read_test_data_csv, write_test_data_csv
from hr_data.hr_data_prosessering.hr_data_prosessering import df_hr_process_pipeline, df_mangfold_join_pipeline
from hr_data.hr_data_prosessering.test_data_generer_i_csv import generate_hr_test_data, generate_row_ids, generate_tk_test_data
from hr_data.hr_data_prosessering.test_data_til_bq import bigquery_upload_hr_df

logging.basicConfig(level=logging.WARNING)

# variabler kan bli hentet av andre filer uten å kjøre main
N_ROWS_TEST_DATA = 100
# if turned on (True), forces dry run and avoids uploading anything
DRY_RUN_OVERRIDE = False

TEST_HR_DATA_FILENAME = "test_data_hr.csv"
TEST_HR_DATA_FILEPATH: Path = Path("hr_data_prosessering", TEST_HR_DATA_FILENAME).resolve()

TEST_TK_DATA_FILENAME = "test_data_tk.csv"
TEST_TK_DATA_FILEPATH: Path = Path("hr_data_prosessering", TEST_TK_DATA_FILENAME).resolve()

TEST_DATA_PROCESSED_FILENAME = "test_data_hr_prossesert.csv"
TEST_DATA_PROCESSED_FILEPATH: Path = Path("hr_data_prosessering", TEST_DATA_PROCESSED_FILENAME).resolve()

SA_KEY_NAME = "heda-access-key"
DATASET = "hr_data"
PROD_PROJECT_ID = "heda-prod-2664"
# service account ikke i dev, kan ikke kjøre direkte i dev?
DEV_PROJECT_ID = "heda-dev-9df1"

TEST_TABLE_NAME = "test_ansatte_direktoratet"


def main(upload_to_bq: bool = False) -> int:
    """Main funksjon som knytter sammen metoder i andre filer"""
    # sjekk environment
    PROD_ENV = os.getenv("PROD_ENV", None)  # set in production env to process real data
    DAG_NODE = os.getenv("DAG_NODE", None)  # set on node running airflow to avoid file writes

    if PROD_ENV:
        logging.info("Kjører i prod environment")
        raise NotImplementedError
    else:
        if not DAG_NODE:
            logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Kjører i dev environment")

        tk_df = get_teamkatalogen_data()
        # print(tk_df.columns)

        ids_array = generate_row_ids(N_ROWS_TEST_DATA)
        df_test_hr_data = generate_hr_test_data(N_ROWS_TEST_DATA, ids_array)
        logging.info(f"Generert {df_test_hr_data.shape[0]} rader test-data form HR")

        df_test_tk_data = generate_tk_test_data(N_ROWS_TEST_DATA, ids_array)
        logging.info(f"Generert {df_test_tk_data.shape[0]} rader test-data form teamkatalogen")

        if not DAG_NODE:
            write_test_data_csv(df_test_hr_data, TEST_HR_DATA_FILEPATH)
            write_test_data_csv(df_test_tk_data, TEST_TK_DATA_FILEPATH)
            logging.debug(f"Skrev generert data til `{TEST_HR_DATA_FILEPATH}` og `{TEST_TK_DATA_FILEPATH}`")

            df_test_hr_data = read_test_data_csv(
                TEST_HR_DATA_FILEPATH, date_column_indexes=["fodselsdato", "ansatt_fra", "ansatt_til"]
            )
            df_test_tk_data = read_test_data_csv(TEST_TK_DATA_FILEPATH, date_column_indexes=[])

        df_test_hr_data = df_hr_process_pipeline(df_test_hr_data)
        df_test_mangfold_data_processed = df_mangfold_join_pipeline(df_test_hr_data, df_test_tk_data)
        logging.debug("Test-data ferdig prossesert")

        if not DAG_NODE:
            write_test_data_csv(df_test_mangfold_data_processed, TEST_DATA_PROCESSED_FILEPATH)
            logging.debug(f"Skrev prosessert test-data til `{TEST_DATA_PROCESSED_FILEPATH}`")

            df_test_mangfold_data_processed = read_test_data_csv(TEST_DATA_PROCESSED_FILEPATH, date_column_indexes=[])

        if upload_to_bq:
            bigquery_upload_hr_df(
                hr_df=df_test_mangfold_data_processed,
                PROJECT_ID=PROD_PROJECT_ID,
                SA_KEY_NAME=SA_KEY_NAME,
                DATASET=DATASET,
                TABLE_NAME=TEST_TABLE_NAME,
            )

    return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser(prog="Prosjekt_mangfold_main")
    parser.add_argument("-dry", "--dry-run", action="store_false")
    args = vars(parser.parse_args())

    # if dry run is NOT enabled and NOT forced on, upload to BigQuery
    upload_to_bq = not (args["dry-run"] or DRY_RUN_OVERRIDE)

    retcode = main(upload_to_bq=upload_to_bq)

    sys.exit(retcode)
