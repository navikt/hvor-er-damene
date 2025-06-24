"""
Prosseserer hr-data (kan kjøre både test og reell data) til forventet format.

Gjør aggregeringer av kolonner og kobler på andre datasett
"""

import csv
from pathlib import Path

import pandas as pd
from dateutil import relativedelta

from df_funksjoner import read_test_data_csv, to_datetime_wrapper, write_test_data_csv


def df_aggregate_age(df: pd.DataFrame):
    today_date = to_datetime_wrapper("today")

    for i in df.index:
        df.loc[i, "aldersgruppe"] = relativedelta.relativedelta(today_date, df.loc[i, "fodselsdato"]).years

    # aldersgrupper er 0-30, 30-50, 50-1000 (ikke at noen er 1000 år gamle)
    # NOTE: hvis noen er over 1000 år gamle skal de bli stående som NAN i endelig data, obs på dette
    # det betyr kildedata har feil fødselsdato
    df["aldersgruppe"] = pd.cut(
        df["aldersgruppe"],
        bins=[-1, 30, 50, 1000],
        labels=["<30", "30-50", "50+"],
    )

    df.drop(columns=["fodselsdato"], inplace=True)
    return df


def df_change_id_column(df):
    df = df.sample(frac=1).reset_index(drop=True)
    df["nav_id"] = df.index.astype(str).str.zfill(4)  # gjør til id på form 0001 etc.
    df.rename(columns={"nav_id": "rad_id"}, inplace=True)

    return df


def df_aggregate_worked_years(df: pd.DataFrame):
    today_date = to_datetime_wrapper("today")

    # for test data er dette bare revers av noe som allerede er kjørt, men det er nødvendig på reell data
    # som allerede har dette formatet
    df["ansatt_til"] = df["ansatt_til"].mask(df["ansatt_til"].gt(today_date), today_date)

    for i in df.index:
        df.loc[i, "ansiennitetsgruppe"] = relativedelta.relativedelta(df.loc[i, "ansatt_til"], df.loc[i, "ansatt_fra"]).years

    # ansiennitetsgrupper er 0-2, 2-4, 4-6, 6-8, 8-10, 10-16, 16+
    df["ansiennitetsgruppe"] = pd.cut(
        df["ansiennitetsgruppe"],
        bins=[-1, 2, 4, 6, 8, 10, 16, 1000],
        labels=["0-2", "2-4", "4-6", "6-8", "8-10", "10-16", "16+"],
    )

    df.drop(columns=["ansatt_til"], inplace=True)
    df.drop(columns=["ansatt_fra"], inplace=True)
    return df


def main(SOURCE_DATA):
    if SOURCE_DATA["csv"] is not None:
        df_test_mangfold_data = read_test_data_csv(SOURCE_DATA["csv"], date_column_indexes=[1, 2, 8])
    else:
        raise NotImplementedError

    df_test_mangfold_data = df_change_id_column(df_test_mangfold_data)
    df_test_mangfold_data = df_aggregate_age(df_test_mangfold_data)
    df_test_mangfold_data = df_aggregate_worked_years(df_test_mangfold_data)

    print(df_test_mangfold_data.head(10))
    print(df_test_mangfold_data.info())

    write_test_data_csv(df_test_mangfold_data, Path("test_data_hr_prossesert.csv"))

    return None


if __name__ == "__main__":
    SOURCE_DATA = {"csv": Path("test_data_hr.csv")}
    main(SOURCE_DATA)
