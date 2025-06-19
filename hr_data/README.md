# Sommerstudenter: Mangfoldsprosjekt
Underprosjekt av [#heda](../README.md)

[Sommerstudenter med Team Heda](https://teamkatalog.nav.no/team/1ae1604f-1007-4846-9cea-0153a0ad7c8c) er ansvarlig.

## Datalast
### Kilde
Data hentes fra HR-data i Oracle database. Se Python-skriptene [daglig_hr_data_til_bq.py](../dags/daglig_hr_data_til_bq.py) og [hr_data_til_bq.py](hr_data_til_bq.py).

### Tabeller
Tabellene som blir laget ligger i BigQuery i Heda sitt prod gcp-prosjekt. 

### Skedulering
Datalasten kjøres daglig om morgenen (Oslo) via Heda sin [airflow](https://heda.airflow.knada.io/).

Se hoved-dokumentering i [README.md](../README.md)

## Oppsett

### uv / pip
Se [`requirements_bq.txt`](../requirements_bq.txt) for nødvendige pakker til `hr_data` prosjektet. Kan brukes av standard Python metoder, DAG og sommerstudenter kjører [uv](https://docs.astral.sh/uv/) som pakkeløsning. Sett opp pakker i et uv-environment med:

```uv pip install ../requirements_bq.txt```
