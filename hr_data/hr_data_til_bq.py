"""
daglig DAG for speiling av hr-tabell fra oracle til bigquery

laster data fra Oracle onprem til BQ
"""

import json
import logging
import os
import sys

import oracledb
import pandas as pd
from google.cloud import secretmanager

sys.path.append("..")  # importere fra teamkatalogen_bq
from hr_data.bigquery_funksjoner import bigquery_upload_hr_df


def hent_oracle_data_til_df(sql_query: str | None = None):
    if sql_query is None:
        raise ValueError("Must have an SQL query to execute against connected Oracle database")

    # hente secret fra Google Secret Manager
    secret_name = "dvh_srv_team_heda_py"
    logging.info(f"Setter miljøvariabl-hemmeligheter fra: {secret_name}")
    full_secret_name = f"projects/847673271220/secrets/{secret_name}/versions/latest"
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": full_secret_name})
    secret = json.loads(response.payload.data.decode("UTF-8"))

    os.environ["DB_HOST"] = secret["DB_HOST"]
    os.environ["DB_PORT"] = secret["DB_PORT"]
    os.environ["DB_USER"] = secret["DB_USER"]
    os.environ["DB_PASSWORD"] = secret["DB_PASSWORD"]
    os.environ["DB_SERVICE_NAME"] = secret["DB_SERVICE_NAME"]

    logging.info(
        f"Secrets for {os.environ['DB_USER']} mot {os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_SERVICE_NAME']}"
    )

    # koble til Oracle og kjøre spørring
    connection = oracledb.connect(
        port=os.environ["DB_PORT"],
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        service_name=os.environ["DB_SERVICE_NAME"],
    )

    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0].lower() for col in cursor.description]
        data = cursor.fetchall()
    df_ansatte = pd.DataFrame(data, columns=columns)
    logging.info(f"Hentet {len(df_ansatte)} rader fra Oracle")
    logging.debug(f"Brukte SQL-spørring: `{sql_query}`")
    connection.close()

    return df_ansatte


def main(project: str | None = None):
    # maps a source oracle DB table to the target BigQuery table name to which it should be mirrored by daily uploads
    oracle_source_to_target_bigquery_mapping_dict = {
        "dt_hr.hrres_ressurs_sommer": "ansatte_direktoratet_raw",
        "dt_hr.hrres_ressurs_sommer_tk": "ansatte_plus_teamkatalog_raw",
        "dt_hr.hrres_ressurs_sommer_tk_roller": "ansatte_plus_teamkatalog_roller_raw",
        "dt_hr.hrres_ressurs_sommer_tk_grupper": "ansatte_teamkatalog_grupper_raw",
    }

    bq_dataset = "hr_data"
    sa_key_name = "heda-access-key"

    for oracle_source_table, bq_target_table in oracle_source_to_target_bigquery_mapping_dict.items():
        sql: str = f"select * from {oracle_source_table}"
        # flagg for om oracle-spørringen feilet: oracle_data_error: bool

        # henter fra Oracle
        try:
            df_ansatte = hent_oracle_data_til_df(sql_query=sql)
            oracle_data_error: bool = False  # flagg for om oracle-spørringen feilet
        except oracledb.DatabaseError as e:
            logging.error(
                f"Databasefeil ved henting av data fra Oracle (sannsynligvis feil eller ikke-eksisterende tabell-navn): \n{e}"
            )
            logging.error(f"Tabellnavn: `{oracle_source_table}`")
            logging.error(f"SQL-spørring som feilet: `{sql}`")
            oracle_data_error: bool = True

            continue
        except Exception as e:
            logging.error(f"Feil ved henting av data fra Oracle: \n{e}")
            oracle_data_error: bool = True
            continue

        # sender data til BigQuery
        if oracle_data_error is False:
            bigquery_upload_hr_df(
                hr_df=df_ansatte,
                PROJECT_ID=project,
                SA_KEY_NAME=sa_key_name,
                DATASET=bq_dataset,
                TABLE_NAME=bq_target_table,
            )
            logging.info(f"Lastet opp {len(df_ansatte)} rader til BigQuery-tabellen `{bq_target_table}`")
        elif oracle_data_error is True:
            logging.error(
                f"Hoppet over lasting av data til BigQuery-tabellen `{bq_target_table}`,\
                      siden Oracle-spørring feilet og ingen data ble hentet"
            )
            continue
        else:  # else skal aldri kunne skje
            raise ValueError("Status på Oracle data er udefinert, kan ikke fortsette")

    return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    project = "heda-prod-2664"

    main(project=project)
