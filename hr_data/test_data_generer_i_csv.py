"""Lager test data i csv-format med tilfeldige verdier som kan brukes videre i utvikling"""

import numpy as np
import pandas as pd


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
        "fodselsdato": pd.date_range(start="1980-01-01", periods=num_rows, freq="D"),
        "alder": rng.integers(20, 71, size=num_rows),
        "ansatt_i_år": rng.integers(0, 51, size=num_rows),
        "stillingsnavn": rng.choice(
            list(test_stillingstitler.keys()), size=num_rows, p=list(test_stillingstitler.values())
        ),
        "organisasjon_avdeling": rng.choice(
            list(test_org_avdelinger.keys()), size=num_rows, p=list(test_org_avdelinger.values())
        ),
        "organisasjon_seksjon": rng.choice(
            list(test_org_seksjoner.keys()), size=num_rows, p=list(test_org_seksjoner.values())
        ),
        "antall_ansatte_under": rng.integers(0, 10, size=num_rows),
        "lederniva": rng.choice(["1", "2", "3", "4", "5"], size=num_rows),
        "kjonn": rng.choice(["Mann", "Kvinne"], size=num_rows),
    }
    return pd.DataFrame(data)
