"""
lager test-data med forventet struktur for å kunne teste frontend

lager test-data direkte i pandas og laster opp til BigQuery test-tabell
(prod vs dev environment?)
"""

import logging
import sys

import numpy as np
import pandas as pd
from google.cloud.bigquery import LoadJobConfig

sys.path.append("..")
from teamkatalogen_bq.funksjoner import create_client

PROJECT_ID = "heda-prod-2664"
SA_KEY_NAME = "heda-access-key"
DATASET = "hr_data"
TEST_TABLE_NAME = "test_ansatte_direktoratet"

bq_client = create_client(PROJECT_ID, SA_KEY_NAME)

cols_test_mangfold_data = [
    "fake_id",
    "fodselsdato",
    "alder",
    "ansatt_i_år",
    "stillingsnavn",
    "organisasjon_avdeling",
    "organisasjon_seksjon",
    "antall_ansatte_under",
    "lederniva",
    "kjonn",
]

df_test_mangfold_data = pd.read_csv(
    "test_data_mock.csv", header=None, names=cols_test_mangfold_data, index_col=False, sep=";"
)

logging.info(f"Generert test dataframe: \n{df_test_mangfold_data.head(10)}")

# laste data til BQ
job_config = LoadJobConfig(
    write_disposition="WRITE_TRUNCATE",
    create_disposition="CREATE_IF_NEEDED",
)
bq_dataset = f"{PROJECT_ID}.{DATASET}"
bq_table = f"{bq_dataset}.{TEST_TABLE_NAME}"

run_job = bq_client.load_table_from_dataframe(df_test_mangfold_data, bq_table, job_config=job_config)
run_job.result()
