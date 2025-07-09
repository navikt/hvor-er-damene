# Sommerstudenter: Mangfoldsprosjekt
Underprosjekt av [#heda](../README.md)

[Sommerstudenter med Team Heda](https://teamkatalog.nav.no/team/1ae1604f-1007-4846-9cea-0153a0ad7c8c) er ansvarlig.

Se også [`README.md`](../README.md) for over-prosjektet, og de relaterte sommerstudent-repoene [mangfold-frontend](https://github.com/navikt/mangfold-frontend) og [mangfold-backend](https://github.com/navikt/mangfold-backend). Prosjektet er organisert på Slack, se `#sommerstudent-prosjekt-mangfold` for mer informasjon.

## Datalast
### Kilde
Data hentes fra HR-data i Oracle database. Se Python-skriptene [`daglig_hr_data_til_bq.py`](../dags/daglig_hr_data_til_bq.py) og [`hr_data_til_bq.py`](hr_data_til_bq.py).

### Tabeller
Tabellene som blir laget ligger i BigQuery i Heda sitt prod gcp-prosjekt. Test data er i dev prosjekt.

Se `#sommerstudent-prosjekt-mangfold` i Slack for mer informasjon om tabeller. Det lages tabeller som speiler view fra datavarehus ([`hr_data_til_bq.py`](hr_data_til_bq.py)), og nye aggregerte tabeller som brukes till innsikt og rapportering ([`main_prosessering.py`](../hr_data/main_prosessering.py)).

### Skedulering
Datalasten kjøres daglig om morgenen (Oslo) via Heda sin [airflow](https://heda.airflow.knada.io/).

Prosessering kjøres etter data-last, og oppdaterer automatisk tabeller i BigQuery som skal brukes til endelig dashboard.

Se hoved-dokumentering i [README.md](../README.md)

## Oppsett

### uv / pip
Se [`requirements_bq.txt`](../requirements_bq.txt) for nødvendige pakker til `hr_data` prosjektet. Kan brukes av standard Python metoder, DAG og sommerstudenter kjører [uv](https://docs.astral.sh/uv/) som pakkeløsning. Sett opp pakker i et uv-environment med:

```uv pip install -r ../requirements_bq.txt```

Det er også en egen [`pyproject.toml`](hr_data/pyproject.toml) fil for under-prosjektet.

Pass på å alltid kjøre  i `hr_data` mappen.

## Videre arbeid

Underprosjektet har ikke blitt splittet ut i eget repo fordi Airflow og service account var satt opp i dette repoet allerede. Veien videre er enten eget repo eller å erstatte overprosjektet som ikke lenger vil være i bruk siden det ble bygget uten tilgang til hr-data og lager et mer begrenset quarto-dashboard.