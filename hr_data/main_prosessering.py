"""
Entry point - kjører alt av prosessering for å håndtere hr_data i BigQuery.

Skiller mellom dev og prod environments, med prod env variabel = true kjøres ekte data som ligger på prod-gcp-prosjekt,
ellers (ingen variabel) kjøres dev ved å først generere falsk data som så lastes opp til tabell i dev-gcp-prosjekt

skriptet `hr_data_til_bq.py` er ikke relatert
"""

## imports
import argparse
import logging
import os
import sys
from pathlib import Path

import google.cloud.bigquery.exceptions as bq_exceptions
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

## program
logging.basicConfig(level=logging.WARNING)
error_flag_handler = bq_funksjoner.ErrorFlagHandler()
# legg til en logger som bare sier True om en .error ble logget noe sted
logging.getLogger().addHandler(error_flag_handler)

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
METADATA_TABLE_NAME = "ansatte_data_status_metadata"
TEST_TABLE_NAME = "test_ansatte_direktoratet"

## input fra bigquery
# tabeller på big query, trenger ikke alle kolonner lokalt så spør bare om X kolonner
# tabeller med tomme kolonner hoppes over
SOURCE_TABLES_AND_COLUMNS = {
    "ansatte_direktoratet_raw": [],
    "ansatte_plus_teamkatalog_raw": [
        "kjonn",
        "alder",
        "ansatt_fra_aar",
        "lederniva",
        "orgniv1_navn",
        "orgniv2_navn",
        "orgniv25_navn",
        "orgniv3_navn",
        "stillingsnavn",
        "team",
        "omrade",
        "roles",
        "roller",
        "sektor",
    ],
    "ansatte_plus_teamkatalog_roller_raw": [
        "kjonn",
        "alder",
        "ansatt_fra_aar",
        "lederniva",
        "orgniv1_navn",
        "orgniv2_navn",
        "orgniv25_navn",
        "orgniv3_navn",
        "stillingsnavn",
        "team",
        "omrade",
        "role",
        "rolle",
        "sektor",
    ],
    "ansatte_teamkatalog_grupper_raw": [],
}
# funksjonalitet for å definere sql-spørringen som skal kjøres på hver tabell
SOURCE_TABLES_SQL_QUERY = {}
# hver kildetabell blir lastet inn som ett dataframe
BQ_TABLE_DF_CONTAINER: dict[str, pd.DataFrame | None] = {}
# None betyr feil i henting av data

# definer SQL spørringer
# velger ut bare ansatte som enten direkte er tilknyttet teknologidirektoratet, og eksluderer eksterne (konsulenter)
table = "ansatte_plus_teamkatalog_raw"
SOURCE_TABLES_SQL_QUERY[table] = f"""
SELECT DISTINCT(pseudo_key), {", ".join(SOURCE_TABLES_AND_COLUMNS[table])}
FROM `{PROD_PROJECT_ID}.{HR_DATASET}.{table}`
WHERE
    orgniv1_kode = "80"
AND
    sektor = 'NAV Statlig'
AND
    orgniv2_kode in ("843", "829", "832", "828", "857", "815", "821", "8202", "8204", "72")
"""

# NOTE: bare statlige direkte ansatte nå
# "sektor not like "Ekstern%" ville inkludere kommunale ansatte også

# NOTE: orgniv2_kode: filtrert på avdelinger som er i organisasjonskartet til NAV, og også i teamkatalog/NOM
# vi filtrerer ut organisatorisk som at det fins en velferdsdirektør "avdeling" som bare har 1 medlem
# disse små avdelingene som ikke er på kartet er ikke interessante statistisk sett

table = "ansatte_plus_teamkatalog_roller_raw"
SOURCE_TABLES_SQL_QUERY[table] = f"""
SELECT DISTINCT(pseudo_key), {", ".join(SOURCE_TABLES_AND_COLUMNS[table])}
FROM `{PROD_PROJECT_ID}.{HR_DATASET}.{table}`
WHERE
    orgniv1_kode = "80"
AND
    sektor = 'NAV Statlig'
AND
    orgniv2_kode in ("843", "829", "832", "828", "857", "815", "821", "8202", "8204", "72")
"""

