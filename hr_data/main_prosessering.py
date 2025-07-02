"""
Entry point - kjører alt av prosessering for å håndtere hr_data i BigQuery.

Skiller mellom dev og prod environments, med prod env variabel = true kjøres ekte data som ligger på prod-gcp-prosjekt,
ellers (ingen variabel) kjøres dev ved å først generere falsk data som så lastes opp til tabell i dev-gcp-prosjekt

skriptet `hr_data_til_bq.py` er ikke relatert
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from google.cloud.bigquery import Client

sys.path.append("..")  # importere fra teamkatalogen_bq
# from teamkatalogen_bq.funksjoner import get_teamkatalogen_data
import teamkatalogen_bq.funksjoner as tk_funksjoner

import hr_data.bigquery_funksjoner as bq_funksjoner  # sirkulær import betyr vi trenger denne typen import, ikke direkte funksjon
from hr_data.hr_data_prosessering.df_funksjoner import read_test_data_csv, write_test_data_csv
from hr_data.hr_data_prosessering.hr_data_prosessering import df_hr_process_pipeline, df_mangfold_join_pipeline
from hr_data.hr_data_prosessering.test_data_generer_i_csv import generate_hr_test_data, generate_row_ids, generate_tk_test_data

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
HR_DATASET = "hr_data"
PROCESSED_DATASET = "mangfold_processed_data"
PROD_PROJECT_ID = "heda-prod-2664"
DEV_PROJECT_ID = "heda-dev-9df1"

# endre her for tabellnavn som brukes i backend
TEST_TABLE_NAME = "test_ansatte_direktoratet"

# tabeller på big query, trenger ikke alle kolonner lokalt så spør bare om X kolonner
SOURCE_TABLES_AND_COLUMNS = {
    "ansatte_direktoratet_raw": [],
    "ansatte_plus_teamkatalog_raw": [
        "kjonn",
        "alder",
        "ansatt_fra_aar",
        "stillingsnavn",
        "orgniv1_navn",
        "orgniv2_navn",
        "orgniv25_navn",
        "orgniv3_navn",
        "orgenhet_navn",
        "team",
        "klynge",
        "omrade",
        "roles",
        "roller",
    ],
    "ansatte_plus_teamkatalog_roller_raw": [
        "kjonn",
        "alder",
        "ansatt_fra_aar",
        "stillingsnavn",
        "orgniv1_navn",
        "orgniv2_navn",
        "orgniv25_navn",
        "orgniv3_navn",
        "orgenhet_navn",
        "team",
        "klynge",
        "omrade",
        "role",
        "rolle",
    ],
    "ansatte_teamkatalog_grupper_raw": [],
}
# funksjonalitet for å definere sql-spørringen som skal kjøres på hver tabell
SOURCE_TABLES_SQL_QUERY = {}
# hver kildetabell blir lastet inn som ett dataframe
BQ_TABLE_DF_CONTAINER: dict[str, pd.DataFrame] = {}

# definer SQL spørringer
# velger ut bare ansatte som enten direkte er tilknyttet teknologidirektoratet, eller som har noe data i henhold til teamkatalogen
# (indirekte knyttet til direktoratet)
table = "ansatte_plus_teamkatalog_raw"
SOURCE_TABLES_SQL_QUERY[table] = f"""
    SELECT {", ".join(SOURCE_TABLES_AND_COLUMNS[table])}
    FROM `{PROD_PROJECT_ID}.{HR_DATASET}.{table}`
    WHERE
        orgniv1_kode = "80"
        OR team    IS NOT NULL
        OR klynge  IS NOT NULL
        OR omrade  IS NOT NULL
        OR roles   IS NOT NULL
        OR roller  IS NOT NULL
    """

table = "ansatte_plus_teamkatalog_roller_raw"
SOURCE_TABLES_SQL_QUERY[table] = f"""
    SELECT {", ".join(SOURCE_TABLES_AND_COLUMNS[table])}
    FROM `{PROD_PROJECT_ID}.{HR_DATASET}.{table}`
    WHERE
        orgniv1_kode = "80"
        OR team    IS NOT NULL
        OR klynge  IS NOT NULL
        OR omrade  IS NOT NULL
        OR role    IS NOT NULL
        OR rolle   IS NOT NULL
    """


def prod_main(PROD_ENV: str | None, DAG_NODE: str | None, upload_to_bq: bool = False) -> int:
    if not DAG_NODE:  # kjører lokal debug
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Kjører i prod environment")

    bq_client: Client = tk_funksjoner.create_client(PROD_PROJECT_ID, SA_KEY_NAME)

    # hent data fra BigQuery
    for source_table, fetch_query in SOURCE_TABLES_SQL_QUERY.items():
        if fetch_query:
            logging.info(f"Henter data fra BigQuery-tabellen `{source_table}`")
            logging.info(f"Kolonner som hentes: {SOURCE_TABLES_AND_COLUMNS[source_table]}")
            big_query_result_df = bq_client.query(fetch_query).to_dataframe()

            BQ_TABLE_DF_CONTAINER[source_table] = big_query_result_df

        else:
            logging.info(f"Skipping `{source_table}` as no columns were specified")

    for table_name, bq_df in BQ_TABLE_DF_CONTAINER.items():
        logging.info(f"Dataframe for `{table_name}` har {bq_df.shape[0]} rader og {bq_df.shape[1]} kolonner")
        logging.debug(f"Kolonner: {bq_df.columns.tolist()}")

        logging.debug(f"{bq_df.head(10)}")

    if upload_to_bq:
        bq_funksjoner.bigquery_upload_hr_df(
            hr_df=None,
            PROJECT_ID=PROD_PROJECT_ID,
            SA_KEY_NAME=SA_KEY_NAME,
            DATASET=PROCESSED_DATASET,
            TABLE_NAME=...,
            bq_client_premade=bq_client,
        )

    return 0


def dev_main(PROD_ENV: str | None, DAG_NODE: str | None, upload_to_bq: bool = False) -> int:
    if not DAG_NODE:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Kjører i dev environment")

    # tk_df = get_teamkatalogen_data()
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
        bq_funksjoner.bigquery_upload_hr_df(
            hr_df=df_test_mangfold_data_processed,
            PROJECT_ID=DEV_PROJECT_ID,
            SA_KEY_NAME=SA_KEY_NAME,
            DATASET=PROCESSED_DATASET,
            TABLE_NAME=TEST_TABLE_NAME,
        )

    return 0


def main(upload_to_bq: bool = False) -> int:
    """Main funksjon som knytter sammen metoder i andre filer"""
    # sjekk environment
    PROD_ENV = os.getenv("PROD_ENV", None)  # set in production env to process real data
    DAG_NODE = os.getenv("DAG_NODE", None)  # set on node running airflow to avoid file writes

    if PROD_ENV:
        retcode = prod_main(PROD_ENV, DAG_NODE, upload_to_bq=upload_to_bq)

    # not prod => dev environment
    else:
        retcode = dev_main(PROD_ENV, DAG_NODE, upload_to_bq=upload_to_bq)

    return retcode


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)

    parser = argparse.ArgumentParser(prog="Prosjekt_mangfold_main")
    parser.add_argument(
        "-d", "--dry", "--dry-run", action="store_true", help="Kjør prosessering uten å laste opp data til BigQuery"
    )
    parser.add_argument(
        "-p", "--prod", "--prod-env", action="store_true", help="Sett skriptet til å kjøre som om environment er production"
    )
    args = vars(parser.parse_args())

    # if dry run is NOT enabled and NOT forced on, upload to BigQuery
    upload_to_bq = not (args["dry"] or DRY_RUN_OVERRIDE)
    logging.info(f"Laste opp til BigQuery: {upload_to_bq}")

    if args["prod"] is True:
        os.environ["PROD_ENV"] = "true"  # override prod environment variable

    retcode = main(upload_to_bq=upload_to_bq)

    sys.exit(retcode)
