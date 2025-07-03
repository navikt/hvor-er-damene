# hvor-er-damene
Prosesserer data fra datavarehuset og teamkatalogen for å tilgjengeliggjøre data for å bruke i dashbord om mangfold.

[Team Heda](https://teamkatalog.nav.no/team/1ae1604f-1007-4846-9cea-0153a0ad7c8c) er ansvarlig.

## Datalast
### Kilde HR data
Det er noen tabeller som team Sigma i datavarehuset har tilgjengeliggjort som views med tilgang til en egen databasebruker `DVH_SRV_TEAM_HEDA_PY`. Disse blir aggregert og lagt i datasettet `mangfold_processed_data` i bigQuery.

#### Tabeller

#### Skedulering
Daglig

### Kilde teamkatalogen
I mappen teamkatalogen_bq blir det kjørt månedlige snapshot av teamkatalogen hentet via deres API. Her finnes det ingen 

#### Tabeller
Tabellene ligger i BigQuery i Heda sitt prod gcp-prosjekt. Datasettet heter `teamkatalogen`, og her ligger følgende tabeller:

| Tabell               | Beskrivelse                                 |
|----------------------|---------------------------------------------|
| monthly_snapshot_raw | Rådata fra teamkatalogen, insert hver måned |
| teamkat_gender_pred | Prosessert data med sannsynlig kjønn        |
| omraade_rolle_stats | Aggregerte data på måned, område og rolle   |
| omraade_stats | Aggregerte data på måned og område          |
| rolle_stats | Aggregerte data på måned og rolle           |


#### Skedulering
Datalasten kjøres månedlig via Heda sin [airflow](https://heda.airflow.knada.io/).
Pga at lasten trenger tilgang til teamkatalogen, kjøres den i Knada sitt miljø.

### Servicebruker
Vi har opprettet egen servicebruker i gcp `heda-access`, som har fått BigQuery Admin-rolle i Heda sitt gcp-prosjekt. Nøkkel for denne servicebrukeren ligger i Google Secret Manager.

## Dashbord

## Quarto
Vi har et eget [dashbord](https://data.ansatt.nav.no/story/7ea943c9-ae07-4d75-9b65-d775c05230dc) for å visualisere dataene.

Kjør `quarto preview dashboard.qmd` for å se dashbordet lokalt.

Kjør så `publish_story.py` for å publisere dashbordet til datamarkedsplassen.