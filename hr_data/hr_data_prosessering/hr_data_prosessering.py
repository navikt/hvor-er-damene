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


def hr_data_map_roles_to_tk_names(input_df: pd.DataFrame, role_column: str = "rolle") -> pd.DataFrame:
    # laget manuelt fra å stirre på teamkatalogen
    roller_mapping = {
        "DEVELOPER": "Utvikler",
        "DOMAIN_RESOURCE": "Fagressurs",
        "TECHNICAL_ADVISER": "Teknisk rådgiver",
        "OTHER": "Annet",
        "SECURITY_CHAMPION": "Security champion",
        "LEGAL_ADVISER": "Jurist",
        "DESIGNER": "Designer",
        "LEAD": "Teamleder",
        "PRODUCT_LEAD": "Produktleder",
        "TECH_LEAD": "Tech lead",
        "SUBJECT_MATTER_EXPERT": "Fagekspert",
        "OPERATIONS": "Drift",
        "DOMAIN_RESPONSIBLE": "Fagansvarlig",
        "FUNCTIONAL_ADVISER": "Funksjonell rådgiver",
        "DOMAIN_EXPERT": "Domeneekspert",
        "ARCHITECT": "Arkitekt",
        "DATA_SCIENTIST": "Data scientist",
        "TECH_DOMAIN_SPECIALIST": "Teknisk domenespesialist",
        "SOLUTION_ARCHITECT": "Løsningsarkitekt",
        "DATA_ENGINEER": "Data engineer",
        "BUSINESS_ANALYST": "Andre roller",
        "TESTER": "Andre roller",
        "AREA_LEAD": "Andre roller",
        "COMMUNICATION_ADVISER": "Andre roller",
        "SECURITY_ARCHITECT": "Andre roller",
        "STAFFING_MANAGER": "Andre roller",
        "CONTROLLER": "Andre roller",
        "PLATFORM_SYSTEM_TECHNICIAN": "Andre roller",
        "DATA_MANAGER": "Andre roller",
        "DESIGN_RESEARCHER": "Andre roller",
        "VISUAL_ANALYTICS_ENGINEER": "Andre roller",
        "HEAD_OF_LEGAL": "Andre roller",
        "MAINTENANCE_MANAGER": "Andre roller",
        "TECHNICAL_TESTER": "Andre roller",
        "DESIGN_LEAD": "Andre roller",
    }

    input_df[role_column] = input_df[role_column].map(roller_mapping)

    return input_df


def get_hr_df_relevant_columns(input_df: pd.DataFrame):
    output_df = input_df[["nav_id", "fodselsdato", "ansatt_fra", "ansatt_til", "rolle", "lederniva", "kjonn"]].copy()
    input_df = pd.DataFrame()  # blank out original

    return output_df


def get_tk_df_relevant_columns(input_df: pd.DataFrame):
    output_df = input_df[["nav_id", "organisasjon_avdeling", "organisasjon_seksjon"]].copy()
    input_df = pd.DataFrame()  # blank out original

    return output_df


def df_aggregate_age_from_dateofbirth(input_df: pd.DataFrame) -> pd.DataFrame:
    today_date = to_datetime_wrapper("today")

    for i in input_df.index:
        input_df.loc[i, "aldersgruppe"] = relativedelta.relativedelta(today_date, input_df.loc[i, "fodselsdato"]).years  # type: ignore
        # type inference er ikke riktig på df.loc

    input_df = df_aggregate_age_group(input_df, age_column="aldersgruppe")

    input_df = input_df.drop(columns=["fodselsdato"])
    return input_df


def df_aggregate_age_group(input_df: pd.DataFrame, age_column="aldersgruppe") -> pd.DataFrame:
    """
    Grupperer alder i år fra input_df

    aldersgrupper er 0-30, 30-50, 50-1000 (ikke at noen er 1000 år gamle)
    NOTE: hvis noen er over 1000 år gamle skal de bli stående som NAN i endelig data, obs på dette
    det betyr kildedata har feil fødselsdato
    """
    input_df[age_column] = pd.cut(
        input_df[age_column],
        bins=[-1, 30, 50, 1000],
        labels=["<30", "30-50", "50+"],
    )

    # patch: for å håndtere NaN senere, legg til en kategori for å fange opp ukjent
    input_df[age_column] = input_df[age_column].cat.add_categories("Ukjent")

    return input_df


