# Sommerstudenter: Mangfoldsprosjekt
Underprosjekt av [#heda](../README.md)

[Sommerstudenter med Team Heda](https://teamkatalog.nav.no/team/1ae1604f-1007-4846-9cea-0153a0ad7c8c) er ansvarlig.

Se også [`README.md`](../README.md) for over-prosjektet, og de relaterte sommerstudent-repoene [mangfold-frontend](https://github.com/navikt/mangfold-frontend) og [mangfold-backend](https://github.com/navikt/mangfold-backend). Prosjektet er organisert på Slack, se [`#sommerstudent-prosjekt-mangfold`](https://nav-it.slack.com/archives/C08TXNNMBAT) for mer informasjon.

## Datalast
### Kilde
Data hentes fra HR-data i Oracle datavarehus. Se Python-skriptene [`daglig_hr_data_til_bq.py`](../dags/daglig_hr_data_til_bq.py) og [`hr_data/hr_data_til_bq.py`](hr_data_til_bq.py).

### Tabeller
Nye tabeller som oprettes ligger i BigQuery i Heda sitt prod gcp-prosjekt. 

Test data er i dev prosjekt - svarer ikke til format på ny reell data lenger.

Se `#sommerstudent-prosjekt-mangfold` i Slack for mer informasjon om BigQuery tabeller og innhold. Det lages tabeller som speiler view fra datavarehus ([`hr_data_til_bq.py`](hr_data_til_bq.py)) i datasettet `hr_data`, og nye aggregerte tabeller som brukes till innsikt og rapportering ([`main_prosessering.py`](../hr_data/main_prosessering.py)) i datasettet `mangfold_processed_data`.

### Skedulering
Datalasten kjøres daglig om morgenen (Oslo) via Heda sin [airflow](https://heda.airflow.knada.io/).

Prosessering kjøres etter data-last, og oppdaterer automatisk tabeller i BigQuery som skal brukes til endelig dashboard.

## Dashboard
Dashboardet som lages er tilgjengelig for Nav-ansatte via: https://mangfold.ansatt.dev.nav.no/

## Oppsett

### uv / pip
Se [`requirements_bq.txt`](../requirements_bq.txt) for nødvendige pakker til `hr_data` prosjektet. Kan brukes av standard Python metoder, DAG og sommerstudenter kjører [uv](https://docs.astral.sh/uv/) som pakkeløsning. Sett opp pakker i et uv-environment med:

```uv pip install -r ../requirements_bq.txt```

Det er også en egen [`hr_data/pyproject.toml`](pyproject.toml) fil for under-prosjektet.

Pass på å alltid kjøre  i `hr_data` mappen.

### Ruff, ty

Prosjektet bruker ruff til automatisk formattering og linting, pluss ty for type-sjekking. Det enkleste er å bruke Visual Studio Code med [ruff](https://github.com/astral-sh/ruff-vscode) og [ty](https://github.com/astral-sh/ty-vscode) extensions installert, da sees advarsler in-line i Vscode. Innstillinger for ruff er i [`ruff.toml`](ruff.toml).

## Videre arbeid
(Denne listen er skrevet i prioritert rekkefølge)

Etter hvert blir det sannsynligvis tilgjengelig historisk data, da må ekstra filtrering gjøres for å velge ut data tilsvarende bare den siste måneden. Tallene i dashboardet vil se veldig rare ut om man ikke bare bruker data fra en måned.

Underprosjektet har ikke blitt splittet ut i eget repo fordi Airflow og service account var satt opp i dette repoet allerede. Veien videre er enten eget repo eller å erstatte overprosjektet som ikke lenger vil være i bruk siden det ble bygget uten tilgang til hr-data og lager et mer begrenset quarto-dashboard.

Det er vurdert bruk av Differential Privacy for å pseudonymisere data (se Navs håndbok for ansvarlig data science under team tada). Dette kan være en framtidig forbedring, akkurat nå brukes SSB-stil prikking.

Det er vurdert sammenslåing av noen typer grupperinger for å samle små grupper av f. eks. stillinger til en samlet "Annen" gruppe. Dette krever mer gjennomtenkning.

Det er ikke gjort automatisk testing av koden enda, det går an å teste manuelt ved å kjøre de ulike filene i mappen [`hr_data/hr_data_prosessering/`](hr_data_prosessering/) og se at de gir forventet output. Det kan være ønskelig med fult dev-prod setup hvor det finnes en dev-versjon av dashboardet som bruker test data som da genereres i [`hr_data/hr_data_prosessering/test_data_generer_i_csv.py`](hr_data_prosessering/test_data_generer_i_csv.py). Men dette krever mye mer arbeid på frontend, backend, og bruk av testing i disse, så det er ikke prioritert nå. 

Skriptet [`hr_data/main_prosessering.py`](main_prosessering.py) er lagt opp til dev-prod split, og det er mulig å kjøre dev-versjonen for å laste opp test-data til BigQuery. Denne brukes ikke til noe.

En del funksjoner brukes ikke lenger, og format på data har endret seg. Trenger gjennomgang av `hr_data/hr_data_prosessering/` for å rengjøre litt.

## Om kildedata
Noen spredte notater om dataen og kildene.

#### Pseudonøkler
- Pseudonøkler er en unik identifikator som er gitt fra viewet vi har tilgang til i datavarehuset. Det skal være garantert at samme en rad med samme pseudonøkkel representerer samme person.

#### Kjønn
- Kjønn er utledet fra personnummer, og skal behandles som sensitiv informasjon. Kjønn presenteres derfor kun for grupperinger. Små grupperinger blir ikke vist direkte, dette håndteres i [mangfold-backend](https://github.com/navikt/mangfold-backend).
- Kjønn tilsvarer juridisk kjønn.
- Kildedataen inneholder kun verdiene "Mann" eller "Kvinne" for kjønn, dette er et garanti fra kilden.

#### Teamkatalog vs ansettelsesdata
- Det er gjort et skille mellom ansettelses-data og teamkatalog-data, og nye tabeller som er laget bruker mønsteret `_hr_` for tabeller med ansettelsesdata og `_tk_` for teamkatalog-data.

#### Unikhet
- Data for ansettelse skal være unik når det er valgt ut ut unike pseudonøkler, og én person skal bare ha én seksjonstilknytning og én stilling (stillingsnavn).
- Data for teamkatalogen er *ikke* unik, så det er mulig å ha flere tilknytninger. Derfor er det ikke filtrert på pseudonøkler i tabeller for teamkatalogen.
- Det er *ikke* nok å bruke `DISTINCT(pseudo_key)` i SQL-spørringer for å velge personer en gang. Det er derfor gjort ekstra filtrering med pandas `.drop_duplicates(subset=["pseudo_key"], keep="first")` for tabeller med ansettelsesdata. Om det legges til en ny tabell som skal inneholde hr-data blir optellingen feil om man glemmer å legge til tabellen i listen `TARGET_TABLES_UNIQUE_HR_DATA` i [`hr_data/main_prosessering.py`](main_prosessering.py).
- Teamkatalog-data har ikke denne filtreringen for å beholde ekstra tilknytninger. Ikke gjør opptellinger som skal representere personer på teamkatalog-data.

#### NA-verdier
- Manglende verdier fylles ut med strengen "Ukjent" rett etter last fra datavarehuset. NA-verdier som eksisterer i endelige BigQuery tabeller er da opstått under prosessering.
- En del "Ukjent" verdier er videre endret til mer deskriptive verdier. Se funksjonen `nan_to_user_friendly_string`.
- Airflow-logger vil skrive ut "Warnings" der det er funnet NA-verdier i kildedataen. Sjekk disse for å se hva som burde fikses i personallsystemet.
- Akkurat nå finnes det ukjente aldre. Ansettelsesår, kjønn, og ledernivå for direktoratet er OK.

#### Metadata-tabell
- Det er laget en metadata-tabell som inneholder informasjon om datalastene som kjøres. Det viktigste er datoen for når siste last skjedde, dette brukes i dashboardet.
- Timestamp er til bruk av maskiner, dato-strengen er ment til å lese av selv (formatteringen ble egentlig valgt for å svare til norsk dato-format, viste seg å være ISO 8601 uten T hvis man sorterer etter år-månede-dag). Dette kan endres på.
- Om man vil legge til eller endre kolonner må man endre schema i BigQuery, siden metadata-tabellen bruker append. Alle andre tabeller overskrives helt så schema blir oppdatert automatisk.

#### main_prosessering.py
- Hovedfilen for prossesering av data, den er lagt opp med SETTINGS øverst i filen. Kan vurdere å splitte til en egen fil.
- Basis-definisjoner som gjøres er ikke under `if __main__` slik at de kan importeres i andre filer.
- Funksjon for å generere metadata og hoved-flyten (pipeline) for prosessering er definert i denne filen for å holde de sentralt. Støttefunksjoner er i [`hr_data/hr_data_prosessering/`](hr_data_prosessering/).
- `main()`funksjonen detekterer environment (basert på eksistens av env variabel for PROD) og velger enten `dev_main()` eller `prod_main()`. Prod-versjonen kjører ekte data. Det er mulig å overstyre og kjøre prod-versjonen med flagg i kommando-linjen, se nederst i filen. Man må være autentisert med BigQuery (`gcloud auth application-default login`) for å kunne hente inn ekte data.
