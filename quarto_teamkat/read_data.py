import pandas as pd
from google.cloud import bigquery

DEFAULT_MONTHS = 48


def load_rolle_stats():
    client = bigquery.Client(project="datafolk-prod-94c7")
    return client.query(
        "SELECT dato_mnd, Rolle, antall_totalt "
        "FROM `datafolk-prod-94c7.teamkatalogen_01012023_01112026.rolle_stats` "
        "ORDER BY dato_mnd, antall_totalt DESC, Rolle"
    ).to_dataframe()


def load_omraade_stats():
    client = bigquery.Client(project="datafolk-prod-94c7")
    return client.query(
        "SELECT dato_mnd, Omraade AS `Område`, antall_totalt "
        "FROM `datafolk-prod-94c7.teamkatalogen_01012023_01112026.omraade_stats` "
        "ORDER BY dato_mnd, antall_totalt DESC, Omraade"
    ).to_dataframe()


def load_internal_stats():
    client = bigquery.Client(project="datafolk-prod-94c7")
    return client.query(
        "SELECT dato_mnd, COUNT(*) AS antall_totalt, "
        "100.0 * COUNTIF(Type = 'Intern') / COUNT(*) AS andel_interne "
        "FROM `datafolk-prod-94c7.teamkatalogen_01012023_01112026.teamkat_gender_pred` "
        "GROUP BY dato_mnd ORDER BY dato_mnd"
    ).to_dataframe()


def prepare_stats(data, months=DEFAULT_MONTHS, group_column="Rolle"):
    data = data[["dato_mnd", group_column, "antall_totalt"]].copy()
    data["dato_mnd"] = pd.to_datetime(data["dato_mnd"], errors="raise")
    data["dato_mnd"] = data["dato_mnd"].dt.to_period("M").dt.to_timestamp()
    data["antall_totalt"] = pd.to_numeric(data["antall_totalt"], errors="raise")
    if data.empty or data.isna().any().any():
        raise ValueError(
            "Data må inneholde måneder, grupper og antall uten manglende verdier."
        )

    first_month = data["dato_mnd"].max() - pd.DateOffset(months=months - 1)
    data = data.loc[data["dato_mnd"] >= first_month]
    return data.sort_values(
        ["dato_mnd", "antall_totalt", group_column], ascending=[True, False, True]
    )


def growth_summary(data, group_column="Rolle"):
    first_month = data["dato_mnd"].min()
    last_month = data["dato_mnd"].max()
    first = data.loc[data["dato_mnd"] == first_month].set_index(group_column)[
        "antall_totalt"
    ]
    last = data.loc[data["dato_mnd"] == last_month].set_index(group_column)[
        "antall_totalt"
    ]
    summary = pd.concat([first.rename("Start"), last.rename("Siste")], axis=1).fillna(0)
    summary["Absolutt endring"] = summary["Siste"] - summary["Start"]
    summary["Endring (%)"] = (
        summary["Absolutt endring"].div(summary["Start"].where(summary["Start"] > 0))
        * 100
    )
    return summary.sort_values("Siste", ascending=False)
