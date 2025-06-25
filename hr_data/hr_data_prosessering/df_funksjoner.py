"""Støttefunksjoner til håndtering av dataframes"""

import csv
from pathlib import Path

import pandas as pd


def read_test_data_csv(source_csv_filename: Path, date_column_indexes: list | None = None) -> pd.DataFrame:
    if date_column_indexes is None:
        raise ValueError("date_column_indexes must be provided as a list of column indexes in target csv file (0-indexed)")

    df_test_mangfold_data = pd.read_csv(
        source_csv_filename,
        header=0,
        index_col=False,
        sep=";",
        parse_dates=date_column_indexes,
        skipinitialspace=True,
        quoting=csv.QUOTE_MINIMAL,
    )

    return df_test_mangfold_data


def write_test_data_csv(df: pd.DataFrame, target_csv_filename: Path) -> None:
    df.to_csv(target_csv_filename, index=False, sep=";", quoting=1, header=True)

    return None


def to_datetime_wrapper(date_str: str) -> pd.Timestamp:
    """Wrapper function to avoid repeating the same transformations everywhere (and shorten code somewhat)

    NOTE: Instead of localizing properly, we drop times and just use the date - nothing we do is precise enough that this matters,
    so we set the attached time to midnight (00:00:00) in UTC. The data is all from Norway,
    but some of it is already normalized to 00:00:00 which we don't want to localize to european timezone,
    as this would change the date. So we just "reduce" it to midnight UTC.
    """
    return pd.to_datetime(date_str, utc=True).normalize()
