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
from hr_data.hr_data_prosessering.hr_data_prosessering import (
    df_aggregate_age_group,
    df_aggregate_worked_year_groups,
    df_hr_process_pipeline,
    df_mangfold_join_pipeline,
    hr_data_map_roles_to_tk_names,
)
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
# tabeller med tomme kolonner hoppes over
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
# vi vil ha output tabeller som er gruppert basert på disse kolonnene,
# med ulike opphavs-tabeller som grupperes for å gi resultatene
TARGET_TABLE_COLUMNS_TO_GROUP_BY = {
    "ansatt_gruppert_hr_avdeling_antall": [
        "kjonn",
        "aldersgruppe",
        "ansiennitetsgruppe",
        "orgniv1_navn",
        "orgniv2_navn",
        "orgniv25_navn",
        "orgniv3_navn",
        "omrade",
    ],
    "ansatt_gruppert_tk_medlemskap_antall": [
        "kjonn",
        "aldersgruppe",
        "ansiennitetsgruppe",
        "orgniv1_navn",
        "omrade",
    ],
    "ansatt_gruppert_hr_stilling_antall": [
        "kjonn",
        "aldersgruppe",
        "ansiennitetsgruppe",
        "stillingsnavn",
    ],
    "ansatt_gruppert_tk_roller_antall": [
        "kjonn",
        "aldersgruppe",
        "ansiennitetsgruppe",
        "rolle",
    ],
}
# hvilken ny tabell skal lages basert på hvilken kildetabell
TARGET_TABLE_TO_SOURCE_TABLE_MAPPING = {
    "ansatt_gruppert_hr_avdeling_antall": "ansatte_plus_teamkatalog_raw",
    "ansatt_gruppert_tk_medlemskap_antall": "ansatte_plus_teamkatalog_raw",
    "ansatt_gruppert_hr_stilling_antall": "ansatte_plus_teamkatalog_roller_raw",
    "ansatt_gruppert_tk_roller_antall": "ansatte_plus_teamkatalog_roller_raw",
}
# slipp å definere target tabeller to ganger, hent fra dict over
TARGET_TABLES_LIST = list(TARGET_TABLE_TO_SOURCE_TABLE_MAPPING.keys())

# funksjonalitet for å definere sql-spørringen som skal kjøres på hver tabell
SOURCE_TABLES_SQL_QUERY = {}
# hver kildetabell blir lastet inn som ett dataframe
BQ_TABLE_DF_CONTAINER: dict[str, pd.DataFrame] = {}
# vi lager nye dataframes som skal ende opp som nye bigquery tabeller
TARGET_TABLE_DF_CONTAINER: dict[str, pd.DataFrame] = {}

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


def bigquery_df_process_pipeline(input_df: pd.DataFrame) -> pd.DataFrame:
    output_df = input_df.copy()

    # grupper på alder
    output_df = output_df.rename(columns={"alder": "aldersgruppe"})
    output_df = df_aggregate_age_group(output_df, age_column="aldersgruppe")

    # grupper på ansiennitet
    output_df = output_df.rename(columns={"ansatt_fra_aar": "ansiennitetsgruppe"})
    # regn ut hvor mange år siden de ble ansatt
    current_year = pd.Timestamp.now().year
    output_df["ansiennitetsgruppe"] = current_year - output_df["ansiennitetsgruppe"].astype(int)
    output_df = df_aggregate_worked_year_groups(output_df, worked_years_column="ansiennitetsgruppe")

    output_df = output_df.fillna("Ukjent")

    return output_df


def prod_main(PROD_ENV: str | None, DAG_NODE: str | None, upload_to_bq: bool = False) -> int:
    if not DAG_NODE:  # kjører lokal debug
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Kjører i prod environment")

    bq_client: Client = tk_funksjoner.create_client(PROD_PROJECT_ID, SA_KEY_NAME)

    # hent data fra BigQuery
    for source_table, fetch_query in SOURCE_TABLES_SQL_QUERY.items():
        if fetch_query:
            logging.info(f"Henter data fra BigQuery-tabellen `{source_table}`")
            logging.debug(f"Kolonner som hentes: {SOURCE_TABLES_AND_COLUMNS[source_table]}")
            big_query_result_df = bq_client.query(fetch_query).to_dataframe()

            BQ_TABLE_DF_CONTAINER[source_table] = big_query_result_df
            logging.info(f"Hentet {big_query_result_df.shape[0]} rader og {big_query_result_df.shape[1]} kolonner")

        else:
            logging.info(f"Skipping `{source_table}` as no columns were specified")

    # kjør første pass med aggregering, fjerner detaljert informasjon om alder og ansettelsesår
    for target_table_name, source_table_name in TARGET_TABLE_TO_SOURCE_TABLE_MAPPING.items():
        # pipeline har en inkludert copy-operasjon
        # så vi forbereder ett nytt dataframe for hver target som en kopi av kilde-tabellene
        # (som kan bruke samme kilde flere ganger)
        TARGET_TABLE_DF_CONTAINER[target_table_name] = bigquery_df_process_pipeline(BQ_TABLE_DF_CONTAINER[source_table_name])

    # lag target tabeller som skal lastes opp i BigQuery som resultat til bruk av backend/frontend
    for target_table in TARGET_TABLES_LIST:
        # grupperer på gitte kolonner og teller opp
        # vi ønsker en rad per mulige kombinasjoner av kjønn, aldersgruppe, ansiennitetsgruppe, avdeling, etc.
        # med antall hvor mange som passer i disse kombinasjonene
        grouped_df = (
            TARGET_TABLE_DF_CONTAINER[target_table]
            .groupby(TARGET_TABLE_COLUMNS_TO_GROUP_BY[target_table], dropna=False, as_index=False, observed=True)
            .size()
        )

        grouped_df = grouped_df.rename(columns={"size": "antall"})  # type: ignore ,wrong inference from .size()
        # sorter sånn at største gruppe kommer først NOTE: kan hende vi fjerner
        grouped_df = grouped_df.sort_values(by=["antall"], ascending=False)

        # håndtering av kolonner som bare er i noen av settene
        if "rolle" in grouped_df.columns:
            grouped_df = hr_data_map_roles_to_tk_names(grouped_df, role_column="rolle")

        logging.debug(grouped_df.info())
        logging.debug(grouped_df.describe())
        if not DAG_NODE:
            grouped_df.to_csv(f"test_grouped_df_{target_table}.csv", index=True, index_label="index")
            logging.debug(f"Skrev prosessert data til `test_grouped_df_{target_table}.csv` for inspeksjon")

        if upload_to_bq:
            bq_funksjoner.bigquery_upload_hr_df(
                hr_df=grouped_df,  # type: ignore ,wrong inference from .size()
                PROJECT_ID=PROD_PROJECT_ID,
                SA_KEY_NAME=SA_KEY_NAME,
                DATASET=PROCESSED_DATASET,
                TABLE_NAME=target_table,
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
