"""
Prosseserer hr-data (kan kjøre både test og reell data) til forventet format.

Gjør aggregeringer av kolonner og kobler på andre datasett
"""

import sys
from pathlib import Path

import pandas as pd
from dateutil import relativedelta

sys.path.append("../..")
from hr_data.hr_data_prosessering.df_funksjoner import read_test_data_csv, to_datetime_wrapper, write_test_data_csv


def df_aggregate_age(input_df: pd.DataFrame) -> pd.DataFrame:
    today_date = to_datetime_wrapper("today")

    for i in input_df.index:
        input_df.loc[i, "aldersgruppe"] = relativedelta.relativedelta(today_date, input_df.loc[i, "fodselsdato"]).years  # type: ignore
        # type inference er ikke riktig på df.loc

    # aldersgrupper er 0-30, 30-50, 50-1000 (ikke at noen er 1000 år gamle)
    # NOTE: hvis noen er over 1000 år gamle skal de bli stående som NAN i endelig data, obs på dette
    # det betyr kildedata har feil fødselsdato
    input_df["aldersgruppe"] = pd.cut(
        input_df["aldersgruppe"],
        bins=[-1, 30, 50, 1000],
        labels=["<30", "30-50", "50+"],
    )

    input_df = input_df.drop(columns=["fodselsdato"])
    return input_df


def df_change_id_column(input_df: pd.DataFrame) -> pd.DataFrame:
    input_df = input_df.sample(frac=1).reset_index(drop=True)
    input_df["nav_id"] = input_df.index.astype(str).str.zfill(4)  # gjør til id på form 0001 etc.
    input_df = input_df.rename(columns={"nav_id": "rad_id"})

    return input_df


def df_aggregate_worked_years(input_df: pd.DataFrame) -> pd.DataFrame:
    today_date = to_datetime_wrapper("today")

    # for test data er dette bare revers av noe som allerede er kjørt, men det er nødvendig på reell data
    # som allerede har dette formatet
    input_df["ansatt_til"] = input_df["ansatt_til"].mask(input_df["ansatt_til"].gt(today_date), today_date)

    for i in input_df.index:
        input_df.loc[i, "ansiennitetsgruppe"] = relativedelta.relativedelta(
            input_df.loc[i, "ansatt_til"],  # type: ignore
            input_df.loc[i, "ansatt_fra"],  # type: ignore
        ).years
        # feil type inference på df.loc (er to datetimes med utc timezone)

    # ansiennitetsgrupper er 0-2, 2-4, 4-6, 6-8, 8-10, 10-16, 16+
    input_df["ansiennitetsgruppe"] = pd.cut(
        input_df["ansiennitetsgruppe"],
        bins=[-1, 2, 4, 6, 8, 10, 16, 1000],
        labels=["0-2", "2-4", "4-6", "6-8", "8-10", "10-16", "16+"],
    )

    input_df = input_df.drop(columns=["ansatt_til"])
    input_df = input_df.drop(columns=["ansatt_fra"])
    return input_df


def df_process_pipeline(input_df: pd.DataFrame) -> pd.DataFrame:
    """Kjører prosessering på df i riktig rekkefølge"""
    output_df = input_df.copy()
    output_df = df_change_id_column(output_df)
    output_df = df_aggregate_age(output_df)
    output_df = df_aggregate_worked_years(output_df)

    return output_df


def main(SOURCE_DATA: dict, target_data_filename: Path) -> None:
    if SOURCE_DATA["csv"] is not None:
        df_test_mangfold_data = read_test_data_csv(SOURCE_DATA["csv"], date_column_indexes=[1, 2, 8])
    else:
        raise NotImplementedError

    df_test_mangfold_data = df_process_pipeline(df_test_mangfold_data)

    print(df_test_mangfold_data.head(10))
    print(df_test_mangfold_data.info())

    write_test_data_csv(df_test_mangfold_data, target_data_filename)

    return None


if __name__ == "__main__":
    SOURCE_DATA = {"csv": Path("test_data_hr.csv")}
    TARGET_DATA_FILENAME = Path("test_data_hr_prossesert.csv")
    main(SOURCE_DATA, TARGET_DATA_FILENAME)
