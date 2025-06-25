"""
Entry point - kjører alt av prosessering for å håndtere hr_data i BigQuery.

Skiller mellom dev og prod environments, med prod env variabel = true kjøres ekte data som ligger på prod-gcp-prosjekt,
ellers (ingen variabel) kjøres dev ved å først generere falsk data som så lastes opp til tabell på dev-gcp-prosjekt

skriptet `hr_data_til_bq.py` er ikke relatert
"""

import logging
import os
import sys
from pathlib import Path

sys.path.append("..")
from hr_data.hr_data_prosessering.df_funksjoner import read_test_data_csv, write_test_data_csv
from hr_data.hr_data_prosessering.hr_data_prosessering import df_process_pipeline
from hr_data.hr_data_prosessering.test_data_generer_i_csv import generate_test_data

logging.basicConfig(level=logging.WARNING)

# variabler kan bli hentet av andre filer uten å kjøre main
N_ROWS_TEST_DATA = 100

TEST_DATA_FILENAME = "test_data_hr.csv"
TEST_DATA_FILEPATH: Path = Path("hr_data_prosessering", TEST_DATA_FILENAME).resolve()

TEST_DATA_PROCESSED_FILENAME = "test_data_hr_prossesert.csv"
TEST_DATA_PROCESSED_FILEPATH: Path = Path("hr_data_prosessering", TEST_DATA_PROCESSED_FILENAME).resolve()

SA_KEY_NAME = "heda-access-key"
DATASET = "hr_data"
PROD_PROJECT_ID = "heda-prod-2664"
DEV_PROJECT_ID = "heda-dev-9df1"

TEST_TABLE_NAME = "test_ansatte_direktoratet"


def main() -> int:
    """Main funksjon som knytter sammen metoder i andre filer"""
    # sjekk environment
    PROD_ENV = os.getenv("PROD_ENV", None)
    if PROD_ENV:
        logging.info("Kjører i prod environment")
        raise NotImplementedError
    else:
        logging.info("Kjører i dev environment")

        df_test_hr_data = generate_test_data(N_ROWS_TEST_DATA)
        logging.info(f"Generert {df_test_hr_data.shape[0]} rader test-data")

        write_test_data_csv(df_test_hr_data, TEST_DATA_FILEPATH)
        logging.debug(f"Skrev generert data til `{TEST_DATA_FILEPATH}`")

        df_test_mangfold_data = read_test_data_csv(TEST_DATA_FILEPATH, date_column_indexes=[1, 2, 8])
        df_test_mangfold_data_processed = df_process_pipeline(df_test_mangfold_data)
        logging.debug("Test-data ferdig prossesert")

        write_test_data_csv(df_test_mangfold_data_processed, TEST_DATA_PROCESSED_FILEPATH)
        logging.debug(f"Skrev prosessert test-data til `{TEST_DATA_PROCESSED_FILEPATH}`")

    return 0


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    retcode = main()

    sys.exit(retcode)
