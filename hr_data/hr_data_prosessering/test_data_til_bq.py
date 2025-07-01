"""
Leser inn test-data (csv) med forventet struktur for å kunne teste frontend

henter data som er laget direkte i pandas og laster opp til BigQuery test-tabell
(prod vs dev environment?)
"""

import logging
import sys
from pathlib import Path

sys.path.append("../..")  # importere fra teamkatalogen_bq
import hr_data.bigquery_funksjoner as bq_funksjoner
import hr_data.main_prosessering as settings
from hr_data.hr_data_prosessering.df_funksjoner import read_test_data_csv


def main(data_source: Path, dry_run: bool = True) -> None:
    if dry_run:
        logging.getLogger().setLevel(logging.DEBUG)

    df_test_mangfold_data = read_test_data_csv(data_source, date_column_indexes=[])
    cols_test_mangfold_data = df_test_mangfold_data.columns

    logging.info(f"Kolonner i dataframe som blir brukt: \n{cols_test_mangfold_data}")
    logging.info(f"Generert test dataframe: \n{df_test_mangfold_data.head(10)}")
    # logging.info(f"{df_test_mangfold_data.info()}")

    if not dry_run:
        bq_funksjoner.bigquery_upload_hr_df(
            hr_df=df_test_mangfold_data,
            PROJECT_ID=settings.DEV_PROJECT_ID,
            SA_KEY_NAME=settings.SA_KEY_NAME,
            DATASET=settings.PROCESSED_DATASET,
            TABLE_NAME=settings.TEST_TABLE_NAME,
        )
    else:
        logging.info(f"""\nWould upload:
        bq_funksjoner.bigquery_upload_hr_df(
            hr_df=df_test,
            PROJECT_ID={settings.DEV_PROJECT_ID},
            SA_KEY_NAME={settings.SA_KEY_NAME},
            DATASET={settings.PROCESSED_DATASET},
            TABLE_NAME={settings.TEST_TABLE_NAME},
        )
        """)

    return None


if __name__ == "__main__":
    logging.basicConfig()
    dry_run = True

    data_source_path = Path(settings.TEST_DATA_PROCESSED_FILENAME).resolve()
    main(data_source_path, dry_run=dry_run)
