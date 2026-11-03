# hvor-er-damene
Dette repoet er arkivert da team Heda er avviklet. Eierskap ble overført til `datafolk` i november 2026 og tabellene ble flyttet til et dataset i BigQuery under `datafolk` sitt prosjekt for ikke å miste historikken. 

Det ble kjørt en månedlig jobb fra januar 2023 til og med november 2026 som kopierte data fra Nav sin teamkatalog. Resultatet er delt i en [datafortelling](https://data.ansatt.nav.no/quarto/c94d05cf-77dd-44fe-9a20-7aa912c2fc14).

#### Mapper

| Mappe | Innhold |
|-------|---------|
| `dags/` | Airflow-jobben som styrte månedlig innhenting, bearbeiding og aggregering av data, samt oppdatering av datafortellingen. |
| `javazone/` | Kilder og kode for diagrammer brukt til JavaZone-presentasjonen "Hvor er damene?".  |
| `navn/` | Navnelister som ble brukt til å supplere prediksjon av kjønn basert på fornavn. |
| `quarto_heda/` | Quarto-dashboard om kvinneandel i tech, med data fra Teamkatalogen, SSB, Samordna opptak og rekruttering i Nav IT. Avviklet|
| `quarto_teamkat/` | Quarto-dashboard som viser utviklingen i Teamkatalogen over tid, fordelt på roller og områder, samt andelen interne. |
| `teamkatalogen_bq/` | Kode for å hente data fra Teamkatalogen, lagre månedlige uttrekk i BigQuery, vaske data, predikere kjønn og lage aggregerte tabeller. |


#### Tabeller
Tabellene ligger i BigQuery i `datafolk` sitt prod gcp-prosjekt, og her ligger følgende tabeller:

| Tabell               | Beskrivelse                                 |
|----------------------|---------------------------------------------|
| monthly_snapshot_raw | Rådata fra teamkatalogen, insert hver måned |
| teamkat_gender_pred | Prosessert data med sannsynlig kjønn        |
| omraade_rolle_stats | Aggregerte data på måned, område og rolle   |
| omraade_stats | Aggregerte data på måned og område          |
| rolle_stats | Aggregerte data på måned og rolle           |
