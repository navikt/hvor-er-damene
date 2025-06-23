"""Lager test data i csv-format med tilfeldige verdier som kan brukes videre i utvikling"""

import numpy as np
import pandas as pd


def n_random_datetimes(start, end, n=10):
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

    return pd.to_datetime(rng.integers(start_u, end_u, n), unit=unit)


def to_datetime_wrapper(date_str):
    """Wrapper function to avoid repeating the same transformations everywhere (and shorten code somewhat)

    NOTE: Instead of localizing properly, we drop times and just use the date - nothing we do is precise enough for this to matter,
    so we set the attached time to midnight (00:00:00) in UTC. The data is all from Norway,
    but some of it is already normalized to 00:00:00 which we don't want to localize to european timezone,
    as this would change the date. So we just "reduce" it to midnight UTC.
    """
    return pd.to_datetime(date_str, utc=True).normalize()


def generate_test_data(num_rows):
    """Genererer testdata med tilfeldige verdier"""
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

    # avdeling, seksjon noen tilhører er helt tilfeldig enda det burde henge sammen med tittel, men det er ikke så farlig
    test_org_avdelinger = {"Teknologi": 0.4, "HR": 0.2, "Sikkerhet": 0.2, "Økonomi": 0.1, "Administrasjon": 0.1}

    test_org_seksjoner = {
        "Utvikling": 0.5,
        "Rekruttering": 0.2,
        "Strategi": 0.1,
        "Regnskap": 0.1,
        "Support": 0.1,
    }

    rng = np.random.default_rng()
    data = {
        "fake_id": [f"{i:04d}" for i in range(1, num_rows + 1)],
        # today som str input til pandas virker som datetime.today()
        "fodselsdato": n_random_datetimes(
            to_datetime_wrapper("1900-01-01"),
            to_datetime_wrapper("today"),
            n=num_rows,
        ).normalize(),  # randomisering setter ikke til midnatt selv om prosessering av kildedata ville gjøre det,
        # så sett normalize() manuelt
        # TODO: alder svarer ikke til fødsel
        "alder": rng.integers(20, 71, size=num_rows),
        "ansatt_i_år": rng.integers(0, 51, size=num_rows),
        "stillingsnavn": rng.choice(
            list(test_stillingstitler.keys()),
            size=num_rows,
            p=list(test_stillingstitler.values()),
        ),
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
        "antall_ansatte_under": rng.integers(0, 10, size=num_rows),
        "lederniva": rng.choice(["1", "2", "3", "4", "5"], size=num_rows),
        "kjonn": rng.choice(["Mann", "Kvinne"], size=num_rows),
    }
    return pd.DataFrame(data)


def main():
    df_test_hr_data = generate_test_data(100)
    print(df_test_hr_data.head(10))

    df_test_hr_data.to_csv("test_data_hr.csv", index=False, sep=";", quoting=1, header=True)


if __name__ == "__main__":
    main()
