create table monthly_snapshot_raw
(
    Tilknyttning STRING,
    Omraade      STRING,
    Klynge       STRING,
    Team         STRING,
    Ident        STRING,
    Fornavn      STRING,
    Etternavn    STRING,
    Type         STRING,
    Roller       STRING,
    Annet        STRING,
    Epost        STRING,
    Startdato    STRING,
    Sluttdato    STRING,
    lastet_dato  DATE
);

create table omraade_rolle_stats
(
    dato_mnd       DATE,
    Omraade        STRING,
    Rolle          STRING,
    antall_totalt  INT64,
    antall_kvinner INT64,
    antall_ukjent  INT64
);

create table omraade_stats
(
    dato_mnd       DATE,
    Omraade        STRING,
    antall_totalt  INT64,
    antall_kvinner INT64,
    antall_ukjent  INT64
);

create table rolle_stats
(
    dato_mnd       DATE,
    Rolle          STRING,
    antall_totalt  INT64,
    antall_kvinner INT64,
    antall_ukjent  INT64
);

create table teamkat_gender_pred
(
    dato_mnd    DATE,
    Ident       STRING,
    Omraade     STRING,
    Team        STRING,
    Roller      STRING,
    Type        STRING,
    for_navn    STRING,
    gender_pred STRING
);
