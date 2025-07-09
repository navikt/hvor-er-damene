"""Lager test data i csv-format med tilfeldige verdier som kan brukes videre i utvikling"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append("../..")  # importere fra teamkatalogen_bq
from hr_data.hr_data_prosessering.df_funksjoner import to_datetime_wrapper, write_test_data_csv


def n_random_datetimes(start: pd.Timestamp, end: pd.Timestamp, n: int = 10) -> pd.DatetimeIndex:
    r"""Function from: https://stackoverflow.com/a/50559321

    unix timestamp is in ns by default.

    divide the unix time value by 10\*\*9 to make it seconds

    The corresponding unit variable is passed to the pd.to_datetime function

    for 1 -> out_format='datetime'
    """
    rng = np.random.default_rng()
    (divide_by, unit) = (10**9, "s")

    start_u = start.value // divide_by
    end_u = end.value // divide_by

    return pd.to_datetime(rng.integers(start_u, end_u, n), unit=unit, utc=True).normalize()


def generate_row_ids(num_rows: int) -> np.ndarray:
    rng = np.random.default_rng()
    ids_array = rng.choice(["A", "B", "C", "D"], num_rows) + rng.integers(1000, 9999, num_rows).astype(str)

    return ids_array


def generate_hr_test_data(num_rows: int, id_col: np.ndarray | None = None) -> pd.DataFrame:
    """
    Genererer testdata med tilfeldige verdier

    Valgfritt: oppgi liste med id-er som brukes som identifiserende kolonne (og kan gjenbrukes i andre metoder for å teste joins)
    """
    rng = np.random.default_rng()

    # vektet med relativt antall av hvor mange som skal dukke opp i test-data
    test_stillingstitler = {
        "Utvikler": 100,
        "Prosjektleder": 10,
        "Designer": 30,
        "Systemadministrator": 35,
        "Dataanalytiker": 100,
        "Data Scientist": 50,
        "Data Engineer": 40,
        "HR-konsulent": 10,
        "HR-ansvarlig": 5,
        "Personalleder": 20,
        "Sikkerhetsansvarlig": 30,
        "Økonomiansvarlig": 5,
        "Direktør": 1,
    }
    # renormaliser til 0-1
    test_stillingstitler = {k: v / sum(test_stillingstitler.values()) for k, v in test_stillingstitler.items()}

    if id_col is None:
        id_col = generate_row_ids(num_rows)

    data = {
        # 4 digits of random ID
        "nav_id": id_col,
        # "today" som str input til pandas virker som datetime.today()
        "fodselsdato": n_random_datetimes(
            to_datetime_wrapper("1900-01-01"),
            to_datetime_wrapper("today"),
            n=num_rows,
        ),
        "ansatt_fra": n_random_datetimes(
            to_datetime_wrapper("1960-01-01"),
            to_datetime_wrapper("today"),
            n=num_rows,
        ),
        "stillingsnavn": rng.choice(
            list(test_stillingstitler.keys()),
            size=num_rows,
            p=list(test_stillingstitler.values()),
        ),
        "lederniva": rng.choice(["1", "2", "3", "4", "5", "6"], size=num_rows, p=[0.0, 0.002, 0.018, 0.03, 0.15, 0.8]),
        "kjonn": rng.choice(["Mann", "Kvinne", "Ukjent"], size=num_rows, p=[0.45, 0.45, 0.10]),
        "irrelevant": rng.choice(["test", "om", "kolonnen", "fjernes"], size=num_rows),
    }

    today_date = to_datetime_wrapper("today")
    # ansatt i tilfeldig periode mellom 1 dag opp til 50 år (365 dager hver), for alle rader
    data["ansatt_til"] = data["ansatt_fra"] + pd.to_timedelta(rng.integers(1, 365 * 50, num_rows), unit="days")

    data_df = pd.DataFrame(data)

    data_df["ansatt_til"] = data_df["ansatt_til"].mask(
        data_df["ansatt_til"].gt(today_date), pd.to_datetime("2099-12-31", utc=True)
    )

    return data_df


def generate_tk_test_data(num_rows: int, id_col: np.ndarray | None = None):
    """Generer test data som tilsvarer teamkatalogen"""
    rng = np.random.default_rng()

    if id_col is None:
        id_col = generate_row_ids(num_rows)

    # sjekk mot excel fra eksport hos teamkatalogen for å finne kolonner som er nyttige til test

    # avdeling, seksjon noen tilhører er helt tilfeldig enda det burde henge sammen med tittel, men det er ikke så farlig
    test_org_avdelinger = {"Teknologi": 0.4, "HR": 0.2, "Sikkerhet": 0.2, "Økonomi": 0.1, "Administrasjon": 0.1}

    test_org_seksjoner = {
        "Utvikling": 0.5,
        "Rekruttering": 0.2,
        "Strategi": 0.1,
        "Regnskap": 0.1,
        "Support": 0.1,
    }

    data = {
        "nav_id": id_col,
        "organisasjon_avdeling": rng.choice(
            list(test_org_avdelinger.keys()),
            size=num_rows,
            p=list(test_org_avdelinger.values()),
        ),
        "organisasjon_seksjon": rng.choice(
            list(test_org_seksjoner.keys()),
            size=num_rows,
            p=list(test_org_seksjoner.values()),
        ),
    }

    data_df = pd.DataFrame(data)

    return data_df


def main(test_hr_data_filename: Path, test_tk_data_filename: Path) -> None:
    n = 100
    ids_array = generate_row_ids(n)

    df_test_hr_data = generate_hr_test_data(n, ids_array)
    print(df_test_hr_data.head(5))

    write_test_data_csv(df_test_hr_data, test_hr_data_filename)

    df_test_tk_data = generate_tk_test_data(n, ids_array)
    # for testing, pass på at indeks ikke er i samme rekkefølge som andre datasett
    df_test_tk_data = df_test_tk_data.sample(frac=1).reset_index(drop=True)
    print(df_test_tk_data.head(5))

    write_test_data_csv(df_test_tk_data, test_tk_data_filename)


if __name__ == "__main__":
    test_hr_data_filename = Path("test_data_hr.csv")
    test_tk_data_filename = Path("test_data_tk.csv")
    main(test_hr_data_filename, test_tk_data_filename)