def df_change_id_column(input_df: pd.DataFrame) -> pd.DataFrame:
    input_df = input_df.sample(frac=1).reset_index(drop=True)  # shuffler
    input_df["nav_id"] = input_df.index.astype(str).str.zfill(4)  # gjør til id på form 0001 etc.
    input_df = input_df.rename(columns={"nav_id": "rad_id"})

    return input_df


def df_aggregate_worked_years_from_timestamps(input_df: pd.DataFrame) -> pd.DataFrame:
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

    input_df = df_aggregate_worked_year_groups(input_df, worked_years_column="ansiennitetsgruppe")

    input_df = input_df.drop(columns=["ansatt_til"])
    input_df = input_df.drop(columns=["ansatt_fra"])
    return input_df


def df_aggregate_worked_year_groups(input_df: pd.DataFrame, worked_years_column="ansiennitetsgruppe") -> pd.DataFrame:
    """
    Grupperer ansiennitet i år fra input_df

    ansiennitetsgrupper er 0-2, 2-4, 4-6, 6-8, 8-10, 10-16, 16+

    NOTE: hvis noen har mer enn 1000 års ansiennitet blir de stående som ansiennetet=NAN, obs på dette
    det betyr kildedata har feil ansatt_fra dato
    """
    input_df[worked_years_column] = pd.cut(
        input_df[worked_years_column],
        bins=[-1, 2, 4, 6, 8, 10, 16, 1000],
        labels=["0-2", "2-4", "4-6", "6-8", "8-10", "10-16", "16+"],
    )

    # patch: for å håndtere NaN senere, legg til en kategori for å fange opp ukjent
    input_df[worked_years_column] = input_df[worked_years_column].cat.add_categories("Ukjent")

    return input_df


def df_hr_process_pipeline(input_df: pd.DataFrame) -> pd.DataFrame:
    """Kjører prosessering på df i riktig rekkefølge"""
    input_df = input_df.rename(columns={"stillingsnavn": "rolle"})  # TODO: prosseser rolle via stillingskatalog
    # (ikke så relevant lenger?)
    output_df = get_hr_df_relevant_columns(input_df)  # kjører copy inne
    output_df = df_aggregate_age_from_dateofbirth(output_df)
    output_df = df_aggregate_worked_years_from_timestamps(output_df)

    return output_df


def df_tk_process_pipeline(input_df: pd.DataFrame) -> pd.DataFrame:
    raise NotImplementedError


def df_mangfold_join_pipeline(input_hr_df: pd.DataFrame, input_tk_df: pd.DataFrame) -> pd.DataFrame:
    output_mangfold_df = input_hr_df.join(input_tk_df.set_index("nav_id"), on="nav_id", how="outer")

    # fjern id-kolonnen når den er brukt, inkluderer omsortering
    output_mangfold_df = df_change_id_column(output_mangfold_df)

    return output_mangfold_df


def main(source_hr_data_filename: Path, target_hr_data_filename: Path, source_tk_data_filename: Path) -> None:
    df_test_hr_data = read_test_data_csv(source_hr_data_filename, date_column_indexes=["fodselsdato", "ansatt_fra", "ansatt_til"])
    df_test_tk_data = read_test_data_csv(source_tk_data_filename, date_column_indexes=[])

    df_test_hr_data = df_hr_process_pipeline(df_test_hr_data)

    df_test_mangfold_data = df_mangfold_join_pipeline(df_test_hr_data, df_test_tk_data)

    print(df_test_mangfold_data.head(10))
    print(df_test_mangfold_data.info())

    write_test_data_csv(df_test_mangfold_data, target_hr_data_filename)

    return None


if __name__ == "__main__":
    source_hr_data_filename = Path("test_data_hr.csv")
    target_hr_data_filename = Path("test_data_hr_prossesert.csv")

    source_tk_data_filename = Path("test_data_tk.csv")
    main(source_hr_data_filename, target_hr_data_filename, source_tk_data_filename)