## output til bigquery
# vi vil ha output tabeller som er gruppert basert på disse kolonnene,
# med ulike opphavs-tabeller som grupperes for å gi resultatene
TARGET_TABLE_COLUMNS_TO_GROUP_BY = {
    "ansatt_gruppert_hr_avdeling_antall": [
        "kjonn",
        "aldersgruppe",
        "ansiennitetsgruppe",
        "orgniv1_navn",  # direktorat (skal bare være 1)
        "orgniv2_navn",  # avdeling
        "org_seksjon",  # seksjon er en ny kolonne som er laget av coalesce orgniv25 + orgniv3
        "lederniva",  # tall fra hr-systemet om hierarkiet for lederskap
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
    "ansatt_gruppert_hr_ansatt_stilling_per_seksjon": [
        "kjonn",
        "aldersgruppe",
        "ansiennitetsgruppe",
        "stillingsnavn",
        "orgniv1_navn",
        "orgniv2_navn",
        "org_seksjon",
        "lederniva",
    ],
}
# hvilken ny tabell skal lages basert på hvilken kildetabell
# en kildetabell kan gi flere output-tabeller
TARGET_TABLE_TO_SOURCE_TABLE_MAPPING = {
    "ansatt_gruppert_hr_avdeling_antall": "ansatte_plus_teamkatalog_raw",
    "ansatt_gruppert_tk_medlemskap_antall": "ansatte_plus_teamkatalog_raw",
    "ansatt_gruppert_hr_stilling_antall": "ansatte_plus_teamkatalog_roller_raw",
    "ansatt_gruppert_tk_roller_antall": "ansatte_plus_teamkatalog_roller_raw",
    "ansatt_gruppert_hr_ansatt_stilling_per_seksjon": "ansatte_plus_teamkatalog_raw",
}
# slipp å definere target tabeller to ganger, hent fra dict over
TARGET_TABLES_LIST = list(TARGET_TABLE_TO_SOURCE_TABLE_MAPPING.keys())
# vi lager nye dataframes som skal ende opp som nye bigquery tabeller
TARGET_TABLE_DF_CONTAINER: dict[str, pd.DataFrame | None] = {}
# None betyr error i laging av df-en


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

    # teknologiavdelingen har ett ekstra nivå på organisasjonskartet
    # for å finne seksjon vil vi ta coalesce orgniv25 + orgniv3
    # og bruke orgniv3 på alle untatt teknologi som har orgniv25 som vi bruker som seksjon
    if "orgniv25_navn" in output_df.columns and "orgniv3_navn" in output_df.columns:
        output_df["org_seksjon"] = output_df["orgniv25_navn"].combine_first(output_df["orgniv3_navn"])

    # fjern potensiell whitespace i avelinger og seksjoner
    output_df["orgniv1_navn"] = output_df["orgniv1_navn"].str.strip()
    output_df["orgniv2_navn"] = output_df["orgniv2_navn"].str.strip()
    if "org_seksjon" in output_df.columns:
        output_df["org_seksjon"] = output_df["org_seksjon"].str.strip()
    if "omrade" in output_df.columns:
        output_df["omrade"] = output_df["omrade"].str.strip()

    if "lederniva" in output_df.columns:
        if output_df["lederniva"].isna().any():
            logging.warning("Lederenivå inneholder NA-verdier før konvertering til int, sjekk for feil")
        try:
            output_df["lederniva"] = pd.to_numeric(output_df["lederniva"], errors="raise", downcast="integer")
        except ValueError as e:
            logging.error(f"Problemer med konvertering av lederniva til ren integer: \n{e}")
            logging.error("Skriver ut NaN-verdier der konvertering feilet")
            output_df["lederniva"] = pd.to_numeric(output_df["lederniva"], errors="coerce", downcast="integer")

        # gjør om verdier til brukervennlig tekst når vi garantert har ints, NA blir stående
        # kan få nye NA-verdier hvis det dukker opp ints som ikke har en mapping, disse er ikke definert i hierarkiet
        output_df = df_map_stillingsniva_til_titler(output_df, lederniva_column="lederniva")

    # send warning om NaN/Null verdier i spesifikke kolonner, datafeil
    if "aldersgruppe" in output_df.columns and output_df["aldersgruppe"].isna().any():
        logging.warning("Aldersgruppe inneholder NA-verdier, sjekk for feil i kilde")
        logging.warning("Skriver ut 'Ukjent alder' til dashboard")
    if "ansiennitetsgruppe" in output_df.columns and output_df["ansiennitetsgruppe"].isna().any():
        logging.warning("Ansiennitetsgruppe inneholder NA-verdier, sjekk for feil i kilde")
        logging.warning("Skriver ut 'Ukjent ansettelsesår' til dashboard")
    if "kjonn" in output_df.columns and output_df["kjonn"].isna().any():
        logging.warning("Kjønn inneholder NA-verdier, sjekk for feil i pipeline da kildedata skal være filtrert")
        logging.warning("Skriver ut 'Ukjent kjønn' til dashboard")
    if "omrade" in output_df.columns and output_df["omrade"].isna().any():
        logging.debug("Knytning til teamkatalog har NA-verdier: er som forventet")

    # generisk erstatning
    output_df = output_df.fillna("Ukjent")

    # erstatt med mer spesifikke brukervennlige verdier for disse kolonnene
    output_df = nan_to_user_friendly_string(output_df)

    # hvorfor erstatte her og ikke over? fordi kategorisk data-type i noen kolonner crasher om man sender inn en ny verdi
    # OGSÅ når ikke noe skal erstattes, så man kan ikke fillna med forskjellige verdier per kolonne om noen kolonner er kategorisk
    # og skal ha en annen fill-verdi

    return output_df


def nan_to_user_friendly_string(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Erstatt gitte kolonners NA-verdier med brukervennlige verdier som kan vises i endelig dashboard

    Ny tekst som skal brukes avhenger av kolonnen som erstattes, så skriver inn begge manuelt

    Alle NA-verdier i kildedata skal være fylt inn med "Ukjent" allerede
    """
    if "aldersgruppe" in input_df.columns:
        input_df["aldersgruppe"] = input_df["aldersgruppe"].cat.rename_categories({"Ukjent": "Ukjent alder"})
    if "ansiennitetsgruppe" in input_df.columns:
        input_df["ansiennitetsgruppe"] = input_df["ansiennitetsgruppe"].cat.rename_categories({"Ukjent": "Ukjent ansettelsesår"})
    if "kjonn" in input_df.columns:
        input_df[["kjonn"]] = input_df[["kjonn"]].replace({"Ukjent": "Ukjent kjønn"})
    if "sektor" in input_df.columns:
        input_df[["sektor"]] = input_df[["sektor"]].replace({"Ukjent": "Ukjent ansattstatus"})
    if "stillingsnavn" in input_df.columns:
        # ekstra erstatning her, for spesifikk kategori med manglende data vi får fra hr
        input_df[["stillingsnavn"]] = input_df[["stillingsnavn"]].replace(
            {"Ukjent": "Ukjent stilling", "Statlig - Mangler registrering i Agresso": "Ukjent stilling"}
        )
    if "lederniva" in input_df.columns:
        input_df["lederniva"] = input_df["lederniva"].replace({"Ukjent": "Ukjent niva"})
    # NOTE: har vurdert å slå sammen små stillingsgrupper til "Annen stilling", men har ikke gjort det til slutt
    # teamkatalog tilknytning
    if "omrade" in input_df.columns:
        input_df[["omrade"]] = input_df[["omrade"]].replace({"Ukjent": "Mangler tilknytning til teamkatalogen"})
    if "team" in input_df.columns:
        input_df[["team"]] = input_df[["team"]].replace({"Ukjent": "Mangler tilknytning til teamkatalogen"})
    if "rolle" in input_df.columns:
        input_df[["rolle"]] = input_df[["rolle"]].replace({"Ukjent": "Mangler tilknytning til teamkatalogen"})
    if "roller" in input_df.columns:
        input_df[["roller"]] = input_df[["roller"]].replace({"Ukjent": "Mangler tilknytning til teamkatalogen"})
    if "role" in input_df.columns:
        input_df[["role"]] = input_df[["role"]].replace({"Ukjent": "Mangler tilknytning til teamkatalogen"})
    if "roles" in input_df.columns:
        input_df[["roles"]] = input_df[["roles"]].replace({"Ukjent": "Mangler tilknytning til teamkatalogen"})

    return input_df


def df_map_stillingsniva_til_titler(input_df: pd.DataFrame, lederniva_column: str = "lederniva") -> pd.DataFrame:
    """
    Gjør om integers i dataen for ledernivå til brukervennlig tekst

    nivåer som ikke er i mapping blir gjort om til NA, så kjør før erstatning av NA-verdier,
    slike verdier er ikke veldefinert i hierarkiet

    tekst som brukes er fra bruker-innspill
    """
    roller_mapping = {
        1: "Arbeids- og velferdsdirektør",
        2: "Direktør",
        3: "Avdelingsdirektør",
        4: "Seksjonssjef",
        5: "Kontorsjef",
        6: "Ressurs",
    }

    input_df[lederniva_column] = input_df[lederniva_column].map(roller_mapping)

    return input_df


def make_and_upload_metadata_table(
    CURRENT_PROJECT_ID: str, bigquery_data_error: bool, bq_client_premade: Client, upload_to_bq: bool = False
) -> bool:
    """
    Lager metadata-tabell som lastes opp i BigQuery

    Inkluderer status på datalast og logging i kolonner
    """
    upload_metadata_error = False

    # sjekk om det var noen tidligere .error i koden
    any_logged_errors: bool = error_flag_handler.error_logged

    metadata_dict = {
        "Status_datalast": f"{'OK' if not bigquery_data_error else 'ERROR'}",
        "Status_logging": f"{'Feil skjedde, sjekk logger i airflow' if any_logged_errors else 'Ingen feil logget'}",
        "Datalast_dato_timestamp": pd.Timestamp.now(tz="Europe/Oslo"),
        "Datalast_dato_string": pd.Timestamp.now(tz="Europe/Oslo").strftime("%Y-%m-%d %H:%M:%S%z"),
    }

    metadata_df = pd.DataFrame(metadata_dict, index=[0])

    if upload_to_bq:
        try:
            bq_funksjoner.bigquery_upload_hr_df(
                hr_df=metadata_df,
                PROJECT_ID=CURRENT_PROJECT_ID,
                SA_KEY_NAME=SA_KEY_NAME,
                DATASET=PROCESSED_DATASET,
                TABLE_NAME=METADATA_TABLE_NAME,
                bq_client_premade=bq_client_premade,
                write_disposition_setting="WRITE_APPEND",
            )
        except bq_exceptions.BigQueryError as e:
            logging.error(f"Feil ved opplasting av metadata til BigQuery-tabellen `{METADATA_TABLE_NAME}`: \n{e}")
            upload_metadata_error = True
        else:
            logging.info(f"Lastet opp {metadata_df.shape[0]} rad metadata til BigQuery-tabellen `{METADATA_TABLE_NAME}`")
    else:
        logging.info(f"""\nWould upload metadata via:
        bq_funksjoner.bigquery_upload_hr_df(
            hr_df=metadata_df,
            PROJECT_ID={CURRENT_PROJECT_ID},
            SA_KEY_NAME={SA_KEY_NAME},
            DATASET={PROCESSED_DATASET},
            TABLE_NAME={METADATA_TABLE_NAME},
            bq_client_premade=bq_client,
            write_disposition_setting="WRITE_TRUNCATE",
        )
        """)
    return upload_metadata_error


def prod_main(CURRENT_PROJECT_ID: str, PROD_ENV: str | None, DAG_NODE: str | None, upload_to_bq: bool = False) -> int:
    if not DAG_NODE:  # kjører lokal debug
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Kjører i prod environment")

    bq_client: Client = tk_funksjoner.create_client(PROD_PROJECT_ID, SA_KEY_NAME)
    bigquery_data_error: bool = False

    # hent data fra BigQuery
    for source_table, fetch_query in SOURCE_TABLES_SQL_QUERY.items():
        if fetch_query:
            try:  # ikke kræsj alt av data-henting fordi en tabell feilet
                logging.info(f"Henter data fra BigQuery-tabellen `{source_table}`")
                logging.debug(f"Kolonner som hentes: {SOURCE_TABLES_AND_COLUMNS[source_table]}")
                big_query_result_df = bq_client.query(fetch_query).to_dataframe()

                BQ_TABLE_DF_CONTAINER[source_table] = big_query_result_df
                logging.info(f"Hentet {big_query_result_df.shape[0]} rader og {big_query_result_df.shape[1]} kolonner")
                bigquery_data_error: bool = False

            except bq_exceptions.BigQueryError as e:
                logging.error(
                    f"Databasefeil ved henting av data fra bigquery (sannsynligvis feil eller ikke-eksisterende tabell-navn): \
                    \n{e}"
                )
                logging.error(f"Tabellnavn: `{source_table}`")
                logging.error(f"SQL-spørring som feilet: `{fetch_query}`")
                BQ_TABLE_DF_CONTAINER[source_table] = None  # ingen data ble hentet, så lagrer None i containeren
                bigquery_data_error: bool = True

                continue
            except Exception as e:
                logging.error(f"Feil ved henting av data fra bigquery: \n{e}")
                BQ_TABLE_DF_CONTAINER[source_table] = None
                bigquery_data_error: bool = True
                continue

        else:
            logging.info(f"Skipping `{source_table}` as no columns were specified")

    # kjør første pass med aggregering, fjerner detaljert informasjon om alder og ansettelsesår
    for target_table_name, source_table_name in TARGET_TABLE_TO_SOURCE_TABLE_MAPPING.items():
        # pipeline har en inkludert copy-operasjon
        # så vi forbereder ett nytt dataframe for hver target som en kopi av kilde-tabellene
        # (som kan bruke samme kilde flere ganger)
        bigquery_df = BQ_TABLE_DF_CONTAINER[source_table_name]
        if bigquery_df is not None:
            logging.info(f"Prosesserer data tiltenkt `{target_table_name}` fra kildetabellen `{source_table_name}`")
            TARGET_TABLE_DF_CONTAINER[target_table_name] = bigquery_df_process_pipeline(bigquery_df)
        else:
            logging.error(f"Kunne ikke prosessere data for `{target_table_name}` fordi henting av kildedata hadde en feil")
            TARGET_TABLE_DF_CONTAINER[target_table_name] = None
            continue

    # lag target tabeller som skal lastes opp i BigQuery som resultat til bruk av backend/frontend
    for target_table in TARGET_TABLES_LIST:
        target_table_source = TARGET_TABLE_DF_CONTAINER[target_table]
        if target_table_source is None:
            logging.error(f"Kunne ikke prosessere data for `{target_table}` fordi henting av kildedata hadde en feil")
            continue
        else:
            # patch for å være sikker på unike verdier med ansettelse,
            # teamkatalog kan ha flere tilknytninger men du kan ikke være ansatt flere steder
            if target_table in ["ansatt_gruppert_hr_avdeling_antall", "ansatt_gruppert_hr_stilling_antall"]:
                target_table_source = target_table_source.drop_duplicates(subset=["pseudo_key"], keep="first")
            # grupperer på gitte kolonner og teller opp
            # vi ønsker en rad per mulige kombinasjoner av kjønn, aldersgruppe, ansiennitetsgruppe, avdeling, etc.
            # med antall hvor mange som passer i disse kombinasjonene
            grouped_df = target_table_source.groupby(
                TARGET_TABLE_COLUMNS_TO_GROUP_BY[target_table], dropna=False, as_index=False, observed=True
            ).size()

            grouped_df = grouped_df.rename(columns={"size": "antall"})  # type: ignore ,wrong inference from .size()
            # sorter sånn at største gruppe kommer først NOTE: kan hende vi fjerner
            grouped_df = grouped_df.sort_values(by=["antall"], ascending=False)

            ## håndtering av kolonner som bare er i noen av settene
            # gi bedre navn til roller fra teamkatalogen
            if "rolle" in grouped_df.columns:
                grouped_df = hr_data_map_roles_to_tk_names(grouped_df, role_column="rolle")

            # TODO: gjør noe med grupper som blir for små? slå sammen noen små seksjoner?

            logging.debug(grouped_df.info())
            logging.debug(grouped_df.describe())
            if not DAG_NODE:
                grouped_df.to_csv(f"test_grouped_df_{target_table}.csv", index=True, index_label="index")
                logging.debug(f"Skrev prosessert data til `test_grouped_df_{target_table}.csv` for inspeksjon")

            if upload_to_bq:
                try:
                    bq_funksjoner.bigquery_upload_hr_df(
                        hr_df=grouped_df,
                        PROJECT_ID=PROD_PROJECT_ID,
                        SA_KEY_NAME=SA_KEY_NAME,
                        DATASET=PROCESSED_DATASET,
                        TABLE_NAME=target_table,
                        bq_client_premade=bq_client,
                        write_disposition_setting="WRITE_TRUNCATE",
                    )
                    logging.info(f"Lastet opp {grouped_df.shape[0]} rader til BigQuery-tabellen `{target_table}`")
                except bq_exceptions.BigQueryError as e:
                    logging.error(f"Feil ved opplasting av data til BigQuery-tabellen `{target_table}`: \n{e}")
                    bigquery_data_error = True
                    continue
            else:
                logging.info(f"""\nWould upload:
                bq_funksjoner.bigquery_upload_hr_df(
                    hr_df=grouped_df,
                    PROJECT_ID={PROD_PROJECT_ID},
                    SA_KEY_NAME={SA_KEY_NAME},
                    DATASET={PROCESSED_DATASET},
                    TABLE_NAME={target_table},
                    bq_client_premade=bq_client,
                    write_disposition_setting="WRITE_TRUNCATE",
                )
                """)

    metadata_upload_error = make_and_upload_metadata_table(
        CURRENT_PROJECT_ID=PROD_PROJECT_ID,
        bigquery_data_error=bigquery_data_error,
        bq_client_premade=bq_client,
        upload_to_bq=upload_to_bq,
    )

    if bigquery_data_error is True:
        logging.error("En eller flere BigQuery-tabeller hadde en feil ved henting/opplasting av data, se logg for detaljer")
        return 1
    if metadata_upload_error is True:
        logging.error("Feil ved opplasting av metadata til BigQuery-tabellen, se logg for detaljer")
        return 1

    # default
    return 0


def dev_main(CURRENT_PROJECT_ID: str, PROD_ENV: str | None, DAG_NODE: str | None, upload_to_bq: bool = False) -> int:
    # NOTE: dev struktur svarer ikke til det som brukes i prod lenger
    if not DAG_NODE:
        logging.getLogger().setLevel(logging.DEBUG)

    PROD_ENV = os.getenv("PROD_ENV", None)
    if PROD_ENV:
        raise ValueError(
            f"Du har satt PROD_ENV variabelen til å indikere prod-environment etter å ha startet programmet. Ikke gjør det. \
            \nPROD_ENV={PROD_ENV}"
        )

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
        logging.info(f"Lastet opp {df_test_mangfold_data_processed.shape[0]} rader til BigQuery-tabellen `{TEST_TABLE_NAME}`")
    else:
        logging.info(f"""\nWould upload:
        bq_funksjoner.bigquery_upload_hr_df(
            hr_df=df_test_mangfold_data_processed,
            PROJECT_ID={DEV_PROJECT_ID},
            SA_KEY_NAME={SA_KEY_NAME},
            DATASET={PROCESSED_DATASET},
            TABLE_NAME={TEST_TABLE_NAME},
        )
        """)

    return 0


def main(upload_to_bq: bool = False) -> int:
    """Main funksjon som knytter sammen metoder i andre filer"""
    # sjekk environment
    PROD_ENV = os.getenv("PROD_ENV", None)  # set in production env to process real data
    DAG_NODE = os.getenv("DAG_NODE", None)  # set on node running airflow to avoid file writes

    if DAG_NODE:
        logging.info("Kjører i Airflow som DAG")
    else:
        logging.info("Kjører lokalt")

    if PROD_ENV:
        CURRENT_PROJECT_ID = PROD_PROJECT_ID
    else:
        CURRENT_PROJECT_ID = DEV_PROJECT_ID

    if PROD_ENV:
        retcode = prod_main(CURRENT_PROJECT_ID, PROD_ENV, DAG_NODE, upload_to_bq=upload_to_bq)

    # not prod => dev environment
    else:
        retcode = dev_main(CURRENT_PROJECT_ID, PROD_ENV, DAG_NODE, upload_to_bq=upload_to_bq)

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
